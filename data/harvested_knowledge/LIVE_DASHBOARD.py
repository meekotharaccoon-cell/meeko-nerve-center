"""
MEEKO MYCELIUM — LIVE DASHBOARD
=================================
http://localhost:7779

Real-time view of YOUR entire system working.
Auto-refreshes every 15 seconds.

Shows:
  - All exchange connections (Alpaca, Coinbase, Kraken, Phantom, pump.fun)
  - Gaza Rose Gallery revenue (Gumroad, PayPal, Stripe, Coinbase Commerce)
  - Active GitHub Actions runs on your conductor + agent repos
  - AI analyst queue (pending recommendations)
  - Recent trades (paper + live)
  - PCRF donation tracker (70% of revenue)
  - Ollama / local AI status
  - System health (all components)
  - MCP server connections available to your agent
"""

import http.server
import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path

DESKTOP  = Path(r'C:\Users\meeko\Desktop')
DB_PATH  = DESKTOP / 'UltimateAI_Master' / 'gaza_rose.db'
INV_DB   = DB_PATH   # same DB for everything
PORT     = 7779
REPOS    = [
    'meekotharaccoon-cell/atomic-agents-conductor',
    'meekotharaccoon-cell/atomic-agents',
    'meekotharaccoon-cell/atomic-agents-staging',
    'meekotharaccoon-cell/atomic-agents-demo',
]
PCRF_LINK = 'https://give.pcrf.net/campaign/739651/donate'

# ── CACHED STATE (updated every 15s by background thread) ─
_state = {
    'last_update': None,
    'exchanges': {},
    'revenue': {},
    'github': {},
    'analyst': {},
    'trades': [],
    'pcrf': {},
    'system': {},
    'mcp': {},
    'pumpfun': {},
}
_lock = threading.Lock()

# ── HTML ─────────────────────────────────────────────────
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Meeko Mycelium — Live Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Outfit:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
:root {
  --ink:   #070b0f;
  --panel: #0d1520;
  --glass: rgba(255,255,255,0.03);
  --b:     #152030;
  --green: #00ff88;
  --gold:  #ffc800;
  --rose:  #ff3366;
  --blue:  #38bdf8;
  --purple:#b57aff;
  --text:  #cce0f0;
  --muted: #3a5060;
  --mono:  'Share Tech Mono', monospace;
  --sans:  'Outfit', sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin:0; padding:0; }
html { background: var(--ink); }
body {
  background: var(--ink); color: var(--text);
  font-family: var(--sans); min-height: 100vh;
  overflow-x: hidden;
}

/* TOP BAR */
.topbar {
  display: flex; align-items: center; gap: 0;
  background: rgba(13,21,32,0.95); border-bottom: 1px solid var(--b);
  padding: 0 28px; height: 54px; position: sticky; top: 0; z-index: 100;
  backdrop-filter: blur(10px);
}
.brand {
  font-family: var(--mono); font-size: 13px; letter-spacing: 2px;
  color: var(--green); margin-right: 28px;
}
.brand em { color: var(--muted); font-style: normal; }
.pulse {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--green); margin-right: 8px;
  box-shadow: 0 0 8px var(--green);
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.7)} }
.live-badge {
  font-family: var(--mono); font-size: 10px; letter-spacing: 2px;
  color: var(--green); text-transform: uppercase;
}
.last-update {
  margin-left: auto; font-family: var(--mono); font-size: 10px;
  color: var(--muted); letter-spacing: 1px;
}
.portal-links { display: flex; gap: 8px; margin-left: 20px; }
.portal-link {
  font-family: var(--mono); font-size: 10px; letter-spacing: 1px;
  padding: 4px 12px; border-radius: 6px; text-decoration: none;
  border: 1px solid var(--b); color: var(--muted); transition: .2s;
  text-transform: uppercase;
}
.portal-link:hover { border-color: var(--green); color: var(--green); }

/* GRID */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px; padding: 20px 24px;
  max-width: 1600px; margin: 0 auto;
}
.card {
  background: var(--panel); border: 1px solid var(--b);
  border-radius: 14px; overflow: hidden;
  transition: border-color .3s;
}
.card:hover { border-color: rgba(0,255,136,.2); }
.card-hdr {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px 12px;
  border-bottom: 1px solid var(--b);
}
.card-title {
  font-family: var(--mono); font-size: 10px; letter-spacing: 2px;
  text-transform: uppercase; color: var(--muted);
  display: flex; align-items: center; gap: 8px;
}
.card-title .dot {
  width: 6px; height: 6px; border-radius: 50%;
}
.dot-green  { background: var(--green); box-shadow: 0 0 6px var(--green); }
.dot-gold   { background: var(--gold);  box-shadow: 0 0 6px var(--gold); }
.dot-rose   { background: var(--rose);  box-shadow: 0 0 6px var(--rose); }
.dot-blue   { background: var(--blue);  box-shadow: 0 0 6px var(--blue); }
.dot-purple { background: var(--purple);box-shadow: 0 0 6px var(--purple); }
.dot-grey   { background: var(--muted); }
.card-badge {
  font-family: var(--mono); font-size: 9px; letter-spacing: 1px;
  padding: 2px 8px; border-radius: 99px; text-transform: uppercase;
}
.badge-ok   { background: rgba(0,255,136,.1);  color: var(--green); border: 1px solid rgba(0,255,136,.2); }
.badge-warn { background: rgba(255,200,0,.1);   color: var(--gold);  border: 1px solid rgba(255,200,0,.2); }
.badge-err  { background: rgba(255,51,102,.1);  color: var(--rose);  border: 1px solid rgba(255,51,102,.2); }
.badge-off  { background: rgba(255,255,255,.04); color: var(--muted); border: 1px solid var(--b); }
.card-body { padding: 16px 18px; }

