import os, re, shutil, json
from pathlib import Path

FOLDER  = Path.home() / 'Desktop' / 'NEW_FOLDER'
CLEAN   = Path.home() / 'Desktop' / 'MEEKO_CLEAN'
SECRETS = Path.home() / 'Desktop' / 'SECRETS_REVIEW'

CLEAN.mkdir(exist_ok=True)
SECRETS.mkdir(exist_ok=True)

SENSITIVE = re.compile(
    r'(?i)(api[_\s-]?key|apikey|secret|token|password|passwd|bearer|private_key'
    r'|aws_|sk-|pk-|ghp_|xox[pb]-)[^\s\n]{6,}', re.MULTILINE
)
SENSITIVE_EXTS = {'.env', '.pem', '.key', '.secret', '.p12', '.pfx', '.crt'}

results = {'clean': [], 'secrets': [], 'skipped': []}

all_files = sorted(FOLDER.rglob('*'))
total = len([f for f in all_files if f.is_file()])
print(f'Found {total} files. Scanning...')

for f in all_files:
    if not f.is_file():
        continue
    rel = f.relative_to(FOLDER)

    if f.suffix.lower() in SENSITIVE_EXTS:
        dest = SECRETS / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        results['secrets'].append(str(rel))
        continue

    try:
        text = f.read_text(encoding='utf-8', errors='replace')
    except:
        dest = CLEAN / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        results['clean'].append(str(rel))
        continue

    if SENSITIVE.search(text):
        dest = SECRETS / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        results['secrets'].append(str(rel))
    else:
        dest = CLEAN / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        results['clean'].append(str(rel))

print(f'\n✅ DONE')
print(f'   Safe to push:    {len(results["clean"])} files  →  Desktop/MEEKO_CLEAN/')
print(f'   Review first:    {len(results["secrets"])} files  →  Desktop/SECRETS_REVIEW/')
print(f'\nCheck SECRETS_REVIEW/ yourself, then delete it.')
print(f'Then copy MEEKO_CLEAN/ into your repo and push.')

out = Path.home() / 'Desktop' / 'ingestion_prescan.json'
out.write_text(json.dumps(results, indent=2))
print(f'\nFull file list saved to: {out}')
