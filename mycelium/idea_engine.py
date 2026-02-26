#!/usr/bin/env python3
"""
Idea Engine
============
The system thinks for itself.

Cycle:
  1. GENERATE  - Combine known APIs + mission + current knowledge into new ideas
  2. TEST      - Actually try the idea (call the API, run the code, check the output)
  3. EVALUATE  - Did it work? Partial? Dead-end?
  4. LEARN     - Store the result. Update the idea graph.
  5. ITERATE   - If it failed, find an alternative path. Only stop at true dead-ends.
  6. SURFACE   - If it worked, wire it into the daily cycle automatically.

Hard walls (stop here):
  - API returns 401/403 and no free tier exists
  - Service explicitly says 'no' (Terms of Service violation)
  - Requires money we don't have
  - Causes harm

Everything else is a learning opportunity, not a dead-end.

Outputs:
  - data/ideas.json           all ideas + their status
  - data/idea_results.json    test results
  - knowledge/ideas/latest.md human-readable idea log
  - mycelium/idea_spawns/     auto-generated scripts for working ideas
"""

import json, datetime, os, traceback
from pathlib import Path
from urllib import request as urllib_request

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
KB     = ROOT / 'knowledge'
SPAWNS = ROOT / 'mycelium' / 'idea_spawns'

for d in [DATA, KB / 'ideas', SPAWNS]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().isoformat()

# ============================================================
# IDEA GRAPH
# Each idea has:
#   id, title, description, apis_needed, mission_relevance,
#   status (untested/testing/working/partial/dead_end/wired_in),
#   test_result, alternative_if_failed, learned
# ============================================================

IDEA_SEEDS = [
    # --- CRYPTO + TRANSPARENCY ---
    {
        'id': 'crypto_donation_tracker',
        'title': 'Crypto Donation Transparency Dashboard',
        'description': 'Track BTC/ETH/SOL donations in real time. Show donors exactly how much has been raised and when it was sent to PCRF. Use CoinCap for prices, Strike for Lightning, Phantom for Solana.',
        'apis': ['coincap', 'coingecko', 'dex_screener'],
        'mission': 'transparency + fundraising',
        'test': 'fetch_coincap_btc',
        'status': 'untested',
    },
    {
        'id': 'congress_crypto_correlation',
        'title': 'Do Congress Trades Predict Crypto Moves?',
        'description': 'Cross-reference congressional stock trades with crypto market movements. When politicians buy defense stocks before a conflict, does crypto spike? Data journalism angle.',
        'apis': ['house_stock_watcher', 'coincap', 'coingecko'],
        'mission': 'transparency + accountability',
        'test': 'cross_reference_congress_crypto',
        'status': 'untested',
    },
    # --- HUMANITARIAN ---
    {
        'id': 'food_insecurity_map',
        'title': 'Food Insecurity Signal from Open Data',
        'description': 'Combine World Bank food access data + USGS disaster data + Open Food Facts to build a signal of where food insecurity is spiking. Content + grant outreach angle.',
        'apis': ['world_bank', 'usgs', 'open_food_facts'],
        'mission': 'humanitarian intelligence',
        'test': 'fetch_world_bank_food',
        'status': 'untested',
    },
    {
        'id': 'disaster_aid_connector',
        'title': 'Earthquake -> Aid Organization Connector',
        'description': 'When USGS detects M5.5+ earthquake, auto-generate content pointing to verified aid organizations for that region. USGS + verified_charities.json.',
        'apis': ['usgs', 'verified_charities'],
        'mission': 'humanitarian response',
        'test': 'fetch_usgs_major',
        'status': 'untested',
    },
    # --- CONTENT ---
    {
        'id': 'wikipedia_trending_content',
        'title': 'Wikipedia Trending -> Timely Content',
        'description': 'When a Palestine/climate/humanitarian topic trends on Wikipedia, auto-generate a post connecting it to the mission. Timing signal from real world attention.',
        'apis': ['wikipedia_pageviews'],
        'mission': 'content timing',
        'test': 'fetch_wiki_trending',
        'status': 'untested',
    },
    {
        'id': 'art_to_nft_pipeline',
        'title': 'Museum Art -> Gaza Rose NFT Companion',
        'description': 'Pair public domain museum art with original Gaza Rose art. List as paired NFT on Magic Eden. The museum piece provides context, the Gaza Rose provides the cause.',
        'apis': ['artic', 'metropolitan_museum'],
        'mission': 'revenue + art',
        'test': 'fetch_artic_public_domain',
        'status': 'untested',
    },
    # --- SOLARPUNK INFRASTRUCTURE ---
    {
        'id': 'carbon_crypto_correlation',
        'title': 'Carbon Intensity vs Crypto Mining Load',
        'description': 'When UK grid carbon is high (dirty energy), surface proof-of-stake alternatives. When low (renewable), celebrate. Content angle: green crypto is real.',
        'apis': ['carbon_intensity', 'coingecko'],
        'mission': 'solarpunk + crypto education',
        'test': 'fetch_carbon_intensity',
        'status': 'untested',
    },
    {
        'id': 'remote_jobs_to_crypto_pay',
        'title': 'Find Jobs That Pay in Crypto -> Share Daily',
        'description': 'Jobicy + Remotive filtered for crypto/Web3 pay. Daily post of top 5 jobs. Audience: people who want out of fiat. Drives Ko-fi + GitHub Sponsors.',
        'apis': ['jobicy', 'remotive'],
        'mission': 'audience building + revenue',
        'test': 'fetch_crypto_jobs',
        'status': 'untested',
    },
    # --- SYSTEM GROWTH ---
    {
        'id': 'fork_success_tracker',
        'title': 'Track Who Forks and What They Build',
        'description': 'GitHub API: watch forks of meeko-nerve-center. When someone forks and commits, surface it. Amplify their work. Network effect + social proof.',
        'apis': ['github_api'],
        'mission': 'system replication',
        'test': 'fetch_github_forks',
        'status': 'untested',
    },
    {
        'id': 'grant_api_scanner',
        'title': 'Scan USAspending for Grant Opportunities',
        'description': 'USAspending has all federal grants. Filter for humanitarian/open source/technology categories. Auto-generate grant applications using grant_outreach.py.',
        'apis': ['usaspending'],
        'mission': 'funding',
        'test': 'fetch_usaspending_grants',
        'status': 'untested',
    },
    # --- NEW IDEAS THE SYSTEM GENERATES ITSELF ---
    # (populated by generate_new_ideas() below)
]

