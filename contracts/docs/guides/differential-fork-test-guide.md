# RAN Data API — FFI Reference for Differential Fork Tests

Date: 2026-04-11
Branch: ran-growth-pipeline

## Purpose

This document is a technical reference for the off-chain data API consumed by Solidity differential fork tests via Forge's `vm.ffi()`. It describes the FFI subcommands, their ABI-encoded outputs, the underlying data schema, and the constants needed to wire up FFI calls from Solidity.

## Data Source

**Database:** `data/ran_accumulator.duckdb` (relative to `contracts/` working directory)

Contains sampled `globalGrowth` values from the Angstrom hook contract on Ethereum mainnet, fetched via `eth_getStorageAt` against an archive RPC node.

**Schema:**

| Column | Type | Description |
|--------|------|-------------|
| `block_number` | UBIGINT | Ethereum block number |
| `pool_id` | VARCHAR | 0x-prefixed bytes32 pool identifier |
| `global_growth` | VARCHAR | 0x-prefixed 66-char hex (bytes32 storage value) |
| `block_timestamp` | UBIGINT | Unix timestamp of the block |
| `sampled_at` | TIMESTAMP | When the sample was fetched |
| `stride` | USMALLINT | Block interval between samples (currently 50) |

**Current dataset (USDC/WETH pool):**
- ~37,678 rows
- Block range: 22,972,937 to 24,856,787
- Stride: 50 blocks (~600 seconds at 12s/block)
- All timestamps backfilled

## Pool Constants

| Name | Value |
|------|-------|
| USDC/WETH pool ID | `0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657` |
| WETH/USDT pool ID | `0x90078845bceb849b171873cfbc92db8540e9c803ff57d9d21b1215ec158e79b3` |
| Angstrom hook | `0x0000000aa232009084Bd71A5797d089AA4Edfad4` |
| Pool Manager | `0x000000000004444c5dc75cB358380D2e3dE08A90` |
| BLOCK_NUMBER_0 | `22_972_937` |
| DB path (relative) | `data/ran_accumulator.duckdb` |

## FFI Invocation

All FFI calls use the Python module runner:

```
.venv/bin/python3 -m scripts.ran_ffi <subcommand> [args]
```

From Solidity, use the `ffiPython()` helper defined in `test/_helpers/BaseTest.sol`:

```solidity
// BaseTest.sol provides:
function ffiPython(string[] memory args) internal returns (bytes memory);
// Prepends ".venv/bin/python3" to args, calls vm.ffi()
```

All outputs are `0x`-prefixed ABI-encoded hex printed to stdout. Errors exit with code 1 and print a message to stderr. **Forge's `vm.ffi()` reverts on non-zero exit codes**, so error conditions surface as test reverts automatically.

**`--db` argument:** Required on every subcommand. Path is relative to Forge's working directory (`contracts/`). Always pass `data/ran_accumulator.duckdb`.

**`--pool` argument:** Accepts raw bytes32 hex with or without `0x` prefix, any case. Normalized internally to `0x`-prefixed lowercase. From Solidity, convert a `PoolId` via `vm.toString(PoolId.unwrap(poolId))`.

**Venv note:** The absolute path `.venv/bin/python3` is hardcoded in `ffiPython()`, so venv activation is not required — the interpreter resolves its own site-packages.

**Valid index range:** 0 to `len() - 1`. Valid timestamps: any value `>=` the earliest `block_timestamp` in the dataset (for nearest mode).

**Stderr examples:** `error: pool not found`, `error: index 6 out of range [0, 5]`, `error: run pipeline to backfill timestamps`.

**Ordering:** All multi-row outputs (`range`, `get_all`) are sorted by `block_number ASC`.

## FFI Subcommands

### `len` — Dataset Row Count

```
.venv/bin/python3 -m scripts.ran_ffi len --pool <hex> --db <path>
```

**Output:** `abi.encode(uint256)` — total number of rows for the pool.

**Solidity decode:**
```solidity
(uint256 count) = abi.decode(result, (uint256));
```

**Errors:** Exit 1 if pool has no data.

---

### `row` — Single Row by Index

```
.venv/bin/python3 -m scripts.ran_ffi row --pool <hex> --idx <n> --db <path>
```

**Args:**
- `--idx` — 0-based index into rows ordered by `block_number ASC`

**Output:** `abi.encode(uint256, uint256, bytes32)` — `(blockNumber, blockTimestamp, globalGrowth)`

**Solidity decode:**
```solidity
(uint256 blockNumber, uint256 blockTimestamp, bytes32 globalGrowth) =
    abi.decode(result, (uint256, uint256, bytes32));
```

**Errors:** Exit 1 if index is out of bounds, negative, or row has NULL timestamp.

---

### `row-by-ts` — Single Row by Timestamp

```
.venv/bin/python3 -m scripts.ran_ffi row-by-ts --pool <hex> --ts <n> --db <path> [--nearest]
```

**Args:**
- `--ts` — Unix timestamp (integer)
- `--nearest` — (optional flag) If set, returns the nearest-lower row (`block_timestamp <= ts`). Without this flag, requires exact match.

**Output:** `abi.encode(uint256, uint256, bytes32)` — `(blockNumber, blockTimestamp, globalGrowth)`

**Solidity decode:** Same as `row`.

**Errors:** Exit 1 if no match found (exact mode) or timestamp is below the dataset minimum (nearest mode).

**Tie-breaking:** In both exact and nearest modes, if multiple rows share the same `block_timestamp`, the one with the highest `block_number` is returned.

---

### `range` — Row Slice by Index

```
.venv/bin/python3 -m scripts.ran_ffi range --pool <hex> --from <n> --to <n> --db <path>
```

