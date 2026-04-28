---
spec_version: 1.3.1
decision_hash: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
decision_hash_protocol: sha256 computed against this file with `decision_hash` field set to the sentinel `<to-be-pinned-after-CORRECTIONS-alpha-prime-3way-cleanup>`. To re-verify, replace the pinned hash with the sentinel string and recompute sha256; should match.
prior_decision_hash_v1.1: f74b2ac577d5182842116a8798f307a610c185f1e6e259b8530e2ec266141728  # superseded by CORRECTIONS-α v1.2 per §9.9
prior_decision_hash_v1.2: 19bdaed9b966232588bfc0034264d9ed32dbb3ab9fbd7e6c9b8a131ff8b7b7a4  # superseded by 3-way review cleanup v1.2.1 per §9.9 (D1+D2+D3+SPM#1+SPM#3+MQS-NB-1 textual fixes)
prior_decision_hash_v1.2.1: b90be50bd9c68b7ea2000c33f6ea34169ea01995391baa8692cf95d13d6f4c6d  # superseded by CORRECTIONS-α' v1.3 per §9.10 (Task 1.1 Step 1 second HALT — Empalme RAMA4D 2010-2014 ships Rev.3 codes not Rev.4; window shortened to 2015-01)
prior_decision_hash_v1.3: 4611abc491258fd92fe83231b956bb356b1b49453b33bd9e2c4dcb20ed486b57  # superseded by CORRECTIONS-α' 3-way review cleanup v1.3.1 (RC R1 §9.10 rejected-pivots count includes α''' operational-impossibility; plan-only D-PROP-1/2/3 fixes flagged HIGH-convergent by MQS+SPM applied in same commit)
dependent_plan: contracts/docs/superpowers/plans/2026-04-27-simple-beta-pair-d-implementation.md
verifier_v1_wave1: PASS-WITH-REVISIONS (Reality Checker, 2026-04-27, 3 NB defects D1/D2/D3 + 4 OOS — D1+D3 closed in v1.1; D2 closed via CLAUDE.md fix in same commit; OOS deferrable)
verifier_v1_wave2: PASS-WITH-REVISIONS (Model QA Specialist fresh instance, 2026-04-27, 5 NB craftsmanship adds R1-R5 — all closed in v1.1; ZERO BLOCKERs, ZERO anti-fishing violations)
verifier_v1.1: pending re-dispatch (RC waived re-dispatch for craftsmanship-only adds; spec sha256 will recompute)
revision_history:
  - v1 2026-04-27 initial draft (Model QA Specialist)
  - v1.1 2026-04-27 inline integration of RC D1 (§3.2 NOTE clarifier extending FAIL to (β>0, p>0.20, neither B fires)), D3 (§5.1 CIIU Rev.3.1→Rev.4 boundary handling), MQS R1 (§5.3 "delta method" → "linear-restriction variance c'Σc"), MQS R2 (§5.3 multicollinearity / negative covariance offset acknowledgment), MQS R3 (§5.1 logit-OLS vs Papke-Wooldridge / Ferrari-Cribari-Neto justification), MQS R4 (§6 empalme residual-bias on logit nonlinearity + CIIU classification), MQS R5 (§3.4 structural-disjunction MHT defense). RC D2 (CLAUDE.md "two-sided" → "one-sided" reconciliation) handled in same-commit CLAUDE.md edit. RC O1 (BPO research note copy to worktree .scratch/) handled in same commit.
  - v1.2 2026-04-28 CORRECTIONS-α revision per Task 1.1 Step 0 schema-stability HALT. User picked Option α from disposition memo (`contracts/.scratch/2026-04-28-task-1.1-step-0-schema-pathological-disposition.md`); §4 sample window 2008-01 → 2010-01 (data-availability-driven legal channel per §9.3); §9.9 new CORRECTIONS audit-trail block; spec sha256 superseded f74b2ac577d5…41728 → 19bdaed9b966…b7a4.
  - v1.2.1 2026-04-28 inline integration of CORRECTIONS-α 3-way review fixes — RC D2 (§9.3 stale window text), SPM #2 (convergent with RC D2), MQS NB-1 (§6 line 179 "2012-2021" → "2010-2020 (132 months)" factual correction), SPM #3 (this revision_history v1.2 entry added — was missing). Plan v2.2 fixes RC D1 (Task 0.1 Step 1 §4 sub-bullet stale), SPM #1 (line 22 + 391 "~218 obs" annotation), RC D3 (CLAUDE.md line 171 N precision) integrated in same commit. Spec sha256 19bdaed9b966…b7a4 → b90be50bd9c6…4c6d.
  - v1.3 2026-04-28 PM CORRECTIONS-α' revision per Task 1.1 Step 1 second HALT (typed exception `PairDEmpalmeSchemaContradictsHarmonizationPin`). DANE Empalme files for 2010-2014 ship Rev.3 codes in `RAMA4D` (column-header-only verification was insufficient; new memory `feedback_schema_pre_flight_must_verify_values` records the lesson). User picked Option α' from disposition memo (`contracts/.scratch/2026-04-28-task-1.1-step-1-empalme-rev3-vs-rev4-disposition.md`): shorten window to 2015-01 → 2026-03 (DANE-canonical Rev.4 throughout via `RAMA4D_R4`). Spec §4 window updated 2010-01 → 2015-01; spec §9.10 new CORRECTIONS-α' audit-trail block; §6 + §5.1 CIIU-revision boundary refs updated to 2015 cutoff. Plan v2.3 Task 1.1 Step 0 era table updated: "2010-01 → 2020-12 RAMA4D" row replaced with "2015-01 → 2020-12 RAMA4D_R4" (72 mo). Spec sha256 b90be50bd9c6…4c6d → 4611abc491258…6b57.
  - v1.3.1 2026-04-28 PM late inline integration of CORRECTIONS-α' 3-way review fixes — RC R1 (§9.10 rejected-pivots count: 6 → 7, includes α''' as operationally-impossible distinct from 6 methodological rejections). Plan v2.3.1 fixes (HIGH convergent finding from MQS H1 + SPM D-PROP-1: plan line 106 Task 0.1 §4 sub-bullet stale "≈195/≈183" → "≈135/≈123"; SPM D-PROP-2: plan Task 1.1 Step 4 empalme-window qualified to 2015-2020 in-scope per §9.10; SPM D-PROP-3: plan Architecture line 23 explicit pre-lag/post-lag distinction). Spec sha256 4611abc491258…6b57 → (computed at end of CORRECTIONS-α'-3way-cleanup pin).
---

# Simple-β Pair D — Pre-registered Design Spec

> **Code-agnostic by mandate** (project memory `feedback_no_code_in_specs_or_plans`). All thresholds and decision-tree branches are pinned in spec text BEFORE any data is pulled. ASCII / pseudo-equations are used to denote methodology; nothing in this document is executable.

---

## §1. Background and motivation

Within the Abrigo Operating Framework (worktree CLAUDE.md, "Abrigo Operating Framework" section), each (Y, M, X) iteration has a three-stage life: **Stage 1** empirical risk validation (does the underlying microeconomic risk admit a measurable β?), **Stage 2** ideal-scenario M sketch on Panoptic, **Stage 3** deployment. **This spec governs Stage 1 only.** Conflating stages is the Phase-A.0 failure mode that produced the parked P1 apparatus and is anti-fishing-banned.

The active iteration (CLAUDE.md "Active iteration" block, 2026-04-27 PM) commits Pair D from the BPO literature pass (`contracts/.scratch/2026-04-27-colombian-bpo-non-industrialization-hedge-research.md`, §6). Pair D is: **Y** = Colombian young-worker services-sector employment share (monthly, DANE GEIH), **X** = COP/USD nominal exchange rate (monthly, Banrep), **lag window** = 6–12 months. The Stage-1 question is whether Y responds positively to lagged X devaluation at conventional one-sided significance.

**Mechanism (literature-grounded, NOT data-grounded).** BPO research note §2 documents the premature-deindustrialization canon (Rodrik 2016; McMillan-Rodrik 2011; **Mendieta-Muñoz 2017** *Journal of Economic Structures* 6:24, "Trade liberalization and premature deindustrialization in Colombia"; ECLAC 2016): LATAM economies peak in manufacturing share at roughly half the GDP per capita of early industrializers and reallocate displaced labor *into* lower-productivity services. BPO research note §3 documents the Philippines comparator (**Beerepoot-Hendriks 2013** *Service Industries Journal* 33(11), "Employability of offshore service-sector workers in the Philippines: dead-end jobs?"; Errighi-Khatiwada-Bodwell ILO 2017): BPO absorbs young educated workers without enabling the wage-to-capital transition — workers self-perceive BPO as a stepping stone to *emigration*, not capital accumulation.

The transmission chain motivating the *positive* sign expectation is: **Baumol → US-Colombia wage arbitrage → US client offshoring decision → BPO sector demand absorption of young Colombian workers**. COP devaluation cheapens Colombian BPO labor in USD terms; US clients re-tender 6–12 months out per the standard offshoring contracting cycle (BPO research note §3 + §6); the Colombian BPO sector recruits young workers (BPO research note §3: "80% young, 67% women" Colombian BPO demographics, ProColombia). Baumol cost disease (Baumol-Bowen 1966; Baumol 2006 NBER WP 12218; Estache et al. 2021) anchors the long-run claim that BPO cannot productivity-match the broader economy, making its share of young employment depend on labor-cost-arbitrage shocks.

**Youth-band citation discrepancy — flagged.** BPO research note §6 quotes `(15–28)`; GEIH feasibility report §Q2 quotes `(14–28)` with statutory citation **Ley 1622 de 2013 ("Estatuto de Ciudadanía Juvenil")** and notes that DANE's own youth labor-market bulletin (`boletin_GEIH_juventud_*.pdf`) uses 14–28 as its headline convention. **This spec adopts 14–28** on the strength of the statutory anchor and DANE's bulletin convention; the BPO note's `(15–28)` is treated as a transcription approximation. **Sensitivities at 18–28 / 18–24 / 15–24 are NOT performed** — varying the age band post-data would constitute Y-construction discretion banned by §9; the pre-committed sensitivity universe is exhausted by R1–R4 of §7.

---

## §2. Hypothesis statement

Let `Y_t` denote the Colombian young-worker (14–28) services-sector (CIIU Rev. 4 A.C. sections G–T, broad services per GEIH feasibility §Q3) employment share in month `t`, computed per spec §5 (logit-transformed). Let `X_{t-k}` denote `log(COP_USD_{t-k})` for lag `k ∈ {6, 9, 12}` months. Let `β_k` denote the OLS coefficient on `X_{t-k}` and let the **composite β** be defined as `β_composite ≡ β_6 + β_9 + β_12`.

Formal hypothesis test (one-sided):

- **H_0:** `β_composite ≤ 0`
- **H_1:** `β_composite > 0`

**Justification of one-sided test (lit-grounded, NOT data-grounded).** The Baumol → arbitrage → offshoring chain in §1 produces an unambiguous sign expectation: COP devaluation cheapens Colombian BPO labor in USD; on the Beerepoot-Hendriks 2013 + Errighi-Bodwell ILO 2017 mechanism this *increases* US client demand at the 6–12-month contracting-cycle horizon; on the Mendieta-Muñoz 2017 channel this *increases* the share of young Colombian workers absorbed into services rather than manufacturing. Both channels point the same direction. The two-sided alternative is theoretically uninformative — no published mechanism predicts that COP devaluation contracts young-worker services share at the 6–12-month horizon. The one-sided choice is locked at spec-authoring time; switching to two-sided post-data is anti-fishing-banned per §9.

---

## §3. Falsification criteria (pre-pinned with concrete numerics)

The verdict on the primary OLS specification (spec §5) maps to one of four labels: **PASS**, **FAIL**, **ESCALATE**, or **SUBSTRATE_TOO_NOISY**. The first three are functions of the primary regression; the fourth is a function of robustness-row sign-flipping per §7. Numeric thresholds below are pinned at spec-authoring time and are not adjustable post-data. This satisfies the convergent BLOCK closure from Reality Checker D3 + Senior Project Manager D2.

### §3.1 PASS-trigger

`β_composite > 0` AND one-sided p-value `≤ 0.05`.

Rationale: conventional α = 0.05 inherited from the closed FX-vol-CPI Phase-A.0 pipeline; one-sided per §2.

### §3.2 FAIL-trigger

`β_composite ≤ 0` AND one-sided p-value `> 0.05`. Rationale: non-positive composite β at non-significant p directly fails H_1.

**NOTE (per RC D1 v1 closure):** §8.1-4(c) extends FAIL to the additional cell `β > 0 AND p > 0.20 AND Clause B does not fire`. §8 is the exhaustive verdict mapping; §3 enumerates trigger primitives only.

### §3.3 ESCALATE-trigger

ESCALATE fires if **either** of two clauses holds.

**ESCALATE Clause A:** `β_composite > 0` AND one-sided p-value `∈ (0.05, 0.20]`. Rationale: a positive composite β with p in the 5%–20% window is suggestive but inconclusive at conventional significance; the framework pre-authorizes (per CLAUDE.md Active iteration block + Phase-A.0 Rev-2 §11.A convex-payoff insufficiency caveat) escalation to convex-payoff evidence before declaring FAIL.

**ESCALATE Clause B (concrete numerics — RC D3 + SPM D2 convergent BLOCK closure):** `β_composite` near zero with high tail asymmetry, defined as both conditions holding simultaneously:

- **(B-i) "near zero":** `|β_composite| / SE(β_composite) < 0.5`. Rationale (pre-data conjecture): a t-statistic absolute value below 0.5 is well inside the standard "indistinguishable from zero" range in social-science econometrics; the 0.5 threshold is conservative and chosen to capture the convex-payoff-relevant case where the *mean* is uninformative but the *tails* may not be. NOT computed from the observed sample.
- **(B-ii) "high tail asymmetry":** `|skew(OLS residuals)| > 1.0` OR `excess kurtosis(OLS residuals) > 3.0`. Rationale (pre-data conjecture): standard financial-econometrics heuristics treat `|skew| > 1` as highly skewed and `excess kurtosis > 3` as heavy-tailed; both moments measure exactly the convex-payoff-relevant departure from Gaussianity that motivates the GARCH-X / EVT escalation suite. NOT computed from the observed sample.

The 0.5 / 1.0 / 3.0 numbers are pinned in this spec and do not move post-data.

### §3.4 ESCALATE-PASS threshold (pre-pinned, concrete numerics)

When ESCALATE fires (Clause A or B), the escalation suite of §5.5 is run and a binary ESCALATE-PASS / ESCALATE-FAIL recorded. **ESCALATE-PASS** fires if **any one or more** of the three disjuncts below hold; otherwise **ESCALATE-FAIL**. Soft language ("credible" or similar) is anti-fishing-banned per §9.

- **(D-i) Quantile β:** the τ = 0.90 quantile-regression coefficient on `X_{t-9}` (representative middle-of-window lag) is `> 0` at one-sided p `≤ 0.10`.
- **(D-ii) GARCH-X β:** in a GARCH(1,1) with `log(COP_USD_{t-k})` for `k ∈ {6, 9, 12}` as exogenous mean-equation regressors, the composite GARCH-X mean β (sum of the three lag coefficients) is `> 0` at one-sided p `≤ 0.10`.
- **(D-iii) EVT β:** in peaks-over-threshold (POT) on upper-tail residuals from the primary OLS, the regression of exceedances on `log(COP_USD_{t-9})` yields a positive coefficient at one-sided p `≤ 0.10`.

The relaxed α = 0.10 vs. α = 0.05 (primary) is the standard escalation-tier convention in the Phase-A.0 spec lineage. Disjunctive "any one or more" semantics reflect the convex-payoff-evidence framing: each disjunct probes a different distributional moment; firing any one suffices for convex-instrument fitness.

**Structural-disjunction defense against multiple-testing critique (per MQS R5 v1 closure):** This disjunction is NOT subject to multiple-testing correction (Bonferroni / Holm / BH-FDR) because each disjunct estimates a *distinct distributional-moment parameter* mapping to a *distinct convex-instrument design* (D-i quantile → range-LP / covered-call structure; D-ii GARCH-X → volatility-conditional perpetual; D-iii EVT → tail-risk put). ESCALATE-PASS records the existence of convex-payoff fitness *somewhere* in the design space, not a single-parameter rejection on three identical tests. MHT-correction would apply if all three estimated the same parameter and the question were "does at least one of three identical tests reject?"; the actual question is structurally different.

### §3.5 SUBSTRATE_TOO_NOISY trigger

If across the four robustness rows R1–R4 (§7) **more than 50%** produce `β_composite` of opposite sign from the primary, the verdict is **SUBSTRATE_TOO_NOISY** regardless of primary-row label. With four R-rows, "more than 50%" means strictly more than 2 out of 4 — i.e., 3 or 4 sign-flipped. Routes to P_D2 (Pair D revision) per §8.

### §3.6 N_MIN gate

If realized N (after §6 methodology-break treatment and §4 lag-window loss) falls below `N_MIN_OBS = 75` (Phase-A.0 floor), the spec HALTS per the §9 protocol. The N_MIN floor matches Phase-A.0 Rev-5.3.1 (per `project_rev531_n_min_relaxation_path_alpha`).

---

## §4. Sample-selection rules

- **Frequency:** monthly.
- **Time window:** 2015-01 through 2026-03 inclusive (excluding any month within the most recent two-month publication-lag tail per GEIH feasibility §Q4). **REVISED 2026-04-28 per CORRECTIONS-α' block §9.10** from the CORRECTIONS-α start of 2010-01 (Task 1.1 Step 1 second HALT-disposition: DANE Empalme files for 2010-01→2014-12 ship `RAMA4D` column with **CIIU Rev.3 codes** despite the column header naming that earlier verification mistook for Rev.4; DANE pre-applied Rev.4 sector coding (`RAMA4D_R4` column) in Empalme catalogs only from 2015-01 onward — the prior CORRECTIONS-α was column-header-verified but not value-content-verified, a discipline gap now closed in `feedback_schema_pre_flight_must_verify_values`). User picked Option α' from the Task 1.1 Step 1 disposition memo (data-availability-driven, DANE-canonical, anti-fishing-cleanest at the value-content level); see §9.10 for full audit trail. Sha256 chain: v1.1 `f74b2ac577d5…41728` → CORRECTIONS-α v1.2 `19bdaed9b966…b7a4` → 3-way cleanup v1.2.1 `b90be50bd9c6…4c6d` → CORRECTIONS-α' v1.3 (this revision).
- **Lag-window loss:** `k = 12` drops the 12 leading X-panel months, leaving 135 − 12 = 123 candidate months pre-methodology-break treatment.
- **Expected realized N:** approximately 123 (one-month tolerance for end-of-window publication-lag drop).
- **Universe:** national aggregate (Cabecera + Resto summed per GEIH feasibility §3); no city-level or departmental-level disaggregation in the primary.
- **N_MIN floor:** `N_MIN_OBS = 75` per §3.6. Expected ≈ 123 is well above; floor exists to handle pathological methodology-break shrinkage.

The `restrict-to-≥2022` window option (which collapses N to ≈ 51, below the floor) is BANNED per §6.

---

## §5. Methodology

### §5.1 Y construction

For each month `t`, define:

```text
                  sum over young-employed persons i of FEX_i * 1{CIIU_i in services_set}
Y_t (raw share) = ───────────────────────────────────────────────────────────────────────
                          sum over young-employed persons i of FEX_i

where:
  young-employed = persons aged 14-28 inclusive (Ley 1622 de 2013) with employment status Ocupado
  services_set   = CIIU Rev. 4 A.C. sections {G, H, I, J, K, L, M, N, O, P, Q, R, S, T} (broad services per GEIH feasibility §Q3)
  FEX_i          = expansion factor (FEX_C_2011 for Marco 2005 files; FEX_C_2018 for Marco 2018 files)
  Cabecera + Resto are summed (national aggregate)
```

The dependent variable in the OLS is the **logit transform**:

```text
Y_t (logit) = log( Y_t (raw share) / (1 − Y_t (raw share)) )
```

**Logit-transform justification.** `Y_t` is bounded in `[0, 1]` and empirically lives in roughly `[0.55, 0.75]` per GEIH feasibility §4-Caveat-8. The logit maps to the real line, validates OLS asymptotically without bounds enforcement, and renders coefficients as log-odds elasticities — textbook treatment for bounded dependent variables. Raw-OLS preserved as R3 (§7).

**Logit vs. fractional-response GLM (per MQS R3 v1 closure).** The logit-OLS choice over Papke-Wooldridge 1996 fractional-response GLM (*Journal of Applied Econometrics* 11(6)) or Ferrari-Cribari-Neto 2004 beta regression (*Journal of Applied Statistics* 31(7)) is justified because the empirical Y range `[0.55, 0.75]` is well-interior to `(0, 1)` — nowhere near the 0/1 boundary that motivates the fractional-response treatment (which exists to handle observations exactly at 0 or 1). Cameron-Trivedi *Microeconometrics* §16.4 endorses logit-OLS as standard for interior-bounded shares. Beta regression and fractional-response GLM are deferred as future-work robustness options but NOT pre-committed for this iteration.

**CIIU revision boundary handling (per RC D3 v1 closure).** GEIH files dated 2008-01 through 2011-12 use **CIIU Rev. 3.1**; files from 2012-01 onward use **CIIU Rev. 4 A.C.** (per DANE Resolution 066 of 2012-01-31, GEIH feasibility §Q3). The DANE-published Rev. 3.1 → Rev. 4 correspondence table is binding for harmonization; the per-file ingest harmonization rule is implementation-deferred to plan Task 1.1 Step 0 with the constraint that a deterministic harmonization rule must exist for every file in the window or the spec HALTS per §9. The `services_set = {G, H, I, J, K, L, M, N, O, P, Q, R, S, T}` defined above refers to the Rev. 4 A.C. labels; Rev. 3.1 files are pre-mapped via the official correspondence table before the `1{CIIU_i in services_set}` indicator is evaluated.

### §5.2 X construction

For each month `t`, define `COP_USD_t` as the end-of-month spot exchange rate from the closed FX-vol-CPI pipeline (Banrep series; reuse per implementation plan Task 1.2). The lag panel is constructed at `k ∈ {6, 9, 12}` months; the regressors are `log(COP_USD_{t-k})` for each lag.

### §5.3 Primary specification

The primary OLS specification is:

```text
Y_t (logit) = α + β_6 · log(COP_USD_{t-6})
                + β_9 · log(COP_USD_{t-9})
                + β_12 · log(COP_USD_{t-12})
                + ε_t
```

The composite β tested in §3 hypotheses is `β_composite = β_6 + β_9 + β_12`. The composite-coefficient hypothesis is tested via a one-sided linear restriction (sum of three coefficients greater than zero); the standard error of the composite is computed via the **linear-restriction variance formula `Var(c'β̂) = c'Σ̂c` for `c = (0, 1, 1, 1)'`** (per MQS R1 v1 closure: "delta method" is technically misnamed for a linear restriction; the closed-form linear formula applies, no Taylor expansion needed). Equivalent to the standard restricted-OLS variance / Wald-restriction variance. The one-sided p-value is one-half the two-sided Wald p-value when the point estimate is in the hypothesized direction, and 1 minus that quantity otherwise.

**Multicollinearity / composite-SE acknowledgment (per MQS R2 v1 closure).** Lags 6/9/12 of `log(COP_USD)` are highly serially correlated (typical AR(1) ≈ 0.95+ at monthly frequency), inflating individual `Var(β̂_k)` estimates. However, the composite is `c'β̂` and `Var(c'β̂) = Σ_k Var(β̂_k) + 2 Σ_{j<k} Cov(β̂_j, β̂_k)`; the covariance terms are **negative** when regressors are positively collinear, so the composite SE is *deflated* relative to the sum-of-individual-SEs intuition. The composite test is therefore precise even when individual lag coefficients have wide CIs. The result memo (Phase 4) MUST explicitly acknowledge this — a reading of "individual lags weren't significant!" is methodologically incorrect; the spec tests the composite and the composite alone.

### §5.4 Lag-window justification

The 6–12 month window is the offshoring-decision contracting-cycle horizon documented in BPO research note §3 (Beerepoot-Hendriks 2013 + Errighi-Bodwell ILO 2017; offshoring contracts are typically annually re-tendered with quarterly review). The three lags `{6, 9, 12}` evenly span the window. Free lag tuning (e.g., sweeping `k = 1, ..., 24` and selecting on fit) is anti-fishing-banned per §9.

### §5.5 Escalation methodology (conditional on §3.3 ESCALATE-trigger)

If ESCALATE fires, three procedures are run, mapped to §3.4:

- **Quantile regression** (D-i): conditional quantile regression of `Y_t (logit)` on the three lagged-X regressors, estimated at `τ = 0.90`.
- **GARCH-X** (D-ii): GARCH(1,1) on `Y_t (logit)` with the three lagged-X regressors entering the mean equation as exogenous covariates.
- **EVT POT** (D-iii): peaks-over-threshold on upper-tail residuals from the primary OLS (threshold = empirical 0.90 residual quantile); exceedances regressed on `log(COP_USD_{t-9})`.

Each yields a coefficient and one-sided p-value; the §3.4 disjunction is evaluated against these.

---

## §6. Methodology-break disposition (pre-pinned)

DANE switched the GEIH master sample from Marco 2005 (population frame derived from the 2005 Census) to Marco 2018 (frame from the 2018 Census) effective January 2021. 2021 was a parallel-collection year; from January 2022 onward, only Marco 2018 is published. DANE has published a 132-month empalme (splice) factor covering **2010-01 through 2020-12 inclusive** per the nota técnica §3.3 verbatim: *"se construye un factor por cada mes a partir de enero de 2010 hasta diciembre 2020 que secuencialmente ajusta una parte del nivel de la serie de ocupados … se divide a θ en 132 partes (son los meses desde enero 2010 hasta diciembre de 2020)"* (`Nota-tecnica-empalme-series-GEIH.pdf`, GEIH feasibility §Q4 + §5 References). **CORRECTIONS-α' v1.3 clarification (per §9.10):** the empalme factor in `FEX_C` is published for the full 2010-2020 window, but DANE pre-applied **Rev.4 sector coding** (`RAMA4D_R4` column) in Empalme catalogs only from **2015-01 → 2020-12 (72 months)**; for 2010-2014 the Empalme files retain `RAMA4D` with Rev.3 codes. Under Option α' the sample window is 2015-01 → 2026-03; the 2010-2014 era is OUT OF SCOPE.

**Primary disposition:** apply the DANE empalme factor for Marco-2005 → Marco-2018 reconciliation per the published nota técnica at `https://www.dane.gov.co/files/investigaciones/boletines/ech/ech/Nota-tecnica-empalme-series-GEIH.pdf`. The empalme is applied to `Y_t` (raw share) before the logit transform of §5.1.

**Robustness disposition R1:** instead of the empalme factor, include a 2021 regime dummy (1 for `t ≥ 2021-01`, 0 otherwise) as an additional regressor in the OLS. This is row R1 of §7.

**BANNED disposition:** restrict the sample to `t ≥ 2022-01` (Marco-2018-only). This collapses N to approximately 51 monthly observations as of 2026-03 — below the `N_MIN_OBS = 75` floor of §3.6. Invoking this disposition would constitute an anti-fishing violation per §9.

**Empalme residual-bias acknowledgment (per MQS R4 v1 closure — substantive limitation).** The DANE empalme corrects for population-frame level shift (Marco 2005 → Marco 2018) but does NOT correct: **(a)** the *nonlinear interaction* of a raw-share level shift with the §5.1 logit transform (`d/dY[logit(Y)] = 1/[Y(1-Y)]` varies across the support, so an empalme calibrated for raw-share linearity does not necessarily neutralize bias in the logit-transformed series); or **(b)** any *sectoral classification changes* between Marco 2005 and Marco 2018 master-sample frames (the empalme handles the population frame, not the sector codings). R1 (2021 regime dummy on logit-Y) is the design's hedge against (a); R2 (BPO-narrow J+M+N) partially probes (b). Residual bias surviving both R1 and R2 is a known limitation that MUST be acknowledged in the Phase-4 result memo; promoting a primary-PASS verdict without this acknowledgment when R1 and R2 are inconsistent with the primary is anti-fishing-banned per §9.

---

## §7. Robustness checks (pre-committed)

Four robustness rows are pre-committed. Each is a single-row alternative that varies exactly one design choice from the primary; multi-dimensional re-specification (varying two or more dimensions simultaneously) is anti-fishing-banned per §9. Each row produces its own `β_composite` estimate.

- **R1 — 2021 regime dummy** (alternative to §6 primary methodology-break disposition). Same primary specification but replace empalme with a 2021 regime dummy.
- **R2 — Y narrow** (CIIU Rev. 4 sections J + M + N only — BPO-narrow per GEIH feasibility §Q3 recommendation). Same primary specification but recompute `Y_t (raw share)` with the numerator restricted to the BPO-narrow sector set; logit transform unchanged.
- **R3 — raw OLS** (no logit transform). Same primary specification but the dependent variable is the raw share `Y_t` instead of `Y_t (logit)`. This is the bounded-range diagnostic (per §5.1 caveat).
- **R4 — HAC standard errors** (Newey-West, lag truncation `L = 12`). Same primary specification and same point-estimate `β̂_composite` but with HAC standard errors substituted for the OLS standard errors; the one-sided p-value is recomputed against the HAC SE. This is the autocorrelation diagnostic per GEIH feasibility §Q5.

### §7.1 R-row consistency classification (pre-pinned)

After all four rows are estimated, classify per the following rule:

- **AGREE:** all four R-rows produce `β_composite` with the same sign as the primary specification (regardless of significance).
- **MIXED:** between one and two R-rows produce sign-flipped `β_composite` relative to the primary.
- **DISAGREE:** three or four R-rows produce sign-flipped `β_composite` relative to the primary. This triggers the SUBSTRATE_TOO_NOISY verdict per §3.5.

Sign comparison uses the primary-specification `β_composite` as the reference; an R-row "matches" the primary if its `β_composite` has the same strict sign (positive vs. non-positive). Significance is not required for sign-matching; this is intentional — sign stability is the diagnostic, not significance stability.

---

## §8. Verdict-decision tree (deterministic mapping)

The tree maps `(β_composite_sign, p_one_sided, R_row_consistency, Clause-B fires?)` to a verdict in `{PASS, FAIL, ESCALATE, SUBSTRATE_TOO_NOISY}`, plus the HALT-N_MIN path. Mapping is exhaustive: every tuple → exactly one verdict; no leaf maps to "TBD" or "specialist judgment."

### §8.1 Mapping rules (evaluated in order)

1. **N gate.** If `N < 75`, verdict = **HALT-N_MIN** per §3.6 / §9.5.
2. **R-consistency.** Compute per §7.1. If `DISAGREE`, verdict = **SUBSTRATE_TOO_NOISY** regardless of primary. Stop.
3. **Otherwise** (R-consistency ∈ {AGREE, MIXED}) evaluate the primary:
   - (a) `β > 0` AND `p ≤ 0.05` → **PASS**. Stop.
   - (b) `β > 0` AND `p ∈ (0.05, 0.20]` → **ESCALATE** (Clause A). Run §5.5; record ESCALATE-PASS / ESCALATE-FAIL per §3.4. Stop.
   - (c) `β > 0` AND `p > 0.20` → if both B-i AND B-ii fire (§3.3) → **ESCALATE** (Clause B); else **FAIL**. Run §5.5 if ESCALATE. Stop.
   - (d) `β ≤ 0` AND `p > 0.05` → if both B-i AND B-ii fire → **ESCALATE** (Clause B); else **FAIL**. Run §5.5 if ESCALATE. Stop.
   - (e) `β ≤ 0` AND `p ≤ 0.05` (wrong-signed significant β̂) → **FAIL**. Clause B is NOT evaluated — wrong-signed significant β̂ unambiguously falsifies H_1, and convex-payoff escalation (grounded in the *positive* sign expectation) does not apply. Stop.

### §8.2 Synthetic-tuple walk (verifying determinism)

Per implementation plan Task 0.1 Step 2 sub-checklist (a)–(d), every leaf is exercised:

| # | Synthetic tuple | Branch | Verdict |
|---|---|---|---|
| 1 | `(β̂=+0.03, p=0.02, AGREE)` | 4(a) | PASS |
| 2 | `(β̂=+0.02, p=0.10, AGREE)` | 4(b) | ESCALATE (A) |
| 3 | `(β̂=+0.001, p=0.40, MIXED, B-i+B-ii fire)` | 4(c) | ESCALATE (B) |
| 4 | `(β̂=+0.001, p=0.40, MIXED, neither fires)` | 4(c) | FAIL |
| 5 | `(β̂=−0.002, p=0.30, AGREE, B-i+B-ii fire)` | 4(d) | ESCALATE (B) |
| 6 | `(β̂=−0.002, p=0.30, AGREE, B-i only)` | 4(d) | FAIL |
| 7 | `(β̂=−0.05, p=0.01, AGREE)` | 4(e) | FAIL |
| 8 | `(β̂=+0.04, p=0.02, DISAGREE)` | step 2 | SUBSTRATE_TOO_NOISY |
| 9 | `(N=60, rest irrelevant)` | step 1 | HALT-N_MIN |

Each row → exactly one verdict; no row → "TBD"; Clause B numerics (`|β̂|/SE < 0.5` AND `|skew| > 1.0` OR `excess kurtosis > 3.0`) are concrete; Clause A `p ∈ (0.05, 0.20]` boundaries are pinned; §3.4 ESCALATE-PASS disjunction (τ = 0.90 quantile, GARCH-X composite, EVT POT, all at p ≤ 0.10) is concrete.

### §8.3 Verdict → next-stage routing

Drives Phase 4 disposition per implementation plan Task 4.1:

- **PASS** → unblock Stage 2 M sketch authoring (separate downstream plan).
- **ESCALATE-PASS** → unblock Stage 2 M sketch with explicit convex-payoff documentation.
- **ESCALATE-FAIL** → Pair D dropped; dispatch fresh Trend Researcher to re-rank Pair A / B / C / E from BPO research note §6 5-pair ranking.
- **FAIL** (no escalation triggered) → same as ESCALATE-FAIL routing.
- **SUBSTRATE_TOO_NOISY** → identify methodology improvements for P_D2 (Pair D revision).
- **HALT-N_MIN** → §9.5 HALT-disposition path.

---

## §9. Anti-fishing invariants

These invariants are immutable for this iteration; they carry forward the Phase-A.0 pattern documented in `feedback_pathological_halt_anti_fishing_checkpoint`.

- **§9.1 Threshold immutability.** No threshold in this spec — α = 0.05 (primary) / α = 0.10 (escalation) / `N_MIN = 75` / Clause B numerics (`|β̂|/SE < 0.5`, `|skew| > 1.0`, `excess kurtosis > 3.0`) / SUBSTRATE_TOO_NOISY > 50% sign-flip / R-row consistency rules — may be adjusted post-data. Any normative revision recomputes the spec sha256 and re-triggers Task 0.2 2-wave verification.

- **§9.2 Y-construction immutability.** The §5.1 construction (youth band 14–28, broad services CIIU sections G–T, national aggregate, logit transform, expansion factors per §5.1) is fixed at spec-authoring time. Sensitivities at 18–28 / 18–24 / 15–24, promoting BPO-narrow J+M+N to primary, promoting raw-share to primary, Bogotá-only, or any other Y reformulation post-data are anti-fishing-banned. The pre-committed sensitivity universe is exhausted by R1–R4 of §7.

- **§9.3 Sample-window immutability.** The **2015-01 → 2026-03 monthly window of §4 is fixed** (revised per §9.10 CORRECTIONS-α' 2026-04-28 PM; chain: 2008-01 pre-revision → 2010-01 per §9.9 CORRECTIONS-α → 2015-01 per §9.10 CORRECTIONS-α'; both shrinkages were data-availability-driven via the legal channel after schema-stability HALT-dispositions). Re-curation post-data (excluding 2020 COVID months, excluding 2021 parallel-collection, restricting to post-2022) is anti-fishing-banned. The §6 methodology-break disposition is pre-pinned; `restrict-to-≥2022` is explicitly BANNED.

- **§9.4 Lag-set immutability.** The set `k ∈ {6, 9, 12}` is fixed per §5.4. Free lag tuning or post-data addition of non-{6, 9, 12} lags is anti-fishing-banned.

- **§9.5 HALT-disposition path.** Any HALT condition — `N < N_MIN`, schema-stability failure (implementation plan Task 1.1 Step 0), DANE-side data anomaly (Task 1.1 Step 6 recovery path), or any reviewer-flagged threshold-tuning / Y-re-construction / escalation-rescue-claim — invokes the protocol from `feedback_pathological_halt_anti_fishing_checkpoint`: (1) typed exception raised by executing specialist; (2) disposition memo filed by Foreground Orchestrator at `contracts/.scratch/2026-04-XX-pair-d-<halt-reason>-disposition.md` enumerating ≥3 pivot options; (3) user surface; (4) user picks the pivot; (5) CORRECTIONS block lands in the next plan revision documenting disposition + chosen pivot + rationale; (6) 3-way review of the CORRECTIONS revision before any further execution. Auto-pivot is anti-fishing-banned.

- **§9.6 Escalation as pre-authorization, not post-hoc rescue.** The §5.5 + §3.4 escalation suite was pre-authorized in CLAUDE.md before any data was pulled. Framing escalation in the result memo as "rescue" is anti-fishing-banned; the framing must be "pre-pinned convex-payoff evidence test, ran whether or not mean-OLS passed" — the same discipline maintained by the closed FX-vol-CPI pipeline (`project_fx_vol_econ_complete_findings`) on its A1 monthly + A4 release-day-excluded sensitivities.

- **§9.7 Spec sha256 governance.** Once the spec sha256 is computed in Task 0.3 and quoted in the implementation plan frontmatter, it governs every downstream artifact: data parquets, notebooks, result tables, memo, gate_verdict.json, and the CLAUDE.md Active iteration block update. Any artifact not citing the pinned sha256 is non-canonical and must be revised before commit.

- **§9.8 Phase-A.0 invariant carryforward.** This iteration inherits Phase-A.0's pre-registration discipline, spec sha256 pin, CORRECTIONS-block-on-revision, and the principle that closed iterations inform the next iteration's prior rather than re-running the same iteration at adjusted thresholds.

- **§9.10 CORRECTIONS block — Task 1.1 Step 1 second HALT (2026-04-28 PM, CORRECTIONS-α').** Per `feedback_pathological_halt_anti_fishing_checkpoint` + spec §9.5 + the new memory `feedback_schema_pre_flight_must_verify_values`, the following audit trail records the post-second-HALT pivot.
  - **HALT trigger.** Plan Task 1.1 Step 1 ingest verification (re-dispatch under CORRECTIONS-α v1.2.1). Typed exception `PairDEmpalmeSchemaContradictsHarmonizationPin`. Disposition memo at `contracts/.scratch/2026-04-28-task-1.1-step-1-empalme-rev3-vs-rev4-disposition.md`.
  - **Cause of HALT.** The CORRECTIONS-α v1.2 / v1.2.1 pinned harmonization rule for 2010-2020 Empalme catalogs assumed `RAMA4D` contained CIIU Rev.4 a.c. codes for the entire 132-month window. Raw value-content inspection at re-dispatch revealed `RAMA4D` ships **CIIU Rev.3 codes** for 2010-2014 (60 months); DANE pre-applied Rev.4 (`RAMA4D_R4` column) only from 2015-01 onward. The prior Step 0 verification was column-header-only, not value-content-verified. Mapping Rev.3 4-digit codes to Rev.4 4-digit codes admits 1-to-many cases requiring author judgment — the precise §9.2 Y-construction-immutability violation that Option α was supposed to eliminate.
  - **User pivot.** User picked **Option α'** (shorten window to 2015-01 → 2026-03). Rationale: DANE-canonical Rev.4 sector coding (`RAMA4D_R4`) is value-content-verified for the entire 2015-2026 window; data-availability-driven legal channel for §9.3 amendment; N=123 post-lag-12 well above N_MIN=75.
  - **Audit-trail effects.**
    - §4 sample window edited (2010-01 → 2015-01); §4 N expectation revised (≈183 → ≈123); §4 cites §9.10 explicitly.
    - §9.3 sample-window-immutability text updated to quote new window with chain-of-revisions pointer.
    - §6 empalme-coverage prose updated: "Rev.4 sector coding via `RAMA4D_R4` is available 2015-01 → 2020-12 in Empalme catalogs (72 months); 2010-01 → 2014-12 Empalme files use `RAMA4D` with Rev.3 codes and are out of scope under Option α'."
    - §5.1 CIIU revision boundary handling text updated: 2008-2014 era is OUT OF SCOPE under the new window; 2015-2020 uses `RAMA4D_R4` from Empalme catalogs; 2022+ uses native Marco-2018 `RAMA4D_R4`.
    - Spec sha256 recomputed per §9.7; old `b90be50bd9c6…4c6d` superseded; chain documented in frontmatter.
    - Plan Task 1.1 Step 0 era table edited: "2010-01 → 2020-12 RAMA4D" row replaced with "2015-01 → 2020-12 RAMA4D_R4" (72 months).
    - §3 numerics, §6 R1, §6 BANNED-restrict-≥2022, §7 R1-R4 robustness universe, §8 verdict tree all unchanged.
  - **Rejected pivots (anti-fishing audit, per disposition memo §5).** α'' (2-digit RAMA2D section-letter mapping for 2010-2014 — author-judgment within §9.2 ban); α''' (back-extend supplemental cid 661 catalog to 2010-2014 — operationally impossible: no cid-661 equivalent exists for 2010-2014); β' (4-digit modal-choice crosswalk — author-judgment); γ' (nearest-neighbor classifier on 2015-2019 paired data — author-constructed model substitution); δ' (2022-only — N=39 below N_MIN=75, banned per §6); ε' (Rev.3-only window — anti-fishing-paradoxical); ζ' (drop sector restriction — Y-redefinition post-data, banned per §9.2). All seven rejections documented (six methodological rejections + one operational impossibility).
  - **Lesson recorded as memory.** `feedback_schema_pre_flight_must_verify_values` (NON-NEGOTIABLE): schema-stability pre-flights MUST verify both column-header names AND sample value-content per file against a published codebook. Header-only verification produced the CORRECTIONS-α invalidation cycle; this lesson now binds future pre-flights.
  - **3-way review of this CORRECTIONS-α' revision.** Per HALT protocol + spec §9.5 + §9.7 sha256-governance, this revision is subject to Reality Checker (Wave 1 evidence + anti-fishing) + Model QA Specialist fresh instance (Wave 2 spec methodology) + Senior Project Manager (Wave 3 plan + workflow integrity). All three must PASS or PASS-WITH-REV-no-blocking before commit; trailer `Doc-Verify: wave1=...` carries all three verdicts.

- **§9.9 CORRECTIONS block — Task 1.1 Step 0 schema-stability HALT (2026-04-28 AM, CORRECTIONS-α).** Per `feedback_pathological_halt_anti_fishing_checkpoint` and the spec's own §9.5 HALT-disposition path, the following CORRECTIONS-block audit trail records the post-first-HALT pivot. (Superseded in part by §9.10 CORRECTIONS-α' which corrected the empalme Rev.4-coverage assumption from "2010-2020 132 months" to "2015-2020 72 months"; §9.9 retained for full audit history.)
  - **HALT trigger.** Plan Task 1.1 Step 0 schema-stability pre-flight (added per SPM D5 BLOCK closure in plan v1 verification). Typed exception `PairDSchemaPreFlightPathological`. Disposition memo at `contracts/.scratch/2026-04-28-task-1.1-step-0-schema-pathological-disposition.md`.
  - **Cause of HALT.** The DANE Empalme nota técnica covers 2010-01 → 2020-12 (132 months) only; 2008-01 → 2009-12 (24 months) falls outside that window. For pre-2010 months, two simultaneous harmonization actions DANE did NOT publish are required: (a) Marco-2005 → Marco-2018 reconciliation (out of scope per DANE nota técnica §3.3 verbatim); (b) CIIU Rev.3.1 → Rev.4 a.c. crosswalk for which DANE's published correspondence admits per-4-digit-code 1-to-many cases requiring author judgment. Per §9.2 Y-construction-immutability, author-judgment harmonization is itself anti-fishing-banned.
  - **User pivot.** User picked **Option α** (shorten sample window to 2010-01 → 2026-03 inclusive). Rationale: data-availability-driven (NOT data-driven; the legal channel for §9.3 sample-window-immutability amendment); DANE-canonical at every break-point; N=183 post-lag-12 well above N_MIN=75.
  - **Audit-trail effects.**
    - §4 sample window edited (2008-01 → 2010-01); §4 N expectation revised (≈206 → ≈183); §4 cites §9.9 explicitly.
    - Spec sha256 recomputed per §9.7 governance (the original v1.1 sha256 `f74b2ac577d5182842116a8798f307a610c185f1e6e259b8530e2ec266141728` is superseded; new sha256 pinned in this revision).
    - Plan Task 1.1 Step 0 amended with the pinned harmonization rules table for Option α (2010-2020 Empalme catalogs cid 755-765; 2021 Marco-2018 semester archives cid 701; 2022-2026 Marco-2018 native).
    - §6 methodology-break disposition language unchanged in substance — DANE empalme remains primary; 2021 regime dummy remains R1; restrict-≥2022 remains BANNED.
    - §7 robustness universe (R1-R4) unchanged — Y-window shrinkage does not redefine the robustness specifications.
  - **Rejected pivots (anti-fishing audit).** Options β (author-judgment crosswalk for 2008-2009), γ (author-constructed empalme extension), ε (empalme-only window dropping post-2020) were enumerated in the disposition memo but NOT chosen. Rationale per memo §6: β admits §9.2 author-judgment Y-construction; γ requires §9 anti-fishing-banned author-constructed empalme; ε excludes the most reliable post-2020 era which is anti-fishing-paradoxical.
  - **3-way review of this CORRECTIONS revision.** Per HALT protocol, this revision is subject to Reality Checker (Wave 1 evidence + anti-fishing) + Model QA Specialist fresh instance (Wave 2 spec methodology) + Senior Project Manager (plan + workflow integrity). All three must PASS or PASS-WITH-REV-no-blocking before commit; trailer `Doc-Verify: wave1=...` carries all three verdicts.

---

**End of spec.** All 9 sections present; no "TBD" placeholders; all thresholds pinned in §3 + §6 + §7 + §9 with concrete numerics and lit-grounded or pre-data-conjecture-grounded rationale; §8 verdict tree deterministic with synthetic-tuple walk in §8.2; §3.4 + §5.5 escalation suite pre-authorized with concrete disjunctive thresholds; §6 methodology-break disposition pre-pins primary + R1, BANS restrict-to-≥2022; §9 anti-fishing invariants explicit and Phase-A.0-aligned. Ready for Task 0.2 2-wave review (Reality Checker Wave 1 + Model QA Specialist fresh instance Wave 2).