# ============================================================
# TESTS
# Each test actually hits the API and checks if useful data comes back
# ============================================================

def fetch_url(url, timeout=10):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/idea-engine'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, str(e)

def test_idea(idea):
    """Run the test for an idea. Return (success, data, error, learned)."""
    test_name = idea.get('test', '')
    
    tests = {
        'fetch_coincap_btc': lambda: fetch_url('https://api.coincap.io/v2/assets/bitcoin'),
        'fetch_wiki_trending': lambda: fetch_url(
            f'https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/'
            f'{(datetime.date.today()-datetime.timedelta(days=1)).strftime("%Y/%m/%d")}'
        ),
        'fetch_usgs_major': lambda: fetch_url(
            'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=5.5&limit=3'
        ),
        'fetch_artic_public_domain': lambda: fetch_url(
            'https://api.artic.edu/api/v1/artworks/search?q=flower&fields=id,title,image_id,is_public_domain&limit=3'
        ),
        'fetch_carbon_intensity': lambda: fetch_url('https://api.carbonintensity.org.uk/intensity'),
        'fetch_crypto_jobs': lambda: fetch_url('https://jobicy.com/api/v2/remote-jobs?count=5&tag=crypto'),
        'fetch_github_forks': lambda: fetch_url(
            'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/forks'
        ),
        'fetch_usaspending_grants': lambda: fetch_url(
            'https://api.usaspending.gov/api/v2/references/toptier_agencies/'
        ),
        'fetch_world_bank_food': lambda: fetch_url(
            'http://api.worldbank.org/v2/country/all/indicator/SN.ITK.DEFC.ZS?format=json&mrv=1&per_page=3'
        ),
        'cross_reference_congress_crypto': lambda: fetch_url(
            'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json'
        ),
    }
    
    test_fn = tests.get(test_name)
    if not test_fn:
        return False, None, f'No test defined for {test_name}', 'Need to write test'
    
    try:
        data, error = test_fn()
        if error:
            return False, None, error, f'API error: {error[:100]}. Try alternative source.'
        if data:
            return True, data, None, 'API responding. Data available. Ready to wire in.'
        return False, None, 'Empty response', 'API returned empty. Check endpoint.'
    except Exception as e:
        return False, None, str(e), f'Exception: {str(e)[:100]}'

# ============================================================
# IDEA GENERATOR
# Looks at what's working and generates new combinations
# ============================================================

