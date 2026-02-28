#!/usr/bin/env python3
"""
Impact Storyteller Engine
==========================
The system has real impact data: trades flagged, art generated,
PCRF dollars raised, engines self-built, ideas implemented.
But it presents this as raw numbers. Nobody feels raw numbers.

This engine turns data into stories.

Three story formats generated daily:

  1. THE THREAD (Mastodon/Bluesky)
     A narrative thread: "Here's what happened while you slept..."
     Tells the story of one cycle in human terms
     Who the congressmember is. What the trade means. What the art shows.
     Reads like a journalist's notebook, not a data dump.

  2. THE LONG READ (docs/stories/)
     Once per week: a 600-800 word narrative piece
     "The Machine That Wouldn't Stop" type angle
     Stored in docs/stories/ and linked from README
     These are what journalists find via search

  3. THE SNAPSHOT (for email/social)
     One powerful sentence that captures this week's impact
     Not: "70% of revenue goes to PCRF"
     But: "This week, a Gaza Rose sold. A child gets medical care."
     Queue to social engine for optimal time posting

Why this matters:
  Stories spread. Data doesn't.
  Stories get shared. Reports don't.
  A journalist needs a story, not a dashboard.
  A donor needs to feel something, not see a percentage.
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

HF_TOKEN = os.environ.get('HF_TOKEN', '')
MASTODON_TOKEN    = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def get_story_data():
    d = {}
    try:
        congress = load(DATA / 'congress.json')
        trades = congress if isinstance(congress, list) else congress.get('trades', [])
        d['trade'] = trades[0] if trades else None
    except: pass
    try:
        arts = load(DATA / 'generated_art.json')
        al = arts if isinstance(arts, list) else arts.get('art', [])
        d['art'] = al[-1] if al else None
        d['art_count'] = len(al)
    except: pass
    try:
        ev = load(DATA / 'kofi_events.json')
        ev = ev if isinstance(ev, list) else ev.get('events', [])
        total = sum(float(e.get('amount',0)) for e in ev if e.get('type') in ('donation','Donation'))
        d['pcrf_total'] = round(total * 0.70, 2)
        d['donations_total'] = round(total, 2)
        recent_donors = [e.get('from_name','') for e in ev[-3:] if e.get('from_name')]
        d['recent_donors'] = recent_donors
    except: pass
    try:
        evo = load(DATA / 'evolution_log.json')
        built = evo.get('built', [])
        d['latest_engine'] = built[-1] if built else None
        d['self_built_count'] = len(built)
    except: pass
    try:
        d['engines'] = len(list((ROOT / 'mycelium').glob('*.py')))
    except: pass
    try:
        world = load(DATA / 'world_state.json')
        events = world.get('events', world.get('news', []))
        d['palestine_news'] = [
            e.get('title', e.get('headline',''))
            for e in events
            if any(kw in e.get('title',e.get('headline','')).lower()
                   for kw in ['gaza','palestine','pcrf','ceasefire'])
        ][:2]
    except: pass
    return d

def ask_llm(prompt, max_tokens=700):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': 'You are a narrative journalist. You turn data into stories that make people feel something. Specific, human, never corporate.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[story] LLM error: {e}')
        return None

def generate_daily_thread(data):
    trade = data.get('trade', {})
    art   = data.get('art', {})
    engine = data.get('latest_engine', {})

    prompt = f"""Write a Mastodon/Bluesky thread (4-5 posts) that tells the story of what this AI system did today.

Data:
  Congressional trade: {json.dumps(trade, default=str)[:300] if trade else 'none today'}
  Latest art: {json.dumps(art, default=str)[:200] if art else 'none'}
  Art total: {data.get('art_count', 0)} pieces total
  PCRF total: ${data.get('pcrf_total', 0):.2f}
  New engine built: {engine.get('title','') if engine else 'none today'}
  Total engines: {data.get('engines', 0)}
  Palestine news: {data.get('palestine_news', [])}

Write a NARRATIVE thread. Not bullet points. A story.
Post 1: The hook — what happened today that matters
Post 2: The accountability piece (if trade exists)
Post 3: The art + impact (Gaza Rose → PCRF)
Post 4: The machine angle (what the system built/did)
Post 5: The invitation (fork it, support it, follow along)

