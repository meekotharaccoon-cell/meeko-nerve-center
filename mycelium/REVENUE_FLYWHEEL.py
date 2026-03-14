# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""REVENUE_FLYWHEEL — Master revenue coordinator
Sees ALL money streams simultaneously. Finds bottlenecks. Routes capital.
Runs the formula: business = revenue + client, as close to 100% autonomous as possible.

Every cycle it asks: what's the highest-leverage action right now?
Then does it. Or emails Meeko the exact 1-click step if it can't.
"""
import os,json,requests,smtplib
from pathlib import Path
from datetime import datetime,timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
API=os.environ.get("ANTHROPIC_API_KEY","")

# Revenue stream definitions with current potential
STREAMS={
    "kofi":{"name":"Ko-fi Sales","monthly_potential":50,"file":"kofi_state.json","key":"total_received"},
    "grants":{"name":"Grants","monthly_potential":2000,"file":"grant_applicant_state.json","key":"total_applied"},
    "sponsors":{"name":"GitHub Sponsors","monthly_potential":145,"file":"sponsors_state.json","key":"total_monthly"},
    "exchange":{"name":"Email Agent Exchange","monthly_potential":300,"file":"email_exchange_state.json","key":"total_earned"},
    "substack":{"name":"Substack","monthly_potential":175,"file":"substack_state.json","key":"issues_published"},
    "gumroad":{"name":"Gumroad","monthly_potential":50,"file":"gumroad_state.json","key":"total_revenue"},
}

def load():
    f=DATA/"flywheel_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"total_coordinated":0,"actions_taken":[],"weekly_report":None}

def save(s):
    (DATA/"flywheel_state.json").write_text(json.dumps(s,indent=2))

def read_all_streams():
    """Get current status of every revenue stream"""
    status={}
    for k,stream in STREAMS.items():
        fp=DATA/stream["file"]
        if fp.exists():
            try:
                d=json.loads(fp.read_text())
                status[k]={
                    "name":stream["name"],
                    "value":d.get(stream["key"],0),
                    "potential":stream["monthly_potential"],
                    "active":True,
                    "raw":d
                }
            except: status[k]={"name":stream["name"],"value":0,"potential":stream["monthly_potential"],"active":False}
        else: status[k]={"name":stream["name"],"value":0,"potential":stream["monthly_potential"],"active":False}
    return status

def identify_bottleneck(streams):
    """Find highest-leverage action"""
    inactive_high_value=[(k,s) for k,s in streams.items() if not s["active"] and s["potential"]>50]
    inactive_high_value.sort(key=lambda x:x[1]["potential"],reverse=True)
    if inactive_high_value: return "unlock",inactive_high_value[0]

    zero_value=[(k,s) for k,s in streams.items() if s["active"] and s["value"]==0]
    if zero_value: return "activate",zero_value[0]

    active=[(k,s) for k,s in streams.items() if s["active"] and s["value"]>0]
    if active:
        best=max(active,key=lambda x:x[1]["potential"]-x[1]["value"])
        return "scale",best

    return "maintain",None

def run_flywheel_analysis(streams,bottleneck_type,bottleneck):
    if not API: return None
    stream_summary="\n".join([f"  {s['name']}: ${s['value']:.2f} (potential ${s['potential']}/mo) [{'ACTIVE' if s['active'] else 'INACTIVE'}]" for s in streams.values()])
    bn_txt=f"{bottleneck_type}: {bottleneck[1]['name']}" if bottleneck else "all streams active"
    prompt=f"""SolarPunk revenue flywheel analysis. Formula: business = revenue + client.
