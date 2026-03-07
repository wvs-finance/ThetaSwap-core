"""Tests for backtest domain types — frozen dataclasses."""
from __future__ import annotations

import pytest

from backtest.types import (
    BacktestResult,
    DailyPoolState,
    PositionPnL,
    ReserveState,
)


# ── DailyPoolState ────────────────────────────────────────────────────

def test_daily_pool_state_fields():
    s = DailyPoolState(
        day="2024-01-01",
        a_t_real=0.12,
        a_t_null=0.10,
        delta_plus=0.02,
        il=0.005,
        n_positions=42,
        pool_daily_fee=100.0,
    )
    assert s.day == "2024-01-01"
    assert s.a_t_real == 0.12
    assert s.a_t_null == 0.10
    assert s.delta_plus == 0.02
    assert s.il == 0.005
    assert s.n_positions == 42
    assert s.pool_daily_fee == 100.0


def test_daily_pool_state_frozen():
    s = DailyPoolState(
        day="2024-01-01", a_t_real=0.12, a_t_null=0.10,
        delta_plus=0.02, il=0.005, n_positions=42, pool_daily_fee=100.0,
    )
    with pytest.raises(AttributeError):
        s.day = "2024-01-02"  # type: ignore[misc]


# ── ReserveState ──────────────────────────────────────────────────────

def test_reserve_state_fields():
    r = ReserveState(
        day="2024-01-01", balance=1000.0, premium_in=50.0,
        payout_out=0.0, trigger_fired=False, delta_plus=0.05,
        donate_amount=0.0,
    )
    assert r.balance == 1000.0
    assert r.trigger_fired is False
    assert r.donate_amount == 0.0


def test_reserve_state_frozen():
    r = ReserveState(
        day="2024-01-01", balance=1000.0, premium_in=50.0,
        payout_out=0.0, trigger_fired=False, delta_plus=0.05,
        donate_amount=0.0,
    )
    with pytest.raises(AttributeError):
        r.balance = 0.0  # type: ignore[misc]


# ── PositionPnL ──────────────────────────────────────────────────────

def test_position_pnl_fields():
    p = PositionPnL(
        position_idx=0, burn_date="2024-03-01", blocklife=72000,
        alive_days=10, fees_earned=50.0, il_cost=20.0,
        premium_paid=5.0, payouts_received=10.0,
        pnl_unhedged=30.0, pnl_hedged=35.0, hedge_value=5.0,
    )
    assert p.position_idx == 0
    assert p.hedge_value == 5.0


def test_position_pnl_frozen():
    p = PositionPnL(
        position_idx=0, burn_date="2024-03-01", blocklife=72000,
        alive_days=10, fees_earned=50.0, il_cost=20.0,
        premium_paid=5.0, payouts_received=10.0,
        pnl_unhedged=30.0, pnl_hedged=35.0, hedge_value=5.0,
    )
    with pytest.raises(AttributeError):
        p.fees_earned = 0.0  # type: ignore[misc]


# ── BacktestResult ───────────────────────────────────────────────────

def test_backtest_result_fields():
    b = BacktestResult(
        gamma=0.05, total_premiums=500.0, total_payouts=300.0,
        trigger_days=3, mean_hedge_value=2.0, median_hedge_value=1.5,
        pct_better_off=0.6, reserve_peak=1000.0,
        reserve_utilization=0.3, position_pnls=[], reserve_states=[],
    )
    assert b.gamma == 0.05
    assert b.position_pnls == []


def test_backtest_result_frozen():
    b = BacktestResult(
        gamma=0.05, total_premiums=500.0, total_payouts=300.0,
        trigger_days=3, mean_hedge_value=2.0, median_hedge_value=1.5,
        pct_better_off=0.6, reserve_peak=1000.0,
        reserve_utilization=0.3, position_pnls=[], reserve_states=[],
    )
    with pytest.raises(AttributeError):
        b.gamma = 0.1  # type: ignore[misc]
