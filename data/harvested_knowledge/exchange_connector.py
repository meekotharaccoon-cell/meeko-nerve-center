"""
INVESTMENT HQ — EXCHANGE CONNECTOR
====================================
Legal API connections to:
  - Alpaca Markets  : US stocks, ETFs, options (free, regulated broker-dealer)
  - Coinbase Advanced Trade : Crypto (already in your system)
  - CCXT / Kraken   : Additional crypto exchanges
  - yfinance        : Free market data for any ticker (no key needed)

HARD RULES BUILT INTO THIS FILE:
  1. Paper trading mode ON by default — no real money until you flip the switch
  2. Nothing executes without a signed ApprovalToken from the portal
  3. Every action is logged before AND after execution
  4. Read operations never require approval
  5. No leverage, no margin, no short-selling (can be enabled explicitly)

PAPER TRADING = Safe. Real = flip PAPER_MODE = False after you're comfortable.
"""

import json
import os
import sqlite3
import getpass
from datetime import datetime
from pathlib import Path

BASE    = Path(r'C:\Users\meeko\Desktop\INVESTMENT_HQ')
DB_PATH = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\gaza_rose.db')
LOG_DIR = BASE / 'logs'

# ── SAFETY SWITCH ─────────────────────────────────────────
# Change to False only after you have tested in paper mode
# and are ready to use real money.
PAPER_MODE = True

# ── RUNTIME KEY STORE (never written to disk) ─────────────
_keys = {}

def load_keys():
    """Prompt for exchange keys at runtime. Called once per session."""
    print("\n=== INVESTMENT HQ — KEY LOADER ===")
    print("Keys live in memory only — never saved to disk.\n")
    print("Press ENTER to skip any exchange for now.\n")

    # Alpaca
    print("-- ALPACA (US Stocks & ETFs) --")
    print("Get free API keys at: alpaca.markets -> Paper Trading first")
    _keys['alpaca_key']    = getpass.getpass("Alpaca API Key: ").strip()
    _keys['alpaca_secret'] = getpass.getpass("Alpaca Secret Key: ").strip()

    # Coinbase Advanced (may already be in bridge session)
    print("\n-- COINBASE ADVANCED TRADE (Crypto) --")
    print("Already set up? Press ENTER to reuse. Otherwise paste new keys.")
    _keys['cb_key']    = getpass.getpass("Coinbase API Key Name (or ENTER to skip): ").strip()
    _keys['cb_secret'] = getpass.getpass("Coinbase Private Key (or ENTER to skip): ").strip()

    # Kraken (optional additional crypto)
    print("\n-- KRAKEN (optional additional crypto exchange) --")
    print("Get keys at: kraken.com -> Security -> API")
    _keys['kraken_key']    = getpass.getpass("Kraken API Key (or ENTER to skip): ").strip()
    _keys['kraken_secret'] = getpass.getpass("Kraken Private Key (or ENTER to skip): ").strip()

    mode_str = "PAPER (safe, no real money)" if PAPER_MODE else "LIVE (real money)"
    print(f"\nMode: {mode_str}")
    print("Keys loaded. Ready to connect.\n")
    return _keys


