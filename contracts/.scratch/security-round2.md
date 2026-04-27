# Round-2 Security Audit — RAN Oracle Test Suite

**Document type:** Adversarial security audit (round 2)
**Scope:** 49 tests across 6 files after assertion tightening and FuturePack guard
**Status:** NEEDS WORK — five new P0/P1 findings, multiple P2s
**Date:** 2026-04-13
**Auditor:** Blockchain Security Auditor
**Defaults to:** NEEDS WORK
**Prior reports reviewed:**
- `security-edge-cases-growth-observer.md`
- `security-edge-cases-growth-to-tick.md`
- `security-edge-cases-ema-transformation.md`
- `integration-review-and-flaws.md`
- `security-final-review.md`
- `diff-tests-review-round2.md`

---

## Executive Summary

The round-1 remediations (FuturePack guard, canary tightening, worst-case binary-search targeting, try/catch forward compatibility) close the headline gaps the prior audits called out. However, **the fix for F-01 introduces a new P0 correctness regression** (N-01, below) that the round-1 audits did not anticipate, and the round-1 audits missed several adversarial surfaces that are wholly new findings at the test-infrastructure and cross-test-coupling layers.

**New findings — 12 total:**
- **P0 (critical):** 2 — N-01 (FuturePack breaks legitimate 24-bit wrap), N-02 (fork-state poisoning pre-Angstrom)
- **P1 (high):** 4 — N-03 (D.4 canary not forward-compatible), N-04 (fuzz seed correlation), N-05 (relativeTimeDelta boundary data-dependent revert), N-06 (DEFAULT_PERIODS may not model production)
- **P2 (medium):** 6 — N-07 through N-12

**What round-1 audits missed, categorically:**
1. **Round-tripping** between applied fixes: applying F-01 (future-pack guard) broke F.3 (legitimate epoch-wrap correctness). No round-1 auditor considered that the fix itself would violate another P1 invariant the same document proposed.
2. **Fork-test pitfalls:** `vm.rollFork` to pre-Angstrom blocks silently produces `extsload = 0` from an EOA/empty account. None of the prior audits examined whether `BLOCK_NUMBER_0` dominates every row's `blockNumber` in the RAN dataset.
3. **FFI supply-chain:** The DuckDB snapshot at `data/ran_accumulator.duckdb` is the off-chain oracle for every differential test. Trust boundary never evaluated.
4. **Cross-test state coupling:** Canary tests (C1, F-01, negative-clamp) assume `block.timestamp` at fork time; future test ordering changes or skill-drift changes silently break the canaries.

---

## Part 1 — NEW P0 Findings

### N-01 P0 — FuturePack guard bricks legitimate 24-bit epoch rollover

**File:** `contracts/src/libraries/transformations/EMAGrowthTransformationLib.sol` L49-55
**Test that proves it missing:** none; `F.3 EMA_Uint24EpochWrapAroundCorrectness` (proposed in `security-edge-cases-ema-transformation.md`) was never implemented.

**Attack / failure mode.** The F-01 remediation reads:

```solidity
if (currentOraclePack.epoch() > currentEpoch) {
    revert FuturePack(currentOraclePack.epoch(), currentEpoch);
}
```

At the 24-bit epoch counter rollover (~34 years from Unix epoch 0), a pack stored just before wrap has `pack.epoch() = 0xFFFFFE`. Immediately after the wrap, `currentEpoch = 0x000001`. The guard evaluates `0xFFFFFE > 0x000001` → **TRUE** → reverts `FuturePack`.

Pre-fix behavior was correct by unchecked-subtraction:
```solidity
timeDelta = int256(uint256(uint24(currentEpoch - pack.epoch()))) * 64;
//        = uint24(0x000001 - 0xFFFFFE) * 64 = 3 * 64 = 192 seconds
```

The F-01 fix as written discriminates "future pack" (timing attack) from "just-wrapped pack" (legitimate) only by the raw uint24 comparison — which these two cases are indistinguishable by. The library now permanently bricks every stored pack at the wrap boundary, requiring operator intervention to re-seed the pack with the new epoch.

**Critical subtle note.** The 24-bit epoch wrap is *not* a far-future edge case. `block.timestamp >> 6` counts from Unix epoch 0. At mainnet's current timestamp (~1.74e9), `(block.timestamp >> 6) ≈ 2.7e7`, which is past `2^24 = 1.68e7`. **The counter has already wrapped at least once.** This means:

- Every pack currently stored on mainnet is already post-wrap.
- The fix's `epoch() > currentEpoch` check is comparing two already-wrapped values.
- The next wrap (~34 years from Unix epoch 0 + one full uint24 cycle) will brick the oracle if F-01 is unpatched.

