#!/usr/bin/env python3
"""
THREE_D_BRAIN.py — The SolarPunk 3-Dimensional Intelligence Engine
===================================================================
v2: Now reads human DIRECTIVES from Notion before synthesizing.
Your words literally shape what the brain decides to do each cycle.

  DIMENSION 1 — REVENUE AXIS
  DIMENSION 2 — REACH AXIS  
  DIMENSION 3 — IMPACT AXIS

Phase 0 (notion_directives_reader) runs first.
This engine reads data/directives.json and injects human intent
into the cross-dimensional synthesis before any decisions are made.

Result: system that acts on YOUR priorities, not just its own patterns.
"""

import json, os, datetime, sys
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M')

MASTODON_TOKEN    = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')
NOTION_TOKEN      = os.environ.get('NOTION_TOKEN', '')
GUMROAD_SECRET    = os.environ.get('GUMROAD_SECRET', '')
HF_TOKEN          = os.environ.get('HF_TOKEN', '')


def load_json(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except Exception as e:
        print(f'  [3d-brain] load error {path}: {e}')
    return default if default is not None else {}


def http_post(url, data=None, headers=None, json_data=None):
    try:
        if json_data:
            body = json.dumps(json_data).encode()
            headers = {**(headers or {}), 'Content-Type': 'application/json'}
        elif data:
            body = urlencode(data).encode()
            headers = {**(headers or {}), 'Content-Type': 'application/x-www-form-urlencoded'}
        else:
            body = b''
        req = urllib_request.Request(url, data=body, headers=headers or {}, method='POST')
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {'error': str(e)}


def http_get(url, headers=None):
    try:
        req = urllib_request.Request(url, headers=headers or {})
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {'error': str(e)}


# ── PHASE 0 OUTPUT: Read human directives ────────────────────────────────────
def load_directives():
    """
    Read today's directives from data/directives.json.
    Written by notion_directives_reader.py (Phase 0).
    This is how YOUR intent shapes the synthesis.
    """
    d = load_json(DATA / 'directives.json')
    if d and d.get('date') == TODAY:
        msg = d.get('human_message', '')
        priority = d.get('priority', [])
        pause = d.get('pause', [])
        amplify = d.get('amplify', [])
        build_next = d.get('build_next')
        if msg or priority:
            print(f'  [3d-brain] 🎯 Human directive active: {msg or priority}')
        return d
    return {'pause': [], 'priority': [], 'amplify': [], 'build_next': None,
            'suppress': [], 'human_message': '', 'raw': ''}


# ── DIMENSION 1: REVENUE ──────────────────────────────────────────────────────
def scan_revenue():
    print('\n[3d-brain] 💰 DIMENSION 1: REVENUE SCAN')
    revenue = {
        'gumroad_total': 0.0,
        'gumroad_products': 0,
        'gumroad_sales': 0,
        'kofi_total': 0.0,
        'grants_total': 0.0,
        'pcrf_routed': 0.0,
        'retained': 0.0,
        'sources': [],
        'last_sale': None,
    }
    gumroad = load_json(DATA / 'gumroad_sales.json')
    if gumroad.get('status') == 'ok':
        revenue['gumroad_total']    = gumroad.get('total_revenue_usd', 0)
        revenue['gumroad_products'] = gumroad.get('products_count', 0)
        revenue['gumroad_sales']    = gumroad.get('sales_count', 0)
        revenue['pcrf_routed']     += gumroad.get('pcrf_split_usd', 0)
        revenue['retained']        += gumroad.get('retained_usd', 0)
        revenue['sources'].append('gumroad')
        if gumroad.get('new_sales'): revenue['last_sale'] = TODAY
    kofi = load_json(DATA / 'kofi_data.json')
    if kofi:
        revenue['kofi_total'] = kofi.get('total', 0)
        revenue['sources'].append('kofi')
    grants = load_json(DATA / 'grant_intelligence.json')
    if grants:
        revenue['grants_total'] = grants.get('estimated_value', 0)
        revenue['sources'].append('grants')
    total = revenue['gumroad_total'] + revenue['kofi_total']
    revenue['grand_total'] = round(total, 2)
    revenue['pcrf_routed'] = round(revenue['pcrf_routed'], 2)
    print(f'  Total revenue: ${revenue["grand_total"]:.2f}')
    print(f'  PCRF routed: ${revenue["pcrf_routed"]:.2f}')
    return revenue


# ── DIMENSION 2: REACH ────────────────────────────────────────────────────────
def scan_reach():
    print('\n[3d-brain] 📡 DIMENSION 2: REACH SCAN')
    reach = {
        'mastodon_followers': 0,
        'github_forks': 0,
        'github_stars': 0,
        'email_list': 0,
        'platforms_active': [],
        'viral_potential': 'low',
    }
    gh_stats = load_json(DATA / 'fork_stats.json')
    if gh_stats:
        reach['github_forks'] = gh_stats.get('total_forks', 0)
        reach['github_stars'] = gh_stats.get('total_stars', 0)
        reach['platforms_active'].append('github')
    social = load_json(DATA / 'social_stats.json')
    if social:
        reach['mastodon_followers'] = social.get('mastodon_followers', 0)
        if social.get('mastodon_active'):  reach['platforms_active'].append('mastodon')
        if social.get('bluesky_active'):   reach['platforms_active'].append('bluesky')
    audience = load_json(DATA / 'audience_data.json')
    if audience:
        reach['email_list'] = audience.get('email_count', 0)
        reach['platforms_active'].append('email')
    forks = reach['github_forks']
    reach['viral_potential'] = ('high' if forks > 20 else 'medium' if forks > 5 else 'building')
    print(f'  GitHub forks: {reach["github_forks"]}')
    print(f'  Platforms: {reach["platforms_active"]}')
    return reach


# ── DIMENSION 3: IMPACT ───────────────────────────────────────────────────────
def scan_impact():
    print('\n[3d-brain] 🌍 DIMENSION 3: IMPACT SCAN')
    impact = {
        'pcrf_total_routed': 0.0,
        'grants_hunting': False,
        'content_humanitarian': False,
        'fork_network_size': 0,
        'cause_commerce_active': False,
        'impact_score': 0,
    }
    gumroad = load_json(DATA / 'gumroad_sales.json')
    if gumroad.get('pcrf_split_usd', 0) > 0:
        impact['pcrf_total_routed']  = gumroad['pcrf_split_usd']
        impact['cause_commerce_active'] = True
        impact['impact_score'] += 30
    if load_json(DATA / 'humanitarian_content.json'):
        impact['content_humanitarian'] = True
        impact['impact_score'] += 20
    grants = load_json(DATA / 'grant_intelligence.json')
    if grants and grants.get('opportunities'):
        impact['grants_hunting'] = True
        impact['impact_score'] += 25
    gh_stats = load_json(DATA / 'fork_stats.json')
    impact['fork_network_size'] = gh_stats.get('total_forks', 0) if gh_stats else 0
    impact['impact_score'] += min(impact['fork_network_size'] * 5, 25)
    print(f'  PCRF routed: ${impact["pcrf_total_routed"]:.2f}')
    print(f'  Impact score: {impact["impact_score"]}/100')
    return impact


# ── CROSS-DIMENSIONAL SYNTHESIS ───────────────────────────────────────────────
def synthesize(revenue, reach, impact, directives):
    """
    The actual 3D thinking. Now informed by HUMAN DIRECTIVES.
    
    Directives can:
    - Override default priorities (if human says "focus on grants", grant actions rise to top)
    - Suppress certain decisions (if human says "pause email", email actions are removed)
    - Add explicit build targets ("build product 11" becomes a top decision)
    - Shift tone of synthesis (urgent vs calm vs experimental)
    """
    print('\n[3d-brain] 🧠 CROSS-DIMENSIONAL SYNTHESIS')

    human_priority  = directives.get('priority', [])
    human_suppress  = directives.get('suppress', []) + directives.get('pause', [])
    human_amplify   = directives.get('amplify', [])
    human_build     = directives.get('build_next')
    human_message   = directives.get('human_message', '')
    human_raw       = directives.get('raw', '')

    if human_message:
        print(f'  📣 Human directive shaping synthesis: "{human_message}"')

    decisions    = []
    insights     = []
    next_actions = []

    # ── HUMAN OVERRIDES: explicit build target ────────────────────────────
    if human_build:
        insights.append(f'🏗️  Human directive: build "{human_build}"')
        decisions.insert(0, f'BUILD NOW: {human_build} — human priority')
        next_actions.insert(0, f'trigger: perpetual_builder.py with target="{human_build}"')

    # ── HUMAN OVERRIDES: explicit priorities override system logic ─────────
    priority_map = {
        'grants':   ('PRIORITY (human): Run grant_auto_submitter.py — human directive', 'trigger: grant_intelligence.py + grant_auto_submitter.py'),
        'gumroad':  ('PRIORITY (human): Push Gumroad products — drive revenue', 'trigger: cross_poster.py with product links'),
        'viral':    ('PRIORITY (human): Amplify viral fork angle', 'trigger: social_poster.py fork-focused content'),
        'content':  ('PRIORITY (human): Focus on content generation', 'trigger: humanitarian_content.py + cross_poster.py'),
        'social':   ('PRIORITY (human): Max social posting today', 'trigger: social_poster.py all platforms'),
        'email':    ('PRIORITY (human): Email outreach cycle', 'trigger: email_gateway.py outreach mode'),
        'products': ('PRIORITY (human): Ship product this cycle', 'trigger: generate-pdfs.yml workflow_dispatch'),
    }
    for p in human_priority:
        if p.lower() in priority_map:
            d, a = priority_map[p.lower()]
            if not any(d in x for x in decisions):
                decisions.insert(0, d)
                next_actions.insert(0, a)

    # ── HUMAN OVERRIDES: amplify signals ──────────────────────────────────
    amplify_map = {
        'fork':     ('AMPLIFY: fork onboarding + community outreach', 'trigger: fork_onboarding.py --all'),
        'grants':   ('AMPLIFY: submit more grant applications', 'trigger: grant_intelligence.py --max'),
        'mastodon': ('AMPLIFY: 2x Mastodon post frequency', 'trigger: cross_poster.py --platform mastodon --double'),
        'art':      ('AMPLIFY: Gaza Rose art generation', 'trigger: art_cause_generator.py --batch'),
    }
    for a in human_amplify:
        if a.lower() in amplify_map:
            d, act = amplify_map[a.lower()]
            decisions.append(d)
            next_actions.append(act)

    # ── SYSTEM PATTERN MATCHING (below human overrides) ────────────────────
    if revenue['gumroad_products'] > 0 and revenue['gumroad_sales'] == 0:
        insights.append('📦 Products live but no sales — funnel needs traffic')
        decision = 'DRIVE TRAFFIC: Gumroad products via Mastodon + social'
        if not any('grants' in h.lower() for h in human_priority):  # don't override human grant focus
            decisions.append(decision)
            next_actions.append('trigger: cross_poster.py with product promotion content')

    if revenue['gumroad_products'] == 0 and reach['github_forks'] > 0:
        insights.append('🔥 Forks exist but no products — monetization gap')
        decisions.append('SHIP PRODUCTS: Run generate-pdfs workflow')
        next_actions.append('trigger: generate-pdfs.yml workflow_dispatch')

    if not reach['platforms_active'] or len(reach['platforms_active']) < 2:
        insights.append('📡 Signal confined to 1 platform')
        if 'social' not in human_suppress and 'mastodon' not in human_suppress:
            decisions.append('EXPAND: Cross-post to all platforms')
            next_actions.append('trigger: social_poster.py')

    if revenue['grand_total'] > 0 and impact['impact_score'] < 30:
        insights.append('💰 Revenue flowing but impact low — check PCRF routing')
        decisions.append('VERIFY: 70% PCRF split routing')
        next_actions.append('check: donation_engine.py PCRF routing')

    if (revenue['gumroad_products'] > 0
            and len(reach['platforms_active']) >= 2
            and impact['cause_commerce_active']):
        insights.append('🌸 All three dimensions active — system compounding')
        decisions.append('SUSTAIN: All cycles running — focus on content quality')
        next_actions.append('trigger: idea_engine.py for next product')

    grants_data = load_json(DATA / 'grant_intelligence.json')
    if grants_data and grants_data.get('top_opportunity'):
        insights.append(f'🏆 Grant opportunity: {grants_data["top_opportunity"]}')
        decisions.append('APPLY: grant_auto_submitter.py for top opportunity')
        next_actions.append('trigger: grant_intelligence.py weekly scan')

    # ── FILTER OUT SUPPRESSED ACTIONS ────────────────────────────────────
    if human_suppress:
        decisions    = [d for d in decisions    if not any(s.lower() in d.lower() for s in human_suppress)]
        next_actions = [a for a in next_actions if not any(s.lower() in a.lower() for s in human_suppress)]
        print(f'  🔇 Suppressed: {human_suppress}')

    print(f'  Insights: {len(insights)} | Decisions: {len(decisions)}')
    for d in decisions[:3]:
        print(f'    → {d}')

    return {
        'insights': insights,
        'decisions': decisions,
        'next_actions': next_actions,
        'human_directive_active': bool(human_message or human_priority),
        'human_message': human_message,
        'synthesis_quality': 'directive-informed' if human_message else ('operational' if decisions else 'baseline'),
    }


# ── NOTION UPDATE ─────────────────────────────────────────────────────────────
def update_notion(brain_state):
    if not NOTION_TOKEN:
        return
    print('\n[3d-brain] 📝 Updating Notion')
    headers = {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28',
    }
    rev       = brain_state.get('revenue', {})
    reach     = brain_state.get('reach', {})
    impact    = brain_state.get('impact', {})
    synthesis = brain_state.get('synthesis', {})
    directive = brain_state.get('directives', {})

    summary_line = (
        f'[{NOW}] '
        f'Rev: ${rev.get("grand_total", 0):.2f} | '
        f'PCRF: ${rev.get("pcrf_routed", 0):.2f} | '
        f'Impact: {impact.get("impact_score", 0)}/100 | '
        f'Forks: {reach.get("github_forks", 0)}'
    )
    if synthesis.get('human_directive_active'):
        summary_line += f' | 🎯 Directive: {synthesis.get("human_message", "")[:60]}'

    search = http_post(
        'https://api.notion.com/v1/search',
        headers=headers,
        json_data={'query': '3D Brain State Log', 'filter': {'value': 'page', 'property': 'object'}}
    )
    pages = search.get('results', []) if not search.get('error') else []
    if pages:
        http_post(
            f'https://api.notion.com/v1/blocks/{pages[0]["id"]}/children',
            headers=headers,
            json_data={'children': [{
                'object': 'block', 'type': 'paragraph',
                'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': summary_line}}]}
            }]}
        )
        print(f'  [notion] ✅ Updated 3D Brain State Log')
    else:
        print('  [notion] Page not found — creating stub')
        http_post('https://api.notion.com/v1/pages', headers=headers, json_data={
            'parent': {'type': 'workspace', 'workspace': True},
            'properties': {'title': [{'type': 'text', 'text': {'content': '🧠 3D Brain State Log'}}]},
            'children': [{'object': 'block', 'type': 'paragraph',
                          'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': summary_line}}]}}]
        })


