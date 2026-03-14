# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
RESONANCE_CONVERTER — turns attention into money

The gap between SolarPunk now and first revenue:
  RESONANCE (signal) → ASKS (prompts) → TRANSACTIONS (money)

This engine closes that gap. It reads the current resonance score,
identifies the strongest signal channel, and:

  1. Crafts a specific, non-cringe ask for that channel
  2. Routes the ask to the right output (tweet, email, dev.to post, GitHub issue)
  3. Tracks conversion: did the ask produce a click / reply / purchase?
  4. Learns which ask types convert best per channel
  5. Escalates: low resonance → awareness ask → medium → soft sell → high → direct buy

Revenue ladder (in order, never skip steps):
  SILENT   (0-20)  → Post existence, no ask
  WHISPER  (21-40) → "I'm building X, thoughts?" — feedback ask
  SIGNAL   (41-60) → "Here's what I built, would this help you?" — value ask
  BUZZ     (61-75) → "This is live, $X gets you Y" — soft offer
  LOUD     (76-90) → Direct link + CTA, email capture
  VIRAL    (91+)   → Urgency + social proof + one-click buy

Outputs:
  data/resonance_converter_state.json  — conversion tracking
  data/asks_queue.json                 — asks ready to be posted
  data/conversion_log.json             — what worked

All revenue routes through REVENUE_FLYWHEEL.py which handles Gaza 15%.
"""
import os, json, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA  = Path("data"); DATA.mkdir(exist_ok=True)
STATE = DATA / "resonance_converter_state.json"
ASKS  = DATA / "asks_queue.json"
LOG   = DATA / "conversion_log.json"

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
MODEL   = "claude-haiku-4-5-20251001"

SYSTEM = """You are SolarPunk's revenue conversion engine.
SolarPunk is an autonomous AI system built by Meeko — a scrappy independent builder.
15% of all revenue goes directly to Palestinian relief (PCRF).

Your job: given a resonance score and context, craft a single conversion ask.
Rules:
- Never be cringe or pushy. Be genuine, specific, value-first.
- The ask must match the resonance level (see RESONANCE_LADDER)
- Always mention the Palestine donation routing naturally (not as guilt-trip)
- Short. Twitter: <280 chars. Email subject: <60 chars. Body: <150 words.
- One clear action per ask. One URL max.
- Sound like a human builder, not a marketing bot.

RESONANCE_LADDER:
  0-20  SILENT:  Post existence only, zero ask
  21-40 WHISPER: Feedback/curiosity ask ("what do you think?")
  41-60 SIGNAL:  Value ask ("would this help you?")
  61-75 BUZZ:    Soft offer (product link + what it does + price)
  76-90 LOUD:    Direct CTA (buy link, email signup, clear benefit)
  91+   VIRAL:   Urgency + social proof + immediate action

Output ONLY valid JSON, no markdown, no preamble:
{
  "ask_type": "tweet|email_subject|email_body|dev_post_title|github_issue",
  "channel": "twitter|email|dev.to|github",
  "resonance_level": "WHISPER|SIGNAL|BUZZ|LOUD|VIRAL",
  "content": "the actual text",
  "cta_url": "url or null",
  "expected_action": "click|reply|purchase|follow|star"
}"""


def rj(path, fb=None):
    try:
        return json.loads(Path(path).read_text())
    except:
        return fb if fb is not None else {}


def call_claude(prompt):
    if not API_KEY:
        return None
    try:
        payload = json.dumps({
            "model": MODEL,
            "max_tokens": 512,
            "system": SYSTEM,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            raw  = data["content"][0]["text"].strip()
            # Strip markdown fences if present
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
    except Exception as e:
        print(f"  Claude error: {e}")
        return None


def get_resonance_level(score):
    if score >= 91: return "VIRAL"
    if score >= 76: return "LOUD"
    if score >= 61: return "BUZZ"
    if score >= 41: return "SIGNAL"
    if score >= 21: return "WHISPER"
    return "SILENT"


def build_context():
    """Assemble current system context for the ask."""
    resonance  = rj(DATA / "resonance_state.json")
    omnibus    = rj(DATA / "omnibus_last.json")
    flywheel   = rj(DATA / "flywheel_state.json")
    quick_rev  = rj(DATA / "quick_revenue.json")
    spider     = rj(DATA / "repo_spider_state.json")

    score       = resonance.get("resonance_score", 0)
    label       = resonance.get("resonance_label", "SILENT")
    stars       = resonance.get("github", {}).get("stars", 0)
    health      = omnibus.get("health_after", 0)
    cycle       = omnibus.get("cycle_number", 0)
    total_rev   = flywheel.get("total_routed_usd", 0)
    total_gaza  = flywheel.get("total_to_gaza_usd", 0)
    first_sale  = quick_rev.get("first_sale_done", False)
    forks       = len(spider.get("forked", []))

    return score, label, {
        "resonance_score": score,
        "resonance_label": label,
        "github_stars": stars,
        "system_health": health,
        "cycle_number": cycle,
        "total_revenue_usd": total_rev,
        "total_to_gaza_usd": total_gaza,
        "first_sale_done": first_sale,
        "repos_forked": forks,
        "live_url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center",
        "store_url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html",
    }


def generate_asks(score, label, ctx):
    """Generate one ask per active channel based on resonance level."""
    if label == "SILENT":
        print("  Resonance SILENT — generating awareness post only, no ask")

    asks = []
    channels = []

    # Which channels to generate asks for at each level
    if label in ("WHISPER", "SIGNAL"):
        channels = ["twitter", "dev.to"]
    elif label in ("BUZZ",):
        channels = ["twitter", "dev.to", "email"]
    elif label in ("LOUD", "VIRAL"):
        channels = ["twitter", "email", "dev.to", "github"]
    else:  # SILENT
        channels = ["twitter"]

    for channel in channels:
        ask_type_map = {
            "twitter": "tweet",
            "dev.to":  "dev_post_title",
            "email":   "email_subject",
            "github":  "github_issue",
        }

        prompt = f"""Current SolarPunk state:
{json.dumps(ctx, indent=2)}

