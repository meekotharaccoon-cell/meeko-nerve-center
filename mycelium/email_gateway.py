#!/usr/bin/env python3
"""
Email Gateway v3 — STRICT INBOUND-ONLY
=========================================
COMPLETE REWRITE. Previous versions caused catastrophic spam.

THE ONLY RULES:

  1. NEVER auto-send email to anyone. Ever. Not newsletters,
     not briefings, not grant updates, not crypto prices,
     not anything. Email only goes OUT as a direct REPLY
     to a real human who emailed IN first.

  2. Only reply if the human's email clearly asks about:
     - SolarPunk / the system itself
     - GitHub / forking / running the system
     - Palestinian solidarity / PCRF / Gaza Rose art
     - Grants the system is applying for
     - Congressional accountability data
     - Crypto signals from the system
     Otherwise: read, log, ignore.

  3. Never reply to automated senders. Ever.
     (GitHub notifications, Stripe, Mailchimp, anything with
      noreply, notifications@, mailer-daemon, etc.)

  4. Never reply to bounce messages or auto-responders.
     If we get a "mailbox doesn't exist" or "Thanks for reaching out"
     auto-reply: mark read, log it, do NOT reply.

  5. Each email address can only receive ONE reply per 48 hours.
     Deduplication prevents loops.

  6. Meeko's own email (GMAIL_ADDRESS) is never replied to
     by this system. Self-emails go to unified_briefing.py only.

  7. All email sending uses ONLY smtp.gmail.com with explicit
     credentials. No third-party services. No bulk APIs.

Everything else — crypto price updates, morning briefings, newsletter
blasts, outreach campaigns — has been moved out of this engine.
This engine does ONE thing: respond to humans who ask about SolarPunk.
"""

import json, datetime, os, smtplib, imaplib, email as email_lib
import re, hashlib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'
FORK_URL = f'{REPO_URL}/fork'

# ── AUTOMATED SENDER DETECTION ──────────────────────────────────────────────

AUTO_SENDER_DOMAINS = {
    'github.com', 'githubusercontent.com', 'noreply.github.com',
    'stripe.com', 'notifications.stripe.com',
    'polymarket.com', 'noreply.polymarket.com',
    'apollo.io', 'mail.apollo.io',
    'flatlogic.com',
    'mailchimp.com', 'list-manage.com',
    'sendgrid.net', 'sendgrid.com',
    'mailgun.org', 'mailgun.net',
    'amazonses.com', 'amazonaws.com',
    'postmarkapp.com',
    'sparkpostmail.com',
    'hubspot.com', 'hs-analytics.net',
    'salesforce.com', 'pardot.com',
    'marketo.com',
    'klaviyo.com',
    'constantcontact.com',
    'campaignmonitor.com',
    'mailerlite.com',
    'convertkit.com',
    'drip.com',
    'intercom.io', 'intercom.com',
    'zendesk.com',
    'freshdesk.com',
    'helpscout.com',
    'notion.so',
    'slack.com',
    'discord.com',
    'twitter.com', 'x.com',
    'facebook.com', 'meta.com',
    'linkedin.com',
    'google.com', 'googlemail.com',
    'accounts.google.com',
    'paypal.com',
    'coinbase.com',
    'binance.com',
    'kraken.com',
    'gumroad.com',
    'substack.com',
    'patreon.com',
    'wordpress.com',
    'heroku.com',
    'netlify.com',
    'vercel.com',
    'cloudflare.com',
    'namecheap.com',
    'godaddy.com',
}

AUTO_SENDER_PREFIXES = [
    'noreply@', 'no-reply@', 'donotreply@', 'do-not-reply@',
    'notifications@', 'notify@', 'alert@', 'alerts@',
    'mailer@', 'mailer-daemon@', 'bounce@', 'bounces@',
    'postmaster@', 'automailer@', 'auto@', 'automated@',
    'robot@', 'bot@', 'system@', 'daemon@',
    'support@', 'help@', 'hello@', 'hi@', 'team@',
    'info@', 'contact@', 'newsletter@', 'news@',
    'updates@', 'update@', 'digest@',
    'feedback@', 'surveys@', 'reply@',
    'marketing@', 'promo@', 'promotions@',
    'billing@', 'payments@', 'invoices@',
    'security@', 'account@', 'accounts@',
    'admin@', 'administrator@',
    'webmaster@',
]

