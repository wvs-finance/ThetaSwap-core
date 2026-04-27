# Security Edge-Case Test Proposals — Growth Observer System

**Document type:** Security audit — adversarial test proposals
**Target surface:** `GrowthObservation.sol` + `BlockNumberAwareGrowthObserverLib.sol` + `EMAGrowthTransformationLib.sol` + `GrowthObservationStorageMod.sol`
**Status:** Audit report — no code written
**Date:** 2026-04-12
**Auditor:** Blockchain Security Auditor

---

## Audit Framing

The growth observer is read-only with respect to Angstrom, but it is **writable by a trusted keeper** and **read by downstream consumers** (EMA transformation, RAN oracle consumers, option pricing, settlement). Compromise modes therefore split into three families:

1. **Liveness / DoS** — cause a downstream reader to revert or return unusably stale data.
2. **Correctness corruption** — cause the buffer or its derived values to silently encode a wrong answer (width narrowing, wrap-around arithmetic, stale reads).
3. **Cross-module inconsistency** — cause the storage module, the library, and the transformation layer to disagree about what is stored.

The existing BTT spec and diff tests cover the **happy path correctness** branches (monotonicity skip, binary search shape, pack round-trip). They do **not** exercise:

- Post-wrap-around behavior of `observeAt` when `_count` has advanced past capacity many times.
- Bit-packing boundary values (`type(uint32).max`, `type(uint16).max`, `type(uint208).max`).
- `EMAGrowthTransformationLib` reading an invalid composite state (oldest == latest, zero-anchor, skipped same-block duplicates).
- The storage module's initialization race and diamond-slot isolation.
- Adversarial keeper input that passes monotonicity but violates other invariants the transformation layer implicitly assumes.

What follows is **12 concrete security-oriented test scenarios** organized by family, with priority tags.

---

## Family A — Bit-packing / Width Narrowing Edge Cases

### A.1 `test__SecurityEdge__BlockNumberUint32BoundaryWrap` — **P0**

**Attack / failure mode.** `GrowthObservation.blockNumber` is uint32. Ethereum mainnet is currently ~20M blocks; at 12 s/block, uint32 exhausts in ~1,633 years. However, the ring buffer's monotonicity check casts the *input* `_blockNumber` via `SafeCastLib.toUint32(_blockNumber)` **inside** `record()` before comparing to the stored uint32. If a caller passes a `uint256 _blockNumber` greater than `type(uint32).max`, the safe-cast reverts — this is correct. But the **comparison** on line 38 also does `toUint32(_blockNumber)` for the skip check. A malicious or buggy keeper that repeatedly passes `_blockNumber = type(uint32).max` followed by `_blockNumber = type(uint32).max + 1` would see the first succeed and the second revert — potentially wedging the recording pipeline if the caller does not handle the revert.

**Concrete setup.** Prime the buffer with a single observation at `blockNumber = type(uint32).max - 1`. Then attempt three records in sequence:
1. `_blockNumber = type(uint32).max` — should push.
2. `_blockNumber = type(uint32).max + 1` — should revert via SafeCastLib.
3. `_blockNumber = 0` — should be silently skipped (stale).

**Assertion.** Step 1 increments count. Step 2 reverts with `SafeCastLib.Overflow`. Step 3 does NOT revert and does NOT change count. After all three steps, `latestObservation().blockNumber() == type(uint32).max`.

**Why P0.** A silent revert path during `record` would halt the keeper pipeline. The behavior must be fully specified and testable so the keeper knows to gracefully handle it far before block ~4.29 billion.

---

### A.2 `test__SecurityEdge__RelativeTimeDeltaUint16Saturation` — **P0**

**Attack / failure mode.** `relativeTimeDelta` is uint16, max 65,535 seconds (≈ 18.2 hours). The natspec says "Overflow reverts via SafeCastLib — this surfaces keeper liveness failures." But if a keeper is offline for > 18.2 hours (consensus halt, Angstrom pause, keeper key rotation), the next `record` call reverts. This is a **liveness cliff**, not just a latent bug. Worse, no existing test verifies this revert is actually reached at exactly the boundary — an off-by-one in SafeCastLib or a subtle cast order could let 65,536 be silently truncated to 0.

