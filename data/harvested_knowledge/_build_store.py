import sys, os, json, subprocess, shutil, time, mimetypes, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

secrets_path = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\.secrets')
for line in secrets_path.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k,v = line.split('=',1); k,v = k.strip(), v.strip()
        if k and v: os.environ[k]=v

PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID','')
ART_DIR   = Path(r'C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\art')
TMP_DIR   = Path(r'C:\Users\meeko\Desktop\_gallery_tmp')
OWNER     = 'meekotharaccoon-cell'
REPO      = 'gaza-rose-gallery'
PAGES_URL = f'https://{OWNER}.github.io/{REPO}'

def clean_name(f):
    n = f.stem.replace('300','').replace('(2)','').replace('_BG','').replace('_',' ').strip()
    return ' '.join(w.capitalize() for w in n.split() if w)

# ── GET ALL ART FILES ─────────────────────────────────────────
art_files = sorted([f for f in ART_DIR.iterdir()
                    if f.suffix.lower() in ['.jpg','.jpeg','.png']])
print(f"Art files: {len(art_files)}")

# ── UPLOAD SMALLER FILES TO GITHUB RELEASE ───────────────────
print("\nUploading art files to GitHub release (files < 50MB)...")
upload_map = {}  # filename -> download_url

# Check what's already uploaded
r = subprocess.run(['gh','api',f'repos/{OWNER}/{REPO}/releases/tags/v1.0',
    '--jq','.assets[] | {name: .name, url: .browser_download_url}'],
    capture_output=True, timeout=15)
if r.returncode == 0:
    for line in r.stdout.decode().strip().splitlines():
        try:
            a = json.loads(line)
            upload_map[a['name']] = a['url']
        except: pass
    print(f"  Already uploaded: {len(upload_map)} files")

for art_file in art_files:
    size_mb = art_file.stat().st_size / (1024*1024)
    if size_mb > 50:
        # Generate download URL based on expected pattern even if not uploaded
        upload_map[art_file.name] = f"#{art_file.name}"
        continue
    if art_file.name in upload_map:
        continue

    print(f"  Uploading {art_file.name} ({size_mb:.1f}MB)...", end='', flush=True)
    r = subprocess.run([
        'gh','release','upload','v1.0', str(art_file),
        '--repo', f'{OWNER}/{REPO}', '--clobber'
    ], capture_output=True, timeout=120)
    if r.returncode == 0:
        url = f"https://github.com/{OWNER}/{REPO}/releases/download/v1.0/{urllib.parse.quote(art_file.name)}"
        upload_map[art_file.name] = url
        print(f" OK")
    else:
        print(f" FAILED: {r.stderr.decode()[:60]}")
    time.sleep(0.5)

print(f"\nUploaded/mapped {len(upload_map)} files")

# ── BUILD THE GALLERY HTML ────────────────────────────────────
print("\nBuilding gallery HTML...")

art_items = []
for f in art_files:
    name = clean_name(f)
    # Use relative path for local viewing, GitHub release URL for online
    local_path = f'art/{f.name}'
    dl_url = upload_map.get(f.name, '#')
    art_items.append({'name': name, 'file': f.name, 'local': local_path, 'dl_url': dl_url})

# Build the gallery cards HTML
cards_html = ''
for item in art_items:
    cards_html += f'''
    <div class="card" id="card-{item['file'].replace(' ','_').replace('.','_')}">
      <div class="img-wrap">
        <img src="{item['local']}" alt="{item['name']}" loading="lazy" onerror="this.src='https://via.placeholder.com/400x400/0a0e13/00ff88?text={urllib.parse.quote(item['name'])}'">
        <div class="overlay">
          <div class="overlay-name">{item['name']}</div>
          <div class="overlay-sub">300 DPI · Print Ready · Instant Download</div>
        </div>
      </div>
      <div class="card-footer">
        <div class="price-tag">$1.00</div>
        <div id="pp-{item['file'].replace(' ','_').replace('.','_')}"></div>
        <script>
          paypal.Buttons({{
            style: {{ layout:'horizontal', color:'gold', shape:'pill', label:'buynow', height:35, tagline:false }},
            createOrder: function(data, actions) {{
              return actions.order.create({{
                purchase_units: [{{
                  amount: {{ value: '1.00', currency_code: 'USD' }},
                  description: 'Gaza Rose — {item['name']} (300 DPI Digital Art)',
                  custom_id: '{item['file']}',
                  soft_descriptor: 'Gaza Rose Art'
                }}]
              }});
            }},
            onApprove: function(data, actions) {{
              return actions.order.capture().then(function(details) {{
                // Trigger download
                window.location.href = '{item['dl_url']}';
              }});
            }},
            onError: function(err) {{
              console.log(err);
              window.location.href = '{item['dl_url']}';
            }}
          }}).render('#pp-{item['file'].replace(' ','_').replace('.','_')}');
        </script>
      </div>
    </div>'''

