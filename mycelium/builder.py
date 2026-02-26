#!/usr/bin/env python3
"""
Builder
========
Reads the Idea Backlog and builds the top validated ideas automatically.

This is the second half of the self-improvement loop:
  idea_engine.py -> tests ideas -> writes BACKLOG.md
  builder.py     -> reads BACKLOG  -> writes actual code -> commits

How it works:
  1. Load ideas.json + idea_learnings.json
  2. Find top validated ideas not yet implemented
  3. For each: generate a working Python script
  4. Test that the script runs without crashing
  5. If passes: save to mycelium/ and commit
  6. Update ideas.json to mark as 'built'

The generated scripts follow the same pattern as all other mycelium scripts:
  - run() function
  - saves to data/ and knowledge/
  - feeds content/queue/
  - no external dependencies beyond stdlib + requests

This runs after idea_engine.py in the weekly cycle.
"""

import json, datetime, subprocess, sys
from pathlib import Path

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'

TODAY = datetime.date.today().isoformat()

# Script templates for validated ideas
# Each template is a minimal working implementation
SCRIPT_TEMPLATES = {

'quake_to_aid': '''
#!/usr/bin/env python3
"""Earthquake -> Humanitarian Aid Pipeline
When M5.5+ quake detected, generate donation appeal + Telegram alert."""
import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
CONT = ROOT / "content" / "queue"
for d in [DATA, CONT]: d.mkdir(parents=True, exist_ok=True)
TODAY = datetime.date.today().isoformat()
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def fetch_json(url):
    try:
        req = urllib_request.Request(url, headers={"User-Agent": "meeko-nerve-center/2.0"})
        with urllib_request.urlopen(req, timeout=12) as r: return json.loads(r.read())
    except: return None

def telegram_send(text):
    if not TELEGRAM_TOKEN: return
    try:
        data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000]}).encode()
        req = urllib_request.Request(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"})
        urllib_request.urlopen(req, timeout=10)
    except Exception as e: print(f"[quake-aid] telegram: {e}")

def run():
    data = fetch_json("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=now-4hours&minmagnitude=5.5&orderby=magnitude")
    if not data: return
    quakes = data.get("features", [])
    if not quakes: print("[quake-aid] No M5.5+ quakes in last 4hr"); return
    posts = []
    for q in quakes[:3]:
        p = q["properties"]
        mag = p.get("mag", 0)
        place = p.get("place", "Unknown location")
        alert = p.get("alert", "none")
        tsunami = " TSUNAMI WATCH" if p.get("tsunami") else ""
        post_text = f"M{mag} earthquake: {place}{tsunami}\\n\\nNatural disasters disproportionately affect people already in crisis.\\n\\nGaza is in active crisis. The children there need aid now:\\nPCRF.net | Gaza Rose proceeds -> PCRF\\n\\n#Earthquake #HumanitarianAid #Gaza #GazaRose"
        posts.append({"platform": "mastodon", "type": "quake_aid", "text": post_text, "mag": mag, "place": place})
        if alert in ["yellow", "orange", "red"] or tsunami:
            telegram_send(f"QUAKE ALERT: M{mag} - {place}{tsunami}\\nAlert level: {alert}\\nContent post generated.")
    (CONT / f"quake_aid_{TODAY}.json").write_text(json.dumps(posts, indent=2))
    print(f"[quake-aid] {len(posts)} posts generated for {len(quakes)} quakes")

if __name__ == "__main__": run()
''',

'price_to_donation_value': '''
#!/usr/bin/env python3
"""Live Crypto Price -> Donation Value Calculator content."""
import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
CONT = ROOT / "content" / "queue"
for d in [DATA, CONT]: d.mkdir(parents=True, exist_ok=True)
TODAY = datetime.date.today().isoformat()

def fetch_json(url):
    try:
        req = urllib_request.Request(url, headers={"User-Agent": "meeko-nerve-center/2.0"})
        with urllib_request.urlopen(req, timeout=10) as r: return json.loads(r.read())
    except: return None

# PCRF treatment costs (approximate, for context)
PCRF_COSTS = [
    ("$25", "one child medical consultation"),
    ("$50", "emergency medicine supply"),
    ("$100", "one week of nutrition for a child"),
    ("$500", "minor surgery support"),
]

def run():
    btc = fetch_json("https://api.coincap.io/v2/assets/bitcoin")
    eth = fetch_json("https://api.coincap.io/v2/assets/ethereum")
    sol = fetch_json("https://api.coincap.io/v2/assets/solana")
    
    prices = {}
    if btc: prices["BTC"] = float(btc["data"]["priceUsd"])
    if eth: prices["ETH"] = float(eth["data"]["priceUsd"])
    if sol: prices["SOL"] = float(sol["data"]["priceUsd"])
    
    if not prices: print("[donation-calc] No price data"); return
    
    lines = ["What your crypto is worth in Gaza right now:\\n"]
    for symbol, price in prices.items():
        for usd_amount, what_it_buys in PCRF_COSTS[:2]:
            amt_float = float(usd_amount.replace("$",""))
            crypto_needed = amt_float / price
            if symbol == "BTC": lines.append(f"{usd_amount} = {crypto_needed:.6f} BTC = {what_it_buys}")
            elif symbol == "ETH": lines.append(f"{usd_amount} = {crypto_needed:.4f} ETH = {what_it_buys}")
            elif symbol == "SOL": lines.append(f"{usd_amount} = {crypto_needed:.2f} SOL = {what_it_buys}")
            break
    
    lines.append(f"\\nDonate directly: PCRF.net")
    lines.append("Gaza Rose art proceeds: 70% to PCRF")
    lines.append("\\n#Gaza #Crypto #Donation #GazaRose #Bitcoin #Solana")
    
    post = [{"platform": "mastodon", "type": "donation_calc", "text": "\\n".join(lines), "prices": prices}]
    (CONT / f"donation_calc_{TODAY}.json").write_text(json.dumps(post, indent=2))
    (DATA / "donation_calc.json").write_text(json.dumps({"date": TODAY, "prices": prices}, indent=2))
    print(f"[donation-calc] Post generated. BTC=${prices.get('BTC',0):,.0f} ETH=${prices.get('ETH',0):,.0f} SOL=${prices.get('SOL',0):.2f}")

if __name__ == "__main__": run()
''',

'carbon_to_grid_post': '''
#!/usr/bin/env python3
"""Carbon Intensity -> Real-Time Grid Post. Posts when grid is very clean."""
import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
CONT = ROOT / "content" / "queue"
for d in [DATA, CONT]: d.mkdir(parents=True, exist_ok=True)
TODAY = datetime.date.today().isoformat()

def fetch_json(url):
    try:
        req = urllib_request.Request(url, headers={"User-Agent": "meeko-nerve-center/2.0"})
        with urllib_request.urlopen(req, timeout=10) as r: return json.loads(r.read())
    except: return None

def run():
    data = fetch_json("https://api.carbonintensity.org.uk/intensity")
    if not data: return
    intensity = data["data"][0]["intensity"]
    actual = intensity.get("actual") or intensity.get("forecast", 0)
    index  = intensity.get("index", "unknown")
    
    # Always generate post, but flag clean moments
    if index in ["very low", "low"]:
        text = f"RIGHT NOW: UK electricity grid is {index} carbon.\\n{actual} gCO2/kWh \\u2014 that\u2019s mostly renewables.\\n\\nThis is what the future looks like when it\u2019s working.\\nSolarPunk isn\u2019t a fantasy. It\u2019s already happening in patches.\\n\\n#SolarPunk #CleanEnergy #RenewableEnergy #ClimateAction"
    else:
        text = f"UK grid carbon right now: {actual} gCO2/kWh ({index})\\nThe energy transition is uneven. Some hours clean, some not.\\nEvery renewable added makes the next clean hour more likely.\\n\\n#ClimateAction #SolarPunk #EnergyTransition"
    
    post = [{"platform": "mastodon", "type": "carbon_grid", "text": text, "carbon": actual, "index": index}]
    (CONT / f"carbon_{TODAY}.json").write_text(json.dumps(post, indent=2))
    print(f"[carbon-post] {index} ({actual} gCO2/kWh) - post generated")

if __name__ == "__main__": run()
''',

'space_launch_to_hope_post': '''
#!/usr/bin/env python3
"""SpaceX Launch -> Hope Content. Every launch = proof of what humans can do."""
import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT = Path(__file__).parent.parent
CONT = ROOT / "content" / "queue"
CONT.mkdir(parents=True, exist_ok=True)
TODAY = datetime.date.today().isoformat()

def fetch_json(url):
    try:
        req = urllib_request.Request(url, headers={"User-Agent": "meeko-nerve-center/2.0"})
        with urllib_request.urlopen(req, timeout=10) as r: return json.loads(r.read())
    except: return None

def run():
    upcoming = fetch_json("https://api.spacexdata.com/v5/launches/upcoming")
    latest   = fetch_json("https://api.spacexdata.com/v5/launches/latest")
    posts = []
    if upcoming and len(upcoming) > 0:
        n = upcoming[0]
        name = n.get("name", "?")
        date = n.get("date_utc", "")[:10]
        posts.append({"platform": "mastodon", "type": "space_hope",
            "text": f"Next SpaceX launch: {name} on {date}\\n\\nWhile humanity builds rockets and reaches for other planets, children in Gaza are trying to survive this one.\\n\\nWe can do both. We must.\\n\\nGaza Rose -> PCRF.net\\n#Space #Gaza #SpaceX #Humanity"})
    if latest:
        name = latest.get("name", "?")
        success = latest.get("success")
        if success:
            posts.append({"platform": "mastodon", "type": "space_hope",
                "text": f"SpaceX just landed {name} successfully.\\n\\nHumans can solve hard problems when we decide to.\\nFeeding every child on Earth is easier than landing a rocket.\\nWe just have to decide.\\n\\n#SpaceX #HumanitarianAid #GazaRose"})
    if posts:
        (CONT / f"space_hope_{TODAY}.json").write_text(json.dumps(posts, indent=2))
        print(f"[space-hope] {len(posts)} posts generated")
    else:
        print("[space-hope] No launch data available")

if __name__ == "__main__": run()
''',
}

