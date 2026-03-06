"""Tests for position-level P&L computation."""
from __future__ import annotations

from backtest.pnl import compute_position_pnl
from backtest.types import DailyPoolState, ReserveState


# ── Helpers ───────────────────────────────────────────────────────────

def _ds(day: str, n_positions: int = 10, pool_daily_fee: float = 100.0,
        il: float = 0.01) -> DailyPoolState:
    return DailyPoolState(
        day=day, a_t_real=0.0, a_t_null=0.0, delta_plus=0.0,
        il=il, n_positions=n_positions, pool_daily_fee=pool_daily_fee,
    )


def _rs(day: str, trigger_fired: bool = False, payout_out: float = 0.0) -> ReserveState:
    return ReserveState(
        day=day, balance=100.0, premium_in=0.0,
        payout_out=payout_out, trigger_fired=trigger_fired,
        delta_plus=0.0, donate_amount=0.0,
    )


# ── Tests ─────────────────────────────────────────────────────────────

def test_unhedged_pnl_correct():
    """unhedged = fees - il_cost."""
    # Position alive 2024-01-01 and 2024-01-02 (burn=2024-01-03, blocklife=14400 => 2 days)
    daily_states_dict = {
        "2024-01-01": _ds("2024-01-01", n_positions=10, il=0.01),
        "2024-01-02": _ds("2024-01-02", n_positions=10, il=0.02),
        "2024-01-03": _ds("2024-01-03", n_positions=10, il=0.01),
    }
    reserve_states_dict = {
        "2024-01-01": _rs("2024-01-01"),
        "2024-01-02": _rs("2024-01-02"),
        "2024-01-03": _rs("2024-01-03"),
    }
    gamma = 0.10

    p = compute_position_pnl(
        position_idx=0, burn_date="2024-01-03", blocklife=14400,
        daily_states_dict=daily_states_dict,
        reserve_states_dict=reserve_states_dict,
        gamma=gamma,
    )
    # fees = 100/10 + 100/10 = 20.0
    # il = 0.01 + 0.02 = 0.03
    assert abs(p.fees_earned - 20.0) < 1e-9
    assert abs(p.il_cost - 0.03) < 1e-9
    assert abs(p.pnl_unhedged - (20.0 - 0.03)) < 1e-9


def test_hedged_gets_payout_on_trigger_day():
    """Position alive on trigger day receives its share of payout."""
    daily_states_dict = {
        "2024-01-01": _ds("2024-01-01", n_positions=5, il=0.0),
        "2024-01-02": _ds("2024-01-02", n_positions=5, il=0.0),
    }
    reserve_states_dict = {
        "2024-01-01": _rs("2024-01-01", trigger_fired=True, payout_out=50.0),
        "2024-01-02": _rs("2024-01-02"),
    }
    gamma = 0.10

    p = compute_position_pnl(
        position_idx=0, burn_date="2024-01-02", blocklife=7200,
        daily_states_dict=daily_states_dict,
        reserve_states_dict=reserve_states_dict,
        gamma=gamma,
    )
    # Alive on 2024-01-01 only (burn = 2024-01-02 excluded)
    # payout = 50.0 / 5 positions = 10.0
    assert abs(p.payouts_received - 10.0) < 1e-9
    # fees = 100/5 = 20.0, premium = 0.10 * 20.0 = 2.0
    # hedged = (1-0.10)*20.0 - 0.0 + 10.0 = 18.0 + 10.0 = 28.0
    assert abs(p.pnl_hedged - 28.0) < 1e-9


def test_position_not_alive_on_trigger_gets_no_payout():
    """Position not alive on trigger day gets zero payouts."""
    daily_states_dict = {
        "2024-01-01": _ds("2024-01-01", n_positions=5, il=0.0),
        "2024-01-02": _ds("2024-01-02", n_positions=5, il=0.0),
        "2024-01-03": _ds("2024-01-03", n_positions=5, il=0.0),
    }
    reserve_states_dict = {
        "2024-01-01": _rs("2024-01-01"),
        "2024-01-02": _rs("2024-01-02", trigger_fired=True, payout_out=50.0),
        "2024-01-03": _rs("2024-01-03"),
    }
    gamma = 0.10

    # Position: burn=2024-01-02, blocklife=7200 => mint=2024-01-01
    # Alive only on 2024-01-01. Trigger is on 2024-01-02 => not alive.
    p = compute_position_pnl(
        position_idx=0, burn_date="2024-01-02", blocklife=7200,
        daily_states_dict=daily_states_dict,
        reserve_states_dict=reserve_states_dict,
        gamma=gamma,
    )
    assert p.payouts_received == 0.0


def test_hedge_value():
    """hedge_value = hedged - unhedged."""
    daily_states_dict = {
        "2024-01-01": _ds("2024-01-01", n_positions=10, il=0.0),
    }
    reserve_states_dict = {
        "2024-01-01": _rs("2024-01-01", trigger_fired=True, payout_out=20.0),
    }
    gamma = 0.10

    p = compute_position_pnl(
        position_idx=0, burn_date="2024-01-02", blocklife=7200,
        daily_states_dict=daily_states_dict,
        reserve_states_dict=reserve_states_dict,
        gamma=gamma,
    )
    assert abs(p.hedge_value - (p.pnl_hedged - p.pnl_unhedged)) < 1e-9
