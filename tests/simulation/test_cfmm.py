"""Tests for CFMM core math — verified against specs/model/ LaTeX spec."""
import math

import numpy as np

from simulation.cfmm import (
    CFMMState,
    payoff,
    invariant,
    risky_reserve,
    numeraire_reserve,
    spot_price,
    init_state,
)


# --- payoff.tex eq 5 ---
def test_payoff_at_zero():
    assert payoff(0.0) == 0.0


def test_payoff_at_one():
    assert math.isclose(payoff(1.0), math.log(2), rel_tol=1e-12)


def test_payoff_monotone():
    prices = np.linspace(0, 10, 100)
    vals = payoff(prices)
    assert np.all(np.diff(vals) > 0)


# --- trading-function.tex eq 13 ---
def test_invariant_on_curve():
    """Points on the reserve curve satisfy ψ = 0."""
    for p in [0.0, 0.5, 1.0, 2.0, 5.0]:
        x = risky_reserve(p)
        y = numeraire_reserve(p)
        assert math.isclose(invariant(x, y), 0.0, abs_tol=1e-12)


# --- reserves.tex eq 6 ---
def test_risky_reserve_at_zero():
    assert risky_reserve(0.0) == 1.0


def test_risky_reserve_decreasing():
    prices = np.linspace(0, 10, 100)
    x = risky_reserve(prices)
    assert np.all(np.diff(x) < 0)


# --- reserves.tex eq 8 ---
def test_numeraire_reserve_at_zero():
    assert numeraire_reserve(0.0) == 0.0


def test_numeraire_reserve_increasing():
    prices = np.linspace(0.01, 10, 100)
    y = numeraire_reserve(prices)
    assert np.all(np.diff(y) > 0)


# --- trading-function.tex eq 17 ---
def test_spot_price_roundtrip():
    """x(p) -> spot_price -> p, roundtrip."""
    for p in [0.1, 0.5, 1.0, 2.0, 5.0]:
        x = risky_reserve(p)
        p_recovered = spot_price(x)
        assert math.isclose(p_recovered, p, rel_tol=1e-12)


# --- initialization.tex ---
def test_init_state_genesis():
    """A_0 = 0: p=0, x=L, y=0."""
    s = init_state(A_0=0.0, L_0=100.0)
    assert s.p == 0.0
    assert s.x == 100.0
    assert math.isclose(s.y, 0.0, abs_tol=1e-12)
    assert s.L == 100.0


def test_init_state_half():
    """A_0 = 0.5, L_0 = 100: numerical verification from spec."""
    s = init_state(A_0=0.5, L_0=100.0)
    assert math.isclose(s.p, 1.0, rel_tol=1e-12)
    assert math.isclose(s.x, 50.0, rel_tol=1e-12)
    assert math.isclose(s.y, 19.31, rel_tol=1e-2)


def test_init_state_invariant():
    """Initial state satisfies ψ = 0."""
    s = init_state(A_0=0.3, L_0=100.0)
    psi = invariant(s.x / s.L, s.y / s.L)
    assert math.isclose(psi, 0.0, abs_tol=1e-10)


# --- Legendre-Fenchel: p*x + y = V_LP(p) ---
def test_legendre_fenchel():
    """Table from reserves.tex numerical verification."""
    for p, _expected_v in [(0, 0), (0.5, 0.4055), (1.0, 0.6931), (2.0, 1.0986)]:
        x = risky_reserve(p)
        y = numeraire_reserve(p)
        lp_value = p * x + y
        assert math.isclose(lp_value, payoff(p), rel_tol=1e-3)
