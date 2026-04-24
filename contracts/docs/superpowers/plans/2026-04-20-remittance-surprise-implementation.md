# Phase-A.0 Remittance-Surprise → TRM-RV Implementation Plan

> **Status:** Rev 3.2 (2026-04-20). See Revision history below. **Rev 3 three-way plan review converged Cycle 1 of 3 per Rule 13; Rev 3.1 applied consolidated fixes; Rev 3.2 is a factual-correction point patch to the Task 11.A row-count threshold (anchored to the measured COPM on-chain launch date 2024-09-17 per Dune `#6940691`) — no new review cycle required.**
> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Revision history

- **Rev 1 (2026-04-20):** initial plan, 30 tasks across 5 phases, committed alongside the three-way-reviewed design doc at `437fd8bd2`.
- **Rev 2 (2026-04-20):** three-way plan review applied (Code Reviewer + Reality Checker + Senior PM); 6 BLOCKs + 14 FLAGs + 7 NITs addressed; task splits and inserts executed (Tasks 17 → 17a/17b/17c; 21 → 21a/21b/21c with a separate Task 21d review gate; 22 → 22a/22b; 24 → 24a/24b with a separate Task 24c review gate; 30 → 30a/30b/30c; + intra-phase review-gate inserts at 18a, 21d, 24c); Phase-0 Task 1 tightened with the "13-input resolution matrix" deliverable requirement; Task 11 data-access mechanism corrected from "pinned Socrata endpoint" to MPR-derived manual compilation (no public remittance API exists; `mcec-87by` is TRM-only). See fix-log at `contracts/.scratch/2026-04-20-remittance-plan-fix-log.md`. Total task count: **41** (5+5+5+18+8 across Phases 0-4).
- **Rev 3 (2026-04-20):** mid-execution methodology escalation. Task 11 implementation (committed at `939df12e1` DONE_WITH_CONCERNS) confirmed the Rev-2 RC B1 finding was worse than anticipated: **BanRep publishes remittance at QUARTERLY cadence only**, not monthly. The load-bearing grounding is the **BanRep suameca series 4150 metadata** at `https://suameca.banrep.gov.co/estadisticas-economicas/informacionSerie/4150/remesas_trabajadores` (series id `REMESAS_TRIMESTRAL`, `descripcionPeriodicidad=Trimestral`, `fechaUltimoCargue=2026-03-06`; in-tree provenance at `contracts/data/banrep_mpr_sources.md:42-52`), corroborated by the ficha metodológica. Four MPR PDFs were inspected as corroborating-only evidence (their "C. Ingresos secundarios (transferencias corrientes)" row is total-current-transfers, not disaggregated remittance; they do not themselves publish a disaggregated monthly aggregate — a negative corroboration, not a confirmation). 104 real quarterly rows (2000-Q1 → 2025-Q4) were committed; Rev-1 spec §§4.6 (monthly LOCF), §4.7 (AR(1) on monthly), §4.8 (real-time vintage primary) are thereby invalidated for the monthly-cadence primary. Rev 3 inserts a **daily-native middle-plan** (new Tasks 11.A–11.E) that: (a) acquires daily on-chain COPM + cCOP flow data via Dune MCP, (b) aggregates daily → weekly via a rich statistics vector preserving intra-week information, (c) cross-validates against the BanRep quarterly series via a pre-registered bridge ρ-gate at N=7 quarterly obs, (d) patches the Rev-1 spec to Rev-1.1 with the new primary X definition + BanRep quarterly as validation row, (e) three-way reviews the Rev-1.1 patch before Phase 2 resumes at Task 12. Total task count: **46** (5+5+**5**+5+18+8 after Rev 3.1 Phase-1.5 promotion; see Rev 3.1 below). **Rev 3 patch is awaiting three-way plan review; no Rev 3 tasks shall execute until that review converges.**
- **Rev 3.1 (2026-04-20):** three-way plan review of the Rev 3 patch converged (Code Reviewer + Reality Checker + Senior PM, same trio as Rev-2 plan review). Unanimous "needs fixes": 6 BLOCKs, 10 FLAGs, 9 NITs. Rev 3.1 applies consolidated fixes in place. Key changes: (1) **plan-body amendment riders** patch upstream stale references to monthly-cadence primary (Goal line 12; Task 9 `CleanedRemittancePanelV1` scope; Task 10 AR(1)-surprise purpose; Task 13 `a1r_monthly_rebase` renamed to `a1r_quarterly_rebase_bridge`) that Rev 3's spec-only patch had left inconsistent; (2) **Task 11.B silent-test-pass hardening** — pinned expected values require an independent reproduction witness (mirrors Task 10 `test_golden_fixture_matches_independent_fit` pattern); (3) **factual-attribution rewrite** of the Rev 3 history bullet grounding BanRep-quarterly-only on the suameca series 4150 metadata (load-bearing) with MPR PDFs relegated to corroborating-only; (4) **cCOP-TOKEN vs Mento-BROKER address disambiguation** in Task 11.A (`0x777a8255…` is the broker venue, not the token; post-2026-01-25 migration renamed cCOP → COPm at the same contract address); (5) **new Rule 14** formalizing retroactive-authorization semantics for in-flight subagents launched before plan-review convergence; (6) **Rule 13 cycle-cap boundary** defined at Task 11.E Step 3 (one cycle = one full 3-parallel-reviewer round-trip + TW consolidation); (7) **Phase 1.5 "Data-Bridge" promotion** — Tasks 11.A–11.E lift out of Phase 2 into a new Phase 1.5 between Phase 1 and Phase 2, restoring Rev-2 PM F4 Task-11/12 parallelism; Phase 2 reverts to its Rev-2 shape (5 tasks: 11, 12, 13, 14, 15); (8) **recovery protocols** added to Tasks 11.A/11.C/11.E enumerating explicit fallback behavior for three distinct failure modes; (9) **decision gates** formalized at Task 11.D Step 1 (wording-only vs economic-mechanism change) and Task 11.C Step 1 (3-HALT vs 5-HALT split). Task IDs 11.A–E preserved; task count unchanged at **46** (5+5+5+5+18+8). See fix-log at `contracts/.scratch/2026-04-20-remittance-plan-rev3-fix-log.md` for per-finding disposition.

**Goal (Rev 3.1 amended — CR-B1):** Implement Phase-A.0 of the Abrigo structural-econometric program: a single-row exercise testing whether a **weekly rich-aggregation vector of daily on-chain COPM + cCOP remittance-channel flows** (per Rev-1.1 spec §4.1 after Task 11.D patch) carries detectable information for COP/USD weekly realized volatility, under identical Rev-4 discipline, on the frozen 947-obs weekly panel (decision-hash extended, not replaced), with pre-registered anti-fishing framing distinct from the CPI-FAIL. The original monthly-BanRep-AR(1) primary was superseded at Rev 3 after Task 11 confirmed BanRep publishes remittance at quarterly cadence only (suameca series 4150 metadata); the BanRep quarterly series is preserved as a pre-registered validation row S14, not as the primary X.

**Architecture:** Three notebooks (NB1 EDA + panel-fingerprint-extension, NB2 OLS ladder + GARCH(1,1)-X + T3b gate + reconciliation, NB3 T1-T7 tests + forest plot + sensitivity sweep + gate aggregation + README auto-render) co-located under `contracts/notebooks/fx_vol_remittance_surprise/Colombia/`. The exercise reuses the Rev-4 `scripts/` pipeline additively — `cleaning.py`, `nb2_serialize.py`, `gate_aggregate.py`, `render_readme.py`, `env.py` — with remittance-specific extensions. Phase 0 invokes the `structural-econometrics` skill to derive the Rev-1 spec resolving the 13 methodology mandatory-inputs enumerated in the design doc. No code in this plan — every task dispatches a specialized subagent with a prose specification.

**Tech Stack:** Python 3.12+, DuckDB 1.5+, statsmodels, arch, scipy, pandas, numpy, matplotlib, specification_curve, Jinja2, jupyter + nbconvert, bibtexparser, ruptures, just (existing worktree justfile).

**Design doc:** `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md` (committed at `437fd8bd2`, three-way-reviewed CR+RC+MQ, TW-consolidated).

**Reference plan:** `contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md` (Rev-4 CPI 33-task plan that shipped successfully 2026-04-19 with FAIL verdict).

---

## Non-Negotiable Rules (enforced on every task)

1. **Strict TDD.** Every task writes a failing test first, verifies the failure, implements minimally via a dispatched subagent, verifies the pass, then commits. Never write implementation before an observably failing test.
2. **Specialized subagent per task.** Foreground orchestrates and verifies; never authors. Each task below names exactly one subagent.
3. **X-trio checkpoint for notebook authoring.** Every task that dispatches a subagent to write notebook cells follows the Notebook Authoring Protocol below. Bulk authoring forbidden.
4. **Scripts-only extended allow-list.** Pipeline work touches `contracts/notebooks/fx_vol_remittance_surprise/`, `contracts/scripts/`, `contracts/scripts/tests/remittance/`, `contracts/data/`, `contracts/.gitignore`, and `contracts/docs/superpowers/specs/` + `contracts/docs/superpowers/plans/` (design-doc + plan directory extensions per Rev-4 precedent). Never `src/`, `test/*.sol`, `foundry.toml`, or any Solidity. **Exception (Rev-2):** completion-record writes to `~/.claude/projects/*/memory/` are permitted out-of-worktree per Rev-4 precedent (see `project_fx_vol_cpi_notebook_complete.md` — the CPI project wrote its completion memory to this path on 2026-04-19). This exception is scoped to Task 30a only.
5. **Additive-only to the frozen panel.** Decision-hash from Rev-4 panel is **extended**, not replaced. Any mutation of existing columns aborts the panel load.
6. **Citation block before every decision/test/fit.** Four parts: reference, why used, relevance to results, connection to Phase-B simulator. Enforced by the Rev-4 pre-commit citation lint (reused as-is).
7. **Chasing-offline rule.** Spec searching, model comparison, rejected alternatives live in the Analytics Reporter's private scratch — never in committed notebooks. Rev-4 forbidden-phrase lint reused.
8. **Anti-fishing discipline.** Every task asserts this is Phase-A.0 — a distinct pre-commitment on the remittance external-inflow channel — not a rescue of the CPI-FAIL. Commit messages and notebook headers reference the design doc's "Why this is not a rescue of CPI-FAIL" section.
9. **Push origin, not upstream.** `origin` = JMSBPP.
10. **Real data over mocks.** Tests hit real DuckDB and real BanRep-derived fixtures; mocks only for HTTP errors that cannot be reproduced.
11. **Test-file naming convention.** All Phase-A.0 tests live under `contracts/scripts/tests/remittance/` to avoid collision with CPI tests. Naming: `test_nb{N}_remittance_section{FIRST}[_{LAST}].py`. **Exception:** environment / scaffold / fixture / integration-guard tests are exempt (e.g., `test_env_remittance.py`, `test_scaffold.py`, `test_banrep_remittance_fetcher.py`, `test_end_to_end_determinism.py`).
12. **Artifact path constants.** All inter-task artifact paths reference constants from `env_remittance.py` (a remittance-specific sibling to the Rev-4 `env.py`).
13. **Reviewer-loop cycle cap.** Any task that says "iterate to PASS" (Task 27, Task 29 sequences) is capped at 3 reviewer cycles. After the third failed cycle, halt and escalate to the user for scope renegotiation rather than recursing silently. (Addresses PM F3; mirrors the Rev-4 spec-derivation 12-cycle cost as a visibility guardrail.)
14. **Retroactive-authorization of in-flight subagents (Rev 3.1 insert — PM-B1).** Any subagent dispatch started before a plan-review convergence point is **frozen-pending-authorization**. Its outputs shall not be committed until the gating review returns unanimous PASS (or PASS-WITH-FIXES) and the TW-consolidation fix-pass lands. Concretely: the Task 11.A implementer dispatched at 2026-04-20 prior to Rev-3 plan-review convergence is specifically named as frozen-pending-authorization. Its artifacts (if returned) are speculative — unused by downstream tasks — until Task 11.E PASSes. Disposition by scenario: (a) if the in-flight subagent completes successfully and its artifacts satisfy Task 11.A Step-1 test assertions, the artifacts become eligible-to-commit under the Task-11.A commit message only *after* Task 11.E PASSes; (b) if the in-flight subagent fails (Dune free-tier hit or schema mismatch), the failure mode + proposed remediation become explicit Task-11.E inputs and no artifact is committed from that dispatch; (c) if the in-flight subagent returns DONE_WITH_CONCERNS, Task 11.E inputs the concern log and either authorizes commit or halts for scope renegotiation. This rule generalizes beyond Task 11.A: any future mid-execution plan-review convergence point inherits the same frozen-pending-authorization semantics for any subagent launched before that point.

---

## Notebook Authoring Protocol (X-trio checkpoint)

Per memory rule `feedback_notebook_trio_checkpoint.md`. Every task that dispatches Analytics Reporter to author notebook cells proceeds trio by trio:

**Trio = (why-markdown cell) + (code cell) + (interpretation-markdown cell)**

1. Subagent writes one markdown cell with the four-part citation block. The "Why used" part explains why the next code cell runs.
2. Subagent writes the code cell.
3. Subagent executes the code cell and verifies it runs without error.
4. Subagent writes one markdown cell interpreting the specific results the code cell just produced.
5. Subagent HALTS and requests human review before authoring the next trio.

