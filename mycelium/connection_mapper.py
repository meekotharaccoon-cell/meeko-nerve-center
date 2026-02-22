#!/usr/bin/env python3
"""
CONNECTION MAPPER
==================
Looks at everything the system has and finds:
  - Scripts with no workflow (unwired)
  - Workflows with no script (orphaned)
  - Data files nothing reads
  - Scripts that could call each other but don't
  - Repos with no cross-links
  - Capability gaps (things the system should have but doesn't)

Outputs:
  - data/connections.json  (machine-readable map)
  - data/gaps.md           (human-readable gap report)
  - Prints specific recommendations

No APIs. No tokens. Pure static analysis.
"""
import os, json, re
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR  = REPO_ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)

CONN_FILE = DATA_DIR / 'connections.json'
GAPS_FILE = DATA_DIR / 'gaps.md'

# Known repos in the ecosystem
KNOWN_REPOS = [
    'meeko-nerve-center',
    'gaza-rose-gallery',
    'solarpunk-learn',
    'solarpunk-legal',
    'solarpunk-remedies',
    'solarpunk-market',
    'solarpunk-mutual-aid',
    'solarpunk-grants',
    'solarpunk-radio',
    'solarpunk-bank',
]

# Capability checklist: what a mature system should have
CAPABILITY_CHECKLIST = {
    'email_outreach':      {'files': ['mycelium/unified_emailer.py'], 'secrets': ['GMAIL_APP_PASSWORD']},
    'social_posting':      {'files': ['mycelium/cross_poster.py'], 'secrets': ['MASTODON_TOKEN']},
    'revenue_tracking':    {'files': ['mycelium/monetization_tracker.py'], 'secrets': ['GUMROAD_TOKEN']},
    'analytics':           {'files': ['mycelium/signal_tracker.py'], 'secrets': []},
    'seo':                 {'files': ['mycelium/seo_submitter.py'], 'secrets': ['INDEXNOW_KEY']},
    'community_outreach':  {'files': ['mycelium/community_outreach.py'], 'secrets': ['REDDIT_CLIENT_ID']},
    'knowledge_library':   {'files': ['lessons/'], 'secrets': []},
    'legal_tools':         {'files': ['solarpunk-legal/'], 'secrets': []},
    'self_evolution':      {'files': ['mycelium/evolve.py'], 'secrets': []},
    'changelog':           {'files': ['mycelium/changelog_generator.py'], 'secrets': []},
    'professional_email':  {'files': ['mycelium/mailer_pro.py'], 'secrets': ['MAILGUN_API_KEY']},
    'youtube_manager':     {'files': ['.github/workflows/youtube-manager.yml'], 'secrets': ['YOUTUBE_CLIENT_ID']},
}

# Cross-links: which scripts SHOULD import or call each other
IDEAL_CONNECTIONS = [
    ('evolve.py', 'connection_mapper.py', 'evolve calls mapper to find gaps'),
    ('evolve.py', 'desktop_cleaner.py', 'evolve calls cleaner on each run'),
    ('evolve.py', 'changelog_generator.py', 'evolve triggers changelog'),
    ('unified_emailer.py', 'mailer_pro.py', 'emailer uses pro delivery'),
    ('unified_emailer.py', 'meeko_brain.py', 'every email brain-gated'),
    ('cross_poster.py', 'meeko_brain.py', 'every post brain-gated'),
    ('signal_tracker.py', 'cross_poster.py', 'tracker informs what to post'),
    ('monetization_tracker.py', 'signal_tracker.py', 'revenue feeds signal'),
    ('knowledge_indexer.py', 'lessons/', 'indexer reads all lessons'),
    ('community_outreach.py', 'content/', 'outreach uses prepared content'),
    ('seo_submitter.py', 'sitemap.xml', 'seo generates and submits sitemap'),
]

def scan_scripts():
    scripts = {}
    mycelium = REPO_ROOT / 'mycelium'
    if mycelium.exists():
        for f in mycelium.glob('*.py'):
            content = f.read_text(errors='ignore')
            imports = re.findall(r'^(?:import|from) ([\w\.]+)', content, re.MULTILINE)
            scripts[f.name] = {
                'path': str(f.relative_to(REPO_ROOT)),
                'size': f.stat().st_size,
                'imports': imports,
                'has_main': '__main__' in content,
                'has_run_fn': 'def run(' in content,
            }
    return scripts

def scan_workflows():
    workflows = {}
    wf_dir = REPO_ROOT / '.github' / 'workflows'
    if wf_dir.exists():
        for f in wf_dir.glob('*.yml'):
            content = f.read_text(errors='ignore')
            scripts_called = re.findall(r'python\s+([\w/\\]+\.py)', content)
            schedules = re.findall(r"cron: '([^']+)'", content)
            workflows[f.name] = {
                'scripts': scripts_called,
                'schedules': schedules,
                'has_manual_trigger': 'workflow_dispatch' in content,
            }
    return workflows

def scan_data():
    data_files = {}
    if DATA_DIR.exists():
        for f in DATA_DIR.glob('*.json'):
            try:
                data_files[f.name] = {'size': f.stat().st_size}
            except: pass
    return data_files

