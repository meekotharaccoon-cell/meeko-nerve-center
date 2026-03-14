#!/usr/bin/env python3
"""
MEEKO MYCELIUM - DIGITAL ORGANISM PULSE

This is the living heartbeat of the system.
Runs twice daily. Never needs a human.

Anatomy:
  EYES     -> SerpAPI (sees web trends)
  VOICE    -> Discord, Mastodon, Dev.to (speaks to world)
  MEMORY   -> meeko-brain repo (remembers everything)
  HANDS    -> PayPal, Stripe, Gumroad, Coinbase (moves money)
  MIND     -> OpenRouter/Kimi AI (thinks and creates)
  BODY     -> GitHub Actions (lives here, always on)
  DNA      -> meeko-nerve-center repo (instructions)
  BLOOD    -> Bitcoin + PayPal (value flows through here)
"""

import os
import json
import requests
import random
from datetime import datetime, timezone

PULSE_TIME = os.environ.get('PULSE_TIME', 'morning')
GALLERY_URL = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'
GITHUB_RAW = 'https://raw.githubusercontent.com/meekotharaccoon-cell/gaza-rose-gallery/main/art/'
ARTIST = 'Meeko'
CAUSE = 'Palestine Children Relief Fund (PCRF)'

# ─────────────────────────────────────────────
# VOICE: What the mycelium says to the world
# ─────────────────────────────────────────────

MORNING_MESSAGES = [
    "🌅 Morning. Gaza Rose Gallery is open.\n\n56 original digital flowers. $1 each. 70% goes straight to the Palestine Children Relief Fund.\n\nBuy art. Fund aid. No middleman.\n{url}",
    "🌹 Every flower in this gallery was made with care and intention.\n\nArtist: Meeko\nCause: Palestine Children Relief Fund\nPrice: $1\n\nSomething beautiful. Something real.\n{url}",
    "☀️ A SolarPunk gallery built from scratch — no VC, no ads, no gatekeepers.\n\nJust art, a mission, and technology built to serve people.\n\nGaza Rose: {url}\n70% to PCRF.",
    "🌸 Open source. Open heart.\n\nGaza Rose Gallery — 56 digital flowers by Meeko.\n$1 per piece. 70% to Palestine children.\n\n{url}",
]

EVENING_MESSAGES = [
    "🌙 Evening check-in from Gaza Rose Gallery.\n\nEvery piece sold today moves money to the Palestine Children Relief Fund. Automatically. Directly.\n\nThis is what ethical tech looks like: {url}",
    "🕊️ Before you sleep — 56 flowers, $1 each, 70% to PCRF.\n\nArt by Meeko. Built with GitHub Actions. Running while the world rests.\n\n{url}",
    "🌃 The gallery doesn't close. The cause doesn't pause.\n\nGaza Rose by Meeko — digital art for humanitarian aid.\n{url}\n\n#Gaza #SolarPunk #DigitalArt #OpenSource",
    "✨ End of day. The system ran itself.\n\nGaza Rose Gallery: 56 original flowers. $1 each. No ads. No trackers. Just art and aid.\n\n{url}",
]


def get_message():
    msgs = MORNING_MESSAGES if PULSE_TIME == 'morning' else EVENING_MESSAGES
    return random.choice(msgs).format(url=GALLERY_URL)


# ─────────────────────────────────────────────
# VOICE: Discord
# ─────────────────────────────────────────────
def post_discord(message):
    webhook = os.environ.get('DISCORD_WEBHOOK')
    if not webhook:
        print('[Discord] No webhook configured — skipping')
        return False
    try:
        r = requests.post(webhook, json={'content': message}, timeout=15)
        if r.status_code in (200, 204):
            print('[Discord] Posted successfully')
            return True
        print(f'[Discord] Failed: {r.status_code}')
    except Exception as e:
        print(f'[Discord] Error: {e}')
    return False


