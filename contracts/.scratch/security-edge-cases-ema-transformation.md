# Security Edge-Case Test Proposals — EMAGrowthTransformationLib

**Document type:** Security audit — adversarial test proposals
**Target file:** `contracts/src/libraries/transformations/EMAGrowthTransformationLib.sol`
**Function under test:** `updateGrowthEMA(CircularBuffer storage, OraclePack, uint96, int24) view returns (OraclePack)`
**Status:** Audit report — no code written
**Date:** 2026-04-12
**Auditor:** Blockchain Security Auditor
**Prior findings referenced:** `security-edge-cases-growth-to-tick.md` (G.1–G.5), `security-edge-cases-growth-observer.md` (C.1, C.2, D.4)

---

## 1. Audit Framing

`EMAGrowthTransformationLib` is a **Layer 2 composition** — a 75-line view function that stitches
four primitives together:

```
buffer (storage read)
   |
   +-- oldest.cumulativeGrowth()   ──┐
   +-- latest.cumulativeGrowth()   ──┴──► growthToTick  ──► int24 growthTick
                                                                |
                                                                v
                                                        clampTick(oraclePack, clampDelta)
                                                                |
                                                                v
                                                        int24 clampedTick
                                                                |
                                                                v
                                                   insertObservation(OraclePack,
                                                       clampedTick, currentEpoch,
                                                       timeDelta, EMAperiods)
```

It inherits the **full revert surface** of every primitive it composes, plus it introduces
**four novel attack surfaces** of its own:

1. **Epoch gate** (`currentEpoch == oraclePack.epoch()` early-return) — can be bypassed,
   spoofed, or made divergent from OraclePack's internal epoch semantics.
2. **Unchecked `timeDelta` subtraction** — `uint24(currentEpoch - oraclePack.epoch()) * 64`
   wraps on the 24-bit boundary (~34 years) and on any oracle-pack-epoch ahead of the
   current epoch (e.g. after time warp / EVM reorg).
3. **Clamp composition** — `clampDelta` is `int24` and unchecked addition inside
   `clampTick` (`_lastTick + clampDelta`) can overflow on extreme values.
4. **Stateless persistence contract** — the library returns an `OraclePack` but does not
   persist it. A caller that fails to persist the return value silently rolls back the
   EMA update, with no revert signal.

The BTT spec covers happy-path correctness (same-epoch no-op, buffer-too-small revert, EMA
convergence with a stable tick, monotonicity). The BTT does **not** enumerate:

- Epoch-boundary races where `block.timestamp >> 6` flips mid-transaction.
- Behavior when `clampDelta < 0` or `clampDelta > MAX_TICK - MIN_TICK`.
- Behavior when `currentOraclePack.epoch() > currentEpoch` (pack from the future).
- Behavior when `EMAperiods == 0` in any of the four slots.
- Behavior when the buffer post-wrap produces an oldest observation with `cumulativeGrowth == 0`.
- Byte-exact idempotency of the same-epoch fast path (the BTT says "returns unchanged" but
  does not assert bitwise equality of the packed uint256).
- Integer widths at the `insertObservation` boundary (`currentEpoch` passed as `uint256`,
  internally packed as 24 bits; `timeDelta` passed as `int256`, internally used as 64-bit).

This document proposes **12 security-focused tests** grouped by attack family, with
priorities anchored to confirmed architectural findings from the prior audits.

---

## 2. Test Proposals

### Family E — Canary Tests for Confirmed Architectural P0 Findings

These tests **canary-ify** findings C.1, C.2, D.4 from the prior audit. They are the single
most important additions to the test suite because they transform anecdotal audit findings
into executable regression tests that fail the moment the underlying bug returns.

---

#### E.1 `test__SecurityEdge__EMA_ZeroAnchorRevertsFor51Min` — **P0**

**Attack / failure mode.** Canary for **C.1** from the prior observer audit. The oldest
observation in a fresh-pool buffer can legitimately have `cumulativeGrowth == 0` (the very
first Angstrom-accumulator reading before any fees have accrued). When the second
observation lands in a new epoch, `updateGrowthEMA` calls
`growthToTick(latest.cg, oldest.cg)` which calls `FullMath.mulDiv(latest.cg, 2^128, 0)` and
**panics with EVM 0x12 (division-by-zero)**. This persists for every call until the oldest
observation is finally evicted — with a 256-slot buffer and ~12-second cadence, that is
**up to 51 minutes of total oracle DoS** on a fresh pool.

