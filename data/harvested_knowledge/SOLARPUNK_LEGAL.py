#!/usr/bin/env python3
"""
SOLARPUNK_LEGAL.py — SolarPunk™ brand protection, trademark tracking, legal fund counter
=========================================================================================
Tracks:
  - SolarPunk™ usage declaration (™ usable immediately, no registration needed)
  - Money accumulated toward USPTO trademark filing ($250-350/class)
  - DBA ("Doing Business As") filing progress
  - Evidence of first commercial use (critical for trademark priority)
  - Legal document generation

KEY LEGAL ANSWER (researched + stored for the system):
  Q: "Should SolarPunk be a business or an AI agent registration?"
  A: BUSINESS FIRST. Here's why:
     - An AI agent cannot legally own anything: no property, no trademark, no bank account
     - A business entity (DBA/LLC) CAN own the SolarPunk trademark
     - A business entity CAN hold a bank account, sign contracts, receive payments
     - The AI agent is the PRODUCT/TOOL of the business — not the business itself
     - Priority order: DBA ($25-100, 1 day) → ™ usage → Business bank account → USPTO (~$250) → LLC (optional, $50-200)
  
  Q: "What IS SolarPunk legally?"
  A: Right now, SolarPunk is a trade name used in commerce. That gives you common-law ™ rights
     in your geographic area. Filing with USPTO gives you federal ® rights (nationwide).
     "SolarPunk" as an AI SOFTWARE BRAND is likely registrable — the general aesthetic
     movement uses lowercase "solarpunk" but yours is a distinct software brand in Class 42.
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

# Legal milestones tracked by the system
MILESTONES = [
    {
        "id": "first_use",
        "title": "✅ First Commercial Use Documented",
        "description": "SolarPunk™ first used in commerce — common-law trademark rights begin here",
        "cost": 0,
        "auto_complete": True,  # We've been building since day 1
        "notes": "Date of first GitHub commit = date of first commercial use. IMPORTANT: Screenshot + save all public-facing uses."
    },
    {
        "id": "tm_symbol",
        "title": "™ Start Using TM Symbol",
        "description": "Add ™ to SolarPunk on all pages, social, and products. No registration needed.",
        "cost": 0,
        "auto_complete": True,
        "notes": "Added to store.html, social.html, all product pages. This creates public notice."
    },
    {
        "id": "dba_filing",
        "title": "📄 File DBA ('Doing Business As')",
        "description": "Register 'SolarPunk' as your trade name with your county/state. $25-100.",
        "cost": 75,
        "auto_complete": False,
        "how": [
            "Google: '[your state] DBA filing'",
            "Most states: file with County Clerk OR Secretary of State",
            "Cost: usually $25-100",
            "Takes 1-3 business days",
            "You don't need a lawyer — it's a simple form",
            "Once filed: you can open a business bank account under SolarPunk",
        ]
    },
    {
        "id": "business_bank",
        "title": "🏦 Open SolarPunk Business Bank Account",
        "description": "Separate business account — required for PayPal business + cleaner taxes",
        "cost": 0,
        "auto_complete": False,
        "how": [
            "After DBA is filed, take DBA certificate to any bank",
            "Mercury Bank (mercury.com) is best for digital businesses — free, online, no minimums",
            "Relay (relayfi.com) is another great free option",
            "Connect this account to Gumroad, Ko-fi, PayPal Business",
        ]
    },
    {
        "id": "uspto_filing",
        "title": "® USPTO Trademark Registration",
        "description": "File SolarPunk® with USPTO for nationwide protection. ~$250-350.",
        "cost": 350,
        "auto_complete": False,
        "how": [
            "Go to teas.uspto.gov (Trademark Electronic Application System)",
            "File TEAS Plus: $250/class OR TEAS Standard: $350/class",
            "Class 42: Computer software and AI services (your primary class)",
            "Class 35: Business services (secondary — covers the marketplace aspect)",
            "Processing time: 8-12 months",
            "You can file yourself — no lawyer needed for straightforward marks",
            "Alternatively: TrademarkEngine.com (~$149 + USPTO fee) handles paperwork",
        ]
    },
    {
        "id": "llc_formation",
        "title": "🏛️ Form SolarPunk LLC (Optional but recommended)",
        "description": "Liability protection — separates personal assets from business debts",
        "cost": 150,
        "auto_complete": False,
        "how": [
            "File Articles of Organization with your state Secretary of State",
            "Wyoming LLC is popular for digital businesses (low fees, strong privacy)",
            "Cost: $50-200 depending on state",
            "Northwest Registered Agent ($39/year) handles registered agent requirement",
            "After LLC: trademark transfers from you personally to the LLC",
        ]
    },
]


def load_state():
    f = DATA / "solarpunk_legal_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {
        "brand_name": "SolarPunk",
        "first_use_date": "2026-03-05",  # Today — document it
        "milestones_complete": ["first_use", "tm_symbol"],  # Already done
        "legal_fund_usd": 0.0,
        "legal_fund_target_usd": 600.0,  # DBA + USPTO Class 42 + buffer
        "trademark_classes": ["42"],  # Computer software / AI
        "evidence_log": [],
        "notes": [],
        "registered_business": False,
        "trademark_filed": False,
        "trademark_registered": False,
    }


def save_state(s):
    (DATA / "solarpunk_legal_state.json").write_text(json.dumps(s, indent=2))


def update_legal_fund(state):
    """Pull current revenue from revenue_inbox and allocate 5% to legal fund."""
    revenue_f = DATA / "revenue_inbox.json"
    if not revenue_f.exists():
        return state

    try:
        revenue = json.loads(revenue_f.read_text())
        total_received = revenue.get("total_received", 0)
        # 5% of all revenue goes to legal fund (separate from 15% Gaza)
        legal_allocation = round(total_received * 0.05, 2)
        state["legal_fund_usd"] = legal_allocation
        state["legal_fund_source"] = "5% of total revenue"
        state["revenue_total"] = total_received
    except:
        pass

    return state


def log_evidence(state):
    """Auto-log evidence of commercial use (for trademark priority)."""
    evidence = state.get("evidence_log", [])
    now = datetime.now(timezone.utc).isoformat()

    # Check for Gumroad live products
    gl = DATA / "gumroad_listings.json"
    if gl.exists():
        try:
            listings = json.loads(gl.read_text())
            live = listings.get("gumroad_live", 0)
            if live > 0 and not any(e.get("type") == "gumroad_live" for e in evidence):
                evidence.append({
                    "type": "gumroad_live",
                    "ts": now,
                    "description": f"{live} products live on Gumroad under SolarPunk brand",
                })
        except: pass

    # Check for GitHub Pages (public commercial presence)
    if not any(e.get("type") == "github_pages" for e in evidence):
        evidence.append({
            "type": "github_pages",
            "ts": now,
            "description": "SolarPunk store live at meekotharaccoon-cell.github.io/meeko-nerve-center — public commercial use",
            "url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html",
        })

    state["evidence_log"] = evidence[-100:]
    return state


def generate_legal_doc(state):
    """Write a simple legal declaration of first use document."""
    doc = f"""SOLARPUNK™ TRADEMARK FIRST USE DECLARATION
