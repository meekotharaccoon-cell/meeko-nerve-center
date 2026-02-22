#!/usr/bin/env python3
"""
EVOLVE.PY
==========
The self-improvement engine.

Every time it runs:
  1. Pulls latest from GitHub (stays current)
  2. Runs connection_mapper (finds gaps + missed links)
  3. Runs desktop_cleaner (organizes local machine)
  4. Checks all workflows for what needs activation
  5. Builds something new (rotates through the build queue)
  6. Reports everything it found
  7. Writes the NEXT version of EVOLVE.bat with findings baked in

The bat file that called this script gets replaced by a smarter one.
The system evolves every single morning.

Run via: EVOLVE.bat (scheduled daily at 7am)
Or manually: python mycelium/evolve.py
"""
import os, sys, json, subprocess, shutil, datetime, platform
from pathlib import Path

START_TIME = datetime.datetime.now()
REPO_ROOT  = Path(__file__).parent.parent
DATA_DIR   = REPO_ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)

EVOLVE_LOG = DATA_DIR / 'evolve_history.json'
BAT_PATH   = Path(r'C:\Users\meeko\Desktop\EVOLVE.bat')
REPO_URL   = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

# ---- UTILITIES ---------------------------------------------------

def log(msg, level='INFO'):
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    icons = {'INFO': '•', 'OK': '✓', 'WARN': '⚠', 'BUILD': '🔨', 'CLEAN': '🧹', 'CONNECT': '🔗', 'EVOLVE': '🌱'}
    icon = icons.get(level, '•')
    print(f'  [{ts}] {icon} {msg}')

def load_history():
    try: return json.loads(EVOLVE_LOG.read_text())
    except: return {'runs': [], 'built': [], 'next_build_index': 0}

def save_history(h):
    EVOLVE_LOG.write_text(json.dumps(h, indent=2))

def run_cmd(cmd, cwd=None, capture=True):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=capture, text=True, cwd=cwd or REPO_ROOT)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)

# ---- STEP 1: PULL LATEST -----------------------------------------

def pull_latest():
    log('Pulling latest from GitHub...', 'INFO')
    ok, out = run_cmd('git pull origin main')
    if ok:
        log('Up to date with GitHub', 'OK')
    else:
        log(f'Pull issue (might be offline): {out[:80]}', 'WARN')
    return ok

# ---- STEP 2: CONNECTION MAPPER -----------------------------------

def find_connections():
    log('Scanning for missed connections...', 'CONNECT')
    try:
        ok, out = run_cmd('python mycelium/connection_mapper.py')
        if ok:
            log('Connection map updated', 'OK')
        return out
    except:
        return 'connection_mapper not available yet'

# ---- STEP 3: DESKTOP CLEANER ------------------------------------

def clean_desktop():
    log('Cleaning desktop...', 'CLEAN')
    try:
        ok, out = run_cmd('python mycelium/desktop_cleaner.py')
        log('Desktop organized', 'OK')
        return out
    except:
        return 'desktop_cleaner not available yet'

# ---- STEP 4: BUILD QUEUE ----------------------------------------
# Each run builds one thing from this rotating queue.
# Items are marked done and never re-built.
# New items get added as the system evolves.

BUILD_QUEUE = [
    {'id': 'index_lessons',      'desc': 'Rebuild knowledge library index',         'cmd': 'python mycelium/knowledge_indexer.py'},
    {'id': 'gen_changelog',      'desc': 'Regenerate changelog from git history',   'cmd': 'python mycelium/changelog_generator.py'},
    {'id': 'run_signal_tracker', 'desc': 'Run signal tracker — what\'s working',    'cmd': 'python mycelium/signal_tracker.py'},
    {'id': 'run_monetization',   'desc': 'Update revenue tracker',                  'cmd': 'python mycelium/monetization_tracker.py'},
    {'id': 'run_seo',            'desc': 'Ping search engines with sitemap',        'cmd': 'python mycelium/seo_submitter.py SEO_DRY_RUN=false'},
    {'id': 'run_cross_poster',   'desc': 'Queue next social media post',            'cmd': 'python mycelium/cross_poster.py'},
    {'id': 'run_brain_check',    'desc': 'Run brain self-check',                    'cmd': 'python mycelium/meeko_brain.py'},
    {'id': 'run_outreach',       'desc': 'Run community outreach (dry)',            'cmd': 'python mycelium/community_outreach.py'},
    {'id': 'verify_workflows',   'desc': 'Verify all workflow files exist',         'cmd': 'python -c "import glob; wf=glob.glob(\'.github/workflows/*.yml\'); print(f\'{len(wf)} workflows found\')"'},
    {'id': 'audit_data_dir',     'desc': 'Audit data directory',                   'cmd': 'python -c "import os,json; files=list(os.walk(\'data\')); print(f\'data/: {sum(len(f) for _,_,f in files)} files\')"'},
]

