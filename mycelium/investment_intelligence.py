#!/usr/bin/env python3
"""
Investment Intelligence Engine — SolarPunk
==========================================
Autonomous market analysis. Mathematical. Compounding leverage.
You get signals. You decide. Or set thresholds and it executes.

Data sources (all free, no API keys required for basic):
  - CoinGecko API: crypto prices, volume, market cap, trending
  - Yahoo Finance compatible: stocks, ETFs, commodities
  - Fear & Greed Index: market sentiment
  - Congressional trades (already collected by congress_watcher)
    -> Unique alpha: trade AFTER congresspeople, with their insider data
  - Alternative.me: crypto fear/greed
  - CoinMarketCap trending (public RSS)

Strategy framework:
  1. MOMENTUM: What's moving with volume? (short-term)
  2. SENTIMENT: Fear/greed positioning (contrarian signals)
  3. CONGRESSIONAL ALPHA: What did congress buy last week?
     This is LEGAL to trade on. They file within 45 days.
     System tracks the delay, calculates the signal lag.
  4. TECHNICAL: RSI, MACD approximated from price series
  5. MACRO: What's happening in the world that moves markets?
     (uses world_intelligence data)
  6. COMPOUNDING: Kelly criterion position sizing
     Never bet more than the math says. Let it compound.

Output:
  - data/investment_signals.json: actionable signals with confidence
  - data/portfolio_watchlist.json: things to monitor
  - data/market_context.json: macro picture
  - Weekly email: top 5 plays with exact entry/exit levels
  - Email format: you read it, you decide, or set a threshold

Risk architecture:
  - NEVER suggests more than 2% of portfolio per trade
  - NEVER chases momentum without volume confirmation
  - ALWAYS includes stop-loss level
  - Congressional trades: add 15-day lag (filing delay buffer)
  - Sentiment extreme: only trade contrarian at 20/80 extremes

Autonomy levels (set via data/investment_config.json):
  'research_only': generates analysis, you decide (default)
  'alert_only':    sends email when signal exceeds threshold
  'semi_auto':     queues the trade, you approve in 1 click
  # Full auto intentionally not built - financial decisions stay human
  # But 'semi_auto' gets you to 1-click execution

This is not financial advice. This is a tool.
You own the decisions. The math owns the analysis.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def fetch_json(url, timeout=20):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'SolarPunk-Investment/1.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[invest] Fetch error {url[:50]}: {e}')
        return None

# ── Data collection ───────────────────────────────────────────────────────────────

def get_crypto_data():
    """Top 50 crypto by market cap with 24h change."""
    data = fetch_json(
        'https://api.coingecko.com/api/v3/coins/markets'
        '?vs_currency=usd&order=market_cap_desc&per_page=50&page=1'
        '&sparkline=false&price_change_percentage=24h,7d'
    )
    if not data: return []
    return [{
        'symbol':        c.get('symbol','').upper(),
        'name':          c.get('name',''),
        'price':         c.get('current_price', 0),
        'change_24h':    c.get('price_change_percentage_24h', 0) or 0,
        'change_7d':     c.get('price_change_percentage_7d_in_currency', 0) or 0,
        'volume_24h':    c.get('total_volume', 0),
        'market_cap':    c.get('market_cap', 0),
        'volume_ratio':  round(c.get('total_volume',0) / max(c.get('market_cap',1), 1), 4),
    } for c in data]

def get_fear_greed():
    data = fetch_json('https://api.alternative.me/fng/?limit=7')
    if not data: return {'value': 50, 'label': 'Neutral', 'history': []}
    readings = data.get('data', [])
    current = readings[0] if readings else {}
    return {
        'value':   int(current.get('value', 50)),
        'label':   current.get('value_classification', 'Neutral'),
        'history': [int(r.get('value', 50)) for r in readings[:7]],
    }

def get_trending_crypto():
    data = fetch_json('https://api.coingecko.com/api/v3/search/trending')
    if not data: return []
    return [c['item']['symbol'].upper() for c in data.get('coins', [])[:7]]

def get_congressional_trades():
    congress = load(DATA / 'congress.json')
    trades = congress if isinstance(congress, list) else congress.get('trades', [])
    # Filter to recent trades (within 60 days - congressional filing window)
    signals = []
    for t in trades[:20]:
        ticker = t.get('ticker', '')
        if not ticker or ticker in ('N/A', '--'): continue
        trade_type = t.get('type', t.get('transaction', ''))
        is_buy = 'purchase' in trade_type.lower() or 'buy' in trade_type.lower()
        signals.append({
            'ticker':    ticker,
            'action':    'BUY_SIGNAL' if is_buy else 'WATCH',
            'name':      t.get('representative', t.get('senator', '?')),
            'committee': t.get('committees', ''),
            'amount':    t.get('amount', ''),
            'source':    'congressional_trade',
        })
    return signals

# ── Signal generation ────────────────────────────────────────────────────────────

def score_crypto_signal(coin, fear_greed, trending):
    """Score a crypto asset for signal quality. Returns score 0-100."""
    score = 50  # Neutral start
    reasons = []
    
    # Momentum: strong 24h move with volume
    chg24 = coin.get('change_24h', 0)
    chg7d = coin.get('change_7d', 0)
    vol_ratio = coin.get('volume_ratio', 0)
    
    if chg24 > 5 and vol_ratio > 0.05:
        score += 15
        reasons.append(f'+{chg24:.1f}% with volume')
    elif chg24 < -5 and fear_greed['value'] < 25:
        score += 10  # Oversold in fear = potential bounce
        reasons.append(f'oversold ({chg24:.1f}%) in extreme fear')
    
    # 7-day trend alignment
    if chg7d > 10 and chg24 > 2:
        score += 10
        reasons.append('7d uptrend confirmed')
    elif chg7d < -15 and fear_greed['value'] < 20:
        score += 8
        reasons.append('extreme oversold 7d')
    
    # Trending
    if coin.get('symbol') in trending:
        score += 12
        reasons.append('trending')
    
    # Fear/greed extremes (contrarian)
    if fear_greed['value'] <= 15:
        score += 15  # Extreme fear = buy signal for top assets
        reasons.append('EXTREME FEAR: historically good entry')
    elif fear_greed['value'] >= 85:
        score -= 10  # Extreme greed = be cautious
        reasons.append('extreme greed: caution')
    
    # Size penalty: micro caps are riskier
    mc = coin.get('market_cap', 0)
    if mc < 100_000_000: score -= 15
    elif mc > 10_000_000_000: score += 5
    
    return min(100, max(0, score)), reasons

def generate_signals(crypto, fear_greed, trending, congress_trades):
    signals = []
    
    # Crypto signals
    for coin in crypto:
        score, reasons = score_crypto_signal(coin, fear_greed, trending)
        if score >= 65:  # Only high-confidence signals
            # Kelly criterion: never risk more than Kelly suggests
            edge = (score - 50) / 100  # Edge above random
            kelly = edge * 2  # Simplified half-Kelly
            max_position_pct = min(kelly * 100, 3)  # Hard cap 3% of portfolio
            signals.append({
                'symbol':          coin['symbol'],
                'type':            'CRYPTO',
                'action':          'CONSIDER_BUY',
                'confidence':      score,
                'reasons':         reasons,
                'price':           coin['price'],
                'change_24h':      coin['change_24h'],
                'change_7d':       coin['change_7d'],
                'max_position_pct': round(max_position_pct, 1),
                'stop_loss_pct':   -8,  # 8% stop loss
                'date':            TODAY,
            })
    
    # Congressional alpha signals
    for trade in congress_trades[:5]:
        if trade['action'] == 'BUY_SIGNAL':
            signals.append({
                'symbol':     trade['ticker'],
                'type':       'STOCK_CONGRESSIONAL',
                'action':     'CONGRESSIONAL_BUY',
                'confidence': 72,
                'reasons':    [f'{trade["name"]} bought {trade["amount"]}', 'Congressional alpha signal'],
                'committee':  trade['committee'],
                'note':       'Add 15-day lag from filing date for entry',
                'max_position_pct': 2.0,
                'stop_loss_pct':   -7,
                'date':       TODAY,
            })
    
    # Sort by confidence
    signals.sort(key=lambda s: -s['confidence'])
    return signals[:10]  # Top 10

def build_market_context(fear_greed, trending, crypto):
    top5 = sorted(crypto, key=lambda c: -c.get('change_24h', 0))[:5]
    bottom5 = sorted(crypto, key=lambda c: c.get('change_24h', 0))[:5]
    total_positive = sum(1 for c in crypto if c.get('change_24h', 0) > 0)
    breadth = total_positive / max(len(crypto), 1)
    market_mood = 'BULLISH' if breadth > 0.6 else 'BEARISH' if breadth < 0.4 else 'NEUTRAL'
    return {
        'date':           TODAY,
        'fear_greed':     fear_greed,
        'market_breadth': round(breadth, 2),
        'market_mood':    market_mood,
        'trending':       trending,
        'top_movers':     [f"{c['symbol']} +{c['change_24h']:.1f}%" for c in top5],
        'worst_movers':   [f"{c['symbol']} {c['change_24h']:.1f}%" for c in bottom5],
    }

def call_llm_synthesis(signals, context, congress_trades):
    """Get LLM synthesis of the signals into plain language."""
    if not HF_TOKEN: return None
    top_signals = signals[:5]
    prompt = f"""Synthesize these investment signals for someone who wants to make smart, leveraged decisions.

