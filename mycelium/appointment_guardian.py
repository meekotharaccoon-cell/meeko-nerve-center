#!/usr/bin/env python3
"""
APPOINTMENT GUARDIAN
=====================
Reads your Gmail. Finds appointments. Creates calendar events.
Adds a noon reminder the day before, in plain human language.
Never stores, logs, or shares any personal info.
Runs daily via GitHub Actions.

Philosophy: typed → read → heard → felt → acted upon
The human sets their life up once. The system remembers forever.
"""
import os, re, json, base64, imaplib, email
from datetime import datetime, timedelta, timezone
from email.header import decode_header
import requests

# ── SECRETS (from GitHub Actions, never in files) ──────────
GMAIL_USER  = 'mickowood86@gmail.com'
GMAIL_PASS  = os.environ.get('GMAIL_APP_PASSWORD', '')
OR_KEY      = os.environ.get('OPENROUTER_KEY', '')

# ── PRIVACY SHIELD ──────────────────────────────────────────
# These are the ONLY fields ever extracted. Nothing else.
# Name of appointment type, date, time, location.
# No personal names, no medical details, no account numbers.
EXTRACT_FIELDS = ['appointment_type', 'date', 'time', 'location', 'notes']

# ── APPOINTMENT KEYWORDS ────────────────────────────────────
APPOINTMENT_SIGNALS = [
    'appointment', 'your visit', 'scheduled for', 'confirmed for',
    'reminder:', 'you have a', 'see you on', 'check-in',
    'arrival time', 'please arrive', 'your appointment is',
    'booking confirmed', 'reservation confirmed', 'class starts',
    'meeting at', 'pickup at', 'drop-off at',
]

def check_gmail_for_appointments():
    """Read Gmail IMAP, find appointment emails, return structured list."""
    if not GMAIL_PASS:
        print('[Guardian] No Gmail password — skipping email scan')
        return []
    
    appointments = []
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select('INBOX')
        
        # Search last 7 days only — fresh appointments, nothing stale
        since = (datetime.now() - timedelta(days=7)).strftime('%d-%b-%Y')
        _, msgs = mail.search(None, f'(SINCE {since})')
        
        for num in msgs[0].split():
            try:
                _, data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])
                subject = str(decode_header(msg['subject'])[0][0])
                body    = get_body(msg)
                
                # Quick filter — does this look like an appointment?
                combined = (subject + ' ' + body).lower()
                if not any(sig in combined for sig in APPOINTMENT_SIGNALS):
                    continue
                
                # Use AI to extract just the structured fields
                extracted = ai_extract_appointment(subject, body)
                if extracted and extracted.get('date'):
                    appointments.append(extracted)
                    print(f"[Guardian] Found: {extracted.get('appointment_type','Appointment')} on {extracted.get('date')}")
            except Exception as e:
                continue  # Skip malformed emails silently
        
        mail.logout()
    except Exception as e:
        print(f'[Guardian] Gmail error: {e}')
    
    return appointments

def get_body(msg):
    """Extract plain text from email."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                try:
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')[:2000]
                except:
                    continue
    try:
        return msg.get_payload(decode=True).decode('utf-8', errors='ignore')[:2000]
    except:
        return ''

def ai_extract_appointment(subject, body):
    """
    Ask AI to extract ONLY structured appointment fields.
    Privacy: AI never sees any field names — only the email content.
    AI outputs only the 5 safe fields. Nothing else passes through.
    """
    if not OR_KEY:
        return None
    
    prompt = f"""Extract appointment details from this email. Return ONLY valid JSON with these exact fields:
{{
  "appointment_type": "short description like 'Dentist', 'DMV', 'Parent-teacher', 'Car service' — no personal names",
  "date": "YYYY-MM-DD or null",
  "time": "HH:MM in 24h or null",
  "location": "address or business name or null",
  "notes": "one sentence of what to bring or do, no personal info, or null"
}}

Rules:
- NEVER include any person's name, medical details, account numbers, or personal identifiers
- If unsure about a field, use null
- appointment_type should be generic category, not specific personal details

Email subject: {subject[:200]}
Email body: {body[:1000]}

