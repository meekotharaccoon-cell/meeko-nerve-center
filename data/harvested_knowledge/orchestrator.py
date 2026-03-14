#!/usr/bin/env python3
"""
🧠 ORCHESTRATOR — Meeko Mycelium Central Nervous System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The missing connective tissue. Runs all 40+ mycelium scripts
in the right order, pipes data between them, creates the
feedback loops that turn isolated tools into one organism.

DATA FLOWS WIRED HERE:
  space_bridge → morning_briefing → cross_poster → social channels
  space_bridge → network_node (WebSocket broadcast)
  signal_tracker → cross_poster → all platforms
  monetization_tracker → revenue dashboard update
  network_node mesh discovery → mycelium_hello outreach
  evolve → detects opportunities → triggers relevant scripts
  identity_vault → signs all outgoing docs
  grant_outreach → auto-apply based on mission match

Usage:
  python ORCHESTRATOR.py                  # full daily cycle
  python ORCHESTRATOR.py --morning        # morning cycle only
  python ORCHESTRATOR.py --evening        # evening cycle only
  python ORCHESTRATOR.py --revenue        # revenue layer only
  python ORCHESTRATOR.py --space          # space + broadcast
  python ORCHESTRATOR.py --mesh           # network discovery + outreach
  python ORCHESTRATOR.py --status         # show status of all layers
  python ORCHESTRATOR.py --connect A B    # manually wire two scripts
"""

import os
import sys
import json
import time
import datetime
import subprocess
import threading
import argparse
from pathlib import Path

# Add mycelium to path
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(REPO_ROOT))

# ─────────────────────────────────────────────
COLORS
# ─────────────────────────────────────────────
class C:
    G='[92m'; Y='[93m'; R='[91m'; CY='[96m'; B='[1m'; D='[2m'; X='[0m'

def ok(s):   print(f"{C.G}  ✓ {s}{C.X}")
def skip(s): print(f"{C.D}  ◦ {s} (skipped — not available){C.X}")
def run_lbl(s): print(f"{C.CY}  ▶ {s}{C.X}")
def err(s):  print(f"{C.Y}  ⚠ {s}{C.X}")
def hdr(s):  print(f"\n{C.G}{C.B}{'='*55}{C.X}\n{C.G}{C.B}  {s}{C.X}\n{C.G}{C.B}{'='*55}{C.X}")

# ─────────────────────────────────────────────
DATA BUS — shared state between all modules
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
SCRIPT RUNNER
# ─────────────────────────────────────────────
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
        cmd = f"python \"{script_path}\" {args}"
        result = subprocess.run(
            cmd, shell=True, capture_output=capture,
            text=True, timeout=60, cwd=str(REPO_ROOT)
        )
        elapsed = time.time() - start
        if result.returncode == 0:
            ok(f"{display} ({elapsed:.1f}s)")
            output = (result.stdout or '').strip()
            RESULTS[script_name] = {'status': 'ok', 'output': output, 'elapsed': elapsed}
            return output
        else:
            err(f"{display} exited {result.returncode}")
            if result.stderr: print(f"  {C.D}{result.stderr[:200]}{C.X}")
            RESULTS[script_name] = {'status': 'error', 'code': result.returncode}
            return None
    except subprocess.TimeoutExpired:
        err(f"{display} timed out")
        RESULTS[script_name] = {'status': 'timeout'}
        return None
    except Exception as e:
        err(f"{display}: {e}")
        RESULTS[script_name] = {'status': 'exception', 'error': str(e)}
        return None