/* METRIC ROWS */
.metric {
  display: flex; justify-content: space-between; align-items: center;
  padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,0.03);
}
.metric:last-child { border: none; }
.metric-lbl { font-size: 12px; color: var(--muted); font-family: var(--mono); }
.metric-val { font-family: var(--mono); font-size: 13px; font-weight: 500; }
.v-green  { color: var(--green); }
.v-gold   { color: var(--gold); }
.v-rose   { color: var(--rose); }
.v-blue   { color: var(--blue); }
.v-purple { color: var(--purple); }
.v-muted  { color: var(--muted); }

/* GITHUB RUNS */
.run-item {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.03);
  font-size: 11px;
}
.run-item:last-child { border: none; }
.run-status {
  width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
}
.rs-success   { background: var(--green); }
.rs-in_progress { background: var(--gold); animation: pulse 1s infinite; }
.rs-failure   { background: var(--rose); }
.rs-queued    { background: var(--muted); }
.rs-cancelled { background: var(--muted); }
.run-name  { flex: 1; color: var(--text); }
.run-repo  { color: var(--muted); font-size: 10px; }
.run-time  { color: var(--muted); font-size: 10px; font-family: var(--mono); }

/* TRADE LIST */
.trade-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.03);
  font-size: 11px; font-family: var(--mono);
}
.trade-item:last-child { border: none; }
.t-buy  { color: var(--green); font-weight: 700; }
.t-sell { color: var(--rose);  font-weight: 700; }
.t-ticker { color: var(--text); flex: 1; }
.t-price  { color: var(--gold); }
.t-paper  { color: var(--muted); font-size: 9px; }

/* PENDING RECS */
.rec-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03);
}
.rec-item:last-child { border: none; }
.rec-action {
  font-family: var(--mono); font-size: 10px; font-weight: 700;
  padding: 2px 8px; border-radius: 4px;
}
.ra-BUY   { background: rgba(0,255,136,.1);  color: var(--green); }
.ra-SELL  { background: rgba(255,51,102,.1);  color: var(--rose); }
.ra-HOLD  { background: rgba(56,189,248,.1);  color: var(--blue); }
.ra-AVOID { background: rgba(255,51,102,.15); color: var(--rose); }
.rec-ticker { font-family: var(--mono); font-size: 13px; font-weight: 600; flex: 1; }
.rec-conf   { font-family: var(--mono); font-size: 10px; color: var(--muted); }

/* PCRF BIG NUMBER */
.pcrf-total {
  text-align: center; padding: 10px 0 16px;
}
.pcrf-total .big {
  font-size: 42px; font-weight: 900; color: var(--green);
  font-family: var(--mono); line-height: 1;
}
.pcrf-total .sub {
  font-size: 11px; color: var(--muted); margin-top: 5px;
  font-family: var(--mono); letter-spacing: 1px;
}
.pcrf-donate {
  display: block; text-align: center; margin-top: 12px;
  background: rgba(0,255,136,0.08); border: 1px solid rgba(0,255,136,0.25);
  color: var(--green); text-decoration: none; padding: 8px 16px;
  border-radius: 8px; font-family: var(--mono); font-size: 11px;
  letter-spacing: 1px; transition: .2s;
}
.pcrf-donate:hover { background: rgba(0,255,136,0.15); }

/* MCP CHIPS */
.mcp-grid {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 4px 0;
}
.mcp-chip {
  font-family: var(--mono); font-size: 10px; letter-spacing: .5px;
  padding: 4px 10px; border-radius: 6px; border: 1px solid var(--b);
  color: var(--muted); transition: .2s;
}
.mcp-chip.active { border-color: rgba(0,255,136,.3); color: var(--green); background: rgba(0,255,136,.05); }
.mcp-chip.warn   { border-color: rgba(255,200,0,.3);  color: var(--gold); }

/* PUMP FUN */
.pf-token {
  display: flex; align-items: center; gap: 10px;
  padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,0.03);
  font-size: 11px;
}
.pf-token:last-child { border: none; }
.pf-name  { flex: 1; color: var(--text); font-family: var(--mono); font-size: 12px; }
.pf-price { color: var(--gold); font-family: var(--mono); }
.pf-chg.pos { color: var(--green); font-family: var(--mono); font-size: 10px; }
.pf-chg.neg { color: var(--rose);  font-family: var(--mono); font-size: 10px; }

/* SYSTEM HEALTH ROW */
.health-row {
  display: flex; flex-wrap: wrap; gap: 8px; padding: 4px 0;
}
.health-chip {
  font-family: var(--mono); font-size: 10px; letter-spacing: .5px;
  padding: 4px 10px; border-radius: 6px;
}
.hc-ok  { background: rgba(0,255,136,.08); border:1px solid rgba(0,255,136,.2); color: var(--green); }
.hc-err { background: rgba(255,51,102,.08); border:1px solid rgba(255,51,102,.2); color: var(--rose); }
.hc-warn{ background: rgba(255,200,0,.08);  border:1px solid rgba(255,200,0,.2);  color: var(--gold); }

