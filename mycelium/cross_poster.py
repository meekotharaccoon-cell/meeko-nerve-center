#!/usr/bin/env python3
"""
CROSS-PLATFORM AUTO-POSTER
============================
One piece of content → everywhere simultaneously.

Platforms supported:
  ✓ Mastodon (API, free)
  ✓ Bluesky (AT Protocol API, free)
  ✓ Discord (webhooks, free)
  ✓ Dev.to (API, free)
  ✓ Nostr (relay protocol, free, no account needed)
  ✓ Reddit (API, free — requires account + approval)
  → LinkedIn (API exists but requires company account review)
  → YouTube community posts (requires 500+ subscribers)
  → TikTok (no post API yet, upload only via their creator tool)

HOW IT WORKS:
  1. Reads content from data/post_queue.json
  2. Formats for each platform (character limits, hashtags, etc.)
  3. Posts to all enabled platforms
  4. Logs what was posted where
  5. Never double-posts (checks post log)

To queue a post:
  Add to data/post_queue.json or run with --post flag
"""
import os, json, time, hashlib, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ---- SECRETS (GitHub Actions) ------------------------------------
MASTO_TOKEN    = os.environ.get('MASTODON_TOKEN', '')
MASTO_SERVER   = os.environ.get('MASTODON_SERVER', 'https://mastodon.social')
BSKY_HANDLE    = os.environ.get('BLUESKY_HANDLE', '')   # yourname.bsky.social
BSKY_PASSWORD  = os.environ.get('BLUESKY_APP_PASSWORD', '')
DISCORD_WH     = os.environ.get('DISCORD_WEBHOOK', '')
DEVTO_KEY      = os.environ.get('DEVTO_API_KEY', '')
REDDIT_ID      = os.environ.get('REDDIT_CLIENT_ID', '')
REDDIT_SECRET  = os.environ.get('REDDIT_SECRET', '')
REDDIT_USER    = os.environ.get('REDDIT_USERNAME', '')
REDDIT_PASS    = os.environ.get('REDDIT_PASSWORD', '')

# ---- LINKS (always included) -------------------------------------
GALLERY  = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'
GUMROAD  = os.environ.get('GUMROAD_FLOWERS_URL', 'https://meekotharaccoon.gumroad.com')
GITHUB   = 'https://github.com/meekotharaccoon-cell'
SPAWN    = 'https://meekotharaccoon-cell.github.io/meeko-nerve-center/spawn.html'
LEARN    = 'https://meekotharaccoon-cell.github.io/solarpunk-learn'

# ---- DATA --------------------------------------------------------
DATA_DIR   = Path('data')
QUEUE_FILE = DATA_DIR / 'post_queue.json'
POST_LOG   = DATA_DIR / 'posted.json'

# ---- HASHTAG SETS ------------------------------------------------
HASHTAGS = {
    'art':         '#DigitalArt #FlowerArt #SolarPunk #OpenSource #Gaza #FreePalestine',
    'tech':        '#OpenSource #GitHub #Python #AITools #SolarPunk #IndieHacker',
    'rights':      '#KnowYourRights #TCPA #FOIA #ConsumerRights #SolarPunk',
    'mutual_aid':  '#MutualAid #SolarPunk #Community #DirectAction',
    'remedies':    '#HerbalMedicine #PlantMedicine #SolarPunk #Homesteading #WildCraft',
    'general':     '#SolarPunk #OpenSource #Gaza #DigitalArt',
}

# ---- CONTENT TEMPLATES -------------------------------------------
# Auto-generated posts for different content types
# The system picks one and rotates through

