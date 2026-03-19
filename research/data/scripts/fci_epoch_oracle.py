"""Epoch-reset FCI oracle — Python reference for Solidity differential testing.

Mirrors FeeConcentrationEpochStorageMod.sol (Option C: destruction by abandonment):
- Epoch-indexed mapping: each epoch gets a fresh FeeConcentrationState
- On epoch expiry, old state abandoned, new state at new epochId
- addTerm delegates to FeeConcentrationState.addTerm() (same math)
- deltaPlus delegates to FeeConcentrationState.deltaPlus()

Per @functional-python: frozen dataclasses, free pure functions.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass

Q128 = 1 << 128


@dataclass(frozen=True)
class EpochOracleState:
    """Maps to FeeConcentrationEpochStorage in Solidity."""

    current_epoch_id: int  # block.timestamp at epoch start
    epoch_length: int  # seconds
    # Current epoch's accumulator (maps to epochStates[poolId][epochId])
    accumulated_sum: int  # Q128-scaled
    theta_sum: int  # Q128-scaled
    removed_pos_count: int


def init_epoch(epoch_length: int, start_timestamp: int) -> EpochOracleState:
    return EpochOracleState(start_timestamp, epoch_length, 0, 0, 0)


def add_term_epoch(
    state: EpochOracleState,
    block_lifetime: int,
    x_squared_q128: int,
    current_timestamp: int,
) -> EpochOracleState:
    epoch_id = state.current_epoch_id
    acc = state.accumulated_sum
    theta = state.theta_sum
    count = state.removed_pos_count

    if state.epoch_length == 0:
        return state

    if current_timestamp >= epoch_id + state.epoch_length:
        # Epoch expired — new epoch, fresh state
        epoch_id = current_timestamp
        acc = 0
        theta = 0
        count = 0

    lifetime = max(block_lifetime, 1)
    return EpochOracleState(
        current_epoch_id=epoch_id,
        epoch_length=state.epoch_length,
        accumulated_sum=acc + x_squared_q128 // lifetime,
        theta_sum=theta + Q128 // lifetime,
        removed_pos_count=count + 1,
    )


def delta_plus_epoch(state: EpochOracleState) -> int:
    """Compute Δ⁺ for epoch state. Formula must match FeeConcentrationStateMod.deltaPlus().

    See also: research/data/scripts/fci_oracle.py for the canonical Python oracle.
    """
    if state.removed_pos_count == 0:
        return 0
    a_t = math.isqrt(state.accumulated_sum << 128)
    n = state.removed_pos_count
    ratio = state.theta_sum // (n * n)
    at_null = math.isqrt(ratio << 128)
    if a_t <= at_null:
        return 0
    result = a_t - at_null
    return min(result, (1 << 128) - 1)


def delta_plus_epoch_view(state: EpochOracleState, current_timestamp: int) -> int:
    """View function: returns 0 if epoch expired (mirrors epochDeltaPlus view)."""
    if state.current_epoch_id == 0:
        return 0
    if current_timestamp >= state.current_epoch_id + state.epoch_length:
        return 0
    return delta_plus_epoch(state)


if __name__ == "__main__":
    # FFI entry point
    # Usage: python fci_epoch_oracle.py <x_squared_q128> <block_lifetime> <epoch_length> <timestamp>
    x_sq = int(sys.argv[1])
    bl = int(sys.argv[2])
    epoch_len = int(sys.argv[3])
    ts = int(sys.argv[4])

    state = init_epoch(epoch_len, ts)
    state = add_term_epoch(state, bl, x_sq, ts)
    dp = delta_plus_epoch(state)
    print(dp)