/* SPINNER */
@keyframes spin { to{transform:rotate(360deg)} }
.spin { display:inline-block; width:12px; height:12px; border:1.5px solid transparent; border-top-color:currentColor; border-radius:50%; animation:spin .7s linear infinite; }

/* EMPTY */
.empty-msg { color: var(--muted); font-family: var(--mono); font-size: 11px; padding: 12px 0; text-align:center; }
</style>
</head>
<body>

<div class="topbar">
  <div class="brand">MEEKO <em>/</em> MYCELIUM</div>
  <div class="pulse"></div>
  <div class="live-badge">Live</div>
  <div class="portal-links">
    <a class="portal-link" href="http://localhost:7778" target="_blank">Invest</a>
    <a class="portal-link" href="http://localhost:7776" target="_blank">Setup</a>
    <a class="portal-link" href="http://localhost:7777" target="_blank">Wizard</a>
    <a class="portal-link" href="PLACEHOLDER_GALLERY" target="_blank">Gallery</a>
  </div>
  <div class="last-update" id="last-update">Loading...</div>
</div>

<div class="grid" id="grid">
  <div class="card">
    <div class="card-hdr">
      <div class="card-title"><div class="dot dot-green"></div>Loading system state...</div>
    </div>
    <div class="card-body">
      <div class="empty-msg"><span class="spin"></span> Connecting to all services...</div>
    </div>
  </div>
</div>

<script>
let lastData = null;

async function refresh() {
  try {
    const r = await fetch('/state');
    const d = await r.json();
    lastData = d;
    render(d);
    document.getElementById('last-update').textContent =
      'Updated ' + new Date().toLocaleTimeString();
  } catch(e) {
    document.getElementById('last-update').textContent = 'Reconnecting...';
  }
}

function card(title, dotClass, badge, badgeClass, body) {
  return `<div class="card">
    <div class="card-hdr">
      <div class="card-title"><div class="dot ${dotClass}"></div>${title}</div>
      <div class="card-badge ${badgeClass}">${badge}</div>
    </div>
    <div class="card-body">${body}</div>
  </div>`;
}

function metric(lbl, val, cls='') {
  return `<div class="metric"><div class="metric-lbl">${lbl}</div><div class="metric-val ${cls}">${val}</div></div>`;
}