**Concrete setup.** Prime an observation at `t = 0`, then try:
1. `relTimeDelta = 65_534` — push succeeds.
2. `relTimeDelta = 65_535` — push succeeds, stored value equals 65,535.
3. `relTimeDelta = 65_536` — must revert with `SafeCastLib.Overflow`.
4. `relTimeDelta = type(uint256).max` — must revert with `SafeCastLib.Overflow`.

**Assertion.** Step 2's stored `relativeTimeDelta()` accessor returns exactly 65535. Steps 3 and 4 both revert with `SafeCastLib.Overflow()` (not silent truncation).

**Why P0.** A silent truncation of `relativeTimeDelta` would cause the EMA transformation to multiply by a very small fake delta — inflating the EMA response disproportionately. Boundary verification is mandatory.

---

### A.3 `test__SecurityEdge__CumulativeGrowthUint208Boundary` — **P1**

**Attack / failure mode.** `cumulativeGrowth` is uint208 (Q80.128 after truncation from Q128.128). The natspec claims ~1.2 million tokens per unit of liquidity. For very thin pools or exotic assets (wstETH, rebasing tokens), Angstrom's `globalGrowth` accumulator could plausibly approach uint208. Two concerns:
1. Does `growthDelta(earlier, later)` still work when both are near `type(uint208).max`? The unchecked subtraction is modulo 2^208.
2. Does `growthToTick` (downstream) survive when `currentGrowth ≈ uint208.max` and `anchorGrowth ≈ 1`? The ratio computation in `FullMath.mulDiv(current, 2^128, anchor)` would overflow 256 bits.

**Concrete setup.**
1. Record `cumulativeGrowth = type(uint208).max - 1` at block B.
2. Record `cumulativeGrowth = type(uint208).max` at block B+1. Check `growthDelta(earlier, later) == 1`.
3. Record `cumulativeGrowth > type(uint208).max` — must revert via SafeCastLib.
4. Invoke `updateGrowthEMA` with oldest `cumulativeGrowth = 1` and latest `cumulativeGrowth = type(uint208).max` — observe whether `growthToTick` reverts with `FullMath` overflow or produces a clamped tick.

**Assertion.** Bit-packing boundary is respected. `growthToTick` either (a) reverts cleanly with a named error propagated from FullMath, or (b) produces a tick that `OraclePackLibrary.clampTick` can bound. Silent wrap is unacceptable.

**Why P1.** Reaching uint208 requires extreme liquidity or degenerate pool state; unlikely but possible. The test documents behavior at the numeric ceiling.

---

## Family B — Ring Buffer / Wrap-Around DoS

### B.1 `test__SecurityEdge__ObserveAtAfterMultipleFullWraps` — **P0**

**Attack / failure mode.** After the buffer fills (256 pushes) and wraps, `CircularBuffer._count` continues incrementing monotonically even though `count()` saturates at 256. The binary search in `observeAt` relies on `CircularBuffer.last(buffer, i)`, which computes `(index - i - 1) % modulus`. If `_count` is never reset, this arithmetic stays correct modulo overflow of `_count` (uint256 — unreachable in practice). But a subtler bug: the BTT spec and diff tests only exercise one wrap. After many wraps (say 10×256 = 2560 pushes), the oldest observation's block number may be far newer than the caller's stale reference, and `observeAt(oldTarget)` must deterministically revert with `ObservationExpired`, not with an internal panic or a returned garbage slot.

**Concrete setup.** Push 2,560 strictly-monotonic observations (10 full wraps). Then call `observeAt(originalFirstBlockNumber)` where `originalFirstBlockNumber` was the very first push.

**Assertion.** The call reverts with `ObservationExpired(targetBlock, oldestBlock)` where `oldestBlock` is the 2,305th block pushed (2560 - 256 + 1 = 2305th). Never panics, never returns a zero observation.

**Why P0.** Silent failures here feed garbage data to the EMA and downstream option pricing. Must be deterministic.

---

### B.2 `test__SecurityEdge__ObserveAtExactlyAtOldestBoundary` — **P0**