# ── MASTODON PULSE POST ───────────────────────────────────────────────────────
def post_pulse(brain_state):
    if not MASTODON_TOKEN: return
    rev       = brain_state.get('revenue', {})
    reach     = brain_state.get('reach', {})
    impact    = brain_state.get('impact', {})
    synthesis = brain_state.get('synthesis', {})
    top       = synthesis.get('decisions', [])
    if not top: return

    post = (
        f'🧠 SolarPunk daily brain [{TODAY}]\n\n'
        f'💰 Revenue: ${rev.get("grand_total", 0):.2f} | PCRF: ${rev.get("pcrf_routed", 0):.2f}\n'
        f'📡 {len(reach.get("platforms_active", []))} platforms | {reach.get("github_forks", 0)} forks\n'
        f'🌍 Impact: {impact.get("impact_score", 0)}/100\n\n'
        f'⚡ {top[0][:120]}\n\n'
        f'#SolarPunk #EthicalAI #CauseCommerce #OpenSource'
    )
    base   = MASTODON_BASE_URL.rstrip('/')
    result = http_post(
        f'{base}/api/v1/statuses',
        headers={'Authorization': f'Bearer {MASTODON_TOKEN}'},
        data={'status': post, 'visibility': 'public'}
    )
    if result.get('id'):
        print(f'\n[3d-brain] 📣 Pulse posted: {result.get("url", "ok")}')


