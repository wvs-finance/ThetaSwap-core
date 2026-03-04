# Tasks: Fee Concentration Index

**Input**: Design documents from `specs/001-fee-concentration-index/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/
**Tests**: Included — TDD skill requires Kontrol proofs and fuzz tests before implementation.
**Organization**: Tasks grouped by user story with TDD ordering (types → invariants → proofs → implementation → fuzz).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and invariants document per TDD skill.

- [ ] T001 Create directory structure: `src/fee-concentration-index/types/`, `test/fee-concentration-index/kontrol/`, `test/fee-concentration-index/fuzz/`
- [ ] T002 Write system invariants in `specs/001-fee-concentration-index/invariants.md` (~10 invariants in Hoare triple format per TDD Phase 2)

**Checkpoint**: Directory structure exists, invariants defined. Ready for type design.

---

## Phase 2: Foundational — Type Definitions (Blocking Prerequisites)

**Purpose**: Define all UDVTs and Mod files per TDD Phase 3. Types MUST compile. No business logic.

**CRITICAL**: No user story implementation can begin until all types are defined and reviewed.

- [ ] T003 [P] Define SwapCount UDVT in `src/fee-concentration-index/types/SwapCount.sol` — `type SwapCount is uint256;`
- [ ] T004 [P] Define SwapCountMod with free functions in `src/fee-concentration-index/types/SwapCountMod.sol` — increment, unwrap, isZero, fromUint256
- [ ] T005 [P] Define FeeShareRatio UDVT in `src/fee-concentration-index/types/FeeShareRatio.sol` — `type FeeShareRatio is uint256;`
- [ ] T006 [P] Define FeeShareRatioMod with free functions in `src/fee-concentration-index/types/FeeShareRatioMod.sol` — fromFeeGrowth (Q128 division), square (mulDiv), unwrap
- [ ] T007 [P] Define AccumulatedHHI UDVT in `src/fee-concentration-index/types/AccumulatedHHI.sol` — `type AccumulatedHHI is uint256;`
- [ ] T008 [P] Define AccumulatedHHIMod with free functions in `src/fee-concentration-index/types/AccumulatedHHIMod.sol` — addTerm, toIndexA (sqrt), toIndexB (complement), unwrap
- [ ] T009 Verify all types compile with `forge build` — no business logic, only type definitions and arithmetic helpers

**Checkpoint**: All UDVTs compile. User review gate per TDD skill. Ready for proofs and implementation.

---

## Phase 3: User Story 1 — Track Position Lifetimes (Priority: P1) MVP

**Goal**: Track per-position swap counts that increment only when swaps use that position's liquidity. Positions grouped by tick range for O(1) lookup.

**Independent Test**: Deploy hook, add position covering active tick, execute N swaps through range, remove position, verify lifetime == N.

### Kontrol Proofs for US1

- [ ] T010 [US1] Write Kontrol proof `prove_swapCount_increment_monotonic` in `test/fee-concentration-index/kontrol/SwapCount.k.sol` — SwapCount only increases
- [ ] T011 [US1] Write Kontrol proof `prove_swapCount_initial_zero` in `test/fee-concentration-index/kontrol/SwapCount.k.sol` — SwapCount starts at 0
- [ ] T012 [US1] Write Kontrol proof `prove_register_adds_position` in `test/fee-concentration-index/kontrol/TickRangeRegistry.k.sol` — registration adds position to correct range
- [ ] T013 [US1] Write Kontrol proof `prove_deregister_removes_position` in `test/fee-concentration-index/kontrol/TickRangeRegistry.k.sol` — deregistration removes position cleanly
- [ ] T014 [US1] Write Kontrol proof `prove_deregister_last_deletes_range` in `test/fee-concentration-index/kontrol/TickRangeRegistry.k.sol` — removing last position deletes range entry

### Implementation for US1

- [ ] T015 [US1] Implement TickRangeRegistryMod free functions in `src/fee-concentration-index/TickRangeRegistryMod.sol` — register, deregister, getPositionsInRange, computeRangeKey
- [ ] T016 [US1] Implement PositionLifetimeMod free functions in `src/fee-concentration-index/PositionLifetimeMod.sol` — initPosition, incrementSwapCount, readLifetime, cleanupPosition
- [ ] T017 [US1] Implement afterAddLiquidity logic: derive positionKey, initialize SwapCount to 0, register in TickRangePositionSet
- [ ] T018 [US1] Implement afterSwap tick-range walking logic: read tick bitmap via StateLibrary.getTickBitmap(), identify overlapping ranges, increment SwapCount for all positions in range

### Fuzz Tests for US1

- [ ] T019 [P] [US1] Write fuzz test `testFuzz_swapCount_monotonic` in `test/fee-concentration-index/fuzz/PositionLifetime.t.sol`
- [ ] T020 [P] [US1] Write fuzz test `testFuzz_register_deregister_roundtrip` in `test/fee-concentration-index/fuzz/TickRangeRegistry.t.sol`
- [ ] T021 [P] [US1] Write fuzz test `testFuzz_only_active_range_incremented` in `test/fee-concentration-index/fuzz/TickRangeRegistry.t.sol` — positions outside swap range not incremented

**Checkpoint**: Position lifetime tracking works end-to-end. Kontrol proofs pass. Fuzz tests pass.

---

## Phase 4: User Story 2 — Compute Fee Share Ratio (Priority: P1)

**Goal**: Compute x_k = feeGrowthInside / feeGrowthGlobal as Q128 value in [0, 1] at position removal.

**Independent Test**: Deploy hook, add single position covering active tick, execute swaps generating fees, remove position, verify x_k == 1 (sole LP captures all fees).

### Kontrol Proofs for US2

- [ ] T022 [US2] Write Kontrol proof `prove_feeShareRatio_bounds` in `test/fee-concentration-index/kontrol/FeeShareRatio.k.sol` — x_k always in [0, 2^128]
- [ ] T023 [US2] Write Kontrol proof `prove_feeShareRatio_zero_when_no_global_fees` in `test/fee-concentration-index/kontrol/FeeShareRatio.k.sol` — x_k == 0 when feeGrowthGlobal == 0
- [ ] T024 [US2] Write Kontrol proof `prove_feeShareRatio_square_no_overflow` in `test/fee-concentration-index/kontrol/FeeShareRatio.k.sol` — x_k^2 via mulDiv does not overflow

### Implementation for US2

- [ ] T025 [US2] Implement FeeConcentrationIndexMod.computeFeeShare in `src/fee-concentration-index/FeeConcentrationIndexMod.sol` — read StateLibrary.getFeeGrowthInside + getFeeGrowthGlobal, compute Q128 ratio
- [ ] T026 [US2] Handle edge case: feeGrowthGlobal == 0 returns FeeShareRatio(0) per FR-011

### Fuzz Tests for US2

- [ ] T027 [P] [US2] Write fuzz test `testFuzz_feeShareRatio_bounds` in `test/fee-concentration-index/fuzz/FeeShareRatio.t.sol` — x_k always <= 2^128
- [ ] T028 [P] [US2] Write fuzz test `testFuzz_feeShareRatio_square_precision` in `test/fee-concentration-index/fuzz/FeeShareRatio.t.sol` — squaring preserves Q128 format

**Checkpoint**: Fee share ratio computation works with Q128 precision. No overflow on squaring.

---

## Phase 5: User Story 3 — Update Fee Concentration Index (Priority: P2)

**Goal**: On position removal, compute theta_k = 1/lifetime, update accumulatedSum += theta_k * x_k^2, expose A_T = sqrt(accumulatedSum) and B_T = 1 - A_T via view function.

**Independent Test**: Deploy hook, add JIT position (lifetime=1, x_k=1), remove it, verify A_T == 1.

**Depends on**: US1 (lifetime) and US2 (fee share ratio) must be complete.

### Kontrol Proofs for US3

- [ ] T029 [US3] Write Kontrol proof `prove_accumulatedHHI_monotonic` in `test/fee-concentration-index/kontrol/AccumulatedHHI.k.sol` — accumulatedSum only increases
- [ ] T030 [US3] Write Kontrol proof `prove_indexA_capped_at_one` in `test/fee-concentration-index/kontrol/AccumulatedHHI.k.sol` — A_T <= 2^128 (capped at 1)
- [ ] T031 [US3] Write Kontrol proof `prove_indexB_complement` in `test/fee-concentration-index/kontrol/AccumulatedHHI.k.sol` — B_T == 2^128 - A_T
- [ ] T032 [US3] Write Kontrol proof `prove_theta_times_xsquared_no_overflow` in `test/fee-concentration-index/kontrol/IndexUpdate.k.sol` — mulDiv chain for theta_k * x_k^2 does not overflow
- [ ] T033 [US3] Write Kontrol proof `prove_zero_lifetime_skipped` in `test/fee-concentration-index/kontrol/IndexUpdate.k.sol` — lifetime == 0 does not update index

### Implementation for US3

- [ ] T034 [US3] Implement FeeConcentrationIndexMod.computeTheta in `src/fee-concentration-index/FeeConcentrationIndexMod.sol` — Q128 division: (1 << 128) / lifetime
- [ ] T035 [US3] Implement FeeConcentrationIndexMod.updateIndex in `src/fee-concentration-index/FeeConcentrationIndexMod.sol` — compute term = mulDiv(theta_k, x_k^2, 2^128), add to accumulatedSum
- [ ] T036 [US3] Implement FeeConcentrationIndexMod.readIndex in `src/fee-concentration-index/FeeConcentrationIndexMod.sol` — sqrt(accumulatedSum << 128) for A_T, cap at 2^128, B_T = complement
- [ ] T037 [US3] Implement afterRemoveLiquidity logic: read lifetime, skip if 0, compute x_k, compute theta_k, update index, deregister position, cleanup swap count
- [ ] T038 [US3] Implement getIndex view function returning (A_T, B_T) as Q128 values per FR-007/FR-012

### Fuzz Tests for US3

- [ ] T039 [P] [US3] Write fuzz test `testFuzz_jit_position_max_concentration` in `test/fee-concentration-index/fuzz/IndexUpdate.t.sol` — JIT (lifetime=1, x_k=1) produces A_T == 1
- [ ] T040 [P] [US3] Write fuzz test `testFuzz_index_monotonic` in `test/fee-concentration-index/fuzz/IndexUpdate.t.sol` — A_T never decreases after any removal
- [ ] T041 [P] [US3] Write fuzz test `testFuzz_index_formula_matches_spec` in `test/fee-concentration-index/fuzz/IndexUpdate.t.sol` — for N equal positions, verify SC-002 formula

**Checkpoint**: Full index computation works. JIT position produces A_T = 1. Formula matches spec.

---

## Phase 6: User Story 4 — EVM Number Representation (Priority: P2)

**Goal**: Verify all fixed-point arithmetic is overflow-free and precision is adequate. Boundary value testing.

**Independent Test**: Compute x_k^2 for boundary values (0, 2^128), verify no overflow and precision within bounds.

**Depends on**: US2 (FeeShareRatio) and US3 (AccumulatedHHI) types must exist.

### Kontrol Proofs for US4

- [ ] T042 [US4] Write Kontrol proof `prove_q128_boundary_squaring` in `test/fee-concentration-index/kontrol/FeeShareRatio.k.sol` — x_k = 2^128 (representing 1.0) squares without overflow
- [ ] T043 [US4] Write Kontrol proof `prove_q128_division_precision` in `test/fee-concentration-index/kontrol/FeeShareRatio.k.sol` — feeGrowthInside / feeGrowthGlobal preserves >= 64 bits precision
- [ ] T044 [US4] Write Kontrol proof `prove_sqrt_q128_precision` in `test/fee-concentration-index/kontrol/AccumulatedHHI.k.sol` — sqrt(Q256) produces correct Q128 result

### Fuzz Tests for US4

- [ ] T045 [P] [US4] Write fuzz test `testFuzz_q128_squaring_boundary` in `test/fee-concentration-index/fuzz/FeeShareRatio.t.sol` — boundary values (0, 1, 2^64, 2^128-1, 2^128)
- [ ] T046 [P] [US4] Write fuzz test `testFuzz_accumulated_sum_no_overflow` in `test/fee-concentration-index/fuzz/IndexUpdate.t.sol` — accumulated sum over many terms stays in Q128

**Checkpoint**: All Q128 arithmetic verified overflow-free. SC-006 satisfied.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration, gas optimization, static analysis per TDD Phase 5 and 7.

- [ ] T047 Run Slither static analysis on `src/fee-concentration-index/` — zero findings required per TDD Phase 5
- [ ] T048 Run Semgrep smart contract rules on `src/fee-concentration-index/` — zero findings required per TDD Phase 5
- [ ] T049 Gas benchmark: afterSwap with 10 positions < 50k gas per SC-004
- [ ] T050 Gas benchmark: afterRemoveLiquidity < 100k gas per SC-005
- [ ] T051 Verify all invariants from `specs/001-fee-concentration-index/invariants.md` are covered by at least one Kontrol proof or fuzz test
- [ ] T052 Final `forge test` — all fuzz tests pass
- [ ] T053 Final `kontrol prove` — all formal proofs pass

**Checkpoint**: All tests pass, static analysis clean, gas budgets met, invariant coverage complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Types)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — SwapCount and TickRangeRegistry types
- **Phase 4 (US2)**: Depends on Phase 2 — FeeShareRatio type
- **Phase 5 (US3)**: Depends on Phase 3 (US1) AND Phase 4 (US2) — needs lifetime + fee share
- **Phase 6 (US4)**: Depends on Phase 4 (US2) and Phase 5 (US3) — boundary testing of existing types
- **Phase 7 (Polish)**: Depends on all user stories complete

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Types)
                      ├── Phase 3 (US1: Lifetimes) ──┐
                      └── Phase 4 (US2: Fee Share) ───┼── Phase 5 (US3: Index) → Phase 6 (US4: Arithmetic) → Phase 7 (Polish)
```

