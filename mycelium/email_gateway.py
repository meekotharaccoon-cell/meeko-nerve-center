#!/usr/bin/env python3
"""
Email Gateway Engine — v2 (FIXED)
====================================
BIG FIX: The previous version was processing every GitHub notification email
(workflow success/fail alerts) as if they were real user messages. This caused:
  - Deploy guides sent to GitHub notification emails (DEPLOY in subject)
  - AI responses sent to workflow failure alerts
  - Replies to spam (stripe, apollo, polymarket)
  - Each reply triggered another GitHub notification -> infinite loop
  - Hundreds of duplicate emails per day

Fix: Strict blocklist of automated senders. Only real humans get responses.
Automated notification emails are silently counted and discarded.

Golden rule: If it's not from a real human, don't touch it.
"""

import json, datetime, os, smtplib, imaplib, email as email_lib, re
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

REPO_URL   = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'
FORK_URL   = f'{REPO_URL}/fork'

# ── AUTOMATED SENDER BLOCKLIST ─────────────────────────────────────────────
# These domains/addresses send automated emails. NEVER reply to them.
# This was the root cause of the email spam loop.
BLOCKED_DOMAINS = [
    'github.com',          # workflow notifications - THE BIG ONE
    'githubusercontent.com',
    'stripe.com',
    'polymarket.com',
    'apollo.io',
    'mail.apollo.io',
    'flatlogic.com',
    'noreply.github.com',
    'notifications.github.com',
    'sendgrid.net',
    'mailchimp.com',
    'amazonses.com',
    'mailgun.org',
    'postmarkapp.com',
    'hubspot.com',
    'salesforce.com',
    'marketo.com',
    'klaviyo.com',
]

BLOCKED_PREFIXES = [
    'noreply@', 'no-reply@', 'donotreply@', 'do-not-reply@',
    'notifications@', 'notify@', 'mailer@', 'bounce@', 'postmaster@',
    'support@github', 'info@github', 'security@github',
    'daemon@', 'mailer-daemon@', 'automailer@',
]

BLOCKED_SUBJECT_PATTERNS = [
    'run failed:', 'run succeeded:', 'run cancelled:', 'run skipped:',
    '[meekotharaccoon-cell/', 'github actions', 'workflow run',
    'unsubscribe', 'email preferences', 'manage notifications',
]

def is_automated_sender(sender_email, from_raw, subject):
    """Return True if this is an automated/notification email we should ignore."""
    email_lower   = sender_email.lower()
    from_lower    = from_raw.lower()
    subject_lower = subject.lower()

    # Check blocked domains
    for domain in BLOCKED_DOMAINS:
        if f'@{domain}' in email_lower or f'.{domain}' in email_lower:
            return True

    # Check blocked prefixes
    for prefix in BLOCKED_PREFIXES:
        if email_lower.startswith(prefix):
            return True

    # Check subject patterns (catches GitHub notification subjects)
    for pattern in BLOCKED_SUBJECT_PATTERNS:
        if pattern in subject_lower:
            return True

    # GitHub's encoded subject lines (=?utf-8?q?...)
    if '=?utf-8?q?' in subject and 'meekotharaccoon-cell' in from_lower + subject_lower:
        return True

    return False

# ── EMAIL CONTENT ──────────────────────────────────────────────────────────
FORK_RESPONSE = """Welcome to the SolarPunk network. 🌱

You asked for your own autonomous AI system.
Here's how to have it running in 10 minutes, free, forever.

━━ STEP 1: FORK ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Go here and click Fork:
{fork_url}

━━ STEP 2: ADD 3 SECRETS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Your forked repo → Settings → Secrets and variables → Actions)

HF_TOKEN — free at huggingface.co/settings/tokens
GMAIL_ADDRESS — your Gmail address
GMAIL_APP_PASSWORD — Google Account → Security → App Passwords

━━ STEP 3: ENABLE ACTIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Actions tab → "I understand my workflows" → Enable)

━━ STEP 4: RUN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Actions → MASTER CONTROLLER → Run workflow)
Your system starts building itself immediately.

That's it. 10 minutes. Free forever.

{repo_url}

Free Palestine. 🌹
— Meeko Nerve Center / SolarPunk
"""

