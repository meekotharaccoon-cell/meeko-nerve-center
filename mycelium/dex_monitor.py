#!/usr/bin/env python3
"""
DEX Monitor — Free crypto signal layer
=======================================
Watches token pairs via DEX Screener (free, no API key).
Sends Telegram alerts when price/volume moves hit thresholds.
Also feeds Pionex grid bot recommendations.

Runs every 30 min via GitHub Actions.
Or locally: python mycelium/dex_monitor.py

No API key needed. Free forever.
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
DATA.mkdir(exist_ok=True)

TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow()

TELEGRAM_TOKEN   = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# ── Tokens to watch ────────────────────────────────────────────────
# Add any pair you want. Find the pairAddress on dexscreener.com
# Format: {"name": "display name", "chain": "solana", "pair": "address"}
WATCH_LIST = [
    # Big movers — used to calibrate signal
    {"name": "SOL/USDC",  "chain": "solana",   "search": "SOL USDC"},
    {"name": "BTC/USDT",  "chain": "ethereum", "search": "WBTC USDT"},
    # Add your own below:
    # {"name": "TOKEN/SOL", "chain": "solana", "search": "TOKEN SOL"},
]

# ── Alert thresholds ───────────────────────────────────────────────
ALERT_RULES = {
    'price_change_5m_pct':  {'up': 3.0,  'down': -3.0},   # % in 5 min
    'price_change_1h_pct':  {'up': 8.0,  'down': -8.0},   # % in 1 hour
    'price_change_24h_pct': {'up': 20.0, 'down': -20.0},  # % in 24 hours
    'volume_24h_usd':       {'spike': 1_000_000},          # $1M+ 24h volume
    'liquidity_usd':        {'low': 10_000},               # <$10K liquidity warning
}

# ── DEX Screener API ───────────────────────────────────────────────
def fetch_pair(search_query):
    url = f'https://api.dexscreener.com/latest/dex/search?q={urllib_request.quote(search_query)}'
    try:
        with urllib_request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        pairs = data.get('pairs', [])
        if not pairs:
            return None
        # Return highest liquidity pair
        return sorted(pairs, key=lambda p: float(p.get('liquidity', {}).get('usd', 0) or 0), reverse=True)[0]
    except Exception as e:
        print(f'[dex] fetch error for "{search_query}": {e}')
        return None

def fetch_token_boosts():
    """Get trending boosted tokens — early signal on what's being promoted."""
    try:
        with urllib_request.urlopen('https://api.dexscreener.com/token-boosts/latest/v1', timeout=10) as r:
            return json.loads(r.read())
    except:
        return []

def fetch_community_takeovers():
    """Community takeovers — grass-roots token revivals."""
    try:
        with urllib_request.urlopen('https://api.dexscreener.com/community-takeovers/latest/v1', timeout=10) as r:
            return json.loads(r.read())
    except:
        return []

# ── Alert logic ────────────────────────────────────────────────────
def check_alerts(token_name, pair):
    alerts = []
    pc = pair.get('priceChange', {})
    liq = float(pair.get('liquidity', {}).get('usd', 0) or 0)
    vol = float(pair.get('volume', {}).get('h24', 0) or 0)
    price = pair.get('priceUsd', 'N/A')

    p5  = float(pc.get('m5',  0) or 0)
    p1h = float(pc.get('h1',  0) or 0)
    p24 = float(pc.get('h24', 0) or 0)

    if p5  >= ALERT_RULES['price_change_5m_pct']['up']:    alerts.append(f'🚀 +{p5:.1f}% in 5min')
    if p5  <= ALERT_RULES['price_change_5m_pct']['down']:  alerts.append(f'📉 {p5:.1f}% in 5min')
    if p1h >= ALERT_RULES['price_change_1h_pct']['up']:    alerts.append(f'🚀 +{p1h:.1f}% in 1hr')
    if p1h <= ALERT_RULES['price_change_1h_pct']['down']:  alerts.append(f'📉 {p1h:.1f}% in 1hr')
    if p24 >= ALERT_RULES['price_change_24h_pct']['up']:   alerts.append(f'🌙 +{p24:.1f}% in 24hr')
    if p24 <= ALERT_RULES['price_change_24h_pct']['down']: alerts.append(f'💀 {p24:.1f}% in 24hr')
    if vol >= ALERT_RULES['volume_24h_usd']['spike']:      alerts.append(f'📊 Vol: ${vol:,.0f}')
    if 0 < liq < ALERT_RULES['liquidity_usd']['low']:     alerts.append(f'⚠️ Low liq: ${liq:,.0f}')

    return alerts, price, p5, p1h, p24, vol, liq

