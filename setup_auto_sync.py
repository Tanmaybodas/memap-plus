#!/usr/bin/env python3
"""
Setup Auto Git Sync for MeMap+
"""

import os
import subprocess
import sys
from pathlib import Path

def check_git_setup():
    """Check if git is properly configured"""
    print("Checking Git setup...")
    
    # Check if git is installed
    try:
        result = subprocess.run('git --version', shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print("Error: Git is not installed")
            return False
        print(f"Git version: {result.stdout.strip()}")
    except:
        print("Error: Git is not available")
        return False
    
    # Check if we're in a git repo
    if not Path('.git').exists():
        print("Error: Not in a git repository")
        return False
    
    # Check git config
    try:
        result = subprocess.run('git config user.name', shell=True, capture_output=True, text=True)
        if not result.stdout.strip():
            print("Warning: Git user.name not set")
            print("Run: git config --global user.name 'Your Name'")
        
        result = subprocess.run('git config user.email', shell=True, capture_output=True, text=True)
        if not result.stdout.strip():
            print("Warning: Git user.email not set")
            print("Run: git config --global user.email 'your.email@example.com'")
    except:
        pass
    
    # Check remote
    try:
        result = subprocess.run('git remote -v', shell=True, capture_output=True, text=True)
        if not result.stdout.strip():
            print("Warning: No remote repository configured")
        else:
            print(f"Remote: {result.stdout.strip()}")
    except:
        pass
    
    return True

def create_shortcuts():
    """Create convenient shortcuts"""
    print("\nCreating shortcuts...")
    
    # Create a simple sync batch file
    batch_content = """@echo off
echo Syncing to Git...
python sync_now.py
pause
"""
    
    with open('quick_sync.bat', 'w') as f:
        f.write(batch_content)
    
    print("Created quick_sync.bat - double-click to sync once")
    
    # Create a watch batch file
    watch_content = """@echo off
echo Starting file watcher...
python watch_and_sync.py
pause
"""
    
    with open('watch_files.bat', 'w') as f:
        f.write(watch_content)
    
    print("Created watch_files.bat - double-click to watch for changes")

def main():
    print("MeMap+ Auto Git Sync Setup")
    print("=" * 40)
    
    if not check_git_setup():
        print("\nPlease fix the Git setup issues above before continuing.")
        return
    
    create_shortcuts()
    
    print("\n" + "=" * 40)
    print("Setup complete! You now have several options:")
    print()
    print("1. Quick Sync (one-time):")
    print("   - Double-click 'quick_sync.bat'")
    print("   - Or run: python sync_now.py")
    print()
    print("2. Watch for changes:")
    print("   - Double-click 'watch_files.bat'")
    print("   - Or run: python watch_and_sync.py")
    print("   - This will automatically sync whenever you save files")
    print()
    print("3. Continuous sync:")
    print("   - Run: python auto_git_sync.py")
    print("   - Checks for changes every 30 seconds")
    print()
    print("4. Manual sync:")
    print("   - Run: python sync_now.py")
    print()
    print("All changes will be automatically committed and pushed to your GitHub repository!")

if __name__ == "__main__":
    main()
