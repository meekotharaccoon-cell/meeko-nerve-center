#!/usr/bin/env python3
"""
DESKTOP CLEANER v2 — Knows Your Actual Machine
================================================
Scans C:\\Users\\meeko\\Desktop and organizes intelligently.

What it does:
  - Consolidates 5+ BACKUP dirs into one BACKUPS\ folder
  - Moves all *_report_*.json and health_report_*.json into Reports\
  - Moves all _ prefixed temp/one-off scripts into _Archive\
  - Moves old versioned files (v14.py, (1).py, (2).py) into _Archive\
  - Moves logs (.log, .txt reports) into Logs\
  - Consolidates all .lnk shortcuts into Shortcuts\
  - Keeps EVOLVE.bat, COMMAND_CENTER.bat at root
  - Keeps UltimateAI_Master\ at root
  - Reports every single action — nothing silent
  - Writes cleanup summary to data/

NEVER deletes without explicit flag. Safe by default.
"""
import os, shutil, json, re
from pathlib import Path
from datetime import datetime, timezone

DESKTOP  = Path(r'C:\Users\meeko\Desktop')
DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / 'desktop_clean_log.json'

# ---- FOLDER STRUCTURE (minimum folders) -------------------------
FOLDERS = {
    'backups':   DESKTOP / 'BACKUPS',
    'reports':   DESKTOP / 'Reports',
    'archive':   DESKTOP / '_Archive',
    'logs':      DESKTOP / 'Logs',
    'shortcuts': DESKTOP / 'Shortcuts',
    'art':       DESKTOP / 'Art',
    'trading':   DESKTOP / 'Finance',
}

# ---- RULES -------------------------------------------------------

# Files/dirs to NEVER touch
PROTECT = {
    'EVOLVE.bat', 'COMMAND_CENTER.bat', 'LAUNCH.bat',
    'UltimateAI_Master', 'mycelium_env',
    'BACKUPS', 'Reports', '_Archive', 'Logs', 'Shortcuts', 'Art', 'Finance',
    '.brave_debug_profile', '.chainlit', '.files',
    'INVESTMENT_HQ', 'TRADING_SYSTEM', 'SOLARPUNK_AUTONOMOUS',
    'atomic-agents-conductor', 'AtomicMycelium-Portable',
    'PRODUCTS', 'New', 'notepad_all',
    'GAZA_ROSE_GALLERY', 'GAZA_ROSE_OMNI',
    'My Gaza Rose designs',
    'desktop.ini',
}

# Pattern matchers
def is_backup_dir(name):
    return bool(re.match(r'BACKUP_\d+', name))

def is_report_file(name):
    return bool(re.match(r'(daily_report|health_report|system_report).*\.(json|txt)', name, re.I))

def is_archive_script(name):
    # Underscore-prefixed one-off scripts
    return name.startswith('_') and name.endswith('.py')

def is_old_version(name):
    # Files like ultimate_ai_self (1).py, v14.py
    return bool(re.search(r'(\(\d+\)|_v\d+)\.py$', name, re.I))

def is_log_file(name):
    return bool(re.match(r'.*(cleanup|log|events).*\.(log|jsonl|txt)$', name, re.I))

def is_shortcut(name):
    return name.endswith('.lnk') or name.endswith('.url')

def is_art_related(name):
    return 'GAZA' in name.upper() or 'ART' in name.upper() or 'ROSE' in name.upper()

# ---- MAIN -------------------------------------------------------

def run():
    print('\n' + '='*56)
    print('  DESKTOP CLEANER v2')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('  Target:', DESKTOP)
    print('='*56)

    if not DESKTOP.exists():
        print('  Desktop not found on this machine. Skipping.')
        return

    # Create folders
    for key, folder in FOLDERS.items():
        folder.mkdir(exist_ok=True)

    moved   = []
    skipped = []
    errors  = []

    items = sorted(DESKTOP.iterdir(), key=lambda x: x.name)

    for item in items:
        name = item.name

        # Protected — never touch
        if name in PROTECT or any(p in name for p in {'UltimateAI_Master'}):
            continue

        dest = None
        reason = ''

        # BACKUP dirs → BACKUPS\
        if item.is_dir() and is_backup_dir(name):
            dest = FOLDERS['backups'] / name
            reason = 'backup directory'

        # Report JSON/txt files → Reports\
        elif item.is_file() and is_report_file(name):
            dest = FOLDERS['reports'] / name
            reason = 'report file'

        # Underscore temp scripts → _Archive\
        elif item.is_file() and is_archive_script(name):
            dest = FOLDERS['archive'] / name
            reason = 'temp/one-off script'

        # Old versioned scripts → _Archive\
        elif item.is_file() and is_old_version(name):
            dest = FOLDERS['archive'] / name
            reason = 'old version'

        # Log/event files → Logs\
        elif item.is_file() and is_log_file(name):
            dest = FOLDERS['logs'] / name
            reason = 'log file'

        # Shortcuts → Shortcuts\
        elif item.is_file() and is_shortcut(name):
            dest = FOLDERS['shortcuts'] / name
            reason = 'shortcut'

        # Gaza/Art bat files → Art\
        elif item.is_file() and is_art_related(name) and name.endswith('.bat'):
            if name not in PROTECT:
                dest = FOLDERS['art'] / name
                reason = 'art-related bat'

        if dest:
            if dest.exists():
                skipped.append({'file': name, 'reason': f'already at {dest.name}'})
            else:
                try:
                    shutil.move(str(item), str(dest))
                    print(f'  [MOVE]  {name}')
                    print(f'          → {dest.parent.name}\\')
                    moved.append({'file': name, 'to': str(dest.relative_to(DESKTOP)), 'reason': reason})
                except Exception as e:
                    print(f'  [ERR]   {name}: {e}')
                    errors.append({'file': name, 'error': str(e)})

    # Remove empty created folders
    for folder in FOLDERS.values():
        try:
            if folder.exists() and not any(folder.iterdir()):
                folder.rmdir()
                print(f'  [RMDIR] Empty folder removed: {folder.name}')
        except: pass

    # Summary
    print(f'\n  Moved:   {len(moved)}')
    print(f'  Skipped: {len(skipped)}')
    print(f'  Errors:  {len(errors)}')

    # Remaining loose files on desktop
    remaining = [x.name for x in DESKTOP.iterdir() if x.is_file() and x.name != 'desktop.ini']
    print(f'  Loose files remaining: {len(remaining)}')
    for r in remaining:
        print(f'    • {r}')

    # Log
    try:
        log = json.loads(LOG_FILE.read_text()) if LOG_FILE.exists() else {'runs': []}
    except:
        log = {'runs': []}

    log['runs'].append({
        'at': datetime.now(timezone.utc).isoformat(),
        'moved': len(moved),
        'moved_files': moved,
        'errors': errors,
    })
    LOG_FILE.write_text(json.dumps(log, indent=2))
    print(f'  Log: {LOG_FILE}')
    print('  ✓ Desktop clean complete')
    return moved, skipped, errors

if __name__ == '__main__':
    run()
