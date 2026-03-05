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
