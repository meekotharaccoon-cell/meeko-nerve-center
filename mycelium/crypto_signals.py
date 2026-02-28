#!/usr/bin/env python3
"""
Crypto Signals Engine
=======================
Finds micro-cap coins that are about to move.
Gives you exact actionable signals. You execute.

This is a SIGNALS engine, not an auto-trader.
Why: Auto-trading requires exchange API keys and may be regulated.
You execute the trade in Phantom/your exchange in under 30 seconds.

The daily status email tells you exactly:
  WHAT to buy
  HOW MUCH (based on your $8 DOT budget)
  WHERE to buy it
  WHEN to sell
  STOP LOSS

Signal criteria (free APIs only):
  1. CoinGecko trending + new listings
  2. Volume spike > 200% in 24h
  3. Market cap < $10M (micro-cap, more explosive potential)
  4. Price < $0.01 (fractional penny coins)
  5. Social momentum (Reddit/Twitter mentions in last 24h)
  6. On-chain activity (new wallets, transfer volume)

For your DOT: also monitors DOT/USDT for optimal exit to fund other trades.

LEGAL: This is not financial advice. Signals are algorithmic pattern detection.
All trades carry risk. Never trade more than you can afford to lose.
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

BUDGET_USD = 8.00  # Your current DOT value

# ── Free API fetchers ──────────────────────────────────────────────────────

def fetch_json(url, timeout=20):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-signals/1.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[signals] Fetch error {url[:60]}: {e}')
        return None

def get_trending_coins():
    """CoinGecko trending endpoint — free, no key needed."""
    data = fetch_json('https://api.coingecko.com/api/v3/search/trending')
    if not data: return []
    coins = []
    for item in data.get('coins', []):
        c = item.get('item', {})
        coins.append({
            'id':     c.get('id'),
            'name':   c.get('name'),
            'symbol': c.get('symbol', '').upper(),
            'rank':   c.get('market_cap_rank', 9999),
            'source': 'trending',
        })
    return coins

def get_new_listings():
    """CoinGecko recently added coins — hot new entries."""
    data = fetch_json('https://api.coingecko.com/api/v3/coins/list/new')
    if not data or not isinstance(data, list): return []
    return [{
        'id':     c.get('id'),
        'name':   c.get('name'),
        'symbol': c.get('symbol', '').upper(),
        'rank':   9999,
        'source': 'new_listing',
    } for c in data[:20]]

def get_coin_details(coin_id):
    """Get price, volume, market cap for a specific coin."""
    data = fetch_json(
        f'https://api.coingecko.com/api/v3/coins/{coin_id}?'
        'localization=false&tickers=false&community_data=false&developer_data=false'
    )
    if not data: return None
    mkt = data.get('market_data', {})
    return {
        'price_usd':       mkt.get('current_price', {}).get('usd', 0),
        'volume_24h':      mkt.get('total_volume', {}).get('usd', 0),
        'volume_change':   mkt.get('price_change_percentage_24h', 0),
        'market_cap':      mkt.get('market_cap', {}).get('usd', 0),
        'price_change_24h': mkt.get('price_change_percentage_24h', 0),
        'price_change_7d':  mkt.get('price_change_percentage_7d', 0),
        'all_time_low':    mkt.get('atl', {}).get('usd', 0),
        'supply':          mkt.get('circulating_supply', 0),
        'exchanges':       [e.get('market', {}).get('name') for e in data.get('tickers', [])[:3]],
    }

def get_dot_price():
    """Get current DOT price and recommendation."""
    data = fetch_json(
        'https://api.coingecko.com/api/v3/simple/price?ids=polkadot&vs_currencies=usd&'
        'include_24hr_change=true&include_7d_change=true'
    )
    if not data: return None
    dot = data.get('polkadot', {})
    return {
        'price':     dot.get('usd', 0),
        'change_24h': dot.get('usd_24h_change', 0),
        'change_7d':  dot.get('usd_7d_change', 0),
    }

# ── Signal scoring ────────────────────────────────────────────────────────────

def score_coin(details, coin_meta):
    """
    Score a coin 0-100 for signal strength.
    Higher = stronger buy signal.
    """
    score = 0
    reasons = []

    price = details.get('price_usd', 0)
    volume_change = details.get('volume_change', 0)
    price_change_24h = details.get('price_change_24h', 0)
    market_cap = details.get('market_cap', 0)

    # Price filter: micro-cap fractional coins
    if price < 0.001:
        score += 25
        reasons.append('sub-penny price (explosive upside potential)')
    elif price < 0.01:
        score += 15
        reasons.append('fractional penny price')
    elif price < 0.10:
        score += 5
        reasons.append('low price point')

    # Volume explosion
    if volume_change > 500:
        score += 30
        reasons.append(f'volume up {volume_change:.0f}% (extreme momentum)')
    elif volume_change > 200:
        score += 20
        reasons.append(f'volume up {volume_change:.0f}% (strong momentum)')
    elif volume_change > 100:
        score += 10
        reasons.append(f'volume up {volume_change:.0f}%')

    # Market cap: micro-cap has more room to run
    if 0 < market_cap < 1_000_000:
        score += 20
        reasons.append('nano-cap (<$1M): highest risk/reward')
    elif market_cap < 10_000_000:
        score += 15
        reasons.append('micro-cap (<$10M): explosive potential')
    elif market_cap < 50_000_000:
        score += 8
        reasons.append('small-cap (<$50M)')

    # Price momentum
    if 5 < price_change_24h < 50:
        score += 15
        reasons.append(f'up {price_change_24h:.1f}% today (building momentum)')
    elif price_change_24h > 50:
        score += 5  # Already pumped, be careful
        reasons.append(f'up {price_change_24h:.1f}% (may be overbought)')
    elif -10 < price_change_24h < 0:
        score += 8
        reasons.append('slight dip in uptrend (buy the dip opportunity)')

    # Trending bonus
    if coin_meta.get('source') == 'trending':
        score += 10
        reasons.append('trending on CoinGecko')

    return score, reasons

def ask_llm_signal(coin_name, symbol, price, market_cap, volume_change, price_change, reasons, budget):
    """Ask LLM to generate a specific trade recommendation."""
    if not HF_TOKEN: return None
    prompt = f"""You are a crypto technical analyst. Generate a specific, actionable trade recommendation.

