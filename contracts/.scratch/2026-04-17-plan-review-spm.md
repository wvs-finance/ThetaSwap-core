# Plan Review — Econ Notebook Implementation (Senior PM)

**Plan:** `contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md`
**Spec:** `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` (rev 2)
**Reviewer:** SeniorProjectManager
**Date:** 2026-04-17

---

## 1. Spec Coverage (§1–§14)

| Spec § | Covered by | Verdict |
|---|---|---|
| §1 Purpose/Scope | All tasks | APPROVED |
| §2 Audience/Format | Task 1 (scaffold), Task 6 (nbconvert) | APPROVED |
| §3 Folder Layout | Task 1 | APPROVED |
| §4.1 cleaning.py determinism + purity | Task 4 (purity lint), Task 13 (emission) | **NEEDS FIX** — determinism guarantee (byte-identical across runs, dtype/ordering stability) is never asserted. Task 13 asserts presence + column set but not deterministic re-run equality. Add a test step: call `load_clean_weekly_panel` twice, assert `pd.testing.assert_frame_equal(df1, df2, check_dtype=True)` and that CSV-serialized bytes match. |
| §4.2 references.bib | Task 2 | APPROVED |
| §4.3 env.py | Task 1 | **NEEDS FIX** — spec requires `specification_curve` in the required-packages tuple; Task 1 omits it. Add to `REQUIRED_PACKAGES`. The 600s nbconvert timeout is covered in Task 6, acceptable. |
| §4.4 JSON handoff blocks | Task 20 schema test | APPROVED — Task 20 Step 1(a) enumerates every block. |
| §4.5 atomic PKL co-emission + version guard degraded mode | Task 20 (atomic), Task 22 (guard) | APPROVED — Task 20 Step 1(b) tests atomic write-or-nothing; Task 22 Step 1 tests degraded mode. |
| §4.6 Jinja2 README + CI diff check | Task 26 Tests C+D | APPROVED |
| §4.7 nb1_panel_fingerprint.json | Tasks 3, 13, 15, 22 | APPROVED |
| §5.1 citation lint | Task 5 | APPROVED |
| §5.2 code visibility | Task 6 | APPROVED |
| §5.3 chasing-offline rule | **NOT ENFORCED** | **BLOCKER** — No task asserts that notebooks contain no "we tried X and picked Y" prose. Add assertion to Tasks 14/21/27 Reality Checker charter OR add a lint scanning NB markdown for forbidden phrases ("we tried", "rejected in favor of", "we chose … over"). Minimum: explicit reviewer checklist item in Task 14/21 charter text. |
| §5.4 NB1 strict agnosticism | Task 9 Step 1 (strict agnosticism assertion mentioned in test) | **NEEDS FIX** — Task 9 references agnosticism in prose but the failing test does not assert it. Add a test assertion: grep NB1 cells for forbidden substrings ("release week", "non-release", "episode") outside Decision #9 intervention subsection. |
| §5.5 query-API-only | Task 4 | APPROVED |
| §6 NB1 sections 1–8 | Tasks 7–13 | APPROVED |
| §7 NB2 §3.5 block-bootstrap | Task 16 | APPROVED |
| §8 NB3 reordered T1→T2→T4/T5→T6→T7→T3a | Tasks 22→25 | APPROVED — order is 22(T1), 23(T2,T4,T5), 24(T6,T7), 25(T3a,forest) which matches spec §8 ordering. |
| §8 two-pronged material-mover rule | Task 26 Test A | APPROVED |
| §8 A9 two-row forest plot | Task 25 Step 1 | APPROVED |
| §9 Handoff contracts | Tasks 13, 20, 22, 26 | APPROVED |
| §10 Cell counts | Informational only | N/A |
| §11 Quality gates | Tasks 14, 21, 27 | APPROVED |
| §12 Open questions | Tasks 24 (ruptures), 25 (spec curve) | APPROVED |
| §13 Non-goals | Implicit | APPROVED |
| §14 References | Task 2 | APPROVED |

---

## 2. Realistic Task Scope

- **Task 13** (NB1 §8 ledger + cleaning.py + fingerprint): **NEEDS FIX — SPLIT**. Emitting `cleaning.py` (12-decision implementation), the 12-row ledger cell, AND fingerprint emission AND running three test files is 2–3 subagent dispatches of work. Split into **13a** (cleaning.py implementation + `test_cleaning_module.py` + Task 4 purity real-file pass) and **13b** (§8 ledger cell + fingerprint emission + `test_nb1_ledger.py`).
- **Task 18** (NB2 §6 GARCH-X + §7 decomposition): **NEEDS FIX — SPLIT**. GARCH-X alone is the single most error-prone fit in the pipeline (|s_t| enforcement, convergence guard, QMLE fallback surfacing, residual+sigma series extraction for handoff). Bundling decomposition dilutes the Model QA review in Step 3.5. Split into **18a** (§6 GARCH-X, with Model QA gate) and **18b** (§7 decomposition).
- **Task 26** (NB3 §9 spotlight + §10 gate + README Jinja2 + CI diff test): **BLOCKER — SPLIT**. Largest task in the plan; two different subagents listed (Data Engineer AND Analytics Reporter) in one task violates "one specialized subagent per task" memory rule. Split into **26a** (§9 spotlight, Analytics Reporter), **26b** (§10 gate aggregation + atomic `gate_verdict.json`, Data Engineer), **26c** (Jinja2 template + README render + CI diff, Data Engineer).
- Tasks 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 19, 20, 21, 22, 23, 24, 25, 27, 28, 29: scope is realistic for one dispatch.

