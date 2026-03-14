#!/usr/bin/env python3
"""
Fade spike strategy - contrarian on extreme moves.
"""
from .base import Strategy, MarketState, Action


class FadeSpikeStrategy(Strategy):
    """Fade extreme moves (contrarian on spikes)."""

    def __init__(self, vel_thresh: float = 0.05, prob_thresh: float = 0.65):
        super().__init__("fade_spike")
        self.vel_thresh = vel_thresh
        self.prob_thresh = prob_thresh

    def act(self, state: MarketState) -> Action:
        if state.near_expiry:
            return Action.HOLD
        velocity = state._velocity()
        if velocity > self.vel_thresh and state.prob > self.prob_thresh:
            return Action.SELL
        elif velocity < -self.vel_thresh and state.prob < (1 - self.prob_thresh):
            return Action.BUY
        return Action.HOLD