function render(d) {
  const ex = d.exchanges || {};
  const rev = d.revenue || {};
  const gh = d.github || {};
  const an = d.analyst || {};
  const trades = d.trades || [];
  const pcrf = d.pcrf || {};
  const sys = d.system || {};
  const mcp = d.mcp || {};
  const pf = d.pumpfun || {};

  let cards = '';

  // ── EXCHANGES ────────────────────────────────────────
  // Alpaca
  const alp = ex.alpaca || {};
  cards += card('Alpaca Markets', 'dot-blue',
    alp.ok ? 'Connected' : alp.skipped ? 'Not Set' : 'Offline',
    alp.ok ? 'badge-ok' : 'badge-off',
    alp.ok ? `
      ${metric('Account', alp.account_number || '...', 'v-muted')}
      ${metric('Equity', '$' + (alp.equity||0).toFixed(2), 'v-green')}
      ${metric('Buying Power', '$' + (alp.buying_power||0).toFixed(2), 'v-blue')}
      ${metric('Open Positions', alp.positions || 0, 'v-gold')}
      ${metric('Mode', alp.paper ? 'PAPER (safe)' : '⚡ LIVE', alp.paper ? 'v-muted' : 'v-rose')}
    ` : '<div class="empty-msg">Not connected — run Grand Setup Wizard</div>'
  );

  // Coinbase
  const cb = ex.coinbase || {};
  cards += card('Coinbase Advanced', 'dot-blue',
    cb.ok ? 'Connected' : 'Not Set',
    cb.ok ? 'badge-ok' : 'badge-off',
    cb.ok ? `
      ${(cb.balances||[]).map(b =>
        metric(b.currency, parseFloat(b.value).toFixed(6), parseFloat(b.value) > 0 ? 'v-green' : 'v-muted')
      ).join('') || '<div class="empty-msg">No balances yet</div>'}
    ` : '<div class="empty-msg">Not connected</div>'
  );

  // Kraken
  const kr = ex.kraken || {};
  cards += card('Kraken', 'dot-purple',
    kr.ok ? 'Connected' : 'Not Set',
    kr.ok ? 'badge-ok' : 'badge-off',
    kr.ok ? `
      ${Object.entries(kr.balances||{}).slice(0,6).map(([k,v]) =>
        metric(k, parseFloat(v).toFixed(6), parseFloat(v) > 0 ? 'v-green' : 'v-muted')
      ).join('') || '<div class="empty-msg">No balances</div>'}
    ` : '<div class="empty-msg">Not connected</div>'
  );

  // Phantom / Solana
  const ph = ex.phantom || {};
  cards += card('Phantom / Solana', 'dot-purple',
    ph.ok ? 'Verified' : 'Not Set',
    ph.ok ? 'badge-ok' : 'badge-off',
    ph.ok ? `
      ${metric('Address', ph.short_address || '...', 'v-purple')}
      ${metric('SOL Balance', (ph.sol_balance||0).toFixed(6) + ' SOL', 'v-green')}
      ${metric('USD Est.', '$' + (ph.sol_usd||0).toFixed(2), 'v-gold')}
      ${metric('Network', 'Mainnet-Beta', 'v-muted')}
    ` : '<div class="empty-msg">Add your Phantom address in Grand Setup Wizard</div>'
  );

  // pump.fun (read-only Solana trending)
  const pfTokens = pf.tokens || [];
  cards += card('pump.fun (Solana / Read)', 'dot-gold',
    pf.ok ? 'Monitoring' : 'Public RPC',
    'badge-warn',
    pfTokens.length ? `
      ${pfTokens.map(t => `
        <div class="pf-token">
          <div class="pf-name">${t.symbol || '???'}</div>
          <div class="pf-price">${t.price || 'N/A'}</div>
          <div class="pf-chg ${(t.change||0) >= 0 ? 'pos' : 'neg'}">${t.change !== undefined ? (t.change >= 0 ? '+' : '') + t.change + '%' : ''}</div>
        </div>`).join('')}
      <div style="font-size:10px;color:var(--muted);font-family:var(--mono);margin-top:8px">Read-only · Approval required for any trades</div>
    ` : '<div class="empty-msg">Fetching Solana token data via public RPC...</div>'
  );

  // ── REVENUE ──────────────────────────────────────────
  const gumroad = rev.gumroad || {};
  cards += card('Gumroad Sales', 'dot-green',
    gumroad.ok ? 'Connected' : 'Not Set',
    gumroad.ok ? 'badge-ok' : 'badge-off',
    gumroad.ok ? `
      ${metric('Products', gumroad.product_count || 0, 'v-green')}
      ${metric('Sales (all time)', gumroad.total_sales || 0, 'v-gold')}
      ${metric('Revenue', '$' + (gumroad.total_revenue||0).toFixed(2), 'v-green')}
      ${metric('PCRF 70%', '$' + ((gumroad.total_revenue||0) * 0.7).toFixed(2), 'v-rose')}
    ` : '<div class="empty-msg">Not connected</div>'
  );

  const stripe = rev.stripe || {};
  cards += card('Stripe', 'dot-blue',
    stripe.ok ? 'Connected' : 'Not Set',
    stripe.ok ? 'badge-ok' : 'badge-off',
    stripe.ok ? `
      ${metric('Available Balance', '$' + (stripe.available||0).toFixed(2), 'v-green')}
      ${metric('Pending', '$' + (stripe.pending||0).toFixed(2), 'v-gold')}
      ${metric('Currency', stripe.currency || 'USD', 'v-muted')}
    ` : '<div class="empty-msg">Not connected — get key at dashboard.stripe.com</div>'
  );

  const paypal = rev.paypal || {};
  cards += card('PayPal', 'dot-blue',
    paypal.ok ? 'Connected' : 'Not Set',
    paypal.ok ? 'badge-ok' : 'badge-off',
    paypal.ok ? `
      ${metric('Status', 'Live API', 'v-green')}
      ${metric('Token', paypal.token_ok ? 'Valid' : 'Expired', paypal.token_ok ? 'v-green' : 'v-rose')}
    ` : '<div class="empty-msg">Not connected — get key at developer.paypal.com</div>'
  );

  const commerce = rev.commerce || {};
  cards += card('Coinbase Commerce', 'dot-blue',
    commerce.ok ? 'Connected' : 'Not Set',
    commerce.ok ? 'badge-ok' : 'badge-off',
    commerce.ok ? `
      ${metric('Checkouts', commerce.checkout_count || 0, 'v-green')}
      ${metric('Accepts', 'BTC · ETH · USDC · SOL · DOGE', 'v-muted')}
    ` : '<div class="empty-msg">Not connected</div>'
  );

  // ── AI ANALYST ────────────────────────────────────────
  const pending = an.pending || [];
  cards += card('AI Analyst Queue', 'dot-gold',
    pending.length + ' Pending',
    pending.length > 0 ? 'badge-warn' : 'badge-ok',
    `${metric('Pending Approval', pending.length, pending.length > 0 ? 'v-gold' : 'v-green')}
    ${metric('Watchlist Size', an.watchlist_size || 0, 'v-blue')}
    ${metric('Local Model', an.model || 'mistral', 'v-muted')}
    ${pending.slice(0,4).map(r => `
      <div class="rec-item">
        <div class="rec-action ra-${r.action}">${r.action}</div>
        <div class="rec-ticker">${r.ticker}</div>
        <div class="rec-conf">${Math.round((r.confidence||0.5)*100)}% · ${r.risk_level||'?'}</div>
      </div>`).join('')}
    ${pending.length > 0 ? '<a href="http://localhost:7778" target="_blank" style="display:block;margin-top:10px;text-align:center;font-family:var(--mono);font-size:10px;color:var(--green);text-decoration:none;letter-spacing:1px">REVIEW IN APPROVAL PORTAL →</a>' : ''}`
  );

  // ── RECENT TRADES ─────────────────────────────────────
  cards += card('Recent Trades', 'dot-green',
    trades.length + ' trades',
    'badge-ok',
    trades.length ? `
      ${trades.slice(0,6).map(t => `
        <div class="trade-item">
          <div class="${t.action==='BUY'?'t-buy':'t-sell'}">${t.action}</div>
          <div class="t-ticker">${t.ticker}</div>
          <div class="t-price">$${parseFloat(t.price||0).toFixed(4)}</div>
          <div class="t-paper">${t.paper_trade ? 'PAPER' : 'LIVE'}</div>
        </div>`).join('')}
    ` : '<div class="empty-msg">No trades yet — approve a recommendation to begin</div>'
  );

  // ── GITHUB CONDUCTOR ─────────────────────────────────
  const runs = gh.runs || [];
  cards += card('GitHub Conductor', 'dot-purple',
    runs.filter(r => r.status==='in_progress').length > 0 ? 'Running' : 'Watching',
    runs.filter(r => r.status==='in_progress').length > 0 ? 'badge-warn' : 'badge-ok',
    runs.length ? `
      ${metric('Active Runs', runs.filter(r=>r.status==='in_progress').length, 'v-gold')}
      ${metric('Recent Runs', runs.length, 'v-muted')}
      ${runs.slice(0,5).map(r => `
        <div class="run-item">
          <div class="run-status rs-${r.conclusion||r.status}"></div>
          <div class="run-name">${r.name||'run'}</div>
          <div class="run-repo">${r.repo||''}</div>
          <div class="run-time">${r.ago||''}</div>
        </div>`).join('')}
    ` : '<div class="empty-msg">No recent workflow runs</div>'
  );

  // ── PCRF TRACKER ─────────────────────────────────────
  const totalRevenue = (gumroad.total_revenue||0) + (stripe.available||0);
  const pcrf_owed    = totalRevenue * 0.7;
  const pcrf_donated = pcrf.total_donated || 0;
  cards += card('PCRF Donation Tracker', 'dot-rose',
    '70% of all revenue',
    'badge-ok',
    `<div class="pcrf-total">
      <div class="big">$${pcrf_owed.toFixed(2)}</div>
      <div class="sub">TOTAL OWED TO PCRF</div>
    </div>
    ${metric('Total Revenue', '$' + totalRevenue.toFixed(2), 'v-green')}
    ${metric('70% Owed', '$' + pcrf_owed.toFixed(2), 'v-rose')}
    ${metric('Donated So Far', '$' + pcrf_donated.toFixed(2), 'v-gold')}
    ${metric('Remaining', '$' + Math.max(0, pcrf_owed - pcrf_donated).toFixed(2), 'v-rose')}
    <a class="pcrf-donate" href="${PCRF_LINK}" target="_blank">Donate Now → give.pcrf.net</a>`
  );

  // ── MCP SERVERS ───────────────────────────────────────
  const mcpStatus = mcp.servers || {};
  const PCRF_LINK_JS = 'https://give.pcrf.net/campaign/739651/donate';
  cards += card('MCP Connections', 'dot-purple',
    'Model Context Protocol',
    'badge-ok',
    `<div class="mcp-grid">
      <div class="mcp-chip ${mcpStatus.phantom?'active':''}">phantom-docs</div>
      <div class="mcp-chip ${mcpStatus.github?'active':''}">github</div>
      <div class="mcp-chip ${mcpStatus.filesystem?'active':''}">filesystem</div>
      <div class="mcp-chip ${mcpStatus.memory?'active':''}">memory</div>
      <div class="mcp-chip ${mcpStatus.sqlite?'active':''}">sqlite/gazarose</div>
      <div class="mcp-chip ${mcpStatus.stripe?'active':''}">stripe</div>
      <div class="mcp-chip ${mcpStatus.paypal?'warn':''}">paypal-agent</div>
      <div class="mcp-chip warn">coinbase</div>
      <div class="mcp-chip ${mcpStatus.alpaca?'active':''}">alpaca-data</div>
      <div class="mcp-chip warn">solana-rpc</div>
    </div>
    <div style="margin-top:12px;font-family:var(--mono);font-size:10px;color:var(--muted);line-height:1.8">
      MCP lets your agent call any connected service.<br>
      Active = config in Claude Desktop claude_desktop_config.json
    </div>`
  );

  // ── SYSTEM HEALTH ─────────────────────────────────────
  const components = sys.components || {};
  cards += card('System Health', 'dot-green',
    sys.all_ok ? 'All OK' : 'Check needed',
    sys.all_ok ? 'badge-ok' : 'badge-warn',
    `<div class="health-row">
      ${Object.entries(components).map(([k,v]) =>
        `<div class="health-chip ${v?'hc-ok':'hc-err'}">${k}</div>`
      ).join('')}
    </div>
    ${metric('Ollama', sys.ollama ? 'Running' : 'Offline', sys.ollama ? 'v-green' : 'v-rose')}
    ${metric('Gaza Rose DB', sys.db ? 'Connected' : 'Error', sys.db ? 'v-green' : 'v-rose')}
    ${metric('Gallery', sys.gallery_count + ' artworks', 'v-green')}
    ${metric('Paper Mode', sys.paper_mode ? 'ON (safe)' : 'LIVE', sys.paper_mode ? 'v-gold' : 'v-rose')}
    ${metric('Uptime', sys.uptime || '...', 'v-muted')}`
  );

  document.getElementById('grid').innerHTML = cards;
}