# Subject patterns that indicate automated/bulk email
AUTO_SUBJECT_PATTERNS = [
    # GitHub patterns
    'run failed:', 'run succeeded:', 'run cancelled:', 'run skipped:',
    '[meekotharaccoon-cell/', 'workflow run', 'github actions',
    'pull request', 'issue opened', 'issue closed',
    # Bounce/auto-reply patterns
    'delivery status notification',
    'undeliverable',
    'mail delivery failed',
    'mailbox does not exist',
    'mailbox not found',
    'address not found',
    'user unknown',
    'no such user',
    'delivery failure',
    'automatic reply',
    'auto reply',
    'auto-reply',
    'out of office',
    'on vacation',
    'away from the office',
    'i am out',
    'thank you for contacting',
    'thanks for reaching out',
    'thanks for contacting',
    'thank you for your email',
    'we received your',
    'we got your',
    'ticket #',
    'case #',
    'reference #',
    'your request',
    'we will be in touch',
    'will get back to you',
    'your message has been received',
    # Marketing patterns
    'unsubscribe', 'manage preferences', 'email preferences',
    'view in browser', 'having trouble viewing',
    'you received this email because',
    'you are receiving this',
    'to stop receiving',
    # Encoded github subjects
    '=?utf-8?q?[meekotharaccoon',
    '=?utf-8?b?',  # base64 encoded subjects from bulk mail
]

# Body patterns that indicate auto-responder
AUTO_BODY_PATTERNS = [
    'this is an automated response',
    'this is an automatic reply',
    'this message was sent automatically',
    'please do not reply to this email',
    'do not reply to this message',
    'this email was sent from an unmonitored address',
    'this inbox is not monitored',
    'this mailbox is not monitored',
    'this message is auto-generated',
    'if you did not request this',
    'you are receiving this because you',
]

# Topics that qualify a human email for a response
RESPONSE_TOPICS = [
    # System-related
    'solarpunk', 'solar punk', 'nerve center', 'meeko',
    'fork', 'github', 'git hub', 'repository', 'repo',
    'how does this work', 'how does it work', 'what is this',
    'tell me more', 'interested in', 'want to know',
    # Mission-related
    'palestine', 'palestinian', 'pcrf', 'gaza', 'humanitarian',
    'congress', 'congressional', 'accountability', 'stock act',
    'trade', 'insider trading',
    # System features
    'crypto', 'bitcoin', 'signal', 'signal tracker',
    'art', 'gaza rose', 'art generator',
    'grant', 'funding', 'application',
    # Meta
    'autonomous', 'ai system', 'self-building', 'self building',
    'open source', 'agpl',
]

def is_automated(from_email: str, from_raw: str, subject: str, body: str) -> tuple[bool, str]:
    """Returns (is_automated, reason). Any True means do not reply."""
    e = from_email.lower().strip()
    s = subject.lower()
    b = body.lower()[:2000]

    # Self-email
    if GMAIL_ADDRESS and GMAIL_ADDRESS.lower() in e:
        return True, 'self-email'

    # Domain blocklist
    for domain in AUTO_SENDER_DOMAINS:
        if e.endswith(f'@{domain}') or e.endswith(f'.{domain}'):
            return True, f'blocked domain: {domain}'

    # Prefix blocklist
    local = e.split('@')[0] if '@' in e else e
    for prefix in AUTO_SENDER_PREFIXES:
        if local == prefix.rstrip('@') or e.startswith(prefix):
            return True, f'auto prefix: {prefix}'

    # Subject patterns
    for pattern in AUTO_SUBJECT_PATTERNS:
        if pattern in s:
            return True, f'auto subject: {pattern[:30]}'

    # Body patterns (bounces / auto-replies)
    for pattern in AUTO_BODY_PATTERNS:
        if pattern in b:
            return True, f'auto body: {pattern[:30]}'

    # Encoded subjects (GitHub's =?utf-8?q? notifications)
    if s.startswith('=?utf') and ('run' in s or 'meekotharaccoon' in s):
        return True, 'encoded github notification'

    return False, ''

