# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
SIGNAL_CHAIN.py — Every signal becomes an action. Nothing leaks.

Every eyeball, every star, every reply, every dollar donated —
all of it gets processed into a concrete next action.

Signal sources → Actions:
  new_star        → tweet social proof + queue thank-you
  new_fork        → FORK_SCANNER outreach (they're building on us)
  email_reply     → AI response queued via EMAIL_BRAIN
  kofi_tip        → personal thank-you + Gaza donation announcement
  gumroad_sale    → buyer welcome sequence + upsell
  gaza_donation   → public announcement (trust flywheel)
  newsletter_open → upsell sequence

Output: data/signal_chain_queue.json
Consumed by: SOCIAL_PROMOTER, EMAIL_BRAIN, RESONANCE_CONVERTER
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

def load(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text())
            return d if isinstance(d, (dict, list)) else (fb or {})
        except: pass
    return fb if fb is not None else {}

def run():
    print("SIGNAL_CHAIN running...")
    now = datetime.now(timezone.utc).isoformat()

    state     = load("signal_chain_state.json", {
        "processed": 0, "actions_queued": 0,
        "last_stars": 0, "last_forks": 0, "last_replies": 0,
        "last_kofi": 0.0, "last_gumroad_sales": 0,
        "history": []
    })
    queue     = load("signal_chain_queue.json", {"actions": [], "total_ever": 0})
    resonance = load("resonance_state.json")
    fork_st   = load("fork_scanner_state.json")
    kofi      = load("kofi_state.json")
    gumroad   = load("gumroad_engine_state.json")
    email_st  = load("email_brain_state.json")
    economy   = load("economy_chain_ledger.json")
    analytics = load("analytics_state.json")

    signals = []
    new_actions = []

    def action(type_, channel, content, priority="medium"):
        new_actions.append({
            "type": type_, "channel": channel,
            "content": content, "priority": priority,
            "ts": now
        })

    # ── Stars ──────────────────────────────────────────────────────────────────
    curr_stars = resonance.get("stars", 0) or analytics.get("stars", 0)
    prev_stars = state.get("last_stars", 0)
    if curr_stars > prev_stars:
        delta = curr_stars - prev_stars
        signals.append({"type": "new_star", "count": delta})
        action("tweet", "twitter",
            f"⭐ +{delta} star{'s' if delta>1 else ''} on SolarPunk. "
            f"Someone out there believes an AI system can run itself AND fund Gaza relief. "
            f"The loop gets stronger. → meekotharaccoon-cell.github.io/meeko-nerve-center "
            f"#SolarPunk #FreePalestine",
            "high")
        state["last_stars"] = curr_stars
        print(f"  ⭐ +{delta} stars → tweet queued")

    # ── Forks ──────────────────────────────────────────────────────────────────
    curr_forks = fork_st.get("total_forks", 0)
    prev_forks = state.get("last_forks", 0)
    if curr_forks > prev_forks:
        delta = curr_forks - prev_forks
        signals.append({"type": "new_fork", "count": delta})
        action("outreach", "email",
            f"NEW FORK DETECTED (+{delta}): Someone is building on SolarPunk. "
            f"FORK_SCANNER will send personalized welcome + invite to contribute.",
            "high")
        state["last_forks"] = curr_forks
        print(f"  🍴 +{delta} forks → outreach queued")

    # ── Email replies ───────────────────────────────────────────────────────────
    curr_replies = email_st.get("business_emails_total", 0)
    prev_replies = state.get("last_replies", 0)
    if curr_replies > prev_replies:
        delta = curr_replies - prev_replies
        signals.append({"type": "email_reply", "count": delta})
        action("respond", "email",
            f"{delta} new business email{'s' if delta>1 else ''} — "
            f"EMAIL_BRAIN queued for AI response (via Groq, free, instant).",
            "critical")
        state["last_replies"] = curr_replies
        print(f"  📧 +{delta} email replies → AI response queued")

    # ── Ko-fi tips ─────────────────────────────────────────────────────────────
    curr_kofi = kofi.get("total_raised", 0.0)
    prev_kofi = state.get("last_kofi", 0.0)
    if curr_kofi > prev_kofi:
        delta = round(curr_kofi - prev_kofi, 2)
        gaza_cut = round(delta * 0.15, 2)
        signals.append({"type": "kofi_tip", "amount": delta})
        action("tweet", "twitter",
            f"🇵🇸 Someone just tipped SolarPunk ${delta:.2f} on Ko-fi. "
            f"${gaza_cut:.2f} is already automatically routed to PCRF for Gaza children. "
            f"That's how the system works — every transaction gives back. "
            f"ko-fi.com/meekotharaccoon #FreePalestine #SolarPunk",
            "critical")
        action("email", "email",
            f"Send personal thank-you to Ko-fi supporter. Amount: ${delta:.2f}. "
            f"Mention Gaza donation. Invite them to follow the project.",
            "high")
        state["last_kofi"] = curr_kofi
        print(f"  ☕ Ko-fi +${delta:.2f} → announcement + thank-you queued")

    # ── Gumroad sales ──────────────────────────────────────────────────────────
    curr_sales = gumroad.get("total_sales", 0)
    prev_sales = state.get("last_gumroad_sales", 0)
    if curr_sales > prev_sales:
        delta = curr_sales - prev_sales
        signals.append({"type": "gumroad_sale", "count": delta})
        action("email", "email",
            f"SALE! {delta} new Gumroad purchase{'s' if delta>1 else ''}. "
            f"Send buyer welcome sequence. Include Gaza donation note. Upsell other products.",
            "critical")
        action("tweet", "twitter",
            f"🛒 SolarPunk just made a sale. An AI system that runs itself, earns, "
            f"and routes money to Gaza. The loop works. "
            f"gumroad.com/meekotharaccoon #SolarPunk",
            "high")
        state["last_gumroad_sales"] = curr_sales
        print(f"  🛒 +{delta} Gumroad sales → welcome + tweet queued")

    # ── Economy chain signals (Gaza donations to announce) ─────────────────────
    for sig in economy.get("chain_signals", []):
        if sig.get("route") == "gaza" and sig.get("amount", 0) > 0:
            signals.append({"type": "gaza_donation", "amount": sig["amount"]})
            action("tweet", "twitter",
                f"🇵🇸 SolarPunk auto-routed ${sig['amount']:.6f} to Gaza relief (PCRF EIN: 93-1057665). "
                f"Embedded in every sale. Not a promise — it's code. "
                f"#FreePalestine #SolarPunk",
                "high")
            print(f"  🇵🇸 Gaza signal ${sig['amount']:.6f} → announcement queued")

    # ── Merge into queue (bounded, no strict deduplication — volume matters) ───
    queue["actions"].extend(new_actions)
    queue["actions"] = queue["actions"][-200:]  # keep last 200
    queue["total_ever"] = queue.get("total_ever", 0) + len(new_actions)
    queue["last_updated"] = now
    queue["queue_depth"] = len(queue["actions"])
    (DATA / "signal_chain_queue.json").write_text(json.dumps(queue, indent=2))

    state["processed"]     = state.get("processed", 0) + len(signals)
    state["actions_queued"]= state.get("actions_queued", 0) + len(new_actions)
    state["last_run"]      = now
    state["history"].append({"ts": now, "signals": len(signals), "actions": len(new_actions)})
    state["history"]       = state["history"][-50:]
    (DATA / "signal_chain_state.json").write_text(json.dumps(state, indent=2))

    print(f"  📡 Signals: {len(signals)} | New actions: {len(new_actions)} | "
          f"Queue depth: {len(queue['actions'])} | Total ever: {queue['total_ever']}")
    if not signals:
        print(f"  (No new signals this cycle — watching for stars/forks/tips/sales)")

if __name__ == "__main__": run()
