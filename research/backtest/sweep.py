"""Trigger-based insurance backtest (INS-05) — gamma sweep.

Implements the trigger-based payout mechanism from main.pdf section 6:
- Premium: PLP pays gamma % of fees into reserve R at exit
- Trigger: Delta+ > delta* fires daily payout
- Payout: D = (Delta+ - delta*) / (1 - delta*) * R, pro-rata to insured positions

Pure functions, frozen dataclasses per @functional-python.
"""
from __future__ import annotations

from statistics import mean, median

from backtest.daily import approximate_mint_date
from backtest.pnl import compute_position_pnl
from backtest.types import BacktestResult, DailyPoolState, PositionPnL, ReserveState


def _build_reserve_states(
    daily_states: list[DailyPoolState],
    raw_positions: list[dict],
    gamma: float,
    delta_star: float,
    initial_balance: float = 0.0,
) -> list[ReserveState]:
    """Simulate trigger-based reserve day by day.

    Each day:
    1. Collect premiums from positions that exit today.
    2. If trigger fires, compute donate amount and distribute.
    """
    burn_dates: dict[str, list[dict]] = {}
    for pos in raw_positions:
        bd = pos["burn_date"]
        burn_dates.setdefault(bd, []).append(pos)

    daily_dict = {ds.day: ds for ds in daily_states}
    sorted_days = sorted(daily_dict.keys())

    balance = initial_balance
    states: list[ReserveState] = []

    for day in sorted_days:
        ds = daily_dict[day]

        # Premium in from positions exiting today
        exiting = burn_dates.get(day, [])
        premium_in = 0.0
        for pos in exiting:
            if pos["blocklife"] <= 1:
                continue
            mint = approximate_mint_date(pos["burn_date"], pos["blocklife"])
            lifetime_fees = 0.0
            for d in sorted_days:
                if d < mint or d >= pos["burn_date"]:
                    continue
                dd = daily_dict[d]
                if dd.n_positions > 0:
                    lifetime_fees += dd.pool_daily_fee / dd.n_positions
            premium_in += gamma * lifetime_fees

        balance += premium_in

        # Trigger check
        trigger = ds.delta_plus > delta_star
        donate_amount = 0.0
        payout_out = 0.0

        if trigger and balance > 0:
            severity = (ds.delta_plus - delta_star) / (1.0 - delta_star)
            donate_amount = severity * balance
            payout_out = min(donate_amount, balance)
            balance -= payout_out

        states.append(ReserveState(
            day=day,
            balance=balance,
            premium_in=premium_in,
            payout_out=payout_out,
            trigger_fired=trigger,
            delta_plus=ds.delta_plus,
            donate_amount=donate_amount,
        ))

    return states


def run_single_backtest(
    daily_states: list[DailyPoolState],
    raw_positions: list[dict],
    gamma: float,
    delta_star: float = 0.09,
    initial_balance: float = 0.0,
) -> BacktestResult:
    """Run one trigger-based backtest at a single gamma."""
    reserve_states = _build_reserve_states(
        daily_states, raw_positions, gamma, delta_star, initial_balance,
    )

    daily_dict = {ds.day: ds for ds in daily_states}
    rs_dict = {rs.day: rs for rs in reserve_states}

    pnls: list[PositionPnL] = []
    for idx, pos in enumerate(raw_positions):
        if pos["blocklife"] <= 1:
            continue
        pnl = compute_position_pnl(
            idx, pos["burn_date"], pos["blocklife"],
            daily_dict, rs_dict, gamma,
        )
        pnls.append(pnl)

    hvs = [p.hedge_value for p in pnls]
    n = len(hvs)
    total_premiums = sum(rs.premium_in for rs in reserve_states)
    total_payouts = sum(rs.payout_out for rs in reserve_states)
    trigger_days = sum(1 for rs in reserve_states if rs.trigger_fired)
    balances = [rs.balance for rs in reserve_states]

    return BacktestResult(
        gamma=gamma,
        total_premiums=total_premiums,
        total_payouts=total_payouts,
        trigger_days=trigger_days,
        mean_hedge_value=mean(hvs) if hvs else 0.0,
        median_hedge_value=median(hvs) if hvs else 0.0,
        pct_better_off=sum(1 for h in hvs if h > 0) / n if n else 0.0,
        reserve_peak=max(balances) if balances else 0.0,
        reserve_utilization=total_payouts / max(balances) if balances and max(balances) > 0 else 0.0,
        position_pnls=pnls,
        reserve_states=reserve_states,
    )


def run_gamma_sweep(
    daily_states: list[DailyPoolState],
    raw_positions: list[dict],
    gammas: list[float],
    delta_star: float = 0.09,
    initial_balance: float = 0.0,
) -> list[BacktestResult]:
    """Run trigger-based backtest across multiple gamma values."""
    return [
        run_single_backtest(daily_states, raw_positions, g, delta_star, initial_balance)
        for g in gammas
    ]
