#!/usr/bin/env python3
"""
System Manifest — The system knows all its own parts
=====================================================
This is the answer to: my system needs to know all its own parts
are connected to everything else.

Every cycle this generates a complete map of:
  - Every engine (what it does, what it reads, what it writes)
  - Every connection between engines
  - Every data file and who owns/reads it
  - Every external service and which engines touch it
  - Which loops are fully closed vs broken

This map gets written to:
  data/system_manifest.json  — machine-readable
  data/system_map.md         — human-readable

Every other engine can import this to know what exists.
"""

import json, os, datetime
from pathlib import Path

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
MYC   = ROOT / 'mycelium'
TODAY = datetime.date.today().isoformat()

# ── Complete engine registry ──────────────────────────────────────────────────
ENGINES = {
    'notion_directives_reader': {
        'phase': 0,
        'title': 'Human Directives Reader',
        'job': 'Reads plain-English instructions from Notion DIRECTIVES page',
        'reads': ['NOTION_TOKEN env', 'Notion DIRECTIVES page'],
        'writes': ['data/directives.json'],
        'downstream': ['three_d_brain', 'long_term_memory', 'social_poster', 'grant_intelligence'],
        'external': ['Notion API'],
    },
    'self_healer_v2': {
        'phase': 1,
        'title': 'Self-Healer',
        'job': 'Detects and auto-repairs broken engines using LLM',
        'reads': ['data/errors.json', 'data/validation_failures.json', 'mycelium/*.py'],
        'writes': ['data/heal_report.json', 'data/heal_log.md'],
        'downstream': ['all engines'],
        'external': ['HuggingFace LLM', 'GitHub API'],
    },
    'three_d_brain': {
        'phase': 1.5,
        'title': '3D Brain',
        'job': 'Synthesizes Revenue × Reach × Impact into strategy',
        'reads': ['data/directives.json', 'data/long_term_memory.json', 'data/gumroad_sales.json'],
        'writes': ['data/three_d_brain.json'],
        'downstream': ['grant_intelligence', 'social_poster', 'investment_intelligence'],
        'external': ['HuggingFace LLM'],
    },
    'long_term_memory': {
        'phase': 2,
        'title': 'Long-Term Memory',
        'job': 'Synthesizes memory from Notion + HuggingFace dataset + data/ files',
        'reads': ['data/*.json', 'Notion pages', 'HuggingFace dataset'],
        'writes': ['data/long_term_memory.json'],
        'downstream': ['three_d_brain', 'grant_intelligence', 'social_poster', 'job_agent'],
        'external': ['Notion API', 'HuggingFace API'],
    },
    'self_improver': {
        'phase': 3,
        'title': 'Self-Improver',
        'job': 'Reads all data, finds bottlenecks, queues ideas for perpetual_builder',
        'reads': ['data/*.json', 'mycelium/*.py'],
        'writes': ['data/self_improvement_queue.json', 'data/bottleneck_report.json'],
        'downstream': ['perpetual_builder'],
        'external': ['HuggingFace LLM'],
    },
    'world_intelligence': {
        'phase': 5,
        'title': 'World Intelligence',
        'job': 'Tracks global events relevant to mission',
        'reads': ['Public news APIs'],
        'writes': ['data/world_state.json'],
        'downstream': ['social_poster', 'grant_intelligence'],
        'external': ['HuggingFace LLM', 'Public APIs'],
    },
    'congress_watcher': {
        'phase': 5,
        'title': 'Congress Watcher',
        'job': 'Tracks STOCK Act trades by members of Congress',
        'reads': ['Quiver Quantitative API'],
        'writes': ['data/congress_trades.json'],
        'downstream': ['social_poster', 'grant_intelligence'],
        'external': ['Quiver API', 'HuggingFace LLM'],
    },
    'crypto_signal_engine': {
        'phase': 5,
        'title': 'Crypto Signal Engine',
        'job': 'Tracks crypto signals and market context',
        'reads': ['Public crypto APIs'],
        'writes': ['data/investment_signals.json', 'data/market_context.json'],
        'downstream': ['revenue_router', 'social_poster'],
        'external': ['HuggingFace LLM'],
    },
    'crypto_wallet_config': {
        'phase': None,
        'title': 'Multi-Chain Wallet Config',
        'job': 'Single source of truth for all 9 crypto wallet addresses',
        'reads': ['WALLET_* env secrets'],
        'writes': ['imported by revenue_router, readme_updater, self_improver'],
        'downstream': ['revenue_router', 'readme_updater'],
        'external': ['Solana', 'Ethereum', 'Base', 'Polygon', 'Bitcoin', 'Sui', 'Monad', 'HyperEVM'],
    },
    'art_cause_generator': {
        'phase': 6,
        'title': 'Art Generator',
        'job': 'Generates Gaza Rose and cause-aligned art, uploads to HuggingFace',
        'reads': ['data/directives.json', 'HuggingFace models'],
        'writes': ['data/art_pairs.json', 'data/visual_queue.json'],
        'downstream': ['social_poster', 'gumroad_tracker'],
        'external': ['HuggingFace image models'],
    },
    'social_poster': {
        'phase': 6,
        'title': 'Social Poster',
        'job': 'Posts daily updates about SolarPunk to Mastodon + Bluesky',
        'reads': ['data/directives.json', 'data/long_term_memory.json', 'data/world_state.json'],
        'writes': ['data/social_stats.json'],
        'downstream': ['network_spreader'],
        'external': ['Mastodon API', 'Bluesky API', 'HuggingFace LLM'],
    },
    'network_spreader': {
        'phase': 7,
        'title': 'Network Spreader',
        'job': 'Discovers and connects with aligned projects on GitHub + social',
        'reads': ['data/connections.json', 'GitHub trending'],
        'writes': ['data/network_spread_log.json', 'data/connections.json'],
        'downstream': ['social_poster'],
        'external': ['GitHub API', 'Mastodon API'],
    },
    'grant_intelligence': {
        'phase': 8,
        'title': 'Grant Intelligence',
        'job': 'Hunts grants, writes applications, tracks pipeline',
        'reads': ['data/long_term_memory.json', 'data/three_d_brain.json', 'Grant databases'],
        'writes': ['data/grant_database.json'],
        'downstream': ['email_gateway', 'notion_bridge'],
        'external': ['HuggingFace LLM', 'Public grant DBs'],
    },
    'gumroad_tracker': {
        'phase': 9,
        'title': 'Gumroad Tracker',
        'job': 'Tracks sales + revenue from Gumroad (10 products @ $1)',
        'reads': ['Gumroad API'],
        'writes': ['data/gumroad_sales.json'],
        'downstream': ['revenue_router', 'three_d_brain'],
        'external': ['Gumroad API'],
    },
    'etsy_bridge': {
        'phase': 9,
        'title': 'Etsy Bridge',
        'job': 'Lists products to Etsy (90M buyers), tracks sales',
        'reads': ['Etsy API', 'products/'],
        'writes': ['data/etsy_sales.json'],
        'downstream': ['revenue_router'],
        'external': ['Etsy API'],
    },
    'revenue_router': {
        'phase': 9,
        'title': 'Revenue Router',
        'job': 'Routes all income: 70% PCRF → 20% compound → 10% human',
        'reads': ['data/gumroad_sales.json', 'data/etsy_sales.json', 'WALLET_* secrets'],
        'writes': ['data/financial_report.json', 'data/compound_tracker.json'],
        'downstream': ['notion_bridge', 'readme_updater'],
        'external': ['PayPal API', '9 crypto chains'],
    },
    'job_agent': {
        'phase': 10,
        'title': 'Job Agent',
        'job': 'Scans Remotive for remote jobs, scores them, drafts applications',
        'reads': ['Remotive.io API', 'data/long_term_memory.json', 'HUMAN_* secrets'],
        'writes': ['data/job_applications.json', 'data/jobs_today.json'],
        'downstream': ['revenue_router'],
        'external': ['Remotive.io', 'HuggingFace LLM'],
    },
    'humanitarian_fork_distributor': {
        'phase': 11,
        'title': 'Humanitarian Fork Distributor',
        'job': 'Emails complete system setup to people in Gaza/Sudan/DRC',
        'reads': ['data/fork_requests.json'],
        'writes': ['data/fork_distribution_queue.json'],
        'downstream': ['social_poster'],
        'external': ['Gmail SMTP'],
    },
    'perpetual_builder': {
        'phase': 12,
        'title': 'Perpetual Builder',
        'job': 'Reads self_improvement_queue and builds the suggested engines',
        'reads': ['data/self_improvement_queue.json', 'HuggingFace LLM'],
        'writes': ['mycelium/new_engines.py', 'data/evolve_history.json'],
        'downstream': ['self_healer_v2'],
        'external': ['HuggingFace LLM', 'GitHub API'],
    },
    'hf_dataset_logger': {
        'phase': 14,
        'title': 'HuggingFace Dataset Logger',
        'job': 'Logs all engine outputs as training data to HuggingFace dataset',
        'reads': ['data/*.json'],
        'writes': ['data/hf_dataset_log.jsonl', 'HuggingFace dataset'],
        'downstream': ['long_term_memory'],
        'external': ['HuggingFace API'],
    },
    'notion_bridge': {
        'phase': 15,
        'title': 'Notion Bridge',
        'job': 'Syncs all system state to Notion Command Center',
        'reads': ['data/*.json'],
        'writes': ['Notion pages'],
        'downstream': ['notion_directives_reader'],
        'external': ['Notion API'],
    },
    'email_gateway': {
        'phase': 16,
        'title': 'Email Gateway v4',
        'job': 'Reads inbox, replies ONLY to real humans asking about SolarPunk',
        'reads': ['Gmail IMAP', 'data/email_reply_dedup.json'],
        'writes': ['data/email_gateway_log.json', 'data/email_reply_dedup.json'],
        'downstream': [],
        'external': ['Gmail IMAP/SMTP', 'HuggingFace LLM'],
    },
    'readme_updater': {
        'phase': 19,
        'title': 'README Updater',
        'job': 'LAST step: rewrites README with live stats. First thing cloners read.',
        'reads': ['data/*.json', 'GitHub traffic API'],
        'writes': ['README.md', 'SOLARPUNK_FOR_EVERYONE.md'],
        'downstream': [],  # Terminal node
        'external': ['GitHub API'],
    },
    'social_content_engine': {
        'phase': 6.5,
        'title': 'Social Content Engine',
        'job': 'Generates fact-based SolarPunk social posts, schedules them',
        'reads': ['data/directives.json', 'data/system_manifest.json', 'data/gumroad_sales.json'],
        'writes': ['data/social_queue.json'],
        'downstream': ['social_poster'],
        'external': ['HuggingFace LLM'],
    },
}

