#!/usr/bin/env python3
"""
MEEKO MYCELIUM — AUTONOMOUS REVENUE ENGINE
==========================================
ONE COMPLETE LOOP. ZERO MANUAL STEPS.

What this does:
  1. Reads your 5 Gumroad products
  2. Uses local Ollama AI to write better titles, descriptions, and SEO
  3. Updates products on Gumroad via API
  4. Builds a GitHub Pages storefront (free hosting, live at meekotharaccoon-cell.github.io)
  5. Monitors sales every hour
  6. Every 48h with no new sales → Ollama rewrites copy and tries again
  7. Every sale → logs it, calculates 70% PCRF amount, updates DB
  8. Runs forever. Stops only to tell you money arrived.

Revenue path: Customer → Gumroad product page → PayPal checkout → Your account
PCRF path:    Sale recorded → 70% calculated → Logged → Donate button shown

Run: python REVENUE_ENGINE.py
Web: http://localhost:7781  (live revenue tracker)
"""

import os, sys, json, sqlite3, time, threading, urllib.request, urllib.parse
import http.server, base64, subprocess, hashlib
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE    = Path(r'C:\Users\meeko\Desktop')
DB_PATH = BASE / 'UltimateAI_Master' / 'gaza_rose.db'
LOG     = BASE / 'UltimateAI_Master' / 'revenue_engine.log'
PORT    = 7781
OWNER   = 'meekotharaccoon-cell'

# ── LOAD SECRETS ────────────────────────────────────────────
secrets_path = BASE / 'UltimateAI_Master' / '.secrets'
for line in secrets_path.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        k, v = k.strip(), v.strip()
        if k and v:
            os.environ[k] = v

GUMROAD_TOKEN = os.environ.get('GUMROAD_TOKEN', '')
CONDUCTOR_TOKEN = os.environ.get('CONDUCTOR_TOKEN', '')

# ── STATE ────────────────────────────────────────────────────
_state = {
    'started': datetime.now().isoformat(),
    'cycle': 0,
    'products': [],
    'total_sales': 0,
    'total_revenue': 0.0,
    'pcrf_owed': 0.0,
    'last_optimize': None,
    'last_sale_check': None,
    'log': [],
    'status': 'starting',
    'storefront_url': '',
}
_lock = threading.Lock()

def log(msg, level='INFO'):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with _lock:
        _state['log'].insert(0, line)
        _state['log'] = _state['log'][:100]
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

