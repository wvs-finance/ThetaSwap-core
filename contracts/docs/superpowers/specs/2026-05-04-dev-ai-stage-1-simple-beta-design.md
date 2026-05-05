---
spec_version: 1.0.1
decision_hash: 456ba39e188d00bb17471359a5803d6aa8a40de3b3788f17294bab828a968204
decision_hash_protocol: sha256 computed against this file with `decision_hash` field set to the sentinel `<to-be-pinned-after-recompute>`. To re-verify, replace the pinned hash with the sentinel string and recompute sha256; should match.
prior_decision_hash_v1_0: 72ebe2561ac8b724df671e7d312e604b6c9a60419ee179ebc45a2454bfa345cc  # superseded 2026-05-05 by v1.0.1 hybrid-FLAG integration (Option D from disposition memo)
parent_iteration_pin: dev-AI-cost iteration (CORRECTIONS-η/θ/ι chain 2026-05-04, parent CLAUDE.md "Abrigo Operating Framework")
sibling_pass_precedent: Pair D Stage-1 simple-β PASS verdict 2026-04-28 (β=+0.13670985, HAC SE 0.02465, t=+5.5456, p_one=1.46e-08); spec sha256 `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`; project memory `project_pair_d_phase2_pass`
dependent_plan: <to-be-emitted-after-spec-acceptance>
verifier_v1_0_wave1: ACCEPT_WITH_FLAGS (Reality Checker, 2026-05-05; 1 FLAG + 3 NITs at /tmp/wave1_rc_dev_ai_stage_1.md; plan-emission unblocked)
verifier_v1_0_wave2: ACCEPT_WITH_FLAGS (Model QA Specialist fresh instance, 2026-05-05; 0 BLOCKs / 5 FLAGs (1 HIGH) / 3 NITs at /tmp/wave2_modelqa_dev_ai_stage_1.md; recommended v1.0.1 inline integration)
verifier_v1_0_1_wave1: pending (RC closure-only on diff, post-v1.0.1 emission)
revision_history:
  - v1.0 2026-05-04 initial draft (Model QA Specialist; chunked-authoring discipline per `feedback_background_agent_stream_watchdog_timeout`); sha256 `72ebe2561ac8b724df671e7d312e604b6c9a60419ee179ebc45a2454bfa345cc`
  - v1.0.1 2026-05-05 hybrid-FLAG integration (Option D from disposition memo): inline integration of MQS FLAG-1 (Section J ⊂ Pair D G–T compositional-accounting acknowledgment as §1 paragraph + new §9.16 invariant; R5 robustness arm DEFERRED to v1.1 conditional gate per disposition memo); MQS FLAG-2 (Section-J-specific logit-derivative amplification quantified in §5.1, ratio 2.34× vs Pair D 1.32×); MQS FLAG-3 (§6 fallback (i) trigger restructured to require §9.5 HALT unconditionally, replaces unpinned "5× Pair D residual variance" reference); MQS FLAG-5 (§4 explicit X-back-extension justification); MQS NIT-1 (§5.1 Y_s1 redesign-dummy pinned as option (a) per Y feasibility memo §1.2); MQS NIT-2 (§5.1 Section J 4-digit code range replaced with Division-list formulation). MQS FLAG-4 (Y_s3 cluster-SE / N_MIN unit) DEFERRED to v1.1 conditional on §8.3 (i) Y_s3 promotion. RC NIT-1/2/3 + MQS NIT-3 deferred (cosmetic).
---

# Simple-β Dev-AI-Cost Iteration — Pre-registered Stage-1 Design Spec

> **Code-agnostic by mandate** (project memory `feedback_no_code_in_specs_or_plans`). All thresholds and decision-tree branches are pinned in spec text BEFORE any data is pulled. ASCII / pseudo-equations are used to denote methodology; nothing in this document is executable.

---

## §1. Background and motivation

Within the Abrigo Operating Framework (worktree CLAUDE.md, "Abrigo Operating Framework" section), each (Y, M, X) iteration has a three-stage life: **Stage 1** empirical risk validation (does the underlying microeconomic risk admit a measurable β?), **Stage 2** ideal-scenario M sketch on Panoptic, **Stage 3** deployment. **This spec governs Stage 1 only.** Conflating stages is the Phase-A.0 failure mode that produced the parked P1 apparatus and is anti-fishing-banned.

The active iteration (CLAUDE.md "Abrigo Operating Framework" section, post-2026-05-04 update; CORRECTIONS-η / CORRECTIONS-θ / CORRECTIONS-ι decomposition chain at `contracts/.scratch/path-b-stage-2/phase-1/`) commits the **dev-AI-cost iteration**: Stage-1 empirical validation that Colombian ICT-subsector young-worker employment share responds positively to lagged COP/USD devaluation. The target population is **LATAM developers paying USD-denominated AI APIs / AI tooling** (Colombia primary; Mexico / Brazil / Argentina / Peru / Chile broader); the structural-transformation channel relevant for these developers is the same Baumol-cost-disease → US-Colombia tech-labor wage arbitrage → US tech-firm offshoring of ICT services chain that drives Pair D's broad-services result, but narrowed to CIIU Rev. 4 Section J ("Información y Comunicaciones") — software development, data processing, telecommunications, and information services specifically. The dev-AI population is *itself* employed in Section J, so the Y measures structural-transformation pressure on the population the future M-sketch will hedge.

**Pair D as sibling precedent (NOT taint).** Pair D — broad-services (CIIU Rev. 4 Sections G–T) employment share for Colombian young workers (14–28) regressed on lagged COP/USD — closed PASS verdict 2026-04-28: β_composite = +0.13670985, HAC SE 0.02465, t = +5.5456, one-sided p = 1.46e-08, R-AGREE 0/4 sign-flips, spec sha256 `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659` (project memory `project_pair_d_phase2_pass`). This iteration re-tests the FX → Colombian-employment transmission under a **narrower Y** (Section J ICT-only vs. Pair D's Section G–T broad-services) and an explicitly **different transmission hypothesis** (US tech-firm offshoring of ICT services for the dev-AI-paying population, vs. Pair D's BPO-flavored services-broad). The Pair D PASS does NOT taint this test in the anti-fishing sense — different Y subsector, different mechanism, different population — but the *re-use of the same X* (COP/USD lagged 6–12mo, same Banrep TRM source) is acknowledged here for transparency. Same-X re-use is the same anti-fishing transparency disclosure Pair D itself made for re-using the FX variable that powered the closed FX-vol-CPI-surprise pipeline at gate verdict FAIL 2026-04-19.

**Mechanism (literature-grounded, NOT data-grounded).** The transmission chain motivating the *positive* sign expectation:

1. **Baumol cost disease (Baumol-Bowen 1966; Baumol 2006 NBER WP 12218; Estache et al. 2021).** US service-sector productivity is structurally low relative to manufacturing; service-sector wages nonetheless track manufacturing-sector wages via labor-market spillover; US tech-services unit labor cost in USD therefore rises faster than tradable-goods unit cost. This anchors the long-run claim that US ICT services cannot productivity-match the broader US economy without offshoring lower-skill work.
2. **US-Colombia tech-labor wage arbitrage (Mendieta-Muñoz 2017 *Journal of Economic Structures* 6:24, "Trade liberalization and premature deindustrialization in Colombia").** COP devaluation cheapens Colombian ICT labor in USD terms. Mendieta-Muñoz traces Colombian deindustrialization to the 1990 Apertura under Gaviria; the Rodrik 2016 / McMillan-Rodrik 2011 premature-deindustrialization canon predicts that displaced labor reallocates *into* services (incl. ICT) rather than into manufacturing.
3. **US tech-firm offshoring (Beerepoot-Hendriks 2013 *Service Industries Journal* 33(11), "Employability of offshore service-sector workers in the Philippines: dead-end jobs?"; Errighi-Khatiwada-Bodwell ILO 2017).** US clients re-tender offshoring contracts on a 6–12-month cycle (annual contracts with quarterly review per the standard offshoring contracting horizon); Section J of CIIU Rev. 4 — software development, data processing, telecom, information services — is the precise sector where this offshoring concentrates for the dev-AI-paying population. The Beerepoot-Hendriks Philippines comparator + Errighi-Bodwell ILO 2017 BPO-comparable framework establish that Section-J-style offshoring absorbs young educated workers without enabling the wage-to-capital transition.
4. **Composite directional prediction.** COP/USD↑ at lag 6–12mo → cheaper Colombian ICT labor in USD → US tech-firm offshoring demand for Section J labor↑ → Section J young-worker (14–28) employment share↑ at lag.

