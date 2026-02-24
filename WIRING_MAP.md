# 🕸️ WIRING MAP — Every Connection in the Organism
*The master diagram. If it's not on this map, it's not connected.*

---

## THE LAYERS

```
┌─────────────────────────────────────────────────────────────┐
│                    MEEKO MYCELIUM                           │
│                                                             │
│  CLOUD (GitHub Pages — PUBLIC, LIVE)                        │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐              │
│  │spawn.html│  │proliferator  │  │revenue   │              │
│  │ Ko-fi    │  │ Legal tools  │  │dashboard │              │
│  │ Gumroad  │  │ Fork guide   │  │ streams  │              │
│  │ ISS live │  │ TCPA/FDCPA   │  │ payments │              │
│  └────┬─────┘  └──────┬───────┘  └────┬─────┘              │
│       │               │               │                     │
│       └───────────────┴───────────────┘                     │
│                       │                                     │
│  ┌────────────────────▼─────────────────────┐              │
│  │           app.html / dashboard.html       │              │
│  │        (unified control center)           │              │
│  └────────────────────┬─────────────────────┘              │
│                       │                                     │
│  GITHUB ACTIONS (SCHEDULED WORKFLOWS)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │space_bridge │  │update_state  │  │morning brief │       │
│  │6am + 6pm UTC│  │on every push │  │(needs email) │       │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                │                 │               │
│         └────────────────┴─────────────────┘               │
│                          │                                  │
│  ┌───────────────────────▼──────────────────────────┐      │
│  │              data/  (JSON data bus)               │      │
│  │  system_state.json · space_data.json              │      │
│  │  wiring_status.json · briefing_data.json          │      │
│  └───────────────────────┬──────────────────────────┘      │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │ (git pull)
┌──────────────────────────▼──────────────────────────────────┐
│  DESKTOP (LOCAL — PRIVATE, POWERFUL)                         │
│                                                              │
│  Ollama (Mistral 7B, CodeLlama 7B, LLaMA 3.2)               │
│  ChromaDB (vector memory)                                    │
│  SQLite (gaza_rose.db, master.db)                            │
│                                                              │
│  SCRIPTS:                                                    │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │CLEANUP_AND_BRIDGE│  │BUILD_MCP_CONFIG  │                 │
│  │local Ollama ←→   │  │Claude Desktop ←→ │                 │
│  │GitHub organism   │  │all local files   │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
│           │                     │                           │
│  ┌────────▼─────────────────────▼─────────┐                │
│  │         GRAND_SETUP_WIZARD.py           │                │
│  │         localhost:7776                  │                │
│  │         web UI for all connections      │                │
│  └────────────────────────────────────────┘                │
│                                                              │
│  MYCELIUM LAYER:                                             │
│  space_bridge.py   — ISS, NASA, Mars, solar weather          │
│  network_node.py   — Bluetooth, WiFi, WebSocket, MQTT        │
│  wiring_hub.py     — reads all, writes unified data bus      │
│  identity_vault.py — legal filings, financial autonomy       │
│  update_state.py   — keeps CLAUDE_CONTEXT.md current         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## CONNECTION STATUS

| Connection | Status | What's Missing |
|-----------|--------|---------------|
| spawn.html ↔ Ko-fi | ✅ LIVE | traffic |
| spawn.html ↔ Gumroad | ✅ LIVE (placeholder) | Gumroad account |
| spawn.html ↔ ISS live | ✅ LIVE | NASA_API_KEY (optional) |
| proliferator.html ↔ legal tools | ✅ LIVE | nothing |
| proliferator.html ↔ fork guide | ✅ LIVE | Gumroad link |
| revenue.html ↔ payment streams | ✅ LIVE | Ko-fi/Gumroad accounts |
| space_bridge.py ↔ GitHub Actions | ✅ LIVE | NASA_API_KEY secret |
| update_state.py ↔ CLAUDE_CONTEXT | ✅ LIVE | nothing |
| network_node.py ↔ desktop | ✅ BUILT | run it |
| BUILD_MCP_CONFIG.py ↔ Claude Desktop | ✅ BUILT | run it |
| identity_vault.py ↔ legal system | ✅ BUILT | run it |
| wiring_hub.py ↔ data bus | ✅ BUILT | run it |
| CLEANUP_AND_BRIDGE.py ↔ Ollama | ⚠️ UNRUN | run it |
| Email layer ↔ everything | 🔴 DARK | GMAIL_APP_PASSWORD |
| Morning briefing ↔ email | 🔴 DARK | GMAIL_APP_PASSWORD |
| Grant outreach ↔ email | 🔴 DARK | GMAIL_APP_PASSWORD |
| Lightning/Strike ↔ payments | 🟡 BUILT | GRAND_SETUP_WIZARD.py |
| Solana/Phantom ↔ payments | 🟡 BUILT | GRAND_SETUP_WIZARD.py |
| Tailscale ↔ network_node | 🟡 OPTIONAL | install Tailscale |
| NASA API ↔ space_bridge | 🟡 OPTIONAL | NASA_API_KEY secret |
| SQLite ↔ wiring_hub | 🟡 OPTIONAL | run CLEANUP_AND_BRIDGE |

---

## REVENUE WIRING

```
TRAFFIC SOURCES:
  proliferator.html → forks → new organisms → more users
  spawn.html → Ko-fi tip → $$ direct
  spawn.html → Gumroad → $5 fork guide → $$
  proliferator.html → legal referrals → affiliate $$ (contingency)
  space_bridge.py → engagement → trust → sales