# ── Telegram ───────────────────────────────────────────────────────
def telegram_send(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        data = json.dumps({'chat_id': TELEGRAM_CHAT_ID, 'text': text[:4000], 'parse_mode': 'HTML'}).encode()
        req  = urllib_request.Request(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            data=data, headers={'Content-Type': 'application/json'}
        )
        urllib_request.urlopen(req, timeout=10)
    except Exception as e:
        print(f'[telegram] {e}')

# ── Pionex recommendations ─────────────────────────────────────────
def pionex_recommendation(pair_data):
    """
    Simple grid bot recommendation based on volatility.
    Pionex grid bots work best on ranging/volatile assets.
    """
    recs = []
    for item in pair_data:
        p = item.get('pair')
        if not p: continue
        pc   = p.get('priceChange', {})
        p24  = abs(float(pc.get('h24', 0) or 0))
        vol  = float(p.get('volume', {}).get('h24', 0) or 0)
        liq  = float(p.get('liquidity', {}).get('usd', 0) or 0)
        name = item.get('name', '?')

        if p24 > 5 and vol > 100_000 and liq > 50_000:
            recs.append({
                'token': name,
                'volatility_24h': p24,
                'volume_24h': vol,
                'liquidity': liq,
                'grid_bot_suitable': p24 < 30,  # too volatile = risky for grid
                'note': 'Good grid bot candidate' if p24 < 30 else 'High volatility - use small position'
            })
    return recs

# ── Main ───────────────────────────────────────────────────────────
def run():
    print(f'[dex] Scanning {len(WATCH_LIST)} pairs + boosts + takeovers...')
    results  = []
    alerts   = []
    pair_data = []

    for token in WATCH_LIST:
        pair = fetch_pair(token['search'])
        if not pair:
            print(f'[dex] No data for {token["name"]}')
            continue

        token_alerts, price, p5, p1h, p24, vol, liq = check_alerts(token['name'], pair)
        result = {
            'name':    token['name'],
            'price':   price,
            'change_5m':  p5,
            'change_1h':  p1h,
            'change_24h': p24,
            'volume_24h': vol,
            'liquidity':  liq,
            'alerts':  token_alerts,
            'url':     pair.get('url', ''),
            'checked': NOW.isoformat(),
        }
        results.append(result)
        pair_data.append({'name': token['name'], 'pair': pair})

        print(f'[dex] {token["name"]}: ${price} | 5m:{p5:+.1f}% 1h:{p1h:+.1f}% 24h:{p24:+.1f}%')
        if token_alerts:
            print(f'  ALERTS: {token_alerts}')
            alerts.append((token['name'], price, token_alerts, pair.get('url','')))

    # Boosts
    boosts = fetch_token_boosts()
    print(f'[dex] {len(boosts)} boosted tokens')

    # Takeovers
    takeovers = fetch_community_takeovers()
    print(f'[dex] {len(takeovers)} community takeovers')

    # Pionex recs
    recs = pionex_recommendation(pair_data)

    # Save state
    state = {
        'updated': NOW.isoformat(),
        'pairs':   results,
        'boosts':  boosts[:10],
        'takeovers': takeovers[:5],
        'pionex_recs': recs,
        'alerts_fired': len(alerts),
    }
    (DATA / 'dex_state.json').write_text(json.dumps(state, indent=2))
    print(f'[dex] Saved to data/dex_state.json')

    # Send Telegram alert if anything fired
    if alerts and TELEGRAM_TOKEN:
        lines = ['<b>DEX Alert — Meeko Nerve Center</b>', '']
        for name, price, token_alerts, url in alerts:
            lines.append(f'<b>{name}</b> @ ${price}')
            for a in token_alerts:
                lines.append(f'  {a}')
            if url: lines.append(f'  <a href="{url}">Chart</a>')
            lines.append('')
        if recs:
            lines.append('<b>Pionex Grid Bot candidates:</b>')
            for r in recs[:3]:
                lines.append(f"  {r['token']}: {r['note']}")
        telegram_send('\n'.join(lines))
        print(f'[dex] Sent {len(alerts)} alerts to Telegram')
    elif not TELEGRAM_TOKEN:
        print('[dex] No TELEGRAM_TOKEN — alerts printed only')
        for name, price, token_alerts, url in alerts:
            print(f'  ALERT: {name} @ ${price}: {token_alerts}')

    # Summary
    print(f'[dex] Done. {len(results)} pairs tracked, {len(alerts)} alerts, {len(recs)} Pionex recs')
    if recs:
        print('[dex] Pionex recommendations:')
        for r in recs:
            print(f"  {r['token']}: {r['note']} (24h vol: ${r['volume_24h']:,.0f})")

if __name__ == '__main__':
    run()