Worse: **during any single transaction at the wrap boundary** (one block spans the wrap), a pack stored at `t0` with `epoch() = 0xFFFFFF` and the same transaction's `currentEpoch` at wrap+k has `0xFFFFFF > k` for all k < 0xFFFFFF — **every** legitimate pack from the prior 34 years reverts.

**Concrete canary test to add (not yet present):**
```solidity
function test__SecurityEdge__F01_Fix_BreaksLegitimateWrap() public {
    vm.warp(uint256(0xFFFFFF) << 6);  // currentEpoch = 0xFFFFFF
    uint24 ceBefore = uint24((block.timestamp >> 6) & 0xFFFFFF);
    assertEq(ceBefore, 0xFFFFFF);

    MockEMABuffer m = new MockEMABuffer(BUFFER_CAPACITY);
    m.recordObs(1000, 0, 1e18);
    m.recordObs(1001, 12, 2e18);

    // Pack stored at prior epoch (legitimate)
    OraclePack storedPack = _packAtEpoch(0xFFFFFE);

    // Advance one epoch — currentEpoch wraps to 0x000000
    vm.warp((uint256(0xFFFFFF) + 1) << 6);
    uint24 ceAfter = uint24((block.timestamp >> 6) & 0xFFFFFF);
    assertEq(ceAfter, 0x000000);

    // Pre-fix: succeeds with timeDelta = 2 * 64 = 128 s.
    // Post-F01: reverts with FuturePack(0xFFFFFE, 0x000000) — INCORRECT
    vm.expectRevert();  // documents regression
    m.runUpdate(storedPack, DEFAULT_PERIODS, DEFAULT_CLAMP);
}
```

**Remediation.** The guard must discriminate "legitimate wrap" from "adversarial future" using an allowed-window bound, e.g.:
```solidity
uint24 epochDelta;
unchecked { epochDelta = uint24(currentEpoch - currentOraclePack.epoch()); }
// Reject only if the forward distance is implausibly large (>1 year of epochs = ~500k).
// Legitimate wrap produces small epochDelta via intentional mod-2^24 arithmetic.
if (epochDelta > MAX_ALLOWED_EPOCH_GAP) revert FuturePack(...);
```

Or: require callers to signal wrap explicitly with an additional parameter.

**Why P0.** The F-01 fix was landed with a P0 test gap that the round-1 audits explicitly warned about (see F.3 in `security-edge-cases-ema-transformation.md`). The fix itself introduces a permanent-DoS at a known future boundary. Every installed pack becomes a time bomb.

---

### N-02 P0 — Fork tests silently return zero when rolling to pre-Angstrom blocks

**File:** `contracts/test/_adapters/AngstromAccumulatorConsumer.fork.diff.t.sol` (all 6 tests)
**Adjacent vulnerable file:** `contracts/test/integration/AngstromRANPipeline.diff.t.sol` `test__Integration__PipelineHappyPath`

**Attack / failure mode.** The `AngstromAccumulatorConsumer` is deployed in `setUp()` at `BLOCK_NUMBER_0` (via the forked state created by `vm.createSelectFork(..., BLOCK_NUMBER_0)` in `BaseForkTest`). It is then marked `vm.makePersistent(address(consumer))`, which tells Foundry to retain the bytecode across fork rolls.

Each test then calls `vm.rollFork(row.blockNumber)` using a block number pulled from the FFI/DuckDB dataset. Nothing prevents `row.blockNumber < BLOCK_NUMBER_0`. When that happens:

1. The fork rolls to a block where the Angstrom contract at `EthereumForkData.AngstromAddresses.ANGSTROM` **did not exist yet** (was deployed later in mainnet time).
2. `extsload` on a non-contract address returns zero (EOA/empty-account semantics).
3. `consumer.globalGrowth(USDC_WETH)` returns `0`.
4. The FFI oracle also returns `globalGrowth = 0` for that row (because the `ran_data_api` script presumably captures post-deploy state only — or worse, it captures pre-deploy rows and encodes them as zero).
5. **The assertion `assertEq(onchain, row.globalGrowth) == assertEq(0, 0)` silently passes.**

The test infrastructure offers no invariant `assert(row.blockNumber >= BLOCK_NUMBER_0)`, and the fuzz test `test__OffChainFuzzDifferentialTest__GlobalGrowthMatches` uniformly samples indices — if any dataset row precedes Angstrom deployment, it silently false-positives.

**Verification.** Check `EthereumForkData.AngstromAddresses.BLOCK_NUMBER_0` against the minimum block in the DuckDB dataset:

```bash
cd contracts && .venv/bin/python -m scripts.ran_ffi min --pool 0xe500...657 --db data/ran_accumulator.duckdb
# compare to EthereumForkData.AngstromAddresses.BLOCK_NUMBER_0
```

If the dataset's minimum block < `BLOCK_NUMBER_0`, N-02 is exploitable today. Even if it is not today, there is no runtime barrier preventing a future dataset refresh from including earlier rows.

**Concrete canary.**
```solidity
function test__BaseForkInvariant__AllDatasetBlocksArePostAngstromDeployment() public onlyForked {
    uint256 n = decodeLen(ffiPython(lenArgs()));
    for (uint256 i; i < n; ++i) {
        AccumulatorRow memory row = decodeRow(ffiPython(rowArgs(vm, i)));
        assertGe(row.blockNumber, BLOCK_NUMBER_0, "pre-deployment row in dataset");
    }
}
```

(Or cheaper: min-row check once, in `setUp`.)

**Remediation options:**
1. Assert `row.blockNumber >= BLOCK_NUMBER_0` at the top of every fork test that uses `vm.rollFork`.
2. Have `ran_data_api.py` filter out pre-deployment rows at query time.
3. In the test, assert `address(ANGSTROM).code.length > 0` post-roll.

**Why P0.** Silently-passing differential test is the worst class of test bug — it converts a "differential" claim into vacuous "0 == 0". A future refactor of `globalGrowth()` to return `block.number` would still pass for all pre-deployment rows. The round-1 audits treated the fork tests as source-of-truth; this finding dismantles that trust.

---

## Part 2 — NEW P1 Findings

### N-03 P1 — D.4 descending-growth canary not forward-compatible with F-04 fix

**File:** `contracts/test/libraries/BlockNumberAwareGrowthObserverLib.diff.t.sol` L423-445

**Failure mode.** The test `test__fuzzSecurityEdge__GrowthDeltaWrapsOnDescendingGrowth` records two observations with descending growth and asserts:

```solidity
assertEq(m.count(), 2, "both obs recorded (record checks block, not growth)");
// ...
uint208 wrappedDelta = older.growthDelta(newer);
uint256 expectedWrap = (uint256(1) << 208) - (firstGrowth - secondGrowth);
assertEq(uint256(wrappedDelta), expectedWrap, "wrap magnitude mismatch");
```

The comment explicitly pins current behavior: `record()` does not check growth monotonicity. This is documented in `integration-review-and-flaws.md` as flaw F-04, with the prescribed fix:
> Inside `record()`, add a check that rejects observations whose `cumulativeGrowth` is less than the latest's. Default behavior change.

The round-2 fix list states "D.4 uses try/catch, forward-compatible with F-04 fix" — but this is for the **integration** test (`test__IntegrationSecurityEdge__D4_...`), not the unit test above. The unit test above has NO try/catch and NO forward-compatibility hatch. **When F-04 is landed, this unit test will fail immediately.**

The symmetric contradiction: the integration D.4 test explicitly handles both "both recorded" and "second rejected" cases, but the unit-level companion forces "both recorded" as an invariant. The two tests encode contradictory specifications of `record()`.

**Remediation.**
```solidity
function test__fuzzSecurityEdge__GrowthDeltaWrapsOnDescendingGrowth(
    uint256 firstGrowth,
    uint256 secondGrowth
) public onlyForked {
    firstGrowth = bound(firstGrowth, 1, type(uint208).max);
    secondGrowth = bound(secondGrowth, 0, firstGrowth - 1);

    MockBlockNumberAware m = new MockBlockNumberAware(BUFFER_CAPACITY);
    m.recordObs(1000, 0, firstGrowth);

    try m.recordObs(1001, 12, secondGrowth) {
        // Current behavior: wrap documented
        assertEq(m.count(), 2);
        uint208 wrappedDelta = m.oldest().growthDelta(m.latest());
        assertEq(uint256(wrappedDelta), (uint256(1) << 208) - (firstGrowth - secondGrowth));
    } catch {
        // F-04 fix: rejected
        assertEq(m.count(), 1);
    }
}
```

**Why P1.** Breaks a straightforward remediation path. A developer applying F-04 will see this test fail and may roll back the fix to avoid the "regression."

---

### N-04 P1 — Fuzz seed correlation in `BinarySearchUnderKeeperSkipPattern`

**File:** `contracts/test/libraries/BlockNumberAwareGrowthObserverLib.diff.t.sol` L389-421

**Failure mode.** `gapSeed` drives **both** the gap distribution AND the search target:

