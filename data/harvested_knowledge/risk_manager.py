import os
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RiskProfile:
    max_daily_loss_percent: float
    max_position_size_percent: float
    max_open_positions: int
    stop_loss_percent: float
    take_profit_percent: float
    paper_trading: bool

class RiskManager:
    """
    The 'Set it and forget it' safety system.
    HARD STOPS that cannot be overridden by the agent.
    """
    
    def __init__(self):
        self.profile = self._load_profile()
        self.daily_pnl = 0.0
        self.open_positions = 0
        self.trades_today = 0
        self.last_reset = datetime.now().date()
        
        # EMERGENCY BRAKES - These are absolute
        self.circuit_breaker_triggered = False
        self.daily_loss_limit_hit = False
    
    def _load_profile(self) -> RiskProfile:
        """Load risk settings from environment."""
        return RiskProfile(
            max_daily_loss_percent=float(os.getenv("MAX_DAILY_LOSS_PERCENT", "2.0")),
            max_position_size_percent=float(os.getenv("MAX_POSITION_SIZE_PERCENT", "10.0")),
            max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "5")),
            stop_loss_percent=float(os.getenv("STOP_LOSS_PERCENT", "5.0")),
            take_profit_percent=float(os.getenv("TAKE_PROFIT_PERCENT", "10.0")),
            paper_trading=os.getenv("PAPER_TRADING_CRYPTO", "true").lower() == "true"
        )
    
    def check_trade_allowed(self, trade_size: float, portfolio_value: float) -> Dict[str, Any]:
        """
        Check if trade is allowed. Returns decision + reason.
        CANNOT be overridden by agent.
        """
        self._reset_daily_if_needed()
        
        # Circuit breaker check
        if self.circuit_breaker_triggered:
            return {
                "allowed": False,
                "reason": "CIRCUIT BREAKER ACTIVE - Manual reset required",
                "action": "HALT"
            }
        
        # Daily loss limit check
        if self.daily_loss_limit_hit:
            return {
                "allowed": False,
                "reason": f"DAILY LOSS LIMIT HIT: {self.profile.max_daily_loss_percent}%",
                "action": "HALT_TRADING_FOR_DAY"
            }
        
        # Position size check
        position_percent = (trade_size / portfolio_value) * 100 if portfolio_value > 0 else 0
        if position_percent > self.profile.max_position_size_percent:
            return {
                "allowed": False,
                "reason": f"Position size {position_percent:.2f}% exceeds limit {self.profile.max_position_size_percent}%",
                "action": "REDUCE_SIZE"
            }
        
        # Max positions check
        if self.open_positions >= self.profile.max_open_positions:
            return {
                "allowed": False,
                "reason": f"Max open positions ({self.profile.max_open_positions}) reached",
                "action": "CLOSE_POSITION_FIRST"
            }
        
        return {
            "allowed": True,
            "reason": "All checks passed",
            "paper_mode": self.profile.paper_trading
        }
    
    def record_trade_result(self, pnl: float):
        """Record profit/loss and check limits."""
        self.daily_pnl += pnl
        self.trades_today += 1
        
        # Check daily loss limit
        if self.daily_pnl < -(self.profile.max_daily_loss_percent):
            self.daily_loss_limit_hit = True
            self._trigger_alert(f"DAILY LOSS LIMIT HIT: {self.daily_pnl:.2f}%")
    
    def _reset_daily_if_needed(self):
        """Reset daily counters at midnight."""
        if datetime.now().date() != self.last_reset:
            self.daily_pnl = 0.0
            self.trades_today = 0
            self.daily_loss_limit_hit = False
            self.last_reset = datetime.now().date()
    
    def _trigger_alert(self, message: str):
        """Send alert (email/SMS) when limits hit."""
        print(f"🚨 RISK ALERT: {message}")
        # TODO: Implement actual notifications when APIs added
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "daily_pnl_percent": self.daily_pnl,
            "daily_loss_limit": self.profile.max_daily_loss_percent,
            "limit_hit": self.daily_loss_limit_hit,
            "open_positions": self.open_positions,
            "max_positions": self.profile.max_open_positions,
            "paper_trading": self.profile.paper_trading,
            "circuit_breaker": self.circuit_breaker_triggered
        }
    
    def manual_reset(self):
        """YOU manually reset after reviewing situation."""
        self.circuit_breaker_triggered = False
        self.daily_loss_limit_hit = False
        self.daily_pnl = 0.0
        print("✅ Risk manager manually reset")
