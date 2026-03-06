"""All matplotlib figure builders for the demo notebook.

Each function takes a SimResult and returns a matplotlib Figure.
"""
from __future__ import annotations

from typing import Final

import matplotlib.pyplot as plt
import numpy as np

from simulation.scenarios import SimResult

# Style constants
HEDGED_COLOR: Final = "#2ecc71"
UNHEDGED_COLOR: Final = "#e74c3c"
INDEX_COLOR: Final = "#3498db"
MARK_COLOR: Final = "#e67e22"
RISKY_COLOR: Final = "#9b59b6"
NUMERAIRE_COLOR: Final = "#f1c40f"
UW_COLOR: Final = "#1abc9c"

PHASE_COLORS: Final = ["#d4e6f1", "#fdebd0", "#fadbd8"]
PHASE_LABELS: Final = ["Calm", "Gradual JIT Growth", "Shock"]


def _add_phase_shading(ax: plt.Axes, T: int) -> None:
    """Add background shading for the 3-phase narrative arc."""
    third = T // 3
    for i, (color, label) in enumerate(zip(PHASE_COLORS, PHASE_LABELS)):
        ax.axvspan(i * third, (i + 1) * third, alpha=0.3, color=color, label=label)


def plot_pnl_comparison(result: SimResult) -> plt.Figure:
    """Plot 1: Hedged vs Unhedged PLP P&L with A_T subplot."""
    T = len(result.A_T)
    blocks = np.arange(T)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), height_ratios=[3, 1],
                                    sharex=True, gridspec_kw={"hspace": 0.08})

    _add_phase_shading(ax1, T)

    ax1.plot(blocks, result.hedged_pnl, color=HEDGED_COLOR, linewidth=2,
             label="PLP (Hedged)")
    ax1.plot(blocks, result.unhedged_pnl, color=UNHEDGED_COLOR, linewidth=2,
             label="PLP (Unhedged)", linestyle="--")
    ax1.set_ylabel("Cumulative P&L")
    ax1.set_title("PLP Profit & Loss: Hedged vs Unhedged", fontsize=14, fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    ax2.fill_between(blocks, result.A_T, alpha=0.4, color=INDEX_COLOR)
    ax2.plot(blocks, result.A_T, color=INDEX_COLOR, linewidth=1)
    ax2.set_ylabel("$A_T$")
    ax2.set_xlabel("Block Number")
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_index_and_price(result: SimResult) -> plt.Figure:
    """Plot 2: A_T trajectory + mark vs index price."""
    T = len(result.A_T)
    blocks = np.arange(T)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True,
                                    gridspec_kw={"hspace": 0.08})

    ax1.plot(blocks, result.A_T, color=INDEX_COLOR, linewidth=1.5)
    ax1.fill_between(blocks, result.A_T, alpha=0.2, color=INDEX_COLOR)
    ax1.set_ylabel("$A_T$ (Fee Concentration)")
    ax1.set_title("Fee Concentration Index & CFMM Price Response", fontsize=14, fontweight="bold")
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3)

    ax2.plot(blocks, result.p_index, color=INDEX_COLOR, linewidth=1.5,
             label="$p_{index} = A_T/(1-A_T)$")
    ax2.plot(blocks, result.p_mark, color=MARK_COLOR, linewidth=1.5,
             label="$p_{mark} = (1-x)/x$", linestyle="--")
    ax2.fill_between(blocks, result.p_index, result.p_mark, alpha=0.15,
                     color=MARK_COLOR, label="Basis")
    ax2.set_ylabel("Price $p$")
    ax2.set_xlabel("Block Number")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_reserves(result: SimResult) -> plt.Figure:
    """Plot 3: Reserve composition (stacked area) over time."""
    T = len(result.A_T)
    blocks = np.arange(T)

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.stackplot(blocks, result.x, result.y,
                 labels=["Risky Reserve $x$", "Numeraire Reserve $y$"],
                 colors=[RISKY_COLOR, NUMERAIRE_COLOR], alpha=0.7)

    total = result.p_index * result.x + result.y
    ax.plot(blocks, total, color="black", linewidth=1.5, linestyle=":",
            label="Total Value $px + y$")

    ax.set_title("CFMM Reserve Composition Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Block Number")
    ax.set_ylabel("Reserve Amount")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_funding_and_premium(result: SimResult) -> plt.Figure:
    """Plot 4: Funding rate + dynamic fee, cumulative premium flows."""
    T = len(result.A_T)
    blocks = np.arange(T)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True,
                                    gridspec_kw={"hspace": 0.12})

    ax1.plot(blocks, result.funding_rates, color=MARK_COLOR, linewidth=1,
             label="Funding Rate $r$", alpha=0.8)
    ax1.plot(blocks, result.fees, color=INDEX_COLOR, linewidth=1.5,
             label=r"Dynamic Fee $\varphi(t)$")
    ax1.set_ylabel("Rate")
    ax1.set_title("Funding Rate & Premium Cost", fontsize=14, fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    ax2.plot(blocks, result.cum_premium_paid, color=UNHEDGED_COLOR, linewidth=1.5,
             label="PLP Premium Paid")
    ax2.plot(blocks, result.cum_premium_earned, color=UW_COLOR, linewidth=1.5,
             label="Underwriter Premium Earned", linestyle="--")
    ax2.set_ylabel("Cumulative Premium")
    ax2.set_xlabel("Block Number")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_welfare_summary(result: SimResult) -> plt.Figure:
    """Plot 5 (Bonus): Ecosystem welfare bar chart."""
    hedged_final = result.hedged_pnl[-1]
    unhedged_final = result.unhedged_pnl[-1]
    uw_final = result.underwriter_pnl[-1]
    total = hedged_final + uw_final

    labels = ["PLP\n(Hedged)", "PLP\n(Unhedged)", "Underwriter", "Total\nWelfare"]
    values = [hedged_final, unhedged_final, uw_final, total]
    colors = [HEDGED_COLOR, UNHEDGED_COLOR, UW_COLOR, "#34495e"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=1.5)

    for bar, val in zip(bars, values):
        y_pos = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, y_pos + abs(y_pos) * 0.02,
                f"{val:.1f}", ha="center", va="bottom", fontweight="bold")

    ax.set_title("Ecosystem Welfare Summary", fontsize=14, fontweight="bold")
    ax.set_ylabel("Cumulative P&L")
    ax.axhline(y=0, color="gray", linewidth=0.5)
    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    return fig
