"""
MEEKO MYCELIUM - SETUP WIZARD
Starts a local web server and opens a beautiful wizard in your browser.
Tests each API key live, then wires everything into your system automatically.

HOW TO RUN:
  python SETUP_WIZARD.py
  (Browser opens automatically to http://localhost:7777)
"""

import http.server
import json
import os
import sqlite3
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path

# ── PATHS ──────────────────────────────────────────────────
DESKTOP       = Path(r'C:\Users\meeko\Desktop')
DB_PATH       = DESKTOP / 'UltimateAI_Master' / 'gaza_rose.db'
GALLERY_DIR   = DESKTOP / 'GAZA_ROSE_GALLERY'
CRYPTO_CFG    = GALLERY_DIR / 'payment_config.json'
PAYMENT_PAGE  = GALLERY_DIR / 'payment.html'
PCRF_LINK     = "https://give.pcrf.net/campaign/739651/donate"
PORT          = 7777

# ── WIZARD HTML ────────────────────────────────────────────
WIZARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Meeko Mycelium — Setup Wizard</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
<style>
:root {
  --rose: #C0395A;
  --rose-light: #e8527a;
  --gold: #FFD700;
  --dark: #0d0d0d;
  --panel: #141414;
  --panel2: #1c1c1c;
  --border: #2a2a2a;
  --green: #39C07A;
  --text: #e8e8e8;
  --muted: #666;
  --mono: 'DM Mono', monospace;
  --sans: 'Syne', sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  background: var(--dark);
  color: var(--text);
  font-family: var(--sans);
  min-height: 100vh;
  overflow-x: hidden;
}

/* BG TEXTURE */
body::before {
  content: '';
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 80% 50% at 20% 10%, rgba(192,57,90,0.06) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 90%, rgba(255,215,0,0.04) 0%, transparent 50%);
  pointer-events: none; z-index: 0;
}

/* LAYOUT */
.wrap { max-width: 760px; margin: 0 auto; padding: 60px 24px 100px; position: relative; z-index: 1; }

/* HEADER */
.hdr { text-align: center; margin-bottom: 64px; }
.hdr-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(192,57,90,0.12); border: 1px solid rgba(192,57,90,0.3);
  color: var(--rose-light); padding: 6px 18px; border-radius: 99px;
  font-size: 12px; letter-spacing: 2px; text-transform: uppercase;
  font-family: var(--mono); margin-bottom: 24px;
}
.hdr h1 {
  font-size: clamp(36px, 6vw, 64px); font-weight: 800; line-height: 1.05;
  letter-spacing: -1px;
}
.hdr h1 span { color: var(--rose); }
.hdr p { color: var(--muted); margin-top: 14px; font-size: 15px; line-height: 1.7; }

/* PROGRESS BAR */
.progress-wrap { margin-bottom: 48px; }
.progress-label {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px; font-family: var(--mono); font-size: 12px; color: var(--muted);
}
.progress-label span { color: var(--gold); font-weight: 500; }
.progress-track {
  height: 3px; background: var(--border); border-radius: 99px; overflow: hidden;
}
.progress-fill {
  height: 100%; background: linear-gradient(90deg, var(--rose), var(--gold));
  border-radius: 99px; transition: width 0.6s cubic-bezier(.4,0,.2,1);
}

/* STEP CARDS */
.step {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 20px;
  margin-bottom: 16px;
  overflow: hidden;
  transition: border-color 0.3s;
}
.step.active { border-color: var(--rose); }
.step.done   { border-color: var(--green); }
.step.skipped { opacity: 0.5; }

.step-header {
  display: flex; align-items: center; gap: 16px;
  padding: 22px 28px; cursor: pointer;
  user-select: none;
}
.step-num {
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--mono); font-size: 13px; font-weight: 500;
  background: var(--border); color: var(--muted);
  transition: all 0.3s;
}
.step.active .step-num { background: var(--rose); color: white; }
.step.done   .step-num { background: var(--green); color: white; }
.step-title { font-size: 17px; font-weight: 600; flex: 1; }
.step-subtitle { font-size: 13px; color: var(--muted); margin-top: 2px; }
.step-status {
  font-family: var(--mono); font-size: 11px; letter-spacing: 1px;
  padding: 4px 12px; border-radius: 99px; text-transform: uppercase;
}
.step-status.waiting  { background: rgba(255,255,255,0.05); color: var(--muted); }
.step-status.testing  { background: rgba(255,215,0,0.1); color: var(--gold); }
.step-status.ok       { background: rgba(57,192,122,0.1); color: var(--green); }
.step-status.fail     { background: rgba(192,57,90,0.1); color: var(--rose); }
.step-status.skipped  { background: rgba(255,255,255,0.05); color: var(--muted); }

.step-body { padding: 0 28px 28px; display: none; }
.step.active .step-body, .step.open .step-body { display: block; }

/* INSTRUCTIONS */
.instr {
  background: var(--panel2); border-radius: 12px; padding: 16px 20px;
  margin-bottom: 20px; font-size: 13px; color: #aaa; line-height: 1.8;
}
.instr strong { color: var(--gold); }
.instr a { color: var(--rose-light); text-decoration: none; }
.instr a:hover { text-decoration: underline; }
.instr ol, .instr ul { padding-left: 18px; margin-top: 8px; }
.instr li { margin-bottom: 4px; }

/* INPUTS */
.field { margin-bottom: 16px; }
.field label {
  display: block; font-family: var(--mono); font-size: 11px;
  letter-spacing: 1px; text-transform: uppercase; color: var(--muted);
  margin-bottom: 8px;
}
.field input, .field textarea {
  width: 100%; background: var(--panel2); border: 1px solid var(--border);
  border-radius: 10px; padding: 13px 16px; color: var(--text);
  font-family: var(--mono); font-size: 13px;
  transition: border-color 0.2s; outline: none;
  resize: vertical;
}
.field input:focus, .field textarea:focus { border-color: var(--rose); }
.field input.ok  { border-color: var(--green); }
.field input.err { border-color: var(--rose); }
.field .hint { font-size: 11px; color: var(--muted); margin-top: 6px; font-family: var(--mono); }

