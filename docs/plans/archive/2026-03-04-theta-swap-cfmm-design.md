# Design: ThetaSwap Piecewise-Linear CLAMM for Fee Concentration Derivatives

**Date**: 2026-03-04
**Status**: Approved
**Branch**: 002-theta-swap-cfmm (to be created)

## Summary

A standalone concentrated liquidity AMM (CLAMM) that trades fee concentration derivatives. The CFMM implements the trading function `y = x - ln(x) - 1` using piecewise-linear approximations aligned to a Uniswap V3-style tick array. It reads `B_T` (fee dispersion index) from the existing FeeConcentrationIndex V4 hook via direct `getIndex()` calls and uses a per-swap funding rate mechanism to align the mark price with the oracle index price.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scope | Full CFMM contract | Complete on-chain implementation: trading function, reserves, fees, LP ops, swaps |
| Architecture | Standalone pool | Independent contract reading getIndex from V4 hook. Cleanest separation. |
| Concentrated liquidity | Piecewise-linear tick array | Mirrors Uniswap V3. Linear approximation of ln(x) per tick. O(1) swap math within a tick. |
| ln(x) computation | Piecewise linear per tick | Enables CLAMM natively. Error O(10^-9) at 1 bps spacing. gammaDEX-core validated this pattern. |
| Oracle feed | Direct getIndex() call | Synchronous STATICCALL per operation. Always fresh, simplest integration. |
| Token model | Single collateral | Virtual (x, y) reserves tracked internally. All deposits/withdrawals in one collateral token (e.g., USDC). |
| Funding settlement | Per-swap | Embedded in swap fee: fee(t) = fee_base + fee_funding(t). No keeper needed. |

## Architecture

```
Uniswap V4 Pool
  └── FeeConcentrationIndex (Hook)
        └── getIndex(key) → (A_T, B_T)    [STATICCALL]
              │
              ▼
ThetaSwap CFMM (Standalone)
  ├── Oracle: B_T → p_index = B_T / (1 - B_T)
  ├── Tick Array: piecewise-linear ln(x) approximation
  ├── LP Positions: concentrated liquidity [tickLower, tickUpper]
  ├── Funding Rate: per-swap mark-index convergence
  └── Collateral: single asset, virtual reserve accounting
```

## Piecewise-Linear Tick Math

Trading function: `y = x - ln(x) - 1`
Spot price: `p = (1 - x) / x`
Tick definition: `p_i = 1.0001^i`

Within tick `[p_i, p_{i+1}]`, the reserve curve `y(p) = ln(1+p) - p/(1+p)` is linearized at the midpoint:
- `ŷ(p) ≈ y(p_mid) + y'(p_mid) · (p - p_mid)` where `y'(p) = 1/(1+p)²`
- Swap math reduces to `Δy = slope · Δp` — O(1) per tick
- Approximation error: `|y - ŷ| ≤ (1/2) · |y''(p_mid)| · (Δp/2)² ≈ O(10⁻⁹)` at 1 bps

## LP Positions & Collateral

- LP deposits collateral into `[tickLower, tickUpper]` range
- Virtual reserves `(x_virtual, y_virtual)` computed from liquidity L and price range
- Fee accrual: per-tick `feeGrowthPerLiquidity` (like Uniswap V3)
- Funding payments embedded in fee growth

## Funding Rate

```
p_index = B_T / (1 - B_T)          // from oracle
p_mark  = (1 - x_active) / x_active // from CFMM state
basis   = p_mark - p_index
κ_n     = α · |basis| / (p_index + 1)
fee_funding = sign(basis) · min(κ_n, fee_max - fee_base)
fee(t)  = fee_base + fee_funding
```

## Contract Structure (SCOP)

```
src/cfmm/
├── ThetaSwapCFMM.sol
├── interfaces/IThetaSwapCFMM.sol
├── modules/ThetaSwapStorageMod.sol
├── types/
│   ├── TickMathMod.sol
│   ├── VirtualReserveMod.sol
│   ├── LiquidityMod.sol
│   ├── CollateralMod.sol
│   ├── SpotPriceMod.sol
│   ├── IndexPriceMod.sol
│   ├── FundingRateMod.sol
│   ├── TickBitmapMod.sol
│   └── PositionMod.sol
└── readers/OracleReaderMod.sol
```

## References

- Mathematical model: `specs/model/main.tex`
- FeeConcentrationIndex: `src/fee-concentration-index/FeeConcentrationIndex.sol`
- gammaDEX-core (JMSBPP/gammaDEX-core): piecewise function pattern for payoff-to-trading-function
- Angeris et al. 2023, "The Geometry of Constant Function Market Makers"
- Angeris et al. 2021, "Replicating Market Makers"
