# RanFfiLib + Differential Fork Test — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pure-decoder library (`RanFfiLib.sol`) and a differential fork test (`DifferentialGrowthFork.t.sol`) that verifies off-chain globalGrowth samples against on-chain Angstrom state across ~37,678 historical blocks.

**Architecture:** Two files in `test/differential/`. `RanFfiLib.sol` contains a struct and three pure decoder free functions. `DifferentialGrowthFork.t.sol` inherits `BaseForkTest`, contains six `internal` arg-builder helpers that call `ffiPython` and pipe through the decoders, plus six test functions (five golden vectors + one fuzz).

**Tech Stack:** Solidity >=0.8.26, Foundry/Forge (vm.ffi, vm.rollFork, bound), BaseForkTest (fork at block 22,972,937), AngstromAccumulatorConsumer (extsload reader), ran_ffi.py (Python FFI CLI, read-only).

**Process constraint:** NON-NEGOTIABLE — every function is presented to the user for approval before writing. No batch writes. No adjacent additions.

**Spec:** `contracts/.scratch/ran-ffi-lib-design.md`
**FFI guide:** `contracts/docs/guides/differential-fork-test-guide.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `test/differential/RanFfiLib.sol` | Create | Struct, constants, three pure decoder free functions |
| `test/differential/DifferentialGrowthFork.t.sol` | Create | Test contract: setUp, six arg builders, six test functions |

No existing files are modified.

---

## Pre-implementation: Run Notebook for Golden Vector Indices

Before Task 1, the user must run `notebooks/growthGlobal.ipynb` cell 13 to get the hardcoded indices for `FirstNonZero` and `MaxSpike`. These values are populated into Task 6 and Task 7.

```bash
cd contracts
source .venv/bin/activate
jupyter nbconvert --to notebook --execute notebooks/growthGlobal.ipynb --output /tmp/growthGlobal-executed.ipynb
```

Read the "Golden Test Vectors" table from the output. Record:
- `first_nonzero` index → used in Task 6 step 3
- `max_spike` index → used in Task 7 step 3

---

### Task 1: AccumulatorRow struct + constants

**Files:**
- Create: `test/differential/RanFfiLib.sol`

- [ ] **Step 1: Present to user for approval**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

struct AccumulatorRow {
    uint256 blockNumber;
    uint256 blockTimestamp;
    uint256 globalGrowth;
}

string constant RAN_POOL_HEX = "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657";
string constant RAN_DB_PATH  = "data/ran_accumulator.duckdb";
```

- [ ] **Step 2: Write file after approval**

Write the above to `test/differential/RanFfiLib.sol`.

- [ ] **Step 3: Verify it compiles**

Run: `cd contracts && source .venv/bin/activate && forge build`
Expected: compiles with no errors (struct and constants are unused — no warnings expected from Forge).

---

### Task 2: decodeLen

**Files:**
- Modify: `test/differential/RanFfiLib.sol`

- [ ] **Step 1: Present to user for approval**

```solidity
function decodeLen(bytes memory raw) pure returns (uint256 count) {
    (count) = abi.decode(raw, (uint256));
}
```

- [ ] **Step 2: Write function after approval**

Append `decodeLen` to `RanFfiLib.sol` after the constants.

- [ ] **Step 3: Verify it compiles**

Run: `cd contracts && forge build`
Expected: compiles clean.

---

### Task 3: decodeRow

**Files:**
- Modify: `test/differential/RanFfiLib.sol`

- [ ] **Step 1: Present to user for approval**

```solidity
function decodeRow(bytes memory raw) pure returns (AccumulatorRow memory row) {
    (uint256 blockNumber, uint256 blockTimestamp, bytes32 growthBytes) =
        abi.decode(raw, (uint256, uint256, bytes32));
    row = AccumulatorRow({
        blockNumber: blockNumber,
        blockTimestamp: blockTimestamp,
        globalGrowth: uint256(growthBytes)
    });
}
```

- [ ] **Step 2: Write function after approval**

Append `decodeRow` to `RanFfiLib.sol` after `decodeLen`.

- [ ] **Step 3: Verify it compiles**

Run: `cd contracts && forge build`
Expected: compiles clean.

---

### Task 4: decodeRange

**Files:**
- Modify: `test/differential/RanFfiLib.sol`

- [ ] **Step 1: Present to user for approval**

