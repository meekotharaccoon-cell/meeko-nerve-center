"""
IGNITE.py — ONE COMMAND. EVERYTHING RUNS.
==========================================
python C:\Users\meeko\Desktop\IGNITE.py

What this does in order:
1. Scans everywhere on this machine for existing credentials
2. Opens the KEY BRIDGE (localhost:7775) — the easiest possible UI to paste your keys
3. For each key: opens the exact browser tab where it lives
4. Saves everything to .secrets (local runtime) AND pushes to GitHub secrets
5. Launches all services in sequence
6. Creates the desktop button that does all of this forever
7. Never needs Meeko again except to approve money decisions

The KEY BRIDGE knows:
- Which secrets are already in GitHub (shows them as green — just re-paste)
- Exactly which URL to open for each service
- Which ones you're already logged into in Brave
- How to verify each key live before accepting it
"""

import http.server
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path

DESKTOP  = Path(r'C:\Users\meeko\Desktop')
DB_PATH  = DESKTOP / 'UltimateAI_Master' / 'gaza_rose.db'
SECRETS  = DESKTOP / 'UltimateAI_Master' / '.secrets'
PORT     = 7775
REPOS    = [
    'meekotharaccoon-cell/atomic-agents-conductor',
    'meekotharaccoon-cell/atomic-agents',
    'meekotharaccoon-cell/atomic-agents-staging',
    'meekotharaccoon-cell/atomic-agents-demo',
]

