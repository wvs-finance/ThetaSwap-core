# Reactive Integration Fork Test Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Validate SomniaAdapter's FeeConcentrationIndex accuracy against real Uniswap V3 WETH/USDC mainnet data, replayed on a Somnia L1 fork.

**Architecture:** Dune SQL query exports ~50 V3 lifecycle events (Swap, Mint, Burn, Collect). Python oracle replays them through exact Q128 math, accumulates Collect fees per position, and bakes expected FCI values + pre-accumulated fee0/fee1 into a JSON fixture. Forge fork test deploys SomniaAdapter on a Somnia fork, replays fixture events via direct calls, and asserts index values match the oracle at snapshot blocks.

**Tech Stack:** Dune Analytics (SQL, V3 tables), Python 3 (integer math), Forge (Somnia fork testing, vm.readFile/vm.parseJson), Solidity ^0.8.26

**Branch:** `003-reactive-integration`

**Design doc:** `docs/plans/2026-03-07-reactive-integration-fork-test-design.md`

---

## Task 0: Branch setup — ensure dependencies exist

**Files:**
- Check: `foundry.toml` (remappings for reactive-lib, v3-core)
- Check: `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol` (parameterized wrappers)
- Check: `src/reactive-integration/types/ReactiveCallbackDataMod.sol` (V3 typed structs)
- Modify: `foundry.toml` (add Somnia RPC endpoint)

**Step 1: Switch to 003-reactive-integration branch**

```bash
git checkout 003-reactive-integration
```

**Step 2: Verify parameterized FCI wrappers exist**

Check that `FeeConcentrationIndexStorageMod.sol` contains the parameterized versions (accepting `FeeConcentrationIndexStorage storage $` as first arg). If not, cherry-pick from `001-fee-concentration-index` or `001-fci-coprimary-diamond`.

Required functions (parameterized + no-arg overloads):
- `registerPosition`
- `setFeeGrowthBaseline` / `getFeeGrowthBaseline` / `deleteFeeGrowthBaseline`
- `deregisterPosition`
- `incrementOverlappingRanges`
- `incrementPosCount` / `decrementPosCount`
- `addStateTerm`

**Step 3: Verify reactive-integration types exist**

Check that these files exist:
- `src/reactive-integration/types/ReactiveCallbackDataMod.sol` (V3SwapData, V3MintData, V3BurnData, V3CollectData)
- `src/reactive-integration/types/SyntheticFeeGrowthMod.sol`
- `src/reactive-integration/types/CollectedFeesMod.sol` (v3PositionKey)
- `src/reactive-integration/libraries/PoolKeyExtMod.sol` (fromV3Pool)

If missing, cherry-pick from `001-fci-coprimary-diamond`.

**Step 4: Add Somnia RPC endpoint to foundry.toml**

Add under `[rpc_endpoints]`:

```toml
somnia = "${SOMNIA_RPC_URL}"
```

**Step 5: Verify build**

Run: `forge build --out out2`
Expected: compiles

**Step 6: Commit**

```bash
git add foundry.toml
git commit -m "chore(003): add Somnia RPC endpoint, verify reactive integration deps"
```

---

## Task 1: Dune V3 query — discover pool and export events

**Files:**
- Create: `data/queries/fci_weth_usdc_v3.sql`

**Step 1: Create the query file**

```bash
mkdir -p data/queries
```

**Step 2: Write the pool discovery query**

Write `data/queries/fci_weth_usdc_v3.sql`:

```sql
-- FCI Reactive Integration Fork Test: WETH/USDC V3 Event Stream
-- Pool: WETH/USDC 0.30% on Uniswap V3 Ethereum mainnet
-- Known address: 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8
-- WETH: 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
-- USDC: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48

-- Section 1: Pool verification
SELECT
    contract_address,
    fee,
    tickSpacing
FROM uniswap_v3_ethereum.UniswapV3Factory_evt_PoolCreated
WHERE token0 = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
  AND token1 = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
  AND fee = 3000
LIMIT 1;
```

**Step 3: Run pool verification via Dune MCP**

Use `mcp__dune__createDuneQuery` + `mcp__dune__executeQueryById`. Confirm pool address and tickSpacing (expected: 60).

**Step 4: Write the dense block range discovery query**

Append to the SQL file:

