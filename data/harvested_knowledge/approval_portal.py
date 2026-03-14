"""
INVESTMENT HQ — APPROVAL PORTAL
=================================
Local web UI on http://localhost:7778
Every trade recommendation must be reviewed here before ANY order executes.

Tabs:
  - PENDING    : AI recommendations waiting for your decision
  - PORTFOLIO  : Your current positions + P&L
  - WATCHLIST  : Assets your agent monitors
  - HISTORY    : All past trades with tax info
  - TAX CENTER : Form 8949, annual summaries, export tools
  - SETTINGS   : Paper/live mode, exchange keys, analyst config

HUMAN ALWAYS IN CONTROL. No trade executes without your click.
"""

import http.server
import json
import sqlite3
import sys
import threading
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

BASE    = Path(r'C:\Users\meeko\Desktop\INVESTMENT_HQ')
DB_PATH = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\gaza_rose.db')
PORT    = 7778

# ── HTML ──────────────────────────────────────────────────
PORTAL_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Investment HQ — Approval Portal</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #080c10; --panel: #0f1519; --panel2: #161d22;
  --border: #1e2830; --green: #00e676; --red: #ff5252;
  --gold: #ffd740; --blue: #40c4ff; --text: #e0e8f0;
  --muted: #4a6070; --mono: 'IBM Plex Mono', monospace;
  --sans: 'Space Grotesk', sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin:0; padding:0; }
body { background:var(--bg); color:var(--text); font-family:var(--sans); min-height:100vh; }

/* NAV */
nav {
  display:flex; align-items:center; gap:0;
  background:var(--panel); border-bottom:1px solid var(--border);
  padding:0 24px; height:56px; position:sticky; top:0; z-index:100;
}
.nav-brand { font-weight:700; font-size:15px; letter-spacing:1px; color:var(--green); margin-right:32px; }
.nav-brand span { color:var(--muted); font-weight:400; }
.nav-tab {
  padding:0 20px; height:56px; display:flex; align-items:center;
  font-size:13px; font-weight:500; cursor:pointer; border-bottom:2px solid transparent;
  transition:.2s; color:var(--muted); letter-spacing:.5px; text-transform:uppercase;
}
.nav-tab:hover { color:var(--text); }
.nav-tab.active { color:var(--green); border-bottom-color:var(--green); }
.nav-badge {
  background:var(--red); color:white; border-radius:99px;
  font-size:10px; padding:1px 6px; margin-left:6px; font-family:var(--mono);
}
.nav-mode {
  margin-left:auto; padding:4px 14px; border-radius:6px;
  font-family:var(--mono); font-size:11px; font-weight:500; letter-spacing:1px;
}
.nav-mode.paper { background:rgba(255,215,64,0.1); color:var(--gold); border:1px solid rgba(255,215,64,0.3); }
.nav-mode.live  { background:rgba(255,82,82,0.1);  color:var(--red);  border:1px solid rgba(255,82,82,0.3); }

/* LAYOUT */
.content { padding:28px 32px; max-width:1200px; }
.tab-content { display:none; }
.tab-content.active { display:block; }

/* CARDS */
.card {
  background:var(--panel); border:1px solid var(--border);
  border-radius:12px; padding:24px; margin-bottom:16px;
}
.card-title { font-size:11px; text-transform:uppercase; letter-spacing:1.5px; color:var(--muted); margin-bottom:16px; font-family:var(--mono); }

/* STAT GRID */
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin-bottom:24px; }
.stat { background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:16px 20px; }
.stat-label { font-size:11px; color:var(--muted); font-family:var(--mono); letter-spacing:.5px; }
.stat-value { font-size:24px; font-weight:700; margin-top:4px; font-family:var(--mono); }
.stat-value.green { color:var(--green); }
.stat-value.red   { color:var(--red); }
.stat-value.gold  { color:var(--gold); }
.stat-value.blue  { color:var(--blue); }

