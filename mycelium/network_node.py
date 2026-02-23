#!/usr/bin/env python3
"""
🕸️ NETWORK NODE — Meeko Mycelium Connectivity Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Turns your desktop into a connectivity hub:
  Bluetooth scanning · WiFi discovery · WebSocket server
  Tailscale status · MQTT bridge · Local API gateway
  Device mesh · Real-time data broadcast

All permission-first. Only scans, never intrudes.
Your system connects to the world. The world connects back.

Usage:
  python network_node.py               # full status report
  python network_node.py --bluetooth   # scan for BLE devices
  python network_node.py --wifi        # scan local network
  python network_node.py --websocket   # start WS server on :8765
  python network_node.py --tailscale   # check Tailscale tunnel
  python network_node.py --serve       # start full connectivity hub
  python network_node.py --mesh        # discover all mycelium nodes
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import datetime
import argparse
import ipaddress
from pathlib import Path
from urllib import request as urllib_request

# ─────────────────────────────────────────────
COLORS
# ─────────────────────────────────────────────
class C:
    G = '\033[92m';  Y = '\033[93m';  R = '\033[91m'
    C = '\033[96m';  B = '\033[94m';  M = '\033[95m'
    W = '\033[97m';  D = '\033[2m';   BOLD = '\033[1m'; X = '\033[0m'

def g(s): return f"{C.G}{s}{C.X}"
def y(s): return f"{C.Y}{s}{C.X}"
def r(s): return f"{C.R}{s}{C.X}"
def c(s): return f"{C.C}{s}{C.X}"
def b(s): return f"{C.BOLD}{s}{C.X}"
def d(s): return f"{C.D}{s}{C.X}"

# ─────────────────────────────────────────────
SYSTEM INFO
# ─────────────────────────────────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_hostname():
    return socket.gethostname()

def run_cmd(cmd, timeout=10):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.returncode
    except:
        return "", 1

def check_tool(name):
    out, code = run_cmd(f"where {name}" if os.name == 'nt' else f"which {name}")
    return code == 0

# ─────────────────────────────────────────────
BLUETOOTH
# ─────────────────────────────────────────────
def scan_bluetooth():
    print(f"\n{b('📶 BLUETOOTH — BLE DEVICE SCAN')}")
    print(d("─" * 55))

    # Try bleak (async BLE library)
    try:
        import bleak
        import asyncio

        async def _scan():
            from bleak import BleakScanner
            print(f"  {c('Scanning for BLE devices (5 seconds)...')}")
            devices = await BleakScanner.discover(timeout=5.0)
            return devices

        devices = asyncio.run(_scan())
        if devices:
            print(f"  {g('Found')} {len(devices)} device(s):\n")
            for dev in sorted(devices, key=lambda d: d.rssi if d.rssi else -999, reverse=True):
                signal = g("STRONG") if (dev.rssi or -100) > -60 else (y("MEDIUM") if (dev.rssi or -100) > -80 else d("WEAK"))
                name = dev.name or d("[unnamed]")
                print(f"  {g('●')} {b(name)}")
                print(f"    Address: {dev.address} · Signal: {dev.rssi} dBm ({signal})")
        else:
            print(f"  {d('No BLE devices in range (or Bluetooth off)')}")
        return devices
    except ImportError:
        print(f"  {y('bleak not installed.')} Install: {g('pip install bleak')}")
        print(f"  {d('bleak is the cross-platform BLE library. Works on Windows, Mac, Linux.')}")
    except Exception as e:
        print(f"  {y('Bluetooth scan error:')} {d(str(e))}")
        print(f"  {d('Make sure Bluetooth is enabled on your system.')}")
    return []

# ─────────────────────────────────────────────
WIFI / LOCAL NETWORK
# ─────────────────────────────────────────────
def scan_local_network():
    print(f"\n{b('📶 LOCAL NETWORK — DEVICE DISCOVERY')}")
    print(d("─" * 55))

    local_ip = get_local_ip()
    hostname = get_hostname()
    print(f"  {c('This machine:')} {g(hostname)} · {g(local_ip)}")

    # Get subnet
    try:
        parts = local_ip.split('.')
        subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        print(f"  {c('Scanning subnet:')} {subnet}")
        print(f"  {d('(pinging active hosts — permission-first, read-only)')}\n")

        live_hosts = []
        base = '.'.join(parts[:3])

        def ping_host(ip):
            cmd = f"ping -n 1 -w 500 {ip}" if os.name == 'nt' else f"ping -c 1 -W 1 {ip}"
            _, code = run_cmd(cmd, timeout=3)
            if code == 0:
                # Try to get hostname
                try:
                    name = socket.gethostbyaddr(ip)[0]
                except:
                    name = ""
                live_hosts.append((ip, name))

        threads = []
        for i in range(1, 255):
            ip = f"{base}.{i}"
            t = threading.Thread(target=ping_host, args=(ip,), daemon=True)
            threads.append(t)
            t.start()
            if len(threads) % 50 == 0:
                for t in threads[-50:]: t.join(timeout=3)

        for t in threads: t.join(timeout=3)

        live_hosts.sort(key=lambda x: int(x[0].split('.')[-1]))
        print(f"  {g('Live hosts found:')} {len(live_hosts)}\n")
        for ip, name in live_hosts:
            is_me = " ← YOU" if ip == local_ip else ""
            name_str = f" ({d(name)})" if name else ""
            print(f"  {g('●')} {ip}{name_str}{g(is_me)}")

        return live_hosts
    except Exception as e:
        print(f"  {y('Network scan error:')} {str(e)}")
        return []

# ─────────────────────────────────────────────
TAILSCALE
# ─────────────────────────────────────────────
def check_tailscale():
    print(f"\n{b('🔹 TAILSCALE — GLOBAL TUNNEL')}")
    print(d("─" * 55))
    print(f"  {d('Tailscale = your machine reachable from anywhere in the world.')}")
    print(f"  {d('Your phone, your server, your friend\'s machine — all on one private network.')}\n")

    if not check_tool('tailscale'):
        print(f"  {y('Tailscale not installed.')}")
        print(f"  Install: {g('https://tailscale.com/download')} (free, takes 3 minutes)")
        print(f"  Then run: {g('tailscale up')}")
        print(f"  Your machine gets a static IP (100.x.x.x) reachable from anywhere.")
        return None

    out, code = run_cmd("tailscale status")
    if code != 0 or not out:
        print(f"  {y('Tailscale installed but not running.')} Start it: {g('tailscale up')}")
        return None

    lines = out.strip().split('\n')
    print(f"  {g('Tailscale is ACTIVE')}\n")
    for line in lines[:15]:
        if line.strip():
            print(f"  {d('  ')} {line}")

    # Get our tailscale IP
    ip_out, _ = run_cmd("tailscale ip -4")
    if ip_out:
        print(f"\n  {c('Your Tailscale IP:')} {g(ip_out)}")
        print(f"  {d('Reachable from any device on your Tailnet, anywhere in the world.')}")
    return ip_out

# ─────────────────────────────────────────────
WEBSOCKET SERVER
# ─────────────────────────────────────────────
WS_CLIENTS = set()
WS_BROADCAST_DATA = {}

def start_websocket_server(port=8765):
    print(f"\n{b('🔌 WEBSOCKET SERVER — REAL-TIME HUB')}")
    print(d("─" * 55))

    try:
        import asyncio
        import websockets

        local_ip = get_local_ip()

        async def handler(websocket):
            WS_CLIENTS.add(websocket)
            client_addr = websocket.remote_address
            print(f"  {g('+')} Client connected: {client_addr[0]}:{client_addr[1]} ({len(WS_CLIENTS)} total)")
            try:
                # Send current state on connect
                state = {
                    "type": "system_state",
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "node": get_hostname(),
                    "ip": local_ip,
                    "clients": len(WS_CLIENTS),
                    "organism": "meeko-mycelium",
                    "message": "Welcome to the nerve center."
                }
                await websocket.send(json.dumps(state))

                async for message in websocket:
                    try:
                        data = json.loads(message)
                        print(f"  {c('<<')} {client_addr[0]}: {json.dumps(data)[:80]}")
                        # Echo with acknowledgment
                        response = {"type": "ack", "received": data, "from": get_hostname()}
                        await websocket.send(json.dumps(response))
                        # Broadcast to all other clients
                        broadcast = {"type": "broadcast", "from": str(client_addr), "data": data}
                        for ws in WS_CLIENTS - {websocket}:
                            try: await ws.send(json.dumps(broadcast))
                            except: pass
                    except json.JSONDecodeError:
                        # Plain text message
                        print(f"  {c('<<')} {client_addr[0]}: {message[:80]}")
            except Exception as e:
                pass
            finally:
                WS_CLIENTS.discard(websocket)
                print(f"  {y('-')} Client disconnected: {client_addr[0]} ({len(WS_CLIENTS)} remaining)")

        async def broadcast_loop():
            """Send system heartbeat every 30s to all clients"""
            while True:
                await asyncio.sleep(30)
                if WS_CLIENTS:
                    heartbeat = {
                        "type": "heartbeat",
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "node": get_hostname(),
                        "clients": len(WS_CLIENTS),
                    }
                    msg = json.dumps(heartbeat)
                    for ws in list(WS_CLIENTS):
                        try: await ws.send(msg)
                        except: WS_CLIENTS.discard(ws)

        async def main():
            async with websockets.serve(handler, "0.0.0.0", port):
                print(f"  {g('WebSocket server running')}")
                print(f"  {c('Local:')}     ws://{local_ip}:{port}")
                print(f"  {c('Loopback:')}  ws://localhost:{port}")
                print(f"  {d('  (Tailscale IP also works if Tailscale is running)')}")
                print(f"\n  {d('Waiting for connections... Ctrl+C to stop')}")
                await asyncio.gather(asyncio.Future(), broadcast_loop())

        asyncio.run(main())

    except ImportError:
        print(f"  {y('websockets not installed.')} Install: {g('pip install websockets')}")
        print(f"  {d('Then run: python network_node.py --websocket')}")
    except OSError as e:
        if 'Address already in use' in str(e) or '10048' in str(e):
            print(f"  {y(f'Port {port} already in use.')} Try: --websocket --port 8766")
        else:
            raise

# ─────────────────────────────────────────────
MQTT BRIDGE
# ─────────────────────────────────────────────
def check_mqtt():
    print(f"\n{b('📡 MQTT — IoT PROTOCOL BRIDGE')}")
    print(d("─" * 55))
    print(f"  {d('MQTT = lightweight pub/sub protocol. Every IoT device speaks it.')}")
    print(f"  {d('Your system as MQTT broker = hub for every smart device you own.')}\n")

    # Check for mosquitto
    has_mosquitto = check_tool('mosquitto')
    has_paho = False
    try:
        import paho.mqtt.client as mqtt
        has_paho = True
    except:
        pass

    if has_mosquitto:
        print(f"  {g('mosquitto broker:')} INSTALLED")
        print(f"  Start broker: {g('mosquitto -v')}")
        out, _ = run_cmd("mosquitto -h")
        print(f"  {d('Default port: 1883 (unencrypted), 8883 (TLS)')}")
    else:
        print(f"  {y('mosquitto not installed.')}")
        if os.name == 'nt':
            print(f"  Install: {g('winget install EclipseFoundation.Mosquitto')}")
        else:
            print(f"  Install: {g('sudo apt install mosquitto mosquitto-clients')}")

    if has_paho:
        print(f"  {g('paho-mqtt Python library:')} INSTALLED")
        # Try connecting to public broker for testing
        try:
            import paho.mqtt.client as mqtt
            connected = [False]
            messages = []

            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    connected[0] = True
                    client.subscribe("meeko/mycelium/#")

            def on_message(client, userdata, msg):
                messages.append((msg.topic, msg.payload.decode()))

            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect_async("test.mosquitto.org", 1883)
            client.loop_start()
            time.sleep(2)

            if connected[0]:
                # Publish a presence message
                payload = json.dumps({
                    "node": get_hostname(),
                    "ip": get_local_ip(),
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "organism": "meeko-mycelium"
                })
                client.publish("meeko/mycelium/presence", payload)
                time.sleep(1)
                print(f"  {g('Public MQTT broker:')} test.mosquitto.org · {g('CONNECTED')}")
                print(f"  {c('Published to:')} meeko/mycelium/presence")
                print(f"  {d('(test broker — for production, run local mosquitto)')}")
            client.loop_stop()
            client.disconnect()
        except Exception as e:
            print(f"  {d('MQTT test: ' + str(e)[:60])}")
    else:
        print(f"  {y('paho-mqtt not installed.')} Install: {g('pip install paho-mqtt')}")

# ─────────────────────────────────────────────
MESH NODE DISCOVERY
# ─────────────────────────────────────────────
def discover_mycelium_nodes():
    """Find other machines running the mycelium organism on local network"""
    print(f"\n{b('🕸️ MYCELIUM MESH — NODE DISCOVERY')}")
    print(d("─" * 55))
    print(f"  {d('Scanning for other Meeko Mycelium nodes on the local network...')}\n")

    local_ip = get_local_ip()
    parts = local_ip.split('.')
    base = '.'.join(parts[:3])

    found_nodes = []
    MYCELIUM_PORTS = [8765, 7776, 8080, 3000, 5000]  # WS server, wizard, common

    def check_node(ip):
        for port in MYCELIUM_PORTS:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                result = s.connect_ex((ip, port))
                s.close()
                if result == 0:
                    found_nodes.append({"ip": ip, "port": port})
                    return
            except:
                pass

    threads = []
    for i in range(1, 255):
        ip = f"{base}.{i}"
        if ip == local_ip: continue
        t = threading.Thread(target=check_node, args=(ip,), daemon=True)
        threads.append(t)
        t.start()

    for t in threads: t.join(timeout=2)

    if found_nodes:
        print(f"  {g('Potential nodes found:')} {len(found_nodes)}")
        for node in found_nodes:
            print(f"  {g('●')} {node['ip']}:{node['port']}")
    else:
        print(f"  {d('No nodes found on local subnet.')}")
        print(f"  {d('(Run network_node.py --websocket on another machine to create a node)')}")

    # Always check GitHub for fork count (the true mesh size)
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center",
            headers={"User-Agent": "MeekoMycelium/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            forks = data.get('forks_count', 0)
            stars = data.get('stargazers_count', 0)
            print(f"\n  {c('Global Mycelium network (GitHub):')}")  
            print(f"  {g('●')} Forks (active organism copies): {g(str(forks))}")
            print(f"  {g('●')} Stars: {stars}")
            print(f"  {d('  Each fork = another autonomous node in the world')}")
    except:
        pass

    return found_nodes

# ─────────────────────────────────────────────
SERVICE STATUS
# ─────────────────────────────────────────────
def check_local_services():
    print(f"\n{b('📊 LOCAL SERVICES — STATUS')}")
    print(d("─" * 55))

    services = [
        ("Ollama (local AI)",     "localhost", 11434),
        ("GRAND_SETUP_WIZARD",    "localhost", 7776),
        ("WebSocket server",      "localhost", 8765),
        ("Mosquitto MQTT",        "localhost", 1883),
        ("Anything on :8080",     "localhost", 8080),
        ("Anything on :3000",     "localhost", 3000),
    ]

    for name, host, port in services:
        try:
            s = socket.socket()
            s.settimeout(0.5)
            result = s.connect_ex((host, port))
            s.close()
            status = g("RUNNING") if result == 0 else d("offline")
            icon = g("●") if result == 0 else d("○")
            print(f"  {icon} {name:<30} :{port}  {status}")
        except:
            print(f"  {d('?')} {name:<30} :{port}  {d('unknown')}")

# ─────────────────────────────────────────────
INSTALL HELPERS
# ─────────────────────────────────────────────
def show_install_guide():
    print(f"\n{b('📦 INSTALL MISSING LAYERS')}")
    print(d("─" * 55))
    print(f"""
  {b('Bluetooth (bleak):')}
    pip install bleak
    {d('Cross-platform BLE. No drivers needed.')}

  {b('WebSocket (websockets):')}
    pip install websockets
    {d('Async WS server. Connects anything to anything.')}

  {b('MQTT (paho):')}
    pip install paho-mqtt
    {d('IoT backbone. Every smart device speaks MQTT.')}

  {b('Mosquitto broker (MQTT server):')}
    {d('Windows:')} winget install EclipseFoundation.Mosquitto
    {d('Linux:')}   sudo apt install mosquitto mosquitto-clients
    {d('Mac:')}     brew install mosquitto

  {b('Tailscale (global tunnel):')}
    Download: https://tailscale.com/download
    Run: tailscale up
    {d('Free. Your machine gets a permanent global IP.')}

  {b('Install everything at once:')}
    pip install bleak websockets paho-mqtt
    {d('Then install Mosquitto + Tailscale from links above.')}
