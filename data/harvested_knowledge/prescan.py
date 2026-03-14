import os, re, shutil, json
from pathlib import Path

FOLDER  = Path.home() / 'Desktop' / 'NEW_FOLDER'
CLEAN   = Path.home() / 'Desktop' / 'MEEKO_CLEAN'
SECRETS = Path.home() / 'Desktop' / 'SECRETS_REVIEW'

CLEAN.mkdir(exist_ok=True)
SECRETS.mkdir(exist_ok=True)

SENSITIVE = re.compile(
    r'(?i)(api[_\s-]?key|apikey|secret|token|password|passwd|bearer|private_key|aws_|sk-|pk-|ghp_|xox[pb]-)[^\s\n]{6,}',
    re.MULTILINE
)
SENSITIVE_EXTS = {'.env', '.pem', '.key', '.secret', '.p12', '.pfx', '.crt'}

results = {'clean': [], 'secrets': []}
all_files = [f for f in FOLDER.rglob('*') if f.is_file()]
print(f'Found {len(all_files)} files. Scanning...')

for f in all_files:
    rel = f.relative_to(FOLDER)
    if f.suffix.lower() in SENSITIVE_EXTS:
        dest = SECRETS / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        results['secrets'].append(str(rel))
        continue
    try:
        text = f.read_text(encoding='utf-8', errors='replace')
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
    except:
        dest = CLEAN / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        results['clean'].append(str(rel))

print(f'\nDONE')
print(f'  Safe to push:  {len(results["clean"])} files  ->  Desktop/MEEKO_CLEAN/')
print(f'  Review first:  {len(results["secrets"])} files  ->  Desktop/SECRETS_REVIEW/')
Path(Path.home() / 'Desktop' / 'ingestion_prescan.json').write_text(json.dumps(results, indent=2))
print(f'\nFull list saved to Desktop/ingestion_prescan.json')