# Final Security Audit — RAN Oracle Test Suite

**Reviewer:** Blockchain Security Auditor
**Date:** 2026-04-13
**Scope:** 48 tests across 6 files + `ffiLib.sol` + 5 libraries under test
**Ground rule:** This report only lists adversarial surface **not already flagged** in:
- `diff-tests-review-round2.md` (observer + growth-to-tick)
- `ema-test-review.md` (EMA library)
- `integration-review-and-flaws.md` (P0s F-01..F-06, P1s F-07..F-14)
- `security-edge-cases-growth-observer.md`, `security-edge-cases-growth-to-tick.md`, `security-edge-cases-ema-transformation.md`

F-01 is now fixed (FuturePack guard in `EMAGrowthTransformationLib.sol:53-55`, tested at
`EMAGrowthTransformationLib.diff.t.sol:84-101`). **F-02, F-03, F-04, F-05, F-06 remain unfixed and
the test suite does not cover them as guards — only as documented-behavior witnesses.**

Findings below are ordered by severity. Each finding includes a concrete attack scenario / silent-
miscomputation window, the exact test artifact that creates false confidence, and a specific
remediation. No finding in this report duplicates prior audits.

---

## Summary

| ID   | Severity | File                                                    | Class                                                  |
|------|----------|---------------------------------------------------------|--------------------------------------------------------|
| X-01 | CRITICAL | all forked suites                                       | onlyForked silent skip hides 38 of 48 tests in CI      |
| X-02 | CRITICAL | `GrowthObservation.diff.t.sol` test 6 (BlockNumberGteBoundary) | Fuzz collides on uint32 cast, tautological assertion |
| X-03 | HIGH     | `GrowthToTickLib.diff.t.sol` (Stage1OverflowReverts)    | `vm.expectRevert(bytes(""))` matches too broadly       |
| X-04 | HIGH     | `AngstromAccumulatorConsumer.fork.diff.t.sol`           | No cross-pool / wrong-pool-id isolation canary         |
| X-05 | HIGH     | `BlockNumberAwareGrowthObserverLib.diff.t.sol` test 16  | BinarySearchUnderKeeperSkipPattern predicate is weaker than correctness claim |
| X-06 | HIGH     | `AngstromRANPipeline.diff.t.sol` (I2 mirrored canary)   | Asserts only inequality; a constant output passes      |
| X-07 | HIGH     | `GrowthObservation.diff.t.sol` (GrowthDeltaMatchesRawSubtraction) | Range `[1, n-1]` excludes anchor boundary            |
| X-08 | HIGH     | `ffiLib.sol` + all FFI-dependent tests                  | No cache-invalidation / freshness check on DuckDB      |
| X-09 | HIGH     | `GrowthToTickLib.diff.t.sol` (NearMaxSqrtPriceCliff)    | try/catch swallows inner reverts that belong to other stages |
| X-10 | HIGH     | `AngstromRANPipeline.diff.t.sol` (D4)                   | Expected-wrap equality hard-codes the bug as spec      |
| X-11 | MEDIUM   | `BlockNumberAwareGrowthObserverLib.diff.t.sol` test 8   | `oldestBlock - 1` can underflow when startBlock is low |
| X-12 | MEDIUM   | `EMAGrowthTransformationLib.diff.t.sol` test 3 (FuturePack) | Guards the fix but not the downstream wrap magnitude |
| X-13 | MEDIUM   | `GrowthToTickLib.diff.t.sol` (AnchorScalingInvariance)  | 1-tick drift tolerance hides a full-bit precision loss |
| X-14 | MEDIUM   | `AngstromRANPipeline.diff.t.sol` (HappyPath)            | `expectedGrowthTick` assertion uses library-under-test |
| X-15 | MEDIUM   | `BlockNumberAwareGrowthObserverLib.diff.t.sol` (RelativeTimeDeltaInRangeRoundTrips) | Does not use `vm.roll` — `recordObs` skip logic masked by test-controlled block numbers |
| X-16 | MEDIUM   | `GrowthObservation.diff.t.sol` (ConsecutiveRowsMonotonic) | 4 assertions derived from 2 row comparisons (diluted coverage) |
| X-17 | MEDIUM   | `EMAGrowthTransformationLib.diff.t.sol` (InsufficientObservations) | `count == 1` assertion missing the `count == 0` branch for post-wrap empty case |
| X-18 | MEDIUM   | `AngstromAccumulatorConsumer.fork.diff.t.sol`           | `MAX_SPIKE_IDX = 27677` is a hard-coded index — dataset drift silently invalidates |
| X-19 | MEDIUM   | `BlockNumberAwareGrowthObserverLib.diff.t.sol` test 2   | Uses `vm.warp(startTimestamp + ...)` where `startTimestamp` is fork-time — timestamp skew silently alters `relTimeDelta` range |
| X-20 | MEDIUM   | `GrowthObservation.diff.t.sol` (PackRoundTripBitPacking) | Asserts three fields individually; misses cross-field bit leakage at boundaries |
| X-21 | LOW      | `ffiLib.sol`                                            | `decodeRange` length check is `require`, not a custom error — bad DX on tool decode failures |
| X-22 | LOW      | all files                                               | Zero use of `vm.label` — trace output in fuzz failures is unreadable |
| X-23 | LOW      | `AngstromRANPipeline.diff.t.sol`                        | `_packAtEpoch` not defined in integration file; `storeOraclePack` called with magic literals inline |
| X-24 | LOW      | `MockBlockNumberAware.rawAt`                            | Test-only leak of storage pointer semantics; could diverge from library |

**Unfixed P0 coverage gap (from prior audits):** F-02, F-03, F-04, F-05, F-06 remain uncovered by
any test as *guards*. The suite contains **witnesses** of the undefined behavior (tests D4 of
integration, `GrowthDeltaWrapsOnDescendingGrowth` of observer). Those tests **calcify the bug as
specification** rather than flag it as a defect — see X-10.

---

## CRITICAL

### X-01 — `onlyForked` silently skips 38 of 48 tests without ALCHEMY_API_KEY