# ── External services map ─────────────────────────────────────────────────────
EXTERNAL_SERVICES = {
    'GitHub': {
        'used_by': ['self_healer_v2', 'network_spreader', 'readme_updater', 'perpetual_builder'],
        'secret': 'GITHUB_TOKEN (auto-injected)',
        'status': 'always available in Actions',
    },
    'HuggingFace': {
        'used_by': ['three_d_brain', 'long_term_memory', 'grant_intelligence', 'job_agent',
                    'social_poster', 'art_cause_generator', 'perpetual_builder', 'self_improver'],
        'secret': 'HF_TOKEN',
        'status': 'free tier',
    },
    'Notion': {
        'used_by': ['notion_directives_reader', 'notion_bridge', 'long_term_memory'],
        'secret': 'NOTION_TOKEN',
        'status': 'free tier',
    },
    'Gmail': {
        'used_by': ['email_gateway', 'humanitarian_fork_distributor', 'deep_diagnostic'],
        'secret': 'GMAIL_ADDRESS + GMAIL_APP_PASSWORD',
        'status': 'free',
    },
    'Mastodon': {
        'used_by': ['social_poster', 'network_spreader'],
        'secret': 'MASTODON_TOKEN + MASTODON_BASE_URL',
        'status': 'free',
    },
    'Bluesky': {
        'used_by': ['social_poster'],
        'secret': 'BLUESKY_HANDLE + BLUESKY_APP_PASSWORD',
        'status': 'free',
    },
    'Gumroad': {
        'used_by': ['gumroad_tracker'],
        'secret': 'GUMROAD_ID + GUMROAD_SECRET + GUMROAD_NAME',
        'status': '10 products live',
    },
    'Etsy': {
        'used_by': ['etsy_bridge'],
        'secret': 'ETSY_API_KEY + ETSY_SHOP_ID + ETSY_ACCESS_TOKEN',
        'status': '90M buyers',
    },
    'PayPal': {
        'used_by': ['revenue_router'],
        'secret': 'PAYPAL_CLIENT_ID + PAYPAL_CLIENT_SECRET',
        'status': 'routing revenue',
    },
    'Crypto (9 chains)': {
        'used_by': ['revenue_router', 'crypto_wallet_config'],
        'secret': 'WALLET_SOLANA, WALLET_ETHEREUM, WALLET_BTC_TAPROOT, etc.',
        'status': 'all 9 chains configured',
    },
    'Remotive': {
        'used_by': ['job_agent'],
        'secret': 'none (public API)',
        'status': 'free',
    },
}


