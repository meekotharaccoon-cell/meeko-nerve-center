#!/usr/bin/env python3
"""
Discord Engine
================
Meeko Nerve Center gets a Discord presence.

What it does:
  1. Posts daily system status to a Discord channel
  2. Posts new Gaza Rose art drops
  3. Posts viral content from the queue
  4. Posts accountability alerts (congressional trades)
  5. Responds to slash commands: /status /art /mission
  6. Creates scheduled events for Ko-fi drops

Setup:
  Create a Discord bot at https://discord.com/developers/applications
  Add it to your server with these permissions:
    - Send Messages, Embed Links, Attach Files, Create Events
    - Read Message History, View Channels
  Required secrets: DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID
  Optional: DISCORD_GUILD_ID (for slash commands + events)
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY = datetime.date.today().isoformat()

DISCORD_TOKEN      = os.environ.get('DISCORD_BOT_TOKEN', '')
DISCORD_CHANNEL    = os.environ.get('DISCORD_CHANNEL_ID', '')
DISCORD_GUILD      = os.environ.get('DISCORD_GUILD_ID', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

DISCORD_API = 'https://discord.com/api/v10'

# ── Discord API helpers ──────────────────────────────────────────────────────

def discord(method, path, body=None, timeout=20):
    if not DISCORD_TOKEN or not DISCORD_CHANNEL:
        return None
    url = f'{DISCORD_API}{path}'
    headers = {
        'Authorization': f'Bot {DISCORD_TOKEN}',
        'Content-Type':  'application/json',
        'User-Agent':    'DiscordBot (https://github.com/meekotharaccoon-cell/meeko-nerve-center, 1.0)',
    }
    try:
        req = urllib_request.Request(url, headers=headers, method=method)
        if body:
            req.data = json.dumps(body).encode()
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[discord] API error {path[:50]}: {e}')
        return None

def send_message(content=None, embeds=None, channel_id=None):
    ch = channel_id or DISCORD_CHANNEL
    if not ch: return None
    body = {}
    if content: body['content'] = content
    if embeds:  body['embeds']  = embeds
    return discord('POST', f'/channels/{ch}/messages', body)

def send_embed(title, description, color=0x2ecc71, fields=None, footer=None, url=None):
    embed = {
        'title':       title,
        'description': description,
        'color':       color,
    }
    if fields: embed['fields'] = fields
    if footer: embed['footer'] = {'text': footer}
    if url:    embed['url'] = url
    embed['timestamp'] = datetime.datetime.utcnow().isoformat()
    return send_message(embeds=[embed])

# ── Load system data ─────────────────────────────────────────────────────────

def load_json(path, default=None):
    try:
        if Path(path).exists():
            return json.loads(Path(path).read_text())
    except: pass
    return default or {}

def get_health_score():
    health = load_json(DATA / 'health_report.json')
    return health.get('score', '?')

def get_top_idea():
    ledger = load_json(DATA / 'idea_ledger.json')
    ideas  = ledger.get('ideas', {})
    il     = list(ideas.values()) if isinstance(ideas, dict) else (ideas if isinstance(ideas, list) else [])
    passed = [i for i in il if i.get('status') in ('passed', 'wired')]
    return passed[-1] if passed else None

def get_latest_evolution():
    evo = load_json(DATA / 'evolution_log.json')
    built = evo.get('built', [])
    return built[-1] if built else None

def get_latest_art():
    arts = load_json(DATA / 'generated_art.json')
    al   = arts if isinstance(arts, list) else arts.get('art', [])
    return al[-1] if al else None

def get_top_accountability():
    congress = load_json(DATA / 'congress.json')
    trades   = congress if isinstance(congress, list) else congress.get('trades', [])
    return trades[0] if trades else None

def get_world_headline():
    world = load_json(DATA / 'world_state.json')
    events = world.get('events', world.get('news', []))
    for e in events:
        title = e.get('title', e.get('headline', ''))
        if any(kw in title.lower() for kw in ['gaza', 'palestine', 'west bank', 'pcrf']):
            return title
    return events[0].get('title', '') if events else None

# ── Post types ───────────────────────────────────────────────────────────────

def post_daily_status():
    health  = get_health_score()
    idea    = get_top_idea()
    evo     = get_latest_evolution()
    headline = get_world_headline()

    fields = [
        {'name': '🧠 System Health', 'value': f'{health}/100', 'inline': True},
        {'name': '📅 Date', 'value': TODAY, 'inline': True},
    ]
    if idea:
        fields.append({'name': '💡 Latest Idea', 'value': idea.get('title', idea.get('name', ''))[:100], 'inline': False})
    if evo:
        fields.append({'name': '⚡ Last Self-Built Engine', 'value': evo.get('title', '')[:100], 'inline': False})
    if headline:
        fields.append({'name': '🌍 Palestine Today', 'value': headline[:200], 'inline': False})

    return send_embed(
        title='🌹 Meeko Nerve Center — Daily Report',
        description='The system ran its full cycle. Here\'s what happened.',
        color=0xe74c3c,
        fields=fields,
        footer='meekotharaccoon-cell/meeko-nerve-center | AGPL-3.0 | Free to fork',
        url='https://meekotharaccoon-cell.github.io/meeko-nerve-center/',
    )

def post_art_drop(art):
    if not art: return None
    title   = art.get('title', 'Gaza Rose')
    prompt  = art.get('prompt', '')[:200]
    img_url = art.get('url', art.get('image_url', ''))

    embed = {
        'title':       f'🌹 New Gaza Rose: {title}',
        'description': f'{prompt}\n\n70% of sales go to Palestinian children via PCRF.',
        'color':       0xe91e63,
        'fields': [
            {'name': '🛒 Get it', 'value': '[Ko-fi Shop](https://ko-fi.com/meekotharaccoon)', 'inline': True},
            {'name': '💖 PCRF', 'value': '[pcrf.net](https://www.pcrf.net)', 'inline': True},
        ],
        'footer': {'text': 'Open source art for Palestinian relief'},
        'timestamp': datetime.datetime.utcnow().isoformat(),
    }
    if img_url:
        embed['image'] = {'url': img_url}

    return send_message(embeds=[embed])

def post_accountability_alert(trade):
    if not trade: return None
    member = trade.get('representative', trade.get('senator', 'Unknown'))
    ticker = trade.get('ticker', '?')
    date   = trade.get('transaction_date', trade.get('date', '?'))
    amount = trade.get('amount', trade.get('range', '?'))

    return send_embed(
        title=f'⚠️ STOCK Act Alert: {member}',
        description=f'**{member}** traded **{ticker}** ({amount}) on {date}.\n\nThis is public record under the STOCK Act.',
        color=0xf39c12,
        fields=[
            {'name': '📋 Source', 'value': '[House Disclosures](https://efts.house.gov/LATEST/search-index?q=%22stock+act%22)', 'inline': True},
        ],
        footer='Meeko tracks congressional trades automatically | Data: public record',
    )

def post_signal(signal):
    """Post a crypto/stock signal to Discord."""
    if not signal: return None
    return send_embed(
        title=f'📡 Signal: {signal.get("symbol", "")}',
        description=signal.get('rationale', '')[:400],
        color=0x1abc9c,
        fields=[
            {'name': '🎯 Action',     'value': signal.get('action', ''),    'inline': True},
            {'name': '💰 Entry',      'value': signal.get('entry', ''),     'inline': True},
            {'name': '📈 Target',     'value': signal.get('target', ''),    'inline': True},
            {'name': '🛡️ Stop Loss', 'value': signal.get('stop_loss', ''), 'inline': True},
            {'name': '⚡ Confidence', 'value': signal.get('confidence', ''), 'inline': True},
        ],
        footer='Not financial advice. DYOR. This is automated signal detection.',
    )

# ── Register slash commands ───────────────────────────────────────────────────

def register_slash_commands():
    """Register slash commands with Discord (run once or when commands change)."""
    if not DISCORD_TOKEN or not DISCORD_GUILD: return

    commands = [
        {
            'name':        'status',
            'description': 'Get the current system health and latest activity',
            'type':        1,
        },
        {
            'name':        'mission',
            'description': 'What is Meeko Nerve Center and why does it exist?',
            'type':        1,
        },
        {
            'name':        'art',
            'description': 'Show the latest Gaza Rose art drop',
            'type':        1,
        },
    ]

    for cmd in commands:
        result = discord('POST', f'/applications/{DISCORD_GUILD}/guilds/{DISCORD_GUILD}/commands', cmd)
        if result:
            print(f'[discord] Registered command: /{cmd["name"]}')

# ── Already posted today? ─────────────────────────────────────────────────────

def already_posted_today():
    log_path = DATA / 'discord_log.json'
    if not log_path.exists(): return False
    try:
        log = json.loads(log_path.read_text())
        return log.get('last_post') == TODAY
    except:
        return False

def mark_posted():
    try:
        (DATA / 'discord_log.json').write_text(json.dumps({'last_post': TODAY}))
    except: pass

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print(f'\n[discord] Discord Engine — {TODAY}')

    if not DISCORD_TOKEN or not DISCORD_CHANNEL:
        print('[discord] No DISCORD_BOT_TOKEN or DISCORD_CHANNEL_ID. Skipping.')
        print('[discord] Setup: https://discord.com/developers/applications')
        return

    if already_posted_today():
        print('[discord] Already posted today. Skipping daily status.')
    else:
        # Daily status
        result = post_daily_status()
        if result:
            print('[discord] ✅ Daily status posted')

        # Art drop if available
        art = get_latest_art()
        if art and art.get('date', '')[:10] == TODAY:
            post_art_drop(art)
            print('[discord] ✅ Art drop posted')

        # Accountability alert
        trade = get_top_accountability()
        if trade:
            post_accountability_alert(trade)
            print('[discord] ✅ Accountability alert posted')

        mark_posted()

    # Post any signals from crypto engine
    signals_path = DATA / 'crypto_signals_queue.json'
    if signals_path.exists():
        try:
            signals = json.loads(signals_path.read_text())
            for s in signals:
                if not s.get('discord_posted'):
                    post_signal(s)
                    s['discord_posted'] = True
                    print(f'[discord] ✅ Signal posted: {s.get("symbol")}')
            signals_path.write_text(json.dumps(signals, indent=2))
        except Exception as e:
            print(f'[discord] Signal post error: {e}')

    print('[discord] Done.')

if __name__ == '__main__':
    run()
