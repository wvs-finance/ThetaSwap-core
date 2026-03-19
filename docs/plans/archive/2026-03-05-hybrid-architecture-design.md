# Design: Hybrid Fee Concentration Insurance Architecture

**Date**: 2026-03-05
**Status**: Approved
**Branch**: 002-theta-swap-cfmm
**Supersedes**: 2026-03-04-theta-swap-cfmm-design.md (Option 1: custom CFMM)

## Summary

Hook-based mutual insurance with ERC-6909 transferable claims and a deferred CFMM market layer. The insurance hook reads A_T, Theta, N from the FeeConcentrationIndex hook via `getIndex()`, derives Delta-plus, collects premiums via fee share redirect, and pays out via `poolManager.donate()` when Delta-plus exceeds Delta-star.

## Empirical Basis

Cross-pool concentration severity analysis (notebook: `notebooks/cross-pool-concentration-severity.ipynb`) established:

- Spearman rho(A_T, log TVL) = +0.19 (weak, within +/-0.3)
- No TVL-concentration correlation: concentration driven by pair type and position count
- All Delta-plus values below Delta-star = 0.09 turning point
- Pools with excess concentration span $35M-$192M TVL

Conclusion: neither pure hook-insurance nor pure CFMM-pool is empirically justified. Hybrid selected.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CFMM market layer | Deferred | Build hook insurance + ERC-6909 only. CFMM layer is future work. ERC-6909 transferability enables markets to emerge organically. |
| Premium collection | Fee share redirect | gamma% of PLP's accrued fees redirected to reserve at removeLiquidity. Explicit, measurable. |
| Payout trigger | donate() on mark-to-market | When Delta-plus > Delta-star at any liquidity event, hook calls poolManager.donate() from reserve. All claim holders benefit via V4's fee distribution. |
| ERC-6909 token ID | uint256(PoolId) | One fungible index asset per pool. Simplest, most composable. |
| Solvency | Pro-rata haircut | If reserve < claims, proportional payout. Reserve never negative. Consistent with fungible claims. |
| Deployment | Separate hook | Insurance hook reads from FCI via getIndex(). Two contracts, clean separation. |
| Approach | A: Minimal Reserve | Per-pool USDC reserve funded by gamma% fee redirect. Self-bootstrapping. No external capital. |

## Architecture

```
Uniswap V4 Pool (any pair)
  +-- FeeConcentrationIndex Hook (existing, branch 001)
  |     +-- getIndex(key) -> (A_T, Theta, N)     [STATICCALL]
  |           |
  |           v
  +-- ThetaSwap Insurance Hook (new, separate contract)
        +-- Reads: A_T, Theta, N from FCI hook
        +-- Derives: Delta-plus = max(0, A_T - sqrt(Theta/N^2))
        +-- Premium: gamma% of PLP's accrued fees redirected at removeLiquidity
        +-- Reserve: per-pool USDC balance
        +-- Payout: donate() when Delta-plus > Delta-star (mark-to-market)
        +-- Claims: ERC-6909 token per pool (tokenId = PoolId)
        +-- Solvency: pro-rata haircut if reserve < claims
```

## Hook Lifecycle

### Registration (afterAddLiquidity)

1. PLP adds liquidity to underlying V4 pool with `hookData = abi.encode(gamma)`
2. Insurance hook stores registration: `registrations[poolId][positionKey] = gamma`
3. Hook mints ERC-6909 claim tokens: `amount = liquidity`, `tokenId = uint256(poolId)`

### Premium Collection (afterRemoveLiquidity)

1. Hook computes PLP's accrued fees from feeGrowthInside
2. Redirects gamma% to per-pool reserve: `reserve[poolId] += gamma * accruedFees`
3. PLP receives `(1 - gamma) * accruedFees` net
4. Burns ERC-6909 claims, clears registration

### Mark-to-Market Payout (any liquidity event where Delta-plus > Delta-star)

