#!/usr/bin/env python3
"""
Humanitarian Content Engine — Strategy-Aware Version

Reads data/strategy.json (from loop_brain.py) and weights post
generation toward what the signals say is actually working.

If no strategy file exists, uses sensible defaults.

Crises covered: Gaza, Congo (DRC), Sudan
Revenue paths: gallery ($1 art), fork guide ($5), Ko-fi tips, GitHub Sponsors
"""

import os, json, datetime, random
from pathlib import Path

ROOT     = Path(__file__).parent.parent
KB       = ROOT / 'knowledge'
CONTENT  = ROOT / 'content'
DATA     = ROOT / 'data'
TODAY    = datetime.date.today().isoformat()

CONTENT.mkdir(exist_ok=True)
(CONTENT / 'queue').mkdir(exist_ok=True)
(CONTENT / 'archive').mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)

# ── Load strategy ──────────────────────────────────────────────────────────
strategy_path = DATA / 'strategy.json'
strategy = {}
if strategy_path.exists():
    try:
        strategy = json.loads(strategy_path.read_text(encoding='utf-8'))
        print(f'  [content] Strategy loaded: {strategy.get("method","?")}')
        print(f'  [content] Primary crisis: {strategy.get("primary_crisis","?")} | Channel: {strategy.get("push_channel","?")}' )
    except Exception:
        pass

if not strategy:
    print('  [content] No strategy file — using defaults')
    strategy = {
        'primary_crisis': 'Gaza',
        'all_crises':     ['Gaza', 'Congo (DRC)', 'Sudan'],
        'post_weights':   {'awareness': 2, 'gallery': 3, 'fork': 2, 'info': 1, 'punchy': 2},
        'push_channel':   'gallery',
        'knowledge_hook': '',
    }

PRIMARY   = strategy.get('primary_crisis', 'Gaza')
ALL_CRISES= strategy.get('all_crises', ['Gaza', 'Congo (DRC)', 'Sudan'])
WEIGHTS   = strategy.get('post_weights', {})
CHANNEL   = strategy.get('push_channel', 'gallery')
HOOK      = strategy.get('knowledge_hook', '')

# ── Load knowledge digest for hook injection ───────────────────────────────
digest_text = ''
if (KB / 'LATEST_DIGEST.md').exists():
    digest_text = (KB / 'LATEST_DIGEST.md').read_text(encoding='utf-8')[:500]

# ── Crisis definitions ─────────────────────────────────────────────────────
CRISES = [
    {
        'name': 'Gaza',
        'context': 'Over 40,000 killed. 2 million displaced. Ongoing siege.',
        'action': "Palestine Children's Relief Fund (PCRF) — 4-star Charity Navigator",
        'action_url': 'https://www.pcrf.net',
        'gallery_url': 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery',
        'gallery_note': '70% of every $1 art sale goes directly to PCRF',
        'hashtags': ['#Gaza', '#Palestine', '#PCRF', '#FreePalestine', '#SolarpunkMycelium'],
    },
    {
        'name': 'Congo (DRC)',
        'context': 'Eastern DRC — millions displaced, worst humanitarian crisis in Africa.',
        'action': 'International Rescue Committee · Doctors Without Borders',
        'action_url': 'https://www.rescue.org',
        'gallery_url': 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery',
        'gallery_note': 'Support this system — proceeds fund humanitarian causes',
        'hashtags': ['#DRC', '#Congo', '#EasternCongo', '#HumanitarianCrisis', '#SolarpunkMycelium'],
    },
    {
        'name': 'Sudan',
        'context': 'Sudan civil war — 8M+ displaced, largest displacement crisis in the world.',
        'action': 'UNHCR Sudan · Save the Children Sudan',
        'action_url': 'https://www.unhcr.org/sudan',
        'gallery_url': 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery',
        'gallery_note': 'Support this system — proceeds fund humanitarian causes',
        'hashtags': ['#Sudan', '#SudanCrisis', '#Darfur', '#HumanitarianAid', '#SolarpunkMycelium'],
    },
]

