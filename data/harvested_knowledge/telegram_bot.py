#!/usr/bin/env python3
"""
Telegram Bot Bridge
===================
Sends you a morning briefing every day.
You reply with commands. No server needed - uses long polling.

Free forever. No monthly cost. Works from GitHub Actions.

Setup (5 minutes):
  1. Open Telegram, message @BotFather
  2. Send: /newbot
  3. Name it: Meeko Nerve Center
  4. Username: meeko_nerve_center_bot (or any available)
  5. Copy the API token -> GitHub Secrets -> TELEGRAM_TOKEN
  6. Message your new bot once (to start the chat)
  7. Run: python mycelium/telegram_bot.py --get-chat-id
  8. Copy the chat ID -> GitHub Secrets -> TELEGRAM_CHAT_ID

Commands you can send to your bot:
  /status    - system health snapshot
  /posts     - today's content queue
  /fixes     - what needs human attention
  /emails    - draft emails summary
  /strategy  - today's strategy
  /help      - list all commands
"""

import os, json, datetime, urllib.request, urllib.error, argparse
from pathlib import Path

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
TODAY  = datetime.date.today().isoformat()

TOKEN   = os.environ.get('TELEGRAM_TOKEN', '')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
API     = f'https://api.telegram.org/bot{TOKEN}'

def tg(method, params=None):
    if not TOKEN:
        return None
    url  = f'{API}/{method}'
    data = json.dumps(params or {}).encode()
    req  = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[telegram] {e}')
        return None

def send(text, chat_id=None, parse_mode='HTML'):
    return tg('sendMessage', {
        'chat_id':    chat_id or CHAT_ID,
        'text':       str(text)[:4000],
        'parse_mode': parse_mode,
    })

def get_updates(offset=0):
    return tg('getUpdates', {'offset': offset, 'timeout': 5})

# ── Morning briefing ──────────────────────────────────────────────
def build_briefing():
    lines = [f'<b>Meeko Nerve Center - {TODAY}</b>', '']

    # Strategy
    sp = DATA / 'strategy.json'
    if sp.exists():
        try:
            s = json.loads(sp.read_text())
            lines += [
                f'<b>Today:</b> {s.get("primary_crisis","Gaza")} focus',
                f'Revenue: {s.get("revenue_channel","gallery")}',
                '',
            ]
        except: pass

    # Health
    hp = DATA / 'heal_report.json'
    if hp.exists():
        try:
            h = json.loads(hp.read_text())
            open_n = h.get('needs_human', 0)
            healed = h.get('total_healed', 0)
            status = 'OK' if open_n == 0 else f'{open_n} need attention'
            lines += [f'<b>System:</b> {status} (healed: {healed})', '']
        except: pass

    # Posts ready
    qp = ROOT / 'content' / 'queue' / 'latest.json'
    if qp.exists():
        try:
            q = json.loads(qp.read_text())
            posts = q if isinstance(q, list) else q.get('posts', [])
            lines.append(f'<b>Posts ready:</b> {len(posts)} queued for today')
        except: pass

    # Emails
    ep = ROOT / 'DRAFT_EMAILS.md'
    if ep.exists():
        count = ep.read_text().count('## Email')
        lines.append(f'<b>Draft emails:</b> {count} ready to review')

    lines += [
        '',
        'Reply with /posts /fixes /emails /strategy',
        'Dashboard: https://meekotharaccoon-cell.github.io/meeko-nerve-center/dashboard.html',
    ]
    return '\n'.join(lines)

# ── Command responses ──────────────────────────────────────────────
def cmd_status():
    hp = DATA / 'heal_report.json'
    if not hp.exists():
        return 'No health data yet. Run self_healer.py first.'
    try:
        h = json.loads(hp.read_text())
        return (
            f'<b>System Health</b>\n'
            f'Auto-healed: {h.get("total_healed",0)}\n'
            f'Open issues: {h.get("needs_human",0)}\n'
            f'Last run: {h.get("last_run","unknown")}'
        )
    except:
        return 'Could not read health data.'

def cmd_posts():
    qp = ROOT / 'content' / 'queue' / 'latest.json'
    if not qp.exists():
        return 'No content queue. Run humanitarian_content.py first.'
    try:
        q = json.loads(qp.read_text())
        posts = q if isinstance(q, list) else q.get('posts', [])
        if not posts:
            return 'Queue is empty today.'
        lines = [f'<b>{len(posts)} posts queued</b>\n']
        for i, p in enumerate(posts[:3], 1):
            text = p.get('text', str(p))[:200]
            lines.append(f'<b>{i}.</b> {text}\n')
        if len(posts) > 3:
            lines.append(f'... and {len(posts)-3} more. See content/queue/latest.json')
        return '\n'.join(lines)
    except:
        return 'Could not read content queue.'

