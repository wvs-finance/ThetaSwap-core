# Code Reviewer — Plan Implementation Guidance Review

**Plan:** `contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md`
**Spec:** `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` (rev 2)
**Reviewer:** Code Reviewer (guidance-quality lens)

---

## 1. Task atomicity — NEEDS FIX

Most Phase 0/Phase 2/Phase 3 tasks are crisply scoped (one subagent, named files, explicit assertions). Pain points:

- 🟡 **Task 1** bundles seven file creations, a justfile edit, a gitignore edit, `env.py` design, notebook skeletons, and a `pin_seed()` helper in one Data Engineer dispatch. This is ~four atomic tasks. Split into (1a) folder + gitkeeps + gitignore, (1b) env.py + test, (1c) ipynb skeletons, (1d) justfile recipe.
- 🟡 **Task 13** asks Data Engineer to simultaneously (a) implement `cleaning.py` from the 12 decisions emitted across Tasks 7–12, (b) author §8 ledger, (c) emit fingerprint, (d) re-run the Task-4 purity test. The "implementation is the cumulative interpretation of 12 prior decisions" is inherently non-atomic. Plan should require Task 13 to produce a cleaning-spec document first that a subsequent dispatch implements against.
- 🟡 **Task 26** dispatches *two* subagents jointly (Data Engineer + Analytics Reporter). The orchestration boundary is undefined — who owns which files? Split into 26a (spotlight narrative) and 26b (Jinja2 + serialization).

## 2. Cross-task consistency — NEEDS FIX

- 🔴 **Test file naming drift.** Tasks use `test_nb1_section1.py`, `test_nb2_section1_2.py`, `test_nb2_section3.py`, `test_nb3_section1_2.py`. Some collapse consecutive sections (1_2), others don't (§3 alone, §4_5, §6_7). Add a one-line convention: `test_nb{N}_section{FIRST}[_...{LAST}].py`.
- 🟡 **Artifact path root.** Plan mixes `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/...` and bare `estimates/nb2_params_point.json`. Lock one convention and reference it via an env.py constant everywhere.
- 🟢 Module names (`cleaning.py`, `panel_fingerprint.py`, `env.py`, `lint_notebook_citations.py`, `nb2_serialize.py`) are consistent between Phase 0 creation and Phase 1–3 import. Task 20 introduces `contracts/scripts/nb2_serialize.py` which was not reserved in Phase 0; add to Task 1 file manifest or add a new Phase-0 task.

## 3. Dependency ordering — NEEDS FIX

- 🟢 Phase 0 → 1 → 2 → 3 dependency chain is sound.
- 🟡 **Task 4 self-contradiction.** Step 2 expects failure because `cleaning.py` does not exist; Step 3 says "the test passes by correctly detecting the synthetic violator; the real-file assertions skip gracefully." Pytest doesn't fail a test that skips — so Step 2's "confirm failure" is false. Fix: the failing-test gate must run against a *violator fixture with real-file assertions stubbed in*, not against a missing file. Rewrite Steps 1–3.
- 🔴 **Task 5 timing vs Phase 1.** Task 5's lint must run on every NB1 commit from Task 7 onward. Plan doesn't state whether pre-commit is installed/activated after Task 5 or merely staged in config. If merely staged, Tasks 7–13 can commit notebooks with missing citation blocks. Add Step: "install pre-commit hooks (`pre-commit install`) before Task 7 begins."
- 🟡 **Task 13 → Task 15 fingerprint consistency.** Task 15 asserts the fingerprint match, but neither task specifies the `conn` fixture (how is DuckDB connected in tests?). Add a shared conftest fixture to Task 1.

## 4. Implementer pain points — NEEDS FIX