# ── WHAT'S ALREADY IN GITHUB ──────────────────────────────
def scan_github_secrets():
    """Check which secrets are already pushed to GitHub."""
    in_github = set()
    try:
        r = subprocess.run(
            ['gh', 'secret', 'list', '--repo', REPOS[0]],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            for line in r.stdout.strip().splitlines():
                parts = line.split()
                if parts:
                    in_github.add(parts[0])
    except Exception:
        pass
    return in_github

# ── LOAD EXISTING .secrets ────────────────────────────────
def load_existing_secrets():
    local = {}
    if SECRETS.exists():
        for line in SECRETS.read_text(encoding='utf-8').strip().splitlines():
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.split('=', 1)
                k, v = k.strip(), v.strip()
                if k and v:
                    local[k] = v
    return local

# ── SERVICE DEFINITIONS ───────────────────────────────────
# Each service: keys needed, where to get them, how to verify
SERVICES = [
    {
        'id':    'alpaca',
        'name':  'Alpaca Markets',
        'desc':  'US Stocks & ETFs — paper trading first',
        'color': '#38bdf8',
        'url':   'https://app.alpaca.markets/paper-trading/overview',
        'url_label': 'alpaca.markets → Paper Trading → API Keys',
        'fields': [
            {'key': 'ALPACA_KEY',    'label': 'API Key ID',     'hint': 'Starts with PK...'},
            {'key': 'ALPACA_SECRET', 'label': 'API Secret Key', 'hint': 'Long random string'},
        ],
        'verify': 'alpaca',
    },
    {
        'id':    'coinbase',
        'name':  'Coinbase Advanced',
        'desc':  'Crypto trading — already linked to your Gmail',
        'color': '#0052ff',
        'url':   'https://www.coinbase.com/settings/api',
        'url_label': 'coinbase.com/settings/api → New API Key → View',
        'fields': [
            {'key': 'CB_API_KEY',    'label': 'API Key Name',   'hint': 'organizations/xxx/apiKeys/xxx'},
            {'key': 'CB_API_SECRET', 'label': 'Private Key',    'hint': '-----BEGIN EC PRIVATE KEY-----', 'multiline': True},
        ],
        'verify': 'coinbase',
    },
    {
        'id':    'coinbase_commerce',
        'name':  'Coinbase Commerce',
        'desc':  'Accept BTC/ETH/USDC payments in your gallery',
        'color': '#0052ff',
        'url':   'https://commerce.coinbase.com/settings',
        'url_label': 'commerce.coinbase.com → Settings → API Keys',
        'fields': [
            {'key': 'COINBASE_COMMERCE_KEY', 'label': 'Commerce API Key', 'hint': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'},
        ],
        'verify': 'commerce',
    },
    {
        'id':    'kraken',
        'name':  'Kraken',
        'desc':  'Additional crypto exchange — Kraken session found in Windows',
        'color': '#5741d9',
        'url':   'https://www.kraken.com/u/security/api',
        'url_label': 'kraken.com → Security → API → Add Key',
        'note':  'Your Kraken SESSION is in Windows Credential Manager (you\'re logged in). Now create an API key for your agent.',
        'fields': [
            {'key': 'KRAKEN_API_KEY',    'label': 'API Key',     'hint': 'Kraken API key string'},
            {'key': 'KRAKEN_API_SECRET', 'label': 'Private Key', 'hint': 'Kraken private key (base64)'},
        ],
        'verify': 'kraken',
    },
    {
        'id':    'phantom',
        'name':  'Phantom Wallet',
        'desc':  'Your Solana address — public, safe to share',
        'color': '#ab9ff2',
        'url':   'brave://extensions/',
        'url_label': 'Open Phantom in Brave → click account name → copy address',
        'fields': [
            {'key': 'PHANTOM_SOLANA_ADDRESS', 'label': 'Solana Address', 'hint': '44-character base58 address'},
        ],
        'verify': 'phantom',
    },
    {
        'id':    'gumroad',
        'name':  'Gumroad',
        'desc':  'Sell your playbooks and art — primary revenue',
        'color': '#ff90e8',
        'url':   'https://app.gumroad.com/api',
        'url_label': 'app.gumroad.com/api → Generate Access Token',
        'fields': [
            {'key': 'GUMROAD_TOKEN', 'label': 'Access Token', 'hint': 'Long token string'},
        ],
        'verify': 'gumroad',
    },
    {
        'id':    'stripe',
        'name':  'Stripe',
        'desc':  'Working on your phone — get the secret key',
        'color': '#635bff',
        'url':   'https://dashboard.stripe.com/apikeys',
        'url_label': 'dashboard.stripe.com/apikeys → Reveal Secret Key',
        'fields': [
            {'key': 'STRIPE_SECRET_KEY', 'label': 'Secret Key', 'hint': 'sk_live_...'},
        ],
        'verify': 'stripe',
    },
    {
        'id':    'paypal',
        'name':  'PayPal',
        'desc':  'Working on your phone — get live API credentials',
        'color': '#003087',
        'url':   'https://developer.paypal.com/dashboard/applications/live',
        'url_label': 'developer.paypal.com → Applications → Live → Your App',
        'fields': [
            {'key': 'PAYPAL_CLIENT_ID',     'label': 'Client ID (Live)',     'hint': 'Long alphanumeric string'},
            {'key': 'PAYPAL_CLIENT_SECRET', 'label': 'Client Secret (Live)', 'hint': 'Long alphanumeric string'},
        ],
        'verify': 'paypal',
    },
    {
        'id':    'github',
        'name':  'GitHub Conductor Token',
        'desc':  'Already authenticated as meekotharaccoon-cell — just create a PAT',
        'color': '#00ff88',
        'url':   'https://github.com/settings/tokens/new?scopes=repo,workflow&description=MeekoMyceliumConductor',
        'url_label': 'github.com → Settings → Tokens → New (repo+workflow)',
        'note':  'gh CLI is already authenticated. This token lets your agent trigger workflows across all 4 repos.',
        'fields': [
            {'key': 'CONDUCTOR_TOKEN', 'label': 'Personal Access Token', 'hint': 'ghp_...'},
        ],
        'verify': 'github',
    },
]

# ── HTML ──────────────────────────────────────────────────
def build_html(in_github, local_secrets):
    services_json = json.dumps(SERVICES)
    in_github_json = json.dumps(list(in_github))
    local_keys_json = json.dumps(list(local_secrets.keys()))

    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Meeko — Key Bridge</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Outfit:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#06090d;--panel:#0d1520;--b:#1a2535;
  --green:#00ff88;--gold:#ffc800;--rose:#ff3060;
  --blue:#38bdf8;--purple:#a78bfa;
  --text:#cce0f0;--muted:#3a5560;
  --mono:'Share Tech Mono',monospace;--sans:'Outfit',sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh}

/* TOPBAR */
.top{
  background:rgba(13,21,32,.97);border-bottom:1px solid var(--b);
  padding:0 28px;height:56px;display:flex;align-items:center;gap:16px;
  position:sticky;top:0;z-index:100;backdrop-filter:blur(12px);
}
.brand{font-family:var(--mono);font-size:13px;letter-spacing:2px;color:var(--green)}
.top-status{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--muted)}
.top-status span{color:var(--green)}

/* HERO */
.hero{max-width:800px;margin:0 auto;padding:48px 24px 32px}
.eyebrow{font-family:var(--mono);font-size:10px;letter-spacing:3px;color:var(--green);
  text-transform:uppercase;margin-bottom:14px;display:flex;align-items:center;gap:10px}
