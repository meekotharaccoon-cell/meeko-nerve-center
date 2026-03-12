#!/usr/bin/env python3
"""
LOOP_BRAIN.py — SolarPunk self-improvement coordinator
=======================================================
Runs at L6 BEFORE SELF_BUILDER and KNOWLEDGE_WEAVER.

THE LOOP THIS CLOSES:
  SELF_BUILDER builds engine X
  → engine X runs next cycle
  → LOOP_BRAIN reads: did X succeed or fail? what data did it produce?
  → LOOP_BRAIN uses AI to plan: what should be built NEXT and why
  → writes loop_brain.json with build priorities
  → SELF_BUILDER reads loop_brain.json → builds the right thing
  → KNOWLEDGE_WEAVER reads loop_brain.json → avoids duplicates
  → cycle repeats. forever.

Without LOOP_BRAIN: builders work in isolation, may duplicate each other,
have no feedback on whether past builds worked.

With LOOP_BRAIN: the system learns from itself and coordinates.
"""
import os, sys, json
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data");     DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
STATE    = DATA / "loop_brain.json"

sys.path.insert(0, str(MYCELIUM))
try:
    from AI_CLIENT import ask_json, ai_available
    AI_OK = True
except ImportError:
    AI_OK = False


def rj(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text())
            if isinstance(d, (dict, list)):
                return d
        except: pass
    return fb if fb is not None else {}


def load_state():
    try:
        return json.loads(STATE.read_text())
    except:
        return {"cycles": 0, "build_history": [], "last_run": None}


def get_engine_outcomes():
    """Check which auto-built engines succeeded or failed in recent cycles."""
    omnibus = rj("omnibus_last.json")
    ok      = set(omnibus.get("engines_ok", []))
    failed  = set(omnibus.get("engines_failed", []))

    # Which engines were auto-built?
    sb_state = rj("self_builder_state.json")
    kw_state = rj("knowledge_weaver_state.json")

    built_by_sb = {b["name"] for b in sb_state.get("built", []) if isinstance(b, dict)}
    built_by_kw = set(kw_state.get("engines_built", []))
    all_built   = built_by_sb | built_by_kw

    outcomes = {}
    for name in all_built:
        if name in ok:
            outcomes[name] = "ok"
        elif name in failed:
            outcomes[name] = "failed"
        else:
            outcomes[name] = "not_run_yet"

    return outcomes, all_built


def get_system_snapshot():
    """Compact summary of current system state for AI planning."""
    omnibus    = rj("omnibus_last.json")
    bottleneck = rj("bottleneck_report.json")
    brain      = rj("brain_state.json")
    weaver     = rj("knowledge_weaver_state.json")
    builder    = rj("self_builder_state.json")
    architect  = rj("architect_plan.json")

    return {
        "health":          brain.get("health_score", 40),
        "cycle":           omnibus.get("cycle_number", 0),
        "engines_ok":      len(omnibus.get("engines_ok", [])),
        "engines_failed":  omnibus.get("engines_failed", []),
        "revenue":         omnibus.get("total_revenue", 0),
        "bottlenecks":     bottleneck.get("top_bottlenecks", [])[:3],
        "kw_built":        weaver.get("engines_built", []),
        "sb_built_total":  builder.get("total_built", 0),
        "architect_focus": architect.get("focus", ""),
        "existing_engines": sorted(f.stem for f in MYCELIUM.glob("*.py")
                                   if f.stem == f.stem.upper()),
    }


