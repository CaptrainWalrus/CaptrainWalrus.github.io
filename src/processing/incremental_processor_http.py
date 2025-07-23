#!/usr/bin/env python3
"""
Incremental session log processor that uses OpenAI via HTTP requests
No external dependencies required - uses built-in Python libraries only
"""

import os
import json
import hashlib
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

class IncrementalProcessor:
    def __init__(self):
        self.cache_dir = Path("src/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "processed_entries.json"
        self.session_logs_dir = Path("session-logs")
        
        # Load existing cache
        self.cache = self.load_cache()
        
        # OpenAI API configuration
        self.api_key = self.load_api_key()
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
    def load_api_key(self):
        """Load API key from .env file"""
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        return line.split('=', 1)[1].strip()
        
        # Also check environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception("No OpenAI API key found in .env file or environment")
        return api_key
        
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
                
                # Detect project based on tags
                if '[NinjaTrader]' in line or 'order-manager' in line.lower() or 'NT_OrderManager' in line:
                    current_entry['project'] = 'nt'
                elif '[FluidJournal]' in line or 'agentic' in line.lower() or 'fluid' in line.lower():
                    current_entry['project'] = 'fluid'
                elif '[Cohere]' in line or 'cohere' in line.lower():
                    current_entry['project'] = 'fluid'  # Map Cohere to FluidJournal
                elif '[VectorBT]' in line:
                    current_entry['project'] = 'fluid'  # Map VectorBT to FluidJournal
        
        # Don't forget the last entry
        if current_entry:
            entry_hash = self.get_entry_hash(current_entry['raw'])
            if entry_hash not in self.cache['entries']:
                new_entries.append(current_entry)
        
        return new_entries
    
    def make_openai_request(self, prompt):
        """Make a request to OpenAI API using urllib"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 200
        }
        
        req = urllib.request.Request(
            self.api_url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result['choices'][0]['message']['content']
                    
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                print(f"⚠️ HTTP Error {e.code}: {error_body}")
                if e.code == 429:  # Rate limit
                    if attempt < max_retries - 1:
                        print(f"   Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                raise Exception(f"OpenAI API error: {error_body}")
                
            except urllib.error.URLError as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Connection error (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    raise Exception(f"Connection failed after {max_retries} attempts: {str(e)}")
                    
            except Exception as e:
                print(f"⚠️ Unexpected error: {type(e).__name__}: {str(e)}")
                raise
        
        raise Exception("Failed to get response from OpenAI after all retries")
    
    def process_with_openai(self, entry):
        """Use OpenAI to create a high-level summary of the entry"""
        prompt = f"""Analyze this development log entry and create a conversational summary:

Timestamp: {entry['timestamp']}
Content: {entry['content']}

Create a JSON response with:
1. "type": "plan" (new/big plans), "feature" (new functionality), "change" (modifications), "fix" (bug fixes)
2. "description": A conversational summary as if telling a colleague what you did (max 100 chars)
3. "technical_detail": Key technical aspect if relevant (optional)
4. "impact": Why this matters for the project (optional)
5. "priority": "high" (revolutionary/critical), "medium" (important), "low" (routine)

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
- Overly technical jargon without context

Return ONLY valid JSON, no extra text."""

        try:
            response_text = self.make_openai_request(prompt)
            
            # Try to parse JSON from response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise Exception("Could not parse JSON from OpenAI response")
            
            return {
                'type': result.get('type', 'change'),
                'description': result.get('description', entry['content'][:100]),
                'technical_detail': result.get('technical_detail'),
                'impact': result.get('impact'),
                'priority': result.get('priority', 'medium')
            }
            
        except Exception as e:
            print(f"⚠️ OpenAI processing failed for entry: {entry['timestamp']}")
            print(f"   Error: {str(e)}")
            raise  # No fallback - we require OpenAI to work
    
    def process_new_entries(self):
        """Process only new entries and update cache"""
        new_entries = self.parse_new_entries()
        
        if not new_entries:
            print("✅ No new entries to process")
            return
        
        print(f"🔄 Processing {len(new_entries)} new entries with OpenAI...")
        
        processed_count = 0
        for i, entry in enumerate(new_entries):
            print(f"   Processing entry {i+1}/{len(new_entries)}: {entry['timestamp'][:50]}...")
            
            try:
                # Process with OpenAI only
                processed = self.process_with_openai(entry)
                
                # Cache the processed entry
                entry_hash = self.get_entry_hash(entry['raw'])
                self.cache['entries'][entry_hash] = {
                    'timestamp': entry['timestamp'],
                    'project': entry['project'],
                    'processed': processed,
                    'hash': entry_hash
                }
                processed_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to process entry: {str(e)}")
                print("   Stopping processing due to error (no fallbacks allowed)")
                raise
        
        # Update last processed time
        self.cache['last_processed'] = datetime.now().isoformat()
        
        # Save cache
        self.save_cache()
        print(f"✅ Successfully processed {processed_count} entries with OpenAI")
        
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
    print("🚀 Starting OpenAI HTTP-based processor (no pip dependencies)...")
    processor = IncrementalProcessor()
    processor.process_new_entries()
    processor.export_for_generator()