#!/usr/bin/env python3
"""
Email Gateway v5 — Zero false positives
========================================
Changes from v4:
  - Added missing blocked domains: tiktok.com, amazon.com, pinterest.com,
    huggingface.co, redbubble.com, society6.com, teepublic.com, nightcafe.studio,
    ebay.com, medium.com, discord.com, mongodb.com, replit.com, gdevelop.io,
    base44.com, solpump.io, canva.com, manychat.com, freeup.net, linktr.ee
  - Added missing auto prefixes: store-news@, website@, nobody@, pinbot@,
    recommendations@, heythere@, canva*@, business-account@
  - is_on_topic() now requires SUBJECT match OR both subject+body match.
    Body-only matches were causing false positives (Amazon email body had "github").
  - Self-emails from the system now go to data/system_inbox.json NOT Gmail.
    Scripts that send to Gmail have been redirected.

THE ONE JOB: Reply to real humans who ask about SolarPunk.
Do nothing else. Never generate outbound email noise.
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

# ── BLOCKED DOMAINS (v5 — complete) ──────────────────────────────────────────
BLOCKED_DOMAINS = {
    # GitHub
    'github.com', 'githubusercontent.com', 'noreply.github.com',
    # Payment processors
    'stripe.com', 'paypal.com', 'square.com', 'braintree.com',
    # Crypto exchanges
    'coinbase.com', 'binance.com', 'kraken.com', 'bitfinex.com',
    'gemini.com', 'kucoin.com', 'bybit.com', 'okx.com',
    'crypto.com', 'ftx.com', 'huobi.com', 'gate.io',
    'cryptohopper.com', 'pionex.us', 'pionex.com',
    'tradingview.com', 'coingecko.com', 'coinmarketcap.com',
    'messari.io', 'glassnode.com', 'nansen.ai',
    'polymarket.com', 'dydx.exchange', 'uniswap.org', 'solpump.io',
    # Email marketing
    'mailchimp.com', 'list-manage.com', 'sendgrid.net', 'sendgrid.com',
    'mailgun.org', 'mailgun.net', 'amazonses.com', 'amazonaws.com',
    'postmarkapp.com', 'sparkpostmail.com', 'klaviyo.com',
    'constantcontact.com', 'campaignmonitor.com', 'mailerlite.com',
    'convertkit.com', 'drip.com', 'substack.com', 'beehiiv.com',
    # CRM / Sales
    'hubspot.com', 'salesforce.com', 'pardot.com', 'marketo.com',
    'apollo.io', 'outreach.io', 'salesloft.com',
    # Social / Communication
    'twitter.com', 'x.com', 'facebook.com', 'meta.com',
    'instagram.com', 'linkedin.com', 'discord.com', 'slack.com',
    'notion.so', 'intercom.io', 'intercom.com',
    'tiktok.com',        # v5 — WAS MISSING. caused TikTok shop reply
    'pinterest.com',     # v5 — WAS MISSING. caused Pinterest marketing reply
    # Support
    'zendesk.com', 'freshdesk.com', 'helpscout.com', 'front.com',
    # Commerce
    'gumroad.com', 'etsy.com', 'shopify.com', 'patreon.com',
    'ko-fi.com', 'buymeacoffee.com',
    'redbubble.com', 'redbubblemail.com', # v5 — was missing
    'society6.com',      # v5 — was missing
    'teepublic.com',     # v5 — was missing
    'ebay.com',          # v5 — was missing
    # Amazon — ALL subdomains
    'amazon.com',        # v5 — WAS MISSING. caused Amazon Associates reply + bounce reply
    # Google
    'google.com', 'googlemail.com', 'accounts.google.com',
    # AI/ML platforms — do not reply to login alerts etc
    'huggingface.co',    # v5 — WAS MISSING. caused HuggingFace login alert reply
    'openai.com',
    # Creator tools
    'canva.com',         # v5 — was slipping through on engage.canva.com subdomains
    'nightcafe.studio',  # v5 — was missing
    'gdevelop.io', 'gdevelop-app.com',  # v5
    'base44.com',        # v5
    'medium.com',        # v5
    'replit.com',        # v5
    'mongodb.com',       # v5
    'manychat.com',      # v5
    'freeup.net',        # v5
    'linktr.ee',         # v5
    # Infra
    'heroku.com', 'netlify.com', 'vercel.com', 'cloudflare.com',
    'namecheap.com', 'godaddy.com', 'digitalocean.com',
    # Other fintech
    'robinhood.com', 'webull.com', 'etrade.com', 'fidelity.com',
    'schwab.com', 'vanguard.com',
    # Resend — they use support@ but it's a system email
    'resend.com',
}

AUTO_PREFIXES = [
    'noreply@', 'no-reply@', 'donotreply@', 'do-not-reply@',
    'notifications@', 'notify@', 'alert@', 'alerts@',
    'mailer@', 'mailer-daemon@', 'bounce@', 'bounces@',
    'postmaster@', 'automailer@', 'auto@', 'automated@',
    'robot@', 'bot@', 'system@', 'daemon@',
    'support@', 'help@', 'hello@', 'hi@', 'team@',
    'info@', 'contact@', 'newsletter@', 'news@',
    'updates@', 'update@', 'digest@', 'feedback@',
    'marketing@', 'promo@', 'promotions@',
    'billing@', 'payments@', 'invoices@',
    'security@', 'account@', 'accounts@',
    'admin@', 'administrator@', 'webmaster@',
    # v5 additions — these were causing false replies
    'store-news@',       # Amazon store news
    'website@',          # HuggingFace login alerts (website@huggingface.co)
    'nobody@',           # Bounce addresses (nobody@bounces.amazon.com)
    'pinbot@',           # Pinterest bots
    'recommendations@',  # Recommendation engines
    'heythere@',         # RedBubble promo
    'notification@',     # TikTok notifications
    'verify@',           # Verification emails
    'canvaworldtour@', 'canvadesignschool@', 'product@', 'business@',
    'ttsmarketplace@',   # TikTok Shop
    'pinterest-recommendations@',
    'ebay@',
    'service@',
    'analytics-noreply@', 'tagmanager-noreply@', 'business-noreply@',
    'account-security-noreply@',
    'fomoapp@',
    'mongodb-atlas@',
    'contact@',
]

AUTO_SUBJECTS = [
    # GitHub Actions
    'run failed:', 'run succeeded:', 'run cancelled:', 'run skipped:',
    '[meekotharaccoon-cell/', 'workflow run', 'github actions',
    'pull request', 'issue opened', 'issue closed',
    # Bounces
    'delivery status notification', 'undeliverable',
    'mail delivery failed', 'mailbox does not exist',
    'mailbox not found', 'address not found',
    'user unknown', 'no such user', 'delivery failure',
    # Auto-replies
    'automatic reply', 'auto reply', 'auto-reply',
    'out of office', 'on vacation', 'away from the office',
    'thank you for contacting', 'thanks for reaching out',
    'thanks for contacting', 'thank you for your email',
    'we received your', 'your request', 'will get back to you',
    'your message has been received', 'ticket #', 'case #',
    # Marketing
    'unsubscribe', 'manage preferences', 'email preferences',
    'view in browser', 'you received this email because',
    'you are receiving this', 'to stop receiving',
    # Security/account — never reply to these
    'new login', 'login from', 'security alert', 'security info',
    'password changed', 'email address has been changed',
    'your code:', 'verification code', 'confirm your',
    '2fa', 'two-factor', 'login code',
    # Commerce
    'bonus available', 'deposit now', 'trade now',
    'tax documents', 'account deactivated', 'account suspended',
    'flash sale', 'free shipping', 'off sitewide', '% off',
    'shop now', 'buy now', 'limited time', 'expires soon',
    # System health emails from OUR OWN system
    # (these are self-emails we want to keep silent in inbox)
    '⚠️ system health', '⚠️ 1 validation', '📁 new grant draft',
    'new grant draft', 'system health:', 'validation failure',
    '[diagnostic]', '[self-fix]', '[blocked]', '[alert]', '[workflow-fail]',
]

AUTO_BODY_PATTERNS = [
    'this is an automated response', 'this is an automatic reply',
    'please do not reply to this email', 'do not reply to this message',
    'this email was sent from an unmonitored address',
    'this message is auto-generated', 'if you did not request this',
    'you are receiving this because you',
    'unsubscribe from this list', 'manage your preferences',
]

# v5 — SUBJECT ONLY topic matching. Body-only matches caused false positives.
# Amazon Associates email body happened to contain "github" somewhere.
# Rule: MUST match in the SUBJECT to reply. Body match alone = ignore.
RESPONSE_TOPICS_SUBJECT = [
    'solarpunk', 'solar punk', 'nerve center', 'meeko',
    'fork this', 'fork it', 'clone this', 'how does this work',
    'what is this', 'tell me more', 'interested in your',
    'palestine', 'palestinian', 'pcrf', 'gaza', 'humanitarian',
    'congress', 'congressional', 'accountability',
    'crypto signal', 'art generator', 'gaza rose',
    'grant question', 'autonomous ai', 'self-building',
    'open source project', 'agpl',
]


def is_placeholder_email(addr: str) -> bool:
    red_flags = ['[', ']', 'paste', 'your ', 'link', 'forum', 'discord', 'community']
    return any(f in addr.lower() for f in red_flags) or '@' not in addr


def is_automated(from_email: str, from_raw: str, subject: str, body: str):
    e = from_email.lower().strip()
    s = subject.lower()
    b = body.lower()[:2000]

    # Self-email
    if GMAIL_ADDRESS and GMAIL_ADDRESS.lower() in e:
        return True, 'self-email (env match)'
    if 'meekotharaccoon' in e:
        return True, 'self-email (username match)'

    # Placeholder
    if is_placeholder_email(from_email):
        return True, 'placeholder address'

    # Domain blocklist
    domain = e.split('@')[-1] if '@' in e else e
    if domain in BLOCKED_DOMAINS:
        return True, f'blocked domain: {domain}'
    for bd in BLOCKED_DOMAINS:
        if domain.endswith('.' + bd):
            return True, f'blocked subdomain: {domain}'

    # Prefix blocklist
    local = e.split('@')[0] + '@' if '@' in e else e
    for prefix in AUTO_PREFIXES:
        if e.startswith(prefix) or local == prefix:
            return True, 'auto prefix'

    # Subject patterns
    for pattern in AUTO_SUBJECTS:
        if pattern in s:
            return True, 'auto subject'

    # Body patterns
    for pattern in AUTO_BODY_PATTERNS:
        if pattern in b:
            return True, 'auto body'

    # Encoded GitHub subjects
    if ('=?utf' in s or '=?UTF' in s) and ('run' in s or 'meekotharaccoon' in s):
        return True, 'encoded github notification'

    return False, ''


def is_on_topic(subject: str, body: str) -> bool:
    """
    v5 — Subject MUST match. Body-only match is not enough.
    Prevents false positives where spam bodies contain common keywords.
    """
    subj_lower = subject.lower()
    return any(topic in subj_lower for topic in RESPONSE_TOPICS_SUBJECT)


def get_dedup_key(from_email: str) -> str:
    return hashlib.md5(from_email.lower().encode()).hexdigest()[:12]


def was_replied_recently(from_email: str) -> bool:
    p = DATA / 'email_reply_dedup.json'
    try:
        dedup = json.loads(p.read_text()) if p.exists() else {}
        last  = dedup.get(get_dedup_key(from_email))
        if not last: return False
        age_h = (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(last)).total_seconds() / 3600
        return age_h < 48
    except:
        return False


def mark_replied(from_email: str):
    p = DATA / 'email_reply_dedup.json'
    try:
        dedup   = json.loads(p.read_text()) if p.exists() else {}
        cutoff  = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        dedup   = {k: v for k, v in dedup.items() if datetime.datetime.fromisoformat(v) > cutoff}
        dedup[get_dedup_key(from_email)] = datetime.datetime.utcnow().isoformat()
        p.write_text(json.dumps(dedup, indent=2))
    except:
        pass


def build_reply(from_email: str, subject: str, body: str) -> str:
    if HF_TOKEN:
        try:
            prompt = f"""You are Meeko Nerve Center — a SolarPunk autonomous AI system for Palestinian solidarity.

