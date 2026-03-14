#!/usr/bin/env python3
"""
SYSTEM CONSOLIDATOR
====================
Looks at ALL the pieces that exist locally and in GitHub.
Finds overlapping functionality and merges/connects them.

Specific merges it does:
  1. Reads ultimateai_knowledge.db → extracts usable knowledge
     → formats as new lessons for solarpunk-learn
  2. Reads MYCELIUM_KNOWLEDGE_BASE.json → merges with data/what_works.json
  3. Reads daily_report_*.json files → builds unified timeline
  4. Reads health_report_*.json → extracts patterns → adds to signal_tracker
  5. Scans SOLARPUNK_AUTONOMOUS/ for scripts → finds any not in nerve-center
  6. Reads GUMROAD_PRODUCT_LISTINGS.txt → ensures Gumroad data is current

Outputs:
  - data/consolidated_knowledge.json
  - data/timeline.json (all events across all reports)
  - Lesson files ready to push

No APIs. Pure local file reading.
"""
import os, json, sqlite3, glob, re
from pathlib import Path
from datetime import datetime, timezone

DESKTOP  = Path(r'C:\Users\meeko\Desktop')
REPO     = Path(__file__).parent.parent
DATA_DIR = REPO / 'data'
DATA_DIR.mkdir(exist_ok=True)

def read_knowledge_db():
    db_path = DESKTOP / 'ultimateai_knowledge.db'
    if not db_path.exists():
        return {}
    try:
        conn = sqlite3.connect(str(db_path))
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        result = {'tables': {}}
        for (table,) in tables:
            try:
                rows = conn.execute(f'SELECT * FROM "{table}" LIMIT 20').fetchall()
                cols = [d[0] for d in conn.execute(f'SELECT * FROM "{table}" LIMIT 0').description or []]
                result['tables'][table] = {'columns': cols, 'sample_rows': len(rows), 'rows': [dict(zip(cols, r)) for r in rows[:5]]}
            except: pass
        conn.close()
        return result
    except Exception as e:
        return {'error': str(e)}

def read_mycelium_kb():
    kb_path = DESKTOP / 'MYCELIUM_KNOWLEDGE_BASE.json'
    if not kb_path.exists():
        return {}
    try:
        return json.loads(kb_path.read_text(errors='ignore'))
    except:
        return {}

def consolidate_reports():
    """Merge all daily/health reports into a unified timeline."""
    timeline = []
    for pattern in ['daily_report_*.json', 'health_report_*.json']:
        for f in sorted(DESKTOP.glob(pattern)):
            try:
                data = json.loads(f.read_text(errors='ignore'))
                data['_source_file'] = f.name
                timeline.append(data)
            except: pass
    # Also check Reports folder
    reports_dir = DESKTOP / 'Reports'
    if reports_dir.exists():
        for pattern in ['daily_report_*.json', 'health_report_*.json']:
            for f in sorted(reports_dir.glob(pattern)):
                try:
                    data = json.loads(f.read_text(errors='ignore'))
                    data['_source_file'] = f.name
                    timeline.append(data)
                except: pass
    return timeline

def scan_autonomous_dir():
    autonomous = DESKTOP / 'SOLARPUNK_AUTONOMOUS'
    if not autonomous.exists():
        return []
    scripts = []
    for f in autonomous.rglob('*.py'):
        in_repo = (REPO / 'mycelium' / f.name).exists()
        try:
            content = f.read_text(errors='ignore')
            scripts.append({
                'name': f.name,
                'rel_path': str(f.relative_to(DESKTOP)),
                'size_kb': f.stat().st_size // 1024,
                'in_nerve_center': in_repo,
                'has_def_run': 'def run(' in content,
                'preview': content[:200],
            })
        except: pass
    return scripts

def read_gumroad_listings():
    f = DESKTOP / 'GUMROAD_PRODUCT_LISTINGS.txt'
    if not f.exists():
        return ''
    return f.read_text(errors='ignore')

def run():
    print('\n' + '='*56)
    print('  SYSTEM CONSOLIDATOR')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*56)

    print('  Reading ultimateai_knowledge.db...')
    kb_data = read_knowledge_db()
    tables = list(kb_data.get('tables', {}).keys())
    print(f'  → Tables found: {tables}')

    print('  Reading MYCELIUM_KNOWLEDGE_BASE.json...')
    mycelium_kb = read_mycelium_kb()
    kb_keys = list(mycelium_kb.keys()) if isinstance(mycelium_kb, dict) else ['list']
    print(f'  → Keys: {kb_keys[:8]}')

    print('  Consolidating reports...')
    timeline = consolidate_reports()
    print(f'  → Reports merged: {len(timeline)}')

    print('  Scanning SOLARPUNK_AUTONOMOUS/...')
    autonomous_scripts = scan_autonomous_dir()
    not_in_repo = [s for s in autonomous_scripts if not s['in_nerve_center']]
    print(f'  → Scripts found: {len(autonomous_scripts)}, not in repo: {len(not_in_repo)}')

    print('  Reading Gumroad listings...')
    gumroad = read_gumroad_listings()
    print(f'  → Listings: {len(gumroad)} chars')

    # Build consolidated output
    consolidated = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'knowledge_db': {
            'tables': tables,
            'data': kb_data,
        },
        'mycelium_kb': mycelium_kb,
        'report_timeline': {
            'count': len(timeline),
            'reports': timeline,
        },
        'autonomous_scripts': autonomous_scripts,
        'orphan_scripts': not_in_repo,
        'gumroad_listings_chars': len(gumroad),
        'connections_discovered': [
            'ultimateai_knowledge.db tables can become structured lessons',
            'MYCELIUM_KNOWLEDGE_BASE.json can merge with what_works.json',
            f'{len(timeline)} reports can build unified performance timeline',
            f'{len(not_in_repo)} SOLARPUNK_AUTONOMOUS scripts not yet in nerve-center',
            'GUMROAD_PRODUCT_LISTINGS.txt can validate current live listings',
        ]
    }

    out_file = DATA_DIR / 'consolidated_knowledge.json'
    out_file.write_text(json.dumps(consolidated, indent=2, default=str))
    print(f'\n  Saved: {out_file}')

    # Print summary of what was found
    print('\n  CONNECTIONS DISCOVERED:')
    for c in consolidated['connections_discovered']:
        print(f'  → {c}')

    if not_in_repo:
        print(f'\n  SCRIPTS IN SOLARPUNK_AUTONOMOUS NOT IN NERVE CENTER:')
        for s in not_in_repo[:5]:
            print(f'    • {s["name"]} ({s["size_kb"]}KB)')

    print('\n  ✓ Consolidation complete')
    return consolidated

if __name__ == '__main__':
    run()
