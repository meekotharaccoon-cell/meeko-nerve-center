#!/usr/bin/env python3
"""
🧠 ORCHESTRATOR — Meeko Mycelium Central Nervous System
Fix: uncommented section dividers (COLORS, DATA BUS, SCRIPT RUNNER etc.)
were being parsed as Python identifiers causing SyntaxError line 59.
"""

import os, sys, json, time, datetime, subprocess, threading, argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT  = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(REPO_ROOT))

# --- COLORS ---
class C:
    G='\033[92m'; Y='\033[93m'; R='\033[91m'; CY='\033[96m'
    B='\033[1m'; D='\033[2m'; X='\033[0m'

def ok(s):       print(C.G  + '  \u2713 ' + s + C.X)
def skip(s):     print(C.D  + '  \u25e6 ' + s + ' (skipped)' + C.X)
def run_lbl(s):  print(C.CY + '  \u25b6 ' + s + C.X)
def err(s):      print(C.Y  + '  \u26a0 ' + s + C.X)
def hdr(s):      print('\n' + C.G + C.B + '='*55 + C.X + '\n' + C.G + C.B + '  ' + s + C.X + '\n' + C.G + C.B + '='*55 + C.X)

# --- DATA BUS — shared state between all modules ---
DATA_BUS_PATH = REPO_ROOT / 'data' / 'orchestrator_bus.json'

def bus_read():
    try:
        if DATA_BUS_PATH.exists():
            return json.loads(DATA_BUS_PATH.read_text())
    except: pass
    return {}

def bus_write(key, value):
    data = bus_read()
    data[key] = value
    data['_updated'] = datetime.datetime.utcnow().isoformat()
    DATA_BUS_PATH.parent.mkdir(exist_ok=True)
    DATA_BUS_PATH.write_text(json.dumps(data, indent=2, default=str))

def bus_get(key, default=None):
    return bus_read().get(key, default)

# --- SCRIPT RUNNER ---
RESULTS = {}

def run_script(script_name, args='', capture=False, label=None):
    """Run a mycelium script and capture its output for piping"""
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        skip(label or script_name)
        return None
    display = label or script_name
    run_lbl(display)
    start = time.time()
    try:
        cmd = 'python "' + str(script_path) + '" ' + args
        result = subprocess.run(cmd, shell=True, capture_output=capture,
                                text=True, timeout=60, cwd=str(REPO_ROOT))
        elapsed = time.time() - start
        if result.returncode == 0:
            ok(display + ' (' + str(round(elapsed, 1)) + 's)')
            output = (result.stdout or '').strip()
            RESULTS[script_name] = {'status': 'ok', 'output': output, 'elapsed': elapsed}
            return output
        else:
            err(display + ' exited ' + str(result.returncode))
            if result.stderr: print('  ' + C.D + result.stderr[:200] + C.X)
            RESULTS[script_name] = {'status': 'error', 'code': result.returncode}
            return None
    except subprocess.TimeoutExpired:
        err(display + ' timed out')
        RESULTS[script_name] = {'status': 'timeout'}
        return None
    except Exception as e:
        err(display + ': ' + str(e))
        RESULTS[script_name] = {'status': 'exception', 'error': str(e)}
        return None

