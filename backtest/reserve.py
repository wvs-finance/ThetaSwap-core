"""Reserve simulation — pure function per @functional-python."""
from __future__ import annotations

from backtest.types import DailyPoolState, ReserveState


def simulate_reserve(
    daily_states: list[DailyPoolState],
    premium_by_day: dict[str, float],
    delta_star: float = 0.09,
    initial_balance: float = 0.0,
) -> list[ReserveState]:
    """Simulate insurance reserve day-by-day.

    Per day:
    1. Premium in: pre-computed lifetime premium from positions exiting this day
    2. Trigger check: if delta_plus > delta_star and balance > 0,
       D = (delta_plus - delta_star) / (1 - delta_star) * balance,
       payout = min(D, balance), balance -= payout
    """
    balance = initial_balance
    result: list[ReserveState] = []

    for state in daily_states:
        # Step 1: collect premiums (pre-computed from position lifetime fees)
        premium = premium_by_day.get(state.day, 0.0)
        balance += premium

        # Step 2: trigger check and payout
        trigger_fired = False
        payout = 0.0
        donate_amount = 0.0

        if state.delta_plus > delta_star and balance > 0:
            trigger_fired = True
            d = (state.delta_plus - delta_star) / (1.0 - delta_star) * balance
            donate_amount = d
            payout = min(d, balance)
            balance -= payout

        result.append(ReserveState(
            day=state.day,
            balance=balance,
            premium_in=premium,
            payout_out=payout,
            trigger_fired=trigger_fired,
            delta_plus=state.delta_plus,
            donate_amount=donate_amount,
        ))

    return result
