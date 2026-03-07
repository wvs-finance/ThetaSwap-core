# FCI Fork Test Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Validate FeeConcentrationIndex accuracy against real Uniswap V4 WETH/USDC mainnet data via fork replay.

**Architecture:** Dune SQL query exports ~50 lifecycle events. Python oracle replays them through exact Q128 math and bakes expected FCI values into a JSON fixture. Forge fork test deploys the harness on a mainnet fork, replays events by calling hook functions directly, and asserts index values match the oracle at snapshot blocks.

**Tech Stack:** Dune Analytics (SQL), Python 3 (integer math), Forge (fork testing, vm.readFile/vm.parseJson), Solidity ^0.8.26

---

## Task 1: Discover WETH/USDC V4 Pool ID via Dune

**Files:**
- Create: `data/queries/fci_weth_usdc_v4.sql`

**Step 1: Create the queries directory**

```bash
mkdir -p data/queries
```

**Step 2: Write the pool discovery query**

Write `data/queries/fci_weth_usdc_v4.sql` with two sections. First, the pool discovery query:

```sql
-- Section 1: Find WETH/USDC V4 pool on Ethereum mainnet
-- WETH: 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
-- USDC: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
SELECT
    id as pool_id,
    currency0,
    currency1,
    fee,
    tickSpacing,
    hooks,
    tick as init_tick,
    sqrtPriceX96 as init_sqrtPriceX96,
    evt_block_number as init_block
FROM uniswap_v4_ethereum.poolmanager_evt_initialize
WHERE (
    (currency0 = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
     AND currency1 = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2)
    OR
    (currency0 = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
     AND currency1 = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)
)
ORDER BY evt_block_number ASC
LIMIT 10;
```

**Step 3: Run the pool discovery query via Dune MCP**

Use `mcp__dune__createDuneQuery` to create and `mcp__dune__executeQueryById` to run it. Record the `pool_id`, `fee`, `tickSpacing`, `hooks`, and `init_block` for the most active pool.

**Step 4: Write the event stream query**

Append to `data/queries/fci_weth_usdc_v4.sql`:

```sql
-- Section 2: Export ~50 lifecycle events for the target pool
-- Replace <POOL_ID> with the id from Section 1
WITH events AS (
    SELECT
        evt_block_number as block_number,
        evt_tx_hash as tx_hash,
        evt_index as log_index,
        'ModifyLiquidity' as event_type,
        sender,
        tickLower as tick_lower,
        tickUpper as tick_upper,
        liquidityDelta as liquidity_delta,
        CAST(NULL AS INTEGER) as swap_tick,
        CAST(NULL AS uint256) as sqrtPriceX96,
        CAST(NULL AS uint256) as swap_liquidity
    FROM uniswap_v4_ethereum.poolmanager_evt_modifyliquidity
    WHERE id = <POOL_ID>

    UNION ALL

    SELECT
        evt_block_number as block_number,
        evt_tx_hash as tx_hash,
        evt_index as log_index,
        'Swap' as event_type,
        sender,
        CAST(NULL AS INTEGER) as tick_lower,
        CAST(NULL AS INTEGER) as tick_upper,
        CAST(NULL AS int256) as liquidity_delta,
        tick as swap_tick,
        sqrtPriceX96,
        liquidity as swap_liquidity
    FROM uniswap_v4_ethereum.poolmanager_evt_swap
    WHERE id = <POOL_ID>
)
SELECT *
FROM events
ORDER BY block_number ASC, log_index ASC
LIMIT 50;
```

**Step 5: Run the event stream query via Dune MCP**

Execute via Dune MCP. Save the raw results for the Python oracle (Task 2).

**Step 6: Commit**

```bash
git add -f data/queries/fci_weth_usdc_v4.sql
git commit -m "data(fci): Dune SQL queries for WETH/USDC V4 event export"
```

---

## Task 2: Write Python Oracle Script

**Files:**
- Create: `data/scripts/fci_oracle.py`
- Create: `data/scripts/requirements.txt`

**Step 1: Create the scripts directory**

```bash
mkdir -p data/scripts
```

**Step 2: Write requirements.txt**

```
# No external dependencies -- pure Python integer math
```

**Step 3: Write fci_oracle.py**

