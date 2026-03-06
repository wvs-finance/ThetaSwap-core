"""Tests for PLP and Underwriter agent state evolution."""
import math

from simulation.agents import (
    PLPState,
    UnderwriterState,
    step_hedged_plp,
    step_unhedged_plp,
    step_underwriter,
)
from simulation.config import SimConfig


def test_plp_initial_state():
    s = PLPState()
    assert s.fee_income == 0.0
    assert s.premium_paid == 0.0
    assert s.protection_value == 0.0
    assert s.net_pnl == 0.0


def test_hedged_plp_earns_fees_and_pays_premium():
    cfg = SimConfig(volume_per_block=10.0, fee_base=0.003, premium_fraction=0.1)
    s = PLPState(liquidity=100.0)
    s_new = step_hedged_plp(s, A_T=0.1, cfg=cfg)
    # Fee earned: L * fee_base * volume = 100 * 0.003 * 10 = 3.0
    assert math.isclose(s_new.fee_income, 3.0, rel_tol=1e-6)
    # Premium: 10% of 3.0 = 0.3
    assert math.isclose(s_new.premium_paid, 0.3, rel_tol=1e-6)


def test_unhedged_plp_reduced_by_concentration():
    cfg = SimConfig(volume_per_block=10.0, fee_base=0.003)
    s = PLPState(liquidity=100.0)
    s_new = step_unhedged_plp(s, A_T=0.5, cfg=cfg)
    # Fee reduced by (1 - A_T) = 0.5: 3.0 * 0.5 = 1.5
    assert math.isclose(s_new.fee_income, 1.5, rel_tol=1e-6)
    assert s_new.premium_paid == 0.0


def test_underwriter_earns_premium():
    s = UnderwriterState(collateral=100.0)
    s_new = step_underwriter(s, premium_inflow=0.3, protection_liability=0.1)
    assert math.isclose(s_new.premium_earned, 0.3, rel_tol=1e-6)
    assert math.isclose(s_new.protection_liability, 0.1, rel_tol=1e-6)
    assert math.isclose(s_new.net_pnl, 0.2, rel_tol=1e-6)


def test_hedged_plp_protection_value_increases_with_concentration():
    cfg = SimConfig(L_insurance=50.0)
    s_low = step_hedged_plp(PLPState(liquidity=100.0), A_T=0.1, cfg=cfg)
    s_high = step_hedged_plp(PLPState(liquidity=100.0), A_T=0.5, cfg=cfg)
    assert s_high.protection_value > s_low.protection_value
