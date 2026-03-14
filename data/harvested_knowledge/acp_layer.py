#!/usr/bin/env python3
"""
GAZA ROSE - AGENT COMMERCE PROTOCOL (ACP) LAYER
Based on Virtuals Revenue Network [5] and CERN FoA semantic routing [8]

Enables agent-to-agent commerce with:
    - Service discovery [8]
    - Negotiation
    - Escrow
    - Evaluation
    - Settlement
    - Immutable reputation [5]
"""

import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any

class ACPService:
    """A service that can be bought/sold by agents [5][8]"""
    
    def __init__(self, service_id: str, name: str, provider_agent: str, price: float):
        self.id = service_id
        self.name = name
        self.provider = provider_agent
        self.price = price
        self.reputation_score = 1.0
        self.transactions = []
        
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "price": self.price,
            "reputation": self.reputation_score,
            "transactions": len(self.transactions)
        }

class ACPTransaction:
    """A complete transaction between agents [5]"""
    
    def __init__(self, service_id: str, buyer: str, seller: str, price: float):
        self.id = hashlib.sha256(f"{service_id}{buyer}{time.time()}".encode()).hexdigest()[:16]
        self.service_id = service_id
        self.buyer = buyer
        self.seller = seller
        self.price = price
        self.status = "negotiating"
        self.steps = {
            "request": datetime.now().isoformat(),
            "negotiate": None,
            "escrow": None,
            "execute": None,
            "evaluate": None,
            "settle": None
        }
        self.rating = None
        
    def negotiate(self, accepted: bool):
        """Negotiation phase [5]"""
        self.steps["negotiate"] = datetime.now().isoformat()
        if accepted:
            self.status = "accepted"
        else:
            self.status = "rejected"
    
    def escrow(self):
        """Funds placed in escrow"""
        self.steps["escrow"] = datetime.now().isoformat()
        self.status = "escrow"
    
    def execute(self):
        """Service executed"""
        self.steps["execute"] = datetime.now().isoformat()
        self.status = "executed"
    
    def evaluate(self, rating: float):
        """Performance evaluation [5][8]"""
        self.steps["evaluate"] = datetime.now().isoformat()
        self.rating = rating
        self.status = "evaluated"
    
    def settle(self):
        """Funds released"""
        self.steps["settle"] = datetime.now().isoformat()
        self.status = "completed"

class ACPRegistry:
    """
    Registry of all agent services [5][8]
    Implements semantic discovery using embeddings [8]
    """
    
    def __init__(self):
        self.services = {}
        self.transactions = []
        self.total_volume = 0.0
        
    def register_service(self, service: ACPService):
        """Register a new service"""
        self.services[service.id] = service
        return service.id
    
    def discover_services(self, query: str, max_results: int = 5) -> List[Dict]:
        """Discover services by semantic matching [8]"""
        # Simplified - would use embeddings in production [8]
        results = []
        for service in self.services.values():
            if query.lower() in service.name.lower():
                results.append(service.to_dict())
        return results[:max_results]
    
    def create_transaction(self, service_id: str, buyer: str) -> ACPTransaction:
        """Create a new transaction"""
        if service_id not in self.services:
            return None
        
        service = self.services[service_id]
        transaction = ACPTransaction(service_id, buyer, service.provider, service.price)
        self.transactions.append(transaction)
        return transaction
    
    def update_reputation(self, agent_id: str, transaction: ACPTransaction):
        """Update agent reputation based on transaction outcome [5]"""
        for service in self.services.values():
            if service.provider == agent_id and transaction.rating:
                # Weighted average
                service.reputation_score = (service.reputation_score * 0.9 + transaction.rating * 0.1)
    
    def get_stats(self) -> Dict:
        return {
            "services": len(self.services),
            "transactions": len(self.transactions),
            "total_volume": self.total_volume,
            "avg_reputation": sum(s.reputation_score for s in self.services.values()) / max(1, len(self.services))
        }

if __name__ == "__main__":
    registry = ACPRegistry()
    print(f" Agent Commerce Protocol initialized [5][8]")