```sql
-- Section 2: Find a dense block range with lifecycle events
-- Look for blocks with both Mint and Burn activity (~50 events total)
SELECT
    (evt_block_number / 1000) * 1000 as bucket,
    COUNT(*) as mint_count
FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Mint
WHERE contract_address = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8
  AND evt_block_number > 20000000
GROUP BY 1
ORDER BY mint_count DESC
LIMIT 20;
```

Run via Dune MCP. Pick a dense bucket (needs Mints + Burns + Swaps + Collects).

**Step 5: Write the full event stream query**

Append to the SQL file. Replace `<BLOCK_START>` and `<BLOCK_END>` with the chosen range:

```sql
-- Section 3: Full event stream — all 4 V3 event types
-- Replace <BLOCK_START> and <BLOCK_END> with the dense range from Section 2

WITH swap_events AS (
    SELECT
        evt_block_number as block_number,
        evt_tx_hash as tx_hash,
        CAST(evt_index AS BIGINT) as log_index,
        'Swap' as event_type,
        CAST(NULL AS VARCHAR) as owner,
        CAST(NULL AS INTEGER) as tick_lower,
        CAST(NULL AS INTEGER) as tick_upper,
        CAST(NULL AS BIGINT) as liquidity,
        CAST(NULL AS BIGINT) as fee_amount0,
        CAST(NULL AS BIGINT) as fee_amount1,
        tick as swap_tick
    FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Swap
    WHERE contract_address = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8
      AND evt_block_number BETWEEN <BLOCK_START> AND <BLOCK_END>
),
mint_events AS (
    SELECT
        evt_block_number as block_number,
        evt_tx_hash as tx_hash,
        CAST(evt_index AS BIGINT) as log_index,
        'Mint' as event_type,
        CAST(owner AS VARCHAR) as owner,
        tickLower as tick_lower,
        tickUpper as tick_upper,
        CAST(amount AS BIGINT) as liquidity,
        CAST(NULL AS BIGINT) as fee_amount0,
        CAST(NULL AS BIGINT) as fee_amount1,
        CAST(NULL AS INTEGER) as swap_tick
    FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Mint
    WHERE contract_address = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8
      AND evt_block_number BETWEEN <BLOCK_START> AND <BLOCK_END>
),
burn_events AS (
    SELECT
        evt_block_number as block_number,
        evt_tx_hash as tx_hash,
        CAST(evt_index AS BIGINT) as log_index,
        'Burn' as event_type,
        CAST(owner AS VARCHAR) as owner,
        tickLower as tick_lower,
        tickUpper as tick_upper,
        CAST(amount AS BIGINT) as liquidity,
        CAST(NULL AS BIGINT) as fee_amount0,
        CAST(NULL AS BIGINT) as fee_amount1,
        CAST(NULL AS INTEGER) as swap_tick
    FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Burn
    WHERE contract_address = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8
      AND evt_block_number BETWEEN <BLOCK_START> AND <BLOCK_END>
),
collect_events AS (
    SELECT
        evt_block_number as block_number,
        evt_tx_hash as tx_hash,
        CAST(evt_index AS BIGINT) as log_index,
        'Collect' as event_type,
        CAST(owner AS VARCHAR) as owner,
        tickLower as tick_lower,
        tickUpper as tick_upper,
        CAST(NULL AS BIGINT) as liquidity,
        CAST(amount0 AS BIGINT) as fee_amount0,
        CAST(amount1 AS BIGINT) as fee_amount1,
        CAST(NULL AS INTEGER) as swap_tick
    FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Collect
    WHERE contract_address = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8
      AND evt_block_number BETWEEN <BLOCK_START> AND <BLOCK_END>
),
-- Sample swaps: 1 per 200-block bucket to keep ~50 total events
swap_ranked AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY (block_number / 200)
        ORDER BY block_number ASC, log_index ASC
    ) as rn
    FROM swap_events
),
swap_sampled AS (
    SELECT block_number, tx_hash, log_index, event_type, owner,
           tick_lower, tick_upper, liquidity, fee_amount0, fee_amount1, swap_tick
    FROM swap_ranked WHERE rn = 1
),
all_events AS (
    SELECT * FROM mint_events
    UNION ALL
    SELECT * FROM burn_events
    UNION ALL
    SELECT * FROM collect_events
    UNION ALL
    SELECT * FROM swap_sampled
)
SELECT *
FROM all_events
ORDER BY block_number ASC, log_index ASC;
```

**Step 6: Run the event stream query via Dune MCP**

