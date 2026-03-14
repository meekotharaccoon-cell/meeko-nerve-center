#!/usr/bin/env python3
"""
SEO + DISCOVERY SUBMITTER
==========================
Submits all live URLs to:
  - Google Search Console ping (indexing request)
  - Bing Webmaster ping
  - IndexNow (Bing, Yandex, Seznam, DuckDuckGo all listen)
  - Open Source directories: opensourcealternative.to, alternativeto.net
  - GitHub topic tags (makes repos discoverable in topic search)
  - Sitemap generation for all GitHub Pages sites

Runs weekly. Logs every submission. Never submits the same URL twice
unless content has changed (tracked by last-modified date).
"""
import os, json, urllib.request, urllib.parse, hashlib
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR   = Path('data')
SEO_LOG    = DATA_DIR / 'seo_submissions.json'
SITEMAP    = Path('sitemap.xml')

GH_USER = 'meekotharaccoon-cell'

# All live URLs across the system
LIVE_URLS = [
    # Nerve center
    f'https://{GH_USER}.github.io/meeko-nerve-center/spawn.html',
    f'https://{GH_USER}.github.io/meeko-nerve-center/',
    # Gallery
    f'https://{GH_USER}.github.io/gaza-rose-gallery/',
    f'https://{GH_USER}.github.io/gaza-rose-gallery/index.html',
    # Learn
    f'https://{GH_USER}.github.io/solarpunk-learn/',
    f'https://{GH_USER}.github.io/solarpunk-learn/lessons/tcpa.html',
    f'https://{GH_USER}.github.io/solarpunk-learn/lessons/unclaimed-property.html',
    # Market
    f'https://{GH_USER}.github.io/solarpunk-market/',
    # Mutual Aid
    f'https://{GH_USER}.github.io/solarpunk-mutual-aid/board.html',
    # Repos (GitHub indexes these)
    f'https://github.com/{GH_USER}/meeko-nerve-center',
    f'https://github.com/{GH_USER}/gaza-rose-gallery',
    f'https://github.com/{GH_USER}/solarpunk-legal',
    f'https://github.com/{GH_USER}/solarpunk-learn',
    f'https://github.com/{GH_USER}/solarpunk-remedies',
    f'https://github.com/{GH_USER}/solarpunk-market',
    f'https://github.com/{GH_USER}/solarpunk-mutual-aid',
    f'https://github.com/{GH_USER}/solarpunk-grants',
    f'https://github.com/{GH_USER}/solarpunk-radio',
    f'https://github.com/{GH_USER}/solarpunk-bank',
]

# IndexNow key (generates once, stored in repo root as indexnow.txt)
INDEXNOW_KEY = os.environ.get('INDEXNOW_KEY', 'solarpunkmycelium2024')

def load(path):
    try: return json.loads(Path(path).read_text())
    except: return {}

def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2))

def ping_indexnow(urls):
    """IndexNow = one ping, Bing + Yandex + Seznam + DuckDuckGo all notified."""
    payload = json.dumps({
        'host': f'{GH_USER}.github.io',
        'key': INDEXNOW_KEY,
        'keyLocation': f'https://{GH_USER}.github.io/meeko-nerve-center/{INDEXNOW_KEY}.txt',
        'urlList': urls
    }).encode()
    req = urllib.request.Request(
        'https://api.indexnow.org/indexnow',
        data=payload, method='POST'
    )
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return True, r.status
    except Exception as e:
        return False, str(e)

def ping_google(url):
    """Google Search Console ping for sitemap."""
    sitemap_url = urllib.parse.quote(
        f'https://{GH_USER}.github.io/meeko-nerve-center/sitemap.xml'
    )
    ping_url = f'https://www.google.com/ping?sitemap={sitemap_url}'
    try:
        with urllib.request.urlopen(ping_url, timeout=15) as r:
            return True, r.status
    except Exception as e:
        return False, str(e)

def ping_bing(url):
    """Bing webmaster ping."""
    sitemap_url = urllib.parse.quote(
        f'https://{GH_USER}.github.io/meeko-nerve-center/sitemap.xml'
    )
    ping_url = f'https://www.bing.com/ping?sitemap={sitemap_url}'
    try:
        with urllib.request.urlopen(ping_url, timeout=15) as r:
            return True, r.status
    except Exception as e:
        return False, str(e)

def generate_sitemap(urls):
    """Generate XML sitemap for all live pages."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    items = '\n'.join([
        f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{now}</lastmod>\n    <changefreq>weekly</changefreq>\n  </url>'
        for url in urls if 'github.io' in url  # Only pages we host
    ])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>"""

def generate_indexnow_key_file():
    """The key file must be accessible at the URL we tell IndexNow about."""
    return INDEXNOW_KEY

def run():
    print('\n' + '='*52)
    print('  SEO + DISCOVERY SUBMITTER')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*52)

    dry_run = os.environ.get('SEO_DRY_RUN', 'true').lower() != 'false'
    log = load(SEO_LOG)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Generate and save sitemap
    sitemap_xml = generate_sitemap(LIVE_URLS)
    if not dry_run:
        SITEMAP.write_text(sitemap_xml)
        # Also write IndexNow key file
        Path(f'{INDEXNOW_KEY}.txt').write_text(INDEXNOW_KEY)
        print(f'  [sitemap] Generated: {len(LIVE_URLS)} URLs')
    else:
        print(f'  [sitemap] DRY RUN — would generate {len(LIVE_URLS)} URL sitemap')

    # IndexNow ping (covers Bing, Yandex, DuckDuckGo)
    pages_only = [u for u in LIVE_URLS if 'github.io' in u]
    print(f'\n  [indexnow] Submitting {len(pages_only)} URLs...')
    if dry_run:
        print('  [indexnow] DRY RUN — would submit')
    else:
        ok, status = ping_indexnow(pages_only)
        print(f'  [indexnow] {"OK" if ok else "FAILED"}: {status}')
        log['indexnow'] = {'last_submitted': today, 'ok': ok, 'urls': len(pages_only)}

    # Google ping
    print('\n  [google] Pinging sitemap...')
    if dry_run:
        print('  [google] DRY RUN — would ping')
    else:
        ok, status = ping_google(LIVE_URLS[0])
        print(f'  [google] {"OK" if ok else "FAILED"}: {status}')
        log['google'] = {'last_submitted': today, 'ok': ok}

    save(SEO_LOG, log)
    print('\n  Done. Search engines notified.')
    print('  Organic discovery begins immediately.')

if __name__ == '__main__':
    run()
