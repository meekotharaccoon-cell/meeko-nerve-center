#!/usr/bin/env python3
"""
🧠 UPDATE STATE — Auto-updates CLAUDE_CONTEXT.md
Runs after any significant system change to keep the brain file current.
Can be triggered manually or by GitHub Actions.

Usage:
  python mycelium/update_state.py
"""

import json
import os
import datetime
import subprocess
from pathlib import Path

def get_git_info():
    try:
        last_commit = subprocess.check_output(['git', 'log', '-1', '--format=%s|%ci'], text=True).strip()
        msg, date = last_commit.split('|')
        file_count = subprocess.check_output(['git', 'ls-files', '--', '*.py', '*.html', '*.md', '*.yml'], text=True).strip().count('\n') + 1
        return {"last_commit": msg.strip(), "last_commit_date": date.strip(), "tracked_files": file_count}
    except:
        return {"last_commit": "unknown", "last_commit_date": "unknown", "tracked_files": 0}

def update_context():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    git = get_git_info()

    # Read existing context
    ctx_path = Path("CLAUDE_CONTEXT.md")
    if ctx_path.exists():
        content = ctx_path.read_text()
        # Update the last-updated line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('*Auto-updated'):
                lines[i] = f'*Auto-updated by the system. Last update: {now} — {git["last_commit"]}*'
                break
        ctx_path.write_text('\n'.join(lines))
        print(f"✓ CLAUDE_CONTEXT.md updated: {now}")
    else:
        print("✗ CLAUDE_CONTEXT.md not found")

    # Also write a machine-readable state file
    state = {
        "updated": now,
        "last_commit": git["last_commit"],
        "last_commit_date": git["last_commit_date"],
        "tracked_files": git["tracked_files"],
        "system": "meeko-nerve-center",
        "status": "ACTIVE",
        "gmail_secret": "MISSING",
        "local_bridge": "NOT_YET_RUN",
        "mcp_config": "NOT_YET_RUN",
    }
    state_path = Path("data/system_state.json")
    state_path.parent.mkdir(exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2))
    print(f"✓ data/system_state.json written")

if __name__ == "__main__":
    update_context()