**Concrete setup.**
1. Initialize a fresh CircularBuffer with capacity 256.
2. `record(buffer, blockNumber=B, relTime=0, cumulativeGrowth=0)` — seeds the zero anchor.
3. Warp `block.timestamp` forward by 64 seconds so the epoch advances.
4. `record(buffer, blockNumber=B+1, relTime=12, cumulativeGrowth=1e18)`.
5. Construct a fresh `OraclePack` whose `epoch()` differs from the current epoch.
6. Call `updateGrowthEMA(buffer, pack, EMAperiods=packed(64,256,1024,4096), clampDelta=100)`.
7. Repeat call 255 more times with monotonically-increasing block numbers and cumulative
   growth values, each in a new epoch.

**Assertion.**
- Call on step 6 reverts with EVM Panic 0x12 (`stdError.divisionError`).
- Calls continue to revert for exactly the number of pushes required to evict the
  zero-anchor observation from the front of the ring. After that push, the call succeeds
  and returns a valid updated OraclePack.
- Additionally assert that in the returned pack, `epoch()` now equals the current computed
  epoch and `lastTick() != oraclePack.lastTick()` (i.e. the update took effect).
- **Recommendation in finding:** add a `ZeroAnchorGrowth()` named revert in `GrowthToTickLib`
  — this test would become a simple `vm.expectRevert(ZeroAnchorGrowth.selector)`.

**Why P0.** Direct oracle DoS. Confirmed attack surface. Without this canary, a future
refactor of `GrowthToTickLib` that "fixes" the zero-anchor panic (by returning 0, for
example) would silently convert a revert-DoS into a **silent-wrong-answer bug** — every
EMA update during the first 51 minutes would integrate tick 0 when the pool's real tick is
elsewhere. The EMAs would lag catastrophically and mispriced options would be underwritten
at predictable times (pool genesis).

---

#### E.2 `test__SecurityEdge__EMA_StagnantPoolDriftsTowardTick0` — **P0**

**Attack / failure mode.** Canary for **C.2** from the prior observer audit. When the pool
has no swap activity between the oldest and latest observations in the buffer
(`oldest.cumulativeGrowth() == latest.cumulativeGrowth()`), `growthToTick` returns **tick 0
exactly** (ratio = 1 → sqrtPrice = 2^96 → tick = 0). The EMAs then pull toward 0 epoch after
epoch. If the pool's "real" price is at a tick far from zero (e.g. WETH/USDC near tick
200,000), the on-chain EMA silently diverges from reality. An attacker who can suppress
trading in the underlying pool (by sandwiching every swap, bribing block builders, or
exploiting Angstrom's MEV-mitigation quiet period) can pull the oracle EMA toward 0 and
then exploit the mispriced oracle downstream.

The clamp at `clampDelta` bounds the **per-update** movement but not the **cumulative**
movement. Over N stagnant epochs, the EMA drifts by up to `N × clampDelta` from its
starting position toward 0. With `clampDelta = 100` and 256 stagnant observations, the EMA
drifts up to 25,600 ticks — enough to dislocate most option pricing.

**Concrete setup.**
1. Build a buffer of 256 observations where `cumulativeGrowth` is identical across all
   observations (`5e30` for each, block numbers strictly monotonic 12 seconds apart).
2. Initialize an OraclePack with `lastTick = 200000` and all four EMAs at 200000.
3. Warp forward one epoch, call `updateGrowthEMA(buffer, pack, periods, clampDelta=100)`.
4. Persist the return value, warp another epoch, re-record a new latest observation
   (still with `cumulativeGrowth = 5e30`), re-call updateGrowthEMA.
5. Repeat for 500 epochs.

**Assertion.**
- After 1 call, returned `spotEMA` has moved toward 0 by at most `clampDelta`.
- After 500 calls, `spotEMA` has drifted from 200000 to a value within `[199500, 199999]`
  (bounded linear drift toward 0). Assert the drift is strictly monotonic toward 0.
- **Economically meaningful assertion:** if `clampDelta × epochsInWindow > |lastTick - 0|`,
  then after enough stagnant epochs the EMA can cross zero and become negative. Document
  this threshold explicitly. For `clampDelta = 100` with starting tick 200000, this is
  2000 stagnant epochs ≈ 35 hours — a plausibly long quiet period on an illiquid pool.
- **Recommendation in finding:** require `clampDelta` to be set conservatively (≤ 10 per
  update for hourly cadence) so the 35-hour window extends beyond plausible attacker
  influence, OR require the caller to detect stagnation (oldest.cg == latest.cg) and skip
  the update (propose a `StagnantBuffer()` early-return instead of feeding tick 0 into the
  EMA).

**Why P0.** Oracle-manipulation attack vector. Confirmed. Similar pattern to the Curve LP
oracle attacks. The clamp is not a defense — it is a *rate-limiter* on a drift that
eventually completes.

---

### Family F — Epoch Gate Attacks

The epoch gate (`currentEpoch == currentOraclePack.epoch()` early-return) and the unchecked
subtraction `uint24(currentEpoch - oraclePack.epoch()) * 64` are both novel to this library
and are not exercised by any BTT branch adversarially.

---

#### F.1 `test__SecurityEdge__EMA_SameEpochNoOpIsBitwiseIdentical` — **P0**

**Attack / failure mode.** The BTT Property 1 says "updateGrowthEMA returns unchanged within
the same epoch." This is typically tested by comparing one or two fields (like `epoch()` or
`spotEMA()`). But `OraclePack` is a packed 256-bit word with **11 distinct fields**
(epoch, orderMap, 4 EMAs, lockMode, referenceTick, currentResiduals, lastResidual). A bug
that overwrites a sub-field while leaving the commonly-checked fields intact would pass a
field-by-field test but corrupt state.