def find_unwired_scripts(scripts, workflows):
    """Scripts with no workflow pointing at them."""
    wired = set()
    for wf in workflows.values():
        for s in wf['scripts']:
            wired.add(Path(s).name)
    unwired = []
    for name in scripts:
        if name not in wired and name not in ('meeko_brain.py', '__init__.py', 'evolve.py'):
            if scripts[name]['has_run_fn'] or scripts[name]['has_main']:
                unwired.append(name)
    return unwired

def find_missing_capabilities(scripts, workflows):
    missing = []
    for cap, reqs in CAPABILITY_CHECKLIST.items():
        for req_file in reqs['files']:
            path = REPO_ROOT / req_file
            if not path.exists() and not any(req_file in s for s in scripts):
                missing.append((cap, req_file, reqs.get('secrets', [])))
                break
    return missing

def find_actual_connections(scripts):
    """Which ideal connections actually exist."""
    present = []
    absent = []
    mycelium = REPO_ROOT / 'mycelium'
    for src, dst, desc in IDEAL_CONNECTIONS:
        src_path = mycelium / src
        if src_path.exists():
            content = src_path.read_text(errors='ignore')
            dst_name = Path(dst).stem
            if dst_name in content or dst in content:
                present.append((src, dst, desc))
            else:
                absent.append((src, dst, desc))
        else:
            absent.append((src, dst, 'source script missing'))
    return present, absent

def build_gap_report(unwired, missing_caps, absent_conns, data_files):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        '# System Gap Report',
        f'Generated: {now}',
        '',
        '---',
        '',
        '## Scripts Not Wired to Any Workflow',
        '*(These run locally but not automatically on GitHub)*',
        '',
    ]
    for s in unwired:
        lines.append(f'- `mycelium/{s}` — needs a `.github/workflows/{s.replace(".py",".yml")}` file')
    if not unwired:
        lines.append('- None! All scripts are wired. ✓')

    lines += [
        '',
        '## Missing Capabilities',
        '',
    ]
    for cap, req_file, secrets in missing_caps:
        lines.append(f'- **{cap}**: needs `{req_file}`')
        if secrets:
            lines.append(f'  - Secrets needed: {', '.join(secrets)}')
    if not missing_caps:
        lines.append('- All planned capabilities present. ✓')

    lines += [
        '',
        '## Connections That Should Exist But Don\'t',
        '',
    ]
    for src, dst, desc in absent_conns:
        lines.append(f'- `{src}` → `{dst}`: {desc}')
    if not absent_conns:
        lines.append('- All ideal connections present. ✓')

    lines += [
        '',
        '## Data Files',
        '',
    ]
    for fname, info in data_files.items():
        size_kb = info['size'] // 1024
        lines.append(f'- `data/{fname}` ({size_kb}KB)')

    lines += [
        '',
        '---',
        '',
        '## Next Actions (Priority Order)',
        '',
        '1. Add `GMAIL_APP_PASSWORD` secret → activates all email workflows',
        '2. Add `MASTODON_TOKEN` + `MASTODON_SERVER` → activates daily posting',
        '3. Run `python mycelium/knowledge_indexer.py` → updates lesson library',
        '4. Post to Hacker News (content/ANNOUNCEMENT_HACKERNEWS.md is ready)',
        '5. Post to r/selfhosted (content/ANNOUNCEMENT_REDDIT_SELFHOSTED.md is ready)',
        '',
        '*This file was generated by `mycelium/connection_mapper.py`*',
    ]
    return '\n'.join(lines)

def run():
    print('\n' + '='*52)
    print('  CONNECTION MAPPER')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*52)

    scripts    = scan_scripts()
    workflows  = scan_workflows()
    data_files = scan_data()

    print(f'  Scripts found:   {len(scripts)}')
    print(f'  Workflows found: {len(workflows)}')
    print(f'  Data files:      {len(data_files)}')

    unwired       = find_unwired_scripts(scripts, workflows)
    missing_caps  = find_missing_capabilities(scripts, workflows)
    present, absent = find_actual_connections(scripts)

    print(f'\n  Unwired scripts:          {len(unwired)}')
    print(f'  Missing capabilities:     {len(missing_caps)}')
    print(f'  Connections present:      {len(present)}')
    print(f'  Connections missing:      {len(absent)}')

    if unwired:
        print('\n  Unwired:')
        for s in unwired: print(f'    - {s}')

    if absent:
        print('\n  Missing connections:')
        for src, dst, desc in absent[:5]:
            print(f'    - {src} → {dst}: {desc}')

    # Save outputs
    conn_data = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'scripts': list(scripts.keys()),
        'workflows': list(workflows.keys()),
        'unwired_scripts': unwired,
        'missing_capabilities': [c[0] for c in missing_caps],
        'connections_present': len(present),
        'connections_absent': len(absent),
        'absent_connections': [{'from': s, 'to': d, 'desc': desc} for s, d, desc in absent],
    }
    CONN_FILE.write_text(json.dumps(conn_data, indent=2))
    GAPS_FILE.write_text(build_gap_report(unwired, missing_caps, absent, data_files))

    print(f'\n  Saved: {CONN_FILE}')
    print(f'  Saved: {GAPS_FILE}')
    print('  ✔ Map complete')
    return conn_data

if __name__ == '__main__':
    run()
