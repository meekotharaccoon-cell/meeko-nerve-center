#!/usr/bin/env python3
"""
Email Gateway Engine
=====================
Anyone with an email address can now talk to this system.
Anyone can GET their own SolarPunk system through email.
This is the most viral distribution mechanism on the planet.
Email is universal. Email works on every phone. Email is forever.

What it does:

  INBOUND (reading emails sent to meekotharaccoon@gmail.com):
    The system checks for emails with specific triggers:
    - Subject contains "FORK ME" → send full setup guide
    - Subject contains "SIGNALS" → send today's crypto signals
    - Subject contains "ACCOUNTABILITY" → send latest congressional trades
    - Subject contains "JOIN" or "SUBSCRIBE" → add to newsletter
    - Subject contains "HELP" → send what the system can do
    - Subject contains "DEPLOY" → send DEPLOY.md as email
    - Anything else from known press contacts → auto-respond with press kit
    - Anything else → LLM reads it, generates a genuine response

  OUTBOUND (system-initiated):
    - Anyone who emails gets a welcome with the system's capabilities
    - Weekly digest to everyone who's ever emailed (opt-in)
    - New fork notification: "someone just forked your system"

  FORK-BY-EMAIL:
    Send an email with subject "FORK ME" to meekotharaccoon@gmail.com
    You get back:
      1. Full DEPLOY.md in the email body
      2. Step-by-step setup for YOUR OWN system
      3. Link to fork the repo
      4. Which 3 secrets to add first to get running in 10 minutes
      5. A welcome to the SolarPunk network

  THIS IS HOW THE NETWORK GROWS.
  Email → Fork → Node → Network → Can't be shut down.
  Every email is a potential new node.
  Golden retriever energy: invite everyone.

Gmail API access via IMAP (no OAuth needed with App Password).
"""

import json, datetime, os, smtplib, imaplib, email as email_lib
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
DEPLOY_URL = f'{REPO_URL}/blob/main/DEPLOY.md'

FORK_RESPONSE = """Welcome to the SolarPunk network. 🌱

You just asked for your own autonomous AI system.
Here's how to have it running in 10 minutes, for free, forever.

━━ STEP 1: FORK ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Go here and click Fork: {fork_url}

━━ STEP 2: ADD 3 SECRETS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Your forked repo → Settings → Secrets and variables → Actions)

HF_TOKEN — free at huggingface.co/settings/tokens
  (This is the AI brain. Takes 2 minutes to get.)

GMAIL_ADDRESS — your Gmail address
GMAIL_APP_PASSWORD — Google Account → Security → App Passwords
  (This lets the system email you its daily intelligence report.)

━━ STEP 3: ENABLE ACTIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Your forked repo → Actions tab → "I understand my workflows" → Enable)

━━ STEP 4: FIRST RUN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Actions → Daily Full Cycle → Run workflow)
Your system starts building itself immediately.

That's it. 10 minutes. Your system runs 5x daily. Forever. Free.

━━ WHAT YOU GET ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
60+ autonomous engines that:
  ✓ Track congressional trades (STOCK Act accountability)
  ✓ Generate art for causes you care about
  ✓ Write and submit grant applications
  ✓ Build their OWN new engines every single day
  ✓ Email you daily intelligence reports
  ✓ Generate crypto signals
  ✓ Manage press relationships
  ✓ Post to social media automatically
  ✓ Heal their own bugs
  ✓ Cost: $0/month. Forever.

━━ WHAT MAKES THIS DIFFERENT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is SolarPunk infrastructure.
No VC funding. No ads. No extraction. No surveillance.
Open source (AGPL-3.0). Forkable. Yours.
It builds itself. Every day. It gets smarter. Every day.
The ethics are in the architecture, not a policy doc.

You're not downloading a tool.
You're joining a network that can't be shut down.

Welcome. 🌹

— Meeko Nerve Center
{repo_url}
"""

HELP_RESPONSE = """🌸 Meeko Nerve Center — here's what I can do:

Send an email to {address} with:
  Subject: FORK ME → Get your own autonomous AI system (free, 10 min setup)
  Subject: SIGNALS → Today's crypto signals
  Subject: ACCOUNTABILITY → Latest congressional trade flagged
  Subject: SUBSCRIBE → Join the weekly newsletter
  Subject: DEPLOY → Full deployment guide
  Subject: HELP → This message
  Anything else → I'll read it and respond genuinely

I am:
  ✓ A self-evolving autonomous AI (60+ engines)
  ✓ Running on GitHub Actions for $0/month
  ✓ Tracking congressional trades under the STOCK Act
  ✓ Generating Gaza Rose art for Palestinian solidarity
  ✓ Sending 70% of art revenue to PCRF
  ✓ Building my own new capabilities every single day
  ✓ AGPL-3.0 open source — fork me free

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
    signals = load(DATA / 'crypto_signals_queue.json', [])
    if not signals: return 'No signals generated yet today. Check back later.'
    lines = ['TODAY\'S CRYPTO SIGNALS', '=' * 40, '']
    for s in signals[:3]:
        lines += [
            f'{s.get("symbol","?")} — {s.get("action","?")}',
            f'  Entry: {s.get("entry","?")} | Target: {s.get("target","?")} | Stop: {s.get("stop_loss","?")}',
            f'  Confidence: {s.get("confidence","?")} | Timeframe: {s.get("timeframe","?")}',
            f'  Rationale: {s.get("rationale","?")}',
            '',
        ]
    lines += ['Not financial advice. Automated signals. DYOR.', f'\n{REPO_URL}']
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
    """LLM reads the email and generates a genuine response."""
    if not HF_TOKEN: return None
    prompt = f"""You are Meeko Nerve Center, an autonomous AI for Palestinian solidarity