Furthermore: the early-return happens *before* the buffer precondition check. If the caller
is on the same epoch but with a 0- or 1-observation buffer, the function returns the
original pack (no revert). This is the intended behavior, but it means the early-return is
**the only path** that can be called with an insufficient buffer without reverting. A
keeper that calls `updateGrowthEMA` rapidly could observe different behaviors depending on
whether a prior call already bumped the epoch — making upstream logic state-dependent in
subtle ways.

**Concrete setup.**
1. Build a full, valid buffer.
2. Construct an OraclePack `P0` with arbitrary non-zero values for every sub-field
   (epoch, all 4 EMAs, reference, residuals, lockMode, orderMap).
3. Warp `block.timestamp` so `(block.timestamp >> 6) & 0xFFFFFF == P0.epoch()` exactly.
4. Call `updateGrowthEMA(buffer, P0, periods, clampDelta)`.
5. Compare the returned pack to `P0` **using raw `OraclePack.unwrap` equality**, not
   field-by-field.

Also execute:
6. Same timestamp, but pass a buffer with `count == 0` and `count == 1`. Expect the
   same-epoch path to **not revert** (since the precondition check runs only on the new-
   epoch path). Document this as intended behavior.
7. Warp by exactly 63 seconds (still within the same 64-second epoch). Re-call. Expect
   bitwise equality again.
8. Warp by 64 seconds (one epoch ahead). Re-call. Expect the pack to change.

**Assertion.**
- `OraclePack.unwrap(returned) == OraclePack.unwrap(P0)` (bitwise).
- Cases 6, 7 hold.
- Case 8 returns a pack whose `epoch()` has advanced by exactly 1.

**Why P0.** The same-epoch fast path is an optimization that can hide a correctness bug.
An assertion on byte-identity is the only reliable test. Any future refactor that uses
early-return + a cheap field update (e.g. "cheap metadata refresh even within an epoch")
would break this and the test would catch it.

---

#### F.2 `test__SecurityEdge__EMA_OraclePackFromFutureProducesGiantTimeDelta` — **P0**

**Attack / failure mode.** The unchecked subtraction is:
```
timeDelta = int256(uint256(uint24(currentEpoch - currentOraclePack.epoch()))) * 64
```

When `oraclePack.epoch() > currentEpoch` (pack is "from the future"), the `uint24` subtraction
wraps to a very large value (close to `2^24`). Then `* 64` produces a `timeDelta` up to
`(2^24 - 1) * 64 ≈ 1.07 × 10^9` seconds (~34 years).

How could `oraclePack.epoch() > currentEpoch` happen?
1. **EVM reorg / testnet time warp:** `block.timestamp` regresses after a reorg. Mainnet
   post-merge timestamps are monotonic but L2 and testnets are not.
2. **Stored pack from a prior deployment:** if the pack is persisted at the diamond layer
   and the diamond is re-deployed on a forked chain with an earlier `block.timestamp`, the
   pack's recorded epoch is ahead of the current chain.
3. **Keeper passing a pack from a different chain / context.** The library signature accepts
   an `OraclePack` by value — there is no check that the pack was produced by the same
   storage context.
4. **24-bit epoch wrap:** the BTT spec notes the 24-bit counter wraps every ~34 years. A
   pack stored just before the wrap would have `epoch() = 0xFFFFFE` while the current epoch
   is `0x000000` — the subtraction `0 - 0xFFFFFE = 0x000002` wraps to 2, producing a
   timeDelta of 128 seconds. **This is correct**, but the test must verify it.

Now the adversarial case: a pack from 1 epoch in the future (`pack.epoch() = currentEpoch + 1`)
wraps the `uint24` subtraction to `2^24 - 1`, giving `timeDelta = (2^24 - 1) * 64 ≈ 10^9`
seconds. Passed to `OraclePack.updateEMAs`, this would collapse the EMA toward the new tick
in a single step (the "time delta cap" mentioned in the BTT Section 1.5 clamps at 75%
convergence, but that is still a **catastrophic single-update shift** — the EMA jumps 75% of
the way from its current value to the new observation).

