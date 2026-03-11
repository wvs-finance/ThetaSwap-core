"""Cumulative vs daily-snapshot Δ⁺ oracle comparison.

Mirrors the on-chain addStateTerm() accumulator logic in Python so we can
compare the cumulative oracle (which retains memory across days) against a
naive daily-snapshot that resets each day.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionExit:
    """A single position removal event."""

    token_id: int
    burn_date: str
    block_lifetime: int
    fee_share_x_k: float


@dataclass(frozen=True)
class CumulativeOracleState:
    """Running accumulator state mirroring on-chain storage."""

    accumulated_sum: float
    theta_sum: float
    removed_pos_count: int


def step_cumulative(
    state: CumulativeOracleState,
    exit_: PositionExit,
) -> CumulativeOracleState:
    """Simulate one addStateTerm() call.

    accumulated_sum += x_k² / block_lifetime
    theta_sum       += 1.0 / block_lifetime
    removed_pos_count += 1
    """
    return CumulativeOracleState(
        accumulated_sum=state.accumulated_sum + exit_.fee_share_x_k ** 2 / exit_.block_lifetime,
        theta_sum=state.theta_sum + 1.0 / exit_.block_lifetime,
        removed_pos_count=state.removed_pos_count + 1,
    )


def cumulative_delta_plus(state: CumulativeOracleState) -> float:
    """Compute Δ⁺ from cumulative state: max(0, sqrt(accum) - sqrt(theta/N²))."""
    n = state.removed_pos_count
    if n == 0:
        return 0.0
    return max(0.0, math.sqrt(state.accumulated_sum) - math.sqrt(state.theta_sum / (n * n)))


def daily_snapshot_delta_plus(exits: list[PositionExit]) -> float:
    """Compute Δ⁺ from a single day's exits only (no memory)."""
    if not exits:
        return 0.0
    n = len(exits)
    acc = sum(e.fee_share_x_k ** 2 / e.block_lifetime for e in exits)
    theta = sum(1.0 / e.block_lifetime for e in exits)
    return max(0.0, math.sqrt(acc) - math.sqrt(theta / (n * n)))


@dataclass(frozen=True)
class DualDeltaPlusSeries:
    """Paired time-series of cumulative and daily-snapshot Δ⁺ values."""

    days: tuple[str, ...]
    cumulative_delta_plus: tuple[float, ...]
    daily_snapshot_delta_plus: tuple[float, ...]


def build_dual_series(exits: list[PositionExit]) -> DualDeltaPlusSeries:
    """Group exits by burn_date and compute both Δ⁺ variants per day."""
    if not exits:
        return DualDeltaPlusSeries(days=(), cumulative_delta_plus=(), daily_snapshot_delta_plus=())

    by_day: dict[str, list[PositionExit]] = defaultdict(list)
    for e in exits:
        by_day[e.burn_date].append(e)

    sorted_days = sorted(by_day)

    days: list[str] = []
    cum_vals: list[float] = []
    snap_vals: list[float] = []

    state = CumulativeOracleState(accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0)

    for day in sorted_days:
        day_exits = by_day[day]
        for e in day_exits:
            state = step_cumulative(state, e)
        days.append(day)
        cum_vals.append(cumulative_delta_plus(state))
        snap_vals.append(daily_snapshot_delta_plus(day_exits))

    return DualDeltaPlusSeries(
        days=tuple(days),
        cumulative_delta_plus=tuple(cum_vals),
        daily_snapshot_delta_plus=tuple(snap_vals),
    )
