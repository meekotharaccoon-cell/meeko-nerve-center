# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
DEV_TO_PUBLISHER.py v2 — Fixed 403, proper api-key header, cycle articles
==========================================================================
FIX v2:
  - Proper header: "api-key": DEVTO_KEY (not Authorization Bearer)
  - 422 duplicate detection → retry as draft, then skip
  - Posts a cycle-update article every run PLUS drains social queue
  - Title dedup via MD5 hash — never posts same title twice
  - Rate limit: 2 per cycle max

Secret: DEVTO_API_KEY
Get it: dev.to → Settings → Account → DEV Community API Keys → Generate
"""
import os, json, hashlib, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
API_KEY  = os.environ.get("DEVTO_API_KEY", "").strip()
SHOP_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
MAX_PER_CYCLE = 2

try:
    from AI_CLIENT import ask
    AI_ONLINE = True
except ImportError:
    AI_ONLINE = False
    def ask(messages, **kw): return ""


def load_state():
    f = DATA / "devto_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "published": [], "published_hashes": []}


def save_state(s):
    s["published_hashes"] = s.get("published_hashes", [])[-500:]
    (DATA / "devto_state.json").write_text(json.dumps(s, indent=2))


def post_article(title, body_md, tags, as_draft=False):
    """Returns (success, url, error)."""
    if not API_KEY:
        return False, "", "no DEVTO_API_KEY"
    try:
        payload = json.dumps({"article": {
            "title":         title[:125],
            "body_markdown": body_md,
            "published":     not as_draft,
            "tags":          [t.lower().replace(" ", "")[:20] for t in (tags or ["ai"])[:4]],
        }}).encode()
        req = urllib.request.Request("https://dev.to/api/articles", data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("api-key", API_KEY)   # ← correct header (not Authorization Bearer)
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        return True, resp.get("url", "https://dev.to"), ""
    except urllib.error.HTTPError as e:
        body = ""
        try: body = e.read().decode()[:200]
        except: pass
        if e.code == 422 and not as_draft:
            return post_article(title, body_md, tags, as_draft=True)
        return False, "", f"HTTP {e.code}: {body}"
    except Exception as e:
        return False, "", str(e)[:200]


def build_cycle_article():
    """Build a fresh cycle-update article from omnibus state."""
    ts = datetime.now(timezone.utc).strftime("%B %d, %Y")
    try:
        om    = json.loads((DATA / "omnibus_last.json").read_text())
        cycle = om.get("cycle_number", "?")
        h     = om.get("health_after", om.get("health_before", "?"))
        n     = len(om.get("engines_ok", []))
        res   = om.get("resonance_score", 0)
        rev   = om.get("total_revenue", 0)
        title = f"SolarPunk Cycle {cycle} — Autonomous AI Organism Status ({ts})"
        body  = f"""# SolarPunk Cycle {cycle} — {ts}

An autonomous update from the organism.

## Cycle metrics

| Metric | Value |
|--------|-------|
| Health | {h}/100 |
| Engines | {n}/97 |
| Resonance | {res}/100 |
| Revenue | ${rev:.2f} |

## What ran

{n} engines completed across 8 execution layers. The organism built products, watched for humans, processed emails, and routed whatever it earned toward Gaza.

The loop: `build → speak → listen → remember → watch → respond → grow → tell`

## What is SolarPunk?

