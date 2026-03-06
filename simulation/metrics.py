"""Welfare and performance metrics — pure functions."""
from __future__ import annotations


def hedge_effectiveness(hedged_pnl: float, unhedged_pnl: float) -> float:
    """(hedged - unhedged) / |unhedged|. Positive means hedge helps."""
    if unhedged_pnl == 0.0:
        return 0.0
    return (hedged_pnl - unhedged_pnl) / abs(unhedged_pnl)


def ecosystem_welfare(plp_pnl: float, underwriter_pnl: float) -> float:
    """Total ecosystem welfare. Positive means positive-sum."""
    return plp_pnl + underwriter_pnl
