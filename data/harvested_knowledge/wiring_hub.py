#!/usr/bin/env python3
"""
🕸️ WIRING HUB — Cross-Layer Data Bus
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reads all system layers, writes unified JSON data bus.
Every layer talks to every other layer through this hub.

What it reads:
  - Space data (space_bridge outputs)
  - Network state (network_node outputs)
  - System state (update_state outputs)
  - Local services (Ollama, ChromaDB, SQLite)
  - GitHub status (repo, workflows, forks)
  - Revenue status (payment endpoints)

What it writes:
  - data/wiring_status.json  — full system state for web pages
  - data/briefing_data.json  — for morning briefing email
  - data/revenue_data.json   — for revenue dashboard
  - WIRING_MAP.md connection table  — updated status

What connects to it:
  - spawn.html reads data/wiring_status.json for live widgets
  - dashboard.html reads all data/ files
  - GitHub Actions runs this after space_bridge
  - Morning briefing uses briefing_data.json

Usage:
  python wiring_hub.py              # full status + write data bus
  python wiring_hub.py --json       # JSON only (for scripts)
  python wiring_hub.py --briefing   # write briefing_data.json
  python wiring_hub.py --revenue    # write revenue_data.json
  python wiring_hub.py --watch      # continuous mode (every 60s)
"""

import os
import sys
import json
import time
import socket
import datetime
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
import argparse

# ─────────────────────────────────────────────────────
COLORS
# ─────────────────────────────────────────────────────
class C:
    G='\033[92m'; Y='\033[93m'; R='\033[91m'
    C='\033[96m'; B='\033[1m'; D='\033[2m'; X='\033[0m'

def g(s): return f"{C.G}{s}{C.X}"
def y(s): return f"{C.Y}{s}{C.X}"
def c(s): return f"{C.C}{s}{C.X}"
def b(s): return f"{C.B}{s}{C.X}"
def d(s): return f"{C.D}{s}{C.X}"
def r(s): return f"{C.R}{s}{C.X}"

# ─────────────────────────────────────────────────────
HELPERS
# ─────────────────────────────────────────────────────
def now_utc(): return datetime.datetime.utcnow().isoformat() + 'Z'

def check_port(host, port, timeout=1):
    try:
        s = socket.socket()
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except: return False

def fetch_url(url, timeout=5):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MeekoMycelium/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read()), None
    except Exception as e:
        return None, str(e)

def run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except: return '', 1

# ─────────────────────────────────────────────────────
LAYER CHECKS
# ─────────────────────────────────────────────────────
def check_local_services():
    services = {
        'ollama':    check_port('localhost', 11434),
        'websocket': check_port('localhost', 8765),
        'wizard':    check_port('localhost', 7776),
        'mqtt':      check_port('localhost', 1883),
    }
    # Check Ollama models if running
    ollama_models = []
    if services['ollama']:
        data, err = fetch_url('http://localhost:11434/api/tags')
        if data and 'models' in data:
            ollama_models = [m['name'] for m in data['models']]
    return {'services': services, 'ollama_models': ollama_models}

def check_github():
    data, err = fetch_url('https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center')
    if err or not data:
        return {'status': 'error', 'error': err}
    return {
        'status': 'live',
        'forks': data.get('forks_count', 0),
        'stars': data.get('stargazers_count', 0),
        'watchers': data.get('watchers_count', 0),
        'open_issues': data.get('open_issues_count', 0),
        'last_push': data.get('pushed_at', ''),
        'size_kb': data.get('size', 0),
    }

def check_space_data():
    # Check if space_bridge has run and left data
    data_dir = Path('data')
    space_files = [
        data_dir / 'iss_position.json',
        data_dir / 'space_report.json',
        data_dir / 'apod.json',
    ]
    found = {}
    for f in space_files:
        if f.exists():
            try:
                found[f.stem] = json.loads(f.read_text())
            except: pass

    # Also try live ISS position
    iss_data, err = fetch_url('http://api.open-notify.org/iss-now.json')
    if iss_data:
        found['iss_live'] = {
            'lat': iss_data.get('iss_position', {}).get('latitude', 0),
            'lon': iss_data.get('iss_position', {}).get('longitude', 0),
            'timestamp': iss_data.get('timestamp', 0)
        }
    return found

