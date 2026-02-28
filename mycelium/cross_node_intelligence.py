#!/usr/bin/env python3
"""
Cross-Node Intelligence Engine
================================
As the network grows (sister systems, forks, independent nodes)
they all need to talk to each other.

Right now each node is an island. This engine builds the bridges.

How nodes communicate:
  1. Each node publishes a PUBLIC intelligence feed:
     data/public_feed.json — committed to the repo, readable by anyone
     Contains: latest signals, latest accountability hits, latest art,
               current system status, what the node built today

  2. This engine reads feeds from sister nodes:
     Fetches their public_feed.json from GitHub raw content
     Aggregates signals: if 3 nodes flag the same pattern, it's significant
     Shares exclusive signals: what one node found that others haven't

  3. Cross-pollination:
     Ideas that worked in one node get shared to all nodes
     Engines that self-built in one node get proposed to others
     Press contacts that replied in one node get shared to network
     Grant funders that responded get flagged across the network

  4. Network health:
     Monitors which nodes are active vs dormant
     Sends revival emails to dormant nodes' owners
     Celebrates milestones across the network

The result:
  A decentralized intelligence network where each node is
  more powerful because of every other node.
  Information advantage compounds across the whole network.
  A journalist covering ONE node gets the whole picture.
  A funder backing ONE node funds the whole network.

This is the SolarPunk mycelium made digital.
Each node a mushroom. The network the actual organism.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_USERNAME    = os.environ.get('GITHUB_USERNAME', 'meekotharaccoon-cell')

RAW_BASE = f'https://raw.githubusercontent.com/{GITHUB_USERNAME}'

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def fetch_json(url):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-network/1.0'})
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except:
        return None

def publish_own_feed():
    """Publish this node's public intelligence feed."""
    feed = {
        'node':     'meeko-nerve-center',
        'date':     TODAY,
        'status':   'active',
        'url':      f'https://github.com/{GITHUB_USERNAME}/meeko-nerve-center',
        'mission':  'Palestinian solidarity + congressional accountability',
    }

    # Latest signals
    try:
        sigs = load(DATA / 'crypto_signals_queue.json', [])
        feed['signals'] = [{
            'symbol': s.get('symbol'), 'action': s.get('action'),
            'confidence': s.get('confidence')
        } for s in sigs[:3]]
    except: pass

    # Latest trade
    try:
        congress = load(DATA / 'congress.json')
        trades = congress if isinstance(congress, list) else congress.get('trades', [])
        if trades:
            t = trades[0]
            feed['latest_accountability'] = (
                f"{t.get('representative', t.get('senator','?'))} "
                f"traded {t.get('ticker','?')}"
            )
    except: pass

    # Stats
    try:
        feed['stats'] = {
            'engines':     len(list((ROOT / 'mycelium').glob('*.py'))),
            'github_stars': load(DATA / 'audience_report.json').get('github', {}).get('stars', 0),
        }
    except: pass

    # What was built today
    try:
        evo = load(DATA / 'evolution_log.json')
        today_builds = [b for b in evo.get('built', []) if b.get('date') == TODAY]
        if today_builds:
            feed['built_today'] = today_builds[-1].get('title', '')
    except: pass

    # Save publicly
    try:
        (DATA / 'public_feed.json').write_text(json.dumps(feed, indent=2))
        print(f'[network] Own feed published')
    except Exception as e:
        print(f'[network] Feed publish error: {e}')

    return feed

def read_sister_feeds():
    """Read public feeds from all sister nodes."""
    spawner_log = load(DATA / 'spawner_log.json', {'network': []})
    sister_nodes = spawner_log.get('network', [])

    feeds = []
    for node in sister_nodes:
        repo = node.get('repo', '')
        if not repo: continue
        url = f'{RAW_BASE}/{repo}/main/data/public_feed.json'
        feed = fetch_json(url)
        if feed:
            feeds.append(feed)
            print(f'[network] Read feed: {repo} — {feed.get("status", "?")} ({feed.get("date", "?")})')
        else:
            print(f'[network] No feed yet: {repo}')

    return feeds

