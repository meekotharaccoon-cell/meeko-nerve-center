#!/usr/bin/env python3
"""
AUTONOMOUS_PUBLISHER.py — The voice that never fails
=====================================================
SolarPunk has 203+ posts queued and nowhere to send them.
This engine ends that permanently.

Multi-channel cascade strategy:
  1. Bluesky (AT Protocol, pure HTTP, free, no OAuth)
  2. DEV.to (API key already set)
  3. Mastodon (if token set)
  4. Twitter/X (if all 4 credentials set)
  5. GitHub Gist (ALWAYS available via GITHUB_TOKEN — fallback)

At least one channel ALWAYS works. The queue will drain.
Max 8 posts total per cycle across all channels.
"""
import os, json, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
SHOP_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
MAX_CYCLE = 8

BSKY_ID    = os.environ.get("BLUESKY_IDENTIFIER", "")
BSKY_PASS  = os.environ.get("BLUESKY_APP_PASSWORD", "")
DEVTO_KEY  = os.environ.get("DEVTO_API_KEY", "")
MAST_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN", "")
MAST_INST  = os.environ.get("MASTODON_INSTANCE", "mastodon.social")
X_KEY      = os.environ.get("X_API_KEY", "")
X_SECRET   = os.environ.get("X_API_SECRET", "")
X_TOKEN    = os.environ.get("X_ACCESS_TOKEN", "")
X_TOK_SEC  = os.environ.get("X_ACCESS_TOKEN_SECRET", "")
GH_TOKEN   = os.environ.get("GITHUB_TOKEN", "")

_bsky_token = None
_bsky_did   = None


# ── BLUESKY ──────────────────────────────────────────────────────────
def bsky_login():
    global _bsky_token, _bsky_did
    if _bsky_token:
        return True
    if not BSKY_ID or not BSKY_PASS:
        return False
    try:
        url  = "https://bsky.social/xrpc/com.atproto.server.createSession"
        data = json.dumps({"identifier": BSKY_ID, "password": BSKY_PASS}).encode()
        req  = urllib.request.Request(url, data=data)
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
        _bsky_token = resp.get("accessJwt")
        _bsky_did   = resp.get("did")
        return bool(_bsky_token)
    except:
        return False


def send_bluesky(text):
    if not bsky_login():
        return False, "not configured"
    try:
        url  = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
        ts   = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        data = json.dumps({
            "repo": _bsky_did, "collection": "app.bsky.feed.post",
            "record": {"$type": "app.bsky.feed.post", "text": text[:300], "createdAt": ts},
        }).encode()
        req = urllib.request.Request(url, data=data)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {_bsky_token}")
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
        uri   = resp.get("uri", "")
        parts = uri.replace("at://", "").split("/")
        link  = f"https://bsky.app/profile/{parts[0]}/post/{parts[2]}" if len(parts) == 3 else uri
        return True, link
    except Exception as e:
        return False, str(e)[:100]


