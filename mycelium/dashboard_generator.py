#!/usr/bin/env python3
"""
Dashboard Generator
====================
Generates a live public dashboard at the GitHub Pages site.

Updates every cycle with real data:
  - System health score (live)
  - Total ideas tested / passed
  - Engines running
  - Self-built engines count
  - Congressional trades flagged
  - Gaza Rose art generated
  - Donations received / PCRF amount
  - Latest crypto signal
  - Top performing post
  - Evolution timeline
  - Live Palestine news ticker

Output: public/index.html (served by GitHub Pages)
The page auto-refreshes every 30 minutes.
Anyone can find it. Anyone can fork it.
"""

import json, datetime, os
from pathlib import Path

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
PUBLIC = ROOT / 'public'

TODAY = datetime.date.today().isoformat()

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def get_stats():
    stats = {
        'health':          100,
        'ideas_tested':    0,
        'ideas_passed':    0,
        'engines':         0,
        'self_built':      0,
        'trades_flagged':  0,
        'art_generated':   0,
        'donations_total': 0.0,
        'pcrf_total':      0.0,
        'top_signal':      None,
        'top_post':        None,
        'latest_evolution': None,
        'palestine_news':  [],
        'uptime_days':     0,
        'last_updated':    TODAY,
    }

    health = load(DATA / 'health_report.json')
    stats['health'] = health.get('score', 100)

    ledger = load(DATA / 'idea_ledger.json')
    ideas  = ledger.get('ideas', {})
    il     = list(ideas.values()) if isinstance(ideas, dict) else (ideas if isinstance(ideas, list) else [])
    stats['ideas_tested'] = len(il)
    stats['ideas_passed'] = sum(1 for i in il if i.get('status') in ('passed','wired'))

    try:
        stats['engines'] = len(list((ROOT / 'mycelium').glob('*.py')))
    except: pass

    evo = load(DATA / 'evolution_log.json')
    built = evo.get('built', [])
    stats['self_built'] = len(built)
    if built:
        stats['latest_evolution'] = built[-1]

    congress = load(DATA / 'congress.json')
    trades   = congress if isinstance(congress, list) else congress.get('trades', [])
    stats['trades_flagged'] = len(trades)

    arts = load(DATA / 'generated_art.json')
    al   = arts if isinstance(arts, list) else arts.get('art', [])
    stats['art_generated'] = len(al)

    kofi = load(DATA / 'kofi_events.json')
    ev   = kofi if isinstance(kofi, list) else kofi.get('events', [])
    total = sum(float(e.get('amount', 0)) for e in ev
                if e.get('type') in ('donation','Donation','subscription'))
    stats['donations_total'] = round(total, 2)
    stats['pcrf_total']      = round(total * 0.70, 2)

    signals = load(DATA / 'crypto_signals_queue.json', [])
    if signals:
        conf_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        signals.sort(key=lambda s: conf_order.get(s.get('confidence','LOW'), 2))
        stats['top_signal'] = signals[0]

    perf = load(DATA / 'content_performance.json')
    tp   = perf.get('top_post')
    if tp and tp.get('text'):
        stats['top_post'] = tp

    world  = load(DATA / 'world_state.json')
    events = world.get('events', world.get('news', []))
    stats['palestine_news'] = [
        e.get('title', e.get('headline', ''))
        for e in events
        if any(kw in e.get('title', e.get('headline', '')).lower()
               for kw in ['gaza', 'palestine', 'pcrf', 'west bank', 'ceasefire'])
    ][:5]

    try:
        start = datetime.date(2026, 2, 1)
        stats['uptime_days'] = (datetime.date.today() - start).days
    except: pass

    return stats

def health_color(score):
    if score >= 90: return '#2ecc71'
    if score >= 70: return '#f39c12'
    return '#e74c3c'

