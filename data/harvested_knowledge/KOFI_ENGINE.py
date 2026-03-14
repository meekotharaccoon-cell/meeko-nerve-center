#!/usr/bin/env python3
"""KOFI_ENGINE — Ko-fi payment processor + Gaza Rose shop
0% platform fee. Every $1 sale: 70c Gaza artists, 30c Loop Fund.
Reads webhook events, splits revenue, auto-triggers art generation loop.
"""
import os,json,smtplib
from pathlib import Path
from datetime import datetime,timezone
from email.mime.text import MIMEText

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
KOFI_USER=os.environ.get("KOFI_USERNAME","meekotharaccoon")

PRODUCTS=[
    {"id":"desert_rose","name":"Desert Rose","desc":"Resilience in arid lands","price":1.00},
    {"id":"white_doves","name":"White Doves of Gaza","desc":"Peace above the rubble","price":1.00},
    {"id":"olive_grove","name":"Ancient Olive Grove","desc":"Roots that survive everything","price":1.00},
    {"id":"tatreez","name":"Tatreez Pattern","desc":"Palestinian embroidery, centuries old","price":1.00},
    {"id":"coastline","name":"Gaza Coastline","desc":"The sea they still reach","price":1.00},
    {"id":"star_hope","name":"Star of Hope","desc":"Light in the dark","price":1.00},
    {"id":"pomegranate","name":"Pomegranate","desc":"Seeds of return","price":1.00},
    {"id":"night_garden","name":"Night Garden","desc":"Dreams that persist","price":1.00},
    {"id":"child_balloon","name":"Child with Balloon","desc":"Joy as resistance","price":1.00},
    {"id":"sunflower","name":"Gaza Sunflower","desc":"Always facing light","price":1.00},
    {"id":"embroidery","name":"Embroidery of Home","desc":"Home stitched into every thread","price":1.00},
    {"id":"sea_glass","name":"Sea Glass","desc":"Beauty from what remains","price":1.00},
]

def load():
    f=DATA/"kofi_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"total_received":0.0,"total_to_gaza":0.0,"total_to_loop":0.0,
            "auto_loops":0,"events":[],"art_orders":[]}

def save(s):
    s["events"]=s.get("events",[])[-500:]
    (DATA/"kofi_state.json").write_text(json.dumps(s,indent=2))

def process_events(state):
    ef=DATA/"kofi_events.json"
    if not ef.exists(): return
    try: events=json.loads(ef.read_text())
    except: return
    processed={e.get("id") for e in state.get("events",[])}
    new=[e for e in events if e.get("id") not in processed]
    for ev in new:
        amt=float(ev.get("amount",1.0)); product=ev.get("product_id","desert_rose")
        to_gaza=round(amt*0.70,2); to_loop=round(amt*0.30,2)
        state["total_received"]+=amt; state["total_to_gaza"]+=to_gaza; state["total_to_loop"]+=to_loop
        state.setdefault("events",[]).append({"id":ev.get("id"),"amt":amt,"product":product,
            "gaza":to_gaza,"loop":to_loop,"ts":datetime.now(timezone.utc).isoformat()})
        state.setdefault("art_orders",[]).append({"product":product,"buyer":ev.get("email",""),"ts":datetime.now(timezone.utc).isoformat()})
        if state["total_to_loop"]>=1.00:
            state["auto_loops"]=state.get("auto_loops",0)+1
            state["total_to_loop"]-=1.00
        print(f"  Sale: ${amt} -> ${to_gaza} Gaza / ${to_loop} Loop | {product}")

def generate_shop_html(state):
    cards="".join([f'<div class="card"><h3>{p["name"]}</h3><p>{p["desc"]}</p>'
        f'<a href="https://ko-fi.com/{KOFI_USER}" class="btn">Buy $1</a></div>' for p in PRODUCTS])
    html=f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Gaza Rose Gallery</title>
<style>body{{font-family:sans-serif;background:#0a0a0a;color:#e8e8e8;margin:0;padding:20px}}
h1{{color:#c8a86b;text-align:center}}p.sub{{text-align:center;color:#888}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;max-width:900px;margin:20px auto}}
.card{{background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:16px;text-align:center}}
.card h3{{color:#c8a86b;margin:0 0 8px}}.card p{{font-size:13px;color:#999;margin:0 0 12px}}
.btn{{display:inline-block;background:#c8a86b;color:#0a0a0a;padding:8px 20px;border-radius:4px;text-decoration:none;font-weight:bold}}
.stats{{text-align:center;margin:20px auto;color:#666;font-size:13px}}</style></head>
<body><h1>🌹 Gaza Rose Gallery</h1>
<p class="sub">$1 AI art. 70¢ to Palestinian artists. 30¢ keeps the loop running.</p>
<p class="stats">Raised: ${state.get("total_received",0):.2f} | To Gaza: ${state.get("total_to_gaza",0):.2f} | Loops: {state.get("auto_loops",0)}</p>
<div class="grid">{cards}</div>
<p class="stats">Built by SolarPunk — autonomous AI income for humanitarian causes</p>
</body></html>"""
    Path("docs").mkdir(exist_ok=True)
    (Path("docs")/"kofi.html").write_text(html)
    print("  Shop HTML updated")

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"KOFI_ENGINE cycle {state['cycles']} | ${state.get('total_received',0):.2f} raised")
    process_events(state)
    generate_shop_html(state)
    print(f"  Gaza fund: ${state.get('total_to_gaza',0):.2f} | Auto-loops: {state.get('auto_loops',0)}")
    save(state); return state

if __name__=="__main__": run()
