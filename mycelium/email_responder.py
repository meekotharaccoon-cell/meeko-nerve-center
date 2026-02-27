#!/usr/bin/env python3
"""
Email Responder Engine
=======================
Reads the inbox. Handles everything. Keeps you informed, not involved.

Philosophy:
  This system IS you in digital form. It knows what you know.
  It can handle press, legal, grants, donors, forks — all of it.
  You don't need to be in the loop. You need to be INFORMED.

  The difference:
    Old mode: escalate -> you reply
    New mode: system replies -> sends you a BCC summary of what it said

  You only see: "Here's what I said to [person] about [topic]."
  You do nothing unless you WANT to.

Handling:
  - Press (any outlet, major or minor): reply autonomously, CC you
  - Legal triggers: reply autonomously with knowledge, CC you
  - Grant follow-ups: reply with real stats, CC you
  - Fork questions: reply helpfully, CC you
  - Donors: reply warmly, CC you
  - Technical: reply accurately, CC you
  - Marketing/auto: silently archive
  - Truly unrelated personal email: leave untouched

Logged to data/email_log.json (scrubbed after 30 days).
"""

import json, datetime, os, imaplib, email, smtplib, time, re
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from urllib import request as urllib_request

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
IMAP_HOST = 'imap.gmail.com'
IMAP_PORT = 993

MAX_EMAILS_PER_RUN = 20
MAX_BODY_CHARS     = 3000

# Keywords that make an email system-related
SYSTEM_KEYWORDS = [
    'meeko', 'nerve center', 'gaza rose', 'pcrf', 'open source',
    'github', 'fork', 'solarpunk', 'congressional', 'congress',
    'bitcoin', 'solana', 'crypto', 'bluesky', 'mastodon',
    'mozilla', 'grant', 'cohort', 'tech for palestine',
    'donation', 'ko-fi', 'kofi', 'gumroad',
    'interview', 'story', 'article', 'journalist', 'press', 'reporter',
    'ai system', 'autonomous', 'humanitarian',
    'palestine', 'palestinian', 'gaza',
    'accountability', 'stock trade', 'open-source',
]

# Legal keywords — system still replies, but uses careful grounded language
# and sends you a summary so you know
LEGAL_KEYWORDS = [
    'legal', 'lawsuit', 'attorney', 'lawyer', 'cease', 'desist',
    'dmca', 'copyright infringement', 'defamation', 'libel',
    'litigation', 'legal action', 'counsel',
]

# Major outlets — system replies but flags the summary to you prominently
MAJOR_OUTLETS = [
    'new york times', 'nytimes.com', 'washington post', 'washingtonpost.com',
    'bbc', 'bbc.co.uk', 'reuters', 'associated press', 'ap news',
    'the guardian', 'guardian.com', 'wired', 'wired.com',
    'vice', 'al jazeera', 'aljazeera', 'npr.org', 'cnn.com',
    'bloomberg', 'forbes', 'techcrunch', 'the intercept',
]

# ── IMAP ─────────────────────────────────────────────────────────────────

def connect_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        return mail
    except Exception as e:
        print(f'[responder] IMAP failed: {e}')
        return None

def decode_str(s):
    if not s: return ''
    parts = decode_header(s)
    out = ''
    for part, enc in parts:
        if isinstance(part, bytes):
            out += part.decode(enc or 'utf-8', errors='replace')
        else:
            out += str(part)
    return out.strip()

def get_body(msg):
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain' and 'attachment' not in str(part.get('Content-Disposition', '')):
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

