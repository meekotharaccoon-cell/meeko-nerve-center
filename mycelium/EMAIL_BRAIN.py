#!/usr/bin/env python3
"""EMAIL_BRAIN - SolarPunk Communications Cortex v2
Reads ALL Gmail. Routes everything. Meeko only sees personal emails.
PERSONAL      -> flagged only (never auto-replied)
APPOINTMENT   -> CALENDAR_BRAIN queue
EXCHANGE_TASK -> exchange_inbox.json (for EMAIL_AGENT_EXCHANGE)
REVENUE       -> revenue_inbox.json (Ko-fi, Gumroad, payment confirmations) WITH body
BUSINESS      -> AI drafts + sends reply
GITHUB        -> log failures
SPAM          -> silent skip

FIXES v2:
- Uses AI_CLIENT (free HF) instead of Anthropic direct
- New EXCHANGE_TASK category: [TASK] emails -> exchange_inbox.json with full body
- queue_revenue() now stores body so KOFI_PAYMENT_TRACKER can parse refs
- queue_exchange_task() feeds EMAIL_AGENT_EXCHANGE directly
"""
import os, json, imaplib, smtplib, email, re, hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from pathlib import Path
from datetime import datetime, timezone

# AI_CLIENT: free HF models, no Anthropic key needed
try:
    from AI_CLIENT import ask, ask_json
    AI_ONLINE = True
except ImportError:
    AI_ONLINE = False
    def ask(messages, **kw): return ""
    def ask_json(prompt, **kw): return None

DATA  = Path("data"); DATA.mkdir(exist_ok=True)
GMAIL = os.environ.get("GMAIL_ADDRESS", "")
GPWD  = os.environ.get("GMAIL_APP_PASSWORD", "")
MAX   = 25

REVENUE_SENDERS   = ["ko-fi.com", "gumroad.com", "redbubble.com", "paypal.com",
                      "stripe.com", "substack.com", "noreply@ko-fi.com"]
APPT_KEYWORDS     = ["appointment", "your visit", "confirmation", "scheduled",
                      "doctor", "dr.", "clinic", "dentist", "dental",
                      "therapy", "telehealth", "booking", "check-in",
                      "lab results", "prescription"]
EXCHANGE_KEYWORDS = ["[task]", "agent task", "agent request", "solarpunk agent"]


def load():
    f = DATA / "email_brain_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "processed": [], "emails_total": 0,
            "personal": 0, "appointments": 0, "revenue": 0, "business": 0,
            "exchange_tasks": 0, "log": []}


def save(s):
    s["log"]       = s.get("log", [])[-200:]
    s["processed"] = s.get("processed", [])[-1000:]
    (DATA / "email_brain_state.json").write_text(json.dumps(s, indent=2))


def decode_str(v):
    if not v: return ""
    parts = decode_header(v); out = ""
    for p, enc in parts:
        out += (p.decode(enc or "utf-8", errors="replace")
                if isinstance(p, bytes) else str(p))
    return out


def get_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if (part.get_content_type() == "text/plain"
                    and "attachment" not in str(part.get("Content-Disposition", ""))):
                try: body += part.get_payload(decode=True).decode("utf-8", errors="replace")
                except: pass
    else:
        try: body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except: pass
    return body[:3000]


def fetch_unread():
    if not GMAIL or not GPWD:
        print("  EMAIL_BRAIN: no Gmail credentials")
        return []
    try:
        m = imaplib.IMAP4_SSL("imap.gmail.com")
        m.login(GMAIL, GPWD)
        m.select("inbox")
        _, ids = m.search(None, "UNSEEN")
        eids = ids[0].split()[-MAX:]
        out = []
        for eid in eids:
            _, data = m.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            out.append({
                "id":      eid.decode(),
                "mid":     msg.get("Message-ID", ""),
                "from":    decode_str(msg.get("From", "")),
                "subject": decode_str(msg.get("Subject", "")),
                "date":    msg.get("Date", ""),
                "body":    get_body(msg),
            })
        m.logout()
        print(f"  {len(out)} unread emails")
        return out
    except Exception as e:
        print(f"  IMAP: {e}")
        return []


