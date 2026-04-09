# RAN Fork Test: Accumulator Snapshot Validation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single fork test that validates the `AngstromRANOracleAdapter` reads against pre-frozen on-chain accumulator data at specific Ethereum blocks.

**Architecture:** Two phases — (1) a data-freezing step using Dune MCP for block discovery + archive RPC for slot reads, producing a JSON fixture; (2) a Solidity fork test that reads the fixture, rolls to each block, and asserts exact equality between the adapter and the frozen values.

**Tech Stack:** Forge (fork test, vm.readFile, vm.parseJson, vm.rollFork), Dune MCP (block discovery), archive RPC via cast (slot reads), Python (freezing script for slot computation and JSON generation).

**Design Spec:** `docs/superpowers/specs/2026-04-07-ran-fork-test-design.md`

---

## File Structure

```
test/
├── _fixtures/
│   └── ran_accumulator_snapshots.json   # Frozen accumulator data (3-5 block snapshots)
└── AngstromRANOracleAdapter.fork.t.sol  # Fork test: single test function

scripts/
└── freeze_ran_snapshots.py              # Freezing script: Dune discovery + RPC slot reads
```

---

## Task 1: Update foundry.toml — Add Fixture Read Permission

**Files:** Modify `foundry.toml`

- [ ] **Step 1:** Add `test/_fixtures` to `fs_permissions`

Change:
```toml
fs_permissions = [{ access = "read-write", path = ".forge-snapshots/" }]
```

To:
```toml
fs_permissions = [
  { access = "read-write", path = ".forge-snapshots/" },
  { access = "read", path = "test/_fixtures/" }
]
```

- [ ] **Step 2:** Create the fixture directory

```bash
mkdir -p test/_fixtures
```

- [ ] **Step 3:** Verify compilation still passes

```bash
forge build
```

- [ ] **Step 4:** Commit

```bash
git add foundry.toml test/_fixtures/
git commit -m "chore: add test/_fixtures read permission for fork test fixtures"
```

---

## Task 2: Discover Blocks and Tick Range via Dune MCP

**Files:** None (MCP queries, output is manual notes for Task 3)

This task uses the Dune MCP to find:
1. 3-5 blocks in Period 3 (≥ 22_200_000) where Angstrom's `globalGrowth` incremented
2. An active LP tick range with non-zero `rewardGrowthOutside` on both boundaries

- [ ] **Step 1:** Query Dune for recent Angstrom execute() transactions

Use `mcp__dune__executeQueryById` or `mcp__dune__createDuneQuery` to find blocks where the Angstrom hook at `0x0000000aa232009084bd71a5797d089aa4edfad4` was called (the `execute()` function distributes rewards). Filter to blocks ≥ 22_200_000.

Example SQL:
```sql
SELECT block_number, block_time, tx_hash
FROM ethereum.transactions
WHERE "to" = 0x0000000aa232009084bd71a5797d089aa4edfad4
  AND block_number >= 22200000
ORDER BY block_number DESC
LIMIT 20
```

Pick 3-5 blocks spaced across at least 100 blocks apart (to see growth accumulation).

- [ ] **Step 2:** Query Dune for active LP positions on the target pool

Find positions with liquidity added to pool `0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657` that are still active. Extract their `tickLower` and `tickUpper`.

- [ ] **Step 3:** Record the discovered values

Note down:
- 3-5 block numbers
- One `[tickLower, tickUpper)` range from an active position
- Verify at least one of the selected blocks has `currentTick` within the discovered range (for in-range branch testing)

---

## Task 3: Write Freezing Script

**Files:** Create `scripts/freeze_ran_snapshots.py`

The script reads Angstrom storage slots at each discovered block via archive RPC and produces the JSON fixture.

- [ ] **Step 1:** Write the freezing script

