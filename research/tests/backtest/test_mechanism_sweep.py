"""Tests for mechanism_sweep — epoch, decay, sliding-window step functions."""
from __future__ import annotations

import math
import pytest

from backtest.oracle_comparison import PositionExit
from backtest.mechanism_sweep import (
    EpochState, step_epoch, epoch_delta_plus,
    DecayState, step_decay, decay_delta_plus,
    WindowState, step_window, window_delta_plus,
)


# ── Epoch tests ──

def test_epoch_state_frozen():
    s = EpochState(accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0,
                   epoch_start="2025-12-23", epoch_length_days=7)
    assert s.epoch_length_days == 7
    with pytest.raises(AttributeError):
        s.epoch_start = "2025-12-24"


def test_step_epoch_within_epoch():
    s0 = EpochState(accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0,
                    epoch_start="2025-12-20", epoch_length_days=7)
    e = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    s1 = step_epoch(s0, e)
    assert s1.accumulated_sum == pytest.approx(0.25 / 7200)
    assert s1.removed_pos_count == 1
    assert s1.epoch_start == "2025-12-20"


def test_step_epoch_crosses_boundary():
    s0 = EpochState(accumulated_sum=999.0, theta_sum=999.0, removed_pos_count=100,
                    epoch_start="2025-12-16", epoch_length_days=7)
    e = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    s1 = step_epoch(s0, e)
    assert s1.accumulated_sum == pytest.approx(0.25 / 7200)
    assert s1.removed_pos_count == 1
    assert s1.epoch_start == "2025-12-23"


def test_epoch_delta_plus():
    s = EpochState(accumulated_sum=0.04, theta_sum=0.01, removed_pos_count=10,
                   epoch_start="2025-12-20", epoch_length_days=7)
    dp = epoch_delta_plus(s)
    assert dp >= 0.0


# ── Decay tests ──

def test_decay_state_frozen():
    s = DecayState(accumulated_sum=1.0, theta_sum=0.5, effective_count=5.0,
                   last_update="2025-12-23", half_life_days=7.0)
    assert s.half_life_days == 7.0


def test_step_decay_applies_decay_before_accumulating():
    s0 = DecayState(accumulated_sum=1.0, theta_sum=0.5, effective_count=5.0,
                    last_update="2025-12-20", half_life_days=7.0)
    e = PositionExit(token_id=1, burn_date="2025-12-27", block_lifetime=7200, fee_share_x_k=0.5)
    s1 = step_decay(s0, e)
    decay = 0.5  # exp(-ln2 * 7/7)
    expected_acc = 1.0 * decay + 0.25 / 7200
    assert s1.accumulated_sum == pytest.approx(expected_acc, rel=1e-6)
    assert s1.effective_count == pytest.approx(5.0 * decay + 1.0, rel=1e-6)


def test_step_decay_same_day_no_decay():
    s0 = DecayState(accumulated_sum=1.0, theta_sum=0.5, effective_count=5.0,
                    last_update="2025-12-23", half_life_days=7.0)
    e = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    s1 = step_decay(s0, e)
    expected_acc = 1.0 + 0.25 / 7200
    assert s1.accumulated_sum == pytest.approx(expected_acc, rel=1e-6)


def test_decay_delta_plus():
    s = DecayState(accumulated_sum=0.04, theta_sum=0.01, effective_count=10.0,
                   last_update="2025-12-23", half_life_days=7.0)
    dp = decay_delta_plus(s)
    assert dp >= 0.0


# ── Window tests ──

def test_window_state_frozen():
    s = WindowState(entries=((0.1, 7200),), window_size=10)
    assert s.window_size == 10


def test_step_window_within_capacity():
    s0 = WindowState(entries=(), window_size=3)
    e1 = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    s1 = step_window(s0, e1)
    assert len(s1.entries) == 1


def test_step_window_evicts_oldest():
    s0 = WindowState(entries=((0.1, 7200), (0.2, 3600), (0.3, 1800)), window_size=3)
    e = PositionExit(token_id=4, burn_date="2025-12-24", block_lifetime=100, fee_share_x_k=0.9)
    s1 = step_window(s0, e)
    assert len(s1.entries) == 3
    assert s1.entries[0] == (0.2, 3600)
    assert s1.entries[-1] == (0.9, 100)


def test_window_delta_plus():
    s = WindowState(entries=((0.5, 7200), (0.3, 3600), (0.2, 1800)), window_size=10)
    dp = window_delta_plus(s)
    assert dp >= 0.0


def test_window_delta_plus_empty():
    s = WindowState(entries=(), window_size=10)
    assert window_delta_plus(s) == 0.0


from backtest.mechanism_sweep import (
    MechanismSeries, build_mechanism_series,
    SweepResult, compute_correlation, run_mechanism_sweep,
)


def test_mechanism_series_dataclass():
    s = MechanismSeries(
        days=("2025-12-23",), delta_plus_values=(0.15,),
        mechanism_name="epoch", params={"epoch_length_days": 7},
    )
    assert s.mechanism_name == "epoch"


def test_build_mechanism_series_epoch():
    exits = [
        PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=100, fee_share_x_k=0.9),
        PositionExit(token_id=2, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.1),
        PositionExit(token_id=3, burn_date="2025-12-24", block_lifetime=7200, fee_share_x_k=0.5),
    ]
    series = build_mechanism_series(exits, mechanism="epoch", epoch_length_days=7)
    assert series.mechanism_name == "epoch"
    assert len(series.days) == 2
    assert all(v >= 0 for v in series.delta_plus_values)


def test_build_mechanism_series_decay():
    exits = [
        PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=100, fee_share_x_k=0.9),
        PositionExit(token_id=2, burn_date="2025-12-24", block_lifetime=7200, fee_share_x_k=0.1),
    ]
    series = build_mechanism_series(exits, mechanism="decay", half_life_days=7.0)
    assert series.mechanism_name == "decay"
    assert len(series.days) == 2


def test_build_mechanism_series_window():
    exits = [
        PositionExit(token_id=i, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
        for i in range(5)
    ]
    series = build_mechanism_series(exits, mechanism="window", window_size=3)
    assert series.mechanism_name == "window"


def test_compute_correlation_perfect():
    assert compute_correlation([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_compute_correlation_inverse():
    assert compute_correlation([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)


def test_compute_correlation_short():
    assert compute_correlation([1], [1]) == 0.0


def test_run_mechanism_sweep_basic():
    exits = [
        PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=100, fee_share_x_k=0.9),
        PositionExit(token_id=2, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.1),
        PositionExit(token_id=3, burn_date="2025-12-24", block_lifetime=7200, fee_share_x_k=0.5),
        PositionExit(token_id=4, burn_date="2025-12-24", block_lifetime=3600, fee_share_x_k=0.5),
        PositionExit(token_id=5, burn_date="2025-12-25", block_lifetime=7200, fee_share_x_k=0.3),
    ]
    from backtest.oracle_comparison import build_dual_series
    dual = build_dual_series(exits)

    results = run_mechanism_sweep(
        exits=exits,
        daily_snapshot_baseline=list(dual.daily_snapshot_delta_plus),
        baseline_days=list(dual.days),
        epoch_lengths=[3, 7],
        half_lives=[3.0, 7.0],
        window_sizes=[3],
    )
    assert len(results) == 5  # 2 epoch + 2 decay + 1 window
    assert all(isinstance(r, SweepResult) for r in results)
