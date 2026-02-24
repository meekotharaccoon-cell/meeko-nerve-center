#!/usr/bin/env python3
"""
gen_status.py — Generate live status.html from data bus JSON files.
Runs in GitHub Actions heartbeat. Writes to status.html in repo root.
This page shows REAL live data auto-updated twice a day.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

def load(filename, default={}):
    p = DATA / filename
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return default

def main():
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    wiring  = load('wiring_status.json')
    state   = load('system_state.json')
    space   = load('space_data.json')
    briefing = load('briefing_data.json')

    # Parse data
    iss = space.get('iss_position', {})
    lat = iss.get('latitude', 'N/A')
    lon = iss.get('longitude', 'N/A')
    
    ollama_running = briefing.get('ollama_running', False)
    ollama_models  = briefing.get('models', [])
    gh_forks       = briefing.get('github_forks', 0)
    gh_stars       = briefing.get('github_stars', 0)
    email_enabled  = briefing.get('email_enabled', False)
    tailscale_ip   = briefing.get('tailscale_ip', 'offline')
    payments_live  = briefing.get('payments_live', False)
    
    local  = wiring.get('local', {})
    github = wiring.get('github', {})

    connections = wiring.get('connections', {})
    conn_items = ''.join([
        f'<div class="conn {'ok' if v else 'off'}"><span class="dot"></span>{k.replace('_',' ')}</div>'
        for k, v in connections.items()
    ]) if connections else '<div class="conn off"><span class="dot"></span>No connection data yet</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="300"><!-- auto-refresh every 5 min -->
<title>Meeko Mycelium — Live Status</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  :root {{ --g:#39ff14; --dark:#0a0a0a; --card:#111; --b:#222; --dim:#555; }}
  body {{ background:var(--dark); color:#eee; font-family:'Courier New',monospace; padding:24px; }}
  h1 {{ color:var(--g); font-size:1.6rem; margin-bottom:4px; }}
  .ts {{ color:var(--dim); font-size:0.8rem; margin-bottom:28px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px; margin-bottom:24px; }}
  .card {{ background:var(--card); border:1px solid var(--b); border-radius:10px; padding:18px; }}
  .card h2 {{ color:var(--g); font-size:0.85rem; letter-spacing:.08em; text-transform:uppercase; margin-bottom:14px; }}
  .stat {{ display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.88rem; }}
  .stat .val {{ color:var(--g); }}
  .stat .val.off {{ color:#ff4444; }}
  .stat .val.dim {{ color:var(--dim); }}
  .conn {{ font-size:0.82rem; margin-bottom:6px; display:flex; align-items:center; gap:6px; }}
  .dot {{ width:7px; height:7px; border-radius:50%; background:#ff4444; display:inline-block; flex-shrink:0; }}
  .conn.ok .dot {{ background:var(--g); animation:pulse 2s infinite; }}
  @keyframes pulse {{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
  .links {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }}
  .links a {{ color:var(--g); background:#0a1a0a; border:1px solid #1a3a1a; border-radius:6px;
              padding:6px 12px; text-decoration:none; font-size:0.82rem; }}
  .links a:hover {{ background:#1a3a1a; }}
  .pulse {{ animation:pulse 2s infinite; }}
</style>
</head>
<body>

<h1>🕸️ Meeko Mycelium — Live Status</h1>
<div class="ts">⭐ Last updated: {now} · Auto-refreshes every 5 minutes</div>

<div class="grid">

  <div class="card">
    <h2>🚀 Space Layer</h2>
    <div class="stat"><span>ISS Latitude</span><span class="val">{lat}</span></div>
    <div class="stat"><span>ISS Longitude</span><span class="val">{lon}</span></div>
    <div class="stat"><span>Data source</span><span class="val">open-notify.org</span></div>
  </div>

  <div class="card">
    <h2>🧠 Local Brain</h2>
    <div class="stat"><span>Ollama</span><span class="val {'off' if not ollama_running else ''}">{"running" if ollama_running else "offline"}</span></div>
    <div class="stat"><span>Models</span><span class="val dim">{', '.join(ollama_models) if ollama_models else 'none'}</span></div>
    <div class="stat"><span>Email layer</span><span class="val {'off' if not email_enabled else ''}">{"live" if email_enabled else "dark (add secret)"}</span></div>
  </div>

  <div class="card">
    <h2>📍 GitHub</h2>
    <div class="stat"><span>Forks</span><span class="val">{gh_forks}</span></div>
    <div class="stat"><span>Stars</span><span class="val">{gh_stars}</span></div>
    <div class="stat"><span>Tailscale</span><span class="val dim">{tailscale_ip}</span></div>
  </div>

  <div class="card">
    <h2>🕸️ Connections</h2>
    {conn_items}
  </div>

</div>

<div class="links">
  <a href="spawn.html">🐚 Spawn</a>
  <a href="proliferator.html">🔥 Proliferator</a>
  <a href="revenue.html">💸 Revenue</a>
  <a href="dashboard.html">📊 Dashboard</a>
  <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">🔗 GitHub</a>
</div>

</body>
</html>"""

    out = ROOT / 'status.html'
    out.write_text(html)
    print(f"\033[92m✓ status.html written ({len(html)} chars)\033[0m")
    print(f"  ISS: {lat}, {lon}")
    print(f"  Ollama: {'running' if ollama_running else 'offline'}")
    print(f"  Email: {'live' if email_enabled else 'dark'}")

if __name__ == '__main__':
    main()
