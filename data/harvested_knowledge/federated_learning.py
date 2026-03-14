"""
FEDERATED LEARNING FOR AGENT SWARMS
Based on Monash University research [citation:3]

Key findings:
    • Federated learning: best scalability (55.6% drop vs 75.7% centralized)
    • 88.6% transferability (vs 64.9% centralized)
    • Strong middle ground between speed and scalability
"""

import numpy as np
import random
from typing import Dict, List, Any, Optional
from collections import defaultdict

class FederatedLearningLayer:
    """
    Federated reinforcement learning for agent swarms [citation:3]
    Each agent trains locally, shares only model updates
    """
    
    def __init__(self):
        self.local_models = {}  # Agent ID -> model weights
        self.global_model = None
        self.training_history = []
        self.aggregation_round = 0
        
    def initialize_agent(self, agent_id: str, initial_weights: Dict):
        """Initialize local model for an agent"""
        self.local_models[agent_id] = {
            "weights": initial_weights,
            "training_steps": 0,
            "avg_loss": 0,
            "performance": 0
        }
    
    def local_training_step(self, agent_id: str, batch: List, learning_rate: float = 0.01):
        """
        Local training on agent's private data [citation:3]
        """
        if agent_id not in self.local_models:
            return None
        
        model = self.local_models[agent_id]
        
        # Simulate training step
        # In real implementation, this would be actual gradient descent
        loss_reduction = random.uniform(0.01, 0.1)
        model["avg_loss"] = model["avg_loss"] * 0.9 + loss_reduction * 0.1
        model["training_steps"] += 1
        
        # Simulate performance improvement
        model["performance"] = min(1.0, model["performance"] + 0.01)
        
        return {
            "agent_id": agent_id,
            "loss": loss_reduction,
            "steps": model["training_steps"],
            "performance": model["performance"]
        }
    
    def aggregate_models(self, sample_ratio: float = 0.3):
        """
        Federated aggregation: average selected agent models [citation:3]
        """
        self.aggregation_round += 1
        
        # Select random subset of agents
        agent_ids = list(self.local_models.keys())
        sample_size = max(1, int(len(agent_ids) * sample_ratio))
        selected = random.sample(agent_ids, min(sample_size, len(agent_ids)))
        
        if not selected:
            return None
        
        # Federated averaging
        aggregated_weights = defaultdict(float)
        for agent_id in selected:
            model = self.local_models[agent_id]
            for key, value in model["weights"].items():
                aggregated_weights[key] += value / len(selected)
        
        # Update global model
        self.global_model = dict(aggregated_weights)
        
        # Distribute to all agents (selectively, not all need update)
        for agent_id in agent_ids:
            if random.random() < 0.5:  # 50% get global update
                self.local_models[agent_id]["weights"] = self.global_model.copy()
        
        return {
            "round": self.aggregation_round,
            "agents_sampled": len(selected),
            "total_agents": len(agent_ids)
        }
    
    def get_scalability_metrics(self) -> Dict:
        """
        Return scalability metrics based on research [citation:3]
        """
        return {
            "scalability_drop": 0.556,  # 55.6% drop (best of all methods)
            "transferability": 0.886,     # 88.6% transferability
            "convergence_epochs": 1950,   # 1,950 ± 89 epochs
            "final_reward": 25.48,        # Comparable to centralized
            "sample_efficiency": "medium"  # Middle ground
        }
    
    def get_agent_performance(self, agent_id: str) -> Dict:
        """Get performance metrics for an agent"""
        if agent_id in self.local_models:
            model = self.local_models[agent_id]
            return {
                "performance": model["performance"],
                "training_steps": model["training_steps"],
                "avg_loss": model["avg_loss"]
            }
        return {}
    
    def should_federate(self) -> bool:
        """Determine if federated aggregation should occur"""
        # Federate every 10 training steps on average
        total_steps = sum(m["training_steps"] for m in self.local_models.values())
        return total_steps > self.aggregation_round * 100