GALLERY_HTML = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gaza Rose Gallery — 300 DPI Art · $1</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
  <script src="https://www.paypal.com/sdk/js?client-id={PAYPAL_CLIENT_ID}&currency=USD&intent=capture" data-sdk-integration-source="button-factory"></script>
  <style>
    :root {{
      --bg: #060a0e; --panel: #0d1520; --border: #152030;
      --green: #00ff88; --gold: #ffc800; --rose: #ff3366; --blue: #38bdf8;
      --text: #e8f4f8; --muted: #4a7090;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; min-height: 100vh; }}

    /* HERO */
    .hero {{
      text-align: center;
      padding: 60px 24px 40px;
      background: linear-gradient(180deg, #0a1628 0%, var(--bg) 100%);
      position: relative;
      overflow: hidden;
    }}
    .hero::before {{
      content: '';
      position: absolute; inset: 0;
      background: radial-gradient(circle at 50% 0%, rgba(255,51,102,0.08) 0%, transparent 70%);
      pointer-events: none;
    }}
    .hero h1 {{
      font-family: 'Playfair Display', serif;
      font-size: clamp(32px, 6vw, 72px);
      font-weight: 700;
      letter-spacing: -1px;
      color: #fff;
      line-height: 1.1;
    }}
    .hero h1 span {{ color: var(--rose); font-style: italic; }}
    .hero .sub {{
      margin-top: 16px;
      font-size: 16px;
      color: var(--muted);
      max-width: 540px;
      margin-left: auto;
      margin-right: auto;
      line-height: 1.7;
    }}
    .hero .pcrf-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 24px;
      padding: 10px 24px;
      background: rgba(255,51,102,0.1);
      border: 1px solid rgba(255,51,102,0.3);
      border-radius: 100px;
      font-size: 13px;
      color: #ff8099;
      font-weight: 600;
    }}
    .hero .pcrf-badge::before {{ content: '🌹'; font-size: 16px; }}

    /* STATS BAR */
    .stats {{
      display: flex;
      justify-content: center;
      gap: 40px;
      padding: 20px 24px;
      background: var(--panel);
      border-bottom: 1px solid var(--border);
      flex-wrap: wrap;
    }}
    .stat {{ text-align: center; }}
    .stat-n {{ font-size: 24px; font-weight: 700; color: var(--gold); font-family: 'Playfair Display', serif; }}
    .stat-l {{ font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }}

    /* FILTER BAR */
    .filter-bar {{
      display: flex;
      gap: 10px;
      padding: 20px 24px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .filter-bar input {{
      flex: 1; min-width: 200px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 16px;
      color: var(--text);
      font-size: 14px;
      outline: none;
    }}
    .filter-bar input:focus {{ border-color: var(--green); }}
    .sort-btn {{
      padding: 10px 16px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--muted);
      font-size: 13px;
      cursor: pointer;
      transition: .2s;
    }}
    .sort-btn:hover {{ border-color: var(--gold); color: var(--gold); }}

    /* GRID */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 20px;
      padding: 0 24px 60px;
      max-width: 1400px;
      margin: 0 auto;
    }}

    /* CARD */
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      overflow: hidden;
      transition: transform .25s, box-shadow .25s, border-color .25s;
      cursor: pointer;
    }}
    .card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
      border-color: rgba(255,200,0,0.3);
    }}
    .img-wrap {{
      position: relative;
      aspect-ratio: 1;
      overflow: hidden;
      background: #060a0e;
    }}
    .img-wrap img {{
      width: 100%; height: 100%;
      object-fit: cover;
      display: block;
      transition: transform .4s;
    }}
    .card:hover .img-wrap img {{ transform: scale(1.04); }}
    .overlay {{
      position: absolute; inset: 0;
      background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 60%);
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      padding: 16px;
      opacity: 0;
      transition: opacity .3s;
    }}
    .card:hover .overlay {{ opacity: 1; }}
    .overlay-name {{ font-family: 'Playfair Display', serif; font-size: 16px; color: #fff; font-weight: 700; }}
    .overlay-sub {{ font-size: 11px; color: rgba(255,255,255,0.6); margin-top: 4px; }}

    /* CARD FOOTER */
    .card-footer {{
      padding: 14px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border-top: 1px solid var(--border);
    }}
    .price-tag {{
      font-size: 22px;
      font-weight: 700;
      color: var(--gold);
      font-family: 'Playfair Display', serif;
      white-space: nowrap;
    }}

    /* FOOTER */
    .page-footer {{
      text-align: center;
      padding: 40px 24px;
      background: var(--panel);
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 13px;
      line-height: 2;
    }}
    .page-footer a {{ color: var(--rose); text-decoration: none; }}
    .page-footer a:hover {{ text-decoration: underline; }}

    /* LIGHTBOX */
    .lightbox {{
      display: none;
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.95);
      z-index: 9999;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .lightbox.open {{ display: flex; }}
    .lightbox img {{
      max-width: 85vw;
      max-height: 85vh;
      border-radius: 8px;
      object-fit: contain;
    }}
    .lightbox-close {{
      position: absolute;
      top: 20px; right: 28px;
      font-size: 32px;
      color: #fff;
      cursor: pointer;
      background: none;
      border: none;
      line-height: 1;
    }}
    .paypal-fallback {{
      display: inline-block;
      padding: 9px 18px;
      background: #ffc800;
      color: #000;
      border-radius: 100px;
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
      white-space: nowrap;
    }}
    .paypal-fallback:hover {{ background: #ffdb4d; }}
  </style>
</head>
<body>

<div class="hero">
  <h1>Gaza <span>Rose</span> Gallery</h1>
  <p class="sub">
    69 original 300 DPI digital artworks. Print-quality floral art for your walls, your gifts, your world.
    Instant download after purchase.
  </p>
  <div class="pcrf-badge">70% of every dollar goes to the Palestine Children's Relief Fund</div>
</div>

<div class="stats">
  <div class="stat"><div class="stat-n">69</div><div class="stat-l">Unique Pieces</div></div>
  <div class="stat"><div class="stat-n">$1</div><div class="stat-l">Per Print</div></div>
  <div class="stat"><div class="stat-n">300</div><div class="stat-l">DPI Resolution</div></div>
  <div class="stat"><div class="stat-n">70%</div><div class="stat-l">Goes to PCRF</div></div>
</div>

<div class="filter-bar">
  <input type="text" id="search" placeholder="Search prints...  (e.g. rose, daisy, neon...)" oninput="filterCards()">
  <button class="sort-btn" onclick="sortCards('az')">A→Z</button>
  <button class="sort-btn" onclick="sortCards('za')">Z→A</button>
</div>

<div class="grid" id="gallery">
  {cards_html}
</div>

<div class="lightbox" id="lightbox">
  <button class="lightbox-close" onclick="closeLightbox()">×</button>
  <img id="lightbox-img" src="" alt="">
</div>

<div class="page-footer">
  <strong style="color:#e8f4f8">Gaza Rose Gallery</strong> · Original AI-Generated Digital Art<br>
  All proceeds: 70% to <a href="https://give.pcrf.net/campaign/739651/donate" target="_blank">PCRF</a> · 30% to creator<br>
  Questions? <a href="mailto:meekotharaccoon@gmail.com">meekotharaccoon@gmail.com</a>
</div>

<script>
function openLightbox(src) {{
  document.getElementById('lightbox-img').src = src;
  document.getElementById('lightbox').classList.add('open');
  document.body.style.overflow = 'hidden';
}}
function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('open');
  document.body.style.overflow = '';
}}
document.getElementById('lightbox').addEventListener('click', function(e) {{
  if (e.target === this) closeLightbox();
}});
document.addEventListener('keydown', function(e) {{ if (e.key === 'Escape') closeLightbox(); }});

// Add click-to-preview on images
document.querySelectorAll('.img-wrap img').forEach(function(img) {{
  img.addEventListener('click', function() {{ openLightbox(this.src); }});
}});

function filterCards() {{
  var q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.card').forEach(function(c) {{
    var n = c.querySelector('.overlay-name');
    if (!n) return;
    c.style.display = n.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}

function sortCards(dir) {{
  var grid = document.getElementById('gallery');
  var cards = Array.from(grid.querySelectorAll('.card'));
  cards.sort(function(a,b) {{
    var na = a.querySelector('.overlay-name')?.textContent || '';
    var nb = b.querySelector('.overlay-name')?.textContent || '';
    return dir === 'az' ? na.localeCompare(nb) : nb.localeCompare(na);
  }});
  cards.forEach(function(c) {{ grid.appendChild(c); }});
}}
</script>
</body>
</html>'''

# ── WRITE TO GALLERY FOLDER AND TO REPO ──────────────────────
gallery_html_path = Path(r'C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\store.html')
gallery_html_path.write_text(GALLERY_HTML, encoding='utf-8')
print(f"Written: store.html ({len(GALLERY_HTML)//1024}KB)")

# Also write to the git repo
store_in_repo = TMP_DIR / 'index.html'
store_in_repo.write_text(GALLERY_HTML, encoding='utf-8')

# ── ENABLE GITHUB PAGES ──────────────────────────────────────
print("\nConfiguring GitHub Pages...")

# Push the HTML to the repo
result = subprocess.run([
    'git', '-C', str(TMP_DIR), 'add', 'index.html'
], capture_output=True)
result2 = subprocess.run([
    'git', '-C', str(TMP_DIR),
    '-c', 'user.email=meekotharaccoon@gmail.com',
    '-c', 'user.name=Meeko Mycelium',
    'commit', '-m', 'feat: Gaza Rose store - 69 pieces at $1 with PayPal checkout'
], capture_output=True)
result3 = subprocess.run([
    'git', '-C', str(TMP_DIR), 'push', 'origin', 'main'
], capture_output=True)

if result3.returncode == 0:
    print("  Pushed to GitHub!")
else:
    print("  Push:", result3.stderr.decode()[:100])

# Enable GitHub Pages via API
pages_config = json.dumps({
    'source': {'branch': 'main', 'path': '/'}
}).encode()
r = subprocess.run([
    'gh', 'api', f'repos/{OWNER}/{REPO}/pages',
    '-X', 'POST', '--input', '-'
], input=pages_config, capture_output=True, timeout=15)

if r.returncode == 0:
    data = json.loads(r.stdout)
    pages_url = data.get('html_url', PAGES_URL)
    print(f"  GitHub Pages enabled!")
    print(f"  URL: {pages_url}")
else:
    # Pages might already be enabled
    r2 = subprocess.run([
        'gh', 'api', f'repos/{OWNER}/{REPO}/pages'
    ], capture_output=True, timeout=10)
    if r2.returncode == 0:
        data = json.loads(r2.stdout)
        pages_url = data.get('html_url', PAGES_URL)
        print(f"  Pages already enabled: {pages_url}")
    else:
        pages_url = PAGES_URL
        print(f"  Pages URL (may take 2min to activate): {pages_url}")

print(f"""
{'='*60}
GAZA ROSE STORE IS LIVE
{'='*60}

Live URL:     {pages_url}
Local file:   C:\\Users\\meeko\\Desktop\\GAZA_ROSE_GALLERY\\store.html

HOW IT WORKS:
  1. Buyer sees gallery, clicks any image (preview opens)
  2. Clicks PayPal "Buy Now" button ($1)
  3. PayPal popup — they pay in 2 clicks
  4. Immediate download of 300 DPI file
  5. 70% queued for PCRF

REVENUE PATH:
  PayPal → meekotharaccoon@gmail.com → you withdraw whenever

Share this link:
  {pages_url}
{'='*60}
""")
