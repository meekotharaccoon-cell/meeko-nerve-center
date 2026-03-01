#!/usr/bin/env python3
"""
Multi-Chain Wallet Configuration
=================================
Accepts every blockchain. Never turns away money.

Wallet hierarchy (from your Phantom setup):
  • Solana         — fastest, lowest fees, best for micropayments
  • Ethereum        — most widely used, highest liquidity
  • Base            — ETH L2, near-zero fees, fast
  • Polygon         — ETH L2, very cheap, high volume
  • Bitcoin Taproot — bc1p... modern, efficient, private
  • Bitcoin SegWit  — bc1q... most compatible, widest support
  • Sui             — high performance, growing ecosystem
  • Monad           — EVM-compatible, emerging
  • HyperEVM Lite   — Hyperliquid ecosystem

Strategy:
  PRIMARY:   Solana (SOL/USDC) — instant, $0.001 fees, used by most platforms
  SECONDARY: Base (USDC) — ETH ecosystem but cheap, Coinbase native
  TERTIARY:  Bitcoin SegWit — widest compatibility, most recognized
  REST:      All others accepted, auto-displayed based on what's available

For the compound/reinvestment split:
  • Route to Solana by default (cheapest compounding)
  • ETH/Base for EVM ecosystem interactions
  • Bitcoin holds as long-term store

NEVER store private keys here. Public addresses only.
"""

import os

# ── Load from environment (set via setup_wizard.py) ───────────────────────
WALLETS = {
    'solana':         os.environ.get('WALLET_SOLANA', ''),
    'ethereum':       os.environ.get('WALLET_ETHEREUM', ''),
    'base':           os.environ.get('WALLET_BASE', ''),          # same address as ETH usually
    'polygon':        os.environ.get('WALLET_POLYGON', ''),       # same address as ETH usually
    'monad':          os.environ.get('WALLET_MONAD', ''),         # same address as ETH usually
    'hyperevm':       os.environ.get('WALLET_HYPEREVM', ''),      # same address as ETH usually
    'bitcoin_taproot':  os.environ.get('WALLET_BTC_TAPROOT', ''),  # bc1p...
    'bitcoin_segwit':   os.environ.get('WALLET_BTC_SEGWIT', ''),   # bc1q...
    'sui':            os.environ.get('WALLET_SUI', ''),
}

# EVM chains share the same address format (0x...)
# If WALLET_ETHEREUM is set, auto-populate all EVM chains that aren't explicitly set
_eth = WALLETS.get('ethereum', '')
for _chain in ('base', 'polygon', 'monad', 'hyperevm'):
    if not WALLETS.get(_chain) and _eth:
        WALLETS[_chain] = _eth


