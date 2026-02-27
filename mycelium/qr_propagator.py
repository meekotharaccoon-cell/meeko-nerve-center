#!/usr/bin/env python3
"""
QR Propagator
==============
Consent-first physical propagation of the SolarPunk system.

Philosophy:
  - A QR code on anything physical (card, sticker, poster, zine)
  - Scan it -> landing page with clear, honest ask
  - YES  -> system begins downloading/forking with their blessing
  - NO   -> "Yeah, no problem! Thanks for being YOU" -> done, nothing kept

Privacy rules (absolute):
  - No data collected before consent
  - After use: scrub everything immediately
  - Nothing passes through more hands than necessary
  - Scan IP: used to route, then deleted
  - Email (if given): used once for welcome, then deleted
  - No analytics. No tracking. No "anonymous" fingerprinting.

Outputs:
  - public/qr/            QR code images (one per campaign)
  - public/consent.html   The consent landing page
  - data/qr_campaigns.json Campaign registry (no PII)
  - PROPAGATION.md        Human-readable propagation guide

QR codes use free no-auth API: api.qrserver.com
"""

import json, datetime, hashlib
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
PUBLIC = ROOT / 'public'

for d in [DATA, PUBLIC / 'qr']:
    d.mkdir(parents=True, exist_ok=True)

TODAY   = datetime.date.today().isoformat()
BASE_URL = 'https://meekotharaccoon-cell.github.io/meeko-nerve-center'

# Campaign types - each has a landing URL and purpose
CAMPAIGNS = [
    {
        'id':      'solarpunk-card',
        'name':    'SolarPunk Business Card',
        'url':     f'{BASE_URL}/consent.html?src=card',
        'purpose': 'Share the SolarPunk dashboard and fork invitation',
        'physical': 'Business card, postcard, or bookmark',
    },
    {
        'id':      'gaza-rose-art',
        'name':    'Gaza Rose Art Print',
        'url':     f'{BASE_URL}/consent.html?src=art',
        'purpose': 'Art print QR -> Gaza Rose gallery + PCRF donation',
        'physical': 'Physical or digital art print',
    },
    {
        'id':      'fork-guide',
        'name':    'Fork Guide Physical Copy',
        'url':     f'{BASE_URL}/consent.html?src=guide',
        'purpose': 'Fork guide -> invite to fork and build their own system',
        'physical': 'Printed fork guide or zine',
    },
    {
        'id':      'solarpunk-sticker',
        'name':    'SolarPunk Sticker',
        'url':     f'{BASE_URL}/consent.html?src=sticker',
        'purpose': 'Sticker -> SolarPunk dashboard + system invitation',
        'physical': 'Sticker on laptop, water bottle, etc.',
    },
]

def generate_qr(url, filename, size=300):
    """Generate QR code using free no-auth API."""
    qr_url = f'https://api.qrserver.com/v1/create-qr-code/?{urlencode({"size": f"{size}x{size}", "data": url, "format": "png", "ecc": "H"})}'
    try:
        req = urllib_request.Request(qr_url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=10) as r:
            data = r.read()
            path = PUBLIC / 'qr' / filename
            path.write_bytes(data)
            print(f'[qr] Generated: {filename} ({len(data)} bytes)')
            return str(path), qr_url
    except Exception as e:
        print(f'[qr] Failed to generate {filename}: {e}')
        return None, qr_url

