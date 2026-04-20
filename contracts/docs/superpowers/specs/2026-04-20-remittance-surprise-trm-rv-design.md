---
title: Abrigo Phase-A.0 — Remittance-surprise → TRM realized-vol structural exercise (design)
date: 2026-04-20
author: Claude (brainstorm session 2026-04-20)
status: DESIGN (pre-plan)
supersedes: none
related:
  - Rev-4 CPI spec: contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md
  - CPI implementation plan: contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md
  - CPI completion record (FAIL verdict): contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json
  - Y×X matrix memory: ~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_colombia_yx_matrix.md
---

# Phase-A.0 — Remittance-surprise → TRM realized-vol (Colombia) — design

## Purpose

The Rev-4 CPI-surprise → TRM realized-vol exercise (2026-04-17 … 2026-04-19) closed with a T3b-FAIL verdict (β̂_CPI = −0.000685, 90% CI contains zero; see `project_fx_vol_cpi_notebook_complete.md` "Primary OLS Column 6" block for the β̂ and CI, whose authoritative value does NOT appear in the verdict-booleans-only `gate_verdict.json`). A three-agent Y×X matrix exploration on 2026-04-20 ranked candidate next-primary macro observables. Intersecting the research-utility rank with the free-tier data-feasibility rank (Dune MCP, Alchemy RPC, public BanRep / DANE / FRED sources) produced, under the specific rank-aggregation method documented in the brainstorm session (sum of research + feasibility ranks), the winner: **remittance-flow surprise → TRM weekly realized volatility** (row A1). Per `project_colombia_yx_matrix.md`, A1 appears in all three option sets (α/β/γ) presented to the user, but it is the chosen *off-chain calibration anchor* — not a unanimous winner across alternative aggregation methods. A3 (US Hispanic-employment surprise) and B1 (COPM mint/burn) remain triangulated companions, deferred to Phase-A.1.

This exercise asks: does the BanRep-published Colombian remittance-inflow AR(1) surprise carry detectable information content for COP/USD weekly realized volatility, under the identical Rev-4 structural-econometrics discipline, on the identical frozen 947-obs weekly panel, with one new *primary* right-hand-side column added plus pre-registered auxiliary columns for the sensitivity sweep?

The exercise is Phase-A.0 of a larger program. Phase-A.1 (broader Y×X engine registry over triangulated cells) and Phase-B (hypothetical-pool simulator) are outlined below but their detailed designs are deferred to future specs.

## Scope and non-goals

### In scope

- One structural-econometric row: primary RHS = remittance-flow AR(1) residual (aggregate monthly inflow; see §Scientific question for US-corridor pivot rationale), LHS = TRM RV^{1/3} weekly (unchanged from Rev-4).
- **One new primary RHS column** in the frozen Colombia weekly panel. Controls remain the six Rev-4 controls: VIX, DXY, EMBI Colombia, Fed Funds, Oil (WTI/Brent), Banrep Repo. Decision-hash is extended, not replaced.
- **Pre-registered auxiliary columns for the sensitivity sweep**: (a) pre/post-2015 regime dummy (Venezuelan-migration onset), (b) Petro-Trump Jan-2025 event dummy, (c) A1 monthly-cadence re-aggregation panel derived from the same primary source, (d) release-day indicator. These are pre-committed in the Rev-1 spec and emitted as distinct columns; they do not constitute new primary regressors.
- A fresh pre-committed one-sided T3b-style gate on β̂_remittance, with HAC SE and GARCH(1,1)-X as co-primary reconciliation. Kernel, bandwidth rule, and interpolation side are deferred to the Rev-1 spec per the Phase-0 mandatory-inputs enumeration below.
- Three notebooks mirroring the CPI layout (EDA / estimation / tests-and-sensitivity), sharing the existing `scripts/` pipeline with additive changes only.
- A `gate_verdict_remittance.json` emission parallel to the CPI `gate_verdict.json`, and an auto-rendered `README.md` for the remittance exercise directory.
- Pre-committed anti-fishing discipline identical to Rev-4: the spec locks gate, controls, SE method, reconciliation rule, and sensitivity sweep before any β̂ is computed.

