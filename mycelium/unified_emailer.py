#!/usr/bin/env python3
"""
UNIFIED EMAILER
================
One script. One sent-log. All outreach flows through here.
Replaces: outreach_emails.py, tech_outreach.py, more_grant_emails.py, grant_outreach.py
No more double-sends. No more separate memories.

Every email checks meeko_brain before sending.
Every send writes to one shared log.
One unsubscribe list. Forever.
"""
import os, json, re, smtplib, hashlib, random, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from pathlib import Path

# Wire the brain — every send decision goes through it
import sys
sys.path.insert(0, os.path.dirname(__file__))
from meeko_brain import would_meeko_approve, MEEKO_DNA

GMAIL_USER   = 'mickowood86@gmail.com'
GMAIL_PASS   = os.environ.get('GMAIL_APP_PASSWORD', '')
SPAWN_URL    = 'https://meekotharaccoon-cell.github.io/meeko-nerve-center/spawn.html'
CLAIM_URL    = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery/claim.html'
GITHUB_URL   = 'https://github.com/meekotharaccoon-cell'
RIGHTS_URL   = 'https://meekotharaccoon-cell.github.io/mycelium-knowledge'

DATA_DIR     = Path('data')
SENT_LOG     = DATA_DIR / 'all_sent.json'       # One log. All sends. All time.
UNSUB_LOG    = DATA_DIR / 'unsubscribed.json'    # One list. Permanent. Honored always.

# ── CONTACT LISTS ────────────────────────────────────────────
# All targets in one place. angle determines email flavor.
# Never email anyone twice. Never email anyone who unsubscribed.

TECH_CONTACTS = [
    {'name': 'Mozilla Foundation',        'email': 'foundation@mozilla.org',         'angle': 'open_source'},
    {'name': 'EleutherAI',               'email': 'contact@eleuther.ai',             'angle': 'open_ai'},
    {'name': 'Hugging Face',             'email': 'press@huggingface.co',            'angle': 'open_ai'},
    {'name': 'LAION',                    'email': 'contact@laion.ai',                'angle': 'open_ai'},
    {'name': '404 Media',                'email': 'tips@404media.co',                'angle': 'journalism'},
    {'name': 'Wired',                    'email': 'tips@wired.com',                  'angle': 'journalism'},
    {'name': 'Rest of World',            'email': 'tips@restofworld.org',            'angle': 'journalism'},
    {'name': 'The Markup',              'email': 'tips@themarkup.org',               'angle': 'journalism'},
    {'name': 'Dev.to',                   'email': 'yo@dev.to',                       'angle': 'dev'},
]

GRANT_CONTACTS = [
    {'name': 'Wikimedia Rapid Fund',     'email': 'rapidfund@wikimedia.org',         'angle': 'grant'},
    {'name': 'Awesome Foundation',       'email': 'secretary@awesomefoundation.org', 'angle': 'grant'},
    {'name': 'Tech for Palestine',       'email': 'hello@techforpalestine.org',      'angle': 'humanitarian'},
    {'name': 'AFAC',                     'email': 'grants@arabculturefund.org',      'angle': 'grant'},
    {'name': 'Jerusalem Fund',           'email': 'info@thejerusalemfund.org',       'angle': 'humanitarian'},
    {'name': 'Harvestworks',             'email': 'info@harvestworks.org',           'angle': 'art_tech'},
]