def cmd_fixes():
    fp = ROOT / 'FIXES_NEEDED.md'
    if not fp.exists():
        return 'No FIXES_NEEDED.md yet.'
    content = fp.read_text()
    if 'No open issues' in content or '0 issues' in content:
        return 'No open issues.'
    # Extract just the issue titles
    lines = [l for l in content.split('\n') if l.startswith('### ')]
    if not lines:
        return content[:1000]
    return '<b>Open issues:</b>\n' + '\n'.join(lines[:7])

def cmd_emails():
    ep = ROOT / 'DRAFT_EMAILS.md'
    if not ep.exists():
        return 'No draft emails yet. Run email_drafter.py first.'
    content = ep.read_text()
    subjects = [l for l in content.split('\n') if '**Subject:**' in l]
    if not subjects:
        return content[:1000]
    return '<b>Draft emails ready:</b>\n' + '\n'.join(subjects[:6]) + '\n\nOpen DRAFT_EMAILS.md to send them.'

def cmd_strategy():
    sp = DATA / 'strategy.json'
    if not sp.exists():
        return 'No strategy yet. Run loop_brain.py first.'
    try:
        s = json.loads(sp.read_text())
        return (
            f'<b>Strategy for {TODAY}</b>\n'
            f'Crisis: {s.get("primary_crisis","Gaza")}\n'
            f'Revenue: {s.get("revenue_channel","gallery")}\n'
            f'Template: {s.get("primary_template","standard")}\n'
            f'Reasoning: {str(s.get("reasoning","rule-based"))[:300]}'
        )
    except:
        return 'Could not read strategy.'

COMMANDS = {
    '/status':   cmd_status,
    '/posts':    cmd_posts,
    '/fixes':    cmd_fixes,
    '/emails':   cmd_emails,
    '/strategy': cmd_strategy,
    '/help': lambda: (
        '<b>Meeko Nerve Center Commands</b>\n'
        '/status   - system health\n'
        '/posts    - today\'s content queue\n'
        '/fixes    - what needs attention\n'
        '/emails   - draft emails summary\n'
        '/strategy - today\'s strategy\n'
        '/help     - this list'
    ),
}

# ── Polling loop (for local/manual use) ───────────────────────────
def poll_once():
    """Check for one batch of updates and respond."""
    offset_file = DATA / 'telegram_offset.json'
    offset = 0
    if offset_file.exists():
        try: offset = json.loads(offset_file.read_text()).get('offset', 0)
        except: pass

    result = get_updates(offset)
    if not result or not result.get('ok'):
        return

    updates = result.get('result', [])
    for upd in updates:
        offset = max(offset, upd['update_id'] + 1)
        msg    = upd.get('message', {})
        text   = msg.get('text', '').strip()
        cid    = msg.get('chat', {}).get('id')
        if text and cid:
            cmd = text.split()[0].lower()
            if cmd in COMMANDS:
                response = COMMANDS[cmd]()
                send(response, chat_id=cid)
            else:
                send('Unknown command. Try /help', chat_id=cid)

    offset_file.write_text(json.dumps({'offset': offset}))

# ── Main ──────────────────────────────────────────────────────────
def send_morning_briefing():
    if not TOKEN or not CHAT_ID:
        print('[telegram] TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set.')
        print('[telegram] Setup:')
        print('  1. Message @BotFather on Telegram -> /newbot')
        print('  2. Copy token -> GitHub Secrets -> TELEGRAM_TOKEN')
        print('  3. Message your new bot once')
        print('  4. Run: python mycelium/telegram_bot.py --get-chat-id')
        print('  5. Copy chat ID -> GitHub Secrets -> TELEGRAM_CHAT_ID')
        return
    msg    = build_briefing()
    result = send(msg)
    if result and result.get('ok'):
        print(f'[telegram] Morning briefing sent!')
    else:
        print(f'[telegram] Failed: {result}')

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--get-chat-id', action='store_true',
                        help='Print your chat ID (run after messaging your bot)')
    parser.add_argument('--poll', action='store_true',
                        help='Check for messages and respond once')
    args = parser.parse_args()

    if args.get_chat_id:
        if not TOKEN:
            print('Set TELEGRAM_TOKEN first')
            return
        result = get_updates()
        if result and result.get('result'):
            for upd in result['result']:
                cid  = upd.get('message', {}).get('chat', {}).get('id')
                name = upd.get('message', {}).get('chat', {}).get('first_name', '')
                if cid:
                    print(f'Chat ID: {cid}  ({name})')
                    print(f'Add TELEGRAM_CHAT_ID={cid} to GitHub Secrets')
        else:
            print('No messages found. Message your bot on Telegram first, then run again.')
        return

    if args.poll:
        poll_once()
        return

    # Default: send morning briefing
    send_morning_briefing()

if __name__ == '__main__':
    run()
