"""Pure-function estimation library for Task 11.O Rev-2 Phase 5b (Analytics Reporter).

Purpose
-------
Consume the 14 Phase-5a panel parquets at
``contracts/.scratch/2026-04-25-task110-rev2-data/`` and produce per-row OLS+HAC
coefficient estimates, the gate-bearing T3b verdict (one-sided 90%
``β̂ − 1.28·HAC SE > 0``), bootstrap reconciliation, Student-t innovation
refit, and the spec §7 specification tests T1–T7.

This module is the estimation kernel; the orchestration script
(``scripts.run_phase5_analytics`` or a notebook) calls these free functions and
assembles the per-row results into the four ``.scratch`` markdown artifacts +
``gate_verdict.json``.

Design constraints (per project memory)
---------------------------------------
* Frozen dataclasses, free pure functions, full typing
  (per ``functional-python`` skill).
* No mutation of upstream panel parquets, DuckDB tables, or
  ``_KNOWN_Y3_METHODOLOGY_TAGS`` admitted set
  (per ``feedback_agent_scope``).
* Anti-fishing audit invariants (per ``feedback_pathological_halt_anti_fishing_checkpoint``):
  ``T3B_CRITICAL_VALUE = 1.28``, ``PRE_REGISTERED_SIGN = 1`` (β > 0),
  ``ALPHA_ONE_SIDED = 0.10`` are pre-registered byte-exact and immutable
  at module level. Modifying any of these requires a CORRECTIONS block
  and 3-way review per spec §9.
* Gate verdict logic is sign-locked: a negative β̂ FAILs the gate
  regardless of magnitude or SE — silent sign-flip rescue is
  anti-fishing-banned.

References
----------
Spec:        contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md
DE artifacts: contracts/.scratch/2026-04-25-task110-rev2-data/
TDD test:    contracts/scripts/tests/inequality/test_phase5b_analytics.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

# ─────────────────────────────────────────────────────────────────────────────
# Spec-pinned constants (anti-fishing immutable)
# ─────────────────────────────────────────────────────────────────────────────

#: One-sided 90% Normal critical value (spec §7 T3b lock).
T3B_CRITICAL_VALUE: Final[float] = 1.28

#: Pre-registered sign hypothesis: β > 0 (spec §7 T3b).
#: Rising X_d → rising inequality differential (Y₃).
PRE_REGISTERED_SIGN: Final[int] = 1

#: One-sided significance level (spec §5 lock; Rev-4 prior-art).
ALPHA_ONE_SIDED: Final[float] = 0.10

#: HAC truncation lag for primary specification (spec §4.1; Newey-West 1987).
PRIMARY_HAC_LAG: Final[int] = 4

#: HAC truncation lag for Row 12 bandwidth sensitivity.
SENSITIVITY_HAC_LAG: Final[int] = 12

#: Bootstrap mean block length for Politis-Romano stationary block (spec §4.1).
BOOTSTRAP_MEAN_BLOCK_LENGTH: Final[int] = 4

#: Bootstrap resamples in the analysis script (spec §4.1).
BOOTSTRAP_DEFAULT_RESAMPLES: Final[int] = 10_000

#: Six pre-committed continuous controls (spec §4.1).
SIX_CONTROL_COLUMNS: Final[tuple[str, ...]] = (
    "vix_avg",
    "oil_return",
    "us_cpi_surprise",
    "banrep_rate_surprise",
    "fed_funds_weekly",
    "intervention_dummy",
)

#: Three parsimonious controls (spec Row 6).
THREE_PARSIMONIOUS_CONTROL_COLUMNS: Final[tuple[str, ...]] = (
    "vix_avg",
    "oil_return",
    "intervention_dummy",
)


# ─────────────────────────────────────────────────────────────────────────────
# Domain types (frozen dataclasses; functional-python skill)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class RegressionResult:
    """Single-row coefficient estimate + inference summary.

    All fields are populated regardless of estimator (OLS+HAC, bootstrap,
    Student-t MLE) so that downstream tabulation is uniform.

    Attributes
    ----------
    beta_hat:
        Point estimate of β (X_d coefficient).
    se:
        Standard error of β̂ (HAC, bootstrap-empirical, or t-MLE).
    t_stat:
        β̂ / SE. NaN-tolerant for zero-SE pathological cases.
    p_value_one_sided:
        Pr(β̂ ≥ observed | H_0: β = 0), under Normal sampling for OLS+HAC.
        Bootstrap reports the empirical right-tail p-value.
    p_value_two_sided:
        Two-sided p-value (T3a in spec §7).
    lower_90_one_sided:
        β̂ − 1.28·SE; the gate-bearing quantity (spec §7 T3b).
    n:
        Sample size at the regression stage.
    estimator:
        Free-text label ("ols_hac4", "ols_hac12", "bootstrap_pr_4_10000",
        "student_t_mle"). For traceability in the markdown output.
    extra:
        Dict of estimator-specific diagnostics (e.g., bootstrap CI quantiles,
        Student-t df estimate). Excluded from the gate-verdict logic.
    """

    beta_hat: float
    se: float
    t_stat: float
    p_value_one_sided: float
    p_value_two_sided: float
    lower_90_one_sided: float
    n: int
    estimator: str
    extra: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GateVerdict:
    """Pre-registered T3b one-sided gate outcome on a regression result.

    Attributes
    ----------
    gate:
        ``"PASS"`` iff sign(β̂) = PRE_REGISTERED_SIGN AND β̂ − 1.28·SE > 0;
        ``"FAIL"`` otherwise. ``"HALT"`` is reserved for analytical-failure
        upstream (e.g., singular design matrix, NaN-corrupted SE) and is
        emitted by the orchestration script, not here.
    beta_hat:
        Point estimate echoed for traceability.
    se:
        SE echoed for traceability.
    lower_90_one_sided:
        β̂ − 1.28·SE.
    n:
        Sample size echoed for traceability.
    """

    gate: str
    beta_hat: float
    se: float
    lower_90_one_sided: float
    n: int


# ─────────────────────────────────────────────────────────────────────────────
# Pure helpers
# ─────────────────────────────────────────────────────────────────────────────


def _design_matrix(
    df: pd.DataFrame, x_col: str, control_cols: Sequence[str]
) -> tuple[pd.Series, pd.DataFrame]:
    """Return (y, X_with_const) numeric DataFrame for regression input.

    Casts every column to float64 to avoid `int16` (intervention_dummy)
    propagating into a non-symmetric design matrix.
    """
    y = df[x_col + "__placeholder"] if False else df  # type-narrow guard
    del y  # placate mypy unused-var
    y_series = df[df.columns[df.columns.get_loc("y3_value")]].astype(float)
    # We want y3_value as Y, x_col as primary regressor, controls in order.
    y_series = df["y3_value"].astype(float)
    cols = [x_col, *control_cols]
    X = df[cols].astype(float).copy()
    X = sm.add_constant(X, has_constant="add")
    return y_series, X


# ─────────────────────────────────────────────────────────────────────────────
# Public API: OLS + HAC
# ─────────────────────────────────────────────────────────────────────────────


def fit_ols_hac(
    df: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    control_cols: Sequence[str],
    hac_lag: int,
) -> RegressionResult:
    """Fit OLS with Newey-West HAC SEs at the given truncation lag.

    Parameters
    ----------
    df:
        Phase-5a panel. Must contain ``y_col``, ``x_col``, and every column
        in ``control_cols``.
    x_col:
        Column name of the variable-of-interest (X_d in spec equation §4.1).
    y_col:
        Column name of the LHS outcome (Y₃ in spec equation §4.1).
    control_cols:
        Ordered tuple of control column names (γ_1 … γ_k).
    hac_lag:
        Newey-West truncation lag (4 = primary, 12 = sensitivity).
    """
    df_local = df[[y_col, x_col, *control_cols]].dropna().copy()
    n = len(df_local)
    y = df_local[y_col].astype(float)
    X = sm.add_constant(df_local[[x_col, *control_cols]].astype(float), has_constant="add")
    model = sm.OLS(y, X)
    fit = model.fit(cov_type="HAC", cov_kwds={"maxlags": hac_lag})

    beta_hat = float(fit.params[x_col])
    se = float(fit.bse[x_col])
    t_stat = float(fit.tvalues[x_col])
    p_two = float(fit.pvalues[x_col])
    # one-sided right-tail p-value: Pr(t > observed) given β > 0 H_a
    p_one = float(stats.norm.sf(t_stat))
    lower_90 = beta_hat - T3B_CRITICAL_VALUE * se

    return RegressionResult(
        beta_hat=beta_hat,
        se=se,
        t_stat=t_stat,
        p_value_one_sided=p_one,
        p_value_two_sided=p_two,
        lower_90_one_sided=lower_90,
        n=n,
        estimator=f"ols_hac{hac_lag}",
        extra={"r_squared": float(fit.rsquared), "rsquared_adj": float(fit.rsquared_adj)},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API: Politis-Romano stationary block bootstrap
# ─────────────────────────────────────────────────────────────────────────────


def _stationary_block_indices(n: int, mean_block_length: int, rng: np.random.Generator) -> np.ndarray:
    """Politis-Romano (1994) stationary block bootstrap index sequence.

    Generates n indices into [0, n) by drawing geometric-length blocks
    starting at uniform-random positions and wrapping circularly.
    """
    p = 1.0 / mean_block_length
    indices = np.empty(n, dtype=np.int64)
    i = 0
    while i < n:
        start = int(rng.integers(0, n))
        block_len = int(rng.geometric(p))
        for j in range(block_len):
            if i >= n:
                break
            indices[i] = (start + j) % n
            i += 1
    return indices


def fit_bootstrap(
    df: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    control_cols: Sequence[str],
    mean_block_length: int = BOOTSTRAP_MEAN_BLOCK_LENGTH,
    n_resamples: int = BOOTSTRAP_DEFAULT_RESAMPLES,
    rng: np.random.Generator | None = None,
) -> RegressionResult:
    """Fit OLS with stationary block bootstrap SE on β̂.

    Returns a RegressionResult with empirical bootstrap SE, percentile-based
    one-sided p-value, and the 90% CI lower bound (5th percentile).
    """
    if rng is None:
        rng = np.random.default_rng()

    df_local = df[[y_col, x_col, *control_cols]].dropna().copy()
    n = len(df_local)

    # Point estimate from OLS on the original sample
    y_full = df_local[y_col].astype(float).to_numpy()
    X_full = sm.add_constant(df_local[[x_col, *control_cols]].astype(float), has_constant="add").to_numpy()
    point_fit = sm.OLS(y_full, X_full).fit()
    # x_col is at column index 1 (after const)
    x_col_idx = 1
    beta_hat = float(point_fit.params[x_col_idx])

    # Bootstrap loop
    boot_betas = np.empty(n_resamples, dtype=np.float64)
    for r in range(n_resamples):
        idx = _stationary_block_indices(n, mean_block_length, rng)
        y_b = y_full[idx]
        X_b = X_full[idx, :]
        try:
            fit_b = sm.OLS(y_b, X_b).fit()
            boot_betas[r] = float(fit_b.params[x_col_idx])
        except (np.linalg.LinAlgError, ValueError):
            boot_betas[r] = np.nan

    boot_betas = boot_betas[np.isfinite(boot_betas)]
    se = float(np.std(boot_betas, ddof=1))
    t_stat = float(beta_hat / se) if se > 0 else float("nan")
    p_one = float(np.mean(boot_betas <= 0.0))  # right-tail null at zero
    p_two = float(2.0 * min(p_one, 1.0 - p_one))
    lower_90 = beta_hat - T3B_CRITICAL_VALUE * se
    p5_q = float(np.quantile(boot_betas, 0.05))
    p95_q = float(np.quantile(boot_betas, 0.95))

    return RegressionResult(
        beta_hat=beta_hat,
        se=se,
        t_stat=t_stat,
        p_value_one_sided=p_one,
        p_value_two_sided=p_two,
        lower_90_one_sided=lower_90,
        n=n,
        estimator=f"bootstrap_pr_{mean_block_length}_{n_resamples}",
        extra={
            "boot_p5": p5_q,
            "boot_p95": p95_q,
            "boot_n_finite": float(len(boot_betas)),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API: Student-t innovation refit
# ─────────────────────────────────────────────────────────────────────────────


def fit_student_t(
    df: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    control_cols: Sequence[str],
) -> RegressionResult:
    """Refit β̂ via OLS + Student-t MLE on residual variance (degree of freedom estimated).

    Implementation: fit OLS to obtain β̂ and residuals, then MLE-fit a
    Student-t distribution on the residuals to estimate df. The reported SE
    on β̂ is computed from the OLS X'X inverse scaled by the t-MLE σ̂² (the
    natural Student-t error analogue at the linear-model level).

    For the live Y₃ panel (76 obs, signed log-difference), this is the
    "heavy-tail robustness check" specified in spec §4.2 sensitivity row 11.
    """
    df_local = df[[y_col, x_col, *control_cols]].dropna().copy()
    n = len(df_local)
    y = df_local[y_col].astype(float)
    X = sm.add_constant(df_local[[x_col, *control_cols]].astype(float), has_constant="add")

    ols_fit = sm.OLS(y, X).fit()
    beta_hat = float(ols_fit.params[x_col])
    resid = ols_fit.resid.to_numpy()

    # Student-t MLE on residuals (scipy fits df, loc, scale)
    df_t, loc_t, scale_t = stats.t.fit(resid, floc=0.0)
    sigma_t_sq = float(scale_t**2 * df_t / (df_t - 2.0)) if df_t > 2.0 else float(np.var(resid, ddof=1))

    # SE from OLS X'X inverse scaled by t-MLE σ²
    XtX_inv = np.linalg.inv(X.values.T @ X.values)
    x_col_pos = list(X.columns).index(x_col)
    se = float(np.sqrt(sigma_t_sq * XtX_inv[x_col_pos, x_col_pos]))
    t_stat = beta_hat / se if se > 0 else float("nan")

    # p-values from Student-t with df_t (heavy-tail-aware inference)
    if df_t > 2.0:
        p_one = float(stats.t.sf(t_stat, df_t))
        p_two = float(2.0 * stats.t.sf(abs(t_stat), df_t))
    else:
        p_one = float(stats.norm.sf(t_stat))
        p_two = float(2.0 * stats.norm.sf(abs(t_stat)))

    lower_90 = beta_hat - T3B_CRITICAL_VALUE * se

    return RegressionResult(
        beta_hat=beta_hat,
        se=se,
        t_stat=t_stat,
        p_value_one_sided=p_one,
        p_value_two_sided=p_two,
        lower_90_one_sided=lower_90,
        n=n,
        estimator="student_t_mle",
        extra={
            "df_t_estimated": float(df_t),
            "scale_t": float(scale_t),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API: gate verdict
# ─────────────────────────────────────────────────────────────────────────────


def compute_gate_verdict(*, beta_hat: float, se: float, n: int) -> GateVerdict:
    """Apply the spec §7 T3b one-sided 90% gate.

    PASS iff:
        sign(β̂) == PRE_REGISTERED_SIGN  AND  β̂ − 1.28·SE > 0

    FAIL otherwise. Sign-flip rescue (β̂ < 0 yet "passes" by absolute-value
    test) is anti-fishing-banned; the sign is locked by spec §9.3.
    """
    lower_90 = beta_hat - T3B_CRITICAL_VALUE * se
    sign_correct = (PRE_REGISTERED_SIGN > 0 and beta_hat > 0) or (
        PRE_REGISTERED_SIGN < 0 and beta_hat < 0
    )
    gate = "PASS" if (sign_correct and lower_90 > 0) else "FAIL"
    return GateVerdict(
        gate=gate,
        beta_hat=beta_hat,
        se=se,
        lower_90_one_sided=lower_90,
        n=n,
    )
