#!/usr/bin/env python3
"""
🧠 BUILD_MCP_CONFIG.py — Connect Claude Desktop to YOUR System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run this ONCE on your desktop. It writes the Claude Desktop
MCP config so that Claude opens already knowing:
  - Your entire file system (UltimateAI_Master)
  - Your SQLite databases (gaza_rose.db, master.db)
  - Your GitHub repos (via filesystem)
  - Your system state (CLAUDE_CONTEXT.md)
  - Your scripts and their purposes

After this runs, restart Claude Desktop.
No more cold starts. No more context rebuilding.

Run:
  python BUILD_MCP_CONFIG.py

Then restart Claude Desktop. That's it.
"""

import os
import json
import sys
import shutil
import subprocess
from pathlib import Path

# ─────────────────────────────────────────────
COLORS
# ─────────────────────────────────────────────
G = '\033[92m'; Y = '\033[93m'; C = '\033[96m'; D = '\033[2m'; B = '\033[1m'; X = '\033[0m'
def ok(s):   print(f"{G}  ✓ {s}{X}")
def warn(s): print(f"{Y}  ⚠ {s}{X}")
def info(s): print(f"{C}  → {s}{X}")
def dim(s):  print(f"{D}    {s}{X}")

# ─────────────────────────────────────────────
PATH DETECTION
# ─────────────────────────────────────────────
def find_claude_config_dir():
    """Find where Claude Desktop stores its config"""
    home = Path.home()
    candidates = [
        # Windows
        Path(os.environ.get('APPDATA', '')) / 'Claude',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Claude',
        home / 'AppData' / 'Roaming' / 'Claude',
        # Mac
        home / 'Library' / 'Application Support' / 'Claude',
        # Linux
        home / '.config' / 'Claude',
        home / '.claude',
    ]
    for p in candidates:
        if p.exists():
            return p
    # Default for Windows
    default = Path(os.environ.get('APPDATA', home)) / 'Claude'
    default.mkdir(parents=True, exist_ok=True)
    return default

def find_node():
    for cmd in ['node', 'node.exe']:
        path = shutil.which(cmd)
        if path: return path
    # Common Windows locations
    for p in [r'C:\Program Files\nodejs\node.exe', r'C:\Program Files (x86)\nodejs\node.exe']:
        if Path(p).exists(): return p
    return 'node'

def find_desktop_path():
    home = Path.home()
    candidates = [
        home / 'Desktop' / 'UltimateAI_Master',
        home / 'Desktop',
        home / 'UltimateAI_Master',
    ]
    for p in candidates:
        if p.exists(): return str(p)
    return str(home / 'Desktop')

def find_repo_path():
    home = Path.home()
    candidates = [
        home / 'Desktop' / 'UltimateAI_Master' / 'meeko-nerve-center',
        home / 'Desktop' / 'meeko-nerve-center',
        home / 'meeko-nerve-center',
    ]
    for p in candidates:
        if p.exists(): return str(p)
    return str(home / 'Desktop' / 'UltimateAI_Master' / 'meeko-nerve-center')

def find_db_paths():
    home = Path.home()
    search_roots = [
        home / 'Desktop',
        home / 'Documents',
        home,
    ]
    found = []
    for root in search_roots:
        if root.exists():
            for db in root.rglob('*.db'):
                found.append(str(db))
    return found[:10]  # limit

