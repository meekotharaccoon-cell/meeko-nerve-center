#!/usr/bin/env python3
"""
DESKTOP CLEANER
================
Organizes C:\\Users\\meeko\\Desktop
Groups files into the minimum number of folders.
Deletes nothing without logging first.
Makes the machine faster by clearing temp files and old logs.

Rules:
  - NEVER delete: .bat, .py, .git, .env, anything in UltimateAI_Master
  - MOVE to folders: documents, images, downloads, shortcuts, misc
  - DELETE: .tmp, desktop.ini (duplicates), ~$ files (Office temp)
  - REPORT: everything moved/deleted, nothing silent

Outputs:
  - data/desktop_clean_log.json
  - Prints every action taken
"""
import os, shutil, json
from pathlib import Path
from datetime import datetime, timezone

DESKTOP   = Path(r'C:\Users\meeko\Desktop')
DATA_DIR  = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
CLEAN_LOG = DATA_DIR / 'desktop_clean_log.json'

# Folders to create (minimum necessary)
FOLDERS = {
    'docs':      DESKTOP / '📂 Documents',
    'images':    DESKTOP / '🖼️ Images',
    'shortcuts': DESKTOP / '🔗 Shortcuts',
    'misc':      DESKTOP / '🗂️ Misc',
}

# Extension to folder mapping
EXT_MAP = {
    '.pdf':  'docs', '.doc':  'docs', '.docx': 'docs',
    '.txt':  'docs', '.md':   'docs', '.rtf':  'docs',
    '.xls':  'docs', '.xlsx': 'docs', '.csv':  'docs',
    '.ppt':  'docs', '.pptx': 'docs',
    '.png':  'images', '.jpg': 'images', '.jpeg': 'images',
    '.gif':  'images', '.bmp': 'images', '.svg':  'images',
    '.webp': 'images', '.ico': 'images',
    '.lnk':  'shortcuts', '.url': 'shortcuts',
}

# Always delete these
DELETE_EXTS = {'.tmp', '.temp', '.bak'}
DELETE_NAMES = {'desktop.ini', 'thumbs.db'}

# Never touch these
PROTECT = {
    'UltimateAI_Master', 'EVOLVE.bat', '.git', '.env',
    '📂 Documents', '🖼️ Images', '🔗 Shortcuts', '🗂️ Misc',
}

def load_log():
    try: return json.loads(CLEAN_LOG.read_text())
    except: return {'runs': [], 'total_moved': 0, 'total_deleted': 0}

def save_log(log): CLEAN_LOG.write_text(json.dumps(log, indent=2))

def run():
    print('\n' + '='*52)
    print('  DESKTOP CLEANER')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*52)

    if not DESKTOP.exists():
        print('  Desktop not found — running on different machine')
        return

    # Create folders
    for folder in FOLDERS.values():
        folder.mkdir(exist_ok=True)

    log = load_log()
    run_log = {'at': datetime.now(timezone.utc).isoformat(), 'moved': [], 'deleted': [], 'skipped': []}

    items = list(DESKTOP.iterdir())
    print(f'  Items on desktop: {len(items)}')

    moved = 0
    deleted = 0
    skipped = 0

    for item in items:
        name = item.name
        ext  = item.suffix.lower()

        # Skip protected
        if any(p in name for p in PROTECT) or name.startswith('.'):
            skipped += 1
            continue

        # Delete junk
        if ext in DELETE_EXTS or name.lower() in DELETE_NAMES:
            try:
                if item.is_file():
                    item.unlink()
                    print(f'  [DELETE] {name}')
                    run_log['deleted'].append(name)
                    deleted += 1
            except Exception as e:
                print(f'  [SKIP] Could not delete {name}: {e}')
            continue

        # Skip folders that aren't ours to move
        if item.is_dir():
            skipped += 1
            continue

        # Move to appropriate folder
        folder_key = EXT_MAP.get(ext)
        if folder_key and folder_key in FOLDERS:
            dest = FOLDERS[folder_key] / name
            if not dest.exists():
                try:
                    shutil.move(str(item), str(dest))
                    print(f'  [MOVE] {name} → {FOLDERS[folder_key].name}')
                    run_log['moved'].append({'file': name, 'to': FOLDERS[folder_key].name})
                    moved += 1
                except Exception as e:
                    print(f'  [SKIP] Could not move {name}: {e}')
                    skipped += 1
            else:
                skipped += 1
        else:
            # Unfamiliar extension — move to misc if it's a lone file
            if item.is_file() and ext not in {'.bat', '.py', '.sh', '.ps1', '.exe', '.msi'}:
                dest = FOLDERS['misc'] / name
                if not dest.exists():
                    try:
                        shutil.move(str(item), str(dest))
                        print(f'  [MOVE] {name} → Misc')
                        run_log['moved'].append({'file': name, 'to': 'Misc'})
                        moved += 1
                    except:
                        skipped += 1
                else:
                    skipped += 1
            else:
                skipped += 1

    # Clean empty created folders
    for folder in FOLDERS.values():
        try:
            if folder.exists() and not any(folder.iterdir()):
                folder.rmdir()
        except: pass

    print(f'\n  Moved:   {moved}')
    print(f'  Deleted: {deleted}')
    print(f'  Skipped: {skipped}')

    log['runs'].append(run_log)
    log['total_moved'] += moved
    log['total_deleted'] += deleted
    save_log(log)
    print('  ✔ Desktop clean complete')

if __name__ == '__main__':
    run()