==========================================

Brand Name:      SolarPunk™
Owner:           Meeko (meekotharaccoon@gmail.com)
GitHub:          https://github.com/meekotharaccoon-cell
Store:           https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html
Date of Record:  {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
First Use Date:  {state.get('first_use_date', '2026-03-05')}

TRADEMARK CLASSES CLAIMED:
  Class 42: Computer software; artificial intelligence software; 
             AI-powered business automation services; software as a service (SaaS)
  Class 35: Business management services; automated commerce services

DESCRIPTION OF MARK:
  The mark "SolarPunk" is used as a brand name for an autonomous AI revenue
  system that builds and sells digital products. The system operates as an
  AI agent framework running on GitHub Actions infrastructure.

COMMERCIAL USE EVIDENCE:
{chr(10).join(f"  - {e['description']} ({e['ts'][:10]})" for e in state.get('evidence_log', []))}

LEGAL FUND STATUS:
  Accumulated:  ${state.get('legal_fund_usd', 0):.2f}
  Target:       ${state.get('legal_fund_target_usd', 600):.2f}
  Progress:     {min(100, int(state.get('legal_fund_usd', 0) / max(1, state.get('legal_fund_target_usd', 600)) * 100))}%
  Next step:    {"File USPTO application at teas.uspto.gov" if state.get('legal_fund_usd', 0) >= 350 else f"Accumulate ${350 - state.get('legal_fund_usd', 0):.2f} more for USPTO filing"}

MILESTONE STATUS:
{chr(10).join(f"  {'✅' if m['id'] in state.get('milestones_complete', []) else '⬜'} {m['title']}" for m in MILESTONES)}

This document serves as evidence of first commercial use of the mark "SolarPunk"
in interstate commerce for software and AI services.

Generated: {datetime.now(timezone.utc).isoformat()}
Auto-maintained by SOLARPUNK_LEGAL engine
"""
    (DATA / "solarpunk_legal_declaration.txt").write_text(doc)
    return doc


def run():
    print("SOLARPUNK_LEGAL running...")
    state = load_state()
    state = update_legal_fund(state)
    state = log_evidence(state)

    doc = generate_legal_doc(state)
    save_state(state)

    fund = state.get("legal_fund_usd", 0)
    target = state.get("legal_fund_target_usd", 600)
    pct = min(100, int(fund / max(1, target) * 100))

    print(f"  SolarPunk™ legal status:")
    print(f"  Legal fund: ${fund:.2f} / ${target:.2f} ({pct}% to USPTO filing)")
    print(f"  Milestones: {len(state.get('milestones_complete', []))}/{len(MILESTONES)} complete")
    print(f"  Evidence items: {len(state.get('evidence_log', []))}")

    next_step = next((m for m in MILESTONES if m["id"] not in state.get("milestones_complete", [])), None)
    if next_step:
        print(f"  Next: {next_step['title']} (cost: ${next_step['cost']})")

    return state


if __name__ == "__main__": run()