```solidity
for (uint256 i; i < BUFFER_CAPACITY; ++i) {
    uint256 gap = 1 + (uint256(keccak256(abi.encode(gapSeed, i))) % 20);
    bn += gap;
    m.recordObs(bn, i == 0 ? 0 : gap * 12, (i + 1) * 1e18);
}
// ...
uint32 target = uint32(bound(gapSeed, oldestBlock, newestBlock));
```

Consequence: the target is not independently fuzzed relative to the gap sequence. The fuzzer cannot explore "a target that falls inside an unusually large gap" independently — both are driven by the same seed, so any relation between target and gap is deterministic per-seed.

In particular, the fuzzer **never exercises** "target lands exactly at a block-number boundary of a recorded observation" independently from "target lands between observations." These two cases hit different binary-search paths. A bug in the `obs.blockNumber() > targetBlock` inequality (off-by-one) would be caught only by the subset of seeds where target = recorded block, which has no guaranteed coverage.

**Additionally:** the assertion `result.blockNumber() <= target` is a necessary but not sufficient invariant. A correct implementation returns the **largest** observation with `blockNumber() <= target`. The test's fallback loop:
```solidity
for (uint256 i; i < c; ++i) {
    uint32 bn_i = m.rawAt(i).blockNumber();
    if (bn_i > result.blockNumber() && bn_i <= target) {
        fail();
    }
}
```
catches the "result is too small" case — this is correct. But the loop does NOT assert `result.blockNumber() >= oldestBlock` (i.e., result is actually in the buffer). If `observeAt` returned a zero-initialized `GrowthObservation`, `result.blockNumber() == 0` and the loop correctly fails — but only if there exists any `bn_i` in the target range. If no `bn_i` satisfies the inner condition, the zero-observation silently passes.

**Remediation.**
```solidity
function test__fuzzSecurityEdge__BinarySearchUnderKeeperSkipPattern(
    uint256 gapSeed,
    uint256 targetSeed  // independent
) public onlyForked {
    // ... gap generation with gapSeed ...
    uint32 target = uint32(bound(targetSeed, oldestBlock, newestBlock));
    // ... query, assert ...
    assertGe(result.blockNumber(), oldestBlock, "result below oldest");
}
```

**Why P1.** Correlated fuzz seeds halve the effective input space. The test name implies "under any keeper skip pattern"; the implementation only exercises a 1-d slice of a 2-d space.

---

### N-05 P1 — `relativeTimeDelta` calculation can spuriously revert on wide-spaced fuzz indices

**File:** `contracts/test/types/GrowthObservation.diff.t.sol` L38-113 (three tests)

**Failure mode.** Multiple tests compute `relativeTimeDelta` as:
```solidity
vm.rollFork(prevRow.blockNumber);
uint256 prevTimestamp = block.timestamp;
// ...
vm.rollFork(currRow.blockNumber);
GrowthObservation curr = newGrowthObservation(
    block.number,
    block.timestamp - prevTimestamp,  // <-- can exceed 65_535
    currRow.globalGrowth
);
```

`newGrowthObservation` calls `SafeCastLib.toUint16(_relativeTimeDelta)`, which reverts `SafeCastLib.Overflow` if the input exceeds 65_535 seconds (~18.2 hours).

The fuzz tests iterate over consecutive dataset rows. If any `(prevRow, currRow)` pair is separated by more than 18.2 hours on mainnet (possible for early or thin-liquidity periods of a pool), the test reverts spuriously with an overflow error that is not the test's subject of investigation. The fuzzer reports a test failure that is actually a data-layout assumption violation.

The three affected tests:
- `test__fuzzDifferential__GrowthDeltaMatchesRawSubtraction`
- `test__fuzzDifferential__ElapsedBlocksMatchesRawSubtraction`
- `test__fuzzDifferential__ConsecutiveRowsMonotonic`

**Remediation.**
```solidity
uint256 delta = block.timestamp - prevTimestamp;
vm.assume(delta <= type(uint16).max);
GrowthObservation curr = newGrowthObservation(block.number, delta, currRow.globalGrowth);
```

Or use `bound` on `idx` to a known-dense index range. Or bound `delta` and document why.

**Why P1.** Spurious CI failures on a valid input erode trust in the test suite and cause developers to `vm.assume` their way around real bugs when they surface. The failure appears to indicate a bug in `newGrowthObservation` when in fact it is the test harness calling it with out-of-spec inputs.

---

### N-06 P1 — `DEFAULT_PERIODS` does not model production EMA spec

