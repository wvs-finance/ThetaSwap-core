# EMA Differential Test Review — `EMAGrowthTransformationLib.diff.t.sol`

**Reviewer:** Blockchain Security Auditor
**Date:** 2026-04-12
**File under review:** `contracts/test/libraries/transformations/EMAGrowthTransformationLib.diff.t.sol` (4 tests)
**Grounding:** `ema-growth-transformation-lib-btt-spec.md`, `security-edge-cases-ema-transformation.md`, `diff-tests-review-round2.md`
**Scope constraint honored:** EMA-unit concerns only (epoch gate, buffer precondition, oldest-as-anchor composition, unchecked timeDelta, same-epoch bypass). Integration concerns (C.1 zero anchor, C.2 stagnant drift, G.1 negative clamp, I.2 inverted anchor) are explicitly deferred to a separate integration suite.

---

## Verdict

**NEEDS WORK.**

Of the four tests in scope, two give meaningful signal (F.1, F.3), one gives narrow signal with a loose assertion (InsufficientObservationsRevertsBelow2), and one has an **unsound correctness claim in its assertion** — F.2 (`FuturePackProducesWrappedTimeDelta`) asserts only that `returned.epoch() == currentEpoch`, which is true for *every* successful update and therefore proves nothing about the "wrapped time delta" the test name advertises. The test is a false canary: it would pass even if the unchecked subtraction were replaced by a saturating-to-zero subtraction, which would be a silent regression.

In addition, the three coverage gaps the user flagged (H.3 same-epoch-bypasses-buffer-check, buffer==2 boundary, argument-order determinism) are uncovered — and they are all within the stated scope. The suite as committed cannot regression-catch those.

---

## Per-Test Critique

### 1. `test__fuzzSecurityEdge__EMA_SameEpochNoOpIsBitwiseIdentical` — **SOLID (with one hole)**

**What the name claims:** Same-epoch call returns the pack bit-exact (F.1 canary).

**What it actually tests:**
- Fuzzes `arbitraryEpochBits` (uint24), `refTick` (int24), `latestResidual` (int24).
- `vm.warp(uint256(epochValue) << 6)` sets `block.timestamp` to the exact start of `epochValue`'s 64-second window — so `currentEpoch == epochValue` exactly.
- Stores a pack with non-zero orderMap (`0xABC`), non-zero updatedEMAs (`0xDEF`), non-zero currentResiduals (`0x123`), along with the fuzzed `refTick` and `latestResidual`.
- Empty buffer (never populated).
- Asserts `OraclePack.unwrap(returned) == OraclePack.unwrap(original)`.

**Strengths:**
- **Correct use of `unwrap` for byte-identity.** This is exactly what the security report's F.1 prescribes — field-by-field would miss a bit-flip in an uncommonly-read slot.
- Uses non-zero values across multiple slots, so a hypothetical "returns `OraclePack.wrap(0)` on same-epoch" regression would be caught.
- Warp logic is correct: `epochValue << 6` places us exactly at the start of `epochValue`'s window, so the `&0xFFFFFF` mask is exercised correctly.
- Empty buffer + same-epoch is the intended H.3 shape, and this test implicitly verifies that the empty-buffer case does NOT revert on the same-epoch fast path.

**Weaknesses:**
1. **Does not test the mid-epoch boundary.** F.1 recommends also warping by 63 seconds (still inside the same 64-second window) and re-asserting bitwise equality. The current test only hits `timestamp = epochValue << 6`, which is the *exact* epoch boundary. If a future refactor introduced a subtle `<` vs `<=` bug in the epoch computation (e.g., `(block.timestamp + 1) >> 6`), this test would still pass at the boundary but fail at `timestamp + 63`.
2. **Implicitly asserts H.3 without naming it.** The empty buffer + same-epoch combination is the H.3 scenario ("same-epoch early-return skips buffer check"). The assertion is correct, but the test name does not advertise this guarantee, so a reader scanning for H.3 coverage will not find it. Renaming or adding a named sub-assertion would clarify the contract.
3. **Not tested: the complement — one-epoch-ahead warp (`timestamp = (epochValue+1) << 6`) should produce a different pack.** Right now the test only proves "same-epoch is idempotent"; it does not prove "different-epoch is NOT idempotent." A broken library that *always* returns the input would pass this test. Pair-assertion is the defensive pattern here.
4. Fuzz range on `arbitraryEpochBits` (full uint24) is correct and does exercise both ends of the 24-bit space. Good.

