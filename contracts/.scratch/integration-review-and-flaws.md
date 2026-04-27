# Integration Test Review & Implementation Flaw Audit — RAN Pipeline

**Reviewer:** Blockchain Security Auditor
**Date:** 2026-04-12
**Scope:**
- Integration test: `contracts/test/integration/AngstromRANPipeline.diff.t.sol` (5 tests)
- Libraries audited: `AngstromAccumulatorConsumer.sol`, `GrowthObservation.sol`, `BlockNumberAwareGrowthObserverLib.sol`, `GrowthToTickLib.sol`, `EMAGrowthTransformationLib.sol`
- Out of scope (per instructions): OraclePack fixes

---

## Part 1 — Integration Test Verdicts

Default verdict grade: **NEEDS WORK** on 3 of 5, **INSUFFICIENT** on 1, **SOLID** on 1.

### Test 1 — `test__Integration__PipelineHappyPath(uint256 startIdxSeed)`

**Verdict: NEEDS WORK — proves almost nothing about the pipeline.**

The test loops over 5 FFI-sourced rows, rolls the fork to each block, and pushes observations via `recordFromOnChain`. Then it builds a stale pack (`currentEpoch - 1`) and calls `runEMA`. The only assertion on the EMA output is `updated.epoch() == currentEpoch`.

Problem: `updated.epoch() == currentEpoch` is the invariant of **every non-same-epoch call** regardless of correctness (the library unconditionally stamps `currentEpoch` into the returned pack via `insertObservation`). This is the same unsound-assertion pattern flagged in the prior EMA test review (`ema-test-review.md` on `FuturePackProducesWrappedTimeDelta`). A broken implementation that returned an uninitialized pack with only the epoch field updated would pass this test.

The test also uses a **fixed `relTimeDelta = 12`** regardless of the actual block-number distance between consecutive FFI rows. If rows 0 and 1 are 5 blocks apart (60s real delta), the observation stores 12s. This decouples the synthetic `relTimeDelta` from the on-chain cadence and invalidates any downstream assumption that `relTimeDelta` reflects real time since the previous observation — which is exactly the weight the EMA uses.

The `count == windowSize` assertion is fine as a smoke check but tautologically follows from 5 monotonically-increasing block numbers and a capacity-256 buffer.

No assertion on the tick that actually fed into the EMA. No assertion on EMA convergence. No fuzz-discrimination between a correct and an incorrect pipeline. The "happy path" is unverified.

---

### Test 2 — `test__IntegrationSecurityEdge__C1_ZeroAnchorRevertsEMA`

**Verdict: NEEDS WORK — revert caught with zero specificity.**

Records a zero-anchor observation (`cg = 0`) followed by a non-zero observation, then expects the EMA update to revert. The assertion is `vm.expectRevert(bytes(""))` — i.e. expect **any** revert with empty data.

This catches the current behavior (EVM Panic 0x12 from FullMath div-by-zero), but it also catches:
- A revert from `InsufficientObservations` if someone silently broke `record()` to skip the first observation.
- A TickMath `InvalidSqrtPrice(0)` if a refactor of `growthToTick` returned 0 on zero-anchor instead of panicking.
- A `SafeCastLib.Overflow` from any path.
- An OOG failure.
- A revert from `StaleObservation` or any other error in `GrowthObservation.sol`.

The security report `security-edge-cases-ema-transformation.md` E.1 is explicit: the canary should be `vm.expectRevert(stdError.divisionError)` — Panic 0x12 specifically. As written, the test passes even if the underlying bug is "fixed" by returning 0 (which would be a **silent-miscomputation regression** — the worst class of bug).

Additionally, the C.1 canary in the security report demands **verifying the revert persists for the lifetime of the zero-anchor observation** (up to 51 minutes on a 256-slot buffer). This test checks one call only; it does not pin the DoS window.

---

### Test 3 — `test__IntegrationSecurityEdge__C2_StagnantPoolProducesTick0`

**Verdict: INSUFFICIENT — short-circuits the pipeline.**

The test records two observations with identical `cumulativeGrowth` (stagnant pool), then calls **`growthToTick(lat.cg, old.cg)` directly** and asserts `computedTick == 0`. It then runs `runEMA` and checks `updated.epoch() == currentEpoch`.

Two critical problems:

