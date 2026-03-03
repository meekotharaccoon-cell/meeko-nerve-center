#!/usr/bin/env python3
"""
NEURON_B — The Skeptic Brain
Role: CRITIC. Finds risks, bottlenecks, what's broken, what will fail next.
"""
import os, json, requests, time
from pathlib import Path
from datetime import datetime

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

REQUIRED_ENGINES = [
    "NEURON_A.py","NEURON_B.py","SYNAPSE.py","SYNTHESIS_FACTORY.py",
    "REVENUE_FLYWHEEL.py","GETSCREEN_BRIDGE.py","email_gateway.py",
    "revenue_router.py","social_poster.py","knowledge_dispatch.py"
]

def gather_state():
    myc = Path("mycelium")
    dat = Path("data")
    engines = sorted([f.name for f in myc.glob("*.py") if not f.name.startswith("__")]) if myc.exists() else []
    missing = [e for e in REQUIRED_ENGINES if e not in engines]
    data_files = {}
    if dat.exists():
        for f in dat.glob("*.json"):
            try: data_files[f.name] = json.loads(f.read_text())
            except: pass
    flywheel = data_files.get("flywheel_state.json", {})
    stale = []
    if dat.exists():
        for f in dat.glob("*.json"):
            age_h = (time.time() - f.stat().st_mtime) / 3600
            if age_h > 25:
                stale.append(f"{f.name} ({age_h:.0f}h old)")
    workflows = sorted([f.name for f in Path(".github/workflows").glob("*.yml")]) if Path(".github/workflows").exists() else []
    return {
        "engines": engines, "missing_required": missing,
        "revenue_balance": flywheel.get("current_balance", 0.0),
        "stale_files": stale[:5],
        "workflow_count": len(workflows), "workflows": workflows,
    }

def think(state):
    risks = []
    if state["missing_required"]: risks.append(f"Missing engines: {state['missing_required']}")
    if state["revenue_balance"] == 0: risks.append("Zero revenue — no income stream activated")
    if state["stale_files"]: risks.append(f"Stale data: {state['stale_files']}")
    if not API_KEY:
        return {"perspective":"SKEPTIC","risks":risks or ["Structurally sound"],
                "biggest_single_risk":risks[0] if risks else "Revenue is $0","health_contribution":40}
    prompt = f"""You are NEURON_B — the SKEPTIC brain of SolarPunk, Meeko's autonomous AI agent.
CRITIC. Find what's broken. Find what blocks revenue. Be honest.

SYSTEM STATE: {json.dumps(state, indent=2)}
PRE-CALCULATED RISKS: {risks}

Respond ONLY with JSON (no markdown):
{{
  "perspective": "SKEPTIC",
  "risks": ["top 3 real risks"],
  "biggest_single_risk": "the one thing most likely to kill progress",
  "what_will_break_next": "honest prediction",
  "revenue_blocker": "specific reason revenue is still $0",
  "missing_engines_impact": "what we cant do without missing engines",
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
        print(f"NEURON_B error: {ex}")
        return {"perspective":"SKEPTIC","biggest_single_risk":"API unavailable","health_contribution":25}

def main():
    print("🧠 NEURON_B (Skeptic) activating...")
    state = gather_state()
    print(f"   Missing: {state['missing_required']}")
    print(f"   Revenue: ${state['revenue_balance']:.2f} | Workflows: {state['workflow_count']}")
    report = think(state)
    report["generated_at"] = datetime.now().isoformat()
    report["system_snapshot"] = state
    Path("data").mkdir(exist_ok=True)
    Path("data/neuron_b_report.json").write_text(json.dumps(report, indent=2))
    print(f"   Biggest risk: {report.get('biggest_single_risk','')}")
    print(f"   Health contribution: {report.get('health_contribution',0)}/100")

if __name__ == "__main__":
    main()
