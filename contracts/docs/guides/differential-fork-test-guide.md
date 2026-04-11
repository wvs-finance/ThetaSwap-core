# Differential Fork Test Guide: RAN globalGrowth Accumulator

Date: 2026-04-11
Branch: ran-growth-pipeline

## What This Guide Is For

You are an AI agent tasked with implementing a differential fuzz test in Solidity (Foundry/Forge). This guide is your complete reference. It assumes you have Solidity and Forge expertise, understand fork testing, but know nothing about the RAN pipeline, its FFI API, or its data schema.

**Your deliverable:** A single new test file at `test/differential/DifferentialGrowthFork.t.sol`. You will not modify any existing file.

---

## 1. What You Are Testing

An off-chain Python pipeline sampled `globalGrowth` values from the Angstrom hook contract on Ethereum mainnet across ~37,678 blocks. These values are stored in a local DuckDB database. Your test verifies: **for any sampled block in the database, rolling a Forge fork to that block and reading `globalGrowth` via `extsload` produces the same value the pipeline recorded.**

If the test passes, the off-chain data is a faithful mirror of on-chain state.

---

## 2. Architecture Overview

### 2.1 On-Chain Contracts (Read-Only, DO NOT MODIFY)

**Angstrom Hook:**
- Address: `0x0000000aa232009084Bd71A5797d089AA4Edfad4`
- Stores cumulative reward growth per pool in the `poolRewards` mapping at storage slot 7

**Uniswap V4 Pool Manager:**
- Address: `0x000000000004444c5dc75cB358380D2e3dE08A90`

**AngstromAccumulatorConsumer** (`src/_adapters/AngstromAccumulatorConsumer.sol`):
- Read-only client that reads Angstrom storage via `extsload`
- Constructor: `constructor(IAngstromAuth _angstrom, IPoolManager _poolManager)`
- Key function: `globalGrowth(PoolId poolId) external view returns (uint256)`
- Derives the storage slot internally: `keccak256(abi.encode(poolId, 7)) + 16777216`

### 2.2 Target Pool

USDC/WETH:
```
Pool ID: 0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657
```

### 2.3 Off-Chain Data Pipeline (Already Built, DO NOT MODIFY)

| Component | Path | Purpose |
|-----------|------|---------|
| `scripts/ran_growth_pipeline.py` | Bulk fetches `globalGrowth` from Alchemy archive RPC, stores in DuckDB |
| `scripts/ran_data_api.py` | Pure-function query API consumed by FFI and notebooks |
| `scripts/ran_ffi.py` | CLI wrapper that ABI-encodes query results for Solidity `vm.ffi()` |
| `data/ran_accumulator.duckdb` | DuckDB database with ~37,678 sampled rows |

---

## 3. DuckDB Schema and Data Characteristics

```sql
CREATE TABLE accumulator_samples (
    block_number    UBIGINT,
    pool_id         VARCHAR,        -- 0x-prefixed 66-char hex (bytes32)
    global_growth   VARCHAR,        -- 0x-prefixed 66-char hex (bytes32)
    block_timestamp UBIGINT,
    sampled_at      TIMESTAMP,
    stride          USMALLINT,
    PRIMARY KEY (pool_id, block_number)
)
```

