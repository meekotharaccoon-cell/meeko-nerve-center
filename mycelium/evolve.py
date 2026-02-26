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
BUILD_QUEUE = [
    {'id': 'index_lessons',   'desc': 'Rebuild knowledge library index',          'fn': 'knowledge_indexer',   'method': 'run'},
    {'id': 'gen_changelog',   'desc': 'Regenerate changelog from full git history','fn': 'changelog_generator', 'method': 'run'},
    {'id': 'scan_assets',     'desc': 'Scan local assets — find missed connections','fn': 'asset_scanner',       'method': 'run'},
    {'id': 'consolidate',     'desc': 'Consolidate local knowledge into system',   'fn': 'system_consolidator', 'method': 'run'},
    {'id': 'map_connections', 'desc': 'Map all connections + generate gap report', 'fn': 'connection_mapper',   'method': 'run'},
    {'id': 'signal_tracker',  'desc': 'Run signal tracker — what is working',     'fn': 'signal_tracker',      'method': 'run'},
    {'id': 'seo_ping',        'desc': 'Ping search engines with updated sitemap',  'fn': 'seo_submitter',       'method': 'run'},
    {'id': 'verify_workflows','desc': 'Count + verify all GitHub Actions workflows',
     'cmd': 'python -c "import glob; wf=glob.glob(\'.github/workflows/*.yml\'); print(str(len(wf))+\' workflows active\')"; '},
    {'id': 'audit_data',      'desc': 'Audit data/ — what has been generated',
     'cmd': 'python -c "import os; [print(f) for f in os.listdir(\'data\')]" '},
    {'id': 'clean_desktop',   'desc': 'Deep clean and organize desktop',           'fn': 'desktop_cleaner',     'method': 'run'},
]

def run_build_item(item, history):
    log(f'Building: {item["desc"]}', '\U0001f528')
    if 'fn' in item:
        mod = load_mod(item['fn'])
        if mod and hasattr(mod, item.get('method', 'run')):
            try:
                getattr(mod, item['method'])()
                return True, 'module run OK'
            except Exception as e:
                return False, str(e)
        else:
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
        log('All build items complete — resetting queue', '\U0001f504')
        history['built'] = []
        remaining = BUILD_QUEUE
    return remaining[0]

# ===================== ENHANCEMENT SUGGESTIONS ====================
def gather_suggestions(history, conn_data):
    runs = len(history.get('runs', []))
    sugs = []
    sugs.append(('SECRETS', 'Add GitHub Secrets to unlock locked workflows', [
        'GMAIL_APP_PASSWORD  -> repo Settings > Secrets > Actions',
        'MASTODON_TOKEN + MASTODON_SERVER  -> create at any Mastodon instance',
        'MAILGUN_API_KEY + MAILGUN_DOMAIN  -> mailgun.com -> free 100/day',
        'GUMROAD_TOKEN  -> Gumroad account > Settings > Advanced',
    ]))
    unwired = conn_data.get('unwired_scripts', []) if conn_data else []
    if unwired:
        sugs.append(('WIRE', f'{len(unwired)} scripts need GitHub Actions workflows', unwired[:4]))
    absent = conn_data.get('connections_absent', []) if conn_data else []
    if absent:
        desc = [f"{c['from']} -> {c['to']}" for c in absent[:3]]
        sugs.append(('CONNECT', "Scripts that should call each other but don't", desc))
    if runs == 0:
        sugs.append(('FIRST', 'First run! Post to Hacker News today', ['SHOW_HN.md is ready to copy-paste']))
    if runs >= 2:
        sugs.append(('SHARE', 'Share the one-pager — content/ONE_PAGER.md is public domain', ['Forward it. Post it.']))
    if runs >= 4:
        sugs.append(('REDDIT', 'Post to Reddit communities', [
            'r/selfhosted -> mycelium/reddit_posts.md',
            'r/solarpunk -> mycelium/reddit_posts.md',
        ]))
    if runs >= 6:
        sugs.append(('DEVTO', 'Publish Dev.to article — mycelium/devto_article.md is ready', ['Go to dev.to > New Post > paste it']))
    if runs >= 8:
        sugs.append(('DOMAIN', 'Consider solarpunkmycelium.org (~$8/yr) for email deliverability', ['porkbun.com or namecheap.com']))
    return sugs

