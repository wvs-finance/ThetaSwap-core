# Test Suite Security & Correctness Review — BlockNumberAwareGrowthObserverLib

**Reviewer:** Blockchain Security Auditor
**Date:** 2026-04-12
**File under review:** `contracts/test/libraries/BlockNumberAwareGrowthObserverLib.diff.t.sol`
**Library under test:** `contracts/src/libraries/BlockNumberAwareGrowthObserverLib.sol`
**Type under test:** `contracts/src/types/GrowthObservation.sol`

---

## Verdict: **NEEDS WORK**

The suite demonstrates effort and covers a meaningful set of properties at a surface level, but it is riddled with assertion-name mismatches, silent skips, and fuzz bounds that never exercise the interesting domain. Of 16 tests, I count **at least 10** where the test either (a) does not prove what its name claims, (b) duplicates a weaker check that another test already makes, or (c) has a gas ceiling so loose it will not catch 2x–3x regressions. **Two P0 findings from the original security report are silently unaddressed** (A.1 BlockNumber uint32 boundary near `type(uint32).max`, B.1 multi-wrap behavior beyond 1 wrap). The `onlyForked` modifier converts every test into a no-op when `ALCHEMY_API_KEY` is not set, and that includes tests that **have no dependency on forked state whatsoever** — a CI running without the key would report 16 passing tests while asserting literally nothing.

This suite is not ready to underwrite a production oracle. It needs a second pass before the library is consumed downstream.

---

## Systemic Issues (Apply Across Multiple Tests)

### Issue S-1: `onlyForked` turns the whole suite into a no-op without the env var — **Critical false confidence**

Every single test in the suite carries the `onlyForked` modifier (from `BaseForkTest`). That modifier silently early-returns if `ALCHEMY_API_KEY` is not set. There is no `vm.skip(true)`, no assertion failure, no status distinction in CI — just `console2.log("skipping forked test")` and a green checkmark.

Looking at each test: only **one** of the 16 tests (`ObserveAtFullBufferBinarySearchWorstCase`) actually needs forked state (it calls `ffiPython(rangeArgs(...))` which pulls from the RAN DuckDB). The remaining 15 are pure unit/fuzz tests that construct their own mocks and use `vm.roll` / `vm.warp` to set up state. They do **not** need a mainnet fork. Gating them on `onlyForked` means:

1. A contributor without Alchemy access runs `forge test` and sees green — believing the library is tested.
2. CI without the secret sees green — believing the library is tested.
3. A regression introduced into the library's pure logic **will not be caught** unless someone explicitly runs with the Alchemy key.

**Fix:** Remove `onlyForked` from 15 of the 16 tests. Only `ObserveAtFullBufferBinarySearchWorstCase` legitimately needs a fork (and even that one only because it pulls a DuckDB row that could be read without forking, if the FFI oracle were refactored).

### Issue S-2: The 20,000 gas ceiling is far too loose to be a regression guard

Four tests assert `assertLt(gasUsed, 20_000, ...)`. The BTT spec Section 7 analyzes the binary search at `log2(256) = 8 SLOADs ≈ 8 * 2,100 + overhead ≈ 17–18k gas` on a cold cache, or ~`8 * 100 + overhead ≈ ~1–2k gas` on a warm cache. Inside a Forge test the cache is warm after the first push. The actual gas used by `observeAt` over a full buffer is typically **1,500–4,000 gas**.

A 20,000 gas ceiling leaves **5–13x headroom**. A regression that turns the binary search into a linear scan (256 SLOADs, each 100 warm = 25,600 gas) would **fail this assertion only marginally** — and a subtler regression (say, quadratic rebalancing in a future refactor introducing extra SLOADs per level — `8 levels × 4 SLOADs = 32 × 100 = 3,200 gas`) would **silently pass**. The ceiling should be derived from observed production gas plus a tight delta (e.g., `observed * 1.25` or a hardcoded `6000` based on empirical measurement), not a round number chosen for comfort.

**Fix:** Record baseline gas via `snapshot` and assert tight bounds; alternatively use Foundry's `--gas-report` + a dedicated `.gas-snapshot` file.

