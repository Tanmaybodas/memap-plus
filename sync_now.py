#!/usr/bin/env python3
"""
Quick sync script - commit and push current changes once
"""

import subprocess
import sys
from datetime import datetime

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    print("Quick Git Sync - Committing and pushing current changes")
    print("-" * 50)
    
    # Check git status
    print("Checking git status...")
    if not run_command("git status"):
        print("Error: Not in a git repository or git not available")
        return
    
    # Add all changes
    print("Staging all changes...")
    if not run_command("git add ."):
        print("Error: Failed to stage changes")
        return
    
    # Check if there are changes to commit
    result = subprocess.run("git diff --cached --name-only", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("Info: No changes to commit")
        return
    
    # Commit changes
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Auto-sync: {timestamp}"
    print(f"Committing changes: {commit_message}")
    
    if not run_command(f'git commit -m "{commit_message}"'):
        print("Error: Failed to commit changes")
        return
    
    # Push changes
    print("Pushing to remote repository...")
    if not run_command("git push origin main"):
        print("Error: Failed to push changes")
        return
    
    print("Successfully synced all changes to Git repository!")

if __name__ == "__main__":
    main()