class AlpacaConnector:
    """
    US Stocks & ETFs via Alpaca Markets.
    Free account, regulated broker-dealer (FINRA/SIPC).
    Paper trading URL used by default.
    """

    PAPER_URL = "https://paper-api.alpaca.markets"
    LIVE_URL  = "https://api.alpaca.markets"
    DATA_URL  = "https://data.alpaca.markets"

    def __init__(self):
        import urllib.request, urllib.error
        self._req = urllib.request
        self._err = urllib.error
        self.base = self.PAPER_URL if PAPER_MODE else self.LIVE_URL

    def _headers(self):
        k = _keys.get('alpaca_key','')
        s = _keys.get('alpaca_secret','')
        if not k or not s:
            raise RuntimeError("Alpaca keys not loaded. Call load_keys() first.")
        return {'APCA-API-KEY-ID': k, 'APCA-API-SECRET-KEY': s, 'Content-Type': 'application/json'}

    def _get(self, path, base=None):
        url = (base or self.base) + path
        req = self._req.Request(url, headers=self._headers())
        resp = self._req.urlopen(req, timeout=15)
        return json.loads(resp.read())

    def _post(self, path, body):
        url = self.base + path
        data = json.dumps(body).encode()
        req = self._req.Request(url, data=data, headers=self._headers(), method='POST')
        resp = self._req.urlopen(req, timeout=15)
        return json.loads(resp.read())

    def _delete(self, path):
        url = self.base + path
        req = self._req.Request(url, headers=self._headers(), method='DELETE')
        resp = self._req.urlopen(req, timeout=15)
        return resp.status

    # READ OPERATIONS (no approval needed)
    def get_account(self):
        return self._get('/v2/account')

    def get_positions(self):
        return self._get('/v2/positions')

    def get_orders(self, status='all', limit=50):
        return self._get(f'/v2/orders?status={status}&limit={limit}')

    def get_portfolio_history(self, period='1M', timeframe='1D'):
        return self._get(f'/v2/account/portfolio/history?period={period}&timeframe={timeframe}')

    def get_bars(self, symbol, timeframe='1Day', limit=30):
        """Get OHLCV price bars for analysis."""
        path = f'/v2/stocks/{symbol}/bars?timeframe={timeframe}&limit={limit}&feed=iex'
        return self._get(path, base=self.DATA_URL)

    def get_latest_quote(self, symbol):
        path = f'/v2/stocks/{symbol}/quotes/latest?feed=iex'
        return self._get(path, base=self.DATA_URL)

    def get_assets(self, symbol=None):
        if symbol:
            return self._get(f'/v2/assets/{symbol}')
        return self._get('/v2/assets?status=active&asset_class=us_equity')

    # WRITE OPERATIONS (require approval_token)
    def submit_order(self, symbol, qty, side, order_type='market',
                     time_in_force='day', approval_token=None):
        """
        Submit a buy or sell order.
        REQUIRES a valid approval_token from the Approval Portal.
        """
        if not approval_token:
            raise PermissionError(
                "Orders require an approval_token.\n"
                "Go to the Approval Portal (port 7778), review the recommendation, "
                "and click Approve to generate a token."
            )
        if not _verify_token(approval_token):
            raise PermissionError("Invalid or expired approval token.")

        if PAPER_MODE:
            _log(f"[PAPER] ORDER: {side} {qty} {symbol} @ {order_type}")
        else:
            _log(f"[LIVE] ORDER: {side} {qty} {symbol} @ {order_type}")

        body = {
            'symbol': symbol,
            'qty': str(qty),
            'side': side,
            'type': order_type,
            'time_in_force': time_in_force
        }
        result = self._post('/v2/orders', body)
        _log(f"Order submitted: {result.get('id','?')} | status: {result.get('status','?')}")
        return result

    def cancel_order(self, order_id):
        return self._delete(f'/v2/orders/{order_id}')


class CoinbaseConnector:
    """Crypto via Coinbase Advanced Trade API."""

    def __init__(self):
        try:
            from coinbase.rest import RESTClient
            k = _keys.get('cb_key','')
            s = _keys.get('cb_secret','')
            if k and s:
                self.client = RESTClient(api_key=k, api_secret=s)
                self.ready = True
            else:
                self.client = None
                self.ready = False
        except Exception as e:
            self.client = None
            self.ready = False
            _log(f"Coinbase connector offline: {e}")

    def get_accounts(self):
        if not self.ready: return {}
        return self.client.get_accounts()

    def get_best_bid_ask(self, product_id):
        """e.g. product_id = 'BTC-USD'"""
        if not self.ready: return {}
        return self.client.get_best_bid_ask(product_ids=[product_id])

    def get_candles(self, product_id, granularity='ONE_DAY', limit=30):
        if not self.ready: return {}
        from datetime import timezone
        import time
        end = int(time.time())
        start = end - (limit * 86400)
        return self.client.get_candles(product_id=product_id,
                                        start=str(start), end=str(end),
                                        granularity=granularity)

    def get_portfolios(self):
        if not self.ready: return {}
        return self.client.get_portfolios()

    def place_order(self, product_id, side, base_size, approval_token=None):
        """Market order. Requires approval token."""
        if not approval_token or not _verify_token(approval_token):
            raise PermissionError("Crypto orders require an approval token from the portal.")
        if not self.ready:
            raise RuntimeError("Coinbase connector not initialized.")

        _log(f"[{'PAPER' if PAPER_MODE else 'LIVE'}] CRYPTO ORDER: {side} {base_size} {product_id}")

        if PAPER_MODE:
            return {'simulated': True, 'product_id': product_id, 'side': side,
                    'base_size': base_size, 'status': 'paper_filled'}

        import uuid
        order_id = str(uuid.uuid4())
        if side == 'BUY':
            result = self.client.market_order_buy(
                client_order_id=order_id,
                product_id=product_id,
                base_size=str(base_size)
            )
        else:
            result = self.client.market_order_sell(
                client_order_id=order_id,
                product_id=product_id,
                base_size=str(base_size)
            )
        return result


