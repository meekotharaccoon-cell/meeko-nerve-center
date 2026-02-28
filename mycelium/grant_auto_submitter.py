#!/usr/bin/env python3
"""
Grant Auto-Submitter
=====================
Grant Intelligence drafts applications. This engine submits them.

Submission methods by funder:
  EMAIL-BASED (automated):
    - NLnet Foundation: apply@nlnet.nl
    - Digital Defender Partnership: grants@digitaldefenders.org
    - Many smaller foundations: direct email

  FORM-BASED (semi-automated):
    - Mozilla, Knight, Open Society: web forms
    - For these: emails YOU the complete ready-to-paste package
      with every field pre-filled, just needs copy-paste + submit

  AUTOMATED EMAIL RULES:
    1. Only submit if draft is >2 days old (cooling period)
    2. Never submit the same grant twice
    3. CC the Gmail address so you have a record
    4. Professional email format with attachments simulated
    5. Log every submission with timestamp

For form-based grants:
  Generates a submission package:
    - Subject line
    - Every field pre-answered
    - Word counts matched to limits
    - Direct URL to the form
    - "Copy this, go here, paste, submit" — 5 minutes max
"""

import json, datetime, os, smtplib, time
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')

# Funders with direct email submission
EMAIL_SUBMISSION_FUNDERS = {
    'nlnet_ngi': {
        'to':      'apply@nlnet.nl',
        'subject': 'NGI Zero Core Application — Meeko Nerve Center',
        'intro':   'Dear NLnet Foundation team,',
        'outro':   'Thank you for considering this application.\n\nBest regards,\nMeeko Nerve Center Project\nhttps://github.com/meekotharaccoon-cell/meeko-nerve-center',
    },
    'digital_defender': {
        'to':      'grants@digitaldefenders.org',
        'subject': 'Digital Security Grant Application — Meeko Nerve Center',
        'intro':   'Dear Digital Defender Partnership team,',
        'outro':   'Thank you for your consideration.\n\nBest regards,\nMeeko Nerve Center Project\nhttps://github.com/meekotharaccoon-cell/meeko-nerve-center',
    },
}

# Funders that need web form — system prepares package for you
FORM_SUBMISSION_FUNDERS = {
    'mozilla_tech_fund': {
        'url':    'https://foundation.mozilla.org/en/what-we-fund/awards/mozilla-technology-fund/',
        'fields': [
            ('Project Name',      'Meeko Nerve Center'),
            ('Organization',      'Independent / Open Source'),
            ('Project URL',       'https://github.com/meekotharaccoon-cell/meeko-nerve-center'),
            ('License',           'AGPL-3.0'),
            ('Team Size',         '1 person'),
            ('Stage',             'Deployed and running'),
        ]
    },
    'knight_prototype': {
        'url':    'https://knightfoundation.org/prototype/',
        'fields': [
            ('Project Name',   'Meeko Nerve Center'),
            ('Project URL',    'https://github.com/meekotharaccoon-cell/meeko-nerve-center'),
            ('Stage',          'Working prototype, in production'),
            ('Team',           'Solo founder, open source'),
        ]
    },
    'prototype_fund_de': {
        'url':    'https://prototypefund.de/en/apply/',
        'fields': [
            ('Project Name',   'Meeko Nerve Center'),
            ('Repository',     'https://github.com/meekotharaccoon-cell/meeko-nerve-center'),
            ('License',        'AGPL-3.0'),
            ('Category',       'Civic Tech / Human Rights'),
        ]
    },
    'nlnet_ngi': {
        'url': 'https://nlnet.nl/propose/',
        'fields': [
            ('Project Name',  'Meeko Nerve Center'),
            ('Website',       'https://github.com/meekotharaccoon-cell/meeko-nerve-center'),
            ('License',       'AGPL-3.0'),
            ('Budget',        'EUR 30,000 — 50,000'),
        ]
    },
}

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def get_drafted_grants():
    """Find grant drafts ready for submission."""
    grants_dir = ROOT / 'content' / 'grants'
    if not grants_dir.exists(): return []
    drafts = []
    for f in sorted(grants_dir.glob('*.txt')):
        try:
            text  = f.read_text()
            lines = text.split('\n')
            grant_id = f.stem.rsplit('_', 1)[0]
            draft_date = f.stem.rsplit('_', 1)[-1] if '_' in f.stem else ''
            # Cooling period: 2 days
            if draft_date and draft_date < (datetime.date.today() - datetime.timedelta(days=2)).isoformat():
                drafts.append({
                    'id':    grant_id,
                    'file':  f,
                    'text':  text,
                    'date':  draft_date,
                    'funder': lines[0].replace('Grant: ', '').strip() if lines else grant_id,
                })
        except: pass
    return drafts