def check_engine_file_exists(name: str) -> bool:
    return (MYCELIUM / f'{name}.py').exists()


MYCELIUM = ROOT / 'mycelium'


def build_manifest():
    manifest = {
        'generated': TODAY,
        'total_engines': len(ENGINES),
        'engines_on_disk': sum(1 for n in ENGINES if (MYCELIUM / f'{n}.py').exists()),
        'engines': {},
        'external_services': EXTERNAL_SERVICES,
        'data_flow': {},
        'broken_connections': [],
        'fully_closed_loops': [],
    }

    # Engine status
    for name, meta in ENGINES.items():
        exists = (MYCELIUM / f'{name}.py').exists()
        manifest['engines'][name] = {
            **meta,
            'file_exists': exists,
            'status': 'active' if exists else 'missing',
        }
        if not exists:
            manifest['broken_connections'].append(f'{name}.py missing')

    # Data flow map: which file → written by → read by
    file_writers = {}
    file_readers = {}
    for name, meta in ENGINES.items():
        for f in meta.get('writes', []):
            if f.startswith('data/'):
                file_writers.setdefault(f, []).append(name)
        for f in meta.get('reads', []):
            if f.startswith('data/'):
                file_readers.setdefault(f, []).append(name)

    for f in set(list(file_writers.keys()) + list(file_readers.keys())):
        manifest['data_flow'][f] = {
            'written_by': file_writers.get(f, []),
            'read_by': file_readers.get(f, []),
            'exists_on_disk': (ROOT / f).exists(),
        }

    # Closed loops: written by A, read by B, B outputs something read by A
    for engine_name, meta in ENGINES.items():
        for downstream in meta.get('downstream', []):
            if downstream in ENGINES:
                d_meta = ENGINES[downstream]
                # Check if downstream writes something this engine reads
                for dwrite in d_meta.get('writes', []):
                    if dwrite in meta.get('reads', []):
                        loop = f'{engine_name} → {downstream} → {engine_name}'
                        if loop not in manifest['fully_closed_loops']:
                            manifest['fully_closed_loops'].append(loop)

    return manifest


