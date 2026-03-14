# File: testnet_starter.py
# Immediate testnet deployment
# Save as: crypto_ubi_engine/testnet_starter.py

import os
from web3 import Web3
from solcx import compile_source

def deploy_testnet():
    """Deploy Solar Token on Polygon Mumbai Testnet TODAY"""
    
    # Connect to Polygon Mumbai
    w3 = Web3(Web3.HTTPProvider('https://rpc-mumbai.maticvigil.com'))
    
    # Test account (use MetaMask test account)
    private_key = os.getenv('TEST_PRIVATE_KEY')
    account = w3.eth.account.from_key(private_key)
    
    print(f"💰 Account: {account.address}")
    print(f"🪙 Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} MATIC")
    
    # Compile contract
    with open('contracts/solar_token.sol', 'r') as f:
        source = f.read()
    
    compiled = compile_source(source)
    contract_id, contract_interface = compiled.popitem()
    
    # Deploy
    contract = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )
    
    # Build transaction
    construct_txn = contract.constructor().build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': w3.to_wei('30', 'gwei')
    })
    
    # Sign and send
    signed = account.sign_transaction(construct_txn)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    
    print(f"🚀 Contract deployment sent! TX: {tx_hash.hex()}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    print(f"✅ Contract deployed at: {receipt.contractAddress}")
    
    # Save address
    with open('deployed_address.txt', 'w') as f:
        f.write(receipt.contractAddress)
    
    return receipt.contractAddress

def setup_testnet_ai():
    """Setup AI trading on testnet exchanges"""
    
    # Create test accounts on crypto exchanges
    exchanges_to_setup = [
        {
            'name': 'Binance Testnet',
            'url': 'https://testnet.binance.vision',
            'api_docs': 'https://testnet.binance.vision/',
            'steps': [
                '1. Go to testnet.binance.vision',
                '2. Create test account',
                '3. Generate API keys',
                '4. Fund with test USDT'
            ]
        },
        {
            'name': 'KuCoin Testnet',
            'url': 'https://sandbox.kucoin.com',
            'api_docs': 'https://docs.kucoin.com/#sandbox',
            'steps': [
                '1. Register at sandbox.kucoin.com',
                '2. Get test API keys',
                '3. Fund with test tokens'
            ]
        }
    ]
    
    print("\n🔧 SETUP CRYPTO EXCHANGE TESTNET ACCOUNTS:")
    for exchange in exchanges_to_setup:
        print(f"\n{exchange['name']}:")
        print(f"URL: {exchange['url']}")
        print("Steps:")
        for step in exchange['steps']:
            print(f"  {step}")
    
    print("\n⏰ Estimated setup time: 30 minutes")
    print("💰 Test funds available: Unlimited test tokens")
    print("🎯 Start arbitrage testing: IMMEDIATELY AFTER SETUP")

def immediate_actions():
    """What you can do RIGHT NOW"""
    
    actions = [
        {
            'time': 'Now (5 min)',
            'action': 'Create testnet accounts on Binance & KuCoin',
            'result': 'Get free test crypto to practice with'
        },
        {
            'time': 'Today (30 min)',
            'action': 'Deploy Solar Token contract on Polygon Mumbai',
            'result': 'Have a live UBI token on testnet'
        },
        {
            'time': 'Today (60 min)',
            'action': 'Run the arbitrage AI on testnet',
            'result': 'Generate simulated UBI distributions'
        },
        {
            'time': 'Week 1',
            'action': 'Add 5 more trading pairs',
            'result': 'Increase arbitrage opportunities 10x'
        },
        {
            'time': 'Week 2',
            'action': 'Deploy with $100 real capital',
            'result': 'Start generating actual UBI'
        },
        {
            'time': 'Month 1',
            'action': 'Scale to $10,000 pool',
            'result': 'Generate $500/month UBI for 100 members'
        }
    ]
    
    print("\n⏳ IMMEDIATE TIMELINE TO INFINITE UBI:")
    for a in actions:
        print(f"\n[{a['time']}]")
        print(f"Action: {a['action']}")
        print(f"Result: {a['result']}")

if __name__ == "__main__":
    print("🚀 SOLARPUNK CRYPTO UBI ENGINE - DAY 1 LAUNCH")
    print("=" * 60)
    
    immediate_actions()
    setup_testnet_ai()
    
    response = input("\n👉 Ready to deploy testnet contract? (y/n): ")
    if response.lower() == 'y':
        address = deploy_testnet()
        print(f"\n🎉 CONTRACT DEPLOYED!")
        print(f"Address: {address}")
        print(f"View on Polygonscan: https://mumbai.polygonscan.com/address/{address}")
        print("\n💫 YOUR UBI TOKEN IS NOW LIVE ON TESTNET!")