#!/usr/bin/env python3
"""
🕸️ NETWORK NODE — Meeko Mycelium Connectivity Layer
Fix: uncommented section dividers (COLORS, SYSTEM INFO, BLUETOOTH etc.)
were being parsed as Python identifiers causing SyntaxError.
"""

import os, sys, json, time, socket, threading, subprocess, datetime, argparse
from pathlib import Path
from urllib import request as urllib_request

# --- Colors ---
class C:
    G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'
    C = '\033[96m'; B = '\033[94m'; M = '\033[95m'
    W = '\033[97m'; D = '\033[2m';  BOLD = '\033[1m'; X = '\033[0m'

def g(s): return C.G    + s + C.X
def y(s): return C.Y    + s + C.X
def r(s): return C.R    + s + C.X
def c(s): return C.C    + s + C.X
def b(s): return C.BOLD + s + C.X
def d(s): return C.D    + s + C.X

# --- System info ---
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def get_hostname():
    return socket.gethostname()

def run_cmd(cmd, timeout=10):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.returncode
    except:
        return '', 1

def check_tool(name):
    out, code = run_cmd('where ' + name if os.name == 'nt' else 'which ' + name)
    return code == 0

# --- Bluetooth ---
def scan_bluetooth():
    print('\n' + b('\U0001f4f6 BLUETOOTH \u2014 BLE DEVICE SCAN'))
    print(d('\u2500' * 55))
    try:
        import bleak, asyncio
        async def _scan():
            from bleak import BleakScanner
            print('  ' + c('Scanning for BLE devices (5 seconds)...'))
            return await BleakScanner.discover(timeout=5.0)
        devices = asyncio.run(_scan())
        if devices:
            print('  ' + g('Found') + ' ' + str(len(devices)) + ' device(s):\n')
            for dev in sorted(devices, key=lambda d: d.rssi if d.rssi else -999, reverse=True):
                signal = g('STRONG') if (dev.rssi or -100) > -60 else (y('MEDIUM') if (dev.rssi or -100) > -80 else d('WEAK'))
                print('  ' + g('●') + ' ' + b(dev.name or d('[unnamed]')))
                print('    Address: ' + dev.address + ' · Signal: ' + str(dev.rssi) + ' dBm (' + signal + ')')
        else:
            print('  ' + d('No BLE devices in range (or Bluetooth off)'))
        return devices
    except ImportError:
        print('  ' + y('bleak not installed.') + ' Install: ' + g('pip install bleak'))
    except Exception as e:
        print('  ' + y('Bluetooth scan error: ') + d(str(e)))
    return []

# --- WiFi / local network ---
def scan_local_network():
    print('\n' + b('\U0001f4f6 LOCAL NETWORK \u2014 DEVICE DISCOVERY'))
    print(d('\u2500' * 55))
    local_ip = get_local_ip()
    hostname = get_hostname()
    print('  ' + c('This machine: ') + g(hostname) + ' · ' + g(local_ip))
    try:
        parts = local_ip.split('.')
        base  = '.'.join(parts[:3])
        print('  ' + c('Scanning subnet: ') + base + '.0/24\n')
        live_hosts = []
        def ping_host(ip):
            cmd = 'ping -n 1 -w 500 ' + ip if os.name == 'nt' else 'ping -c 1 -W 1 ' + ip
            _, code = run_cmd(cmd, timeout=3)
            if code == 0:
                try:   name = socket.gethostbyaddr(ip)[0]
                except: name = ''
                live_hosts.append((ip, name))
        threads = []
        for i in range(1, 255):
            t = threading.Thread(target=ping_host, args=(base + '.' + str(i),), daemon=True)
            threads.append(t); t.start()
            if len(threads) % 50 == 0:
                for tt in threads[-50:]: tt.join(timeout=3)
        for t in threads: t.join(timeout=3)
        live_hosts.sort(key=lambda x: int(x[0].split('.')[-1]))
        print('  ' + g('Live hosts: ') + str(len(live_hosts)) + '\n')
        for ip, name in live_hosts:
            is_me = ' \u2190 YOU' if ip == local_ip else ''
            name_str = ' (' + d(name) + ')' if name else ''
            print('  ' + g('●') + ' ' + ip + name_str + g(is_me))
        return live_hosts
    except Exception as e:
        print('  ' + y('Network scan error: ') + str(e))
        return []

