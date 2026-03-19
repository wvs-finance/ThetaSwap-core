"""Gamma calibration — pure functions per @functional-python."""
from __future__ import annotations

from backtest.types import PositionPnL


def derive_gamma_star(wtp: float, avg_fees: float) -> float:
    """Derive optimal gamma from willingness-to-pay and average fees.

    gamma_star = min(wtp / avg_fees, 1.0).
    Returns 1.0 if avg_fees == 0.
    """
    if avg_fees == 0.0:
        return 1.0
    return min(wtp / avg_fees, 1.0)


def compute_avg_fees(position_pnls: list[PositionPnL]) -> float:
    """Compute average fees earned across all positions."""
    if not position_pnls:
        return 0.0
    return sum(p.fees_earned for p in position_pnls) / len(position_pnls)
