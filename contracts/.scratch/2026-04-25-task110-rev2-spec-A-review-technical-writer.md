# Technical Writer Review — Task 11.O Rev-2 Spec, Track A (Autonomous)

**Date:** 2026-04-25
**Reviewer:** Technical Writer agent (re-dispatch with corrected product framing)
**Subject:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (604 lines, uncommitted)
**Comparison precedents:**
- `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md`
- `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md`
**Product memo (corrected):** `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_abrigo_convex_instruments_inequality.md`
**Lens:** Standard TW (style + structure + citation discipline) + product-purpose alignment (CONVEX instruments / MACRO shocks / inequality lens).

---

## Verdict

**NEEDS-WORK** (non-blocking on standard TW dimensions; **blocking on product-purpose alignment**).

The spec is exceptionally well-structured on the standard TW axes (precedent-aligned heading hierarchy, code-agnostic body, anchors used uniformly, citation discipline observed in 4 of 4 major methodological choices). The standard TW dimensions would clear a PASS-with-non-blocking-advisories.

However, the **product-purpose alignment lens reveals two blocking gaps and three non-blocking gaps** that prevent reviewer confidence that the spec is aligned with Abrigo's actual product purpose (convex instruments hedging macro shocks viewed through the inequality lens). The spec frames itself as a *mean-effect identification* exercise without acknowledging that mean-β identification is necessary-but-insufficient for a convex-payoff product. A future revision (Rev-2.1) addressing the product-purpose gaps below would graduate this to PASS.

The corrected dispatch's blocking concern is real: §1.1's product-context paragraph mentions "progressive hedge for labor-income holders" but never names "convex" or "option-like," and §10/§11 never propose convex-payoff extensions to the resolution matrix. The mean-β framing is treated as the *complete* identification strategy when it should be flagged as the *first stage* of a multi-stage product-validity test.

---

## SECTION 1 — Standard TW Findings

### 1.1 Style consistency with project precedent — PASS

Compared to `2026-04-24-y3-inequality-differential-design.md` and `2026-04-24-carbon-basket-xd-design.md`:

| Dimension | Precedent style | Track A spec | Verdict |
|---|---|---|---|
| Heading hierarchy | `# Title` → `## N. Section` → `### N.M Sub` | Same | MATCH |
| Front-matter block | Date / Status / Trigger / Brainstorm trail | Date / Branch / Track / Predecessor commits / Skill / Author / Methodology authority | EXTENDED but consistent (richer because it is a Rev-2, not a brainstorm-converged design) |
| Section numbering | Monotonic (1, 2, 3, …) | Monotonic (0, 1, 2, …, 17) | MATCH |
| Inline tables for axis grids / parameter ledgers | Yes | Yes | MATCH |
| Code-block usage | Equations and identifiers only; no Python/SQL | Equations + identifiers only (`Y_asset_leg_t = …`, `Y₃_t = …`); no executable code | MATCH |
| Anchor preservation discipline | Byte-exact preservation rhetoric | Byte-exact preservation rhetoric (§5 table includes `MDES_FORMULATION_HASH` SHA) | MATCH (and stronger — Track A repeats the SHA inline) |

**Verdict:** Style consistency is excellent.

### 1.2 Code-agnostic body — PASS

No Python or SQL function bodies appear in the spec. References to functions (`required_power(n,k,mdes_sd)`, `load_onchain_y3_weekly(...)`) are cited *by signature only* in §13, never with bodies inlined. Equations appear in pseudo-mathematical code blocks, not Python.

This satisfies the user's NON-NEGOTIABLE memory `feedback_no_code_in_specs_or_plans`.

### 1.3 Heading hierarchy monotonic — PASS

Sections 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 are monotonic. Sub-section indices (1.1, 1.2, 1.3, 1.4; 2.1 → 2.7; 3.1 → 3.4; 4.1 → 4.4) are monotonic within each section.