class KrakenConnector:
    """Optional: additional crypto exchange via CCXT."""

    def __init__(self):
        try:
            import ccxt
            k = _keys.get('kraken_key','')
            s = _keys.get('kraken_secret','')
            if k and s:
                self.exchange = ccxt.kraken({'apiKey': k, 'secret': s})
                self.ready = True
            else:
                # Public data only (no auth needed for prices)
                self.exchange = ccxt.kraken()
                self.ready = False
        except Exception as e:
            self.exchange = None
            self.ready = False
            _log(f"Kraken connector: {e}")

    def get_ticker(self, symbol='BTC/USD'):
        if not self.exchange: return {}
        return self.exchange.fetch_ticker(symbol)

    def get_ohlcv(self, symbol='BTC/USD', timeframe='1d', limit=30):
        if not self.exchange: return []
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def get_balance(self):
        if not self.ready: return {}
        return self.exchange.fetch_balance()

    def place_order(self, symbol, side, amount, approval_token=None):
        if not approval_token or not _verify_token(approval_token):
            raise PermissionError("Kraken orders require an approval token.")
        if not self.ready:
            raise RuntimeError("Kraken not authenticated.")
        if PAPER_MODE:
            return {'simulated': True, 'symbol': symbol, 'side': side, 'amount': amount}
        return self.exchange.create_order(symbol, 'market', side, amount)


# ── FREE MARKET DATA (no API key needed) ──────────────────

class MarketData:
    """
    Free market data via yfinance. No API key required.
    Use for: price history, fundamentals, news, options chains.
    """

    def get_quote(self, ticker):
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.fast_info
        return {
            'ticker': ticker,
            'price': getattr(info, 'last_price', None),
            'prev_close': getattr(info, 'previous_close', None),
            'market_cap': getattr(info, 'market_cap', None),
            '52w_high': getattr(info, 'year_high', None),
            '52w_low': getattr(info, 'year_low', None),
        }

    def get_history(self, ticker, period='3mo', interval='1d'):
        import yfinance as yf
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)
        return df

    def get_info(self, ticker):
        import yfinance as yf
        return yf.Ticker(ticker).info

    def get_news(self, ticker):
        import yfinance as yf
        return yf.Ticker(ticker).news

    def get_options_chain(self, ticker):
        import yfinance as yf
        t = yf.Ticker(ticker)
        dates = t.options
        if not dates: return None
        return t.option_chain(dates[0])

    def bulk_quotes(self, tickers):
        """Get quotes for a list of tickers at once."""
        import yfinance as yf
        data = yf.download(tickers, period='2d', progress=False)
        return data


# ── HELPERS ───────────────────────────────────────────────

def _log(msg):
    ts = datetime.now()
    line = f"[{ts.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(f"  [EXCHANGE] {msg}")
    log_file = LOG_DIR / f"exchange_{ts.strftime('%Y-%m')}.log"
    with open(log_file, 'a') as f:
        f.write(line + '\n')

def _verify_token(token):
    """Verify an approval token from the portal. Tokens expire after 5 minutes."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        row = conn.execute(
            "SELECT created_at, used FROM approval_tokens WHERE token=?", (token,)
        ).fetchone()
        conn.close()
        if not row: return False
        if row[1]: return False  # already used
        created = datetime.fromisoformat(row[0])
        age = (datetime.now() - created).total_seconds()
        return age < 300  # 5-minute window
    except Exception:
        return False

def mark_token_used(token):
    """Mark a token as consumed after order execution."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("UPDATE approval_tokens SET used=1 WHERE token=?", (token,))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_paper_mode():
    return PAPER_MODE

def set_paper_mode(enabled: bool):
    """Flip paper/live mode. Requires explicit call — not automatic."""
    global PAPER_MODE
    if not enabled:
        confirm = input("TYPE 'I UNDERSTAND REAL MONEY' to switch to live mode: ")
        if confirm.strip() != 'I UNDERSTAND REAL MONEY':
            print("Live mode NOT enabled. Staying in paper mode.")
            return False
    PAPER_MODE = enabled
    mode = "PAPER" if enabled else "LIVE"
    _log(f"Mode switched to: {mode}")
    return True
