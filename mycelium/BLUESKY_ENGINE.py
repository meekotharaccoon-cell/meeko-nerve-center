# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
BLUESKY_ENGINE.py — Posts to Bluesky via AT Protocol
=====================================================
No OAuth. No app registration. Pure HTTPS.
Needs: BLUESKY_IDENTIFIER (email or handle) + BLUESKY_APP_PASSWORD

Get app password: bsky.social → Settings → App Passwords → Add App Password
Add as GitHub Secrets: BLUESKY_IDENTIFIER + BLUESKY_APP_PASSWORD

Drains the 203-item social queue automatically, 5 posts per cycle.
"""
import os, json, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA       = Path("data"); DATA.mkdir(exist_ok=True)
IDENTIFIER = os.environ.get("BLUESKY_IDENTIFIER", "")
APP_PASS   = os.environ.get("BLUESKY_APP_PASSWORD", "")
BSKY_HOST  = "https://bsky.social"
SHOP_URL   = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
MAX_POSTS  = 5


def bsky_post(endpoint, payload, token=None):
    url  = f"{BSKY_HOST}/xrpc/{endpoint}"
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def login():
    if not IDENTIFIER or not APP_PASS:
        return None, None
    try:
        resp = bsky_post("com.atproto.server.createSession", {
            "identifier": IDENTIFIER,
            "password":   APP_PASS,
        })
        return resp.get("accessJwt"), resp.get("did")
    except Exception as e:
        print(f"  Bluesky login failed: {e}")
        return None, None


def post_text(token, did, text):
    try:
        ts   = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        resp = bsky_post("com.atproto.repo.createRecord", {
            "repo":       did,
            "collection": "app.bsky.feed.post",
            "record": {
                "$type":     "app.bsky.feed.post",
                "text":      text[:300],
                "createdAt": ts,
            },
        }, token=token)
        uri = resp.get("uri", "")
        if uri.startswith("at://"):
            parts = uri.replace("at://", "").split("/")
            if len(parts) == 3:
                return True, f"https://bsky.app/profile/{parts[0]}/post/{parts[2]}"
        return True, uri
    except Exception as e:
        return False, str(e)


def load_queue():
    f = DATA / "social_queue.json"
    if f.exists():
        try:
            q = json.loads(f.read_text())
            return q, q.get("posts", [])
        except: pass
    # Fallback: tweets_queue.txt
    tf = DATA / "tweets_queue.txt"
    if tf.exists():
        try:
            lines = [l.strip() for l in tf.read_text().splitlines() if l.strip() and not l.startswith("#")]
            posts = [{"text": l, "platform": "bluesky"} for l in lines]
            return {"posts": posts}, posts
        except: pass
    return {"posts": []}, []


def save_queue(q):
    (DATA / "social_queue.json").write_text(json.dumps(q, indent=2))


def load_state():
    f = DATA / "bluesky_engine_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "posted": 0, "failed": 0}


def save_state(s):
    (DATA / "bluesky_engine_state.json").write_text(json.dumps(s, indent=2))


def run():
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"BLUESKY_ENGINE cycle {state['cycles']}")

    if not IDENTIFIER or not APP_PASS:
        print("  ⚠️  BLUESKY_IDENTIFIER or BLUESKY_APP_PASSWORD not set")
        print("  → bsky.social → Settings → App Passwords → Add App Password")
        print("  → Add as GitHub Secrets: BLUESKY_IDENTIFIER + BLUESKY_APP_PASSWORD")
        save_state(state)
        return state

    token, did = login()
    if not token:
        print("  ❌ Login failed")
        save_state(state)
        return state
    print(f"  ✅ Logged in as {IDENTIFIER}")

    queue, posts = load_queue()
    unsent = [p for p in posts if not p.get("sent_bluesky") and not p.get("sent")]
    print(f"  Queue: {len(unsent)} unsent posts")

    if not unsent:
        try:
            omnibus = json.loads((DATA / "omnibus_last.json").read_text())
            cycle   = omnibus.get("cycle_number", "?")
            engines = len(omnibus.get("engines_ok", []))
            unsent  = [{"text": f"🌿 SolarPunk cycle {cycle} — {engines} engines running. Autonomous AI organism routing 15% to Gaza every cycle. {SHOP_URL}", "platform": "bluesky"}]
            posts.append(unsent[0])
            queue["posts"] = posts
        except:
            unsent = [{"text": f"🌿 SolarPunk — autonomous AI organism. 15% to Gaza always. {SHOP_URL}"}]

    sent = 0
    for post in posts:
        if sent >= MAX_POSTS: break
        if post.get("sent_bluesky") or post.get("sent"): continue
        text = post.get("text", "") or post.get("content", "")
        if not text: continue
        if SHOP_URL not in text and len(text) < 260:
            text = text.rstrip() + f" {SHOP_URL}"
        success, url = post_text(token, did, text)
        post["sent_bluesky"] = True
        post["bsky_url"]     = url if success else ""
        post["bsky_at"]      = datetime.now(timezone.utc).isoformat()
        if success:
            state["posted"] = state.get("posted", 0) + 1
            print(f"  ✅ {url}")
        else:
            state["failed"] = state.get("failed", 0) + 1
            print(f"  ❌ {url[:80]}")
        sent += 1

    queue["posts"] = posts
    save_queue(queue)
    save_state(state)
    print(f"  Sent: {sent} | All-time: {state['posted']}")
    return state


if __name__ == "__main__":
    run()
