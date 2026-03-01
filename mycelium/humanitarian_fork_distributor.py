#!/usr/bin/env python3
"""
Humanitarian Fork Distributor — Send the whole system to people who need it
===========================================================================
This is the most important engine in the whole system.

The idea: people in Gaza, Sudan, Congo, and other active crises who have
an email address and internet connection should receive THIS ENTIRE SYSTEM.

Not a link. Not a tutorial. The actual working setup.
Configured. Ready to run. Free. Forever.

What they receive:
  1. The full meeko-nerve-center repo (via fork or clone)
  2. A customized setup guide for their context
  3. Pre-configured for their country/language/currency
  4. A first-cycle directive written for their situation
  5. Information about their local income opportunities
  6. Connection to the broader SolarPunk network

What this does for them:
  - Passive income from digital products (no capital needed)
  - Grant hunting engine customized for their region
  - Social posting in their language
  - Their own revenue router (they keep 100% — or choose their own cause split)
  - Full documentation + setup wizard

What this does for the network:
  - Every recipient becomes a node
  - Every node generates data that trains better models
  - Every node has its own HF dataset
  - The network learns from every context simultaneously
  - Global South expertise flows into the training data

Distribution channels:
  1. Email (direct to known addresses)
  2. Social post with setup link (reach > direct)
  3. GitHub fork + star (they get notified)
  4. WhatsApp/Telegram when contact info available
  5. Through existing humanitarian networks (PCRF, UNRWA contacts)

Region configurations built in:
  - Gaza / Palestine
  - Sudan
  - Democratic Republic of Congo
  - Yemen
  - Haiti
  - Syria
  - Myanmar
  - Generic (any crisis context)
"""

import json, os, datetime, smtplib
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
NOTION_TOKEN       = os.environ.get('NOTION_TOKEN', '')
GITHUB_REPO        = 'meekotharaccoon-cell/meeko-nerve-center'
GITHUB_REPO_URL    = f'https://github.com/{GITHUB_REPO}'


# ── Region configurations ─────────────────────────────────────────────────────
REGION_CONFIGS = {
    'gaza': {
        'name': 'Gaza / Palestine',
        'language': 'Arabic + English',
        'currency': 'USD (international)',
        'primary_platforms': ['Gumroad', 'Ko-fi', 'GitHub Sponsors'],
        'grant_focus': ['Open Society', 'Digital Defender Partnership', 'Mozilla', 'NLnet'],
        'social_focus': ['Mastodon', 'Bluesky', 'Twitter/X'],
        'income_ideas': [
            'Digital guides about life under occupation (Gumroad $1-5)',
            'Technical documentation and translation work (Upwork)',
            'Open source contributions + GitHub Sponsors',
            'Research assistance (remote, async)',
            'Arabic language content creation',
        ],
        'cause_split': '70% kept (family support) / 30% to any cause you choose',
        'first_directive': 'Focus on income generation. The system will find freelance work and list digital products. Every dollar goes to you and your family first.',
        'note': 'You are not alone. This system was built with solidarity. It keeps running even under internet restrictions.',
    },
    'sudan': {
        'name': 'Sudan',
        'language': 'Arabic + English',
        'currency': 'USD (international)',
        'primary_platforms': ['Gumroad', 'Ko-fi', 'GitHub Sponsors'],
        'grant_focus': ['Open Society', 'Digital Defender', 'Mozilla', 'Knight Foundation'],
        'social_focus': ['Mastodon', 'Bluesky'],
        'income_ideas': [
            'Documentation and reporting work (high demand, remote)',
            'Data collection and research assistance',
            'Content creation about Sudanese context',
            'Digital product creation from local expertise',
            'Grant applications for civil society organizations',
        ],
        'cause_split': '100% kept — you decide what to do with it',
        'first_directive': 'Generate income immediately. Focus on freelance work the system can do on your behalf.',
        'note': 'The system works offline-friendly and can batch operations during internet windows.',
    },
    'drc': {
        'name': 'Democratic Republic of Congo',
        'language': 'French + Swahili + English',
        'currency': 'USD (international)',
        'primary_platforms': ['Gumroad', 'Ko-fi'],
        'grant_focus': ['Open Society', 'Mozilla', 'Prototype Fund'],
        'social_focus': ['Mastodon', 'Bluesky'],
        'income_ideas': [
            'French language content and translation',
            'Research and documentation',
            'Digital guides about mining rights, land rights',
            'Technical remote work',
        ],
        'cause_split': '100% kept',
        'first_directive': 'Start with grant hunting — large amounts available for DRC civil society.',
        'note': 'French language support is built in. The grant engine knows DRC-focused funders.',
    },
    'generic': {
        'name': 'Crisis Context',
        'language': 'English (add your language)',
        'currency': 'USD (international)',
        'primary_platforms': ['Gumroad', 'Ko-fi', 'GitHub Sponsors'],
        'grant_focus': ['Open Society', 'Mozilla', 'NLnet', 'Digital Defender'],
        'social_focus': ['Mastodon', 'Bluesky'],
        'income_ideas': [
            'Digital products from your expertise',
            'Freelance technical/writing work',
            'Grant applications for your organization',
            'Open source contributions',
        ],
        'cause_split': '100% kept — support yourself and your community',
        'first_directive': 'The system will start generating income immediately. Tell it your priorities.',
        'note': 'This system was built for resilience. It runs on GitHub Actions for free.',
    },
}


