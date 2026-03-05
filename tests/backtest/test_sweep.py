"""Tests for gamma sweep orchestrator."""
from __future__ import annotations

from backtest.sweep import run_single_backtest, run_gamma_sweep
from backtest.types import BacktestResult, DailyPoolState


# ── Fixtures (3 days, 2 positions) ───────────────────────────────────

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

# Position 0: burn=2024-01-03, blocklife=14400 (2 days) => mint ~ 2024-01-01
# Position 1: burn=2024-01-02, blocklife=7200 (1 day) => mint ~ 2024-01-01
# Position 1 has blocklife=7200 > 1, so included in exits and PnL
RAW_POSITIONS = [
    {"burn_date": "2024-01-03", "blocklife": 14400},
    {"burn_date": "2024-01-02", "blocklife": 7200},
]

POOL_DAILY_FEE = 100.0


def _build_daily_states():
    from backtest.daily import build_daily_states
    return build_daily_states(DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS, POOL_DAILY_FEE)


# ── Tests ─────────────────────────────────────────────────────────────

def test_run_single_backtest_returns_backtest_result():
    daily_states = _build_daily_states()
    result = run_single_backtest(daily_states, RAW_POSITIONS, gamma=0.10)
    assert isinstance(result, BacktestResult)


def test_run_single_backtest_fields_correct():
    daily_states = _build_daily_states()
    result = run_single_backtest(daily_states, RAW_POSITIONS, gamma=0.10)
    assert result.gamma == 0.10
    assert result.total_premiums >= 0.0
    assert result.total_payouts >= 0.0
    assert result.trigger_days >= 0
    assert len(result.reserve_states) == 3
    # 2 positions both have blocklife > 1
    assert len(result.position_pnls) == 2


def test_run_single_backtest_aggregation():
    daily_states = _build_daily_states()
    result = run_single_backtest(daily_states, RAW_POSITIONS, gamma=0.10)
    # total_premiums = sum of reserve_states premium_in
    assert abs(result.total_premiums - sum(rs.premium_in for rs in result.reserve_states)) < 1e-9
    # total_payouts = sum of reserve_states payout_out
    assert abs(result.total_payouts - sum(rs.payout_out for rs in result.reserve_states)) < 1e-9
    # trigger_days = count of trigger_fired
    assert result.trigger_days == sum(1 for rs in result.reserve_states if rs.trigger_fired)


def test_run_single_backtest_reserve_solvency():
    """INS-01: reserve balance never goes negative."""
    daily_states = _build_daily_states()
    result = run_single_backtest(daily_states, RAW_POSITIONS, gamma=0.10)
    for rs in result.reserve_states:
        assert rs.balance >= 0.0


def test_run_gamma_sweep_returns_correct_length():
    daily_states = _build_daily_states()
    gammas = [0.01, 0.05, 0.10, 0.20]
    results = run_gamma_sweep(daily_states, RAW_POSITIONS, gammas)
    assert len(results) == 4
    assert all(isinstance(r, BacktestResult) for r in results)


def test_higher_gamma_more_premiums():
    daily_states = _build_daily_states()
    gammas = [0.01, 0.10, 0.50]
    results = run_gamma_sweep(daily_states, RAW_POSITIONS, gammas)
    for i in range(len(results) - 1):
        assert results[i].total_premiums <= results[i + 1].total_premiums


def test_blocklife_one_excluded():
    """Positions with blocklife <= 1 are excluded from exits and PnL."""
    daily_states = _build_daily_states()
    positions_with_short = [
        {"burn_date": "2024-01-03", "blocklife": 14400},
        {"burn_date": "2024-01-02", "blocklife": 1},  # blocklife <= 1, excluded
    ]
    result = run_single_backtest(daily_states, positions_with_short, gamma=0.10)
    # Only 1 position has blocklife > 1
    assert len(result.position_pnls) == 1
