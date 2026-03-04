#!/usr/bin/env python3
"""EMAIL_BRAIN - SolarPunk Communications Cortex
Reads ALL Gmail. Routes everything. Meeko only sees personal emails.
PERSONAL -> flagged only (never auto-replied)
APPOINTMENT -> CALENDAR_BRAIN -> TOMORROW: You have X at Y
REVENUE -> income engines
BUSINESS -> Claude drafts + sends reply
GITHUB -> log failures
SPAM -> silent skip
"""
import os,json,imaplib,smtplib,email,re,hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from pathlib import Path
from datetime import datetime,timezone
import requests

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
API=os.environ.get("ANTHROPIC_API_KEY","")
MAX=25

REVENUE_SENDERS=["ko-fi.com","gumroad.com","redbubble.com","paypal.com","stripe.com","substack.com"]
APPT_KEYWORDS=["appointment","your visit","confirmation","scheduled","doctor","dr.","clinic",
    "dentist","dental","therapy","telehealth","booking","check-in","lab results","prescription"]

def load():
    f=DATA/"email_brain_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"processed":[],"emails_total":0,"personal":0,"appointments":0,"revenue":0,"business":0,"log":[]}

def save(s):
    s["log"]=s.get("log",[])[-200:]
    s["processed"]=s.get("processed",[])[-1000:]
    (DATA/"email_brain_state.json").write_text(json.dumps(s,indent=2))

def decode_str(v):
    if not v: return ""
    parts=decode_header(v); out=""
    for p,enc in parts:
        out+=(p.decode(enc or "utf-8",errors="replace") if isinstance(p,bytes) else str(p))
    return out

def get_body(msg):
    body=""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type()=="text/plain" and "attachment" not in str(part.get("Content-Disposition","")):
                try: body+=part.get_payload(decode=True).decode("utf-8",errors="replace")
                except: pass
    else:
        try: body=msg.get_payload(decode=True).decode("utf-8",errors="replace")
        except: pass
    return body[:3000]

def fetch_unread():
    if not GMAIL or not GPWD: return []
    try:
        m=imaplib.IMAP4_SSL("imap.gmail.com"); m.login(GMAIL,GPWD); m.select("inbox")
        _,ids=m.search(None,"UNSEEN"); eids=ids[0].split()[-MAX:]
        out=[]
        for eid in eids:
            _,data=m.fetch(eid,"(RFC822)")
            msg=email.message_from_bytes(data[0][1])
            out.append({"id":eid.decode(),"mid":msg.get("Message-ID",""),
                "from":decode_str(msg.get("From","")),"subject":decode_str(msg.get("Subject","")),
                "date":msg.get("Date",""),"body":get_body(msg)})
        m.logout(); print(f"  {len(out)} unread emails"); return out
    except Exception as e: print(f"  IMAP: {e}"); return []

def classify(em):
    s=em["from"].lower(); subj=em["subject"].lower(); body=em["body"].lower()
    for rev in REVENUE_SENDERS:
        if rev in s: return "REVENUE"
    if any(k in subj or k in body for k in APPT_KEYWORDS): return "APPOINTMENT"
    if "github.com" in s or "@github.com" in s: return "GITHUB"
    if not API:
        if any(w in subj for w in ["invoice","order","payment","receipt","sale"]): return "REVENUE"
        if any(w in subj for w in ["hi ","hey ","miss you","thinking of"]): return "PERSONAL"
        return "BUSINESS"
    prompt=f"""Classify this email. FROM:{em['from']} SUBJECT:{em['subject']} BODY:{em['body'][:400]}
Categories: PERSONAL(friend/family-never auto-reply) APPOINTMENT(medical/dental/any visit) REVENUE(payment/sale) BUSINESS(professional) GITHUB(CI alerts) SPAM(promo)
Respond ONLY JSON: {{"cat":"CATEGORY"}}"""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":50,"messages":[{"role":"user","content":prompt}]},timeout=15)
        t=r.json()["content"][0]["text"]; s2,e=t.find("{"),t.rfind("}")+1
        return json.loads(t[s2:e]).get("cat","BUSINESS")
    except: return "BUSINESS"

def extract_appt(em):
    if not API:
        text=em["subject"]+" "+em["body"]
        dm=re.search(r'(\w+ \d{1,2},? \d{4}|\d{1,2}/\d{1,2}/\d{4})',text)
        tm=re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',text)
        return {"date_str":dm.group(1) if dm else None,"time_str":tm.group(1) if tm else None,
                "location":"see original email","type":"appointment","provider":em["from"],"source_subject":em["subject"]}
    prompt=f"""Extract appointment. FROM:{em['from']} SUBJECT:{em['subject']} BODY:{em['body'][:1500]}
ONLY JSON: {{"date_str":"Month DD YYYY","time_str":"HH:MM AM/PM","location":"addr","type":"doctor/etc","provider":"name","notes":"any"}}"""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":250,"messages":[{"role":"user","content":prompt}]},timeout=20)
        t=r.json()["content"][0]["text"]; s2,e=t.find("{"),t.rfind("}")+1
        d=json.loads(t[s2:e]); d["source_subject"]=em["subject"]; return d
    except: return {"date_str":None,"time_str":None,"location":"see email","type":"appointment","provider":em["from"],"source_subject":em["subject"]}

