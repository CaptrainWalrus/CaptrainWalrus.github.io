#!/usr/bin/env python3
"""
Simple test script to verify OpenAI API connectivity
"""
import os
import sys

# Read API key from .env file manually
env_file = '.env'
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                os.environ['OPENAI_API_KEY'] = line.split('=', 1)[1].strip()

try:
    from openai import OpenAI
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key found in environment")
        sys.exit(1)
    
    print(f"✅ API Key found: {api_key[:20]}...{api_key[-4:]}")
    
    # Initialize client
    client = OpenAI(api_key=api_key)
    
    # Try a simple completion
    print("🔄 Testing OpenAI connection...")
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'Hello, API is working!'"}],
        max_tokens=20
    )
    
    print(f"✅ Success! Response: {response.choices[0].message.content}")
    
except ImportError:
    print("❌ OpenAI package not installed. Run: pip install openai")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    if hasattr(e, 'response') and e.response:
        print(f"   Status: {e.response.status_code}")
        print(f"   Body: {e.response.text}")