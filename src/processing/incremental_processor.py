#!/usr/bin/env python3
"""
Incremental session log processor that uses OpenAI for new entries only
Caches processed content to avoid regenerating existing entries
"""

import os
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not installed, will use basic extraction")

class IncrementalProcessor:
    def __init__(self):
        self.cache_dir = Path("src/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "processed_entries.json"
        self.session_logs_dir = Path("session-logs")
        
        # Load existing cache
        self.cache = self.load_cache()
        
        # Initialize OpenAI only if we have new content
        self.client = None
        
    def load_cache(self):
        """Load previously processed entries"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"entries": {}, "last_processed": None}
        return {"entries": {}, "last_processed": None}
    
    def save_cache(self):
        """Save processed entries to cache"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def get_entry_hash(self, entry_text):
        """Generate hash for an entry to detect changes"""
        return hashlib.sha256(entry_text.encode()).hexdigest()
    
    def parse_new_entries(self):
        """Find entries that haven't been processed yet"""
        new_entries = []
        session_log = self.session_logs_dir / "claude_memory.md"
        
        if not session_log.exists():
            return new_entries
            
        with open(session_log, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse entries
        lines = content.split('\n')
        current_entry = None
        
        for i, line in enumerate(lines):
            if line.startswith('## 20'):  # Date header
                if current_entry:
                    # Check if this entry is new
                    entry_hash = self.get_entry_hash(current_entry['raw'])
                    if entry_hash not in self.cache['entries']:
                        new_entries.append(current_entry)
                
                # Start new entry
                current_entry = {
                    'timestamp': line.replace('## ', '').strip(),
                    'raw': line,
                    'content': '',
                    'project': None
                }
            elif current_entry and line.strip():
                current_entry['raw'] += '\n' + line
                current_entry['content'] += line + ' '
                
                # Detect project
                if '[NinjaTrader]' in line or 'order-manager' in line.lower():
                    current_entry['project'] = 'nt'
                elif '[FluidJournal]' in line or 'agentic' in line.lower():
                    current_entry['project'] = 'fluid'
        
        # Don't forget the last entry
        if current_entry:
            entry_hash = self.get_entry_hash(current_entry['raw'])
            if entry_hash not in self.cache['entries']:
                new_entries.append(current_entry)
        
        return new_entries
    
    def process_with_openai(self, entry):
        """Use OpenAI to create a high-level summary of the entry"""
        if not OPENAI_AVAILABLE:
            return self.basic_extraction(entry)
            
        if not self.client:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("⚠️ No OpenAI API key, using basic extraction")
                return self.basic_extraction(entry)
            self.client = OpenAI(api_key=api_key)
        
        if not OPENAI_AVAILABLE or not self.client:
            # Skip processing without OpenAI
            return None
        
        # Retry logic for connection errors
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                prompt = f"""Analyze this development log entry and create a conversational summary:

Timestamp: {entry['timestamp']}
Content: {entry['content']}

Create a JSON response with:
1. "type": "add" (new feature), "remove" (cleanup/deletion), or "idea" (concept/planning)
2. "description": A conversational summary as if telling a colleague what you did (max 100 chars)
3. "technical_detail": Key technical aspect if relevant (optional)
4. "impact": Why this matters for the project (optional)

Write the description as if you're the developer talking to a friend about what you worked on today.
Don't use "User" - this is YOUR development journey. Keep it natural and human.

Good examples:
- "Finally got the PnL values showing correctly after that marathon debug session"
- "Built a split storage system that actually makes sense now"
- "Trades were getting rejected left and right - had to dig deep into the risk logic"
- "That storageClient error had me stumped for hours"
- "Realized the system needs to detect when we should trade the opposite direction"

Avoid:
- Corporate speak or formal documentation language
- Third person references
- Overly technical jargon without context"""

                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=200,
                    timeout=30  # Add 30 second timeout
                )
                
                result = json.loads(response.choices[0].message.content)
                return {
                    'type': result.get('type', 'idea'),
                    'description': result.get('description', entry['content'][:100]),
                    'technical_detail': result.get('technical_detail'),
                    'impact': result.get('impact')
                }
                
            except json.JSONDecodeError:
                # If we can't parse JSON, return None to skip
                print(f"⚠️ Failed to parse OpenAI response as JSON")
                return None
                
            except Exception as e:
                error_type = type(e).__name__
                if error_type in ['APIConnectionError', 'Timeout', 'ConnectionError']:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Connection error (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print(f"⚠️ Connection failed after {max_retries} attempts")
                        return None
                else:
                    print(f"⚠️ OpenAI processing failed: {error_type}: {str(e)}")
                    if hasattr(e, '__dict__'):
                        print(f"   Details: {e.__dict__}")
                    return None
        
        return None  # If all retries failed
    
    def basic_extraction(self, entry):
        """Fallback extraction without OpenAI"""
        content_lower = entry['content'].lower()
        
        # Determine type
        entry_type = 'idea'
        if any(word in content_lower for word in ['added', 'implemented', 'created', 'fixed']):
            entry_type = 'add'
        elif any(word in content_lower for word in ['removed', 'deleted', 'cleaned']):
            entry_type = 'remove'
        
        # Extract description - just get the core message
        sentences = entry['content'].split('.')
        description = sentences[0].strip() if sentences else entry['content'][:100]
        
        # Simply truncate to length
        if len(description) > 95:
            description = description[:92] + '...'
        
        return {
            'type': entry_type,
            'description': description,
            'technical_detail': None,
            'impact': None
        }
    
    def process_new_entries(self):
        """Process only new entries and update cache"""
        new_entries = self.parse_new_entries()
        
        if not new_entries:
            print("✅ No new entries to process")
            return
        
        print(f"🔄 Processing {len(new_entries)} new entries...")
        
        for entry in new_entries:
            # Process with OpenAI only
            processed = self.process_with_openai(entry)
            
            # Only cache if successfully processed
            if processed:
                entry_hash = self.get_entry_hash(entry['raw'])
                self.cache['entries'][entry_hash] = {
                    'timestamp': entry['timestamp'],
                    'project': entry['project'],
                    'processed': processed,
                    'hash': entry_hash
                }
        
        # Update last processed time
        self.cache['last_processed'] = datetime.now().isoformat()
        
        # Save cache
        self.save_cache()
        print(f"✅ Processed and cached {len(new_entries)} new entries")
        
    def get_project_changes(self):
        """Get organized changes by project and date"""
        nt_changes = {}
        fluid_changes = {}
        
        for entry_data in self.cache['entries'].values():
            # Extract date from timestamp
            date = entry_data['timestamp'].split()[0] if ' ' in entry_data['timestamp'] else entry_data['timestamp']
            
            change_item = {
                'type': entry_data['processed']['type'],
                'description': entry_data['processed']['description'],
                'technical_detail': entry_data['processed'].get('technical_detail'),
                'impact': entry_data['processed'].get('impact')
            }
            
            if entry_data['project'] == 'nt':
                if date not in nt_changes:
                    nt_changes[date] = []
                nt_changes[date].append(change_item)
            elif entry_data['project'] == 'fluid':
                if date not in fluid_changes:
                    fluid_changes[date] = []
                fluid_changes[date].append(change_item)
        
        return nt_changes, fluid_changes
    
    def export_for_generator(self):
        """Export processed data for the HTML generator"""
        nt_changes, fluid_changes = self.get_project_changes()
        
        output_data = {
            'generated_at': datetime.now().isoformat(),
            'last_processed': self.cache['last_processed'],
            'total_entries': len(self.cache['entries']),
            'nt_changes': nt_changes,
            'fluid_changes': fluid_changes,
            'cache_info': {
                'total_cached': len(self.cache['entries']),
                'last_update': self.cache['last_processed']
            }
        }
        
        output_file = Path("src/content/incremental_content.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported data to {output_file}")
        return output_data

if __name__ == "__main__":
    processor = IncrementalProcessor()
    processor.process_new_entries()
    processor.export_for_generator()