def queue_appointment(details):
    f=DATA/"appointments_inbox.json"
    existing=json.loads(f.read_text()) if f.exists() else []
    details["queued_at"]=datetime.now(timezone.utc).isoformat()
    existing.append(details); f.write_text(json.dumps(existing,indent=2))

def queue_revenue(em):
    f=DATA/"revenue_inbox.json"
    existing=json.loads(f.read_text()) if f.exists() else []
    amt=re.search(r'\$(\d+\.?\d*)',em["subject"]+em["body"])
    existing.append({"ts":datetime.now(timezone.utc).isoformat(),"from":em["from"],
        "subject":em["subject"],"amount":float(amt.group(1)) if amt else 0})
    f.write_text(json.dumps(existing[-100:],indent=2))

def flag_personal(em,state):
    f=DATA/"personal_flagged.json"
    existing=json.loads(f.read_text()) if f.exists() else []
    existing.append({"ts":datetime.now(timezone.utc).isoformat()[:16],
        "from":em["from"],"subject":em["subject"],"snippet":em["body"][:150]})
    f.write_text(json.dumps(existing[-50:],indent=2))
    state["personal"]=state.get("personal",0)+1

def draft_business_reply(em):
    if not API: return None
    prompt=f"""You are SolarPunk, Meeko's AI agent. Draft a business email reply.
FROM:{em['from']} SUBJECT:{em['subject']} BODY:{em['body'][:1200]}
Meeko: Gaza Rose Gallery ($1 AI art, 70% to Palestinian artists) + SolarPunk autonomous system.
Warm, genuine, direct. Under 120 words.
ONLY JSON: {{"subject":"Re:...","body":"reply","send":true,"reason":"why"}}
send=false if uncertain."""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":400,"messages":[{"role":"user","content":prompt}]},timeout=25)
        t=r.json()["content"][0]["text"]; s2,e=t.find("{"),t.rfind("}")+1
        return json.loads(t[s2:e])
    except: return None

def send_email(to,subject,body,reply_mid=None):
    if not GMAIL or not GPWD: return False
    try:
        msg=MIMEMultipart(); msg["From"]=GMAIL; msg["To"]=to; msg["Subject"]=subject
        if reply_mid: msg["In-Reply-To"]=reply_mid; msg["References"]=reply_mid
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,to,msg.as_string())
        return True
    except Exception as e: print(f"  send: {e}"); return False

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"EMAIL_BRAIN cycle {state['cycles']} | {GMAIL or 'no credentials'}")
    if not GMAIL: save(state); return state
    emails=fetch_unread(); done=set(state.get("processed",[]))
    for em in emails:
        h=hashlib.md5((em["mid"]+em["subject"]).encode()).hexdigest()[:12]
        if h in done: continue
        done.add(h); cat=classify(em)
        state["emails_total"]=state.get("emails_total",0)+1
        entry={"ts":datetime.now(timezone.utc).isoformat()[:16],"from":em["from"][:35],"subj":em["subject"][:50],"cat":cat,"action":""}
        if cat=="PERSONAL":
            flag_personal(em,state); entry["action"]="flagged_meeko_only"
        elif cat=="APPOINTMENT":
            d=extract_appt(em); queue_appointment(d)
            state["appointments"]=state.get("appointments",0)+1
            entry["action"]=f"appt_queued:{d.get('type','?')}"
        elif cat=="REVENUE":
            queue_revenue(em); state["revenue"]=state.get("revenue",0)+1; entry["action"]="revenue_routed"
        elif cat=="BUSINESS":
            draft=draft_business_reply(em)
            if draft and draft.get("send"):
                m=re.search(r'<(.+?)>',em["from"]); to=m.group(1) if m else em["from"]
                ok=send_email(to,draft["subject"],draft["body"],em["mid"])
                state["business"]=state.get("business",0)+(1 if ok else 0)
                entry["action"]="replied" if ok else "draft_saved"
            else: entry["action"]="business_queued_review"
        elif cat=="GITHUB":
            entry["action"]="gh_failure_logged" if "fail" in em["subject"].lower() else "gh_logged"
        else: entry["action"]=f"skipped_{cat.lower()}"
        state.setdefault("log",[]).append(entry)
        print(f"  [{cat}] {em['subject'][:45]} -> {entry['action']}")
    state["processed"]=list(done)
    save(state); return state

if __name__=="__main__": run()