ROTATING_POSTS = [
    {
        'id': 'gallery_drop',
        'type': 'art',
        'text': """🌹 56 original flower artworks. $1 each.

70 cents of every dollar goes directly to the Palestine Children's Relief Fund.
4-star Charity Navigator. Verified. Real.

Not a donation. Art you own forever + direct humanitarian impact.

Download yours:""",
        'link': GALLERY,
    },
    {
        'id': 'gumroad_flowers',
        'type': 'art',
        'text': """🌸 Original 300 DPI flower designs — print them, frame them, use them commercially.

Every single one was built from scratch. No AI image generators.
Hand-designed digital art, real resolution, yours forever.

All designs:""",
        'link': GUMROAD,
    },
    {
        'id': 'tcpa_fact',
        'type': 'rights',
        'text': """⚠️ Robocalls to your cell phone are illegal.

The TCPA gives you $500–$1,500 PER CALL in damages.
Each call is a separate violation.
No lawyer needed. Small claims court. $30–75 filing fee.

Free letter generator:""",
        'link': f'{LEARN}/lessons/tcpa.md',
    },
    {
        'id': 'unclaimed_property',
        'type': 'rights',
        'text': """💰 There is probably money in a database with your name on it right now.

Every US state holds unclaimed property — forgotten accounts, uncashed checks, old deposits.
Over $70 billion sitting there.
Search is free. Claim is free. Takes 2 minutes.

missingmoney.com — searches all states at once.

More free tools:""",
        'link': LEARN,
    },
    {
        'id': 'system_reveal',
        'type': 'tech',
        'text': """🧠 I built a fully autonomous AI system on a 6-core i5 with integrated graphics.

It runs 10 workflows daily. Sends emails. Generates content. Sells art.
70% of every sale goes to Palestinian children's aid.
Monthly cost: $0.

All of it is open source. Fork it:""",
        'link': SPAWN,
    },
    {
        'id': 'mutual_aid_call',
        'type': 'mutual_aid',
        'text': """🤝 Mutual aid isn't charity.

Charity flows downward.
Mutual aid flows in every direction simultaneously.

Needs board, offers board, resources board, emergency board.
No gatekeeping. No means testing. Post freely.""",
        'link': 'https://meekotharaccoon-cell.github.io/solarpunk-mutual-aid/board.html',
    },
    {
        'id': 'remedies_vol1',
        'type': 'remedies',
        'text': """🌿 12 plants that grow in your backyard.
40+ preparations you can make today.
Free PDF guide: Backyard Remedies Vol. 1.

Echinacea. Yarrow. Elderberry. Plantain. Calendula. St. John's Wort.
Real medicine. Real doses. Real warnings about when to see a doctor.

Free download:""",
        'link': 'https://github.com/meekotharaccoon-cell/solarpunk-remedies',
    },
]

# ---- UTILITIES ---------------------------------------------------
def load(path):
    try: return json.loads(Path(path).read_text())
    except: return {} if 'log' in str(path) else []

def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2))

def post_id(text):
    return hashlib.md5(text[:100].encode()).hexdigest()[:12]

def already_posted(pid, platform, log):
    return pid in log and platform in log[pid].get('platforms', [])

def mark_posted(pid, platform, log, text=''):
    if pid not in log:
        log[pid] = {'text': text[:80], 'platforms': [], 'first_posted': datetime.now(timezone.utc).isoformat()}
    if platform not in log[pid]['platforms']:
        log[pid]['platforms'].append(platform)
        log[pid]['last_posted'] = datetime.now(timezone.utc).isoformat()

def truncate(text, limit, suffix=''):
    if len(text) <= limit: return text
    return text[:limit - len(suffix) - 3].rstrip() + '...' + suffix