**Priority for fix:** P1 (the core assertion is sound; add the 63-second mid-epoch warp and the +1-epoch negative assertion to close the gaps).

---

### 2. `test__SecurityEdge__EMA_InsufficientObservationsRevertsBelow2` — **OK but LOOSE**

**What the name claims:** Revert when buffer count < 2.

**What it actually tests:**
- Empty buffer (count 0), stale pack → expect `InsufficientObservations.selector`.
- Single observation (count 1), stale pack → expect `InsufficientObservations.selector`.

**Strengths:**
- Uses **selector-specific** `vm.expectRevert(InsufficientObservations.selector)` — this is the right pattern, and it correctly distinguishes this revert from, say, `EmptyBuffer`, division-by-zero panic, or any other downstream revert the buffer primitives might throw.
- Tests both the `count == 0` and `count == 1` cases — good boundary coverage on the "below 2" claim.
- Uses a stale pack (`currentEpoch - 1`) so the function bypasses the epoch gate and actually reaches the precondition check. Correct control of the execution path.

**Weaknesses:**
1. **Missing the positive boundary: does the function NOT revert at count == 2?** The test name says "RevertsBelow2," which is a claim about the *exact* boundary. Without an accompanying test that shows `count == 2` succeeds (or at least does not revert with `InsufficientObservations`), a future off-by-one that changes `count < 2` to `count <= 2` (rejecting count == 2 by mistake) would not be caught. The BTT Section 6.1 explicitly names `count == 2` as the minimum-viable case.
2. **No fuzzing over the block numbers / growth values of the single recorded observation.** Arguably not needed (the revert is triggered by count, not content), but using fuzzed `(bn, rtd, cg)` would also catch a hypothetical regression where the library's buffer precondition check accidentally reads observation contents before checking count.
3. **Does not verify the revert does NOT leak state.** Since the function is `view`, this is low-priority — but a sanity check that `block.timestamp` is not unexpectedly mutated (e.g., by a bad cheatcode interaction) would harden the test.
4. **Not testing the `EmptyBuffer` propagation path.** If the library's precondition check were refactored to rely on `oldestObservation()` throwing `EmptyBuffer` instead of the explicit `count < 2` check, the revert selector would change from `InsufficientObservations` to `EmptyBuffer`. This test would correctly FAIL in that case — which is actually the desired behavior — but then the test name misrepresents the guarantee: the guarantee is "reverts with *some* error selector when count < 2," not specifically `InsufficientObservations`. Consider whether the test is pinning the selector (current behavior) or the semantics (caller-visible revert); the BTT spec Section 2.1 is ambiguous on this point.

**Priority for fix:** P1 (add the `count == 2` success case; the existing revert assertions are sound).

---

### 3. `test__fuzzSecurityEdge__EMA_FuturePackProducesWrappedTimeDelta` — **UNSOUND ASSERTION**

**What the name claims:** F.2 canary — pack from the future triggers uint24 subtraction wrap, producing a giant `timeDelta` that corrupts EMAs.

**What it actually tests (and fails to test):**
- Records 2 observations (block 1000 and 1001, growth 1e18 → 2e18).
- Warps to `block.timestamp = 10_000`, computes `currentEpoch = 10_000 >> 6 & 0xFFFFFF = 156`.
- Fuzzes `futureOffset ∈ [1, 2^24 - 2]`, computes `futureEpoch = currentEpoch + futureOffset` (unchecked wrap on overflow).
- Constructs pack with `futureEpoch`.
- Asserts `returned.epoch() == currentEpoch`.

**The problem with this assertion:**

