#!/usr/bin/env python3
"""
ADDITIONAL GRANT + OPPORTUNITY EMAILS
Based on research: Creative Capital, Awesome Foundation, Innovate Grant,
Harvestworks, Knight Foundation individual grants
All fully composed. Never repeated. Sent once per ID.
"""
import smtplib, json, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

GMAIL_USER = 'mickowood86@gmail.com'
GMAIL_PASS = os.environ.get('GMAIL_APP_PASSWORD', '')
GALLERY    = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'
GITHUB     = 'https://github.com/meekotharaccoon-cell'
SENT_LOG   = 'mycelium/sent_more_grants.json'

EMAILS = [
    {
        'id': 'awesome_foundation',
        'to': 'secretary@awesomefoundation.org',
        'subject': 'Awesome Foundation Grant Application — Gaza Rose Gallery',
        'body': '''Hi Awesome Foundation,

I'm applying for a monthly grant for Gaza Rose Gallery.

The project: 56 original 300 DPI digital flower artworks, $1 each, 70% to the Palestine Children's Relief Fund. The gallery runs itself — GitHub Actions handles promotion, health checks, AI-generated content, and automated email replies. Zero monthly cost. Fully open source and forkable by any humanitarian cause.

What I'd use a grant for: The 12 largest artworks (50–125 MB each) currently can't be served from GitHub. A grant would cover Cloudinary CDN for one year — about $89 — making all 68 artworks accessible and allowing me to add more.

The rest would go to the mission directly.

Gallery: ''' + GALLERY + '''
Code: ''' + GITHUB + '''

Thank you,
Meeko
mickowood86@gmail.com'''
    },
    {
        'id': 'innovate_grant',
        'to': 'hello@innovategrant.com',
        'subject': 'Innovate Grant Application — Digital Art / Humanitarian Tech',
        'body': '''Hi Innovate Grant,

I'd like to apply for the Innovate Grant for Gaza Rose Gallery.

I'm Meeko — a self-taught digital artist. Gaza Rose Gallery is 56 original 300 DPI digital flower artworks, $1 each, 70% to the Palestine Children's Relief Fund. The gallery runs autonomously on free GitHub infrastructure with zero monthly cost.

What makes the work innovative: I built the Meeko Mycelium — an autonomous system where a GitHub repo acts as AI memory, Actions schedules are the heartbeat, and the whole thing manages itself. It's the first (that I know of) autonomous humanitarian art distribution system built entirely on free cloud infrastructure. The architecture is open source and replicable.

Gallery: ''' + GALLERY + '''
Code: ''' + GITHUB + '''

Happy to submit through your formal process.

Meeko
mickowood86@gmail.com'''
    },
    {
        'id': 'harvestworks_residency',
        'to': 'info@harvestworks.org',
        'subject': 'Artist-in-Residence Application Inquiry — Art + Autonomous Tech',
        'body': '''Hi Harvestworks,

I'm writing to ask about the 2026 Artist-in-Residence program.

I'm Meeko — a self-taught digital artist and developer. My current project is Gaza Rose Gallery, a fully autonomous humanitarian art platform where 70% of every $1 sale goes to the Palestine Children's Relief Fund. The system — which I call the Meeko Mycelium — manages itself via GitHub Actions, generates its own content, responds to emails with AI, and maintains persistent memory across sessions. It runs on free infrastructure with zero monthly cost.

What I'd want to develop with Harvestworks' support: A deeper exploration of what it means to build systems that outlast you — specifically, the ethics and design of autonomous humanitarian infrastructure. I'd also use the $5,000 commission to expand the gallery to cover DRC, Sudan, and other active crises with verified partner charities.

Gallery: ''' + GALLERY + '''
Code: ''' + GITHUB + '''

Is there a formal application I should complete?

Meeko
mickowood86@gmail.com'''
    },
    {
        'id': 'fractured_atlas',
        'to': 'info@fracturedatlas.org',
        'subject': 'Fiscal Sponsorship Application — Gaza Rose Gallery',
        'body': '''Hi Fractured Atlas,

I'm applying for fiscal sponsorship for Gaza Rose Gallery.

I'm Meeko — a self-taught digital artist. Gaza Rose Gallery is 56 original 300 DPI digital flower artworks, $1 each, 70% committed to verified humanitarian charities (starting with PCRF, expanding to MSF and IRC for Sudan and DRC coverage). The gallery runs entirely autonomously on free GitHub infrastructure — no server costs, no monthly fees.

I'm seeking fiscal sponsorship because:
1. Tax-deductible donations matter to the buyers and grant-makers I'm approaching
2. Grants from Mozilla Foundation, Knight Foundation, and Wikimedia require a legal entity
3. Full financial transparency is central to the mission — every dollar trackable

I've also applied to Open Collective but understand Fractured Atlas specializes in individual artists.

Gallery: ''' + GALLERY + '''
Code: ''' + GITHUB + '''

What does the application process look like?

Meeko
mickowood86@gmail.com'''
    },
]

def load_sent():
    try:
        with open(SENT_LOG) as f: return json.load(f)
    except: return {}

def save_sent(sent):
    os.makedirs('mycelium', exist_ok=True)
    with open(SENT_LOG, 'w') as f: json.dump(sent, f, indent=2)

def send_email(to, subject, body):
    msg = MIMEMultipart()
    msg['From'] = f'Meeko / Gaza Rose Gallery <{GMAIL_USER}>'
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)

def run():
    if not GMAIL_PASS:
        print('[More Grants] GMAIL_APP_PASSWORD not set. Emails staged:')
        for e in EMAILS: print(f'  -> {e["to"]} | {e["subject"]}')
        return
    sent = load_sent()
    for e in EMAILS:
        if e['id'] in sent:
            print(f'[More Grants] Already sent: {e["id"]}')
            continue
        try:
            send_email(e['to'], e['subject'], e['body'])
            sent[e['id']] = {'to': e['to'], 'sent_at': datetime.now(timezone.utc).isoformat()}
            save_sent(sent)
            print(f'[More Grants] SENT -> {e["to"]}')
        except Exception as ex:
            print(f'[More Grants] FAILED {e["to"]}: {ex}')

if __name__ == '__main__':
    run()
