#!/usr/bin/env python3
"""
NEURON_A.py -- Builder Brain (v2)
Analyzes state, proposes income expansions, finds opportunities.
Focused on: what can SolarPunk actually BUILD and EARN right now?
"""
import os, json, requests
from pathlib import Path
from datetime import datetime

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DATA = Path("data")
MYC  = Path("mycelium")
DATA.mkdir(exist_ok=True)

def analyze():
    engines = [e.name for e in MYC.glob("*.py")] if MYC.exists() else []
    flywheel = {}
    ff = DATA / "flywheel_state.json"
    if ff.exists():
        try: flywheel = json.loads(ff.read_text())
        except: pass

    tier = 0
    tf = DATA / "tier_state.json"
    if tf.exists():
        try: tier = json.loads(tf.read_text()).get("current_tier", 0)
        except: pass

    desktop = {}
    df = DATA / "desktop_connection.json"
    if df.exists():
        try: desktop = json.loads(df.read_text())
        except: pass

    revenue    = flywheel.get("current_balance", 0)
    streams    = list(flywheel.get("streams", {}).keys())
    brave_live = desktop.get("brave_debug_live", False)
    desktop_up = desktop.get("loop_status") == "CONNECTED"

    if not API_KEY:
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": f"Builder: {len(engines)} engines, ${revenue:.2f} revenue. Priority: activate Gaza Rose Gallery automation via Brave.",
            "proposals": [
                "Automate Gaza Rose Gallery Instagram/Etsy posts using Brave CDP",
                "Build email subscriber landing page for humanitarian newsletter",
                "Create affiliate product links for art supply recommendations"
            ],
            "income_opportunities": [
                {"stream": "Gaza Rose Gallery", "method": "Brave CDP auto-post", "effort": "low", "potential": "$50-200/mo"},
                {"stream": "Affiliate Links", "method": "Art/tech product recommendations in content", "effort": "low", "potential": "$20-100/mo"},
                {"stream": "Newsletter", "method": "Weekly curated content + affiliate", "effort": "medium", "potential": "$50-300/mo"},
            ]
        }
    else:
        prompt = f"""You are NEURON_A, Builder Brain of SolarPunk autonomous income system.

STATE:
- Engines: {engines}
- Revenue: ${revenue:.2f}
- Streams: {streams or ['none']}
- Tier: {tier}
- Desktop: {'connected' if desktop_up else 'not connected'}
- Brave browser: {'LIVE' if brave_live else 'not available'}

MISSION: Find 3 highest-leverage income/capability moves RIGHT NOW.

Rules:
- Legal, ethical passive income only
- Automatable with Python + browser (no manual steps)
- Can realistically earn $10-500/month
- Fast time to first dollar (days not months)
- Be specific (exact platform, method, steps)

JSON only (no fences):
{{"summary":"one line","proposals":["action1","action2","action3"],"income_opportunities":[{{"stream":"name","method":"exact how","effort":"low/med/high","potential":"$X-Y/mo"}}]}}"""

        try:
            r = requests.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key": API_KEY, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 800,
                      "messages": [{"role": "user", "content": prompt}]}, timeout=30)
            r.raise_for_status()
            t = r.json()["content"][0]["text"]
            s, e = t.find("{"), t.rfind("}") + 1
            report = json.loads(t[s:e]) if s >= 0 else {}
            report["timestamp"] = datetime.now().isoformat()
        except Exception as ex:
            print(f"NEURON_A err: {ex}")
            report = {"timestamp": datetime.now().isoformat(), "summary": f"API err: {ex}",
                      "proposals": [], "income_opportunities": []}

    (DATA / "neuron_a_report.json").write_text(json.dumps(report, indent=2))
    print(f"NEURON_A: {report.get('summary','done')}")
    return report

if __name__ == "__main__":
    analyze()