# ── DB ───────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('''CREATE TABLE IF NOT EXISTS revenue_sales (
        id TEXT PRIMARY KEY,
        timestamp TEXT, product_id TEXT, product_name TEXT,
        amount_cents INTEGER, currency TEXT,
        pcrf_amount REAL, pcrf_percent REAL DEFAULT 70,
        email TEXT, country TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS revenue_cycles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, action TEXT, result TEXT
    )''')
    conn.commit()
    conn.close()

def record_sale(sale_id, product_name, amount_cents, email='', country=''):
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(
            'INSERT OR IGNORE INTO revenue_sales VALUES (?,?,?,?,?,?,?,?,?,?)',
            (sale_id, datetime.now().isoformat(), sale_id[:8], product_name,
             amount_cents, 'USD', amount_cents * 0.70 / 100, 70.0, email, country)
        )
        conn.commit()
    except Exception as e:
        log(f"DB sale error: {e}")
    finally:
        conn.close()

def get_pcrf_total():
    conn = sqlite3.connect(str(DB_PATH))
    r = conn.execute('SELECT SUM(pcrf_amount) FROM revenue_sales').fetchone()
    conn.close()
    return r[0] or 0.0

# ── GUMROAD API ──────────────────────────────────────────────
def gumroad_get(endpoint):
    req = urllib.request.Request(
        f'https://api.gumroad.com/v2/{endpoint}',
        headers={'Authorization': f'Bearer {GUMROAD_TOKEN}'}
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

def gumroad_put(product_id, data):
    """Update a product on Gumroad."""
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        f'https://api.gumroad.com/v2/products/{product_id}',
        data=encoded,
        method='PUT',
        headers={
            'Authorization': f'Bearer {GUMROAD_TOKEN}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

def fetch_products():
    """Get all Gumroad products with current stats."""
    d = gumroad_get('products')
    products = d.get('products', [])
    with _lock:
        _state['products'] = [
            {
                'id': p.get('id'),
                'name': p.get('name'),
                'price': p.get('price', 0),
                'description': p.get('description', ''),
                'short_url': p.get('short_url', ''),
                'sales_count': p.get('sales_count', 0),
                'revenue': float(p.get('revenue', 0)),
                'thumbnail': p.get('thumbnail_url', ''),
            }
            for p in products
        ]
        _state['total_sales']   = sum(p.get('sales_count', 0) for p in products)
        _state['total_revenue'] = sum(float(p.get('revenue', 0)) for p in products) / 100
        _state['pcrf_owed']     = get_pcrf_total()
    return _state['products']

def check_new_sales():
    """Poll Gumroad sales and record any new ones."""
    try:
        d = gumroad_get('sales')
        sales = d.get('sales', [])
        new_count = 0
        for sale in sales:
            sid = sale.get('id')
            conn = sqlite3.connect(str(DB_PATH))
            exists = conn.execute('SELECT 1 FROM revenue_sales WHERE id=?', (sid,)).fetchone()
            conn.close()
            if not exists:
                record_sale(
                    sid,
                    sale.get('product_name', 'Unknown'),
                    sale.get('price', 0),
                    sale.get('email', ''),
                    sale.get('country', '')
                )
                new_count += 1
                amount = sale.get('price', 0) / 100
                log(f"NEW SALE: {sale.get('product_name')} ${amount:.2f} — PCRF gets ${amount*0.70:.2f}")
        
        with _lock:
            _state['last_sale_check'] = datetime.now().isoformat()
        return new_count
    except Exception as e:
        log(f"Sale check error: {e}")
        return 0

# ── OLLAMA AI OPTIMIZER ──────────────────────────────────────
def ask_ollama(prompt, model='llama3.2:latest'):
    try:
        payload = json.dumps({
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.6, 'num_predict': 300}
        }).encode()
        req = urllib.request.Request(
            'http://localhost:11434/api/generate', data=payload,
            headers={'Content-Type': 'application/json'}
        )
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read()).get('response', '').strip()
    except Exception as e:
        log(f"Ollama error: {e}")
        return None

def optimize_product(product):
    """Use local AI to write better copy for a product."""
    name = product['name']
    current_desc = product.get('description', '')[:300]
    price_dollars = product.get('price', 0) / 100

    prompt = f"""You are an expert copywriter for digital products.

Product: "{name}"
Current price: ${price_dollars:.2f}
Current description snippet: {current_desc}

This product is sold on Gumroad. The seller donates 70% of every sale to PCRF (Palestine Children's Relief Fund).

Write an optimized product listing with:
1. A compelling title (max 60 chars)
2. A persuasive description (150-200 words) that:
   - Opens with the buyer's problem/desire
   - Lists 3 specific benefits
   - Mentions the 70% PCRF donation (this is a real differentiator)
   - Ends with a clear call to action
3. Five SEO tags (comma-separated)

Format your response as JSON:
{{"title": "...", "description": "...", "tags": "tag1, tag2, tag3, tag4, tag5"}}

Write only the JSON, no other text."""

    response = ask_ollama(prompt)
    if not response:
        return None
    
    # Extract JSON from response
    try:
        # Find JSON block
        start = response.find('{')
        end   = response.rfind('}') + 1
        if start >= 0 and end > start:
            data = json.loads(response[start:end])
            return data
    except Exception as e:
        log(f"JSON parse error for {name}: {e}")
    return None

def run_optimization_cycle():
    """Fetch products, optimize copy, push updates to Gumroad."""
    log("Starting optimization cycle...")
    products = fetch_products()
    
    if not products:
        log("No products found on Gumroad")
        return
    
    optimized = 0
    for product in products:
        pid  = product['id']
        name = product['name']
        log(f"  Optimizing: {name}")
        
        new_copy = optimize_product(product)
        if not new_copy:
            log(f"  Could not generate copy for {name}")
            continue
        
        # Push update to Gumroad
        try:
            update_data = {}
            if new_copy.get('description'):
                update_data['description'] = new_copy['description']
            if new_copy.get('tags'):
                update_data['tags'] = new_copy['tags']
            
            if update_data:
                result = gumroad_put(pid, update_data)
                if result.get('success'):
                    log(f"  Updated {name}: new description + tags pushed")
                    optimized += 1
                else:
                    log(f"  Gumroad update failed for {name}")
        except Exception as e:
            log(f"  Push error for {name}: {e}")
        
        time.sleep(2)  # be gentle with the API
    
    with _lock:
        _state['last_optimize'] = datetime.now().isoformat()
        _state['cycle'] += 1
    
    log(f"Optimization complete: {optimized}/{len(products)} products updated")
    
    # Record cycle
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('INSERT INTO revenue_cycles VALUES (NULL,?,?,?)',
        (datetime.now().isoformat(), 'optimize',
         f'{optimized}/{len(products)} products updated'))
    conn.commit()
    conn.close()
    
    # Rebuild storefront after optimization
    build_storefront()

# ── GITHUB PAGES STOREFRONT ──────────────────────────────────
def build_storefront():
    """Build a free GitHub Pages landing page that drives traffic to Gumroad."""
    products = _state.get('products', [])
    if not products:
        return
    
    product_cards = ''
    for p in products:
        price = p.get('price', 0) / 100
        url   = p.get('short_url', '#')
        name  = p.get('name', 'Product')
        desc  = p.get('description', '')[:120].replace('"', '&quot;').replace('<','').replace('>','')
        product_cards += f'''
        <div class="card">
          <div class="card-name">{name}</div>
          <div class="card-desc">{desc}...</div>
          <div class="card-price">${price:.2f}</div>
          <a class="buy-btn" href="{url}" target="_blank">Get It →</a>
        </div>'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gaza Rose — AI Tools & Digital Products</title>
