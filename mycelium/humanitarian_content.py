#!/usr/bin/env python3
"""
Humanitarian Content Engine

Reads the daily knowledge harvest and generates:
  1. Social posts (Mastodon/Bluesky) that raise awareness + drive traffic
  2. Content linking crises (Gaza, Congo, Sudan) to real action (gallery, donations)
  3. A daily content_queue.json other workflows can consume

No API keys required for generation. Mastodon/Bluesky posting uses
existing secrets when available.
"""

import os, json, datetime, random
from pathlib import Path

ROOT    = Path(__file__).parent.parent
KB      = ROOT / 'knowledge'
CONTENT = ROOT / 'content'
TODAY   = datetime.date.today().isoformat()

CONTENT.mkdir(exist_ok=True)
(CONTENT / 'queue').mkdir(exist_ok=True)
(CONTENT / 'archive').mkdir(exist_ok=True)

# ── Load latest knowledge ──────────────────────────────────────────────────
digest = ''
latest = KB / 'LATEST_DIGEST.md'
if latest.exists():
    digest = latest.read_text(encoding='utf-8')[:2000]

github_json = KB / 'github' / 'latest.json'
gh_repos = []
if github_json.exists():
    try:
        gh_repos = json.loads(github_json.read_text())[:5]
    except Exception:
        pass

# ── Crisis context ─────────────────────────────────────────────────────────
CRISES = [
    {
        'name': 'Gaza',
        'context': 'Over 40,000 killed. 2 million displaced. Ongoing siege.',
        'action': 'Palestine Children\'s Relief Fund (PCRF) — 4-star Charity Navigator · EIN 93-1057665',
        'action_url': 'https://www.pcrf.net',
        'gallery_url': 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery',
        'gallery_note': '70% of every $1 art sale goes directly to PCRF',
        'hashtags': ['#Gaza', '#Palestine', '#PCRF', '#GazaGenocide', '#FreePalestine'],
    },
    {
        'name': 'Congo (DRC)',
        'context': 'Eastern DRC conflict — millions displaced, worst humanitarian crisis in Africa.',
        'action': 'International Rescue Committee · Doctors Without Borders · UNICEF DRC',
        'action_url': 'https://www.rescue.org',
        'gallery_url': 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery',
        'gallery_note': 'Support this system — proceeds fund humanitarian causes',
        'hashtags': ['#DRC', '#Congo', '#EasternCongo', '#M23', '#HumanitarianCrisis'],
    },
    {
        'name': 'Sudan',
        'context': 'Sudan civil war — 8+ million displaced, largest displacement crisis in the world.',
        'action': 'UNHCR Sudan · Save the Children Sudan',
        'action_url': 'https://www.unhcr.org/sudan',
        'gallery_url': 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery',
        'gallery_note': 'Support this system — proceeds fund humanitarian causes',
        'hashtags': ['#Sudan', '#SudanWar', '#SudanCrisis', '#Khartoum', '#Darfur'],
    },
]

# ── Template library ───────────────────────────────────────────────────────
# Each template rotates. Long enough to be real, short enough to post.

def make_posts(crisis: dict) -> list:
    name = crisis['name']
    ctx  = crisis['context']
    act  = crisis['action']
    url  = crisis['action_url']
    gurl = crisis['gallery_url']
    gnote= crisis['gallery_note']
    tags = ' '.join(crisis['hashtags'][:3])

    posts = [
        # Awareness + action
        f"{name}: {ctx}\n\nThis is happening right now.\n\n"
        f"Direct action: {act}\n{url}\n\n"
        f"{tags} #SolarpunkMycelium",

        # Gallery-linked
        f"A self-replicating AI system built on free infrastructure.\n"
        f"56 original artworks · $1 each · {gnote}.\n\n"
        f"Every sale is a vote for people over profit.\n"
        f"{gurl}\n\n"
        f"{tags} #OpenSource #Solarpunk",

        # Fork/replicate call to action
        f"This system runs itself 24/7 at $0/month.\n"
        f"Anyone can fork it and aim it at any cause.\n\n"
        f"Current mission: raise money for {name}.\n"
        f"Code: https://github.com/meekotharaccoon-cell/meeko-nerve-center\n\n"
        f"{tags} #FOSS #AutonomousAI",

        # Informational + link
        f"{name} crisis update: {ctx}\n\n"
        f"Ways to help:\n"
        f"· {act}\n"
        f"· Buy $1 art → {gnote}: {gurl}\n"
        f"· Fork this system, aim it at your cause: github.com/meekotharaccoon-cell\n\n"
        f"{tags}",

        # Short punchy
        f"$1. That's it. One dollar.\n"
        f"Buy original art. 70% goes to {name} relief.\n"
        f"Zero corporate middlemen.\n"
        f"{gurl}\n\n"
        f"{tags} #DirectAction",
    ]
    return posts


