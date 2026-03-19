"""
FCI metric computation — pure functions, Q128 arithmetic.

Mirrors hhi_oracle.py but operates on typed domain objects.
This is the ground-truth reference for differential testing.
"""
from __future__ import annotations

from math import isqrt

from .types import FCIState, FCIMetrics

Q128: int = 1 << 128
INDEX_ONE: int = (1 << 128) - 1


def floor_one(n: int) -> int:
    return 1 if n == 0 else n


def compute_index_a(accumulated_sum: int) -> int:
    """A_T = sqrt(accumulatedSum) in Q128, capped at INDEX_ONE."""
    if accumulated_sum >= Q128:
        return INDEX_ONE
    a = isqrt(accumulated_sum << 128)
    return min(a, INDEX_ONE)


def compute_at_null(theta_sum: int, n: int) -> int:
    """atNull = sqrt(thetaSum / N²) in Q128."""
    if n == 0 or theta_sum == 0:
        return 0
    ratio = theta_sum // (n * n)
    if ratio >= Q128:
        return INDEX_ONE
    a = isqrt(ratio << 128)
    return min(a, INDEX_ONE)


def compute_delta_plus(index_a: int, at_null: int) -> int:
    """Δ⁺ = max(0, A_T - atNull)."""
    return max(0, index_a - at_null)


def fci_state_to_metrics(state: FCIState) -> FCIMetrics:
    """Convert FCI accumulator state to final metrics."""
    index_a = compute_index_a(state.accumulated_sum)
    at_null = compute_at_null(state.theta_sum, state.removed_pos_count)
    delta_plus = compute_delta_plus(index_a, at_null)
    return FCIMetrics(
        accumulated_sum=state.accumulated_sum,
        index_a=index_a,
        theta_sum=state.theta_sum,
        removed_pos_count=state.removed_pos_count,
        at_null=at_null,
        delta_plus=delta_plus,
    )


def compute_x_k(pos_liquidity: int, total_range_liquidity: int) -> int:
    """x_k = posLiq / totalRangeLiq in Q128."""
    if total_range_liquidity == 0:
        return 0
    x = pos_liquidity * Q128 // total_range_liquidity
    return min(x, INDEX_ONE)


def compute_x_k_squared(x_k: int) -> int:
    """x_k² in Q128."""
    return x_k * x_k // Q128


def compute_term(x_k_squared: int, block_lifetime: int) -> int:
    """θ_k · x_k² = x_k² / blockLifetime in Q128."""
    return x_k_squared // floor_one(block_lifetime)


def compute_theta(block_lifetime: int) -> int:
    """θ_k = Q128 / blockLifetime."""
    return Q128 // floor_one(block_lifetime)
