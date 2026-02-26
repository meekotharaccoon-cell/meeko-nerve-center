#!/usr/bin/env python3
"""
Open Library Reader
====================
Open Library API -> curated reading lists for the mission.

Use cases:
  - Find books about Palestine, humanitarian aid, SolarPunk, climate
  - Generate 'reading list' content posts (high engagement)
  - Feed the knowledge base with book summaries
  - Surface FREE ebooks available on Internet Archive

No auth. No cost. 20M+ books.
"""

import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
KB    = ROOT / 'knowledge'
DATA  = ROOT / 'data'
CONT  = ROOT / 'content' / 'queue'

for d in [KB / 'books', DATA, CONT]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()

MISSION_SEARCHES = [
    'Palestine history',
    'humanitarian aid',
    'solarpunk fiction',
    'climate justice',
    'open source technology',
    'Gaza',
    'refugee crisis',
    'blockchain society',
    'digital rights',
    'mutual aid',
]

def fetch_json(url, timeout=12):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[books] fetch error: {e}')
        return None

def search_books(query, limit=5):
    url = f'https://openlibrary.org/search.json?q={urllib_request.quote(query)}&limit={limit}&fields=key,title,author_name,first_publish_year,subject,ia,availability'
    data = fetch_json(url)
    if not data: return []
    
    books = []
    for doc in data.get('docs', []):
        has_ebook = bool(doc.get('ia'))  # Internet Archive = free to read
        books.append({
            'title':    doc.get('title', ''),
            'authors':  doc.get('author_name', [])[:2],
            'year':     doc.get('first_publish_year'),
            'subjects': doc.get('subject', [])[:5],
            'free':     has_ebook,
            'url':      f"https://openlibrary.org{doc.get('key', '')}",
            'read_url': f"https://archive.org/details/{doc['ia'][0]}" if doc.get('ia') else None,
            'query':    query,
        })
    return books

def run():
    print(f'[books] Open Library Reader \u2014 {TODAY}')
    
    all_books = []
    for query in MISSION_SEARCHES[:5]:  # limit requests
        print(f'[books] Searching: {query}')
        books = search_books(query)
        all_books.extend(books)
    
    # Deduplicate by title
    seen = set()
    unique = []
    for b in all_books:
        if b['title'] not in seen:
            seen.add(b['title'])
            unique.append(b)
    
    free_books = [b for b in unique if b['free']]
    print(f'[books] {len(unique)} books found, {len(free_books)} free to read')
    
    # Save
    (DATA / 'books.json').write_text(json.dumps({'date': TODAY, 'books': unique, 'free': free_books}, indent=2))
    
    # Generate reading list post
    if free_books:
        top = free_books[:5]
        lines = ['Free books on Palestine, climate justice, and open tech:\n']
        for b in top:
            authors = ', '.join(b['authors']) if b['authors'] else 'Unknown'
            lines.append(f"\u2022 *{b['title']}* \u2014 {authors}")
            if b['read_url']: lines.append(f"  Read free: {b['read_url']}")
        lines.append('\n#Books #FreeCulture #Palestine #ClimateJustice #OpenAccess')
        
        post = [{'platform': 'mastodon', 'type': 'reading_list', 'text': '\n'.join(lines)}]
        (CONT / f'books_{TODAY}.json').write_text(json.dumps(post, indent=2))
    
    # Knowledge digest
    lines = [f'# Mission Reading List \u2014 {TODAY}', '', f'{len(unique)} books | {len(free_books)} free on Internet Archive', '']
    for b in unique[:10]:
        free_tag = ' \ud83d\udcd6 FREE' if b['free'] else ''
        lines.append(f"- **{b['title']}** ({b['year']}) \u2014 {', '.join(b['authors'][:1])}{free_tag}")
        if b['read_url']: lines.append(f"  {b['read_url']}")
    
    (KB / 'books' / f'{TODAY}.md').write_text('\n'.join(lines))
    (KB / 'books' / 'latest.md').write_text('\n'.join(lines))
    
    print(f'[books] Done.')
    return {'books': unique, 'free': free_books}

if __name__ == '__main__':
    run()
