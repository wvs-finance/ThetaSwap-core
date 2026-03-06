"""Funding rate, premium, and dynamic fee logic.

Implements specs/model/funding-rate.tex equations.
"""
from __future__ import annotations

from typing import TypeAlias

import numpy as np

# Domain types
Price: TypeAlias = float | np.ndarray
Rate: TypeAlias = float | np.ndarray


def mark_price(x: Price) -> Price:
    """p_mark = (1 - x) / x.  (funding-rate.tex eq mark-price)"""
    return (1.0 - x) / x


def funding_rate(
    basis: Price,
    p_index: Price,
    alpha: float,
) -> Rate:
    """r = α * |basis| / (p_index + 1).  (funding-rate.tex eq funding-rate-evolution)"""
    return alpha * np.abs(basis) / (p_index + 1.0)


def dynamic_fee(
    basis: Price,
    p_index: Price,
    alpha: float,
    fee_base: float,
    fee_max: float,
) -> Rate:
    """φ(t) = φ_base + sign(basis) * min(r, φ_max - φ_base).

    Clamped to [0, fee_max].  (funding-rate.tex eq dynamic-fee)
    """
    r = funding_rate(basis, p_index, alpha)
    fee_fund = np.sign(basis) * np.minimum(r, fee_max - fee_base)
    raw = fee_base + fee_fund
    return np.clip(raw, 0.0, fee_max)


def funding_payment(
    basis: Price,
    p_index: Price,
    alpha: float,
) -> Price:
    """F = r * basis.  (funding-rate.tex eq funding-payment)"""
    r = funding_rate(basis, p_index, alpha)
    return r * basis