### Issue S-3: BTT fuzz tests use block numbers starting at `block.number`, which on a fork is ~current-mainnet

Tests like `DescendingBlockOrderingInvariant`, `CountSaturatesAtCapacity`, `ObserveAtMonotonicity`, and `BinarySearchUnderKeeperSkipPattern` use `uint256 startBlock = block.number`. On a fork pinned to mainnet at ~block 20M, `startBlock + BUFFER_CAPACITY * 5 = 20_000_000 + 1280 < type(uint32).max`, so it fits. But the tests **never exercise** values close to `type(uint32).max`, meaning the uint32 narrowing boundary (P0 finding A.1 from the original report) is never hit. More subtly: the tests implicitly depend on `block.number` being reasonable, which is a brittle coupling.

---

## Per-Test Critique

### 1. `test__fuzzDifferential__ObserveAtFullBufferBinarySearchWorstCase`

**Name claim:** Worst-case gas + correctness for binary search over a full buffer.

**What it actually does:** Loads 256 rows from the Python oracle, records them, calls `observeAt(rows[1].blockNumber)`, asserts the returned row matches and gas < 20,000 and span > 1800s.

**Problems:**
- "Worst case" is never justified. The binary search worst case for `observeAt` is **the target that sits at maximum search depth** (typically an odd index in the middle of the buffer, not index 1). Index 1 from the top is actually a **near-best** case — the search converges in ~1–2 iterations because `low=1, high=255, mid=128`, and `obs[128].blockNumber > rows[1].blockNumber`, so `low=129`, etc. The test does not probe the actual worst case. Rename or restructure to iterate over multiple targets and assert the max gas across all of them.
- The `spanSeconds > 1800` assertion depends on the DuckDB fixture data, not on the library. If the FFI oracle returned 256 rows from a 5-minute window, this assertion would fail and the user would blame the library. Weakly coupled.
- Gas ceiling 20,000 — see S-2.
- Depends on `onlyForked` — see S-1 (this one is legitimate).

**False confidence rating:** Medium. The name promises worst-case; the test delivers average-case.

### 2. `test__fuzzDifferential__ObserveAtProductionCadence30MinCoverage`

**Name claim:** The buffer provides ≥30 minutes of history under 12s production cadence.

**What it actually does:** Constructs 256 observations at 12s spacing, calls `observeAt(startBlock + 1)`, asserts the row is correct and `productionSpanSeconds > 1800`.

**Problems:**
- The `productionSpanSeconds > 1800` assertion is a **tautology** — `(256 - 1) * 12 = 3060 > 1800` is determined entirely by the Solidity-level constants `BUFFER_CAPACITY` and `BLOCK_TIME_SECONDS`. It proves nothing about the library; it proves that 255 × 12 > 1800. Delete the assertion or convert it to a `console2.log` annotation. If you want a regression guard on capacity configuration, write a separate compile-time `assert(BUFFER_CAPACITY * BLOCK_TIME_SECONDS > 30 minutes)`.
- Like test 1, `observeAt(startBlock + 1)` is a near-best-case search target, not worst-case.
- The name claims "production cadence" but nothing validates that the observed cadence **is** production cadence — the test literally constructs it. This is a scenario, not an invariant.

**False confidence rating:** High. The key numerical assertion is a tautology and the correctness assertion tests a friendly case.

### 3. `test__fuzzDifferential__ObserveAtPostWrapGasStability`

**Name claim:** Gas stability after the buffer wraps.

**What it actually does:** Pushes `bound(wrapSeed, 257, 2560)` observations, then queries for the oldest-surviving block + 1.

