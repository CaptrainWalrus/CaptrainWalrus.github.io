#!/usr/bin/env python3
"""
Let OpenAI generate the entire website from raw session logs
No static coding - OpenAI does all organization, categorization, and HTML generation
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

def make_openai_request(prompt, max_tokens=4000):
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

def chunk_session_logs(raw_content, max_chunk_size=15000):
    """Split session logs into chunks that fit OpenAI token limits"""
    lines = raw_content.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line_size = len(line)
        if current_size + line_size > max_chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def process_chunk_with_openai(chunk, chunk_num, total_chunks):
    """Process a single chunk and extract structured data"""
    print(f"  Processing chunk {chunk_num}/{total_chunks}...")
    
    prompt = f"""Extract and categorize ALL development entries from this session log chunk ({chunk_num}/{total_chunks}).

For each entry, return JSON format:
{{
  "project": "NT_OrderManager" or "FluidJournal",
  "date": "YYYY-MM-DD",
  "category": "plan" (big plans), "feature" (new functionality), "change" (modifications), or "fix" (bug fixes),
  "priority": "high", "medium", or "low",
  "description": "Natural, conversational summary (max 100 chars)",
  "technical_detail": "Key technical aspect if relevant",
  "impact": "Why this matters"
}}

PROJECT RULES:
- NT_OrderManager: NinjaTrader, trading, strategies, signals, order management, randomization
- FluidJournal: Agentic memory, storage, risk agents, LanceDB, machine learning, graduation, Gaussian Process

CATEGORY RULES:
- plan: Revolutionary breakthroughs, major architecture changes, new system designs
- feature: New functionality, implementations, additions
- change: Modifications, updates, improvements to existing code
- fix: Bug fixes, error corrections, problem solving

Extract EVERY entry from this chunk. Return as JSON array.

CHUNK DATA:
{chunk}"""

    try:
        response = make_openai_request(prompt, max_tokens=4000)
        # Try to parse JSON from response
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            print(f"  ⚠️ Could not parse JSON from chunk {chunk_num}")
            return []
    except Exception as e:
        print(f"  ❌ Failed to process chunk {chunk_num}: {e}")
        return []

def generate_html_from_data(all_entries):
    """Generate final HTML from processed entries"""
    print("🔄 Asking OpenAI to generate final HTML from all processed entries...")
    
    # Organize data
    nt_entries = [e for e in all_entries if e.get('project') == 'NT_OrderManager']
    fluid_entries = [e for e in all_entries if e.get('project') == 'FluidJournal']
    
    prompt = f"""Generate a complete HTML website called "I just want to build" using this processed data.

DESIGN REQUIREMENTS:
- Dark GitHub theme (#0d1117 background, #161b22 cards)
- Fixed header with avatar: https://avatars.githubusercontent.com/u/2623736?s=400&u=e7f8d6597d1d222a1f038ed316af1e439c3a57b4&v=4
- Banner: "I just want to build"
- Two columns with scrollable content (80vh height)
- Color-coded categories: Plans (purple), Features (green), Changes (blue), Fixes (red)
- Priority badges (HIGH/MEDIUM/LOW)
- Tech stack footer

ORGANIZE BY PRIORITY ORDER:
1. 🚀 Plans (purple)
2. ✨ Features (green) 
3. 🔧 Changes (blue)
4. 🐛 Fixes (red)

NT_OrderManager entries ({len(nt_entries)} total):
{json.dumps(nt_entries, indent=2)}

FluidJournal entries ({len(fluid_entries)} total):
{json.dumps(fluid_entries, indent=2)}

Return ONLY complete HTML - no explanations."""
    
    return make_openai_request(prompt, max_tokens=8000)

def generate_website_with_openai():
    """Let OpenAI generate the entire website by processing all chunks"""
    
    # Load raw session logs
    session_log = Path("session-logs/claude_memory.md")
    if not session_log.exists():
        print("❌ No session logs found")
        return
    
    with open(session_log, 'r', encoding='utf-8') as f:
        raw_content = f.read()
    
    print(f"🔄 Processing entire session log ({len(raw_content)} characters)...")
    
    # Split into chunks
    chunks = chunk_session_logs(raw_content)
    print(f"📦 Split into {len(chunks)} chunks for processing")
    
    # Process each chunk
    all_entries = []
    for i, chunk in enumerate(chunks, 1):
        entries = process_chunk_with_openai(chunk, i, len(chunks))
        all_entries.extend(entries)
    
    print(f"✅ Extracted {len(all_entries)} total entries from all chunks")
    
    # Generate final HTML
    try:
        html_content = generate_html_from_data(all_entries)
        
        # Write to index.html
        output_path = Path("index.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Complete website generated with ALL {len(all_entries)} entries!")
        print("🤖 OpenAI processed the entire session log")
        
    except Exception as e:
        print(f"❌ Failed to generate final HTML: {e}")

if __name__ == "__main__":
    generate_website_with_openai()