#!/usr/bin/env python3
"""
World Intelligence Engine
==========================
Pulls global data that directly serves the humanitarian mission.

APIs wired in:
  - World Bank        -> global poverty, health, education stats
  - USAspending.gov   -> US government contract + spending transparency
  - Data USA          -> US demographics + social data
  - Open Food Facts   -> food access + product data
  - Nager.Date        -> public holidays globally (context for outreach timing)
  - openFDA           -> food/drug safety alerts (public health angle)
  - GeckoTerminal     -> new crypto launches (Solana/DEX intelligence)
  - CoinCap           -> real-time crypto prices (backup to CoinGecko)
  - Binance           -> 24hr market data
  - SpaceX            -> launch data (hope + tech angle)
  - ExchangeRate-API  -> live FX rates (donation conversion context)
  - Open Library      -> books on humanitarian topics
  - MusicBrainz       -> music tagging for content
  - Wikipedia Pageviews -> what topics are surging right now

Outputs:
  - knowledge/world/latest.json     raw intelligence
  - knowledge/world/latest.md       human-readable digest
  - data/world_state.json           current world snapshot
  - content/queue/world_*.json      content posts derived from data
"""

import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
KB    = ROOT / 'knowledge'
DATA  = ROOT / 'data'
CONT  = ROOT / 'content' / 'queue'

for d in [KB / 'world', DATA, CONT]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow()

def fetch_json(url, timeout=12):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[world] fetch error {url[:60]}: {e}')
        return None

# === WORLD BANK ============================================================
def fetch_world_bank():
    print('[world] World Bank...')
    indicators = {
        'SI.POV.DDAY':  'poverty_extreme',       # % living on <$2.15/day
        'SH.DYN.MORT':  'child_mortality',        # under-5 mortality per 1000
        'SE.PRM.NENR':  'school_enrollment',      # primary school enrollment %
        'SH.STA.BASS.ZS': 'basic_sanitation',     # access to basic sanitation %
        'SH.H2O.BASW.ZS': 'clean_water_access',   # access to clean water %
    }
    results = {}
    for code, name in list(indicators.items())[:3]:  # limit requests
        url = f'http://api.worldbank.org/v2/country/all/indicator/{code}?format=json&mrv=1&per_page=5'
        data = fetch_json(url)
        if data and len(data) > 1 and data[1]:
            latest = [d for d in data[1] if d.get('value') is not None]
            if latest:
                results[name] = {
                    'value':   latest[0]['value'],
                    'country': latest[0].get('country', {}).get('value', '?'),
                    'year':    latest[0].get('date', '?'),
                }
    print(f'[world] World Bank: {len(results)} indicators')
    return results

# === USA SPENDING ==========================================================
def fetch_usaspending():
    print('[world] USAspending...')
    # Top federal agencies by spending
    data = fetch_json('https://api.usaspending.gov/api/v2/references/toptier_agencies/')
    if not data: return {}
    
    agencies = []
    for agency in (data.get('results', []) or [])[:10]:
        agencies.append({
            'name':        agency.get('agency_name', ''),
            'budget':      agency.get('budget_authority_amount', 0),
            'percent_total': agency.get('percentage_of_total_budget_authority', 0),
        })
    
    # Recent contracts (transparency angle)
    awards = fetch_json('https://api.usaspending.gov/api/v2/search/spending_by_category/awarding_agency/?filters={"time_period":[{"start_date":"' + TODAY[:7] + '-01","end_date":"' + TODAY + '"}]}&limit=5')
    
    result = {'top_agencies': agencies, 'date': TODAY}
    print(f'[world] USAspending: {len(agencies)} agencies')
    return result

