"""Exit-based payoff backtest — payout = premium × ((max_p / p*)^α - 1).

The price mapping p = Δ⁺/(1-Δ⁺) from FCI-09 converts concentration deviation
into an insurance price. The payoff at exit scales with the worst concentration
experienced during the position's lifetime, raised to power α.

Pure functions, frozen dataclasses per @functional-python.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median

from backtest.daily import approximate_mint_date
from backtest.types import DailyPoolState


@dataclass(frozen=True)
class ExitPayoffResult:
    """Result for one (γ, α, Δ*) payoff backtest."""
    gamma: float
    alpha: float
    delta_star: float
    initial_balance: float
    total_premiums: float
    total_payouts: float
    mean_hedge_value: float
    median_hedge_value: float
    pct_better_off: float
    reserve_final: float
    reserve_peak: float
    position_results: list[PositionExitResult]


@dataclass(frozen=True)
class PositionExitResult:
    """Per-position result under exit payoff mechanism."""
    position_idx: int
    burn_date: str
    blocklife: int
    alive_days: int
    fees_earned: float
    premium: float
    max_delta_plus: float
    max_price: float
    payoff_multiplier: float
    payout: float
    hedge_value: float


def delta_to_price(delta_plus: float) -> float:
    """FCI-09: p = Δ⁺ / (1 - Δ⁺)."""
    if delta_plus >= 1.0:
        return float("inf")
    return delta_plus / (1.0 - delta_plus)


def payoff_multiplier(max_price: float, p_star: float, alpha: float) -> float:
    """Compute (max_p / p*)^α - 1, floored at 0."""
    if max_price <= p_star or p_star <= 0:
        return 0.0
    return (max_price / p_star) ** alpha - 1.0


def run_exit_payoff_backtest(
    daily_states: list[DailyPoolState],
    raw_positions: list[dict],
    gamma: float,
    alpha: float,
    delta_star: float = 0.09,
    initial_balance: float = 0.0,
) -> ExitPayoffResult:
    """Run exit-based payoff backtest.

    For each position, at exit (afterRemoveLiquidity):
    1. Compute premium = γ × lifetime_fees → R += premium
    2. Compute max_p = max price experienced during lifetime
    3. Compute payout = premium × ((max_p / p*)^α - 1) → R -= min(payout, R)
    4. HV = payout - premium

    Positions processed in exit-date order (reserve is path-dependent).
    """
    daily_dict = {ds.day: ds for ds in daily_states}
    sorted_days = sorted(daily_dict.keys())
    p_star = delta_to_price(delta_star)

    # Pre-compute per-position data
    pos_records: list[dict] = []
    for idx, pos in enumerate(raw_positions):
        if pos["blocklife"] <= 1:
            continue
        mint = approximate_mint_date(pos["burn_date"], pos["blocklife"])

        lifetime_fees = 0.0
        max_dp = 0.0
        alive_days = 0

        for day in sorted_days:
            if day < mint or day >= pos["burn_date"]:
                continue
            ds = daily_dict[day]
            alive_days += 1
            if ds.n_positions > 0:
                lifetime_fees += ds.pool_daily_fee / ds.n_positions
            if ds.delta_plus > max_dp:
                max_dp = ds.delta_plus

        pos_records.append({
            "idx": idx,
            "burn": pos["burn_date"],
            "blocklife": pos["blocklife"],
            "alive_days": alive_days,
            "lifetime_fees": lifetime_fees,
            "max_dp": max_dp,
        })

    # Process in exit order (reserve is sequential)
    pos_records.sort(key=lambda r: r["burn"])

    balance = initial_balance
    peak = initial_balance
    total_premiums = 0.0
    total_payouts = 0.0
    results_by_idx: dict[int, PositionExitResult] = {}

    for rec in pos_records:
        premium = gamma * rec["lifetime_fees"]
        max_p = delta_to_price(rec["max_dp"])
        mult = payoff_multiplier(max_p, p_star, alpha)

        # Step 1: premium in
        balance += premium
        total_premiums += premium

        # Step 2: payout out
        raw_payout = premium * mult
        actual_payout = min(raw_payout, balance)
        balance -= actual_payout
        total_payouts += actual_payout

        if balance > peak:
            peak = balance

        hv = actual_payout - premium

        results_by_idx[rec["idx"]] = PositionExitResult(
            position_idx=rec["idx"],
            burn_date=rec["burn"],
            blocklife=rec["blocklife"],
            alive_days=rec["alive_days"],
            fees_earned=rec["lifetime_fees"],
            premium=premium,
            max_delta_plus=rec["max_dp"],
            max_price=max_p,
            payoff_multiplier=mult,
            payout=actual_payout,
            hedge_value=hv,
        )

    # Collect in original order
    position_results = [results_by_idx[rec["idx"]] for rec in sorted(pos_records, key=lambda r: r["idx"])]

    hvs = [r.hedge_value for r in position_results]
    n = len(hvs)

    return ExitPayoffResult(
        gamma=gamma,
        alpha=alpha,
        delta_star=delta_star,
        initial_balance=initial_balance,
        total_premiums=total_premiums,
        total_payouts=total_payouts,
        mean_hedge_value=mean(hvs) if hvs else 0.0,
        median_hedge_value=median(hvs) if hvs else 0.0,
        pct_better_off=sum(1 for h in hvs if h > 0) / n if n else 0.0,
        reserve_final=balance,
        reserve_peak=peak,
        position_results=position_results,
    )


def run_alpha_sweep(
    daily_states: list[DailyPoolState],
    raw_positions: list[dict],
    gamma: float,
    alphas: list[float],
    delta_star: float = 0.09,
    initial_balance: float = 0.0,
) -> list[ExitPayoffResult]:
    """Sweep α values for the exit payoff mechanism."""
    return [
        run_exit_payoff_backtest(daily_states, raw_positions, gamma, a, delta_star, initial_balance)
        for a in alphas
    ]
