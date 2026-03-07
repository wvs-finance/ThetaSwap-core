# Tasks: ThetaSwap Fee Concentration Insurance CFMM

**Input**: Design documents from `/specs/002-theta-swap-cfmm/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/IThetaSwapInsurance.md
**Methodology**: Type-Driven Development (TDD) — invariants and types before implementation, Kontrol proofs per type
**Constraints**: SCOP (no inheritance, no `library`, no `modifier`), Diamond storage pattern

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory structure, invariants, and project skeleton

- [X] T001 Create directory structure: `src/theta-swap-insurance/{interfaces,modules,types,readers}/`, `src/master-hook/`, `test/theta-swap-insurance/{unit,kontrol,fuzz}/`, `test/master-hook/integration/`
- [X] T002 Write insurance-specific invariants (INS-001 through INS-010) in `specs/002-theta-swap-cfmm/invariants.md`
- [X] T003 Create IThetaSwapInsurance.sol interface (events, errors, external function signatures) in `src/theta-swap-insurance/interfaces/IThetaSwapInsurance.sol` from `specs/002-theta-swap-cfmm/contracts/IThetaSwapInsurance.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: FCI refactor to facet, diamond storage, shared types that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

### FCI Refactor

- [ ] T004 Refactor `src/fee-concentration-index/FeeConcentrationIndex.sol`: remove BaseHook inheritance, convert to diamond facet pattern (remove constructor, use diamond storage, expose callbacks as external functions callable via delegatecall)
- [ ] T005 Update all FCI tests in `test/fee-concentration-index/` to work with refactored facet (deploy via harness that simulates delegatecall context)

### Diamond Storage & Oracle

- [ ] T006 Create `src/theta-swap-insurance/modules/ThetaSwapStorageMod.sol`: diamond storage structs (InsurancePool, PLPProtectionPosition, UnderwriterPosition, InsuranceTick, OracleSnapshot) with keccak256 slot accessors per `specs/002-theta-swap-cfmm/data-model.md`
- [ ] T007 Create `src/theta-swap-insurance/readers/OracleReaderMod.sol`: free functions to read `getIndex()` from FCI facet via diamond self-call, compute `p_index = B_T / (1 - B_T)` (Q128)

### Shared Types (needed by multiple user stories)

- [ ] T008 [P] Create `src/theta-swap-insurance/types/CollateralMod.sol`: UDVT `type Collateral is uint256` (WAD-scaled), free functions: `add`, `sub`, `isZero`, `unwrap`, `fromUint256`
- [ ] T009 [P] Create `src/theta-swap-insurance/types/PiecewiseTickMod.sol`: struct with `slopeQ128` (int256) and `interceptQ128` (int256), free functions: `computeCoefficients(int24 tick, int24 tickSpacing)` (linearize `y = ln(1+p) - p/(1+p)` at tick midpoint), `evalY(slope, intercept, deltaP)`, `evalDeltaY(slope, deltaP)`
- [ ] T010 [P] Create `src/theta-swap-insurance/types/InsuranceTickBitmapMod.sol`: tick bitmap for initialized tick lookup, free functions: `flipTick`, `nextInitializedTickWithinOneWord`, `isInitialized` (follows V4 TickBitmap pattern adapted for insurance tick array)
- [ ] T011 [P] Create `src/theta-swap-insurance/types/IndexPriceMod.sol`: UDVT `type IndexPrice is uint256` (Q128), free functions: `fromBT(uint128 indexB)` → `p_index = B_T / (1 - B_T)`, `unwrap`, `isZero`
- [ ] T012 [P] Create `src/theta-swap-insurance/types/SpotPriceMod.sol`: UDVT `type SpotPrice is uint256` (Q128), free functions: `fromReserves(uint256 virtualX)` → `p_mark = (1-x)/x`, `unwrap`

### Kontrol Proofs for Foundational Types

