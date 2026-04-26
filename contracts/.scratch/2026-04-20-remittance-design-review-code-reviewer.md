# Code-Reviewer review — 2026-04-20 remittance-surprise design doc

Reviewed: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md`

## 1. Executive verdict

**PASS-WITH-FIXES.** The design is structurally sound, inherits cleanly from Rev-4, and its constraint list for `writing-plans` is unusually specific (phase-by-phase, agent-by-agent). All cited Rev-4 artifacts physically exist. Two scope contradictions, one broken reference convention, and three pre-commitment gaming surfaces need in-place fixes before `writing-plans` consumes it. None require structural rework.

## 2. BLOCK-severity findings

### B1. Scope contradiction: `contracts/notebooks/` and `contracts/research/data/` are not in the scripts-only allow-list
- **Design line 40**: "only `contracts/scripts/`, `contracts/research/data/`, `contracts/notebooks/`, and `.gitignore` are touched."
- **Design line 118**: "touches `contracts/scripts/`, `contracts/research/data/`, `.gitignore` exclusively (per `feedback_scripts_only_scope.md`)."
- **Design line 174**: "no pre-existing file outside `contracts/notebooks/fx_vol_remittance_surprise/`, `contracts/scripts/`, `contracts/research/data/`, and `.gitignore` is modified."
- **Actual memory** (`/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/feedback_scripts_only_scope.md`) says the exhaustive allowed list is: `contracts/scripts/*.py`, `contracts/scripts/tests/*.py`, `contracts/data/` (note: NOT `research/data/`), `contracts/.gitignore`, `contracts/requirements.txt`. The Rev-4 CPI exercise de-facto wrote to `contracts/notebooks/` anyway, but the memory was never updated to reflect that precedent.
- **Fix**: Either (a) cite that Rev-4 established a superseding precedent and add `contracts/notebooks/fx_vol_*/` explicitly to an "amended allow-list" section, or (b) update the memory first (out-of-band) and then re-cite. Also reconcile `research/data/` vs `data/` — the design uses both without disambiguation.

### B2. Sensitivity-sweep specification contradicts "only one new data column added"
- **Design line 29**: "Exactly one new data column added to the frozen Colombia weekly panel."
- **Design line 62**: sensitivity sweep includes "pre-/post-2015 subsample split", "Petro-Trump Jan-2025 event-dummied subsample", and "A1 monthly-cadence re-aggregation". The 2015 break dummy, the Jan-2025 event dummy, and the monthly re-aggregation cannot be executed with only one new column; they require a regime-dummy column, an event-dummy column, and a monthly-frequency panel respectively.
- **Fix**: Either (a) restate as "exactly one new *primary regressor* column; additional auxiliary columns for pre-registered sensitivity dummies are permitted and enumerated in §Methodology", or (b) drop the subsample dummies from pre-registration and keep only re-slicing-based sensitivities. Leaving this unresolved hands `writing-plans` an unsolvable ordering constraint.

### B3. Three memory paths use `~/.claude/projects/.../memory/` ellipsis that cannot be resolved deterministically
- **Design lines 11, 104, 181**: reference `~/.claude/projects/.../memory/project_colombia_yx_matrix.md` and "closing memory update in `~/.claude/projects/.../memory/`".
- The actual path is `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/`. The `...` ellipsis is human-readable but `writing-plans` and downstream review agents cannot mechanically resolve it. A plan task that says "read file at path-with-ellipsis" is not auditable.
- **Fix**: Replace all `.../memory/` with the full absolute path. Three instances.

## 3. FLAG-severity findings

### F1. Pre-commitment item #1 is gameable — "spec hash computed and committed to git before any β̂ is computed"
- **Design line 82**: The discipline is "spec hash computed," but there is no stated witness of WHEN β̂ was first computed. If the author updates the spec after first running the regression but before writing the gate-verdict cell, the Git log will show spec-hash committed before gate-verdict — but not before β̂. Rev-4 had the same issue; the de-facto witness was "no `params_point.json` file exists in the tree at spec-commit time".
- **Fix**: Add: "Spec-hash commit SHA must be an ancestor of any commit adding `estimates/nb2_params_point.json` or `nb2_params_full.pkl`. CI check enforces this via `git merge-base --is-ancestor`."

### F2. "Integration tests" deliverable references a directory naming convention inconsistent with existing artifacts
- **Design line 103**: `test_nb{1,2,3}_remittance_end_to_end_execution.py`.
- **Existing CPI tests** (verified): `test_nb1_end_to_end_execution.py`, `test_nb2_end_to_end_execution.py`, `test_nb3_end_to_end_execution.py` — no `_cpi_` infix.
- With two sibling exercises, dropping a distinguishing infix on either side creates collision risk; adding `_remittance_` on one side but not the other creates discovery asymmetry.
- **Fix**: Either rename CPI tests to `_cpi_` suffix (breaks frozen artifact discipline — reject) or use a subdirectory `contracts/scripts/tests/remittance/test_nb{1,2,3}_end_to_end_execution.py`. Pick one and state it in the design.

### F3. Reconciliation-rule "identical to Rev-4's `nb2_serialize.reconcile()` semantics" asserts semantics, not code
- **Design line 60**: Claims identical semantics but does not specify whether the Phase-A.0 implementation CALLS the existing `reconcile()` (inheritance-by-import) or RE-IMPLEMENTS it (inheritance-by-spec). These are observably different for additive-only claims.
- **Fix**: State "calls `from scripts.nb2_serialize import reconcile`; no re-implementation." This makes the additive-only claim testable.

### F4. Success-criterion "Three notebooks pass integration tests in CI" is under-specified
- **Design line 170**: "no silent-test-pass instances" — but the 5-instance CPI catalogue (in `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md`) lists specific patterns (e.g. tests that pass with zero assertions, tests that import but never execute the guard). Without naming the pattern checks, a reviewer cannot mechanically verify the criterion.
- **Fix**: Reference the specific 3-integration-test guard from the lessons memory and state which patterns the integration tests must affirmatively exclude.

### F5. Anti-fishing structural separation is asserted at risk line 163 but not specified with testable witnesses
- The design asserts CPI vs remittance are "different causal mechanisms" (line 163), but an external reviewer cannot verify this without seeing (a) the distinct pre-registered hypothesis statement, (b) the distinct null, (c) the distinct sensitivity sweep. These are scattered across §Scientific question and not co-located.
- **Fix**: Add a §"Why this is not a rescue of CPI-FAIL" section that lists the three structural separators in one place.

## 4. NIT-severity findings

### N1. Line 11 references `~/.claude/projects/.../memory/project_colombia_yx_matrix.md` in the YAML frontmatter but the file is 181 not 11 for the full path. Minor YAML hygiene.

### N2. Design line 96 says "path assigned at spec-creation time" for the Rev-1 spec. Naming it explicitly (e.g. `2026-04-2X-remittance-surprise-trm-rv-spec.md`) would let `writing-plans` emit the filename deterministically without a round-trip.

### N3. Line 165 "Decision-hash drift risk" mentions "any inadvertent mutation of existing columns aborts the panel-load step" — good, but does not cite which function enforces it. `cleaning.py._compute_decision_hash` is the enforcer; cite it inline.

### N4. The "scripts-only scope" clause (line 40) and the "feedback_scripts_only_scope.md" citation (line 118) appear in two different phases. Consolidate into §Scope and reference from phase-1.

### N5. Line 133 "Model QA Specialist (if available)" — "if available" is non-deterministic. Either include or exclude; hedged inclusion is not plannable.

## 5. Positive findings (preserve during fixes)

- **Explicit constraint propagation for `writing-plans`** (lines 106–139): phase-by-phase, agent-by-agent, with review gates named. Unusually precise for a design doc. Do not weaken during fixes.
- **Additive-only inheritance claim** (line 76) is backed by specific file enumeration (lines 68–74), all seven of which were verified to exist on disk.
- **Anti-fishing framing** is stated at multiple levels: spec, notebook headers, emission JSON, memory file. Repetition is load-bearing.
- **Risk section** (§Risks and caveats, lines 157–165) names seven concrete risks with plan-phase disposition. Each risk has a witness (revision vintage, 2015 regime, 2025 Petro-Trump, silent-test-pass). This is reviewer-actionable.
- **Distinction between Phase-A.0 / Phase-A.1 / Phase-B / Phase-C** (lines 141–155) keeps Phase-A.0 tightly scoped while giving `writing-plans` visibility into the larger program.
- **Pre-commitment item #11** (line 92) asserts anti-fishing at spec, notebook header, and emission level — three-layer redundancy is correct discipline.

## 6. Reference-integrity audit

| # | Reference (as stated in design) | Absolute path | Exists? |
|---|---|---|---|
| 1 | Rev-4 CPI spec (L8, L178) | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` | YES |
| 2 | CPI impl plan (L9, L179) | `.../contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md` | YES |
| 3 | CPI gate_verdict.json (L10, L180) | `.../contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json` | YES (FAIL verdict confirmed) |
| 4 | CPI README (L180) | `.../contracts/notebooks/fx_vol_cpi_surprise/Colombia/README.md` | YES |
| 5 | 01_data_eda.ipynb (L68) | `.../contracts/notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb` | YES |
| 6 | 02_estimation.ipynb (L69) | `.../contracts/notebooks/fx_vol_cpi_surprise/Colombia/02_estimation.ipynb` | YES |
| 7 | 03_tests_and_sensitivity.ipynb (L70) | `.../contracts/notebooks/fx_vol_cpi_surprise/Colombia/03_tests_and_sensitivity.ipynb` | YES |
| 8 | cleaning.py (L71) | `.../contracts/scripts/cleaning.py` | YES |
| 9 | nb2_serialize.py (L72) | `.../contracts/scripts/nb2_serialize.py` | YES |
| 10 | gate_aggregate.py (L73) | `.../contracts/scripts/gate_aggregate.py` | YES |
| 11 | render_readme.py (L74) | `.../contracts/scripts/render_readme.py` | YES |
| 12 | Y×X matrix memory (L11, L181) | `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_colombia_yx_matrix.md` | YES — but design uses `.../memory/` ellipsis (B3) |
| 13 | Y×X agent reports (L182) | `.../contracts/.scratch/2026-04-20-*.md` | YES (5 files found) |
| 14 | REMITTANCE_VOLATILITY_SWAP corpus (L183) | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/` | YES |
| 15 | MACRO_RISKS framework (L184) | `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/` | YES |
| 16 | All 13 project memories (L186–199) | `.../memory/feedback_*.md` + `project_*.md` | ALL 13 YES — all present in the angstrom-worktree memory dir |

**Summary**: 16/16 references resolve to existing files. Three of them (lines 11, 104, 181) use an unresolvable `.../memory/` ellipsis that `writing-plans` cannot mechanically follow — see finding B3.

---

**End of code-reviewer report.** Absolute paths throughout. Review is read-only; design doc not modified.
