#!/usr/bin/env python3
"""
SYNAPSE.py -- SolarPunk Brain Coordinator (v2)
Runs last in OMNIBRAIN. Reads all engine outputs, computes real health score,
sends Meeko the daily report with actual metrics. No fake zeros.
"""
import os, json, requests, smtplib
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GMAIL   = os.environ.get("GMAIL_ADDRESS", "")
GPASS   = os.environ.get("GMAIL_APP_PASSWORD", "")
DATA    = Path("data")
MYC     = Path("mycelium")
DATA.mkdir(exist_ok=True)
RUN_ID  = datetime.now().strftime("%Y%m%d-%H%M")

UPGRADES = [
    (20,  "Claude Pro -- 5x context, priority API"),
    (25,  "Custom Domain -- professional presence"),
    (35,  "API Credits -- more synthesis cycles"),
    (50,  "Mailgun -- 10k emails/month"),
    (54,  "GitHub Pro -- unlimited Actions"),
    (200, "VPS -- always-on SolarPunk"),
    (500, "Dedicated Server -- full autonomy"),
]

def load(fname):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {}

def gather():
    engines   = list(MYC.glob("*.py")) if MYC.exists() else []
    data_files = list(DATA.glob("*.json"))
    flywheel  = load("flywheel_state.json")
    memory    = load("loop_memory.json") if (DATA / "loop_memory.json").exists() else []
    if isinstance(memory, list): cycles = len(memory)
    else: cycles = memory.get("count", 0)
    synth_log = load("synthesis_log.json")
    tier      = load("tier_state.json")
    guardian  = load("guardian_state.json")
    income    = load("income_hunt.json")
    prev      = load("brain_state.json")

    revenue   = flywheel.get("current_balance", 0)
    streams   = flywheel.get("streams", {})
    active_streams = [(k, v.get("balance", 0)) for k, v in streams.items() if v.get("balance", 0) > 0]

    next_up = None
    for thresh, desc in UPGRADES:
        if revenue < thresh:
            next_up = (thresh, desc, thresh - revenue)
            break

    return {
        "engines_total": len(engines),
        "engine_names": [e.name for e in engines],
        "data_files": len(data_files),
        "revenue": revenue,
        "active_streams": active_streams,
        "income_opportunities": income.get("opportunities_found", [])[:2],
        "next_upgrade": next_up,
        "loop_cycles": cycles,
        "auto_built": len(synth_log.get("built", [])),
        "tier": tier.get("current_tier", 0),
        "guardian": guardian.get("status", "unknown"),
        "prev_score": prev.get("health_score", 0),
        "a_report": load("neuron_a_report.json").get("summary", ""),
        "b_report": load("neuron_b_report.json").get("summary", ""),
        "top_income_action": income.get("action", "") or load("neuron_a_report.json").get("proposals", [""])[0] if load("neuron_a_report.json").get("proposals") else "",
    }

def score(s):
    if not API_KEY:
        pts = 20
        pts += min(40, s["engines_total"] * 3)
        pts += min(10, s["data_files"] * 1)
        pts += min(10, s["loop_cycles"])
        pts += min(10, s["tier"] * 2)
        if s["revenue"] > 0: pts += 5
        if s["guardian"] == "healthy": pts += 5
        return {"health_score": min(100, pts), "status": "Local compute (no API)", "top_action": s["top_income_action"] or "Activate Gaza Rose Gallery income stream", "risk": "No Anthropic API key"}

    prompt = f"""SYNAPSE health check for SolarPunk autonomous income system.

REAL STATS:
- Engines: {s['engines_total']} ({', '.join(s['engine_names'][:6])})
- Data files: {s['data_files']}
- Revenue: ${s['revenue']:.2f}
- Active income streams: {s['active_streams'] or 'none yet'}
- Loop cycles: {s['loop_cycles']}
- Auto-built engines: {s['auto_built']}
- Tier: {s['tier']}
- Guardian: {s['guardian']}
- Builder says: {s['a_report'][:200]}
- Skeptic says: {s['b_report'][:200]}

Score 0-100. {s['engines_total']} engines is NOT zero. Be honest.

JSON only (no fences): {{"health_score":<int>,"status":"one line","top_action":"exact next income action","risk":"biggest risk"}}"""

    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": API_KEY, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 400,
                  "messages": [{"role": "user", "content": prompt}]}, timeout=30)
        r.raise_for_status()
        t = r.json()["content"][0]["text"]
        s2, e = t.find("{"), t.rfind("}") + 1
        if s2 >= 0: return json.loads(t[s2:e])
    except Exception as ex:
        print(f"Score API err: {ex}")

    pts = 20 + min(40, s["engines_total"] * 3)
    return {"health_score": min(100, pts), "status": "API err -- local compute", "top_action": "", "risk": ""}

def send(s, h):
    if not GMAIL or not GPASS: return
    sc = h.get("health_score", 0)
    prev = s["prev_score"]
    trend = f"+{sc-prev}" if sc > prev else (f"{sc-prev}" if sc < prev else "=")
    nu = s["next_upgrade"]
    up_line = f"${nu[0]} -> {nu[1]} (need ${nu[2]:.0f} more)" if nu else "All upgrades funded!"

    streams_text = "\n".join(f"  {k}: ${v:.2f}" for k,v in s["active_streams"]) if s["active_streams"] else "  (none active yet)"
    opps = "\n".join(f"  -> {o.get('name','?')}: {o.get('monthly_potential','?')}/mo" for o in s["income_opportunities"]) if s["income_opportunities"] else "  (run INCOME_HUNTER for opportunities)"

    body = f"""SOLARPUNK -- {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
{'='*50}
HEALTH: {sc}/100 ({trend}) | TIER: {s['tier']} | GUARDIAN: {s['guardian'].upper()}
{h.get('status','')}

SYSTEM STATS
{'--'*25}
  Engines running:    {s['engines_total']}
  Data files:         {s['data_files']}
  Revenue balance:    ${s['revenue']:.2f}
  Loop cycles:        {s['loop_cycles']}
  Auto-built engines: {s['auto_built']}

INCOME STREAMS
{'--'*25}
{streams_text}

OPPORTUNITIES DETECTED
{'--'*25}
{opps}

UPGRADE PATH: {up_line}

TOP ACTION:   {h.get('top_action','')}
BIGGEST RISK: {h.get('risk','')}

The loop never stops. -- SolarPunk"""

    subject = f"SolarPunk [{sc}/100 {trend}] T{s['tier']} | {s['engines_total']} engines | ${s['revenue']:.2f} | {datetime.now().strftime('%m/%d %H:%M')}"
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject; msg["From"] = GMAIL; msg["To"] = GMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(GMAIL, GPASS); srv.send_message(msg)
        print(f"Email: {subject}")
    except Exception as e:
        print(f"Email err: {e}")

if __name__ == "__main__":
    print(f"SYNAPSE v2 -- {RUN_ID}")
    s = gather()
    print(f"Stats: {s['engines_total']} engines | ${s['revenue']:.2f} | Tier {s['tier']}")
    h = score(s)
    sc = h.get("health_score", 0)
    print(f"Health: {sc}/100")
    (DATA / "brain_state.json").write_text(json.dumps({
        "run_id": RUN_ID, "timestamp": datetime.now().isoformat(),
        "health_score": sc, "engines_total": s["engines_total"],
        "revenue": s["revenue"], "tier": s["tier"],
        "status": h.get("status",""), "top_action": h.get("top_action","")
    }, indent=2))
    send(s, h)
    print(f"SYNAPSE done -- {sc}/100")
