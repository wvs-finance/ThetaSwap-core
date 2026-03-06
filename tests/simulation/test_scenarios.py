"""Tests for simulation loop and metrics."""
import numpy as np

from simulation.scenarios import run_simulation, SimResult
from simulation.metrics import hedge_effectiveness, ecosystem_welfare
from simulation.config import SimConfig


def test_run_simulation_shape():
    cfg = SimConfig(T=100, volume_per_block=10.0)
    result = run_simulation(cfg, seed=42)
    assert isinstance(result, SimResult)
    assert result.A_T.shape == (100,)
    assert result.hedged_pnl.shape == (100,)
    assert result.unhedged_pnl.shape == (100,)
    assert result.underwriter_pnl.shape == (100,)


def test_hedged_beats_unhedged_under_shock():
    """Under concentration shock, hedged PLP should outperform."""
    cfg = SimConfig(T=500, volume_per_block=10.0)
    result = run_simulation(cfg, seed=42, scenario="shock")
    assert result.hedged_pnl[-1] > result.unhedged_pnl[-1]


def test_invariant_holds():
    """CFMM invariant ψ ≈ 0 at every step."""
    cfg = SimConfig(T=100)
    result = run_simulation(cfg, seed=42)
    assert np.all(np.abs(result.invariant_check) < 1e-8)


def test_a_t_bounded():
    """A_T in [0, 1) at every step (CFMM-31)."""
    cfg = SimConfig(T=100)
    result = run_simulation(cfg, seed=42)
    assert np.all(result.A_T >= 0.0)
    assert np.all(result.A_T < 1.0)


def test_hedge_effectiveness_positive_under_shock():
    cfg = SimConfig(T=500)
    result = run_simulation(cfg, seed=42, scenario="shock")
    eff = hedge_effectiveness(result.hedged_pnl[-1], result.unhedged_pnl[-1])
    assert eff > 0.0


def test_ecosystem_welfare_positive():
    cfg = SimConfig(T=500)
    result = run_simulation(cfg, seed=42, scenario="gradual")
    welfare = ecosystem_welfare(result.hedged_pnl[-1], result.underwriter_pnl[-1])
    assert welfare > 0.0
