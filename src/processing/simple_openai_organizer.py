#!/usr/bin/env python3
"""
Simple approach: Use existing processed entries and let OpenAI reorganize them
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path

def load_api_key():
    """Load API key from .env file"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    return line.split('=', 1)[1].strip()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise Exception("No OpenAI API key found")
    return api_key

def make_openai_request(prompt, max_tokens=8000):
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
        "max_tokens": max_tokens
    }
    
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ OpenAI request failed: {e}")
        raise

def generate_website():
    """Use existing processed entries and ask OpenAI to organize them properly"""
    
    # Load existing processed content
    content_file = Path("src/content/incremental_content.json")
    if not content_file.exists():
        print("❌ No processed content found")
        return
    
    with open(content_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get all entries
    nt_changes = data.get('nt_changes', {})
    fluid_changes = data.get('fluid_changes', {})
    
    print(f"🔄 Found {len(nt_changes)} NT days and {len(fluid_changes)} Fluid days")
    
    # Count total entries
    total_nt = sum(len(entries) for entries in nt_changes.values())
    total_fluid = sum(len(entries) for entries in fluid_changes.values())
    print(f"📊 Total entries: NT={total_nt}, Fluid={total_fluid}")
    
    prompt = f"""Generate a complete HTML website called "I just want to build" using this development data.

REQUIREMENTS:
1. Show ALL entries from the data (NT: {total_nt} entries, Fluid: {total_fluid} entries)
2. Organize by priority: 🚀 Plans → ✨ Features → 🔧 Changes → 🐛 Fixes
3. Two columns with scrollable content (height: 80vh)
4. Natural, conversational descriptions
5. Priority badges (HIGH/MEDIUM/LOW)

DESIGN:
- Dark GitHub theme (#0d1117 background, #161b22 cards)
- Fixed header with avatar: https://avatars.githubusercontent.com/u/2623736?s=400&u=e7f8d6597d1d222a1f038ed316af1e439c3a57b4&v=4
- Banner: "I just want to build"
- Color-coded categories: Plans (purple), Features (green), Changes (blue), Fixes (red)
- Tech stack footer

CATEGORIZATION RULES:
- Plans: Revolutionary breakthroughs, major architecture changes (e.g., "Range-Based Graduation System", "Gaussian Process Migration")
- Features: New functionality, implementations (e.g., "Split storage system", "Risk Agent")  
- Changes: Modifications, improvements (e.g., "Updated ME service", "Enhanced logging")
- Fixes: Bug fixes, error corrections (e.g., "Fixed PnL issue", "Fixed schema error")

NT_OrderManager data:
{json.dumps(nt_changes, indent=2)}

FluidJournal data:
{json.dumps(fluid_changes, indent=2)}

Generate complete HTML showing ALL {total_nt + total_fluid} entries organized by priority. Return ONLY HTML."""

    try:
        print("🔄 Asking OpenAI to generate organized website...")
        html_content = make_openai_request(prompt)
        
        # Write to index.html
        output_path = Path("index.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Website generated with ALL {total_nt + total_fluid} entries!")
        
    except Exception as e:
        print(f"❌ Failed to generate website: {e}")

if __name__ == "__main__":
    generate_website()