def check_network():
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        hostname, local_ip = 'unknown', '127.0.0.1'

    # Check Tailscale
    tailscale_ip = None
    ts_out, ts_code = run('tailscale ip -4', timeout=5)
    if ts_code == 0 and ts_out:
        tailscale_ip = ts_out.strip()

    return {
        'hostname': hostname,
        'local_ip': local_ip,
        'tailscale_ip': tailscale_ip,
        'tailscale_active': tailscale_ip is not None,
    }

def check_payment_endpoints():
    """Check that payment pages are reachable"""
    endpoints = {
        'gallery': 'https://meekotharaccoon-cell.github.io/meeko-nerve-center/spawn.html',
        'revenue': 'https://meekotharaccoon-cell.github.io/meeko-nerve-center/revenue.html',
        'proliferator': 'https://meekotharaccoon-cell.github.io/meeko-nerve-center/proliferator.html',
    }
    results = {}
    for name, url in endpoints.items():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'MeekoWiringHub/1.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                results[name] = {'status': resp.status, 'live': resp.status == 200}
        except Exception as e:
            results[name] = {'status': 0, 'live': False, 'error': str(e)[:50]}
    return results

def load_system_state():
    """Load the auto-updated system state JSON"""
    path = Path('data/system_state.json')
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return {}

# ─────────────────────────────────────────────────────
BUILD THE DATA BUS
# ─────────────────────────────────────────────────────
def build_wiring_status():
    print(f"  {c('Checking local services...')}")
    local = check_local_services()

    print(f"  {c('Checking GitHub...')}")
    github = check_github()

    print(f"  {c('Checking space data...')}")
    space = check_space_data()

    print(f"  {c('Checking network...')}")
    network = check_network()

    print(f"  {c('Checking payment endpoints...')}")
    payments = check_payment_endpoints()

    system_state = load_system_state()

    wiring = {
        'meta': {
            'timestamp': now_utc(),
            'generator': 'wiring_hub.py',
            'version': '1.0',
            'organism': 'meeko-mycelium'
        },
        'local': local,
        'github': github,
        'space': space,
        'network': network,
        'payments': payments,
        'system_state': system_state,
        'connections': {
            'local_to_github': local['services']['ollama'] and github['status'] == 'live',
            'space_data_fresh': 'iss_live' in space,
            'network_global': network['tailscale_active'],
            'payments_live': all(v.get('live') for v in payments.values()),
            'email_layer': os.environ.get('GMAIL_APP_PASSWORD') is not None,
        }
    }
    return wiring

def write_data_bus(wiring, data_dir=None):
    if data_dir is None:
        # Try repo data dir, fallback to cwd
        if Path('data').exists():
            data_dir = Path('data')
        else:
            data_dir = Path('.')

    data_dir = Path(data_dir)
    data_dir.mkdir(exist_ok=True)

    # Main wiring status
    out = data_dir / 'wiring_status.json'
    out.write_text(json.dumps(wiring, indent=2))
    print(f"  {g('Written:')} {out}")

    # Briefing data (flat summary for email)
    briefing = {
        'timestamp': wiring['meta']['timestamp'],
        'ollama_running': wiring['local']['services']['ollama'],
        'ollama_models': wiring['local']['ollama_models'],
        'github_forks': wiring['github'].get('forks', 0),
        'github_stars': wiring['github'].get('stars', 0),
        'payments_live': wiring['connections']['payments_live'],
        'email_enabled': wiring['connections']['email_layer'],
        'iss_lat': wiring['space'].get('iss_live', {}).get('lat', 'N/A'),
        'iss_lon': wiring['space'].get('iss_live', {}).get('lon', 'N/A'),
        'tailscale': wiring['network']['tailscale_active'],
        'local_ip': wiring['network']['local_ip'],
    }
    briefing_out = data_dir / 'briefing_data.json'
    briefing_out.write_text(json.dumps(briefing, indent=2))
    print(f"  {g('Written:')} {briefing_out}")

    # Revenue data
    revenue = {
        'timestamp': wiring['meta']['timestamp'],
        'pages_live': wiring['payments'],
        'github': {
            'forks': wiring['github'].get('forks', 0),
            'stars': wiring['github'].get('stars', 0),
        },
        'email_layer': wiring['connections']['email_layer'],
        'notes': [
            'Gaza Rose gallery live (PayPal inline)',
            'Bitcoin address active',
            'Fork guide ready — needs Gumroad listing',
            'Ko-fi needs account creation',
        ]
    }
    revenue_out = data_dir / 'revenue_data.json'
    revenue_out.write_text(json.dumps(revenue, indent=2))
    print(f"  {g('Written:')} {revenue_out}")

    return out, briefing_out, revenue_out