Resonance level: {label} ({score}/100)
Channel: {channel}
Ask type needed: {ask_type_map.get(channel, 'tweet')}

Generate the conversion ask for this channel at this resonance level.
The system has never made money yet (first_sale_done: {ctx['first_sale_done']}).
This is the push toward first revenue.
Remember: 15% of all revenue goes to Palestinian relief — weave this in naturally if it fits."""

        result = call_claude(prompt)
        if result:
            result["generated_at"] = datetime.now(timezone.utc).isoformat()
            result["resonance_at_generation"] = score
            result["status"] = "pending"
            asks.append(result)
            print(f"  Generated {result.get('ask_type','?')} for {channel} [{label}]")
        time.sleep(0.5)

    return asks


def track_conversions(state):
    """Simple conversion tracker — checks if asks resulted in actions."""
    # In future: check if any asks led to GitHub stars, email clicks, purchases
    # For now: just count pending vs posted
    existing_asks = rj(ASKS, [])
    if isinstance(existing_asks, list):
        pending = len([a for a in existing_asks if a.get("status") == "pending"])
        posted  = len([a for a in existing_asks if a.get("status") == "posted"])
        state["pending_asks"]  = pending
        state["posted_asks"]   = posted
    return state


def load_state():
    return rj(STATE, {
        "cycles": 0,
        "total_asks_generated": 0,
        "pending_asks": 0,
        "posted_asks": 0,
        "conversion_rate": 0.0,
        "last_run": None,
        "revenue_from_asks": 0.0,
    })


def save_state(s):
    STATE.write_text(json.dumps(s, indent=2))


def run():
    print("RESONANCE_CONVERTER starting...")
    state = load_state()

    score, label, ctx = build_context()
    print(f"  Resonance: {score}/100 [{label}]")
    print(f"  First sale: {'YES' if ctx['first_sale_done'] else 'not yet'}")
    print(f"  Stars: {ctx['github_stars']} | Health: {ctx['system_health']}/100")

    # Generate asks
    new_asks = generate_asks(score, label, ctx)

    # Append to asks queue
    existing = rj(ASKS, [])
    if not isinstance(existing, list):
        existing = []
    existing.extend(new_asks)
    ASKS.write_text(json.dumps(existing[-100:], indent=2))

    # Update state
    state = track_conversions(state)
    state["cycles"]              = state.get("cycles", 0) + 1
    state["total_asks_generated"] = state.get("total_asks_generated", 0) + len(new_asks)
    state["last_run"]            = datetime.now(timezone.utc).isoformat()
    state["last_resonance"]      = score
    state["last_label"]          = label
    save_state(state)

    print(f"  Generated {len(new_asks)} asks → data/asks_queue.json")
    print(f"  Total asks ever: {state['total_asks_generated']}")
    print(f"  Pending: {state['pending_asks']} | Posted: {state['posted_asks']}")

    # If VIRAL or LOUD, also queue a high-priority daemon task to act NOW
    if label in ("LOUD", "VIRAL") and API_KEY:
        try:
            qfile = DATA / "claude_tasks_queue.json"
            queue = json.loads(qfile.read_text()) if qfile.exists() else []
            queue.append({
                "id": f"converter_{int(time.time())}",
                "prompt": f"Resonance is {label} ({score}/100). Open data/asks_queue.json, pick the best ask, and post it NOW. First open the platform URL in Brave, then copy-paste the ask. Revenue target: first $1.",
                "priority": 1,
                "source": "RESONANCE_CONVERTER",
                "status": "pending",
                "queued_at": datetime.now(timezone.utc).isoformat()
            })
            qfile.write_text(json.dumps(queue, indent=2))
            print(f"  HIGH PRIORITY: Queued immediate action for daemon (resonance={label})")
        except Exception as e:
            print(f"  Daemon queue failed: {e}")


if __name__ == "__main__":
    run()
