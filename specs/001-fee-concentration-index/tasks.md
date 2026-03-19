# Tasks: Fee Concentration Index (v3 — Current State Audit)

**Branch**: `001-fee-concentration-index`
**Last audit**: 2026-03-06
**Status**: Implementation largely complete, tests/verification incomplete

---

## Summary of What Exists

### Source files (all compile)
- `src/fee-concentration-index/FeeConcentrationIndex.sol` — diamond HookFacet, hookData dual-path
- `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol` — diamond storage + free functions
- `src/fee-concentration-index/types/` — FeeConcentrationStateMod, FeeShareRatioMod, SwapCountMod, BlockCountMod, TickRangeMod, TickRangeRegistryMod, FeeGrowthReaderMod
- `src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol`
- `src/libraries/HookUtilsMod.sol` — derivePoolAndPosition, sortTicks

### Test files (38/39 pass)
- `test/fee-concentration-index/unit/AfterAddLiquidity.t.sol` — 11 tests (INV-002, INV-004)
- `test/fee-concentration-index/unit/AfterSwap.t.sol` — 8 tests (INV-001, INV-003) + 2 fuzz
- `test/fee-concentration-index/unit/AfterRemoveLiquidity.t.sol` — 6 tests (deregister, JIT, getIndex)
- `test/fee-concentration-index/fuzz/FeeConcentrationIndexFull.fuzz.t.sol` — 4 tier tests (1 FAILING: tolerance)
- `test/fee-concentration-index/recon/` — Chimera fuzz (2 tests pass)
- `test/fee-concentration-index/kontrol/SwapCount.k.sol` — 2 proofs (INV-001, INV-002)
- `test/fee-concentration-index/kontrol/FeeShareRatio.k.sol` — 3 proofs (INV-006, INV-007, SC-006)

### Harness
- `test/fee-concentration-index/harness/FeeConcentrationIndexHarness.sol` — inherits FCI, exposes storage views
- `test/fee-concentration-index/harness/MockPositionManager.sol`

---

## Remaining Work

### Phase A: Fix Failing Test (P0)

- [ ] A01 Fix `testFuzz_tier1_equalCapitalEqualTime` precision tolerance — delta 362 > max 320. Likely needs wider tolerance or rounding fix in `toIndexA`.

---

### Phase B: Missing Kontrol Proofs (P1)

FeeConcentrationState proofs — `test/fee-concentration-index/kontrol/FeeConcentrationState.k.sol` (new file):

- [ ] B01 `prove_fci_indexBoundedness` — FCI-001: 0 <= toIndexA(state) <= Q128
- [ ] B02 `prove_fci_thetaSumNonNeg` — FCI-002: addTerm only increases thetaSum
- [ ] B03 `prove_fci_posCountNonNeg` — FCI-003: decrementPos requires posCount > 0
- [ ] B04 `prove_fci_deviationNonNeg` — FCI-005: deltaPlus(state) >= 0
- [ ] B05 `prove_fci_deviationUpperBound` — FCI-006: deltaPlus(state) < Q128
- [ ] B06 `prove_fci_coPrimaryConsistency` — FCI-007: same state, same deltaPlus
- [ ] B07 `prove_fci_priceNonNeg` — FCI-009: toDeltaPlusPrice(state) >= 0
- [ ] B08 `prove_fci_priceMonotonicity` — FCI-010: higher deltaPlus, higher price
- [ ] B09 `prove_fci_priceInvertibility` — FCI-011: round-trip identity

TickRangeRegistry proofs — `test/fee-concentration-index/kontrol/TickRangeRegistry.k.sol` (new file):

- [ ] B10 `prove_register_adds_position` — INV-004
- [ ] B11 `prove_deregister_removes_position` — INV-004
- [ ] B12 `prove_deregister_last_deletes_range` — INV-005

Index update proof — `test/fee-concentration-index/kontrol/IndexUpdate.k.sol` (new file):

- [ ] B13 `prove_accumulatedSum_monotonic` — INV-008
- [ ] B14 `prove_indexA_capped_at_one` — INV-009
- [ ] B15 `prove_zero_lifetime_skipped` — INV-010

---

### Phase C: Missing Fuzz Tests (P1)

