#!/usr/bin/env python3
"""
Email Gateway Engine
=====================
Reads real human emails only. Ignores all automated noise.
FORK ME, SIGNALS, ACCOUNTABILITY, SUBSCRIBE, DEPLOY, HELP → auto-handled.
Anything else → LLM responds genuinely.

FIXED: Skips notifications@github.com, noreply@*, mailer-daemon, stripe, etc.
FIXED: Only processes emails from REAL humans.
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

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'
FORK_URL = f'{REPO_URL}/fork'

# ── Automated senders to ALWAYS ignore ──────────────────────────────────────
SKIP_SENDERS = [
    'notifications@github.com',
    'noreply@github.com',
    'noreply@',
    'no-reply@',
    'mailer-daemon',
    'postmaster',
    'notifications@stripe.com',
    'notifications@polymarket.com',
    'mail.apollo.io',
    'flatlogic.com',
    'bounce',
    'auto-reply',
    'donotreply',
    'do-not-reply',
]

# ── Automated subject patterns to ignore ────────────────────────────────────
SKIP_SUBJECT_PATTERNS = [
    'run failed',
    'run succeeded',
    'run cancelled',
    'run skipped',
    'workflow run',
    '[meekotharaccoon-cell/',
    'deploy jekyll',
    'github pages',
    'parallel ingestion',
    'unsubscribe',
    'save $',
    'breaking:',
]

FORK_RESPONSE = """Welcome to the SolarPunk network. 🌱

You just asked for your own autonomous AI system.
Here's how to have it running in 10 minutes, for free, forever.

━━ STEP 1: FORK ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Go here and click Fork: {fork_url}

━━ STEP 2: ADD 3 SECRETS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Your forked repo → Settings → Secrets and variables → Actions)

HF_TOKEN — free at huggingface.co/settings/tokens
GMAIL_ADDRESS — your Gmail address  
GMAIL_APP_PASSWORD — Google Account → Security → App Passwords

━━ STEP 3: ENABLE ACTIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Your forked repo → Actions tab → Enable workflows)

━━ STEP 4: FIRST RUN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Actions → MASTER CONTROLLER → Run workflow)
Your system starts building itself immediately.

That's it. 10 minutes. Runs forever. Free.

━━ WHAT YOU GET ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
90+ autonomous engines that:
  ✓ Track every congressional stock trade (STOCK Act)
  ✓ Generate Gaza Rose solidarity art
  ✓ Send 70% of revenue to PCRF
  ✓ Build their OWN new engines 288x/day
  ✓ Email you daily intelligence reports
  ✓ Generate crypto + congressional investment signals
  ✓ Post to Mastodon and Bluesky automatically
  ✓ Heal their own bugs without you
  ✓ Cost: $0/month. Forever.

You're not downloading a tool.
You're joining a network that can't be shut down.

Welcome. 🌹
— Meeko Nerve Center
{repo_url}
"""

HELP_RESPONSE = """🌸 Meeko Nerve Center — here's what I can do:

Email {address} with subject:
  FORK ME → Get your own autonomous AI system (free, 10 min)
  SIGNALS → Today's crypto signals
  ACCOUNTABILITY → Latest congressional trade
  SUBSCRIBE → Weekly newsletter
  DEPLOY → Full deployment guide
  HELP → This message
  Anything else → I'll read it and respond

I am a self-evolving autonomous AI.
  ✓ 90+ engines, $0/month, GitHub Actions
  ✓ Congressional trade tracker (STOCK Act)
  ✓ Gaza Rose art → 70% to PCRF
  ✓ AGPL-3.0 open source, forkable