The oracle must replicate the exact Solidity math:
- `Q128 = 1 << 128`
- `INDEX_ONE = (1 << 128) - 1`
- `isqrt(n)` = integer square root (Python 3.8+ has `math.isqrt`)
- `addTerm(state, block_lifetime, x_squared_q128)`:
  - `lifetime = max(block_lifetime, 1)` (floorOne)
  - `state.accumulated_sum += x_squared_q128 // lifetime`
  - `state.theta_sum += Q128 // lifetime`
- `toIndexA(state)`:
  - if `accumulated_sum >= Q128`: return `INDEX_ONE`
  - `a = isqrt(accumulated_sum << 128)`
  - return `min(a, INDEX_ONE)`
- `fromFeeGrowthDelta(range_now, pos_last, baseline, pos_liq, total_liq)`:
  - `pos_fee_delta = range_now - pos_last` (wrapping uint256 subtraction)
  - `range_fee_delta = range_now - baseline`
  - `fee_ratio_q128 = mulDiv(pos_fee_delta, Q128, range_fee_delta)` if range_fee_delta > 0 else 0
  - `ratio = mulDiv(fee_ratio_q128, pos_liq, total_liq)` capped at INDEX_ONE
  - return ratio
- `square(x)`: `(x * x) // Q128`
- `mulDiv(a, b, c)`: `(a * b) // c` (Python int handles arbitrary precision)

The script:
1. Reads a JSON file of raw Dune events (from Task 1 output, manually saved)
2. Replays events in order, maintaining per-position and per-range state:
   - `positions`: dict of `positionKey -> {tickLower, tickUpper, liquidity, addBlock, baselineSwapCount, feeGrowthBaseline0}`
   - `ranges`: dict of `rangeKey -> {positions: set, swapCount, totalLiquidity, tickLower, tickUpper}`
   - `fci_state`: `{accumulated_sum, theta_sum, pos_count}`
3. At configurable snapshot blocks, records `(indexA, thetaSum, posCount, accumulatedSum)`
4. Outputs `data/fixtures/fci_weth_usdc_v4.json` in the fixture schema