refresh();
setInterval(refresh, 15000);
</script>
</body>
</html>"""

PCRF_LINK_REPLACE = 'https://give.pcrf.net/campaign/739651/donate'
GALLERY_PLACEHOLDER = str(DESKTOP / 'GAZA_ROSE_GALLERY' / 'index.html')

# ── STATE COLLECTORS ──────────────────────────────────────
_start_time = time.time()

def collect_all():
    state = {
        'last_update': datetime.now().isoformat(),
        'exchanges': collect_exchanges(),
        'revenue':   collect_revenue(),
        'github':    collect_github(),
        'analyst':   collect_analyst(),
        'trades':    collect_trades(),
        'pcrf':      collect_pcrf(),
        'system':    collect_system(),
        'mcp':       collect_mcp(),
        'pumpfun':   collect_pumpfun(),
    }
    return state

def _db():
    return sqlite3.connect(str(DB_PATH))

def collect_exchanges():
    result = {}

    # Alpaca (paper)
    try:
        alpaca_key    = _read_secret('ALPACA_KEY')
        alpaca_secret = _read_secret('ALPACA_SECRET')
        if alpaca_key and alpaca_secret:
            req = urllib.request.Request(
                'https://paper-api.alpaca.markets/v2/account',
                headers={'APCA-API-KEY-ID': alpaca_key, 'APCA-API-SECRET-KEY': alpaca_secret}
            )
            data = json.loads(urllib.request.urlopen(req, timeout=10).read())
            positions_req = urllib.request.Request(
                'https://paper-api.alpaca.markets/v2/positions',
                headers={'APCA-API-KEY-ID': alpaca_key, 'APCA-API-SECRET-KEY': alpaca_secret}
            )
            positions = json.loads(urllib.request.urlopen(positions_req, timeout=10).read())
            result['alpaca'] = {
                'ok': True, 'paper': True,
                'account_number': data.get('account_number','')[:8]+'...',
                'equity': float(data.get('equity',0)),
                'buying_power': float(data.get('buying_power',0)),
                'positions': len(positions),
            }
        else:
            result['alpaca'] = {'ok': False, 'skipped': True}
    except Exception as e:
        result['alpaca'] = {'ok': False, 'error': str(e)[:80]}

    # Coinbase
    try:
        cb_key = _read_secret('CB_API_KEY')
        cb_sec = _read_secret('CB_API_SECRET')
        if cb_key and cb_sec:
            from coinbase.rest import RESTClient
            client = RESTClient(api_key=cb_key, api_secret=cb_sec)
            accounts = client.get_accounts()
            accts = accounts.accounts if hasattr(accounts, 'accounts') else []
            balances = []
            for a in accts:
                bal = getattr(getattr(a, 'available_balance', None), 'value', '0') or '0'
                if float(bal) > 0:
                    balances.append({'currency': a.currency, 'value': bal})
            result['coinbase'] = {'ok': True, 'balances': balances}
        else:
            result['coinbase'] = {'ok': False}
    except Exception as e:
        result['coinbase'] = {'ok': False, 'error': str(e)[:80]}

    # Kraken
    try:
        kr_key = _read_secret('KRAKEN_API_KEY')
        kr_sec = _read_secret('KRAKEN_API_SECRET')
        if kr_key and kr_sec:
            import ccxt
            ex = ccxt.kraken({'apiKey': kr_key, 'secret': kr_sec})
            bal = ex.fetch_balance()
            non_zero = {k: str(v) for k,v in bal.get('total',{}).items() if v and float(v) > 0}
            result['kraken'] = {'ok': True, 'balances': non_zero}
        else:
            result['kraken'] = {'ok': False}
    except Exception as e:
        result['kraken'] = {'ok': False, 'error': str(e)[:80]}

    # Phantom / Solana
    try:
        addr = _read_secret('PHANTOM_SOLANA_ADDRESS')
        if not addr:
            # Try DB fallback
            try:
                conn = _db()
                row = conn.execute("SELECT value FROM crypto_config WHERE key='phantom_address'").fetchone()
                conn.close()
                if row: addr = row[0]
            except: pass
        if addr:
            payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"getBalance","params":[addr]}).encode()
            req = urllib.request.Request('https://api.mainnet-beta.solana.com', data=payload,
                                         headers={'Content-Type':'application/json'})
            data = json.loads(urllib.request.urlopen(req, timeout=10).read())
            sol = data.get('result',{}).get('value',0) / 1_000_000_000
            result['phantom'] = {
                'ok': True,
                'short_address': f"{addr[:8]}...{addr[-6:]}",
                'sol_balance': sol,
                'sol_usd': sol * 170  # rough estimate — yfinance can give real price
            }
        else:
            result['phantom'] = {'ok': False}
    except Exception as e:
        result['phantom'] = {'ok': False, 'error': str(e)[:80]}

    return result

def collect_revenue():
    result = {}

    # Gumroad
    try:
        token = _read_secret('GUMROAD_TOKEN')
        if token:
            req = urllib.request.Request(
                'https://api.gumroad.com/v2/products',
                headers={'Authorization': f'Bearer {token}'}
            )
            data = json.loads(urllib.request.urlopen(req, timeout=10).read())
            products = data.get('products', [])
            total_sales   = sum(p.get('sales_count', 0) for p in products)
            total_revenue = sum(float(p.get('price',0))/100 * p.get('sales_count',0) for p in products)
            result['gumroad'] = {
                'ok': True,
                'product_count': len(products),
                'total_sales': total_sales,
                'total_revenue': total_revenue
            }
        else:
            result['gumroad'] = {'ok': False}
    except Exception as e:
        result['gumroad'] = {'ok': False, 'error': str(e)[:80]}

    # Stripe
    try:
        import stripe as stripe_lib
        sk = _read_secret('STRIPE_SECRET_KEY')
        if sk:
            stripe_lib.api_key = sk
            bal = stripe_lib.Balance.retrieve()
            avail   = bal['available'][0]['amount'] / 100
            pending = bal['pending'][0]['amount'] / 100
            result['stripe'] = {
                'ok': True,
                'available': avail,
                'pending': pending,
                'currency': bal['available'][0]['currency'].upper()
            }
        else:
            result['stripe'] = {'ok': False}
    except Exception as e:
        result['stripe'] = {'ok': False, 'error': str(e)[:80]}

    # PayPal
    try:
        import base64
        pp_id  = _read_secret('PAYPAL_CLIENT_ID')
        pp_sec = _read_secret('PAYPAL_CLIENT_SECRET')
        if pp_id and pp_sec:
            creds = base64.b64encode(f"{pp_id}:{pp_sec}".encode()).decode()
            req = urllib.request.Request(
                'https://api-m.paypal.com/v1/oauth2/token',
                data=b'grant_type=client_credentials',
                headers={'Authorization': f'Basic {creds}', 'Content-Type':'application/x-www-form-urlencoded'}
            )
            data = json.loads(urllib.request.urlopen(req, timeout=10).read())
            result['paypal'] = {'ok': True, 'token_ok': 'access_token' in data}
        else:
            result['paypal'] = {'ok': False}
    except Exception as e:
        result['paypal'] = {'ok': False, 'error': str(e)[:80]}

    # Coinbase Commerce
    try:
        ck = _read_secret('COINBASE_COMMERCE_KEY')
        if ck:
            req = urllib.request.Request(
                'https://api.commerce.coinbase.com/checkouts',
                headers={'X-CC-Api-Key': ck, 'X-CC-Version': '2018-03-22'}
            )
            data = json.loads(urllib.request.urlopen(req, timeout=10).read())
            result['commerce'] = {'ok': True, 'checkout_count': len(data.get('data',[]))}
        else:
            result['commerce'] = {'ok': False}
    except Exception as e:
        result['commerce'] = {'ok': False, 'error': str(e)[:80]}

    return result

def collect_github():
    runs = []
    try:
        for repo in REPOS:
            result = subprocess.run(
                ['gh', 'run', 'list', '--repo', repo, '--limit', '3', '--json',
                 'name,status,conclusion,createdAt,databaseId'],
                capture_output=True, timeout=15
            )
            if result.returncode == 0:
                repo_runs = json.loads(result.stdout)
                for r in repo_runs:
                    created = r.get('createdAt','')
                    try:
                        dt  = datetime.fromisoformat(created.replace('Z','+00:00'))
                        ago = _time_ago(dt)
                    except: ago = ''
                    runs.append({
                        'name':       r.get('name','run'),
                        'status':     r.get('status','unknown'),
                        'conclusion': r.get('conclusion',''),
                        'repo':       repo.split('/')[1],
                        'ago':        ago
                    })
    except Exception as e:
        pass
    return {'runs': runs}

def collect_analyst():
    try:
        conn = _db()
        pending = conn.execute(
            "SELECT id,ticker,action,confidence,risk_level FROM analyses WHERE status='pending_approval' ORDER BY timestamp DESC LIMIT 10"
        ).fetchall()
        watchlist = conn.execute(
            "SELECT COUNT(*) FROM watchlist WHERE active=1"
        ).fetchone()
        conn.close()
        cols = ['id','ticker','action','confidence','risk_level']
        return {
            'pending':       [dict(zip(cols,r)) for r in pending],
            'watchlist_size': (watchlist[0] if watchlist else 0),
            'model':         'mistral'
        }
    except Exception:
        return {'pending': [], 'watchlist_size': 0, 'model': 'mistral'}

def collect_trades():
    try:
        conn = _db()
        rows = conn.execute(
            'SELECT ticker,action,quantity,price,paper_trade,timestamp FROM trades ORDER BY timestamp DESC LIMIT 10'
        ).fetchall()
        conn.close()
        cols = ['ticker','action','quantity','price','paper_trade','timestamp']
        return [dict(zip(cols,r)) for r in rows]
    except Exception:
        return []

def collect_pcrf():
    try:
        conn = _db()
        try:
            conn.execute('CREATE TABLE IF NOT EXISTS pcrf_donations (id INTEGER PRIMARY KEY, amount REAL, date TEXT, note TEXT)')
            row = conn.execute('SELECT SUM(amount) FROM pcrf_donations').fetchone()
            conn.commit()
        except: row = (0,)
        conn.close()
        return {'total_donated': float(row[0] or 0)}
    except Exception:
        return {'total_donated': 0}

def collect_system():
    components = {}

    # Python
    components['Python'] = True

    # Ollama
    try:
        urllib.request.urlopen('http://localhost:11434', timeout=3)
        components['Ollama'] = True
        ollama_ok = True
    except:
        components['Ollama'] = False
        ollama_ok = False

    # Gaza Rose DB
    try:
        conn = _db()
        conn.close()
        components['GazaRoseDB'] = True
        db_ok = True
    except:
        components['GazaRoseDB'] = False
        db_ok = False

    # Gallery
    gallery_path = DESKTOP / 'GAZA_ROSE_GALLERY'
    gallery_count = len(list(gallery_path.glob('art/*.jpg'))) + len(list(gallery_path.glob('art/*.png'))) + len(list(gallery_path.glob('art/*.webp'))) if gallery_path.exists() else 0
    components['Gallery'] = gallery_count > 0

    # Investment HQ
    components['InvestmentHQ'] = (DESKTOP / 'INVESTMENT_HQ' / 'src' / 'ai_analyst.py').exists()

    # Conductor repo
    components['Conductor'] = (DESKTOP / 'atomic-agents-conductor' / '.github').exists()

    uptime_secs = int(time.time() - _start_time)
    uptime = f"{uptime_secs//3600}h {(uptime_secs%3600)//60}m {uptime_secs%60}s"

    return {
        'components': components,
        'all_ok': all(components.values()),
        'ollama': ollama_ok,
        'db': db_ok,
        'gallery_count': gallery_count,
        'paper_mode': True,  # default safe
        'uptime': uptime
    }

def collect_mcp():
    """Check which MCP servers are configured in Claude Desktop."""
    mcp_config = Path(os.environ.get('APPDATA','')) / 'Claude' / 'claude_desktop_config.json'
    servers = {}
    if mcp_config.exists():
        try:
            config = json.loads(mcp_config.read_text())
            configured = config.get('mcpServers', {})
            servers['phantom']    = 'phantom' in str(configured)
            servers['github']     = 'github' in str(configured)
            servers['filesystem'] = 'filesystem' in str(configured)
            servers['memory']     = 'memory' in str(configured)
            servers['sqlite']     = 'sqlite' in str(configured)
            servers['stripe']     = 'stripe' in str(configured)
            servers['paypal']     = 'paypal' in str(configured)
            servers['alpaca']     = 'alpaca' in str(configured)
        except: pass
    return {'servers': servers, 'config_path': str(mcp_config)}

def collect_pumpfun():
    """
    pump.fun is Solana-based — no official REST API.
    We read trending token data via the public DexScreener API
    which indexes Solana/pump.fun tokens.
    """
    try:
        req = urllib.request.Request(
            'https://api.dexscreener.com/token-boosts/top/v1',
            headers={'User-Agent': 'MeekoMycelium/1.0'}
        )
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        tokens = []
        for item in (data if isinstance(data, list) else [])[:5]:
            token_addr = item.get('tokenAddress','')
            chain      = item.get('chainId','')
            if 'solana' in chain.lower():
                tokens.append({
                    'symbol': item.get('description','?')[:10],
                    'price': item.get('url',''),
                    'change': None
                })
        return {'ok': True, 'tokens': tokens}
    except Exception as e:
        return {'ok': False, 'tokens': [], 'error': str(e)[:80]}

# ── HELPERS ───────────────────────────────────────────────
def _read_secret(name: str) -> str:
    """Read secret from env var (set by GitHub Actions / manual export)."""
    return os.environ.get(name, '').strip()

def _time_ago(dt: datetime) -> str:
    try:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        diff = (now - dt).total_seconds()
        if diff < 60:   return f"{int(diff)}s ago"
        if diff < 3600: return f"{int(diff//60)}m ago"
        return f"{int(diff//3600)}h ago"
    except: return ''

def background_collector():
    while True:
        try:
            new_state = collect_all()
            with _lock:
                _state.update(new_state)
        except Exception as e:
            print(f"  [Dashboard] Collect error: {e}")
        time.sleep(15)

# ── HTTP HANDLER ─────────────────────────────────────────
class DashHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _json(self, data, code=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ('/','/index.html'):
            html = DASHBOARD_HTML.replace('PLACEHOLDER_GALLERY',
                   'file:///' + GALLERY_PLACEHOLDER.replace('\\','/'))
            html = html.replace('PCRF_LINK_JS', PCRF_LINK_REPLACE)
            body = html.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type','text/html;charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/state':
            with _lock:
                self._json(_state)
        else:
            self.send_response(404); self.end_headers()

# ── MAIN ─────────────────────────────────────────────────
if __name__ == '__main__':
    print(f"\n{'='*58}")
    print(f"  MEEKO MYCELIUM — LIVE DASHBOARD")
    print(f"{'='*58}")
    print(f"\n  http://localhost:{PORT}")
    print(f"  Auto-refreshes every 15 seconds.")
    print(f"  Shows all exchanges, revenue, trades, AI queue.")
    print(f"  Press Ctrl+C to stop.\n")

    # Prime state immediately
    print("  Collecting initial system state...")
    try:
        initial = collect_all()
        with _lock:
            _state.update(initial)
        print("  State loaded.\n")
    except Exception as e:
        print(f"  Initial collect note: {e}\n")

    # Background refresh thread
    t = threading.Thread(target=background_collector, daemon=True)
    t.start()

    server = http.server.HTTPServer(('127.0.0.1', PORT), DashHandler)
    threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Dashboard closed.\n")
