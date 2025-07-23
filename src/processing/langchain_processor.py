#!/usr/bin/env python3
"""
LangChain processor for Claude session logs
Extracts insights and generates content for auto-regen website
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# LangChain imports
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Import our context tagger
from context_tagger import ContextTagger

class SessionLogProcessor:
    def __init__(self):
        """Initialize the LangChain processor"""
        self.setup_llm()
        self.setup_chains()
        self.context_tagger = ContextTagger()
        self.session_logs_dir = Path("session-logs")
        self.output_dir = Path("src/content")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_llm(self):
        """Setup the language model"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.llm = OpenAI(
            temperature=0.3,
            max_tokens=2000,
            openai_api_key=api_key
        )
        
    def setup_chains(self):
        """Setup LangChain processing chains"""
        
        # Chain for extracting key insights from session logs with context awareness
        insight_template = PromptTemplate(
            input_variables=["session_content", "project_contexts"],
            template="""
            Analyze this Claude development session log and extract the most important insights.
            Focus on breakthroughs, major problems solved, learning patterns, and development momentum.
            
            Project Contexts Found: {project_contexts}
            
            Session Content:
            {session_content}
            
            Please provide:
            1. Major Breakthrough (if any): What significant progress was made?
            2. Key Problem Solved: What important challenge was overcome?
            3. Learning Pattern: What development pattern or insight emerged?
            4. Current Momentum: What is the current development velocity and focus?
            5. Project Focus: Based on the contexts, what is the main project focus?
            
            Format as a JSON object with keys: breakthrough, problem_solved, learning_pattern, momentum, project_focus
            """
        )
        self.insight_chain = LLMChain(llm=self.llm, prompt=insight_template)
        
        # Chain for generating website narrative content
        narrative_template = PromptTemplate(
            input_variables=["insights_data"],
            template="""
            Transform these development insights into engaging website content that tells the story
            of an active software development journey.
            
            Insights:
            {insights_data}
            
            Create compelling narrative content that:
            - Shows the evolution of ideas and solutions
            - Highlights learning and growth patterns
            - Demonstrates problem-solving approaches
            - Conveys the excitement of building and discovering
            
            Write in first person as if the developer is sharing their journey.
            Use markdown formatting. Keep it engaging but professional.
            """
        )
        self.narrative_chain = LLMChain(llm=self.llm, prompt=narrative_template)
        
    def find_session_files(self) -> List[Path]:
        """Find all session log files"""
        session_files = []
        
        # Look for claude_memory.md and CLAUDE.md files
        for pattern in ["**/*claude_memory.md", "**/CLAUDE.md"]:
            session_files.extend(self.session_logs_dir.glob(pattern))
            
        return sorted(session_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def read_session_file(self, file_path: Path) -> Dict[str, Any]:
        """Read and parse a session log file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract metadata
            project_name = self.extract_project_name(file_path)
            last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            # Get recent entries (last 30 days)
            recent_content = self.extract_recent_entries(content, days=30)
            
            return {
                'file_path': str(file_path),
                'project_name': project_name,
                'last_modified': last_modified.isoformat(),
                'content': content,
                'recent_content': recent_content,
                'word_count': len(content.split())
            }
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def extract_project_name(self, file_path: Path) -> str:
        """Extract project name from file path"""
        # If file is in a subdirectory, use that as project name
        parts = file_path.parts
        if len(parts) > 2:  # More than just session-logs/filename
            return parts[-2].replace('-', ' ').title()
        else:
            return "Main Project"
    
    def extract_recent_entries(self, content: str, days: int = 30) -> str:
        """Extract entries from the last N days"""
        # Look for timestamp patterns
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Simple approach: extract entries with recent timestamps
        lines = content.split('\n')
        recent_lines = []
        
        for line in lines:
            # Look for date patterns like "2025-07-23" or "## 2025-07-23"
            date_match = re.search(r'20\d{2}-\d{2}-\d{2}', line)
            if date_match:
                try:
                    entry_date = datetime.strptime(date_match.group(), '%Y-%m-%d')
                    if entry_date >= cutoff_date:
                        recent_lines.append(line)
                except:
                    recent_lines.append(line)  # Include if date parsing fails
            elif recent_lines:  # Include content after recent date headers
                recent_lines.append(line)
        
        return '\n'.join(recent_lines) if recent_lines else content[-5000:]  # Fallback to last 5000 chars
    
    def process_with_langchain(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process session data with LangChain to extract insights"""
        try:
            # First, run context tagging on the content
            print(f"🏷️ Tagging contexts for {session_data['project_name']}...")
            context_analysis = self.context_tagger.process_session_log(session_data['recent_content'])
            
            # Prepare context summary for LangChain
            context_summary = ", ".join([f"{ctx}({count})" for ctx, count in context_analysis['context_summary'].items()])
            if not context_summary:
                context_summary = "General development"
            
            # Extract insights using LangChain with context awareness
            print(f"🧠 Analyzing {session_data['project_name']} with contexts: {context_summary}")
            insights_response = self.insight_chain.run(
                session_content=context_analysis['enhanced_content'],
                project_contexts=context_summary
            )
            
            # Try to parse as JSON, fallback to text
            try:
                insights = json.loads(insights_response)
            except:
                insights = {
                    'breakthrough': 'Analysis in progress',
                    'problem_solved': insights_response[:200],
                    'learning_pattern': 'Continuous development',
                    'momentum': 'Active development',
                    'project_focus': context_analysis['primary_contexts'][0] if context_analysis['primary_contexts'] else 'General'
                }
            
            return {
                'project_name': session_data['project_name'],
                'last_modified': session_data['last_modified'],
                'word_count': session_data['word_count'],
                'insights': insights,
                'context_analysis': context_analysis,
                'primary_contexts': context_analysis['primary_contexts'],
                'context_summary': context_analysis['context_summary']
            }
            
        except Exception as e:
            print(f"Error processing {session_data['project_name']}: {e}")
            return {
                'project_name': session_data['project_name'],
                'last_modified': session_data['last_modified'],
                'word_count': session_data['word_count'],
                'insights': {
                    'breakthrough': 'Processing...',
                    'problem_solved': 'Analysis pending',
                    'learning_pattern': 'Development ongoing',
                    'momentum': 'Active',
                    'project_focus': 'General'
                },
                'context_analysis': {'context_summary': {}, 'primary_contexts': []},
                'primary_contexts': [],
                'context_summary': {}
            }
    
    def generate_narrative_content(self, all_insights: List[Dict[str, Any]]) -> str:
        """Generate narrative content from all insights"""
        try:
            # Combine insights into a summary
            insights_summary = json.dumps(all_insights, indent=2)
            
            print("✍️ Generating narrative content...")
            narrative = self.narrative_chain.run(insights_data=insights_summary)
            
            return narrative
            
        except Exception as e:
            print(f"Error generating narrative: {e}")
            return self.create_fallback_content(all_insights)
    
    def create_fallback_content(self, all_insights: List[Dict[str, Any]]) -> str:
        """Create fallback content if LangChain processing fails"""
        content = "# Development Journey\n\n"
        content += "Welcome to my development journey! Here's what I've been working on:\n\n"
        
        for project in all_insights:
            content += f"## {project['project_name']}\n\n"
            insights = project['insights']
            
            if insights.get('breakthrough'):
                content += f"**Latest Breakthrough:** {insights['breakthrough']}\n\n"
            
            if insights.get('problem_solved'):
                content += f"**Problem Solved:** {insights['problem_solved']}\n\n"
            
            if insights.get('momentum'):
                content += f"**Current Status:** {insights['momentum']}\n\n"
            
            content += f"*Last updated: {project['last_modified'][:10]}*\n\n"
            content += "---\n\n"
        
        return content
    
    def process_all_sessions(self):
        """Main processing function"""
        print("🚀 Starting session log processing...")
        
        # Find all session files
        session_files = self.find_session_files()
        print(f"📁 Found {len(session_files)} session files")
        
        if not session_files:
            print("❌ No session files found in session-logs/ directory")
            return
        
        # Process each session file
        all_insights = []
        for file_path in session_files:
            print(f"📖 Reading {file_path}")
            session_data = self.read_session_file(file_path)
            
            if session_data:
                insights = self.process_with_langchain(session_data)
                all_insights.append(insights)
        
        # Generate narrative content
        narrative_content = self.generate_narrative_content(all_insights)
        
        # Save processed data
        output_data = {
            'generated_at': datetime.now().isoformat(),
            'narrative_content': narrative_content,
            'projects': all_insights,
            'total_projects': len(all_insights),
            'total_words': sum(p['word_count'] for p in all_insights)
        }
        
        # Save as JSON for HTML generator
        output_file = self.output_dir / 'processed_content.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Processing complete! Output saved to {output_file}")
        print(f"📊 Processed {len(all_insights)} projects with {output_data['total_words']} total words")

if __name__ == "__main__":
    try:
        processor = SessionLogProcessor()
        processor.process_all_sessions()
    except Exception as e:
        print(f"❌ Error: {e}")
        # Create minimal output for HTML generator to work
        output_dir = Path("src/content")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        fallback_data = {
            'generated_at': datetime.now().isoformat(),
            'narrative_content': "# Development Journey\n\nProcessing session logs...",
            'projects': [],
            'total_projects': 0,
            'total_words': 0
        }
        
        with open(output_dir / 'processed_content.json', 'w') as f:
            json.dump(fallback_data, f, indent=2)
        
        print("⚠️ Created fallback content")