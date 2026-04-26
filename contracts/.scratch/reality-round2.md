# Reality Check Round 2 — RAN Oracle Test Suite "Tightening"

**Reviewer**: TestingRealityChecker
**Date**: 2026-04-13
**Prior verdict**: NEEDS WORK / leaning FANTASY, 13/48 believable.
**Current verdict**: **NEEDS WORK** — moved from FANTASY-leaning to HONEST-but-thin. ~18–20/48 believable now. Real improvements on a few fixes; two "fixes" are fig leaves; one is a flat-out lie in a comment.

Default disposition: **Do not certify production-ready**. A second revision cycle is still required.

---

## Global fixes — verified

### G-1. `onlyForked` now uses `vm.skip(true)` — REAL FIX

`test/_helpers/BaseForkTest.t.sol:25–32`:

```solidity
modifier onlyForked() {
    if (!forked) {
        vm.skip(true);
        return;
    }
    console2.log("running forked test");
    _;
}
```

This is correct. Foundry now reports these as **SKIPPED**, not PASSED, when `ALCHEMY_API_KEY` is unset. The round-1 "fantasy green in 27 s" failure mode is fixed at the reporting layer.

Caveats:
- **CI can still pass with the key unset**. Skipped tests do not fail a run by default. If CI runs without `ALCHEMY_API_KEY`, all 34 fork tests silently skip and the pipeline is green. Required upgrade: CI must fail if any test in the `diff` profile is skipped, **or** require `ALCHEMY_API_KEY` at job level.
- The round-1 concern that "27 s = tests not running" now has a new interpretation: 27 s without a key == tests skipped (honest); 27 s **with** a key still can't be right for a suite that does `vm.rollFork` + ffi-to-Python 30+ times. If CI produces 27 s with the key set, that is a signal some fork tests still no-op through another path.

### G-2. `runs = 5` still the default — PARTIAL

`foundry.toml:97–98` still has `runs = 5` for `[profile.diff.fuzz]`. A new `[profile.diff-deep]` with `runs = 100` exists. That is a documentation gesture, not a fix, unless CI runs `diff-deep`. **Show the CI pipeline invoking `FOUNDRY_PROFILE=diff-deep forge test` or this remains "example-based testing" dressed with a deep-profile escape hatch.** 100 runs is also still too few for the uint208 / uint32 domain — the correct target is 256–1024 for security-edge tests, 10k+ for overflow/boundary checks. This is an improvement in posture only.

### G-3. Catch-all `bytes("")` semi-replaced — FIG LEAF

The literal `vm.expectRevert(bytes(""))` has been replaced in critical canaries with:

```solidity
try this.externalGrowthToTick(...) {
    fail();
} catch (bytes memory reason) {
    assertEq(reason.length, 0, "expected FullMath bare require (empty revert) for zero anchor");
}
```

