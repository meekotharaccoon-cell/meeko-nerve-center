#!/usr/bin/env python3
"""
MAILER PRO
===========
Drop-in upgrade from Gmail App Password to professional email delivery.

Priority order (uses best available):
  1. Postmark  — dedicated IP, best deliverability, open tracking ($15/mo)
  2. Mailgun   — dedicated IP on paid, 100/day free, open tracking on free
  3. SendGrid  — 100/day free, shared IP, open tracking
  4. Gmail     — fallback, works, but shared IP = more spam filtering

The system auto-detects which credentials are present and uses the best one.
No code changes needed when you upgrade — just add the secret.

Open tracking: when the recipient opens the email, we log it.
This tells us: did the foundation read the grant application?
Did the tech contact open the hello email?
That signal feeds directly into signal_tracker.py's recommendations.

SECRETS (add whichever you have):
  POSTMARK_SERVER_TOKEN  — from postmarkhq.com (best)
  MAILGUN_API_KEY        — from mailgun.com (free tier: 100/day)
  MAILGUN_DOMAIN         — your sending domain in Mailgun
  SENDGRID_API_KEY       — from sendgrid.com (free: 100/day)
  GMAIL_APP_PASSWORD     — fallback
  GMAIL_USER             — fallback sender address

Domain setup (do once, unlocks everything):
  1. Buy a domain: ~$12/year (Namecheap, Porkbun)
     OR use a free subdomain from mailgun's sandbox (for testing)
  2. Add DNS records Mailgun/Postmark gives you (SPF, DKIM, DMARC)
  3. Update MAIL_FROM below
  4. Deliverability goes from ~60% inbox to ~98% inbox
"""
import os, json, urllib.request, urllib.parse, base64, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from pathlib import Path

# ---- CREDENTIALS (auto-detected) ---------------------------------
POSTMARK_TOKEN  = os.environ.get('POSTMARK_SERVER_TOKEN', '')
MAILGUN_KEY     = os.environ.get('MAILGUN_API_KEY', '')
MAILGUN_DOMAIN  = os.environ.get('MAILGUN_DOMAIN', '')
SENDGRID_KEY    = os.environ.get('SENDGRID_API_KEY', '')
GMAIL_PASS      = os.environ.get('GMAIL_APP_PASSWORD', '')
GMAIL_USER      = os.environ.get('GMAIL_USER', 'solarpunk.mycelium@gmail.com')

MAIL_FROM       = os.environ.get('MAIL_FROM', GMAIL_USER)
MAIL_FROM_NAME  = 'SolarPunk Mycelium'

# ---- TRACKING LOG ------------------------------------------------
DATA_DIR    = Path('data')
OPEN_LOG    = DATA_DIR / 'email_opens.json'
SEND_LOG    = DATA_DIR / 'mailer_pro_sent.json'

def load(path):
    try: return json.loads(Path(path).read_text())
    except: return {}

def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2))

# ---- PROVIDER DETECTION ------------------------------------------
def best_provider():
    if POSTMARK_TOKEN:  return 'postmark'
    if MAILGUN_KEY and MAILGUN_DOMAIN: return 'mailgun'
    if SENDGRID_KEY:    return 'sendgrid'
    if GMAIL_PASS:      return 'gmail'
    return None

def provider_info():
    p = best_provider()
    features = {
        'postmark':  {'open_tracking': True,  'dedicated_ip': True,  'daily_limit': 45000, 'cost': '$15/mo'},
        'mailgun':   {'open_tracking': True,  'dedicated_ip': False, 'daily_limit': 100,   'cost': 'Free / $35+'},
        'sendgrid':  {'open_tracking': True,  'dedicated_ip': False, 'daily_limit': 100,   'cost': 'Free / $20+'},
        'gmail':     {'open_tracking': False, 'dedicated_ip': False, 'daily_limit': 500,   'cost': 'Free'},
    }
    return p, features.get(p, {})

# ---- SENDERS -----------------------------------------------------
def send_postmark(to, subject, body_text, body_html=None, tag=None):
    payload = {
        'From': f'{MAIL_FROM_NAME} <{MAIL_FROM}>',
        'To': to,
        'Subject': subject,
        'TextBody': body_text,
        'TrackOpens': True,
        'TrackLinks': 'HtmlAndText',
    }
    if body_html:
        payload['HtmlBody'] = body_html
    if tag:
        payload['Tag'] = tag  # e.g. 'grants', 'hello', 'tcpa'

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        'https://api.postmarkapp.com/email',
        data=data, method='POST'
    )
    req.add_header('Accept', 'application/json')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-Postmark-Server-Token', POSTMARK_TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            return True, resp.get('MessageID', 'sent'), resp
    except Exception as e:
        return False, str(e), {}

def send_mailgun(to, subject, body_text, body_html=None, tag=None):
    data = {
        'from': f'{MAIL_FROM_NAME} <mailgun@{MAILGUN_DOMAIN}>',
        'to': to,
        'subject': subject,
        'text': body_text,
        'o:tracking': 'yes',
        'o:tracking-clicks': 'yes',
        'o:tracking-opens': 'yes',
    }
    if body_html:
        data['html'] = body_html
    if tag:
        data['o:tag'] = tag

    encoded = urllib.parse.urlencode(data).encode()
    creds = base64.b64encode(f'api:{MAILGUN_KEY}'.encode()).decode()
    req = urllib.request.Request(
        f'https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages',
        data=encoded, method='POST'
    )
    req.add_header('Authorization', f'Basic {creds}')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            return True, resp.get('id', 'sent'), resp
    except Exception as e:
        return False, str(e), {}

