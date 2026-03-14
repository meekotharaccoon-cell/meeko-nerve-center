#!/usr/bin/env python3
"""
Art + Cause Generator
======================
Pairs free museum art (Art Institute of Chicago + Metropolitan Museum)
with your Gaza Rose / humanitarian mission content.

Outputs:
  - content/queue/art_cause_*.json   ready-to-post social content
  - knowledge/art/latest.md          art digest
  - data/art_pairs.json              artwork + message pairs

How it works:
  1. Pulls artworks from free museum APIs
  2. Filters for resonant themes (peace, resistance, suffering, hope, flowers)
  3. Pairs each artwork with a cause message
  4. Generates Instagram/Mastodon posts with image URL + text

This is your highest-quality visual content pipeline.
Museum art is copyright-free. Zero cost. High perceived value.
"""

import json, datetime, random
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
CONT  = ROOT / 'content' / 'queue'

for d in [DATA, KB / 'art', CONT]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()

# Themes that resonate with the Gaza Rose mission
THEME_KEYWORDS = [
    'flower', 'rose', 'garden', 'peace', 'dove', 'mother',
    'child', 'family', 'suffering', 'hope', 'light', 'sky',
    'resistance', 'freedom', 'portrait', 'hands', 'prayer',
    'grief', 'journey', 'refugee', 'displacement', 'home',
    'Palestine', 'Middle East', 'Arab', 'Islamic', 'Ottoman',
    'war', 'conflict', 'healing', 'community', 'solidarity',
    'olive', 'tree', 'earth', 'water', 'bread',
]

# Message templates paired with art
CAUSE_MESSAGES = [
    "Art has always documented what power tries to erase.\n\nThe Gaza Rose exists because beauty persists even in devastation.\n70% of proceeds to PCRF \u2192 link in bio",
    
    "Every flower painted in a time of war is an act of resistance.\n\nThe Gaza Rose gallery: meekotharaccoon-cell.github.io/meeko-nerve-center\n\n#GazaRose #Art #Palestine #Solidarity",
    
    "Museums preserve what humans almost destroyed.\nArtists preserve what war tries to silence.\n\nSupport Palestinian children surviving today:\nPCRF.net | Gaza Rose proceeds go directly there.",
    
    "This artwork survived centuries.\nChildren in Gaza deserve the same chance.\n\nGaza Rose art \u2192 70% to PCRF (Palestinian Children's Relief Fund)\n#ArtForGood #Palestine #GazaRose",
    
    "Art crosses every border.\nAid should too.\n\nThe Gaza Rose: art + action + transparency.\nSee where every dollar goes \u2192 link in bio",
    
    "What do flowers mean when painted in times of siege?\nEverything.\n\nThe Gaza Rose collection \u2014 each piece a message.\n#GazaRose #DigitalArt #PalestinianArt",
    
    "Museums collect art. We use it.\nBecause beauty without purpose is decoration.\nBeauty with purpose is resistance.\n\nGaza Rose gallery \u2192 proceeds to Palestinian children.",
    
    "This artist painted in the language of their time.\nWe paint in ours.\n\nJoin the signal: github.com/meekotharaccoon-cell/meeko-nerve-center\n#OpenSource #Art #SolarPunk",
]

def fetch_json(url, timeout=15):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[art] fetch error: {e}')
        return None

def fetch_artic_artworks():
    """Art Institute of Chicago \u2014 free, high res, open access."""
    print('[art] Fetching Art Institute of Chicago...')
    artworks = []
    
    # Search for resonant themes
    queries = ['flower', 'peace', 'mother child', 'garden', 'portrait woman', 'hands']
    
    for query in queries[:3]:  # limit requests
        url = f'https://api.artic.edu/api/v1/artworks/search?q={urllib_request.quote(query)}&fields=id,title,artist_display,date_display,image_id,department_title,place_of_origin,description&limit=5'
        data = fetch_json(url)
        if not data: continue
        
        for artwork in data.get('data', []):
            if not artwork.get('image_id'): continue
            artworks.append({
                'id':         str(artwork.get('id', '')),
                'title':      artwork.get('title', 'Untitled'),
                'artist':     artwork.get('artist_display', 'Unknown artist'),
                'date':       artwork.get('date_display', ''),
                'department': artwork.get('department_title', ''),
                'origin':     artwork.get('place_of_origin', ''),
                'image_url':  f"https://www.artic.edu/iiif/2/{artwork['image_id']}/full/843,/0/default.jpg",
                'page_url':   f"https://www.artic.edu/artworks/{artwork.get('id', '')}",
                'source':     'Art Institute of Chicago',
                'query':      query,
            })
    
    print(f'[art] Got {len(artworks)} artworks from ARTIC')
    return artworks

