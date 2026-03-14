#!/usr/bin/env python3
"""
MEEKO MYCELIUM — BRAIN SYNC

Runs after every pulse.
Updates meeko-brain repo with current system state.
This is how the mycelium remembers what it did.
"""

import os
import json
import base64
import requests
from datetime import datetime, timezone

TOKEN = os.environ.get('BRAIN_TOKEN') or os.environ.get('GITHUB_TOKEN')
PULSE_TIME = os.environ.get('PULSE_TIME', 'unknown')
OWNER = 'meekotharaccoon-cell'
BRAIN_REPO = 'meeko-brain'
API = 'https://api.github.com'

HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28'
}


def get_file_sha(path):
    r = requests.get(f'{API}/repos/{OWNER}/{BRAIN_REPO}/contents/{path}', headers=HEADERS)
    if r.status_code == 200:
        return r.json().get('sha')
    return None


def update_file(path, content, message):
    sha = get_file_sha(path)
    encoded = base64.b64encode(content.encode()).decode()
    payload = {'message': message, 'content': encoded}
    if sha:
        payload['sha'] = sha
    r = requests.put(
        f'{API}/repos/{OWNER}/{BRAIN_REPO}/contents/{path}',
        headers=HEADERS,
        json=payload
    )
    return r.status_code in (200, 201)


def read_pulse_log():
    try:
        with open(f'mycelium/last_{PULSE_TIME}_pulse.json') as f:
            return json.load(f)
    except:
        return {}


def sync():
    now = datetime.now(timezone.utc)
    log = read_pulse_log()

    system_state = f"""# SYSTEM STATE — Updated {now.strftime('%Y-%m-%d %H:%M UTC')}

## Last Pulse
- Time: {now.isoformat()}
- Pulse: {PULSE_TIME}
- Gallery: {log.get('gallery_status', 'unknown')}
- Discord: {'posted' if log.get('discord') else 'skipped'}
- Mastodon: {'posted' if log.get('mastodon') else 'skipped'}
- Dev.to: {'posted' if log.get('devto') else 'skipped'}

## Gaza Rose Gallery
- Repo: meekotharaccoon-cell/gaza-rose-gallery
- URL: https://meekotharaccoon-cell.github.io/gaza-rose-gallery
- Art: 56 images in art/ folder
- 12 skipped (>50MB): Dusk_Daisies, Dahlias, Lilac_BG, Jasmine_BG, Crocus, Sunrise_Bloom, Fern_BG, Hibiscus, Flytrap_BG, Larkspur_BG, Magnolia_BG2, Cherry_Blossom_BG
- NEEDS: GitHub Pages enabled at /settings/pages

## Nerve Center
- Repo: meekotharaccoon-cell/meeko-nerve-center
- Morning pulse: 9AM EST (14:00 UTC)
- Evening pulse: 9PM EST (02:00 UTC)
- Secrets: PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, GUMROAD_TOKEN, OPENROUTER_KEY, STRIPE_SECRET, KIMI_API_KEY, SERPAPI_KEY, COINBASE_COMMERCE_KEY — all added
- Missing secrets: DISCORD_WEBHOOK, MASTODON_TOKEN (user must create these)

## Landing Page
- LIVE: https://meekotharaccoon-cell.github.io

## All Repos
meeko-brain (PRIVATE), meeko-nerve-center, gaza-rose-gallery, meekotharaccoon-cell.github.io,
atomic-agents, atomic-agents-conductor, atomic-agents-staging, atomic-agents-demo
"""

    ok = update_file('SYSTEM_STATE.md', system_state, f'auto: {PULSE_TIME} pulse sync {now.strftime("%Y-%m-%d %H:%M")}')
    print(f'[Brain Sync] SYSTEM_STATE.md updated: {ok}')


if __name__ == '__main__':
    sync()