def classify(em):
    s    = em["from"].lower()
    subj = em["subject"].lower()
    body = em["body"].lower()

    # Fast-path: exchange task
    if any(kw in subj for kw in EXCHANGE_KEYWORDS) or "[task]" in subj:
        return "EXCHANGE_TASK"

    # Fast-path: revenue senders
    for rev in REVENUE_SENDERS:
        if rev in s: return "REVENUE"

    # Fast-path: appointment keywords
    if any(k in subj or k in body for k in APPT_KEYWORDS):
        return "APPOINTMENT"

    # Fast-path: GitHub
    if "github.com" in s or "@github.com" in s:
        return "GITHUB"

    # AI classification — free HF models
    prompt = (
        f"Classify this email.\n"
        f"FROM:{em['from']}\nSUBJECT:{em['subject']}\nBODY:{em['body'][:400]}\n\n"
        f"Categories:\n"
        f"  EXCHANGE_TASK: someone wants an AI agent to do a task\n"
        f"  PERSONAL: friend or family — never auto-reply\n"
        f"  APPOINTMENT: medical/dental/any visit confirmation\n"
        f"  REVENUE: payment/sale notification\n"
        f"  BUSINESS: professional inquiry\n"
        f"  GITHUB: CI/CD alerts\n"
        f"  SPAM: promotional\n"
        f'Respond ONLY with JSON: {{"cat": "CATEGORY"}}'
    )
    result = ask_json(prompt, max_tokens=50)
    if result:
        cat = result.get("cat", "BUSINESS").strip().upper()
        valid = {"EXCHANGE_TASK", "PERSONAL", "APPOINTMENT", "REVENUE", "BUSINESS", "GITHUB", "SPAM"}
        return cat if cat in valid else "BUSINESS"

    # Keyword fallback without AI
    if any(w in subj for w in ["invoice", "order", "payment", "receipt", "sale"]):
        return "REVENUE"
    if any(w in subj for w in ["hi ", "hey ", "miss you", "thinking of"]):
        return "PERSONAL"
    return "BUSINESS"


def extract_appt(em):
    prompt = (
        f"Extract appointment details from this email.\n"
        f"FROM:{em['from']}\nSUBJECT:{em['subject']}\nBODY:{em['body'][:1500]}\n"
        f'Respond ONLY with JSON: {{"date_str":"Month DD YYYY","time_str":"HH:MM AM/PM","location":"addr","type":"doctor/etc","provider":"name","notes":"any"}}'
    )
    result = ask_json(prompt, max_tokens=250)
    if result:
        result["source_subject"] = em["subject"]
        return result
    # Regex fallback
    text = em["subject"] + " " + em["body"]
    dm   = re.search(r'(\w+ \d{1,2},? \d{4}|\d{1,2}/\d{1,2}/\d{4})', text)
    tm   = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', text)
    return {
        "date_str":       dm.group(1) if dm else None,
        "time_str":       tm.group(1) if tm else None,
        "location":       "see original email",
        "type":           "appointment",
        "provider":       em["from"],
        "source_subject": em["subject"],
    }


def queue_appointment(details):
    f = DATA / "appointments_inbox.json"
    existing = json.loads(f.read_text()) if f.exists() else []
    details["queued_at"] = datetime.now(timezone.utc).isoformat()
    existing.append(details)
    f.write_text(json.dumps(existing, indent=2))


def queue_revenue(em):
    """Store revenue notification — includes body so payment tracker can parse refs."""
    f = DATA / "revenue_inbox.json"
    existing = json.loads(f.read_text()) if f.exists() else []
    amt = re.search(r'\$(\d+\.?\d*)', em["subject"] + em["body"])
    entry = {
        "ts":      datetime.now(timezone.utc).isoformat(),
        "from":    em["from"],
        "subject": em["subject"],
        "body":    em["body"][:1000],   # FIX: include body for payment ref parsing
        "amount":  float(amt.group(1)) if amt else 0,
    }
    existing.append(entry)
    f.write_text(json.dumps(existing[-200:], indent=2))


def queue_exchange_task(em):
    """Write task emails to exchange_inbox.json for EMAIL_AGENT_EXCHANGE to consume."""
    f = DATA / "exchange_inbox.json"
    existing = json.loads(f.read_text()) if f.exists() else []
    entry = {
        "ts":               datetime.now(timezone.utc).isoformat(),
        "email_id":         em.get("mid", "") or em.get("id", ""),
        "from":             em["from"],
        "subject":          em["subject"],
        "body":             em["body"][:2000],
        "is_exchange_task": True,
    }
    existing.append(entry)
    f.write_text(json.dumps(existing[-200:], indent=2))


