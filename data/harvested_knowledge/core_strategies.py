import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class StrategyType(Enum):
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    ARBITRAGE = "arbitrage"
    TREND_FOLLOWING = "trend_following"

@dataclass
class Signal:
    symbol: str
    strategy: StrategyType
    action: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0.0 to 1.0
    expected_return: float
    stop_loss: float
    take_profit: float
    timestamp: datetime

class StrategyEngine:
    """
    Multiple trading strategies that generate signals.
    Risk manager decides which signals to execute.
    """
    
    def __init__(self):
        self.strategies = {
            StrategyType.MEAN_REVERSION: self._mean_reversion,
            StrategyType.MOMENTUM: self._momentum,
            StrategyType.TREND_FOLLOWING: self._trend_following
        }
        self.price_history: Dict[str, List[float]] = {}
    
    async def analyze(self, symbol: str, current_price: float, market_data: Dict) -> List[Signal]:
        """
        Run all strategies on an asset, return signals.
        """
        # Update price history
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(current_price)
        
        # Keep last 100 prices
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
        
        signals = []
        
        for strategy_type, strategy_func in self.strategies.items():
            signal = await strategy_func(symbol, current_price, market_data)
            if signal:
                signals.append(signal)
        
        return signals
    
    async def _mean_reversion(self, symbol: str, price: float, data: Dict) -> Optional[Signal]:
        """
        Buy when price below average, sell when above.
        """
        if len(self.price_history.get(symbol, [])) < 20:
            return None
        
        prices = self.price_history[symbol]
        avg_price = sum(prices[-20:]) / 20
        
        deviation = (price - avg_price) / avg_price
        
        if deviation < -0.02:  # 2% below average
            return Signal(
                symbol=symbol,
                strategy=StrategyType.MEAN_REVERSION,
                action="buy",
                confidence=min(abs(deviation) * 10, 0.9),
                expected_return=0.02,
                stop_loss=price * 0.95,
                take_profit=avg_price,
                timestamp=datetime.now()
            )
        elif deviation > 0.02:  # 2% above average
            return Signal(
                symbol=symbol,
                strategy=StrategyType.MEAN_REVERSION,
                action="sell",
                confidence=min(abs(deviation) * 10, 0.9),
                expected_return=0.02,
                stop_loss=price * 1.05,
                take_profit=avg_price,
                timestamp=datetime.now()
            )
        
        return None
    
    async def _momentum(self, symbol: str, price: float, data: Dict) -> Optional[Signal]:
        """
        Buy when price going up, sell when going down.
        """
        if len(self.price_history.get(symbol, [])) < 10:
            return None
        
        prices = self.price_history[symbol]
        recent_change = (price - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        
        if recent_change > 0.01:  # 1% up in last 5 periods
            return Signal(
                symbol=symbol,
                strategy=StrategyType.MOMENTUM,
                action="buy",
                confidence=min(recent_change * 50, 0.85),
                expected_return=recent_change * 2,
                stop_loss=price * 0.97,
                take_profit=price * 1.05,
                timestamp=datetime.now()
            )
        elif recent_change < -0.01:
            return Signal(
                symbol=symbol,
                strategy=StrategyType.MOMENTUM,
                action="sell",
                confidence=min(abs(recent_change) * 50, 0.85),
                expected_return=abs(recent_change) * 2,
                stop_loss=price * 1.03,
                take_profit=price * 0.95,
                timestamp=datetime.now()
            )
        
        return None
    
    async def _trend_following(self, symbol: str, price: float, data: Dict) -> Optional[Signal]:
        """
        Follow established trends.
        """
        # Simplified trend detection
        if len(self.price_history.get(symbol, [])) < 50:
            return None
        
        prices = self.price_history[symbol]
        short_avg = sum(prices[-10:]) / 10
        long_avg = sum(prices[-50:]) / 50
        
        if short_avg > long_avg * 1.01:  # Short above long = uptrend
            return Signal(
                symbol=symbol,
                strategy=StrategyType.TREND_FOLLOWING,
                action="buy",
                confidence=0.7,
                expected_return=0.05,
                stop_loss=long_avg * 0.98,
                take_profit=price * 1.10,
                timestamp=datetime.now()
            )
        elif short_avg < long_avg * 0.99:
            return Signal(
                symbol=symbol,
                strategy=StrategyType.TREND_FOLLOWING,
                action="sell",
                confidence=0.7,
                expected_return=0.05,
                stop_loss=long_avg * 1.02,
                take_profit=price * 0.90,
                timestamp=datetime.now()
            )
        
        return None
