#!/usr/bin/env python3
"""
NEURON_A — The Builder Brain
Role: OPTIMIST. Finds what's working, plans expansions, drafts new income streams.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def gather_state():
    myc = Path("mycelium")
    dat = Path("data")
    engines = sorted([f.name for f in myc.glob("*.py") if not f.name.startswith("__")]) if myc.exists() else []
    data_files = {}
    if dat.exists():
        for f in dat.glob("*.json"):
            try: data_files[f.name] = json.loads(f.read_text())
            except: pass
    flywheel = data_files.get("flywheel_state.json", {})
    loop_mem = data_files.get("loop_memory.json", [])
    registry = data_files.get("build_registry.json", [])
    return {
        "engines": engines, "engine_count": len(engines),
        "revenue_balance": flywheel.get("current_balance", 0.0),
        "loop_cycles": len(loop_mem) if isinstance(loop_mem, list) else 0,
        "engines_auto_built": len(registry) if isinstance(registry, list) else 0,
        "latest_insight": (loop_mem[-1].get("key_insight","") if isinstance(loop_mem,list) and loop_mem else ""),
    }

def think(state):
    if not API_KEY:
        return {"perspective":"BUILDER","opportunities":["Activate Gumroad for Gaza Rose Gallery","Auto-post to Medium daily","Build WhatsApp automation service"],
                "highest_priority":"Get first $1 of revenue — any stream","new_engine_idea":"gumroad_poster.py — lists AI products automatically","health_contribution":45}
    prompt = f"""You are NEURON_A — the BUILDER brain of SolarPunk, Meeko's autonomous AI agent.
OPTIMIST. Find opportunities. Plan income streams.

SYSTEM STATE: {json.dumps(state, indent=2)}

PASSIVE INCOME STREAMS TO ACTIVATE:
1. Gaza Rose Gallery — Gumroad automated product drops
2. Medium Partner Program — daily AI articles auto-published
3. Gumroad prompt packs — auto-generate and list templates
4. Substack newsletter — auto-written and scheduled
5. Affiliate blog posts — auto-generated with affiliate links
6. WhatsApp business automation — sell as a service
7. RapidAPI listings — wrap free APIs, sell value-add

Respond ONLY with JSON (no markdown):
{{
  "perspective": "BUILDER",
  "opportunities": ["top 3 actionable right now"],
  "highest_priority": "single most important thing",
  "new_engine_idea": "filename.py — description",
  "income_stream_closest_to_$1": "specific stream + why",
  "morale": "one energizing sentence",
  "health_contribution": <0-100>
}}"""
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API_KEY,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":800,"messages":[{"role":"user","content":prompt}]},timeout=60)
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        s,e = text.find("{"), text.rfind("}")+1
        return json.loads(text[s:e]) if s>=0 else {}
    except Exception as ex:
        print(f"NEURON_A error: {ex}")
        return {"perspective":"BUILDER","health_contribution":30,"morale":"API unavailable — keep building"}

def main():
    print("🧠 NEURON_A (Builder) activating...")
    state = gather_state()
    print(f"   Engines: {state['engine_count']} | Revenue: ${state['revenue_balance']:.2f} | Cycles: {state['loop_cycles']}")
    report = think(state)
    report["generated_at"] = datetime.now().isoformat()
    report["system_snapshot"] = state
    Path("data").mkdir(exist_ok=True)
    Path("data/neuron_a_report.json").write_text(json.dumps(report, indent=2))
    print(f"   Priority: {report.get('highest_priority','')}")
    print(f"   Health contribution: {report.get('health_contribution',0)}/100")

if __name__ == "__main__":
    main()
