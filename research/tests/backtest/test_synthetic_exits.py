"""Tests for synthetic exit generation calibration."""
from __future__ import annotations

import math

from backtest.oracle_comparison import build_dual_series
from backtest.synthetic_exits import (
    _delta_plus_from_concentration,
    build_from_raw_positions,
    calibrate_concentration,
    generate_synthetic_day,
)
from econometrics.data import DAILY_AT_MAP, DAILY_AT_NULL_MAP, RAW_POSITIONS


def test_uniform_concentration_zero_delta() -> None:
    """Uniform fee shares (c=1/N) should produce Δ⁺=0."""
    bls = (100, 200, 300)
    dp = _delta_plus_from_concentration(1.0 / 3.0, bls)
    assert abs(dp) < 1e-15


def test_concentration_monotonic() -> None:
    """Higher concentration → higher Δ⁺."""
    bls = (10, 1000, 5000)
    dp_low = _delta_plus_from_concentration(0.3, bls)
    dp_high = _delta_plus_from_concentration(0.9, bls)
    assert dp_high > dp_low


def test_calibrate_zero_target() -> None:
    """Target Δ⁺=0 returns uniform concentration 1/N."""
    bls = (100, 200, 300)
    c = calibrate_concentration(0.0, bls)
    assert abs(c - 1.0 / 3.0) < 1e-10


def test_calibrate_reproduces_target() -> None:
    """Calibrated c reproduces the target Δ⁺ within tolerance."""
    bls = (10, 1000, 5000, 20000)
    target = 0.05
    c = calibrate_concentration(target, bls)
    actual = _delta_plus_from_concentration(c, bls)
    assert abs(actual - target) < 1e-9


def test_generate_synthetic_day_count() -> None:
    """Generates correct number of exits."""
    exits, c = generate_synthetic_day("2025-12-23", 0.1, (10, 100, 1000), 0)
    assert len(exits) == 3
    assert all(e.burn_date == "2025-12-23" for e in exits)


def test_full_stream_reproduces_daily_at_map() -> None:
    """Synthetic stream matches DAILY_AT_MAP Δ⁺ within 1e-8."""
    stream = build_from_raw_positions(RAW_POSITIONS, DAILY_AT_MAP, DAILY_AT_NULL_MAP)
    dual = build_dual_series(list(stream.exits))

    target_dict = {
        d: max(0.0, DAILY_AT_MAP.get(d, 0) - DAILY_AT_NULL_MAP.get(d, 0))
        for d in stream.concentration_params
    }
    synth_dict = dict(zip(dual.days, dual.daily_snapshot_delta_plus))

    for day in stream.concentration_params:
        target = target_dict[day]
        synth = synth_dict.get(day, 0.0)
        assert abs(synth - target) < 1e-8, f"Day {day}: target={target}, synth={synth}"
