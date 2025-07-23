#!/usr/bin/env python3
"""
Dead simple approach: Read claude_memory.md directly and ask OpenAI to generate the complete website
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

def extract_key_entries(session_content):
    """Extract only the key development entries from session log"""
    lines = session_content.split('\n')
    entries = []
    
    for line in lines:
        # Look for timestamp entries that contain actual development work
        if '## 2025-' in line and any(keyword in line.lower() for keyword in [
            'fixed', 'implemented', 'added', 'created', 'updated', 'completed', 
            'revolutionary', 'breakthrough', 'critical', 'major', 'success']):
            entries.append(line)
        # Also grab a few lines after each timestamp for context
        elif entries and len(entries) < 100:  # Limit to prevent too much text
            if line.strip() and not line.startswith('#'):
                entries.append(line)
    
    return '\n'.join(entries[:20])  # Take first 20 most relevant entries

def generate_website():
    """Read session log directly and generate complete website"""
    
    # Read the session log
    session_log = Path("session-logs/claude_memory.md")
    if not session_log.exists():
        print("❌ No session logs found at session-logs/claude_memory.md")
        return
    
    with open(session_log, 'r', encoding='utf-8') as f:
        session_content = f.read()
    
    print(f"🔄 Processing session log directly ({len(session_content)} characters)...")
    
    # Extract key entries to stay under token limits
    key_content = extract_key_entries(session_content)
    print(f"🎯 Extracted key entries ({len(key_content)} characters)...")
    
    # Create simpler, shorter prompt
    prompt = f'''Create an HTML page "I just want to build" with dark theme from this dev log:

DESIGN: Dark GitHub theme, fixed header with avatar https://avatars.githubusercontent.com/u/2623736?s=400&u=e7f8d6597d1d222a1f038ed316af1e439c3a57b4&v=4, banner "I just want to build", two columns (NT_OrderManager | FluidJournal), scrollable.

CATEGORIZE as NT_OrderManager (trading/NinjaTrader) or FluidJournal (agentic memory/ML). 
ORGANIZE: Plans→Features→Changes→Fixes with color codes.

DEV ENTRIES:
{key_content}

Return complete HTML only.'''
    
    try:
        print("🔄 Asking OpenAI to generate complete website from session log...")
        html_content = make_openai_request(prompt)
        
        # Write to index.html
        output_path = Path("index.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Complete website generated directly from session log!")
        print(f"📄 Output written to {output_path}")
        
    except Exception as e:
        print(f"❌ Failed to generate website: {e}")

if __name__ == "__main__":
    generate_website()