def run_build(history):
    built = set(history.get('built', []))
    queue = [b for b in BUILD_QUEUE if b['id'] not in built]

    if not queue:
        log('All build items complete — queue will reset', 'BUILD')
        history['built'] = []  # Reset and start over with next evolution
        queue = BUILD_QUEUE

    item = queue[0]
    log(f'Building: {item["desc"]}', 'BUILD')
    ok, out = run_cmd(item['cmd'])
    status = 'OK' if ok else 'WARN'
    log(f'Build result: {out[:120]}', status)
    history['built'].append(item['id'])
    return item, ok, out

# ---- STEP 5: ENHANCEMENT SUGGESTIONS ----------------------------

def generate_enhancements(connections_out, build_item, build_ok):
    """
    Look at system state and generate specific, actionable enhancements.
    These get baked into the next EVOLVE.bat as visible suggestions.
    """
    history = load_history()
    runs = len(history.get('runs', []))

    suggestions = []

    # Always check for missing secrets
    secrets_needed = [
        ('GMAIL_APP_PASSWORD', 'activates all 10 email workflows'),
        ('MASTODON_TOKEN + MASTODON_SERVER', 'activates social posting'),
        ('BLUESKY_APP_PASSWORD + BLUESKY_HANDLE', 'activates Bluesky posting'),
        ('YOUTUBE_CLIENT_ID etc (5 secrets)', 'activates YouTube manager'),
        ('GUMROAD_TOKEN', 'activates revenue tracking'),
        ('MAILGUN_API_KEY + MAILGUN_DOMAIN', 'activates open tracking on emails (free)'),
    ]
    suggestions.append(('SECRETS', 'Add GitHub secrets to activate more workflows', secrets_needed))

    # Run-count based suggestions
    if runs < 3:
        suggestions.append(('FORK', 'Share the fork link — system recruits its own successors', [REPO_URL + '/fork']))
    if runs >= 3:
        suggestions.append(('DOMAIN', 'Buy solarpunkmycelium.org (~$8/year) — email deliverability upgrade', ['porkbun.com']))
    if runs >= 5:
        suggestions.append(('REDDIT', 'Post to r/solarpunk, r/selfhosted, r/opensource — content ready in content/', ['Use content/ANNOUNCEMENT_REDDIT_*.md']))
    if runs >= 7:
        suggestions.append(('PRODUCTMAP', 'Add yourself to FORK_REGISTRY.md — prove the model', [REPO_URL + '/blob/main/FORK_REGISTRY.md']))

    # Connection gaps (simple static analysis)
    py_files = list((REPO_ROOT / 'mycelium').glob('*.py')) if (REPO_ROOT / 'mycelium').exists() else []
    wf_files = list((REPO_ROOT / '.github' / 'workflows').glob('*.yml')) if (REPO_ROOT / '.github' / 'workflows').exists() else []

    unwired = []
    for py in py_files:
        name = py.stem
        wired = any(name in wf.read_text() for wf in wf_files)
        if not wired and name not in ('meeko_brain', '__init__'):
            unwired.append(name)

    if unwired:
        suggestions.append(('WIRE', f'These scripts have no GitHub Actions workflow yet', unwired))

    return suggestions

# ---- STEP 6: WRITE NEXT EVOLVE.BAT ------------------------------