```solidity
function decodeRange(bytes memory raw) pure returns (AccumulatorRow[] memory rows) {
    (
        uint256 count,
        uint256[] memory blockNumbers,
        uint256[] memory blockTimestamps,
        bytes32[] memory growths
    ) = abi.decode(raw, (uint256, uint256[], uint256[], bytes32[]));

    require(
        count == blockNumbers.length
            && count == blockTimestamps.length
            && count == growths.length,
        "decodeRange: count mismatch"
    );

    rows = new AccumulatorRow[](count);
    for (uint256 i; i < count; ++i) {
        rows[i] = AccumulatorRow({
            blockNumber: blockNumbers[i],
            blockTimestamp: blockTimestamps[i],
            globalGrowth: uint256(growths[i])
        });
    }
}
```

- [ ] **Step 2: Write function after approval**

Append `decodeRange` to `RanFfiLib.sol` after `decodeRow`.

- [ ] **Step 3: Verify it compiles**

Run: `cd contracts && forge build`
Expected: compiles clean.

- [ ] **Step 4: Commit RanFfiLib.sol**

```bash
cd contracts && git add test/differential/RanFfiLib.sol
git commit -m "feat(test): add RanFfiLib — struct, constants, pure decoders for differential fork tests"
```

---

### Task 5: Test contract scaffold + setUp + arg builders

**Files:**
- Create: `test/differential/DifferentialGrowthFork.t.sol`

Each arg builder is presented one at a time. The scaffold + setUp comes first.

- [ ] **Step 5a: Present scaffold + setUp to user for approval**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {BaseForkTest} from "anstrong-test/_helpers/BaseForkTest.t.sol";
import {AngstromAccumulatorConsumer} from "core/src/_adapters/AngstromAccumulatorConsumer.sol";
import {IAngstromAuth} from "core/src/interfaces/IAngstromAuth.sol";
import {console2} from "forge-std/console2.sol";
import "anstrong-test/_fork_references/Ethereum.sol" as EthereumForkData;
import {
    AccumulatorRow,
    RAN_POOL_HEX,
    RAN_DB_PATH,
    decodeLen,
    decodeRow,
    decodeRange
} from "./RanFfiLib.sol";