**Concrete setup.** Four deterministic cases:
1. `currentEpoch = 100, pack.epoch() = 50` — normal forward advance. `timeDelta = 50 * 64 = 3200`.
2. `currentEpoch = 0, pack.epoch() = 0xFFFFFF` — legitimate epoch wrap after ~34 years.
   `timeDelta = 1 * 64 = 64`. Assert correct.
3. `currentEpoch = 100, pack.epoch() = 101` — pack is 1 epoch in the future (reorg or time
   warp). `timeDelta = (2^24 - 1) * 64 ≈ 1.07e9`. Assert the EMAs are catastrophically
   re-weighted.
4. `currentEpoch = 100, pack.epoch() = 0x7FFFFF` (mid-range future). `timeDelta ≈ (2^24 - 0x7FFFFF + 100) * 64`
   — some large value. Assert behavior.

**Assertion.**
- Case 1 is the baseline.
- Case 2 is correct (the wrap is intentional).
- Case 3 produces an EMA that converges ≥ 50% toward `clampedTick` in one update. Flag
  this as a potential corruption vector.
- **Recommendation:** add an explicit check `if (currentOraclePack.epoch() > currentEpoch) return currentOraclePack;`
  (ignore future packs) OR revert with `OraclePackFromFuture()`. The current behavior silently
  accepts the pack and corrupts the EMA.

**Why P0.** Silent miscomputation triggered by an adversarial but plausible state (reorg,
time warp, cross-chain pack). The unchecked wrap is intentional for the 34-year boundary
but incidentally accommodates adversarial inputs.

---

#### F.3 `test__SecurityEdge__EMA_Uint24EpochWrapAroundCorrectness` — **P1**

**Attack / failure mode.** Confirms the 24-bit epoch boundary at `~34 years from Unix epoch 0`
works correctly. Although ~34 years is long, the `block.timestamp >> 6` formula starts from
Unix epoch 0, not from deployment — so the counter is **already at `~1.74e9 / 64 ≈ 2.7e7`**
(about 27 million), which is past `2^24 = 16.7M`. **The counter has already wrapped at least
once.** Current epoch on mainnet is roughly `(block.timestamp >> 6) & 0xFFFFFF`, giving a
value in `[0, 2^24)`.

This means **every pack's epoch is already post-wrap** and the "unchecked subtraction wraps
on counter rollover" comment in the source is describing the current reality, not a far-
future edge case.

The test must verify that two packs stored on opposite sides of a 24-bit wrap boundary
produce a correct `timeDelta`.

**Concrete setup.** Use `vm.warp` to set `block.timestamp` such that:
1. `(block.timestamp >> 6) & 0xFFFFFF == 0xFFFFFE`, pack.epoch() = 0xFFFFFD → timeDelta = 64.
2. Warp by 128 seconds → `currentEpoch = 0x000000` (wrapped), pack.epoch() still 0xFFFFFD
   → `uint24(0 - 0xFFFFFD) = 3`, timeDelta = 192. Correct.
3. Warp by 64 more seconds → `currentEpoch = 0x000001`, pack.epoch() = 0 → timeDelta = 64.

**Assertion.** All three cases produce the correct (epochs × 64) timeDelta. No wrap
corrupts the delta. The EMA convergence happens at the correct rate across the wrap.

**Why P1.** The 24-bit wrap happens every ~34 years counting from Unix epoch 0. In practice
the current mainnet state has already wrapped. A test pins this.

---

### Family G — Clamp Escape & Degenerate Parameters

---

#### G.1 `test__SecurityEdge__EMA_NegativeClampDeltaInvertedSemantics` — **P0**

**Attack / failure mode.** `clampDelta` is typed as `int24` but semantically represents a
non-negative distance. `OraclePack.clampTick` implementation:
```
if (newTick > _lastTick + clampDelta)  clamped = _lastTick + clampDelta;
else if (newTick < _lastTick - clampDelta) clamped = _lastTick - clampDelta;
else clamped = newTick;
```
With `clampDelta < 0`:
- The upper bound `_lastTick + clampDelta` is **below** `_lastTick`.
- The lower bound `_lastTick - clampDelta` is **above** `_lastTick` (subtracting a negative).
- Now `upper < lower`. The first branch `newTick > upper` is satisfied by essentially every
  `newTick`, clamping to the (negative-adjusted) upper. The second branch `newTick < lower`
  is also satisfied by essentially every `newTick`, clamping to the (positive-adjusted)
  lower.
- The branches are checked in order — the first branch wins. Result: every `newTick` is
  pulled *down* by `|clampDelta|` from `_lastTick`, regardless of the actual computed tick.

This is a **silent miscomputation**: the library does not validate `clampDelta >= 0`.
Furthermore, in `unchecked` arithmetic, `_lastTick + clampDelta` can wrap int24 if
`_lastTick + clampDelta < MIN_TICK` or `_lastTick - clampDelta > MAX_TICK`.

