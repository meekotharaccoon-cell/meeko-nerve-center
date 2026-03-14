"""
TRADING DASHBOARD — Web UI
===========================
Local web server. Open in browser. Your command center for:
  - Viewing AI analyst recommendations
  - Approving or rejecting each trade (ONE CLICK)
  - Seeing live positions and P&L
  - Generating tax reports
  - Reviewing full trade history

Run: python trading_dashboard.py
Opens: http://localhost:7778
"""

import http.server
import json
import os
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

BASE = Path(r'C:\Users\meeko\Desktop\TRADING_SYSTEM')
PORT = 7778

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Meeko Trading Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #080c10; --panel: #0f1419; --panel2: #161d26;
  --border: #1e2a36; --border2: #263040;
  --green: #00d97e; --red: #ff4560; --gold: #ffd700;
  --blue: #00aaff; --muted: #4a6070;
  --text: #cdd9e5; --text2: #8899a6;
  --mono: 'IBM Plex Mono', monospace;
  --head: 'Bebas Neue', sans-serif;
  --body: 'Inter', sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--body);min-height:100vh;overflow-x:hidden}

/* GRID */
.shell{display:grid;grid-template-rows:56px 1fr;min-height:100vh}
.topbar{
  background:var(--panel);border-bottom:1px solid var(--border);
  display:flex;align-items:center;padding:0 24px;gap:24px;
  position:sticky;top:0;z-index:100;
}
.logo{font-family:var(--head);font-size:22px;letter-spacing:2px;color:var(--gold)}
.logo span{color:var(--text2);font-size:14px;font-family:var(--mono);letter-spacing:1px;margin-left:12px}
.topbar-right{margin-left:auto;display:flex;gap:16px;align-items:center}
.live-dot{width:8px;height:8px;border-radius:50%;background:var(--green);
  animation:pulse 2s infinite;display:inline-block}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.mode-badge{
  font-family:var(--mono);font-size:11px;letter-spacing:2px;
  padding:4px 12px;border-radius:4px;text-transform:uppercase;
}
.mode-paper{background:rgba(0,173,255,0.15);color:var(--blue);border:1px solid rgba(0,173,255,0.3)}
.mode-live{background:rgba(255,69,96,0.15);color:var(--red);border:1px solid rgba(255,69,96,0.3)}

.main{display:grid;grid-template-columns:260px 1fr;gap:0}
.sidebar{
  background:var(--panel);border-right:1px solid var(--border);
  padding:20px 0; position:sticky;top:56px;height:calc(100vh - 56px);
  overflow-y:auto;
}
.nav-section{padding:8px 20px;font-family:var(--mono);font-size:10px;
  letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-top:12px}
.nav-item{
  display:flex;align-items:center;gap:10px;padding:10px 20px;
  cursor:pointer;font-size:14px;color:var(--text2);transition:.2s;
  border-left:3px solid transparent;
}
.nav-item:hover{background:var(--panel2);color:var(--text);border-left-color:var(--border2)}
.nav-item.active{background:var(--panel2);color:var(--gold);border-left-color:var(--gold)}
.nav-badge{
  margin-left:auto;background:var(--red);color:white;
  font-size:11px;font-family:var(--mono);padding:2px 7px;border-radius:99px;
  display:none;
}
.nav-badge.show{display:inline-block}

.content{padding:28px;overflow-y:auto;height:calc(100vh - 56px)}

/* PANELS */
.view{display:none}.view.active{display:block}
.page-title{font-family:var(--head);font-size:32px;letter-spacing:2px;margin-bottom:6px;color:var(--text)}
.page-sub{color:var(--text2);font-size:13px;margin-bottom:28px}

/* STAT CARDS */
.stat-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:28px}
.stat-card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:18px 20px}
.stat-label{font-family:var(--mono);font-size:11px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:8px}
.stat-val{font-size:24px;font-weight:600;font-family:var(--mono)}
.stat-val.green{color:var(--green)}.stat-val.red{color:var(--red)}
.stat-val.gold{color:var(--gold)}.stat-val.blue{color:var(--blue)}
.stat-change{font-size:12px;font-family:var(--mono);color:var(--text2);margin-top:4px}