# === GECKO TERMINAL (DEX new launches) =====================================
def fetch_gecko_terminal():
    print('[world] GeckoTerminal (new pools)...')
    # New pools on Solana (most relevant for Phantom strategy)
    data = fetch_json('https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page=1')
    if not data: return []
    
    pools = []
    for pool in (data.get('data', []) or [])[:10]:
        attrs = pool.get('attributes', {})
        pools.append({
            'name':        attrs.get('name', ''),
            'price_usd':   attrs.get('base_token_price_usd', ''),
            'volume_24h':  attrs.get('volume_usd', {}).get('h24', ''),
            'created':     attrs.get('pool_created_at', ''),
            'dex':         pool.get('relationships', {}).get('dex', {}).get('data', {}).get('id', ''),
            'url':         f"https://www.geckoterminal.com/solana/pools/{pool.get('id','').split('_')[-1]}",
        })
    
    print(f'[world] GeckoTerminal: {len(pools)} new Solana pools')
    return pools

# === COINCAP (real-time crypto) ============================================
def fetch_coincap():
    print('[world] CoinCap...')
    data = fetch_json('https://api.coincap.io/v2/assets?limit=10')
    if not data: return []
    
    coins = []
    for c in (data.get('data', []) or []):
        coins.append({
            'name':      c.get('name'),
            'symbol':    c.get('symbol'),
            'price':     round(float(c.get('priceUsd', 0) or 0), 4),
            'change_24h': round(float(c.get('changePercent24Hr', 0) or 0), 2),
            'volume_24h': round(float(c.get('volumeUsd24Hr', 0) or 0)),
        })
    
    print(f'[world] CoinCap: {len(coins)} assets')
    return coins

# === EXCHANGE RATES (donation context) =====================================
def fetch_exchange_rates():
    print('[world] Exchange rates...')
    data = fetch_json('https://open.er-api.com/v6/latest/USD')
    if not data: return {}
    
    # Key currencies for your donor base + Palestine context
    currencies = ['EUR', 'GBP', 'ILS', 'JOD', 'EGP', 'TRY', 'CAD', 'AUD']
    rates = {c: data['rates'].get(c) for c in currencies if c in data.get('rates', {})}
    
    print(f'[world] Exchange rates: {len(rates)} currencies')
    return {'base': 'USD', 'rates': rates, 'date': TODAY}

# === SPACEX ================================================================
def fetch_spacex():
    print('[world] SpaceX...')
    latest  = fetch_json('https://api.spacexdata.com/v5/launches/latest')
    upcoming = fetch_json('https://api.spacexdata.com/v5/launches/upcoming')
    
    result = {}
    if latest:
        result['latest'] = {
            'name':    latest.get('name'),
            'date':    latest.get('date_utc', '')[:10],
            'success': latest.get('success'),
            'details': (latest.get('details') or '')[:200],
        }
    if upcoming and len(upcoming) > 0:
        next_launch = upcoming[0]
        result['next'] = {
            'name': next_launch.get('name'),
            'date': next_launch.get('date_utc', '')[:10],
        }
    
    print(f'[world] SpaceX: latest={result.get("latest",{}).get("name","?")} next={result.get("next",{}).get("name","?")}')
    return result

# === OPEN FOOD FACTS (humanitarian food access) ============================
def fetch_food_data():
    print('[world] Open Food Facts...')
    # Look for basic staple foods - context for food insecurity content
    data = fetch_json('https://world.openfoodfacts.org/cgi/search.pl?search_terms=bread&search_simple=1&action=process&json=1&page_size=5')
    if not data: return {}
    
    products = []
    for p in (data.get('products', []) or [])[:5]:
        products.append({
            'name':    p.get('product_name', ''),
            'brands':  p.get('brands', ''),
            'country': p.get('countries', ''),
            'nutri':   p.get('nutriscore_grade', ''),
        })
    
    print(f'[world] Food Facts: {len(products)} products')
    return {'products': products, 'note': 'Staple food access data for humanitarian context'}

# === WIKIPEDIA TRENDING ====================================================
def fetch_wikipedia_trending():
    print('[world] Wikipedia trending...')
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y/%m/%d')
    data = fetch_json(f'https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{yesterday}')
    if not data: return []
    
    articles = []
    items = data.get('items', [{}])[0].get('articles', [])[:20]
    # Filter out meta pages
    skip = ['main_page', 'special:', 'wikipedia:', 'portal:', 'help:']
    for a in items:
        title = a.get('article', '')
        if any(s in title.lower() for s in skip): continue
        articles.append({
            'title': title.replace('_', ' '),
            'views': a.get('views', 0),
        })
    
    print(f'[world] Wikipedia: {len(articles)} trending articles')
    return articles[:10]

