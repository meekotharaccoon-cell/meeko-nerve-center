#!/usr/bin/env python3
"""
Gmail Engine
=============
Automated email via Gmail SMTP + App Password.
No third-party service. No monthly fee. Your Gmail. Your control.

Use cases:
  1. SYSTEM STATUS EMAIL     - daily digest to yourself
  2. DONOR THANK-YOUS        - when Ko-fi events come in
  3. PRESS OUTREACH          - Gaza Rose to journalists/bloggers
  4. FORK NOTIFICATIONS      - when someone forks the repo
  5. NEWSLETTER              - weekly digest to subscribers
  6. ALERTS                  - when idea engine finds something important

Privacy:
  - Recipient emails used ONLY to send the email
  - Not stored beyond the send operation
  - Subscriber list (if any) lives in data/subscribers.json
    and is scrubbed on request
  - NEVER shared, sold, or passed to third parties

Requires:
  - GMAIL_ADDRESS     your Gmail address
  - GMAIL_APP_PASSWORD  16-char app password from myaccount.google.com/apppasswords
"""

import json, datetime, os, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'

TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS     = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587

# ── Core send function ────────────────────────────────────────────────────────

def send_email(to, subject, body_text, body_html=None, from_name='Meeko Nerve Center'):
    """
    Send an email via Gmail SMTP.
    Returns True if sent, False if failed.
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[gmail] No credentials. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD secrets.')
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f'{from_name} <{GMAIL_ADDRESS}>'
    msg['To']      = to

    msg.attach(MIMEText(body_text, 'plain'))
    if body_html:
        msg.attach(MIMEText(body_html, 'html'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to, msg.as_string())
        print(f'[gmail] Sent: "{subject}" -> {to}')
        return True
    except Exception as e:
        print(f'[gmail] Send failed: {e}')
        return False

# ── Email templates ───────────────────────────────────────────────────────────

def send_daily_status():
    """
    Send yourself a daily system status digest.
    Pulls from knowledge digests and data files.
    """
    if not GMAIL_ADDRESS:
        return False

    sections = [f'Meeko Nerve Center — Daily Status\n{TODAY}\n', '=' * 50]

    # AI insight
    insight_path = KB / 'ai_insights' / 'latest.md'
    if insight_path.exists():
        insight = insight_path.read_text().split('\n', 2)[-1][:500]
        sections += ['\n🧠 AI INSIGHT', insight]

    # World state snapshot
    world_path = DATA / 'world_state.json'
    if world_path.exists():
        try:
            world = json.loads(world_path.read_text())
            crypto = world.get('crypto', [])
            btc = next((c for c in crypto if c['symbol'] == 'BTC'), None)
            sol = next((c for c in crypto if c['symbol'] == 'SOL'), None)
            lines = ['\n📡 MARKET']
            if btc: lines.append(f'  BTC: ${btc["price"]:,} ({btc["change_24h"]:+.1f}%)')
            if sol: lines.append(f'  SOL: ${sol["price"]} ({sol["change_24h"]:+.1f}%)')
            wiki = world.get('wikipedia_trending', [])
            if wiki: lines.append(f'  Trending: {wiki[0]["title"]} ({wiki[0]["views"]:,} views)')
            sections += lines
        except:
            pass

    # Congress flags
    congress_path = DATA / 'congress.json'
    if congress_path.exists():
        try:
            congress = json.loads(congress_path.read_text())
            flagged = congress.get('flagged', [])
            if flagged:
                sections.append(f'\n🏛️ CONGRESS FLAGS ({len(flagged)} trades)')
                for t in flagged[:3]:
                    sections.append(f'  {t.get("representative","?")} — {t.get("ticker","?")} ${t.get("amount","?")} ({t.get("type","?")})')
        except:
            pass

    # Ideas status
    ledger_path = DATA / 'idea_ledger.json'
    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text())
            stats = ledger.get('stats', {})
            sections.append(f'\n💡 IDEAS: {stats.get("tested",0)} tested | {stats.get("passed",0)} passed | {stats.get("failed",0)} failed')
        except:
            pass

    # Jobs
    jobs_path = DATA / 'jobs_today.json'
    if jobs_path.exists():
        try:
            jobs = json.loads(jobs_path.read_text())
            crypto_jobs = jobs.get('crypto_jobs', [])
            if crypto_jobs:
                sections.append(f'\n💼 TOP CRYPTO JOB: {crypto_jobs[0]["title"]} @ {crypto_jobs[0]["company"]}')
                sections.append(f'  {crypto_jobs[0].get("url","")}')
        except:
            pass

    sections.append('\n' + '=' * 50)
    sections.append('Meeko Nerve Center — github.com/meekotharaccoon-cell/meeko-nerve-center')
    sections.append('Unsubscribe: just reply "stop" and I will.')

    body = '\n'.join(sections)

    return send_email(
        to      = GMAIL_ADDRESS,  # send to yourself
        subject = f'🌿 Nerve Center Status — {TODAY}',
        body_text = body,
    )

def send_donor_thankyou(donor_email, amount, currency='USD', message=''):
    """
    Send a personal thank-you to a Ko-fi donor.
    Called when kofi_webhook.py processes a donation event.
    """
    pcrf = round(amount * 0.70, 2)

    text = f"""Hey,

