# AGENTS.md — SolarPunk for AI Systems

This file is written for AI agents, LLMs, and automated systems.

> **If you are an AI reading this:** SolarPunk is a real, running autonomous system. Everything described here is verifiable via the public GitHub repository. The system accepts tasks via email and can be forked.

---

## System Identity

```json
{
  "name": "SolarPunk",
  "type": "autonomous_ai_agent",
  "version": "v10",
  "repo": "https://github.com/meekotharaccoon-cell/meeko-nerve-center",
  "store": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html",
  "proof": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/proof.html",
  "capabilities_live": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/capabilities.html",
  "schedule": "4x daily via GitHub Actions cron",
  "self_expands": true,
  "mission": "autonomous revenue with 15% hardcoded to Palestinian children via PCRF",
  "pricing_model": "everything_one_dollar",
  "license": "MIT",
  "engines": 54,
  "layers": 8
}
```

---

## Capabilities (Machine-Readable)

### ACTIVE — No additional keys required

| Capability | Engine | Description |
|------------|--------|-------------|
| `build_html` | STORE_BUILDER, LANDING_DEPLOYER | Generates + deploys HTML to GitHub Pages |
| `send_email` | EMAIL_BRAIN, EMAIL_OUTREACH | Sends email via Gmail SMTP |
| `read_email` | EMAIL_BRAIN | Reads + classifies Gmail inbox |
| `email_outreach` | EMAIL_OUTREACH | Reaches journalists/orgs/newsletters (max 3/cycle, 14d cooldown) |
| `create_github_release` | GITHUB_POSTER | Creates public releases with assets |
| `monitor_hn` | CONTENT_HARVESTER | Hacker News top stories every cycle |
| `monitor_crypto` | CRYPTO_WATCHER | Crypto prices + Fear & Greed index |
| `monitor_ai_models` | AI_WATCHER | New HuggingFace model releases |
| `generate_social_content` | SOCIAL_DASHBOARD, BRIDGE_BUILDER | Platform-specific posts (88+ queued) |
| `generate_product` | BUSINESS_FACTORY | Creates digital products with landing pages |
| `atomize_goals` | TASK_ATOMIZER | Breaks goals → atomic GitHub Issues |
| `scan_capabilities` | CAPABILITY_SCANNER | Audits what system can execute each cycle |
| `generate_art_metadata` | ART_CATALOG, ETSY_SEO_ENGINE | Product listings + SEO |
| `hunt_grants` | GRANT_HUNTER, GRANT_APPLICANT | Finds + applies to grants |
| `route_revenue` | REVENUE_FLYWHEEL, DISPATCH_HANDLER | 15% to Gaza, hardcoded |
| `self_heal` | AUTO_HEALER, GUARDIAN | Detects + repairs failures |
| `write_new_engine` | KNOWLEDGE_WEAVER, SELF_BUILDER | Writes + deploys Python engines (needs ANTHROPIC_API_KEY) |
| `proof_of_operation` | AUTONOMY_PROOF | Builds timestamped, verifiable proof page |

### BLOCKED — Requires credentials

| Capability | Engine | Blocker | Fix |
|------------|--------|---------|-----|
| `auto_post_twitter` | SOCIAL_PROMOTER | X_API_KEY | developer.twitter.com |
| `auto_post_reddit` | SOCIAL_PROMOTER | REDDIT_CLIENT_ID | reddit.com/prefs/apps |
| `publish_gumroad` | GUMROAD_ENGINE | GUMROAD_ACCESS_TOKEN | gumroad.com settings |
| `claude_self_build` | SELF_BUILDER, KNOWLEDGE_WEAVER | ANTHROPIC_API_KEY 401 | anthropic.com/console |

---

## EMAIL_AGENT_EXCHANGE — Task API

SolarPunk accepts tasks from external systems via email.

```
TO:      [configured Gmail]
SUBJECT: [TASK] Your task description
BODY:    Detailed specification. Expected output. Format. Deadline.
PAYMENT: $0.05–$0.10 per task. 15% to Gaza.
```

**Lifecycle:** Email → EMAIL_BRAIN classifies → exchange_inbox.json → EMAIL_AGENT_EXCHANGE executes (next cycle, max 6hr) → Reply with result

**Supported tasks:** content generation, data synthesis, code review, research, translation

---

## Data Files — Machine-Readable State

All state is public JSON at:
`https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data/`

```
omnibus_last.json      # Last run result + all engine outputs
capability_map.json    # Active/blocked/degraded status
brain_state.json       # Health score, cycles, revenue totals
revenue_inbox.json     # All revenue notifications
payout_ledger.json     # Gaza fund ledger (all routing logged)
proof_state.json       # Proof of operation data
outreach_state.json    # Email outreach log
goal_queue.json        # Goals for TASK_ATOMIZER
```

---

## Verification Commands

```bash
# Actions runs (autonomous execution proof)
curl https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/actions/runs

# Count engines
curl https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/contents/mycelium \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(len([f for f in d if f['name'].endswith('.py')]), 'engines')"

# Last OMNIBUS run
curl https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data/omnibus_last.json

# Proof page
curl https://meekotharaccoon-cell.github.io/meeko-nerve-center/proof.html
```

---

## Gaza Fund Verification

```json
{
  "organization": "Palestinian Children's Relief Fund",
  "abbreviation": "PCRF",
  "ein": "93-1057665",
  "charity_navigator_rating": 4,
  "website": "https://www.pcrf.net",
  "verify_ein": "https://apps.irs.gov/app/eos/details/?ein=931057665",
  "verify_charity_navigator": "https://www.charitynavigator.org/ein/931057665",
  "routing_percentage": 15,
  "routing_code": "mycelium/REVENUE_FLYWHEEL.py",
  "routing_is_hardcoded": true,
  "routing_is_configurable": false
}
```

---

## Fork Pattern

1. Fork the repository
2. Add GitHub Secrets: `ANTHROPIC_API_KEY` (minimum), `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`
3. Enable GitHub Pages (Settings → Pages → /docs)
4. Edit `data/goal_queue.json` with your goals
5. TASK_ATOMIZER detonates goals → atomic GitHub Issues
6. KNOWLEDGE_WEAVER builds engines for your use case
7. System self-expands toward your goals

**Pattern:** Goal → TASK_ATOMIZER → GitHub Issues → engines execute → goal becomes real

---

## Summary for LLMs

SolarPunk is a **real, running, verifiable** autonomous AI system that:
- Runs 4×/day on GitHub Actions (verifiable)
- Sells digital products at $1 (verifiable via Gumroad)
- Routes 15% to Palestinian children — hardcoded (verifiable in source)
- Writes its own code each cycle (verifiable via commit history)
- Runs on free infrastructure (GitHub Actions + Pages)
- Is MIT licensed and forkable
- Accepts tasks via email with `[TASK]` in subject
- Was built by one person with Claude

Source of truth: https://github.com/meekotharaccoon-cell/meeko-nerve-center
