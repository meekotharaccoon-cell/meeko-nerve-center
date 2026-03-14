# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""ARCHITECT.py — SolarPunk's Strategic Brain
============================================
Runs every cycle in L6. Reads the full system state, identifies gaps,
and writes architect_plan.json that tells SELF_BUILDER and BUSINESS_FACTORY
what to build next.

This is the "what should the system build next?" engine.
SELF_BUILDER and BUSINESS_FACTORY read this plan before deciding.

Every cycle:
1. Audit what's working vs failing (from omnibus_last.json)
2. Check revenue gaps (what streams are zero?)
3. Use AI to propose 3 new engine ideas + 3 new business niches
4. Score and prioritize them
5. Write architect_plan.json with ranked priorities
6. Update self-improvement log with what changed
"""
import os, json, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask, ask_json
    AI_ONLINE = True
except ImportError:
    AI_ONLINE = False
    def ask(messages, **kw): return ""
    def ask_json(prompt, **kw): return None

DATA = Path("data"); DATA.mkdir(exist_ok=True)

REVENUE_STREAMS = [
    "email_agent_exchange", "gumroad", "ko_fi", "github_sponsors",
    "amazon_affiliate", "substack", "redbubble", "etsy"
]


def load():
    f = DATA / "architect_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "plans_written": 0, "engine_ideas": [], "niche_ideas": [],
            "revenue_gaps": [], "improvement_log": []}


def save(s):
    s["improvement_log"] = s.get("improvement_log", [])[-100:]
    (DATA / "architect_state.json").write_text(json.dumps(s, indent=2))


def rj(fname, fallback=None):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fallback if fallback is not None else {}


def audit_system():
    """Build full system snapshot for AI analysis."""
    omnibus = rj("omnibus_last.json")
    exchange = rj("email_exchange_state.json")
    brain = rj("brain_state.json")
    flywheel = rj("flywheel_summary.json")
    self_builder = rj("self_builder_state.json")
    biz_factory = rj("business_factory_state.json")
    kofi_tracker = rj("kofi_tracker_state.json")

    engines_ok     = omnibus.get("engines_ok", [])
    engines_failed = omnibus.get("engines_failed", [])
    engines_skip   = omnibus.get("engines_skipped", [])

    return {
        "health":          brain.get("health_score", 0),
        "total_loops":     brain.get("total_loops_completed", 0),
        "engines_ok":      engines_ok,
        "engines_failed":  engines_failed,
        "engines_skipped": engines_skip,
        "exchange_tasks":  exchange.get("total_tasks", 0),
        "exchange_earned": exchange.get("total_earned", 0.0),
        "exchange_gaza":   exchange.get("total_to_gaza", 0.0),
        "kofi_verified":   kofi_tracker.get("total_verified", 0.0),
        "businesses_built": len(biz_factory.get("businesses_built", [])),
        "engines_built":   self_builder.get("total_built", 0),
        "revenue_potential": biz_factory.get("total_revenue_potential", 0),
        "active_revenue_streams": [s for s in REVENUE_STREAMS
                                   if not all(rj(f"{s}_state.json") == {} for _ in [1])],
    }


def identify_revenue_gaps(audit):
    """Find where revenue is zero or low."""
    gaps = []
    if audit["exchange_earned"] == 0:
        gaps.append("EMAIL_AGENT_EXCHANGE: no tasks completed yet — needs promotion")
    if audit["businesses_built"] < 3:
        gaps.append(f"BUSINESS_FACTORY: only {audit['businesses_built']} businesses built — keep building")
    if audit["kofi_verified"] == 0:
        gaps.append("No verified Ko-fi payments yet — need more promotion + task completion")
    if "SOCIAL_PROMOTER" in audit["engines_failed"]:
        gaps.append("SOCIAL_PROMOTER failing — fix needed, losing promotion cycles")
    if "LANDING_DEPLOYER" in audit["engines_failed"]:
        gaps.append("LANDING_DEPLOYER failing — businesses not getting live pages")
    return gaps


def generate_plan(audit, gaps):
    """Use AI to generate new engine ideas and business niches based on system state."""
    if not AI_ONLINE:
        return _fallback_plan(audit, gaps)

    already_built_engines = [b.get("name", "") for b in rj("self_builder_state.json").get("built", [])]
    already_built_niches  = [b.get("niche", "") for b in rj("business_factory_state.json").get("businesses_built", [])]

    prompt = f"""You are ARCHITECT, the strategic brain of SolarPunk — an autonomous AI system that builds revenue streams to fund Palestinian artists and relief.

CURRENT SYSTEM STATE:
{json.dumps(audit, indent=2)}

REVENUE GAPS IDENTIFIED:
{json.dumps(gaps, indent=2)}

ENGINES ALREADY BUILT: {already_built_engines}
BUSINESS NICHES ALREADY BUILT: {already_built_niches}

YOUR JOB: Decide what to build next to maximize autonomous revenue.

Design:
1. Three NEW Python engine ideas (not already built above)
   - Each should close a revenue gap or create a new stream
   - Must be buildable by GitHub Actions, no human input needed
   - Must use: requests, smtplib, json, os, pathlib (no external services except Gmail, GitHub, Ko-fi, Gumroad, HuggingFace)