**Severity:** CRITICAL
**Location:**
- `contracts/test/_helpers/BaseForkTest.t.sol:25-32`
- Every `onlyForked` test in `AngstromAccumulatorConsumer.fork.diff.t.sol` (6/6),
  `GrowthObservation.diff.t.sol` (6/6), `BlockNumberAwareGrowthObserverLib.diff.t.sol` (17/17),
  `AngstromRANPipeline.diff.t.sol` (5/5) — **34 of 48 tests total**

**Description:** `onlyForked` wraps the test body in `if (forked) { _; return; } console2.log(...)`.
If `ALCHEMY_API_KEY` is missing, `BaseTest.setUp()` catches the `vm.envString` revert, logs
"skipping forked test", and the test method returns green without asserting anything. Forge reports
it as a pass.

Prior audit `diff-tests-review-round2.md` (SS-1) flagged this for the observer suite. It remains
unfixed and **it applies to the entire fork-grounded surface**, including the integration pipeline
and the bit-packing tests (`GrowthObservation.diff.t.sol`) that do not actually need a fork —
tests 1-7 of that file only use FFI decoded data and `vm.rollFork`, but 5 of them do not read any
chain state and could run in mock mode.

**Attack / CI scenario:**
1. Developer deletes `ALCHEMY_API_KEY` from `.env` to debug a local issue, forgets to restore.
2. CI job without the key reports 34 green tests, asserts nothing.
3. A refactor that breaks `AngstromAccumulatorConsumer.globalGrowth` passes CI.
4. Staging deploys. Production drains.

**Assertion that gives false confidence:** every `assertEq` / `assertTrue` inside an `onlyForked`
body. The logs emit `console2.log("skipping forked test")` — not visible in CI dashboards unless
verbose.

**Remediation:**
1. Replace the silent-skip with `vm.skip(true)` (forge-std 1.9+). This produces a distinct
   `[SKIP]` result in the terminal and CI, not a `[PASS]`.
2. For `GrowthObservation.diff.t.sol` tests that consume FFI data but do not read chain state
   (tests 1, 5 — `PackRoundTripBitPacking`, `RealObservationsAreNonZero`), remove `onlyForked`
   and make them run against the DuckDB dataset without a fork.
3. Require `ALCHEMY_API_KEY` in CI as a hard prerequisite — fail the job early on missing.

---

### X-02 — `BlockNumberGteBoundary` fuzz assertion is tautological at low row indices

**Severity:** CRITICAL
**Location:** `contracts/test/types/GrowthObservation.diff.t.sol:130-157`

**Description:** The test fuzzes `idxSeed`, bounds it to `[1, n-2]`, then reads rows at
`idx-1`, `idx`, `idx+1`. It casts each `blockNumber` to `uint32` and asserts lt/gte relationships.

The problem: **`uint32(targetRow.blockNumber)` can collide with `uint32(belowRow.blockNumber)` if
`targetRow.blockNumber - belowRow.blockNumber` is a multiple of `2^32`**. This is probabilistically
zero for the current ETH mainnet dataset (BLOCK_NUMBER_0 is ~2025-era, far below uint32.max), but
it becomes a real silent-success path once RAN backfills deeper historical or synthetic datasets.

More importantly: the assertions `below.blockNumberLt(target)` and `above.blockNumberGte(target)`
are *tautologies* given the indexing contract of the DuckDB dataset (rows are sorted by block
number ascending by construction). The test cannot fail unless the DuckDB loader returns out-of-
order rows — at which point **every other FFI-grounded test also breaks** and this one is not
diagnostic.

**Silent-miscomputation window:** A refactor that introduces a bug in `blockNumberGte` or
`blockNumberLt` (e.g., flipping `>=` to `>`) would fail at **exact boundary** comparisons — which
this test **never constructs** because `target = uint32(targetRow.blockNumber)` and the test only
ever compares obs at `targetRow.blockNumber` itself (guaranteed `==`, which `blockNumberGte`
returns true for correctly by construction).

The test never compares `atTarget.blockNumberGte(target + 1)` or `target - 1`. The off-by-one
regime — where `>=` vs `>` would actually differ — is not exercised.

**Remediation:**
```solidity
// Add explicit off-by-one boundary assertions that actually discriminate >= from >
assertTrue(atTarget.blockNumberGte(target), "== equality must return true for >=");
assertFalse(atTarget.blockNumberGte(target + 1), ">= must return false one above");
assertTrue(atTarget.blockNumberLt(target + 1), "< must return true one above");
assertFalse(atTarget.blockNumberLt(target), "< must return false at equality");
```

---

## HIGH

### X-03 — `Stage1OverflowReverts` uses `vm.expectRevert(bytes(""))`

**Severity:** HIGH
**Location:** `contracts/test/libraries/GrowthToTickLib.diff.t.sol:128-141`

**Description:** The test configures inputs expected to trigger `FullMath.mulDiv` overflow, then
uses `vm.expectRevert(bytes(""))` which matches **any revert data, including empty revert data**.
`FullMath.mulDiv`'s overflow path uses `require(denominator > prod1, ...)` which reverts with
empty data in the current v4-core — so this test happens to pass, **but it will also pass if a
regression introduces a different revert path** (e.g., downstream `sqrt` returning 0 causing a
`TickMath.InvalidSqrtPrice(0)` revert, which is a structured error selector, which does not match
`bytes("")` — actually it *doesn't* match — but worse, if the implementation were refactored to
revert with a custom error, the test fails spuriously).

Worse: **`vm.expectRevert(bytes(""))` also matches Panic(0x11) from arithmetic overflow**, which
is the semantically different failure mode that F-02 documents. The test cannot distinguish
"FullMath overflow" from "arithmetic panic" from "custom named error" — all three pass.

**Prior audit `diff-tests-review-round2.md` item 4 flagged this for the zero-anchor tests**, but
the same defect repeats in this `Stage1Overflow` test and in the zero-anchor revert in
`GrowthToTickLib_ZeroAnchorReverts`, and in integration test `C1_ZeroAnchorRevertsEMA`
(`AngstromRANPipeline.diff.t.sol:162`).

