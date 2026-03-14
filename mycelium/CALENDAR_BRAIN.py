# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""CALENDAR_BRAIN v2 - Appointment -> ICS -> TOMORROW reminder
Reads appointments_inbox.json -> sends ICS email to self -> Google Calendar auto-imports

FIXES v2 — companion to EMAIL_BRAIN v3:
- is_real_appointment() validation gate before ANY email is sent
- low-confidence appointments: logged but NOT emailed (no more ghost reminders)
- bot sender check as second line of defense
- appointment must have both date_str AND time_str
- bot subject patterns block phantom events
"""
import os, json, smtplib, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

DATA  = Path("data"); DATA.mkdir(exist_ok=True)
GMAIL = os.environ.get("GMAIL_ADDRESS", "")
GPWD  = os.environ.get("GMAIL_APP_PASSWORD", "")

# Bot sender patterns -- second line of defense after EMAIL_BRAIN
BOT_PATTERNS = [
    "noreply", "no-reply", "no_reply", "donotreply", "do-not-reply",
    "mailer-daemon", "automated", "notifications@", "alerts@",
]

# Subject patterns that guarantee this is NOT a real appointment
BOT_SUBJECT_PATTERNS = [
    "order confirmed", "your order", "receipt for", "invoice",
    "verify your email", "reset your password", "welcome to",
    "subscription confirmed", "unsubscribe", "out of office",
    "auto-reply", "delivery notification", "account created",
    "thanks for signing", "thank you for register",
]


def load():
    f = DATA / "calendar_brain_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "sent": 0, "skipped": 0, "log": []}


def save(s):
    s["log"] = s.get("log", [])[-100:]
    (DATA / "calendar_brain_state.json").write_text(json.dumps(s, indent=2))


def is_real_appointment(appt):
    """
    Validate that this looks like a real human appointment.
    Returns (is_valid, reason) tuple.
    This is the fix for ghost calendar reminders from auto-reply bots.
    """
    # Must have a date string
    if not appt.get("date_str"):
        return False, "no_date"

    # Must have time info
    if not appt.get("time_str"):
        return False, "no_time"

    # Low confidence (regex fallback) = queue for review, not emailed
    if appt.get("confidence") in ("low", None):
        return False, "low_confidence"

    # Bot sender check -- second line of defense
    provider = (appt.get("provider") or appt.get("source_from") or "").lower()
    if any(p in provider for p in BOT_PATTERNS):
        return False, "bot_sender"

    # Bot subject check
    subj = (appt.get("source_subject") or "").lower()
    if any(p in subj for p in BOT_SUBJECT_PATTERNS):
        return False, f"bot_subject"

    return True, "ok"


def build_ics(appt):
    typ   = (appt.get("type") or "appointment").title()
    loc   = appt.get("location") or "see email"
    ts    = appt.get("time_str") or "see email"
    ds    = appt.get("date_str") or "see email"
    prov  = appt.get("provider") or ""
    notes = appt.get("notes") or ""
    uid   = f"solarpunk-{datetime.now().strftime('%Y%m%d%H%M%S')}@meeko"
    try:
        from dateutil import parser as dp
        dt = dp.parse(f"{ds} {ts}").replace(tzinfo=timezone.utc)
    except:
        dt = datetime.now(timezone.utc) + timedelta(days=7)
    dtstr = dt.strftime("%Y%m%dT%H%M%SZ")
    dtend = (dt + timedelta(hours=1)).strftime("%Y%m%dT%H%M%SZ")
    now   = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//SolarPunk//CalendarBrain//EN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now}
DTSTART:{dtstr}
DTEND:{dtend}
SUMMARY:{typ} - {ts}
LOCATION:{loc}
DESCRIPTION:Type: {typ}\\nDate: {ds}\\nTime: {ts}\\nLocation: {loc}\\nProvider: {prov}\\nNotes: {notes}\\n[SolarPunk CalendarBrain v2]
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:TOMORROW: You have {typ} at {loc} - {ts}
TRIGGER:-PT24H
END:VALARM
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:IN 1 HOUR: {typ} at {loc}
TRIGGER:-PT1H
END:VALARM
END:VEVENT
END:VCALENDAR""".encode()


def send_reminder(appt):
    if not GMAIL or not GPWD: return False
    typ   = (appt.get("type") or "appointment").lower()
    loc   = appt.get("location") or "location in original email"
    ts    = appt.get("time_str") or "see original email"
    ds    = appt.get("date_str") or ""
    prov  = appt.get("provider") or ""
    notes = appt.get("notes") or ""
    conf  = appt.get("confidence", "?")
    subj  = f"TOMORROW: You have {typ} at {loc} - {ts}"
    body  = (
        f"SolarPunk detected a REAL appointment (confidence: {conf}).\n\n"
        f"TOMORROW: {typ.upper()}\n"
        f"  When:    {ts}, {ds}\n"
        f"  Where:   {loc}\n"
        f"  With:    {prov}\n"
        f"  Notes:   {notes or 'none'}\n\n"
        f"Added to Google Calendar. Alarms: 24h before + 1h before.\n"
        f"[SolarPunk CalendarBrain v2 - validated appointment]\n"
        f"[Source: {appt.get('source_subject', '')}]"
    )
    msg = MIMEMultipart("mixed")
    msg["From"]    = GMAIL
    msg["To"]      = GMAIL
    msg["Subject"] = subj
    msg.attach(MIMEText(body, "plain"))
    try:
        ics  = build_ics(appt)
        part = MIMEBase("text", "calendar", method="REQUEST", name="appointment.ics")
        part.set_payload(ics)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename="appointment.ics")
        part.add_header("Content-Type", 'text/calendar; method=REQUEST; name="appointment.ics"')
        msg.attach(part)
    except:
        pass
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(GMAIL, GPWD)
            s.sendmail(GMAIL, GMAIL, msg.as_string())
        print(f"  Calendar reminder sent: {subj[:65]}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def run():
    state = load()
    state["cycles"]   = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"CALENDAR_BRAIN v2 cycle {state['cycles']}")

    inbox = DATA / "appointments_inbox.json"
    if not inbox.exists():
        print("  No appointments inbox")
        save(state)
        return state

    try:
        appts = json.loads(inbox.read_text())
    except:
        save(state)
        return state

    sent_keys = {e.get("key") for e in state.get("log", [])}
    sent = skipped = 0

    for appt in appts:
        key = f"{appt.get('type','?')}_{appt.get('date_str','?')}_{appt.get('provider','?')}"
        if key in sent_keys:
            continue

        # VALIDATION -- this is the fix for ghost appointments
        valid, reason = is_real_appointment(appt)
        if not valid:
            print(f"  SKIP ({reason}): {appt.get('source_subject','?')[:60]}")
            state.setdefault("log", []).append({
                "key":     key,
                "ts":      datetime.now(timezone.utc).isoformat(),
                "sent":    False,
                "skipped": True,
                "reason":  reason,
            })
            state["skipped"] = state.get("skipped", 0) + 1
            skipped += 1
            continue

        ok = send_reminder(appt)
        state["sent"] = state.get("sent", 0) + (1 if ok else 0)
        state.setdefault("log", []).append({
            "key":  key,
            "ts":   datetime.now(timezone.utc).isoformat(),
            "sent": ok,
        })
        sent += 1

    print(f"  {sent} sent | {skipped} skipped (not real) | {state.get('sent',0)} total sent")
    save(state)
    return state


if __name__ == "__main__":
    run()