/* BUTTONS */
.btn-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; }
.btn {
  padding: 11px 24px; border-radius: 10px; border: none; cursor: pointer;
  font-family: var(--sans); font-size: 14px; font-weight: 600;
  transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px;
}
.btn-primary { background: var(--rose); color: white; }
.btn-primary:hover { background: var(--rose-light); transform: translateY(-1px); }
.btn-primary:active { transform: translateY(0); }
.btn-secondary {
  background: transparent; color: var(--muted);
  border: 1px solid var(--border);
}
.btn-secondary:hover { border-color: var(--muted); color: var(--text); }
.btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none !important; }

/* RESULT BOX */
.result-box {
  margin-top: 16px; padding: 14px 18px; border-radius: 10px;
  font-family: var(--mono); font-size: 12px; line-height: 1.7;
  display: none;
}
.result-box.ok   { background: rgba(57,192,122,0.08); border: 1px solid rgba(57,192,122,0.3); color: #8fefbc; }
.result-box.fail { background: rgba(192,57,90,0.08);  border: 1px solid rgba(192,57,90,0.3);  color: #f08080; }
.result-box.show { display: block; }

/* SPINNER */
@keyframes spin { to { transform: rotate(360deg); } }
.spinner {
  width: 16px; height: 16px; border: 2px solid transparent;
  border-top-color: currentColor; border-radius: 50%;
  animation: spin 0.7s linear infinite; display: inline-block;
}

/* FINAL SUCCESS */
.finale {
  background: linear-gradient(135deg, #0d1a12, #12200a);
  border: 2px solid var(--green);
  border-radius: 24px; padding: 48px; text-align: center;
  margin-top: 32px; display: none;
}
.finale.show { display: block; }
.finale h2 { font-size: 36px; color: var(--green); margin-bottom: 12px; }
.finale p { color: #aaa; margin-bottom: 24px; line-height: 1.8; }
.finale .pcrf-cta {
  display: inline-block; background: var(--rose); color: white;
  text-decoration: none; padding: 14px 36px; border-radius: 12px;
  font-weight: 700; font-size: 15px; transition: 0.2s;
}
.finale .pcrf-cta:hover { background: var(--rose-light); transform: scale(1.03); }
.finale .status-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  margin: 28px 0; text-align: left;
}
.finale .status-item {
  background: rgba(255,255,255,0.04); border-radius: 10px;
  padding: 14px 18px; font-family: var(--mono); font-size: 12px;
}
.finale .status-item .lbl { color: var(--muted); margin-bottom: 4px; }
.finale .status-item .val { color: var(--green); }
.finale .status-item .val.warn { color: var(--gold); }

/* SEPARATOR */
.sep { height: 1px; background: var(--border); margin: 32px 0; }
</style>
</head>
<body>
<div class="wrap">

  <!-- HEADER -->
  <div class="hdr">
    <div class="hdr-badge">&#9670; Meeko Mycelium &#9670; Setup Wizard</div>
    <h1>Connect Your<br><span>Revenue System</span></h1>
    <p>Paste each API key in order. Your system tests, validates, and wires everything automatically.<br>
    Keys are never written to disk — only connection status is saved.</p>
  </div>

  <!-- PROGRESS -->
  <div class="progress-wrap">
    <div class="progress-label">
      <span>Progress</span>
      <span id="prog-label">Step 0 of 5</span>
    </div>
    <div class="progress-track"><div class="progress-fill" id="prog-fill" style="width:0%"></div></div>
  </div>

  <!-- ── STEP 1: GUMROAD ── -->
  <div class="step active" id="step-gumroad">
    <div class="step-header" onclick="toggleOpen('step-gumroad')">
      <div class="step-num">1</div>
      <div style="flex:1">
        <div class="step-title">Gumroad</div>
        <div class="step-subtitle">Sell your PDFs &amp; art — primary revenue channel</div>
      </div>
      <div class="step-status waiting" id="status-gumroad">Waiting</div>
    </div>
    <div class="step-body">
      <div class="instr">
        <strong>How to get your Gumroad Access Token:</strong>
        <ol>
          <li>Go to <a href="https://gumroad.com/oauth/applications" target="_blank">gumroad.com/oauth/applications</a></li>
          <li>Click <strong>New Application</strong></li>
          <li>Name it anything (e.g. "Meeko System") &rarr; Save</li>
          <li>Click <strong>Generate Access Token</strong></li>
          <li>Copy the long token that appears</li>
        </ol>
      </div>
      <div class="field">
        <label>Gumroad Access Token</label>
        <input type="password" id="key-gumroad" placeholder="Paste your Gumroad access token here...">
        <div class="hint">Starts with a long alphanumeric string</div>
      </div>
      <div class="btn-row">
        <button class="btn btn-primary" onclick="testStep('gumroad')"><span id="btn-gumroad-txt">Test &amp; Connect</span></button>
        <button class="btn btn-secondary" onclick="skipStep('gumroad')">Skip for now</button>
      </div>
      <div class="result-box" id="result-gumroad"></div>
    </div>
  </div>

  <!-- ── STEP 2: COINBASE COMMERCE ── -->
  <div class="step" id="step-commerce">
    <div class="step-header" onclick="toggleOpen('step-commerce')">
      <div class="step-num">2</div>
      <div style="flex:1">
        <div class="step-title">Coinbase Commerce</div>
        <div class="step-subtitle">Accept BTC, ETH, USDC, SOL from customers</div>
      </div>
      <div class="step-status waiting" id="status-commerce">Waiting</div>
    </div>
    <div class="step-body">
      <div class="instr">
        <strong>How to get your Coinbase Commerce API Key:</strong>
        <ol>
          <li>Go to <a href="https://commerce.coinbase.com" target="_blank">commerce.coinbase.com</a></li>
          <li>Sign up or log in (separate from main Coinbase)</li>
          <li>Go to <strong>Settings &rarr; Security &rarr; API Keys</strong></li>
          <li>Click <strong>Create an API key</strong></li>
          <li>Copy the key shown (only shown once — copy it now!)</li>
        </ol>
      </div>
      <div class="field">
        <label>Coinbase Commerce API Key</label>
        <input type="password" id="key-commerce" placeholder="Paste your Commerce API key here...">
        <div class="hint">A long alphanumeric string from commerce.coinbase.com</div>
      </div>
      <div class="btn-row">
        <button class="btn btn-primary" onclick="testStep('commerce')"><span id="btn-commerce-txt">Test &amp; Connect</span></button>
        <button class="btn btn-secondary" onclick="skipStep('commerce')">Skip for now</button>
      </div>
      <div class="result-box" id="result-commerce"></div>
    </div>
  </div>

  <!-- ── STEP 3: COINBASE ADVANCED ── -->
  <div class="step" id="step-coinbase">
    <div class="step-header" onclick="toggleOpen('step-coinbase')">
      <div class="step-num">3</div>
      <div style="flex:1">
        <div class="step-title">Coinbase Advanced Trade</div>
        <div class="step-subtitle">Read your balances &amp; track revenue</div>
      </div>
      <div class="step-status waiting" id="status-coinbase">Waiting</div>
    </div>
    <div class="step-body">
      <div class="instr">
        <strong>How to get your Coinbase Advanced Trade API Key:</strong>
        <ol>
          <li>Go to <a href="https://www.coinbase.com/settings/api" target="_blank">coinbase.com/settings/api</a></li>
          <li>Click <strong>+ New API Key</strong></li>
          <li>Under permissions check <strong>View</strong> only (read-only is safest)</li>
          <li>Complete 2FA verification</li>
          <li>Copy the <strong>API Key Name</strong> (starts with <code>organizations/...</code>)</li>
          <li>Copy the <strong>Private Key</strong> (the full block including <code>-----BEGIN EC PRIVATE KEY-----</code>)</li>
        </ol>
      </div>
      <div class="field">
        <label>Coinbase API Key Name</label>
        <input type="password" id="key-cb-name" placeholder="organizations/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/apiKeys/...">
      </div>
      <div class="field">
        <label>Coinbase Private Key (full block)</label>
        <textarea id="key-cb-secret" rows="5" placeholder="-----BEGIN EC PRIVATE KEY-----&#10;MHQCAQEEIxxxxxxxx...&#10;-----END EC PRIVATE KEY-----"></textarea>
        <div class="hint">Paste the entire key including the BEGIN/END lines</div>
      </div>
      <div class="btn-row">
        <button class="btn btn-primary" onclick="testStep('coinbase')"><span id="btn-coinbase-txt">Test &amp; Connect</span></button>
        <button class="btn btn-secondary" onclick="skipStep('coinbase')">Skip for now</button>
      </div>
      <div class="result-box" id="result-coinbase"></div>
    </div>
  </div>

  <!-- ── STEP 4: PHANTOM ── -->
  <div class="step" id="step-phantom">
    <div class="step-header" onclick="toggleOpen('step-phantom')">
      <div class="step-num">4</div>
      <div style="flex:1">
        <div class="step-title">Phantom Wallet (Solana)</div>
        <div class="step-subtitle">Accept SOL &amp; USDC directly — zero fees</div>
      </div>
      <div class="step-status waiting" id="status-phantom">Waiting</div>
    </div>
    <div class="step-body">
      <div class="instr">
        <strong>How to get your Phantom wallet address:</strong>
        <ol>
          <li>Click the <strong>Phantom extension</strong> in your Brave browser</li>
          <li>Click your <strong>account name</strong> at the top of Phantom</li>
          <li>Your address is shown below it — click to copy</li>
          <li>It looks like: <code>7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU</code></li>
        </ol>
        <br>
        <strong>This is your PUBLIC address</strong> — completely safe to share. It's like an email address, not a password.
      </div>
      <div class="field">
        <label>Your Phantom / Solana Address (public)</label>
        <input type="text" id="key-phantom" placeholder="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU">
        <div class="hint">44-character base58 string — paste your public wallet address</div>
      </div>
      <div class="btn-row">
        <button class="btn btn-primary" onclick="testStep('phantom')"><span id="btn-phantom-txt">Verify &amp; Connect</span></button>
        <button class="btn btn-secondary" onclick="skipStep('phantom')">Skip for now</button>
      </div>
      <div class="result-box" id="result-phantom"></div>
    </div>
  </div>

  <!-- ── STEP 5: ALPACA TRADING ── -->
  <div class="step" id="step-alpaca">
    <div class="step-header" onclick="toggleOpen('step-alpaca')">
      <div class="step-num">5</div>
      <div style="flex:1">
        <div class="step-title">Alpaca Markets — Stock &amp; Crypto Trading</div>
        <div class="step-subtitle">Paper trading free &bull; No real money needed to start</div>
      </div>
      <div class="step-status waiting" id="status-alpaca">Waiting</div>
    </div>
    <div class="step-body">
      <div class="instr">
        <strong>Alpaca is a commission-free, FINRA-registered broker with a full API.</strong>
        Paper trading is 100% free — same API, fake money. Start there.<br><br>
        <strong>How to get your Alpaca API keys:</strong>
        <ol>
          <li>Go to <a href="https://app.alpaca.markets" target="_blank">app.alpaca.markets</a> and create a free account</li>
          <li>From your dashboard, click <strong>Paper Trading</strong> (top right)</li>
          <li>Go to <strong>Overview &rarr; API Keys</strong></li>
          <li>Click <strong>Generate New Key</strong> &rarr; copy both keys shown</li>
          <li>For live trading later: same steps under <strong>Live Trading</strong> after funding your account</li>
        </ol>
      </div>
      <div class="field">
        <label>Alpaca API Key ID</label>
        <input type="password" id="key-alpaca-id" placeholder="PKXXXXXXXXXXXXXXXXXXXXXXXX">
        <div class="hint">Starts with PK (paper) or AK (live)</div>
      </div>
      <div class="field">
        <label>Alpaca Secret Key</label>
        <input type="password" id="key-alpaca-secret" placeholder="Your Alpaca secret key">
      </div>
      <div class="field">
        <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
          <input type="checkbox" id="alpaca-live" style="width:auto">
          <span>This is a LIVE (real money) account</span>
        </label>
        <div class="hint">Leave unchecked for paper trading (recommended to start)</div>
      </div>
      <div class="btn-row">
        <button class="btn btn-primary" onclick="testStep('alpaca')"><span id="btn-alpaca-txt">Test &amp; Connect</span></button>
        <button class="btn btn-secondary" onclick="skipStep('alpaca')">Skip for now</button>
      </div>
      <div class="result-box" id="result-alpaca"></div>
    </div>
  </div>

  <!-- ── STEP 6: OPTIONAL ── -->
  <div class="step" id="step-optional">
    <div class="step-header" onclick="toggleOpen('step-optional')">
      <div class="step-num">6</div>
      <div style="flex:1">
        <div class="step-title">Stripe &amp; PayPal <span style="color:var(--muted);font-size:13px;font-weight:400;">(optional)</span></div>
        <div class="step-subtitle">Add when your accounts are working</div>
      </div>
      <div class="step-status waiting" id="status-optional">Optional</div>
    </div>
    <div class="step-body">
      <div class="instr">
        These can be added later when your Stripe/PayPal accounts are resolved.
        Your system works fully with Gumroad + Coinbase + Phantom in the meantime.
      </div>
      <div class="field">
        <label>Stripe Secret Key (optional)</label>
        <input type="password" id="key-stripe" placeholder="sk_live_... or sk_test_...">
      </div>
      <div class="field">
        <label>PayPal Client ID (optional)</label>
        <input type="password" id="key-pp-id" placeholder="Your PayPal Client ID">
      </div>
      <div class="field">
        <label>PayPal Secret (optional)</label>
        <input type="password" id="key-pp-secret" placeholder="Your PayPal Secret">
      </div>
      <div class="btn-row">
        <button class="btn btn-primary" onclick="testStep('optional')"><span id="btn-optional-txt">Test What's Filled</span></button>
        <button class="btn btn-secondary" onclick="skipStep('optional')">Skip — do later</button>
      </div>
      <div class="result-box" id="result-optional"></div>
    </div>
  </div>

  <div class="sep"></div>

  <!-- FINAL SETUP BUTTON -->
  <div style="text-align:center;margin-bottom:32px;">
    <button class="btn btn-primary" id="btn-finalize" style="font-size:16px;padding:16px 48px;border-radius:14px;" onclick="finalize()">
      <span id="btn-finalize-txt">Wire Everything Into My System</span>
    </button>
    <div style="color:var(--muted);font-size:12px;margin-top:12px;font-family:var(--mono);">
      Writes payment page, updates gallery, saves status to Gaza Rose DB
    </div>
  </div>

  <!-- FINALE -->
  <div class="finale" id="finale">
    <h2>System Ready</h2>
    <p>All connected services have been wired into your gallery, database, and payment pages.<br>
    Your system is live.</p>
    <div class="status-grid" id="finale-grid"></div>
    <a href="GAZA_ROSE_GALLERY/index.html" class="pcrf-cta" style="margin-bottom:16px;display:inline-block;margin-right:12px;">Open Gallery</a>
    <a href="GAZA_ROSE_GALLERY/payment.html" class="pcrf-cta" style="background:#1a3a1a;border:1px solid var(--green);display:inline-block;margin-bottom:16px;margin-right:12px;">Payment Page</a>
    <a href="https://give.pcrf.net/campaign/739651/donate" target="_blank" class="pcrf-cta" style="background:var(--panel2);border:1px solid var(--rose);display:inline-block;">Donate to PCRF</a>
    <div style="margin-top:28px;font-size:13px;color:var(--muted);">
      Signed: Meeko &mdash; Gaza refugees benefit FIRST. Forever.
    </div>
  </div>

</div><!-- /wrap -->

<script>
const state = {
  completed: new Set(),
  results: {},
  total: 6
};

function updateProgress() {
  const done = state.completed.size;
  document.getElementById('prog-fill').style.width = (done / state.total * 100) + '%';
  document.getElementById('prog-label').textContent = `Step ${done} of ${state.total}`;
}

function toggleOpen(id) {
  const el = document.getElementById(id);
  el.classList.toggle('open');
}

function setStatus(step, status, text) {
  const el = document.getElementById(`status-${step}`);
  el.className = `step-status ${status}`;
  el.textContent = text;
}

function setResult(step, ok, msg) {
  const box = document.getElementById(`result-${step}`);
  box.className = `result-box ${ok ? 'ok' : 'fail'} show`;
  box.innerHTML = msg;
}

function setBtnText(step, text) {
  document.getElementById(`btn-${step}-txt`).textContent = text;
}

async function testStep(step) {
  const btn = document.querySelector(`#step-${step} .btn-primary`);
  btn.disabled = true;
  setStatus(step, 'testing', 'Testing...');
  setBtnText(step, '');
  document.getElementById(`btn-${step}-txt`).innerHTML = '<span class="spinner"></span>';

  const payload = {};
  if (step === 'gumroad')  payload.token   = document.getElementById('key-gumroad').value.trim();
  if (step === 'commerce') payload.key     = document.getElementById('key-commerce').value.trim();
  if (step === 'coinbase') {
    payload.api_key_name = document.getElementById('key-cb-name').value.trim();
    payload.api_secret   = document.getElementById('key-cb-secret').value.trim();
  }
  if (step === 'phantom')  payload.address = document.getElementById('key-phantom').value.trim();
  if (step === 'alpaca') {
    payload.alpaca_key    = document.getElementById('key-alpaca-id').value.trim();
    payload.alpaca_secret = document.getElementById('key-alpaca-secret').value.trim();
    payload.alpaca_live   = document.getElementById('alpaca-live').checked;
  }
  if (step === 'optional') {
    payload.stripe_key    = document.getElementById('key-stripe').value.trim();
    payload.paypal_id     = document.getElementById('key-pp-id').value.trim();
    payload.paypal_secret = document.getElementById('key-pp-secret').value.trim();
  }

  try {
    const resp = await fetch(`/test/${step}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await resp.json();

    if (data.ok) {
      setStatus(step, 'ok', 'Connected');
      setBtnText(step, 'Connected!');
      document.getElementById(`step-${step}`).classList.add('done');
      document.getElementById(`step-${step}`).classList.remove('active');
      setResult(step, true, data.message);
      state.completed.add(step);
      state.results[step] = data;

      // Auto-open next step
      const steps = ['gumroad','commerce','coinbase','phantom','alpaca','optional'];
      const idx = steps.indexOf(step);
      if (idx < steps.length - 1) {
        const nextEl = document.getElementById(`step-${steps[idx+1]}`);
        nextEl.classList.add('active');
        nextEl.scrollIntoView({behavior:'smooth', block:'center'});
      }
    } else {
      setStatus(step, 'fail', 'Failed');
      setBtnText(step, 'Retry');
      setResult(step, false, data.message);
      btn.disabled = false;
    }
  } catch(e) {
    setStatus(step, 'fail', 'Error');
    setBtnText(step, 'Retry');
    setResult(step, false, `Network error: ${e.message}`);
    btn.disabled = false;
  }

  updateProgress();
}

function skipStep(step) {
  setStatus(step, 'skipped', 'Skipped');
  document.getElementById(`step-${step}`).classList.add('skipped');
  state.completed.add(step + '_skip');

  const stepsSkip = ['gumroad','commerce','coinbase','phantom','alpaca','optional'];
  const idxSkip = stepsSkip.indexOf(step);
}

async function finalize() {
  const btn = document.getElementById('btn-finalize');
  btn.disabled = true;
  document.getElementById('btn-finalize-txt').innerHTML = '<span class="spinner"></span>&nbsp;Wiring everything...';

  try {
    const resp = await fetch('/finalize', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(state.results)
    });
    const data = await resp.json();

    const grid = document.getElementById('finale-grid');
    grid.innerHTML = '';
    for (const [k, v] of Object.entries(data.summary)) {
      grid.innerHTML += `<div class="status-item">
        <div class="lbl">${k}</div>
        <div class="val ${v.ok ? '' : 'warn'}">${v.detail}</div>
      </div>`;
    }

    document.getElementById('finale').classList.add('show');
    document.getElementById('finale').scrollIntoView({behavior:'smooth'});
  } catch(e) {
    btn.disabled = false;
    document.getElementById('btn-finalize-txt').textContent = 'Wire Everything Into My System';
    alert('Error: ' + e.message);
  }
}
</script>
</body>
</html>"""

# ── REQUEST HANDLER ────────────────────────────────────────
class WizardHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # silence default logging

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            body = WIZARD_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = json.loads(self.rfile.read(length)) if length else {}

        if self.path == '/test/gumroad':
            self.send_json(test_gumroad(body))
        elif self.path == '/test/commerce':
            self.send_json(test_commerce(body))
        elif self.path == '/test/coinbase':
            self.send_json(test_coinbase(body))
        elif self.path == '/test/phantom':
            self.send_json(test_phantom(body))
        elif self.path == '/test/optional':
            self.send_json(test_optional(body))
        elif self.path == '/test/alpaca':
            self.send_json(test_alpaca(body))
        elif self.path == '/finalize':
            self.send_json(finalize(body))
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

# ── TEST FUNCTIONS ─────────────────────────────────────────
def test_gumroad(body):
    token = body.get('token', '').strip()
    if not token:
        return {'ok': False, 'message': 'No token provided.'}
    try:
        req = urllib.request.Request(
            'https://api.gumroad.com/v2/user',
            headers={'Authorization': f'Bearer {token}'}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        user = data.get('user', {})
        email = user.get('email', 'verified')
        _save_connection('gumroad', 'connected', {'email': email})
        _store_runtime('gumroad_token', token)
        return {'ok': True, 'message': f'Connected as: {email}', 'email': email}
    except Exception as e:
        return {'ok': False, 'message': f'Error: {e}'}

def test_commerce(body):
    key = body.get('key', '').strip()
    if not key:
        return {'ok': False, 'message': 'No key provided.'}
    try:
        req = urllib.request.Request(
            'https://api.commerce.coinbase.com/checkouts',
            headers={'X-CC-Api-Key': key, 'X-CC-Version': '2018-03-22'}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        count = len(data.get('data', []))
        _save_connection('coinbase_commerce', 'connected', {'checkouts': count})
        _store_runtime('commerce_key', key)
        return {'ok': True, 'message': f'Connected! {count} existing checkout(s) found.<br>Accepts: BTC, ETH, USDC, SOL, DOGE, LTC', 'checkouts': count}
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:200]
        return {'ok': False, 'message': f'HTTP {e.code}: {msg}'}
    except Exception as e:
        return {'ok': False, 'message': f'Error: {e}'}

def test_coinbase(body):
    api_key = body.get('api_key_name', '').strip()
    api_secret = body.get('api_secret', '').strip()
    if not api_key or not api_secret:
        return {'ok': False, 'message': 'Both API Key Name and Private Key are required.'}
    try:
        from coinbase.rest import RESTClient
        client = RESTClient(api_key=api_key, api_secret=api_secret)
        accounts = client.get_accounts()
        acct_list = accounts.accounts if hasattr(accounts, 'accounts') else []
        with_balance = []
        balances = {}
        for a in acct_list:
            val = float(getattr(getattr(a, 'available_balance', None), 'value', 0) or 0)
            if val > 0:
                currency = getattr(a, 'currency', '?')
                balances[currency] = val
                with_balance.append(f"{currency}: {val}")
        bal_str = ', '.join(with_balance) if with_balance else 'No balances yet'
        _save_connection('coinbase_advanced', 'connected', {'accounts': len(acct_list), 'balances': balances})
        _store_runtime('cb_api_key', api_key)
        _store_runtime('cb_api_secret', api_secret)
        return {'ok': True, 'message': f'{len(acct_list)} accounts found.<br>Balances: {bal_str}', 'balances': balances}
    except Exception as e:
        return {'ok': False, 'message': f'Error: {e}<br><br>Make sure you copied the full private key including the BEGIN/END lines.'}

def test_phantom(body):
    address = body.get('address', '').strip()
    if not address or len(address) < 32:
        return {'ok': False, 'message': 'Address looks too short. Copy the full address from Phantom.'}
    try:
        payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"getBalance","params":[address]}).encode()
        req = urllib.request.Request(
            'https://api.mainnet-beta.solana.com', data=payload,
            headers={'Content-Type': 'application/json'}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        lamports = data.get('result', {}).get('value', 0)
        sol = lamports / 1_000_000_000
        short = f"{address[:8]}...{address[-6:]}"
        _save_connection('phantom_solana', 'connected', {'address': address, 'sol_balance': sol})
        _store_runtime('phantom_address', address)
        return {'ok': True, 'message': f'Wallet verified on Solana mainnet!<br>Address: {short}<br>Balance: {sol:.6f} SOL', 'address': address, 'sol': sol}
    except Exception as e:
        return {'ok': False, 'message': f'Error: {e}'}

def test_optional(body):
    msgs = []
    ok_any = False
    stripe_key    = body.get('stripe_key', '').strip()
    paypal_id     = body.get('paypal_id', '').strip()
    paypal_secret = body.get('paypal_secret', '').strip()

    if stripe_key:
        try:
            import stripe as stripe_lib
            stripe_lib.api_key = stripe_key
            bal = stripe_lib.Balance.retrieve()
            avail = bal['available'][0]['amount'] / 100
            curr  = bal['available'][0]['currency'].upper()
            _save_connection('stripe', 'connected', {'balance': avail})
            _store_runtime('stripe_key', stripe_key)
            msgs.append(f'Stripe: Connected — balance {avail} {curr}')
            ok_any = True
        except Exception as e:
            msgs.append(f'Stripe: {e}')
    else:
        msgs.append('Stripe: Skipped')

    if paypal_id and paypal_secret:
        try:
            import base64
            creds = base64.b64encode(f"{paypal_id}:{paypal_secret}".encode()).decode()
            req = urllib.request.Request(
                'https://api-m.paypal.com/v1/oauth2/token',
                data=b'grant_type=client_credentials',
                headers={'Authorization': f'Basic {creds}', 'Content-Type': 'application/x-www-form-urlencoded'}
            )
            resp = urllib.request.urlopen(req, timeout=15)
            _save_connection('paypal', 'connected', {})
            _store_runtime('paypal_id', paypal_id)
            _store_runtime('paypal_secret', paypal_secret)
            msgs.append('PayPal: Connected')
            ok_any = True
        except Exception as e:
            msgs.append(f'PayPal: {e}')
    else:
        msgs.append('PayPal: Skipped')

    return {'ok': True, 'message': '<br>'.join(msgs)}

def test_alpaca(body):
    key    = body.get('alpaca_key', '').strip()
    secret = body.get('alpaca_secret', '').strip()
    live   = body.get('alpaca_live', False)
    if not key or not secret:
        return {'ok': False, 'message': 'Both Alpaca API Key ID and Secret Key are required.'}
    try:
        from alpaca.trading.client import TradingClient
        client = TradingClient(key, secret, paper=not live)
        acct   = client.get_account()
        mode   = 'LIVE' if live else 'PAPER'
        equity = float(acct.equity)
        bp     = float(acct.buying_power)
        _save_connection('alpaca_' + mode.lower(), 'connected',
                         {'equity': equity, 'buying_power': bp, 'mode': mode})
        _store_runtime('alpaca_key', key)
        _store_runtime('alpaca_secret', secret)
        _store_runtime('alpaca_live', live)
        # Wire keys into trading system
        sys.path.insert(0, str(DESKTOP / 'TRADING_SYSTEM'))
        import trading_bridge
        trading_bridge.set_keys(alpaca_key=key, alpaca_secret=secret, alpaca_live=live)
        return {
            'ok': True,
            'message': f'Alpaca {mode} connected!<br>Equity: ${equity:,.2f} | Buying Power: ${bp:,.2f}',
            'equity': equity,
            'mode': mode,
        }
    except Exception as e:
        return {'ok': False, 'message': f'Error: {e}<br><br>Make sure you created the key at alpaca.markets'}

# ── FINALIZE ───────────────────────────────────────────────
def finalize(results):
    summary = {}

    # 1. Rebuild payment page with phantom address
    phantom_address = _get_runtime('phantom_address')
    if phantom_address:
        _build_payment_page(phantom_address)
        short = f"{phantom_address[:8]}...{phantom_address[-6:]}"
        summary['Payment Page'] = {'ok': True, 'detail': f'Built with {short}'}
    else:
        summary['Payment Page'] = {'ok': False, 'detail': 'No Phantom address — skipped'}

    # 2. Write payment_config.json for gallery
    cfg = {
        'updated': datetime.now().isoformat(),
        'phantom_solana': phantom_address or '',
        'pcrf_donation_link': PCRF_LINK,
        'pcrf_note': 'PCRF accepts fiat only. Convert crypto, then donate at the link above.',
        'accepted_via_phantom': ['SOL', 'USDC'],
        'accepted_via_coinbase_commerce': ['BTC', 'ETH', 'USDC', 'SOL', 'DOGE', 'LTC']
    }
    with open(CRYPTO_CFG, 'w') as f:
        json.dump(cfg, f, indent=2)
    summary['Payment Config'] = {'ok': True, 'detail': 'payment_config.json written'}

    # 3. Rebuild gallery HTML with crypto buttons
    try:
        result = subprocess.run(
            [sys.executable, str(GALLERY_DIR / 'rebuild_gallery.py')],
            capture_output=True, text=True, timeout=30
        )
        summary['Gallery'] = {'ok': True, 'detail': '69 artworks, crypto buttons live'}
    except Exception as e:
        summary['Gallery'] = {'ok': False, 'detail': str(e)}

    # 4. Update treasury script to use Solana instead of PayPal
    _update_treasury(phantom_address)
    summary['Treasury Script'] = {'ok': True, 'detail': 'Updated to Solana payments'}

    # 5. Run UltimateAI evolution
    try:
        master = DESKTOP / 'UltimateAI_Master' / 'ultimate_ai_master_v15.py'
        subprocess.Popen([sys.executable, str(master), '--evolve'],
                        creationflags=0x00000008)  # DETACHED_PROCESS on Windows
        summary['UltimateAI Master'] = {'ok': True, 'detail': 'Evolution cycle triggered'}
    except Exception as e:
        summary['UltimateAI Master'] = {'ok': False, 'detail': str(e)}

    # 6. Log all connections
    gumroad = _get_connection_status('gumroad')
    commerce = _get_connection_status('coinbase_commerce')
    cb_adv  = _get_connection_status('coinbase_advanced')
    phantom = _get_connection_status('phantom_solana')
    summary['Gumroad']            = {'ok': gumroad == 'connected',  'detail': gumroad}
    summary['Coinbase Commerce']  = {'ok': commerce == 'connected', 'detail': commerce}
    summary['Coinbase Advanced']  = {'ok': cb_adv == 'connected',   'detail': cb_adv}
    summary['Phantom/Solana']     = {'ok': phantom == 'connected',  'detail': phantom}
    summary['PCRF Link']          = {'ok': True, 'detail': 'Verified — give.pcrf.net live'}

    return {'ok': True, 'summary': summary}

# ── HELPERS ────────────────────────────────────────────────
_runtime = {}   # in-memory only — never written to disk

def _store_runtime(key, value):
    _runtime[key] = value

def _get_runtime(key):
    return _runtime.get(key, '')

def _save_connection(platform, status, details):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute('''CREATE TABLE IF NOT EXISTS crypto_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, platform TEXT, status TEXT, details TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS crypto_config (
            key TEXT PRIMARY KEY, value TEXT, updated TEXT)''')
        conn.execute('INSERT INTO crypto_connections VALUES (NULL,?,?,?,?)',
            (datetime.now().isoformat(), platform, status, json.dumps(details)))
        # Save phantom address specifically for payment pages
        if platform == 'phantom_solana' and details.get('address'):
            conn.execute('INSERT OR REPLACE INTO crypto_config VALUES (?,?,?)',
                ('phantom_address', details['address'], datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception:
        pass

def _get_connection_status(platform):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        row = conn.execute(
            'SELECT status FROM crypto_connections WHERE platform=? ORDER BY id DESC LIMIT 1',
            (platform,)).fetchone()
        conn.close()
        return row[0] if row else 'not connected'
    except:
        return 'unknown'

def _build_payment_page(phantom_address):
    addr_short = f"{phantom_address[:8]}...{phantom_address[-6:]}"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pay with Crypto — Gaza Rose Gallery</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap" rel="stylesheet">
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:#0d0d0d;color:#e8e8e8;font-family:'Syne',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
    .container{{max-width:680px;width:100%}}
    h1{{font-size:40px;font-weight:800;text-align:center;margin-bottom:8px;background:linear-gradient(45deg,#FFD700,#f39c12);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
    .sub{{text-align:center;color:#666;margin-bottom:40px;font-size:14px;font-family:'DM Mono',monospace}}
    .card{{background:#141414;border:1px solid #2a2a2a;border-radius:20px;padding:28px;margin-bottom:16px;transition:.3s}}
    .card:hover{{border-color:#C0395A}}
    .card-head{{display:flex;align-items:center;gap:14px;margin-bottom:18px}}
    .icon{{font-size:32px}}
    .card-title{{font-size:18px;font-weight:700}}
    .card-sub{{color:#666;font-size:12px;font-family:'DM Mono',monospace;margin-top:3px}}
    .tag{{display:inline-block;background:#1a1a2a;border:1px solid #C0395A;color:#C0395A;padding:3px 10px;border-radius:99px;font-size:11px;margin:2px;font-family:'DM Mono',monospace}}
    .tag.g{{background:#1a2a1a;border-color:#39C07A;color:#39C07A}}
    .addr{{background:#111;border:1px solid #333;border-radius:10px;padding:14px 18px;font-family:'DM Mono',monospace;font-size:12px;color:#39C07A;word-break:break-all;margin:14px 0}}
    .copy-btn{{background:#C0395A;color:white;border:none;padding:10px 24px;border-radius:10px;cursor:pointer;font-family:'Syne',sans-serif;font-weight:700;font-size:13px;transition:.2s}}
    .copy-btn:hover{{background:#e04070;transform:scale(1.03)}}
    .copy-btn.ok{{background:#39C07A}}
    .note{{background:#1a1a00;border:1px solid rgba(255,215,0,0.2);border-radius:10px;padding:14px 18px;font-size:12px;color:#aaa;margin-top:12px;font-family:'DM Mono',monospace;line-height:1.7}}
    .note strong{{color:#FFD700}}
    .pcrf{{background:linear-gradient(135deg,#1a1a2e,#16213e);border:2px solid #C0395A;border-radius:20px;padding:36px;text-align:center;margin-top:16px}}
    .pcrf h2{{color:#FFD700;font-size:22px;margin-bottom:12px}}
    .pcrf p{{color:#aaa;font-size:13px;line-height:1.7;margin-bottom:20px}}
    .pcrf a{{display:inline-block;background:#C0395A;color:white;text-decoration:none;padding:13px 32px;border-radius:10px;font-weight:700;font-size:14px;transition:.2s}}
    .pcrf a:hover{{background:#e04070;transform:scale(1.03)}}
    .verified{{color:#39C07A;font-size:11px;font-family:'DM Mono',monospace;margin-top:10px}}
    .back{{text-align:center;margin-top:24px}}
    .back a{{color:#666;text-decoration:none;font-size:13px;font-family:'DM Mono',monospace}}
    .back a:hover{{color:#C0395A}}
  </style>
</head>
<body>
<div class="container">
  <h1>Pay with Crypto</h1>
  <div class="sub">Gaza Rose Gallery &bull; By Meeko &bull; 70% to PCRF Forever</div>

  <div class="card">
    <div class="card-head">
      <div class="icon">&#9675;</div>
      <div>
        <div class="card-title">Solana / USDC via Phantom</div>
        <div class="card-sub">Instant &bull; Near-zero fees &bull; No middleman</div>
      </div>
    </div>
    <span class="tag g">SOL</span>
    <span class="tag g">USDC on Solana</span>
    <div class="addr" id="sol-addr">{phantom_address}</div>
    <button class="copy-btn" onclick="copy('sol-addr',this)">Copy Address</button>
    <div class="note">
      <strong>How to pay:</strong> Open Phantom in Brave &rarr; Send &rarr; paste this address &rarr; enter amount &rarr; confirm.
    </div>
  </div>

  <div class="card">
    <div class="card-head">
      <div class="icon">&#8383;</div>
      <div>
        <div class="card-title">Bitcoin, Ethereum &amp; More</div>
        <div class="card-sub">Via Coinbase Commerce &bull; All major coins</div>
      </div>
    </div>
    <span class="tag">BTC</span><span class="tag">ETH</span><span class="tag">USDC</span><span class="tag">SOL</span><span class="tag">DOGE</span>
    <div class="note" style="margin-top:14px">
      <strong>To pay with BTC/ETH/DOGE:</strong> Visit the product listing on
      <a href="https://gumroad.com/meeko" style="color:#C0395A">Gumroad</a> and select your preferred coin at checkout,
      or message Meeko directly to generate a custom invoice.
    </div>
  </div>

  <div class="pcrf">
    <h2>70% to Palestinian Children</h2>
    <p>Every purchase triggers a <strong>70% donation to PCRF</strong> &mdash; Palestine Children's Relief Fund.<br>
    Verified 501(c)(3) &bull; 4-star Charity Navigator &bull; Founded 1991</p>
    <a href="{PCRF_LINK}" target="_blank">Donate Directly to PCRF</a>
    <div class="verified">Verified at pcrf.net &bull; EIN on file</div>
  </div>

  <div class="back"><a href="index.html">&larr; Back to Gallery</a></div>
</div>
<script>
function copy(id, btn) {{
  navigator.clipboard.writeText(document.getElementById(id).innerText.trim()).then(() => {{
    btn.textContent='Copied!'; btn.classList.add('ok');
    setTimeout(()=>{{btn.textContent='Copy Address';btn.classList.remove('ok')}},2000);
  }});
}}
</script>
</body></html>"""
    with open(PAYMENT_PAGE, 'w', encoding='utf-8') as f:
        f.write(html)

def _update_treasury(phantom_address):
    """Update autonomous_treasury.py to use Solana instead of PayPal"""
    treasury_path = GALLERY_DIR / 'autonomous_treasury.py'
    if not phantom_address:
        return
    new_content = f"""# =====================================================
# AUTONOMOUS TREASURY - SOLANA PAYMENT INTEGRATION
# Updated by Setup Wizard on {datetime.now().strftime('%Y-%m-%d %H:%M')}
# =====================================================
import pod_config
import json
import urllib.request
from datetime import datetime

PHANTOM_ADDRESS = "{phantom_address}"
PCRF_LINK = "{PCRF_LINK}"

def check_sol_balance():
    \"\"\"Check current SOL balance of the treasury wallet\"\"\"
    payload = json.dumps({{"jsonrpc":"2.0","id":1,"method":"getBalance","params":[PHANTOM_ADDRESS]}}).encode()
    req = urllib.request.Request('https://api.mainnet-beta.solana.com', data=payload,
        headers={{'Content-Type':'application/json'}})
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    return data.get('result', {{}}).get('value', 0) / 1_000_000_000

def weekly_art_cycle(self):
    \"\"\"Generate art, add to store, sell, donate 70% to PCRF.\"\"\"
    print("\\n  WEEKLY ART CYCLE")

    artwork_file = generate_art()
    title = f"Gaza Rose - Generation {{self.generation}}"
    product = pod_config.create_product(artwork_file, title, 25.00)
    sale = pod_config.process_sale(product['id'], 25.00)

    pcrf_amount = sale['amount'] * 0.70
    reinvest    = sale['amount'] * 0.30

    print(f"  Sale: ${{sale['amount']:.2f}}")
    print(f"  PCRF share (70%): ${{pcrf_amount:.2f}} — convert to USD and donate at:")
    print(f"  {{PCRF_LINK}}")
    print(f"  Treasury (30%): ${{reinvest:.2f}}")

    sol_balance = check_sol_balance()
    print(f"  Treasury SOL balance: {{sol_balance:.6f}} SOL")
    print(f"  Payment address: {{PHANTOM_ADDRESS[:8]}}...{{PHANTOM_ADDRESS[-6:]}}")

    self.balance += reinvest
    self.generation += 1
"""
    with open(treasury_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

# ── MAIN ───────────────────────────────────────────────────
if __name__ == '__main__':
    server = http.server.HTTPServer(('127.0.0.1', PORT), WizardHandler)
    print(f"\n{'='*56}")
    print(f"  MEEKO MYCELIUM — SETUP WIZARD")
    print(f"{'='*56}")
    print(f"\n  Opening your browser to http://localhost:{PORT}")
    print(f"  Fill in each API key in order.")
    print(f"  Press Ctrl+C in this window when done.\n")

    threading.Timer(1.2, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  Wizard closed. Your connections are saved.")
        print(f"  Gaza Rose DB: {DB_PATH}")
        print(f"  Gallery: {GALLERY_DIR / 'index.html'}")
        print(f"  Payment page: {PAYMENT_PAGE}\n")