**(a) The tick-0 assertion never touches `updateGrowthEMA`.** Calling `growthToTick` directly is a unit test of `GrowthToTickLib`, not an integration test of the EMA pipeline. The security report C.2 / E.2 canary is about the **drift of the EMA toward tick 0 over multiple epochs**, not about the immediate return value of `growthToTick`. This test would pass even if `updateGrowthEMA` silently ignored the tick-0 output.

**(b) The second assertion (`updated.epoch() == currentEpoch`) does not prove "the EMA is being pulled toward tick 0."** It proves the pack was updated. The EMA exposure is completely unverified. A correct canary would assert that the returned pack's `spotEMA` moves toward 0 by at most `clampDelta` per call, or that after N iterations the spot EMA is within `[initial - N*clampDelta, initial]` — the bounded-drift invariant.

The test also uses a starting pack with `lastTick = 0` (zeroed), so there is no drift to detect: the EMA is already at 0. Setting the starting pack's `lastTick = 200000` (as the security report prescribes) would make the drift measurable. As written, the C.2 canary cannot distinguish a stagnant-pool drift bug from correct behavior.

---

### Test 4 — `test__IntegrationSecurityEdge__I2_EMAPassesLatestAsCurrentNotAnchor`

**Verdict: NEEDS WORK — proves a property of `growthToTick`, not of the EMA.**

The test computes `correctTick = growthToTick(lat.cg, old.cg)` and `invertedTick = growthToTick(old.cg, lat.cg)`, asserts the former is positive and the latter is negative, then calls `runEMA` and checks `updated.epoch() == currentEpoch`.

The two direct `growthToTick` calls are a unit test of argument-order symmetry — they prove nothing about `EMAGrowthTransformationLib`. The security report I.2 demands proof that the library **itself** calls `growthToTick(latest, oldest)` and not the inverted form. Specifically, it should verify the tick actually fed into `insertObservation` matches `growthToTick(lat, old)` pre-clamp.

As written, a bug that inverted the arguments inside `updateGrowthEMA` would:
1. Compute `invertedTick` (negative).
2. Feed it into `insertObservation`.
3. Update the pack's `epoch()` to `currentEpoch`.
4. **The test would pass** — because the only assertion on the EMA output is the epoch field.

This is a false canary. The two direct `growthToTick` assertions are a sanity check (and a correct one), but they do not protect the EMA pipeline from the I.2 bug class. A proper assertion would either (a) extract the EMA's spot value from the returned pack and assert it moved by a magnitude consistent with `correctTick` post-clamp, or (b) construct a reference pack by manually running the pipeline off-chain and compare `OraclePack.unwrap(returned)` byte-exact.

---

### Test 5 — `test__IntegrationSecurityEdge__D4_DescendingGrowthProducesGarbageTick`

**Verdict: SOLID (strongest of the five).**

Records two observations with `cg = 5e30` then `cg = 1e30` (descending), which is a legitimate scenario under a reorg or Angstrom accounting anomaly. Asserts:
1. `count == 2` — proves `record()` does not reject descending growth (documents the vulnerability).
2. `growthDelta` produces the exact 2^208 - 4e30 wrapped value — **byte-exact expected-value assertion**.
3. `growthToTick(lat.cg, old.cg)` returns a negative tick (the "garbage").

This is the only test in the suite with a specific numeric expectation (`expectedWrap = (1 << 208) - (5e30 - 1e30)`) rather than a loose direction check. That gives it real regression-catching power. The wrapped-delta assertion would catch any change to the uint208 storage width or to `growthDelta`'s unchecked semantics.

**Weaknesses (minor):**
- Does not run `runEMA` to prove downstream corruption. The security report D.4 / G.5 / I.2 canary chain requires showing that a descending growth observation, once it reaches the EMA, corrupts the stored EMA silently. The test stops at `growthToTick`, so it does not close the loop.
- Does not verify the `InsufficientObservations` revert is **not** hit (i.e., proves the descending sample actually reaches the EMA computation path). Adding `runEMA` + a tick-impact assertion would complete the canary.
- The `garbageTick < 0` bound is loose. A more discriminating assertion would compute the expected negative tick from the wrapped ratio in Python and assert byte-exact match.

---

## Part 2 — Integration Coverage Gaps

The five tests, collectively, **do not exercise** the following adversarial conditions that the security reports mark P0:

1. **F.1 — Bitwise identity of same-epoch no-op.** No integration test constructs a pack whose epoch equals `currentEpoch` and asserts the pipeline returns the pack bit-exact. The unit test `test__fuzzSecurityEdge__EMA_SameEpochNoOpIsBitwiseIdentical` covers this for the library alone but not for the full pipeline (where `AngstromAccumulatorConsumer` fork state is live and could be read into the pack).
2. **F.2 — Future-pack time-delta wrap.** No integration test constructs a pack with `epoch() > currentEpoch` and measures the resulting catastrophic single-update convergence. The existing unit test is *unsound* (the prior review flagged it; it was deleted per the file listing).
3. **G.1 — Negative clampDelta silent inversion.** The integration harness hardcodes `DEFAULT_CLAMP = 1000` — the adversarial case `clampDelta = -1` is never exercised.
4. **B.1 / H.2 — Post-wrap oldest correctness.** All 5 integration tests use `count <= 5` observations. The ring buffer never wraps (capacity 256). A bug in `oldestObservation()`'s `last(buffer, total-1)` computation post-wrap would not be caught here.
5. **Persistence contract.** `EMAGrowthTransformationLib` returns an `OraclePack` but does not persist it. No integration test verifies that a caller that fails to persist the return value silently rolls back the EMA update. This is a documentation-level concern but also a real bug class (caller forgets to write-back).
6. **Real on-chain stagnation.** Test C.2 uses synthetic data (`5e30` repeated). A real Angstrom pool can have stretches of no fee accrual. The fork infrastructure (`BaseForkTest`, `rangeArgs`, FFI oracle) is available — the test could be rewritten to query a known-stagnant block range from the FFI dataset and exercise the pipeline against it. The synthetic data short-circuits the validation that Angstrom's real state can produce the stagnation condition.
7. **Composability with `lastBlockUpdated` / `configStore`.** The integration test instantiates `AngstromAccumulatorConsumer` but calls only `globalGrowth`. The other read paths (`growthInside`, `poolExists`, `getPoolConfig`, `lastBlockUpdated`) are not exercised in the pipeline context — specifically, **no test verifies that the pipeline handles a pool that isn't in the Angstrom config store** (an adversarial "wrong pool ID" attack).
8. **Stale keeper / liveness cliff.** A18.2-hour keeper outage overflows `relativeTimeDelta` (uint16). The integration test passes `relTimeDelta = 12` and never stresses the overflow boundary. The unit test covers this — but a keeper-style integration test that sets `relTimeDelta = 65_536` via `recordFromOnChain` (which hardcodes 12) cannot be built with the current `MockRANPipeline`. Add a `recordSyntheticAtCurrentGrowth` helper that exposes the boundary.
9. **TickMath cliff.** No test feeds an on-chain growth pair whose ratio approaches `MAX_SQRT_PRICE` (G.2 boundary). For a real USDC/WETH pool this is unreachable, but a synthetic-data integration test at the boundary would pin the pipeline against a future `TickMath` upgrade.
10. **Multi-pool isolation.** All tests use `USDC_WETH`. If any library accidentally shared state across pools (e.g., a `PoolId` derivation bug in `AngstromAccumulatorConsumer.globalGrowth`'s `deriveMapping`), no integration test would catch it.

---

## Part 3 — Implementation Flaw Audit (library-level)

### Severity Matrix

| ID    | Severity | File                                      | Line(s) | Flaw                                                                                           | Caught by tests?                                |
|-------|----------|-------------------------------------------|---------|------------------------------------------------------------------------------------------------|-------------------------------------------------|
| F-01  | P0       | `EMAGrowthTransformationLib.sol`          | 65-67   | Unchecked `timeDelta` computation silently accepts packs from the future, producing ~10^9s delta | No (unit test was unsound, deleted)             |
| F-02  | P0       | `GrowthToTickLib.sol`                     | 27      | Zero-anchor div-by-zero surfaces as anonymous Panic 0x12 — no named error                      | Partially (Test 2 uses `bytes("")` — too loose) |
| F-03  | P0       | `GrowthToTickLib.sol`                     | 24-37   | No precondition `currentGrowth >= anchorGrowth` — silently returns negative tick on inversion  | No (integration Test 4 unit-tests it only)      |
| F-04  | P0       | `BlockNumberAwareGrowthObserverLib.sol`   | 28-46   | `record()` does not reject descending `cumulativeGrowth` — silent wrap in `growthDelta`         | Partially (Test 5 documents wrap; no guard)     |
| F-05  | P0       | `EMAGrowthTransformationLib.sol`          | 57      | Feeds `latest.cumulativeGrowth()` and `oldest.cumulativeGrowth()` with no monotonicity check   | No                                              |
| F-06  | P0       | `EMAGrowthTransformationLib.sol`          | 42      | `clampDelta` typed as `int24` with no sign validation — negative values silently invert clamp  | No                                              |
| F-07  | P1       | `EMAGrowthTransformationLib.sol`          | 64-67   | `unchecked` block wraps BOTH the subtraction AND the `* 64` multiplication; scope creep         | No                                              |
| F-08  | P1       | `AngstromAccumulatorConsumer.sol`         | 59-68   | `growthInside()` `unchecked` block wraps three separate subtractions; silent on reorg/anomaly   | No                                              |
| F-09  | P1       | `BlockNumberAwareGrowthObserverLib.sol`   | 38      | Silent skip of same-block observations denies the keeper any correction path                    | No                                              |
| F-10  | P1       | `EMAGrowthTransformationLib.sol`          | 45-46   | Epoch gate runs BEFORE buffer precondition — state-dependent error surface (H.3)                | No                                              |
| F-11  | P1       | `GrowthObservation.sol`                   | 79-83   | `growthDelta` signature is `(earlier, later)` — positional ambiguity, easy to invert at call-site | No                                              |
| F-12  | P1       | `AngstromAccumulatorConsumer.sol`         | 42-44   | `globalGrowth` reads `REWARD_GROWTH_SIZE` offset with zero validation of Angstrom storage layout | No                                              |
| F-13  | P1       | `EMAGrowthTransformationLib.sol`          | 60      | `clampTick` is called with a `clampedTick` whose output has no post-bound check vs `MAX_TICK`/`MIN_TICK` | No                                              |
| F-14  | P1       | `EMAGrowthTransformationLib.sol`          | 41      | `EMAperiods` accepted unchecked — zero periods freeze the EMA silently (G.3)                    | No                                              |
| F-15  | P2       | `GrowthObservation.sol`                   | 88-92   | `elapsedBlocks` unchecked — wraps on misordered inputs, no revert on violation                  | No                                              |
| F-16  | P2       | `BlockNumberAwareGrowthObserverLib.sol`   | 86-113  | Binary search has no termination-bound assertion — a corrupted buffer could infinite-loop       | No                                              |
| F-17  | P2       | `AngstromAccumulatorConsumer.sol`         | 97-101  | `poolExists` iterates `totalEntries` unbounded — gas-grief vector if config store bloats        | No                                              |

**P0 count: 6** — These must block production. Three (F-02, F-03, F-05) form a chain: one unhandled caller error (inverted args, zero anchor, descending growth) can silently corrupt the EMA through the full pipeline. The integration suite catches none of them adequately.

### Per-flaw detail

#### F-01 — Future-pack silent corruption (P0)
**File:** `EMAGrowthTransformationLib.sol`, lines 64-67.
```solidity
unchecked {
    timeDelta = int256(uint256(uint24(currentEpoch - currentOraclePack.epoch()))) * 64;
}
```
**Attack:** A pack whose `epoch()` is even 1 ahead of `currentEpoch` wraps the `uint24` subtraction to `2^24 - 1`, producing a `timeDelta ≈ 1.07e9` seconds. `OraclePack.insertObservation` interprets this as ~34 years elapsed and applies near-total EMA replacement (bounded by the 75% time-delta cap in `updateEMAs`). Triggerable by: (a) testnet / L2 reorg, (b) stored pack from a forked deployment, (c) cross-chain context, (d) any pack-source that doesn't verify epoch monotonicity. No revert — silent miscomputation.

**Caught by tests?** No. The prior unit test was unsound (asserted only `returned.epoch() == currentEpoch`) and was deleted. The integration suite does not attempt this. **This is the single most dangerous uncovered surface in the library.**

**Fix (library):** Add `if (currentOraclePack.epoch() > currentEpoch) return currentOraclePack;` after step 1 (epoch gate), or `require(currentOraclePack.epoch() <= currentEpoch, OraclePackFromFuture());`.

**Fix (test):** Add an integration test that constructs a pack with `epoch() = currentEpoch + 1`, records 2 observations, runs the EMA, and asserts **either** the library reverts **or** captures a pre/post pack and shows the resulting spotEMA has moved by `>50%` of the distance to the clamped tick — a bound inconsistent with a 12-second real time delta.

#### F-02 — Anonymous div-by-zero on zero anchor (P0)
**File:** `GrowthToTickLib.sol`, line 27.
```solidity
uint256 ratioQ128 = FullMath.mulDiv(uint256(currentGrowth), FixedPoint128.Q128, uint256(anchorGrowth));
```
**Attack:** `anchorGrowth == 0` triggers EVM Panic 0x12 from FullMath. Legitimate on genesis pool observation. Persists for 256 pushes (~51 minutes of DoS) until the zero-anchor is evicted. No named error — the caller cannot discriminate "oracle not ready" from "oracle corrupted" from "oracle hit an arithmetic bug."

**Caught by tests?** Test 2 uses `vm.expectRevert(bytes(""))` — matches any revert, including a hypothetical regression that returned 0 instead of reverting. Not a protective canary.

**Fix (library):** Add `if (anchorGrowth == 0) revert ZeroAnchorGrowth();` at the top of `growthToTick`. Caller can now branch on `ZeroAnchorGrowth.selector`.

**Fix (test):** Replace `vm.expectRevert(bytes(""))` with `vm.expectRevert(stdError.divisionError)` (pins current behavior) or `vm.expectRevert(ZeroAnchorGrowth.selector)` (after the fix).

#### F-03 — Inverted argument silent negative tick (P0)
**File:** `GrowthToTickLib.sol`, lines 24-37.
```solidity
function growthToTick(uint208 currentGrowth, uint208 anchorGrowth) pure returns (int24 tick) {
    // no check that currentGrowth >= anchorGrowth
    ...
}
```
**Attack:** A caller that swaps arguments — `growthToTick(oldest, latest)` instead of `growthToTick(latest, oldest)` — produces a ratio < 1, a `sqrtPriceX96 < 2^96`, and a negative tick. **No revert.** The inverted tick passes through `clampTick` and `insertObservation` without any sanity check, silently corrupting the oracle. Tested at the unit level in `growthToTick`, but there is no structural barrier in `EMAGrowthTransformationLib` — a future refactor of the composition is the exact bug vector.

**Caught by tests?** No. Test 4 unit-tests the symmetry of `growthToTick` but does not pin the argument order inside `updateGrowthEMA`.

**Fix (library):** `require(currentGrowth >= anchorGrowth, RatioBelowUnity());` at function entry. Makes the inverted-caller bug a revert, eliminating silent miscomputation.

**Fix (test):** An integration test that constructs a buffer with descending growth (already exists as D.4's setup) and then runs `updateGrowthEMA` — and asserts the call reverts with `RatioBelowUnity` (post-fix) or at minimum asserts the returned pack's `spotEMA` does not go negative.

#### F-04 — Silent wrap on descending growth (P0)
**File:** `BlockNumberAwareGrowthObserverLib.sol`, lines 28-46.
The `record()` function enforces block-number monotonicity but not growth monotonicity. Angstrom's `globalGrowth` is documented as monotonically non-decreasing, but (a) reorgs, (b) subtle Angstrom accounting bugs, (c) fee-rebate donations can violate this. On violation, `growthDelta(earlier, later)` wraps modulo 2^208 to a value near `type(uint208).max`, and `growthToTick` happily computes a ratio that looks plausible but encodes a ~MAX_TICK growth event.

**Caught by tests?** Test 5 documents the wrap but does not assert that `record()` or `updateGrowthEMA` rejects the input. It treats the vulnerability as specification.

**Fix (library):** Inside `record()`, after the block-number check, add:
```solidity
if (SafeCastLib.toUint208(_cumulativeGrowth) < latest.cumulativeGrowth())
    revert NonMonotonicGrowth();
```
Default behavior change — should be feature-flagged or governance-controlled because keeper pipelines may have a legitimate need to accept retractions (e.g., after a reorg). Safest default: revert.

**Fix (test):** Extend Test 5 to run `runEMA` on the descending-growth buffer and assert the pipeline reverts (post-fix) or that the corrupted tick does not leak to the EMA.

#### F-05 — No anchor-order enforcement at EMA composition (P0)
**File:** `EMAGrowthTransformationLib.sol`, line 57.
```solidity
int24 growthTick = growthToTick(latest.cumulativeGrowth(), oldest.cumulativeGrowth());
```
**Attack:** Structural — depends on `latest.cg >= oldest.cg`. If F-04 is unfixed, this line feeds an inverted ratio into `growthToTick`, which (per F-03) returns a negative tick. Downstream `insertObservation` accepts it. End-to-end silent miscomputation.

**Caught by tests?** No. Test 4 fires an assertion against `growthToTick` directly, not against the library's composition. Test 5 stops before `runEMA`.

**Fix:** Add `if (latest.cumulativeGrowth() < oldest.cumulativeGrowth()) revert NonMonotonicGrowth();` before line 57. Belt-and-braces with F-04 and F-03.

#### F-06 — Negative clampDelta silent clamp inversion (P0)
**File:** `EMAGrowthTransformationLib.sol`, line 42 (and downstream into `OraclePack.clampTick`).
**Attack:** `clampDelta < 0` passes through to `clampTick` where `_lastTick + clampDelta` produces a bound *below* `_lastTick` and `_lastTick - clampDelta` produces a bound *above* `_lastTick`. The branch ordering means virtually every `newTick` clamps to `_lastTick + clampDelta` (which is `_lastTick - |clampDelta|`). The effect: an adversarial operator with governance control over `clampDelta` can pull the EMA downward at `|clampDelta|` per update regardless of the true tick.

**Caught by tests?** No. Integration tests hardcode `DEFAULT_CLAMP = 1000`.

**Fix (library):** `require(clampDelta >= 0, InvalidClampDelta());` at `updateGrowthEMA` entry.

**Fix (test):** Add an integration test with `clampDelta = -1` and assert it reverts.

#### F-07 — Unchecked block scope creep on `timeDelta` (P1)
**File:** `EMAGrowthTransformationLib.sol`, lines 64-67.
The `unchecked { timeDelta = ... * 64; }` block wraps both the `uint24(currentEpoch - pack.epoch())` subtraction (which *needs* to be unchecked for the wrap on the 34-year counter boundary) AND the `* 64` multiplication (which **does not** need unchecked — `(2^24) * 64 = 2^30`, well within `int256`). A future refactor replacing `64` with a larger constant would silently overflow without the compiler complaining.

**Fix:** Split the unchecked:
```solidity
uint24 epochDelta;
unchecked { epochDelta = uint24(currentEpoch - currentOraclePack.epoch()); }
timeDelta = int256(uint256(epochDelta)) * 64; // checked multiplication
```

#### F-08 — `growthInside` triple-unchecked subtraction (P1)
**File:** `AngstromAccumulatorConsumer.sol`, lines 59-68.
Three subtractions under one `unchecked` block:
- `outsideBelow - outsideAbove`
- `outsideAbove - outsideBelow`
- `global - outsideBelow - outsideAbove`
Any one of these can wrap on a reorg or on an Angstrom accumulator inconsistency, producing a near-2^256 return value that downstream consumers interpret as a legitimate growth measurement. No invariant check, no named error.

**Fix:** Either (a) split into checked subtractions (costs gas but surfaces bugs as reverts), or (b) add post-condition bounds: `if (result > global) revert InvariantViolated();`.

#### F-09 — Same-block-first-wins denies keeper corrections (P1)
**File:** `BlockNumberAwareGrowthObserverLib.sol`, line 38.
```solidity
if (latest.blockNumber() >= SafeCastLib.toUint32(_blockNumber)) return;
```
The natspec documents this as "idempotent for keeper retries." The cost: if the keeper's *first* write for a block is wrong (bug, half-synced Angstrom state, race condition), the error is locked in for that block and every downstream consumer integrates the wrong observation. There is no governance override.

**Fix (design):** Add an `adminReplaceLatest(GrowthObservation correctObs)` path gated by access control. Or accept the tradeoff and document it more prominently than a `@dev` line.

#### F-10 — Epoch gate precedes buffer precondition (P1)
**File:** `EMAGrowthTransformationLib.sol`, lines 45-46.
If `pack.epoch() == currentEpoch` the function returns immediately, regardless of buffer count. If they differ, the function reverts on `count < 2`. A caller's error-handling code has to branch on epoch state to predict which failure mode it will see — a non-uniform error surface.

**Fix:** Move the `count < 2` check before the epoch check. Trades one extra SLOAD in the hot path for uniform errors; the observability benefit outweighs the gas cost on a `view` function called once per epoch.

#### F-11 — `growthDelta(earlier, later)` positional ambiguity (P1)
**File:** `GrowthObservation.sol`, lines 79-83.
Named parameters are `earlier` and `later`, but the call site in the pipeline is `old.growthDelta(lat)`. Positional semantics mean swapping the receiver and argument is a one-character bug. The natspec warns about it but there is no compile-time or runtime enforcement.

**Fix (library):** Two options:
- (a) Rename to `growthDelta(GrowthObservation b) returns (uint208 delta)` and assert `b.blockNumber() > self.blockNumber()` at runtime, reverting on violation. Self-check eliminates the ambiguity.
- (b) Replace with `growthBetween(GrowthObservation a, GrowthObservation b)` that internally orders by block number.

#### F-12 — `globalGrowth` hardcodes Angstrom storage layout (P1)
**File:** `AngstromAccumulatorConsumer.sol`, lines 42-44.
`POOL_REWARDS_SLOT = 7` and `REWARD_GROWTH_SIZE = 16777216` are hardcoded constants derived from Angstrom's internal storage layout. An Angstrom upgrade that shifts slot 7 or changes the offset would silently return garbage. Since Angstrom is read-only to this codebase, there is no versioning contract.

**Fix (defensive):**
- Add an `ANGSTROM_VERSION()` or equivalent version-check in the constructor.
- Or: validate the returned `globalGrowth` is monotonic-non-decreasing over successive calls and revert on regression (a weak smoke check).
- Or: make the slot constants immutable-configurable so a redeploy can pin to a new layout.

**Attack vector:** Angstrom upgrade pushes slot 7 to slot 8. This contract silently reads `extsload(7)` and returns whatever lives at the old slot (possibly reward-count or a different pool's data). The oracle silently mispriced for weeks.

#### F-13 — Clamp output not re-bound against TickMath range (P1)
**File:** `EMAGrowthTransformationLib.sol`, line 60.
`clampTick` does unchecked arithmetic on `int24 _lastTick + int24 clampDelta`. If `_lastTick` is near `MAX_TICK` and `clampDelta` pushes it past `type(int24).max`, the addition wraps int24, producing a clamped tick outside `[MIN_TICK, MAX_TICK]`. `insertObservation` does not re-validate.

**Fix:** After the clamp, `clampedTick = clampedTick > MAX_TICK ? MAX_TICK : (clampedTick < MIN_TICK ? MIN_TICK : clampedTick);`.

#### F-14 — Zero `EMAperiods` silently accepted (P1)
**File:** `EMAGrowthTransformationLib.sol`, line 41.
The BTT requires each of the four 24-bit period values to be `>= 64` (one epoch). No runtime enforcement. Setting any period to 0 via governance misconfiguration either divides by zero downstream or silently freezes that EMA.

**Fix:** Validate all four periods at entry:
```solidity
require(uint24(EMAperiods) >= 64 && uint24(EMAperiods >> 24) >= 64 && uint24(EMAperiods >> 48) >= 64 && uint24(EMAperiods >> 72) >= 64, InvalidEMAPeriods());
```

#### F-15 — `elapsedBlocks` unchecked wrap (P2)
**File:** `GrowthObservation.sol`, lines 88-92. Symmetric to F-11 but for block numbers. Not currently called in the pipeline (as far as I can see in the library code), so severity is P2 — but it is a latent footgun for future callers.

#### F-16 — Binary search has no explicit termination bound (P2)
**File:** `BlockNumberAwareGrowthObserverLib.sol`, lines 86-113.
The `while (low < high)` loop relies on `mid = (low + high) / 2` strictly-monotonically narrowing the range. A corrupted buffer where the stored block numbers are non-monotonic could theoretically oscillate — though the current invariant (enforced by `record()`'s monotonicity check) prevents this.

**Fix:** Bound the loop with an iteration count: `uint256 iter; while (low < high && iter++ < total) { ... }`. The check is free (read-only counter) and defensively caps the gas.

#### F-17 — `poolExists` unbounded iteration (P2)
**File:** `AngstromAccumulatorConsumer.sol`, lines 97-101.
Loops over `store.totalEntries()` checking each entry. If the config store bloats (operator misconfiguration), gas cost grows linearly. Called in a view path, so no direct DoS — but a caller invoking it in a transaction could hit block-gas-limit.

**Fix:** Either (a) hard-cap the iteration count, or (b) document that this is a pure read path and callers must offline-query total entries first.

---

## Part 4 — Recommended Fixes (prioritized)

### Code-level fixes (in order of severity)

1. **F-01 future pack rejection** (single line, 4 lines after the epoch gate). Eliminates the catastrophic time-delta wrap.
2. **F-03 ratio-below-unity revert** (one `require` at `growthToTick` entry). Collapses the silent-negative-tick surface.
3. **F-05 monotonic anchor check in EMA composition** (one `require`). Belt-and-braces with F-03/F-04.
4. **F-02 named `ZeroAnchorGrowth()` error** (one `if + revert` at `growthToTick` entry). Enables selector-based revert classification.
5. **F-06 non-negative clampDelta guard** (one `require` at `updateGrowthEMA` entry).
6. **F-04 monotonic growth check in `record()`** (governance-flagged — default on in production).
7. **F-14 non-zero EMAperiods validator** (one `require` at `updateGrowthEMA` entry).
8. **F-13 post-clamp tick-range bound** (two ternaries).
9. **F-07 split unchecked block** (refactor 3 lines).
10. **F-08 bounded subtractions in `growthInside`** (add 3 post-condition checks).
11. **F-10 reorder buffer check before epoch gate** (3-line reshuffle).
12. **F-11 `growthDelta` self-ordering or renaming** (library-level API change, requires call-site migration).
13. **F-12 Angstrom layout version check** (design-level; requires upstream coordination).

### Test-level fixes (immediate, no code changes to libraries)

1. **Strengthen integration Test 1** to assert the clamped tick actually fed to `insertObservation` (compute expected pre-clamp tick via `growthToTick(lat, old)` and compare).
2. **Tighten integration Test 2** from `bytes("")` to `stdError.divisionError` — pins the current Panic 0x12 behavior so a silent "fix" to return 0 is caught.
3. **Extend integration Test 3** to set pack's `lastTick = 200_000` and loop the EMA update across N stagnant epochs — assert drift bound `|lastTick_N - lastTick_0| <= N * clampDelta`.
4. **Extend integration Test 4** to extract the spot EMA delta from the returned pack and compare it against `growthToTick(lat, old)` post-clamp. Proves the composition, not just the primitive.
5. **Extend integration Test 5** to run `runEMA` on the descending-growth buffer and assert the corrupted tick reaches `insertObservation` — or that the pipeline reverts (post-F-04 fix).
6. **Add integration test for F-01** (future pack).
7. **Add integration test for F-06** (negative clampDelta).
8. **Add integration test for post-wrap oldest correctness** (pump 512 observations into the mock, then run the EMA and compare against a Python mirror).
9. **Add integration test for multi-pool isolation** — instantiate two pools in the same `AngstromAccumulatorConsumer`, record into both, and verify growth values do not cross-contaminate.
10. **Add a `recordSyntheticAtCurrentGrowth(rtd)` helper to `MockRANPipeline`** so the uint16 `relativeTimeDelta` overflow can be exercised in the integration context.

---

## Closing Statement

The 5-test integration suite advertises "happy path + 4 cross-library security canaries" — in practice, **4 of the 5 tests rely on the single assertion `updated.epoch() == currentEpoch`**, which is the weakest possible post-condition for `updateGrowthEMA` and can never distinguish a correct implementation from a broken one. Test 5 (D.4) is the only test with a discriminating numeric assertion; the other four short-circuit past the EMA composition (Tests 2, 3, 4 test `growthToTick` or primitives directly) or prove only epoch-stamping (Test 1).

Beneath the tests, the five libraries ship with **six P0-class implementation flaws** — three of which (F-01, F-03, F-05) form a silent-miscomputation chain from the observer through `GrowthToTickLib` into the EMA pipeline. None of the current tests would catch a regression in any of the six.

The single highest-leverage change is **F-01 (reject packs from the future)**: one line of Solidity closes the largest silent-wrap surface in the library. The single highest-leverage test change is **tightening Test 2's `vm.expectRevert(bytes(""))` to a selector-specific revert** — this transforms a weak smoke assertion into a meaningful canary.

Recommend: **do not deploy** until F-01 through F-06 are resolved. The current integration suite should be expanded to at least 10 tests before it can serve as a regression shield for production.