STREAMS:
{stream_summary}
BOTTLENECK: {bn_txt}
CONTEXT: Autonomous system on GitHub Actions. Funds Palestinian artists. Operator: Meeko (solo creator).
What single action in the next cycle maximizes total revenue fastest?
ONLY JSON: {{"action":"specific thing to do","stream":"{bottleneck[0] if bottleneck else 'all'}","why":"1 sentence","autonomous":true/false,"meeko_step":"exact step if needs human or null","expected_impact":"$X in Y timeframe","priority":1-10}}"""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":300,"messages":[{"role":"user","content":prompt}]},timeout=25)
        t=r.json()["content"][0]["text"]; s,e=t.find("{"),t.rfind("}")+1
        return json.loads(t[s:e])
    except: return None

def take_autonomous_action(recommendation,state):
    """Actually do things that are 100% autonomous"""
    if not recommendation or not recommendation.get("autonomous"): return False
    action=recommendation.get("action","")
    stream=recommendation.get("stream","")
    # Signal other engines via shared state files
    if "grant" in stream.lower():
        # Trigger grant hunter to run an extra scan
        trigger=DATA/"grant_trigger.json"
        trigger.write_text(json.dumps({"triggered_by":"flywheel","reason":action,"ts":datetime.now(timezone.utc).isoformat()}))
        print(f"  Triggered GRANT_HUNTER extra scan")
        return True
    if "exchange" in stream.lower() or "agent" in stream.lower():
        # Post exchange to social
        social=DATA/"social_queue.json"
        posts=json.loads(social.read_text()) if social.exists() else []
        posts.append({"text":f"🤖 SolarPunk Email Agent Exchange is live. AI agents that work via email, pay per task. Research, grant writing, code review, copy — $0.05-$0.10/task. 15% funds Gaza artists. Send [TASK] to my email. #SolarPunk #AI #Gaza","ts":datetime.now(timezone.utc).isoformat(),"source":"flywheel"})
        social.write_text(json.dumps(posts[-20:],indent=2))
        print(f"  Queued exchange promotion to social")
        return True
    if "ko" in stream.lower() or "kofi" in stream.lower():
        social=DATA/"social_queue.json"
        posts=json.loads(social.read_text()) if social.exists() else []
        posts.append({"text":f"🌹 Gaza Rose Gallery — $1 AI art. 70¢ goes directly to Palestinian artists. 30¢ keeps the system running. 12 designs. ko-fi.com/meekotharaccoon #Gaza #Palestine #Art #SolarPunk","ts":datetime.now(timezone.utc).isoformat(),"source":"flywheel"})
        social.write_text(json.dumps(posts[-20:],indent=2))
        return True
    return False

def notify_meeko_action(recommendation):
    if not GMAIL or not GPWD or not recommendation: return
    if recommendation.get("autonomous"): return  # Already handled
    step=recommendation.get("meeko_step","")
    if not step: return
    body=(f"FLYWHEEL RECOMMENDATION — Highest leverage action right now:\n\n"
        f"ACTION: {recommendation.get('action','')}\n"
        f"STREAM: {recommendation.get('stream','')}\n"
        f"WHY: {recommendation.get('why','')}\n"
        f"EXPECTED: {recommendation.get('expected_impact','')}\n"
        f"PRIORITY: {recommendation.get('priority',0)}/10\n\n"
        f"YOUR STEP:\n  {step}\n\n"
        f"Once you do this, SolarPunk handles the rest automatically.\n"
        f"[SolarPunk REVENUE_FLYWHEEL — {datetime.now(timezone.utc).isoformat()[:16]}]")
    try:
        msg=MIMEMultipart(); msg["From"]=GMAIL; msg["To"]=GMAIL
        msg["Subject"]=f"[SolarPunk] 1 action → {recommendation.get('expected_impact','more revenue')}"
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,GMAIL,msg.as_string())
    except: pass

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    streams=read_all_streams()
    total_potential=sum(s["potential"] for s in streams.values())
    total_current=sum(s["value"] for s in streams.values() if isinstance(s["value"],(int,float)))
    print(f"REVENUE_FLYWHEEL | Current: ${total_current:.2f} | Potential: ${total_potential}/mo")
    for k,s in streams.items():
        print(f"  {s['name']:25} ${s['value']:8.2f} [{'✓' if s['active'] else '✗'}]")

    bt_type,bt=identify_bottleneck(streams)
    print(f"  Bottleneck: {bt_type} — {bt[1]['name'] if bt else 'none'}")
    rec=run_flywheel_analysis(streams,bt_type,bt)
    if rec:
        acted=take_autonomous_action(rec,state)
        if not acted: notify_meeko_action(rec)
        state.setdefault("actions_taken",[]).append({"ts":datetime.now(timezone.utc).isoformat(),"rec":rec,"acted":acted})
        state["total_coordinated"]=state.get("total_coordinated",0)+1
        print(f"  Action: {'autonomous' if acted else 'emailed Meeko'} | {rec.get('action','?')[:60]}")

    (DATA/"flywheel_summary.json").write_text(json.dumps({"ts":datetime.now(timezone.utc).isoformat(),
        "total_current":total_current,"total_potential":total_potential,"streams":streams,
        "recommendation":rec},indent=2))
    save(state); return state

if __name__=="__main__": run()
