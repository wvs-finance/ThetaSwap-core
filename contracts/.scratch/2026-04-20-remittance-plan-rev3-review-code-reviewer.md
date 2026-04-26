# Rev-3 Plan Patch — Code Reviewer Independent Review

**Reviewer:** Code Reviewer (discipline-isolated; parallel to Reality Checker + Senior PM)
**Subject:** Rev-3 patch at `6034b360f` inserting Tasks 11.A–11.E into `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
**Date:** 2026-04-23

---

## 1. Executive verdict

**BLOCK** — the Rev-3 middle-plan is internally well-structured (task ordering, file paths, subagent assignments, scripts-only compliance all pass), but it leaves three pre-Rev-3 artifacts in a logically inconsistent state relative to the new daily-native primary X: (1) the top-of-plan Goal statement at line 12 still asserts a "monthly remittance AR(1) surprise" primary; (2) Task 9 builds `CleanedRemittancePanelV1` around a single monthly "remittance primary-RHS column"; (3) Task 10 constructs an AR(1) surprise on the now-invalidated monthly series. Rev-3 Task 11.D patches the spec §§4.6/4.7/4.8 but never re-scopes these upstream plan tasks. Phase 2+ cannot resume coherently until plan-text consistency is restored; executing Tasks 11.A–11.E as written still leaves the seam between Phase 1 and Phase 2 broken. One additional BLOCK on the Task 11.B test-spec (silent-test-pass risk on the "pinned values at 6-decimal tolerance" claim with no fixture-generation protocol). Three FLAGs on integration-test coverage gaps in Tasks 11.A/11.C/11.D. Task count (46), row-number claims (§12 rows 5/6/7/8), file-path precision, commit-message conventions, bridge-gate logic, and subagent-assignment coherence all pass.

---

## 2. BLOCK-severity findings

### CR-B1 — Stale Goal statement + stale Phase-1 tasks under Rev-3 pivot
**Location:** Line 12 Goal; Task 9 (line 177); Task 10 (line 191); Task 13 (line 344).
**Issue:** Rev-3 Task 11.D is scoped to the **spec** at `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md`, but the **plan** carries multiple stale references to the monthly-cadence primary:
- Line 12 (Goal): `"Colombian aggregate-monthly remittance AR(1) surprise"` — unchanged.
- Task 9 Step 1: `"CleanedRemittancePanelV1 … adding only the remittance primary-RHS column"` — assumes single-column primary. Under Rev-3 the primary is a 6-channel weekly vector from Task 11.B.
- Task 10: `construct_ar1_surprise(series, …)` built for a scalar monthly series. Under Rev-3, BanRep quarterly becomes validation row S14; the primary is the on-chain weekly vector, which has no AR(1)-on-monthly step.
- Task 13 Step 1 reads: "**`a1r_monthly_rebase`** (the primary remittance surprise re-aggregated to monthly cadence …)" — this re-aggregation assumes the primary is monthly.
**Impact:** The Phase 1 → Phase 2 seam is now logically discontinuous. If Tasks 11.A–11.E execute first (as Rev-3 implies by gating Phase-2-resumption on Task 11.E), but Phase 1 Tasks 9/10 were already executed under the old semantics, the seam between "V1 dataclass with monthly primary" (Task 9) and "weekly 6-channel vector on-chain primary" (Task 11.B) has no bridge task. The `cleaning.py` extensions, the dataclass shape, and the aux-column definition in Task 13 need plan-text patches parallel to the spec patch.
**Recommended fix:** Add a **Rev-3 plan-body amendment pass** sibling to Task 11.D that patches (a) line 12 Goal wording, (b) Task 9 V1 field list, (c) Task 10 purpose (reframe as "AR(1) on BanRep-quarterly validation series only"), (d) Task 13 `a1r_monthly_rebase` semantics or demote to sensitivity. Mark all three as "Rev-3 plan-amendment rider" inside Task 11.D, or lift as Task 11.D.2. Do not execute Tasks 11.A–11.E until this plan-body re-scoping is committed.

### CR-B2 — Task 11.B golden-fixture test-spec is silent-test-pass bait
**Location:** Task 11.B Step 1 (line 264).
**Issue:** The test asserts `"pinned values from the golden fixture at 6-decimal tolerance"` for six output channels against `golden_daily_flow.csv` (a "hand-authored synthetic 35-row fixture"). But the plan provides no protocol for how the expected pinned values are computed — the author implementing Step 3 will naturally compute expected values **from the same aggregation function they are writing**, trivially passing the test. This is the exact silent-test-pass pattern catalogued in `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md`.
**Impact:** The test passes without proving the transformation is correct.
**Recommended fix:** Either (a) require Step 1 to hand-compute the six channels independently (pencil-and-paper or pandas one-liner in the test file with inline arithmetic derivation), commit the expected values **before** Step 3 implementation, and make Step 2's "confirm failure" the observable evidence; or (b) add an independent-reviewer checkpoint where a second subagent computes expected values from the fixture without reading the implementation module. Task 11.B as written fails the "would this test actually fail at the stated point" check.

---

## 3. FLAG-severity findings

### CR-F1 — Task 11.A row-count assertion `≥ 720` is under-constrained
**Location:** Task 11.A Step 1.
**Issue:** `"row count ≥ 720"` is satisfied by ~24 months but says nothing about coverage continuity, NaN-gaps inside the window, or the pre-Oct-2024 NaN-discipline claim being meaningful. An implementation returning 800 all-COPM rows with zero cCOP rows post-Oct-2024 passes.
**Recommended fix:** Add an assertion that `copm_mint_usd` has non-NaN values spanning Apr-2024 → latest and `ccop_usdt_inflow_usd` has non-NaN values spanning Oct-2024 → latest with no internal NaN gaps > 3 consecutive days.

### CR-F2 — Task 11.C notebook-execute-test coupling unclear
**Location:** Task 11.C Step 1 reads "Author failing test for the notebook's §1 … §4 (verdict emission). X-trio HALTs between each section for human review."
**Issue:** The test appears to be an ex-ante test that asserts §1–§4 exist, but the X-trio authoring discipline HALTs the author between sections. Which fails first — the test (because §1 doesn't exist yet) or the X-trio checkpoint (because section 1 trio isn't reviewed yet)? The task ordering of Steps 1 → 2 → 3 is ambiguous. Task 11.C also omits an inline `nbconvert --execute` guard analogous to Phase-3 protocol note (line 384). Under Rev-4 lessons memory, every notebook-authoring task needs an inline nbconvert-execute step to prevent the 5-instance silent-test-pass pattern.
**Recommended fix:** Add an explicit Step 3.5: `nbconvert --execute --inplace contracts/notebooks/fx_vol_remittance_surprise/Colombia/0B_bridge_validation.ipynb --ExecutePreprocessor.timeout=600; assert returncode=0`. Clarify whether Step 1's test is a structural-existence test or a post-authoring behavior test.

### CR-F3 — Task 11.D fix-log writes do not chain to Task 11.E
**Location:** Task 11.D Step 2 says the fix-log is at `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-fix-log.md`; Task 11.E's review-input is implicitly the Rev-1.1 patched spec itself.
**Issue:** Task 11.E does not explicitly name the fix-log as a review input. Rev-2 precedent (the Rev-2 plan-review fix-log cited at line 9) treated the fix-log as a first-class reviewer deliverable. Without that, reviewers at Task 11.E might evaluate the patched spec against the pre-patch spec with no rationale context.
**Recommended fix:** Task 11.E Step 1 should name both `specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` (now Rev-1.1) and `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-fix-log.md` as review artifacts.

---

## 4. NIT-severity findings

### CR-N1 — Filename-naming precedent inconsistency
**Location:** Task 11.A filename `dune_onchain_flow_fetcher.py` vs Task 11 precedent `banrep_remittance_fetcher.py` (DONE_WITH_CONCERNS; no `_loader` vs `_fetcher` ambiguity). Acceptable but consider `dune_onchain_remittance_fetcher.py` to parallel the `banrep_remittance_fetcher.py` naming.

### CR-N2 — Task 11.D Step 1 matrix-row enumeration is inline prose, not a checklist
**Location:** Task 11.D Step 1.
**Issue:** Listing rows 5/6/7/8 with per-row intended resolutions as a single paragraph creates review ambiguity. Converting to a 4-bullet checklist would make the reviewer-check in Task 11.E mechanical.

### CR-N3 — Rev-3 daily-vector aggregation `flow_directional_asymmetry_w` is ambiguous
**Location:** Task 11.B Step 1 channel 4: `"pos-days minus neg-days"`.
**Issue:** For a USD-flow series, "pos-days" and "neg-days" need definition. Is "pos-day" `mint_usd > burn_usd` on that day, or `net_flow > 0`? For cCOP (which has inflow+outflow as separate columns) the definition shifts. Pin this in the test spec.

### CR-N4 — Task count footer update missed one parallel claim
**Location:** Line 816 reads `"Phase 2: Tasks 11, 11.A, 11.B, 11.C, 11.D, 11.E, 12, 13, 14, 15 (10 tasks; up from 5 in Rev-2 …)"`. Correct count. No defect. Task-count self-check PASSES: 5 (Phase 0) + 5 (Phase 1) + 10 (Phase 2) + 18 (Phase 3) + 8 (Phase 4) = 46, and `grep -c "^### Task"` returns 46. Verified.

---

## 5. Positive findings

- **§12 matrix-row claims accurate.** The plan's "rows 5/6/7/8 revisited" claim cross-references correctly against `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md:272-275`: row 5 = Andrews bandwidth, row 6 = LOCF direction, row 7 = AR order, row 8 = vintage discipline. The rationale annotations ("no longer applies; mark as superseded" for row 6; "now on daily-aggregated weekly vector" for row 7; "daily on-chain does not revise" for row 8) are coherent with the daily-native pivot.
- **Bridge-gate logic is coherent and post-hoc-adjustment-proof.** `PASS: ρ > 0.5 AND sign-concordant`, `FAIL: ρ ≤ 0.3 OR sign-discordant`, `INCONCLUSIVE: 0.3 < ρ ≤ 0.5` partitions the [−1, 1] ρ-space cleanly with no gaps. Pre-registration language ("pre-registered gate BEFORE computing any correlation") is explicit. The FAIL-BRIDGE narrative-pivot clause ("economic interpretation shifts from 'remittance' to 'crypto-rail income-conversion'") is anti-fishing-compliant — the primary regression still runs on a well-defined observable.
- **Scripts-only scope compliance: PASS.** All new file paths (`contracts/scripts/dune_onchain_flow_fetcher.py`, `contracts/scripts/weekly_onchain_flow_vector.py`, `contracts/data/copm_ccop_daily_flow.csv`, `contracts/data/dune_onchain_sources.md`, `contracts/scripts/tests/remittance/*`, `contracts/notebooks/fx_vol_remittance_surprise/Colombia/0B_bridge_validation.ipynb`, `contracts/.scratch/*`, `contracts/docs/superpowers/specs/…rev1.md` via Rev-2 allow-list extension) fall within Rule #4's allow-list. Zero violations.
- **Subagent assignment coherence: PASS.** 11.A/11.B = Data Engineer (matches `project_ran_python_session.md` and memory rule for Dune-MCP-bearing tasks); 11.C = Analytics Reporter with X-trio discipline (matches `feedback_notebook_trio_checkpoint.md`); 11.D = Technical Writer with `structural-econometrics` re-invocation clause (acceptable per `feedback_specialized_agents_per_task.md`); 11.E = three parallel reviewers CR + RC + TW (matches `feedback_three_way_review.md`).
- **Commit-message convention: PASS.** All five tasks use `(Rev-3 Task 11.X)` suffix. `feat(remittance):` for code tasks (11.A/11.B/11.C); `spec(remittance):` for spec-patch tasks (11.D/11.E). Consistent with recent-commit style in `git log`.
- **Task 11.A fallback clause ("do NOT fabricate data") properly defends the real-data-over-mocks rule** from memory (`feedback_real_data_over_mocks.md`).
- **Task 11.E gate language** ("This gate is non-negotiable per memory rule `feedback_three_way_review.md`") correctly cites the memory rule and invokes the 3-cycle cap from Plan Rule 13. Good discipline.

---

## Recommended resolution path

1. Author a **Rev-3 plan-body amendment rider** (new sub-task bundled into Task 11.D or lifted as Task 11.D.2) patching line 12 Goal, Task 9 dataclass scope, Task 10 purpose, Task 13 `a1r_monthly_rebase` semantics. Without this, Rev-3 resolves the spec but leaves the plan self-contradictory. **(BLOCK CR-B1)**
2. Revise Task 11.B Step 1 to require hand-computed pinned expected values committed before Step 3 implementation, with an independent-reviewer checkpoint. **(BLOCK CR-B2)**
3. Address FLAGs CR-F1, CR-F2, CR-F3 inline.
4. NITs are optional.
5. Re-run Code Reviewer after these are applied.

---

**Sign-off:** Code Reviewer — BLOCK. Ready to re-review after CR-B1 and CR-B2 are addressed; FLAGs/NITs non-blocking for second pass.