`returned.epoch() == currentEpoch` is the invariant of **every non-same-epoch update path**, regardless of whether the pack was from the future or from the past. The library's step 7 calls `insertObservation(..., currentEpoch, timeDelta, ...)`, and `insertObservation` always stamps the returned pack with the `currentEpoch` it was handed. So:

- If the library is correct (current behavior: unchecked wrap, giant timeDelta, EMAs corrupted) → assertion passes.
- If the library is "fixed" with a saturating subtraction (`timeDelta = max(0, currentEpoch - pack.epoch()) * 64`) → assertion STILL passes because `returned.epoch()` is still `currentEpoch`.
- If the library is "fixed" by rejecting future packs via `require(pack.epoch() <= currentEpoch)` → the call would revert, but the test makes no assertion about revert, so it would FAIL only because of the revert, not because of a mismatched epoch field.

**In other words, this test does not canary the "wrapped time delta" claim at all.** It only proves the function stamps the returned pack with the current epoch, which is a separate and much weaker invariant.

To actually canary F.2, the test must assert something about the EMA state after the update — for example:
- Capture pre-call `spotEMA`, `fastEMA`, `slowEMA`, `eonsEMA`. Note that they are all 0 in the fresh pack.
- After the call, assert that at least one EMA has moved by a magnitude consistent with a giant (~1e9) timeDelta — OR assert the specific numeric EMA value against an off-chain mirror of `updateEMAs` computed with the wrapped timeDelta.
- Alternatively, differential-test against a reference implementation that explicitly wraps, and verify bit-equality of the returned pack.

**Additional issues:**

1. **The fuzz range `[1, 2^24 - 2]` is mostly vacuous.** The distinction between `futureOffset = 1` (wraps to `2^24 - 1`) and `futureOffset = 2^23` (wraps to `2^23`) and `futureOffset = 2^24 - 2` (wraps to `2`) produces *very different* timeDeltas, yet the assertion treats them identically. The fuzzer is doing work that cannot distinguish outcomes.
2. **The 2 recorded observations (growth 1e18 → 2e18) are unused for the assertion.** The test computes a `growthTick ≈ 6931`, clamps it to ±100, feeds it into `insertObservation` — and then throws away all that work by only checking `epoch()`. The test does not verify that the clamped tick reached the EMAs.
3. **Name says "produces wrapped time delta" but nothing about the time delta is measured.** The word "produces" in the test name implies an observable effect; the assertion observes only the epoch, which is not the effect.

**Priority for fix:** **P0 — the assertion must be replaced.** This is the single most important test to strengthen. Current behavior: passes whether the library is correct, broken, or silently "fixed." That is the textbook definition of a false canary.

**Concrete fix options (all within scope):**
- (Preferred) Make this a **deterministic** test with a hand-picked `futureOffset = 1` and assert the exact expected EMA output by computing `(2^24 - 1) * 64` off-chain and mirroring `updateEMAs`.
- (Alternative) Compare the returned pack bit-exact against a pack produced by an identically-constructed reference call with the same (wrapped) timeDelta. Differential self-consistency.
- (Weakest but still better) Assert that *at least one* EMA field in the returned pack differs from a control run where `futureOffset = 0` (same-epoch no-op). This at least proves the wrapped path executes.

---

### 4. `test__SecurityEdge__EMA_Uint24EpochWrapAroundAdvance` — **SOLID as a smoke test, WEAK as an F.3 canary**

**What the name claims:** F.3 — 24-bit epoch wrap produces correct advance across the `0xFFFFFF → 0x000000` boundary.

**What it actually tests:**
- Records 2 observations, warps to `block.timestamp = 5 << 6 = 320` → `currentEpoch = 5`.
- Constructs pack with `packEpoch = type(uint24).max - 2 = 0xFFFFFD`.
- Calls `updateGrowthEMA`, asserts `returned.epoch() == 5`.

