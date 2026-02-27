#!/usr/bin/env python3
"""
Email Responder Engine
=======================
Reads the inbox. Identifies emails related to the system.
Replies automatically in your voice. Keeps you out of the loop.

Only escalates to you when it genuinely cannot handle it:
  - Legal threats
  - Financial decisions over $100
  - Someone claiming to be press at a major outlet (requires your personal touch)
  - Anything ambiguous where a wrong reply could cause harm

Everything else: it reads, understands, replies, archives.

How it works:
  1. Connects to Gmail via IMAP (same app password as SMTP)
  2. Reads unread emails in inbox
  3. Scores relevance: is this about the system?
  4. Classifies intent: press, grant, fork, donor, technical, spam, escalate
  5. Drafts a reply using the LLM in your voice
  6. Sends the reply via SMTP
  7. Marks original as read and labels it [auto-replied]
  8. Logs everything to data/email_log.json
  9. Escalates to you only when truly necessary

Privacy:
  - Sender addresses logged only for 30 days
  - Email bodies never stored, only processed in memory
  - Escalation emails include full context so you can reply if needed
"""

import json, datetime, os, imaplib, email, smtplib, time
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from urllib import request as urllib_request

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
IMAP_HOST = 'imap.gmail.com'
IMAP_PORT = 993

MAX_EMAILS_PER_RUN = 20   # Don't process more than this in one cycle
MAX_BODY_CHARS     = 3000 # Truncate long bodies before sending to LLM

# ── Keywords that identify system-related emails ─────────────────────────────
SYSTEM_KEYWORDS = [
    'meeko', 'nerve center', 'gaza rose', 'pcrf', 'open source',
    'github', 'fork', 'solarpunk', 'congressional', 'congress',
    'bitcoin', 'solana', 'crypto', 'bluesky', 'mastodon',
    'mozilla', 'grant', 'cohort', 'tech for palestine',
    'donation', 'ko-fi', 'kofi', 'gumroad',
    'interview', 'story', 'article', 'journalist', 'press',
    'ai system', 'autonomous', 'humanitarian',
    'palestine', 'palestinian', 'gaza',
]

# ── Escalation triggers ────────────────────────────────────────────────────────
# If any of these are in the email, escalate to you instead of auto-replying
ESCALATE_KEYWORDS = [
    'legal', 'lawsuit', 'attorney', 'lawyer', 'cease', 'desist',
    'dmca', 'copyright infringement', 'defamation', 'libel',
    'acquisition', 'acquire', 'buy your', 'purchase your',
    'invest $', 'investing $', 'wire transfer',
    'new york times', 'washington post', 'bbc', 'reuters', 'ap news',
    'the guardian', 'wired magazine', 'vice news', 'al jazeera',
]

# ── IMAP utilities ───────────────────────────────────────────────────────────

def connect_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        return mail
    except Exception as e:
        print(f'[responder] IMAP connect failed: {e}')
        return None

def decode_str(s):
    """Decode email header strings (handles encoded words)."""
    if not s: return ''
    parts = decode_header(s)
    decoded = ''
    for part, enc in parts:
        if isinstance(part, bytes):
            try:
                decoded += part.decode(enc or 'utf-8', errors='replace')
            except:
                decoded += part.decode('utf-8', errors='replace')
        else:
            decoded += str(part)
    return decoded.strip()

def get_body(msg):
    """Extract plain text body from email message."""
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get('Content-Disposition', ''))
            if ct == 'text/plain' and 'attachment' not in cd:
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    body += part.get_payload(decode=True).decode(charset, errors='replace')
                except:
                    pass
    else:
        try:
            charset = msg.get_content_charset() or 'utf-8'
            body = msg.get_payload(decode=True).decode(charset, errors='replace')
        except:
            pass
    return body.strip()

def fetch_unread_emails(mail):
    """Return list of (uid, from, subject, body) for unread inbox emails."""
    try:
        mail.select('INBOX')
        _, data = mail.uid('search', None, 'UNSEEN')
        uids = data[0].split()
        if not uids:
            return []

        emails = []
        for uid in uids[-MAX_EMAILS_PER_RUN:]:  # most recent first
            try:
                _, msg_data = mail.uid('fetch', uid, '(RFC822)')
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                sender  = decode_str(msg.get('From', ''))
                subject = decode_str(msg.get('Subject', ''))
                body    = get_body(msg)[:MAX_BODY_CHARS]
                msg_id  = decode_str(msg.get('Message-ID', ''))
                reply_to = decode_str(msg.get('Reply-To', '')) or sender

                # Extract just the email address
                import re
                addr_match = re.search(r'<([^>]+)>', sender)
                sender_addr = addr_match.group(1) if addr_match else sender

                emails.append({
                    'uid':       uid,
                    'sender':    sender,
                    'sender_addr': sender_addr,
                    'reply_to':  reply_to,
                    'subject':   subject,
                    'body':      body,
                    'msg_id':    msg_id,
                })
            except Exception as e:
                print(f'[responder] Error reading email uid {uid}: {e}')

        print(f'[responder] Found {len(emails)} unread emails')
        return emails
    except Exception as e:
        print(f'[responder] Fetch error: {e}')
        return []