def send_sendgrid(to, subject, body_text, body_html=None, tag=None):
    payload = {
        'personalizations': [{'to': [{'email': to}]}],
        'from': {'email': MAIL_FROM, 'name': MAIL_FROM_NAME},
        'subject': subject,
        'content': [{'type': 'text/plain', 'value': body_text}],
        'tracking_settings': {
            'click_tracking': {'enable': True},
            'open_tracking': {'enable': True},
        },
    }
    if body_html:
        payload['content'].append({'type': 'text/html', 'value': body_html})
    if tag:
        payload['categories'] = [tag]

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        'https://api.sendgrid.com/v3/mail/send',
        data=data, method='POST'
    )
    req.add_header('Authorization', f'Bearer {SENDGRID_KEY}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return True, 'sent', {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return False, body, {}
    except Exception as e:
        return False, str(e), {}

def send_gmail(to, subject, body_text, body_html=None, tag=None):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f'{MAIL_FROM_NAME} <{GMAIL_USER}>'
    msg['To']      = to
    msg.attach(MIMEText(body_text, 'plain'))
    if body_html:
        msg.attach(MIMEText(body_html, 'html'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, to, msg.as_string())
        return True, 'gmail_sent', {}
    except Exception as e:
        return False, str(e), {}

# ---- MAIN SEND FUNCTION ------------------------------------------
def send(to, subject, body_text, body_html=None, tag=None, dry_run=False):
    """
    Send an email using the best available provider.
    Logs the send with provider used, message ID, timestamp.
    Returns (success, message_id, provider_used)
    """
    provider, info = provider_info()

    if not provider:
        print('  [mailer] No email credentials found')
        return False, 'no_provider', None

    print(f'  [mailer] Provider: {provider} | To: {to} | Subject: {subject[:50]}')
    if info.get('open_tracking'):
        print(f'  [mailer] Open tracking: ENABLED')

    if dry_run:
        print(f'  [mailer] DRY RUN — would send via {provider}')
        return True, 'dry_run', provider

    senders = {
        'postmark': send_postmark,
        'mailgun':  send_mailgun,
        'sendgrid': send_sendgrid,
        'gmail':    send_gmail,
    }

    ok, msg_id, resp = senders[provider](to, subject, body_text, body_html, tag)

    # Log it
    log = load(SEND_LOG)
    if 'sent' not in log:
        log['sent'] = []
    log['sent'].append({
        'to': to,
        'subject': subject[:80],
        'provider': provider,
        'tag': tag,
        'message_id': msg_id,
        'ok': ok,
        'sent_at': datetime.now(timezone.utc).isoformat(),
    })
    save(SEND_LOG, log)

    status = 'SENT' if ok else 'FAILED'
    print(f'  [mailer] {status}: {msg_id}')
    return ok, msg_id, provider

# ---- OPEN TRACKING PULLER ----------------------------------------
def pull_open_stats():
    """
    Pull open/click data from provider APIs.
    Mailgun and Postmark both have event APIs.
    This tells us which emails were actually read.
    """
    opens = load(OPEN_LOG)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    if MAILGUN_KEY and MAILGUN_DOMAIN:
        try:
            creds = base64.b64encode(f'api:{MAILGUN_KEY}'.encode()).decode()
            req = urllib.request.Request(
                f'https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/events?event=opened&limit=100'
            )
            req.add_header('Authorization', f'Basic {creds}')
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            events = data.get('items', [])
            opens[today] = opens.get(today, {})
            opens[today]['mailgun_opens'] = len(events)
            opens[today]['opened_subjects'] = [
                e.get('message', {}).get('headers', {}).get('subject', '')[:60]
                for e in events[:10]
            ]
            print(f'  [opens] Mailgun: {len(events)} opens')
        except Exception as e:
            print(f'  [opens] Mailgun error: {e}')

    if POSTMARK_TOKEN:
        # Postmark message stream stats
        try:
            req = urllib.request.Request(
                'https://api.postmarkapp.com/stats/outbound/opens?count=50&offset=0'
            )
            req.add_header('X-Postmark-Server-Token', POSTMARK_TOKEN)
            req.add_header('Accept', 'application/json')
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            total_opens = data.get('TotalOpened', 0)
            opens[today] = opens.get(today, {})
            opens[today]['postmark_total_opens'] = total_opens
            print(f'  [opens] Postmark: {total_opens} total opens')
        except Exception as e:
            print(f'  [opens] Postmark error: {e}')

    save(OPEN_LOG, opens)
    return opens

# ---- STATUS REPORT -----------------------------------------------
def status():
    provider, info = provider_info()
    print('\n' + '='*52)
    print('  MAILER PRO STATUS')
    print('='*52)
    print(f'  Active provider: {provider or "NONE — add a credential"}')
    if info:
        print(f'  Open tracking:   {"YES" if info.get("open_tracking") else "NO"}')
        print(f'  Dedicated IP:    {"YES" if info.get("dedicated_ip") else "NO"}')
        print(f'  Daily limit:     {info.get("daily_limit", "?")} emails')
        print(f'  Cost:            {info.get("cost", "?")}')    
    print('\n  To upgrade:')
    print('  1. Get Mailgun free account (100/day, open tracking)')
    print('     mailgun.com → add MAILGUN_API_KEY + MAILGUN_DOMAIN secrets')
    print('  2. Get Postmark ($15/mo, dedicated IP, best deliverability)')
    print('     postmarkhq.com → add POSTMARK_SERVER_TOKEN secret')
    print('  3. The system auto-switches to best available provider')
    print('='*52)

if __name__ == '__main__':
    status()
    pull_open_stats()
