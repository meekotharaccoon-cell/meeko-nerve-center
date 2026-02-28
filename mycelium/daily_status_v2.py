#!/usr/bin/env python3
"""
Daily Status Engine v2 — The Actual Intelligence Report
=========================================================
The old status email told you Bitcoin's price when you have no Bitcoin.
This one tells you what to DO.

Every section is actionable:
  1. YOUR MONEY: DOT position + top crypto signal + exact buy instructions
  2. YOUR SYSTEM: health score, what ran, what evolved
  3. YOUR MISSION: accountability hits, Palestine news, PCRF impact
  4. YOUR GRANTS: which applications went out, which are pending
  5. YOUR PRESS: who was contacted, who needs following up
  6. YOUR ART: what was generated, Ko-fi/Gumroad status
  7. COPY-PASTE ACTIONS: exact commands/text you can paste RIGHT NOW to make something happen

You receive one email. Everything important is in it. Nothing useless is in it.
"""

import json, datetime, os, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

DIV = '=' * 60
SUB = '-' * 40

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

# ── Section builders ─────────────────────────────────────────────────────────

def section_money():
    lines = [DIV, '💰 YOUR MONEY — ACTIONABLE TODAY', DIV]

    # DOT position
    dot = load(DATA / 'dot_position.json')
    if dot and dot.get('dot'):
        d = dot['dot']
        m = dot.get('market', {})
        lines += [
            f'DOT POSITION: {d["holdings"]}',
            f'  Price:    {d["current"]} (24h: {d["change_24h"]} | 7d: {d["change_7d"]})',
            f'  Verdict:  {d["action"]}',
            f'  Target:   {d["target"]}',
            f'  Where:    {d["where"]}',
            '',
        ]
    else:
        lines += ['DOT: No data today.', '']

    # Top crypto signal
    signals = load(DATA / 'crypto_signals_queue.json', [])
    if isinstance(signals, list) and signals:
        # Take the highest confidence signal
        conf_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        signals.sort(key=lambda s: conf_order.get(s.get('confidence', 'LOW'), 2))
        top = signals[0]

        lines += [
            f'🚨 TOP SIGNAL: {top["symbol"]} ({top["name"]})',
            f'  Action:    {top["action"]}',
            f'  Entry:     {top["entry"]}',
            f'  Target:    {top["target"]}',
            f'  Stop Loss: {top["stop_loss"]}',
            f'  Timeframe: {top["timeframe"]}',
            f'  Confidence: {top["confidence"]}',
            f'  Where:     {top["where_to_buy"]}',
            f'  Why:       {top["rationale"]}',
            f'  ⚠️  Risk:   {top["risk_warning"]}',
            '',
        ]

        if len(signals) > 1:
            lines.append('Other signals today:')
            for s in signals[1:]:
                lines.append(f'  {s["symbol"]}: {s["action"]} @ {s["entry"]} (conf: {s["confidence"]})')
            lines.append('')
    else:
        lines += ['No strong signals today. Hold DOT, wait for setup.', '']

    # ── COPY-PASTE ACTION ──
    lines += [
        '📋 COPY-PASTE ACTION:',
        '  To buy a signal: Open Phantom → Swap → paste token symbol/address',
        '  To sell DOT: Phantom → Portfolio → DOT → Sell',
        '  Signal history: data/crypto_signals_history.json in your repo',
    ]

    return '\n'.join(lines)

def section_system():
    lines = [DIV, '🧠 YOUR SYSTEM', DIV]

    health = load(DATA / 'health_report.json')
    score  = health.get('score', '?')
    engines_data = health.get('engines', [])
    broken = [e for e in engines_data if e.get('score', 100) < 50]
    lines += [f'Health Score: {score}/100']
    if broken:
        lines.append(f'Engines needing attention: {len(broken)}')
        for b in broken[:3]:
            lines.append(f'  ❌ {b["engine"]}: {b["status"]}')
    else:
        lines.append('All engines healthy ✅')
    lines.append('')

    # Evolution
    evo_log = load(DATA / 'evolution_log.json')
    built   = evo_log.get('built', [])
    if built:
        latest = built[-1]
        lines += [
            f'Self-Evolution: {len(built)} engines self-built total',
            f'  Latest: {latest.get("title", "")} ({latest.get("date", "")})',
            ''
        ]

    # Healing
    heal_log = load(DATA / 'healing_log.json')
    today_heals = [h for h in heal_log.get('heals', []) if h.get('date') == TODAY]
    if today_heals:
        lines += [f'Self-Healing: Fixed {len(today_heals)} engine(s) today']
        for h in today_heals:
            lines.append(f'  🔧 {h["engine"]}: {h["diagnosis"][:80]}')
        lines.append('')

    return '\n'.join(lines)