def render_html(s):
    signal_html = ''
    if s['top_signal']:
        sig = s['top_signal']
        signal_html = f"""
        <div class="signal-card">
          <div class="signal-header">⚡ LIVE SIGNAL: {sig.get('symbol','')} — {sig.get('action','')}</div>
          <div class="signal-body">
            <span>Entry: {sig.get('entry','')}</span>
            <span>Target: {sig.get('target','')}</span>
            <span>Confidence: {sig.get('confidence','')}</span>
          </div>
          <div class="signal-note">Not financial advice. Automated signal detection.</div>
        </div>"""

    news_items = ''.join(
        f'<li>{n[:140]}</li>' for n in s['palestine_news']
    ) if s['palestine_news'] else '<li>No Palestine-related news found today.</li>'

    evo_html = ''
    if s['latest_evolution']:
        e = s['latest_evolution']
        evo_html = f"<p><strong>Latest self-built engine:</strong> {e.get('title','')} &mdash; {e.get('date','')}</p>"

    hc = health_color(s['health'])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="1800">
  <title>Meeko Nerve Center — Live Dashboard</title>
  <meta name="description" content="A self-evolving autonomous AI that tracks congressional trades, generates Palestinian solidarity art, and funds PCRF. $0/month. Open source. Running right now.">
  <meta property="og:title" content="Meeko Nerve Center — Live AI Dashboard">
  <meta property="og:description" content="Autonomous AI for accountability + Palestinian relief. Self-evolving. Free. Open source.">
  <meta name="twitter:card" content="summary_large_image">
  <style>
    :root {{
      --bg: #0d0d0d;
      --card: #161616;
      --border: #2a2a2a;
      --text: #f0f0f0;
      --muted: #888;
      --rose: #e74c3c;
      --green: #2ecc71;
      --gold: #f39c12;
      --teal: #1abc9c;
      --blue: #3498db;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Courier New', monospace;
      font-size: 14px;
      line-height: 1.6;
    }}
    header {{
      background: linear-gradient(135deg, #1a0a0a 0%, #0d0d0d 100%);
      border-bottom: 1px solid var(--rose);
      padding: 2rem;
      text-align: center;
    }}
    header h1 {{
      font-size: 2rem;
      color: var(--rose);
      letter-spacing: 0.1em;
    }}
    header p {{
      color: var(--muted);
      margin-top: 0.5rem;
      max-width: 600px;
      margin-left: auto;
      margin-right: auto;
    }}
    .tagline {{
      color: var(--teal);
      font-size: 0.9rem;
      margin-top: 0.5rem;
    }}
    .badge-row {{
      display: flex;
      gap: 0.5rem;
      justify-content: center;
      flex-wrap: wrap;
      margin-top: 1rem;
    }}
    .badge {{
      background: var(--card);
      border: 1px solid var(--border);
      padding: 0.25rem 0.75rem;
      border-radius: 999px;
      font-size: 0.75rem;
      color: var(--muted);
    }}
    .badge.live {{ border-color: var(--green); color: var(--green); }}
    .badge.rose  {{ border-color: var(--rose);  color: var(--rose);  }}
    main {{
      max-width: 1100px;
      margin: 2rem auto;
      padding: 0 1rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }}
    .stat-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      text-align: center;
      transition: border-color 0.2s;
    }}
    .stat-card:hover {{ border-color: var(--rose); }}
    .stat-card .num {{
      font-size: 2.5rem;
      font-weight: bold;
      line-height: 1;
    }}
    .stat-card .label {{
      color: var(--muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      margin-top: 0.5rem;
    }}
    .section {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }}
    .section h2 {{
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: var(--muted);
      border-bottom: 1px solid var(--border);
      padding-bottom: 0.75rem;
      margin-bottom: 1rem;
    }}
    .health-bar {{
      height: 8px;
      background: var(--border);
      border-radius: 999px;
      overflow: hidden;
      margin: 0.5rem 0;
    }}
    .health-fill {{
      height: 100%;
      background: {hc};
      width: {s['health']}%;
      border-radius: 999px;
      transition: width 1s ease;
    }}
    .signal-card {{
      background: #0d1a17;
      border: 1px solid var(--teal);
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1rem;
    }}
    .signal-header {{
      color: var(--teal);
      font-weight: bold;
      margin-bottom: 0.5rem;
    }}
    .signal-body {{
      display: flex;
      gap: 1.5rem;
      flex-wrap: wrap;
      font-size: 0.85rem;
    }}
    .signal-note {{
      color: var(--muted);
      font-size: 0.7rem;
      margin-top: 0.5rem;
    }}
    ul.news {{ list-style: none; }}
    ul.news li {{
      padding: 0.4rem 0;
      border-bottom: 1px solid var(--border);
      color: #ccc;
    }}
    ul.news li:last-child {{ border-bottom: none; }}
    ul.news li::before {{ content: '\u2192 '; color: var(--rose); }}
    .mission-stack {{
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      font-size: 0.85rem;
    }}
    .mission-step {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.4rem 0.75rem;
      background: #111;
      border-radius: 4px;
    }}
    .mission-step .arrow {{ color: var(--rose); }}
    footer {{
      text-align: center;
      color: var(--muted);
      font-size: 0.75rem;
      padding: 2rem;
      border-top: 1px solid var(--border);
      margin-top: 2rem;
    }}
    footer a {{ color: var(--rose); text-decoration: none; }}
    .pulse {{
      display: inline-block;
      width: 8px; height: 8px;
      background: var(--green);
      border-radius: 50%;
      animation: pulse 2s infinite;
      margin-right: 0.5rem;
    }}
    @keyframes pulse {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50%        {{ opacity: 0.4; transform: scale(1.4); }}
    }}
    @media (max-width: 600px) {{
      header h1 {{ font-size: 1.4rem; }}
      .stat-card .num {{ font-size: 1.8rem; }}
    }}
  </style>