**File:** `contracts/test/libraries/transformations/EMAGrowthTransformationLib.diff.t.sol` L38
**File:** `contracts/test/integration/AngstromRANPipeline.diff.t.sol` L83

Both tests use:
```solidity
uint96 constant DEFAULT_PERIODS = uint96(100 + (256 << 24) + (1024 << 48) + (4096 << 72));
```

Decoding: `spot = 100 seconds`, `fast = 256 seconds`, `slow = 1024 seconds`, `eons = 4096 seconds`.

The BTT specification and EMA documentation specify each period MUST be `>= 64` seconds (one epoch). 100 passes — but the documentation further recommends `spot >= 10 minutes = 600 s`, `fast >= 1 hour`, `slow >= 8 hours`, `eons >= 1 day`. The test constants are **three to four orders of magnitude shorter than production recommendations.**

Consequences on test validity:
1. With `EMA_PERIOD_SPOT = 100` and `timeDelta = 64`, the convergence is `64/100 = 64%` per update — nearly full replacement. EMA smoothing is effectively absent.
2. Convergence-test invariants (e.g., "EMA drifts at most `clampDelta` per update") hold only when the time-delta-to-period ratio is small. At 64/100, the bounded-drift claim does not hold — the EMA can move by `0.64 * (clampedTick - previousEMA)`, which on the default `clampDelta = 100` means the EMA can move up to 64 ticks per update, not 100. The bound is correct, but the behavior is pathological.
3. Tests designed to catch "pull toward tick 0" (the stagnation canary C.2) run with effectively-no-smoothing EMAs, so drift per step is near-maximum. The test passes not because the system is correct but because the EMA is so aggressive that drift is always visible at the clamp bound.
4. **`test__IntegrationSecurityEdge__C2_StagnantPoolDoesNotRevertAndTicksEpoch`** asserts `afterSecond == afterFirst` for same-epoch re-entry. This holds because the epoch gate short-circuits before EMA math. The DEFAULT_PERIODS mismatch does not affect this specific assertion, but it means the test does not exercise production-representative convergence dynamics.

**Remediation.**
Use `DEFAULT_PERIODS` that match production: e.g., `uint96(600 + (3600 << 24) + (28800 << 48) + (86400 << 72))`. If the tests deliberately use short periods for unit-test determinism, document the intent explicitly and add a companion test with production periods to ensure tests also pass in the long-period regime.

**Why P1.** Tests validated against non-production parameters give false confidence. A production misconfiguration (spot=100 by typo) would pass every test and deploy.

---

## Part 3 — NEW P2 Findings

### N-07 P2 — FFI supply-chain: DuckDB snapshot is untrusted ground truth

**File:** `contracts/test/_ffi_utils/ffiLib.sol` + `contracts/scripts/ran_ffi.py` + `contracts/data/ran_accumulator.duckdb`

The entire differential test regime compares on-chain state against rows pulled from a local DuckDB file. The file is an artifact with no integrity check:

- No checksum verification in `ffiPython`.
- No signing or commit pinning of the snapshot contents.
- No schema assertion in `decodeRow` / `decodeRange` (Solidity side) or in `ran_ffi.py` (Python side).
- `ran_data_api.py` is presumably well-tested, but no contract test verifies it returns truthful data vs. a known-correct reference.

A developer who regenerates the snapshot with a bug, or a malicious PR that seeds arbitrary values, can silently change the "expected" side of every differential assertion. The tests would green.

**Remediation.**
1. Commit a `data/ran_accumulator.duckdb.sha256` checksum and verify in `BaseForkTest.setUp`.
2. Assert `decodeLen > 0` and a known-constant value for a pinned block (e.g. `row[0].blockNumber == <pinned>`).
3. Document in `ffiLib.sol` the trust model.

**Why P2.** Low probability, high impact. CI and manual review are the existing barrier; a signed snapshot is a defense-in-depth.

---

### N-08 P2 — `setUp` doesn't `vm.makePersistent` `consumer` in integration test's buffer

**File:** `contracts/test/integration/AngstromRANPipeline.diff.t.sol` L99-101

The test does:
```solidity
pipeline = new MockRANPipeline(BUFFER_CAPACITY, consumer, USDC_WETH);
vm.makePersistent(address(pipeline));
```

`pipeline` stores `consumer` by immutable reference. `vm.makePersistent(address(consumer))` at line 97 persists `consumer`'s bytecode across fork rolls. Good.

But consider: what happens if a test calls `vm.rollFork` to a block where `address(consumer)` has pre-existing mainnet code that differs from the persistent test bytecode? Foundry documentation indicates `vm.makePersistent` takes precedence, but this is a known footgun. More concretely: `AngstromAccumulatorConsumer` is newly deployed at a test-chosen address (CREATE). If that address collides with a mainnet contract at some block, behavior is undefined.