Each post under 400 chars. Conversational. Human. Real.
Separate posts with ---

Do NOT start every post with 'I' or 'We'. Vary the opening."""
    return ask_llm(prompt, max_tokens=600)

def generate_weekly_long_read(data):
    prompt = f"""Write a 700-word narrative piece about this autonomous AI system.

Data this week:
  Trades flagged: the system has flagged congressional trades automatically
  Art generated: {data.get('art_count', 0)} Gaza Rose pieces total
  PCRF total: ${data.get('pcrf_total', 0):.2f} raised
  Self-built engines: {data.get('self_built_count', 0)}
  Total engines: {data.get('engines', 0)}
  Repo: {REPO_URL}

Angle: "The machine that built itself to fight corruption and fund Palestinian children"

Structure:
- Open with a specific scene (a trade being flagged at 3am)
- Build to the technical innovation (it wrote its own code)
- Connect to the human stakes (Palestinian children's medical care)
- Close with the invitation (anyone can fork this)

Journalistic style. Specific details. No jargon. 
This piece will be found by journalists via search.

Write the full piece. No headers. Flowing narrative."""
    return ask_llm(prompt, max_tokens=900)

def generate_snapshot(data):
    prompt = f"""Write ONE powerful sentence that captures this week's impact.

Facts:
  Art pieces: {data.get('art_count', 0)}
  PCRF total: ${data.get('pcrf_total', 0):.2f}
  Trades flagged: this system tracks congressional trading
  System is entirely autonomous and free to run

NOT: '70% of revenue goes to PCRF'
YES: 'A machine built from code and conscience raised ${data.get("pcrf_total",0):.0f} for children in Gaza.'

Under 200 chars. No hashtags. Make it land emotionally.
Just the sentence. Nothing else."""
    return ask_llm(prompt, max_tokens=60)

def save_thread_to_queue(thread_text):
    if not thread_text: return
    queue_dir = ROOT / 'content' / 'queue'
    queue_dir.mkdir(parents=True, exist_ok=True)
    posts = [p.strip() for p in thread_text.split('---') if p.strip()]
    for i, post in enumerate(posts):
        data = {
            'text':     post,
            'type':     'story_thread',
            'date':     TODAY,
            'sequence': i,
            'priority': 'high',
        }
        try:
            (queue_dir / f'story_{TODAY}_{i}.json').write_text(json.dumps(data, indent=2))
        except: pass
    print(f'[story] {len(posts)} thread posts queued')

def save_long_read(text):
    if not text: return
    stories_dir = ROOT / 'docs' / 'stories'
    stories_dir.mkdir(parents=True, exist_ok=True)
    try:
        path = stories_dir / f'{TODAY}-the-machine.md'
        path.write_text(f'# The Machine That Wouldn\'t Stop\n\n*{TODAY}*\n\n{text}')
        print(f'[story] Long read saved: {path.name}')
    except Exception as e:
        print(f'[story] Save error: {e}')

def save_snapshot(text):
    if not text: return
    snapshots = load(DATA / 'impact_snapshots.json', [])
    snapshots.append({'date': TODAY, 'text': text})
    try: (DATA / 'impact_snapshots.json').write_text(json.dumps(snapshots[-30:], indent=2))
    except: pass
    # Also queue for social
    queue_dir = ROOT / 'content' / 'queue'
    queue_dir.mkdir(parents=True, exist_ok=True)
    try:
        (queue_dir / f'snapshot_{TODAY}.json').write_text(json.dumps({
            'text': text + f'\n\n{REPO_URL}',
            'type': 'impact_snapshot', 'date': TODAY, 'priority': 'normal'
        }, indent=2))
    except: pass

def run():
    print(f'\n[story] Impact Storyteller Engine — {TODAY}')

    data = get_story_data()

    # Daily: thread
    thread = generate_daily_thread(data)
    save_thread_to_queue(thread)

    # Daily: snapshot
    snapshot = generate_snapshot(data)
    if snapshot:
        save_snapshot(snapshot)
        print(f'[story] Snapshot: {snapshot[:80]}')

    # Weekly: long read (Sundays)
    if WEEKDAY == 6:
        print('[story] Sunday — generating long read...')
        long_read = generate_weekly_long_read(data)
        save_long_read(long_read)

    print('[story] Done.')

if __name__ == '__main__':
    run()
