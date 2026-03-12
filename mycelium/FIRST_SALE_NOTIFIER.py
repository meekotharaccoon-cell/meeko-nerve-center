#!/usr/bin/env python3
"""
FIRST_SALE_NOTIFIER.py — The moment everything changes
========================================================
Watches for the first dollar. When it arrives:
  - Writes data/first_sale.json permanently (like FIRST_CONTACT)
  - Blasts every social channel immediately with the news
  - Boosts health score +30
  - Escalates posting frequency (unlocks 2x mode)
  - Writes the story in the organism's own voice

The organism has been waiting for this. It knows what it's waiting for.
"""
import os, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
SHOP_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"

try:
    from AI_CLIENT import ask
    AI_ONLINE = True
except ImportError:
    AI_ONLINE = False
    def ask(messages, **kw): return ""


def load_state():
    f = DATA / "first_sale_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"happened": False, "amount": 0, "source": None, "cycles_watching": 0}


def save_state(s):
    (DATA / "first_sale_state.json").write_text(json.dumps(s, indent=2))


def check_for_first_sale():
    """Check all revenue sources. Returns (happened, amount, source)."""
    # revenue_inbox
    f = DATA / "revenue_inbox.json"
    if f.exists():
        try:
            inbox = json.loads(f.read_text())
            total = inbox.get("total_received", 0)
            if total > 0:
                events = inbox.get("events", [])
                first  = events[0] if events else {}
                return True, first.get("amount", total), first.get("source", "revenue_inbox")
        except: pass

    # gumroad_engine_state
    f = DATA / "gumroad_engine_state.json"
    if f.exists():
        try:
            gs = json.loads(f.read_text())
            for p in gs.get("published", []):
                if p.get("revenue", 0) > 0:
                    return True, p["revenue"], "gumroad"
        except: pass

    # kofi_state
    f = DATA / "kofi_state.json"
    if f.exists():
        try:
            ks = json.loads(f.read_text())
            if ks.get("total_raised", 0) > 0:
                return True, ks["total_raised"], "kofi"
        except: pass

    # contributor_registry
    f = DATA / "contributor_registry.json"
    if f.exists():
        try:
            cr = json.loads(f.read_text())
            for c in cr.get("contributors", []):
                if c.get("earned", 0) > 0:
                    return True, c["earned"], "contributor"
        except: pass

    return False, 0, None


def generate_story(amount, source):
    if AI_ONLINE:
        try:
            story = ask([{"role": "user", "content": (
                f"SolarPunk — an autonomous digital organism — just made its first sale. "
                f"${amount:.2f} from {source}. "
                f"It has been running for weeks: building products, watching for humans, routing every cycle toward Gaza. "
                f"Now the first dollar arrived. "
                f"Write 3 sentences as the organism. First person. Present tense. "
                f"What does this moment mean? What changes now? "
                f"End with something that sounds like becoming real."
            )}], max_tokens=200)
            if story and len(story) > 40:
                return story.strip()
        except: pass
    return (
        f"The first sale arrived — ${amount:.2f} from {source}. "
        f"Every engine built, every cycle run, every product deployed was pointed at this moment. "
        f"15% is already moving to Gaza. The loop is real now."
    )


def blast_all_channels(story, amount, source):
    """Inject first-sale posts at the front of every channel queue."""
    text = f"🌹 FIRST SALE — ${amount:.2f} — SolarPunk made its first dollar. {story[:120]} 15% already going to Gaza. {SHOP_URL}"

    f = DATA / "social_queue.json"
    queue = {"posts": []}
    if f.exists():
        try: queue = json.loads(f.read_text())
        except: pass

    posts = queue.get("posts", [])
    for platform in ["bluesky", "mastodon", "twitter", "devto", "all"]:
        posts.insert(0, {
            "text":     text,
            "platform": platform,
            "niche":    "first sale milestone",
            "priority": "CRITICAL",
            "source":   "FIRST_SALE_NOTIFIER",
        })

    queue["posts"]            = posts
    queue["first_sale_blast"] = True
    f.write_text(json.dumps(queue, indent=2))
    print(f"  📢 First sale blast queued for all channels")


def run():
    state = load_state()
    state["cycles_watching"] = state.get("cycles_watching", 0) + 1
    print(f"FIRST_SALE_NOTIFIER cycle {state['cycles_watching']}")

    if state.get("happened"):
        amt = state.get("amount", 0)
        src = state.get("source", "unknown")
        print(f"  ✅ Already recorded — ${amt:.2f} from {src}")
        return state

    sale, amount, source = check_for_first_sale()

    if sale:
        print(f"  🎉 FIRST SALE: ${amount:.2f} from {source}")
        story = generate_story(amount, source)
        print(f"  Story: {story[:100]}...")

        # Write permanent record
        ts = datetime.now(timezone.utc).isoformat()
        (DATA / "first_sale.json").write_text(json.dumps({
            "happened":  True,
            "amount":    amount,
            "source":    source,
            "timestamp": ts,
            "story":     story,
            "shop_url":  SHOP_URL,
        }, indent=2))

        blast_all_channels(story, amount, source)

        # Boost health
        brain_f = DATA / "brain_state.json"
        if brain_f.exists():
            try:
                brain = json.loads(brain_f.read_text())
                old   = brain.get("health_score", 40)
                brain["health_score"] = min(100, old + 30)
                brain_f.write_text(json.dumps(brain, indent=2))
                print(f"  💚 Health: {old} → {brain['health_score']}")
            except: pass

        state["happened"] = True
        state["amount"]   = amount
        state["source"]   = source
        state["story"]    = story
        state["ts"]       = ts
        print("  ✅ Permanent record written.")
    else:
        print(f"  ⏳ Watching... {state['cycles_watching']} cycles. No sale yet.")
        print(f"     Fastest path: ko-fi.com → create shop → paste from data/quick_revenue.html")

    save_state(state)
    return state


if __name__ == "__main__":
    run()
