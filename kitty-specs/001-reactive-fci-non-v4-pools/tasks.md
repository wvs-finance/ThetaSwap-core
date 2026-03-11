# Tasks: Reactive FCI for Non-V4 Pools

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Generated**: 2026-03-06

## Subtask Index

| ID | Description | WP | Parallel |
|----|-------------|-----|----------|
| T001 | Create ReactiveHookAdapterStorageMod.sol — diamond storage | WP01 | |
| T002 | Add CollectedFees struct and COLLECT_FEE_STORAGE_SLOT | WP01 | |
| T003 | Create storage accessor free functions | WP01 | |
| T004 | Create ReactiveHookAdapter.sol — contract shell, constructor, auth state | WP02 | |
| T005 | Implement setAuthorized(address, bool) — owner-only whitelist | WP02 | |
| T006 | Implement onV3Swap(V3SwapData) | WP02 | |
| T007 | Implement onV3Mint(V3MintData) | WP02 | |
| T008 | Implement onV3Collect(V3CollectData) | WP02 | |
| T009 | Implement onV3Burn(V3BurnData) — fee share + HHI accumulation | WP02 | |
| T010 | Implement getIndex(PoolKey) — read own AccumulatedHHI | WP02 | |
| T011 | Fuzz test: adapter rejects unauthorized callers (RX-005) | WP03 | [P] |
| T012 | Fuzz test: swap translation equivalence (RX-006) | WP03 | [P] |
| T013 | Fuzz test: mint translation equivalence (RX-007) | WP03 | [P] |
| T014 | Fuzz test: unregistered burn no-op (RX-009) | WP03 | [P] |
| T015 | Fuzz test: collect fee accumulation correctness | WP03 | [P] |
| T016 | Static analysis: Slither on src/reactive-integration/ | WP04 | |
| T017 | Static analysis: Semgrep on src/reactive-integration/ | WP04 | [P] with T016 |
| T018 | Kontrol prove: SyntheticFeeGrowth.k.sol + PoolKeyExt.k.sol | WP04 | |
| T019 | Forge test: run all fuzz tests, verify pass | WP04 | |

## Work Packages

---

### WP01: Adapter Diamond Storage

**Priority**: P1 (foundation)
**Goal**: Create the parallel FCI storage module for the ReactiveHookAdapter
**Dependencies**: None
**Subtasks**: T001, T002, T003
**Requirement Refs**: FR-007
**Estimated prompt size**: ~250 lines
**Prompt file**: [tasks/WP01-adapter-diamond-storage.md](tasks/WP01-adapter-diamond-storage.md)

**Implementation sketch**:
1. Create `ReactiveHookAdapterStorageMod.sol` with REACTIVE_FCI_STORAGE_SLOT
2. Add CollectedFees struct and COLLECT_FEE_STORAGE_SLOT
3. Write accessor free functions following existing FCI storage pattern

**Success criteria**:
- [ ] Storage struct compiles with `forge build`
- [ ] Storage slot hashes are distinct from FCI_STORAGE_SLOT
- [ ] All accessor functions are free functions (SCOP)

---

### WP02: ReactiveHookAdapter Contract

**Priority**: P1 (core implementation)
**Goal**: Implement the adapter contract with 4 typed callbacks, auth, and index query
**Dependencies**: WP01
**Subtasks**: T004, T005, T006, T007, T008, T009, T010
**Requirement Refs**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-008, FR-009, FR-010, FR-011, FR-012, FR-016
**Estimated prompt size**: ~500 lines
**Prompt file**: [tasks/WP02-reactive-hook-adapter.md](tasks/WP02-reactive-hook-adapter.md)

**Implementation sketch**:
1. Create contract shell with constructor (owner, factory)
2. Add whitelist auth (setAuthorized, inline checks)
3. Implement onV3Swap — PoolKey construction + incrementOverlappingRanges
4. Implement onV3Mint — position registration
5. Implement onV3Collect — fee accumulation
6. Implement onV3Burn — fee share computation + HHI accumulation + cleanup
7. Implement getIndex — read own AccumulatedHHI

**Success criteria**:
- [ ] All 4 callbacks compile and are `external`
- [ ] Auth reverts on unauthorized sender
- [ ] Burn with accumulated Collect fees computes correct fee share
- [ ] getIndex returns (indexA, indexB) from own storage
- [ ] No `library`, `modifier`, or `is` (except if needed for interface)

---

### WP03: Fuzz Tests

**Priority**: P1 (verification)
**Goal**: Write fuzz tests covering system-level invariants RX-005, RX-006, RX-007, RX-009
**Dependencies**: WP02
**Subtasks**: T011, T012, T013, T014, T015
**Requirement Refs**: FR-004, FR-005, FR-006, FR-008, FR-009
**Estimated prompt size**: ~400 lines
**Prompt file**: [tasks/WP03-fuzz-tests.md](tasks/WP03-fuzz-tests.md)
**Parallel opportunities**: All 5 tests are independent — can be written in parallel

**Implementation sketch**:
1. Create test harness with MockV3Pool + deployed adapter
2. Write auth rejection test (random sender → revert)
3. Write swap equivalence test (compare swap counts)
4. Write mint equivalence test (compare position state)
5. Write unregistered burn test (state unchanged)
6. Write collect accumulation test (fees sum correctly)

**Success criteria**:
- [ ] All 5 fuzz tests compile
- [ ] `forge test --match-contract` passes for each

---

### WP04: Static Analysis + Verification

**Priority**: P1 (gate)
**Goal**: Run Slither, Semgrep, Kontrol, and forge test — fix all findings
**Dependencies**: WP03
**Subtasks**: T016, T017, T018, T019
**Requirement Refs**: FR-013, FR-014, FR-015
**Estimated prompt size**: ~300 lines
**Prompt file**: [tasks/WP04-static-analysis-verification.md](tasks/WP04-static-analysis-verification.md)

**Implementation sketch**:
1. Run Slither on src/reactive-integration/, fix findings
2. Run Semgrep with Decurity rules, fix findings
3. Run kontrol prove on 7 scaffolded proofs
4. Run forge test on all fuzz tests
5. Verify every invariant RX-001..RX-010 covered

**Success criteria**:
- [ ] Slither: zero high/medium findings
- [ ] Semgrep: zero findings
- [ ] Kontrol: all 7 proofs pass
- [ ] Forge: all fuzz tests pass