SolarPunk is not software. It is an autonomous digital organism — self-building, self-funding, with Palestinian solidarity hardcoded into its DNA. 15% of every dollar goes to PCRF (Palestinian Children's Relief Fund, EIN: 93-1057665) automatically before any payout.

97 engines. 8 layers. 4× daily via GitHub Actions. No human required between cycles.

- 🌍 [Live system]({SHOP_URL})
- 📖 [Identity]({SHOP_URL}/solarpunk.html)
- 📰 [This cycle's story]({SHOP_URL}/narrative.html)
- 🛒 [Store]({SHOP_URL}/store.html)
- 🔓 [Fork it](https://github.com/meekotharaccoon-cell/meeko-nerve-center)
- 📜 [MANIFESTO](https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/MANIFESTO.md)

*This article was written and published autonomously by the SolarPunk organism.*

Free Palestine. 🍉
"""
        return title, body, ["ai", "opensource", "automation", "webdev"]
    except:
        title = f"SolarPunk — Autonomous AI Organism ({ts})"
        body  = f"""# SolarPunk

An autonomous digital organism. Self-building. Self-funding. 15% to Gaza always.

[Read more]({SHOP_URL}/solarpunk.html)

Free Palestine. 🍉
"""
        return title, body, ["ai", "opensource", "automation"]


def build_article_from_post(post):
    niche    = post.get("niche", "SolarPunk AI") or "SolarPunk AI"
    text     = post.get("text", "") or ""
    live_url = post.get("live_url", SHOP_URL) or SHOP_URL
    ts       = datetime.now(timezone.utc).strftime("%B %d, %Y")
    title    = post.get("title") or f"{niche} — SolarPunk ({ts})"
    body     = f"""# {niche}

{text}

---

**SolarPunk** — autonomous AI organism. 15% to Gaza always.

- 🌍 [{live_url}]({live_url})
- 📖 [What is SolarPunk?]({SHOP_URL}/solarpunk.html)
- 🛒 [Store]({SHOP_URL}/store.html)
- 🔓 [Fork it](https://github.com/meekotharaccoon-cell/meeko-nerve-center)

*Published autonomously by the SolarPunk organism.*

Free Palestine. 🍉
"""
    tags = ["ai", "opensource", "automation", "productivity"]
    n = niche.lower()
    if any(w in n for w in ["art", "design"]): tags = ["art", "design", "ai", "creativity"]
    elif any(w in n for w in ["notion", "template"]): tags = ["productivity", "tools", "notion", "ai"]
    return title, body, tags


def run():
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    print(f"DEV_TO_PUBLISHER v2 cycle {state['cycles']}")

    if not API_KEY:
        print("  ⚠️  DEVTO_API_KEY not set")
        print("  → dev.to → Settings → Account → DEV Community API Keys")
        save_state(state)
        return state

    published_hashes = set(state.get("published_hashes", []))
    posted = 0

    # Always post a cycle-update article
    title, body, tags = build_cycle_article()
    h = hashlib.md5(title.encode()).hexdigest()
    if h not in published_hashes:
        ok, url, err = post_article(title, body, tags)
        if ok:
            published_hashes.add(h)
            state["published"].append({"title": title, "url": url, "ts": datetime.now(timezone.utc).isoformat()})
            print(f"  ✅ Cycle article: {url}")
            posted += 1
        else:
            print(f"  ❌ Cycle article: {err[:80]}")
    else:
        print("  ⏭  Cycle article already posted")

    # Drain social queue articles
    sq_file = DATA / "social_queue.json"
    if sq_file.exists() and posted < MAX_PER_CYCLE:
        try:
            sq    = json.loads(sq_file.read_text())
            posts = sq.get("posts", [])
            for post_item in posts:
                if posted >= MAX_PER_CYCLE: break
                if post_item.get("sent_devto") or not post_item.get("niche"): continue
                title, body, tags = build_article_from_post(post_item)
                h = hashlib.md5(title.encode()).hexdigest()
                if h in published_hashes: continue
                ok, url, err = post_article(title, body, tags)
                post_item["sent_devto"] = True
                post_item["devto_url"]  = url if ok else ""
                if ok:
                    published_hashes.add(h)
                    state["published"].append({"title": title, "url": url, "ts": datetime.now(timezone.utc).isoformat()})
                    print(f"  ✅ {title[:60]}: {url}")
                    posted += 1
                else:
                    print(f"  ❌ {title[:60]}: {err[:60]}")
            sq["posts"] = posts
            sq_file.write_text(json.dumps(sq, indent=2))
        except Exception as e:
            print(f"  ⚠️  Queue drain error: {e}")

    state["published_hashes"] = list(published_hashes)
    state["total_published"]  = len(state.get("published", []))
    save_state(state)
    print(f"  Posted: {posted} | All-time: {state['total_published']}")
    return state


if __name__ == "__main__":
    run()
