#!/usr/bin/env python3
"""
File Watcher - Automatically sync to Git when files are modified
"""

import os
import time
import subprocess
from datetime import datetime
from pathlib import Path

class FileWatcher:
    def __init__(self, watch_path=".", ignore_patterns=None):
        self.watch_path = Path(watch_path)
        self.ignore_patterns = ignore_patterns or ['.git', '__pycache__', '.pyc', '.env', 'node_modules']
        self.last_sync_time = time.time()
        self.sync_cooldown = 5  # Minimum seconds between syncs
        
    def should_ignore(self, file_path):
        """Check if file should be ignored"""
        file_path = Path(file_path)
        for pattern in self.ignore_patterns:
            if pattern in str(file_path):
                return True
        return False
    
    def run_git_sync(self):
        """Run git sync commands"""
        try:
            # Check if we're in a git repo
            if not (self.watch_path / '.git').exists():
                return False
                
            # Add all changes
            result = subprocess.run('git add .', shell=True, capture_output=True, text=True, cwd=self.watch_path)
            if result.returncode != 0:
                return False
            
            # Check if there are changes
            result = subprocess.run('git diff --cached --name-only', shell=True, capture_output=True, text=True, cwd=self.watch_path)
            if not result.stdout.strip():
                return True  # No changes, but that's OK
            
            # Commit changes
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_msg = f"Auto-sync: {timestamp}"
            result = subprocess.run(f'git commit -m "{commit_msg}"', shell=True, capture_output=True, text=True, cwd=self.watch_path)
            if result.returncode != 0:
                print(f"Commit failed: {result.stderr}")
                return False
            
            # Push changes
            result = subprocess.run('git push origin main', shell=True, capture_output=True, text=True, cwd=self.watch_path)
            if result.returncode != 0:
                print(f"Push failed: {result.stderr}")
                return False
                
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Synced to Git: {result.stdout.strip()}")
            return True
            
        except Exception as e:
            print(f"Sync error: {e}")
            return False
    
    def get_file_mtime(self, file_path):
        """Get file modification time"""
        try:
            return os.path.getmtime(file_path)
        except:
            return 0
    
    def watch(self):
        """Watch for file changes and auto-sync"""
        print(f"Watching {self.watch_path} for changes...")
        print("Press Ctrl+C to stop")
        
        file_times = {}
        
        try:
            while True:
                changed = False
                
                # Check all files in the directory
                for root, dirs, files in os.walk(self.watch_path):
                    # Skip ignored directories
                    dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
                    
                    for file in files:
                        file_path = Path(root) / file
                        
                        if self.should_ignore(file_path):
                            continue
                            
                        current_time = self.get_file_mtime(file_path)
                        file_str = str(file_path)
                        
                        if file_str in file_times:
                            if current_time > file_times[file_str]:
                                changed = True
                                print(f"File changed: {file_path.name}")
                        
                        file_times[file_str] = current_time
                
                # Sync if changes detected and cooldown passed
                if changed and (time.time() - self.last_sync_time) > self.sync_cooldown:
                    if self.run_git_sync():
                        self.last_sync_time = time.time()
                
                time.sleep(2)  # Check every 2 seconds
                
        except KeyboardInterrupt:
            print("\nStopped watching")

def main():
    watcher = FileWatcher()
    watcher.watch()

if __name__ == "__main__":
    main()