/* RECOMMENDATION CARDS */
.rec-list{display:flex;flex-direction:column;gap:16px}
.rec-card{
  background:var(--panel);border:1px solid var(--border);border-radius:16px;
  overflow:hidden;transition:.3s;
}
.rec-card:hover{border-color:var(--border2)}
.rec-card.pending{border-left:4px solid var(--gold)}
.rec-card.approved{border-left:4px solid var(--green)}
.rec-card.rejected{border-left:4px solid var(--red);opacity:.6}

.rec-header{display:flex;align-items:center;gap:14px;padding:16px 20px;cursor:pointer}
.rec-symbol{font-family:var(--head);font-size:26px;letter-spacing:2px;min-width:80px}
.rec-price{font-family:var(--mono);font-size:15px;color:var(--text2)}
.rec-action{
  padding:4px 14px;border-radius:6px;font-weight:600;font-size:13px;
  font-family:var(--mono);letter-spacing:1px;
}
.action-BUY{background:rgba(0,217,126,.15);color:var(--green);border:1px solid rgba(0,217,126,.3)}
.action-SELL{background:rgba(255,69,96,.15);color:var(--red);border:1px solid rgba(255,69,96,.3)}
.action-HOLD{background:rgba(255,215,0,.12);color:var(--gold);border:1px solid rgba(255,215,0,.3)}
.action-WATCH{background:rgba(0,170,255,.12);color:var(--blue);border:1px solid rgba(0,170,255,.3)}
.rec-status{margin-left:auto;font-family:var(--mono);font-size:11px;letter-spacing:1px;
  padding:3px 10px;border-radius:4px;text-transform:uppercase}
.status-PENDING{background:rgba(255,215,0,.1);color:var(--gold)}
.status-APPROVED{background:rgba(0,217,126,.1);color:var(--green)}
.status-REJECTED{background:rgba(255,69,96,.1);color:var(--red)}
.rec-time{font-family:var(--mono);font-size:11px;color:var(--muted)}

.rec-body{padding:0 20px 20px;display:none}
.rec-card.open .rec-body{display:block}

.analysis-box{
  background:var(--panel2);border-radius:10px;padding:16px 18px;
  font-size:13px;line-height:1.8;color:var(--text);margin-bottom:16px;
  white-space:pre-wrap;font-family:var(--body);
}
.indicators{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}
.ind{
  background:var(--bg);border:1px solid var(--border);
  border-radius:6px;padding:6px 12px;
  font-family:var(--mono);font-size:11px;
}
.ind-label{color:var(--muted)}.ind-val{color:var(--text);margin-left:6px}

.headlines{margin-bottom:16px}
.headlines-title{font-family:var(--mono);font-size:10px;letter-spacing:2px;
  color:var(--muted);text-transform:uppercase;margin-bottom:8px}
.headline{font-size:12px;color:var(--text2);padding:4px 0;
  border-bottom:1px solid var(--border);line-height:1.5}

.approval-bar{display:flex;gap:10px;align-items:center;padding-top:12px;
  border-top:1px solid var(--border)}
