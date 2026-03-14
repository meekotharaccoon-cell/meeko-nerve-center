#!/usr/bin/env python3
"""
ASSET SCANNER
==============
Scans the local machine and GitHub repos for ALL assets.
Finds things the GitHub system doesn't know about locally.
Finds local scripts that SHOULD be pushed but aren't.
Finds knowledge (JSON, db, txt) that could feed the system.
Builds a complete map of what exists and what's connected.

Outputs: data/asset_map.json, data/local_assets.md

No APIs. Reads local filesystem only.
"""
import os, json, sqlite3, re
from pathlib import Path
from datetime import datetime, timezone

DESKTOP  = Path(r'C:\Users\meeko\Desktop')
REPO     = Path(__file__).parent.parent
DATA_DIR = REPO / 'data'
DATA_DIR.mkdir(exist_ok=True)

OUT_JSON = DATA_DIR / 'asset_map.json'
OUT_MD   = DATA_DIR / 'local_assets.md'

# Known valuable files on the desktop we should bridge
KNOWN_ASSETS = [
    {'file': r'C:\Users\meeko\Desktop\ultimateai_knowledge.db',
     'type': 'sqlite', 'desc': 'Knowledge base database — could feed lesson library'},
    {'file': r'C:\Users\meeko\Desktop\MYCELIUM_KNOWLEDGE_BASE.json',
     'type': 'json', 'desc': 'Mycelium knowledge base — merge with system'},
    {'file': r'C:\Users\meeko\Desktop\ultimateai_events.jsonl',
     'type': 'jsonl', 'desc': 'Event log — feed into signal tracker'},
    {'file': r'C:\Users\meeko\Desktop\ultimateai_pip_map.json',
     'type': 'json', 'desc': 'Pip dependency map — for requirements generation'},
    {'file': r'C:\Users\meeko\Desktop\GUMROAD_PRODUCT_LISTINGS.txt',
     'type': 'text', 'desc': 'Gumroad listings — sync to live store'},
    {'file': r'C:\Users\meeko\Desktop\AllDependencies.txt',
     'type': 'text', 'desc': 'Full dependency list — generate requirements.txt'},
    {'file': r'C:\Users\meeko\Desktop\MEEKO_MYCELIUM_SYSTEM_GUIDE.pdf',
     'type': 'pdf', 'desc': 'System guide PDF — already exists, ensure it is live'},
    {'file': r'C:\Users\meeko\Desktop\docker-compose.yml',
     'type': 'yaml', 'desc': 'Docker config — could containerize the system'},
    {'file': r'C:\Users\meeko\Desktop\system_report.txt',
     'type': 'text', 'desc': 'System report — extract and archive'},
]

INTERESTING_DIRS = [
    r'C:\Users\meeko\Desktop\INVESTMENT_HQ',
    r'C:\Users\meeko\Desktop\TRADING_SYSTEM',
    r'C:\Users\meeko\Desktop\SOLARPUNK_AUTONOMOUS',
    r'C:\Users\meeko\Desktop\PRODUCTS',
]

def scan_file(path):
    p = Path(path)
    if not p.exists():
        return None
    info = {
        'exists': True,
        'size_kb': p.stat().st_size // 1024,
        'modified': datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
    }
    # Try reading contents
    try:
        if path.endswith('.json'):
            data = json.loads(p.read_text(errors='ignore'))
            if isinstance(data, dict):
                info['keys'] = list(data.keys())[:10]
            elif isinstance(data, list):
                info['items'] = len(data)
        elif path.endswith('.jsonl'):
            lines = p.read_text(errors='ignore').strip().split('\n')
            info['lines'] = len(lines)
        elif path.endswith('.txt'):
            text = p.read_text(errors='ignore')
            info['lines'] = len(text.split('\n'))
            info['preview'] = text[:200]
        elif path.endswith('.db'):
            try:
                conn = sqlite3.connect(path)
                tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                info['tables'] = [t[0] for t in tables]
                conn.close()
            except: pass
    except: pass
    return info

def scan_dir(path):
    p = Path(path)
    if not p.exists():
        return None
    files = list(p.rglob('*'))
    py_files = [f for f in files if f.suffix == '.py']
    return {
        'exists': True,
        'total_files': len(files),
        'py_files': len(py_files),
        'py_names': [f.name for f in py_files[:10]],
    }