# ── Build content queue ────────────────────────────────────────────────────
queue = []
for crisis in CRISES:
    for post in make_posts(crisis):
        queue.append({
            'crisis':    crisis['name'],
            'text':      post,
            'char_len':  len(post),
            'platforms': ['mastodon', 'bluesky'],
            'generated': TODAY,
            'status':    'queued',
        })

# Shuffle so platforms see varied content
random.shuffle(queue)

# Save full queue
queue_path = CONTENT / 'queue' / f'{TODAY}.json'
queue_path.write_text(json.dumps(queue, indent=2), encoding='utf-8')

# Latest pointer (other workflows read this)
latest_queue = CONTENT / 'queue' / 'latest.json'
latest_queue.write_text(json.dumps(queue, indent=2), encoding='utf-8')

print(f'✓ Generated {len(queue)} posts for {len(CRISES)} crises')

# ── Post to Mastodon (if token present) ────────────────────────────────────
MASTODON_TOKEN = os.environ.get('MASTODON_TOKEN', '').strip()
MASTODON_URL   = os.environ.get('MASTODON_URL', 'https://mastodon.social').strip()

if MASTODON_TOKEN:
    try:
        import urllib.request
        # Post one item from each crisis per day (3 posts total)
        posted = 0
        for crisis in CRISES:
            crisis_posts = [q for q in queue if q['crisis'] == crisis['name']]
            if not crisis_posts: continue
            post = crisis_posts[0]  # first = most recently shuffled
            text = post['text']
            if len(text) > 500: text = text[:497] + '…'

            payload = json.dumps({'status': text,
                                  'visibility': 'public'}).encode()
            req = urllib.request.Request(
                f'{MASTODON_URL}/api/v1/statuses',
                data=payload,
                headers={'Authorization': f'Bearer {MASTODON_TOKEN}',
                         'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read())
                print(f'  ✓ Mastodon [{crisis["name"]}]: {resp.get("url","posted")}')
                post['status'] = 'posted_mastodon'
                posted += 1
    except Exception as e:
        print(f'  ✗ Mastodon error: {e}')
else:
    print('  ○ Mastodon: no token — posts queued, not sent')

# ── Post to Bluesky (if credentials present) ───────────────────────────────
BSKY_HANDLE = os.environ.get('BLUESKY_HANDLE', '').strip()
BSKY_PASS   = os.environ.get('BLUESKY_APP_PASSWORD', '').strip()

if BSKY_HANDLE and BSKY_PASS:
    try:
        import urllib.request
        # Auth
        auth_payload = json.dumps({'identifier': BSKY_HANDLE,
                                    'password': BSKY_PASS}).encode()
        req = urllib.request.Request(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            data=auth_payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            session = json.loads(r.read())
        token = session['accessJwt']
        did   = session['did']

        for crisis in CRISES:
            crisis_posts = [q for q in queue if q['crisis'] == crisis['name']]
            if not crisis_posts: continue
            post = crisis_posts[0]
            text = post['text']
            if len(text) > 300: text = text[:297] + '…'

            now_iso = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            record  = {'$type': 'app.bsky.feed.post',
                       'text': text, 'createdAt': now_iso}
            payload = json.dumps({'repo': did, 'collection': 'app.bsky.feed.post',
                                  'record': record}).encode()
            req = urllib.request.Request(
                'https://bsky.social/xrpc/com.atproto.repo.createRecord',
                data=payload,
                headers={'Authorization': f'Bearer {token}',
                         'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read())
                print(f'  ✓ Bluesky [{crisis["name"]}]: posted')
    except Exception as e:
        print(f'  ✗ Bluesky error: {e}')
else:
    print('  ○ Bluesky: no credentials — posts queued, not sent')

# ── Save updated queue with statuses ──────────────────────────────────────
queue_path.write_text(json.dumps(queue, indent=2), encoding='utf-8')
latest_queue.write_text(json.dumps(queue, indent=2), encoding='utf-8')

# ── Write human-readable summary ──────────────────────────────────────────
summary = [
    f'# Humanitarian Content — {TODAY}', '',
    f'*{len(queue)} posts generated for {len(CRISES)} crises*', '',
]
for crisis in CRISES:
    summary += [f"## {crisis['name']}", '', f"> {crisis['context']}", '']
    for p in [q for q in queue if q['crisis'] == crisis['name']][:2]:
        summary += ['```', p['text'], '```', '']

(CONTENT / 'archive' / f'{TODAY}.md').write_text(
    '\n'.join(summary), encoding='utf-8')
(CONTENT / 'latest.md').write_text(
    '\n'.join(summary), encoding='utf-8')

print(f'\n✅ Done. Content written to content/queue/latest.json')