### Path allow-list (extends memory rule via Rev-4 precedent)

`feedback_scripts_only_scope.md` strictly enumerates `contracts/scripts/*.py`, `contracts/scripts/tests/*.py`, `contracts/data/`, `contracts/.gitignore`, `contracts/requirements.txt`. The Rev-4 CPI exercise established de-facto precedent for extending this allow-list to include `contracts/notebooks/fx_vol_*/` and `contracts/docs/superpowers/specs/`; see `project_fx_vol_cpi_notebook_complete.md` and `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` as the superseding precedent. Phase-A.0 inherits this amended allow-list explicitly. The complete set of paths this exercise may touch:

- `contracts/scripts/*.py` and `contracts/scripts/tests/*.py` (additive)
- `contracts/data/` (note: memory says `data/`, not `research/data/`; Phase-A.0 uses `contracts/data/` to stay memory-aligned; any reference to `research/data/` below is corrected to `data/`)
- `contracts/notebooks/fx_vol_remittance_surprise/Colombia/` (new directory, per Rev-4 precedent)
- `contracts/docs/superpowers/specs/` (Rev-1 spec, per Rev-4 precedent)
- `contracts/docs/superpowers/plans/` (implementation plan, per Rev-4 precedent)
- `contracts/.gitignore`
- `contracts/requirements.txt` (additive only if a new pin is required)

### Explicitly out of scope

- No engine-registry refactor. Approach C dataclass candidate-registry is deferred to Phase-A.1, conditional on Phase-A.0 producing a non-null verdict that justifies scaling.
- No on-chain data ingestion. COPM mint/burn, cCOP volume, cCOP net directional flow are deferred to Phase-A.1 once short-sample inference methodology is developed.
- No pool-design-space simulator. Phase-B is outlined, not designed.
- No Solidity, no contract changes, no changes to foundry.toml. The scripts-only precedent above bounds the file surface.
- No changes to the frozen CPI artifacts. The Rev-4 `gate_verdict.json` = FAIL stays as-published. This exercise does not re-run the CPI regression and does not reframe the CPI-FAIL as "rescued."

## Scientific question (precise)

Let `ΔlogRem_m` = monthly log-change in Colombian **aggregate** remittance inflows (BanRep monthly aggregate published via public channels — see data-source note below). Let `ε^Rem_m` = residual from an AR(1) fit of `ΔlogRem_m` on pre-sample data (vintage discipline — real-time vintage vs. current-vintage — to be fixed by the Rev-1 spec per the Phase-0 mandatory inputs enumeration), interpolated to weekly via a Friday-anchored step-function (interpolation side — LOCF vs next-week-fill — also resolved in the Rev-1 spec).

**Data-source note (supersedes any earlier phrasing).** Per `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COLOMBIAN_ECONOMY_CRYPTO.md` §1.2 (lines 113–115) and Agent 3's ranked-candidate report, BanRep publishes **monthly family-remittance aggregates** as a downloadable time series; **corridor breakdowns** (US / Spain / other) appear in Monetary Policy Reports and special blog posts but NOT as a single monthly corridor CSV. The primary RHS therefore operates on the aggregate monthly inflow, not a US-corridor subset. The US corridor dominates the aggregate in practice (≈53% of flow per `COLOMBIAN_ECONOMY_CRYPTO.md` §1.2), so the aggregate series is a high-signal proxy for US-corridor dynamics, but it is not identical to them. The Rev-1 spec pre-commits a **quarterly corridor reconstruction** sensitivity row (from Monetary Policy Report tables plus the Basco & Ojeda-Joya 2024 Borrador 1273 methodology) as a secondary robustness check; the reconstruction-SE term is priced into the gate only in that secondary row, not in the primary.

