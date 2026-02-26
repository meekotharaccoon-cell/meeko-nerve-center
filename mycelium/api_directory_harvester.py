#!/usr/bin/env python3
"""
API Directory Harvester
========================
Scrapes free API directories to discover new tools for the system.

Sources:
  - https://github.com/public-apis/public-apis (the master list)
  - https://public-apis.io
  - Raw GitHub API list (JSON)

Outputs:
  - knowledge/apis/latest.json  — full catalog
  - knowledge/apis/new_today.md — APIs discovered today
  - data/api_opportunities.json — APIs most relevant to Meeko's mission

Runs daily. Every new useful free API = potential new system capability.
"""

import json, datetime, re
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
KB    = ROOT / 'knowledge'
DATA  = ROOT / 'data'
(KB / 'apis').mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()

# Categories most relevant to Meeko's mission
MISSION_CATEGORIES = [
    'Cryptocurrency', 'Finance', 'Government', 'Social',
    'News', 'Science', 'Open Data', 'Environment',
    'Humanitarian', 'Charity', 'Jobs', 'Art',
    'Music', 'Development', 'Machine Learning',
]

MISSION_KEYWORDS = [
    'free', 'open', 'humanitarian', 'climate', 'environment',
    'crypto', 'bitcoin', 'solana', 'nft', 'defi',
    'government', 'congress', 'transparency', 'open data',
    'news', 'social', 'community', 'charity', 'nonprofit',
    'earthquake', 'disaster', 'space', 'nasa',
    'jobs', 'remote work', 'freelance',
    'art', 'music', 'creative',
]

def fetch(url, timeout=15):
    try:
        req = urllib_request.Request(
            url,
            headers={'User-Agent': 'meeko-nerve-center/2.0 (github.com/meekotharaccoon-cell/meeko-nerve-center)'}
        )
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'[api-harvest] fetch error {url[:60]}: {e}')
        return ''

def fetch_json(url, timeout=15):
    raw = fetch(url, timeout)
    if not raw: return None
    try:
        return json.loads(raw)
    except:
        return None

# ── Source 1: public-apis GitHub raw JSON ─────────────────────────────────
def harvest_public_apis_github():
    """
    The canonical public-apis list.
    Raw JSON from: https://github.com/public-apis/public-apis
    They maintain a machine-readable index at the API.
    """
    print('[api-harvest] Fetching public-apis/public-apis...')

    # Try the raw README to parse categories
    raw = fetch('https://raw.githubusercontent.com/public-apis/public-apis/master/README.md')
    if not raw:
        return []

    apis = []
    current_category = 'Unknown'
    
    for line in raw.split('\n'):
        # Category header
        if line.startswith('## '):
            current_category = line[3:].strip()
            continue
        
        # Table row: | API | Description | Auth | HTTPS | CORS |
        if line.startswith('|') and '|' in line[1:]:
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]  # remove empty
            if len(parts) >= 3 and parts[0] != 'API' and '---' not in parts[0]:
                # Extract link from markdown [Name](url)
                name_raw = parts[0]
                desc = parts[1] if len(parts) > 1 else ''
                auth = parts[2] if len(parts) > 2 else ''
                https = parts[3] if len(parts) > 3 else ''
                
                # Parse name and URL from [Name](URL)
                url_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', name_raw)
                if url_match:
                    name = url_match.group(1)
                    url  = url_match.group(2)
                else:
                    name = name_raw
                    url  = ''
                
                apis.append({
                    'name':     name,
                    'description': desc,
                    'category': current_category,
                    'auth':     auth,
                    'https':    https == 'Yes',
                    'url':      url,
                    'free':     auth.lower() in ['no', 'apikey', ''],
                    'source':   'public-apis/public-apis',
                })
    
    print(f'[api-harvest] Parsed {len(apis)} APIs from public-apis/public-apis')
    return apis

