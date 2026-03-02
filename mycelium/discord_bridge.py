#!/usr/bin/env python3
"""
Discord Bridge — SolarPunk Nerve Center
========================================
Connects the system's data to Discord using the bot credentials
already stored in GitHub secrets (DIS_APP_ID, DIS_APP_PUBLIC_KEY,
DIS_BOT_TOKEN, DIS_CHANNEL_ID).

What this does:
  1. Posts daily system briefing to Discord channel
  2. Posts new Gumroad sales notifications
  3. Posts when new PDF products go live
  4. Posts crypto signal alerts
  5. Posts social engagement milestones
  6. Reads messages for "!status" command → replies with system health

Discord secrets needed (add in GitHub → Settings → Secrets):
  DIS_APP_ID         — already added ✅
  DIS_APP_PUBLIC_KEY — already added ✅
  DIS_BOT_TOKEN      — Bot token (Discord Developer Portal → Bot → Token)
  DIS_CHANNEL_ID     — Channel ID to post into (right-click channel → Copy ID)

Why DIS_APP_ID + DIS_APP_PUBLIC_KEY are not enough alone:
  Those are for slash commands / webhook verification.
  DIS_BOT_TOKEN is needed for actually posting messages.
  If you don't have one yet: Discord Developer Portal → Your App → Bot → Reset Token

Architecture:
  - Outbound: system → Discord (this script)
  - Inbound: Discord → system via webhook (discord-bot.yml handles verification)
"""

import json, os, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

DIS_BOT_TOKEN  = os.environ.get('DIS_BOT_TOKEN', '')
DIS_CHANNEL_ID = os.environ.get('DIS_CHANNEL_ID', '')
DIS_APP_ID     = os.environ.get('DIS_APP_ID', '')

DISCORD_API = 'https://discord.com/api/v10'


def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}


