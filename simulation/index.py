"""Synthetic fee concentration index (A_T) trajectory generators.

All generators return numpy arrays of shape (T,) with values in [0, 1).
"""
from __future__ import annotations

from typing import Final, TypeAlias

import numpy as np

# Domain types
IndexValue: TypeAlias = float | np.ndarray
TimeSeries: TypeAlias = np.ndarray

# Bounds
MIN_A: Final[float] = 0.001
MAX_A: Final[float] = 0.999


def index_price(a_t: IndexValue) -> IndexValue:
    """p = A_T / (1 - A_T).  Odds-ratio mapping (payoff.tex)."""
    return a_t / (1.0 - a_t)


def generate_calm(
    T: int = 1000,
    base: float = 0.1,
    sigma: float = 0.02,
    seed: int = 42,
) -> TimeSeries:
    """Low, stable concentration with small noise."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, sigma, T)
    return np.clip(base + noise, MIN_A, MAX_A)


def generate_gradual(
    T: int = 1000,
    a_start: float = 0.05,
    a_end: float = 0.65,
    tau: float = 100.0,
) -> TimeSeries:
    """S-curve ramp from a_start to a_end via sigmoid."""
    t = np.arange(T, dtype=float)
    t_mid = T / 2.0
    sigmoid = 1.0 / (1.0 + np.exp(-(t - t_mid) / tau))
    return np.clip(a_start + (a_end - a_start) * sigmoid, MIN_A, MAX_A)


def generate_shock(
    T: int = 1000,
    base: float = 0.1,
    spike: float = 0.8,
    t_shock: int = 100,
    decay: float = 0.01,
) -> TimeSeries:
    """Constant base, then spike at t_shock with exponential decay back."""
    t = np.arange(T, dtype=float)
    decay_curve = np.where(
        t >= t_shock,
        base + (spike - base) * np.exp(-decay * (t - t_shock)),
        base,
    )
    return np.clip(decay_curve, MIN_A, MAX_A)


def generate_narrative_arc(
    T_per_phase: int = 1000,
    seed: int = 42,
) -> TimeSeries:
    """Calm -> Gradual -> Shock concatenated into one trajectory."""
    calm = generate_calm(T=T_per_phase, base=0.1, sigma=0.02, seed=seed)
    gradual = generate_gradual(
        T=T_per_phase, a_start=float(calm[-1]), a_end=0.65, tau=T_per_phase / 10,
    )
    shock = generate_shock(
        T=T_per_phase, base=0.5, spike=0.8,
        t_shock=T_per_phase // 10, decay=0.005,
    )
    return np.concatenate([calm, gradual, shock])
