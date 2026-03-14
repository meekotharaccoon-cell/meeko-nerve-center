import os, re, shutil, json, hashlib, sys
from pathlib import Path

FOLDER  = Path.home() / 'Desktop' / 'NEW_FOLDER'
CLEAN   = Path.home() / 'Desktop' / 'MEEKO_CLEAN'
SECRETS = Path.home() / 'Desktop' / 'SECRETS_REVIEW'

CLEAN.mkdir(exist_ok=True)
SECRETS.mkdir(exist_ok=True)

SENSITIVE = re.compile(
    r'(sk_live_[\w]{20,}'
    r'|sk_test_[\w]{20,}'
    r'|pk_live_[\w]{20,}'
    r'|rk_live_[\w]{20,}'
    r'|ghp_[\w]{36}'
    r'|sk-[a-zA-Z0-9]{32,}'
    r'|xox[bp]-[\w\-]+'
    r'|(?i)api[_\s-]?key[\s:=]+[\w\-]{16,}'
    r'|(?i)secret[\s:=]+[\w\-\.]{8,}'
    r'|(?i)password[\s:=]+[\S]{8,}'
    r'|(?i)bearer\s+[\w\-\.]{20,})',
    re.MULTILINE
)
SENSITIVE_EXTS = {'.env', '.pem', '.key', '.secret', '.p12', '.pfx', '.crt', '.ps1'}
SKIP_EXTS      = {'.exe', '.dll', '.zip', '.tar', '.gz', '.rar', '.pyc',
                  '.mp3', '.mp4', '.avi', '.mov', '.db', '.sqlite', '.iso'}

def safe_copy(src, dest_dir, rel):
    """Copy file, flattening path if too long for Windows."""
    dest = dest_dir / rel
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    except OSError:
        # Path too long - flatten to single level with hash
        hsh  = hashlib.md5(str(rel).encode()).hexdigest()[:8]
        flat = dest_dir / f'{src.stem[:40]}_{hsh}{src.suffix}'
        try:
            shutil.copy2(src, flat)
        except:
            pass  # Truly unreadable, skip

results = {'clean': [], 'secrets': [], 'skipped': []}

try:
    all_files = [f for f in FOLDER.rglob('*') if f.is_file()]
except Exception as e:
    print(f'Error reading folder: {e}')
    sys.exit(1)

total = len(all_files)
print(f'Found {total:,} files. Scanning...')

for i, f in enumerate(all_files):
    if i % 5000 == 0 and i > 0:
        pct = round(i/total*100, 1)
        print(f'  {i:,}/{total:,} ({pct}%) ...')

    ext = f.suffix.lower()
    try:
        rel = f.relative_to(FOLDER)
    except:
        continue

    if ext in SKIP_EXTS:
        results['skipped'].append(str(rel))
        continue

    if ext in SENSITIVE_EXTS:
        safe_copy(f, SECRETS, rel)
        results['secrets'].append(str(rel))
        continue

    try:
        text = f.read_text(encoding='utf-8', errors='replace')
        if SENSITIVE.search(text):
            safe_copy(f, SECRETS, rel)
            results['secrets'].append(str(rel))
        else:
            safe_copy(f, CLEAN, rel)
            results['clean'].append(str(rel))
    except:
        safe_copy(f, CLEAN, rel)
        results['clean'].append(str(rel))

print(f'\n{"="*50}')
print(f'DONE')
print(f'  Safe to push:  {len(results["clean"]):,} files  ->  Desktop/MEEKO_CLEAN/')
print(f'  Review first:  {len(results["secrets"]):,} files  ->  Desktop/SECRETS_REVIEW/')
print(f'  Skipped:       {len(results["skipped"]):,} binary/media files')

out = Path.home() / 'Desktop' / 'ingestion_prescan.json'
out.write_text(json.dumps(results, indent=2))
print(f'\nFull list: Desktop/ingestion_prescan.json')
print(f'\nNEXT: review SECRETS_REVIEW/ then delete it, then push MEEKO_CLEAN/ to repo')