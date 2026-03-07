"""Duration model: does fee concentration risk shorten LP position lifetimes?

Model: log(blocklife) = beta_0 + beta_1 * A_T + beta_2 * IL + eps

beta_1 < 0 -> higher concentration drives earlier exit (insurance demand signal).
HC1 heteroskedasticity-robust standard errors for reliable inference.
"""
from __future__ import annotations

import math

import jax
import jax.numpy as jnp
import jax.scipy.stats as jstats
from jax import Array

from econometrics.ingest import build_lagged_positions
from econometrics.types import (
    LaggedPositionRow,
    QuartileRow,
    RobustDurationResult,
    SensitivityRow,
)

BLOCKS_PER_HOUR: float = 300.0


def _get_a_t(pos: LaggedPositionRow, measure: str) -> float:
    """Extract A_T value based on measure type."""
    if measure == "max":
        return pos.max_a_t
    elif measure == "mean":
        return pos.mean_a_t
    elif measure == "median":
        return pos.median_a_t
    raise ValueError(f"Unknown measure: {measure}")


def duration_model_robust(
    positions: list[LaggedPositionRow],
    measure: str = "max",
) -> RobustDurationResult:
    """OLS duration model with HC1 robust standard errors.

    Implements: log(blocklife_i) = b0 + b1*A_T_i + b2*IL_i + e_i
    HC1: Var(b_hat) = (X'X)^{-1} (sum e_i^2 x_i x_i') (X'X)^{-1} * n/(n-k)
    """
    n = len(positions)
    log_bl = jnp.array([jnp.log(float(p.blocklife)) for p in positions])
    a_t = jnp.array([_get_a_t(p, measure) for p in positions])
    il = jnp.array([p.il_proxy for p in positions])
    ones = jnp.ones(n)

    X = jnp.column_stack([ones, a_t, il])
    k = 3

    # OLS: beta = (X'X)^{-1} X'y
    XtX = X.T @ X
    Xty = X.T @ log_bl
    params = jnp.linalg.solve(XtX, Xty)

    # Residuals and R^2
    y_hat = X @ params
    residuals = log_bl - y_hat
    ss_res = float(jnp.sum(residuals ** 2))
    ss_tot = float(jnp.sum((log_bl - jnp.mean(log_bl)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # OLS SEs: sigma^2 (X'X)^{-1}
    sigma2 = ss_res / (n - k)
    XtX_inv = jnp.linalg.inv(XtX)
    ols_cov = sigma2 * XtX_inv
    ols_ses = jnp.sqrt(jnp.diag(ols_cov))

    # HC1 robust SEs: (X'X)^{-1} (sum e_i^2 x_i x_i') (X'X)^{-1} * n/(n-k)
    meat = jnp.zeros((k, k))
    for i in range(n):
        xi = X[i, :].reshape(-1, 1)
        meat = meat + (float(residuals[i]) ** 2) * (xi @ xi.T)
    robust_cov = XtX_inv @ meat @ XtX_inv * (n / (n - k))
    robust_ses = jnp.sqrt(jnp.diag(jnp.abs(robust_cov)))

    # p-values (two-sided, normal approximation)
    t_stats_ols = params / ols_ses
    p_ols = 2.0 * jstats.norm.sf(jnp.abs(t_stats_ols))
    t_stats_robust = params / robust_ses
    p_robust = 2.0 * jstats.norm.sf(jnp.abs(t_stats_robust))

    mean_bl = float(jnp.mean(jnp.array([float(p.blocklife) for p in positions])))

    return RobustDurationResult(
        beta_a_t=float(params[1]),
        se_a_t=float(ols_ses[1]),
        p_value_a_t=float(p_ols[1]),
        robust_se_a_t=float(robust_ses[1]),
        robust_p_value_a_t=float(p_robust[1]),
        beta_il=float(params[2]),
        se_il=float(ols_ses[2]),
        p_value_il=float(p_ols[2]),
        robust_se_il=float(robust_ses[2]),
        robust_p_value_il=float(p_robust[2]),
        beta_intercept=float(params[0]),
        n_obs=n,
        r_squared=r_squared,
        mean_blocklife=mean_bl,
        mean_blocklife_hours=mean_bl / BLOCKS_PER_HOUR,
    )


def economic_magnitude(
    result: RobustDurationResult,
    delta_a_t: float = 0.10,
) -> dict[str, float]:
    """Translate beta_1 into economic quantities.

    A delta_a_t increase in max A_T changes blocklife by exp(beta_1 * delta_a_t) factor.
    """
    factor = math.exp(result.beta_a_t * delta_a_t)
    hours_change = result.mean_blocklife_hours * (factor - 1.0)
    return {
        "delta_a_t": delta_a_t,
        "factor": factor,
        "hours_shortened": abs(hours_change),
        "pct_change": (factor - 1.0) * 100,
        "mean_blocklife_hours": result.mean_blocklife_hours,
    }


def quartile_analysis(
    positions: list[LaggedPositionRow],
    measure: str = "max",
) -> list[QuartileRow]:
    """Split positions into 4 quartiles by A_T, report mean blocklife."""
    sorted_pos = sorted(positions, key=lambda p: _get_a_t(p, measure))
    n = len(sorted_pos)
    q_size = n // 4
    return [
        QuartileRow(
            quartile=q + 1,
            mean_blocklife_hours=sum(p.blocklife for p in chunk) / len(chunk) / BLOCKS_PER_HOUR,
            mean_a_t=sum(_get_a_t(p, measure) for p in chunk) / len(chunk),
            n_obs=len(chunk),
        )
        for q in range(4)
        for chunk in [sorted_pos[q * q_size : ((q + 1) * q_size if q < 3 else n)]]
        if chunk
    ]


def nested_models(
    positions: list[LaggedPositionRow],
    measure: str = "max",
) -> dict[str, RobustDurationResult]:
    """Run full, A_T-only, and IL-only models for comparison."""
    full = duration_model_robust(positions, measure=measure)

    # A_T-only: zero out IL
    a_t_only_pos = [
        LaggedPositionRow(
            burn_date=p.burn_date, mint_date=p.mint_date, blocklife=p.blocklife,
            max_a_t=p.max_a_t, mean_a_t=p.mean_a_t, median_a_t=p.median_a_t,
            il_proxy=0.0,
        )
        for p in positions
    ]
    a_t_only = duration_model_robust(a_t_only_pos, measure=measure)

    # IL-only: zero out A_T
    il_only_pos = [
        LaggedPositionRow(
            burn_date=p.burn_date, mint_date=p.mint_date, blocklife=p.blocklife,
            max_a_t=0.0, mean_a_t=0.0, median_a_t=0.0,
            il_proxy=p.il_proxy,
        )
        for p in positions
    ]
    il_only = duration_model_robust(il_only_pos, measure=measure)

    return {"full": full, "a_t_only": a_t_only, "il_only": il_only}


def sensitivity_sweep(
    raw_positions: list[tuple[str, int, float]],
    daily_at_map: dict[str, float],
    il_map: dict[str, float],
    lags: list[int] | None = None,
    measures: list[str] | None = None,
) -> list[SensitivityRow]:
    """Sweep over lag windows and A_T measures."""
    if lags is None:
        lags = [0, 1, 2, 3, 4, 5, 6, 7, 10]
    if measures is None:
        measures = ["max", "mean", "median"]

    rows: list[SensitivityRow] = []
    for lag in lags:
        positions = build_lagged_positions(raw_positions, daily_at_map, il_map, lag)
        if len(positions) < 10:
            continue
        for measure in measures:
            result = duration_model_robust(positions, measure=measure)
            rows.append(SensitivityRow(
                lag=lag,
                measure=measure,
                beta_a_t=result.beta_a_t,
                robust_se_a_t=result.robust_se_a_t,
                robust_p_value_a_t=result.robust_p_value_a_t,
                n_obs=result.n_obs,
            ))
    return rows