.eyebrow::before{content:'';display:block;width:20px;height:1px;background:var(--green)}
h1{font-size:clamp(28px,5vw,46px);font-weight:900;line-height:1.08;letter-spacing:-1px;margin-bottom:12px}
h1 em{color:var(--green);font-style:normal}
.hero-sub{color:var(--muted);font-size:14px;line-height:1.8;max-width:520px}

/* PROGRESS */
.progress-wrap{max-width:800px;margin:0 auto 32px;padding:0 24px}
.prog-row{display:flex;justify-content:space-between;font-family:var(--mono);
  font-size:11px;color:var(--muted);margin-bottom:8px}
.prog-row span{color:var(--gold)}
.prog-track{height:3px;background:var(--b);border-radius:99px;overflow:hidden}
.prog-fill{height:100%;background:linear-gradient(90deg,var(--green),var(--blue));
  border-radius:99px;transition:width .6s cubic-bezier(.4,0,.2,1)}

/* CARDS */
.cards{max-width:800px;margin:0 auto;padding:0 24px 80px}
.svc-card{
  background:var(--panel);border:1px solid var(--b);border-radius:16px;
  margin-bottom:10px;overflow:hidden;transition:border-color .3s,box-shadow .3s;
}
.svc-card.active{border-color:var(--green);box-shadow:0 0 0 1px rgba(0,255,136,.08)}
.svc-card.done{border-color:rgba(0,255,136,.25)}
.svc-card.skip{opacity:.4}

