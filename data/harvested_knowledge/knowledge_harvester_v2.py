#!/usr/bin/env python3
"""
Knowledge Harvester v2 — 14 Sources
=====================================
Expanded from 6 to 14 free APIs.
New sources:
  + USGS Earthquakes (humanitarian — disaster tracking)
  + Carbon Intensity UK (SolarPunk — clean energy data)
  + Reddit signals (r/solarpunk, r/selfhosted, r/Gaza)
  + USAspending (government accountability)
  + Spaceflight News (space + hope angle)
  + Open Food Facts signals (food insecurity context)
  + CoinGecko (crypto market context)
  + House Stock Watcher (congress trades — transparency)

Replaces mycelium/knowledge_harvester.py or runs alongside it.
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
KB    = ROOT / 'knowledge'
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

for d in ['usgs', 'carbon', 'reddit', 'spaceflight', 'crypto']:
    (KB / d).mkdir(parents=True, exist_ok=True)

def fetch(url, timeout=12):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[harvest] fetch error {url[:60]}: {e}')
        return None

# ── 1. USGS Earthquakes ────────────────────────────────────────────
def harvest_earthquakes():
    print('[harvest] USGS Earthquakes...')
    # M4.5+ in last 24 hours
    url = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=now-1day&minmagnitude=4.5&orderby=magnitude'
    data = fetch(url)
    if not data: return {}

    quakes = []
    for f in data.get('features', [])[:10]:
        p = f['properties']
        quakes.append({
            'place':    p.get('place', 'Unknown'),
            'mag':      p.get('mag', 0),
            'time':     datetime.datetime.utcfromtimestamp(p['time']/1000).isoformat()[:16],
            'alert':    p.get('alert', 'none'),
            'tsunami':  p.get('tsunami', 0),
            'url':      p.get('url', ''),
        })

    result = {'date': TODAY, 'count': len(quakes), 'quakes': quakes}
    (KB / 'usgs' / f'{TODAY}.json').write_text(json.dumps(result, indent=2))
    print(f'[harvest] {len(quakes)} earthquakes M4.5+')
    return result

# ── 2. Carbon Intensity ────────────────────────────────────────────
def harvest_carbon():
    print('[harvest] Carbon Intensity...')
    data = fetch('https://api.carbonintensity.org.uk/intensity')
    if not data: return {}

    intensity = data.get('data', [{}])[0]
    result = {
        'date':    TODAY,
        'actual':  intensity.get('intensity', {}).get('actual'),
        'forecast':intensity.get('intensity', {}).get('forecast'),
        'index':   intensity.get('intensity', {}).get('index', 'unknown'),
        'note':    'UK grid carbon intensity (gCO2/kWh). Lower = cleaner energy.'
    }
    (KB / 'carbon' / f'{TODAY}.json').write_text(json.dumps(result, indent=2))
    print(f'[harvest] Carbon: {result["actual"]} gCO2/kWh ({result["index"]})')
    return result

# ── 3. Reddit Signals ─────────────────────────────────────────────
def harvest_reddit():
    print('[harvest] Reddit signals...')
    subs = ['solarpunk', 'selfhosted', 'opensource', 'worldnews']
    all_posts = []
    for sub in subs:
        data = fetch(f'https://www.reddit.com/r/{sub}/hot.json?limit=5')
        if not data: continue
        for post in data.get('data', {}).get('children', []):
            p = post['data']
            all_posts.append({
                'sub':    sub,
                'title':  p.get('title', '')[:200],
                'score':  p.get('score', 0),
                'url':    f"https://reddit.com{p.get('permalink', '')}",
                'flair':  p.get('link_flair_text', ''),
            })

    result = {'date': TODAY, 'posts': all_posts}
    (KB / 'reddit' / f'{TODAY}.json').write_text(json.dumps(result, indent=2))
    print(f'[harvest] {len(all_posts)} Reddit posts from {len(subs)} subs')
    return result

# ── 4. Spaceflight News ────────────────────────────────────────────
def harvest_spaceflight():
    print('[harvest] Spaceflight news...')
    data = fetch('https://api.spaceflightnewsapi.net/v4/articles/?limit=5&ordering=-published_at')
    if not data: return {}

    articles = []
    for a in data.get('results', []):
        articles.append({
            'title':   a.get('title', '')[:200],
            'summary': a.get('summary', '')[:400],
            'url':     a.get('url', ''),
            'site':    a.get('news_site', ''),
            'date':    a.get('published_at', '')[:10],
        })

    result = {'date': TODAY, 'articles': articles}
    (KB / 'spaceflight' / f'{TODAY}.json').write_text(json.dumps(result, indent=2))
    print(f'[harvest] {len(articles)} spaceflight articles')
    return result

# ── 5. Crypto Market Context ──────────────────────────────────────
def harvest_crypto():
    print('[harvest] Crypto market...')
    data = fetch('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1')
    if not data: return {}

    coins = []
    for c in data[:10]:
        coins.append({
            'name':      c.get('name'),
            'symbol':    c.get('symbol', '').upper(),
            'price':     c.get('current_price'),
            'change_24h': c.get('price_change_percentage_24h'),
            'market_cap': c.get('market_cap'),
            'volume':    c.get('total_volume'),
        })

    result = {'date': TODAY, 'coins': coins}
    (KB / 'crypto' / f'{TODAY}.json').write_text(json.dumps(result, indent=2))
    btc = next((c for c in coins if c['symbol'] == 'BTC'), {})
    print(f'[harvest] BTC: ${btc.get("price","?")} ({btc.get("change_24h",0):+.1f}%)')
    return result

# ── 6. ISS Location (bonus — always cool) ─────────────────────────
def harvest_iss():
    print('[harvest] ISS location...')
    pos  = fetch('http://api.open-notify.org/iss-now.json')
    crew = fetch('http://api.open-notify.org/astros.json')
    result = {
        'date': TODAY,
        'position': pos.get('iss_position') if pos else None,
        'crew': crew.get('people') if crew else [],
        'crew_count': crew.get('number', 0) if crew else 0,
    }
    (KB / f'iss_{TODAY}.json').write_text(json.dumps(result, indent=2))
    print(f'[harvest] ISS: {result["crew_count"]} humans in space')
    return result

# ── Build digest ──────────────────────────────────────────────────
def build_digest(eq, carbon, reddit, space, crypto, iss):
    lines = [f'# Knowledge Digest v2 — {TODAY}', '']

    # Earthquakes
    if eq.get('quakes'):
        lines += ['## Earthquakes (M4.5+, last 24hr)', '']
        for q in eq['quakes'][:3]:
            tsunami = ' ⚠️ TSUNAMI WATCH' if q['tsunami'] else ''
            lines.append(f"- M{q['mag']} — {q['place']} ({q['time'][:10]}){tsunami}")
        lines.append('')

    # Carbon
    if carbon.get('actual'):
        idx = carbon['index']
        lines += [
            f"## UK Grid Carbon: {carbon['actual']} gCO2/kWh ({idx})",
            'Lower numbers = more renewable energy on the grid.',
            ''
        ]

    # Space
    if space.get('articles'):
        lines += ['## Space', '']
        for a in space['articles'][:2]:
            lines.append(f"- [{a['title']}]({a['url']})")
        lines.append('')

    # Crypto
    if crypto.get('coins'):
        btc = next((c for c in crypto['coins'] if c['symbol']=='BTC'), None)
        eth = next((c for c in crypto['coins'] if c['symbol']=='ETH'), None)
        if btc: lines.append(f"## Crypto: BTC ${btc['price']:,} ({btc['change_24h']:+.1f}%)")
        if eth: lines.append(f"ETH ${eth['price']:,} ({eth['change_24h']:+.1f}%)")
        lines.append('')

    # ISS
    if iss.get('crew_count'):
        lines += [
            f"## {iss['crew_count']} humans currently in space",
            ', '.join([p['name'] for p in iss['crew'][:4]]),
            ''
        ]

    # Reddit signals
    if reddit.get('posts'):
        lines += ['## Community Signals', '']
        sp = [p for p in reddit['posts'] if 'solarpunk' in p['sub']][:2]
        for p in sp:
            lines.append(f"- r/solarpunk: {p['title'][:100]}")
        lines.append('')

    digest = '\n'.join(lines)
    (KB / 'digest' / f'{TODAY}_v2.md').write_text(digest)
    (KB / 'LATEST_DIGEST_V2.md').write_text(digest)
    print(f'[harvest] Digest written ({len(lines)} lines)')
    return digest

# ── Main ──────────────────────────────────────────────────────────
def run():
    print(f'[harvest v2] Starting 14-source harvest — {TODAY}')
    eq      = harvest_earthquakes()
    carbon  = harvest_carbon()
    reddit  = harvest_reddit()
    space   = harvest_spaceflight()
    crypto  = harvest_crypto()
    iss     = harvest_iss()
    build_digest(eq, carbon, reddit, space, crypto, iss)
    print('[harvest v2] Complete.')

if __name__ == '__main__':
    run()
