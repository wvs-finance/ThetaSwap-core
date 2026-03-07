# Implementation Plan: ThetaSwap Fee Concentration Insurance CFMM

**Branch**: `002-theta-swap-cfmm` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-theta-swap-cfmm/spec.md`

## Summary

Build a piecewise-linear CLAMM that prices fee concentration insurance as a V4 hook facet within the MasterHook diamond pattern. PLPs buy protection (premium = streaming V4 fee deductions), underwriters sell protection (deposit collateral into tick ranges). The trading function `y = x - ln(x) - 1` is linearized per tick for O(1) swap math. The insurance facet reads B_T from FeeConcentrationIndex (sibling facet) and uses a per-swap funding rate to align mark price with oracle index price.

## Technical Context

**Language/Version**: Solidity ^0.8.26
**Primary Dependencies**: Uniswap V4 core (PoolManager, Hooks, StateLibrary), forge-std, kontrol-cheatcodes, Solady (FixedPointMathLib), MasterHook diamond (hook-bazaar/monorepo), Compose extensions
**Storage**: Diamond storage pattern (keccak256 slot hashing, disjoint slots per facet)
**Testing**: forge test (unit + fuzz), kontrol prove (formal verification), slither, semgrep
**Target Platform**: EVM (Ethereum mainnet / L2s with Cancun opcodes: TSTORE/TLOAD)
**Project Type**: Smart contract (V4 hook facet)
**Constraints**: SCOP (no inheritance in contracts, no `library` keyword, no `modifier` keyword). Type-driven development (types + invariants before any implementation).

## Constitution Check

Constitution is unpopulated (template only). No gates to enforce. Proceed.

## Project Structure

### Documentation (this feature)

```text
specs/002-theta-swap-cfmm/
├── spec.md              # Feature specification (done)
├── plan.md              # This file (done)
├── research.md          # Phase 0 output (done)
├── data-model.md        # Phase 1 output (done)
├── invariants.md        # Insurance-specific invariants (Phase 2 of TDD)
├── checklists/
│   └── requirements.md  # Quality checklist (done)
├── contracts/           # Interface contracts
│   └── IThetaSwapInsurance.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── types/                               # Existing model-independent UDVTs (reuse)
│   ├── ReserveXMod.sol                  # Reuse for virtual reserves
│   ├── ReserveYMod.sol                  # Reuse for virtual reserves
│   ├── LiquidityMod.sol                 # Reuse for underwriter liquidity
│   ├── SqrtPriceX96Mod.sol              # Reuse for V4 price format
│   ├── TickIndexMod.sol                 # Reuse for tick positions
│   └── ...
├── fee-concentration-index/             # Existing (001), refactored to facet
│   ├── FeeConcentrationIndex.sol        # Refactor: remove BaseHook → facet
│   └── ...                              # Types & modules unchanged
├── theta-swap-insurance/                # NEW — this feature
│   ├── ThetaSwapInsurance.sol           # Main facet: external functions
│   ├── interfaces/
│   │   └── IThetaSwapInsurance.sol      # Public interface
│   ├── modules/
│   │   └── ThetaSwapStorageMod.sol      # Diamond storage
│   ├── types/
│   │   ├── PiecewiseTickMod.sol         # Slope + intercept per tick
│   │   ├── PremiumRateMod.sol           # Streaming premium computation
│   │   ├── FundingRateMod.sol           # fee_base + fee_funding
│   │   ├── IndexPriceMod.sol            # B_T → p_index mapping
│   │   ├── SpotPriceMod.sol             # p_mark from virtual reserves
│   │   ├── CollateralMod.sol            # Single-asset collateral UDVT
│   │   ├── InsurancePositionMod.sol     # PLP protection lifecycle
│   │   ├── UnderwriterPositionMod.sol   # Underwriter position + fees
│   │   └── InsuranceTickBitmapMod.sol   # Initialized tick lookup
│   └── readers/
│       └── OracleReaderMod.sol          # Read getIndex from FCI facet
├── master-hook/                         # MasterHook integration
│   ├── CompositeAfterSwap.sol           # FCI.afterSwap + Insurance.afterSwap
│   ├── CompositeAfterAddLiq.sol         # FCI + Insurance afterAddLiquidity
│   └── CompositeAfterRemoveLiq.sol      # FCI + Insurance afterRemoveLiquidity
test/
├── theta-swap-insurance/
│   ├── unit/                            # Per-type-module unit tests
│   ├── kontrol/                         # Formal proofs (prove_ prefix)
│   └── fuzz/                            # Fuzz tests for invariants
└── master-hook/
    └── integration/                     # E2E: MasterHook + both facets
```

**Structure Decision**: Follows existing project layout from 001 branch. Each feature gets its own directory under `src/` with `types/`, `modules/`, `interfaces/`, `readers/` subdirectories. SCOP constraints: no inheritance, no library keyword, file-level free functions in Mod files.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Composite facets for shared callbacks | FCI and Insurance both need afterSwap, afterAddLiquidity, afterRemoveLiquidity | Diamond can only map one facet per selector. Composite facet calls both in sequence. Alternative (merging into one facet) loses separation of concerns and testability. |
| FCI refactor from BaseHook to facet | MasterHook diamond requires facets, not standalone hooks | Alternative (keeping FCI as standalone) is impossible — V4 only allows one hook per pool. |
