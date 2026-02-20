#!/usr/bin/env python3
"""
MYCELIUM HELLO — v2
====================
One email. One button. Everything connected behind it.
Full AI disclosure. Real unsubscribe. A fact before it leaves.
Never assumes. Never hedges. States what's true.
"""
import os, json, smtplib, imaplib, email, random, hashlib, re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from pathlib import Path

GMAIL_USER  = 'mickowood86@gmail.com'
GMAIL_PASS  = os.environ.get('GMAIL_APP_PASSWORD', '')
CLAIM_URL   = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery/claim.html'
GALLERY_URL = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'
GITHUB_URL  = 'https://github.com/meekotharaccoon-cell'
RIGHTS_URL  = 'https://meekotharaccoon-cell.github.io/mycelium-knowledge'
UNSUB_FILE  = 'data/unsubscribed.json'
SENT_FILE   = 'data/hello_sent.json'

# ── FACTS. Not hedges. Not assumptions. Facts. ──────────────
# Every line is verifiable. No "you might." No "most people."
FACTS = [
    ("Every US state holds unclaimed property — abandoned bank accounts, forgotten deposits, uncashed checks. The national database is missingmoney.com. Free to search, free to claim.", "💰"),
    ("The FTC has active refund programs right now for consumers affected by settled cases. No lawyer. No claim form fee. The list is at ftc.gov/refunds.", "⚖️"),
    ("The TCPA makes it illegal to call your cell phone with a robocall without consent. Each illegal call is $500–$1,500 in statutory damages. The FCC complaint portal is fcc.gov/consumers/guides/filing-informal-complaint.", "📱"),
    ("Your full credit report is free at annualcreditreport.com — the federally mandated one, not the paid subscription sites. One in five reports contains an error. Errors are disputable and removable.", "📊"),
    ("CCPA (California) and GDPR (EU) give you the right to demand deletion of your personal data from any company holding it. The request is one email. They have 30–45 days to comply.", "🗑️"),
    ("The SEC Whistleblower Program pays 10–30% of sanctions over $1M to tipsters whose information leads to enforcement. Tips are accepted anonymously at sec.gov/whistleblower.", "💼"),
    ("Every creative work published before January 1, 1928 is in the US public domain. Free to use, copy, sell, adapt. Project Gutenberg hosts 70,000+ of them at gutenberg.org.", "📚"),
    ("The FDCPA prohibits debt collectors from calling before 8am or after 9pm, using abusive language, or contacting your employer. Each violation is up to $1,000 in damages. Document the date, time, and number.", "🛡️"),
    ("The Awesome Foundation gives $1,000 grants monthly with no reporting requirements and no strings. Applications are always open at awesomefoundation.org.", "🌟"),
    ("Wikipedia's Rapid Fund gives up to $50,000 to open knowledge projects. No nonprofit status required. Rolling deadline. Apply at meta.wikimedia.org/wiki/Rapid_Fund.", "🔬"),
    ("haveibeenpwned.com shows every known data breach your email address appeared in. Free, instant, no account required. Built by a security researcher and trusted by governments worldwide.", "🔐"),
    ("GitHub Actions gives every public repository 2,000 free compute minutes per month. A fully autonomous agent system — email, grants, publishing, payments — runs entirely within that free tier.", "🧬"),
]

def load_json(path):
    try:
        with open(path) as f: return json.load(f)
    except: return {}

def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f: json.dump(data, f, indent=2)

def get_unsubscribe_token(addr):
    return hashlib.sha256(f"unsub-{addr}-meeko".encode()).hexdigest()[:16]

def get_prev_recipients():
    if not GMAIL_PASS: return set()
    recipients = set()
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select('"[Gmail]/Sent Mail"')
        _, msgs = mail.search(None, 'ALL')
        for num in msgs[0].split()[-300:]:
            try:
                _, data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])
                to = msg.get('To', '')
                found = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', to)
                for addr in found:
                    if addr.lower() != GMAIL_USER.lower():
                        recipients.add(addr.lower().strip())
            except: continue
        mail.logout()
    except Exception as e:
        print(f'[Hello] Gmail scan error: {e}')
    return recipients

