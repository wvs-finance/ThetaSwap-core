"""Domain types for ETH/USDC backtest — frozen dataclasses per @functional-python."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DailyPoolState:
    """One day of aggregated pool metrics."""
    day: str
    a_t_real: float
    a_t_null: float
    delta_plus: float
    il: float
    n_positions: int
    pool_daily_fee: float


@dataclass(frozen=True)
class ReserveState:
    """Insurance reserve snapshot after processing one day."""
    day: str
    balance: float
    premium_in: float
    payout_out: float
    trigger_fired: bool
    delta_plus: float
    donate_amount: float


@dataclass(frozen=True)
class PositionPnL:
    """P&L decomposition for a single LP position."""
    position_idx: int
    burn_date: str
    blocklife: int
    alive_days: int
    fees_earned: float
    il_cost: float
    premium_paid: float
    payouts_received: float
    pnl_unhedged: float
    pnl_hedged: float
    hedge_value: float


@dataclass(frozen=True)
class BacktestResult:
    """Aggregate result for one gamma calibration run."""
    gamma: float
    total_premiums: float
    total_payouts: float
    trigger_days: int
    mean_hedge_value: float
    median_hedge_value: float
    pct_better_off: float
    reserve_peak: float
    reserve_utilization: float
    position_pnls: list[PositionPnL]
    reserve_states: list[ReserveState]