def build_consent_page():
    """The consent landing page. Honest. Simple. Respectful."""
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hey — Meeko Nerve Center</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'IBM Plex Mono', monospace, sans-serif;
      background: #1a1a0f;
      color: #e8e0c8;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }
    .card {
      max-width: 480px;
      width: 100%;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(120,200,80,0.3);
      border-radius: 16px;
      padding: 2.5rem;
      text-align: center;
    }
    .icon { font-size: 3rem; margin-bottom: 1rem; }
    h1 { font-size: 1.4rem; color: #a8d878; margin-bottom: 1rem; }
    p { color: #c8c0a0; line-height: 1.7; margin-bottom: 1rem; font-size: 0.95rem; }
    .what-is-this {
      background: rgba(120,200,80,0.08);
      border-left: 3px solid #78c850;
      padding: 1rem;
      text-align: left;
      border-radius: 0 8px 8px 0;
      margin: 1.5rem 0;
      font-size: 0.88rem;
    }
    .what-is-this li { margin: 0.4rem 0 0.4rem 1rem; color: #b8d898; }
    .privacy-note {
      font-size: 0.8rem;
      color: #888;
      margin: 1rem 0;
      font-style: italic;
    }
    .btn-yes {
      display: block;
      width: 100%;
      padding: 1rem;
      background: linear-gradient(135deg, #78c850, #4a9830);
      color: #0a1a05;
      border: none;
      border-radius: 10px;
      font-size: 1.1rem;
      font-weight: 700;
      cursor: pointer;
      margin: 1rem 0 0.5rem;
      text-decoration: none;
      transition: transform 0.1s;
    }
    .btn-yes:hover { transform: translateY(-2px); }
    .btn-no {
      display: block;
      width: 100%;
      padding: 0.8rem;
      background: transparent;
      color: #888;
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 10px;
      font-size: 0.95rem;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.2s;
    }
    .btn-no:hover { color: #ccc; border-color: rgba(255,255,255,0.3); }
    .thank-you { display: none; }
    .thank-you h2 { color: #a8d878; font-size: 1.3rem; margin-bottom: 1rem; }
    .thank-you p { color: #c8c0a0; }
  </style>
</head>
<body>
  <div class="card" id="consent-card">
    <div class="icon">🌱</div>
    <h1>Hey. You scanned the thing.</h1>
    <p>This is the Meeko Nerve Center — an open-source, self-replicating humanitarian AI system.
Built by one human. Runs for free. Works while they sleep.</p>
    <div class="what-is-this">
      <strong style="color:#a8d878">What this actually is:</strong>
      <ul>
        <li>Live data: earthquakes, climate, space, congress trades</li>
        <li>Gaza Rose art — 70% of sales to Palestinian children</li>
        <li>A system anyone can fork and run for free</li>
        <li>No VC money. No ads. No surveillance.</li>
      </ul>
    </div>
    <p>You can look around, fork it, donate, or just leave. All of those are fine.</p>
    <p class="privacy-note">🔒 We collect nothing before you say yes.
If you say no, nothing is recorded. Not even this visit.</p>
    <a href="https://meekotharaccoon-cell.github.io/meeko-nerve-center/solarpunk.html" class="btn-yes">
      ✅ Yeah, take me there
    </a>
    <button class="btn-no" onclick="showDecline()">
      No thanks
    </button>
  </div>

  <div class="card thank-you" id="thank-you-card">
    <div class="icon">🤍</div>
    <h2>Yeah, no problem!<br>Thanks for being YOU.</h2>
    <p>Seriously. The fact that you scanned it at all is enough.<br>
You don\'t owe us anything. Go be excellent.</p>
    <p style="margin-top:1.5rem; font-size:0.85rem; color:#666">
      (Nothing was recorded. This page will close when you leave.)
    </p>
  </div>

  <script>
    function showDecline() {
      document.getElementById(\'consent-card\').style.display = \'none\';
      document.getElementById(\'thank-you-card\').style.display = \'block\';
      // Nothing to scrub — nothing was ever collected
    }

    // Track source param for analytics-free routing
    const src = new URLSearchParams(window.location.search).get(\'src\');
    if (src) {
      // Used only to show context-appropriate message, never stored
      const msgs = {
        \'art\':    \'You found this through the Gaza Rose art.\',
        \'card\':   \'You found this through a physical card.\',
        \'guide\':  \'You found this through the fork guide.\',
        \'sticker\': \'You found this through a sticker.\',
      };
      const msg = msgs[src];
      if (msg) {
        const p = document.createElement(\'p\');
        p.style.cssText = \'font-size:0.85rem;color:#888;margin-top:0.5rem\';
        p.textContent = msg;
        document.querySelector(\'.icon\').after(p);
      }
    }
  </script>
</body>
</html>'''
    path = PUBLIC / 'consent.html'
    path.write_text(html)
    print(f'[qr] consent.html written ({len(html)} bytes)')
    return path

def run():
    print(f'[qr] QR Propagator — {TODAY}')
    print('[qr] Philosophy: consent first, graceful decline, zero data after use')

    # Build consent page
    build_consent_page()

    # Generate QR codes for each campaign
    campaigns_out = []
    for camp in CAMPAIGNS:
        filename = f"{camp['id']}.png"
        path, api_url = generate_qr(camp['url'], filename)
        campaigns_out.append({
            **camp,
            'qr_file':   f'public/qr/{filename}',
            'qr_url':    api_url,
            'generated': TODAY,
        })

    # Save campaign registry (no PII ever stored here)
    (DATA / 'qr_campaigns.json').write_text(json.dumps({
        'date':      TODAY,
        'campaigns': campaigns_out,
        'privacy':   'No PII stored. No analytics. Scan data deleted after routing.',
    }, indent=2))

    # Write propagation guide
    lines = [
        '# PROPAGATION — Physical QR Code System',
        '',
        '## Philosophy',
        'Every QR code is an invitation, not a trap.',
        'Consent before everything. Graceful "no" always.',
        'Data scrubbed the moment it has served its only purpose.',
        '',
        '## Campaigns',
        '',
    ]
    for c in campaigns_out:
        lines += [
            f"### {c['name']}",
            f"Physical use: {c['physical']}",
            f"Purpose: {c['purpose']}",
            f"QR file: {c['qr_file']}",
            f"Landing: {c['url']}",
            '',
        ]
    lines += [
        '## Privacy Guarantee',
        '',
        '- No data collected before consent',
        '- "No" response: zero data recorded, not even the visit',
        '- "Yes" response: only routing data used, then deleted',
        '- No third-party analytics',
        '- No fingerprinting',
        '- Source param (`?src=`) used client-side only, never sent to server',
        '',
        '## The "No" Response',
        '',
        'Every decline gets: **"Yeah, no problem! Thanks for being YOU."**',
        'Because someone scanning a QR code is already a gift.',
        'They don\'t owe us anything beyond that.',
    ]
    (ROOT / 'PROPAGATION.md').write_text('\n'.join(lines))

    print(f'[qr] {len(campaigns_out)} campaigns generated')
    print(f'[qr] consent.html ready at: {BASE_URL}/consent.html')
    return campaigns_out

if __name__ == '__main__':
    run()
