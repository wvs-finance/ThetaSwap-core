# RAN Fork Test: Accumulator Snapshot Validation — Design Specification

**Date**: 2026-04-07
**Branch**: `thetaswap-patches` (worktree: `.worktree/ranFromAngstrom/contracts/`)
**Status**: Design approved, pending implementation plan
**Upstream plan**: `docs/superpowers/plans/2026-04-06-range-accrual-note-v1a.md` (Task 6 adapted)

---

## 1. What We're Building

A single Forge fork test that story-tells the Angstrom reward accumulator values over 3-5 blocks by comparing the `AngstromRANOracleAdapter` (`ran.sol`) reads against a pre-frozen JSON fixture. Two-phase process: (1) freeze script populates the fixture via Dune MCP + archive RPC, (2) fork test consumes it.

---

## 2. Phase 1: Freezing Script

### Discovery (Dune MCP)

Query Angstrom reward events to find 3-5 blocks in Period 3 (mature regime, blocks ≥ 22_200_000 — after Angstrom's reward distribution stabilized, per Exercise B session summary) where `globalGrowth` incremented. Also discover an active LP position with non-zero `rewardGrowthOutside` on both tick boundaries.

Target contract: Angstrom hook `0x0000000aa232009084bd71a5797d089aa4edfad4`.
Target pool: `0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657`.

**PoolId compatibility assumption:** The same `poolId` bytes are used for both the Angstrom hook's `poolRewards` mapping (slot 7) and the V4 PoolManager's `pools` mapping (slot 6). This is true by design — Angstrom is a V4 hook and uses V4's `PoolId = keccak256(abi.encode(PoolKey))`.

### Slot Reads (RPC via `cast storage`)

For each discovered block, read 4 storage values via `eth_getStorageAt` on an archive RPC:

| Value | Slot derivation | Source | `extsload` signature |
|-------|----------------|--------|---------------------|
| `globalGrowth` | `keccak256(abi.encode(poolId, 7)) + 2^24` | Angstrom hook | `extsload(uint256) → uint256` |
| `rewardGrowthOutside[tickLower]` | `keccak256(abi.encode(poolId, 7)) + uint24(tickLower)` | Angstrom hook | `extsload(uint256) → uint256` |
| `rewardGrowthOutside[tickUpper]` | `keccak256(abi.encode(poolId, 7)) + uint24(tickUpper)` | Angstrom hook | `extsload(uint256) → uint256` |
| `slot0` (current tick) | V4 PoolManager pool state slot | V4 PoolManager `0x000000000004444c5dc75cB358380D2e3dE08A90` | `extsload(bytes32) → bytes32` |

**`extsload` signature difference:** The Angstrom hook's `extsload` takes `uint256` and returns `uint256`. The V4 PoolManager's `extsload` takes `bytes32` and returns `bytes32`. The adapter handles this internally (using `IUniV4.gudExtsload` for PoolManager reads). The freezing script must use the correct signature per contract — `eth_getStorageAt` bypasses this since it reads raw storage, but any direct `extsload` calls must match the target contract's ABI.

The tick range `[tickLower, tickUpper)` is discovered from Dune — an active LP position with non-zero `rewardGrowthOutside` on both boundaries.

**int24 → uint24 wrapping for negative ticks:** Angstrom indexes `rewardGrowthOutside` by `uint24(tick)`. For negative ticks, Solidity's `uint24(int24)` performs two's complement wrapping: `uint24(-1200) = 16776016`, `uint24(-600) = 16776616`. The freezing script (Python) must replicate this: `tick_offset = tick & 0xFFFFFF`. Using raw negative values will compute wrong slots silently.

### Pre-computation

The freezing script computes `expectedGrowthInside` for each snapshot using the three-branch formula and the raw slot values:

- `currentTick < tickLower`: `outsideBelow - outsideAbove`
- `currentTick in [tickLower, tickUpper)`: `globalGrowth - outsideBelow - outsideAbove`
- `currentTick >= tickUpper`: `outsideAbove - outsideBelow`

This pre-computed value is the "oracle truth" the fork test asserts against.

### Output Format

JSON at `test/_fixtures/ran_accumulator_snapshots.json`:

```json
{
  "pool": {
    "poolId": "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657",
    "angstromHook": "0x0000000aa232009084bd71a5797d089aa4edfad4",
    "poolManager": "0x000000000004444c5dc75cB358380D2e3dE08A90",
    "tickLower": -1200,
    "tickUpper": -600
  },
  "snapshots": [
    {
      "blockNumber": 21500000,
      "blockTimestamp": 1737000000,
      "globalGrowth": "0x...",
      "outsideBelow": "0x...",
      "outsideAbove": "0x...",
      "currentTick": -900,
      "expectedGrowthInside": "0x..."
    }
  ]
}
```

Tick values in the JSON are placeholders — the actual values come from the Dune discovery step. Snapshots are ordered by ascending `blockNumber`. The `expectedGrowthInside` field is derived from the raw slot values by the freezing script, not from on-chain reads.

---

## 3. Phase 2: Fork Test

### Single Test Function

`test/AngstromRANOracleAdapter.fork.t.sol` contains one test:

```
function test_accumulatorSnapshotsMatchFixture()
```

### Test Flow

1. Read JSON fixture via `vm.readFile("test/_fixtures/ran_accumulator_snapshots.json")` + `vm.parseJson`
2. `vm.createFork(vm.envString("ETH_RPC_URL"), snapshots[0].blockNumber)` — fork at first snapshot block
3. Deploy `AngstromRANOracleAdapter(angstromHook, poolManager)` on the fork
4. For each snapshot (i = 0..N-1):
   - `vm.rollFork(snapshot.blockNumber)`
   - Assert exact: `adapter.globalGrowth(poolId) == snapshot.globalGrowth`
   - Assert exact: `adapter.growthInside(poolId, tickLower, tickUpper) == snapshot.expectedGrowthInside`
   - Conservation cross-check (for in-range snapshots where `tickLower <= currentTick < tickUpper`): assert `expectedGrowthInside == globalGrowth - outsideBelow - outsideAbove` using raw fixture values
5. Assert monotonicity: `globalGrowth[i] >= globalGrowth[i-1]` for all consecutive pairs

### Assertion Strategy

| Value | Match type | Rationale |
|-------|-----------|-----------|
| `globalGrowth` | Exact equality | Single slot read, deterministic |
| `growthInside` | Exact equality | Both fixture and fork read the same block — storage is deterministic. Any mismatch indicates a real bug (wrong slot, wrong branch, int24 wrapping error). |
| Conservation | Exact equality | For in-range snapshots: `growthInside == globalGrowth - outsideBelow - outsideAbove`. Validates branch selection and arithmetic independently of the adapter. |
| Monotonicity | Strict `>=` | Accumulators are cumulative sums, never decrease |

---

## 4. File Locations

| File | Path | New? |
|------|------|------|
| Fixture JSON | `test/_fixtures/ran_accumulator_snapshots.json` | Yes — created by freezing script |
| Fork test | `test/AngstromRANOracleAdapter.fork.t.sol` | Yes |
| Foundry config | `foundry.toml` | Edit — add `fs_permissions` for `test/_fixtures` |

### foundry.toml change

Add read permission for the fixture directory:

```toml
fs_permissions = [
    { access = "read-write", path = ".forge-snapshots/" },
    { access = "read", path = "test/_fixtures" }
]
```

---

## 5. Run Command

```bash
ETH_RPC_URL=<archive_rpc> forge test --match-contract AngstromRANOracleAdapterForkTest -vv
```

Requires an archive-capable RPC (Alchemy, dRPC, Infura archive) since the test rolls to historical blocks.

---

## 6. Data Points

3-5 block snapshots from Period 3 (mature Angstrom regime, blocks ≥ 22_200_000). Selection criteria:
- Blocks where `globalGrowth` incremented (non-zero reward distribution)
- Tick range from an active LP position discovered via Dune with non-zero `rewardGrowthOutside` on both boundaries
- At least one snapshot where `currentTick` is in-range, confirming the middle branch of the three-branch formula

**Period 3 definition:** Blocks ≥ 22_200_000 (approximately late March 2026). This is when Angstrom's reward distribution stabilized into a consistent pattern after initial bootstrapping (Periods 1-2). Per Exercise B session summary, only Period 3 data is policy-relevant for demand estimation. The freezing script should select blocks within this range.

---

## 7. Dependencies

| Dependency | Required for |
|-----------|-------------|
| Dune MCP | Discovery: find blocks with reward events, find active LP tick range |
| Archive RPC | Slot reads at historical blocks (`eth_getStorageAt`) |
| `cast storage` or Python `web3.eth.get_storage_at` | Freezing script slot reads |
| `vm.readFile` + `vm.parseJson` (Forge) | Fork test reads fixture |

---

## 8. Non-Goals

- This test does NOT validate the n/N ratio computation (that's the differential test, Task 10)
- This test does NOT validate `AccrualManagerMod` functions (those need separate unit/integration tests)
- This test does NOT require the Python FFI oracle — it's pure Solidity + JSON fixture
- No ERC-1155 minting or claim flow is tested — only the oracle adapter reads
