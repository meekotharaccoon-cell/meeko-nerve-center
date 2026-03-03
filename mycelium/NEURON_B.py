#!/usr/bin/env python3
"""
NEURON_B.py -- Skeptic Brain (v2)
Reviews NEURON_A's proposals for risk, legality, feasibility.
Filters out anything shady. Approves what's genuinely safe.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DATA = Path("data")
DATA.mkdir(exist_ok=True)

RED_FLAGS = [
    "spam", "unsolicited email", "scraped email list", "pyramid",
    "MLM", "get rich quick", "guaranteed returns", "impersonat",
    "mislead", "fake review", "astroturfing", "violate ToS",
    "copyright infring", "DMCA", "without consent"
]

def review():
    a_rep = {}
    af = DATA / "neuron_a_report.json"
    if af.exists():
        try: a_rep = json.loads(af.read_text())
        except: pass

    proposals    = a_rep.get("proposals", [])
    opportunities = a_rep.get("income_opportunities", [])

    # Quick local filter before API
    auto_flagged = []
    for prop in proposals:
        for flag in RED_FLAGS:
            if flag.lower() in prop.lower():
                auto_flagged.append(f"{prop} (flagged: {flag})")
                break

    if not API_KEY:
        approved = [p for p in proposals if p not in [f.split(" (")[0] for f in auto_flagged]]
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": f"Skeptic: {len(approved)}/{len(proposals)} proposals approved. {len(auto_flagged)} auto-flagged.",
            "approved": approved,
            "rejected": auto_flagged,
            "risk_notes": [
                "All automated content must be original or properly licensed",
                "Only email people who opted in (no cold spam)",
                "Check each platform's ToS before automating",
                "GDPR: don't store EU personal data without consent"
            ],
            "confidence": 75
        }
    else:
        prompt = f"""You are NEURON_B, Skeptic Brain of SolarPunk.

NEURON_A proposed:
{json.dumps(proposals, indent=2)}

Income opportunities:
{json.dumps(opportunities, indent=2)}

Your job: FILTER ruthlessly. Approve what's genuinely safe and legal. Reject anything risky.

AUTO-FLAGGED (already rejected): {auto_flagged}

Reject if:
- Requires spamming or unsolicited contact
- Violates platform ToS
- Could harm SolarPunk's reputation
- Is misleading or deceptive in any way
- Involves copyright infringement
- Requires scraping without permission

Approve if:
- 100% legal in US
- Ethical (you'd be proud to show Meeko)
- Platform ToS compliant
- Genuinely helps people or creates real value

JSON only (no fences):
{{"summary":"one line","approved":["approved action"],"rejected":["rejected + exact reason"],"risk_notes":["important caution"],"confidence":<0-100>}}"""

        try:
            r = requests.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key": API_KEY, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 700,
                      "messages": [{"role": "user", "content": prompt}]}, timeout=30)
            r.raise_for_status()
            t = r.json()["content"][0]["text"]
            s, e = t.find("{"), t.rfind("}") + 1
            report = json.loads(t[s:e]) if s >= 0 else {}
            report["timestamp"] = datetime.now().isoformat()
        except Exception as ex:
            print(f"NEURON_B err: {ex}")
            report = {"timestamp": datetime.now().isoformat(), "summary": f"API err: {ex}",
                      "approved": proposals, "rejected": auto_flagged, "risk_notes": [], "confidence": 50}

    (DATA / "neuron_b_report.json").write_text(json.dumps(report, indent=2))
    print(f"NEURON_B: {report.get('summary','done')} | Confidence: {report.get('confidence','?')}")
    return report

if __name__ == "__main__":
    review()
