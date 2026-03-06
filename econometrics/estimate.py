"""Structural logit estimation via JAX autodiff.

Estimates: P(Exit=1) = σ(β₀ + β₁·A_T + β₂·SwapCount + β₃·JIT_lag)
where β₁ is the concentration risk premium (parameter of interest).

Uses JAX for exact gradients and Hessian-based standard errors.
"""
from __future__ import annotations

import jax
import jax.numpy as jnp
import jax.scipy.optimize
import jax.scipy.stats as jstats
from jax import Array

from econometrics.types import EstimationResult, FEE_REVENUE_PROXY


def nll(params: Array, X: Array, y: Array) -> Array:
    """Negative log-likelihood for binary logit.

    Args:
        params: Coefficient vector [β₀, β₁, β₂, β₃].
        X: Design matrix (n, 4) with intercept column.
        y: Binary outcome vector (n,).
    """
    logits = X @ params
    log_p = -jax.nn.softplus(-logits)
    log_1_minus_p = -jax.nn.softplus(logits)
    return -jnp.mean(y * log_p + (1.0 - y) * log_1_minus_p)


def structural_logit(
    exit: Array,
    a_t: Array,
    jit_lag: Array,
    swap_count: Array,
) -> EstimationResult:
    """Estimate structural logit of LP exit decision.

    Args:
        exit: Binary outcome (1 = LP exits), shape (n,).
        a_t: Fee concentration index at exit event, shape (n,).
        jit_lag: Lagged JIT count (instrument as control), shape (n,).
        swap_count: Daily swap count (fee revenue proxy), shape (n,).

    Returns:
        EstimationResult with β₃ (concentration), SEs, p-values, WTP.
    """
    n = exit.shape[0]
    ones = jnp.ones(n)
    X = jnp.column_stack([ones, a_t, swap_count, jit_lag])

    init_params = jnp.zeros(4)
    result = jax.scipy.optimize.minimize(
        nll, init_params, args=(X, exit), method="BFGS"
    )
    params = result.x

    hess = jax.hessian(nll)(params, X, exit)
    cov = jnp.linalg.inv(hess * n) / n
    ses = jnp.sqrt(jnp.diag(jnp.abs(cov)))

    z_scores = params / ses
    p_values = 2.0 * jstats.norm.sf(jnp.abs(z_scores))

    nll_fitted = float(nll(params, X, exit))
    null_params = jnp.zeros(4).at[0].set(params[0])
    nll_null = float(nll(null_params, X, exit))
    pseudo_r2 = 1.0 - nll_fitted / nll_null if nll_null > 0 else 0.0

    ll = -nll_fitted * n

    k = 4
    aic = 2 * k - 2 * ll

    beta_1 = float(params[1])
    mean_a_t = float(jnp.mean(a_t))
    wtp = beta_1 * mean_a_t * FEE_REVENUE_PROXY

    return EstimationResult(
        beta_concentration=beta_1,
        se_concentration=float(ses[1]),
        p_value_concentration=float(p_values[1]),
        beta_swap=float(params[2]),
        beta_jit_lag=float(params[3]),
        n_obs=n,
        pseudo_r2=pseudo_r2,
        wtp_mean=max(wtp, 0.0),
        log_likelihood=ll,
        aic=aic,
    )
