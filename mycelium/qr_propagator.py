#!/usr/bin/env python3
"""
QR Propagator
==============
Consent-first physical-to-digital bridge.

The idea:
  Any physical object (card, sticker, print, merch, zine)
  gets a QR code. Someone scans it.
  They land on a consent page.
  They say Yes  -> system begins propagating (fork guide, download, etc.)
  They say No   -> "Yeah, no problem! Thanks for being YOU." Full stop.
  ALL data scrubbed immediately after either path completes.

Philosophy:
  - Minimum friction, maximum respect
  - Never pass data through more hands than necessary
  - A 'No' is just as valid as a 'Yes'
  - The system grows by invitation, never by capture

Outputs:
  - public/qr/          QR code images (PNG) for printing
  - public/consent.html Landing page with consent flow
  - data/qr_manifest.json  What QR codes exist and what they point to

QR API used: api.qrserver.com (free, no auth, returns PNG)
"""

import json, datetime, hashlib
from pathlib import Path
from urllib import request as urllib_request

ROOT   = Path(__file__).parent.parent
PUBLIC = ROOT / 'public'
DATA   = ROOT / 'data'

(PUBLIC / 'qr').mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()

# QR destinations - each physical object type gets its own QR
QR_DESTINATIONS = [
    {
        'id':       'fork_guide',
        'label':    'Fork Guide Card',
        'purpose':  'Someone scanned a physical card about the $5 fork guide',
        'url':      'https://meekotharaccoon-cell.github.io/meeko-nerve-center/consent.html?src=fork_guide',
        'action':   'Download the $5 fork guide and start your own system',
    },
    {
        'id':       'gaza_rose',
        'label':    'Gaza Rose Art Print',
        'purpose':  'Someone scanned a Gaza Rose art print or postcard',
        'url':      'https://meekotharaccoon-cell.github.io/meeko-nerve-center/consent.html?src=gaza_rose',
        'action':   'See the Gaza Rose gallery and support Palestinian children',
    },
    {
        'id':       'solarpunk',
        'label':    'SolarPunk Dashboard Sticker',
        'purpose':  'Someone scanned a SolarPunk sticker',
        'url':      'https://meekotharaccoon-cell.github.io/meeko-nerve-center/consent.html?src=solarpunk',
        'action':   'See the live SolarPunk Information Commons dashboard',
    },
    {
        'id':       'nerve_center',
        'label':    'Nerve Center Business Card',
        'purpose':  'Someone scanned the main nerve center card',
        'url':      'https://meekotharaccoon-cell.github.io/meeko-nerve-center/consent.html?src=nerve_center',
        'action':   'Fork the entire Meeko Nerve Center system',
    },
]

QR_API = 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&format=png&data='

def generate_qr(destination):
    """Download QR code image for a destination URL."""
    url = QR_API + urllib_request.quote(destination['url'])
    out = PUBLIC / 'qr' / f"{destination['id']}.png"
    
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=15) as r:
            out.write_bytes(r.read())
        print(f'[qr] Generated: {out.name} -> {destination["url"]}')
        return str(out)
    except Exception as e:
        print(f'[qr] Failed {destination["id"]}: {e}')
        return None