- 🔴 **Task 9 figure specificity.** "Three standalone figure blocks for raw RV, log(RV), RV^{1/3} — each with a time-series subplot, an ACF subplot (lags 1–12), and a distribution subplot." A lazy Analytics Reporter can satisfy this with axis labels absent. Require axes labels, units (log-returns squared vs %²·252), title referencing the transform, and a caption citing the bibliography key.
- 🔴 **Task 16 highlight ambiguity.** Plan says "Column 6 highlighted (bold-border or colored background in the LaTeX render)" with "or" leaving implementation ambiguous. Pick one mechanism (recommend: a `\cellcolor{gray!15}` on the column header row, or bolded row labels). Lock it.
- 🔴 **Task 20 AGREE/DISAGREE definition.** §10 reconciliation rule is "±1 SE on sign and significance at 10%" — but which SE (OLS HAC? GARCH QMLE?) and which parameter (β̂ on CPI only, or δ̂ too)? Task 20 Step 3 uses the same prose. Specify: agreement requires (a) same sign, (b) overlapping 90% CIs using each fit's own SE, (c) concordant significance at 10% — tested on β̂_CPI for OLS vs δ̂ for GARCH-X (the two are not the same parameter; "±1 SE" comparison across different parameters is undefined).
- 🟡 **Task 26 README template fields.** Plan names the file `_readme_template.md.j2` but doesn't enumerate the required sections (one-line verdict, β̂ table, reconciliation row, forest-plot embed, per-test table, links to three PDFs, spec-hash footer). Add an explicit section checklist.

## 5. Hidden pitfalls — NEEDS FIX

- 🔴 **Task 6 timeout.** Pinning `ExecutePreprocessor.timeout=600` is likely insufficient. GARCH-X MLE at ~2,500 daily obs + Student-t + Hessian PD checks + B=1000 block bootstrap + Bai-Perron endogenous breaks + 12 sensitivity refits + PDF export can exceed 10 minutes on a laptop. Raise default to 1800s or make it configurable via env.py constant `NBCONVERT_TIMEOUT`.
- 🟡 **env.py version pins timing.** Task 1 creates env.py with version-pin asserts; but the resolution of *which* pin values is implicit. Add a Step: "read version strings from the current venv's `pip freeze` and write those exact pins into env.py, recording the venv activation command in the README."
- 🟡 **Pre-commit install step missing.** No task adds `pre-commit install` to `contracts/requirements.txt` or the setup doc. The hook exists only in config until a developer runs `pre-commit install` manually.
- 🟡 **`just notebooks` idempotency.** NB2 writes a JSON to `estimates/`; NB1 writes the fingerprint. Re-running `just notebooks` overwrites both. Task 28 should assert the second run produces byte-identical JSON (determinism guarantee from §4.1).

## 6. Test quality — APPROVED WITH CHANGES

- 🟢 Tasks 3, 4 (after the Step 2 fix), 5, 6, 20 describe tests precisely enough that a skilled developer writes the correct test.
- 🟡 Tasks 7–12 describe notebook tests via headless execution and output-content assertions ("asserts the executed output contains a manifest table"). The assertion *target* is underspecified — is this a DOM/HTML parse of the rendered notebook, a check on a specific cell's `outputs` list, or a text substring? Add: "assertions operate on `nb.cells[i].outputs` for code cells or `nb.cells[i].source` for markdown cells, using `nbformat` to parse the post-execution `.ipynb`."
- 🟡 Task 13 Test A asserts "no nulls in columns the ledger commits to clean" — "columns the ledger commits to" is not a machine-readable contract. Require the ledger to emit a companion YAML or JSON manifest declaring per-column null-policy, which the test reads.

---

## Top-level Verdict

**APPROVED WITH CHANGES.** The plan's architecture, dependency chain, and subagent dispatching are sound, and the no-code constraint is respected. But four blockers will cause concrete mid-task stalls: (1) Task 4's impossible failing-test gate, (2) Task 16 highlight ambiguity, (3) Task 20 reconciliation rule definition, (4) Task 6 timeout under-provisioning. The naming-consistency and figure-specificity fixes are lower-severity but accumulate into reviewer churn. Apply the listed fixes before dispatching Phase 0.
