#!/usr/bin/env python3
"""
Social Engine
==============
Cross-posts content queue to Bluesky and Mastodon.
Reads from content/queue/*.json and posts automatically.

Secrets needed (already set):
  BLUESKY_HANDLE        your Bluesky handle e.g. yourname.bsky.social
  BLUESKY_PASSWORD      your Bluesky app password
  MASTODON_KEY          Mastodon app client key
  MASTODON_SECRET       Mastodon app client secret
  MASTODON_TOKEN        Mastodon access token
  MASTODON_BASE_URL     your Mastodon instance e.g. https://mastodon.social

Content queue format (content/queue/*.json):
  [
    {"platform": "all", "type": "cause", "text": "..."},
    {"platform": "mastodon", "type": "word", "text": "..."}
  ]

Posted items get marked posted:true so they don't re-send.
"""

import json, datetime, os, time
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode

ROOT    = Path(__file__).parent.parent
CONTENT = ROOT / 'content' / 'queue'
DATA    = ROOT / 'data'
TODAY   = datetime.date.today().isoformat()

BLUESKY_HANDLE   = os.environ.get('BLUESKY_HANDLE', '')
BLUESKY_PASSWORD = os.environ.get('BLUESKY_PASSWORD', '')
MASTODON_TOKEN   = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')

# ── Bluesky ────────────────────────────────────────────────────────────────────

def bluesky_login():
    if not BLUESKY_HANDLE or not BLUESKY_PASSWORD:
        return None, None
    try:
        payload = json.dumps({'identifier': BLUESKY_HANDLE, 'password': BLUESKY_PASSWORD}).encode()
        req = urllib_request.Request(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            data=payload, headers={'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            return data.get('accessJwt'), data.get('did')
    except Exception as e:
        print(f'[social] Bluesky login failed: {e}')
        return None, None

def bluesky_post(text, token, did):
    if not token: return False
    # Truncate to 300 chars (Bluesky limit)
    if len(text) > 300:
        text = text[:297] + '...'
    try:
        payload = json.dumps({
            'repo':       did,
            'collection': 'app.bsky.feed.post',
            'record': {
                '$type':     'app.bsky.feed.post',
                'text':      text,
                'createdAt': datetime.datetime.utcnow().isoformat() + 'Z'
            }
        }).encode()
        req = urllib_request.Request(
            'https://bsky.social/xrpc/com.atproto.repo.createRecord',
            data=payload,
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
        )
        urllib_request.urlopen(req, timeout=15)
        print(f'[social] Bluesky: posted ({len(text)} chars)')
        return True
    except Exception as e:
        print(f'[social] Bluesky post failed: {e}')
        return False

# ── Mastodon ───────────────────────────────────────────────────────────────────

def mastodon_post(text):
    if not MASTODON_TOKEN: return False
    # Truncate to 500 chars (Mastodon limit)
    if len(text) > 500:
        text = text[:497] + '...'
    try:
        payload = urlencode({'status': text, 'visibility': 'public'}).encode()
        req = urllib_request.Request(
            f'{MASTODON_BASE_URL.rstrip("/")}/api/v1/statuses',
            data=payload,
            headers={
                'Authorization': f'Bearer {MASTODON_TOKEN}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        urllib_request.urlopen(req, timeout=15)
        print(f'[social] Mastodon: posted ({len(text)} chars)')
        return True
    except Exception as e:
        print(f'[social] Mastodon post failed: {e}')
        return False

# ── Content queue ──────────────────────────────────────────────────────────────

def load_queue_files():
    """Load all unposted content from content/queue/."""
    CONTENT.mkdir(parents=True, exist_ok=True)
    items = []
    for f in sorted(CONTENT.glob('*.json')):
        try:
            data = json.loads(f.read_text())
            if isinstance(data, list):
                for item in data:
                    item['_file'] = str(f)
                    items.append(item)
            elif isinstance(data, dict):
                data['_file'] = str(f)
                items.append(data)
        except:
            pass
    return items

def mark_posted(item):
    """Mark item as posted in its source file."""
    try:
        f = Path(item['_file'])
        data = json.loads(f.read_text())
        if isinstance(data, list):
            for entry in data:
                if entry.get('text') == item.get('text'):
                    entry['posted'] = TODAY
        elif isinstance(data, dict):
            data['posted'] = TODAY
        f.write_text(json.dumps(data, indent=2))
    except:
        pass

def run():
    print(f'[social] Social Engine — {TODAY}')

    items = load_queue_files()
    unposted = [i for i in items if not i.get('posted')]
    print(f'[social] {len(unposted)} unposted items found')

    if not unposted:
        print('[social] Nothing to post today')
        return

    # Login to Bluesky once
    bsky_token, bsky_did = bluesky_login()
    if bsky_token:
        print('[social] Bluesky logged in')
    else:
        print('[social] Bluesky not available')

    if MASTODON_TOKEN:
        print('[social] Mastodon ready')
    else:
        print('[social] Mastodon not available')

    posted = 0
    # Post max 3 items per run to avoid spam
    for item in unposted[:3]:
        text     = item.get('text', '')
        platform = item.get('platform', 'all').lower()
        if not text:
            continue

        success = False
        if platform in ('all', 'bluesky') and bsky_token:
            if bluesky_post(text, bsky_token, bsky_did):
                success = True
                time.sleep(2)  # be polite to API

        if platform in ('all', 'mastodon') and MASTODON_TOKEN:
            if mastodon_post(text):
                success = True
                time.sleep(2)

        if success:
            mark_posted(item)
            posted += 1

    print(f'[social] Done. Posted {posted} items.')
    return posted

if __name__ == '__main__':
    run()
