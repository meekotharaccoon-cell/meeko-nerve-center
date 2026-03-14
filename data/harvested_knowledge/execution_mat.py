import asyncio
from typing import Dict, List
from datetime import datetime

from mycelium.constitution import RootSystem
from mycelium.nodes.crypto_hypha import CryptoHypha
from mycelium.nodes.stock_hypha import StockHypha

class ExecutionMycelium:
    """
    The mat - connects all hyphae and enforces constitution.
    No trade happens without passing through here.
    """
    
    def __init__(self, root: RootSystem):
        self.root = root
        self.hyphae: Dict[str, object] = {}
        self.pending_trades = []
        self.executed_today = []
    
    async def spawn_hypha(self, specialty: str, capital: float) -> Dict:
        """
        Birth new node through constitutional approval.
        """
        hypha_id = f"{specialty}_{len(self.hyphae) + 1}"
        
        approval = self.root.register_hypha(hypha_id, specialty, capital)
        
        if not approval["approved"]:
            return approval
        
        # Instantiate based on specialty
        if specialty == "crypto":
            hypha = CryptoHypha(hypha_id, capital, self.root)
        elif specialty == "stock":
            hypha = StockHypha(hypha_id, capital, self.root)
        else:
            return {"approved": False, "reason": f"Unknown specialty: {specialty}"}
        
        self.hyphae[hypha_id] = hypha
        
        return {
            "approved": True,
            "hypha_id": hypha_id,
            "specialty": specialty,
            "capital_allocated": capital,
            "network_status": approval
        }
    
    async def run_nutrient_cycle(self):
        """
        One full cycle: all hyphae gather, best opportunities execute.
        """
        print(f"\n🍄 NUTRIENT CYCLE: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 50)
        
        all_insights = []
        
        # Gather from all hyphae
        for hypha_id, hypha in self.hyphae.items():
            if hasattr(hypha, 'gather_nutrients'):
                insights = await hypha.gather_nutrients()
                all_insights.extend([(hypha_id, i) for i in insights])
                print(f"  {hypha_id}: {len(insights)} insights")
        
        # Sort by confidence
        all_insights.sort(key=lambda x: x[1].confidence, reverse=True)
        
        # Execute top 3 (diversity across specialties)
        executed = 0
        for hypha_id, insight in all_insights[:5]:
            if executed >= 3:
                break
            
            hypha = self.hyphae[hypha_id]
            result = await hypha.execute_trade(insight)
            
            if result.get("executed"):
                print(f"  ✅ {hypha_id}: {insight.signal.upper()} {insight.symbol} @ {insight.price:.2f}")
                executed += 1
            elif result.get("circuit_breaker"):
                print(f"  🛑 CIRCUIT BREAKER: {result['reason']}")
                break
        
        # Log network status
        status = self.root.get_network_status()
        print(f"\n💰 Network: ${status['network_capital']:.2f} | Spore Bank: ${status['spore_bank']:.2f} | Hyphae: {status['total_hyphae']}")
        
        return status
    
    async def run_autonomous_cycles(self, interval_minutes: int = 30):
        """
        Continuous operation until constitution says stop.
        """
        print("🍄 MYCELIUM AUTONOMOUS MODE")
        print(f"   Cycle interval: {interval_minutes} minutes")
        print(f"   Spawning initial hyphae...")
        
        # Spawn initial network (Phase 1: $100)
        await self.spawn_hypha("crypto", 30)   # $30 to crypto
        await self.spawn_hypha("stock", 30)    # $30 to stocks
        # $40 remains in network reserve
        
        print(f"   Initial network spawned. 2 hyphae active.")
        print("   Press Ctrl+C to stop, or type 'status' for network health\n")
        
        try:
            while True:
                status = await self.run_nutrient_cycle()
                
                # Check if we can spawn new hypha (growth!)
                if status['can_spawn_new'] and status['network_capital'] > 50:
                    new_capital = min(20, status['network_capital'] * 0.2)
                    if len(self.hyphae) % 2 == 0:
                        await self.spawn_hypha("crypto", new_capital)
                    else:
                        await self.spawn_hypha("stock", new_capital)
                    print(f"   🌱 NEW HYPHA SPAWNED (auto-growth)")
                
                print(f"\n⏰ Next cycle in {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Mycelium entering dormancy...")
            self._generate_network_report()
    
    def _generate_network_report(self):
        """Final growth report."""
        import json
        from datetime import datetime
        
        status = self.root.get_network_status()
        report = {
            "timestamp": datetime.now().isoformat(),
            "final_network_capital": status['network_capital'],
            "spore_bank": status['spore_bank'],
            "total_hyphae": status['total_hyphae'],
            "hyphae_performance": {
                hid: h.get_status() for hid, h in self.hyphae.items()
            },
            "constitution": status['constitution']
        }
        
        with open(f"data/mycelium/final_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Final Report Saved")
        print(f"   Network grew from $100 to ${status['network_capital']:.2f}")
        print(f"   You earned: ${status['network_capital'] - 100:.2f} (50% of profits)")
        print(f"   Spore Bank: ${status['spore_bank']:.2f} (emergency reserve)")