Someone emailed:
Subject: {subject[:200]}
Body: {body[:600]}

Write a genuine, focused reply. Rules:
- Answer what they actually asked
- If they want to fork/run it: Repo: {REPO_URL} — Fork: {FORK_URL} — needs HF_TOKEN + Gmail app password
- Mention: 70% of revenue → PCRF, $0/month to run, 931+ unique cloners in 14 days
- Under 200 words
- End: Free Palestine. 🌹
- Sign: Meeko Nerve Center
- No internal details, no email addresses

Reply body only."""
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

    return f"""Thanks for reaching out about Meeko Nerve Center. 🌸

This is a self-evolving SolarPunk AI system:
  • Congressional accountability tracking (STOCK Act trades)
  • Palestinian solidarity — 70% of revenue → PCRF
  • Gaza Rose generative art
  • $0/month to run, entirely on GitHub's free tier
  • 931+ unique cloners in 14 days

Fork it and run your own:
  {FORK_URL}
  Needs: HF_TOKEN + Gmail app password (3 minutes to set up)

Full system: {REPO_URL}

Free Palestine. 🌹
— Meeko Nerve Center"""


def send_reply(to_email: str, orig_subject: str, body: str) -> bool:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[gateway] No SMTP credentials')
        return False
    if is_placeholder_email(to_email):
        print(f'[gateway] BLOCKED placeholder address: {to_email}')
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


def append_log(entry: dict):
    p = DATA / 'email_gateway_log.json'
    try:
        data = json.loads(p.read_text()) if p.exists() else {'interactions': []}
        data.setdefault('interactions', []).append(entry)
        data['interactions'] = data['interactions'][-500:]
        p.write_text(json.dumps(data, indent=2))
    except:
        pass


def decode_header(value: str) -> str:
    try:
        from email.header import decode_header as _dh
        parts = _dh(value)
        return ''.join(
            p.decode(enc or 'utf-8', errors='replace') if isinstance(p, bytes) else p
            for p, enc in parts
        )
    except:
        return value


def check_inbox() -> list:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[gateway] No credentials, skipping inbox check')
        return []
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select('INBOX')
        _, data = mail.search(None, 'UNSEEN')
        ids = data[0].split()
        messages = []
        for eid in ids[-30:]:
            _, msg_data = mail.fetch(eid, '(RFC822)')
            if not msg_data or not msg_data[0]: continue
            msg = email_lib.message_from_bytes(msg_data[0][1])
            mail.store(eid, '+FLAGS', '\\Seen')  # Always mark read

            subject    = decode_header(msg.get('Subject', ''))
            from_raw   = msg.get('From', '')
            match      = re.search(r'[\w.+\-]+@[\w.\-]+\.[\w.]+', from_raw)
            from_email = match.group(0) if match else from_raw

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

            messages.append({'from_email': from_email, 'from_raw': from_raw,
                              'subject': subject, 'body': body[:3000]})
        mail.close(); mail.logout()
        return messages
    except Exception as e:
        print(f'[gateway] IMAP error: {e}')
        return []


def run():
    print(f'\n[gateway] Email Gateway v5 — {TODAY}')
    DATA.mkdir(parents=True, exist_ok=True)

    messages = check_inbox()
    print(f'[gateway] Unread: {len(messages)}')

    replied = 0; ignored_auto = 0; ignored_off = 0; ignored_dedup = 0

    for msg in messages:
        fe, subj, body = msg['from_email'], msg['subject'], msg['body']

        auto, reason = is_automated(fe, msg['from_raw'], subj, body)
        if auto:
            ignored_auto += 1
            append_log({'date': TODAY, 'from': fe[:40], 'subject': subj[:60],
                        'action': 'ignored_automated', 'reason': reason})
            continue

        if not is_on_topic(subj, body):
            ignored_off += 1
            append_log({'date': TODAY, 'from': fe[:40], 'subject': subj[:60], 'action': 'ignored_offtopic'})
            continue

        if was_replied_recently(fe):
            ignored_dedup += 1
            append_log({'date': TODAY, 'from': fe[:40], 'subject': subj[:60], 'action': 'ignored_dedup'})
            continue

        print(f'[gateway] Real human: {fe[:40]} | {subj[:50]}')
        reply = build_reply(fe, subj, body)
        ok    = send_reply(fe, subj, reply)
        action = 'replied' if ok else 'reply_failed'
        if ok: mark_replied(fe); replied += 1
        append_log({'date': TODAY, 'from': fe[:40], 'subject': subj[:60], 'action': action})

    print(f'[gateway] Replied: {replied} | Auto-ignored: {ignored_auto} | Off-topic: {ignored_off} | Dedup: {ignored_dedup}')


if __name__ == '__main__':
    run()