**Concrete setup.** Five cases:
1. `clampDelta = 0` — expect `clamped == _lastTick` (all ticks pinned). Confirms BTT 6.6.
2. `clampDelta = -1` — a narrow negative. Compute the expected result manually and compare.
3. `clampDelta = type(int24).min = -8388608` — extreme negative.
4. `clampDelta = type(int24).max = 8388607` — extreme positive (BTT 6.7, no clamp).
5. `clampDelta = 100, _lastTick = MAX_TICK` — unchecked addition `MAX_TICK + 100` wraps
   int24 to a value below `MIN_TICK`. Check the clamp result and see if `TickMath.getTickAtSqrtPrice`
   chokes.

**Assertion.**
- Case 1 returns `_lastTick` for every input.
- Case 2 clamps to `_lastTick - 1` for all but the one exact `newTick == _lastTick - 1` input.
- Case 3 produces a clamped tick outside `[MIN_TICK, MAX_TICK]` range if unchecked arithmetic
  wraps; document this as a TickMath out-of-range output that would cause downstream
  failures.
- Case 5 likely wraps and produces a ridiculous clamped tick. Document.
- **Recommendation:** add `require(clampDelta >= 0, InvalidClampDelta());` at the start of
  `updateGrowthEMA`. This test would become a simple revert assertion.

**Why P0.** Silent miscomputation on a parameter that has no runtime validation. An
operator who configures `clampDelta = -100` by mistake would see the oracle silently
produce drifting ticks with no revert signal. This is a governance / configuration bug
with silent impact.

---

#### G.2 `test__SecurityEdge__EMA_ClampAddOverflowAtInt24Boundary` — **P1**

**Attack / failure mode.** Independent of sign: `clampTick` performs `_lastTick + clampDelta`
inside an `unchecked` block. With `_lastTick = MAX_TICK = 887272` (or closer to
`type(int24).max = 8388607`) and large positive `clampDelta`, the sum overflows int24. Solidity
0.8+ catches this in checked arithmetic, but `unchecked` allows it to wrap.

Note that `OraclePack.lastTick()` is bounded by the residual encoding, not by `MAX_TICK`
— the reference tick is a 22-bit value in `[-2^21, 2^21 - 1]`, residual is 12-bit, so
`lastTick` can take values up to `~2^21 + 2^11 ≈ 2_099_200`. `MAX_TICK` is 887272, so a
legitimate `lastTick` can exceed `MAX_TICK` briefly during a rebase transition (before
`growthTick` is clamped). This means the clamp output can be passed as `newTick` to
`insertObservation` **outside the TickMath range** — and since `insertObservation` does not
re-check TickMath bounds, the residual would be stored as-is.

**Concrete setup.**
1. Construct an OraclePack with `lastTick()` as close to `type(int24).max` as achievable
   via reference + residual.
2. Set `clampDelta = type(int24).max / 2` and feed a `growthTick = type(int24).max`.
3. Observe the overflow-wrapped clamp result.

**Assertion.**
- The clamp result either (a) wraps int24, producing a clamped tick outside
  `[MIN_TICK, MAX_TICK]`, which `insertObservation` encodes silently; or (b) stays within
  a provably safe range by the structure of OraclePack's residual encoding.
- If (a), document and recommend a post-clamp bound check:
  `clamped = int24(max(MIN_TICK, min(MAX_TICK, clamped)))`.

**Why P1.** Low-probability (requires extreme OraclePack state) but silent miscomputation.

---

#### G.3 `test__SecurityEdge__EMA_EMAperiodsZeroInAnySlot` — **P1**

**Attack / failure mode.** `EMAperiods` is a `uint96` containing four `uint24` period values.
The BTT Fuzz Input Ranges (Section 9) require each period to be `>= 64` (one epoch), but
the library **does not enforce this**. If any of the four periods is 0, the downstream
`updateEMAs` computation likely divides by the period — producing a division-by-zero panic
or, worse, a silent no-op if the implementation is `if (period == 0) return currentEMA`.

A mis-configured governance parameter setting `EMAperiods = 0` (forgotten initialization,
typo in deployment) would permanently freeze or permanently panic the EMA updates.

**Concrete setup.** Four cases:
1. `EMAperiods = 0` (all four slots zero).
2. `EMAperiods = packed(0, 256, 1024, 4096)` — only spot is zero.
3. `EMAperiods = packed(64, 64, 64, 64)` — minimum non-zero (one-epoch periods).
4. `EMAperiods = packed(1, 1, 1, 1)` — periods of 1 *second* (below the one-epoch floor).