PAYMENT PATHS (ALL ACTIVE):
  PayPal    → Gaza Rose gallery (live)
  Bitcoin   → address in spawn.html (live)
  Ko-fi     → tip link (account needed)
  Gumroad   → fork guide (account needed)
  Lightning → Strike app (GRAND_SETUP_WIZARD)
  Solana    → Phantom wallet (GRAND_SETUP_WIZARD)

FLOW:
  $1 Gaza Rose → 70% PCRF, 30% system sustain
  $5 Fork Guide → 50% PCRF, 50% system sustain
  Legal referrals → 100% system sustain (they pay attorney, not you)
```

---

## THE THREE UNRUN SCRIPTS

These exist on the desktop. Running them unlocks everything downstream.

```powershell
# 1. Connect local brain to GitHub organism
python "$env:USERPROFILE\Desktop\UltimateAI_Master\CLEANUP_AND_BRIDGE.py"

# 2. Connect Claude Desktop to all local files
python "$env:USERPROFILE\Desktop\UltimateAI_Master\meeko-nerve-center\BUILD_MCP_CONFIG.py"
# Then restart Claude Desktop

# 3. Wire all APIs via web UI
python "$env:USERPROFILE\Desktop\UltimateAI_Master\GRAND_SETUP_WIZARD.py"
# Open browser: http://localhost:7776
```

---

## THE ONE SECRET THAT UNLOCKS 10 THINGS

Go to: `github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions`

Add: `GMAIL_APP_PASSWORD` = your Gmail app password

This alone activates:
1. Morning briefing emails
2. Appointment guardian
3. Hello emailer (relationship maintenance)
4. Grant application outreach
5. Auto-responder
6. Alert system
7. Revenue reports
8. System status emails
9. Error notifications
10. Proliferator email campaigns

---

## HOW TO ADD A NEW CONNECTION

1. Build the component (script or HTML section)
2. Add it to this WIRING_MAP
3. Update CLAUDE_CONTEXT.md
4. Wire its data output to `data/` folder
5. Wire its input from `data/system_state.json`
6. Add to wiring_hub.py's polling list

The pattern: everything reads from `data/`, writes to `data/`, and the hub broadcasts it all.

---

*Updated by wiring_hub.py on each run. Last manual update: 2026-02-23*