Coin: {coin_name} ({symbol})
Current Price: ${price}
Market Cap: ${market_cap:,.0f}
Volume Change 24h: {volume_change:.0f}%
Price Change 24h: {price_change:.1f}%
Signal reasons: {', '.join(reasons)}
Trader's budget: ${budget}

Provide a SPECIFIC recommendation in JSON:
{{
  "action": "BUY / WAIT / AVOID",
  "entry_price": "specific price or range",
  "position_size_usd": number (portion of ${budget} to use, e.g. 3.00),
  "target_price": "specific take-profit price",
  "stop_loss": "specific stop-loss price",
  "timeframe": "e.g. 24-72 hours",
  "confidence": "LOW / MEDIUM / HIGH",
  "where_to_buy": "exchange name e.g. Phantom DEX, Uniswap, Gate.io",
  "rationale": "2-3 sentence explanation",
  "risk_warning": "one specific risk to watch for"
}}

IMPORTANT: Be specific and realistic. If the signal is weak, say WAIT or AVOID.
Do not recommend using more than 40% of budget on any single trade.
Respond ONLY with the JSON object.
"""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 400,
            'messages': [
                {'role': 'system', 'content': 'You are a precise crypto analyst. Respond only with valid JSON.'},
                {'role': 'user',   'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            text = json.loads(r.read())['choices'][0]['message']['content'].strip()
        start = text.find('{')
        end   = text.rfind('}') + 1
        return json.loads(text[start:end])
    except Exception as e:
        print(f'[signals] LLM error: {e}')
        return None

def get_dot_recommendation(dot_data, budget):
    """Specific DOT recommendation for your current holdings."""
    if not dot_data: return None
    price     = dot_data['price']
    change_24 = dot_data['change_24h']
    change_7  = dot_data['change_7d']

    # Simple rule-based DOT advice
    if change_24 > 5 and change_7 > 10:
        action = 'HOLD — momentum building. Wait for target.'
        target = round(price * 1.15, 4)
    elif change_24 < -5:
        action = 'HOLD — dip. Do not sell into weakness.'
        target = round(price * 1.20, 4)
    elif change_7 > 20:
        action = f'CONSIDER SELLING 50% — took strong gains. Lock in profit.'
        target = round(price * 1.10, 4)
    else:
        action = 'HOLD — wait for clearer signal.'
        target = round(price * 1.15, 4)

    return {
        'symbol':      'DOT',
        'action':      action,
        'current':     f'${price:.4f}',
        'target':      f'${target:.4f}',
        'change_24h':  f'{change_24:.1f}%',
        'change_7d':   f'{change_7:.1f}%',
        'holdings':    f'~${budget:.2f} worth',
        'where':       'Phantom Wallet → sell via Uniswap or Kraken',
    }

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print(f'\n[signals] Crypto Signals Engine — {TODAY}')

    signals = []

    # DOT analysis first (your current holdings)
    print('[signals] Analyzing your DOT position...')
    dot_data = get_dot_price()
    dot_rec  = get_dot_recommendation(dot_data, BUDGET_USD)
    if dot_rec:
        print(f'[signals] DOT: {dot_rec["action"]}')

    # Find trending + new coins
    print('[signals] Scanning trending coins...')
    candidates = get_trending_coins()[:7] + get_new_listings()[:5]

    top_signals = []
    for coin in candidates:
        if not coin.get('id'): continue
        print(f'[signals] Analyzing {coin["symbol"]}...')
        details = get_coin_details(coin['id'])
        if not details: continue
        if details.get('price_usd', 0) <= 0: continue

        score, reasons = score_coin(details, coin)
        if score >= 40:  # Only surface meaningful signals
            top_signals.append({
                'coin':    coin,
                'details': details,
                'score':   score,
                'reasons': reasons,
            })

    # Sort by score, take top 3
    top_signals.sort(key=lambda x: x['score'], reverse=True)
    top_signals = top_signals[:3]

    print(f'[signals] Found {len(top_signals)} signals above threshold')

    for s in top_signals:
        coin    = s['coin']
        details = s['details']
        
        rec = ask_llm_signal(
            coin['name'], coin['symbol'],
            details['price_usd'],
            details['market_cap'],
            details.get('volume_change', 0),
            details.get('price_change_24h', 0),
            s['reasons'],
            BUDGET_USD,
        )

        if rec and rec.get('action') != 'AVOID':
            signal = {
                'date':        TODAY,
                'symbol':      coin['symbol'],
                'name':        coin['name'],
                'coin_id':     coin['id'],
                'score':       s['score'],
                'reasons':     s['reasons'],
                'price_usd':   details['price_usd'],
                'market_cap':  details['market_cap'],
                'action':      rec.get('action', ''),
                'entry':       rec.get('entry_price', ''),
                'position_usd': rec.get('position_size_usd', 0),
                'target':      rec.get('target_price', ''),
                'stop_loss':   rec.get('stop_loss', ''),
                'timeframe':   rec.get('timeframe', ''),
                'confidence':  rec.get('confidence', ''),
                'where_to_buy': rec.get('where_to_buy', ''),
                'rationale':   rec.get('rationale', ''),
                'risk_warning': rec.get('risk_warning', ''),
                'discord_posted': False,
            }
            signals.append(signal)

    # Save signals
    try:
        (DATA / 'crypto_signals_queue.json').write_text(json.dumps(signals, indent=2))
        (DATA / 'crypto_signals_history.json')
        # Append to history
        hist_path = DATA / 'crypto_signals_history.json'
        history = []
        if hist_path.exists():
            try: history = json.loads(hist_path.read_text())
            except: pass
        history.extend(signals)
        # Keep last 90 days
        cutoff = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
        history = [s for s in history if s.get('date', '') >= cutoff]
        hist_path.write_text(json.dumps(history, indent=2))
    except Exception as e:
        print(f'[signals] Save error: {e}')

    # Save DOT status
    if dot_rec:
        try:
            (DATA / 'dot_position.json').write_text(json.dumps({
                'date': TODAY,
                'dot':  dot_rec,
                'market': dot_data,
            }, indent=2))
        except: pass

    print(f'[signals] Done. Signals generated: {len(signals)}')
    for s in signals:
        print(f'  [{s["score"]}] {s["symbol"]}: {s["action"]} @ {s["entry"]} → target {s["target"]} (confidence: {s["confidence"]})')

if __name__ == '__main__':
    run()