**Assertion.**
- Case 1: determine whether `updateEMAs` reverts or silently no-ops. Document.
- Case 2: spot EMA is frozen at its prior value; other EMAs update normally.
- Case 3: EMAs converge but with maximum volatility (no smoothing).
- Case 4: EMAs converge even faster / behave degenerately — document.
- **Recommendation:** add an input-validation helper that rejects any slot < 64:
  `require(spot >= 64 && fast >= 64 && slow >= 64 && eons >= 64, InvalidEMAPeriods());`

**Why P1.** Governance / configuration hygiene. Prevents silent misconfigurations.

---

### Family H — Buffer State Edge Cases

---

#### H.1 `test__SecurityEdge__EMA_BufferWithTwoIdenticalObservations` — **P1**

**Attack / failure mode.** The minimum viable buffer has `count == 2`. If both observations
have **identical `cumulativeGrowth`** (stagnant pool or keeper replaying the same value),
`growthToTick` returns tick 0. This is the shrunken-buffer version of C.2, testing the
minimum-count edge specifically. Also tests that the buffer count check at `< 2` is
inclusive/exclusive correctly.

**Concrete setup.**
1. `record(B=100, t=0, cg=1e18)`.
2. `record(B=101, t=12, cg=1e18)` (same growth).
3. Warp to a new epoch, call `updateGrowthEMA`.

**Assertion.** Returns tick 0. EMAs pull toward 0 (rate-limited by clamp). Same behavior
as E.2 but with the minimum buffer. Confirms no off-by-one in the `count < 2` guard — with
exactly `count == 2`, the function should not revert.

**Why P1.** Boundary confirmation of the BTT spec. Minimum-viable edge.

---

#### H.2 `test__SecurityEdge__EMA_BufferPostWrapOldestIsCorrectSurvivor` — **P1**

**Attack / failure mode.** After the ring buffer wraps (≥ 257 pushes), the "oldest"
observation is no longer at push-index 0 — it is at the middle of the underlying array.
`oldestObservation()` uses `CircularBuffer.last(buffer, total - 1)` where `total` is
`CircularBuffer.count()` saturated at capacity. A bug in this lookup — or a regression
when upgrading OpenZeppelin CircularBuffer — would cause `oldestObservation()` to return
the wrong slot, and `updateGrowthEMA` would compute the growth ratio against a wrong
anchor.

The downstream symptom: the EMA silently tracks a wildly wrong growth rate with no revert.
This is a pure silent-miscomputation attack surface.

**Concrete setup.**
1. Capacity 256 buffer, push 512 observations with strictly-increasing block numbers and
   strictly-increasing `cumulativeGrowth`.
2. Capture the 257th observation (which should be the post-wrap oldest).
3. Call `updateGrowthEMA`.
4. Reverse-compute the expected ratio: `latest.cumulativeGrowth() / (captured 257th).cumulativeGrowth()`.
5. Compute the expected tick via an off-chain Python mirror of `growthToTick`.

**Assertion.** The clamp-input tick from the function matches the reverse-computed value
exactly (before clamp adjustment). Tests that `oldestObservation()` returns the 257th push.

**Why P1.** Silent miscomputation. Differential-style check rooted in post-wrap buffer
mechanics.

---

#### H.3 `test__SecurityEdge__EMA_SameEpochEarlyReturnSkipsBufferCheck` — **P2**

**Attack / failure mode.** The epoch check runs *before* the buffer precondition check.
This means a caller can call `updateGrowthEMA` with an empty or single-observation buffer
**as long as they are on the same epoch as the pack**, and the function returns
`currentOraclePack` unchanged without reverting.

Is this a bug or intended? It is intended (gas optimization: avoid storage reads when we
know the result). But it means the error surface is **state-dependent**:
- At the start of an epoch: `updateGrowthEMA` reverts on empty buffer.
- Mid-epoch (after a successful prior call): `updateGrowthEMA` succeeds on empty buffer.

A caller that clears the buffer (via some admin function) and then immediately calls
`updateGrowthEMA` in the same transaction/epoch would observe no error. Only on the next
epoch would the error surface.

**Concrete setup.** Three cases:
1. Empty buffer + pack.epoch() == currentEpoch → expect no revert, returns pack unchanged.
2. Empty buffer + pack.epoch() != currentEpoch → expect `InsufficientObservations` revert.
3. Single-observation buffer in either epoch case → expect same behavior as (1)/(2).

**Assertion.** All three hold. Document the state-dependent error surface. Optionally
recommend: move the `count < 2` check *before* the epoch check, so the error surface is
uniform regardless of epoch state. Counter-argument: the current ordering is a legitimate
gas optimization for the hot path.

**Why P2.** Low-severity usability concern. Documented for consumer awareness, not
remediation-required.

---

### Family I — Integration Boundary & Silent Failure Modes

---

#### I.1 `test__SecurityEdge__EMA_CurrentEpochBitPackingSurvivesInsertObservation` — **P1**