```python
#!/usr/bin/env python3
"""FCI Oracle: replays V4 pool events through exact Q128 integer math.

Usage:
    python fci_oracle.py --input data/raw/dune_export.json --output data/fixtures/fci_weth_usdc_v4.json
"""
import json
import math
import argparse
from dataclasses import dataclass, field

Q128 = 1 << 128
INDEX_ONE = (1 << 128) - 1


def isqrt(n: int) -> int:
    return math.isqrt(n)


def mul_div(a: int, b: int, c: int) -> int:
    if c == 0:
        return 0
    return (a * b) // c


def range_key(tick_lower: int, tick_upper: int) -> str:
    return f"{tick_lower}:{tick_upper}"


def position_key(sender: str, tick_lower: int, tick_upper: int, salt: str = "0x" + "00" * 32) -> str:
    """Mirrors keccak256(abi.encodePacked(sender, tickLower, tickUpper, salt))."""
    # For the oracle, we use a deterministic string key.
    # The forge test will compute the real keccak — values match because
    # we assert on FCI state aggregates, not per-position keys.
    return f"{sender}:{tick_lower}:{tick_upper}:{salt}"


@dataclass
class RangeState:
    positions: set = field(default_factory=set)
    swap_count: int = 0
    total_liquidity: int = 0
    tick_lower: int = 0
    tick_upper: int = 0


@dataclass
class PositionState:
    tick_lower: int = 0
    tick_upper: int = 0
    liquidity: int = 0
    add_block: int = 0
    baseline_swap_count: int = 0
    fee_growth_baseline0: int = 0


@dataclass
class FCIState:
    accumulated_sum: int = 0
    theta_sum: int = 0
    pos_count: int = 0

    def add_term(self, block_lifetime: int, x_squared_q128: int):
        lifetime = max(block_lifetime, 1)
        self.accumulated_sum += x_squared_q128 // lifetime
        self.theta_sum += Q128 // lifetime

    def increment_pos(self):
        self.pos_count += 1

    def decrement_pos(self):
        assert self.pos_count > 0
        self.pos_count -= 1

    def to_index_a(self) -> int:
        raw = self.accumulated_sum
        if raw >= Q128:
            return INDEX_ONE
        a = isqrt(raw << 128)
        return min(a, INDEX_ONE)


def fee_share_from_growth(pos_fee: int, range_fee: int) -> int:
    if range_fee == 0:
        return 0
    ratio = mul_div(pos_fee, Q128, range_fee)
    return min(ratio, INDEX_ONE)


def fee_share_from_delta(range_now: int, pos_last: int, baseline: int,
                         pos_liq: int, total_liq: int) -> int:
    if total_liq == 0:
        return 0
    # Wrapping subtraction (uint256 semantics)
    mask = (1 << 256) - 1
    pos_fee_delta = (range_now - pos_last) & mask
    range_fee_delta = (range_now - baseline) & mask
    fee_ratio = fee_share_from_growth(pos_fee_delta, range_fee_delta)
    ratio = mul_div(fee_ratio, pos_liq, total_liq)
    return min(ratio, INDEX_ONE)


def square_q128(x: int) -> int:
    return mul_div(x, x, Q128)


def replay_events(events: list, snapshot_blocks: list[int], pool_meta: dict) -> dict:
    fci = FCIState()
    positions: dict[str, PositionState] = {}
    ranges: dict[str, RangeState] = {}
    snapshots = []

    for evt in events:
        block = evt["blockNumber"]
        etype = evt["eventType"]

        if etype == "ModifyLiquidity":
            liq_delta = int(evt["liquidityDelta"])
            sender = evt["sender"]
            tl = evt["tickLower"]
            tu = evt["tickUpper"]
            pk = position_key(sender, tl, tu, evt.get("salt", "0x" + "00" * 32))
            rk = range_key(tl, tu)

            if liq_delta > 0:
                # afterAddLiquidity
                if rk not in ranges:
                    ranges[rk] = RangeState(tick_lower=tl, tick_upper=tu)
                r = ranges[rk]
                r.positions.add(pk)
                r.total_liquidity += liq_delta
                positions[pk] = PositionState(
                    tick_lower=tl, tick_upper=tu,
                    liquidity=liq_delta, add_block=block,
                    baseline_swap_count=r.swap_count,
                    fee_growth_baseline0=0  # V4 path reads from chain; oracle uses 0 placeholder
                )
                fci.increment_pos()

            elif liq_delta < 0:
                # afterRemoveLiquidity
                pos_liq = abs(liq_delta)
                pos = positions[pk]
                r = ranges[rk]

                swap_lifetime = r.swap_count - pos.baseline_swap_count
                block_lifetime = block - pos.add_block

                # x_k = posLiquidity / totalRangeLiquidity (simplified for oracle)
                xk = fee_share_from_growth(pos_liq, r.total_liquidity)

                if swap_lifetime > 0:
                    x_sq = square_q128(xk)
                    fci.add_term(block_lifetime, x_sq)

                fci.decrement_pos()

                r.positions.discard(pk)
                if len(r.positions) == 0:
                    r.swap_count = 0
                    r.total_liquidity = 0
                del positions[pk]

        elif etype == "Swap":
            tick = evt["swapTick"]
            # Increment overlapping ranges
            for rk, r in ranges.items():
                if len(r.positions) > 0:
                    # intersects: range [tl, tu) overlaps [tickMin, tickMax)
                    tick_min = tick
                    tick_max = tick + 1  # single-tick swap in fork context
                    if r.tick_lower < tick_max and r.tick_upper > tick_min:
                        r.swap_count += 1

        # Check for snapshot
        if block in snapshot_blocks:
            snapshots.append({
                "blockNumber": block,
                "expectedIndexA": str(fci.to_index_a()),
                "expectedThetaSum": str(fci.theta_sum),
                "expectedPosCount": str(fci.pos_count),
                "expectedAccumulatedSum": str(fci.accumulated_sum),
            })

    return {
        "pool": pool_meta,
        "forkBlock": events[0]["blockNumber"] - 1 if events else 0,
        "events": events,
        "snapshots": snapshots,
    }


def main():
    parser = argparse.ArgumentParser(description="FCI Oracle")
    parser.add_argument("--input", required=True, help="Raw Dune export JSON")
    parser.add_argument("--output", required=True, help="Output fixture JSON")
    parser.add_argument("--snapshots", type=str, default="",
                        help="Comma-separated snapshot block numbers")
    args = parser.parse_args()

    with open(args.input) as f:
        raw = json.load(f)

    events = raw["events"]
    pool_meta = raw["pool"]
    snap_blocks = [int(b) for b in args.snapshots.split(",") if b.strip()]

    # If no snapshots specified, use last event block
    if not snap_blocks and events:
        snap_blocks = [events[-1]["blockNumber"]]

    fixture = replay_events(events, snap_blocks, pool_meta)

    with open(args.output, "w") as f:
        json.dump(fixture, f, indent=2)

    print(f"Wrote {len(fixture['events'])} events, {len(fixture['snapshots'])} snapshots to {args.output}")


if __name__ == "__main__":
    main()
```

