"""Simulation loop — runs the full backtest and returns time series."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, TypeAlias

import numpy as np

from simulation.agents import (
    PLPState,
    UnderwriterState,
    step_hedged_plp,
    step_unhedged_plp,
    step_underwriter,
)
from simulation.cfmm import (
    init_state,
    invariant,
    payoff,
    risky_reserve,
    numeraire_reserve,
)
from simulation.config import SimConfig
from simulation.funding import dynamic_fee, funding_payment, funding_rate, mark_price
from simulation.index import (
    generate_calm,
    generate_gradual,
    generate_narrative_arc,
    generate_shock,
    index_price,
)

# Type aliases
ScenarioName: TypeAlias = Literal["calm", "gradual", "shock", "narrative"]
TimeSeries: TypeAlias = np.ndarray


@dataclass
class SimResult:
    """All time series from a simulation run. Mutable only during construction."""

    A_T: TimeSeries
    p_index: TimeSeries
    p_mark: TimeSeries
    x: TimeSeries
    y: TimeSeries
    hedged_pnl: TimeSeries
    unhedged_pnl: TimeSeries
    underwriter_pnl: TimeSeries
    funding_rates: TimeSeries
    fees: TimeSeries
    cum_premium_paid: TimeSeries
    cum_premium_earned: TimeSeries
    invariant_check: TimeSeries


_GENERATORS: Final = {
    "calm": lambda T, seed: generate_calm(T=T, seed=seed),
    "gradual": lambda T, _seed: generate_gradual(T=T),
    "shock": lambda T, _seed: generate_shock(T=T),
    "narrative": lambda T, seed: generate_narrative_arc(T_per_phase=(T + 2) // 3, seed=seed)[:T],
}


def _generate_a_t(scenario: ScenarioName, T: int, seed: int) -> TimeSeries:
    gen = _GENERATORS.get(scenario, _GENERATORS["narrative"])
    return gen(T, seed)


def run_simulation(
    cfg: SimConfig,
    seed: int = 42,
    scenario: ScenarioName = "narrative",
) -> SimResult:
    """Run the full simulation loop. Returns all time series for plotting."""
    T = cfg.T
    A_T = _generate_a_t(scenario, T, seed)

    # Pre-allocate output arrays
    p_idx = np.zeros(T)
    p_mrk = np.zeros(T)
    xs = np.zeros(T)
    ys = np.zeros(T)
    hedged = np.zeros(T)
    unhedged = np.zeros(T)
    uw_pnl = np.zeros(T)
    fund_rates = np.zeros(T)
    fees = np.zeros(T)
    cum_prem_paid = np.zeros(T)
    cum_prem_earned = np.zeros(T)
    inv_check = np.zeros(T)

    # Initialize agents
    plp_h = PLPState(liquidity=cfg.L_0)
    plp_u = PLPState(liquidity=cfg.L_0)
    uw = UnderwriterState(collateral=cfg.underwriter_collateral)

    for t in range(T):
        a = A_T[t]

        # Oracle price and CFMM reserves at current A_T
        p = float(index_price(a))
        x = cfg.L_0 * float(risky_reserve(p))
        y = cfg.L_0 * float(numeraire_reserve(p))

        # Mark price from per-liquidity reserves
        p_m = float(mark_price(x / cfg.L_0))

        # Funding
        basis = p_m - p
        r = float(funding_rate(basis, p, cfg.alpha))
        fee = float(dynamic_fee(basis, p, cfg.alpha, cfg.fee_base, cfg.fee_max))

        # Step agents
        plp_h = step_hedged_plp(plp_h, a, cfg)
        plp_u = step_unhedged_plp(plp_u, a, cfg)

        premium = cfg.premium_fraction * cfg.L_0 * cfg.fee_base * cfg.volume_per_block
        prot_liability = float(payoff(p)) * cfg.L_insurance
        uw = step_underwriter(uw, premium, prot_liability)

        # Record
        p_idx[t] = p
        p_mrk[t] = p_m
        xs[t] = x
        ys[t] = y
        hedged[t] = plp_h.net_pnl
        unhedged[t] = plp_u.net_pnl
        uw_pnl[t] = uw.net_pnl
        fund_rates[t] = r
        fees[t] = fee
        cum_prem_paid[t] = plp_h.premium_paid
        cum_prem_earned[t] = uw.premium_earned
        inv_check[t] = float(invariant(x / cfg.L_0, y / cfg.L_0))

    return SimResult(
        A_T=A_T,
        p_index=p_idx,
        p_mark=p_mrk,
        x=xs,
        y=ys,
        hedged_pnl=hedged,
        unhedged_pnl=unhedged,
        underwriter_pnl=uw_pnl,
        funding_rates=fund_rates,
        fees=fees,
        cum_premium_paid=cum_prem_paid,
        cum_premium_earned=cum_prem_earned,
        invariant_check=inv_check,
    )
