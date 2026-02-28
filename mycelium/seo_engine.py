#!/usr/bin/env python3
"""
SEO Engine
===========
Makes the system discoverable by search engines.

Generates:
  1. sitemap.xml (tells Google/Bing what pages exist)
  2. robots.txt  (tells crawlers what to index)
  3. Meta tags injection into index.html (already in dashboard)
  4. A blog-style /posts/ page with accountability content
     (each congressional trade = a page Google can index)
  5. Schema.org structured data (makes results rich snippets)
  6. Submits sitemap to Google Search Console ping endpoint

Target search queries this system should rank for:
  - "congressional insider trading tracker"
  - "STOCK Act violations"
  - "Palestinian solidarity open source"
  - "autonomous AI GitHub Actions"
  - "free AI that evolves itself"
  - "Gaza Rose art"
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
PUBLIC = ROOT / 'public'

TODAY    = datetime.date.today().isoformat()
SITE_URL = 'https://meekotharaccoon-cell.github.io/meeko-nerve-center'

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def generate_sitemap(pages):
    urls = '\n'.join(
        f"""  <url>
    <loc>{SITE_URL}/{p}</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>daily</changefreq>
    <priority>{pr}</priority>
  </url>"""
        for p, pr in pages
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>"""

def generate_robots():
    return f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""

def generate_accountability_post(trade):
    """Generate an SEO-rich HTML page for a congressional trade."""
    member = trade.get('representative', trade.get('senator', 'Unknown Member'))
    ticker = trade.get('ticker', 'Unknown')
    date   = trade.get('transaction_date', trade.get('date', 'Unknown Date'))
    amount = trade.get('amount', trade.get('range', 'Unknown Amount'))
    slug   = f"{member.lower().replace(' ','-')}-{ticker.lower()}-{date}"

    return slug, f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{member} Traded {ticker} — STOCK Act Disclosure | Meeko Nerve Center</title>
  <meta name="description" content="{member} disclosed a trade of {ticker} ({amount}) on {date}. Public record under the STOCK Act. Tracked automatically by Meeko Nerve Center.">
  <meta property="og:title" content="{member} Traded {ticker} on {date}">
  <meta property="og:description" content="STOCK Act public disclosure. {amount}. Tracked automatically.">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{member} Traded {ticker} — STOCK Act Disclosure",
    "datePublished": "{date}",
    "author": {{"@type": "Organization", "name": "Meeko Nerve Center"}},
    "description": "Public congressional trade disclosure tracked under the STOCK Act."
  }}
  </script>
  <style>
    body {{ font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 1rem; background: #0d0d0d; color: #f0f0f0; }}
    h1 {{ color: #e74c3c; }}
    .meta {{ color: #888; font-size: 0.85rem; margin: 1rem 0; }}
    .data {{ background: #161616; border: 1px solid #2a2a2a; padding: 1rem; border-radius: 8px; }}
    a {{ color: #e74c3c; }}
    .back {{ margin-top: 2rem; }}
  </style>
</head>
<body>
  <h1>⚠️ {member}: {ticker}</h1>
  <div class="meta">STOCK Act Disclosure &mdash; Tracked by Meeko Nerve Center &mdash; {TODAY}</div>
  <div class="data">
    <p><strong>Member:</strong> {member}</p>
    <p><strong>Ticker:</strong> {ticker}</p>
    <p><strong>Transaction Date:</strong> {date}</p>
    <p><strong>Amount:</strong> {amount}</p>
    <p><strong>Source:</strong> <a href="https://efts.house.gov/LATEST/search-index?q=%22stock+act%22" target="_blank">House Financial Disclosures</a></p>
  </div>
  <p style="margin-top:1rem;color:#ccc">This is public record under the STOCK Act (Stop Trading on Congressional Knowledge Act).
  Members of Congress are required to disclose trades within 45 days.</p>
  <div class="back"><a href="{SITE_URL}/">← Back to Meeko Nerve Center</a></div>
</body>
</html>"""

def ping_search_engines(sitemap_url):
    """Ping Google and Bing to re-index after update."""
    endpoints = [
        f'https://www.google.com/ping?sitemap={sitemap_url}',
        f'https://www.bing.com/ping?sitemap={sitemap_url}',
    ]
    for url in endpoints:
        try:
            req = urllib_request.Request(url, headers={'User-Agent': 'meeko-seo/1.0'})
            with urllib_request.urlopen(req, timeout=10) as r:
                print(f'[seo] Pinged: {url[:60]} — {r.status}')
        except Exception as e:
            print(f'[seo] Ping failed {url[:60]}: {e}')

def run():
    print(f'\n[seo] SEO Engine — {TODAY}')
    PUBLIC.mkdir(exist_ok=True)
    posts_dir = PUBLIC / 'trades'
    posts_dir.mkdir(exist_ok=True)

    pages = [
        ('', '1.0'),             # homepage
        ('MANIFESTO.md', '0.8'), # manifesto
        ('DEPLOY.md', '0.7'),    # deploy guide
    ]

    # Generate trade pages
    congress = load(DATA / 'congress.json')
    trades   = congress if isinstance(congress, list) else congress.get('trades', [])
    for trade in trades[:20]:  # Top 20 trades get their own pages
        slug, html = generate_accountability_post(trade)
        try:
            (posts_dir / f'{slug}.html').write_text(html)
            pages.append((f'trades/{slug}.html', '0.6'))
        except: pass

    if trades:
        print(f'[seo] Generated {min(len(trades),20)} trade pages')

    # Write sitemap
    sitemap = generate_sitemap(pages)
    try:
        (PUBLIC / 'sitemap.xml').write_text(sitemap)
        print(f'[seo] sitemap.xml written ({len(pages)} URLs)')
    except Exception as e:
        print(f'[seo] Sitemap error: {e}')

    # Write robots.txt
    try:
        (PUBLIC / 'robots.txt').write_text(generate_robots())
        print('[seo] robots.txt written')
    except Exception as e:
        print(f'[seo] robots.txt error: {e}')

    # Ping search engines
    ping_search_engines(f'{SITE_URL}/sitemap.xml')

    print(f'[seo] Done. {len(pages)} pages indexed.')

if __name__ == '__main__':
    run()
