"""Tests for econometrics.types — frozen dataclasses."""
from __future__ import annotations

from econometrics.types import (
    LaggedPositionRow,
    QuartileRow,
    RobustDurationResult,
    SensitivityRow,
)


def test_lagged_position_row_frozen() -> None:
    row = LaggedPositionRow(
        burn_date="2026-01-01",
        mint_date="2025-12-25",
        blocklife=50400,
        max_a_t=0.22,
        mean_a_t=0.15,
        median_a_t=0.14,
        il_proxy=0.01,
    )
    assert row.max_a_t == 0.22
    assert row.mint_date == "2025-12-25"
    try:
        row.max_a_t = 0.5  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass


def test_robust_duration_result_has_robust_fields() -> None:
    r = RobustDurationResult(
        beta_a_t=-2.0, se_a_t=1.0, p_value_a_t=0.05,
        robust_se_a_t=1.2, robust_p_value_a_t=0.09,
        beta_il=1.0, se_il=0.5, p_value_il=0.05,
        robust_se_il=0.6, robust_p_value_il=0.09,
        beta_intercept=8.0,
        n_obs=500, r_squared=0.05,
        mean_blocklife=30000.0, mean_blocklife_hours=100.0,
    )
    assert r.robust_se_a_t == 1.2
    assert r.robust_p_value_a_t == 0.09


def test_sensitivity_row() -> None:
    s = SensitivityRow(lag=5, measure="max", beta_a_t=-1.5, robust_se_a_t=0.8, robust_p_value_a_t=0.06, n_obs=400)
    assert s.lag == 5
    assert s.measure == "max"


def test_quartile_row() -> None:
    q = QuartileRow(quartile=1, mean_blocklife_hours=200.0, mean_a_t=0.08, n_obs=150)
    assert q.quartile == 1