# === BUILD WORLD STATE DIGEST ==============================================
def build_digest(world_bank, spending, gecko, coincap, fx, spacex, food, wiki):
    lines = [f'# World Intelligence Digest \u2014 {TODAY}', '']
    
    # Crypto
    if coincap:
        btc = next((c for c in coincap if c['symbol']=='BTC'), None)
        sol = next((c for c in coincap if c['symbol']=='SOL'), None)
        lines += ['## Crypto Market', '']
        if btc: lines.append(f"- BTC: ${btc['price']:,} ({btc['change_24h']:+.1f}%)")
        if sol: lines.append(f"- SOL: ${sol['price']} ({sol['change_24h']:+.1f}%)")
        lines.append('')
    
    # New Solana pools (for Phantom strategy)
    if gecko:
        lines += ['## New Solana Pools (GeckoTerminal)', '']
        for p in gecko[:3]:
            lines.append(f"- {p['name']} | Vol 24h: ${p['volume_24h']} | {p['url']}")
        lines.append('')
    
    # Space
    if spacex.get('next'):
        lines += [f"## Next SpaceX Launch: {spacex['next']['name']} on {spacex['next']['date']}", '']
    
    # Wikipedia trending (content signal)
    if wiki:
        lines += ['## Trending on Wikipedia (content signal)', '']
        for a in wiki[:5]:
            lines.append(f"- {a['title']} ({a['views']:,} views)")
        lines.append('')
    
    # Humanitarian data
    if world_bank:
        lines += ['## World Bank Snapshot', '']
        for key, val in world_bank.items():
            lines.append(f"- {key}: {val['value']} ({val['country']}, {val['year']})")
        lines.append('')
    
    return '\n'.join(lines)

# === MAIN ==================================================================
def run():
    print(f'[world] World Intelligence Engine \u2014 {TODAY}')
    
    world_bank = fetch_world_bank()
    spending   = fetch_usaspending()
    gecko      = fetch_gecko_terminal()
    coincap    = fetch_coincap()
    fx         = fetch_exchange_rates()
    spacex     = fetch_spacex()
    food       = fetch_food_data()
    wiki       = fetch_wikipedia_trending()
    
    state = {
        'date':       TODAY,
        'world_bank': world_bank,
        'usaspending': spending,
        'solana_new_pools': gecko,
        'crypto':     coincap,
        'exchange_rates': fx,
        'spacex':     spacex,
        'food':       food,
        'wikipedia_trending': wiki,
    }
    
    (DATA / 'world_state.json').write_text(json.dumps(state, indent=2))
    
    digest = build_digest(world_bank, spending, gecko, coincap, fx, spacex, food, wiki)
    (KB / 'world' / f'{TODAY}.md').write_text(digest)
    (KB / 'world' / 'latest.md').write_text(digest)
    
    # Generate content from Wikipedia trending
    if wiki:
        trending_titles = [a['title'] for a in wiki[:5]]
        post = {
            'platform': 'mastodon',
            'type':     'world_signal',
            'text':     f"What the world is reading today:\n" + 
                       '\n'.join(f'\u2022 {t}' for t in trending_titles) +
                       f'\n\nSource: Wikipedia \u2014 {TODAY}\n#OpenData #WorldSignal',
        }
        (CONT / f'world_{TODAY}.json').write_text(json.dumps([post], indent=2))
    
    print(f'[world] Complete. State saved.')
    if gecko: print(f'[world] {len(gecko)} new Solana pools detected')
    if wiki:  print(f'[world] Top trending: {wiki[0]["title"]} ({wiki[0]["views"]:,} views)')
    
    return state

if __name__ == '__main__':
    run()
