import os
import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

from core.agent import AIChatbot
from finance.data_engine import FreeDataEngine
from finance.risk_manager import RiskManager
from finance.strategies.core_strategies import StrategyEngine, Signal

load_dotenv()

class FinancialSuperAgent:
    """
    The 'Set it and forget it' financial agent.
    Runs autonomously within YOUR risk limits.
    """
    
    def __init__(self):
        self.chat_agent = AIChatbot(
            agent_id="financial_assistant",
            system_prompt="You are a financial analysis AI. Provide market insights and explain trading decisions."
        )
        
        self.data_engine = FreeDataEngine()
        self.risk_manager = RiskManager()
        self.strategy_engine = StrategyEngine()
        
        # Portfolio tracking (paper trading mode default)
        self.portfolio = {
            "cash": 100000.0,  # Starting paper money
            "positions": {},   # symbol -> {quantity, entry_price}
            "history": []
        }
        
        # Watchlists
        self.crypto_watchlist = ["bitcoin", "ethereum", "solana"]
        self.stock_watchlist = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        
        self.running = False
    
    async def run_analysis_cycle(self):
        """
        One full analysis cycle:
        1. Fetch market data
        2. Generate signals
        3. Check risk limits
        4. Execute paper trades
        5. Log everything
        """
        print(f"\n🔍 Analysis Cycle: {datetime.now().strftime('%H:%M:%S')}")
        
        # Fetch data
        assets = await self.data_engine.get_multiple_assets(
            self.crypto_watchlist,
            self.stock_watchlist
        )
        
        all_signals = []
        
        for symbol, data in assets.items():
            print(f"  📊 {symbol}: ${data.price:.2f} ({data.change_24h:+.2f}%)")
            
            # Generate signals
            signals = await self.strategy_engine.analyze(
                symbol, data.price, {"volume": data.volume}
            )
            all_signals.extend(signals)
        
        # Sort by confidence
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # Execute top signals within risk limits
        for signal in all_signals[:3]:  # Top 3 only
            await self._evaluate_signal(signal)
        
        # Log status
        self._log_status()
    
    async def _evaluate_signal(self, signal: Signal):
        """Check signal against risk manager before executing."""
        print(f"\n🎯 Signal: {signal.action.upper()} {signal.symbol}")
        print(f"   Strategy: {signal.strategy.value}")
        print(f"   Confidence: {signal.confidence:.2%}")
        print(f"   Expected Return: {signal.expected_return:.2%}")
        
        # Check with risk manager
        portfolio_value = self._calculate_portfolio_value()
        trade_size = portfolio_value * 0.1  # 10% of portfolio per trade
        
        risk_check = self.risk_manager.check_trade_allowed(trade_size, portfolio_value)
        
        if not risk_check["allowed"]:
            print(f"   🛡️ BLOCKED: {risk_check['reason']}")
            return
        
        # Execute paper trade
        await self._execute_paper_trade(signal, trade_size)
    
    async def _execute_paper_trade(self, signal: Signal, size: float):
        """Execute paper trade (simulated, no real money)."""
        is_paper = self.risk_manager.profile.paper_trading
        
        mode = "PAPER" if is_paper else "LIVE"
        print(f"   💸 Executing {mode} trade: {signal.action} ${size:.2f} of {signal.symbol}")
        
        # Simulate execution
        trade_record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": signal.symbol,
            "action": signal.action,
            "size": size,
            "entry_price": 0,  # Would be filled price
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "paper": is_paper,
            "strategy": signal.strategy.value
        }
        
        self.portfolio["history"].append(trade_record)
        
        # Update positions (simplified)
        if signal.action == "buy":
            self.portfolio["cash"] -= size
            self.portfolio["positions"][signal.symbol] = {
                "quantity": size / 100,  # Simplified
                "entry": 100.0
            }
        elif signal.action == "sell" and signal.symbol in self.portfolio["positions"]:
            del self.portfolio["positions"][signal.symbol]
            self.portfolio["cash"] += size * 1.02  # Assume 2% profit for demo
        
        print(f"   ✅ Trade recorded. Cash remaining: ${self.portfolio['cash']:.2f}")
    
    def _calculate_portfolio_value(self) -> float:
        """Calculate total portfolio value."""
        positions_value = sum(
            pos["quantity"] * pos["entry"] 
            for pos in self.portfolio["positions"].values()
        )
        return self.portfolio["cash"] + positions_value
    
    def _log_status(self):
        """Log current status."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "portfolio_value": self._calculate_portfolio_value(),
            "cash": self.portfolio["cash"],
            "positions": len(self.portfolio["positions"]),
            "risk_status": self.risk_manager.get_status()
        }
        
        print(f"\n💼 Portfolio Value: ${status['portfolio_value']:.2f}")
        print(f"   Cash: ${status['cash']:.2f}")
        print(f"   Positions: {status['positions']}")
        print(f"   Daily P&L: {status['risk_status']['daily_pnl_percent']:.2f}%")
        
        # Save to file
        with open("data/performance/status.json", "w") as f:
            json.dump(status, f, indent=2)
    
    async def chat(self, message: str) -> str:
        """Talk to the financial assistant."""
        result = await self.chat_agent.process(message)
        return result["response"] if result["success"] else "Error processing request"
    
    async def run_autonomous_mode(self, interval_minutes: int = 60):
        """
        'Set it and forget it' mode.
        Runs analysis every X minutes automatically.
        """
        print("🤖 AUTONOMOUS MODE ACTIVATED")
        print(f"   Analyzing every {interval_minutes} minutes")
        print(f"   Risk limits: {self.risk_manager.profile.max_daily_loss_percent}% daily loss max")
        print(f"   Paper trading: {self.risk_manager.profile.paper_trading}")
        print("   Press Ctrl+C to stop\n")
        
        self.running = True
        
        try:
            while self.running:
                await self.run_analysis_cycle()
                print(f"\n⏰ Next analysis in {interval_minutes} minutes...")
                print("   (Ctrl+C to stop, or type 'status' in another window)")
                await asyncio.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n\n🛑 Autonomous mode stopped")
            self._generate_report()
    
    def _generate_report(self):
        """Generate daily performance report."""
        report = {
            "date": datetime.now().isoformat(),
            "trades": len(self.portfolio["history"]),
            "final_value": self._calculate_portfolio_value(),
            "return_pct": ((self._calculate_portfolio_value() / 100000) - 1) * 100
        }
        
        with open(f"data/performance/report_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📈 Daily Report:")
        print(f"   Trades: {report['trades']}")
        print(f"   Return: {report['return_pct']:+.2f}%")
        print(f"   Report saved to data/performance/")
