# 🕸️ WIRING MAP — Meeko Mycelium
*Every connection between every layer. Updated as new wires are added.*

---

## DATA FLOWS (ACTIVE)

```
SPACE BRIDGE (space_bridge.py)
  ↓ ISS position, crew, solar wind, NASA APOD, Mars rovers
  → orchestrator_bus.json              [WIRED ✓]
  → morning_briefing.py (reads bus)    [WIRED ✓]
  → network_node.py (WebSocket bcast)  [NEEDS: run --websocket first]
  → cross_poster.py (APOD post)        [NEEDS: social API keys]
  → spawn.html (live widget)           [WIRED ✓ — updates every 10s]

ORCHESTRATOR.py
  → morning_cycle: space→signal→briefing→outreach→grants→state
  → evening_cycle: space→pulse→cross_poster→seo→revenue→evolve→state
  → revenue_layer: monetization→snapshot→grants
  → mesh_layer: github_forks→network_node→connection_mapper→outreach
  → data bus: all layers share data    [WIRED ✓]

MORNING_BRIEFING.py
  ← orchestrator_bus.json (ISS, crew, solar)
  ← revenue_snapshot.json
  ← data/grants/scan_*.json
  ← GitHub API (gallery traffic)
  → email to mickowood86@gmail.com     [NEEDS: GMAIL_APP_PASSWORD]

IDENTITY_VAULT.py
  → TCPA demand letters                [WIRED ✓]
  → FOIA request letters               [WIRED ✓]
  → Artist attestation certs           [WIRED ✓]
  → SHA256 + GPG signing               [WIRED ✓]
  → Wallet address management          [WIRED ✓]
  → Grant applications (identity)      [feeds grant_outreach.py]

GRANT_OUTREACH.py
  ← identity_vault (applicant info)   [WIRED ✓]
  → data/grants/ scan JSONs            [WIRED ✓]
  → data/grants/ application packages [WIRED ✓]
  → morning_briefing (reads scan data) [WIRED ✓]
  → ORCHESTRATOR runs it daily         [WIRED ✓]

NETWORK_NODE.py
  → BLE scan (requires bleak)          [READY: pip install bleak]
  → WiFi/LAN discovery                 [WIRED ✓]
  → WebSocket server :8765             [WIRED ✓]
  → MQTT presence (requires paho)      [READY: pip install paho-mqtt]
  → GitHub fork count (global mesh)    [WIRED ✓]
  → Tailscale check                    [WIRED ✓]

REVENUE LAYER
  spawn.html → Ko-fi, Sponsors, Gumroad, PayPal, BTC  [WIRED ✓]
  proliferator.html → legal tools drive traffic        [LIVE ✓]
  revenue.html → all streams in one dashboard          [LIVE ✓]
  monetization_tracker.py → revenue_snapshot.json     [WIRED ✓]
  morning_briefing ← revenue_snapshot                 [WIRED ✓]
```

---

## CONNECTIONS STILL NEEDED

| From | To | Blocker |
|------|----|--------|
| cross_poster.py | NASA APOD daily post | Needs social API keys |
| lightning_checkout.js | spawn.html + gallery | Needs Strike API key |
| Solana/Phantom | gallery checkout | Needs GRAND_SETUP_WIZARD.py run |
| GMAIL_APP_PASSWORD | ALL email scripts | Add to GitHub Secrets |
| Gumroad listing | spawn.html $5 link | Create listing at gumroad.com |
| Ko-fi page | spawn.html button | Create page at ko-fi.com |
| GitHub Sponsors | FUNDING.yml | Enable at github.com/sponsors |
| identity_vault wallets | spawn.html BTC section | Run --init to set addresses |
| network_node WebSocket | space_bridge data | Run both: WS then space --push |
| evolve.py | README auto-update | Needs GITHUB_TOKEN in Actions |

---

## NEW REVENUE IDEAS FROM CROSS-WIRING

### 1. Space Data as a Service
- `space_bridge.py --serve` → WebSocket stream of ISS/solar data
- Anyone connecting to your WS node gets live space data
- Add tip request in the WS welcome message
- Wires: `network_node.py --websocket` ← `space_bridge` → broadcast

### 2. Legal Doc Generation as a Micro-Service
- `identity_vault.py --generate-tcpa` creates a signed document
- Add a simple web form to proliferator.html that POSTs to local API
- $1-5 per generated document (premium version with pre-filled identity)
- Wires: `proliferator.html` → local Flask API → `identity_vault.py`

### 3. FOIA Subscription
- `grant_outreach.py` already tracks grant deadlines
- Add FOIA alert: auto-generate + email FOIA requests for specific agencies
- Wires: `grant_outreach.py` → `identity_vault.generate_foia` → `mailer_pro.py`

### 4. Fork-and-Earn Program
- Every fork = a new autonomous node
- `network_node.py --mesh` tracks fork count from GitHub API
- Auto-email fork owners via `community_outreach.py`
- Include Ko-fi + Gumroad links in outreach
- Wires: mesh_layer → `community_outreach.py` → revenue links

### 5. Artist Cert NFT-style
- `identity_vault.py --artist-cert` generates signed certificates
- Each cert has unique ID (SHA256-based)
- Post cert to IPFS → permanent, verifiable, shareable
- Wires: `identity_vault.py` → IPFS upload → cert URL in gallery

### 6. Space Weather Alerts
- `space_bridge.py` tracks Kp index (geomagnetic storm level)
- When Kp > 5 (storm), auto-post alert to all social channels
- Premium: email alert subscribers directly
- Wires: `space_bridge.py` → `cross_poster.py` → `mailer_pro.py`

### 7. Morning Briefing as a Product
- The briefing itself (space + revenue + grants) is valuable
- Create a simple signup form → `mycelium_hello.py` adds to list
- Weekly digest of space data + legal tips → `mailer_pro.py`
- Wires: `mycelium_hello.py` → `morning_briefing.py` → subscriber list

---

## PATTERN THAT REPEATS

```
1. COLLECT data from any source (space, legal, social, financial)
2. PROCESS through AI or script
3. DISTRIBUTE across all channels (email, social, website, WebSocket)
4. MONETIZE where there's value (tips, docs, subscriptions, guides)
5. ROUTE proceeds to causes
6. REPEAT at next layer
```

Every new data source = new content = new audience = new revenue path.
Every new revenue path = new funds = new capabilities = more data sources.
The loop tightens with each cycle.

---

## ONE-LINE COMMANDS TO WIRE EACH LAYER

```bash
# Run full organism daily cycle
python mycelium/ORCHESTRATOR.py

# Space data → bus → everything that reads it
python mycelium/space_bridge.py --push

# Network discovery + mesh outreach
python mycelium/ORCHESTRATOR.py --mesh

# Revenue audit
python mycelium/ORCHESTRATOR.py --revenue

# Status of all layers
python mycelium/ORCHESTRATOR.py --status

# Sign a legal document
python mycelium/identity_vault.py --sign YOUR_FILE.txt

# Generate TCPA demand (for a robocall you received)
python mycelium/identity_vault.py --generate-tcpa

# Scan grant opportunities
python mycelium/grant_outreach.py

# Generate application for top grant
python mycelium/grant_outreach.py --apply "NLnet Foundation"

# Start WebSocket hub (real-time data stream)
python mycelium/network_node.py --websocket
```

---
*This file is the connective tissue map. Update it every time a new wire is added.*
*The pattern: wire one layer → discover two more → wire those → repeat.*