def build_consent_page():
    """Build the consent landing page.
    
    This is the most important page in the system.
    It is the ONLY place where a human decision gate exists.
    Yes = proceed. No = full stop + graceful thank you + data scrub.
    """
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hey! Quick question.</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Georgia', serif;
      background: #1a1a2e;
      color: #e8e0d5;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }
    .card {
      max-width: 480px;
      width: 100%;
      background: #16213e;
      border-radius: 16px;
      padding: 2.5rem;
      border: 1px solid #0f3460;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    .eyebrow {
      font-size: 0.75rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: #7eb8a4;
      margin-bottom: 1rem;
    }
    h1 {
      font-size: 1.8rem;
      line-height: 1.3;
      margin-bottom: 1rem;
      color: #f0e6d3;
    }
    .context {
      font-size: 0.95rem;
      line-height: 1.7;
      color: #b8a898;
      margin-bottom: 2rem;
    }
    .what-happens {
      background: #0f3460;
      border-radius: 10px;
      padding: 1.2rem;
      margin-bottom: 2rem;
      font-size: 0.9rem;
      line-height: 1.6;
      color: #c8d8e8;
    }
    .what-happens strong { color: #7eb8a4; }
    .privacy-note {
      font-size: 0.8rem;
      color: #6a8a7a;
      margin-bottom: 2rem;
      line-height: 1.6;
    }
    .buttons { display: flex; gap: 1rem; flex-wrap: wrap; }
    .btn {
      flex: 1;
      min-width: 140px;
      padding: 1rem 1.5rem;
      border-radius: 10px;
      font-size: 1rem;
      cursor: pointer;
      border: none;
      font-family: inherit;
      transition: all 0.2s;
    }
    .btn-yes {
      background: #7eb8a4;
      color: #1a1a2e;
      font-weight: bold;
    }
    .btn-yes:hover { background: #9ecab8; transform: translateY(-1px); }
    .btn-no {
      background: transparent;
      color: #b8a898;
      border: 1px solid #3a4a5a;
    }
    .btn-no:hover { border-color: #7eb8a4; color: #c8d8c8; }
    .response { display: none; text-align: center; padding: 2rem 0; }
    .response h2 { font-size: 1.5rem; margin-bottom: 1rem; }
    .response p { color: #b8a898; line-height: 1.7; }
    .scrub-note {
      font-size: 0.75rem;
      color: #4a6a5a;
      margin-top: 1.5rem;
    }
  </style>
</head>
<body>
  <div class="card">
    <div id="question">
      <div class="eyebrow">Meeko Nerve Center</div>
      <h1>Hey. Can I show you something?</h1>
      <div class="context" id="context-text">
        You scanned a QR code on something physical.<br>
        Before anything happens, I want to ask you directly.
      </div>
      <div class="what-happens">
        <strong>If you say yes:</strong><br>
        <span id="action-text">You\'ll be taken to the Meeko Nerve Center — an open, free, self-replicating humanitarian AI system. No account needed.</span>
      </div>
      <div class="privacy-note">
        ⚪️ Your scan data is used only to get you where you\'re going.<br>
        ⚪️ We don\'t track you, store your device info, or share anything.<br>
        ⚪️ After you choose, any session data is scrubbed. Gone. Forever.
      </div>
      <div class="buttons">
        <button class="btn btn-yes" onclick="handleYes()">Yeah, show me →</button>
        <button class="btn btn-no" onclick="handleNo()">No thanks</button>
      </div>
    </div>
    <div class="response" id="yes-response">
      <h2>Let\'s go. ἳf</h2>
      <p>Taking you there now...</p>
      <p class="scrub-note">✓ Session data scrubbed.</p>
    </div>
    <div class="response" id="no-response">
      <h2>Yeah, no problem!</h2>
      <p style="font-size:1.3rem; margin-bottom:1rem;">Thanks for being <strong>YOU</strong>.</p>
      <p>Seriously. The world is better with you in it, exactly as you are.</p>
      <p class="scrub-note">✓ Session data scrubbed. Nothing stored.</p>
    </div>
  </div>

  <script>
    // Read source from URL param
    const params = new URLSearchParams(window.location.search);
    const src = params.get(\'src\') || \'nerve_center\';
    
    const destinations = {
      fork_guide:   { action: \'Download the $5 fork guide and start your own system\', url: \'https://meekotharaccoon-cell.github.io/meeko-nerve-center/\' },
      gaza_rose:    { action: \'See the Gaza Rose gallery and support Palestinian children\', url: \'https://meekotharaccoon-cell.github.io/meeko-nerve-center/\' },
      solarpunk:    { action: \'See the live SolarPunk Information Commons dashboard\', url: \'https://meekotharaccoon-cell.github.io/meeko-nerve-center/solarpunk.html\' },
      nerve_center: { action: \'Fork the entire Meeko Nerve Center — free, open, yours\', url: \'https://github.com/meekotharaccoon-cell/meeko-nerve-center\' },
    };
    
    const dest = destinations[src] || destinations.nerve_center;
    document.getElementById(\'action-text\').textContent = dest.action;
    
    function scrubSession() {
      // Clear everything we can from the browser
      try { sessionStorage.clear(); } catch(e) {}
      try { localStorage.clear(); } catch(e) {}
      // Remove URL params
      history.replaceState(null, \'\', window.location.pathname);
    }
    
    function handleYes() {
      document.getElementById(\'question\').style.display = \'none\';
      document.getElementById(\'yes-response\').style.display = \'block\';
      scrubSession();
      setTimeout(() => { window.location.href = dest.url; }, 1200);
    }
    
    function handleNo() {
      document.getElementById(\'question\').style.display = \'none\';
      document.getElementById(\'no-response\').style.display = \'block\';
      scrubSession();
      // Nothing else happens. Full stop. Graceful exit.
    }
  </script>
</body>
</html>'''
    
    (PUBLIC / 'consent.html').write_text(html)
    print('[qr] consent.html built')

def run():
    print(f'[qr] QR Propagator — {TODAY}')
    
    manifest = {'date': TODAY, 'qr_codes': []}
    
    for dest in QR_DESTINATIONS:
        path = generate_qr(dest)
        manifest['qr_codes'].append({
            **dest,
            'qr_image': f'public/qr/{dest["id"]}.png',
            'generated': TODAY,
        })
    
    (DATA / 'qr_manifest.json').write_text(json.dumps(manifest, indent=2))
    build_consent_page()
    
    print(f'[qr] {len(manifest["qr_codes"])} QR codes generated')
    print(f'[qr] Consent page: public/consent.html')
    print(f'[qr] Print-ready QR images: public/qr/')
    
    return manifest

if __name__ == '__main__':
    run()
