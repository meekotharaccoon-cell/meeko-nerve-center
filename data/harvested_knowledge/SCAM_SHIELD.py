#!/usr/bin/env python3
"""SCAM_SHIELD — Email security + verification layer
- Analyzes every incoming email for scam/phishing/malware signals
- Warns Meeko about dangerous emails with clear explanation
- Auto-quarantines: marks suspicious, never acts on them
- Verifies legit opportunities and flags them as safe
- Operates 100% within legal/ethical bounds: detect, warn, document. Never hack back.
"""
import os,json,re,requests,smtplib
from pathlib import Path
from datetime import datetime,timezone
from email.mime.text import MIMEText

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
API=os.environ.get("ANTHROPIC_API_KEY","")

SCAM_SIGNALS=[
    "click here to claim","you've been selected","congratulations you won",
    "verify your account immediately","your account will be suspended",
    "send gift cards","wire transfer required","urgent response needed",
    "nigerian prince","lottery winner","unclaimed inheritance",
    "crypto investment guaranteed","double your bitcoin","exclusive trading signal",
    "work from home $5000/day","make money fast no experience",
    "IRS notice","final warning","legal action","arrest warrant",
    "confirm your password","update payment info","unusual activity detected",
    "you owe money","debt collection","lawsuit filed"
]

LEGIT_DOMAINS=["github.com","anthropic.com","ko-fi.com","gumroad.com","stripe.com",
               "paypal.com","mozilla.org","opentech.fund","shuttleworthfoundation.org",
               "nlnet.nl","knightfoundation.org","gitcoin.co","afac.com.lb",
               "substack.com","redbubble.com","google.com","microsoft.com"]

def load():
    f=DATA/"scam_shield_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"scams_caught":0,"safe_verified":0,"quarantine":[],"log":[]}

def save(s):
    s["log"]=s.get("log",[])[-200:]
    s["quarantine"]=s.get("quarantine",[])[-100:]
    (DATA/"scam_shield_state.json").write_text(json.dumps(s,indent=2))

def quick_score(em):
    """Heuristic scam scoring - no API needed"""
    score=0; signals=[]
    body_lower=(em.get("subject","")+" "+em.get("body","")).lower()
    sender=em.get("from","").lower()

    for sig in SCAM_SIGNALS:
        if sig in body_lower:
            score+=20; signals.append(sig)

    # Domain mismatch (claims to be PayPal but not from paypal.com)
    if "paypal" in body_lower and "paypal.com" not in sender: score+=30; signals.append("paypal_spoof")
    if "github" in body_lower and "github.com" not in sender and "noreply" not in sender: score+=20; signals.append("github_spoof")
    if "bank" in body_lower and not any(d in sender for d in ["bank","chase","wells","citi"]): score+=15; signals.append("bank_spoof")

    # Urgency + pressure
    urgent_words=["immediately","urgent","asap","within 24 hours","final notice","last chance"]
    if sum(1 for w in urgent_words if w in body_lower)>=2: score+=25; signals.append("pressure_tactics")

    # Suspicious links
    sus_link=re.findall(r'http[s]?://(?:bit\.ly|tinyurl|t\.co|goo\.gl)/\S+',body_lower)
    if sus_link: score+=15; signals.append(f"shortened_links:{len(sus_link)}")

    # Crypto scam patterns
    if re.search(r'(double|triple|10x|100x|guaranteed).{0,20}(crypto|bitcoin|ethereum|profit)',body_lower):
        score+=40; signals.append("crypto_scam")

    # Legit domain = reduce score
    if any(d in sender for d in LEGIT_DOMAINS): score=max(0,score-30); signals.append("legit_domain")

    return score, signals

