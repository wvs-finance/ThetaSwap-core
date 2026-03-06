"""Tests for exit hazard (logit) estimation."""
from __future__ import annotations

import math

from econometrics.hazard import (
    exit_lag_sensitivity,
    exit_quartile_analysis,
    logit_mle,
    marginal_effect_at_means,
)
from econometrics.types import ExitPanelRow, LogitResult, MarginalEffect


def _make_panel(n_days: int = 20, n_positions: int = 50) -> list[ExitPanelRow]:
    """Synthetic panel where higher A_T correlates with exit."""
    import random
    random.seed(42)
    rows: list[ExitPanelRow] = []
    for pos in range(n_positions):
        lifetime = random.randint(3, n_days)
        burn_day = random.randint(lifetime, n_days)
        mint_day = burn_day - lifetime
        for d in range(mint_day, burn_day + 1):
            if d < 0 or d >= n_days:
                continue
            a_t = 0.10 + 0.005 * d + random.gauss(0, 0.02)
            il = 0.01 + random.gauss(0, 0.005)
            exited = 1 if d == burn_day else 0
            rows.append(ExitPanelRow(
                position_idx=pos,
                day=f"2025-12-{d + 1:02d}",
                exited=exited,
                a_t_lagged=max(0.01, a_t),
                il=max(0.0, il),
                log_age=math.log(max(1, d - mint_day)),
            ))
    return rows


def test_logit_mle_returns_logit_result() -> None:
    panel = _make_panel()
    result = logit_mle(panel)
    assert isinstance(result, LogitResult)
    assert result.n_obs == len(panel)
    assert result.n_exits == sum(1 for r in panel if r.exited == 1)
    assert result.n_clusters > 0
    assert result.log_likelihood < 0.0
    assert result.aic > 0.0


def test_logit_mle_clustered_se_positive() -> None:
    panel = _make_panel()
    result = logit_mle(panel)
    assert result.cluster_se_a_t > 0.0
    assert math.isfinite(result.cluster_se_a_t)
    assert result.cluster_se_il > 0.0


def test_logit_mle_pseudo_r2_bounded() -> None:
    panel = _make_panel()
    result = logit_mle(panel)
    assert 0.0 <= result.pseudo_r2 < 1.0


def test_logit_mle_mean_exit_prob_reasonable() -> None:
    panel = _make_panel()
    result = logit_mle(panel)
    assert 0.0 < result.mean_exit_prob < 1.0


def test_marginal_effect_at_means_returns_type() -> None:
    panel = _make_panel()
    result = logit_mle(panel)
    me = marginal_effect_at_means(result, delta_a_t=0.10)
    assert isinstance(me, MarginalEffect)
    assert me.delta_a_t == 0.10
    assert math.isfinite(me.marginal_effect)
    assert math.isfinite(me.implied_premium_usd)


def test_exit_quartile_analysis_four_quartiles() -> None:
    panel = _make_panel()
    quartiles = exit_quartile_analysis(panel)
    assert len(quartiles) == 4
    assert all(q.quartile in (1, 2, 3, 4) for q in quartiles)


def test_logit_mle_quadratic_returns_type() -> None:
    """Quadratic logit returns QuadraticLogitResult with turning point."""
    from econometrics.data import DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS
    from econometrics.ingest import build_exit_panel_deviation
    from econometrics.hazard import logit_mle_quadratic
    from econometrics.types import QuadraticLogitResult

    panel = build_exit_panel_deviation(
        RAW_POSITIONS, DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, lag_days=1
    )
    result = logit_mle_quadratic(panel)
    assert isinstance(result, QuadraticLogitResult)
    assert result.n_obs > 0
    assert result.n_exits > 0
    assert result.beta_quadratic > 0  # inverted-U: quadratic term positive
    assert result.cluster_p_quadratic < 0.10  # significant


def test_exit_lag_sensitivity_returns_results() -> None:
    from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS
    rows = exit_lag_sensitivity(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP, lags=[1, 2])
    assert len(rows) >= 1
    assert all(hasattr(r, 'lag') for r in rows)