Execute via Dune MCP. Save raw results as `data/raw/dune_v3_export.json` for the Python oracle.

**Step 7: Commit**

```bash
git add -f data/queries/fci_weth_usdc_v3.sql
git commit -m "data(003): Dune SQL queries for WETH/USDC V3 event export"
```

---

## Task 2: Python V3 oracle — replay events and generate fixture

**Files:**
- Create: `data/scripts/fci_v3_oracle.py`

**Step 1: Write the V3 oracle script**

The oracle replicates exact Solidity math with V3-specific Collect accumulation:

```python
#!/usr/bin/env python3
"""FCI V3 Oracle: replays V3 pool events through exact Q128 integer math.

Handles Collect accumulation: Collect fees are tracked per position and
baked into the subsequent Burn event's fee0/fee1 fields in the output fixture.

Usage:
    python fci_v3_oracle.py \
        --input data/raw/dune_v3_export.json \
        --output data/fixtures/fci_weth_usdc_v3.json \
        --snapshots 21000050,21000100,21000150
"""
import json
import math
import argparse
from dataclasses import dataclass, field
from typing import Optional


Q128 = 1 << 128
INDEX_ONE = (1 << 128) - 1


def isqrt(n: int) -> int:
    return math.isqrt(n)


def mul_div(a: int, b: int, c: int) -> int:
    if c == 0:
        return 0
    return (a * b) // c


def floor_one(x: int) -> int:
    return max(x, 1)


@dataclass
class Range:
    tick_lower: int
    tick_upper: int
    positions: set = field(default_factory=set)
    swap_count: int = 0
    total_liquidity: int = 0


@dataclass
class Position:
    owner: str
    tick_lower: int
    tick_upper: int
    liquidity: int
    add_block: int
    range_key: str


@dataclass
class CollectedFees:
    fee0: int = 0
    fee1: int = 0


@dataclass
class FCIState:
    accumulated_sum: int = 0
    theta_sum: int = 0
    pos_count: int = 0

    def add_term(self, block_lifetime: int, x_squared_q128: int) -> None:
        lifetime = floor_one(block_lifetime)
        self.accumulated_sum += x_squared_q128 // lifetime
        self.theta_sum += Q128 // lifetime

    def increment_pos(self) -> None:
        self.pos_count += 1

    def decrement_pos(self) -> None:
        assert self.pos_count > 0
        self.pos_count -= 1

    def to_index_a(self) -> int:
        raw = self.accumulated_sum
        if raw >= Q128:
            return INDEX_ONE
        a = isqrt(raw << 128)
        return min(a, INDEX_ONE)


def range_key(tick_lower: int, tick_upper: int) -> str:
    # Matches Solidity: keccak256(abi.encode(tickLower, tickUpper))
    # For oracle purposes, a string key suffices (not computing actual keccak)
    return f"{tick_lower},{tick_upper}"


def position_key(owner: str, tick_lower: int, tick_upper: int) -> str:
    # Matches Solidity: keccak256(abi.encodePacked(owner, tickLower, tickUpper))
    return f"{owner},{tick_lower},{tick_upper}"


def intersects(la: int, ua: int, lb: int, ub: int) -> bool:
    return la < ub and lb < ua


class V3FCIOracle:
    def __init__(self):
        self.state = FCIState()
        self.positions: dict[str, Position] = {}
        self.ranges: dict[str, Range] = {}
        self.collected_fees: dict[str, CollectedFees] = {}
        self.current_block: int = 0

    def on_swap(self, block: int, tick: int) -> None:
        self.current_block = block
        for rk, r in self.ranges.items():
            if r.positions and intersects(r.tick_lower, r.tick_upper, tick, tick + 1):
                r.swap_count += 1

    def on_mint(self, block: int, owner: str, tick_lower: int, tick_upper: int, liquidity: int) -> None:
        self.current_block = block
        pos_key = position_key(owner, tick_lower, tick_upper)
        rk = range_key(tick_lower, tick_upper)

        if rk not in self.ranges:
            self.ranges[rk] = Range(tick_lower=tick_lower, tick_upper=tick_upper)

        r = self.ranges[rk]
        r.positions.add(pos_key)
        r.total_liquidity += liquidity

        self.positions[pos_key] = Position(
            owner=owner,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            liquidity=liquidity,
            add_block=block,
            range_key=rk,
        )
        self.state.increment_pos()

    def on_collect(self, owner: str, tick_lower: int, tick_upper: int,
                   fee_amount0: int, fee_amount1: int) -> None:
        pos_key = position_key(owner, tick_lower, tick_upper)
        if pos_key not in self.collected_fees:
            self.collected_fees[pos_key] = CollectedFees()
        self.collected_fees[pos_key].fee0 += fee_amount0
        self.collected_fees[pos_key].fee1 += fee_amount1

    def on_burn(self, block: int, owner: str, tick_lower: int, tick_upper: int,
                liquidity: int) -> tuple[int, int]:
        """Returns (accumulated_fee0, accumulated_fee1) consumed from Collect events."""
        self.current_block = block
        pos_key = position_key(owner, tick_lower, tick_upper)
        rk = range_key(tick_lower, tick_upper)

        pos = self.positions.get(pos_key)
        if pos is None:
            return (0, 0)

        r = self.ranges[rk]
        block_lifetime = block - pos.add_block
        swap_lifetime = r.swap_count

        # Deregister
        r.positions.discard(pos_key)
        total_range_liq = r.total_liquidity
        r.total_liquidity -= liquidity

        # Consume accumulated Collect fees
        fees = self.collected_fees.pop(pos_key, CollectedFees())

        if swap_lifetime > 0 and total_range_liq > 0 and pos.liquidity > 0:
            # SyntheticFeeGrowth
            pos_delta = mul_div(fees.fee0, Q128, pos.liquidity) if pos.liquidity > 0 else 0
            range_delta = mul_div(fees.fee0, Q128, total_range_liq) if total_range_liq > 0 else 0

            # FeeShareRatio
            if range_delta > 0:
                ratio = mul_div(pos_delta, Q128, range_delta)
                ratio = min(ratio, INDEX_ONE)
            else:
                ratio = 0

            # square
            x_squared = (ratio * ratio) // Q128

            self.state.add_term(block_lifetime, x_squared)

        self.state.decrement_pos()
        del self.positions[pos_key]

        return (fees.fee0, fees.fee1)

    def snapshot(self) -> dict:
        return {
            "indexA": str(self.state.to_index_a()),
            "thetaSum": str(self.state.theta_sum),
            "posCount": str(self.state.pos_count),
            "accumulatedSum": str(self.state.accumulated_sum),
        }


def main():
    parser = argparse.ArgumentParser(description="FCI V3 Oracle")
    parser.add_argument("--input", required=True, help="Raw Dune export JSON")
    parser.add_argument("--output", required=True, help="Output fixture JSON")
    parser.add_argument("--snapshots", required=True, help="Comma-separated snapshot block numbers")
    parser.add_argument("--pool-address", default="0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8")
    parser.add_argument("--token0", default="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    parser.add_argument("--token1", default="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    parser.add_argument("--fee", type=int, default=3000)
    parser.add_argument("--tick-spacing", type=int, default=60)
    parser.add_argument("--somnia-fork-block", type=int, required=True)
    args = parser.parse_args()

    snapshot_blocks = set(int(b) for b in args.snapshots.split(","))

    with open(args.input) as f:
        raw_events = json.load(f)

    oracle = V3FCIOracle()
    fixture_events = []
    snapshots = []

    for evt in raw_events:
        block = int(evt["block_number"])
        event_type = evt["event_type"]

        if event_type == "Swap":
            oracle.on_swap(block, int(evt["swap_tick"]))
            fixture_events.append({
                "blockNumber": block,
                "eventType": "Swap",
                "tick": int(evt["swap_tick"]),
            })

        elif event_type == "Mint":
            oracle.on_mint(
                block,
                evt["owner"],
                int(evt["tick_lower"]),
                int(evt["tick_upper"]),
                int(evt["liquidity"]),
            )
            fixture_events.append({
                "blockNumber": block,
                "eventType": "Mint",
                "owner": evt["owner"],
                "tickLower": int(evt["tick_lower"]),
                "tickUpper": int(evt["tick_upper"]),
                "liquidity": str(int(evt["liquidity"])),
            })

        elif event_type == "Collect":
            oracle.on_collect(
                evt["owner"],
                int(evt["tick_lower"]),
                int(evt["tick_upper"]),
                int(evt["fee_amount0"]),
                int(evt["fee_amount1"]),
            )
            # Collect events are NOT added to fixture — fees baked into Burn

        elif event_type == "Burn":
            fee0, fee1 = oracle.on_burn(
                block,
                evt["owner"],
                int(evt["tick_lower"]),
                int(evt["tick_upper"]),
                int(evt["liquidity"]),
            )
            fixture_events.append({
                "blockNumber": block,
                "eventType": "Burn",
                "owner": evt["owner"],
                "tickLower": int(evt["tick_lower"]),
                "tickUpper": int(evt["tick_upper"]),
                "liquidity": str(int(evt["liquidity"])),
                "fee0": str(fee0),
                "fee1": str(fee1),
            })

        # Check for snapshot
        if block in snapshot_blocks:
            snapshot_blocks.discard(block)
            snap = oracle.snapshot()
            snap["blockNumber"] = block
            snapshots.append(snap)

    # Any remaining snapshot blocks (if events didn't land exactly on them)
    for sb in sorted(snapshot_blocks):
        snap = oracle.snapshot()
        snap["blockNumber"] = sb
        snapshots.append(snap)

    fixture = {
        "pool": {
            "address": args.pool_address,
            "token0": args.token0,
            "token1": args.token1,
            "fee": args.fee,
            "tickSpacing": args.tick_spacing,
        },
        "somniaForkBlock": args.somnia_fork_block,
        "events": fixture_events,
        "snapshots": sorted(snapshots, key=lambda s: s["blockNumber"]),
    }

    with open(args.output, "w") as f:
        json.dump(fixture, f, indent=2)

    print(f"Generated fixture with {len(fixture_events)} events and {len(snapshots)} snapshots")
    print(f"Final state: {oracle.snapshot()}")


if __name__ == "__main__":
    main()
```