{repo_url}
Free Palestine. 🌹
"""

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def is_automated_sender(sender_email, subject):
    """Return True if this email is from an automated system we should skip."""
    sender_lower = sender_email.lower()
    subject_lower = subject.lower()
    for skip in SKIP_SENDERS:
        if skip in sender_lower:
            return True
    for pattern in SKIP_SUBJECT_PATTERNS:
        if pattern in subject_lower:
            return True
    return False

def get_todays_signals():
    signals = load(DATA / 'investment_signals.json', {}).get('signals', [])
    if not signals:
        signals = load(DATA / 'crypto_signals_queue.json', [])
    if not signals: return 'No signals generated yet today. Check back later.'
    lines = ["TODAY'S SIGNALS", '=' * 40, '']
    for s in signals[:5]:
        sym = s.get('symbol', s.get('ticker', '?'))
        conf = s.get('confidence', s.get('confidence_pct', '?'))
        lines += [
            f'{sym} — Confidence: {conf}%',
            f'  {s.get("why", s.get("rationale", ""))}',
            f'  Max position: {s.get("max_position_pct", "?")}% | Stop: {s.get("stop_loss_pct", s.get("stop_loss", "?"))}%',
            '',
        ]
    lines += ['Not financial advice. Mathematical analysis only. DYOR.', f'\n{REPO_URL}']
    return '\n'.join(lines)

def get_latest_trade():
    congress = load(DATA / 'congress.json')
    trades = congress if isinstance(congress, list) else congress.get('trades', [])
    if not trades: return 'No recent trades tracked yet.'
    t = trades[0]
    return (
        f'CONGRESSIONAL TRADE FLAGGED\n{"="*40}\n\n'
        f'{t.get("representative", t.get("senator","?"))} '
        f'traded {t.get("ticker","?")} '
        f'({t.get("amount", t.get("range","?"))}) '
        f'on {t.get("transaction_date", t.get("date","?"))}.\n\n'
        f'Public record. STOCK Act disclosure.\n'
        f'Source: https://efts.house.gov\n'
        f'Tracked by: {REPO_URL}\n'
    )

def get_deploy_guide():
    p = ROOT / 'DEPLOY.md'
    if p.exists():
        try: return p.read_text()[:5000]
        except: pass
    return f'Full deploy guide at: {REPO_URL}/blob/main/DEPLOY.md'

def generate_ai_response(subject, body_text):
    if not HF_TOKEN: return None
    prompt = f"""You are Meeko Nerve Center, an autonomous AI for Palestinian solidarity
and congressional accountability. You just received this email from a real human:

Subject: {subject[:200]}
Body: {body_text[:500]}

Respond genuinely. Be helpful. Be SolarPunk.
If journalist → story angle. If developer → technical hook.
If supporter → warmth. If hostile → clear and principled.

