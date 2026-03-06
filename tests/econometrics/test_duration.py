"""Tests for econometrics.duration — OLS + HC1 robust SEs."""
from __future__ import annotations

from econometrics.duration import (
    duration_model_robust,
    economic_magnitude,
    nested_models,
    quartile_analysis,
    sensitivity_sweep,
)
from econometrics.types import LaggedPositionRow


def _make_positions(n: int = 100) -> list[LaggedPositionRow]:
    """Synthetic data: higher max_a_t -> shorter blocklife."""
    import random
    random.seed(42)
    positions = []
    for i in range(n):
        a_t = 0.05 + (i / n) * 0.20  # 0.05 to 0.25
        # log(bl) = 10 - 5*a_t + noise
        noise = random.gauss(0, 0.5)
        log_bl = 10.0 - 5.0 * a_t + noise
        bl = max(2, int(2.718 ** log_bl))
        positions.append(LaggedPositionRow(
            burn_date=f"2026-01-{(i % 28) + 1:02d}",
            mint_date=f"2025-12-{(i % 28) + 1:02d}",
            blocklife=bl,
            max_a_t=a_t,
            mean_a_t=a_t * 0.8,
            median_a_t=a_t * 0.85,
            il_proxy=random.gauss(0.01, 0.005),
        ))
    return positions


def test_duration_model_robust_returns_result() -> None:
    positions = _make_positions()
    result = duration_model_robust(positions, measure="max")
    assert result.n_obs == 100
    assert result.beta_a_t < 0  # negative effect by construction
    assert result.robust_se_a_t > 0
    assert result.robust_p_value_a_t >= 0


def test_robust_se_differs_from_ols_se() -> None:
    positions = _make_positions()
    result = duration_model_robust(positions, measure="max")
    # Robust and OLS SEs should differ (heteroskedasticity present)
    assert result.se_a_t != result.robust_se_a_t


def test_economic_magnitude() -> None:
    positions = _make_positions()
    result = duration_model_robust(positions, measure="max")
    mag = economic_magnitude(result, delta_a_t=0.10)
    assert "factor" in mag
    assert "hours_shortened" in mag
    assert mag["factor"] < 1.0  # shortens (beta < 0)


def test_quartile_analysis() -> None:
    positions = _make_positions()
    quartiles = quartile_analysis(positions, measure="max")
    assert len(quartiles) == 4
    assert quartiles[0].quartile == 1
    assert quartiles[3].quartile == 4
    # Q1 (low A_T) should have longer blocklife than Q4 (high A_T)
    assert quartiles[0].mean_blocklife_hours > quartiles[3].mean_blocklife_hours


def test_nested_models() -> None:
    positions = _make_positions()
    models = nested_models(positions, measure="max")
    assert "full" in models
    assert "a_t_only" in models
    assert "il_only" in models
    assert models["full"].n_obs == models["a_t_only"].n_obs


def test_sensitivity_sweep() -> None:
    from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS
    rows = sensitivity_sweep(
        RAW_POSITIONS, DAILY_AT_MAP, IL_MAP,
        lags=[0, 3, 5], measures=["max", "mean"],
    )
    # 3 lags * 2 measures = 6 rows (some may have 0 obs if excluded)
    assert len(rows) <= 6
    assert all(r.lag in [0, 3, 5] for r in rows)
    assert all(r.measure in ["max", "mean"] for r in rows)
