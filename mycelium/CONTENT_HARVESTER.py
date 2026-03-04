#!/usr/bin/env python3
"""
CONTENT_HARVESTER — Zero-cost content intelligence engine
Uses only FREE public APIs (no keys required):
  - HackerNews API    (trending tech stories)
  - Reddit JSON       (community pulse — no auth, .json suffix)
  - Open-Meteo        (free weather for eco/climate content)
  - DEV.to API        (free tech articles)

Writes: data/content_harvest.json
Output feeds NEURON_A (what to write about) + social posting engines.
"""
import json, requests, time
from pathlib import Path
from datetime import datetime, timezone

OUT = Path("data/content_harvest.json")
HEADERS = {"User-Agent": "SolarPunk/2.0 (Gaza Rose Gallery; humanitarian tech)"}

def fetch_hackernews(limit=5):
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers=HEADERS, timeout=8
        ).json()[:limit]
        stories = []
        for sid in ids:
            s = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                headers=HEADERS, timeout=5).json()
            if s and s.get("title"):
                stories.append({"title": s.get("title",""), "url": s.get("url",""),
                    "score": s.get("score",0), "source": "hackernews"})
            time.sleep(0.1)
        print(f"  HackerNews: {len(stories)} stories")
        return stories
    except Exception as e:
        print(f"  HN error: {e}")
        return []

def fetch_reddit_json(subreddits=None, limit=3):
    if subreddits is None:
        subreddits = ["solarpunk", "Gaza", "technology", "ArtificialIntelligence"]
    posts = []
    for sub in subreddits:
        try:
            r = requests.get(f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}",
                headers=HEADERS, timeout=8)
            if r.status_code == 200:
                for c in r.json().get("data",{}).get("children",[]):
                    d = c.get("data",{})
                    if not d.get("is_video") and d.get("title"):
                        posts.append({"title": d.get("title",""),
                            "url": "https://reddit.com" + d.get("permalink",""),
                            "score": d.get("score",0), "subreddit": sub, "source": "reddit"})
            time.sleep(0.3)
        except Exception as e:
            print(f"  Reddit r/{sub}: {e}")
    print(f"  Reddit: {len(posts)} posts")
    return posts

def fetch_devto(tag="opensource", limit=5):
    try:
        articles = requests.get(
            f"https://dev.to/api/articles?tag={tag}&per_page={limit}&top=7",
            headers=HEADERS, timeout=8).json()
        out = [{"title": a.get("title",""), "url": a.get("url",""),
                "hearts": a.get("positive_reactions_count",0), "source": "devto"}
               for a in articles if isinstance(a, dict) and a.get("title")]
        print(f"  DEV.to: {len(out)} articles")
        return out
    except Exception as e:
        print(f"  DEV.to: {e}")
        return []

def fetch_weather_vibe():
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=31.5&longitude=34.47"
            "&current=temperature_2m,weathercode&timezone=Asia/Gaza", timeout=8).json()
        curr = r.get("current",{})
        temp = curr.get("temperature_2m","?")
        code = curr.get("weathercode",0)
        vibes = {range(0,2):"sunny",range(2,4):"partly cloudy",range(61,68):"rainy",range(71,78):"snowy"}
        vibe = next((v for rng,v in vibes.items() if code in rng), "variable")
        print(f"  Gaza weather: {temp}C {vibe}")
        return {"temp_c": temp, "vibe": vibe, "code": code, "location": "Gaza City"}
    except Exception as e:
        print(f"  Weather: {e}")
        return {}

def distill_themes(all_content):
    words = {}
    skip = {"the","a","an","and","or","is","in","to","of","for","on","with","that","this","how","why",
            "what","are","was","by","at","from","be","it","as","not","but","my","i","you","we","have","has","can"}
    for item in all_content:
        for w in item.get("title","").lower().replace("-"," ").split():
            w = w.strip(".,!?\"'()[]")
            if len(w) > 3 and w not in skip:
                words[w] = words.get(w, 0) + 1
    return [{"word": w, "count": c} for w,c in sorted(words.items(), key=lambda x: x[1], reverse=True)[:20]]

def generate_content_angles(themes, hn_stories, reddit_posts):
    angles = []
    if hn_stories:
        angles.append({"type": "tech_solidarity",
            "hook": f"How '{hn_stories[0]['title'][:60]}...' connects to Gaza resilience",
            "platform": "twitter/linkedin", "effort": "5min"})
    angles.append({"type": "gallery_promo",
        "hook": "$1 gets you AI art. 70c goes to Gaza Rose Gallery. The loop funds itself.",
        "platform": "all", "effort": "30sec",
        "url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center"})
    angles.append({"type": "origin_story",
        "hook": "I built an AI that earns money while I sleep and donates automatically.",
        "platform": "twitter/substack", "effort": "15min"})
    sp = [p for p in reddit_posts if p.get("subreddit") == "solarpunk"]
    if sp:
        angles.append({"type": "community_bridge",
            "hook": f"SolarPunk is talking about: {sp[0]['title'][:80]}",
            "platform": "reddit/twitter", "effort": "10min"})
    return angles

def main():
    print("CONTENT_HARVESTER starting...")
    ts = datetime.now(timezone.utc).isoformat()
    hn = fetch_hackernews(limit=5)
    reddit = fetch_reddit_json()
    devto = fetch_devto(tag="opensource", limit=4)
    weather = fetch_weather_vibe()
    all_content = hn + reddit + devto
    themes = distill_themes(all_content)
    angles = generate_content_angles(themes, hn, reddit)
    harvest = {"timestamp": ts, "sources": {"hackernews": hn, "reddit": reddit, "devto": devto},
        "gaza_weather": weather, "trending_themes": themes, "content_angles": angles,
        "total_items": len(all_content), "status": "harvested"}
    OUT.write_text(json.dumps(harvest, indent=2))
    print(f"Harvested {len(all_content)} items -> {len(angles)} content angles")
    if angles:
        print(f"Best angle: {angles[0]['hook'][:80]}")

if __name__ == "__main__":
    main()