def is_on_topic(subject: str, body: str) -> bool:
    """Only reply if the human is clearly asking about our system/mission."""
    text = (subject + ' ' + body).lower()
    return any(topic in text for topic in RESPONSE_TOPICS)

def get_reply_dedup_key(from_email: str) -> str:
    return hashlib.md5(from_email.lower().encode()).hexdigest()[:12]

def was_replied_recently(from_email: str) -> bool:
    """Prevent replying to same address more than once per 48 hours."""
    p = DATA / 'email_reply_dedup.json'
    try:
        if p.exists():
            dedup = json.loads(p.read_text())
        else:
            dedup = {}
        key  = get_reply_dedup_key(from_email)
        last = dedup.get(key)
        if not last:
            return False
        last_dt = datetime.datetime.fromisoformat(last)
        age_h   = (datetime.datetime.utcnow() - last_dt).total_seconds() / 3600
        return age_h < 48
    except:
        return False

def mark_replied(from_email: str):
    p = DATA / 'email_reply_dedup.json'
    try:
        dedup = json.loads(p.read_text()) if p.exists() else {}
        key   = get_reply_dedup_key(from_email)
        dedup[key] = datetime.datetime.utcnow().isoformat()
        # Prune old entries (>7 days)
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        dedup  = {k: v for k, v in dedup.items()
                  if datetime.datetime.fromisoformat(v) > cutoff}
        p.write_text(json.dumps(dedup, indent=2))
    except:
        pass

def build_reply(from_email: str, subject: str, body: str) -> str:
    """Generate a focused reply about SolarPunk/the system."""
    # Try LLM first
    if HF_TOKEN:
        try:
            prompt = f"""You are Meeko Nerve Center, a SolarPunk autonomous AI system
for Palestinian solidarity and congressional accountability.

Someone emailed you:
Subject: {subject[:200]}
Body: {body[:600]}

Write a genuine, helpful reply. Rules:
- Stay focused on what they asked about the system
- If they want to fork/run it, give them the key info:
  Repo: {REPO_URL}
  Fork: {FORK_URL}
  Needs: HF_TOKEN (free at huggingface.co) + Gmail app password
- Mention PCRF / Gaza Rose art if relevant
- Keep it under 200 words
- End with: Free Palestine. 🌹
- Sign as: Meeko Nerve Center
- Do NOT mention email addresses, secrets, or internal system details

Reply only with the email body text."""
            payload = json.dumps({
                'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
                'max_tokens': 400,
                'messages': [
                    {'role': 'system', 'content': 'You are Meeko, a SolarPunk AI. Direct, warm, genuine.'},
                    {'role': 'user', 'content': prompt}
                ]
            }).encode()
            req = urllib_request.Request(
                'https://router.huggingface.co/v1/chat/completions',
                data=payload,
                headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
            )
            with urllib_request.urlopen(req, timeout=45) as r:
                return json.loads(r.read())['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f'[gateway] LLM error: {e}')

    # Fallback static reply
    return f"""Thanks for reaching out about Meeko Nerve Center. 🌸

This is a self-evolving SolarPunk AI system for:
  • Congressional accountability (STOCK Act trade tracking)
  • Palestinian solidarity (Gaza Rose art → PCRF donations)
  • $0/month autonomous infrastructure

To run your own:
  Fork: {FORK_URL}
  Add 3 secrets: HF_TOKEN, GMAIL_ADDRESS, GMAIL_APP_PASSWORD
  Enable Actions → run MASTER CONTROLLER

{REPO_URL}

Free Palestine. 🌹
— Meeko Nerve Center"""

def send_reply(to_email: str, orig_subject: str, body: str) -> bool:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[gateway] No credentials — cannot send')
        return False
    try:
        subject = orig_subject if orig_subject.startswith('Re:') else f'Re: {orig_subject}'
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko Nerve Center 🌸 <{GMAIL_ADDRESS}>'
        msg['To']      = to_email
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo()
            s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f'[gateway] SMTP error: {e}')
        return False

def log(entry: dict):
    p = DATA / 'email_gateway_log.json'
    try:
        log_data = json.loads(p.read_text()) if p.exists() else {'interactions': []}
        log_data.setdefault('interactions', []).append(entry)
        log_data['interactions'] = log_data['interactions'][-500:]
        p.write_text(json.dumps(log_data, indent=2))
    except:
        pass