- **US1 and US2 can run in parallel** after Phase 2
- **US3 depends on both US1 and US2**
- **US4 depends on US3**

### Within Each User Story (TDD Order)

1. Kontrol proofs written ONE AT A TIME (build → prove → review → next)
2. Implementation after proofs scaffold exists
3. Fuzz tests after implementation
4. User review gate after each file

### Parallel Opportunities

- T003-T008: All type definitions can be written in parallel (different files)
- T010-T014: Kontrol proofs for US1 written sequentially (TDD rule)
- T019-T021: US1 fuzz tests can run in parallel
- Phase 3 (US1) and Phase 4 (US2) can run in parallel
- T039-T041: US3 fuzz tests can run in parallel
- T045-T046: US4 fuzz tests can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup + invariants
2. Complete Phase 2: All type definitions (foundational)
3. Complete Phase 3: US1 — position lifetime tracking (P1)
4. Complete Phase 4: US2 — fee share ratio computation (P1)
5. **STOP and VALIDATE**: Both P1 stories independently testable

### Incremental Delivery

1. Setup + Types → Foundation ready
2. Add US1 (lifetimes) → Test: N swaps → lifetime == N
3. Add US2 (fee share) → Test: sole LP → x_k == 1
4. Add US3 (index) → Test: JIT → A_T == 1
5. Add US4 (arithmetic) → Test: boundary values, no overflow
6. Polish → Gas, static analysis, coverage

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Kontrol proofs are ONE AT A TIME per TDD skill — no batching
- Each file gets user review before moving to next file
- SCOP: No `is`, no `library`, no `modifier` in production code
- Commit after each task or logical group
