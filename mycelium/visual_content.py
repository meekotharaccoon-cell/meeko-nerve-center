#!/usr/bin/env python3
"""
Visual Content Engine
======================
Picsum Photos (free, no auth) + HuggingFace FLUX image gen.

Picsum Photos: https://picsum.photos
  - Returns beautiful random photos
  - Can seed for consistent images: https://picsum.photos/seed/gaza-rose/800/600
  - Can get specific images by ID
  - All CC0 / public domain
  - Perfect for:
    - Post backgrounds
    - Social media visual variety
    - Dashboard placeholder art
    - Any content that needs a beautiful image fast

HuggingFace FLUX (with HF_TOKEN):
  - Generate actual custom images from prompts
  - Gaza Rose imagery, SolarPunk scenes, etc.
  - Free tier via HuggingFace Inference Providers

Outputs:
  - data/visual_queue.json    images ready for posts
  - public/images/            downloaded images for the site
  - content/queue/visuals_*.json  visual content posts
"""

import json, datetime, os, random
from pathlib import Path
from urllib import request as urllib_request

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
PUBLIC = ROOT / 'public' / 'images'
CONT   = ROOT / 'content' / 'queue'
PUBLIC.mkdir(parents=True, exist_ok=True)

TODAY     = datetime.date.today().isoformat()
HF_TOKEN  = os.environ.get('HF_TOKEN', '')

# Picsum seeded images — consistent beautiful photos for recurring content types
PICSUM_SEEDS = {
    'hope':          'solarpunk-hope',
    'earth':         'earth-green',
    'community':     'community-people', 
    'flowers':       'garden-flowers',
    'technology':    'open-source-tech',
    'space':         'cosmos-stars',
    'justice':       'solidarity-hands',
    'water':         'clean-water',
}

# FLUX prompts for AI-generated images (when HF_TOKEN available)
FLUX_PROMPTS = [
    'A single red rose growing through cracked concrete, soft golden light, solarpunk aesthetic, hopeful',
    'Hands of many different skin tones holding seeds, botanical illustration style, warm colors',
    'Open source code flowing like a river through a green forest, digital art, solarpunk',
    'A community garden in an urban setting at dusk, solar panels visible, diverse people, warm light',
    'Abstract: a rose made of circuit board patterns, glowing softly, teal and earth tones',
]

def fetch_picsum(seed, width=800, height=600):
    """Get a consistent beautiful photo by seed. Returns image URL (no download needed)."""
    url = f'https://picsum.photos/seed/{seed}/{width}/{height}'
    return url  # Picsum URLs are direct embed-ready

def get_picsum_info(image_id):
    """Get metadata for a specific Picsum image."""
    try:
        req = urllib_request.Request(
            f'https://picsum.photos/id/{image_id}/info',
            headers={'User-Agent': 'meeko-nerve-center/2.0'}
        )
        with urllib_request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except:
        return None

def generate_flux_image(prompt):
    """Generate image with HuggingFace FLUX. Returns image bytes or None."""
    if not HF_TOKEN:
        return None
    
    payload = json.dumps({'inputs': prompt}).encode()
    
    try:
        req = urllib_request.Request(
            'https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell',
            data=payload,
            headers={
                'Authorization': f'Bearer {HF_TOKEN}',
                'Content-Type': 'application/json',
            }
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            return r.read()  # PNG bytes
    except Exception as e:
        print(f'[visuals] FLUX error: {e}')
        return None

def build_visual_queue():
    """Build a queue of images ready for social posts."""
    queue = []
    
    # Picsum images (always available, no token needed)
    for theme, seed in PICSUM_SEEDS.items():
        url = fetch_picsum(seed)
        queue.append({
            'type':    'picsum',
            'theme':   theme,
            'url':     url,
            'embed':   url,  # Direct embed URL
            'credit':  'Photo via Picsum Photos (CC0)',
            'suitable_for': f'{theme} content posts',
        })
    
    print(f'[visuals] {len(queue)} Picsum images queued')
    
    # FLUX generated images (if HF_TOKEN available)
    if HF_TOKEN:
        print('[visuals] Generating FLUX image...')
        prompt = random.choice(FLUX_PROMPTS)
        img_bytes = generate_flux_image(prompt)
        if img_bytes:
            img_path = PUBLIC / f'flux_{TODAY}.png'
            img_path.write_bytes(img_bytes)
            queue.append({
                'type':    'flux_generated',
                'theme':   'gaza_rose_ai',
                'prompt':  prompt,
                'path':    str(img_path),
                'url':     f'https://meekotharaccoon-cell.github.io/meeko-nerve-center/images/flux_{TODAY}.png',
                'credit':  'AI-generated via FLUX.1-schnell (HuggingFace)',
            })
            print(f'[visuals] FLUX image generated: flux_{TODAY}.png')
    else:
        print('[visuals] No HF_TOKEN — skipping FLUX generation. Picsum images ready.')
    
    return queue

def run():
    print(f'[visuals] Visual Content Engine — {TODAY}')
    
    queue = build_visual_queue()
    
    output = {'date': TODAY, 'images': queue, 'total': len(queue)}
    (DATA / 'visual_queue.json').write_text(json.dumps(output, indent=2))
    
    # Build content posts pairing images with messages
    posts = []
    cause_themes = ['flowers', 'hope', 'community', 'justice']
    for theme in cause_themes:
        img = next((i for i in queue if i['theme'] == theme), None)
        if img:
            posts.append({
                'platform':  'instagram',
                'type':      'visual_cause',
                'image_url': img['url'],
                'theme':     theme,
                'caption':   f'[Add cause message for {theme} theme — or let hf_brain.py generate one]',
            })
    
    (CONT / f'visuals_{TODAY}.json').write_text(json.dumps(posts, indent=2))
    
    print(f'[visuals] Done. {len(queue)} images, {len(posts)} content posts ready.')
    return output

if __name__ == '__main__':
    run()