def flag_personal(em, state):
    f = DATA / "personal_flagged.json"
    existing = json.loads(f.read_text()) if f.exists() else []
    existing.append({
        "ts":      datetime.now(timezone.utc).isoformat()[:16],
        "from":    em["from"],
        "subject": em["subject"],
        "snippet": em["body"][:150],
    })
    f.write_text(json.dumps(existing[-50:], indent=2))
    state["personal"] = state.get("personal", 0) + 1


def draft_business_reply(em):
    prompt = (
        f"You are SolarPunk, Meeko's AI agent. Draft a warm, genuine business reply.\n"
        f"FROM:{em['from']}\nSUBJECT:{em['subject']}\nBODY:{em['body'][:1200]}\n\n"
        f"Context: Gaza Rose Gallery ($1 AI art, 70% to Palestinian artists) + SolarPunk autonomous system.\n"
        f"Keep under 120 words. Direct and genuine.\n"
        f'Respond ONLY with JSON: {{"subject":"Re:...","body":"reply text","send":true,"reason":"why"}}\n'
        f"Set send=false if ambiguous."
    )
    return ask_json(prompt, max_tokens=400)


def send_email(to, subject, body, reply_mid=None):
    if not GMAIL or not GPWD: return False
    try:
        msg = MIMEMultipart()
        msg["From"]    = GMAIL
        msg["To"]      = to
        msg["Subject"] = subject
        if reply_mid:
            msg["In-Reply-To"] = reply_mid
            msg["References"]  = reply_mid
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(GMAIL, GPWD)
            s.sendmail(GMAIL, to, msg.as_string())
        return True
    except Exception as e:
        print(f"  send: {e}")
        return False


def run():
    state = load()
    state["cycles"]   = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"EMAIL_BRAIN cycle {state['cycles']} | {GMAIL or 'no credentials'} | AI={'online' if AI_ONLINE else 'offline'}")

    if not GMAIL:
        save(state)
        return state

    emails = fetch_unread()
    done   = set(state.get("processed", []))

    for em in emails:
        h = hashlib.md5((em["mid"] + em["subject"]).encode()).hexdigest()[:12]
        if h in done: continue
        done.add(h)

        cat = classify(em)
        state["emails_total"] = state.get("emails_total", 0) + 1
        entry = {
            "ts":     datetime.now(timezone.utc).isoformat()[:16],
            "from":   em["from"][:35],
            "subj":   em["subject"][:50],
            "cat":    cat,
            "action": "",
        }

        if cat == "EXCHANGE_TASK":
            queue_exchange_task(em)
            state["exchange_tasks"] = state.get("exchange_tasks", 0) + 1
            entry["action"] = "exchange_queued"

        elif cat == "PERSONAL":
            flag_personal(em, state)
            entry["action"] = "flagged_meeko_only"

        elif cat == "APPOINTMENT":
            d = extract_appt(em)
            queue_appointment(d)
            state["appointments"] = state.get("appointments", 0) + 1
            entry["action"] = f"appt_queued:{d.get('type', '?')}"

        elif cat == "REVENUE":
            queue_revenue(em)
            state["revenue"] = state.get("revenue", 0) + 1
            entry["action"] = "revenue_routed"

        elif cat == "BUSINESS":
            draft = draft_business_reply(em)
            if draft and draft.get("send"):
                m  = re.search(r'<(.+?)>', em["from"])
                to = m.group(1) if m else em["from"]
                ok = send_email(to, draft["subject"], draft["body"], em["mid"])
                state["business"] = state.get("business", 0) + (1 if ok else 0)
                entry["action"]   = "replied" if ok else "draft_saved"
            else:
                entry["action"] = "business_queued_review"

        elif cat == "GITHUB":
            entry["action"] = "gh_failure_logged" if "fail" in em["subject"].lower() else "gh_logged"

        else:
            entry["action"] = f"skipped_{cat.lower()}"

        state.setdefault("log", []).append(entry)
        print(f"  [{cat}] {em['subject'][:45]} → {entry['action']}")

    state["processed"] = list(done)
    save(state)
    return state


if __name__ == "__main__":
    run()