One minor advisory: §10's enumeration uses `ε.1, ε.2, ε.3, ε.4, ε.5` (Greek epsilon) while §6 uses arabic `1–13`. The mixed numbering is intentional (epsilon = "future-revision," distinguished from gate-bearing rows) and is documented at §10 first paragraph. Acceptable but flag in errata for the first reader.

### 1.4 Cross-references resolve — PASS with one trivial advisory

Verified anchor resolutions:
- §1.2 references §10 ε.1 → resolves at §10 (line 456) ✓
- §3.4 references §6 T1 → resolves at §7 T1 (line 359). **MINOR:** §3.4 says "tested by §6 T1" but T1 is in §7. This is a 1-section drift; not a blocker but should be corrected in Rev-2.1 to "§7 T1."
- §4.4 references §10 ε.1 → resolves ✓
- §6 references `2026-04-25-y3-rev532-review-reality-checker.md` → resolves to a file in `contracts/.scratch/` (cited).
- §7 T7 references §6 row 6 → resolves ✓
- §10 ε.5 references "FX-vol product-read pivot path 3" → resolves to `project_fx_vol_econ_gate_verdict_and_product_read.md` per implication; advisory: cite the memory entry by name.

**Verdict:** All cross-references resolve except the §3.4 → §6/§7 drift, which is a typo-class issue.

### 1.5 Internal consistency on anchor literals — PASS (byte-exact verified across all citations)

Methodology literals appear in:
- §1 (line 26): `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`
- §5 row "Y₃ primary methodology literal" (line 283): same literal byte-exact
- §13 (line 506): same literal byte-exact
- §1 (line 26): `y3_v2_imf_only_sensitivity_3country_ke_unavailable`
- §5 (line 284): same literal byte-exact
- §13 (line 507): same literal byte-exact

`carbon_basket_user_volume_usd` appears in §1, §2.1, §2.2, §5, §6, §13, §15 — byte-exact in all 7 occurrences.

The N anchors 76 / 65 / 56 appear:
- §1 (76 obs)
- §5 MDES recompute table (76 / 65 / 56)
- §6 row 1 (76), row 3 (65), row 4 (56)
- §13 (76 joint, 56 joint)

All consistent. **PASS.**

`MDES_FORMULATION_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` appears in:
- §5 (line 281)
- §9 item 6 (line 444)

Both byte-exact. **PASS.**

### 1.6 Citation discipline (`feedback_notebook_citation_block`) — PASS on covered items

The 4-part citation block (reference / why used / relevance / connection-to-simulator) is observed in:
- §1.4 (Y₃ identity transform) — all 4 parts present ✓
- §4.2 (HAC + Student-t distributional assumption) — all 4 parts present ✓
- §4.4 (intervention_dummy substitution) — all 4 parts present ✓

**Citation discipline is observed on every methodological choice that gets a 4-part block** — this is excellent.

**Advisory (non-blocking):** §6 (the 13-row resolution matrix) introduces *13 design choices* but the row-by-row rationale is compressed into the table cells. The matrix is the spec's biggest pre-registration commitment yet does not get its own 4-part block. Recommendation for Rev-2.1: add a §6.5 "Citation block for the resolution matrix" with the four parts (Reference: Reiss-Wolak Phase 4 sensitivity-grid principle; Why used; Relevance to results; Connection to product). This is non-blocking because each row's verdict is documented, but a single overarching citation block would tighten the discipline.

**Standard TW Verdict on Section 1: PASS-with-non-blocking-advisories.**

---

## SECTION 2 — Product-Purpose Alignment Findings (CORRECTED FRAMING)

The corrected product memo states: **Abrigo offers convex (option-like) financial instruments hedging MACROECONOMIC shocks viewed through the INEQUALITY lens.** The shocks are MACRO; the inequality lens is in Y₃'s WC-CPI-weighted (60/25/15) construction. Convex payoffs require tail-risk / asymmetric-response evidence — mean-β identification is necessary-but-insufficient.

### 2.1 BLOCKING — Product purpose statement absent from the introduction

