# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
SYNAPSE v2 - Resolver
Reads NEURON_A+B outputs. Synthesizes final decisions. Sends OMNIBRAIN email.
FIX: Gathers real stats directly from repo - never depends on empty A/B reports.
"""
import os, json, requests, smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY","")
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS","")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD","")
RUN_ID             = os.environ.get("GITHUB_RUN_ID", f"local-{int(datetime.now().timestamp())}")

UPGRADE_TIERS = [
    (20,"Claude Pro"),(25,"Domain name"),(35,"API credits"),
    (50,"Mailgun"),(54,"GitHub Pro"),(200,"VPS hosting"),(500,"Dedicated server")
]

def gather_real_stats():
    """Ground truth directly from repo files - never trust empty A/B reports."""
    engines_total = len(list(Path("mycelium").glob("*.py"))) if Path("mycelium").exists() else 0
    data_files    = len(list(Path("data").glob("*.json"))) if Path("data").exists() else 0
    flywheel,loop_mem,synth_log,prev = {},{},{},{}
    for fname in ["flywheel_state.json","loop_memory.json","synthesis_log.json","brain_state.json"]:
        fp = Path("data")/fname
        if fp.exists():
            try:
                obj = json.loads(fp.read_text())
                if fname=="flywheel_state.json": flywheel=obj
                elif fname=="loop_memory.json": loop_mem=obj if isinstance(obj,list) else {}
                elif fname=="synthesis_log.json": synth_log=obj
                elif fname=="brain_state.json": prev=obj
            except: pass
    revenue = flywheel.get("current_balance",0)
    nu = next((t for t in UPGRADE_TIERS if t[0]>revenue), UPGRADE_TIERS[-1])
    cycles = len(loop_mem) if isinstance(loop_mem,list) else 0
    return {"engines_total":engines_total,"data_files":data_files,"revenue":revenue,
            "cycles":cycles,"synth_built":len(synth_log.get("built",[])),
            "prev_score":prev.get("health_score",0),"next_upgrade":nu[0],"next_upgrade_name":nu[1]}

def call_claude(stats, a_report, b_report):
    if not ANTHROPIC_API_KEY:
        score = min(100, max(20, 20 + stats["engines_total"]*2 + stats["cycles"]))
        return {
            "health_score": score,
            "top_actions": [o.get("action","") for o in a_report.get("opportunities",[])[:3]],
            "synthesis": f"{stats['engines_total']} engines running, {stats['cycles']} autonomous cycles done. No API key - running on pure logic. First priority: add ANTHROPIC_API_KEY to GitHub Secrets to unlock full AI synthesis.",
            "next_run_priority": b_report.get("refined_priority","Add ANTHROPIC_API_KEY to GitHub Secrets"),
            "passive_income_progress": "Gaza Rose Gallery tracking active. GitHub Sponsors setup pending. Newsletter idea queued.",
            "meeko_headline": f"{stats['engines_total']} engines autonomous"
        }
    prompt = f"""You are SYNAPSE, resolver brain of SolarPunk. Synthesize everything into one clear decision.
REAL STATS (ground truth): {stats['engines_total']} engines | {stats['data_files']} data files | ${stats['revenue']:.2f} revenue | {stats['cycles']} loop cycles | {stats['synth_built']} factory-built engines | prev score {stats['prev_score']}/100
NEURON_A thesis: {a_report.get('builder_thesis','n/a')}
NEURON_B thesis: {b_report.get('skeptic_thesis','n/a')}
Vetted opportunities: {json.dumps(b_report.get('vetted_opportunities',[])[:3],indent=2)}
{stats['engines_total']} engines + {stats['data_files']} data files + {stats['cycles']} cycles = REAL functioning system. Score honestly.
0=dead, 30=just started, 50=functional, 75=thriving, 100=self-sustaining passive income machine.
Respond ONLY JSON (no markdown):
{{"health_score":<int 0-100>,"top_actions":["a1","a2","a3"],"synthesis":"one paragraph - what is actually happening and what to do","next_run_priority":"single most important thing","passive_income_progress":"honest assessment","meeko_headline":"punchy subject line phrase"}}"""
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":ANTHROPIC_API_KEY,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":800,"messages":[{"role":"user","content":prompt}]},
            timeout=60)
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        s,e = text.find("{"),text.rfind("}")+1
        return json.loads(text[s:e]) if s>=0 else {}
    except Exception as ex:
        return {"health_score":40,"synthesis":str(ex),"top_actions":[]}

def build_email(stats, synthesis, a_report, b_report):
    score = synthesis.get("health_score",0)
    prev  = stats["prev_score"]
    trend = f"+{score-prev}" if score>prev else (f"{score-prev}" if score<prev else "=")
    now   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    subject = f"SolarPunk [{score}/100 {trend}] - {stats['engines_total']} engines | ${stats['revenue']:.2f} | {now[:10]}"
    body = f"""SOLARPUNK OMNIBRAIN REPORT
{now}
{'='*50}

REAL SYSTEM STATS
{'-'*40}
  Engines in mycelium/    {stats['engines_total']:>6}
  Data files produced     {stats['data_files']:>6}
  Revenue balance         ${stats['revenue']:>8.2f}
  Next upgrade            ${stats['next_upgrade']} -> {stats['next_upgrade_name']}
  Loop cycles completed   {stats['cycles']:>6}
  Engines auto-built      {stats['synth_built']:>6}
  Health score            {score:>5}/100  ({trend})

SYNTHESIS
{'-'*40}
{synthesis.get('synthesis','No synthesis available.')}

PASSIVE INCOME PROGRESS
{'-'*40}
{synthesis.get('passive_income_progress','Building foundations.')}

TOP ACTIONS
{'-'*40}"""
    for i,a in enumerate(synthesis.get("top_actions",[])[:5],1): body+=f"\n  {i}. {a}"
    body+=f"""

NEURON_A: {a_report.get('builder_thesis','-')}
NEURON_B: {b_report.get('skeptic_thesis','-')}

NEXT RUN PRIORITY
{'-'*40}
  {synthesis.get('next_run_priority','-')}

RUN: {RUN_ID}
{'='*50}
The loop never stops. - SolarPunk"""
    return subject, body

def send_email(subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f"No email creds - would send: {subject}")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"]=subject; msg["From"]=GMAIL_ADDRESS; msg["To"]=GMAIL_ADDRESS
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(GMAIL_ADDRESS,GMAIL_APP_PASSWORD); s.send_message(msg)
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Email error: {e}")

def main():
    print("SYNAPSE v2 - Resolver starting...")
    stats = gather_real_stats()
    print(f"Stats: {stats['engines_total']} engines | ${stats['revenue']:.2f} | {stats['cycles']} cycles")
    a_report,b_report = {},{}
    for fname,target in [("neuron_a_report.json","a"),("neuron_b_report.json","b")]:
        fp = Path("data")/fname
        if fp.exists():
            try:
                obj=json.loads(fp.read_text())
                if target=="a": a_report=obj
                else: b_report=obj
            except: pass
    synthesis = call_claude(stats,a_report,b_report)
    score = synthesis.get("health_score",0)
    print(f"Health score: {score}/100")
    subject,body = build_email(stats,synthesis,a_report,b_report)
    send_email(subject,body)
    Path("data").mkdir(exist_ok=True)
    Path("data/brain_state.json").write_text(json.dumps({
        "run_id":RUN_ID,"health_score":score,"stats":stats,
        "synthesis":synthesis,"generated_at":datetime.now(timezone.utc).isoformat()
    },indent=2))
    print(f"Brain state saved. Score: {score}/100")

if __name__ == "__main__": main()