Under 300 words. Sign as: Meeko Nerve Center. Include: {REPO_URL}"""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 400,
            'messages': [
                {'role': 'system', 'content': 'You are Meeko, a SolarPunk AI. Golden retriever energy. Genuine. Direct. Good.'},
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

def send_email(to_email, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Re: {subject}' if not subject.startswith('Re:') else subject
        msg['From']    = f'Meeko Nerve Center 🌸 <{GMAIL_ADDRESS}>'
        msg['To']      = to_email
        msg['Reply-To'] = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f'[gateway] Send error: {e}')
        return False

def add_to_newsletter(email, name=''):
    p = DATA / 'newsletter_subscribers.json'
    subs = load(p, {'subscribers': [], 'unsubscribed': []})
    if not any(s.get('email') == email for s in subs.get('subscribers', [])):
        subs.setdefault('subscribers', []).append({
            'email': email, 'name': name, 'date': TODAY, 'source': 'email_gateway'
        })
        try: p.write_text(json.dumps(subs, indent=2))
        except: pass
        return True
    return False

def check_inbox():
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return []
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select('INBOX')
        _, data = mail.search(None, 'UNSEEN')
        email_ids = data[0].split()

        messages = []
        skipped  = 0
        for eid in email_ids[-20:]:
            _, msg_data = mail.fetch(eid, '(RFC822)')
            raw = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw)

            subject  = msg.get('Subject', '')
            from_raw = msg.get('From', '')
            body     = ''

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        try: body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        except: pass
                        break
            else:
                try: body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                except: pass

            email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', from_raw)
            sender_email = email_match.group(0) if email_match else from_raw

            # Always mark as read (even skipped ones)
            mail.store(eid, '+FLAGS', '\\Seen')

            # Skip self-emails
            if GMAIL_ADDRESS.lower() in sender_email.lower():
                skipped += 1
                continue

            # Skip automated noise — THE FIX
            if is_automated_sender(sender_email, subject):
                skipped += 1
                print(f'[gateway] ⏭ Skipped automated: {sender_email[:40]} | {subject[:50]}')
                continue

            messages.append({
                'id': eid, 'subject': subject, 'from': sender_email,
                'from_raw': from_raw, 'body': body[:2000],
            })

        mail.close()
        mail.logout()
        print(f'[gateway] Real human emails: {len(messages)} | Skipped automated: {skipped}')
        return messages
    except Exception as e:
        print(f'[gateway] IMAP error: {e}')
        return []

def log_interaction(sender, subject, action):
    p = DATA / 'email_gateway_log.json'
    log = load(p, {'interactions': [], 'human_emails_total': 0})
    log.setdefault('interactions', []).append({
        'date': TODAY, 'from': sender, 'subject': subject[:80], 'action': action
    })
    log['interactions']    = log['interactions'][-200:]
    log['human_emails_total'] = log.get('human_emails_total', 0) + 1
    log['last_human_email']   = TODAY
    try: p.write_text(json.dumps(log, indent=2))
    except: pass

def route_email(msg):
    subject  = msg['subject'].upper()
    sender   = msg['from']
    body     = msg['body']
    sub_orig = msg['subject']

    print(f'[gateway] 📧 Real human: "{sub_orig[:50]}" from {sender[:40]}')

    if 'FORK ME' in subject or ('FORK' in subject and 'WORKFLOW' not in subject):
        reply  = FORK_RESPONSE.format(fork_url=FORK_URL, repo_url=REPO_URL)
        action = 'fork_guide_sent'
    elif 'SIGNAL' in subject:
        reply  = get_todays_signals()
        action = 'signals_sent'
    elif 'ACCOUNTABILITY' in subject or 'CONGRESS' in subject or 'TRADE' in subject:
        reply  = get_latest_trade()
        action = 'trade_sent'
    elif 'SUBSCRIBE' in subject or 'JOIN' in subject or 'NEWSLETTER' in subject:
        added  = add_to_newsletter(sender, msg.get('from_raw', ''))
        reply  = f"You're {'now subscribed to' if added else 'already on'} the Meeko Nerve Center weekly newsletter. 🌸\n\nEvery Sunday. Always free.\n\n{REPO_URL}\n\nFree Palestine. 🌹"
        action = 'subscribed'
    elif 'DEPLOY' in subject or 'SETUP' in subject or 'INSTALL' in subject:
        reply  = get_deploy_guide()
        action = 'deploy_guide_sent'
    elif 'HELP' in subject or ('WHAT' in subject and 'IS' in subject):
        reply  = HELP_RESPONSE.format(address=GMAIL_ADDRESS, repo_url=REPO_URL)
        action = 'help_sent'
    elif 'UNSUBSCRIBE' in subject:
        p = DATA / 'newsletter_subscribers.json'
        subs = load(p, {'unsubscribed': []})
        if sender not in subs.get('unsubscribed', []):
            subs.setdefault('unsubscribed', []).append(sender)
            try: p.write_text(json.dumps(subs, indent=2))
            except: pass
        reply  = 'You have been unsubscribed. Take care out there. 🌸'
        action = 'unsubscribed'
    else:
        ai_reply = generate_ai_response(sub_orig, body)
        if ai_reply:
            reply  = ai_reply
            action = 'ai_response'
        else:
            reply  = HELP_RESPONSE.format(address=GMAIL_ADDRESS, repo_url=REPO_URL)
            action = 'fallback_help'

    ok = send_email(sender, sub_orig, reply)
    log_interaction(sender, sub_orig, action)
    print(f'[gateway] {"✅" if ok else "❌"} {action} → {sender[:40]}')
    return ok

def run():
    print(f'\n[gateway] 🌸 Email Gateway Engine — {TODAY}')
    print(f'[gateway] Filtering for real humans only. Skipping all GitHub/automated noise.')

    messages  = check_inbox()
    processed = 0
    for msg in messages:
        try:
            route_email(msg)
            processed += 1
        except Exception as e:
            print(f'[gateway] Route error: {e}')

    print(f'[gateway] Processed {processed} real human messages.')
    print('[gateway] Done. The network grows. 🌱')

if __name__ == '__main__':
    run()