<meta name="description" content="Professional AI playbooks, tools, and art. 70% of every sale goes directly to PCRF — Palestine Children's Relief Fund.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#060a0e;color:#cce0f0;font-family:'Outfit',sans-serif;min-height:100vh}}
header{{text-align:center;padding:60px 20px 40px;background:linear-gradient(135deg,#0a1520,#0d1f10)}}
header h1{{font-size:clamp(32px,5vw,56px);font-weight:800;color:#00ff88;letter-spacing:-1px}}
header p{{color:#7ab;font-size:18px;margin-top:12px;max-width:600px;margin-inline:auto}}
.pcrf-banner{{background:rgba(255,51,102,0.1);border:1px solid rgba(255,51,102,0.3);
  text-align:center;padding:16px;color:#ff6688;font-size:14px}}
.pcrf-banner strong{{color:#ff3366}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
  gap:24px;max-width:1200px;margin:40px auto;padding:0 20px}}
.card{{background:#0d1520;border:1px solid #152030;border-radius:16px;padding:28px;
  transition:.3s;display:flex;flex-direction:column;gap:12px}}
.card:hover{{border-color:#00ff88;transform:translateY(-4px);box-shadow:0 8px 40px rgba(0,255,136,0.1)}}
.card-name{{font-size:18px;font-weight:700;color:#fff;line-height:1.3}}
.card-desc{{font-size:13px;color:#6a8fa0;line-height:1.6;flex:1}}
.card-price{{font-size:28px;font-weight:800;color:#00ff88}}
.buy-btn{{display:block;text-align:center;padding:14px;background:#00ff88;
  color:#060a0e;border-radius:10px;text-decoration:none;font-weight:700;font-size:15px;
  transition:.2s}}
.buy-btn:hover{{background:#00dd77}}
footer{{text-align:center;padding:40px 20px;color:#3a5060;font-size:13px;border-top:1px solid #152030}}
footer a{{color:#38bdf8;text-decoration:none}}
</style>
</head>
<body>
<header>
  <h1>Gaza Rose</h1>
  <p>Professional AI playbooks, automation tools, and generative art. Built by Meeko.</p>
</header>
<div class="pcrf-banner">
  <strong>70% of every sale</strong> goes directly to 
  <strong><a href="https://give.pcrf.net/campaign/739651/donate" style="color:#ff3366" target="_blank">PCRF — Palestine Children's Relief Fund</a></strong>
</div>
<div class="grid">
  {product_cards}
</div>
<footer>
  <p>Made with local AI. Powered by purpose.</p>
  <p style="margin-top:8px">
    <a href="https://give.pcrf.net/campaign/739651/donate" target="_blank">Donate directly to PCRF →</a>
  </p>
</footer>
</body>
</html>'''
    
    # Push to GitHub Pages repo
    try:
        content_b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
        
        # Check if index.html exists
        r = subprocess.run(
            ['gh', 'api', f'repos/{OWNER}/{OWNER}.github.io/contents/index.html'],
            capture_output=True, timeout=15
        )
        
        args = [
            'gh', 'api', f'repos/{OWNER}/{OWNER}.github.io/contents/index.html',
            '-X', 'PUT',
            '-F', 'message=auto: update storefront from revenue engine',
            '-F', f'content={content_b64}',
        ]
        
        if r.returncode == 0:
            try:
                sha = json.loads(r.stdout).get('sha')
                if sha:
                    args += ['-F', f'sha={sha}']
            except:
                pass
        
        result = subprocess.run(args, capture_output=True, timeout=20)
        
        if result.returncode == 0:
            url = f'https://{OWNER}.github.io/'
            with _lock:
                _state['storefront_url'] = url
            log(f"Storefront live at: {url}")
        else:
            err = result.stderr.decode()[:200]
            if '404' in err or 'Not Found' in err:
                log("GitHub Pages repo doesn't exist yet — creating it...")
                create_github_pages_repo(html)
            else:
                log(f"Storefront push error: {err}")
    except Exception as e:
        log(f"Storefront error: {e}")

def create_github_pages_repo(html_content):
    """Create the username.github.io repo if it doesn't exist."""
    try:
        # Create repo
        r = subprocess.run(
            ['gh', 'api', 'user/repos', '-X', 'POST',
             '-F', 'name=meekotharaccoon-cell.github.io',
             '-F', 'description=Gaza Rose — AI Tools, 70% to PCRF',
             '-F', 'private=false',
             '-F', 'auto_init=true'],
            capture_output=True, timeout=20
        )
        if r.returncode == 0:
            log("Created GitHub Pages repo")
            time.sleep(3)
            build_storefront()  # retry now that repo exists
        else:
            log(f"Repo create error: {r.stderr.decode()[:100]}")
    except Exception as e:
        log(f"Repo create failed: {e}")

# ── MAIN REVENUE LOOP ────────────────────────────────────────
def revenue_loop():
    """The main autonomous loop. Runs forever."""
    log("Revenue engine started. Loop running every hour.")
    
    # Immediate first run
    try:
        fetch_products()
        run_optimization_cycle()
        check_new_sales()
    except Exception as e:
        log(f"First cycle error: {e}")
    
    last_optimize_time = datetime.now()
    
    while True:
        time.sleep(3600)  # check every hour
        
        try:
            # Always check for sales
            new_sales = check_new_sales()
            fetch_products()
            
            if new_sales > 0:
                log(f"REVENUE: {new_sales} new sale(s) this hour!")
                pcrf = get_pcrf_total()
                log(f"PCRF total owed: ${pcrf:.2f}")
            
            # Re-optimize every 48 hours if no sales
            hours_since_optimize = (datetime.now() - last_optimize_time).total_seconds() / 3600
            total_sales = _state.get('total_sales', 0)
            
            if hours_since_optimize >= 48 or (total_sales == 0 and hours_since_optimize >= 12):
                log("Re-optimizing product copy (12h/48h cycle)...")
                run_optimization_cycle()
                last_optimize_time = datetime.now()
                
        except Exception as e:
            log(f"Loop error: {e}")

# ── WEB DASHBOARD ─────────────────────────────────────────────
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="30">
<title>Gaza Rose — Revenue Engine</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Outfit:wght@400;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#060a0e;--panel:#0d1520;--b:#152030;--green:#00ff88;--gold:#ffc800;--rose:#ff3366;--blue:#38bdf8;--text:#cce0f0;--muted:#3a5060;--mono:'Share Tech Mono',monospace;--sans:'Outfit',sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--sans);padding:24px}
h1{font-size:24px;font-weight:800;color:var(--green);font-family:var(--mono)}
.sub{color:var(--muted);font-size:12px;font-family:var(--mono);margin:4px 0 24px}
.big{font-size:48px;font-weight:800;color:var(--green);font-family:var(--mono);margin:8px 0}
.big.gold{color:var(--gold)}
.big.rose{color:var(--rose)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-bottom:24px}
.card{background:var(--panel);border:1px solid var(--b);border-radius:12px;padding:20px}
.card h2{font-family:var(--mono);font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:12px}
.row{display:flex;justify-content:space-between;padding:5px 0;font-size:13px;border-bottom:1px solid rgba(255,255,255,0.03)}
.row:last-child{border:none}
.val{font-family:var(--mono);color:var(--green)}
.val.warn{color:var(--gold)}
.log-item{font-size:11px;font-family:var(--mono);padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.03);color:#7ab}
.log-item:last-child{border:none}
.pcrf-box{background:rgba(255,51,102,0.08);border:1px solid rgba(255,51,102,0.3);border-radius:12px;padding:20px;margin-bottom:24px;text-align:center}
.pcrf-label{font-family:var(--mono);font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#ff6688;margin-bottom:8px}
.donate-btn{display:inline-block;margin-top:12px;padding:12px 24px;background:var(--rose);color:#fff;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px}
a.store{color:var(--blue);font-size:13px}
</style>
</head>
<body>
<h1>GAZA ROSE — REVENUE ENGINE</h1>
<div class="sub" id="ts">Loading...</div>
<div id="content">Loading...</div>
<script>
async function load(){
  const d=await(await fetch('/state')).json();
  document.getElementById('ts').textContent=
    'Cycle '+d.cycle+' | Last check: '+(d.last_sale_check||'—').replace('T',' ').slice(0,19)+
    ' | Optimized: '+(d.last_optimize||'never').replace('T',' ').slice(0,19);
  
  const rev=d.total_revenue||0;
  const pcrf=d.pcrf_owed||0;
  const url=d.storefront_url||'';
  
  document.getElementById('content').innerHTML=`
    <div class="pcrf-box">
      <div class="pcrf-label">PCRF Owed (70% of all sales)</div>
      <div class="big rose">$${pcrf.toFixed(2)}</div>
      <a class="donate-btn" href="https://give.pcrf.net/campaign/739651/donate" target="_blank">Donate to PCRF →</a>
    </div>
    <div class="grid">
      <div class="card">
        <h2>Revenue</h2>
        <div class="big">$${rev.toFixed(2)}</div>
        <div class="row"><span>Total sales</span><span class="val">${d.total_sales||0}</span></div>
        <div class="row"><span>Products live</span><span class="val">${(d.products||[]).length}</span></div>
        ${url?`<div style="margin-top:10px"><a class="store" href="${url}" target="_blank">Storefront: ${url}</a></div>`:'<div style="margin-top:10px;color:var(--muted);font-size:12px">Building storefront...</div>'}
      </div>
      <div class="card">
        <h2>Products</h2>
        ${(d.products||[]).map(p=>`
          <div class="row">
            <span style="font-size:12px">${p.name.slice(0,28)}</span>
            <span class="val">${p.sales_count} sales / $${(p.price/100).toFixed(2)}</span>
          </div>`).join('')}
      </div>
      <div class="card">
        <h2>Engine Status</h2>
        <div class="row"><span>Status</span><span class="val">${d.status||'running'}</span></div>
        <div class="row"><span>Cycle</span><span class="val">${d.cycle}</span></div>
        <div class="row"><span>Ollama</span><span class="val">mycelium</span></div>
        <div class="row"><span>Auto-optimize</span><span class="val">every 48h</span></div>
        <div class="row"><span>Sale check</span><span class="val">every 1h</span></div>
      </div>
    </div>
    <div class="card">
      <h2>Activity Log</h2>
      ${(d.log||[]).slice(0,20).map(l=>`<div class="log-item">${l}</div>`).join('')}
    </div>
  `;
}
load();setInterval(load,30000);
</script>
</body>
</html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            b = DASHBOARD_HTML.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html;charset=utf-8')
            self.send_header('Content-Length', len(b))
            self.end_headers()
            self.wfile.write(b)
        elif self.path == '/state':
            with _lock:
                b = json.dumps(_state, default=str).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(b))
            self.end_headers()
            self.wfile.write(b)
        else:
            self.send_response(404)
            self.end_headers()

# ── ENTRY POINT ──────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "="*58)
    print("  GAZA ROSE — AUTONOMOUS REVENUE ENGINE")
    print("="*58)
    print(f"\n  Dashboard: http://localhost:{PORT}")
    print(f"  Loop: sale check every 1h, optimize every 48h")
    print(f"  PCRF: 70% of every sale auto-calculated")
    print(f"  Press Ctrl+C to stop\n")
    
    init_db()
    
    with _lock:
        _state['status'] = 'running'
    
    # Revenue loop in background
    t = threading.Thread(target=revenue_loop, daemon=True)
    t.start()
    
    # Open dashboard
    import webbrowser
    threading.Timer(2.0, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    
    # Web server
    server = http.server.HTTPServer(('127.0.0.1', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Engine stopped.")