def scan_local_pythons():
    """Python scripts on desktop not in any repo."""
    if not DESKTOP.exists():
        return []
    scripts = []
    for f in DESKTOP.glob('*.py'):
        name = f.name
        # Check if it's in the github repo
        in_repo = (REPO / 'mycelium' / name).exists()
        scripts.append({
            'name': name,
            'size_kb': f.stat().st_size // 1024,
            'in_repo': in_repo,
            'recommend': 'push to repo' if not in_repo else 'already in repo',
        })
    return scripts

def build_report(assets, dirs, local_scripts):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        '# Local Asset Map',
        f'Generated: {now}',
        '',
        '## Known Asset Files',
        '',
    ]
    for asset in KNOWN_ASSETS:
        info = assets.get(asset['file'])
        status = '✓ EXISTS' if (info and info.get('exists')) else '✗ NOT FOUND'
        lines.append(f'### {Path(asset["file"]).name} — {status}')
        lines.append(f'*{asset["desc"]}*')
        if info and info.get('exists'):
            lines.append(f'- Size: {info.get("size_kb", "?")}KB')
            if 'keys' in info: lines.append(f'- Keys: {info["keys"]}')
            if 'tables' in info: lines.append(f'- DB tables: {info["tables"]}')
            if 'lines' in info: lines.append(f'- Lines: {info["lines"]}')
        lines.append('')

    lines += [
        '## Interesting Directories',
        '',
    ]
    for d in INTERESTING_DIRS:
        info = dirs.get(d)
        name = Path(d).name
        status = f"{info['total_files']} files, {info['py_files']} scripts" if info else 'NOT FOUND'
        lines.append(f'- **{name}**: {status}')

    lines += [
        '',
        '## Local Python Scripts Not Yet in Repo',
        '',
    ]
    orphans = [s for s in local_scripts if not s['in_repo']]
    for s in orphans:
        lines.append(f'- `{s["name"]}` ({s["size_kb"]}KB) — {s["recommend"]}')
    if not orphans:
        lines.append('- All local scripts are in the repo ✓')

    lines += [
        '',
        '## Next Connection Opportunities',
        '',
        '1. **ultimateai_knowledge.db** → extract lessons → add to solarpunk-learn',
        '2. **MYCELIUM_KNOWLEDGE_BASE.json** → merge with data/what_works.json',
        '3. **ultimateai_events.jsonl** → feed into signal_tracker.py event history',
        '4. **GUMROAD_PRODUCT_LISTINGS.txt** → sync to live Gumroad store via API',
        '5. **SOLARPUNK_AUTONOMOUS/** → audit what it has, merge best parts into nerve-center',
        '6. **INVESTMENT_HQ/** → if it has working code, surface it through solarpunk-bank',
        '',
        '*Generated by mycelium/asset_scanner.py*',
    ]
    return '\n'.join(lines)

def run():
    print('\n' + '='*56)
    print('  ASSET SCANNER')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*56)

    # Scan known asset files
    assets = {}
    for asset in KNOWN_ASSETS:
        info = scan_file(asset['file'])
        assets[asset['file']] = info
        status = '✓' if (info and info.get('exists')) else '✗'
        print(f'  {status} {Path(asset["file"]).name}')

    # Scan interesting dirs
    dirs = {}
    for d in INTERESTING_DIRS:
        info = scan_dir(d)
        dirs[d] = info
        status = f"{info['total_files']} files" if info else 'missing'
        print(f'  → {Path(d).name}: {status}')

    # Scan local scripts
    local_scripts = scan_local_pythons()
    orphans = [s for s in local_scripts if not s['in_repo']]
    print(f'  Local scripts not in repo: {len(orphans)}')

    # Save outputs
    map_data = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'assets': assets,
        'directories': dirs,
        'local_scripts': local_scripts,
        'orphan_scripts': orphans,
    }
    OUT_JSON.write_text(json.dumps(map_data, indent=2, default=str))
    OUT_MD.write_text(build_report(assets, dirs, local_scripts))

    print(f'  Saved: {OUT_JSON}')
    print(f'  Saved: {OUT_MD}')
    print('  ✓ Asset scan complete')
    return map_data

if __name__ == '__main__':
    run()