**Problems:**
- Gas is bounded by < 20,000 — see S-2.
- "Stability" suggests measuring variance across many wrap depths; the test asserts only the **upper bound** on a single invocation. A regression that makes gas spike at exactly `totalPushes = 512` would only fail if the spike exceeds 20k — otherwise "stability" holds by the test's own definition. Consider snapshotting gas across multiple wrap depths and asserting the delta is small (< 500 gas).
- Like tests 1 and 2, `oldestSurvivingIdx + 1` is near one end of the buffer — not a worst-case search.
- `bound(wrapSeed, BUFFER_CAPACITY + 1, BUFFER_CAPACITY * 10)` = 257–2560 pushes. This never exercises **high wrap counts** (e.g., 100+ wraps). The original security report's B.1 explicitly asked for 10 full wraps (2560 pushes) as the **minimum** — so 2560 is the ceiling here, which aligns. But 257 (one wrap + 1) and 2560 behave identically mathematically — the modulo arithmetic doesn't care. A fuzzer picking evenly across [257, 2560] will mostly pick values that behave the same as a single wrap. Consider exponentially-distributed wrap depths.

**False confidence rating:** Medium. Tests a real thing, but the measurements are too loose to detect a 2–3× regression.

### 4. `test__fuzzSecurityEdge__RelativeTimeDeltaInRangeRoundTrips`

**Name claim:** In-range `relativeTimeDelta` round-trips correctly through the bit-packed slot.

**What it actually does:** Records two observations with varied `relTimeDelta`, asserts `latest().relativeTimeDelta() == relTimeDelta`.

**Problems:**
- **Only `latest()` is checked.** The test name implies "round trip" — which should also verify `observeAt` retrieval and `oldest()` retrieval. If the packing logic broke during the shift-into-higher-slot path (say, a bitmask mis-typed), `latest()` could be correct (reading from the most-recent SLOAD) while `observeAt` at an index returns garbage. Strengthen: also call `observeAtTarget(1001)` and `oldest()` and assert their `relativeTimeDelta()` values match.
- Fuzz range `[0, uint16.max]` is the full valid range — good.
- `relativeTimeDelta` at the exact boundary value `uint16.max` should be checked explicitly with a dedicated assertion, not just left to the fuzzer (which will hit it probabilistically with very low hit rate among 65k values). Follow the BTT spec's "boundary value" convention and add `type(uint16).max` as a specific vector.

**False confidence rating:** Low. Mostly fine, but incomplete.

### 5. `test__fuzzSecurityEdge__RelativeTimeDeltaOverflowReverts`

**Name claim:** Over-range `relTimeDelta` reverts via SafeCastLib.

**What it actually does:** Records a base observation, then records a second with `relTimeDelta > uint16.max`, expects `SafeCastLib.Overflow.selector`.

**Problems:**
- Correct intent, clean implementation, good boundary.
- **But**: the test does not verify that when the revert occurs, the **buffer is not corrupted**. After a revert, `count()` should still be 1, `latest()` should still be the first observation, etc. Solidity reverts unwind state, but this is a library that writes to storage — a careful auditor still wants to assert post-revert state. Add: `assertEq(m.count(), 1); assertEq(m.latest().blockNumber(), 1000);` after the revert.

**False confidence rating:** Low. Correct on the narrow claim, misses the broader invariant.

### 6. `test__fuzzSecurityEdge__BlockNumberInRangeRoundTrips`

**Name claim:** In-range `blockNumber` round-trips through bit-packing.

**What it actually does:** Records a single observation with `bound(bn, 0, uint32.max)`, asserts `latest().blockNumber() == bn`.

**Problems:**
- `bn = 0` is **a reachable-but-nonsensical** case. `record()` will accept `blockNumber = 0` as the first observation. Nothing wrong with the test — but note that in production, block 0 is the genesis block and passing it is a keeper bug. The BTT spec Section 1.1 notes this case but does not specify the desired behavior. The test silently accepts it.
- Same weakness as test 4: only `latest()` is checked; `oldest()` and `observeAt` are not.
- Does not verify `blockNumber = uint32.max` as a specific vector (relies on the fuzzer rarely finding it).

**False confidence rating:** Low. Same pattern as test 4.

### 7. `test__fuzzSecurityEdge__BlockNumberOverflowReverts`

**Name claim:** Block numbers exceeding `uint32.max` revert on record.

