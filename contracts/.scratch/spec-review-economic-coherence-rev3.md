# Economic Coherence Review -- Rev 3

Reviewer: Papa Bear (Opus)
Date: 2026-04-09
Spec: angstrom-panoptic-vault-architecture-design.md (Rev 3)

---

## Finding B1 (CRITICAL): feesAccrued Does NOT Carry Angstrom Rewards

Section 2.7 claims Angstrom's `beforeRemoveLiquidity` hook "pays real asset0 reward tokens" that "appear in the `feesAccrued` return value that the SFPM reads."

This is incorrect. Code trace:

1. **PoolManager.modifyLiquidity** (v4-core Pool.sol:143-189): `feesAccrued` is computed from `Pool.getFeeGrowthInside` -- Uniswap's internal swap-fee accumulators (`feeGrowthInside0X128`, `feeGrowthInside1X128`). These are populated by swap volume, not by hook-injected tokens.

2. **Angstrom's beforeRemoveLiquidity** (PoolUpdates.sol:122-155): Pays rewards via `UNI_V4.sync()` + `safeTransfer` + `UNI_V4.settleFor(sender)`. This credits the sender's PoolManager delta directly. It does NOT write to Uniswap's internal fee growth accumulators.

3. **SFPM** (SemiFungiblePositionManagerV4.sol:1047-1048): Derives `collectedSingleLeg` from `feesAccrued.amount0()` and `feesAccrued.amount1()`. Angstrom rewards land in `callerDelta` (principal), not `feesAccrued` (premium).

Consequence: The SFPM classifies Angstrom rewards as principal movement, not premium. The streaming premium pipeline does NOT naturally pick up Angstrom rewards. The adapter scope described in Section 4.5 is understated -- it needs to handle actual premium accrual, not just fee-growth estimation.

## Finding B2 (INFO): k Clarification Is Adequate

The Q128.128 conversion (multiply by liquidity, right-shift 128) is confirmed by `X128MathLib.fullMulX128` (line 21) and `flatDivX128` (line 10). This is deterministic arithmetic, not a tunable parameter. The spec's description matches the code exactly.

## Finding B3 (INFO): Rev 2 Residual Concerns

- **Bootstrapping** (Section 4.7): Adequately addressed. Protocol seeds initial liquidity; premium accrual is independent of swap volume (per the adapter).
- **Frozen ranges** (Invariant 6.9): Correctly handled. Ratio asymptotes to zero; dead options market is economic reality, not protocol failure.
- **Ratio approximation** (Section 2.3): Acknowledged as known limitation. Arbitrageurs maintain alignment. Acceptable.

---

## Verdict

Section 2.7 and 4.5 rest on the claim that V4's `feesAccrued` return naturally carries Angstrom hook-injected rewards into the SFPM premium pipeline. Code review of PoolManager, Pool.sol, and PoolUpdates.sol proves this is false. `feesAccrued` reflects only Uniswap-native swap fee growth. Angstrom rewards flow through `settleFor`, which adjusts `callerDelta` (principal), not `feesAccrued` (premium). The SFPM adapter therefore cannot be scoped to "just fee-growth estimation" -- it must intercept the premium accrual path itself, which is a materially larger modification than the spec describes. The k clarification and residual risk handling are both sound. The architecture is viable but Section 2.7/4.5 must be corrected before implementation can proceed.

**BLOCK** -- B1 must be resolved. The premium delivery mechanism is architecturally different from what the spec describes.
