#!/usr/bin/env python3
"""Analyze recent trades and generate insights."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Load the most recent trades file
logs_dir = Path(__file__).parent / "logs"
trades_files = sorted(logs_dir.glob("trades_*.csv"))
# Use the most recent file with 973 trades
latest = logs_dir / "trades_20251231_161516.csv"
print(f"Analyzing: {latest.name}")

df = pd.read_csv(latest)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Basic stats
print(f"\n{'='*60}")
print("TRADING SESSION SUMMARY")
print(f"{'='*60}")
print(f"Total trades: {len(df)}")
print(f"Duration: {(df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60:.1f} min")
print(f"Total PnL: ${df['pnl'].sum():.2f}")
print(f"Win rate: {(df['pnl'] > 0).mean() * 100:.1f}%")
print(f"Avg PnL per trade: ${df['pnl'].mean():.2f}")
print(f"Sharpe (approx): {df['pnl'].mean() / (df['pnl'].std() + 1e-6) * np.sqrt(len(df)):.2f}")

# By asset
print(f"\n{'='*60}")
print("PNL BY ASSET")
print(f"{'='*60}")
by_asset = df.groupby('asset').agg({
    'pnl': ['sum', 'mean', 'count'],
}).round(2)
by_asset.columns = ['Total PnL', 'Avg PnL', 'Trades']
by_asset['Win Rate'] = df.groupby('asset').apply(lambda x: (x['pnl'] > 0).mean() * 100).round(1)
print(by_asset.sort_values('Total PnL', ascending=False))

# By action (BUY vs SELL)
print(f"\n{'='*60}")
print("PNL BY ACTION")
print(f"{'='*60}")
by_action = df.groupby('action').agg({
    'pnl': ['sum', 'mean', 'count'],
}).round(2)
by_action.columns = ['Total PnL', 'Avg PnL', 'Trades']
by_action['Win Rate'] = df.groupby('action').apply(lambda x: (x['pnl'] > 0).mean() * 100).round(1)
print(by_action)

# Entry probability distribution
print(f"\n{'='*60}")
print("ENTRY PROBABILITY ANALYSIS")
print(f"{'='*60}")
df['prob_bucket'] = pd.cut(df['prob_at_entry'], bins=[0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0],
                           labels=['<0.3', '0.3-0.4', '0.4-0.5', '0.5-0.6', '0.6-0.7', '>0.7'])
by_prob = df.groupby('prob_bucket').agg({
    'pnl': ['sum', 'mean', 'count']
}).round(2)
by_prob.columns = ['Total PnL', 'Avg PnL', 'Trades']
print(by_prob)

# Time remaining analysis
print(f"\n{'='*60}")
print("TIME REMAINING ANALYSIS")
print(f"{'='*60}")
df['time_bucket'] = pd.cut(df['time_remaining'], bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                           labels=['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'])
by_time = df.groupby('time_bucket').agg({
    'pnl': ['sum', 'mean', 'count']
}).round(2)
by_time.columns = ['Total PnL', 'Avg PnL', 'Trades']
print(by_time)

# Trade duration analysis
print(f"\n{'='*60}")
print("TRADE DURATION ANALYSIS")
print(f"{'='*60}")
print(f"Avg duration: {df['duration_sec'].mean():.2f}s")
print(f"Median duration: {df['duration_sec'].median():.2f}s")
print(f"Max duration: {df['duration_sec'].max():.2f}s")

# Correlation between duration and PnL
corr = df['duration_sec'].corr(df['pnl'])
print(f"Duration vs PnL correlation: {corr:.3f}")

# Consecutive wins/losses
print(f"\n{'='*60}")
print("STREAK ANALYSIS")
print(f"{'='*60}")
wins = df['pnl'] > 0
current_streak = 0
max_win_streak = 0
max_loss_streak = 0
current_loss = 0

for w in wins:
    if w:
        current_streak += 1
        max_win_streak = max(max_win_streak, current_streak)
        current_loss = 0
    else:
        current_loss += 1
        max_loss_streak = max(max_loss_streak, current_loss)
        current_streak = 0

print(f"Max winning streak: {max_win_streak}")
print(f"Max losing streak: {max_loss_streak}")

# Plot
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle(f'Trading Analysis - {latest.name}', fontsize=14)

# 1. Cumulative PnL
ax = axes[0, 0]
cumsum = df['pnl'].cumsum()
ax.plot(cumsum.values, linewidth=1)
ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
ax.set_title(f'Equity Curve (Final: ${cumsum.iloc[-1]:.0f})')
ax.set_xlabel('Trade #')
ax.set_ylabel('Cumulative PnL ($)')
ax.grid(True, alpha=0.3)

# 2. PnL by asset
ax = axes[0, 1]
asset_pnl = df.groupby('asset')['pnl'].sum().sort_values()
colors = ['red' if x < 0 else 'green' for x in asset_pnl.values]
ax.barh(asset_pnl.index, asset_pnl.values, color=colors)
ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
ax.set_title('PnL by Asset')
ax.set_xlabel('Total PnL ($)')

# 3. PnL by action
ax = axes[0, 2]
action_pnl = df.groupby('action')['pnl'].sum()
colors = ['red' if x < 0 else 'green' for x in action_pnl.values]
ax.bar(action_pnl.index, action_pnl.values, color=colors)
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.set_title('PnL by Action (BUY=Long UP, SELL=Long DOWN)')
ax.set_ylabel('Total PnL ($)')

# 4. Entry probability distribution
ax = axes[1, 0]
ax.hist(df['prob_at_entry'], bins=20, edgecolor='black', alpha=0.7)
ax.axvline(x=0.5, color='red', linestyle='--', label='Fair value')
ax.set_title('Entry Probability Distribution')
ax.set_xlabel('Probability at Entry')
ax.set_ylabel('Count')
ax.legend()

# 5. PnL distribution
ax = axes[1, 1]
ax.hist(df['pnl'], bins=50, edgecolor='black', alpha=0.7)
ax.axvline(x=0, color='red', linestyle='--')
ax.axvline(x=df['pnl'].mean(), color='green', linestyle='--', label=f'Mean: ${df["pnl"].mean():.2f}')
ax.set_title('PnL Distribution')
ax.set_xlabel('PnL ($)')
ax.set_ylabel('Count')
ax.legend()

# 6. Time remaining vs PnL
ax = axes[1, 2]
scatter = ax.scatter(df['time_remaining'], df['pnl'], alpha=0.3, s=10)
ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
corr_time = df['time_remaining'].corr(df['pnl'])
ax.set_title(f'Time Remaining vs PnL (corr: {corr_time:.3f})')
ax.set_xlabel('Time Remaining (fraction)')
ax.set_ylabel('PnL ($)')

plt.tight_layout()
plt.savefig(logs_dir.parent / 'latest_analysis.png', dpi=150)
print(f"\n✅ Saved plot to: latest_analysis.png")
plt.show()