# --- SPACE LAYER ---
def run_space_layer():
    hdr('\U0001f6f8 SPACE LAYER')
    try:
        import urllib.request
        iss = json.loads(urllib.request.urlopen('http://api.open-notify.org/iss-now.json', timeout=8).read())
        pos = iss.get('iss_position', {})
        bus_write('iss_position', pos)
        ok('ISS: ' + str(pos.get('latitude','?')) + '\xb0, ' + str(pos.get('longitude','?')) + '\xb0')
    except Exception as e:
        err('ISS fetch: ' + str(e))
    try:
        crew_data = json.loads(urllib.request.urlopen('http://api.open-notify.org/astros.json', timeout=8).read())
        iss_crew = [p['name'] for p in crew_data.get('people', []) if p.get('craft') == 'ISS']
        bus_write('iss_crew', iss_crew)
        ok('ISS crew: ' + ', '.join(iss_crew))
    except: pass
    iss_pos = bus_get('iss_position', {})
    crew    = bus_get('iss_crew', [])
    crew_str = ', '.join(crew) if crew else 'unknown'
    space_summary = ('\U0001f6f8 ISS: ' + str(iss_pos.get('latitude','?')) +
                     '\xb0 lat, ' + str(iss_pos.get('longitude','?')) + '\xb0 lon\n' +
                     '\U0001f468\u200d\U0001f680 Crew: ' + crew_str)
    bus_write('space_summary', space_summary)
    ok('Space data on bus')

# --- MORNING CYCLE ---
def morning_cycle():
    hdr('\U0001f305 MORNING CYCLE')
    run_space_layer()
    run_script('signal_tracker.py',       label='Signal tracker')
    run_script('morning_briefing.py',     label='Morning briefing')
    run_script('appointment_guardian.py', label='Appointment guardian')
    run_script('mycelium_hello.py',       label='Hello emailer')
    run_script('grant_outreach.py',       label='Grant scanner')
    run_script('update_state.py',         label='System state update')
    bus_write('last_morning_cycle', datetime.datetime.utcnow().isoformat())
    ok('Morning cycle complete')

# --- EVENING CYCLE ---
def evening_cycle():
    hdr('\U0001f306 EVENING CYCLE')
    run_space_layer()
    run_script('pulse.py',                  label='System pulse')
    run_script('cross_poster.py',           label='Cross-poster')
    run_script('seo_submitter.py',          label='SEO submitter')
    run_script('monetization_tracker.py',   label='Revenue tracker')
    run_script('changelog_generator.py',    label='Changelog')
    run_script('evolve.py',                 label='Evolve + self-improve')
    run_script('update_state.py',           label='System state update')
    bus_write('last_evening_cycle', datetime.datetime.utcnow().isoformat())
    ok('Evening cycle complete')

# --- REVENUE LAYER ---
def revenue_layer():
    hdr('\U0001f4b0 REVENUE LAYER')
    run_script('monetization_tracker.py', label='Revenue tracker')
    snapshot = {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'sources': {
            'gumroad':         {'status': 'live'},
            'etsy':            {'status': 'live'},
            'ko_fi':           {'status': 'live'},
            'bitcoin':         {'status': 'address_active'},
            'grants':          {'status': 'outreach_running'},
        },
    }
    snap_path = REPO_ROOT / 'data' / 'revenue_snapshot.json'
    snap_path.parent.mkdir(exist_ok=True)
    snap_path.write_text(json.dumps(snapshot, indent=2))
    bus_write('revenue_snapshot', snapshot)
    run_script('grant_outreach.py', label='Grant outreach')
    ok('Revenue layer complete')

# --- MESH LAYER ---
def mesh_layer():
    hdr('\U0001f578\ufe0f MESH LAYER')
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center',
            headers={'User-Agent': 'MeekoMycelium/1.0'}
        )
        repo_data = json.loads(urllib.request.urlopen(req, timeout=8).read())
        forks = repo_data.get('forks_count', 0)
        stars = repo_data.get('stargazers_count', 0)
        bus_write('github_forks', forks)
        bus_write('github_stars', stars)
        ok('GitHub: ' + str(forks) + ' forks (nodes) \xb7 ' + str(stars) + ' stars')
    except Exception as e:
        err('GitHub API: ' + str(e))
    run_script('network_node.py',      args='--mesh', label='Local mesh scan')
    run_script('connection_mapper.py',               label='Connection mapper')
    run_script('community_outreach.py',              label='Community outreach')
    bus_write('last_mesh_cycle', datetime.datetime.utcnow().isoformat())

