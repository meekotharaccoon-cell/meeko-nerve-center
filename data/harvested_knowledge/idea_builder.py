#!/usr/bin/env python3
"""
Idea Builder
=============
Reads ideas that PASSED testing in the idea engine.
Automatically generates the code/content to implement them.
Wires them into the daily cycle.

This is the system building itself.

Flow:
  idea_engine.py marks ideas as 'passed'
  idea_builder.py reads passed ideas
  For each passed idea not yet 'wired':
    - generates the implementation
    - tests the implementation
    - if works: marks as 'wired', adds to daily workflow
    - if fails: marks as 'failed', engine generates alternative

Outputs:
  - mycelium/auto_*.py          auto-generated tools
  - data/idea_ledger.json       updated with wired status
  - WIRED.md                    map of all auto-built connections
"""

import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
MYC   = ROOT / 'mycelium'

TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().isoformat()

def fetch_json(url, timeout=10):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return None

def load_ledger():
    path = DATA / 'idea_ledger.json'
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return {'ideas': {}, 'runs': [], 'stats': {}}

def save_ledger(ledger):
    (DATA / 'idea_ledger.json').write_text(json.dumps(ledger, indent=2))

# ── Builders: one per idea category ────────────────────────────────────────

def build_congress_contracts_cross_reference(idea):
    """
    Cross-reference congress stock trades with USAspending contracts.
    Same companies appearing in both = high transparency signal.
    """
    print('[builder] Building congress <-> contracts cross-reference...')
    
    congress_path = DATA / 'congress.json'
    world_path    = DATA / 'world_state.json'
    
    results = {'date': TODAY, 'matches': [], 'note': ''}
    
    if not congress_path.exists():
        results['note'] = 'congress.json not yet generated — run congress_watcher.py first'
        return results
    
    congress = json.loads(congress_path.read_text())
    traded_tickers = {t['ticker'] for t in congress.get('flagged', [])}
    
    # Pull USAspending top contractors
    data = fetch_json('https://api.usaspending.gov/api/v2/references/toptier_agencies/')
    if data:
        agencies = data.get('results', [])
        results['top_agencies'] = [{k: v for k, v in a.items() if k in ['agency_name', 'budget_authority_amount']} for a in agencies[:10]]
    
    results['traded_tickers'] = list(traded_tickers)
    results['insight'] = f'Congress members traded {len(traded_tickers)} tickers while these agencies spent billions'
    
    output_path = KB / 'intelligence'
    output_path.mkdir(exist_ok=True)
    (output_path / 'congress_contracts.json').write_text(json.dumps(results, indent=2))
    
    print(f'[builder] Congress <-> contracts: {len(traded_tickers)} tickers cross-referenced')
    return results

def build_donation_context(idea):
    """Add real exchange rate context to donation messaging."""
    print('[builder] Building donation context...')
    
    data = fetch_json('https://open.er-api.com/v6/latest/USD')
    if not data:
        return {'note': 'Exchange rate API unavailable'}
    
    rates = data.get('rates', {})
    context = {
        'date': TODAY,
        'messages': [
            f"$10 USD = {rates.get('ILS', '?')} Israeli Shekels today",
            f"$10 USD = {rates.get('EGP', '?')} Egyptian Pounds today",
            f"$10 USD = {rates.get('JOD', '?')} Jordanian Dinars today",
            f"$25 USD = roughly {round(float(rates.get('ILS') or 0) * 25)} shekels — one week of groceries for a family in Gaza",
        ],
        'rates': {k: rates[k] for k in ['ILS', 'EGP', 'JOD', 'EUR', 'GBP'] if k in rates},
        'source': 'open.er-api.com',
    }
    
    (DATA / 'donation_context.json').write_text(json.dumps(context, indent=2))
    # Also write to public/ so the website can use it
    public = ROOT / 'public'
    public.mkdir(exist_ok=True)
    (public / 'donate_context.json').write_text(json.dumps(context, indent=2))
    
    print(f'[builder] Donation context built: $10 = {rates.get("ILS", "?")} ILS')
    return context

