import sys, os, json, urllib.request, urllib.parse, urllib.error
import base64, time, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

secrets_path = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\.secrets')
for line in secrets_path.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k,v = line.split('=',1); k,v = k.strip(), v.strip()
        if k and v: os.environ[k]=v

GALLERY = Path(r'C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY')
ART_DIR = GALLERY / 'art'
GT = os.environ.get('GUMROAD_TOKEN','')
OWNER = 'meekotharaccoon-cell'

# ── GET ALL ART FILES ────────────────────────────────────────
art_files = sorted([f for f in ART_DIR.iterdir() if f.suffix.lower() in ['.jpg','.jpeg','.png']])
print(f"Found {len(art_files)} art files")

def clean_name(filename):
    name = filename.stem
    name = name.replace('300','').replace('(2)','').replace('_BG','').replace('_',' ').strip()
    return ' '.join(w.capitalize() for w in name.split())

def gumroad_create_product(name, desc, price_cents=100):
    data = urllib.parse.urlencode({
        'name': name,
        'description': desc,
        'price': str(price_cents),
        'published': 'true',
    }).encode()
    req = urllib.request.Request(
        'https://api.gumroad.com/v2/products',
        data=data,
        headers={'Authorization': 'Bearer '+GT, 'Content-Type': 'application/x-www-form-urlencoded'}
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=20).read())
        if resp.get('success'):
            return resp['product']
        else:
            print('  Gumroad create error:', resp.get('message','?'))
            return None
    except Exception as e:
        print('  Error:', e)
        return None

def gumroad_upload_file(product_id, file_path):
    """Upload art file to Gumroad product using multipart."""
    try:
        import mimetypes
        boundary = b'----GazaRoseBoundary'
        file_data = file_path.read_bytes()
        mime = mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream'

        body = b''
        body += b'--' + boundary + b'\r\n'
        body += f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode()
        body += f'Content-Type: {mime}\r\n\r\n'.encode()
        body += file_data + b'\r\n'
        body += b'--' + boundary + b'--\r\n'

        req = urllib.request.Request(
            f'https://api.gumroad.com/v2/products/{urllib.parse.quote(product_id)}/product_files',
            data=body,
            headers={
                'Authorization': 'Bearer '+GT,
                'Content-Type': f'multipart/form-data; boundary={boundary.decode()}',
            }
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
        return resp.get('success', False)
    except Exception as e:
        print(f'    Upload error: {e}')
        return False

# ── LOAD OR BUILD PRODUCT MAP ────────────────────────────────
product_map_path = GALLERY / 'product_map.json'
product_map = {}
if product_map_path.exists():
    product_map = json.loads(product_map_path.read_text(encoding='utf-8'))
    print(f"Loaded {len(product_map)} existing products from map")

# ── CREATE GUMROAD PRODUCTS FOR EACH PIECE ───────────────────
print(f"\nCreating/verifying Gumroad products for {len(art_files)} art pieces...")
created = 0
skipped = 0

for art_file in art_files:
    fname = art_file.name
    if fname in product_map:
        skipped += 1
        continue

    display_name = clean_name(art_file)
    desc = (
        f"**Gaza Rose Collection — {display_name}**\n\n"
        f"High-resolution 300 DPI digital art, ready for printing up to 20x20 inches.\n\n"
        f"*70% of every purchase goes directly to the Palestine Children's Relief Fund (PCRF).*\n\n"
        f"✦ 300 DPI print-ready file\n"
        f"✦ Instant download after purchase\n"
        f"✦ Commercial use permitted\n"
        f"✦ Unique AI-generated floral art\n\n"
        f"**Your $1 makes a difference.**"
    )

    product = gumroad_create_product(
        name=f"Gaza Rose — {display_name}",
        desc=desc,
        price_cents=100
    )

    if product:
        product_id = product['id']
        short_url  = product.get('short_url','')
        print(f"  CREATED: {display_name} -> {short_url}")
        product_map[fname] = {
            'id': product_id,
            'name': display_name,
            'url': short_url,
            'file_uploaded': False
        }
        product_map_path.write_text(json.dumps(product_map, indent=2), encoding='utf-8')
        created += 1
        time.sleep(0.8)  # Be kind to API
    else:
        print(f"  FAILED: {display_name}")

print(f"\nProducts: {created} created, {skipped} already existed, {len(product_map)} total")

# ── UPLOAD FILES FOR SMALLER IMAGES (< 20MB) ─────────────────
print("\nUploading smaller art files to Gumroad...")
uploaded = 0
for art_file in art_files:
    fname = art_file.name
    if fname not in product_map:
        continue
    if product_map[fname].get('file_uploaded'):
        continue
    size_mb = art_file.stat().st_size / (1024*1024)
    if size_mb > 20:
        print(f"  SKIP (too large {size_mb:.0f}MB): {fname}")
        continue

    print(f"  Uploading {fname} ({size_mb:.1f}MB)...")
    pid = product_map[fname]['id']
    ok = gumroad_upload_file(pid, art_file)
    if ok:
        product_map[fname]['file_uploaded'] = True
        product_map_path.write_text(json.dumps(product_map, indent=2), encoding='utf-8')
        print(f"    UPLOADED")
        uploaded += 1
    time.sleep(1)

print(f"Uploaded {uploaded} files")
print(f"\nProduct map saved: {product_map_path}")
print(f"Run _build_gallery_html.py next to generate the store page")
