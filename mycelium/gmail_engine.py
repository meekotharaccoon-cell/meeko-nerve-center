#!/usr/bin/env python3
"""
Gmail Engine
=============
Automated email via Gmail SMTP + App Password.
"""

import json, datetime, os, smtplib, html, re
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'

TODAY = datetime.date.today().isoformat()
DAY_OF_YEAR = datetime.date.today().timetuple().tm_yday

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587

# ── Utilities ─────────────────────────────────────────────────────────────────

def clean_html_entities(text):
    """Decode HTML entities fully, including double-encoded ones like &amp;#8211;"""
    if not text:
        return text
    # Unescape twice to handle double-encoding (&amp;#8211; -> &#8211; -> –)
    cleaned = html.unescape(html.unescape(str(text)))
    return cleaned

def fetch_json(url, timeout=10):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-gmail/1.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except:
        return None

def get_live_crypto():
    """Fetch crypto prices directly if world_state has an empty array."""
    # Try CoinGecko
    cg = fetch_json('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,solana&vs_currencies=usd&include_24hr_change=true')
    if cg:
        result = {}
        if 'bitcoin' in cg:
            result['BTC'] = {
                'price': round(float(cg['bitcoin'].get('usd', 0)), 2),
                'change_24h': round(float(cg['bitcoin'].get('usd_24h_change', 0)), 2),
            }
        if 'solana' in cg:
            result['SOL'] = {
                'price': round(float(cg['solana'].get('usd', 0)), 2),
                'change_24h': round(float(cg['solana'].get('usd_24h_change', 0)), 2),
            }
        return result
    # Binance fallback
    result = {}
    for sym, pair in [('BTC','BTCUSDT'), ('SOL','SOLUSDT')]:
        d = fetch_json(f'https://api.binance.com/api/v3/ticker/24hr?symbol={pair}')
        if d:
            result[sym] = {
                'price': round(float(d.get('lastPrice', 0)), 2),
                'change_24h': round(float(d.get('priceChangePercent', 0)), 2),
            }
    return result

# ── Core send ─────────────────────────────────────────────────────────────────

def send_email(to, subject, body_text, body_html=None, from_name='Meeko Nerve Center'):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[gmail] No credentials.')
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

# ── Daily status ──────────────────────────────────────────────────────────────

def send_daily_status():
    if not GMAIL_ADDRESS:
        return False

    sections = [f'Meeko Nerve Center — Daily Status\n{TODAY}\n', '=' * 50]

    # AI insight
    insight_path = KB / 'ai_insights' / 'latest.md'
    if insight_path.exists():
        insight = insight_path.read_text().split('\n', 2)[-1][:500]
        sections += ['\n🧠 AI INSIGHT', insight]

    # Market: crypto prices
    world_path = DATA / 'world_state.json'
    sections.append('\n📡 MARKET')
    crypto_data = {}
    try:
        if world_path.exists():
            world = json.loads(world_path.read_text())
            crypto_list = world.get('crypto', [])

            # If world_state has actual data, use it
            if crypto_list:
                btc = next((c for c in crypto_list if c.get('symbol') == 'BTC'), None)
                sol = next((c for c in crypto_list if c.get('symbol') == 'SOL'), None)
                if btc:
                    crypto_data['BTC'] = {'price': btc['price'], 'change_24h': btc['change_24h']}
                if sol:
                    crypto_data['SOL'] = {'price': sol['price'], 'change_24h': sol['change_24h']}

        # If world_state crypto was empty, fetch live right now
        if not crypto_data:
            print('[gmail] world_state crypto empty — fetching live')
            crypto_data = get_live_crypto()

        if crypto_data.get('BTC'):
            b = crypto_data['BTC']
            sections.append(f"  BTC: ${b['price']:,.2f} ({b['change_24h']:+.2f}%)")
        if crypto_data.get('SOL'):
            s = crypto_data['SOL']
            sections.append(f"  SOL: ${s['price']:,.2f} ({s['change_24h']:+.2f}%)")

        # Wikipedia trending — filtered
        DOMAIN_EXT = re.compile(r'^\.\w{2,6}$')
        SKIP_WORDS = ['erotic', 'pornograph', 'xxx', 'sexual', 'nude', 'onlyfans', 'adult film']
        if world_path.exists():
            wiki = world.get('wikipedia_trending', [])
            clean_wiki = [
                a for a in wiki
                if not DOMAIN_EXT.match(a.get('title', ''))
                and not any(w in a.get('title', '').lower() for w in SKIP_WORDS)
            ]
            if clean_wiki:
                top = clean_wiki[0]
                sections.append(f"  Trending: {top['title']} ({top['views']:,} views)")

    except Exception as e:
        sections.append(f'  (Market data unavailable: {e})')

    # Congress
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

    # Ideas — compute live from ledger, not stale stats object
    ledger_path = DATA / 'idea_ledger.json'
    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text())
            ideas  = ledger.get('ideas', {})

            # ideas can be a dict (id->obj) or a list — handle both
            if isinstance(ideas, dict):
                idea_list = list(ideas.values())
            else:
                idea_list = ideas

            total  = len(idea_list)
            passed = sum(1 for i in idea_list if i.get('status') in ('passed','wired'))
            failed = sum(1 for i in idea_list if i.get('status') == 'failed')

            # Count what happened specifically TODAY
            today_tested = sum(1 for i in idea_list if (i.get('tested') or '')[:10] == TODAY)
            today_passed = sum(1 for i in idea_list if (i.get('tested') or '')[:10] == TODAY and i.get('status') in ('passed','wired'))

            if today_tested > 0:
                sections.append(f'\n💡 IDEAS: {total} total | {passed} passed | {failed} failed')
                sections.append(f'   Today: {today_tested} tested, {today_passed} passed')
            else:
                sections.append(f'\n💡 IDEAS: {total} total | {passed} passed | {failed} failed')
                sections.append(f'   (No new tests today — engine generated no new ideas this run)')
        except Exception as e:
            sections.append(f'\n💡 IDEAS: (error reading ledger: {e})')

    # Jobs — rotate by day, decode HTML entities
    jobs_path = DATA / 'jobs_today.json'
    if jobs_path.exists():
        try:
            jobs = json.loads(jobs_path.read_text())
            crypto_jobs = jobs.get('crypto_jobs', [])
            if crypto_jobs:
                # Rotate: use day-of-year mod len so it changes daily
                idx = DAY_OF_YEAR % len(crypto_jobs)
                job = crypto_jobs[idx]
                title   = clean_html_entities(job.get('title', ''))
                company = clean_html_entities(job.get('company', ''))
                url     = job.get('url', '')
                sections.append(f'\n💼 TOP CRYPTO JOB: {title} @ {company}')
                sections.append(f'  {url}')
        except Exception as e:
            sections.append(f'\n💼 JOBS: (error: {e})')

    sections.append('\n' + '=' * 50)
    sections.append('Meeko Nerve Center — github.com/meekotharaccoon-cell/meeko-nerve-center')
    sections.append('Reply "stop" to unsubscribe.')

    body = '\n'.join(sections)
    return send_email(
        to        = GMAIL_ADDRESS,
        subject   = f'🌿 Nerve Center — {TODAY}',
        body_text = body,
    )

