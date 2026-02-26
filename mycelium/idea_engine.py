#!/usr/bin/env python3
"""
Idea Engine
============
The system generates its own ideas.
Tests them. Learns from results.
Only stops at true hard walls.

This is the meta-layer. Every other script is a capability.
This script asks: what NEW capability should exist?
Then it tries to build it. Then it measures if it worked.

Cycle:
  1. SCAN    - what APIs/tools/data do we have?
  2. GAP     - what connections aren't made yet?
  3. IDEATE  - generate idea for a new connection
  4. TEST    - try it (minimal version)
  5. LEARN   - record result (success/fail/partial/blocked)
  6. EVOLVE  - if blocked, find alternative. if dead-end, flag and move on.
  7. PROPOSE - write the actual implementation if test passes

Outputs:
  - data/ideas.json          all ideas + their status
  - data/idea_learnings.json what worked, what didn't, why
  - knowledge/ideas/BACKLOG.md  queue of validated ideas to build
  - knowledge/ideas/GRAVEYARD.md dead-ends and why they died (valuable!)
  - content/queue/idea_*.json   shareable insights from the learning process

This script runs weekly. Each run it picks the top 3 untested ideas and tests them.
Over time it builds a self-expanding capability map.
"""

import json, datetime, os, hashlib
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
CONT  = ROOT / 'content' / 'queue'

for d in [DATA, KB / 'ideas', CONT]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().isoformat()

# ============================================================
# CAPABILITY MAP
# What the system currently knows how to do.
# Each run adds to this. This is the system's self-knowledge.
# ============================================================
CURRENT_CAPABILITIES = [
    {'id': 'crypto_prices',     'tool': 'dex_monitor.py',          'data': ['price', 'volume', 'liquidity'], 'apis': ['dexscreener', 'coingecko', 'coincap']},
    {'id': 'job_discovery',     'tool': 'crypto_jobs.py',           'data': ['remote_jobs', 'crypto_jobs'],  'apis': ['jobicy', 'remotive']},
    {'id': 'art_content',       'tool': 'art_cause_generator.py',   'data': ['artworks', 'cause_posts'],    'apis': ['artic', 'met']},
    {'id': 'world_intel',       'tool': 'world_intelligence.py',    'data': ['world_bank', 'spacex', 'fx'],  'apis': ['worldbank', 'spacex', 'exchangerate', 'coincap', 'geckoterminal']},
    {'id': 'earthquake_watch',  'tool': 'knowledge_harvester_v2.py','data': ['earthquakes'],                'apis': ['usgs']},
    {'id': 'carbon_track',      'tool': 'knowledge_harvester_v2.py','data': ['carbon_intensity'],           'apis': ['carbonintensity']},
    {'id': 'congress_watch',    'tool': 'congress_watcher.py',      'data': ['trades', 'accountability'],   'apis': ['house_stock_watcher']},
    {'id': 'book_discovery',    'tool': 'open_library_reader.py',   'data': ['books', 'free_ebooks'],       'apis': ['openlibrary', 'archive_org']},
    {'id': 'music_intel',       'tool': 'music_intelligence.py',    'data': ['artists', 'tracks'],          'apis': ['musicbrainz', 'itunes']},
    {'id': 'space_news',        'tool': 'knowledge_harvester_v2.py','data': ['launches', 'space_articles'], 'apis': ['spaceflight_news', 'open_notify']},
    {'id': 'reddit_signal',     'tool': 'knowledge_harvester_v2.py','data': ['community_posts'],            'apis': ['reddit']},
    {'id': 'arxiv_research',    'tool': 'knowledge_harvester.py',   'data': ['research_papers'],            'apis': ['arxiv']},
    {'id': 'github_trends',     'tool': 'knowledge_harvester.py',   'data': ['trending_repos'],             'apis': ['github']},
    {'id': 'content_generation','tool': 'humanitarian_content.py',  'data': ['posts', 'drafts'],            'apis': []},
    {'id': 'telegram_alerts',   'tool': 'telegram_bot.py',          'data': ['alerts', 'briefings'],        'apis': ['telegram']},
    {'id': 'rss_feed',          'tool': 'rss_generator.py',         'data': ['feed_xml'],                   'apis': []},
    {'id': 'notion_sync',       'tool': 'notion_bridge.py',         'data': ['notion_pages'],               'apis': ['notion']},
    {'id': 'wikipedia_trending','tool': 'world_intelligence.py',    'data': ['trending_topics'],            'apis': ['wikipedia']},
    {'id': 'api_discovery',     'tool': 'api_directory_harvester.py','data': ['new_apis'],                  'apis': ['public_apis_github']},
    {'id': 'grant_outreach',    'tool': 'grant_outreach.py',        'data': ['grant_drafts'],               'apis': []},
    {'id': 'email_drafts',      'tool': 'email_drafter.py',         'data': ['email_drafts'],               'apis': []},
    {'id': 'youtube_scripts',   'tool': 'youtube_shorts_writer.py', 'data': ['video_scripts'],              'apis': []},
]