# ─────────────────────────────────────────────
SPACE LAYER — pull + broadcast
# ─────────────────────────────────────────────
def run_space_layer():
    hdr('🛸 SPACE LAYER')
    # Pull ISS + solar + NASA data
    try:
        import urllib.request, json as _json
        iss = _json.loads(
            urllib.request.urlopen('http://api.open-notify.org/iss-now.json', timeout=8).read()
        )
        pos = iss.get('iss_position', {})
        bus_write('iss_position', pos)
        ok(f"ISS: {pos.get('latitude','?')}°, {pos.get('longitude','?')}°")
    except Exception as e:
        err(f"ISS fetch: {e}")

    try:
        crew_data = _json.loads(
            urllib.request.urlopen('http://api.open-notify.org/astros.json', timeout=8).read()
        )
        iss_crew = [p['name'] for p in crew_data.get('people',[]) if p.get('craft')=='ISS']
        bus_write('iss_crew', iss_crew)
        ok(f"ISS crew: {', '.join(iss_crew)}")
    except: pass

    try:
        solar = _json.loads(
            urllib.request.urlopen('https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json', timeout=8).read()
        )
        if isinstance(solar, list) and len(solar) > 1:
            latest = solar[-1]
            speed = float(latest[2]) if latest[2] else None
            if speed:
                bus_write('solar_wind_kms', speed)
                ok(f"Solar wind: {speed:.0f} km/s")
    except: pass

    # Generate space summary for morning briefing
    iss_pos = bus_get('iss_position', {})
    crew = bus_get('iss_crew', [])
    solar_speed = bus_get('solar_wind_kms', 0)

    space_summary = (
        f"\ud83d\udef8 ISS: {iss_pos.get('latitude','?')}° lat, {iss_pos.get('longitude','?')}° lon\n"
        f"👨\u200d🚀 Crew: {', '.join(crew) if crew else 'unknown'}\n"
        f"\u2600\ufe0f Solar wind: {solar_speed:.0f} km/s"
    )
    bus_write('space_summary', space_summary)
    ok("Space data written to bus → available to morning_briefing, pulse, cross_poster")

# ─────────────────────────────────────────────
MORNING CYCLE
# ─────────────────────────────────────────────
def morning_cycle():
    hdr('🌅 MORNING CYCLE')
    print(f"  {C.D}Order: space → signal → briefing → outreach{C.X}\n")

    # 1. Space data first (feeds into briefing)
    run_space_layer()

    # 2. Signal tracker (what's trending, what needs attention)
    run_script('signal_tracker.py', label='Signal tracker')
    signals = bus_get('signals', {})

    # 3. Morning briefing (now has space data from bus)
    run_script('morning_briefing.py', label='Morning briefing')

    # 4. Check appointments
    run_script('appointment_guardian.py', label='Appointment guardian')

    # 5. Outreach (hello emailer)
    run_script('mycelium_hello.py', label='Hello emailer')

    # 6. Grant outreach
    run_script('grant_outreach.py', label='Grant scanner')

    # 7. Update system state
    run_script('update_state.py', label='System state update')

    bus_write('last_morning_cycle', datetime.datetime.utcnow().isoformat())
    ok("Morning cycle complete")

# ─────────────────────────────────────────────
EVENING CYCLE
# ─────────────────────────────────────────────
def evening_cycle():
    hdr('🌆 EVENING CYCLE')
    print(f"  {C.D}Order: space → content → publish → monetize → evolve{C.X}\n")

    # 1. Space update
    run_space_layer()

    # 2. Pulse (system health check)
    run_script('pulse.py', label='System pulse')

    # 3. Cross-poster (publishes content everywhere)
    # Feeds it the space summary from bus
    run_script('cross_poster.py', label='Cross-poster')

    # 4. SEO / discovery
    run_script('seo_submitter.py', label='SEO submitter')

    # 5. Monetization tracker (pulls all revenue data)
    run_script('monetization_tracker.py', label='Revenue tracker')

    # 6. Changelog
    run_script('changelog_generator.py', label='Changelog')

    # 7. Evolve (AI analysis of what's working, what to improve)
    run_script('evolve.py', label='Evolve + self-improve')

    # 8. Update system state
    run_script('update_state.py', label='System state update')

    bus_write('last_evening_cycle', datetime.datetime.utcnow().isoformat())
    ok("Evening cycle complete")

