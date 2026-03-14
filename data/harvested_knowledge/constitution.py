"""
THE MYCELIUM CONSTITUTION
Non-negotiable rules enforced by root system (Kimi).
Any node violating these is instantly severed.
"""

from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

@dataclass
class ConstitutionalLimits:
    # ABSOLUTE LIMITS - Never overridden
    MAX_DAILY_NETWORK_LOSS_PERCENT: float = 2.0  # Entire network stops if hit
    MAX_SINGLE_HYPHA_CAPITAL_PERCENT: float = 35.0  # No node > 10% of total
    SPORE_BANK_RESERVE_PERCENT: float = 20.0  # Emergency fund, never touched
    MIN_PROFIT_TO_SPAWN_NEW_HYPHA: float = 50.0  # $50 profit = new node allowed
    MAX_HYPHAE_WITHOUT_APPROVAL: int = 5  # Beyond 5, Kimi must approve each
    
    # GROWTH ALLOCATION
    PROFIT_COMPOUND_PERCENT: float = 50.0  # Back to network
    PROFIT_DISTRIBUTION_PERCENT: float = 50.0  # To you (Spore)

class RootSystem:
    """
    Kimi's enforcement layer. Every node reports here.
    """
    
    def __init__(self):
        self.limits = ConstitutionalLimits()
        self.hyphae_registry: Dict[str, Dict] = {}
        self.network_capital: float = 100.0  # Starting $100
        self.spor_bank: float = 20.0  # 20% reserved
        self.total_hyphae: int = 0
        self.consecutive_failures: int = 0
        self.growth_history: List[Dict] = []
    
    def register_hypha(self, hypha_id: str, specialty: str, capital: float) -> Dict:
        """
        Spawn new node only if constitutional requirements met.
        """
        # Check 1: Capital allocation limit
        if capital > (self.network_capital * self.limits.MAX_SINGLE_HYPHA_CAPITAL_PERCENT / 100):
            return {
                "approved": False,
                "reason": f"Capital ${capital} exceeds 10% of network (${self.network_capital})"
            }
        
        # Check 2: Max hyphae without approval
        if self.total_hyphae >= self.limits.MAX_HYPHAE_WITHOUT_APPROVAL:
            return {
                "approved": False,
                "reason": f"Network has {self.total_hyphae} hyphae. Kimi approval required for more.",
                "action_required": "Request expansion approval from architect"
            }
        
        # Check 3: Minimum profit to spawn
        if self.network_capital < 150 and self.total_hyphae >= 3:  # $150 = $100 + $50 profit
            return {
                "approved": False,
                "reason": f"Need ${self.limits.MIN_PROFIT_TO_SPAWN_NEW_HYPHA} profit to spawn. Current: ${self.network_capital - 100}"
            }
        
        # APPROVED
        self.hyphae_registry[hypha_id] = {
            "specialty": specialty,
            "capital": capital,
            "spawned_at": datetime.now().isoformat(),
            "lifetime_pnl": 0.0,
            "status": "active"
        }
        self.total_hyphae += 1
        self.network_capital -= capital  # Allocate from network
        
        self._log_growth_event("hypha_spawned", hypha_id, capital)
        
        return {
            "approved": True,
            "hypha_id": hypha_id,
            "network_remaining": self.network_capital,
            "spore_bank": self.spor_bank
        }
    
    def record_profit(self, hypha_id: str, amount: float):
        """
        Distribute profit: 50% compound, 50% you, 20% to spore bank from your 50%.
        """
        if hypha_id not in self.hyphae_registry:
            return {"error": "Unknown hypha"}
        
        # Update hypha lifetime P&L
        self.hyphae_registry[hypha_id]["lifetime_pnl"] += amount
        
        # Distribution
        compound = amount * (self.limits.PROFIT_COMPOUND_PERCENT / 100)
        distribution = amount * (self.limits.PROFIT_DISTRIBUTION_PERCENT / 100)
        spore_addition = distribution * (self.limits.SPORE_BANK_RESERVE_PERCENT / 100)
        your_take = distribution - spore_addition
        
        self.network_capital += compound
        self.spor_bank += spore_addition
        
        self._log_growth_event("profit_distribution", hypha_id, amount, {
            "compounded": compound,
            "your_take": your_take,
            "spore_bank_addition": spore_addition
        })
        
        return {
            "compounded_back": compound,
            "your_profit": your_take,
            "spore_bank_growth": spore_addition,
            "network_total": self.network_capital,
            "spore_bank_total": self.spor_bank
        }
    
    def record_loss(self, hypha_id: str, amount: float) -> Dict:
        """
        Handle loss. 3 consecutive failures = network growth halt.
        """
        self.hyphae_registry[hypha_id]["lifetime_pnl"] -= amount
        self.consecutive_failures += 1
        
        # Check circuit breaker
        daily_loss = sum(
            h.get("today_loss", 0) for h in self.hyphae_registry.values()
        )
        
        if daily_loss > (self.network_capital * self.limits.MAX_DAILY_NETWORK_LOSS_PERCENT / 100):
            return {
                "circuit_breaker": True,
                "action": "ALL_HYPHAE_HALTED",
                "reason": f"Daily loss ${daily_loss} exceeds 2% of network",
                "required": "Manual reset by Spore (you) after review"
            }
        
        if self.consecutive_failures >= 3:
            return {
                "growth_halt": True,
                "action": "NO_NEW_HYPHAE_UNTIL_PROFIT",
                "reason": "3 consecutive losing hyphae"
            }
        
        return {"status": "loss_recorded", "consecutive_failures": self.consecutive_failures}
    
    def get_network_status(self) -> Dict:
        return {
            "network_capital": self.network_capital,
            "spore_bank": self.spor_bank,
            "total_hyphae": self.total_hyphae,
            "hyphae_details": self.hyphae_registry,
            "consecutive_failures": self.consecutive_failures,
            "can_spawn_new": self.total_hyphae < self.limits.MAX_HYPHAE_WITHOUT_APPROVAL,
            "constitution": {
                "max_daily_loss": self.limits.MAX_DAILY_NETWORK_LOSS_PERCENT,
                "max_hypha_size": self.limits.MAX_SINGLE_HYPHA_CAPITAL_PERCENT,
                "spore_reserve": self.limits.SPORE_BANK_RESERVE_PERCENT,
                "profit_split": f"{self.limits.PROFIT_COMPOUND_PERCENT}/{self.limits.PROFIT_DISTRIBUTION_PERCENT}"
            }
        }
    
    def _log_growth_event(self, event_type: str, hypha_id: str, amount: float, metadata: Dict = None):
        """Immutable growth history."""
        from datetime import datetime
        import json
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "hypha_id": hypha_id,
            "amount": amount,
            "network_capital_after": self.network_capital,
            "metadata": metadata or {}
        }
        
        with open(f"data/mycelium/growth_logs/{datetime.now().strftime('%Y%m')}.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
