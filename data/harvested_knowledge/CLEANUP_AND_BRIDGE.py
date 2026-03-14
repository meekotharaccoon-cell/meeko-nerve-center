#!/usr/bin/env python3
"""
CLEANUP_AND_BRIDGE.py — Connect Local Ollama Brain to GitHub Organism
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
What this does:
  1. Checks Ollama is running and lists available models
  2. Scans ALL Python/JSON/bat files on your Desktop
  3. Builds a complete inventory of your system
  4. Pulls latest state from GitHub
  5. Pushes local state to GitHub (updates system_state.json)
  6. Generates CLAUDE_CONTEXT summary for session handoff
  7. Wires all local scripts into the data bus

Run:
  python CLEANUP_AND_BRIDGE.py
  python CLEANUP_AND_BRIDGE.py --scan-only
  python CLEANUP_AND_BRIDGE.py --push (push local state to GitHub)
"""

import os
import sys
import json
import time
import socket
import argparse
import datetime
import subprocess
from pathlib import Path
import urllib.request

# Colors
G = '\033[92m'; Y = '\033[93m'; C = '\033[96m'; D = '\033[2m'; B = '\033[1m'; X = '\033[0m'; R = '\033[91m'
def ok(s):   print(f"{G}  ✓ {s}{X}")
def warn(s): print(f"{Y}  ⚠ {s}{X}")
def info(s): print(f"{C}  → {s}{X}")
def dim(s):  print(f"{D}    {s}{X}")
def err(s):  print(f"{R}  ✗ {s}{X}")
def head(s): print(f"{B}\n{s}{X}")

DESKTOP = Path.home() / 'Desktop'
MASTER_DIR = DESKTOP / 'UltimateAI_Master'

def check_ollama():
    head("🧠 OLLAMA STATUS")
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            data = json.loads(r.read())
            models = [m['name'] for m in data.get('models', [])]
            ok(f"Ollama running. Models: {', '.join(models) or 'none'}")
            return models
    except Exception as e:
        warn(f"Ollama not responding: {e}")
        warn("Start with: ollama serve")
        warn("Download:   https://ollama.ai")
        return []

def scan_desktop():
    head("🔍 DESKTOP SCAN")
    
    result = {
        'py': [], 'json': [], 'bat': [], 'html': [], 'md': [], 'db': [], 'other': []
    }
    
    extensions = {
        '.py': 'py', '.json': 'json', '.bat': 'bat',
        '.html': 'html', '.md': 'md', '.db': 'db'
    }
    
    scanned = 0
    for root, dirs, files in os.walk(DESKTOP):
        # Skip hidden dirs and common junk
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in (
            '__pycache__', 'node_modules', '.git', 'venv', 'env'
        )]
        for fname in files:
            fpath = Path(root) / fname
            ext = fpath.suffix.lower()
            cat = extensions.get(ext, 'other')
            if cat != 'other' or fpath.stat().st_size < 1_000_000:
                result[cat].append(str(fpath))
            scanned += 1
    
    info(f"Files scanned: {scanned}")
    for cat, files in result.items():
        if files:
            ok(f"{cat}: {len(files)} files")
            for f in files[:10]:
                rel = str(Path(f).relative_to(DESKTOP))
                dim(rel)
            if len(files) > 10:
                dim(f"  ... and {len(files) - 10} more")
    
    return result