# ── Source 2: Mixed Analytics big list (already in our knowledge) ──────────
def harvest_mixed_analytics_list():
    """
    The big list from the document the user shared.
    Already parsed — 224 APIs across categories.
    We store these as known-good baseline.
    """
    # These are the ones from the user's document
    known_good = [
        {'name': 'DEX Screener',      'url': 'https://api.dexscreener.com', 'category': 'Crypto', 'auth': 'no',     'free': True},
        {'name': 'CoinGecko',         'url': 'https://api.coingecko.com',   'category': 'Crypto', 'auth': 'no',     'free': True},
        {'name': 'House Stock Watcher','url': 'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json', 'category': 'Government', 'auth': 'no', 'free': True},
        {'name': 'USGS Earthquakes',  'url': 'https://earthquake.usgs.gov/fdsnws/event/1/', 'category': 'Science', 'auth': 'no', 'free': True},
        {'name': 'Carbon Intensity',  'url': 'https://api.carbonintensity.org.uk', 'category': 'Environment', 'auth': 'no', 'free': True},
        {'name': 'Open Notify (ISS)', 'url': 'http://api.open-notify.org',  'category': 'Science', 'auth': 'no',   'free': True},
        {'name': 'Spaceflight News',  'url': 'https://api.spaceflightnewsapi.net', 'category': 'Science', 'auth': 'no', 'free': True},
        {'name': 'SpaceX',            'url': 'https://api.spacexdata.com',  'category': 'Science', 'auth': 'no',   'free': True},
        {'name': 'NASA',              'url': 'https://api.nasa.gov',        'category': 'Science', 'auth': 'apikey','free': True},
        {'name': 'Reddit',            'url': 'https://www.reddit.com',      'category': 'Social',  'auth': 'no',   'free': True},
        {'name': 'HackerNews',        'url': 'https://hacker-news.firebaseio.com', 'category': 'News', 'auth': 'no','free': True},
        {'name': 'USAspending',       'url': 'https://api.usaspending.gov', 'category': 'Government', 'auth': 'no','free': True},
        {'name': 'FBI Wanted',        'url': 'https://api.fbi.gov',         'category': 'Government', 'auth': 'no','free': True},
        {'name': 'Open Food Facts',   'url': 'https://world.openfoodfacts.org', 'category': 'Food', 'auth': 'no', 'free': True},
        {'name': 'CoinCap',           'url': 'https://api.coincap.io',      'category': 'Crypto', 'auth': 'no',   'free': True},
        {'name': 'Binance',           'url': 'https://api4.binance.com',    'category': 'Crypto', 'auth': 'no',   'free': True},
        {'name': 'Kraken',            'url': 'https://api.kraken.com',      'category': 'Crypto', 'auth': 'no',   'free': True},
        {'name': 'GeckoTerminal',     'url': 'https://api.geckoterminal.com','category': 'Crypto', 'auth': 'no',  'free': True},
        {'name': 'Open Library',      'url': 'https://openlibrary.org',     'category': 'Books',  'auth': 'no',   'free': True},
        {'name': 'arXiv',             'url': 'https://arxiv.org/help/api',  'category': 'Science', 'auth': 'no',  'free': True},
        {'name': 'Wikipedia',         'url': 'https://en.wikipedia.org/w/api.php', 'category': 'Content', 'auth': 'no', 'free': True},
        {'name': 'Jobicy',            'url': 'https://jobicy.com/api/v2/remote-jobs', 'category': 'Jobs', 'auth': 'no', 'free': True},
        {'name': 'Open Brewery DB',   'url': 'https://api.openbrewerydb.org', 'category': 'Food', 'auth': 'no',  'free': True},
        {'name': 'Art Institute of Chicago', 'url': 'https://api.artic.edu', 'category': 'Art', 'auth': 'no',   'free': True},
        {'name': 'Metropolitan Museum', 'url': 'https://collectionapi.metmuseum.org', 'category': 'Art', 'auth': 'no', 'free': True},
        {'name': 'MusicBrainz',       'url': 'https://musicbrainz.org/ws/2/', 'category': 'Music', 'auth': 'no', 'free': True},
        {'name': 'iTunes Search',     'url': 'https://itunes.apple.com/search', 'category': 'Music', 'auth': 'no','free': True},
        {'name': 'ExchangeRate-API',  'url': 'https://open.er-api.com',     'category': 'Finance','auth': 'no',  'free': True},
        {'name': 'Data USA',          'url': 'https://datausa.io/api',      'category': 'Government','auth': 'no','free': True},
        {'name': 'World Bank',        'url': 'https://api.worldbank.org',   'category': 'Government','auth': 'no','free': True},
    ]
    print(f'[api-harvest] {len(known_good)} known-good baseline APIs')
    return known_good