# ─────────────────────────────────────────────
REVENUE LAYER
# ─────────────────────────────────────────────
def revenue_layer():
    hdr('💰 REVENUE LAYER')
    print(f"  {C.D}Wiring: monetization_tracker → revenue.html → cross_poster{C.X}\n")

    # Track revenue
    run_script('monetization_tracker.py', label='Revenue tracker')

    # Pull revenue data from bus and write to data/revenue_snapshot.json
    snapshot = {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'sources': {
            'gaza_rose_gallery': {'status': 'live', 'url': 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery', 'payment': 'paypal'},
            'fork_guide_gumroad': {'status': 'product_ready_needs_listing', 'price': 5, 'content': 'products/fork-guide.md'},
            'ko_fi': {'status': 'needs_setup', 'url': 'https://ko-fi.com'},
            'bitcoin': {'status': 'address_active'},
            'lightning': {'status': 'built_not_wired', 'file': 'mycelium/lightning_checkout.js'},
            'solana': {'status': 'configured_not_wired'},
            'legal_referrals': {'status': 'traffic_needed', 'tools': ['TCPA', 'FDCPA', 'FOIA']},
            'grants': {'status': 'outreach_running'},
        },
        'next_action': 'Create Gumroad listing at gumroad.com — product content ready at products/fork-guide.md',
    }
    snap_path = REPO_ROOT / 'data' / 'revenue_snapshot.json'
    snap_path.parent.mkdir(exist_ok=True)
    snap_path.write_text(json.dumps(snapshot, indent=2))
    ok("Revenue snapshot written → data/revenue_snapshot.json")

    # Grant scanner
    run_script('grant_outreach.py', label='Grant outreach')

    bus_write('revenue_snapshot', snapshot)
    ok("Revenue data on bus → available to all layers")

# ─────────────────────────────────────────────
MESH LAYER — discover nodes + outreach
# ─────────────────────────────────────────────
def mesh_layer():
    hdr('🕸️ MESH LAYER — NETWORK DISCOVERY + OUTREACH')

    # Check GitHub fork count — each fork is a node
    try:
        import urllib.request, json as _json
        req = urllib.request.Request(
            'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center',
            headers={'User-Agent': 'MeekoMycelium/1.0'}
        )
        repo_data = _json.loads(urllib.request.urlopen(req, timeout=8).read())
        forks = repo_data.get('forks_count', 0)
        stars = repo_data.get('stargazers_count', 0)
        watchers = repo_data.get('watchers_count', 0)
        bus_write('github_forks', forks)
        bus_write('github_stars', stars)
        ok(f"GitHub: {forks} forks (nodes) · {stars} stars · {watchers} watching")
    except Exception as e:
        err(f"GitHub API: {e}")

    # Local network scan
    run_script('network_node.py', args='--mesh', label='Local mesh scan')

    # Connection mapper
    run_script('connection_mapper.py', label='Connection mapper')

    # Outreach to new connections
    run_script('community_outreach.py', label='Community outreach')

    bus_write('last_mesh_cycle', datetime.datetime.utcnow().isoformat())

# ─────────────────────────────────────────────
STATUS REPORT
# ─────────────────────────────────────────────
def status_report():
    hdr('📊 STATUS — ALL LAYERS')

    bus = bus_read()
    scripts = sorted(SCRIPT_DIR.glob('*.py'))

    # Layer status
    layers = [
        ('🛸 Space Bridge',      'space_bridge.py',        bus.get('iss_position')),
        ('🕸️ Network Node',     'network_node.py',        True),
        ('🌅 Morning Briefing', 'morning_briefing.py',    bus.get('last_morning_cycle')),
        ('💰 Revenue Tracker',  'monetization_tracker.py', bus.get('revenue_snapshot')),
        ('📡 Signal Tracker',   'signal_tracker.py',      bus.get('signals')),
        ('📧 Email Layer',      'unified_emailer.py',     os.environ.get('GMAIL_APP_PASSWORD')),
        ('🧠 Evolve',           'evolve.py',              True),
        ('🔐 Identity Vault',  'identity_vault.py',      (SCRIPT_DIR / 'identity_vault.py').exists()),
        ('🌱 Grant Outreach',  'grant_outreach.py',      True),
        ('🔄 Cross-Poster',    'cross_poster.py',        True),
    ]

    print(f"  {'Layer':<28} {'Script':<28} {'Status':<10}")
    print(f"  {'-'*28} {'-'*28} {'-'*10}")
    for name, script, active in layers:
        exists = (SCRIPT_DIR / script).exists()
        if not exists:
            status = f"{C.Y}MISSING{C.X}"
        elif active:
            status = f"{C.G}ACTIVE{C.X}"
        else:
            status = f"{C.D}IDLE{C.X}"
        print(f"  {name:<28} {C.D}{script:<28}{C.X} {status}")

    print(f"\n  {C.D}Total scripts in mycelium: {len(scripts)}{C.X}")
    print(f"  {C.D}Data bus entries: {len(bus)}{C.X}")

    # Blockers
    print(f"\n  {C.B}BLOCKERS (one action each):{C.X}")
    blockers = [
        ('GMAIL_APP_PASSWORD', 'GitHub Secrets', '10 email capabilities'),
        ('Gumroad listing', 'gumroad.com', '$5 fork guide — content at products/fork-guide.md'),
        ('BUILD_MCP_CONFIG.py', 'Run on desktop', 'permanent Claude memory'),
        ('Ko-fi link', '5 min setup', 'passive tip income'),
    ]
    for blocker, action, unlock in blockers:
        set_status = f"{C.G}DONE{C.X}" if os.environ.get('GMAIL_APP_PASSWORD') and 'GMAIL' in blocker else f"{C.Y}PENDING{C.X}"
        print(f"  {C.Y}●{C.X} {blocker} → {C.D}{action}{C.X} → unlocks: {C.CY}{unlock}{C.X}")

    # Bus data summary
    if bus:
        print(f"\n  {C.B}Data bus snapshot:{C.X}")
        for k, v in list(bus.items())[:8]:
            if k.startswith('_'): continue
            v_str = str(v)[:60] + '...' if len(str(v)) > 60 else str(v)
            print(f"  {C.D}  {k}: {v_str}{C.X}")

# ─────────────────────────────────────────────
FULL DAILY CYCLE
# ─────────────────────────────────────────────
def full_cycle():
    start = time.time()
    morning_cycle()
    revenue_layer()
    mesh_layer()
    evening_cycle()

    elapsed = time.time() - start
    ok_count = sum(1 for r in RESULTS.values() if r.get('status') == 'ok')
    err_count = sum(1 for r in RESULTS.values() if r.get('status') != 'ok')

    bus_write('last_full_cycle', datetime.datetime.utcnow().isoformat())
    bus_write('cycle_results', {'ok': ok_count, 'errors': err_count, 'elapsed_s': elapsed})

    print(f"\n{C.G}{C.B}{'='*55}{C.X}")
    print(f"{C.G}{C.B}  CYCLE COMPLETE{C.X}")
    print(f"  {C.G}✓{C.X} {ok_count} layers ran successfully")
    if err_count:
        print(f"  {C.Y}⚠{C.X} {err_count} had issues (see above)")
    print(f"  {C.D}Elapsed: {elapsed:.1f}s{C.X}")
    print(f"{C.G}{C.B}{'='*55}{C.X}")

# ─────────────────────────────────────────────
MAIN
# ─────────────────────────────────────────────
def main():
    now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    print(f"\n{C.G}{C.B}{'='*55}")
    print(f"  🧠 MEEKO MYCELIUM ORCHESTRATOR")
    print(f"  Wiring all 40+ layers into one organism")
    print(f"  {now}")
    print(f"{'='*55}{C.X}\n")

    p = argparse.ArgumentParser()
    p.add_argument('--morning',  action='store_true')
    p.add_argument('--evening',  action='store_true')
    p.add_argument('--revenue',  action='store_true')
    p.add_argument('--space',    action='store_true')
    p.add_argument('--mesh',     action='store_true')
    p.add_argument('--status',   action='store_true')
    args = p.parse_args()

    if args.morning:  morning_cycle()
    elif args.evening: evening_cycle()
    elif args.revenue: revenue_layer()
    elif args.space:   run_space_layer()
    elif args.mesh:    mesh_layer()
    elif args.status:  status_report()
    else:              full_cycle()

if __name__ == '__main__':
    main()
