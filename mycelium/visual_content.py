#!/usr/bin/env python3
"""
Visual Content Engine
======================
Free images for every content post.

Sources:
  1. Picsum Photos   - random beautiful photography (no auth, zero cost)
     https://picsum.photos/{width}/{height}  -> random photo URL
     https://picsum.photos/seed/{seed}/{w}/{h} -> consistent seeded image

  2. Museum Art      - public domain (already in art_cause_generator.py)

  3. FLUX via HF     - AI-generated Gaza Rose variations (if HF_TOKEN set)

Use cases:
  - Every social post gets a visual
  - Thumbnail generation for YouTube
  - Art+Cause posts paired with Picsum backgrounds
  - SolarPunk dashboard ambient imagery

Outputs:
  - data/visual_queue.json    list of image URLs ready to use in posts
  - public/visuals.json       public manifest of available images
  - content/queue/visuals_*.json  visual assignments for today\'s posts
"""

import json, datetime, random, hashlib
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
CONT  = ROOT / 'content' / 'queue'
PUBLIC = ROOT / 'public'

for d in [DATA, CONT, PUBLIC]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()

# Picsum dimensions for different use cases
DIMENSIONS = {
    'instagram':  (1080, 1080),
    'youtube_thumb': (1280, 720),
    'twitter':    (1200, 675),
    'mastodon':   (1200, 630),
    'story':      (1080, 1920),
    'banner':     (1500, 500),
}

# Seeds for consistent images (seed = same image every time)
SEED_MAP = {
    'solarpunk':      'solarpunk-forest',
    'space':          'space-stars',
    'earthquake':     'earth-geology',
    'crypto':         'tech-abstract',
    'congress':       'capitol-architecture',
    'art_cause':      'museum-gallery',
    'jobs':           'remote-work',
    'books':          'library-reading',
    'music':          'concert-crowd',
    'food':           'market-produce',
    'climate':        'wind-turbines',
    'general':        TODAY,  # today\'s date = fresh image each day
}

def picsum_url(width, height, seed=None, grayscale=False):
    """Generate a Picsum Photos URL. No auth needed."""
    base = 'https://picsum.photos'
    if seed:
        url = f'{base}/seed/{seed}/{width}/{height}'
    else:
        url = f'{base}/{width}/{height}'
    if grayscale:
        url += '?grayscale'
    return url

def verify_picsum(url, timeout=5):
    """Check if Picsum URL resolves (it redirects to actual image)."""
    try:
        req = urllib_request.Request(url, method='HEAD', headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return r.status in (200, 301, 302)
    except:
        return False

def generate_visual_manifest():
    """Generate a full manifest of available visuals for today."""
    visuals = {}

    for theme, seed in SEED_MAP.items():
        visuals[theme] = {}
        for platform, (w, h) in DIMENSIONS.items():
            visuals[theme][platform] = {
                'url':   picsum_url(w, h, seed=seed),
                'width': w,
                'height': h,
                'seed':  seed,
            }

    return visuals

def assign_visuals_to_content():
    """Read today\'s content queue and assign images to each post."""
    assignments = []
    queue_dir = CONT
    if not queue_dir.exists():
        return assignments

    # Theme detection from post content
    def detect_theme(text):
        text_lower = (text or '').lower()
        if any(k in text_lower for k in ['solarpunk', 'carbon', 'climate', 'grid']): return 'solarpunk'
        if any(k in text_lower for k in ['space', 'launch', 'iss', 'astronaut']): return 'space'
        if any(k in text_lower for k in ['earthquake', 'quake', 'disaster']): return 'earthquake'
        if any(k in text_lower for k in ['crypto', 'bitcoin', 'btc', 'sol', 'eth']): return 'crypto'
        if any(k in text_lower for k in ['congress', 'representative', 'trade', 'stock']): return 'congress'
        if any(k in text_lower for k in ['art', 'museum', 'painting', 'gaza rose']): return 'art_cause'
        if any(k in text_lower for k in ['job', 'remote', 'hire', 'work']): return 'jobs'
        if any(k in text_lower for k in ['book', 'read', 'library']): return 'books'
        if any(k in text_lower for k in ['music', 'artist', 'song']): return 'music'
        return 'general'

    for queue_file in queue_dir.iterdir():
        if not queue_file.suffix == '.json': continue
        if 'visuals' in queue_file.name: continue
        try:
            posts = json.loads(queue_file.read_text())
            if not isinstance(posts, list): continue
            for post in posts:
                text = post.get('text', '') + ' ' + post.get('type', '')
                theme = detect_theme(text)
                platform = post.get('platform', 'mastodon')
                w, h = DIMENSIONS.get(platform, (1200, 630))
                assignments.append({
                    'source_file': queue_file.name,
                    'post_type':   post.get('type', 'unknown'),
                    'platform':    platform,
                    'theme':       theme,
                    'image_url':   picsum_url(w, h, seed=SEED_MAP.get(theme, TODAY)),
                    'width':  w,
                    'height': h,
                })
        except:
            continue

    return assignments

def run():
    print(f'[visual] Visual Content Engine — {TODAY}')

    # Generate full visual manifest
    manifest = generate_visual_manifest()
    (DATA / 'visual_queue.json').write_text(json.dumps({'date': TODAY, 'visuals': manifest}, indent=2))
    (PUBLIC / 'visuals.json').write_text(json.dumps({'date': TODAY, 'visuals': manifest}, indent=2))

    # Assign visuals to today\'s content
    assignments = assign_visuals_to_content()
    if assignments:
        (CONT / f'visuals_{TODAY}.json').write_text(json.dumps(assignments, indent=2))
        print(f'[visual] {len(assignments)} visual assignments created')

    # Quick spot check
    test_url = picsum_url(800, 600, seed='solarpunk-forest')
    works = verify_picsum(test_url)
    print(f'[visual] Picsum test: {test_url}')
    print(f'[visual] Picsum reachable: {works}')

    # Sample URLs for reference
    print('[visual] Sample URLs:')
    print(f'  Instagram square: {picsum_url(1080, 1080, seed=TODAY)}')
    print(f'  YouTube thumb:    {picsum_url(1280, 720, seed="space-stars")}')
    print(f'  SolarPunk theme:  {picsum_url(1200, 630, seed="solarpunk-forest")}')

    return {'manifest': manifest, 'assignments': len(assignments)}

if __name__ == '__main__':
    run()
