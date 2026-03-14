"""
TAX LEDGER — IRS-Compliant Trade Record Keeping
=================================================
Every single trade — stocks and crypto — is logged here.
Generates Form 8949-compatible data for your accountant.
Tracks cost basis using FIFO (IRS default method).

FILES GENERATED:
  data/trades/trades_YYYY.csv        — raw trade log, one row per fill
  data/tax_reports/tax_YYYY.json     — annual P&L summary
  data/tax_reports/form_8949_YYYY.csv — ready for your tax preparer

DISCLAIMER: This is a record-keeping tool. Consult a tax professional
for advice. Crypto is taxed as property (IRS Notice 2014-21). Stocks
follow standard brokerage rules. Short-term (<1yr) vs long-term (>1yr)
holding periods determine your capital gains rate.
"""

import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(r'C:\Users\meeko\Desktop\TRADING_SYSTEM')

# CSV columns — matches Form 8949 fields where possible
TRADE_COLUMNS = [
    'date_time',        # ISO 8601
    'exchange',         # alpaca / coinbase
    'mode',             # LIVE / PAPER
    'symbol',           # BTC-USD / AAPL etc
    'asset_type',       # stock / crypto
    'side',             # BUY / SELL
    'quantity',         # decimal
    'price',            # per unit USD
    'total_value',      # quantity * price
    'fees',             # USD
    'net_proceeds',     # total_value - fees (for sells)
    'cost_basis',       # from FIFO lot matching
    'gain_loss',        # net_proceeds - cost_basis (sells only)
    'holding_days',     # days held (for short/long term classification)
    'term',             # SHORT / LONG / N/A
    'order_id',
    'notes',
]


