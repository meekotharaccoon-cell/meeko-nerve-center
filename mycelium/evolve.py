#!/usr/bin/env python3
"""
EVOLVE.PY v2 — Full Self-Improvement Engine
=============================================
Every run:
  1.  Pull latest from GitHub
  2.  Scan local assets (finds what the system doesn't know about)
  3.  Consolidate local knowledge into GitHub system
  4.  Clean desktop (organizes into minimum folders)
  5.  Map all connections (finds unwired scripts, gaps, missed links)
  6.  Build one item from the rotating queue
  7.  Auto-push new files to GitHub
  8.  Write next-generation EVOLVE.bat with findings baked in

The bat file that called this gets replaced by a smarter one.
Run daily at 7am via Task Scheduler.
Or run manually: python mycelium/evolve.py
"""
import os, sys, json, subprocess, datetime, importlib.util
from pathlib import Path

START   = datetime.datetime.now()
REPO    = Path(__file__).parent.parent
DATA    = REPO / 'data'
DATA.mkdir(exist_ok=True)

HISTORY_FILE = DATA / 'evolve_history.json'
BAT_PATH     = Path(r'C:\Users\meeko\Desktop\EVOLVE.bat')
REPO_URL     = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

def ts(): return datetime.datetime.now().strftime('%H:%M:%S')

def log(msg, sym='•'):
    print(f'  [{ts()}] {sym} {msg}')

def run_cmd(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or REPO)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)

def load_mod(name):
    p = REPO / 'mycelium' / f'{name}.py'
    if not p.exists(): return None
    spec = importlib.util.spec_from_file_location(name, p)
    mod  = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(mod)
    except: return None
    return mod

def load_history():
    try: return json.loads(HISTORY_FILE.read_text())
    except: return {'runs': [], 'built': [], 'gen': 1}

def save_history(h):
    HISTORY_FILE.write_text(json.dumps(h, indent=2))

# ===================== BUILD QUEUE ================================
# Rotates through every run. Never builds the same thing twice
# until all are done, then resets.

BUILD_QUEUE = [
    {'id': 'index_lessons',     'desc': 'Rebuild knowledge library index (now 13 lessons)',  'fn': 'knowledge_indexer', 'method': 'run'},
    {'id': 'gen_changelog',     'desc': 'Regenerate changelog from full git history',         'fn': 'changelog_generator', 'method': 'run'},
    {'id': 'scan_assets',       'desc': 'Scan local assets — find missed connections',        'fn': 'asset_scanner', 'method': 'run'},
    {'id': 'consolidate',       'desc': 'Consolidate local knowledge into system',            'fn': 'system_consolidator', 'method': 'run'},
    {'id': 'map_connections',   'desc': 'Map all connections + generate gap report',          'fn': 'connection_mapper', 'method': 'run'},
    {'id': 'signal_tracker',    'desc': 'Run signal tracker — what is actually working',     'fn': 'signal_tracker', 'method': 'run'},
    {'id': 'seo_ping',          'desc': 'Ping search engines with updated sitemap',           'fn': 'seo_submitter', 'method': 'run'},
    {'id': 'verify_workflows',  'desc': 'Count + verify all GitHub Actions workflows',
     'cmd': 'python -c "import glob; wf=glob.glob(\'.github/workflows/*.yml\'); print(str(len(wf))+\' workflows active\')"; '},
    {'id': 'audit_data',        'desc': 'Audit data/ — what has been generated so far',
     'cmd': 'python -c "import os; [print(f) for f in os.listdir(\'data\')]" '},
    {'id': 'clean_desktop',     'desc': 'Deep clean and organize desktop',                    'fn': 'desktop_cleaner', 'method': 'run'},
]

def run_build_item(item, history):
    log(f'Building: {item["desc"]}', '🔨')
    if 'fn' in item:
        mod = load_mod(item['fn'])
        if mod and hasattr(mod, item.get('method', 'run')):
            try:
                getattr(mod, item['method'])()
                return True, 'module run OK'
            except Exception as e:
                return False, str(e)
        else:
            # Fallback: run as subprocess
            ok, out = run_cmd(f'python mycelium/{item["fn"]}.py')
            return ok, out
    elif 'cmd' in item:
        ok, out = run_cmd(item['cmd'])
        return ok, out
    return False, 'no runner'

def next_build_item(history):
    built = set(history.get('built', []))
    remaining = [b for b in BUILD_QUEUE if b['id'] not in built]
    if not remaining:
        log('All build items complete — resetting queue for next cycle', '🔄')
        history['built'] = []
        remaining = BUILD_QUEUE
    return remaining[0]