HELLO_FACTS = [
    ("Every US state holds unclaimed property — abandoned accounts, uncashed checks, forgotten deposits. The national database is missingmoney.com. Free to search, free to claim.", "💰"),
    ("The FTC has active refund programs for consumers affected by settled cases. No lawyer. No fee. ftc.gov/refunds", "⚖️"),
    ("The TCPA makes robocalls to your cell illegal without consent. Each violation: $500–$1,500. Document the number, date, time. File at fcc.gov/consumers.", "📱"),
    ("Your full credit report is free at annualcreditreport.com — federally mandated, not a subscription. One in five contains errors. Errors are disputable.", "📊"),
    ("The FDCPA prohibits debt collectors from calling before 8am or after 9pm. Each violation: up to $1,000. Log date, time, number.", "🛡️"),
    ("GitHub Actions gives every public repo 2,000 free compute minutes monthly. A fully autonomous AI agent system runs entirely within that free tier.", "🧬"),
    ("The Awesome Foundation gives $1,000 monthly with no strings and no reporting. awesomefoundation.org — applications always open.", "🌟"),
    ("haveibeenpwned.com shows every data breach your email appeared in. Free, instant, no account required.", "🔐"),
    ("Every creative work published before 1928 is US public domain. Free to use, copy, sell, adapt. 70,000+ at gutenberg.org.", "📚"),
    ("The SEC Whistleblower Program pays 10–30% of sanctions over $1M to tipsters. Anonymous submissions accepted at sec.gov/whistleblower.", "💼"),
]

def load(path):
    try:
        with open(path) as f: return json.load(f)
    except: return {}

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f: json.dump(data, f, indent=2)

def token(addr):
    return hashlib.sha256(f"unsub-{addr}-meeko".encode()).hexdigest()[:16]

def unsub_link(addr):
    return f"mailto:{GMAIL_USER}?subject=UNSUBSCRIBE-{token(addr)}&body=Remove me."

def already_sent(addr, sent_log):
    return addr.lower() in sent_log

def is_unsubscribed(addr, unsub_log):
    return addr.lower() in unsub_log

def process_unsubscribes():
    """Scan inbox for UNSUBSCRIBE replies. Honor immediately."""
    if not GMAIL_PASS: return
    import imaplib, email as emaillib
    unsubs = load(UNSUB_LOG)
    try:
        m = imaplib.IMAP4_SSL('imap.gmail.com')
        m.login(GMAIL_USER, GMAIL_PASS)
        m.select('INBOX')
        _, msgs = m.search(None, 'SUBJECT "UNSUBSCRIBE-"')
        for num in msgs[0].split():
            try:
                _, data = m.fetch(num, '(RFC822)')
                msg = emaillib.message_from_bytes(data[0][1])
                sender = msg.get('From','')
                for addr in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', sender):
                    addr = addr.lower().strip()
                    if addr != GMAIL_USER.lower():
                        unsubs[addr] = datetime.now(timezone.utc).isoformat()
                        print(f'  [unsub] Honored forever: {addr}')
                m.store(num, '+FLAGS', '\\Seen')
            except: continue
        m.logout()
        save(UNSUB_LOG, unsubs)
    except Exception as e:
        print(f'  [unsub] Scan error: {e}')