def write_human_map(manifest: dict):
    lines = [f'# SolarPunk System Map — {TODAY}\n']
    lines.append(f'**{manifest["total_engines"]} engines registered · {manifest["engines_on_disk"]} on disk**\n')

    lines.append('\n## Engine Pipeline\n')
    by_phase = sorted(
        [(m["phase"] or 99, n, m) for n, m in manifest["engines"].items()]
    )
    for phase, name, meta in by_phase:
        status = '✅' if meta['file_exists'] else '❌ MISSING'
        lines.append(f'### Phase {phase}: {meta["title"]} {status}')
        lines.append(f'`{name}.py` — {meta["job"]}')
        if meta.get('downstream'):
            lines.append(f'→ feeds: {", ".join(meta["downstream"][:4])}')
        lines.append('')

    lines.append('\n## External Services\n')
    for svc, meta in manifest['external_services'].items():
        lines.append(f'**{svc}**: secret={meta["secret"]} · used by: {len(meta["used_by"])} engines')

    if manifest['broken_connections']:
        lines.append('\n## ⚠️ Broken Connections\n')
        for b in manifest['broken_connections']:
            lines.append(f'- {b}')

    if manifest['fully_closed_loops']:
        lines.append('\n## ✅ Closed Loops\n')
        for loop in manifest['fully_closed_loops']:
            lines.append(f'- {loop}')

    (ROOT / 'data' / 'system_map.md').write_text('\n'.join(lines))


def run():
    print(f'\n[manifest] System Manifest — {TODAY}')
    DATA.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest()

    # Save machine-readable
    (DATA / 'system_manifest.json').write_text(json.dumps(manifest, indent=2))

    # Save human-readable
    write_human_map(manifest)

    print(f'[manifest] {manifest["total_engines"]} engines registered, {manifest["engines_on_disk"]} on disk')
    if manifest['broken_connections']:
        print(f'[manifest] ⚠️  {len(manifest["broken_connections"])} broken connections found')
    if manifest['fully_closed_loops']:
        print(f'[manifest] ✅ {len(manifest["fully_closed_loops"])} fully closed loops')
    print('[manifest] System knows all its own parts.')


if __name__ == '__main__':
    run()