# ── DEV.TO ───────────────────────────────────────────────────────────
def send_devto(title, body_md, tags):
    if not DEVTO_KEY:
        return False, "no DEVTO_API_KEY"
    try:
        payload = json.dumps({"article": {
            "title":         title[:125],
            "body_markdown": body_md,
            "published":     True,
            "tags":          [t.lower().replace(" ", "")[:20] for t in (tags or ["ai"])[:4]],
        }}).encode()
        req = urllib.request.Request("https://dev.to/api/articles", data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("api-key", DEVTO_KEY)
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        return True, resp.get("url", "https://dev.to")
    except urllib.error.HTTPError as e:
        body = ""
        try: body = e.read().decode()[:200]
        except: pass
        return False, f"HTTP {e.code}: {body}"
    except Exception as e:
        return False, str(e)[:100]


# ── MASTODON ──────────────────────────────────────────────────────────
def send_mastodon(text):
    if not MAST_TOKEN:
        return False, "no token"
    try:
        data = urllib.parse.urlencode({"status": text[:500]}).encode()
        req  = urllib.request.Request(f"https://{MAST_INST}/api/v1/statuses", data=data, method="POST")
        req.add_header("Authorization", f"Bearer {MAST_TOKEN}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
        return True, resp.get("url", "")
    except Exception as e:
        return False, str(e)[:100]


# ── TWITTER/X ─────────────────────────────────────────────────────────
def send_twitter(text):
    if not all([X_KEY, X_SECRET, X_TOKEN, X_TOK_SEC]):
        return False, "missing credentials"
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=X_KEY, consumer_secret=X_SECRET,
            access_token=X_TOKEN, access_token_secret=X_TOK_SEC,
        )
        resp = client.create_tweet(text=text[:280])
        tid  = resp.data.get("id") if resp.data else "?"
        return True, f"https://twitter.com/i/web/status/{tid}"
    except Exception as e:
        return False, str(e)[:100]


# ── GITHUB GIST (always available) ────────────────────────────────────
def send_github_gist(text, title="SolarPunk Update"):
    if not GH_TOKEN:
        return False, "no GITHUB_TOKEN"
    try:
        ts      = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        payload = json.dumps({
            "description": title,
            "public":      True,
            "files":       {f"solarpunk_{ts}.md": {"content": f"{text}\n\n{SHOP_URL}"}},
        }).encode()
        req = urllib.request.Request("https://api.github.com/gists", data=payload, method="POST")
        req.add_header("Authorization", f"token {GH_TOKEN}")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "SolarPunk/1.0")
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
        return True, resp.get("html_url", "")
    except Exception as e:
        return False, str(e)[:100]


# ── QUEUE ──────────────────────────────────────────────────────────────
def load_queue():
    posts = []
    f = DATA / "social_queue.json"
    if f.exists():
        try:
            q = json.loads(f.read_text())
            posts = q.get("posts", [])
        except: pass
    # Also absorb tweets_queue.txt
    tf = DATA / "tweets_queue.txt"
    if tf.exists():
        try:
            seen  = {p.get("text", "") for p in posts}
            for line in tf.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and line not in seen:
                    posts.append({"text": line, "platform": "all", "source": "tweets_queue_txt"})
        except: pass
    return posts


def save_queue(posts):
    (DATA / "social_queue.json").write_text(json.dumps({"posts": posts, "last_drain": datetime.now(timezone.utc).isoformat()}, indent=2))


def make_devto_article(post):
    niche    = post.get("niche", "SolarPunk AI") or "SolarPunk AI"
    text     = post.get("text", "") or ""
    live_url = post.get("live_url", SHOP_URL) or SHOP_URL
    ts       = datetime.now(timezone.utc).strftime("%B %d, %Y")
    title    = post.get("title") or f"{niche} — SolarPunk ({ts})"
    body     = f"""# {niche}\n\n{text}\n\n---\n\n**SolarPunk** — autonomous AI organism. 15% to Gaza always.\n\n- 🌍 [{live_url}]({live_url})\n- 📖 [What is SolarPunk?]({SHOP_URL}/solarpunk.html)\n- 🛒 [Store]({SHOP_URL}/store.html)\n- 🔓 [Fork it](https://github.com/meekotharaccoon-cell/meeko-nerve-center)\n\n*Published autonomously by the SolarPunk organism.*\n"""
    tags = ["ai", "opensource", "automation", "productivity"]
    n = niche.lower()
    if any(w in n for w in ["art", "design"]): tags = ["art", "design", "ai", "creativity"]
    elif any(w in n for w in ["notion", "template"]): tags = ["productivity", "tools", "notion", "ai"]
    return title, body, tags


def load_state():
    f = DATA / "autonomous_publisher_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "total_sent": 0, "by_channel": {}}


def save_state(s):
    (DATA / "autonomous_publisher_state.json").write_text(json.dumps(s, indent=2))


