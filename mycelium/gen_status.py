#!/usr/bin/env python3
"""
gen_status.py - Generate live status.html from data bus JSON files.
Fix: pre-compute all dynamic values BEFORE the f-string to avoid
nested single quotes inside single-quoted f-strings (Python 3.11 SyntaxError).
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

def load(filename, default=None):
    if default is None:
        default = {}
    p = DATA / filename
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return default

def main():
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    wiring   = load('wiring_status.json')
    space    = load('space_data.json')
    briefing = load('briefing_data.json')

    iss = space.get('iss_position', {})
    lat = iss.get('latitude', 'N/A')
    lon = iss.get('longitude', 'N/A')

    ollama_running = briefing.get('ollama_running', False)
    ollama_models  = briefing.get('models', [])
    gh_forks       = briefing.get('github_forks', 0)
    gh_stars       = briefing.get('github_stars', 0)
    email_enabled  = briefing.get('email_enabled', False)
    tailscale_ip   = briefing.get('tailscale_ip', 'offline')
    connections    = wiring.get('connections', {})

    # Pre-compute all dynamic fragments (avoids nested quote errors in f-string)
    if connections:
        conn_parts = []
        for k, v in connections.items():
            css   = 'ok' if v else 'off'
            label = k.replace('_', ' ')
            conn_parts.append('<div class="conn ' + css + '"><span class="dot"></span>' + label + '</div>')
        conn_items = ''.join(conn_parts)
    else:
        conn_items = '<div class="conn off"><span class="dot"></span>No connection data yet</div>'

    ollama_class = '' if ollama_running else ' off'
    ollama_text  = 'running' if ollama_running else 'offline'
    email_class  = '' if email_enabled else ' off'
    email_text   = 'live' if email_enabled else 'dark (add secret)'
    models_text  = ', '.join(ollama_models) if ollama_models else 'none'

    # Build HTML using string concatenation for the dynamic parts
    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<meta http-equiv="refresh" content="300">\n'
        '<title>Meeko Mycelium \u2014 Live Status</title>\n'
        '<style>\n'
        '  * { box-sizing:border-box; margin:0; padding:0; }\n'
        '  :root { --g:#39ff14; --dark:#0a0a0a; --card:#111; --b:#222; --dim:#555; }\n'
        '  body { background:var(--dark); color:#eee; font-family:\'Courier New\',monospace; padding:24px; }\n'
        '  h1 { color:var(--g); font-size:1.6rem; margin-bottom:4px; }\n'
        '  .ts { color:var(--dim); font-size:0.8rem; margin-bottom:28px; }\n'
        '  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px; margin-bottom:24px; }\n'
        '  .card { background:var(--card); border:1px solid var(--b); border-radius:10px; padding:18px; }\n'
        '  .card h2 { color:var(--g); font-size:0.85rem; text-transform:uppercase; margin-bottom:14px; }\n'
        '  .stat { display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.88rem; }\n'
        '  .stat .val { color:var(--g); }\n'
        '  .stat .val.off { color:#ff4444; }\n'
        '  .stat .val.dim { color:var(--dim); }\n'
        '  .conn { font-size:0.82rem; margin-bottom:6px; display:flex; align-items:center; gap:6px; }\n'
        '  .dot { width:7px; height:7px; border-radius:50%; background:#ff4444; display:inline-block; flex-shrink:0; }\n'
        '  .conn.ok .dot { background:var(--g); animation:pulse 2s infinite; }\n'
        '  @keyframes pulse {0%,100%{opacity:1}50%{opacity:.3}}\n'
        '  .links { display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }\n'
        '  .links a { color:var(--g); background:#0a1a0a; border:1px solid #1a3a1a; border-radius:6px; padding:6px 12px; text-decoration:none; font-size:0.82rem; }\n'
        '  .links a:hover { background:#1a3a1a; }\n'
        '</style>\n</head>\n<body>\n'
        '<h1>\U0001f578\ufe0f Meeko Mycelium \u2014 Live Status</h1>\n'
        '<div class="ts">Last updated: ' + now + ' &middot; Auto-refreshes every 5 min</div>\n'
        '<div class="grid">\n'
        '  <div class="card"><h2>\U0001f680 Space Layer</h2>\n'
        '    <div class="stat"><span>ISS Latitude</span><span class="val">' + str(lat) + '</span></div>\n'
        '    <div class="stat"><span>ISS Longitude</span><span class="val">' + str(lon) + '</span></div>\n'
        '  </div>\n'
        '  <div class="card"><h2>\U0001f9e0 Local Brain</h2>\n'
        '    <div class="stat"><span>Ollama</span><span class="val' + ollama_class + '">' + ollama_text + '</span></div>\n'
        '    <div class="stat"><span>Models</span><span class="val dim">' + models_text + '</span></div>\n'
        '    <div class="stat"><span>Email</span><span class="val' + email_class + '">' + email_text + '</span></div>\n'
        '  </div>\n'
        '  <div class="card"><h2>\U0001f4cd GitHub</h2>\n'
        '    <div class="stat"><span>Forks</span><span class="val">' + str(gh_forks) + '</span></div>\n'
        '    <div class="stat"><span>Stars</span><span class="val">' + str(gh_stars) + '</span></div>\n'
        '    <div class="stat"><span>Tailscale</span><span class="val dim">' + str(tailscale_ip) + '</span></div>\n'
        '  </div>\n'
        '  <div class="card"><h2>\U0001f578\ufe0f Connections</h2>\n'
        '    ' + conn_items + '\n'
        '  </div>\n'
        '</div>\n'
        '<div class="links">\n'
        '  <a href="spawn.html">\U0001f41a Spawn</a>\n'
        '  <a href="proliferator.html">\U0001f525 Proliferator</a>\n'
        '  <a href="revenue.html">\U0001f4b8 Revenue</a>\n'
        '  <a href="dashboard.html">\U0001f4ca Dashboard</a>\n'
        '  <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">\U0001f517 GitHub</a>\n'
        '</div>\n</body>\n</html>'
    )

    out = ROOT / 'status.html'
    out.write_text(html)
    print('status.html written (' + str(len(html)) + ' chars)')
    print('  ISS: ' + str(lat) + ', ' + str(lon))
    print('  Ollama: ' + ollama_text)

if __name__ == '__main__':
    main()
