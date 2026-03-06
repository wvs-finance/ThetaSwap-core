"""Smoke tests for plotting — verify figures are created without errors."""
import matplotlib
matplotlib.use("Agg")

from simulation.scenarios import run_simulation
from simulation.config import SimConfig
from simulation.plotting import (
    plot_pnl_comparison,
    plot_index_and_price,
    plot_reserves,
    plot_funding_and_premium,
    plot_welfare_summary,
)


def _result():
    return run_simulation(SimConfig(T=100), seed=42)


def test_plot_pnl_creates_figure():
    fig = plot_pnl_comparison(_result())
    assert fig is not None
    assert len(fig.axes) >= 2


def test_plot_index_creates_figure():
    fig = plot_index_and_price(_result())
    assert fig is not None


def test_plot_reserves_creates_figure():
    fig = plot_reserves(_result())
    assert fig is not None


def test_plot_funding_creates_figure():
    fig = plot_funding_and_premium(_result())
    assert fig is not None


def test_plot_welfare_creates_figure():
    fig = plot_welfare_summary(_result())
    assert fig is not None