**Section J vs. Pair D's Section G–T cut.** Pair D measured the broad-services aggregate (G = wholesale/retail trade, H = transport, I = accommodation, J = ICT, K = finance, L = real estate, M = professional/scientific/technical, N = administrative, O = public administration, P = education, Q = health/social, R = arts/entertainment, S = other services, T = household). Section J alone is the ICT subsector — software development, data-processing, telecom, information services — and is structurally smaller (~700–1,200 14–28 employed per month in Colombia per GEIH cell-size estimates from the Y feasibility memo). Narrowing from G–T to J is what makes this iteration's mechanism specifically about ICT services rather than BPO-flavored services-broad; the same composite-β logic and same X applies.

**Compositional-accounting risk acknowledgment (per Wave-1 RC FLAG #1 + Wave-2 MQS FLAG-1 v1.0 closure inherited as v1.0.1 §1 paragraph + load-bearing in §9.16).** Section J is a strict subset of Pair D's Section G–T, and Pair D's broad-services aggregate already PASSed Stage-1 with β_composite = +0.137. A positive β_composite on Section J is therefore consistent with EITHER (i) the dev-AI-cost transmission mechanism firing independently at the ICT-narrow subsector level, OR (ii) Section J's compositional contribution to Pair D's broad-services PASS — i.e., a re-discovery of the Pair D signal aggregated up to ICT. **The Stage-1 verdict here cannot distinguish these two possibilities without a Section-J-vs-Section-(G–T-minus-J) decomposition.** This is acknowledged here in §1 as a verdict-interpretation caveat; the Stage-1 PASS routing language in §8.3 is bound by §9.16 to flag this ambiguity in the Phase-4 result memo, requiring downstream Stage-2 M-sketch authoring to address the decomposition explicitly. Adding an R5 robustness arm "primary spec on (Sections G–T minus J)" — where a similar β_composite would imply Section J is compositional, while a smaller β_composite would imply Section J's narrowing has an independent ICT signal — was DEFERRED at v1.0.1 authoring time per the disposition memo Option D (not added at this revision; conditional gate for v1.1 if user explicitly invokes the design change OR if Stage-2 dispatch surfaces the need). The compositional-accounting risk inherits the Pair D RC FLAG #1 "hedge the *correlation* not the *BPO causal channel*" caveat and binds *more strongly* here because the Y is a strict subset of the already-PASSing Y rather than an independent panel.

**Section J literature-anchor sub-aggregate-substitutability flagged (per Wave-1 RC FLAG #1).** The transmission-chain inheritance from "BPO offshoring works in Philippines" → "Section J offshoring works in Colombia" rests on a sub-aggregate-substitutability assumption: Section J Divisions 58–63 contain BPO-relevant Divisions 62 (Computer programming) + 63 (Information service activities), but ALSO contain non-BPO Divisions 58 (Publishing), 59 (Motion picture/video), 60 (Programming & broadcasting), and 61 (Telecommunications) — sectors that respond to OTHER demand drivers (telecom regulatory cycles, advertising spend, content market) than US tech-firm offshoring. If Section J β_composite > 0 turns out positive, attribution to "dev-AI offshoring channel" cannot be made cleanly without additional sub-Division decomposition. This is also bound by §9.16 as a Phase-4 result-memo disclosure requirement; Stage-2 M-sketch dispatch (if Stage-1 PASSes) MUST calibrate hedge geometry against the ICT-services-direct sub-component (Divisions 62–63), NOT against the Section J aggregate β_composite.

**BPO research note pointer.** The literature evidence base is documented in the BPO research note (`contracts/.scratch/2026-04-27-colombian-bpo-non-industrialization-hedge-research.md`) and is anchored on the Mendieta-Muñoz 2017 + Beerepoot-Hendriks 2013 + Errighi-Bodwell ILO 2017 papers. The dev-AI-cost iteration extends this literature to the ICT-narrow subset; the same canonical citations apply since the Section J cut is a sub-aggregate of the literature's services-broad evidence base.

**CORRECTIONS-η / θ / ι decomposition chain (precedent).** The dev-AI-cost iteration's Y / X / a_s decomposition discipline is documented at:

- `contracts/.scratch/path-b-stage-2/phase-1/corrections_eta_decomposition.md` — Y / X / a_s / a_l / premium-leg / payout-leg decomposition rules.
- `contracts/.scratch/path-b-stage-2/phase-1/corrections_theta_substrate_scope_clarification.md` — substrate-panel scope (the v1.5-data on-chain substrate is reserved for a_l, NOT Stage-1 Y); Y must come from off-chain national-statistics-agency / central-bank / developer-survey sources.
- `contracts/.scratch/path-b-stage-2/phase-1/corrections_iota_a_s_framing.md` — a_s is per-user instrument balance sheet (NOT aggregate macro variable); calibrated at Stage-2 from AI-vendor pricing + DevSurvey.

**Y selection precedent (Y feasibility memo).** Y_p / Y_s1 / Y_s2 / Y_s3 are pre-pinned at `contracts/.scratch/2026-05-04-dev-ai-y-feasibility.md` §5 PRE-COMMIT recommendation. This spec consumes that memo's pre-commit verbatim; no Y construction is authored here for the first time.

**Variables NOT in Stage-1 scope.** The following are explicitly deferred to downstream stages and are NOT inputs to the §5 OLS:

- **a_s** — per-user instrument balance sheet (per CORRECTIONS-ι; Stage-2 M-sketch from AI-vendor pricing + DevSurvey LATAM cohort distributions).
- **a_l** — on-chain LP yield vaults (per CORRECTIONS-θ; v1.5-data substrate panel reuse, Stage-2/3).
- **Premium leg** / **payout leg** — Stage-3 plumbing.
- **Iron-condor / range / strike geometry** — Stage-2 M-sketch on Panoptic.

Including any of these in the §5 specification would constitute stage drift and is anti-fishing-banned per §9.

**Youth-band citation discrepancy — flagged once and resolved.** The BPO research note quotes `(15–28)`; the GEIH feasibility report and the dev-AI Y feasibility memo §5 quote `(14–28)` with statutory anchor **Ley 1622 de 2013 ("Estatuto de Ciudadanía Juvenil")** and DANE's youth labor-market bulletin convention. **This spec adopts 14–28** following the statutory anchor and DANE's published convention; sensitivities at 18–28 / 18–24 / 15–24 are NOT performed (varying the age band post-data would constitute Y-construction discretion banned by §9; the pre-committed sensitivity universe is exhausted by R1–R4 of §7 + Y_s1 / Y_s2 / Y_s3 of §5).

---

## §2. Hypothesis statement

Let `Y_t` denote the Colombian young-worker (14–28) employment share in **CIIU Rev. 4 Section J ("Información y Comunicaciones")** in month `t`, computed per spec §5 (logit-transformed). Let `X_{t-k}` denote `log(COP_USD_{t-k})` for lag `k ∈ {6, 9, 12}` months. Let `β_k` denote the OLS coefficient on `X_{t-k}` and let the **composite β** be defined as `β_composite ≡ β_6 + β_9 + β_12`.

Formal hypothesis test (one-sided):

- **H_0:** `β_composite ≤ 0`
- **H_1:** `β_composite > 0`

**Justification of one-sided test (lit-grounded, NOT data-grounded).** The §1 transmission chain (Baumol → US-Colombia ICT-labor wage arbitrage → US tech-firm offshoring of Section J labor at 6–12mo lag → Section J young-worker share↑) produces an unambiguous sign expectation. COP devaluation cheapens Colombian Section J labor in USD terms; on the Beerepoot-Hendriks 2013 + Errighi-Bodwell ILO 2017 mechanism this *increases* US tech-firm offshoring demand at the 6–12-month contracting horizon; on the Mendieta-Muñoz 2017 channel this *increases* the share of young Colombian workers absorbed into services rather than manufacturing. Both channels point the same direction. Section J is a strict subset of Pair D's Section G–T broad services where Pair D itself produced an unambiguous β = +0.137 PASS verdict; the Section-J-narrow re-test inherits the same sign expectation by construction. The two-sided alternative is theoretically uninformative — no published mechanism predicts that COP devaluation contracts ICT-section young-worker share at the 6–12-month horizon. The one-sided choice is locked at spec-authoring time; switching to two-sided post-data is anti-fishing-banned per §9.

**Composite-β framing rationale.** Lags 6 / 9 / 12 of `log(COP_USD)` are highly serially correlated (typical AR(1) ≈ 0.95+ at monthly frequency); individual `β̂_k` estimates have wide confidence intervals due to multicollinearity, but their *sum* `c'β̂ = β_6 + β_9 + β_12` (with `c = (0, 1, 1, 1)'` excluding intercept) is precisely estimated under the linear-restriction variance formula `Var(c'β̂) = c'Σ̂c`. The composite-β framing therefore tests the *cumulative* offshoring-cycle response across the 6–12mo contracting horizon as a single number, which is the economically meaningful quantity. This framing inherits Pair D §5.3 + MQS R1/R2 v1 closure verbatim.

**Sign expectation pin.** `β_composite > 0` is fixed at spec-authoring time. Inferring sign from data and *then* citing the mechanism is anti-fishing-banned per §9.

---

## §3. Falsification criteria (pre-pinned with concrete numerics)

The verdict on the primary OLS specification (spec §5) maps to one of four labels: **PASS**, **FAIL**, **ESCALATE**, or **SUBSTRATE_TOO_NOISY**. The first three are functions of the primary regression; the fourth is a function of robustness-row sign-flipping per §7. Numeric thresholds below are pinned at spec-authoring time and are not adjustable post-data. This carries forward Pair D §3 verbatim — same primitives, same numerics, applied to the Section-J-narrow Y construction.

### §3.1 PASS-trigger

`β_composite > 0` AND one-sided p-value `≤ 0.05`.

Rationale: conventional α = 0.05 inherited from the closed FX-vol-CPI Phase-A.0 pipeline and Pair D Stage-1 spec; one-sided per §2.

### §3.2 FAIL-trigger

`β_composite ≤ 0` AND one-sided p-value `> 0.05`. Rationale: non-positive composite β at non-significant p directly fails H_1.

**NOTE (per Pair D RC D1 v1 closure inherited):** §8.1-4(c) extends FAIL to the additional cell `β > 0 AND p > 0.20 AND Clause B does not fire`. §8 is the exhaustive verdict mapping; §3 enumerates trigger primitives only.

### §3.3 ESCALATE-trigger

ESCALATE fires if **either** of two clauses holds.

**ESCALATE Clause A:** `β_composite > 0` AND one-sided p-value `∈ (0.05, 0.20]`. Rationale: a positive composite β with p in the 5%–20% window is suggestive but inconclusive at conventional significance; the framework pre-authorizes (per CLAUDE.md "Abrigo Operating Framework" + Phase-A.0 Rev-2 §11.A convex-payoff insufficiency caveat) escalation to convex-payoff evidence before declaring FAIL. The same Clause A semantics applied in Pair D and produced no Clause-A fire there (β was significant at p = 1.46e-08); the clause is preserved here in case Section-J-narrow Y exhibits weaker mean-β signal due to smaller cell size.

**ESCALATE Clause B (concrete numerics):** `β_composite` near zero with high tail asymmetry, defined as both conditions holding simultaneously:

- **(B-i) "near zero":** `|β_composite| / SE(β_composite) < 0.5`. Rationale (pre-data conjecture): a t-statistic absolute value below 0.5 is well inside the standard "indistinguishable from zero" range in social-science econometrics; the 0.5 threshold is conservative and chosen to capture the convex-payoff-relevant case where the *mean* is uninformative but the *tails* may not be. NOT computed from the observed sample.
- **(B-ii) "high tail asymmetry":** `|skew(OLS residuals)| > 1.0` OR `excess kurtosis(OLS residuals) > 3.0`. Rationale (pre-data conjecture): standard financial-econometrics heuristics treat `|skew| > 1` as highly skewed and `excess kurtosis > 3` as heavy-tailed; both moments measure exactly the convex-payoff-relevant departure from Gaussianity that motivates the GARCH-X / EVT escalation suite. NOT computed from the observed sample.

The 0.5 / 1.0 / 3.0 numbers are pinned in this spec and do not move post-data. This inherits Pair D §3.3 + MQS R5 v1 closure structural-disjunction defense.

### §3.4 ESCALATE-PASS threshold (pre-pinned, concrete numerics)

When ESCALATE fires (Clause A or B), the escalation suite of §5.5 is run and a binary ESCALATE-PASS / ESCALATE-FAIL recorded. **ESCALATE-PASS** fires if **any one or more** of the three disjuncts below hold; otherwise **ESCALATE-FAIL**. Soft language ("credible" or similar) is anti-fishing-banned per §9.

- **(D-i) Quantile β:** the τ = 0.90 quantile-regression coefficient on `X_{t-9}` (representative middle-of-window lag) is `> 0` at one-sided p `≤ 0.10`.
- **(D-ii) GARCH-X β:** in a GARCH(1,1) with `log(COP_USD_{t-k})` for `k ∈ {6, 9, 12}` as exogenous mean-equation regressors, the composite GARCH-X mean β (sum of the three lag coefficients) is `> 0` at one-sided p `≤ 0.10`.
- **(D-iii) EVT β:** in peaks-over-threshold (POT) on upper-tail residuals from the primary OLS, the regression of exceedances on `log(COP_USD_{t-9})` yields a positive coefficient at one-sided p `≤ 0.10`.

The relaxed α = 0.10 vs. α = 0.05 (primary) is the standard escalation-tier convention in the Phase-A.0 spec lineage and Pair D Stage-1 precedent. Disjunctive "any one or more" semantics reflect the convex-payoff-evidence framing: each disjunct probes a different distributional moment; firing any one suffices for convex-instrument fitness.

**Structural-disjunction defense against multiple-testing critique (per Pair D MQS R5 v1 closure inherited).** This disjunction is NOT subject to multiple-testing correction (Bonferroni / Holm / BH-FDR) because each disjunct estimates a *distinct distributional-moment parameter* mapping to a *distinct convex-instrument design* (D-i quantile → range-LP / covered-call structure on Panoptic; D-ii GARCH-X → volatility-conditional perpetual; D-iii EVT → tail-risk put). ESCALATE-PASS records the existence of convex-payoff fitness *somewhere* in the design space, not a single-parameter rejection on three identical tests. MHT-correction would apply if all three estimated the same parameter and the question were "does at least one of three identical tests reject?"; the actual question is structurally different.

### §3.5 SUBSTRATE_TOO_NOISY trigger

If across the four robustness rows R1–R4 (§7) **more than 50%** produce `β_composite` of opposite sign from the primary, the verdict is **SUBSTRATE_TOO_NOISY** regardless of primary-row label. With four R-rows, "more than 50%" means strictly more than 2 out of 4 — i.e., 3 or 4 sign-flipped. Routes to a Y-construction revision (analog of P_D2 in Pair D's verdict tree) per §8.

### §3.6 N_MIN gate

If realized N (after §6 methodology-break treatment and §4 lag-window loss) falls below `N_MIN_OBS = 75` (Phase-A.0 floor), the spec HALTS per the §9 protocol. The N_MIN floor matches Phase-A.0 Rev-5.3.1 (per `project_rev531_n_min_relaxation_path_alpha`) and Pair D Stage-1. Expected realized N for Y_p is 134 (per Y feasibility memo §1); N_MIN floor exists as a guard against pathological cell-size shrinkage in Section-J-narrow Y due to GEIH per-month cell counts being structurally smaller than Pair D's broad-services aggregate.

---

## §4. Sample-selection rules

- **Frequency:** monthly.
- **Time window:** 2015-01 through 2026-03 inclusive (excluding any month within the most recent two-month publication-lag tail per Y feasibility memo §1.1 and Pair D feasibility precedent). The 2015-01 lower bound is **inherited from Pair D CORRECTIONS-α' Option-α'** (spec sha256 `964c62cca…ef659` §9.10): DANE pre-applied Rev.4 sector coding (`RAMA4D_R4` column) in Empalme catalogs only from 2015-01 onward; for 2010-2014 the Empalme files retain `RAMA4D` with Rev.3 codes, which would require author-judgment 1-to-many crosswalks banned by §9. Inheriting Pair D's window also pre-empts the schema-stability HALT cascade Pair D experienced (typed exception `PairDEmpalmeSchemaContradictsHarmonizationPin`, lesson recorded in memory `feedback_schema_pre_flight_must_verify_values`).
- **Lag-window loss + X-back-extension departure from Pair D (per MQS FLAG-5 v1.0 closure).** Raw 2015-01 → 2026-03 spans 135 monthly cells. Pair D's spec text (sha `964c62cca…ef659` §4 lines 110–111) accounted for lag-12 by dropping the 12 leading Y months: 135 − 12 = 123 candidate months, with Y starting at 2016-01. **Dev-AI departs from this convention by back-extending the X panel into 2014-01 → 2014-12** to preserve Y starting at 2015-01: the 12 leading X observations from 2014-01 through 2014-12 of `log(COP_USD)` are joined into the panel and consumed as regressors, while the dependent variable starts at 2015-01. Realized N is therefore expected to be approximately **134** (one-month tolerance for end-of-window publication-lag drop). **Justification:** Banrep TRM is available continuously back to 1991-12 (no data-availability constraint pre-2015 on the X side), so back-extending X into 2014 is mechanically trivial and preserves the maximum Y-window the §4 sample-window pin allows. The departure from Pair D's accounting is a Y-window-extension by 11 months (Y_eff = 2015-01 → 2026-03 = 134 mo vs. Pair D's Y_eff = 2016-01 → 2026-03 = 123 mo), NOT a lag-window re-tuning, and is therefore consistent with §9.4 lag-set immutability. Pair D's pipeline ultimately produced N=134 at the joint-panel commit — this spec adopts the actual-Pair-D-pipeline N convention rather than the Pair D spec-text convention. Plan Task 1.1 dispatch will require the implementing DE to explicitly extend the X panel to 2014-01 (NOT silently drop pre-2015 X observations).
- **Universe:** national aggregate (Cabecera + Resto summed, per GEIH feasibility §3 of the Pair D precedent; consumed via §5.1 below); no city-level or departmental-level disaggregation in the primary.
- **N_MIN floor:** `N_MIN_OBS = 75` per §3.6. Expected ≈ 134 is well above; floor exists to handle pathological cell-size shrinkage in the Section-J-narrow cell. Per Y feasibility memo §1.1 caveat, the Section J cell is ~700–1,200 14–28 employed per month vs. Pair D's broad-services aggregate of ~7,000–9,000; this is borderline for monthly stability but well above the N=75 monthly-observation floor (a separate issue from cell-count stability, discussed in §6).
- **Banned window contraction:** The `restrict-to-≥2022` window option (which collapses N to ≈ 39 monthly observations as of 2026-03, well below the floor) is BANNED per §6, mirroring Pair D §6 BANNED disposition.

The window pinning, lag-window-loss accounting, universe definition, N_MIN floor, and BANNED contraction are immutable per §9. Re-tuning of window boundaries post-data is anti-fishing-banned.

---

## §5. Methodology

### §5.1 Y construction (PRIMARY)

For each month `t`, define:

```text
                  sum over young-employed persons i of FEX_i * 1{CIIU_section_i == "J"}
Y_t (raw share) = ─────────────────────────────────────────────────────────────────────
                          sum over young-employed persons i of FEX_i

where:
  young-employed     = persons aged 14-28 inclusive (Ley 1622 de 2013) with
                       employment status Ocupado
  CIIU_section_i     = CIIU Rev. 4 A.C. section letter assigned to person i's
                       primary occupation, derived from RAMA4D_R4 4-digit code
                       via DANE's published Section-letter mapping
  Section J          = "Información y Comunicaciones" — Divisions 58 (Publishing
                       activities), 59 (Motion picture, video, TV), 60 (Programming
                       & broadcasting), 61 (Telecommunications), 62 (Computer
                       programming, consultancy & related), 63 (Information
                       service activities), per CIIU Rev. 4 A.C.
  FEX_i              = expansion factor (FEX_C_2018 throughout; the 2015-2026
                       window is post-Marco-2018 in the Empalme-corrected series
                       per Pair D §6 precedent)
  Cabecera + Resto are summed (national aggregate)
```

The dependent variable in the OLS is the **logit transform**:

```text
Y_t (logit) = log( Y_t (raw share) / (1 - Y_t (raw share)) )
```

**Logit-transform justification.** `Y_t` is bounded in `[0, 1]` and empirically lives in roughly `[0.04, 0.10]` per Y feasibility memo §5 (Section J cell-size estimate). The logit maps to the real line, validates OLS asymptotically without bounds enforcement, and renders coefficients as log-odds elasticities — textbook treatment for bounded dependent variables. Raw-OLS preserved as R3 (§7). This is technically correct on the same grounds as Pair D §5.1.

**Logit vs. fractional-response GLM (per Pair D MQS R3 v1 closure inherited).** The logit-OLS choice over Papke-Wooldridge 1996 fractional-response GLM (*Journal of Applied Econometrics* 11(6)) or Ferrari-Cribari-Neto 2004 beta regression (*Journal of Applied Statistics* 31(7)) is justified because the empirical Y range `[0.04, 0.10]` is well-interior to `(0, 1)` — nowhere near the 0/1 boundary that motivates the fractional-response treatment. Cameron-Trivedi *Microeconometrics* §16.4 endorses logit-OLS as standard for interior-bounded shares. Beta regression and fractional-response GLM are deferred as future-work robustness options but NOT pre-committed for this iteration.

**Section-J-specific logit-derivative amplification acknowledgment (per MQS FLAG-2 v1.0 closure).** While the empirical Y range `[0.04, 0.10]` is well-interior to `(0, 1)` (so logit is defined and finite throughout), the derivative `d/dY[logit(Y)] = 1/[Y(1-Y)]` varies substantially more across the Section-J support than across Pair D's broad-services support. Specifically:

- At Pair D's Y range `[0.55, 0.75]`: `d/dY[logit(Y)]` ranges from `1/(0.55 × 0.45) ≈ 4.04` at the lower bound to `1/(0.75 × 0.25) ≈ 5.33` at the upper bound. **Across-support ratio: 1.32×.**
- At dev-AI's Y range `[0.04, 0.10]`: `d/dY[logit(Y)]` ranges from `1/(0.04 × 0.96) ≈ 26.04` at the lower bound to `1/(0.10 × 0.90) ≈ 11.11` at the upper bound. **Across-support ratio: 2.34×.**

The **logit nonlinearity at Section J's share range is ~2.3× more curved** than at Pair D's. Operationally: a small raw-share level error (e.g., DANE empalme residual after Marco-2018 frame change, or sectoral-classification-boundary noise in `RAMA4D_R4`) maps to a **2-6× larger logit-Y level error** at Section J's range than at Pair D's. The §6 empalme-residual-bias acknowledgment (`d/dY[logit(Y)] = 1/[Y(1-Y)]` varying across the support) is therefore *more* load-bearing here than in Pair D, and the design's hedges against this amplification are: (a) the §6 R1 (2021 regime dummy on logit-Y) which probes whether the empalme residual interacts with the methodology-break disposition; (b) the §7 R3 (raw-OLS, no logit transform) which sidesteps the nonlinearity entirely; (c) the §6 cell-size HALT-only fallbacks (§9.5 protocol) which catch sample-variance-driven Y volatility before it propagates through the logit derivative. Cross-reference: §6 line 244 (empalme residual-bias) AND §7 R3 (raw-OLS robustness) bind to this amplification concern. Promoting a primary-PASS verdict without acknowledging the Section-J-specific amplification in the Phase-4 result memo when R1 / R3 are inconsistent with the primary is anti-fishing-banned per §9.

**CIIU revision boundary handling (per Pair D RC D3 v1 closure inherited; further simplified by Option-α' window).** The Y_p sample window 2015-01 → 2026-03 is fully in the **CIIU Rev. 4 A.C. era** (DANE Resolution 066 of 2012-01-31 mandates Rev. 4 A.C. starting 2012-01); furthermore, DANE's `RAMA4D_R4` field is value-content-verified for the entire 2015-2026 Empalme window (per Pair D §9.10). There is therefore NO CIIU Rev. 3.1 → Rev. 4 boundary inside the Y_p window. The 4-digit `RAMA4D_R4` code is mapped to Section letters via DANE's published Section table; **Section J corresponds to 4-digit codes whose Division (first 2 digits) is in the set {58, 59, 60, 61, 62, 63}, with Section-letter assignment determined by DANE's published Section table for CIIU Rev. 4 A.C.** (per MQS NIT-2 v1.0 closure: this Division-list formulation supersedes the prior "4-digit codes 5811–6399 inclusive of all sub-classes" range expression which admitted non-existent CIIU codes as a literal numeric range; the Division-list formulation is structurally identical for canonical Section-letter mapping but rules out the literal-range misreading). Implementation-deferred to plan Task 1.1 with the constraint that the deterministic Section-J indicator must be unambiguous for every month in the window or the spec HALTS per §9.

**Sensitivity Y constructions (NOT primary, defined here for §7 robustness universe and §5 pre-commit).** Per Y feasibility memo §5, three sensitivity Y arms are pre-pinned:

- **Y_s1 — DANE EMS Section J nominal-income index** (Encuesta Mensual de Servicios; aggregate index, NOT micro-data; base 2018=100; monthly cadence; window 2018-01 → 2026-03; N=87 post-lag-12; **pre-committed 2020-01 regime dummy = 1 for `t ≥ 2020-01`, 0 otherwise; option (a) per Y feasibility memo §1.2 line 73 — options (b) restrict-to-2020+ window (UNVIABLE — N drops below N_MIN) and (c) accept-the-break-as-noise are explicitly rejected at spec-authoring time per MQS NIT-1 v1.0 closure**). Y_s1 is NOT included in the R1-R4 robustness universe of §7 (which are all single-row alternatives to the primary OLS specification). Y_s1 is reserved for downstream cross-validation if the §7 R-row consistency classification yields MIXED.
- **Y_s2 — GEIH young-worker share in Section M ("Actividades profesionales, científicas y técnicas")** (CIIU Rev. 4 A.C.; same micro-data source as Y_p; same monthly cadence; same 2015-01 → 2026-03 window; logit transform; N=134 post-lag-12). Probes the ICT-subsector boundary (Section M is the broader knowledge-worker cell, structurally adjacent to Section J). Activated as **R2 of §7** (replaces Pair D's "Y narrow J+M+N" R2 row with an even-narrower Section-J-vs-Section-M comparison).
- **Y_s3 — UNCTADstat EBOPS-9 cross-LATAM annual panel** (6 countries CO/MX/BR/AR/PE/CL; 2008-2024 annual; log-transform; country fixed effects; AR credibility regime dummy 2007-2015; cluster SEs by country; N_panel = 102 cells). Cadence-mismatched (annual vs Pair D's monthly anchor) — secondary by design and reserved for downstream regional-validity sensitivity if Stage-2 M-sketch authoring requires cross-LATAM evidence. NOT activated in §7 R1-R4 robustness universe.

### §5.2 X construction

For each month `t`, define `COP_USD_t` as the end-of-month spot exchange rate from the **Banrep TRM (Tasa Representativa del Mercado) public API**, sourced via the same pipeline that powered the closed FX-vol-CPI Phase-A.0 work and Pair D Stage-1 (per Y feasibility memo §1 lead paragraph: "X side is fixed... USD/COP lagged 6–12 mo via central-bank reference rates is feasible via Banrep TRM... Pair D already validated the Banrep TRM piece"). The lag panel is constructed at `k ∈ {6, 9, 12}` months; the regressors are `log(COP_USD_{t-k})` for each lag.

**Anti-fishing transparency on X re-use.** This iteration uses the *same* COP/USD variable as Pair D under a *different* (Y, transmission-channel-hypothesis) pair (Section-J-narrow ICT services vs. Pair D's broad services Section G–T). The Pair D PASS verdict (β = +0.137, p = 1.46e-08, 2026-04-28) does NOT taint this test — Pair D and this iteration test different Y constructions with different mechanism narrowings. However, the re-use of the same X variable is acknowledged here in the same anti-fishing-transparency spirit Pair D itself disclosed when re-using the FX variable that powered the closed FX-vol-CPI-surprise pipeline.

**X is monthly end-of-month spot.** Daily TRM is aggregated to month-end-spot (last published trading day of month `t`), not month-average. This matches Pair D §5.2 verbatim.

---

### §5.3 Primary specification

The primary OLS specification is:

```text
Y_t (logit) = α + β_6 · log(COP_USD_{t-6})
                + β_9 · log(COP_USD_{t-9})
                + β_12 · log(COP_USD_{t-12})
                + ε_t
```

The composite β tested in §3 hypotheses is `β_composite = β_6 + β_9 + β_12`. The composite-coefficient hypothesis is tested via a one-sided linear restriction (sum of three coefficients greater than zero); the standard error of the composite is computed via the **linear-restriction variance formula `Var(c'β̂) = c'Σ̂c` for `c = (0, 1, 1, 1)'`** (per Pair D MQS R1 v1 closure inherited: "delta method" is technically misnamed for a linear restriction; the closed-form linear formula applies, no Taylor expansion needed). Equivalent to the standard restricted-OLS variance / Wald-restriction variance. The one-sided p-value is one-half the two-sided Wald p-value when the point estimate is in the hypothesized direction, and 1 minus that quantity otherwise.

**Multicollinearity / composite-SE acknowledgment (per Pair D MQS R2 v1 closure inherited).** Lags 6/9/12 of `log(COP_USD)` are highly serially correlated (typical AR(1) ≈ 0.95+ at monthly frequency), inflating individual `Var(β̂_k)` estimates. However, the composite is `c'β̂` and `Var(c'β̂) = Σ_k Var(β̂_k) + 2 Σ_{j<k} Cov(β̂_j, β̂_k)`; the covariance terms are **negative** when regressors are positively collinear, so the composite SE is *deflated* relative to the sum-of-individual-SEs intuition. The composite test is therefore precise even when individual lag coefficients have wide CIs. The result memo (Phase 4) MUST explicitly acknowledge this — a reading of "individual lags weren't significant!" is methodologically incorrect; the spec tests the composite and the composite alone. Pair D's PASS verdict (β = +0.137) was concentrated at lag-6 (≈80% of composite per Pair D Stage-1 PM late evening MEMO §1 RC FLAG #3); this iteration may exhibit a similar concentration profile or a different one — both are consistent with the composite-β framing as long as the composite point estimate has the hypothesized sign.

**Regression standard errors.** The primary specification reports OLS standard errors (homoskedasticity-assuming). HAC (Newey-West) standard errors with lag truncation `L = 12` are the **R4 robustness row** of §7 — this is intentional, since Pair D's PASS verdict survived HAC SE substitution at p = 1.46e-08 → p = 0.0000... at HAC; the R4 row is a pre-committed robustness diagnostic and not a primary-spec choice.

### §5.4 Lag-window justification

The 6–12 month window is the **offshoring-decision contracting-cycle horizon** documented in BPO research note §3 (Beerepoot-Hendriks 2013 + Errighi-Bodwell ILO 2017; offshoring contracts are typically annually re-tendered with quarterly review). The three lags `{6, 9, 12}` evenly span the window. Free lag tuning (e.g., sweeping `k = 1, ..., 24` and selecting on fit) is anti-fishing-banned per §9.4.

**Section-J-narrow lag-window inheritance.** The 6–12mo offshoring horizon applies to Section J labor demand identically as it applies to Pair D's broad services — US tech-firm offshoring contracts to Colombian Section J vendors (software shops, telecom, data-processing firms) are re-tendered on the same annual-with-quarterly-review cycle. There is no first-principles reason to expect a different lag-window for ICT-narrow vs. broad-services offshoring; if Stage-1 estimation reveals different lag-concentration patterns (e.g., β_6 dominating vs. β_12 dominating), this is a Stage-2 M-sketch design input but does NOT motivate post-data lag-window re-tuning per §9.4.

### §5.5 Escalation methodology (conditional on §3.3 ESCALATE-trigger)

If ESCALATE fires, three procedures are run, mapped to §3.4:

- **Quantile regression** (D-i): conditional quantile regression of `Y_t (logit)` on the three lagged-X regressors, estimated at `τ = 0.90`. Tests whether the *upper-tail* of Y's conditional distribution responds positively to FX devaluation — the convex-payoff-relevant moment for a Panoptic perpetual that pays out on extreme Section-J-employment-share realizations.
- **GARCH-X** (D-ii): GARCH(1,1) on `Y_t (logit)` with the three lagged-X regressors entering the mean equation as exogenous covariates. Tests whether mean-β remains positive under explicit time-varying-volatility correction. The composite GARCH-X β is the sum of the three lag mean-equation coefficients.
- **EVT POT** (D-iii): peaks-over-threshold on upper-tail residuals from the primary OLS (threshold = empirical 0.90 residual quantile); exceedances regressed on `log(COP_USD_{t-9})`. Tests whether *extreme positive* residual realizations covary with X — the most direct EVT-style test of tail-region β.

Each yields a coefficient and one-sided p-value; the §3.4 disjunction is evaluated against these. The escalation suite is run if and only if §3.3 ESCALATE-trigger fires per §8 verdict tree; running it speculatively when the primary regression PASSes at §3.1 is anti-fishing-banned per §9.6 (escalation as pre-authorization, not post-hoc rescue).

**Escalation precedent from Pair D.** Pair D pre-authorized this same escalation suite and did not need to invoke it (PASS verdict at §3.1). The current iteration inherits the suite verbatim with the same numerics; if Section-J-narrow Y produces a weaker mean-β signal due to smaller cell size, escalation is the pre-authorized mechanism for testing convex-instrument fitness.

---

## §6. Methodology-break disposition (pre-pinned)

DANE switched the GEIH master sample from Marco 2005 (population frame derived from the 2005 Census) to Marco 2018 (frame from the 2018 Census) effective January 2021. 2021 was a parallel-collection year; from January 2022 onward, only Marco 2018 is published. DANE has published an empalme (splice) factor in `FEX_C` covering 2010-01 through 2020-12 inclusive per the nota técnica (`Nota-tecnica-empalme-series-GEIH.pdf`, GEIH feasibility §Q4 + Pair D §6). Per Pair D CORRECTIONS-α' clarification (spec sha256 `964c62cca…ef659` §9.10): DANE pre-applied **Rev.4 sector coding** (`RAMA4D_R4` column) in Empalme catalogs only from **2015-01 → 2020-12 (72 months)**; for 2010-2014 the Empalme files retain `RAMA4D` with Rev.3 codes (out of scope under the 2015-01 window).

**Primary disposition:** apply the DANE empalme factor for Marco-2005 → Marco-2018 reconciliation per the published nota técnica. Within the §4 sample window 2015-01 → 2026-03, the empalme is applied to the 2015-01 → 2020-12 segment (72 months of the in-scope window); the 2021-01 → 2026-03 segment is post-Marco-2018 and uses native FEX_C_2018 expansion factors without empalme. The empalme is applied to `Y_t` (raw share) before the logit transform of §5.1.

**Robustness disposition R1:** instead of the empalme factor, include a 2021 regime dummy (1 for `t ≥ 2021-01`, 0 otherwise) as an additional regressor in the OLS. This is row R1 of §7. Inherits Pair D §6 R1 verbatim.

**BANNED disposition:** restrict the sample to `t ≥ 2022-01` (Marco-2018-only). This collapses N to approximately 39 monthly observations as of 2026-03 — well below the `N_MIN_OBS = 75` floor of §3.6. Invoking this disposition would constitute an anti-fishing violation per §9. (Pair D banned this same disposition for the same reason at the same N collapse, per Pair D §6 BANNED.)

**Empalme residual-bias acknowledgment (per Pair D MQS R4 v1 closure inherited — substantive limitation).** The DANE empalme corrects for population-frame level shift (Marco 2005 → Marco 2018) but does NOT correct: **(a)** the *nonlinear interaction* of a raw-share level shift with the §5.1 logit transform (`d/dY[logit(Y)] = 1/[Y(1-Y)]` varies across the support, so an empalme calibrated for raw-share linearity does not necessarily neutralize bias in the logit-transformed series); or **(b)** any *sectoral classification changes* between Marco 2005 and Marco 2018 master-sample frames (the empalme handles the population frame, not the sector codings; though within the §4 window 2015-01 → 2026-03 the sector coding `RAMA4D_R4` is value-content-stable per Pair D §9.10). R1 (2021 regime dummy on logit-Y) is the design's hedge against (a); R2 (Section M instead of Section J — see §7) partially probes Section-boundary stability. Residual bias surviving both R1 and R2 is a known limitation that MUST be acknowledged in the Phase-4 result memo; promoting a primary-PASS verdict without this acknowledgment when R1 and R2 are inconsistent with the primary is anti-fishing-banned per §9.

**Section-J cell-size stability (additional Section-J-specific concern, not present in Pair D).** Per Y feasibility memo §1.1 caveat, the Section J cell is structurally smaller than Pair D's broad-services aggregate (~700–1,200 14–28 employed per month vs. ~7,000–9,000). Smaller cell counts increase month-to-month sampling variance in the raw share `Y_t`. Pre-registered fallbacks if monthly-Y volatility produces unstable HAC standard errors:

- **Fallback (i):** 3-month rolling-average `Y_t` (each month is the average of months `t-1`, `t`, `t+1` raw shares; logit-transform on the averaged share). NOT pre-committed as primary. **Trigger restructured per MQS FLAG-3 v1.0 closure**: invocation of fallback (i) requires the §9.5 HALT-disposition protocol UNCONDITIONALLY — (1) typed exception raised by executing specialist documenting observed cell-size pathology (e.g., observed monthly cell-count < threshold, observed HAC SE explosion, observed residual variance instability); (2) disposition memo at `contracts/.scratch/2026-05-XX-dev-ai-section-j-cell-pathology-disposition.md` enumerating ≥3 pivot options including fallback (i) AND fallback (ii) AND alternative-Y promotion (Y_s2 Section M); (3) user surface; (4) user picks the pivot; (5) CORRECTIONS block lands in next plan revision; (6) 3-way review of CORRECTIONS revision before any further execution. **The prior v1.0 trigger language "5× the median monthly variance estimated from Pair D's Section G–T precedent at the same window" is REMOVED** because the unpinned reference admitted post-data-tuning footgun (which Pair D residual variance? primary spec? R1? R4-HAC? at what data revision?). Fallback (i) trigger evaluation IS itself a §9.5 HALT, never a primary-spec auto-fallback.
- **Fallback (ii):** quarterly aggregation (Y_q = average of three monthly raw shares within quarter `q`; logit-transform on quarterly share; quarterly X_q = end-of-quarter spot; lag panel `k_q ∈ {2, 3, 4}` quarters approximating 6/9/12 months). N_quarterly post-lag-4 ≈ 41 — below N_MIN. UNVIABLE as primary; reserved as cross-validation only.

These fallbacks are **NOT** activations the primary spec triggers; they are pre-registered for documentation only. The primary spec runs monthly Section-J Y as defined in §5.1 with the §6 empalme disposition; any pivot to a fallback requires the §9.5 HALT protocol.

---

## §7. Robustness checks (pre-committed)

Four robustness rows are pre-committed. Each is a single-row alternative that varies exactly one design choice from the primary; multi-dimensional re-specification (varying two or more dimensions simultaneously) is anti-fishing-banned per §9. Each row produces its own `β_composite` estimate.

- **R1 — 2021 regime dummy** (alternative to §6 primary methodology-break disposition). Same primary specification but replace empalme with a 2021 regime dummy. Inherits Pair D R1 verbatim.
- **R2 — Y narrow** (CIIU Rev. 4 Section M only — "Actividades profesionales, científicas y técnicas"). Same primary specification but recompute `Y_t (raw share)` with the numerator restricted to Section M employment instead of Section J; logit transform unchanged. Probes the ICT-subsector-vs-knowledge-worker boundary: Section J is ICT-narrow; Section M is the broader knowledge-worker cell. If Section M produces a sign-flipped β, that signals the §1 mechanism is concentrated in ICT-narrow rather than knowledge-worker-broad. **NOTE:** This R2 differs from Pair D's R2 (which used Section J + M + N "BPO-narrow") because the primary Y is *already* narrow (Section J alone), so the meaningful comparison is to a sibling-narrow sector (Section M) rather than to a broader aggregate.
- **R3 — raw OLS** (no logit transform). Same primary specification but the dependent variable is the raw share `Y_t` instead of `Y_t (logit)`. This is the bounded-range diagnostic (per §5.1 caveat). Inherits Pair D R3 verbatim.
- **R4 — HAC standard errors** (Newey-West, lag truncation `L = 12`). Same primary specification and same point-estimate `β̂_composite` but with HAC standard errors substituted for the OLS standard errors; the one-sided p-value is recomputed against the HAC SE. This is the autocorrelation diagnostic. Inherits Pair D R4 verbatim.

**Robustness universe immutability.** R1-R4 as defined above are the COMPLETE robustness universe. Adding R5+ post-data, swapping any R-row for a different alternative, or activating Y_s1 (DANE EMS index) or Y_s3 (UNCTADstat panel) as in-universe robustness rows is anti-fishing-banned per §9.2. Y_s1 and Y_s3 are reserved as downstream cross-validation arms (per §5.1) only if §7.1 R-row consistency classification yields MIXED.

### §7.1 R-row consistency classification (pre-pinned)

After all four rows are estimated, classify per the following rule:

- **AGREE:** all four R-rows produce `β_composite` with the same sign as the primary specification (regardless of significance).
- **MIXED:** between one and two R-rows produce sign-flipped `β_composite` relative to the primary.
- **DISAGREE:** three or four R-rows produce sign-flipped `β_composite` relative to the primary. This triggers the SUBSTRATE_TOO_NOISY verdict per §3.5.

Sign comparison uses the primary-specification `β_composite` as the reference; an R-row "matches" the primary if its `β_composite` has the same strict sign (positive vs. non-positive). Significance is not required for sign-matching; this is intentional — sign stability is the diagnostic, not significance stability. Inherits Pair D §7.1 verbatim. Pair D itself produced **AGREE 0/4 sign-flips** at PASS verdict 2026-04-28; this iteration may produce AGREE / MIXED / DISAGREE depending on Section-J-narrow specifics.

---

## §8. Verdict-decision tree (deterministic mapping)

The tree maps `(β_composite_sign, p_one_sided, R_row_consistency, Clause-B fires?)` to a verdict in `{PASS, FAIL, ESCALATE, SUBSTRATE_TOO_NOISY}`, plus the HALT-N_MIN path. Mapping is exhaustive: every tuple → exactly one verdict; no leaf maps to "TBD" or "specialist judgment." Inherits Pair D §8 verbatim — same structure, same numerics, same routing.

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

Per Pair D plan Task 0.1 Step 2 sub-checklist precedent, every leaf is exercised:

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

Drives downstream disposition per the Stage-1/2/3 lifecycle of the Abrigo Operating Framework:

- **PASS** → unblock Stage-2 M-sketch authoring (separate downstream spec). The dev-AI Stage-2 will sketch a Panoptic perpetual on a Section-J-or-equivalent reference index, with strike geometry calibrated from this PASS verdict's β_composite point estimate and HAC-CI bounds.
- **ESCALATE-PASS** → unblock Stage-2 M-sketch with explicit convex-payoff documentation. The escalation suite output (which disjunct(s) fired) becomes a primary input to the Stage-2 strike-geometry choice (D-i quantile → range-LP; D-ii GARCH-X → vol-conditional perpetual; D-iii EVT → tail-risk put).
- **ESCALATE-FAIL** → dev-AI iteration's Y_p (Section J share) DROPPED. Routing options: (i) re-rank Y_s1 / Y_s2 / Y_s3 sensitivity arms as candidate replacement primary Y in a Y_p2 iteration; (ii) re-evaluate the §1 mechanism narrowing (Section J vs. Section M vs. broader knowledge-worker aggregate) and re-author the spec accordingly. NEITHER option is auto-pivoted; routing requires the §9.5 HALT-disposition protocol (typed exception, disposition memo, user pivot, CORRECTIONS block, 3-way review).
- **FAIL** (no escalation triggered) → same as ESCALATE-FAIL routing.
- **SUBSTRATE_TOO_NOISY** → identify methodology improvements for a Y_p revision (analog of P_D2 in Pair D's tree; e.g., switch to fallback (i) 3-month rolling Y, switch to Y_s2 Section M, etc.). Methodology improvements are NOT auto-pivoted; routing requires §9.5 HALT-disposition.
- **HALT-N_MIN** → §9.5 HALT-disposition path.

**Stage-2 / Stage-3 dependence.** Stage-2 M-sketch authoring requires a PASS or ESCALATE-PASS verdict at Stage 1. Stage-3 deployment requires a PASS verdict at Stage 1 plus the Stage-2 M-sketch plus live Panoptic LP capital + execution test. Conflating stages — e.g., authoring Stage-2 M-sketch content in this Stage-1 spec, or claiming Stage-3 deployment readiness from Stage-1 PASS alone — is anti-fishing-banned per §9.

---

## §9. Anti-fishing invariants

These invariants are immutable for this iteration; they carry forward the Phase-A.0 pattern documented in `feedback_pathological_halt_anti_fishing_checkpoint` and the Pair D Stage-1 pattern (spec sha256 `964c62cca…ef659` §9). Any threshold or design-element revision triggers a §9.5 HALT-disposition with CORRECTIONS-block, user pivot, and 3-way review before further execution.

- **§9.1 Threshold immutability.** No threshold in this spec — α = 0.05 (primary) / α = 0.10 (escalation) / `N_MIN_OBS = 75` / Clause B numerics (`|β̂|/SE < 0.5`, `|skew| > 1.0`, `excess kurtosis > 3.0`) / SUBSTRATE_TOO_NOISY > 50% sign-flip / R-row consistency rules — may be adjusted post-data. Any normative revision recomputes the spec sha256 and re-triggers Wave 1 + Wave 2 verification.

- **§9.2 Y-construction immutability.** The §5.1 PRIMARY construction (Y_p = Section J young-worker (14–28) employment share, national aggregate, logit transform, FEX_C_2018 expansion factors, RAMA4D_R4 4-digit codes mapped to Section J via DANE Section table) is fixed at spec-authoring time. Sensitivities at 18–28 / 18–24 / 15–24 age bands, promoting Y_s1 (DANE EMS index) or Y_s3 (UNCTADstat panel) to primary, switching from Section J to Section M as primary, promoting raw-share to primary, Bogotá-only restriction, or any other Y reformulation post-data are anti-fishing-banned. The pre-committed sensitivity universe is exhausted by R1–R4 of §7. Y_s1 / Y_s2 / Y_s3 are downstream cross-validation arms, NOT in-universe robustness rows.

- **§9.3 Sample-window immutability.** The 2015-01 → 2026-03 monthly window of §4 is fixed. Re-curation post-data (excluding 2020 COVID months, excluding 2021 parallel-collection, restricting to post-2022, extending earlier to 2008-2014) is anti-fishing-banned. The §6 methodology-break disposition is pre-pinned; `restrict-to-≥2022` is explicitly BANNED. The 2015-01 lower bound inherits Pair D CORRECTIONS-α' Option-α' rationale verbatim — DANE-canonical Rev.4 sector coding (`RAMA4D_R4`) is value-content-verified for the entire 2015-2026 window; pre-2015 windows admit Rev.3 contamination requiring author-judgment crosswalks banned by §9.2.

- **§9.4 Lag-set immutability.** The set `k ∈ {6, 9, 12}` is fixed per §5.4. Free lag tuning, post-data addition of non-{6, 9, 12} lags, or post-data inversion to leading rather than lagging X is anti-fishing-banned. Section-J-narrow-vs-broad-services Y is NOT a justification for re-tuning the lag window — the §1 offshoring-contracting-cycle horizon applies identically across services subsectors per §5.4.

- **§9.5 HALT-disposition path.** Any HALT condition — `N < N_MIN`, schema-stability failure (analog of Pair D Task 1.1 Step 0 / Step 1 HALTs), DANE-side data anomaly, Section-J cell-size pathological shrinkage triggering §6 fallback (i) or (ii) consideration, or any reviewer-flagged threshold-tuning / Y-re-construction / escalation-rescue-claim — invokes the protocol from `feedback_pathological_halt_anti_fishing_checkpoint`: (1) typed exception raised by executing specialist; (2) disposition memo filed by Foreground Orchestrator at `contracts/.scratch/2026-05-XX-dev-ai-<halt-reason>-disposition.md` enumerating ≥3 pivot options; (3) user surface; (4) user picks the pivot; (5) CORRECTIONS block lands in the next plan revision documenting disposition + chosen pivot + rationale; (6) 3-way review of the CORRECTIONS revision before any further execution. Auto-pivot is anti-fishing-banned.

- **§9.6 Escalation as pre-authorization, not post-hoc rescue.** The §5.5 + §3.4 escalation suite was pre-authorized in this spec before any data was pulled. Framing escalation in the result memo as "rescue" is anti-fishing-banned; the framing must be "pre-pinned convex-payoff evidence test, ran whether or not mean-OLS passed" — the same discipline maintained by the closed FX-vol-CPI pipeline (`project_fx_vol_econ_complete_findings`) on its A1 monthly + A4 release-day-excluded sensitivities, and by Pair D Stage-1 on its escalation-suite pre-authorization (which Pair D ultimately did not need to invoke at PASS verdict).

- **§9.7 Spec sha256 governance.** Once the spec sha256 is computed and quoted in the dependent implementation plan frontmatter, it governs every downstream artifact: data parquets, notebooks, result tables, memo, gate_verdict.json, and the CLAUDE.md "Abrigo Operating Framework" Active iteration block update. Any artifact not citing the pinned sha256 is non-canonical and must be revised before commit.

- **§9.8 Phase-A.0 + Pair D invariant carryforward.** This iteration inherits the Phase-A.0 pre-registration discipline, spec sha256 pin, CORRECTIONS-block-on-revision pattern, Pair D §9 invariants, and the principle that closed iterations inform the next iteration's prior rather than re-running the same iteration at adjusted thresholds.

- **§9.9 Sibling-iteration X re-use disclosure.** This spec re-uses the COP/USD X variable that powered Pair D Stage-1 (PASS verdict 2026-04-28 at β = +0.137, p = 1.46e-08). The re-use is pre-disclosed in §1 + §5.2; the iteration's distinguishing feature is Y narrowing from Pair D's Section G–T to Section J alone with a parallel transmission-channel narrowing from BPO-flavored services-broad to ICT-narrow tech-services offshoring. Re-using the same X across two iterations with different Y constructions is NOT itself anti-fishing — the analog of running multiple regressions on the same X with different Ys is standard cross-validation. What WOULD be anti-fishing is failing to disclose the re-use, or selecting Y_p Section J post-data because it produced a better β than alternative narrow cuts considered. Y_p Section J was selected pre-data per Y feasibility memo §5 PRIMARY recommendation; this spec consumes that pre-pin verbatim.

- **§9.10 Sibling-iteration FX-vol-CPI X re-use disclosure (transitive).** Pair D itself re-used the COP/USD variable that powered the closed FX-vol-CPI pipeline (gate verdict FAIL 2026-04-19; see Pair D §1 + memory `project_fx_vol_econ_complete_findings`). This dev-AI-cost iteration is therefore the *third* iteration in the Pair D X-lineage (FX-vol-CPI FAIL → Pair D PASS → dev-AI Stage-1 pending). The transitive disclosure: the prior FX-vol-CPI FAIL does not taint Pair D, and Pair D's PASS does not taint dev-AI Stage-1, because each iteration tests a different (Y, mechanism) pair. But the X-lineage transparency is required at every link, and is recorded here for full traceability.

- **§9.11 Stage-1-only scope.** This spec governs Stage-1 ONLY. Authoring Stage-2 M-sketch content (Panoptic strike geometry, perpetual / range-LP / iron-condor structure, on-chain pool selection, LP capital sourcing) or Stage-3 deployment content (live LP, execution test, premium / payout plumbing) in this spec is anti-fishing-banned per §9.5 stage drift discipline. Stage-2 / Stage-3 are separate spec authoring tasks dispatched only after this Stage-1 spec produces a PASS or ESCALATE-PASS verdict.

- **§9.12 a_s / a_l explicit out-of-scope.** Per CORRECTIONS-ι (`contracts/.scratch/path-b-stage-2/phase-1/corrections_iota_a_s_framing.md`), a_s is a per-user instrument balance sheet calibrated at Stage-2 from AI-vendor public pricing + DevSurvey LATAM cohort distributions; a_s is NOT a country-aggregate macroeconomic variable. Including a_s as a regressor or as a Y-construction component in this Stage-1 spec is anti-fishing-banned per §9.11 stage drift. Per CORRECTIONS-θ, a_l (on-chain LP yield vaults; v1.5-data substrate panel) is similarly Stage-2/3 only and NOT a Stage-1 input. The Y_s3 UNCTADstat EBOPS-9 cross-LATAM panel discussed in §5.1 is a Y SENSITIVITY ARM at the cross-LATAM aggregate level — it is NOT a_s, and the anti-conflation note in Y feasibility memo §1 binds: nesting a_s framing through BoP "computer services imports" requires four lossy fractions (ICT → SaaS → AI → developer-paid LATAM-resident) that CORRECTIONS-ι rejects.

- **§9.13 Off-chain Y mandate (per CORRECTIONS-θ).** Y must come from off-chain national-statistics-agency / central-bank / developer-survey sources; the v1.5-data on-chain substrate panel is reserved for a_l (Stage-2/3) and is NOT a Stage-1 Y input. Y_p (DANE GEIH micro-data) honors this; Y_s1 (DANE EMS), Y_s2 (DANE GEIH Section M), and Y_s3 (UNCTADstat panel) all honor this. Substituting on-chain volume / on-chain user counts / on-chain AI-protocol activity as Y in this Stage-1 spec is anti-fishing-banned per §9.11 stage drift and §9.13 off-chain mandate.

- **§9.14 Free-tier methodology only (per CORRECTIONS-δ inheritance).** All data sources for Y, X, sensitivity arms, and any escalation-suite inputs must be free-tier accessible. Paid-tier data sources (Sensor Tower / AppMagic LATAM AI-app revenue, Stripe Atlas LATAM, paid Meetup Pro API, paid INEGI tokens beyond the standard free token) are NOT permitted for Stage-1 work. The §6 HALT-and-surface candidates listed in Y feasibility memo §6 are explicitly out-of-scope.

- **§9.15 Code-agnostic discipline.** Per `feedback_no_code_in_specs_or_plans`: this spec contains no executable code, no SQL, no Python, no R. ASCII pseudo-equations and pseudo-code-blocks (`text`-fenced) are permitted for methodology specification. Any executable code must live in the dependent implementation plan + supervised execution artifacts, NOT in this spec.

- **§9.16 Compositional-accounting verdict-interpretation discipline (NEW per MQS FLAG-1 HIGH + RC FLAG-1 v1.0 closure).** Section J ⊂ Pair D Section G–T is a strict-subset relationship (per §1 compositional-accounting risk acknowledgment). A positive `β_composite` on Y_p (Section J) at Stage-1 PASS / ESCALATE-PASS is consistent with EITHER (i) the dev-AI-cost transmission mechanism firing independently at the ICT-narrow subsector level, OR (ii) Section J's compositional contribution to Pair D's broad-services PASS — i.e., a re-discovery of the Pair D signal aggregated up to ICT. **The Stage-1 verdict here cannot distinguish these two possibilities without a Section-J-vs-Section-(G–T-minus-J) decomposition.** Any Phase-4 result memo emitted from this iteration MUST include (a) explicit acknowledgment of the compositional-accounting ambiguity; (b) a `β_composite_section_J` vs `β_composite_pair_D_inherited` comparison reading from the `project_pair_d_phase2_pass` memory verbatim; (c) a flagged-not-resolved status on which of (i) or (ii) is operative. Stage-2 M-sketch dispatch (if invoked downstream of a Stage-1 PASS / ESCALATE-PASS verdict) MUST address the decomposition explicitly — either by adding the deferred R5 robustness arm (primary spec on Sections G–T minus J) as a v1.1 spec revision OR by calibrating hedge geometry against the ICT-services-direct sub-component (Divisions 62–63) per the §1 sub-aggregate-substitutability flag rather than against the Section J aggregate `β_composite`. Promoting a Stage-1 PASS verdict to Stage-2 / Stage-3 dispatch *without* this disclosure is anti-fishing-banned. The R5 robustness arm "primary spec on (Sections G–T minus J)" is hereby PRE-AUTHORIZED for v1.1 spec revision under the conditional gate: user explicitly invokes the design change (option from disposition memo Option C) OR Stage-2 dispatch surfaces the need (i.e., post-Stage-1 PASS, Stage-2 M-sketch authoring requires the decomposition to calibrate hedge geometry).

---

## §10. Self-review checklist

Filled in at spec-authoring time per the chunked-authoring discipline of `feedback_background_agent_stream_watchdog_timeout`. Items below verify spec completeness against Pair D format precedent + dispatch brief requirements.

| # | Check | Status |
|---|-------|--------|
| 1 | Frontmatter present with `spec_version`, `decision_hash` (sentinel), `decision_hash_protocol`, `parent_iteration_pin`, `sibling_pass_precedent`, `dependent_plan` (deferred), `verifier_v1_wave1` (pending), `verifier_v1_wave2` (pending), `revision_history` | YES |
| 2 | §1 Background cites Abrigo Operating Framework, Pair D Stage-1 PASS, CORRECTIONS-η/θ/ι chain, Mendieta-Muñoz 2017 + Beerepoot-Hendriks 2013 + Errighi-Bodwell ILO 2017 lit anchors, Section J vs Pair D G–T narrowing | YES |
| 3 | §2 Hypothesis: H_0 / H_1 stated formally, one-sided test, lit-grounded sign justification, composite-β framing rationale | YES |
| 4 | §3 Falsification criteria: PASS / FAIL / ESCALATE-A / ESCALATE-B / ESCALATE-PASS / SUBSTRATE_TOO_NOISY / N_MIN gate all pre-pinned with concrete numerics (0.05 / 0.20 / 0.50 / 1.0 / 3.0 / 0.10 / 75 / 50%) | YES |
| 5 | §3.4 ESCALATE-PASS structural-disjunction MHT defense present | YES |
| 6 | §4 Sample-selection: window 2015-01 → 2026-03 pinned, lag-window-loss accounting, expected N=134, N_MIN=75 floor, BANNED `restrict-to-≥2022` | YES |
| 7 | §5.1 Y construction: Section J specifically (Divisions 58–63), youth 14–28, FEX_C_2018, RAMA4D_R4, logit transform, fractional-response GLM justification, CIIU revision boundary handling, sensitivity Y_s1/Y_s2/Y_s3 pre-pinned | YES |
| 8 | §5.2 X construction: Banrep TRM end-of-month spot, lag panel k ∈ {6,9,12}, anti-fishing transparency on X re-use disclosed | YES |
| 9 | §5.3 Primary specification: OLS equation, composite β = β_6+β_9+β_12, linear-restriction variance c'Σc with c=(0,1,1,1)', multicollinearity acknowledgment | YES |
| 10 | §5.4 Lag-window justification: 6–12mo offshoring contracting-cycle horizon, Section-J inheritance | YES |
| 11 | §5.5 Escalation methodology: D-i quantile τ=0.90, D-ii GARCH(1,1) X, D-iii EVT POT all defined; pre-authorization-not-rescue framing | YES |
| 12 | §6 Methodology-break: empalme primary disposition, R1 alternative, BANNED restrict-≥2022, empalme residual-bias acknowledgment, Section-J cell-size fallbacks (i) / (ii) | YES |
| 13 | §7 Robustness: R1 (2021 dummy), R2 (Y narrow Section M), R3 (raw OLS), R4 (HAC SE) all defined; §7.1 AGREE / MIXED / DISAGREE classification | YES |
| 14 | §8 Verdict-decision tree: §8.1 mapping rules 1-4 + (a)-(e) deterministic; §8.2 synthetic-tuple walk 9 rows exhaustive; §8.3 next-stage routing | YES |
| 15 | §9 Anti-fishing invariants: 15 enumerated invariants covering threshold immutability, Y-construction immutability, sample-window immutability, lag-set immutability, HALT protocol, escalation-as-pre-authorization, sha256 governance, X re-use disclosures, Stage-1-only scope, a_s/a_l out-of-scope, off-chain Y mandate, free-tier mandate, code-agnostic discipline | YES |
| 16 | Stream-watchdog mitigation: chunked authoring ≤200 lines per Edit/Write call with wc -l verification between | YES |
| 17 | Sentinel `<to-be-pinned-after-recompute>` intact at frontmatter line 3 for orchestrator post-emission sha256 patching | YES |

---

**End of spec.** All 9 sections present plus §10 self-review; no "TBD" placeholders remaining; all thresholds pinned in §3 + §6 + §7 + §9 with concrete numerics; §8 verdict tree deterministic with synthetic-tuple walk in §8.2; §3.4 + §5.5 escalation suite pre-authorized with concrete disjunctive thresholds; §6 methodology-break disposition pre-pins primary + R1, BANS restrict-to-≥2022; §9 anti-fishing invariants explicit, Phase-A.0-aligned, Pair-D-aligned, and CORRECTIONS-η/θ/ι-compliant. Ready for orchestrator post-emission sha256 patching, plan emission, and 2-wave Reality Checker + Model QA Specialist verification.