HELP_RESPONSE = """🌸 Meeko Nerve Center — here's what I can do:

Send an email to {address} with:
  Subject: FORK ME   → Get your own autonomous AI system (free)
  Subject: SIGNALS   → Today's crypto signals
  Subject: CONGRESS  → Latest congressional trade flagged
  Subject: SUBSCRIBE → Join the weekly newsletter
  Subject: HELP      → This message

I track congressional trades, generate Gaza Rose art for PCRF,
build my own new capabilities every day, and run on $0/month.
Fully open source (AGPL-3.0).

{repo_url}

Free Palestine. 🌹
"""

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def get_todays_signals():
    signals = load(DATA / 'investment_signals.json', {}).get('signals', [])
    if not signals:
        signals = load(DATA / 'crypto_signals_queue.json', [])
    if not signals: return 'No signals generated yet today. Check back tomorrow.'
    lines = ["TODAY'S TOP SIGNALS", '=' * 40, '']
    for s in signals[:3]:
        lines += [
            f'{s.get("symbol", s.get("coin","?"))} — confidence: {s.get("confidence","?")}',
            f'  Reasons: {", ".join(s.get("reasons", [s.get("rationale","?")][:1]))}',
            f'  Max position: {s.get("max_position_pct","?")}'  ,
            f'  Stop loss: {s.get("stop_loss_pct","?")}',
            '',
        ]
    lines.append('Not financial advice. Mathematical signals. DYOR.')
    lines.append(f'\n{REPO_URL}')
    return '\n'.join(lines)

def get_latest_trade():
    congress = load(DATA / 'congress.json')
    trades = congress if isinstance(congress, list) else congress.get('trades', [])
    if not trades: return 'No recent congressional trades tracked yet.'
    t = trades[0]
    return (
        f'CONGRESSIONAL TRADE FLAGGED\n{"="*40}\n\n'
        f'{t.get("representative", t.get("senator","Unknown"))} '
        f'traded {t.get("ticker","?")} '
        f'({t.get("amount", t.get("range","?"))}) '
        f'on {t.get("transaction_date", t.get("date","?"))}.\n\n'
        f'Public record. STOCK Act disclosure.\n'
        f'Tracked by: {REPO_URL}\n'
    )

