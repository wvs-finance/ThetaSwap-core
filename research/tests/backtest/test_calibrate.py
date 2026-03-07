"""Tests for gamma calibration."""
from __future__ import annotations

from backtest.calibrate import compute_avg_fees, derive_gamma_star
from backtest.types import PositionPnL


# ── derive_gamma_star ─────────────────────────────────────────────────

def test_basic_gamma_star():
    """gamma_star = wtp / avg_fees."""
    gamma = derive_gamma_star(wtp=5.0, avg_fees=100.0)
    assert abs(gamma - 0.05) < 1e-9


def test_gamma_star_bounded_at_one():
    """gamma_star capped at 1.0 when wtp > avg_fees."""
    gamma = derive_gamma_star(wtp=200.0, avg_fees=100.0)
    assert gamma == 1.0


def test_gamma_star_zero_fees():
    """Zero avg_fees => gamma_star = 1.0 (edge case)."""
    gamma = derive_gamma_star(wtp=5.0, avg_fees=0.0)
    assert gamma == 1.0


# ── compute_avg_fees ──────────────────────────────────────────────────

def _make_pnl(fees: float) -> PositionPnL:
    return PositionPnL(
        position_idx=0, burn_date="2024-01-01", blocklife=7200,
        alive_days=1, fees_earned=fees, il_cost=0.0,
        premium_paid=0.0, payouts_received=0.0,
        pnl_unhedged=fees, pnl_hedged=fees, hedge_value=0.0,
    )


def test_compute_avg_fees():
    pnls = [_make_pnl(10.0), _make_pnl(20.0), _make_pnl(30.0)]
    avg = compute_avg_fees(pnls)
    assert abs(avg - 20.0) < 1e-9


def test_compute_avg_fees_empty():
    avg = compute_avg_fees([])
    assert avg == 0.0