def analyze_with_claude(em):
    if not API: return None
    prompt=f"""Analyze this email for scam/phishing/malware risk. Be precise.
FROM: {em.get('from','')} SUBJECT: {em.get('subject','')} BODY: {em.get('body','')[:600]}
Consider: phishing, social engineering, malware links, impersonation, advance fee fraud, crypto scams.
ONLY JSON: {{"risk":"high/medium/low/safe","category":"phishing/scam/spam/legit/opportunity","summary":"1 sentence","safe_to_act":true/false,"why":"brief reason"}}"""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":200,"messages":[{"role":"user","content":prompt}]},timeout=20)
        t=r.json()["content"][0]["text"]; s,e=t.find("{"),t.rfind("}")+1
        return json.loads(t[s:e])
    except: return None

def alert_meeko(em,score,signals,analysis):
    if not GMAIL or not GPWD: return
    risk=analysis.get("risk","high") if analysis else ("high" if score>60 else "medium")
    body=(f"SCAM SHIELD ALERT - {risk.upper()} RISK\n\n"
        f"From: {em.get('from','')}\n"
        f"Subject: {em.get('subject','')}\n"
        f"Risk Score: {score}/100\n"
        f"Signals: {', '.join(signals)}\n"
        f"Analysis: {analysis.get('summary','') if analysis else 'Heuristic detection'}\n"
        f"Why dangerous: {analysis.get('why','Multiple scam signals detected') if analysis else ''}\n\n"
        f"ACTION: This email has been QUARANTINED. Do not click any links or reply.\n"
        f"SolarPunk will not act on this email.\n\n"
        f"[SolarPunk SCAM_SHIELD - {datetime.now(timezone.utc).isoformat()[:16]}]")
    try:
        msg=MIMEText(body); msg["From"]=GMAIL; msg["To"]=GMAIL
        msg["Subject"]=f"SCAM ALERT [{risk.upper()}]: {em.get('subject','')[:50]}"
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,GMAIL,msg.as_string())
    except: pass

def scan_inbox():
    """Scan processed emails for scam signals"""
    log_f=DATA/"email_brain_state.json"
    if not log_f.exists(): return []
    try: state=json.loads(log_f.read_text())
    except: return []
    return state.get("log",[])[-30:]  # Recent emails

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"SCAM_SHIELD cycle {state['cycles']} | {state.get('scams_caught',0)} caught")

    # Load all email metadata we've seen
    email_log=scan_inbox()
    already_scanned={e.get("id","") for e in state.get("log",[])}
    new_emails=[e for e in email_log if e.get("ts","") not in already_scanned]

    print(f"  Scanning {len(new_emails)} new emails")
    for em_meta in new_emails[:20]:
        # Build minimal email object from log
        em={"from":em_meta.get("from",""),"subject":em_meta.get("subj",""),"body":""}
        score,signals=quick_score(em)

        if score>=40:
            # High enough to warrant Claude analysis
            analysis=analyze_with_claude(em) if API else None
            is_scam=(analysis.get("risk") in ["high","medium"] if analysis else score>=50)
            entry={"id":em_meta.get("ts",""),"from":em["from"],"subj":em["subject"],
                   "score":score,"signals":signals,"risk":analysis.get("risk","?") if analysis else "medium",
                   "ts":datetime.now(timezone.utc).isoformat(),"quarantined":is_scam}
            if is_scam:
                state["scams_caught"]=state.get("scams_caught",0)+1
                state.setdefault("quarantine",[]).append(entry)
                alert_meeko(em,score,signals,analysis)
                print(f"  SCAM [{score}pts]: {em['subject'][:50]} | {', '.join(signals[:3])}")
            else:
                print(f"  OK [{score}pts]: {em['subject'][:40]}")
            state.setdefault("log",[]).append(entry)
        else:
            state["safe_verified"]=state.get("safe_verified",0)+1
            state.setdefault("log",[]).append({"id":em_meta.get("ts",""),"score":score,"safe":True,"ts":datetime.now(timezone.utc).isoformat()[:16]})

    print(f"  Total: {state.get('scams_caught',0)} scams | {state.get('safe_verified',0)} safe")
    save(state); return state

if __name__=="__main__": run()
