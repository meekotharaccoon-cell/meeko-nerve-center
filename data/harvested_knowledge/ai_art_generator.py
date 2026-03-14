#!/usr/bin/env python3
"""
GAZA ROSE - AUTONOMOUS AI ART GENERATOR
Creates new flower art every hour. Adds to gallery automatically.
Artist: Meeko  All proceeds to UNRWA USA
"""

import os
import random
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# =============================================
# YOUR ARTISTIC DNA - NEVER CHANGES
# =============================================
ARTIST = "Meeko"
BITCOIN = "bc1ppmp8e7n8zlxzuafllpdjpdaxmfrrvr46r4jylg6pf38433m4f0ssjeqpah"
SIGNATURE_STYLE = "Generative Flower Art  Humanitarian Series"

# =============================================
# FLOWER SPECIES (YOUR COLLECTION)
# =============================================
FLOWERS = [
    "Gaza Rose", "Palestine Sunflower", "Olive Branch Lily",
    "Cedar of Lebanon", "Jasmine of Jaffa", "Nablus Tulip",
    "Hebron Iris", "Jericho Rose", "Ramallah Lavender",
    "Bethlehem Poppy", "Nazareth Lily", "Golan Orchid"
]

COLORS = [
    "#ff6b6b", "#feca57", "#6b5b95", "#88d8b0", "#ff9ff3",
    "#54a0ff", "#ff6bc6", "#5f27cd", "#00d2d3", "#ff9f43"
]

def generate_artwork():
    """Create one unique flower artwork"""
    
    # Random selection
    flower = random.choice(FLOWERS)
    color = random.choice(COLORS)
    variation = random.randint(1, 9999)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create canvas (1200x1200, 300 DPI ready)
    img = Image.new('RGB', (1200, 1200), color)
    draw = ImageDraw.Draw(img)
    
    # Draw flower pattern (generative)
    for i in range(random.randint(50, 200)):
        x = random.randint(0, 1200)
        y = random.randint(0, 1200)
        size = random.randint(10, 80)
        petal_color = random.choice(COLORS + ['#ffffff', '#000000'])
        draw.ellipse([x, y, x+size, y+size], fill=petal_color, outline=None)
    
    # Add artist signature
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    draw.text((600, 1000), f"{flower} #{variation}", fill='white', anchor='mm', font=font)
    draw.text((600, 1050), f"Artist: {ARTIST}", fill='white', anchor='mm', font=font)
    draw.text((600, 1100), f" 100% to UNRWA USA  Gaza Relief", fill='#ffd700', anchor='mm', font=font)
    
    # Save file
    filename = f"{flower.replace(' ', '_')}_{variation}_{timestamp}.png"
    filepath = os.path.join(r"C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\art", filename)
    img.save(filepath, dpi=(300,300))
    
    print(f"   Created: {flower} #{variation}")
    return filename

def update_gallery_index():
    """Rebuild index.html with ALL artworks (old + new)"""
    
    gallery_path = r"C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY"
    art_path = r"C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\art"
    index_path = os.path.join(gallery_path, "index.html")
    
    # Get all images
    images = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        images.extend(glob.glob(os.path.join(art_path, ext)))
    images.sort(key=os.path.getmtime, reverse=True)
    
    # Build HTML
    html = []
    html.append('<!DOCTYPE html>')
    html.append('<html>')
    html.append('<head>')
    html.append('    <meta charset="UTF-8">')
    html.append('    <meta name="viewport" content="width=device-width, initial-scale=1">')
    html.append('    <title> GAZA ROSE - AUTONOMOUS ART GALLERY</title>')
    html.append('    <link rel="icon" href="data:;base64,=">')
    html.append('    <style>')
    html.append('        body { background: #0a0a0a; color: white; font-family: Arial; padding: 40px; }')
    html.append('        .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 30px; }')
    html.append('        .art-card { background: #1a1a1a; border-radius: 16px; padding: 20px; }')
    html.append('        img { width: 100%; height: 300px; object-fit: cover; border-radius: 8px; }')
    html.append('        .price { color: #ff6b6b; font-size: 24px; font-weight: bold; }')
    html.append('        .artist { color: #feca57; }')
    html.append('        .bitcoin-btn { background: #ff6b6b; color: white; padding: 12px 30px; border: none; border-radius: 30px; cursor: pointer; width: 100%; }')
    html.append('    </style>')
    html.append('</head>')
    html.append('<body>')
    html.append('    <h1> GAZA ROSE - AUTONOMOUS ART GALLERY</h1>')
    html.append(f'    <h3>Artist: {ARTIST}  {len(images)} Artworks  100% to UNRWA USA</h3>')
    html.append('    <div class="gallery">')
    
    for img_path in images:
        img_name = os.path.basename(img_path)
        title = os.path.splitext(img_name)[0].replace('_', ' ').replace('-', ' ')
        html.append(f'        <div class="art-card">')
        html.append(f'            <img src="art/{img_name}">')
        html.append(f'            <h3>{title}</h3>')
        html.append(f'            <p class="artist"> {ARTIST}</p>')
        html.append(f'            <p class="price">.00 USD</p>')
        html.append(f'            <button class="bitcoin-btn" onclick="alert(\' Thank you!\\n\\nSend  BTC to:\\n{BITCOIN}\\n\\n100% to UNRWA USA - Gaza Relief\')">')
        html.append(f'                 BUY WITH BITCOIN ')
        html.append(f'            </button>')
        html.append(f'        </div>')
    
    html.append('    </div>')
    html.append('    <p style="text-align: center; margin-top: 60px; color: #666;">')
    html.append(f'         AI generates new art every hour  Last generation: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    html.append('    </p>')
    html.append('</body>')
    html.append('</html>')
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))
    
    print(f"   Gallery updated with {len(images)} artworks")

def run_forever():
    """Generate art every hour, forever"""
    print("\n AUTONOMOUS AI ART ENGINE STARTED")
    print(f" Artist: {ARTIST}")
    print(f" Bitcoin: {BITCOIN}")
    print(f" Generating new art every hour...\n")
    
    cycle = 1
    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  Generation {cycle}")
        generate_artwork()
        update_gallery_index()
        print(f"   Next generation in 1 hour...")
        cycle += 1
        time.sleep(3600)  # 1 hour

if __name__ == "__main__":
    import glob
    run_forever()
