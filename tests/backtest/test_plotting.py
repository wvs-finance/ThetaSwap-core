"""Smoke tests for plotting functions — verify each returns a Figure."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from backtest.daily import build_daily_states
from backtest.plotting import hedge_distribution_plot, money_plot, reserve_plot
from backtest.sweep import run_gamma_sweep, run_single_backtest


# ── Fixtures ─────────────────────────────────────────────────────────

DAILY_AT_MAP = {
    "2024-01-01": 0.12,
    "2024-01-02": 0.08,
    "2024-01-03": 0.15,
}

DAILY_AT_NULL_MAP = {
    "2024-01-01": 0.05,
    "2024-01-02": 0.10,
    "2024-01-03": 0.05,
}

IL_MAP = {
    "2024-01-01": 0.001,
    "2024-01-02": 0.002,
    "2024-01-03": 0.003,
}

RAW_POSITIONS = [
    {"burn_date": "2024-01-03", "blocklife": 14400},
    {"burn_date": "2024-01-02", "blocklife": 7200},
]

POOL_DAILY_FEE = 100.0


def _daily_states():
    return build_daily_states(DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS, POOL_DAILY_FEE)


# ── Tests ─────────────────────────────────────────────────────────────

def test_money_plot_returns_figure():
    ds = _daily_states()
    results = run_gamma_sweep(ds, RAW_POSITIONS, [0.05, 0.10])
    fig = money_plot(results)
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_reserve_plot_returns_figure():
    ds = _daily_states()
    result = run_single_backtest(ds, RAW_POSITIONS, gamma=0.10)
    fig = reserve_plot(result)
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_hedge_distribution_plot_returns_figure():
    ds = _daily_states()
    result = run_single_backtest(ds, RAW_POSITIONS, gamma=0.10)
    fig = hedge_distribution_plot(result)
    assert isinstance(fig, Figure)
    plt.close(fig)