```python
#!/usr/bin/env python3
"""Freeze Angstrom accumulator snapshots for fork test validation.

Usage:
    ETH_RPC_URL=<archive_rpc> python3 scripts/freeze_ran_snapshots.py \
        --blocks 22200100,22200200,22200300 \
        --tick-lower -1200 \
        --tick-upper -600 \
        --output test/_fixtures/ran_accumulator_snapshots.json
"""

import argparse
import json
import subprocess
import sys
from typing import Any

# ── Constants ──
ANGSTROM_HOOK = "0x0000000aa232009084bd71a5797d089aa4edfad4"
POOL_MANAGER = "0x000000000004444c5dc75cB358380D2e3dE08A90"
POOL_ID = "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657"
POOL_REWARDS_SLOT = 7
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
    """int24 → uint24 wrapping (two's complement). Critical for negative ticks."""
    return tick & 0xFFFFFF


def read_storage_at(address: str, slot: int, block: int) -> int:
    """Read a storage slot via cast storage at a specific block."""
    import os
    rpc = os.environ["ETH_RPC_URL"]
    slot_hex = hex(slot)
    result = subprocess.run(
        ["cast", "storage", address, slot_hex, "--block", str(block), "--rpc-url", rpc],
        capture_output=True, text=True, check=True
    )
    return int(result.stdout.strip(), 16)


def read_current_tick(pool_id_hex: str, block: int) -> int:
    """Read current tick from V4 PoolManager slot0 at a specific block.

    V4 Slot0 layout: sqrtPriceX96 (160 bits) | tick (24 bits) | ...
    tick is at bits 160-183.
    """
    # Pool state slot = keccak256(abi.encode(poolId, POOLS_SLOT=6)) + 0
    base = keccak_mapping_slot(pool_id_hex, 6)
    raw = read_storage_at(POOL_MANAGER, base, block)
    # Extract tick from bits 160-183
    tick_uint24 = (raw >> 160) & 0xFFFFFF
    # Convert uint24 back to int24
    if tick_uint24 >= (1 << 23):
        return tick_uint24 - (1 << 24)
    return tick_uint24


def compute_growth_inside(
    global_growth: int, outside_below: int, outside_above: int, current_tick: int,
    tick_lower: int, tick_upper: int
) -> int:
    """Three-branch growthInside computation (unchecked uint256 arithmetic)."""
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
    outside_below = read_storage_at(ANGSTROM_HOOK, base + tick_to_uint24(tick_lower), block)
    outside_above = read_storage_at(ANGSTROM_HOOK, base + tick_to_uint24(tick_upper), block)
    current_tick = read_current_tick(POOL_ID, block)

    expected_gi = compute_growth_inside(
        global_growth, outside_below, outside_above, current_tick, tick_lower, tick_upper
    )

    # Read block timestamp via cast
    import os
    rpc = os.environ["ETH_RPC_URL"]
    result = subprocess.run(
        ["cast", "block", str(block), "--field", "timestamp", "--rpc-url", rpc],
        capture_output=True, text=True, check=True
    )
    timestamp = int(result.stdout.strip())

    # Validate non-zero — if archive RPC lacks this block, cast returns 0 silently
    assert global_growth != 0, f"globalGrowth is zero at block {block} — archive RPC may not serve this block"

    return {
        "blockNumber": block,
        "blockTimestamp": timestamp,
        "currentTick": current_tick,
        "expectedGrowthInside": to_hex256(expected_gi),
        "globalGrowth": to_hex256(global_growth),
        "outsideAbove": to_hex256(outside_above),
        "outsideBelow": to_hex256(outside_below),
    }


def main():
    parser = argparse.ArgumentParser(description="Freeze Angstrom accumulator snapshots")
    parser.add_argument("--blocks", required=True, help="Comma-separated block numbers")
    parser.add_argument("--tick-lower", required=True, type=int, help="int24 tick lower")
    parser.add_argument("--tick-upper", required=True, type=int, help="int24 tick upper")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    blocks = [int(b.strip()) for b in args.blocks.split(",")]

    print(f"Freezing {len(blocks)} snapshots for ticks [{args.tick_lower}, {args.tick_upper})...")

    snapshots = []
    for block in sorted(blocks):
        print(f"  Block {block}...", end=" ", flush=True)
        snap = freeze_snapshot(block, args.tick_lower, args.tick_upper)
        snapshots.append(snap)
        print(f"tick={snap['currentTick']}, globalGrowth={snap['globalGrowth'][:18]}...")

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
```

