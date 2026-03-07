"""Domain types — frozen dataclasses, type aliases, constants per @functional-python."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, TypeAlias


# ── Constants ──────────────────────────────────────────────────────────
POOL_ADDRESS: Final = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
POOL_NAME: Final = "ETH/USDC 30bps"
FEE_TIER: Final = 3000
WINDOW_DAYS: Final = 90
MIN_JIT_EVENTS: Final = 50
FEE_REVENUE_PROXY: Final = 100.0  # avg daily fee revenue in USD per LP (placeholder)


# ── Type Aliases ───────────────────────────────────────────────────────
DuneRow: TypeAlias = dict[str, object]


# ── Value Types ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class DailyPanelRow:
    """One day of the estimation panel from Dune Q2+Q3."""
    day: str
    a_t: float
    passive_exit_count: int
    total_positions: int
    jit_count: int
    swap_count: int
    jit_count_lag1: int


@dataclass(frozen=True)
class PositionRow:
    """One LP lifecycle from Dune Q4v2."""
    burn_date: str
    blocklife: int
    daily_a_t: float
    il_proxy: float  # from Q5, merged by burn_date


@dataclass(frozen=True)
class EstimationResult:
    """Structural logit estimation output."""
    beta_concentration: float   # β₃ — parameter of interest
    se_concentration: float
    p_value_concentration: float
    beta_swap: float
    beta_jit_lag: float
    n_obs: int
    pseudo_r2: float
    wtp_mean: float             # β₃ × E[A_T] × FeeRevenue
    log_likelihood: float
    aic: float


@dataclass(frozen=True)
class DurationResult:
    """Duration model: log(blocklife) ~ A_T + IL + constant."""
    beta_a_t: float        # β₁ — concentration effect on position duration
    se_a_t: float
    p_value_a_t: float
    beta_il: float         # β₂ — IL control
    se_il: float
    p_value_il: float
    beta_intercept: float
    n_obs: int
    r_squared: float
    mean_blocklife: float  # average position duration in blocks
    mean_blocklife_hours: float  # ~12s per block


@dataclass(frozen=True)
class LaggedPositionRow:
    """Position with lagged A_T treatment variables."""
    burn_date: str
    mint_date: str
    blocklife: int
    max_a_t: float
    mean_a_t: float
    median_a_t: float
    il_proxy: float


@dataclass(frozen=True)
class RobustDurationResult:
    """Duration model with both OLS and HC1 robust standard errors."""
    beta_a_t: float
    se_a_t: float
    p_value_a_t: float
    robust_se_a_t: float
    robust_p_value_a_t: float
    beta_il: float
    se_il: float
    p_value_il: float
    robust_se_il: float
    robust_p_value_il: float
    beta_intercept: float
    n_obs: int
    r_squared: float
    mean_blocklife: float
    mean_blocklife_hours: float


@dataclass(frozen=True)
class SensitivityRow:
    """One row of the lag/measure sensitivity sweep."""
    lag: int
    measure: str  # "max", "mean", "median"
    beta_a_t: float
    robust_se_a_t: float
    robust_p_value_a_t: float
    n_obs: int


@dataclass(frozen=True)
class QuartileRow:
    """Dose-response: mean blocklife per A_T quartile."""
    quartile: int  # 1-4
    mean_blocklife_hours: float
    mean_a_t: float
    n_obs: int


# ── Exit Hazard Model Types ───────────────────────────────────────────

@dataclass(frozen=True)
class ExitPanelRow:
    """One position-day observation for the exit hazard model."""
    position_idx: int
    day: str
    exited: int
    a_t_lagged: float
    il: float
    log_age: float


@dataclass(frozen=True)
class LogitResult:
    """Logit MLE estimation output with day-clustered SEs."""
    beta_a_t: float
    beta_il: float
    beta_log_age: float
    beta_intercept: float
    se_a_t: float
    se_il: float
    se_log_age: float
    se_intercept: float
    cluster_se_a_t: float
    cluster_se_il: float
    cluster_se_log_age: float
    cluster_se_intercept: float
    p_value_a_t: float
    cluster_p_value_a_t: float
    n_obs: int
    n_exits: int
    n_clusters: int
    log_likelihood: float
    aic: float
    pseudo_r2: float
    mean_exit_prob: float


@dataclass(frozen=True)
class MarginalEffect:
    """Insurance pricing translation from logit marginal effect."""
    marginal_effect: float
    delta_a_t: float
    prob_increase: float
    hours_lost: float
    implied_premium_usd: float
    mean_exit_prob: float


@dataclass(frozen=True)
class QuadraticLogitResult:
    """Logit MLE with quadratic treatment term and day-clustered SEs."""
    beta_linear: float
    beta_quadratic: float
    beta_il: float
    beta_log_age: float
    beta_intercept: float
    cluster_se_linear: float
    cluster_se_quadratic: float
    cluster_p_linear: float
    cluster_p_quadratic: float
    turning_point: float
    n_obs: int
    n_exits: int
    n_clusters: int
    log_likelihood: float
    aic: float
    pseudo_r2: float
    mean_exit_prob: float