# ===================== ENHANCEMENT SUGGESTIONS ====================

def gather_suggestions(history, conn_data):
    runs = len(history.get('runs', []))
    sugs = []

    # Always: missing secrets
    sugs.append(('SECRETS', 'Add GitHub Secrets to unlock locked workflows', [
        'GMAIL_APP_PASSWORD  → repo Settings > Secrets > Actions',
        'MASTODON_TOKEN + MASTODON_SERVER  → create at any Mastodon instance',
        'MAILGUN_API_KEY + MAILGUN_DOMAIN  → mailgun.com → free 100/day',
        'GUMROAD_TOKEN  → Gumroad account > Settings > Advanced',
    ]))

    # Unwired scripts
    unwired = conn_data.get('unwired_scripts', []) if conn_data else []
    if unwired:
        sugs.append(('WIRE', f'{len(unwired)} scripts need GitHub Actions workflows', unwired[:4]))

    # Missing connections
    absent = conn_data.get('connections_absent', []) if conn_data else []
    if absent:
        desc = [f"{c['from']} → {c['to']}" for c in absent[:3]]
        sugs.append(('CONNECT', 'Scripts that should call each other but don\'t', desc))

    # Run-based suggestions
    if runs == 0:
        sugs.append(('FIRST', 'First run! Post to Hacker News today', ['content/ANNOUNCEMENT_HACKERNEWS.md is ready to copy-paste']))
    if runs >= 2:
        sugs.append(('SHARE', 'Share the one-pager — content/ONE_PAGER.md is public domain', ['Forward it. Post it. Print it.']))
    if runs >= 4:
        sugs.append(('REDDIT', 'Post to Reddit communities — content is ready', [
            'r/selfhosted → content/ANNOUNCEMENT_REDDIT_SELFHOSTED.md',
            'r/solarpunk → content/ANNOUNCEMENT_REDDIT_SOLARPUNK.md',
        ]))
    if runs >= 6:
        sugs.append(('DEVTO', 'Publish Dev.to article — content/DEVTO_ARTICLE.md is ready', ['Go to dev.to > New Post > paste it']))
    if runs >= 8:
        sugs.append(('DOMAIN', 'Consider solarpunkmycelium.org (~$8/yr) for email deliverability', ['porkbun.com or namecheap.com']))

    return sugs

# ===================== WRITE NEXT BAT ============================

def write_next_bat(gen, sugs, built_item, build_ok):
    now  = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    next_gen = gen + 1

    sug_lines = []
    for cat, title, items in sugs:
        sug_lines.append(f'echo   [{cat}] {title}')
        for item in items[:3]:
            safe = str(item).replace('%', '%%')[:72]
            sug_lines.append(f'echo     - {safe}')
    sug_block = '\n'.join(sug_lines)

    build_status = 'OK' if build_ok else 'WARN'
    build_desc   = built_item.get('desc', '?')[:60]

    bat = f"""@echo off
REM EVOLVE.bat — Generation {next_gen}
REM Last evolved: {now}
REM Last built:   [{build_status}] {build_desc}
REM
REM This file was written by the system itself.
REM It replaces itself on every run.
REM Fork it: {REPO_URL}/fork

title SolarPunk Mycelium — Gen {next_gen} evolving...
color 0A

echo.
echo  ==================================================
echo   SOLARPUNK MYCELIUM — EVOLUTION ENGINE
echo   Generation {next_gen}  /  {now}
echo   Last built: {build_desc[:50]}
echo  ==================================================
echo.

set REPO=%USERPROFILE%\Desktop\UltimateAI_Master\meeko-nerve-center
if not exist "%REPO%" (
  echo [SETUP] Cloning repo...
  md "%USERPROFILE%\Desktop\UltimateAI_Master" 2>nul
  cd /d "%USERPROFILE%\Desktop\UltimateAI_Master"
  git clone {REPO_URL}
)
cd /d "%REPO%"

echo [1/8] Pulling latest...
git pull origin main
echo.

echo [2/8] Running full evolution engine...
python mycelium\evolve.py
echo.

echo [3/8] Pushing new outputs to GitHub...
git add -A
git commit -m "auto: gen {next_gen} %%date%%" 2>nul
git push origin main 2>nul
echo.

echo [4/8] Ensuring daily schedule exists...
schtasks /query /tn "SolarPunk Mycelium Evolve" >nul 2>&1
if errorlevel 1 (
  schtasks /create /tn "SolarPunk Mycelium Evolve" /tr "\"%USERPROFILE%\Desktop\EVOLVE.bat\"" /sc daily /st 07:00 /f >nul 2>&1
  echo Scheduled: daily at 7:00 AM
) else (
  echo Already scheduled at 7:00 AM
)
echo.

echo  ==================================================
echo   ENHANCEMENTS — Generation {next_gen} Report
echo  ==================================================
echo.
{sug_block}
echo.
echo   System: {REPO_URL}
echo   Dashboard: meekotharaccoon-cell.github.io/meeko-nerve-center/dashboard.html
echo   Links: meekotharaccoon-cell.github.io/meeko-nerve-center/link.html
echo   Gallery: meekotharaccoon-cell.github.io/gaza-rose-gallery
echo.
echo   Generation {next_gen} complete. This bat has been replaced.
echo   Next run: tomorrow 7am (or double-click EVOLVE.bat now).
echo  ==================================================
echo.
pause
"""
    return bat