Let `RV^{1/3}_w` = weekly realized volatility of TRM (frozen from Rev-4 panel, unchanged).

Pre-committed OLS specification:
- LHS: `RV^{1/3}_w`
- Primary RHS: `ε^Rem_w`
- Controls: VIX_w, DXY_w, EMBI_w, FedFunds_w, Oil_w, Repo_w (unchanged from Rev-4)
- HAC Newey-West SE with Andrews 1991 optimal bandwidth

Pre-committed one-sided T3b gate on β̂_Rem:
- Null: β̂_Rem ≤ 0 (no positive information content)
- Alternative: β̂_Rem > 0 (remittance surprise raises TRM vol)
- Gate rule: β̂_Rem − 1.28 · SE(β̂_Rem) > 0 (one-sided α = 0.10)

Pre-committed co-primary: GARCH(1,1)-X with `ε^Rem_w` in the mean equation (identical to the Rev-4 CPI GARCH-X convention via `scipy` L-BFGS-B custom likelihood). Reconciliation rule: directional concordance with OLS (sign agreement + CI-contains-zero agreement + significance concordance) — **implemented by importing** `from scripts.nb2_serialize import reconcile` rather than by re-implementation, which makes the additive-only claim testable against the Rev-4 codepath. Note: Agent 3's engine-integration sketch proposed dropping Oil and adding US BLS Hispanic-employment share as a control; the design preserves the Rev-4 six-control set verbatim to preserve the decision-hash and inheritance invariant. Any proposed deviation from Rev-4 controls is rejected at spec time unless justified in the Rev-1 spec with a preservation-of-Rev-4-hash argument.

Sensitivity sweep pre-registered at spec time: A1 monthly-cadence re-aggregation, A4 release-day-excluded weekly, release-day-only sub-sample, pre-/post-2015 subsample split (Venezuelan-migration regime onset), Petro-Trump Jan-2025 event-dummied subsample.

## Methodology inheritance from Rev-4

This exercise explicitly inherits the following Rev-4 artifacts verbatim:

- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb` — EDA-notebook layout, 12 Decisions structure, `LockedDecisions` frozen-dataclass pattern, panel-fingerprint emission
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/02_estimation.ipynb` — OLS ladder structure, GARCH-X build, T3b gate cell, reconciliation cell, atomic JSON emission pattern
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/03_tests_and_sensitivity.ipynb` — T1-T7 test scaffold, forest-plot construction, anti-fishing halt
- `contracts/scripts/cleaning.py` — panel-load wrapper, `load_cleaned_panel(conn) → CleanedPanel`, `_compute_decision_hash` helper
- `contracts/scripts/nb2_serialize.py` — build-payload, `reconcile()` directional-concordance, `write_all` atomic-emit, HandoffMetadata
- `contracts/scripts/gate_aggregate.py` — pure `build_gate_verdict(inputs) → dict` + `write_gate_verdict_atomic`
- `contracts/scripts/render_readme.py` — Jinja2 auto-render with byte-identical-CI diff-check

The Phase-A.0 exercise produces siblings of these files, co-located under `contracts/notebooks/fx_vol_remittance_surprise/Colombia/`, with minimal diffs: new RHS column in `LockedDecisions`, new surprise-constructor entry-point, new spec-hash input to `gate_aggregate`. No refactor of shared scripts; **additive-only changes**, discovered through the pre-registered diff cap.

## Pre-commitment discipline

Inherited from Rev-4 verbatim (see `feedback_no_code_in_specs_or_plans.md` memory — this design is 100% code-agnostic):

1. Spec hash is computed and committed to git before any β̂ is computed. The spec-hash commit SHA MUST be an ancestor of any commit introducing `estimates/nb2_params_point.json` or `nb2_params_full.pkl`; CI check enforces this via `git merge-base --is-ancestor`. Witness: no `estimates/nb2_params_point.json` or `nb2_params_full.pkl` exists in the tree at spec-commit time (replicates the de-facto Rev-4 witness).
2. Panel decision-hash from the frozen Colombia weekly panel is verified at load time; any deviation aborts.
3. Three-way spec review gate: **Code Reviewer + Reality Checker + Technical Writer** (per `feedback_three_way_review.md`) before any implementation task starts.
4. X-trio checkpoint discipline during notebook authoring (per `feedback_notebook_trio_checkpoint.md`): notebook-author agent HALTS after every `(why-markdown, code-cell, interpretation-markdown)` trio for human review.
5. 4-part decision-citation block before every test, decision, or spec choice (per `feedback_notebook_citation_block.md`): reference / why used / relevance to results / connection to simulator.
6. STRICT TDD (per `feedback_strict_tdd.md`): no implementation for a feature whose test hasn't been written and verified to fail first.
7. Specialized-agent dispatch per plan task (per `feedback_specialized_agents_per_task.md`): foreground orchestrates and verifies, never authors.
8. Implementation review agents (per `feedback_implementation_review_agents.md`): Code Reviewer + Reality Checker + Senior Developer; Data Engineer fixes.
9. Integration-test guard against silent-test-pass (per `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md`): `jupyter nbconvert --to notebook --execute` on each of the 3 notebooks as a standing test in `contracts/scripts/tests/`, preventing the 5-instance silent-test-pass pattern we catalogued in the CPI exercise.
10. Real-data-over-mocks (per `feedback_real_data_over_mocks.md`): tests hit the real frozen panel and cached fixtures derived from real BanRep/public-API pulls; mocks permitted only for HTTP transport errors that cannot be reproduced deterministically in CI.
11. Anti-fishing framing: this exercise is a DISTINCT pre-commitment on a different macro mechanism (remittance-inflow channel), NOT a rescue of the CPI FAIL. The distinction is asserted in the spec, in every notebook header, and in the `gate_verdict_remittance.json` emission. **Evidence that the remittance channel pre-dates the CPI FAIL**: `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/REMITTANCE_VOLATILITY_SWAP.md` has mtime 2026-04-02, seventeen days before the CPI FAIL verdict on 2026-04-19; the pre-committed-but-unrun Reiss-Wolak spec at `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/specs/INCOME_SETTLEMENT/2026-04-02-ccop-cop-usd-flow-response.md` is also a pre-FAIL artifact. See also the dedicated §"Why this is not a rescue of CPI-FAIL" below.

## Why this is not a rescue of CPI-FAIL

Three structural separators, co-located here so a reviewer can verify them in one place:

1. **Distinct pre-registered hypothesis**. CPI exercise asked: does CPI AR(1) surprise raise weekly TRM realized vol through an inflation-expectations → FX-repricing channel? Phase-A.0 asks: does remittance AR(1) surprise raise weekly TRM realized vol through an external-inflow → parity-deviation channel (Dallas Fed / IMF GIV mechanism). These are different transmission chains, not alternative operationalizations of the same channel.
2. **Distinct null**. CPI null was `β̂_CPI ≤ 0` on inflation surprise; Phase-A.0 null is `β̂_Rem ≤ 0` on a separately constructed remittance surprise, with the economic-sign prior deferred to the Rev-1 spec (see Phase-0 mandatory inputs below — a two-sided gate is on the table).
3. **Distinct sensitivity sweep**. Phase-A.0 pre-registers pre/post-2015 (Venezuelan-migration regime), Petro-Trump Jan-2025 event dummy, and Dec-Jan seasonality — structural breaks that are *remittance-mechanism-specific* and do not appear in the CPI sweep.

**Provenance evidence**: the remittance channel was a candidate in the research corpus before the CPI exercise FAILED. `REMITTANCE_VOLATILITY_SWAP.md` mtime is 2026-04-02 (filesystem-verifiable); CPI FAIL was 2026-04-19; the remittance hypothesis is therefore not a post-hoc rescue. See also the pre-committed-but-unrun Reiss-Wolak spec dated 2026-04-02 at `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/specs/INCOME_SETTLEMENT/`.

## Mandatory inputs to the Phase-0 `structural-econometrics` skill call

The design doc deliberately does NOT resolve methodology; the Rev-1 spec does. The `structural-econometrics` skill, invoked in plan phase 0, MUST resolve each of the items below in the Rev-1 spec it produces. The three-way spec review MUST verify all items are resolved with justification; any item left open BLOCKS spec acceptance.

**Gate and power**

1. **Economic sign prior for gate direction**. Justify one-sided vs two-sided. Remittance inflows are plausibly volatility-reducing (stabilizing income) or volatility-increasing (stress-response inflow during depreciation episodes). The one-sided rule halves the rejection region; adopting it requires a pre-registered transmission-mechanism argument isolating the sign, or the gate is two-sided.
2. **Pre-committed minimum detectable effect size (MDES)**. Compute ex-ante at the chosen α, effective-N under HAC, and target power (e.g. 80%). Document as an MDES value in SD-units of residualized RV^{1/3}. Pre-register the interpretive rule that `FAIL` with `|β̂| > MDES/2` is reported as *inconclusive* in `gate_verdict_remittance.json`, not as rejection.
3. **Alternate-LHS sensitivity row**. Re-using the Rev-4 LHS (RV^{1/3}) without an LHS-power check cannot distinguish "remittance has no effect on TRM vol" from "TRM RV^{1/3} is a low-power outcome on this panel." Pre-register at least one alternate LHS ∈ {log-RV, GARCH(1,1)-filtered residual vol, Parkinson intraday-range vol} as a reported sensitivity row; do not gate on it.

**Standard-error and interpolation**

4. **HAC kernel choice**. Bartlett / Quadratic-Spectral / Parzen. Andrews 1991 gives different optimal bandwidths per kernel; the kernel must be named.
5. **Bandwidth rule**. Andrews 1991 plug-in (with AR(1) pre-whitening, explicit) or Newey-West 1994 data-driven. Pick one.
6. **Step-interpolation side**. Last-observation-carried-forward vs next-observation-back-filled. State whether the release-day falls on the week of release or the following week.

**Surprise construction**

7. **AR order selection**. AR(1) vs seasonal AR vs SARIMA(1,0,0)(1,0,0)_12 vs BIC selection over `p ∈ {1,2,3,12}`. Dallas Fed / IDB literature documents 12-month Colombian remittance seasonality; plain AR(1) likely leaves seasonal autocorrelation in the residual.
8. **Vintage discipline**. Real-time vs current-vintage, with training-set vintage frozen at spec-commit date and residual computed on first-release values only (per Orphanides 2001 surprise-identification practice). Covers the `revision-resistant` ambiguity flagged in §Risks #1.
9. **Structural-break test**. Quandt-Andrews unknown-break-point on pre-sample data; if estimated break is within ±12 months of 2015, keep the 2015 dummy; otherwise use the data-driven break.

**Reconciliation and co-primary**

10. **Reconciliation rule under heteroskedasticity**. Rev-4's `reconcile()` uses sign + CI-contains-zero + significance concordance; under GARCH-X-corrected heteroskedasticity, OLS and GARCH can legitimately disagree on significance while agreeing on sign. Pre-register a numerical-intersection secondary reconciliation ("both 90% CIs must exclude zero on the same side") as an auxiliary check.
11. **GARCH-X parametrization**. Mean-equation vs variance-equation vs GARCH-in-mean. The design's default is mean-equation (inherited from Rev-4); a variance-equation robustness row should be pre-registered under the stress-response hypothesis.
12. **Dec-Jan seasonality sensitivity**. Colombian remittance has quincena + December-holiday surges. Pre-register a Dec-Jan-excluded sensitivity row to distinguish seasonality-driven signal from structural surprise-content.
13. **Event-study co-primary** (per Agent 3 §4 #1 and Basco-Ojeda-Joya 2024 caveat). The cited literature studies remittance *cyclicality*, not *volatility causation*; the vol-causation claim is novel. Pre-register an event-study co-primary around BanRep release-date windows with its own threshold so that the primary gate is not the only gate on a novel identification claim.

The Rev-1 spec emitted by the `structural-econometrics` skill MUST enumerate its resolution for each of 1–13 with citations. The three-way spec review explicitly audits this enumeration.

## Deliverables

1. Rev-1 spec under `contracts/docs/superpowers/specs/`, emitted by the `structural-econometrics` skill in plan phase 0. Proposed filename: `2026-04-2X-remittance-surprise-trm-rv-spec.md` (where `X` is the spec-commit date). This lets `writing-plans` emit the filename deterministically without a round-trip.
2. Three notebooks under `contracts/notebooks/fx_vol_remittance_surprise/Colombia/`: `01_data_eda.ipynb`, `02_estimation.ipynb`, `03_tests_and_sensitivity.ipynb`.
3. Panel-fingerprint JSON under `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb1_panel_fingerprint.json` — extends the Rev-4 decision-hash with the new remittance column.
4. Estimation artifacts: `nb2_params_point.json`, `nb2_reconcile.json`.
5. Sensitivity artifacts: `nb3_forest.json`, `nb3_sensitivity_table.json`.
6. Gate verdict: `gate_verdict_remittance.json` — parallel to Rev-4 `gate_verdict.json`.
7. Auto-rendered `README.md` for the exercise directory (byte-identical-CI-checked).
8. Integration tests under `contracts/scripts/tests/remittance/test_nb{1,2,3}_end_to_end_execution.py` (nbconvert --execute per notebook). The subdirectory pattern (`tests/remittance/...`) is chosen deliberately to avoid collision with the existing `tests/test_nb{1,2,3}_end_to_end_execution.py` CPI tests; renaming the frozen CPI tests is out of scope (it would break the frozen-artifact discipline). Each integration test must affirmatively exclude the five silent-test-pass patterns catalogued in `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md` (tests that pass with zero assertions, tests that import without executing the guard, etc.); silent-test-pass exclusion is a named success criterion, not a blanket assertion.
9. Closing memory update in `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/` (file name assigned at completion time) with verdict digest + pointers; index entry added to `MEMORY.md`.

## Implementation constraints (for writing-plans to pick up)

The implementation plan produced by `writing-plans` MUST include the following as first-class structural elements:

### Plan phase 0 — structural-econometrics skill dispatch

First phase of the implementation plan invokes the `structural-econometrics` skill to derive a formal Rev-1 spec for the remittance-surprise → TRM-RV question. The skill's output is the pre-committed spec document referenced above. The plan's subsequent phases are gated on this spec being accepted via three-way review (Code Reviewer + Reality Checker + Technical Writer).

Rationale: the Rev-4 CPI exercise used this exact pattern (spec first, 12 reviewer passes, then implementation). Reusing the pattern preserves the pre-commitment discipline that vindicated the CPI FAIL verdict.

### Plan phase 1 — data ingestion (scripts-only)

Scope bounded by the amended allow-list in §Scope (no duplication of the memory rule here). Acquires the BanRep monthly **aggregate** remittance series (not US-corridor; see §Scientific question data-source note) via public BanRep CSV download or `datos.gov.co` Socrata endpoint; step-interpolates to Friday-anchored weekly (interpolation side per Rev-1 spec); AR(1) surprise constructor (AR order per Rev-1 spec); merges into a new panel fingerprint that extends the Rev-4 decision-hash without invalidating it. The decision-hash extension is enforced by `cleaning.py._compute_decision_hash`: any inadvertent mutation of existing columns aborts the panel-load step.

### Plan phase 2 — notebook authoring with X-trio checkpoints

Three notebooks mirror the CPI layout. Each notebook is authored by a specialized subagent (Analytics Reporter per memory) with MANDATORY HALT after every (why-md, code-cell, interpretation-md) trio for human review. No bulk authoring. Notebook 1 = EDA + panel fingerprint extension. Notebook 2 = OLS ladder + GARCH-X + T3b gate + reconciliation + atomic JSON emission. Notebook 3 = T1-T7 tests + forest plot + sensitivity sweep + gate aggregation.

### Plan phase 3 — strategic agent dispatch after spec acceptance

After the Rev-1 spec is accepted, each plan task dispatches a specialized subagent per `feedback_specialized_agents_per_task.md`:

- Data Engineer: panel extension + surprise constructor
- Analytics Reporter: notebook authoring (with X-trio discipline)
- Code Reviewer + Reality Checker + Technical Writer: three-way spec review
- Code Reviewer + Reality Checker + Senior Developer: three-way implementation review
- Data Engineer: fixes from review
- Model QA Specialist: GARCH-X parametrization, HAC kernel and bandwidth, MDES computation, alternate-LHS sensitivity, and the full Phase-0 mandatory-inputs audit (items 1–13 in §Mandatory inputs above). Included unconditionally; not hedged.

Foreground orchestrates + verifies; never authors.

### Plan phase 4 — integration tests + three-way review + close

Integration tests per the 3-notebook guard, three-way implementation review, atomic commit with completion-memory update. Any silent-test-pass instance (as catalogued in the CPI exercise reviewer-lessons memory) aborts the phase.

## Phase-A.1 and Phase-B outline

### Phase-A.1 (conditional on Phase-A.0 non-null verdict)

If Phase-A.0 produces β̂_Rem with CI excluding zero (PASS), Phase-A.1 builds the Approach C engine — typed frozen-dataclass candidate registry in `contracts/scripts/fx_vol_engine/` — and registers the remaining triangulated / high-ranked cells from the Y×X matrix: at minimum B1 (COPM mint/burn → Y₃), A3 (US HispEmp → Y₃), and B3 (cCOP net-direction → Y₈) as Phase-A.1 rows. Engine architecture per `project_colombia_yx_matrix.md` memory: `DataSubstrate` enum branches pipeline between off-chain-weekly and on-chain-daily-aggregated-weekly rows.

If Phase-A.0 returns a FAIL verdict, Phase-A.1 is deferred; the FAIL is published with the same anti-fishing discipline as the CPI FAIL, and the broader matrix is re-examined for the next iteration candidate.

### Phase-B (pool-design-space simulator)

Phase-B takes Phase-A outputs (β̂, σ̂, HAC-SE, sensitivity rows from any PASS row) and calibrates a hypothetical `cCOP/X` pool simulator that reproduces the identified channel under ideal conditions. Output: `pool_feasibility_<candidate>.json`. Detailed design deferred.

### Phase-C (pool construction)

Out of scope entirely. Downstream milestone conditional on Phase-B simulations.

## Risks and caveats

1. **Revision-vintage risk**. BanRep remittance data is revised up to 3 months post-initial release. Real-time vintages must be used for surprise construction, not current-vintage values. Flagged as a plan-phase-1 blocker if real-time vintages are not accessible on free tier.
2. **Sample-overlap caveat**. 18-year weekly panel supports the exercise in principle, but monthly→weekly step-interpolation introduces autocorrelation-inflated DOF. HAC Newey-West SE is non-negotiable; effective N drops toward ~200–250.
3. **Regime change 2015**. Venezuelan-migration onset (2015-2022) affects receiving-household composition; a Quandt-Andrews structural-break test is mandatory with pre-/post-2015 subsample dummies.
4. **Petro-Trump Jan 2025 episode**. Littio self-reported 100%+ account growth in 48 hours (per `OFFCHAIN_COP_BEHAVIOR.md` §1 L17; source is a Littio self-report relayed via Colombia-One reporting, not a primary dataset). This is a pre-sample structural event. Pre-register an event-dummy in the sensitivity sweep. Context: `COPM_MINTEO_DEEP_DIVE.md` §1.5 documents 200K Colombians using Littio overall, of whom ~100K use COPM via Littio at ≈$200M/mo COPM volume.
5. **CPI-FAIL bias / framing discipline**. Switching primary to remittance-surprise MUST NOT be framed as a rescue. The distinction is: CPI-surprise tested inflation-channel → FX-vol causation; remittance-surprise tests a different causal mechanism (external-inflow channel → parity-deviation → FX-vol). Every notebook header, every commit message, and the completion memory file must assert this distinction explicitly.
6. **Silent-test-pass risk**. 5 instances caught in the CPI exercise. Phase-A.0 installs the 3-integration-test guard (nbconvert --execute per notebook) from day one.
7. **Decision-hash drift risk**. Adding new columns to the frozen panel must extend the decision-hash, not replace it. Any inadvertent mutation of existing columns aborts the panel-load step via `scripts/cleaning.py::_compute_decision_hash`.
8. **Novelty-claim scoping**. The "no prior DeFi variance swap on stablecoin flow volume" precedent from `LITERATURE_PRECEDENTS.md` §9 applies to on-chain *flow-volume* variance. The Phase-A.0 LHS is TRM realized vol (an FX asset-price variance series), for which Ghysels-Sohn and Andersen-Bollerslev et al. FX-RV literature is rich. The defensible novelty claim is therefore scoped: "novel on Colombia-specific remittance-surprise → FX-vol identification," not "novel on FX-vol derivative." Notebook headers and completion memory assert this scoping explicitly.

## Success criteria

- Spec (Rev-1) accepted by three-way review with zero BLOCK-severity findings.
- Three notebooks pass integration tests (nbconvert --execute) in CI, no silent-test-pass instances.
- `gate_verdict_remittance.json` emitted atomically with full reconciliation payload.
- Auto-rendered README matches Jinja2-template byte-identically in CI.
- Completion memory file documents the verdict (PASS or FAIL) + pointers, with anti-fishing framing explicit.
- Total scope additive-only: no pre-existing file outside the amended allow-list in §Scope (`contracts/scripts/`, `contracts/data/`, `contracts/notebooks/fx_vol_remittance_surprise/`, `contracts/docs/superpowers/specs/`, `contracts/docs/superpowers/plans/`, `contracts/.gitignore`, `contracts/requirements.txt`) is modified.

## References

- Rev-4 CPI spec: `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md`
- Rev-4 CPI plan: `contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md`
- CPI completion record: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/README.md` and `estimates/gate_verdict.json`
- Y×X matrix: `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_colombia_yx_matrix.md`
- Five Y×X agent reports at `contracts/.scratch/2026-04-20-*.md`
- REMITTANCE_VOLATILITY_SWAP corpus: `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/`
- MACRO_RISKS framework: `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/`
- Project memories:
  - `feedback_no_code_in_specs_or_plans.md`
  - `feedback_three_way_review.md`
  - `feedback_strict_tdd.md`
  - `feedback_specialized_agents_per_task.md`
  - `feedback_implementation_review_agents.md`
  - `feedback_notebook_citation_block.md`
  - `feedback_notebook_trio_checkpoint.md`
  - `feedback_scripts_only_scope.md`
  - `feedback_real_data_over_mocks.md`
  - `project_fx_vol_cpi_notebook_complete.md`
  - `project_fx_vol_econ_complete_findings.md`
  - `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md`
  - `project_fx_vol_econ_gate_verdict_and_product_read.md`
  - `project_colombia_yx_matrix.md`