.qty-input{
  background:var(--panel2);border:1px solid var(--border2);color:var(--text);
  border-radius:8px;padding:9px 14px;font-family:var(--mono);font-size:13px;
  width:130px;outline:none;
}
.qty-input:focus{border-color:var(--gold)}
.btn{
  padding:10px 22px;border-radius:8px;border:none;cursor:pointer;
  font-family:var(--body);font-weight:600;font-size:13px;
  transition:.2s;display:inline-flex;align-items:center;gap:6px;
}
.btn:active{transform:scale(.98)}
.btn-approve{background:var(--green);color:#000}
.btn-approve:hover{filter:brightness(1.15)}
.btn-reject{background:transparent;color:var(--red);border:1px solid var(--red)}
.btn-reject:hover{background:rgba(255,69,96,.1)}
.btn-refresh{background:var(--panel2);color:var(--text2);border:1px solid var(--border)}
.btn-refresh:hover{border-color:var(--text2);color:var(--text)}
.btn-gold{background:var(--gold);color:#000}
.btn-gold:hover{filter:brightness(1.1)}
.confirm-msg{font-family:var(--mono);font-size:12px;margin-top:8px;display:none}
.confirm-msg.show{display:block}
.confirm-msg.ok{color:var(--green)}.confirm-msg.err{color:var(--red)}

/* POSITIONS TABLE */
.table-wrap{overflow-x:auto;margin-top:8px}
table{width:100%;border-collapse:collapse;font-size:13px}
thead tr{border-bottom:2px solid var(--border)}
th{font-family:var(--mono);font-size:11px;color:var(--muted);
  text-transform:uppercase;letter-spacing:1px;padding:10px 14px;text-align:left}
tbody tr{border-bottom:1px solid var(--border);transition:.2s}
tbody tr:hover{background:var(--panel2)}
td{padding:12px 14px;font-family:var(--mono);font-size:13px}
.pos-pl-pos{color:var(--green)}.pos-pl-neg{color:var(--red)}

/* TAX SECTION */
.tax-year-row{display:flex;gap:12px;align-items:center;margin-bottom:20px;flex-wrap:wrap}
.tax-card{
  background:var(--panel);border:1px solid var(--border);border-radius:12px;
  padding:20px;margin-bottom:12px;
}
.tax-line{display:flex;justify-content:space-between;align-items:center;
  padding:10px 0;border-bottom:1px solid var(--border);font-size:14px}
.tax-line:last-child{border:none}
.tax-line .lbl{color:var(--text2)}
.tax-line .val{font-family:var(--mono);font-weight:600}

/* EMPTY STATES */
.empty{text-align:center;padding:60px 20px;color:var(--muted)}
.empty .icon{font-size:48px;margin-bottom:16px;opacity:.4}
.empty h3{font-family:var(--head);font-size:24px;letter-spacing:2px;margin-bottom:8px;color:var(--text2)}
.empty p{font-size:14px;line-height:1.6}

/* SCROLLBAR */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}
</style>
</head>
<body>
<div class="shell">

<!-- TOPBAR -->
<div class="topbar">
  <div class="logo">MEEKO TRADING <span>COMMAND CENTER</span></div>
  <div class="topbar-right">
    <span class="live-dot"></span>
    <span id="mode-badge" class="mode-badge mode-paper">PAPER MODE</span>
    <span style="font-family:var(--mono);font-size:12px;color:var(--muted)" id="clock"></span>
  </div>
</div>

<div class="main">
<!-- SIDEBAR -->
<div class="sidebar">
  <div class="nav-section">Overview</div>
  <div class="nav-item active" onclick="showView('portfolio')">&#9632; Portfolio</div>
  <div class="nav-item" onclick="showView('positions')">&#9671; Positions</div>

  <div class="nav-section">AI Analyst</div>
  <div class="nav-item" onclick="showView('pending')" id="nav-pending">
    &#9650; Pending Approvals
    <span class="nav-badge" id="pending-badge">0</span>
  </div>
  <div class="nav-item" onclick="showView('history')">&#9632; Trade History</div>

  <div class="nav-section">Tax & Records</div>
  <div class="nav-item" onclick="showView('tax')">&#9670; Tax Reports</div>

  <div class="nav-section">System</div>
  <div class="nav-item" onclick="showView('analyze')">&#9651; Run Analysis</div>
  <div class="nav-item" onclick="window.open('http://localhost:7777','_blank')">&#9654; Setup Wizard</div>
</div>

<!-- CONTENT -->
<div class="content">

  <!-- PORTFOLIO VIEW -->
  <div class="view active" id="view-portfolio">
    <div class="page-title">PORTFOLIO</div>
    <div class="page-sub">Live account overview. Paper mode by default — switch to Live in Setup Wizard.</div>
    <div class="stat-row" id="portfolio-stats">
      <div class="stat-card">
        <div class="stat-label">Equity</div>
        <div class="stat-val gold" id="stat-equity">—</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Buying Power</div>
        <div class="stat-val blue" id="stat-bp">—</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Cash</div>
        <div class="stat-val" id="stat-cash">—</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Portfolio Value</div>
        <div class="stat-val" id="stat-pv">—</div>
      </div>
    </div>
    <div style="display:flex;gap:10px;margin-bottom:20px">
      <button class="btn btn-refresh" onclick="loadPortfolio()">Refresh Portfolio</button>
      <button class="btn btn-gold" onclick="showView('pending')">View AI Recommendations</button>
    </div>
    <div id="portfolio-error" style="display:none" class="empty">
      <div class="icon">&#9888;</div>
      <h3>NOT CONNECTED</h3>
      <p>Run the Setup Wizard to connect your Alpaca account.<br>Paper trading is free — no real money needed to start.</p>
      <br><button class="btn btn-gold" onclick="window.open('http://localhost:7777','_blank')">Open Setup Wizard</button>
    </div>
  </div>

  <!-- POSITIONS VIEW -->
  <div class="view" id="view-positions">
    <div class="page-title">POSITIONS</div>
    <div class="page-sub">Current open positions and unrealized P&L.</div>
    <button class="btn btn-refresh" onclick="loadPositions()" style="margin-bottom:20px">Refresh Positions</button>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Symbol</th><th>Qty</th><th>Avg Price</th>
          <th>Current</th><th>Market Value</th><th>Unrealized P&L</th><th>%</th>
        </tr></thead>
        <tbody id="positions-body">
          <tr><td colspan="7" style="text-align:center;color:var(--muted);padding:40px">Loading...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- PENDING APPROVALS -->
  <div class="view" id="view-pending">
    <div class="page-title">PENDING APPROVALS</div>
    <div class="page-sub">Your AI analyst's recommendations. YOU decide what executes — approve or reject each one.</div>
    <div style="margin-bottom:20px;display:flex;gap:10px">
      <button class="btn btn-refresh" onclick="loadPending()">Refresh Queue</button>
      <button class="btn btn-gold" onclick="showView('analyze')">Run New Analysis</button>
    </div>
    <div id="pending-list" class="rec-list">
      <div class="empty">
        <div class="icon">&#9651;</div>
        <h3>QUEUE EMPTY</h3>
        <p>No pending recommendations.<br>Run an analysis to get AI picks for your watchlist.</p>
      </div>
    </div>
  </div>

  <!-- TRADE HISTORY -->
  <div class="view" id="view-history">
    <div class="page-title">TRADE HISTORY</div>
    <div class="page-sub">Every trade logged. Paper trades shown in blue.</div>
    <div class="table-wrap" style="margin-top:8px">
      <table>
        <thead><tr>
          <th>Date</th><th>Exchange</th><th>Mode</th><th>Symbol</th>
          <th>Side</th><th>Qty</th><th>Price</th><th>Total</th>
          <th>G/L</th><th>Term</th>
        </tr></thead>
        <tbody id="history-body">
          <tr><td colspan="10" style="text-align:center;color:var(--muted);padding:40px">Loading...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- TAX REPORTS -->
  <div class="view" id="view-tax">
    <div class="page-title">TAX REPORTS</div>
    <div class="page-sub">FIFO cost basis. Form 8949-ready CSV. Consult a tax professional.</div>
    <div class="tax-year-row">
      <select id="tax-year" style="background:var(--panel2);border:1px solid var(--border2);color:var(--text);padding:10px 14px;border-radius:8px;font-family:var(--mono);font-size:13px;outline:none">
        <option>2026</option><option>2025</option><option>2024</option>
      </select>
      <button class="btn btn-refresh" onclick="loadTax()">Generate Report</button>
      <button class="btn btn-gold" onclick="download8949()">Download Form 8949 CSV</button>
    </div>
    <div id="tax-content">
      <div class="empty">
        <div class="icon">&#9670;</div>
        <h3>SELECT YEAR</h3>
        <p>Choose a tax year above and click Generate Report.</p>
      </div>
    </div>
  </div>

  <!-- RUN ANALYSIS -->
  <div class="view" id="view-analyze">
    <div class="page-title">RUN ANALYSIS</div>
    <div class="page-sub">Enter symbols and your local Mistral AI will analyze them. Results go to Pending Approvals.</div>
    <div class="tax-card">
      <div class="tax-line" style="flex-direction:column;align-items:flex-start;gap:10px">
        <label style="font-family:var(--mono);font-size:11px;color:var(--muted);letter-spacing:2px;text-transform:uppercase">
          Symbols (comma-separated)
        </label>
        <input id="analyze-symbols" type="text" value="AAPL, TSLA, BTC-USD, ETH-USD, SOL-USD"
          style="width:100%;background:var(--bg);border:1px solid var(--border2);color:var(--text);
          border-radius:8px;padding:12px 16px;font-family:var(--mono);font-size:14px;outline:none">
      </div>
      <div class="tax-line" style="flex-direction:column;align-items:flex-start;gap:10px">
        <label style="font-family:var(--mono);font-size:11px;color:var(--muted);letter-spacing:2px;text-transform:uppercase">
          Extra context for AI (optional)
        </label>
        <input id="analyze-context" type="text" placeholder="e.g. I want to reduce crypto exposure this week"
          style="width:100%;background:var(--bg);border:1px solid var(--border2);color:var(--text);
          border-radius:8px;padding:12px 16px;font-family:var(--mono);font-size:14px;outline:none">
      </div>
    </div>
    <button class="btn btn-gold" style="font-size:15px;padding:14px 36px" onclick="runAnalysis()">
      <span id="analyze-btn-txt">Run AI Analysis</span>
    </button>
    <div id="analyze-status" style="margin-top:16px;font-family:var(--mono);font-size:13px;color:var(--text2)"></div>
  </div>

</div><!-- /content -->
</div><!-- /main -->
</div><!-- /shell -->

<script>
// Clock
setInterval(() => {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString();
}, 1000);

// View switching
function showView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('view-' + name)?.classList.add('active');
  event?.currentTarget?.classList.add('active');
  if (name === 'pending') loadPending();
  if (name === 'positions') loadPositions();
  if (name === 'history') loadHistory();
  if (name === 'portfolio') loadPortfolio();
}