# ── Score APIs by mission relevance ──────────────────────────────────────
def score_api(api):
    score = 0
    text = (api.get('name','') + ' ' + api.get('description','') + ' ' + api.get('category','')).lower()
    
    for kw in MISSION_KEYWORDS:
        if kw in text: score += 2
    
    if api.get('free'): score += 3
    if api.get('auth','').lower() == 'no': score += 2  # no auth = easiest to use
    if api.get('https'): score += 1
    
    # Boost categories we care most about
    cat = api.get('category', '').lower()
    if any(c.lower() in cat for c in ['crypto', 'government', 'science', 'environment', 'humanitarian']):
        score += 4
    
    return score

# ── Main ──────────────────────────────────────────────────────────────────
def run():
    print(f'[api-harvest] Discovering free APIs — {TODAY}')
    
    all_apis = []
    
    # Source 1: GitHub master list
    github_apis = harvest_public_apis_github()
    all_apis.extend(github_apis)
    
    # Source 2: Known good baseline
    baseline = harvest_mixed_analytics_list()
    
    # Merge (deduplicate by name)
    existing_names = {a['name'].lower() for a in all_apis}
    for api in baseline:
        if api['name'].lower() not in existing_names:
            all_apis.append(api)
            existing_names.add(api['name'].lower())
    
    print(f'[api-harvest] Total unique APIs: {len(all_apis)}')
    
    # Score by mission relevance
    for api in all_apis:
        api['mission_score'] = score_api(api)
    
    # Top opportunities
    top = sorted(all_apis, key=lambda a: a['mission_score'], reverse=True)[:50]
    free_noauth = [a for a in all_apis if a.get('auth','').lower() == 'no' and a.get('free', True)]
    
    print(f'[api-harvest] {len(free_noauth)} APIs require zero auth (instant use)')
    
    # Save full catalog
    catalog = {
        'date':        TODAY,
        'total':       len(all_apis),
        'free_noauth': len(free_noauth),
        'top_50':      top,
        'all':         all_apis,
    }
    (KB / 'apis' / f'{TODAY}.json').write_text(json.dumps(catalog, indent=2))
    (KB / 'apis' / 'latest.json').write_text(json.dumps(catalog, indent=2))
    
    # Save opportunities doc
    opp = {
        'date':    TODAY,
        'top_mission_apis': top[:20],
        'free_noauth_count': len(free_noauth),
        'categories': list({a.get('category','?') for a in all_apis}),
    }
    (DATA / 'api_opportunities.json').write_text(json.dumps(opp, indent=2))
    
    # Build readable digest
    lines = [f'# Free API Discoveries — {TODAY}', '', f'Total found: {len(all_apis)} | Zero-auth: {len(free_noauth)}', '', '## Top APIs for Meeko\'s Mission', '']
    for a in top[:15]:
        auth_note = '🔓 No auth' if a.get('auth','').lower() == 'no' else f'🔑 {a.get("auth","?")}'
        lines.append(f"### {a['name']} ({a.get('category','?')})")
        lines.append(f"{a.get('description','')[:120]}")
        lines.append(f"{auth_note} | Score: {a['mission_score']} | {a.get('url','')}")
        lines.append('')
    
    digest = '\n'.join(lines)
    (KB / 'apis' / f'{TODAY}_digest.md').write_text(digest)
    (KB / 'apis' / 'LATEST_DIGEST.md').write_text(digest)
    
    print(f'[api-harvest] Done. Top 3 mission APIs:')
    for a in top[:3]:
        print(f"  {a['name']}: {a.get('description','')[:80]}")
    
    return catalog

if __name__ == '__main__':
    run()
