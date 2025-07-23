#!/usr/bin/env python3
"""
Simple backfill script that works without external dependencies
Manually tags the main claude_memory.md file with project contexts
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

class SimpleContextTagger:
    """Simplified context tagger that works without external dependencies"""
    
    def __init__(self):
        self.project_patterns = {
            'NinjaTrader': [
                r'ninjatrader', r'ninja trader', r'order-manager', r'trading strategy',
                r'signal approval', r'position tracking', r'entry signal', r'exit signal',
                r'OrderManagement\.cs', r'TraditionalStrategies\.cs', r'SignalFeatures\.cs',
                r'deregisterposition', r'registerposition', r'\bpnl\b', r'MGC', r'trading',
                r'agentic memory', r'risk agent', r'ME service', r'MI service', r'RF service',
                r'\$\d+', r'bars.*OHLC', r'stop loss', r'take profit'
            ],
            'FluidJournal': [
                r'fluid journal', r'fluidjournal', r'production-curves',
                r'storage agent', r'risk service', r'langchain', r'vector store',
                r'lancedb', r'graduation', r'feature graduation', r'range-based',
                r'gaussian process', r'similarity matching', r'pattern clustering',
                r'model training', r'RF training', r'pytorch', r'machine learning',
                r'feature importance', r'vectorbt', r'backtesting', r'\.py\b', r'\.js\b'
            ],
            'VectorBT': [
                r'vectorbt', r'backtesting', r'strategy optimization',
                r'feature ranking', r'decile optimization', r'sweet spot',
                r'boruta', r'portfolio', r'returns', r'sharpe ratio',
                r'drawdown', r'equity curve'
            ],
            'Infrastructure': [
                r'docker', r'github actions', r'workflow', r'deployment',
                r'ci/cd', r'container', r'service', r'port \d+', r'endpoint',
                r'api', r'server', r'database', r'environment', r'config',
                r'logging', r'monitoring', r'debugging', r'localhost:\d+'
            ]
        }
    
    def detect_contexts(self, text: str) -> list:
        """Detect project contexts in text"""
        text_lower = text.lower()
        contexts = []
        
        for context, patterns in self.project_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matches += 1
            
            # If we find multiple matches, include this context
            if matches >= 2:  # Require at least 2 pattern matches
                confidence = min(matches / len(patterns), 1.0)
                contexts.append((context, confidence))
        
        return sorted(contexts, key=lambda x: x[1], reverse=True)

def process_claude_memory():
    """Process the main claude_memory.md file"""
    
    # File paths
    source_file = Path("/mnt/c/workspace/claude_memory.md")
    backup_file = Path(f"/mnt/c/workspace/claude_memory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    
    if not source_file.exists():
        print(f"❌ File not found: {source_file}")
        return False
    
    print(f"📖 Reading: {source_file}")
    
    # Read the file
    try:
        content = source_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Create backup
    try:
        backup_file.write_text(content, encoding='utf-8')
        print(f"📁 Backup created: {backup_file}")
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False
    
    # Initialize tagger
    tagger = SimpleContextTagger()
    
    # Split into entries
    entries = []
    lines = content.split('\n')
    current_entry = ""
    entry_count = 0
    
    for line in lines:
        current_entry += line + '\n'
        
        # Look for timestamp headers to end entries
        if re.match(r'^##\s+20\d{2}-\d{2}-\d{2}', line) and current_entry.strip():
            if entry_count > 0:  # Don't process the first header line alone
                entries.append(current_entry[:-len(line)-1])  # Remove current line
                current_entry = line + '\n'
            entry_count += 1
    
    # Add final entry
    if current_entry.strip():
        entries.append(current_entry)
    
    print(f"📝 Found {len(entries)} entries to process")
    
    # Process entries
    new_content = ""
    total_tags_added = 0
    context_summary = {}
    
    for i, entry in enumerate(entries):
        # Detect contexts
        contexts = tagger.detect_contexts(entry)
        
        if contexts:
            # Get top contexts (minimum confidence 0.1)
            tags = [ctx for ctx, conf in contexts if conf >= 0.1][:3]  # Max 3 tags
            
            if tags:
                # Add tags to the header line
                lines = entry.split('\n')
                header_line = lines[0] if lines else ""
                
                # Check if header has timestamp
                if re.match(r'^##\s+20\d{2}-\d{2}-\d{2}', header_line):
                    # Add tags after the header
                    tag_string = " " + " ".join([f"[{tag}]" for tag in tags])
                    lines[0] = header_line + tag_string
                    entry = '\n'.join(lines)
                    
                    total_tags_added += len(tags)
                    print(f"  📌 Entry {i+1}: Added {tags}")
                    
                    # Update summary
                    for tag in tags:
                        context_summary[tag] = context_summary.get(tag, 0) + 1
        
        new_content += entry
        if not entry.endswith('\n'):
            new_content += '\n'
    
    print(f"\n✅ Processing complete:")
    print(f"   - Total entries: {len(entries)}")
    print(f"   - Tags added: {total_tags_added}")
    print(f"   - Context distribution: {dict(context_summary)}")
    
    # Ask user before applying changes
    print(f"\n🤔 Apply these changes to {source_file}? (y/N): ", end="")
    response = input().strip().lower()
    
    if response in ['y', 'yes']:
        try:
            source_file.write_text(new_content, encoding='utf-8')
            print(f"💾 Updated: {source_file}")
            
            # Copy to Cohere session-logs
            cohere_dir = Path("/mnt/c/workspace/Cohere")
            session_logs_dir = cohere_dir / "session-logs"
            session_logs_dir.mkdir(exist_ok=True)
            
            dest_file = session_logs_dir / "claude_memory.md"
            dest_file.write_text(new_content, encoding='utf-8')
            print(f"📋 Copied to: {dest_file}")
            
            print(f"\n🎉 SUCCESS! Your claude_memory.md is now tagged and ready!")
            print(f"📂 Location: {dest_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error writing file: {e}")
            return False
    else:
        print("🏃 Changes not applied.")
        return False

def main():
    """Main function"""
    print("🚀 Simple Claude Memory Context Tagger")
    print("=" * 50)
    
    success = process_claude_memory()
    
    if success:
        print(f"\n✅ COMPLETE! Your session log is now tagged and ready for the auto-regen website!")
        print(f"\n🔄 Next steps:")
        print(f"  1. Copy starter-files to your dev-journey repository")
        print(f"  2. Add OpenAI API key to repository secrets") 
        print(f"  3. Commit and push to trigger auto-generation")
        print(f"\n🌐 Your website will be live at: https://captrainwalrus.github.io/dev-journey")
    else:
        print(f"\n❌ Tagging incomplete. Please check errors above.")

if __name__ == "__main__":
    main()