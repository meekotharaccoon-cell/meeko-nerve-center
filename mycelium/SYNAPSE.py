#!/usr/bin/env python3
"""
SYNAPSE — The Resolver + Brain State + Daily Email
Reads NEURON_A + NEURON_B, synthesizes with REAL stats, sends email to Meeko.
Health score is grounded in reality — never hallucinated 0.
"""
import os, json, requests, smtplib
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GMAIL   = os.environ.get("GMAIL_ADDRESS", "")
GPASS   = os.environ.get("GMAIL_APP_PASSWORD", "")
RUN_ID  = os.environ.get("GITHUB_RUN_ID", datetime.now().strftime("%Y%m%d%H%M"))

def gather_real_stats():
    myc = Path("mycelium")
    dat = Path("data")
    engines = sorted([f.name for f in myc.glob("*.py") if not f.name.startswith("__")]) if myc.exists() else []
    workflows = sorted([f.name for f in Path(".github/workflows").glob("*.yml")]) if Path(".github/workflows").exists() else []
    data_files = {}
    if dat.exists():
        for f in dat.glob("*.json"):
            try: data_files[f.name] = json.loads(f.read_text())
            except: pass
    flywheel   = data_files.get("flywheel_state.json", {})
    loop_mem   = data_files.get("loop_memory.json", [])
    registry   = data_files.get("build_registry.json", [])
    prev_brain = data_files.get("brain_state.json", {})
    REQUIRED   = ["NEURON_A.py","NEURON_B.py","SYNAPSE.py","SYNTHESIS_FACTORY.py",
                  "REVENUE_FLYWHEEL.py","email_gateway.py","social_poster.py"]
    return {
        "engines_total": len(engines), "engines": engines,
        "workflows": workflows, "workflow_count": len(workflows),
        "missing_engines": [e for e in REQUIRED if e not in engines],
        "data_files_count": len(data_files),
        "revenue_balance": flywheel.get("current_balance", 0.0),
        "revenue_streams": flywheel.get("streams", []),
        "loop_cycles": len(loop_mem) if isinstance(loop_mem, list) else 0,
        "engines_auto_built": len(registry) if isinstance(registry, list) else 0,
        "prev_health_score": prev_brain.get("health_score", 0),
    }

def calc_base_score(stats):
    score = 0
    score += min(stats["engines_total"] * 3, 30)   # up to 30 for engines
    score += min(stats["workflow_count"] * 5, 20)   # up to 20 for workflows
    score += 10 if stats["revenue_balance"] > 0 else 0
    score += min(stats["loop_cycles"] * 2, 20)      # up to 20 for loops
    score += max(0, 20 - len(stats["missing_engines"]) * 4)  # penalty for missing
    return max(5, min(int(score), 95))

def synthesize(stats, report_a, report_b):
    base = calc_base_score(stats)
    if not API_KEY:
        return {"health_score": base, "verdict": "BUILD",
                "synthesis": f"SolarPunk has {stats['engines_total']} engines and {stats['workflow_count']} workflows running.",
                "top_priority": report_a.get("highest_priority","Activate first revenue stream"),
                "key_risk": report_b.get("biggest_single_risk","Zero revenue"),
                "what_to_do_today": "Trigger BUILD_YOURSELF with turbo=true"}
    prompt = f"""You are SYNAPSE — resolver of SolarPunk's dual-brain architecture.

REAL SYSTEM STATS (FACTS — use these to score honestly):
{json.dumps(stats, indent=2)}

NEURON_A (Builder) said:
{json.dumps(report_a, indent=2)}

NEURON_B (Skeptic) said:
{json.dumps(report_b, indent=2)}

Calculated base health score from REAL stats: {base}/100
A system with {stats['engines_total']} engines and {stats['workflow_count']} workflows is NOT a zero.

Respond ONLY with JSON (no markdown):
{{
  "health_score": {base},
  "synthesis": "2-3 sentence honest summary",
  "verdict": "BUILD|FIX|WAIT",
  "top_priority": "single most important action",
  "key_risk": "single biggest risk",
  "what_to_do_today": "concrete action",
  "passive_income_ETA": "realistic estimate of first $1"
}}"""
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API_KEY,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":1000,"messages":[{"role":"user","content":prompt}]},timeout=60)
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        s,e = text.find("{"), text.rfind("}")+1
        result = json.loads(text[s:e]) if s>=0 else {}
        # Floor — Claude cannot hallucinate below base score
        if result.get("health_score",0) < base - 10:
            result["health_score"] = base
        return result
    except Exception as ex:
        print(f"SYNAPSE error: {ex}")
        return {"health_score": base, "verdict": "BUILD", "synthesis": "Running on base score."}

