#!/usr/bin/env python3
"""
Free LangChain processor using Ollama (no API key required)
Alternative to OpenAI for processing Claude session logs
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Try different free LLM options
try:
    # Option 1: Ollama (completely free, runs locally)
    from langchain.llms import Ollama
    USE_OLLAMA = True
except ImportError:
    USE_OLLAMA = False

try:
    # Option 2: Hugging Face (free tier)
    from langchain.llms import HuggingFacePipeline
    USE_HUGGINGFACE = True
except ImportError:
    USE_HUGGINGFACE = False

# Import our context tagger
from context_tagger import ContextTagger

class FreeSessionLogProcessor:
    def __init__(self):
        """Initialize with free LLM options"""
        self.llm = self.setup_free_llm()
        self.context_tagger = ContextTagger()
        self.session_logs_dir = Path("session-logs")
        self.output_dir = Path("src/content")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_free_llm(self):
        """Setup free LLM (Ollama preferred, fallback to simple processing)"""
        
        if USE_OLLAMA:
            try:
                # Use Ollama with a small model (e.g., llama2, mistral)
                llm = Ollama(model="llama2:7b")
                print("✅ Using Ollama (free local LLM)")
                return llm
            except Exception as e:
                print(f"⚠️ Ollama not available: {e}")
        
        if USE_HUGGINGFACE:
            try:
                # Use Hugging Face free tier
                from transformers import pipeline
                pipe = pipeline("text-generation", model="gpt2")
                llm = HuggingFacePipeline(pipeline=pipe)
                print("✅ Using Hugging Face free tier")
                return llm
            except Exception as e:
                print(f"⚠️ Hugging Face not available: {e}")
        
        print("⚠️ No free LLMs available, using rule-based processing")
        return None
    
    def process_with_rules(self, content: str, contexts: list) -> dict:
        """Rule-based processing when no LLM is available"""
        
        # Simple keyword-based insight extraction
        insights = {
            'breakthrough': 'Processing development updates...',
            'problem_solved': 'Analyzing session progress...',
            'learning_pattern': 'Tracking development patterns...',
            'momentum': 'Active development',
            'project_focus': contexts[0] if contexts else 'General Development'
        }
        
        # Look for breakthrough keywords
        breakthrough_words = ['breakthrough', 'complete', 'success', 'fixed', 'solved', 'implemented']
        for word in breakthrough_words:
            if word.lower() in content.lower():
                insights['breakthrough'] = f"Made progress with {word}-related development"
                break
        
        # Look for problem-solving
        problem_words = ['error', 'bug', 'issue', 'problem', 'fix', 'debug']
        for word in problem_words:
            if word.lower() in content.lower():
                insights['problem_solved'] = f"Addressed {word}-related challenge"
                break
        
        # Determine momentum based on recent activity
        if 'complete' in content.lower() or 'success' in content.lower():
            insights['momentum'] = 'High momentum - completing features'
        elif 'error' in content.lower() or 'debug' in content.lower():
            insights['momentum'] = 'Problem-solving phase'
        else:
            insights['momentum'] = 'Steady development progress'
        
        return insights
    
    def process_with_llm(self, content: str, contexts: list) -> dict:
        """Process with free LLM when available"""
        try:
            prompt = f"""
            Analyze this development session and provide insights:
            
            Project contexts: {', '.join(contexts) if contexts else 'General'}
            Content: {content[:1000]}...
            
            Provide brief insights about:
            1. What breakthrough or progress was made
            2. What problem was solved
            3. Current development momentum
            
            Keep responses under 50 words each.
            """
            
            response = self.llm(prompt)
            
            # Parse response (simple keyword extraction)
            return {
                'breakthrough': response[:100] if 'breakthrough' in response.lower() else 'Development progress made',
                'problem_solved': response[:100] if 'problem' in response.lower() else 'Technical challenges addressed',
                'learning_pattern': 'Continuous learning and development',
                'momentum': 'Active development phase',
                'project_focus': contexts[0] if contexts else 'General Development'
            }
            
        except Exception as e:
            print(f"⚠️ LLM processing failed: {e}")
            return self.process_with_rules(content, contexts)
    
    def find_session_files(self) -> List[Path]:
        """Find all session log files"""
        session_files = []
        for pattern in ["**/*claude_memory.md", "**/CLAUDE.md"]:
            session_files.extend(self.session_logs_dir.glob(pattern))
        return sorted(session_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def process_session_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single session file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract project name and metadata
            project_name = self.extract_project_name(file_path)
            last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            # Get recent content (last 30 days)
            recent_content = self.extract_recent_entries(content)
            
            # Run context tagging
            context_analysis = self.context_tagger.process_session_log(recent_content)
            contexts = context_analysis['primary_contexts']
            
            # Process with available method
            if self.llm:
                insights = self.process_with_llm(recent_content, contexts)
            else:
                insights = self.process_with_rules(recent_content, contexts)
            
            return {
                'project_name': project_name,
                'last_modified': last_modified.isoformat(),
                'word_count': len(content.split()),
                'insights': insights,
                'context_analysis': context_analysis,
                'primary_contexts': contexts,
                'context_summary': context_analysis['context_summary']
            }
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def extract_project_name(self, file_path: Path) -> str:
        """Extract project name from file path"""
        parts = file_path.parts
        if len(parts) > 2:
            return parts[-2].replace('-', ' ').title()
        return "Main Project"
    
    def extract_recent_entries(self, content: str, days: int = 30) -> str:
        """Extract recent entries from content"""
        # Simple approach: return last 2000 characters
        return content[-2000:] if len(content) > 2000 else content
    
    def generate_website_content(self, all_insights: List[Dict[str, Any]]) -> str:
        """Generate narrative website content"""
        content = "# Development Journey\n\n"
        content += "Welcome to my development journey! Here's what I've been working on:\n\n"
        
        # Add project summaries
        for project in all_insights:
            content += f"## {project['project_name']}\n\n"
            
            insights = project['insights']
            if insights.get('breakthrough'):
                content += f"**Latest Progress:** {insights['breakthrough']}\n\n"
            
            if insights.get('problem_solved'):
                content += f"**Challenges Addressed:** {insights['problem_solved']}\n\n"
            
            if insights.get('momentum'):
                content += f"**Current Status:** {insights['momentum']}\n\n"
            
            # Add context tags
            if project.get('primary_contexts'):
                tags = " ".join([f"`{ctx}`" for ctx in project['primary_contexts']])
                content += f"**Focus Areas:** {tags}\n\n"
            
            content += f"*Last updated: {project['last_modified'][:10]}*\n\n"
            content += "---\n\n"
        
        return content
    
    def process_all_sessions(self):
        """Main processing function"""
        print("🚀 Starting free session log processing...")
        
        # Find session files
        session_files = self.find_session_files()
        print(f"📁 Found {len(session_files)} session files")
        
        if not session_files:
            print("❌ No session files found")
            return
        
        # Process files
        all_insights = []
        for file_path in session_files:
            print(f"📖 Processing {file_path}")
            result = self.process_session_file(file_path)
            if result:
                all_insights.append(result)
        
        # Generate content
        narrative_content = self.generate_website_content(all_insights)
        
        # Save output
        output_data = {
            'generated_at': datetime.now().isoformat(),
            'narrative_content': narrative_content,
            'projects': all_insights,
            'total_projects': len(all_insights),
            'total_words': sum(p['word_count'] for p in all_insights),
            'processing_method': 'FREE' if not self.llm else 'LLM'
        }
        
        output_file = self.output_dir / 'processed_content.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Free processing complete! Output: {output_file}")
        print(f"📊 Processed {len(all_insights)} projects")
        print(f"🆓 Method: {'Rule-based (no LLM needed)' if not self.llm else 'Free LLM'}")

if __name__ == "__main__":
    try:
        processor = FreeSessionLogProcessor()
        processor.process_all_sessions()
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Create minimal fallback
        output_dir = Path("src/content")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        fallback_data = {
            'generated_at': datetime.now().isoformat(),
            'narrative_content': "# Development Journey\n\nProcessing session logs (no API key required)...",
            'projects': [],
            'total_projects': 0,
            'total_words': 0,
            'processing_method': 'FALLBACK'
        }
        
        with open(output_dir / 'processed_content.json', 'w') as f:
            json.dump(fallback_data, f, indent=2)
        
        print("⚠️ Created fallback content (works without any API keys)")