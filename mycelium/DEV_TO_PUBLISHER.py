#!/usr/bin/env python3
"""
DEV_TO_PUBLISHER — publishes technical articles to dev.to automatically

What it does each cycle:
  1. Checks if DEVTO_API_KEY secret is set
  2. Generates a new article via Claude (rotates through topics)
  3. Posts to dev.to with SolarPunk / Palestine solidarity / automation tags
  4. Tracks published articles in data/devto_state.json
  5. Rate limits to 1 article per 23 hours

Requires: DEVTO_API_KEY GitHub secret
Get one free at: https://dev.to/settings/extensions
Outputs:  data/devto_state.json
"""
import os, sys, json, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA = Path("data")
DATA.mkdir(exist_ok=True)
STATE_FILE = DATA / "devto_state.json"

APIKEY        = os.environ.get("DEVTO_API_KEY", "").strip()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {"published": [], "last_published": None, "total": 0}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def rj(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try:
            return json.loads(f.read_text())
        except:
            pass
    return fb if fb is not None else {}


def ask_claude(prompt):
    """Generate article content via Claude API."""
    if not ANTHROPIC_KEY:
        return None
    try:
        payload = json.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            return data["content"][0]["text"]
    except Exception as e:
        print(f"  Claude error: {e}")
        return None


def publish_to_devto(title, body, tags):
    """POST article to dev.to API."""
    payload = json.dumps({
        "article": {
            "title": title,
            "body_markdown": body,
            "published": True,
            "tags": tags[:4]  # dev.to max 4 tags
        }
    }).encode()
    req = urllib.request.Request(
        "https://dev.to/api/articles",
        data=payload,
        headers={
            "api-key": APIKEY,
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def generate_article(count):
    """Generate an article based on system context."""
    topics = [
        "How I built an autonomous AI system that donates to Gaza",
        "GitHub Actions as a free autonomous AI brain: architecture deep dive",
        "Building ethical AI revenue systems with open source tools",
        "Autonomous art + solidarity: a SolarPunk architecture walkthrough",
        "Zero-cost AI automation: GitHub Actions + Python + Claude API",
        "How to hardcode humanitarian routing into your AI revenue system",
        "Palestine solidarity through open source AI art galleries",
        "Building a self-healing autonomous system on GitHub free tier",
    ]
    topic = topics[count % len(topics)]

    prompt = f"""Write a technical dev.to article (700-900 words, markdown) titled: "{topic}"

Real context about the system:
- SolarPunk: autonomous AI system running on GitHub Actions, 100% free tier
- 76 Python engines across 8 layers (L0-L7), orchestrated by OMNIBUS.py
- 15% of all revenue hardcoded to Palestinian Children's Relief Fund (PCRF, EIN 93-1057665)
- Runs 4x/day (cron), self-healing via AUTO_HEALER.py, self-expanding via SELF_BUILDER.py
- Stack: Python 3.11, GitHub Actions, Anthropic Claude API, Gmail SMTP, GitHub Pages
- Live: https://meekotharaccoon-cell.github.io/meeko-nerve-center
- Repo: https://github.com/meekotharaccoon-cell/meeko-nerve-center

Write in first person, technical but accessible. Include real code snippets from the system.
End every article with the GitHub repo link and "Free Palestine. 🍉"
Format: proper markdown with headers, code blocks, etc."""

    content = ask_claude(prompt)
    if not content:
        # Static fallback
        content = f"""# {topic}

I built SolarPunk — an autonomous AI system that runs entirely on GitHub Actions' free tier
and routes 15% of every dollar it makes to the Palestinian Children's Relief Fund.

## Architecture

The core is OMNIBUS.py, an orchestrator running 76 Python engines across 8 layers:

```python
def run():
    for layer in [L0, L1, L2, L3, L4, L5, L6, L7]:
        layer()
```

Each engine is a standalone `.py` file that reads state from `data/` JSON files and writes
back. No database. No server. Just GitHub's free compute, running 4x per day.

## Layer breakdown

- **L0**: GUARDIAN health checks, AUTO_HEALER fixes broken engines, integrity scans
- **L1**: EMAIL_BRAIN reads inbox, AI_WATCHER monitors trends, CONTENT_HARVESTER
- **L2**: GRANT_HUNTER searches funding, REVENUE_FLYWHEEL routes money
- **L3**: LANDING_DEPLOYER builds pages, EMAIL_AGENT_EXCHANGE earns per-task
- **L4**: SOCIAL_PROMOTER, DEV_TO_PUBLISHER (this engine!), AGENT_TWEET_WRITER
- **L5**: GUMROAD_ENGINE, KOFI_ENGINE, PAYPAL_PAYOUT
- **L6**: SELF_BUILDER uses Claude API to write new engines autonomously
- **L7**: MEMORY_PALACE, NIGHTLY_DIGEST, AUTONOMY_PROOF

## The Gaza routing

In REVENUE_FLYWHEEL.py, before any money moves anywhere else:

```python
GAZA_PERCENT = 0.15
to_gaza = total_received * GAZA_PERCENT
route_to_pcrf(to_gaza)  # PCRF EIN: 93-1057665
```

Not configurable. Not optional. Baked into the architecture.

## Try it

The system is fully open source: https://github.com/meekotharaccoon-cell/meeko-nerve-center

Fork it. Adapt it. Route it to whatever cause matters to you.

Free Palestine. 🍉
"""
    return topic, content


def run():
    print("DEV_TO_PUBLISHER starting...")

    if not APIKEY:
        print("  SKIP: DEVTO_API_KEY not set")
        print("  To enable: add DEVTO_API_KEY to GitHub Secrets")
        print("  Get one free at: https://dev.to/settings/extensions")
        return

    state = load_state()

    # Rate limit: max 1 article per 23 hours
    if state.get("last_published"):
        last = datetime.fromisoformat(state["last_published"])
        age  = datetime.now(timezone.utc) - last
        if age < timedelta(hours=23):
            print(f"  SKIP: published {age.seconds//3600}h ago (rate limit: 23h)")
            return

    title, body = generate_article(state.get("total", 0))
    tags = ["python", "opensource", "github", "automation"]

    try:
        result      = publish_to_devto(title, body, tags)
        article_url = result.get("url", "unknown")
        article_id  = result.get("id", "unknown")

        state["published"].append({
            "id":    article_id,
            "title": title,
            "url":   article_url,
            "ts":    datetime.now(timezone.utc).isoformat()
        })
        state["last_published"] = datetime.now(timezone.utc).isoformat()
        state["total"]          = len(state["published"])
        save_state(state)

        print(f"  PUBLISHED: {title}")
        print(f"  URL: {article_url}")
        print(f"  Total articles: {state['total']}")

    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  HTTP ERROR {e.code}: {err[:300]}")
    except Exception as e:
        print(f"  ERROR: {e}")


if __name__ == "__main__":
    run()
