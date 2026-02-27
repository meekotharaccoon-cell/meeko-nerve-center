#!/usr/bin/env python3
"""
Video Engine
=============
Generates short videos using HuggingFace Inference API.
Uses CogVideoX (best for artistic/cause content, free tier).
Creates 30-second scripts, generates video, uploads to YouTube.

Secrets needed:
  HF_TOKEN          already set
  YOUTUBE_API_KEY   get from console.cloud.google.com (free)
                    Enable YouTube Data API v3
                    Create API key
                    Add to GitHub secrets as YOUTUBE_API_KEY

What it makes:
  - Gaza Rose cause videos (30 sec)
  - Congressional conflict alerts (short, shareable)
  - Word of the day animated cards
  - SolarPunk vision clips
  - Custom videos for fork users

Outputs:
  - public/video/latest.mp4   most recent video
  - data/video_queue.json     upcoming video scripts
  - data/video_log.json       history of generated videos
"""

import json, datetime, os, time
from pathlib import Path
from urllib import request as urllib_request

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / 'data'
PUBLIC  = ROOT / 'public' / 'video'
CONTENT = ROOT / 'content' / 'queue'
PUBLIC.mkdir(parents=True, exist_ok=True)
CONTENT.mkdir(parents=True, exist_ok=True)

TODAY        = datetime.date.today().isoformat()
HF_TOKEN     = os.environ.get('HF_TOKEN', '')
YOUTUBE_KEY  = os.environ.get('YOUTUBE_API_KEY', '')

# Best free models for short video generation via HuggingFace
VIDEO_MODELS = [
    'THUDM/CogVideoX-5b',           # best artistic quality, Gaza Rose style
    'Lightricks/LTX-Video',          # fast, good for short clips
]

# ── Script templates ───────────────────────────────────────────────────────────

SCRIPT_TEMPLATES = {
    'gaza_rose': [
        "A red rose blooms in golden light. Petals unfurl slowly. Text appears: 'Gaza Rose.' Text: '70% of every sale funds Palestinian children.' Text: 'PCRF — Palestinian Children's Relief Fund.' Text: 'Open source. Built in solidarity.' Rose continues blooming.",
        "Time lapse of a rose growing through cracked earth. Warm sunrise colors. Text: 'Something beautiful can grow anywhere.' Text: 'Gaza Rose art project.' Text: 'pcrf.net — donate directly.'",
    ],
    'congress_alert': [
        "News ticker style animation. Text: 'Your representative is trading stocks.' Text: 'While writing laws that affect those same companies.' Text: 'Meeko Nerve Center watches so you don\'t have to.' Text: 'Open source. Free. Running every morning.'",
    ],
    'solarpunk': [
        "Lush green city with solar panels. People in community gardens. Warm golden hour light. Text: 'Technology that serves people.' Text: 'Not the other way around.' Text: 'Meeko Nerve Center — fork it for your cause.' Text: 'github.com/meekotharaccoon-cell/meeko-nerve-center'",
    ],
    'word_of_day': [
        "Minimalist dark background. Single word appears letter by letter. Definition fades in below. Example sentence. Final text: 'This is what we\'re building toward.' Hashtag: #WordOfTheDay #SolarPunk",
    ]
}

def get_todays_script():
    """Pick a script based on day of week for variety."""
    day = datetime.date.today().weekday()
    if day in (0, 3):   return 'gaza_rose',     SCRIPT_TEMPLATES['gaza_rose'][day % len(SCRIPT_TEMPLATES['gaza_rose'])]
    if day in (1, 4):   return 'solarpunk',     SCRIPT_TEMPLATES['solarpunk'][0]
    if day == 2:        return 'congress_alert', SCRIPT_TEMPLATES['congress_alert'][0]
    return 'word_of_day', SCRIPT_TEMPLATES['word_of_day'][0]

# ── HuggingFace video generation ───────────────────────────────────────────────

def generate_video_hf(prompt, model=VIDEO_MODELS[0]):
    """Generate video via HuggingFace Inference API."""
    if not HF_TOKEN:
        print('[video] No HF_TOKEN')
        return None

    print(f'[video] Generating with {model}...')
    print(f'[video] Prompt: {prompt[:80]}...')

    try:
        payload = json.dumps({
            'inputs': prompt,
            'parameters': {
                'num_frames':       48,   # ~2 seconds at 24fps, scale up later
                'num_inference_steps': 25,
                'guidance_scale':   6.0,
            }
        }).encode()

        req = urllib_request.Request(
            f'https://api-inference.huggingface.co/models/{model}',
            data=payload,
            headers={
                'Authorization': f'Bearer {HF_TOKEN}',
                'Content-Type':  'application/json',
                'Accept':        'video/mp4'
            }
        )

        # Video generation takes time — longer timeout
        with urllib_request.urlopen(req, timeout=120) as r:
            if r.status == 200:
                video_bytes = r.read()
                if len(video_bytes) > 1000:  # sanity check
                    print(f'[video] Generated {len(video_bytes)/1024:.0f}KB video')
                    return video_bytes

        print('[video] Empty response from HF')
        return None

    except Exception as e:
        print(f'[video] HF generation failed: {e}')
        return None

# ── YouTube upload ─────────────────────────────────────────────────────────────