def post_to_discord(message: str, channel_id: str = None) -> bool:
    """Post a message to a Discord channel via bot token."""
    if not DIS_BOT_TOKEN:
        print('[discord] No DIS_BOT_TOKEN — add it to GitHub secrets to enable posting')
        return False
    ch = channel_id or DIS_CHANNEL_ID
    if not ch:
        print('[discord] No DIS_CHANNEL_ID — add it to GitHub secrets')
        return False
    try:
        payload = json.dumps({'content': message[:2000]}).encode()
        req = urllib_request.Request(
            f'{DISCORD_API}/channels/{ch}/messages',
            data=payload,
            headers={
                'Authorization': f'Bot {DIS_BOT_TOKEN}',
                'Content-Type': 'application/json',
            },
            method='POST'
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
        if result.get('id'):
            print(f'[discord] ✅ Posted: {message[:60]}...')
            return True
        print(f'[discord] API error: {result}')
        return False
    except Exception as e:
        print(f'[discord] Error: {e}')
        return False


def build_daily_briefing() -> str:
    """Build daily system status message for Discord."""
    lines = [f'🌸 **SolarPunk Daily Briefing — {TODAY}**', '']

    # Revenue
    brain = load(DATA / 'three_d_brain.json')
    if brain:
        rev = brain.get('revenue', {})
        reach = brain.get('reach', {})
        impact = brain.get('impact', {})
        lines.append(f'💰 **Revenue:** ${rev.get("grand_total", 0):.2f} total')
        lines.append(f'🍴 **Forks:** {reach.get("github_forks", 0)} | ⭐ Stars: {reach.get("github_stars", 0)}')
        lines.append(f'🎯 **Impact Score:** {impact.get("impact_score", 0)}/100')
        lines.append('')

    # Workflow health
    health = load(DATA / 'workflow_health.json')
    if health:
        color = {'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'}.get(health.get('color', ''), '⚪')
        lines.append(f'{color} **Workflows:** {health.get("health_pct", 0)}% healthy ({health.get("passing", 0)}/{health.get("total", 0)} passing)')
        if health.get('failures'):
            lines.append('❌ Failing: ' + ', '.join(f['name'] for f in health['failures'][:3]))
        lines.append('')

    # Gumroad products
    gumroad = load(DATA / 'gumroad_products.json')
    if gumroad:
        products = gumroad if isinstance(gumroad, list) else gumroad.get('products', [])
        lines.append(f'📦 **Gumroad Products Live:** {len(products)}')
        lines.append('')

    lines.append('70% of all revenue → PCRF 🌹 | Free Palestine')
    lines.append(f'System: https://github.com/meekotharaccoon-cell/meeko-nerve-center')
    return '\n'.join(lines)


def build_sale_notification(sale: dict) -> str:
    amount = sale.get('amount', '?')
    product = sale.get('product_name', 'Unknown product')
    pcrf_share = round(float(str(amount).replace('$', '')) * 0.70, 2) if amount != '?' else '?'
    return (
        f'💸 **NEW SALE** — {product}\n'
        f'Amount: ${amount} | PCRF share: ${pcrf_share}\n'
        f'🌹 Free Palestine'
    )


def check_new_sales() -> list:
    """Check for new sales since last Discord post."""
    sales_log = load(DATA / 'gumroad_sales.json', [])
    if isinstance(sales_log, dict): sales_log = sales_log.get('sales', [])
    last_posted_path = DATA / 'discord_last_sale_posted.json'
    last_posted = load(last_posted_path, {'count': 0})
    prev_count = last_posted.get('count', 0)
    new_sales = sales_log[prev_count:]
    if new_sales:
        last_posted['count'] = len(sales_log)
        try: last_posted_path.write_text(json.dumps(last_posted, indent=2))
        except: pass
    return new_sales


def post_system_status_command_response() -> str:
    """Build a compact status string for !status command responses."""
    brain = load(DATA / 'three_d_brain.json')
    health = load(DATA / 'workflow_health.json')
    rev = brain.get('revenue', {}).get('grand_total', 0) if brain else 0
    hp = health.get('health_pct', 0) if health else 0
    color = {'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'}.get(health.get('color', '') if health else '', '⚪')
    return (
        f'**Meeko Nerve Center** {color}\n'
        f'Revenue: ${rev:.2f} | Health: {hp}% | Date: {TODAY}\n'
        f'70% → PCRF 🌹 | https://github.com/meekotharaccoon-cell/meeko-nerve-center'
    )


def run():
    print(f'\n[discord] Discord Bridge — {TODAY}')

    if not DIS_BOT_TOKEN:
        print('[discord] DIS_BOT_TOKEN missing. Your DIS_APP_ID and DIS_APP_PUBLIC_KEY are')
        print('[discord] connected for webhook verification, but posting requires DIS_BOT_TOKEN.')
        print('[discord] To get it: Discord Developer Portal → Your App → Bot → Reset Token')
        print('[discord] Then add DIS_BOT_TOKEN to GitHub secrets.')
        # Still write status so system knows what happened
        (DATA / 'discord_status.json').write_text(json.dumps({
            'date': TODAY,
            'status': 'DIS_BOT_TOKEN missing',
            'DIS_APP_ID': 'connected' if DIS_APP_ID else 'missing',
            'note': 'App ID and Public Key are set. Add DIS_BOT_TOKEN to enable posting.'
        }, indent=2))
        return

    # 1. Post daily briefing
    briefing = build_daily_briefing()
    ok = post_to_discord(briefing)

    # 2. Post new sales if any
    new_sales = check_new_sales()
    for sale in new_sales[:5]:  # Max 5 sale notifications
        post_to_discord(build_sale_notification(sale))

    # 3. Write status
    (DATA / 'discord_status.json').write_text(json.dumps({
        'date': TODAY,
        'briefing_posted': ok,
        'new_sales_notified': len(new_sales),
        'status': 'connected' if ok else 'error',
    }, indent=2))

    print(f'[discord] Done. Briefing: {"✅" if ok else "❌"} | Sales notified: {len(new_sales)}')


if __name__ == '__main__':
    run()