def section_mission():
    lines = [DIV, '🌍 YOUR MISSION — ACCOUNTABILITY + RELIEF', DIV]

    # Congressional trades
    congress = load(DATA / 'congress.json')
    trades   = congress if isinstance(congress, list) else congress.get('trades', [])
    if trades:
        lines.append(f'Congressional trades flagged today: {len(trades)}')
        for t in trades[:3]:
            member = t.get('representative', t.get('senator', '?'))
            ticker = t.get('ticker', '?')
            date   = t.get('transaction_date', t.get('date', '?'))
            lines.append(f'  ⚠️  {member}: {ticker} ({date})')
        lines += ['', '📋 ACTION: Post these on social. They are public record. Use #STOCKAct']
        lines.append('')

    # Palestine news
    world = load(DATA / 'world_state.json')
    events = world.get('events', world.get('news', []))
    relevant = [e for e in events if any(kw in e.get('title', e.get('headline', '')).lower()
                for kw in ['gaza', 'palestine', 'pcrf', 'west bank', 'ceasefire'])]
    if relevant:
        lines.append('Palestine in the news today:')
        for e in relevant[:3]:
            lines.append(f'  → {e.get("title", e.get("headline", ""))[:120]}')
        lines.append('')

    # Donations received
    kofi = load(DATA / 'kofi_events.json')
    events_list = kofi if isinstance(kofi, list) else kofi.get('events', [])
    today_donations = [e for e in events_list
                       if e.get('type') in ('donation', 'Donation', 'subscription')
                       and e.get('timestamp', e.get('date', ''))[:10] == TODAY]
    if today_donations:
        total = sum(float(e.get('amount', 0)) for e in today_donations)
        pcrf  = round(total * 0.70, 2)
        lines += [
            f'Ko-fi today: ${total:.2f} received | ${pcrf:.2f} going to PCRF',
            '',
        ]

    return '\n'.join(lines)

def section_grants():
    lines = [DIV, '📋 GRANTS', DIV]

    submitted = load(DATA / 'grant_submissions.json').get('submitted', [])
    recent    = [s for s in submitted if s.get('date', '') >= (datetime.date.today() - datetime.timedelta(days=30)).isoformat()]

    if recent:
        lines.append(f'{len(recent)} application(s) sent in the last 30 days:')
        for s in recent:
            lines.append(f'  ✅ {s["grant_name"]} ({s["date"]}) via {s["method"]}')
    else:
        lines.append('No grants submitted yet. Engine runs daily and will apply automatically.')

    lines.append('')
    return '\n'.join(lines)

def section_press():
    lines = [DIV, '📰 PRESS + OUTREACH', DIV]

    fu_log = load(DATA / 'press_followup_log.json').get('contacts', {})
    active    = [(e, v) for e, v in fu_log.items() if v.get('status') != 'retired']
    due_today = [(e, v) for e, v in active
                 if len(v.get('followups', [])) == 0
                 and (datetime.date.today() - datetime.date.fromisoformat(v.get('sent_date', TODAY)[:10])).days >= 5]

    if active:
        lines.append(f'Active press contacts: {len(active)}')
    if due_today:
        lines.append(f'Follow-ups sent today: {len(due_today)}')
        for email, v in due_today[:3]:
            lines.append(f'  📤 {v.get("outlet", email)}')
    if not active and not due_today:
        lines.append('No active press outreach. Outreach engine sources new contacts daily.')

    lines.append('')
    return '\n'.join(lines)

def section_art():
    lines = [DIV, '🌹 ART + SHOP', DIV]

    # Latest art
    arts = load(DATA / 'generated_art.json')
    al   = arts if isinstance(arts, list) else arts.get('art', [])
    today_art = [a for a in al if a.get('date', '')[:10] == TODAY]
    if today_art:
        lines.append(f'{len(today_art)} Gaza Rose(s) generated today:')
        for a in today_art[:2]:
            lines.append(f'  🌹 {a.get("title", a.get("prompt", ""))[:80]}')

    # Ko-fi posts
    kofi_posts = load(DATA / 'kofi_posts.json', [])
    today_posts = [p for p in kofi_posts if p.get('date') == TODAY]
    if today_posts:
        lines.append(f'Ko-fi: {len(today_posts)} post(s) created today')
        for p in today_posts:
            status = '✅ Auto-posted' if p.get('posted_via_api') else '📋 Emailed to you for posting'
            lines.append(f'  {status}: {p.get("art", "")}')

    # Gumroad listings
    gumroad = load(DATA / 'gumroad_listings.json', [])
    today_listings = [g for g in gumroad if g.get('date') == TODAY]
    if today_listings:
        lines.append(f'Gumroad: {len(today_listings)} new listing(s) today')
        for g in today_listings:
            status = '✅ Auto-listed' if g.get('listed_via_api') else '📋 Emailed to you'
            lines.append(f'  {status}: {g.get("title", "")[:60]}')

    if not today_art and not today_posts and not today_listings:
        lines.append('No art activity today.')

    lines.append('')
    return '\n'.join(lines)