**Attack / failure mode.** The boundary `targetBlock == oldest.blockNumber()` is covered in the BTT in words but edge-case wrap interactions are not. After a wrap, the "oldest" slot sits in the middle of the underlying array. `last(buffer, total-1)` computes `(index - total) % modulus`. An off-by-one there (or a change in OZ v5.x) would cause the comparison `oldest.blockNumber() > targetBlock` to be wrong by exactly one block — returning either the oldest when it should revert, or reverting when it should return the oldest.

**Concrete setup.** Fill the buffer to 256, then push 128 more observations (buffer is deep into post-wrap territory). Call:
1. `observeAt(oldestBlock)` — should return the oldest observation exactly.
2. `observeAt(oldestBlock - 1)` — should revert with `ObservationExpired`.
3. `observeAt(oldestBlock + 1)` — should return the oldest observation (nothing newer-or-equal except itself if no other observation is at oldestBlock+1; the second-oldest if one is).

**Assertion.** All three behaviors hold, byte-exact. Explicitly capture the returned observation's full 32-byte value and check against an oracle table computed off-chain.

**Why P0.** A single-block off-by-one in the boundary is a silent-wrong-answer bug, exactly the class that got Curve, Euler, and others drained.

---

### B.3 `test__SecurityEdge__BinarySearchInvariantUnderKeeperGaps` — **P1**

**Attack / failure mode.** The binary search assumes the buffer is sorted by block number in descending order (newest at index 0). This holds if `record()` is ever called with strictly-monotonic `_blockNumber`. But what if the keeper submits blocks `[100, 101, 102, 101, 103, 104]`? The stale `101` is silently skipped. Fine — but what if the keeper submits `[100, 101, 102, 50, 103]`? The `50` is skipped. What if between recording and reading, an `extsload` race inserts a value? The library doesn't support that, but the test must **prove** binary search is correct under every gap pattern, not just under a full dense cadence (which is what the existing `ProductionCadence30MinCoverage` test does).

**Concrete setup.** Use `vm.assume` / fuzz to generate a sequence of 256 `(blockNumber, stale?)` pairs where the "stale" entries violate monotonicity. Apply them all via `record`. Then for each unique block number actually stored, call `observeAt(b)` and verify it returns the observation whose block number equals `b`. For each gap block number `g` (recorded-block-minus-1 for random gaps), `observeAt(g)` returns the largest stored block `< g` (or the oldest if `g == oldestBlock`).

**Assertion.** Binary search returns the correct predecessor for every in-range target block under arbitrary keeper skip patterns.

**Why P1.** This is the invariant the EMA silently depends on. If keeper retries ever desynchronize the monotonic sequence, everything downstream is suspect.

---

## Family C — Cross-Module / Transformation Layer

### C.1 `test__SecurityEdge__EMAUpdateRevertsOnZeroAnchorGrowth` — **P0**

**Attack / failure mode.** `EMAGrowthTransformationLib.updateGrowthEMA` calls `growthToTick(latest.cumulativeGrowth(), oldest.cumulativeGrowth())`. If `oldest.cumulativeGrowth() == 0`, `FullMath.mulDiv(current, Q128, 0)` panics with division-by-zero. The first-ever observation for a brand-new pool could legitimately be zero (no fees accrued yet). As soon as the second observation arrives and the same-epoch gate releases, `updateGrowthEMA` reverts — **every call** — until the oldest observation is finally evicted 256 pushes later.

**Concrete setup.** Initialize a fresh pool buffer. Record:
1. `(block=B, relTime=0, growth=0)` — the genesis-like observation.
2. `(block=B+1, relTime=12, growth=1e18)` at a different epoch.

Call `updateGrowthEMA(...)` with a fresh OraclePack.

**Assertion.** Either (a) the call reverts cleanly with a named error the caller can branch on (ideal — propose adding an explicit check), or (b) it reverts with an EVM Panic 0x12 (current observed behavior). Document the current behavior. If (b), flag this as a **Critical** liveness finding: a single zero-growth first observation poisons the EMA for up to 256 blocks × 12 s = 51 minutes.

