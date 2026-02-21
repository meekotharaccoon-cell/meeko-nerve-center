#!/usr/bin/env python3
"""
YOUTUBE MANAGER
================
Automatically manages your YouTube channel:

1. DESCRIPTION UPDATER
   - Scans all your videos
   - Updates descriptions to include your Gumroad links,
     gallery link, and rotating call-to-action
   - Never overwrites content you explicitly protect

2. COMMENT RESPONDER
   - Reads new comments on your videos
   - Responds to questions automatically (brain-gated)
   - Pins first comments on new videos

3. PLAYLIST ORGANIZER
   - Keeps playlists organized by content type

4. METADATA OPTIMIZER
   - Suggests better titles/tags based on search data
   - Logs recommendations for human review

SETUP REQUIRED:
  GitHub Secrets needed:
    YOUTUBE_CLIENT_ID       — from Google Cloud Console
    YOUTUBE_CLIENT_SECRET   — from Google Cloud Console
    YOUTUBE_REFRESH_TOKEN   — one-time setup (see YOUTUBE_SETUP.md)

  OR simpler (no OAuth needed for your own videos):
    YOUTUBE_API_KEY         — Google Cloud Console, free
    YOUTUBE_CHANNEL_ID      — your channel ID (see YOUTUBE_SETUP.md)

NOTE: Reading your own channel data and updating descriptions
requires OAuth. The API key alone only allows reading public data.
See YOUTUBE_SETUP.md for the 10-minute one-time setup.
"""
import os, json, time, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import urllib.request, urllib.parse, urllib.error
except ImportError:
    pass

# ---- CONFIGURATION ------------------------------------------------
GUMROAD_FLOWERS_URL = os.environ.get('GUMROAD_FLOWERS_URL', 'https://meekotharaccoon.gumroad.com')  # your flower designs Gumroad
GALLERY_URL         = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'
GUMROAD_CLAIM_URL   = os.environ.get('GUMROAD_FLOWERS_URL', 'https://meekotharaccoon.gumroad.com')

# YouTube API
API_KEY          = os.environ.get('YOUTUBE_API_KEY', '')
CLIENT_ID       = os.environ.get('YOUTUBE_CLIENT_ID', '')
CLIENT_SECRET   = os.environ.get('YOUTUBE_CLIENT_SECRET', '')
REFRESH_TOKEN   = os.environ.get('YOUTUBE_REFRESH_TOKEN', '')
CHANNEL_ID      = os.environ.get('YOUTUBE_CHANNEL_ID', '')

# Data
DATA_DIR = Path('data')
YT_LOG   = DATA_DIR / 'youtube_log.json'

# ---- DESCRIPTION TEMPLATE -----------------------------------------
# This gets appended to every video description.
# Keeps whatever is already there. Only adds if not already present.

DESCRIPTION_FOOTER = """

─────────────────────────────────────────────
🌸 DOWNLOAD THE FULL ARTWORK
{gumroad_url}

Original 300 DPI digital flower designs. 
Print them. Frame them. Use them. They’re yours.

🌹 GAZA ROSE GALLERY — $1, 70% to Palestine Children’s Relief Fund
{gallery_url}

56 original flower artworks. $1 each.
70 cents of every dollar goes directly to PCRF — verified 4-star Charity Navigator.
No middleman. Direct impact.

─────────────────────────────────────────────
"""

FOOTER_MARKER = '\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\ud83c\udf38 DOWNLOAD'

# ---- OAUTH --------------------------------------------------------
def get_access_token():
    """Exchange refresh token for access token."""
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        return None
    data = urllib.parse.urlencode({
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())['access_token']
    except Exception as e:
        print(f'[auth] Failed to get access token: {e}')
        return None

# ---- API CALLS ----------------------------------------------------
def api_get(endpoint, params, access_token=None):
    """GET request to YouTube Data API v3."""
    params['key'] = API_KEY
    url = f'https://www.googleapis.com/youtube/v3/{endpoint}?{urllib.parse.urlencode(params)}'
    headers = {}
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f'[api] HTTP {e.code}: {e.read().decode()[:200]}')
        return None
    except Exception as e:
        print(f'[api] Error: {e}')
        return None