# ===================== WRITE NEXT BAT ============================
def write_next_bat(gen, sugs, built_item, build_ok):
    now        = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    next_gen   = gen + 1
    sug_lines  = []
    for cat, title, items in sugs:
        sug_lines.append(f'echo   [{cat}] {title}')
        for item in items[:3]:
            safe = str(item).replace('%', '%%')[:72]
            sug_lines.append(f'echo     - {safe}')
    sug_block    = '\n'.join(sug_lines)
    build_status = 'OK' if build_ok else 'WARN'
    build_desc   = built_item.get('desc', '?')[:60]

    # Use string concat to avoid f-string + Windows backslash issues
    p = '%USERPROFILE%'
    bat = (
        '@echo off\n'
        + f'REM EVOLVE.bat Generation {next_gen}\n'
        + f'REM Last evolved: {now}\n'
        + f'REM Last built: [{build_status}] {build_desc}\n'
        + 'REM Written by the system itself. Fork: ' + REPO_URL + '/fork\n'
        + '\ntitle SolarPunk Mycelium Gen ' + str(next_gen) + ' evolving...\ncolor 0A\n'
        + 'echo.\necho  ==================================================\n'
        + f'echo   SOLARPUNK MYCELIUM EVOLUTION ENGINE Gen {next_gen}\n'
        + f'echo   Last built: {build_desc[:50]}\n'
        + 'echo  ==================================================\necho.\n'
        + 'set REPO=' + p + '\\Desktop\\meeko-nerve-center\n'
        + 'if not exist "%REPO%" cd /d ' + p + '\\Desktop && git clone ' + REPO_URL + '\n'
        + 'cd /d %REPO%\n'
        + 'git pull origin main\necho.\n'
        + 'python mycelium\\evolve.py\necho.\n'
        + 'git add -A\n'
        + f'git commit -m "auto: gen {next_gen}" 2>nul\n'
        + 'git push origin main 2>nul\necho.\n'
        + 'echo  ==================================================\n'
        + f'echo   ENHANCEMENTS Gen {next_gen}\n'
        + 'echo  ==================================================\necho.\n'
        + sug_block + '\necho.\n'
        + f'echo   System: {REPO_URL}\n'
        + f'echo   Generation {next_gen} complete.\n'
        + 'echo  ==================================================\necho.\npause\n'
    )
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
    log(f'Generation {gen} / Run #{run_num}', '\U0001f331')

    log('Pulling from GitHub...')
    run_cmd('git pull origin main')

    log('Scanning local assets...')
    asset_mod = load_mod('asset_scanner')
    if asset_mod:
        try: asset_mod.run()
        except: pass

    log('Consolidating local knowledge...')
    cons_mod = load_mod('system_consolidator')
    if cons_mod:
        try: cons_mod.run()
        except: pass

    log('Cleaning desktop...')
    clean_mod = load_mod('desktop_cleaner')
    if clean_mod:
        try: clean_mod.run()
        except: pass

    log('Mapping connections...')
    conn_data = {}
    conn_mod = load_mod('connection_mapper')
    if conn_mod:
        try: conn_data = conn_mod.run() or {}
        except: pass

    build_item = next_build_item(history)
    build_ok, build_out = run_build_item(build_item, history)
    history.setdefault('built', []).append(build_item['id'])
    log(f'Built: {build_item["desc"]} — {"OK" if build_ok else "WARN"}', '\U0001f528')

    sugs = gather_suggestions(history, conn_data)

    history.setdefault('runs', []).append({
        'run': run_num, 'gen': gen, 'at': START.isoformat(),
        'built': build_item['id'], 'build_ok': build_ok,
        'sugs': [s[0] for s in sugs],
        'duration_s': (datetime.datetime.now() - START).seconds,
    })
    history['gen'] = gen
    save_history(history)

    next_bat = write_next_bat(gen, sugs, build_item, build_ok)
    out_dir = REPO / 'mycelium' / 'evolve_output'
    out_dir.mkdir(exist_ok=True)
    (out_dir / 'EVOLVE_next.bat').write_text(next_bat)

    try:
        BAT_PATH.write_text(next_bat)
        history['gen'] = gen + 1
        save_history(history)
        log(f'Desktop EVOLVE.bat -> Gen {gen + 1}', '\u2713')
    except Exception as e:
        log(f'Could not write desktop bat: {e}', '\u26a0')

    elapsed = (datetime.datetime.now() - START).seconds
    print('\n' + '='*56)
    print(f'  EVOLUTION COMPLETE — Gen {gen} Run #{run_num}')
    print(f'  Built: {build_item["desc"]}')
    print(f'  Time:  {elapsed}s  |  Next gen: {gen + 1}')
    print()
    print('  ENHANCEMENTS:')
    for cat, title, items in sugs:
        print(f'  [{cat}] {title}')
        for item in items[:2]: print(f'    * {str(item)[:68]}')
    print('='*56)

if __name__ == '__main__':
    run()