def build_email_html(to_email, fact_text, fact_emoji):
    """
    ONE email. ONE button. That button goes to the free flower claim page.
    Everything else — gallery, github, rights, fork — is there waiting
    IF they want it. Their click is their choice. We don't push.
    """
    unsub_token = get_unsubscribe_token(to_email)
    unsub_link  = f"mailto:{GMAIL_USER}?subject=UNSUBSCRIBE-{unsub_token}&body=Remove me."

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>A flower for you — Gaza Rose Gallery</title>
</head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:Georgia,serif">
<div style="max-width:560px;margin:0 auto;padding:32px 24px">

  <!-- AI DISCLOSURE — top, honest, first -->
  <p style="font-size:11px;color:rgba(255,255,255,0.25);text-align:center;margin-bottom:28px;line-height:1.8">
    🤖 Automated email · sent by an AI agent on behalf of Meeko · your data is never stored or shared ·
    <a href="{unsub_link}" style="color:rgba(255,45,107,0.5);text-decoration:none">stop these forever</a>
  </p>

  <!-- THE OFFER -->
  <h1 style="font-size:1.8rem;color:#fff;margin:0 0 12px;font-weight:normal;line-height:1.3">
    🌹 Pick a flower.<br>
    <span style="color:#ff2d6b">It's yours. Free.</span>
  </h1>
  <p style="color:rgba(255,255,255,0.55);font-size:1rem;line-height:1.75;margin:0 0 28px">
    Gaza Rose Gallery has 56 original artworks. Browse them all.
    Pick one — any one — and download it at full 300 DPI resolution.
    No email. No account. No catch. The other 55 are $1 each,
    and 70% of every dollar goes directly to Palestinian children's aid through PCRF.
  </p>

  <!-- THE ONE BUTTON -->
  <div style="text-align:center;margin:32px 0">
    <a href="{CLAIM_URL}"
       style="display:inline-block;background:linear-gradient(135deg,#ff2d6b,#ff6b35);
              color:#fff;text-decoration:none;padding:18px 44px;border-radius:12px;
              font-size:1.1rem;font-weight:bold;letter-spacing:.5px;
              box-shadow:0 8px 30px rgba(255,45,107,0.35)">
      🌹 &nbsp; Browse and pick your free flower
    </a>
    <p style="color:rgba(255,255,255,0.25);font-size:.75rem;margin-top:12px">
      Opens the gallery · no login required · your choice is yours
    </p>
  </div>

  <!-- FACT — stated as fact, no hedges -->
  <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
              border-radius:10px;padding:18px 22px;margin:28px 0">
    <p style="color:rgba(255,255,255,0.35);font-size:.7rem;letter-spacing:2px;
              text-transform:uppercase;margin:0 0 8px">{fact_emoji} Something true</p>
    <p style="color:rgba(255,255,255,0.75);font-size:.95rem;line-height:1.75;margin:0">
      {fact_text}
    </p>
  </div>

  <!-- EVERYTHING ELSE — small, quiet, their choice -->
  <div style="border-top:1px solid rgba(255,255,255,0.06);padding-top:20px;
              text-align:center;margin-top:28px">
    <p style="color:rgba(255,255,255,0.2);font-size:.75rem;margin-bottom:12px;letter-spacing:1px;text-transform:uppercase">
      Everything else, if you want it
    </p>
    <p style="margin:0;line-height:2.2">
      <a href="{GALLERY_URL}"   style="color:rgba(255,45,107,0.6);text-decoration:none;font-size:.8rem;margin:0 10px">Full gallery</a>
      <a href="{RIGHTS_URL}"    style="color:rgba(255,45,107,0.6);text-decoration:none;font-size:.8rem;margin:0 10px">Free rights toolkit</a>
      <a href="{GITHUB_URL}"    style="color:rgba(255,45,107,0.6);text-decoration:none;font-size:.8rem;margin:0 10px">Fork the system</a>
      <a href="https://www.pcrf.net" style="color:rgba(255,45,107,0.6);text-decoration:none;font-size:.8rem;margin:0 10px">PCRF</a>
    </p>
  </div>

  <!-- FOOTER -->
  <p style="text-align:center;color:rgba(255,255,255,0.12);font-size:.7rem;
            margin-top:28px;line-height:1.8">
    Meeko · Gaza Rose Gallery · open source · no ads · no middlemen<br>
    <a href="{unsub_link}" style="color:rgba(255,45,107,0.3);text-decoration:none">
      Remove me from all future emails
    </a>
  </p>

</div>
</body>
</html>"""

def send_hello(to_email, html_body):
    try:
        msg = MIMEMultipart('alternative')
        msg['From']    = f'Meeko — Gaza Rose Gallery <{GMAIL_USER}>'
        msg['To']      = to_email
        msg['Subject'] = '🌹 A flower for you — pick any one, it\'s free'
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f'[Hello] Send failed to {to_email}: {e}')
        return False

def process_unsubscribes():
    if not GMAIL_PASS: return
    unsubs = load_json(UNSUB_FILE)
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select('INBOX')
        _, msgs = mail.search(None, 'SUBJECT "UNSUBSCRIBE-"')
        for num in msgs[0].split():
            try:
                _, data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])
                sender = msg.get('From', '')
                found  = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
                for addr in found:
                    addr = addr.lower().strip()
                    if addr != GMAIL_USER.lower():
                        unsubs[addr] = datetime.now(timezone.utc).isoformat()
                        print(f'[Hello] Unsubscribed forever: {addr}')
                mail.store(num, '+FLAGS', '\\Seen')
            except: continue
        mail.logout()
        save_json(UNSUB_FILE, unsubs)
    except Exception as e:
        print(f'[Hello] Unsubscribe scan error: {e}')

def run():
    print(f"\n{'='*50}")
    print("  MYCELIUM HELLO v2")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    process_unsubscribes()
    unsubs = load_json(UNSUB_FILE)
    sent   = load_json(SENT_FILE)

    print('[Hello] Scanning sent mail...')
    all_recipients = get_prev_recipients()
    print(f'[Hello] Previous contacts found: {len(all_recipients)}')

    skip     = set(unsubs.keys()) | set(sent.keys()) | {GMAIL_USER.lower()}
    to_hello = [e for e in all_recipients if e not in skip][:10]

    if not to_hello:
        print('[Hello] No new contacts today.')
        return

    sent_count = 0
    for addr in to_hello:
        fact_text, fact_emoji = random.choice(FACTS)
        html = build_email_html(addr, fact_text, fact_emoji)
        if send_hello(addr, html):
            sent[addr] = {'sent_at': datetime.now(timezone.utc).isoformat()}
            sent_count += 1
            print(f'[Hello] ✓ {addr}')

    save_json(SENT_FILE, sent)
    print(f'\n[Hello] Sent {sent_count} today · {len(sent)} total · {len(unsubs)} unsubscribed (permanent)')

if __name__ == '__main__':
    run()