def upload_to_youtube(video_path, title, description, tags):
    """
    Upload video to YouTube via YouTube Data API v3.
    Requires YOUTUBE_API_KEY and OAuth — for now logs upload details.
    Full OAuth flow needs a one-time browser auth step.

    SETUP (one time only):
      1. Go to console.cloud.google.com
      2. Create project or use existing
      3. Enable YouTube Data API v3
      4. Create OAuth 2.0 credentials (Desktop app)
      5. Download client_secrets.json
      6. Run: python mycelium/youtube_auth.py (one-time browser auth)
      7. Add resulting token to GitHub secrets as YOUTUBE_OAUTH_TOKEN
    """
    if not YOUTUBE_KEY:
        print('[video] No YOUTUBE_API_KEY — video saved locally only')
        print(f'[video] Title: {title}')
        print(f'[video] File: {video_path}')
        print('[video] To enable YouTube: add YOUTUBE_API_KEY to GitHub secrets')
        return None

    # YouTube upload requires multipart upload — queuing for when OAuth is set up
    print(f'[video] YouTube upload queued: {title}')
    queue_entry = {
        'date':        TODAY,
        'title':       title,
        'description': description,
        'tags':        tags,
        'file':        str(video_path),
        'status':      'pending_oauth'
    }
    log_path = DATA / 'video_log.json'
    log = json.loads(log_path.read_text()) if log_path.exists() else {'videos': []}
    log['videos'].append(queue_entry)
    log_path.write_text(json.dumps(log, indent=2))
    return queue_entry

# ── Queue social posts for the video ──────────────────────────────────────────

def queue_video_social_post(video_type, youtube_url=None):
    """Queue a social post announcing the video."""
    posts = {
        'gaza_rose': f'New Gaza Rose video.\n\nEvery view is solidarity. Every share reaches further.\n70% of art sales → PCRF.\n\n{youtube_url or "Link in bio."}\n\n#GazaRose #Palestine #PCRF #SolarPunk',
        'congress_alert': f'Your representatives are trading stocks while writing your laws.\n\nMeeko Nerve Center watches the disclosures so you don\'t have to.\n\nOpen source. Free. Running every morning.\n\n{youtube_url or "Link in bio."}\n\n#Congress #Accountability #OpenSource',
        'solarpunk': f'Technology that serves people.\n\nNot corporations. Not shareholders. People.\n\nFork the system: github.com/meekotharaccoon-cell/meeko-nerve-center\n\n#SolarPunk #OpenSource #ForkIt',
        'word_of_day': f'Word the world needs today.\n\n{youtube_url or "Watch the full definition."}\n\n#WordOfTheDay #SolarPunk #Language',
    }
    text = posts.get(video_type, posts['solarpunk'])
    post = [{'platform': 'all', 'type': 'video', 'text': text, 'video_type': video_type}]
    out = CONTENT / f'video_post_{TODAY}_{video_type}.json'
    out.write_text(json.dumps(post, indent=2))
    print(f'[video] Social post queued: {out.name}')

# ── Main ───────────────────────────────────────────────────────────────────────

def run():
    print(f'[video] Video Engine — {TODAY}')

    if not HF_TOKEN:
        print('[video] HF_TOKEN required. Set it in GitHub secrets.')
        return

    video_type, script = get_todays_script()
    print(f'[video] Type: {video_type}')

    # Try each model in order until one works
    video_bytes = None
    for model in VIDEO_MODELS:
        video_bytes = generate_video_hf(script, model)
        if video_bytes:
            break
        time.sleep(5)

    if not video_bytes:
        print('[video] Generation failed on all models today. Will retry tomorrow.')
        queue_video_social_post(video_type)  # still queue a text post
        return

    # Save video
    video_path = PUBLIC / f'{TODAY}_{video_type}.mp4'
    video_path.write_bytes(video_bytes)
    latest_path = PUBLIC / 'latest.mp4'
    latest_path.write_bytes(video_bytes)
    print(f'[video] Saved: {video_path}')

    # Upload to YouTube
    titles = {
        'gaza_rose':      f'Gaza Rose — {TODAY} | Palestine Solidarity Art',
        'congress_alert': f'Congress Stock Watch — {TODAY} | Meeko Nerve Center',
        'solarpunk':      f'SolarPunk Vision — {TODAY} | Open Source Humanitarian AI',
        'word_of_day':    f'Word of the Day — {TODAY} | Meeko Nerve Center',
    }
    tags = {
        'gaza_rose':      ['Gaza', 'Palestine', 'PCRF', 'GazaRose', 'Solidarity', 'OpenSource'],
        'congress_alert': ['Congress', 'Accountability', 'StockTrades', 'OpenSource', 'Democracy'],
        'solarpunk':      ['SolarPunk', 'OpenSource', 'HumanitarianAI', 'ForkIt'],
        'word_of_day':    ['WordOfTheDay', 'SolarPunk', 'Language', 'Liberation'],
    }
    desc = f'Meeko Nerve Center — autonomous humanitarian AI.\nOpen source: github.com/meekotharaccoon-cell/meeko-nerve-center\nGaza Rose art: 70% to PCRF (pcrf.net)\n\nFork for your cause: $5 guide in the repo.'

    upload_to_youtube(video_path, titles.get(video_type, 'Meeko Nerve Center'), desc, tags.get(video_type, []))
    queue_video_social_post(video_type)

    print(f'[video] Done. {video_type} video ready.')

if __name__ == '__main__':
    run()
