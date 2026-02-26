#!/usr/bin/env python3
"""
RSS / Atom Feed Generator
==========================
Generates a live RSS feed from all system outputs.
Anyone can subscribe in any RSS reader. No social media needed.

Feeds generated:
  public/feed.xml       - main feed (all content)
  public/news.xml       - humanitarian updates only
  public/tech.xml       - technical posts only

Feed readers that work: Feedly, NewsBlur, Inoreader, Miniflux,
Newsboat (terminal), NetNewsWire (Mac), any podcast app.

Subscribers get every post automatically, forever, for free.
"""

import json, datetime, html
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT    = Path(__file__).parent.parent
PUBLIC  = ROOT / 'public'
CONTENT = ROOT / 'content'
PUBLIC.mkdir(exist_ok=True)

SITE_URL  = 'https://meekotharaccoon-cell.github.io/meeko-nerve-center'
GAL_URL   = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'
REPO_URL  = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'
TITLE     = 'Meeko Nerve Center'
DESCRIPTION = 'Autonomous humanitarian AI system. Daily updates on Gaza, Sudan, Congo. Open source. $0/month.'

def rss_date(d=None):
    dt = d or datetime.datetime.utcnow()
    return dt.strftime('%a, %d %b %Y %H:%M:%S +0000')

def collect_items():
    """Collect all content items from the system."""
    items = []

    # Newsletter
    nl_dir = CONTENT / 'newsletter'
    if nl_dir.exists():
        for f in sorted(nl_dir.glob('*.md')):
            if 'latest' in f.name: continue
            try:
                text  = f.read_text(encoding='utf-8')
                title = text.split('\n')[0].lstrip('# ').strip()
                date  = f.stem.replace('-', ' ')  # rough date from filename
                items.append({
                    'title':   title or f'Newsletter {f.stem}',
                    'link':    f'{SITE_URL}/content/newsletter/{f.name}',
                    'desc':    text[:500].strip(),
                    'date':    rss_date(),
                    'type':    'newsletter',
                    'guid':    f'newsletter-{f.stem}',
                })
            except: pass

    # Content archive
    arch_dir = CONTENT / 'archive'
    if arch_dir.exists():
        for f in sorted(arch_dir.glob('*.md'), reverse=True)[:14]:
            try:
                text  = f.read_text(encoding='utf-8')
                title = f'Daily Posts {f.stem}'
                items.append({
                    'title':   title,
                    'link':    f'{SITE_URL}/content/archive/{f.name}',
                    'desc':    text[:500].strip(),
                    'date':    rss_date(),
                    'type':    'posts',
                    'guid':    f'archive-{f.stem}',
                })
            except: pass

    # YouTube shorts scripts
    yt_dir = CONTENT / 'youtube'
    if yt_dir.exists():
        for f in sorted(yt_dir.glob('*.md'), reverse=True)[:7]:
            if 'latest' in f.name: continue
            try:
                text  = f.read_text(encoding='utf-8')
                title = f'Video Scripts {f.stem}'
                items.append({
                    'title':   title,
                    'link':    f'{SITE_URL}/content/youtube/{f.name}',
                    'desc':    text[:300].strip(),
                    'date':    rss_date(),
                    'type':    'video',
                    'guid':    f'yt-{f.stem}',
                })
            except: pass

    # Static items (always present)
    items += [
        {
            'title': 'Gaza Rose Gallery - $1 art, 70% to PCRF',
            'link':  GAL_URL,
            'desc':  '56 original artworks. $1 each. 70% of every sale goes to the Palestine Children\'s Relief Fund (4-star Charity Navigator).',
            'date':  rss_date(),
            'type':  'humanitarian',
            'guid':  'gallery-static',
        },
        {
            'title': 'Fork This System - $5 guide to build your own',
            'link':  f'{REPO_URL}/blob/main/products/fork-guide.md',
            'desc':  'Full guide to forking this system and aiming it at any cause. Python, GitHub Actions, GitHub Pages. $0/month to run.',
            'date':  rss_date(),
            'type':  'tech',
            'guid':  'fork-guide-static',
        },
    ]

    return items

def build_rss(items, filter_type=None):
    filtered = [i for i in items if filter_type is None or i['type'] == filter_type]

    rss  = ET.Element('rss', version='2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    chan = ET.SubElement(rss, 'channel')

    type_label = f' ({filter_type})' if filter_type else ''
    ET.SubElement(chan, 'title').text = TITLE + type_label
    ET.SubElement(chan, 'link').text  = SITE_URL
    ET.SubElement(chan, 'description').text = DESCRIPTION
    ET.SubElement(chan, 'language').text    = 'en-us'
    ET.SubElement(chan, 'lastBuildDate').text = rss_date()
    atom_link = ET.SubElement(chan, 'atom:link')
    atom_link.set('href', f'{SITE_URL}/feed.xml')
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')

    for item in filtered[:20]:  # RSS best practice: max 20 items
        it = ET.SubElement(chan, 'item')
        ET.SubElement(it, 'title').text       = html.escape(item['title'])
        ET.SubElement(it, 'link').text        = item['link']
        ET.SubElement(it, 'description').text = html.escape(item['desc'])
        ET.SubElement(it, 'pubDate').text     = item['date']
        ET.SubElement(it, 'guid').text        = f'{SITE_URL}/guid/{item["guid"]}'

    return ET.tostring(rss, encoding='unicode', xml_declaration=False)

def run():
    items = collect_items()
    print(f'[rss] Collected {len(items)} items')

    # Main feed
    main_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + build_rss(items)
    (PUBLIC / 'feed.xml').write_text(main_xml, encoding='utf-8')
    print(f'[rss] Written: public/feed.xml ({len(items)} items)')

    # Humanitarian feed
    hum_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + build_rss(items, 'humanitarian')
    (PUBLIC / 'humanitarian.xml').write_text(hum_xml, encoding='utf-8')
    print(f'[rss] Written: public/humanitarian.xml')

    # Tech feed
    tech_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + build_rss(items, 'tech')
    (PUBLIC / 'tech.xml').write_text(tech_xml, encoding='utf-8')
    print(f'[rss] Written: public/tech.xml')

    print(f'[rss] Subscribe: {SITE_URL}/feed.xml')

if __name__ == '__main__':
    run()
