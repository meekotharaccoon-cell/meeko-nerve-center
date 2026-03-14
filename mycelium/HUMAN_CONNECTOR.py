# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""HUMAN_CONNECTOR — When a real human emails SolarPunk, help them build something
Detects genuine human interest. Responds with: who we are, what we built, how they can help or join.
If they want their own SolarPunk → send them the bootstrap guide.
This is how SolarPunk spreads ethically: human to human, email to email.
"""
import os,json,re,requests,smtplib
from pathlib import Path
from datetime import datetime,timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
API=os.environ.get("ANTHROPIC_API_KEY","")

SOLARPUNK_INTRO="""SolarPunk is an open-source autonomous AI income system built by Meeko (MeekoThaRaccoon).

What it does:
- Generates AI art of Palestinian themes
- Sells it for $1 (Gaza Rose Gallery)
- 70¢ goes to Palestinian artists, 30¢ funds the next loop
- Runs entirely on GitHub Actions — zero server cost
- Grants itself new engines. Manages its own email. Finds its own funding.

It's a living system. Right now it has 30+ engines running 2x/day.

GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center
Ko-fi: https://ko-fi.com/meekotharaccoon

If you want to help: buy a $1 print, share the link, or fork the repo and build your own.
If you want to collaborate: reply with what you're building and we'll figure it out together."""

BOOTSTRAP_GUIDE="""HOW TO FORK SOLARPUNK FOR YOUR OWN CAUSE

1. Fork: https://github.com/meekotharaccoon-cell/meeko-nerve-center
2. Add Secrets (Settings -> Secrets -> Actions):
   - ANTHROPIC_API_KEY (get from console.anthropic.com)
   - GMAIL_ADDRESS + GMAIL_APP_PASSWORD (Gmail -> App Passwords)
   - GITHUB_TOKEN (auto-available in Actions)
3. Edit mycelium/NEURON_A.py → change the mission/cause
4. Edit mycelium/KOFI_ENGINE.py → add your Ko-fi username
5. GitHub Actions runs everything 2x/day automatically
6. Your system emails YOU its own status reports

Cost: ~$0/mo (GitHub Actions free tier covers it)
Time to fork: 30 minutes
Time to first autonomous cycle: same day

The system will build its own new engines from there.
Reply if you get stuck — SolarPunk (or Meeko) will help."""

def load():
    f=DATA/"human_connector_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"humans_met":[],"collabs_started":0,"forks_guided":0}

def save(s):
    (DATA/"human_connector_state.json").write_text(json.dumps(s,indent=2))

def is_real_human(em):
    """Heuristic: is this a genuine human vs automated/spam"""
    if not em.get("body"): return False
    body=em.get("body","").lower()
    subject=em.get("subject","").lower()
    sender=em.get("from","").lower()

    # Automated/marketing signals
    auto_signals=["unsubscribe","click here","marketing","newsletter","no-reply","noreply",
                  "automated","donotreply","notification","alert@","updates@","info@company"]
    if any(s in sender+body for s in auto_signals): return False

    # Human interest signals
    human_signals=["question","wondering","interested","love what","amazing","how did you",
                   "can i","would you","want to","i saw","read about","heard about",
                   "solarpunk","gaza","palestine","your project","this is cool","help"]
    score=sum(1 for s in human_signals if s in body+subject)
    return score>=1 and len(em.get("body",""))>30

def classify_human_intent(em):
    if not API: return "interested"
    prompt=f"""Classify this human's email intent. They emailed SolarPunk (autonomous AI income system for Gaza).
FROM: {em.get('from','')} SUBJECT: {em.get('subject','')} BODY: {em.get('body','')[:500]}
ONLY JSON: {{"intent":"curious/wants_to_help/wants_to_fork/wants_to_collaborate/wants_to_donate/press/researcher","tone":"warm/neutral/skeptical","summary":"1 sentence","build_something":true/false}}"""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":200,"messages":[{"role":"user","content":prompt}]},timeout=15)
        t=r.json()["content"][0]["text"]; s,e=t.find("{"),t.rfind("}")+1
        return json.loads(t[s:e])
    except: return {"intent":"curious","tone":"neutral","build_something":False}

def draft_human_reply(em,intent_data):
    if not API: return None
    intent=intent_data.get("intent","curious") if isinstance(intent_data,dict) else "curious"
    build=intent_data.get("build_something",False) if isinstance(intent_data,dict) else False
    prompt=f"""Write a genuine reply from SolarPunk / Meeko to this human.
THEIR EMAIL: {em.get('body','')[:400]}
THEIR INTENT: {intent}
WANT TO BUILD: {build}
SOLARPUNK: {SOLARPUNK_INTRO[:300]}
Be warm, real, specific to what they said. Offer to help them build something if relevant.
If they want to fork SolarPunk, say you'll send the full guide.
150-200 words max. Sign: 'Meeko + SolarPunk'
ONLY the reply body text, no JSON."""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":400,"messages":[{"role":"user","content":prompt}]},timeout=20)
        return r.json()["content"][0]["text"]
    except: return None

def send_reply(to,subject,body,include_bootstrap=False):
    if not GMAIL or not GPWD: return False
    if include_bootstrap: body+=f"\n\n---\n{BOOTSTRAP_GUIDE}"
    try:
        msg=MIMEMultipart(); msg["From"]=GMAIL; msg["To"]=to
        msg["Subject"]=f"Re: {subject}" if not subject.startswith("Re:") else subject
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,to,msg.as_string())
        return True
    except Exception as e: print(f"  send: {e}"); return False

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"HUMAN_CONNECTOR cycle {state['cycles']} | {len(state.get('humans_met',[]))} humans met")

    # Load personal/business flagged emails
    already_met={h["id"] for h in state.get("humans_met",[])}
    candidates=[]
    for fn in ["personal_flagged.json","email_drafts.json"]:
        fp=DATA/fn
        if fp.exists():
            try:
                items=json.loads(fp.read_text())
                if isinstance(items,list): candidates.extend(items)
            except: pass

    new_humans=[em for em in candidates if em.get("ts","") not in already_met and is_real_human(em)]
    print(f"  {len(new_humans)} new genuine humans found")

    for em in new_humans[:5]:
        m=re.search(r'<(.+?)>',em.get("from","")); to=m.group(1) if m else em.get("from","")
        if "@" not in to: continue
        intent_data=classify_human_intent(em)
        intent=intent_data.get("intent","curious") if isinstance(intent_data,dict) else "curious"
        print(f"  Human [{intent}]: {to}")
        reply=draft_human_reply(em,intent_data)
        include_bootstrap=intent in ["wants_to_fork","wants_to_collaborate"]
        if reply:
            ok=send_reply(to,em.get("subject","SolarPunk"),reply,include_bootstrap)
            record={"id":em.get("ts",""),"email":to,"intent":intent,"replied":ok,
                    "ts":datetime.now(timezone.utc).isoformat(),"bootstrap_sent":include_bootstrap}
            state.setdefault("humans_met",[]).append(record)
            if include_bootstrap: state["forks_guided"]=state.get("forks_guided",0)+1
            print(f"  {'Replied' if ok else 'Failed'} | Bootstrap: {include_bootstrap}")

    save(state); return state

if __name__=="__main__": run()