**Attack / failure mode.** The library passes `uint256(currentEpoch)` (where `currentEpoch`
is a 24-bit value in `[0, 2^24)`) to `insertObservation`. Internally, `storeOraclePack`
does `_currentEpoch << 232` and packs it as the top 24 bits of the 256-bit word. Solidity
silently truncates bits 232+ if `_currentEpoch` exceeds 24 bits.

The library's `currentEpoch` is computed as `uint24((block.timestamp >> 6) & 0xFFFFFF)` so
it is already masked to 24 bits — but the cast-widen-to-uint256 discards the uint24 type
information. A future refactor that passes the raw `block.timestamp >> 6` (dropping the
mask) would produce a `uint256` exceeding 24 bits. Then:
- `_currentEpoch << 232` shifts out bits `>= 24`, silently truncating.
- Two different "current timestamps" could produce the same packed epoch after truncation.
- A future `epoch()` read would return a stale value modulo 2^24, and the same-epoch gate
  would false-positive or false-negative for the wrong range of timestamps.

**Concrete setup.**
1. Warp `block.timestamp` to `0xFFFFFF << 6` (just before the 24-bit wrap).
2. Call `updateGrowthEMA`. Capture `returned.epoch()`.
3. Warp to `0x1000000 << 6` (immediately after wrap).
4. Call `updateGrowthEMA`. Capture `returned.epoch()`.

**Assertion.** Both returned epochs are in `[0, 2^24)`. `returned.epoch()` from step 2 is
`0xFFFFFF`. `returned.epoch()` from step 4 is `0x000000`. The same-epoch gate compares
correctly across the wrap.

**Why P1.** Pin the mask-to-24-bit invariant. A future refactor dropping the mask would be
caught.

---

#### I.2 `test__SecurityEdge__EMA_InvertedAnchorOrderSilentBug` — **P0**

**Attack / failure mode.** Canary for **G.5** from the prior `GrowthToTickLib` audit. The
library calls `growthToTick(latest.cg, oldest.cg)` — with `latest` as the first argument
(currentGrowth) and `oldest` as the second (anchorGrowth). If a future refactor swaps the
argument order (typo, copy-paste, mistaken "alphabetical" reordering), the function
produces a ratio < 1, maps to a negative tick, and the EMA integrates the negative value
silently. No revert. The bug would manifest only as downstream mispricing.

**Concrete setup.**
1. Buffer with `oldest.cg = 1000, latest.cg = 2000` (ratio = 2, tick ≈ 6931).
2. Call `updateGrowthEMA`, capture returned pack's spotEMA contribution via the equivalent
   of `lastTick() - referenceTick()`.
3. Simulate the inverted-argument bug via a mocked-override library (or by manually
   constructing a buffer where oldest > latest — which requires D.4's non-monotonic-growth
   scenario).

**Assertion.** Under correct argument order, the clamped tick fed to `insertObservation`
is positive and matches `growthToTick(2000, 1000)` pre-clamp.

Under the bug scenario, document that the resulting tick is negative with the same absolute
value. Recommend: add an invariant test that `latest.cumulativeGrowth() >= oldest.cumulativeGrowth()`
as a precondition in `updateGrowthEMA` (requires that the observer's record path enforces
monotonic growth — see D.4).

**Why P0.** Silent miscomputation. The library itself does not validate the arg order —
it is structural only. A defensive check would eliminate an entire class of bug.

---

## 3. Summary — Priority Matrix

| ID  | Test Name                                                        | Family | Priority |
|-----|------------------------------------------------------------------|--------|----------|
| E.1 | EMA_ZeroAnchorRevertsFor51Min                                    | E      | P0       |
| E.2 | EMA_StagnantPoolDriftsTowardTick0                                | E      | P0       |
| F.1 | EMA_SameEpochNoOpIsBitwiseIdentical                              | F      | P0       |
| F.2 | EMA_OraclePackFromFutureProducesGiantTimeDelta                   | F      | P0       |
| F.3 | EMA_Uint24EpochWrapAroundCorrectness                             | F      | P1       |
| G.1 | EMA_NegativeClampDeltaInvertedSemantics                          | G      | P0       |
| G.2 | EMA_ClampAddOverflowAtInt24Boundary                              | G      | P1       |
| G.3 | EMA_EMAperiodsZeroInAnySlot                                      | G      | P1       |
| H.1 | EMA_BufferWithTwoIdenticalObservations                           | H      | P1       |
| H.2 | EMA_BufferPostWrapOldestIsCorrectSurvivor                        | H      | P1       |
| H.3 | EMA_SameEpochEarlyReturnSkipsBufferCheck                         | H      | P2       |
| I.1 | EMA_CurrentEpochBitPackingSurvivesInsertObservation              | I      | P1       |
| I.2 | EMA_InvertedAnchorOrderSilentBug                                 | I      | P0       |