**Strengths:**
- Exercises the unchecked subtraction across the wrap boundary: `uint24(5 - 0xFFFFFD) = uint24(8)`, so `timeDelta = 8 * 64 = 512` seconds. Correct.
- The scenario is realistic — as the security report notes, on mainnet `block.timestamp >> 6 & 0xFFFFFF` has already wrapped multiple times, so every live pack is on the "post-wrap" side. This test pins that.

**Weaknesses (same class as F.2):**
1. **Same unsound assertion.** `returned.epoch() == currentEpoch` is the generic post-update invariant, not an F.3-specific invariant. A library that wraps correctly passes; a library that wraps incorrectly (e.g., if the unchecked block were removed and Solidity 0.8+ reverted) would *fail at the call site* rather than at the assertion — the test would report a failure, but not because of the epoch assertion it makes.
2. **Does not verify the magnitude of `timeDelta`.** The whole point of F.3 is that the unchecked wrap produces `timeDelta = 8 * 64 = 512`, which is the *correct* small value (not a giant wrapped value). Without asserting anything about the EMA movement, this test cannot distinguish "correct small delta" from "giant wrapped delta that happened to leave the EMA unchanged." The BTT Property 6 (Section 3) is weaker than F.3's claim; this test only verifies Property 6.
3. **Missing the complement case.** The security report's F.3 prescribes **three** cases: before wrap (`currentEpoch = 0xFFFFFE, pack.epoch = 0xFFFFFD`), across wrap (`currentEpoch = 0, pack.epoch = 0xFFFFFD`), after wrap (`currentEpoch = 1, pack.epoch = 0`). The current test only covers a single across-wrap instance (case 2-ish). A single data point does not verify a boundary — it verifies that *a* value in the space works.
4. **Not a fuzz test.** The scenario is fully deterministic, which is fine for a canary, but F.3 naturally wants at least the 3 case-variants above. Making this a parameterized test over `(currentEpoch, packEpoch)` tuples would harden it.

**Priority for fix:** P1 (add the three prescribed sub-cases and assert the timeDelta magnitude via a mirrored off-chain computation; the current assertion is not wrong, just insufficient).

---

## Cross-Cutting Issues (apply to all four tests)

### CS-1 No `vm.label` / no failure-message discipline

None of the four tests use `vm.label` for the `MockEMABuffer`, and failure messages are minimal (e.g., `"same-epoch: pack must be returned bit-exact"`). Under fuzz failure the reproducer will not clearly identify which test path failed. Minor, but worth noting for debugging ergonomics.

### CS-2 `DEFAULT_PERIODS` packs four values of `100` — below the spec's minimum of 64 × epoch

The spec (Section 9, Fuzz Input Ranges) says `EMAperiods` slots should be `>= 64` (spot), `>= 256` (fast), etc. The test's `DEFAULT_PERIODS = uint96(100 + (100 << 24) + (100 << 48) + (100 << 72))` uses 100 for every slot, which satisfies the spot minimum but is **below** the fast/slow/eons minimums. If `OraclePackLibrary.updateEMAs` has any internal assertion on period ordering (spot < fast < slow < eons), this could cause silent different behavior than production. Confirm by reading the update path, or switch to a spec-compliant default.

### CS-3 No assertion on `oldest` being used as anchor (no composition test)

This is a scope-gap, addressed in the proposals below. The library's growthToTick call argument order is structural — nothing in the existing suite would catch a swap of `latest.cumulativeGrowth()` and `oldest.cumulativeGrowth()` in line 57 of the library. The user's scope explicitly includes this. Not covered.

### CS-4 `MockEMABuffer.runUpdate` is `view` — good, but fuzz tests re-deploy the mock per run

Each fuzz iteration calls `new MockEMABuffer(BUFFER_CAPACITY)`. For fuzz tests without pre-populated buffers (test 1), this is trivial. For tests 3 and 4 (pre-populated with 2 observations), it is correct but slow — the storage reset per iteration is fine for correctness but worth a note on runtime. Not a correctness issue.

### CS-5 No integration between `vm.warp` and `vm.roll`