def run():
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    ts = datetime.now(timezone.utc).isoformat()

    channels = {
        "bluesky":  bool(BSKY_ID and BSKY_PASS),
        "devto":    bool(DEVTO_KEY),
        "mastodon": bool(MAST_TOKEN),
        "twitter":  bool(X_KEY and X_SECRET and X_TOKEN and X_TOK_SEC),
        "github":   bool(GH_TOKEN),
    }
    active = [c for c, ok in channels.items() if ok]
    print(f"AUTONOMOUS_PUBLISHER cycle {state['cycles']} | active: {', '.join(active) or 'github-only'}")

    posts  = load_queue()
    unsent = [p for p in posts if not p.get("published_autonomous")]
    print(f"  Queue: {len(unsent)} unsent / {len(posts)} total")

    if not unsent:
        try:
            om    = json.loads((DATA / "omnibus_last.json").read_text())
            cycle = om.get("cycle_number", "?")
            h     = om.get("health_after", om.get("health_before", "?"))
            n     = len(om.get("engines_ok", []))
            res   = om.get("resonance_score", 0)
            unsent = [{"text": f"🌿 SolarPunk cycle {cycle} — {n} engines, health {h}/100, resonance {res}/100. Autonomous AI routing 15% to Gaza. {SHOP_URL}/narrative.html", "platform": "all", "source": "auto"}]
            posts.extend(unsent)
        except:
            unsent = [{"text": f"🌿 SolarPunk — autonomous AI organism. 15% to Gaza. {SHOP_URL}", "platform": "all"}]

    sent_total   = 0
    devto_posted = 0

    for post in posts:
        if sent_total >= MAX_CYCLE: break
        if post.get("published_autonomous"): continue

        text = post.get("text", "") or post.get("content", "")
        if not text: continue
        if SHOP_URL not in text and len(text) < 240:
            text = text.rstrip() + f" {SHOP_URL}"

        sent_any = False
        results  = {}

        if channels["bluesky"]:
            ok, info = send_bluesky(text)
            results["bluesky"] = info
            if ok:
                sent_any = True
                state["by_channel"]["bluesky"] = state["by_channel"].get("bluesky", 0) + 1
                print(f"  ✅ Bluesky: {info[:80]}")
            else:
                print(f"  ⚠️  Bluesky: {info[:60]}")

        if channels["devto"] and devto_posted < 2 and post.get("niche"):
            title, body, tags = make_devto_article(post)
            ok, info = send_devto(title, body, tags)
            results["devto"] = info
            if ok:
                sent_any  = True
                devto_posted += 1
                state["by_channel"]["devto"] = state["by_channel"].get("devto", 0) + 1
                print(f"  ✅ DEV.to: {info[:80]}")
            else:
                print(f"  ⚠️  DEV.to: {info[:60]}")

        if channels["mastodon"]:
            ok, info = send_mastodon(text)
            results["mastodon"] = info
            if ok:
                sent_any = True
                state["by_channel"]["mastodon"] = state["by_channel"].get("mastodon", 0) + 1
                print(f"  ✅ Mastodon: {info[:80]}")
            else:
                print(f"  ⚠️  Mastodon: {info[:60]}")

        if channels["twitter"]:
            ok, info = send_twitter(text)
            results["twitter"] = info
            if ok:
                sent_any = True
                state["by_channel"]["twitter"] = state["by_channel"].get("twitter", 0) + 1
                print(f"  ✅ Twitter: {info[:80]}")
            else:
                print(f"  ⚠️  Twitter: {info[:60]}")

        # GitHub Gist — last resort, always available
        if not sent_any and channels["github"]:
            niche = post.get("niche", "SolarPunk Update")
            ok, info = send_github_gist(text, title=niche)
            results["github_gist"] = info
            if ok:
                sent_any = True
                state["by_channel"]["github_gist"] = state["by_channel"].get("github_gist", 0) + 1
                print(f"  ✅ GitHub Gist: {info[:80]}")

        post["published_autonomous"] = True
        post["published_at"]         = ts
        post["channel_results"]      = results
        post["published_success"]    = sent_any
        if sent_any:
            state["total_sent"] = state.get("total_sent", 0) + 1
            sent_total += 1

    save_queue(posts)
    save_state(state)
    print(f"  Sent this cycle: {sent_total} | All-time: {state['total_sent']}")
    if not active:
        print("  ⚠️  No social channels → add BLUESKY_IDENTIFIER + BLUESKY_APP_PASSWORD to GitHub Secrets")
    return state


if __name__ == "__main__":
    run()