# Put primary crisis first
CRISES.sort(key=lambda c: (0 if c['name'] == PRIMARY else 1))

# ── Channel-specific CTAs ──────────────────────────────────────────────────
CHANNEL_CTA = {
    'gallery':    ('→ $1 art, 70% to relief: ', 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'),
    'kofi':       ('→ Ko-fi tip jar (no fees): ', 'https://ko-fi.com/meekotharaccoon'),
    'fork_guide': ('→ $5 fork guide (build your own): ', 'https://gumroad.com/meekotharaccoon'),
    'sponsor':    ('→ GitHub Sponsors: ', 'https://github.com/sponsors/meekotharaccoon-cell'),
}
cta_label, cta_url = CHANNEL_CTA.get(CHANNEL, CHANNEL_CTA['gallery'])

# ── Post template factory ──────────────────────────────────────────────────
def make_posts(crisis: dict) -> dict:
    """Returns dict of {template_name: post_text} for this crisis."""
    name  = crisis['name']
    ctx   = crisis['context']
    act   = crisis['action']
    url   = crisis['action_url']
    gurl  = crisis['gallery_url']
    gnote = crisis['gallery_note']
    tags  = ' '.join(crisis['hashtags'][:3])

    hook_line = f'\n\nToday in open-source: {HOOK}' if HOOK else ''

    return {
        'awareness': (
            f"{name}: {ctx}\n\n"
            f"This is happening now. Direct action:\n"
            f"{act}\n{url}\n\n"
            f"{tags} #DirectAction"
        ),
        'gallery': (
            f"56 original artworks. $1 each. {gnote}.\n\n"
            f"Every sale funds {name} relief directly — no middlemen.\n"
            f"{cta_label}{cta_url}\n\n"
            f"{tags} #Art #OpenSource"
        ),
        'fork': (
            f"A self-replicating autonomous AI. $0/month to run.\n"
            f"Anyone can fork it and aim it at any cause.\n\n"
            f"Current mission: {name}.\n"
            f"Fork it: https://github.com/meekotharaccoon-cell/meeko-nerve-center\n\n"
            f"{tags} #FOSS #Solarpunk"
        ),
        'info': (
            f"{name} crisis: {ctx}\n\n"
            f"How to help:\n"
            f"· {act}: {url}\n"
            f"· Buy $1 art → {gnote}: {gurl}\n"
            f"· Fork this system: github.com/meekotharaccoon-cell{hook_line}\n\n"
            f"{tags}"
        ),
        'punchy': (
            f"$1. One dollar.\n"
            f"Original art. 70% to {name} relief.\n"
            f"Zero middlemen. Zero corporate cut.\n"
            f"{gurl}\n\n"
            f"{tags} #DirectAction"
        ),
    }

# ── Build weighted queue ───────────────────────────────────────────────────
queue = []

for crisis in CRISES:
    templates = make_posts(crisis)
    # Primary crisis gets full weight, others get 1 post each (variety)
    is_primary = (crisis['name'] == PRIMARY)

    for tname, text in templates.items():
        weight = WEIGHTS.get(tname, 1) if is_primary else 1
        for _ in range(weight):
            queue.append({
                'crisis':    crisis['name'],
                'template':  tname,
                'primary':   is_primary,
                'channel':   CHANNEL,
                'text':      text,
                'char_len':  len(text),
                'platforms': ['mastodon', 'bluesky'],
                'generated': TODAY,
                'status':    'queued',
                'strategy':  strategy.get('method', 'default'),
            })

random.shuffle(queue)
print(f'  [content] {len(queue)} posts generated | primary={PRIMARY} | channel={CHANNEL}')

# ── Save queue ─────────────────────────────────────────────────────────────
(CONTENT / 'queue' / f'{TODAY}.json').write_text(
    json.dumps(queue, indent=2), encoding='utf-8')
(CONTENT / 'queue' / 'latest.json').write_text(
    json.dumps(queue, indent=2), encoding='utf-8')

# ── Post to Mastodon ───────────────────────────────────────────────────────
import urllib.request
MASTODON_TOKEN = os.environ.get('MASTODON_TOKEN', '').strip()
MASTODON_URL   = os.environ.get('MASTODON_URL', 'https://mastodon.social').strip()

if MASTODON_TOKEN:
    posted = 0
    # Post one per crisis (max 3/day so we don't spam)
    seen_crises = set()
    for item in queue:
        if item['crisis'] in seen_crises: continue
        if posted >= 3: break
        text = item['text']
        if len(text) > 500: text = text[:497] + '…'
        try:
            payload = json.dumps({'status': text, 'visibility': 'public'}).encode()
            req = urllib.request.Request(
                f"{MASTODON_URL}/api/v1/statuses",
                data=payload,
                headers={'Authorization': f'Bearer {MASTODON_TOKEN}',
                         'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read())
                item['status'] = 'posted_mastodon'
                item['post_url'] = resp.get('url', '')
                print(f'  [mastodon] {item["crisis"]}: {resp.get("url","posted")}')
                seen_crises.add(item['crisis'])
                posted += 1
        except Exception as e:
            print(f'  [mastodon] Error: {e}')
else:
    print('  [mastodon] No token — posts queued only')

# ── Post to Bluesky ────────────────────────────────────────────────────────
BSKY_HANDLE = os.environ.get('BLUESKY_HANDLE', '').strip()
BSKY_PASS   = os.environ.get('BLUESKY_APP_PASSWORD', '').strip()

if BSKY_HANDLE and BSKY_PASS:
    try:
        auth = json.dumps({'identifier': BSKY_HANDLE, 'password': BSKY_PASS}).encode()
        req  = urllib.request.Request(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            data=auth, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as r:
            session = json.loads(r.read())
        token = session['accessJwt']
        did   = session['did']

        seen_crises = set()
        for item in queue:
            if item['crisis'] in seen_crises: continue
            text = item['text']
            if len(text) > 300: text = text[:297] + '…'
            now_iso = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            payload = json.dumps({'repo': did, 'collection': 'app.bsky.feed.post',
                                  'record': {'$type': 'app.bsky.feed.post',
                                             'text': text, 'createdAt': now_iso}}).encode()
            req = urllib.request.Request(
                'https://bsky.social/xrpc/com.atproto.repo.createRecord',
                data=payload,
                headers={'Authorization': f'Bearer {token}',
                         'Content-Type': 'application/json'},
                method='POST')
            with urllib.request.urlopen(req, timeout=15) as r:
                json.loads(r.read())
                print(f'  [bluesky] {item["crisis"]}: posted')
                seen_crises.add(item['crisis'])
            if len(seen_crises) >= 3: break
    except Exception as e:
        print(f'  [bluesky] Error: {e}')
else:
    print('  [bluesky] No credentials — posts queued only')

# ── Update queue with final statuses ──────────────────────────────────────
(CONTENT / 'queue' / f'{TODAY}.json').write_text(
    json.dumps(queue, indent=2), encoding='utf-8')
(CONTENT / 'queue' / 'latest.json').write_text(
    json.dumps(queue, indent=2), encoding='utf-8')

# ── Human-readable archive ─────────────────────────────────────────────────
lines = [
    f'# Humanitarian Content — {TODAY}',
    f'*Strategy: {strategy.get("method","default")} | Primary: {PRIMARY} | Channel: {CHANNEL}*',
    f'*Reasoning: {strategy.get("reasoning","defaults")}*', '',
    f'{len(queue)} posts generated', '',
]
for crisis in CRISES:
    lines += [f'## {crisis["name"]}', '']
    for item in [q for q in queue if q['crisis']==crisis['name']][:2]:
        lines += [f'**[{item["template"]}]** status: {item["status"]}',
                  '```', item['text'], '```', '']

(CONTENT / 'archive' / f'{TODAY}.md').write_text('\n'.join(lines), encoding='utf-8')
(CONTENT / 'latest.md').write_text('\n'.join(lines), encoding='utf-8')

print(f'\n  Done. content/queue/latest.json ready.')