**Why P0.** This is a real DoS. The existing EMA BTT spec does not enumerate this. Fix: either guard `record()` to skip zero-growth, or add a named revert in the transformation, or require `record()` to be preceded by a primer observation with non-zero growth.

---

### C.2 `test__SecurityEdge__EMAUpdateWithIdenticalOldestAndLatest` — **P0**

**Attack / failure mode.** If `count == 2` and both observations have equal `cumulativeGrowth` (a stagnant pool — no swaps for > 12 s between the only two recorded blocks), `growthToTick` computes `FullMath.mulDiv(x, Q128, x) = Q128`, then `sqrt(Q128) = 2^64`, then `<<32 = 2^96 = MIN_SQRT_PRICE` or exactly at price 1.0. `TickMath.getTickAtSqrtPrice(2^96)` returns 0 (price 1 = tick 0). That is *correct* semantically. But the EMA then integrates over `timeDelta` epochs worth of tick 0, which for a pool whose "true" tick is wildly different (e.g. WETH/USDC at tick ~200k) produces an EMA that **silently lags reality by catastrophic amounts** until it recovers.

**Concrete setup.** Pool observations: `(B, 0, 5e30)`, `(B+5, 60, 5e30)`. Current real pool tick: `200000`. Previous OraclePack EMA: `198000`. Call `updateGrowthEMA` with clampDelta = 100. Inspect returned OraclePack's EMA fields.

**Assertion.** Document the pull toward tick 0. If the clamp at `clampDelta = 100` bounds the movement to `198000 - 100 = 197900`, accept that. But flag if the clamp is larger or if the pulled-EMA value is ever below a threshold that would mispriced options. Require `clampDelta` to be enforced tightly relative to real volatility.

**Why P0.** This is exactly the oracle-stagnation attack: make the on-chain EMA drift toward tick 0 by stopping trading in the underlying pool, then exploit the mispriced oracle. Bundle-cadence recording does not guarantee price movement between observations.

---

### C.3 `test__SecurityEdge__EMAUpdateWithCountLessThanTwo` — **P1**

**Attack / failure mode.** The transformation layer checks `count < 2` and reverts with `InsufficientObservations`. This is correct but untested in the BTT spec for the *differential* behavior. Fuzz: what if a caller invokes `updateGrowthEMA` immediately after `initializePool` but before `recordObservation`? Does the storage module's `buffers[poolId]` return a zero-sized buffer or panic? The storage module's `recordObservation` does not check initialization — it delegates directly. So `updateGrowthEMA` on an uninitialized pool would see `count == 0` → revert `InsufficientObservations`. But on an *initialized-but-empty* pool, same result. The test must verify both cases yield the same named revert, not a mysterious panic.

**Concrete setup.** Three cases:
1. Pool never `initializePool`'d, call `updateGrowthEMA`.
2. Pool `initializePool`'d, zero `recordObservation` calls, call `updateGrowthEMA`.
3. Pool with exactly 1 observation, call `updateGrowthEMA`.

**Assertion.** Case 1 panics (0x32 out-of-bounds — since `count` call on uninitialized `_data.length == 0`, the `last(0)` on an empty array would underflow). Case 2 reverts with `InsufficientObservations`. Case 3 reverts with `InsufficientObservations`. If case 1 and case 2 are indistinguishable to the caller, that's a usability bug — propose an explicit `PoolNotInitialized` check in the storage module's read paths.

**Why P1.** Prevents confused callers from receiving generic EVM panics. Named errors are a defensive-programming hygiene requirement.

---

## Family D — Keeper / Replay / State Inconsistency

### D.1 `test__SecurityEdge__RecordIdempotencyUnderKeeperRetry` — **P1**

**Attack / failure mode.** The natspec says "idempotent for keeper retries." Verify that calling `record(B, t, g)` three times in a row with identical args produces exactly one observation in the buffer. Also verify that `record(B, t, g)` followed by `record(B, t', g')` (same block, different time/growth) silently drops the second — meaning **the first write wins and the keeper cannot correct a bad write within the same block**.

**Concrete setup.**
1. `record(100, 12, 1000)` → count becomes 1, latest = (100, 12, 1000).
2. `record(100, 24, 2000)` → count stays 1, latest UNCHANGED.
3. `record(100, 0, 0)` → count stays 1, latest UNCHANGED.
4. `record(101, 12, 1500)` → count becomes 2, latest = (101, 12, 1500).