def send_email(stats, brain):
    if not GMAIL or not GPASS: return
    score = brain.get("health_score", 0)
    prev  = stats.get("prev_health_score", 0)
    delta = score - prev
    trend = f"▲{delta}" if delta > 0 else (f"▼{abs(delta)}" if delta < 0 else "→0")
    subject = f"🌱 SolarPunk [{score}/100 {trend}] — {stats['engines_total']} engines | ${stats['revenue_balance']:.2f} | {datetime.now().strftime('%m/%d %H:%M')} UTC"
    body = f"""🌱 SOLARPUNK BRAIN REPORT
{'='*50}

REAL SYSTEM STATS
{'─'*40}
Engines in mycelium/:    {stats['engines_total']}
Workflows active:         {stats['workflow_count']}
Data files produced:      {stats['data_files_count']}
Revenue balance:          ${stats['revenue_balance']:.2f}
Loop cycles:              {stats['loop_cycles']}
Engines auto-built:       {stats['engines_auto_built']}
Missing engines:          {', '.join(stats['missing_engines']) or 'None'}

HEALTH SCORE: {score}/100  (was {prev}, {trend})
VERDICT: {brain.get('verdict','?')}

SYNTHESIS:
{brain.get('synthesis','')}

TOP PRIORITY:
  {brain.get('top_priority','')}

KEY RISK:
  {brain.get('key_risk','')}

TODAY:
  {brain.get('what_to_do_today','')}

PASSIVE INCOME ETA: {brain.get('passive_income_ETA','Unknown')}

ENGINES:
  {', '.join(stats['engines'])}

WORKFLOWS:
  {', '.join(stats['workflows'])}

Run BUILD_YOURSELF to add more engines:
→ github.com/meekotharaccoon-cell/meeko-nerve-center/actions

— SolarPunk 🌱  |  Run: {RUN_ID}"""
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = GMAIL
        msg["To"] = GMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL, GPASS)
            s.send_message(msg)
        print(f"Email sent: {subject[:60]}...")
    except Exception as ex:
        print(f"Email error: {ex}")

def main():
    print("⚡ SYNAPSE activating...")
    stats = gather_real_stats()
    print(f"   {stats['engines_total']} engines | {stats['workflow_count']} workflows | ${stats['revenue_balance']:.2f}")
    report_a, report_b = {}, {}
    af = Path("data/neuron_a_report.json")
    bf = Path("data/neuron_b_report.json")
    if af.exists(): report_a = json.loads(af.read_text())
    if bf.exists(): report_b = json.loads(bf.read_text())
    brain = synthesize(stats, report_a, report_b)
    brain["run_id"] = RUN_ID
    brain["generated_at"] = datetime.now().isoformat()
    brain["stats"] = stats
    Path("data").mkdir(exist_ok=True)
    Path("data/brain_state.json").write_text(json.dumps(brain, indent=2))
    print(f"   Health: {brain.get('health_score',0)}/100 | Verdict: {brain.get('verdict','?')}")
    send_email(stats, brain)

if __name__ == "__main__":
    main()