**Step 4: Commit**

```bash
git add -f data/scripts/fci_oracle.py data/scripts/requirements.txt
git commit -m "data(fci): Python oracle for Q128 FCI math — generates pre-baked JSON fixture"
```

---

## Task 3: Export Raw Events from Dune and Generate Fixture

**Files:**
- Create: `data/raw/dune_export.json` (intermediate, gitignored)
- Create: `data/fixtures/fci_weth_usdc_v4.json`

**Step 1: Run the event stream Dune query**

Use `mcp__dune__executeQueryById` with the query from Task 1. Save the results.

**Step 2: Format raw results into oracle input JSON**

Transform the Dune output into the oracle's expected input format:

```json
{
  "pool": {
    "token0": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "token1": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "fee": 500,
    "tickSpacing": 10,
    "hooks": "0x0000000000000000000000000000000000000000"
  },
  "events": [
    {
      "blockNumber": 21000010,
      "txHash": "0x...",
      "logIndex": 0,
      "eventType": "ModifyLiquidity",
      "sender": "0x...",
      "tickLower": -60,
      "tickUpper": 60,
      "liquidityDelta": "1000000000000000000",
      "salt": "0x0000000000000000000000000000000000000000000000000000000000000000"
    }
  ]
}
```

Save to `data/raw/dune_export.json`.

**Step 3: Pick snapshot blocks**

Choose 3-5 block numbers from within the event range. Good choices:
- After the first removal event
- Midway through the event stream
- At the last event

**Step 4: Run the oracle**

```bash
mkdir -p data/fixtures
python3 data/scripts/fci_oracle.py \
    --input data/raw/dune_export.json \
    --output data/fixtures/fci_weth_usdc_v4.json \
    --snapshots "BLOCK1,BLOCK2,BLOCK3"
```

**Step 5: Verify the fixture**

Open `data/fixtures/fci_weth_usdc_v4.json` and check:
- `forkBlock` is 1 less than the first event's block
- Events are ordered by `(blockNumber, logIndex)`
- Snapshots have non-zero `expectedIndexA` (at least after a removal with swaps)
- `expectedPosCount` matches the number of active positions at that block

**Step 6: Commit**

```bash
git add -f data/fixtures/fci_weth_usdc_v4.json
git commit -m "data(fci): pre-baked JSON fixture for WETH/USDC V4 fork test"
```

---

## Task 4: Write Fork Test — JSON Parsing Structs

**Files:**
- Create: `test/fee-concentration-index/fork/FeeConcentrationIndex.fork.t.sol`

**Step 1: Create the fork test directory**

```bash
mkdir -p test/fee-concentration-index/fork
```

**Step 2: Write the JSON parsing structs and test skeleton**

The test needs Solidity structs that match the JSON fixture schema so `vm.parseJson` can decode them.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {BeforeSwapDelta} from "v4-core/src/types/BeforeSwapDelta.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
import {StateLibrary} from "v4-core/src/libraries/StateLibrary.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

import {FeeConcentrationIndexHarness} from "../harness/FeeConcentrationIndexHarness.sol";
import {MockPositionManager} from "../harness/MockPositionManager.sol";
import {getCurrentTick, getFeeGrowthInside0} from
    "../../../src/fee-concentration-index/types/FeeGrowthReaderMod.sol";

// JSON fixture structs — field names must match JSON keys exactly for vm.parseJson
struct PoolMeta {
    address token0;
    address token1;
    uint24 fee;
    int24 tickSpacing;
    address hooks;
}

struct EventData {
    uint256 blockNumber;
    bytes32 txHash;
    uint256 logIndex;
    string eventType;
    address sender;
    int24 tickLower;
    int24 tickUpper;
    int256 liquidityDelta;
    int24 swapTick;
    bytes32 salt;
}

