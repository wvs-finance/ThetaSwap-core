# Implementation Plan: Fee Concentration Index

**Branch**: `001-fee-concentration-index` | **Date**: 2026-03-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-fee-concentration-index/spec.md`

## Summary

Build an on-chain component that tracks adverse competition risk in Uniswap V4 liquidity provision. The component is a Uniswap V4 hook that computes an HHI-weighted fee concentration index by tracking per-position swap counts (lifetimes), fee share ratios, and sophistication weights. Positions are grouped by tick range for O(1) lookup on afterSwap. The accumulated squared sum is stored persistently; A_T and B_T are derived lazily via sqrt on read.

## Technical Context

**Language/Version**: Solidity ^0.8.26
**Primary Dependencies**: Uniswap V4 core (PoolManager, Hooks, StateLibrary, TickBitmap), forge-std, kontrol-cheatcodes
**Storage**: Uniswap V4 hook storage (contract state mappings)
**Testing**: Foundry (forge test for fuzz), Kontrol (kontrol prove for formal verification)
**Target Platform**: EVM (Ethereum mainnet, L2s)
**Project Type**: Solidity library + hook contract
**Performance Goals**: afterSwap < 50k gas (10 positions), afterRemoveLiquidity < 100k gas
**Constraints**: Q128 fixed-point for fee share ratios, no overflow on squaring, SCOP philosophy (no inheritance in contracts, no library keyword, no modifier keyword)
**Scale/Scope**: Single hook contract, ~5 source files, ~10 invariants

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Project constitution is not yet ratified. Using TDD skill constraints as governing principles:

| Gate | Status | Notes |
|------|--------|-------|
| SCOP: No inheritance in contracts | PASS | Hook contract uses no `is` (tests may use `is Test`) |
| SCOP: No `library` keyword | PASS | All helpers are file-level free functions in Mod files |
| SCOP: No `modifier` keyword | PASS | Inline checks or requireX() free functions |
| TDD: Types and invariants before implementation | PASS | Following TDD skill phases |
| TDD: Per-file review gates | PASS | Each file reviewed before continuing |
| TDD: Kontrol proofs one at a time | PASS | Sequential proof workflow |

## Project Structure

### Documentation (this feature)

```text
specs/001-fee-concentration-index/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output (hook interface)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── fee-concentration-index/
│   ├── types/
│   │   ├── SwapCount.sol           # UDVT: swap count per position
│   │   ├── SwapCountMod.sol        # Mod file with free functions
│   │   ├── FeeShareRatio.sol       # UDVT: x_k in Q128
│   │   ├── FeeShareRatioMod.sol    # Mod file: division, squaring
│   │   ├── AccumulatedHHI.sol      # UDVT: sum of theta_k * x_k^2
│   │   └── AccumulatedHHIMod.sol   # Mod file: addTerm, sqrt, toIndexA, toIndexB
│   ├── TickRangeRegistryMod.sol    # Free functions: register, deregister, lookup by tick range
│   ├── PositionLifetimeMod.sol     # Free functions: start, incrementSwapCount, end
│   └── FeeConcentrationIndexMod.sol # Free functions: computeFeeShare, computeTheta, updateIndex, readIndex
│
test/
├── fee-concentration-index/
│   ├── kontrol/
│   │   ├── SwapCount.k.sol         # Kontrol proofs for SwapCount UDVT
│   │   ├── FeeShareRatio.k.sol     # Kontrol proofs for Q128 overflow safety
│   │   ├── AccumulatedHHI.k.sol    # Kontrol proofs for accumulation + sqrt
│   │   ├── TickRangeRegistry.k.sol # Kontrol proofs for register/deregister
│   │   └── IndexUpdate.k.sol       # Kontrol proofs for full index update
│   └── fuzz/
│       ├── PositionLifetime.t.sol  # Fuzz tests for lifetime tracking
│       ├── FeeShareRatio.t.sol     # Fuzz tests for Q128 arithmetic
│       ├── IndexUpdate.t.sol       # Fuzz tests for index formula
│       └── TickRangeRegistry.t.sol # Fuzz tests for registry operations
```

**Structure Decision**: Single-project layout following existing `src/` convention. Types in `src/fee-concentration-index/types/` with Mod pattern. Logic in file-level free functions (Mod files). Tests split between Kontrol formal proofs and Foundry fuzz tests.

## Post-Design Constitution Re-check

| Gate | Status | Notes |
|------|--------|-------|
| SCOP: No inheritance in contracts | PASS | Hook contract standalone, no `is` in production code |
| SCOP: No `library` keyword | PASS | All logic in Mod files (file-level free functions) |
| SCOP: No `modifier` keyword | PASS | Inline checks, requireX() free functions |
| TDD: Types and invariants before implementation | PASS | data-model.md defines all entities before code |
| TDD: Per-file review gates | PASS | Each file reviewed before continuing |
| TDD: Kontrol proofs one at a time | PASS | Sequential proof workflow planned |

## Phase Completion

| Phase | Status | Output |
|-------|--------|--------|
| Phase 0: Research | COMPLETE | [research.md](./research.md) — 6 research decisions (R1-R6) |
| Phase 1: Design | COMPLETE | [data-model.md](./data-model.md), [contracts/](./contracts/) |
| Phase 2: Tasks | PENDING | Awaiting `/speckit.tasks` |

## Complexity Tracking

No constitution violations requiring justification.
