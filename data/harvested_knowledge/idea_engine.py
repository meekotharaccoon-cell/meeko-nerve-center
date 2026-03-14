#!/usr/bin/env python3
"""
Idea Engine
============
The system generates its own ideas.
Tests them against available APIs and tools.
Learns from success AND failure.
Finds alternatives when something doesn't work.
Only stops at a true hard wall (API says no, logic dead-end).

This is the self-directing brain layer.

Cycle:
  1. OBSERVE    - read current system state, knowledge, results
  2. IDEATE     - generate new connection ideas from what's available
  3. SCORE      - rank ideas by feasibility + mission impact
  4. TEST       - attempt the highest-scored untested idea
  5. EVALUATE   - did it work? what did we learn?
  6. ADAPT      - if failed, find alternative. if succeeded, wire it in.
  7. RECORD     - write everything to idea_ledger.json
  8. REPEAT

Outputs:
  - data/idea_ledger.json     all ideas, test results, learnings
  - data/ideas_working.json   ideas that passed testing
  - data/ideas_failed.json    ideas that failed + why + alternatives tried
  - knowledge/ideas/latest.md human-readable idea digest
  - mycelium/IDEAS.md         ideas ready for human review / implementation
"""

import json, datetime, hashlib, traceback
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
MYC   = ROOT / 'mycelium'

for d in [DATA, KB / 'ideas']:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().isoformat()

# ── Idea taxonomy ──────────────────────────────────────────────────────────
# Each idea has:
#   id         - hash of title
#   title      - what it does
#   category   - content | revenue | intelligence | tool | connection
#   apis       - which APIs it needs
#   inputs     - what data/files it reads
#   outputs    - what it produces
#   mission    - how it serves the mission (1-10)
#   feasibility- can we do it with zero-cost tools? (1-10)
#   status     - untested | testing | passed | failed | dead_end | wired
#   result     - what happened when tested
#   learning   - what the system learned
#   alternative- next idea to try if this failed
#   created    - timestamp
#   tested     - timestamp