# ── Chain metadata ─────────────────────────────────────────────────────────────
CHAIN_META = {
    'solana': {
        'name': 'Solana', 'symbol': 'SOL', 'stablecoin': 'USDC',
        'avg_fee_usd': 0.001, 'finality_sec': 1,
        'best_for': 'micropayments, USDC routing, DeFi compounding',
        'explorer': 'https://solscan.io/account/{address}',
        'qr_prefix': 'solana:{address}',
        'priority': 1,
    },
    'base': {
        'name': 'Base', 'symbol': 'ETH', 'stablecoin': 'USDC',
        'avg_fee_usd': 0.01, 'finality_sec': 2,
        'best_for': 'Coinbase users, cheap ETH ecosystem, USDC',
        'explorer': 'https://basescan.org/address/{address}',
        'qr_prefix': 'ethereum:{address}@8453',
        'priority': 2,
    },
    'ethereum': {
        'name': 'Ethereum', 'symbol': 'ETH', 'stablecoin': 'USDC',
        'avg_fee_usd': 2.00, 'finality_sec': 12,
        'best_for': 'largest ecosystem, institutional, NFTs',
        'explorer': 'https://etherscan.io/address/{address}',
        'qr_prefix': 'ethereum:{address}',
        'priority': 3,
    },
    'polygon': {
        'name': 'Polygon', 'symbol': 'MATIC/POL', 'stablecoin': 'USDC',
        'avg_fee_usd': 0.01, 'finality_sec': 2,
        'best_for': 'gaming, NFTs, high-volume micropayments',
        'explorer': 'https://polygonscan.com/address/{address}',
        'qr_prefix': 'ethereum:{address}@137',
        'priority': 4,
    },
    'bitcoin_segwit': {
        'name': 'Bitcoin (SegWit)', 'symbol': 'BTC', 'stablecoin': None,
        'avg_fee_usd': 1.00, 'finality_sec': 600,
        'best_for': 'widest recognition, most compatible, store of value',
        'explorer': 'https://mempool.space/address/{address}',
        'qr_prefix': 'bitcoin:{address}',
        'priority': 5,
    },
    'bitcoin_taproot': {
        'name': 'Bitcoin (Taproot)', 'symbol': 'BTC', 'stablecoin': None,
        'avg_fee_usd': 1.00, 'finality_sec': 600,
        'best_for': 'privacy, efficiency, modern Bitcoin',
        'explorer': 'https://mempool.space/address/{address}',
        'qr_prefix': 'bitcoin:{address}',
        'priority': 6,
    },
    'sui': {
        'name': 'Sui', 'symbol': 'SUI', 'stablecoin': 'USDC',
        'avg_fee_usd': 0.001, 'finality_sec': 1,
        'best_for': 'gaming, NFTs, fast growing ecosystem',
        'explorer': 'https://suiscan.xyz/mainnet/account/{address}',
        'qr_prefix': 'sui:{address}',
        'priority': 7,
    },
    'monad': {
        'name': 'Monad', 'symbol': 'MON', 'stablecoin': 'USDC',
        'avg_fee_usd': 0.001, 'finality_sec': 1,
        'best_for': 'high performance EVM, emerging ecosystem',
        'explorer': 'https://explorer.monad.xyz/address/{address}',
        'qr_prefix': 'ethereum:{address}',
        'priority': 8,
    },
    'hyperevm': {
        'name': 'HyperEVM (Lite)', 'symbol': 'HYPE', 'stablecoin': 'USDC',
        'avg_fee_usd': 0.001, 'finality_sec': 1,
        'best_for': 'Hyperliquid ecosystem, perps traders',
        'explorer': 'https://hyperscan.xyz/address/{address}',
        'qr_prefix': 'ethereum:{address}',
        'priority': 9,
    },
}


# ── Public API ─────────────────────────────────────────────────────────────────
def get_active_wallets():
    """Return all wallets that have an address configured."""
    return {chain: addr for chain, addr in WALLETS.items() if addr}

def get_primary_wallet():
    """Return the best wallet for routing. Prefers Solana for low fees."""
    for chain in ('solana', 'base', 'polygon', 'ethereum', 'bitcoin_segwit'):
        if WALLETS.get(chain):
            return chain, WALLETS[chain]
    return None, None

def get_payment_page_data():
    """
    Return structured data for a payment/donation page.
    Shows all active wallets sorted by priority.
    """
    active = get_active_wallets()
    chains = []
    for chain, addr in active.items():
        meta = CHAIN_META.get(chain, {})
        chains.append({
            'chain': chain,
            'name': meta.get('name', chain),
            'symbol': meta.get('symbol', ''),
            'address': addr,
            'explorer': meta.get('explorer', '').replace('{address}', addr),
            'qr': meta.get('qr_prefix', '').replace('{address}', addr),
            'fee': meta.get('avg_fee_usd', 0),
            'best_for': meta.get('best_for', ''),
            'priority': meta.get('priority', 99),
        })
    chains.sort(key=lambda x: x['priority'])
    return chains

def format_wallet_list_for_post():
    """Format wallet list for a social post or email."""
    active = get_active_wallets()
    if not active:
        return 'Wallets not yet configured.'
    lines = ['Accepting on all chains:']
    for chain in sorted(active.keys(), key=lambda c: CHAIN_META.get(c, {}).get('priority', 99)):
        meta = CHAIN_META.get(chain, {})
        addr = active[chain]
        short = addr[:6] + '...' + addr[-4:] if len(addr) > 12 else addr
        lines.append(f'  {meta.get("name", chain)} ({meta.get("symbol", "")}): {short}')
    return '\n'.join(lines)
