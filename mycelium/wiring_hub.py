#!/usr/bin/env python3
"""
Wiring Hub - Cross-Layer Data Bus
Fix: uncommented section dividers were parsed as Python identifiers (SyntaxError line 91).
Removed all COLORS / HELPERS / LAYER CHECKS style bare identifiers.
"""

import os, sys, json, time, socket, datetime, subprocess, urllib.request, urllib.error
from pathlib import Path
import argparse

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

# --- Colors ---
class C:
    G='\033[92m'; Y='\033[93m'; R='\033[91m'
    C_='\033[96m'; B='\033[1m'; D='\033[2m'; X='\033[0m'

def g(s): return C.G  + s + C.X
def y(s): return C.Y  + s + C.X
def c(s): return C.C_ + s + C.X
def b(s): return C.B  + s + C.X
def d(s): return C.D  + s + C.X
def r(s): return C.R  + s + C.X

# --- Helpers ---
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

def run_cmd(cmd, timeout=10):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.returncode
    except: return '', 1

# --- Layer checks ---
def check_local_services():
    services = {
        'ollama':    check_port('localhost', 11434),
        'websocket': check_port('localhost', 8765),
        'wizard':    check_port('localhost', 7776),
        'mqtt':      check_port('localhost', 1883),
    }
    ollama_models = []
    if services['ollama']:
        data, _ = fetch_url('http://localhost:11434/api/tags')
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
    found = {}
    for stem in ['iss_position', 'space_report', 'apod']:
        f = DATA / (stem + '.json')
        if f.exists():
            try: found[stem] = json.loads(f.read_text())
            except: pass
    iss_data, _ = fetch_url('http://api.open-notify.org/iss-now.json')
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
    tailscale_ip = None
    ts_out, ts_code = run_cmd('tailscale ip -4', timeout=5)
    if ts_code == 0 and ts_out:
        tailscale_ip = ts_out.strip()
    return {
        'hostname': hostname,
        'local_ip': local_ip,
        'tailscale_ip': tailscale_ip,
        'tailscale_active': tailscale_ip is not None,
    }

def check_payment_endpoints():
    endpoints = {
        'gallery':      'https://meekotharaccoon-cell.github.io/meeko-nerve-center/spawn.html',
        'revenue':      'https://meekotharaccoon-cell.github.io/meeko-nerve-center/revenue.html',
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
    path = DATA / 'system_state.json'
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return {}

# --- Build data bus ---
def build_wiring_status():
    print('[wiring] Checking local services...')
    local = check_local_services()
    print('[wiring] Checking GitHub...')
    github = check_github()
    print('[wiring] Checking space data...')
    space = check_space_data()
    print('[wiring] Checking network...')
    network = check_network()
    print('[wiring] Checking payment endpoints...')
    payments = check_payment_endpoints()
    system_state = load_system_state()
    return {
        'meta': {
            'timestamp': now_utc(),
            'generator': 'wiring_hub.py',
            'version': '2.0',
            'organism': 'meeko-mycelium'
        },
        'local': local,
        'github': github,
        'space': space,
        'network': network,
        'payments': payments,
        'system_state': system_state,
        'connections': {
            'local_to_github':  local['services']['ollama'] and github['status'] == 'live',
            'space_data_fresh': 'iss_live' in space,
            'network_global':   network['tailscale_active'],
            'payments_live':    all(v.get('live') for v in payments.values()),
            'email_layer':      os.environ.get('GMAIL_APP_PASSWORD') is not None,
        }
    }

def write_data_bus(wiring, data_dir=None):
    if data_dir is None:
        data_dir = Path('data') if Path('data').exists() else Path('.')
    data_dir = Path(data_dir)
    data_dir.mkdir(exist_ok=True)
    out = data_dir / 'wiring_status.json'
    out.write_text(json.dumps(wiring, indent=2))
    briefing = {
        'timestamp':      wiring['meta']['timestamp'],
        'ollama_running': wiring['local']['services']['ollama'],
        'ollama_models':  wiring['local']['ollama_models'],
        'github_forks':   wiring['github'].get('forks', 0),
        'github_stars':   wiring['github'].get('stars', 0),
        'payments_live':  wiring['connections']['payments_live'],
        'email_enabled':  wiring['connections']['email_layer'],
        'iss_lat':        wiring['space'].get('iss_live', {}).get('lat', 'N/A'),
        'iss_lon':        wiring['space'].get('iss_live', {}).get('lon', 'N/A'),
        'tailscale':      wiring['network']['tailscale_active'],
        'local_ip':       wiring['network']['local_ip'],
    }
    (data_dir / 'briefing_data.json').write_text(json.dumps(briefing, indent=2))
    revenue = {
        'timestamp':   wiring['meta']['timestamp'],
        'pages_live':  wiring['payments'],
        'github':      {'forks': wiring['github'].get('forks', 0), 'stars': wiring['github'].get('stars', 0)},
        'email_layer': wiring['connections']['email_layer'],
    }
    (data_dir / 'revenue_data.json').write_text(json.dumps(revenue, indent=2))
    print('[wiring] Written: wiring_status.json briefing_data.json revenue_data.json')
    return out

# --- Main ---
def run():
    print('\n[wiring] Wiring Hub - ' + now_utc())
    wiring = build_wiring_status()
    write_data_bus(wiring)
    gh = wiring['github']
    print('[wiring] GitHub forks: ' + str(gh.get('forks', 0)) + ' stars: ' + str(gh.get('stars', 0)))
    print('[wiring] Payments live: ' + str(wiring['connections']['payments_live']))

def main():
    parser = argparse.ArgumentParser(description='Wiring Hub - Cross-Layer Data Bus')
    parser.add_argument('--json',     action='store_true')
    parser.add_argument('--watch',    action='store_true')
    parser.add_argument('--interval', type=int, default=60)
    parser.add_argument('--no-write', action='store_true')
    args = parser.parse_args()
    wiring = build_wiring_status()
    if args.json:
        print(json.dumps(wiring, indent=2))
        return
    if not args.no_write:
        write_data_bus(wiring)
    if args.watch:
        while True:
            try:
                time.sleep(args.interval)
                wiring = build_wiring_status()
                write_data_bus(wiring)
            except KeyboardInterrupt:
                break

if __name__ == '__main__':
    main()