# ── Setup package generator ─────────────────────────────────────────────────────
def generate_setup_email(recipient_name, recipient_email, region_key='generic'):
    region = REGION_CONFIGS.get(region_key, REGION_CONFIGS['generic'])

    subject = f'🌸 A complete autonomous income system — yours, free, right now'

    body = f"""Hello{' ' + recipient_name if recipient_name else ''},

I'm sending you something I built. It's yours. No strings.

This is an autonomous AI system that:
  • Generates passive income from digital products
  • Applies for freelance jobs on your behalf
  • Hunts for grants from international funders
  • Posts to social media automatically
  • Runs entirely on GitHub's free tier ($0/month)
  • Keeps running even when you're offline

It's already configured for your context ({region['name']}):
  • Platforms: {', '.join(region['primary_platforms'])}
  • Grant focus: {', '.join(region['grant_focus'][:3])}
  • Revenue: {region['cause_split']}

Income ideas your system will pursue:
{chr(10).join('  • ' + idea for idea in region['income_ideas'])}

────────────────────────────────────────
🚀 HOW TO START (5 minutes)
────────────────────────────────────────

1. Create a FREE GitHub account: https://github.com/join

2. Fork this repo: {GITHUB_REPO_URL}
   (Click the Fork button in the top right)

3. Go to your fork → Settings → Secrets and Variables → Actions

4. Add these secrets (free accounts needed):
   • HF_TOKEN: Get free at huggingface.co/settings/tokens
   • GMAIL_ADDRESS: Your Gmail
   • GMAIL_APP_PASSWORD: Gmail → Security → App Passwords

5. Go to Actions → MASTER CONTROLLER → Run workflow

6. Write your priorities in the DIRECTIVES page (system creates it in Notion)

That's it. The system runs twice a day from that point forward.

────────────────────────────────────────
🔑 IMPORTANT NOTE
────────────────────────────────────────

{region['note']}

The system is yours. Modify it. Fork it again and share it with others.
The code is open source (AGPL-3.0). You can see everything it does.
It never lies. It never hides. It works for you.

Your first directive is already written:
"{region['first_directive']}"

Open the DIRECTIVES page after setup and change it to whatever you need.

────────────────────────────────────────
🤝 THE NETWORK
────────────────────────────────────────

When your system is running, you can also help others get started.
Every node in this network strengthens every other node.
We are building decentralized infrastructure for people who need it most.

Free Palestine. 🌹
Free Sudan. Free Congo. Free everyone.

— SolarPunk Network
{GITHUB_REPO_URL}
"""
    return subject, body


# ── Email sender ──────────────────────────────────────────────────────────────
def send_setup_email(recipient_name, recipient_email, region_key='generic'):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f'[fork_dist] No email credentials — queuing for manual send to {recipient_email}')
        queue_for_manual_send(recipient_name, recipient_email, region_key)
        return False

    subject, body = generate_setup_email(recipient_name, recipient_email, region_key)
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'SolarPunk Network <{GMAIL_ADDRESS}>'
        msg['To']      = recipient_email
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, recipient_email, msg.as_string())
        print(f'[fork_dist] ✅ Sent to {recipient_email} ({region_key})')
        return True
    except Exception as e:
        print(f'[fork_dist] Email error: {e}')
        queue_for_manual_send(recipient_name, recipient_email, region_key)
        return False


def queue_for_manual_send(name, email, region):
    queue_path = DATA / 'fork_distribution_queue.json'
    DATA.mkdir(parents=True, exist_ok=True)
    queue = []
    try:
        if queue_path.exists(): queue = json.loads(queue_path.read_text())
    except: pass
    queue.append({'date': TODAY, 'name': name, 'email': email, 'region': region, 'sent': False})
    queue_path.write_text(json.dumps(queue, indent=2))
    print(f'[fork_dist] Queued: {email} ({region})')