# ============================================================
# IDEA TEMPLATES
# Combinations the system hasn't tried yet.
# Format: {source_capability} + {target_capability} = {idea}
# ============================================================
IDEA_TEMPLATES = [
    {
        'id': 'quake_to_aid',
        'title': 'Earthquake -> Humanitarian Aid Pipeline',
        'description': 'When USGS detects M5.5+ earthquake, auto-generate donation appeal post + find relevant orgs via Open Library + alert via Telegram',
        'connects': ['earthquake_watch', 'content_generation', 'telegram_alerts'],
        'test_url': 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=5.5&limit=1',
        'test_field': 'features',
        'value': 'humanitarian',
        'effort': 'low',
    },
    {
        'id': 'price_to_donation_value',
        'title': 'Live Crypto Price -> Donation Value Calculator',
        'description': 'Show donors exactly what their crypto is worth in USD and what it buys (PCRF cost per treatment). Updates in real-time.',
        'connects': ['crypto_prices', 'content_generation'],
        'test_url': 'https://api.coincap.io/v2/assets/bitcoin',
        'test_field': 'data',
        'value': 'revenue',
        'effort': 'low',
    },
    {
        'id': 'congress_to_accountability_post',
        'title': 'Congress Trade -> Same-Day Accountability Post',
        'description': 'When a new trade is filed, auto-post within hours. Speed = credibility. First mover on accountability content.',
        'connects': ['congress_watch', 'content_generation', 'telegram_alerts'],
        'test_url': 'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json',
        'test_field': None,
        'value': 'audience',
        'effort': 'medium',
    },
    {
        'id': 'trending_to_content_timing',
        'title': 'Wikipedia Trending -> Content Timing Engine',
        'description': 'If a topic related to Palestine/climate/crypto is trending on Wikipedia, publish related content within the hour. Ride the wave.',
        'connects': ['wikipedia_trending', 'content_generation'],
        'test_url': 'https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/2026/01/01',
        'test_field': 'items',
        'value': 'audience',
        'effort': 'low',
    },
    {
        'id': 'new_solana_pool_to_alert',
        'title': 'New Solana Pool Launch -> Telegram Alert',
        'description': 'GeckoTerminal detects new Solana pool with >$50K liquidity in first hour. Telegram alert fires. You decide whether to buy.',
        'connects': ['world_intel', 'telegram_alerts'],
        'test_url': 'https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page=1',
        'test_field': 'data',
        'value': 'revenue',
        'effort': 'low',
    },
    {
        'id': 'job_to_skills_gap',
        'title': 'Job Market -> Skills Gap Analyzer',
        'description': 'What skills are crypto/Web3 jobs asking for most? Track over time. Surface what to learn next to maximize earning.',
        'connects': ['job_discovery'],
        'test_url': 'https://jobicy.com/api/v2/remote-jobs?count=50&tag=blockchain',
        'test_field': 'jobs',
        'value': 'personal',
        'effort': 'low',
    },
    {
        'id': 'art_to_nft_pipeline',
        'title': 'Museum Art Pairs -> NFT Mint Queue',
        'description': 'Art+Cause pairs that score highest -> suggested NFT mints on Phantom. Pairs the content pipeline with the revenue pipeline.',
        'connects': ['art_content', 'crypto_prices'],
        'test_url': 'https://api.artic.edu/api/v1/artworks/search?q=flower&fields=id,title,image_id&limit=3',
        'test_field': 'data',
        'value': 'revenue',
        'effort': 'medium',
    },
    {
        'id': 'carbon_to_grid_post',
        'title': 'Carbon Intensity -> Real-Time Grid Post',
        'description': 'When UK grid goes very low carbon (lots of renewables), auto-post: "Right now X% of UK electricity is renewable." SolarPunk content that writes itself.',
        'connects': ['carbon_track', 'content_generation'],
        'test_url': 'https://api.carbonintensity.org.uk/intensity',
        'test_field': 'data',
        'value': 'audience',
        'effort': 'low',
    },
    {
        'id': 'space_launch_to_hope_post',
        'title': 'SpaceX Launch -> Hope Content',
        'description': 'Every rocket launch is proof humanity can still do impossible things. Auto-generate "this is what we\'re capable of" posts timed to launches.',
        'connects': ['space_news', 'content_generation'],
        'test_url': 'https://api.spacexdata.com/v5/launches/upcoming',
        'test_field': None,
        'value': 'audience',
        'effort': 'low',
    },
    {
        'id': 'book_to_reading_thread',
        'title': 'Free Books -> Weekly Reading Thread',
        'description': 'Every Sunday: post a thread of 5 free books on Open Library/Archive.org related to that week\'s biggest news event.',
        'connects': ['book_discovery', 'wikipedia_trending', 'content_generation'],
        'test_url': 'https://openlibrary.org/search.json?q=Palestine&limit=3&fields=title,author_name,ia',
        'test_field': 'docs',
        'value': 'audience',
        'effort': 'low',
    },
    {
        'id': 'fx_rates_to_donation_context',
        'title': 'Exchange Rates -> Donation Context Posts',
        'description': 'Show what $10/$50/$100 donations convert to in local currencies of donor countries. Make the donation feel more real and tangible.',
        'connects': ['world_intel', 'content_generation'],
        'test_url': 'https://open.er-api.com/v6/latest/USD',
        'test_field': 'rates',
        'value': 'revenue',
        'effort': 'low',
    },
    {
        'id': 'music_to_playlist',
        'title': 'Resistance Music -> Curated Playlist Posts',
        'description': 'Weekly: "5 songs that carry the message" post. MusicBrainz artists tagged with resistance/protest/solidarity. High shareability.',
        'connects': ['music_intel', 'content_generation'],
        'test_url': 'https://musicbrainz.org/ws/2/artist/?query=Palestine&fmt=json&limit=3',
        'test_field': 'artists',
        'value': 'audience',
        'effort': 'low',
    },
    {
        'id': 'api_discovery_to_auto_wire',
        'title': 'New API Discovery -> Auto-Suggest Integration',
        'description': 'When api_directory_harvester finds a new high-scoring API, auto-generate a stub script to test it and add to backlog.',
        'connects': ['api_discovery'],
        'test_url': 'https://raw.githubusercontent.com/public-apis/public-apis/master/README.md',
        'test_field': None,
        'value': 'system',
        'effort': 'high',
    },
    {
        'id': 'world_bank_to_impact_posts',
        'title': 'World Bank Data -> Impact Visualization Posts',
        'description': '"X% of people in Y country lack clean water" posts with source. Factual, shareable, drives Ko-fi donations.',
        'connects': ['world_intel', 'content_generation'],
        'test_url': 'http://api.worldbank.org/v2/country/all/indicator/SH.H2O.BASW.ZS?format=json&mrv=1&per_page=3',
        'test_field': None,
        'value': 'revenue',
        'effort': 'low',
    },
    {
        'id': 'reddit_to_trend_map',
        'title': 'Reddit Signals -> Weekly Trend Map',
        'description': 'Track which topics on r/solarpunk, r/worldnews, r/opensource are gaining momentum week over week. Use to plan content 7 days ahead.',
        'connects': ['reddit_signal', 'content_generation'],
        'test_url': 'https://www.reddit.com/r/solarpunk/hot.json?limit=10',
        'test_field': 'data',
        'value': 'audience',
        'effort': 'low',
    },
]

