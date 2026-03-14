"""
INVESTMENT HQ — TRADE JOURNAL & TAX TRACKER
=============================================
Records every single trade with full audit trail.
Calculates cost basis, P&L, holding periods.
Generates IRS Form 8949 compatible exports.
Tracks wash sales (30-day rule).

Everything saved to:
  - SQLite (Gaza Rose DB) for fast queries
  - CSV files in data/trades/ for your records
  - Annual tax folders in data/tax/

Cost basis method: FIFO (First In, First Out) — most common, IRS default.
"""

import csv
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

BASE    = Path(r'C:\Users\meeko\Desktop\INVESTMENT_HQ')
DB_PATH = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\gaza_rose.db')


class TradeJournal:
    """Complete trade record with tax intelligence built in."""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute('''CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            date TEXT,
            ticker TEXT,
            asset_type TEXT,
            action TEXT,
            quantity REAL,
            price REAL,
            fees REAL DEFAULT 0,
            total_cost REAL,
            exchange TEXT,
            order_id TEXT,
            analysis_id INTEGER,
            notes TEXT,
            paper_trade INTEGER DEFAULT 0
        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS tax_lots (
            id TEXT PRIMARY KEY,
            ticker TEXT,
            asset_type TEXT,
            quantity REAL,
            cost_basis_per_unit REAL,
            date_acquired TEXT,
            date_sold TEXT,
            sale_price_per_unit REAL,
            proceeds REAL,
            cost_basis REAL,
            gain_loss REAL,
            term TEXT,
            wash_sale INTEGER DEFAULT 0,
            wash_sale_disallowed REAL DEFAULT 0
        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS positions (
            ticker TEXT PRIMARY KEY,
            asset_type TEXT,
            quantity REAL,
            avg_cost_basis REAL,
            total_invested REAL,
            first_purchase TEXT,
            last_updated TEXT
        )''')

        conn.commit()
        conn.close()

    # ── RECORD TRADES ─────────────────────────────────────

    def record_buy(self, ticker: str, quantity: float, price: float,
                   exchange: str, asset_type: str = 'stock',
                   fees: float = 0, order_id: str = '',
                   analysis_id: int = None, notes: str = '',
                   paper: bool = True) -> str:
        """
        Record a completed buy. Called after order fills.
        Returns trade ID.
        """
        trade_id   = str(uuid.uuid4())[:12]
        total_cost = (quantity * price) + fees
        now        = datetime.now()

        conn = sqlite3.connect(str(DB_PATH))

        # Insert trade record
        conn.execute(
            'INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (trade_id, now.isoformat(), now.date().isoformat(),
             ticker.upper(), asset_type, 'BUY',
             quantity, price, fees, total_cost,
             exchange, order_id, analysis_id, notes,
             1 if paper else 0)
        )

        # Create tax lot (one lot per buy)
        lot_id = str(uuid.uuid4())[:12]
        conn.execute(
            '''INSERT INTO tax_lots (id,ticker,asset_type,quantity,cost_basis_per_unit,
               date_acquired,date_sold,sale_price_per_unit,proceeds,cost_basis,gain_loss,term)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (lot_id, ticker.upper(), asset_type,
             quantity, price + (fees/quantity if quantity else 0),
             now.date().isoformat(),
             None, None, None, None, None, 'open')
        )

        # Update positions
        existing = conn.execute(
            'SELECT quantity, avg_cost_basis, total_invested FROM positions WHERE ticker=?',
            (ticker.upper(),)
        ).fetchone()

        if existing:
            old_qty, old_avg, old_total = existing
            new_qty   = old_qty + quantity
            new_total = old_total + total_cost
            new_avg   = new_total / new_qty
            conn.execute(
                'UPDATE positions SET quantity=?, avg_cost_basis=?, total_invested=?, last_updated=? WHERE ticker=?',
                (new_qty, new_avg, new_total, now.isoformat(), ticker.upper())
            )
        else:
            avg_cb = total_cost / quantity if quantity else 0
            conn.execute(
                'INSERT INTO positions VALUES (?,?,?,?,?,?,?)',
                (ticker.upper(), asset_type, quantity, avg_cb,
                 total_cost, now.date().isoformat(), now.isoformat())
            )

        conn.commit()
        conn.close()

        self._append_to_csv(trade_id, now.date().isoformat(), ticker, asset_type,
                            'BUY', quantity, price, fees, total_cost, exchange, paper, notes)
        self._log(f"BUY recorded: {quantity} {ticker} @ ${price:.4f} | Total: ${total_cost:.2f}")
        return trade_id

    def record_sell(self, ticker: str, quantity: float, price: float,
                    exchange: str, asset_type: str = 'stock',
                    fees: float = 0, order_id: str = '',
                    analysis_id: int = None, notes: str = '',
                    paper: bool = True) -> dict:
        """
        Record a completed sell. Calculates gain/loss using FIFO.
        Returns tax event summary.
        """
        trade_id = str(uuid.uuid4())[:12]
        proceeds = (quantity * price) - fees
        now      = datetime.now()

        conn = sqlite3.connect(str(DB_PATH))

        # FIFO: match against open lots
        open_lots = conn.execute(
            '''SELECT id, quantity, cost_basis_per_unit, date_acquired
               FROM tax_lots
               WHERE ticker=? AND date_sold IS NULL
               ORDER BY date_acquired ASC''',
            (ticker.upper(),)
        ).fetchall()

        remaining_to_sell = quantity
        total_cost_basis  = 0
        total_gain_loss   = 0
        closed_lots       = []

        for lot_id, lot_qty, lot_cb, date_acq in open_lots:
            if remaining_to_sell <= 0:
                break

            sold_from_lot = min(remaining_to_sell, lot_qty)
            lot_proceeds  = sold_from_lot * price
            lot_cb_total  = sold_from_lot * lot_cb
            lot_gain_loss = lot_proceeds - lot_cb_total - (fees * sold_from_lot / quantity)

            # Determine short/long term
            acq_date  = datetime.strptime(date_acq, '%Y-%m-%d')
            hold_days = (now - acq_date).days
            term      = 'LONG_TERM' if hold_days >= 366 else 'SHORT_TERM'

            # Check wash sale (if sold at a loss within 30 days of similar purchase)
            wash = self._check_wash_sale(conn, ticker, now, lot_gain_loss)

            # Close the lot
            conn.execute(
                '''UPDATE tax_lots SET date_sold=?, sale_price_per_unit=?,
                   proceeds=?, cost_basis=?, gain_loss=?, term=?,
                   wash_sale=?, wash_sale_disallowed=?
                   WHERE id=?''',
                (now.date().isoformat(), price,
                 lot_proceeds, lot_cb_total, lot_gain_loss,
                 term, 1 if wash else 0,
                 abs(lot_gain_loss) if wash and lot_gain_loss < 0 else 0,
                 lot_id)
            )

            # If partial lot, create remainder
            if sold_from_lot < lot_qty:
                remainder_id = str(uuid.uuid4())[:12]
                conn.execute(
                    '''INSERT INTO tax_lots (id,ticker,asset_type,quantity,cost_basis_per_unit,
                       date_acquired,date_sold,term)
                       VALUES (?,?,?,?,?,?,?,?)''',
                    (remainder_id, ticker.upper(), asset_type,
                     lot_qty - sold_from_lot, lot_cb,
                     date_acq, None, 'open')
                )

            total_cost_basis  += lot_cb_total
            total_gain_loss   += lot_gain_loss
            remaining_to_sell -= sold_from_lot
            closed_lots.append({
                'lot_id': lot_id,
                'qty': sold_from_lot,
                'cost_basis': lot_cb_total,
                'proceeds': lot_proceeds,
                'gain_loss': lot_gain_loss,
                'term': term,
                'wash_sale': wash
            })

        # Insert trade record
        conn.execute(
            'INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (trade_id, now.isoformat(), now.date().isoformat(),
             ticker.upper(), asset_type, 'SELL',
             quantity, price, fees, proceeds,
             exchange, order_id, analysis_id, notes,
             1 if paper else 0)
        )

        # Update position quantity
        existing = conn.execute(
            'SELECT quantity, total_invested FROM positions WHERE ticker=?',
            (ticker.upper(),)
        ).fetchone()
        if existing:
            new_qty = existing[0] - quantity
            if new_qty <= 0.0001:
                conn.execute('DELETE FROM positions WHERE ticker=?', (ticker.upper(),))
            else:
                new_total = existing[1] - total_cost_basis
                new_avg   = new_total / new_qty if new_qty > 0 else 0
                conn.execute(
                    'UPDATE positions SET quantity=?, avg_cost_basis=?, total_invested=?, last_updated=? WHERE ticker=?',
                    (new_qty, new_avg, new_total, now.isoformat(), ticker.upper())
                )

        conn.commit()
        conn.close()

        tax_event = {
            'trade_id': trade_id,
            'ticker': ticker,
            'quantity': quantity,
            'proceeds': proceeds,
            'total_cost_basis': total_cost_basis,
            'total_gain_loss': total_gain_loss,
            'net_gain_loss': total_gain_loss,
            'lots_closed': closed_lots
        }

        self._append_to_csv(trade_id, now.date().isoformat(), ticker, asset_type,
                            'SELL', quantity, price, fees, proceeds, exchange, paper,
                            f"G/L: ${total_gain_loss:.2f}")
        gl_str = f"+${total_gain_loss:.2f}" if total_gain_loss >= 0 else f"-${abs(total_gain_loss):.2f}"
        self._log(f"SELL recorded: {quantity} {ticker} @ ${price:.4f} | G/L: {gl_str}")
        return tax_event

    def _check_wash_sale(self, conn, ticker, sell_date, gain_loss) -> bool:
        """IRS wash sale rule: can't claim a loss if you buy same asset 30 days before/after."""
        if gain_loss >= 0:
            return False
        window_start = (sell_date - timedelta(days=30)).date().isoformat()
        window_end   = (sell_date + timedelta(days=30)).date().isoformat()
        recent_buy = conn.execute(
            '''SELECT id FROM trades WHERE ticker=? AND action='BUY'
               AND date BETWEEN ? AND ? LIMIT 1''',
            (ticker.upper(), window_start, window_end)
        ).fetchone()
        return recent_buy is not None

    # ── REPORTING ─────────────────────────────────────────

    def get_positions(self) -> list:
        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute('SELECT * FROM positions ORDER BY ticker').fetchall()
        conn.close()
        cols = ['ticker','asset_type','quantity','avg_cost_basis','total_invested',
                'first_purchase','last_updated']
        return [dict(zip(cols, r)) for r in rows]

    def get_pnl_summary(self) -> dict:
        """Total realized and unrealized P&L."""
        conn = sqlite3.connect(str(DB_PATH))
        # Realized
        rows = conn.execute(
            '''SELECT term,
                      SUM(CASE WHEN gain_loss > 0 THEN gain_loss ELSE 0 END) as gains,
                      SUM(CASE WHEN gain_loss < 0 THEN gain_loss ELSE 0 END) as losses,
                      COUNT(*) as count
               FROM tax_lots WHERE date_sold IS NOT NULL
               GROUP BY term'''
        ).fetchall()
        conn.close()

        summary = {}
        for row in rows:
            term, gains, losses, count = row
            summary[term] = {
                'gains': round(gains or 0, 2),
                'losses': round(losses or 0, 2),
                'net': round((gains or 0) + (losses or 0), 2),
                'trade_count': count
            }
        return summary

    def generate_form_8949(self, year: int = None) -> Path:
        """
        Generate an IRS Form 8949 compatible CSV.
        Columns match exactly what TurboTax/TaxAct expect.
        """
        year = year or datetime.now().year
        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute(
            '''SELECT ticker, date_acquired, date_sold, proceeds, cost_basis,
                      gain_loss, term, wash_sale, wash_sale_disallowed
               FROM tax_lots
               WHERE date_sold IS NOT NULL
               AND strftime('%Y', date_sold) = ?
               ORDER BY term DESC, date_sold ASC''',
            (str(year),)
        ).fetchall()
        conn.close()

        out_dir = BASE / 'data' / 'tax' / str(year)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f'form_8949_{year}.csv'

        with open(out_file, 'w', newline='') as f:
            writer = csv.writer(f)
            # IRS Form 8949 headers
            writer.writerow([
                'Description of Property',
                'Date Acquired',
                'Date Sold or Disposed',
                'Proceeds (Sales Price)',
                'Cost or Other Basis',
                'Adjustment Code',
                'Amount of Adjustment',
                'Gain or (Loss)',
                'Term (Short/Long)'
            ])
            for row in rows:
                ticker, acq, sold, proceeds, basis, gl, term, wash, wash_disallowed = row
                adj_code = 'W' if wash else ''
                writer.writerow([
                    ticker,
                    acq,
                    sold,
                    round(proceeds or 0, 2),
                    round(basis or 0, 2),
                    adj_code,
                    round(wash_disallowed or 0, 2),
                    round(gl or 0, 2),
                    'Short-Term' if term == 'SHORT_TERM' else 'Long-Term'
                ])

        self._log(f"Form 8949 ({year}) saved: {out_file}")
        return out_file

    def generate_annual_summary(self, year: int = None) -> dict:
        """Full year tax summary — what you owe estimate."""
        year = year or datetime.now().year
        pnl  = self.get_pnl_summary()

        st_net = pnl.get('SHORT_TERM', {}).get('net', 0)
        lt_net = pnl.get('LONG_TERM', {}).get('net', 0)

        # Rough tax estimates (consult a CPA for actual filing)
        # Short-term gains taxed as ordinary income (~22-37% bracket)
        # Long-term gains taxed at preferential rates (0/15/20%)
        st_tax_est = max(0, st_net * 0.24)  # conservative 24%
        lt_tax_est = max(0, lt_net * 0.15)  # standard 15%

        summary = {
            'year': year,
            'short_term_net': round(st_net, 2),
            'long_term_net': round(lt_net, 2),
            'total_net': round(st_net + lt_net, 2),
            'estimated_tax_short_term': round(st_tax_est, 2),
            'estimated_tax_long_term': round(lt_tax_est, 2),
            'estimated_total_tax': round(st_tax_est + lt_tax_est, 2),
            'note': 'ESTIMATES ONLY. Consult a CPA for actual tax filing.',
            'form_8949': str(self.generate_form_8949(year))
        }

        # Save JSON summary
        out_dir = BASE / 'data' / 'tax' / str(year)
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / f'tax_summary_{year}.json', 'w') as f:
            json.dump(summary, f, indent=2)

        self._log(f"Tax summary {year}: Net {summary['total_net']} | Est. tax: ${summary['estimated_total_tax']}")
        return summary

    def get_trade_history(self, ticker: str = None, year: int = None, limit: int = 100) -> list:
        conn = sqlite3.connect(str(DB_PATH))
        if ticker:
            rows = conn.execute(
                'SELECT * FROM trades WHERE ticker=? ORDER BY timestamp DESC LIMIT ?',
                (ticker.upper(), limit)
            ).fetchall()
        elif year:
            rows = conn.execute(
                "SELECT * FROM trades WHERE strftime('%Y',date)=? ORDER BY timestamp DESC LIMIT ?",
                (str(year), limit)
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?', (limit,)
            ).fetchall()
        conn.close()
        cols = ['id','timestamp','date','ticker','asset_type','action','quantity',
                'price','fees','total_cost','exchange','order_id','analysis_id',
                'notes','paper_trade']
        return [dict(zip(cols, r)) for r in rows]

    # ── CSV APPEND ────────────────────────────────────────

    def _append_to_csv(self, trade_id, date, ticker, asset_type, action,
                        qty, price, fees, total, exchange, paper, notes):
        year     = datetime.now().year
        csv_dir  = BASE / 'data' / 'trades'
        csv_path = csv_dir / f'trades_{year}.csv'
        write_header = not csv_path.exists()
        with open(csv_path, 'a', newline='') as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(['Trade ID','Date','Ticker','Asset Type','Action',
                            'Quantity','Price','Fees','Total','Exchange','Paper','Notes'])
            w.writerow([trade_id, date, ticker, asset_type, action,
                        qty, price, fees, total, exchange,
                        'YES' if paper else 'LIVE', notes])

    def _log(self, msg):
        ts  = datetime.now().strftime('%H:%M:%S')
        out = f"  [JOURNAL {ts}] {msg}"
        print(out)
        log_path = BASE / 'logs' / f"journal_{datetime.now().strftime('%Y-%m')}.log"
        with open(log_path, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