function fmt(n) {
  if (n == null) return '—';
  return '$' + parseFloat(n).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
}
function fmtNum(n) {
  return parseFloat(n).toLocaleString('en-US', {maximumFractionDigits:6});
}

// ── PORTFOLIO ─────────────────────────────────────────────
async function loadPortfolio() {
  try {
    const r = await fetch('/api/portfolio');
    const d = await r.json();
    if (d.error) { showPortfolioError(); return; }
    document.getElementById('portfolio-error').style.display = 'none';
    document.getElementById('stat-equity').textContent = fmt(d.equity);
    document.getElementById('stat-bp').textContent     = fmt(d.buying_power);
    document.getElementById('stat-cash').textContent   = fmt(d.cash);
    document.getElementById('stat-pv').textContent     = fmt(d.portfolio_value);
    const badge = document.getElementById('mode-badge');
    if (d.mode === 'LIVE') {
      badge.textContent = 'LIVE MODE'; badge.className = 'mode-badge mode-live';
    }
  } catch(e) { showPortfolioError(); }
}
function showPortfolioError() {
  document.getElementById('portfolio-error').style.display = 'block';
}

// ── POSITIONS ─────────────────────────────────────────────
async function loadPositions() {
  const tbody = document.getElementById('positions-body');
  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--muted)">Loading...</td></tr>';
  try {
    const r = await fetch('/api/positions');
    const d = await r.json();
    if (!d.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--muted)">No open positions</td></tr>';
      return;
    }
    tbody.innerHTML = d.map(p => {
      const plCls = parseFloat(p.unrealized_pl) >= 0 ? 'pos-pl-pos' : 'pos-pl-neg';
      const pctCls = parseFloat(p.unrealized_pct) >= 0 ? 'pos-pl-pos' : 'pos-pl-neg';
      return `<tr>
        <td style="font-weight:600;color:var(--text)">${p.symbol}</td>
        <td>${fmtNum(p.qty)}</td>
        <td>${fmt(p.avg_price)}</td>
        <td>${fmt(p.current)}</td>
        <td>${fmt(p.market_val)}</td>
        <td class="${plCls}">${fmt(p.unrealized_pl)}</td>
        <td class="${pctCls}">${parseFloat(p.unrealized_pct).toFixed(2)}%</td>
      </tr>`;
    }).join('');
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--red)">Not connected to exchange</td></tr>`;
  }
}

