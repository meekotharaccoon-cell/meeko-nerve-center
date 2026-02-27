#!/usr/bin/env python3
"""
World Intelligence Engine
==========================
Pulls global data that directly serves the humanitarian mission.
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
        'SI.POV.DDAY':  'poverty_extreme',
        'SH.DYN.MORT':  'child_mortality',
        'SE.PRM.NENR':  'school_enrollment',
    }
    results = {}
    for code, name in list(indicators.items())[:3]:
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
    data = fetch_json('https://api.usaspending.gov/api/v2/references/toptier_agencies/')
    if not data: return {}
    agencies = []
    for agency in (data.get('results', []) or [])[:10]:
        agencies.append({
            'name':          agency.get('agency_name', ''),
            'budget':        agency.get('budget_authority_amount', 0),
            'percent_total': agency.get('percentage_of_total_budget_authority', 0),
        })
    result = {'top_agencies': agencies, 'date': TODAY}
    print(f'[world] USAspending: {len(agencies)} agencies')
    return result

# === GECKO TERMINAL ========================================================
def fetch_gecko_terminal():
    print('[world] GeckoTerminal (new pools)...')
    data = fetch_json('https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page=1')
    if not data: return []
    pools = []
    for pool in (data.get('data', []) or [])[:10]:
        attrs = pool.get('attributes', {})
        pools.append({
            'name':       attrs.get('name', ''),
            'price_usd':  attrs.get('base_token_price_usd', ''),
            'volume_24h': attrs.get('volume_usd', {}).get('h24', ''),
            'created':    attrs.get('pool_created_at', ''),
            'dex':        pool.get('relationships', {}).get('dex', {}).get('data', {}).get('id', ''),
            'url':        f"https://www.geckoterminal.com/solana/pools/{pool.get('id','').split('_')[-1]}",
        })
    print(f'[world] GeckoTerminal: {len(pools)} new Solana pools')
    return pools

# === CRYPTO PRICES — multiple fallbacks ====================================
def fetch_crypto():
    """
    Try CoinGecko first (most reliable, no auth needed),
    then CoinCap, then Binance spot as last resort.
    Returns a normalised list regardless of source.
    """
    print('[world] Crypto prices...')

    # --- CoinGecko simple price (free, no key) ---
    cg_ids = 'bitcoin,ethereum,solana,binancecoin,ripple,cardano,avalanche-2,polkadot,chainlink,uniswap'
    cg_url = f'https://api.coingecko.com/api/v3/simple/price?ids={cg_ids}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true'
    cg = fetch_json(cg_url)
    if cg and isinstance(cg, dict) and len(cg) > 0:
        symbol_map = {
            'bitcoin':'BTC','ethereum':'ETH','solana':'SOL',
            'binancecoin':'BNB','ripple':'XRP','cardano':'ADA',
            'avalanche-2':'AVAX','polkadot':'DOT','chainlink':'LINK','uniswap':'UNI'
        }
        coins = []
        for coin_id, sym in symbol_map.items():
            if coin_id in cg:
                d = cg[coin_id]
                coins.append({
                    'name':       coin_id.replace('-2','').title(),
                    'symbol':     sym,
                    'price':      round(float(d.get('usd', 0)), 4),
                    'change_24h': round(float(d.get('usd_24h_change', 0)), 2),
                    'volume_24h': round(float(d.get('usd_24h_vol', 0))),
                })
        if coins:
            print(f'[world] CoinGecko: {len(coins)} coins')
            return coins

    # --- CoinCap fallback ---
    print('[world] CoinGecko failed, trying CoinCap...')
    cap = fetch_json('https://api.coincap.io/v2/assets?limit=10')
    if cap and cap.get('data'):
        coins = []
        for c in cap['data']:
            try:
                coins.append({
                    'name':       c.get('name'),
                    'symbol':     c.get('symbol'),
                    'price':      round(float(c.get('priceUsd', 0) or 0), 4),
                    'change_24h': round(float(c.get('changePercent24Hr', 0) or 0), 2),
                    'volume_24h': round(float(c.get('volumeUsd24Hr', 0) or 0)),
                })
            except:
                pass
        if coins:
            print(f'[world] CoinCap: {len(coins)} coins')
            return coins

    # --- Binance spot last resort ---
    print('[world] CoinCap failed, trying Binance...')
    pairs = {'BTCUSDT':'BTC','ETHUSDT':'ETH','SOLUSDT':'SOL','BNBUSDT':'BNB'}
    coins = []
    for pair, sym in pairs.items():
        d = fetch_json(f'https://api.binance.com/api/v3/ticker/24hr?symbol={pair}')
        if d:
            try:
                coins.append({
                    'name':       sym,
                    'symbol':     sym,
                    'price':      round(float(d.get('lastPrice', 0)), 4),
                    'change_24h': round(float(d.get('priceChangePercent', 0)), 2),
                    'volume_24h': round(float(d.get('quoteVolume', 0))),
                })
            except:
                pass
    if coins:
        print(f'[world] Binance: {len(coins)} coins')
    else:
        print('[world] All crypto sources failed — returning empty')
    return coins

# === EXCHANGE RATES ========================================================
def fetch_exchange_rates():
    print('[world] Exchange rates...')
    data = fetch_json('https://open.er-api.com/v6/latest/USD')
    if not data: return {}
    currencies = ['EUR', 'GBP', 'ILS', 'JOD', 'EGP', 'TRY', 'CAD', 'AUD']
    rates = {c: data['rates'].get(c) for c in currencies if c in data.get('rates', {})}
    print(f'[world] Exchange rates: {len(rates)} currencies')
    return {'base': 'USD', 'rates': rates, 'date': TODAY}

# === SPACEX ================================================================
def fetch_spacex():
    print('[world] SpaceX...')
    latest   = fetch_json('https://api.spacexdata.com/v5/launches/latest')
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
        result['next'] = {
            'name': upcoming[0].get('name'),
            'date': upcoming[0].get('date_utc', '')[:10],
        }
    print(f'[world] SpaceX done')
    return result

# === OPEN FOOD FACTS =======================================================
def fetch_food_data():
    print('[world] Open Food Facts...')
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
    return {'products': products}

# === WIKIPEDIA TRENDING — with real content filter =========================
def fetch_wikipedia_trending():
    print('[world] Wikipedia trending...')
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y/%m/%d')
    data = fetch_json(f'https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{yesterday}')
    if not data: return []

    # Patterns that make an article NOT worth surfacing
    SKIP_PREFIXES = ['main_page', 'special:', 'wikipedia:', 'portal:', 'help:', 'file:']
    SKIP_WORDS = [
        'erotic', 'pornograph', 'xxx', 'sexual', 'nude', 'nsfw',
        'sex_work', 'onlyfans', 'adult_film',
    ]
    # Also skip bare domain-extension articles like ".xxx", ".com", ".net" etc.
    import re
    DOMAIN_EXT = re.compile(r'^\.\w{2,6}$')

    articles = []
    items = data.get('items', [{}])[0].get('articles', [])[:50]  # look at top 50 to get 10 good ones
    for a in items:
        raw   = a.get('article', '')
        title = raw.replace('_', ' ')
        lower = raw.lower()

        if any(lower.startswith(s) for s in SKIP_PREFIXES): continue
        if any(w in lower for w in SKIP_WORDS): continue
        if DOMAIN_EXT.match(title): continue  # skip ".xxx", ".org" etc.

        articles.append({'title': title, 'views': a.get('views', 0)})
        if len(articles) >= 10:
            break

    print(f'[world] Wikipedia: {len(articles)} clean trending articles')
    return articles

# === BUILD DIGEST ==========================================================
def build_digest(world_bank, spending, gecko, coincap, fx, spacex, food, wiki):
    lines = [f'# World Intelligence Digest \u2014 {TODAY}', '']
    if coincap:
        btc = next((c for c in coincap if c['symbol']=='BTC'), None)
        sol = next((c for c in coincap if c['symbol']=='SOL'), None)
        lines += ['## Crypto Market', '']
        if btc: lines.append(f"- BTC: ${btc['price']:,} ({btc['change_24h']:+.1f}%)")
        if sol: lines.append(f"- SOL: ${sol['price']} ({sol['change_24h']:+.1f}%)")
        lines.append('')
    if gecko:
        lines += ['## New Solana Pools', '']
        for p in gecko[:3]:
            lines.append(f"- {p['name']} | Vol 24h: ${p['volume_24h']} | {p['url']}")
        lines.append('')
    if spacex.get('next'):
        lines += [f"## Next SpaceX: {spacex['next']['name']} on {spacex['next']['date']}", '']
    if wiki:
        lines += ['## Trending on Wikipedia', '']
        for a in wiki[:5]:
            lines.append(f"- {a['title']} ({a['views']:,} views)")
        lines.append('')
    if world_bank:
        lines += ['## World Bank', '']
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
    coincap    = fetch_crypto()          # <-- multi-source now
    fx         = fetch_exchange_rates()
    spacex     = fetch_spacex()
    food       = fetch_food_data()
    wiki       = fetch_wikipedia_trending()  # <-- filtered now

    state = {
        'date':               TODAY,
        'world_bank':         world_bank,
        'usaspending':        spending,
        'solana_new_pools':   gecko,
        'crypto':             coincap,
        'exchange_rates':     fx,
        'spacex':             spacex,
        'food':               food,
        'wikipedia_trending': wiki,
    }
    (DATA / 'world_state.json').write_text(json.dumps(state, indent=2))

    digest = build_digest(world_bank, spending, gecko, coincap, fx, spacex, food, wiki)
    (KB / 'world' / f'{TODAY}.md').write_text(digest)
    (KB / 'world' / 'latest.md').write_text(digest)

    if wiki:
        post = {
            'platform': 'mastodon',
            'type':     'world_signal',
            'text':     'What the world is reading today:\n' +
                        '\n'.join(f'\u2022 {a["title"]}' for a in wiki[:5]) +
                        f'\n\n#OpenData #WorldSignal',
        }
        (CONT / f'world_{TODAY}.json').write_text(json.dumps([post], indent=2))

    print(f'[world] Complete.')
    if coincap: print(f"[world] BTC: ${next((c['price'] for c in coincap if c['symbol']=='BTC'), 'n/a'):,}")
    if wiki:    print(f"[world] Top trending: {wiki[0]['title']} ({wiki[0]['views']:,} views)")
    return state

if __name__ == '__main__':
    run()
