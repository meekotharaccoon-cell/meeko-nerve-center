#!/usr/bin/env python3
"""
Rich analytics dashboard for trade analysis.
Serves an interactive HTML page to explore trading data.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request
from datetime import datetime

app = Flask(__name__)
LOGS_DIR = Path(__file__).parent / "logs"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            padding: 20px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #333;
        }
        h1 { color: #fff; font-size: 24px; }
        select {
            padding: 10px 15px;
            font-size: 14px;
            background: #1a1a1a;
            color: #fff;
            border: 1px solid #333;
            border-radius: 6px;
            cursor: pointer;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        .stat-card {
            background: #1a1a1a;
            padding: 18px;
            border-radius: 10px;
            border: 1px solid #2a2a2a;
        }
        .stat-label { color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-value { font-size: 28px; font-weight: 600; margin-top: 5px; }
        .stat-value.positive { color: #22c55e; }
        .stat-value.negative { color: #ef4444; }
        .stat-value.neutral { color: #fff; }
        .stat-sub { color: #666; font-size: 11px; margin-top: 3px; }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 25px;
        }
        .chart-container {
            background: #1a1a1a;
            border-radius: 10px;
            padding: 15px;
            border: 1px solid #2a2a2a;
        }
        .chart-title {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 10px;
            color: #ccc;
        }
        .full-width { grid-column: span 2; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #2a2a2a;
        }
        th {
            background: #111;
            color: #888;
            font-weight: 500;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }
        tr:hover { background: #222; }
        .tag {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
        }
        .tag-buy { background: #22c55e22; color: #22c55e; }
        .tag-sell { background: #3b82f622; color: #3b82f6; }
        .insights {
            background: #1a1a1a;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            border: 1px solid #2a2a2a;
        }
        .insight-item {
            padding: 10px 0;
            border-bottom: 1px solid #2a2a2a;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .insight-item:last-child { border-bottom: none; }
        .insight-icon { font-size: 18px; }
        .section-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #fff;
        }
        @media (max-width: 1200px) {
            .charts-grid { grid-template-columns: 1fr; }
            .full-width { grid-column: span 1; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Trading Analytics</h1>
        <select id="fileSelect" onchange="loadData()">
            {% for f in files %}
            <option value="{{ f.name }}" {{ 'selected' if f.name == selected else '' }}>
                {{ f.name }} ({{ f.trades }} trades)
            </option>
            {% endfor %}
        </select>
    </div>

    <div id="dashboard">
        <div class="stats-grid" id="statsGrid"></div>
        <div class="charts-grid" id="chartsGrid"></div>
        <div class="insights" id="insights"></div>
    </div>

    <script>
        const darkLayout = {
            paper_bgcolor: '#1a1a1a',
            plot_bgcolor: '#1a1a1a',
            font: { color: '#888', size: 11 },
            margin: { t: 30, r: 20, b: 40, l: 50 },
            xaxis: { gridcolor: '#2a2a2a', zerolinecolor: '#333' },
            yaxis: { gridcolor: '#2a2a2a', zerolinecolor: '#333' },
        };

        async function loadData() {
            const file = document.getElementById('fileSelect').value;
            const resp = await fetch(`/api/analyze?file=${file}`);
            const data = await resp.json();
            renderDashboard(data);
        }

        function renderDashboard(data) {
            // Stats cards
            const statsHtml = `
                <div class="stat-card">
                    <div class="stat-label">Total PnL</div>
                    <div class="stat-value ${data.total_pnl >= 0 ? 'positive' : 'negative'}">
                        $${data.total_pnl.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                    </div>
                    <div class="stat-sub">${data.roi.toFixed(1)}% ROI</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Trades</div>
                    <div class="stat-value neutral">${data.total_trades.toLocaleString()}</div>
                    <div class="stat-sub">${data.duration_min.toFixed(1)} min session</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Win Rate</div>
                    <div class="stat-value ${data.win_rate >= 50 ? 'positive' : 'neutral'}">${data.win_rate.toFixed(1)}%</div>
                    <div class="stat-sub">${data.wins} wins / ${data.losses} losses</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg PnL/Trade</div>
                    <div class="stat-value ${data.avg_pnl >= 0 ? 'positive' : 'negative'}">
                        $${data.avg_pnl.toFixed(2)}
                    </div>
                    <div class="stat-sub">Median: $${data.median_pnl.toFixed(2)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Sharpe Ratio</div>
                    <div class="stat-value ${data.sharpe >= 1 ? 'positive' : 'neutral'}">${data.sharpe.toFixed(2)}</div>
                    <div class="stat-sub">Sortino: ${data.sortino.toFixed(2)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Max Drawdown</div>
                    <div class="stat-value negative">$${Math.abs(data.max_drawdown).toFixed(2)}</div>
                    <div class="stat-sub">${data.max_drawdown_pct.toFixed(1)}% of peak</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Profit Factor</div>
                    <div class="stat-value ${data.profit_factor >= 1 ? 'positive' : 'negative'}">${data.profit_factor.toFixed(2)}</div>
                    <div class="stat-sub">Gross: $${data.gross_profit.toFixed(0)} / -$${Math.abs(data.gross_loss).toFixed(0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg Duration</div>
                    <div class="stat-value neutral">${data.avg_duration.toFixed(1)}s</div>
                    <div class="stat-sub">Median: ${data.median_duration.toFixed(1)}s</div>
                </div>
            `;
            document.getElementById('statsGrid').innerHTML = statsHtml;

            // Charts
            document.getElementById('chartsGrid').innerHTML = `
                <div class="chart-container full-width">
                    <div class="chart-title">Equity Curve</div>
                    <div id="equityChart"></div>
                </div>
                <div class="chart-container">
                    <div class="chart-title">PnL by Asset</div>
                    <div id="assetChart"></div>
                </div>
                <div class="chart-container">
                    <div class="chart-title">PnL by Action</div>
                    <div id="actionChart"></div>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Entry Probability Distribution</div>
                    <div id="probChart"></div>
                </div>
                <div class="chart-container">
                    <div class="chart-title">PnL by Entry Probability</div>
                    <div id="probPnlChart"></div>
                </div>
                <div class="chart-container">
                    <div class="chart-title">PnL by Time Remaining</div>
                    <div id="timeChart"></div>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Trade Duration Distribution</div>
                    <div id="durationChart"></div>
                </div>
                <div class="chart-container full-width">
                    <div class="chart-title">PnL Distribution</div>
                    <div id="pnlDistChart"></div>
                </div>
                <div class="chart-container full-width">
                    <div class="chart-title">Rolling Win Rate (50 trades)</div>
                    <div id="rollingWinChart"></div>
                </div>
            `;

            // Equity curve
            Plotly.newPlot('equityChart', [{
                y: data.equity_curve,
                type: 'scatter',
                mode: 'lines',
                fill: 'tozeroy',
                line: { color: data.total_pnl >= 0 ? '#22c55e' : '#ef4444', width: 2 },
                fillcolor: data.total_pnl >= 0 ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)'
            }], {...darkLayout, height: 250, showlegend: false});

            // Asset chart
            const assetColors = data.by_asset.pnl.map(v => v >= 0 ? '#22c55e' : '#ef4444');
            Plotly.newPlot('assetChart', [{
                x: data.by_asset.assets,
                y: data.by_asset.pnl,
                type: 'bar',
                marker: { color: assetColors }
            }], {...darkLayout, height: 220});

            // Action chart
            Plotly.newPlot('actionChart', [{
                x: data.by_action.actions,
                y: data.by_action.pnl,
                type: 'bar',
                marker: { color: data.by_action.pnl.map(v => v >= 0 ? '#22c55e' : '#ef4444') }
            }], {...darkLayout, height: 220});

            // Prob distribution
            Plotly.newPlot('probChart', [{
                x: data.prob_hist.bins,
                y: data.prob_hist.counts,
                type: 'bar',
                marker: { color: '#3b82f6' }
            }], {...darkLayout, height: 220});

            // Prob vs PnL
            Plotly.newPlot('probPnlChart', [{
                x: data.by_prob.buckets,
                y: data.by_prob.avg_pnl,
                type: 'bar',
                marker: { color: data.by_prob.avg_pnl.map(v => v >= 0 ? '#22c55e' : '#ef4444') }
            }], {...darkLayout, height: 220});

            // Time remaining vs PnL
            Plotly.newPlot('timeChart', [{
                x: data.by_time.buckets,
                y: data.by_time.avg_pnl,
                type: 'bar',
                marker: { color: data.by_time.avg_pnl.map(v => v >= 0 ? '#22c55e' : '#ef4444') }
            }], {...darkLayout, height: 220});

            // Duration distribution
            Plotly.newPlot('durationChart', [{
                x: data.duration_hist.bins,
                y: data.duration_hist.counts,
                type: 'bar',
                marker: { color: '#8b5cf6' }
            }], {...darkLayout, height: 220});

            // PnL distribution
            Plotly.newPlot('pnlDistChart', [{
                x: data.pnl_hist.bins,
                y: data.pnl_hist.counts,
                type: 'bar',
                marker: { color: data.pnl_hist.bins.map(v => v >= 0 ? '#22c55e' : '#ef4444') }
            }], {...darkLayout, height: 200});

            // Rolling win rate
            Plotly.newPlot('rollingWinChart', [{
                y: data.rolling_win_rate,
                type: 'scatter',
                mode: 'lines',
                line: { color: '#f59e0b', width: 1.5 }
            }, {
                y: Array(data.rolling_win_rate.length).fill(50),
                type: 'scatter',
                mode: 'lines',
                line: { color: '#666', width: 1, dash: 'dash' }
            }], {...darkLayout, height: 200, showlegend: false});

            // Insights
            let insightsHtml = '<div class="section-title">🔍 Key Insights</div>';
            data.insights.forEach(i => {
                insightsHtml += `<div class="insight-item"><span class="insight-icon">${i.icon}</span><span>${i.text}</span></div>`;
            });

            // Add detailed tables
            insightsHtml += `
                <div class="section-title" style="margin-top: 25px;">📊 Detailed Breakdown</div>
                <table>
                    <thead>
                        <tr><th>Asset</th><th>Trades</th><th>Win Rate</th><th>Total PnL</th><th>Avg PnL</th><th>Best</th><th>Worst</th></tr>
                    </thead>
                    <tbody>
                        ${data.asset_details.map(a => `
                            <tr>
                                <td><strong>${a.asset}</strong></td>
                                <td>${a.trades}</td>
                                <td>${a.win_rate.toFixed(1)}%</td>
                                <td style="color: ${a.pnl >= 0 ? '#22c55e' : '#ef4444'}">$${a.pnl.toFixed(2)}</td>
                                <td>$${a.avg.toFixed(2)}</td>
                                <td style="color: #22c55e">$${a.best.toFixed(2)}</td>
                                <td style="color: #ef4444">$${a.worst.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>

                <div class="section-title" style="margin-top: 25px;">⏱️ Timing Analysis</div>
                <table>
                    <thead>
                        <tr><th>Time Remaining</th><th>Trades</th><th>Win Rate</th><th>Total PnL</th><th>Avg PnL</th></tr>
                    </thead>
                    <tbody>
                        ${data.time_details.map(t => `
                            <tr>
                                <td>${t.bucket}</td>
                                <td>${t.trades}</td>
                                <td>${t.win_rate.toFixed(1)}%</td>
                                <td style="color: ${t.pnl >= 0 ? '#22c55e' : '#ef4444'}">$${t.pnl.toFixed(2)}</td>
                                <td>$${t.avg.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>

                <div class="section-title" style="margin-top: 25px;">🎯 Entry Probability Analysis</div>
                <table>
                    <thead>
                        <tr><th>Probability Range</th><th>Trades</th><th>Win Rate</th><th>Total PnL</th><th>Avg PnL</th></tr>
                    </thead>
                    <tbody>
                        ${data.prob_details.map(p => `
                            <tr>
                                <td>${p.bucket}</td>
                                <td>${p.trades}</td>
                                <td>${p.win_rate.toFixed(1)}%</td>
                                <td style="color: ${p.pnl >= 0 ? '#22c55e' : '#ef4444'}">$${p.pnl.toFixed(2)}</td>
                                <td>$${p.avg.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>

                <div class="section-title" style="margin-top: 25px;">📈 Streak Analysis</div>
                <table>
                    <thead>
                        <tr><th>Metric</th><th>Value</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>Max Winning Streak</td><td style="color: #22c55e">${data.max_win_streak} trades</td></tr>
                        <tr><td>Max Losing Streak</td><td style="color: #ef4444">${data.max_loss_streak} trades</td></tr>
                        <tr><td>Avg Winning Streak</td><td>${data.avg_win_streak.toFixed(1)} trades</td></tr>
                        <tr><td>Avg Losing Streak</td><td>${data.avg_loss_streak.toFixed(1)} trades</td></tr>
                        <tr><td>Current Streak</td><td>${data.current_streak > 0 ? '+' : ''}${data.current_streak} (${data.current_streak > 0 ? 'winning' : 'losing'})</td></tr>
                    </tbody>
                </table>
            `;

            document.getElementById('insights').innerHTML = insightsHtml;
        }

        // Load on start
        loadData();
    </script>
</body>
</html>
"""