def fetch_met_artworks():
    """Metropolitan Museum of Art \u2014 free, open access."""
    print('[art] Fetching Metropolitan Museum...')
    artworks = []
    
    # Search Middle Eastern / relevant departments
    searches = [
        ('flower', True),
        ('rose garden', True),
        ('peace', True),
    ]
    
    for query, has_image in searches[:2]:
        search_url = f'https://collectionapi.metmuseum.org/public/collection/v1/search?q={urllib_request.quote(query)}&hasImages=true&isPublicDomain=true'
        data = fetch_json(search_url)
        if not data: continue
        
        object_ids = data.get('objectIDs', [])[:5]
        for oid in object_ids:
            obj = fetch_json(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}')
            if not obj: continue
            if not obj.get('primaryImage'): continue
            if not obj.get('isPublicDomain', False): continue
            
            artworks.append({
                'id':         str(oid),
                'title':      obj.get('title', 'Untitled'),
                'artist':     obj.get('artistDisplayName', 'Unknown artist'),
                'date':       obj.get('objectDate', ''),
                'department': obj.get('department', ''),
                'origin':     obj.get('country', obj.get('culture', '')),
                'image_url':  obj.get('primaryImage', ''),
                'page_url':   obj.get('objectURL', ''),
                'source':     'Metropolitan Museum of Art',
                'query':      query,
                'medium':     obj.get('medium', ''),
            })
    
    print(f'[art] Got {len(artworks)} artworks from Met')
    return artworks

def score_artwork(artwork):
    """Score how well this artwork resonates with the mission."""
    score = 0
    text = (artwork.get('title','') + ' ' + artwork.get('artist','') + ' ' + 
            artwork.get('origin','') + ' ' + artwork.get('department','')).lower()
    
    for kw in THEME_KEYWORDS:
        if kw.lower() in text: score += 2
    
    # Bonus for Middle Eastern origin
    middle_east = ['arab', 'persian', 'ottoman', 'islamic', 'egypt', 'levant', 
                   'turkey', 'iran', 'iraq', 'syria', 'jordan', 'lebanon', 'israel']
    if any(me in text for me in middle_east): score += 5
    
    if artwork.get('image_url'): score += 3
    
    return score

def generate_pairs(artworks):
    """Pair artworks with cause messages."""
    pairs = []
    messages = CAUSE_MESSAGES.copy()
    random.shuffle(messages)
    
    for i, artwork in enumerate(artworks):
        message = messages[i % len(messages)]
        
        caption = f"""{artwork['title']}
{artwork['artist']}, {artwork['date']}
{artwork['source']}

{message}"""
        
        pairs.append({
            'artwork':      artwork,
            'message':      message,
            'caption':      caption,
            'image_url':    artwork.get('image_url', ''),
            'platform':     'instagram',
            'hashtags':     '#GazaRose #ArtForGood #Palestine #FreePalestine #MuseumArt #OpenAccess #SolarPunk',
            'full_post':    caption + '\n\n' + '#GazaRose #ArtForGood #Palestine #FreePalestine #MuseumArt',
            'score':        artwork.get('score', 0),
        })
    
    return pairs

def run():
    print(f'[art] Art + Cause Generator \u2014 {TODAY}')
    
    all_artworks = []
    all_artworks.extend(fetch_artic_artworks())
    all_artworks.extend(fetch_met_artworks())
    
    # Score and sort
    for aw in all_artworks:
        aw['score'] = score_artwork(aw)
    all_artworks.sort(key=lambda a: a['score'], reverse=True)
    
    print(f'[art] {len(all_artworks)} total artworks, scoring for mission resonance...')
    
    # Generate pairs
    top_artworks = all_artworks[:14]  # 2 posts/day for a week
    pairs = generate_pairs(top_artworks)
    
    # Save
    output = {
        'date':     TODAY,
        'total_artworks': len(all_artworks),
        'pairs':    pairs,
        'week_queue': pairs[:7],  # one per day
    }
    (DATA / 'art_pairs.json').write_text(json.dumps(output, indent=2))
    
    # Content queue
    queue_posts = []
    for pair in pairs[:7]:
        queue_posts.append({
            'platform': 'instagram',
            'type':     'art_cause',
            'image':    pair['image_url'],
            'text':     pair['full_post'],
            'source':   pair['artwork']['source'],
            'title':    pair['artwork']['title'],
        })
    
    (CONT / f'art_cause_{TODAY}.json').write_text(json.dumps(queue_posts, indent=2))
    
    # Knowledge digest
    lines = [f'# Art + Cause Queue \u2014 {TODAY}', '',
             f'{len(all_artworks)} artworks sourced, {len(pairs)} pairs generated', '']
    for i, pair in enumerate(pairs[:5]):
        aw = pair['artwork']
        lines += [
            f"## {i+1}. {aw['title']}",
            f"*{aw['artist']}, {aw['date']}*",
            f"Source: {aw['source']}",
            f"Image: {aw.get('image_url', 'N/A')}",
            f"Score: {aw['score']}",
            '',
        ]
    
    digest = '\n'.join(lines)
    (KB / 'art' / f'{TODAY}.md').write_text(digest)
    (KB / 'art' / 'latest.md').write_text(digest)
    
    print(f'[art] {len(pairs)} art+cause pairs ready')
    print(f'[art] Top artwork: {all_artworks[0]["title"]} ({all_artworks[0]["source"]}) score={all_artworks[0]["score"]}')
    if pairs:
        print(f'[art] First image URL: {pairs[0]["image_url"]}')
    
    return output

if __name__ == '__main__':
    run()
