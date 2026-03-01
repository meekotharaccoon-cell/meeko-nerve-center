#!/usr/bin/env python3
"""
THREE_D_BRAIN.py — The SolarPunk 3-Dimensional Intelligence Engine
===================================================================
This is the meta-cognition layer. It doesn't just run tasks — it THINKS
across ALL dimensions of the system simultaneously:

  DIMENSION 1 — REVENUE AXIS
    Gumroad sales × Ko-fi donations × grant funding
    → What's making money? What should we make next?

  DIMENSION 2 — REACH AXIS
    Social engagement × fork count × SEO × email opens
    → Who's listening? How far is the signal spreading?

  DIMENSION 3 — IMPACT AXIS
    Cause metrics × PCRF routing × humanitarian intelligence
    → Is the work actually doing good in the world?

Cross-dimensional synthesis generates STRATEGIC DECISIONS, not just reports.
Runs as Phase 1.5 in MASTER_CONTROLLER — after self-healer, before everything else.

Output: data/three_d_brain.json + posts strategic insight to social + updates Notion.
"""

import json, os, datetime, glob
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M')

# ── Secrets ──────────────────────────────────────────────────────────────────
MASTODON_TOKEN    = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')
NOTION_TOKEN      = os.environ.get('NOTION_TOKEN', '')
GUMROAD_SECRET    = os.environ.get('GUMROAD_SECRET', '')
HF_TOKEN          = os.environ.get('HF_TOKEN', '')


def load_json(path, default=None):
    """Load a JSON file or return default. Never crashes."""
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text())
    except Exception as e:
        print(f"  [3d-brain] load error {path}: {e}")
    return default if default is not None else {}


def http_post(url, data=None, headers=None, json_data=None):
    """Simple HTTP POST wrapper."""
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
    """Simple HTTP GET wrapper."""
    try:
        req = urllib_request.Request(url, headers=headers or {})
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {'error': str(e)}


# ── DIMENSION 1: REVENUE ──────────────────────────────────────────────────────
def scan_revenue():
    """Aggregate all revenue streams into one picture."""
    print("\n[3d-brain] 💰 DIMENSION 1: REVENUE SCAN")
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

    # Gumroad data
    gumroad = load_json(DATA / 'gumroad_sales.json')
    if gumroad.get('status') == 'ok':
        revenue['gumroad_total'] = gumroad.get('total_revenue_usd', 0)
        revenue['gumroad_products'] = gumroad.get('products_count', 0)
        revenue['gumroad_sales'] = gumroad.get('sales_count', 0)
        revenue['pcrf_routed'] += gumroad.get('pcrf_split_usd', 0)
        revenue['retained'] += gumroad.get('retained_usd', 0)
        revenue['sources'].append('gumroad')
        if gumroad.get('new_sales'):
            revenue['last_sale'] = TODAY

    # Ko-fi data (if exists)
    kofi = load_json(DATA / 'kofi_data.json')
    if kofi:
        revenue['kofi_total'] = kofi.get('total', 0)
        revenue['sources'].append('kofi')

    # Grant data
    grants = load_json(DATA / 'grant_intelligence.json')
    if grants:
        revenue['grants_total'] = grants.get('estimated_value', 0)
        revenue['sources'].append('grants')

    total = revenue['gumroad_total'] + revenue['kofi_total']
    revenue['grand_total'] = round(total, 2)
    revenue['pcrf_routed'] = round(revenue['pcrf_routed'], 2)

    print(f"  Total revenue: ${revenue['grand_total']:.2f}")
    print(f"  PCRF routed: ${revenue['pcrf_routed']:.2f}")
    print(f"  Products live: {revenue['gumroad_products']}")
    return revenue


