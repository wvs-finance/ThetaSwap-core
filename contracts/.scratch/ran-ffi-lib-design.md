# RanFfiLib Design — Differential Fork Test FFI Decoder Library

**Date:** 2026-04-11
**Status:** APPROVED (post-review rev 1)
**Deliverables:** `test/differential/RanFfiLib.sol` + `test/differential/DifferentialGrowthFork.t.sol`
**Depends on:** `test/_helpers/BaseTest.sol` (ffiPython), `src/_adapters/AngstromAccumulatorConsumer.sol`, `scripts/ran_ffi.py` (read-only)
**Reviewed by:** Reality Checker, Solidity Smart Contract Engineer (2026-04-11)

---

## 1. File, Struct, and Constants

One new file: `test/differential/RanFfiLib.sol`.

### Struct

```
AccumulatorRow {
    uint256 blockNumber
    uint256 blockTimestamp
    uint256 globalGrowth
}
```

All fields are `uint256` — matching the raw ABI decode output with zero narrowing casts. This eliminates silent truncation risk flagged by both reviewers. Downstream consumers (e.g., `GrowthObservation`) are responsible for their own narrowing when they ingest these values.

### Constants

- `RAN_POOL_HEX`: `"0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657"` (USDC/WETH pool ID)
- `RAN_DB_PATH`: `"data/ran_accumulator.duckdb"`

Both baked in — fixed for the entire differential test suite.

---

## 2. Free Functions — Pure Decoders

Three `pure` free functions taking `bytes memory` (the raw output from `ffiPython`) and returning typed values:

| Function | Input ABI shape | Returns |
|----------|----------------|---------|
| `decodeLen(bytes memory)` | `abi.encode(uint256)` | `uint256` |
| `decodeRow(bytes memory)` | `abi.encode(uint256, uint256, bytes32)` | `AccumulatorRow` |
| `decodeRange(bytes memory)` | `abi.encode(uint256, uint256[], uint256[], bytes32[])` | `AccumulatorRow[]` |

`decodeRow` serves `row`, `min`, `max`, and `row-by-ts` — all share the same ABI shape. Inside, it `abi.decode`s `(uint256, uint256, bytes32)` and casts `bytes32 -> uint256` for `globalGrowth`. No narrowing casts — all fields stay `uint256`.

`decodeRange` validates that `count` matches the actual array lengths before iterating: `require(count == blockNumbers.length && count == blockTimestamps.length && count == globalGrowths.length)`. The Python API enforces a hard cap of 1,000 rows per `range` call — exceeding this causes a Python-side `QueryError` before any ABI encoding occurs.

---

## 3. Arg Builders on the Test Contract

The differential fork test contract inherits `BaseForkTest` (which gives it `ffiPython`). Six `internal` helper methods build the `string[]` args array, call `ffiPython`, and pipe through the matching decoder:

| Helper | FFI subcommand | Decoder |
|--------|---------------|---------|
| `_ffiLen()` | `len` | `decodeLen` |
| `_ffiRow(uint256 idx)` | `row` | `decodeRow` |
| `_ffiRowByTs(uint256 ts)` | `row-by-ts --nearest` | `decodeRow` |
| `_ffiMin()` | `min` | `decodeRow` |
| `_ffiMax()` | `max` | `decodeRow` |
| `_ffiRange(uint256 from, uint256 to)` | `range` | `decodeRange` |

Each uses `RAN_POOL_HEX` and `RAN_DB_PATH` from the library. Test body reads:

```
AccumulatorRow memory row = _ffiRow(idx);
vm.rollFork(row.blockNumber);
uint256 onchain = consumer.globalGrowth(USDC_WETH);
assertEq(onchain, row.globalGrowth);
```

---

## 4. Test Functions

All tests share the `test__OffChainDifferentialTest__` prefix. All use the `onlyForked` modifier.

| Test function | Vector source |
|---|---|
| `test__OffChainDifferentialTest__First` | idx 0, pre-settlement, growth == 0 |
| `test__OffChainDifferentialTest__Last` | idx n-1, most recent sample |
| `test__OffChainDifferentialTest__FirstNonZero` | Hardcoded index from notebook EDA (first row where growth > 0) |
| `test__OffChainDifferentialTest__MaxSpike` | Hardcoded index from notebook EDA (largest single-stride growth delta) |
| `test__OffChainDifferentialTest__Midpoint` | idx n/2 |
| `test__OffChainDifferentialTest__GlobalGrowthMatches(uint256 idxSeed)` | Fuzz: any row via bound(idxSeed, 0, n-1) |

`FirstNonZero` and `MaxSpike` use hardcoded indices derived from `notebooks/growthGlobal.ipynb` cell 13. The notebook's EDA already identifies these vectors — searching at runtime wastes FFI subprocess calls and risks missing the target if the cap is too low. The hardcoded indices are populated by running the notebook once before implementation and reading the output.

Golden vector source: `notebooks/growthGlobal.ipynb` cell 13 (EDA-derived test vectors).

---

## 5. Implementation Process

NON-NEGOTIABLE: every function is implemented one at a time following TDD + type-driven development.

1. Present the function signature and body to the user
2. User approves or requests changes
3. Write the approved function
4. Run `forge test` (or `forge build` for non-test code) targeting that function
5. Verify green before presenting the next function

No batch writes. No adjacent additions. Dependency order:

1. `AccumulatorRow` struct + constants
2. `decodeLen`
3. `decodeRow`
4. `decodeRange`
5. Arg builders: `_ffiLen`, `_ffiRow`, `_ffiRowByTs`, `_ffiMin`, `_ffiMax`, `_ffiRange` (one at a time)
6. Test functions: `First`, `Last`, `FirstNonZero`, `MaxSpike`, `Midpoint`, `GlobalGrowthMatches` (one at a time)

---

## Scope Rules

**MUST NOT modify:**
- Any existing Solidity files
- Any Python scripts
- `foundry.toml`

**Creates:**
- `test/differential/RanFfiLib.sol`
- `test/differential/DifferentialGrowthFork.t.sol`

Both files in `test/differential/` — no files created outside this directory.
