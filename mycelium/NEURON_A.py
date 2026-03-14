# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
NEURON_A v3 - Builder Brain (HuggingFace free AI)
Scans system state, finds high-leverage passive income opportunities.
Writes: data/neuron_a_report.json
"""
import os, json, sys
from pathlib import Path
from datetime import datetime, timezone

# Import shared AI client
sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask_json
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

def gather_state():
    engines = sorted([f.name for f in Path("mycelium").glob("*.py")]) if Path("mycelium").exists() else []
    data_files = sorted([f.name for f in Path("data").glob("*.json")]) if Path("data").exists() else []
    flywheel, loop_mem, synth_log, brain = {}, [], {}, {}
    for fname in ["flywheel_state.json","loop_memory.json","synthesis_log.json","brain_state.json"]:
        fp = Path("data") / fname
        if fp.exists():
            try:
                obj = json.loads(fp.read_text())
                if fname=="flywheel_state.json": flywheel=obj
                elif fname=="loop_memory.json": loop_mem=obj if isinstance(obj,list) else []
                elif fname=="synthesis_log.json": synth_log=obj
                elif fname=="brain_state.json": brain=obj
            except: pass
    return {
        "engines": engines, "engine_count": len(engines), "data_files": data_files,
        "revenue": flywheel.get("current_balance", 0),
        "revenue_streams": flywheel.get("streams", {}),
        "loop_cycles": len(loop_mem),
        "last_insight": loop_mem[-1].get("key_insight","") if loop_mem else "",
        "synth_built": len(synth_log.get("built",[])),
        "brain_health": brain.get("health_score", 0),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def fallback_report():
    return {
        "opportunities": [
            {"name":"Gaza Rose Gallery Etsy SEO","type":"revenue","effort":"low","impact":"high",
             "action":"Generate 10 AI-optimized product descriptions with SEO keywords","estimated_value":"$50-200/month"},
            {"name":"GitHub Sponsors","type":"revenue","effort":"low","impact":"medium",
             "action":"Enable at github.com/sponsors/meekotharaccoon-cell","estimated_value":"$20-100/month"},
            {"name":"SolarPunk Newsletter on Substack","type":"growth","effort":"low","impact":"high",
             "action":"Write first issue: I built a self-running AI agent for free","estimated_value":"audience + future paid"},
            {"name":"Free API content pipeline","type":"system","effort":"low","impact":"medium",
             "action":"HackerNews + Reddit JSON -> daily automated content","estimated_value":"zero-cost content stream"},
            {"name":"Ko-fi promotion","type":"revenue","effort":"low","impact":"high",
             "action":"Share ko-fi.com/meekotharaccoon on social — first $5 triggers the loop","estimated_value":"$5-50/month"}
        ],
        "builder_thesis": "Ko-fi + GitHub Sponsors = first dollars at zero spend",
        "priority_build": "AFFILIATE_TRACKER.py - passive income while you sleep",
        "free_apis_untapped": ["Open-Meteo - free weather","HackerNews API - trending tech","Reddit JSON - community pulse"],
        "meeko_action_needed": "Enable GitHub Sponsors at github.com/sponsors/meekotharaccoon-cell"
    }

def call_ai(state):
    if not AI_AVAILABLE:
        return fallback_report()
    prompt = f"""You are NEURON_A, Builder Brain of SolarPunk (Meeko's autonomous passive income agent).
System: {state['engine_count']} engines ({', '.join(state['engines'][:15])})
Revenue: ${state['revenue']:.2f} | Cycles: {state['loop_cycles']} | Last insight: {state['last_insight']}
Find 5 highest-leverage opportunities RIGHT NOW for passive income. Think: what builds forever?
Respond ONLY JSON (no markdown):
{{"opportunities":[{{"name":"name","type":"revenue|growth|system","effort":"low|medium|high","impact":"low|medium|high","action":"specific next action","estimated_value":"what this generates"}}],
"builder_thesis":"one sentence strategic insight",
"priority_build":"FILENAME.py - what to build next and why",
"free_apis_untapped":["api - why useful"],
"meeko_action_needed":"one thing only Meeko can do or null"}}"""
    try:
        result = ask_json(prompt, max_tokens=1200)
        return result if result else fallback_report()
    except Exception as ex:
        print(f"NEURON_A AI error: {ex}")
        return {"opportunities":[], "builder_thesis": f"AI error: {ex}", "priority_build": ""}

def main():
    print("NEURON_A v3 - Builder Brain (HuggingFace free AI)")
    state = gather_state()
    print(f"State: {state['engine_count']} engines | ${state['revenue']:.2f} | {state['loop_cycles']} cycles")
    report = call_ai(state)
    report["system_state"] = state
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    Path("data").mkdir(exist_ok=True)
    Path("data/neuron_a_report.json").write_text(json.dumps(report, indent=2))
    print(f"Builder thesis: {report.get('builder_thesis','?')}")
    for opp in report.get("opportunities",[])[:3]:
        print(f"  [{opp.get('impact','?')}] {opp.get('name','')}: {opp.get('action','')}")
    print("NEURON_A done.")

if __name__ == "__main__": main()
