"""Tests for econometrics.types — frozen dataclasses."""
from __future__ import annotations

from econometrics.types import (
    ExitPanelRow,
    LaggedPositionRow,
    LogitResult,
    MarginalEffect,
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


def test_exit_panel_row_construction() -> None:
    row = ExitPanelRow(
        position_idx=0, day="2025-12-10", exited=1,
        a_t_lagged=0.13, il=0.012, log_age=2.3,
    )
    assert row.exited in (0, 1)
    assert row.a_t_lagged == 0.13
    assert row.log_age == 2.3


def test_logit_result_construction() -> None:
    result = LogitResult(
        beta_a_t=0.5, beta_il=-0.3, beta_log_age=-0.1, beta_intercept=-3.0,
        se_a_t=0.1, se_il=0.2, se_log_age=0.05, se_intercept=0.5,
        cluster_se_a_t=0.15, cluster_se_il=0.25, cluster_se_log_age=0.08, cluster_se_intercept=0.6,
        p_value_a_t=0.001, cluster_p_value_a_t=0.003,
        n_obs=5000, n_exits=600, n_clusters=41,
        log_likelihood=-800.0, aic=1608.0, pseudo_r2=0.05, mean_exit_prob=0.12,
    )
    assert result.beta_a_t == 0.5
    assert result.n_clusters == 41


def test_marginal_effect_construction() -> None:
    me = MarginalEffect(
        marginal_effect=0.05, delta_a_t=0.10, prob_increase=0.005,
        hours_lost=24.0, implied_premium_usd=2.40, mean_exit_prob=0.12,
    )
    assert me.marginal_effect == 0.05
    assert me.implied_premium_usd == 2.40