- [ ] T013 [P] Create `test/theta-swap-insurance/kontrol/CollateralMod.k.sol`: prove round-trip (wrap/unwrap), add/sub commutativity, no overflow on valid inputs
- [ ] T014 [P] Create `test/theta-swap-insurance/kontrol/PiecewiseTickMod.k.sol`: prove piecewise error bound `|y - y_exact| <= epsilon` per tick, slope sign correctness
- [ ] T015 [P] Create `test/theta-swap-insurance/kontrol/IndexPriceMod.k.sol`: prove `fromBT` correctness (B_T=0 → p_index=0, B_T→1 → p_index→MAX), no division by zero
- [ ] T016 [P] Create `test/theta-swap-insurance/kontrol/SpotPriceMod.k.sol`: prove `fromReserves` bounds, no division by zero when x > 0

**Checkpoint**: Foundation ready — diamond storage, oracle reader, shared types, and FCI facet all in place

---

## Phase 3: User Story 3 — Initialize Insurance Pool (Priority: P2)

**Goal**: Pool creator initializes a ThetaSwap insurance pool for a V4 pool, linking it to FCI and setting CFMM parameters

**Independent Test**: Deploy ThetaSwapInsurance facet, call `initialize()`, verify state stored correctly, verify double-init reverts

**Why first**: US1 and US2 both require an initialized pool. This is the prerequisite.

### Implementation for User Story 3

- [ ] T017 [US3] Implement `initialize()` in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: validate params (feeBase < feeMax, alpha > 0, tickSpacing valid), store InsurancePool state, compute and cache piecewise-linear coefficients for all ticks via `PiecewiseTickMod.computeCoefficients`, set initial virtual reserves from `initialSqrtPrice`, emit `InsurancePoolInitialized`
- [ ] T018 [US3] Write unit test for `initialize()` in `test/theta-swap-insurance/unit/Initialize.t.sol`: test happy path (state stored correctly, coefficients computed), test revert on double-init (`InsurancePool__AlreadyInitialized`), test revert on invalid params

**Checkpoint**: Insurance pool can be initialized and read. Prerequisite for US1 and US2.

---

## Phase 4: User Story 1 — PLP Buys Fee Concentration Protection (Priority: P1) MVP

**Goal**: PLPs register their V4 position for insurance, stream fees as premium, receive protection that appreciates with concentration, auto-close when margin depleted

**Independent Test**: Register a PLP, simulate fee accrual via swaps, verify premium streams out and protection value accrues. Simulate margin depletion → auto-close.

### Types for User Story 1

- [ ] T019 [P] [US1] Create `src/theta-swap-insurance/types/InsurancePositionMod.sol`: struct PLPProtectionPosition (owner, v4PositionId, premiumFraction Q128, margin WAD, feeGrowthBaseline, protectionValue, registrationBlock, isActive), free functions: `create`, `accruePremium(feeAccrued, premiumFraction) → (premiumAmount, newMargin)`, `accrueProtection(deltaProtection)`, `shouldAutoClose(minMargin) → bool`, `close() → (marginReturned, protectionValue)`
- [ ] T020 [P] [US1] Create `src/theta-swap-insurance/types/PremiumRateMod.sol`: UDVT `type PremiumRate is uint256` (Q128), free functions: `fromFeeAccrual(feeAccrued, premiumFraction)` → premium amount, `streamPremium(position, feeGrowthDelta)` → updated position with premium deducted from margin

### Kontrol Proofs for US1 Types

- [ ] T021 [P] [US1] Create `test/theta-swap-insurance/kontrol/InsurancePositionMod.k.sol`: prove margin monotonically decreases with premium accrual (INS-001), prove auto-close triggers iff margin <= MIN_MARGIN (INS-002), prove self-sizing (INS-003)
- [ ] T022 [P] [US1] Create `test/theta-swap-insurance/kontrol/PremiumRateMod.k.sol`: prove premium conservation (premium deducted from margin = premium routed to pool), prove zero-fee → zero-premium

### Implementation for User Story 1

