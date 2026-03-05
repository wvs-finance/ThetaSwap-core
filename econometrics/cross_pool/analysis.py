"""Cross-pool concentration analysis: correlation, plots, architecture decision."""
from __future__ import annotations

import math
from typing import Final, Literal, Sequence

import matplotlib.pyplot as plt

from econometrics.cross_pool.types import PoolConcentration

# ── Constants ──
CATEGORY_COLORS: Final[dict[str, str]] = {
    "stable_stable": "#2ecc71",
    "stable_token": "#3498db",
    "token_token": "#e74c3c",
}

CATEGORY_LABELS: Final[dict[str, str]] = {
    "stable_stable": "Stable/Stable",
    "stable_token": "Stable/Token",
    "token_token": "Token/Token",
}

ArchitectureChoice = Literal["HOOK_INSURANCE", "CFMM_POOL", "HYBRID"]


# ── Pure functions ──

def _ranks(xs: Sequence[float]) -> list[float]:
    """Compute ranks (1-based, average ties)."""
    indexed = sorted(enumerate(xs), key=lambda t: t[1])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(indexed):
        j = i
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j + 1) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def spearman_rank(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Spearman rank correlation coefficient."""
    n = len(xs)
    if n < 3:
        return 0.0
    rx = _ranks(xs)
    ry = _ranks(ys)
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1.0 - 6.0 * d2 / (n * (n * n - 1))


def summary_table(results: Sequence[PoolConcentration]) -> str:
    """Markdown table of all pools with A_T, TVL, category."""
    lines = [
        "| # | Pair | Fee | TVL ($M) | A_T | A_T_null | Δ⁺ | N_pos | Category |",
        "|---|------|-----|----------|-----|----------|-----|-------|----------|",
    ]
    for i, r in enumerate(results, 1):
        pair = f"{r.pool.token0_symbol}/{r.pool.token1_symbol}"
        lines.append(
            f"| {i} | {pair} | {r.pool.fee_tier}bps | "
            f"{r.pool.tvl_usd / 1e6:.1f} | {r.a_t:.4f} | "
            f"{r.a_t_null:.4f} | {r.delta_plus:.4f} | "
            f"{r.n_positions} | {r.pool.pair_category} |"
        )
    return "\n".join(lines)


def architecture_decision(rho_tvl: float, rho_vol: float) -> ArchitectureChoice:
    """Return architecture recommendation based on rank correlations."""
    if rho_tvl < -0.3:
        return "HOOK_INSURANCE"
    if rho_tvl > 0.3:
        return "CFMM_POOL"
    return "HYBRID"


# ── Plot builders ──

def scatter_at_vs_tvl(
    results: Sequence[PoolConcentration],
) -> tuple[plt.Figure, plt.Axes]:
    """Scatter: A_T vs log₁₀(TVL), colored by pair category."""
    fig, ax = plt.subplots(figsize=(9, 6))
    for cat, color in CATEGORY_COLORS.items():
        xs = [math.log10(r.pool.tvl_usd) for r in results if r.pool.pair_category == cat]
        ys = [r.a_t for r in results if r.pool.pair_category == cat]
        labels = [
            f"{r.pool.token0_symbol}/{r.pool.token1_symbol}\n{r.pool.fee_tier}bps"
            for r in results if r.pool.pair_category == cat
        ]
        ax.scatter(xs, ys, c=color, s=100, label=CATEGORY_LABELS[cat], edgecolors="black", zorder=3)
        for x, y, lbl in zip(xs, ys, labels):
            ax.annotate(lbl, (x, y), textcoords="offset points", xytext=(8, 4), fontsize=7)

    tvls = [math.log10(r.pool.tvl_usd) for r in results]
    ats = [r.a_t for r in results]
    rho = spearman_rank(tvls, ats)
    ax.set_xlabel("log₁₀(TVL USD)")
    ax.set_ylabel("A_T (fee concentration index)")
    ax.set_title(f"Fee Concentration vs Pool Size — Spearman ρ = {rho:.3f}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig, ax


def scatter_delta_vs_tvl(
    results: Sequence[PoolConcentration],
) -> tuple[plt.Figure, plt.Axes]:
    """Scatter: Δ⁺ vs log₁₀(TVL), colored by pair category."""
    fig, ax = plt.subplots(figsize=(9, 6))
    for cat, color in CATEGORY_COLORS.items():
        xs = [math.log10(r.pool.tvl_usd) for r in results if r.pool.pair_category == cat]
        ys = [r.delta_plus for r in results if r.pool.pair_category == cat]
        labels = [
            f"{r.pool.token0_symbol}/{r.pool.token1_symbol}\n{r.pool.fee_tier}bps"
            for r in results if r.pool.pair_category == cat
        ]
        ax.scatter(xs, ys, c=color, s=100, label=CATEGORY_LABELS[cat], edgecolors="black", zorder=3)
        for x, y, lbl in zip(xs, ys, labels):
            ax.annotate(lbl, (x, y), textcoords="offset points", xytext=(8, 4), fontsize=7)

    ax.axhline(y=0.09, color="red", linestyle="--", alpha=0.5, label="Δ* = 0.09 (insurance trigger)")
    ax.set_xlabel("log₁₀(TVL USD)")
    ax.set_ylabel("Δ⁺ (excess concentration)")
    ax.set_title("Excess Concentration vs Pool Size")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig, ax
