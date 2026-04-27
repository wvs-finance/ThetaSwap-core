# Senior Developer Review — RAN Oracle Test Suite

**Reviewer:** EngineeringSeniorDeveloper
**Date:** 2026-04-13
**Scope:** 6 test files + `ffiLib.sol`. Code quality only — no security claims.

---

## TL;DR

The suite is **functionally sound and well-targeted** (golden-vector + fuzz + security-edge + integration). TDD discipline is visible (a few tests clearly failed first — revert canaries, arg-order canaries). But it suffers from:

1. **Heavy copy-paste in mock construction** (`new MockBlockNumberAware(BUFFER_CAPACITY); vm.makePersistent(...)` appears 10+ times across one file alone).
2. **Three-naming-convention chaos** (`test__fuzzBTT__`, `test__fuzzDifferential__`, `test__fuzzSecurityEdge__`, `test__SecurityEdge__`, `test__Integration__`, `test__IntegrationSecurityEdge__`, `test__BTT__`, `test__OffChainDifferentialTest__`, `test__OffChainFuzzDifferentialTest__`). No documented policy — a newcomer will not know which prefix to pick for a new test.
3. **FFI per-iteration overhead is real and unnecessary** — `decodeLen(ffiPython(lenArgs()))` is called inside every fuzz body when `n` is invariant across the process lifetime. On 5 runs × 6 tests × ~2 FFI calls each = ~60 Python subprocess spawns minimum, several hundred if `--fuzz-runs` is raised.
4. **Gas-budget `18_000` magic number** duplicated 4 times with no single source of truth.
5. **Mock proliferation is borderline excessive** but each mock has a distinct responsibility — see §5 below for a consolidation proposal.
6. **Stray emacs lockfiles and `~` backups** in `test/_adapters/utils/`, `test/types/`, `test/_adapters/`, `test/_helpers/` — noise that should never land.

Action-items are prioritized by **effort × impact** at the end.

---

## 1. Duplication

### 1.1 Mock-and-persist boilerplate (HIGH impact, LOW effort)

`BlockNumberAwareGrowthObserverLib.diff.t.sol` constructs `MockBlockNumberAware` **10 separate times** in test bodies, each followed by `vm.makePersistent`. This is because some tests need a fresh buffer, but the pattern has no helper:

```solidity
MockBlockNumberAware m = new MockBlockNumberAware(BUFFER_CAPACITY);
vm.makePersistent(address(m));
```

appears at lines 170–171, 186–187, 198–199, 213–214, 221–222, 252–253, 272–273, 286–287, 307–308, 327–328, 346–347, 370–371, 388–389, 428–429. That's **14 occurrences** in one file. Fix:

```solidity
function _freshMock() internal returns (MockBlockNumberAware m) {
    m = new MockBlockNumberAware(BUFFER_CAPACITY);
    vm.makePersistent(address(m));
}
```

Saves ~28 lines and, more importantly, centralizes the persistence contract. If `BUFFER_CAPACITY` ever changes per-test, the helper takes an override.

### 1.2 `vm.warp` + epoch-extraction (MEDIUM impact, LOW effort)

Repeated across `EMAGrowthTransformationLib.diff.t.sol` and `AngstromRANPipeline.diff.t.sol`:

```solidity
uint24 currentEpoch = uint24((block.timestamp >> 6) & 0xFFFFFF);
OraclePack stalePack = OraclePackLibrary.storeOraclePack(
    uint256(currentEpoch - 1), 0, 0, int24(0), uint96(0), int24(0), 0
);
```

