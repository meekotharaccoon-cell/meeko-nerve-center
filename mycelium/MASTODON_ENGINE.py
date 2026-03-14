# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
MASTODON_ENGINE.py — Posts to Mastodon / Fediverse
================================================
Needs: MASTODON_ACCESS_TOKEN + (optional) MASTODON_INSTANCE

Get token: mastodon.social → Settings → Development → New Application
  → Permissions: write:statuses
  → Copy "Your access token"

Add as GitHub Secrets:
  MASTODON_ACCESS_TOKEN
  MASTODON_INSTANCE (optional, defaults to mastodon.social)
"""
import os, json, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
TOKEN    = os.environ.get("MASTODON_ACCESS_TOKEN", "")
INSTANCE = os.environ.get("MASTODON_INSTANCE", "mastodon.social").rstrip("/")
SHOP_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
MAX_POSTS = 3


def toot(text):
    url  = f"https://{INSTANCE}/api/v1/statuses"
    data = urllib.parse.urlencode({"status": text[:500]}).encode()
    req  = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())
        return True, resp.get("url", "")


def load_state():
    f = DATA / "mastodon_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "posted": 0, "failed": 0}


def save_state(s):
    (DATA / "mastodon_state.json").write_text(json.dumps(s, indent=2))


def run():
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    print(f"MASTODON_ENGINE cycle {state['cycles']} | instance={INSTANCE}")

    if not TOKEN:
        print("  ⚠️  MASTODON_ACCESS_TOKEN not set")
        print("  → mastodon.social → Settings → Development → New Application → write:statuses")
        save_state(state)
        return state

    f = DATA / "social_queue.json"
    posts = []
    queue = {"posts": []}
    if f.exists():
        try:
            queue = json.loads(f.read_text())
            posts = queue.get("posts", [])
        except: pass

    unsent = [p for p in posts if not p.get("sent_mastodon") and not p.get("sent")]
    print(f"  Queue: {len(unsent)} unsent")

    if not unsent:
        try:
            omnibus = json.loads((DATA / "omnibus_last.json").read_text())
            cycle   = omnibus.get("cycle_number", "?")
            engines = len(omnibus.get("engines_ok", []))
            text    = f"🌿 SolarPunk cycle {cycle} — {engines} engines running autonomously. AI organism routing 15% to Gaza (PCRF). {SHOP_URL} #Gaza #Palestine #AI #OpenSource"
            fallback = {"text": text, "sent_mastodon": False, "source": "MASTODON_auto"}
            posts.append(fallback)
            unsent = [fallback]
        except: pass

    sent = 0
    for post in posts:
        if sent >= MAX_POSTS: break
        if post.get("sent_mastodon") or post.get("sent"): continue
        text = post.get("text", "") or post.get("content", "")
        if not text: continue
        if SHOP_URL not in text and len(text) < 460:
            text = text.rstrip() + f" {SHOP_URL}"
        try:
            success, url = toot(text)
            post["sent_mastodon"] = True
            post["mastodon_url"] = url
            state["posted"] = state.get("posted", 0) + 1
            print(f"  ✅ {url}")
        except Exception as e:
            post["sent_mastodon"] = True
            state["failed"] = state.get("failed", 0) + 1
            print(f"  ❌ {str(e)[:80]}")
        sent += 1

    queue["posts"] = posts
    f.write_text(json.dumps(queue, indent=2))
    save_state(state)
    print(f"  Sent: {sent} | All-time: {state['posted']}")
    return state


if __name__ == "__main__":
    run()