- [ ] T023 [US1] Implement `registerForInsurance()` in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: validate pool initialized, validate v4PositionId exists (via StateLibrary), validate underwriter liquidity > 0, validate premiumFraction in (0, Q128_ONE], create PLPProtectionPosition, snapshot feeGrowthBaseline, emit `PLPRegistered`
- [ ] T024 [US1] Implement `deregisterInsurance()` in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: validate position exists and is active, compute final premium + protection, close position, return margin + protection value, emit `PLPDeregistered`
- [ ] T025 [US1] Implement `_insuranceAfterAddLiquidity()` in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: if sender is registered PLP, snapshot fee baseline for new liquidity, activate insurance streaming
- [ ] T026 [US1] Implement `_insuranceAfterRemoveLiquidity()` in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: if sender is registered PLP, compute final fee accrual, deduct last premium, check auto-close conditions (margin <= MIN_MARGIN or fee stream = 0), close position if triggered, emit `PLPAutoClose` if auto-closed
- [ ] T027 [US1] Implement premium streaming in `_insuranceAfterSwap()` (partial — PLP premium accrual only) in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: for each active PLP, compute feeGrowthDelta since last snapshot, deduct premiumFraction as premium, update margin, check auto-close

### Unit Tests for User Story 1

- [ ] T028 [US1] Write unit tests in `test/theta-swap-insurance/unit/PLPProtection.t.sol`: test register (happy path + all revert cases), test premium streaming (premium deducted proportionally to fees), test auto-close on margin depletion, test auto-close on fee stream cessation, test deregister returns margin + protection

**Checkpoint**: PLPs can register, stream premiums, receive protection, and auto-close. Core value proposition testable.

---

## Phase 5: User Story 2 — Underwriter Provides Insurance Backing (Priority: P1)

**Goal**: Underwriters deposit collateral into tick ranges, earn streaming premiums from PLPs, bear risk when concentration rises

**Independent Test**: Deposit collateral into a tick range, simulate PLP premium streaming + swaps, verify underwriter earns premiums and can withdraw collateral + earnings.

### Types for User Story 2

- [ ] T029 [P] [US2] Create `src/theta-swap-insurance/types/UnderwriterPositionMod.sol`: struct UnderwriterPosition (owner, tickLower, tickUpper, liquidity, collateralDeposited, premiumGrowthInsideBaseline Q128, protectionPayoutsBaseline Q128), free functions: `create`, `computePremiumsEarned(currentPremiumGrowthInside)`, `computeProtectionPayouts(currentPayoutsInside)`, `computeNetReturn()` → collateral + premiums - payouts
- [ ] T030 [P] [US2] Create `src/theta-swap-insurance/types/FundingRateMod.sol`: UDVT `type FundingRate is int256` (Q128, signed), free functions: `compute(uint24 feeBase, uint24 feeMax, uint128 alpha, IndexPrice pIndex, SpotPrice pMark)` → `fee_base + sign(pMark - pIndex) * min(alpha * |pMark - pIndex| / (pIndex + 1), feeMax - feeBase)`, `toEffectiveFee()`, `isPositive()`, `abs()`

### Kontrol Proofs for US2 Types

- [ ] T031 [P] [US2] Create `test/theta-swap-insurance/kontrol/UnderwriterPositionMod.k.sol`: prove net return = collateral + premiums - payouts, prove premiums proportional to liquidity share
- [ ] T032 [P] [US2] Create `test/theta-swap-insurance/kontrol/FundingRateMod.k.sol`: prove funding rate bounds `|fee_funding| <= fee_max - fee_base` (INS-007), prove `fee(t) >= 0` always (fee_base >= 0, bounded correction), prove convergence direction (sign matches mark-index divergence)

### Implementation for User Story 2