**What it actually does:** `bound(bn, uint32.max + 1, uint256.max)`, expects `SafeCastLib.Overflow`.

**Problems:**
- **This test does NOT satisfy P0 finding A.1 from the original security report.** A.1 is specifically about the behavior **near** `uint32.max` — i.e., `record(uint32.max - 1)` followed by `record(uint32.max)` followed by `record(uint32.max + 1)` to verify the boundary step produces expected behavior (push, push, revert) and that the sequence does not wedge the pipeline. This test only exercises the overflow in isolation on an **empty buffer**. Specifically:
  - It does not verify the pre-boundary push succeeds.
  - It does not verify post-revert buffer state.
  - It does not verify that calling with a stale block number (say, `0`) after the revert still silently skips (the full sequence A.1 asks for).

**False confidence rating:** High. Name suggests "overflow revert is tested," but the critical P0 finding is the sequence — not the isolated revert.

### 8. `test__fuzzSecurityEdge__ObserveAtExactOldestBoundaryPostWrap`

**Name claim:** `observeAt` at exactly the oldest block and one block earlier returns the correct value / reverts.

**What it actually does:** Pushes 257–1024 observations (1–4 wraps), then calls `observeAt(oldestBlock)` (expects success) and `observeAt(oldestBlock - 1)` (expects `ObservationExpired`).

**Problems:**
- Good test in intent. The two-sided boundary is exactly what the BTT spec requires.
- Missing: `observeAt(oldestBlock + 1)`. The original security report's B.2 **explicitly asks for three cases**: `oldest`, `oldest - 1`, and `oldest + 1`. Adding the +1 case closes an off-by-one hole (returns oldest if no entry at +1, returns second-oldest if one exists).
- The assertion `assertEq(uint256(atBoundary.blockNumber()), uint256(oldestBlock))` only checks the block number field. The full 32-byte observation should be compared to `m.oldest()` via `GrowthObservation.unwrap()` (as done elsewhere in the suite). Otherwise a packing bug could let one field round-trip while another is wrong.
- `bound(wrapSeed, BUFFER_CAPACITY + 1, BUFFER_CAPACITY * 4)` — same weakness as test 3, doesn't exercise deep wraps.

**False confidence rating:** Medium. Closest to rigorous among the security-edge tests, but still misses the +1 case and under-asserts.

### 9. `test__fuzzBTT__RecordMonotonicity_DescendingBlocksSilentlySkipped`

**Name claim:** Records with `secondBlock <= firstBlock` are silently skipped.

**What it actually does:** Records at `firstBlock`, then at `bound(secondBlock, 0, firstBlock)`. Asserts count unchanged, latest unchanged.

**Problems:**
- The `bound(secondBlock, 0, firstBlock)` **includes `secondBlock == firstBlock`**. The library's skip condition is `>=` (strict monotonicity required), so the same-block case is correctly skipped. But this is the exact same behavior that `RecordIdempotence_SameBlockDuplicateSkipped` (test 15) tests. This test thus **overlaps with test 15** when the fuzzer picks `secondBlock == firstBlock`. Not a correctness issue, but the two tests are not independent — and the name "DescendingBlocks" is misleading when the same-block case is a valid fuzz pick.
- Consider splitting: `bound(secondBlock, 0, firstBlock - 1)` for the strict-descending case, and a separate dedicated idempotence test for same-block.
- The test does not check that the **second** observation's data (the 12, 2e18 values) did not leak into the latest slot. It only asserts `blockNumber()` and `cumulativeGrowth()` of latest, not `relativeTimeDelta()`. A subtle bug could let one field update while the others don't.

**False confidence rating:** Low. Correct in intent, overlaps with test 15, slightly under-asserted.

### 10. `test__fuzzBTT__CountSaturatesAtCapacity`

**Name claim:** After `N` pushes, `count()` = `min(N, capacity)`.

**What it actually does:** Pushes 1–1280 observations, asserts count equals the expected floor.

