# Reactive Integration Fork Test Design: SomniaAdapter Accuracy Validation

**Date:** 2026-03-07
**Branch:** 003-reactive-integration
**Status:** Approved

## Goal

Validate that the reactive integration path computes the same FeeConcentrationIndex as a Python oracle, using real-world Uniswap V3 pool data replayed on a Somnia L1 fork. This proves the reactive event-intake → parameterized FCI pipeline produces correct results independently of V4.

## Target

- **Pool:** WETH/USDC 0.30% on Uniswap V3 Ethereum mainnet
- **Sample size:** ~50 lifecycle events (Swap, Mint, Burn, Collect)
- **Approach:** Monolithic SomniaAdapter with direct entry points, tested on Somnia fork

## Architecture

### Data Pipeline

```
Dune SQL query (V3 WETH/USDC 0.30%)
       |
       v
Python oracle (Q128 math, V3 event replay, Collect accumulation)
       |
       v
data/fixtures/fci_weth_usdc_v3.json
       |
       v
Forge integration fork test on Somnia — reads fixture via vm.readFile + vm.parseJson
```

### Dune Query (`data/queries/fci_weth_usdc_v3.sql`)

- Target: WETH/USDC 0.30% pool on Uniswap V3 Ethereum mainnet
- Events: Swap, Mint, Burn, Collect — ordered by `(block_number, log_index)`
- ~50 lifecycle events in a dense block range
- All 4 event types needed because Collect fees are accumulated separately in V3

### Python Oracle (`data/scripts/fci_v3_oracle.py`)

- Reads raw Dune export
- Replays V3 events through exact FCI math: Q128 fixed-point, integer sqrt, addTerm, incrementPos/decrementPos
- Handles Collect accumulation per position (same logic as ReactLogicMod)
- On Burn: consumes accumulated fees, computes SyntheticFeeGrowth, derives FeeShareRatio
- At snapshot blocks: records `(indexA, thetaSum, posCount, accumulatedSum)`
- Outputs pre-baked fixture with events + expected values
- Burn events in the fixture include pre-accumulated fee0/fee1

### JSON Fixture Schema (`data/fixtures/fci_weth_usdc_v3.json`)

```json
{
  "pool": {
    "address": "0x...",
    "token0": "0x...",
    "token1": "0x...",
    "fee": 3000,
    "tickSpacing": 60
  },
  "somniaForkBlock": 12345678,
  "events": [
    {
      "blockNumber": 21000010,
      "eventType": "Swap",
      "tick": -200520
    },
    {
      "blockNumber": 21000012,
      "eventType": "Mint",
      "owner": "0x...",
      "tickLower": -60,
      "tickUpper": 60,
      "liquidity": "1000000000000000000"
    },
    {
      "blockNumber": 21000015,
      "eventType": "Burn",
      "owner": "0x...",
      "tickLower": -60,
      "tickUpper": 60,
      "liquidity": "1000000000000000000",
      "fee0": "500000000000",
      "fee1": "300000000000"
    }
  ],
  "snapshots": [
    {
      "blockNumber": 21000050,
      "expectedIndexA": "170141183460469231731687303715884105727",
      "expectedThetaSum": "340282366920938463463374607431768211456",
      "expectedPosCount": "2"
    }
  ]
}
```

Note: Collect events are consumed by the Python oracle during accumulation. They do not appear as replay events — their fees are baked into the subsequent Burn event's fee0/fee1 fields.

## SomniaAdapter Contract

### File: `src/reactive-integration/adapters/somnia/SomniaAdapter.sol`

Storage: Own diamond slot at `keccak256("SomniaAdapter.fci.storage")`, accessor in `SomniaAdapterStorageMod.sol`.

### Entry Points

```solidity
onV3Swap(V3SwapData calldata data)
    → incrementOverlappingRanges($, poolId, data.tick, data.tick)

onV3Mint(V3MintData calldata data)
    → registerPosition($, poolId, rk, posKey, ...)
    → setFeeGrowthBaseline($, poolId, posKey, 0)
    → incrementPosCount($, poolId)

onV3Burn(V3BurnData calldata data, uint256 fee0, uint256 fee1)
    → deregisterPosition($, poolId, posKey, data.liquidity)
    → if swapLifetime > 0: SyntheticFeeGrowth → FeeShareRatio → addStateTerm
    → decrementPosCount($, poolId)
    → deleteFeeGrowthBaseline($, poolId, posKey)

getIndex(PoolKey calldata key) view → (uint128 indexA, uint256 thetaSum, uint256 posCount)
```

### Key Properties

