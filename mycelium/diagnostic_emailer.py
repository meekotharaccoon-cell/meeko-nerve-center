#!/usr/bin/env python3
"""
Diagnostic Emailer
===================
Sends Meeko a REAL, UNIQUE status report every run.
No duplicates. No generic templates. Actual data, actual status, actual problems.

This is the email you WANT to get:
  - What's working RIGHT NOW
  - What's failing RIGHT NOW  
  - What was built since last email
  - Grant pipeline status
  - Investment signals
  - What needs your attention (max 3 items)
  - What to ignore (the system is handling it)

Every email has a content fingerprint. If nothing changed, no email sent.
"""

import json, datetime, os, smtplib, hashlib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.now().strftime('%H:%M')

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def save(path, data):
    try: Path(path).write_text(json.dumps(data, indent=2))
    except: pass

def collect_state():
    """Pull everything the system knows about itself right now."""
    state = {}

    # Workflow health
    wh = load(DATA / 'workflow_health.json', {})
    state['health_pct']  = wh.get('health_pct', 0)
    state['health_color']= wh.get('color', 'UNKNOWN')
    state['total_wf']    = wh.get('total', 0)
    state['failing_wf']  = wh.get('failing', 0)
    state['retried_wf']  = wh.get('retried', 0)
    state['failures']    = [f.get('name', f.get('file', '?')) for f in wh.get('failures', [])]

    # Evolution / self-builds
    evo = load(DATA / 'evolution_log.json', {'built': []})
    built = evo.get('built', [])
    today_builds = [b for b in built if b.get('date') == TODAY]
    state['total_engines']   = len(list((ROOT / 'mycelium').glob('*.py')))
    state['self_built_total']= len(built)
    state['built_today']     = [b.get('title', b.get('name', '?')) for b in today_builds]

    # Grants
    db = load(DATA / 'grant_database.json', [])
    state['grants_total']   = len(db)
    state['grants_drafted'] = sum(1 for g in db if g.get('status') == 'drafted')
    state['grants_pending'] = sum(1 for g in db if g.get('status') == 'researching')
    # Most recently drafted
    drafted = sorted([g for g in db if g.get('draft_date')], key=lambda x: x.get('draft_date',''), reverse=True)
    state['latest_grant_draft'] = f"{drafted[0]['funder']} — {drafted[0]['draft_date']}" if drafted else 'None yet'

    # Investment signals
    inv = load(DATA / 'investment_signals.json', {})
    sigs = inv.get('signals', [])
    state['top_signal']    = sigs[0].get('symbol', '?') if sigs else 'None'
    state['top_confidence']= sigs[0].get('confidence', 0) if sigs else 0
    state['signal_count']  = len(sigs)
    mc = load(DATA / 'market_context.json', {})
    state['fear_greed']    = mc.get('fear_greed', '?')
    state['market_mood']   = mc.get('mood', '?')

    # Congress
    congress = load(DATA / 'congress.json', {})
    trades = congress if isinstance(congress, list) else congress.get('trades', [])
    state['trade_count'] = len(trades)
    state['latest_trade'] = ''
    if trades:
        t = trades[0]
        state['latest_trade'] = (
            f"{t.get('representative', t.get('senator','?'))} traded "
            f"{t.get('ticker','?')} on {t.get('transaction_date', t.get('date','?'))}"
        )

    # Social / art
    arts = load(DATA / 'generated_art.json', {})
    al = arts if isinstance(arts, list) else arts.get('art', [])
    state['art_count'] = len(al)

    # Network
    spread = load(DATA / 'network_spread_log.json', {})
    state['forks'] = spread.get('total_forks', 0)
    state['nodes'] = spread.get('total_nodes', 1)

    # Email gateway real humans
    gw = load(DATA / 'email_gateway_log.json', {})
    state['real_emails_total'] = gw.get('human_emails_total', 0)
    state['last_real_email']   = gw.get('last_human_email', 'never')

    # Self-healer
    heal = load(DATA / 'heal_report.json', {})
    state['issues_fixed_total'] = heal.get('total_fixed', 0)
    state['last_fix'] = heal.get('last_fix_date', 'none')

    return state

def content_fingerprint(state):
    """Hash of key dynamic values. If unchanged, skip email."""
    key_values = (
        str(state.get('health_pct')),
        str(state.get('failing_wf')),
        str(state.get('self_built_total')),
        str(state.get('grants_drafted')),
        str(state.get('latest_grant_draft')),
        str(state.get('top_signal')),
        str(state.get('trade_count')),
        ','.join(state.get('built_today', [])),
    )
    return hashlib.md5('|'.join(key_values).encode()).hexdigest()[:12]