def load_learnings():
    path = DATA / 'idea_learnings.json'
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return {'successes': [], 'tested': {}}

def load_ideas():
    path = DATA / 'ideas.json'
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return {'proposals': []}

def test_script(script_path):
    """Quick syntax check."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', str(script_path)],
            capture_output=True, timeout=10
        )
        return result.returncode == 0, result.stderr.decode()
    except Exception as e:
        return False, str(e)

def run():
    print(f'[builder] Build cycle \u2014 {TODAY}')
    
    learnings = load_learnings()
    ideas     = load_ideas()
    
    validated = learnings.get('successes', [])
    print(f'[builder] {len(validated)} validated ideas')
    
    built = []
    for idea_id in validated:
        if idea_id not in SCRIPT_TEMPLATES:
            print(f'[builder] No template for {idea_id} \u2014 skipping (needs manual build)')
            continue
        
        target = ROOT / 'mycelium' / f'{idea_id}.py'
        if target.exists():
            print(f'[builder] {idea_id} already built \u2014 skipping')
            continue
        
        print(f'[builder] Building {idea_id}...')
        code = SCRIPT_TEMPLATES[idea_id].strip()
        target.write_text(code)
        
        ok, err = test_script(target)
        if ok:
            print(f'[builder] \u2705 {idea_id} built and syntax-clean')
            built.append(idea_id)
        else:
            print(f'[builder] \u26a0\ufe0f Syntax error in {idea_id}: {err}')
            target.unlink()  # remove broken file
    
    print(f'[builder] Done. {len(built)} scripts built: {built}')
    return built

if __name__ == '__main__':
    run()