IDEA_POOL = [
    # ── CONTENT IDEAS ────────────────────────────────────────────────────
    {
        'title': 'Daily "What Congress bought today" post from stock watcher data',
        'category': 'content',
        'apis': ['House Stock Watcher'],
        'inputs': ['data/congress.json'],
        'outputs': ['content/queue/congress_daily.json'],
        'mission': 9,
        'feasibility': 9,
        'test': 'check_file_exists',
        'test_target': 'data/congress.json',
        'alternative': 'Use USAspending.gov contracts instead',
    },
    {
        'title': 'Pair USGS earthquake data with Red Cross / UN OCHA aid response links',
        'category': 'content',
        'apis': ['USGS Earthquakes', 'Red Cross (web)'],
        'inputs': ['knowledge/usgs/'],
        'outputs': ['content/queue/disaster_aid.json'],
        'mission': 10,
        'feasibility': 8,
        'test': 'check_file_exists',
        'test_target': 'knowledge/usgs/',
        'alternative': 'Use Wikipedia recent disasters page',
    },
    {
        'title': 'Auto-generate weekly carbon report from UK grid data with SolarPunk framing',
        'category': 'content',
        'apis': ['Carbon Intensity API'],
        'inputs': ['knowledge/carbon/'],
        'outputs': ['content/queue/carbon_weekly.json'],
        'mission': 8,
        'feasibility': 9,
        'test': 'fetch_url',
        'test_target': 'https://api.carbonintensity.org.uk/intensity',
        'alternative': 'Use ElectricityMap API (free tier)',
    },
    {
        'title': 'Wikipedia pageview spikes -> identify trending topics -> generate timely content',
        'category': 'content',
        'apis': ['Wikipedia Pageviews'],
        'inputs': ['knowledge/world/latest.md'],
        'outputs': ['content/queue/trending_today.json'],
        'mission': 7,
        'feasibility': 10,
        'test': 'fetch_url',
        'test_target': 'https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/2026/02/25',
        'alternative': 'Use Reddit hot posts as trending signal',
    },
    {
        'title': 'Museum art + earthquake location pairing: art from affected region + aid link',
        'category': 'content',
        'apis': ['USGS', 'Metropolitan Museum', 'ARTIC'],
        'inputs': ['knowledge/usgs/', 'data/art_pairs.json'],
        'outputs': ['content/queue/art_disaster.json'],
        'mission': 10,
        'feasibility': 7,
        'test': 'check_file_exists',
        'test_target': 'data/art_pairs.json',
        'alternative': 'Use Wikimedia Commons free images instead',
    },
    {
        'title': 'ISS crew + space news -> weekly hope post (humans doing amazing things)',
        'category': 'content',
        'apis': ['Open Notify', 'Spaceflight News'],
        'inputs': ['knowledge/spaceflight/'],
        'outputs': ['content/queue/hope_weekly.json'],
        'mission': 7,
        'feasibility': 10,
        'test': 'fetch_url',
        'test_target': 'http://api.open-notify.org/astros.json',
        'alternative': 'Use NASA APOD (Astronomy Picture of the Day)',
    },
    {
        'title': 'Free book on Palestine available on Archive.org -> amplify it weekly',
        'category': 'content',
        'apis': ['Open Library', 'Internet Archive'],
        'inputs': ['knowledge/books/latest.md'],
        'outputs': ['content/queue/book_amplify.json'],
        'mission': 9,
        'feasibility': 9,
        'test': 'check_file_exists',
        'test_target': 'knowledge/books/latest.md',
        'alternative': 'Search Project Gutenberg directly',
    },
    {
        'title': 'World Bank child mortality data -> context for Gaza children posts',
        'category': 'content',
        'apis': ['World Bank'],
        'inputs': ['data/world_state.json'],
        'outputs': ['content/queue/child_data.json'],
        'mission': 10,
        'feasibility': 8,
        'test': 'check_file_exists',
        'test_target': 'data/world_state.json',
        'alternative': 'Use UNICEF open data API',
    },

    # ── REVENUE IDEAS ─────────────────────────────────────────────────────
    {
        'title': 'Crypto jobs digest -> weekly newsletter -> Ko-fi membership content',
        'category': 'revenue',
        'apis': ['Jobicy', 'Remotive'],
        'inputs': ['data/jobs_today.json'],
        'outputs': ['content/newsletter/crypto_jobs_weekly.md'],
        'mission': 6,
        'feasibility': 9,
        'test': 'check_file_exists',
        'test_target': 'data/jobs_today.json',
        'alternative': 'Scrape We Work Remotely public page',
    },
    {
        'title': 'GeckoTerminal new Solana pool alerts -> Telegram -> Phantom buy signal',
        'category': 'revenue',
        'apis': ['GeckoTerminal', 'Telegram Bot'],
        'inputs': ['data/world_state.json'],
        'outputs': ['telegram_alert'],
        'mission': 5,
        'feasibility': 8,
        'test': 'fetch_url',
        'test_target': 'https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page=1',
        'alternative': 'Use DEX Screener trending instead',
    },
    {
        'title': 'Exchange rate context on donation pages: $10 USD = X ILS/EGP today',
        'category': 'revenue',
        'apis': ['ExchangeRate-API'],
        'inputs': ['data/world_state.json'],
        'outputs': ['public/donate_context.json'],
        'mission': 8,
        'feasibility': 10,
        'test': 'fetch_url',
        'test_target': 'https://open.er-api.com/v6/latest/USD',
        'alternative': 'Use CoinGecko fiat rates',
    },
    {
        'title': 'Auto-generate Etsy SEO tags from Open Food Facts + Art data for Gaza Rose listings',
        'category': 'revenue',
        'apis': ['Open Food Facts', 'ARTIC', 'Met Museum'],
        'inputs': ['data/art_pairs.json'],
        'outputs': ['data/etsy_tags.json'],
        'mission': 7,
        'feasibility': 8,
        'test': 'check_file_exists',
        'test_target': 'data/art_pairs.json',
        'alternative': 'Generate tags from humanitarian_content.py keywords',
    },

    # ── INTELLIGENCE IDEAS ────────────────────────────────────────────────
    {
        'title': 'Cross-reference congress stock trades with USAspending contracts: same companies?',
        'category': 'intelligence',
        'apis': ['House Stock Watcher', 'USAspending'],
        'inputs': ['data/congress.json', 'data/world_state.json'],
        'outputs': ['knowledge/intelligence/congress_contracts.json'],
        'mission': 10,
        'feasibility': 7,
        'test': 'check_file_exists',
        'test_target': 'data/congress.json',
        'alternative': 'Use OpenSecrets data (web scrape)',
    },
    {
        'title': 'Correlate BTC price changes with Wikipedia trending topics (market sentiment signal)',
        'category': 'intelligence',
        'apis': ['CoinCap', 'Wikipedia Pageviews'],
        'inputs': ['data/world_state.json', 'knowledge/crypto/'],
        'outputs': ['knowledge/intelligence/btc_sentiment.json'],
        'mission': 5,
        'feasibility': 8,
        'test': 'fetch_url',
        'test_target': 'https://api.coincap.io/v2/assets/bitcoin',
        'alternative': 'Use Reddit r/bitcoin sentiment instead',
    },
    {
        'title': 'Spaceflight launch calendar -> content timing: post hope content on launch days',
        'category': 'intelligence',
        'apis': ['SpaceX', 'Spaceflight News'],
        'inputs': ['data/world_state.json'],
        'outputs': ['data/content_calendar.json'],
        'mission': 7,
        'feasibility': 9,
        'test': 'fetch_url',
        'test_target': 'https://api.spacexdata.com/v5/launches/upcoming',
        'alternative': 'Use NASA launch schedule page',
    },
    {
        'title': 'arXiv AI papers -> extract tools/methods -> update system capabilities weekly',
        'category': 'intelligence',
        'apis': ['arXiv'],
        'inputs': ['knowledge/arxiv/latest.md'],
        'outputs': ['knowledge/intelligence/ai_capabilities.md'],
        'mission': 7,
        'feasibility': 9,
        'test': 'check_file_exists',
        'test_target': 'knowledge/arxiv/latest.md',
        'alternative': 'Use HuggingFace papers page',
    },

    # ── CONNECTION IDEAS ──────────────────────────────────────────────────
    {
        'title': 'Music + earthquake: surface protest songs from affected country after quake',
        'category': 'connection',
        'apis': ['USGS', 'MusicBrainz'],
        'inputs': ['knowledge/usgs/', 'data/music.json'],
        'outputs': ['content/queue/music_solidarity.json'],
        'mission': 9,
        'feasibility': 7,
        'test': 'check_file_exists',
        'test_target': 'data/music.json',
        'alternative': 'Use iTunes Search for country-specific music',
    },
    {
        'title': 'Free book + museum art from same region + cause message = rich cultural post',
        'category': 'connection',
        'apis': ['Open Library', 'Met Museum', 'ARTIC'],
        'inputs': ['knowledge/books/latest.md', 'data/art_pairs.json'],
        'outputs': ['content/queue/culture_cause.json'],
        'mission': 9,
        'feasibility': 8,
        'test': 'check_file_exists',
        'test_target': 'knowledge/books/latest.md',
        'alternative': 'Use Wikimedia Commons + Project Gutenberg',
    },
    {
        'title': 'Remote job in NGO/nonprofit -> pair with Gaza Rose donation ask -> post together',
        'category': 'connection',
        'apis': ['Jobicy', 'Remotive'],
        'inputs': ['data/jobs_today.json'],
        'outputs': ['content/queue/job_plus_cause.json'],
        'mission': 8,
        'feasibility': 9,
        'test': 'check_file_exists',
        'test_target': 'data/jobs_today.json',
        'alternative': 'Source NGO jobs from Idealist (web)',
    },
]