def write_next_bat(run_num, suggestions, build_item, connections_out, clean_out):
    """
    Write a new EVOLVE.bat that:
    - Has this run's findings baked in as visible comments
    - Runs everything again tomorrow
    - Gets smarter each iteration
    """
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    next_run = run_num + 1

    sug_lines = []
    for cat, title, items in suggestions:
        sug_lines.append(f'echo   [{cat}] {title}')
        for item in items[:2]:
            item_str = str(item)[:70]
            sug_lines.append(f'echo       {item_str}')
    suggestions_block = '\n'.join(sug_lines)

    bat_content = f"""@echo off
REM EVOLVE.bat — Generation {next_run}
REM Last evolved: {now}
REM Last built: {build_item['desc']}
REM This file was written by the system itself. It replaces itself on every run.
REM Delete it and it will be recreated next push. Fork it and it runs for someone else.

title SolarPunk Mycelium — Evolving... (Gen {next_run})
color 0A

echo.
echo  ==================================================
echo   SOLARPUNK MYCELIUM — EVOLUTION ENGINE
echo   Generation: {next_run}
echo   {now}
echo  ==================================================
echo.

REM Step 1: Go to the repo
cd /d "%~dp0UltimateAI_Master\meeko-nerve-center" 2>nul || (
  cd /d "%USERPROFILE%\Desktop\UltimateAI_Master\meeko-nerve-center" 2>nul || (
    echo   [WARN] Could not find repo. Clone it first:
echo   git clone {REPO_URL}
    pause
    exit /b 1
  )
)

echo  [1/6] Pulling latest from GitHub...
git pull origin main
echo.

echo  [2/6] Cleaning desktop...
python mycelium\desktop_cleaner.py
echo.

echo  [3/6] Mapping connections...
python mycelium\connection_mapper.py
echo.

echo  [4/6] Running build queue...
python mycelium\evolve.py
echo.

echo  [5/6] Pushing any new files...
git add -A
git commit -m "auto: evolution gen {next_run} %date%" 2>nul
git push origin main 2>nul
echo.

echo  [6/6] This run's enhancements:
echo.
{suggestions_block}
echo.
echo  ==================================================
echo   Evolution complete. New EVOLVE.bat written.
echo   Open it tomorrow morning or let Task Scheduler run it.
echo  ==================================================
echo.

REM Copy new bat to desktop (the system replaces itself)
copy /Y mycelium\evolve_output\EVOLVE_next.bat "%USERPROFILE%\Desktop\EVOLVE.bat" 2>nul

pause
"""
    return bat_content

# ---- STEP 7: TASK SCHEDULER SETUP -------------------------------

def print_task_scheduler_cmd(bat_path):
    cmd = f'schtasks /create /tn "SolarPunk Mycelium Evolve" /tr "{bat_path}" /sc daily /st 07:00 /f'
    print('\n' + '='*52)
    print('  TO SCHEDULE DAILY AT 7AM:')
    print('  Run this in Command Prompt as Administrator:')
    print(f'  {cmd}')
    print('='*52 + '\n')
    return cmd

# ---- MAIN -------------------------------------------------------

def run():
    print('\n' + '='*52)
    print('  EVOLVE.PY — Self-Improvement Engine')
    print(f'  {START_TIME.strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*52)

    history = load_history()
    run_num = len(history.get('runs', [])) + 1
    log(f'Evolution run #{run_num}', 'EVOLVE')

    # Run all steps
    pull_latest()
    connections_out = find_connections()
    clean_out = clean_desktop()
    build_item, build_ok, build_out = run_build(history)
    suggestions = generate_enhancements(connections_out, build_item, build_ok)

    # Record this run
    run_record = {
        'run': run_num,
        'at': START_TIME.isoformat(),
        'built': build_item['id'],
        'build_ok': build_ok,
        'suggestions': [s[0] for s in suggestions],
        'duration_s': (datetime.datetime.now() - START_TIME).seconds,
    }
    history.setdefault('runs', []).append(run_record)
    save_history(history)

    # Write next bat
    next_bat = write_next_bat(run_num, suggestions, build_item, connections_out, clean_out)
    out_dir = REPO_ROOT / 'mycelium' / 'evolve_output'
    out_dir.mkdir(exist_ok=True)
    next_bat_path = out_dir / 'EVOLVE_next.bat'
    next_bat_path.write_text(next_bat)
    log(f'Next EVOLVE.bat written: Gen {run_num + 1}', 'EVOLVE')

    # Also write directly to desktop
    try:
        BAT_PATH.write_text(next_bat)
        log(f'Desktop EVOLVE.bat updated to Gen {run_num + 1}', 'OK')
    except Exception as e:
        log(f'Could not write to desktop: {e}', 'WARN')

    # Summary
    print('\n' + '='*52)
    print(f'  RUN #{run_num} COMPLETE')
    print(f'  Built: {build_item["desc"]}')
    print(f'  Duration: {(datetime.datetime.now() - START_TIME).seconds}s')
    print(f'  Total runs: {run_num}')
    print('\n  ENHANCEMENTS FOR NEXT EVOLUTION:')
    for cat, title, items in suggestions:
        print(f'  [{cat}] {title}')
        for item in items[:2]:
            print(f'    • {str(item)[:70]}')
    print_task_scheduler_cmd(BAT_PATH)

if __name__ == '__main__':
    run()