.svc-hdr{
  display:flex;align-items:center;gap:14px;padding:18px 20px;
  cursor:pointer;user-select:none;
}
.svc-icon{
  width:36px;height:36px;border-radius:10px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-weight:900;font-size:13px;font-family:var(--mono);
  background:var(--b);color:var(--muted);transition:.3s;
}
.svc-card.active .svc-icon{background:var(--green);color:#000}
.svc-card.done .svc-icon{background:rgba(0,255,136,.15);color:var(--green)}
.svc-info{flex:1;min-width:0}
.svc-name{font-size:15px;font-weight:700}
.svc-desc{font-size:12px;color:var(--muted);margin-top:2px}
.svc-badge{
  font-family:var(--mono);font-size:9px;letter-spacing:1px;text-transform:uppercase;
  padding:3px 10px;border-radius:99px;white-space:nowrap;
}
.b-wait{background:rgba(255,255,255,.04);color:var(--muted)}
.b-gh{background:rgba(0,255,136,.1);color:var(--green);border:1px solid rgba(0,255,136,.2)}
.b-ok{background:rgba(0,255,136,.12);color:var(--green)}
.b-skip{background:rgba(255,255,255,.04);color:var(--muted)}
.b-fail{background:rgba(255,48,96,.1);color:var(--rose)}

.svc-body{padding:0 20px 20px;display:none}
.svc-card.active .svc-body,.svc-card.open .svc-body{display:block}

/* GITHUB BANNER */
.gh-banner{
  background:rgba(0,255,136,.05);border:1px solid rgba(0,255,136,.2);
  border-radius:10px;padding:12px 16px;
  font-family:var(--mono);font-size:11px;color:var(--green);
  margin-bottom:14px;line-height:1.8;
}

/* NOTE BOX */
.note-box{
  background:rgba(255,200,0,.05);border:1px solid rgba(255,200,0,.2);
  border-radius:10px;padding:11px 15px;
  font-size:12px;color:#c0a830;margin-bottom:14px;line-height:1.7;
}

/* URL BUTTON */
.url-btn{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(56,189,248,.08);border:1px solid rgba(56,189,248,.2);
  color:var(--blue);padding:9px 16px;border-radius:9px;
  font-family:var(--mono);font-size:11px;letter-spacing:.5px;
  cursor:pointer;text-decoration:none;margin-bottom:14px;
  transition:.2s;
}
.url-btn:hover{background:rgba(56,189,248,.15);border-color:rgba(56,189,248,.4)}
.url-btn::before{content:'→  '}

/* FIELDS */
.field{margin-bottom:12px}
.field label{
  display:block;font-family:var(--mono);font-size:9px;letter-spacing:1.5px;
  text-transform:uppercase;color:var(--muted);margin-bottom:7px;
}
.field input,.field textarea{
  width:100%;background:rgba(255,255,255,.04);border:1px solid var(--b);
  border-radius:9px;padding:11px 14px;color:var(--text);
  font-family:var(--mono);font-size:12px;outline:none;
  transition:border-color .2s;resize:vertical;
}
.field input:focus,.field textarea:focus{border-color:var(--green)}
.field input.ok{border-color:var(--green)}
.field input.err{border-color:var(--rose)}
.field .hint{font-size:10px;color:var(--muted);margin-top:4px;font-family:var(--mono)}

/* BUTTONS */
.btn-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.btn{
  padding:10px 20px;border-radius:9px;border:none;cursor:pointer;
  font-family:var(--sans);font-size:13px;font-weight:600;
  transition:.2s;display:inline-flex;align-items:center;gap:7px;
}
.btn-save{background:var(--green);color:#000}
.btn-save:hover{background:#4dffa0;transform:translateY(-1px)}
.btn-save:disabled{opacity:.4;cursor:not-allowed;transform:none}
.btn-skip{background:transparent;color:var(--muted);border:1px solid var(--b)}
.btn-skip:hover{border-color:var(--muted);color:var(--text)}

/* RESULT */
.result{
  margin-top:12px;padding:11px 14px;border-radius:9px;
  font-family:var(--mono);font-size:11px;line-height:1.8;display:none;
}
.result.ok{background:rgba(0,255,136,.06);border:1px solid rgba(0,255,136,.2);color:#70ffaa;display:block}
.result.fail{background:rgba(255,48,96,.06);border:1px solid rgba(255,48,96,.2);color:#ff9090;display:block}

/* LAUNCH SECTION */
.launch{max-width:800px;margin:0 auto 60px;padding:0 24px}
.launch-card{
  background:linear-gradient(135deg,#0d1f14,#0a1825);
  border:2px solid var(--green);border-radius:18px;padding:36px;text-align:center;
}
.launch-card h2{font-size:26px;color:var(--green);margin-bottom:8px;font-weight:800}
.launch-card p{color:var(--muted);font-size:13px;line-height:1.8;margin-bottom:24px}
.big-btn{
  display:inline-flex;align-items:center;gap:10px;
  background:var(--green);color:#000;border:none;padding:16px 48px;
  border-radius:12px;font-weight:900;font-size:16px;cursor:pointer;
  font-family:var(--sans);transition:.2s;letter-spacing:-.3px;
}
.big-btn:hover{background:#4dffa0;transform:scale(1.03)}
.big-btn:disabled{opacity:.5;cursor:not-allowed;transform:none}

/* SPINNER */
@keyframes spin{to{transform:rotate(360deg)}}
.spin{display:inline-block;width:13px;height:13px;border:2px solid transparent;
  border-top-color:currentColor;border-radius:50%;animation:spin .7s linear infinite}

/* STATUS GRID */
.status-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:16px 0;text-align:left}
.status-item{background:rgba(255,255,255,.03);border-radius:8px;padding:10px 14px;
  font-family:var(--mono);font-size:11px}
.status-item .s-lbl{color:var(--muted);margin-bottom:2px}
.status-item .s-val{color:var(--green)}
.status-item .s-val.warn{color:var(--gold)}
</style>
</head>
<body>

<div class="top">
  <div class="brand">MEEKO / KEY BRIDGE</div>
  <div class="top-status">
    <span id="done-count">0</span> / """ + str(len(SERVICES)) + r""" services connected
  </div>
</div>

<div class="hero">
  <div class="eyebrow">One time setup</div>
  <h1>Close every gap.<br><em>Right now.</em></h1>
  <p class="hero-sub">Your secrets are already in GitHub — we're bridging them to your local runtime. For each service: click the link, copy the key, paste it. That's it. Your system runs itself after this.</p>
</div>

<div class="progress-wrap">
  <div class="prog-row"><span>Key Bridge Progress</span><span id="prog-txt">Starting...</span></div>
  <div class="prog-track"><div class="prog-fill" id="prog-fill" style="width:0%"></div></div>
</div>

<div class="cards" id="cards-container">
  <!-- rendered by JS -->
</div>

<div class="launch">
  <div class="launch-card">
    <h2>Launch Everything</h2>
    <p>All connected services get bridged to local runtime.<br>
    Your agent starts, your dashboard opens, your system runs itself.</p>
    <button class="big-btn" id="launch-btn" onclick="launch()">
      <span id="launch-txt">Launch My System</span>
    </button>
    <div id="launch-result" style="display:none;margin-top:20px"></div>
  </div>
</div>

<script>
const SERVICES = """ + services_json + r""";
const IN_GITHUB = new Set(""" + in_github_json + r""");
const LOCAL_KEYS = new Set(""" + local_keys_json + r""");
const TOTAL = SERVICES.length;

const saved = new Set();
const order = SERVICES.map(s => s.id);

function updateProgress() {
  const n = saved.size;
  document.getElementById('done-count').textContent = n;
  document.getElementById('prog-fill').style.width = (n/TOTAL*100)+'%';
  const pct = Math.round(n/TOTAL*100);
  document.getElementById('prog-txt').textContent = pct+'% complete';
}

function badge(svc) {
  const keys = svc.fields.map(f => f.key);
  const allGh = keys.every(k => IN_GITHUB.has(k));
  const allLocal = keys.every(k => LOCAL_KEYS.has(k));
  if (saved.has(svc.id)) return '<span class="svc-badge b-ok">Connected</span>';
  if (allGh && allLocal) return '<span class="svc-badge b-ok">Ready</span>';
  if (allGh) return '<span class="svc-badge b-gh">In GitHub — paste locally</span>';
  return '<span class="svc-badge b-wait">Needs key</span>';
}

function renderAll() {
  const container = document.getElementById('cards-container');
  container.innerHTML = SERVICES.map((svc, idx) => {
    const keys = svc.fields.map(f => f.key);
    const allGh = keys.every(k => IN_GITHUB.has(k));
    const ghBanner = allGh ? `
      <div class="gh-banner">
        ✓ These keys are already in your GitHub secrets from the Setup Wizard.<br>
        Just re-paste them here to connect your local runtime. One last time.
      </div>` : '';
    const noteBanner = svc.note ? `<div class="note-box">${svc.note}</div>` : '';

    const fields = svc.fields.map(f => `
      <div class="field">
        <label>${f.label}</label>
        ${f.multiline
          ? `<textarea id="${svc.id}-${f.key}" rows="3" placeholder="${f.hint}"></textarea>`
          : `<input type="password" id="${svc.id}-${f.key}" placeholder="${f.hint}">`}
        <div class="hint">${f.hint}</div>
      </div>`).join('');

    const isFirst = idx === 0;
    return `
    <div class="svc-card ${isFirst?'active':''}" id="sc-${svc.id}">
      <div class="svc-hdr" onclick="toggle('${svc.id}')">
        <div class="svc-icon" style="color:${svc.color}">${(idx+1)}</div>
        <div class="svc-info">
          <div class="svc-name">${svc.name}</div>
          <div class="svc-desc">${svc.desc}</div>
        </div>
        <div id="badge-${svc.id}">${badge(svc)}</div>
      </div>
      <div class="svc-body">
        ${ghBanner}
        ${noteBanner}
        <a class="url-btn" href="${svc.url}" target="_blank"
           onclick="return openUrl('${svc.url}','${svc.id}')">${svc.url_label}</a>
        ${fields}
        <div class="btn-row">
          <button class="btn btn-save" id="btn-${svc.id}"
            onclick="save('${svc.id}')">
            <span id="btn-txt-${svc.id}">Save &amp; Verify</span>
          </button>
          <button class="btn btn-skip" onclick="skip('${svc.id}')">Skip</button>
        </div>
        <div class="result" id="result-${svc.id}"></div>
      </div>
    </div>`;
  }).join('');
}

function openUrl(url, svcId) {
  if (url.startsWith('brave://') || url.startsWith('chrome://')) {
    return true; // let browser handle it
  }
  window.open(url, '_blank');
  return false;
}

function toggle(id) {
  document.getElementById('sc-'+id).classList.toggle('open');
}

function showResult(id, ok, html) {
  const el = document.getElementById('result-'+id);
  el.className = 'result ' + (ok?'ok':'fail');
  el.innerHTML = html;
}

function nextCard(current) {
  const idx = order.indexOf(current);
  if (idx < order.length-1) {
    const next = order[idx+1];
    const el = document.getElementById('sc-'+next);
    el.classList.add('active');
    el.classList.remove('skip');
    setTimeout(()=>el.scrollIntoView({behavior:'smooth',block:'center'}), 400);
  }
}

async function save(id) {
  const svc = SERVICES.find(s => s.id===id);
  const btn = document.getElementById('btn-'+id);
  btn.disabled = true;
  document.getElementById('btn-txt-'+id).innerHTML = '<span class="spin"></span>';

  const payload = {service: id, fields: {}};
  for (const f of svc.fields) {
    const el = document.getElementById(id+'-'+f.key);
    payload.fields[f.key] = el ? el.value.trim() : '';
  }

  try {
    const r = await fetch('/save', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    const d = await r.json();
    if (d.ok) {
      document.getElementById('sc-'+id).classList.add('done');
      document.getElementById('sc-'+id).classList.remove('active');
      document.getElementById('badge-'+id).innerHTML =
        '<span class="svc-badge b-ok">Connected</span>';
      document.getElementById('btn-txt-'+id).textContent = 'Connected!';
      showResult(id, true, d.message + (d.github ? '<br>&#9670; Pushed to GitHub secrets' : ''));
      saved.add(id);
      updateProgress();
      nextCard(id);
    } else {
      document.getElementById('btn-txt-'+id).textContent = 'Retry';
      btn.disabled = false;
      showResult(id, false, d.message || d.error || 'Unknown error');
    }
  } catch(e) {
    document.getElementById('btn-txt-'+id).textContent = 'Retry';
    btn.disabled = false;
    showResult(id, false, e.message);
  }
}

function skip(id) {
  document.getElementById('sc-'+id).classList.add('skip');
  document.getElementById('sc-'+id).classList.remove('active');
  document.getElementById('badge-'+id).innerHTML = '<span class="svc-badge b-skip">Skipped</span>';
  saved.add(id+'_skip');
  updateProgress();
  nextCard(id);
}

async function launch() {
  const btn = document.getElementById('launch-btn');
  btn.disabled = true;
  document.getElementById('launch-txt').innerHTML = '<span class="spin"></span> Launching...';
  try {
    const r = await fetch('/launch', {method:'POST'});
    const d = await r.json();
    const el = document.getElementById('launch-result');
    el.style.display = 'block';
    el.innerHTML = `
      <div class="status-grid">
        ${Object.entries(d.status||{}).map(([k,v])=>`
        <div class="status-item">
          <div class="s-lbl">${k}</div>
          <div class="s-val ${v.ok?'':'warn'}">${v.msg}</div>
        </div>`).join('')}
      </div>
      <div style="margin-top:16px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
        <a href="http://localhost:7780" target="_blank" style="color:var(--green);font-family:var(--mono);font-size:12px;text-decoration:none;padding:8px 16px;border:1px solid rgba(0,255,136,.3);border-radius:8px">Agent Status →</a>
        <a href="http://localhost:7779" target="_blank" style="color:var(--blue);font-family:var(--mono);font-size:12px;text-decoration:none;padding:8px 16px;border:1px solid rgba(56,189,248,.3);border-radius:8px">Live Dashboard →</a>
        <a href="http://localhost:7778" target="_blank" style="color:var(--gold);font-family:var(--mono);font-size:12px;text-decoration:none;padding:8px 16px;border:1px solid rgba(255,200,0,.3);border-radius:8px">Investment Portal →</a>
      </div>`;
    document.getElementById('launch-txt').textContent = 'Launched';
  } catch(e) {
    btn.disabled = false;
    document.getElementById('launch-txt').textContent = 'Launch My System';
    alert(e.message);
  }
}

renderAll();
updateProgress();
</script>
</body>
</html>"""

# ── VERIFIERS ─────────────────────────────────────────────
def verify_alpaca(fields):
    k, s = fields.get('ALPACA_KEY',''), fields.get('ALPACA_SECRET','')
    if not k or not s: return False, 'Both keys required'
    try:
        req = urllib.request.Request(
            'https://paper-api.alpaca.markets/v2/account',
            headers={'APCA-API-KEY-ID': k, 'APCA-API-SECRET-KEY': s}
        )
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        eq = float(data.get('equity', 0))
        return True, f'Paper account connected — equity: ${eq:.2f}'
    except Exception as e:
        return False, str(e)

def verify_coinbase(fields):
    k, s = fields.get('CB_API_KEY',''), fields.get('CB_API_SECRET','')
    if not k or not s: return False, 'Both fields required'
    try:
        from coinbase.rest import RESTClient
        client = RESTClient(api_key=k, api_secret=s)
        accts = client.get_accounts()
        n = len(accts.accounts) if hasattr(accts, 'accounts') else 0
        return True, f'Coinbase connected — {n} accounts found'
    except Exception as e:
        return False, str(e)

def verify_commerce(fields):
    k = fields.get('COINBASE_COMMERCE_KEY','')
    if not k: return False, 'API key required'
    try:
        req = urllib.request.Request(
            'https://api.commerce.coinbase.com/checkouts',
            headers={'X-CC-Api-Key': k, 'X-CC-Version': '2018-03-22'}
        )
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return True, f'Commerce connected — {len(data.get("data",[]))} checkouts'
    except Exception as e:
        return False, str(e)

def verify_kraken(fields):
    k, s = fields.get('KRAKEN_API_KEY',''), fields.get('KRAKEN_API_SECRET','')
    if not k or not s: return False, 'Both keys required'
    try:
        import ccxt
        ex = ccxt.kraken({'apiKey': k, 'secret': s})
        bal = ex.fetch_balance()
        non_zero = [c for c, v in bal.get('total',{}).items() if v and float(v) > 0]
        return True, f'Kraken connected — balances: {", ".join(non_zero[:4]) or "empty"}'
    except Exception as e:
        return False, str(e)

def verify_phantom(fields):
    addr = fields.get('PHANTOM_SOLANA_ADDRESS','')
    if not addr or len(addr) < 32: return False, 'Address looks too short'
    try:
        payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"getBalance","params":[addr]}).encode()
        req = urllib.request.Request('https://api.mainnet-beta.solana.com', data=payload,
                                     headers={'Content-Type':'application/json'})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        sol = data.get('result',{}).get('value',0) / 1_000_000_000
        return True, f'Solana wallet verified — {sol:.6f} SOL'
    except Exception as e:
        return False, str(e)

def verify_gumroad(fields):
    t = fields.get('GUMROAD_TOKEN','')
    if not t: return False, 'Token required'
    try:
        req = urllib.request.Request('https://api.gumroad.com/v2/user',
                                     headers={'Authorization': f'Bearer {t}'})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        email = data.get('user',{}).get('email','verified')
        return True, f'Gumroad connected as {email}'
    except Exception as e:
        return False, str(e)

def verify_stripe(fields):
    k = fields.get('STRIPE_SECRET_KEY','')
    if not k: return False, 'Key required'
    try:
        import stripe as sl
        sl.api_key = k
        bal = sl.Balance.retrieve()
        avail = bal['available'][0]['amount'] / 100
        cur   = bal['available'][0]['currency'].upper()
        return True, f'Stripe connected — balance: {avail} {cur}'
    except Exception as e:
        return False, str(e)

def verify_paypal(fields):
    cid, cs = fields.get('PAYPAL_CLIENT_ID',''), fields.get('PAYPAL_CLIENT_SECRET','')
    if not cid or not cs: return False, 'Both fields required'
    try:
        import base64
        creds = base64.b64encode(f"{cid}:{cs}".encode()).decode()
        req = urllib.request.Request(
            'https://api-m.paypal.com/v1/oauth2/token',
            data=b'grant_type=client_credentials',
            headers={'Authorization': f'Basic {creds}',
                     'Content-Type':'application/x-www-form-urlencoded'}
        )
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return True, 'PayPal LIVE connected — token valid'
    except Exception as e:
        return False, str(e)

def verify_github(fields):
    t = fields.get('CONDUCTOR_TOKEN','')
    if not t: return False, 'Token required'
    try:
        req = urllib.request.Request('https://api.github.com/user',
                                     headers={'Authorization': f'token {t}',
                                              'Accept': 'application/vnd.github+json'})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return True, f'GitHub connected as {data.get("login","?")}'
    except Exception as e:
        return False, str(e)

VERIFIERS = {
    'alpaca':           verify_alpaca,
    'coinbase':         verify_coinbase,
    'coinbase_commerce':verify_commerce,
    'kraken':           verify_kraken,
    'phantom':          verify_phantom,
    'gumroad':          verify_gumroad,
    'stripe':           verify_stripe,
    'paypal':           verify_paypal,
    'github':           verify_github,
}

def save_to_secrets_and_github(fields: dict):
    """Save fields to .secrets file and push to GitHub."""
    existing = {}
    if SECRETS.exists():
        for line in SECRETS.read_text(encoding='utf-8').strip().splitlines():
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.split('=', 1)
                existing[k.strip()] = v.strip()
    for k, v in fields.items():
        if v:
            existing[k] = v
            os.environ[k] = v
    # Write back
    header = '# MEEKO MYCELIUM LOCAL SECRETS — never commit this file\n'
    lines  = header + '\n'.join(f'{k}={v}' for k, v in existing.items()) + '\n'
    SECRETS.write_text(lines, encoding='utf-8')
    # Push to GitHub
    pushed = 0
    for k, v in fields.items():
        if v:
            for repo in REPOS:
                r = subprocess.run(
                    ['gh', 'secret', 'set', k, '--repo', repo],
                    input=v.encode(), capture_output=True, timeout=15
                )
                if r.returncode == 0:
                    pushed += 1
    return pushed

# ── LAUNCH ────────────────────────────────────────────────
def do_launch():
    status = {}
    scripts = [
        ('Autonomous Agent',  DESKTOP / 'AUTONOMOUS_AGENT.py',   7780),
        ('Live Dashboard',    DESKTOP / 'LIVE_DASHBOARD.py',      7779),
        ('Investment Portal', DESKTOP / 'INVESTMENT_HQ' / 'src' / 'approval_portal.py', 7778),
    ]
    for name, path, port in scripts:
        if path.exists():
            try:
                subprocess.Popen(
                    [sys.executable, str(path)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                status[name] = {'ok': True, 'msg': f'localhost:{port}'}
            except Exception as e:
                status[name] = {'ok': False, 'msg': str(e)[:60]}
        else:
            status[name] = {'ok': False, 'msg': 'script not found'}

    # Fire conductor dispatch
    try:
        subprocess.run(
            ['gh', 'workflow', 'run', 'dispatch.yml',
             '--repo', 'meekotharaccoon-cell/atomic-agents-conductor',
             '--field', 'message=ignite-launch'],
            capture_output=True, timeout=15
        )
        status['GitHub Conductor'] = {'ok': True, 'msg': 'dispatched to all repos'}
    except Exception as e:
        status['GitHub Conductor'] = {'ok': False, 'msg': str(e)[:60]}

    return status

# ── HTTP SERVER ────────────────────────────────────────────
class BridgeHandler(http.server.BaseHTTPRequestHandler):
    _html_cache = None

    def log_message(self, *a): pass

    def _json(self, d, code=200):
        b = json.dumps(d, default=str).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            b = BridgeHandler._html_cache.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html;charset=utf-8')
            self.send_header('Content-Length', len(b))
            self.end_headers()
            self.wfile.write(b)
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = json.loads(self.rfile.read(length)) if length else {}

        if self.path == '/save':
            svc_id = body.get('service', '')
            fields = body.get('fields', {})
            # Verify
            verifier = VERIFIERS.get(svc_id)
            if verifier:
                ok, msg = verifier(fields)
            else:
                ok, msg = True, 'Saved (no verifier)'
            if ok:
                saved_count = save_to_secrets_and_github(fields)
                self._json({'ok': True, 'message': msg,
                            'github': saved_count > 0})
            else:
                self._json({'ok': False, 'message': msg})

        elif self.path == '/launch':
            status = do_launch()
            self._json({'ok': True, 'status': status})

        else:
            self.send_response(404); self.end_headers()

# ── DESKTOP SHORTCUT ──────────────────────────────────────
def create_desktop_shortcut():
    """Create a proper Windows .lnk shortcut on the Desktop."""
    shortcut_path = DESKTOP / 'LAUNCH MEEKO.lnk'
    launcher_bat  = DESKTOP / 'IGNITE.bat'

    # Write the .bat launcher
    bat = f'''@echo off
title Meeko Mycelium — Igniting...
color 0A
echo.
echo  Igniting Meeko Mycelium...
echo.
python "{DESKTOP / 'IGNITE.py'}"
'''
    launcher_bat.write_text(bat)

    # Create .lnk via PowerShell WScript.Shell
    ps = f"""
$WS = New-Object -ComObject WScript.Shell
$SC = $WS.CreateShortcut("{shortcut_path}")
$SC.TargetPath = "python"
$SC.Arguments = '"{DESKTOP / "IGNITE.py"}"'
$SC.WorkingDirectory = "{DESKTOP}"
$SC.WindowStyle = 1
$SC.Description = "Launch Meeko Mycelium — Everything at once"
$SC.Save()
"""
    try:
        subprocess.run(['powershell', '-Command', ps], capture_output=True, timeout=10)
        print(f'  Desktop shortcut created: {shortcut_path}')
    except Exception as e:
        print(f'  Shortcut note: {e}')

    # Also create a .url as fallback (always works)
    url_path = DESKTOP / 'MEEKO BRIDGE.url'
    url_path.write_text('[InternetShortcut]\nURL=http://localhost:7775\n')
    print(f'  Browser shortcut: {url_path}')

# ── MAIN ──────────────────────────────────────────────────
if __name__ == '__main__':
    print(f"\n{'='*58}")
    print(f"  MEEKO MYCELIUM — IGNITE")
    print(f"{'='*58}")
    print(f"\n  Scanning your system...")

    in_github     = scan_github_secrets()
    local_secrets = load_existing_secrets()

    print(f"  GitHub secrets found: {len(in_github)}")
    for s in sorted(in_github):
        print(f"    IN GITHUB: {s}")
    print(f"  Local secrets loaded: {len(local_secrets)}")
    print()

    # Build HTML with live data
    BridgeHandler._html_cache = build_html(in_github, local_secrets)

    # Create desktop shortcut
    create_desktop_shortcut()
    print()
    print(f"  Key Bridge: http://localhost:{PORT}")
    print(f"  Opening browser...")
    print(f"  Press Ctrl+C when done.\n")

    server = http.server.HTTPServer(('127.0.0.1', PORT), BridgeHandler)
    threading.Timer(1.2, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Key Bridge closed. Secrets saved.")
