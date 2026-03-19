"""Tests for exit-based payoff backtest."""
from __future__ import annotations

import math

from backtest.payoff import (
    ExitPayoffResult,
    PositionExitResult,
    delta_to_price,
    payoff_multiplier,
    run_exit_payoff_backtest,
    run_alpha_sweep,
)
from backtest.types import DailyPoolState


# ── Helpers ───────────────────────────────────────────────────────────

def _make_state(day: str, delta_plus: float, n_positions: int = 10,
                pool_daily_fee: float = 100.0) -> DailyPoolState:
    return DailyPoolState(
        day=day, a_t_real=0.0, a_t_null=0.0,
        delta_plus=delta_plus, il=0.0,
        n_positions=n_positions, pool_daily_fee=pool_daily_fee,
    )


SIMPLE_STATES = [
    _make_state("2024-01-01", delta_plus=0.05),
    _make_state("2024-01-02", delta_plus=0.20),  # above Δ*=0.09
    _make_state("2024-01-03", delta_plus=0.03),
]

SIMPLE_POSITIONS = [
    {"burn_date": "2024-01-03", "blocklife": 14400},  # alive 2 days, sees Δ⁺=0.20
    {"burn_date": "2024-01-02", "blocklife": 7200},    # alive 1 day, max Δ⁺=0.05
]


# ── Unit tests ────────────────────────────────────────────────────────

def test_delta_to_price():
    assert delta_to_price(0.0) == 0.0
    assert abs(delta_to_price(0.5) - 1.0) < 1e-9
    assert abs(delta_to_price(0.09) - 0.09 / 0.91) < 1e-9
    assert delta_to_price(1.0) == float("inf")


def test_payoff_multiplier_below_threshold():
    p_star = delta_to_price(0.09)
    assert payoff_multiplier(0.05, p_star, 2.0) == 0.0


def test_payoff_multiplier_above_threshold():
    p_star = delta_to_price(0.09)
    max_p = delta_to_price(0.20)
    result = payoff_multiplier(max_p, p_star, 2.0)
    expected = (max_p / p_star) ** 2 - 1
    assert abs(result - expected) < 1e-9


def test_payoff_multiplier_alpha_one():
    p_star = delta_to_price(0.09)
    max_p = delta_to_price(0.20)
    result = payoff_multiplier(max_p, p_star, 1.0)
    expected = max_p / p_star - 1
    assert abs(result - expected) < 1e-9


# ── Integration tests ─────────────────────────────────────────────────

def test_run_exit_payoff_returns_correct_type():
    result = run_exit_payoff_backtest(
        SIMPLE_STATES, SIMPLE_POSITIONS, gamma=0.10, alpha=2.0,
        delta_star=0.09, initial_balance=1000.0,
    )
    assert isinstance(result, ExitPayoffResult)
    assert result.alpha == 2.0
    assert result.gamma == 0.10
    assert len(result.position_results) == 2


def test_position_above_threshold_gets_payout():
    result = run_exit_payoff_backtest(
        SIMPLE_STATES, SIMPLE_POSITIONS, gamma=0.10, alpha=2.0,
        delta_star=0.09, initial_balance=1000.0,
    )
    # Position 0: alive Jan 1-2, max Δ⁺ = 0.20 > 0.09 → gets payout
    pos0 = result.position_results[0]
    assert pos0.max_delta_plus == 0.20
    assert pos0.payout > pos0.premium  # multiplier > 1 at α=2
    assert pos0.hedge_value > 0


def test_position_below_threshold_no_payout():
    result = run_exit_payoff_backtest(
        SIMPLE_STATES, SIMPLE_POSITIONS, gamma=0.10, alpha=2.0,
        delta_star=0.09, initial_balance=1000.0,
    )
    # Position 1: alive Jan 1 only, max Δ⁺ = 0.05 < 0.09 → no payout
    pos1 = result.position_results[1]
    assert pos1.max_delta_plus == 0.05
    assert pos1.payout == 0.0
    assert pos1.hedge_value < 0  # paid premium, got nothing


def test_solvency_invariant():
    """Reserve never goes negative."""
    result = run_exit_payoff_backtest(
        SIMPLE_STATES, SIMPLE_POSITIONS, gamma=0.10, alpha=3.0,
        delta_star=0.09, initial_balance=0.0,
    )
    assert result.reserve_final >= 0.0


def test_higher_alpha_more_payout_for_severe_events():
    """Higher α concentrates more payout on severe events."""
    r1 = run_exit_payoff_backtest(
        SIMPLE_STATES, SIMPLE_POSITIONS, gamma=0.10, alpha=1.0,
        delta_star=0.09, initial_balance=1000.0,
    )
    r2 = run_exit_payoff_backtest(
        SIMPLE_STATES, SIMPLE_POSITIONS, gamma=0.10, alpha=2.0,
        delta_star=0.09, initial_balance=1000.0,
    )
    # Position 0 experienced severe event — should get more at higher α
    assert r2.position_results[0].payout > r1.position_results[0].payout


def test_alpha_sweep_returns_correct_length():
    results = run_alpha_sweep(
        SIMPLE_STATES, SIMPLE_POSITIONS, gamma=0.10,
        alphas=[0.5, 1.0, 2.0], delta_star=0.09, initial_balance=1000.0,
    )
    assert len(results) == 3
    assert results[0].alpha == 0.5
    assert results[2].alpha == 2.0


def test_zero_seed_premium_funds_reserve():
    """With R₀=0, premiums from exiting positions fund the reserve."""
    result = run_exit_payoff_backtest(
        SIMPLE_STATES, SIMPLE_POSITIONS, gamma=0.10, alpha=2.0,
        delta_star=0.09, initial_balance=0.0,
    )
    assert result.total_premiums > 0.0
    # Positions exit in burn_date order: pos1 (Jan 2) then pos0 (Jan 3)
    # pos1 exits first, pays premium, gets no payout (below threshold)
    # pos0 exits second, pays premium, gets payout funded by both premiums
    assert result.reserve_final >= 0.0
