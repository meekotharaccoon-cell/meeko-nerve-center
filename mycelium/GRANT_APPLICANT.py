# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""GRANT_APPLICANT - Fills and submits grant applications autonomously
Email grants -> Claude drafts + sends application
Form grants -> emails Meeko exact pre-filled steps
Tracks all applications, follows up on email chains automatically
"""
import os,json,smtplib,requests,re
from pathlib import Path
from datetime import datetime,timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
API=os.environ.get("ANTHROPIC_API_KEY","")

PROFILE={
    "project":"SolarPunk / Gaza Rose Gallery",
    "creator":"Meeko (MeekoThaRaccoon)",
    "desc":"Open-source autonomous AI system generating income for Palestinian artists. $1 art sales: 70c to Gaza Rose artists, 30c funds the next loop. Built on GitHub Actions, zero infrastructure cost.",
    "mission":"Fund Palestinian artists through automated AI art generation and sales.",
    "impact":"Directly funds Palestinian artists displaced by conflict. Every sale is autonomous and immediate.",
    "github":"https://github.com/meekotharaccoon-cell/meeko-nerve-center",
    "website":"https://meekotharaccoon-cell.github.io/meeko-nerve-center",
    "tech":"Python, GitHub Actions, Claude API, Hugging Face FLUX.1, Ko-fi, Gumroad",
    "budget":"$500-$5000 for artist fund expansion and infrastructure",
    "email":os.environ.get("GMAIL_ADDRESS","meekotharaccoon@gmail.com"),
}

def load():
    f=DATA/"grant_applicant_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"applied":[],"total_applied":0,"email_chains":[]}

def save(s):
    (DATA/"grant_applicant_state.json").write_text(json.dumps(s,indent=2))

def draft_email_app(grant):
    if not API: return None
    prompt=f"""Write a complete grant application email for SolarPunk.
GRANT: {grant['name']} | NOTES: {grant.get('notes','')} | REQS: {grant.get('key_requirements',[])}
PITCH: {grant.get('pitch','')}
PROJECT: {PROFILE['desc']}
MISSION: {PROFILE['mission']} | IMPACT: {PROFILE['impact']}
GITHUB: {PROFILE['github']} | BUDGET: {PROFILE['budget']}
Be honest: independent creator, not nonprofit. 300-400 words. Compelling and genuine.
ONLY JSON (no markdown): {{"subject":"subject line","body":"full email body","to_address":"{grant.get('application_email','grants@example.com')}","ready_to_send":true}}"""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":900,"messages":[{"role":"user","content":prompt}]},timeout=40)
        t=r.json()["content"][0]["text"]; s,e=t.find("{"),t.rfind("}")+1
        return json.loads(t[s:e])
    except Exception as ex: return {"error":str(ex)}

def draft_grant_reply(thread_subject,thread_body,grant_name):
    """Auto-reply to grant email chains - keep the conversation going"""
    if not API: return None
    prompt=f"""You are SolarPunk replying to a grant email chain for {grant_name}.