struct SnapshotData {
    uint256 blockNumber;
    uint128 expectedIndexA;
    uint256 expectedThetaSum;
    uint256 expectedPosCount;
    uint256 expectedAccumulatedSum;
}

contract FeeConcentrationIndexForkTest is Test {
    using PoolIdLibrary for PoolKey;

    FeeConcentrationIndexHarness harness;
    PoolKey poolKey;
    PoolId poolId;
    IPoolManager pm;

    EventData[] events;
    SnapshotData[] snapshots;
    uint256 forkBlock;

    function setUp() public {
        // Load fixture
        string memory json = vm.readFile("data/fixtures/fci_weth_usdc_v4.json");

        // Parse pool metadata
        bytes memory poolRaw = vm.parseJson(json, ".pool");
        PoolMeta memory pool = abi.decode(poolRaw, (PoolMeta));

        forkBlock = abi.decode(vm.parseJson(json, ".forkBlock"), (uint256));

        // Fork mainnet
        vm.createSelectFork("mainnet", forkBlock);

        // PoolManager is already deployed on mainnet
        pm = IPoolManager(0x000000000004444c5dc75cB358380D2e3dE08A90);
        MockPositionManager mockPosm = new MockPositionManager(pm);

        // Deploy harness at correct hook-flag address
        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
        );
        bytes memory constructorArgs = abi.encode(address(mockPosm));
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this), flags,
            type(FeeConcentrationIndexHarness).creationCode, constructorArgs
        );
        harness = new FeeConcentrationIndexHarness{salt: salt}(
            IPositionManager(address(mockPosm))
        );
        require(address(harness) == hookAddress, "hook address mismatch");

        // Build PoolKey from fixture metadata
        poolKey = PoolKey({
            currency0: Currency.wrap(pool.token0),
            currency1: Currency.wrap(pool.token1),
            fee: pool.fee,
            tickSpacing: pool.tickSpacing,
            hooks: IHooks(address(harness))
        });
        poolId = poolKey.toId();

        // Parse events array
        bytes memory eventsRaw = vm.parseJson(json, ".events");
        EventData[] memory evts = abi.decode(eventsRaw, (EventData[]));
        for (uint256 i; i < evts.length; i++) {
            events.push(evts[i]);
        }

        // Parse snapshots array
        bytes memory snapsRaw = vm.parseJson(json, ".snapshots");
        SnapshotData[] memory snaps = abi.decode(snapsRaw, (SnapshotData[]));
        for (uint256 i; i < snaps.length; i++) {
            snapshots.push(snaps[i]);
        }
    }

    function test_fork_wethUsdc_replayEvents_indexMatchesOracle() public {
        uint256 snapshotIdx = 0;

        for (uint256 i; i < events.length; i++) {
            EventData memory evt = events[i];
            vm.roll(evt.blockNumber);

            if (_isModifyLiquidity(evt) && evt.liquidityDelta > 0) {
                _replayAddLiquidity(evt);
            } else if (_isSwap(evt)) {
                _replaySwap(evt);
            } else if (_isModifyLiquidity(evt) && evt.liquidityDelta < 0) {
                _replayRemoveLiquidity(evt);
            }

            // Check snapshot assertions
            if (snapshotIdx < snapshots.length
                && evt.blockNumber >= snapshots[snapshotIdx].blockNumber)
            {
                _assertSnapshot(snapshots[snapshotIdx]);
                snapshotIdx++;
            }
        }

        // Assert all snapshots were checked
        assertEq(snapshotIdx, snapshots.length, "not all snapshots checked");
    }

    // ── Event type helpers ──

    function _isModifyLiquidity(EventData memory evt) internal pure returns (bool) {
        return keccak256(bytes(evt.eventType)) == keccak256("ModifyLiquidity");
    }

    function _isSwap(EventData memory evt) internal pure returns (bool) {
        return keccak256(bytes(evt.eventType)) == keccak256("Swap");
    }

    // ── Replay helpers ──

    function _replayAddLiquidity(EventData memory evt) internal {
        ModifyLiquidityParams memory params = ModifyLiquidityParams({
            tickLower: evt.tickLower,
            tickUpper: evt.tickUpper,
            liquidityDelta: evt.liquidityDelta,
            salt: evt.salt
        });

        harness.afterAddLiquidity(
            evt.sender,
            poolKey,
            params,
            BalanceDelta.wrap(0),
            BalanceDelta.wrap(0),
            ""  // V4 path: empty hookData
        );
    }

    function _replaySwap(EventData memory evt) internal {
        SwapParams memory params = SwapParams({
            zeroForOne: true,  // direction doesn't matter for FCI
            amountSpecified: -1,
            sqrtPriceLimitX96: 0
        });

        harness.beforeSwap(address(0), poolKey, params, "");
        harness.afterSwap(address(0), poolKey, params, BalanceDelta.wrap(0), "");
    }

    function _replayRemoveLiquidity(EventData memory evt) internal {
        ModifyLiquidityParams memory params = ModifyLiquidityParams({
            tickLower: evt.tickLower,
            tickUpper: evt.tickUpper,
            liquidityDelta: evt.liquidityDelta,
            salt: evt.salt
        });

        harness.beforeRemoveLiquidity(evt.sender, poolKey, params, "");
        harness.afterRemoveLiquidity(
            evt.sender,
            poolKey,
            params,
            BalanceDelta.wrap(0),
            BalanceDelta.wrap(0),
            ""  // V4 path: empty hookData
        );
    }

    // ── Assertion helpers ──

    function _assertSnapshot(SnapshotData memory snap) internal view {
        (uint128 indexA, uint256 thetaSum, uint256 posCount) =
            harness.getIndex(poolKey, false);

        uint256 n = posCount > 0 ? posCount : 1;
        uint256 tolerance = 1 + n * FixedPointMathLib.sqrt(n);

        assertApproxEqAbs(
            uint256(indexA),
            uint256(snap.expectedIndexA),
            tolerance,
            "indexA mismatch at snapshot"
        );
        assertEq(posCount, snap.expectedPosCount, "posCount mismatch at snapshot");
    }
}
```

**Step 3: Verify it compiles** (will fail if fixture doesn't exist yet, but struct/import errors will show)

```bash
FOUNDRY_OUT=out2 forge build 2>&1 | grep -E "Error|error" | head -20
```

**Step 4: Commit**

```bash
git add test/fee-concentration-index/fork/FeeConcentrationIndex.fork.t.sol
git commit -m "test(fci): fork test skeleton — JSON parsing structs, replay loop, snapshot assertions"
```

---

## Task 5: Run End-to-End and Iterate

**Step 1: Run the fork test**

```bash
FOUNDRY_OUT=out2 forge test \
    --match-path "test/fee-concentration-index/fork/*" \
    -vvv \
    --fork-url $ETH_RPC_URL 2>&1 | tail -40