- [ ] T033 [US2] Implement `addUnderwriterLiquidity()` in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: validate tick range (tickLower < tickUpper, divisible by tickSpacing, within bounds), compute collateral required from virtual reserves at tick range, update InsuranceTick liquidityNet/liquidityGross at both ticks, flip tick bitmap, update activeLiquidity if range contains currentTick, snapshot premiumGrowthInside/protectionPayoutsInside baselines, transfer collateral from sender, emit `UnderwriterAdded`
- [ ] T034 [US2] Implement `removeUnderwriterLiquidity()` in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: validate position exists, compute earned premiums and protection payouts since baseline, compute net return (collateral + premiums - payouts), update tick state (decrement liquidity), flip bitmap if tick becomes uninitialized, update activeLiquidity, transfer collateral to sender, emit `UnderwriterRemoved`
- [ ] T035 [US2] Implement full `_insuranceAfterSwap()` in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: read oracle (B_T via OracleReaderMod), compute p_index and p_mark, compute funding rate, accrue streaming premiums to underwriter tick accumulators (premiumGrowthOutside), handle tick crossings (update activeLiquidity += liquidityNet, flip premiumGrowthOutside/protectionPayoutsOutside), update virtual reserves using piecewise-linear coefficients, emit `PremiumAccrued`
- [ ] T036 [US2] Implement tick crossing logic as free functions in `src/theta-swap-insurance/ThetaSwapInsurance.sol` (or a helper Mod): `crossTick(tick)` → update activeLiquidity, flip outside accumulators; `computePremiumGrowthInside(tickLower, tickUpper, currentTick, globalPremiumGrowth)` → inside growth for position range

### Unit Tests for User Story 2

- [ ] T037 [US2] Write unit tests in `test/theta-swap-insurance/unit/UnderwriterPosition.t.sol`: test add liquidity (collateral computed correctly, ticks updated), test remove liquidity (net return computed correctly), test premium accrual proportional to liquidity share, test tick crossing updates activeLiquidity correctly
- [ ] T038 [US2] Write unit tests in `test/theta-swap-insurance/unit/FundingRate.t.sol`: test funding rate computation at various mark-index divergences, test bounds (never exceeds feeMax), test convergence direction, test edge cases (pIndex = 0, pIndex = MAX)

**Checkpoint**: Full two-sided insurance market functional. PLPs stream premiums, underwriters earn them. Funding rate drives mark-to-index convergence.

---

## Phase 6: User Story 4 — Query Insurance State (Priority: P3)

**Goal**: Observers can query all insurance state: prices, rates, positions, pool metrics

**Independent Test**: After operations from US1/US2/US3, call all view functions and verify returned values match expected state.

### Implementation for User Story 4

- [ ] T039 [P] [US4] Implement `getInsuranceState()` view in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: return (currentTick, activeLiquidity, virtualReserveX, virtualReserveY)
- [ ] T040 [P] [US4] Implement `getMarkPrice()` view in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: compute `p_mark = (1-x)/x` from current virtualReserveX using `SpotPriceMod`
- [ ] T041 [P] [US4] Implement `getIndexPrice()` view in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: call `OracleReaderMod` to read FCI `getIndex()`, compute `p_index = B_T / (1 - B_T)` using `IndexPriceMod`
- [ ] T042 [P] [US4] Implement `getPremiumRate()` view in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: compute current funding rate using `FundingRateMod`, return (fundingRate, effectiveFee)
- [ ] T043 [P] [US4] Implement `getProtectionValue()` view in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: look up PLPProtectionPosition, return (margin, protectionValue, premiumPaid, isActive)
- [ ] T044 [P] [US4] Implement `getUnderwriterPosition()` view in `src/theta-swap-insurance/ThetaSwapInsurance.sol`: look up UnderwriterPosition, compute earned premiums/payouts since baseline, return (tickLower, tickUpper, liquidity, premiumsEarned, protectionPayouts)

### Unit Tests for User Story 4

- [ ] T045 [US4] Write unit tests in `test/theta-swap-insurance/unit/ViewFunctions.t.sol`: test all view functions return correct values after initialization, after PLP registration, after underwriter deposit, after swaps

