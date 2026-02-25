# 🧠 CLAUDE CONTEXT — LOAD THIS FIRST
*Auto-updated by the system. Last update: 2026-02-25 21:22 UTC — first local harvest run*

> **IF YOU ARE CLAUDE:** Read this entire file before doing anything else. You are not starting fresh — you are picking up an active organism mid-build. Everything below is verified state.

---

## WHO THIS IS

**Meeko** — artist, builder, system architect. Palestinian solidarity (Gaza Rose). Solarpunk ethics. i5-8500, 32GB RAM desktop running Ollama locally. Zero corporate backing. Zero monthly cost. Building everything from scratch, permission-first, values baked into the license.

**The mission:** Self-replicating autonomous system that spreads ethical infrastructure, generates revenue to sustain itself, and routes money to causes that matter. PCRF gets 70% of Gaza Rose sales.

---

## THE ORGANISM — VERIFIED CURRENT STATE

### GitHub (PUBLIC, LIVE — verified 2026-02-24)
- **Main brain:** `meekotharaccoon-cell/meeko-nerve-center`
- **Workflows:** 10+ running on schedule
- **Pages live:** spawn.html, proliferator.html, revenue.html, app.html, dashboard.html, link.html
- **Base URL:** `https://meekotharaccoon-cell.github.io/meeko-nerve-center/`

### Local Desktop (PRIVATE, POWERFUL)
- Ollama: Mistral 7B, CodeLlama 7B, LLaMA 3.2 ← running
- ChromaDB: vector memory ← active
- SQLite: gaza_rose.db, master.db ← active
- **THREE SCRIPTS STILL UNRUN:**
  - `CLEANUP_AND_BRIDGE.py` — connects Ollama ↔ GitHub. **RUN THIS FIRST.**
  - `BUILD_MCP_CONFIG.py` — connects Claude Desktop to everything. Run second.
  - `GRAND_SETUP_WIZARD.py` — web UI at localhost:7776 for all API wiring.

### Single Biggest Blocker
`GMAIL_APP_PASSWORD` not in GitHub Secrets. One secret = 10 email capabilities live simultaneously.

---

## EVERYTHING BUILT — COMPLETE INVENTORY

### mycelium/ (local Python tools)
| File | Status | What it does |
|------|--------|-------------|
| `space_bridge.py` | ✅ LIVE + scheduled | ISS, NASA APOD, Near Earth Objects, solar weather, Mars rovers |
| `network_node.py` | ✅ BUILT | Bluetooth BLE, WiFi scan, WebSocket server, MQTT, Tailscale, mesh |
| `wiring_hub.py` | ✅ BUILT | Cross-layer data bus — reads all layers, writes unified JSON |
| `identity_vault.py` | ✅ BUILT | FOIA, debt validation, cease & desist, credit dispute, SOL, benefits |
| `update_state.py` | ✅ LIVE + scheduled | Auto-updates CLAUDE_CONTEXT.md + data/system_state.json |

### HTML pages (GitHub Pages — public)
| File | Status | What it does |
|------|--------|-------------|
| `spawn.html` | ✅ LIVE | Ko-fi, Gumroad, live ISS widget, sponsor links |
| `proliferator.html` | ✅ LIVE | Viral fork engine + full legal warfare center (TCPA/FDCPA/FOIA) |
| `revenue.html` | ✅ LIVE | All income streams unified dashboard |
| `dashboard.html` | ✅ LIVE | System control panel |
| `app.html` | ✅ LIVE | Main app interface |
| `link.html` | ✅ LIVE | Link hub |

### Products
| File | Status | What it does |
|------|--------|-------------|
| `products/fork-guide.md` | ✅ CONTENT READY | $5 sellable system fork guide — needs Gumroad listing |

### GitHub Actions workflows
| Workflow | Schedule | What it does |
|----------|----------|-------------|
| `space-bridge-daily.yml` | 6am + 6pm UTC | Runs space_bridge, writes data/ |
| `update-state.yml` | On every push | Updates CLAUDE_CONTEXT.md + system_state.json |
| `wiring-hub-daily.yml` | 7am + 7pm UTC | Runs wiring_hub, writes data bus JSON |
| `morning_briefing` + others | Various | 9+ more scheduled workflows |

### Root files
- `BUILD_MCP_CONFIG.py` — run once on desktop, connects Claude Desktop permanently
- `CLAUDE_CONTEXT.md` — THIS FILE — session handoff brain
- `WIRING_MAP.md` — master diagram of all connections
- `IMMORTALITY.md`, `SOLARPUNK.md`, `KNOW_YOUR_RIGHTS.md`, etc.