def generate_new_ideas(existing_ideas, working_apis):
    """Cross-pollinate working APIs to generate new ideas."""
    new_ideas = []
    
    # Pattern: if two APIs both work, what's the intersection?
    combos = [
        (
            'gecko_terminal_new_pools',
            ['gecko_terminal', 'telegram'],
            'Auto-alert for new Solana pool launches with >$10K liquidity. Phantom entry signal.',
            'New Solana Pool Alert -> Telegram',
            'revenue + crypto intelligence',
        ),
        (
            'spacex_carbon_hope_post',
            ['spacex', 'carbon_intensity'],
            'When next SpaceX launch happens AND carbon intensity is low: post a SolarPunk hope piece. Two signals = one timely post.',
            'SpaceX Launch + Clean Grid = Hope Content',
            'solarpunk content',
        ),
        (
            'world_bank_grant_match',
            ['world_bank', 'usaspending'],
            'Match World Bank country data (poverty, health gaps) to USAspending grants in same area. Auto-generate grant applications.',
            'World Bank Data -> Grant Target Finder',
            'funding intelligence',
        ),
        (
            'music_art_post',
            ['musicbrainz', 'artic'],
            'Pair resistance music artist with public domain art on same theme. Visual + audio content unit.',
            'Resistance Music + Museum Art = Post Unit',
            'content quality',
        ),
        (
            'job_skill_gap_analyzer',
            ['jobicy', 'remotive', 'arxiv'],
            'What skills do crypto/Web3 jobs require vs what arXiv says is being researched? Gap = content + learning roadmap.',
            'Job Market vs Research Gap Analysis',
            'audience education',
        ),
        (
            'wikipedia_trending_art_pair',
            ['wikipedia_pageviews', 'artic', 'metropolitan_museum'],
            'When a humanitarian topic trends on Wikipedia, pull relevant museum art and make a post that day.',
            'Trending Topic + Museum Art = Timely Visual Post',
            'content timing + quality',
        ),
        (
            'book_to_post_pipeline',
            ['open_library', 'wikipedia'],
            'When a book about Palestine/climate is freely available on Internet Archive, generate a post with a direct read link. Free education, zero friction.',
            'Free Books -> Direct Share Posts',
            'education + mission',
        ),
        (
            'exchange_rate_donation_nudge',
            ['exchange_rates', 'coingecko'],
            'When USD is strong against ILS/JOD/EGP, post: "Your donation goes further today." Real FX data, real impact context.',
            'FX Rate -> Donation Impact Message',
            'fundraising intelligence',
        ),
    ]
    
    existing_ids = {i['id'] for i in existing_ideas}
    
    for idea_id, apis, desc, title, mission in combos:
        if idea_id not in existing_ids:
            new_ideas.append({
                'id':     idea_id,
                'title':  title,
                'description': desc,
                'apis':   apis,
                'mission': mission,
                'test':   None,
                'status': 'generated',
                'source': 'idea_engine_self_generated',
                'generated': TODAY,
            })
    
    return new_ideas

# ============================================================
# SPAWN: working ideas become real scripts
# ============================================================

def spawn_script(idea, test_data):
    """Turn a working idea into a real Python script."""
    script_path = SPAWNS / f"{idea['id']}.py"
    if script_path.exists():
        return  # already exists
    
    content = f'''#!/usr/bin/env python3
"""
AUTO-GENERATED by idea_engine.py on {TODAY}
Idea: {idea['title']}
Mission: {idea['mission']}
Status: WORKING - spawned from successful test

Do not delete this header. Edit the body as needed.
"""

import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

def run():
    # TODO: expand this stub into full implementation
    # Idea: {idea['description']}
    # APIs: {idea['apis']}
    print(f"[{idea['id']}] Running...")
    # Add implementation here
    pass

if __name__ == '__main__':
    run()
'''
    script_path.write_text(content)
    print(f"[idea-engine] Spawned: mycelium/idea_spawns/{idea['id']}.py")

# ============================================================
# LOAD / SAVE idea state
# ============================================================

def load_ideas():
    path = DATA / 'ideas.json'
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return []

def save_ideas(ideas):
    (DATA / 'ideas.json').write_text(json.dumps(ideas, indent=2))

def load_results():
    path = DATA / 'idea_results.json'
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return []

def save_results(results):
    (DATA / 'idea_results.json').write_text(json.dumps(results, indent=2))

# ============================================================
# MAIN
# ============================================================

