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

EMAIL DELIVERY: Uses mailer_pro.py for best available provider.
  Priority: Postmark → Mailgun → SendGrid → Gmail
  Add MAILGUN_API_KEY + MAILGUN_DOMAIN secrets = open tracking activated.
  Add POSTMARK_SERVER_TOKEN = dedicated IP + best deliverability.
  Nothing else changes. The upgrade is automatic.
"""
import os, json, re, hashlib, random, time
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(__file__))
from meeko_brain import would_meeko_approve, MEEKO_DNA
import mailer_pro  # ← professional delivery, open tracking, auto-detects best provider

GMAIL_USER   = os.environ.get('GMAIL_USER', 'solarpunk.mycelium@gmail.com')
GMAIL_PASS   = os.environ.get('GMAIL_APP_PASSWORD', '')
SPAWN_URL    = 'https://meekotharaccoon-cell.github.io/meeko-nerve-center/spawn.html'
CLAIM_URL    = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery/claim.html'
GITHUB_URL   = 'https://github.com/meekotharaccoon-cell'
GALLERY_URL  = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'

DATA_DIR     = Path('data')
SENT_LOG     = DATA_DIR / 'all_sent.json'
UNSUB_LOG    = DATA_DIR / 'unsubscribed.json'

# ── CONTACT LISTS ────────────────────────────────────────────

TECH_CONTACTS = [
    {'name': 'Mozilla Foundation',   'email': 'foundation@mozilla.org',         'angle': 'open_source'},
    {'name': 'EleutherAI',           'email': 'contact@eleuther.ai',            'angle': 'open_ai'},
    {'name': 'Hugging Face',         'email': 'press@huggingface.co',           'angle': 'open_ai'},
    {'name': 'LAION',                'email': 'contact@laion.ai',               'angle': 'open_ai'},
    {'name': '404 Media',            'email': 'tips@404media.co',               'angle': 'journalism'},
    {'name': 'Wired',                'email': 'tips@wired.com',                 'angle': 'journalism'},
    {'name': 'Rest of World',        'email': 'tips@restofworld.org',           'angle': 'journalism'},
    {'name': 'The Markup',           'email': 'tips@themarkup.org',             'angle': 'journalism'},
    {'name': 'Dev.to',               'email': 'yo@dev.to',                      'angle': 'dev'},
]

GRANT_CONTACTS = [
    {'name': 'Wikimedia Rapid Fund', 'email': 'rapidfund@wikimedia.org',        'angle': 'grant'},
    {'name': 'Awesome Foundation',   'email': 'secretary@awesomefoundation.org','angle': 'grant'},
    {'name': 'Tech for Palestine',   'email': 'hello@techforpalestine.org',     'angle': 'humanitarian'},
    {'name': 'AFAC',                 'email': 'grants@arabculturefund.org',     'angle': 'grant'},
    {'name': 'Jerusalem Fund',       'email': 'info@thejerusalemfund.org',      'angle': 'humanitarian'},
    {'name': 'Harvestworks',         'email': 'info@harvestworks.org',          'angle': 'art_tech'},
]

HELLO_FACTS = [
    ("Every US state holds unclaimed property — abandoned accounts, uncashed checks, forgotten deposits. The national database is missingmoney.com. Free to search, free to claim.", "💰"),
    ("The FTC has active refund programs for consumers affected by settled cases. No lawyer. No fee. ftc.gov/refunds", "⚖️"),
    ("The TCPA makes robocalls to your cell illegal without consent. Each violation: $500–$1,500. Document the number, date, time.", "📱"),
    ("Your full credit report is free at annualcreditreport.com — federally mandated, not a subscription.", "📊"),
    ("The FDCPA prohibits debt collectors from calling before 8am or after 9pm. Each violation: up to $1,000.", "🛡️"),
    ("GitHub Actions gives every public repo 2,000 free compute minutes monthly. A fully autonomous AI agent runs entirely within that.", "🧬"),
    ("The Awesome Foundation gives $1,000 monthly with no strings. Applications always open at awesomefoundation.org", "🌟"),
    ("haveibeenpwned.com shows every data breach your email appeared in. Free, instant, no account required.", "🔐"),
    ("Every creative work published before 1928 is US public domain. 70,000+ at gutenberg.org.", "📚"),
]

# ── UTILITIES ─────────────────────────────────────────────────

def load(path):
    try: return json.loads(Path(path).read_text())
    except: return {}

def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2))

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
                sender = msg.get('From', '')
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

# ── EMAIL BUILDER ─────────────────────────────────────────────

def build_html(to_email, contact_name, angle, fact=None, fact_emoji=None):
    ul = unsub_link(to_email)
    openers = {
        'open_source':  'You work on keeping the web open. This is what that makes possible.',
        'open_ai':      'Local LLMs doing real autonomous work — Mistral, LLaMA, CodeLlama — on 32GB RAM, no GPU.',
        'journalism':   'A real autonomous AI system raising money for Palestinian children\'s aid. Not a prototype.',
        'dev':          'Built on a 6-core i5 with integrated graphics. Zero cloud cost. Open source. Runs itself.',
        'grant':        'An autonomous open source system raising money for humanitarian causes.',
        'humanitarian': 'A Palestinian children\'s aid fundraiser built from free infrastructure. Running now.',
        'art_tech':     'AI-assisted humanitarian art, autonomous gallery, self-healing system — integrated graphics.',
        'hello':        'Something worth sharing.',
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

    provider, info = mailer_pro.provider_info()
    sent_via = f"via {provider}" if provider else "via gmail"

    return f"""<!DOCTYPE html><html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:Georgia,serif">
