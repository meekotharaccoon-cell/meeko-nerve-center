#!/usr/bin/env python3
"""
Donor Follow-up Sequence Engine
================================
Donors get one thank-you and then silence. This ends that.

Sequence per donor:
  Day 0:  Thank-you + unique Gaza Rose art (handled by donation_engine)
  Day 7:  PCRF impact update — here's what your donation did
  Day 30: New Gaza Rose art drop — a gift, no ask attached

This engine:
  1. Reads kofi_events.json for all donors
  2. Checks who is due for a Day 7 or Day 30 follow-up
  3. Generates a personal message using the LLM
  4. Sends the email
  5. Marks the follow-up sent in the events log
"""

import json, datetime, os, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY     = datetime.date.today()
TODAY_STR = TODAY.isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

def ask_llm(prompt, max_tokens=400):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model':      'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages':   [
                {'role': 'system', 'content': 'You write warm, personal, non-corporate donor messages for a Palestinian solidarity art project. Short, human, real. Sign as Meeko.'},
                {'role': 'user',   'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[donor_seq] LLM error: {e}')
        return None

def send_email(to_addr, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = to_addr
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to_addr, msg.as_string())
        print(f'[donor_seq] Sent to {to_addr}: {subject}')
        return True
    except Exception as e:
        print(f'[donor_seq] Send failed: {e}')
        return False

def days_since(date_str):
    try:
        d = datetime.date.fromisoformat(date_str[:10])
        return (TODAY - d).days
    except:
        return -1

def generate_day7_message(donor_name, amount, original_message):
    pcrf_url = 'https://www.pcrf.net'
    prompt = f"""Write a Day 7 follow-up email to a donor.

Donor: {donor_name or 'friend'}
Amount donated: ${amount}
Their original message: \"{original_message or 'none'}\"

The email should:
- Be warm and personal, not corporate
- Share a specific fact about PCRF impact (e.g. $25 feeds a child for a month, $100 funds a medical consultation)
- Mention that 70% of their donation went directly to PCRF ({pcrf_url})
- NOT ask for anything else
- Be under 150 words
- Sign as Meeko

Just the email body. No subject line.
"""
    return ask_llm(prompt)

def generate_day30_message(donor_name, amount):
    prompt = f"""Write a Day 30 follow-up email to a donor. This is purely a gift — no ask whatsoever.

Donor: {donor_name or 'friend'}
Original amount: ${amount}

The email should:
- Feel like hearing from a friend, not an organization
- Share that new Gaza Rose art was just generated
- Include the GitHub link where they can see the art: https://github.com/meekotharaccoon-cell/meeko-nerve-center
- Mention the project is still running, still free, still open source
- Be under 120 words
- Sign as Meeko

Just the email body. No subject line.
"""
    return ask_llm(prompt)

def run():
    print(f'\n[donor_seq] Donor Follow-up Sequence — {TODAY_STR}')

    events_path = DATA / 'kofi_events.json'
    if not events_path.exists():
        print('[donor_seq] No kofi_events.json. Skipping.')
        return

    try:
        events = json.loads(events_path.read_text())
    except Exception as e:
        print(f'[donor_seq] Read error: {e}')
        return

    if isinstance(events, list):
        event_list = events
    elif isinstance(events, dict):
        event_list = events.get('events', [])
    else:
        return

    sent_count = 0
    modified   = False

    for event in event_list:
        # Only process donation events with an email
        if event.get('type') not in ('donation', 'Donation', 'subscription'):
            continue
        email = event.get('email') or event.get('kofi_email', '')
        if not email or '@' not in email:
            continue

        name    = event.get('from_name') or event.get('name', '')
        amount  = event.get('amount', 0)
        message = event.get('message', '')
        date    = event.get('timestamp') or event.get('date', '')
        age     = days_since(date)

        followups = event.setdefault('followups_sent', [])

        # Day 7 check
        if age >= 7 and 'day7' not in followups:
            print(f'[donor_seq] Day 7 follow-up due for {email}')
            body = generate_day7_message(name, amount, message)
            if body:
                sent = send_email(email, 'A week in — thank you still', body)
                if sent:
                    followups.append('day7')
                    modified = True
                    sent_count += 1

        # Day 30 check
        if age >= 30 and 'day30' not in followups:
            print(f'[donor_seq] Day 30 follow-up due for {email}')
            body = generate_day30_message(name, amount)
            if body:
                sent = send_email(email, 'Still here, still building', body)
                if sent:
                    followups.append('day30')
                    modified = True
                    sent_count += 1

    if modified:
        try:
            if isinstance(events, list):
                events_path.write_text(json.dumps(event_list, indent=2))
            else:
                events['events'] = event_list
                events_path.write_text(json.dumps(events, indent=2))
            print(f'[donor_seq] Events updated with followup tracking')
        except Exception as e:
            print(f'[donor_seq] Save error: {e}')

    print(f'[donor_seq] Done. Sent {sent_count} follow-up(s).')

if __name__ == '__main__':
    run()
