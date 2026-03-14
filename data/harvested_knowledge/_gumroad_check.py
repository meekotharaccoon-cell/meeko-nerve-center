import sys, os, json, urllib.request, urllib.parse, base64
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

secrets_path = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\.secrets')
for line in secrets_path.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k,v = line.split('=',1); k,v = k.strip(), v.strip()
        if k and v: os.environ[k]=v

gt = os.environ.get('GUMROAD_TOKEN','')

# Get user info
req = urllib.request.Request('https://api.gumroad.com/v2/user',
    headers={'Authorization':'Bearer '+gt})
d = json.loads(urllib.request.urlopen(req, timeout=8).read())
user = d.get('user',{})
email = user.get('email','')
profile = user.get('profile_url','')
print('GUMROAD EMAIL:', email)
print('GUMROAD PROFILE:', profile)
print()

# Get existing products
req2 = urllib.request.Request('https://api.gumroad.com/v2/products',
    headers={'Authorization':'Bearer '+gt})
p = json.loads(urllib.request.urlopen(req2, timeout=8).read())
print('EXISTING PRODUCTS (' + str(len(p.get('products',[]))) + '):')
for prod in p.get('products',[]):
    name = prod.get('name','?')
    price = prod.get('price',0)/100
    url = prod.get('short_url','?')
    pid = prod.get('id','?')
    print('  ' + name + ' | $' + str(price) + ' | ' + url + ' | id:' + pid)