**Step 2: Run the oracle against Dune export**

```bash
python data/scripts/fci_v3_oracle.py \
    --input data/raw/dune_v3_export.json \
    --output data/fixtures/fci_weth_usdc_v3.json \
    --snapshots <SNAPSHOT_BLOCKS> \
    --somnia-fork-block <RECENT_SOMNIA_BLOCK>
```

Expected: generates `data/fixtures/fci_weth_usdc_v3.json` with events and snapshots.

**Step 3: Inspect the fixture**

Verify:
- Events are ordered by blockNumber
- Burn events include fee0/fee1 > 0 (at least some)
- Snapshots have non-zero indexA (at least after some removals)
- No Collect events in the output

**Step 4: Commit**

```bash
git add -f data/scripts/fci_v3_oracle.py data/fixtures/fci_weth_usdc_v3.json
git commit -m "data(003): V3 FCI oracle + WETH/USDC fixture with Collect accumulation"
```

---

## Task 3: SomniaAdapterStorageMod.sol

**Files:**
- Create: `src/reactive-integration/adapters/somnia/SomniaAdapterStorageMod.sol`

**Step 1: Write the storage accessor**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FeeConcentrationIndexStorage} from "../../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";

bytes32 constant SOMNIA_FCI_STORAGE_SLOT = keccak256("SomniaAdapter.fci.storage");