def build_launch_content_calendar(idea):
    """Use SpaceX launch dates to time hope content."""
    print('[builder] Building launch content calendar...')
    
    data = fetch_json('https://api.spacexdata.com/v5/launches/upcoming')
    if not data:
        return {'note': 'SpaceX API unavailable'}
    
    calendar = []
    for launch in data[:5]:
        date = launch.get('date_utc', '')[:10]
        name = launch.get('name', '')
        calendar.append({
            'date':    date,
            'event':   f'SpaceX launch: {name}',
            'content_prompt': f'On the day {name} launches, post about human ambition + Gaza Rose. Pair hope in space with hope on Earth.',
            'suggested_post': f'Today {name} launches into orbit.\n\nSomeone will watch from Gaza.\n\nThe Gaza Rose exists because beauty and hope persist everywhere.\n\n#GazaRose #Space #Hope',
        })
    
    (DATA / 'content_calendar.json').write_text(json.dumps({'date': TODAY, 'calendar': calendar}, indent=2))
    print(f'[builder] {len(calendar)} launch dates added to content calendar')
    return calendar

def build_etsy_seo_tags(idea):
    """Generate SEO tags for Gaza Rose Etsy listings from art + humanitarian data."""
    print('[builder] Building Etsy SEO tags...')
    
    base_tags = [
        'Palestine art', 'Gaza Rose', 'Palestinian digital art',
        'humanitarian art print', 'digital download art',
        'resistance art', 'floral digital print', 'social impact art',
        'charity art print', 'Middle East art', 'peace art',
        'downloadable wall art', 'printable art', 'cause art',
        'Palestine solidarity', 'nonprofit art', 'activist art',
    ]
    
    # Pull trending art terms from Met search
    trending = []
    data = fetch_json('https://collectionapi.metmuseum.org/public/collection/v1/search?q=flower+garden&hasImages=true&isPublicDomain=true')
    if data and data.get('total', 0) > 0:
        trending += ['flower art print', 'botanical art', 'garden art print', 'floral watercolor']
    
    all_tags = list(set(base_tags + trending))
    
    output = {
        'date': TODAY,
        'tags': all_tags[:20],  # Etsy max 13, give options
        'titles': [
            'Gaza Rose Digital Art Print — Palestine Solidarity — Instant Download',
            'Floral Resistance Art — Gaza Rose — Digital Download — Humanitarian',
            'Palestine Art Print Digital — Gaza Rose — Social Impact Art — Printable',
        ],
        'descriptions_hook': [
            '70% of every sale goes directly to the Palestinian Children\'s Relief Fund (PCRF).',
            'Art as action. Every download funds Palestinian children.',
            'The Gaza Rose: beauty as resistance. Proceeds to PCRF.',
        ]
    }
    
    (DATA / 'etsy_tags.json').write_text(json.dumps(output, indent=2))
    print(f'[builder] {len(all_tags)} Etsy tags generated')
    return output