**Assertion.** Steps 2, 3 leave the latest observation byte-identical to the step-1 result. This proves first-write-wins and documents that keeper corrections within a block are impossible.

**Why P1.** If a keeper's first submission is wrong (bug, stale read, half-synced Angstrom state), the error is locked in for that block. The test documents this so downstream consumers know they cannot trust single observations — they must smooth over several.

---

### D.2 `test__SecurityEdge__StorageModDiamondSlotCollisionIsolation` — **P2**

**Attack / failure mode.** `GrowthObservationStorage` lives at a fixed keccak256 slot. If any other diamond facet in the downstream system (EMAGrowthStorageMod, AccumulatorConsumerStorageMod, etc.) shares a storage slot by accident — either directly or via sloppy struct packing that extends into an adjacent slot — state corruption is silent. Diamond storage isolation is the #1 foot-gun of the pattern.

**Concrete setup.** Deploy all diamond storage modules (growth observation, EMA, any others in the system). Write distinctive marker values into each module's storage via their respective APIs. Read each module back and verify no cross-contamination. Also compute each module's `STORAGE_SLOT` constant and assert all are pairwise distinct.

**Assertion.** All storage slot constants are pairwise distinct. Distinctive writes to module A are not readable through module B's accessors.

**Why P2.** Low-probability but high-impact. Storage slot constants change rarely; a test here would catch a copy-paste bug immediately after someone adds a new module.

---

### D.3 `test__SecurityEdge__InitializePoolReentrancyAndDoubleInit` — **P1**

**Attack / failure mode.** `initializePool` checks `if ($.initialized[poolId]) revert PoolAlreadyInitialized;`. But the `CircularBuffer.setup()` call in OZ v5.1 first clears `_count` and then calls `Arrays.unsafeSetLength`. If `setup` were ever called on an already-initialized pool (bypassing the guard through an inheritance or delegatecall path), it would reset `_count = 0` and silently erase all prior observations without resizing `_data`. The existing guard is correct *within this module*, but: does the module expose any path (upgrade, migrate, admin function) that could reach `setup` on a live buffer?

**Concrete setup.**
1. `initializePool(poolId, 256)`.
2. Record 100 observations.
3. Call `initializePool(poolId, 256)` again — must revert.
4. Call `initializePool(poolId, 512)` — must revert (even with different size).
5. Scan the module for any function that calls `CircularBuffer.setup` — there should be exactly one, guarded.

**Assertion.** Double-init reverts. Grep for uses of `CircularBuffer.setup` in the codebase returns only the guarded path. No other path can re-setup a live buffer.

**Why P1.** Silent buffer resets erase history. If any upgrade logic or migration function exists now or is added later, this test pins the invariant.

---

### D.4 `test__SecurityEdge__GrowthDeltaUncheckedWrapOnMisorderedInputs` — **P0**

**Attack / failure mode.** `growthDelta(earlier, later)` uses `unchecked` subtraction. The natspec says "Callers MUST ensure `later.cumulativeGrowth() >= earlier.cumulativeGrowth()`." The ring buffer monotonicity guarantees this **by block number**, but not by cumulative growth — Angstrom's globalGrowth is documented as monotonically non-decreasing, but: (a) is it guaranteed non-decreasing across all pools and all pool states? (b) can a fork reorg make a newer observation have a *lower* globalGrowth than an older one because the reorged block's Angstrom state differed? (c) can a subtle Angstrom accounting bug (fee rebate, donation withdrawal) decrement the accumulator?

If any of (a)–(c) hold, `growthDelta` silently wraps to a near-`2^208` value and the EMA transformation's `growthToTick` computes a ratio near `type(uint208).max` — producing a wildly wrong tick that still falls inside `TickMath`'s valid range. Downstream pricing catastrophically mispriced.

**Concrete setup.** Fuzz `record(B1, t1, G1)` then `record(B2, t2, G2)` with `B2 > B1` but `G2 < G1` (deliberately violating the implicit invariant). Read back both observations and compute `growthDelta(obs1, obs2)`. Also invoke `updateGrowthEMA`.