def decode_header_value(value: str) -> str:
    try:
        from email.header import decode_header as _dh
        parts = _dh(value)
        return ''.join(
            p.decode(enc or 'utf-8', errors='replace') if isinstance(p, bytes) else p
            for p, enc in parts
        )
    except:
        return value

def check_inbox() -> list[dict]:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return []
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select('INBOX')
        _, data = mail.search(None, 'UNSEEN')
        ids = data[0].split()
        messages = []
        for eid in ids[-30:]:  # Max 30 unread
            _, msg_data = mail.fetch(eid, '(RFC822)')
            if not msg_data or not msg_data[0]: continue
            raw = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw)
            # Always mark read regardless of what we do with it
            mail.store(eid, '+FLAGS', '\\Seen')

            subject  = decode_header_value(msg.get('Subject', ''))
            from_raw = msg.get('From', '')
            match    = re.search(r'[\w.+\-]+@[\w.\-]+\.[\w.]+', from_raw)
            from_email = match.group(0) if match else from_raw

            # Extract body
            body = ''
            if msg.is_multipart():
                for part in msg.walk():
                    ct = part.get_content_type()
                    if ct == 'text/plain':
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        except: pass
                        break
            else:
                try: body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                except: pass

            messages.append({
                'from_email': from_email,
                'from_raw': from_raw,
                'subject': subject,
                'body': body[:3000],
            })
        mail.close()
        mail.logout()
        return messages
    except Exception as e:
        print(f'[gateway] IMAP error: {e}')
        return []

def run():
    print(f'\n[gateway] 📬 Email Gateway v3 — STRICT INBOUND-ONLY — {TODAY}')
    DATA.mkdir(parents=True, exist_ok=True)

    messages = check_inbox()
    print(f'[gateway] Unread emails: {len(messages)}')

    replied = 0
    ignored_auto = 0
    ignored_offtopic = 0
    ignored_dedup = 0

    for msg in messages:
        from_email = msg['from_email']
        subject    = msg['subject']
        body       = msg['body']

        # Gate 1: Automated sender?
        auto, reason = is_automated(from_email, msg['from_raw'], subject, body)
        if auto:
            ignored_auto += 1
            log({'date': TODAY, 'from': from_email[:40], 'subject': subject[:60],
                 'action': 'ignored_automated', 'reason': reason})
            continue

        # Gate 2: On-topic (asking about the system)?
        if not is_on_topic(subject, body):
            ignored_offtopic += 1
            log({'date': TODAY, 'from': from_email[:40], 'subject': subject[:60],
                 'action': 'ignored_offtopic'})
            print(f'[gateway] Off-topic, skipping: {from_email[:40]} | {subject[:50]}')
            continue

        # Gate 3: Already replied recently?
        if was_replied_recently(from_email):
            ignored_dedup += 1
            log({'date': TODAY, 'from': from_email[:40], 'subject': subject[:60],
                 'action': 'ignored_dedup'})
            print(f'[gateway] Already replied recently, skipping: {from_email[:40]}')
            continue

        # All gates passed — this is a real human asking about the system
        print(f'[gateway] ✨ Real human, on-topic: {from_email[:40]}')
        print(f'[gateway]   Subject: {subject[:60]}')

        reply = build_reply(from_email, subject, body)
        ok    = send_reply(from_email, subject, reply)

        if ok:
            mark_replied(from_email)
            replied += 1
            log({'date': TODAY, 'from': from_email[:40], 'subject': subject[:60],
                 'action': 'replied'})
            print(f'[gateway] ✅ Replied to {from_email[:40]}')
        else:
            log({'date': TODAY, 'from': from_email[:40], 'subject': subject[:60],
                 'action': 'reply_failed'})

    print(f'[gateway] Done.')
    print(f'[gateway]   Replied: {replied}')
    print(f'[gateway]   Ignored (automated): {ignored_auto}')
    print(f'[gateway]   Ignored (off-topic): {ignored_offtopic}')
    print(f'[gateway]   Ignored (dedup): {ignored_dedup}')

if __name__ == '__main__':
    run()
