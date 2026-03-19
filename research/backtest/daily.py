"""Daily pool state builder — pure function per @functional-python."""
from __future__ import annotations

from datetime import datetime, timedelta

from backtest.types import DailyPoolState

BLOCKS_PER_DAY: int = 7200


def approximate_mint_date(burn_date: str, blocklife: int) -> str:
    """Estimate mint date from burn date and blocklife (blocks / 7200 = days)."""
    burn_dt = datetime.strptime(burn_date, "%Y-%m-%d")
    days_alive = blocklife / BLOCKS_PER_DAY
    mint_dt = burn_dt - timedelta(days=days_alive)
    return mint_dt.strftime("%Y-%m-%d")


def build_daily_states(
    daily_at_map: dict[str, float],
    daily_at_null_map: dict[str, float],
    il_map: dict[str, float],
    raw_positions: list[dict],
    pool_daily_fee: float,
) -> list[DailyPoolState]:
    """Build sorted list of DailyPoolState from raw data maps.

    A position is alive on day d if mint_date <= d < burn_date.
    """
    # Pre-compute mint dates for all positions
    position_windows: list[tuple[str, str]] = []
    for pos in raw_positions:
        mint = approximate_mint_date(pos["burn_date"], pos["blocklife"])
        position_windows.append((mint, pos["burn_date"]))

    sorted_days = sorted(daily_at_map.keys())
    states: list[DailyPoolState] = []

    for day in sorted_days:
        a_t_real = daily_at_map[day]
        a_t_null = daily_at_null_map.get(day, 0.0)
        delta_plus = max(0.0, a_t_real - a_t_null)
        il = il_map.get(day, 0.0)

        # Count positions alive on this day: mint_date <= day < burn_date
        n_positions = sum(
            1 for mint, burn in position_windows if mint <= day < burn
        )

        states.append(DailyPoolState(
            day=day,
            a_t_real=a_t_real,
            a_t_null=a_t_null,
            delta_plus=delta_plus,
            il=il,
            n_positions=n_positions,
            pool_daily_fee=pool_daily_fee,
        ))

    return states
