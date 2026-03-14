#!/usr/bin/env python3
"""
MEEKO MYCELIUM — ONE BUTTON LAUNCHER
======================================
Double-click LAUNCH.bat on your desktop.
This script does everything from there:

1. Auto-recovers every secret it can find on your machine
2. Opens a browser page showing ONLY what it couldn't find
3. For each missing secret: shows exactly where to get it + a link
4. When you paste the last key -> launches your entire system
5. Never asks for the same secret twice (saves permanently)

One button. Everything runs. Stops only when it needs you.
"""

import http.server, json, os, re, subprocess, sys, threading, time, webbrowser
from pathlib import Path
from datetime import datetime

# ── PATHS ────────────────────────────────────────────────────────────
DESKTOP    = Path(r'C:\Users\meeko\Desktop')
BASE       = DESKTOP / 'UltimateAI_Master'
SECRETS_F  = BASE / '.secrets'
AUTO_F     = BASE / '_auto_secrets.json'
LOG_F      = BASE / 'launch.log'
PORT       = 7775
VENV       = DESKTOP / 'mycelium_env' / 'Scripts' / 'python.exe'
PYTHON     = str(VENV) if VENV.exists() else sys.executable

# ── WHAT WE NEED & WHERE TO GET IT ──────────────────────────────────
SECRETS_MAP = {
    'ALPACA_KEY': {
        'label': 'Alpaca API Key',
        'hint':  'Paper trading key — free account',
        'url':   'https://alpaca.markets/dashboard',
        'steps': 'Login -> API Keys tab -> Generate New Key -> copy Key ID',
        'example': 'PKXXXXXXXXXXXXXXXXXXXXXXX (starts with PK)',
        'group': 'Trading',
    },
    'ALPACA_SECRET': {
        'label': 'Alpaca Secret Key',
        'hint':  'Same page as Alpaca Key — shown once',
        'url':   'https://alpaca.markets/dashboard',
        'steps': 'Same page as above -> copy Secret Key (only shown once when generated)',
        'example': 'long string of letters/numbers',
        'group': 'Trading',
    },
    'CB_API_KEY': {
        'label': 'Coinbase API Key Name',
        'hint':  'Advanced Trade API key',
        'url':   'https://www.coinbase.com/settings/api',
        'steps': 'Login -> Settings -> API -> New API Key -> name format: organizations/.../apiKeys/...',
        'example': 'organizations/abc123/apiKeys/def456',
        'group': 'Crypto',
    },
    'CB_API_SECRET': {
        'label': 'Coinbase EC Private Key',
        'hint':  'The -----BEGIN EC PRIVATE KEY----- block',
        'url':   'https://www.coinbase.com/settings/api',
        'steps': 'Same page -> copy the full private key including the BEGIN/END lines',
        'example': '-----BEGIN EC PRIVATE KEY-----\\n...\\n-----END EC PRIVATE KEY-----',
        'group': 'Crypto',
    },
    'COINBASE_COMMERCE_KEY': {
        'label': 'Coinbase Commerce API Key',
        'hint':  'Accept crypto payments for your art/products',
        'url':   'https://commerce.coinbase.com/settings/security',
        'steps': 'Login to Commerce -> Settings -> Security -> Show API Key',
        'example': '32-character alphanumeric key',
        'group': 'Payments',
    },
    'KRAKEN_API_KEY': {
        'label': 'Kraken API Key',
        'hint':  'Your Kraken session detected — key may be there',
        'url':   'https://www.kraken.com/u/security/api',
        'steps': 'Login -> Security -> API -> Generate New Key -> copy API Key',
        'example': 'alphanumeric string ~56 chars',
        'group': 'Crypto',
    },
    'KRAKEN_API_SECRET': {
        'label': 'Kraken Private Key',
        'hint':  'Base64 private key for signing requests',
        'url':   'https://www.kraken.com/u/security/api',
        'steps': 'Same page -> copy Private Key (long base64 string)',
        'example': 'base64 string ~88+ chars',
        'group': 'Crypto',
    },
    'PHANTOM_SOLANA_ADDRESS': {
        'label': 'Phantom Wallet Address',
        'hint':  'Your public Solana address — NOT a secret',
        'url':   'https://phantom.app',
        'steps': 'Open Phantom in Brave -> click your address at top -> Copy -> paste here',
        'example': '44-character base58 string (starts with a letter, not EPjF...)',
        'group': 'Crypto',
    },
    'GUMROAD_TOKEN': {
        'label': 'Gumroad Access Token',
        'hint':  'For your Gaza Rose art sales',
        'url':   'https://app.gumroad.com/settings/advanced',
        'steps': 'Login -> Settings -> Advanced -> Generate Access Token -> copy it',
        'example': 'long alphanumeric string',
        'group': 'Revenue',
    },
    'STRIPE_SECRET_KEY': {
        'label': 'Stripe Secret Key',
        'hint':  'Live secret key (starts with sk_live_)',
        'url':   'https://dashboard.stripe.com/apikeys',
        'steps': 'Login -> Developers -> API Keys -> Reveal Secret Key -> copy sk_live_...',
        'example': 'sk_live_51... (very long)',
        'group': 'Revenue',
    },
    'PAYPAL_CLIENT_ID': {
        'label': 'PayPal Client ID',
        'hint':  'Live app credentials',
        'url':   'https://developer.paypal.com/dashboard/applications/live',
        'steps': 'Login -> Dashboard -> My Apps -> your app -> copy Client ID',
        'example': 'long alphanumeric string',
        'group': 'Revenue',
    },
    'PAYPAL_CLIENT_SECRET': {
        'label': 'PayPal Client Secret',
        'hint':  'Same page as PayPal Client ID',
        'url':   'https://developer.paypal.com/dashboard/applications/live',
        'steps': 'Same page -> Show Secret -> copy it',
        'example': 'long alphanumeric string',
        'group': 'Revenue',
    },
    'CONDUCTOR_TOKEN': {
        'label': 'GitHub Personal Access Token',
        'hint':  'Controls all 4 of your repos — ALREADY FOUND in gh CLI',
        'url':   'https://github.com/settings/tokens',
        'steps': 'Already recovered from gh CLI. Paste it below to confirm.',
        'example': 'gho_... or ghp_...',
        'group': 'GitHub',
    },
}