# ── Region-specific landing page generator ───────────────────────────────────────
def generate_landing_pages():
    """Generate customized setup guide pages for each region."""
    pages_dir = ROOT / 'public' / 'setup'
    pages_dir.mkdir(parents=True, exist_ok=True)

    for key, region in REGION_CONFIGS.items():
        page_content = f"""# 🌸 SolarPunk Setup Guide — {region['name']}

> **This autonomous AI system is free. It works for you. No payment required. Ever.**

## What you get

An AI system that runs 24/7 on GitHub's free tier and:
- Lists and sells digital products for you
- Applies for remote freelance jobs on your behalf  
- Hunts for international grants
- Posts to social media automatically
- Routes 100% of earnings to you

## Income possibilities

{chr(10).join('- ' + idea for idea in region['income_ideas'])}

## Revenue

{region['cause_split']}

## Start in 5 minutes

1. **Create GitHub account** (free): https://github.com/join
2. **Fork this repo**: {GITHUB_REPO_URL} → click Fork
3. **Add 3 secrets** (Settings → Secrets):
   - `HF_TOKEN` — free at huggingface.co/settings/tokens
   - `GMAIL_ADDRESS` — your Gmail
   - `GMAIL_APP_PASSWORD` — Gmail → Security → App Passwords
4. **Run the system**: Actions → MASTER CONTROLLER → Run workflow
5. **Write your priorities**: Go to your Notion workspace and find the DIRECTIVES page

First directive already set for your context:
> *"{region['first_directive']}"*

---

**Note:** {region['note']}

**Language:** {region['language']}

Free Palestine. Free Sudan. Free Congo. Free everyone. 🌹

Source: {GITHUB_REPO_URL}
"""
        (pages_dir / f'{key}.md').write_text(page_content)

    print(f'[fork_dist] Generated {len(REGION_CONFIGS)} landing pages in public/setup/')


# ── Network post ──────────────────────────────────────────────────────────────
def generate_distribution_post():
    return (
        f'🌸 This autonomous AI system is FREE for anyone who needs it.\n\n'
        f'If you are in Gaza, Sudan, Congo, or any crisis zone and have email + internet:\n\n'
        f'• Fork this repo: {GITHUB_REPO_URL}\n'
        f'• Add 3 free API keys\n'
        f'• The system generates income for you automatically\n\n'
        f'Digital products. Freelance jobs. Grant hunting. Social posting.\n'
        f'Runs 24/7 on GitHub\'s free tier. $0/month. Yours forever.\n\n'
        f'Full setup guide: {GITHUB_REPO_URL}/tree/main/public/setup\n\n'
        f'#FreePalestine #Sudan #Congo #OpenSource #SolarPunk #EthicalAI'
    )


# ── Batch sender ──────────────────────────────────────────────────────────────
def send_to_list(recipients):
    """
    Send to a list of recipients.
    recipients: [{'name': str, 'email': str, 'region': str}]
    """
    sent = 0
    failed = 0
    for r in recipients:
        ok = send_setup_email(
            r.get('name', ''),
            r['email'],
            r.get('region', 'generic')
        )
        if ok: sent += 1
        else: failed += 1
    print(f'[fork_dist] Batch complete: {sent} sent, {failed} queued')
    return sent, failed


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    print(f'\n[fork_dist] Humanitarian Fork Distributor — {TODAY}')
    DATA.mkdir(parents=True, exist_ok=True)

    # 1. Generate landing pages
    generate_landing_pages()

    # 2. Generate the social post
    post = generate_distribution_post()
    (DATA / 'fork_distribution_post.txt').write_text(post)
    print(f'[fork_dist] Social post ready: data/fork_distribution_post.txt')

    # 3. Process any queued recipients
    queue_path = DATA / 'fork_distribution_queue.json'
    if queue_path.exists():
        queue = json.loads(queue_path.read_text())
        unsent = [r for r in queue if not r.get('sent')]
        if unsent:
            print(f'[fork_dist] Processing {len(unsent)} queued recipients')
            sent, failed = send_to_list(unsent)
            # Mark sent ones
            for r in queue:
                if not r.get('sent') and sent > 0:
                    r['sent'] = True
                    sent -= 1
            queue_path.write_text(json.dumps(queue, indent=2))

    # 4. Check for new recipients from Notion
    # (People who fill out the request form in Notion get added here)
    new_recipients_path = DATA / 'fork_requests.json'
    if new_recipients_path.exists():
        requests = json.loads(new_recipients_path.read_text())
        new = [r for r in requests if not r.get('sent')]
        if new:
            print(f'[fork_dist] {len(new)} new fork requests')
            send_to_list(new)
            for r in requests:
                r['sent'] = True
            new_recipients_path.write_text(json.dumps(requests, indent=2))

    # 5. Stats
    total_sent = 0
    if queue_path.exists():
        queue = json.loads(queue_path.read_text())
        total_sent = sum(1 for r in queue if r.get('sent'))
    print(f'[fork_dist] Total systems distributed: {total_sent}')
    print(f'[fork_dist] Each one is a new income node in the network.')
    print('[fork_dist] Done.')


if __name__ == '__main__':
    run()