function somniaFciStorage() pure returns (FeeConcentrationIndexStorage storage s) {
    bytes32 slot = SOMNIA_FCI_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}
```

**Step 2: Verify build**

Run: `forge build --out out2`
Expected: compiles

**Step 3: Commit**

```bash
git add src/reactive-integration/adapters/somnia/SomniaAdapterStorageMod.sol
git commit -m "feat(003): add SomniaAdapterStorageMod — diamond storage for Somnia FCI"
```

---

## Task 4: SomniaAdapter.sol

**Files:**
- Create: `src/reactive-integration/adapters/somnia/SomniaAdapter.sol`

**Step 1: Write the contract**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";

import {V3SwapData, V3MintData, V3BurnData} from "../../types/ReactiveCallbackDataMod.sol";
import {somniaFciStorage} from "./SomniaAdapterStorageMod.sol";
import {
    FeeConcentrationIndexStorage,
    registerPosition, setFeeGrowthBaseline, deleteFeeGrowthBaseline,
    incrementOverlappingRanges, deregisterPosition,
    incrementPosCount, decrementPosCount, addStateTerm
} from "../../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {TickRange, fromTicks} from "../../../fee-concentration-index/types/TickRangeMod.sol";
import {FeeShareRatio} from "../../../fee-concentration-index/types/FeeShareRatioMod.sol";
import {SwapCount} from "../../../fee-concentration-index/types/SwapCountMod.sol";
import {BlockCount} from "../../../fee-concentration-index/types/BlockCountMod.sol";
import {SyntheticFeeGrowth, fromBurnAmount, toFeeShareRatio} from "../../types/SyntheticFeeGrowthMod.sol";
import {v3PositionKey} from "../../types/CollectedFeesMod.sol";

// SomniaAdapter: FCI computation for V3 pools on Somnia L1.
// Generic event-intake interface — Somnia binding added later.
// SCOP compliant: no is, no library, no modifier.
contract SomniaAdapter {
    function onV3Swap(V3SwapData calldata data) external {
        FeeConcentrationIndexStorage storage $ = somniaFciStorage();
        PoolId poolId = _poolId(data.pool);
        incrementOverlappingRanges($, poolId, data.tick, data.tick);
    }

    function onV3Mint(V3MintData calldata data) external {
        FeeConcentrationIndexStorage storage $ = somniaFciStorage();
        PoolId poolId = _poolId(data.pool);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);
        TickRange rk = fromTicks(data.tickLower, data.tickUpper);
        registerPosition($, poolId, rk, posKey, data.tickLower, data.tickUpper, data.liquidity);
        setFeeGrowthBaseline($, poolId, posKey, 0);
        incrementPosCount($, poolId);
    }

    function onV3Burn(V3BurnData calldata data, uint256 fee0, uint256 fee1) external {
        FeeConcentrationIndexStorage storage $ = somniaFciStorage();
        PoolId poolId = _poolId(data.pool);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);

        (, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) =
            deregisterPosition($, poolId, posKey, data.liquidity);

        if (!swapLifetime.isZero()) {
            SyntheticFeeGrowth posDelta = fromBurnAmount(fee0, data.liquidity);
            SyntheticFeeGrowth rangeDelta = fromBurnAmount(fee0, totalRangeLiq);
            FeeShareRatio xk = toFeeShareRatio(posDelta, rangeDelta);
            uint256 xSquaredQ128 = xk.square();
            addStateTerm($, poolId, blockLifetime, xSquaredQ128);
        }

        decrementPosCount($, poolId);
        deleteFeeGrowthBaseline($, poolId, posKey);
    }

    function getIndex(PoolId poolId) external view returns (
        uint128 indexA, uint256 thetaSum, uint256 posCount
    ) {
        FeeConcentrationIndexStorage storage $ = somniaFciStorage();
        indexA = $.fciState[poolId].toIndexA();
        thetaSum = $.fciState[poolId].thetaSum;
        posCount = $.fciState[poolId].posCount;
    }

    // Compute PoolId from pool address — uses a fixed synthetic PoolKey.
    // The test constructs the same PoolKey from fixture data.
    function _poolId(address pool) internal pure returns (PoolId) {
        // For testing: PoolId is just keccak256 of pool address.
        // In production, this would use fromV3Pool() with real token data.
        return PoolId.wrap(keccak256(abi.encodePacked(pool)));
    }

    receive() external payable {}
}
```