**Problems:**
- Clean, good.
- `assertLe(m.count(), BUFFER_CAPACITY)` is **redundant** with `assertEq(m.count(), expectedCount)` when `expectedCount = min(pushCount, BUFFER_CAPACITY)` by construction. If the first assertion passes, the second necessarily does. Delete the second line for clarity.
- Does not verify that after saturation, the **oldest** observation advances (i.e., that the buffer is genuinely FIFO and not silently dropping new pushes once full). Add: record enough pushes to wrap, then check `oldest().blockNumber()` is one of the newer-than-startBlock values, not `startBlock`.

**False confidence rating:** Low. Correct on the narrow count claim, misses the deeper FIFO-behavior claim.

### 11. `test__BTT__EmptyBufferBehavior`

**Name claim:** Empty-buffer reads revert with `EmptyBuffer`.

**What it actually does:** Asserts `count == 0`, `latest()` reverts, `oldest()` reverts.

**Problems:**
- Missing: `observeAt(anyBlock)` on empty buffer. The library explicitly has `if (total == 0) revert EmptyBuffer();` as the **first** check in `observeAt`, and that's a distinct code path from `latestObservation` and `oldestObservation`. Add: `vm.expectRevert(EmptyBuffer.selector); m.observeAtTarget(uint32(0));`
- The `onlyForked` modifier on this test is especially egregious — an empty-buffer test has **zero** dependency on mainnet state.

**False confidence rating:** Low.

### 12. `test__fuzzBTT__RecordThenReadRoundTrip`

**Name claim:** After one record, all three read paths (`latest`, `oldest`, `observeAt`) return the same observation.

**What it actually does:** Records one observation, reads all three, asserts they all match.

**Problems:**
- `bound(bn, 1, uint32.max)` — excludes `bn = 0`. Is that intentional? The library accepts `blockNumber = 0`. Either document why 0 is excluded or include it.
- `growth = bound(growth, 0, uint208.max)` — the boundary value `uint208.max` is covered **probabilistically**. The BTT spec Section 9.3 recommends explicit boundary vectors; the test relies on fuzzer luck.
- The test only writes **one** observation, so `observeAt(bn)` hits the "newest check" early-return (`newest.blockNumber() <= targetBlock`, returns newest). It does **not** exercise the binary-search path. The claim "record-then-read round-trip" does not cover the binary-search read path. Add a second record + a target that's between oldest and latest.

**False confidence rating:** Low-medium. The single-observation case is a degenerate search.

### 13. `test__fuzzBTT__DescendingBlockOrderingInvariant`

**Name claim:** The buffer's slots are strictly descending by block number when iterated via `last(buffer, i)`.

**What it actually does:** Pushes 2–512 observations, iterates, asserts strictly descending.

**Problems:**
- Solid test. This is one of the strongest in the suite.
- `bound(pushCountSeed, 2, BUFFER_CAPACITY * 2)` — good, covers both pre-wrap and post-wrap. Could extend to `* 5` or `* 10` for deeper wraps, but `* 2` is the **minimum** needed to exercise post-wrap ordering.
- Observations are pushed at sequential `startBlock + i` with gap 1 — very regular. The **keeper-skip pattern test** (test 16) covers irregular gaps, but a single fuzz test combining irregular gaps **and** post-wrap ordering would be stronger. As it stands, the ordering invariant is only verified under the regular cadence.

**False confidence rating:** Low.

### 14. `test__fuzzBTT__ObserveAtMonotonicity`

**Name claim:** For `t1 < t2`, `observeAt(t1).blockNumber() <= observeAt(t2).blockNumber()`.

**What it actually does:** Fills buffer to capacity (no wrap), picks two targets in `[oldestBlock, newestBlock]`, asserts monotonic.

**Problems:**
- **Does not exercise post-wrap state.** After a wrap, the oldest slot is in the middle of the array, and the monotonicity invariant is non-trivial to prove. Fill to `BUFFER_CAPACITY` exactly means no wrap ever occurs. This test silently skips the harder case. Change the push loop to `2 * BUFFER_CAPACITY` or use a fuzzed `pushCount`.
- The test only records observations at 1-block spacing — no keeper gaps. Under real operation, block-number gaps are variable.
- `assertLe(r1.blockNumber(), r2.blockNumber())` is correct but weak — the assertion only checks **monotonic**, not **correct**. A bug that returns the same oldest observation for every target would pass this test. Strengthen: for a specific `t1`, verify `observeAt(t1).blockNumber() <= t1` AND `observeAt(t1+1).blockNumber() > observeAt(t1).blockNumber() - 1` (i.e., the returned block is actually the predecessor).