def make_id(title):
    return hashlib.md5(title.encode()).hexdigest()[:12]

def load_ledger():
    path = DATA / 'idea_ledger.json'
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return {'ideas': {}, 'runs': [], 'stats': {'tested': 0, 'passed': 0, 'failed': 0, 'dead_ends': 0}}

def save_ledger(ledger):
    (DATA / 'idea_ledger.json').write_text(json.dumps(ledger, indent=2))
    # Split into working / failed for easy reading
    ideas = list(ledger['ideas'].values())
    working  = [i for i in ideas if i['status'] in ('passed', 'wired')]
    failed   = [i for i in ideas if i['status'] in ('failed', 'dead_end')]
    untested = [i for i in ideas if i['status'] == 'untested']
    (DATA / 'ideas_working.json').write_text(json.dumps(working, indent=2))
    (DATA / 'ideas_failed.json').write_text(json.dumps(failed, indent=2))

def test_fetch_url(url):
    """Test: can we actually reach this API?"""
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=10) as r:
            data = r.read(512)  # just enough to confirm it responds
            return True, f'HTTP {r.status} — {len(data)} bytes'
    except Exception as e:
        return False, str(e)

def test_check_file(path_str):
    """Test: does the required input file/folder exist?"""
    p = ROOT / path_str
    if p.exists():
        if p.is_dir():
            files = list(p.iterdir())
            return True, f'Directory exists with {len(files)} files'
        else:
            size = p.stat().st_size
            return True, f'File exists ({size} bytes)'
    return False, f'Not found: {p}'

