#!/usr/bin/env python3
"""
FCI V3 Oracle — replays Fee Concentration Index math against raw V3 events.

Reads:  data/raw/fci_v3_weth_usdc_events.json
Writes: data/fixtures/fci_v3_weth_usdc.json

Key differences from V4:
  - Position key: keccak256(abi.encodePacked(owner, tickLower, tickUpper)) — no salt
  - Events: separate Swap, Mint, Burn, Collect (not ModifyLiquidity)
  - Collect accumulates fees per-position; Burn consumes them to compute FCI term

Dependencies: pycryptodome   (pip install pycryptodome)
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from Crypto.Hash import keccak as _keccak_mod


# ---------------------------------------------------------------------------
# Keccak-256 helper
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Key derivation
# ---------------------------------------------------------------------------

def v3_position_key(owner: str, tick_lower: int, tick_upper: int) -> bytes:
    """keccak256(abi.encodePacked(owner, tickLower, tickUpper))"""
    packed = (
        _encode_address(owner)
        + _encode_int24(tick_lower)
        + _encode_int24(tick_upper)
    )
    return keccak256(packed)


def range_key(tick_lower: int, tick_upper: int) -> bytes:
    """keccak256(abi.encodePacked(tickLower, tickUpper))"""
    packed = _encode_int24(tick_lower) + _encode_int24(tick_upper)
    return keccak256(packed)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

Q128: int = 1 << 128
INDEX_ONE: int = (1 << 128) - 1  # type(uint128).max


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PositionInfo:
    """Per-position tracking state."""
    liquidity: int
    add_block: int
    baseline_swap_count: int
    collected_fee0: int = 0  # Accumulated by Collect, tracked for ReactVM parity (FCI uses liquidity share)
    collected_fee1: int = 0  # Same — not used in FCI formula but mirrors on-chain CollectedFees state


@dataclass
class TickRangeInfo:
    """Per-range aggregate state."""
    total_liquidity: int = 0
    swap_count: int = 0
    positions: Dict[bytes, PositionInfo] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# FCI V3 State Machine
# ---------------------------------------------------------------------------

class FCIStateV3:
    """Replays V3 events to compute the Fee Concentration Index."""

    def __init__(self) -> None:
        self.ranges: Dict[bytes, TickRangeInfo] = {}
        self.pos_to_range: Dict[bytes, bytes] = {}
        self._range_ticks: Dict[bytes, Tuple[int, int]] = {}

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

    # -- Mint (add liquidity) ----------------------------------------------
    def process_mint(
        self,
        owner: str,
        tick_lower: int,
        tick_upper: int,
        liquidity: int,
        block_number: int,
    ) -> None:
        pk = v3_position_key(owner, tick_lower, tick_upper)
        rk = range_key(tick_lower, tick_upper)
        self._range_ticks[rk] = (tick_lower, tick_upper)
        tr = self._get_or_create_range(rk)

        if pk in tr.positions:
            # Re-add: accumulate liquidity, reset baseline/addBlock
            tr.positions[pk].liquidity += liquidity
            tr.positions[pk].add_block = block_number
            tr.positions[pk].baseline_swap_count = tr.swap_count
        else:
            tr.positions[pk] = PositionInfo(
                liquidity=liquidity,
                add_block=block_number,
                baseline_swap_count=tr.swap_count,
            )
            self.pos_count += 1

        tr.total_liquidity += liquidity
        self.pos_to_range[pk] = rk

    # -- Burn (remove liquidity) -------------------------------------------
    def process_burn(
        self,
        owner: str,
        tick_lower: int,
        tick_upper: int,
        liquidity: int,
        block_number: int,
    ) -> None:
        pk = v3_position_key(owner, tick_lower, tick_upper)

        # Skip orphan positions never registered in our window
        if pk not in self.pos_to_range:
            return

        rk = self.pos_to_range[pk]
        tr = self.ranges.get(rk)
        if tr is None or pk not in tr.positions:
            return

        pos = tr.positions[pk]

        # Compute FCI term from liquidity share (not fee amounts).
        # total_liquidity is NOT decremented before computing x_k — matches Solidity.
        swap_lifetime = tr.swap_count - pos.baseline_swap_count
        block_lifetime = max(1, block_number - pos.add_block)
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
            self._range_ticks.pop(rk, None)

    # -- Collect (accumulate fees) -----------------------------------------
    def process_collect(
        self,
        owner: str,
        tick_lower: int,
        tick_upper: int,
        fee0: int,
        fee1: int,
    ) -> None:
        """Accumulate collected fees per-position. No FCI term produced yet."""
        pk = v3_position_key(owner, tick_lower, tick_upper)
        rk = range_key(tick_lower, tick_upper)
        tr = self.ranges.get(rk)
        if tr is None or pk not in tr.positions:
            return
        tr.positions[pk].collected_fee0 += fee0
        tr.positions[pk].collected_fee1 += fee1

    # -- Swap --------------------------------------------------------------
    def process_swap(self, tick: int) -> None:
        tick_after = tick

        if self.last_known_tick is None:
            self.last_known_tick = tick_after
            return

        tick_before = self.last_known_tick
        tick_min = min(tick_before, tick_after)
        tick_max = max(tick_before, tick_after)

        # Increment swap count for intersecting ranges
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

    def to_at_null(self) -> int:
        """Competitive null: sqrt(thetaSum / N^2) in Q128."""
        n = self.pos_count
        if n == 0 or self.theta_sum == 0:
            return 0
        ratio = self.theta_sum // (n * n)
        if ratio >= Q128:
            return INDEX_ONE
        a = math.isqrt(ratio << 128)
        return min(a, INDEX_ONE)

    def to_delta_plus(self) -> int:
        """Concentration deviation: max(0, A_T - atNull) in Q128."""
        a = self.to_index_a()
        n = self.to_at_null()
        return max(0, a - n)

    def to_delta_plus_price(self) -> int:
        """Concentration price: delta+ * Q128 / (Q128 - delta+) in Q128."""
        d = self.to_delta_plus()
        if d == 0:
            return 0
        return (d * Q128) // (Q128 - d)

    def snapshot(self, block_number: int) -> dict:
        return {
            "blockNumber": block_number,
            "expectedIndexA": self.to_index_a(),
            "expectedThetaSum": self.theta_sum,
            "expectedPosCount": self.pos_count,
            "expectedAccumulatedSum": self.accumulated_sum,
            "expectedAtNull": self.to_at_null(),
            "expectedDeltaPlus": self.to_delta_plus(),
            "expectedDeltaPlusPrice": self.to_delta_plus_price(),
        }


# ---------------------------------------------------------------------------
# Replay logic
# ---------------------------------------------------------------------------

def replay(
    events: List[dict],
    snapshot_blocks: Optional[List[int]] = None,
) -> Tuple[FCIStateV3, List[dict]]:
    """Replay a list of V3 events through the FCI state machine.

    Args:
        events: List of event dicts with ``eventType`` and block/field data.
        snapshot_blocks: Optional list of block numbers at which to take snapshots.

    Returns:
        Tuple of (final state, list of snapshot dicts).
    """
    state = FCIStateV3()
    snapshots: List[dict] = []
    snapshot_set = set(snapshot_blocks or [])

    # Group events by block for snapshot-after-block semantics
    block_groups: Dict[int, List[Tuple[int, dict]]] = {}
    for idx, ev in enumerate(events):
        bn = ev["blockNumber"]
        if bn not in block_groups:
            block_groups[bn] = []
        block_groups[bn].append((idx, ev))

    sorted_blocks = sorted(block_groups.keys())

    for bn in sorted_blocks:
        group = block_groups[bn]
        for idx, ev in group:
            etype = ev["eventType"]
            if etype == "Swap":
                state.process_swap(tick=ev["tick"])
            elif etype == "Mint":
                state.process_mint(
                    owner=ev["owner"],
                    tick_lower=ev["tickLower"],
                    tick_upper=ev["tickUpper"],
                    liquidity=int(ev["liquidity"]),
                    block_number=bn,
                )
            elif etype == "Burn":
                state.process_burn(
                    owner=ev["owner"],
                    tick_lower=ev["tickLower"],
                    tick_upper=ev["tickUpper"],
                    liquidity=int(ev["liquidity"]),
                    block_number=bn,
                )
            elif etype == "Collect":
                state.process_collect(
                    owner=ev["owner"],
                    tick_lower=ev["tickLower"],
                    tick_upper=ev["tickUpper"],
                    fee0=int(ev.get("fee0", 0)),
                    fee1=int(ev.get("fee1", 0)),
                )

        # Snapshot after processing all events in this block
        if bn in snapshot_set:
            last_idx = group[-1][0]
            snap = state.snapshot(block_number=bn)
            snap["afterEventIndex"] = last_idx
            snapshots.append(snap)

    return state, snapshots


# ---------------------------------------------------------------------------
# Main — file-based replay
# ---------------------------------------------------------------------------

def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    input_path = project_root / "data" / "raw" / "fci_v3_weth_usdc_events.json"
    output_path = project_root / "data" / "fixtures" / "fci_v3_weth_usdc.json"

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r") as f:
        raw = json.load(f)

    events = raw["events"]
    print(f"Loaded {len(events)} events from {input_path}")

    snapshot_blocks = raw.get("snapshotBlocks", [])
    state, snapshots = replay(events, snapshot_blocks=snapshot_blocks)

    output = {
        "pool": raw.get("pool", ""),
        "forkBlock": raw.get("forkBlock", 0),
        "eventCount": len(events),
        "snapshotCount": len(snapshots),
        "events": events,
        "snapshots": snapshots,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(snapshots)} snapshots to {output_path}")

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
