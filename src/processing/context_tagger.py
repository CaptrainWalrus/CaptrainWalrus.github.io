#!/usr/bin/env python3
"""
Context tagger for Claude session logs
Automatically tags entries with project context like [NinjaTrader], [FluidJournal], etc.
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class ProjectContext:
    """Definition of a project context for tagging"""
    tag: str
    keywords: List[str]
    patterns: List[str]
    description: str

class ContextTagger:
    def __init__(self):
        """Initialize the context tagger with project definitions"""
        self.project_contexts = [
            ProjectContext(
                tag="NinjaTrader",
                keywords=[
                    "ninjatrader", "ninja trader", "nt", "order-manager",
                    "trading strategy", "signal approval", "position tracking",
                    "entry signal", "exit signal", "stop loss", "take profit",
                    "pattern matching", "order flow", "market data",
                    "OrderManagement.cs", "TraditionalStrategies.cs",
                    "SignalFeatures.cs", "MainStrategy.cs", "CurvesStrategy",
                    "deregisterposition", "registerposition", "pnl", "bars",
                    "MGC", "gold", "futures", "trading", "agentic memory",
                    "risk agent", "ME service", "MI service", "RF service"
                ],
                patterns=[
                    r"order[-_]manager",
                    r"ninja[-_]trader",
                    r"trading[-_]system",
                    r"signal[-_]approval",
                    r"position[-_]tracking",
                    r"\.cs\b",  # C# files
                    r"\b(ME|MI|RF)[-_]service",
                    r"\$\d+",  # Dollar amounts (trading profits/losses)
                    r"\bpnl\b",
                    r"\bmgc\b",
                    r"\bbars?\b.*\b(OHLC|market|price)",
                ],
                description="NinjaTrader trading platform and related services"
            ),
            
            ProjectContext(
                tag="FluidJournal",
                keywords=[
                    "fluid journal", "fluidjournal", "production-curves",
                    "agentic memory", "storage agent", "risk service",
                    "langchain", "vector store", "lancedb", "graduation",
                    "feature graduation", "range-based", "gaussian process",
                    "similarity matching", "pattern clustering", "GP",
                    "model training", "RF training", "pytorch", "machine learning",
                    "feature importance", "vectorbt", "backtesting"
                ],
                patterns=[
                    r"production[-_]curves",
                    r"fluid[-_]journal",
                    r"agentic[-_]memory",
                    r"storage[-_]agent",
                    r"risk[-_]service",
                    r"vector[-_]store",
                    r"lance[-_]?db",
                    r"\.py\b",  # Python files
                    r"\.js\b",  # JavaScript files
                    r"langchain",
                    r"gaussian[-_]process",
                    r"feature[-_]graduation"
                ],
                description="AI/ML research and agentic memory system"
            ),
            
            ProjectContext(
                tag="Cohere",
                keywords=[
                    "cohere", "auto-regen", "website", "github pages",
                    "session logs", "claude memory", "content generation",
                    "static site", "html generator", "jinja2", "markdown",
                    "repository", "workflow", "automation"
                ],
                patterns=[
                    r"auto[-_]regen",
                    r"github[-_]pages",
                    r"session[-_]logs",
                    r"claude[-_]memory",
                    r"\.html\b",
                    r"\.md\b",
                    r"content[-_]generation",
                    r"static[-_]site"
                ],
                description="Auto-regenerating website project"
            ),
            
            ProjectContext(
                tag="VectorBT",
                keywords=[
                    "vectorbt", "backtesting", "strategy optimization",
                    "feature ranking", "decile optimization", "sweet spot",
                    "boruta", "feature importance", "portfolio", "returns",
                    "sharpe ratio", "drawdown", "equity curve"
                ],
                patterns=[
                    r"vectorbt",
                    r"backtest",
                    r"strategy[-_]optimization",
                    r"feature[-_]ranking",
                    r"decile[-_]optimization",
                    r"sharpe[-_]ratio",
                    r"equity[-_]curve"
                ],
                description="Backtesting and strategy optimization"
            ),
            
            ProjectContext(
                tag="Infrastructure",
                keywords=[
                    "docker", "github actions", "workflow", "deployment",
                    "ci/cd", "container", "service", "port", "endpoint",
                    "api", "server", "database", "environment", "config",
                    "logging", "monitoring", "debugging", "troubleshooting"
                ],
                patterns=[
                    r"github[-_]actions",
                    r"\.yml\b",
                    r"\.yaml\b",
                    r"docker",
                    r"port\s+\d+",
                    r"localhost:\d+",
                    r"api[-_]endpoint",
                    r"service[-_]status"
                ],
                description="Infrastructure, deployment, and system administration"
            )
        ]
    
    def detect_project_contexts(self, text: str) -> List[Tuple[str, float]]:
        """
        Detect which project contexts are present in the text
        Returns list of (tag, confidence_score) tuples
        """
        text_lower = text.lower()
        context_scores = {}
        
        for context in self.project_contexts:
            score = 0.0
            total_possible = len(context.keywords) + len(context.patterns)
            
            # Check keywords
            for keyword in context.keywords:
                if keyword.lower() in text_lower:
                    score += 1.0
            
            # Check regex patterns
            for pattern in context.patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 1.0
            
            # Calculate confidence as percentage of matches
            confidence = (score / total_possible) if total_possible > 0 else 0.0
            
            if confidence > 0:
                context_scores[context.tag] = confidence
        
        # Return sorted by confidence, minimum threshold 0.05 (5%)
        return [(tag, score) for tag, score in sorted(context_scores.items(), 
                                                     key=lambda x: x[1], reverse=True)
                if score >= 0.05]
    
    def tag_entry(self, entry_text: str, timestamp: str = None) -> Dict[str, any]:
        """
        Tag a single log entry with project contexts
        Returns enhanced entry data
        """
        contexts = self.detect_project_contexts(entry_text)
        
        # Determine primary context (highest confidence)
        primary_context = contexts[0][0] if contexts else "General"
        
        # Create tags list
        tags = [tag for tag, confidence in contexts if confidence >= 0.1]  # 10% threshold for tags
        
        return {
            'original_text': entry_text,
            'timestamp': timestamp,
            'primary_context': primary_context,
            'all_contexts': contexts,
            'tags': tags,
            'tagged_text': self.add_visual_tags(entry_text, tags)
        }
    
    def add_visual_tags(self, text: str, tags: List[str]) -> str:
        """Add visual tags to the beginning of entry text"""
        if not tags:
            return text
        
        tag_string = " ".join([f"[{tag}]" for tag in tags])
        
        # If text starts with a header (##), insert tags after it
        if text.strip().startswith('##'):
            lines = text.split('\n', 1)
            if len(lines) > 1:
                return f"{lines[0]} {tag_string}\n{lines[1]}"
            else:
                return f"{lines[0]} {tag_string}"
        else:
            return f"{tag_string} {text}"
    
    def process_session_log(self, session_content: str) -> Dict[str, any]:
        """
        Process an entire session log and tag all entries
        Returns enhanced session data with context analysis
        """
        # Split into individual entries (by date headers)
        entries = self.split_into_entries(session_content)
        
        tagged_entries = []
        context_summary = {}
        
        for entry in entries:
            tagged_entry = self.tag_entry(entry['text'], entry['timestamp'])
            tagged_entries.append(tagged_entry)
            
            # Accumulate context statistics
            for tag in tagged_entry['tags']:
                context_summary[tag] = context_summary.get(tag, 0) + 1
        
        # Generate enhanced session content
        enhanced_content = self.reconstruct_session_content(tagged_entries)
        
        return {
            'original_content': session_content,
            'enhanced_content': enhanced_content,
            'entries': tagged_entries,
            'context_summary': context_summary,
            'total_entries': len(tagged_entries),
            'primary_contexts': list(context_summary.keys())
        }
    
    def split_into_entries(self, content: str) -> List[Dict[str, str]]:
        """Split session content into individual entries by timestamp headers"""
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
                        'text': current_entry.strip()
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
                'text': current_entry.strip()
            })
        
        return entries
    
    def reconstruct_session_content(self, tagged_entries: List[Dict[str, any]]) -> str:
        """Reconstruct session content with tags added"""
        return '\n\n'.join([entry['tagged_text'] for entry in tagged_entries])
    
    def generate_context_report(self, session_data: Dict[str, any]) -> str:
        """Generate a summary report of project contexts found"""
        report = "# Project Context Analysis\n\n"
        
        if not session_data['context_summary']:
            return report + "No specific project contexts detected.\n"
        
        report += "## Context Distribution\n\n"
        for context, count in sorted(session_data['context_summary'].items(), 
                                   key=lambda x: x[1], reverse=True):
            percentage = (count / session_data['total_entries']) * 100
            report += f"- **{context}**: {count} entries ({percentage:.1f}%)\n"
        
        report += f"\n**Total Entries**: {session_data['total_entries']}\n"
        report += f"**Primary Contexts**: {', '.join(session_data['primary_contexts'])}\n"
        
        return report

# Example usage and testing
if __name__ == "__main__":
    tagger = ContextTagger()
    
    # Test with sample text
    sample_text = """
    ## 2025-07-23 17:25:00 - Fixed NinjaTrader Integration
    Updated SignalFeatures.cs to properly send PnL data to the ME service.
    The storage agent now receives complete trade outcome data with normalized
    pnlPerContract values for fair comparison across position sizes.
    """
    
    result = tagger.tag_entry(sample_text)
    print("Tagged entry:")
    print(result['tagged_text'])
    print(f"Contexts: {result['tags']}")
    print(f"Primary: {result['primary_context']}")