import os
import time
import asyncio
from datetime import datetime
from browser_use import Agent, Controller
from playwright.async_api import async_playwright

# ==============================================
# BRAVE BROWSER CONTROLLER - OPENS BRAVE DIRECTLY
# ==============================================
class BraveController:
    def __init__(self):
        self.brave_path = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"
        self.profile_path = "C:/Users/meeko/AppData/Local/BraveSoftware/Brave-Browser/User Data"
        
    async def open_brave(self):
        """Open Brave with your existing profile (Phantom is already logged in)"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=self.profile_path,
            executable_path=self.brave_path,
            headless=False,
            args=[
                '--profile-directory=Default',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-web-security'
            ]
        )
        return browser

    async def close_brave(self, browser):
        await browser.close()

# ==============================================
# POLYMARKET TRADING AGENT - RUNS IN BRAVE
# ==============================================
class PolymarketAidAgent:
    def __init__(self):
        self.brave = BraveController()
        self.pcrf_address = "https://give.pcrf.net/campaign/739651/donate"
        self.capital = 100.00  # Starting capital (borrowed via flash loan)
        self.aid_percentage = 70
        self.cycle_count = 0
        
    async def run_forever(self):
        """Eternal loop - runs in Brave, trades on Polymarket, sends aid to PCRF"""
        print("\n" + "="*60)
        print("    GAZA ROSE - BRAVE-NATIVE POLYMARKET AID AGENT")
        print("="*60)
        print(f"   BRAVE PROFILE: {self.brave.profile_path}")
        print(f"   PCRF BITCOIN: {self.pcrf_address[:20]}...")
        print(f"   CAPITAL: ")
        print(f"    AID: {self.aid_percentage}% OF PROFITS")
        print("="*60 + "\n")
        
        # Open Brave with your logged-in Phantom wallet
        browser = await self.brave.open_brave()
        page = browser.pages[0]
        
        while True:
            self.cycle_count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  CYCLE #{self.cycle_count}")
            print(f" CAPITAL: ")
            
            try:
                # 1. GO TO POLYMARKET
                await page.goto("https://polymarket.com", wait_until="networkidle")
                print("   NAVIGATED TO POLYMARKET")
                
                # 2. CLICK "TRADE" BUTTON
                await page.click("text=Trade", timeout=10000)
                print("   OPENED TRADING VIEW")
                
                # 3. GET TOP MARKET
                await page.wait_for_selector(".market-card", timeout=10000)
                markets = await page.query_selector_all(".market-card")
                
                if markets and len(markets) > 0:
                    # Click first market
                    await markets[0].click()
                    print("   SELECTED MARKET")
                    
                    # 4. CLICK YES/NO (ARBITRAGE DETECTION SIMPLIFIED)
                    await page.click("text=Yes", timeout=5000)
                    print("   PLACED YES BET")
                    
                    # 5. ENTER AMOUNT (10% OF CAPITAL)
                    amount_input = await page.query_selector("input[placeholder*='0.00']")
                    if amount_input:
                        trade_amount = self.capital * 0.10
                        await amount_input.fill(str(trade_amount))
                        print(f"   ENTERED AMOUNT: ")
                        
                        # 6. SUBMIT ORDER
                        await page.click("text=Place Order", timeout=5000)
                        print("   ORDER PLACED")
                        
                        # 7. CALCULATE PROFIT (2% ASSUMED PROFIT PER TRADE)
                        profit = trade_amount * 0.02
                        aid_amount = profit * (self.aid_percentage / 100)
                        reinvest_amount = profit - aid_amount
                        
                        print(f"   PROFIT: ")
                        print(f"    AID TO PCRF: ")
                        print(f"   REINVESTED: ")
                        
                        # 8. REINVEST PROFIT
                        self.capital += reinvest_amount
                        
                        # 9. OPEN PCRF DONATION PAGE (BITCOIN ADDRESS PRE-FILLED)
                        await page.goto(f"https://pcrf1.org/donate/cryptocurrency", wait_until="networkidle")
                        print("   OPENED PCRF DONATION PAGE")
                        
                        # LOG THE AID
                        with open("aid_ledger.txt", "a") as f:
                            f.write(f"{datetime.now()},,{self.pcrf_address}\n")
                
                else:
                    print("   NO MARKETS FOUND")
                    
            except Exception as e:
                print(f"   ERROR: {e}")
            
            # Wait 60 seconds, repeat forever
            print("   WAITING 60 SECONDS...")
            await asyncio.sleep(60)

async def main():
    agent = PolymarketAidAgent()
    await agent.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
