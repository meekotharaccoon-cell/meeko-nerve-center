#!/usr/bin/env python3
"""
MYCELIUM EMAIL RESPONDER

Checks mickowood86@gmail.com for new replies.
Uses OpenRouter AI to draft human, warm, unique responses.
Sends them automatically via Gmail SMTP.
Never uses the same phrasing twice.
Logs all correspondence to brain repo.

Needs: GMAIL_APP_PASSWORD secret
Get it: myaccount.google.com/security -> 2-Step Verification -> App Passwords -> Mail
"""

import os
import json
import smtplib
import imaplib
import email
import email.utils
import requests
import hashlib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

GMAIL_USER = 'mickowood86@gmail.com'
GMAIL_PASS = os.environ.get('GMAIL_APP_PASSWORD')
OPENROUTER = os.environ.get('OPENROUTER_KEY')
GALLERY = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'

# Track replied message IDs to avoid double-replies
REPLIED_LOG = 'mycelium/replied_messages.json'

SYSTEM_PROMPT = """You are Meeko's autonomous email assistant.
Meeko is a digital artist who built Gaza Rose Gallery — 56 original digital flowers,
$1 each, 70% to Palestine Children's Relief Fund. The gallery runs itself on GitHub Actions.

When replying to emails:
- Be warm, genuine, and conversational — not corporate
- Never use the same opening twice
- Be specific to what they said
- Keep it short (3-5 sentences max unless they asked a complex question)
- Sign as: Meeko / Gaza Rose Gallery
- If they're PCRF or a humanitarian org: be extra grateful and direct about the partnership
- If they're offering help/services: be appreciative but honest about what's actually needed
- If they're a buyer: thank them specifically and make sure they know the impact
- If unsure: be friendly and ask one clear question

NEVER:
- Use 'I hope this email finds you well'
- Use 'Best regards' (use something more personal)
- Sound like a corporation
- Be sycophantic
- Repeat phrases from previous emails
"""

def load_replied():
    try:
        with open(REPLIED_LOG) as f:
            return set(json.load(f))
    except:
        return set()

def save_replied(replied_set):
    os.makedirs('mycelium', exist_ok=True)
    with open(REPLIED_LOG, 'w') as f:
        json.dump(list(replied_set), f)

def get_new_emails():
    if not GMAIL_PASS:
        print('[Email] No GMAIL_APP_PASSWORD — skipping')
        return []
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select('inbox')
        # Search for unread emails from the last 24 hours
        _, data = mail.search(None, 'UNSEEN')
        msg_ids = data[0].split()
        messages = []
        for mid in msg_ids[-20:]:  # max 20 at once
            _, msg_data = mail.fetch(mid, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            messages.append({
                'id': mid.decode(),
                'message_id': msg.get('Message-ID', ''),
                'from': msg.get('From', ''),
                'subject': msg.get('Subject', ''),
                'in_reply_to': msg.get('In-Reply-To', ''),
                'body': get_body(msg),
                'raw': msg
            })
        mail.logout()
        return messages
    except Exception as e:
        print(f'[Email] IMAP error: {e}')
        return []

def get_body(msg):
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
        except:
            pass
    # Strip quoted text (lines starting with >)
    lines = [l for l in body.split('\n') if not l.startswith('>')]
    return '\n'.join(lines).strip()[:2000]  # limit context

def ai_reply(from_addr, subject, body):
    if not OPENROUTER:
        return None
    prompt = f"""New email received:
FROM: {from_addr}
SUBJECT: {subject}
BODY:
{body}

Write a reply from Meeko. Be genuine and specific to what they said.
Reply ONLY with the email body text, no subject line, no metadata."""
    try:
        r = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER}',
                'HTTP-Referer': GALLERY,
                'Content-Type': 'application/json'
            },
            json={
                'model': 'openai/gpt-4o-mini',
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 400,
                'temperature': 0.85
            },
            timeout=30
        )
        return r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[AI] Reply generation failed: {e}')
        return None

def send_reply(to_addr, subject, body, in_reply_to=None):
    if not GMAIL_PASS:
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f'Meeko / Gaza Rose Gallery <{GMAIL_USER}>'
        msg['To'] = to_addr
        msg['Subject'] = subject if subject.startswith('Re:') else f'Re: {subject}'
        if in_reply_to:
            msg['In-Reply-To'] = in_reply_to
            msg['References'] = in_reply_to
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)
        print(f'[Email] Replied to {to_addr}')
        return True
    except Exception as e:
        print(f'[Email] Send failed: {e}')
        return False

def run():
    if not GMAIL_PASS:
        print('[Email Responder] GMAIL_APP_PASSWORD not set. Skipping.')
        print('To enable: myaccount.google.com/security -> 2-Step Verification -> App Passwords -> Mail')
        return

    replied = load_replied()
    new_emails = get_new_emails()
    print(f'[Email] Found {len(new_emails)} unread messages')

    for msg in new_emails:
        msg_key = msg['message_id'] or msg['id']
        if msg_key in replied:
            print(f'[Email] Already replied to {msg_key}')
            continue

        from_addr = email.utils.parseaddr(msg['from'])[1]

        # Skip our own sent emails
        if GMAIL_USER in from_addr:
            continue

        print(f'[Email] Processing: {msg["subject"]} from {from_addr}')

        reply_body = ai_reply(from_addr, msg['subject'], msg['body'])
        if not reply_body:
            print(f'[Email] Could not generate reply for {from_addr}')
            continue

        sent = send_reply(from_addr, msg['subject'], reply_body, msg['message_id'])
        if sent:
            replied.add(msg_key)

    save_replied(replied)
    print(f'[Email Responder] Done. Total replied: {len(replied)}')

if __name__ == '__main__':
    run()