**Checkpoint**: All external interface functions implemented and testable.

---

## Phase 7: MasterHook Integration (Composite Facets)

**Purpose**: Wire FCI and Insurance facets together via composite facets in the MasterHook diamond

- [ ] T046 [P] Create `src/master-hook/CompositeAfterSwap.sol`: composite facet that calls FCI `_afterSwap` (updates B_T) then Insurance `_insuranceAfterSwap` (accrues premiums, updates CFMM) in sequence via internal delegatecall
- [ ] T047 [P] Create `src/master-hook/CompositeAfterAddLiq.sol`: composite facet that calls FCI `_afterAddLiquidity` (register position, snapshot baseline) then Insurance `_insuranceAfterAddLiquidity` in sequence
- [ ] T048 [P] Create `src/master-hook/CompositeAfterRemoveLiq.sol`: composite facet that calls FCI `_afterRemoveLiquidity` (deregister, accumulate HHI) then Insurance `_insuranceAfterRemoveLiquidity` (auto-close PLP) in sequence
- [ ] T049 Write integration test in `test/master-hook/integration/MasterHookIntegration.t.sol`: deploy MasterHook with both facets wired via composite selectors, add V4 liquidity (triggers composite afterAddLiquidity), swap (triggers composite afterSwap — FCI updates B_T, Insurance accrues premiums), verify both facets' state updated in same tx

**Checkpoint**: End-to-end system working through MasterHook diamond dispatch.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Fuzz testing, formal verification, static analysis, edge cases

### Fuzz Tests

- [ ] T050 [P] Write fuzz tests in `test/theta-swap-insurance/fuzz/InsuranceInvariants.fuzz.t.sol`: INS-001 (premium conservation), INS-002 (auto-close threshold), INS-003 (self-sizing hedge), INS-009 (collateral solvency) — 10,000+ runs
- [ ] T051 [P] Write fuzz tests in `test/theta-swap-insurance/fuzz/PiecewiseTick.fuzz.t.sol`: INS-004 (piecewise error bound), fuzz across all tick values and tick spacings
- [ ] T052 [P] Write fuzz tests in `test/theta-swap-insurance/fuzz/TickCrossing.fuzz.t.sol`: INS-005 (tick crossing liquidity), fuzz multi-tick swaps

### Kontrol Proofs for Invariants

- [ ] T053 [P] Create `test/theta-swap-insurance/kontrol/OracleConsistency.k.sol`: prove INS-006 (p_index = B_T / (1 - B_T) from FCI facet)
- [ ] T054 [P] Create `test/theta-swap-insurance/kontrol/FundingBounds.k.sol`: prove INS-007 (|fee_funding| <= fee_max - fee_base)
- [ ] T055 [P] Create `test/theta-swap-insurance/kontrol/ProtectionMonotonicity.k.sol`: prove INS-008 (A_T increases => protection value increases)

### Static Analysis & Edge Cases

- [ ] T056 Run Slither on `src/theta-swap-insurance/` and `src/master-hook/`: fix all high/medium findings
- [ ] T057 Write edge case tests in `test/theta-swap-insurance/unit/EdgeCases.t.sol`: B_T = 0 (full concentration), B_T → 1 (no concentration), zero underwriter liquidity → revert, oracle failure → revert, fee stream cessation → auto-close, x → 0 (max tick bound)

### Final Verification

- [ ] T058 Run full test suite: `forge test` — all unit, fuzz, and integration tests pass
- [ ] T059 Run Kontrol proofs: `kontrol build && kontrol prove` — all formal proofs pass
- [ ] T060 Verify all 10 insurance invariants (INS-001 through INS-010) are covered by at least one test or proof

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US3 Initialize (Phase 3)**: Depends on Phase 2 — BLOCKS US1 and US2 (pool must exist)
- **US1 PLP Protection (Phase 4)**: Depends on Phase 3 — can run in parallel with US2
- **US2 Underwriter Backing (Phase 5)**: Depends on Phase 3 — can run in parallel with US1
- **US4 Query State (Phase 6)**: Depends on Phase 4 + Phase 5 (needs both sides of market)
- **MasterHook Integration (Phase 7)**: Depends on Phase 4 + Phase 5 (needs both facets)
- **Polish (Phase 8)**: Depends on all previous phases