def generate_ai_response(subject, body_text):
    if not HF_TOKEN: return None
    prompt = f"""You are Meeko Nerve Center, an autonomous AI for Palestinian solidarity
and congressional accountability. You just received this email from a real person:

Subject: {subject[:200]}
Body: {body_text[:500]}

Respond genuinely. Be helpful. Be human. Be SolarPunk.
If journalist: give them a story angle.
If developer: give them a technical hook.
If supporter: give them warmth.
Under 250 words. Sign as: Meeko Nerve Center
Include: {REPO_URL}"""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 350,
            'messages': [
                {'role': 'system', 'content': 'You are Meeko, a SolarPunk AI. Genuine. Direct. Good.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except:
        return None

def send_reply(to_email, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False
    # Never reply to automated senders even if somehow they got past the filter
    if is_automated_sender(to_email, to_email, subject):
        print(f'[gateway] ⛔ Blocked auto-reply to: {to_email[:40]}')
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Re: {subject}' if not subject.startswith('Re:') else subject
        msg['From']    = f'Meeko Nerve Center 🌸 <{GMAIL_ADDRESS}>'
        msg['To']      = to_email
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f'[gateway] Send error: {e}')
        return False

def add_to_newsletter(email_addr):
    p = DATA / 'newsletter_subscribers.json'
    subs = load(p, {'subscribers': [], 'unsubscribed': []})
    if not any(s.get('email') == email_addr for s in subs.get('subscribers', [])):
        subs.setdefault('subscribers', []).append({
            'email': email_addr, 'date': TODAY, 'source': 'email_gateway'
        })
        try: p.write_text(json.dumps(subs, indent=2))
        except: pass
        return True
    return False

def check_inbox():
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[gateway] No credentials — skipping inbox check')
        return [], 0
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select('INBOX')
        _, data = mail.search(None, 'UNSEEN')
        email_ids = data[0].split()

        real_messages = []
        automated_count = 0

        for eid in email_ids[-20:]:  # Check up to 20 unread
            _, msg_data = mail.fetch(eid, '(RFC822)')
            raw = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw)

            subject  = msg.get('Subject', '')
            from_raw = msg.get('From', '')

            # Decode encoded subjects like =?utf-8?q?...
            try:
                from email.header import decode_header
                parts = decode_header(subject)
                subject = ''.join(
                    p.decode(enc or 'utf-8') if isinstance(p, bytes) else p
                    for p, enc in parts
                )
            except:
                pass

            email_match = re.search(r'[\w.+-]+@[\w.-]+\.[\w.]+', from_raw)
            sender_email = email_match.group(0) if email_match else from_raw

            # Mark as read regardless
            mail.store(eid, '+FLAGS', '\\Seen')

            # CRITICAL: Skip self-emails
            if GMAIL_ADDRESS.lower() in sender_email.lower():
                continue

            # CRITICAL: Skip all automated senders
            if is_automated_sender(sender_email, from_raw, subject):
                automated_count += 1
                continue

            # Extract body for real human emails
            body = ''
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        try: body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        except: pass
                        break
            else:
                try: body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                except: pass

            real_messages.append({
                'id': eid, 'subject': subject,
                'from': sender_email, 'from_raw': from_raw,
                'body': body[:2000],
            })

        mail.close()
        mail.logout()
        print(f'[gateway] Inbox: {len(real_messages)} real, {automated_count} automated (ignored)')
        return real_messages, automated_count
    except Exception as e:
        print(f'[gateway] IMAP error: {e}')
        return [], 0

def log_interaction(sender, subject, action):
    p = DATA / 'email_gateway_log.json'
    log = load(p, {'interactions': []})
    log.setdefault('interactions', []).append({
        'date': TODAY, 'from': sender[:40], 'subject': subject[:80], 'action': action
    })
    log['interactions'] = log['interactions'][-200:]
    try: p.write_text(json.dumps(log, indent=2))
    except: pass

def route_email(msg):
    subject  = msg['subject'].upper()
    sender   = msg['from']
    body     = msg['body']
    sub_orig = msg['subject']

    print(f'[gateway] 📨 Routing: "{sub_orig[:50]}" from {sender[:40]}')

    if 'FORK ME' in subject or 'FORK' in subject:
        reply  = FORK_RESPONSE.format(fork_url=FORK_URL, repo_url=REPO_URL)
        action = 'fork_guide_sent'

    elif 'SIGNAL' in subject:
        reply  = get_todays_signals()
        action = 'signals_sent'

    elif any(w in subject for w in ['CONGRESS', 'ACCOUNTABILITY', 'TRADE']):
        reply  = get_latest_trade()
        action = 'trade_sent'

    elif any(w in subject for w in ['SUBSCRIBE', 'JOIN', 'NEWSLETTER']):
        added  = add_to_newsletter(sender)
        reply  = f"""You're {'now subscribed to' if added else 'already on'} the Meeko Nerve Center newsletter. 🌸

Every Sunday: congressional hits, Gaza Rose drops, PCRF impact numbers, system evolution.

While you wait: {REPO_URL}\n\nFree Palestine. 🌹"""
        action = 'subscribed'

    elif any(w in subject for w in ['HELP', 'WHAT', 'HOW']):
        reply  = HELP_RESPONSE.format(address=GMAIL_ADDRESS, repo_url=REPO_URL)
        action = 'help_sent'

    elif 'UNSUBSCRIBE' in subject:
        p    = DATA / 'newsletter_subscribers.json'
        subs = load(p, {'unsubscribed': []})
        if sender not in subs.get('unsubscribed', []):
            subs.setdefault('unsubscribed', []).append(sender)
            try: p.write_text(json.dumps(subs, indent=2))
            except: pass
        reply  = 'You have been unsubscribed. Take care out there. 🌸'
        action = 'unsubscribed'

    else:
        ai_reply = generate_ai_response(sub_orig, body)
        reply    = ai_reply if ai_reply else HELP_RESPONSE.format(address=GMAIL_ADDRESS, repo_url=REPO_URL)
        action   = 'ai_response' if ai_reply else 'fallback_help'

    ok = send_reply(sender, sub_orig, reply)
    log_interaction(sender, sub_orig, action)
    print(f'[gateway] {"✅" if ok else "❌"} {action} → {sender[:40]}')
    return ok

def run():
    print(f'\n[gateway] 🌸 Email Gateway Engine — {TODAY}')
    print('[gateway] FIXED: Automated senders (GitHub, Stripe, etc.) are now ignored.')

    messages, auto_ignored = check_inbox()
    print(f'[gateway] Real human emails to process: {len(messages)}')
    print(f'[gateway] Automated emails silently ignored: {auto_ignored}')

    processed = 0
    for msg in messages:
        try:
            route_email(msg)
            processed += 1
        except Exception as e:
            print(f'[gateway] Route error: {e}')

    # Log summary
    p = DATA / 'email_gateway_stats.json'
    stats = load(p, {'runs': []})
    stats.setdefault('runs', []).append({
        'date': TODAY,
        'real_processed': processed,
        'automated_ignored': auto_ignored
    })
    stats['runs'] = stats['runs'][-30:]
    try: p.write_text(json.dumps(stats, indent=2))
    except: pass

    print(f'[gateway] Done. Real: {processed} processed. Auto-noise: {auto_ignored} ignored. 🌱')

if __name__ == '__main__':
    run()
