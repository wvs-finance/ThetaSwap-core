"""Synthetic exit generation calibrated to reproduce known daily Δ⁺.

For each day, generates N position exits with (x_k, blocklife) tuples
such that the daily-snapshot formula reproduces the target DAILY_AT_MAP Δ⁺.

Calibration model: one "dominant LP" gets fee share c (assigned to the
shortest blocklife = JIT behavior), remaining N-1 LPs split (1-c)/(N-1).
Bisection on c to match target Δ⁺.

Per @functional-python: frozen dataclasses, free pure functions, full typing.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass

from backtest.oracle_comparison import PositionExit


@dataclass(frozen=True)
class SyntheticExitStream:
    """Full synthetic exit stream calibrated to target Δ⁺ series."""

    exits: tuple[PositionExit, ...]
    concentration_params: dict[str, float]  # day -> calibrated c


def _delta_plus_from_concentration(
    c: float,
    blocklifetimes: tuple[int, ...],
) -> float:
    """Compute Δ⁺ for a given concentration parameter c.

    c: dominant LP's fee share (assigned to shortest blocklife).
    Remaining (1-c)/(N-1) split uniformly among others.
    """
    n = len(blocklifetimes)
    if n == 0:
        return 0.0
    if n == 1:
        # Single exit: acc = c²/bl, theta = 1/bl, N=1
        # Δ⁺ = max(0, sqrt(c²/bl) - sqrt(1/bl)) = max(0, (c-1)/sqrt(bl))
        # Always ≤ 0 since c ≤ 1, so Δ⁺ = 0
        return 0.0

    bl_sorted = sorted(blocklifetimes)
    bl_dominant = bl_sorted[0]
    bl_rest = bl_sorted[1:]

    rest_share = (1.0 - c) / (n - 1)

    acc = c ** 2 / bl_dominant + rest_share ** 2 * sum(1.0 / bl for bl in bl_rest)
    theta = sum(1.0 / bl for bl in bl_sorted)
    n_sq = n ** 2

    return max(0.0, math.sqrt(acc) - math.sqrt(theta / n_sq))


def calibrate_concentration(
    target_dp: float,
    blocklifetimes: tuple[int, ...],
    tol: float = 1e-10,
    max_iter: int = 200,
) -> float:
    """Solve for concentration c that produces target Δ⁺ via bisection.

    c ∈ [1/N, 1]: dominant LP's fee share.
    Blocklifetimes sorted ascending — index 0 gets the dominant share.
    Returns c. If target_dp ≤ 0 or N < 2, returns 1/N (uniform).
    """
    n = len(blocklifetimes)
    if n < 2 or target_dp <= 0:
        return 1.0 / max(n, 1)

    lo = 1.0 / n
    hi = 1.0

    # Check if target is achievable
    dp_at_max = _delta_plus_from_concentration(hi, blocklifetimes)
    if dp_at_max < target_dp:
        return hi  # Saturate at maximum concentration

    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        dp_mid = _delta_plus_from_concentration(mid, blocklifetimes)
        if abs(dp_mid - target_dp) < tol:
            return mid
        if dp_mid < target_dp:
            lo = mid
        else:
            hi = mid

    return (lo + hi) / 2.0


def generate_synthetic_day(
    day: str,
    target_dp: float,
    blocklifetimes: tuple[int, ...],
    base_token_id: int,
) -> tuple[list[PositionExit], float]:
    """Generate synthetic exits for one day calibrated to target Δ⁺.

    Returns (exits, calibrated_c).
    """
    n = len(blocklifetimes)
    if n == 0:
        return [], 0.0

    c = calibrate_concentration(target_dp, blocklifetimes)
    bl_sorted = tuple(sorted(blocklifetimes))

    exits: list[PositionExit] = []

    if n == 1:
        exits.append(PositionExit(
            token_id=base_token_id,
            burn_date=day,
            block_lifetime=bl_sorted[0],
            fee_share_x_k=c,
        ))
    else:
        rest_share = (1.0 - c) / (n - 1)

        # Dominant LP: shortest blocklife, highest fee share
        exits.append(PositionExit(
            token_id=base_token_id,
            burn_date=day,
            block_lifetime=bl_sorted[0],
            fee_share_x_k=c,
        ))

        # Passive LPs: remaining blocklifetimes, uniform fee share
        for i, bl in enumerate(bl_sorted[1:], start=1):
            exits.append(PositionExit(
                token_id=base_token_id + i,
                burn_date=day,
                block_lifetime=bl,
                fee_share_x_k=rest_share,
            ))

    return exits, c


def generate_synthetic_stream(
    daily_targets: dict[str, float],
    day_blocklifetimes: dict[str, tuple[int, ...]],
) -> SyntheticExitStream:
    """Generate full synthetic exit stream from daily targets and blocklifetimes.

    daily_targets: day -> target Δ⁺ (from DAILY_AT_MAP - DAILY_AT_NULL_MAP).
    day_blocklifetimes: day -> tuple of blocklifetimes for that day's exits
                        (from RAW_POSITIONS empirical data).
    """
    all_exits: list[PositionExit] = []
    concentration_params: dict[str, float] = {}
    token_counter = 0

    for day in sorted(daily_targets):
        blocklifetimes = day_blocklifetimes.get(day, ())
        if not blocklifetimes:
            continue

        target_dp = daily_targets[day]
        exits, c = generate_synthetic_day(day, target_dp, blocklifetimes, token_counter)
        all_exits.extend(exits)
        concentration_params[day] = c
        token_counter += len(exits)

    return SyntheticExitStream(
        exits=tuple(all_exits),
        concentration_params=concentration_params,
    )


def build_from_raw_positions(
    raw_positions: list[tuple[str, int, float]],
    daily_at_map: dict[str, float],
    daily_at_null_map: dict[str, float],
) -> SyntheticExitStream:
    """Convenience: build synthetic stream from RAW_POSITIONS + DAILY_AT_MAP.

    Uses RAW_POSITIONS blocklifetimes per day, targets from AT maps.
    """
    by_day: dict[str, list[int]] = defaultdict(list)
    for burn_date, blocklife, _ in raw_positions:
        by_day[burn_date].append(blocklife)

    daily_targets: dict[str, float] = {}
    day_bls: dict[str, tuple[int, ...]] = {}

    for day in sorted(by_day):
        dp = max(0.0, daily_at_map.get(day, 0.0) - daily_at_null_map.get(day, 0.0))
        daily_targets[day] = dp
        day_bls[day] = tuple(by_day[day])

    return generate_synthetic_stream(daily_targets, day_bls)
