"""Tests for synthetic A_T trajectory generators."""
import numpy as np

from simulation.index import (
    generate_calm,
    generate_gradual,
    generate_shock,
    generate_narrative_arc,
    index_price,
)


def test_index_price_zero():
    assert index_price(0.0) == 0.0


def test_index_price_half():
    assert index_price(0.5) == 1.0


def test_index_price_array():
    a = np.array([0.0, 0.25, 0.5, 0.75])
    p = index_price(a)
    expected = np.array([0.0, 1 / 3, 1.0, 3.0])
    np.testing.assert_allclose(p, expected, rtol=1e-12)


def test_calm_shape_and_bounds():
    a = generate_calm(T=1000, base=0.1, sigma=0.02, seed=42)
    assert a.shape == (1000,)
    assert np.all(a >= 0.0)
    assert np.all(a < 1.0)
    assert np.isclose(np.mean(a), 0.1, atol=0.05)


def test_gradual_ramps_up():
    a = generate_gradual(T=1000, a_start=0.05, a_end=0.65, tau=100.0)
    assert a.shape == (1000,)
    assert a[0] < 0.15
    assert a[-1] > 0.55
    assert np.all(a >= 0.0)
    assert np.all(a < 1.0)


def test_shock_spikes_and_decays():
    a = generate_shock(T=1000, base=0.1, spike=0.8, t_shock=100, decay=0.01)
    assert a.shape == (1000,)
    assert a[99] < 0.2  # before shock
    assert a[100] > 0.7  # at shock
    assert a[-1] < a[100]  # decayed
    assert np.all(a >= 0.0)
    assert np.all(a < 1.0)


def test_narrative_arc_concatenates():
    a = generate_narrative_arc(T_per_phase=500)
    assert a.shape == (1500,)
    assert np.all(a >= 0.0)
    assert np.all(a < 1.0)
    # Calm phase low, end of shock phase higher than calm
    assert np.mean(a[:100]) < np.mean(a[1100:1200])