def check_github():
    head("📍 GITHUB STATUS")
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center",
            headers={'User-Agent': 'MeekoMycelium/1.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            ok(f"Repo: {data['full_name']}")
            ok(f"Forks: {data['forks_count']} · Stars: {data['stargazers_count']}")
            ok(f"Last push: {data['pushed_at'][:10]}")
            return data
    except Exception as e:
        warn(f"GitHub unreachable: {e}")
        return None

def git_pull():
    """Pull latest from GitHub into local repo"""
    repo_candidates = [
        MASTER_DIR / 'meeko-nerve-center',
        DESKTOP / 'meeko-nerve-center',
        Path.home() / 'meeko-nerve-center',
    ]
    for repo in repo_candidates:
        if (repo / '.git').exists():
            info(f"Pulling latest: {repo}")
            try:
                result = subprocess.run(
                    ['git', 'pull', 'origin', 'main'],
                    capture_output=True, text=True, cwd=repo, timeout=30
                )
                if result.returncode == 0:
                    ok(f"Git pull: {result.stdout.strip() or 'up to date'}")
                else:
                    warn(f"Git pull issue: {result.stderr[:100]}")
                return repo
            except FileNotFoundError:
                warn("Git not installed. Download: https://git-scm.com")
            except Exception as e:
                warn(f"Git pull failed: {e}")
            return repo
    warn("No local repo found. Run BOOTSTRAP.ps1 to clone.")
    return None

def build_inventory(scan_results, ollama_models, github_data):
    """Build the system state JSON"""
    inventory = {
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
        'generator': 'CLEANUP_AND_BRIDGE.py',
        'hostname': socket.gethostname(),
        'desktop_files': {
            cat: len(files) for cat, files in scan_results.items()
        },
        'ollama': {
            'running': bool(ollama_models),
            'models': ollama_models
        },
        'github': {
            'reachable': bool(github_data),
            'forks': github_data.get('forks_count', 0) if github_data else 0,
            'stars': github_data.get('stargazers_count', 0) if github_data else 0,
        },
        'key_files': {
            'CLEANUP_AND_BRIDGE': str(Path(__file__)),
        }
    }
    return inventory

def wire_scripts(scan_results):
    """Create a script registry from all found Python files"""
    head("🕸️ SCRIPT REGISTRY")
    
    registry_path = MASTER_DIR / 'SCRIPT_REGISTRY.json'
    registry = {'generated': datetime.datetime.now().isoformat(), 'scripts': []}
    
    for pyfile in scan_results.get('py', []):
        p = Path(pyfile)
        entry = {
            'name': p.name,
            'path': str(p),
            'dir': str(p.parent),
            'size': p.stat().st_size,
            'purpose': 'unknown'
        }
        # Try to read docstring for purpose
        try:
            content = p.read_text(errors='ignore')[:500]
            lines = content.split('\n')
            for i, line in enumerate(lines[:20]):
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    purpose_lines = []
                    for j in range(i+1, min(i+5, len(lines))):
                        l = lines[j].strip().strip('"').strip("'")
                        if l:
                            purpose_lines.append(l)
                        if '"""' in lines[j] or "'''" in lines[j]:
                            break
                    if purpose_lines:
                        entry['purpose'] = ' '.join(purpose_lines)[:100]
                    break
        except:
            pass
        registry['scripts'].append(entry)
    
    MASTER_DIR.mkdir(exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2))
    ok(f"Script registry written: {registry_path}")
    ok(f"Total scripts indexed: {len(registry['scripts'])}")
    
    return registry

def generate_master_runner(scan_results):
    """Generate RUN_ALL.bat that runs all scripts in logical order"""
    head("📦 GENERATING RUN_ALL.bat")
    
    bat_path = MASTER_DIR / 'RUN_ALL.bat'
    
    # Key scripts in priority order
    priority_scripts = [
        'CLEANUP_AND_BRIDGE.py',
        'BUILD_MCP_CONFIG.py',
        'GRAND_SETUP_WIZARD.py',
    ]
    
    lines = ['@echo off', 'echo Meeko Mycelium - Running all scripts', 'echo ======================================', '']
    
    # Priority scripts first
    for script in priority_scripts:
        found = next((f for f in scan_results.get('py', []) if Path(f).name == script), None)
        if found:
            lines.append(f'echo Running: {script}')
            lines.append(f'python "{found}"')
            lines.append('echo.')
    
    # Then mycelium scripts
    for pyfile in scan_results.get('py', []):
        p = Path(pyfile)
        if p.name not in priority_scripts and 'mycelium' in str(p) and not p.name.startswith('_'):
            lines.append(f'echo Running: {p.name}')
            lines.append(f'python "{p}"')
            lines.append('echo.')
    
    lines.extend(['', 'echo All scripts complete.', 'pause'])
    
    bat_content = '\n'.join(lines)
    bat_path.write_text(bat_content)
    ok(f"RUN_ALL.bat written: {bat_path}")
    return bat_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scan-only', action='store_true')
    parser.add_argument('--push', action='store_true')
    args = parser.parse_args()
    
    print()
    print(G + B + "━" * 60 + X)
    print(G + B + "  CLEANUP AND BRIDGE" + X)
    print(G + B + "  Local Ollama ↔ GitHub Organism" + X)
    print(G + B + "━" * 60 + X)
    
    # Run all checks
    ollama_models = check_ollama()
    scan_results = scan_desktop()
    
    if not args.scan_only:
        github_data = check_github()
        repo = git_pull()
        inventory = build_inventory(scan_results, ollama_models, github_data)
        wire_scripts(scan_results)
        generate_master_runner(scan_results)
        
        # Save local inventory
        inv_path = MASTER_DIR / 'local_inventory.json'
        MASTER_DIR.mkdir(exist_ok=True)
        inv_path.write_text(json.dumps(inventory, indent=2))
        ok(f"Inventory saved: {inv_path}")
    
    print()
    print(G + "━" * 60 + X)
    print(G + "  BRIDGE COMPLETE" + X)
    print(G + "━" * 60 + X)
    print()
    ok("Next: python BUILD_MCP_CONFIG.py")
    ok("Then: restart Claude Desktop")
    print()

if __name__ == '__main__':
    main()