# --- Tailscale ---
def check_tailscale():
    print('\n' + b('\U0001f539 TAILSCALE \u2014 GLOBAL TUNNEL'))
    print(d('\u2500' * 55))
    if not check_tool('tailscale'):
        print('  ' + y('Tailscale not installed.'))
        print('  Install: ' + g('https://tailscale.com/download'))
        return None
    out, code = run_cmd('tailscale status')
    if code != 0 or not out:
        print('  ' + y('Tailscale installed but not running. Start: ') + g('tailscale up'))
        return None
    print('  ' + g('Tailscale ACTIVE') + '\n')
    for line in out.strip().split('\n')[:15]:
        if line.strip(): print('    ' + line)
    ip_out, _ = run_cmd('tailscale ip -4')
    if ip_out:
        print('\n  ' + c('Your Tailscale IP: ') + g(ip_out))
    return ip_out

# --- WebSocket server ---
WS_CLIENTS = set()

def start_websocket_server(port=8765):
    print('\n' + b('\U0001f50c WEBSOCKET SERVER \u2014 REAL-TIME HUB'))
    print(d('\u2500' * 55))
    try:
        import asyncio, websockets
        local_ip = get_local_ip()
        async def handler(ws):
            WS_CLIENTS.add(ws)
            addr = ws.remote_address
            print('  ' + g('+') + ' Client: ' + addr[0])
            try:
                state = {'type': 'system_state', 'node': get_hostname(),
                         'ip': local_ip, 'organism': 'meeko-mycelium'}
                await ws.send(json.dumps(state))
                async for msg in ws:
                    try:
                        data = json.loads(msg)
                        await ws.send(json.dumps({'type': 'ack', 'received': data}))
                    except: pass
            finally:
                WS_CLIENTS.discard(ws)
                print('  ' + y('-') + ' Client disconnected: ' + addr[0])
        async def run():
            async with websockets.serve(handler, '0.0.0.0', port):
                print('  ' + g('Running on ws://') + local_ip + ':' + str(port))
                print('  ' + d('Ctrl+C to stop'))
                await asyncio.Future()
        asyncio.run(run())
    except ImportError:
        print('  ' + y('websockets not installed. ') + 'Install: ' + g('pip install websockets'))
    except OSError as e:
        print('  ' + y('Port ' + str(port) + ' in use: ') + str(e))

# --- MQTT bridge ---
def check_mqtt():
    print('\n' + b('\U0001f4e1 MQTT \u2014 IoT PROTOCOL BRIDGE'))
    print(d('\u2500' * 55))
    if check_tool('mosquitto'):
        print('  ' + g('mosquitto broker: INSTALLED'))
    else:
        print('  ' + y('mosquitto not installed.'))
        if os.name == 'nt': print('  Install: ' + g('winget install EclipseFoundation.Mosquitto'))
        else:               print('  Install: ' + g('sudo apt install mosquitto mosquitto-clients'))
    try:
        import paho.mqtt.client as mqtt
        print('  ' + g('paho-mqtt: INSTALLED'))
        connected = [False]
        def on_connect(cl, ud, fl, rc):
            if rc == 0: connected[0] = True
        cl = mqtt.Client()
        cl.on_connect = on_connect
        cl.connect_async('test.mosquitto.org', 1883)
        cl.loop_start(); time.sleep(2)
        if connected[0]:
            payload = json.dumps({'node': get_hostname(), 'ip': get_local_ip(),
                                   'ts': datetime.datetime.utcnow().isoformat()})
            cl.publish('meeko/mycelium/presence', payload)
            print('  ' + g('test.mosquitto.org: CONNECTED'))
        cl.loop_stop(); cl.disconnect()
    except ImportError:
        print('  ' + y('paho-mqtt not installed. ') + 'Install: ' + g('pip install paho-mqtt'))
    except Exception as e:
        print('  ' + d('MQTT: ' + str(e)[:60]))

