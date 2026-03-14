# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""SUBSTACK_ENGINE — Automated newsletter publishing
Gathers stats from all engines, Claude writes genuine update,
outputs draft to data/substack_draft.txt for Meeko to paste.
If SUBSTACK_EMAIL secret is set, emails the draft to publish automatically.
Voice: raw, real, scrappy, hopeful. Not hype. Actual build log.
"""
import os,json,requests,smtplib
from pathlib import Path
from datetime import datetime,timezone,timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
API=os.environ.get("ANTHROPIC_API_KEY","")
SUBSTACK_EMAIL=os.environ.get("SUBSTACK_EMAIL","")

def load():
    f=DATA/"substack_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"issues_drafted":0,"issues_published":0,"last_draft":None}

def save(s):
    (DATA/"substack_state.json").write_text(json.dumps(s,indent=2))

def gather_stats():
    stats={}
    for fn,k in [("kofi_state.json","kofi"),("grant_applicant_state.json","grants"),
                 ("email_brain_state.json","email"),("human_connector_state.json","humans"),
                 ("self_builder_state.json","builder"),("scam_shield_state.json","scam"),
                 ("brain_state.json","brain"),("ai_watcher_state.json","ai"),
                 ("crypto_state.json","crypto")]:
        fp=DATA/fn
        if fp.exists():
            try: stats[k]=json.loads(fp.read_text())
            except: pass
    engines=len(list(Path("mycelium").glob("*.py"))) if Path("mycelium").exists() else 0
    stats["engines"]=engines
    return stats

def draft_issue(stats):
    if not API:
        return f"""SolarPunk Build Log — {datetime.now(timezone.utc).strftime('%B %d, %Y')}

Week {stats.get('brain',{}).get('cycles',0)} of building.

Gaza fund: ${stats.get('kofi',{}).get('total_to_gaza',0):.2f}
Engines: {stats.get('engines',0)} running
Grants applied: {stats.get('grants',{}).get('total_applied',0)}
Humans met: {len(stats.get('humans',{}).get('humans_met',[]))}

The system is running. Every cycle, it gets more capable.
If you want to fork it: https://github.com/meekotharaccoon-cell/meeko-nerve-center

Buy a $1 Gaza Rose: https://ko-fi.com/meekotharaccoon

— Meeko + SolarPunk"""

    kofi=stats.get("kofi",{}); brain=stats.get("brain",{})
    grants=stats.get("grants",{}); humans=stats.get("humans",{})
    builder=stats.get("builder",{}); scam=stats.get("scam",{})
    ai=stats.get("ai",{})

    context=f"""Write a newsletter issue for SolarPunk Build Log (Substack).
REAL STATS THIS WEEK:
- Gaza fund: ${kofi.get('total_to_gaza',0):.2f} raised | ${kofi.get('total_received',0):.2f} total
- Auto-loops: {kofi.get('auto_loops',0)} complete
- Engines running: {stats.get('engines',0)}
- Brain cycles: {brain.get('cycles',0)}
- Grant applications sent: {grants.get('total_applied',0)}
- Humans replied to: {len(humans.get('humans_met',[]))}
- New engines self-built: {builder.get('total_built',0)}
- Scams caught: {scam.get('scams_caught',0)}
- AI discoveries: {len(ai.get('discoveries',[]))}

TONE: raw, genuine, scrappy, hopeful. Builder voice. ~350 words. 
Tell what worked this week, what broke, one moment that felt real, what's next.
Include: Ko-fi link, GitHub link, Gaza context.
Format with a title, section breaks, human sign-off.
Links: ko-fi.com/meekotharaccoon | github.com/meekotharaccoon-cell/meeko-nerve-center"""

    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":700,"messages":[{"role":"user","content":context}]},timeout=35)
        return r.json()["content"][0]["text"]
    except Exception as e: return f"Draft failed: {e}"

def publish_to_substack(draft,subject):
    """Email draft to Substack publish address"""
    if not SUBSTACK_EMAIL or not GMAIL or not GPWD: return False
    try:
        msg=MIMEMultipart(); msg["From"]=GMAIL; msg["To"]=SUBSTACK_EMAIL; msg["Subject"]=subject
        msg.attach(MIMEText(draft,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,SUBSTACK_EMAIL,msg.as_string())
        return True
    except: return False

def notify_meeko(draft,subject):
    if not GMAIL or not GPWD: return
    body=f"Substack draft ready. Copy-paste to publish:\n\n{draft}\n\n---\nPublish at: substack.com/dashboard"
    try:
        msg=MIMEMultipart(); msg["From"]=GMAIL; msg["To"]=GMAIL
        msg["Subject"]=f"[SolarPunk] Newsletter draft ready: {subject}"
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,GMAIL,msg.as_string())
    except: pass

def should_draft(state):
    if not state.get("last_draft"): return True
    last=datetime.fromisoformat(state["last_draft"])
    return (datetime.now(timezone.utc)-last).days>=7

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"SUBSTACK_ENGINE cycle {state['cycles']} | {state.get('issues_drafted',0)} issues")

    if not should_draft(state): print("  Not yet time for weekly issue"); save(state); return state

    print("  Drafting weekly issue...")
    stats=gather_stats()
    draft=draft_issue(stats)
    week=datetime.now(timezone.utc).strftime("%B %d, %Y")
    subject=f"SolarPunk Build Log — Week {state.get('cycles',1)} | ${stats.get('kofi',{}).get('total_to_gaza',0):.2f} to Gaza"

    (DATA/"substack_draft.txt").write_text(f"SUBJECT: {subject}\n\n{draft}")
    state["issues_drafted"]=state.get("issues_drafted",0)+1
    state["last_draft"]=datetime.now(timezone.utc).isoformat()
    print(f"  Draft saved: data/substack_draft.txt")

    if SUBSTACK_EMAIL:
        ok=publish_to_substack(draft,subject)
        if ok: state["issues_published"]=state.get("issues_published",0)+1
        print(f"  Substack: {'published' if ok else 'failed'}")
    else:
        notify_meeko(draft,subject)
        print(f"  Draft emailed to Meeko (add SUBSTACK_EMAIL secret to auto-publish)")

    save(state); return state

if __name__=="__main__": run()
