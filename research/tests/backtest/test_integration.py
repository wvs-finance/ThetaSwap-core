"""Integration tests with real data from econometrics.data."""
from __future__ import annotations

import pytest

from econometrics.data import DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS
from backtest.calibrate import compute_avg_fees, derive_gamma_star
from backtest.daily import build_daily_states
from backtest.sweep import run_gamma_sweep, run_single_backtest


# ── Helper ────────────────────────────────────────────────────────────

def _to_dicts(raw: list[tuple[str, int, float]]) -> list[dict]:
    """Convert econometrics tuples to dicts expected by backtest."""
    return [{"burn_date": bd, "blocklife": bl} for bd, bl, _ in raw]


# ── Tests ─────────────────────────────────────────────────────────────

def test_full_backtest_real_data():
    raw_dicts = _to_dicts(RAW_POSITIONS)
    daily_states = build_daily_states(
        DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, raw_dicts, pool_daily_fee=50_000.0
    )
    assert len(daily_states) == 41

    result = run_single_backtest(daily_states, raw_dicts, gamma=0.10, delta_star=0.09)

    assert len(result.position_pnls) > 500
    assert len(result.reserve_states) == 41
    assert result.total_premiums > 0.0

    # INS-01: reserve never negative
    for rs in result.reserve_states:
        assert rs.balance >= 0.0

    trigger_days = [rs for rs in result.reserve_states if rs.trigger_fired]
    assert len(trigger_days) >= 1


def test_gamma_sweep_real_data():
    raw_dicts = _to_dicts(RAW_POSITIONS)
    daily_states = build_daily_states(
        DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, raw_dicts, pool_daily_fee=50_000.0
    )

    results = run_gamma_sweep(daily_states, raw_dicts, gammas=[0.01, 0.10])
    assert len(results) == 2
    # Higher gamma => more premiums
    assert results[1].total_premiums > results[0].total_premiums


def test_gamma_star_calibration_real_data():
    raw_dicts = _to_dicts(RAW_POSITIONS)
    daily_states = build_daily_states(
        DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, raw_dicts, pool_daily_fee=50_000.0
    )

    # Run at gamma=0.001 to get avg_fees
    result_low = run_single_backtest(daily_states, raw_dicts, gamma=0.001, delta_star=0.09)
    avg_fees = compute_avg_fees(result_low.position_pnls)

    # Derive gamma_star from WTP=110
    gamma_star = derive_gamma_star(wtp=110.0, avg_fees=avg_fees)
    assert 0 < gamma_star < 1

    # Run backtest at gamma_star
    result_star = run_single_backtest(daily_states, raw_dicts, gamma=gamma_star, delta_star=0.09)
    assert result_star.total_premiums > 0.0
    assert len(result_star.position_pnls) > 500
