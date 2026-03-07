"""Exit hazard model: does fee concentration risk drive LP exits?

Model: P(exit_i,t = 1) = sigma(b0 + b1*A_T,t-lag + b2*IL_t + b3*log(age_i,t))

b1 > 0 -> higher concentration increases exit probability (insurance demand).
Day-clustered sandwich SEs for reliable inference.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Final

import jax
import jax.numpy as jnp
import jax.scipy.stats as jstats
from jax import Array

from econometrics.ingest import build_exit_panel
from econometrics.types import (
    ExitPanelRow,
    LogitResult,
    MarginalEffect,
    QuadraticLogitResult,
    QuartileRow,
    SensitivityRow,
)

FEE_REVENUE_PER_HOUR: Final[float] = 100.0
AVG_REMAINING_HOURS: Final[float] = 48.0


def _panel_to_arrays(
    panel: list[ExitPanelRow],
) -> tuple[Array, Array, list[str]]:
    """Convert panel rows to JAX arrays (X, y) and day list for clustering."""
    n = len(panel)
    y = jnp.array([float(r.exited) for r in panel])
    X = jnp.column_stack([
        jnp.ones(n),
        jnp.array([r.a_t_lagged for r in panel]),
        jnp.array([r.il for r in panel]),
        jnp.array([r.log_age for r in panel]),
    ])
    days = [r.day for r in panel]
    return X, y, days


def _neg_log_likelihood(params: Array, X: Array, y: Array) -> float:
    """Negative log-likelihood for logit model."""
    z = X @ params
    log_p = -jax.nn.softplus(-z)
    log_1mp = -jax.nn.softplus(z)
    return -float(jnp.sum(y * log_p + (1.0 - y) * log_1mp))


def _hessian_and_scores(
    params: Array, X: Array, y: Array,
) -> tuple[Array, Array]:
    """Compute Hessian and per-observation score vectors for logit."""
    z = X @ params
    p = jax.nn.sigmoid(z)
    residuals = y - p
    scores = residuals[:, None] * X
    w = p * (1.0 - p)
    H = -(X.T * w[None, :]) @ X
    return H, scores


def _newton_raphson(
    X: Array, y: Array, max_iter: int = 50, tol: float = 1e-8,
) -> Array:
    """Newton-Raphson (IRLS) for logit — exact Hessian, guaranteed convergence."""
    k = X.shape[1]
    params = jnp.zeros(k)
    for _ in range(max_iter):
        z = X @ params
        p = jax.nn.sigmoid(z)
        residuals = y - p
        w = p * (1.0 - p) + 1e-12  # ridge for numerical stability
        H = -(X.T * w[None, :]) @ X
        grad = X.T @ residuals
        step = jnp.linalg.solve(-H, grad)
        params = params + step
        if float(jnp.max(jnp.abs(step))) < tol:
            break
    return params


def logit_mle(panel: list[ExitPanelRow]) -> LogitResult:
    """Logit MLE with day-clustered sandwich standard errors."""
    X, y, days = _panel_to_arrays(panel)
    n, k = X.shape

    params = _newton_raphson(X, y)

    ll = -_neg_log_likelihood(params, X, y)
    ll_null = -_neg_log_likelihood(jnp.zeros(k), X, y)
    pseudo_r2 = 1.0 - ll / ll_null if ll_null != 0 else 0.0

    H, scores = _hessian_and_scores(params, X, y)
    H_inv = jnp.linalg.inv(H)

    mle_cov = -H_inv
    mle_ses = jnp.sqrt(jnp.abs(jnp.diag(mle_cov)))

    unique_days = sorted(set(days))
    n_clusters = len(unique_days)
    meat = jnp.zeros((k, k))
    for day_label in unique_days:
        mask = jnp.array([1.0 if d == day_label else 0.0 for d in days])
        g_t = jnp.sum(scores * mask[:, None], axis=0)
        meat = meat + jnp.outer(g_t, g_t)

    correction = (n_clusters / (n_clusters - 1)) * (n / (n - k)) if n_clusters > 1 else 1.0
    cluster_cov = H_inv @ meat @ H_inv * correction
    cluster_ses = jnp.sqrt(jnp.abs(jnp.diag(cluster_cov)))

    t_mle = params / mle_ses
    p_mle = 2.0 * jstats.norm.sf(jnp.abs(t_mle))
    t_cluster = params / cluster_ses
    p_cluster = 2.0 * jstats.norm.sf(jnp.abs(t_cluster))

    p_hat = jax.nn.sigmoid(X @ params)
    mean_p = float(jnp.mean(p_hat))

    return LogitResult(
        beta_a_t=float(params[1]),
        beta_il=float(params[2]),
        beta_log_age=float(params[3]),
        beta_intercept=float(params[0]),
        se_a_t=float(mle_ses[1]),
        se_il=float(mle_ses[2]),
        se_log_age=float(mle_ses[3]),
        se_intercept=float(mle_ses[0]),
        cluster_se_a_t=float(cluster_ses[1]),
        cluster_se_il=float(cluster_ses[2]),
        cluster_se_log_age=float(cluster_ses[3]),
        cluster_se_intercept=float(cluster_ses[0]),
        p_value_a_t=float(p_mle[1]),
        cluster_p_value_a_t=float(p_cluster[1]),
        n_obs=n,
        n_exits=int(jnp.sum(y)),
        n_clusters=n_clusters,
        log_likelihood=ll,
        aic=-2.0 * ll + 2.0 * k,
        pseudo_r2=pseudo_r2,
        mean_exit_prob=mean_p,
    )


def _panel_to_quadratic_arrays(
    panel: list[ExitPanelRow],
) -> tuple[Array, Array, list[str]]:
    """Convert panel rows to JAX arrays with quadratic treatment term."""
    n = len(panel)
    y = jnp.array([float(r.exited) for r in panel])
    a_t = jnp.array([r.a_t_lagged for r in panel])
    X = jnp.column_stack([
        jnp.ones(n),
        a_t,
        a_t ** 2,
        jnp.array([r.il for r in panel]),
        jnp.array([r.log_age for r in panel]),
    ])
    days = [r.day for r in panel]
    return X, y, days


def logit_mle_quadratic(panel: list[ExitPanelRow]) -> QuadraticLogitResult:
    """Logit MLE with quadratic treatment: b1*dev + b2*dev^2 + b3*IL + b4*log(age).

    Captures inverted-U relationship between fee concentration and exits.
    """
    X, y, days = _panel_to_quadratic_arrays(panel)
    n, k = X.shape

    params = _newton_raphson(X, y)

    ll = -_neg_log_likelihood(params, X, y)
    ll_null = -_neg_log_likelihood(jnp.zeros(k), X, y)
    pseudo_r2 = 1.0 - ll / ll_null if ll_null != 0 else 0.0

    H, scores = _hessian_and_scores(params, X, y)
    H_inv = jnp.linalg.inv(H)

    # Day-clustered sandwich SEs
    unique_days = sorted(set(days))
    n_clusters = len(unique_days)
    meat = jnp.zeros((k, k))
    for day_label in unique_days:
        mask = jnp.array([1.0 if d == day_label else 0.0 for d in days])
        g_t = jnp.sum(scores * mask[:, None], axis=0)
        meat = meat + jnp.outer(g_t, g_t)

    correction = (n_clusters / (n_clusters - 1)) * (n / (n - k)) if n_clusters > 1 else 1.0
    cluster_cov = H_inv @ meat @ H_inv * correction
    cluster_ses = jnp.sqrt(jnp.abs(jnp.diag(cluster_cov)))

    t_cluster = params / cluster_ses
    p_cluster = 2.0 * jstats.norm.sf(jnp.abs(t_cluster))

    # Turning point: -beta_linear / (2 * beta_quadratic)
    beta_lin = float(params[1])
    beta_quad = float(params[2])
    turning_point = -beta_lin / (2.0 * beta_quad) if beta_quad != 0.0 else float('inf')

    p_hat = jax.nn.sigmoid(X @ params)
    mean_p = float(jnp.mean(p_hat))

    return QuadraticLogitResult(
        beta_linear=beta_lin,
        beta_quadratic=beta_quad,
        beta_il=float(params[3]),
        beta_log_age=float(params[4]),
        beta_intercept=float(params[0]),
        cluster_se_linear=float(cluster_ses[1]),
        cluster_se_quadratic=float(cluster_ses[2]),
        cluster_p_linear=float(p_cluster[1]),
        cluster_p_quadratic=float(p_cluster[2]),
        turning_point=turning_point,
        n_obs=n,
        n_exits=int(jnp.sum(y)),
        n_clusters=n_clusters,
        log_likelihood=ll,
        aic=-2.0 * ll + 2.0 * k,
        pseudo_r2=pseudo_r2,
        mean_exit_prob=mean_p,
    )


def marginal_effect_at_means(
    result: LogitResult,
    delta_a_t: float = 0.10,
    fee_revenue_per_hour: float = FEE_REVENUE_PER_HOUR,
    avg_remaining_hours: float = AVG_REMAINING_HOURS,
) -> MarginalEffect:
    """Translate beta_1 into insurance pricing quantities."""
    p_bar = result.mean_exit_prob
    me = result.beta_a_t * p_bar * (1.0 - p_bar)
    prob_inc = me * delta_a_t
    hours_lost = abs(prob_inc) * avg_remaining_hours
    premium = hours_lost * fee_revenue_per_hour

    return MarginalEffect(
        marginal_effect=me,
        delta_a_t=delta_a_t,
        prob_increase=prob_inc,
        hours_lost=hours_lost,
        implied_premium_usd=premium,
        mean_exit_prob=p_bar,
    )


def exit_quartile_analysis(panel: list[ExitPanelRow]) -> list[QuartileRow]:
    """Split panel days into 4 quartiles by A_T, report exit rate per quartile."""
    day_at: dict[str, float] = {}
    day_exits: dict[str, int] = defaultdict(int)
    day_total: dict[str, int] = defaultdict(int)

    for r in panel:
        day_at[r.day] = r.a_t_lagged
        day_exits[r.day] += r.exited
        day_total[r.day] += 1

    sorted_days = sorted(day_at.keys(), key=lambda d: day_at[d])
    n = len(sorted_days)
    q_size = n // 4

    quartiles: list[QuartileRow] = []
    for q in range(4):
        start = q * q_size
        end = (q + 1) * q_size if q < 3 else n
        chunk = sorted_days[start:end]
        if not chunk:
            continue
        total_exits = sum(day_exits[d] for d in chunk)
        total_obs = sum(day_total[d] for d in chunk)
        exit_rate = total_exits / total_obs if total_obs > 0 else 0.0
        mean_at = sum(day_at[d] for d in chunk) / len(chunk)
        quartiles.append(QuartileRow(
            quartile=q + 1,
            mean_blocklife_hours=exit_rate * 100,
            mean_a_t=mean_at,
            n_obs=total_obs,
        ))

    return quartiles


def exit_lag_sensitivity(
    raw_positions: list[tuple[str, int, float]],
    daily_at_map: dict[str, float],
    il_map: dict[str, float],
    lags: list[int] | None = None,
) -> list[SensitivityRow]:
    """Sweep over lag windows and report beta_1 stability."""
    if lags is None:
        lags = [1, 2, 3, 5, 7]

    rows: list[SensitivityRow] = []
    for lag in lags:
        panel = build_exit_panel(raw_positions, daily_at_map, il_map, lag_days=lag)
        if len(panel) < 50:
            continue
        result = logit_mle(panel)
        rows.append(SensitivityRow(
            lag=lag,
            measure="logit",
            beta_a_t=result.beta_a_t,
            robust_se_a_t=result.cluster_se_a_t,
            robust_p_value_a_t=result.cluster_p_value_a_t,
            n_obs=result.n_obs,
        ))
    return rows