ORIGINAL EMAIL: {thread_body[:800]}
PROJECT: {PROFILE['desc']} | GITHUB: {PROFILE['github']}
Reply warmly and answer any questions about SolarPunk. Provide any requested info.
ONLY JSON: {{"subject":"Re: {thread_subject}","body":"reply text","send":true}}"""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":600,"messages":[{"role":"user","content":prompt}]},timeout=30)
        t=r.json()["content"][0]["text"]; s,e=t.find("{"),t.rfind("}")+1
        return json.loads(t[s:e])
    except: return None

def send_email(to,subject,body):
    if not GMAIL or not GPWD: return False
    try:
        msg=MIMEMultipart(); msg["From"]=GMAIL; msg["To"]=to
        msg["Subject"]=subject; msg["Reply-To"]=GMAIL
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,to,msg.as_string())
        return True
    except Exception as e: print(f"  send: {e}"); return False

def notify_meeko(grant,reason):
    if not GMAIL or not GPWD: return
    subj=f"GRANT ACTION NEEDED: {grant['name']}"
    body=(f"SolarPunk found a grant but needs you to complete it:\n\n"
        f"GRANT: {grant['name']}\n"
        f"POTENTIAL: {grant.get('amount_range','unknown')}\n"
        f"DEADLINE: {grant.get('deadline','check website')}\n"
        f"APPLY AT: {grant.get('application_url') or grant.get('url','')}\n\n"
        f"WHY I NEED YOU: {reason}\n\n"
        f"COPY-PASTE INFO:\n"
        f"  Project: {PROFILE['project']}\n"
        f"  Description: {PROFILE['desc']}\n"
        f"  GitHub: {PROFILE['github']}\n"
        f"  Website: {PROFILE['website']}\n"
        f"  Budget: {PROFILE['budget']}\n"
        f"  Tech: {PROFILE['tech']}\n\n"
        f"Requirements: {grant.get('key_requirements',[])}\n"
        f"Pitch: {grant.get('pitch','')}\n\n"
        f"[SolarPunk GRANT_APPLICANT - I handled everything I could autonomously]")
    send_email(GMAIL,subj,body)
    print(f"  Meeko notified: {grant['name']}")

def check_grant_replies():
    """Check revenue_inbox / email_drafts for replies to our grant applications"""
    inbox=DATA/"revenue_inbox.json"
    if not inbox.exists(): return []
    try: emails=json.loads(inbox.read_text())
    except: return []
    grant_replies=[]
    grant_orgs=["mozilla","opentech","knight","shuttleworth","ford","nlnet","prototype",
                "gitcoin","awesome","afac","palfest","rhizome","techforgood","experiment",
                "opencollective","wikimedia","creative commons","sundance","artforjustice"]
    for em in emails:
        sender=em.get("from","").lower()
        if any(org in sender for org in grant_orgs):
            grant_replies.append(em)
    return grant_replies

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"GRANT_APPLICANT cycle {state['cycles']} | {state.get('total_applied',0)} applied")

    # Check for grant reply emails and continue chains
    replies=check_grant_replies()
    for reply in replies[:3]:
        print(f"  GRANT REPLY from {reply.get('from','?')[:40]}")
        draft=draft_grant_reply(reply.get("subject",""),reply.get("body",""),reply.get("from",""))
        if draft and draft.get("send"):
            m=re.search(r'<(.+?)>',reply.get("from","")); to=m.group(1) if m else reply.get("from","")
            if "@" in to:
                ok=send_email(to,draft["subject"],draft["body"])
                print(f"  {'Replied' if ok else 'Reply failed'} to grant chain: {to}")
                state.setdefault("email_chains",[]).append({"ts":datetime.now(timezone.utc).isoformat(),"to":to,"subj":draft["subject"],"sent":ok})

    # Process new grant applications
    gf=DATA/"grants_found.json"
    if not gf.exists(): print("  No grants_found - run GRANT_HUNTER first"); save(state); return state
    grants=json.loads(gf.read_text())
    applied_names={a["name"] for a in state.get("applied",[])}
    candidates=[g for g in grants if g.get("priority") in ["high","medium"] and g["name"] not in applied_names]
    print(f"  {len(candidates)} new candidates")

    for grant in candidates[:3]:
        name=grant["name"]; typ=grant.get("application_type","unknown")
        print(f"  -> {name} [{typ}]")
        record={"name":name,"type":typ,"ts":datetime.now(timezone.utc).isoformat(),"status":"attempted"}

        if typ=="email" and grant.get("application_email"):
            draft=draft_email_app(grant)
            if draft and draft.get("ready_to_send") and draft.get("body"):
                ok=send_email(draft["to_address"],draft["subject"],draft["body"])
                record["status"]="sent" if ok else "draft_failed"
                print(f"  {'Sent' if ok else 'FAILED'}: {draft.get('to_address','?')}")
            else:
                notify_meeko(grant,"Could not draft email - check grants_found.json")
                record["status"]="meeko_notified"
        else:
            notify_meeko(grant,f"Type '{typ}' requires browser - URL ready for you above")
            record["status"]="meeko_notified"

        state.setdefault("applied",[]).append(record)
        state["total_applied"]=state.get("total_applied",0)+1

    save(state); return state

if __name__=="__main__": run()
