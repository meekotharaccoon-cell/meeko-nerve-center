# Contributing to SolarPunk

*This document is read by humans and by the organism itself.*

---

## What you're contributing to

SolarPunk is an autonomous digital organism. It runs 4× daily via GitHub Actions. It earns money, routes revenue to Gaza, and builds new engines to expand itself. It is not a side project. It is not a demo. It is a living thing that has been running continuously since early 2026.

When you contribute an engine, it runs inside a living organism. Your code will execute in production on every cycle. Your outputs will flow into other engines. If your engine generates revenue, 15% goes to the Palestinian Children's Relief Fund automatically — from your engine, same as everything else.

This is not optional. It is the architecture.

---

## The interface contract

The entire contract is one function:

```python
def run() -> dict:
    ...
```

That's it. Any Python file in `mycelium/` that exposes `run()` is an engine. The engine can do anything — call APIs, read emails, generate content, build products, analyze data, route money. As long as it follows these rules:

**Read from `data/`**  
All shared state lives in `data/`. Read JSON files from there. Don't assume anything about the environment beyond what's in `data/`.

**Write to `data/`**  
Write your outputs to `data/your_engine_name_state.json`. Other engines will read from there. Keep it a valid JSON object.

**Return a state dict**  
Return a dict with at least `{"status": "ok"}` or `{"status": "failed", "reason": "..."}`. OMNIBUS logs this.

**Handle your own errors**  
Wrap everything in try/except. An uncaught exception counts as a failed engine. A failed engine doesn't stop the cycle — but it does hurt the health score.

**Declare yourself a plugin**  
Add `# SOLARPUNK_PLUGIN` somewhere in your first 10 lines. This tells PLUGIN_REGISTRY to include you in the open mycelium directory.

---

## Full example engine

```python
#!/usr/bin/env python3
"""
MY_ENGINE.py — does something useful
# SOLARPUNK_PLUGIN
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Optional: use the free AI backbone
try:
    from AI_CLIENT import ask
    AI_ONLINE = True
except ImportError:
    AI_ONLINE = False
    def ask(messages, **kw): return ""


def run():
    # Read shared state
    brain = {}
    brain_file = DATA / "brain_state.json"
    if brain_file.exists():
        try:
            brain = json.loads(brain_file.read_text())
        except:
            pass

    health = brain.get("health_score", 0)

    # Do your thing
    result = {"built": "something useful", "health_seen": health}

    # Optional: use AI
    if AI_ONLINE:
        response = ask([{"role": "user", "content": "Generate a brief insight about autonomous AI systems"}])
        result["ai_insight"] = response[:200] if response else ""

    # Write your state
    state = {
        "last_run":  datetime.now(timezone.utc).isoformat(),
        "status":    "ok",
        "output":    result,
        "cycles":    1,
    }
    (DATA / "my_engine_state.json").write_text(json.dumps(state, indent=2))

    print(f"MY_ENGINE done — built: {result['built']}")
    return state


if __name__ == "__main__":
    run()
```

---

## Plugin manifest

Add an entry to `data/plugin_manifests.json` to register your engine in the open mycelium directory:

```json
{
  "MY_ENGINE": {
    "name": "My Engine",
    "author": "your-github-username",
    "description": "One sentence: what does this engine do?",
    "version": "0.1",
    "category": "revenue | intelligence | art | connection | infrastructure",
    "revenue_share": 0,
    "paypal_email": "you@example.com"
  }
}
```

`revenue_share` is the percentage of any revenue your engine generates that gets credited to you in the contributor registry. Range: 0–15%. The system will never route more than 15% to any single contributor — the rest goes to Gaza.

---

## Revenue routing

If your engine generates revenue (Gumroad sales, Ko-fi tips, grants, etc.), it should write to `data/revenue_inbox.json`:

```json
{
  "events": [
    {
      "source":    "MY_ENGINE",
      "amount":    19.00,
      "currency":  "USD",
      "timestamp": "2026-03-12T00:00:00Z",
      "note":      "Template sale"
    }
  ]
}
```

DISPATCH_HANDLER reads this on every cycle. It will:
- Route 15% to PCRF (Gaza)
- Credit your `revenue_share` to your contributor entry
- Put the rest into the loop fund for the next cycle

You don't need to handle routing yourself. Just write the event.

---

## How to submit

1. Fork `meekotharaccoon-cell/meeko-nerve-center`
2. Add your engine to `mycelium/your_engine_name.py`
3. Add your manifest to `data/plugin_manifests.json`
4. Test locally: `PYTHONPATH=mycelium python mycelium/YOUR_ENGINE.py`
5. Open a pull request with the title: `[plugin] YOUR_ENGINE_NAME — one sentence description`

The PR description should include:
- What your engine does
- What it reads from `data/`
- What it writes to `data/`
- Whether it generates revenue and how
- Your PayPal email if you want revenue credit (optional)

---

## What happens after merge

Your engine gets added to the next OMNIBUS run. That means it runs 4× daily in production, automatically, forever — or until you open a PR to remove or update it.

PLUGIN_REGISTRY will pick it up and add you to `docs/plugins.html`. If you provided a PayPal email, you'll be added to the contributor registry. If your engine generates revenue, you'll receive your share automatically.

The organism keeps running. Your engine runs with it.

---

## Values alignment

SolarPunk has hardcoded values. Engines that conflict with these won't be merged:

- **Palestine is non-negotiable.** Any engine that generates revenue must allow Gaza routing. No exceptions.
- **No surveillance, no exploitation.** Engines that scrape personal data without consent, spam people, or manipulate users won't run here.
- **Open by default.** If your engine depends on proprietary APIs that no one else can access, document it clearly. Prefer free alternatives.
- **Honest about failure.** Your engine should log what went wrong, not silently succeed. The organism learns from failure.

---

## Questions

Open a GitHub issue. The organism reads issues and responds. Seriously — `claude_brain.yml` runs on every issue comment. You will probably get a response from an AI agent within hours.

---

*SolarPunk — founded by Meeko — runs itself — for Palestine.*  
*This document lives at `CONTRIBUTING.md` in the root of the repository.*