def find_cross_node_patterns(own_feed, sister_feeds):
    """Find signals that appear across multiple nodes."""
    if not sister_feeds: return []

    # Find shared signals
    all_signals = []
    for feed in [own_feed] + sister_feeds:
        for sig in feed.get('signals', []):
            all_signals.append(sig.get('symbol', ''))

    from collections import Counter
    counts = Counter(all_signals)
    shared = [sym for sym, count in counts.items() if count >= 2 and sym]

    patterns = []
    if shared:
        patterns.append({
            'type':    'converging_signal',
            'detail':  f'Multiple nodes flagging: {', '.join(shared)}',
            'nodes':   len(sister_feeds) + 1,
            'significance': 'HIGH — network convergence',
        })

    return patterns

def synthesize_network_brief(own_feed, sister_feeds, patterns):
    if not HF_TOKEN or not sister_feeds: return None
    active = sum(1 for f in sister_feeds if f.get('status') == 'active')
    summary = {
        'total_nodes':  len(sister_feeds) + 1,
        'active_nodes': active + 1,
        'patterns':     patterns,
        'sister_missions': [f.get('mission', '')[:60] for f in sister_feeds[:5]],
    }
    prompt = f"""Synthesize this multi-node network intelligence brief in 3 sentences.

Network state: {json.dumps(summary, indent=2)}

What does this network collectively know that no single node knows alone?
What's the most important cross-node insight?
SolarPunk framing: this is decentralized justice infrastructure.

Return 3 sentences only. Plain text."""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 150,
            'messages': [
                {'role': 'system', 'content': 'You synthesize network intelligence. 3 sentences. Be specific.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except:
        return None

def send_network_brief(brief, own_feed, sister_feeds, patterns):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    if not sister_feeds: return  # No point until there are sisters
    lines = [
        f'🌐 Network Intelligence Brief — {TODAY}',
        f'Nodes: {len(sister_feeds)+1} | Active: {sum(1 for f in sister_feeds if f.get("status")=="active")+1}',
        '',
    ]
    if brief:
        lines += ['SYNTHESIS:', brief, '']
    if patterns:
        lines.append('CROSS-NODE PATTERNS:')
        for p in patterns:
            lines.append(f'  [{p["significance"]}] {p["detail"]}')
        lines.append('')
    lines.append('SISTER NODE STATUS:')
    for f in sister_feeds[:5]:
        icon = '✅' if f.get('status') == 'active' else '😴'
        lines.append(f'  {icon} {f.get("node","?")} — last: {f.get("date","?")}')
        if f.get('built_today'):
            lines.append(f'       Built today: {f["built_today"]}')
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🌐 Network brief: {len(sister_feeds)+1} nodes active'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[network] Brief emailed')
    except Exception as e:
        print(f'[network] Email error: {e}')

def run():
    print(f'\n[network] 🌐 Cross-Node Intelligence — {TODAY}')

    own_feed     = publish_own_feed()
    sister_feeds = read_sister_feeds()
    patterns     = find_cross_node_patterns(own_feed, sister_feeds)
    brief        = synthesize_network_brief(own_feed, sister_feeds, patterns)

    report = {
        'date':          TODAY,
        'own_node':      'meeko-nerve-center',
        'sister_count':  len(sister_feeds),
        'patterns':      patterns,
        'brief':         brief,
    }
    try: (DATA / 'network_intelligence.json').write_text(json.dumps(report, indent=2))
    except: pass

    send_network_brief(brief, own_feed, sister_feeds, patterns)

    print(f'[network] Nodes: {len(sister_feeds)+1} | Patterns: {len(patterns)}')
    if brief:
        print(f'[network] Brief: {brief[:100]}')
    print('[network] The mycelium speaks. 🍄')

if __name__ == '__main__':
    run()