**Args:**
- `--from` — Start index (inclusive, 0-based)
- `--to` — End index (exclusive)

**Output:** `abi.encode(uint256, uint256[], uint256[], bytes32[])` — `(count, blockNumbers[], blockTimestamps[], globalGrowths[])`

**Solidity decode:**
```solidity
(uint256 count, uint256[] memory blockNumbers, uint256[] memory blockTimestamps, bytes32[] memory globalGrowths) =
    abi.decode(result, (uint256, uint256[], uint256[], bytes32[]));
```

**Limits:** Maximum 1,000 rows per call. Exceeding this exits 1.

**Errors:** Exit 1 if `from > to`, `from < 0`, `to > dataset_len`, or span exceeds 1,000.

---

### `min` — First Row (Earliest Block)

```
.venv/bin/python3 -m scripts.ran_ffi min --pool <hex> --db <path>
```

**Output:** `abi.encode(uint256, uint256, bytes32)` — `(blockNumber, blockTimestamp, globalGrowth)` for the row with the smallest `block_number`.

**Solidity decode:** Same as `row`.

**Errors:** Exit 1 if pool has no data.

---

### `max` — Last Row (Latest Block)

```
.venv/bin/python3 -m scripts.ran_ffi max --pool <hex> --db <path>
```

**Output:** `abi.encode(uint256, uint256, bytes32)` — `(blockNumber, blockTimestamp, globalGrowth)` for the row with the largest `block_number`.

**Solidity decode:** Same as `row`.

**Errors:** Exit 1 if pool has no data.

---

## On-Chain Reader

`src/_adapters/AngstromAccumulatorConsumer.sol` provides read-only access to Angstrom's on-chain state:

```solidity
contract AngstromAccumulatorConsumer {
    constructor(IAngstromAuth _angstrom, IPoolManager _poolManager);

    // Returns cumulative global reward growth for a pool.
    // Reads via extsload at: keccak256(abi.encode(poolId, 7)) + 16777216
    function globalGrowth(PoolId poolId) external view returns (uint256);

    // Returns cumulative reward growth inside a tick range.
    function growthInside(PoolId poolId, int24 tickLower, int24 tickUpper) external view returns (uint256);

    // Returns the block number of the most recent Angstrom bundle execution.
    function lastBlockUpdated() external view returns (uint64);
}
```

**Storage layout constants:**
- `POOL_REWARDS_SLOT = 7`
- `REWARD_GROWTH_SIZE = 16777216` (offset to `globalGrowth` within the rewards struct)

## Existing Test Infrastructure

**`test/_helpers/BaseTest.sol`:**
- `ffiPython(string[] memory args) -> bytes memory` — prepends `.venv/bin/python3`, calls `vm.ffi()`
- `pythonRunCmd() -> string[] memory` — returns `[".venv/bin/python3"]`

**`test/_helpers/BaseForkTest.t.sol`:**
- Extends `BaseTest`
- `setUp()` creates a fork at `BLOCK_NUMBER_0` (22,972,937) via `vm.createSelectFork(vm.rpcUrl("mainnet"), BLOCK_NUMBER_0)`
- Exposes `USDC_WETH`, `WETH_USDT` as `PoolId` values
- `onlyForked()` modifier — skips test if `ALCHEMY_API_KEY` env var is not set

**`test/_fork_references/Ethereum.sol`:**
- `AngstromAddresses.USDC_WETH` — bytes32 pool ID
- `AngstromAddresses.ANGSTROM` — hook contract address
- `AngstromAddresses.BLOCK_NUMBER_0` — 22,972,937
- `UniswapAddresses.POOL_MANAGER` — Pool Manager address
- `Tokens.WETH`, `Tokens.USDC`, `Tokens.USDT` — token addresses

## FFI-to-Pseudocode Mapping

The `row` subcommand returns all three values (`blockNumber`, `blockTimestamp`, `globalGrowth`) in a single FFI call, which is more efficient than three separate calls. The pseudocode getters from the original design map to FFI subcommands as follows:

| Pseudocode getter | FFI equivalent |
|-------------------|---------------|
| `dataSetLen(poolId)` | `len --pool <id> --db <path>` → decode `(uint256)` |
| `getBlockNumber(poolId, idx)` | `row --pool <id> --idx <n> --db <path>` → first element of `(uint256, uint256, bytes32)` |
| `getBlockTimestamp(poolId, idx)` | `row --pool <id> --idx <n> --db <path>` → second element |
| `getGlobalGrowth(poolId, idx)` | `row --pool <id> --idx <n> --db <path>` → third element (bytes32) |
| `getGlobalGrowth(poolId, blockTimestamp)` | `row-by-ts --pool <id> --ts <n> --db <path>` → third element |

## Running Tests with FFI

```bash
cd contracts
source .venv/bin/activate
forge test --ffi --match-path "test/differential/*" -vv
```

**Requirements:**
- `ALCHEMY_API_KEY` in `.env` (for mainnet fork RPC)
- Python venv at `.venv/` with `duckdb` and `eth_abi` installed
- `data/ran_accumulator.duckdb` populated by the pipeline

## Golden Test Vectors

These indices (from the notebook EDA) are worth explicit (non-fuzz) assertions:

| Label | Description |
|-------|-------------|
| Index 0 | First block (22,972,937) — Angstrom genesis |
| Last index | Most recent sample |
| First non-zero | First block where `globalGrowth > 0` (first settlement) |
| Max spike | Largest single-stride growth delta |
| Zero-growth | Block where `globalGrowth == 0` (pre-settlement) |
| Midpoint | Middle of dataset |

Retrieve exact values via `row --pool <id> --idx <n> --db data/ran_accumulator.duckdb`.