def get_trade_files():
    """Get all trade files with metadata."""
    files = []
    for f in sorted(LOGS_DIR.glob("trades_*.csv"), reverse=True):
        try:
            df = pd.read_csv(f)
            files.append({
                'name': f.name,
                'trades': len(df),
                'path': str(f)
            })
        except:
            pass
    return files

def analyze_trades(filepath):
    """Comprehensive trade analysis."""
    df = pd.read_csv(filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Basic stats
    total_pnl = df['pnl'].sum()
    total_trades = len(df)
    wins = (df['pnl'] > 0).sum()
    losses = (df['pnl'] <= 0).sum()
    win_rate = wins / total_trades * 100 if total_trades > 0 else 0

    # Duration
    duration_min = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60

    # PnL metrics
    avg_pnl = df['pnl'].mean()
    median_pnl = df['pnl'].median()
    std_pnl = df['pnl'].std()

    # Sharpe & Sortino (annualized approximation)
    sharpe = (avg_pnl / std_pnl * np.sqrt(total_trades)) if std_pnl > 0 else 0
    downside_std = df[df['pnl'] < 0]['pnl'].std() if len(df[df['pnl'] < 0]) > 0 else 1
    sortino = (avg_pnl / downside_std * np.sqrt(total_trades)) if downside_std > 0 else 0

    # Drawdown
    equity = df['pnl'].cumsum()
    peak = equity.cummax()
    drawdown = equity - peak
    max_drawdown = drawdown.min()
    max_drawdown_pct = (max_drawdown / peak.max() * 100) if peak.max() > 0 else 0

    # Profit factor
    gross_profit = df[df['pnl'] > 0]['pnl'].sum()
    gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    # Duration stats
    avg_duration = df['duration_sec'].mean()
    median_duration = df['duration_sec'].median()

    # ROI (assuming $500 position size from the data)
    position_size = df['size'].iloc[0] if 'size' in df.columns else 500
    roi = (total_pnl / (position_size * 4)) * 100  # 4 markets

    # By asset
    by_asset = df.groupby('asset').agg({
        'pnl': ['sum', 'mean', 'count', 'max', 'min']
    }).reset_index()
    by_asset.columns = ['asset', 'pnl', 'avg', 'trades', 'best', 'worst']
    by_asset['win_rate'] = df.groupby('asset').apply(lambda x: (x['pnl'] > 0).mean() * 100).values

    # By action
    by_action = df.groupby('action')['pnl'].agg(['sum', 'mean', 'count']).reset_index()

    # Probability buckets
    prob_bins = [0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0]
    prob_labels = ['<0.3', '0.3-0.4', '0.4-0.5', '0.5-0.6', '0.6-0.7', '>0.7']
    df['prob_bucket'] = pd.cut(df['prob_at_entry'], bins=prob_bins, labels=prob_labels)
    by_prob = df.groupby('prob_bucket', observed=True).agg({
        'pnl': ['sum', 'mean', 'count']
    }).reset_index()
    by_prob.columns = ['bucket', 'pnl', 'avg', 'trades']
    by_prob['win_rate'] = df.groupby('prob_bucket', observed=True).apply(
        lambda x: (x['pnl'] > 0).mean() * 100, include_groups=False
    ).values

    # Time buckets
    time_bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    time_labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
    df['time_bucket'] = pd.cut(df['time_remaining'], bins=time_bins, labels=time_labels)
    by_time = df.groupby('time_bucket', observed=True).agg({
        'pnl': ['sum', 'mean', 'count']
    }).reset_index()
    by_time.columns = ['bucket', 'pnl', 'avg', 'trades']
    by_time['win_rate'] = df.groupby('time_bucket', observed=True).apply(
        lambda x: (x['pnl'] > 0).mean() * 100, include_groups=False
    ).values

    # Histograms
    prob_hist, prob_edges = np.histogram(df['prob_at_entry'], bins=20)
    duration_hist, duration_edges = np.histogram(df['duration_sec'].clip(0, 30), bins=20)
    pnl_hist, pnl_edges = np.histogram(df['pnl'].clip(-100, 100), bins=40)

    # Rolling win rate
    rolling_win = (df['pnl'] > 0).rolling(50).mean() * 100
    rolling_win = rolling_win.dropna().tolist()

    # Streak analysis
    streaks = []
    current = 0
    for pnl in df['pnl']:
        if pnl > 0:
            if current >= 0:
                current += 1
            else:
                streaks.append(current)
                current = 1
        else:
            if current <= 0:
                current -= 1
            else:
                streaks.append(current)
                current = -1
    streaks.append(current)

    win_streaks = [s for s in streaks if s > 0]
    loss_streaks = [abs(s) for s in streaks if s < 0]

    max_win_streak = max(win_streaks) if win_streaks else 0
    max_loss_streak = max(loss_streaks) if loss_streaks else 0
    avg_win_streak = np.mean(win_streaks) if win_streaks else 0
    avg_loss_streak = np.mean(loss_streaks) if loss_streaks else 0

    # Generate insights
    insights = []

    # Best/worst asset
    best_asset = by_asset.loc[by_asset['pnl'].idxmax()]
    worst_asset = by_asset.loc[by_asset['pnl'].idxmin()]
    insights.append({'icon': '🏆', 'text': f"Best performer: {best_asset['asset']} (+${best_asset['pnl']:.2f}, {best_asset['win_rate']:.1f}% win rate)"})
    if worst_asset['pnl'] < 0:
        insights.append({'icon': '⚠️', 'text': f"Worst performer: {worst_asset['asset']} (${worst_asset['pnl']:.2f}, {worst_asset['win_rate']:.1f}% win rate)"})

    # Timing insight
    best_time = by_time.loc[by_time['avg'].idxmax()] if len(by_time) > 0 else None
    if best_time is not None:
        insights.append({'icon': '⏰', 'text': f"Best timing: {best_time['bucket']} time remaining (${best_time['avg']:.2f} avg)"})

    # Probability insight
    best_prob = by_prob.loc[by_prob['avg'].idxmax()] if len(by_prob) > 0 else None
    if best_prob is not None:
        insights.append({'icon': '🎯', 'text': f"Best entry zone: {best_prob['bucket']} probability (${best_prob['avg']:.2f} avg)"})

    # Action bias
    buy_pnl = df[df['action'] == 'BUY']['pnl'].sum()
    sell_pnl = df[df['action'] == 'SELL']['pnl'].sum()
    if abs(buy_pnl - sell_pnl) > 100:
        better = 'BUY (UP bets)' if buy_pnl > sell_pnl else 'SELL (DOWN bets)'
        insights.append({'icon': '📊', 'text': f"Direction bias: {better} outperforming by ${abs(buy_pnl - sell_pnl):.2f}"})

    # Win rate vs profitability
    if win_rate < 30 and total_pnl > 0:
        insights.append({'icon': '💡', 'text': f"Low win rate ({win_rate:.1f}%) but profitable - asymmetric payoffs working"})

    # Streak warning
    if max_loss_streak > 15:
        insights.append({'icon': '🔴', 'text': f"Max losing streak of {max_loss_streak} trades - check risk management"})

    return {
        'total_pnl': total_pnl,
        'total_trades': total_trades,
        'wins': int(wins),
        'losses': int(losses),
        'win_rate': win_rate,
        'duration_min': duration_min,
        'avg_pnl': avg_pnl,
        'median_pnl': median_pnl,
        'sharpe': sharpe,
        'sortino': sortino,
        'max_drawdown': max_drawdown,
        'max_drawdown_pct': max_drawdown_pct,
        'profit_factor': min(profit_factor, 99.99),
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'avg_duration': avg_duration,
        'median_duration': median_duration,
        'roi': roi,
        'equity_curve': equity.tolist(),
        'by_asset': {
            'assets': by_asset['asset'].tolist(),
            'pnl': by_asset['pnl'].tolist()
        },
        'by_action': {
            'actions': by_action['action'].tolist(),
            'pnl': by_action['sum'].tolist()
        },
        'by_prob': {
            'buckets': by_prob['bucket'].astype(str).tolist(),
            'avg_pnl': by_prob['avg'].tolist()
        },
        'by_time': {
            'buckets': by_time['bucket'].astype(str).tolist(),
            'avg_pnl': by_time['avg'].tolist()
        },
        'prob_hist': {
            'bins': ((prob_edges[:-1] + prob_edges[1:]) / 2).tolist(),
            'counts': prob_hist.tolist()
        },
        'duration_hist': {
            'bins': ((duration_edges[:-1] + duration_edges[1:]) / 2).tolist(),
            'counts': duration_hist.tolist()
        },
        'pnl_hist': {
            'bins': ((pnl_edges[:-1] + pnl_edges[1:]) / 2).tolist(),
            'counts': pnl_hist.tolist()
        },
        'rolling_win_rate': rolling_win,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'avg_win_streak': avg_win_streak,
        'avg_loss_streak': avg_loss_streak,
        'current_streak': streaks[-1] if streaks else 0,
        'insights': insights,
        'asset_details': by_asset.to_dict('records'),
        'time_details': by_time.to_dict('records'),
        'prob_details': by_prob.to_dict('records'),
    }

@app.route('/')
def index():
    files = get_trade_files()
    selected = files[0]['name'] if files else None
    return render_template_string(HTML_TEMPLATE, files=files, selected=selected)

@app.route('/api/analyze')
def api_analyze():
    filename = request.args.get('file')
    filepath = LOGS_DIR / filename
    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404

    try:
        data = analyze_trades(filepath)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("📊 Trading Analytics Dashboard")
    print("=" * 60)
    print(f"Open: http://localhost:5002")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5002, debug=False)
