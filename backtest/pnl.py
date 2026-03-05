"""Position-level P&L — pure function per @functional-python."""
from __future__ import annotations

from datetime import datetime, timedelta

from backtest.types import DailyPoolState, PositionPnL, ReserveState

BLOCKS_PER_DAY: int = 7200


def _approximate_mint_date(burn_date: str, blocklife: int) -> str:
    """Estimate mint date from burn date and blocklife."""
    burn_dt = datetime.strptime(burn_date, "%Y-%m-%d")
    days_alive = blocklife / BLOCKS_PER_DAY
    mint_dt = burn_dt - timedelta(days=days_alive)
    return mint_dt.strftime("%Y-%m-%d")


def compute_position_pnl(
    position_idx: int,
    burn_date: str,
    blocklife: int,
    daily_states_dict: dict[str, DailyPoolState],
    reserve_states_dict: dict[str, ReserveState],
    gamma: float,
) -> PositionPnL:
    """Compute P&L for a single LP position over its alive window.

    Position is alive on day d if mint_date <= d < burn_date.
    """
    mint_date = _approximate_mint_date(burn_date, blocklife)

    fees = 0.0
    il_cost = 0.0
    payouts = 0.0
    alive_days = 0

    for day in sorted(daily_states_dict.keys()):
        if day < mint_date or day >= burn_date:
            continue

        alive_days += 1
        ds = daily_states_dict[day]
        rs = reserve_states_dict[day]

        # Accrue fees: position's share of pool daily fee
        if ds.n_positions > 0:
            fees += ds.pool_daily_fee / ds.n_positions

        # Accrue IL
        il_cost += ds.il

        # Collect payout if trigger fired and position is alive
        if rs.trigger_fired and ds.n_positions > 0:
            payouts += rs.payout_out / ds.n_positions

    premium = gamma * fees
    pnl_unhedged = fees - il_cost
    pnl_hedged = (1.0 - gamma) * fees - il_cost + payouts
    hedge_value = pnl_hedged - pnl_unhedged

    return PositionPnL(
        position_idx=position_idx,
        burn_date=burn_date,
        blocklife=blocklife,
        alive_days=alive_days,
        fees_earned=fees,
        il_cost=il_cost,
        premium_paid=premium,
        payouts_received=payouts,
        pnl_unhedged=pnl_unhedged,
        pnl_hedged=pnl_hedged,
        hedge_value=hedge_value,
    )
