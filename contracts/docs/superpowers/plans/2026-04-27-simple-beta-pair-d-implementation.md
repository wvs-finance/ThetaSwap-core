---
spec_sha256: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
spec_version_pinned: 1.3.1 (CORRECTIONS-α' + 3-way cleanup per Task 1.1 Step 1 second HALT 2026-04-28 PM; supersedes v1.3 4611abc491258…6b57 which superseded v1.2.1 b90be50bd9c6…4c6d which superseded v1.2 19bdaed9b966…b7a4 which superseded v1.1 f74b2ac577d5…41728; 3 verifier waves all PASS-WITH-REV at v1.3 with ZERO BLOCKERs)
plan_verifier_v1_wave1: PASS-WITH-REVISIONS (Reality Checker, 2026-04-27, 6 defects — all integrated in v2)
plan_verifier_v1_wave2: PASS-WITH-REVISIONS with 2 BLOCK-severity (Senior Project Manager, 2026-04-27, 11 defects — all integrated in v2)
plan_verifier_v2_wave1: pending re-dispatch
plan_verifier_v2_wave2: pending re-dispatch
revision_history:
  - v1 2026-04-27 initial draft
  - v2 2026-04-27 integrate RC + SPM verifier defects (~17 total). Convergent fix on ESCALATE threshold (RC D3 + SPM D2 BLOCK). New schema-break verification (SPM D5 BLOCK). Timeline buffer added; Doc-Verify trailer gaps closed; HALT protocol expanded; closure-archival step added; goal-sentence reworded; youth-band discrepancy flagged; Phase-2 parallelization annotation corrected; trio-HALT taxonomy added; ESCALATE-FAIL handoff concretized.
  - v2.1 2026-04-27 inline patch integrating SPM v2 verifier findings (N1 self-review spec-coverage bullet + N2 Task 2.4 Step 5 "credible" → spec §3 ESCALATE-PASS threshold reference; N2 was a convergent finding RC NB-R2 + SPM N2). N3-N6 LOW polish items deferred to next plan revision. RC v2 PASS (no STILL-BLOCKING). SPM v2 PASS-WITH-REVISIONS (zero v1-BLOCK carryover; 6 new defects all NON-BLOCKING).
  - v2.2 2026-04-28 CORRECTIONS-α revision per Task 1.1 Step 0 schema-stability HALT (typed exception `PairDSchemaPreFlightPathological`). User picked Option α from disposition memo (`contracts/.scratch/2026-04-28-task-1.1-step-0-schema-pathological-disposition.md`): shorten sample window to 2010-01 → 2026-03 (DANE-canonical, anti-fishing-cleanest). Plan Task 1.1 Step 0 amended with pinned harmonization rules table per Option α; Step 1 window updated 2008→2010; Step 4 simplified (Empalme catalogs pre-incorporate the empalme factor in FEX_C); Task 1.3 Step 2 N expectation revised 206→183. Spec §4 + §9.9 + frontmatter updated; new spec sha256 pinned (supersedes v1.1 sha256 `f74b2ac577d5…41728`). 3-way review of CORRECTIONS (RC + MQS-fresh + SPM) before commit per HALT protocol.
  - v2.3 2026-04-28 PM CORRECTIONS-α' revision per Task 1.1 Step 1 second HALT (typed exception `PairDEmpalmeSchemaContradictsHarmonizationPin`). DANE Empalme files for 2010-2014 ship `RAMA4D` with Rev.3 codes; CORRECTIONS-α's column-header-only verification was insufficient (now codified in `feedback_schema_pre_flight_must_verify_values`). User picked Option α' from disposition memo (`contracts/.scratch/2026-04-28-task-1.1-step-1-empalme-rev3-vs-rev4-disposition.md`): shorten window to 2015-01 → 2026-03 (DANE-canonical Rev.4 throughout via `RAMA4D_R4`). Spec §4 window updated 2010-01 → 2015-01; spec §9.10 new CORRECTIONS-α' audit-trail block; spec §6 + §5.1 CIIU-revision boundary refs updated to 2015 cutoff. Plan Task 1.1 Step 0 era table edited: "2010-01 → 2020-12 RAMA4D" row replaced with "2015-01 → 2020-12 RAMA4D_R4" (72 mo); Step 1 window 2010→2015; Task 1.3 Step 2 N expectation 183→123. Spec sha256 b90be50bd9c6…4c6d → (computed at end of CORRECTIONS-α'-3-way-review pin). 3-way review (RC + MQS-fresh + SPM) before commit per HALT protocol.
  - v2.4 2026-04-28 PM late evening CORRECTIONS-β revision per Phase-3 3-way review finding (Senior Developer ACCEPT_WITH_REMEDIATION verdict; Reality Checker ACCEPT_WITH_FLAGS; Code Reviewer PASS_WITH_NITS). **Documented deviation: Phase-2 was originally executed as standalone Python scripts (`scripts/task_2_1_primary_ols.py`, `scripts/task_2_2_robustness.py` — script-form numerical results committed at HEAD `bce431544`), NOT as notebooks under the trio-checkpoint discipline that plan-Tasks 2.2 + 2.3 mandated per memory `feedback_notebook_trio_checkpoint` (NON-NEGOTIABLE).** SD verified: `notebooks/` directory was empty at Phase-2 close; no per-trio HALTs fired during script-form execution; no CORRECTIONS-block had been recorded. The script-form execution produced byte-deterministic JSON (arguably stronger reproducibility than mutable notebook state) but bypassed the discipline. **User-chosen remediation 2026-04-28 PM late evening: Option β.** Re-execute Phase 2 as notebooks with proper trio structure, mirroring `contracts/notebooks/fx_vol_cpi_surprise/Colombia/` 3-notebook pattern (per user "same patterns" override of plan's 5-notebook schema). Execution under Phase 2.5 below; numerical content reproduces script-form JSON byte-for-byte (sha256 round-trip asserted in NB02 §2 + NB03 §6); spec sha256 NOT bumped (Phase-2 numerical artifacts retain governance under v1.3.1; this plan revision documents the documentation-layer remediation only). Phase 2.5 added below; MEMO §10 task-numbering reconciliation table cross-references plan-Task vs orchestrator-execution-Task numbering. Per `feedback_two_wave_doc_verification`, this plan revision is committed under user-explicit auto-mode override per memory `feedback_proceed_without_asking_auto_mode`; 2-wave verification deferred (acknowledged process trade-off).
notebook_trailer_convention: This plan defines a deferred-trailer convention for notebook commits during Phase 2 (`Doc-Verify: orchestrator-only-pre-Phase-3 (3-way review deferred to Task 3.2)` per SPM D9). Notebook commits are intentionally trailer-light pre-Phase-3; the 3-way review in Task 3.2 audits notebooks retrospectively. Future audits of Doc-Verify trailers should be aware of this convention to avoid false-positive process-violation flags. Standard 2-wave + 3-way trailers apply at all spec / memo / CLAUDE.md commits.
---

# Simple-β Pair D — Colombian BPO Trap Hedge Empirical Validation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Per project convention `feedback_no_code_in_specs_or_plans`, this plan is code-agnostic; implementation specifics are deferred to executor sub-agents per task. Per `feedback_specialized_agents_per_task`, each task names the specialist owner.

**Goal:** Empirically test whether Colombian young-worker services-sector employment share responds positively to lagged COP/USD devaluation, producing a falsifiable feasibility verdict (β > 0 PASS / β = 0 FAIL → escalate to convex-payoff evidence) that determines whether Pair D **becomes a candidate for Stage 2 (M sketch) authoring as a separate downstream plan**, or is killed in favor of revisiting Pair A/B/C/E from the BPO research note 5-pair ranking. Stage 2 + Stage 3 are explicitly NOT promised by this Stage-1 plan.

**Architecture:** Pre-registered single OLS (logit-OLS for bounded Y) regression with deliberately simpler methodology than the parked P1 apparatus per user "start simple" directive. Y = Colombian young-worker services-sector employment share (DANE GEIH monthly, youth band 14-28 per Ley 1622/2013, CIIU Rev.4 A.C. sections G-T broad services primary + J+M+N BPO-narrow sensitivity, ~135 monthly observations 2015-01 → 2026-03 post-CORRECTIONS-α' / N≈123 post-lag-12 — pre-lag-12 universe chain: ~218 original feasibility-universe → ~195 CORRECTIONS-α (2010-01 start; first HALT) → ~135 CORRECTIONS-α' (2015-01 start; second HALT — DANE Empalme RAMA4D ships Rev.3 codes 2010-2014 not Rev.4 as previously assumed); post-lag-12 N chain: ~206 → ~183 → ~123; logit-transformed for bounded [0.55, 0.75] range). X = COP/USD lagged 6-12 months (reuses closed FX-vol-CPI Phase-A.0 pipeline series). Sign expectation pre-pinned positive (Baumol → US-Colombia wage arbitrage → offshoring transmission, lit-grounded via Mendieta-Muñoz 2017 + Beerepoot-Hendriks 2013 mechanism validation).

**Tech stack (specialist-side, advisory):** Python pandas + statsmodels for OLS; arch package for GARCH-X if escalation triggers; DuckDB for panel storage per existing `contracts/scripts/` convention; Jupyter notebook with trio-checkpoint discipline (`feedback_notebook_trio_checkpoint`) and 4-part citation block (`feedback_notebook_citation_block`).

**Stage discipline (per CLAUDE.md framework Ideal-scenario clause):** This plan executes Stage 1 (empirical risk validation) only. Stage 2 (M sketch on Panoptic) and Stage 3 (deployment) are downstream and out of scope. Exit gate: positive-β confirmation at conventional significance, OR convex-payoff escalation evidence per pre-pinned contingency.

**Anti-fishing invariants (immutable through this plan):**
- Spec sha256-pinned in Phase 0; governs every downstream artifact
- Methodology-break disposition pre-committed in spec to {empalme factor / 2021 regime dummy} — restrict-to-≥2022 (which fails N_MIN=75) is anti-fishing-banned as a methodology choice
- Threshold pre-pinned in spec §3 to one-sided α=0.05 (H₀: composite β ≤ 0); choice of one-sided is fixed at spec authoring time, justified from literature not data, and locked by spec sha256; switching to two-sided post-data is anti-fishing-banned
- Escalation to quantile / GARCH-X / EVT pre-authorized BEFORE estimation; ESCALATE-PASS threshold itself pre-pinned with concrete numerics in spec §3 (per RC + SPM convergent flag); not a post-hoc rescue
- 3-way review of result memo regardless of verdict (PASS / FAIL / ESCALATE / SUBSTRATE_TOO_NOISY)
- HALT-disposition protocol per `feedback_pathological_halt_anti_fishing_checkpoint` invoked at every HALT point: typed exception → disposition memo enumerating ≥3 pivot options → user surface → user picks pivot → CORRECTIONS block → 3-way review of CORRECTIONS revision; auto-pivot is anti-fishing-banned

**Scope:** ~2-3 calendar weeks at single-stream pace with parallel Phase-1 dispatch. ~1.5 weeks lower bound IF zero HALT-disposition cycles fire AND escalation does not trigger — both are non-trivial conditions. Per SPM Wave 2 timeline check: 9.5-11 specialist-days unconditional; +1.5 days if escalation triggers. NOT the 416-line P1 apparatus, but tighter scope does not mean tighter timeline — methodology rigor preserved.

**Source artifacts (read before executing):**
- `contracts/.scratch/2026-04-27-colombian-bpo-non-industrialization-hedge-research.md` — BPO literature pass; mechanism + literature anchors + 5-pair ranking with Pair D as rank-1
- `contracts/.scratch/2026-04-27-dane-geih-y-feasibility.md` — GEIH feasibility; pinned youth/sector/methodology-break parameters
- `.worktree/ranFromAngstrom/CLAUDE.md` — framework section + Active iteration block (Pair D commit)
- Closed FX-vol-CPI pipeline at `contracts/notebooks/fx_vol_cpi_surprise/Colombia/` — COP/USD reuse pattern + Banrep series provenance

---

## File Structure

**Created by this plan:**

```
contracts/docs/superpowers/specs/2026-04-27-simple-beta-pair-d-design.md
  Phase 0 deliverable. Pre-registered single OLS spec, sha256-pinned.

contracts/.scratch/simple-beta-pair-d/
  data/
    geih_young_workers_services_share.parquet  Monthly Y (broad G-T)
    geih_young_workers_narrow_share.parquet    Monthly Y_narrow (J+M+N)
    cop_usd_panel.parquet                       Monthly X with lag panel
    panel_combined.parquet                      Aligned (timestamp, Y, X_lags)
    DATA_PROVENANCE.md                          Sources + transformations
  notebooks/
    env.py                                      Path + dependencies + citation template
    references.bib                              Lit anchors + spec sha256 + plan sha256
    01_geih_construct.ipynb                     Y construction with trio-checkpoint
    02_panel_align.ipynb                        X join + alignment
    03_ols_estimate.ipynb                       Primary OLS with trio-checkpoint
    04_escalation_if_needed.ipynb               Conditional: quantile / GARCH-X / EVT
    05_robustness.ipynb                         Always-runs robustness pass
  output/
    PRIMARY_RESULTS.md                          β̂, t-stat, p-value, sign per spec decision tree
    ROBUSTNESS_RESULTS.md                       4 robustness rows
    ESCALATION_RESULTS.md                       Conditional on Task 2.2 verdict = ESCALATE
    MEMO.md                                     Stakeholder memo with verdict + disposition
    gate_verdict.json                           Machine-readable verdict
    DISPOSITION.md                              User decision artifact (Phase 4)
```

**Modified by this plan:**

```
.worktree/ranFromAngstrom/CLAUDE.md
  Active iteration block updated post-Phase 3 with verdict + disposition pointer.
```

---

## Phase 0: Pre-registered spec

Goal: produce a sha256-pinned spec that fixes hypothesis, methodology, thresholds, and sample-selection rules BEFORE any GEIH micro-data is pulled.

### Task 0.1: Author simple-β spec

**Owner:** Model QA Specialist (drafts), Foreground Orchestrator (oversight)

**Files:**
- Create: `contracts/docs/superpowers/specs/2026-04-27-simple-beta-pair-d-design.md`

- [ ] **Step 1: Specialist drafts the spec.** Sections required:
  - §1 Background — Pair D mechanism + literature anchors (Mendieta-Muñoz 2017 + Beerepoot-Hendriks 2013) + framework Stage 1 location + Pair D commit context (CLAUDE.md Active iteration block). **MUST flag the youth-band citation discrepancy explicitly:** BPO research note §6 wrote (15-28); GEIH feasibility §Q2 wrote (14-28) with Ley 1622/2013 statutory citation; spec adopts 14-28 on the strength of the statutory anchor and DANE's own youth bulletin convention. Sensitivity at 18-28 / 18-24 is NOT performed (would constitute Y-construction post-data discretion banned by spec §9).
  - §2 Hypothesis: H₀: composite β ≤ 0; H₁: composite β > 0 (one-sided permitted given pre-pinned positive sign expectation; spec must justify the one-sided choice from the literature, not from observed data).
  - §3 Falsification criteria — three-way exhaustive: PASS-trigger (composite β̂ > 0 at p ≤ 0.05 one-sided), FAIL-trigger (composite β̂ ≤ 0 at p > 0.05), ESCALATE-trigger MUST be pre-pinned with concrete numerics (per RC D3 + SPM D2 convergent BLOCK):
    - First clause (precise): composite β̂ > 0 with p ∈ (0.05, 0.20] one-sided
    - Second clause (precise — REQUIRED): "composite β̂ near zero with high tail asymmetry" must be replaced with concrete numbers — (a) numeric definition of "near zero" (e.g., `|β̂| / SE < 0.5`), (b) numeric definition of "high tail asymmetry" (e.g., `|skew(residuals)| > 1.0` OR `excess kurtosis > 3.0`), (c) rationale for each numeric choice from literature or pre-data conjecture only — NEVER from observed sample statistics
    - ESCALATE-PASS threshold MUST also be pre-pinned per SPM D2: "quantile β̂(0.90) > 0 at p ≤ 0.10 one-sided OR GARCH-X mean-β > 0 at p ≤ 0.10 one-sided OR EVT extreme-quantile β̂ > 0 at p ≤ 0.10" — or alternative concrete numerics, but NEVER "credible" or other soft language
  - §4 Sample-selection: monthly **2015-01** through 2026-03 (revised per spec §9.10 CORRECTIONS-α' 2026-04-28 PM; chain: 2008-01 pre-revision → 2010-01 per CORRECTIONS-α §9.9 → 2015-01 per CORRECTIONS-α' §9.10 — Marco-2005-era Empalme harmonization gap surfaced by Step 0 pre-flight; second HALT surfaced when DANE Empalme RAMA4D 2010-2014 contained Rev.3 not Rev.4 codes (column-header verification was insufficient; lesson at `feedback_schema_pre_flight_must_verify_values`); user picked Option α from disposition memo (first HALT) and Option α' from second disposition memo); excludes most recent ≤2 months for data-availability lag; N expected ≈ 135 pre-lag, ≈ 123 post-lag-12; N_MIN_OBS = 75 (Phase-A.0 floor) — HALT-disposition if realized N < 75 after methodology-break treatment.
  - §5 Methodology — primary OLS specification:
    `logit(Y_t) = α + Σ_{k∈{6,9,12}} β_k · log(COP_USD_{t-k}) + ε_t`
    Composite β = β_6 + β_9 + β_12 (the lag window bounded by literature 6-12mo offshoring transmission).
  - §6 Methodology-break disposition (pre-pinned):
    - Primary: apply DANE empalme factor for Marco-2005 → Marco-2018 reconciliation (DANE-published nota técnica)
    - Robustness 1: 2021 regime dummy instead of empalme
    - BANNED: restrict-to-≥2022 (collapses N to ~51, below N_MIN=75 — anti-fishing-violation if invoked)
  - §7 Robustness checks pre-committed:
    - R1: 2021 regime dummy (alternative methodology-break treatment)
    - R2: Y narrow (CIIU J+M+N only — BPO-specific subset)
    - R3: raw OLS (no logit transform) — bounded-range diagnostic
    - R4: HAC SE (Newey-West, lag 12) — autocorrelation diagnostic
  - §8 Verdict-decision tree — deterministic mapping from (composite β̂ sign × p-value × R-row consistency) to {PASS, FAIL, ESCALATE, SUBSTRATE_TOO_NOISY}. SUBSTRATE_TOO_NOISY triggers if R-rows produce sign-flipping > 50% (the panel cannot stably estimate the relationship).
  - §9 Anti-fishing invariants: no threshold tuning, no Y-construction post-data, no event-set re-curation, HALT-disposition path; spec sha256 pin governs all downstream artifacts.

- [ ] **Step 2: Orchestrator reviews draft for code-agnosticism + completeness.** No "TBD"; verdict-tree deterministic given any (β̂, p, robustness consistency) input; one-sided test justification grounded in literature not data. **Concrete sub-checklist for verdict-tree determinism:** (a) walk every leaf of the verdict tree with a synthetic (β̂, p, R-consistency) tuple; (b) confirm exactly one verdict fires per tuple; (c) confirm no leaf maps to "TBD" or "see specialist judgment"; (d) confirm ESCALATE second clause is concrete numerics not soft language.

- [ ] **Step 3: Compute spec sha256.** Hash the spec file content with `decision_hash` field set to sentinel; record hash in spec frontmatter. Document the sentinel-hash protocol per the P1 spec precedent.

### Task 0.2: 2-wave verification on spec

**Owner:** Foreground Orchestrator dispatches; Reality Checker (Wave 1) + Model QA Specialist fresh instance (Wave 2) execute in parallel

**Files:**
- Read: `contracts/docs/superpowers/specs/2026-04-27-simple-beta-pair-d-design.md`

- [ ] **Step 1: Dispatch Reality Checker (Wave 1).** Charge: evidence grounding (literature anchors actually cited from BPO research note); anti-fishing rigor (no soft thresholds, no escape hatches in escalation contingency, methodology-break disposition properly pinned); production-vs-prototype framing (this is Stage 1 only).

- [ ] **Step 2: Dispatch Model QA Specialist (Wave 2, fresh instance — neither the spec author nor any prior reviewer).** Charge: methodology integrity (one-sided test justified from literature, lag composite specification statistically sound, logit-vs-raw-OLS choice justified, methodology-break empalme treatment statistically defensible, ESCALATE-trigger precisely defined). **Specifically MUST verify per RC D3 + SPM D2 convergent BLOCK:** the ESCALATE second-clause numbers (`|β̂|/SE` bound + tail-asymmetry bound) AND the ESCALATE-PASS threshold numbers are (a) pre-data concrete numerics (no soft language); (b) citation-grounded or pre-data-conjecture-grounded (NEVER observed-sample-grounded); (c) sha256-pinned with the rest of the spec.

- [ ] **Step 3: Integrate findings per v2 verdict-combination rule.** Revisions applied inline; spec sha256 re-computed if revisions are normative; per-WA-precedent BLOCK from either wave halts and re-dispatches, PASS-WITH-REV proceeds with integration.

### Task 0.3: Commit spec

**Owner:** Foreground Orchestrator

**Files:**
- Modify: spec frontmatter (decision_hash + verifier_v3_*)

- [ ] **Step 1: Update spec frontmatter** with final sha256, both verifier verdicts, verifier-agent IDs.

- [ ] **Step 2: Commit spec** with `Doc-Verify: wave1=<verdict>/<RC-id> wave2=<verdict>/<MQS-id>` trailer per the user-intended v2 audit-trail rule (spirit-over-letter).

- [ ] **Step 3: Quote spec sha256 in this plan's frontmatter.**

---

## Phase 1: GEIH data pull (Y construction)

> **Parallel-dispatch annotation:** Tasks 1.1 (GEIH Y) and 1.2 (COP/USD X) operate on independent data sources; dispatch them as two parallel Data Engineer subagent instances. Task 1.3 (alignment) is sequential after both land.

### Task 1.1: GEIH micro-data pull + Y construction

**Owner:** Data Engineer

**Files:**
- Create: `contracts/.scratch/simple-beta-pair-d/data/geih_young_workers_services_share.parquet`
- Create: `contracts/.scratch/simple-beta-pair-d/data/geih_young_workers_narrow_share.parquet`
- Create section in `DATA_PROVENANCE.md`

- [ ] **Step 0 (CLOSED per Task 1.1 Step 0 schema-stability HALT 2026-04-28; Option α picked):** The schema-stability pre-flight surfaced a non-pinnable break-point at 2008-01→2009-12 (DANE Empalme nota técnica covers 2010-01→2020-12 only; pre-2010 requires author-judgment Rev.3.1→Rev.4 crosswalk). Disposition memo at `contracts/.scratch/2026-04-28-task-1.1-step-0-schema-pathological-disposition.md` enumerated 5 pivot options; user picked Option α (shorten window to 2010-01 → 2026-03). Spec §4 sample window updated; spec §9.9 CORRECTIONS block records audit trail. **Pinned harmonization rules table for Option α** (DANE-canonical at every break-point):

  | Era | Source catalog | Schema notes | FEX field | Sector field |
  |---|---|---|---|---|
  | 2015-01 → 2020-12 (72 mo) | GEIH Empalme catalogs cid 755-765 (per-year ZIPs, but only the 2015-2020 subset under Option α' per §9.10 — Empalme files for 2010-2014 ship `RAMA4D` with **CIIU Rev.3 codes** and are OUT OF SCOPE) | Comma-separated, UTF-8, single-file (no Cabecera/Resto split); FEX_C pre-incorporates empalme factor; sector codes Rev.4-pre-applied via `RAMA4D_R4` column (DANE-canonical from 2015-01 onward; verified by raw value-content inspection per `feedback_schema_pre_flight_must_verify_values`) | `FEX_C` | `RAMA4D_R4` |
  | 2021-01 → 2021-12 (12 mo) | Marco-2018 semester archives within cid 701 (`GEIH - Marco-2018(I.Semestre).zip` + `GEIH_Marco_2018(II. semestre).zip`) | Schema matches 2022+ Marco-2018 native; preferred over per-month native files for 2021 | `FEX_C18` | `RAMA4D_R4` |
  | 2022-01 → 2026-03 (51 mo) | Marco-2018 native per-month catalogs (cid 819, 853, 900, etc.) | 2022-2025: comma-separated, Latin-1 encoding (mojibake risk on UTF-8 read); 2026: semicolon-separated, UTF-8, new prefix columns `PERIODO`, `MES`, `PER` ahead of `DIRECTORIO` | `FEX_C18` | `RAMA4D_R4` |

  Stable primary keys across all eras: `DIRECTORIO`, `SECUENCIA_P`, `ORDEN`. Unified column aliases at ingest: `_fex_c` ← {FEX_C, FEX_C18}; `_rama4d_rev4` ← {RAMA4D, RAMA4D_R4}; `P6040` (age) is stable. Per Empalme-catalog construction: no separate empalme transformation step needed downstream — the published FEX_C already incorporates it.

- [ ] **Step 1: Specialist downloads GEIH monthly micro-data** for **2015-01 through 2026-03** from DANE catalogues per the Step 0 era table above (revised window per CORRECTIONS-α' per spec §9.10; supersedes the CORRECTIONS-α 2010-01 start). Apply the per-era schema-harmonization rule (column rename + encoding selection) at ingest time. ~135 monthly files expected.

- [ ] **Step 2: Specialist filters per spec §4 sample-selection rules** — youth band 14-28 (Ley 1622/2013), employed status (Ocupado=1), then split into broad-services (CIIU Rev.4 A.C. sections G-T) and narrow-services (J+M+N) subsets.

- [ ] **Step 3: Specialist computes monthly Y_t** for both subsets: Y_broad = (count young employed in G-T / count all young employed); Y_narrow = (count young employed in J+M+N / count all young employed). Persists each to its parquet with schema `(timestamp_utc, Y_raw, Y_logit, n_young_employed, n_young_in_sector)`.

- [ ] **Step 4: Methodology-break treatment is automatic per Option α' + per spec §6.** Under Option α', the in-scope GEIH Empalme catalogs (cid 755-765) for **2015-2020** (the empalme factor is published for the full 2010-2020 window per nota técnica §3.3, but 2010-2014 is OUT OF SCOPE under Option α' per spec §9.10 because the Rev.4 sector coding `RAMA4D_R4` is available 2015-2020 only) already pre-incorporate the empalme factor in `FEX_C`; no separate empalme transformation is needed downstream. Marco-2018 semester archives for 2021 + Marco-2018 native for 2022+ already use the post-Marco-2018 frame. Document this in `DATA_PROVENANCE.md` with the DANE nota técnica URL (`https://www.dane.gov.co/files/investigaciones/boletines/ech/ech/Nota-tecnica-empalme-series-GEIH.pdf`) for traceability; the §6 R1 (2021 regime dummy) robustness option remains available as an alternative methodology-break treatment.

- [ ] **Step 5: Specialist documents** all download URLs, filter steps, sample sizes per month, empalme application in `DATA_PROVENANCE.md`.

- [ ] **Step 6: Reality Checker spot-check** — independently pull 3 random months from DANE, recompute Y on each, confirm match with the parquet. No silent data corruption. **Recovery path on discrepancy (per RC D-adjacent + SPM Failure Mode 2):** If RC spot-check flags discrepancy, HALT, dispatch Senior Developer to triangulate (re-pull from DANE + re-execute DE pipeline + diff); if root cause is DE error, redispatch DE with concrete failure case; if root cause is DANE-side data change, HALT to disposition memo per anti-fishing protocol.

### Task 1.2: COP/USD panel from FX-vol-CPI pipeline

**Owner:** Data Engineer

**Files:**
- Create: `contracts/.scratch/simple-beta-pair-d/data/cop_usd_panel.parquet`

- [ ] **Step 1: Specialist reuses closed FX-vol-CPI pipeline** Banrep COP/USD daily series at `contracts/notebooks/fx_vol_cpi_surprise/Colombia/`. Either re-pulls from Banrep API or copies-with-attribution from the closed pipeline's data directory.

- [ ] **Step 2: Specialist aggregates daily → monthly** end-of-month spot rate; documents the aggregation convention (last business day of month).

- [ ] **Step 3: Specialist constructs lag panel** with k ∈ {6, 9, 12} months; computes log(COP_USD_{t-k}) for each lag column; drops leading rows where lag is undefined.

- [ ] **Step 4: Specialist documents source + transformation** in `DATA_PROVENANCE.md`.

### Task 1.3: Panel alignment + N verification

**Owner:** Data Engineer

**Files:**
- Create: `contracts/.scratch/simple-beta-pair-d/data/panel_combined.parquet`

- [ ] **Step 1: Specialist inner-joins** Y_broad + Y_narrow + X lag panel on monthly timestamp.

- [ ] **Step 2: Specialist verifies N** ≥ N_MIN=75 after join (expected ≈ 123 = 135 − 12 leading months lost to lag, per CORRECTIONS-α'; chain: ≈ 206 original → ≈ 183 CORRECTIONS-α → ≈ 123 CORRECTIONS-α'). **HALT protocol per `feedback_pathological_halt_anti_fishing_checkpoint` (per RC D4):** If N < 75, raise typed exception `PairDSampleStructurallyPathological`; Foreground Orchestrator files disposition memo at `contracts/.scratch/2026-04-XX-pair-d-N-pathological-disposition.md` enumerating ≥3 pivot options (e.g., shorter lag window, narrower Y, alternative methodology-break treatment); surfaces to user; user picks pivot; CORRECTIONS block lands in next plan revision; 3-way review of CORRECTIONS revision. Auto-selection of pivot is anti-fishing-banned.

- [ ] **Step 3: Specialist persists final panel** with schema `(timestamp_utc, Y_broad_logit, Y_broad_raw, Y_narrow_logit, Y_narrow_raw, log_cop_usd_lag6, log_cop_usd_lag9, log_cop_usd_lag12, n_young_employed, n_young_in_services_broad, n_young_in_services_narrow)`.

- [ ] **Step 4: Reality Checker QC** — spot-check 5 random rows across the full window; flag any anomalies (outliers, missing data, schema violations).

- [ ] **Step 5: Commit data directory + DATA_PROVENANCE.md** with `Doc-Verify: rc=<RC-spot-check-verdict>/<RC-id>` trailer (per SPM D9 — data commits get RC-only trailer since no domain-specialist Wave-2 applies to raw data).

---

## Phase 2: OLS execution + result tables

> **Phase 2 dependency annotation (per SPM D3 correction):** Tasks 2.1 → 2.2 → 2.3 are SEQUENTIAL (not parallel as the original plan implied). Task 2.3 R-rows feed back into Task 2.2's verdict per spec §8 SUBSTRATE_TOO_NOISY rule (sign-flipping > 50% across R-rows triggers SUBSTRATE_TOO_NOISY regardless of primary β̂); therefore Task 2.3 must complete before Task 2.2's final verdict is recorded. Task 2.4 is conditional on Task 2.2 verdict = ESCALATE.
>
> **Trio-HALT taxonomy (per SPM D7):** Trio HALTs are orchestrator-resolvable IF the question maps to a pre-pinned spec section. Trio HALTs require user input IF (a) spec gap discovered post-data, (b) data anomaly with no spec-pinned disposition, (c) verdict-tree leaf not anticipated. Cases (a) and (c) trigger spec-amendment loop with re-sha256 per the anti-fishing protocol.
>
> **v2.4 CORRECTIONS-β implementation note (2026-04-28 PM late evening):** Phase 2 was originally executed as standalone Python scripts (`contracts/.scratch/simple-beta-pair-d/scripts/task_2_1_primary_ols.py`, `task_2_2_robustness.py`) committed at HEAD `bce431544`. The script-form execution produced byte-deterministic JSON artifacts (`primary_ols.json` sha256 `d4790e743…dcf`, `robustness_pack.json` sha256 `67dd18cfeb2584fa…b078904`) but bypassed the trio-checkpoint discipline that this plan's Tasks 2.2-2.3 mandate per memory `feedback_notebook_trio_checkpoint` (NON-NEGOTIABLE). Phase-3 Senior Developer review (ACCEPT_WITH_REMEDIATION) flagged this as an unrecorded process violation. **User-chosen remediation: Option β** — re-execute Phase 2 as notebooks with proper trio structure under user "same patterns" override (3-notebook scheme mirroring `contracts/notebooks/fx_vol_cpi_surprise/Colombia/`: NB01 data EDA + NB02 estimation + NB03 tests/sensitivity; plan's NB04 escalation skipped — Clause-A gate did not fire). Numerical content reproduces script-form JSON byte-deterministically (sha256 round-trip asserted in NB02 §2 + NB03 §6). Spec sha256 `964c62cca…ef659` is NOT bumped (per §9.7 governance, the Phase-2 numerical artifacts retain v1.3.1 governance; this plan revision documents the documentation-layer remediation only). The script-form artifacts under `scripts/` + `results/` are preserved as the canonical Phase-2 numerical record; the notebook-form re-execution under `notebooks/` is the trio-disciplined documentation re-emission.

### Task 2.1: Notebook scaffolding

**Owner:** Analytics Reporter

**Files:**
- Create: `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/env.py`, `references.bib`, notebooks 01-05 (skeletons only). **Note (v2.4 path corrections):** original scaffold landed at `contracts/.scratch/simple-beta-pair-d/notebooks/` per a literal read of an obsolete plan path; first move (PR #76, HEAD `1999e18c6`) relocated to `contracts/notebooks/abrigo_pair_d/` to match the canonical `contracts/notebooks/<project>/` convention; second move (PR #77) renamed to `bpo_offshoring_fx_lag/Colombia/` to mirror the naming convention of `fx_vol_cpi_surprise/Colombia/` (outcome-name `bpo_offshoring` + driver-name `fx` + qualifier `lag` + country scope subfolder). The `bpo_offshoring_fx_lag` name encodes the actual hypothesis under test: the BPO offshoring labor-absorption channel is FX-lag-driven (Baumol → US-Colombia wage arbitrage → BPO offshoring at 6-12mo lag → young-worker services share rises).

- [ ] **Step 1: Specialist sets up env.py** following the existing `contracts/notebooks/abrigo_y3_x_d/env.py` pattern (parents-fix landed at commit `865402c2c` per CLAUDE.md). Paths point to the simple-β-pair-d directory.

- [ ] **Step 2: Specialist creates references.bib** with: Mendieta-Muñoz 2017 (Colombia premature deindustrialization); Rodrik 2016; McMillan-Rodrik 2011; Beerepoot-Hendriks 2013; this plan's spec (with sha256-pin); BPO research note path; GEIH feasibility report path.

- [ ] **Step 3: Specialist creates notebook skeletons** (01-05) with section headers matching spec analysis sections. Each notebook starts with the 4-part citation block (`feedback_notebook_citation_block`) for its first decision.

- [ ] **Step 4: Commit scaffolding only.** No analysis content yet.

### Task 2.2: Notebook 03 — primary OLS (trio-checkpoint discipline)

**Owner:** Analytics Reporter (with mandatory trio-checkpoint HALTs per `feedback_notebook_trio_checkpoint`)

**Files:**
- Modify: `notebooks/03_ols_estimate.ipynb`
- Create: `output/PRIMARY_RESULTS.md`

> **Trio anatomy reminder (NON-NEGOTIABLE):** Each trio is `(why-markdown → code-cell → interpretation-markdown)`; HALT for orchestrator review after each trio. Do NOT collapse to code-only cells.

- [ ] **Step 1: First trio — load panel + descriptive stats.** Why-block (citation per spec); code cell loads parquet + computes summary stats (N, Y range, X range, missing-data check); interpretation reports panel shape + sanity check. **HALT.**

- [ ] **Step 2: Second trio — primary OLS estimate.** Why-block (logit transform per spec §5; lag composite per spec §5); code cell runs `statsmodels` OLS of `Y_broad_logit` on `log_cop_usd_lag6 + log_cop_usd_lag9 + log_cop_usd_lag12 + intercept`; interpretation reports β̂_6, β̂_9, β̂_12, composite β̂ = sum, t-stat, p-value (one-sided per spec). **HALT.**

- [ ] **Step 3: Third trio — verdict per spec decision tree.** Why-block (spec §3 + §8 verdict mapping); code cell evaluates the spec decision tree on observed (composite β̂, p, sign); interpretation reports verdict ∈ {PASS, FAIL, ESCALATE, SUBSTRATE_TOO_NOISY}. **HALT.**

- [ ] **Step 4: Orchestrator reads PRIMARY_RESULTS.md** and confirms verdict-tree mapping is deterministic per spec.

- [ ] **Step 5: Commit notebook 03 + PRIMARY_RESULTS.md** with `Doc-Verify: orchestrator-only-pre-Phase-3 (3-way review deferred to Task 3.2)` trailer per SPM D9 (notebook commits are intentionally trailer-light pre-Phase-3; Task 3.2 audits notebooks retrospectively).

### Task 2.3: Notebook 05 — robustness pass (always)

**Owner:** Analytics Reporter (trio-checkpoint discipline)

**Files:**
- Modify: `notebooks/05_robustness.ipynb`
- Create: `output/ROBUSTNESS_RESULTS.md`

> **Trio anatomy reminder:** Same `(why-markdown → code-cell → interpretation-markdown)` discipline as Task 2.2; HALT after each trio.

- [ ] **Step 1: First trio — R1 (2021 regime dummy).** Re-run primary OLS with 2021 dummy instead of empalme. Report β̂. **HALT.**

- [ ] **Step 2: Second trio — R2 (Y narrow).** Re-run primary OLS on Y_narrow_logit. Report β̂. **HALT.**

- [ ] **Step 3: Third trio — R3 (raw OLS, no logit).** Bounded-range diagnostic. Report β̂. **HALT.**

- [ ] **Step 4: Fourth trio — R4 (HAC SE).** Newey-West HAC(12) standard errors on the primary specification. Report adjusted t-stat. **HALT.**

- [ ] **Step 5: Fifth trio — robustness summary.** Sign-consistency check across R1-R4 vs primary; classify as AGREE / MIXED / DISAGREE per spec convention. Output ROBUSTNESS_RESULTS.md. **HALT.**

- [ ] **Step 6: Commit notebook 05 + ROBUSTNESS_RESULTS.md** with `Doc-Verify: orchestrator-only-pre-Phase-3 (3-way review deferred to Task 3.2)` trailer per SPM D9.

### Task 2.4: Notebook 04 — escalation if needed (CONDITIONAL)

**Owner:** Analytics Reporter (only if Task 2.2 verdict = ESCALATE)

**Files:**
- Modify (only if triggered): `notebooks/04_escalation_if_needed.ipynb`
- Create (only if triggered): `output/ESCALATION_RESULTS.md`

- [ ] **Step 1: Conditional execution gate.** If Task 2.2 verdict ≠ ESCALATE, skip Task 2.4 entirely and proceed to Phase 3. Document the skip in MEMO.md (Phase 3) as "Escalation not triggered; primary verdict was {PASS / FAIL / SUBSTRATE_TOO_NOISY}."

- [ ] **Step 2: Trio — quantile regression.** Why-block (spec §3 ESCALATE definition); `statsmodels` QuantReg on Y_broad_logit at q ∈ {0.10, 0.25, 0.50, 0.75, 0.90}; interpretation reports tail β̂ asymmetry (does the upper-tail β̂ differ from median?). **HALT.**

- [ ] **Step 3: Trio — GARCH-X variance specification.** Why-block; `arch` package GARCH(1,1) with lagged log COP/USD as exogenous mean-shifter; interpretation reports β̂_X in mean equation + variance asymmetry. **HALT.**

- [ ] **Step 4: Trio — EVT lower-tail.** Why-block; block-maxima or POT (peaks-over-threshold) on Y_logit residuals from primary OLS; interpretation reports tail-index + extreme-quantile β̂. **HALT.**

- [ ] **Step 5: Trio — escalation verdict.** Composite call: evaluate the spec §3 ESCALATE-PASS threshold disjunction on the observed quantile / GARCH-X / EVT estimates (per spec §3 the threshold is `quantile β̂(0.90) > 0 at p ≤ 0.10 one-sided OR GARCH-X mean-β > 0 at p ≤ 0.10 one-sided OR EVT extreme-quantile β̂ > 0 at p ≤ 0.10` — soft language like "credible" is anti-fishing-banned per spec §3 + §9). Classify as ESCALATE-PASS / ESCALATE-FAIL based on whether the spec-pinned disjunction fires. **HALT.**

- [ ] **Step 6: Commit notebook 04 + ESCALATION_RESULTS.md** with `Doc-Verify: orchestrator-only-pre-Phase-3 (3-way review deferred to Task 3.2)` trailer per SPM D9.

---

## Phase 3: Memo + verdict + 3-way review

### Task 3.1: Draft result memo

**Owner:** Analytics Reporter

**Files:**
- Create: `contracts/.scratch/simple-beta-pair-d/output/MEMO.md`
- Create: `contracts/.scratch/simple-beta-pair-d/output/gate_verdict.json`

- [ ] **Step 1: Specialist drafts memo** with sections (Reads, per SPM D10: PRIMARY_RESULTS.md, ROBUSTNESS_RESULTS.md, ESCALATION_RESULTS.md if present, spec sha256, panel_combined.parquet schema, all notebooks 01-05):
  - §1 Spec sha256 pin (quoted from Phase 0)
  - §2 Pair D recap (Y, X, mechanism, lit-grounded sign expectation)
  - §3 Sample summary (N, time range, methodology-break treatment per spec §6)
  - §4 Primary result + verdict per spec decision tree (composite β̂, p, sign)
  - §5 Robustness summary (R1-R4 + AGREE/MIXED/DISAGREE classification)
  - §6 Convex-payoff escalation results IF triggered (ESCALATE-PASS / ESCALATE-FAIL); IF not triggered, document the skip
  - §7 Honest interpretation: did the empirical β confirm the lit-grounded sign expectation? If FAIL, did escalation rescue (pre-pinned, NOT post-hoc — the framework pre-authorized escalation in CLAUDE.md before any data was pulled)?
  - §8 Implications for next stage: M sketch (PASS or ESCALATE-PASS) / kill Pair D (FAIL after ESCALATE-FAIL — revisit other pairs from BPO research note 5-pair ranking) / refine (SUBSTRATE_TOO_NOISY — identify methodology improvements for P_D2)

- [ ] **Step 2: Specialist writes machine-readable gate_verdict.json** with: `spec_sha256`, `primary_beta_composite`, `primary_pvalue`, `primary_verdict`, `escalation_triggered`, `escalation_verdict`, `robustness_consistency`, `recommended_next_step`.

### Task 3.2: Three-way implementation review

**Owner:** Foreground Orchestrator dispatches; Code Reviewer + Reality Checker + Senior Developer execute in parallel per `feedback_implementation_review_agents`

**Files:**
- Read: MEMO.md, gate_verdict.json, all upstream artifacts (notebooks 01-05 if present, data parquets, spec)

- [ ] **Step 1: Dispatch Code Reviewer** on notebooks 01-05. Charge: implementation matches spec methodology; no silent-test-pass patterns; no threshold tuning post-data; trio-checkpoint citation blocks present.

- [ ] **Step 2: Dispatch Reality Checker** on memo + gate_verdict.json. Charge: every memo claim supported by a result-table cell; no narrative softening of FAIL or ESCALATE-FAIL; next-step recommendation maps cleanly from verdict per spec decision tree.

- [ ] **Step 3: Dispatch Senior Developer** on notebooks + memo together. Production-readiness check — could a fresh engineer re-run with only the spec + this notebook + the data?

- [ ] **Step 4: Integrate findings.** Per `feedback_pathological_halt_anti_fishing_checkpoint`, any reviewer flag of threshold-tuning / Y-re-construction / escalation-rescue-claim triggers HALT-disposition memo before any revision lands.

### Task 3.3: Final commit + CLAUDE.md update

**Owner:** Foreground Orchestrator

**Files:**
- Modify: MEMO.md, gate_verdict.json (post-review revisions)
- Modify: `.worktree/ranFromAngstrom/CLAUDE.md` Active iteration block

- [ ] **Step 1: Apply review revisions** that don't change verdict, tune thresholds, or redefine Y/X.

- [ ] **Step 2: Commit final memo** with `Doc-Verify:` trailer (Code Reviewer + Reality Checker + Senior Developer agent IDs).

- [ ] **Step 3: Update CLAUDE.md Active iteration block** with verdict + next-stage disposition pointer. CLAUDE.md edit triggers Reality Checker + Workflow Architect 2-wave per v2 default for governance writes; dispatch them on the diff before commit. Commit with `Doc-Verify: wave1=<RC-verdict>/<RC-id> wave2=<WA-verdict>/<WA-id>` trailer per SPM D9.

- [ ] **Step 4: Save memory entry** at `~/.claude/.../memory/project_simple_beta_pair_d_complete.md` with verdict + key findings + path forward. Memory writes are out of scope for the 2-wave rule.

---

## Phase 4: Disposition

Goal: surface verdict to user; user decides next-stage pivot.

### Task 4.1: User decision

**Owner:** Foreground Orchestrator

**Files:**
- Create: `contracts/.scratch/simple-beta-pair-d/output/DISPOSITION.md`

- [ ] **Step 1: Surface MEMO.md verdict + gate_verdict.json to user** with concise disposition options:
  - **PASS** → unblock M sketch (Stage 2 of framework) for Pair D's (Y, X)
  - **ESCALATE-PASS** → unblock M sketch with convex-payoff documentation in the M sketch
  - **FAIL after ESCALATE-FAIL** → consider Pair D dropped; per SPM D8: dispatch fresh Trend Researcher to re-rank Pair A/B/C/E given Pair-D-FAIL evidence (which mechanism assumption broke?); the re-ranking memo is the input artifact for the next iteration's Phase 0 spec
  - **SUBSTRATE_TOO_NOISY** → identify methodology improvements for P_D2 (Pair D revision); options include longer time window, narrower Y, alternative X transformation

- [ ] **Step 2: User chooses next step.**

- [ ] **Step 3: Persist decision to** `contracts/.scratch/simple-beta-pair-d/output/DISPOSITION.md` with timestamp + chosen-next-step + verbatim user-rationale paragraph. Commit with `Doc-Verify:` trailer (spirit-over-letter). This file is the auditable handoff — mirrors the Phase-A.0 EXIT verdict pattern.

- [ ] **Step 4 (M-sketch handoff per SPM D11): If escalation chosen (M sketch), invoke writing-plans for the M-sketch plan with explicit handoff payload:** (a) Pair D verdict + composite β̂ + p; (b) spec sha256 of this Stage-1 spec; (c) DISPOSITION.md path; (d) Panoptic-pool eligibility constraint per CLAUDE.md framework M-clause; (e) ideal-scenario-modeling permission per CLAUDE.md framework. This avoids forgetting Stage-1 evidence on the Stage-2 doorstep.

- [ ] **Step 5 (closure-archival per RC D6): If verdict = FAIL after ESCALATE-FAIL OR SUBSTRATE_TOO_NOISY AND user disposition = kill-Pair-D**, archive `contracts/.scratch/simple-beta-pair-d/` to `contracts/.scratch/archive-2026-MM-pair-d/` per the Phase-A.0 archive convention; update CLAUDE.md Active iteration block to point to archive location for posterity. If pivot/refine chosen, archive only on the next Pair commit (avoid premature archival).

---

## Self-review checklist (run by orchestrator before commit of THIS plan)

- **Spec coverage:** does every requirement in the GEIH feasibility report (youth=14-28; CIIU G-T primary + J+M+N sensitivity; methodology-break empalme; logit-Y; ~218 obs feasibility-universe / ~195 CORRECTIONS-α / ~135 CORRECTIONS-α' / N≈123 post-lag-12; CIIU Rev.3→Rev.4 + Marco-2005→Marco-2018 schema-stability with value-content verification per `feedback_schema_pre_flight_must_verify_values`) map to a task here? **Verified — Task 0.1 spec, Task 1.1 Step 0 schema-stability pre-flight (header), Task 1.1 Step 1 ingest-time value-content verification, Task 1.3 N verification.**

- **Placeholder scan:** zero "TBD" / "TODO" / "fill in details" / "similar to Task N" / "implement appropriate handling". **Verified — all steps name a specialist deliverable or dispatch with explicit charge.**

- **Code-agnosticism:** zero executable code blocks per `feedback_no_code_in_specs_or_plans`. **Verified — equation notation in §5 is methodology specification, not executable code; specialist-side tech-stack notes are advisory.**

- **Specialist coverage:** every task names an owner per `feedback_specialized_agents_per_task`. **Verified — Model QA Specialist (spec), Data Engineer (data), Analytics Reporter (notebooks + memo), Reality Checker / Code Reviewer / Senior Developer / Workflow Architect (reviews).**

- **Anti-fishing discipline:** spec sha256 pin, threshold pre-registration, HALT-disposition path, 3-way memo review regardless of verdict, methodology-break pre-pinning to {empalme / 2021-dummy} with restrict-to-≥2022 BANNED. **Verified — Phase 0 + Task 1.1 Step 4 + Task 3.2 + spec §6 + spec §9.**

- **2-wave doc verification (v2 spirit-over-letter):** spec write triggers RC + Model QA Specialist (Task 0.2); plan write (this file) triggers RC + Senior Project Manager (orchestrator dispatches before commit); memo triggers Code Reviewer + Reality Checker + Senior Developer (Task 3.2); CLAUDE.md update triggers RC + Workflow Architect (Task 3.3 Step 3). **Verified.**

- **Type / name consistency:** `Y_broad`, `Y_narrow`, `Y_logit`, `Y_raw`, `log_cop_usd_lag{6,9,12}` naming consistent across spec, notebooks, memo, gate_verdict.json. **Verified.**

- **Stage discipline:** plan executes Stage 1 only; Stage 2 (M sketch) and Stage 3 (deployment) explicitly out of scope. **Verified — frontmatter + Phase 4 routing.**

---

## Execution handoff

Plan complete pending 2-wave verification per the user-intended v2 rule.

**Two execution options:**

1. **Subagent-Driven (recommended)** — orchestrator dispatches a fresh specialist per task per the named owners, reviews between tasks, mandatory trio-checkpoint HALTs in Phase 2.

2. **Inline Execution** — execute tasks in this session via `superpowers:executing-plans`, batch with checkpoints. Higher context burn; harder to enforce specialist discipline.

**Recommended: Subagent-Driven**, given the trio-checkpoint discipline mandated by `feedback_notebook_trio_checkpoint` and the multi-specialist design of the plan.
