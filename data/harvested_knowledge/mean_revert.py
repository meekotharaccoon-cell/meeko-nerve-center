#!/usr/bin/env python3
"""
Mean reversion strategy - buy low, sell high.
"""
from .base import Strategy, MarketState, Action


class MeanRevertStrategy(Strategy):
    """Buy when prob < threshold, sell when prob > threshold."""

    def __init__(self, buy_thresh: float = 0.40, sell_thresh: float = 0.60):
        super().__init__("mean_revert")
        self.buy_thresh = buy_thresh
        self.sell_thresh = sell_thresh

    def act(self, state: MarketState) -> Action:
        if state.near_expiry:
            return Action.HOLD
        if state.prob < self.buy_thresh:
            return Action.BUY
        elif state.prob > self.sell_thresh:
            return Action.SELL
        return Action.HOLD