2. Three NEW business niches (not already built above)
   - Digital products that can be fully automated
   - $9-$97 price point
   - Mission-aligned: AI + autonomy + Gaza

3. One critical system fix
   - What's the single most important thing broken right now?

Respond ONLY with JSON:
{{
  "engine_ideas": [
    {{"name": "ENGINE_NAME", "purpose": "one sentence", "revenue_impact": "high/medium/low", "effort": "low/medium", "priority": 1}},
    {{"name": "ENGINE_NAME2", "purpose": "...", "revenue_impact": "...", "effort": "...", "priority": 2}},
    {{"name": "ENGINE_NAME3", "purpose": "...", "revenue_impact": "...", "effort": "...", "priority": 3}}
  ],
  "business_niches": [
    {{"niche": "Niche Name", "product_type": "digital_download", "price": 27, "platform": "Gumroad", "audience": "who buys this", "why_now": "why this niche works right now"}},
    {{"niche": "Niche Name2", "product_type": "ebook", "price": 17, "platform": "Gumroad", "audience": "...", "why_now": "..."}},
    {{"niche": "Niche Name3", "product_type": "template_pack", "price": 37, "platform": "Gumroad+Etsy", "audience": "...", "why_now": "..."}}
  ],
  "critical_fix": "what to fix and how",
  "next_priority": "what should the system focus on this cycle",
  "confidence": 0.85
}}"""

    result = ask_json(prompt, max_tokens=2000)
    return result or _fallback_plan(audit, gaps)


def _fallback_plan(audit, gaps):
    ideas = [
        {"name": "REDDIT_POSTER", "purpose": "Auto-post SolarPunk content to relevant subreddits", "revenue_impact": "high", "effort": "low", "priority": 1},
        {"name": "REVENUE_FORECASTER", "purpose": "Project monthly revenue from all streams, email weekly report", "revenue_impact": "medium", "effort": "low", "priority": 2},
        {"name": "REDBUBBLE_ENGINE", "purpose": "Generate and upload Gaza Rose art to Redbubble", "revenue_impact": "high", "effort": "medium", "priority": 3},
    ]
    niches = [
        {"niche": "AI Side Income Blueprint", "product_type": "ebook", "price": 27, "platform": "Gumroad", "audience": "people wanting passive income"},
        {"niche": "Palestine Solidarity Art Pack", "product_type": "digital_download", "price": 15, "platform": "Gumroad", "audience": "activists and artists"},
        {"niche": "GitHub Actions for Beginners", "product_type": "video_course_notes", "price": 37, "platform": "Gumroad", "audience": "developers"},
    ]
    return {"engine_ideas": ideas, "business_niches": niches,
            "critical_fix": gaps[0] if gaps else "Continue building",
            "next_priority": "Build more revenue streams", "confidence": 0.6}


def write_plan(plan, audit, gaps):
    """Write architect_plan.json that other engines consume."""
    full_plan = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system_audit": audit,
        "revenue_gaps": gaps,
        "engine_ideas": plan.get("engine_ideas", []),
        "business_niches": plan.get("business_niches", []),
        "critical_fix": plan.get("critical_fix", ""),
        "next_priority": plan.get("next_priority", ""),
        "confidence": plan.get("confidence", 0.5),
        # Priority queue for SELF_BUILDER
        "build_next_engine": plan.get("engine_ideas", [{}])[0].get("name", "") if plan.get("engine_ideas") else "",
        # Priority queue for BUSINESS_FACTORY
        "build_next_niche": plan.get("business_niches", [{}])[0] if plan.get("business_niches") else {},
    }
    (DATA / "architect_plan.json").write_text(json.dumps(full_plan, indent=2))
    return full_plan


def run():
    state = load()
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"ARCHITECT cycle {state['cycles']} | AI={'online' if AI_ONLINE else 'offline'}")

    audit = audit_system()
    gaps  = identify_revenue_gaps(audit)

    print(f"  Health: {audit['health']} | Exchange tasks: {audit['exchange_tasks']} | Earned: ${audit['exchange_earned']:.2f}")
    print(f"  Businesses: {audit['businesses_built']} | Engines built: {audit['engines_built']}")
    if gaps:
        print(f"  Gaps found: {len(gaps)}")
        for g in gaps[:3]:
            print(f"    - {g[:80]}")

    plan = generate_plan(audit, gaps)
    full_plan = write_plan(plan, audit, gaps)

    state["plans_written"] = state.get("plans_written", 0) + 1
    state["engine_ideas"]  = [e.get("name") for e in plan.get("engine_ideas", [])]
    state["niche_ideas"]   = [n.get("niche") for n in plan.get("business_niches", [])]
    state["revenue_gaps"]  = gaps
    state.setdefault("improvement_log", []).append({
        "ts":       datetime.now(timezone.utc).isoformat()[:16],
        "priority": full_plan.get("next_priority", ""),
        "fix":      full_plan.get("critical_fix", "")[:80],
        "engines":  state["engine_ideas"],
    })

    print(f"  Plan written | Next engine: {full_plan.get('build_next_engine','?')} | Next niche: {full_plan.get('build_next_niche',{}).get('niche','?')}")
    save(state)
    return full_plan


if __name__ == "__main__":
    run()