**False confidence rating:** Medium-High. The monotonicity property is weaker than what the name claims, and the degenerate "always returns oldest" implementation would pass.

### 15. `test__fuzzBTT__RecordIdempotence_SameBlockDuplicateSkipped`

**Name claim:** Duplicate same-block records leave the latest observation byte-identical.

**What it actually does:** Records `(bn, 0, 1e18)`, then `(bn, 999, 5e18)`, asserts count and `GrowthObservation.unwrap(latest)` unchanged.

**Problems:**
- Clean, uses byte-level unwrap comparison (unlike test 9). Good.
- Does not verify that `observeAt(bn)` also returns the first observation (not the second). Byte-identical unwrap on `latest` implies the push was skipped, so `observeAt` would be correct by construction — but an explicit check costs nothing and catches regressions.
- This test's coverage **overlaps with test 9** in the `secondBlock == firstBlock` fuzz case. See test 9's critique.

**False confidence rating:** Low.

### 16. `test__fuzzSecurityEdge__BinarySearchUnderKeeperSkipPattern`

**Name claim:** Binary search returns correct predecessor under irregular gaps.

**What it actually does:** Pushes 256 observations at gaps of 1–20 blocks, picks a random target in range, asserts `result.blockNumber() <= target` and gas < 20k.

**Problems:**
- `assertLe(result.blockNumber(), target)` is **not a correctness check** — it only verifies the returned block is at most the target. A degenerate implementation that always returns `oldestBlock` would pass this for any target in range. The **real** correctness property is: `result.blockNumber()` is the **maximum** stored block number that is `<= target`. Strengthen: also iterate through all stored blocks and assert no stored block `b` has `result.blockNumber() < b <= target`. Or compute the expected predecessor from the recorded sequence and assert equality.
- The gap distribution is `1 + (keccak256 % 20)`, i.e., uniform on `[1, 20]`. Real keeper skips are **bimodal**: mostly gap=1 (every block), sometimes very large gaps during outages. The distribution used here does not stress the binary search under the production-realistic pattern.
- Target is `bound(gapSeed, oldestBlock, newestBlock)` — correctly fuzzes over the full domain.
- Gas ceiling 20,000 — see S-2.

**False confidence rating:** High. The weak correctness assertion (`<= target`) is the headline issue — a broken binary search that returns the wrong but older entry would slip through.

---

## Coverage Gaps (Missing Tests)

### Gap G-1: P0 finding A.1 is silently unaddressed

The original security report's P0 finding A.1 — sequential record at `uint32.max - 1`, `uint32.max`, `uint32.max + 1`, `0` — is **not covered**. Test 7 only exercises the isolated overflow revert on an empty buffer. The critical behavioral property (boundary step + post-revert staleness handling) is missing.

### Gap G-2: P0 finding B.1 is only partially addressed

B.1 asked for `observeAt` behavior after **10 full wraps** (2560 pushes), verifying that the oldest eviction + binary search is deterministic. Test 3 exercises up to 10 wraps (2560 pushes) for gas but does not assert `observeAt(originalFirstBlock)` reverts with `ObservationExpired`. The revert-after-many-wraps correctness is untested.

### Gap G-3: No test exercises `observeAt` with `target == latest.blockNumber()` exactly

The library has an early-return: `if (newest.blockNumber() <= targetBlock) return newest;`. This is hit when `targetBlock == newest.blockNumber()`. No test specifically targets this branch — tests that call `observeAt` with the newest block are happenstance rather than intentional. Add a test that records N observations and calls `observeAt(latestBlockNumber)`, asserts the returned observation equals `latest()`.

