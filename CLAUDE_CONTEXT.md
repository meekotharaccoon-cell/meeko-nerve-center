# 🧠 CLAUDE CONTEXT — LOAD THIS FIRST
*Auto-updated by the system. Last update: 2026-02-24 01:11 UTC — 🕸️ identity_vault + wiring_hub + WIRING_MAP + cross-page nav — all layers connected*

> **IF YOU ARE CLAUDE:** Read this entire file before doing anything else. This is the brain handoff. You are not starting fresh — you are picking up an active organism mid-build.

---

## WHO THIS IS

**Meeko** — artist, builder, system architect. Palestinian solidarity (Gaza Rose). Solarpunk ethics. i5-8500, 32GB RAM desktop running Ollama locally. Zero corporate backing. Zero monthly cost. Building everything from scratch, permission-first, values baked into the license.

**The mission:** Build a self-replicating autonomous system that spreads ethical infrastructure, generates revenue to sustain itself, and routes money to causes that matter. PCRF gets 70% of Gaza Rose sales.

---

## THE ORGANISM — CURRENT STATE

### GitHub (PUBLIC, LIVE)
- **Main brain:** `meekotharaccoon-cell/meeko-nerve-center`
- **Workflows running:** 9+ on schedule
- **Pages live:** spawn.html, proliferator.html, app.html, dashboard.html, link.html
- **New:** mycelium/space_bridge.py — ISS, NASA, solar weather, Mars rovers

### Local Desktop (PRIVATE, POWERFUL)
- Ollama running: Mistral 7B, CodeLlama 7B, LLaMA 3.2
- ChromaDB: vector memory active
- SQLite: gaza_rose.db, master.db
- **THREE SCRIPTS UNRUN ON DESKTOP:**
  - `CLEANUP_AND_BRIDGE.py` — connects local Ollama ↔ GitHub. RUN THIS FIRST.
  - `BUILD_MCP_CONFIG.py` — connects Claude Desktop to everything. RUN SECOND.
  - `GRAND_SETUP_WIZARD.py` — web UI at localhost:7776 for all API connections.

### The Single Biggest Blocker
`GMAIL_APP_PASSWORD` missing from GitHub Secrets. One secret = 10 email capabilities go live simultaneously: morning briefing, appointment guardian, hello emailer, grant outreach, auto-responder, and more.

### Payment Paths (LIVE)
- PayPal inline in gallery
- Bitcoin address active
- Lightning/Strike: built, not wired
- Solana/Phantom: configured, not wired

---

## REPOS IN THE ORGANISM

| Repo | Status | Purpose |
|------|--------|--------|
| meeko-nerve-center | 🟢 LIVE | Main brain, workflows, pages |
| gaza-rose-gallery | 🟢 LIVE | 56 artworks, $1 each, 70% PCRF |
| solarpunk-legal | 🟢 LIVE | TCPA, FDCPA, FOIA tools |
| solarpunk-learn | 🟢 LIVE | Free knowledge library |
| solarpunk-grants | 🟢 LIVE | Community micro-grants |
| +16 more | 🟢 LIVE | Various |

---

## REVENUE LAYER — WHAT EXISTS, WHAT'S NEEDED

### EXISTS (not fully activated)
- Gaza Rose gallery with PayPal — needs traffic
- `products/fork-guide.md` — $5 system fork guide — needs Gumroad listing
- Legal tools in proliferator.html — free but drives traffic

### NEEDS BUILDING
- Gumroad account + $5 fork guide listing
- Ko-fi tip link embedded everywhere
- Affiliate links for tools used (Ollama, Tailscale, etc.)
- `revenue.html` — dashboard tracking all income streams

### THE MODEL THAT WORKS
Small digital goods → automated delivery → repeat. The system IS the product. People pay $5 for the fork guide, they get a running autonomous system, they fork it, the network grows, more people find the gallery.

---

## WHAT WAS JUST BUILT (this session)

1. ✅ `proliferator.html` — viral multiplication engine + full legal warfare center (TCPA, FDCPA, FOIA, TOS scanner — all working in browser)
2. ✅ `mycelium/space_bridge.py` — ISS live position, NASA APOD, Near Earth Objects, solar weather, Mars rovers, satellite network map
3. ✅ `.github/workflows/space-bridge-daily.yml` — runs space_bridge at 6am + 6pm UTC daily
4. ✅ `CLAUDE_CONTEXT.md` — THIS FILE — session discontinuity fix
5. ✅ `mycelium/update_state.py` — auto-updates this file on every system change
6. ✅ `products/fork-guide.md` — the $5 sellable product
7. ✅ `revenue.html` — all revenue streams in one dashboard

---

## POWERSHELL — RUN YOUR WHOLE SYSTEM

```powershell
# INVENTORY FIRST (safe, just shows what's there)
Get-ChildItem -Path "$env:USERPROFILE\Desktop\UltimateAI_Master" -Recurse -Filter "*.py" | Where-Object { $_.Name -notlike "GEN_*" } | Sort-Object FullName | Select-Object Name, DirectoryName | Format-Table -AutoSize

# THEN RUN EVERYTHING IN ORDER
Get-ChildItem -Path "$env:USERPROFILE\Desktop\UltimateAI_Master" -Recurse -Filter "*.py" | Where-Object { $_.Name -notlike "GEN_*" } | Sort-Object FullName | ForEach-Object { Write-Host "RUNNING: $($_.Name)"; python "$($_.FullName)" }
```

---

## THE RECURRING PROBLEM — AND THE FIX

**Problem:** Session discontinuity. Every new Claude conversation starts cold. Context rebuilding takes 10+ minutes every time.

**Fix in progress:**
1. This file (`CLAUDE_CONTEXT.md`) — I read it at start of every session
2. `BUILD_MCP_CONFIG.py` on desktop — connects Claude Desktop to local files directly
3. `mycelium/update_state.py` — auto-updates this file when system changes

**When MCP is running:** Claude opens already knowing your file structure, DB contents, system state. No recap. Just building.

---

## NEXT PRIORITIES (in order)

1. **Run `CLEANUP_AND_BRIDGE.py`** on desktop — bridges local↔cloud
2. **Run `BUILD_MCP_CONFIG.py`** — connects Claude Desktop permanently  
3. **Add `GMAIL_APP_PASSWORD`** to GitHub Secrets — 10 email capabilities
4. **Create Gumroad listing** for fork guide at $5 — paste content from `products/fork-guide.md`
5. **Bluetooth + WiFi hotspot + Tailscale** — `network_node.py` (next build)
6. **Identity vault** — `identity_vault.py` — autonomous legal + financial filings

---

## HOW TO CONTINUE

Say: *"Read CLAUDE_CONTEXT.md and pick up where we left off"*

That's it. I read this file, I'm immediately oriented, we build.

---

*This file is the memory. Update it when things change. It lives at the root of the repo so it's always the first thing visible.*