# ── DIMENSION 2: REACH ────────────────────────────────────────────────────────
def scan_reach():
    """Map the spread of the signal across all platforms."""
    print("\n[3d-brain] 📡 DIMENSION 2: REACH SCAN")
    reach = {
        'mastodon_followers': 0,
        'github_forks': 0,
        'github_stars': 0,
        'email_list': 0,
        'platforms_active': [],
        'viral_potential': 'low',
    }

    # GitHub stats
    gh_stats = load_json(DATA / 'fork_stats.json')
    if gh_stats:
        reach['github_forks'] = gh_stats.get('total_forks', 0)
        reach['github_stars'] = gh_stats.get('total_stars', 0)
        reach['platforms_active'].append('github')

    # Social stats
    social = load_json(DATA / 'social_stats.json')
    if social:
        reach['mastodon_followers'] = social.get('mastodon_followers', 0)
        if social.get('mastodon_active'):
            reach['platforms_active'].append('mastodon')
        if social.get('bluesky_active'):
            reach['platforms_active'].append('bluesky')

    # Audience data
    audience = load_json(DATA / 'audience_data.json')
    if audience:
        reach['email_list'] = audience.get('email_count', 0)
        reach['platforms_active'].append('email')

    # Determine viral potential
    forks = reach['github_forks']
    reach['viral_potential'] = (
        'high' if forks > 20 else
        'medium' if forks > 5 else
        'building'
    )

    print(f"  GitHub forks: {reach['github_forks']}")
    print(f"  Platforms active: {reach['platforms_active']}")
    print(f"  Viral potential: {reach['viral_potential']}")
    return reach


# ── DIMENSION 3: IMPACT ───────────────────────────────────────────────────────
def scan_impact():
    """Measure real-world humanitarian impact."""
    print("\n[3d-brain] 🌍 DIMENSION 3: IMPACT SCAN")
    impact = {
        'pcrf_total_routed': 0.0,
        'grants_hunting': False,
        'content_humanitarian': False,
        'fork_network_size': 0,
        'cause_commerce_active': False,
        'impact_score': 0,
    }

    # Check if PCRF routing has happened
    gumroad = load_json(DATA / 'gumroad_sales.json')
    if gumroad.get('pcrf_split_usd', 0) > 0:
        impact['pcrf_total_routed'] = gumroad['pcrf_split_usd']
        impact['cause_commerce_active'] = True
        impact['impact_score'] += 30

    # Check humanitarian content
    humanitarian = load_json(DATA / 'humanitarian_content.json')
    if humanitarian:
        impact['content_humanitarian'] = True
        impact['impact_score'] += 20

    # Check grant hunting
    grants = load_json(DATA / 'grant_intelligence.json')
    if grants and grants.get('opportunities'):
        impact['grants_hunting'] = True
        impact['impact_score'] += 25

    # Fork network = our signal spreading = impact multiplier
    gh_stats = load_json(DATA / 'fork_stats.json')
    impact['fork_network_size'] = gh_stats.get('total_forks', 0) if gh_stats else 0
    impact['impact_score'] += min(impact['fork_network_size'] * 5, 25)

    print(f"  PCRF routed: ${impact['pcrf_total_routed']:.2f}")
    print(f"  Impact score: {impact['impact_score']}/100")
    print(f"  Cause commerce: {impact['cause_commerce_active']}")
    return impact


# ── CROSS-DIMENSIONAL SYNTHESIS ───────────────────────────────────────────────
def synthesize(revenue, reach, impact):
    """
    The actual 3D thinking. Where do the three dimensions intersect?
    What does the PATTERN tell us?
    """
    print("\n[3d-brain] 🧠 CROSS-DIMENSIONAL SYNTHESIS")

    decisions = []
    insights = []
    next_actions = []

    # Pattern: Products exist but no sales
    if revenue['gumroad_products'] > 0 and revenue['gumroad_sales'] == 0:
        insights.append("📦 Products are live but no sales yet — the funnel needs traffic")
        decisions.append("PRIORITY: Drive traffic to Gumroad via Mastodon + social posting")
        next_actions.append("trigger: cross_poster.py with product promotion content")

    # Pattern: No products but traffic exists
    if revenue['gumroad_products'] == 0 and reach['github_forks'] > 0:
        insights.append("🔥 Forks exist but no products — monetization gap detected")
        decisions.append("PRIORITY: Run generate-pdfs workflow immediately")
        next_actions.append("trigger: generate-pdfs.yml workflow_dispatch")

    # Pattern: Low reach = signal not spreading
    if not reach['platforms_active'] or len(reach['platforms_active']) < 2:
        insights.append("📡 Signal confined to 1 platform — needs expansion")
        decisions.append("EXPAND: Activate cross-posting to all platforms")
        next_actions.append("trigger: social_poster.py")

    # Pattern: Revenue exists but low impact score
    if revenue['grand_total'] > 0 and impact['impact_score'] < 30:
        insights.append("💰 Revenue flowing but impact score low — check PCRF routing")
        decisions.append("VERIFY: Confirm 70% PCRF split is happening automatically")
        next_actions.append("check: donation_engine.py PCRF routing")

    # Pattern: All three dimensions building — green status
    if revenue['gumroad_products'] > 0 and len(reach['platforms_active']) >= 2 and impact['cause_commerce_active']:
        insights.append("🌸 All three dimensions active — system is compounding")
        decisions.append("SUSTAIN: Keep all cycles running, focus on content quality")
        next_actions.append("trigger: idea_engine.py for next product")

    # Always: what's the next $1 product to build?
    grants_data = load_json(DATA / 'grant_intelligence.json')
    if grants_data and grants_data.get('top_opportunity'):
        insights.append(f"🏆 Grant opportunity: {grants_data['top_opportunity']}")
        decisions.append("APPLY: grant_auto_submitter.py for top opportunity")
        next_actions.append("trigger: grant_intelligence.py weekly scan")

    print(f"  Insights: {len(insights)}")
    print(f"  Decisions: {len(decisions)}")
    for d in decisions[:3]:
        print(f"    → {d}")

    return {
        'insights': insights,
        'decisions': decisions,
        'next_actions': next_actions,
        'synthesis_quality': 'operational' if len(decisions) > 0 else 'baseline',
    }


