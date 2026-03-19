"""Tests for JAX structural logit estimation."""
from __future__ import annotations

import jax.numpy as jnp
import jax.random as jr
from econometrics.estimate import structural_logit, nll
from econometrics.types import EstimationResult


def test_nll_perfect_separation_low_loss() -> None:
    """When model perfectly predicts, NLL should be near zero."""
    params = jnp.array([0.0, 10.0, 0.0, 0.0])
    X = jnp.array([[1.0, 1.0, 0.0, 0.0],
                    [1.0, -1.0, 0.0, 0.0]])
    y = jnp.array([1.0, 0.0])
    loss = float(nll(params, X, y))
    assert loss < 0.1


def test_nll_random_params_positive() -> None:
    """NLL should always be positive."""
    params = jnp.array([0.5, -0.3, 0.1, 0.2])
    X = jnp.ones((5, 4))
    y = jnp.array([1.0, 0.0, 1.0, 0.0, 1.0])
    loss = float(nll(params, X, y))
    assert loss > 0


def test_positive_a_t_coefficient_on_synthetic_data() -> None:
    """On synthetic data where high A_T → exit, β₃ should be positive."""
    key = jr.PRNGKey(42)
    n = 500
    k1, k2, k3, k4 = jr.split(key, 4)

    a_t = jr.uniform(k1, (n,))
    swap_count = jr.poisson(k2, 50.0, (n,)).astype(jnp.float32)
    jit_lag = jr.poisson(k3, 3.0, (n,)).astype(jnp.float32)

    latent = 2.0 * a_t - 1.0 + jr.logistic(k4, (n,))
    exit_var = (latent > 0).astype(jnp.float32)

    result = structural_logit(
        exit=exit_var,
        a_t=a_t,
        jit_lag=jit_lag,
        swap_count=swap_count,
    )
    assert isinstance(result, EstimationResult)
    assert result.beta_concentration > 0
    assert result.p_value_concentration < 0.05


def test_estimation_result_has_wtp() -> None:
    """Result should include non-negative dollar WTP estimate."""
    key = jr.PRNGKey(123)
    n = 300
    k1, k2, k3, k4 = jr.split(key, 4)

    a_t = jr.uniform(k1, (n,))
    exit_var = (a_t + jr.logistic(k2, (n,)) * 0.5 > 0.5).astype(jnp.float32)

    result = structural_logit(
        exit=exit_var,
        a_t=a_t,
        jit_lag=jr.poisson(k3, 2.0, (n,)).astype(jnp.float32),
        swap_count=jr.poisson(k4, 40.0, (n,)).astype(jnp.float32),
    )
    assert result.wtp_mean >= 0


def test_all_zeros_exit_returns_result() -> None:
    """Edge case: no exits. Should still return a result (β₃ ≈ 0)."""
    n = 100
    result = structural_logit(
        exit=jnp.zeros(n),
        a_t=jnp.ones(n) * 0.5,
        jit_lag=jnp.ones(n),
        swap_count=jnp.ones(n) * 10,
    )
    assert isinstance(result, EstimationResult)
    assert result.n_obs == n