- [ ] C01 `testFuzz_feeShareRatio_bounds` in `test/fee-concentration-index/fuzz/FeeShareRatio.t.sol` — full uint256 range (Kontrol proof covers uint128 only)
- [ ] C02 `testFuzz_feeShareRatio_square_precision` — verify square() result <= Q128
- [ ] C03 `testFuzz_jit_position_max_concentration` in `test/fee-concentration-index/fuzz/IndexUpdate.t.sol` — JIT: lifetime=1, x_k=1 produces A_T == 1 (SC-001)
- [ ] C04 `testFuzz_index_monotonic` — A_T never decreases (INV-008)
- [ ] C05 `testFuzz_index_formula_matches_spec` — N equal positions match SC-002 formula

---

### Phase D: Co-Primary State Tests (P1)

- [ ] D01 `test_atNull_zero_when_no_positions` in `test/fee-concentration-index/unit/FeeConcentrationState.t.sol` — posCount=0, atNull=0
- [ ] D02 `test_deltaPlus_equals_AT_when_no_active_positions` — N=0, Theta=0, A_T>0, Delta+=A_T
- [ ] D03 `test_deltaPlus_zero_symmetric_pool` — A_T=0.5, Theta=Q128, N=2, atNull=0.5, Delta+=0
- [ ] D04 `testFuzz_fci_nullLowerBound` — FCI-004: A_T >= atNull when posCount > 0

---

### Phase E: Static Analysis (P2)

- [ ] E01 Run Slither on `src/fee-concentration-index/` — zero high/medium findings
- [ ] E02 Run Semgrep smart contract rules — zero findings

---

### Phase F: Gas Benchmarks + Polish (P2)

- [ ] F01 Gas benchmark: afterSwap with 10 positions < 50k gas (SC-004)
- [ ] F02 Gas benchmark: afterRemoveLiquidity < 100k gas (SC-005)
- [ ] F03 Verify all 21 invariants covered by at least one Kontrol proof or fuzz test
- [ ] F04 Final `forge test` — all tests pass
- [ ] F05 Final `kontrol prove` — all proofs pass

---

## Invariant Coverage Matrix

| ID | Description | Kontrol | Fuzz | Unit |
|----|-------------|---------|------|------|
| INV-001 | SwapCount monotonic | SwapCount.k.sol | AfterSwap.t.sol | AfterSwap.t.sol |
| INV-002 | SwapCount initial zero | SwapCount.k.sol | — | AfterAddLiquidity.t.sol |
| INV-003 | Only overlapping range incremented | — | AfterSwap.t.sol | AfterSwap.t.sol |
| INV-004 | Registry consistency | **B10, B11** | Chimera | AfterAddLiquidity.t.sol |
| INV-005 | Deregister last deletes range | **B12** | — | AfterRemoveLiquidity.t.sol |
| INV-006 | FeeShareRatio bounds | FeeShareRatio.k.sol | **C01** | — |
| INV-007 | Fee share zero when no fees | FeeShareRatio.k.sol | — | — |
| INV-008 | AccumulatedSum monotonic | **B13** | **C04** | — |
| INV-009 | IndexA capped at one | **B14** | — | — |
| INV-010 | Zero lifetime skipped | **B15** | — | AfterRemoveLiquidity.t.sol |
| FCI-001 | Index boundedness | **B01** | — | — |
| FCI-002 | ThetaSum non-negative | **B02** | — | — |
| FCI-003 | PosCount non-negative | **B03** | — | — |
| FCI-004 | Null lower bound | — | **D04** | — |
| FCI-005 | Deviation non-negative | **B04** | — | — |
| FCI-006 | Deviation upper bound | **B05** | — | — |
| FCI-007 | Co-primary consistency | **B06** | — | — |
| FCI-009 | Price non-negative | **B07** | — | — |
| FCI-010 | Price monotonicity | **B08** | — | — |
| FCI-011 | Price invertibility | **B09** | — | — |

**Bold** = not yet implemented. All others exist and pass.

---

## Execution Order

```
A01 (fix failing test)
  |
  v
B01..B15 (Kontrol proofs — one at a time)
  |
  v
C01..C05 + D01..D04 (fuzz + unit tests — can parallel)
  |
  v
E01..E02 (static analysis)
  |
  v
F01..F05 (gas + final verification)
```

**Estimated remaining**: 28 tasks (1 fix + 15 proofs + 9 tests + 2 static analysis + 5 polish)
