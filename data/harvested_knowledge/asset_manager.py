@"
"""
SolarPunk Asset Management System
Manages tokenized resources and distributions
"""

import json
from datetime import datetime

class AssetManager:
    def __init__(self):
        self.assets = {}
        self.transaction_log = []
        self.initialize_default_assets()
    
    def initialize_default_assets(self):
        """Initialize with default asset structure"""
        self.assets = {
            'liquidity_pool': {
                'balance': 10000.00,
                'currency': 'USD',
                'purpose': 'Trading liquidity'
            },
            'humanitarian_fund': {
                'balance': 0.00,
                'currency': 'USD',
                'purpose': 'Gaza relief distribution'
            },
            'ubi_reserve': {
                'balance': 0.00,
                'currency': 'USD',
                'purpose': 'Universal Basic Income'
            },
            'development_fund': {
                'balance': 0.00,
                'currency': 'USD',
                'purpose': 'System development'
            }
        }
    
    def allocate_profits(self, amount, source='liquidity_pool'):
        """Allocate profits according to SolarPunk distribution protocol"""
        if amount <= 0:
            return False
        
        allocations = {
            'humanitarian_fund': 0.50,  # 50% to Gaza relief
            'ubi_reserve': 0.30,        # 30% to UBI
            'development_fund': 0.20     # 20% to development
        }
        
        # Verify sufficient funds
        if self.assets[source]['balance'] < amount:
            print(f"❌ Insufficient funds in {source}")
            return False
        
        # Execute allocations
        for fund, percentage in allocations.items():
            allocation_amount = amount * percentage
            self.assets[source]['balance'] -= allocation_amount
            self.assets[fund]['balance'] += allocation_amount
            
            # Log transaction
            self.log_transaction({
                'timestamp': datetime.now().isoformat(),
                'from': source,
                'to': fund,
                'amount': allocation_amount,
                'type': 'profit_allocation'
            })
        
        print(f"✅ Allocated ${amount:,.2f} according to SolarPunk protocol")
        return True
    
    def log_transaction(self, transaction_data):
        """Record transaction in log"""
        self.transaction_log.append(transaction_data)
        
        # Save to file
        with open('logs/transactions.json', 'w') as f:
            json.dump(self.transaction_log, f, indent=2)
    
    def get_balance_sheet(self):
        """Generate balance sheet report"""
        report = "╔══════════════════════════════════════════════╗\n"
        report += "║          SOLARPUNK ASSET LEDGER             ║\n"
        report += "╠══════════════════════════════════════════════╣\n"
        
        total = 0
        for asset, details in self.assets.items():
            balance = details['balance']
            total += balance
            # Fixed formatting: removed extra $ sign in format string
            report += f"║ {asset.replace('_', ' ').title():20} ${balance:12,.2f} ║\n"
        
        report += "╠══════════════════════════════════════════════╣\n"
        report += f"║ {'TOTAL ASSETS':20} ${total:12,.2f} ║\n"
        report += "╚══════════════════════════════════════════════╝"
        
        return report
    
    def execute_daily_cycle(self, profit_amount=1000):
        """Execute daily profit allocation cycle"""
        print(f"\n🔄 Executing Daily Allocation Cycle")
        print(f"📊 Profit to allocate: ${profit_amount:,.2f}")
        
        success = self.allocate_profits(profit_amount)
        
        if success:
            print(self.get_balance_sheet())
            print(f"\n📝 Transaction logged: logs/transactions.json")
            return True
        return False

def asset_management_demo():
    """Interactive demonstration of asset management"""
    manager = AssetManager()
    
    while True:
        print("\n" + "="*50)
        print("SOLARPUNK ASSET MANAGEMENT SYSTEM")
        print("="*50)
        print("1. View Balance Sheet")
        print("2. Execute Daily Allocation")
        print("3. View Transaction History")
        print("4. Reset to Default")
        print("5. Export Reports")
        print("6. Exit System")
        print("="*50)
        
        choice = input("\nSelect option (1-6): ")
        
        if choice == "1":
            print(manager.get_balance_sheet())
        
        elif choice == "2":
            try:
                amount = float(input("Enter profit amount to allocate: $"))
                manager.execute_daily_cycle(amount)
            except ValueError:
                print("❌ Please enter a valid amount")
        
        elif choice == "3":
            print("\n📋 Transaction History:")
            for tx in manager.transaction_log[-10:]:  # Show last 10 transactions
                print(f"  {tx['timestamp']}: ${tx['amount']:,.2f} {tx['type']}")
        
        elif choice == "4":
            manager.initialize_default_assets()
            print("✅ System reset to default state")
        
        elif choice == "5":
            with open('exports/balance_sheet.txt', 'w') as f:
                f.write(manager.get_balance_sheet())
            print("✅ Balance sheet exported to exports/balance_sheet.txt")
        
        elif choice == "6":
            print("\n🚀 Asset management session completed")
            print("💾 All data saved to logs/ and exports/")
            break
        
        else:
            print("❌ Invalid selection")

def main():
    """Main function for controller integration"""
    asset_management_demo()
    return True

if __name__ == "__main__":
    main()
"@ | Out-File -FilePath "modules/asset_manager.py" -Encoding UTF8 -Force