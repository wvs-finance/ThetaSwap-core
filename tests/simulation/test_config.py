"""Tests for simulation config."""
from simulation.config import SimConfig


def test_default_config_creates():
    cfg = SimConfig()
    assert cfg.T == 3000
    assert cfg.L_0 == 100.0
    assert cfg.A_0 == 0.0


def test_config_is_frozen():
    cfg = SimConfig()
    try:
        cfg.T = 999
        assert False, "Should be frozen"
    except AttributeError:
        pass


def test_config_custom_values():
    cfg = SimConfig(T=500, alpha=0.2)
    assert cfg.T == 500
    assert cfg.alpha == 0.2
    assert cfg.fee_base == 0.003  # default preserved
