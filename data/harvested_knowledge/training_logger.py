"""
Training logger for RL experiments.
Logs trades, PPO updates, and episode summaries to CSV files.
"""
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class TradeRecord:
    """Single trade record."""
    timestamp: str
    asset: str
    action: str  # BUY, SELL, HOLD
    side: str  # UP, DOWN
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    duration_sec: float
    time_remaining: float  # When trade was opened
    prob_at_entry: float
    prob_at_exit: float
    binance_change: float  # Underlying price change during trade


@dataclass
class UpdateRecord:
    """PPO update record."""
    timestamp: str
    update_num: int
    policy_loss: float
    value_loss: float
    entropy: float
    approx_kl: float
    clip_fraction: float
    explained_variance: float
    buffer_avg_reward: float
    buffer_win_rate: float  # % of positive rewards in buffer
    cumulative_pnl: float
    cumulative_trades: int
    cumulative_win_rate: float


@dataclass
class EpisodeRecord:
    """Market episode (15-min window) summary."""
    timestamp: str
    asset: str
    condition_id: str
    outcome: str  # WIN, LOSS, NO_TRADE
    trades_taken: int
    episode_pnl: float
    final_prob: float
    binance_change: float
    total_exposure_time: float  # % of episode with position


class TrainingLogger:
    """Log training data to CSV files."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        # Session ID for this run
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # File paths
        self.trades_file = os.path.join(log_dir, f"trades_{self.session_id}.csv")
        self.updates_file = os.path.join(log_dir, f"updates_{self.session_id}.csv")
        self.episodes_file = os.path.join(log_dir, f"episodes_{self.session_id}.csv")

        # Buffers
        self.trades: List[TradeRecord] = []
        self.updates: List[UpdateRecord] = []
        self.episodes: List[EpisodeRecord] = []

        # Per-episode tracking
        self.episode_trades: Dict[str, List[TradeRecord]] = {}
        self.episode_start_times: Dict[str, datetime] = {}

        # Counters
        self.update_count = 0

        # Write headers
        self._write_headers()

        print(f"  [LOG] Session: {self.session_id}")
        print(f"  [LOG] Trades:  {self.trades_file}")
        print(f"  [LOG] Updates: {self.updates_file}")

    def _write_headers(self):
        """Write CSV headers."""
        # Trades
        with open(self.trades_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'asset', 'action', 'side', 'entry_price', 'exit_price',
                'size', 'pnl', 'duration_sec', 'time_remaining', 'prob_at_entry',
                'prob_at_exit', 'binance_change'
            ])
            writer.writeheader()

        # Updates
        with open(self.updates_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'update_num', 'policy_loss', 'value_loss', 'entropy',
                'approx_kl', 'clip_fraction', 'explained_variance', 'buffer_avg_reward',
                'buffer_win_rate', 'cumulative_pnl', 'cumulative_trades', 'cumulative_win_rate'
            ])
            writer.writeheader()

        # Episodes
        with open(self.episodes_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'asset', 'condition_id', 'outcome', 'trades_taken',
                'episode_pnl', 'final_prob', 'binance_change', 'total_exposure_time'
            ])
            writer.writeheader()

    def log_trade(
        self,
        asset: str,
        action: str,
        side: str,
        entry_price: float,
        exit_price: float,
        size: float,
        pnl: float,
        duration_sec: float,
        time_remaining: float,
        prob_at_entry: float,
        prob_at_exit: float,
        binance_change: float = 0.0,
        condition_id: str = None
    ):
        """Log a completed trade."""
        record = TradeRecord(
            timestamp=datetime.now().isoformat(),
            asset=asset,
            action=action,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            size=size,
            pnl=pnl,
            duration_sec=duration_sec,
            time_remaining=time_remaining,
            prob_at_entry=prob_at_entry,
            prob_at_exit=prob_at_exit,
            binance_change=binance_change
        )

        self.trades.append(record)

        # Track per-episode
        if condition_id:
            if condition_id not in self.episode_trades:
                self.episode_trades[condition_id] = []
            self.episode_trades[condition_id].append(record)

        # Append to CSV
        with open(self.trades_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(record).keys()))
            writer.writerow(asdict(record))

    def log_update(
        self,
        metrics: Dict[str, float],
        buffer_rewards: List[float],
        cumulative_pnl: float,
        cumulative_trades: int,
        cumulative_wins: int
    ):
        """Log a PPO update."""
        self.update_count += 1

        # Compute buffer stats
        avg_reward = sum(buffer_rewards) / len(buffer_rewards) if buffer_rewards else 0
        win_rate = sum(1 for r in buffer_rewards if r > 0) / len(buffer_rewards) if buffer_rewards else 0
        cum_win_rate = cumulative_wins / cumulative_trades if cumulative_trades > 0 else 0

        record = UpdateRecord(
            timestamp=datetime.now().isoformat(),
            update_num=self.update_count,
            policy_loss=metrics.get('policy_loss', 0),
            value_loss=metrics.get('value_loss', 0),
            entropy=metrics.get('entropy', 0),
            approx_kl=metrics.get('approx_kl', 0),
            clip_fraction=metrics.get('clip_fraction', 0),
            explained_variance=metrics.get('explained_variance', 0),
            buffer_avg_reward=avg_reward,
            buffer_win_rate=win_rate,
            cumulative_pnl=cumulative_pnl,
            cumulative_trades=cumulative_trades,
            cumulative_win_rate=cum_win_rate
        )

        self.updates.append(record)

        # Append to CSV
        with open(self.updates_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(record).keys()))
            writer.writerow(asdict(record))

    def log_episode(
        self,
        asset: str,
        condition_id: str,
        outcome: str,
        final_prob: float,
        binance_change: float = 0.0,
        total_exposure_time: float = 0.0
    ):
        """Log a market episode completion."""
        trades = self.episode_trades.get(condition_id, [])
        episode_pnl = sum(t.pnl for t in trades)

        record = EpisodeRecord(
            timestamp=datetime.now().isoformat(),
            asset=asset,
            condition_id=condition_id[:8],  # Truncate for readability
            outcome=outcome,
            trades_taken=len(trades),
            episode_pnl=episode_pnl,
            final_prob=final_prob,
            binance_change=binance_change,
            total_exposure_time=total_exposure_time
        )

        self.episodes.append(record)

        # Clear episode tracking
        if condition_id in self.episode_trades:
            del self.episode_trades[condition_id]

        # Append to CSV
        with open(self.episodes_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(record).keys()))
            writer.writerow(asdict(record))

    def get_summary(self) -> Dict:
        """Get current session summary."""
        total_pnl = sum(t.pnl for t in self.trades)
        wins = sum(1 for t in self.trades if t.pnl > 0)

        return {
            'session_id': self.session_id,
            'total_trades': len(self.trades),
            'total_pnl': total_pnl,
            'win_rate': wins / len(self.trades) if self.trades else 0,
            'total_updates': len(self.updates),
            'total_episodes': len(self.episodes),
            'avg_trade_pnl': total_pnl / len(self.trades) if self.trades else 0,
        }


# Global logger instance
_logger: Optional[TrainingLogger] = None


def get_logger() -> TrainingLogger:
    """Get or create global logger."""
    global _logger
    if _logger is None:
        _logger = TrainingLogger()
    return _logger


def reset_logger():
    """Reset logger for new session."""
    global _logger
    _logger = TrainingLogger()
    return _logger