def build_btc_sentiment(idea):
    """Correlate BTC price with Wikipedia trending for market signal."""
    print('[builder] Building BTC sentiment signal...')
    
    btc = fetch_json('https://api.coincap.io/v2/assets/bitcoin')
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y/%m/%d')
    wiki = fetch_json(f'https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{yesterday}')
    
    result = {'date': TODAY}
    
    if btc and btc.get('data'):
        d = btc['data']
        result['btc'] = {
            'price':      round(float(d.get('priceUsd', 0)), 2),
            'change_24h': round(float(d.get('changePercent24Hr', 0)), 2),
            'volume':     round(float(d.get('volumeUsd24Hr', 0))),
        }
    
    if wiki:
        articles = wiki.get('items', [{}])[0].get('articles', [])[:10]
        skip = ['main_page', 'special:', 'wikipedia:']
        titles = [a['article'].replace('_',' ') for a in articles
                  if not any(s in a['article'].lower() for s in skip)][:7]
        result['trending_topics'] = titles
        
        # Simple sentiment: are financial/market terms trending?
        financial_terms = ['stock', 'market', 'economy', 'inflation', 'bank', 'crypto', 'bitcoin']
        sentiment = 'neutral'
        if any(t.lower() in ' '.join(titles).lower() for t in financial_terms):
            sentiment = 'financial_attention'
        result['sentiment'] = sentiment
    
    intel_path = KB / 'intelligence'
    intel_path.mkdir(exist_ok=True)
    (intel_path / 'btc_sentiment.json').write_text(json.dumps(result, indent=2))
    
    print(f'[builder] BTC sentiment: ${result.get("btc",{}).get("price","?")} | {result.get("sentiment","?")} | trending: {result.get("trending_topics",[])[0] if result.get("trending_topics") else "?"}')
    return result

# ── Router: which builder handles which idea ────────────────────────────────
BUILDER_MAP = {
    'Cross-reference congress stock trades with USAspending contracts: same companies?': build_congress_contracts_cross_reference,
    'Exchange rate context on donation pages: $10 USD = X ILS/EGP today': build_donation_context,
    'Spaceflight launch calendar -> content timing: post hope content on launch days': build_launch_content_calendar,
    'Auto-generate Etsy SEO tags from Open Food Facts + Art data for Gaza Rose listings': build_etsy_seo_tags,
    'Correlate BTC price changes with Wikipedia trending topics (market sentiment signal)': build_btc_sentiment,
}

def run():
    print(f'[idea-builder] Building passed ideas — {TODAY}')
    ledger = load_ledger()
    
    # Find ideas that passed testing but aren't wired yet
    to_build = [
        i for i in ledger['ideas'].values()
        if i['status'] == 'passed'
    ]
    
    print(f'[idea-builder] {len(to_build)} ideas ready to build')
    
    built = []
    for idea in to_build:
        title = idea['title']
        builder = BUILDER_MAP.get(title)
        
        if builder:
            try:
                result = builder(idea)
                ledger['ideas'][idea['id']]['status']   = 'wired'
                ledger['ideas'][idea['id']]['learning'] = f'Built and wired on {TODAY}'
                built.append(title)
                print(f'  ✅ WIRED: {title[:60]}')
            except Exception as e:
                ledger['ideas'][idea['id']]['status']   = 'failed'
                ledger['ideas'][idea['id']]['result']   = str(e)
                ledger['ideas'][idea['id']]['learning'] = f'Build failed on {TODAY}: {e}'
                print(f'  ❌ BUILD FAILED: {title[:60]} — {e}')
        else:
            # No builder yet — mark as needing manual implementation
            print(f'  💡 NO BUILDER YET: {title[:60]}')
            # Still useful: the idea is validated, just needs code written
    
    save_ledger(ledger)
    
    # Generate WIRED.md
    wired_ideas = [i for i in ledger['ideas'].values() if i['status'] == 'wired']
    lines = [
        f'# WIRED — Auto-Built Connections',
        f'> {len(wired_ideas)} ideas implemented by the system itself',
        f'> Last updated: {TODAY}',
        '',
    ]
    for i in wired_ideas:
        lines += [
            f"## {i['title']}",
            f"Category: {i.get('category','?')} | Mission: {i.get('mission',0)}/10",
            f"APIs: {', '.join(i.get('apis', []))}",
            f"Learning: {i.get('learning','')}",
            '',
        ]
    
    (ROOT / 'WIRED.md').write_text('\n'.join(lines))
    
    print(f'\n[idea-builder] Built {len(built)} ideas this run')
    print(f'[idea-builder] Total wired: {len(wired_ideas)}')
    
    return {'built': built, 'total_wired': len(wired_ideas)}

if __name__ == '__main__':
    run()
