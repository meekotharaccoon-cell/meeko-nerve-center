#!/usr/bin/env python3
"""
Momentum strategy - follow the trend.
"""
from .base import Strategy, MarketState, Action


class MomentumStrategy(Strategy):
    """Follow the trend based on velocity."""

    def __init__(self, threshold: float = 0.03):
        super().__init__("momentum")
        self.threshold = threshold

    def act(self, state: MarketState) -> Action:
        if state.near_expiry:
            return Action.HOLD
        velocity = state._velocity()
        if velocity > self.threshold:
            return Action.BUY
        elif velocity < -self.threshold:
            return Action.SELL
        return Action.HOLD
