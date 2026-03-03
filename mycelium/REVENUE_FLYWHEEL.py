#!/usr/bin/env python3
"""
REVENUE_FLYWHEEL — Tracks all income streams, advises on next upgrade.
$20 Investment Advisor powered by Claude API.
"""
import os, json, requests, smtplib
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GMAIL   = os.environ.get("GMAIL_ADDRESS", "")
GPASS   = os.environ.get("GMAIL_APP_PASSWORD", "")

UPGRADE_TIERS = [
    {"cost": 20,  "name": "Claude Pro",          "benefit": "5x more API capacity for SolarPunk"},
    {"cost": 25,  "name": "Custom domain",        "benefit": "Professional brand, trust signals"},
    {"cost": 35,  "name": "Anthropic API credits","benefit": "SolarPunk thinks faster and more"},
    {"cost": 50,  "name": "Mailgun",              "benefit": "Bulk email for knowledge dispatch"},
    {"cost": 54,  "name": "GitHub Pro",           "benefit": "Private repos, more Actions minutes"},
    {"cost": 200, "name": "VPS server",           "benefit": "24/7 always-on SolarPunk server"},
    {"cost": 500, "name": "Dedicated server",     "benefit": "Full autonomy, no limits"},
]

DEFAULT_STREAMS = [
    {"name": "Gaza Rose Gallery",    "platform": "manual",   "status": "active",  "monthly_est": 0.0},
    {"name": "Gumroad products",     "platform": "gumroad",  "status": "pending", "monthly_est": 0.0},
    {"name": "Medium Partner",       "platform": "medium",   "status": "pending", "monthly_est": 0.0},
    {"name": "Substack newsletter",  "platform": "substack", "status": "pending", "monthly_est": 0.0},
    {"name": "Affiliate posts",      "platform": "blog",     "status": "pending", "monthly_est": 0.0},
    {"name": "WhatsApp automation",  "platform": "manual",   "status": "pending", "monthly_est": 0.0},
    {"name": "RapidAPI listings",    "platform": "rapidapi", "status": "pending", "monthly_est": 0.0},
    {"name": "Prompt packs",         "platform": "gumroad",  "status": "pending", "monthly_est": 0.0},
]

def load_state():
    sf = Path("data/flywheel_state.json")
    if sf.exists():
        try: return json.loads(sf.read_text())
        except: pass
    return {"current_balance": 0.0, "streams": DEFAULT_STREAMS, "transactions": []}

def save_state(state):
    Path("data").mkdir(exist_ok=True)
    state["last_updated"] = datetime.now().isoformat()
    Path("data/flywheel_state.json").write_text(json.dumps(state, indent=2))

def next_upgrade(balance):
    for t in UPGRADE_TIERS:
        if balance < t["cost"]: return t
    return UPGRADE_TIERS[-1]

def investment_advice(state):
    if not API_KEY:
        t = next_upgrade(state["current_balance"])
        return f"Save toward {t['name']} (${t['cost']}) — {t['benefit']}"
    balance = state["current_balance"]
    streams = state["streams"]
    engines = sorted([f.name for f in Path("mycelium").glob("*.py") if not f.name.startswith("__")])
    prompt = f"""You are a $20 Investment Advisor for SolarPunk — Meeko's autonomous income system.

STATE: Balance=${balance:.2f} | Engines={len(engines)} | Active streams={[s['name'] for s in streams if s['status']=='active']}

UPGRADE OPTIONS:
{json.dumps(UPGRADE_TIERS, indent=2)}

Where should $20 go RIGHT NOW to unlock the most passive income fastest?
Respond in 2-3 sentences. Be specific. Start with the upgrade name."""
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API_KEY,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":300,"messages":[{"role":"user","content":prompt}]},timeout=30)
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    except Exception as ex:
        t = next_upgrade(balance)
        return f"[API err] {t['name']} (${t['cost']}) — {t['benefit']}"

def check_thresholds(state, advice):
    balance = state["current_balance"]
    t = next_upgrade(balance)
    pct = (balance / t["cost"]) * 100 if t["cost"] > 0 else 100
    if 98 <= pct or (50 <= pct < 52):
        if not GMAIL or not GPASS: return
        milestone = "🎉 THRESHOLD REACHED — UPGRADE NOW" if pct >= 98 else f"50% to {t['name']}"
        body = f"💰 REVENUE FLYWHEEL\n\n{milestone}\nBalance: ${balance:.2f} / ${t['cost']}\n\n$20 ADVICE:\n{advice}\n\nStreams:\n"
        for s in state["streams"]:
            body += f"  {'✅' if s['status']=='active' else '⏳'} {s['name']}: ${s['monthly_est']:.2f}/mo\n"
        try:
            msg = MIMEText(body)
            msg["Subject"] = f"💰 SolarPunk Revenue — {milestone[:40]}"
            msg["From"] = GMAIL; msg["To"] = GMAIL
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(GMAIL, GPASS); s.send_message(msg)
            print(f"Revenue alert sent: {milestone}")
        except Exception as ex:
            print(f"Email error: {ex}")

def main():
    print("💰 REVENUE_FLYWHEEL activating...")
    state  = load_state()
    advice = investment_advice(state)
    balance = state["current_balance"]
    t = next_upgrade(balance)
    pct = (balance / t["cost"]) * 100 if t["cost"] > 0 else 0
    print(f"   Balance: ${balance:.2f} | Next: {t['name']} (${t['cost']}) [{pct:.0f}%]")
    print(f"   Advice: {advice[:100]}")
    state["investment_advice"] = advice
    state["next_upgrade"] = t
    state["progress_pct"] = round(pct, 1)
    save_state(state)
    check_thresholds(state, advice)

if __name__ == "__main__":
    main()
