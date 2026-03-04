#!/usr/bin/env python3
"""
ETSY_SEO_ENGINE — Gaza Rose Gallery SEO Amplifier
Generates 10 Etsy-optimized product descriptions per cycle.
Uses Claude API if available, falls back to templates.

Writes: data/etsy_seo_output.json
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OUT     = Path("data/etsy_seo_output.json")

ART_THEMES = [
    {"title": "Desert Rose at Dawn", "style": "impressionist"},
    {"title": "White Doves Over the Mediterranean", "style": "dreamlike"},
    {"title": "Olive Grove Eternal", "style": "painterly"},
    {"title": "Tatreez Pattern Bloom", "style": "geometric"},
    {"title": "Gaza Coastline at Golden Hour", "style": "landscape"},
    {"title": "Star of Hope Rising", "style": "symbolic"},
    {"title": "Pomegranate Season", "style": "botanical"},
    {"title": "Night Garden in Ruins", "style": "surrealist"},
    {"title": "Child with Balloon", "style": "figurative"},
    {"title": "The Return - Sunflower Field", "style": "hopeful"},
]

SEO_TAGS = [
    "Palestine art print", "Gaza solidarity", "digital wall art",
    "instant download art", "AI generated art", "humanitarian art",
    "bedroom wall decor", "digital download", "printable wall art",
    "unique art print", "social impact art", "Palestinian culture",
    "donation art print"
]

def make_description(theme):
    return f"""{theme['title']} - AI Digital Art Print

{theme['style'].title()} digital artwork that carries meaning beyond aesthetics.

[ROSE] 70c of every $1 supports Gaza Rose Gallery - Palestinian artists & community relief.
[LOOP] 30c feeds the SolarPunk Loop - reinvested to generate more art, more support.

INSTANT DIGITAL DOWNLOAD
- 4000 x 4000px JPEG (300 DPI - print any size)
- Download immediately after payment
- Personal & commercial use included

YOUR PURCHASE MATTERS
This isn't just wall art - it's a small act of solidarity.
Every $1 automatically splits: artist support -> loop fund -> more art.
The loop feeds itself. Your $1 echoes.

Tags: {', '.join(SEO_TAGS)}"""

def try_claude(theme):
    if not API_KEY:
        return None
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-opus-4-6", "max_tokens": 500, "messages": [{
                "role": "user",
                "content": f"""Write an Etsy product description for this digital art:
Title: {theme['title']} | Style: {theme['style']}
- Emotional opening line
- Mention: 70% of sale -> Gaza Rose Gallery
- Download specs (4000px JPEG)  
- 3 bullet "perfect for" points
- Under 250 words
- End with: Tags: Palestine art print, Gaza solidarity, digital wall art, instant download art, AI generated art, humanitarian art, bedroom wall decor, digital download, printable wall art, unique art print, social impact art, Palestinian culture, donation art print"""
            }]}, timeout=20)
        if r.status_code == 200:
            return r.json()["content"][0]["text"]
    except:
        pass
    return None

def main():
    print("ETSY_SEO_ENGINE starting...")
    results = []
    for theme in ART_THEMES:
        print(f"  {theme['title']}...")
        claude_desc = try_claude(theme)
        results.append({
            "title": theme["title"],
            "style": theme["style"],
            "description": claude_desc or make_description(theme),
            "tags": SEO_TAGS,
            "tag_string": ", ".join(SEO_TAGS[:13]),
            "source": "claude" if claude_desc else "template",
            "generated_at": datetime.now(timezone.utc).isoformat()
        })
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_listings": len(results),
        "claude_enhanced": sum(1 for r in results if r["source"] == "claude"),
        "listings": results,
        "note": "Copy-paste each into Etsy -> Add listing. Title as-is.",
        "status": "ready to post"
    }
    OUT.write_text(json.dumps(output, indent=2))
    print(f"Generated {len(results)} Etsy listings ({output['claude_enhanced']} Claude-enhanced)")

if __name__ == "__main__":
    main()