- [ ] **Step 2:** Install Python dependencies into the project venv

```bash
source .venv/bin/activate
pip install eth-abi eth-hash[pycryptodome]
```

Note: The Angstrom repo uses `.venv/` (per README). If using the thetaSwap `uhi8/` venv instead, replace `source .venv/bin/activate` with `source ../../uhi8/bin/activate` throughout.

- [ ] **Step 3:** Run the freezing script with discovered blocks from Task 2

```bash
source .venv/bin/activate
ETH_RPC_URL=<archive_rpc> python3 scripts/freeze_ran_snapshots.py \
    --blocks <block1>,<block2>,<block3> \
    --tick-lower <discovered_tick_lower> \
    --tick-upper <discovered_tick_upper> \
    --output test/_fixtures/ran_accumulator_snapshots.json
```

- [ ] **Step 4:** Verify the fixture looks correct

```bash
cat test/_fixtures/ran_accumulator_snapshots.json | python3 -m json.tool | head -30
```

Check: all hex values are non-zero, `blockNumber` is ascending, at least one snapshot has `currentTick` in range.

- [ ] **Step 5:** Commit

```bash
git add scripts/freeze_ran_snapshots.py test/_fixtures/ran_accumulator_snapshots.json
git commit -m "data: freeze Angstrom accumulator snapshots for fork test"
```

---

## Task 4: Write Fork Test

**Files:** Create `test/AngstromRANOracleAdapter.fork.t.sol`

- [ ] **Step 1:** Write the fork test

```solidity
// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import "forge-std/Test.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {IAngstromAuth} from "core/src/interfaces/IAngstromAuth.sol";
import {AngstromRANOracleAdapter} from "core/src/ran.sol";

/// @title AngstromRANOracleAdapter Fork Test
/// @notice Validates adapter reads against pre-frozen on-chain accumulator snapshots.
/// @dev Requires ETH_RPC_URL pointing to an archive node.
///      Fixture: test/_fixtures/ran_accumulator_snapshots.json
contract AngstromRANOracleAdapterForkTest is Test {
    string constant FIXTURE_PATH = "test/_fixtures/ran_accumulator_snapshots.json";

    AngstromRANOracleAdapter adapter;
    PoolId poolId;
    int24 tickLower;
    int24 tickUpper;

    /// @dev Fields MUST be alphabetical by JSON key name — Forge's vm.parseJson
    ///      encodes object fields in alphabetical order for abi.decode.
    struct Snapshot {
        uint256 blockNumber;
        uint256 blockTimestamp;
        int256 currentTick;
        uint256 expectedGrowthInside;
        uint256 globalGrowth;
        uint256 outsideAbove;
        uint256 outsideBelow;
    }

    function test_accumulatorSnapshotsMatchFixture() public {
        // ── Read fixture ──
        string memory json = vm.readFile(FIXTURE_PATH);

        address angstromHook = vm.parseJsonAddress(json, ".pool.angstromHook");
        address poolManager = vm.parseJsonAddress(json, ".pool.poolManager");
        tickLower = int24(vm.parseJsonInt(json, ".pool.tickLower"));
        tickUpper = int24(vm.parseJsonInt(json, ".pool.tickUpper"));
        poolId = PoolId.wrap(vm.parseJsonBytes32(json, ".pool.poolId"));

        // ── Count snapshots ──
        bytes memory snapshotsRaw = vm.parseJson(json, ".snapshots");
        Snapshot[] memory snapshots = abi.decode(snapshotsRaw, (Snapshot[]));
        uint256 n = snapshots.length;
        require(n >= 3, "Fixture must have at least 3 snapshots");

        // ── Fork at first block ──
        uint256 forkId = vm.createFork(
            vm.envString("ETH_RPC_URL"),
            snapshots[0].blockNumber
        );
        vm.selectFork(forkId);

        // ── Deploy adapter on fork ──
        adapter = new AngstromRANOracleAdapter(
            IAngstromAuth(angstromHook),
            IPoolManager(poolManager)
        );

        uint256 prevGlobalGrowth = 0;

        for (uint256 i; i < n; i++) {
            Snapshot memory snap = snapshots[i];

            // Roll to snapshot block
            vm.rollFork(snap.blockNumber);

            // ── Assert globalGrowth (exact) ──
            uint256 adapterGG = adapter.globalGrowth(poolId);
            assertEq(
                adapterGG,
                snap.globalGrowth,
                string.concat(
                    "globalGrowth mismatch at block ",
                    vm.toString(snap.blockNumber)
                )
            );

            // ── Assert growthInside (exact) ──
            uint256 adapterGI = adapter.growthInside(poolId, tickLower, tickUpper);
            assertEq(
                adapterGI,
                snap.expectedGrowthInside,
                string.concat(
                    "growthInside mismatch at block ",
                    vm.toString(snap.blockNumber)
                )
            );

            // ── Conservation cross-check (in-range snapshots) ──
            int24 snapTick = int24(snap.currentTick);
            if (snapTick >= tickLower && snapTick < tickUpper) {
                uint256 conservationGI;
                unchecked {
                    conservationGI = snap.globalGrowth - snap.outsideBelow - snap.outsideAbove;
                }
                assertEq(
                    snap.expectedGrowthInside,
                    conservationGI,
                    string.concat(
                        "Conservation violated at block ",
                        vm.toString(snap.blockNumber)
                    )
                );
            }

            // ── Monotonicity ──
            if (i > 0) {
                assertGe(
                    adapterGG,
                    prevGlobalGrowth,
                    string.concat(
                        "globalGrowth decreased at block ",
                        vm.toString(snap.blockNumber)
                    )
                );
            }
            prevGlobalGrowth = adapterGG;

            // ── Story-tell ──
            console2.log("Block", snap.blockNumber);
            console2.log("  globalGrowth:", adapterGG);
            console2.log("  growthInside:", adapterGI);
            console2.log("  currentTick:", snapTick);
            console2.log("  ---");
        }
    }
}
```