**Finding:** §1.1 contains a product-context paragraph that says:

> "The product thesis (`project_abrigo_inequality_hedge_thesis.md`) is that Abrigo offers a *progressive hedge for labor-income holders* — i.e., a derivative whose payoff is correlated with the differential between top-decile asset returns and bottom-quintile cost-of-living returns."

This describes the *outcome* (a derivative on the inequality differential) but does NOT name:
- That the product is **CONVEX** (option-like, capped-loss / levered-upside payoff)
- That the shocks driving the hedge are **MACROECONOMIC** (CPI/FOMC/oil/FX-intervention) — not microeconomic / household-level
- That the inequality lens enters specifically through the **WC-CPI 60/25/15 weighting** and is invisible without it

A reader unfamiliar with the corrected product memo cannot infer from the spec body that:
1. The product is convex (the word "convex," "option-like," "tail-risk," "asymmetric" never appears in 604 lines).
2. The macro shocks are explicitly the identifying variation source, not microeconomic shocks. (§4.3 says "what variation identifies β: week-to-week variation in X_d" — this is the *mean-effect* identification, not the *macro-shock* identification.)
3. The 60/25/15 weights are the inequality-lens marker. (§3.3 mentions "60/25/15 weighted CPI components" once, in a passing parenthetical, with no flag that this is the inequality-focus marker.)

**Required fix (blocking):** Insert a §0.5 or expand §1.1 to read approximately:

> "Abrigo offers **convex (option-like) financial instruments** — derivatives with capped-loss / levered-upside payoffs — that hedge **macroeconomic shocks** (CPI release surprises, FOMC decisions, oil-price moves, FX-intervention dates) **viewed through the inequality lens**. The inequality lens enters specifically through Y₃'s WC-CPI-weighted (60/25/15 food/energy-housing/transport-fuel) construction per `2026-04-24-y3-inequality-differential-design.md` §4 — these working-class-bundle weights distinguish Y₃ from an aggregate-CPI outcome variable. This Rev-2 spec tests whether on-chain Mento basket activity (X_d) correlates with the inequality-differential outcome (Y₃) at the *mean* level. Mean-β identification is the *first stage* of product validity; convex-payoff pricing additionally requires tail-risk / variance-amplification / quantile-shift evidence flagged for Rev-2.1+ extension at §10."

Without this paragraph, the spec reads as a vanilla econometric exercise on a constructed differential — not as a stage in a convex-instrument-pricing product validation.

### 2.2 BLOCKING — Mean-β framing without flagging it as insufficient for convex pricing

**Finding:** §4.1 specifies OLS+HAC(4) on Y₃ with a one-sided gate at T3b. §11 (failure scenarios) describes three outcomes — all framed as PASS / FAIL on the *mean coefficient*. There is **no acknowledgment anywhere in the spec** that:

- A statistically detectable mean-β (T3b PASS) is **necessary but not sufficient** for the convex-instrument product.
- Convex payoffs (caps, floors, asymmetric leverage) are priced from the **distribution** of Y₃ conditional on X_d shocks — not from the conditional mean.
- Even if T3b PASSES, the simulator (§12) cannot price convex payoffs from β̂ alone. It would need quantile regression or variance-conditional-on-X_d evidence.

The spec implicitly treats T3b PASS as "product painkiller framing supported" (§11 Scenario A) — but this is overclaim relative to the actual product. A T3b PASS supports a *linear-payoff* hedge (e.g., a forward on Y₃), not a convex payoff (an option on Y₃).

**Required fix (blocking):** Add a §11.A or §12.A subsection that explicitly says:

