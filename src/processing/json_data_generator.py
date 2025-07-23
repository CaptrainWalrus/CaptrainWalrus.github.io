#!/usr/bin/env python3
"""
Generate JSON data files for NT and FluidJournal updates from session logs
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path

def load_api_key():
    """Load API key from environment"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        # Try .env file
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        return line.split('=', 1)[1].strip()
        raise Exception("No OpenAI API key found")
    return api_key

def make_openai_request(prompt):
    """Make a request to OpenAI API"""
    api_key = load_api_key()
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4000
    }
    
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            if 'error' in result:
                raise Exception(f"OpenAI API error: {result['error']}")
            return result['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        error_response = e.read().decode('utf-8')
        print(f"❌ HTTP Error {e.code}: {error_response}")
        raise
    except Exception as e:
        print(f"❌ OpenAI request failed: {e}")
        raise

def extract_project_entries(session_content, project_type):
    """Extract entries for specific project type"""
    lines = session_content.split('\n')
    entries = []
    
    for line in lines:
        # Look for timestamp entries with development work
        if '## 2025-' in line and any(keyword in line.lower() for keyword in [
            'fixed', 'implemented', 'added', 'created', 'updated', 'completed', 
            'revolutionary', 'breakthrough', 'critical', 'major', 'success']):
            
            # Check if this entry is relevant to the project
            content_lower = line.lower()
            if project_type == 'NT' and any(nt_keyword in content_lower for nt_keyword in [
                'ninjatrader', 'trading', 'strategy', 'signal', 'randomiz', 'order']):
                entries.append(line)
            elif project_type == 'FluidJournal' and any(fj_keyword in content_lower for fj_keyword in [
                'agentic', 'memory', 'storage', 'risk', 'lancedb', 'graduation', 'gaussian', 'ml']):
                entries.append(line)
            elif project_type == 'FluidJournal' and 'range-based' in content_lower:
                entries.append(line)
    
    return '\n'.join(entries[:15])  # Limit to most relevant entries

def generate_project_data(project_type):
    """Generate JSON data for a specific project"""
    
    # Read session log
    session_log = Path("session-logs/claude_memory.md")
    if not session_log.exists():
        print(f"❌ No session logs found")
        return []
    
    with open(session_log, 'r', encoding='utf-8') as f:
        session_content = f.read()
    
    # Extract relevant entries
    relevant_content = extract_project_entries(session_content, project_type)
    
    if not relevant_content:
        print(f"⚠️  No {project_type} entries found")
        return []
    
    print(f"🎯 Extracted {project_type} entries ({len(relevant_content)} characters)")
    
    # Create prompt for OpenAI
    prompt = f'''Extract development entries for {project_type} from this session log and return as JSON array.

For each entry, create:
{{
  "type": "plan|feature|change|fix",
  "priority": "high|medium|low", 
  "description": "Natural first-person summary (max 80 chars)",
  "technical_detail": "Key technical aspect (optional)",
  "impact": "Why this matters (optional)"
}}

RULES:
- plan: Revolutionary breakthroughs, major architecture changes
- feature: New functionality, implementations
- change: Modifications, improvements  
- fix: Bug fixes, error corrections
- Write naturally as developer speaking to colleague
- Focus on {"trading/NinjaTrader systems" if project_type == "NT" else "agentic memory/ML systems"}

ENTRIES:
{relevant_content}

Return only JSON array, no explanations.'''
    
    try:
        response = make_openai_request(prompt)
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            print(f"⚠️  Could not parse JSON from {project_type} response")
            return []
            
    except Exception as e:
        print(f"❌ Failed to generate {project_type} data: {e}")
        return []

def generate_data_files():
    """Generate both NT and FluidJournal JSON files"""
    
    print("🔄 Generating NT OrderManager data...")
    nt_data = generate_project_data('NT')
    
    print("🔄 Generating FluidJournal data...")
    fluid_data = generate_project_data('FluidJournal')
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Write NT data
    nt_file = data_dir / "nt_updates.json"
    with open(nt_file, 'w', encoding='utf-8') as f:
        json.dump(nt_data, f, indent=2)
    print(f"✅ NT data written to {nt_file} ({len(nt_data)} entries)")
    
    # Write FluidJournal data
    fluid_file = data_dir / "fluid_updates.json"
    with open(fluid_file, 'w', encoding='utf-8') as f:
        json.dump(fluid_data, f, indent=2)
    print(f"✅ FluidJournal data written to {fluid_file} ({len(fluid_data)} entries)")
    
    print(f"🎉 Generated {len(nt_data) + len(fluid_data)} total entries!")

if __name__ == "__main__":
    generate_data_files()