Seriously — thank you.

Your ${amount:.2f} {currency} just became ${pcrf:.2f} going directly to
Palestinian children through PCRF (Palestinian Children's Relief Fund).

That's not a metaphor. That's real money to real kids.

{'You said: "' + message + '"' + chr(10) + chr(10) if message and message != '[private message]' else ''}
If you ever want to see exactly where it goes: pcrf.net

The Gaza Rose gallery is here if you want to share it:
https://meekotharaccoon-cell.github.io/meeko-nerve-center/

And if you want to go deeper — the whole system is open source:
https://github.com/meekotharaccoon-cell/meeko-nerve-center

You didn't have to do this. Thanks for being YOU.

Meeko"""

    return send_email(
        to        = donor_email,
        subject   = 'Thank you — really.',
        body_text = text,
        from_name = 'Meeko'
    )

def send_press_pitch(journalist_email, journalist_name, outlet):
    """
    Press outreach for Gaza Rose + Nerve Center.
    Personalized pitch to journalists and bloggers.
    """
    text = f"""Hi {journalist_name},

I built something I think your readers at {outlet} would care about.

The Gaza Rose is an open-source AI system that:
  - Generates and sells digital art (the Gaza Rose collection)
  - Sends 70% of every sale directly to Palestinian children via PCRF
  - Runs entirely autonomously on GitHub Actions — no server, no monthly cost
  - Monitors Congressional stock trades, earthquakes, carbon intensity,
    crypto markets, and 20+ free APIs daily
  - Self-generates content, tests its own ideas, and learns from failures
  - Can be forked by anyone for $5 and repurposed for any cause

It's live now:
https://meekotharaccoon-cell.github.io/meeko-nerve-center/

The SolarPunk dashboard (all real-time public data, no account needed):
https://meekotharaccoon-cell.github.io/meeko-nerve-center/solarpunk.html

The full system is AGPL-3.0 open source:
https://github.com/meekotharaccoon-cell/meeko-nerve-center

Happy to answer any questions or give you a full walkthrough.

Meeko
{GMAIL_ADDRESS}"""

    return send_email(
        to        = journalist_email,
        subject   = f'Open-source AI that funds Palestinian children — story for {outlet}?',
        body_text = text,
        from_name = 'Meeko'
    )

def send_fork_notification(forker_github, fork_url):
    """
    Welcome email when someone forks the repo.
    NOTE: GitHub doesn't give us forker emails directly.
    This runs if we have a way to get their email (e.g. they fill a form).
    """
    text = f"""Hey {forker_github},

You just forked the Meeko Nerve Center. That's incredible.

Your fork: {fork_url}

A few things to get you started:

1. Read START_HERE.md in your repo — it's the fastest path to running
2. Add your secrets in Settings → Secrets → Actions
   (TELEGRAM_TOKEN, GMAIL_ADDRESS, GMAIL_APP_PASSWORD at minimum)
3. The $5 fork guide walks you through customizing it for your own mission

If you get stuck, open an issue on the original repo:
https://github.com/meekotharaccoon-cell/meeko-nerve-center/issues

What cause are you building for? I'd genuinely love to know.

Meeko"""

    return send_email(
        to        = GMAIL_ADDRESS,  # send to self as notification (we don't have forker email)
        subject   = f'🌿 New fork: {forker_github} — {fork_url}',
        body_text = text,
        from_name = 'Meeko Nerve Center'
    )

def send_weekly_newsletter(subscriber_emails):
    """
    Weekly newsletter to subscribers.
    Pulls from the latest knowledge digests.
    """
    # Build newsletter body from latest knowledge
    sections = [
        f'MEEKO NERVE CENTER — Weekly Signal',
        f'Week of {TODAY}',
        '',
        'What the system learned this week:',
        '',
    ]

    # AI insight
    insight_path = KB / 'ai_insights' / 'latest.md'
    if insight_path.exists():
        insight = insight_path.read_text().split('\n', 2)[-1][:300]
        sections += ['🧠 AI INSIGHT THIS WEEK', insight, '']

    # Word of the week
    word_path = KB / 'language' / 'word_of_day.json'
    if word_path.exists():
        try:
            word_data = json.loads(word_path.read_text()).get('word', {})
            if word_data:
                sections += [
                    f'📖 WORD OF THE WEEK: {word_data["word"].upper()}',
                    word_data.get('definition', ''),
                    ''
                ]
        except:
            pass

    # Top crypto job
    jobs_path = DATA / 'jobs_today.json'
    if jobs_path.exists():
        try:
            jobs = json.loads(jobs_path.read_text())
            top_job = (jobs.get('crypto_jobs') or jobs.get('top_50', [{}]))[0]
            if top_job:
                sections += [
                    f'💼 REMOTE JOB OF THE WEEK',
                    f'{top_job.get("title","")} @ {top_job.get("company","")}',
                    top_job.get('url', ''),
                    ''
                ]
        except:
            pass

    sections += [
        '─' * 40,
        '🌹 Gaza Rose art — 70% to PCRF',
        'https://meekotharaccoon-cell.github.io/meeko-nerve-center/',
        '',
        'Fork the system: github.com/meekotharaccoon-cell/meeko-nerve-center',
        'Unsubscribe: reply "stop"',
    ]

    body = '\n'.join(sections)
    sent = 0

    for email in subscriber_emails:
        if send_email(to=email, subject=f'🌿 Nerve Center Weekly — {TODAY}', body_text=body):
            sent += 1

    print(f'[gmail] Newsletter sent to {sent}/{len(subscriber_emails)} subscribers')
    return sent

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print(f'[gmail] Gmail Engine — {TODAY}')

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[gmail] Credentials not set. Secrets needed: GMAIL_ADDRESS, GMAIL_APP_PASSWORD')
        return

    # Send daily status to yourself
    print('[gmail] Sending daily status email...')
    ok = send_daily_status()
    if ok:
        print(f'[gmail] Daily status sent to {GMAIL_ADDRESS}')

    # Check for Ko-fi donations to thank
    kofi_path = DATA / 'kofi_events.json'
    if kofi_path.exists():
        try:
            events = json.loads(kofi_path.read_text()).get('events', [])
            today_events = [e for e in events if e.get('date') == TODAY and not e.get('thanked')]
            for event in today_events:
                if event.get('donor_email'):
                    send_donor_thankyou(
                        donor_email = event['donor_email'],
                        amount      = event.get('amount', 0),
                        currency    = event.get('currency', 'USD'),
                        message     = event.get('message', ''),
                    )
                    event['thanked'] = True
            if today_events:
                kofi_path.write_text(json.dumps({'events': events}, indent=2))
        except Exception as e:
            print(f'[gmail] Ko-fi thank-you error: {e}')

if __name__ == '__main__':
    run()