# ── NOTION UPDATE ─────────────────────────────────────────────────────────────
def update_notion(brain_state):
    """Push the 3D brain state to Notion command center."""
    if not NOTION_TOKEN:
        print("\n[3d-brain] ⚠️  NOTION_TOKEN not set — skipping Notion update")
        return

    print("\n[3d-brain] 📝 Updating Notion command center")
    headers = {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28',
    }

    # Search for existing page
    search = http_post(
        'https://api.notion.com/v1/search',
        headers=headers,
        json_data={'query': '🧠 SolarPunk Brain State', 'filter': {'value': 'page', 'property': 'object'}}
    )

    rev = brain_state.get('revenue', {})
    reach = brain_state.get('reach', {})
    impact = brain_state.get('impact', {})
    synthesis = brain_state.get('synthesis', {})

    content_text = f"""# 🧠 SolarPunk 3D Brain State — {TODAY}

## 💰 DIMENSION 1: REVENUE
- Total Revenue: ${rev.get('grand_total', 0):.2f}
- Gumroad Products: {rev.get('gumroad_products', 0)}
- Total Sales: {rev.get('gumroad_sales', 0)}
- PCRF Routed: ${rev.get('pcrf_routed', 0):.2f} (70%)

## 📡 DIMENSION 2: REACH  
- GitHub Forks: {reach.get('github_forks', 0)}
- Platforms Active: {', '.join(reach.get('platforms_active', ['none']))}
- Viral Potential: {reach.get('viral_potential', 'unknown')}

## 🌍 DIMENSION 3: IMPACT
- Impact Score: {impact.get('impact_score', 0)}/100
- Cause Commerce: {'✅ Active' if impact.get('cause_commerce_active') else '⚠️ Not yet'}
- Grants Hunting: {'✅ Yes' if impact.get('grants_hunting') else '⚠️ No'}

## 🔮 SYNTHESIS & DECISIONS
{chr(10).join(f'- {d}' for d in synthesis.get('decisions', ['No decisions yet']))}

## ⚡ NEXT ACTIONS
{chr(10).join(f'- {a}' for a in synthesis.get('next_actions', ['No actions yet']))}

---
*Auto-generated by three_d_brain.py at {NOW} UTC*
"""

    # Try to update existing page or create new one
    pages = search.get('results', []) if not search.get('error') else []

    if pages:
        page_id = pages[0]['id']
        result = http_post(
            f'https://api.notion.com/v1/blocks/{page_id}/children',
            headers=headers,
            json_data={
                'children': [{
                    'object': 'block',
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': [{'type': 'text', 'text': {'content': f'[{NOW}] Revenue: ${rev.get("grand_total", 0):.2f} | PCRF: ${rev.get("pcrf_routed", 0):.2f} | Impact: {impact.get("impact_score", 0)}/100 | Forks: {reach.get("github_forks", 0)}'}}]
                    }
                }]
            }
        )
        print(f"  [notion] ✅ Updated existing page: {pages[0].get('url', page_id)}")
    else:
        # Create new page at workspace level
        result = http_post(
            'https://api.notion.com/v1/pages',
            headers=headers,
            json_data={
                'parent': {'type': 'workspace', 'workspace': True},
                'properties': {
                    'title': [{'type': 'text', 'text': {'content': '🧠 SolarPunk Brain State'}}]
                },
                'children': [{
                    'object': 'block',
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': [{'type': 'text', 'text': {'content': content_text}}]
                    }
                }]
            }
        )
        if result.get('error'):
            print(f"  [notion] ❌ Failed: {result['error']}")
        else:
            print(f"  [notion] ✅ Created new page")