In practice the CREATE address is determined by deployer nonce at setUp time (on a forked chain, the deployer EOA is fresh). Collision risk is negligible. But the test has no assertion that `address(consumer).code.length > 0` after each `rollFork`, so a "Foundry persistence bug" regression would silently break the test.

**Remediation.**
```solidity
assertGt(address(consumer).code.length, 0, "consumer code lost after rollFork");
```
at the top of each test using the consumer post-rollFork.

**Why P2.** Future Foundry versions have had persistence bugs. Defensive invariant. Low impact if `vm.makePersistent` works as advertised.

---

### N-09 P2 — `test__fuzzSecurityEdge__EMA_FuturePackReverts` bounds break at 24-bit wrap boundary

**File:** `contracts/test/libraries/transformations/EMAGrowthTransformationLib.diff.t.sol` L92-94

```solidity
uint256 maxOffset = uint256(type(uint24).max) - uint256(currentEpoch);
futureOffset = uint24(bound(uint256(futureOffset), 1, maxOffset));
```

If `currentEpoch = type(uint24).max` (the moment of the wrap), `maxOffset = 0`, then `bound(x, 1, 0)` — Foundry's `bound` reverts on `min > max`. The test spuriously fails when run at a block whose timestamp puts `currentEpoch` at the wrap boundary.

The fork setup typically uses a fixed `BLOCK_NUMBER_0`, so the actual `currentEpoch` at test time is deterministic. But any future change to `BLOCK_NUMBER_0` (e.g., re-forking to the latest block) could hit this boundary.

Also coupled with N-01: if F-01 is rewritten to allow small forward offsets (as the remediation suggests), the test needs to be updated to bound `futureOffset` above the new allowed-window threshold.

**Remediation.**
```solidity
vm.warp(10_000);  // deterministic; makes currentEpoch = 156
uint24 currentEpoch = uint24((block.timestamp >> 6) & 0xFFFFFF);
// ... now maxOffset is stable
```

**Why P2.** State-dependent test brittleness. Low probability.

---

### N-10 P2 — `GrowthObservation.diff.t.sol` does not assert `rollFork` actually changed block state

The fuzz tests call `vm.rollFork(row.blockNumber)` and then use `block.number` and `block.timestamp`. If `vm.rollFork` silently failed (e.g., RPC timeout with a fallback behavior), `block.number` and `block.timestamp` might be stale. No assertion:
```solidity
vm.rollFork(currRow.blockNumber);
assertEq(block.number, currRow.blockNumber, "rollFork did not advance block");
```

**Why P2.** Defensive. Foundry's `vm.rollFork` reverts on RPC failure typically, but network-side variability has been observed in CI.

---

### N-11 P2 — `test__IntegrationSecurityEdge__C1_ZeroAnchorRevertsEMA` can emit FuturePack under specific fork timestamps

**File:** `contracts/test/integration/AngstromRANPipeline.diff.t.sol` L158-172

```solidity
uint24 currentEpoch = uint24((block.timestamp >> 6) & 0xFFFFFF);
OraclePack stalePack = OraclePackLibrary.storeOraclePack(
    uint256(currentEpoch - 1), 0, 0, int24(0), uint96(0), int24(0), 0
);
```

