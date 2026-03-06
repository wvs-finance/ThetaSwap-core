"""CFMM core math — implements specs/model/ LaTeX equations.

All functions accept and return floats or numpy arrays.
References: specs/model/payoff.tex, reserves.tex, trading-function.tex, initialization.tex
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, TypeAlias

import numpy as np

# Domain type aliases
Price: TypeAlias = float | np.ndarray
Reserve: TypeAlias = float | np.ndarray


@dataclass(frozen=True)
class CFMMState:
    """Snapshot of CFMM state at one point in time."""
    x: float  # risky reserve (feeConcentrationToken)
    y: float  # numeraire reserve
    L: float  # liquidity
    p: float  # spot price


def payoff(p: Price) -> Price:
    """V_LP(p) = ln(1 + p).  (payoff.tex eq 5)"""
    return np.log1p(p)


def invariant(x: Reserve, y: Reserve) -> Reserve:
    """ψ(x, y) = y + ln(x) + 1 - x.  (trading-function.tex eq 13)

    Returns 0 when (x, y) is on the curve.
    """
    return y + np.log(x) + 1.0 - x


def risky_reserve(p: Price) -> Reserve:
    """x(p) = 1 / (1 + p).  (reserves.tex eq 6)"""
    return 1.0 / (1.0 + p)


def numeraire_reserve(p: Price) -> Reserve:
    """y(p) = ln(1 + p) - p / (1 + p).  (reserves.tex eq 8)"""
    return np.log1p(p) - p / (1.0 + p)


def spot_price(x: Reserve) -> Price:
    """p = (1 - x) / x.  (trading-function.tex eq 17)"""
    return (1.0 - x) / x


def init_state(A_0: float, L_0: float) -> CFMMState:
    """Derive initial CFMM state from A_0 and L_0.  (initialization.tex)

    p_0 = A_0 / (1 - A_0)
    x_0 = L_0 * (1 - A_0)
    y_0 = L_0 * (-ln(1 - A_0) - A_0)
    """
    if A_0 == 0.0:
        return CFMMState(x=L_0, y=0.0, L=L_0, p=0.0)
    p_0 = A_0 / (1.0 - A_0)
    x_0 = L_0 * (1.0 - A_0)
    y_0 = L_0 * (-np.log(1.0 - A_0) - A_0)
    return CFMMState(x=x_0, y=y_0, L=L_0, p=p_0)
