#!/usr/bin/env python3
"""
Multi-Chain Wallet Configuration
=================================
Accepts every blockchain. Never turns away money.

Checks multiple possible secret names for each wallet so it works
regardless of what you named it in GitHub Secrets. If you already
have ETH_WALLET or PHANTOM_WALLET_ADDRESS set, this finds it.

Your 9 wallets from Phantom:
  Solana, Ethereum, Base, Polygon, Bitcoin Taproot,
  Bitcoin SegWit, Sui, Monad, HyperEVM Lite

EVM chains (Ethereum/Base/Polygon/Monad/HyperEVM) share one 0x... address.
Set one, the rest auto-fill.

NEVER store private keys here. Public addresses only.
"""

import os


def _get(*env_names):
    """Try multiple env var names, return first match."""
    for name in env_names:
        val = os.environ.get(name, '').strip()
        if val:
            return val
    return ''


# ── Load wallets — checks every reasonable secret name ────────────────────────
WALLETS = {
    'solana': _get(
        'WALLET_SOLANA', 'SOL_WALLET', 'SOLANA_WALLET', 'SOLANA_ADDRESS',
    ),
    'ethereum': _get(
        'WALLET_ETHEREUM', 'ETH_WALLET', 'ETHEREUM_WALLET', 'ETHEREUM_ADDRESS',
        'PHANTOM_WALLET_ADDRESS',  # older setup_wizard used this
    ),
    'base': _get(
        'WALLET_BASE', 'BASE_WALLET',
    ),
    'polygon': _get(
        'WALLET_POLYGON', 'MATIC_WALLET', 'POLYGON_WALLET',
    ),
    'monad': _get(
        'WALLET_MONAD', 'MONAD_WALLET',
    ),
    'hyperevm': _get(
        'WALLET_HYPEREVM', 'HYPEREVM_WALLET', 'HYPE_WALLET',
    ),
    'bitcoin_taproot': _get(
        'WALLET_BTC_TAPROOT', 'BTC_TAPROOT', 'BITCOIN_TAPROOT',
    ),
    'bitcoin_segwit': _get(
        'WALLET_BTC_SEGWIT', 'BTC_SEGWIT', 'BITCOIN_SEGWIT', 'BTC_WALLET',
    ),
    'sui': _get(
        'WALLET_SUI', 'SUI_WALLET', 'SUI_ADDRESS',
    ),
}

# EVM chains share the same 0x... address.
# If ethereum is set, auto-fill any EVM chain that isn't explicitly configured.
_eth = WALLETS['ethereum']
for _chain in ('base', 'polygon', 'monad', 'hyperevm'):
    if not WALLETS[_chain] and _eth:
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
        'name': 'Base', 'symbol': 'ETH/USDC', 'stablecoin': 'USDC',
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
        'name': 'Polygon', 'symbol': 'POL', 'stablecoin': 'USDC',
        'avg_fee_usd': 0.01, 'finality_sec': 2,
        'best_for': 'high-volume micropayments, Global South',
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
    """Return best wallet for routing. Prefers Solana (lowest fees)."""
    for chain in ('solana', 'base', 'polygon', 'ethereum', 'bitcoin_segwit'):
        if WALLETS.get(chain):
            return chain, WALLETS[chain]
    return None, None


def get_payment_page_data():
    """Structured data for payment/donation page. All active wallets by priority."""
    active = get_active_wallets()
    chains = []
    for chain, addr in active.items():
        meta = CHAIN_META.get(chain, {})
        chains.append({
            'chain':    chain,
            'name':     meta.get('name', chain),
            'symbol':   meta.get('symbol', ''),
            'address':  addr,
            'explorer': meta.get('explorer', '').replace('{address}', addr),
            'qr':       meta.get('qr_prefix', '').replace('{address}', addr),
            'fee':      meta.get('avg_fee_usd', 0),
            'best_for': meta.get('best_for', ''),
            'priority': meta.get('priority', 99),
        })
    chains.sort(key=lambda x: x['priority'])
    return chains


def format_wallet_list_for_post():
    """Short wallet list for social posts and emails."""
    active = get_active_wallets()
    if not active:
        return 'Wallets not yet configured.'
    lines = ['Accepting crypto on all chains:']
    for chain in sorted(active.keys(), key=lambda c: CHAIN_META.get(c, {}).get('priority', 99)):
        meta = CHAIN_META.get(chain, {})
        addr = active[chain]
        short = addr[:6] + '...' + addr[-4:] if len(addr) > 12 else addr
        lines.append(f'  {meta.get("name", chain)} ({meta.get("symbol", "")}): {short}')
    return '\n'.join(lines)


def diagnostics():
    """Print which wallets are configured and from which secret names."""
    print('\n[wallets] Configured wallets:')
    active = get_active_wallets()
    if not active:
        print('  None configured yet. Run setup_wizard.py to add wallet addresses.')
        return
    for chain, addr in sorted(active.items(), key=lambda x: CHAIN_META.get(x[0], {}).get('priority', 99)):
        meta = CHAIN_META.get(chain, {})
        short = addr[:8] + '...' + addr[-6:] if len(addr) > 16 else addr
        print(f'  ✅ {meta.get("name", chain):20s} {short}')
    print(f'\n  Total: {len(active)}/9 chains active')
    primary_chain, primary_addr = get_primary_wallet()
    if primary_chain:
        print(f'  Primary routing chain: {primary_chain}')


if __name__ == '__main__':
    diagnostics()
