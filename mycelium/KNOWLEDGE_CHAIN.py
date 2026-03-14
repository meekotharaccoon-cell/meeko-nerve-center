# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
KNOWLEDGE_CHAIN.py — The system learns from itself every cycle.

Reads all engine states, synthesizes patterns, generates:
  → Builder prompts for SELF_BUILDER (what to fix, what to build next)
  → Content angles for NEWSLETTER_ENGINE + SOCIAL_PROMOTER
  → Market intelligence for BUSINESS_FACTORY + REVENUE_OPTIMIZER
  → Health patterns for AUTO_HEALER + ARCHITECT
  → Priority actions for OMNIBUS briefing

Runs on free Groq (llama3-70b). When AI is down, falls back to
deterministic rules — the system never stops thinking.

Input:  all data/*.json files (engine states)
Output: data/knowledge_chain_synthesis.json
        → consumed by every strategic engine in the system
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

try:
    from AI_CLIENT import ask_json, ask, ai_available
except ImportError:
    def ask_json(*a, **k): return None
    def ask(*a, **k): return ""
    def ai_available(): return False

def load(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text())
            return d if isinstance(d, (dict, list)) else (fb or {})
        except: pass
    return fb if fb is not None else {}

def run():
    print("KNOWLEDGE_CHAIN running...")
    now = datetime.now(timezone.utc).isoformat()

    # Gather all intelligence
    history    = load("omnibus_history.json", [])
    resonance  = load("resonance_state.json")
    economy    = load("economy_chain_ledger.json")
    signals    = load("signal_chain_state.json")
    growth     = load("growth_chain_state.json")
    analytics  = load("analytics_state.json")
    bottleneck = load("bottleneck_report.json")
    content    = load("content_harvest_state.json")
    newsletter = load("newsletter_state.json")
    gumroad    = load("gumroad_engine_state.json")
    kofi_st    = load("kofi_state.json")
    fork_st    = load("fork_scanner_state.json")
    prev_synth = load("knowledge_chain_synthesis.json", {})

    # Compute derived intelligence (deterministic, no AI needed)
    cycles_run = len(history) if isinstance(history, list) else 0
    health_trend = [
        c.get("health_after", c.get("health", 0))
        for c in (history[-7:] if isinstance(history, list) else [])
    ]
    last_cycle  = history[-1] if isinstance(history, list) and history else {}
    engines_failed = last_cycle.get("engines_failed", [])
    engines_ok_count = len(last_cycle.get("engines_ok", []))
    resonance_score = resonance.get("score", 0)
    total_earned = economy.get("total_earned", 0)
    loop_closed  = economy.get("loop_closed", False)
    stars   = resonance.get("stars", 0) or analytics.get("stars", 0)
    forks   = fork_st.get("total_forks", 0)
    signals_processed = signals.get("processed", 0)
    gumroad_products_live = gumroad.get("total_live", 0)
    kofi_items = kofi_st.get("items_listed", 0)
    substack_subs = newsletter.get("subscribers", 0)

    synthesis = {
        "ts": now,
        "cycles_run": cycles_run,
        "health_trend": health_trend,
        "health_improving": len(health_trend) > 1 and health_trend[-1] > health_trend[0],
        "total_earned": total_earned,
        "loop_closed": loop_closed,
        "resonance_score": resonance_score,
        "engines_failed": engines_failed,
        "engines_ok_count": engines_ok_count,
        "signals_processed": signals_processed,
        "stars": stars,
        "forks": forks,
        "insights": [],
        "builder_prompts": [],
        "content_angles": [],
        "next_engines_to_build": [],
        "priority_action": "",
        "bottlenecks": [],
    }

    # ── Deterministic insights ─────────────────────────────────────────────────
    ins  = synthesis["insights"]
    bp   = synthesis["builder_prompts"]
    ca   = synthesis["content_angles"]
    ne   = synthesis["next_engines_to_build"]
    bot  = synthesis["bottlenecks"]

    if engines_failed:
        ins.append(f"❌ Failing engines: {', '.join(engines_failed[:5])} — AUTO_HEALER should patch these")
        bp.append(f"Fix these failing SolarPunk engines by reading each file, finding the error, and patching: {', '.join(engines_failed[:5])}")

    if total_earned == 0 and cycles_run > 5:
        bot.append("No revenue yet — distribution is the bottleneck, not the product")
        ins.append("Zero revenue after many cycles = the work is built, the door isn't open yet")
        ca.append("Show the system running in real-time — builders love process transparency")
        ca.append("Gaza donation tracking makes the mission the marketing — show the counter")
        ne.append("REDDIT_POSTER — post to r/SideProject, r/MachineLearning, r/selfhosted, r/opensource daily")
        ne.append("SHOW_HN_POSTER — auto-draft Show HN post and flag it for Meeko to submit")
        ne.append("PRODUCTHUNT_DRAFTER — generate Product Hunt submission and save to data/ph_submission.json")

    if gumroad_products_live == 0:
        bot.append("Gumroad products queued but not live — needs manual creation at gumroad.com")
        ins.append("10 products ready in gumroad_listings.json, none live yet. This is the fastest revenue path.")
        synthesis["priority_action"] = "Go to gumroad.com, create the 10 products from data/gumroad_listings.json. Fastest path to first dollar."

    if kofi_items == 0:
        bot.append("Ko-fi shop not set up — copy items from data/quick_revenue.html")
        ne.append("KOFI_AUTO_POSTER — automatically create Ko-fi shop items via API")

    if stars >= 1 and not prev_synth.get("hn_posted"):
        ins.append(f"{stars} GitHub star(s) = social proof. Time to post Show HN.")
        ca.append("Show HN: I built a self-running AI agent that auto-donates to Gaza — post at news.ycombinator.com")

    if substack_subs == 0:
        ne.append("SIGNUP_WIDGET — embed email signup on every page, feed into Substack/Mailchimp")

    if forks > 0:
        ins.append(f"{forks} forks = people building on SolarPunk. Massive social proof. Feature them.")
        ca.append(f"Shoutout the {forks} builders who forked SolarPunk — community = moat")

    if synthesis["health_improving"]:
        ins.append("System health is improving — acceleration phase, add distribution engines")
    else:
        ins.append("Health plateau — fix failing engines before adding new ones")

    # ── AI-enhanced synthesis (free Groq) ─────────────────────────────────────
    if ai_available() and cycles_run > 0:
        context = f"""SolarPunk autonomous AI revenue system. Current state:
- Cycles: {cycles_run} | Health trend: {health_trend[-3:]} | Earned: ${total_earned:.2f}
- Resonance: {resonance_score}/100 | Stars: {stars} | Forks: {forks}
- Failing engines: {engines_failed[:5]}
- Gumroad live: {gumroad_products_live} | Ko-fi items: {kofi_items}
- Loop closed: {loop_closed}
- Known bottlenecks: {bot}

Give exactly:
1. The single highest-leverage action to take RIGHT NOW for first revenue
2. One new engine name + one sentence purpose (fill a gap in the system)
3. One tweet to post today

Respond as JSON: {{"priority": str, "engine": {{"name": str, "purpose": str}}, "tweet": str}}"""

        result = ask_json(context)
        if result:
            if result.get("priority"):
                synthesis["priority_action"] = result["priority"]
                ins.append(f"🤖 AI says: {result['priority'][:100]}")
            if result.get("engine", {}).get("name"):
                ne.append(f"{result['engine']['name']} — {result['engine'].get('purpose', '')}")
                bp.append(f"Build {result['engine']['name']}: {result['engine'].get('purpose', '')}")
            if result.get("tweet"):
                ca.append(result["tweet"])
            print(f"  🧠 AI synthesis: {synthesis['priority_action'][:80]}")
        else:
            print(f"  🧠 AI unavailable — deterministic synthesis only")

    # ── Dedupe and trim ────────────────────────────────────────────────────────
    synthesis["next_engines_to_build"] = list(dict.fromkeys(ne))[:10]
    synthesis["content_angles"]        = list(dict.fromkeys(ca))[:10]
    synthesis["builder_prompts"]       = list(dict.fromkeys(bp))[:10]
    synthesis["bottlenecks"]           = list(dict.fromkeys(bot))[:10]

    if not synthesis["priority_action"] and bot:
        synthesis["priority_action"] = bot[0]

    (DATA / "knowledge_chain_synthesis.json").write_text(json.dumps(synthesis, indent=2))

    print(f"  🧬 Insights: {len(ins)} | Next engines: {len(synthesis['next_engines_to_build'])} | "
          f"Content angles: {len(synthesis['content_angles'])}")
    print(f"  🎯 Priority: {synthesis['priority_action'][:80]}")
    for i in ins[:3]:
        print(f"     • {i[:80]}")

if __name__ == "__main__": run()
