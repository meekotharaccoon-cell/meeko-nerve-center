import asyncio
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, time

from finance.data_engine import FreeDataEngine
from finance.strategies.core_strategies import StrategyEngine
from mycelium.constitution import RootSystem

@dataclass
class StockInsight:
    symbol: str
    price: float
    signal: str
    confidence: float
    market_session: str  # 'pre', 'regular', 'after'

class StockHypha:
    """
    Specialized node for stock markets.
    Respects market hours, focuses on momentum.
    """
    
    def __init__(self, hypha_id: str, capital: float, root: RootSystem):
        self.id = hypha_id
        self.capital = capital
        self.root = root
        self.engine = FreeDataEngine()
        self.strategies = StrategyEngine()
        
        # Multi-market watchlist (expandable to UK, EU, Asia)
        self.us_watchlist = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        self.uk_watchlist = []  # Expand when ready
        self.eu_watchlist = []  # Expand when ready
        
        self.positions = {}
        self.today_pnl = 0.0
        self.active = True
    
    def get_market_session(self) -> str:
        """Determine current market session."""
        now = datetime.now().time()
        et_now = now  # Simplified - assumes ET
        
        if time(4, 0) <= et_now < time(9, 30):
            return "pre"
        elif time(9, 30) <= et_now < time(16, 0):
            return "regular"
        elif time(16, 0) <= et_now < time(20, 0):
            return "after"
        return "closed"
    
    async def gather_nutrients(self) -> List[StockInsight]:
        """Scan stock markets (only when open)."""
        if not self.active:
            return []
        
        session = self.get_market_session()
        if session == "closed":
            return []  # Rest when markets closed
        
        insights = []
        
        for symbol in self.us_watchlist:
            data = await self.engine.get_stock_price(symbol)
            if not data:
                continue
            
            signals = await self.strategies.analyze(symbol, data.price, {
                "volume": data.volume
            })
            
            for signal in signals:
                if signal.confidence > 0.75:  # Higher threshold for stocks
                    insights.append(StockInsight(
                        symbol=symbol,
                        price=data.price,
                        signal=signal.action,
                        confidence=signal.confidence,
                        market_session=session
                    ))
        
        return insights
    
    async def execute_trade(self, insight: StockInsight) -> Dict:
        """Execute with stock-specific risk management."""
        # Stocks: more conservative position sizing
        trade_size = min(self.capital * 0.15, 30)  # 15% max, $30 max
        
        expected_profit = trade_size * 0.015  # 1.5% expected (conservative)
        
        if insight.signal == "sell":
            expected_profit = -trade_size * 0.005  # Small loss if wrong
        
        result = self.root.record_profit(self.id, expected_profit)
        
        self.today_pnl += expected_profit
        
        return {
            "executed": True,
            "symbol": insight.symbol,
            "session": insight.market_session,
            "size": trade_size,
            "expected_pnl": expected_profit,
            "network_distribution": result
        }
    
    def get_status(self) -> Dict:
        return {
            "hypha_id": self.id,
            "specialty": "stocks",
            "capital": self.capital,
            "today_pnl": self.today_pnl,
            "active": self.active,
            "current_session": self.get_market_session(),
            "watchlist_count": len(self.us_watchlist)
        }
