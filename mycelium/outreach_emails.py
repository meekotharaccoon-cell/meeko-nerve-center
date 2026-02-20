#!/usr/bin/env python3
"""
MYCELIUM OUTREACH

Sends all initial outreach emails on first run.
Tracks what was sent so it never sends twice.
All emails are fully composed — no placeholders.
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

GMAIL_USER = 'mickowood86@gmail.com'
GMAIL_PASS = os.environ.get('GMAIL_APP_PASSWORD')
SENT_LOG = 'mycelium/sent_outreach.json'
GALLERY = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'
GITHUB = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

OUTREACH = [
    {
        'id': 'pcrf_partnership',
        'to': 'info@pcrf.net',
        'subject': 'Gaza Rose Gallery — Artist Partnership & Donation Routing',
        'body': """Hi PCRF team,

I'm Meeko — I'm a digital artist and I built Gaza Rose Gallery (https://meekotharaccoon-cell.github.io/gaza-rose-gallery) specifically to fund your work.

Here's what it does: 56 original 300 DPI digital art pieces, $1 each, 70% of every sale pledged to PCRF. The gallery runs automatically 24/7 on free infrastructure with no ads, no investors, no middlemen. Buyers pay via PayPal, Bitcoin, or Lightning Network.

I have two practical questions:

1. Is there a direct payment method — wire, crypto address, or a dedicated Benevity/network link — that gets donations to you with the fewest fees? PayPal donates take ~3% before it reaches you.

2. Would a formal acknowledgment or partnership letter be possible? Not for promotional purposes — I just want to make sure the money is attributed correctly when I transfer it.

I'm not an organization. I'm one person who wanted to do something real. The gallery is open source at https://github.com/meekotharaccoon-cell/gaza-rose-gallery if you'd like to see how it works.

Thank you for everything you do for the children.

Meeko
mickowood86@gmail.com"""
    },
    {
        'id': 'cloudinary_humanitarian',
        'to': 'support@cloudinary.com',
        'subject': 'Humanitarian Project — Free Tier Request for Gaza Art Gallery',
        'body': """Hi Cloudinary team,

I'm writing to ask whether Cloudinary has a humanitarian or open-source free tier.

I built Gaza Rose Gallery (https://meekotharaccoon-cell.github.io/gaza-rose-gallery), an autonomous digital art gallery where 70% of every $1 sale goes directly to the Palestine Children's Relief Fund. It's fully open source, zero ads, zero corporate backing.

I have 12 high-resolution artworks (300 DPI, 50–125 MB each) that are too large to serve from GitHub. Cloudinary's CDN and automatic WebP conversion would make these accessible without breaking anything — and it aligns perfectly with what you're already great at.

I'm a single person. Not a company. The whole stack costs me $0/month and I'd like to keep it that way so every dollar goes to Gaza.

If a free or reduced account is possible, I'd prominently credit Cloudinary in the gallery and GitHub README. If not, I understand — just wanted to ask the right people directly.

Thank you,
Meeko
mickowood86@gmail.com
https://github.com/meekotharaccoon-cell/gaza-rose-gallery"""
    },
    {
        'id': 'strike_business_upgrade',
        'to': 'support@strike.me',
        'subject': 'Upgrading to Business API — Gaza Rose Lightning Payments',
        'body': """Hi Strike team,

I just signed up for a Strike account and I'm integrating Lightning payments into my humanitarian art gallery.

Gaza Rose Gallery (https://meekotharaccoon-cell.github.io/gaza-rose-gallery) sells 56 original digital artworks at $1 each, with 70% going to the Palestine Children's Relief Fund. I'm building this to be as friction-free as possible — and Lightning is the answer for near-zero fee $1 payments.

I'd like to use the Strike API to:
- Generate Lightning invoices when buyers click 'Pay' on the gallery
- Auto-deliver download links after payment confirmation via webhook
- Keep everything serverless on GitHub Actions

I understand I need to onboard as a business for API access. I'm happy to provide whatever is needed — my goal is to get this working so Lightning becomes the default payment method and PayPal becomes the fallback.

Can you point me to the fastest path to get API access for a small humanitarian creator?

Thank you,
Meeko
mickowood86@gmail.com
https://meekotharaccoon-cell.github.io/gaza-rose-gallery"""
    },
    {
        'id': 'github_sponsors_apply',
        'to': 'sponsors@github.com',
        'subject': 'Gaza Rose Gallery — Open Source Humanitarian Project',
        'body': """Hi GitHub Sponsors team,

I'd like to apply for GitHub Sponsors for my project Gaza Rose Gallery.

The project: An autonomous, open-source digital art gallery at https://meekotharaccoon-cell.github.io/gaza-rose-gallery. 56 original artworks, $1 each, 70% of sales goes to the Palestine Children's Relief Fund. The entire system — promotion, health checks, brain memory, email responses — runs automatically on GitHub Actions with zero monthly cost.

GitHub org: meekotharaccoon-cell
Main repo: https://github.com/meekotharaccoon-cell/meeko-nerve-center

Any sponsorship would go directly into expanding the gallery (more art, better infrastructure, potentially a full donation routing system). This is a one-person project with a real mission.

I'd love to be considered. Happy to provide any additional information you need.

Meeko
mickowood86@gmail.com"""
    }
]

def load_sent():
    try:
        with open(SENT_LOG) as f:
            return json.load(f)
    except:
        return {}

def save_sent(sent):
    os.makedirs('mycelium', exist_ok=True)
    with open(SENT_LOG, 'w') as f:
        json.dump(sent, f, indent=2)

def send_email(to, subject, body):
    if not GMAIL_PASS:
        print(f'[Outreach] No GMAIL_APP_PASSWORD — would send to {to}')
        print(f'  Subject: {subject}')
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = f'Meeko / Gaza Rose Gallery <{GMAIL_USER}>'
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)
        print(f'[Outreach] Sent to {to}')
        return True
    except Exception as e:
        print(f'[Outreach] Failed to {to}: {e}')
        return False

def run():
    sent = load_sent()
    for email_def in OUTREACH:
        eid = email_def['id']
        if eid in sent:
            print(f'[Outreach] Already sent: {eid}')
            continue
        ok = send_email(email_def['to'], email_def['subject'], email_def['body'])
        if ok:
            sent[eid] = {
                'sent_at': datetime.now(timezone.utc).isoformat(),
                'to': email_def['to'],
                'subject': email_def['subject']
            }
    save_sent(sent)

if __name__ == '__main__':
    run()