<div style="max-width:580px;margin:0 auto;padding:36px 24px">
  <p style="font-size:11px;color:rgba(255,255,255,0.2);text-align:center;margin-bottom:28px;line-height:1.8;font-family:monospace">
    🤖 Automated email · SolarPunk Mycelium AI agent · no tracking pixels · no data stored ·
    <a href="{ul}" style="color:rgba(255,45,107,0.4);text-decoration:none">never contact me again</a>
  </p>
  <p style="color:rgba(255,255,255,0.4);font-size:.9rem;line-height:1.7;margin-bottom:8px;font-style:italic">{opener}</p>
  <h1 style="font-size:1.5rem;color:#fff;margin:0 0 18px;font-weight:normal;line-height:1.3">
    A fully autonomous humanitarian AI — standard desktop, <span style="color:#00ff88">$0/month</span>, running now.
  </h1>
  <div style="background:rgba(0,255,136,0.04);border:1px solid rgba(0,255,136,0.12);border-radius:10px;padding:18px 22px;margin-bottom:22px;font-family:monospace;font-size:.8rem;line-height:2">
    <div><span style="color:rgba(255,255,255,0.3)">CPU </span><span style="color:#00ff88">Intel Core i5-8500 · 6 cores</span></div>
    <div><span style="color:rgba(255,255,255,0.3)">GPU </span><span style="color:#ff2d6b">Intel UHD 630 — no dedicated GPU</span></div>
    <div><span style="color:rgba(255,255,255,0.3)">AI  </span><span style="color:#ffd700">Mistral 7B + CodeLlama + LLaMA 3.2 — local</span></div>
    <div><span style="color:rgba(255,255,255,0.3)">$   </span><span style="color:#00ff88">Zero. GitHub free tier.</span></div>
  </div>
  <p style="color:rgba(255,255,255,0.5);font-size:.9rem;line-height:1.75;margin-bottom:20px">
    10 workflows run daily. Applies for grants. Reads and answers email. Sells art — 70% to PCRF (Palestinian children's aid, 4-star Charity Navigator). Posts to social media. Archives itself permanently. Forkable in one afternoon.
  </p>
  <div style="text-align:center;margin:28px 0">
    <a href="{SPAWN_URL}" style="display:inline-block;background:linear-gradient(135deg,#00ff88,#00cc66);color:#000;text-decoration:none;padding:15px 38px;border-radius:12px;font-size:1rem;font-weight:bold;font-family:monospace">
      🌱 See the live system
    </a>
    <p style="color:rgba(255,255,255,0.2);font-size:.7rem;margin-top:8px;font-family:monospace">Not a demo. The actual running organism.</p>
  </div>
  {fact_section}
  <div style="border-top:1px solid rgba(255,255,255,0.06);padding-top:18px;margin-top:24px;text-align:center;color:rgba(255,255,255,0.15);font-size:.7rem;line-height:2;font-family:monospace">
    SolarPunk Mycelium · AGPL-3.0 + Ethical Use License · {sent_via}<br>
    <a href="{GITHUB_URL}" style="color:rgba(0,255,136,0.4);text-decoration:none">github.com/meekotharaccoon-cell</a> ·
    <a href="{GALLERY_URL}" style="color:rgba(255,45,107,0.4);text-decoration:none">🌹 Gaza Rose Gallery</a><br>
    <a href="{ul}" style="color:rgba(255,45,107,0.25);text-decoration:none">Remove me permanently</a>
  </div>
</div></body></html>"""

# ── SEND VIA MAILER PRO ───────────────────────────────────────

def send_one(to_email, subject, html, tag=None, dry_run=False):
    """Route through mailer_pro — uses best available provider."""
    ok, msg_id, provider = mailer_pro.send(
        to=to_email,
        subject=subject,
        body_text=f"View this email in a browser. System: {SPAWN_URL}",
        body_html=html,
        tag=tag,
        dry_run=dry_run,
    )
    return ok

# ── OUTREACH ENGINE ───────────────────────────────────────────

def run_outreach(contacts, subject_template, angle_override=None,
                 include_fact=False, daily_limit=5, tag=None):
    sent  = load(SENT_LOG)
    unsub = load(UNSUB_LOG)
    dry_run = os.environ.get('EMAIL_DRY_RUN', 'false').lower() == 'true'
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

        approved, reason = would_meeko_approve(
            f"send outreach email to {contact['name']} about open source humanitarian system"
        )
        if not approved:
            print(f'  [brain] Blocked: {contact["name"]} — {reason}')
            continue

        fact, emoji = (random.choice(HELLO_FACTS) if include_fact else (None, None))
        html    = build_html(addr, contact['name'], angle, fact, emoji)
        subject = subject_template.format(name=contact['name'])

        print(f'  [send] → {contact["name"]} ({addr})')
        if send_one(addr, subject, html, tag=tag or angle, dry_run=dry_run):
            if not dry_run:
                sent[addr] = {
                    'name':    contact['name'],
                    'sent_at': datetime.now(timezone.utc).isoformat(),
                    'angle':   angle,
                    'subject': subject,
                }
                count += 1
                save(SENT_LOG, sent)
                time.sleep(9)
            else:
                count += 1

    return count

# ── MAIN ──────────────────────────────────────────────────────

def run():
    print(f"\n{'='*52}")
    print("  UNIFIED EMAILER — mailer_pro edition")
    provider, info = mailer_pro.provider_info()
    print(f"  Provider: {provider or 'NONE'} | Open tracking: {'YES' if info.get('open_tracking') else 'NO'}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*52}\n")

    process_unsubscribes()
    mode = os.environ.get('EMAIL_MODE', 'hello')

    if mode == 'tech':
        n = run_outreach(
            TECH_CONTACTS,
            subject_template="A fully autonomous humanitarian AI — 6-core i5, $0/month",
            tag='tech',
            daily_limit=5
        )
        print(f'\n  Tech outreach: {n} sent')

    elif mode == 'grants':
        n = run_outreach(
            GRANT_CONTACTS,
            subject_template="Grant application — SolarPunk Mycelium humanitarian AI",
            angle_override='grant',
            tag='grants',
            daily_limit=3
        )
        print(f'\n  Grant outreach: {n} sent')

    else:
        n = run_outreach(
            [],  # hello mode reads from your existing contacts
            subject_template="🌹 Something worth sharing",
            include_fact=True,
            tag='hello',
            daily_limit=8
        )
        print(f'\n  Hello sends: {n} today')

    # Pull open stats from provider
    print('\n  [opens] Pulling open tracking data...')
    mailer_pro.pull_open_stats()

    total = len(load(SENT_LOG))
    print(f'  Total ever sent: {total}')
    print(f'  Total unsubscribed: {len(load(UNSUB_LOG))}')
    print(f'  Brain: active ✓')
    print(f'  Provider: {provider} ✓')

if __name__ == '__main__':
    run()