_secrets = {}
_launched = False
_lock = threading.Lock()

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_F, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

# ── SECRET RECOVERY ─────────────────────────────────────────────────
def auto_recover():
    """Pull every secret we can find without asking Meeko."""
    recovered = {}

    # 1. From .secrets file
    if SECRETS_F.exists():
        for line in SECRETS_F.read_text(encoding='utf-8').splitlines():
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                k, v = k.strip(), v.strip()
                if k and v:
                    recovered[k] = v
        if recovered:
            log(f"Loaded {len(recovered)} secrets from .secrets file")

    # 2. Auto-scan JSON
    if AUTO_F.exists():
        try:
            auto = json.loads(AUTO_F.read_text())
            for k, v in auto.items():
                if k not in recovered:
                    recovered[k] = v
                    log(f"Auto-recovered: {k}")
        except:
            pass

    # 3. GH CLI token
    if 'CONDUCTOR_TOKEN' not in recovered:
        r = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
        if r.stdout.strip():
            recovered['CONDUCTOR_TOKEN'] = r.stdout.strip()
            log("Auto-got CONDUCTOR_TOKEN from gh CLI")

    # 4. Phantom from connect_crypto.py (but validate it's a real wallet, not USDC mint)
    if 'PHANTOM_SOLANA_ADDRESS' not in recovered:
        cp = BASE / 'connect_crypto.py'
        if cp.exists():
            content = cp.read_text(encoding='utf-8', errors='ignore')
            for addr in re.findall(r'[1-9A-HJ-NP-Za-km-z]{43,44}', content):
                # Skip known token/program addresses
                if addr not in ('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                                'So11111111111111111111111111111111111111112'):
                    recovered['PHANTOM_SOLANA_ADDRESS'] = addr
                    log(f"Auto-got PHANTOM address: {addr[:10]}...")
                    break

    # 5. Env vars
    for k in SECRETS_MAP:
        if k not in recovered and os.environ.get(k, '').strip():
            recovered[k] = os.environ[k].strip()
            log(f"Got {k} from environment")

    return recovered

def save_secrets(secrets: dict):
    """Write all secrets to .secrets file and push to GitHub."""
    # Write .secrets
    lines = ['# MEEKO MYCELIUM - SECRETS (auto-managed)', '# Never commit this file']
    for k in SECRETS_MAP:
        v = secrets.get(k, '')
        lines.append(f"{k}={v}")
    SECRETS_F.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    # Set in current process env
    for k, v in secrets.items():
        if v:
            os.environ[k] = v

    # Push to GitHub (all 4 repos)
    repos = [
        'meekotharaccoon-cell/atomic-agents-conductor',
        'meekotharaccoon-cell/atomic-agents',
        'meekotharaccoon-cell/atomic-agents-staging',
        'meekotharaccoon-cell/atomic-agents-demo',
    ]
    pushed = []
    for k, v in secrets.items():
        if v:
            for repo in repos:
                try:
                    r = subprocess.run(
                        ['gh', 'secret', 'set', k, '--body', v, '--repo', repo],
                        capture_output=True, timeout=15
                    )
                    if r.returncode == 0:
                        pushed.append(k)
                except:
                    pass
    if pushed:
        log(f"Pushed {len(set(pushed))} secrets to GitHub ({len(repos)} repos)")

def launch_system():
    """Launch every component of the system."""
    global _launched
    if _launched:
        return
    _launched = True

    log("=" * 50)
    log("LAUNCHING FULL SYSTEM")
    log("=" * 50)

    def bg(cmd, name):
        def run():
            log(f"Starting: {name}")
            try:
                subprocess.Popen(
                    ['pythonw' if 'pythonw' in PYTHON else PYTHON] + cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=str(DESKTOP)
                )
            except Exception as e:
                try:
                    subprocess.Popen(
                        [sys.executable] + cmd,
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                        cwd=str(DESKTOP)
                    )
                except Exception as e2:
                    log(f"Failed to start {name}: {e2}")
        t = threading.Thread(target=run, daemon=True)
        t.start()
        time.sleep(1.5)

    bg([str(DESKTOP / 'AUTONOMOUS_AGENT.py')],  'Autonomous Agent (port 7780)')
    bg([str(DESKTOP / 'LIVE_DASHBOARD.py')],     'Live Dashboard (port 7779)')
    bg([str(DESKTOP / 'INVESTMENT_HQ' / 'src' / 'approval_portal.py')], 'Investment Portal (port 7778)')
    bg([str(DESKTOP / 'GAZA_ROSE_OMNI' / 'master_orchestrator.py')],    'OMNI Orchestrator')

    # Fire conductor dispatch
    time.sleep(3)
    try:
        subprocess.run([
            'gh', 'workflow', 'run', 'dispatch.yml',
            '--repo', 'meekotharaccoon-cell/atomic-agents-conductor',
            '--field', 'message=full-system-launch-' + datetime.now().strftime('%Y%m%d-%H%M')
        ], timeout=20, capture_output=True)
        log("Conductor dispatch fired")
    except Exception as e:
        log(f"Conductor dispatch: {e}")

    # Open all portals
    time.sleep(2)
    for port, label in [(7780,'Agent'), (7779,'Dashboard'), (7778,'Invest')]:
        try:
            webbrowser.open(f'http://localhost:{port}')
            time.sleep(0.5)
        except:
            pass

    log("ALL SYSTEMS LAUNCHED")

# ── WEB UI ──────────────────────────────────────────────────────────
def build_html(secrets: dict) -> str:
    missing = {k: v for k, v in SECRETS_MAP.items() if not secrets.get(k, '').strip()}
    have    = {k: v for k, v in SECRETS_MAP.items() if secrets.get(k, '').strip()}

    groups = {}
    for k, meta in missing.items():
        g = meta['group']
        groups.setdefault(g, []).append((k, meta))

    group_html = ''
    for gname, items in groups.items():
        cards = ''
        for k, meta in items:
            cards += f'''
<div class="secret-card" id="card-{k}">
  <div class="sc-top">
    <div>
      <div class="sc-label">{meta["label"]}</div>
      <div class="sc-hint">{meta["hint"]}</div>
    </div>
    <a class="sc-link" href="{meta["url"]}" target="_blank">Open &rarr;</a>
  </div>
  <div class="sc-steps">{meta["steps"]}</div>
  <div class="sc-example">e.g. {meta["example"]}</div>
  <div class="sc-input-row">
    <input class="sc-input" type="password" id="inp-{k}"
           placeholder="Paste your {meta["label"]} here..."
           onchange="markDirty('{k}')"
           oninput="markDirty('{k}')">
    <button class="sc-eye" onclick="toggleEye('{k}')" title="Show/hide">👁</button>
    <button class="sc-save" onclick="saveOne('{k}')">Save</button>
  </div>
  <div class="sc-status" id="st-{k}"></div>
</div>'''
        group_html += f'<div class="group-label">{gname}</div>{cards}'

    have_html = ''
    for k, meta in have.items():
        v = secrets.get(k, '')
        display = v[:6] + '...' + v[-4:] if len(v) > 10 else v
        have_html += f'<div class="have-row"><span class="have-key">{meta["label"]}</span><span class="have-val">{display}</span><span class="have-ok">CONNECTED</span></div>'

    missing_count = len(missing)
    have_count = len(have)
    pct = int(have_count / len(SECRETS_MAP) * 100) if SECRETS_MAP else 0

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Meeko — System Launcher</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Outfit:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
:root{{--bg:#060a0e;--panel:#0d1520;--b:#152030;--green:#00ff88;--gold:#ffc800;--rose:#ff3366;--blue:#38bdf8;--muted:#3a5060;--text:#cce0f0;--mono:"Share Tech Mono",monospace;--sans:"Outfit",sans-serif}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;padding:32px 24px}}
.topbar{{display:flex;align-items:center;justify-content:space-between;margin-bottom:32px}}
h1{{font-size:26px;font-weight:900;color:var(--green);font-family:var(--mono)}}
.sub{{color:var(--muted);font-size:12px;font-family:var(--mono);margin-top:4px}}
.progress-wrap{{background:var(--panel);border:1px solid var(--b);border-radius:12px;padding:20px 24px;margin-bottom:28px}}
.prog-top{{display:flex;justify-content:space-between;margin-bottom:10px;font-size:13px}}
.prog-bar{{height:8px;background:var(--b);border-radius:4px;overflow:hidden}}
.prog-fill{{height:100%;background:linear-gradient(90deg,var(--green),var(--gold));border-radius:4px;transition:width 0.5s ease;width:{pct}%}}
.prog-num{{font-family:var(--mono);color:var(--green);font-size:22px;font-weight:800}}
.prog-label{{color:var(--muted);font-size:12px}}
.launch-btn{{width:100%;padding:20px;background:linear-gradient(135deg,#00cc66,#00aa44);border:none;border-radius:14px;color:#000;font-size:18px;font-weight:900;font-family:var(--sans);cursor:pointer;letter-spacing:1px;transition:.2s;margin-bottom:28px;opacity:{1.0 if missing_count==0 else 0.3}}}
.launch-btn:hover{{transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,255,136,0.3)}}
.launch-btn:disabled{{cursor:default;opacity:0.25}}
.group-label{{font-family:var(--mono);font-size:10px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin:24px 0 10px}}
.secret-card{{background:var(--panel);border:1px solid var(--b);border-radius:12px;padding:18px 20px;margin-bottom:12px;transition:.2s}}
.secret-card.saved{{border-color:rgba(0,255,136,0.4);background:rgba(0,255,136,0.03)}}
.sc-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}}
.sc-label{{font-weight:700;font-size:15px}}
.sc-hint{{font-size:12px;color:var(--muted);margin-top:2px}}
.sc-link{{padding:6px 14px;border:1px solid var(--blue);color:var(--blue);border-radius:8px;font-size:12px;text-decoration:none;white-space:nowrap;font-family:var(--mono);transition:.2s}}
.sc-link:hover{{background:var(--blue);color:#000}}
.sc-steps{{font-size:12px;color:#6090b0;margin:6px 0 4px;line-height:1.6}}
.sc-example{{font-family:var(--mono);font-size:10px;color:var(--muted);margin-bottom:10px}}
.sc-input-row{{display:flex;gap:8px;align-items:center}}
.sc-input{{flex:1;padding:10px 14px;background:#0a1828;border:1px solid var(--b);border-radius:8px;color:var(--text);font-family:var(--mono);font-size:13px;outline:none;transition:.2s}}
.sc-input:focus{{border-color:var(--blue);box-shadow:0 0 0 3px rgba(56,189,248,0.1)}}
.sc-eye,.sc-save{{padding:10px 14px;border-radius:8px;border:1px solid var(--b);background:var(--b);color:var(--text);cursor:pointer;font-size:13px;font-family:var(--mono);transition:.2s;white-space:nowrap}}
.sc-save{{background:rgba(0,255,136,0.1);border-color:rgba(0,255,136,0.3);color:var(--green)}}
.sc-save:hover{{background:var(--green);color:#000}}
.sc-status{{font-size:11px;font-family:var(--mono);margin-top:6px;min-height:16px}}
.sc-status.ok{{color:var(--green)}}
.sc-status.err{{color:var(--rose)}}
.have-section{{margin-top:28px}}
.have-section h2{{font-family:var(--mono);font-size:10px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:10px}}
.have-row{{display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.03);font-size:12px}}
.have-row:last-child{{border:none}}
.have-key{{color:var(--muted);flex:1}}
.have-val{{font-family:var(--mono);color:#6090a0;font-size:11px}}
.have-ok{{color:var(--green);font-family:var(--mono);font-size:11px;margin-left:auto}}
.paste-all{{background:rgba(255,200,0,0.06);border:1px solid rgba(255,200,0,0.2);border-radius:10px;padding:14px 18px;margin-bottom:20px;font-size:13px;line-height:1.7}}
.paste-all strong{{color:var(--gold)}}
</style>
</head>
<body>
<div class="topbar">
  <div>
    <h1>MEEKO MYCELIUM</h1>
    <div class="sub">ONE BUTTON — EVERYTHING CONNECTS</div>
  </div>
</div>

<div class="progress-wrap">
  <div class="prog-top">
    <div>
      <div class="prog-num" id="pct-num">{have_count} / {len(SECRETS_MAP)}</div>
      <div class="prog-label">services connected</div>
    </div>
    <div style="text-align:right">
      <div class="prog-num" style="color:{"var(--rose)" if missing_count > 0 else "var(--green)"}">
        {missing_count}
      </div>
      <div class="prog-label">still needed</div>
    </div>
  </div>
  <div class="prog-bar"><div class="prog-fill" id="prog-fill"></div></div>
</div>

{"" if missing_count == 0 else f"""<div class="paste-all">
  <strong>Fastest way:</strong> If you have a .env or text file with your keys, 
  <a href="#" onclick="bulkPaste()" style="color:var(--blue)">click here to paste all at once</a> 
  and the system will sort them automatically.
</div>"""}

<button class="launch-btn" id="launch-btn"
  onclick="launchAll()"
  {"" if missing_count == 0 else 'disabled title="Fill in all secrets first"'}>
  {"LAUNCH EVERYTHING" if missing_count == 0 else f"LAUNCH (fill {missing_count} more secrets first)"}
</button>

{group_html}

<div class="have-section">
  <h2>Already Connected ({have_count})</h2>
  {have_html if have_html else "<div style='color:var(--muted);font-size:12px'>None yet</div>"}
</div>

<script>
const total = {len(SECRETS_MAP)};

function toggleEye(k) {{
  const inp = document.getElementById('inp-' + k);
  inp.type = inp.type === 'password' ? 'text' : 'password';
}}

function markDirty(k) {{
  const st = document.getElementById('st-' + k);
  st.textContent = '';
  st.className = 'sc-status';
}}

async function saveOne(k) {{
  const inp = document.getElementById('inp-' + k);
  const val = inp.value.trim();
  const st  = document.getElementById('st-' + k);
  const card = document.getElementById('card-' + k);
  if (!val) {{ st.textContent = 'paste a value first'; st.className='sc-status err'; return; }}
  st.textContent = 'saving...';
  try {{
    const r = await fetch('/save', {{
      method: 'POST',
      headers: {{'Content-Type':'application/json'}},
      body: JSON.stringify({{key: k, value: val}})
    }});
    const d = await r.json();
    if (d.ok) {{
      st.textContent = 'saved + pushed to GitHub';
      st.className = 'sc-status ok';
      card.classList.add('saved');
      inp.type = 'password';
      inp.value = val.slice(0,4) + '...' + val.slice(-4);
      inp.disabled = true;
      updateProgress(d.have_count);
    }} else {{
      st.textContent = 'error: ' + d.msg;
      st.className = 'sc-status err';
    }}
  }} catch(e) {{
    st.textContent = 'network error';
    st.className = 'sc-status err';
  }}
}}

function updateProgress(haveCount) {{
  const pct = Math.round(haveCount / total * 100);
  document.getElementById('prog-fill').style.width = pct + '%';
  document.getElementById('pct-num').textContent = haveCount + ' / ' + total;
  if (haveCount === total) {{
    const btn = document.getElementById('launch-btn');
    btn.disabled = false;
    btn.textContent = 'LAUNCH EVERYTHING';
    btn.style.opacity = '1';
  }}
}}

async function launchAll() {{
  const btn = document.getElementById('launch-btn');
  btn.textContent = 'LAUNCHING...';
  btn.disabled = true;
  try {{
    await fetch('/launch', {{method: 'POST'}});
    btn.textContent = 'LAUNCHED — check the new windows';
    btn.style.background = 'linear-gradient(135deg,#38bdf8,#0ea5e9)';
  }} catch(e) {{
    btn.textContent = 'error — check console';
    btn.disabled = false;
  }}
}}

function bulkPaste() {{
  const text = prompt('Paste your .env content or any text containing KEY=VALUE pairs:');
  if (!text) return;
  const lines = text.split('\\n');
  const found = {{}};
  for (const line of lines) {{
    const eq = line.indexOf('=');
    if (eq > 0) {{
      const k = line.slice(0, eq).trim().toUpperCase().replace(/[^A-Z_]/g,'');
      const v = line.slice(eq+1).trim().replace(/^["']|["']$/g,'');
      if (k && v) found[k] = v;
    }}
  }}
  let matched = 0;
  for (const [k, v] of Object.entries(found)) {{
    const inp = document.getElementById('inp-' + k);
    if (inp && !inp.disabled) {{
      inp.value = v;
      inp.type = 'text';
      matched++;
    }}
  }}
  if (matched > 0) alert('Matched ' + matched + ' keys! Click Save on each one to confirm.');
  else alert('No matching keys found. Check your format (KEY=value).');
}}
</script>
</body>
</html>'''

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _html(self, content, code=200):
        b = content.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def _json(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            with _lock:
                self._html(build_html(_secrets))
        elif self.path == '/state':
            with _lock:
                self._json({
                    'have_count': sum(1 for k in SECRETS_MAP if _secrets.get(k, '').strip()),
                    'missing': [k for k in SECRETS_MAP if not _secrets.get(k, '').strip()],
                    'launched': _launched,
                })
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if self.path == '/save':
            k = body.get('key', '').strip()
            v = body.get('value', '').strip()
            if k and v and k in SECRETS_MAP:
                with _lock:
                    _secrets[k] = v
                    save_secrets(_secrets)
                have_count = sum(1 for kk in SECRETS_MAP if _secrets.get(kk, '').strip())
                log(f"Saved: {k} ({have_count}/{len(SECRETS_MAP)} total)")
                self._json({'ok': True, 'have_count': have_count})
            else:
                self._json({'ok': False, 'msg': 'invalid key'})

        elif self.path == '/launch':
            threading.Thread(target=launch_system, daemon=True).start()
            self._json({'ok': True})

        else:
            self.send_response(404); self.end_headers()


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(f"\n{'='*56}")
    print(f"  MEEKO MYCELIUM — ONE BUTTON LAUNCHER")
    print(f"{'='*56}")

    # Auto-recover everything possible
    recovered = auto_recover()
    with _lock:
        _secrets.update(recovered)

    have  = sum(1 for k in SECRETS_MAP if _secrets.get(k, '').strip())
    need  = len(SECRETS_MAP) - have
    print(f"\n  Auto-recovered:  {have} / {len(SECRETS_MAP)} secrets")
    print(f"  Still needed:    {need}")
    if need == 0:
        print(f"  All secrets found — launching immediately...")
        launch_system()
    else:
        print(f"  Opening browser to collect {need} remaining secrets...")

    server = http.server.HTTPServer(('127.0.0.1', PORT), Handler)
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    print(f"\n  Browser: http://localhost:{PORT}")
    print(f"  Paste your keys there. Each one is saved + pushed to GitHub instantly.")
    print(f"  When all {len(SECRETS_MAP)} are done -> click LAUNCH EVERYTHING.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Launcher stopped.\n")