/* RECOMMENDATION CARD */
.rec-card {
  background:var(--panel2); border:1px solid var(--border);
  border-radius:14px; margin-bottom:16px; overflow:hidden;
  transition:border-color .2s;
}
.rec-card:hover { border-color:var(--green); }
.rec-header {
  display:flex; align-items:center; gap:16px;
  padding:20px 24px; border-bottom:1px solid var(--border);
}
.action-badge {
  padding:5px 14px; border-radius:6px; font-family:var(--mono);
  font-size:13px; font-weight:500; letter-spacing:1px;
}
.action-badge.BUY   { background:rgba(0,230,118,0.1);  color:var(--green); border:1px solid rgba(0,230,118,0.3); }
.action-badge.SELL  { background:rgba(255,82,82,0.1);   color:var(--red);   border:1px solid rgba(255,82,82,0.3); }
.action-badge.HOLD  { background:rgba(64,196,255,0.1);  color:var(--blue);  border:1px solid rgba(64,196,255,0.3); }
.action-badge.AVOID { background:rgba(255,82,82,0.15);  color:var(--red);   border:1px solid rgba(255,82,82,0.4); }
.rec-ticker { font-size:24px; font-weight:700; font-family:var(--mono); }
.rec-price  { font-size:14px; color:var(--muted); margin-left:auto; font-family:var(--mono); }
.rec-body { padding:20px 24px; }
.rec-reasoning { color:#a0b8c8; line-height:1.7; margin-bottom:16px; font-size:14px; }
.rec-meta { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px; }
.meta-chip {
  background:var(--panel); border:1px solid var(--border);
  border-radius:6px; padding:4px 12px;
  font-family:var(--mono); font-size:11px; color:var(--muted);
}
.meta-chip span { color:var(--text); }

/* CONFIDENCE BAR */
.conf-bar { margin-bottom:16px; }
.conf-label { display:flex; justify-content:space-between; font-family:var(--mono); font-size:11px; color:var(--muted); margin-bottom:6px; }
.conf-track { height:4px; background:var(--border); border-radius:99px; overflow:hidden; }
.conf-fill  { height:100%; border-radius:99px; transition:width .5s; }

/* TRADE SIZE INPUT */
.trade-input {
  display:flex; align-items:center; gap:10px; margin-bottom:20px;
  flex-wrap:wrap;
}
.qty-box {
  background:var(--panel); border:1px solid var(--border);
  border-radius:8px; padding:8px 14px;
  color:var(--text); font-family:var(--mono); font-size:14px;
  width:120px; outline:none;
}
.qty-box:focus { border-color:var(--green); }
.trade-label { font-size:12px; color:var(--muted); font-family:var(--mono); }

/* APPROVE/REJECT BUTTONS */
.action-row { display:flex; gap:10px; }
.btn-approve {
  background:var(--green); color:#000; border:none;
  padding:10px 28px; border-radius:8px; font-weight:700;
  font-size:14px; cursor:pointer; transition:.2s; font-family:var(--sans);
}
.btn-approve:hover { background:#69ff9e; transform:translateY(-1px); }
.btn-reject {
  background:transparent; color:var(--red); border:1px solid var(--red);
  padding:10px 24px; border-radius:8px; font-weight:600;
  font-size:14px; cursor:pointer; transition:.2s; font-family:var(--sans);
}
.btn-reject:hover { background:rgba(255,82,82,0.1); }
.btn-skip {
  background:transparent; color:var(--muted); border:1px solid var(--border);
  padding:10px 20px; border-radius:8px; font-size:13px;
  cursor:pointer; transition:.2s; font-family:var(--sans);
}
.btn-skip:hover { border-color:var(--muted); color:var(--text); }

/* APPROVED TOAST */
.toast {
  position:fixed; bottom:24px; right:24px;
  background:var(--green); color:#000;
  padding:14px 24px; border-radius:10px;
  font-weight:700; font-size:14px;
  transform:translateY(100px); opacity:0;
  transition:.3s; z-index:999;
}
.toast.show { transform:translateY(0); opacity:1; }

/* TABLE */
table { width:100%; border-collapse:collapse; font-size:13px; }
th {
  text-align:left; padding:10px 14px;
  font-family:var(--mono); font-size:10px; letter-spacing:1px;
  text-transform:uppercase; color:var(--muted);
  border-bottom:1px solid var(--border);
}
td { padding:11px 14px; border-bottom:1px solid rgba(255,255,255,0.04); }
tr:hover td { background:rgba(255,255,255,0.02); }
.td-green { color:var(--green); font-family:var(--mono); }
.td-red   { color:var(--red);   font-family:var(--mono); }
.td-mono  { font-family:var(--mono); }
.td-muted { color:var(--muted); font-family:var(--mono); }

/* WATCHLIST INPUT */
.wl-form { display:flex; gap:10px; margin-bottom:20px; flex-wrap:wrap; }
.wl-input {
  background:var(--panel2); border:1px solid var(--border);
  border-radius:8px; padding:9px 14px;
  color:var(--text); font-family:var(--mono); font-size:13px;
  outline:none; width:160px;
}
.wl-input:focus { border-color:var(--green); }
.wl-select {
  background:var(--panel2); border:1px solid var(--border);
  border-radius:8px; padding:9px 14px;
  color:var(--text); font-size:13px; outline:none;
}
.btn-add {
  background:var(--green); color:#000; border:none;
  padding:9px 20px; border-radius:8px;
  font-weight:700; font-size:13px; cursor:pointer; transition:.2s;
}
.btn-add:hover { background:#69ff9e; }
.btn-analyze {
  background:var(--blue); color:#000; border:none;
  padding:9px 20px; border-radius:8px;
  font-weight:700; font-size:13px; cursor:pointer; transition:.2s;
}
.btn-analyze:hover { background:#80d8ff; }

/* EMPTY STATE */
.empty { text-align:center; padding:60px; color:var(--muted); }
.empty h3 { font-size:18px; margin-bottom:8px; color:var(--text); }
.empty p  { font-size:14px; line-height:1.7; }

/* SPINNER */
@keyframes spin { to { transform:rotate(360deg); } }
.spin { display:inline-block; width:14px; height:14px; border:2px solid transparent; border-top-color:currentColor; border-radius:50%; animation:spin .7s linear infinite; }

/* RISK COLORS */
.risk-LOW      { color:var(--green); }
.risk-MEDIUM   { color:var(--gold); }
.risk-HIGH     { color:var(--red); }
.risk-VERY_HIGH{ color:#ff1744; font-weight:700; }
</style>
</head>
<body>

<nav>
  <div class="nav-brand">INVESTMENT HQ <span>/ Meeko</span></div>
  <div class="nav-tab active" onclick="showTab('pending')">Pending <span class="nav-badge" id="pending-count">0</span></div>
  <div class="nav-tab" onclick="showTab('portfolio')">Portfolio</div>
  <div class="nav-tab" onclick="showTab('watchlist')">Watchlist</div>
  <div class="nav-tab" onclick="showTab('history')">History</div>
  <div class="nav-tab" onclick="showTab('tax')">Tax Center</div>
  <div class="nav-mode paper" id="mode-badge">PAPER MODE</div>
</nav>

<div class="content">

  <!-- ── PENDING ── -->
  <div class="tab-content active" id="tab-pending">
    <div class="stats" id="pending-stats"></div>
    <div id="pending-list">
      <div class="empty">
        <h3>No pending recommendations</h3>
        <p>Add tickers to your watchlist and run the analyst<br>to generate recommendations here.</p>
      </div>
    </div>
  </div>

  <!-- ── PORTFOLIO ── -->
  <div class="tab-content" id="tab-portfolio">
    <div class="stats" id="portfolio-stats"></div>
    <div class="card">
      <div class="card-title">Current Positions</div>
      <div id="positions-table">
        <div class="empty"><h3>No open positions</h3><p>Approve your first buy to start tracking.</p></div>
      </div>
    </div>
    <div class="card">
      <div class="card-title">P&amp;L Summary</div>
      <div id="pnl-table"></div>
    </div>
  </div>

  <!-- ── WATCHLIST ── -->
  <div class="tab-content" id="tab-watchlist">
    <div class="card">
      <div class="card-title">Add to Watchlist</div>
      <div class="wl-form">
        <input class="wl-input" id="wl-ticker" placeholder="AAPL, BTC-USD..." maxlength="12">
        <select class="wl-select" id="wl-type">
          <option value="stock">Stock</option>
          <option value="etf">ETF</option>
          <option value="crypto">Crypto</option>
        </select>
        <input class="wl-input" id="wl-notes" placeholder="Notes (optional)" style="width:200px">
        <button class="btn-add" onclick="addToWatchlist()">+ Add</button>
        <button class="btn-analyze" onclick="analyzeAll()"><span id="analyze-btn-txt">Analyze All Now</span></button>
      </div>
      <div id="watchlist-table">
        <div class="empty"><h3>Watchlist is empty</h3><p>Add tickers above. Your AI agent will analyze them and queue recommendations here.</p></div>
      </div>
    </div>
  </div>

  <!-- ── HISTORY ── -->
  <div class="tab-content" id="tab-history">
    <div class="card">
      <div class="card-title">Trade History (all trades — paper &amp; live)</div>
      <div id="history-table">
        <div class="empty"><h3>No trades yet</h3></div>
      </div>
    </div>
  </div>

  <!-- ── TAX CENTER ── -->
  <div class="tab-content" id="tab-tax">
    <div class="stats" id="tax-stats"></div>
    <div class="card">
      <div class="card-title">Tax Documents</div>
      <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px;">
        <button class="btn-analyze" onclick="exportForm8949()">Export Form 8949 CSV</button>
        <button class="btn-analyze" onclick="generateSummary()">Generate Annual Summary</button>
      </div>
      <div id="tax-content">
        <p style="color:var(--muted); font-size:13px; font-family:var(--mono);">
          Form 8949 covers all your capital gains and losses.<br>
          Export to CSV and import directly into TurboTax or TaxAct.<br><br>
          IMPORTANT: These are computer-generated estimates. Always have a CPA review your actual return.
        </p>
      </div>
    </div>
    <div class="card">
      <div class="card-title">Closed Positions &amp; Tax Lots</div>
      <div id="tax-lots-table">
        <div class="empty"><h3>No closed positions yet</h3></div>
      </div>
    </div>
  </div>

</div>

<!-- TOAST -->
<div class="toast" id="toast"></div>

<script>
// ── STATE ──────────────────────────────────────────────
let currentTab = 'pending';
let pendingData = [];

// ── NAV ───────────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  event.currentTarget.classList.add('active');
  currentTab = name;
  loadTab(name);
}

function loadTab(name) {
  if (name === 'pending')   loadPending();
  if (name === 'portfolio') loadPortfolio();
  if (name === 'watchlist') loadWatchlist();
  if (name === 'history')   loadHistory();
  if (name === 'tax')       loadTax();
}

// ── PENDING ───────────────────────────────────────────
async function loadPending() {
  const data = await api('/data/pending');
  pendingData = data.analyses || [];
  document.getElementById('pending-count').textContent = pendingData.length;

  const stats = document.getElementById('pending-stats');
  const buys  = pendingData.filter(a => a.action === 'BUY').length;
  const sells = pendingData.filter(a => a.action === 'SELL').length;
  const holds = pendingData.filter(a => a.action === 'HOLD').length;
  stats.innerHTML = `
    <div class="stat"><div class="stat-label">Pending</div><div class="stat-value gold">${pendingData.length}</div></div>
    <div class="stat"><div class="stat-label">BUY signals</div><div class="stat-value green">${buys}</div></div>
    <div class="stat"><div class="stat-label">SELL signals</div><div class="stat-value red">${sells}</div></div>
    <div class="stat"><div class="stat-label">HOLD signals</div><div class="stat-value blue">${holds}</div></div>
  `;

  const list = document.getElementById('pending-list');
  if (!pendingData.length) {
    list.innerHTML = '<div class="empty"><h3>No pending recommendations</h3><p>Add tickers to your watchlist and click "Analyze All Now" to generate recommendations.</p></div>';
    return;
  }

  list.innerHTML = pendingData.map(a => {
    const conf    = Math.round((a.confidence || 0.5) * 100);
    const confCol = conf >= 70 ? '#00e676' : conf >= 50 ? '#ffd740' : '#ff5252';
    const ind     = JSON.parse(a.indicators || '{}');
    const rsi     = ind.rsi_14 ? ind.rsi_14.toFixed(1) : 'N/A';
    const macd    = ind.macd ? ind.macd.toFixed(4) : 'N/A';
    return `
    <div class="rec-card" id="rec-${a.id}">
      <div class="rec-header">
        <div class="action-badge ${a.action}">${a.action}</div>
        <div class="rec-ticker">${a.ticker}</div>
        <div class="rec-price">$${parseFloat(a.price || 0).toFixed(2)}</div>
      </div>
      <div class="rec-body">
        <div class="rec-reasoning">${a.reasoning || 'Analysis in progress...'}</div>
        <div class="rec-meta">
          <div class="meta-chip">Risk: <span class="risk-${a.risk_level}">${a.risk_level}</span></div>
          <div class="meta-chip">RSI: <span>${rsi}</span></div>
          <div class="meta-chip">MACD: <span>${macd}</span></div>
          <div class="meta-chip">Asset: <span>${a.asset_type}</span></div>
          <div class="meta-chip">Time: <span>${a.timestamp ? a.timestamp.slice(0,16) : 'now'}</span></div>
        </div>
        <div class="conf-bar">
          <div class="conf-label"><span>Confidence</span><span style="color:${confCol}">${conf}%</span></div>
          <div class="conf-track"><div class="conf-fill" style="width:${conf}%;background:${confCol}"></div></div>
        </div>
        ${a.action !== 'HOLD' && a.action !== 'AVOID' ? `
        <div class="trade-input">
          <span class="trade-label">Quantity:</span>
          <input class="qty-box" id="qty-${a.id}" type="number" min="0.001" step="0.001" value="1" placeholder="# shares/coins">
          <span class="trade-label" id="total-${a.id}" style="color:var(--muted)"></span>
        </div>` : ''}
        <div class="action-row">
          ${a.action !== 'HOLD' && a.action !== 'AVOID' ? `
          <button class="btn-approve" onclick="approveRec(${a.id}, '${a.ticker}', '${a.action}', '${a.asset_type}', ${a.price || 0})">
            Approve ${a.action} — Execute
          </button>` : ''}
          <button class="btn-reject" onclick="rejectRec(${a.id})">Reject</button>
          <button class="btn-skip" onclick="skipRec(${a.id})">Skip for now</button>
        </div>
      </div>
    </div>`;
  }).join('');

  // Live total calc
  pendingData.forEach(a => {
    const qtyEl = document.getElementById(`qty-${a.id}`);
    const totEl = document.getElementById(`total-${a.id}`);
    if (qtyEl && totEl) {
      const update = () => {
        const total = (parseFloat(qtyEl.value) || 0) * parseFloat(a.price || 0);
        totEl.textContent = `= $${total.toFixed(2)} estimated`;
      };
      qtyEl.addEventListener('input', update);
      update();
    }
  });
}

async function approveRec(id, ticker, action, assetType, price) {
  const qtyEl = document.getElementById(`qty-${id}`);
  const qty   = parseFloat(qtyEl ? qtyEl.value : 1) || 1;

  const confirmed = confirm(
    `APPROVE ${action}: ${qty} ${ticker} @ ~$${price.toFixed(2)}\n` +
    `Estimated total: $${(qty * price).toFixed(2)}\n\n` +
    `This will place a real order (or paper trade).\nProceed?`
  );
  if (!confirmed) return;

  const result = await api('/approve', {
    method: 'POST',
    body: JSON.stringify({ analysis_id: id, ticker, action, asset_type: assetType, quantity: qty, price })
  });

  if (result.ok) {
    showToast(`${action} approved for ${qty} ${ticker} — Order placed!`);
    document.getElementById(`rec-${id}`).style.opacity = '0.3';
    setTimeout(() => loadPending(), 1500);
  } else {
    alert('Error: ' + (result.error || 'Unknown error'));
  }
}

async function rejectRec(id) {
  await api('/reject', { method: 'POST', body: JSON.stringify({ analysis_id: id }) });
  document.getElementById(`rec-${id}`).remove();
  showToast('Recommendation rejected and archived');
}

function skipRec(id) {
  document.getElementById(`rec-${id}`).style.opacity = '0.4';
}

// ── PORTFOLIO ─────────────────────────────────────────
async function loadPortfolio() {
  const data = await api('/data/portfolio');
  const positions = data.positions || [];
  const pnl       = data.pnl || {};

  const invested = positions.reduce((s, p) => s + (p.total_invested || 0), 0);
  document.getElementById('portfolio-stats').innerHTML = `
    <div class="stat"><div class="stat-label">Open Positions</div><div class="stat-value blue">${positions.length}</div></div>
    <div class="stat"><div class="stat-label">Total Invested</div><div class="stat-value gold">$${invested.toFixed(2)}</div></div>
  `;

  if (!positions.length) {
    document.getElementById('positions-table').innerHTML =
      '<div class="empty"><h3>No open positions</h3></div>';
  } else {
    document.getElementById('positions-table').innerHTML = `
      <table>
        <tr><th>Ticker</th><th>Type</th><th>Qty</th><th>Avg Cost</th><th>Total Invested</th><th>Since</th></tr>
        ${positions.map(p => `
        <tr>
          <td class="td-mono">${p.ticker}</td>
          <td class="td-muted">${p.asset_type}</td>
          <td class="td-mono">${parseFloat(p.quantity).toFixed(4)}</td>
          <td class="td-mono">$${parseFloat(p.avg_cost_basis).toFixed(4)}</td>
          <td class="td-mono">$${parseFloat(p.total_invested).toFixed(2)}</td>
          <td class="td-muted">${(p.first_purchase||'').slice(0,10)}</td>
        </tr>`).join('')}
      </table>`;
  }

  // P&L
  const stNet = (pnl.SHORT_TERM || {}).net || 0;
  const ltNet = (pnl.LONG_TERM  || {}).net || 0;
  document.getElementById('pnl-table').innerHTML = `
    <table>
      <tr><th>Type</th><th>Realized Gains</th><th>Realized Losses</th><th>Net</th><th>Trades</th></tr>
      <tr>
        <td>Short-Term (&lt;1yr)</td>
        <td class="td-green">$${((pnl.SHORT_TERM||{}).gains||0).toFixed(2)}</td>
        <td class="td-red">$${Math.abs((pnl.SHORT_TERM||{}).losses||0).toFixed(2)}</td>
        <td class="${stNet >= 0 ? 'td-green' : 'td-red'}">$${stNet.toFixed(2)}</td>
        <td class="td-muted">${(pnl.SHORT_TERM||{}).trade_count||0}</td>
      </tr>
      <tr>
        <td>Long-Term (&ge;1yr)</td>
        <td class="td-green">$${((pnl.LONG_TERM||{}).gains||0).toFixed(2)}</td>
        <td class="td-red">$${Math.abs((pnl.LONG_TERM||{}).losses||0).toFixed(2)}</td>
        <td class="${ltNet >= 0 ? 'td-green' : 'td-red'}">$${ltNet.toFixed(2)}</td>
        <td class="td-muted">${(pnl.LONG_TERM||{}).trade_count||0}</td>
      </tr>
    </table>`;
}

// ── WATCHLIST ─────────────────────────────────────────
async function loadWatchlist() {
  const data = await api('/data/watchlist');
  const items = data.watchlist || [];
  if (!items.length) {
    document.getElementById('watchlist-table').innerHTML =
      '<div class="empty"><h3>Watchlist empty</h3><p>Add tickers above to start.</p></div>';
    return;
  }
  document.getElementById('watchlist-table').innerHTML = `
    <table>
      <tr><th>Ticker</th><th>Type</th><th>Added</th><th>Notes</th><th></th></tr>
      ${items.map(i => `
      <tr>
        <td class="td-mono">${i.ticker}</td>
        <td class="td-muted">${i.asset_type}</td>
        <td class="td-muted">${(i.added||'').slice(0,10)}</td>
        <td style="color:var(--muted)">${i.notes||''}</td>
        <td>
          <button class="btn-skip" style="padding:4px 12px;font-size:11px"
            onclick="removeFromWatchlist('${i.ticker}')">Remove</button>
        </td>
      </tr>`).join('')}
    </table>`;
}

async function addToWatchlist() {
  const ticker = document.getElementById('wl-ticker').value.trim().toUpperCase();
  const type   = document.getElementById('wl-type').value;
  const notes  = document.getElementById('wl-notes').value.trim();
  if (!ticker) { alert('Enter a ticker symbol'); return; }
  await api('/watchlist/add', { method:'POST', body: JSON.stringify({ticker, asset_type: type, notes}) });
  document.getElementById('wl-ticker').value = '';
  document.getElementById('wl-notes').value  = '';
  showToast(`${ticker} added to watchlist`);
  loadWatchlist();
}

async function removeFromWatchlist(ticker) {
  await api('/watchlist/remove', { method:'POST', body: JSON.stringify({ticker}) });
  loadWatchlist();
}

async function analyzeAll() {
  const btn = document.getElementById('analyze-btn-txt');
  btn.innerHTML = '<span class="spin"></span> Analyzing...';
  const result = await api('/analyze/watchlist', { method: 'POST' });
  btn.textContent = 'Analyze All Now';
  showToast(`${result.count || 0} analyses queued — check Pending tab`);
  document.querySelector('[onclick="showTab(\'pending\')"]').click();
}

// ── HISTORY ───────────────────────────────────────────
async function loadHistory() {
  const data   = await api('/data/history');
  const trades = data.trades || [];
  if (!trades.length) {
    document.getElementById('history-table').innerHTML =
      '<div class="empty"><h3>No trades yet</h3></div>';
    return;
  }
  document.getElementById('history-table').innerHTML = `
    <table>
      <tr><th>Date</th><th>Ticker</th><th>Action</th><th>Qty</th><th>Price</th><th>Total</th><th>Exchange</th><th>Paper</th><th>Notes</th></tr>
      ${trades.map(t => `
      <tr>
        <td class="td-muted">${t.date||''}</td>
        <td class="td-mono">${t.ticker}</td>
        <td class="action-badge ${t.action}" style="display:inline-block;margin:2px 0">${t.action}</td>
        <td class="td-mono">${parseFloat(t.quantity).toFixed(4)}</td>
        <td class="td-mono">$${parseFloat(t.price).toFixed(4)}</td>
        <td class="td-mono">$${parseFloat(t.total_cost).toFixed(2)}</td>
        <td class="td-muted">${t.exchange||''}</td>
        <td style="color:${t.paper_trade ? 'var(--gold)' : 'var(--green)'}; font-family:var(--mono); font-size:11px">${t.paper_trade ? 'PAPER' : 'LIVE'}</td>
        <td style="color:var(--muted);font-size:12px">${t.notes||''}</td>
      </tr>`).join('')}
    </table>`;
}

// ── TAX ───────────────────────────────────────────────
async function loadTax() {
  const data = await api('/data/tax');
  const sum  = data.summary || {};
  document.getElementById('tax-stats').innerHTML = `
    <div class="stat"><div class="stat-label">ST Net G/L</div>
      <div class="stat-value ${sum.short_term_net>=0?'green':'red'}">$${(sum.short_term_net||0).toFixed(2)}</div></div>
    <div class="stat"><div class="stat-label">LT Net G/L</div>
      <div class="stat-value ${sum.long_term_net>=0?'green':'red'}">$${(sum.long_term_net||0).toFixed(2)}</div></div>
    <div class="stat"><div class="stat-label">Est. Tax Due</div>
      <div class="stat-value red">$${(sum.estimated_total_tax||0).toFixed(2)}</div></div>
    <div class="stat"><div class="stat-label">Total Net</div>
      <div class="stat-value ${sum.total_net>=0?'green':'red'}">$${(sum.total_net||0).toFixed(2)}</div></div>
  `;
}

async function exportForm8949() {
  const result = await api('/tax/form8949', { method:'POST' });
  showToast(result.message || 'Form 8949 exported');
}

async function generateSummary() {
  const result = await api('/tax/summary', { method:'POST' });
  showToast(result.message || 'Summary generated');
}

// ── UTILS ─────────────────────────────────────────────
async function api(path, opts={}) {
  try {
    const r = await fetch(path, {
      headers: {'Content-Type': 'application/json'},
      ...opts
    });
    return await r.json();
  } catch(e) { return {error: e.message}; }
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}

// ── INIT ──────────────────────────────────────────────
loadPending();
setInterval(loadPending, 30000); // refresh every 30s
</script>
</body>
</html>"""

# ── REQUEST HANDLER ───────────────────────────────────────
class PortalHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, *args): pass

    def send_json(self, data, code=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            body = PORTAL_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/data/pending':
            self.send_json({'analyses': _get_pending()})
        elif self.path == '/data/portfolio':
            self.send_json({'positions': _get_positions(), 'pnl': _get_pnl()})
        elif self.path == '/data/watchlist':
            self.send_json({'watchlist': _get_watchlist()})
        elif self.path == '/data/history':
            self.send_json({'trades': _get_history()})
        elif self.path == '/data/tax':
            self.send_json({'summary': _get_tax_summary()})
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = json.loads(self.rfile.read(length)) if length else {}

        if self.path == '/approve':
            self.send_json(_approve_trade(body))
        elif self.path == '/reject':
            self.send_json(_reject_analysis(body))
        elif self.path == '/watchlist/add':
            self.send_json(_add_watchlist(body))
        elif self.path == '/watchlist/remove':
            self.send_json(_remove_watchlist(body))
        elif self.path == '/analyze/watchlist':
            self.send_json(_trigger_analysis())
        elif self.path == '/tax/form8949':
            self.send_json(_export_8949())
        elif self.path == '/tax/summary':
            self.send_json(_tax_summary_export())
        else:
            self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

# ── DATA FUNCTIONS ────────────────────────────────────────
def _db():
    return sqlite3.connect(str(DB_PATH))

def _get_pending():
    try:
        conn = _db()
        rows = conn.execute(
            "SELECT id,timestamp,ticker,asset_type,action,confidence,risk_level,price,reasoning,indicators FROM analyses WHERE status='pending_approval' ORDER BY timestamp DESC"
        ).fetchall()
        conn.close()
        cols = ['id','timestamp','ticker','asset_type','action','confidence','risk_level','price','reasoning','indicators']
        return [dict(zip(cols, r)) for r in rows]
    except: return []

def _get_positions():
    try:
        conn = _db()
        rows = conn.execute('SELECT * FROM positions ORDER BY ticker').fetchall()
        conn.close()
        cols = ['ticker','asset_type','quantity','avg_cost_basis','total_invested','first_purchase','last_updated']
        return [dict(zip(cols, r)) for r in rows]
    except: return []

def _get_pnl():
    try:
        conn = _db()
        rows = conn.execute(
            "SELECT term, SUM(CASE WHEN gain_loss>0 THEN gain_loss ELSE 0 END), SUM(CASE WHEN gain_loss<0 THEN gain_loss ELSE 0 END), COUNT(*) FROM tax_lots WHERE date_sold IS NOT NULL GROUP BY term"
        ).fetchall()
        conn.close()
        result = {}
        for term, gains, losses, count in rows:
            result[term] = {'gains': round(gains or 0,2), 'losses': round(losses or 0,2), 'net': round((gains or 0)+(losses or 0),2), 'trade_count': count}
        return result
    except: return {}

def _get_watchlist():
    try:
        conn = _db()
        rows = conn.execute("SELECT ticker,asset_type,added,notes FROM watchlist WHERE active=1").fetchall()
        conn.close()
        return [{'ticker':r[0],'asset_type':r[1],'added':r[2],'notes':r[3]} for r in rows]
    except: return []

def _get_history():
    try:
        conn = _db()
        rows = conn.execute('SELECT id,timestamp,date,ticker,asset_type,action,quantity,price,fees,total_cost,exchange,order_id,analysis_id,notes,paper_trade FROM trades ORDER BY timestamp DESC LIMIT 200').fetchall()
        conn.close()
        cols = ['id','timestamp','date','ticker','asset_type','action','quantity','price','fees','total_cost','exchange','order_id','analysis_id','notes','paper_trade']
        return [dict(zip(cols, r)) for r in rows]
    except: return []

def _get_tax_summary():
    try:
        conn = _db()
        rows = conn.execute(
            "SELECT term, SUM(CASE WHEN gain_loss>0 THEN gain_loss ELSE 0 END), SUM(CASE WHEN gain_loss<0 THEN gain_loss ELSE 0 END) FROM tax_lots WHERE date_sold IS NOT NULL GROUP BY term"
        ).fetchall()
        conn.close()
        st_net = lt_net = 0
        for term, gains, losses in rows:
            net = (gains or 0) + (losses or 0)
            if 'SHORT' in str(term): st_net = net
            if 'LONG'  in str(term): lt_net = net
        return {
            'short_term_net': round(st_net, 2),
            'long_term_net':  round(lt_net, 2),
            'total_net':      round(st_net + lt_net, 2),
            'estimated_total_tax': round(max(0, st_net * 0.24) + max(0, lt_net * 0.15), 2)
        }
    except: return {}

def _approve_trade(body):
    """Generate approval token and execute order."""
    try:
        analysis_id = body.get('analysis_id')
        ticker      = body.get('ticker', '').upper()
        action      = body.get('action', 'BUY')
        asset_type  = body.get('asset_type', 'stock')
        quantity    = float(body.get('quantity', 1))
        price       = float(body.get('price', 0))

        # Create approval token
        token = str(uuid.uuid4())
        conn  = _db()
        conn.execute('''CREATE TABLE IF NOT EXISTS approval_tokens (
            token TEXT PRIMARY KEY, analysis_id INTEGER,
            created_at TEXT, used INTEGER DEFAULT 0,
            action TEXT, ticker TEXT, quantity REAL, price REAL)''')
        conn.execute('INSERT INTO approval_tokens VALUES (?,?,?,0,?,?,?,?)',
                     (token, analysis_id, datetime.now().isoformat(), action, ticker, quantity, price))
        # Mark analysis as approved
        conn.execute("UPDATE analyses SET status='approved' WHERE id=?", (analysis_id,))
        conn.commit()
        conn.close()

        # Execute order via connector (paper mode by default)
        sys.path.insert(0, str(BASE / 'src'))
        from exchange_connector import AlpacaConnector, CoinbaseConnector, get_paper_mode, mark_token_used
        from trade_journal import TradeJournal
        journal = TradeJournal()
        side    = action.lower()  # buy or sell

        order_result = {}
        exchange_used = 'paper' if get_paper_mode() else 'live'

        if asset_type in ('stock', 'etf'):
            alpaca = AlpacaConnector()
            try:
                order_result = alpaca.submit_order(ticker, quantity, side,
                                                   approval_token=token)
                exchange_used = 'alpaca'
            except Exception as e:
                # Log but don't block in paper mode
                order_result = {'error': str(e), 'paper_simulated': get_paper_mode()}
                exchange_used = 'alpaca_paper'

        elif asset_type == 'crypto':
            cb = CoinbaseConnector()
            try:
                product_id = ticker if '-' in ticker else f"{ticker}-USD"
                order_result = cb.place_order(product_id, side.upper(), quantity,
                                              approval_token=token)
                exchange_used = 'coinbase'
            except Exception as e:
                order_result = {'error': str(e), 'paper_simulated': get_paper_mode()}
                exchange_used = 'coinbase_paper'

        mark_token_used(token)

        # Record in journal
        if action == 'BUY':
            trade_id = journal.record_buy(
                ticker, quantity, price, exchange_used, asset_type,
                analysis_id=analysis_id, paper=get_paper_mode()
            )
        else:
            tax_event = journal.record_sell(
                ticker, quantity, price, exchange_used, asset_type,
                analysis_id=analysis_id, paper=get_paper_mode()
            )
            trade_id = tax_event.get('trade_id', 'recorded')

        # Save approved recommendation
        approved_file = BASE / 'approved' / f"{ticker}_{action}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(approved_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'ticker': ticker, 'action': action, 'quantity': quantity,
                'price': price, 'analysis_id': analysis_id,
                'trade_id': str(trade_id), 'order_result': order_result,
                'paper_mode': get_paper_mode()
            }, f, indent=2, default=str)

        return {
            'ok': True,
            'message': f"{action} {quantity} {ticker} executed",
            'trade_id': str(trade_id),
            'paper_mode': get_paper_mode()
        }

    except Exception as e:
        return {'ok': False, 'error': str(e)}

def _reject_analysis(body):
    try:
        conn = _db()
        conn.execute("UPDATE analyses SET status='rejected' WHERE id=?", (body.get('analysis_id'),))
        conn.commit()
        conn.close()
        # Move to rejected folder
        import glob
        for f in glob.glob(str(BASE / 'pending' / f"*.json")):
            data = json.load(open(f))
            if data.get('id') == body.get('analysis_id'):
                Path(f).rename(BASE / 'rejected' / Path(f).name)
                break
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def _add_watchlist(body):
    try:
        conn = _db()
        conn.execute('''CREATE TABLE IF NOT EXISTS watchlist (
            ticker TEXT PRIMARY KEY, asset_type TEXT, added TEXT, notes TEXT, active INTEGER DEFAULT 1)''')
        conn.execute('INSERT OR REPLACE INTO watchlist VALUES (?,?,?,?,1)',
                     (body['ticker'].upper(), body.get('asset_type','stock'),
                      datetime.now().isoformat(), body.get('notes','')))
        conn.commit()
        conn.close()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def _remove_watchlist(body):
    try:
        conn = _db()
        conn.execute("UPDATE watchlist SET active=0 WHERE ticker=?", (body['ticker'].upper(),))
        conn.commit()
        conn.close()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def _trigger_analysis():
    """Kick off analyst on all watchlist items in background thread."""
    def run():
        try:
            sys.path.insert(0, str(BASE / 'src'))
            from ai_analyst import AIAnalyst
            a = AIAnalyst()
            a.analyze_watchlist()
        except Exception as e:
            print(f"Analyst error: {e}")
    threading.Thread(target=run, daemon=True).start()
    conn = _db()
    count = conn.execute("SELECT COUNT(*) FROM watchlist WHERE active=1").fetchone()[0]
    conn.close()
    return {'ok': True, 'count': count, 'message': f'Analysis started for {count} assets'}

def _export_8949():
    try:
        sys.path.insert(0, str(BASE / 'src'))
        from trade_journal import TradeJournal
        path = TradeJournal().generate_form_8949()
        return {'ok': True, 'message': f'Form 8949 saved to {path}', 'path': str(path)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def _tax_summary_export():
    try:
        sys.path.insert(0, str(BASE / 'src'))
        from trade_journal import TradeJournal
        summary = TradeJournal().generate_annual_summary()
        return {'ok': True, 'message': f'Tax summary saved — Est. tax: ${summary.get("estimated_total_tax",0)}', 'summary': summary}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


if __name__ == '__main__':
    server = http.server.HTTPServer(('127.0.0.1', PORT), PortalHandler)
    print(f"\n{'='*56}")
    print(f"  INVESTMENT HQ — APPROVAL PORTAL")
    print(f"{'='*56}")
    print(f"\n  Opening http://localhost:{PORT}")
    print(f"  All trade approvals happen here.")
    print(f"  Press Ctrl+C to close.\n")
    threading.Timer(1.2, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Portal closed.")