> "**Convex-payoff insufficiency caveat (per `project_abrigo_convex_instruments_inequality.md`).** A T3b PASS at the mean-β level is *necessary* for convex-instrument pricing but *not sufficient*. Convex payoffs require additional evidence on: (a) tail-risk asymmetry (lower-tail Y₃ shifts conditional on large X_d shocks); (b) variance amplification (Var[Y₃ | X_d high] vs Var[Y₃ | X_d low] — partly tested at T2 but not at the convex-pricing-relevant tail); (c) quantile-regression β̂(τ) at τ ∈ {0.10, 0.25, 0.75, 0.90} to detect asymmetric impact across the Y₃ distribution. This Rev-2 spec deliberately scopes to mean-β identification as the *first stage* of product validation; a Rev-2.1 extension adding quantile / variance-regression rows to the resolution matrix is required for downstream simulator calibration of convex payoffs. The simulator's β̂_X_d-anchored hedge-leg coefficient at §12 is therefore valid only for *linear-payoff* hedge instruments (forwards, swaps); convex payoffs (puts, calls, caps, floors) require Rev-2.1+ evidence."

Without this caveat, a future engineer reading the spec might wire β̂ into a convex-payoff pricer and miscalibrate the product.

### 2.3 NON-BLOCKING ADVISORY — FAIL sensitivity rows lack product-perspective explanations

**Finding:** §6 rows 3 (65-week LOCF-tail-excluded) and 4 (56-week IMF-IFS-only) are pre-registered FAIL on N_MIN. The spec correctly documents that they MUST be reported regardless. However, the spec does **not explain what the FAILs mean from the product-perspective**:

- If the 65-week sensitivity FAILS, what does it mean for the product? (Answer per the corrected product memo: the LOCF-extended tail observations are necessary for the panel; pruning them collapses panel power below the convex-pricing threshold.)
- If the 56-week IMF-IFS-only sensitivity FAILS, what does it mean? (Answer: source upgrades for CO and BR are necessary infrastructure investments for product viability; absent them, the product cannot be calibrated even at the mean-β level.)

**Recommended fix (non-blocking):** In §6 below the FAIL-row table, add a one-paragraph "Product-perspective interpretation of the pre-registered FAILs":

> "From the Abrigo product perspective: Row 3's pre-registered FAIL means the LOCF-tail-extended observations (weeks 66–76 of the panel) are *load-bearing* for the panel's power. Pruning them is not a viable path forward; the LOCF policy stays. Row 4's pre-registered FAIL means CO→Banrep and BR→IBGE source upgrades are *necessary infrastructure* for product viability — reverting either drops the panel below 75 weeks and below 0.80 power. These FAILs are not bugs; they are evidence that the source-mix decisions made at Task 11.N.2d are load-bearing for the product."

This satisfies the dispatch's gap-3 concern.

### 2.4 NON-BLOCKING ADVISORY — Roadmap section pointing to convex-payoff extensions absent

**Finding:** §10 "Sensitivity grid (future-revision options)" lists ε.1 (panel decomposition), ε.2 (bond-anchored Y₃), ε.3 (population-weighted aggregation), ε.4 (crypto-vol Y candidate), ε.5 (intraday event-window). All five are *mean-effect* extensions of the same OLS+HAC framework. **None of them point to convex-payoff-relevant extensions:**

- Quantile regression (β̂(τ) for τ ∈ {0.10, 0.25, 0.75, 0.90}) — partially addresses convex-payoff tail-risk evidence
- GARCH-X variance equation with X_d in the conditional-variance specification — addresses variance amplification for convex-payoff variance scaling
- Conditional-quantile / lower-tail-stabilization regression on X_d — directly addresses the convex-instrument tail-risk component
- Option-implied-vol surface mapping (if/when an Abrigo prototype is live) — final-stage product-pricing test

**Recommended fix (non-blocking):** Add §10.6 (or restructure §10 to add a "ζ" group for convex-payoff future revisions):

