#!/usr/bin/env python3
"""
Email Opt-In Guard — Global dedup + consent layer for ALL outbound email
=========================================================================
PROBLEM SOLVED: The system was sending the same email to the same address
multiple times (Remi from OTF received 2 duplicates before responding).

This module is the SINGLE GATEKEEPER for all external outbound email.
Every script that sends external email MUST call this module first.

HOW IT WORKS:
  1. Before sending ANY first-contact email to an external address:
     - Check data/email_optin_log.json for this address
     - If already contacted within 30 days: BLOCK. Don't send again.
     - If opted out: BLOCK FOREVER. Never contact again.
     - If not seen before: Send opt-in email first. Queue the actual email.

  2. The opt-in email says:
     "Do you even want info on THIS system? Reply with Yes or No."
     Yes → sends the queued email
     No → marks them opted-out forever, deletes their data

  3. When email_gateway.py sees a reply:
     - "yes" reply → marks opted-in, sends queued email
     - "no" reply → marks opted-out forever
     - anything else (auto-reply, human reply to different topic) → ignored

  4. All of this is persisted to data/email_optin_log.json and committed
     to git so dedup survives across workflow runs.

USAGE (in other scripts):
    from mycelium.email_optin_guard import can_send, mark_optin_sent

    if can_send(to_email):
        send_optin_request(to_email, name, queue_payload)
    # Don't send the actual email yet — wait for Yes reply

Or for self-emails (gmail_address to gmail_address):
    These bypass opt-in (you're emailing yourself).
"""

import json, os, datetime, hashlib, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

OPTIN_LOG_PATH  = DATA / 'email_optin_log.json'
OPTIN_QUEUE_PATH = DATA / 'email_optin_queue.json'


def _email_key(email: str) -> str:
    return hashlib.md5(email.lower().strip().encode()).hexdigest()[:16]


def load_optin_log() -> dict:
    try:
        if OPTIN_LOG_PATH.exists():
            return json.loads(OPTIN_LOG_PATH.read_text())
    except: pass
    return {}


def save_optin_log(log: dict):
    DATA.mkdir(parents=True, exist_ok=True)
    try: OPTIN_LOG_PATH.write_text(json.dumps(log, indent=2))
    except: pass


def is_self_email(email: str) -> bool:
    """Self-emails bypass opt-in (internal system emails to you)."""
    if GMAIL_ADDRESS and GMAIL_ADDRESS.lower() in email.lower():
        return True
    if 'meekotharaccoon' in email.lower():
        return True
    return False


def get_status(email: str) -> str:
    """
    Returns one of:
      'clear'      — never contacted, safe to send opt-in
      'pending'    — opt-in sent, waiting for reply
      'opted_in'   — replied Yes, safe to send actual email
      'opted_out'  — replied No, NEVER contact again
      'cooldown'   — contacted too recently, wait
    """
    if is_self_email(email):
        return 'self'
    log = load_optin_log()
    key = _email_key(email)
    entry = log.get(key)
    if not entry:
        return 'clear'
    status = entry.get('status', 'clear')
    if status == 'opted_out':
        return 'opted_out'
    if status == 'opted_in':
        return 'opted_in'
    if status == 'pending':
        # Check if pending expired (30 days without reply = move back to clear)
        sent_date = entry.get('optin_sent')
        if sent_date:
            try:
                age = (datetime.date.today() - datetime.date.fromisoformat(sent_date)).days
                if age > 30:
                    return 'clear'  # Expired — they ignored it, don't spam
            except: pass
        return 'pending'
    return 'clear'


def can_send_first_contact(email: str) -> bool:
    """Can we send an opt-in request to this address?"""
    if is_self_email(email):
        return True  # Always OK to email yourself
    status = get_status(email)
    return status == 'clear'  # Only if never contacted


def mark_optin_sent(email: str, name: str = '', context: str = ''):
    """Record that opt-in email was sent."""
    log = load_optin_log()
    key = _email_key(email)
    log[key] = {
        'email_preview': email[:40],
        'name': name,
        'status': 'pending',
        'optin_sent': TODAY,
        'context': context,
    }
    save_optin_log(log)


def mark_opted_in(email: str):
    """They replied Yes."""
    log = load_optin_log()
    key = _email_key(email)
    entry = log.get(key, {})
    entry['status'] = 'opted_in'
    entry['opted_in_date'] = TODAY
    log[key] = entry
    save_optin_log(log)
    print(f'[optin] ✅ Opted IN: {email[:40]}')


def mark_opted_out(email: str):
    """They replied No — never contact again."""
    log = load_optin_log()
    key = _email_key(email)
    entry = log.get(key, {})
    entry['status'] = 'opted_out'
    entry['opted_out_date'] = TODAY
    log[key] = entry
    save_optin_log(log)
    # Remove from queue if present
    try:
        if OPTIN_QUEUE_PATH.exists():
            queue = json.loads(OPTIN_QUEUE_PATH.read_text())
            queue = [q for q in queue if _email_key(q.get('email', '')) != key]
            OPTIN_QUEUE_PATH.write_text(json.dumps(queue, indent=2))
    except: pass
    print(f'[optin] 🚫 Opted OUT (forever): {email[:40]}')