# ============================================================
# TEST ENGINE
# ============================================================
def test_idea(idea):
    """
    Minimal test: can we reach the API and get the expected data?
    Returns: success, data_sample, error
    """
    url = idea.get('test_url')
    if not url:
        return {'status': 'untestable', 'reason': 'no test_url defined'}
    
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/idea-engine'})
        with urllib_request.urlopen(req, timeout=10) as r:
            raw = r.read()
            data = json.loads(raw)
        
        # Check expected field exists
        field = idea.get('test_field')
        if field:
            # Handle nested (list wrapper)
            if isinstance(data, list):
                check = data[0] if data else {}
                has_field = field in check if isinstance(check, dict) else True
            elif isinstance(data, dict):
                has_field = field in data
            else:
                has_field = True
            
            if not has_field:
                return {
                    'status': 'partial',
                    'reason': f'API reachable but field "{field}" not found',
                    'keys_found': list(data.keys()) if isinstance(data, dict) else 'list',
                }
        
        # Sample the data
        if isinstance(data, list):
            sample = data[:1]
        elif isinstance(data, dict):
            sample = {k: str(v)[:100] for k, v in list(data.items())[:3]}
        else:
            sample = str(data)[:200]
        
        return {
            'status': 'success',
            'data_sample': sample,
            'bytes': len(raw),
        }
    
    except Exception as e:
        err = str(e)
        # Classify the failure
        if '403' in err or '401' in err:
            return {'status': 'blocked', 'reason': 'API requires auth or denied access', 'error': err}
        elif '404' in err:
            return {'status': 'dead_end', 'reason': 'Endpoint not found (404)', 'error': err}
        elif '429' in err:
            return {'status': 'rate_limited', 'reason': 'Rate limited - retry later', 'error': err}
        elif 'timeout' in err.lower():
            return {'status': 'timeout', 'reason': 'API timed out', 'error': err}
        else:
            return {'status': 'error', 'reason': err}