// ── PENDING ───────────────────────────────────────────────
async function loadPending() {
  const list = document.getElementById('pending-list');
  try {
    const r = await fetch('/api/pending');
    const d = await r.json();
    const items = Object.values(d).sort((a,b) => b.created.localeCompare(a.created));
    const badge = document.getElementById('pending-badge');
    const count = items.filter(i => i.status === 'PENDING').length;
    badge.textContent = count;
    badge.className = 'nav-badge' + (count > 0 ? ' show' : '');
    if (!items.length) {
      list.innerHTML = `<div class="empty"><div class="icon">&#9651;</div><h3>QUEUE EMPTY</h3><p>No recommendations yet.<br>Click "Run New Analysis" to get AI picks.</p></div>`;
      return;
    }
    list.innerHTML = items.map(rec => buildRecCard(rec)).join('');
  } catch(e) {
    list.innerHTML = `<div class="empty"><div class="icon">&#9888;</div><h3>ERROR</h3><p>${e.message}</p></div>`;
  }
}

function buildRecCard(rec) {
  const action = (rec.ai_analysis || '').match(/RECOMMENDATION[:\s]+([A-Z]+)/)?.[1] || 'WATCH';
  const risk   = (rec.ai_analysis || '').match(/RISK LEVEL[:\s]+([A-Z]+)/)?.[1] || '';
  const inds = rec.indicators || {};
  const indHTML = Object.entries(inds).filter(([k]) => k !== 'trend').map(([k,v]) =>
    `<div class="ind"><span class="ind-label">${k}</span><span class="ind-val">${v}</span></div>`
  ).join('');
  const headlines = (rec.headlines || []).map(h =>
    `<div class="headline">&#8250; ${h}</div>`
  ).join('');

  const isActive = rec.status === 'PENDING';
  return `<div class="rec-card ${rec.status.toLowerCase()}" id="rec-${rec.id}">
    <div class="rec-header" onclick="toggleRec('${rec.id}')">
      <div class="rec-symbol">${rec.symbol}</div>
      <div>
        <div class="rec-price">${fmt(rec.current_price)}</div>
        <div class="rec-time">${rec.created?.slice(0,16).replace('T',' ')}</div>
      </div>
      <div class="rec-action action-${action}">${action}</div>
      <div class="rec-status status-${rec.status}">${rec.status}</div>
    </div>
    <div class="rec-body">
      <div class="analysis-box">${rec.ai_analysis || 'No analysis text'}</div>
      ${inds && Object.keys(inds).length ? `<div class="indicators">${indHTML}</div>` : ''}
      ${headlines ? `<div class="headlines"><div class="headlines-title">Recent Headlines</div>${headlines}</div>` : ''}
      ${isActive ? `
      <div class="approval-bar">
        <input class="qty-input" id="qty-${rec.id}" type="number" placeholder="Qty / Size" min="0" step="any">
        <button class="btn btn-approve" onclick="approve('${rec.id}')">&#10003; Approve</button>
        <button class="btn btn-reject" onclick="reject('${rec.id}')">&#10007; Reject</button>
      </div>
      <div class="confirm-msg" id="msg-${rec.id}"></div>
      ` : ''}
    </div>
  </div>`;
}

