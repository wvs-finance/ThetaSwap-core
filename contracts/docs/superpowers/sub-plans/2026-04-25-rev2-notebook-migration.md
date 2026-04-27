# Sub-plan — Task 11.O.NB-α: Rev-2 analytical work migrated to notebooks

**Authored.** 2026-04-26 (revised from 2026-04-25 directive; CORRECTIONS-applied 2026-04-26 post 3-way review NEEDS-WORK)
**Owner.** Foreground orchestrator (this thread)
**Upstream major plan.** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` — Rev-5.3.3 CORRECTIONS block §C, Task 11.O.NB-α (super-task body at lines 2170-2188)
**Track.** α (Rev-2 mean-β re-presentation in notebook form; convex-payoff testing is OUT OF SCOPE — that is Task 11.O.ζ-α / Rev-3)
**Status.** Authored — pending CR + RC re-review (TW peer PASS-w-adv stands) post-CORRECTIONS

---

## Trigger

The Rev-5.3.2 Phase 5b analytical deliverable (commit `799cbc280`, gate verdict **FAIL**, primary Row-1 `β̂_X_d = −2.7987e−8` with HAC(4) SE `1.4234e−8`, t-stat `−1.9662`, two-sided p `0.0493`, one-sided 90% lower bound `−4.6207e−8`, n = 76, window `[2024-09-27, 2026-03-13]`) currently ships as Python script form: `contracts/scripts/phase5_data_prep.py` + `phase5_analytics.py` + `run_phase5_analytics.py` plus 14 panel parquets at `contracts/.scratch/2026-04-25-task110-rev2-data/` and five markdown / JSON artifacts at `contracts/.scratch/2026-04-25-task110-rev2-analysis/` (`estimates.md`, `spec_tests.md`, `sensitivity.md`, `summary.md`, `gate_verdict.json`). The canonical values above are sourced byte-exact from `notebooks/abrigo_y3_x_d/estimates/gate_verdict.json` (byte-identical to `contracts/.scratch/2026-04-25-task110-rev2-analysis/gate_verdict.json`) and from the Phase 5a `manifest.md` row-summary table; any divergence in the executing notebooks is a BLOCKING defect.

The user directive (Rev-5.3.3 CORRECTIONS block §C) is to re-author this work in the canonical 3-notebook structure mirroring the FX-vol-CPI Colombia precedent (`contracts/notebooks/fx_vol_cpi_surprise/Colombia/` — three notebooks `01_data_eda.ipynb` + `02_estimation.ipynb` + `03_tests_and_sensitivity.ipynb`, supporting `env.py` + `references.bib` + `_nbconvert_template/` + `estimates/` + `figures/` + `pdf/`, README auto-rendered from `_readme_template.md.j2` fed by `gate_verdict.json`).

Foreground orchestration has already established the scaffolding stub at `notebooks/abrigo_y3_x_d/` (`env.py` copied with parents[3]→parents[2] depth adjustment pending; `references.bib` copied; `_nbconvert_template/` copied; `estimates/gate_verdict.json` already in place; `figures/` and `pdf/` empty). The remaining work is the three-notebook authoring + README auto-render, performed under STRICT `feedback_notebook_trio_checkpoint` HALT-every-trio discipline.

The mean-β FAIL is a *re-presentation* deliverable — no new estimates are introduced, no thresholds are tuned, no rows are added. The Rev-5.3.2 published 14-row matrix is the byte-exact upstream input. Convex-payoff insufficiency caveat (Rev-2 spec §11.A) is preserved verbatim at NB3 §5 because Rev-3 ζ-group is the separate stage where convex-payoff hypotheses get tested; this sub-plan does NOT pre-empt Rev-3.

---

## Pre-commitment (binding)

1. **Trio-checkpoint discipline (NON-NEGOTIABLE).** Every Analytics Reporter dispatch authors EXACTLY ONE trio: (why-markdown citation block, code-cell, interpretation-markdown). After each trio the agent HALTs; the orchestrator does NOT pre-emptively dispatch the next trio. The user reviews the rendered trio in-loop and explicitly approves before the next dispatch fires. This applies to every numbered sub-task below tagged `Analytics Reporter / 1 trio`. Bulk authoring across multiple trios in a single dispatch is FORBIDDEN per `feedback_notebook_trio_checkpoint`.

2. **4-part citation block discipline (NON-NEGOTIABLE).** Every test / decision / spec-choice in NB1 / NB2 / NB3 is preceded by the 4-part markdown block per `feedback_notebook_citation_block`: (1) reference (paper / textbook / project memory / prior decision); (2) why used (the analytical-method-fit rationale specific to this Rev-2 estimation context, NOT a generic textbook description); (3) relevance to results (what this method's output specifically contributes to the gate verdict / sensitivity row / specification test outcome); (4) connection to product (how this analytical choice connects to Abrigo's convex-instrument-pricing / inequality-hedge product purpose). The `references.bib` already copied from FX-vol-CPI Colombia is the citation-source-of-truth and may be extended (additions only; no deletions).

3. **No re-estimation drift.** NB1 / NB2 / NB3 reproduce the Rev-5.3.2 published estimates BYTE-EXACT against the Phase 5a parquets at `contracts/.scratch/2026-04-25-task110-rev2-data/` and the published `gate_verdict.json` at `contracts/.scratch/2026-04-25-task110-rev2-analysis/gate_verdict.json` (also copied to `notebooks/abrigo_y3_x_d/estimates/gate_verdict.json`). Any drift (rounding, library version skew, seed mismatch) is a BLOCKING defect; the post-notebook 3-way review will reject the deliverable.

4. **3-notebook structure precedent locked.** NB1 = data EDA + panel fingerprint; NB2 = primary estimation; NB3 = specification tests + sensitivity + gate verdict + forest plot + auto-rendered README. The FX-vol-CPI Colombia structure is the binding template at the section level; deviation from this structure requires CORRECTIONS-block discipline at the major-plan level, NOT a unilateral sub-plan choice.

5. **Convex-payoff insufficiency caveat preserved.** NB3 §5 reproduces the Rev-2 spec §11.A convex-payoff caveat verbatim (`project_abrigo_convex_instruments_inequality`). Mean-β alone is INSUFFICIENT for convex-payoff product pricing; NB3 §5 explicitly flags that Rev-3 ζ-group is the separate stage where quantile / GARCH-X / lower-tail / option-surface hypotheses get tested. This caveat is product-load-bearing and is NOT subject to editorial compression in NB3.

6. **Mento-native ONLY.** Per `project_abrigo_mento_native_only` and Rev-5.3.3 pre-commitment 6, the X_d in this Rev-2 re-presentation is the published Mento-native cCOP basket-volume series (address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606`). The cCOP-vs-COPM provenance audit (Task 11.P.MR-β.1) is a separate sub-plan and does NOT block this Rev-2 re-presentation; the Rev-2 published estimates remain byte-exact regardless of how the table-naming clarification lands.

7. **No code in this sub-plan body.** 100% code-agnostic per `feedback_no_code_in_specs_or_plans`. Backticked names, paths, and hashes are reference identifiers, not code.

8. **Push to origin (JMSBPP), NEVER upstream.** Per `feedback_push_origin_not_upstream`. Standard for all sub-plan execution.

---

## Sub-task list (31 entries — sub-task 17 split into 17.1-17.7; sub-task 24 split into 24a/24b per CR + TW advisories applied 2026-04-26)

The 31 sub-tasks below are organized into four blocks: NB1 trios (sub-tasks 1-7), NB2 trios (sub-tasks 8-15), NB3 trios (sub-tasks 16-23 with sub-task 17 expanded to 17.1-17.7), and README auto-render (sub-tasks 24a + 24b). Each numbered sub-task is the unit of agent dispatch; each `Analytics Reporter / 1 trio` sub-task HALTs after one (why-markdown, code-cell, interpretation-markdown) trio for explicit user review per pre-commitment 1.