# ============================================================
# LEARNING ENGINE
# ============================================================
def load_learnings():
    path = DATA / 'idea_learnings.json'
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return {'tested': {}, 'successes': [], 'failures': [], 'dead_ends': [], 'blocked': []}

def save_learnings(learnings):
    (DATA / 'idea_learnings.json').write_text(json.dumps(learnings, indent=2))

def load_ideas():
    path = DATA / 'ideas.json'
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return {'ideas': [], 'last_run': None}

def save_ideas(ideas_data):
    (DATA / 'ideas.json').write_text(json.dumps(ideas_data, indent=2))

# ============================================================
# ALTERNATIVE FINDER
# If one approach is blocked, find another way to the same goal
# ============================================================
def find_alternative(idea, failure_reason):
    """
    When an idea fails, look for alternative approaches.
    Returns alternative idea or None if dead-end.
    """
    alternatives = {
        'blocked':      'Try a different API endpoint or use cached data instead of live',
        'rate_limited': 'Add caching layer - fetch once daily, reuse throughout day',
        'timeout':      'Add retry logic with exponential backoff',
        'dead_end':     'Search api_directory_harvester results for alternative API',
        'partial':      'Adapt field mapping - data exists but structure differs',
    }
    
    alt_note = alternatives.get(failure_reason, 'Unknown failure - manual investigation needed')
    
    return {
        'original_id':  idea['id'],
        'alternative':  alt_note,
        'next_action':  'manual' if failure_reason == 'dead_end' else 'auto_retry',
        'generated':    NOW,
    }

# ============================================================
# PROPOSAL GENERATOR
# If test passes, generate the actual implementation plan
# ============================================================
def generate_proposal(idea, test_result):
    """
    Generate implementation proposal for a validated idea.
    This goes into BACKLOG.md for the next build cycle.
    """
    return {
        'id':          idea['id'],
        'title':       idea['title'],
        'description': idea['description'],
        'connects':    idea['connects'],
        'value':       idea['value'],
        'effort':      idea['effort'],
        'test_passed': True,
        'test_data':   test_result.get('data_sample', {}),
        'proposed_file': f"mycelium/{idea['id']}.py",
        'priority':    'high' if idea['value'] in ['revenue', 'humanitarian'] else 'medium',
        'proposed_at': NOW,
    }

