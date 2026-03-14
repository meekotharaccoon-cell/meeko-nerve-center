import sys, os, json, subprocess, urllib.request, base64
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

secrets_path = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\.secrets')
for line in secrets_path.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k,v = line.split('=',1); k,v = k.strip(), v.strip()
        if k and v: os.environ[k]=v

GT = os.environ.get('GUMROAD_TOKEN','')
PP_ID = os.environ.get('PAYPAL_CLIENT_ID','')
PP_SC = os.environ.get('PAYPAL_CLIENT_SECRET','')
CT = os.environ.get('CONDUCTOR_TOKEN','')

print("=== WHAT IS REAL RIGHT NOW ===\n")

# Gumroad - what products, any sales?
req = urllib.request.Request('https://api.gumroad.com/v2/products',
    headers={'Authorization':'Bearer '+GT})
prods = json.loads(urllib.request.urlopen(req,timeout=8).read()).get('products',[])
print(f"GUMROAD: {len(prods)} products live")
total_sales = 0
for p in prods:
    sales = p.get('sales_count',0)
    revenue = p.get('total_revenue_cents',0)/100
    total_sales += revenue
    print(f"  '{p['name']}' | ${p['price']/100} | {sales} sales | ${revenue:.2f} earned")
print(f"  TOTAL EARNED: ${total_sales:.2f}")

# Art files
art_dir = Path(r'C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\art')
art_files = [f for f in art_dir.iterdir() if f.suffix.lower() in ['.jpg','.jpeg','.png']]
total_size = sum(f.stat().st_size for f in art_files) / (1024*1024*1024)
print(f"\nART: {len(art_files)} files, {total_size:.1f}GB total")

# Gumroad - check if we can create products (test with small payload)
try:
    import urllib.parse
    test_data = urllib.parse.urlencode({
        'name': 'TEST_DELETE_ME',
        'price': '100',
        'published': 'false'
    }).encode()
    req2 = urllib.request.Request('https://api.gumroad.com/v2/products',
        data=test_data,
        headers={'Authorization':'Bearer '+GT,'Content-Type':'application/x-www-form-urlencoded'})
    resp = json.loads(urllib.request.urlopen(req2,timeout=10).read())
    if resp.get('success'):
        prod_id = resp['product']['id']
        # Delete test product
        req3 = urllib.request.Request(f'https://api.gumroad.com/v2/products/{urllib.parse.quote(prod_id)}',
            headers={'Authorization':'Bearer '+GT}, method='DELETE')
        urllib.request.urlopen(req3,timeout=10)
        print("\nGUMROAD API: CAN CREATE PRODUCTS ✓")
        can_create = True
    else:
        print(f"\nGUMROAD API: Cannot create: {resp.get('message','?')}")
        can_create = False
except Exception as e:
    print(f"\nGUMROAD API: Error: {str(e)[:100]}")
    can_create = False

# Ollama
data = json.loads(urllib.request.urlopen('http://localhost:11434/api/tags',timeout=3).read())
models = [m['name'] for m in data.get('models',[])]
print(f"\nOLLAMA: {models}")

# GitHub pages status
r = subprocess.run(['gh','api','repos/meekotharaccoon-cell/gaza-rose-gallery/pages'],
    capture_output=True, timeout=10)
if r.returncode == 0:
    pg = json.loads(r.stdout)
    print(f"\nGITHUB PAGES: {pg.get('html_url','?')} | status: {pg.get('status','?')}")
else:
    print(f"\nGITHUB PAGES: not yet active")

print(f"\nCAP: can_create_gumroad_products={can_create}")