1. Hook calls `FCI.getIndex(key)` -> derives Delta-plus
2. If Delta-plus > Delta-star: hook calls `poolManager.donate()` from reserve
3. Donation proportional to `(Delta-plus - Delta-star)` and available reserve
4. All ERC-6909 claim holders benefit via V4's fee distribution (pro-rata)
5. Pro-rata haircut if reserve < computed donation amount

### Deregistration (afterRemoveLiquidity)

1. PLP collects donated fees via normal V4 fee collection
2. ERC-6909 burned, registration cleared

## FCI Hook Extension

The existing FeeConcentrationIndex hook needs two additions:

1. **Track Theta and N**: Add `thetaSum[poolId]` (incremented by 1/blockLifetime at each removal) and `posCount[poolId]` (incremented at add, decremented at remove) to FeeConcentrationIndexStorage.

2. **Extend getIndex() signature**: Return `(uint128 aT, uint128 thetaSum, uint256 posCount)` so the insurance hook can compute Delta-plus.

## ERC-6909 Index Asset

- **tokenId** = `uint256(PoolId)` -- one fungible token per insured pool
- **Minting**: at registration, `amount = liquidity`
- **Burning**: at deregistration
- **Transferability**: standard ERC-6909 transfers. Recipient receives future donate() distributions. Bridge to deferred CFMM layer.
- **No separate USDC token**: reserve is internal accounting. ERC-6909 represents claim on future protection payouts.

## Contract Structure

```
src/theta-swap-insurance/
  ThetaSwapInsurance.sol          # Hook contract (BaseHook + IERC6909)
  interfaces/
    IThetaSwapInsurance.sol       # Updated: remove underwriter methods, add getReserve/getProtectionGrowth
  modules/
    ThetaSwapStorageMod.sol       # Diamond storage: registrations, reserve, protectionGrowth
  types/
    PremiumFactorMod.sol          # Keep: gamma% factor type
    ReserveMod.sol                # NEW: per-pool reserve accounting
    ClaimsMod.sol                 # NEW: ERC-6909 mint/burn/transfer logic
  libraries/
    DonateCalcLib.sol             # NEW: compute donate amount from Delta-plus, Delta-star, reserve

src/fee-concentration-index/
  FeeConcentrationIndex.sol                    # MODIFY: add Theta, N tracking + extended getIndex()
  modules/
    FeeConcentrationIndexStorageMod.sol        # MODIFY: add thetaSum, posCount mappings
```

### Deletions (Option 1 custom CFMM artifacts)

- `InsurancePoolMod.sol` -- custom CFMM trading function
- `LogPriceMod.sol` -- log-price type for custom CFMM
- `LogPriceMath.sol` -- log-price math library
- `SettleMath.sol` -- settlement math for custom CFMM
- `UnderwriterPositionMod.sol` -- underwriter position type
- `MarginMod.sol` -- margin type for custom CFMM

## LaTeX Spec Updates (specs/model/)

| File | Action |
|------|--------|
| main.tex | Replace "pending" with hybrid decision. Update abstract. |
| payoff.tex | No changes (architecture-independent). |
| funding-rate.tex | Update mark price def. Add donate() settlement. Remove CFMM mark price option. |
| invariants.tex | Replace pending stub with: INS-01 reserve solvency, INS-02 premium collection, INS-03 donate trigger, INS-04 claim mint/burn, INS-05 pro-rata fairness. |
| reserves.tex | NEW: reserve accounting (gamma% redirect, per-pool balance, donate depletion). |
| initialization.tex | NEW: hook initialization (set gamma, Delta-star, FCI address). |
| preamble.tex | Add notation: gamma, R (reserve), protectionGrowth. |

## References

- Cross-pool analysis: `notebooks/cross-pool-concentration-severity.ipynb`
- Existing FCI hook: `src/fee-concentration-index/FeeConcentrationIndex.sol`
- Existing spec: `specs/model/main.tex`
- Prior design (superseded): `docs/plans/2026-03-04-theta-swap-cfmm-design.md`
- Angeris et al. 2022, "A Primer on Perpetuals" (funding rate)
- Ma & Crapis 2024 (competitive null A_T^{1/N})