# ===================== MAIN ======================================

def run():
    print('\n' + '='*56)
    print('  EVOLVE.PY v2 — Self-Improvement Engine')
    print(f'  {START.strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*56)

    history  = load_history()
    gen      = history.get('gen', 1)
    run_num  = len(history.get('runs', [])) + 1
    log(f'Generation {gen} / Run #{run_num}', '🌱')

    # Step 1: Pull
    log('Pulling from GitHub...')
    run_cmd('git pull origin main')

    # Step 2: Scan local assets
    log('Scanning local assets...')
    asset_mod = load_mod('asset_scanner')
    asset_data = {}
    if asset_mod:
        try: asset_data = asset_mod.run() or {}
        except: pass

    # Step 3: Consolidate knowledge
    log('Consolidating local knowledge...')
    cons_mod = load_mod('system_consolidator')
    if cons_mod:
        try: cons_mod.run()
        except: pass

    # Step 4: Clean desktop
    log('Cleaning desktop...')
    clean_mod = load_mod('desktop_cleaner')
    if clean_mod:
        try: clean_mod.run()
        except: pass

    # Step 5: Map connections
    log('Mapping connections...')
    conn_data = {}
    conn_mod = load_mod('connection_mapper')
    if conn_mod:
        try: conn_data = conn_mod.run() or {}
        except: pass

    # Step 6: Build one item
    build_item = next_build_item(history)
    build_ok, build_out = run_build_item(build_item, history)
    history.setdefault('built', []).append(build_item['id'])
    log(f'Built: {build_item["desc"]} — {"OK" if build_ok else "WARN"}', '🔨')

    # Gather suggestions
    sugs = gather_suggestions(history, conn_data)

    # Record run
    history.setdefault('runs', []).append({
        'run': run_num, 'gen': gen,
        'at': START.isoformat(),
        'built': build_item['id'],
        'build_ok': build_ok,
        'sugs': [s[0] for s in sugs],
        'duration_s': (datetime.datetime.now() - START).seconds,
    })
    history['gen'] = gen
    save_history(history)

    # Write next bat
    next_bat = write_next_bat(gen, sugs, build_item, build_ok)

    # Write to repo (committed next push)
    out_dir = REPO / 'mycelium' / 'evolve_output'
    out_dir.mkdir(exist_ok=True)
    (out_dir / 'EVOLVE_next.bat').write_text(next_bat)

    # Write directly to desktop (replaces current bat)
    try:
        BAT_PATH.write_text(next_bat)
        history['gen'] = gen + 1
        save_history(history)
        log(f'Desktop EVOLVE.bat → Gen {gen + 1}', '✓')
    except Exception as e:
        log(f'Could not write desktop bat: {e}', '⚠')

    # Print summary
    elapsed = (datetime.datetime.now() - START).seconds
    print('\n' + '='*56)
    print(f'  EVOLUTION COMPLETE — Gen {gen} Run #{run_num}')
    print(f'  Built: {build_item["desc"]}')
    print(f'  Time:  {elapsed}s')
    print(f'  Next generation: {gen + 1}')
    print()
    print('  ENHANCEMENTS:')
    for cat, title, items in sugs:
        print(f'  [{cat}] {title}')
        for item in items[:2]: print(f'    • {str(item)[:68]}')
    print()
    print(f'  Dashboard: meekotharaccoon-cell.github.io/meeko-nerve-center/dashboard.html')
    print('=' * 56)

if __name__ == '__main__':
    run()