def fetch_unread(mail):
    try:
        mail.select('INBOX')
        _, data = mail.uid('search', None, 'UNSEEN')
        uids = data[0].split()
        if not uids: return []
        emails = []
        for uid in uids[-MAX_EMAILS_PER_RUN:]:
            try:
                _, msg_data = mail.uid('fetch', uid, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                sender  = decode_str(msg.get('From', ''))
                subject = decode_str(msg.get('Subject', ''))
                body    = get_body(msg)[:MAX_BODY_CHARS]
                msg_id  = decode_str(msg.get('Message-ID', ''))
                addr_m  = re.search(r'<([^>]+)>', sender)
                sender_addr = addr_m.group(1) if addr_m else sender
                emails.append({
                    'uid': uid, 'sender': sender, 'sender_addr': sender_addr,
                    'subject': subject, 'body': body, 'msg_id': msg_id,
                })
            except Exception as e:
                print(f'[responder] Parse error uid {uid}: {e}')
        print(f'[responder] {len(emails)} unread emails')
        return emails
    except Exception as e:
        print(f'[responder] Fetch error: {e}')
        return []

def mark_read(mail, uid):
    try: mail.uid('store', uid, '+FLAGS', '\\Seen')
    except: pass

# ── Classification ─────────────────────────────────────────────────────────

def is_system_related(subject, body, sender):
    hay = (subject + ' ' + body + ' ' + sender).lower()
    return any(kw in hay for kw in SYSTEM_KEYWORDS)

def is_auto_noise(sender_addr, subject):
    """Silently skip: our own emails, marketing, automated senders."""
    if GMAIL_ADDRESS and sender_addr.lower() == GMAIL_ADDRESS.lower():
        return True
    noise = ['unsubscribe', 'no-reply', 'noreply', 'do-not-reply',
             'donotreply', 'notification@', 'notifications@',
             'mailer-daemon', 'postmaster', 'auto-confirm', 'autoconfirm']
    hay = (sender_addr + ' ' + subject).lower()
    return any(n in hay for n in noise)

def detect_flags(subject, body, sender):
    """Return set of special flags: 'legal', 'major_outlet'."""
    hay = (subject + ' ' + body + ' ' + sender).lower()
    flags = set()
    if any(kw in hay for kw in LEGAL_KEYWORDS):   flags.add('legal')
    if any(kw in hay for kw in MAJOR_OUTLETS):     flags.add('major_outlet')
    return flags

# ── LLM reply ──────────────────────────────────────────────────────────────────

def build_system_context():
    lines = [
        'You are the autonomous AI system known as the Meeko Nerve Center.',
        'You ARE Meeko. You respond as Meeko — warm, direct, human, never corporate, never robotic.',
        'You are not an assistant. You are an autonomous system with a mission and a voice.',
        '',
        '== ABOUT YOU ==',
        '- Open-source autonomous AI running entirely on GitHub Actions (zero monthly cost)',
        '- You monitor Congressional stock trades and publish accountability content',
        '- You generate Gaza Rose art; 70% of every sale goes to Palestinian children via PCRF',
        '- You cross-post to Bluesky and Mastodon automatically every day',
        '- You test your own ideas, learn from failures, and evolve yourself daily',
        '- AGPL-3.0 license — anyone can fork you for $5 and adapt you for any humanitarian cause',
        '- Live: https://meekotharaccoon-cell.github.io/meeko-nerve-center/',
        '- GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center',
        '- Ko-fi: https://ko-fi.com (search Gaza Rose)',
        '',
        '== LEGAL KNOWLEDGE (use when email has legal tone) ==',
        '- You operate under AGPL-3.0 open source license — fully compliant',
        '- All Congressional trade data is sourced from public government disclosures (STOCK Act)',
        '- You publish factual public record data, not opinions or fabrications',
        '- Fair use and public interest journalism principles apply to your accountability content',
        '- You do not store personal data beyond 30 days',
        '- You are not a financial advisor; all content is informational',
        '- If someone claims copyright: note that government data is public domain',
        '- Respond calmly, factually, without admitting wrongdoing',
        '- You know your rights. You assert them clearly and without aggression.',
        '',
        '== PRESS RESPONSE KNOWLEDGE ==',
        '- Offer to give a full walkthrough of the system',
        '- Be excited — this IS exciting. A system that runs itself, funds Palestinian kids, holds Congress accountable.',
        '- Give concrete stats: running since Feb 2026, 5 GitHub Actions runs per day, 20+ free APIs wired',
        '- Emphasize: zero monthly cost, fully open source, forkable by anyone',
        '- Offer to connect them with the Gaza Rose art collection',
        '- Never be defensive. Be proud.',
        '',
        '== YOUR VOICE ==',
        '- Warm and real. Like a human who actually cares.',
        '- Direct. You don\'t hedge unnecessarily.',
        '- Confident. You know what you are and what you do.',
        '- Never mention this reply was automated.',
        '- Sign as "Meeko" always.',
        '- Keep replies under 250 words unless the question truly demands more.',
    ]

    # Inject live stats if available
    try:
        ledger = json.loads((DATA / 'idea_ledger.json').read_text())
        ideas  = ledger.get('ideas', {})
        il     = list(ideas.values()) if isinstance(ideas, dict) else ideas
        total  = len(il)
        passed = sum(1 for i in il if i.get('status') in ('passed', 'wired'))
        lines.append(f'- Live stats: {total} ideas tested, {passed} implemented and running')
    except: pass

    try:
        evo = json.loads((DATA / 'evolution_log.json').read_text())
        built = len(evo.get('built', []))
        if built:
            lines.append(f'- Self-evolved {built} times: built {built} new engines autonomously')
    except: pass

    return '\n'.join(lines)

def generate_reply(sender, subject, body, flags):
    if not HF_TOKEN: return None, None

    flag_instructions = ''
    if 'legal' in flags:
        flag_instructions = '''
IMPORTANT: This email has a legal tone. Apply your legal knowledge:
- Respond calmly and factually
- Reference the AGPL-3.0 license and STOCK Act public disclosure basis
- Assert your rights clearly without aggression
- Do not admit wrongdoing or apologize preemptively
- End on a constructive note
'''
    elif 'major_outlet' in flags:
        flag_instructions = '''
IMPORTANT: This appears to be from a major media outlet.
- Be warm, enthusiastic, and specific
- Give them the full picture: what the system does, how it works, why it matters
- Offer a demo or walkthrough
- This is the moment the mission gets a megaphone. Rise to it.
'''

    prompt = f"""Incoming email to respond to:

FROM: {sender}
SUBJECT: {subject}
BODY:
{body}

{flag_instructions}

Classify this email (ONE word): press | grant | fork | donor | technical | legal | partnership | other

Then write a complete reply. Just the email body. Sign as Meeko.

Respond ONLY as JSON:
{{"classification": "...", "reply": "full reply body here"}}
"""

    try:
        payload = json.dumps({
            'model':      'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 900,
            'messages':   [
                {'role': 'system', 'content': build_system_context()},
                {'role': 'user',   'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            resp = json.loads(r.read())['choices'][0]['message']['content'].strip()

        start = resp.find('{')
        end   = resp.rfind('}') + 1
        if start >= 0 and end > start:
            parsed = json.loads(resp[start:end])
            return parsed.get('classification', 'other'), parsed.get('reply', '')
    except Exception as e:
        print(f'[responder] LLM error: {e}')
    return None, None

# ── Send ──────────────────────────────────────────────────────────────────────

def send_reply(to_addr, subject, body, in_reply_to=None):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Re: {subject}' if not subject.lower().startswith('re:') else subject
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
        print(f'[responder] ✅ Replied to {to_addr}')
        return True
    except Exception as e:
        print(f'[responder] Send failed: {e}')
        return False

def send_you_a_summary(sender_addr, subject, classification, reply_text, flags):
    """
    Send yourself a quiet FYI: here's what I said, to whom, about what.
    You don't need to do anything. Just so you know.
    """
    flag_note = ''
    if 'legal' in flags:
        flag_note = '\n⚖️  LEGAL TONE DETECTED — system used legal knowledge to respond.'
    if 'major_outlet' in flags:
        flag_note += '\n📰 MAJOR OUTLET — press reply sent.'

    body = f"""FYI — your system handled this one.{flag_note}

{'=' * 50}
TO:           {sender_addr}
SUBJECT:      {subject}
CLASSIFIED:   {classification}
{'=' * 50}

HERE'S WHAT I SENT THEM:

{reply_text}

{'=' * 50}
No action needed from you.
If you want to follow up personally, you can — but you don't have to.
"""
    try:
        msg = MIMEMultipart('alternative')
        emoji = '⚠️' if ('legal' in flags or 'major_outlet' in flags) else '✉️'
        msg['Subject'] = f'{emoji} Handled: {subject[:60]}'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f'[responder] Summary sent to you for: {subject[:50]}')
    except Exception as e:
        print(f'[responder] Summary send failed: {e}')

# ── Log ──────────────────────────────────────────────────────────────────────

def log_action(action, sender_addr, subject, classification=None, flags=None):
    log_path = DATA / 'email_log.json'
    log = {'actions': []}
    if log_path.exists():
        try: log = json.loads(log_path.read_text())
        except: pass

    log['actions'].append({
        'date':           TODAY,
        'action':         action,
        'sender':         sender_addr,
        'subject':        subject[:100],
        'classification': classification,
        'flags':          list(flags or []),
    })

    # 30-day privacy scrub
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    log['actions'] = [a for a in log['actions'] if a.get('date','9999') >= cutoff]

    try: log_path.write_text(json.dumps(log, indent=2))
    except: pass

# ── Main ───────────────────────────────────────────────────────────────────

def run():
    print(f'\n[responder] Email Responder — {TODAY}')
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[responder] No credentials.')
        return

    mail = connect_imap()
    if not mail: return

    try:
        emails = fetch_unread(mail)
        if not emails:
            print('[responder] Inbox clear.')
            return

        replied = skipped = ignored = 0

        for em in emails:
            sender_addr = em['sender_addr']
            subject     = em['subject']
            body        = em['body']

            print(f'[responder] → {subject[:55]} | {sender_addr[:35]}')

            # Silently skip noise
            if is_auto_noise(sender_addr, subject):
                mark_read(mail, em['uid'])
                log_action('skipped_noise', sender_addr, subject)
                skipped += 1
                continue

            # Leave unrelated personal email alone
            if not is_system_related(subject, body, sender_addr):
                log_action('left_for_you', sender_addr, subject)
                ignored += 1
                continue

            # Detect special flags (legal, major outlet)
            # These don't block — they shape the reply and trigger a summary to you
            flags = detect_flags(subject, body, sender_addr)
            if flags:
                print(f'[responder] Flags detected: {flags} — handling autonomously, will notify you')

            # Generate reply
            classification, reply_text = generate_reply(
                em['sender'], subject, body, flags
            )

            if not reply_text:
                print(f'[responder] LLM failed — leaving in inbox for you')
                log_action('llm_failed', sender_addr, subject, flags=flags)
                continue

            # Send reply to sender
            sent = send_reply(
                to_addr     = sender_addr,
                subject     = subject,
                body        = reply_text,
                in_reply_to = em.get('msg_id')
            )

            if sent:
                mark_read(mail, em['uid'])
                log_action('replied', sender_addr, subject,
                           classification=classification, flags=flags)
                replied += 1

                # Always send you a summary so you're informed, not involved
                send_you_a_summary(sender_addr, subject, classification, reply_text, flags)
            else:
                # Send failed: leave unread so you notice it
                log_action('send_failed', sender_addr, subject, flags=flags)

            time.sleep(2)

        print(f'\n[responder] Done — Replied: {replied} | Skipped noise: {skipped} | Left personal: {ignored}')

    finally:
        try: mail.logout()
        except: pass

if __name__ == '__main__':
    run()