---

## 3. Exact-Requirements Check

- **Task 17 Step 1**: "no auto-branching based on any outcome" — good. But "Student-t re-fit" uses `statsmodels.regression.linear_model.OLS` — OLS cannot set a Student-t likelihood. **NEEDS FIX**: name the correct API (`statsmodels.regression.linear_model.OLS` produces Gaussian MLE; Student-t requires `statsmodels.miscmodels.tmodel.TLinearModel` or a custom `GenericLikelihoodModel`). Spec §7.5 requires ν̂ reported, which only works with a Student-t likelihood implementation. Resolve API choice in task.
- **Task 20 Step 1(a)** schema enumeration: approved — every §4.4 block named.
- **Task 25 Step 1** row count: spec §8 says "13 rows under two-row A9, fewer if A9 is collapsed; exact count locked during implementation." Task 25 lists 12 rows (primary, GARCH-X, decomp-CPI, decomp-PPI, 3 subsamples, A1, A4, A5, A6, A8, A9⁺, A9⁻ = 13). **APPROVED** — count consistent.
- **Task 28**: "assert the pipeline completes and produces a verdict" — vague. **NEEDS FIX**: specify that assertions cover (a) three `.ipynb` exit 0, (b) three PDFs exist and are non-empty (>50 KB), (c) `gate_verdict.json` parses and `gate_verdict` is `"PASS"` or `"FAIL"` (not null).

---

## 4. Subagent Assignment

- **Task 2** (BibTeX scaffold, Technical Writer): APPROVED — Technical Writer owns citations/references, correct fit.
- **Task 5** (notebook-parsing CLI lint, AI Engineer): **NEEDS FIX** — AI Engineer is a mismatch for a deterministic `nbformat`-based CLI. Reassign to **Data Engineer** (consistent with Task 3 fingerprint utility, same toolchain).
- **Task 6** (nbconvert LaTeX template, Technical Writer): APPROVED — LaTeX template authoring is doc-adjacent.
- **Task 26** (mixed Data Engineer + Analytics Reporter): see Section 2 split recommendation.
- **Task 28** (Reality Checker for end-to-end run): APPROVED — Reality Checker owns cross-artifact verification per memory.
- All other assignments approved.

---

## 5. Dependency Graph

- Task 6 → Task 7: spec requires cell tags (`remove-input`, `section:N`) to drive PDF filtering and test-cell filtering. Plan states Phase 0 parallel {2,3,4,5,6} then Phase 1. APPROVED.
- Task 5 → Task 7: citation lint must exist before first citation-block cell authored. APPROVED (Phase 0 precedes Phase 1).
- Task 3 → Task 13: fingerprint utility precedes emission. APPROVED.
- Task 13 → Task 15: NB2 imports cleaning module. APPROVED.
- Task 20 → Task 22: NB3 loads handoff. APPROVED.
- **NEEDS FIX**: Task 4 purity lint's real-file assertions skip until `cleaning.py` exists (Task 13). The plan's Step 3 comment hints at this but the dependency is implicit. Add explicit note in Task 13: "This task causes Task 4's real-file assertions to activate; re-run Task 4 test suite as part of Task 13 Step 5 (already in Test C — OK)."

---

## 6. Review Gates

- **Task 14** (NB1: Model QA + Reality Checker + Technical Writer): APPROVED. Covers econometric defensibility, citation reality, narrative clarity.
- **Task 21** (NB2: Model QA + Reality Checker + Code Reviewer): **NEEDS FIX** — Code Reviewer covers serialization/atomicity but NB2 PDF readability (ladder presentation, GARCH convergence diagnostics rendering, Student-t side-by-side layout) has no Technical Writer pass. Options: (a) swap Code Reviewer for Technical Writer; (b) add a 4th reviewer. Recommend (a): Code Reviewer's serialization concerns are already covered by Task 20's explicit schema test and atomic-emit test. Technical Writer is the missing lens for PDF-export-ready NB2.
- **Task 27** (NB3: Model QA + Reality Checker + Technical Writer): APPROVED.

---

## Top-Level Verdict

**APPROVED WITH CHANGES**

**Must-fix before execution (BLOCKERs):**
1. §5.3 chasing-offline rule enforcement (add reviewer checklist or lint).
2. Task 26 split into 26a/26b/26c (two subagents in one task violates memory rule).

**Should-fix (NEEDS FIX):**
3. §4.1 determinism assertion added to Task 13 (or 13a).
4. §4.3 `specification_curve` added to Task 1 `REQUIRED_PACKAGES`.
5. §5.4 strict agnosticism test assertion in Task 9.
6. Task 13 split into 13a (cleaning.py) + 13b (ledger + fingerprint).
7. Task 18 split into 18a (GARCH-X) + 18b (decomposition).
8. Task 17 Student-t API name correction.
9. Task 28 specific assertion list.
10. Task 5 reassignment AI Engineer → Data Engineer.
11. Task 21 reviewer swap Code Reviewer → Technical Writer.

With these 11 changes, the plan is dispatchable task-by-task under the subagent-driven-development workflow.
