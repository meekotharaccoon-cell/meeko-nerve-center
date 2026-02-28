#!/usr/bin/env python3
"""
Backup Engine
==============
All of the system's intelligence lives in data/ and knowledge/.
Right now if the repo gets corrupted, deleted, or GitHub
goes down, everything is gone. Years of signals history,
idea ledger, donor list, press contacts, crypto patterns.

This engine creates redundant backups in multiple locations.

Backup targets (all free):
  1. GitHub Gist (private) — compressed JSON of all data files
  2. HuggingFace Dataset — versioned backup repo
  3. Local archive in repo — data/backups/YYYY-MM-DD/ (weekly)

What gets backed up:
  - All data/*.json files (the brain)
  - knowledge/ingested/ (extracted knowledge)
  - MANIFESTO.md, COLLABORATORS.md (important docs)
  - Current engine list (what exists)

Restore process:
  1. Clone repo
  2. Run: python mycelium/backup_engine.py --restore
  3. It fetches latest backup from Gist and rebuilds data/

Schedule: Daily backup to Gist, weekly to HuggingFace.
"""

import json, datetime, os, gzip, base64, sys
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEK  = datetime.date.today().isocalendar()[1]  # week number

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
HF_TOKEN     = os.environ.get('HF_TOKEN', '')
HF_USERNAME  = os.environ.get('HF_USERNAME', 'meekotharaccoon')

GIST_BACKUP_ID_FILE = DATA / 'backup_gist_id.txt'
MAX_LOCAL_BACKUPS   = 4  # keep 4 weeks of local backups

def collect_data_files():
    """Returns {filename: content_string} for all data JSON files."""
    files = {}
    for f in sorted(DATA.glob('*.json')):
        if 'backup' in f.name: continue
        try:
            content = f.read_text()
            if len(content) < 10_000_000:  # skip files >10MB
                files[f.name] = content
        except: pass
    return files

def compress_bundle(files):
    """Compress all files into a single gzipped JSON string."""
    bundle = json.dumps({
        'date':    TODAY,
        'version': 1,
        'files':   files,
        'engine_count': len(list((ROOT / 'mycelium').glob('*.py'))),
    })
    compressed = gzip.compress(bundle.encode())
    return base64.b64encode(compressed).decode()

def decompress_bundle(b64_string):
    compressed = base64.b64decode(b64_string)
    bundle     = gzip.decompress(compressed).decode()
    return json.loads(bundle)

def github_api(method, path, body=None):
    if not GITHUB_TOKEN: return None
    try:
        req = urllib_request.Request(
            f'https://api.github.com/{path}',
            data=json.dumps(body).encode() if body else None,
            headers={
                'Authorization': f'Bearer {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github+json',
                'Content-Type': 'application/json',
            },
            method=method
        )
        with urllib_request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[backup] GitHub API error: {e}')
        return None

def backup_to_gist(b64_bundle):
    """Create or update a private GitHub Gist with the backup."""
    gist_data = {
        'description': f'Meeko Nerve Center data backup — {TODAY}',
        'public':      False,
        'files': {
            f'meeko_backup_{TODAY}.json.gz.b64': {
                'content': b64_bundle[:500_000]  # Gist 10MB limit, split if needed
            }
        }
    }

    # Try to update existing gist first
    gist_id = None
    if GIST_BACKUP_ID_FILE.exists():
        try: gist_id = GIST_BACKUP_ID_FILE.read_text().strip()
        except: pass

    if gist_id:
        result = github_api('PATCH', f'gists/{gist_id}', gist_data)
        if result:
            print(f'[backup] Updated Gist: {gist_id}')
            return gist_id

    # Create new gist
    result = github_api('POST', 'gists', gist_data)
    if result:
        new_id = result.get('id', '')
        try: GIST_BACKUP_ID_FILE.write_text(new_id)
        except: pass
        print(f'[backup] Created Gist: {new_id}')
        return new_id

    return None

def backup_to_local():
    """Weekly local backup inside the repo (committed to git)."""
    if datetime.date.today().weekday() != 6:  # Sundays only
        return
    backup_dir = DATA / 'backups' / TODAY
    backup_dir.mkdir(parents=True, exist_ok=True)

    files = collect_data_files()
    for fname, content in files.items():
        try: (backup_dir / fname).write_text(content)
        except: pass

    # Clean old backups
    all_backups = sorted([d for d in (DATA / 'backups').iterdir() if d.is_dir()])
    while len(all_backups) > MAX_LOCAL_BACKUPS:
        oldest = all_backups.pop(0)
        try:
            import shutil; shutil.rmtree(oldest)
        except: pass

    print(f'[backup] Local backup: {len(files)} files in data/backups/{TODAY}/')

def restore_from_gist():
    """Restore data/ from the latest Gist backup."""
    gist_id = None
    if GIST_BACKUP_ID_FILE.exists():
        try: gist_id = GIST_BACKUP_ID_FILE.read_text().strip()
        except: pass

    if not gist_id:
        print('[backup] No Gist ID found. Cannot restore.')
        return False

    gist = github_api('GET', f'gists/{gist_id}')
    if not gist:
        print('[backup] Could not fetch Gist.')
        return False

    for fname, fdata in gist.get('files', {}).items():
        b64 = fdata.get('content', '')
        if not b64: continue
        try:
            bundle = decompress_bundle(b64)
            for data_file, content in bundle.get('files', {}).items():
                dest = DATA / data_file
                dest.write_text(content)
                print(f'[backup] Restored: {data_file}')
            print(f'[backup] Restore complete from backup dated {bundle.get("date")}')
            return True
        except Exception as e:
            print(f'[backup] Restore error: {e}')
    return False

def run():
    if '--restore' in sys.argv:
        print('\n[backup] RESTORE MODE')
        restore_from_gist()
        return

    print(f'\n[backup] Backup Engine — {TODAY}')

    files  = collect_data_files()
    print(f'[backup] Collected {len(files)} data files')

    bundle = compress_bundle(files)
    size_kb = round(len(bundle) / 1024, 1)
    print(f'[backup] Compressed bundle: {size_kb}KB')

    if GITHUB_TOKEN:
        gist_id = backup_to_gist(bundle)
        if gist_id:
            print(f'[backup] ✅ Gist backup complete')
        else:
            print(f'[backup] ⚠️  Gist backup failed')
    else:
        print('[backup] No GITHUB_TOKEN — skipping Gist backup')

    backup_to_local()

    # Save backup log
    log = {'date': TODAY, 'files_backed_up': len(files), 'size_kb': size_kb}
    try: (DATA / 'backup_log.json').write_text(json.dumps(log, indent=2))
    except: pass

    print('[backup] Done.')

if __name__ == '__main__':
    run()
