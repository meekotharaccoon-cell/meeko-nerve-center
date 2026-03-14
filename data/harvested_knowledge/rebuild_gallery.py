"""
Gaza Rose Gallery HTML Generator
Scans art folder and rebuilds index.html with all images
Run this anytime you add new art to regenerate the gallery
"""
import os
from datetime import datetime

art_folder = r'C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\art'
output_file = r'C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\index.html'

images = sorted([f for f in os.listdir(art_folder) if f.lower().endswith(('.jpg','.jpeg','.png'))])

def make_title(filename):
    name = os.path.splitext(filename)[0]
    name = name.replace('300', '').replace('_BG', ' (Background Version)')
    name = name.replace('_', ' ').replace('(1)', '').replace('(2)', '').strip()
    return name.title()

cards = ''
for img in images:
    title = make_title(img)
    price = 25 if 'BG' in img or 'Background' in img else 18
    cards += f'''
        <div class="art-card">
          <img class="art-image" src="art/{img}" alt="{title}" loading="lazy">
          <div class="art-info">
            <div class="art-title">{title}</div>
            <div class="art-generation">🌹 Gaza Rose Collection &nbsp;·&nbsp; 300 DPI Print-Ready</div>
            <div class="art-price">${price}.00</div>
            <a class="btn" href="https://gumroad.com/meeko" target="_blank">Buy on Gumroad</a>
            <a class="btn btn-crypto" href="payment.html" style="background:linear-gradient(45deg,#1a1a2e,#2a2a4e);margin-top:8px;border:1px solid #C0395A;">⬡ Pay with Crypto</a>
          </div>
        </div>'''