### Gap G-4: No test exercises `target > latest.blockNumber()`

The same early-return also handles `targetBlock > newest.blockNumber()` (returns newest). No test explicitly exercises this "future target" case. A keeper might legitimately query a target block that is ahead of the latest recording. The BTT spec Section 1.2 mentions this branch.

### Gap G-5: No test verifies `count == 1` single-observation binary search

Test 12 records one observation and checks `observeAt(bn)`, but `bn == target` hits the newest-check early-return, not the binary search. Calling `observeAt(bn - 1)` on a single-observation buffer should revert with `ObservationExpired`. This edge case (BTT spec Section 6.6) is untested.

### Gap G-6: No test verifies `count == 2` binary search

BTT spec Section 6.7 explicitly covers `count == 2`. Not exercised. The binary search loop `while (low < high)` with `low=1, high=1` does not execute, and the result is `last(buffer, 1)` — the oldest of two. A test should record 2 observations at blocks `B, B+10` and call `observeAt(B+5)` expecting `B`.

### Gap G-7: No differential test against the Python oracle for `observeAt` semantics

`ffiLib.sol` provides `rangeArgs` and `decodeRange` helpers to pull rows from the DuckDB. The one differential test uses the oracle only to **populate** the buffer, then calls `observeAt` without cross-checking against an off-chain "expected predecessor" computation. A true differential test would:
1. Pull N rows from the oracle.
2. Record them into the buffer.
3. For each random target, compute the expected predecessor **in Python** (or in Solidity via linear scan), call `observeAt`, assert equality.
This is the class of test the file's `.diff.t.sol` naming suggests is present — but it is not.

### Gap G-8: No post-revert buffer-state tests

After any `SafeCastLib.Overflow` revert (tests 5, 7) or `ObservationExpired` revert (test 8), no test verifies the buffer is unchanged. Solidity reverts unwind storage, but defensive tests should confirm it.

### Gap G-9: No test for `relativeTimeDelta` accumulation correctness over many records

The BTT spec Section 3 Property 7 describes round-trip. But `relativeTimeDelta` is **caller-provided** (per natspec 8.4), and a test should record a sequence where the cumulative `relTimeDelta` reconstructs the real time between first and last observation. No test exercises this semantic.

### Gap G-10: No gas snapshot for `record()`

All gas assertions are for `observeAt`. No gas ceiling on `record()`. A regression that adds a SLOAD-heavy invariant check to `record` would silently pass.

---

## Tests That Should Be Strengthened (Specific Changes)

| Test | Change |
|------|--------|
| 1 (WorstCase) | Iterate across all 256 indices as targets; assert `max(gasUsed) < 6_000` (tight, based on empirical 1,500–4,000 gas observation). |
| 2 (Production) | Delete the tautological `productionSpanSeconds > 1800` assertion. Replace with `assertEq(observeAt(startBlock + k).blockNumber(), startBlock + k)` for several `k`. |
| 3 (PostWrap) | Add assertion that `observeAt(startBlock)` reverts with `ObservationExpired` (the oldest was evicted). Tighten gas ceiling to ~6k. |
| 4, 6 (RoundTrip) | Also assert field values via `observeAt()` and `oldest()`. Explicitly test boundary values (0, type(uint16).max for delta; 0, type(uint32).max for blockNumber). |
| 5, 7 (Revert) | After the expected revert, assert buffer state is unchanged (count, latest byte-identical). |
| 7 (BlockOverflow) | Replace with full P0 A.1 sequence: push `uint32.max - 1`, push `uint32.max`, push `uint32.max + 1` (expect revert), push `0` (expect silent skip). Verify final state. |
| 8 (ExactOldest) | Add third case `observeAt(oldestBlock + 1)`. Compare full 32-byte unwrap. |
| 9 (Monotonicity) | Split `bound(secondBlock, 0, firstBlock - 1)` to remove overlap with test 15. Also assert `relativeTimeDelta` unchanged. |
| 10 (CountSaturate) | Delete redundant `assertLe`. Add FIFO check: after saturation, verify `oldest` has advanced. |
| 11 (EmptyBuffer) | Add `observeAt` empty-buffer revert check. Remove `onlyForked`. |
| 12 (RoundTrip) | Record 3 observations, not 1. Exercise the binary search path. Explicitly include boundary values. |
| 13 (DescendingOrdering) | Fuzz the block-gap pattern (1–20) and combine with post-wrap. |
| 14 (Monotonicity) | Use `2 * BUFFER_CAPACITY` pushes to exercise post-wrap. Strengthen assertion: result is the **exact** predecessor (compare to off-chain linear scan). |
| 15 (Idempotence) | Add `observeAt(bn)` check. |
| 16 (KeeperSkip) | Replace `assertLe(result, target)` with exact-predecessor assertion (compute via linear scan). Use bimodal gap distribution. |