def run_test(idea):
    """Run the appropriate test for an idea."""
    test_type   = idea.get('test', 'check_file_exists')
    test_target = idea.get('test_target', '')
    
    if test_type == 'fetch_url':
        return test_fetch_url(test_target)
    elif test_type == 'check_file_exists':
        return test_check_file(test_target)
    else:
        return False, f'Unknown test type: {test_type}'

def build_ideas_md(ledger):
    """Human-readable summary of all ideas and their status."""
    ideas = list(ledger['ideas'].values())
    stats = ledger['stats']
    
    lines = [
        f'# Idea Engine Ledger — {TODAY}',
        f'',
        f'Total: {len(ideas)} | Tested: {stats["tested"]} | Passed: {stats["passed"]} | Failed: {stats["failed"]} | Dead ends: {stats["dead_ends"]}',
        f'',
    ]
    
    status_emoji = {'passed': '✅', 'wired': '🔌', 'failed': '❌', 'dead_end': '🧱', 'untested': '💡', 'testing': '🔬'}
    
    for cat in ['content', 'revenue', 'intelligence', 'connection', 'tool']:
        cat_ideas = [i for i in ideas if i.get('category') == cat]
        if not cat_ideas: continue
        lines += [f'## {cat.upper()}', '']
        for idea in sorted(cat_ideas, key=lambda x: x.get('mission', 0), reverse=True):
            emoji = status_emoji.get(idea['status'], '?')
            lines.append(f"{emoji} **{idea['title']}**")
            lines.append(f"   Mission: {idea.get('mission',0)}/10 | Feasibility: {idea.get('feasibility',0)}/10 | APIs: {', '.join(idea.get('apis',[]))}")
            if idea.get('result'):
                lines.append(f"   Result: {idea['result']}")
            if idea.get('learning'):
                lines.append(f"   Learning: {idea['learning']}")
            if idea.get('alternative') and idea['status'] in ('failed', 'dead_end'):
                lines.append(f"   Next try: {idea['alternative']}")
            lines.append('')
    
    return '\n'.join(lines)