The pre-fix-up count was 24; the post-fix-up count is 31 (24 base + 6 sub-tasks added by 17→17.1-17.7 split + 1 sub-task added by 24→24a/24b split). The original sub-task numbering (1-16, 18-23) is preserved; only sub-tasks 17 and 24 are decomposed.

The numbering preserves the section order each notebook will display when rendered to PDF.

---

### Block A — NB1: data EDA + panel fingerprint (sub-tasks 1-7)

**Notebook target.** `notebooks/abrigo_y3_x_d/01_data_eda.ipynb`
**Upstream input.** Phase 5a parquets at `contracts/.scratch/2026-04-25-task110-rev2-data/` (14 panel rows + `manifest.md` + `data_dictionary.md` + `validation.md` + `_audit_summary.json`); Rev-5.3.2 published DuckDB state.
**Downstream consumer.** NB2 (consumes panel-fingerprint JSON emitted by NB1 §1); NB3 (consumes Y₃ component decomposition emitted by NB1 §2 + outlier diagnostics emitted by NB1 §6).

#### Sub-task 1 — NB1 §0 — notebook header + panel-fingerprint validation

- **Deliverable.** NB1 §0 with: notebook title; one-sentence purpose statement (this notebook validates the Rev-5.3.2 panel construction; estimation lives in NB2; specification tests live in NB3); upstream input enumeration (14 parquets at `contracts/.scratch/2026-04-25-task110-rev2-data/`); downstream consumer enumeration (NB2 / NB3); panel-fingerprint validation (row counts per panel; `source_methodology` field with literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` for the primary; primary panel window `[2024-09-27, 2026-03-13]`; n = 76 weeks for the primary panel; pre-registered FAIL rows at n = 65 (Row 3 LOCF-tail-excluded) and n = 56 (Row 4 IMF-only); deferred-empty Rows 9 / 10 with n = 0 per Phase 5a `manifest.md` §1.2); pin to `gate_verdict.json` SHA at `notebooks/abrigo_y3_x_d/estimates/gate_verdict.json`.
- **Acceptance.** NB1 §0 renders cleanly; panel-fingerprint values match the Phase 5a `_audit_summary.json` byte-exact; the gate-verdict pin SHA is reproducible.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Entry-point trio for Block A. **BLOCKING upstream relation:** sub-task 1 cannot dispatch until the `env.py` `parents[3] → parents[2]` depth-adjustment fix lands at `notebooks/abrigo_y3_x_d/env.py`. That fix is OUT OF SCOPE for this sub-plan and is dispatched as a separate Senior Developer scaffolding-fix line under the major plan Task 11.O.NB-α body (lines 2170-2188); see §"Dispatch ordering" item 1 for the binding ordering. Without the fix, panel-load at NB1 §0 will resolve `_CONTRACTS_DIR` to the worktree root rather than `contracts/` and Block A will deadlock.

#### Sub-task 2 — NB1 §1 — panel-construction validation (1-2 trios)

- **Deliverable.** NB1 §1 with: per-row diagnostic for each of the 14 panels (`panel_row_01_primary` … `panel_row_14_wc_cpi_weights_sens`); column count; non-null fraction per column; date-coverage spans; cross-row consistency check (the 14 rows should differ ONLY by their published spec-row methodology). Emits a panel-fingerprint JSON to `notebooks/abrigo_y3_x_d/estimates/panel_fingerprint.json` consumed by NB2 §1 and NB3.
- **Acceptance.** Panel-fingerprint JSON contains: `n_rows_per_panel`, `column_count_per_panel`, `non_null_fraction_per_column`, `date_min_per_panel`, `date_max_per_panel`, `cross_row_consistency_flag` (boolean per-row pair). Byte-exact against `_audit_summary.json` where the fields overlap.
- **Subagent.** Analytics Reporter / 1-2 trios (allow 2 if one trio is per-row diagnostics and the second is the cross-row consistency aggregation; user gates the second trio).
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 1 closed.

#### Sub-task 3 — NB1 §2 — Y₃ component decomposition

- **Deliverable.** NB1 §2 with: per-country differential Y₃ component decomposition (CO / BR / EU; KE skipped per `source_methodology = y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`); equal-weight cross-country aggregation diagnostic; pre-registered WC-CPI weights (60/25/15) traceability per `project_y3_inequality_differential_design`. Citation block cites `project_y3_inequality_differential_design` + `project_abrigo_inequality_hedge_thesis`.
- **Acceptance.** Y₃ aggregate matches `panel_row_01_primary.parquet` Y₃ column byte-exact at the per-week level; per-country components sum to the equal-weight aggregate within floating-point tolerance; WC-CPI weight provenance traces back to the pre-registration.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 2 closed (panel-fingerprint locked).

#### Sub-task 4 — NB1 §3 — X_d distribution + diurnal pattern

- **Deliverable.** NB1 §3 with: weekly X_d distribution (histogram + kernel density estimate); UTC 13-17 NA-hours diurnal signature documentation per TR Finding 2 (Carbon DeFi protocol contracts ≈ 52% of cCOP Transfer events; ρ(X_d, fed_funds) = `−0.614`); flag that this signature is consistent with professional MM activity rather than retail hedge demand. Citation block cites TR Finding 2 from `contracts/.scratch/2026-04-25-mento-userbase-research.md` + `project_carbon_user_arb_partition_rule` + `project_carbon_defi_attribution_celo`.
- **Acceptance.** Histogram + KDE figures emit to `notebooks/abrigo_y3_x_d/figures/x_d_distribution.png`; diurnal signature plot emits to `notebooks/abrigo_y3_x_d/figures/x_d_diurnal_utc.png`; ρ(X_d, fed_funds) reproduces the `−0.614` value byte-exact from the published Phase 5b summary.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 2 closed.

#### Sub-task 5 — NB1 §4 — macro controls inventory

- **Deliverable.** NB1 §4 with: enumeration of the 6 macro controls (`fed_funds`, `bcb_selic`, `vix`, `dxy`, `mxef`, `intervention_dummy`); rationale for `intervention_dummy` substitution (the Rev-5.3.2 spec replaced one of the published-FX-vol-paper controls with this dummy because the source series was discontinued); per-control coverage span; per-control non-null fraction. Citation block cites Rev-2 spec §3 (substitution rationale narrative) + Phase 5a `data_dictionary.md` at `contracts/.scratch/2026-04-25-task110-rev2-data/data_dictionary.md` (variable definition + units + cleaning steps for `intervention_dummy`).
- **Acceptance.** Each control is documented with its DuckDB source, its window, and its substitution lineage where applicable; values match `panel_row_01_primary.parquet` columns byte-exact.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 2 closed.

#### Sub-task 6 — NB1 §5 — joint X_d × Y_3 weekly grid

- **Deliverable.** NB1 §5 with: joint coverage diagnostic for (X_d × Y₃) at the weekly level; reproduction of the published Rev-5.3.2 anchor counts (76 / 65 / 56 weeks under the three pre-registered intersection definitions); scatter plot with regression line annotation for visual sanity. Citation block cites Rev-2 spec §4 (window selection rationale) + `project_phase15_5_task_chain_post_rev531`.
- **Acceptance.** The 76 / 65 / 56 anchor counts reproduce byte-exact from the Phase 5a `_audit_summary.json`; scatter figure emits to `notebooks/abrigo_y3_x_d/figures/xd_y3_scatter.png`.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 3 closed (Y₃ decomposition locked) + sub-task 4 closed (X_d distribution locked).

#### Sub-task 7 — NB1 §6 — outlier and influence diagnostics

- **Deliverable.** NB1 §6 with: Cook's distance per observation; high-leverage flag at the 4/n threshold; the 2026-03-06 anchor week with Cook's D = 0.888 (Model QA surface from Phase 5b); per-observation residual diagnostics; flag that NO observation is dropped (the Rev-5.3.2 pre-commitment is to retain all 86 weeks); the 0.888 value is documented for downstream NB3 sensitivity inspection but does NOT trigger row exclusion. Citation block cites Cook (1977) `references.bib` entry + Belsley-Kuh-Welsch (1980) + `feedback_pathological_halt_anti_fishing_checkpoint` (no silent threshold tuning; the high-leverage observation stays in).
- **Acceptance.** Cook's D series matches the Phase 5b Model QA output byte-exact; 2026-03-06 row appears at the top of the high-leverage list; outlier table emits to a deterministic JSON at `notebooks/abrigo_y3_x_d/estimates/outlier_diagnostics.json` consumed by NB3.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 6 closed.

---

### Block B — NB2: primary estimation (sub-tasks 8-15)

**Notebook target.** `notebooks/abrigo_y3_x_d/02_estimation.ipynb`
**Upstream input.** NB1 panel-fingerprint JSON + 14 Phase 5a parquets + the Rev-5.3.2 published `gate_verdict.json`.
**Downstream consumer.** NB3 (consumes per-row estimates JSON emitted by NB2 §1-§6).

#### Sub-task 8 — NB2 §0 — notebook header + panel-load

- **Deliverable.** NB2 §0 with: notebook title; one-sentence purpose statement (this notebook executes the Rev-2 mean-β primary OLS+HAC(4) regression and the 14-row sensitivity ladder; specification tests live in NB3); upstream input enumeration (NB1 panel-fingerprint JSON + 14 parquets); downstream consumer enumeration (NB3); panel-load with the seed pin from `env.py`.
- **Acceptance.** Header renders; panel-load reads `panel_row_01_primary.parquet` byte-exact (n = 76 rows, window `[2024-09-27, 2026-03-13]`, columns match data dictionary).
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Block A closed (NB1 fully assembled and 3-way reviewed).

#### Sub-task 9 — NB2 §1 — primary OLS+HAC(4) Newey-West regression (1-2 trios)

- **Deliverable.** NB2 §1 with: pre-committed primary regression `Y₃ = α + β · X_d + γ' · controls + ε`; OLS point estimate; Newey-West HAC(4) standard error; one-sided T3b 90% lower bound (the gate-bearing quantity, NOT a two-sided CI); n = 76; gate-rule statement (one-sided T3b: PASS iff `β̂ − 1.28 · SE > 0`; FAIL otherwise — reproduced verbatim from Rev-2 spec §6 pre-registration); reproduction of canonical Rev-5.3.2 published Row-1 values BYTE-EXACT against `notebooks/abrigo_y3_x_d/estimates/gate_verdict.json` — point estimate `β̂_X_d = −2.7987050503705652e−08`, HAC(4) SE `1.4234226026833985e−08`, t-stat `−1.9661799981920483`, two-sided p `0.04927782209941108`, one-sided 90% lower bound `−4.6206859818053154e−08`, n = 76, window `[2024-09-27, 2026-03-13]`. Statistical power at primary n: `power(76, k=13, MDES_SD=0.40) = 0.8689` per the pre-registered Cohen f² formulation pin (`project_mdes_formulation_pin`). Emits per-row estimates JSON to `notebooks/abrigo_y3_x_d/estimates/primary_estimate.json`. Citation block cites Newey-West (1987) + the Rev-2 spec §3 functional form + `project_mdes_formulation_pin`.
- **Acceptance.** β̂ point estimate matches published `−2.7987e−8` byte-exact at the full JSON precision; HAC(4) SE matches `1.4234e−8` byte-exact; t-stat matches `−1.9662` byte-exact; two-sided p matches `0.0493`; one-sided 90% lower bound matches `−4.6207e−8`; n = 76; gate verdict emits FAIL.
- **Subagent.** Analytics Reporter / 1-2 trios (allow 2 if one trio is the regression run and the second is the gate-rule annotation; user gates the second).
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 8 closed.

#### Sub-task 10 — NB2 §2 — bootstrap reconciliation

- **Deliverable.** NB2 §2 with: Politis-Romano (1994) stationary block bootstrap on the primary OLS; B=10000 replications; bootstrap 90% CI for β̂_X_d; HAC-bootstrap agreement flag (overlap ≥50% per FX-vol-CPI Colombia precedent); reproduction of the Rev-5.3.2 published bootstrap CI byte-exact. Citation block cites Politis-Romano (1994) `references.bib` entry + the FX-vol-CPI Colombia NB2 §3.5 precedent + `project_fx_vol_econ_complete_findings` (HAC-bootstrap AGREEMENT rules out SE artifact).
- **Acceptance.** Bootstrap 90% CI reproduces the published Phase 5b row-2 sensitivity output byte-exact; agreement flag emits to `notebooks/abrigo_y3_x_d/estimates/bootstrap_recon.json`.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 9 closed.

#### Sub-task 11 — NB2 §3 — Student-t innovations refit (Row 11 sensitivity)

- **Deliverable.** NB2 §3 with: refit of the primary OLS under Student-t innovation assumption (degrees of freedom estimated from residuals); β̂_X_d under t-distribution; 90% CI; reproduction of `panel_row_11_student_t.parquet` published estimate byte-exact. Citation block cites the t-innovation rationale (heavy-tail robustness) + `panel_row_11` provenance.
- **Acceptance.** Row-11 estimate matches the published value at 4 significant digits.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 9 closed.

#### Sub-task 12 — NB2 §4 — HAC(12) bandwidth sensitivity (Row 12)

- **Deliverable.** NB2 §4 with: refit of the primary OLS with HAC bandwidth = 12 (the lag is widened from the Andrews-Newey rule-of-thumb HAC(4) to HAC(12)); β̂_X_d unchanged (point estimate is OLS); SE under HAC(12); 90% CI; reproduction of `panel_row_12_hac12_bandwidth.parquet` published estimate byte-exact. Citation block cites Newey-West (1987) bandwidth selection + Andrews (1991) automatic bandwidth + the Rev-2 spec sensitivity-row rationale.
- **Acceptance.** Row-12 estimate matches the published value byte-exact.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 9 closed.

#### Sub-task 13 — NB2 §5 — first-differenced sensitivity (Row 13)

- **Deliverable.** NB2 §5 with: first-difference refit `ΔY₃ = α + β · ΔX_d + γ' · Δcontrols + ε`; β̂ under first-differencing; HAC(4) SE on the differenced regression; 90% CI; reproduction of `panel_row_13_first_differenced.parquet` published estimate byte-exact. Citation block cites Stock-Watson (2007) Ch. 14 first-difference rationale + the Rev-2 spec sensitivity-row rationale (unit-root robustness check).
- **Acceptance.** Row-13 estimate matches the published value byte-exact.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 9 closed.

#### Sub-task 14 — NB2 §6 — WC-CPI weights sensitivity (Row 14)

- **Deliverable.** NB2 §6 with: refit of the primary OLS under three WC-CPI weight schemes (50/30/20; 60/25/15-primary; 70/20/10); per-scheme β̂_X_d; per-scheme 90% CI; reproduction of `panel_row_14_wc_cpi_weights_sens.parquet` published estimate byte-exact for the 50/30/20 and 70/20/10 alternatives (60/25/15 is the primary already in §1). Citation block cites `project_y3_inequality_differential_design` (pre-registration of 60/25/15) + the Rev-2 spec §11.B alternative-weights sensitivity rationale.
- **Acceptance.** Row-14 estimates for both alternative schemes match the published values byte-exact.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 9 closed.

#### Sub-task 15 — NB2 §7 — coefficient table + 90% CI forest plot (deterministic figure for README)

- **Deliverable.** NB2 §7 with: 14-row coefficient table (one row per `panel_row_NN`); per-row β̂ + HAC SE + 90% CI lower / upper + n; deterministic 14-row forest plot ordered by spec-row priority (primary at top, divider, then sensitivities); plot emits to `notebooks/abrigo_y3_x_d/figures/forest_plot.png` consumed by NB3 §7 and the auto-rendered README. Coefficient table emits to `notebooks/abrigo_y3_x_d/estimates/coef_table.json`. Citation block cites the FX-vol-CPI Colombia NB3 §8 forest-plot precedent + `feedback_pathological_halt_anti_fishing_checkpoint` (no silent row reordering).
- **Acceptance.** Forest plot reproduces the Rev-5.3.2 published 14-row plot at the visual level (CI whiskers correct, ordering correct, divider correct); JSON coefficient table is byte-exact against the published 14-row matrix.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-tasks 9-14 closed (all 14 rows estimated).

---

### Block C — NB3: specification tests + sensitivity + gate verdict (sub-tasks 16-23)

**Notebook target.** `notebooks/abrigo_y3_x_d/03_tests_and_sensitivity.ipynb`
**Upstream input.** NB2 estimates JSONs (`primary_estimate.json` + `bootstrap_recon.json` + `coef_table.json`) + NB1 panel-fingerprint + outlier diagnostics.
**Downstream consumer.** Auto-rendered README (sub-task 24); the gate verdict at `notebooks/abrigo_y3_x_d/estimates/gate_verdict.json` already exists and is reproduced byte-exact by NB3.

#### Sub-task 16 — NB3 §0 — notebook header + estimate-load

- **Deliverable.** NB3 §0 with: notebook title; one-sentence purpose statement (this notebook runs T1-T7 specification tests + reproduces the 14-row sensitivity gate verdict + emits the forest plot + auto-renders the README); upstream input enumeration (NB2 estimates + NB1 panel-fingerprint + outlier diagnostics); downstream consumer enumeration (auto-rendered README); pin to the published `gate_verdict.json` SHA.
- **Acceptance.** Header renders; all NB2 / NB1 inputs load successfully; SHA pin reproduces.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Block B closed (NB2 fully assembled and 3-way reviewed).

#### Sub-task 17 — NB3 §1 — T1-T7 specification tests (split across sub-tasks 17.1-17.7, ONE trio per test for dispatch atomicity)

NB3 §1 hosts the T1-T7 specification-test suite. Each test is its own dispatch unit (sub-tasks 17.1 through 17.7) to remove any "bulk authoring" misreading risk per the CR advisory under the spec-review trio dated 2026-04-26. The user gates each trio individually per `feedback_notebook_trio_checkpoint`. The seven sub-tasks emit per-test verdicts to a shared JSON at `notebooks/abrigo_y3_x_d/estimates/spec_tests.json`; the JSON is appended (or rewritten with all loaded entries) at each trio close. T3 carries two sub-components (T3a placebo + T3b primary gate) under one sub-task because the gate-rule pre-registration treats them as a single bundled test (placebo + gate) per Rev-2 spec §5.

#### Sub-task 17.1 — NB3 §1.1 — T1 (exogeneity / Hausman-style)

- **Deliverable.** NB3 §1.1 trio with: T1 exogeneity test on X_d; F-stat (`3.4797` per spec test report) / chi-square; p-value; verdict (REJECTS at p = `0.003111` per `gate_verdict.json` `t1_exogeneity_p`); explicit interpretation (β̂ is a PREDICTIVE-REGRESSION coefficient, NOT a structural elasticity — the FX-vol-CPI Colombia Finding 14 carry-forward is consolidated at sub-task 20 NB3 §4). Citation block cites Hausman (1978) + Rev-2 spec §5.
- **Acceptance.** T1 verdict matches `gate_verdict.json` byte-exact (REJECTS at p = `0.003111`).
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 16 closed.

#### Sub-task 17.2 — NB3 §1.2 — T2 (Levene equal-variance)

- **Deliverable.** NB3 §1.2 trio with: Levene equal-variance test on weekly residuals; F-stat; p-value; verdict per `gate_verdict.json` `t2_levene_p = 0.20379` (NULL-NOT-REJECTED — no detectable weekly variance premium). Citation block cites Levene (1960) + the FX-vol-CPI Colombia NB3 §1.2 precedent.
- **Acceptance.** T2 verdict matches `gate_verdict.json` byte-exact (NULL-NOT-REJECTED at p = `0.20379`).
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 17.1 closed.

#### Sub-task 17.3 — NB3 §1.3 — T3 (placebo + primary-gate one-sided 90%)

- **Deliverable.** NB3 §1.3 trio with TWO sub-components rendered as a single trio because the gate-rule pre-registration treats them as a bundled test:
  - **T3a placebo regression** — pre-week leads of X_d as predictors; per-lead β̂ + p-value; verdict per `gate_verdict.json` `t3a_p_two = 0.04928` (REJECTS — same two-sided p as the primary indicates leads are spurious correlates of Y₃, consistent with the predictive-regression framing).
  - **T3b primary gate** — one-sided 90% computation `β̂ − 1.28 · SE > 0`; computed lower bound = `−4.6207e−8` < 0; verdict FAIL per `gate_verdict.json` `t3b_passes = false`; explicit reproduction of the gate verdict statement byte-exact.
  Citation block cites the Rev-2 spec §5 placebo design + Bertrand-Duflo-Mullainathan (2004) + the Rev-2 spec §6 gate-rule pre-registration + `feedback_strict_tdd`.
- **Acceptance.** T3a verdict matches byte-exact (REJECTS at two-sided p = `0.04928`); T3b verdict matches byte-exact (FAIL); the one-sided 90% lower bound `−4.6207e−8` reproduces byte-exact.
- **Subagent.** Analytics Reporter / 1 trio (the T3a + T3b sub-components are authored in a single trio because they are pre-registered as one bundled test).
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 17.2 closed.

#### Sub-task 17.4 — NB3 §1.4 — T4 (Ljung-Box autocorrelation)

- **Deliverable.** NB3 §1.4 trio with: Ljung-Box test on residuals at lags 4 and 8; p-values per `gate_verdict.json` `t4_ljungbox_lag4_p = 0.50136` and `t4_ljungbox_lag8_p = 0.33080`; verdict NULL-NOT-REJECTED (no autocorrelation detected at standard significance thresholds). Citation block cites Ljung-Box (1978).
- **Acceptance.** Both lag-4 and lag-8 p-values reproduce byte-exact.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 17.3 closed.

#### Sub-task 17.5 — NB3 §1.5 — T5 (Jarque-Bera normality)

- **Deliverable.** NB3 §1.5 trio with: Jarque-Bera normality test on residuals; p-value per `gate_verdict.json` `t5_jb_p = 0.68334`; verdict per `t5_normality_rejects = false` (residuals are not statistically distinguishable from normal at 90%). Citation block cites Jarque-Bera (1980) + Breusch-Pagan (1979) + White (1980) for cross-reference to heteroskedasticity diagnostics.
- **Acceptance.** T5 verdict matches `gate_verdict.json` byte-exact.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 17.4 closed.

#### Sub-task 17.6 — NB3 §1.6 — T6 (Chow / break stability) — anchor for sub-task 19

- **Deliverable.** NB3 §1.6 trio with: T6 break-stability test computation; Chow-style p-value per `gate_verdict.json` `t6_chow_p = null` (recorded as null in JSON; cite the source-of-truth in `spec_tests.md`); verdict per `t6_break_rejects = false` (no detectable break in coefficient across the panel window). The T6 cross-row coefficient stability TABLE (β̂_X_d across all 14 rows) is the load-bearing artifact and is authored in sub-task 19; sub-task 17.6 produces the underlying test statistic and verdict that sub-task 19 consumes. Citation block cites the Rev-2 spec §5 T6 rule.
- **Acceptance.** T6 verdict matches `gate_verdict.json` byte-exact.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 17.5 closed.

#### Sub-task 17.7 — NB3 §1.7 — T7 (predictive-vs-structural framing) — anchor for sub-task 20

- **Deliverable.** NB3 §1.7 trio with: T7 framing test; per `gate_verdict.json` `t7_predictive_or_structural = "predictive"` and `t7_within_one_se = false`; explicit verdict that β̂ is a PREDICTIVE-REGRESSION coefficient, NOT a structural elasticity. The full T7 framing markdown + simulator-calibration-flag carry-forward from FX-vol Finding 14 lives at sub-task 20 NB3 §4; sub-task 17.7 produces the test verdict that sub-task 20 elaborates. Citation block cites Stock-Watson (2007) Ch. 14 predictive-regression framing.
- **Acceptance.** T7 verdict matches `gate_verdict.json` byte-exact.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 17.6 closed.

#### Sub-task 18 — NB3 §2 — pre-registered FAIL sensitivity reproduction (Rows 3, 4)

- **Deliverable.** NB3 §2 with: reproduction of `panel_row_03_locf_tail_excluded` (LOCF tail-week-excluded sensitivity) and `panel_row_04_imf_only_sensitivity` (IMF-only data-source sensitivity); per-row 90% CI; flag both rows as PRE-REGISTERED FAIL sensitivities (the FX-vol-CPI Colombia precedent A1 / A4 rows were pre-registered as POSITIVE-CI-excluding-zero candidates that became material-mover candidates under T3b-FAIL but were halted by anti-fishing protocol; the Rev-2 spec follows the same pattern). Citation block cites `feedback_pathological_halt_anti_fishing_checkpoint` + Simonsohn-Simmons-Nelson (2020).
- **Acceptance.** Row 3 reproduces byte-exact at n = 65; Row 4 reproduces byte-exact at n = 56; the FAIL-sensitivity flag is explicit in the rendered markdown; pre-registered power values `power(65, 13, 0.40) = 0.8027` and `power(56, 13, 0.40) = 0.7301` are cited.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 17.7 closed (all seven specification-test trios complete).

#### Sub-task 19 — NB3 §3 — cross-row coefficient stability (T6)

- **Deliverable.** NB3 §3 with: T6 cross-row coefficient stability table (β̂_X_d across all 14 rows); pairwise sign-agreement flag; cross-row stability verdict per the Rev-2 spec §5 T6 rule. Citation block cites the Rev-2 spec §5 T6 rule + the FX-vol-CPI Colombia NB3 §6 cross-row stability precedent.
- **Acceptance.** T6 table reproduces byte-exact from the Phase 5b spec_tests.md.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 17.6 (T6 trio) closed.

#### Sub-task 20 — NB3 §4 — predictive-vs-structural framing (T7 + FX-vol Finding 14 carry-forward)

- **Deliverable.** NB3 §4 with: T7 explicit framing of β̂ as a PREDICTIVE-REGRESSION coefficient (NOT structural); carry-forward of FX-vol-CPI Colombia Finding 14 from `project_fx_vol_econ_complete_findings` (T1 exogeneity REJECTS in the FX-vol case; same exogeneity question reappears here and the T7 framing is the explicit answer); flag for downstream simulator calibration that β̂ is NOT a structural-elasticity input. Citation block cites Stock-Watson (2007) Ch. 14 predictive-regression framing + Hansen (1982) GMM + `project_fx_vol_econ_gate_verdict_and_product_read` (predictive-regression flag for simulator calibration).
- **Acceptance.** T7 framing markdown is explicit; the simulator-calibration flag is product-load-bearing and traceable.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 17.7 (T7 trio) closed.

#### Sub-task 21 — NB3 §5 — convex-payoff insufficiency caveat reproduction (spec §11.A verbatim)

- **Deliverable.** NB3 §5 reproduces the Rev-2 spec §11.A convex-payoff insufficiency caveat VERBATIM (byte-exact prose lift, with quote markers); explicit cross-reference to Task 11.O.ζ-α (Rev-3 ζ-group) as the separate stage where convex-payoff hypotheses get tested; explicit flag that mean-β alone is INSUFFICIENT for convex-payoff product pricing. Citation block cites `project_abrigo_convex_instruments_inequality` + the Rev-2 spec §11.A pre-commitment.
- **Acceptance.** §11.A prose is byte-exact against `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`; cross-reference to Rev-3 ζ-group is unambiguous; product-load-bearing claim is preserved.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 20 closed.

#### Sub-task 22 — NB3 §6 — anti-fishing audit table reproduction (spec §9 byte-exact)

- **Deliverable.** NB3 §6 reproduces the Rev-2 spec §9 anti-fishing audit table BYTE-EXACT (every threshold, every row, every gate-rule definition); explicit flag that NO threshold has been modified post-hoc; explicit reference to `feedback_pathological_halt_anti_fishing_checkpoint` (no silent threshold tuning). Citation block cites Simonsohn-Simmons-Nelson (2020) + Ankel-Peters-Brodeur-Connolly (2024) + the Rev-2 spec §9 pre-commitment.
- **Acceptance.** §9 audit table prose and structure are byte-exact against the Rev-2 spec.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 21 closed.

#### Sub-task 23 — NB3 §7 — forest plot + per-test gate table

- **Deliverable.** NB3 §7 with: 14-row forest plot (consumed from NB2 §7 figure file at `notebooks/abrigo_y3_x_d/figures/forest_plot.png`); per-test gate table (one row per T1-T7, per-test verdict, per-test role — primary gate vs auxiliary; verdicts loaded from `gate_verdict.json` `spec_tests` block: T1 exogeneity REJECTS at p = `0.003111`, T3a REJECTS at two-sided p = `0.04928`, T3b passes = false, T6 break-rejects = false, T7 framing = `predictive`); final gate verdict statement reproducing `gate_verdict.json` byte-exact (gate=FAIL, `β̂_X_d = −2.7987e−8`, HAC(4) SE = `1.4234e−8`, one-sided 90% lower bound = `−4.6207e−8`, t-stat = `−1.9662`, two-sided p = `0.0493`, n = 76, window `[2024-09-27, 2026-03-13]`). Citation block cites the FX-vol-CPI Colombia NB3 §8 + §9 precedent.
- **Acceptance.** Forest plot displays correctly in PDF render; per-test table reproduces byte-exact; final gate verdict statement reproduces byte-exact against `gate_verdict.json`.
- **Subagent.** Analytics Reporter / 1 trio.
- **Reviewer (per-trio).** User in-loop.
- **Dependency.** Sub-task 22 closed.

---

### Block D — README auto-render (sub-task 24)

Sub-task 24 is split across 24a (template authoring; Senior Developer) and 24b (render + verify; Analytics Reporter) to remove the dual-subagent ambiguity in the original drafting per the TW peer-review Advisory-4 (2026-04-26).

#### Sub-task 24a — README Jinja2 template authoring

- **Deliverable.** `notebooks/abrigo_y3_x_d/_readme_template.md.j2` — Jinja2 template mirroring the FX-vol-CPI Colombia `_readme_template.md.j2` structure: gate-verdict headline; primary-results table; reconciliation table; forest-plot embed; per-test gate table. Bound variables are fed from `gate_verdict.json` + `coef_table.json` + `spec_tests.json` + `bootstrap_recon.json`. The template is editorial / template-engineering work and falls outside the trio-checkpoint discipline scope.
- **Acceptance.** Template syntax is valid Jinja2; all referenced keys (e.g., `{{ row_1_beta_hat }}`, `{{ row_1_lower_90 }}`, `{{ row_1_n }}`, `{{ gate_verdict }}`, `{{ spec_tests.t1_rejects }}`) match keys in the upstream JSON files; structural mirror to FX-vol-CPI Colombia template is unambiguous.
- **Subagent.** Senior Developer.
- **Reviewer.** User reviews the template before render dispatch.
- **Dependency.** Sub-task 23 closed (NB3 fully assembled and all JSONs emitted).

#### Sub-task 24b — README render + post-render verification

- **Deliverable.** `notebooks/abrigo_y3_x_d/README.md` rendered from the template against the four upstream JSON files (output is product-facing, summary-only, no analytical claims beyond what the gate verdict supports). Render-time substitution is mechanical; no editorial drift.
- **Acceptance.** README renders cleanly without `KeyError`; the gate-verdict headline displays **FAIL** with the byte-exact Row-1 values from `gate_verdict.json` (`β̂ = −2.7987e−8`, HAC(4) SE = `1.4234e−8`, one-sided 90% lower bound = `−4.6207e−8`, n = 76, window `[2024-09-27, 2026-03-13]`); forest plot embeds correctly; per-test gate table populates from `spec_tests.json` for all of T1-T7.
- **Subagent.** Analytics Reporter.
- **Reviewer.** User in-loop on the rendered README.
- **Dependency.** Sub-task 24a closed.

---

## Dispatch ordering (binding sequence)

0. **BLOCKING upstream — env.py scaffolding fix.** Block A sub-task 1 cannot dispatch until the `env.py` `parents[3] → parents[2]` depth-adjustment fix lands at `notebooks/abrigo_y3_x_d/env.py`. The fix is OUT OF SCOPE for this sub-plan and is dispatched as a separate Senior Developer scaffolding-fix line under the major plan Task 11.O.NB-α body (cited at lines 2170-2188 of `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`). Without the fix, panel-load at NB1 §0 will resolve `_CONTRACTS_DIR` to the worktree root rather than `contracts/` and Block A will deadlock. The orchestrator MUST verify the env.py fix has landed (post-fix `parents[2]` resolves to `contracts/`) before sub-task 1 dispatches.
1. **Block A — NB1 trios.** Sub-tasks 1 → 2 → 3 / 4 (parallelizable; same dependency on sub-task 2) → 5 (parallel with 3 / 4; same dependency) → 6 (depends on 3 + 4) → 7 (depends on 6).
2. **NB1 post-notebook 3-way review.** CR + RC + TW review the assembled `01_data_eda.ipynb`. PASS unblocks Block B; BLOCK triggers fix-up rewrite (3-cycle cap per `feedback_three_way_review`).
3. **Block B — NB2 trios.** Sub-tasks 8 → 9 → 10 / 11 / 12 / 13 / 14 (parallelizable; same dependency on sub-task 9) → 15 (depends on 10-14 all closed).
4. **NB2 post-notebook 3-way review.** CR + RC + TW review `02_estimation.ipynb`. PASS unblocks Block C.
5. **Block C — NB3 trios.** Sub-tasks 16 → 17.1 → 17.2 → 17.3 → 17.4 → 17.5 → 17.6 → 17.7 (each a single-trio dispatch; user gates each individually) → 18 → 19 → 20 → 21 → 22 → 23.
6. **NB3 post-notebook 3-way review.** CR + RC + TW review `03_tests_and_sensitivity.ipynb`. PASS unblocks Block D.
7. **Block D — README auto-render.** Sub-task 24a (Senior Developer template authoring) → 24b (Analytics Reporter render + verify).
8. **Final post-deliverable 3-way review.** CR + RC + TW review the assembled `notebooks/abrigo_y3_x_d/` deliverable as a whole (notebooks rendered to PDF + README rendered + all JSONs in `estimates/` + all figures in `figures/`). PASS closes Task 11.O.NB-α.

The dispatch ordering enforces that every notebook is fully assembled and 3-way reviewed before the next notebook starts; this prevents downstream notebooks from inheriting unreviewed defects from upstream notebooks.

---

## Acceptance criteria for the sub-plan as a whole

The sub-plan is COMPLETE (Task 11.O.NB-α closed) when ALL of the following hold:

- **A1.** `notebooks/abrigo_y3_x_d/01_data_eda.ipynb` executes end-to-end via `nbconvert --execute` against the Phase 5a parquets + DuckDB state without error; renders to PDF at `notebooks/abrigo_y3_x_d/pdf/01_data_eda.pdf`; passes post-notebook 3-way review (CR + RC + TW PASS).
- **A2.** `notebooks/abrigo_y3_x_d/02_estimation.ipynb` executes end-to-end via `nbconvert --execute`; renders to PDF at `notebooks/abrigo_y3_x_d/pdf/02_estimation.pdf`; reproduces the Rev-5.3.2 published 14-row coefficient table BYTE-EXACT against `gate_verdict.json` (Row-1 primary `β̂ = −2.7987e−8`, HAC(4) SE = `1.4234e−8`, n = 76; Row-3 LOCF-tail-excluded n = 65 pre-registered FAIL; Row-4 IMF-only n = 56 pre-registered FAIL; Rows 9 and 10 deferred-empty per Phase 5a `manifest.md`); no re-estimation drift; passes post-notebook 3-way review.
- **A3.** `notebooks/abrigo_y3_x_d/03_tests_and_sensitivity.ipynb` executes end-to-end via `nbconvert --execute`; renders to PDF at `notebooks/abrigo_y3_x_d/pdf/03_tests_and_sensitivity.pdf`; reproduces the Rev-5.3.2 published T1-T7 spec-test verdicts byte-exact against `gate_verdict.json` `spec_tests` block (T1 REJECTS at p = `0.003111`, T3a REJECTS at two-sided p = `0.04928`, T3b passes = false, T6 break-rejects = false, T7 = `predictive`); reproduces the gate verdict FAIL with the canonical Row-1 values (β̂, SE, t-stat, two-sided p, one-sided 90% lower bound, n, window) byte-exact; passes post-notebook 3-way review.
- **A4.** `notebooks/abrigo_y3_x_d/README.md` is auto-rendered from `_readme_template.md.j2` against `gate_verdict.json` + `coef_table.json` + `spec_tests.json` + `bootstrap_recon.json`; the gate-verdict headline displays **FAIL** with byte-exact Row-1 values from `gate_verdict.json` (β̂ = `−2.7987e−8`, HAC(4) SE = `1.4234e−8`, one-sided 90% lower bound = `−4.6207e−8`, n = 76, window `[2024-09-27, 2026-03-13]`); forest plot embeds correctly; per-test gate table populates without `KeyError`.
- **A5.** Every test / decision / spec-choice in NB1 / NB2 / NB3 carries the 4-part citation block per `feedback_notebook_citation_block`. The post-notebook 3-way review explicitly verifies citation-block coverage; missing or generic citation blocks are a BLOCKING defect.
- **A6.** The convex-payoff insufficiency caveat at NB3 §5 is preserved verbatim from Rev-2 spec §11.A. The cross-reference to Task 11.O.ζ-α (Rev-3 ζ-group) is unambiguous.
- **A7.** No code, schema, design doc, DuckDB, or existing notebook (FX-vol-CPI Colombia precedent) is modified by Task 11.O.NB-α execution. **Categorically forbidden under this sub-plan:** (i) re-estimation of any panel row — every numeric output in NB1 / NB2 / NB3 is byte-exact reproduction from the Phase 5a parquets and the published `gate_verdict.json`; running an estimator with intent to produce new numbers (even with identical seed and library versions) is forbidden; (ii) modification of any panel parquet under `contracts/.scratch/2026-04-25-task110-rev2-data/`; (iii) modification of any JSON / markdown artifact under `contracts/.scratch/2026-04-25-task110-rev2-analysis/`; (iv) silent threshold tuning, row reordering, or row exclusion (per `feedback_pathological_halt_anti_fishing_checkpoint`); (v) editorial compression of the convex-payoff caveat at NB3 §5 (per pre-commitment 5). The only filesystem deltas are: new files under `notebooks/abrigo_y3_x_d/` (NB1/NB2/NB3 ipynb + PDFs + JSONs + figures + `_readme_template.md.j2` + `README.md`); a one-time `env.py` path-depth adjustment from `parents[3]` → `parents[2]` (Senior Developer dispatch under the existing scaffolding-fix line of the major plan, NOT under this sub-plan).
- **A8.** All artifacts are committed to branch `phase0-vb-mvp` and pushed to `origin` per `feedback_push_origin_not_upstream`.
- **A9.** Memory entry updated to record Task 11.O.NB-α COMPLETED with pointer to `notebooks/abrigo_y3_x_d/README.md`.

---

## Reviewers

- **Per-trio (during authoring).** User in-loop. The user reviews each rendered (why-markdown, code-cell, interpretation-markdown) trio and explicitly approves before the next trio dispatches. Per `feedback_notebook_trio_checkpoint`, this is NON-NEGOTIABLE.
- **Per-notebook (post-assembly).** CR (Code Reviewer) + RC (Reality Checker) + TW (Technical Writer) per `feedback_three_way_review`. The post-notebook review is binary (PASS / BLOCK); BLOCK triggers fix-up rewrite under the 3-cycle cap. The Code Reviewer focuses on byte-exact reproduction of the published Rev-5.3.2 estimates; the Reality Checker focuses on citation-block fidelity and prose-vs-results consistency; the Technical Writer focuses on prose clarity, section ordering, and the convex-payoff caveat preservation at NB3 §5.
- **Sub-plan authoring review (this document).** CR + RC + TW per `feedback_three_way_review`. This document is the spec for the work; spec-review trio gates execution.
- **Final deliverable review.** CR + RC + TW review the assembled `notebooks/abrigo_y3_x_d/` directory as a whole including the auto-rendered README. PASS closes Task 11.O.NB-α.

---

## Reference paths

**Major plan and Rev-5.3.3 anchor.**
- `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` — major plan; Task 11.O.NB-α super-task body at lines 2170-2188.

**Track A spec.**
- `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` — Rev-2 mean-β spec being migrated to notebook form (sha `d9e7ed4c8` at authoring time per Phase 5a `manifest.md`).

**Phase 5a Data Engineer output (panel parquets).**
- `contracts/.scratch/2026-04-25-task110-rev2-data/panel_row_01_primary.parquet` … `panel_row_14_wc_cpi_weights_sens.parquet`
- `contracts/.scratch/2026-04-25-task110-rev2-data/manifest.md`
- `contracts/.scratch/2026-04-25-task110-rev2-data/data_dictionary.md`
- `contracts/.scratch/2026-04-25-task110-rev2-data/validation.md`
- `contracts/.scratch/2026-04-25-task110-rev2-data/queries.md`
- `contracts/.scratch/2026-04-25-task110-rev2-data/_audit_summary.json`

**Phase 5b Analytics Reporter output (estimates and verdicts).**
- `contracts/.scratch/2026-04-25-task110-rev2-analysis/estimates.md`
- `contracts/.scratch/2026-04-25-task110-rev2-analysis/spec_tests.md`
- `contracts/.scratch/2026-04-25-task110-rev2-analysis/sensitivity.md`
- `contracts/.scratch/2026-04-25-task110-rev2-analysis/summary.md`
- `contracts/.scratch/2026-04-25-task110-rev2-analysis/gate_verdict.json`

**Existing scripts (upstream of notebook migration; NOT modified by this sub-plan).**
- `contracts/scripts/phase5_data_prep.py`
- `contracts/scripts/phase5_analytics.py`
- `contracts/scripts/run_phase5_analytics.py`
- `contracts/tests/inequality/test_phase5b_analytics.py`

**FX-vol-CPI Colombia precedent (binding 3-notebook structure template).**
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb`
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/02_estimation.ipynb`
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py`
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/references.bib`
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/_nbconvert_template/`
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/_readme_template.md.j2`
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/README.md`

**Task 11.O.NB-α scaffolding (already established by foreground orchestrator).**
- `contracts/notebooks/abrigo_y3_x_d/env.py` (parents[3] → parents[2] depth adjustment pending; Senior Developer dispatch under separate scaffolding-fix line at major plan `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` lines 2170-2188 within the Task 11.O.NB-α body)
- `contracts/notebooks/abrigo_y3_x_d/references.bib`
- `contracts/notebooks/abrigo_y3_x_d/_nbconvert_template/`
- `contracts/notebooks/abrigo_y3_x_d/estimates/gate_verdict.json`
- `contracts/notebooks/abrigo_y3_x_d/figures/` (empty)
- `contracts/notebooks/abrigo_y3_x_d/pdf/` (empty)

**Trend Researcher output (TR Findings 1, 2, 3 — anchoring the diurnal-pattern citation at NB1 §3).**
- `contracts/.scratch/2026-04-25-mento-userbase-research.md`

**Project memory (binding entries cited above).**
- `feedback_notebook_citation_block`
- `feedback_notebook_trio_checkpoint`
- `feedback_three_way_review`
- `feedback_no_code_in_specs_or_plans`
- `feedback_push_origin_not_upstream`
- `feedback_strict_tdd`
- `feedback_pathological_halt_anti_fishing_checkpoint`
- `project_abrigo_convex_instruments_inequality`
- `project_abrigo_mento_native_only`
- `project_y3_inequality_differential_design`
- `project_carbon_user_arb_partition_rule`
- `project_carbon_defi_attribution_celo`
- `project_critical_local_paths_resume`
- `project_phase15_5_task_chain_post_rev531`
- `project_mdes_formulation_pin`
- `project_fx_vol_econ_complete_findings`
- `project_fx_vol_econ_gate_verdict_and_product_read`
- `project_abrigo_inequality_hedge_thesis`

---

## Budget and scope

- **Authoring budget for THIS sub-plan document.** ≤ 45 minutes editorial.
- **Execution budget for the 24 sub-tasks.** Out of scope for this sub-plan; tracked at the major-plan Task 11.O.NB-α body.
- **File scope under THIS sub-plan authoring.** Create `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md`. NO modifications to: major plan, code, schema, design doc, DuckDB, existing notebooks (FX-vol-CPI Colombia precedent), existing scaffolding under `notebooks/abrigo_y3_x_d/`. Sub-plan execution will adjust `env.py` depth via Senior Developer dispatch under a separate line; this document does not perform that adjustment.
- **Code-agnostic body.** 100%. Backticked names / paths / hashes are reference identifiers, not code.

---

## Cross-references

- **Sibling sub-plans under Rev-5.3.3.**
  - `contracts/docs/superpowers/sub-plans/2026-04-25-rev3-zeta-group.md` (Track α Rev-3 ζ-group convex-payoff extensions; TO BE AUTHORED)
  - `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (Task 11.P.MR-β.1 cCOP-vs-COPM provenance audit; TO BE AUTHORED)
  - `contracts/docs/superpowers/sub-plans/2026-04-25-beta-spec.md` (Track β spec authoring; TO BE AUTHORED after MR-β.1 completes)
  - `contracts/docs/superpowers/sub-plans/2026-04-25-beta-execution.md` (Track β analytical execution; TO BE AUTHORED after β spec converges)
- **This sub-plan does NOT block any sibling sub-plan.** Track α Rev-2 notebook migration (this document) and Track β execution are independent at the dispatch level. Track α Rev-3 ζ-group is a separate stage of α and may begin after this sub-plan converges 3-way review (or in parallel, at user discretion).

---

## CORRECTIONS — Rev-5.3.5 β-resolution interpretation reframe (2026-04-26)

**Trigger.** MR-β.1 sub-task 1 HALT-VERIFY → user picked path β → Rev-2's X_d ingestion was scope-mismatched (Minteo-fintech `0xc92e8fc2…` is OUT of Mento-native scope; `0x8A567e2a…` is the canonical Mento V2 `StableTokenCOP`). Authoritative disposition: `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`. Major-plan anchor: Rev-5.3.5 CORRECTIONS in `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`.

**Numbers stay byte-exact. Only interpretation-cell framing changes.**

### §B pre-commitment 6 retraction (post-CR-trio-finding §3.1, 2026-04-26)

**§B pre-commitment 6 (line 35) is RETRACTED under Rev-5.3.5.** The pre-commitment's claim that `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` is "Mento-native cCOP basket-volume series" is false: the address is **Minteo-fintech COPM-Minteo** (out of Mento-native scope per the major-plan Rev-5.3.5 CORRECTIONS block + `project_abrigo_mento_native_only` β-corrigendum + `project_mento_canonical_naming_2026` β-corrigendum + the disposition memo's empirical Dune evidence). The Mento-native COPm address is `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (Mento V2 `StableTokenCOP`).

The pre-commitment's "no block on Rev-2 re-presentation" clause is honored without contradiction: numbers stay byte-exact (Rev-2 published estimates reproduce against the Phase 5a parquets unchanged); the X_d in this notebook re-presentation IS the published Minteo-fintech series (now correctly classified out-of-Mento-native-scope); the framing rescope to scope-mismatch close-out per the rest of this CORRECTIONS block carries the disposition forward without re-estimating, re-binning, or re-thresholding any Rev-2 row.

A reader landing in §B-6 must read this retraction first; the original §B-6 text is preserved unmodified for audit-trail purposes but is overlaid by this retraction. Future revisions of the NB-α sub-plan can either (a) replace §B-6 in place under a Rev-5.3.6+ CORRECTIONS-block discipline, OR (b) leave §B-6 + this retraction stacked indefinitely; either is acceptable per `feedback_pathological_halt_anti_fishing_checkpoint` anti-fishing-on-memory-edits append-only-or-section-replace-with-corrigendum discipline.

### Affected dispatch units

NB-α's 31 dispatch units carry forward unchanged for byte-exact migration of Rev-2 panels, gate verdicts (β̂ = −2.7987e−8, n = 76, T3b FAIL), T1–T7 spec tests, Phase 5b sensitivity rows, and all artifact paths. Anti-fishing invariants (N_MIN=75, POWER_MIN=0.80, MDES_SD=0.40, MDES_FORMULATION_HASH = `4940360dcd2987…cefa`, decision_hash = `6a5f9d1b05c1…443c`) preserved byte-exact.

What changes: every `interpretation-markdown` cell whose Rev-2-source framing falls into the **banned substring set** must be rewritten using the **canonical reframe substring set**, with deterministic grep-verifiable acceptance per TW-2a advisory:

- **Banned substring set** (banned in migrated NB-α interpretation cells): `Mento-native hedge`, `hedge thesis`, `tested-and-failed`, `tested and failed`, `Mento-hedge-fail`, `Mento-hedge-thesis-tested-and-failed`.
- **Required canonical reframe substring set** (≥1 must appear in each affected interpretation cell): `Minteo-fintech scope-mismatch`, `scope-mismatch close-out`, `Rev-2 closes scope-mismatch`, `Minteo-fintech X_d`.
- **Reviewer verification (deterministic):** `grep -i -F` over migrated notebooks must show **zero** matches in the banned set across the migrated NB-α corpus, and **≥1** match in the canonical set per affected interpretation cell. The 3-way review on NB-α deliverables runs this grep as a falsifiable acceptance criterion; any banned-set match in the migrated corpus fails review.

### Rescoped interpretation framing (concrete language)

For every interpretation cell where the original Rev-2 framing was applicable, the dispatched Analytics Reporter applies one of the following framings:

- **For NB1 §0 panel-fingerprint validation cells** — frame the panel as recording the X_d series ingested for Rev-2 (i.e., `0xc92e8fc2…` Minteo-fintech transfers, 110,253 events, 76 weeks). Cross-reference the β-corrigenda in `project_mento_canonical_naming_2026` and `project_abrigo_mento_native_only`. State explicitly that this panel is preserved as historical scope-mismatched X_d; the in-scope Mento-native COPm address is `0x8A567e2a…` (β-track Rev-3 territory).
- **For NB2 estimation-row interpretation cells** — frame each row's β̂ + HAC SE + 90% one-sided lower bound + n + T3b verdict as **"the regression of Y₃ on Minteo-fintech X_d series."** State explicitly that the gate FAIL on T3b reflects Minteo-fintech-X_d's predictive-not-structural relationship with Y₃, NOT a test of Mento-native hedge demand. The sign-flip (β̂ < 0), the ρ(X_d, fed_funds) = −0.614 confounder, and T1 REJECTS predictive-not-structural are now coherent under the Minteo-fintech-payments-rail interpretation.
- **For NB3 sensitivity-row interpretation cells** — same reframe as NB2; sensitivity rows preserved byte-exact; framing flipped from "Mento-hedge-tested-and-failed" to "Minteo-fintech-scope-mismatched-close-out."
- **For README auto-rendered summary** — the Jinja2 template's interpretation paragraphs are reframed under the same rule. The product-facing summary states: Rev-2 closes as scope-mismatch; β-track Rev-3 (against `0x8A567e2a…` Mento-native COPm) is the actual test of Mento-native hedge demand.

### Citation-block discipline reaffirmed

The 4-part `feedback_notebook_citation_block` discipline is unchanged. Every test/decision/spec choice in interpretation cells is preceded by reference / why used / relevance to results / connection to simulator markdown. Under β-reframe, a NEW citation reference is added wherever the interpretation cell touches scope: the disposition memo at `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` is cited as the authoritative scope-mismatch source.

### Trio-checkpoint discipline reaffirmed

The `feedback_notebook_trio_checkpoint` HALT-after-each-trio discipline is unchanged. Analytics Reporter HALTS after every (why-markdown, code-cell, interpretation-markdown) trio for human review; bulk authoring is anti-fishing-banned. Under β-reframe, the trio's interpretation cell is the only point where reframing applies; the why-markdown and code-cell are byte-exact migration artifacts.

### Out-of-scope reaffirmed under Rev-5.3.5

NB-α does NOT:
- Re-estimate any Rev-2 row (anti-fishing-immutable).
- Re-bin, re-threshold, or re-evaluate any gate verdict.
- Ingest β-track Rev-3 X_d data (that is Task 11.P.spec-β / Task 11.P.exec-β scope).
- Mutate any DuckDB row (consume-only invariant).
- Author any new Solidity, Python, or schema migration.
- Conflate the Rev-2 (Minteo-scope) interpretation with the future Rev-3 (Mento-native scope) interpretation — these are distinct analytical exercises.

### Reviewer cycle for this CORRECTIONS block

Bundled into the same post-hoc 3-way review (CR + RC + TW) that is dispatched on the major-plan Rev-5.3.5 CORRECTIONS block + the MR-β.1 sub-plan §I CORRECTIONS block + the disposition memo. Single review trio covers the full β-resolution disposition. Convergence is required before NB-α dispatch unit 1 (the env.py-gated NB1 §0 panel-fingerprint validation) can re-dispatch under the rescoped framing.
