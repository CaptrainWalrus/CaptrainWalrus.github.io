#!/usr/bin/env python3
"""
Sync workflow for keeping session logs updated
Monitors workspace claude_memory.md files and syncs to Cohere project
"""

import os
import shutil
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SessionLogSyncHandler(FileSystemEventHandler):
    """File system event handler for syncing session logs"""
    
    def __init__(self, sync_manager):
        self.sync_manager = sync_manager
        self.last_sync = {}  # Track last sync times to avoid duplicate processing
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only process claude_memory.md and CLAUDE.md files
        if file_path.name in ['claude_memory.md', 'CLAUDE.md']:
            # Debounce: only sync if file hasn't been processed in last 5 seconds
            now = time.time()
            if file_path in self.last_sync and (now - self.last_sync[file_path]) < 5:
                return
                
            self.last_sync[file_path] = now
            print(f"📝 Detected change: {file_path}")
            self.sync_manager.sync_file(file_path)

class SessionLogSyncManager:
    """Manages syncing of session logs to Cohere project"""
    
    def __init__(self):
        self.workspace_dir = Path("/mnt/c/workspace")
        self.cohere_dir = Path("/mnt/c/workspace/Cohere")
        self.session_logs_dir = self.cohere_dir / "session-logs"
        self.projects_dir = self.session_logs_dir / "projects"
        
        # Ensure directories exist
        self.session_logs_dir.mkdir(exist_ok=True)
        self.projects_dir.mkdir(exist_ok=True)
    
    def get_project_mapping(self, source_file: Path) -> tuple:
        """Determine project name and destination for a source file"""
        relative_path = source_file.relative_to(self.workspace_dir)
        parts = relative_path.parts
        
        if len(parts) == 1:  # Root level claude_memory.md
            return ("main", self.session_logs_dir / "claude_memory.md")
        
        # Project-specific file
        project_name = parts[0].lower().replace(' ', '-')
        
        # Special handling for known projects
        if project_name == "fluidjournal":
            if "agentic_memory" in str(source_file):
                project_name = "fluidjournal-agentic"
            else:
                project_name = "fluidjournal"
        elif project_name.startswith("vectorbt"):
            project_name = "vectorbt"
        elif project_name == "order-manager":
            project_name = "ninjatrader"
        
        dest_dir = self.projects_dir / project_name
        dest_dir.mkdir(exist_ok=True)
        
        return (project_name, dest_dir / source_file.name)
    
    def sync_file(self, source_file: Path):
        """Sync a single file to the Cohere session logs"""
        try:
            if not source_file.exists():
                print(f"⚠️ Source file no longer exists: {source_file}")
                return
            
            # Get destination
            project_name, dest_file = self.get_project_mapping(source_file)
            
            # Read source content
            content = source_file.read_text(encoding='utf-8')
            
            # Write to destination
            dest_file.write_text(content, encoding='utf-8')
            
            print(f"✅ Synced {project_name}: {source_file} → {dest_file}")
            
            # Update sync timestamp
            timestamp_file = self.session_logs_dir / ".sync_timestamp"
            timestamp_file.write_text(datetime.now().isoformat(), encoding='utf-8')
            
        except Exception as e:
            print(f"❌ Error syncing {source_file}: {e}")
    
    def initial_sync(self):
        """Perform initial sync of all session log files"""
        print("🔄 Performing initial sync...")
        
        # Find all session log files
        session_files = []
        
        # Main workspace files
        for pattern in ["claude_memory.md", "CLAUDE.md"]:
            main_file = self.workspace_dir / pattern
            if main_file.exists():
                session_files.append(main_file)
        
        # Project-specific files
        for item in self.workspace_dir.iterdir():
            if item.is_dir() and item.name != "Cohere":
                for pattern in ["claude_memory.md", "CLAUDE.md"]:
                    # Check root of project
                    project_file = item / pattern
                    if project_file.exists():
                        session_files.append(project_file)
                    
                    # Check subdirectories (recursively, but limited depth)
                    for subdir in item.rglob(pattern):
                        if subdir.is_file():
                            session_files.append(subdir)
        
        print(f"📁 Found {len(session_files)} session files")
        
        # Sync each file
        for source_file in session_files:
            self.sync_file(source_file)
        
        print(f"✅ Initial sync complete!")
    
    def start_monitoring(self):
        """Start monitoring for file changes"""
        print("👀 Starting file system monitoring...")
        
        event_handler = SessionLogSyncHandler(self)
        observer = Observer()
        
        # Monitor the entire workspace (excluding Cohere directory)
        for item in self.workspace_dir.iterdir():
            if item.is_dir() and item.name != "Cohere":
                observer.schedule(event_handler, str(item), recursive=True)
                print(f"   Monitoring: {item}")
        
        # Also monitor root level files
        observer.schedule(event_handler, str(self.workspace_dir), recursive=False)
        
        observer.start()
        
        try:
            print("🔄 Monitoring active. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor...")
            observer.stop()
        
        observer.join()
        print("✅ Monitor stopped.")
    
    def create_pre_commit_hook(self):
        """Create a pre-commit hook script for manual syncing"""
        hook_script = self.workspace_dir / "sync-session-logs.py"
        
        hook_content = f'''#!/usr/bin/env python3
"""
Pre-commit hook script to sync session logs before git commits
Run this before committing to ensure session logs are up to date
"""

import sys
import os
sys.path.append(r"{self.cohere_dir}")

from sync_workflow import SessionLogSyncManager

def main():
    print("🔄 Syncing session logs before commit...")
    
    sync_manager = SessionLogSyncManager()
    sync_manager.initial_sync()
    
    print("✅ Session logs synced! Ready to commit.")

if __name__ == "__main__":
    main()
'''
        
        hook_script.write_text(hook_content, encoding='utf-8')
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod(hook_script, 0o755)
        
        print(f"📜 Created pre-commit script: {hook_script}")
        print(f"   Run before commits: python {hook_script}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync session logs to Cohere project')
    parser.add_argument('--watch', action='store_true', help='Start file monitoring')
    parser.add_argument('--sync', action='store_true', help='Perform one-time sync')
    parser.add_argument('--hook', action='store_true', help='Create pre-commit hook script')
    
    args = parser.parse_args()
    
    sync_manager = SessionLogSyncManager()
    
    if args.hook:
        sync_manager.create_pre_commit_hook()
    elif args.watch:
        sync_manager.initial_sync()
        sync_manager.start_monitoring()
    elif args.sync:
        sync_manager.initial_sync()
    else:
        # Default: show status and options
        print("🔄 Session Log Sync Manager")
        print("Options:")
        print("  --sync    Perform one-time sync of all session logs")
        print("  --watch   Start continuous monitoring and syncing")
        print("  --hook    Create pre-commit hook script")
        print("\nExample usage:")
        print("  python sync-workflow.py --sync")
        print("  python sync-workflow.py --watch")

if __name__ == "__main__":
    main()