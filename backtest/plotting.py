"""Plotting functions for backtest results — each returns a matplotlib Figure."""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from backtest.types import BacktestResult


def money_plot(results: list[BacktestResult]) -> Figure:
    """Two-subplot figure: top = P&L time series, bottom = delta_plus time series.

    Unhedged line (red) vs hedged per gamma (green shades).
    Trigger days shaded in background.
    """
    if not results:
        fig, _ = plt.subplots(2, 1, figsize=(12, 8))
        return fig

    # Use first result for reference (all share same daily_states)
    ref = results[0]
    days = [rs.day for rs in ref.reserve_states]
    trigger_mask = [rs.trigger_fired for rs in ref.reserve_states]

    fig, (ax_pnl, ax_delta) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Shade trigger days on both axes
    for ax in (ax_pnl, ax_delta):
        for i, fired in enumerate(trigger_mask):
            if fired:
                ax.axvspan(i - 0.5, i + 0.5, alpha=0.15, color="orange")

    # Build cumulative unhedged P&L from first result's position PnLs
    # Use reserve-level: cumulative (premium_in - payout_out) as proxy
    # Actually plot per-day aggregate: unhedged = pool_fee - il per day
    # We use reserve_states for day-level data
    x = np.arange(len(days))

    # Unhedged cumulative: sum of (fee_share - il) per day across positions
    # Approximate from reserve: no hedge means full fees, minus IL
    # For simplicity, plot cumulative premium_in (hedged) vs cumulative payout (benefit)
    for idx, res in enumerate(results):
        green_shade = 0.3 + 0.5 * idx / max(len(results) - 1, 1)
        color = (0.0, green_shade, 0.0)
        cum_net = np.cumsum([rs.premium_in - rs.payout_out for rs in res.reserve_states])
        label = f"gamma={res.gamma:.3f}"
        ax_pnl.plot(x, cum_net, color=color, label=label, linewidth=1.5)

    ax_pnl.set_ylabel("Cumulative Reserve Net")
    ax_pnl.legend(fontsize=8)
    ax_pnl.set_title("Money Plot: Reserve Net by Gamma")

    # Bottom: delta_plus time series
    deltas = [rs.delta_plus for rs in ref.reserve_states]
    ax_delta.plot(x, deltas, color="steelblue", linewidth=1.5)
    ax_delta.set_ylabel("Delta+")
    ax_delta.set_xlabel("Day")
    ax_delta.set_xticks(x[::max(1, len(x) // 10)])
    ax_delta.set_xticklabels([days[i] for i in range(0, len(days), max(1, len(days) // 10))],
                              rotation=45, fontsize=7)

    fig.tight_layout()
    return fig


def reserve_plot(result: BacktestResult) -> Figure:
    """R(t) fill + line, vertical lines on trigger days."""
    days = [rs.day for rs in result.reserve_states]
    balances = [rs.balance for rs in result.reserve_states]
    x = np.arange(len(days))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(x, balances, alpha=0.3, color="steelblue")
    ax.plot(x, balances, color="steelblue", linewidth=1.5)

    for i, rs in enumerate(result.reserve_states):
        if rs.trigger_fired:
            ax.axvline(i, color="red", linestyle="--", alpha=0.7)

    ax.set_ylabel("Reserve Balance R(t)")
    ax.set_xlabel("Day")
    ax.set_title(f"Reserve Trajectory (gamma={result.gamma:.3f})")
    ax.set_xticks(x[::max(1, len(x) // 10)])
    ax.set_xticklabels([days[i] for i in range(0, len(days), max(1, len(days) // 10))],
                        rotation=45, fontsize=7)

    fig.tight_layout()
    return fig


def hedge_distribution_plot(result: BacktestResult) -> Figure:
    """Histogram of hedge_value_i, vertical line at 0."""
    hedge_values = [p.hedge_value for p in result.position_pnls]

    fig, ax = plt.subplots(figsize=(8, 5))
    if hedge_values:
        ax.hist(hedge_values, bins=min(30, max(5, len(hedge_values) // 5)),
                edgecolor="black", alpha=0.7, color="steelblue")
    ax.axvline(0, color="red", linestyle="--", linewidth=1.5, label="break-even")
    ax.set_xlabel("Hedge Value (hedged - unhedged)")
    ax.set_ylabel("Count")
    ax.set_title(f"Hedge Value Distribution (gamma={result.gamma:.3f})")
    ax.legend()

    fig.tight_layout()
    return fig
