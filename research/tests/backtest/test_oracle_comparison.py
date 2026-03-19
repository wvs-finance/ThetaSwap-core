"""Tests for oracle_comparison module — cumulative vs daily-snapshot Δ⁺."""
from __future__ import annotations

import math
import pytest

from backtest.oracle_comparison import (
    PositionExit,
    CumulativeOracleState,
    step_cumulative,
    cumulative_delta_plus,
    daily_snapshot_delta_plus,
    DualDeltaPlusSeries,
    build_dual_series,
)


def test_position_exit_frozen():
    pe = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.25)
    assert pe.token_id == 1
    assert pe.burn_date == "2025-12-23"
    assert pe.block_lifetime == 7200
    assert pe.fee_share_x_k == 0.25
    with pytest.raises(AttributeError):
        pe.token_id = 2


def test_cumulative_oracle_state_frozen():
    s = CumulativeOracleState(accumulated_sum=1.5, theta_sum=0.8, removed_pos_count=10)
    assert s.accumulated_sum == 1.5
    assert s.theta_sum == 0.8
    assert s.removed_pos_count == 10
    with pytest.raises(AttributeError):
        s.accumulated_sum = 2.0


def test_step_cumulative_first_exit():
    initial = CumulativeOracleState(accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0)
    exit_ = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    result = step_cumulative(initial, exit_)
    assert result.accumulated_sum == pytest.approx(0.25 / 7200)
    assert result.theta_sum == pytest.approx(1.0 / 7200)
    assert result.removed_pos_count == 1


def test_step_cumulative_accumulates():
    s0 = CumulativeOracleState(accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0)
    e1 = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    e2 = PositionExit(token_id=2, burn_date="2025-12-24", block_lifetime=3600, fee_share_x_k=0.3)
    s1 = step_cumulative(s0, e1)
    s2 = step_cumulative(s1, e2)
    assert s2.accumulated_sum > s1.accumulated_sum
    assert s2.theta_sum > s1.theta_sum
    assert s2.removed_pos_count == 2


def test_cumulative_delta_plus_matches_solidity_formula():
    state = CumulativeOracleState(accumulated_sum=0.04, theta_sum=0.01, removed_pos_count=10)
    expected = max(0.0, math.sqrt(0.04) - math.sqrt(0.01 / 100))
    assert cumulative_delta_plus(state) == pytest.approx(expected)


def test_cumulative_delta_plus_zero_when_no_concentration():
    n = 10
    lifetime = 7200
    x_k = 1.0 / n
    acc_sum = n * (x_k ** 2 / lifetime)
    theta_sum = n * (1.0 / lifetime)
    state = CumulativeOracleState(accumulated_sum=acc_sum, theta_sum=theta_sum, removed_pos_count=n)
    assert cumulative_delta_plus(state) == pytest.approx(0.0, abs=1e-12)


def test_cumulative_delta_plus_zero_state():
    state = CumulativeOracleState(accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0)
    assert cumulative_delta_plus(state) == 0.0


def test_daily_snapshot_delta_plus_basic():
    exits = [
        PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.8),
        PositionExit(token_id=2, burn_date="2025-12-23", block_lifetime=3600, fee_share_x_k=0.2),
    ]
    dp = daily_snapshot_delta_plus(exits)
    assert dp >= 0.0


def test_daily_snapshot_delta_plus_empty():
    assert daily_snapshot_delta_plus([]) == 0.0


def test_dual_series_dataclass():
    s = DualDeltaPlusSeries(
        days=("2025-12-23", "2025-12-24"),
        cumulative_delta_plus=(0.15, 0.14),
        daily_snapshot_delta_plus=(0.15, 0.001),
    )
    assert len(s.days) == 2
    assert s.cumulative_delta_plus[1] > s.daily_snapshot_delta_plus[1]


def test_build_dual_series_divergence():
    exits = [
        PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=100, fee_share_x_k=0.95),
        PositionExit(token_id=2, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.05),
        PositionExit(token_id=3, burn_date="2025-12-24", block_lifetime=7200, fee_share_x_k=0.5),
        PositionExit(token_id=4, burn_date="2025-12-24", block_lifetime=7200, fee_share_x_k=0.5),
    ]
    series = build_dual_series(exits)
    assert len(series.days) == 2
    assert series.daily_snapshot_delta_plus[1] < series.daily_snapshot_delta_plus[0]
    assert series.cumulative_delta_plus[1] > 0
    assert series.cumulative_delta_plus[1] > series.daily_snapshot_delta_plus[1]


def test_build_dual_series_empty():
    series = build_dual_series([])
    assert len(series.days) == 0


# --- Task 5-6: positions_from_raw_data + real-data integration tests ---

from backtest.oracle_comparison import positions_from_raw_data
from econometrics.data import RAW_POSITIONS, DAILY_AT_MAP


def test_positions_from_raw_data():
    raw = [
        ("2025-12-23", 100, 0.15843),
        ("2025-12-23", 7200, 0.15843),
        ("2025-12-24", 3600, 0.13833),
    ]
    exits = positions_from_raw_data(raw)
    assert len(exits) == 3
    assert all(isinstance(e, PositionExit) for e in exits)
    assert exits[0].token_id == 0
    assert exits[1].token_id == 1
    assert exits[2].token_id == 2
    assert exits[0].burn_date == "2025-12-23"
    assert exits[2].burn_date == "2025-12-24"
    assert exits[0].block_lifetime == 100
    assert exits[0].fee_share_x_k == 0.15843


def test_dual_series_real_data_dec23_spike():
    exits = positions_from_raw_data(RAW_POSITIONS)
    series = build_dual_series(exits)
    dec23_idx = series.days.index("2025-12-23")
    assert series.daily_snapshot_delta_plus[dec23_idx] > 0.01, \
        f"Dec 23 daily Δ⁺ should be elevated: {series.daily_snapshot_delta_plus[dec23_idx]}"
    if dec23_idx + 1 < len(series.days):
        dec24_cum = series.cumulative_delta_plus[dec23_idx + 1]
        dec24_snap = series.daily_snapshot_delta_plus[dec23_idx + 1]
        assert dec24_cum > 0.01, f"Cumulative should stay elevated after spike: {dec24_cum}"
        assert dec24_cum >= dec24_snap * 0.5, "Cumulative should be at least comparable to daily after spike"


def test_dual_series_real_data_has_all_days():
    exits = positions_from_raw_data(RAW_POSITIONS)
    series = build_dual_series(exits)
    unique_burn_dates = sorted(set(bd for bd, _, _ in RAW_POSITIONS))
    assert series.days == tuple(unique_burn_dates)
    assert len(series.cumulative_delta_plus) == len(unique_burn_dates)
    assert len(series.daily_snapshot_delta_plus) == len(unique_burn_dates)