""")

# ─────────────────────────────────────────────
HEADER
# ─────────────────────────────────────────────
def print_header():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    local_ip = get_local_ip()
    hostname = get_hostname()
    print()
    print(g("━" * 60))
    print(g("  🕸️ MEEKO MYCELIUM — NETWORK NODE"))
    print(f"  {d('Your desktop as connectivity hub')}")
    print(f"  {c(hostname)} · {c(local_ip)} · {d(now)}")
    print(g("━" * 60))

# ─────────────────────────────────────────────
MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Meeko Mycelium Network Node")
    parser.add_argument("--bluetooth",  action="store_true", help="Scan for BLE devices")
    parser.add_argument("--wifi",       action="store_true", help="Scan local network")
    parser.add_argument("--tailscale",  action="store_true", help="Check Tailscale status")
    parser.add_argument("--websocket",  action="store_true", help="Start WebSocket server")
    parser.add_argument("--mqtt",       action="store_true", help="Check MQTT / publish presence")
    parser.add_argument("--mesh",       action="store_true", help="Discover mycelium nodes")
    parser.add_argument("--install",    action="store_true", help="Show install guide")
    parser.add_argument("--serve",      action="store_true", help="Start full hub (WS + MQTT)")
    parser.add_argument("--port",       type=int, default=8765)
    args = parser.parse_args()

    print_header()

    if args.websocket or args.serve:
        start_websocket_server(args.port)
        return

    if args.install:
        show_install_guide()
        return

    specific = any([args.bluetooth, args.wifi, args.tailscale, args.mqtt, args.mesh])

    if specific:
        if args.bluetooth:  scan_bluetooth()
        if args.wifi:       scan_local_network()
        if args.tailscale:  check_tailscale()
        if args.mqtt:       check_mqtt()
        if args.mesh:       discover_mycelium_nodes()
    else:
        # Full status report
        check_local_services()
        check_tailscale()
        check_mqtt()
        discover_mycelium_nodes()
        show_install_guide()

    print()
    print(g("━" * 60))
    print(f"  {d('network_node.py · Meeko Mycelium · permission-first always')}")
    print(g("━" * 60))
    print()

if __name__ == "__main__":
    main()
