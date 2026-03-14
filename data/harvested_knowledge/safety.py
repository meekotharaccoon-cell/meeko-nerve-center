import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class SafetyPolicy:
    name: str
    pattern: Optional[str]
    risk_level: RiskLevel
    action: str

class SystemSafety:
    HARD_CODED_PATTERNS = [
        (r"(?i)(password|secret|key|token)\s*[=:]\s*\S+", "credential_exposure", RiskLevel.CRITICAL),
        (r"(?i)(rm\s+-rf|del\s+/f|format\s+[a-z]:)", "destructive_command", RiskLevel.CRITICAL),
        (r"(?i)DROP\s+TABLE|DELETE\s+FROM.*WHERE\s+1\s*=\s*1", "database_destruction", RiskLevel.CRITICAL),
        (r"(?i)(import\s+os|subprocess|socket)\s*.*\b(system|exec|eval|compile)\b", "code_injection", RiskLevel.HIGH),
    ]
    
    def __init__(self):
        self.policies = []
        self.blocked_count = 0
        
        for pattern, name, risk in self.HARD_CODED_PATTERNS:
            self.policies.append(SafetyPolicy(
                name=name, pattern=pattern, risk_level=risk,
                action="block" if risk == RiskLevel.CRITICAL else "flag"
            ))
    
    def check(self, content: str, context: str = "unknown") -> Dict[str, Any]:
        violations = []
        max_risk = RiskLevel.NONE
        action = "allow"
        
        for policy in self.policies:
            if not policy.pattern:
                continue
            if re.findall(policy.pattern, content):
                violations.append({"policy": policy.name, "risk": policy.risk_level.name, "action": policy.action})
                if policy.risk_level.value > max_risk.value:
                    max_risk = policy.risk_level
                if policy.action == "block":
                    action = "block"
        
        if len(violations) >= 3:
            action = "block"
        
        if action == "block":
            self.blocked_count += 1
        
        return {
            "allowed": action != "block",
            "action": action,
            "max_risk": max_risk.name,
            "violations": violations,
            "risk_score": 1.0 - (max_risk.value / 4.0)
        }
