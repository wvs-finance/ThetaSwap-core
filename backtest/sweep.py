"""Gamma sweep orchestrator — pure functions per @functional-python."""
from __future__ import annotations

from collections import Counter
from statistics import mean, median

from backtest.pnl import compute_position_pnl
from backtest.reserve import simulate_reserve
from backtest.types import BacktestResult, DailyPoolState


def run_single_backtest(
    daily_states: list[DailyPoolState],
    raw_positions: list[dict],
    gamma: float,
    delta_star: float = 0.09,
) -> BacktestResult:
    """Run one backtest for a given gamma.

    Steps:
    1. Count exits_per_day from raw_positions (skip blocklife <= 1)
    2. simulate_reserve
    3. compute_position_pnl for each position with blocklife > 1
    4. Aggregate into BacktestResult
    """
    # Step 1: exits per day
    exits_per_day: dict[str, int] = dict(Counter(
        pos["burn_date"] for pos in raw_positions if pos["blocklife"] > 1
    ))

    # Step 2: reserve simulation
    reserve_states = simulate_reserve(daily_states, exits_per_day, gamma, delta_star)

    # Build lookup dicts
    daily_dict = {ds.day: ds for ds in daily_states}
    reserve_dict = {rs.day: rs for rs in reserve_states}

    # Step 3: position PnL for each eligible position
    position_pnls = []
    for idx, pos in enumerate(raw_positions):
        if pos["blocklife"] <= 1:
            continue
        pnl = compute_position_pnl(
            position_idx=idx,
            burn_date=pos["burn_date"],
            blocklife=pos["blocklife"],
            daily_states_dict=daily_dict,
            reserve_states_dict=reserve_dict,
            gamma=gamma,
        )
        position_pnls.append(pnl)

    # Step 4: aggregate
    total_premiums = sum(rs.premium_in for rs in reserve_states)
    total_payouts = sum(rs.payout_out for rs in reserve_states)
    trigger_days = sum(1 for rs in reserve_states if rs.trigger_fired)

    hedge_values = [p.hedge_value for p in position_pnls]
    mean_hedge = mean(hedge_values) if hedge_values else 0.0
    median_hedge = median(hedge_values) if hedge_values else 0.0
    pct_better = (
        sum(1 for h in hedge_values if h > 0) / len(hedge_values)
        if hedge_values else 0.0
    )

    reserve_peak = max(rs.balance for rs in reserve_states) if reserve_states else 0.0
    reserve_utilization = (
        total_payouts / reserve_peak if reserve_peak > 0 else 0.0
    )

    return BacktestResult(
        gamma=gamma,
        total_premiums=total_premiums,
        total_payouts=total_payouts,
        trigger_days=trigger_days,
        mean_hedge_value=mean_hedge,
        median_hedge_value=median_hedge,
        pct_better_off=pct_better,
        reserve_peak=reserve_peak,
        reserve_utilization=reserve_utilization,
        position_pnls=position_pnls,
        reserve_states=reserve_states,
    )


def run_gamma_sweep(
    daily_states: list[DailyPoolState],
    raw_positions: list[dict],
    gammas: list[float],
    delta_star: float = 0.09,
) -> list[BacktestResult]:
    """Run backtests across a range of gamma values."""
    return [
        run_single_backtest(daily_states, raw_positions, g, delta_star)
        for g in gammas
    ]