---

## False-Confidence Findings (Tests That Look Rigorous But Are Weak)

1. **Test 2 (`ObserveAtProductionCadence30MinCoverage`):** The `productionSpanSeconds > 1800` assertion is a tautology. The name implies an operational property; the test proves `255 * 12 > 1800`.

2. **Test 7 (`BlockNumberOverflowReverts`):** The name suggests P0 A.1 coverage; the test is a degenerate single-revert check on an empty buffer.

3. **Test 14 (`ObserveAtMonotonicity`):** Passes if the library always returns the oldest observation, since oldest ≤ oldest is trivially `<=`. The monotonicity property as written does not establish correctness — it only establishes consistency.

4. **Test 16 (`BinarySearchUnderKeeperSkipPattern`):** `assertLe(result.blockNumber(), target)` similarly passes for a broken implementation that returns any older value. The name promises binary-search correctness; the assertion checks a much weaker property.

5. **Test 3 (`PostWrapGasStability`):** "Stability" is asserted as "< 20,000 gas" — an absolute upper bound, not a stability measure. A measurement that legitimately stabilizes at 3k gas and regresses to stable 19k gas would pass.

6. **The entire suite (`onlyForked` modifier):** Without `ALCHEMY_API_KEY`, all 16 tests silently no-op. For 15 of them this is unjustified — they have no fork dependency.

---

## Priority Actions (in order)

1. **P0 — Remove `onlyForked` from 15 of 16 tests.** Current state is an existential false confidence.
2. **P0 — Replace test 7 with a full P0 A.1 sequence.** The original P0 security finding is unaddressed.
3. **P0 — Strengthen test 14 and test 16 assertions** from `<=` to exact predecessor. These pass for broken implementations.
4. **P0 — Delete tautological assertion in test 2.** It proves nothing.
5. **P1 — Tighten gas ceilings** to ~6k (or empirically derived + 20% margin) and add gas snapshots for `record`.
6. **P1 — Add the missing coverage gaps G-3 through G-7** (`observeAt` early-return branches, `count==1`, `count==2`).
7. **P1 — Add the differential Python oracle check (G-7)** so `.diff.t.sol` earns its filename.
8. **P2 — De-duplicate tests 9 and 15** via explicit range splits.

---

## Summary Numbers

- **16 tests total**
- **1** test is strong (test 13 — DescendingBlockOrderingInvariant)
- **4** tests are roughly correct with minor strengthening needed (tests 5, 10, 11, 15)
- **7** tests have meaningful weaknesses in either assertion breadth or scope (tests 1, 3, 4, 6, 8, 9, 12)
- **4** tests have high false-confidence risk (tests 2, 7, 14, 16)
- **15 of 16** tests silently no-op without `ALCHEMY_API_KEY`
- **1 of 6** P0 findings from the original report is adequately covered (only A.2 — RelativeTimeDeltaUint16Saturation, via tests 4+5); A.1 (BlockNumber uint32 boundary), B.1 (multi-wrap), B.2 (exact oldest boundary, partial) are not fully covered. C.1, C.2, D.4 are out of scope per user note. A.3 was P1, not covered (acceptable for now).

Default verdict: **NEEDS WORK** — recommend a focused second pass addressing the P0 actions above before this suite is considered sufficient coverage for the library.