Bulk authoring of multiple trios in a single dispatch is forbidden. Infrastructure tasks (scaffold, lint scripts, env, CI tests) are exempt.

---

## Phase 0 — Rev-1 Spec Derivation + Three-Way Review

### Task 1: Invoke `structural-econometrics` skill for Rev-1 spec

**Subagent:** foreground invokes the `structural-econometrics` skill (per user's global CLAUDE.md convention of skill-as-spec-deriver).

**Files:**
- Create: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md`

- [ ] **Step 1:** Pin the design-doc commit hash via `git rev-parse HEAD -- contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md` and confirm it matches `437fd8bd2` (or record the current hash in the Rev-1 spec header if it has advanced). The Rev-1 spec derivation consumes the design doc verbatim. (Addresses RC N1.)
- [ ] **Step 2:** Invoke `structural-econometrics` skill passing: (a) the design doc absolute path as the question-scope; (b) the 13 items under §"Mandatory inputs to the Phase-0 structural-econometrics skill call" in the design doc as the resolution set. The skill must produce a Rev-1 spec that resolves every one of the 13 items with a concrete pre-committed choice and a justification trail.
- [ ] **Step 3:** Verify the Rev-1 spec file was written to the expected path with a non-empty body.
- [ ] **Step 4 (Rev-2 tightened — gating deliverable):** Require the Rev-1 spec to include a **13-input resolution matrix** as a standalone table with exactly four columns: (item | resolution | justification | reviewer-checkable condition). The 13 rows must be: sign prior, MDES, HAC kernel, bandwidth rule, interpolation side, alternate-LHS sensitivity, AR order, vintage discipline, reconciliation rule under heteroskedasticity, Quandt-Andrews window, GARCH parametrization, Dec-Jan seasonality, event-study co-primary. Each row's "reviewer-checkable condition" column must state the objective signal Tasks 2-4 reviewers will verdict against (e.g., "HAC kernel row PASSes iff a Bartlett/Parzen/QS choice is named AND a one-sentence citation is given AND a bandwidth-selection rule is specified"). Absence of the matrix, or any row with a null reviewer-checkable condition, is a spec-derivation failure. (Addresses PM B2.)
- [ ] **Step 5: Commit** the Rev-1 spec with message `spec(remittance): Rev-1 spec derived by structural-econometrics skill; 13-input resolution matrix embedded`.

### Task 2: Code Reviewer independent review of Rev-1 spec

**Subagent:** Code Reviewer

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1-review-code-reviewer.md`

- [ ] **Step 1:** Dispatch Code Reviewer agent with the Rev-1 spec as input and the design doc's Phase-0 mandatory-inputs list as the coverage checklist. Focus: row-by-row verdict against the 13-input resolution matrix (Task 1 Step 4) — for each row, assert the reviewer-checkable condition is met. Do not tell the agent about parallel reviewers.
- [ ] **Step 2:** Verify the report landed at the expected path.
- [ ] **Step 3:** Log verdict (PASS / PASS-WITH-FIXES / BLOCK) and itemized BLOCK/FLAG/NIT findings.
- [ ] **Step 4:** Commit the scratch report with message `review(remittance): Code Reviewer Rev-1 spec review`.

### Task 3: Reality Checker independent review of Rev-1 spec

**Subagent:** Reality Checker

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1-review-reality-checker.md`

- [ ] **Step 1:** Dispatch Reality Checker with the Rev-1 spec as input. Instruct the agent to audit every factual claim, data-source availability statement, literature citation, and evidence-backed methodology choice. Focus: for each row of the 13-input resolution matrix, verify the "justification" column cites something that exists (paper, corpus file, public dataset) and the "reviewer-checkable condition" can be evaluated against observable reality.
- [ ] **Step 2:** Verify report landed.
- [ ] **Step 3:** Log verdict + findings.
- [ ] **Step 4:** Commit with message `review(remittance): Reality Checker Rev-1 spec review`.

### Task 4: Technical Writer independent review of Rev-1 spec

**Subagent:** Technical Writer

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1-review-technical-writer.md`

- [ ] **Step 1:** Dispatch Technical Writer with the Rev-1 spec as input. Focus: clarity, internal consistency, ambiguity resolution, reference integrity, reader-auditability of each pre-committed choice. Explicitly audit the 13-input resolution matrix for column-completeness and cross-section consistency (no row orphaned, no row with conflicting language elsewhere in the spec).
- [ ] **Step 2:** Verify report landed.
- [ ] **Step 3:** Log verdict + findings.
- [ ] **Step 4:** Commit with message `review(remittance): Technical Writer Rev-1 spec review`.

### Task 5: Technical Writer consolidates + applies fixes to Rev-1 spec

**Subagent:** Technical Writer

**Files:**
- Modify: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md`
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1-fix-log.md`

- [ ] **Step 1:** Dispatch Technical Writer with all three review reports + the Rev-1 spec. Apply fixes in place: BLOCKs first (design-level issues in place; methodology BLOCKs escalated back to `structural-econometrics` skill if the reviewer-revealed methodology choice cannot be made at Technical-Writer level).
- [ ] **Step 2:** Verify the fix-log documents every finding's disposition (applied / deferred with reason / rejected with reasoning).
- [ ] **Step 3:** If any BLOCK was deferred, halt and require re-invocation of `structural-econometrics` skill for that specific item.
- [ ] **Step 4:** Confirm word-count delta is documented.
- [ ] **Step 5: Commit** the Rev-1 spec update + fix-log with message `spec(remittance): Rev-1 spec fix-pass, all 3-way reviewer findings addressed`.

---

## Phase 1 — Infrastructure Extension (Additive to Rev-4 Pipeline)

### Task 6: Scaffold remittance-exercise folders + scoped `.gitignore` rules

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/.gitkeep`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/figures/.gitkeep`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/pdf/.gitkeep`
- Create: `contracts/scripts/tests/remittance/__init__.py`
- Modify: `contracts/.gitignore`

- [ ] **Step 1: Write the failing test.** `contracts/scripts/tests/remittance/test_scaffold.py` asserts: three subfolders exist under `contracts/notebooks/fx_vol_remittance_surprise/Colombia/`; `contracts/.gitignore` contains scoped rules for `contracts/notebooks/fx_vol_remittance_surprise/**/estimates/*.pkl`, `contracts/notebooks/fx_vol_remittance_surprise/**/pdf/`, and the same `_nbconvert_template/**/*.aux` pattern (or whichever pattern Rev-4 actually emits — cross-check the Rev-4 `contracts/.gitignore` block added by the CPI project and mirror it exactly to avoid drift; addresses CR N3); the `remittance/__init__.py` test package is importable.
- [ ] **Step 2: Run the test and confirm failure.**
- [ ] **Step 3: Create folders + gitkeeps; extend `.gitignore` with the three scoped rules.**
- [ ] **Step 4: Run the test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): folder scaffold + scoped gitignore for Phase-A.0`.

### Task 7: `env_remittance.py` — path constants + package pins

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/env_remittance.py`
- Create: `contracts/scripts/tests/remittance/test_env_remittance.py`

- [ ] **Step 1: Write the failing test.** Assert `env_remittance` exposes: `DUCKDB_PATH` (same value as Rev-4 `env.DUCKDB_PATH` — shared DB), `ESTIMATES_DIR`, `FIGURES_DIR`, `PDF_DIR`, `FINGERPRINT_PATH`, `POINT_JSON_PATH`, `FULL_PKL_PATH`, `GATE_VERDICT_REMITTANCE_PATH`, `README_REMITTANCE_PATH`, `NBCONVERT_TIMEOUT` (inherit from Rev-4), `REQUIRED_PACKAGES` (inherit from Rev-4). Assert `pin_seed(seed)` helper is re-exported from the Rev-4 `env.py` (no duplication). Assert the `conn` fixture at `contracts/scripts/tests/remittance/conftest.py` yields a DuckDB connection to the same DB.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3 (Rev-2 disambiguated — CR F2):** Implement `env_remittance.py` as a sibling to Rev-4 `env.py`. The absolute source path for the Rev-4 module is `contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py`. Import strategy: add a top-of-file block of the form `from contracts.notebooks.fx_vol_cpi_surprise.Colombia.env import pin_seed, NBCONVERT_TIMEOUT, REQUIRED_PACKAGES, DUCKDB_PATH as _REV4_DUCKDB_PATH`; set `DUCKDB_PATH = _REV4_DUCKDB_PATH` to signal the shared-DB contract. The remittance-specific `ESTIMATES_DIR`, `FIGURES_DIR`, `PDF_DIR`, `FINGERPRINT_PATH`, `POINT_JSON_PATH`, `FULL_PKL_PATH`, `GATE_VERDICT_REMITTANCE_PATH`, `README_REMITTANCE_PATH` are declared as module-level constants in `env_remittance.py` (NOT re-exported from Rev-4). If Python-package-import semantics fail (`contracts.notebooks…` is not a declared package), use a `sys.path`-insert shim with the absolute notebook-directory path; document the chosen strategy in the module docstring.
- [ ] **Step 4: Implement `conftest.py`** deferring to the Rev-4 conftest fixture. The Rev-4 conftest exists at `contracts/scripts/tests/conftest.py` (verified on disk per RC evidence); assume it exists (per PM N2; Rev-4 shipped). If the fixture-import fails at test time, fail loudly rather than silently re-implement.
- [ ] **Step 5: Run and confirm pass.**
- [ ] **Step 6: Commit** with message `feat(remittance): env_remittance.py path constants, inherit-from-Rev-4 package pins`.

### Task 8: Empty `.ipynb` skeletons + placeholder README

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/02_estimation.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/README.md` (placeholder, overwritten by Task 24)
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/_readme_template.md.j2`
- Test: `contracts/scripts/tests/remittance/test_notebook_skeletons.py`

- [ ] **Step 1: Write the failing test.** Assert each `.ipynb` is valid `nbformat.v4` with: (a) title markdown cell; (b) "Phase-A.0 — Remittance-surprise → TRM RV" header with explicit anti-fishing disclaimer paragraph from the design doc's §"Why this is not a rescue of CPI-FAIL"; (c) "Gate Verdict" placeholder admonition ("populated after NB2 and NB3"); (d) zero code cells; (e) the Jinja2 template has the 7-section structure from Rev-4 but with remittance-specific wording.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author skeletons using `nbformat`.** Jinja2 template copied from Rev-4 `_readme_template.md.j2` as starting point with wording swaps.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): .ipynb skeletons + anti-fishing disclaimer headers + README template`.

### Task 9: Extend `cleaning.py` with `load_cleaned_remittance_panel`

**Subagent:** Data Engineer

**Files:**
- Modify: `contracts/scripts/cleaning.py` (additive only — new function)
- Test: `contracts/scripts/tests/remittance/test_cleaning_remittance.py`

**Rev 3.1 plan-body amendment rider (CR-B1):** Under Rev 3.1, the primary X is the weekly rich-aggregation vector from Phase-1.5 Task 11.B (6 on-chain channels per week), not a single scalar monthly-remittance column. The `CleanedRemittancePanelV1` scaffold below is *retained as a vestigial seam* so the dataclass hierarchy (V1→V2→V3) and the decision-hash-extension seam remain intact; its "remittance primary-RHS column" semantics are overridden by Phase-1.5 Task 11.B at panel-assembly time (Task 12+), where the 6-channel vector replaces the scalar. Implementers: the V1 dataclass should either (a) carry a scalar placeholder column that Task 11.A/B overwrites on load, or (b) promote the scalar slot to a `Mapping[str, np.ndarray]` container that Task 11.B populates. Decide at implementation time after reading Rev-1.1 spec §4.1 (Task 11.D output).

- [ ] **Step 1 (Rev-2 scoped — CR B2; Rev 3.1 amended — CR-B1): Write the failing test, restricted to primary-RHS only.** Assert `load_cleaned_remittance_panel(conn) → CleanedRemittancePanelV1` exists, where `CleanedRemittancePanelV1` is a new frozen dataclass mirroring `CleanedPanel` but adding **only** the remittance primary-RHS scaffold column (vestigial seam per the rider above — Phase-1.5 Task 11.B overrides the actual content; no auxiliary columns, no quarterly-corridor column — those extend the dataclass in Tasks 13 and 14). Assert it inherits the Rev-4 `LockedDecisions` + extends with remittance-primary-RHS decision identifiers only. Assert the existence (but not the full behavior) of a `_compute_decision_hash_remittance` seam that the Task-12 test will exercise end-to-end; Task 9 only asserts the primary-RHS scaffold column is hashed. Full-dataclass validation (V1 → V2 aux columns → V3 corridor) is deferred to Task 15 panel-integration.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.** The new function loads the Rev-4 frozen panel via `load_cleaned_panel(conn)`, joins the remittance primary-RHS column, and installs the decision-hash-extension seam. Do not pre-declare fields that Tasks 13/14 will add; let those tasks extend the dataclass additively (`CleanedRemittancePanelV2` extending V1, etc.) so each task's test asserts only the columns it is responsible for.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): cleaning.py extension — load_cleaned_remittance_panel (V1: primary-RHS only), additive to Rev-4`.

### Task 10: AR(1) surprise constructor module

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/surprise_constructor.py` (pure — frozen dataclass + free functions per functional-python skill)
- Test: `contracts/scripts/tests/remittance/test_surprise_constructor.py`

**Rev 3.1 plan-body amendment rider (CR-B1):** Under Rev 3.1, the AR(1)-surprise pathway is **no longer applied to the primary X** (the primary is the Phase-1.5 Task 11.B weekly 6-channel vector, which does not go through AR(1) surprise construction). Task 10's `construct_ar1_surprise` is retained as a reusable pure module scoped to **validation row S14 — the BanRep-quarterly series** (per Rev-1.1 spec §6). Its role is to emit the quarterly-cadence AR(1) surprise that the bridge-validation notebook (Phase-1.5 Task 11.C) and the downstream sensitivity-row ladder (Task 23) consume. Implementers: the AR-order parameter, the pre-sample discipline, and the interpolation-side resolution-matrix rows (Rev-1.1 §12 rows 6/7/8) are resolved by Task 11.D with the caveat that row 6 (LOCF direction) no longer applies under Rev 3.1 — BanRep-quarterly has no intra-quarter vintages to interpolate — and row 8 (vintage discipline) shifts from daily-on-chain-no-revision to quarterly-snapshot-at-publication-date.

- [ ] **Step 1 (Rev 3.1 amended — CR-B1): Write the failing test, scoped to the BanRep-quarterly validation path only.** Assert `construct_ar1_surprise(series, pre_sample_end_date, vintage_policy) → SurpriseSeries` exists. Assert the pre-sample / rolling refit policy pinned in the Rev-1.1 spec is honored. Assert the quarterly-snapshot vintage-policy path (per Rev-1.1 §12 row 8 after patch) is honored; the LOCF-interpolation path is no longer exercised (Rev-1.1 §12 row 6 superseded). Explicitly flag that the surprise constructor does NOT run against the primary X (Task 11.B weekly vector bypasses this module).
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.** Pure function; no side effects; input validation at boundaries only.
- [ ] **Step 4: Run and confirm pass with golden fixtures** (real BanRep-derived test data in `contracts/scripts/tests/remittance/fixtures/`).
- [ ] **Step 5: Commit** with message `feat(remittance): AR(1) surprise constructor per Rev-1 spec`.

---

## Phase 2a — Data Ingestion (historical anchor: Task 11 only)

> **Rev-3.1 F-3.1-1 reconciliation note**: Phase sequence is intentionally non-monotone (0, 1, **2a**, 1.5, **2b**, 3, 4). Task 11 landed DONE_WITH_CONCERNS BEFORE the escalation, so it physically precedes the Phase-1.5 middle-plan that responds to its finding. Phase 2b (Panel Extension, Tasks 12-15) resumes after Phase 1.5 convergence. Readers: follow 0 → 1 → 2a (Task 11) → 1.5 (Rev-3 middle-plan) → 2b (Tasks 12-15) → 3 → 4.

**Rev 3.1 structural note (PM-F2):** Phase 2 in Rev-3.1 spans Task 11 (DONE_WITH_CONCERNS at `939df12e1`, retained here as historical context because its quarterly-only BanRep finding is the trigger for Phase 1.5) followed by the textual insert of **Phase 1.5 — Data-Bridge** (Tasks 11.A–11.E) and then Phase 2 resumes with Tasks 12-15. Textually this means "Phase 2" appears as two section blocks in the document: the first containing only Task 11 (historical), the second (after Phase 1.5) containing Tasks 12–15. This is intentional — it preserves the causal ordering (Task 11 triggers Phase 1.5 triggers Phase-2-resume) while keeping Task 11 inside Phase 2 per the Rev-2 shape.

### Task 11: BanRep aggregate monthly remittance — MPR-derived manual compilation (Rev-2, may parallelize with Task 12)

**Subagent:** Data Engineer

**Scheduling note (Rev-2, PM F4):** Task 11 and Task 12 share no code dependency; their failing-test authoring and implementation can run in parallel. The Task-12 decision-hash-extension only depends on Task 9's `CleanedRemittancePanelV1` seam, not on Task 11's fixture.

**Rev-2 correction (RC B1):** The original plan asserted a "pinned public Socrata endpoint" for aggregate monthly remittance. This is **factually wrong**: the BanRep Socrata dataset `mcec-87by` at `datos.gov.co/resource/mcec-87by.json` is the *Tasa de Cambio Representativa del Mercado* (TRM) feed, not remittance. No public API (Socrata, SDMX, REST, or otherwise) publishes BanRep aggregate-monthly family-remittance inflows as a single time series. The access pattern is: BanRep's quarterly **Monetary Policy Report (MPR)** / *Informe de Política Monetaria* PDFs and Excel annexes publish remittance aggregates in Balance-of-Payments tables. These must be compiled by hand once per quarter, committed as a real-data fixture, and re-pulled manually (not by API) when a new MPR vintage drops. Vintage-timestamp = MPR publication date.

**Files:**
- Create: `contracts/scripts/banrep_remittance_loader.py` (loader, not API fetcher)
- Create: `contracts/data/banrep_remittance_aggregate_monthly.csv` (manually compiled real-data fixture, committed; source column names each cell's originating MPR table)
- Create: `contracts/data/banrep_remittance_aggregate_monthly.SOURCE.md` (per-row provenance: MPR quarter, table number, URL, access date)
- Test: `contracts/scripts/tests/remittance/test_banrep_remittance_loader.py`

- [ ] **Step 1 (Rev-2 manual-compilation subtask):** Before writing any code, the Data Engineer manually compiles `banrep_remittance_aggregate_monthly.csv` from the BanRep MPR series covering the Rev-4 sample window. Each row: `date` (month-end), `aggregate_inflow_usd`, `mpr_vintage_date`, `source_table`. The `SOURCE.md` file records per-row provenance (MPR URL + table reference + access timestamp) so a reviewer can audit the compilation by hand.
- [ ] **Step 2: Write the failing test.** Assert `load_banrep_aggregate_monthly_remittance(csv_path) → DataFrame` exists and returns columns `date` (month-end) + `aggregate_inflow_usd` + `mpr_vintage_date`. Assert the loader is a pure read of the committed CSV (no network calls). Assert the row count matches the expected monthly count over the Rev-4 sample window. Assert every row has a non-null `mpr_vintage_date`. Do **not** assert "pinned endpoint returns the same data" — the re-pull mechanism is manual MPR re-parse, not an API call.
- [ ] **Step 3: Run and confirm failure.**
- [ ] **Step 4: Implement** the pure-read loader. Document explicitly in the module docstring that re-pulling requires MPR re-parse; there is no API.
- [ ] **Step 5: Run and confirm pass** against the committed fixture.
- [ ] **Step 6: Commit** with message `feat(remittance): MPR-derived aggregate monthly remittance loader + manually compiled fixture with per-row SOURCE provenance`.

**Task 11 post-implementation status (Rev 3, 2026-04-20):** implementation committed at `939df12e1` as DONE_WITH_CONCERNS. File name actually used was `banrep_remittance_fetcher.py` (not `_loader.py` as the Rev-2 plan text said); schema emitted `{reference_period, value_usd, mpr_vintage_date, source_url}`. The implementer exhaustively verified that BanRep publishes this series at QUARTERLY cadence only (104 rows 2000-Q1 → 2025-Q4, all carrying `mpr_vintage_date = 2026-03-06` snapshot; no revision archive). The monthly-cadence primary in Rev-1 spec §§4.6/4.7/4.8 is invalidated. **Phase 1.5 Tasks 11.A–11.E (below, promoted out of Phase 2 per Rev-3.1 PM-F2) are the Rev-3 middle-plan response.**

---

## Phase 1.5 — Data-Bridge (Rev 3.1 promoted per PM-F2)

**Phase-1.5 rationale:** Rev-3 originally placed Tasks 11.A–11.E inside Phase 2 alongside Task 11 and Tasks 12–15. Rev-3.1 (PM-F2) promotes them to a new Phase 1.5 "Data-Bridge" sub-phase between Phase 1 and Phase 2, for three reasons: (i) the 5 tasks form a single atomic workstream (daily-native primary acquisition + bridge-validation + spec patch + spec-patch review) distinct from the Phase-2 panel-extension workstream (Tasks 12–15); (ii) promoting them restores the Rev-2 PM F4 granted parallelism between Task 11 and Task 12 (which Rev-3's Phase-2-gate had silently retracted); (iii) a standalone phase boundary makes the gate language ("Phase 2 resumes only after Task 11.E PASSes") clean rather than surgical-mid-phase. Task IDs 11.A–E are preserved.

**Phase-1.5 gate (clarified per Rev 3.1 PM-F2 alt-resolution):** Task 12 depends only on Task 9's `CleanedRemittancePanelV1` scaffold (per Rev-2 PM F4) and may begin its failing-test authoring in parallel with Phase 1.5. However, Task 12's *implementation step* (merging primary X into the panel) is blocked until Task 11.E PASSes, because the primary X definition is set by the Rev-1.1 spec patch (Task 11.D output). Tasks 13–15 remain fully blocked until Phase 1.5 closes. Phase 3 remains fully blocked until Phase 2 closes.

### Task 11.A: Daily on-chain COPM + cCOP flow acquisition via Dune MCP (Rev 3 insert; Rev-3.1 Phase-1.5 promoted)

**Subagent:** Data Engineer (MANDATORY: `mcp__dune__*` tools)

**Rationale (Rev 3.1 amended — RC-F2, RC-N2):** The quarterly-only BanRep finding means the monthly-cadence primary cannot be built from public off-chain data. The daily-native middle-plan replaces it with a daily on-chain signal aggregated to weekly via a rich statistics vector (not a flat sum), preserving intra-week information that a monthly-aggregate X would discard. COPM launched Apr-2024 (adoption-colour figures such as "$200M/mo" and "100K Littio users" circulate in marketing materials but are not in-corpus-verified by Reality Checker at Rev 3.1 review; removed from load-bearing rationale per RC-N2; retained only as non-load-bearing background). cCOP launched Oct-2024. Per `CCOP_BEHAVIORAL_FINGERPRINTS.md` line 27: the 4,913-sender figure is specifically the cCOP-OLD cohort (address `0x8a56…`, "Dead (migrated Jan 2025)") — it is a pre-migration lifetime stock, NOT a forward-looking active-post-Oct-2024 population (RC-F2 correction). The post-migration cohort populating Apr-2024 → present may be smaller and must be recomputed by the Task 11.A subagent at acquisition time; "≥4,913 lifetime cleaned-cohort senders (pre-migration)" is the only defensible phrasing. Union window: Apr-2024 → most-recent ≈ 22-24 months daily. **Pre-committed N for downstream T3b critical value and bridge-gate power analysis: N = 95 weekly observations** (the conservative floor anchored to Rev-4-panel-end Feb-2026; RC-F3 single-number commitment). If the observed sample yields more than 95 weekly rows at Task 11.A implementation time, the additional rows are held in the fixture but the pre-committed test statistic uses exactly N=95 anchored at the Feb-2026 floor.

**Data-target disambiguation (Rev 3.1 — RC-B2):** two distinct on-chain entities must not be conflated:
- **cCOP TOKEN contract address** — the ERC-20 token itself (holds balances, `transfer`/`transferFrom` events are the raw transfer signal). The Task 11.A subagent must look up the current cCOP token contract via Dune `mcp__dune__searchTablesByContractAddress` or Celo block explorer before querying; **note the post-2026-01-25 migration renamed cCOP → COPm at the SAME contract address** (per corpus `CCOP_BEHAVIORAL_FINGERPRINTS.md` migration row) — the subagent must handle the rename and verify the address maps to the active (not "old/dead") contract. **Rev-3.1 F-3.1-2 footnote**: the corpus file `CCOP_BEHAVIORAL_FINGERPRINTS.md` has an internal date inconsistency on this migration — line 27 reads "Jan 2025" while line 163 reads "Jan 2026"; Rev-3.1 aligns with the more specific line-163 date ("2026-01-25") as the canonical rename date. The subagent MUST use 2026-01-25 as the cutover and ignore the line-27 reading.
- **Mento BROKER contract address** `0x777a8255ca72412f0d706dc03c9d1987306b4cad` — the swap venue (Mento protocol broker, NOT the token). Its events are swap-level, not transfer-level. Dune query `#6939814` queries broker swaps and is the correct source for swap-venue volumes; it is **not** a source for token-level transfers.

A subagent that confuses these two queries the broker when it needs token transfers, or vice versa — the data acquired will be categorically wrong. Task 11.A Step 3 must explicitly verify each query's target entity before execution.

**Files:**
- Create: `contracts/scripts/dune_onchain_flow_fetcher.py` (pure loader + validator; no network on import) — filename preserved per Rev-3 precedent (CR-N1 optional rename to `dune_onchain_remittance_fetcher.py` rejected as unnecessary churn)
- Create: `contracts/data/copm_ccop_daily_flow.csv` (real-data fixture, committed; columns: `date, copm_mint_usd, copm_burn_usd, copm_unique_minters, ccop_usdt_inflow_usd, ccop_usdt_outflow_usd, ccop_unique_senders, source_query_ids`)
- Create: `contracts/data/dune_onchain_sources.md` (per-query provenance log)
- Test: `contracts/scripts/tests/remittance/test_dune_onchain_flow_fetcher.py`

- [ ] **Step 1 (Rev 3.1 tightened — CR-F1; Rev 3.2 factual correction):** Write failing test asserting the 8-column schema + daily-monotone date index + pre-Oct-2024 NaN cCOP discipline + non-negative USD + non-empty `source_query_ids` + `FileNotFoundError` on missing path + determinism + **row count ≥ 580 AND ≥ 500 rows with non-zero `copm_mint_usd OR ccop_usdt_inflow_usd`** (CR-F1 tightening: bare row-count is satisfiable by zero-filled padding; the non-zero constraint ensures the data is economically load-bearing). **Rev 3.2 threshold correction**: the Rev-3.1 text said `≥ 720` on the premise of "24 months × 30 days" but COPM's actual on-chain launch is 2024-09-17 (verified via Dune `#6940691`), yielding 585 calendar days to April 2026. The 720 figure would force zero-padding a pre-launch synthetic window — the exact anti-pattern CR-F1's 500-non-zero companion is designed to forbid. The COPM-launch-anchored floor of 580 preserves CR-F1's intent. Additionally assert `copm_mint_usd` has non-NaN values spanning 2024-09-17 → latest and `ccop_usdt_inflow_usd` has non-NaN values spanning 2024-10-31 → latest with no internal NaN gaps exceeding 3 consecutive days (per CR-F1 full recommendation).
- [ ] **Step 2:** Run and confirm failure.
- [ ] **Step 3 (Rev 3.1 schema-verification step added — RC-F1):** Acquire via Dune MCP. Before executing any cached query, call `mcp__dune__getDuneQuery` on each query ID (`#6941901`, `#6940691`, `#6939814`) and verify the **actual** query title and target entity match the expected role. Specifically: `#6940691` is labeled "COP Token Comparison (all 3 tokens)" in `CCOP_BEHAVIORAL_FINGERPRINTS.md:209` — NOT "COPM transfers" as the Rev-3 plan text said (RC-F1). If the verified schema does not match the expected per-role schema for this task, **log the mismatch in `contracts/data/dune_onchain_sources.md`** and either (a) use `mcp__dune__executeQueryById` on a different cached query whose schema matches, or (b) use `mcp__dune__updateDuneQuery` only if existing-query modification is required (RC-N1: prefer read-only `mcp__dune__executeQueryById` before any `updateDuneQuery` that burns credits). Credit budget: ≤30 free-tier credits.
- [ ] **Step 4:** Write CSV with real joined data + `dune_onchain_sources.md` provenance log (including schema-verification log from Step 3).
- [ ] **Step 5:** Implement pure loader + validator.
- [ ] **Step 6:** Run tests, confirm pass.
- [ ] **Step 7:** Commit with message `feat(remittance): daily COPM+cCOP on-chain flow fixture + Dune loader (Rev-3 Task 11.A, Rev-3.1 schema-verified)`.

**Recovery protocol (Rev 3.1 — PM-F1; replaces Rev-3 "Fallback" note):** Three concrete failure modes enumerated:
1. **Dune MCP free-tier exhausted (credits burned).** Action: foreground decides between (a) manual Dune CSV export paste-in — the `source_query_ids` field of the fixture becomes a pasted-from-Dune-UI URL list rather than an MCP-returned ID list, satisfying Step-1's non-empty assertion; the `dune_onchain_sources.md` log records the paste-in method explicitly; (b) direct Celo RPC via Alchemy free tier — the loader adopts a different source-column taxonomy and the `source_query_ids` field is replaced by `source_rpc_endpoints`. Decision criterion: prefer (a) if Dune has the exact query cached; prefer (b) if Dune queries need modification beyond the credit budget. Log the decision + error messages + paste-in sources at `contracts/.scratch/2026-04-20-dune-mcp-fallback-log.md` (PM-N3 explicit scratch path).
2. **Query schema mismatch at Step-3 verification.** Action: per Step 3 body above. Does not require user escalation unless all three cached query IDs fail schema verification simultaneously, in which case escalate.
3. **Zero or near-zero data returned (e.g., all-zero-flow days exceeding 50% of rows).** Action: halt acquisition and escalate to user — either the query filters are misconfigured (fixable by Step-3 verification re-run) or the on-chain rails are genuinely sparse (a finding that itself requires re-scoping of the identification strategy). Do NOT fabricate data or pad with zeroes.

Do NOT fabricate data under any failure mode.

### Task 11.B: Weekly rich-aggregation module (daily → weekly vector; Rev 3 insert)

**Subagent:** Data Engineer

**Rationale:** Flat daily-sum-to-weekly loses intra-week heterogeneity. A multi-channel weekly vector preserves information that is load-bearing for the primary identification at small sample size (N≈95 weekly obs).

**Files:**
- Create: `contracts/scripts/weekly_onchain_flow_vector.py` (pure transformation module)
- Create: `contracts/scripts/tests/remittance/test_weekly_onchain_flow_vector.py`
- Create: `contracts/scripts/tests/remittance/fixtures/golden_daily_flow.csv` (hand-authored synthetic 35-row fixture spanning 5 Friday-anchored weeks)

- [ ] **Step 1 (Rev 3.1 hardened — CR-B2; silent-test-pass prevention; Rev 3.3 concentration-channel clarification):** Write failing test for `aggregate_daily_to_weekly_vector(daily_df, friday_anchor_tz="America/Bogota") → pd.DataFrame` with 6 output channels per week: `flow_sum_w`, `flow_var_w` (daily-within-week variance), **`flow_concentration_w` (HHI of the 7 daily |net_flow| values within the week, computed as `(|daily_flow|² summed) / (|daily_flow| summed)²`; this is INTRA-WEEK CONCENTRATION — a weekly scalar that captures whether the week's activity is spiky vs diffuse across its 7 days; it is NOT per-address concentration — the daily CSV does not carry per-address data and Task 11.B does not require it; a Task-11.A code-review reviewer misread this as per-address HHI, which is explicitly NOT the intended channel semantics)**, `flow_directional_asymmetry_w` (pos-day count minus neg-day count, where a pos-day is defined per-channel as `net_flow_usd > 0` for COPM (`copm_mint_usd − copm_burn_usd`) and for cCOP (`ccop_usdt_inflow_usd − ccop_usdt_outflow_usd`); resolving CR-N3), `unique_daily_active_senders_w` (union across COPM+cCOP), `flow_max_single_day_w`. Assert pinned values from the golden fixture at 6-decimal tolerance.

  **Independent reproduction witness (MANDATORY — mirrors Task 10 `test_golden_fixture_matches_independent_fit` pattern against the 5-instance CPI silent-test-pass catalogue):** the pinned expected values MUST be computed via an independent reproduction path in the test file that does NOT import `weekly_onchain_flow_vector`. For each of the 6 channels, the test file inlines an independent computation (e.g., `flow_sum_w` via a pandas `resample('W-FRI').sum()` one-liner; `flow_var_w` via `resample('W-FRI').var(ddof=0)`; `flow_concentration_w` via an inline `(abs_flow ** 2).sum() / abs_flow.sum()**2` reduction; analogously for the remaining three channels). The 6 pinned values in the assertion block are the outputs of these inline independent computations, committed to the test file BEFORE Step 3 implementation. Step 3's implementation must match those pinned values to pass. This guards against the silent-test-pass pattern where an implementer computes expected values from the same function being written.

  Assert determinism + order-invariance + pre-data-window NaN discipline.
- [ ] **Step 2:** Run and confirm failure — the failure mode must be "function does not exist" or "function returns wrong shape", NOT a tolerance mismatch (tolerance mismatch at this stage is evidence the independent reproduction witness is buggy, which is itself a blocker).
- [ ] **Step 3:** Implement pure vectorized aggregation (pandas groupby + named-agg). The implementation must match the independent reproduction witness to 6-decimal tolerance; any divergence means either (a) the implementation is wrong, or (b) the independent reproduction witness is wrong — both are blocking.
- [ ] **Step 4:** Run tests, confirm pass.
- [ ] **Step 5:** Commit with message `feat(remittance): weekly rich-aggregation vector preserving daily information + independent reproduction witness (Rev-3 Task 11.B, Rev-3.1 silent-test-pass hardening)`.

### Task 11.C: Bridge-validation notebook (pre-registered ρ-gate; Rev 3 insert)

**Subagent:** Analytics Reporter (X-trio discipline per `feedback_notebook_trio_checkpoint.md`)

**Rationale:** Cross-validate that the daily on-chain aggregate is an economically meaningful proxy for the BanRep remittance channel. Pre-register the gate BEFORE computing any correlation. Under FAIL-BRIDGE the primary regression still runs (X is a well-defined on-chain observable), but the economic-interpretation narrative shifts from "remittance" to "crypto-rail income-conversion."

**Files:**
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/0B_bridge_validation.ipynb` (one-off validation notebook, 4-5 X-trio cells)
- Create: `contracts/.scratch/2026-04-20-onchain-banrep-bridge-result.md` (scratch log of the gate outcome)

- [ ] **Step 1 (Rev 3.1 clarified — CR-F2, PM-F3 decision gate):** Author failing test for the notebook's §1 (data alignment), §2 (quarterly aggregation), §3 (Pearson ρ + sign-concordance), §4 (verdict emission). The test is a **post-authoring behavior test** (asserts cells execute correctly and emit the expected verdict structure), NOT a structural-existence test (it does not fail merely because §1 does not exist yet). Author-implementer's choice of granularity (PM-F3): either (a) a single Task 11.C authoring pass of 4-5 X-trios under the atomicity ceiling if the data alignment is simple enough (recommended when Task 11.A returns a clean Apr-2024 → present daily CSV with no gaps > 3 days), or (b) split into 11.C.1 (§1 alignment + §2 quarterly aggregation, 2-3 X-trios) and 11.C.2 (§3 Pearson-ρ + §4 verdict emission, 2-3 X-trios) if data cleanup adds complexity. The decision is made at 11.C authoring time by the foreground; if split, renumber internally (task IDs remain 11.C.1 / 11.C.2 — the Phase 1.5 task count stays at 5 by convention). X-trio HALTs between each section for human review.
- [ ] **Step 2:** Run nbconvert-execute; confirm failure (expected failure mode: notebook has no code cells yet, nbconvert returns non-zero).
- [ ] **Step 3:** Author NB 0B cells trio-by-trio. Pre-registered gate logic (committed BEFORE any ρ computation):
  - PASS-BRIDGE: ρ > 0.5 on N=7 quarterly obs AND sign-concordant on Δ quarter-over-quarter
  - FAIL-BRIDGE: ρ ≤ 0.3 OR sign-discordant
  - INCONCLUSIVE-BRIDGE: 0.3 < ρ ≤ 0.5
- [ ] **Step 4:** Run notebook, confirm test pass + emit scratch log with verdict.
- [ ] **Step 4.5 (Rev 3.1 mandatory — CR-F2):** Inline integration-test execution: `subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", "contracts/notebooks/fx_vol_remittance_surprise/Colombia/0B_bridge_validation.ipynb", "--ExecutePreprocessor.timeout=600"])` and assert `returncode == 0`. This is the bridge-notebook analogue of the Phase-3 protocol note (line 384) — every notebook-authoring task gets an inline nbconvert-execute guard to catch the silent-test-pass pattern locally.
- [ ] **Step 5:** Commit with message `feat(remittance): bridge-validation notebook (on-chain vs BanRep quarterly; Rev-3 Task 11.C, Rev-3.1 nbconvert-guarded)`.

**Recovery protocol (Rev 3.1 — PM-F1):** Bridge-gate outcome recovery paths:
1. **FAIL-BRIDGE (ρ ≤ 0.3 or sign-discordant).** The primary regression still runs (the on-chain X is a well-defined observable), but the economic-interpretation narrative shifts from "remittance" to "crypto-rail income-conversion." This shift MUST be documented in the completion memory (Task 30a) and the Rev-1.1.1 spec patch (not-yet-authored; create at the time FAIL-BRIDGE is observed) re-scopes the X interpretation in §4.1 only (no mechanism change — §§4.2+ unchanged). No new three-way spec review required for Rev-1.1.1 scope-narrowing of the interpretation alone; the mechanism-preservation qualifier matches Task 11.D's decision gate (see below).
2. **INCONCLUSIVE-BRIDGE (0.3 < ρ ≤ 0.5).** The primary regression still runs; the completion memory documents the inconclusive bridge as a caveat; no spec patch required.
3. **PASS-BRIDGE.** Proceed without narrative shift.

### Task 11.D: Rev-1.1 spec patch (Rev 3 insert — SPEC amendment)

**Subagent:** Technical Writer (amendment) + structural-econometrics skill re-invocation if any new methodology decision surfaces

**Rationale:** The daily-native middle-plan changes the primary X definition; the Rev-1 spec must reflect the amendment with explicit supersedes-banner language. The 13-input resolution matrix must be revisited for any row whose resolution is affected (sign prior, MDES at new effective-N, HAC bandwidth at new sample size, interpolation side no longer applies, AR order no longer on monthly-source, vintage policy now on daily on-chain source, reconciliation unchanged, Quandt-Andrews window unchanged, GARCH-X unchanged, Dec-Jan seasonality unchanged, event-study unchanged).

**Files:**
- Modify: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` (patch to Rev-1.1 in place; update frontmatter `status` + `Revision history`)
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-fix-log.md`

- [ ] **Step 1 (Rev 3.1 decision gate — PM-F4; matrix-row checklist — CR-N2):** Up-front classification gate: for each of the four §12 matrix rows being patched (5 Andrews bandwidth, 6 interpolation side, 7 AR order, 8 vintage discipline), classify the patch as either **wording-only/cadence-only** (TW completes alone) or **economic-mechanism change** (requires `structural-econometrics` skill re-invocation for that row before TW continues). The concrete rule: if the row's resolution column changes a named kernel/method/parameter/number (e.g., Andrews bandwidth rule changes from Bartlett to Parzen, AR order changes from 1 to 2, MDES target changes numerically), it is an economic-mechanism change. If the row's resolution column changes only which cadence or data source is described (e.g., "monthly series" → "daily on-chain aggregated weekly vector" with the same AR order), it is wording-only. Decision-gate output committed to the fix-log before any patch text is authored.

  Author the Rev-1.1 patch in place as a checklist:
  - [ ] Add "supersedes banner" section noting the Task 11 finding and the quarterly-only BanRep reality, grounded on the suameca series 4150 metadata (matching Rev-3.1 Revision history rewrite).
  - [ ] Redefine primary X in §4.1 as the weekly rich-aggregation vector from Phase-1.5 Task 11.B.
  - [ ] Add BanRep quarterly as a pre-registered validation row S14 in §6, fed by the Task-10 AR(1)-constructor-on-quarterly path and Task-13 `a1r_quarterly_rebase_bridge` aux column.
  - [ ] Update §4.5 MDES to reflect new N = 95 (the pre-committed conservative floor per Task 11.A Rev-3.1 rationale; RC-F3 single-number commitment).
  - [ ] Patch §12 matrix row 5 (Andrews bandwidth at new N=95; classify per decision gate).
  - [ ] Patch §12 matrix row 6 (interpolation side → "no longer applies under daily-on-chain primary; superseded"; wording-only).
  - [ ] Patch §12 matrix row 7 (AR order → "no longer applies to primary; retained for validation-row S14 quarterly AR(1) per Task 10"; classify per decision gate).
  - [ ] Patch §12 matrix row 8 (vintage discipline → "daily on-chain does not revise; quarterly validation-row vintage = BanRep MPR publication date"; wording-only).
- [ ] **Step 2:** Fix-log documents every matrix-row change with its decision-gate classification from Step 1. Any methodology-row classified as economic-mechanism change requires `structural-econometrics` skill re-invocation BEFORE TW patches the row body; fix-log records the skill-re-invocation output.
- [ ] **Step 3:** Commit with message `spec(remittance): Rev-1.1 patch — daily-native primary X + BanRep-quarterly validation row (Rev-3 Task 11.D, Rev-3.1 decision-gated)`.

### Task 11.E: Three-way review of Rev-1.1 spec patch (Rev 3 insert)

**Subagent:** three parallel dispatches — Code Reviewer + Reality Checker + Technical Writer (spec-review trio per `feedback_three_way_review.md`).

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-review-technical-writer.md`

- [ ] **Step 1 (Rev 3.1 fix-log-as-input — CR-F3):** Dispatch three reviewers in parallel; each receives **both** the patched spec at `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` (now Rev-1.1) AND the fix-log at `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-fix-log.md` as first-class review inputs (precedent: Rev-2 plan-review's fix-log was similarly a first-class reviewer deliverable; without the fix-log the reviewers cannot evaluate the decision-gate classifications Task 11.D Step 2 committed). Each reviewer independently reviews the Rev-1.1 patch against: (a) consistency with Rev-1 pre-Rev-1.1 content not superseded, (b) coverage of all 13 resolution-matrix rows that need updating, (c) anti-fishing framing preserved or strengthened (the patch is explicitly framed as a methodology escalation responding to a real-world data reality, NOT as a rescue of a null result), (d) factual grounding of any new claims (RC), (e) clarity of the supersedes-banner and the new primary X definition (TW).
- [ ] **Step 2:** Consolidate via Technical Writer; apply all BLOCKs + FLAGs in place; NITs optional.
- [ ] **Step 3 (Rev 3.1 cycle-cap boundary — PM-B2):** Iterate with an explicit cycle definition. **One cycle = one full round-trip** of: (a) three reviewers dispatched in parallel, (b) Technical Writer consolidates all three reports, (c) if any reviewer flagged BLOCK, the offending reviewer's specific BLOCK items are fixed in the spec and **that same reviewer** is re-dispatched (not all three) on the next round-trip. Plan Rule 13 caps the **count of full round-trips at 3**. Additionally, to guard against pathological ping-pong, a per-reviewer re-dispatch counter is also capped at 3 (a single reviewer may BLOCK at most 3 times before escalation). After the third failed full round-trip OR the third re-dispatch of the same reviewer — whichever triggers first — halt and escalate to the user for scope renegotiation, not silent recursion. If a BLOCK is methodology-level (reveals an economic-mechanism error in the §12 resolution matrix that was mis-classified as wording-only at Task 11.D Step 1), the `structural-econometrics` skill is re-invoked before the next round-trip; skill re-invocation does NOT itself count as a new cycle.
- [ ] **Step 4:** Commit with message `spec(remittance): Rev-1.1 fix-pass, all 3-way reviewer findings addressed (Rev-3 Task 11.E, Rev-3.1 cycle-bounded)`.

**Recovery protocol (Rev 3.1 — PM-F1):** BLOCK-routing decision tree:
1. **Code Reviewer BLOCK** (e.g., file-path errors, citation-block format violations, commit-message convention drift). Route to Technical Writer for in-place patch; re-dispatch Code Reviewer only.
2. **Reality Checker BLOCK** (e.g., cited paper does not exist, data-source availability claim is unverified, numeric value does not ground in in-tree provenance). Route to Technical Writer if the fix is textual; route to `structural-econometrics` skill if the fix requires re-deriving a methodology choice; re-dispatch Reality Checker only.
3. **Technical Writer BLOCK** (e.g., ambiguous supersedes banner, contradictory paragraphs, unclear primary-X definition). Route to Technical Writer for self-consolidation; re-dispatch Technical Writer only (a second-TW-pass is permitted and is counted as a cycle).
4. **Multiple simultaneous BLOCKs.** TW consolidation batches all fixes into one round-trip; all offending reviewers are re-dispatched in parallel (counts as one cycle, not N cycles).

**Gate:** Phase-2 tasks' implementation steps shall NOT resume until Task 11.E returns a unanimous PASS-WITH-FIXES or PASS verdict and TW consolidation is committed. This gate is non-negotiable per memory rule `feedback_three_way_review.md`. Task 12's failing-test authoring may begin in parallel with Phase 1.5 per the Phase-1.5 rationale above, but its implementation step is blocked on Task 11.E.

---

## Phase 2b — Panel Extension (resumes after Phase 1.5 convergence)

### Task 12: Decision-hash extension preserving Rev-4 fingerprint (may parallelize with Task 11)

**Subagent:** Data Engineer

**Scheduling note (Rev-2, PM F4):** Task 12 depends only on Task 9's `CleanedRemittancePanelV1` seam. It has no dependency on Task 11's fixture. Task 12's test and implementation can run in parallel with Task 11.

**Files:**
- Modify: `contracts/scripts/cleaning.py` (additive — new `_compute_decision_hash_remittance`)
- Test: `contracts/scripts/tests/remittance/test_decision_hash_extension.py`

- [ ] **Step 1 (Rev-2 scoped — CR B1): Write the failing test, restricted to primary-column hash only.** Assert (a) the Rev-4 decision-hash value (`6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`, verified by Reality Checker from `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json:23`) is preserved byte-exact when the remittance-panel loader runs; (b) the extended decision-hash is a deterministic function of the Rev-4 hash + the sorted primary-RHS-column spec hash (aux columns are hashed in Task 13, corridor column in Task 14 — their incremental hash contributions are deferred to those tasks' tests); (c) any mutation of an existing Rev-4 column aborts with `FrozenPanelViolation` at panel-load. Defer the "aux-column hash inclusion" and "corridor-column hash inclusion" assertions to the Task 13 and Task 14 test specs respectively.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** the extension function with a seam for aux-column and corridor-column hash contributions that Tasks 13 and 14 will plug into.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): decision-hash extension (primary-RHS only) preserving Rev-4 frozen panel invariants`.

### Task 13: Auxiliary columns — regime, event, A1-monthly, release-day

**Subagent:** Data Engineer

**Files:**
- Modify: `contracts/scripts/cleaning.py` (additive — new helper functions)
- Test: `contracts/scripts/tests/remittance/test_auxiliary_columns.py`

- [ ] **Step 1 (Rev 3.1 amended — CR-B1): Write the failing test.** Assert four auxiliary columns exist on the loaded panel: `regime_post_2015` (binary dummy), `event_petro_trump_2025` (binary dummy for documented Jan-2025 48h window), **`a1r_quarterly_rebase_bridge`** (the BanRep-quarterly AR(1) surprise from Task 10 rebased onto the weekly panel via step-constant within each quarter; this is the Rev 3.1 replacement for the obsolete `a1r_monthly_rebase` name, which assumed a monthly primary that no longer exists — renamed to reflect the Rev-1.1 quarterly-only BanRep reality; operationally serves as the S14 validation-row column per Rev-1.1 spec §6, exposed on the panel so the sensitivity forest-plot (Task 23) can render the bridge row alongside the on-chain primary), `release_day_indicator` (binary). Each column's computation rule matches the Rev-1.1 spec exactly. Assert each aux-column hash extends the decision-hash produced by Task 12's seam (i.e., the extended-hash after Task 13 is deterministic, includes all four aux-column spec hashes in sorted order, and still preserves the Rev-4 base hash). This test absorbs the aux-column portion of CR B1.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** extending `CleanedRemittancePanelV1` → `CleanedRemittancePanelV2` additively.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): auxiliary columns (regime/event/A1-R-bridge/release-day) per Rev-1.1 spec; hash extension`.

### Task 14: Quarterly corridor reconstruction sensitivity column

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/corridor_reconstruction.py`
- Create: `contracts/data/banrep_corridor_quarterly.csv` (committed fixture)
- Modify: `contracts/scripts/cleaning.py` (additive)
- Test: `contracts/scripts/tests/remittance/test_corridor_reconstruction.py`

- [ ] **Step 0 (Rev-2 pre-flight — RC F1):** Before writing any test, the Data Engineer reads Basco & Ojeda-Joya 2024 *Borrador* 1273 in full and produces a one-page reconstruction recipe as a scratch note at `contracts/.scratch/2026-04-20-remittance-corridor-reconstruction-recipe.md`. Borrador 1273 is cited as a *caveat* and *anchor* for corridor reconstruction in the Rev-1 spec — it is **not** a documented step-by-step replication target. If the recipe cannot be derived from the paper's published tables, Task 14 produces an **empty-placeholder sensitivity row** documenting the gap (with `corridor_reconstruction_available: false` in the downstream gate verdict) rather than silently omitting the row. Decide go/no-go at the end of Step 0.
- [ ] **Step 1: Write the failing test.** If Step-0 recipe is derivable: assert `reconstruct_us_corridor_quarterly(monthly_aggregate_df, mpr_quarterly_breakdown_df) → DataFrame` exists with a reconstruction-SE column propagated for downstream gate pricing. If Step-0 recipe is NOT derivable: assert the empty-placeholder path emits the `corridor_reconstruction_available: false` marker and a non-null reason-string pointing to the Step-0 scratch note.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** (reconstruction or empty-placeholder path per Step 0 outcome). Extend `CleanedRemittancePanelV2` → `CleanedRemittancePanelV3` with the corridor column (or placeholder null column with provenance flag). Include the corridor-column hash in the extended decision-hash per the Task-12 seam.
- [ ] **Step 4: Run and confirm pass** against a committed MPR-derived fixture (or the empty-placeholder path).
- [ ] **Step 5: Commit** with message `feat(remittance): quarterly corridor reconstruction sensitivity column (or documented-gap placeholder) + hash extension`.

### Task 15: Panel validation + integration smoke test

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/tests/remittance/test_panel_integration.py`

- [ ] **Step 1: Write the failing test.** Run `load_cleaned_remittance_panel(conn)` end-to-end (loading the `CleanedRemittancePanelV3` that Tasks 9/13/14 build additively). Assert all columns present, row count = 947 (unchanged from Rev-4, verified by Reality Checker against `nb1_panel_fingerprint.json:188` and memory), decision-hash = Rev-4-hash-extended with primary-RHS + aux columns + corridor column (or null-corridor marker), no nulls in primary or auxiliary columns over sample window, primary-column mean and std are in expected ranges (from the Rev-1 spec).
- [ ] **Step 2: Run the test.** First run will likely reveal integration bugs.
- [ ] **Step 3: Fix integration issues.** Dispatch Data Engineer to address any panel-load failures; do not modify Rev-4 artifacts. **Escalation branch (Rev-2, PM F1):** if the failure implicates a Rev-4 decision (e.g., date-column join semantics, a Rev-4 decision-hash invariant changes shape, or a Rev-4 artifact must be re-emitted), **halt** and escalate to the user for scope-expansion approval rather than silently amending Rev-4. The scripts-only allow-list (rule #4) already forbids this; the escalation path is the documented exit.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `test(remittance): end-to-end panel-load integration test`.

---

## Phase 3 — Notebook Authoring (X-Trio Discipline)

**Phase-3 protocol note (Rev-2, PM F5):** Every Phase-3 authoring task's "nbconvert-execute" step means `subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", <committed-path>, "--ExecutePreprocessor.timeout=1800"])` against the committed notebook path (not a `/tmp` copy), with returncode=0 asserted inline in that task. This is additive to Task 25's end-to-end nbconvert guards; the inline per-task execution catches errors trio-locally so Task 25 is a final belt-and-braces layer, not the first-responder.

**Intra-phase review gates (Rev-2, PM B1):** After each notebook is fully authored, a three-way implementation-review trio (Code Reviewer + Reality Checker + Senior Developer, per memory `feedback_implementation_review_agents.md`) executes against just that notebook before the next notebook begins. These gates are Tasks 18a (after NB1), 21c (after NB2), 24c (after NB3). Rev-4's successful shipping relied on this pattern; omitting it risks systemic defects compounding across notebooks.

### Task 16: NB1 §1 — Panel load + fingerprint (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb1_panel_fingerprint.json`
- Test: `contracts/scripts/tests/remittance/test_nb1_remittance_section1.py`

- [ ] **Step 1: Write the failing test.** Assert NB1 §1 exists with the standard X-trio layout; fingerprint JSON is emitted atomically with extended decision-hash, Rev-4-base-hash, timestamp, package versions, auxiliary-column hashes.
- [ ] **Step 2:** Dispatch Analytics Reporter with the X-trio protocol. The agent authors trio 1 (panel load) + trio 2 (fingerprint emission) and HALTs after each trio. Foreground reviews between trios.
- [ ] **Step 3: nbconvert-execute** the committed NB1 notebook inline (see Phase-3 protocol note); assert returncode=0.
- [ ] **Step 4: Run the failing test;** confirm it passes.
- [ ] **Step 5: Commit** with message `feat(remittance): NB1 §1 panel load + fingerprint emission`.

### Task 17a: NB1 §2 — Decisions 1-4 (Analytics Reporter, X-trio; Rev-2 split per PM B3)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb1_remittance_section2_d1_4.py`

**Rev-2 context:** Rev-1 Task 17 packed 12 decisions into a single subagent dispatch. Rev-4 precedent (CPI Tasks 9-12) split decisions across 4 tasks of ~3 decisions each. At ~5 min foreground review per trio, 12 trios = ~60 min serial — violates subagent-driven-development atomicity. Splitting into 17a/17b/17c × 4 decisions each keeps each task under the 30-min granularity ceiling.

- [ ] **Step 1: Write the failing test.** Assert NB1 §2 contains `LockedDecisions`-equivalent entries for Decisions 1-4 (sample window preserved; LHS unchanged; primary RHS = remittance-AR(1) surprise; 6 controls preserved — whichever four the Rev-1 spec assigns to this batch). Each decision has a 4-part citation block.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio protocol — 4 trios (one per decision). HALT after each.
- [ ] **Step 3: nbconvert-execute** the committed NB1 notebook inline (see Phase-3 protocol note above); assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB1 §2 — Decisions 1-4 for remittance-surprise`.

### Task 17b: NB1 §2 — Decisions 5-8 (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb1_remittance_section2_d5_8.py`

- [ ] **Step 1: Write the failing test.** Assert NB1 §2 contains Decisions 5-8 entries with 4-part citation blocks.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio — 4 trios. HALT after each.
- [ ] **Step 3: nbconvert-execute** the committed NB1 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB1 §2 — Decisions 5-8 for remittance-surprise`.

### Task 17c: NB1 §2 — Decisions 9-12 (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb1_remittance_section2_d9_12.py`

- [ ] **Step 1: Write the failing test.** Assert NB1 §2 contains Decisions 9-12 entries (frequency, collinearity, stationarity, plus whichever fourth decision the Rev-1 spec assigns) with 4-part citation blocks. Cross-assert the full §2 contains exactly 12 decisions (Tasks 17a + 17b + 17c summed).
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio — 4 trios. HALT after each.
- [ ] **Step 3: nbconvert-execute** the committed NB1 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB1 §2 — Decisions 9-12 for remittance-surprise; full 12-decision block complete`.

### Task 18: NB1 §3-5 — EDA plots + diagnostics + panel validation (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Create: figures under `contracts/notebooks/fx_vol_remittance_surprise/Colombia/figures/`
- Test: `contracts/scripts/tests/remittance/test_nb1_remittance_section3_5.py`

- [ ] **Step 1: Write the failing test.** Assert NB1 §3 (univariate EDA of remittance surprise + LHS + controls), §4 (bivariate co-movement diagnostics), §5 (stationarity tests per Rev-1 spec — ADF / KPSS / Phillips-Perron as pre-committed). Each section has ≥2 trios; each code cell executes; each figure is emitted to `figures/`.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; HALT between trios.
- [ ] **Step 3: nbconvert-execute** the committed NB1 notebook inline (see Phase-3 protocol note); assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB1 §3-5 — EDA + diagnostics + stationarity tests`.

### Task 18a: Three-way review gate — NB1 complete (Rev-2 insert per PM B1)

**Subagent:** three parallel dispatches (Code Reviewer + Reality Checker + Senior Developer) per memory rule `feedback_implementation_review_agents.md`.

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-nb1-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb1-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb1-review-senior-developer.md`

- [ ] **Step 1:** Dispatch three reviewers in parallel against just NB1 (Tasks 16–18) + all NB1-derived artifacts (`nb1_panel_fingerprint.json`, §3-5 figures, Tasks 16-18 tests). Per-reviewer focus (Rev-2, CR F4):
  - **Code Reviewer:** file-path correctness, additive-only extension of Rev-4 `cleaning.py`, test coverage of NB1 §1 and §2 (12 decisions split across 17a/17b/17c), decision-hash invariant preservation.
  - **Reality Checker:** verify panel row_count = 947, verify each of the 12 Decisions' citation blocks points to existing references, audit stationarity-test outcomes against the Rev-1 spec's pre-committed expectations.
  - **Senior Developer:** architectural coherence — is NB1 a clean consumer of the `cleaning.py` extension layer, or are there private imports bypassing the intended API? Are the V1/V2/V3 dataclass extensions orthogonal and additive?
  None of the three reviewers sees the others' reports.
- [ ] **Step 2:** Verify all three reports landed.
- [ ] **Step 3:** Log verdicts + itemize findings.
- [ ] **Step 4:** If BLOCK findings: dispatch Data Engineer to fix (subject to the 3-cycle cap in rule #13); re-dispatch the offending reviewer. Do not begin Task 19 until NB1 gate PASSes.
- [ ] **Step 5: Commit** the three scratch reports with message `review(remittance): NB1 three-way review gate (Tasks 16-18)`.

### Task 19: NB2 §1-3 — OLS ladder (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/02_estimation.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb2_remittance_section1_3.py`

- [ ] **Step 1: Write the failing test.** Assert NB2 §1 (sample + panel verification), §2 (pre-fit diagnostics per Rev-1 spec), §3 (OLS ladder — base, +primary-surprise, +controls, final model) exist and execute cleanly. Final model coefficient β̂_remittance with HAC SE (kernel + bandwidth from Rev-1 spec) is emitted.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; one trio per sub-step.
- [ ] **Step 3: nbconvert-execute** the committed NB2 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB2 §1-3 — OLS ladder with HAC SE per Rev-1 spec`.

### Task 20: NB2 §4-6 — GARCH(1,1)-X co-primary (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/02_estimation.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb2_remittance_section4_6.py`

- [ ] **Step 1: Write the failing test.** Assert §4 (GARCH baseline fit), §5 (GARCH(1,1)-X with remittance-surprise in mean- OR variance-equation per Rev-1 spec), §6 (convergence diagnostics + GARCH-X β̂_remittance emission). `scipy` L-BFGS-B custom likelihood per Rev-4 pattern.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio. Flag convergence-instability handling per Rev-1 spec.
- [ ] **Step 3: nbconvert-execute** the committed NB2 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB2 §4-6 — GARCH(1,1)-X co-primary per Rev-1 spec`.

### Task 21a: `build_payload_remittance` helper (Data Engineer; Rev-2 split per CR N5 / PM F2)

**Subagent:** Data Engineer

**Files:**
- Modify: `contracts/scripts/nb2_serialize.py` (additive — `build_payload_remittance`)
- Test: `contracts/scripts/tests/remittance/test_nb2_serialize_remittance.py`

**Rev-2 context:** Rev-1 Task 21 packed Analytics Reporter notebook authoring AND a Data Engineer helper into one task, violating the "one subagent per task" rule (CR N5, PM F2). Splitting 21a (DE helper) and 21b/c (AR notebook + gate) preserves subagent atomicity and lets the helper test run before the notebook depends on it.

- [ ] **Step 1: Write the failing test.** Assert `build_payload_remittance(point_results, reconcile_results, full_fit) → PayloadRemittance` exists, produces a JSON-serializable dict for `nb2_params_point.json` + `nb2_reconcile.json`, preserves atomic-emission semantics (stage→fsync→rename) shared with the Rev-4 helper.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** as an additive function in `nb2_serialize.py`. Do not modify the existing Rev-4 CPI-payload function.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): nb2_serialize.build_payload_remittance helper`.

### Task 21b: NB2 §7-9 — T3b gate + reconciliation + economic magnitude (Analytics Reporter, X-trio; Rev-2 split per PM B3)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/02_estimation.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb2_remittance_section7_9.py`

- [ ] **Step 1: Write the failing test.** Assert §7 (T3b gate per Rev-1 spec — one-sided or two-sided per sign prior; MDES check), §8 (reconciliation rule per Rev-1 spec — directional or numerical-intersection between OLS and GARCH-X; the rule chosen under heteroskedasticity per Rev-1 row 9 of the resolution matrix), §9 (economic-magnitude interpretation — basis-points-of-vol magnitude translated at the Rev-1 spec's pricing anchors). Each section has trio discipline.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; HALT between trios.
- [ ] **Step 3: nbconvert-execute** the committed NB2 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB2 §7-9 — T3b gate + reconciliation + economic magnitude`.

### Task 21c: NB2 §10-12 — sensitivity rows + atomic emission (Analytics Reporter, X-trio; Rev-2 split per PM B3)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/02_estimation.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb2_params_point.json`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb2_reconcile.json`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb2_params_full.pkl`
- Test: `contracts/scripts/tests/remittance/test_nb2_remittance_section10_12.py`

- [ ] **Step 1: Write the failing test.** Assert §10 (alternate-LHS sensitivity row; Dec-Jan seasonality check — both specified by the Rev-1 spec resolution matrix; these are pre-registered sensitivities, not post-hoc spotlights), §11 (quarterly corridor reconstruction sensitivity — or the documented-gap placeholder path from Task 14), §12 (atomic JSON + pickle emission via `nb2_serialize.build_payload_remittance` from Task 21a). Integration-verify atomic emission (stage→fsync→rename). All three artifact files are emitted byte-deterministically.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; HALT between trios.
- [ ] **Step 3: nbconvert-execute** the committed NB2 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB2 §10-12 — sensitivity rows + atomic emission`.

### Task 21d: Three-way review gate — NB2 complete (Rev-2 insert per PM B1)

**Subagent:** three parallel dispatches (Code Reviewer + Reality Checker + Senior Developer).

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-nb2-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb2-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb2-review-senior-developer.md`

- [ ] **Step 1:** Dispatch three reviewers in parallel against NB2 (Tasks 19–21c) + NB2 artifacts. Per-reviewer focus:
  - **Code Reviewer:** additive-only `nb2_serialize.py` extension, HAC kernel/bandwidth correctness per Rev-1 spec row, GARCH-X convergence handling, atomic-emission test coverage.
  - **Reality Checker:** verify each cell's citation block references existing papers/data; independently recompute β̂_remittance point estimate (even roughly) to spot a missing multiplier or sign-flip; confirm reconciliation rule matches Rev-1 spec row 9.
  - **Senior Developer:** architectural coherence — is the GARCH-X fit layered on top of the OLS ladder correctly? Is the atomic emission separable from the authoring layer so Task 24a/b can reuse the payload unchanged?
- [ ] **Step 2:** Verify all three reports landed.
- [ ] **Step 3:** Log verdicts + itemize findings.
- [ ] **Step 4:** If BLOCK findings: dispatch Data Engineer to fix (3-cycle cap); re-dispatch the offending reviewer. Do not begin Task 22a until NB2 gate PASSes.
- [ ] **Step 5: Commit** the three scratch reports with message `review(remittance): NB2 three-way review gate (Tasks 19-21c)`.

### Task 22a: NB3 §1-3 — pre-flight + T1 exogeneity + T2 Levene + T3a replay (Analytics Reporter, X-trio; Rev-2 split per PM B3)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb3_remittance_section1_3.py`

**Rev-2 context:** Rev-1 Task 22 packed 7 tests into one subagent dispatch (7 trios serial). Splitting into 22a (T1-T3a) + 22b (T3b + T4-T7) keeps each under the atomicity ceiling and matches Rev-4's narrower packing.

- [ ] **Step 1 (Rev-2 tightened — CR F3):** Write the failing test. Assert NB3 §1 (pre-flight — unpack NB2 PKL into bare-name variables per the Rev-4 silent-test-pass lesson; assert each bare-name variable is of the expected type and non-NaN), §2 (T1 exogeneity), §3 (T2 Levene + T3a stat-significance replay). Each test emits a verdict dict compatible with `gate_aggregate.build_gate_verdict`. **CR F3 fix — numerical assertions mandatory:** for each test the test spec asserts at least one numerical field, not only that the verdict-dict key exists:
  - T1: F-statistic is finite, > 0, and within ±0.1 of an independently pre-computed expected value from the Rev-1 spec's pre-fit-diagnostic block.
  - T2: Levene p-value lies in `[0.0, 1.0]` and is within ±0.05 of the independently pre-computed expected value.
  - T3a: |t-statistic| > 0 and the reported two-sided p-value matches within ±1e-6 a scipy-computed recomputation from the emitted β̂ and SE.
  These assertions guard against silent-test-pass pattern #1 — "test asserts a dict exists, not that its values are numerically correct." This pattern caused 3 of 5 CPI silent-test-pass incidents.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; one trio per test (pre-flight, T1, T2, T3a) = 4 trios.
- [ ] **Step 3: nbconvert-execute** the committed NB3 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB3 §1-3 — pre-flight + T1 + T2 + T3a with numerical assertions`.

### Task 22b: NB3 §4-6 — T3b gate replay + T4-T7 (Analytics Reporter, X-trio; Rev-2 split per PM B3)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb3_remittance_section4_6.py`

- [ ] **Step 1 (Rev-2 tightened — CR F3):** Write the failing test. Assert NB3 §4 (T3b gate replay — the NB2 gate-stat is re-evaluated in NB3 and matches within tolerance; each arm of the gate has a numerical MDES-pass or MDES-fail flag with the underlying ES value asserted), §5 (T4 residual autocorrelation — Ljung-Box Q statistic is finite, >0, with p-value in `[0, 1]` and a reported lag matching Rev-1 spec), §6 (T5 Normal/robustness — Jarque-Bera stat finite, ≥0, p-value in `[0, 1]`; T6 heteroscedasticity — White/Breusch-Pagan stat finite, ≥0, p-value in `[0, 1]`; T7 specification-curve — at least N=k curves emitted where k is the Rev-1 spec's committed count, each with a numerical β̂ value). No test may assert merely "key exists"; each assertion must pin at least one numerical field.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; one trio per test (T3b, T4, T5+T6, T7) = 4 trios.
- [ ] **Step 3: nbconvert-execute** the committed NB3 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB3 §4-6 — T3b replay + T4-T7 with numerical assertions`.

### Task 23: NB3 §7-9 — Forest plot + anti-fishing halt + material-mover spotlight (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/figures/forest_plot.png`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb3_forest.json` (Rev-2 add per CR F1; design-doc §Deliverables item 5)
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb3_sensitivity_table.json` (Rev-2 add per CR F1; design-doc §Deliverables item 5)
- Test: `contracts/scripts/tests/remittance/test_nb3_remittance_section7_9.py`

- [ ] **Step 1 (Rev 3.1 amended — CR-B1): Write the failing test.** Assert §7 (all primary + sensitivity rows: primary, alternate-LHS, **A1-R-bridge** (BanRep-quarterly AR(1)-surprise rebased-to-weekly — the validation-row S14 from Rev-1.1 §6; renamed from the obsolete "A1-R monthly" per CR-B1 since the monthly cadence is no longer a pre-committed sensitivity under Rev 3.1), release-day-only, pre/post-2015 Quandt-Andrews-windowed, Petro-Trump event-dummied, quarterly corridor reconstruction — or the documented-gap placeholder if Task 14 Step 0 decided no-recipe; plus any Rev-1.1-spec additions). Assert `nb3_forest.json` is emitted with one row per sensitivity (β̂, SE, CI bounds, row label). Assert `nb3_sensitivity_table.json` is emitted with the same rows plus gate-pass/fail flags per row. Assert §8 (forest-plot render at `figures/forest_plot.png`; rows sorted per Rev-1.1 spec). Assert §9 (anti-fishing halt condition — material-mover §9 spotlight is emitted ONLY if primary T3b PASSes; otherwise §9 cells emit empty placeholders referencing the design doc's anti-fishing framing and the §8 sensitivity-row pre-registration; A1-R-bridge + release-day-excluded rows are preserved as pre-registered sensitivities, not post-hoc rescue claims).
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio.
- [ ] **Step 3: nbconvert-execute** the committed NB3 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.** Verify `nb3_forest.json` + `nb3_sensitivity_table.json` are byte-deterministic across two runs.
- [ ] **Step 5: Commit** with message `feat(remittance): NB3 §7-9 — forest + anti-fishing halt + nb3_forest.json + nb3_sensitivity_table.json`.

### Task 24a: NB3 §10 — Gate aggregation (Data Engineer helper + Analytics Reporter cells; Rev-2 split per CR N5 / PM F2)

**Subagent:** Data Engineer (for `build_gate_verdict_remittance` + `render_readme` helper extension); then Analytics Reporter (for notebook §10 cells). Split across sub-dispatches per the "one-subagent-per-task" rule; the DE work and its test complete before AR authors cells against the function.

**Files:**
- Modify: `contracts/scripts/gate_aggregate.py` (additive — `build_gate_verdict_remittance`)
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/gate_verdict_remittance.json`
- Test: `contracts/scripts/tests/remittance/test_gate_aggregate_remittance.py`
- Test: `contracts/scripts/tests/remittance/test_nb3_remittance_section10.py`

- [ ] **Step 1a (DE sub-task):** Write the failing test asserting `gate_aggregate.build_gate_verdict_remittance(nb2_point, nb2_reconcile, nb3_tests, nb3_sensitivity) → dict` exists; produces a verdict payload with fields (primary-verdict, reconciliation-outcome, T1-T7 sub-verdicts, sensitivity rows, anti-fishing-halt flag); uses atomic emission via `write_gate_verdict_atomic`.
- [ ] **Step 1b (DE sub-task):** Run test, implement helper, confirm pass.
- [ ] **Step 2: Write the NB3 §10 failing test.** Assert §10 calls the Task-24a helper and emits `gate_verdict_remittance.json` byte-identically across two runs (determinism check; matches Rev-4 `_FINGERPRINT_NONDET_KEYS` allowlist pattern).
- [ ] **Step 3:** Dispatch Analytics Reporter with X-trio for §10 cells.
- [ ] **Step 4: nbconvert-execute** the committed NB3 notebook inline; assert returncode=0. Verify `gate_verdict_remittance.json` is emitted.
- [ ] **Step 5: Run test and confirm pass** (byte-identical across two runs).
- [ ] **Step 6: Commit** with message `feat(remittance): NB3 §10 — build_gate_verdict_remittance helper + gate emission`.

### Task 24b: NB3 §11 — README auto-render (Data Engineer helper + Analytics Reporter cells; Rev-2 split per CR N5 / PM F2)

**Subagent:** Data Engineer (for `render_readme` remittance-template-selector extension); then Analytics Reporter (for notebook §11 cells).

**Files:**
- Modify: `contracts/scripts/render_readme.py` (additive — remittance template selector)
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/README.md` (overwrites Task 8 placeholder — verified non-placeholder by Task 24b test per PM N3)
- Test: `contracts/scripts/tests/remittance/test_render_readme_remittance.py`
- Test: `contracts/scripts/tests/remittance/test_nb3_remittance_section11.py`

- [ ] **Step 1a (DE sub-task):** Write the failing test asserting `render_readme(gate_verdict_remittance, template_path=..._readme_template.md.j2)` returns a byte-identical rendered string across two calls (pure function; Jinja2 deterministic).
- [ ] **Step 1b (DE sub-task):** Run test, implement template-selector extension, confirm pass.
- [ ] **Step 2: Write the NB3 §11 failing test.** Assert §11 invokes `render_readme` and writes `README.md` byte-identically across two runs. Add a PM-N3 guard: assert the rendered README does NOT contain the Task-8 placeholder sentinel (e.g., assert the rendered README length > a minimum threshold and does not contain a known placeholder substring).
- [ ] **Step 3:** Dispatch Analytics Reporter with X-trio for §11 cells.
- [ ] **Step 4: nbconvert-execute** the committed NB3 notebook inline; assert returncode=0.
- [ ] **Step 5: Run test and confirm pass.**
- [ ] **Step 6: Commit** with message `feat(remittance): NB3 §11 — README auto-render; verified non-placeholder`.

### Task 24c: Three-way review gate — NB3 complete (Rev-2 insert per PM B1)

**Subagent:** three parallel dispatches (Code Reviewer + Reality Checker + Senior Developer).

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-nb3-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb3-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb3-review-senior-developer.md`

- [ ] **Step 1:** Dispatch three reviewers in parallel against NB3 (Tasks 22a–24b) + NB3 artifacts. Per-reviewer focus:
  - **Code Reviewer:** numerical-assertion coverage in Tasks 22a/22b (no test asserts only dict-key existence); CR F1 deliverables (`nb3_forest.json`, `nb3_sensitivity_table.json`) present; atomic emission of `gate_verdict_remittance.json`; template-selector cleanly additive.
  - **Reality Checker:** audit the forest-plot row labels against the Rev-1 spec's pre-committed sensitivity list (no rows silently added, none silently dropped); verify A1-R renaming is consistent everywhere; audit the anti-fishing halt behavior under the (hypothetical) T3b-FAIL branch.
  - **Senior Developer:** architectural coherence — is the gate-aggregation layer a pure function of NB2+NB3 artifacts? Is the README auto-render deterministic and reproducible from committed inputs only?
- [ ] **Step 2:** Verify all three reports landed.
- [ ] **Step 3:** Log verdicts + itemize findings.
- [ ] **Step 4:** If BLOCK findings: dispatch Data Engineer to fix (3-cycle cap); re-dispatch the offending reviewer. Do not begin Task 25 until NB3 gate PASSes.
- [ ] **Step 5: Commit** the three scratch reports with message `review(remittance): NB3 three-way review gate (Tasks 22a-24b)`.

---

## Phase 4 — Integration Tests + Review + Close

### Task 25: Three nbconvert-execute integration-test guards

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/tests/remittance/test_nb1_remittance_end_to_end_execution.py`
- Create: `contracts/scripts/tests/remittance/test_nb2_remittance_end_to_end_execution.py`
- Create: `contracts/scripts/tests/remittance/test_nb3_remittance_end_to_end_execution.py`

- [ ] **Step 1: Write three failing tests.** Each test `subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute", <path>, "--output", "/tmp/<name>", "--ExecutePreprocessor.timeout=1800"])` and asserts returncode=0. Tests are guards against the silent-test-pass pattern (5 instances catalogued in the CPI exercise per memory `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md:68`). They are not skipped in CI. **Rev-2 explicit coverage per RC F3:** the three nbconvert guards catch pattern-1 (whole-notebook-execution failure) directly. The other four patterns are covered as follows: pattern-2 (prose-vs-code drift) caught by the CR F3 numerical assertions in Tasks 22a/22b; pattern-3 (zero-assertion tests) forbidden by rule #1 strict-TDD + each Phase-3 task's Step-1 test-assertion list; pattern-4 (silent-column-drift) caught by Task 12/13/14 decision-hash-extension invariants; pattern-5 (non-deterministic emission) caught by Task 26 byte-identical regression. Task 25's own test-spec header block enumerates these five patterns so a future reader can verdict whether coverage remains complete.
- [ ] **Step 2: Run and confirm failure** (tests will fail initially because `/tmp/<name>` doesn't exist or execution has a bug).
- [ ] **Step 3: Fix any end-to-end execution bug** that surfaces. Do not suppress the test.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `test(remittance): 3-notebook nbconvert-execute integration guards`.

### Task 26: End-to-end regression test (determinism + idempotency)

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/tests/remittance/test_end_to_end_determinism.py`

- [ ] **Step 1: Write the failing test.** Run all three notebooks end-to-end twice, store all output artifacts in two scratch dirs, diff them. Assert byte-identical except for a frozen allowlist of non-deterministic keys (e.g., `{"generated_at"}` per Rev-4 `_FINGERPRINT_NONDET_KEYS` pattern). Include the Rev-4 mutation-test pattern: inject 5 known-wrong changes and assert the regression test catches each.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Iterate until determinism holds** for all artifacts.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `test(remittance): end-to-end determinism + mutation-catch gauntlet`.

### Task 27: Model QA Specialist econometric calibration review

**Subagent:** Model QA Specialist

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-impl-review-model-qa.md`

- [ ] **Step 1:** Dispatch Model QA Specialist with the three notebooks (post-Phase-3), the Rev-1 spec, and the gate_verdict_remittance.json as inputs. Audit: did the implementation faithfully execute the Rev-1 spec's 13 mandatory choices? Are econometric calibrations (HAC bandwidth, GARCH-X convergence, MDES verification, Quandt-Andrews test) correctly executed?
- [ ] **Step 2:** Verify report landed.
- [ ] **Step 3:** Log verdict + findings.
- [ ] **Step 4:** If BLOCK findings: dispatch Data Engineer to fix; re-dispatch Model QA for re-verification. Iterate to PASS, bounded by rule #13's 3-cycle cap — after the third failed Model QA cycle, halt and escalate to the user.
- [ ] **Step 5: Commit** with message `review(remittance): Model QA implementation review (pass N)`.

### Task 28: Three-way implementation review (Code Reviewer + Reality Checker + Senior Developer)

**Subagent:** three parallel dispatches per memory rule `feedback_implementation_review_agents.md`.

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-impl-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-20-remittance-impl-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-20-remittance-impl-review-senior-developer.md`

- [ ] **Step 1:** Dispatch three reviewers in parallel against the full Phase-A.0 implementation (notebooks + scripts + tests + artifacts). Each receives the design doc + Rev-1 spec + fix-log + full implementation tree. None knows about the others. **Per-reviewer focus (Rev-2, CR F4):**
  - **Code Reviewer:** file-path and dependency correctness across all 38 tasks; allow-list compliance (rule #4 + its memory-file exception); scripts-only scope respected; no Solidity / foundry.toml / src/ touched; test-file naming convention honored (rule #11 with its infra-test exception); atomic-emission discipline on all JSON/pickle artifacts; decision-hash invariant holds end-to-end; all per-notebook intra-phase gates (Tasks 18a, 21d, 24c) left no unresolved BLOCKs.
  - **Reality Checker:** every cited reference in every notebook's 4-part citation blocks points to an existing paper/corpus file; every numerical assertion in tests can be independently recomputed by hand or a small scipy call; the Rev-4 frozen-panel invariants (row-count 947, base decision-hash) hold byte-exact after the remittance extension; anti-fishing framing language in notebook headers and commit messages is consistent; the gate verdict (PASS/FAIL) and its supporting statistics are internally consistent (β̂, SE, CI, p-value all agree arithmetically).
  - **Senior Developer:** architectural coherence — is the remittance pipeline a clean additive layer atop Rev-4, or are there private imports or hidden coupling? Is the V1/V2/V3 dataclass extension pattern applied consistently? Does the gate-aggregation + README-render layer reproduce byte-identically from committed inputs only? Could a Phase-A.1 downstream exercise reuse the remittance extension pattern without copy-paste?
- [ ] **Step 2:** Verify all three reports landed.
- [ ] **Step 3:** Log verdicts + itemize findings across severity tiers.
- [ ] **Step 4: Commit** the three scratch reports with message `review(remittance): 3-way implementation review reports`.

### Task 29: Data Engineer applies impl-review fixes

**Subagent:** Data Engineer (per memory rule `feedback_implementation_review_agents.md`: Data Engineer fixes)

**Files:**
- Modify: as-needed per review findings

- [ ] **Step 1:** Dispatch Data Engineer with all three review reports. Apply BLOCK fixes first, FLAGs second, NITs if time permits.
- [ ] **Step 2:** Re-run the full test suite + nbconvert integration guards + determinism test.
- [ ] **Step 3:** If any BLOCK was deferred, halt and re-invoke the specific reviewer. Bound by rule #13's 3-cycle cap across Task 28 ↔ Task 29 loops; after the third failed cycle, halt and escalate.
- [ ] **Step 4: Commit** with message `fix(remittance): apply 3-way implementation review fixes`.

### Task 30a: Completion memory (Technical Writer; Rev-2 split per PM F6)

**Subagent:** Technical Writer

**Files:**
- Create: `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_remittance_surprise_exercise_complete.md` (Rev-4 precedent: CPI completion memory lives at same path prefix per `project_fx_vol_cpi_notebook_complete.md`; allow-list exception codified in rule #4 Rev-2 extension)

- [ ] **Step 1 (Rev 3.1 amended — CR-B1):** Dispatch Technical Writer to author the completion memory containing: verdict digest (PASS or FAIL), β̂_remittance + SE + CI, all test verdicts (T1-T7), reconciliation outcome, all sensitivity-row outcomes (primary, alternate-LHS, **A1-R-bridge** (BanRep-quarterly AR(1)-surprise rebased-to-weekly, replacing the obsolete "A1-R monthly" per Rev 3.1 CR-B1), release-day-only, pre/post-2015 Quandt-Andrews, Petro-Trump event-dummied, quarterly corridor reconstruction or its documented-gap placeholder), anti-fishing framing re-asserted (Phase-A.0 is a distinct pre-commitment on the remittance external-inflow channel via the on-chain COPM+cCOP rail, not a rescue of the CPI-FAIL; the Rev-3 methodology escalation is pre-commitment-preserving per Rev-3.1 Rule 14), pointers to all 11 artifacts (`nb1_panel_fingerprint.json`, `nb2_params_point.json`, `nb2_reconcile.json`, `nb2_params_full.pkl`, `nb3_forest.json`, `nb3_sensitivity_table.json`, `gate_verdict_remittance.json`, `README.md`, `forest_plot.png`, plus MPR-source provenance, bridge-validation scratch note from Task 11.C, and corridor-reconstruction-recipe scratch notes), lessons learned, Phase-A.1 go/no-go recommendation conditional on verdict.
- [ ] **Step 2:** Verify the memory file landed at the expected path.
- [ ] **Step 3: Commit** with message `docs(remittance): Phase-A.0 completion memory authored`.

### Task 30b: MEMORY.md index + design-doc completed-status footer (Technical Writer; Rev-2 split per PM F6)

**Subagent:** Technical Writer

**Files:**
- Modify: `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/MEMORY.md` (one-line pointer to Task 30a memory; precedent: `project_fx_vol_cpi_notebook_complete.md` is indexed similarly)
- Modify: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md` (append "completed YYYY-MM-DD / verdict: {PASS|FAIL}" status footer; precedent: Rev-4 design doc footer pattern)

- [ ] **Step 1:** Technical Writer appends the completion pointer to `MEMORY.md` (one line, matching the Rev-4 CPI pointer format).
- [ ] **Step 2:** Technical Writer appends the completed-status footer to the design doc.
- [ ] **Step 3: Commit** with message `docs(remittance): MEMORY.md index + design-doc completed-status footer`.

### Task 30c: Final test run + push (Rev-2 split per PM F6 and N4)

**Subagent:** Data Engineer (final test run); foreground (push).

**Files:** no file modifications; verification + push only.

- [ ] **Step 1:** Data Engineer runs the full test + integration + determinism suite one final time to confirm clean state.
- [ ] **Step 2 (Rev-2 disambiguated — PM N4):** Verify clean `git status` on branch `phase0-vb-mvp`; push the branch to `origin` (JMSBPP remote) per memory rule `feedback_push_origin_not_upstream.md` — **NOT** `upstream` (wvs-finance). "Merge phase0-vb-mvp status" in the Rev-1 plan was ambiguous; Rev-2 clarifies that nothing is merged into `main` at this task — the branch is pushed and the user decides merge/PR disposition separately per memory rule `feedback_no_merge_without_approval.md`.
- [ ] **Step 3: Commit** (if test-run or push produced trivial follow-on edits) with message `chore(remittance): Phase-A.0 complete, verdict={PASS|FAIL}, push to origin` (CR N2 — replaced the non-conventional `close(...)` prefix with `chore(...)`).

---

## Spec-coverage self-check (Rev-2 updated for split task numbers)

The design doc's Phase-0 mandatory-inputs enumeration has 13 items. Each is covered by Task 1's 13-input resolution matrix (Rev-2 tightened) and operationally by downstream tasks:

- Sign prior → Task 1 Step 4 + Task 21b §7 (T3b gate, one-sided or two-sided per sign prior)
- MDES → Task 1 Step 4 + Task 11.D Step 1 (Rev-1.1 §4.5 re-computation at N=95) + Task 22b §4 (numerical MDES assertion in T3b replay) + Task 27 (Model QA audit)
- Alternate-LHS sensitivity → Task 21c §10 (emission) + Task 23 §7 (forest-plot row)
- HAC kernel → Task 19 §3 + Task 21d (NB2 review-gate CR focus) + Task 27
- Andrews bandwidth → Task 19 §3 + Task 11.D Step 1 (Rev-1.1 §12 row 5 patch at N=95)
- Interpolation side → Rev 3.1 superseded for primary X (Task 11.D §12 row 6 marks as "no longer applies"); retained for validation-row S14 quarterly AR(1) path via Task 10
- AR order → Task 10 (validation-row S14 quarterly path only under Rev 3.1); Task 11.D Step 1 §12 row 7 patch
- Vintage discipline → Task 11 (quarterly BanRep MPR-vintage-date column, now demoted to validation-row S14) + Task 11.A (daily on-chain no-revision vintage for primary X) + Task 11.D Step 1 §12 row 8 patch
- Reconciliation rule under heteroskedasticity → Task 21b §8 (directional or numerical-intersection per Rev-1.1 spec row 9)
- Quandt-Andrews → Task 23 §7 (pre/post-2015 row)
- GARCH parametrization → Task 20 §5
- Dec-Jan seasonality → Task 21c §10 (pre-registered sensitivity row alongside alternate-LHS)
- Event-study co-primary → Task 23 §7-9 (Petro-Trump row, anti-fishing-halt-conditional spotlight)

All 13 covered across Phases 0/1.5/2/3/4. Phase 1.5 (Tasks 11.D Step 1) is the Rev-3.1 entry point for rows 5/6/7/8 re-resolution under the daily-native primary X.

**Task 21c packing note (Rev-2, CR N4 addressed):** Rev-1 §9 originally hosted both alternate-LHS and Dec-Jan seasonality in the same notebook section. Rev-2 lifts both into Task 21c §10 (sensitivity-rows batch) with separate trios so each is an independently auditable entry. The forest-plot row labels in Task 23 §7 then render these as distinct entries.

Anti-fishing framing appears in Task 8 (notebook headers), Task 11.D (Rev-1.1 supersedes-banner explicitly frames the methodology escalation as data-reality-driven, not null-result-driven), Task 11.E (three-way review of the Rev-1.1 patch guards against back-door unreviewed-spec execution), Tasks 22b-23 (NB3 §9 halt condition), Task 30a (completion memory). Three-way reviews at Phase 0 (Tasks 2-4 spec review CR+RC+TW per `feedback_three_way_review.md`), Phase 1.5 (Task 11.E spec-patch review CR+RC+TW, Rev-3 insert; Rev-3.1 cycle-cap-bounded per Rule 13 + Task 11.E Step 3 boundary definition), Phase 3 intra-phase gates (Tasks 18a, 21d, 24c CR+RC+SD per `feedback_implementation_review_agents.md`, Rev-2 inserts), Phase 4 (Tasks 27-28 impl review).

Additive-only scope: every Phase-1 task is additive to Rev-4 pipeline; Phase-1.5 tasks are additive to Phase-1 (new scripts, new data fixtures, new notebook 0B, spec-patch only to already-additive spec file); decision-hash extension preserves Rev-4 hash (Task 12 test) and extends in Tasks 13 (aux columns including `a1r_quarterly_rebase_bridge` per Rev-3.1 rename) + 14 (corridor column or placeholder).

**Total task count (Rev-3.1): 46.**
- Phase 0: Tasks 1-5 (5 tasks; unchanged from Rev-1)
- Phase 1: Tasks 6-10 (5 tasks; unchanged)
- Phase 1.5 (Rev-3.1 promoted per PM-F2): Tasks 11.A, 11.B, 11.C, 11.D, 11.E (**5 tasks**; Rev-3 daily-native middle-plan inserts, promoted out of Phase 2 in Rev-3.1 to form a standalone Data-Bridge sub-phase with clean gate boundaries)
- Phase 2: Tasks 11 (post-execution history), 12, 13, 14, 15 (**5 tasks**; Rev-2 shape restored after Rev-3.1 Phase-1.5 promotion)
- Phase 3: Tasks 16, 17a, 17b, 17c, 18, 18a, 19, 20, 21a, 21b, 21c, 21d, 22a, 22b, 23, 24a, 24b, 24c (18 tasks; unchanged from Rev-2)
- Phase 4: Tasks 25, 26, 27, 28, 29, 30a, 30b, 30c (8 tasks; unchanged from Rev-2)

Sum check: 5 + 5 + 5 + 5 + 18 + 8 = 46. Same task count as Rev-3; only the phase-boundary rearrangement changed in Rev-3.1.

**Growth narrative (Rev 3.1 re-baselined per PM-N1):** Rev-4 CPI shipped with 33 tasks as counted in `CLAUDE.md` (36 with letter-suffix expansions shown in the plan body). Rev-2 remittance was 41 tasks. Rev-3 remittance is 46 tasks — 5 tasks higher than Rev-2, reflecting the Rev-3 methodology-escalation insert (Tasks 11.A–11.E responding to the Task-11 quarterly-only BanRep finding). Rev-3.1 preserves the 46-task count and rearranges the phase structure for clarity. Growth vs Rev-1's nominal 30 reflects: (a) 3 intra-phase review gates (Rev-4 parity per PM B1), (b) split-for-atomicity of four over-packed authoring tasks (PM B3), (c) helper+author separation for dual-subagent tasks (CR N5 / PM F2), (d) completion unbundling (PM F6), (e) Rev-3 daily-native methodology-escalation insert (5 tasks).

---

## Execution handoff

**Plan complete and saved to `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. This matches the Rev-4 CPI plan's successful execution pattern.
2. **Inline Execution** — Execute tasks in this session using `executing-plans`, batch with checkpoints.

Which approach?