> "**ζ-group: Convex-payoff future-revision extensions (per `project_abrigo_convex_instruments_inequality.md`).** Mean-β identification at §4.1 is the *first stage* of product validity. Rev-2.1+ revisions are reserved for:
> - **ζ.1 Quantile regression β̂(τ)** at τ ∈ {0.10, 0.25, 0.75, 0.90} to detect asymmetric mean-shift across the Y₃ distribution.
> - **ζ.2 GARCH-X conditional variance.** Estimate Var[Y₃ | X_d] by including X_d in the GARCH(1,1) variance equation per FX-vol notebook §3.4 prior-art.
> - **ζ.3 Lower-tail conditional regression.** Specifically test whether large positive X_d shocks correspond to lower-tail compression of Y₃ (the convex put-floor payoff scenario).
> - **ζ.4 Option-implied-vol calibration.** Once an Abrigo prototype is live, calibrate option-implied vol surface to historical Y₃ distribution conditional on X_d.
>
> These extensions are deferred from Rev-2 because they are not necessary for mean-β identification; they ARE necessary for convex-payoff product calibration."

This addresses the dispatch's gap-4.

### 2.5 NON-BLOCKING ADVISORY — Inequality-lens documentation is muted

**Finding:** The 60/25/15 WC-CPI weighting is the spec's primary inequality-lens marker. It appears in the spec only at:
- §3.3 (line 165): "60/25/15 weighted CPI components" — passing parenthetical
- That's it. Seven hundred words in §1 and §2 about Y₃ never name "60/25/15" or "WC-CPI weighting" as the inequality-lens marker.

This is a clarity gap because:
1. A reader who has not opened the Y₃ design doc cannot tell that Y₃ is *not* a generic aggregate inequality measure.
2. The substitution of `intervention_dummy` for `cpi_surprise_ar1` in §4.4 is justified ("Y₃ already contains Δlog(WC_CPI)") but never names *which* WC-CPI weighting — which is the load-bearing identification primitive.

**Recommended fix (non-blocking):** In §1.3 (Outcome variable), add an inline reference:

> "Where `Δ_country_t = R_equity_country_t + Δlog(WC_CPI_country_t)` (sign convention: rises when inequality widens via either rich-side gains OR working-class cost-of-living squeeze). **The WC-CPI is constructed with pre-registered budget-share weights (60% food / 25% energy+housing-utilities / 15% transport-fuel) per `2026-04-24-y3-inequality-differential-design.md` §4 — these working-class-bundle weights are the inequality-lens marker that distinguishes Y₃ from an aggregate-CPI outcome variable.**"

This single sentence addresses the dispatch's gap-5.

### 2.6 NON-BLOCKING ADVISORY — Macro-shock identification clarity is implicit, not explicit

**Finding:** The corrected product memo emphasizes that **macro shocks** (not microeconomic) are the identification source. The spec's controls in §4.1 (VIX_avg, oil_return, US_CPI_surprise, BanRep_rate_surprise, Fed_funds_weekly, intervention_dummy) ARE all macro shocks — but the spec never names them as such.

§7 T1 (exogeneity test) speaks of "X_d's residual variation" — which is correct — but never frames identification as "the **macro shocks** drive the identifying variation; X_d's residual after macro-shock partialling is what β̂ identifies."

**Recommended fix (non-blocking):** Add a sentence to §4.3 right after the identification-strategy paragraph:

> "**Macro-shock identification framing (per `project_abrigo_convex_instruments_inequality.md`).** The identifying variation in this regression is the residual variation in X_d *after partialling out macroeconomic shocks*: VIX (global risk), oil (commodity), US CPI surprise (US monetary), BanRep rate surprise (Colombian monetary), Fed funds (global rate), and intervention dummy (Colombian FX policy). Each control is a macro-level shock; none is microeconomic / household-level. β̂ identifies the marginal association between X_d and Y₃ that survives this macro-shock partial — which is the relevant-for-product quantity because Abrigo's convex instruments are designed to hedge macro shocks specifically (not micro shocks)."

This addresses the dispatch's gap-6.

---

## SECTION 3 — Summary Findings Table