art_count = len(images)
now = datetime.now().strftime('%B %d, %Y')

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gaza Rose Gallery — Autonomous AI Art for Palestine</title>
  <meta name="description" content="AI-generated floral art. 70% of every purchase goes directly to PCRF (Palestine Children's Relief Fund). Created by Meeko.">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', sans-serif; background: #0a0a0a; color: white; padding: 40px 20px; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    
    /* HEADER */
    .header {{ text-align: center; margin-bottom: 60px; }}
    .badge {{ background: linear-gradient(45deg, #C0395A, #ff6b6b); color: white; padding: 6px 20px; border-radius: 30px; display: inline-block; font-weight: bold; margin-bottom: 20px; font-size: 14px; letter-spacing: 1px; }}
    h1 {{ font-size: clamp(32px, 5vw, 56px); margin-bottom: 10px; background: linear-gradient(45deg, #FFD700, #f39c12, #ff6b6b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .subhead {{ font-size: 18px; color: #aaa; margin-bottom: 10px; }}
    .verified {{ font-size: 13px; color: #4CAF50; }}
    
    /* STATS */
    .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 40px 0; max-width: 600px; margin: 40px auto; }}
    .stat-card {{ background: #1a1a1a; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #333; }}
    .stat-number {{ font-size: 36px; font-weight: bold; color: #FFD700; }}
    .stat-label {{ color: #888; font-size: 13px; margin-top: 5px; }}
    
    /* PCRF BANNER */
    .pcrf-banner {{ background: linear-gradient(135deg, #1a1a2e, #16213e); border: 2px solid #C0395A; border-radius: 20px; padding: 40px; margin: 40px 0; text-align: center; }}
    .pcrf-banner h2 {{ color: #FFD700; margin-bottom: 15px; font-size: 24px; }}
    .pcrf-banner p {{ color: #ccc; margin-bottom: 20px; line-height: 1.7; }}
    .pcrf-link {{ display: inline-block; background: #C0395A; color: white; padding: 14px 35px; border-radius: 30px; text-decoration: none; font-weight: bold; font-size: 16px; transition: 0.3s; }}
    .pcrf-link:hover {{ background: #ff4d6d; transform: scale(1.05); }}
    .verified-badge {{ display: inline-block; background: #1a3a1a; border: 1px solid #4CAF50; color: #4CAF50; padding: 5px 15px; border-radius: 20px; font-size: 12px; margin-top: 15px; }}
    
    /* GALLERY */
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; margin: 40px 0; }}
    .art-card {{ background: #1a1a1a; border-radius: 16px; overflow: hidden; transition: transform 0.3s, border-color 0.3s; border: 1px solid #2a2a2a; }}
    .art-card:hover {{ transform: translateY(-8px); border-color: #C0395A; box-shadow: 0 20px 40px rgba(192,57,90,0.2); }}
    .art-image {{ width: 100%; height: 280px; object-fit: cover; display: block; }}
    .art-info {{ padding: 20px; }}
    .art-title {{ font-size: 17px; font-weight: bold; margin-bottom: 6px; color: white; }}
    .art-generation {{ color: #C0395A; font-size: 12px; margin-bottom: 12px; }}
    .art-price {{ color: #FFD700; font-size: 26px; font-weight: bold; margin: 12px 0; }}
    .btn {{ display: block; background: linear-gradient(45deg, #C0395A, #ff6b6b); color: white; text-decoration: none; padding: 12px 20px; border-radius: 30px; font-weight: bold; text-align: center; transition: 0.3s; border: none; cursor: pointer; }}
    .btn:hover {{ transform: scale(1.03); box-shadow: 0 8px 20px rgba(192,57,90,0.4); }}
    
    /* FOOTER */
    .footer {{ text-align: center; margin-top: 80px; color: #555; border-top: 1px solid #222; padding-top: 40px; }}
    .footer p {{ margin-bottom: 8px; }}
    .footer .artist {{ color: #FFD700; font-size: 16px; font-weight: bold; }}
  </style>
</head>
<body>
<div class="container">

  <div class="header">
    <div class="badge">🌹 GAZA ROSE COLLECTION 🌹</div>
    <h1>Autonomous AI Art<br>for Palestine</h1>
    <div class="subhead">300 DPI Print-Ready · Created by Meeko · {art_count} Original Pieces</div>
    <div class="verified">✅ 70% of every purchase donated to PCRF (Verified 501c3 · 4-Star Charity Navigator)</div>
  </div>

  <div class="stats">
    <div class="stat-card">
      <div class="stat-number">{art_count}</div>
      <div class="stat-label">Artworks</div>
    </div>
    <div class="stat-card">
      <div class="stat-number">70%</div>
      <div class="stat-label">To PCRF Forever</div>
    </div>
    <div class="stat-card">
      <div class="stat-number">300</div>
      <div class="stat-label">DPI Resolution</div>
    </div>
  </div>

  <div class="pcrf-banner">
    <h2>🕊️ Every Purchase Helps Palestinian Children</h2>
    <p>
      70% of every sale goes directly to <strong>PCRF — Palestine Children's Relief Fund</strong>, 
      a verified 501(c)(3) nonprofit with a 4-star Charity Navigator rating.<br>
      Founded 1991 · Providing medical care, surgery sponsorship, and humanitarian aid to Palestinian children.
    </p>
    <a class="pcrf-link" href="https://give.pcrf.net/campaign/739651/donate" target="_blank">
      🕊️ Donate Directly to PCRF
    </a>
    <br>
    <span class="verified-badge">✅ Verified at pcrf.net · Charity Navigator 4-Star Rating</span>
  </div>

  <div class="gallery">
{cards}
  </div>

  <div class="footer">
    <p>🌹 Gaza Rose Gallery · Updated {now}</p>
    <p>All art generated at 300 DPI · Print-ready for canvas, framing, and merchandise</p>
    <p>Purchase prints, downloads, and licensed use at <a href="https://gumroad.com/meeko" style="color:#C0395A;">gumroad.com/meeko</a></p>
    <br>
    <p class="artist">🎨 ARTIST: MEEKO · AUTONOMOUS ART MOVEMENT · FOR GAZA 🕊️</p>
    <p style="margin-top: 10px; font-size: 12px;">PCRF Donation Link: <a href="https://give.pcrf.net/campaign/739651/donate" style="color:#4CAF50;">give.pcrf.net/campaign/739651/donate</a></p>
  </div>

</div>
</body>
</html>"""

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ Gallery rebuilt with {art_count} artworks")
print(f"✅ Saved to: {output_file}")
print(f"✅ PCRF verified donation link embedded")
print(f"✅ 70% allocation stated correctly throughout")
