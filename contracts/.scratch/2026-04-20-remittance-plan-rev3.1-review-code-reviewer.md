# Rev-3.1 Plan — Code Reviewer Second-Cycle Review

**Reviewer:** Code Reviewer (second cycle per Plan Rule 13)
**Subject:** Rev 3.1 at `d7dfc4390` of `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
**Prior cycle result:** BLOCK (2 BLOCK + 3 FLAG + 4 NIT)
**Date:** 2026-04-23

---

## 1. Executive verdict

**PASS.** Both Rev-3 BLOCKs are fully resolved; all three Rev-3 FLAGs are resolved; 3 of 4 NITs are APPLIED, 1 explicitly REJECTED by TW with acceptable rationale. No new BLOCK-severity findings were introduced by the Rev-3.1 additions (Phase 1.5 promotion, Rule 14, recovery protocols, decision gates). Per Rule 13 convergence directive, **ship it**.

---

## 2. Per-finding disposition audit (Rev-3 findings)

### CR-B1 — Stale Goal + stale Phase-1 tasks under daily-native pivot → **CLOSED**

All four sub-checks verified:
- **Goal (line 13):** Now reads "weekly rich-aggregation vector of daily on-chain COPM + cCOP remittance-channel flows"; BanRep quarterly explicitly demoted to validation row S14. Monthly primary explicitly superseded. PASS.
- **Task 9 (line 179):** Carries a "Rev 3.1 plan-body amendment rider (CR-B1)" block reframing `CleanedRemittancePanelV1` as vestigial-seam; Step 1 is explicitly amended. PASS.
- **Task 10 (line 195):** Rider at line 203 explicitly restricts AR(1) surprise pathway to validation row S14 (BanRep quarterly); Step 1 reflects the restriction. PASS.
- **Task 13 (line 401):** `a1r_monthly_rebase` renamed to `a1r_quarterly_rebase_bridge`; commit message updated to `A1-R-bridge`. PASS.
- **Downstream propagation:** Task 23 §7 (line 676) and Task 30a (line 819) both reference "A1-R-bridge" with explicit rename annotation. Spec-coverage self-check (lines 856-858) updated to reflect rows 6/7/8 handling under Rev-3.1. PASS.

### CR-B2 — Task 11.B silent-test-pass risk → **CLOSED**

Task 11.B Step 1 (line 292, continued at line 294) now contains an explicit "Independent reproduction witness (MANDATORY)" block specifying:
- The test file must NOT import `weekly_onchain_flow_vector`.
- Per-channel independent pandas one-liner formulas enumerated inline (`resample('W-FRI').sum()`, `resample('W-FRI').var(ddof=0)`, inline HHI reduction, etc.).
- Pinned values committed BEFORE Step 3 implementation.
- Explicit reference to "Task 10 `test_golden_fixture_matches_independent_fit` pattern" and the 5-instance CPI silent-test-pass catalogue.

Step 2 failure-mode clarified to require "function does not exist / returns wrong shape", not tolerance mismatch. This is a stronger-than-requested fix: the witness is inlined in the test file (Option a from my recommendation), and the Step-2 failure-mode redefinition closes a secondary loophole. PASS.

### CR-F1 — Task 11.A row-count under-constrained → **CLOSED**

Step 1 (line 266) tightened to: `row count ≥ 720 AND ≥ 500 rows with non-zero copm_mint_usd OR ccop_usdt_inflow_usd`, plus the explicit continuity assertion (`copm_mint_usd` non-NaN Apr-2024 → latest, `ccop_usdt_inflow_usd` non-NaN Oct-2024 → latest, no internal NaN gaps > 3 consecutive days). All three fix-components from my recommendation landed. PASS.

### CR-F2 — Task 11.C missing nbconvert-execute → **CLOSED**

New Step 4.5 (line 319) adds an explicit `subprocess.run([..., "--execute", "--inplace", ..., "--ExecutePreprocessor.timeout=600"])` with `returncode==0` assertion. Step 1 further clarified as a post-authoring behavior test (not structural-existence). PASS.

### CR-F3 — Task 11.D fix-log not cited as 11.E review input → **CLOSED**

Task 11.E Step 1 (line 360) now names BOTH the patched spec AND the fix-log at `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-fix-log.md` as first-class review inputs, with explicit precedent citation to Rev-2 plan-review's fix-log. PASS.

### CR-N1 — filename rename `..._remittance_fetcher.py` → **REJECTED (ACCEPTABLE)**

TW rejected as "unnecessary churn"; explicit note inlined at Task 11.A Files block (line 261). Rationale is defensible — renaming post-commit creates a `_loader.py` vs `_fetcher.py` Rev-3 → Rev-3.1 churn that the already-committed Task 11 (`banrep_remittance_fetcher.py`) does not follow either. I accept the rejection.

### CR-N2, CR-N3, CR-N4 → **CLOSED**

CR-N2 (matrix-row checklist) applied via PM-F4 fix at Task 11.D Step 1 (lines 340-347). CR-N3 (`flow_directional_asymmetry_w` pos-day definition) pinned inline at Task 11.B Step 1 (line 292, parenthetical). CR-N4 (task-count footer) applied via PM-N1 growth narrative (line 883). PASS.

---

## 3. New findings on Rev-3.1 additions (regression check)

### Phase 1.5 promotion (PM-F2): No new BLOCKs

- Phase-1.5 section (line 242) cleanly bounded with its own gate rationale (line 244) and gate statement (line 246). The "Phase 2 appears as two section blocks" structural note (line 215) is the awkward bit but is explicitly annotated as intentional, and the spec-coverage self-check at line 865 names the Phase-1.5 boundary correctly. No forward-reference dependency bugs: Task 12's failing-test-authoring-parallel + implementation-blocked gate is coherent.
- File-path scope: all Phase-1.5 file paths remain within Rule 4 allow-list. No violation.
- Subagent assignments: 11.A=DE, 11.B=DE, 11.C=AR (X-trio), 11.D=TW+skill-reinvocation, 11.E=CR+RC+TW — all match prior cycle's verified coherence.

### Rule 14 (PM-B1): No new BLOCKs

Rule 14 at line 40 formalizes frozen-pending-authorization cleanly, enumerates three scenarios (a/b/c), and names the specific in-flight subagent. The generalization clause ("any future mid-execution plan-review convergence point") is forward-compatible without creating silent-approval loopholes. Good rule.

### Recovery protocols (PM-F1): No new BLOCKs

- Task 11.A (line 274-279): three failure modes enumerated with concrete actions + explicit "Do NOT fabricate data" re-assertion.
- Task 11.C (line 322-325): PASS/INCONCLUSIVE/FAIL-BRIDGE paths clearly routed, with the Rev-1.1.1 scope-narrowing clause bounded to §4.1 interpretation only (no mechanism change) — this correctly inherits the Task 11.D decision gate.
- Task 11.E (line 365-369): BLOCK-routing decision tree has clean per-reviewer routing; the "multiple simultaneous BLOCKs counts as one cycle, not N cycles" clause is the correct anti-ping-pong guard.

### Decision gates (PM-F3, PM-F4): No new BLOCKs

- Task 11.C 3-HALT/5-HALT split decision (line 312) delegates to implementer at authoring time with explicit criterion. Acceptable.
- Task 11.D wording-only vs economic-mechanism classification gate (line 337) is sharp and committable pre-patch. Strong fix.

---

## 4. New FLAGs / NITs

**None.**

One marginal observation (not even a NIT): the Phase-2 "two section blocks" split (Task 11 historical in the first block, Tasks 12-15 in the second) is textually ugly but defensibly annotated. A future Rev could consider renaming the first block to "Phase 2-prelude" but this is a naming aesthetic, not a defect.

---

## 5. Sign-off

**PASS.** All 2 Rev-3 BLOCKs + 3 Rev-3 FLAGs CLOSED; 3 of 4 NITs CLOSED, 1 REJECTED with acceptable rationale; no new BLOCK/FLAG/NIT introduced by Rev-3.1 additions. Rev-3.1 is executable. Per Rule 13 second-cycle convergence: **ship it.** Phase 1.5 may proceed (subject to parallel Reality Checker + Senior PM second-cycle reviews reaching PASS independently).

— Code Reviewer
