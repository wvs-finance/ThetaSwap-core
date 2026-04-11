#!/usr/bin/env python3
"""Freeze Angstrom accumulator snapshots for fork test validation.

Usage:
    ALCHEMY_API_KEY=<key> python3 scripts/freeze_ran_snapshots.py \
        --blocks 24827762,24827780,24827794,24827806 \
        --tick-lower 199890 \
        --tick-upper 199910 \
        --output test/_fixtures/ran_accumulator_snapshots.json
"""

import argparse
import json
import os
import subprocess
import sys

from typing import Any

from scripts.ran_utils import (
    derive_pool_rewards_slot,
    encode_uint256,
    read_storage_at,
)

# ── Constants ──
ANGSTROM_HOOK = "0x0000000aa232009084bd71a5797d089aa4edfad4"
POOL_MANAGER = "0x000000000004444c5dc75cB358380D2e3dE08A90"
POOL_ID = "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657"
POOL_REWARDS_SLOT = 7
POOLS_SLOT = 6
REWARD_GROWTH_SIZE = 16777216  # 2^24

ALCHEMY_BASE_URL = "https://eth-mainnet.g.alchemy.com/v2/"


# ── Tick function stubs (out of scope — globalGrowth time series only) ──


def tick_to_uint24(tick: int) -> int:
    """Convert a signed int24 tick to unsigned uint24.

    OUT OF SCOPE — stub only. Will be implemented when tick-level
    analysis is added to the pipeline.
    """
    raise NotImplementedError("tick_to_uint24 is out of scope for globalGrowth time series")


def read_current_tick(pool_id: str, block: int) -> int:
    """Read the current tick for a pool at a given block.

    OUT OF SCOPE — stub only.
    """
    raise NotImplementedError("read_current_tick is out of scope for globalGrowth time series")


def compute_growth_inside(
    global_growth: int,
    outside_below: int,
    outside_above: int,
    current_tick: int,
    tick_lower: int,
    tick_upper: int,
) -> int:
    """Compute growthInside from global and outside accumulators.

    OUT OF SCOPE — stub only.
    """
    raise NotImplementedError("compute_growth_inside is out of scope for globalGrowth time series")


def _build_rpc_url() -> str:
    """Build the Alchemy RPC URL from ALCHEMY_API_KEY env var."""
    api_key = os.environ.get("ALCHEMY_API_KEY")
    if not api_key:
        print("ERROR: ALCHEMY_API_KEY not set. Need an archive RPC.", file=sys.stderr)
        sys.exit(1)
    return ALCHEMY_BASE_URL + api_key


def freeze_snapshot(
    block: int, tick_lower: int, tick_upper: int, rpc_url: str,
) -> tuple[dict[str, Any], str]:
    """Freeze all accumulator values at a specific block."""
    global_growth_slot = derive_pool_rewards_slot(POOL_ID, POOL_REWARDS_SLOT, REWARD_GROWTH_SIZE)

    global_growth = read_storage_at(ANGSTROM_HOOK, global_growth_slot, block, rpc_url)
    outside_below = read_storage_at(
        ANGSTROM_HOOK,
        derive_pool_rewards_slot(POOL_ID, POOL_REWARDS_SLOT, 0) + tick_to_uint24(tick_lower),
        block,
        rpc_url,
    )
    outside_above = read_storage_at(
        ANGSTROM_HOOK,
        derive_pool_rewards_slot(POOL_ID, POOL_REWARDS_SLOT, 0) + tick_to_uint24(tick_upper),
        block,
        rpc_url,
    )
    current_tick = read_current_tick(POOL_ID, block)

    if global_growth == 0:
        print(
            f"WARNING: globalGrowth is zero at block {block} — "
            f"archive RPC may not serve this block",
            file=sys.stderr,
        )

    expected_gi = compute_growth_inside(
        global_growth, outside_below, outside_above, current_tick, tick_lower, tick_upper
    )

    # Determine which branch was used
    if current_tick < tick_lower:
        branch = "below"
    elif current_tick >= tick_upper:
        branch = "above"
    else:
        branch = "in-range"

    # Read block timestamp via cast
    result = subprocess.run(
        ["cast", "block", str(block), "--field", "timestamp", "--rpc-url", rpc_url],
        capture_output=True, text=True, check=True,
    )
    timestamp = int(result.stdout.strip())

    # Keys in alphabetical order — Forge's vm.parseJson + abi.decode
    # requires struct fields to match alphabetical key ordering
    return {
        "blockNumber": block,
        "blockTimestamp": timestamp,
        "currentTick": current_tick,
        "expectedGrowthInside": encode_uint256(expected_gi),
        "globalGrowth": encode_uint256(global_growth),
        "outsideAbove": encode_uint256(outside_above),
        "outsideBelow": encode_uint256(outside_below),
    }, branch


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze Angstrom accumulator snapshots")
    parser.add_argument("--blocks", required=True, help="Comma-separated block numbers")
    parser.add_argument("--tick-lower", required=True, type=int, help="int24 tick lower")
    parser.add_argument("--tick-upper", required=True, type=int, help="int24 tick upper")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    rpc_url = _build_rpc_url()

    blocks = [int(b.strip()) for b in args.blocks.split(",")]

    print(
        f"Freezing {len(blocks)} snapshots for ticks [{args.tick_lower}, {args.tick_upper})..."
    )
    print(f"  uint24(tickLower) = {tick_to_uint24(args.tick_lower)}")
    print(f"  uint24(tickUpper) = {tick_to_uint24(args.tick_upper)}")
    print()

    snapshots = []
    for block in sorted(blocks):
        print(f"  Block {block}...", end=" ", flush=True)
        snap, branch = freeze_snapshot(block, args.tick_lower, args.tick_upper, rpc_url)
        snapshots.append(snap)
        print(
            f"tick={snap['currentTick']}, branch={branch}, "
            f"globalGrowth={snap['globalGrowth'][:18]}..."
        )

    fixture = {
        "pool": {
            "poolId": POOL_ID,
            "angstromHook": ANGSTROM_HOOK,
            "poolManager": POOL_MANAGER,
            "tickLower": args.tick_lower,
            "tickUpper": args.tick_upper,
        },
        "snapshots": snapshots,
    }

    with open(args.output, "w") as f:
        json.dump(fixture, f, indent=2, sort_keys=False)

    print(f"\nFixture written to {args.output} ({len(snapshots)} snapshots)")


if __name__ == "__main__":
    main()