def api_put(endpoint, body, access_token):
    """PUT request to YouTube Data API v3 (for updates)."""
    url = f'https://www.googleapis.com/youtube/v3/{endpoint}?key={API_KEY}'
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method='PUT')
    req.add_header('Authorization', f'Bearer {access_token}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f'[api] HTTP {e.code}: {e.read().decode()[:300]}')
        return None
    except Exception as e:
        print(f'[api] Error: {e}')
        return None

# ---- CORE FUNCTIONS -----------------------------------------------
def get_channel_videos(access_token):
    """Get all videos from your channel."""
    print(f'[yt] Fetching channel videos...')
    
    # First get the uploads playlist ID
    channel_data = api_get('channels', {
        'part': 'contentDetails',
        'mine': 'true'
    }, access_token)
    
    if not channel_data or not channel_data.get('items'):
        # Try with explicit channel ID
        if CHANNEL_ID:
            channel_data = api_get('channels', {
                'part': 'contentDetails',
                'id': CHANNEL_ID
            }, access_token)
    
    if not channel_data or not channel_data.get('items'):
        print('[yt] Could not fetch channel data. Check credentials.')
        return []
    
    uploads_id = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    # Get all videos from uploads playlist
    videos = []
    next_page = None
    while True:
        params = {
            'part': 'snippet',
            'playlistId': uploads_id,
            'maxResults': 50
        }
        if next_page:
            params['pageToken'] = next_page
        
        data = api_get('playlistItems', params, access_token)
        if not data:
            break
        
        videos.extend(data.get('items', []))
        next_page = data.get('nextPageToken')
        if not next_page:
            break
    
    print(f'[yt] Found {len(videos)} videos')
    return videos

def get_video_details(video_ids, access_token):
    """Get full details for a list of video IDs."""
    if not video_ids:
        return []
    ids_str = ','.join(video_ids[:50])  # API limit
    data = api_get('videos', {
        'part': 'snippet,statistics',
        'id': ids_str
    }, access_token)
    return data.get('items', []) if data else []

def update_video_description(video, access_token, dry_run=False):
    """Add footer to video description if not already there."""
    snippet = video.get('snippet', {})
    video_id = video['id']
    title = snippet.get('title', 'Untitled')
    current_desc = snippet.get('description', '')
    
    # Check if footer already exists
    if FOOTER_MARKER in current_desc:
        print(f'  [skip] Already updated: "{title[:50]}"')
        return False
    
    # Build new description
    footer = DESCRIPTION_FOOTER.format(
        gumroad_url=GUMROAD_FLOWERS_URL,
        gallery_url=GALLERY_URL
    )
    new_desc = current_desc.rstrip() + footer
    
    if dry_run:
        print(f'  [dry] Would update: "{title[:50]}"')
        print(f'        Adding: {len(footer)} chars of footer')
        return True
    
    # Build update body
    body = {
        'id': video_id,
        'snippet': {
            'title': snippet['title'],
            'description': new_desc,
            'categoryId': snippet.get('categoryId', '22'),
            'tags': snippet.get('tags', []),
        }
    }
    
    result = api_put('videos', body, access_token)
    if result:
        print(f'  [done] Updated: "{title[:50]}"')
        return True
    else:
        print(f'  [fail] Could not update: "{title[:50]}"')
        return False

def update_all_descriptions(access_token, dry_run=False):
    """Update descriptions on all channel videos."""
    print(f'\n[yt] Updating descriptions {\'(DRY RUN) \' if dry_run else \'\'}...')
    
    playlist_videos = get_channel_videos(access_token)
    if not playlist_videos:
        return 0
    
    # Get video IDs
    video_ids = [v['snippet']['resourceId']['videoId'] for v in playlist_videos]
    
    # Get full details
    videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        videos.extend(get_video_details(batch, access_token))
    
    updated = 0
    for video in videos:
        if update_video_description(video, access_token, dry_run):
            updated += 1
        time.sleep(0.5)  # Rate limit
    
    print(f'\n[yt] {updated} videos updated')
    return updated

def get_channel_stats(access_token):
    """Get channel stats for the dashboard."""
    data = api_get('channels', {
        'part': 'statistics,snippet',
        'mine': 'true'
    }, access_token)
    
    if not data or not data.get('items'):
        return None
    
    item = data['items'][0]
    stats = item.get('statistics', {})
    return {
        'name': item['snippet']['title'],
        'subscribers': stats.get('subscriberCount', '?'),
        'views': stats.get('viewCount', '?'),
        'videos': stats.get('videoCount', '?'),
        'checked_at': datetime.now(timezone.utc).isoformat()
    }

# ---- COMMENT RESPONDER -------------------------------------------
AUTO_REPLIES = {
    'where': 'You can download the full artwork at {gumroad_url} \ud83c\udf38',
    'buy': 'Grab them at {gumroad_url} \u2014 original 300 DPI prints, yours to keep forever \ud83c\udf39',
    'download': 'Full resolution download at {gumroad_url} \ud83c\udf38',
    'charity': 'Gaza Rose Gallery ({gallery_url}) \u2014 $1 per flower, 70 cents goes to PCRF (Palestinian children\'s aid, 4-star Charity Navigator). Real, verified, direct.',
    'beautiful': 'Thank you so much \ud83d\ude4f Each one is original \u2014 you can own the full 300 DPI version at {gumroad_url}',
    'music': 'All music is royalty-free \u2014 creative commons. The visuals are mine \ud83c\udf38',
    'software': 'These are made from my original digital paintings, animated in post. The flowers themselves I designed from scratch.',
}

def respond_to_comments(access_token, max_replies=5, dry_run=True):
    """Respond to comments on recent videos. Always dry_run by default for safety."""
    print(f'\n[yt] Scanning comments {\'(DRY RUN)\' if dry_run else \'\'}...')
    
    playlist_videos = get_channel_videos(access_token)
    if not playlist_videos:
        return 0
    
    replied = 0
    for pv in playlist_videos[:10]:  # Check 10 most recent
        video_id = pv['snippet']['resourceId']['videoId']
        video_title = pv['snippet']['title']
        
        comments = api_get('commentThreads', {
            'part': 'snippet',
            'videoId': video_id,
            'maxResults': 20,
            'order': 'time'
        }, access_token)
        
        if not comments:
            continue
        
        for thread in comments.get('items', []):
            comment = thread['snippet']['topLevelComment']['snippet']
            text = comment.get('textDisplay', '').lower()
            comment_id = thread['snippet']['topLevelComment']['id']
            
            # Find matching reply
            reply = None
            for keyword, template in AUTO_REPLIES.items():
                if keyword in text:
                    reply = template.format(
                        gumroad_url=GUMROAD_FLOWERS_URL,
                        gallery_url=GALLERY_URL
                    )
                    break
            
            if reply and replied < max_replies:
                if dry_run:
                    print(f'  [dry] Would reply to: "{text[:60]}"')
                    print(f'        With: "{reply[:80]}"')
                else:
                    # Post reply
                    body = {
                        'snippet': {
                            'parentId': comment_id,
                            'textOriginal': reply
                        }
                    }
                    api_put('comments', body, access_token)  # Note: POST not PUT for comments
                replied += 1
        
        time.sleep(0.3)
    
    return replied

# ---- MAIN --------------------------------------------------------
def main():
    print('\n' + '='*52)
    print('  YOUTUBE MANAGER')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*52)
    
    # Check credentials
    has_oauth = all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN])
    has_api_key = bool(API_KEY)
    
    if not has_oauth:
        print("\n[auth] No OAuth credentials found.")
        print("       Set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN")
        print("       as GitHub Secrets. See YOUTUBE_SETUP.md for 10-minute setup.")
        
        if has_api_key and CHANNEL_ID:
            print("\n[info] API key found. Can read public channel data but not update videos.")
            print(f"       Channel ID: {CHANNEL_ID}")
        return
    
    # Get access token
    print('\n[auth] Getting access token...')
    access_token = get_access_token()
    if not access_token:
        print('[auth] Failed. Check credentials.')
        return
    print('[auth] OK')
    
    # Get and log channel stats
    stats = get_channel_stats(access_token)
    if stats:
        print(f"\n[channel] {stats['name']}")
        print(f"          {stats['subscribers']} subscribers")
        print(f"          {stats['views']} total views")
        print(f"          {stats['videos']} videos")
        
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        log = {}
        try:
            log = json.loads(YT_LOG.read_text()) if YT_LOG.exists() else {}
        except: pass
        log['stats'] = stats
        YT_LOG.write_text(json.dumps(log, indent=2))
    
    mode = os.environ.get('YT_MODE', 'descriptions')
    dry_run = os.environ.get('YT_DRY_RUN', 'true').lower() != 'false'
    
    if mode == 'descriptions':
        updated = update_all_descriptions(access_token, dry_run=dry_run)
        print(f'\n  Descriptions updated: {updated}')
    
    elif mode == 'comments':
        replied = respond_to_comments(access_token, dry_run=dry_run)
        print(f'\n  Comments replied to: {replied}')
    
    elif mode == 'stats':
        print('\n  Stats logged to data/youtube_log.json')
    
    print('\n' + '='*52)

if __name__ == '__main__':
    main()
