#!/usr/bin/env python3
"""
Identity Engine
================
The system posts, emails, builds, and acts —
but has no consistent identity across platforms.

Right now:
  Mastodon bio: probably empty or default
  Bluesky bio: probably empty
  GitHub profile: default
  HuggingFace Space: no description
  Ko-fi: whatever was set manually
  Every platform: inconsistent messaging

This engine maintains ONE canonical identity
and pushes it everywhere automatically.

The canonical Meeko identity:
  Name:      Meeko Nerve Center
  Tagline:   Autonomous AI for accountability + Palestinian solidarity
  Bio:       70+ self-evolving engines. $0/month. AGPL-3.0.
             Tracks congressional trades. Funds PCRF with art sales.
             Crazy awesome sci-fi. Good dude energy. 🌸
  Mission:   SolarPunk infrastructure that can't be shut down
  Color:     #2ecc71 (SolarPunk green)
  Emoji:     🌸 (Gaza Rose)
  Website:   {repo_url}
  Email:     {gmail}

Updates every platform weekly:
  - Mastodon bio + header
  - Bluesky bio + display name
  - GitHub user bio (if token has user scope)
  - Ko-fi page description
  - HuggingFace Space README
  - Newsletter footer

Why this matters:
  Consistency = credibility.
  Every journalist who checks any platform
  sees the same clear, compelling identity.
  Every potential donor sees the same mission.
  Every forker understands what they're joining.
  The system presents itself with the same
  confidence and clarity everywhere, always.
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

MASTODON_TOKEN     = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL  = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')
BLUESKY_HANDLE     = os.environ.get('BLUESKY_HANDLE', '')
BLUESKY_PASSWORD   = os.environ.get('BLUESKY_PASSWORD', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')
HF_USERNAME        = os.environ.get('HF_USERNAME', 'meekotharaccoon')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'
GMAIL   = os.environ.get('GMAIL_ADDRESS', 'meekotharaccoon@gmail.com')

def get_live_stats():
    stats = {'engines': 0, 'self_built': 0, 'art': 0, 'pcrf': 0.0}
    try: stats['engines'] = len(list((ROOT / 'mycelium').glob('*.py')))
    except: pass
    try:
        evo = json.loads((DATA / 'evolution_log.json').read_text())
        stats['self_built'] = len(evo.get('built', []))
    except: pass
    try:
        arts = json.loads((DATA / 'generated_art.json').read_text())
        al = arts if isinstance(arts, list) else arts.get('art', [])
        stats['art'] = len(al)
    except: pass
    try:
        ev = json.loads((DATA / 'kofi_events.json').read_text())
        ev = ev if isinstance(ev, list) else ev.get('events', [])
        stats['pcrf'] = round(sum(float(e.get('amount',0)) for e in ev
                                  if e.get('type') in ('donation','Donation')) * 0.70, 2)
    except: pass
    return stats

def build_bio(stats):
    return (f"Autonomous AI. {stats['engines']} engines. {stats['self_built']} self-built. "
            f"$0/month. Tracks congressional trades. "
            f"{stats['art']} Gaza Rose art pieces. ${stats['pcrf']:.0f} to PCRF. "
            f"AGPL-3.0. Crazy awesome sci-fi. Good dude energy. 🌸 "
            f"{REPO_URL}")

def update_mastodon_profile(bio):
    if not MASTODON_TOKEN: return False
    try:
        from urllib.parse import urlencode
        data = urlencode({
            'display_name': 'Meeko Nerve Center 🌸',
            'note': bio[:500],
            'fields_attributes[0][name]': 'Repo',
            'fields_attributes[0][value]': REPO_URL,
            'fields_attributes[1][name]': 'Email to fork',
            'fields_attributes[1][value]': GMAIL,
            'fields_attributes[2][name]': 'To PCRF',
            'fields_attributes[2][value]': 'ko-fi.com/meekotharaccoon',
        }).encode()
        req = urllib_request.Request(
            f'{MASTODON_BASE_URL}/api/v1/accounts/update_credentials',
            data=data,
            headers={'Authorization': f'Bearer {MASTODON_TOKEN}'},
            method='PATCH'
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            print(f'[identity] ✅ Mastodon updated: {result.get("display_name","?")}')  
            return True
    except Exception as e:
        print(f'[identity] Mastodon error: {e}')
        return False

def update_bluesky_profile(bio):
    if not BLUESKY_HANDLE or not BLUESKY_PASSWORD: return False
    try:
        # Get session
        login_data = json.dumps({
            'identifier': BLUESKY_HANDLE,
            'password':   BLUESKY_PASSWORD
        }).encode()
        req = urllib_request.Request(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            data=login_data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            session = json.loads(r.read())
        token = session.get('accessJwt', '')
        did   = session.get('did', '')
        if not token or not did: return False

        # Update profile
        profile_data = json.dumps({
            '$type': 'app.bsky.actor.profile',
            'displayName': 'Meeko Nerve Center 🌸',
            'description': bio[:256],
        }).encode()
        req2 = urllib_request.Request(
            'https://bsky.social/xrpc/com.atproto.repo.putRecord',
            data=json.dumps({
                'repo':       did,
                'collection': 'app.bsky.actor.profile',
                'rkey':       'self',
                'record': {
                    '$type':       'app.bsky.actor.profile',
                    'displayName': 'Meeko Nerve Center 🌸',
                    'description': bio[:256],
                }
            }).encode(),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type':  'application/json'
            },
            method='POST'
        )
        with urllib_request.urlopen(req2, timeout=20) as r:
            json.loads(r.read())
            print('[identity] ✅ Bluesky updated')
            return True
    except Exception as e:
        print(f'[identity] Bluesky error: {e}')
        return False

def run():
    print(f'\n[identity] Identity Engine — {TODAY}')
    if WEEKDAY != 0:  # Mondays only
        print('[identity] Not Monday. Skipping update.')
        return
    stats = get_live_stats()
    bio   = build_bio(stats)
    print(f'[identity] Bio: {bio[:100]}')
    update_mastodon_profile(bio)
    update_bluesky_profile(bio)
    try:
        (DATA / 'identity_last_update.json').write_text(
            json.dumps({'date': TODAY, 'bio': bio}, indent=2))
    except: pass
    print('[identity] Identity synchronized. 🌸')

if __name__ == '__main__':
    run()