**Note:** `_poolId` uses a simplified hash for testing. The fork test must use the same PoolId derivation. This avoids needing `fromV3Pool()` which requires the V3 pool contract to be callable (it won't be on Somnia fork). If the test needs to use `fromV3Pool()`, deploy a mock V3 pool — but the simplified approach is cleaner.

**Step 2: Verify build**

Run: `forge build --out out2`
Expected: compiles

**Step 3: Commit**

```bash
git add src/reactive-integration/adapters/somnia/SomniaAdapter.sol
git commit -m "feat(003): add SomniaAdapter — FCI for V3 pools on Somnia, generic event intake"
```

---

## Task 5: Fork test — write and run

**Files:**
- Create: `test/fee-concentration-index/integration/fork/SomniaAdapter.integration.fork.t.sol`

**Step 1: Write the fork test**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Test.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {SomniaAdapter} from
    "../../../../src/reactive-integration/adapters/somnia/SomniaAdapter.sol";
import {V3SwapData, V3MintData, V3BurnData} from
    "../../../../src/reactive-integration/types/ReactiveCallbackDataMod.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";

contract SomniaAdapterIntegrationForkTest is Test {
    using stdJson for string;

    SomniaAdapter adapter;
    string fixture;
    PoolId poolId;

    // Mock pool address — must match fixture
    address constant MOCK_POOL = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8;

    function setUp() public {
        // Fork Somnia
        uint256 somniaFork = vm.createFork("somnia");
        vm.selectFork(somniaFork);

        // Deploy adapter
        adapter = new SomniaAdapter();

        // Load fixture
        fixture = vm.readFile("data/fixtures/fci_weth_usdc_v3.json");

        // Derive poolId — must match adapter's _poolId()
        poolId = PoolId.wrap(keccak256(abi.encodePacked(MOCK_POOL)));
    }

    function test_integration_fork_somniaAdapter_replayV3Events_indexMatchesOracle() public {
        // Parse events array
        bytes memory eventsRaw = fixture.parseRaw(".events");
        uint256 eventCount = abi.decode(
            fixture.parseRaw(string.concat(".events.", vm.toString(uint256(0)), ".blockNumber")),
            (uint256)
        );

        // Parse snapshot expectations
        bytes memory snapshotsRaw = fixture.parseRaw(".snapshots");

        // Build snapshot lookup
        uint256 snapshotCount = _countSnapshots();
        uint256[] memory snapshotBlocks = new uint256[](snapshotCount);
        uint256[] memory expectedIndexA = new uint256[](snapshotCount);
        uint256[] memory expectedThetaSum = new uint256[](snapshotCount);
        uint256[] memory expectedPosCount = new uint256[](snapshotCount);

        for (uint256 s; s < snapshotCount; ++s) {
            string memory prefix = string.concat(".snapshots[", vm.toString(s), "]");
            snapshotBlocks[s] = abi.decode(fixture.parseRaw(string.concat(prefix, ".blockNumber")), (uint256));
            expectedIndexA[s] = abi.decode(fixture.parseRaw(string.concat(prefix, ".expectedIndexA")), (uint256));
            expectedThetaSum[s] = abi.decode(fixture.parseRaw(string.concat(prefix, ".expectedThetaSum")), (uint256));
            expectedPosCount[s] = abi.decode(fixture.parseRaw(string.concat(prefix, ".expectedPosCount")), (uint256));
        }

        // Replay events
        uint256 numEvents = _countEvents();
        for (uint256 i; i < numEvents; ++i) {
            string memory prefix = string.concat(".events[", vm.toString(i), "]");
            uint256 blockNum = abi.decode(fixture.parseRaw(string.concat(prefix, ".blockNumber")), (uint256));
            string memory eventType = abi.decode(fixture.parseRaw(string.concat(prefix, ".eventType")), (string));

            if (_strEq(eventType, "Swap")) {
                int24 tick = int24(abi.decode(fixture.parseRaw(string.concat(prefix, ".tick")), (int256)));
                adapter.onV3Swap(V3SwapData({
                    pool: IUniswapV3Pool(MOCK_POOL),
                    tick: tick
                }));
            } else if (_strEq(eventType, "Mint")) {
                address owner = abi.decode(fixture.parseRaw(string.concat(prefix, ".owner")), (address));
                int24 tickLower = int24(abi.decode(fixture.parseRaw(string.concat(prefix, ".tickLower")), (int256)));
                int24 tickUpper = int24(abi.decode(fixture.parseRaw(string.concat(prefix, ".tickUpper")), (int256)));
                uint128 liquidity = uint128(abi.decode(fixture.parseRaw(string.concat(prefix, ".liquidity")), (uint256)));
                adapter.onV3Mint(V3MintData({
                    pool: IUniswapV3Pool(MOCK_POOL),
                    owner: owner,
                    tickLower: tickLower,
                    tickUpper: tickUpper,
                    liquidity: liquidity
                }));
            } else if (_strEq(eventType, "Burn")) {
                address owner = abi.decode(fixture.parseRaw(string.concat(prefix, ".owner")), (address));
                int24 tickLower = int24(abi.decode(fixture.parseRaw(string.concat(prefix, ".tickLower")), (int256)));
                int24 tickUpper = int24(abi.decode(fixture.parseRaw(string.concat(prefix, ".tickUpper")), (int256)));
                uint128 liquidity = uint128(abi.decode(fixture.parseRaw(string.concat(prefix, ".liquidity")), (uint256)));
                uint256 fee0 = abi.decode(fixture.parseRaw(string.concat(prefix, ".fee0")), (uint256));
                uint256 fee1 = abi.decode(fixture.parseRaw(string.concat(prefix, ".fee1")), (uint256));
                adapter.onV3Burn(
                    V3BurnData({
                        pool: IUniswapV3Pool(MOCK_POOL),
                        owner: owner,
                        tickLower: tickLower,
                        tickUpper: tickUpper,
                        liquidity: liquidity
                    }),
                    fee0,
                    fee1
                );
            }

            // Check snapshots
            for (uint256 s; s < snapshotCount; ++s) {
                if (blockNum == snapshotBlocks[s]) {
                    (uint128 indexA, uint256 thetaSum, uint256 posCount) = adapter.getIndex(poolId);
                    assertApproxEqAbs(
                        uint256(indexA),
                        expectedIndexA[s],
                        _indexATolerance(expectedPosCount[s]),
                        string.concat("indexA mismatch at snapshot block ", vm.toString(blockNum))
                    );
                    assertEq(thetaSum, expectedThetaSum[s],
                        string.concat("thetaSum mismatch at snapshot block ", vm.toString(blockNum)));
                    assertEq(posCount, expectedPosCount[s],
                        string.concat("posCount mismatch at snapshot block ", vm.toString(blockNum)));
                }
            }
        }
    }

    // ── Helpers ──

    function _countEvents() internal view returns (uint256) {
        // Try parsing increasing indices until it reverts
        for (uint256 i; i < 1000; ++i) {
            try vm.parseJsonUint(fixture, string.concat(".events[", vm.toString(i), "].blockNumber")) returns (uint256) {
                continue;
            } catch {
                return i;
            }
        }
        return 0;
    }

    function _countSnapshots() internal view returns (uint256) {
        for (uint256 i; i < 100; ++i) {
            try vm.parseJsonUint(fixture, string.concat(".snapshots[", vm.toString(i), "].blockNumber")) returns (uint256) {
                continue;
            } catch {
                return i;
            }
        }
        return 0;
    }

    function _strEq(string memory a, string memory b) internal pure returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    function _indexATolerance(uint256 posCount) internal pure returns (uint256) {
        // Tolerance scales with position count — same heuristic as fuzz tests.
        // 0.1% of Q128 per active position, minimum 1.
        uint256 q128 = 1 << 128;
        if (posCount == 0) return 1;
        return (q128 / 1000) * posCount;
    }
}
```

**Step 2: Run the test**

Run: `forge test --match-path "test/fee-concentration-index/integration/fork/*" --out out2 -v --fork-url $SOMNIA_RPC_URL`
Expected: PASS (if fixture is correctly generated)

If `SOMNIA_RPC_URL` is not set, test will fail with fork creation error — this is expected in CI without credentials.

**Step 3: Debug if needed**

If assertions fail:
1. Check Python oracle math vs Solidity math — run a small manual example through both
2. Check PoolId derivation matches between test and adapter
3. Check event ordering in fixture matches Dune query ORDER BY
4. Check that `_poolId` in `SomniaAdapter` matches `keccak256(abi.encodePacked(MOCK_POOL))` in the test

**Step 4: Commit**

```bash
git add test/fee-concentration-index/integration/fork/SomniaAdapter.integration.fork.t.sol
git commit -m "test(003): SomniaAdapter integration fork test — replay V3 events, assert FCI matches oracle"
```

---

## Task 6: Full verification and cleanup

**Step 1: Full build**

Run: `forge build --out out2`
Expected: zero errors

**Step 2: Run all existing tests (regression)**

Run: `forge test --out out2 -v --no-match-path "test/fee-concentration-index/integration/*"`
Expected: all existing tests pass (39 FCI + others)

**Step 3: Run integration test**

Run: `forge test --match-path "test/fee-concentration-index/integration/fork/*" --out out2 -v`
Expected: PASS

**Step 4: Final commit if any fixes were needed**

**Step 5: Push**

```bash
git push origin 003-reactive-integration
```

---

## Dependency Graph

```
Task 0: branch setup (ensure deps)
  ├─ Task 1: Dune V3 query (no code deps)
  │    └─ Task 2: Python V3 oracle (needs Dune output)
  │         └─ Task 5: Fork test (needs fixture from Task 2)
  ├─ Task 3: SomniaAdapterStorageMod (no deps)
  │    └─ Task 4: SomniaAdapter (needs Task 3)
  │         └─ Task 5: Fork test (needs adapter from Task 4)
  └─ Task 6: Full verification (needs all above)
```

Tasks 1 and 3 can run in parallel after Task 0.
Tasks 2 and 4 can run in parallel (independent outputs).
Task 5 depends on both Tasks 2 and 4.
Task 6 is the final gate.
