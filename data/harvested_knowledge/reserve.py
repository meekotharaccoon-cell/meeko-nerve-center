"""
SPORE BANK - The immortal reserve.
20% of all profits. Never risked. Always growing.
Emergency fund for network survival.
"""

import json
from datetime import datetime
from typing import Dict

class SporeBank:
    """
    Constitutional reserve. Cannot be withdrawn without:
    1. Network collapse (all hyphae failed)
    2. 90 days of no profits
    3. Kimi + Spore (you) dual approval
    """
    
    def __init__(self, root):
        self.root = root
        self.reserves = 20.0  # Starting reserve from initial $100
        self.emergency_withdrawals = 0
        self.last_emergency = None
    
    def deposit(self, amount: float):
        """Add to immortal reserve."""
        self.reserves += amount
        self._log_transaction("deposit", amount)
    
    def emergency_withdrawal(self, reason: str, amount: float) -> Dict:
        """
        ONLY for network survival. Requires documentation.
        """
        if amount > self.reserves * 0.5:
            return {
                "approved": False,
                "reason": "Cannot withdraw >50% of reserves in one emergency"
            }
        
        if self.emergency_withdrawals >= 3:
            return {
                "approved": False,
                "reason": "Too many emergency withdrawals. Network deemed unstable."
            }
        
        self.reserves -= amount
        self.emergency_withdrawals += 1
        self.last_emergency = datetime.now().isoformat()
        
        self._log_transaction("emergency_withdrawal", amount, reason)
        
        return {
            "approved": True,
            "amount": amount,
            "remaining_reserves": self.reserves,
            "warning": "EMERGENCY PROTOCOL ACTIVATED - Review constitution"
        }
    
    def get_status(self) -> Dict:
        return {
            "reserves": self.reserves,
            "emergency_withdrawals_count": self.emergency_withdrawals,
            "last_emergency": self.last_emergency,
            "status": "HEALTHY" if self.reserves > 100 else "CRITICAL"
        }
    
    def _log_transaction(self, tx_type: str, amount: float, reason: str = None):
        log = {
            "timestamp": datetime.now().isoformat(),
            "type": tx_type,
            "amount": amount,
            "reason": reason,
            "reserves_after": self.reserves
        }
        
        with open("data/mycelium/spore_bank_ledger.jsonl", "a") as f:
            f.write(json.dumps(log) + "\n")