If `currentEpoch == 0` at fork time (i.e., `block.timestamp < 64`), `currentEpoch - 1` wraps to `0xFFFFFF` (via uint256 underflow constrained to 24 bits by `storeOraclePack`'s internal mask). The stored pack now has `epoch() = 0xFFFFFF > currentEpoch = 0`, so the F-01 FuturePack guard triggers **before** `growthToTick(latest=1e18, oldest=0)` is called. The zero-anchor panic is never reached. The try/catch catches `FuturePack` revert with non-empty `reason`, and:
```solidity
assertEq(reason.length, 0, "expected FullMath bare require (empty revert) for zero anchor");
```
fails.

In practice, the `BaseForkTest` fork block has `block.timestamp >> ~1.74e9`, so `currentEpoch != 0` in normal CI. But:
1. A CI change that uses a different fork block could hit this.
2. A test run without `ALCHEMY_API_KEY` skips via `onlyForked` — which is a silent skip, hiding the regression.
3. The test is fragile under N-01's remediation: if the FuturePack guard is relaxed to allow small forward offsets, the zero-anchor revert reaches `growthToTick` only for packs far enough in the past.

**Remediation.**
```solidity
vm.warp(1e6);  // ensure currentEpoch - 1 does not wrap
uint24 currentEpoch = uint24((block.timestamp >> 6) & 0xFFFFFF);
```

Or explicitly use `_packAtEpoch(currentEpoch - 1)` with a `require(currentEpoch > 0)` sanity.

**Why P2.** State-dependent; low probability in current CI; becomes P1 when F-01 remediation lands.

---

### N-12 P2 — No test of the persistence contract: library return value dropped silently

**File:** all 49 tests, test infrastructure design

`EMAGrowthTransformationLib.updateGrowthEMA` returns an `OraclePack`. The library is stateless; the caller is responsible for persisting the return value. No test verifies what happens if the caller **drops** the return value:

```solidity
m.runUpdate(stalePack, DEFAULT_PERIODS, DEFAULT_CLAMP);  // return value dropped
```

There is no revert, no warning, no diagnostic. The subsequent call sees the unchanged stored `currentOraclePack` and silently rolls back the EMA update. This is not a bug in the library but a contract-design property that no test pins.

A dedicated invariant test would:
1. Call `runUpdate` without storing the return.
2. Call `runUpdate` again with the same stored pack.
3. Observe that both calls returned the same value (no state mutation between).
4. Document that "two consecutive unpersisted calls produce identical output" — i.e., the library is read-only.

**Why P2.** Documentation-level. Useful for integrators. Not a vulnerability of the library itself, but a rakeable foot-gun for consumers.

---

## Part 4 — Fix Regression Check: Round-1 Reported Fixes vs. Current Tests

| Fix              | Round-1 Finding | Current Test                                               | Regression?                                                                                             |
|------------------|------------------|------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| I.2 canary       | Inverted anchor  | `test__IntegrationSecurityEdge__I2_EMAPassesLatestAsCurrentNotAnchor` | **Weak.** Asserts `storedTick > 0` only. A bug producing `storedTick = 1` (off-by-one in `growthToTick` from an inverted arg + sign flip) passes. Should assert byte-exact expected tick. |
| D.4 try/catch    | Descending growth | integration `D4_...` uses try/catch                        | **OK at integration layer.** But N-03 above — the unit test on the same property is NOT forward-compatible and encodes the opposite specification. |
| Empty revert     | `bytes("")` → try/catch + `reason.length == 0` in 3 sites | 3 sites fixed | **OK,** but N-11 above shows fragility under test-timestamp variance. |
| `onlyForked`     | Silent pass      | Uses `vm.skip(true)`                                       | **OK,** Foundry now reports skip in summary. But: `vm.skip` affects test-fork tests only; unit tests without `onlyForked` are unaffected. This is correct. |
| F-01 guard       | Future pack      | Rejects `pack.epoch() > currentEpoch`                      | **BROKEN (N-01).** Legitimate 24-bit wrap now reverts.                                                   |
| F-06 canary      | Negative clamp   | `test__fuzzSecurityEdge__EMA_NegativeClampDeltaCurrentlyAccepted` | **Tautological success assertion.** Under the "current silent behavior" branch, asserts only `returned.epoch() == currentEpoch`, which is true for every non-same-epoch call. A bug that corrupted the EMA while still advancing epoch would pass. |
| HappyPath        | Tautology        | Now asserts non-decreasing growth independently            | **Weakened by N-02.** If the fuzz picks a pre-deployment row, both `old.cg()` and `lat.cg()` are 0; `lat >= old` is trivially true. |
| WorstCase binary | Worst case is `rows[n-2]` | Correctly targets 2nd-oldest              | **OK.** Good fix.                                                                                        |

---

## Part 5 — Coverage Delta vs. Round-1 Recommendations

Of the round-1 proposed canaries (see `security-edge-cases-*.md` + `integration-review-and-flaws.md`):

**Addressed (8):**
- A.2 RelativeTimeDeltaUint16Saturation — partial coverage via two fuzz tests
- B.2 ObserveAtExactlyAtOldestBoundary — `test__fuzzSecurityEdge__ObserveAtExactOldestBoundaryPostWrap` covers post-wrap variant
- C.2 EMAUpdateWithIdenticalOldestAndLatest — covered in `C2_StagnantPool...` integration test (with caveats in integration-review)
- D.4 GrowthDeltaUncheckedWrapOnMisorderedInputs — unit + integration tests
- F.1 SameEpochNoOpIsBitwiseIdentical — covered by `EMA_SameEpochNoOpIsBitwiseIdentical`
- F.2 OraclePackFromFutureProducesGiantTimeDelta — replaced by FuturePack revert test; see N-01
- G.1 (observer) InvertedClampSemantics — partially covered by `EMA_NegativeClampDeltaCurrentlyAccepted`; see N-04's sibling concern
- I.2 InvertedAnchorOrderSilentBug — covered with a weak assertion

**Still missing (9):**
- A.1 BlockNumberUint32BoundaryWrap sequence (type(uint32).max → max+1 → 0)
- A.3 CumulativeGrowthUint208Boundary deterministic boundary
- B.1 ObserveAtAfterMultipleFullWraps with 2560+ pushes + specific revert assertion
- B.3 BinarySearchInvariantUnderKeeperGaps — **N-04** documents the coverage gap
- C.3 EMAUpdateWithCountLessThanTwo distinguishing empty vs uninitialized
- D.1 RecordIdempotencyUnderKeeperRetry deterministic three-call sequence
- D.2 StorageModDiamondSlotCollisionIsolation
- D.3 InitializePoolReentrancyAndDoubleInit
- F.3 EMA_Uint24EpochWrapAroundCorrectness — **N-01** shows this is now critical

**New P0 coverage gaps from round-2 findings:**
- F-01-regression canary (N-01)
- Pre-deployment-row fork invariant (N-02)

---

## Part 6 — Prioritized Remediation

**Immediate (must block production):**
1. **Fix F-01 guard (N-01).** Replace `if (pack.epoch() > currentEpoch) revert` with a bounded forward-gap check. Write the F.3 canary to verify legitimate wrap works.
2. **Add pre-deployment-row invariant test (N-02).** Assert every row in the RAN dataset post-dates `BLOCK_NUMBER_0`. Or filter at the Python layer.
3. **Reconcile D.4 unit vs. integration tests (N-03).** Apply try/catch to the unit test so the F-04 remediation does not break CI.

**Before audit closure:**
4. **Decouple fuzz seeds in BinarySearchUnderKeeperSkipPattern (N-04).** Add `targetSeed` as a second fuzz parameter.
5. **Bound `relativeTimeDelta` inputs in GrowthObservation.diff tests (N-05).** Use `vm.assume(delta <= type(uint16).max)`.
6. **Align DEFAULT_PERIODS with production spec (N-06).** Or add a companion test with production periods.

**Hardening:**
7. Commit DuckDB snapshot checksum (N-07).
8. Assert `consumer.code.length > 0` after each `rollFork` (N-08).
9. Warp to a deterministic `block.timestamp` in `EMA_FuturePackReverts` (N-09).
10. Assert `block.number` changed after `rollFork` (N-10).
11. Warp to a known `currentEpoch > 1` in `C1_ZeroAnchor...` (N-11).
12. Add a persistence-contract read-only-library test (N-12).

---

## Part 7 — Closing Statement

The round-1 remediations improved precision (try/catch, explicit selectors, worst-case targeting) but did not audit the remediations themselves against each other. The F-01 fix (N-01) demonstrates this clearly: the patch resolved one P0 by creating another, and the F.3 canary that would have caught the regression was never implemented.

The deeper structural issue is that the differential-test regime trusts the off-chain oracle (DuckDB snapshot) and the fork-state contract (Angstrom at `BLOCK_NUMBER_0`) as ground truths without pinning either. N-02 and N-07 are the two specific manifestations of this gap; the generalized concern is that the test suite's correctness depends on implicit environmental assumptions (fork timestamp, dataset vintage, deployer nonce) that no test asserts.

Verdict: **NEEDS WORK.** Not shippable to production until N-01, N-02, N-03 are resolved. The rest can ship incrementally.

---

## Appendix — Test Counts by File and New Finding

| File                                                       | Tests | New P0 | New P1 | New P2 |
|------------------------------------------------------------|-------|--------|--------|--------|
| `AngstromAccumulatorConsumer.fork.diff.t.sol`              | 6     | 1 (N-02) | 0    | 1 (N-08) |
| `GrowthObservation.diff.t.sol`                             | 7     | 0      | 1 (N-05) | 1 (N-10) |
| `BlockNumberAwareGrowthObserverLib.diff.t.sol`             | 16    | 0      | 2 (N-03, N-04) | 0 |
| `GrowthToTickLib.diff.t.sol`                               | 10    | 0      | 0      | 0      |
| `EMAGrowthTransformationLib.diff.t.sol`                    | 4     | 1 (N-01) | 1 (N-06) | 1 (N-09) |
| `AngstromRANPipeline.diff.t.sol`                           | 6     | 0      | 0      | 2 (N-11, N-12) |
| Cross-cutting                                              | —     | 0      | 0      | 1 (N-07) |
| **Total new findings**                                      | 49    | **2**  | **4**  | **6**  |
