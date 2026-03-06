"""Tests for daily pool state builder."""
from __future__ import annotations

from backtest.daily import build_daily_states


# ── Fixtures ──────────────────────────────────────────────────────────

DAILY_AT_MAP = {
    "2024-01-01": 0.12,
    "2024-01-02": 0.08,
    "2024-01-03": 0.15,
}

DAILY_AT_NULL_MAP = {
    "2024-01-01": 0.10,
    "2024-01-02": 0.10,
    "2024-01-03": 0.10,
}

IL_MAP = {
    "2024-01-01": 0.001,
    "2024-01-02": 0.002,
    "2024-01-03": 0.003,
}

# Position: blocklife = 14400 blocks => 14400/7200 = 2 days before burn
# burn_date = 2024-01-03 => mint ~ 2024-01-01
RAW_POSITIONS = [
    {"burn_date": "2024-01-03", "blocklife": 14400},
    # burn_date = 2024-01-02, blocklife = 7200 => mint ~ 2024-01-01
    {"burn_date": "2024-01-02", "blocklife": 7200},
]

POOL_DAILY_FEE = 100.0


# ── Tests ─────────────────────────────────────────────────────────────

def test_length_matches_daily_at_map():
    states = build_daily_states(DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS, POOL_DAILY_FEE)
    assert len(states) == 3


def test_sorted_by_day():
    states = build_daily_states(DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS, POOL_DAILY_FEE)
    days = [s.day for s in states]
    assert days == sorted(days)


def test_delta_plus_clamped_to_zero():
    """Day 2024-01-02: a_t_real=0.08 < a_t_null=0.10, so delta_plus=0."""
    states = build_daily_states(DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS, POOL_DAILY_FEE)
    day2 = [s for s in states if s.day == "2024-01-02"][0]
    assert day2.delta_plus == 0.0


def test_delta_plus_positive():
    """Day 2024-01-01: a_t_real=0.12 > a_t_null=0.10 => delta_plus=0.02."""
    states = build_daily_states(DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS, POOL_DAILY_FEE)
    day1 = [s for s in states if s.day == "2024-01-01"][0]
    assert abs(day1.delta_plus - 0.02) < 1e-9


def test_n_positions_counts_alive():
    """
    Position 0: mint ~ 2024-01-01, burn = 2024-01-03 => alive on 01, 02 (not 03, burn day)
    Position 1: mint ~ 2024-01-01, burn = 2024-01-02 => alive on 01 (not 02, burn day)
    Day 01: both alive => 2
    Day 02: only position 0 => 1
    Day 03: none alive => 0
    """
    states = build_daily_states(DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS, POOL_DAILY_FEE)
    by_day = {s.day: s for s in states}
    assert by_day["2024-01-01"].n_positions == 2
    assert by_day["2024-01-02"].n_positions == 1
    assert by_day["2024-01-03"].n_positions == 0


def test_pool_daily_fee_propagated():
    states = build_daily_states(DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS, POOL_DAILY_FEE)
    assert all(s.pool_daily_fee == POOL_DAILY_FEE for s in states)