# ─────────────────────────────────────────────
# VOICE: Mastodon
# ─────────────────────────────────────────────
def post_mastodon(message):
    token = os.environ.get('MASTODON_TOKEN')
    server = os.environ.get('MASTODON_SERVER', 'mastodon.social')
    if not token:
        print('[Mastodon] No token configured — skipping')
        return False
    try:
        r = requests.post(
            f'https://{server}/api/v1/statuses',
            headers={'Authorization': f'Bearer {token}'},
            data={'status': message[:500]},
            timeout=15
        )
        if r.status_code == 200:
            print('[Mastodon] Posted successfully')
            return True
        print(f'[Mastodon] Failed: {r.status_code}')
    except Exception as e:
        print(f'[Mastodon] Error: {e}')
    return False


# ─────────────────────────────────────────────
# VOICE: Dev.to (morning only — full articles)
# ─────────────────────────────────────────────
def post_devto():
    api_key = os.environ.get('DEVTO_API_KEY')
    if not api_key or PULSE_TIME != 'morning':
        print('[Dev.to] Skipping (no key or evening pulse)')
        return False

    today = datetime.now(timezone.utc).strftime('%B %d, %Y')
    article = {
        'title': f'Gaza Rose Gallery — SolarPunk humanitarian art ({today})',
        'published': True,
        'body_markdown': f"""# Gaza Rose Gallery

Artist Meeko built a fully autonomous digital art gallery where 70% of every sale goes directly to the Palestine Children Relief Fund.

**56 original 300 DPI digital flowers. $1 each.**

No ads. No trackers. No VC funding. Just GitHub Actions, PayPal, and a clear mission.

## How it works

- Gallery lives on GitHub Pages (free, permanent)
- PayPal handles payments ($1 per artwork)
- 70% of each sale routes to PCRF
- GitHub Actions runs promotion twice daily
- The system updates itself — no human required

## The technology

- **Body**: GitHub Actions (always-on, free)
- **Memory**: Private brain repo (state persists across sessions)
- **Voice**: Discord + Mastodon + Dev.to (you're reading one now)
- **Hands**: PayPal + Stripe + Coinbase (money moves)
- **Eyes**: SerpAPI (web awareness)
- **Mind**: OpenRouter AI (content generation)

This is SolarPunk in practice: technology that serves people, built transparently, open source, with ethics baked in from day one.

## Visit the gallery

{GALLERY_URL}

#opensource #solarPunk #Gaza #digitalArt #humanitarianTech #PCRF
""",
        'tags': ['opensource', 'solarPunk', 'javascript', 'programming']
    }
    try:
        r = requests.post(
            'https://dev.to/api/articles',
            headers={'api-key': api_key, 'Content-Type': 'application/json'},
            json={'article': article},
            timeout=15
        )
        if r.status_code == 201:
            print(f"[Dev.to] Article published: {r.json().get('url')}")
            return True
        print(f'[Dev.to] Failed: {r.status_code} {r.text[:200]}')
    except Exception as e:
        print(f'[Dev.to] Error: {e}')
    return False


# ─────────────────────────────────────────────
# EYES: Check gallery health
# ─────────────────────────────────────────────
def check_gallery():
    try:
        r = requests.get(GALLERY_URL, timeout=15)
        status = 'LIVE' if r.status_code == 200 else f'DOWN ({r.status_code})'
    except Exception as e:
        status = f'UNREACHABLE ({e})'
    print(f'[Gallery] Status: {status}')
    return status


# ─────────────────────────────────────────────
# PULSE: main heartbeat
# ─────────────────────────────────────────────
def pulse():
    now = datetime.now(timezone.utc).isoformat()
    print(f'\n🍄 MEEKO MYCELIUM — {PULSE_TIME.upper()} PULSE')
    print(f'   Time: {now}')
    print(f'   Gallery: {GALLERY_URL}\n')

    # EYES — sense the world
    gallery_status = check_gallery()

    # VOICE — speak to the world
    message = get_message()
    print(f'\n[Message]\n{message}\n')

    results = {
        'timestamp': now,
        'pulse': PULSE_TIME,
        'gallery_status': gallery_status,
        'discord': post_discord(message),
        'mastodon': post_mastodon(message),
        'devto': post_devto(),
    }

    # Save pulse log
    with open(f'mycelium/last_{PULSE_TIME}_pulse.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f'\n✅ {PULSE_TIME.capitalize()} pulse complete')
    print(json.dumps(results, indent=2))
    return results


if __name__ == '__main__':
    pulse()
