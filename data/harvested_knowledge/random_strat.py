#!/usr/bin/env python3
"""
Random baseline strategy.
"""
import numpy as np
from .base import Strategy, MarketState, Action


class RandomStrategy(Strategy):
    """Random baseline - for verifying pipeline works."""

    def __init__(self):
        super().__init__("random")

    def act(self, state: MarketState) -> Action:
        if state.near_expiry:
            return Action.HOLD
        return np.random.choice([Action.HOLD, Action.BUY, Action.SELL])
