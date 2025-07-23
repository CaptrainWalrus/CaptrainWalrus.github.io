#!/usr/bin/env python3
"""
Setup script for backfilling context tags to existing claude_memory.md files
"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    
    required_packages = [
        'watchdog',  # For file monitoring
    ]
    
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def test_context_tagger():
    """Test the context tagger with sample content"""
    print("\n🧪 Testing context tagger...")
    
    # Add the processing directory to path
    sys.path.append('starter-files/src/processing')
    
    try:
        from context_tagger import ContextTagger
        
        tagger = ContextTagger()
        
        # Test with sample content
        sample_content = """
        ## 2025-07-11 09:50:00 - Fixed NT DeregisterPosition Calls
        Fixed the three main DeregisterPosition calls in OrderManagement.cs to include outcomeData parameter.
        All three now properly send PnL data to ME service for storage in Agentic Memory.
        """
        
        result = tagger.tag_entry(sample_content)
        print(f"✅ Context tagger working!")
        print(f"   Detected contexts: {result['tags']}")
        print(f"   Primary context: {result['primary_context']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Context tagger import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Context tagger test failed: {e}")
        return False

def run_backfill_preview():
    """Run a dry-run preview of the backfill"""
    print("\n🔍 Running backfill preview (dry run)...")
    
    try:
        from backfill_tagger import BackfillTagger
        
        tagger = BackfillTagger()
        tagger.run_backfill(dry_run=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Backfill preview failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Claude Memory Backfill System")
    
    # Check if we're in the right directory
    if not Path("starter-files").exists():
        print("❌ Please run this script from the Cohere directory")
        print("   Current directory should contain 'starter-files' folder")
        return
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        return
    
    # Step 2: Test context tagger
    if not test_context_tagger():
        print("❌ Context tagger test failed")
        return
    
    # Step 3: Run preview
    if not run_backfill_preview():
        print("❌ Backfill preview failed")
        return
    
    # Step 4: Ask user if they want to apply changes
    print("\n" + "="*60)
    print("🎯 BACKFILL PREVIEW COMPLETE!")
    print("="*60)
    print("\nThe preview above shows what tags would be added to your session logs.")
    print("This will:")
    print("  ✅ Create backups of your original files")
    print("  ✅ Add context tags like [NinjaTrader], [FluidJournal], etc.")
    print("  ✅ Copy tagged files to Cohere/session-logs/ for auto-regen website")
    print("  ✅ Preserve all your original content")
    
    response = input("\n🤔 Apply these changes? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print("\n💾 Applying backfill changes...")
        try:
            from backfill_tagger import BackfillTagger
            tagger = BackfillTagger()
            tagger.run_backfill(dry_run=False)
            
            print("\n✅ BACKFILL COMPLETE!")
            print("\n📂 Your session logs are now ready for the auto-regen website!")
            print(f"   Location: {Path.cwd() / 'session-logs'}")
            print("\n🔄 Next steps:")
            print("  1. Copy the starter-files to your dev-journey repository")
            print("  2. Add your OpenAI API key to repository secrets")
            print("  3. Commit and push to trigger the auto-generation")
            print("\n🎉 Your development journey website will be live!")
            
        except Exception as e:
            print(f"❌ Backfill failed: {e}")
    else:
        print("\n🏃 Backfill cancelled. Run again when ready!")
        print("\n💡 To apply changes later:")
        print("   python backfill-tagger.py --apply")

if __name__ == "__main__":
    main()