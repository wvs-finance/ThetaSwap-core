"""PLP and Underwriter agent state models.

Each step function takes the previous state + current block parameters,
returns a new frozen state. Pure functions, no mutation.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from simulation.cfmm import payoff
from simulation.config import SimConfig
from simulation.index import index_price


@dataclass(frozen=True)
class PLPState:
    """Passive LP state — tracks cumulative P&L components."""

    liquidity: float = 100.0
    fee_income: float = 0.0
    premium_paid: float = 0.0
    protection_value: float = 0.0
    net_pnl: float = 0.0


@dataclass(frozen=True)
class UnderwriterState:
    """Underwriter state — tracks premium vs liability."""

    collateral: float = 100.0
    premium_earned: float = 0.0
    protection_liability: float = 0.0
    net_pnl: float = 0.0


def step_hedged_plp(state: PLPState, A_T: float, cfg: SimConfig) -> PLPState:
    """Advance hedged PLP by one block."""
    gross_fee = state.liquidity * cfg.fee_base * cfg.volume_per_block
    premium = cfg.premium_fraction * gross_fee
    p = index_price(A_T)
    prot = float(payoff(p)) * cfg.L_insurance

    new_fee = state.fee_income + gross_fee
    new_prem = state.premium_paid + premium

    return replace(
        state,
        fee_income=new_fee,
        premium_paid=new_prem,
        protection_value=prot,
        net_pnl=new_fee - new_prem + prot,
    )


def step_unhedged_plp(state: PLPState, A_T: float, cfg: SimConfig) -> PLPState:
    """Advance unhedged PLP by one block.

    Fee income reduced by (1 - A_T): JIT captures the concentrated portion.
    """
    gross_fee = state.liquidity * cfg.fee_base * cfg.volume_per_block
    effective_fee = gross_fee * (1.0 - A_T)
    new_fee = state.fee_income + effective_fee

    return replace(state, fee_income=new_fee, net_pnl=new_fee)


def step_underwriter(
    state: UnderwriterState,
    premium_inflow: float,
    protection_liability: float,
) -> UnderwriterState:
    """Advance underwriter by one block."""
    new_prem = state.premium_earned + premium_inflow

    return replace(
        state,
        premium_earned=new_prem,
        protection_liability=protection_liability,
        net_pnl=new_prem - protection_liability,
    )
