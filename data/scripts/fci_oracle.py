#!/usr/bin/env python3
"""
FCI Oracle — replays Fee Concentration Index math against raw V4 events.

Reads:  data/raw/fci_weth_usdc_v4_events.json
Writes: data/fixtures/fci_weth_usdc_v4.json

Dependencies: pycryptodome   (pip install pycryptodome)
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Keccak-256 helper (using pycryptodome)
# ---------------------------------------------------------------------------
from Crypto.Hash import keccak as _keccak_mod


def keccak256(data: bytes) -> bytes:
    return _keccak_mod.new(data=data, digest_bits=256).digest()


# ---------------------------------------------------------------------------
# abi.encodePacked helpers
# ---------------------------------------------------------------------------

def _encode_address(addr: str) -> bytes:
    """20 bytes from a hex address string."""
    return bytes.fromhex(addr.removeprefix("0x").lower())


def _encode_int24(val: int) -> bytes:
    """3 bytes, signed, big-endian."""
    return val.to_bytes(3, byteorder="big", signed=True)


def _encode_bytes32(val: str) -> bytes:
    """32 bytes from a hex string."""
    raw = bytes.fromhex(val.removeprefix("0x").lower())
    return raw.rjust(32, b"\x00")


def position_key(sender: str, tick_lower: int, tick_upper: int, salt: str) -> bytes:
    """keccak256(abi.encodePacked(sender, tickLower, tickUpper, salt))"""
    packed = (
        _encode_address(sender)
        + _encode_int24(tick_lower)
        + _encode_int24(tick_upper)
        + _encode_bytes32(salt)
    )
    return keccak256(packed)


def range_key(tick_lower: int, tick_upper: int) -> bytes:
    """keccak256(abi.encodePacked(tickLower, tickUpper))"""
    packed = _encode_int24(tick_lower) + _encode_int24(tick_upper)
    return keccak256(packed)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

Q128 = 1 << 128
INDEX_ONE = (1 << 128) - 1  # type(uint128).max


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PositionInfo:
    liquidity: int
    add_block: int
    baseline_swap_count: int


@dataclass
class TickRangeInfo:
    total_liquidity: int = 0
    swap_count: int = 0
    positions: Dict[bytes, PositionInfo] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# FCI State Machine
# ---------------------------------------------------------------------------

class FCIState:
    def __init__(self):
        # range_key -> TickRangeInfo
        self.ranges: Dict[bytes, TickRangeInfo] = {}
        # position_key -> range_key (lookup for deregistration)
        self.pos_to_range: Dict[bytes, bytes] = {}
        # Global accumulators
        self.accumulated_sum: int = 0
        self.theta_sum: int = 0
        self.pos_count: int = 0
        # Tick tracking for swaps
        self.last_known_tick: Optional[int] = None

    def _get_or_create_range(self, rk: bytes) -> TickRangeInfo:
        if rk not in self.ranges:
            self.ranges[rk] = TickRangeInfo()
        return self.ranges[rk]

    # -- Register (add liquidity) ------------------------------------------
    def register(self, sender: str, tick_lower: int, tick_upper: int,
                 salt: str, liquidity_delta: int, block_number: int):
        pk = position_key(sender, tick_lower, tick_upper, salt)
        rk = range_key(tick_lower, tick_upper)
        tr = self._get_or_create_range(rk)

        # Add position (re-add overwrites baseline/addBlock, adds liquidity again)
        tr.positions[pk] = PositionInfo(
            liquidity=liquidity_delta,
            add_block=block_number,
            baseline_swap_count=tr.swap_count,
        )
        tr.total_liquidity += liquidity_delta
        self.pos_to_range[pk] = rk
        self.pos_count += 1

    # -- Deregister (remove liquidity) -------------------------------------
    def deregister(self, sender: str, tick_lower: int, tick_upper: int,
                   salt: str, block_number: int):
        pk = position_key(sender, tick_lower, tick_upper, salt)

        # Skip orphan positions never registered in our window
        if pk not in self.pos_to_range:
            return

        rk = self.pos_to_range[pk]
        tr = self.ranges.get(rk)
        if tr is None or pk not in tr.positions:
            return

        pos = tr.positions[pk]

        swap_lifetime = tr.swap_count - pos.baseline_swap_count
        block_lifetime = block_number - pos.add_block
        if block_lifetime == 0:
            block_lifetime = 1

        # total_liquidity is NOT decremented per-position for FCI calc
        total_liq = tr.total_liquidity

        if swap_lifetime > 0 and total_liq > 0:
            # x_k = posLiquidity * Q128 // totalRangeLiquidity
            x_k = pos.liquidity * Q128 // total_liq
            # xSquared = x_k * x_k // Q128
            x_squared = x_k * x_k // Q128
            # accumulatedSum += xSquared // blockLifetime
            self.accumulated_sum += x_squared // block_lifetime
            # thetaSum += Q128 // blockLifetime
            self.theta_sum += Q128 // block_lifetime

        self.pos_count -= 1

        # Remove position from range
        del tr.positions[pk]
        del self.pos_to_range[pk]

        # If range empty, reset
        if not tr.positions:
            tr.total_liquidity = 0
            tr.swap_count = 0

    # -- Swap --------------------------------------------------------------
    def process_swap(self, swap_tick: int):
        tick_after = swap_tick

        if self.last_known_tick is None:
            # First swap — no prior tick, so no range to sweep
            self.last_known_tick = tick_after
            return

        tick_before = self.last_known_tick
        tick_min = min(tick_before, tick_after)
        tick_max = max(tick_before, tick_after)

        # Increment swap count for intersecting ranges
        for rk, tr in self.ranges.items():
            if not tr.positions:
                continue
            # Recover tick bounds from positions (all positions in a range
            # share the same tickLower/tickUpper).  We store them when creating
            # the range, but actually the range_key is derived from them.
            # We need the actual tick bounds.  Let's store them.
            pass

        # We need tick bounds per range. Refactor: store them.
        # This is handled via _range_ticks populated during register/deregister.
        for rk, (rl, ru) in self._range_ticks.items():
            tr = self.ranges.get(rk)
            if tr is None or not tr.positions:
                continue
            # intersects: lower < tickMax && upper > tickMin
            if rl < tick_max and ru > tick_min:
                tr.swap_count += 1

        self.last_known_tick = tick_after

    # -- Index computation -------------------------------------------------
    def to_index_a(self) -> int:
        if self.accumulated_sum >= Q128:
            return INDEX_ONE
        a = math.isqrt(self.accumulated_sum << 128)
        return min(a, INDEX_ONE)

    def snapshot(self) -> dict:
        return {
            "expectedIndexA": str(self.to_index_a()),
            "expectedThetaSum": str(self.theta_sum),
            "expectedPosCount": str(self.pos_count),
            "expectedAccumulatedSum": str(self.accumulated_sum),
        }


# ---------------------------------------------------------------------------
# Patched FCIState with tick-range tracking
# ---------------------------------------------------------------------------
# We need to track (tickLower, tickUpper) per range_key for swap intersection.
# Monkey-patching is ugly; let's use an init override instead.

class FCIStateV2(FCIState):
    """FCIState with range tick tracking for swap intersection."""

    def __init__(self):
        super().__init__()
        self._range_ticks: Dict[bytes, Tuple[int, int]] = {}

    def register(self, sender: str, tick_lower: int, tick_upper: int,
                 salt: str, liquidity_delta: int, block_number: int):
        rk = range_key(tick_lower, tick_upper)
        self._range_ticks[rk] = (tick_lower, tick_upper)
        super().register(sender, tick_lower, tick_upper, salt,
                         liquidity_delta, block_number)

    def deregister(self, sender: str, tick_lower: int, tick_upper: int,
                   salt: str, block_number: int):
        super().deregister(sender, tick_lower, tick_upper, salt, block_number)
        # Clean up tick tracking if range is now empty
        rk = range_key(tick_lower, tick_upper)
        tr = self.ranges.get(rk)
        if tr is not None and not tr.positions:
            self._range_ticks.pop(rk, None)


# ---------------------------------------------------------------------------
# Main replay logic
# ---------------------------------------------------------------------------

SNAPSHOT_BLOCKS = [23659523, 23662024, 23665656, 23667514]


def replay(events: list) -> Tuple[FCIStateV2, list]:
    state = FCIStateV2()
    snapshots = []
    snapshot_set = set(SNAPSHOT_BLOCKS)

    # Group events by block for snapshot-after-block semantics
    block_groups: Dict[int, list] = {}
    for idx, ev in enumerate(events):
        bn = ev["blockNumber"]
        if bn not in block_groups:
            block_groups[bn] = []
        block_groups[bn].append((idx, ev))

    sorted_blocks = sorted(block_groups.keys())

    for bn in sorted_blocks:
        group = block_groups[bn]
        for idx, ev in group:
            if ev["eventType"] == "Swap":
                state.process_swap(ev["swapTick"])
            elif ev["eventType"] == "ModifyLiquidity":
                liq_delta = int(ev["liquidityDelta"])
                if liq_delta > 0:
                    # Add / increase
                    state.register(
                        sender=ev["sender"],
                        tick_lower=ev["tickLower"],
                        tick_upper=ev["tickUpper"],
                        salt=ev["salt"],
                        liquidity_delta=liq_delta,
                        block_number=bn,
                    )
                elif liq_delta < 0:
                    # Remove
                    state.deregister(
                        sender=ev["sender"],
                        tick_lower=ev["tickLower"],
                        tick_upper=ev["tickUpper"],
                        salt=ev["salt"],
                        block_number=bn,
                    )
                # liq_delta == 0: no-op

        # Check snapshot after processing all events in this block
        if bn in snapshot_set:
            # Find the last event index in this block
            last_idx = group[-1][0]
            snap = state.snapshot()
            snap["blockNumber"] = bn
            snap["afterEventIndex"] = last_idx
            snapshots.append(snap)

    return state, snapshots


def main():
    # Resolve paths relative to the project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    input_path = project_root / "data" / "raw" / "fci_weth_usdc_v4_events.json"
    output_path = project_root / "data" / "fixtures" / "fci_weth_usdc_v4.json"

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r") as f:
        raw = json.load(f)

    events = raw["events"]
    print(f"Loaded {len(events)} events from {input_path}")

    state, snapshots = replay(events)

    # Build output
    output = {
        "pool": raw["pool"],
        "forkBlock": raw["forkBlock"],
        "events": events,
        "snapshots": snapshots,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(snapshots)} snapshots to {output_path}")

    # Print snapshot summary
    for snap in snapshots:
        print(
            f"  Block {snap['blockNumber']}: "
            f"indexA={snap['expectedIndexA']}, "
            f"posCount={snap['expectedPosCount']}, "
            f"accSum={snap['expectedAccumulatedSum']}, "
            f"thetaSum={snap['expectedThetaSum']}"
        )


if __name__ == "__main__":
    main()