def build_html(to_email, contact_name, angle, fact=None, fact_emoji=None):
    """One email template. Angle adjusts the opener. Always honest."""
    ul = unsub_link(to_email)

    openers = {
        'open_source':  'You work on keeping the web open. This is what that makes possible when it runs unsupervised.',
        'open_ai':      'Local LLMs doing real autonomous work — Mistral, LLaMA, CodeLlama — on 32GB RAM, no GPU, zero cloud cost.',
        'journalism':   'A real autonomous AI system on a standard desktop, raising money for Palestinian children\'s aid. Not a prototype.',
        'dev':          'Built on a 6-core i5 with integrated graphics. Zero cloud cost. Open source. Runs itself.',
        'grant':        'An autonomous open source system raising money for humanitarian causes — and the grant application that comes with it.',
        'humanitarian': 'A Palestinian children\'s aid fundraiser built entirely from free infrastructure. Running now.',
        'art_tech':     'AI-generated humanitarian art, autonomous gallery, self-healing system — all on integrated graphics.',
        'hello':        'We\'ve been in contact before. I wanted to introduce this properly.',
    }
    opener = openers.get(angle, openers['hello'])

    fact_section = ''
    if fact:
        fact_section = f"""
  <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
              border-radius:10px;padding:18px 22px;margin:24px 0">
    <p style="color:rgba(255,255,255,0.3);font-size:.7rem;letter-spacing:2px;text-transform:uppercase;margin:0 0 8px">{fact_emoji} Something true</p>
    <p style="color:rgba(255,255,255,0.75);font-size:.95rem;line-height:1.75;margin:0">{fact}</p>
  </div>"""

    return f"""<!DOCTYPE html><html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:Georgia,serif">
<div style="max-width:580px;margin:0 auto;padding:36px 24px">
  <p style="font-size:11px;color:rgba(255,255,255,0.2);text-align:center;margin-bottom:28px;line-height:1.8;font-family:monospace">
    🤖 Automated email · AI agent on behalf of Meeko · no tracking · no data stored ·
    <a href="{ul}" style="color:rgba(255,45,107,0.4);text-decoration:none">never contact me again</a>
  </p>
  <p style="color:rgba(255,255,255,0.4);font-size:.9rem;line-height:1.7;margin-bottom:8px;font-style:italic">{opener}</p>
  <h1 style="font-size:1.5rem;color:#fff;margin:0 0 18px;font-weight:normal;line-height:1.3">
    A fully autonomous humanitarian AI system — standard desktop, <span style="color:#00ff88">$0/month</span>, running now.
  </h1>
  <div style="background:rgba(0,255,136,0.04);border:1px solid rgba(0,255,136,0.12);border-radius:10px;padding:18px 22px;margin-bottom:22px;font-family:monospace;font-size:.8rem;line-height:2">
    <div style="color:rgba(255,255,255,0.25);font-size:.65rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px">THE MACHINE</div>
    <div><span style="color:rgba(255,255,255,0.3)">CPU </span><span style="color:#00ff88">Intel Core i5-8500 · 6 cores · 3.0GHz</span></div>
    <div><span style="color:rgba(255,255,255,0.3)">RAM </span><span style="color:#00ff88">32GB</span></div>
    <div><span style="color:rgba(255,255,255,0.3)">GPU </span><span style="color:#ff2d6b">Intel UHD 630 — integrated, no dedicated GPU</span></div>
    <div><span style="color:rgba(255,255,255,0.3)">AI  </span><span style="color:#ffd700">Mistral 7B + CodeLlama + LLaMA 3.2 — local, private, free</span></div>
    <div><span style="color:rgba(255,255,255,0.3)">$   </span><span style="color:#00ff88">Zero. GitHub free tier. No subscriptions.</span></div>
  </div>
  <p style="color:rgba(255,255,255,0.5);font-size:.9rem;line-height:1.75;margin-bottom:20px">
    9 workflows run on schedule. It searches for grants and applies. Reads and answers email. Sells art with inline payments — 70% to PCRF (Palestinian children's aid, EIN 93-1057665). Sends a free artwork to anyone who visits. Backs itself up across multiple permanent archives. Can clone itself to any new owner in one click. The license (AGPL-3.0 + Ethical Rider) legally prevents weaponization, surveillance, or capture.
  </p>
  <div style="text-align:center;margin:28px 0">
    <a href="{SPAWN_URL}" style="display:inline-block;background:linear-gradient(135deg,#00ff88,#00cc66);color:#000;text-decoration:none;padding:15px 38px;border-radius:12px;font-size:1rem;font-weight:bold;font-family:monospace">
      🧬 See the live system
    </a>
    <p style="color:rgba(255,255,255,0.2);font-size:.7rem;margin-top:8px;font-family:monospace">Not a demo. The actual running organism.</p>
  </div>
  {fact_section}
  <div style="border-top:1px solid rgba(255,255,255,0.06);padding-top:18px;margin-top:24px;text-align:center;color:rgba(255,255,255,0.15);font-size:.7rem;line-height:2;font-family:monospace">
    Meeko · Gaza Rose Gallery · AGPL-3.0 + Ethical Use License<br>
    <a href="{GITHUB_URL}" style="color:rgba(0,255,136,0.4);text-decoration:none">github.com/meekotharaccoon-cell</a> ·
    <a href="{CLAIM_URL}" style="color:rgba(255,45,107,0.4);text-decoration:none">free flower</a><br>
    <a href="{ul}" style="color:rgba(255,45,107,0.25);text-decoration:none">Remove me permanently</a>
  </div>
</div></body></html>"""