# ── MASTODON PULSE POST ───────────────────────────────────────────────────────
def post_pulse(brain_state):
    """Post a brief 3D pulse to Mastodon — not promotional, just real."""
    if not MASTODON_TOKEN:
        print("\n[3d-brain] ⚠️  No MASTODON_TOKEN — skipping social pulse")
        return

    rev = brain_state.get('revenue', {})
    reach = brain_state.get('reach', {})
    impact = brain_state.get('impact', {})
    synthesis = brain_state.get('synthesis', {})

    # Only post if there's something meaningful to say
    top_decision = synthesis.get('decisions', [])
    if not top_decision:
        print("\n[3d-brain] ℹ️  Nothing significant to post today")
        return

    post = f"""🧠 SolarPunk daily brain state [{TODAY}]

💰 Revenue: ${rev.get('grand_total', 0):.2f} total | PCRF routed: ${rev.get('pcrf_routed', 0):.2f}
📡 Reach: {len(reach.get('platforms_active', []))} platforms | {reach.get('github_forks', 0)} forks | {reach.get('viral_potential', '?')} viral potential
🌍 Impact: {impact.get('impact_score', 0)}/100

⚡ Priority today: {top_decision[0][:120] if top_decision else 'Building'}

#SolarPunk #EthicalAI #CauseCommerce #OpenSource"""

    base = MASTODON_BASE_URL.rstrip('/')
    result = http_post(
        f'{base}/api/v1/statuses',
        headers={'Authorization': f'Bearer {MASTODON_TOKEN}'},
        data={'status': post, 'visibility': 'public'}
    )

    if result.get('id'):
        print(f"\n[3d-brain] 📣 Posted pulse: {result.get('url', 'posted')}")
    else:
        print(f"\n[3d-brain] ⚠️  Post failed: {result.get('error', result)}")


# ── MAIN ──────────────────────────────────────────────────────────────────────
def run():
    print(f"\n{'='*60}")
    print(f"[three_d_brain] 🌸 SolarPunk 3D Intelligence Engine — {NOW}")
    print(f"{'='*60}")

    DATA.mkdir(parents=True, exist_ok=True)

    # Scan all three dimensions
    revenue = scan_revenue()
    reach   = scan_reach()
    impact  = scan_impact()

    # Cross-dimensional synthesis
    synthesis = synthesize(revenue, reach, impact)

    # Assemble full brain state
    brain_state = {
        'timestamp': NOW,
        'date': TODAY,
        'revenue': revenue,
        'reach': reach,
        'impact': impact,
        'synthesis': synthesis,
        'system_status': {
            'gumroad_configured': bool(GUMROAD_SECRET),
            'notion_configured': bool(NOTION_TOKEN),
            'mastodon_configured': bool(MASTODON_TOKEN),
            'hf_configured': bool(HF_TOKEN),
        }
    }

    # Save to data/
    output_path = DATA / 'three_d_brain.json'
    output_path.write_text(json.dumps(brain_state, indent=2))
    print(f"\n[three_d_brain] ✅ Brain state saved → data/three_d_brain.json")

    # Update Notion
    update_notion(brain_state)

    # Post pulse to social
    post_pulse(brain_state)

    # Print summary
    print(f"\n{'='*60}")
    print(f"[three_d_brain] 🌸 SYNTHESIS COMPLETE")
    print(f"  Revenue: ${revenue['grand_total']:.2f} | PCRF: ${revenue['pcrf_routed']:.2f}")
    print(f"  Reach: {len(reach['platforms_active'])} platforms | {reach['github_forks']} forks")
    print(f"  Impact: {impact['impact_score']}/100")
    print(f"  Decisions generated: {len(synthesis['decisions'])}")
    print(f"{'='*60}\n")

    return brain_state


if __name__ == '__main__':
    run()
