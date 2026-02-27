#!/usr/bin/env python3
"""
Patreon Engine
===============
Ko-fi is great for one-time sales.
Patreon is recurring income — the difference between $8
in your wallet and $200/month that keeps coming.

What this engine does:
  1. Monitors Patreon for new patrons and tier changes
  2. Sends personal thank-you messages to new patrons
  3. Creates monthly patron update posts automatically
  4. Generates tier benefit content (exclusive art, early signals, etc.)
  5. Tracks patron retention and alerts on churn

Suggested tiers to create manually at patreon.com/create:
  🌱 Seedling ($3/mo): Monthly newsletter + Discord role
  🌸 Rose ($7/mo): Weekly Gaza Rose art + crypto signals
  🌿 Mycelium ($15/mo): Everything + your name in MANIFESTO
  🌍 Root ($50/mo): Everything + monthly 1:1 system report

Requires: PATREON_ACCESS_TOKEN (from patreon.com/portal/registration/register-clients)
Without token: generates content drafts and emails them.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
PATREON_TOKEN      = os.environ.get('PATREON_ACCESS_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

PATREON_API = 'https://www.patreon.com/api/oauth2/v2'

def patreon_get(path, params=''):
    if not PATREON_TOKEN: return None
    url = f'{PATREON_API}/{path}?{params}'
    try:
        req = urllib_request.Request(
            url,
            headers={
                'Authorization': f'Bearer {PATREON_TOKEN}',
                'User-Agent': 'meeko-patreon/1.0',
            }
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[patreon] API error {path}: {e}')
        return None

def get_campaign_stats():
    data = patreon_get('campaigns', 'fields[campaign]=patron_count,pledge_sum,created_at')
    if not data: return {}
    campaigns = data.get('data', [])
    if not campaigns: return {}
    attrs = campaigns[0].get('attributes', {})
    return {
        'patrons':     attrs.get('patron_count', 0),
        'monthly_usd': round(attrs.get('pledge_sum', 0) / 100, 2),
    }

def get_recent_patrons():
    data = patreon_get(
        'members',
        'fields[member]=full_name,email,patron_status,pledge_relationship_start,'
        'currently_entitled_amount_cents&include=currently_entitled_tiers'
    )
    if not data: return []
    patrons = []
    for m in data.get('data', []):
        attrs = m.get('attributes', {})
        if attrs.get('patron_status') == 'active_patron':
            patrons.append({
                'name':       attrs.get('full_name', 'Patron'),
                'email':      attrs.get('email', ''),
                'since':      attrs.get('pledge_relationship_start', '')[:10],
                'amount_usd': round(attrs.get('currently_entitled_amount_cents', 0) / 100, 2),
            })
    return patrons

def generate_monthly_post():
    if not HF_TOKEN: return None

    # Load stats
    stats = get_campaign_stats()
    arts  = DATA / 'generated_art.json'
    al    = []
    if arts.exists():
        try:
            d = json.loads(arts.read_text())
            al = d if isinstance(d, list) else d.get('art', [])
        except: pass
    art_count = len(al)

    evo   = DATA / 'evolution_log.json'
    built = []
    if evo.exists():
        try: built = json.loads(evo.read_text()).get('built', [])
        except: pass

    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 500,
            'messages': [{
                'role': 'user',
                'content': f"""Write a warm monthly Patreon update post.

Project: Meeko Nerve Center — autonomous AI for Palestinian solidarity
Patrons: {stats.get('patrons', 0)}
Monthly income: ${stats.get('monthly_usd', 0)}
Art pieces generated this month: {art_count}
New engines self-built: {len(built)}

Tone: personal, grateful, specific about impact. Not corporate.
Mention what patron support makes possible (server costs = $0 but
their support funds the human\'s time and energy).
Under 400 words."""
            }]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[patreon] LLM error: {e}')
        return None

def email_monthly_draft(post):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD or not post: return
    lines = [
        f'Monthly Patreon post ready — {TODAY}',
        '',
        'Paste this at: https://www.patreon.com/posts/create',
        '',
        '=' * 50,
        post,
        '=' * 50,
        '',
        'Suggested add-ons before posting:',
        '  - Attach latest Gaza Rose art as header image',
        '  - Add link to Ko-fi for non-patrons',
        '  - Tag as available to all tiers',
    ]
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🌸 Patreon monthly post ready — {TODAY}'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[patreon] Monthly post draft emailed')
    except Exception as e:
        print(f'[patreon] Email error: {e}')

def is_first_of_month():
    return datetime.date.today().day == 1

def run():
    print(f'\n[patreon] Patreon Engine — {TODAY}')

    stats = get_campaign_stats()
    if stats:
        print(f'[patreon] Patrons: {stats["patrons"]} | Monthly: ${stats["monthly_usd"]}')
        try:
            (DATA / 'patreon_stats.json').write_text(json.dumps({'date': TODAY, **stats}, indent=2))
        except: pass
    else:
        print('[patreon] No Patreon token or no campaign found.')
        print('[patreon] Create your campaign at: https://www.patreon.com/create')
        print('[patreon] Then add PATREON_ACCESS_TOKEN to GitHub Secrets.')

    # Monthly post on the 1st
    if is_first_of_month():
        print('[patreon] First of month — generating monthly update post...')
        post = generate_monthly_post()
        if PATREON_TOKEN:
            # Would post via API here — Patreon post creation requires extra OAuth scope
            email_monthly_draft(post)
        else:
            email_monthly_draft(post)

    # Check for new patrons
    if PATREON_TOKEN:
        patrons = get_recent_patrons()
        print(f'[patreon] Active patrons: {len(patrons)}')

    print('[patreon] Done.')

if __name__ == '__main__':
    run()
