# SolarPunk System Map — 2026-03-02

**24 engines registered · 23 on disk**


## Engine Pipeline

### Phase 1: Self-Healer ✅
`self_healer_v2.py` — Detects and auto-repairs broken engines using LLM
→ feeds: all engines

### Phase 1.5: 3D Brain ✅
`three_d_brain.py` — Synthesizes Revenue × Reach × Impact into strategy
→ feeds: grant_intelligence, social_poster, investment_intelligence

### Phase 2: Long-Term Memory ✅
`long_term_memory.py` — Synthesizes memory from Notion + HuggingFace dataset + data/ files
→ feeds: three_d_brain, grant_intelligence, social_poster, job_agent

### Phase 3: Self-Improver ✅
`self_improver.py` — Reads all data, finds bottlenecks, queues ideas for perpetual_builder
→ feeds: perpetual_builder

### Phase 5: Congress Watcher ✅
`congress_watcher.py` — Tracks STOCK Act trades by members of Congress
→ feeds: social_poster, grant_intelligence

### Phase 5: Crypto Signal Engine ❌ MISSING
`crypto_signal_engine.py` — Tracks crypto signals and market context
→ feeds: revenue_router, social_poster

### Phase 5: World Intelligence ✅
`world_intelligence.py` — Tracks global events relevant to mission
→ feeds: social_poster, grant_intelligence

### Phase 6: Art Generator ✅
`art_cause_generator.py` — Generates Gaza Rose and cause-aligned art, uploads to HuggingFace
→ feeds: social_poster, gumroad_tracker

### Phase 6: Social Poster ✅
`social_poster.py` — Posts daily updates about SolarPunk to Mastodon + Bluesky
→ feeds: network_spreader

### Phase 6.5: Social Content Engine ✅
`social_content_engine.py` — Generates fact-based SolarPunk social posts, schedules them
→ feeds: social_poster

### Phase 7: Network Spreader ✅
`network_spreader.py` — Discovers and connects with aligned projects on GitHub + social
→ feeds: social_poster

### Phase 8: Grant Intelligence ✅
`grant_intelligence.py` — Hunts grants, writes applications, tracks pipeline
→ feeds: email_gateway, notion_bridge

### Phase 9: Etsy Bridge ✅
`etsy_bridge.py` — Lists products to Etsy (90M buyers), tracks sales
→ feeds: revenue_router

### Phase 9: Gumroad Tracker ✅
`gumroad_tracker.py` — Tracks sales + revenue from Gumroad (10 products @ $1)
→ feeds: revenue_router, three_d_brain

### Phase 9: Revenue Router ✅
`revenue_router.py` — Routes all income: 70% PCRF → 20% compound → 10% human
→ feeds: notion_bridge, readme_updater

### Phase 10: Job Agent ✅
`job_agent.py` — Scans Remotive for remote jobs, scores them, drafts applications
→ feeds: revenue_router

### Phase 11: Humanitarian Fork Distributor ✅
`humanitarian_fork_distributor.py` — Emails complete system setup to people in Gaza/Sudan/DRC
→ feeds: social_poster

### Phase 12: Perpetual Builder ✅
`perpetual_builder.py` — Reads self_improvement_queue and builds the suggested engines
→ feeds: self_healer_v2

### Phase 14: HuggingFace Dataset Logger ✅
`hf_dataset_logger.py` — Logs all engine outputs as training data to HuggingFace dataset
→ feeds: long_term_memory

### Phase 15: Notion Bridge ✅
`notion_bridge.py` — Syncs all system state to Notion Command Center
→ feeds: notion_directives_reader

### Phase 16: Email Gateway v4 ✅
`email_gateway.py` — Reads inbox, replies ONLY to real humans asking about SolarPunk

### Phase 19: README Updater ✅
`readme_updater.py` — LAST step: rewrites README with live stats. First thing cloners read.

### Phase 99: Multi-Chain Wallet Config ✅
`crypto_wallet_config.py` — Single source of truth for all 9 crypto wallet addresses
→ feeds: revenue_router, readme_updater

### Phase 99: Human Directives Reader ✅
`notion_directives_reader.py` — Reads plain-English instructions from Notion DIRECTIVES page
→ feeds: three_d_brain, long_term_memory, social_poster, grant_intelligence


## External Services

**GitHub**: secret=GITHUB_TOKEN (auto-injected) · used by: 4 engines
**HuggingFace**: secret=HF_TOKEN · used by: 8 engines
**Notion**: secret=NOTION_TOKEN · used by: 3 engines
**Gmail**: secret=GMAIL_ADDRESS + GMAIL_APP_PASSWORD · used by: 3 engines
**Mastodon**: secret=MASTODON_TOKEN + MASTODON_BASE_URL · used by: 2 engines
**Bluesky**: secret=BLUESKY_HANDLE + BLUESKY_APP_PASSWORD · used by: 1 engines
**Gumroad**: secret=GUMROAD_ID + GUMROAD_SECRET + GUMROAD_NAME · used by: 1 engines
**Etsy**: secret=ETSY_API_KEY + ETSY_SHOP_ID + ETSY_ACCESS_TOKEN · used by: 1 engines
**PayPal**: secret=PAYPAL_CLIENT_ID + PAYPAL_CLIENT_SECRET · used by: 1 engines
**Crypto (9 chains)**: secret=WALLET_SOLANA, WALLET_ETHEREUM, WALLET_BTC_TAPROOT, etc. · used by: 2 engines
**Remotive**: secret=none (public API) · used by: 1 engines

## ⚠️ Broken Connections

- crypto_signal_engine.py missing