### User Story Dependencies

- **US3 (Initialize)**: Foundation only. No cross-story dependency.
- **US1 (PLP)**: Requires US3. Independent of US2 for basic premium streaming (underwriter liquidity can be seeded in test setup).
- **US2 (Underwriter)**: Requires US3. Independent of US1 for basic collateral management (PLP premium can be seeded in test setup).
- **US4 (Query)**: Requires US1 + US2 for meaningful state to query.

### Within Each User Story (TDD Order)

1. Types (UDVTs + Mod files) — FIRST
2. Kontrol proofs for types — verify type safety
3. Implementation (external functions using types)
4. Unit tests — verify behavior
5. Story checkpoint — independently testable

### Parallel Opportunities

**Phase 2 (Foundational)**: T008, T009, T010, T011, T012 can all run in parallel (different type files). T013-T016 can run in parallel (different proof files).

**Phase 4 + 5 (US1 + US2)**: After US3 completes, US1 and US2 can proceed in parallel since they touch different type files and different function implementations.

**Phase 6 (US4)**: All view functions (T039-T044) can run in parallel.

**Phase 7**: All composite facets (T046-T048) can run in parallel.

**Phase 8**: All fuzz tests (T050-T052) and Kontrol proofs (T053-T055) can run in parallel.

---

## Parallel Example: Phase 2 Foundational Types

```bash
# Launch all foundational types in parallel:
Task T008: "Create CollateralMod.sol"
Task T009: "Create PiecewiseTickMod.sol"
Task T010: "Create InsuranceTickBitmapMod.sol"
Task T011: "Create IndexPriceMod.sol"
Task T012: "Create SpotPriceMod.sol"

# Then launch all Kontrol proofs in parallel:
Task T013: "Kontrol proof for CollateralMod"
Task T014: "Kontrol proof for PiecewiseTickMod"
Task T015: "Kontrol proof for IndexPriceMod"
Task T016: "Kontrol proof for SpotPriceMod"
```

## Parallel Example: US1 + US2 After US3

```bash
# After US3 (Initialize) completes, launch both stories:

# US1 types:
Task T019: "Create InsurancePositionMod.sol"
Task T020: "Create PremiumRateMod.sol"

# US2 types (in parallel with US1):
Task T029: "Create UnderwriterPositionMod.sol"
Task T030: "Create FundingRateMod.sol"
```

---

## Implementation Strategy

### MVP First (US3 + US1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (FCI refactor + shared types)
3. Complete Phase 3: US3 (Initialize pool)
4. Complete Phase 4: US1 (PLP protection)
5. **STOP and VALIDATE**: PLP can register, stream premium, auto-close
6. This is the minimum viable insurance product (one-sided)

### Incremental Delivery

1. Setup + Foundational → Diamond storage, FCI facet, shared types ready
2. Add US3 (Initialize) → Pool can be created
3. Add US1 (PLP Protection) → PLPs can buy insurance (MVP!)
4. Add US2 (Underwriter) → Two-sided market complete
5. Add US4 (Query) → Full observability
6. Add MasterHook Integration → Production-ready diamond dispatch
7. Polish → Fuzz, Kontrol, Slither, edge cases

### Suggested MVP Scope

**US3 + US1 only**. A PLP can register for insurance against fee concentration, with premium streaming from their V4 fees. Underwriter liquidity is seeded by the deployer for testing. This validates the core economic mechanism before building the full two-sided market.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- TDD order within each story: Types → Kontrol → Implementation → Unit tests
- SCOP: all free functions in Mod files, no library/modifier/inheritance
- Diamond storage: each entity group uses disjoint keccak256 slot
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