# ── MAIN ──────────────────────────────────────────────────────────────────────
def run():
    print(f'\n{"="*60}')
    print(f'[three_d_brain] 🌸 SolarPunk 3D Intelligence Engine v2 — {NOW}')
    print(f'{"="*60}')

    DATA.mkdir(parents=True, exist_ok=True)

    # PHASE 0: Load human directives — shapes everything that follows
    print('\n[3d-brain] 🎯 Loading human directives (Phase 0 output)')
    directives = load_directives()

    # Scan all three dimensions
    revenue = scan_revenue()
    reach   = scan_reach()
    impact  = scan_impact()

    # Cross-dimensional synthesis — NOW DIRECTIVE-INFORMED
    synthesis = synthesize(revenue, reach, impact, directives)

    brain_state = {
        'timestamp': NOW,
        'date': TODAY,
        'revenue': revenue,
        'reach': reach,
        'impact': impact,
        'synthesis': synthesis,
        'directives': {
            'active': bool(directives.get('human_message') or directives.get('priority')),
            'message': directives.get('human_message', ''),
            'priority': directives.get('priority', []),
            'pause': directives.get('pause', []),
            'amplify': directives.get('amplify', []),
            'build_next': directives.get('build_next'),
        },
        'system_status': {
            'gumroad_configured':  bool(GUMROAD_SECRET),
            'notion_configured':   bool(NOTION_TOKEN),
            'mastodon_configured': bool(MASTODON_TOKEN),
            'hf_configured':       bool(HF_TOKEN),
        }
    }

    (DATA / 'three_d_brain.json').write_text(json.dumps(brain_state, indent=2))
    print(f'\n[three_d_brain] ✅ Brain state saved → data/three_d_brain.json')

    update_notion(brain_state)
    post_pulse(brain_state)

    print(f'\n{"="*60}')
    print(f'[three_d_brain] 🌸 SYNTHESIS COMPLETE')
    print(f'  Revenue: ${revenue["grand_total"]:.2f} | PCRF: ${revenue["pcrf_routed"]:.2f}')
    print(f'  Reach: {len(reach["platforms_active"])} platforms | {reach["github_forks"]} forks')
    print(f'  Impact: {impact["impact_score"]}/100')
    print(f'  Synthesis: {synthesis["synthesis_quality"]}')
    print(f'  Decisions: {len(synthesis["decisions"])}')
    if synthesis.get('human_directive_active'):
        print(f'  🎯 Human directive shaped this synthesis')
    print(f'{"="*60}\n')

    return brain_state


if __name__ == '__main__':
    run()