# ─────────────────────────────────────────────
MCP SERVER INSTALLERS
# ─────────────────────────────────────────────
def install_mcp_servers():
    """Install the MCP servers we need via npx (they auto-install)"""
    servers = [
        ("@modelcontextprotocol/server-filesystem", "File system access"),
        ("@modelcontextprotocol/server-sqlite",     "SQLite database access"),
        ("@modelcontextprotocol/server-github",     "GitHub integration"),
        ("@modelcontextprotocol/server-memory",     "Persistent memory"),
    ]
    print(f"\n{B}Installing MCP servers...{X}")
    for pkg, desc in servers:
        print(f"  Checking {desc}...")
        result = subprocess.run(
            ['npx', '--yes', pkg, '--version'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            ok(f"{pkg}")
        else:
            warn(f"{pkg} (will install on first use via npx)")

# ─────────────────────────────────────────────
BUILD CONFIG
# ─────────────────────────────────────────────
def build_config():
    node = find_node()
    desktop = find_desktop_path()
    repo = find_repo_path()
    dbs = find_db_paths()

    # Filesystem roots to expose
    fs_roots = list(set([
        desktop,
        str(Path.home() / 'Desktop'),
        str(Path.home() / 'Documents'),
        repo,
    ]))
    fs_roots = [r for r in fs_roots if Path(r).exists()]

    config = {
        "mcpServers": {
            # FILESYSTEM — access all your files
            "filesystem": {
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                ] + fs_roots,
                "description": "Full access to your Desktop and project files"
            },

            # MEMORY — persistent memory across sessions
            "memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
                "description": "Persistent memory. Claude remembers things across sessions."
            },

            # GITHUB — direct repo access
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": os.environ.get("GITHUB_TOKEN", "")
                },
                "description": "GitHub integration — read/write repos directly"
            },
        }
    }

    # Add SQLite servers for each DB found
    for i, db_path in enumerate(dbs[:5]):
        db_name = Path(db_path).stem
        config["mcpServers"][f"sqlite_{db_name}"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", db_path],
            "description": f"SQLite: {db_name}"
        }

    return config

# ─────────────────────────────────────────────
WRITE AND VERIFY
# ─────────────────────────────────────────────
def main():
    print(f"\n{B}{G}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{X}")
    print(f"{B}{G}  🧠 BUILD_MCP_CONFIG — Connecting Claude to YOUR system{X}")
    print(f"{B}{G}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{X}\n")

    # Step 1: Find Claude config directory
    config_dir = find_claude_config_dir()
    config_path = config_dir / 'claude_desktop_config.json'
    info(f"Claude config directory: {config_dir}")

    # Step 2: Backup existing config if present
    if config_path.exists():
        backup = config_path.with_suffix('.json.bak')
        shutil.copy(config_path, backup)
        ok(f"Backed up existing config to {backup.name}")

    # Step 3: Detect paths
    desktop = find_desktop_path()
    repo = find_repo_path()
    dbs = find_db_paths()

    info(f"Desktop path:  {desktop}")
    info(f"Repo path:     {repo}")
    if dbs:
        info(f"Databases found: {len(dbs)}")
        for db in dbs:
            dim(db)

    # Step 4: Build config
    config = build_config()
    servers = list(config['mcpServers'].keys())
    info(f"MCP servers configured: {len(servers)}")
    for s in servers:
        dim(s)

    # Step 5: Write config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    ok(f"Config written: {config_path}")

    # Step 6: Check Node.js
    node = find_node()
    node_out, node_code = '', 1
    try:
        result = subprocess.run([node, '--version'], capture_output=True, text=True, timeout=5)
        node_out = result.stdout.strip()
        node_code = result.returncode
    except:
        pass

    if node_code == 0:
        ok(f"Node.js: {node_out}")
    else:
        warn("Node.js not found. MCP servers need Node.js.")
        print(f"  {D}Install from: https://nodejs.org (LTS version){X}")

    # Step 7: Done
    print(f"\n{G}{B}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{X}")
    print(f"{G}{B}  DONE. Now do this:{X}")
    print(f"{G}{B}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{X}")
    print(f"""
  1. {G}Quit Claude Desktop completely{X} (not just close the window)
  2. {G}Reopen Claude Desktop{X}
  3. Start a new conversation
  4. Say: {C}\"Read CLAUDE_CONTEXT.md from the meeko-nerve-center repo and get oriented\"{X}

  Claude will open knowing:
    {D}✓ Your entire file system{X}
    {D}✓ Your databases{X}
    {D}✓ Your repos{X}
    {D}✓ Persistent memory across sessions{X}

  No more cold starts. The system is always oriented.
  {D}Config location: {config_path}{X}
""")

if __name__ == '__main__':
    main()