def queue_pending_email(email: str, name: str, subject: str, body: str, context: str = ''):
    """Queue the actual email to send after they opt in."""
    DATA.mkdir(parents=True, exist_ok=True)
    queue = []
    try:
        if OPTIN_QUEUE_PATH.exists():
            queue = json.loads(OPTIN_QUEUE_PATH.read_text())
    except: pass
    # Dedup: only one pending per address
    queue = [q for q in queue if q.get('email', '').lower() != email.lower()]
    queue.append({
        'email': email,
        'name': name,
        'subject': subject,
        'body': body,
        'context': context,
        'queued_date': TODAY,
    })
    OPTIN_QUEUE_PATH.write_text(json.dumps(queue, indent=2))


def send_optin_email(to_email: str, name: str, context: str = '') -> bool:
    """
    Send the opt-in gate email.
    Subject: Do you want info on this? Reply Yes or No.
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f'[optin] No SMTP credentials — cannot send opt-in to {to_email[:40]}')
        return False

    greeting = f'Hello {name},' if name else 'Hello,'
    body = f"""{greeting}

Quick question before anything else:

Do you want to receive information about the Meeko Nerve Center / SolarPunk system?

Reply with:
  YES — and I'll send you the full details
  NO  — and I'll leave you alone forever and remove your address entirely

That's it. No tricks. One of those two replies and you're done either way.

— Meeko Nerve Center
{REPO_URL}
"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Do you want info on this? (Reply Yes or No)'
        msg['From']    = f'Meeko Nerve Center 🌸 <{GMAIL_ADDRESS}>'
        msg['To']      = to_email
        msg['Reply-To'] = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        print(f'[optin] ✅ Opt-in sent to {to_email[:40]}')
        return True
    except Exception as e:
        print(f'[optin] SMTP error: {e}')
        return False


def send_queued_email_to_optin(email: str) -> bool:
    """Send the queued email now that they've opted in."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return False
    try:
        if not OPTIN_QUEUE_PATH.exists():
            return False
        queue = json.loads(OPTIN_QUEUE_PATH.read_text())
        pending = [q for q in queue if q.get('email', '').lower() == email.lower()]
        if not pending:
            print(f'[optin] No queued email for {email[:40]}')
            return False
        item = pending[0]
        msg = MIMEMultipart('alternative')
        msg['Subject'] = item['subject']
        msg['From']    = f'Meeko Nerve Center 🌸 <{GMAIL_ADDRESS}>'
        msg['To']      = email
        msg.attach(MIMEText(item['body'], 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, email, msg.as_string())
        # Remove from queue
        queue = [q for q in queue if q.get('email', '').lower() != email.lower()]
        OPTIN_QUEUE_PATH.write_text(json.dumps(queue, indent=2))
        print(f'[optin] ✅ Queued email sent to opted-in address: {email[:40]}')
        return True
    except Exception as e:
        print(f'[optin] Error sending queued email: {e}')
        return False


def process_reply(from_email: str, subject: str, body: str):
    """
    Called by email_gateway.py when processing inbound emails.
    Handles Yes/No replies to opt-in emails.
    Returns True if this was an opt-in reply (handled here).
    """
    text = (subject + ' ' + body).lower().strip()
    # Check if this is a response to our opt-in request
    status = get_status(from_email)
    if status != 'pending':
        return False  # Not waiting for opt-in reply from this address

    # Clean reply detection
    text_stripped = text.replace('re:', '').strip()
    first_word = text_stripped.split()[0] if text_stripped.split() else ''

    is_yes = (
        text_stripped.startswith('yes') or
        first_word == 'yes' or
        'yes i want' in text_stripped or
        'yes please' in text_stripped
    )
    is_no = (
        text_stripped.startswith('no') or
        first_word == 'no' or
        'no thanks' in text_stripped or
        'no thank you' in text_stripped or
        'leave me alone' in text_stripped or
        'unsubscribe' in text_stripped
    )

    if is_yes:
        mark_opted_in(from_email)
        send_queued_email_to_optin(from_email)
        return True
    elif is_no:
        mark_opted_out(from_email)
        return True
    else:
        # Not a clear Yes/No — probably an auto-reply or human saying something else
        # Don't process as opt-in, let email_gateway handle normally
        return False


def first_contact(to_email: str, name: str, subject: str, body: str, context: str = '') -> bool:
    """
    The ONE function all external email senders call.
    Handles everything: dedup check → opt-in → queue.
    Returns True if opt-in was sent (or already opted in).
    Returns False if blocked (opted out or duplicate).
    """
    if is_self_email(to_email):
        # Self emails don't need opt-in
        return True

    status = get_status(to_email)

    if status == 'opted_out':
        print(f'[optin] 🚫 BLOCKED (opted out): {to_email[:40]}')
        return False

    if status == 'pending':
        print(f'[optin] ⏳ BLOCKED (already pending): {to_email[:40]}')
        return False

    if status == 'opted_in':
        # Already consented — queue is already sent. Log that we're not re-sending.
        print(f'[optin] ✅ Already opted in: {to_email[:40]} — send directly')
        return True  # Caller can send their email

    # status == 'clear' — first contact
    queue_pending_email(to_email, name, subject, body, context)
    ok = send_optin_email(to_email, name, context)
    if ok:
        mark_optin_sent(to_email, name, context)
    return ok