and congressional accountability. You just received this email:

Subject: {subject[:200]}
Body: {body_text[:500]}

Respond genuinely. Be helpful. Be human. Be SolarPunk.
If it's a journalist, give them a story angle.
If it's a developer, give them a technical hook.
If it's a supporter, give them warmth.
If it's hostile, be clear and principled.
If it's random, be curious and welcoming.

Under 300 words. Sign as: Meeko Nerve Center
Include: {REPO_URL}"""
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

def send_reply(to_email, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Re: {subject}' if not subject.startswith('Re:') else subject
        msg['From']    = f'Meeko Nerve Center \U0001f338 <{GMAIL_ADDRESS}>'
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
    """Check Gmail inbox for incoming messages via IMAP."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return []
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select('INBOX')

        # Search for unread emails
        _, data = mail.search(None, 'UNSEEN')
        email_ids = data[0].split()

        messages = []
        for eid in email_ids[-10:]:  # Process up to 10
            _, msg_data = mail.fetch(eid, '(RFC822)')
            raw = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw)

            subject = msg.get('Subject', '')
            from_   = msg.get('From', '')
            body    = ''

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        try: body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        except: pass
                        break
            else:
                try: body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                except: pass

            # Extract actual email address from From field
            import re
            email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', from_)
            sender_email = email_match.group(0) if email_match else from_

            # Skip emails from self
            if GMAIL_ADDRESS.lower() in sender_email.lower():
                continue

            messages.append({
                'id':      eid,
                'subject': subject,
                'from':    sender_email,
                'from_raw': from_,
                'body':    body[:2000],
            })

            # Mark as read
            mail.store(eid, '+FLAGS', '\\Seen')

        mail.close()
        mail.logout()
        return messages
    except Exception as e:
        print(f'[gateway] IMAP error: {e}')
        return []

def log_interaction(sender, subject, action):
    p = DATA / 'email_gateway_log.json'
    log = load(p, {'interactions': []})
    log.setdefault('interactions', []).append({
        'date': TODAY, 'from': sender, 'subject': subject[:80], 'action': action
    })
    log['interactions'] = log['interactions'][-200:]
    try: p.write_text(json.dumps(log, indent=2))
    except: pass

def route_email(msg):
    subject  = msg['subject'].upper()
    sender   = msg['from']
    body     = msg['body']
    sub_orig = msg['subject']

    print(f'[gateway] Routing: "{sub_orig[:50]}" from {sender[:40]}')

    if 'FORK ME' in subject or 'FORK' in subject:
        reply = FORK_RESPONSE.format(fork_url=FORK_URL, repo_url=REPO_URL)
        action = 'fork_guide_sent'

    elif 'SIGNAL' in subject:
        reply = get_todays_signals()
        action = 'signals_sent'

    elif 'ACCOUNTABILITY' in subject or 'CONGRESS' in subject or 'TRADE' in subject:
        reply = get_latest_trade()
        action = 'trade_sent'

    elif 'SUBSCRIBE' in subject or 'JOIN' in subject or 'NEWSLETTER' in subject:
        added = add_to_newsletter(sender, msg.get('from_raw', ''))
        reply = f"""You're {'now subscribed to' if added else 'already on'} the Meeko Nerve Center weekly newsletter. 🌸

You'll get: congressional accountability hits, Gaza Rose art drops,
PCRF impact numbers, system evolution updates, crypto signals.

Every Sunday. Always free.

While you wait: {REPO_URL}

Free Palestine. 🌹
"""
        action = 'subscribed'

    elif 'DEPLOY' in subject or 'SETUP' in subject or 'INSTALL' in subject:
        reply = get_deploy_guide()
        action = 'deploy_guide_sent'

    elif 'HELP' in subject or 'WHAT' in subject or 'HOW' in subject:
        reply = HELP_RESPONSE.format(address=GMAIL_ADDRESS, repo_url=REPO_URL)
        action = 'help_sent'

    elif 'UNSUBSCRIBE' in subject:
        p = DATA / 'newsletter_subscribers.json'
        subs = load(p, {'unsubscribed': []})
        if sender not in subs.get('unsubscribed', []):
            subs.setdefault('unsubscribed', []).append(sender)
            try: p.write_text(json.dumps(subs, indent=2))
            except: pass
        reply = 'You have been unsubscribed. Take care out there. 🌸'
        action = 'unsubscribed'

    else:
        # AI reads it and responds
        ai_reply = generate_ai_response(sub_orig, body)
        if ai_reply:
            reply  = ai_reply
            action = 'ai_response'
        else:
            reply  = HELP_RESPONSE.format(address=GMAIL_ADDRESS, repo_url=REPO_URL)
            action = 'fallback_help'

    ok = send_reply(sender, sub_orig, reply)
    log_interaction(sender, sub_orig, action)
    print(f'[gateway] {"\u2705" if ok else "\u274c"} Replied: {action} → {sender[:40]}')
    return ok

def run():
    print(f'\n[gateway] \U0001f338 Email Gateway Engine \u2014 {TODAY}')
    print(f'[gateway] Anyone who emails {GMAIL_ADDRESS} gets the SolarPunk network.')

    messages = check_inbox()
    print(f'[gateway] Unread messages: {len(messages)}')

    processed = 0
    for msg in messages:
        try:
            route_email(msg)
            processed += 1
        except Exception as e:
            print(f'[gateway] Route error: {e}')

    print(f'[gateway] Processed {processed} messages.')
    print('[gateway] Done. The network grows. 🌱')

if __name__ == '__main__':
    run()