contract DifferentialGrowthForkTest is BaseForkTest {
    AngstromAccumulatorConsumer consumer;

    function setUp() public override {
        super.setUp();
        if (!forked) return;

        consumer = new AngstromAccumulatorConsumer(
            IAngstromAuth(EthereumForkData.AngstromAddresses.ANGSTROM),
            POOL_MANAGER
        );
    }
}
```

- [ ] **Step 5b: Write scaffold after approval**

Write the above to `test/differential/DifferentialGrowthFork.t.sol`.

- [ ] **Step 5c: Verify it compiles**

Run: `cd contracts && forge build`
Expected: compiles clean.

- [ ] **Step 5d: Present _ffiLen to user for approval**

```solidity
function _ffiLen() internal returns (uint256) {
    string[] memory args = new string[](7);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "len";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--db";
    args[6] = RAN_DB_PATH;
    return decodeLen(ffiPython(args));
}
```

- [ ] **Step 5e: Write _ffiLen after approval, verify compile**

- [ ] **Step 5f: Present _ffiRow to user for approval**

```solidity
function _ffiRow(uint256 idx) internal returns (AccumulatorRow memory) {
    string[] memory args = new string[](9);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "row";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--idx";
    args[6] = vm.toString(idx);
    args[7] = "--db";
    args[8] = RAN_DB_PATH;
    return decodeRow(ffiPython(args));
}
```

- [ ] **Step 5g: Write _ffiRow after approval, verify compile**

- [ ] **Step 5h: Present _ffiRowByTs to user for approval**

```solidity
function _ffiRowByTs(uint256 ts) internal returns (AccumulatorRow memory) {
    string[] memory args = new string[](10);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "row-by-ts";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--ts";
    args[6] = vm.toString(ts);
    args[7] = "--db";
    args[8] = RAN_DB_PATH;
    args[9] = "--nearest";
    return decodeRow(ffiPython(args));
}
```

- [ ] **Step 5i: Write _ffiRowByTs after approval, verify compile**

- [ ] **Step 5j: Present _ffiMin to user for approval**

```solidity
function _ffiMin() internal returns (AccumulatorRow memory) {
    string[] memory args = new string[](7);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "min";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--db";
    args[6] = RAN_DB_PATH;
    return decodeRow(ffiPython(args));
}
```

- [ ] **Step 5k: Write _ffiMin after approval, verify compile**

- [ ] **Step 5l: Present _ffiMax to user for approval**

```solidity
function _ffiMax() internal returns (AccumulatorRow memory) {
    string[] memory args = new string[](7);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "max";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--db";
    args[6] = RAN_DB_PATH;
    return decodeRow(ffiPython(args));
}
```

- [ ] **Step 5m: Write _ffiMax after approval, verify compile**

- [ ] **Step 5n: Present _ffiRange to user for approval**

```solidity
function _ffiRange(uint256 from_, uint256 to_) internal returns (AccumulatorRow[] memory) {
    string[] memory args = new string[](11);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "range";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--from";
    args[6] = vm.toString(from_);
    args[7] = "--to";
    args[8] = vm.toString(to_);
    args[9] = "--db";
    args[10] = RAN_DB_PATH;
    return decodeRange(ffiPython(args));
}
```

- [ ] **Step 5o: Write _ffiRange after approval, verify compile**

- [ ] **Step 5p: Commit scaffold + all arg builders**

```bash
cd contracts && git add test/differential/DifferentialGrowthFork.t.sol
git commit -m "feat(test): add DifferentialGrowthForkTest scaffold with FFI arg builders"
```

---

### Task 6: test__OffChainDifferentialTest__First

**Files:**
- Modify: `test/differential/DifferentialGrowthFork.t.sol`

- [ ] **Step 1: Present to user for approval**

```solidity
/// @notice Index 0 — pre-settlement block. globalGrowth should be 0.
function test__OffChainDifferentialTest__First() public onlyForked {
    AccumulatorRow memory row = _ffiRow(0);
    vm.rollFork(row.blockNumber);
    uint256 onchain = consumer.globalGrowth(USDC_WETH);
    assertEq(onchain, row.globalGrowth, "first row mismatch");
}
```

- [ ] **Step 2: Write test after approval**

- [ ] **Step 3: Run test**

Run: `cd contracts && source .venv/bin/activate && FOUNDRY_FUZZ_RUNS=1 forge test --ffi --match-test "test__OffChainDifferentialTest__First" -vv`
Expected: PASS (or "skipping forked test" if no ALCHEMY_API_KEY).

---

### Task 7: test__OffChainDifferentialTest__Last

**Files:**
- Modify: `test/differential/DifferentialGrowthFork.t.sol`

- [ ] **Step 1: Present to user for approval**

```solidity
/// @notice Last row — most recent sample.
function test__OffChainDifferentialTest__Last() public onlyForked {
    uint256 n = _ffiLen();
    AccumulatorRow memory row = _ffiRow(n - 1);
    vm.rollFork(row.blockNumber);
    uint256 onchain = consumer.globalGrowth(USDC_WETH);
    assertEq(onchain, row.globalGrowth, "last row mismatch");
}
```

- [ ] **Step 2: Write test after approval**

- [ ] **Step 3: Run test**

Run: `cd contracts && source .venv/bin/activate && FOUNDRY_FUZZ_RUNS=1 forge test --ffi --match-test "test__OffChainDifferentialTest__Last" -vv`
Expected: PASS.

---

### Task 8: test__OffChainDifferentialTest__FirstNonZero

**Files:**
- Modify: `test/differential/DifferentialGrowthFork.t.sol`

**Prerequisite:** Hardcoded index from notebook EDA (cell 13, `first_nonzero` row). Replace `FIRST_NONZERO_IDX` with the actual value.

- [ ] **Step 1: Present to user for approval**

```solidity
/// @notice First block where globalGrowth > 0 (first Angstrom settlement).
/// @dev Index from notebooks/growthGlobal.ipynb cell 13.
function test__OffChainDifferentialTest__FirstNonZero() public onlyForked {
    uint256 idx = FIRST_NONZERO_IDX; // hardcoded from notebook EDA
    AccumulatorRow memory row = _ffiRow(idx);
    assertTrue(row.globalGrowth > 0, "expected non-zero growth");
    vm.rollFork(row.blockNumber);
    uint256 onchain = consumer.globalGrowth(USDC_WETH);
    assertEq(onchain, row.globalGrowth, "first nonzero mismatch");
}
```

Where `FIRST_NONZERO_IDX` is a `uint256 constant` declared at contract level, populated from the notebook output.

- [ ] **Step 2: Write test after approval (with actual index)**

- [ ] **Step 3: Run test**

Run: `cd contracts && source .venv/bin/activate && FOUNDRY_FUZZ_RUNS=1 forge test --ffi --match-test "test__OffChainDifferentialTest__FirstNonZero" -vv`
Expected: PASS.

---

### Task 9: test__OffChainDifferentialTest__MaxSpike

**Files:**
- Modify: `test/differential/DifferentialGrowthFork.t.sol`

**Prerequisite:** Hardcoded index from notebook EDA (cell 13, `max_spike` row). Replace `MAX_SPIKE_IDX` with the actual value.

- [ ] **Step 1: Present to user for approval**

```solidity
/// @notice Block with the largest single-stride growth delta.
/// @dev Index from notebooks/growthGlobal.ipynb cell 13.
function test__OffChainDifferentialTest__MaxSpike() public onlyForked {
    uint256 idx = MAX_SPIKE_IDX; // hardcoded from notebook EDA
    AccumulatorRow memory row = _ffiRow(idx);
    vm.rollFork(row.blockNumber);
    uint256 onchain = consumer.globalGrowth(USDC_WETH);
    assertEq(onchain, row.globalGrowth, "max spike mismatch");
}
```

Where `MAX_SPIKE_IDX` is a `uint256 constant` declared at contract level, populated from the notebook output.

- [ ] **Step 2: Write test after approval (with actual index)**

- [ ] **Step 3: Run test**

Run: `cd contracts && source .venv/bin/activate && FOUNDRY_FUZZ_RUNS=1 forge test --ffi --match-test "test__OffChainDifferentialTest__MaxSpike" -vv`
Expected: PASS.

---

### Task 10: test__OffChainDifferentialTest__Midpoint

**Files:**
- Modify: `test/differential/DifferentialGrowthFork.t.sol`

- [ ] **Step 1: Present to user for approval**

```solidity
/// @notice Midpoint index — spot check the middle of the dataset.
function test__OffChainDifferentialTest__Midpoint() public onlyForked {
    uint256 n = _ffiLen();
    uint256 mid = n / 2;
    AccumulatorRow memory row = _ffiRow(mid);
    vm.rollFork(row.blockNumber);
    uint256 onchain = consumer.globalGrowth(USDC_WETH);
    assertEq(onchain, row.globalGrowth, "midpoint mismatch");
}
```

- [ ] **Step 2: Write test after approval**

- [ ] **Step 3: Run test**

Run: `cd contracts && source .venv/bin/activate && FOUNDRY_FUZZ_RUNS=1 forge test --ffi --match-test "test__OffChainDifferentialTest__Midpoint" -vv`
Expected: PASS.

---

### Task 11: test__OffChainDifferentialTest__GlobalGrowthMatches (fuzz)

**Files:**
- Modify: `test/differential/DifferentialGrowthFork.t.sol`

- [ ] **Step 1: Present to user for approval**

```solidity
/// @notice Differential fuzz test — any row in the dataset.
function test__OffChainDifferentialTest__GlobalGrowthMatches(uint256 idxSeed) public onlyForked {
    uint256 n = _ffiLen();
    require(n > 0, "empty dataset");
    uint256 idx = bound(idxSeed, 0, n - 1);

    AccumulatorRow memory row = _ffiRow(idx);
    vm.rollFork(row.blockNumber);
    uint256 onchain = consumer.globalGrowth(USDC_WETH);
    assertEq(onchain, row.globalGrowth, "globalGrowth mismatch");
}
```

- [ ] **Step 2: Write test after approval**

- [ ] **Step 3: Run fuzz test (limited iterations)**

Run: `cd contracts && source .venv/bin/activate && FOUNDRY_FUZZ_RUNS=20 forge test --ffi --match-test "test__OffChainDifferentialTest__GlobalGrowthMatches" -vv`
Expected: PASS (20 fuzz iterations, each rolls fork to a different block).

- [ ] **Step 4: Commit all test functions**

```bash
cd contracts && git add test/differential/DifferentialGrowthFork.t.sol
git commit -m "feat(test): add 6 differential fork tests — 5 golden vectors + 1 fuzz"
```

---

### Task 12: Full suite run

- [ ] **Step 1: Run all differential tests together**

Run: `cd contracts && source .venv/bin/activate && FOUNDRY_FUZZ_RUNS=20 forge test --ffi --match-path "test/differential/*" -vv`
Expected: all 6 tests PASS.

- [ ] **Step 2: Run full test suite to check for regressions**

Run: `cd contracts && source .venv/bin/activate && forge test --ffi -vv`
Expected: no regressions in existing tests.
