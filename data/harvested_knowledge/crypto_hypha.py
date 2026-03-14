import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from finance.data_engine import FreeDataEngine
from finance.strategies.core_strategies import StrategyEngine, Signal
from mycelium.constitution import RootSystem

@dataclass
class CryptoInsight:
    symbol: str
    price: float
    signal: str
    confidence: float
    strategy: str
    timestamp: datetime

class CryptoHypha:
    """
    Specialized node for cryptocurrency markets.
    24/7 operation, high volatility tolerance.
    """
    
    def __init__(self, hypha_id: str, capital: float, root: RootSystem):
        self.id = hypha_id
        self.capital = capital
        self.root = root
        self.engine = FreeDataEngine()
        self.strategies = StrategyEngine()
        
        self.watchlist = ["bitcoin", "ethereum", "solana", "cardano"]
        self.positions = {}
        self.today_pnl = 0.0
        self.lifetime_pnl = 0.0
        
        self.active = True
    
    async def gather_nutrients(self) -> List[CryptoInsight]:
        """
        Scan crypto markets for opportunities.
        """
        if not self.active:
            return []
        
        insights = []
        
        # Fetch market data
        for symbol in self.watchlist:
            data = await self.engine.get_crypto_price(symbol)
            if not data:
                continue
            
            # Generate signals
            signals = await self.strategies.analyze(symbol, data.price, {
                "volume": data.volume,
                "change_24h": data.change_24h
            })
            
            for signal in signals:
                if signal.confidence > 0.7:  # High confidence only
                    insights.append(CryptoInsight(
                        symbol=symbol.upper(),
                        price=data.price,
                        signal=signal.action,
                        confidence=signal.confidence,
                        strategy=signal.strategy.value,
                        timestamp=datetime.now()
                    ))
        
        return insights
    
    async def execute_trade(self, insight: CryptoInsight) -> Dict:
        """
        Attempt trade within constitutional limits.
        """
        trade_size = min(self.capital * 0.2, 50)  # 20% of hypha capital, max $50
        
        # Check with root system
        can_trade = self.root.hyphae_registry[self.id].get("can_trade", True)
        if not can_trade:
            return {"executed": False, "reason": "Trading halted by constitution"}
        
        # Simulate/paper trade
        expected_profit = trade_size * 0.02 if insight.signal == "buy" else -trade_size * 0.01
        
        # Record with root
        if expected_profit > 0:
            result = self.root.record_profit(self.id, expected_profit)
        else:
            result = self.root.record_loss(self.id, abs(expected_profit))
            if result.get("circuit_breaker"):
                self.active = False
                return {"executed": False, "circuit_breaker": True, "reason": result["reason"]}
        
        self.today_pnl += expected_profit
        self.lifetime_pnl += expected_profit
        
        return {
            "executed": True,
            "symbol": insight.symbol,
            "action": insight.signal,
            "size": trade_size,
            "expected_pnl": expected_profit,
            "network_status": result
        }
    
    def get_status(self) -> Dict:
        return {
            "hypha_id": self.id,
            "specialty": "cryptocurrency",
            "capital": self.capital,
            "today_pnl": self.today_pnl,
            "lifetime_pnl": self.lifetime_pnl,
            "active": self.active,
            "watchlist": self.watchlist
        }