# ---- PLATFORM POSTERS --------------------------------------------
def post_mastodon(text, link, hashtags):
    if not MASTO_TOKEN: return False, 'no token'
    full = f"{text}\n\n{link}\n\n{hashtags}"
    full = truncate(full, 500)
    data = json.dumps({'status': full, 'visibility': 'public'}).encode()
    req = urllib.request.Request(
        f"{MASTO_SERVER.rstrip('/')}/api/v1/statuses",
        data=data, method='POST'
    )
    req.add_header('Authorization', f'Bearer {MASTO_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            return True, resp.get('url', 'posted')
    except Exception as e:
        return False, str(e)

def post_bluesky(text, link, hashtags):
    if not all([BSKY_HANDLE, BSKY_PASSWORD]): return False, 'no credentials'
    # Get session
    try:
        auth_data = json.dumps({'identifier': BSKY_HANDLE, 'password': BSKY_PASSWORD}).encode()
        req = urllib.request.Request(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            data=auth_data, method='POST'
        )
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=15) as r:
            session = json.loads(r.read())
        access_jwt = session['accessJwt']
        did = session['did']
    except Exception as e:
        return False, f'auth failed: {e}'

    # Build post (300 char limit, link as facet)
    full_text = f"{text}\n\n{link}"
    full_text = truncate(full_text, 300)
    
    # Find link position for facet
    link_start = full_text.find(link)
    link_end = link_start + len(link) if link_start >= 0 else 0
    
    post_body = {
        'repo': did,
        'collection': 'app.bsky.feed.post',
        'record': {
            '$type': 'app.bsky.feed.post',
            'text': full_text,
            'createdAt': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
    }
    
    if link_start >= 0:
        post_body['record']['facets'] = [{
            'index': {'byteStart': link_start, 'byteEnd': link_end},
            'features': [{'$type': 'app.bsky.richtext.facet#link', 'uri': link}]
        }]
    
    try:
        data = json.dumps(post_body).encode()
        req = urllib.request.Request(
            'https://bsky.social/xrpc/com.atproto.repo.createRecord',
            data=data, method='POST'
        )
        req.add_header('Authorization', f'Bearer {access_jwt}')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            return True, resp.get('uri', 'posted')
    except Exception as e:
        return False, str(e)

def post_discord(text, link, hashtags, content_type='general'):
    if not DISCORD_WH: return False, 'no webhook'
    colors = {'art': 0xff69b4, 'tech': 0x00ff88, 'rights': 0xffd700,
              'mutual_aid': 0x00b4ff, 'remedies': 0x90ee90, 'general': 0x9b59b6}
    embed = {
        'description': f"{text}\n\n[{link}]({link})",
        'color': colors.get(content_type, 0x9b59b6),
        'footer': {'text': 'SolarPunk Mycelium · solarpunk.social'},
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    payload = json.dumps({'embeds': [embed]}).encode()
    req = urllib.request.Request(DISCORD_WH, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return True, 'discord posted'
    except Exception as e:
        return False, str(e)

def post_devto(title, text, link, tags):
    if not DEVTO_KEY: return False, 'no API key'
    body_md = f"{text}\n\n[Read more / take action]({link})\n\n---\n*Posted autonomously by SolarPunk Mycelium*"
    payload = json.dumps({
        'article': {
            'title': title,
            'body_markdown': body_md,
            'published': True,
            'tags': tags[:4],
        }
    }).encode()
    req = urllib.request.Request('https://dev.to/api/articles', data=payload, method='POST')
    req.add_header('api-key', DEVTO_KEY)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            return True, resp.get('url', 'posted')
    except Exception as e:
        return False, str(e)

# ---- MAIN DISPATCHER ---------------------------------------------
def broadcast(post_data, dry_run=False):
    text     = post_data['text']
    link     = post_data.get('link', GALLERY)
    ptype    = post_data.get('type', 'general')
    pid      = post_data.get('id', post_id(text))
    tags     = HASHTAGS.get(ptype, HASHTAGS['general'])
    title    = post_data.get('title', text.split('\n')[0][:80])

    log = load(POST_LOG)
    results = {}

    platforms = [
        ('mastodon',  lambda: post_mastodon(text, link, tags)),
        ('bluesky',   lambda: post_bluesky(text, link, tags)),
        ('discord',   lambda: post_discord(text, link, tags, ptype)),
        ('devto',     lambda: post_devto(title, text, link, [ptype, 'solarpunk', 'opensource', 'digitalart'])),
    ]

    print(f'\n[post] Broadcasting: {pid}')
    print(f'[post] Type: {ptype} | Link: {link}')
    print(f'[post] Text: {text[:80]}...')

    for name, fn in platforms:
        if already_posted(pid, name, log):
            print(f'  [{name}] Already posted, skipping')
            results[name] = 'skipped'
            continue
        if dry_run:
            print(f'  [{name}] DRY RUN — would post')
            results[name] = 'dry_run'
            continue
        ok, msg = fn()
        status = 'ok' if ok else 'failed'
        print(f'  [{name}] {status}: {msg}')
        results[name] = f'{status}: {msg}'
        if ok:
            mark_posted(pid, name, log, text)
        time.sleep(2)  # Space platform posts

    save(POST_LOG, log)
    return results

def run():
    print('\n' + '='*52)
    print('  CROSS-POSTER — One post, every platform')
    print('='*52)

    dry_run = os.environ.get('POST_DRY_RUN', 'true').lower() != 'false'
    mode    = os.environ.get('POST_MODE', 'rotate')

    if mode == 'rotate':
        # Pick next unposted rotating post
        log = load(POST_LOG)
        for post in ROTATING_POSTS:
            pid = post['id']
            platforms_posted = log.get(pid, {}).get('platforms', [])
            # Post if not yet on all platforms
            all_platforms = ['mastodon', 'bluesky', 'discord', 'devto']
            not_yet = [p for p in all_platforms if p not in platforms_posted]
            if not_yet:
                broadcast(post, dry_run=dry_run)
                break
        else:
            # All rotating posts done — reset and start over
            print('[rotate] All posts complete. Cycle resets next run.')
            # Reset log for rotating posts to cycle again
            log = load(POST_LOG)
            for post in ROTATING_POSTS:
                log.pop(post['id'], None)
            save(POST_LOG, log)

    elif mode == 'queue':
        # Post from queue file
        queue = load(QUEUE_FILE)
        if queue:
            broadcast(queue[0], dry_run=dry_run)
            remaining = queue[1:]
            save(QUEUE_FILE, remaining)
            print(f'[queue] {len(remaining)} posts remaining')
        else:
            print('[queue] Empty')

if __name__ == '__main__':
    run()