`vm.warp` changes `block.timestamp` but not `block.number`. The library does not read `block.number`, so this is fine. However, the recorded observations in tests 2, 3, 4 use hard-coded block numbers (`1000, 1001`) that are unrelated to the warped timestamps. If a future refactor of the library introduced a `block.number` consistency check (which the observer layer has), this decoupling would cause spurious failures. Note for integration-test design.

---

## Proposed Additional Tests — In-Scope Coverage Gaps

The user's scope explicitly includes: epoch gate edge cases, buffer count == 2 boundary, H.3 same-epoch-bypass, returned-pack invariants, idempotence, and ordering-of-growthToTick-arguments. The four tests committed do not cover these. Below are the proposals — names, scenarios, assertions, priorities. No Solidity code.

---

### PROPOSAL A. `test__SecurityEdge__EMA_EpochZeroBothSidesNoOp` — **P1**

**Scope:** Epoch gate edge case.

**Scenario:** Warp `block.timestamp = 0` (so `currentEpoch = 0`). Construct pack with `epoch = 0` and non-zero values in every other slot. Empty buffer.

**Assertion:** `OraclePack.unwrap(returned) == OraclePack.unwrap(original)`. The same-epoch fast path must handle the `0 == 0` case identically to the general case (no off-by-one, no "uninitialized" misinterpretation of epoch 0). Paired with the existing F.1 test, this proves the epoch gate is uniform across the full uint24 range including the zero boundary.

**Why needed:** Epoch 0 is a special value in many protocols (sentinel for "uninitialized"). If a future refactor adds `if (pack.epoch() == 0) { /* treat as uninitialized */ }`, this test would fail, exposing the semantic change.

---

### PROPOSAL B. `test__SecurityEdge__EMA_CountEqualsTwoDoesNotRevert` — **P0**

**Scope:** Buffer count == 2 boundary (the positive complement of test 2).

**Scenario:** Empty buffer, record exactly 2 observations with strictly-different `cumulativeGrowth` (e.g., 1e18 → 2e18). Warp to a new epoch (different from pack.epoch). Call `updateGrowthEMA`.

**Assertion:**
1. The call does NOT revert (no `InsufficientObservations`, no downstream `EmptyBuffer`).
2. `returned.epoch() == currentEpoch`.
3. `OraclePack.unwrap(returned) != OraclePack.unwrap(original)` — proves the update path executed (negative assertion, cheap, effective).

**Why needed:** Paired with the existing `InsufficientObservationsRevertsBelow2`, this pins the exact boundary at `count < 2`. Without this, a regression `count <= 2` would not be caught. BTT Section 6.1 names this as the minimum-viable case.

---

### PROPOSAL C. `test__SecurityEdge__EMA_SameEpochBypassesBufferCheckEvenWithCountOne` — **P0**

**Scope:** H.3 scenario — same-epoch early-return bypasses buffer precondition (explicitly in scope per user).

**Scenario:** Record exactly 1 observation (would revert on the new-epoch path). Construct pack with `pack.epoch() == currentEpoch`. Call `updateGrowthEMA`.

**Assertion:**
1. No revert (the same-epoch path short-circuits before the buffer check).
2. `OraclePack.unwrap(returned) == OraclePack.unwrap(original)` — pack is returned bit-exact.
3. Also run the same scenario with `count == 0` (empty buffer) — same assertion holds.
4. **Negative complement:** In the SAME test (or an immediately adjacent one), warp by 64 seconds and re-call with the same 1-observation buffer. Assert the call NOW reverts with `InsufficientObservations.selector`. This proves the behavior is state-dependent on the epoch gate, not a bug in the precondition check.

**Why needed:** H.3 is explicitly named in the user's scope. It also documents an intended behavior (epoch-gate-before-precondition) that is easy to accidentally reverse during refactors. Without this test, a future refactor that moves the precondition check to the top of the function (per the security report's recommendation #6) would *silently* break the gas-hot-path contract that callers may rely on. This test locks in the current contract; a refactor would then be an intentional, reviewed change.

---

### PROPOSAL D. `test__fuzzSecurityEdge__EMA_ReturnedEpochAlwaysCurrentNotPack` — **P1**