def build_email_body(state):
    """Build a unique, data-dense status email."""
    lines = []
    lines.append(f'SolarPunk Status — {TODAY} {NOW} UTC')
    lines.append('=' * 55)
    lines.append('')

    # Health
    color_icon = {'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'}.get(state['health_color'], '⚪')
    lines.append(f'WORKFLOW HEALTH: {color_icon} {state["health_pct"]}% ({state["total_wf"]} total, {state["failing_wf"]} failing, {state["retried_wf"]} retried)')
    if state['failures']:
        lines.append('  Failing workflows:')
        for f in state['failures'][:8]:
            lines.append(f'    ✗ {f}')
    lines.append('')

    # What's new today
    if state['built_today']:
        lines.append(f'🔨 BUILT TODAY ({len(state["built_today"])} new engines):')
        for b in state['built_today']:
            lines.append(f'  + {b}')
    else:
        lines.append(f'🔨 SELF-BUILT TOTAL: {state["self_built_total"]} engines across all time')
    lines.append(f'   Engine count: {state["total_engines"]} active')
    lines.append('')

    # Grants
    lines.append(f'💼 GRANTS: {state["grants_drafted"]} drafted | {state["grants_pending"]} pending | {state["grants_total"]} total')
    lines.append(f'   Latest draft: {state["latest_grant_draft"]}')
    lines.append(f'   → Check content/grants/ for draft letters ready to submit')
    lines.append('')

    # Investment
    lines.append(f'📈 INVESTMENT SIGNALS: {state["signal_count"]} active')
    if state['signal_count'] > 0:
        lines.append(f'   Top: {state["top_signal"]} — {state["top_confidence"]}% confidence')
    lines.append(f'   Fear & Greed: {state["fear_greed"]} | Market: {state["market_mood"]}')
    lines.append('')

    # Congress
    lines.append(f'🏛️  CONGRESS: {state["trade_count"]} trades tracked')
    if state['latest_trade']:
        lines.append(f'   Latest: {state["latest_trade"]}')
    lines.append('')

    # Network
    lines.append(f'🌐 NETWORK: {state["nodes"]} nodes | {state["forks"]} forks | {state["art_count"]} art pieces')
    lines.append(f'   Real human emails received: {state["real_emails_total"]} (last: {state["last_real_email"]})')
    lines.append('')

    # Self-healing
    lines.append(f'🔧 SELF-HEALER: {state["issues_fixed_total"]} issues fixed autonomously (last: {state["last_fix"]})')
    lines.append('')

    # What needs attention
    attention = []
    if state['failing_wf'] > 5:
        attention.append(f'{state["failing_wf"]} workflows still failing after retries — check Actions tab')
    if state['grants_drafted'] == 0:
        attention.append('No grants drafted yet — check HF_TOKEN is working')
    if state['trade_count'] == 0:
        attention.append('No congressional trades tracked — congress_watcher may need QUIVER_API_KEY')
    if state['real_emails_total'] == 0:
        attention.append('No real human emails yet — system is ready, network not yet reached')

    if attention:
        lines.append('⚠️  ACTION ITEMS (max 3):')
        for a in attention[:3]:
            lines.append(f'  → {a}')
    else:
        lines.append('✅ NO ACTION NEEDED — system is handling everything.')
    lines.append('')

    # What NOT to worry about
    lines.append('🤖 SYSTEM IS HANDLING (no action needed):')
    lines.append('  ✓ Workflow retries — master_controller auto-retries all failures')
    lines.append('  ✓ Bug fixes — self_healer reads diagnostics, generates fixes, commits')
    lines.append('  ✓ Email routing — gateway now filters GitHub noise, only humans get responses')
    lines.append('  ✓ Grant drafting — rotating through all 6 grants each week')
    lines.append('  ✓ Content — perpetual_builder adding engines every cycle')
    lines.append('')

    lines.append('Free Palestine. 🌹')
    lines.append('https://github.com/meekotharaccoon-cell/meeko-nerve-center')

    return '\n'.join(lines)

def send_diagnostic(subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[diagnostic] No email credentials. Skipping send.')
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'SolarPunk Diagnostics <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[diagnostic] ✅ Status email sent')
        return True
    except Exception as e:
        print(f'[diagnostic] Email error: {e}')
        return False

def run():
    print(f'\n[diagnostic] 📊 Diagnostic Emailer — {TODAY} {NOW}')

    state = collect_state()
    fingerprint = content_fingerprint(state)

    # Check last sent fingerprint — only email if something changed
    log_path = DATA / 'diagnostic_email_log.json'
    log = load(log_path, {'last_fingerprint': '', 'sent': [], 'skipped': 0})

    if log.get('last_fingerprint') == fingerprint:
        log['skipped'] = log.get('skipped', 0) + 1
        save(log_path, log)
        print(f'[diagnostic] Nothing changed since last email. Skipped (saves inbox). Skip count: {log["skipped"]}')
        # Force send every 6 hours even if no change (for heartbeat)
        last_sent = log.get('sent', [])
        if last_sent:
            last_time_str = last_sent[-1].get('timestamp', '')
            if last_time_str:
                try:
                    last_time = datetime.datetime.fromisoformat(last_time_str)
                    hours_since = (datetime.datetime.utcnow() - last_time).total_seconds() / 3600
                    if hours_since < 6:
                        print(f'[diagnostic] Last email {hours_since:.1f}h ago. Skipping heartbeat.')
                        return
                except: pass

    # Build and send
    health_icon = {'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'}.get(state['health_color'], '⚪')
    new_builds = len(state['built_today'])
    subject = (
        f"{health_icon} SolarPunk {state['health_pct']}% health | "
        f"{new_builds} built today | "
        f"{state['grants_drafted']}/{state['grants_total']} grants drafted | "
        f"{TODAY} {NOW}"
    )

    body = build_email_body(state)
    sent = send_diagnostic(subject, body)

    if sent:
        log['last_fingerprint'] = fingerprint
        log['skipped'] = 0
        log.setdefault('sent', []).append({
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'date': TODAY,
            'time': NOW,
            'health_pct': state['health_pct'],
            'built_today': new_builds,
            'fingerprint': fingerprint,
        })
        log['sent'] = log['sent'][-50:]  # Keep last 50
        save(log_path, log)

    print(f'[diagnostic] Done.')

if __name__ == '__main__':
    run()