# ─────────────────────────────────────────────────────
PRINT STATUS
# ─────────────────────────────────────────────────────
def print_status(wiring):
    print(f"\n{b('🕸️ WIRING STATUS')}")
    print(d("━" * 60))

    # Local services
    print(f"\n  {b('LOCAL SERVICES')}")
    for svc, running in wiring['local']['services'].items():
        icon = g('●') if running else d('○')
        status = g('RUNNING') if running else d('offline')
        print(f"  {icon} {svc:<20} {status}")
    if wiring['local']['ollama_models']:
        print(f"  {d('  Models:')} {', '.join(wiring['local']['ollama_models'])}")

    # GitHub
    print(f"\n  {b('GITHUB')}")
    gh = wiring['github']
    if gh.get('status') == 'live':
        print(f"  {g('●')} meeko-nerve-center   {g('LIVE')}")
        print(f"    Forks: {gh['forks']} · Stars: {gh['stars']} · Last push: {gh.get('last_push', 'N/A')[:10]}")
    else:
        print(f"  {y('●')} GitHub: {gh.get('error', 'offline')}")

    # Space
    print(f"\n  {b('SPACE LAYER')}")
    if 'iss_live' in wiring['space']:
        iss = wiring['space']['iss_live']
        print(f"  {g('●')} ISS live    lat:{iss['lat']:.2f} lon:{iss['lon']:.2f}")
    else:
        print(f"  {d('○')} ISS: no live data (space_bridge not run yet)")

    # Network
    print(f"\n  {b('NETWORK')}")
    net = wiring['network']
    print(f"  {g('●')} {net['hostname']} · {net['local_ip']}")
    if net['tailscale_active']:
        print(f"  {g('●')} Tailscale: {net['tailscale_ip']}")
    else:
        print(f"  {d('○')} Tailscale: not running")

    # Payments
    print(f"\n  {b('PAYMENT ENDPOINTS')}")
    for name, status in wiring['payments'].items():
        icon = g('●') if status.get('live') else r('○')
        live = g('LIVE') if status.get('live') else r('DOWN')
        print(f"  {icon} {name:<20} {live}")

    # Cross-layer connections
    print(f"\n  {b('CROSS-LAYER CONNECTIONS')}")
    conns = wiring['connections']
    items = [
        ('local → github',   conns['local_to_github']),
        ('space data fresh',  conns['space_data_fresh']),
        ('global network',    conns['network_global']),
        ('payments live',     conns['payments_live']),
        ('email layer',       conns['email_layer']),
    ]
    for name, status in items:
        icon = g('●') if status else y('○')
        label = g('CONNECTED') if status else y('DARK')
        print(f"  {icon} {name:<25} {label}")

    print()

# ─────────────────────────────────────────────────────
WATCH MODE
# ─────────────────────────────────────────────────────
def watch_mode(interval=60):
    print(f"  {c('Watch mode: polling every')} {interval}s {d('(Ctrl+C to stop)')}")
    while True:
        try:
            wiring = build_wiring_status()
            write_data_bus(wiring)
            print_status(wiring)
            print(f"  {d(f'Next poll in {interval}s...')}")
            time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n  {g('Watch mode stopped.')}")
            break

# ─────────────────────────────────────────────────────
MAIN
# ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Wiring Hub — Cross-Layer Data Bus")
    parser.add_argument('--json',     action='store_true', help='JSON output only')
    parser.add_argument('--briefing', action='store_true', help='Write briefing data')
    parser.add_argument('--revenue',  action='store_true', help='Write revenue data')
    parser.add_argument('--watch',    action='store_true', help='Continuous polling')
    parser.add_argument('--interval', type=int, default=60)
    parser.add_argument('--no-write', action='store_true', help='Status only, no file writes')
    args = parser.parse_args()

    if not args.json:
        print()
        print(g("━" * 60))
        print(g("  🕸️ MEEKO WIRING HUB — Cross-Layer Data Bus"))
        print(f"  {d('All layers talking to all layers.')}")
        print(g("━" * 60))
        print()

    if args.watch:
        watch_mode(args.interval)
        return

    wiring = build_wiring_status()

    if args.json:
        print(json.dumps(wiring, indent=2))
        return

    print_status(wiring)

    if not args.no_write:
        write_data_bus(wiring)

    print(g("━" * 60))
    print()

if __name__ == '__main__':
    main()