# ============================================================
# MAIN CYCLE
# ============================================================
def run():
    print(f'[idea-engine] Cycle start \u2014 {TODAY}')
    
    learnings = load_learnings()
    ideas_data = load_ideas()
    
    # Load all ideas, mark already-tested ones
    all_ideas = IDEA_TEMPLATES.copy()
    tested_ids = set(learnings['tested'].keys())
    
    # Pick untested ideas first, then re-test partial/rate_limited
    untested = [i for i in all_ideas if i['id'] not in tested_ids]
    retestable = [i for i in all_ideas if learnings['tested'].get(i['id'], {}).get('status') 
                  in ('rate_limited', 'timeout', 'partial')]
    
    to_test = (untested + retestable)[:5]  # test 5 per run
    
    print(f'[idea-engine] {len(untested)} untested, {len(retestable)} retestable, testing {len(to_test)}')
    
    new_successes = []
    new_failures  = []
    proposals     = []
    dead_ends     = []
    
    for idea in to_test:
        print(f'[idea-engine] Testing: {idea["title"]}')
        result = test_idea(idea)
        
        print(f'  -> {result["status"]}: {result.get("reason", "ok")}')
        
        # Record
        learnings['tested'][idea['id']] = {
            'status':  result['status'],
            'reason':  result.get('reason', ''),
            'tested':  NOW,
            'title':   idea['title'],
        }
        
        if result['status'] == 'success':
            proposal = generate_proposal(idea, result)
            proposals.append(proposal)
            new_successes.append(idea['id'])
            if idea['id'] not in learnings['successes']:
                learnings['successes'].append(idea['id'])
        
        elif result['status'] == 'dead_end':
            dead_ends.append(idea)
            if idea['id'] not in learnings['dead_ends']:
                learnings['dead_ends'].append(idea['id'])
        
        elif result['status'] == 'blocked':
            alt = find_alternative(idea, 'blocked')
            if idea['id'] not in learnings['blocked']:
                learnings['blocked'].append({'id': idea['id'], 'alternative': alt})
        
        else:
            alt = find_alternative(idea, result['status'])
            new_failures.append({'idea': idea['id'], 'result': result, 'alternative': alt})
    
    # Update ideas store
    ideas_data = {
        'last_run':   NOW,
        'total_ideas': len(all_ideas),
        'tested':     len(learnings['tested']),
        'successes':  len(learnings['successes']),
        'dead_ends':  len(learnings['dead_ends']),
        'blocked':    len(learnings['blocked']),
        'untested':   len(untested),
        'proposals':  proposals,
        'all_ideas':  all_ideas,
    }
    save_ideas(ideas_data)
    save_learnings(learnings)
    
    # Write BACKLOG.md
    build_backlog(proposals, learnings)
    
    # Write GRAVEYARD.md
    if dead_ends:
        build_graveyard(dead_ends, learnings)
    
    # Summary
    print(f'[idea-engine] Results: {len(new_successes)} passed, {len(new_failures)} failed, {len(dead_ends)} dead-ends')
    if new_successes:
        print(f'[idea-engine] VALIDATED: {new_successes}')
    if proposals:
        print(f'[idea-engine] {len(proposals)} proposals ready to build')
        for p in proposals:
            print(f'  -> [{p["priority"].upper()}] {p["title"]}')
    
    return ideas_data

def build_backlog(proposals, learnings):
    lines = [
        '# Idea Backlog \u2014 Validated & Ready to Build',
        f'*Generated: {TODAY} | Source: idea_engine.py*', '',
        f'Validated: {len(learnings["successes"])} | Tested: {len(learnings["tested"])} | Dead-ends: {len(learnings["dead_ends"])}', '',
    ]
    
    if proposals:
        high = [p for p in proposals if p['priority'] == 'high']
        med  = [p for p in proposals if p['priority'] == 'medium']
        
        if high:
            lines += ['## \ud83d\udd34 High Priority (Revenue + Humanitarian)', '']
            for p in high:
                lines += [
                    f"### {p['title']}",
                    f"**File:** `{p['proposed_file']}`",
                    f"**Value:** {p['value']} | **Effort:** {p['effort']}",
                    f"{p['description']}",
                    f"**Connects:** {', '.join(p['connects'])}", ''
                ]
        if med:
            lines += ['## \ud83dí¿¡ Medium Priority', '']
            for p in med:
                lines += [
                    f"### {p['title']}",
                    f"{p['description']}",
                    f"**File:** `{p['proposed_file']}`", ''
                ]
    
    # All validated successes from history
    if learnings['successes']:
        lines += ['## \u2705 All Validated Ideas', '']
        all_ideas_by_id = {i['id']: i for i in IDEA_TEMPLATES}
        for sid in learnings['successes']:
            idea = all_ideas_by_id.get(sid, {})
            lines.append(f"- **{idea.get('title', sid)}** \u2014 {idea.get('value', '?')} value")
        lines.append('')
    
    (KB / 'ideas' / 'BACKLOG.md').write_text('\n'.join(lines))
    print('[idea-engine] BACKLOG.md updated')

def build_graveyard(dead_ends, learnings):
    lines = [
        '# Idea Graveyard \u2014 Dead-Ends & What We Learned',
        '*These ideas failed. That\u2019s valuable. We know what doesn\u2019t work.*', '',
    ]
    for idea in dead_ends:
        result = learnings['tested'].get(idea['id'], {})
        lines += [
            f"## {idea['title']}",
            f"**Why it died:** {result.get('reason', 'unknown')}",
            f"**Lesson:** {idea.get('description', '')[:200]}",
            f"**Alternative:** Look for different API or different approach", ''
        ]
    (KB / 'ideas' / 'GRAVEYARD.md').write_text('\n'.join(lines))
    print('[idea-engine] GRAVEYARD.md updated')

if __name__ == '__main__':
    run()