- No auth layer — Somnia binding is TBD, auth added when known
- No Collect accumulation — handled offline by Python oracle, baked into fixture
- Reuses all parameterized FCI wrappers from `FeeConcentrationIndexStorageMod.sol`
- Reuses V3 typed structs from `ReactiveCallbackDataMod.sol`
- Reuses `SyntheticFeeGrowthMod`, `CollectedFeesMod` (v3PositionKey), `PoolKeyExtMod`
- `receive() external payable` — placeholder for future Somnia binding
- SCOP compliant: no `is`, no `library`, no `modifier`

### Differences from ReactiveHookAdapter

- No `requireAuthorized` / `authorizedCallers` / `rvmId`
- No Collect accumulation (offline in oracle vs. online in ReactVM)
- Independent storage slot
- No dependency on Reactive Network libraries

## Forge Integration Fork Test

### File: `test/fee-concentration-index/integration/fork/SomniaAdapter.integration.fork.t.sol`

### Setup

1. `vm.createSelectFork("somnia", somniaForkBlock)` — fork Somnia at a recent block
2. Deploy `SomniaAdapter` on the Somnia fork
3. Load JSON fixture via `vm.readFile` + `vm.parseJson`
4. Construct `PoolKey` directly from fixture pool parameters (token0, token1, fee, tickSpacing) — no `fromV3Pool()` call since the V3 pool doesn't exist on Somnia

### Replay Loop

```
for each event in fixture.events:
    if event.type == "Swap":
        adapter.onV3Swap(V3SwapData({pool: mockPool, tick: event.tick}))
    elif event.type == "Mint":
        adapter.onV3Mint(V3MintData({pool: mockPool, owner: event.owner, ...}))
    elif event.type == "Burn":
        adapter.onV3Burn(V3BurnData({...}), event.fee0, event.fee1)

    if event.blockNumber is a snapshot block:
        (indexA, thetaSum, posCount) = adapter.getIndex(poolKey)
        assertApproxEqAbs(indexA, expected.indexA, tolerance)
        assertEq(thetaSum, expected.thetaSum)
        assertEq(posCount, expected.posCount)
```

### PoolKey Construction

The V3 pool contract doesn't exist on Somnia, so `fromV3Pool()` can't be used at test time. Instead, the test constructs the `PoolKey` directly from fixture data:

```solidity
PoolKey memory key = PoolKey({
    currency0: Currency.wrap(fixture.pool.token0),
    currency1: Currency.wrap(fixture.pool.token1),
    fee: fixture.pool.fee,
    tickSpacing: fixture.pool.tickSpacing,
    hooks: IHooks(address(adapter))
});
```

A mock V3 pool address is also needed for the V3 typed structs. A minimal mock that returns the correct token0/token1/fee/tickSpacing is deployed in setup, or the pool address from the fixture is used as-is (the adapter only uses it as an identifier via `fromV3Pool` internally in `getIndex`).

### Tolerance

Same `_indexATolerance(n, bl)` from the fuzz test suite. `thetaSum` and `posCount` are exact.

### Test Name

`test_integration_fork_somniaAdapter_replayV3Events_indexMatchesOracle()`

### RPC Requirement

`SOMNIA_RPC_URL` env var. Test should skip gracefully if not set.

## File Layout

```
src/reactive-integration/adapters/somnia/
  SomniaAdapter.sol                          # Contract shell
  SomniaAdapterStorageMod.sol                # Diamond storage accessor

data/
  queries/fci_weth_usdc_v3.sql               # Dune V3 query
  scripts/fci_v3_oracle.py                   # Python oracle (offline)
  fixtures/fci_weth_usdc_v3.json             # Pre-baked fixture

test/fee-concentration-index/integration/fork/
  SomniaAdapter.integration.fork.t.sol       # Fork test
```

## Dependencies (from existing code on 003-reactive-integration)

- `FeeConcentrationIndexStorageMod.sol` — parameterized wrappers
- `FeeConcentrationStateMod.sol`, `TickRangeRegistryMod.sol`, `TickRangeMod.sol` — FCI types
- `SwapCountMod.sol`, `BlockCountMod.sol`, `FeeShareRatioMod.sol` — FCI primitives
- `ReactiveCallbackDataMod.sol` — V3 typed structs
- `SyntheticFeeGrowthMod.sol` — fee growth conversion
- `CollectedFeesMod.sol` — `v3PositionKey()`
- `PoolKeyExtMod.sol` — `fromV3Pool()` (used internally by getIndex)

## Out of Scope

- Somnia-specific reactive binding (event subscription API, callback mechanism) — TBD
- Auth layer for SomniaAdapter — added when Somnia binding is known
- Cross-check against V4 fork test results
- Collect accumulation inside the adapter
- Multiple pools / larger sample sizes
- SomniaEventRouter or any event routing layer