**Scope:** Returned pack invariant — epoch should be `currentEpoch`, not `pack.epoch()`.

**Scenario:** Fuzz `packEpoch` (uint24), fuzz `currentEpochOffset` (int32 in a bounded range). Warp to a chosen `block.timestamp`, construct pack with the fuzzed `packEpoch`, record 2 observations, call update. Skip iterations where `packEpoch == currentEpoch` (that is F.1's domain).

**Assertion:** `returned.epoch() == currentEpoch` for every non-same-epoch iteration. Additionally, `returned.epoch() != pack.epoch()` unless they coincidentally match `currentEpoch`.

**Why needed:** F.2 and F.3 each hit a specific point in this space. A fuzz test that sweeps the space confirms the invariant is global, not just at hand-picked points. Paired with PROPOSAL F below, this also provides the asserting signal that the F.2 test currently lacks.

---

### PROPOSAL E. `test__SecurityEdge__EMA_TwoSequentialSameEpochCallsBitwiseIdempotent` — **P1**

**Scope:** Idempotence within an epoch (BTT Property 1, named in user scope).

**Scenario:** Build a valid buffer (2+ observations). Warp so `currentEpoch == pack.epoch`. Call `updateGrowthEMA` once, capture the returned pack. Call `updateGrowthEMA` again on the returned pack (no `vm.warp` between). Capture the second return.

**Assertion:** `OraclePack.unwrap(firstReturn) == OraclePack.unwrap(secondReturn) == OraclePack.unwrap(original)`. Three-way bit-equality proves the operation is idempotent *and* the first call made no hidden state change that the second call would observe.

**Why needed:** Property 1 of the BTT is stated as "returns unchanged," not "is idempotent across sequential calls." The stronger statement (idempotence) is what the library must actually guarantee; the current F.1 test verifies only one call. A regression where the function returns an updated pack (with, say, a bumped residual) and then returns the SAME updated pack on the second call would pass F.1 (each call individually matches its input), but fail idempotence unless the input to call 2 is the output of call 1 — which this test explicitly sets up.

Actually — on reflection, this is subtly wrong as stated: the second call's input IS the first call's output, and if the first call returned a modified pack, the second call's `pack.epoch()` would equal the modified pack's epoch, which should still equal `currentEpoch`, so the second call returns the modified pack again. This test is therefore equivalent to F.1 under the current implementation. **Re-scope this proposal to a DIFFERENT epoch:** call once in epoch N, warp 64 seconds, call again in epoch N+1 (both times with valid buffer), and assert the SECOND call's return has `epoch() == N+1` while the first's has `epoch() == N`. That tests the transition, not the idempotence. The true idempotence is F.1 itself; this proposal is redundant with PROPOSAL F below. **Dropped; use F instead.**

---

### PROPOSAL F. `test__SecurityEdge__EMA_SameEpochMultipleCallsAreBitwiseStable` — **P0, replaces E**

**Scope:** Combines idempotence (user scope) with the missing F.1 negative complement (identified in test 1 weakness 3).

**Scenario:** Build a valid buffer. Construct a pack with arbitrary non-zero sub-fields and `epoch = E`. Warp to three timestamps in sequence:
1. `block.timestamp = E << 6` (start of epoch E). Call update on the original pack. Capture `result1`.
2. `block.timestamp = (E << 6) + 63` (end of epoch E, still same epoch). Call update on `result1`. Capture `result2`.
3. `block.timestamp = (E + 1) << 6` (start of epoch E+1). Call update on `result2`. Capture `result3`.

**Assertions:**
1. `OraclePack.unwrap(result1) == OraclePack.unwrap(original)` (same-epoch no-op at lower boundary).
2. `OraclePack.unwrap(result2) == OraclePack.unwrap(original)` (same-epoch no-op at upper boundary).
3. `OraclePack.unwrap(result3) != OraclePack.unwrap(original)` (different-epoch DID update).
4. `result3.epoch() == E + 1`.

**Why needed:** This closes three gaps simultaneously — the mid-epoch boundary (test 1 weakness 1), the negative complement proving "different epoch is NOT idempotent" (test 1 weakness 3), and idempotence within a single epoch (user scope). One test, high return on investment.

---

### PROPOSAL G. `test__SecurityEdge__EMA_OldestPassedAsAnchorNotLatest` — **P0**

**Scope:** Growth → tick argument ordering. The library calls `growthToTick(latest.cg, oldest.cg)`. A regression swapping the order produces a negative tick with the same magnitude (per GrowthToTickLib's sign symmetry). User scope explicitly names this gap.

**Scenario:** Deterministic setup — no fuzz.
- Record observation 1: `(bn=1000, rtd=0, cg=1e18)`.
- Record observation 2: `(bn=1001, rtd=12, cg=2e18)`.
- `oldest.cg = 1e18, latest.cg = 2e18`. Ratio = 2 (latest/oldest), which maps to a KNOWN positive tick ≈ +6931. The INVERTED ratio = 0.5 (oldest/latest), which maps to a KNOWN negative tick ≈ -6931.
- Warp to a new epoch. Construct pack with `lastTick = 0`, `clampDelta = MAX_INT24` (no clamping), all EMAs = 0.
- Call update.

**Assertion:**
1. Compute the expected post-insertObservation residual via the OraclePack bit layout: residual = clampedTick - referenceTick. With referenceTick starting at 0, residual = clampedTick.
2. Extract `latestResidual` from the returned pack (bottom 12 bits, interpreted as int12 — or retrieve via the library's accessor if one exists; otherwise decode manually).
3. Assert `latestResidual > 0` (strictly positive). An inverted-argument regression would produce `latestResidual < 0`.

**Alternative formulation if the 12-bit residual decode is awkward:** After the call, read any of the EMA fields. With all EMAs starting at 0 and a large clampDelta, the first update will pull each EMA toward `clampedTick`. If `clampedTick > 0`, at least one EMA will be `> 0` after the update. If the args were inverted, `clampedTick < 0` and every EMA would be `< 0`. **Assert spotEMA > 0.**

**Why needed:** I.2 from the security report. Argument ordering is structural in the library — no runtime check enforces it. This test is the only protection against a typo/refactor that swaps the args. The user has explicitly included this in scope. Without this test, a two-character edit in line 57 of the library would pass every other existing test.

**Note on scope boundary:** this test does read an EMA field (`spotEMA` or equivalent), which edges into "testing OraclePack math." However, the assertion is only on the **sign** of the resulting EMA, not its magnitude — and the sign is purely a function of the sign of `clampedTick`, which is purely a function of the argument order to `growthToTick`. This is within the spirit of the user's scope: it tests the composition that EMA adds on top, not the OraclePack math itself.

---

### PROPOSAL H. `test__SecurityEdge__EMA_TimeDeltaMagnitudeMatchesEpochDifference` — **P0 (subsumes current test 3)**

**Scope:** Actually canary F.2 and F.3 (current tests 3 and 4 fail to do this).

**Scenario:** Parameterize over `(currentEpoch, packEpoch)` tuples:
- Normal forward: `(100, 50)` → expected `timeDelta = 50 × 64 = 3200`.
- Unit-ahead future (F.2): `(100, 101)` → expected wrapped `timeDelta = (2^24 - 1) × 64 ≈ 1.07e9`.
- Across 24-bit wrap (F.3): `(5, 0xFFFFFD)` → expected `timeDelta = 8 × 64 = 512`.
- Large forward (F.2 variant): `(100, 0x7FFFFF)` → expected wrapped `timeDelta = (100 - 0x7FFFFF) mod 2^24 × 64`.

Record 2 observations with identical growth (`cg_1 == cg_2`) so `growthTick = 0` and `clampedTick = 0`. This isolates the `timeDelta` signal from the `clampedTick` signal.

**Assertion:** For each tuple, compute the expected EMA state analytically (given `updateEMAs(clampedTick=0, timeDelta=T, periods)` with known constants) OR differential-test against a Python mirror of the updateEMAs function. Assert byte-equality of the returned pack against the expected pack.

**Alternative simpler assertion (if full mirroring is heavy):** For the unit-ahead-future case, assert that the returned pack's EMA fields have moved by a magnitude that is quantitatively distinguishable from the normal-forward case — the giant timeDelta forces near-immediate convergence to `clampedTick = 0`, while the small-timeDelta case leaves the EMAs nearly unchanged. `assertApproxEqAbs(eonsEMA_future, 0, tolerance)` vs `assertApproxEqAbs(eonsEMA_normal, originalEMA, tolerance)`.

**Why needed:** Current tests 3 and 4 **both** assert only `returned.epoch() == currentEpoch`, which does not canary what their names claim. This proposal actually tests the timeDelta — the load-bearing invariant of both F.2 and F.3. Current tests should be **replaced** (not added alongside) since their assertion is a strict subset of PROPOSAL H's assertion (H also implies the epoch check, because `updateEMAs` stamps epoch = `currentEpoch` as part of the same pack return).

**Caveat on scope:** this test touches OraclePack EMA math, which the user said is out of scope. **However**, the only way to meaningfully canary F.2/F.3 is to observe the `timeDelta`'s effect on state — and `timeDelta` has no effect on any other field. If the user wants to keep strictly-zero OraclePack math in the test, the fallback is to compare the returned pack bit-exact against a reference call constructed the same way (differential self-consistency with a clean OraclePack) — but that is equivalent to asserting `returned == returned`, which is vacuous. **There is no way to test F.2/F.3 without touching the OraclePack output state.** Recommend the user reconsider the scope boundary for these two tests, or accept that the current tests 3 and 4 are structurally unable to canary their named claim.

---

## Summary — Priority Table

| ID | Test Name | Priority | Status |
|----|-----------|----------|--------|
| (existing 1) | `EMA_SameEpochNoOpIsBitwiseIdentical` | — | **SOLID** (add mid-epoch + negative complement per PROPOSAL F) |
| (existing 2) | `EMA_InsufficientObservationsRevertsBelow2` | — | **OK** (add PROPOSAL B for the positive boundary) |
| (existing 3) | `EMA_FuturePackProducesWrappedTimeDelta` | — | **UNSOUND ASSERTION — REPLACE WITH PROPOSAL H** |
| (existing 4) | `EMA_Uint24EpochWrapAroundAdvance` | — | **WEAK — REPLACE WITH PROPOSAL H** |
| A | `EMA_EpochZeroBothSidesNoOp` | P1 | Add |
| B | `EMA_CountEqualsTwoDoesNotRevert` | P0 | Add |
| C | `EMA_SameEpochBypassesBufferCheckEvenWithCountOne` (H.3) | P0 | Add |
| D | `EMA_ReturnedEpochAlwaysCurrentNotPack` (fuzz sweep) | P1 | Add |
| F | `EMA_SameEpochMultipleCallsAreBitwiseStable` | P0 | Add (subsumes existing 1 if desired) |
| G | `EMA_OldestPassedAsAnchorNotLatest` | P0 | Add (argument-order canary) |
| H | `EMA_TimeDeltaMagnitudeMatchesEpochDifference` | P0 | Add (replaces existing 3 + 4) |

---

## Closing Statement

The four-test suite as committed leaves three P0 gaps open: the argument-order canary (G), the H.3 bypass invariant (C), and a functional canary for the `timeDelta` wrap (H). Tests 3 and 4 have correct setups but inert assertions — they protect against almost no regression that is not also caught by test 1. Reordering priorities: implement G, C, H first; augment test 1 with the mid-epoch and negative complement (PROPOSAL F); add B for the count == 2 boundary. After those five additions the suite rises from "name-matches-scope" to "assertion-matches-name."

**Verdict: NEEDS WORK.** Primary defect: test 3's assertion is semantically empty with respect to its name. Secondary defects: three in-scope gaps (buffer == 2, H.3, arg-order) are uncovered. No further audit findings from the security report at this scope level — the proposals above exhaust the in-scope EMA-unit surface.
