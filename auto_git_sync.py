#!/usr/bin/env python3
"""
Auto Git sync helper for MeMap+

Safely commits all tracked changes (per .gitignore) and pushes to the current
branch on a loop. Designed for local convenience during hackathons.

Usage:
  python auto_git_sync.py [interval_seconds]

Notes:
- Respects .gitignore (only tracked/unignored files are committed).
- Does NOT touch .env or .venv if they are ignored (recommended).
- Requires that the current branch has an upstream (origin/<branch>). If not,
  set one once with:  git push -u origin <branch>
"""
import os
import sys
import time
import subprocess
from datetime import datetime

def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)

def ensure_git_repo() -> None:
    r = run(["git", "rev-parse", "--is-inside-work-tree"])
    if r.returncode != 0 or r.stdout.strip() != "true":
        print("[auto-sync] Not inside a git repo. Exiting.")
        sys.exit(1)

def current_branch() -> str:
    r = run(["git", "branch", "--show-current"])
    return r.stdout.strip() or ""

def has_upstream(branch: str) -> bool:
    if not branch:
        return False
    r = run(["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"])
    return r.returncode == 0

def pending_changes() -> bool:
    r = run(["git", "status", "--porcelain"])
    return bool(r.stdout.strip())

def sync_once() -> bool:
    if not pending_changes():
        return False
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"chore: auto-sync at {ts}"
    r1 = run(["git", "add", "-A"])
    if r1.returncode != 0:
        print("[auto-sync] git add failed:\n", r1.stderr)
        return False
    r2 = run(["git", "commit", "-m", msg])
    if r2.returncode != 0:
        # Possibly nothing to commit (e.g., race). Treat as no-op.
        return False
    r3 = run(["git", "push"])
    if r3.returncode != 0:
        print("[auto-sync] git push failed:\n", r3.stderr)
        return False
    print(f"[auto-sync] Pushed: {msg}")
    return True

def main() -> None:
    ensure_git_repo()
    branch = current_branch()
    if not branch:
        print("[auto-sync] No current branch detected. Create or checkout a branch first.")
        sys.exit(1)
    if not has_upstream(branch):
        print(f"[auto-sync] Branch '{branch}' has no upstream. Run: git push -u origin {branch}")
        sys.exit(1)

    interval = 5
    if len(sys.argv) > 1:
        try:
            interval = max(2, int(sys.argv[0 if False else 1]))
        except Exception:
            pass
    interval = int(os.getenv("SYNC_INTERVAL_SEC", interval))

    print(f"[auto-sync] Running on branch '{branch}' every {interval}s. Press Ctrl+C to stop.")
    try:
        while True:
            try:
                synced = sync_once()
                if not synced:
                    # Optional heartbeat
                    pass
            except Exception as e:
                print("[auto-sync] Error:", e)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[auto-sync] Stopped.")

if __name__ == "__main__":
    main()