4 occurrences. Extract to a shared helper (the existing `_packAtEpoch` in `EMAGrowthTransformationLib.diff.t.sol` does half the job but it's not reused by the integration test).

### 1.3 Dense-buffer-fill loop (MEDIUM impact, LOW effort)

The pattern

```solidity
for (uint256 i; i < N; ++i) {
    vm.roll(startBlock + i);
    vm.warp(startTimestamp + i * 12);
    m.recordObs(block.number, i == 0 ? 0 : 12, (i + 1) * 1e18);
}
```

appears in `test__fuzzDifferential__ObserveAtProductionCadence30MinCoverage`, `test__fuzzDifferential__ObserveAtPostWrapGasStability`, `test__fuzzSecurityEdge__ObserveAtExactOldestBoundaryPostWrap`, `test__fuzzBTT__DescendingBlockOrderingInvariant`, `test__fuzzBTT__ObserveAtMonotonicity`. 5 copies of a synthetic timeline generator. The seed-permuted variant in `test__fuzzSecurityEdge__BinarySearchUnderKeeperSkipPattern` is a legitimate sibling that should live next to it as `_fillKeeperSkip`.

### 1.4 Consecutive-row fork+record pattern (MEDIUM impact, LOW effort)

In `GrowthObservation.diff.t.sol`, three consecutive tests (`GrowthDeltaMatchesRawSubtraction`, `ElapsedBlocksMatchesRawSubtraction`, `ConsecutiveRowsMonotonic`) are **~20-line byte-for-byte duplicates** except for the final assertion block. One `_twoConsecutiveObs(idx)` helper returning `(prev, curr)` collapses ~60 lines to ~20.

---

## 2. Naming conventions

Current prefixes observed:

| Prefix | Count | Files |
|---|---|---|
| `test__fuzzBTT__` | 6 | BlockNumberAware, GrowthToTick |
| `test__fuzzDifferential__` | 6 | GrowthObservation, BlockNumberAware |
| `test__fuzzSecurityEdge__` | 7 | BlockNumberAware, EMA, GrowthToTick |
| `test__SecurityEdge__` | 1 | EMA (non-fuzz) |
| `test__Integration__` | 1 | Pipeline |
| `test__IntegrationSecurityEdge__` | 3 | Pipeline |
| `test__BTT__` | 1 | BlockNumberAware (non-fuzz empty buffer) |
| `test__OffChainDifferentialTest__` | 5 | ConsumerFork |
| `test__OffChainFuzzDifferentialTest__` | 1 | ConsumerFork |

**Problems:**
- `test__OffChainDifferentialTest__First` vs `test__fuzzDifferential__PackRoundTripBitPackingSuccess` — same category (off-chain differential), different convention.
- `test__SecurityEdge__` vs `test__fuzzSecurityEdge__` is a reasonable distinction (non-fuzz vs fuzz) but undocumented.
- `test__IntegrationSecurityEdge__C1_...` uses `C1_` / `C2_` / `I2_` / `D4_` prefixes from a risk-mitigation-map that is not cross-referenced in the test file itself. If that doc goes stale, `D4` becomes archaeological.

**Recommendation:** Adopt a single 3-axis scheme:

```
test_<Category>_<Variant>_<PropertyDescription>
```

Where:
- `Category` ∈ {`Unit`, `Fuzz`, `Fork`, `Integration`}
- `Variant` ∈ {`Diff`, `BTT`, `SecEdge`, `Happy`, `Revert`} (optional)
- `PropertyDescription` ∈ PascalCase assertion summary

Example: `test_Fork_Diff_GlobalGrowthMatchesFirstRow`, `test_Fuzz_BTT_CountSaturatesAtCapacity`, `test_Integration_SecEdge_DescendingGrowthProducesGarbageTick`.

Then risk-map IDs (`C1`, `D4`) go in a NatSpec `/// @dev Mitigates risk map item C1 (zero-anchor)` rather than the test name. This keeps the name semantic and the traceability explicit.

---

## 3. Assertion message quality

### 3.1 Generic strings that don't help debugging

```solidity
assertEq(onchain, row.globalGrowth, "first row mismatch");          // _adapters
assertEq(uint256(obs.blockNumber()), row.blockNumber, "blockNumber"); // types
assertEq(uint256(lat.cumulativeGrowth()), growth, "latest.growth"); // libraries
```

When a CI run fails, `"first row mismatch"` tells the reader nothing. Prefer:

```solidity
assertEq(onchain, row.globalGrowth,
    "globalGrowth(USDC_WETH) @ block != indexer row[0]");
```

The assertion should name **what was compared and where**, not just restate the test name.

### 3.2 Good examples worth copying

`GrowthToTickLib.diff.t.sol` gets this right:
- `"tick floor violated"`
- `"monotonicity violated: larger growth gave smaller tick"`
- `"anchor-scaling invariance drift > 1 tick"`

These name the mathematical property. **Propagate this style** — every `"mismatch"` in the other files should be upgraded to a property name.

### 3.3 `assertEq` on struct-unwrap — poor error output

In `BlockNumberAwareGrowthObserverLib.diff.t.sol`:

```solidity
assertEq(
    GrowthObservation.unwrap(m.latest()),
    GrowthObservation.unwrap(originalLatest),
    "stale record must not modify any field of latest"
);
```

On failure, Forge will print two bytes32 blobs. That tells you nothing about **which of the three packed fields** changed. Consider a custom `_assertGrowthObsEq(actual, expected, label)` helper that unpacks and asserts field-by-field.

---

## 4. Test data setup

### 4.1 Hardcoded constants should be named

- `1000, 1001` as block numbers appears **12 times** across files. Make `uint256 constant SYNTH_BLOCK_A = 1000; SYNTH_BLOCK_B = 1001;` or accept them as parameters.
- `5e30`, `1e30`, `1e18` as growth values are used as "large" and "typical" — name them (`SYNTH_GROWTH_LARGE`, `SYNTH_GROWTH_TYPICAL`).
- `12` seconds for block time is inlined everywhere; BaseForkTest already has `BLOCK_TIME_SECONDS = 12` implicit. Promote to a constant in the pipeline base class.
- `18_000` gas budget: 4 copies, no single constant. Declare `uint256 constant OBSERVE_AT_GAS_BUDGET = 18_000;` with a comment explaining **how it was derived** (binary-search-over-256-entries worst case? measured locally?).

### 4.2 `FIRST_OBSERVATION_TIME_DELTA = 0`

Fine and well-named, but it's defined in **two separate files** (`GrowthObservation.diff.t.sol:15` and `BlockNumberAwareGrowthObserverLib.diff.t.sol:56`). Promote to `ffiLib.sol` or a new `RANTestConstants.sol`.

### 4.3 `DEFAULT_PERIODS` literal is opaque

```solidity
uint96 constant DEFAULT_PERIODS = uint96(100 + (256 << 24) + (1024 << 48) + (4096 << 72));
```

Defined in **two files** with identical values. Needs:
1. De-duplication.
2. A builder helper: `_packPeriods(uint24 spot, uint24 fast, uint24 slow, uint24 eons)`.
3. The literal should reference a spec section in a comment (`// spec §X.Y — minimums`).

---

## 5. Mock contract design

Three mocks exist: `MockBlockNumberAware`, `MockEMABuffer`, `MockRANPipeline`. Are they redundant?

| Mock | Responsibility |
|---|---|
| `MockBlockNumberAware` | Exposes `record`, `observeAt`, `latest`, `oldest`, `count`, `rawAt` for the buffer library |
| `MockEMABuffer` | Same `record`, but exposes `updateGrowthEMA` instead of `observeAt` |
| `MockRANPipeline` | Adds the on-chain consumer dependency + EMA + synthetic record path |

**Verdict:** not redundant in *responsibility*, but redundant in *plumbing*. All three wrap the same `CircularBuffer.Bytes32CircularBuffer` and expose the same `record` entry point. The consolidation I recommend:

```solidity
// Base shared across all three test files
contract MockGrowthBuffer {
    CircularBuffer.Bytes32CircularBuffer internal buffer;
    constructor(uint256 cap) { CircularBuffer.setup(buffer, cap); }
    function recordObs(uint256 bn, uint256 rtd, uint256 cg) external {
        record(buffer, bn, rtd, cg);
    }
    function latest() external view returns (GrowthObservation) { return latestObservation(buffer); }
    function oldest() external view returns (GrowthObservation) { return oldestObservation(buffer); }
    function count() external view returns (uint256) { return observationCount(buffer); }
}

// Specialized per test file — inherits above, adds only the method under test
contract MockWithObserveAt is MockGrowthBuffer { /* observeAtTarget, rawAt */ }
contract MockWithEMA is MockGrowthBuffer { /* runUpdate */ }
contract MockPipeline is MockGrowthBuffer { /* consumer wiring + runEMA + recordFromOnChain */ }
```

One shared base eliminates ~40 lines of duplication without losing per-test clarity. Forge has no problem with mocks inheriting from each other in test files.

**However** — these mocks live in the test files themselves, so the inheritance would force a shared file. That's fine: `test/_helpers/MockGrowthBuffer.sol` is the right home. **Only do this if the suite grows beyond 3 mocks**; at 3, inlined duplication is arguably still cheaper than the import overhead. Rate: **MEDIUM effort, MEDIUM impact** — defer until a 4th mock is needed.

---

## 6. Profile configuration (`foundry.toml [profile.diff]`)

```toml
[profile.diff]
ffi = true
match_path = "test/**/*.diff.t.sol"
no_match_path = "lib/*"
verbosity = 2

[profile.diff.fuzz]
runs = 5

[profile.diff.invariant]
runs = 0
```

**Good:**
- `ffi = true` scoped to the diff profile (not default).
- `match_path` glob correctly captures the `.diff.t.sol` convention.
- `invariant.runs = 0` is explicit — invariants are inappropriate for FFI-heavy tests.

**Problems:**

1. **`runs = 5` is extremely low.** With 5 runs per fuzz test, many property-based assertions (e.g. `test__fuzzBTT__GrowthToTick_Monotonicity`) have almost zero chance of hitting edge cases. This appears to be an FFI-cost concession. Justify it in a comment or raise it for non-FFI tests (see §7).

2. **No `fuzz.seed` pin.** Fuzz tests that use FFI for ground truth are still non-deterministic across CI runs. Pin a seed for the diff profile: `seed = "0x..."`.

3. **`no_match_path = "lib/*"`** — fine, but `lib/**` (doublestar) is the safer glob. Single-star won't catch deeply nested `lib/bunni-v2/src/...`.

4. **No `fail_fast`.** For a differential suite that's intentionally slow, `fail_fast = true` saves CI minutes once one FFI comparison fails.

5. **Verbosity 2 is fine for CI but hides the `console2.log` gas prints** that `BlockNumberAwareGrowthObserverLib.diff.t.sol` adds. Either lift verbosity to 3 (noisy but informative) or delete the `console2.log` lines and migrate to `vm.recordLogs` / forge snapshot for gas regressions.

---

## 7. FFI subprocess overhead

### Current cost per fuzz test iteration

Example: `test__fuzzDifferential__GrowthDeltaMatchesRawSubtraction`:

1. `ffiPython(lenArgs())` → 1 subprocess
2. `ffiPython(rowArgs(vm, idx-1))` → 1 subprocess
3. `ffiPython(rowArgs(vm, idx))` → 1 subprocess

**3 subprocess spawns per fuzz iteration × 5 runs = 15 per test.**

`test__fuzzDifferential__BlockNumberGteBoundary` does **4** per iteration (`lenArgs`, then 3 `rowArgs`).

### Cost reduction options, ranked by ROI

1. **Cache `len` in `setUp`.** The dataset length is a static property of the DuckDB file — it cannot change mid-run. Cache it once:

   ```solidity
   uint256 internal _cachedLen;

   function setUp() public virtual override {
       super.setUp();
       if (!forked) return;
       _cachedLen = decodeLen(ffiPython(lenArgs()));
   }
   ```

   **Savings: ~50% of FFI calls across the suite.** Zero behavioral change.

2. **Use `rangeArgs` to fetch both rows in one call** when a test needs `idx-1` and `idx`. `rangeArgs(vm, idx-1, idx+1)` returns both rows in a single subprocess. The infrastructure already exists in `ffiLib.sol` — just not used for consecutive-pair tests.

   **Savings: another ~33%** on the 3 consecutive-row tests in `GrowthObservation.diff.t.sol`.

3. **Batch-prefetch the entire golden-vector set in `setUp`** for tests that don't need fork rolls. `test__fuzzDifferential__PackRoundTripBitPackingSuccess` only reads one row — it can be re-expressed as an indexed-array lookup against a `setUp`-time fetched range.

   **Savings: all FFI calls for pure-pack tests.** Requires a mini-refactor but pays for itself.

4. **Don't bother:** at `runs = 5`, FFI cost is ~3 s total for the suite, well under CI budget. If `runs` ever climbs to 100+, items 1-3 become mandatory.

**Recommendation:** do item 1 now (trivial), defer 2-3 until fuzz runs increase.

---

## 8. Test organization — are security-edge tests misfiled?

`BlockNumberAwareGrowthObserverLib.diff.t.sol` holds **both** BTT-style property tests AND seven `SecurityEdge` tests. At 444 lines and 17 tests, this file is pushing the limit of what a reviewer can keep in working memory.

**Suggestion:** split by concern:

```
test/libraries/
  BlockNumberAwareGrowthObserverLib.diff.t.sol         (BTT + property tests only)
  BlockNumberAwareGrowthObserverLib.secedge.diff.t.sol (SafeCastLib overflow, wrap boundary, keeper-skip)
```

The `*.secedge.diff.t.sol` naming is speculative — alternatively, colocate with the risk-mitigation-map document. Do not over-split; <100 lines per file is too granular.

`EMAGrowthTransformationLib.diff.t.sol` (3 tests, 103 lines) is correctly sized. `GrowthObservation.diff.t.sol` (6 tests, 159 lines) is correctly sized. `GrowthToTickLib.diff.t.sol` (11 tests, 178 lines) is borderline but the tests are tightly related.

**Verdict:** only `BlockNumberAwareGrowthObserverLib.diff.t.sol` is a candidate for splitting, and only if it grows further. Not urgent.

---

## 9. Dependency coupling

### 9.1 Direct imports from `core/src/libraries/` internals

Tests import and exercise *free functions* (`record`, `observeAt`, `latestObservation`). This is a legitimate coupling — the library API **is** free functions. No issue.

### 9.2 `vm.expectRevert(bytes(""))` is a code smell

Two occurrences:
- `GrowthToTickLib.diff.t.sol:99` (`ZeroAnchorReverts`)
- `GrowthToTickLib.diff.t.sol:139` (`Stage1OverflowReverts`)
- `AngstromRANPipeline.diff.t.sol:162` (`C1_ZeroAnchorRevertsEMA`)

`bytes("")` matches any revert, including "out of gas" or "stack too deep". This couples the test to **anything that reverts**, not to the specific panic. If the library later adds a named error for division-by-zero, these tests won't notice the regression.

**Fix:** use `vm.expectRevert(stdError.divisionError)` (forge-std provides the Panic(0x12) selector) for the divide-by-zero cases. For stage-1 overflow, match the specific `stdError.arithmeticError` panic.

### 9.3 `abi.encodeWithSignature("ObservationExpired(uint32,uint32)", ...)`

```solidity
vm.expectRevert(
    abi.encodeWithSignature("ObservationExpired(uint32,uint32)", oldestBlock - 1, oldestBlock)
);
```

The signature is a **string literal**. If the library ever renames this error or changes its parameter types, the test passes silently (the signature hash just won't match and the revert-matching fails — but a naive reviewer won't catch it).

**Fix:** import the error selector directly:
```solidity
import {ObservationExpired} from "core/src/libraries/BlockNumberAwareGrowthObserverLib.sol";
...
vm.expectRevert(
    abi.encodeWithSelector(ObservationExpired.selector, oldestBlock - 1, oldestBlock)
);
```

Same pattern recommended for `EmptyBuffer()` at lines 291 and 294 of the same file.

---

## 10. TDD discipline — any tests look retrofitted?

Evidence of **genuine TDD** (tests clearly written to fail first):

- `test__IntegrationSecurityEdge__I2_EMAPassesLatestAsCurrentNotAnchor` — canary specifically for an arg-order bug. Mirror-construction pattern is textbook TDD.
- `test__fuzzSecurityEdge__GrowthDeltaWrapsOnDescendingGrowth` — the assertion `expectedWrap = (uint256(1) << 208) - ...` shows the author *derived* the wrap magnitude, didn't just read it off a running contract.
- `test__fuzzSecurityEdge__EMA_FuturePackReverts` — the `bound(...)` on `futureOffset` shows the author thought about `uint24` wrap **before** writing the assertion.
- Both `test__fuzzBTT__RecordMonotonicity_DescendingBlocksSilentlySkipped` and `RecordIdempotence_SameBlockDuplicateSkipped` explicitly capture the **absence** of state change, which is hard to fake retrospectively.

Evidence of potentially **retrofitted** tests:

- `test__fuzzDifferential__ObserveAtFullBufferBinarySearchWorstCase` — the `console2.log` calls and the `assertLt(gasUsed, 18_000, ...)` feel like they were added **after** measuring the gas, not before as a budget. A real TDD sequence would have the budget locked *before* observing the implementation. The `18_000` number is suspicious (not a round power of two, not documented). Ask: was this the spec budget, or the measured budget + 10%?

- `test__fuzzDifferential__ObserveAtProductionCadence30MinCoverage` — same pattern. The `1800` seconds (30-min floor) is a real spec constant and legitimate; the gas budget is not.

**Recommendation:** document gas budgets with a comment explaining their origin:
```solidity
// Budget: 18_000 gas covers binary search over 256 entries (log2(256) = 8 iterations
//         at ~2000 gas each) with a 20% safety margin. Measured baseline: 14_500.
uint256 constant OBSERVE_AT_GAS_BUDGET = 18_000;
```

---

## 11. Gas measurement idiom

The `gasBefore = gasleft(); ...; gasUsed = gasBefore - gasleft();` pattern appears **5 times**. It is:

1. **Not accurate** — `gasleft()` itself costs gas, and the wrapping doesn't account for that.
2. **Not stable** across Forge versions — better to use `vm.snapshot()` + `snapshotGasLastCall()` (Forge ≥ 1.0).
3. **Boilerplate.**

**Recommendation:** migrate to `snapshotGasLastCall`:

```solidity
mock.observeAtTarget(target);
uint256 gasUsed = vm.snapshotGasLastCall("observeAt");
```

This auto-writes to `.forge-snapshots/observeAt.snap` and fails CI on regression without manual `assertLt`. It's a drop-in replacement and kills the boilerplate.

---

## 12. Miscellaneous cleanup

### 12.1 Unused imports

- `BlockNumberAwareGrowthObserverLib.diff.t.sol:6` imports `console2` but only uses it in 3 of 17 tests — fine, but delete if the logs go away per §6.5.
- `AngstromAccumulatorConsumer.fork.diff.t.sol:7` imports `console2` — unused. Delete.
- `AngstromAccumulatorConsumer.fork.diff.t.sol:13-18` imports `minArgs`, `maxArgs`, `rangeArgs`, `decodeRange` — all unused. Delete.
- `GrowthToTickLib.diff.t.sol:5` imports `console2` — unused. Delete.
- `EMAGrowthTransformationLib.diff.t.sol:6` imports `console2` — unused. Delete.

Forge does not warn on unused imports; a `solhint` rule does.

### 12.2 Stray emacs/backup files

```
test/_adapters/AngstromAccumulatorConsumer.fork.diff.t.sol~
test/_adapters/utils/#RanFfiLib.sol#
test/_adapters/utils/RanFfiLib.sol~
test/_helpers/BaseForkTest.t.sol~
test/_helpers/BaseTest.sol (unrelated, but check)
test/types/GrowthObservation.diff.t.sol~
test/types/GrowthObservation.t.sol~
```

Git is already tracking them as untracked (see initial `git status`). These are **emacs auto-save artifacts**; they should be in `.gitignore` (`*~`, `.#*`, `#*#`) and swept from the repo. Do this before any PR.

### 12.3 `test/_adapters/utils/` is empty except for backups

After cleanup, this directory will only contain lockfiles. Either delete the directory or put something meaningful there. The scaffolding implies a planned `RanFfiLib.sol` under `utils/` that was moved to `test/_ffi_utils/ffiLib.sol` — the vestigial folder should die.

### 12.4 `decodeRange` `count` parameter is redundant

In `ffiLib.sol:103-114`:

```solidity
(uint256 count, uint256[] memory blockNumbers, ...) = abi.decode(...);
require(
    count == blockNumbers.length && count == blockTimestamps.length && count == growths.length,
    "decodeRange: count mismatch"
);
```

If all three arrays are guaranteed to be the same length by the Python encoder, `count` is redundant and should be derived from `blockNumbers.length`. Either:
(a) drop `count` from the ABI on the Python side; or
(b) keep the `require` as a defensive check but document that it guards against **Python encoder bugs**, not user input.

This is a micro-point, but it's the kind of thing that trips up readers ("why do we pass length AND arrays?").

### 12.5 `GrowthObservation.t.sol` (non-diff) is 670 bytes

```
test/types/GrowthObservation.t.sol           670 bytes
test/types/GrowthObservation.diff.t.sol     6533 bytes
```

The tiny `.t.sol` likely has 1-2 trivial tests. Check whether it's still meaningful or whether its coverage is subsumed by the diff suite. If subsumed, delete.

---

## Action items — prioritized

### Ship now (trivial, high value)
1. **Delete emacs lockfiles and `*~` backups**; add `*~`, `.#*`, `#*#` to `.gitignore`. (5 min)
2. **Delete unused imports** (console2 × 4, minArgs/maxArgs/rangeArgs/decodeRange in ConsumerFork). (5 min)
3. **Cache `decodeLen(lenArgs())` in `setUp`** — halves FFI calls across the suite. (15 min, zero risk)
4. **Replace `abi.encodeWithSignature` with `.selector` imports** for `ObservationExpired` and `EmptyBuffer`. (10 min)
5. **Extract `_freshMock()` helper** in `BlockNumberAwareGrowthObserverLib.diff.t.sol`. (15 min)

### Ship soon (small effort, real quality win)
6. **Promote constants** (`BLOCK_TIME_SECONDS`, `OBSERVE_AT_GAS_BUDGET`, `FIRST_OBSERVATION_TIME_DELTA`, `DEFAULT_PERIODS`, `SYNTH_BLOCK_A/B`, `SYNTH_GROWTH_*`) to a `RANTestConstants.sol` — eliminate duplication across files. (30 min)
7. **Extract `_twoConsecutiveObs(idx)` helper** in `GrowthObservation.diff.t.sol` — collapse ~60 lines. (20 min)
8. **Adopt single naming convention** (`test_<Category>_<Variant>_<PropertyDescription>`) and rename all 30+ tests. Do this in a single commit labeled "test: unify naming convention". (1 h)
9. **Upgrade generic assertion messages** to property names — especially in the ConsumerFork and GrowthObservation files. (30 min)

### Ship next sprint (medium effort, compounding value)
10. **Migrate gas measurement to `snapshotGasLastCall`** and commit `.forge-snapshots/` — removes boilerplate and catches regressions automatically. (1 h)
11. **Use `rangeArgs` for consecutive-pair tests** — cuts FFI cost by another third. (45 min)
12. **Add `fuzz.seed` to `[profile.diff]`** for reproducibility; consider raising `runs` once FFI is cached. (10 min + CI tuning)
13. **Document `test__IntegrationSecurityEdge__C1/C2/D4/I2_` codes** with a NatSpec `@dev` linking to the risk-mitigation-map scratch file. Otherwise those IDs bit-rot. (20 min)

### Defer (only if scope grows)
14. **Consolidate mocks into `MockGrowthBuffer` base** — wait until a 4th mock arises.
15. **Split `BlockNumberAwareGrowthObserverLib.diff.t.sol`** into BTT + secedge files — only if it grows past 500 lines.
16. **Replace `vm.expectRevert(bytes(""))`** with `stdError.divisionError` / `stdError.arithmeticError` — only if the libraries under test add named errors.

---

## Summary grade

| Dimension | Grade | Notes |
|---|---|---|
| Correctness of approach (diff tests, BTT, security-edge) | A | Textbook structure. |
| Duplication / DRY | C+ | Fixable in under 2 hours. |
| Naming consistency | C− | Three+ conventions, no documented rule. |
| Assertion quality | B | Some excellent, some generic. |
| Mock design | B+ | Borderline proliferation but each mock is justified. |
| TDD discipline | B+ | Most tests are clearly test-first; 2 gas-budget tests look measured-after. |
| FFI efficiency | B | Wastes `lenArgs()` calls but not catastrophic at `runs=5`. |
| Repo hygiene | D | Emacs backup files tracked. Fix immediately. |

**Overall: B.** Substantial, well-organized, evidently written by someone who knows differential testing. The path to A is a half-day of cleanup (action items 1–9) — no architectural changes required.