function toggleRec(id) {
  document.getElementById('rec-' + id)?.classList.toggle('open');
}

async function approve(id) {
  const qty = document.getElementById('qty-' + id)?.value;
  const msg = document.getElementById('msg-' + id);
  try {
    const r = await fetch('/api/approve', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({rec_id: id, qty: qty ? parseFloat(qty) : null})
    });
    const d = await r.json();
    if (d.ok) {
      msg.textContent = 'APPROVED — Token: ' + d.token.slice(0,12) + '...  Trade queued for execution.';
      msg.className = 'confirm-msg show ok';
      setTimeout(loadPending, 1000);
    } else {
      msg.textContent = 'Error: ' + d.error;
      msg.className = 'confirm-msg show err';
    }
  } catch(e) {
    const m = document.getElementById('msg-' + id);
    m.textContent = 'Error: ' + e.message;
    m.className = 'confirm-msg show err';
  }
}

async function reject(id) {
  const msg = document.getElementById('msg-' + id);
  try {
    await fetch('/api/reject', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({rec_id: id, reason: 'Rejected by user'})
    });
    msg.textContent = 'Rejected.';
    msg.className = 'confirm-msg show err';
    setTimeout(loadPending, 1000);
  } catch(e) {}
}

// ── HISTORY ───────────────────────────────────────────────
async function loadHistory() {
  const tbody = document.getElementById('history-body');
  try {
    const r = await fetch('/api/history');
    const d = await r.json();
    if (!d.length) {
      tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:40px;color:var(--muted)">No trades yet</td></tr>';
      return;
    }
    tbody.innerHTML = d.slice(0,100).map(t => {
      const isPaper = t.mode === 'PAPER';
      const glNum = parseFloat(t.gain_loss || 0);
      const glCls = glNum >= 0 ? 'pos-pl-pos' : 'pos-pl-neg';
      const glStr = t.side === 'SELL' ? fmt(t.gain_loss) : '—';
      return `<tr style="${isPaper ? 'color:var(--blue);opacity:.7' : ''}">
        <td>${t.date_time?.slice(0,10)}</td>
        <td>${t.exchange}</td>
        <td><span style="font-family:var(--mono);font-size:11px;padding:2px 8px;border-radius:4px;
          background:${isPaper?'rgba(0,170,255,.1)':'rgba(0,217,126,.1)'};
          color:${isPaper?'var(--blue)':'var(--green)'}">${t.mode}</span></td>
        <td style="font-weight:600">${t.symbol}</td>
        <td style="color:${t.side==='BUY'?'var(--green)':'var(--red)'};font-weight:600">${t.side}</td>
        <td>${fmtNum(t.quantity)}</td>
        <td>${fmt(t.price)}</td>
        <td>${fmt(t.total_value)}</td>
        <td class="${glCls}">${glStr}</td>
        <td><span style="font-size:11px;font-family:var(--mono)">${t.term||'—'}</span></td>
      </tr>`;
    }).join('');
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="10" style="padding:40px;text-align:center;color:var(--red)">Error: ${e.message}</td></tr>`;
  }
}

// ── TAX ───────────────────────────────────────────────────
async function loadTax() {
  const year = document.getElementById('tax-year').value;
  const box  = document.getElementById('tax-content');
  box.innerHTML = '<div style="color:var(--text2);font-family:var(--mono);padding:20px">Generating...</div>';
  try {
    const r = await fetch('/api/tax?year=' + year);
    const d = await r.json();
    if (d.error) { box.innerHTML = `<div class="empty"><h3>NO DATA</h3><p>${d.error}</p></div>`; return; }
    box.innerHTML = `
      <div class="tax-card">
        <div class="tax-line"><span class="lbl">Tax Year</span><span class="val gold">${d.year}</span></div>
        <div class="tax-line"><span class="lbl">Total Trades (Live)</span><span class="val">${d.total_trades}</span></div>
        <div class="tax-line"><span class="lbl">Total Fees Paid</span><span class="val red">${fmt(d.total_fees_usd)}</span></div>
        <div class="tax-line"><span class="lbl">Short-Term Gains/Losses</span>
          <span class="val ${parseFloat(d.short_term_gain)>=0?'green':'red'}">${fmt(d.short_term_gain)}</span></div>
        <div class="tax-line"><span class="lbl">Long-Term Gains/Losses</span>
          <span class="val ${parseFloat(d.long_term_gain)>=0?'green':'red'}">${fmt(d.long_term_gain)}</span></div>
        <div class="tax-line" style="border-top:2px solid var(--border)">
          <span class="lbl" style="font-weight:600">TOTAL CAPITAL GAINS</span>
          <span class="val gold" style="font-size:20px">${fmt(d.total_gain)}</span>
        </div>
      </div>
      <div style="font-family:var(--mono);font-size:11px;color:var(--muted);line-height:1.8">
        ${d.disclaimer || ''}
      </div>
      <div style="margin-top:16px;font-family:var(--mono);font-size:12px;color:var(--text2)">
        ${d.sells?.length || 0} sell transaction(s) found. 
        Click "Download Form 8949 CSV" above to get the file for your tax preparer.
      </div>`;
  } catch(e) {
    box.innerHTML = `<div class="empty"><h3>ERROR</h3><p>${e.message}</p></div>`;
  }
}

async function download8949() {
  const year = document.getElementById('tax-year').value;
  const r = await fetch('/api/form8949?year=' + year);
  const d = await r.json();
  if (d.path) {
    alert('Form 8949 CSV saved to:\n' + d.path + '\n\nShare this file with your tax preparer.');
  }
}

// ── ANALYSIS ──────────────────────────────────────────────
async function runAnalysis() {
  const syms = document.getElementById('analyze-symbols').value.split(',').map(s=>s.trim()).filter(Boolean);
  const ctx  = document.getElementById('analyze-context').value;
  const btn  = document.getElementById('analyze-btn-txt');
  const status = document.getElementById('analyze-status');
  btn.textContent = 'Running... (this takes ~30 seconds)';
  status.textContent = 'Sending to your local Mistral model...';
  try {
    const r = await fetch('/api/analyze', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({symbols: syms, context: ctx})
    });
    const d = await r.json();
    btn.textContent = 'Run AI Analysis';
    status.textContent = `Done! ${d.count} analysis/analyses queued. Going to Pending Approvals...`;
    setTimeout(() => showView('pending'), 1500);
  } catch(e) {
    btn.textContent = 'Run AI Analysis';
    status.textContent = 'Error: ' + e.message;
  }
}

// Init
loadPortfolio();
setInterval(loadPending, 30000);
</script>
</body></html>"""


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send_json(self, data, code=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path in ('/', '/index.html'):
            body = DASHBOARD_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == '/api/portfolio':
            self.send_json(api_portfolio())
        elif parsed.path == '/api/positions':
            self.send_json(api_positions())
        elif parsed.path == '/api/pending':
            self.send_json(api_pending())
        elif parsed.path == '/api/history':
            self.send_json(api_history())
        elif parsed.path == '/api/tax':
            year = int(qs.get('year', [datetime.now().year])[0])
            self.send_json(api_tax(year))
        elif parsed.path == '/api/form8949':
            year = int(qs.get('year', [datetime.now().year])[0])
            self.send_json(api_form8949(year))
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        if self.path == '/api/approve':
            self.send_json(api_approve(body))
        elif self.path == '/api/reject':
            self.send_json(api_reject(body))
        elif self.path == '/api/analyze':
            self.send_json(api_analyze(body))
        else:
            self.send_response(404); self.end_headers()


# ── API HANDLERS ───────────────────────────────────────────

def api_portfolio():
    try:
        from trading_bridge import AlpacaBridge
        b = AlpacaBridge(); b.connect()
        return b.account()
    except Exception as e:
        return {'error': str(e)}

def api_positions():
    try:
        from trading_bridge import AlpacaBridge
        b = AlpacaBridge(); b.connect()
        return b.positions()
    except Exception as e:
        return []

def api_pending():
    queue = BASE / 'approval_queue' / 'pending.json'
    if not queue.exists(): return {}
    with open(queue) as f: return json.load(f)

def api_history():
    try:
        from tax_ledger import TaxLedger
        return TaxLedger().all_trades_df(paper=True)
    except Exception as e:
        return []

def api_tax(year):
    try:
        from tax_ledger import TaxLedger
        return TaxLedger().annual_summary(year)
    except Exception as e:
        return {'error': str(e)}

def api_form8949(year):
    try:
        from tax_ledger import TaxLedger
        path = TaxLedger().form_8949_csv(year)
        return {'path': path}
    except Exception as e:
        return {'error': str(e)}

def api_approve(body):
    try:
        from ai_analyst import AIAnalyst
        analyst = AIAnalyst()
        token = analyst.approve(body['rec_id'], override_qty=body.get('qty'))
        return {'ok': True, 'token': token}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def api_reject(body):
    try:
        from ai_analyst import AIAnalyst
        AIAnalyst().reject(body['rec_id'], body.get('reason', ''))
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def api_analyze(body):
    try:
        from ai_analyst import AIAnalyst
        results = AIAnalyst().analyze_watchlist(body.get('symbols', []))
        return {'ok': True, 'count': len(results)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# ── MAIN ───────────────────────────────────────────────────
if __name__ == '__main__':
    server = http.server.HTTPServer(('127.0.0.1', PORT), DashboardHandler)
    print(f"\n{'='*56}")
    print(f"  MEEKO TRADING DASHBOARD")
    print(f"{'='*56}")
    print(f"  http://localhost:{PORT}")
    print(f"  Ctrl+C to stop\n")
    threading.Timer(1.2, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Dashboard closed.")