def section_copy_paste_actions():
    lines = [
        DIV,
        '📋 COPY-PASTE ACTIONS — Do these right now',
        DIV,
    ]

    action_num = 1

    # Check for any signals
    signals = load(DATA / 'crypto_signals_queue.json', [])
    if signals:
        top = signals[0]
        if top.get('action', '').startswith('BUY'):
            lines += [
                f'{action_num}. CRYPTO TRADE:',
                f'   Open: {top.get("where_to_buy", "your exchange")}',
                f'   Search: {top["symbol"]}',
                f'   Buy: ${top.get("position_usd", "?")} worth',
                f'   Set sell alert at: {top["target"]}',
                f'   Set stop loss at: {top["stop_loss"]}',
                '',
            ]
            action_num += 1

    # Congressional accountability post
    congress = load(DATA / 'congress.json')
    trades   = congress if isinstance(congress, list) else congress.get('trades', [])
    if trades:
        t = trades[0]
        member = t.get('representative', t.get('senator', ''))
        ticker = t.get('ticker', '')
        lines += [
            f'{action_num}. ACCOUNTABILITY POST (paste to Bluesky/Mastodon):',
            f'   "{member} traded ${ticker} while potentially influencing policy.',
            f'   Public record. STOCK Act disclosure.',
            f'   Source: https://efts.house.gov #STOCKAct #Accountability"',
            '',
        ]
        action_num += 1

    # Ko-fi drafts
    drafts = load(DATA / 'kofi_drafts.json', [])
    today_drafts = [d for d in drafts if d.get('date') == TODAY and d.get('status') == 'pending_manual']
    if today_drafts:
        lines += [
            f'{action_num}. KOFI POST (paste at https://ko-fi.com/manage/posts/new):',
            today_drafts[0]['caption'][:300] + '...',
            '',
        ]
        action_num += 1

    # Wikipedia drafts
    wiki_drafts = load(DATA / 'wikipedia_drafts.json', [])
    unsubmitted = [d for d in wiki_drafts if not d.get('submitted') and d.get('date') == TODAY]
    if unsubmitted:
        d = unsubmitted[0]
        wiki_title = d['article'].replace(' ', '_')
        lines += [
            f'{action_num}. WIKIPEDIA CONTRIBUTION:',
            f'   Go to: https://en.wikipedia.org/wiki/Talk:{wiki_title}',
            f'   Paste: {d["draft"][:200]}...',
            '',
        ]
        action_num += 1

    if action_num == 1:
        lines.append('No urgent actions today. System is running autonomously.')

    return '\n'.join(lines)

# ── Main ──────────────────────────────────────────────────────────────────────

def send_email(subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[status_v2] Email sent')
    except Exception as e:
        print(f'[status_v2] Email error: {e}')

def run():
    print(f'\n[status_v2] Daily Status v2 — {TODAY}')

    sections = [
        f'MEEKO NERVE CENTER — DAILY INTELLIGENCE REPORT',
        f'{TODAY}',
        f'System is alive. Here is everything that matters.\n',
        section_money(),
        section_system(),
        section_mission(),
        section_grants(),
        section_press(),
        section_art(),
        section_copy_paste_actions(),
        DIV,
        'Full system: https://github.com/meekotharaccoon-cell/meeko-nerve-center',
        'Ko-fi: https://ko-fi.com/meekotharaccoon',
        DIV,
    ]

    body = '\n'.join(sections)

    # Count actions
    action_count = body.count('COPY-PASTE') + body.count('📋 ACTION')

    subject = f'🧠 Meeko Daily Intel — {TODAY}'
    if action_count > 0:
        subject = f'🚨 {action_count} action(s) ready — Meeko {TODAY}'

    send_email(subject, body)
    print(f'[status_v2] Done. Report length: {len(body)} chars')

if __name__ == '__main__':
    run()
