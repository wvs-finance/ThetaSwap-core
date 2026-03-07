# FCI Fork Test Design: Real-World Accuracy Validation

**Date:** 2026-03-07
**Branch:** 001-fee-concentration-index
**Status:** Approved

## Goal

Validate the FeeConcentrationIndex against real-world Uniswap V4 pool data by replaying on-chain events on a mainnet fork and comparing the computed FCI index against a Python oracle that implements the exact same Q128 fixed-point math.

## Target

- **Pool:** WETH/USDC on Uniswap V4 Ethereum mainnet
- **Sample size:** ~50 lifecycle events (adds, swaps, removes)
- **Approach:** Direct fork replay (Approach A)

## Architecture

### Data Pipeline

```
Dune SQL query --> raw event export (CSV/JSON)
       |
       v
Python oracle (Q128 math) --> data/fixtures/fci_weth_usdc_v4.json
       |
       v
Forge fork test reads fixture via vm.readFile + vm.parseJson
```

### Dune Queries (`data/queries/fci_weth_usdc_v4.sql`)

Two queries:

1. **Event stream**: ~50 lifecycle events for WETH/USDC V4 pool ordered by `(block_number, log_index)`. Fields per row:
   - `block_number`, `tx_hash`, `log_index`
   - `event_type`: `ModifyLiquidity` or `Swap`
   - `sender`, `tickLower`, `tickUpper`, `liquidityDelta` (liquidity events)
   - `tick` (swap events -- post-swap tick)
   - `sqrtPriceX96` (context)

2. **Snapshots**: At 3-5 block numbers within the event range, capture pool position set and tick state for intermediate FCI cross-checks.

### Python Oracle (`data/scripts/fci_oracle.py`)

- Reads raw Dune export
- Replays events through exact FCI math: Q128 fixed-point, integer `sqrt`, `addTerm`, `incrementPos`/`decrementPos`
- At each snapshot block, records `(indexA, thetaSum, posCount, accumulatedSum)`
- Outputs pre-baked fixture with events + expected values

### JSON Fixture Schema (`data/fixtures/fci_weth_usdc_v4.json`)

```json
{
  "pool": {
    "token0": "0x...",
    "token1": "0x...",
    "fee": 500,
    "tickSpacing": 10,
    "hooks": "0x..."
  },
  "forkBlock": 21000000,
  "events": [
    {
      "blockNumber": 21000010,
      "txHash": "0x...",
      "logIndex": 0,
      "eventType": "ModifyLiquidity",
      "sender": "0x...",
      "tickLower": -60,
      "tickUpper": 60,
      "liquidityDelta": "1000000000000000000"
    }
  ],
  "snapshots": [
    {
      "blockNumber": 21000050,
      "expectedIndexA": "170141183460469231731687303715884105727",
      "expectedThetaSum": "340282366920938463463374607431768211456",
      "expectedPosCount": "2",
      "expectedAccumulatedSum": "..."
    }
  ]
}
```

## Forge Fork Test

### File: `test/fee-concentration-index/fork/FeeConcentrationIndex.fork.t.sol`

### Setup

1. `vm.createSelectFork("mainnet", forkBlock)` -- fork at the block just before the first event
2. Deploy `FeeConcentrationIndexHarness` at a CREATE2 address with correct hook flag bits (via HookMiner)
3. Harness constructor takes the real on-chain `PositionManager` -- `_poolManager()` returns the actual mainnet PoolManager
4. Load JSON fixture via `vm.readFile` + `vm.parseJson`

### Replay Loop

```
for each event in fixture.events:
    vm.roll(event.blockNumber)
    if event.type == "ModifyLiquidity" && liquidityDelta > 0:
        call harness.afterAddLiquidity(...)
    elif event.type == "Swap":
        call harness.beforeSwap(...) then harness.afterSwap(...)
    elif event.type == "ModifyLiquidity" && liquidityDelta < 0:
        call harness.beforeRemoveLiquidity(...) then harness.afterRemoveLiquidity(...)

    if event.blockNumber is a snapshot block:
        (indexA, thetaSum, posCount) = harness.getIndex(key, false)
        assertApproxEqAbs(indexA, expectedIndexA, tolerance)
        assertEq(thetaSum, expectedThetaSum)
        assertEq(posCount, expectedPosCount)
```

### Key Design Decisions

- **Direct hook calls, not through PoolManager**: We call hook functions directly on the harness. This avoids needing token balances/approvals while still reading real on-chain state (feeGrowthInside, tick) from the forked PoolManager via StateLibrary.
- **Pre-baked JSON, no FFI at test time**: Python oracle runs offline once. Forge test reads the fixture deterministically. CI-friendly, no Python dependency at test time.
- **Tolerance**: `indexA` uses `_indexATolerance(n, bl)` from the fuzz test suite. `thetaSum` and `posCount` are exact (no rounding in their accumulation).

## Edge Cases

- **Duplicate position keys**: Same sender + same tick range across multiple adds. Registry handles re-registration (idempotent, tested in unit tests).
- **Block gaps**: Events may be sparse. `vm.roll` skips ahead.
- **Zero-liquidity adds**: Filtered out in the Dune query.
- **Tick crossing during swap**: beforeSwap/afterSwap transient storage pair works identically in fork context.

## Error Handling

- **JSON parse failure**: `vm.parseJson` reverts on malformed JSON -- test fails loudly.
- **Fork RPC failure**: Standard forge behavior -- test skipped/failed if `ETH_RPC_URL` not set.
- **Pool state mismatch**: If pool doesn't exist at `forkBlock`, `getCurrentTick` reverts immediately.

## Test Naming

- `test_fork_wethUsdc_replayEvents_indexMatchesOracle()` -- main replay test
- Future: `test_fork_wethUsdc_snapshotN_stateConsistent()` -- per-snapshot granular tests

## File Layout

```
data/
  queries/fci_weth_usdc_v4.sql          # Dune SQL queries
  scripts/fci_oracle.py                 # Python oracle (Q128 math)
  fixtures/fci_weth_usdc_v4.json        # Pre-baked test fixture
test/fee-concentration-index/fork/
  FeeConcentrationIndex.fork.t.sol      # Fork test
```

## Out of Scope (future work)

- Simulated replay without fork (Approach B)
- Per-event property assertions (Approach C)
- Multiple pools / larger sample sizes
- Reactive path (V3) fork testing