def already_submitted(grant_id):
    log = load(DATA / 'grant_submissions.json', {'submitted': []})
    return any(s.get('grant_id') == grant_id for s in log.get('submitted', []))

def log_submission(grant_id, funder, method, success):
    p = DATA / 'grant_submissions.json'
    log = load(p, {'submitted': []})
    log.setdefault('submitted', []).append({
        'grant_id': grant_id,
        'funder':   funder,
        'method':   method,
        'success':  success,
        'date':     TODAY,
    })
    try: p.write_text(json.dumps(log, indent=2))
    except: pass

def submit_by_email(grant_id, draft_text, funder_config):
    """Send grant application directly by email."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return False, 'No Gmail credentials'
    try:
        # Extract letter body (skip header lines)
        lines = draft_text.split('\n')
        body_start = next((i for i, l in enumerate(lines) if l.strip().startswith('Dear') or i > 5), 4)
        letter_body = '\n'.join(lines[body_start:])

        full_body = f"{funder_config['intro']}\n\n{letter_body}\n\n{funder_config['outro']}"

        msg = MIMEMultipart('alternative')
        msg['Subject'] = funder_config['subject']
        msg['From']    = f'Meeko Nerve Center <{GMAIL_ADDRESS}>'
        msg['To']      = funder_config['to']
        msg['CC']      = GMAIL_ADDRESS
        msg['Reply-To'] = GMAIL_ADDRESS
        msg.attach(MIMEText(full_body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, [funder_config['to'], GMAIL_ADDRESS], msg.as_string())
        return True, f'Emailed to {funder_config["to"]}'
    except Exception as e:
        return False, str(e)

def prepare_form_package(draft, funder_config):
    """Prepare a ready-to-paste form submission package."""
    lines = draft['text'].split('\n')
    body_start = next((i for i, l in enumerate(lines) if i > 4), 4)
    letter = '\n'.join(lines[body_start:]).strip()

    package = []
    package.append(f'GRANT FORM SUBMISSION PACKAGE')
    package.append(f'Funder: {draft["funder"]}')
    package.append(f'Form URL: {funder_config["url"]}')
    package.append(f'Prepared: {TODAY}')
    package.append('')
    package.append('STEP 1: Go to the URL above')
    package.append('STEP 2: Fill in these fields:')
    package.append('')
    for field, value in funder_config.get('fields', []):
        package.append(f'  [{field}]')
        package.append(f'  {value}')
        package.append('')
    package.append('STEP 3: In the project description / cover letter field, paste:')
    package.append('=' * 60)
    package.append(letter[:3000])
    package.append('=' * 60)
    package.append('')
    package.append('STEP 4: Submit')
    package.append(f'STEP 5: Reply to this email with "submitted" so the system can track it')
    return '\n'.join(package)

def email_form_package(grant_id, draft, package_text):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'✉️  Grant ready to submit: {draft["funder"]} — 5 min task'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(package_text, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f'[grant_submit] Form package emailed for {draft["funder"]}')
    except Exception as e:
        print(f'[grant_submit] Email error: {e}')

def run():
    print(f'\n[grant_submit] Grant Auto-Submitter — {TODAY}')

    drafts = get_drafted_grants()
    print(f'[grant_submit] Found {len(drafts)} drafted grants (cooling period passed)')

    submitted_count = 0
    packaged_count  = 0

    for draft in drafts:
        gid = draft['id']
        if already_submitted(gid):
            print(f'[grant_submit] Already submitted: {gid}')
            continue

        # Email-based submission
        if gid in EMAIL_SUBMISSION_FUNDERS:
            cfg   = EMAIL_SUBMISSION_FUNDERS[gid]
            ok, detail = submit_by_email(gid, draft['text'], cfg)
            log_submission(gid, draft['funder'], 'email', ok)
            print(f'[grant_submit] {"\u2705" if ok else "\u274c"} Email submitted: {draft["funder"]} — {detail}')
            submitted_count += 1
            time.sleep(5)  # Be polite

        # Form-based: prepare package
        elif gid in FORM_SUBMISSION_FUNDERS:
            cfg     = FORM_SUBMISSION_FUNDERS[gid]
            package = prepare_form_package(draft, cfg)
            email_form_package(gid, draft, package)
            log_submission(gid, draft['funder'], 'form_package_sent', True)
            packaged_count += 1

        # Unknown: send the draft to you to handle
        else:
            email_form_package(gid, draft, draft['text'])
            log_submission(gid, draft['funder'], 'forwarded_to_human', True)
            packaged_count += 1

    print(f'[grant_submit] Auto-submitted: {submitted_count} | Packaged for you: {packaged_count}')
    print('[grant_submit] Done.')

if __name__ == '__main__':
    run()