**Assertion.** Option A: `growthDelta` returns a near-`2^208` wrapped value (document this). Option B (recommended): propose adding a `record()` invariant check that rejects observations whose `cumulativeGrowth` is less than the stored latest's `cumulativeGrowth`, with a named error `NonMonotonicGrowth`. Without such a guard, this test serves as the canary.

**Why P0.** This is the most realistic attack vector in the system: Angstrom state is read-only to us, but a reorg or Angstrom bug can feed us descending growth. Silent wrap is unacceptable. A keeper that submits mis-ordered growth values should be rejected, not accommodated.

---

## Summary — Priority Matrix

| ID  | Test Name                                                        | Family | Priority |
|-----|------------------------------------------------------------------|--------|----------|
| A.1 | BlockNumberUint32BoundaryWrap                                    | A      | P0       |
| A.2 | RelativeTimeDeltaUint16Saturation                                | A      | P0       |
| A.3 | CumulativeGrowthUint208Boundary                                  | A      | P1       |
| B.1 | ObserveAtAfterMultipleFullWraps                                  | B      | P0       |
| B.2 | ObserveAtExactlyAtOldestBoundary                                 | B      | P0       |
| B.3 | BinarySearchInvariantUnderKeeperGaps                             | B      | P1       |
| C.1 | EMAUpdateRevertsOnZeroAnchorGrowth                               | C      | P0       |
| C.2 | EMAUpdateWithIdenticalOldestAndLatest                            | C      | P0       |
| C.3 | EMAUpdateWithCountLessThanTwo                                    | C      | P1       |
| D.1 | RecordIdempotencyUnderKeeperRetry                                | D      | P1       |
| D.2 | StorageModDiamondSlotCollisionIsolation                          | D      | P2       |
| D.3 | InitializePoolReentrancyAndDoubleInit                            | D      | P1       |
| D.4 | GrowthDeltaUncheckedWrapOnMisorderedInputs                       | D      | P0       |

**P0 count: 6** — must be added before any production use of the oracle downstream.
**P1 count: 5** — should be added before the audit is closed.
**P2 count: 1** — nice-to-have hardening.

---

## Cross-Cutting Recommendations (not tests — design changes)

While in audit scope, these surfaced as likely code changes that would eliminate entire test classes:

1. **Named error for `growthToTick` anchor == 0.** Replace the current implicit Panic 0x12 with an explicit `ZeroAnchorGrowth()` revert in `GrowthToTickLib`. Test C.1 becomes a simple `vm.expectRevert` assertion instead of a behavioral investigation.

2. **Monotonic growth check in `record()`.** Add, alongside the block-number monotonicity skip, an optional (feature-flagged) check that rejects observations with `cumulativeGrowth < latest.cumulativeGrowth()`. Default off to preserve idempotency semantics; default on in production. Eliminates D.4's unchecked-wrap surface.

3. **`PoolNotInitialized` error in read paths.** The storage module's `recordObservation`, `observeAt`, `latestObservation`, `oldestObservation` all currently panic on uninitialized pools with an EVM 0x32. Replace with a named `PoolNotInitialized(poolId)` revert via an `initialized[poolId]` check. Eliminates C.3 ambiguity.

4. **Prove the keeper access control.** The natspec says "keeper is trusted/access-controlled" but the library itself has no access check — it relies on the storage module's `recordObservation` being called only from a trusted adapter. Verify with a fork test that NO non-adapter caller can reach `recordObservation` (gnosis-style access test). Out of scope for this library, but should be added in the adapter test suite.

---

## Methodology Notes

- Every proposed test should be a **fork test** using the existing `BaseForkTest` infrastructure, because the realistic attack surface involves real Angstrom state and real block numbers near production.
- Boundary tests (A.1, A.2, A.3) can use unit-style setup without forking — but running them as fork tests pins them to real mainnet Angstrom behavior.
- D.4 specifically benefits from being a **differential test** against an off-chain Python oracle that computes the "correct" behavior had the library rejected non-monotonic growth. This surfaces silent wrap immediately.