# ── Donor thank-you ───────────────────────────────────────────────────────────

def send_donor_thankyou(donor_email, amount, currency='USD', message=''):
    pcrf = round(amount * 0.70, 2)
    text = f"""Hey,

Seriously — thank you.

Your ${amount:.2f} {currency} just became ${pcrf:.2f} going directly to
Palestinian children through PCRF (Palestinian Children's Relief Fund).

{'You said: "' + message + '"' + chr(10) + chr(10) if message and message != '[private message]' else ''}If you ever want to see exactly where it goes: pcrf.net

The Gaza Rose gallery:
https://meekotharaccoon-cell.github.io/meeko-nerve-center/

Full open-source system:
https://github.com/meekotharaccoon-cell/meeko-nerve-center

You didn't have to do this. Thanks for being YOU.

Meeko"""
    return send_email(
        to        = donor_email,
        subject   = 'Thank you — really.',
        body_text = text,
        from_name = 'Meeko'
    )

# ── Press pitch ───────────────────────────────────────────────────────────────

def send_press_pitch(journalist_email, journalist_name, outlet):
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

Live now: https://meekotharaccoon-cell.github.io/meeko-nerve-center/
Open source: https://github.com/meekotharaccoon-cell/meeko-nerve-center

Happy to answer any questions.

Meeko
{GMAIL_ADDRESS}"""
    return send_email(
        to        = journalist_email,
        subject   = f'Open-source AI that funds Palestinian children — story for {outlet}?',
        body_text = text,
        from_name = 'Meeko'
    )

# ── Fork notification ─────────────────────────────────────────────────────────

def send_fork_notification(forker_github, fork_url):
    text = f"""New fork detected.

Forker: {forker_github}
Fork URL: {fork_url}

The network is growing."""
    return send_email(
        to        = GMAIL_ADDRESS,
        subject   = f'🌿 New fork: {forker_github}',
        body_text = text,
    )

# ── Weekly newsletter ─────────────────────────────────────────────────────────

def send_weekly_newsletter(subscriber_emails):
    sections = [
        'MEEKO NERVE CENTER — Weekly Signal',
        f'Week of {TODAY}', '', 'What the system learned this week:', '',
    ]
    insight_path = KB / 'ai_insights' / 'latest.md'
    if insight_path.exists():
        insight = insight_path.read_text().split('\n', 2)[-1][:300]
        sections += ['🧠 AI INSIGHT', insight, '']
    word_path = KB / 'language' / 'word_of_day.json'
    if word_path.exists():
        try:
            wd = json.loads(word_path.read_text()).get('word', {})
            if wd:
                sections += [f'📖 WORD: {wd["word"].upper()}', wd.get('definition',''), '']
        except:
            pass
    jobs_path = DATA / 'jobs_today.json'
    if jobs_path.exists():
        try:
            jobs = json.loads(jobs_path.read_text())
            cj = jobs.get('crypto_jobs', [])
            if cj:
                idx = DAY_OF_YEAR % len(cj)
                j = cj[idx]
                sections += [
                    '💼 JOB OF THE WEEK',
                    f"{clean_html_entities(j.get('title',''))} @ {clean_html_entities(j.get('company',''))}",
                    j.get('url',''), ''
                ]
        except:
            pass
    sections += [
        '─' * 40,
        '🌹 Gaza Rose — 70% to PCRF',
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
    print(f'[gmail] Newsletter sent to {sent}/{len(subscriber_emails)}')
    return sent

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print(f'[gmail] Gmail Engine — {TODAY}')
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[gmail] Credentials missing.')
        return

    print('[gmail] Sending daily status...')
    ok = send_daily_status()
    if ok:
        print(f'[gmail] Status sent to {GMAIL_ADDRESS}')

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
            print(f'[gmail] Ko-fi error: {e}')

if __name__ == '__main__':
    run()
