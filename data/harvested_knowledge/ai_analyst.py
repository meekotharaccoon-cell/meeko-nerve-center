"""
AI ANALYST — Investment Intelligence Engine
============================================
Uses your LOCAL Mistral model (already running via Ollama) to analyze
markets and generate recommendations. No data leaves your machine.

YOUR AGENT'S ROLE:
  - Fetches real price data and technical indicators
  - Asks Mistral to analyze the opportunity
  - Writes a recommendation to the approval queue
  - YOU see it in the dashboard, read the reasoning, and APPROVE or REJECT
  - Only after your approval does trading_bridge even attempt to execute

WHAT THE AI ANALYZES:
  - Price trend (SMA, momentum)
  - Volume patterns
  - RSI (overbought/oversold)
  - Recent news sentiment (via free Yahoo Finance headlines)
  - Gaza Rose revenue context (your own system's income data)
"""

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))

BASE       = Path(r'C:\Users\meeko\Desktop\TRADING_SYSTEM')
DB_PATH    = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\gaza_rose.db')
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "mistral"


class AIAnalyst:
    """
    Wraps your local Mistral model with financial analysis context.
    Reads market data, builds a structured prompt, gets Mistral's analysis,
    and creates a pending approval entry.
    """

    def __init__(self):
        self.queue_file = BASE / 'approval_queue' / 'pending.json'
        self.approved_file = BASE / 'approval_queue' / 'approved.json'
        self.analysis_dir = BASE / 'data' / 'ai_analysis'
        for f in [self.queue_file, self.approved_file]:
            if not f.exists():
                f.write_text('{}')

    # ── ANALYZE A SYMBOL ───────────────────────────────────

    def analyze(self, symbol, context=''):
        """
        Full analysis pipeline for one symbol.
        Returns a recommendation dict ready for the approval queue.
        """
        print(f"\n  [ANALYST] Analyzing {symbol}...")

        # 1. Get market data
        data = self._get_market_data(symbol)
        if not data:
            return {'error': f'Could not fetch data for {symbol}'}

        # 2. Calculate indicators
        indicators = self._calc_indicators(data['history'])

        # 3. Get current quote
        quote = data.get('quote', {})

        # 4. Get news headlines
        headlines = self._get_headlines(symbol)

        # 5. Get Gaza Rose revenue context
        gz_context = self._get_gaza_rose_context()

        # 6. Build prompt and ask Mistral
        analysis_text = self._ask_mistral(
            symbol, quote, indicators, headlines, gz_context, context
        )

        # 7. Build recommendation
        rec = {
            'id':          str(uuid.uuid4()),
            'created':     datetime.now().isoformat(),
            'symbol':      symbol,
            'asset_type':  'crypto' if '-' in symbol else 'stock',
            'current_price': quote.get('price'),
            'indicators':  indicators,
            'headlines':   headlines[:3],
            'ai_analysis': analysis_text,
            'status':      'PENDING',
            'approved_by': None,
            'approved_at': None,
        }

        # 8. Save to pending queue
        self._add_to_queue(rec)

        # 9. Save full analysis to file
        out = self.analysis_dir / f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(out, 'w') as f:
            json.dump(rec, f, indent=2)

        print(f"  [ANALYST] Analysis complete. Pending your approval in dashboard.")
        return rec

    def analyze_watchlist(self, symbols):
        """Analyze a list of symbols and queue them all."""
        results = []
        for sym in symbols:
            try:
                r = self.analyze(sym)
                results.append(r)
            except Exception as e:
                results.append({'symbol': sym, 'error': str(e)})
        return results

    def get_pending(self):
        """Get all pending recommendations awaiting approval."""
        with open(self.queue_file) as f:
            return json.load(f)

    def approve(self, rec_id, override_qty=None, override_price=None):
        """
        YOU call this when you approve a recommendation.
        Returns an approval token that trading_bridge will check.
        """
        with open(self.queue_file) as f:
            pending = json.load(f)

        if rec_id not in pending:
            raise ValueError(f"Recommendation {rec_id} not found in queue")

        rec = pending[rec_id]
        token = str(uuid.uuid4())

        # Save to approved file
        with open(self.approved_file) as f:
            approved = json.load(f)

        approved[token] = {
            'rec_id':    rec_id,
            'symbol':    rec['symbol'],
            'side':      rec.get('action', 'BUY'),
            'qty':       override_qty or rec.get('suggested_qty', 1),
            'price':     override_price or rec.get('current_price'),
            'approved_at': datetime.now().isoformat(),
            'used':      False,
        }

        with open(self.approved_file, 'w') as f:
            json.dump(approved, f, indent=2)

        # Update pending
        rec['status'] = 'APPROVED'
        rec['approved_at'] = datetime.now().isoformat()
        rec['approval_token'] = token
        pending[rec_id] = rec

        with open(self.queue_file, 'w') as f:
            json.dump(pending, f, indent=2)

        print(f"  [ANALYST] Approved {rec['symbol']} — token: {token[:8]}...")
        return token

    def reject(self, rec_id, reason=''):
        """Reject a recommendation — it will not be executed."""
        with open(self.queue_file) as f:
            pending = json.load(f)
        if rec_id in pending:
            pending[rec_id]['status'] = 'REJECTED'
            pending[rec_id]['rejected_at'] = datetime.now().isoformat()
            pending[rec_id]['reject_reason'] = reason
            with open(self.queue_file, 'w') as f:
                json.dump(pending, f, indent=2)
        print(f"  [ANALYST] Rejected {rec_id}")

    # ── MARKET DATA ────────────────────────────────────────

    def _get_market_data(self, symbol):
        from trading_bridge import get_quote_free, get_history_free
        try:
            quote   = get_quote_free(symbol)
            history = get_history_free(symbol, period='3mo', interval='1d')
            return {'quote': quote, 'history': history}
        except Exception as e:
            print(f"  [ANALYST] Data error for {symbol}: {e}")
            return None

    def _calc_indicators(self, history):
        """Calculate SMA, RSI, momentum from price history."""
        if not history or len(history) < 14:
            return {}
        closes = [float(h['close']) for h in history if h.get('close')]
        try:
            import ta
            import pandas as pd
            s = pd.Series(closes)
            sma_20 = float(s.rolling(20).mean().iloc[-1]) if len(closes) >= 20 else None
            sma_50 = float(s.rolling(50).mean().iloc[-1]) if len(closes) >= 50 else None
            rsi = float(ta.momentum.RSIIndicator(s, window=14).rsi().iloc[-1])
            macd_obj = ta.trend.MACD(s)
            macd = float(macd_obj.macd().iloc[-1])
            macd_signal = float(macd_obj.macd_signal().iloc[-1])
            current = closes[-1]
            momentum = round((current - closes[-14]) / closes[-14] * 100, 2)
            return {
                'current_price': current,
                'sma_20':        round(sma_20, 4) if sma_20 else None,
                'sma_50':        round(sma_50, 4) if sma_50 else None,
                'rsi':           round(rsi, 2),
                'macd':          round(macd, 4),
                'macd_signal':   round(macd_signal, 4),
                'momentum_14d':  momentum,
                'trend':         'BULLISH' if current > (sma_20 or current) else 'BEARISH',
            }
        except Exception as e:
            closes_arr = closes[-20:]
            avg = sum(closes_arr) / len(closes_arr)
            return {
                'current_price': closes[-1],
                'sma_approx':    round(avg, 4),
                'momentum_14d':  round((closes[-1] - closes[-14]) / closes[-14] * 100, 2),
            }

    def _get_headlines(self, symbol):
        """Get recent news headlines via yfinance."""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            news = ticker.news or []
            return [n.get('title', '') for n in news[:5]]
        except Exception:
            return []

    def _get_gaza_rose_context(self):
        """Pull Gaza Rose revenue context so AI knows your financial situation."""
        try:
            import sqlite3
            conn = sqlite3.connect(str(DB_PATH))
            rows = conn.execute(
                "SELECT platform, status FROM revenue_connections ORDER BY id DESC LIMIT 5"
            ).fetchall()
            conn.close()
            connected = [r[0] for r in rows if r[1] == 'connected']
            return f"Gaza Rose revenue channels connected: {', '.join(connected) or 'none yet'}"
        except Exception:
            return "Gaza Rose revenue context unavailable"

    # ── MISTRAL ANALYSIS ───────────────────────────────────

    def _ask_mistral(self, symbol, quote, indicators, headlines, gz_context, extra_context):
        """Send analysis request to local Mistral. Returns analysis text."""
        price    = quote.get('price', 'unknown')
        rsi      = indicators.get('rsi', 'N/A')
        trend    = indicators.get('trend', 'N/A')
        momentum = indicators.get('momentum_14d', 'N/A')
        sma20    = indicators.get('sma_20', 'N/A')
        news_str = '\n'.join(f"  - {h}" for h in headlines) if headlines else "  No headlines available"

        prompt = f"""You are a financial analysis assistant for an independent investor named Meeko.
Your job is to analyze {symbol} and give a clear, honest recommendation.

IMPORTANT CONSTRAINTS:
- Meeko must manually approve every single trade. You NEVER execute anything.
- Always mention risks clearly. Never be overconfident.
- Consider that 70% of Meeko's Gaza Rose revenue goes to PCRF charity — capital preservation matters.
- Keep analysis under 300 words. Be direct.

MARKET DATA FOR {symbol}:
- Current price: ${price}
- RSI (14): {rsi} (>70 overbought, <30 oversold)
- Trend vs SMA20: {trend} (SMA20 = {sma20})
- 14-day momentum: {momentum}%

RECENT HEADLINES:
{news_str}

CONTEXT:
{gz_context}
{extra_context}

Provide:
1. RECOMMENDATION: BUY / SELL / HOLD / WATCH (pick one)
2. REASONING: 2-3 sentences explaining why
3. SUGGESTED ENTRY: price level or "current market"
4. RISK LEVEL: LOW / MEDIUM / HIGH
5. KEY RISK: the one thing that could make this wrong
6. SUGGESTED POSITION SIZE: small (1-2% of portfolio) / medium (3-5%) / skip

Be direct. Meeko will read this before approving or rejecting."""

        try:
            resp = requests.post(OLLAMA_URL, json={
                'model':  MODEL,
                'prompt': prompt,
                'stream': False,
            }, timeout=60)
            return resp.json().get('response', 'No response from Mistral')
        except Exception as e:
            return f"Mistral offline or error: {e}\n\nBasic analysis: RSI={rsi}, Trend={trend}, Momentum={momentum}%"

    def _add_to_queue(self, rec):
        with open(self.queue_file) as f:
            pending = json.load(f)
        pending[rec['id']] = rec
        with open(self.queue_file, 'w') as f:
            json.dump(pending, f, indent=2)


if __name__ == '__main__':
    analyst = AIAnalyst()
    symbols = ['AAPL', 'BTC-USD', 'ETH-USD']
    print(f"\nAnalyzing: {symbols}")
    for sym in symbols:
        r = analyst.analyze(sym)
        print(f"\n=== {sym} ===")
        print(r.get('ai_analysis', r.get('error', 'unknown')))