**Remediation:** Pin the expected revert data:
```solidity
vm.expectRevert(stdError.arithmeticError); // Panic 0x11 for overflow
// or, after F-02 fix:
vm.expectRevert(GrowthToTickLib.Stage1Overflow.selector);
```

---

### X-04 — No wrong-pool-id / cross-pool isolation canary

**Severity:** HIGH
**Location:** `contracts/test/_adapters/AngstromAccumulatorConsumer.fork.diff.t.sol` (all 6 tests)

**Description:** Every test in this file reads `consumer.globalGrowth(USDC_WETH)` — one hardcoded
pool id. `globalGrowth` derives a storage slot via
`bytes32(POOL_REWARDS_SLOT).deriveMapping(PoolId.unwrap(poolId))`
(`AngstromAccumulatorConsumer.sol:43-44`). A bug in `deriveMapping` that **misuses the pool id**
(e.g., clips to uint160, uses `keccak256(poolId)` instead of `keccak256(poolId, slot)`,
byte-reverses the key) would go undetected because:

1. The FFI dataset is captured for `USDC_WETH` only (see `ffiLib.sol:13 RAN_POOL_HEX`).
2. The assertion compares on-chain read to the off-chain row for the *same* pool.
3. If `globalGrowth(USDC_WETH)` silently read `globalGrowth(WETH_USDT)` slot instead
   (because the derivation is wrong but consistently wrong), the on-chain value would be the
   *wrong pool's* growth — and the test would still pass **only if** the off-chain dataset was
   generated with the same buggy derivation.

More practical attack: an adversary pushes an Angstrom upgrade that changes `POOL_REWARDS_SLOT`
from 7 to 8 (F-12 in prior audit). `AngstromAccumulatorConsumer` silently reads slot 7 for a
token that happens to live there, returning **arbitrary attacker-controlled data**. No test
in the suite detects this because all tests read a value derived from the *same* slot constant.

**Assertion that gives false confidence:** `assertEq(onchain, row.globalGrowth, ...)` — the right-
hand side is also computed from the same Angstrom contract (just read from a DuckDB snapshot
indexed by the Python FFI, which calls the same RPC). Both sides drift together on an Angstrom
upgrade.

**Remediation:**
1. Add a **dual-pool canary test**: read `globalGrowth(WETH_USDT)`, assert it differs from
   `globalGrowth(USDC_WETH)`, and assert both match independently-sourced off-chain values.
2. Add a **wrong-pool-id negative test**: compute `PoolId.wrap(bytes32(uint256(1)))` and assert
   `globalGrowth` returns 0 (uninitialized slot).
3. Add a **storage-slot layout smoke test**: assert `consumer.lastBlockUpdated()` is non-zero
   (sanity check that `LAST_BLOCK_CONFIG_STORE_SLOT = 3` is still valid). If this read returns
   0 or a garbage address for `configStore()`, the layout constant is wrong.

---

### X-05 — `BinarySearchUnderKeeperSkipPattern` predicate is weaker than the correctness claim

**Severity:** HIGH
**Location:** `contracts/test/libraries/BlockNumberAwareGrowthObserverLib.diff.t.sol:387-419`

**Description:** The test asserts `result.blockNumber() <= target` and then scans the buffer for
any stored block `bn_i` with `result.blockNumber() < bn_i <= target` (calling `fail()` if found).

The scan logic is correct in principle but has a **silent failure mode when the result is the
oldest observation**: if a bug caused `observeAt` to always return `oldest()` regardless of target,
the scan's predicate `bn_i > result.blockNumber() && bn_i <= target` would still flag it *only if*
`target > oldest.blockNumber()`. For adversarial `gapSeed` values that cause `target` to land
exactly on `oldestBlock`, the scan finds no violating row, and the test passes with `result =
oldest`. This is acceptable in the "target equals oldest" degenerate case, but the fuzz
distribution from `bound(gapSeed, oldestBlock, newestBlock)` has a probability `1/(newest-oldest)`
of landing on `oldestBlock` — at least one fuzz run in 256 typical runs.

**More importantly:** the test uses `gasSeed` **both** as the target seed and as the gap-pattern
seed. The same seed drives both the storage layout and the query point. A fuzz run with
`gapSeed = 0` produces `gap = 1 + 0 = 1` everywhere **and** `target = oldestBlock` (via the bound
clamp on the low end). The test is self-correlated.

**Remediation:**
```solidity
// Decouple the gap seed from the target seed, add strict-inequality assertion:
function test__fuzzSecurityEdge__BinarySearchUnderKeeperSkipPattern(
    uint256 gapSeed,
    uint256 targetSeed  // separate seed
) public onlyForked {
    ...
    // Assert the result is STRICTLY the largest bn <= target (not just "some" bn <= target):
    uint32 expectedResult = 0;
    for (uint256 i; i < c; ++i) {
        uint32 bn_i = m.rawAt(i).blockNumber();
        if (bn_i <= target && bn_i > expectedResult) expectedResult = bn_i;
    }
    assertEq(result.blockNumber(), expectedResult, "observeAt returned non-maximal observation");
}
```

---

### X-06 — I2 mirrored canary asserts only inequality, not direction

**Severity:** HIGH
**Location:** `contracts/test/integration/AngstromRANPipeline.diff.t.sol:199-220`

**Description:** The test records `(1e30, 5e30)` in one pipeline and `(5e30, 1e30)` in a mirror,
then asserts `OraclePack.unwrap(packA) != OraclePack.unwrap(packB)`. This is intended to be the
F-03 / I-2 canary — if someone swaps the `growthToTick(latest, oldest)` argument order, the two
packs should differ.

**The assertion is too weak.** Two counterexamples pass this test **while the bug is present**:

1. **Constant-output regression.** If a refactor breaks `updateGrowthEMA` such that it always
   returns a zeroed pack (or any pack that doesn't depend on growth), both pipelines return
   identical packs — the test **correctly fails**. OK.

2. **Arg-order swap regression.** Both `growthToTick(5e30, 1e30)` and `growthToTick(1e30, 5e30)`
   return valid but opposite-sign ticks. `packA` and `packB` are indeed different — the test
   passes. **But the bug is present.** The original pipeline's intent was `growthTick > 0`; after
   the swap it is `< 0`. The test cannot detect this because `!=` doesn't care about direction.

3. **Same-sign output regression.** If `growthToTick` were replaced with `abs(growthToTick(a,b))`,
   both pipelines would return ticks of the same magnitude and sign. Packs still differ if any
   other field is stamped from the growth magnitude (e.g., `_lastTick`). Test passes, bug shipped.

**Remediation:**
```solidity
// Assert the direction of the tick advancement, not just inequality.
// packA should have positive tick movement, packB should have negative.
int24 spotA = packA.spotEMA(); // or whatever the decoded EMA field is
int24 spotB = packB.spotEMA();
assertGt(spotA, 0, "ascending growth must produce positive EMA");
assertLt(spotB, 0, "descending growth must produce negative EMA (F-03 canary)");
```
Or, even stronger, **assert the sum is zero or near-zero** (sign symmetry property from
`GrowthToTickLib.diff.t.sol:123-125`):
```solidity
assertLe(abs(spotA + spotB), 1, "sign symmetry violated under argument swap");
```

---

### X-07 — `GrowthDeltaMatchesRawSubtraction` fuzz bound excludes anchor

**Severity:** HIGH
**Location:** `contracts/test/types/GrowthObservation.diff.t.sol:38-61`

**Description:** `bound(idxSeed, 1, n - 1)` — idx=0 excluded. The test computes `expectedDelta =
currRow.globalGrowth - prevRow.globalGrowth`, always positive given the dataset's monotonicity.

**The gap:** The test never exercises `growthDelta` with **the anchor as `later` and a newer obs
as `earlier`** — i.e., the misordered case that F-11 (prior audit) names as positional ambiguity.
The function signature is `growthDelta(earlier, later) returns later.cg - earlier.cg`; an inverted
caller computes `growthDelta(later, earlier) = earlier.cg - later.cg` which wraps to `2^208 -
delta`. This test's assertion `prev.growthDelta(curr) == expectedDelta` pins the correct-order
case but never the inverted case.

Note: `GrowthDeltaWrapsOnDescendingGrowth` in the observer file (line 421-443) does exercise the
wrap, but it does so by **recording descending growth**, not by **passing observations in the wrong
order** — two different code paths. The positional ambiguity is still uncovered.

**Remediation:** Add a companion test that calls `curr.growthDelta(prev)` (inverted args) on
ascending-growth data and asserts the result equals `2^208 - expectedDelta`. This pins the
wrap-on-inversion behavior and makes the F-11 fix (renaming arguments or adding a require)
a test-breaking change rather than a silent behavior flip.

---

### X-08 — No cache-invalidation check on `ran_accumulator.duckdb`

**Severity:** HIGH
**Location:** `contracts/test/_ffi_utils/ffiLib.sol:14 RAN_DB_PATH`; all FFI-grounded tests

**Description:** The DuckDB path `data/ran_accumulator.duckdb` is hardcoded. If the file is
stale (e.g., captured at BLOCK_NUMBER_0 = 22500000 but Angstrom has since been upgraded),
the FFI returns data that disagrees with on-chain reads at the same block — but only for post-
BLOCK_NUMBER_0 rows. The tests do `vm.rollFork(row.blockNumber)` and then assert
`consumer.globalGrowth(USDC_WETH) == row.globalGrowth`.

If the FFI dataset was captured against a **pre-upgrade** Angstrom storage layout and the fork
now points at a **post-upgrade** block, the reads diverge and the test fails — loudly. OK so far.

**The silent failure mode:** If the DuckDB file is *missing* entirely, the Python script
`scripts/ran_ffi.py` exits with error (seen in grep: `sys.exit(1)` on missing data paths).
`ffiPython(...)` in the forge test then has `raw == ""` and `abi.decode(raw, ...)` reverts with
empty data — **which is caught by nothing**. The test fails with a generic "EvmError: Revert"
that gives no indication the FFI data is stale/missing vs a real assertion failure.

**Worse silent failure mode:** If the DuckDB file exists but was captured for a *different* pool
(`RAN_POOL_HEX` constant was changed at capture time), all assertions fail — but the error
message is `globalGrowth mismatch`, implying a library bug when the real cause is test
infrastructure drift.

**Remediation:**
1. Add a first-run smoke test that verifies the DuckDB schema version and pool id:
   ```solidity
   function test_FFI_datasetPoolIdMatchesConst() public onlyForked {
       bytes memory poolIdBytes = ffiPython(poolIdArgs()); // new FFI command
       assertEq(abi.decode(poolIdBytes, (bytes32)), bytes32(USDC_WETH), "FFI dataset drift");
   }
   ```
2. Add a min-length assertion: `decodeLen(ffiPython(lenArgs())) > 1000` to fail fast if the
   dataset is truncated.
3. Make `scripts/ran_ffi.py` version-stamp its output so `decodeLen` can include a version byte
   the Solidity side can check.

---

### X-09 — `NearMaxSqrtPriceCliff` `try/catch` swallows non-TickMath reverts

**Severity:** HIGH
**Location:** `contracts/test/libraries/GrowthToTickLib.diff.t.sol:157-177`

**Description:** The test wraps `externalGrowthToTick` in `try/catch` and branches on success/
revert. The catch block asserts `sqrtPriceX96 >= uint256(TickMath.MAX_SQRT_PRICE)` — implying the
revert came from `TickMath.getTickAtSqrtPrice`. **But any revert is caught**, including:
- `FullMath.mulDiv` overflow (Stage 1 — from a later fuzz run with different bounds)
- Solady `sqrt` on adversarial input
- Memory / gas exhaustion

The catch block's assertion is a **necessary but not sufficient** condition. A Stage 1 overflow
that happens to satisfy `sqrtPriceX96 >= MAX_SQRT_PRICE` (trivially true if the computation
overflowed into high bits) would pass the catch branch but the actual revert came from mulDiv,
not TickMath. The test claims to pin a TickMath-cliff revert but pins something weaker.

**Attack on confidence:** A regression that moves the revert source from TickMath to FullMath —
e.g., an overflow exposure due to changing the Q128 constant — would still pass this test. The
test's name `NearMaxSqrtPriceCliff` implies structural pinning; the assertion doesn't deliver it.

**Remediation:** Use `vm.expectRevert(TickMath.InvalidSqrtPrice.selector)` with the try/catch
replaced by a direct `if (sqrtPriceX96 >= MAX) { vm.expectRevert(...); } else { ... }` fork.
Or use Foundry's `expectRevert` with selector matching inside the catch.

---

### X-10 — D4 test calcifies the F-04 bug as specification

**Severity:** HIGH
**Location:** `contracts/test/integration/AngstromRANPipeline.diff.t.sol:222-237`

**Description:** The test records descending growth, reads the observation, and asserts
`wrappedDelta == (1 << 208) - (5e30 - 1e30)`. The comment on line 233 says:
`"growthDelta must wrap silently"`. The assertion is **an equality**, not a revert — it **pins
the current broken behavior as intended behavior**.

Prior audit `integration-review-and-flaws.md` flagged F-04 and F-05 (no monotonic growth check in
`record()` or `updateGrowthEMA`). The **fix** for F-04 is to `revert NonMonotonicGrowth()` in
`record()`. If that fix lands, this test **fails** — because `recordSynthetic` at line 224 would
revert on the second call, `growthDelta` would never execute, and the assertion would never be
reached.

**This creates a hostile-to-fix artifact.** A developer applying F-04's recommended fix has to
simultaneously rewrite this test, risking either (a) leaving the fix un-tested or (b) leaving
this test dangling. The test's current form is a **regression-detection device for non-fix** — it
catches the state where F-04 is correctly fixed and flags it as a break.

**Remediation:** Rewrite the test to be **bidirectional on the fix state**:
```solidity
function test__IntegrationSecurityEdge__D4_DescendingGrowthHandling() public onlyForked {
    pipeline.recordSynthetic(1000, 0, 5e30);
    try pipeline.recordSynthetic(1001, 12, 1e30) {
        // F-04 unfixed: record succeeded; document wrap behavior but mark as TODO
        uint208 wrappedDelta = pipeline.oldest().growthDelta(pipeline.latest());
        assertEq(uint256(wrappedDelta), (uint256(1) << 208) - (5e30 - 1e30));
        emit log_string("UNFIXED F-04: non-monotonic growth accepted silently");
    } catch Error(string memory reason) {
        // F-04 fixed: record rejected; verify buffer untouched
        assertEq(pipeline.count(), 1, "failed record must not mutate buffer");
    } catch (bytes memory lowData) {
        assertEq(bytes4(lowData), bytes4(keccak256("NonMonotonicGrowth()")), "wrong revert");
        assertEq(pipeline.count(), 1, "failed record must not mutate buffer");
    }
}
```
This pattern is hostile to reviewers (nested try/catch) — preferable is a **feature flag** in
`record()` that defaults to revert, and this test asserts revert.

---

## MEDIUM

### X-11 — `ObserveAtExactOldestBoundaryPostWrap` underflows when startBlock is low

**Severity:** MEDIUM
**Location:** `contracts/test/libraries/BlockNumberAwareGrowthObserverLib.diff.t.sol:220-243`

**Description:** Line 242: `m.observeAtTarget(oldestBlock - 1)` where `oldestBlock =
uint32(startBlock + oldestSurvivingIdx)`. If `startBlock + oldestSurvivingIdx == 0` (only
happens when the test runs against a fork at genesis or a non-fork context with block.number = 0),
the subtraction underflows `uint32` to `type(uint32).max`. The `observeAt` call would then
traverse the newest path (newest <= target returns newest) instead of reverting with
`ObservationExpired`. The test would fail — but with a confusing error.

More realistically: the test uses `vm.roll` indirectly via the loop (`vm.roll(startBlock + i)`).
`startBlock = block.number` from `setUp` which inherits the fork block. For the fork reference
block BLOCK_NUMBER_0 (~mainnet contemporary), no underflow. But if someone changes BLOCK_NUMBER_0
to a small number, or if the test is moved to a non-fork suite, the underflow happens silently.

**Assertion that gives false confidence:** `vm.expectRevert(abi.encodeWithSignature(...))` —
the hard-coded signature string is **brittle**, as prior audit flagged. This compounds: if the
test silently reaches a different revert path (uint32-wrap target), the hard-coded signature
still doesn't match and the test fails — but the user sees `revert signature mismatch`, not
`test assumes non-genesis block`.

**Remediation:**
```solidity
vm.assume(startBlock + oldestSurvivingIdx > 0); // guard underflow
// And pin the error:
vm.expectRevert(abi.encodeWithSelector(ObservationExpired.selector, oldestBlock - 1, oldestBlock));
```

---

### X-12 — `EMA_FuturePackReverts` does not bound the magnitude of prevented corruption

**Severity:** MEDIUM
**Location:** `contracts/test/libraries/transformations/EMAGrowthTransformationLib.diff.t.sol:84-101`

**Description:** The test verifies the F-01 guard fires on future packs. It asserts the revert
with the correct selector and args. Good.

**The missing assertion:** there is no test proving that **without the guard**, the computation
would produce catastrophic output. A refactor that accidentally removes the guard **and**
replaces it with a no-op would make this test fail (good), but a refactor that *moves* the guard
to a later stage (e.g., after the buffer read) would still revert with `FuturePack` in
production-relevant scenarios but with wrong intermediates that break assumptions of subsequent
stages. The test doesn't witness the bug's *magnitude* — only its *absence*.

**More concrete gap:** The guard rejects `currentOraclePack.epoch() > currentEpoch`. What about
`currentOraclePack.epoch() == currentEpoch + 1` **in the presence of a `vm.warp` race** where
`block.timestamp` decreases between lines 46 and 53 of the library? EVM doesn't allow
`block.timestamp` decrease within a tx, but L2 reorgs and fork-tests do. The test's `vm.warp` is
monotonic; the adversarial warp-backward scenario is not covered.

**Remediation:** Add a "wrapped-delta magnitude" canary that temporarily reintroduces the
unguarded path via a direct internal function call (if library structure allows) and asserts the
catastrophic `timeDelta ≈ 2^24 * 64`. Or, if library refactor to expose the inner computation
isn't desired, add a comment-tag flagging F-01 coverage as "guard-only, not magnitude-bounded."

---

### X-13 — `AnchorScalingInvariance` tolerates 1-tick drift which equals the LSB of the tick space

**Severity:** MEDIUM
**Location:** `contracts/test/libraries/GrowthToTickLib.diff.t.sol:75-94`

**Description:** The test scales both `currentGrowth` and `anchorGrowth` by `k` and asserts the
resulting tick differs by at most 1. The rationale: `FullMath.mulDiv` introduces integer-division
rounding error that propagates through `sqrt` to at most 1 tick at the Q128.128 scale.

**The assertion is too loose in one direction.** For `k = 2`, the error should be strictly 0 —
scaling both numerator and denominator by 2 cancels exactly in `mulDiv(current, Q128, anchor)`.
The test permits `k >= 2` and asserts `diff <= 1`, which means a regression that introduces a
1-tick error at `k = 2` passes. The **correct** assertion would be: for `k` a power of 2 that
divides both values without remainder, the error is 0.

More critically: the test does not scan across `k = 2, 4, 8, ..., 2^30` to verify the drift
magnitude *doesn't grow with k*. If a regression caused the rounding error to scale with `log(k)`,
the test's 1-tick tolerance would still pass up to `k = 2^N` for some N, then silently fail at
larger k — but the fuzz distribution clamps `k <= maxK = type(uint208).max / currentGrowth`, which
is typically small (since currentGrowth is fuzzed up to `uint208.max / 2`), so large-k cases are
rarely exercised.

**Remediation:**
```solidity
// Deterministic case at k=2 — error must be EXACTLY 0
function test_scalingInvariance_k2_exact() public pure {
    int24 t1 = growthToTick(1e30, 5e29);
    int24 t2 = growthToTick(2e30, 1e30);
    assertEq(t1, t2, "k=2 scaling must preserve tick exactly");
}
// Log-scan k
for (uint256 k = 2; k <= 1 << 30; k <<= 4) { ... }
```

---

### X-14 — `HappyPath` `expectedGrowthTick` uses the library under test as its own oracle

**Severity:** MEDIUM
**Location:** `contracts/test/integration/AngstromRANPipeline.diff.t.sol:135-136`

**Description:** Line 135:
```solidity
int24 expectedGrowthTick = growthToTick(lat.cumulativeGrowth(), old.cumulativeGrowth());
assertGe(expectedGrowthTick, 0, "...");
```

The test names `expectedGrowthTick` but the "expected" value is **computed by the very function
under test**. The assertion `>= 0` is the only discriminating check — everything before it is
tautology.

If `growthToTick` had a bug where it always returned `0` for ascending growth, this test would
pass. If it returned `MAX_TICK` for ascending growth, this test would pass. **The only bug class
this assertion catches is "returns negative for ascending growth" — which is exactly what F-03
describes** — and the check is `>= 0`, not `> 0`, so even a regression returning 0 for all
monotonic positive-growth cases would pass.

**Remediation:** Compute the expected tick **off-chain** (Python FFI) against the same growth
pair, and assert on-chain matches off-chain. The FFI infrastructure is already in place.

---

### X-15 — `RelativeTimeDeltaInRangeRoundTrips` doesn't exercise `record()` skip logic

**Severity:** MEDIUM
**Location:** `contracts/test/libraries/BlockNumberAwareGrowthObserverLib.diff.t.sol:167-181`

**Description:** The test records at blocks 1000 and 1001, then reads the latest's
`relativeTimeDelta`. It does not use `vm.roll` — the `block.number` of the EVM at test time is
unrelated to the stored `1000` and `1001`. `record()` does its own `SafeCastLib.toUint32` and
block-skip logic based on the input `_blockNumber`, not `block.number`. So the test *does*
exercise the storage/retrieval, but it does **not** exercise the integration between real block
numbers and stored block numbers.

**Silent miscomputation window:** If `record()` were refactored to use `block.number` instead of
the input `_blockNumber` for monotonicity checking, the test would still pass (because both
stored block numbers are > 0 and real `block.number` at fork time is > 1001). The test's lack of
`vm.roll` means it cannot discriminate "uses input block number" from "uses block.number" from
"uses some other heuristic."

**Remediation:** Add `vm.roll(10000)` before `m.recordObs(1000, 0, 1e18)` — if the library were
using `block.number`, the record would be rejected (1000 < 10000 is fine; but a library using
`block.number` for monotonicity would reject 1001 as being < 10000).

---

### X-16 — `ConsecutiveRowsMonotonic` dilutes coverage with 4 assertions on one comparison

**Severity:** MEDIUM
**Location:** `contracts/test/types/GrowthObservation.diff.t.sol:88-113`

**Description:** 4 assertions (`gte`, `!gte`, `lt`, `!lt`) on a single `(prev, curr)` pair with
`curr.blockNumber() > prev.blockNumber()` by DuckDB invariant. All 4 assertions are algebraic
consequences of the single fact `curr.bn > prev.bn` and the correct pairing of gte/lt operators.

A refactor that broke `lt` (e.g., `<=` instead of `<`) would fail `assertFalse(curr.lt(prev))` —
OK. But the test reports this as 4 coverage data-points in a matrix where the real information
content is 1. Aggregate coverage metrics overstate the rigor of the suite.

**More subtle gap:** the equality case (`curr.bn == prev.bn`) is never tested — impossible via
DuckDB rows (they're distinct by construction), but trivial to synthesize. A bug where
`gte` returned `false` on equality would not be caught.

**Remediation:** Split into two tests — one for strict ordering (as-is, but merge the 4
assertions into 2) and one deterministic equality test for the boundary.

---

### X-17 — `InsufficientObservations` does not pin the `count == 0` post-empty branch

**Severity:** MEDIUM
**Location:** `contracts/test/libraries/transformations/EMAGrowthTransformationLib.diff.t.sol:69-82`

**Description:** The test covers `count == 0` (empty buffer) and `count == 1` (one record). Both
revert. What it does not cover: **a buffer that was filled and then "emptied" via some external
operation**. CircularBuffer doesn't provide an explicit clear, but a future library addition
(e.g., governance-controlled reset) would create a state where `count` drops to 0 between two
updates.

The test re-deploys `MockEMABuffer` between sub-cases rather than exercising the same buffer
through multiple states. This masks any state-dependent behavior in the count check.

**Remediation:** Add a sub-case that records 2 observations, runs update successfully, then
(via a governance path to be added) clears the buffer and asserts the next update reverts with
`InsufficientObservations` — verifying the state-dependent branch, not the pristine one.

---

### X-18 — `MAX_SPIKE_IDX = 27677` is an opaque hard-coded constant

**Severity:** MEDIUM
**Location:** `contracts/test/_adapters/AngstromAccumulatorConsumer.fork.diff.t.sol:25`

**Description:** The constant `MAX_SPIKE_IDX = 27677` is meant to index the row in the DuckDB
dataset with the largest single-block growth spike — a canary for integer-width assumptions.
Problems:
1. No comment explains what dataset generation produced this index.
2. If the DuckDB dataset is regenerated (e.g., extended with newer blocks), the "max spike" index
   may shift — but the test still reads index 27677. The test passes if that row's growth is
   merely recorded on-chain correctly, which is the same invariant as every other row. **The
   "spike" semantic is lost** unless someone re-verifies this index is still the argmax.
3. No assertion verifies `row.globalGrowth` at this index is meaningfully large. A regenerated
   dataset could have 27677 as a near-zero row, and the test still passes as a degenerate
   duplicate of test 1 (First).

**Remediation:** Either (a) compute the argmax at test time via a Python FFI `argmax-growth-delta`
command, or (b) add an assertion that `row.globalGrowth > SOME_THRESHOLD` to verify semantic
relevance, or (c) add a comment documenting how to regenerate this index and what value of
`globalGrowth` corresponds to it.

---

### X-19 — `ObserveAtProductionCadence` uses fork-time `startTimestamp`, drift-sensitive

**Severity:** MEDIUM
**Location:** `contracts/test/libraries/BlockNumberAwareGrowthObserverLib.diff.t.sol:91-129`

**Description:** `startTimestamp = block.timestamp` inherits the fork block's timestamp (~1.7B
for BLOCK_NUMBER_0). The test then uses `vm.warp(startTimestamp + i * 12)` and passes
`relTimeDelta = 12` (uint16-safe). OK.

**Drift-sensitivity:** If someone changes BLOCK_NUMBER_0 to a block where the timestamp is close
to `2^64 - 256*12`, the warp loop's final iteration overflows the EVM's uint64 timestamp and
`vm.warp` reverts. The test would fail — but with an opaque `vm.warp` error. **Not immediate risk**
(current BLOCK_NUMBER_0 is far from uint64.max), but a latent footgun.

More importantly: the loop computes `growth = (i + 1) * 1e18`. For i approaching 256,
`growth ≈ 2.56e20`, well within uint208. No overflow. But if BUFFER_CAPACITY is raised in the
future without also re-thinking the synthetic growth scale, the test could silently enter a
region where `newGrowthObservation` reverts via SafeCastLib. Test infrastructure brittleness.

**Remediation:** Document the coupling between BUFFER_CAPACITY, growth scale, and timestamp
range. Add a static assertion at test entry.

---

### X-20 — `PackRoundTrip` doesn't exercise cross-field bit leakage

**Severity:** MEDIUM
**Location:** `contracts/test/types/GrowthObservation.diff.t.sol:22-36`

**Description:** The test sets `blockNumber`, `relativeTimeDelta=0`, and `cumulativeGrowth`, then
reads each field back. It does not test the adversarial case where all three fields are at
**simultaneous maxima**: `blockNumber = uint32.max`, `relativeTimeDelta = uint16.max`,
`cumulativeGrowth = uint208.max`. If the bit-packing had an off-by-one in the shift amount
(e.g., `<< 49` instead of `<< 48`), the fields would overlap — **but overlap at the max values is
the most sensitive regime**. The fuzz distribution picks `relativeTimeDelta = 0` (hardcoded
`FIRST_OBSERVATION_TIME_DELTA`), so the middle 16 bits are always 0. A bit-leak from `blockNumber`
into the middle 16 bits would be masked.

**Remediation:** Add a deterministic test case with all three fields at `type(T).max`:
```solidity
function test_PackRoundTrip_allMax() public pure {
    GrowthObservation obs = newGrowthObservation(
        type(uint32).max, type(uint16).max, type(uint208).max
    );
    assertEq(uint256(obs.blockNumber()), type(uint32).max);
    assertEq(uint256(obs.relativeTimeDelta()), type(uint16).max);
    assertEq(uint256(obs.cumulativeGrowth()), type(uint208).max);
}
```

---

## LOW

### X-21 — `decodeRange` `require` bypasses revert-selector matching

**Severity:** LOW
**Location:** `contracts/test/_ffi_utils/ffiLib.sol:111-114`

**Description:** `require(count == blockNumbers.length && ..., "decodeRange: count mismatch")`.
String-message `require`s emit `Error(string)` — **not a named selector**. Any test that expects
a specific revert around an FFI decode cannot distinguish `Error("decodeRange: count mismatch")`
from unrelated string-reverts. Use a custom error instead.

---

### X-22 — Zero `vm.label` calls across the suite

**Severity:** LOW
**Location:** All test files

**Description:** `vm.label` attaches human-readable names to addresses in Foundry traces. The
suite uses `new MockBlockNumberAware(...)`, `new MockEMABuffer(...)`, `new MockRANPipeline(...)`,
and `new AngstromAccumulatorConsumer(...)` — none are labeled. Fuzz failure traces show raw
`0x1234...` addresses, which on a 5-mock test is nearly unreadable.

**Remediation:** Add `vm.label(address(m), "MockObserver")` etc. in setUp.

---

### X-23 — `storeOraclePack` literals inline in integration test

**Severity:** LOW
**Location:** `contracts/test/integration/AngstromRANPipeline.diff.t.sol:139-141, 158-160, 172-174, 209-211`

**Description:** The integration test constructs `OraclePack` via direct `storeOraclePack(epoch-1,
0, 0, 0, 0, 0, 0)` at 4 sites. The unit test uses a `_packAtEpoch` helper. The integration file
duplicates the pattern with magic-zero literals, making a refactor of `OraclePack` layout (add a
field, change offsets) require editing 4 sites. Extract into a helper.

---

### X-24 — `MockBlockNumberAware.rawAt` exposes internal buffer ordering

**Severity:** LOW
**Location:** `contracts/test/libraries/BlockNumberAwareGrowthObserverLib.diff.t.sol:49-51`

**Description:** `rawAt(i)` returns `CircularBuffer.last(buffer, i)` directly. Tests rely on this
to verify "descending ordering." If the library swaps to a different underlying buffer (e.g.,
OpenZeppelin's SortedDoublyLinkedList), `CircularBuffer.last(...)` is no longer meaningful — the
test must also be updated. This is an acceptable coupling for a library-specific test, but the
test name `DescendingBlockOrderingInvariant` implies a library contract, whereas the assertion
proves an OpenZeppelin `CircularBuffer` contract. Document this explicitly.

---

## Cross-Cutting Adversarial Surface Not Covered Anywhere

### A. Reentrancy via OraclePack caller

`updateGrowthEMA` is `view`, so reentrancy into storage writes is impossible **at this layer**. But
the returned `OraclePack` is persisted by the caller. If the caller's persist logic calls back
into `updateGrowthEMA` (e.g., a hook that reads its own pack to decide whether to update), there
is a read-reentrancy window where `buffer` reflects state-between-records and the EMA drifts. No
test models this caller pattern — which is exactly how hook-composed oracles are integrated.

**Recommendation:** Document the caller contract (`recordFromOnChain` then `runEMA` then persist)
and add an integration canary that reenters during persist.

### B. Block-timestamp manipulation by proposers

`currentEpoch = uint24((block.timestamp >> 6) & 0xFFFFFF)` — 64-second epochs. A proposer can
adjust `block.timestamp` up to 12 seconds without consensus penalty. The epoch boundary is
therefore manipulable within a ~64-second window (the proposer can delay or advance the epoch
flip by 12s). No test models a proposer-driven adversarial warp to skip an epoch update or
force a same-epoch no-op when a real update was due.

**Recommendation:** Add a test that warps `block.timestamp` to `epoch_boundary - 1` and to
`epoch_boundary + 1`, asserting the same-epoch / advance behavior crosses cleanly. This is a
1-second discrimination, within proposer-manipulation range.

### C. `CircularBuffer._count` vs `_tail` desync under `setup()` reentry

OpenZeppelin's `CircularBuffer.setup()` can be called multiple times (each re-initializes the
capacity). In the mock, `setup` is called in constructor — fine. But if a production caller
exposes a governance `resize()` path that calls `setup` again, `_count` is zeroed while `_data`
retains old values. A subsequent `last(buffer, 0)` returns a stale slot. No test models this.

**Recommendation:** Document that `setup` must be called exactly once post-deployment. If the
production `AngstromAccumulatorConsumer` adapter wraps the buffer, add an explicit constructor
guard.

### D. Keeper capture: the `same-block-first-wins` trust surface

F-09 in the prior audit noted same-block observations are silently skipped. The implication for
adversarial keepers: a keeper who submits a *wrong* growth value at block N locks the buffer for
that block — a later correct submission from a whitelisted fallback keeper is rejected. An
integration test that demonstrates this griefing path (two keeper addresses, one adversarial)
would make the trust assumption concrete.

### E. `poolExists` timing side-channel

`AngstromAccumulatorConsumer.poolExists` loops over `totalEntries()` and returns on the first
non-empty entry. Gas usage varies by pool position in the config store — a side channel for
off-chain observers to infer which pools exist without storage proofs. Low severity but worth
documenting; not tested.

---

## Remediation Priority

**Block production launch:**
- X-01 (silent fork skip in CI — critical, same as prior SS-1)
- X-02 (tautological boundary assertion)
- X-04 (no cross-pool canary — storage layout drift undetected)
- X-06 (mirrored canary under-asserts)
- X-10 (D4 calcifies bug)
- X-03 + X-09 (revert taxonomy leaks)
- X-08 (FFI dataset freshness check)

**Fix in the first post-launch iteration:**
- X-05, X-07, X-11, X-13, X-14, X-15 — all involve strengthened assertions on existing tests.

**Nice-to-have hygiene:**
- X-16, X-20, X-17, X-19, X-21, X-22, X-23, X-24 — reduce false-confidence, improve DX.

---

## Final Note on Prior-Audit Coverage

Of the 6 P0 flaws flagged in `integration-review-and-flaws.md`:
- **F-01 (future pack):** FIXED in library, TESTED (though X-12 flags a gap in the test's
  magnitude assertion).
- **F-02 (zero anchor anonymous revert):** UNFIXED. Tests use `vm.expectRevert(bytes(""))` which
  is too loose (X-03).
- **F-03 (inverted arg silent negative tick):** UNFIXED. I2 test exists but under-asserts (X-06).
- **F-04 (silent wrap on descending growth):** UNFIXED. D4 test calcifies the wrap as
  specification (X-10).
- **F-05 (no anchor-order enforcement):** UNFIXED. Same gap as F-03.
- **F-06 (negative clampDelta):** UNFIXED. All tests hardcode `DEFAULT_CLAMP = 100` or `1000`,
  never negative. **No test exercises the negative clamp inversion.**

**5 of 6 P0 flaws remain both unfixed and untested as guards.** The test suite is best understood
as a behavior-witness corpus rather than a production-readiness gate. Before mainnet deployment,
either (a) the library fixes must land and these tests must be converted to revert-assertions,
or (b) the protocol must formally document that these cases are the caller's responsibility and
add runtime checks in the hook that integrates the oracle.
