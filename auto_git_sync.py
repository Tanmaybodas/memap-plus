#!/usr/bin/env python3
"""
Auto Git Sync - Automatically commit and push changes to Git repository
"""

import os
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import hashlib

class AutoGitSync:
    def __init__(self, repo_path=".", branch="main", remote="origin"):
        self.repo_path = Path(repo_path).resolve()
        self.branch = branch
        self.remote = remote
        self.last_commit_hash = None
        self.watched_files = set()
        
    def run_command(self, cmd, cwd=None):
        """Run a git command and return the result"""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                cwd=cwd or self.repo_path,
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def get_git_status(self):
        """Get current git status"""
        success, stdout, stderr = self.run_command("git status --porcelain")
        if success:
            return stdout.split('\n') if stdout else []
        return []
    
    def get_unstaged_files(self):
        """Get list of unstaged files"""
        status_lines = self.get_git_status()
        unstaged_files = []
        
        for line in status_lines:
            if line.strip():
                status = line[:2]
                filename = line[3:].strip()
                if status.startswith(('M', 'A', 'D', 'R', 'C', 'U')) and not status.endswith(' '):
                    unstaged_files.append(filename)
        
        return unstaged_files
    
    def commit_changes(self, message=None):
        """Commit all changes with automatic message"""
        if not message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Auto-sync: {timestamp}"
        
        # Add all changes
        success, _, stderr = self.run_command("git add .")
        if not success:
            print(f"❌ Failed to stage files: {stderr}")
            return False
        
        # Check if there are changes to commit
        success, stdout, _ = self.run_command("git diff --cached --name-only")
        if not stdout.strip():
            print("ℹ️  No changes to commit")
            return True
        
        # Commit changes
        success, _, stderr = self.run_command(f'git commit -m "{message}"')
        if not success:
            print(f"❌ Failed to commit: {stderr}")
            return False
        
        print(f"✅ Committed changes: {message}")
        return True
    
    def push_changes(self):
        """Push changes to remote repository"""
        success, stdout, stderr = self.run_command(f"git push {self.remote} {self.branch}")
        if not success:
            print(f"❌ Failed to push: {stderr}")
            return False
        
        print(f"✅ Pushed changes to {self.remote}/{self.branch}")
        return True
    
    def sync_once(self):
        """Perform one sync operation"""
        print(f"🔄 Checking for changes in {self.repo_path}")
        
        unstaged_files = self.get_unstaged_files()
        if not unstaged_files:
            print("ℹ️  No changes detected")
            return True
        
        print(f"📝 Found {len(unstaged_files)} changed files:")
        for file in unstaged_files[:5]:  # Show first 5 files
            print(f"   - {file}")
        if len(unstaged_files) > 5:
            print(f"   ... and {len(unstaged_files) - 5} more")
        
        # Commit changes
        if not self.commit_changes():
            return False
        
        # Push changes
        if not self.push_changes():
            return False
        
        return True
    
    def watch_and_sync(self, interval=30):
        """Continuously watch for changes and sync"""
        print(f"🚀 Starting auto-sync (checking every {interval}s)")
        print(f"📁 Watching: {self.repo_path}")
        print(f"🌿 Branch: {self.branch}")
        print(f"🔗 Remote: {self.remote}")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        try:
            while True:
                self.sync_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Auto-sync stopped by user")
        except Exception as e:
            print(f"\n❌ Auto-sync error: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto Git Sync - Automatically sync changes to Git")
    parser.add_argument("--interval", "-i", type=int, default=30, 
                       help="Sync interval in seconds (default: 30)")
    parser.add_argument("--once", "-o", action="store_true", 
                       help="Run sync once instead of watching")
    parser.add_argument("--branch", "-b", default="main", 
                       help="Git branch (default: main)")
    parser.add_argument("--remote", "-r", default="origin", 
                       help="Git remote (default: origin)")
    
    args = parser.parse_args()
    
    sync = AutoGitSync(branch=args.branch, remote=args.remote)
    
    if args.once:
        sync.sync_once()
    else:
        sync.watch_and_sync(args.interval)

if __name__ == "__main__":
    main()
