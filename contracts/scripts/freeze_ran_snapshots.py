#!/usr/bin/env python3
"""Freeze Angstrom accumulator snapshots for fork test validation.

Usage:
    ETH_RPC_URL=<archive_rpc> python3 scripts/freeze_ran_snapshots.py \
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

# ── Constants ──
ANGSTROM_HOOK = "0x0000000aa232009084bd71a5797d089aa4edfad4"
POOL_MANAGER = "0x000000000004444c5dc75cB358380D2e3dE08A90"
POOL_ID = "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657"
POOL_REWARDS_SLOT = 7
POOLS_SLOT = 6
REWARD_GROWTH_SIZE = 16777216  # 2^24


def keccak_mapping_slot(key_hex: str, mapping_slot: int) -> int:
    """keccak256(abi.encode(key, slot)) — Solidity mapping slot derivation.

    Matches OZ SlotDerivation.deriveMapping(bytes32 slot, bytes32 key):
    memory layout is key || slot, then keccak256 over 64 bytes.
    """
    from eth_abi import encode
    from eth_hash.auto import keccak

    key_bytes = bytes.fromhex(key_hex.replace("0x", "").zfill(64))
    encoded = encode(["bytes32", "uint256"], [key_bytes, mapping_slot])
    return int.from_bytes(keccak(encoded), "big")


def to_hex256(val: int) -> str:
    """Encode uint256 as 0x-prefixed 64-char hex (66 chars total).

    Required for Forge's vm.parseJson — variable-length hex strings
    are misinterpreted as left-aligned bytes, not right-aligned numbers.
    """
    return "0x" + val.to_bytes(32, "big").hex()


def tick_to_uint24(tick: int) -> int:
    """int24 → uint24 wrapping (two's complement). Critical for negative ticks.

    Examples:
      tick_to_uint24(-1200) == 16776016
      tick_to_uint24(199890) == 199890
      tick_to_uint24(0) == 0
    """
    return tick & 0xFFFFFF


def read_storage_at(address: str, slot: int, block: int) -> int:
    """Read a storage slot via cast storage at a specific block."""
    rpc = os.environ["ETH_RPC_URL"]
    slot_hex = hex(slot)
    result = subprocess.run(
        ["cast", "storage", address, slot_hex, "--block", str(block), "--rpc-url", rpc],
        capture_output=True, text=True, check=True,
    )
    return int(result.stdout.strip(), 16)


def read_current_tick(pool_id_hex: str, block: int) -> int:
    """Read current tick from V4 PoolManager slot0 at a specific block.

    V4 Slot0 layout (from v4-core/src/types/Slot0.sol):
      24 bits empty | 24 bits lpFee | 12 bits protocolFee 1→0 |
      12 bits protocolFee 0→1 | 24 bits tick | 160 bits sqrtPriceX96

    tick is extracted via: signextend(2, shr(160, packed))
    """
    base = keccak_mapping_slot(pool_id_hex, POOLS_SLOT)
    raw = read_storage_at(POOL_MANAGER, base, block)
    # Extract tick from bits 160-183
    tick_uint24 = (raw >> 160) & 0xFFFFFF
    # Convert uint24 back to int24 (sign extend from bit 23)
    if tick_uint24 >= (1 << 23):
        return tick_uint24 - (1 << 24)
    return tick_uint24


def compute_growth_inside(
    global_growth: int,
    outside_below: int,
    outside_above: int,
    current_tick: int,
    tick_lower: int,
    tick_upper: int,
) -> int:
    """Three-branch growthInside computation (unchecked uint256 arithmetic).

    Matches ran.sol growthInside():
      currentTick < tickLower:  outsideBelow - outsideAbove
      currentTick >= tickUpper: outsideAbove - outsideBelow
      else (in range):          globalGrowth - outsideBelow - outsideAbove
    """
    MOD = 1 << 256
    if current_tick < tick_lower:
        return (outside_below - outside_above) % MOD
    elif current_tick >= tick_upper:
        return (outside_above - outside_below) % MOD
    else:
        return (global_growth - outside_below - outside_above) % MOD


def freeze_snapshot(block: int, tick_lower: int, tick_upper: int) -> dict[str, Any]:
    """Freeze all accumulator values at a specific block."""
    base = keccak_mapping_slot(POOL_ID, POOL_REWARDS_SLOT)

    global_growth = read_storage_at(ANGSTROM_HOOK, base + REWARD_GROWTH_SIZE, block)
    outside_below = read_storage_at(
        ANGSTROM_HOOK, base + tick_to_uint24(tick_lower), block
    )
    outside_above = read_storage_at(
        ANGSTROM_HOOK, base + tick_to_uint24(tick_upper), block
    )
    current_tick = read_current_tick(POOL_ID, block)

    # Validate non-zero — if archive RPC lacks this block, cast returns 0 silently
    assert (
        global_growth != 0
    ), f"globalGrowth is zero at block {block} — archive RPC may not serve this block"

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
    rpc = os.environ["ETH_RPC_URL"]
    result = subprocess.run(
        ["cast", "block", str(block), "--field", "timestamp", "--rpc-url", rpc],
        capture_output=True, text=True, check=True,
    )
    timestamp = int(result.stdout.strip())

    # Keys in alphabetical order — Forge's vm.parseJson + abi.decode
    # requires struct fields to match alphabetical key ordering
    return {
        "blockNumber": block,
        "blockTimestamp": timestamp,
        "currentTick": current_tick,
        "expectedGrowthInside": to_hex256(expected_gi),
        "globalGrowth": to_hex256(global_growth),
        "outsideAbove": to_hex256(outside_above),
        "outsideBelow": to_hex256(outside_below),
    }, branch


def main():
    parser = argparse.ArgumentParser(description="Freeze Angstrom accumulator snapshots")
    parser.add_argument("--blocks", required=True, help="Comma-separated block numbers")
    parser.add_argument("--tick-lower", required=True, type=int, help="int24 tick lower")
    parser.add_argument("--tick-upper", required=True, type=int, help="int24 tick upper")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    if "ETH_RPC_URL" not in os.environ:
        print("ERROR: ETH_RPC_URL not set. Need an archive RPC.", file=sys.stderr)
        sys.exit(1)

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
        snap, branch = freeze_snapshot(block, args.tick_lower, args.tick_upper)
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
