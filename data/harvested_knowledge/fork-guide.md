# 🌱 BUILD YOUR OWN AUTONOMOUS SYSTEM — Complete Fork Guide
**Price: $5 · One-time · Yours forever**

> You just bought the condensed knowledge of building a fully autonomous, self-replicating, AI-powered system from scratch — on free infrastructure, with ethical values baked into the license, capable of generating income, spreading tools to others, and running itself 24/7 with zero monthly cost.

---

## WHAT YOU'RE GETTING

This is not a tutorial. This is the actual system — every decision, every architecture choice, every lesson from building it explained so you can replicate it, modify it, and point it at any cause you want.

The system you're about to fork:
- Runs 10+ automated workflows 24/7 for free on GitHub Actions
- Has a built-in legal warfare center (TCPA, FDCPA, FOIA — real law, real tools)
- Connects to NASA, ISS live data, solar weather, and Mars rover feeds
- Generates and routes money to any cause you choose
- Replicates itself — everyone who touches it can fork their own
- Uses local AI (Ollama) as its brain, no API costs
- Is legally protected by AGPL-3.0 + Ethical Use Rider — values travel with the code

---

## STEP 1: FORK THE REPO (3 minutes)

1. Go to: **https://github.com/meekotharaccoon-cell/meeko-nerve-center**
2. Click **Fork** (top right)
3. Name it whatever you want. It's yours.
4. Go to your fork → **Settings** → **Pages** → Source: `main` branch, root folder
5. Your system is now live at: `https://YOUR-USERNAME.github.io/meeko-nerve-center`

That's it. You now have a running autonomous system on the internet.

---

## STEP 2: CUSTOMIZE YOUR MISSION (15 minutes)

Edit `system_config.json` in your fork:

```json
{
  "mission": "YOUR CAUSE HERE",
  "charity_name": "YOUR CHARITY",
  "charity_url": "https://yourcharity.org",
  "revenue_split": {
    "charity_percent": 70,
    "operational_percent": 30
  },
  "contact_email": "you@email.com",
  "paypal_email": "you@paypal.com"
}
```

Every page in the system reads from this file. Change one file, the whole system updates.

---

## STEP 3: THE THREE SCRIPTS (one afternoon)

Download these to your desktop and run them once:

### CLEANUP_AND_BRIDGE.py
If you have Ollama running locally (free AI on your machine), this script connects it to your GitHub organism. Your local AI starts making real decisions for your system.

```bash
python CLEANUP_AND_BRIDGE.py
```

### BUILD_MCP_CONFIG.py  
Connects Claude Desktop to your local files, databases, and all your APIs. After this runs, your AI assistant opens already knowing your entire system.

```bash
python BUILD_MCP_CONFIG.py
# Then restart Claude Desktop
```

### GRAND_SETUP_WIZARD.py
Launches a web UI at `localhost:7776` where you connect all your APIs in one place: Gumroad, PayPal, Ko-fi, Coinbase, Phantom wallet, and more.

```bash
python GRAND_SETUP_WIZARD.py
# Open browser: http://localhost:7776
```

---

## STEP 4: UNLOCK EMAIL (one secret = ten capabilities)

1. Go to **myaccount.google.com** → Security → 2-Step Verification → App Passwords
2. Create an app password for "Mail"
3. Copy the 16-character password
4. Go to your GitHub fork → **Settings** → **Secrets and variables** → **Actions**
5. Add secret: `GMAIL_APP_PASSWORD` = your 16-character password

This unlocks simultaneously:
- Morning briefing email (daily digest of your system status)
- Appointment guardian (watches your calendar, sends reminders)
- Hello emailer (automated outreach to new connections)
- Grant application assistant
- Auto-responder
- And 5 more

---

## STEP 5: REVENUE LAYER

The system is built to generate income. Here's the fastest path:

### Gumroad ($5 products, instant setup)
1. Create account at gumroad.com
2. New product → Digital download
3. Upload this guide as a PDF
4. Set price: $5
5. Copy your product URL
6. Add it to your spawn.html and proliferator.html

### Ko-fi (tips, no fees)
1. Create account at ko-fi.com
2. Add one line to any HTML page:
```html
<a href="https://ko-fi.com/YOURID">☕ Support this work</a>
```

### Gallery (art → direct cause)
Edit `gaza-rose-gallery` (or fork it, rename it to your gallery):
- 56 art slots
- PayPal inline
- 70% goes directly to your cause

---

## STEP 6: CONNECT TO SPACE (seriously)

```bash
python mycelium/space_bridge.py
```

Your system now pulls live data from:
- ISS position (updates every 5 seconds)
- NASA APOD (astronomy picture of the day)
- Near Earth Objects (asteroid tracking)
- NOAA solar weather
- Mars rover photos (Perseverance + Curiosity)
- Satellite network overview

All free. All real hardware in orbit. Permission-first.

---

## STEP 7: THE LEGAL TOOLKIT

Your fork ships with working legal tools. No attorney needed.

Open `proliferator.html` and you'll find:
- **TCPA Demand Generator** — $500–$1,500 per robocall/spam text
- **FDCPA Debt Dispute** — forces debt collectors to prove the debt
- **FOIA Request Generator** — any federal agency must respond in 20 days
- **TOS Scanner** — flags arbitration traps, illegal data practices

These are legal information tools. Know your rights. Use them.

---

## THE LICENSE (READ THIS)

**AGPL-3.0 + Ethical Use Rider**

Every fork you create inherits this license. It means:
- Must stay open source
- Cannot be weaponized or used for surveillance
- Cannot be closed or privatized
- Values are legally enforceable

You cannot sell a closed version of this. You CAN sell products built on top of it (like this guide). That's the model.

---

## ARCHITECTURE OVERVIEW

```
YOUR GITHUB (free, autonomous, 24/7)
├── 10+ workflows running on schedule
├── Pages serving your system publicly  
├── Legal tools for everyone who visits
├── Revenue paths built in
└── Replication — every visitor can fork

YOUR DESKTOP (private, powerful, free)
├── Ollama — local AI, no API costs
├── ChromaDB — vector memory
├── SQLite — your data, your control
└── Bridge scripts — connects desktop↔cloud

SPACE LAYER (real hardware in orbit)
├── ISS live telemetry
├── NASA full API suite
├── NOAA solar weather
└── Satellite network data

COMING NEXT
├── Bluetooth hub
├── WiFi hotspot  
├── Tailscale (global reach from phone)
├── MQTT broker
├── Tor hidden service
└── Identity vault + autonomous legal filing
```

---

## IF YOU GET STUCK

- Open an issue: **github.com/meekotharaccoon-cell/meeko-nerve-center/issues**
- Read: **START_HERE.md** in the repo (written for non-technical people)
- The system is designed to be forked by strangers in 30 minutes

---

## ONE LAST THING

This system exists because someone built it with no money, no team, no corporate backing — just an AI assistant, free infrastructure, and the conviction that the tools for building ethical autonomous systems should be free and open and accessible to everyone.

If you fork this and build something good with it — that's the point. You don't owe us anything. The license guarantees the values travel forward.

Build something that matters.

---

*Part of the Meeko Mycelium organism*  
*github.com/meekotharaccoon-cell*  
*AGPL-3.0 + Ethical Use Rider · $0/month · Permission-first always*