| Dimension | Verdict | Action required |
|---|---|---|
| Style consistency with project precedent | PASS | None |
| Code-agnostic body | PASS | None |
| Heading hierarchy monotonic | PASS | None |
| Cross-references resolve | PASS-with-trivial-advisory | Fix §3.4's "§6 T1" → "§7 T1" typo in Rev-2.1 |
| Internal consistency on anchor literals (76/65/56, methodology literals, MDES hash) | PASS | None |
| Citation discipline (4-part block) | PASS-with-non-blocking-advisory | Add §6.5 4-part block for the 13-row resolution matrix in Rev-2.1 |
| **Product-purpose alignment §2.1 (convex instruments / macro shocks named in intro)** | **BLOCKING** | **Insert §0.5 or expand §1.1 to name "convex," "option-like," "macroeconomic," "WC-CPI 60/25/15 inequality lens"** |
| **Product-purpose alignment §2.2 (mean-β framed as insufficient for convex pricing)** | **BLOCKING** | **Add §11.A or §12.A "Convex-payoff insufficiency caveat" tying β̂_X_d to linear-payoff hedges only and flagging quantile/variance evidence as Rev-2.1+ requirement** |
| Product-purpose alignment §2.3 (FAIL sensitivities have product-perspective explanations) | NON-BLOCKING | Add product-perspective paragraph below §6 FAIL-row table |
| Product-purpose alignment §2.4 (roadmap to convex-payoff extensions) | NON-BLOCKING | Add §10.6 ζ-group for convex-payoff future revisions (quantile, GARCH-X, lower-tail, option-implied-vol) |
| Product-purpose alignment §2.5 (60/25/15 inequality-lens documented) | NON-BLOCKING | Add inline WC-CPI 60/25/15 reference at §1.3 |
| Product-purpose alignment §2.6 (macro-shock identification explicitly named) | NON-BLOCKING | Add macro-shock framing sentence at §4.3 |

---

## SECTION 4 — Final Verdict

**NEEDS-WORK** at Rev-2 due to the two blocking product-purpose findings (§2.1 and §2.2). The standard TW dimensions are excellent and would clear PASS-with-non-blocking-advisories on their own; the blocking concerns are entirely on the product-purpose alignment lens.

**Rev-2.1 acceptance criteria (proposed):**
1. Insert convex-instrument / macro-shock / inequality-lens product-purpose paragraph at §0.5 or expanded §1.1 (resolves §2.1).
2. Insert "Convex-payoff insufficiency caveat" at §11.A or §12.A flagging mean-β as first-stage-only and naming quantile / variance / lower-tail evidence as Rev-2.1+ requirements (resolves §2.2).
3. Address the four non-blocking advisories (§2.3, §2.4, §2.5, §2.6) — recommended but not gating.
4. Fix the §3.4 → §7 typo (trivial).
5. Optionally add the §6.5 resolution-matrix 4-part citation block (recommended for citation-discipline tightening).

**Track-A vs Track-B head-to-head note:** The spec's §16 ("Track-A author's pre-registered analytical position vs default reasonable") is exemplary in transparency — it surfaces five non-default choices for adversarial scrutiny. Track B's spec, when reviewed, should be checked for the same transparency. If Track A and Track B converge on most choices except one or two, that convergence is itself useful Reviewer evidence for plan-fold.

**Comparison context (corrected product framing):** The Track A spec is a high-quality mean-effect econometric exercise that would clear a peer-review bar at any competent ECTRIC journal. Its gap is not analytical rigor — it's product-context completeness. The corrected dispatch's framing is correct: mean-β alone is insufficient for a convex-instrument product, and the spec must say so explicitly. With the two blocking fixes applied, this graduates to PASS.

---

## Files referenced

- **Spec under review:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`
- **Product memo (corrected):** `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_abrigo_convex_instruments_inequality.md`
- **Style precedent 1:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md`
- **Style precedent 2:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md`
- **Citation discipline reference:** `feedback_notebook_citation_block` in user memory
- **This review:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-review-technical-writer.md`

**End of Technical Writer review (re-dispatch with corrected product framing).**