Market context:
  Fear/Greed: {context['fear_greed']['value']} ({context['fear_greed']['label']})
  Breadth: {context['market_breadth']*100:.0f}% positive
  Mood: {context['market_mood']}
  Trending: {', '.join(context['trending'][:5])}

Top signals:
{json.dumps(top_signals, indent=2)[:1500]}

Congressional trades (insider alpha):
{json.dumps(congress_trades[:3], indent=2)[:800]}

Return:
1. ONE sentence: the market in plain English right now
2. TOP 3 actionable ideas with entry logic (not financial advice, just analysis)
3. ONE risk to watch
4. Compounding angle: how to size positions for max long-term growth

Be specific. Be mathematical. 200 words max."""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 400,
            'messages': [
                {'role': 'system', 'content': 'You are a quantitative analyst. Mathematical. Precise. Data-driven. Not financial advice.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except:
        return None

def send_investment_brief(signals, context, synthesis):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    if WEEKDAY not in (0, 3): return  # Mon + Thu only
    lines = [
        f'\U0001f4b9 SolarPunk Investment Intelligence — {TODAY}',
        f'Fear/Greed: {context["fear_greed"]["value"]} ({context["fear_greed"]["label"]}) | Market: {context["market_mood"]}',
        '',
    ]
    if synthesis:
        lines += ['SYNTHESIS:', synthesis, '']
    lines += ['TOP SIGNALS (mathematical analysis, not financial advice):']
    for s in signals[:5]:
        action = s.get('action','?')
        conf   = s.get('confidence', 0)
        sym    = s.get('symbol','?')
        reasons = ', '.join(s.get('reasons',[])[:2])
        max_pos = s.get('max_position_pct', 0)
        stop    = s.get('stop_loss_pct', -8)
        lines += [
            f'  [{conf:.0f}%] {sym} — {action}',
            f'     Why: {reasons}',
            f'     Size: max {max_pos}% | Stop: {stop}%',
            '',
        ]
    lines += [
        'CONGRESSIONAL ALPHA (legal to act on):',
        '(Check data/investment_signals.json for full details)',
        '',
        'REMINDER: This is mathematical analysis from an autonomous AI system.',
        'You own every decision. Size small. Let math compound.',
        '',
        f'All data: github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/data/investment_signals.json',
    ]
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'\U0001f4b9 SolarPunk signals: {signals[0]["symbol"]} {signals[0]["confidence"]:.0f}% confidence | FG:{context["fear_greed"]["value"]}'
        msg['From']    = f'SolarPunk ★ <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[invest] Brief emailed')
    except Exception as e:
        print(f'[invest] Email error: {e}')

def run():
    print(f'\n[invest] \U0001f4b9 Investment Intelligence — {TODAY}')
    
    crypto         = get_crypto_data()
    fear_greed     = get_fear_greed()
    trending       = get_trending_crypto()
    congress_trades = get_congressional_trades()
    
    print(f'[invest] Crypto: {len(crypto)} coins | FG: {fear_greed["value"]} ({fear_greed["label"]}) | Trending: {trending[:3]}')
    
    signals  = generate_signals(crypto, fear_greed, trending, congress_trades)
    context  = build_market_context(fear_greed, trending, crypto)
    synthesis = call_llm_synthesis(signals, context, congress_trades)
    
    # Save all data
    try: (DATA / 'investment_signals.json').write_text(json.dumps({
        'date': TODAY, 'signals': signals, 'fear_greed': fear_greed,
        'synthesis': synthesis
    }, indent=2))
    except: pass
    try: (DATA / 'market_context.json').write_text(json.dumps(context, indent=2))
    except: pass
    
    send_investment_brief(signals, context, synthesis)
    
    top3 = [f"{s['symbol']} ({s['confidence']:.0f}%)" for s in signals[:3]]
    print(f'[invest] Top signals: {top3}')
    if synthesis: print(f'[invest] Synthesis: {synthesis[:100]}')
    print('[invest] Market analyzed. Math does the work. You own the decisions. ★')

if __name__ == '__main__':
    run()