def plan_with_ai(outcomes, snap, state):
    """Use Groq (free) to decide what to build next and coordinate builders."""
    already_built = list(snap["kw_built"]) + [
        b["name"] for b in rj("self_builder_state.json").get("built", [])
        if isinstance(b, dict)
    ]

    failed_built = [name for name, status in outcomes.items() if status == "failed"]
    working_built = [name for name, status in outcomes.items() if status == "ok"]

    prompt = f"""You are LOOP_BRAIN, the self-improvement coordinator for SolarPunk — an autonomous AI income system.

SYSTEM STATE:
- Health: {snap['health']}/100 (cycle {snap['cycle']})
- Revenue: ${snap['revenue']:.2f}
- Engines running OK: {snap['engines_ok']}
- Engines FAILING: {snap['engines_failed'][:10]}
- Top bottlenecks: {snap['bottlenecks']}

AUTO-BUILT ENGINES THAT WORKED: {working_built}
AUTO-BUILT ENGINES THAT FAILED: {failed_built}
ALL EXISTING ENGINES: {snap['existing_engines'][:40]}
ALREADY BUILT BY AI: {already_built[:20]}

Your job: coordinate SELF_BUILDER and KNOWLEDGE_WEAVER to maximize system growth.

Respond with JSON:
{{
  "next_build_priority": [
    {{"name": "ENGINE_NAME", "purpose": "what it does", "why_now": "specific reason from state above"}},
    {{"name": "ENGINE_NAME_2", "purpose": "what it does", "why_now": "specific reason"}}
  ],
  "avoid_building": ["list of names that would duplicate existing work"],
  "fix_first": ["names of failed auto-built engines that should be retried or replaced"],
  "loop_insight": "one sentence: what is the system's biggest bottleneck right now",
  "focus": "revenue|growth|stability|connection"
}}"""

    result = ask_json(prompt, max_tokens=600)
    return result


def update_architect_plan(priorities, snap):
    """Write priority ideas into architect_plan.json format so SELF_BUILDER reads them."""
    existing = rj("architect_plan.json")
    if not isinstance(existing, dict):
        existing = {}

    ideas = []
    for p in priorities:
        ideas.append({
            "name":    p.get("name", ""),
            "purpose": p.get("purpose", ""),
            "why_now": p.get("why_now", ""),
            "source":  "LOOP_BRAIN",
            "ts":      datetime.now(timezone.utc).isoformat(),
        })

    existing["engine_ideas"] = ideas + existing.get("engine_ideas", [])[: 10]
    existing["loop_brain_ts"] = datetime.now(timezone.utc).isoformat()
    existing["focus"] = snap.get("health", 40)

    (DATA / "architect_plan.json").write_text(json.dumps(existing, indent=2))


def run():
    print("LOOP_BRAIN — closing the self-improvement loop...")
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1

    outcomes, all_built = get_engine_outcomes()
    snap = get_system_snapshot()

    print(f"  Cycle {state['cycles']} | Health {snap['health']}/100 | "
          f"Revenue ${snap['revenue']:.2f}")
    print(f"  Auto-built engines: {len(all_built)} total | "
          f"Outcomes: {dict(list(outcomes.items())[:5])}")

    plan = None
    if AI_OK and ai_available():
        try:
            plan = plan_with_ai(outcomes, snap, state)
            print(f"  AI plan: focus={plan.get('focus','?')} | "
                  f"insight={plan.get('loop_insight','')[:80]}")
        except Exception as e:
            print(f"  AI planning error: {e}")

    if plan and plan.get("next_build_priority"):
        update_architect_plan(plan["next_build_priority"], snap)
        print(f"  Wrote {len(plan['next_build_priority'])} priorities to architect_plan.json")

    # Save coordination state
    state["last_run"]       = datetime.now(timezone.utc).isoformat()
    state["last_outcomes"]  = outcomes
    state["last_plan"]      = plan
    state["last_snap_health"] = snap["health"]
    state.setdefault("build_history", []).append({
        "ts":          datetime.now(timezone.utc).isoformat(),
        "cycle":       snap["cycle"],
        "health":      snap["health"],
        "built_total": len(all_built),
        "failed":      [n for n, s in outcomes.items() if s == "failed"],
        "focus":       plan.get("focus") if plan else "no_ai",
        "insight":     plan.get("loop_insight", "") if plan else "",
    })
    state["build_history"] = state["build_history"][-50:]

    STATE.write_text(json.dumps(state, indent=2))
    print("LOOP_BRAIN done — builders will use updated priorities")


if __name__ == "__main__":
    run()