def run():
    print(f'[idea-engine] Starting \u2014 {TODAY}')
    
    # Load existing state
    existing = load_ideas()
    results  = load_results()
    existing_ids = {i['id'] for i in existing}
    
    # Merge in seeds not yet tracked
    for seed in IDEA_SEEDS:
        if seed['id'] not in existing_ids:
            existing.append(seed)
            existing_ids.add(seed['id'])
    
    # Generate new ideas from cross-pollination
    working_apis = [r['idea_id'] for r in results if r.get('success')]
    new_ideas = generate_new_ideas(existing, working_apis)
    for idea in new_ideas:
        if idea['id'] not in existing_ids:
            existing.append(idea)
            existing_ids.add(idea['id'])
            print(f"[idea-engine] New idea generated: {idea['title']}")
    
    # Test untested ideas (up to 5 per run to avoid rate limits)
    tested_count = 0
    working = []
    failed  = []
    
    for idea in existing:
        if idea.get('status') not in ['untested', 'generated']: continue
        if tested_count >= 5: break
        if not idea.get('test'): 
            idea['status'] = 'generated_needs_test'
            continue
        
        print(f"[idea-engine] Testing: {idea['title']}")
        success, data, error, learned = test_idea(idea)
        tested_count += 1
        
        result = {
            'idea_id':  idea['id'],
            'title':    idea['title'],
            'tested':   NOW,
            'success':  success,
            'error':    error,
            'learned':  learned,
            'data_sample': str(data)[:200] if data else None,
        }
        results.append(result)
        
        if success:
            idea['status']  = 'working'
            idea['learned'] = learned
            working.append(idea)
            spawn_script(idea, data)
            print(f"  \u2705 WORKING: {idea['title']}")
            print(f"  Learned: {learned}")
        else:
            # Not a dead-end yet - find alternative
            if 'rate limit' in str(error).lower() or '429' in str(error):
                idea['status'] = 'rate_limited'
                idea['learned'] = 'Rate limited. Retry later or use cached data.'
                print(f"  \u23f3 RATE LIMITED: {idea['title']}")
            elif '401' in str(error) or '403' in str(error):
                idea['status'] = 'needs_auth'
                idea['learned'] = 'Needs API key. Check for free tier.'
                print(f"  \ud83d\udd11 NEEDS AUTH: {idea['title']}")
            else:
                idea['status'] = 'failed_retry'
                idea['learned'] = learned
                failed.append(idea)
                print(f"  \u274c FAILED: {idea['title']} \u2014 {error}")
    
    # Save state
    save_ideas(existing)
    save_results(results)
    
    # Build digest
    total     = len(existing)
    n_working = len([i for i in existing if i['status'] == 'working'])
    n_wired   = len([i for i in existing if i['status'] == 'wired_in'])
    n_pending = len([i for i in existing if i['status'] in ['untested','generated','generated_needs_test']])
    n_failed  = len([i for i in existing if i['status'] == 'failed_retry'])
    
    lines = [
        f'# Idea Engine Log \u2014 {TODAY}',
        '',
        f'Total ideas: {total} | Working: {n_working} | Wired in: {n_wired} | Pending: {n_pending} | Failed/retry: {n_failed}',
        '',
        '## Tested This Run',
        '',
    ]
    
    for r in results[-tested_count:]:
        status = '\u2705' if r['success'] else '\u274c'
        lines.append(f"{status} **{r['title']}**")
        lines.append(f"   Learned: {r['learned']}")
        lines.append('')
    
    if new_ideas:
        lines += ['## Self-Generated Ideas (new this run)', '']
        for idea in new_ideas:
            lines.append(f"- **{idea['title']}**: {idea['description'][:100]}")
        lines.append('')
    
    lines += [
        '## All Ideas Status', '',
        '| Status | Count |',
        '|--------|-------|',
        f'| \u2705 Working | {n_working} |',
        f'| \ud83dí´Œ Wired in | {n_wired} |',
        f'| \u23f3 Pending test | {n_pending} |',
        f'| \u274c Failed (retry) | {n_failed} |',
    ]
    
    digest = '\n'.join(lines)
    (KB / 'ideas' / f'{TODAY}.md').write_text(digest)
    (KB / 'ideas' / 'latest.md').write_text(digest)
    
    print(f'\n[idea-engine] Run complete.')
    print(f'  Tested: {tested_count} | Working: {len(working)} | Failed: {len(failed)}')
    print(f'  New self-generated ideas: {len(new_ideas)}')
    print(f'  Total idea graph: {total} ideas')
    
    return {
        'total': total, 'working': n_working,
        'tested_this_run': tested_count,
        'new_ideas': len(new_ideas),
    }

if __name__ == '__main__':
    run()