**P0 count: 6** — must block production deployment. Each represents either a confirmed
architectural finding (E.1, E.2, I.2) or a novel attack surface (F.1, F.2, G.1).
**P1 count: 6** — should be added before audit closure.
**P2 count: 1** — hardening / documentation.

---

## 4. Cross-Cutting Design Recommendations (not tests)

These surfaced during the audit and would **eliminate entire test classes** if implemented:

1. **Named `ZeroAnchorGrowth()` revert in `GrowthToTickLib`.** Replaces EVM Panic 0x12.
   Test E.1 becomes a trivial `vm.expectRevert`.

2. **`require(clampDelta >= 0, InvalidClampDelta())` at function entry.** Eliminates the
   negative-clampDelta silent-miscomputation surface (G.1). Single-line defense.

3. **`require(currentOraclePack.epoch() <= currentEpoch, OraclePackFromFuture())`.** Rejects
   packs from the future (reorg, time warp, cross-chain). Eliminates F.2's silent-wrap
   attack.

4. **EMAperiods validator:** reject any zero-valued period. Prevents configuration errors
   from freezing the oracle (G.3).

5. **Stagnant-buffer early-return:** when `oldest.cumulativeGrowth() == latest.cumulativeGrowth()`,
   return `currentOraclePack` unchanged (don't feed tick 0 into the EMA). Eliminates the
   drift-toward-tick-0 exploit (E.2, H.1). Requires a design discussion: legitimate
   stagnation vs. legitimate tick-0 observation.

6. **Move buffer precondition check before epoch gate.** Makes the error surface uniform
   (H.3). Trades a small amount of hot-path gas for clearer semantics.

7. **Post-clamp range check:** ensure `clampedTick ∈ [MIN_TICK, MAX_TICK]` before passing
   to `insertObservation`. Prevents G.2's out-of-range tick from corrupting the OraclePack
   residual encoding.

8. **Enforce `latest.cg >= oldest.cg` at the observer's `record()` path.** Eliminates D.4's
   non-monotonic-growth wrap surface and makes the argument order G.5 / I.2 structurally
   irrelevant.

---

## 5. Methodology Notes

- Every test should be a **forge fuzz or differential test** using the existing scaffolding
  under `contracts/test/libraries/` and `contracts/test/_adapters/`.
- For tests that require precise `block.timestamp` control (F.1, F.2, F.3, I.1), use
  `vm.warp(..)` extensively. Do NOT assume `vm.roll` also warps.
- For tests that stress the OraclePack bit layout (F.1, I.1, G.2), use `OraclePack.unwrap`
  for byte-exact assertions rather than field-by-field comparison.
- Tests E.1, E.2, H.2, I.2 benefit from a **differential harness against a Python mirror**
  of the `updateGrowthEMA` pipeline. This surfaces silent miscomputations immediately.
- Tests F.2 and G.1 are **destructive**: they intentionally produce corrupted state. Mark
  them clearly and avoid running them against persistent test fixtures.

---

## 6. Threat Model Summary

| Threat                                    | Test(s) covering it         | Severity  |
|-------------------------------------------|-----------------------------|-----------|
| Pool-genesis oracle DoS (zero anchor)     | E.1                         | Critical  |
| Stagnant-pool EMA drift exploit           | E.2, H.1                    | Critical  |
| Reorg / time-warp EMA corruption          | F.2                         | High      |
| Configuration-error oracle freeze         | G.1, G.3                    | High      |
| Bitwise identity of same-epoch no-op      | F.1                         | Medium    |
| Argument-order silent miscomputation      | I.2                         | High      |
| 24-bit epoch wrap correctness             | F.3, I.1                    | Medium    |
| Post-wrap buffer anchor correctness       | H.2                         | Medium    |
| int24 clamp-boundary overflow             | G.2                         | Medium    |
| State-dependent error surface             | H.3                         | Low       |

---

## 7. Closing Audit Statement

`EMAGrowthTransformationLib` is a **compact but fragile composition**. The code itself is
75 lines with no visible bugs, yet the composition inherits the full attack surfaces of
four dependencies (`CircularBuffer`, `GrowthObservation`, `GrowthToTickLib`, `OraclePack`)
and introduces four novel ones (epoch gate, unchecked time-delta wrap, unchecked clamp
arithmetic, stateless persistence contract).

The confirmed P0 architectural findings **C.1 (zero-anchor DoS)** and **C.2 (stagnant-pool
drift)** are directly exploitable through this library. **E.1 and E.2 must be added before
any production use.** The other ten proposals harden the library against future refactors
and configuration errors.

The most impactful single change is **recommendation #5 (stagnant-buffer early-return)**.
It closes the largest silent-miscomputation window the library currently has and requires
only a two-line addition. Recommend it be prioritized over purely-test-based mitigations.
