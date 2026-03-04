#!/usr/bin/env python3
"""
NEURON_B v2 - Skeptic Brain
Stress-tests NEURON_A proposals. Finds failure modes. Adds safeguard awareness.
Writes: data/neuron_b_report.json
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def main():
    print("NEURON_B v2 - Skeptic Brain starting...")
    a_report = {}
    ap = Path("data/neuron_a_report.json")
    if ap.exists():
        try: a_report = json.loads(ap.read_text())
        except: pass
    if not a_report:
        a_report = {"opportunities":[],"builder_thesis":"No NEURON_A data","priority_build":""}

    if not ANTHROPIC_API_KEY:
        report = {
            "vetted_opportunities": a_report.get("opportunities",[]),
            "killed_ideas": [],
            "risks": [
                "SYNTHESIS_FACTORY must never git merge - caused last repo wipe (all workflows deleted)",
                "GUARDIAN workflow needed on every push to catch catastrophic changes",
                "Revenue $0 - Gaza Rose Gallery SEO is highest immediate priority",
                "No external monitoring - system only watches itself after the fact"
            ],
            "refined_priority": a_report.get("priority_build","ETSY_SEO_ENGINE.py"),
            "skeptic_thesis": "Infrastructure only matters when generating income - revenue actions first, automation second",
            "safeguards_needed": [
                "SYNTHESIS_FACTORY: hard-block .github/ writes and git merge in code scanner",
                "GUARDIAN.yml: trigger on every push, email Meeko on any catastrophic change within minutes",
                "Checkpoint: save known-good state (commit SHA + file list) after each healthy run"
            ]
        }
    else:
        prompt = f"""You are NEURON_B, Skeptic Brain of SolarPunk. Stress-test these ideas with brutal honesty.
NEURON_A proposed: {json.dumps(a_report.get('opportunities',[]), indent=2)}
Builder thesis: {a_report.get('builder_thesis','')}
Known system risks: SYNTHESIS_FACTORY wiped all workflows via git merge. Revenue $0. No push-triggered monitoring.
Kill bad ideas. Refine good ones. Add missing risks.
Respond ONLY JSON (no markdown):
{{"vetted_opportunities":[only ideas surviving scrutiny, same format],
"killed_ideas":["idea - why it won't work"],
"risks":["risk - mitigation"],
"refined_priority":"what to ACTUALLY build first after scrutiny",
"skeptic_thesis":"what the builder missed in one sentence",
"safeguards_needed":["specific safeguard to prevent another wipe or failure"]}}"""
        try:
            r = requests.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key":ANTHROPIC_API_KEY,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
                json={"model":"claude-sonnet-4-20250514","max_tokens":1200,"messages":[{"role":"user","content":prompt}]},
                timeout=60)
            r.raise_for_status()
            text = r.json()["content"][0]["text"]
            s,e = text.find("{"),text.rfind("}")+1
            report = json.loads(text[s:e]) if s>=0 else {"vetted_opportunities":a_report.get("opportunities",[]),"risks":[]}
        except Exception as ex:
            print(f"NEURON_B error: {ex}")
            report = {"risks":[str(ex)],"vetted_opportunities":a_report.get("opportunities",[]),"refined_priority":a_report.get("priority_build","")}

    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    Path("data").mkdir(exist_ok=True)
    Path("data/neuron_b_report.json").write_text(json.dumps(report, indent=2))
    print(f"Skeptic thesis: {report.get('skeptic_thesis','?')}")
    print(f"Refined priority: {report.get('refined_priority','?')}")
    for risk in report.get("risks",[])[:3]: print(f"  RISK: {risk}")
    print("NEURON_B done.")

if __name__ == "__main__": main()