# --- Mesh node discovery ---
def discover_mycelium_nodes():
    print('\n' + b('\U0001f578\ufe0f MYCELIUM MESH \u2014 NODE DISCOVERY'))
    print(d('\u2500' * 55))
    local_ip = get_local_ip()
    parts    = local_ip.split('.')
    base     = '.'.join(parts[:3])
    found    = []
    PORTS    = [8765, 7776, 8080, 3000, 5000]
    def check_node(ip):
        for port in PORTS:
            try:
                s = socket.socket()
                s.settimeout(0.5)
                if s.connect_ex((ip, port)) == 0:
                    found.append({'ip': ip, 'port': port})
                    return
            except: pass
            finally:
                try: s.close()
                except: pass
    threads = []
    for i in range(1, 255):
        ip = base + '.' + str(i)
        if ip == local_ip: continue
        t = threading.Thread(target=check_node, args=(ip,), daemon=True)
        threads.append(t); t.start()
    for t in threads: t.join(timeout=2)
    if found:
        print('  ' + g('Nodes found: ') + str(len(found)))
        for n in found: print('  ' + g('●') + ' ' + n['ip'] + ':' + str(n['port']))
    else:
        print('  ' + d('No nodes on local subnet.'))
    try:
        req = urllib_request.Request(
            'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center',
            headers={'User-Agent': 'MeekoMycelium/1.0'}
        )
        data = json.loads(urllib_request.urlopen(req, timeout=5).read())
        forks = data.get('forks_count', 0)
        stars = data.get('stargazers_count', 0)
        print('\n  ' + c('Global network (GitHub):'))
        print('  ' + g('●') + ' Forks (organism copies): ' + g(str(forks)))
        print('  ' + g('●') + ' Stars: ' + str(stars))
    except: pass
    return found

# --- Local service status ---
def check_local_services():
    print('\n' + b('\U0001f4ca LOCAL SERVICES'))
    print(d('\u2500' * 55))
    services = [
        ('Ollama (local AI)',   'localhost', 11434),
        ('GRAND_SETUP_WIZARD',  'localhost', 7776),
        ('WebSocket server',    'localhost', 8765),
        ('Mosquitto MQTT',      'localhost', 1883),
        ('Port 8080',           'localhost', 8080),
        ('Port 3000',           'localhost', 3000),
    ]
    for name, host, port in services:
        try:
            s = socket.socket()
            s.settimeout(0.5)
            up = s.connect_ex((host, port)) == 0
            s.close()
            status = g('RUNNING') if up else d('offline')
            icon   = g('●')      if up else d('○')
            print('  ' + icon + ' ' + name.ljust(30) + ':' + str(port) + '  ' + status)
        except:
            print('  ' + d('?') + ' ' + name.ljust(30) + ':' + str(port) + '  ' + d('unknown'))

# --- Header ---
def print_header():
    now      = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    local_ip = get_local_ip()
    hostname = get_hostname()
    print()
    print(g('\u2501' * 55))
    print(g('  \U0001f578\ufe0f MEEKO MYCELIUM \u2014 NETWORK NODE'))
    print('  ' + c(hostname) + ' \xb7 ' + c(local_ip) + ' \xb7 ' + d(now))
    print(g('\u2501' * 55))

# --- Main ---
def main():
    parser = argparse.ArgumentParser(description='Meeko Mycelium Network Node')
    parser.add_argument('--bluetooth', action='store_true')
    parser.add_argument('--wifi',      action='store_true')
    parser.add_argument('--tailscale', action='store_true')
    parser.add_argument('--websocket', action='store_true')
    parser.add_argument('--mqtt',      action='store_true')
    parser.add_argument('--mesh',      action='store_true')
    parser.add_argument('--serve',     action='store_true')
    parser.add_argument('--port',      type=int, default=8765)
    args = parser.parse_args()

    print_header()

    if args.websocket or args.serve:
        start_websocket_server(args.port)
        return

    specific = any([args.bluetooth, args.wifi, args.tailscale, args.mqtt, args.mesh])
    if specific:
        if args.bluetooth:  scan_bluetooth()
        if args.wifi:       scan_local_network()
        if args.tailscale:  check_tailscale()
        if args.mqtt:       check_mqtt()
        if args.mesh:       discover_mycelium_nodes()
    else:
        check_local_services()
        check_tailscale()
        check_mqtt()
        discover_mycelium_nodes()

    print()
    print(g('\u2501' * 55))
    print('  ' + d('network_node.py \xb7 Meeko Mycelium \xb7 permission-first always'))
    print(g('\u2501' * 55) + '\n')

if __name__ == '__main__':
    main()
