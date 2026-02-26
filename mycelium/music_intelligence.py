#!/usr/bin/env python3
"""
Music Intelligence
===================
MusicBrainz + iTunes Search -> music that resonates with the mission.

Use cases:
  - Find music about Palestine, resistance, hope, climate
  - Generate 'music for the cause' content posts
  - Surface artists worth amplifying
  - Background research for YouTube video mood/tone
  - Find music with open/Creative Commons licenses

Both APIs: free, no auth.
"""

import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
KB    = ROOT / 'knowledge'
DATA  = ROOT / 'data'
CONT  = ROOT / 'content' / 'queue'

for d in [KB / 'music', DATA, CONT]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()

MISSION_SEARCHES = [
    'Palestine',
    'resistance',
    'solidarity',
    'protest',
    'freedom',
]

ITUNES_SEARCHES = [
    'protest music',
    'world music peace',
    'Palestinian music',
]

def fetch_json(url, timeout=12):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[music] fetch error: {e}')
        return None

def search_musicbrainz(query):
    url = f'https://musicbrainz.org/ws/2/artist/?query={urllib_request.quote(query)}&fmt=json&limit=5'
    data = fetch_json(url)
    if not data: return []
    
    artists = []
    for a in data.get('artists', []):
        artists.append({
            'name':    a.get('name', ''),
            'country': a.get('country', ''),
            'tags':    [t['name'] for t in a.get('tags', [])[:5]],
            'score':   a.get('score', 0),
            'url':     f"https://musicbrainz.org/artist/{a.get('id', '')}",
            'query':   query,
        })
    return artists

def search_itunes(query):
    url = f'https://itunes.apple.com/search?term={urllib_request.quote(query)}&entity=musicTrack&limit=5'
    data = fetch_json(url)
    if not data: return []
    
    tracks = []
    for t in data.get('results', []):
        tracks.append({
            'title':   t.get('trackName', ''),
            'artist':  t.get('artistName', ''),
            'album':   t.get('collectionName', ''),
            'genre':   t.get('primaryGenreName', ''),
            'preview': t.get('previewUrl', ''),
            'url':     t.get('trackViewUrl', ''),
            'query':   query,
        })
    return tracks

def run():
    print(f'[music] Music Intelligence \u2014 {TODAY}')
    
    all_artists = []
    for q in MISSION_SEARCHES[:3]:
        all_artists.extend(search_musicbrainz(q))
    
    all_tracks = []
    for q in ITUNES_SEARCHES[:2]:
        all_tracks.extend(search_itunes(q))
    
    print(f'[music] {len(all_artists)} artists, {len(all_tracks)} tracks')
    
    output = {'date': TODAY, 'artists': all_artists, 'tracks': all_tracks}
    (DATA / 'music.json').write_text(json.dumps(output, indent=2))
    
    # Content post
    if all_artists:
        top = [a for a in all_artists if a['score'] > 60][:5]
        if top:
            lines = ['Music that carries the message:\n']
            for a in top:
                country = f" ({a['country']})" if a['country'] else ''
                lines.append(f"\u2022 {a['name']}{country}")
            lines.append('\n#Music #WorldMusic #Palestine #Resistance #SoundForGood')
            post = [{'platform': 'mastodon', 'type': 'music', 'text': '\n'.join(lines)}]
            (CONT / f'music_{TODAY}.json').write_text(json.dumps(post, indent=2))
    
    # Digest
    lines = [f'# Music Intelligence \u2014 {TODAY}', '']
    if all_artists:
        lines += ['## Artists', '']
        for a in all_artists[:8]:
            tags = ', '.join(a['tags'][:3]) if a['tags'] else ''
            lines.append(f"- **{a['name']}** {a.get('country','')} | {tags}")
        lines.append('')
    
    (KB / 'music' / f'{TODAY}.md').write_text('\n'.join(lines))
    (KB / 'music' / 'latest.md').write_text('\n'.join(lines))
    
    print('[music] Done.')
    return output

if __name__ == '__main__':
    run()
