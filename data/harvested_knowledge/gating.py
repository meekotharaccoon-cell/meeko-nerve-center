#!/usr/bin/env python3
"""
Gating strategy - Mixture of Experts that routes to different strategies.
"""
import numpy as np
from typing import List, Dict
from .base import Strategy, MarketState, Action


class GatingStrategy(Strategy):
    """Routes to different expert strategies based on state."""

    def __init__(self, experts: List[Strategy], hidden_size: int = 32):
        super().__init__("gating")
        self.experts = experts
        self.n_experts = len(experts)

        # Gating network
        self.input_dim = 18  # Optimized for 15-min expiries
        self.w1 = np.random.randn(self.input_dim, hidden_size) * 0.1
        self.b1 = np.zeros(hidden_size)
        self.w2 = np.random.randn(hidden_size, self.n_experts) * 0.1
        self.b2 = np.zeros(self.n_experts)

    def _gate(self, x: np.ndarray) -> np.ndarray:
        """Compute expert weights."""
        h = np.tanh(x @ self.w1 + self.b1)
        logits = h @ self.w2 + self.b2
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / exp_logits.sum()

    def act(self, state: MarketState) -> Action:
        features = state.to_features()
        weights = self._gate(features)

        if self.training:
            # Sample expert
            expert_idx = np.random.choice(self.n_experts, p=weights)
        else:
            # Use highest weighted expert
            expert_idx = np.argmax(weights)

        return self.experts[expert_idx].act(state)

    def get_expert_weights(self, state: MarketState) -> Dict[str, float]:
        """Get current expert weights for debugging."""
        features = state.to_features()
        weights = self._gate(features)
        return {e.name: float(w) for e, w in zip(self.experts, weights)}