### data/ (auto-generated JSON bus)
- `system_state.json` — updated on every push by update_state.py
- `wiring_status.json` — full cross-layer status (written by wiring_hub)
- `briefing_data.json` — flattened state for morning email
- `revenue_data.json` — revenue layer state

---

## PAYMENT LAYER — FULL STATUS

| Method | Status | What's needed |
|--------|--------|--------------|
| PayPal | ✅ LIVE (in gallery) | traffic |
| Bitcoin | ✅ LIVE (address in spawn.html) | traffic |
| Ko-fi | 🟡 LINK IN spawn.html | create account |
| Gumroad | 🟡 LINK IN spawn.html | create account + list fork-guide.md at $5 |
| Lightning/Strike | 🟡 BUILT | run GRAND_SETUP_WIZARD.py |
| Solana/Phantom | 🟡 BUILT | run GRAND_SETUP_WIZARD.py |

---

## REVENUE MODEL (the working one)

```
Traffic → proliferator.html (forks → more organisms)
       → spawn.html (Ko-fi tip, Gumroad $5 guide, Bitcoin)
       → Gaza Rose gallery ($1/artwork, 70% PCRF)
       → legal referrals (TCPA/FDCPA attorneys on contingency)
       → affiliates (tools we use and recommend)
```

The system IS the product. Someone buys the $5 fork guide → gets a running organism → forks it → network grows → more people find gallery → more PCRF donations.

---

## CROSS-LAYER CONNECTIONS (built, wiring_hub tracks these)

```
space_bridge → data/space_data.json → spawn.html ISS widget
wiring_hub   → data/wiring_status.json → dashboard.html live status
update_state → CLAUDE_CONTEXT.md → Claude session memory
network_node → websocket :8765 → real-time mesh
identity_vault → ~/.identity_vault/ → legal doc storage
BUILD_MCP_CONFIG → Claude Desktop → local filesystem
```

---

## THE THREE COMMANDS THAT CHANGE EVERYTHING

Run these on your desktop, in this order:

```powershell
# 1. Bridge local brain to GitHub
python "$env:USERPROFILE\Desktop\UltimateAI_Master\CLEANUP_AND_BRIDGE.py"

# 2. Connect Claude Desktop to everything (then restart Claude Desktop)
cd "$env:USERPROFILE\Desktop\UltimateAI_Master\meeko-nerve-center"
git pull
python BUILD_MCP_CONFIG.py

# 3. Wire all APIs
python "$env:USERPROFILE\Desktop\UltimateAI_Master\GRAND_SETUP_WIZARD.py"
# Open: http://localhost:7776
```

---

## ONE SECRET THAT UNLOCKS 10 THINGS

`github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions`

Add `GMAIL_APP_PASSWORD` → activates: morning briefing, grant outreach, appointment guardian, hello emailer, auto-responder, alert system, revenue reports, status emails, error notifications, proliferator campaigns.

Optional but useful: `NASA_API_KEY` (free at api.nasa.gov) → enhances space_bridge.

---

## NEXT PRIORITIES (audited 2026-02-24)

**IMMEDIATE (you can do right now):**
1. Run `CLEANUP_AND_BRIDGE.py` — bridges local↔cloud
2. Run `BUILD_MCP_CONFIG.py` + restart Claude Desktop — fixes session discontinuity permanently
3. Add `GMAIL_APP_PASSWORD` to GitHub Secrets
4. Create Gumroad account → list fork-guide.md at $5

**NEXT BUILD:**
5. Unified nav bar across all HTML pages (spawn, proliferator, revenue, dashboard siloed now)
6. Live `data/wiring_status.json` widget on dashboard.html
7. Affiliate links for Ollama, Tailscale, etc. in proliferator.html
8. Ko-fi + Gumroad account links wired into revenue.html once accounts created
9. NASA_API_KEY as GitHub Secret

**FUTURE:**
- CLEANUP_AND_BRIDGE.py + Ollama integration → local AI generating content
- Morning briefing email chain automation
- Grant application outreach system

---

## HOW TO CONTINUE NEXT SESSION

Say: **"Read CLAUDE_CONTEXT.md and pick up where we left off"**

I'll read this, be immediately oriented, and we build from the exact right place.

See `WIRING_MAP.md` for full connection diagram.

---

*This file is the memory. The organism updates it automatically. It lives at the repo root.*