# --- STATUS REPORT ---
def status_report():
    hdr('\U0001f4ca STATUS \u2014 ALL LAYERS')
    bus     = bus_read()
    scripts = sorted(SCRIPT_DIR.glob('*.py'))
    layers = [
        ('\U0001f6f8 Space Bridge',      'space_bridge.py',        bus.get('iss_position')),
        ('\U0001f578\ufe0f Network Node', 'network_node.py',        True),
        ('\U0001f305 Morning Briefing',  'morning_briefing.py',    bus.get('last_morning_cycle')),
        ('\U0001f4b0 Revenue Tracker',   'monetization_tracker.py', bus.get('revenue_snapshot')),
        ('\U0001f4e1 Signal Tracker',    'signal_tracker.py',      bus.get('signals')),
        ('\U0001f4e7 Email Layer',       'unified_emailer.py',     os.environ.get('GMAIL_APP_PASSWORD')),
        ('\U0001f9e0 Evolve',            'evolve.py',              True),
    ]
    print('  Layer                         Script                       Status')
    print('  ' + '-'*28 + ' ' + '-'*28 + ' ' + '-'*10)
    for name, script, active in layers:
        exists = (SCRIPT_DIR / script).exists()
        if not exists:   status = C.Y + 'MISSING' + C.X
        elif active:     status = C.G + 'ACTIVE'  + C.X
        else:            status = C.D + 'IDLE'    + C.X
        print('  ' + name[:28].ljust(28) + ' ' + C.D + script[:28].ljust(28) + C.X + ' ' + status)
    print('\n  ' + C.D + 'Total scripts: ' + str(len(scripts)) + C.X)
    print('  ' + C.D + 'Data bus entries: ' + str(len(bus)) + C.X)

# --- FULL DAILY CYCLE ---
def full_cycle():
    start = time.time()
    morning_cycle()
    revenue_layer()
    mesh_layer()
    evening_cycle()
    elapsed = time.time() - start
    ok_count  = sum(1 for r in RESULTS.values() if r.get('status') == 'ok')
    err_count = sum(1 for r in RESULTS.values() if r.get('status') != 'ok')
    bus_write('last_full_cycle', datetime.datetime.utcnow().isoformat())
    bus_write('cycle_results', {'ok': ok_count, 'errors': err_count, 'elapsed_s': elapsed})
    print('\n' + C.G + C.B + '='*55 + C.X)
    print(C.G + C.B + '  CYCLE COMPLETE' + C.X)
    print('  ' + C.G + '\u2713' + C.X + ' ' + str(ok_count) + ' layers ran successfully')
    if err_count:
        print('  ' + C.Y + '\u26a0' + C.X + ' ' + str(err_count) + ' had issues (see above)')
    print('  ' + C.D + 'Elapsed: ' + str(round(elapsed, 1)) + 's' + C.X)
    print(C.G + C.B + '='*55 + C.X)

# --- MAIN ---
def main():
    now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    print('\n' + C.G + C.B + '='*55)
    print('  🧠 MEEKO MYCELIUM ORCHESTRATOR')
    print('  Wiring all layers into one organism')
    print('  ' + now)
    print('='*55 + C.X + '\n')
    p = argparse.ArgumentParser()
    p.add_argument('--morning',  action='store_true')
    p.add_argument('--evening',  action='store_true')
    p.add_argument('--revenue',  action='store_true')
    p.add_argument('--space',    action='store_true')
    p.add_argument('--mesh',     action='store_true')
    p.add_argument('--status',   action='store_true')
    args = p.parse_args()
    if args.morning:   morning_cycle()
    elif args.evening: evening_cycle()
    elif args.revenue: revenue_layer()
    elif args.space:   run_space_layer()
    elif args.mesh:    mesh_layer()
    elif args.status:  status_report()
    else:              full_cycle()

if __name__ == '__main__':
    main()