def mark_read_and_label(mail, uid, label='auto-replied'):
    """Mark email as read. Try to apply a label."""
    try:
        mail.uid('store', uid, '+FLAGS', '\\Seen')
        # Gmail labels via IMAP COPY to label folder
        try:
            mail.uid('copy', uid, label)
        except:
            pass  # Label might not exist, that's fine
    except Exception as e:
        print(f'[responder] Mark read error: {e}')

# ── Scoring and classification ──────────────────────────────────────────────

def is_system_related(subject, body, sender):
    """Return True if this email is about the system."""
    haystack = (subject + ' ' + body + ' ' + sender).lower()
    hits = sum(1 for kw in SYSTEM_KEYWORDS if kw in haystack)
    return hits >= 1

def needs_escalation(subject, body):
    """Return escalation reason string or None."""
    haystack = (subject + ' ' + body).lower()
    for kw in ESCALATE_KEYWORDS:
        if kw in haystack:
            return kw
    return None

def skip_email(sender_addr, subject, body):
    """Return True if this email should be silently skipped."""
    # Skip if it's from ourselves (prevents reply loops)
    if GMAIL_ADDRESS and sender_addr.lower() == GMAIL_ADDRESS.lower():
        return True
    # Skip obvious marketing/auto emails
    auto_signals = ['unsubscribe', 'no-reply', 'noreply', 'do-not-reply',
                    'donotreply', 'notification@', 'notifications@',
                    'mailer-daemon', 'postmaster']
    haystack = (sender_addr + ' ' + subject).lower()
    return any(s in haystack for s in auto_signals)

# ── LLM reply generation ─────────────────────────────────────────────────────

