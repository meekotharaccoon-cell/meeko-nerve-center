#!/usr/bin/env python3
"""
GRAND_SETUP_WIZARD.py — Web UI for All API Connections
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Runs a local web UI at http://localhost:7776

Let's you:
  - Set all API keys and secrets (stored locally, never uploaded)
  - Wire Lightning/Strike payments
  - Wire Solana/Phantom payments
  - Connect Tailscale
  - Test all connections
  - Generate .env file for local use
  - View wiring status in browser

Run:
  python GRAND_SETUP_WIZARD.py
  Then open: http://localhost:7776
"""

import os
import sys
import json
import http.server
import threading
import webbrowser
from pathlib import Path
import urllib.parse

PORT = 7776
CONFIG_FILE = Path.home() / '.meeko' / 'config.json'

CONFIG_FILE.parent.mkdir(exist_ok=True)
if not CONFIG_FILE.exists():
    CONFIG_FILE.write_text(json.dumps({}))    

def load_config():
    try: return json.loads(CONFIG_FILE.read_text())
    except: return {}

def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data, indent=2))

# ============================================================
# HTML
# ============================================================
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meeko Setup Wizard</title>
<style>
  * { box-sizing: border-box; margin:0; padding:0; }
  body { background: #0a0a0a; color: #eee; font-family: 'Courier New', monospace; padding: 24px; }
  h1 { color: #39ff14; margin-bottom: 4px; }
  .sub { color: #555; margin-bottom: 32px; font-size: 0.9rem; }
  .section { background: #111; border: 1px solid #222; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
  .section h2 { color: #39ff14; font-size: 1rem; margin-bottom: 16px; }
  label { display: block; color: #888; font-size: 0.8rem; margin-bottom: 4px; margin-top: 12px; }
  input[type=text], input[type=password] {
    width: 100%; background: #000; border: 1px solid #333; border-radius: 4px;
    padding: 8px 12px; color: #fff; font-family: monospace; font-size: 0.9rem;
  }
  input:focus { outline: none; border-color: #39ff14; }
  button {
    background: #39ff14; color: #000; border: none; border-radius: 4px;
    padding: 10px 20px; font-weight: 700; cursor: pointer; margin-top: 16px;
    font-size: 0.9rem;
  }
  button:hover { background: #2dcc10; }
  .btn-secondary { background: #222; color: #39ff14; border: 1px solid #39ff14; }
  .status { padding: 8px 12px; border-radius: 4px; margin-top: 12px; font-size: 0.85rem; }
  .ok { background: #0a2010; color: #39ff14; border: 1px solid #39ff14; }
  .warn { background: #1a1200; color: #ffaa00; border: 1px solid #ffaa00; }
  .err { background: #1a0000; color: #ff4444; border: 1px solid #ff4444; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .dot.green { background: #39ff14; }
  .dot.red { background: #ff4444; }
  .dot.yellow { background: #ffaa00; }
</style>
</head>
<body>
<h1>🕸️ Meeko Setup Wizard</h1>
<div class="sub">localhost:7776 · Configure all connections</div>

<div class="section">
  <h2>📊 System Status</h2>
  <div id="status-grid">Loading...</div>
  <button class="btn-secondary" onclick="refreshStatus()">Refresh</button>
</div>

<div class="section">
  <h2>📧 Email (Gmail)</h2>
  <p style="color:#666;font-size:0.85rem;margin-bottom:12px">
    Add to GitHub Secrets too: github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets
  </p>
  <label>Gmail App Password</label>
  <input type="password" id="gmail_pw" placeholder="xxxx xxxx xxxx xxxx">
  <label>Gmail Address</label>
  <input type="text" id="gmail_addr" placeholder="yourname@gmail.com">
  <button onclick="saveField('gmail')">Save Email Config</button>
</div>

<div class="section">
  <h2>🚀 NASA API</h2>
  <p style="color:#666;font-size:0.85rem;margin-bottom:12px">
    Free at: <a href="https://api.nasa.gov" target="_blank" style="color:#39ff14">api.nasa.gov</a> (instant, no credit card)
  </p>
  <label>NASA API Key</label>
  <input type="text" id="nasa_key" placeholder="your-nasa-api-key">
  <button onclick="saveField('nasa')">Save NASA Key</button>
</div>

<div class="section">
  <h2>⚡ Lightning / Strike</h2>
  <p style="color:#666;font-size:0.85rem;margin-bottom:12px">
    Get at: <a href="https://strike.me" target="_blank" style="color:#39ff14">strike.me</a> · Instant Bitcoin payments
  </p>
  <label>Strike API Key</label>
  <input type="password" id="strike_key" placeholder="your-strike-api-key">
  <label>Strike Username</label>
  <input type="text" id="strike_user" placeholder="your-strike-handle">
  <button onclick="saveField('strike')">Save Strike Config</button>
</div>

<div class="section">
  <h2>◎ Solana / Phantom</h2>
  <p style="color:#666;font-size:0.85rem;margin-bottom:12px">
    Wallet address from your Phantom wallet
  </p>
  <label>Solana Wallet Address</label>
  <input type="text" id="solana_addr" placeholder="Your Solana public key">
  <button onclick="saveField('solana')">Save Solana Config</button>
</div>

<div class="section">
  <h2>🔑 GitHub Token</h2>
  <p style="color:#666;font-size:0.85rem;margin-bottom:12px">
    For local scripts that push directly to GitHub.
    Get at: github.com/settings/tokens
  </p>
  <label>GitHub Personal Access Token</label>
  <input type="password" id="gh_token" placeholder="ghp_xxxx">
  <button onclick="saveField('github')">Save GitHub Token</button>
</div>

<div class="section">
  <h2>📜 Generate .env File</h2>
  <p style="color:#666;font-size:0.85rem;margin-bottom:12px">
    Creates .env in repo root. Never committed (in .gitignore).
  </p>
  <button onclick="generateEnv()">Generate .env</button>
  <div id="env-result"></div>
</div>

<script>
async function refreshStatus() {
  const r = await fetch('/status');
  const d = await r.json();
  let html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">';
  for (const [k, v] of Object.entries(d)) {
    const dot = v ? 'green' : 'red';
    const label = v ? 'OK' : 'offline';
    html += `<div><span class="dot ${dot}"></span>${k}: ${label}</div>`;
  }
  html += '</div>';
  document.getElementById('status-grid').innerHTML = html;
}

async function saveField(type) {
  const fields = {
    gmail:  {pw: document.getElementById('gmail_pw')?.value, addr: document.getElementById('gmail_addr')?.value},
    nasa:   {key: document.getElementById('nasa_key')?.value},
    strike: {key: document.getElementById('strike_key')?.value, user: document.getElementById('strike_user')?.value},
    solana: {addr: document.getElementById('solana_addr')?.value},
    github: {token: document.getElementById('gh_token')?.value},
  };
  const r = await fetch('/save', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({type, data: fields[type]})
  });
  const d = await r.json();
  alert(d.ok ? 'Saved!' : 'Error: ' + d.error);
}

async function generateEnv() {
  const r = await fetch('/generate-env', {method: 'POST'});
  const d = await r.json();
  document.getElementById('env-result').innerHTML = 
    d.ok ? `<div class="status ok">.env created: ${d.path}</div>` : 
           `<div class="status err">Error: ${d.error}</div>`;
}

refreshStatus();
</script>
</body>
</html>
"""

# ============================================================
# REQUEST HANDLER
# ============================================================
class Handler(http.server.BaseHTTPRequestHandler):
    
    def log_message(self, format, *args): pass  # suppress logs
    
    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        
        elif self.path == '/status':
            import socket
            def port_open(p):
                try:
                    s = socket.socket(); s.settimeout(0.5)
                    r = s.connect_ex(('localhost', p)); s.close()
                    return r == 0
                except: return False
            
            cfg = load_config()
            self.send_json({
                'Ollama':        port_open(11434),
                'WebSocket:8765': port_open(8765),
                'MQTT:1883':     port_open(1883),
                'Gmail config':  bool(cfg.get('gmail')),
                'NASA key':      bool(cfg.get('nasa', {}).get('key')),
                'Strike config': bool(cfg.get('strike')),
                'GitHub token':  bool(cfg.get('github', {}).get('token')),
            })
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        
        if self.path == '/save':
            try:
                cfg = load_config()
                cfg[body['type']] = body['data']
                save_config(cfg)
                self.send_json({'ok': True})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)})
        
        elif self.path == '/generate-env':
            try:
                cfg = load_config()
                env_lines = ['# Meeko Mycelium .env — DO NOT COMMIT', '']
                
                if cfg.get('gmail'):
                    env_lines.append(f"GMAIL_APP_PASSWORD={cfg['gmail'].get('pw', '')}")
                    env_lines.append(f"GMAIL_ADDRESS={cfg['gmail'].get('addr', '')}")
                if cfg.get('nasa'):
                    env_lines.append(f"NASA_API_KEY={cfg['nasa'].get('key', '')}")
                if cfg.get('strike'):
                    env_lines.append(f"STRIKE_API_KEY={cfg['strike'].get('key', '')}")
                    env_lines.append(f"STRIKE_USERNAME={cfg['strike'].get('user', '')}")
                if cfg.get('solana'):
                    env_lines.append(f"SOLANA_WALLET={cfg['solana'].get('addr', '')}")
                if cfg.get('github'):
                    env_lines.append(f"GITHUB_TOKEN={cfg['github'].get('token', '')}")
                
                # Find repo path
                candidates = [
                    Path.home() / 'Desktop' / 'UltimateAI_Master' / 'meeko-nerve-center',
                    Path.home() / 'Desktop' / 'meeko-nerve-center',
                ]
                env_path = Path.home() / '.meeko' / '.env'
                for c in candidates:
                    if c.exists():
                        env_path = c / '.env'
                        break
                
                env_path.write_text('\n'.join(env_lines))
                self.send_json({'ok': True, 'path': str(env_path)})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)})
        else:
            self.send_response(404)
            self.end_headers()

# ============================================================
# MAIN
# ============================================================
def main():
    print(f"\n\033[92m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print(f"\033[92m  GRAND SETUP WIZARD — localhost:{PORT}\033[0m")
    print(f"\033[92m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m\n")
    
    server = http.server.HTTPServer(('localhost', PORT), Handler)
    
    print(f"\033[96m  Opening browser: http://localhost:{PORT}\033[0m")
    print(f"\033[2m  Press Ctrl+C to stop\033[0m\n")
    
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n\033[92m  Wizard stopped.\033[0m")

if __name__ == '__main__':
    main()