def run(max_tests=10):
    print(f'[idea-engine] Starting idea cycle — {TODAY}')
    ledger = load_ledger()
    
    # Register all ideas from pool
    for raw_idea in IDEA_POOL:
        iid = make_id(raw_idea['title'])
        if iid not in ledger['ideas']:
            ledger['ideas'][iid] = {
                **raw_idea,
                'id':      iid,
                'status':  'untested',
                'result':  None,
                'learning': None,
                'created': NOW,
                'tested':  None,
            }
    
    # Find untested ideas, sorted by mission * feasibility score
    untested = [
        i for i in ledger['ideas'].values()
        if i['status'] == 'untested'
    ]
    untested.sort(key=lambda i: i.get('mission',0) * i.get('feasibility',0), reverse=True)
    
    print(f'[idea-engine] {len(untested)} untested ideas, testing top {min(max_tests, len(untested))}')
    
    passed_this_run = []
    failed_this_run = []
    
    for idea in untested[:max_tests]:
        iid = idea['id']
        print(f'[idea-engine] Testing: {idea["title"][:70]}...')
        
        ledger['ideas'][iid]['status'] = 'testing'
        ledger['ideas'][iid]['tested'] = NOW
        
        success, result = run_test(idea)
        
        if success:
            ledger['ideas'][iid]['status']   = 'passed'
            ledger['ideas'][iid]['result']    = result
            ledger['ideas'][iid]['learning']  = f'Confirmed viable on {TODAY}. Ready to wire into daily cycle.'
            ledger['stats']['passed'] += 1
            passed_this_run.append(idea['title'])
            print(f'  ✅ PASSED: {result}')
        else:
            # Check if there's an alternative to try
            alt = idea.get('alternative')
            if alt:
                ledger['ideas'][iid]['status']   = 'failed'
                ledger['ideas'][iid]['result']    = result
                ledger['ideas'][iid]['learning']  = f'Failed on {TODAY}: {result}. Alternative queued: {alt}'
                
                # Auto-register the alternative as a new idea
                alt_id = make_id(alt)
                if alt_id not in ledger['ideas']:
                    ledger['ideas'][alt_id] = {
                        'id':          alt_id,
                        'title':       alt,
                        'category':    idea['category'],
                        'apis':        [],
                        'inputs':      idea.get('outputs', []),
                        'outputs':     [],
                        'mission':     idea.get('mission', 5),
                        'feasibility': max(1, idea.get('feasibility', 5) - 1),
                        'status':      'untested',
                        'result':      None,
                        'learning':    f'Auto-generated alternative to: {idea["title"]}',
                        'test':        'fetch_url' if 'http' in alt.lower() else 'check_file_exists',
                        'test_target': '',
                        'alternative': None,
                        'created':     NOW,
                        'tested':      None,
                    }
                    print(f'  ↳ Alternative registered: {alt}')
                
                ledger['stats']['failed'] += 1
                failed_this_run.append(idea['title'])
                print(f'  ❌ FAILED: {result}')
            else:
                ledger['ideas'][iid]['status']   = 'dead_end'
                ledger['ideas'][iid]['result']    = result
                ledger['ideas'][iid]['learning']  = f'Dead end on {TODAY}. No alternative available.'
                ledger['stats']['dead_ends'] += 1
                failed_this_run.append(idea['title'])
                print(f'  🧱 DEAD END: {result}')
        
        ledger['stats']['tested'] += 1
    
    # Record this run
    ledger['runs'].append({
        'date':    TODAY,
        'tested':  len(passed_this_run) + len(failed_this_run),
        'passed':  len(passed_this_run),
        'failed':  len(failed_this_run),
        'new_alternatives': len(failed_this_run),
    })
    
    # Save everything
    save_ledger(ledger)
    
    # Build human-readable docs
    ideas_md = build_ideas_md(ledger)
    (KB / 'ideas' / f'{TODAY}.md').write_text(ideas_md)
    (KB / 'ideas' / 'latest.md').write_text(ideas_md)
    (MYC / 'IDEAS.md').write_text(ideas_md)
    
    # Summary
    total_ideas = len(ledger['ideas'])
    total_passed = ledger['stats']['passed']
    total_untested = len([i for i in ledger['ideas'].values() if i['status'] == 'untested'])
    
    print(f'\n[idea-engine] Run complete:')
    print(f'  Total ideas in ledger: {total_ideas}')
    print(f'  Passed (viable):       {total_passed}')
    print(f'  Still untested:        {total_untested}')
    print(f'  This run passed:       {len(passed_this_run)}')
    print(f'  This run failed:       {len(failed_this_run)}')
    
    if passed_this_run:
        print(f'\n  ✅ VIABLE IDEAS READY TO BUILD:')
        for t in passed_this_run:
            print(f'    - {t}')
    
    if failed_this_run:
        print(f'\n  ❌ FAILED (alternatives queued):')
        for t in failed_this_run:
            print(f'    - {t}')
    
    return ledger

if __name__ == '__main__':
    run()