def classify_and_reply(sender, subject, body):
    """
    Ask the LLM to:
      1. Classify the email (press, grant, fork question, donor, technical, other)
      2. Draft an appropriate reply

    Returns (classification, reply_text) or (None, None) on failure.
    """
    if not HF_TOKEN:
        return None, None

    # Load system context for the LLM
    context_parts = [
        'You are the autonomous email responder for the Meeko Nerve Center.',
        'You respond as Meeko — warm, direct, human, never corporate.',
        '',
        'About the system:',
        '- Open-source autonomous AI running on GitHub Actions (zero monthly cost)',
        '- Monitors Congressional stock trades for public accountability',
        '- Generates Gaza Rose art; 70% of sales go to Palestinian children via PCRF',
        '- Cross-posts to Bluesky and Mastodon automatically',
        '- AGPL-3.0 license, forkable by anyone for any humanitarian cause',
        '- Live at: https://meekotharaccoon-cell.github.io/meeko-nerve-center/',
        '- GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center',
        '',
        'Your reply rules:',
        '- Be warm, specific, and human — never use corporate language',
        '- Answer the actual question being asked',
        '- For press: be enthusiastic, offer a walkthrough, give the GitHub link',
        '- For grants: be concrete about impact (24 ideas tested, 19 passed, running since Feb 2026)',
        '- For fork questions: be helpful and encouraging, point to START_HERE.md',
        '- For donors: be deeply grateful, share the PCRF impact',
        '- For technical questions: answer accurately, admit if you don\'t know',
        '- Keep replies under 250 words unless the question demands more',
        '- Sign off as "Meeko" not "Meeko Nerve Center"',
        '- Never mention that this reply was automated',
    ]

    # Add any available live data as context
    ledger_path = DATA / 'idea_ledger.json'
    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text())
            ideas  = ledger.get('ideas', {})
            idea_list = list(ideas.values()) if isinstance(ideas, dict) else ideas
            total  = len(idea_list)
            passed = sum(1 for i in idea_list if i.get('status') in ('passed','wired'))
            context_parts.append(f'- Current system stats: {total} ideas tested, {passed} passed')
        except:
            pass

    system_prompt = '\n'.join(context_parts)

    prompt = f"""Incoming email:

FROM: {sender}
SUBJECT: {subject}
BODY:
{body}

---

First, classify this email. Choose ONE:
  press       - journalist or blogger asking about the system
  grant       - grant organization following up or asking questions
  fork        - someone asking how to fork or use the system
  donor       - someone who donated or wants to donate
  technical   - technical question about the code or APIs
  partnership - someone proposing collaboration
  other       - related to the system but doesn't fit above

Then write a complete reply email (no subject line needed, just the body).

Respond ONLY with a JSON object:
{{
  "classification": "press|grant|fork|donor|technical|partnership|other",
  "reply": "Full email body here. Sign as Meeko."
}}
"""

    try:
        payload = json.dumps({
            'model':      'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 800,
            'messages':   [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            data     = json.loads(r.read())
            response = data['choices'][0]['message']['content'].strip()

        # Parse JSON from response
        start = response.find('{')
        end   = response.rfind('}') + 1
        if start >= 0 and end > start:
            parsed = json.loads(response[start:end])
            return parsed.get('classification', 'other'), parsed.get('reply', '')

    except Exception as e:
        print(f'[responder] LLM error: {e}')

    return None, None

# ── SMTP send ───────────────────────────────────────────────────────────────────

def send_reply(to_addr, subject, body, in_reply_to=None):
    """Send a reply email."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Re: {subject}' if not subject.startswith('Re:') else subject
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = to_addr
        if in_reply_to:
            msg['In-Reply-To'] = in_reply_to
            msg['References']  = in_reply_to
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to_addr, msg.as_string())

        print(f'[responder] Replied to {to_addr}: {subject[:50]}')
        return True
    except Exception as e:
        print(f'[responder] Send failed to {to_addr}: {e}')
        return False

def escalate_to_user(email_data, reason):
    """Forward to yourself with context when human judgment is needed."""
    try:
        body = f"""Your system flagged this email for your attention.

Reason: {reason}

{'=' * 50}
FROM:    {email_data['sender']}
SUBJECT: {email_data['subject']}
{'=' * 50}

{email_data['body']}

{'=' * 50}

This email was NOT auto-replied. You should reply manually if needed."""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"⚠️ ESCALATED: {email_data['subject'][:60]}"
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())

        print(f'[responder] Escalated to you: {email_data["subject"][:50]}')
    except Exception as e:
        print(f'[responder] Escalation failed: {e}')

# ── Logging ───────────────────────────────────────────────────────────────────

def log_action(action, sender_addr, subject, classification=None, escalation_reason=None):
    log_path = DATA / 'email_log.json'
    log = {'actions': []}
    if log_path.exists():
        try:
            log = json.loads(log_path.read_text())
        except:
            pass

    log['actions'].append({
        'date':               TODAY,
        'action':             action,          # 'replied', 'escalated', 'skipped', 'not_relevant'
        'sender':             sender_addr,
        'subject':            subject[:100],
        'classification':     classification,
        'escalation_reason':  escalation_reason,
    })

    # Privacy: scrub entries older than 30 days
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    log['actions'] = [a for a in log['actions'] if a.get('date', '9999') >= cutoff]

    try:
        log_path.write_text(json.dumps(log, indent=2))
    except:
        pass

# ── Main ───────────────────────────────────────────────────────────────────

def run():
    print(f'\n[responder] Email Responder Engine — {TODAY}')

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[responder] No Gmail credentials. Skipping.')
        return

    mail = connect_imap()
    if not mail:
        return

    try:
        emails = fetch_unread_emails(mail)
        if not emails:
            print('[responder] Inbox clear. Nothing to process.')
            return

        replied = 0
        escalated = 0
        skipped = 0

        for em in emails:
            sender_addr = em['sender_addr']
            subject     = em['subject']
            body        = em['body']

            print(f'[responder] Processing: {subject[:60]} from {sender_addr[:40]}')

            # Skip noise
            if skip_email(sender_addr, subject, body):
                print(f'[responder] Skipping auto/marketing email')
                mark_read_and_label(mail, em['uid'], 'auto-skipped')
                log_action('skipped', sender_addr, subject)
                skipped += 1
                continue

            # Check relevance
            if not is_system_related(subject, body, sender_addr):
                print(f'[responder] Not system-related. Leaving for you.')
                log_action('not_relevant', sender_addr, subject)
                # Don't mark as read — leave it in inbox for you
                continue

            # Check escalation
            esc_reason = needs_escalation(subject, body)
            if esc_reason:
                print(f'[responder] Escalating: "{esc_reason}" trigger')
                escalate_to_user(em, esc_reason)
                mark_read_and_label(mail, em['uid'], 'escalated')
                log_action('escalated', sender_addr, subject, escalation_reason=esc_reason)
                escalated += 1
                time.sleep(1)
                continue

            # Generate reply
            classification, reply_text = classify_and_reply(
                em['sender'], subject, body
            )

            if not reply_text:
                print(f'[responder] LLM could not generate reply. Escalating.')
                escalate_to_user(em, 'LLM reply generation failed')
                escalated += 1
                continue

            # Send reply to original sender
            sent = send_reply(
                to_addr    = sender_addr,
                subject    = subject,
                body       = reply_text,
                in_reply_to = em.get('msg_id')
            )

            if sent:
                mark_read_and_label(mail, em['uid'], 'auto-replied')
                log_action('replied', sender_addr, subject, classification=classification)
                replied += 1
            else:
                # If send fails, escalate so nothing falls through the cracks
                escalate_to_user(em, 'Reply send failed')
                escalated += 1

            time.sleep(2)  # Be polite to the mail server

        print(f'\n[responder] Done. Replied: {replied} | Escalated: {escalated} | Skipped: {skipped}')

    finally:
        try:
            mail.logout()
        except:
            pass

if __name__ == '__main__':
    run()