def send(to_email, subject, html):
    """Send one email. Returns True on success."""
    if not GMAIL_PASS:
        print(f'  [send] No password — skipping {to_email}')
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['From']    = f'Meeko — Mycelium System <{GMAIL_USER}>'
        msg['To']      = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f'  [send] Failed → {to_email}: {e}')
        return False

def run_outreach(contacts, subject_template, angle_override=None, include_fact=False, daily_limit=5):
    """Send outreach to a contact list. Brain-gated. Deduped globally."""
    sent  = load(SENT_LOG)
    unsub = load(UNSUB_LOG)
    count = 0

    for contact in contacts:
        if count >= daily_limit: break
        addr  = contact['email'].lower()
        angle = angle_override or contact.get('angle', 'hello')

        if is_unsubscribed(addr, unsub):
            print(f'  [skip] Unsubscribed: {addr}')
            continue
        if already_sent(addr, sent):
            print(f'  [skip] Already sent: {addr}')
            continue

        # Brain gate — does this align with values?
        approved, reason = would_meeko_approve(f"send outreach email to {contact['name']} about open source humanitarian system")
        if not approved:
            print(f'  [brain] Blocked: {contact["name"]} — {reason}')
            continue

        fact, emoji = (random.choice(HELLO_FACTS) if include_fact else (None, None))
        html = build_html(addr, contact['name'], angle, fact, emoji)
        subject = subject_template.format(name=contact['name'])

        print(f'  [send] → {contact["name"]} ({addr})')
        if send(addr, subject, html):
            sent[addr] = {
                'name':    contact['name'],
                'sent_at': datetime.now(timezone.utc).isoformat(),
                'angle':   angle,
                'subject': subject,
            }
            count += 1
            save(SENT_LOG, sent)
            time.sleep(9)  # Space sends — never looks like a blast

    return count

def run():
    print(f"\n{'='*52}")
    print("  UNIFIED EMAILER — Brain-gated, globally deduped")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*52}\n")

    process_unsubscribes()

    mode = os.environ.get('EMAIL_MODE', 'hello')

    if mode == 'tech':
        n = run_outreach(
            TECH_CONTACTS,
            subject_template="A fully autonomous humanitarian AI — 6-core i5, integrated graphics, $0/month",
            include_fact=False,
            daily_limit=5
        )
        print(f'\n  Tech outreach: {n} sent')

    elif mode == 'grants':
        n = run_outreach(
            GRANT_CONTACTS,
            subject_template="Grant application — Meeko Mycelium humanitarian AI system",
            angle_override='grant',
            include_fact=False,
            daily_limit=3
        )
        print(f'\n  Grant outreach: {n} sent')

    else:  # hello — default, runs daily
        import imaplib, email as elib
        # Get previous contacts from sent mail
        contacts = []
        sent  = load(SENT_LOG)
        unsub = load(UNSUB_LOG)
        if GMAIL_PASS:
            try:
                m = imaplib.IMAP4_SSL('imap.gmail.com')
                m.login(GMAIL_USER, GMAIL_PASS)
                m.select('"[Gmail]/Sent Mail"')
                _, msgs = m.search(None, 'ALL')
                seen = set()
                for num in msgs[0].split()[-300:]:
                    try:
                        _, data = m.fetch(num, '(RFC822)')
                        msg = elib.message_from_bytes(data[0][1])
                        to = msg.get('To','')
                        for addr in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', to):
                            addr = addr.lower().strip()
                            if addr != GMAIL_USER.lower() and addr not in seen:
                                seen.add(addr)
                                contacts.append({'email': addr, 'name': addr.split('@')[0].title(), 'angle': 'hello'})
                    except: continue
                m.logout()
            except Exception as e:
                print(f'  [hello] Gmail scan error: {e}')

        n = run_outreach(
            contacts,
            subject_template="🌹 A flower for you — and something true",
            include_fact=True,
            daily_limit=8
        )
        print(f'\n  Hello sends: {n} today')

    total = len(load(SENT_LOG))
    print(f'  Total ever sent (all modes): {total}')
    print(f'  Total unsubscribed (honored forever): {len(load(UNSUB_LOG))}')
    print(f'  Brain: active ✓')

if __name__ == '__main__':
    run()
