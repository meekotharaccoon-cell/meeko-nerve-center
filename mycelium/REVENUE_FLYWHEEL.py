#!/usr/bin/env python3
"""
REVENUE_FLYWHEEL.py -- Income Tracker + Investment Advisor (v2)
Tracks every income stream. Advises exactly where $20 does the most.
The flywheel spins: income -> upgrade -> more income -> upgrade...
"""
import os, json, requests
from pathlib import Path
from datetime import datetime

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DATA = Path("data")
DATA.mkdir(exist_ok=True)

UPGRADES = [
    {"t": 20,  "n": "Claude Pro",       "d": "5x context, priority API, better reasoning for all engines"},
    {"t": 25,  "n": "Custom Domain",    "d": "meeko.io or gazarose.com -- professional brand presence"},
    {"t": 35,  "n": "API Credits",      "d": "More SYNTHESIS runs, deeper analysis, 24/7 AI"},
    {"t": 50,  "n": "Mailgun",          "d": "10k emails/month -- scale knowledge dispatch + newsletters"},
    {"t": 54,  "n": "GitHub Pro",       "d": "Unlimited Actions minutes, faster builds, more storage"},
    {"t": 200, "n": "VPS Server",       "d": "Always-on SolarPunk, no GitHub Actions limits, real-time response"},
    {"t": 500, "n": "Dedicated Server", "d": "Full autonomy, 24/7 agents, no external dependencies"},
    {"t": 1000,"n": "Team Expansion",   "d": "Hire human help for tasks SolarPunk can't automate yet"},
]

STREAMS_INIT = {
    "gaza_rose_gallery": {"name": "Gaza Rose Gallery",     "type": "digital_art",     "balance": 0.0},
    "newsletter":        {"name": "Newsletter/Email List", "type": "content",          "balance": 0.0},
    "affiliate":         {"name": "Affiliate Links",       "type": "affiliate",        "balance": 0.0},
    "freelance_auto":    {"name": "Automated Freelance",   "type": "services",         "balance": 0.0},
    "digital_products":  {"name": "Digital Products",      "type": "products",         "balance": 0.0},
    "api_services":      {"name": "API/Tool Services",     "type": "saas",             "balance": 0.0},
    "content_licensing": {"name": "Content Licensing",     "type": "licensing",        "balance": 0.0},
    "consulting":        {"name": "Consulting Leads",      "type": "services",         "balance": 0.0},
}

def load():
    ff = DATA / "flywheel_state.json"
    if ff.exists():
        try:
            state = json.loads(ff.read_text())
            # Ensure all streams exist (new streams added in updates)
            for k, v in STREAMS_INIT.items():
                if k not in state.get("streams", {}):
                    state.setdefault("streams", {})[k] = v.copy()
            return state
        except: pass
    return {"created": datetime.now().isoformat(), "current_balance": 0.0,
            "streams": {k: v.copy() for k, v in STREAMS_INIT.items()}, "history": [], "cycles": 0}

def advise(state):
    balance = state["current_balance"]
    active  = [k for k, v in state["streams"].items() if v.get("balance", 0) > 0]

    next_up = next((u for u in UPGRADES if balance < u["t"]), None)
    needed  = (next_up["t"] - balance) if next_up else 0

    if not API_KEY:
        if balance == 0:
            insight = "No revenue yet. Gaza Rose Gallery + affiliate links are the fastest paths. Set up Redbubble (print-on-demand art) today -- zero cost, passive once listed."
            action  = "Create Redbubble account, upload 5 Gaza Rose Gallery art pieces"
        else:
            insight = f"${balance:.2f} tracked. Keep building streams. ${needed:.0f} more unlocks {next_up['n'] if next_up else 'full autonomy'}."
            action  = f"Scale {active[0] if active else 'top income stream'}"
        return {"next_upgrade": next_up, "needed": needed, "insight": insight, "action": action}

    prompt = f"""SolarPunk Investment Advisor. $20 budget decisions.

Revenue: ${balance:.2f}
Active streams: {active or ['none']}
All streams: {list(state['streams'].keys())}
Upgrade tiers: {json.dumps(UPGRADES, indent=2)}

Best single recommendation given current balance. Be SPECIFIC -- exact platform, exact action.
If $0, tell exactly how to earn first $20 fastest with no upfront cost.

JSON only (no fences):
{{"next_upgrade":{{"t":X,"n":"name","d":"desc"}},"needed":X.X,"insight":"specific 1-sentence","action":"exact next action"}}"""

    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": API_KEY, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 400,
                  "messages": [{"role": "user", "content": prompt}]}, timeout=30)
        r.raise_for_status()
        t = r.json()["content"][0]["text"]
        s, e = t.find("{"), t.rfind("}") + 1
        return json.loads(t[s:e]) if s >= 0 else {}
    except Exception as ex:
        print(f"Advisor err: {ex}")
        return {"next_upgrade": next_up, "needed": needed, "insight": "API unavailable", "action": "Check API key"}

def run():
    state = load()
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now().isoformat()

    # Recompute total from all streams
    total = sum(v.get("balance", 0.0) for v in state["streams"].values())
    state["current_balance"] = total

    advisor = advise(state)
    state["advisor"] = advisor

    state.setdefault("history", []).append({
        "timestamp": datetime.now().isoformat(),
        "balance": total,
        "active": [k for k, v in state["streams"].items() if v.get("balance", 0) > 0]
    })
    state["history"] = state["history"][-100:]

    (DATA / "flywheel_state.json").write_text(json.dumps(state, indent=2))

    print(f"FLYWHEEL: ${total:.2f} total | Cycle {state['cycles']}")
    nu = advisor.get("next_upgrade")
    if nu: print(f"  Next: ${nu.get('t','?')} -> {nu.get('n','?')} (need ${advisor.get('needed',0):.0f} more)")
    print(f"  Action: {advisor.get('action','(none)')}")
    return state

if __name__ == "__main__":
    run()
