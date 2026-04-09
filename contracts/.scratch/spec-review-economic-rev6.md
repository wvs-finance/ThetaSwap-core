# Economic Coherence Review -- Rev 6

Reviewer: Papa Bear (Opus)
Date: 2026-04-09
Verdict: **FLAG**

---

## 1. Rolling-window T resolves the mean-reversion concern -- conditionally

The four-layer architecture correctly separates the convergent cumulative observable from the transformation. A rolling-window T can produce a stationary, mean-reverting underlying suitable for short straddles, as the research report demonstrates. However, the rolling-window T requires on-chain checkpoints (storing accumulator values at periodic intervals). The spec does not address checkpoint storage cost or liveness -- if checkpoints are missed, the window degrades. This is an implementation gap, not a blocker.

## 2. "Vault enforces bounds, T is unconstrained" has a subtle exploit surface

The monotonicity guard clamps the rate to never decrease. A malicious or buggy T that oscillates (returns high then low values) would be clamped to the high-water mark permanently, inflating totalAssets beyond real accrual. The continuity cap partially mitigates this but does not prevent a ratchet exploit where T alternates between max-jump and zero. Recommendation: add a staleness/liveness check -- if T's raw output drops below the previous bounded rate for N consecutive calls, freeze or flag the transformation.

## 3. Denomination mismatch: confirmed FLAG

globalGrowth accumulators are denominated in asset0 (confirmed: PoolUpdates.sol line 146 pays rewards in currency0; line 213 subtracts rewardTotal from asset0 deltas). V_B accepts asset1 deposits. The spec (Section 2.1, 4.2) says "share price is a pluggable transformation T_B of globalGrowth, measured in asset1 terms" but never specifies HOW T_B converts asset0-denominated growth into asset1-denominated rate. T_B needs a price oracle or a fixed conversion factor, neither of which is mentioned. Without this, V_B's totalAssets computation is undefined.

## 4. Remaining blockers

No hard blockers beyond the denomination gap. The checkpoint storage design and ratchet-exploit mitigation are FLAGS that must be resolved before Phase 1 implementation begins.

---

**Verdict: FLAG** -- The architecture is sound but the asset0-to-asset1 conversion in T_B is unspecified, and the monotonicity clamp creates a ratchet surface for adversarial T. Both are resolvable without architectural changes.
