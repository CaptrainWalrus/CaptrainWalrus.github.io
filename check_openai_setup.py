#!/usr/bin/env python3
"""
Check OpenAI setup and configuration
"""
import sys
import os

print("🔍 Checking OpenAI setup...\n")

# Check Python version
print(f"✅ Python version: {sys.version}")

# Check if OpenAI is installed
try:
    import openai
    print(f"✅ OpenAI installed: {openai.__version__}")
except ImportError:
    print("❌ OpenAI NOT installed!")
    print("   Run: pip install openai")
    sys.exit(1)

# Check if dotenv is installed
try:
    import dotenv
    print("✅ python-dotenv installed")
except ImportError:
    print("❌ python-dotenv NOT installed!")
    print("   Run: pip install python-dotenv")
    sys.exit(1)

# Check for .env file
if os.path.exists('.env'):
    print("✅ .env file exists")
    
    # Load and check API key
    dotenv.load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key:
        print(f"✅ API key found: {api_key[:20]}...{api_key[-4:]}")
    else:
        print("❌ API key NOT found in .env")
else:
    print("❌ .env file NOT found")

print("\n🔧 Testing OpenAI connection...")

# Try to use OpenAI
try:
    from openai import OpenAI
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key to test with")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    # Simple test
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'Connection successful!'"}],
        max_tokens=10,
        timeout=10
    )
    
    print(f"✅ OpenAI connection successful!")
    print(f"   Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ OpenAI connection failed!")
    print(f"   Error: {type(e).__name__}: {str(e)}")
    sys.exit(1)

print("\n✅ All checks passed! OpenAI is ready to use.")