</head>
<body>

<header>
  <h1>🌹 Meeko Nerve Center</h1>
  <p>A self-evolving autonomous AI brain for accountability and Palestinian solidarity.</p>
  <p class="tagline"><span class="pulse"></span>Running right now &mdash; $0/month &mdash; open source &mdash; can't be shut down</p>
  <div class="badge-row">
    <span class="badge live">⚡ Live</span>
    <span class="badge rose">🌹 Gaza Rose</span>
    <span class="badge">AGPL-3.0</span>
    <span class="badge">Self-Evolving</span>
    <span class="badge">{s['uptime_days']}d uptime</span>
    <span class="badge">Updated: {TODAY}</span>
  </div>
</header>

<main>

  <div class="grid">
    <div class="stat-card">
      <div class="num" style="color:{hc}">{s['health']}</div>
      <div class="label">System Health / 100</div>
    </div>
    <div class="stat-card">
      <div class="num" style="color:var(--blue)">{s['engines']}</div>
      <div class="label">Autonomous Engines</div>
    </div>
    <div class="stat-card">
      <div class="num" style="color:var(--teal)">{s['self_built']}</div>
      <div class="label">Self-Built Engines</div>
    </div>
    <div class="stat-card">
      <div class="num" style="color:var(--gold)">{s['ideas_tested']}</div>
      <div class="label">Ideas Tested</div>
    </div>
    <div class="stat-card">
      <div class="num" style="color:var(--green)">{s['ideas_passed']}</div>
      <div class="label">Ideas Implemented</div>
    </div>
    <div class="stat-card">
      <div class="num" style="color:var(--rose)">{s['trades_flagged']}</div>
      <div class="label">Trades Flagged</div>
    </div>
    <div class="stat-card">
      <div class="num" style="color:#e91e63">{s['art_generated']}</div>
      <div class="label">Gaza Rose Art</div>
    </div>
    <div class="stat-card">
      <div class="num" style="color:var(--green)">${s['pcrf_total']}</div>
      <div class="label">To PCRF via Art Sales</div>
    </div>
  </div>

  <div class="section">
    <h2>System Health</h2>
    <div class="health-bar"><div class="health-fill"></div></div>
    <p style="color:{hc};margin-top:0.5rem">{s['health']}/100 &mdash; {'All systems operational' if s['health'] >= 90 else 'Some engines need attention' if s['health'] >= 70 else 'System degraded — self-healing active'}</p>
    {evo_html}
  </div>

  {f'<div class="section"><h2>Live Crypto Signal</h2>{signal_html}</div>' if signal_html else ''}

  <div class="section">
    <h2>Palestine Today</h2>
    <ul class="news">{news_items}</ul>
  </div>

  <div class="section">
    <h2>Mission Stack</h2>
    <div class="mission-stack">
      <div class="mission-step"><span>⚠️</span> Track congressional trades under the STOCK Act</div>
      <div class="mission-step"><span class="arrow">↓</span></div>
      <div class="mission-step"><span>🌹</span> Generate Gaza Rose art from accountability data</div>
      <div class="mission-step"><span class="arrow">↓</span></div>
      <div class="mission-step"><span>💰</span> Sell art on Ko-fi + Gumroad</div>
      <div class="mission-step"><span class="arrow">↓</span></div>
      <div class="mission-step"><span>💚</span> 70% of proceeds → PCRF (Palestinian children's medical relief)</div>
      <div class="mission-step"><span class="arrow">↓</span></div>
      <div class="mission-step"><span>🔄</span> System evolves itself daily, finds new ways to do all of the above</div>
    </div>
  </div>

  <div class="section">
    <h2>Fork This System</h2>
    <p style="margin-bottom:1rem;color:#ccc">Anyone can run their own node. Free. Takes 5 minutes. Every fork funds Palestinian relief.</p>
    <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center/fork"
       style="display:inline-block;background:var(--rose);color:#fff;padding:0.6rem 1.5rem;border-radius:6px;text-decoration:none;font-weight:bold">
      🌹 Fork &amp; Deploy Free
    </a>
    &nbsp;
    <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/MANIFESTO.md"
       style="display:inline-block;background:var(--card);border:1px solid var(--border);color:var(--text);padding:0.6rem 1.5rem;border-radius:6px;text-decoration:none">
      Read the Manifesto
    </a>
  </div>

</main>

<footer>
  <p>🌹 Meeko Nerve Center &mdash; Built by one person with no funding, no team, no office.</p>
  <p style="margin-top:0.5rem">
    <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">GitHub</a> &nbsp;|&nbsp;
    <a href="https://ko-fi.com/meekotharaccoon">Ko-fi</a> &nbsp;|&nbsp;
    <a href="https://www.pcrf.net">PCRF</a> &nbsp;|&nbsp;
    AGPL-3.0 &mdash; Free to fork
  </p>
  <p style="margin-top:0.5rem">Last updated: {TODAY} &mdash; Auto-refreshes every 30 min</p>
</footer>

</body>
</html>"""

def run():
    print(f'\n[dashboard] Generating live dashboard — {TODAY}')
    PUBLIC.mkdir(exist_ok=True)

    stats = get_stats()
    html  = render_html(stats)

    try:
        (PUBLIC / 'index.html').write_text(html)
        print(f'[dashboard] ✅ index.html written ({len(html):,} chars)')
        print(f'[dashboard] Stats: health={stats["health"]} engines={stats["engines"]} self_built={stats["self_built"]}')
    except Exception as e:
        print(f'[dashboard] Write error: {e}')

    # Save stats JSON for other systems to consume
    try:
        (DATA / 'dashboard_stats.json').write_text(json.dumps(stats, indent=2, default=str))
    except: pass

if __name__ == '__main__':
    run()