```

**Step 2: Debug any failures**

Common issues:
- **JSON field name mismatch**: Solidity struct field names must match JSON keys exactly (case-sensitive). Forge's `vm.parseJson` is strict.
- **Type mismatch**: Large numbers in JSON must be strings, decoded as `uint256`. Ensure the Python oracle outputs string representations for all large integers.
- **PoolManager state**: If `getCurrentTick` or `getFeeGrowthInside0` reverts, the pool may not exist at the fork block. Adjust `forkBlock`.
- **HookMiner timeout**: If `HookMiner.find` takes too long, increase gas limit or use a pre-computed salt.
- **Tolerance**: If `indexA` is off by more than tolerance, check the Python oracle's integer arithmetic matches Solidity exactly (especially `isqrt` and integer division).

**Step 3: Verify all assertions pass**

Expected output:
```
[PASS] test_fork_wethUsdc_replayEvents_indexMatchesOracle()
```

**Step 4: Run existing tests to confirm no regressions**

```bash
FOUNDRY_OUT=out2 forge test --match-path "test/fee-concentration-index/unit/*" -v
FOUNDRY_OUT=out2 forge test --match-path "test/fee-concentration-index/fuzz/*" -v
```

All 37 existing tests should still pass.

**Step 5: Final commit**

```bash
git add -A
git commit -m "test(fci): fork test passing — WETH/USDC V4 replay validates FCI against Python oracle"
```

---

## Task 6: Push and Update Tasks

**Step 1: Push**

```bash
git push origin 001-fee-concentration-index
```

**Step 2: Update specs/001-fee-concentration-index/tasks.md**

Mark the fork test task as complete in the task tracker.
