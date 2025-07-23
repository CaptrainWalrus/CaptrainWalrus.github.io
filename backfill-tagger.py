#!/usr/bin/env python3
"""
Backfill tagger for existing claude_memory.md files
Automatically adds project context tags to existing session entries
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

# Import our context tagger (assuming it's in the same directory or PATH)
sys.path.append('starter-files/src/processing')
from context_tagger import ContextTagger

class BackfillTagger:
    def __init__(self):
        """Initialize the backfill tagger"""
        self.context_tagger = ContextTagger()
        self.workspace_dir = Path("/mnt/c/workspace")
        self.cohere_dir = Path("/mnt/c/workspace/Cohere")
        
    def find_claude_memory_files(self) -> list:
        """Find all claude_memory.md files in workspace"""
        memory_files = []
        
        # Main workspace claude_memory.md
        main_file = self.workspace_dir / "claude_memory.md"
        if main_file.exists():
            memory_files.append(("Main Workspace", main_file))
        
        # Look for project-specific claude_memory.md files
        for project_dir in self.workspace_dir.iterdir():
            if project_dir.is_dir() and project_dir.name != "Cohere":
                claude_file = project_dir / "claude_memory.md"
                if claude_file.exists():
                    memory_files.append((project_dir.name, claude_file))
                    
                # Also check subdirectories
                if project_dir.name == "FluidJournal":
                    agentic_file = project_dir / "agentic_memory" / "claude_memory.md"
                    if agentic_file.exists():
                        memory_files.append(("FluidJournal-AgenticMemory", agentic_file))
        
        return memory_files
    
    def backup_file(self, file_path: Path):
        """Create a backup of the original file"""
        backup_path = file_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
        print(f"📁 Backup created: {backup_path}")
        return backup_path
    
    def split_into_entries(self, content: str) -> list:
        """Split content into individual timestamped entries"""
        entries = []
        current_entry = ""
        current_timestamp = None
        
        lines = content.split('\n')
        
        for line in lines:
            # Look for timestamp headers like "## 2025-07-23 17:25:00"
            timestamp_match = re.match(r'^##\s+(20\d{2}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)', line)
            
            if timestamp_match:
                # Save previous entry
                if current_entry.strip():
                    entries.append({
                        'timestamp': current_timestamp,
                        'header_line': current_entry.split('\n')[0] if current_entry else "",
                        'content': current_entry.strip(),
                        'original_content': current_entry.strip()
                    })
                
                # Start new entry
                current_timestamp = timestamp_match.group(1)
                current_entry = line + '\n'
            else:
                current_entry += line + '\n'
        
        # Add final entry
        if current_entry.strip():
            entries.append({
                'timestamp': current_timestamp,
                'header_line': current_entry.split('\n')[0] if current_entry else "",
                'content': current_entry.strip(),
                'original_content': current_entry.strip()
            })
        
        return entries
    
    def process_entry(self, entry: dict) -> dict:
        """Process a single entry and add context tags"""
        # Use our context tagger to detect contexts
        contexts = self.context_tagger.detect_project_contexts(entry['content'])
        
        # Determine primary context and tags
        primary_context = contexts[0][0] if contexts else "General"
        tags = [tag for tag, confidence in contexts if confidence >= 0.1]  # 10% threshold
        
        # Add tags to the header line if not already present
        header_line = entry['header_line']
        
        # Check if tags are already present
        existing_tags = re.findall(r'\[([^\]]+)\]', header_line)
        tags_to_add = [tag for tag in tags if tag not in existing_tags]
        
        if tags_to_add:
            # Add tags after the timestamp and title
            tag_string = " " + " ".join([f"[{tag}]" for tag in tags_to_add])
            
            # Insert tags after the header but before any existing content
            lines = entry['content'].split('\n')
            if lines:
                lines[0] = lines[0] + tag_string
                tagged_content = '\n'.join(lines)
            else:
                tagged_content = entry['content'] + tag_string
        else:
            tagged_content = entry['content']
        
        return {
            **entry,
            'primary_context': primary_context,
            'contexts': contexts,
            'tags': tags,
            'tagged_content': tagged_content,
            'tags_added': tags_to_add
        }
    
    def reconstruct_file_content(self, processed_entries: list, original_content: str) -> str:
        """Reconstruct the file content with tagged entries"""
        # Start with any content before the first timestamp entry
        lines = original_content.split('\n')
        header_content = []
        
        for line in lines:
            if re.match(r'^##\s+20\d{2}-\d{2}-\d{2}', line):
                break
            header_content.append(line)
        
        # Build the new content
        new_content = '\n'.join(header_content)
        if header_content and header_content[-1].strip():
            new_content += '\n\n'
        
        # Add processed entries
        for entry in processed_entries:
            new_content += entry['tagged_content'] + '\n\n'
        
        return new_content.rstrip() + '\n'
    
    def process_file(self, file_info: tuple, dry_run: bool = True) -> dict:
        """Process a single claude_memory.md file"""
        project_name, file_path = file_info
        
        print(f"\n🔍 Processing: {project_name} ({file_path})")
        
        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return {'success': False, 'error': str(e)}
        
        # Split into entries
        entries = self.split_into_entries(content)
        print(f"📝 Found {len(entries)} entries")
        
        # Process each entry
        processed_entries = []
        total_tags_added = 0
        context_summary = {}
        
        for entry in entries:
            processed_entry = self.process_entry(entry)
            processed_entries.append(processed_entry)
            
            # Count tags added
            if processed_entry['tags_added']:
                total_tags_added += len(processed_entry['tags_added'])
                print(f"  📌 {processed_entry['timestamp']}: Added {processed_entry['tags_added']}")
            
            # Update context summary
            for tag in processed_entry['tags']:
                context_summary[tag] = context_summary.get(tag, 0) + 1
        
        # Reconstruct file content
        new_content = self.reconstruct_file_content(processed_entries, content)
        
        # Show summary
        print(f"✅ Summary for {project_name}:")
        print(f"   - Total entries: {len(entries)}")
        print(f"   - Tags added: {total_tags_added}")
        print(f"   - Context distribution: {dict(context_summary)}")
        
        if not dry_run:
            # Create backup
            backup_path = self.backup_file(file_path)
            
            # Write new content
            file_path.write_text(new_content, encoding='utf-8')
            print(f"💾 Updated: {file_path}")
        else:
            print(f"🏃 DRY RUN: Would update {file_path}")
        
        return {
            'success': True,
            'project_name': project_name,
            'file_path': str(file_path),
            'entries_processed': len(entries),
            'tags_added': total_tags_added,
            'context_summary': context_summary,
            'processed_entries': processed_entries
        }
    
    def create_cohere_session_logs(self, processed_files: list):
        """Create session-logs directory structure for Cohere project"""
        session_logs_dir = self.cohere_dir / "session-logs"
        session_logs_dir.mkdir(exist_ok=True)
        
        # Create projects subdirectory
        projects_dir = session_logs_dir / "projects"
        projects_dir.mkdir(exist_ok=True)
        
        for file_result in processed_files:
            if not file_result['success']:
                continue
                
            project_name = file_result['project_name']
            
            # Create project-specific directory
            if project_name == "Main Workspace":
                # Copy main claude_memory.md to session-logs root
                dest_file = session_logs_dir / "claude_memory.md"
            else:
                # Create project subdirectory
                project_dir = projects_dir / project_name.lower().replace(' ', '-')
                project_dir.mkdir(exist_ok=True)
                dest_file = project_dir / "claude_memory.md"
            
            # Copy the tagged content
            source_file = Path(file_result['file_path'])
            if source_file.exists():
                content = source_file.read_text(encoding='utf-8')
                dest_file.write_text(content, encoding='utf-8')
                print(f"📋 Copied to: {dest_file}")
    
    def run_backfill(self, dry_run: bool = True):
        """Run the complete backfill process"""
        print("🚀 Starting Claude Memory Backfill Tagging")
        print(f"{'🏃 DRY RUN MODE' if dry_run else '💾 LIVE MODE'}")
        
        # Find all claude_memory.md files
        memory_files = self.find_claude_memory_files()
        print(f"\n📁 Found {len(memory_files)} claude_memory.md files:")
        for project_name, file_path in memory_files:
            print(f"   - {project_name}: {file_path}")
        
        if not memory_files:
            print("❌ No claude_memory.md files found!")
            return
        
        # Process each file
        processed_files = []
        for file_info in memory_files:
            result = self.process_file(file_info, dry_run)
            processed_files.append(result)
        
        # Create summary report
        print("\n📊 BACKFILL SUMMARY:")
        total_entries = sum(r['entries_processed'] for r in processed_files if r['success'])
        total_tags = sum(r['tags_added'] for r in processed_files if r['success'])
        
        print(f"   Total files processed: {len([r for r in processed_files if r['success']])}")
        print(f"   Total entries tagged: {total_entries}")
        print(f"   Total tags added: {total_tags}")
        
        # Global context summary
        global_contexts = {}
        for result in processed_files:
            if result['success']:
                for context, count in result['context_summary'].items():
                    global_contexts[context] = global_contexts.get(context, 0) + count
        
        print(f"   Global context distribution:")
        for context, count in sorted(global_contexts.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {context}: {count} entries")
        
        if not dry_run:
            # Create Cohere session-logs structure
            print(f"\n📁 Creating Cohere session-logs structure...")
            self.create_cohere_session_logs(processed_files)
            
            print(f"\n✅ Backfill complete! Tagged files are ready for the auto-regen website.")
            print(f"📂 Session logs copied to: {self.cohere_dir / 'session-logs'}")
        else:
            print(f"\n🏃 DRY RUN complete! Run with --apply to make changes.")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill context tags to claude_memory.md files')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry run)')
    parser.add_argument('--file', type=str, help='Process specific file only')
    
    args = parser.parse_args()
    
    tagger = BackfillTagger()
    
    if args.file:
        # Process specific file
        file_path = Path(args.file)
        if file_path.exists():
            result = tagger.process_file(("Custom", file_path), not args.apply)
            print(f"\n✅ Processed {args.file}")
        else:
            print(f"❌ File not found: {args.file}")
    else:
        # Process all files
        tagger.run_backfill(dry_run=not args.apply)

if __name__ == "__main__":
    main()