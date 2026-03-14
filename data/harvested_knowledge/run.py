#!/usr/bin/env python3
"""
Gaza Rose Autonomous Promoter
Runs in GitHub Actions — no localhost, no open tabs, no friction.
Secrets come from GitHub repo secrets. Nothing sensitive ever in this file.
"""

import os
import random
import requests
from datetime import datetime, timezone

GALLERY_URL = "https://meekotharaccoon-cell.github.io/gaza-rose-gallery/"
PCRF_URL = "https://www.pcrf.net"
RELEASE_API = "https://api.github.com/repos/meekotharaccoon-cell/gaza-rose-gallery/releases/tags/v1.0-art-collection"

POST_TEMPLATES = [
    "🌹 Gaza Rose art — $1 each, 70% goes directly to Palestinian children via PCRF. Instant download, no account needed. {url}",
    "If you could send $1 to help a child in Gaza, you would. Here's that button. 🌹 Original AI floral art, $1 per piece, 70% to PCRF. {url}",
    "Art meets action. 🌹 The Gaza Rose Gallery: $1 per digital piece, 70% to Palestinian Children's Relief Fund. {url} #FreePalestine",
    "Open source. Zero friction. 🌹 Gaza Rose — $1/piece, 70% to PCRF within days of purchase. {url}",
    "The mycelium grows: every $1 → PCRF → medical care for a child in Gaza. SolarPunk in action. 🌹 {url} #OpenSource #SolarPunk",
]


def get_art_count():
    try:
        r = requests.get(RELEASE_API, timeout=10)
        data = r.json()
        assets = [a for a in data.get("assets", []) if a["name"].lower().endswith((".jpg", ".jpeg", ".png"))]
        return len(assets)
    except Exception:
        return 69


def get_post_text():
    count = get_art_count()
    text = random.choice(POST_TEMPLATES).format(url=GALLERY_URL)
    return f"{text}\n\n{count} original pieces. $1 each. 70% to PCRF."


def post_discord(text):
    webhook = os.environ.get("DISCORD_WEBHOOK")
    if not webhook:
        print("⏭  Discord: not configured, skipping")
        return
    payload = {
        "content": text,
        "username": "Gaza Rose 🌹",
        "embeds": [{
            "title": "🌹 Gaza Rose Gallery",
            "description": "$1 per piece · 70% to PCRF · Instant download",
            "url": GALLERY_URL,
            "color": 16720491,
            "footer": {"text": "Open source · SolarPunk · Built with love"}
        }]
    }
    r = requests.post(webhook, json=payload, timeout=10)
    print("✅ Discord: posted" if r.status_code in (200, 204) else f"❌ Discord: {r.status_code}")


def post_mastodon(text):
    token = os.environ.get("MASTODON_TOKEN")
    server = os.environ.get("MASTODON_SERVER", "mastodon.social")
    if not token:
        print("⏭  Mastodon: not configured, skipping")
        return
    r = requests.post(
        f"https://{server}/api/v1/statuses",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": text[:490], "visibility": "public"},
        timeout=10
    )
    print("✅ Mastodon: posted" if r.status_code == 200 else f"❌ Mastodon: {r.status_code}")


def post_devto(text):
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key:
        print("⏭  Dev.to: not configured, skipping")
        return
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    article = {
        "article": {
            "title": f"Gaza Rose Gallery — {date_str}",
            "body_markdown": f"# 🌹 Gaza Rose Gallery\n\n{text}\n\n## The Mission\n\nEvery purchase sends 70% directly to the [Palestine Children's Relief Fund]({PCRF_URL}). Instant download. No account. No friction.\n\n[Browse the Gallery →]({GALLERY_URL})\n\n---\n*Open source. SolarPunk. Built to get aid to Gaza without friction.*",
            "published": True,
            "tags": ["opensource", "solarpunk", "art", "charity"]
        }
    }
    r = requests.post("https://dev.to/api/articles", headers={"api-key": api_key}, json=article, timeout=10)
    print("✅ Dev.to: published" if r.status_code == 201 else f"❌ Dev.to: {r.status_code}")


def main():
    target = os.environ.get("TARGET_PLATFORM", "all").lower()
    text = get_post_text()

    print(f"\n🌹 Gaza Rose Promoter — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"📝 Post ({len(text)} chars):\n{text}\n")
    print(f"🎯 Target: {target}\n")

    if target in ("all", "discord"):
        post_discord(text)
    if target in ("all", "mastodon"):
        post_mastodon(text)
    if target in ("all", "devto"):
        post_devto(text)

    print("\n🌹 Done.")


if __name__ == "__main__":
    main()