class TaxLedger:
    def __init__(self):
        self.year = datetime.now().year
        self.trades_dir = BASE / 'data' / 'trades'
        self.tax_dir    = BASE / 'data' / 'tax_reports'
        self.trades_dir.mkdir(parents=True, exist_ok=True)
        self.tax_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.trades_dir / f'trades_{self.year}.csv'
        self._ensure_csv()
        # In-memory FIFO lot tracker: symbol -> list of (date, qty, price)
        self._lots = defaultdict(list)
        self._load_lots()

    # ── RECORD A FILL ──────────────────────────────────────

    def record_fill(self, exchange, mode, symbol, side, qty,
                    price, order_id, fees=0.0, notes=''):
        """
        Write one trade to the ledger. Called automatically by trading_bridge.
        For PAPER trades, writes with mode=PAPER — excluded from tax calcs.
        """
        now = datetime.now(timezone.utc).isoformat()
        total = round(qty * price, 6) if price else 0
        asset_type = 'crypto' if '-' in symbol else 'stock'

        cost_basis  = 0.0
        gain_loss   = 0.0
        hold_days   = 0
        term        = 'N/A'
        net_proceeds = 0.0

        if side.upper() == 'BUY' and mode == 'LIVE':
            self._lots[symbol].append({
                'date': now,
                'qty':  qty,
                'price': price,
                'remaining': qty
            })

        elif side.upper() == 'SELL' and mode == 'LIVE':
            net_proceeds = round(total - fees, 6)
            cost_basis, hold_days = self._fifo_cost(symbol, qty, now)
            gain_loss = round(net_proceeds - cost_basis, 6)
            term = 'LONG' if hold_days >= 365 else 'SHORT'

        row = {
            'date_time':    now,
            'exchange':     exchange,
            'mode':         mode,
            'symbol':       symbol,
            'asset_type':   asset_type,
            'side':         side.upper(),
            'quantity':     qty,
            'price':        price,
            'total_value':  total,
            'fees':         fees,
            'net_proceeds': net_proceeds,
            'cost_basis':   cost_basis,
            'gain_loss':    gain_loss,
            'holding_days': hold_days,
            'term':         term,
            'order_id':     order_id,
            'notes':        notes,
        }

        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=TRADE_COLUMNS)
            writer.writerow(row)

        self._save_lots()
        self._update_snapshot(row)
        return row

    # ── TAX REPORTS ────────────────────────────────────────

    def annual_summary(self, year=None):
        """
        Generate annual P&L summary.
        Returns dict with totals for short-term and long-term gains/losses.
        """
        year = year or self.year
        csv_path = self.trades_dir / f'trades_{year}.csv'
        if not csv_path.exists():
            return {'year': year, 'trades': 0, 'note': 'No trades found for this year'}

        short_gain = 0.0
        long_gain  = 0.0
        total_fees = 0.0
        trades     = 0
        sells      = []

        with open(csv_path, newline='') as f:
            for row in csv.DictReader(f):
                if row['mode'] == 'PAPER':
                    continue
                trades += 1
                total_fees += float(row['fees'] or 0)
                if row['side'] == 'SELL' and row['gain_loss']:
                    gl = float(row['gain_loss'])
                    if row['term'] == 'LONG':
                        long_gain += gl
                    else:
                        short_gain += gl
                    sells.append({
                        'date':        row['date_time'][:10],
                        'symbol':      row['symbol'],
                        'qty':         row['quantity'],
                        'proceeds':    row['net_proceeds'],
                        'cost_basis':  row['cost_basis'],
                        'gain_loss':   row['gain_loss'],
                        'term':        row['term'],
                    })

        summary = {
            'year':              year,
            'total_trades':      trades,
            'total_fees_usd':    round(total_fees, 2),
            'short_term_gain':   round(short_gain, 2),
            'long_term_gain':    round(long_gain, 2),
            'total_gain':        round(short_gain + long_gain, 2),
            'sells':             sells,
            'generated':         datetime.now().isoformat(),
            'disclaimer':        'Consult a tax professional. FIFO cost basis. Crypto taxed as property per IRS Notice 2014-21.',
        }

        out = self.tax_dir / f'tax_{year}.json'
        with open(out, 'w') as f:
            json.dump(summary, f, indent=2)
        return summary

    def form_8949_csv(self, year=None):
        """
        Generate a Form 8949-compatible CSV.
        Column names match what TurboTax and most tax software expects.
        """
        year = year or self.year
        summary = self.annual_summary(year)
        out = self.tax_dir / f'form_8949_{year}.csv'
        fields_8949 = [
            'Description of property',
            'Date acquired',
            'Date sold or disposed',
            'Proceeds (sales price)',
            'Cost or other basis',
            'Gain or (loss)',
            'Short or Long term',
        ]
        with open(out, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields_8949)
            writer.writeheader()
            for sell in summary.get('sells', []):
                writer.writerow({
                    'Description of property': f"{sell['qty']} {sell['symbol']}",
                    'Date acquired':   'VARIOUS',
                    'Date sold or disposed': sell['date'],
                    'Proceeds (sales price)': sell['proceeds'],
                    'Cost or other basis':    sell['cost_basis'],
                    'Gain or (loss)':         sell['gain_loss'],
                    'Short or Long term':     sell['term'],
                })
        return str(out)

    def all_trades_df(self, year=None, paper=False):
        """Return all trades as a list of dicts. Set paper=True to include paper trades."""
        year = year or self.year
        csv_path = self.trades_dir / f'trades_{year}.csv'
        if not csv_path.exists():
            return []
        rows = []
        with open(csv_path, newline='') as f:
            for row in csv.DictReader(f):
                if not paper and row['mode'] == 'PAPER':
                    continue
                rows.append(row)
        return rows

    # ── FIFO COST BASIS ────────────────────────────────────

    def _fifo_cost(self, symbol, qty_sold, sell_date):
        """Calculate cost basis using FIFO — IRS default method."""
        lots = self._lots.get(symbol, [])
        remaining = float(qty_sold)
        total_cost = 0.0
        buy_dates  = []

        for lot in lots:
            if remaining <= 0:
                break
            available = float(lot.get('remaining', 0))
            if available <= 0:
                continue
            used = min(remaining, available)
            total_cost += used * float(lot['price'])
            buy_dates.append(lot['date'][:10])
            lot['remaining'] = available - used
            remaining -= used

        # Calculate average holding days
        hold_days = 0
        if buy_dates:
            try:
                oldest = datetime.fromisoformat(buy_dates[0])
                sell   = datetime.fromisoformat(sell_date[:10])
                hold_days = (sell - oldest).days
            except Exception:
                hold_days = 0

        return round(total_cost, 6), hold_days

    # ── PERSISTENCE ────────────────────────────────────────

    def _ensure_csv(self):
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                csv.DictWriter(f, fieldnames=TRADE_COLUMNS).writeheader()

    def _load_lots(self):
        lots_file = BASE / 'data' / 'lots.json'
        if lots_file.exists():
            with open(lots_file) as f:
                data = json.load(f)
                for symbol, lots in data.items():
                    self._lots[symbol] = lots

    def _save_lots(self):
        lots_file = BASE / 'data' / 'lots.json'
        with open(lots_file, 'w') as f:
            json.dump(dict(self._lots), f, indent=2)

    def _update_snapshot(self, row):
        snap_file = BASE / 'data' / 'latest_snapshot.json'
        try:
            if snap_file.exists():
                with open(snap_file) as f:
                    snap = json.load(f)
            else:
                snap = {'trades': [], 'last_updated': ''}
            snap['trades'].insert(0, row)
            snap['trades'] = snap['trades'][:100]  # keep last 100
            snap['last_updated'] = datetime.now().isoformat()
            with open(snap_file, 'w') as f:
                json.dump(snap, f, indent=2, default=str)
        except Exception:
            pass


if __name__ == '__main__':
    ledger = TaxLedger()
    print("\n=== TAX LEDGER STATUS ===")
    summary = ledger.annual_summary()
    print(json.dumps(summary, indent=2))
    f8949 = ledger.form_8949_csv()
    print(f"\nForm 8949 CSV: {f8949}")