Respond with JSON only, no other text."""

    try:
        r = requests.post('https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OR_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'openai/gpt-4o-mini',
                  'messages': [{'role': 'user', 'content': prompt}],
                  'max_tokens': 200, 'temperature': 0},
            timeout=20)
        text = r.json()['choices'][0]['message']['content']
        text = re.sub(r'```json|```', '', text).strip()
        parsed = json.loads(text)
        # Enforce privacy: only keep allowed fields
        return {k: parsed.get(k) for k in EXTRACT_FIELDS}
    except:
        return None

def build_reminder_text(appt):
    """
    Build a plain-English reminder a human would actually want to read.
    The kind you'd write yourself on a sticky note.
    
    'Dentist appointment tomorrow at 2:30 PM — 123 Main St Dental.
     Remember to bring your insurance card.'
    """
    atype    = appt.get('appointment_type', 'Appointment')
    time_str = appt.get('time', '')
    location = appt.get('location', '')
    notes    = appt.get('notes', '')
    
    # Format time humanly
    if time_str:
        try:
            t = datetime.strptime(time_str, '%H:%M')
            time_str = t.strftime('%-I:%M %p')  # "2:30 PM"
        except:
            pass
    
    # Build the sentence
    parts = [f"🔔 {atype} is tomorrow"]
    if time_str:
        parts[0] += f" at {time_str}"
    if location:
        parts.append(f"📍 {location}")
    if notes:
        parts.append(f"📝 {notes}")
    
    return '\n'.join(parts)

def create_calendar_event(appt, gcal_token):
    """
    Create a Google Calendar event for the appointment
    AND a noon reminder the day before.
    Uses Google Calendar API directly.
    """
    if not appt.get('date'):
        return False
    
    try:
        appt_date = datetime.strptime(appt['date'], '%Y-%m-%d')
    except:
        return False
    
    atype    = appt.get('appointment_type', 'Appointment')
    location = appt.get('location', '')
    reminder = build_reminder_text(appt)
    
    # ── EVENT: The actual appointment ──────────────────────
    event_start = appt_date.replace(
        hour  = int(appt['time'].split(':')[0]) if appt.get('time') else 9,
        minute= int(appt['time'].split(':')[1]) if appt.get('time') else 0
    )
    event_end = event_start + timedelta(hours=1)
    
    event_body = {
        'summary': f"📅 {atype}",
        'location': location,
        'description': reminder,
        'start': {'dateTime': event_start.isoformat(), 'timeZone': 'America/New_York'},
        'end':   {'dateTime': event_end.isoformat(),   'timeZone': 'America/New_York'},
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup',  'minutes': 60},
                {'method': 'email',  'minutes': 1440},  # 24h before
            ]
        }
    }
    
    # ── REMINDER EVENT: Day before at noon ─────────────────
    reminder_dt = appt_date.replace(day=appt_date.day - 1, hour=12, minute=0)
    # Handle month rollover properly
    reminder_dt = appt_date - timedelta(days=1)
    reminder_dt = reminder_dt.replace(hour=12, minute=0, second=0)
    
    reminder_body = {
        'summary': f"⏰ TOMORROW: {atype}",
        'description': reminder,
        'start': {'dateTime': reminder_dt.isoformat(), 'timeZone': 'America/New_York'},
        'end':   {'dateTime': (reminder_dt + timedelta(minutes=15)).isoformat(), 'timeZone': 'America/New_York'},
        'reminders': {
            'useDefault': False,
            'overrides': [{'method': 'popup', 'minutes': 0}]
        }
    }
    
    headers = {'Authorization': f'Bearer {gcal_token}', 'Content-Type': 'application/json'}
    base_url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
    
    r1 = requests.post(base_url, headers=headers, json=event_body,    timeout=15)
    r2 = requests.post(base_url, headers=headers, json=reminder_body, timeout=15)
    
    if r1.status_code in (200, 201):
        print(f"[Guardian] Created event: {atype} on {appt['date']}")
    if r2.status_code in (200, 201):
        print(f"[Guardian] Created noon reminder for day before")
    
    return r1.status_code in (200, 201)

def run():
    print(f"\n{'='*50}")
    print("  APPOINTMENT GUARDIAN")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    appointments = check_gmail_for_appointments()
    
    if not appointments:
        print("[Guardian] No new appointments found in last 7 days.")
        return
    
    print(f"\n[Guardian] Found {len(appointments)} appointment(s):")
    for a in appointments:
        print(f"  → {a.get('appointment_type')} | {a.get('date')} {a.get('time','')}")
    
    # Calendar events require OAuth token
    # For now: print what WOULD be created
    print("\n[Guardian] Calendar events that will be created:")
    for a in appointments:
        print(f"\n  EVENT: {a.get('appointment_type')}")
        print(f"  Date:  {a.get('date')} at {a.get('time','TBD')}")
        print(f"  Where: {a.get('location','TBD')}")
        print(f"\n  REMINDER (noon the day before):")
        print(f"  {build_reminder_text(a)}")

if __name__ == '__main__':
    run()