- ~37,678 rows for the USDC/WETH pool
- Block range: 22,972,937 through 24,856,787
- Stride: 50 blocks between samples (~10 minutes)
- All rows have backfilled `block_timestamp` values
- `global_growth` is the raw `uint256` storage value, hex-encoded as `bytes32`
- Early blocks (before Angstrom's first settlement) have `globalGrowth == 0`

---

## 4. FFI API Reference

### 4.1 How FFI Works

The Python script `scripts/ran_ffi.py` reads from DuckDB and prints ABI-encoded hex to stdout. Forge's `vm.ffi()` captures this output. The `BaseTest` contract provides `ffiPython(string[] memory args) -> bytes memory`, which prepends `.venv/bin/python3` to your argument array and calls `vm.ffi()`.

From Solidity, build argument arrays starting with `-m scripts.ran_ffi` (Python module invocation syntax):

```solidity
string[] memory args = new string[](7);
args[0] = "-m";
args[1] = "scripts.ran_ffi";
args[2] = "len";              // subcommand
args[3] = "--pool";
args[4] = POOL_HEX;           // full bytes32 hex with 0x prefix
args[5] = "--db";
args[6] = DB_PATH;            // "data/ran_accumulator.duckdb"
bytes memory result = ffiPython(args);
```

On error, the script exits with code 1 and prints a message to stderr. `vm.ffi()` will revert if the subprocess exits non-zero.

### 4.2 Subcommand Reference

**`len`** -- Total row count for a pool.

```
.venv/bin/python3 -m scripts.ran_ffi len --pool <hex> --db <path>
```
Output: `abi.encode(uint256)` -- row count.
Decode: `(uint256 count) = abi.decode(result, (uint256))`

---

**`row`** -- Single row by 0-based index (ordered by ascending `block_number`).

```
.venv/bin/python3 -m scripts.ran_ffi row --pool <hex> --idx <n> --db <path>
```
Output: `abi.encode(uint256, uint256, bytes32)` -- `(blockNumber, blockTimestamp, globalGrowth)`.
Decode: `(uint256 blockNumber, uint256 blockTimestamp, bytes32 globalGrowth) = abi.decode(result, (uint256, uint256, bytes32))`

---

**`row-by-ts`** -- Single row by block timestamp.

```
.venv/bin/python3 -m scripts.ran_ffi row-by-ts --pool <hex> --ts <n> --db <path> [--nearest]
```
Output: `abi.encode(uint256, uint256, bytes32)` -- same as `row`.
The `--nearest` flag returns the nearest-lower row if no exact match exists.

---

**`range`** -- Row slice from index `from` (inclusive) to `to` (exclusive). Max 1,000 rows.

```
.venv/bin/python3 -m scripts.ran_ffi range --pool <hex> --from <n> --to <n> --db <path>
```
Output: `abi.encode(uint256, uint256[], uint256[], bytes32[])` -- `(count, blockNumbers[], blockTimestamps[], globalGrowths[])`.

---

**`min`** -- Row with the smallest `block_number`.

```
.venv/bin/python3 -m scripts.ran_ffi min --pool <hex> --db <path>
```
Output: `abi.encode(uint256, uint256, bytes32)` -- same as `row`.

---

**`max`** -- Row with the largest `block_number`.

```
.venv/bin/python3 -m scripts.ran_ffi max --pool <hex> --db <path>
```
Output: `abi.encode(uint256, uint256, bytes32)` -- same as `row`.

### 4.3 Constants for FFI Calls

Use these exact string values in your Solidity constants:

```solidity
string constant POOL_HEX = "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657";
string constant DB_PATH  = "data/ran_accumulator.duckdb";
```

---

## 5. Existing Test Infrastructure

### 5.1 BaseTest (`test/_helpers/BaseTest.sol`)

Import: `import {BaseTest} from "anstrong-test/_helpers/BaseTest.sol";`

Provides:
- `ffiPython(string[] memory args) -> bytes memory` -- Prepends `.venv/bin/python3` and calls `vm.ffi()`.
- `pythonRunCmd() -> string[] memory` -- Returns `[".venv/bin/python3"]`.

### 5.2 BaseForkTest (`test/_helpers/BaseForkTest.t.sol`)

Import: `import {BaseForkTest} from "anstrong-test/_helpers/BaseForkTest.t.sol";`

Extends `BaseTest`. Provides:
- `BLOCK_NUMBER_0` -- constant `22_972_937` (Angstrom genesis block).
- `POOL_MANAGER` -- `IPoolManager` instance at the Pool Manager address.
- `USDC_WETH` -- `PoolId` wrapping the USDC/WETH pool ID bytes32.
- `WETH`, `USDC`, `USDT` -- ERC20 token instances.
- `forked` -- boolean, true if `ALCHEMY_API_KEY` was found in `.env`.
- `onlyForked()` -- modifier that skips the test body if `forked` is false. The test still passes; it just does nothing.
- `setUp()` -- Creates a mainnet fork at `BLOCK_NUMBER_0` via `vm.createSelectFork(vm.rpcUrl("mainnet"), BLOCK_NUMBER_0)`. If `ALCHEMY_API_KEY` is missing, `forked` stays false.

### 5.3 Ethereum Fork Constants (`test/_fork_references/Ethereum.sol`)

Import: `import "anstrong-test/_fork_references/Ethereum.sol" as EthereumForkData;`

Key values:
```solidity
EthereumForkData.AngstromAddresses.ANGSTROM       // 0x0000000aa232009084Bd71A5797d089AA4Edfad4
EthereumForkData.AngstromAddresses.USDC_WETH      // bytes32 pool ID
EthereumForkData.AngstromAddresses.BLOCK_NUMBER_0  // 22_972_937
EthereumForkData.UniswapAddresses.POOL_MANAGER     // 0x000000000004444c5dc75cB358380D2e3dE08A90
```

### 5.4 Remappings (from `foundry.toml`, DO NOT MODIFY)

| Import Prefix | Resolves To |
|---------------|-------------|
| `anstrong-test/` | `test/` |
| `core/src/` | `src/` |
| `v4-core/src/` | `lib/v4-periphery/lib/v4-core/src/` |
| `forge-std/` | `lib/forge-std/src` |
| `openzeppelin-contracts/` | `lib/openzeppelin-contracts/contracts/` |

---

## 6. Complete Import List for Your Test File

```solidity
import {BaseForkTest} from "anstrong-test/_helpers/BaseForkTest.t.sol";
import {AngstromAccumulatorConsumer} from "core/src/_adapters/AngstromAccumulatorConsumer.sol";
import {IAngstromAuth} from "core/src/interfaces/IAngstromAuth.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {console2} from "forge-std/console2.sol";
import "anstrong-test/_fork_references/Ethereum.sol" as EthereumForkData;
```

---

## 7. Implementation Blueprint

### 7.1 Contract Skeleton

```solidity
// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {BaseForkTest} from "anstrong-test/_helpers/BaseForkTest.t.sol";
import {AngstromAccumulatorConsumer} from "core/src/_adapters/AngstromAccumulatorConsumer.sol";
import {IAngstromAuth} from "core/src/interfaces/IAngstromAuth.sol";
import "anstrong-test/_fork_references/Ethereum.sol" as EthereumForkData;

contract DifferentialGrowthForkTest is BaseForkTest {
    AngstromAccumulatorConsumer consumer;

    string constant POOL_HEX = "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657";
    string constant DB_PATH  = "data/ran_accumulator.duckdb";

    function setUp() public override {
        super.setUp();
        if (!forked) return;

        consumer = new AngstromAccumulatorConsumer(
            IAngstromAuth(EthereumForkData.AngstromAddresses.ANGSTROM),
            POOL_MANAGER
        );
    }

    // ... FFI helpers and test functions ...
}
```

**Why deploy in setUp, not per-test:** The `AngstromAccumulatorConsumer` is deployed once at `BLOCK_NUMBER_0`. When you call `vm.rollFork(someOtherBlock)`, the contract address remains valid -- Forge preserves deployed bytecode across fork rolls. But `extsload` reads Angstrom's storage at the *rolled-to block*, which is the entire point.

### 7.2 FFI Helper Functions

**Dataset length:**

```solidity
function _ffiDatasetLen() internal returns (uint256) {
    string[] memory args = new string[](7);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "len";
    args[3] = "--pool";
    args[4] = POOL_HEX;
    args[5] = "--db";
    args[6] = DB_PATH;
    bytes memory result = ffiPython(args);
    return abi.decode(result, (uint256));
}
```

**Single row by index:**

```solidity
function _ffiGetRow(uint256 idx) internal returns (
    uint256 blockNumber,
    uint256 blockTimestamp,
    bytes32 growth
) {
    string[] memory args = new string[](9);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "row";
    args[3] = "--pool";
    args[4] = POOL_HEX;
    args[5] = "--idx";
    args[6] = vm.toString(idx);
    args[7] = "--db";
    args[8] = DB_PATH;
    bytes memory result = ffiPython(args);
    (blockNumber, blockTimestamp, growth) = abi.decode(result, (uint256, uint256, bytes32));
}
```

**Min row (earliest block):**

```solidity
function _ffiGetMin() internal returns (
    uint256 blockNumber,
    uint256 blockTimestamp,
    bytes32 growth
) {
    string[] memory args = new string[](7);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "min";
    args[3] = "--pool";
    args[4] = POOL_HEX;
    args[5] = "--db";
    args[6] = DB_PATH;
    bytes memory result = ffiPython(args);
    (blockNumber, blockTimestamp, growth) = abi.decode(result, (uint256, uint256, bytes32));
}
```

**Max row (latest block):**

```solidity
function _ffiGetMax() internal returns (
    uint256 blockNumber,
    uint256 blockTimestamp,
    bytes32 growth
) {
    string[] memory args = new string[](7);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "max";
    args[3] = "--pool";
    args[4] = POOL_HEX;
    args[5] = "--db";
    args[6] = DB_PATH;
    bytes memory result = ffiPython(args);
    (blockNumber, blockTimestamp, growth) = abi.decode(result, (uint256, uint256, bytes32));
}
```

### 7.3 The Differential Fuzz Test

```solidity
function test__DifferentialFuzz__GlobalGrowthMatches(uint256 idxSeed) public onlyForked {
    // 1. Get total row count from DuckDB
    uint256 datasetLen = _ffiDatasetLen();
    require(datasetLen > 0, "empty dataset");

    // 2. Bound fuzz input to valid range
    uint256 idx = bound(idxSeed, 0, datasetLen - 1);

    // 3. Fetch the off-chain row
    (uint256 blockNumber, , bytes32 offchainGrowth) = _ffiGetRow(idx);

    // 4. Roll the fork to that exact block
    vm.rollFork(blockNumber);

    // 5. Read on-chain globalGrowth at that block
    uint256 onchainGrowth = consumer.globalGrowth(USDC_WETH);

    // 6. Assert equality
    assertEq(onchainGrowth, uint256(offchainGrowth), "globalGrowth mismatch");
}
```

**Key details:**
- `vm.rollFork(blockNumber)` sends an RPC call to the fork endpoint and updates the underlying chain state to that block. All subsequent storage reads reflect the state at that block.
- `globalGrowth()` returns `uint256`. The FFI returns `bytes32`. Cast with `uint256(offchainGrowth)`.
- The `onlyForked()` modifier makes the test a no-op (still passes) when `ALCHEMY_API_KEY` is absent.
- Each `vm.rollFork()` costs one RPC call. Keep fuzz runs modest (see Section 9).

### 7.4 Golden Vector Tests (Explicit, Non-Fuzz)

Add these as regression anchors alongside the fuzz test:

```solidity
/// @notice First block in dataset -- Angstrom genesis. globalGrowth should be 0.
function test__Golden__FirstBlock() public onlyForked {
    (uint256 blockNumber, , bytes32 offchainGrowth) = _ffiGetMin();
    vm.rollFork(blockNumber);
    uint256 onchainGrowth = consumer.globalGrowth(USDC_WETH);
    assertEq(onchainGrowth, uint256(offchainGrowth), "first block mismatch");
}

/// @notice Last block in dataset -- most recent sample.
function test__Golden__LastBlock() public onlyForked {
    (uint256 blockNumber, , bytes32 offchainGrowth) = _ffiGetMax();
    vm.rollFork(blockNumber);
    uint256 onchainGrowth = consumer.globalGrowth(USDC_WETH);
    assertEq(onchainGrowth, uint256(offchainGrowth), "last block mismatch");
}

/// @notice Index 0 -- first row by ascending block_number.
function test__Golden__IndexZero() public onlyForked {
    (uint256 blockNumber, , bytes32 offchainGrowth) = _ffiGetRow(0);
    vm.rollFork(blockNumber);
    uint256 onchainGrowth = consumer.globalGrowth(USDC_WETH);
    assertEq(onchainGrowth, uint256(offchainGrowth), "index 0 mismatch");
}

/// @notice Midpoint index -- spot check the middle of the dataset.
function test__Golden__Midpoint() public onlyForked {
    uint256 datasetLen = _ffiDatasetLen();
    uint256 mid = datasetLen / 2;
    (uint256 blockNumber, , bytes32 offchainGrowth) = _ffiGetRow(mid);
    vm.rollFork(blockNumber);
    uint256 onchainGrowth = consumer.globalGrowth(USDC_WETH);
    assertEq(onchainGrowth, uint256(offchainGrowth), "midpoint mismatch");
}
```

**Optional additional golden vectors** (recommended but not required):
- First block where `globalGrowth > 0` (first settlement): iterate early rows via `row` until growth is non-zero.
- A block where `globalGrowth == 0` (pre-settlement): index 0 likely covers this, but an explicit name helps readability.
- Block with the largest single-stride growth delta: requires comparing consecutive rows.

---

## 8. How vm.rollFork Works

`vm.rollFork(uint256 blockNumber)` is a Forge cheatcode that:

1. Sends `eth_getBlockByNumber` to the fork RPC endpoint for the target block.
2. Updates the fork's block context (`block.number`, `block.timestamp`, etc.).
3. All subsequent `SLOAD`, `EXTCODESIZE`, `CALL`, `STATICCALL` operate against the state at that block.

Contracts you deployed at the initial fork block remain callable. Forge preserves their bytecode. But when those contracts call `extsload` on external addresses, they read storage *at the rolled-to block*. This is the mechanism that makes differential testing across historical blocks possible.

---

## 9. Running the Test

### 9.1 Prerequisites

1. **Alchemy API key** in `contracts/.env`:
   ```
   ALCHEMY_API_KEY=your_key_here
   ```
   The fork RPC URL in `foundry.toml` is `https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}`.

2. **Python venv activated** (required for FFI subprocess):
   ```bash
   cd contracts
   source .venv/bin/activate
   ```
   The venv has `duckdb` and `eth_abi` already installed.

3. **DuckDB database populated** at `contracts/data/ran_accumulator.duckdb`. Already done by the pipeline.

### 9.2 Commands

```bash
cd contracts
source .venv/bin/activate

# Run all differential tests
forge test --ffi --match-path "test/differential/*" -vv

# Run only the fuzz test
forge test --ffi --match-test "test__DifferentialFuzz__GlobalGrowthMatches" -vv

# Run only the golden vector tests
forge test --ffi --match-test "test__Golden__" -vv

# Run with reduced fuzz iterations to avoid RPC rate limits
FOUNDRY_FUZZ_RUNS=20 forge test --ffi --match-test "test__DifferentialFuzz" -vv
```

### 9.3 Fuzz Run Configuration

Each fuzz iteration calls `vm.rollFork()`, which makes an RPC request. Alchemy's free tier allows ~330 compute units/second.

| Scenario | Recommended `FOUNDRY_FUZZ_RUNS` | Approx. Time |
|----------|-------------------------------|--------------|
| Local development | 20 | ~20 seconds |
| CI pipeline | 50 | ~50 seconds |
| Full coverage | 256 (Forge default) | ~4 minutes |

Use the environment variable rather than modifying `foundry.toml` (which is out of scope).

---

## 10. Scope Rules

**You MUST:**
- Create `test/differential/DifferentialGrowthFork.t.sol`
- Extend `BaseForkTest`
- Use `ffiPython()` from `BaseTest` for all FFI calls
- Use `AngstromAccumulatorConsumer` for on-chain reads (deploy in `setUp()`)
- Use `vm.rollFork()` to change block state
- Pass `data/ran_accumulator.duckdb` as the `--db` argument in all FFI calls
- Include both the fuzz test and golden vector tests
- Use the `onlyForked` modifier on every test function
- Guard `setUp()` with `if (!forked) return;` after `super.setUp()`

**You MUST NOT:**
- Modify any existing Solidity files
- Modify any Python scripts
- Modify `foundry.toml`
- Create new Python code
- Create files outside `test/differential/`

---

## 11. Potential Failure Modes and Debugging

### 11.1 FFI Reverts with No Output

**Cause:** Python venv not activated, or `duckdb`/`eth_abi` not installed.
**Fix:** Run `source .venv/bin/activate` before `forge test --ffi`.

### 11.2 "pool not found" from FFI

**Cause:** Pool ID mismatch. Check that `POOL_HEX` is the full 66-character hex string with `0x` prefix.

### 11.3 Fork RPC Rate Limiting

**Cause:** Too many `vm.rollFork()` calls per second.
**Fix:** Reduce fuzz runs: `FOUNDRY_FUZZ_RUNS=20`.

### 11.4 globalGrowth Mismatch (assertEq fails)

**Most likely cause:** Bug in the pipeline's storage read logic.
**Unlikely cause:** Block reorg (only affects blocks < 100 confirmations deep).
**Debug approach:**

1. Note the failing block number from the test output.
2. Verify manually with `cast`:

```bash
# Compute the storage slot
POOL_ID=0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657
BASE_SLOT=$(cast keccak $(cast abi-encode "f(bytes32,uint256)" $POOL_ID 7))
GROWTH_SLOT=$(python3 -c "print(hex(int('$BASE_SLOT', 16) + 16777216))")

# Read the storage at the failing block
cast storage 0x0000000aa232009084Bd71A5797d089AA4Edfad4 $GROWTH_SLOT \
  --rpc-url https://eth-mainnet.g.alchemy.com/v2/$ALCHEMY_API_KEY \
  --block <FAILING_BLOCK_NUMBER>
```

### 11.5 "Skipping forked test" (Tests Pass but Do Nothing)

**Cause:** `ALCHEMY_API_KEY` not in `contracts/.env`.
**Fix:** Add the key to `.env`.

### 11.6 Consumer Deployment Fails in setUp

**Cause:** Angstrom contract doesn't exist at the fork block.
**This should not happen:** `BLOCK_NUMBER_0` (22,972,937) is Angstrom's genesis block.

### 11.7 Angstrom Upgrade Breaks Slot Derivation

**Cause:** If Angstrom's storage layout changes in the future, the `AngstromAccumulatorConsumer` slot derivation will produce wrong results.
**Scope:** This would require updating `AngstromAccumulatorConsumer.sol`, which is a separate concern outside this test's scope. The test validates historical data, so past blocks remain unaffected.

---

## 12. Storage Slot Derivation (Background)

You do not need to implement this -- the `AngstromAccumulatorConsumer` handles it -- but understanding the derivation helps with debugging.

The on-chain `globalGrowth` for a pool lives at:

```
slot = keccak256(abi.encode(poolId, POOL_REWARDS_SLOT)) + REWARD_GROWTH_SIZE
```

Where:
- `POOL_REWARDS_SLOT = 7` (Angstrom's storage layout)
- `REWARD_GROWTH_SIZE = 16777216` (0x1000000, offset within the `PoolRewards` struct)
- `poolId` = bytes32 pool identifier

The `AngstromAccumulatorConsumer` uses OpenZeppelin's `SlotDerivation.deriveMapping` to compute `keccak256(abi.encode(poolId, 7))`, then adds the `REWARD_GROWTH_SIZE` offset.

---

## 13. Completion Checklist

Before considering the implementation done, verify every item:

- [ ] File exists at `test/differential/DifferentialGrowthFork.t.sol`
- [ ] Contract extends `BaseForkTest`
- [ ] `setUp()` calls `super.setUp()` first
- [ ] `setUp()` returns early with `if (!forked) return;`
- [ ] `setUp()` deploys `AngstromAccumulatorConsumer` with correct constructor args
- [ ] Every test function uses the `onlyForked` modifier
- [ ] Fuzz test bounds `idxSeed` to `[0, datasetLen - 1]`
- [ ] Fuzz test calls `vm.rollFork(blockNumber)` before reading on-chain state
- [ ] Fuzz test casts `bytes32` to `uint256` before comparing: `uint256(offchainGrowth)`
- [ ] FFI args use module syntax: `-m scripts.ran_ffi`
- [ ] FFI args pass `--db data/ran_accumulator.duckdb`
- [ ] FFI args pass `--pool 0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657`
- [ ] Golden vector tests exist for: first block, last block, index 0, midpoint
- [ ] No existing files were modified
- [ ] `forge test --ffi --match-path "test/differential/*" -vv` passes with `ALCHEMY_API_KEY` set