- [ ] **Step 2:** Verify compilation (no RPC needed for build)

```bash
forge build
```

Expected: compiles with no errors. (`--match-contract` is a `forge test` flag, not `forge build`.)

- [ ] **Step 3:** Run the fork test against archive RPC

```bash
ETH_RPC_URL=<archive_rpc> forge test --match-contract AngstromRANOracleAdapterForkTest -vv
```

Expected: all assertions pass, console output shows accumulator values at each block.

- [ ] **Step 4:** Commit

```bash
git add test/AngstromRANOracleAdapter.fork.t.sol
git commit -m "test(ran): fork test — adapter verified against frozen Angstrom snapshots"
```

---

## Spec Coverage Checklist

| Spec Section | Task | Status |
|---|---|---|
| 1. What We're Building | All tasks | Covered |
| 2. Phase 1: Discovery (Dune) | Task 2 | Covered |
| 2. Phase 1: Slot reads (RPC) | Task 3 | Covered |
| 2. Phase 1: int24→uint24 wrapping | Task 3 (tick_to_uint24) | Covered |
| 2. Phase 1: extsload signature diff | Task 3 (uses eth_getStorageAt, bypasses) | Covered |
| 2. Phase 1: PoolId compatibility | Task 4 (same poolId for both) | Covered |
| 2. Phase 1: Pre-computation | Task 3 (compute_growth_inside) | Covered |
| 2. Phase 1: JSON output format | Task 3 (freeze_snapshot) | Covered |
| 3. Phase 2: Fork test flow | Task 4 | Covered |
| 3. Phase 2: Exact equality (globalGrowth) | Task 4 (assertEq) | Covered |
| 3. Phase 2: Exact equality (growthInside) | Task 4 (assertEq) | Covered |
| 3. Phase 2: Conservation cross-check | Task 4 (in-range check) | Covered |
| 3. Phase 2: Monotonicity | Task 4 (assertGe) | Covered |
| 4. fs_permissions | Task 1 | Covered |
| 5. Run command | Task 4 Step 3 | Covered |
| 6. Period 3 block range | Task 2 (≥ 22_200_000) | Covered |