This **still matches every revert whose revert-data is empty** — including: `require(false)` without a message, out-of-gas bubbling as empty bytes in some paths, `assert(false)` if it ever emitted empty (it doesn't, but a future refactor could), a missing function selector hitting a fallback that reverts empty, etc. It is **not** the specific Panic(0x12) or Panic(0x11) that `FullMath.mulDiv` produces on division by zero / overflow.

Actually verify: `FullMath.mulDiv` in Uniswap V4 uses `require(denominator > 0)` (no reason) and `require(denominator > prod1)` — both empty reverts. So an empty-reason revert *is* what mulDiv produces. That's correct **today** — but:

1. If `FullMath` is ever refactored to use `Panic(0x12)` (Solidity's native arithmetic panic) to match modern idiom, **this test silently passes against the wrong revert path**.
2. If a caller adds a `require(anchor != 0, "zero")` *above* `FullMath.mulDiv`, this test **continues to pass against the new require even though the original mulDiv path is now unreachable**. That's a regression the test explicitly fails to catch.
3. The assertion `assertEq(reason.length, 0, …)` does not verify **where** in the stack the revert came from. If a mutant adds a new `require` somewhere earlier with no reason string (e.g., a defensive `require(anchorGrowth != 0)` at the top), the test passes, but the canary's claim — "the named bug in `FullMath.mulDiv` reverts" — is no longer true.

**Verdict**: empty-reason match is marginally more informative than `bytes("")`, but it is still not a targeted canary. A real canary must assert a specific selector (`Panic.selector, 0x12`) **and** optionally use `vm.recordLogs` / stack trace inspection to confirm the revert originated inside `FullMath.mulDiv`. Without that, the tests `GrowthToTick_ZeroAnchorReverts` and `GrowthToTick_Stage1OverflowReverts` remain weak canaries.

### G-4. 5-run fuzz for boundary tests — UNFIXED

The `RelativeTimeDeltaOverflowReverts`, `BlockNumberOverflowReverts`, and every other `test__fuzz*` still runs 5 seeds under the default profile. 5 seeds over a `uint256` domain is not fuzzing. This remains a global defect.

---

## Per-fix reality check (as listed by the user)

### Fix 1: I.2 canary now reads `OraclePack.lastTick()` sign — DOES IT PROVE ARG ORDER?

**Current test** (`AngstromRANPipeline.diff.t.sol:207–224`):

```solidity
pipeline.recordSynthetic(1000, 0, 1e30);       // oldest (ascending)
pipeline.recordSynthetic(1001, 12, 5e30);      // latest (ascending)
...
OraclePack updated = pipeline.runEMA(stalePack, DEFAULT_PERIODS, int24(100));
int24 storedTick = updated.lastTick();
assertGt(storedTick, int24(0), "EMA must pass latest.growth as current ...");
```

**Walk-through of the canary logic** (from `EMAGrowthTransformationLib.sol:66`):

```solidity
int24 growthTick = growthToTick(latest.cumulativeGrowth(), oldest.cumulativeGrowth());
```

- Correct code: `growthToTick(5e30, 1e30)` → positive tick (5x growth). Clamped to +100. `insertObservation(clampedTick=100, ...)` sets `lastResidual = 100`, `referenceTick = 0`, so `lastTick() = 0 + 100 = 100 > 0`. **Test passes.**
- Arg-order bug (mutant swaps to `growthToTick(oldest.cumulativeGrowth(), latest.cumulativeGrowth())` = `growthToTick(1e30, 5e30)`): `currentGrowth < anchorGrowth` → either reverts (currentGrowth=1e30 < anchorGrowth=5e30 means ratio < 1, sqrtPrice < MIN_SQRT_PRICE, reverts with `InvalidSqrtPrice`) **or** returns a negative tick clamped to -100, giving `lastTick = -100`. Either way, `assertGt(storedTick, 0)` fails.

**Verdict**: this version **does** canary arg-order correctly. The round-1 objection is resolved. A mutation that flips the two arguments to `growthToTick` inside `updateGrowthEMA` is now caught.

**Remaining caveat**: the canary is narrow. It catches "latest/oldest swapped" but not "latest/oldest both set to the same wrong observation" (e.g., a bug that reads `oldest` twice). Also, the stalePack has `referenceTick = 0` and no EMA state, so the clamp `int24(100)` is tight to zero. With a different stalePack (non-zero `referenceTick`), the signed lastTick changes and the assertion could silently pass for the mutant if `referenceTick > 100`. The test is believable but not robust across initial-state permutations.

**Upgrade**: run the same canary with a matrix of stalePack states (e.g., `lastTick ∈ {-200, -100, 0, 100, 200}`) and assert the direction of change, not absolute sign.

---

### Fix 2: D.4 uses try/catch — DOES THE CATCH BRANCH CATCH ANYTHING REAL?

**Current test** (`AngstromRANPipeline.diff.t.sol:226–242`):

```solidity
pipeline.recordSynthetic(1000, 0, 5e30);
try pipeline.recordSynthetic(1001, 12, 1e30) {
    assertEq(pipeline.count(), 2, "both obs recorded despite non-monotonic growth");
    ...
    assertGt(uint256(wrappedDelta), uint256(1) << 207, "descending growth wraps to near 2^208 ...");
} catch {
    assertEq(pipeline.count(), 1, "non-monotonic growth correctly rejected by record()");
}
```

**Today**: `record()` checks block monotonicity (not growth), so the call does not revert. The `try` branch runs, and the assertion on the wrapped delta magnitude is meaningful and precise.

**"Forward-compatible" claim**: the `catch` branch would fire if `record()` is later hardened to reject non-monotonic growth. But:
1. **The catch is a bare `catch {}` — no reason string, no selector**. If `record()` reverts for any **other** reason (e.g., a future bug introduces an OOG, a wrong error, a SafeCast panic from a malformed input), the test still "passes" with `count() == 1`. The catch is a wildcard.
2. **The catch asserts `count() == 1`**, which would be true after any reverting call regardless of cause.

So the "forward-compatible" claim is false-positive-prone. If `record()` is refactored and a bug causes the second call to revert spuriously, the catch branch happily documents `count()==1` and the suite stays green while behavior regresses.

**Verdict**: today the test's `try` branch **is** a real canary (precise wrap magnitude on descending growth). The `catch` branch is a **fig leaf for forward-compatibility** — it does not verify the revert reason matches any intentional hardening.

**Upgrade**: `catch (bytes memory reason)` with an assertion that matches a named selector (e.g., `NonMonotonicGrowth.selector`). Until such an error type exists, drop the try/catch — the current production code never enters the catch branch, so the catch is dead code documenting a hypothetical future.

---

### Fix 3: `bytes("")` replaced with try/catch + length check — STRONGER OR STILL MATCHES TOO MUCH?

See G-3 above. **Still matches too much.** Specific:

- `GrowthToTick_ZeroAnchorReverts` (line 96–104): catch + `assertEq(reason.length, 0)`. Matches every empty-revert anywhere up the call stack.
- `GrowthToTick_Stage1OverflowReverts` (line 131–147): same pattern.
- `C1_ZeroAnchorRevertsEMA` (`AngstromRANPipeline.diff.t.sol:158–172`): same pattern.

A mutant that introduces a `require(anchor != 0)` at the top of `updateGrowthEMA` (without a reason string) would:
- Change where the revert originates (from FullMath deep in the call stack to an early guard).
- Still produce an empty revert.
- **Pass the test.**

That is exactly the scenario C1 was claimed to canary: "zero anchor reverts in the EMA path at the correct stage." The current assertion cannot distinguish "correct stage" from "any earlier stage."

**Verdict**: marginal improvement over `bytes("")`; still not a targeted canary. These tests rely on the continued absence of any earlier `require` statement in the call path — a brittle negative specification.

---

### Fix 4: F-01 FuturePack guard + canary test — DOES THE GUARD COVER ALL FUTURE-PACK PATHS?

**Guard** (`EMAGrowthTransformationLib.sol:50–55`):

```solidity
if (currentOraclePack.epoch() > currentEpoch) {
    revert FuturePack(currentOraclePack.epoch(), currentEpoch);
}
```

**Test** (`EMAGrowthTransformationLib.diff.t.sol:84–101`): asserts the specific selector + both args. Good — selector + args. Under 5 fuzz runs the bound `[1 .. type(uint24).max - currentEpoch]` is enormous, so 5 seeds sample essentially random points — OK for catching "guard disabled" (any seed would fail) but useless for boundary cases.

**Coverage gaps**:

1. **Off-by-one at the boundary** (`packEpoch == currentEpoch + 1` vs `packEpoch == currentEpoch`) is not explicitly tested. If the guard were `>=` instead of `>` (a typical mutation), the test with a random `futureOffset ∈ [1, max]` would still pass, but the boundary-case "pack exactly one epoch ahead" would be caught only probabilistically. Missing an explicit `futureOffset = 1` test.
2. **Epoch wrap at uint24 boundary**: `currentEpoch` is computed as `(block.timestamp >> 6) & 0xFFFFFF`. When `block.timestamp >> 6` overflows uint24 (year ~2036+ at 64 s/epoch), epoch wraps. A pack stored in epoch `0xFFFFF0` with the current on-chain counter now at `0x000005` — is that "future"? The guard uses uint24 compare, and `0xFFFFF0 > 0x000005 == true`, so the stale-but-wrapped pack is rejected as "future." This is a **latent bug in the guard** that the test does not exercise. The test's `bound(futureOffset, 1, maxOffset)` explicitly excludes the wrap regime — it *cannot* reach this scenario.
3. **Same-epoch short-circuit runs FIRST** (line 47). If the pack's epoch is *equal* to `currentEpoch`, the function returns early without ever hitting the FuturePack guard. A mutant that changed the epoch check to `<=` and the short-circuit to `<` would still appear to work for non-future packs but fail for future packs — but the current test does not verify the short-circuit path doesn't swallow future packs.
4. **The guard is upstream of the `count < 2` check**. If a pack is future **and** the buffer has <2 observations, the guard fires first. Test exists only with 2 recorded obs. A future-pack path with 0 obs is not tested — a mutant that moves the count check above the guard would break in that scenario, and the test wouldn't catch it.

**Verdict**: the guard itself looks correct for non-wrap epochs. The test covers the happy mutation path. It does **not** cover the epoch-wrap regime, the exact boundary, or ordering with the count check. Tightening needed.

---

### Fix 5: F-06 negative clampDelta canary — DOES IT TEST ANYTHING OR JUST DOCUMENT "DOESN'T REVERT"?

**Test** (`EMAGrowthTransformationLib.diff.t.sol:103–123`):

```solidity
function test__fuzzSecurityEdge__EMA_NegativeClampDeltaCurrentlyAccepted(int24 clamp) public {
    clamp = int24(bound(clamp, -1000, -1));
    ...
    try m.runUpdate(stalePack, DEFAULT_PERIODS, clamp) returns (OraclePack returned) {
        assertEq(uint256(returned.epoch()), uint256(currentEpoch), "EMA advances epoch with negative clampDelta (current silent behavior)");
    } catch {
        // F-06 fix applied: guard now rejects negative clampDelta. Test is forward-compatible.
    }
}
```

**Reality-check against the actual library**:

```
grep clampDelta contracts/src/libraries/transformations/EMAGrowthTransformationLib.sol
line 43: int24 clampDelta (parameter)
line 69: OraclePackLibrary.clampTick(growthTick, currentOraclePack, clampDelta)
```

**There is NO guard on `clampDelta` in the library**. The comment "F-06 fix applied: guard now rejects negative clampDelta" is **false** — no fix has been applied. The `catch {}` branch is unreachable because the library does not revert on negative clampDelta, `OraclePackLibrary.clampTick` treats it as an `int24` and uses it in signed arithmetic (which flips the clamp direction — negative delta makes `lastTick + clampDelta < lastTick - clampDelta`, so the clamp range inverts, likely clamping to a degenerate point).

What the test actually verifies today:
1. The `try` branch always executes.
2. `returned.epoch() == currentEpoch` — i.e., the epoch advanced. But that's a property of the same `insertObservation` call that happens for **any** clampDelta value. It doesn't distinguish negative from positive.

The test is not a canary. It documents "negative clampDelta doesn't revert today," but the library file that the test imports has no matching guard to canary. **The comment in the `catch` branch is a lie about code that doesn't exist.**

**Worse**: with negative `clampDelta`, `clampTick` may return a value that is far from the intended `growthTick` — possibly producing a nonsense `lastResidual` that breaks EMA math. The test does not assert any property of the **value** — only that epoch advanced. A genuinely pathological output (e.g., `lastTick` pinned at an absurd value) is silently accepted.

**Verdict**: **FIG LEAF with a false comment**. The test neither validates a fix nor fails against current behavior. It passes on any input that doesn't OOG. Either:
- Add a real guard (`if (clampDelta < 0) revert NegativeClampDelta();`) and have the test assert that selector; **or**
- Rename the test to `EMA_NegativeClampDeltaProducesPathologicalOutput` and assert the specific pathology (e.g., `returned.lastTick()` lands outside a reasonable range).

Either way, the current test **must not be cited as canary coverage for F-06**.

---

### Fix 6: HappyPath replaces `growthToTick` call with `assertGe(lat.growth, old.growth)` — IS THIS A TAUTOLOGY?

**Current test** (`AngstromRANPipeline.diff.t.sol:137–141`):

```solidity
assertGe(
    lat.cumulativeGrowth(),
    old.cumulativeGrowth(),
    "real on-chain growth must be non-decreasing over the sampled window"
);
```

Where `lat` and `old` come from `pipeline.latest()` and `pipeline.oldest()`, which read the ring buffer populated by `pipeline.recordFromOnChain(...)` which pulls `consumer.globalGrowth(poolId)` at each sampled block.

**Is this a tautology?** Not quite, but it's close. Let's be precise:

- The values in `lat` and `old` are the real on-chain growth values at two different block numbers (oldest sampled, newest sampled).
- `assertGe(latest, oldest)` asserts that the on-chain Angstrom accumulator is non-decreasing over the sampled window.
- The test does **not** test `growthToTick`, `updateGrowthEMA`, or the EMA math. It asserts an on-chain invariant.
- Later, the test asserts `updated.epoch() == currentEpoch`. The returned pack's other fields (EMA values, `lastTick`, `residualTick`, `orderMap`) are not inspected.

**What the test verifies about the library**: the buffer records what `recordFromOnChain` feeds it (oldest/latest blockNumber and growth match rows[0] and rows[windowSize-1]). That IS a meaningful smoke test of the buffer + consumer chain: a mutant that corrupts storage or reads the wrong slot would fail the first four asserts (`old.blockNumber()`, `lat.blockNumber()`, `old.cumulativeGrowth()`, `lat.cumulativeGrowth()`).

**What it does NOT verify**: the EMA output. A mutation in `updateGrowthEMA` that corrupts every EMA field except `epoch` would pass silently. The `assertGe` is a red herring — it's an on-chain invariant, not a library property.

**Is the `assertGe` itself a tautology?** No — the Angstrom accumulator **is** in principle non-decreasing, but this is a property of Angstrom's contract, not of the library under test. It's a sanity check on the fixture. If a mutation to `consumer.globalGrowth` made it return `0` for the latest block, the `assertGe` would still pass (0 ≥ 0). So it's a weak sanity check at best.

**Verdict**: replacing `growthToTick(lat, old)` with `assertGe(lat, old)` removed a tautology (`growthToTick(x, x) == 0` is identity) and replaced it with a weak sanity check on fixture data. It is **not a stronger test of library behavior**, merely a more honest one. The HappyPath still does not verify any EMA output. A proper upgrade would assert specific values of `updated.referenceTick()`, `updated.residualTick(0)`, or `updated.lastTick()` against a Python reference.

---

### Fix 7: WorstCase binary search targets `rows[n-2]` — DOES THIS TRAVERSE THE DEEPEST PATH?

**Current test** (`BlockNumberAwareGrowthObserverLib.diff.t.sol:67–91`):

```solidity
AccumulatorRow[] memory rows = decodeRange(ffiPython(rangeArgs(vm, 0, 256)));
for (uint256 i; i < rows.length; ++i) {
    mock.recordObs(rows[i].blockNumber, FIRST_OBSERVATION_TIME_DELTA, rows[i].globalGrowth);
}
uint32 target = uint32(rows[rows.length - 2].blockNumber);  // rows[254]
```

**Buffer geometry**: 256 obs, stored with `CircularBuffer`. Ring buffer is logically reverse-indexed: `rawAt(0)` is newest (rows[255]), `rawAt(1)` is rows[254], ..., `rawAt(255)` is rows[0]. Binary search in `observeAt` searches over `[0, count-1]` = `[0, 255]`.

- Target = `rows[254].blockNumber`. In the reverse-indexed buffer this is at logical index 1.
- Binary search visits: mid = (0+255)/2 = 127, then (0+126)/2 = 63, ..., until it converges on index 1.
- Number of iterations to find index 1 in a 256-element array: log2(256) = 8 iterations. Actually the deepest path is finding any element — binary search always takes ≈ log2(n) iterations regardless of position for a successful search. The "worst case" for binary search is **search depth**, and the depth for any hit in a 256-element sorted array is 8 iterations.

**So does `rows[254]` actually exercise a deeper path than `rows[1]`?** Slightly — for elements at specific indices the search may terminate early (e.g., mid=127 hits rows[128] → wrong, go left; etc.). But in both cases the search runs to its maximum depth ≈ log2(256). The round-1 claim that "rows[1] is shallow and rows[n-2] is deep" is not correct — binary search depth is symmetric. Elements near the middle (index ~128) may find the target at the first probe (mid), elements at indices 0 and n-1 require full traversal.

**The right worst-case is index 0 or index n-1** (target at an extreme) — the search probes 127 iterations before converging on the boundary.

Wait — actually for 256 elements, binary search is always ≈ ceil(log2(256)) = 8 comparisons. I was confused. Fine: **the choice of target index barely matters**. What matters is whether the array is fully populated, which it is.

**Verdict**: moving from `rows[1]` to `rows[n-2]` is a cosmetic change. For 256-element binary search, any in-range target takes ~8 iterations. The fix addresses a misstated round-1 concern, but neither version is a true worst-case stress — both are equally "worst case" for a 256-entry search. The actual concerns are:

1. **Gas ceiling of 18,000 is still unjustified**. 8 storage loads × ~2100 gas cold = 16,800 + overhead. The ceiling has no comment citing the expected op count × per-op cost.
2. **No test for the `>` target (beyond newest) or the `<` target (before oldest) path**, which have different branch coverage than hit-in-range.
3. **No test for the pre-wrap vs post-wrap case**, which `ObserveAtPostWrapGasStability` addresses with a separate test but also uses the arbitrary 18k ceiling.

---

### Fix 8: `onlyForked` uses `vm.skip(true)` — DOES CI PASS WITHOUT KEY?

Covered in G-1. **Yes, CI still passes without the key** unless CI is configured to fail on skipped tests. Foundry's default behavior: skipped tests do not fail the run.

**Test the claim**: run `FOUNDRY_PROFILE=diff forge test` without the key in a clean environment. Expected:
- 34 fork tests report SKIPPED.
- Remaining ~14 tests run.
- Exit code 0.

This is an improvement over silent PASSED, but it is **not sufficient for CI certification**. Required CI behavior:
- Production-readiness pipeline **must** provision `ALCHEMY_API_KEY` and fail if any `diff`-profile test is SKIPPED.
- Or: add a meta-test `test__MetaGuard__ForkTestsActuallyRan()` that reverts if `forked == false`, so every CI run asserts the key is set.

Neither is currently in place.

---

## Canary report card (round 2)

| Canary | Round 1 verdict | Round 2 verdict |
|---|---|---|
| `C.1` zero-anchor reverts in EMA | FAILS TO CANARY | Still **WEAK** — empty-revert match is too permissive; cannot distinguish mulDiv panic from any other empty revert |
| `C.2` stagnant pool | FAILS TO CANARY | **Unchanged** — still tests epoch advance + idempotence, not stagnation. Name still misleading. |
| `D.4` descending growth | Canaries correctly | Still canaries correctly; new catch branch is dead code today |
| `I.2` arg-order | FAILED TO CANARY | **NOW CANARIES CORRECTLY** via `lastTick` sign check |
| `F-01` future-pack | N/A | **Canaries the bulk mutation**; misses boundary + epoch-wrap |
| `F-06` negative clampDelta | N/A | **DOES NOT CANARY** — comment is false, library has no guard, assertion is weak |

**Score update**: 13/48 → ~18/48 believable. The I.2 fix is a genuine upgrade (+1). The F-01 test is new and believable (+1). D.4 stays believable. F-06 does not count (comment is false). HappyPath's change is neutral (removed tautology, added weak sanity check).

---

## Tests that still give false confidence (named)

1. **`EMA_NegativeClampDeltaCurrentlyAccepted`** — comment claims a fix that doesn't exist in code. The `catch` branch is unreachable. This test will **green up to 100%** against any mutation because its only non-trivial assertion (`returned.epoch() == currentEpoch`) holds for nearly every input. **If this test is cited as coverage for F-06, that citation is a fabrication.**

2. **`GrowthToTick_ZeroAnchorReverts` / `GrowthToTick_Stage1OverflowReverts` / `C1_ZeroAnchorRevertsEMA`** — all three still rely on "some empty-reason revert happens." A plausible refactor of `FullMath` to use Panic selectors, or an added upstream `require` without a reason string, silently changes what these tests detect while keeping them green. They give **false confidence that the named bug location reverts**, when in fact any empty revert anywhere satisfies them.

3. **`D4_DescendingGrowthCurrentlyWrapsOrShouldRevert`** — today works, but the wildcard `catch {}` paired with "forward-compatible" framing creates a future time bomb: any future regression that causes `record()` to revert spuriously will be absorbed into the catch branch as evidence of "non-monotonic growth correctly rejected." This is a **fig leaf specifically for forward-compat**.

4. **`ObserveAtFullBufferBinarySearchWorstCase` / `ObserveAtProductionCadence30MinCoverage` / `ObserveAtPostWrapGasStability`** — gas ceiling `< 18_000` still has no derivation. A regression from 16k to 17.5k passes; a cold/warm storage flip between runs could push above 18k and flake CI with no real regression. **Gas-budget tests need a derivation comment or they're performative.**

5. **`PipelineHappyPath`** — still asserts `epoch == currentEpoch` and nothing about the EMA output. The replacement of `growthToTick(lat, old)` with `assertGe(lat, old)` removed a tautology but **did not add a single assertion about EMA behavior**. Any mutation to `updateEMAs` (called inside `insertObservation`) that corrupts the EMA state but preserves epoch passes this test unchanged.

6. **`AngstromAccumulatorConsumer` tautology** — untouched in round 2. The Python DuckDB mirror is still compared against the same on-chain read. If both mirrors share a bug (the realistic failure mode), neither side detects it.

7. **`GrowthObservation.RealObservationsAreNonZero`** — untouched. `isZero()` returns true only if the entire 256-bit slot is zero; any non-zero blockNumber makes it false regardless of growth. Tests `blockNumber != 0`, not the library.

---

## Verdict on the "tightened" suite

**NEEDS WORK**. Moved from "fantasy-leaning" to "honest-but-thin":

- Real improvements: `vm.skip(true)`, I.2 now canaries arg-order, F-01 guard present and mostly tested, D.4 still solid.
- Fig leaves: empty-revert length check, D.4 catch branch, F-06 test with false comment, gas ceilings, WorstCase cosmetic fix.
- Lie in a comment: F-06 claims a fix that doesn't exist.
- Unfixed: `runs = 5` as default, `onlyForked` CI behavior, AngstromAccumulatorConsumer differential-vs-mirror, no EMA numeric output assertions, tautological GrowthObservation tests.

**Believable count**: ~18 of 48, up from 13/48. Still under 40%.

**Production readiness**: **NOT CERTIFIED**. Required before another assessment:

1. **Delete or fix the F-06 test and its false comment**. Either add the negative-clampDelta guard in the library and assert the selector, or rename + assert a specific pathology. Citing the current test as F-06 coverage is misrepresentation.
2. **Replace every empty-revert length check with a selector match**. For FullMath's empty `require`, either change FullMath to use Panic(0x11/0x12) and match the panic selector, or wrap the call in a named error. The current tests cannot distinguish "the bug I care about reverts" from "something reverts empty."
3. **Prove CI runs fork tests**. Add a guard that fails the run if any fork test is skipped. Measure CI wall-clock with key set — should exceed 5 minutes, not 27 seconds.
4. **Bump fuzz runs**. `runs = 5` is not fuzzing. Either change the default to ≥ 256 or show CI invokes `diff-deep` with ≥ 1024 runs for security-edge tests.
5. **Add 3+ numeric EMA tests** asserting output fields against a Python reference, including HappyPath. Currently the EMA math's correctness is untested outside of same-epoch no-op.
6. **Add F-01 boundary tests**: `futureOffset = 1` (exact off-by-one), and at least one test in the uint24-wrap regime.
7. **Remove the D.4 catch branch** (unreachable today) or make it assert a specific error name (`NonMonotonicGrowth.selector`) and add that error to `record()` in the same PR.

**Timeline estimate**: 2–3 days of test rewrites, plus one library change (F-06 guard) or one test rename/retarget. Do not treat "all green" as readiness until at least items 1, 2, and 3 land.

---

## Summary table — what each claimed fix actually did

| Claim | Reality |
|---|---|
| `vm.skip(true)` in `onlyForked` | **Real fix at reporting layer**; CI still green without key unless pipeline enforces |
| I.2 reads `OraclePack.lastTick()` sign | **Real fix**; now canaries arg-order correctly |
| D.4 try/catch forward-compatible | **Try branch real canary; catch branch is dead code + fig leaf** |
| Empty-revert length check replaces `bytes("")` | **Fig leaf** — still matches any empty revert anywhere |
| F-01 guard + canary | **Real guard + bulk-mutation coverage**; misses boundary + wrap regime |
| F-06 negative clampDelta | **Fig leaf with false comment** — no library guard exists |
| HappyPath `assertGe(lat, old)` | **Neutral** — removed one tautology, added weak fixture sanity check, still no EMA output assertion |
| WorstCase targets `rows[n-2]` | **Cosmetic** — binary search depth is ~log2(n) regardless of target position |

**Default verdict**: NEEDS WORK. Do not ship.
