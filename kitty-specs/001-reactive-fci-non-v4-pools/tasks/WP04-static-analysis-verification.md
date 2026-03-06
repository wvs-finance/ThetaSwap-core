---
work_package_id: "WP04"
title: "Static Analysis + Verification"
lane: "planned"
dependencies: ["WP03"]
subtasks: ["T016", "T017", "T018", "T019"]
requirement_refs: ["FR-013", "FR-014", "FR-015"]
history:
  - date: "2026-03-06"
    action: "created"
    by: "spec-kitty.tasks"
---

# WP04: Static Analysis + Verification

**Objective**: Run all verification gates — Slither, Semgrep, Kontrol formal proofs, and forge fuzz tests. Fix all findings. This is the final gate before the feature is complete.

**Implementation command**: `spec-kitty implement WP04 --base WP03`

## Context

The type-driven development process requires a clean static analysis gate. Kontrol proofs were scaffolded in Phase 4 (7 proofs across 2 files). Fuzz tests were written in WP03. This WP runs everything and fixes any issues.

**Proof files**:
- `test/reactive-integration/kontrol/SyntheticFeeGrowth.k.sol` — 3 proofs (RX-008)
- `test/reactive-integration/kontrol/PoolKeyExt.k.sol` — 4 proofs (RX-001..004)

**Invariant coverage matrix**:

| Invariant | Verification | File |
|-----------|-------------|------|
| RX-001 | Kontrol proof | PoolKeyExt.k.sol |
| RX-002 | Kontrol proof | PoolKeyExt.k.sol |
| RX-003 | Kontrol proof | PoolKeyExt.k.sol |
| RX-004 | Kontrol proof | PoolKeyExt.k.sol |
| RX-005 | Fuzz test | ReactiveHookAdapter.fuzz.t.sol |
| RX-006 | Fuzz test | ReactiveHookAdapter.fuzz.t.sol |
| RX-007 | Fuzz test | ReactiveHookAdapter.fuzz.t.sol |
| RX-008 | Kontrol proof | SyntheticFeeGrowth.k.sol |
| RX-009 | Fuzz test | ReactiveHookAdapter.fuzz.t.sol |
| RX-010 | Subscription layer | Out of scope (dedup in reactive contract) |

## Subtasks

### T016: Slither Analysis

**Purpose**: Run Slither on the reactive-integration source, fix all high/medium findings.

**Steps**:
1. Run: `slither src/reactive-integration/ --filter-paths "test/"`
2. Review all findings
3. Fix high and medium severity issues
4. Document any false positives with `// slither-disable-next-line` and rationale comment
5. Re-run to verify clean

**Common findings to expect**:
- Reentrancy warnings on external calls (likely false positive — adapter doesn't hold funds)
- Uninitialized storage (ensure all storage accessors initialize correctly)
- Low-level assembly in storage slot access (expected, document)

**Validation**:
- [ ] Zero high findings
- [ ] Zero medium findings
- [ ] All disabled findings have rationale comments

### T017: Semgrep Analysis

**Purpose**: Run Semgrep with DeFi-specific rules.

**Steps**:
1. Run: `semgrep --config https://github.com/Decurity/semgrep-smart-contracts --metrics=off src/reactive-integration/`
2. Review all findings
3. Fix genuine issues
4. Re-run to verify clean

**Validation**:
- [ ] Zero findings after fixes

### T018: Kontrol Formal Proofs

**Purpose**: Run all 7 Kontrol proofs and verify they pass.

**Steps**:
1. `kontrol build`
2. Run proofs one at a time:
   - `kontrol prove --match-test prove_syntheticFeeGrowth_zeroLiquidity`
   - `kontrol prove --match-test prove_syntheticFeeGrowth_feeShareBounds`
   - `kontrol prove --match-test prove_syntheticFeeGrowth_zeroRange`
   - `kontrol prove --match-test prove_poolKey_hooksField`
   - `kontrol prove --match-test prove_poolKey_deterministic`
   - `kontrol prove --match-test prove_poolKey_distinct`
   - `kontrol prove --match-test prove_poolKey_roundTrip`
3. If any proof fails: diagnose, fix the type code or proof, re-run
4. Document proof results

**Expected issues**:
- `prove_poolKey_distinct` may hit solver timeout for large input spaces — tighten `vm.assume` bounds if needed
- `prove_poolKey_roundTrip` depends on MockV3Factory — ensure mock behavior matches Kontrol's symbolic execution model

**Validation**:
- [ ] All 7 proofs pass
- [ ] No timeouts

### T019: Forge Fuzz Tests

**Purpose**: Run all fuzz tests and verify they pass.

**Steps**:
1. `forge test --match-contract ReactiveHookAdapterFuzz -vvv`
2. If any test fails: diagnose, fix implementation or test, re-run
3. Verify all 5 fuzz tests pass with default fuzz runs (256)
4. Run with extended fuzz runs for confidence: `forge test --match-contract ReactiveHookAdapterFuzz --fuzz-runs 10000`

**Validation**:
- [ ] All 5 fuzz tests pass at 256 runs
- [ ] All 5 fuzz tests pass at 10000 runs
- [ ] No spurious failures

## Definition of Done

- [ ] Slither: zero high/medium findings on src/reactive-integration/
- [ ] Semgrep: zero findings on src/reactive-integration/
- [ ] Kontrol: all 7 proofs pass
- [ ] Forge: all 5 fuzz tests pass at 10000 runs
- [ ] Every invariant RX-001..RX-009 covered by at least one proof or fuzz test
- [ ] RX-010 documented as out of scope (subscription layer responsibility)

## Risks

- **Kontrol timeout**: Some proofs may require narrower input bounds. Prepare fallback bounds that still cover the meaningful domain.
- **Slither false positives on assembly**: Storage slot access uses inline assembly — expected Slither warnings. Document with disable comments.
- **Fuzz test flakiness**: Ensure `vm.assume` constraints are tight enough to avoid invalid inputs but loose enough for coverage.
