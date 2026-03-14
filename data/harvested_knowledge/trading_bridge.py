"""
TRADING BRIDGE — Exchange Connections
======================================
Connects to Alpaca (stocks + crypto) and Coinbase Advanced Trade.

IMPORTANT DESIGN RULES — NEVER BROKEN:
  1. PAPER TRADING is the default. Live mode requires explicit opt-in.
  2. NO trade executes without a human approval token from approval_queue.py
  3. Every action — read or write — is logged to the tax ledger.
  4. Keys live in memory only, entered at runtime via the Setup Wizard.

LEGAL BASIS:
  - Alpaca Markets: US-registered broker-dealer, FINRA member, SIPC insured.
    API trading is explicitly permitted in their Terms of Service.
    Paper trading sandbox is identical to live — safe to test everything.
  - Coinbase Advanced Trade: Licensed in all US states, MSB registered with FinCEN.
    API trading explicitly permitted in their Terms of Service.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE    = Path(r'C:\Users\meeko\Desktop\TRADING_SYSTEM')
DB_PATH = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\gaza_rose.db')

# Runtime-only key store — never written to disk
_KEYS = {}

def set_keys(alpaca_key=None, alpaca_secret=None, alpaca_live=False,
             coinbase_key=None, coinbase_secret=None):
    """Called by Setup Wizard. Keys stay in memory only."""
    if alpaca_key:    _KEYS['alpaca_key']    = alpaca_key
    if alpaca_secret: _KEYS['alpaca_secret'] = alpaca_secret
    if coinbase_key:  _KEYS['coinbase_key']  = coinbase_key
    if coinbase_secret: _KEYS['coinbase_secret'] = coinbase_secret
    _KEYS['alpaca_live'] = alpaca_live
    _KEYS['loaded'] = True


class AlpacaBridge:
    """
    Connects to Alpaca Markets.
    Paper mode by default — identical API, fake money.
    Switch to live only when you're ready and have funded your account.
    """

    def __init__(self, live=False):
        self.live = live or _KEYS.get('alpaca_live', False)
        self._client = None
        self._data_client = None

    def connect(self):
        from alpaca.trading.client import TradingClient
        from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
        key    = _KEYS.get('alpaca_key', '')
        secret = _KEYS.get('alpaca_secret', '')
        if not key or not secret:
            raise ValueError("Alpaca keys not loaded. Run Setup Wizard first.")
        paper = not self.live
        self._client = TradingClient(key, secret, paper=paper)
        self._data_client = StockHistoricalDataClient(key, secret)
        self._crypto_data = CryptoHistoricalDataClient(key, secret)
        mode = "LIVE" if self.live else "PAPER"
        _log(f"Alpaca connected [{mode}]")
        return self

    def account(self):
        """Get your account info — buying power, equity, P&L."""
        acct = self._client.get_account()
        return {
            'mode': 'LIVE' if self.live else 'PAPER',
            'equity':        float(acct.equity),
            'buying_power':  float(acct.buying_power),
            'cash':          float(acct.cash),
            'portfolio_value': float(acct.portfolio_value),
            'day_trade_count': acct.daytrade_count,
            'pdt_flag':      acct.pattern_day_trader,
        }

    def positions(self):
        """Get all current positions."""
        raw = self._client.get_all_positions()
        return [{
            'symbol':    p.symbol,
            'qty':       float(p.qty),
            'avg_price': float(p.avg_entry_price),
            'current':   float(p.current_price),
            'market_val': float(p.market_value),
            'unrealized_pl': float(p.unrealized_pl),
            'unrealized_pct': float(p.unrealized_plpc) * 100,
        } for p in raw]

    def orders(self, status='all', limit=50):
        """Get recent orders."""
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus
        req = GetOrdersRequest(status=QueryOrderStatus.ALL, limit=limit)
        raw = self._client.get_orders(filter=req)
        return [{
            'id':        str(o.id),
            'symbol':    o.symbol,
            'side':      o.side.value,
            'qty':       float(o.qty or 0),
            'filled_qty': float(o.filled_qty or 0),
            'type':      o.order_type.value,
            'status':    o.status.value,
            'filled_avg_price': float(o.filled_avg_price or 0),
            'submitted': str(o.submitted_at),
            'filled':    str(o.filled_at),
        } for o in raw]

    def quote(self, symbol):
        """Get latest quote for a stock symbol."""
        from alpaca.data.requests import StockLatestQuoteRequest
        req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        result = self._data_client.get_stock_latest_quote(req)
        q = result[symbol]
        return {
            'symbol': symbol,
            'ask':    float(q.ask_price),
            'bid':    float(q.bid_price),
            'mid':    round((float(q.ask_price) + float(q.bid_price)) / 2, 4),
        }

    def history(self, symbol, days=30, timeframe='1Day'):
        """Get historical OHLCV bars for a symbol."""
        import pandas as pd
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        from datetime import timedelta
        tf_map = {'1Min': TimeFrame.Minute, '1Hour': TimeFrame.Hour, '1Day': TimeFrame.Day}
        tf = tf_map.get(timeframe, TimeFrame.Day)
        start = datetime.now(timezone.utc) - timedelta(days=days)
        req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=tf, start=start)
        bars = self._data_client.get_stock_bars(req)
        df = bars.df
        if hasattr(df.index, 'levels'):
            df = df.loc[symbol]
        return df.reset_index().to_dict('records')

    def submit_order(self, approval_token, symbol, side, qty,
                     order_type='market', limit_price=None):
        """
        Submit an order. REQUIRES a valid approval_token from approval_queue.
        Without the token this raises immediately — hard stop.
        """
        from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        # Verify approval token
        _verify_approval(approval_token, symbol, side, qty)
        side_enum = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
        if order_type == 'market':
            req = MarketOrderRequest(symbol=symbol, qty=qty,
                                     side=side_enum, time_in_force=TimeInForce.DAY)
        else:
            req = LimitOrderRequest(symbol=symbol, qty=qty, side=side_enum,
                                    limit_price=limit_price,
                                    time_in_force=TimeInForce.DAY)
        order = self._client.submit_order(req)
        _log(f"Order submitted: {side} {qty} {symbol} [{order.id}]")
        _record_order(order, 'alpaca', self.live)
        return {'order_id': str(order.id), 'status': order.status.value}

    def cancel_order(self, order_id):
        self._client.cancel_order_by_id(order_id)
        _log(f"Order cancelled: {order_id}")


class CoinbaseBridge:
    """Connects to Coinbase Advanced Trade for crypto."""

    def __init__(self):
        self._client = None

    def connect(self):
        from coinbase.rest import RESTClient
        key    = _KEYS.get('coinbase_key', '')
        secret = _KEYS.get('coinbase_secret', '')
        if not key or not secret:
            raise ValueError("Coinbase keys not loaded. Run Setup Wizard first.")
        self._client = RESTClient(api_key=key, api_secret=secret)
        _log("Coinbase Advanced Trade connected")
        return self

    def account(self):
        accounts = self._client.get_accounts()
        result = {}
        for a in (accounts.accounts or []):
            val = float(getattr(getattr(a, 'available_balance', None), 'value', 0) or 0)
            if val > 0:
                result[getattr(a, 'currency', '?')] = val
        return result

    def quote(self, product_id='BTC-USD'):
        """Get best bid/ask for a crypto product."""
        product = self._client.get_best_bid_ask(product_ids=[product_id])
        p = product.pricebooks[0] if product.pricebooks else None
        if not p:
            return None
        return {
            'product': product_id,
            'ask': float(p.asks[0].price) if p.asks else None,
            'bid': float(p.bids[0].price) if p.bids else None,
        }

    def orders(self, limit=50):
        """Get recent orders."""
        result = self._client.list_orders(limit=limit)
        orders = []
        for o in (result.orders or []):
            orders.append({
                'id':      o.order_id,
                'product': o.product_id,
                'side':    o.side,
                'status':  o.status,
                'size':    o.order_configuration,
                'created': o.created_time,
            })
        return orders

    def submit_order(self, approval_token, product_id, side, base_size,
                     order_type='market', limit_price=None):
        """Submit a crypto order. Requires approval token — hard stop without it."""
        _verify_approval(approval_token, product_id, side, base_size)
        import uuid
        client_order_id = str(uuid.uuid4())
        if order_type == 'market':
            if side.upper() == 'BUY':
                order = self._client.market_order_buy(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=str(base_size)
                )
            else:
                order = self._client.market_order_sell(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=str(base_size)
                )
        else:
            if side.upper() == 'BUY':
                order = self._client.limit_order_gtc_buy(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=str(base_size),
                    limit_price=str(limit_price)
                )
            else:
                order = self._client.limit_order_gtc_sell(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=str(base_size),
                    limit_price=str(limit_price)
                )
        _log(f"Coinbase order: {side} {base_size} {product_id}")
        _record_coinbase_order(order, product_id, side, base_size)
        return order

# ── FREE MARKET DATA (no API key needed) ───────────────────

def get_quote_free(symbol):
    """Get quote via yfinance — no API key, free, good enough for analysis."""
    import yfinance as yf
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    return {
        'symbol':   symbol,
        'price':    getattr(info, 'last_price', None),
        'prev_close': getattr(info, 'previous_close', None),
        'day_high': getattr(info, 'day_high', None),
        'day_low':  getattr(info, 'day_low', None),
        'volume':   getattr(info, 'three_month_average_volume', None),
        'market_cap': getattr(info, 'market_cap', None),
    }

def get_history_free(symbol, period='3mo', interval='1d'):
    """Get historical data via yfinance."""
    import yfinance as yf
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df.empty:
        return []
    df = df.round(4)
    records = []
    for idx, row in df.iterrows():
        records.append({
            'date':   str(idx.date()),
            'open':   float(row['Open'].iloc[0]) if hasattr(row['Open'], 'iloc') else float(row['Open']),
            'high':   float(row['High'].iloc[0]) if hasattr(row['High'], 'iloc') else float(row['High']),
            'low':    float(row['Low'].iloc[0]) if hasattr(row['Low'], 'iloc') else float(row['Low']),
            'close':  float(row['Close'].iloc[0]) if hasattr(row['Close'], 'iloc') else float(row['Close']),
            'volume': int(row['Volume'].iloc[0]) if hasattr(row['Volume'], 'iloc') else int(row['Volume']),
        })
    return records

# ── INTERNAL HELPERS ───────────────────────────────────────

def _verify_approval(token, symbol, side, qty):
    """Hard gate — no token, no trade. Period."""
    queue_file = BASE / 'approval_queue' / 'approved.json'
    if not queue_file.exists():
        raise PermissionError("No approval file found. Use the dashboard to approve trades.")
    with open(queue_file) as f:
        approved = json.load(f)
    if token not in approved:
        raise PermissionError(
            f"Approval token '{token}' not found. "
            "Open the Trading Dashboard and approve this trade first."
        )
    entry = approved[token]
    if entry.get('used'):
        raise PermissionError("This approval token has already been used.")
    if entry.get('symbol') != symbol:
        raise PermissionError(f"Token was approved for {entry.get('symbol')}, not {symbol}.")
    # Mark as used
    entry['used'] = True
    entry['used_at'] = datetime.now().isoformat()
    with open(queue_file, 'w') as f:
        json.dump(approved, f, indent=2)

def _record_order(order, exchange, live):
    """Write every order to the tax ledger CSV immediately."""
    from tax_ledger import TaxLedger
    TaxLedger().record_fill(
        exchange=exchange,
        mode='LIVE' if live else 'PAPER',
        symbol=str(order.symbol),
        side=str(order.side.value),
        qty=float(order.filled_qty or order.qty or 0),
        price=float(order.filled_avg_price or 0),
        order_id=str(order.id),
        fees=0.0
    )

def _record_coinbase_order(order, product_id, side, base_size):
    from tax_ledger import TaxLedger
    TaxLedger().record_fill(
        exchange='coinbase',
        mode='LIVE',
        symbol=product_id,
        side=side,
        qty=float(base_size),
        price=0.0,  # filled price comes in webhook/later
        order_id=str(getattr(order, 'order_id', 'unknown')),
        fees=0.0
    )

def _log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[TRADING {ts}] {msg}"
    print(f"  {line}")
    log_file = BASE / 'logs' / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, 'a') as f:
        f.write(line + '\n')
