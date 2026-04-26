# NB1 Three-Way Review — Model QA (Econometric Correctness)

**Reviewer:** Model QA Specialist
**Review date:** 2026-04-18
**Artifact under review:** `contracts/notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb` (118 cells, 9 336 lines JSON)
**Ancillary artifacts:** `scripts/cleaning.py` (230 lines, frozen Decisions #1-#12), `references.bib` (35 entries, 437 lines), Phase 1 findings digest (2026-04-18), NB3 pre-registration (2026-04-18), BanRep methodology research note (2026-04-18), spec Rev 4, implementation plan.
**Scope:** econometric-integrity review only. Code style, prose quality, and operational concerns are explicitly out of scope for this prong.

---

## 1. Executive summary

**Verdict: CONDITIONAL PASS.** NB1 is econometrically defensible and the Phase 1 pipeline is materially sound. All five of my live spot-checks (Decisions #1, #2, #4, #7, #8, #9, plus §5 correlation matrix and §6 stationarity diagnostic) reconcile the notebook's claimed numerics against the live DuckDB warehouse at four significant figures, which is rare and reassuring. Specifically I re-derived live: Decision #1 n_weeks=947; Decision #2 RV^(1/3) mean=0.0585, std=0.0229, skew=1.1393, kurt_exc=2.7727; Decision #4 Colombian CPI 205 neg / 13 pos / 729 zero, mean_nonzero=−0.6878; Decision #6 banrep n_events=88; Decision #7 VIX mean=19.90, std=8.75, skew=+2.44, kurt_exc=+8.51, max=74.62; Decision #8 oil mean=−0.0004, std=0.0602, kurt_exc=+17.7917; Decision #9 intervention regime rates 71.0% / 3.8% / 63.5% / 22.6%, data-freshness gap=73 weeks; §5 max |Pearson|=−0.1416 (vix×oil); §6 ADF smallest rejection at banrep p=0.0143 and KPSS 5-of-7 rejections at clipped values. Every numeric in the decision cards I spot-checked round-trips exactly. The twelve Decisions are ledger-addressable, the anti-fishing seals are binding, and the honest footnotes on regime-anchoring and attenuation bias are present where they should be.

The three concerns that prevent an unqualified pass are:

1. **S7 pre-registration propagation gap (HIGH severity).** Decision #9's card (cell 90) explicitly declares S7 ("drop 2024-10-07+ subsample (73 weeks)") as pre-registered and states it "must be propagated" to `2026-04-18-nb3-sensitivity-preregistration.md`. The propagation has not happened: a content-grep of the pre-registration doc returns zero matches for `S7`, `2024-10-07`, `2024-10`, or `freshness`. The Decision #9 markdown is the only on-disk record of S7. Under the pre-registration's own §5 Amendment Protocol, the pre-registration binds at disk-mtime; once NB2 runs, S7 is no longer addable. S7 is therefore in a pre-registration limbo and will be ruled out by its own governing document the moment NB2 estimates β̂_CPI. This blocks Phase 2 and must be fixed before NB2 estimation is dispatched.
2. **references.bib freshness gap (MEDIUM severity).** Cell 75 Decision #6 card explicitly names `Anzoátegui-Zapata & Galvis 2019` and `Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022` as the grounding canon for the BanRep event-study methodology, but grep confirms both are still absent from `references.bib` (35 entries, not the 37 the digest expects). The Decision #6 citation chain rests on two references the bibliography does not supply. This is a documented Task 15 cleanup item but Phase 2 should not start with the citation gap unclosed, because Phase 2's NB2 reconciliation discussion will cite the same literature.
3. **KPSS-ADF disagreement in Decision #11 is presented honestly but the interpretation is underspecified (MEDIUM severity).** Decision #11 (cells 102, 105) adopts an ADF-primary verdict on 7 series where 5 of 7 fail KPSS (cpi_surprise_ar1, us_cpi_surprise, banrep_rate_surprise, vix_avg, intervention_dummy). The notebook attributes KPSS rejection to over-rejection under heteroskedasticity and regime shifts. That is a defensible move, but the attribution should be quantified (e.g., via a wild-bootstrap KPSS on the same sample) rather than asserted by canon citation. For a T3b gate whose power depends on clean HAC asymptotics, leaving 5 of 7 series at KPSS stat > 0.05 with prose-only resolution is a thin reed to lean on.

Subject to remediation of (1) and (2) before NB2 is dispatched, and documentation of the wild-bootstrap plan for (3), Phase 2 is clear to begin.

---

## 2. Decision-by-decision audit

Each entry below assesses the decision against four criteria: (a) citation grounds the choice in literature; (b) locked value is consistent with canonical spec; (c) anti-fishing binding is pre-committed; (d) declared sensitivities are pre-registered (not ad-hoc). Good = pass, Concerning = flag.

### Decision #1 — Sample window lock (cell 18)

- **What's good:** The window is pinned by a structural constraint (IBR unavailable pre-2008) rather than a judgment call. Justification text explicitly re-derives the binding series live in cell 17 rather than hard-coding. Andrews (1991) q/T = 4.2×10⁻³ calculation at T=947 is algebraically correct and empirically honest. SSDE 2024 + Ankel-Peters 2024 citations ground the pre-commitment discipline.
- **What's concerning:** Nothing material. The "alphabetically first among ties" tiebreaker (`dane_ipc_monthly`) for the upper edge is arbitrary but deterministic and disclosed.
- **Verdict:** PASS.

### Decision #2 — LHS transform lock: RV^(1/3) (cell 33)

- **What's good:** Wilson-Hilferty (1931) citation is the correct parametric grounding — cube-root of χ² is approximately Gaussian, so for weekly RV (a sum-of-squares object approximately χ²-distributed conditional on variance) the cube-root transform is theory-motivated, not data-mined. The notebook honestly documents that log(RV) wins empirically (|skew|=0.29, kurt_exc=0.64 versus RV^(1/3) |skew|=1.14, kurt_exc=2.77 — **spot-checked live, matches exactly**) and still binds the pre-committed choice. This is textbook anti-fishing discipline.
- **What's concerning:** The Simonsohn (2020) citation for anti-fishing is correctly applied. One quibble: the cell 30 interpretation states the RV^(1/3) residuals are "within the Gaussian-working-model tolerance OLS inference accepts" — the kurt_exc of 2.77 is sizeable. OLS point estimation is consistent regardless of residual normality, but HAC-adjusted standard errors assume finite fourth moments and slow decay; kurt_exc=2.77 is still finite but pushes the sample toward the regime where bootstrap-HAC reconciliation becomes important. That is exactly what A12 covers, so the path is consistent, but the prose claim could be tighter.
- **Verdict:** PASS with minor prose flag.

### Decision #3 — Frequency lock: weekly (cell 36, not explicitly shown but indexed in ledger)

- **What's good:** Weekly primary + daily companion (for A1 sensitivity) is the standard macro-finance split. Consistent with ABDV 2003 convention.
- **What's concerning:** Nothing material.
- **Verdict:** PASS.

### Decision #4 — Colombian CPI surprise specification (cell 45)

- **What's good:** The grounding chain (ABDV 2003 → Balduzzi-Elton-Green 2001 → Simonsohn 2020) is exactly the right canon for AR(1)-expanding-window surprise construction. The §4a Trio 2 audit (cell 41) rules out three alternative explanations for the 94%-negative asymmetry with live DB queries: alignment_rate=1.000, no imputation column on the realized side, 643-month pre-sample warmup. Root-cause is accepted as regime mismatch. I **spot-checked live** the pre-sample vs in-sample CPI MoM means: 1.2308 vs 0.4053 (roughly 3×), matching the digest claim. The 205 neg / 13 pos / 218 nonzero / 729 zero / 947 total breakdown is **spot-checked live and matches exactly**. Mean_nonzero = −0.6878, skew_nonzero = 0.9010, kurt_exc_nonzero = 1.1148 — all within the card's reported precision. Attenuation bias is disclosed on the card (`attenuation_risk: yes — classical measurement-error on surprise`), so downstream readers cannot miss the caveat.
- **What's concerning:** The sensitivity_alt_window cell lists `rolling 60-month AR(1)` but the card's sensitivity list omits A9 sign-asymmetric (it is in the pre-registration doc as S1's row neighbor). The A9 asymmetric-response cell is in the card (`sensitivity_alt_primary: |surprise| (A9)`). Consistent. No gap.
- **Verdict:** PASS.

### Decision #5 — US CPI warmup lock (cell 54)

- **What's good:** Same ABDV 2003 operator, symmetric sign balance (110 pos / 107 neg) vs Colombian's asymmetric 13/205 — this is the critical **falsifier** for the "regime-anchoring" hypothesis. Applying the same operator to unbiased data (US) returns unbiased surprises; applying it to hyperinflation-anchored data (Colombia) returns systematically negative surprises. The symmetric US result is the smoking gun that Colombian asymmetry is not a methodological bug. The 8.51 excess kurtosis on the US side is attributed live to 4 real macro events (Lehman 2008, oil shock 2008-07, COVID 2020-04, inflation deceleration 2022-07). Pre-committed A12 HAC bandwidth sensitivity covers the fat-tail concern.
- **What's concerning:** The 12-month warmup is spec-committed, not independently audited. A subagent could counter that 24-month warmup might yield different surprise magnitudes. But the "A12 HAC(12) bandwidth sensitivity" listed on the card is a fat-tail sensitivity, not a warmup sensitivity — calling A12 the "sensitivity_alt" here conflates two orthogonal robustness checks. The warmup-length sensitivity is not pre-registered anywhere I can find. This is a minor gap, not a block.
- **Verdict:** PASS with minor flag on warmup-length alt.

### Decision #6 — BanRep rate surprise (cell 75)

- **What's good:** Methodological heterogeneity across regressors (AR(1) for CPI, event-study for policy rate) is correctly motivated by the step-function property of policy rates. Cell 73 cites ABDV 2003 Table 4 as precedent for mixed-methodology surprise construction. The 88-event spot-check matches live. Sign balance 42 pos / 46 neg (**symmetric**) contrasts Colombian CPI's 13/205 asymmetry and confirms the event-study operator is appropriate for this series. Top-5 outliers attributed to real decisions. Correlation with cpi_surprise_ar1 = +0.074 (**spot-checked live = 0.0739**) — no collinearity.
- **What's concerning:** **Two citations to named Colombian-literature references (Anzoátegui-Zapata & Galvis 2019, Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022) are prose-only because the bib entries do not yet exist.** This is explicitly flagged on the card (`references_bib_gap` field) and in the digest as a Task 15 cleanup item. As a scientific-integrity matter, a Decision card citing references its bibliography does not index is a material weakness. Fixable in a single commit.
- **Verdict:** CONDITIONAL PASS — contingent on bib entries landing before Task 15 closes.

### Decision #7 — VIX aggregation: weekly mean (cell 66)

- **What's good:** ABDL 2001 + Ang-Hodrick-Xing-Zhang 2006 citations are the correct canon for weekly-aggregation of daily volatility measures. Audit is clean: Monday alignment, no lookahead, 4.85 avg daily obs/week. Spot-checked live: mean=19.90, std=8.75, skew=+2.44, kurt_exc=+8.51, max=74.62 — **exact match** to card. The rejection of `vix_friday_close` is spec-referenced, not data-mined.
- **What's concerning:** Nothing material.
- **Verdict:** PASS.

### Decision #8 — oil_return aggregation (cell 81)

- **What's good:** ABDE 2001 standard aggregation, honest 2020-04-20 negative WTI handling via `value > 0` filter. The card enumerates three rejected alternatives (weekly-mean, Friday-close, arithmetic return) with explicit reasons. Spot-checked live: mean=−0.0004, std=0.0602, kurt_exc=+17.79 — **exact match** to card. The small-denominator artifact at 2020-03-30 is honestly footnoted.
- **What's concerning:** kurt_exc=17.79 is the fattest-tailed regressor in the panel and the card does not pre-register a specific oil-focused sensitivity (the sensitivity_alt field states "none pre-registered specific to oil; A11 leave-one-out covers drop-oil case"). For a weekly log-return on WTI spanning 2008 GFC + 2014-2016 price collapse + 2020 negative-settlement + 2022 Russia-Ukraine shock, 17.79 is still a finite fourth moment but is exactly the regime where HAC(4) bandwidth sensitivity becomes material. A12 is the right robustness check; it is pre-registered.
- **Verdict:** PASS.

### Decision #9 — intervention regressor + data-freshness (cell 90)

- **What's good:** The card honestly surfaces the 73-week data-freshness gap (banrep_intervention_daily ends 2024-10-04; **live-verified — max_date=2024-10-04, gap=73 weeks, 8% of sample**), quantifies the regime heterogeneity (2008-2014: 71%, 2015-2019: 3.8%, 2020 COVID: 63.5%, 2024: 22.6% — **all four regime percentages spot-checked live and match exactly**), and declares a named new sensitivity (S7) to address the gap. The literature canon (Fuentes-Pincheira-Julio-Rincón 2014 BIS WP 462, Rincón-Torres 2021) is in `references.bib`. Correlation with cpi_surprise_ar1 = −0.0998 (**spot-checked live**) confirms low collinearity. Active fraction = 316/947 = 33.4% — card claims 33%, matches.
- **What's concerning:** **The S7 pre-registration is not propagated to `2026-04-18-nb3-sensitivity-preregistration.md`.** Grep on S7, 2024-10-07, 2024-10, freshness returns zero hits in the pre-registration doc. The Decision #9 card (cell 90 last paragraph) **explicitly states**: "S7 pre-registration amends `contracts/.scratch/2026-04-18-nb3-sensitivity-preregistration.md` and must be propagated there before Task 13 freezes the NB3 spec." This has not happened. Under the pre-registration's own §5 Amendment Protocol, the disk-mtime of the pre-registration file is the pre-commitment event; once NB2 runs, S7 cannot be retroactively added. The decision card's declaration of S7 is insufficient — the pre-registration doc is the governing artifact under the pre-registration's own interpretation rules.
- **Verdict:** **CONDITIONAL PASS — S7 propagation is the top critical issue (see §6, issue 1).**

### Decision #10 — collinearity policy (cell 96)

- **What's good:** Belsley-Kuh-Welsch 1980 canon correctly applied with intercept in the design matrix (common applied-work error avoided). Max VIF = 1.0391 — far below BKW 5/10 thresholds. Max pairwise Pearson = −0.142 (**spot-checked live = −0.1416**) — well below 0.7 caution. Decision cleanly "no adjustment required."
- **What's concerning:** Nothing.
- **Verdict:** PASS.

### Decision #11 — stationarity policy: levels (cell 105)

- **What's good:** ADF + KPSS dual diagnostic is textbook. Pre-committed treatment (ADF governs, use levels). ELS 1996 + KPSS 1992 + Campbell-Lo-MacKinlay 1997 + Hamilton 1994 canon is correct. **Live-verified ADF stats:** rv_cuberoot −3.60 (p=0.0057), cpi_surprise_ar1 −4.74 (p=0.0001), us_cpi_surprise −10.28 (p=0.0000), banrep_rate_surprise −3.31 (p=0.0143), vix_avg −5.55 (p=0.0000), oil_return −9.77 (p=0.0000), intervention_dummy −3.50 (p=0.0080). Smallest rejection = banrep at p=0.0143, exactly as claimed in card.
- **What's concerning:** Live-verified KPSS p-values: rv_cuberoot 0.0978, cpi_surprise_ar1 0.0100 (clipped), us_cpi_surprise 0.0380, banrep_rate_surprise 0.0428, vix_avg 0.0134, oil_return 0.1000 (clipped), intervention_dummy 0.0100 (clipped). **5 of 7 series reject KPSS stationarity.** The prose attribution to "heteroskedasticity + regime shifts" is econometrically defensible (KPSS is known to over-reject under variance breaks per Zivot-Andrews 1992 literature) but is asserted, not quantified. A wild-bootstrap KPSS on the same series would empirically settle whether KPSS rejection is heteroskedasticity-driven versus genuine unit-root-or-near-unit-root. That check is not present. For surprise series (cpi_surprise_ar1, us_cpi_surprise, banrep_rate_surprise) theory predicts stationarity (stochastic mean-zero construction) so ADF rejection is the theory-backed verdict; for vix_avg and intervention_dummy the KPSS rejection at p=0.01 is a genuine near-unit-root concern worth acknowledging more forcefully.
- **Verdict:** PASS with prose/robustness flag (see §7 minor issue).

### Decision #12 — merge policy: listwise complete-case (cell 114)

- **What's good:** Conrad-Schoelkopf-Tushteva 2025 canon. Trivial to satisfy on current data (zero nulls, n=947 across all three candidate policies). Pre-commitment is prospective (binds future data refreshes). S7 subsample interaction correctly identified as orthogonal (policy-based regime exclusion, not a missingness event).
- **What's concerning:** Cell 108 Trio 1 interpretation paragraph states "S7-sensitivity consideration (per Decision #9): the S7 subsample drops all weeks on or after 2024-10-01 ... n = 874". But Decision #9's card (cell 90) specifies the threshold as `week_start >= 2024-10-07`. These dates differ (2024-10-01 vs 2024-10-07) — and both references are in the same notebook. Pick one. This is a minor consistency flag, not a block, but should be fixed in Task 15.
- **Verdict:** PASS with minor prose flag.

---

## 2b. Deep-dive on the two defensibility puzzles

Two of the twelve Decisions warrant substantial expansion beyond the short entries above because they carry the bulk of the identifying risk.

### 2b.1 Decision #4 — the Colombian CPI asymmetry

The 205 negative / 13 positive / 218 nonzero breakdown on `cpi_surprise_ar1` is the single most unusual finding in NB1 and is the principal risk to T3b. The notebook's §4a Trio 2 audit chain (cell 41) ruled out three alternative explanations via live DuckDB queries:

1. **Release-date alignment bug.** If the weekly-panel mapped DANE releases to the wrong ISO weeks, the AR(1) forecaster could be systematically over- or under-counting recent realizations. Cell 41's live-recomputed `alignment_rate = 1.000` (217 of 217 DANE IPC release dates map 1-to-1 to non-zero weeks in the panel — I did not re-verify this specific computation but the `n_nonzero = 218` rate is consistent with 12-month-per-year-plus-one-leap releases). Ruled out.
2. **Imputation contamination.** If realized CPI values were partly vendor-imputed and the AR(1) forecaster were conditioning on a mix of real and imputed history, the forecast bias could be carrying imputation artifacts. Cell 41 verifies `dane_ipc_monthly` has no `is_imputed` column — every row is an official DANE release. Ruled out.
3. **Warm-up inadequacy.** If the AR(1) coefficient estimator had not converged by the time the 2008-01 release emitted its first forecast, the early-sample forecasts could be noise-inflated. 643 pre-sample months of conditioning data (1954-2007) vs the 12-month ABDV 2003 default warmup threshold. Ruled out.

The residual explanation is **regime anchoring**: the expanding-window AR(1) forecaster conditions its intercept on the full 1954-present history, which includes the 1954-2007 high-inflation period (mean IPC MoM = 1.23% per my live spot-check) versus the in-sample 2008-2026 modern-regime mean (0.41%). The AR(1) mean-reversion draws the forecast toward 1.23% while realized values drift around 0.41%, so realized-minus-forecast is systematically negative. This is a genuine design property of the pre-committed specification, not a pipeline bug.

**Attenuation-bias econometric implication.** Classical errors-in-variables theory: if the true market-expected CPI is closer to the modern-regime mean than the AR(1) forecast, then the constructed surprise regressor equals the true surprise plus a systematic offset (−0.69 on nonzero events, per spot-check). The systematic offset is a deterministic shift, not classical Gaussian measurement error, so the attenuation is not the textbook attenuation-toward-zero of Wooldridge §9.4 — it is a mean-shift bias that interacts with the intercept. For the slope coefficient β̂_CPI, the offset affects attenuation if and only if the true surprise innovation and the offset are correlated, which they are here (corr(cpi_surprise_ar1, CPI_level) = +0.37 per digest §4a). The bias is therefore partly attenuation, partly intercept-shift. The pre-registered S6 (de-meaned surprise) will quantify the attenuation component empirically by running Column-6 with the in-sample mean subtracted.

**What I did not audit that would strengthen Decision #4.** The digest §4a states `cpi_surprise_ar1` correlation with CPI level = +0.37. I did not spot-check this. It is the canonical evidence that the asymmetry is regime-anchoring rather than random: a null correlation would be weak evidence for the regime story. If a three-way reviewer or Phase 2 author wants to re-verify this for peace of mind, the query is one line of SQL. The finding is consistent with the regime-mean ratio (3×), so I have no reason to doubt it.

### 2b.2 Decision #6 — the BanRep event-study methodology

The digest summarizes Decision #6 as "event-study daily ΔIBR at Junta decision dates, weekly sign-preserving sum, methodologically distinct from AR(1) because policy rate is step-function." This is correct but understates what is at stake.

**Why the methodological heterogeneity is defensible.** An AR(1) expanding-window forecaster applied to a step-function series would produce nearly zero forecast errors everywhere except at meeting dates, plus a small systematic non-zero smoothing term that reflects the AR(1)'s attempt to extrapolate across meetings. The resulting "surprise" series would be mechanically small-in-magnitude most weeks and large only at meetings, but with a spurious low-magnitude non-zero component in between. Event-study construction at the meeting date yields exactly-zero surprises off-meeting and full-magnitude surprises on-meeting, which is the correct identification for the announcement-response channel the Column-6 regression is meant to isolate.

**ABDV 2003 Table 4 precedent.** ABDV 2003 (the canonical citation throughout §4) actually does mix methodologies in its empirical work — AR(1) on continuously-released macro indicators (CPI, PPI, employment) and event-study on policy-rate announcements. This is explicitly noted in cell 73's "Why used" subsection: "ABDV 2003 Table 4 specifically mixes AR(1)-expanding surprises on announcement-release series with event-study surprises on rate paths, establishing the methodological heterogeneity across regressors as textbook rather than deviant." This is the correct precedent and correctly cited.

**What is not in references.bib (but should be).** The §4c Trio 3 card (cell 75) explicitly names the Colombian-literature canon that directly motivated the event-study choice: Anzoátegui-Zapata & Galvis (2019, *Cuadernos de Economía* 38(77)) and Uribe-Gil & Galvis-Ciro (2022, BIS WP 1022). Both apply the event-study construction to ΔIBR at Junta Directiva meeting dates specifically for Colombia. Both are prose-cited, neither is in the bib. The separate research note `2026-04-18-banrep-rate-surprise-methodology-research.md` also grounds these references. The gap is purely operational — add the two bib entries and update the test.

**Cross-validation of the event-study choice.** The 88-event count in the Decision #1 window maps 1:1 to the 89 `policy_rate_decision` rows in `banrep_meeting_calendar` (the digest notes 234 total rows = 89 decisions + 145 hold-inferred, with 88 of the 89 decisions falling within the 2008-2026 window). The single unmapped decision is the 2008-01 meeting, which sits at the sample lower edge and contributes no weekly observation under ISO week-start alignment. This is a clean construction, and the sign-balance symmetry (42 pos / 46 neg, contrast Colombian CPI's 13 / 205) is strong evidence that the operator is un-anchored and correctly calibrated.

---

## 3. Econometric coherence assessment

The Column-6 regressor set — {cpi_surprise_ar1, us_cpi_surprise, banrep_rate_surprise, vix_avg, oil_return, intervention_dummy} — is sound for identifying a Colombian CPI-surprise effect on COP/USD realized volatility under standard macro-to-FX transmission theory. The inclusion logic:

- `us_cpi_surprise` controls for dollar-leg inflation variation (the other side of the COP/USD pair).
- `banrep_rate_surprise` controls for the Colombian monetary-policy response channel that co-moves with CPI surprises.
- `vix_avg` controls for global-risk aggregate that would otherwise load onto the Colombian regressor via flight-to-quality channels.
- `oil_return` controls for the commodity-channel Colombia is textbook-exposed to (net oil exporter, oil in COP terms is a mechanical COP driver).
- `intervention_dummy` controls for BanRep FX intervention, which is policy-contingent on COP/USD vol and creates simultaneity concerns if omitted.

What is **missing** from Column-6 — and worth naming explicitly because the notebook does not dwell on it — is any fiscal or commodity-terms-of-trade control beyond oil. Colombia exports coffee and coal alongside oil; to the extent coffee and coal shocks are orthogonal to oil, they are absorbed into the residual. The omission is consistent with the primary-volatility-on-CPI-surprise frame (a CPI-surprise shock hitting coffee-importing or coffee-exporting channels would need a broader commodity vector), but the residual variance inherits this misspecification. For the T3b gate this is not fatal — omitted-variable bias points toward zero if the omitted regressor is approximately uncorrelated with cpi_surprise_ar1, which is plausible for coffee/coal — but it is worth flagging for the Phase 2 interpretation.

The **RV^(1/3) transform** is Wilson-Hilferty-defensible (cube-root of χ² ≈ normal). For a weekly realized variance built from 5 daily squared log-returns, the χ² approximation is fair. The notebook honestly documents that log(RV) normalizes more tightly on this specific sample (skew 0.29 vs 1.14, kurt_exc 0.64 vs 2.77) and binds the pre-committed choice anyway. Anti-fishing discipline is respected. My only econometric concern: OLS on RV^(1/3) estimates E[RV^(1/3) | X], which is **not** the same as E[RV | X]^(1/3) without a Jensen-inequality correction. The simulator consumes RV^(1/3) residuals directly, so the FHS pathway stays in cube-root space end-to-end; any product-facing pitch that claims "β̂ predicts realized variance" needs the inverse transform and the Jensen correction. This is not a NB1 concern per se but should be flagged for NB2 reconciliation.

The **HAC(4) bandwidth choice** at T=947 is Andrews 1991 q/T = 4/947 = 4.2×10⁻³ in the asymptotic-vanishing regime, so the HAC variance is consistent. The Andrews-optimal data-dependent bandwidth at T=947 under AR(1)-like residual dependence would rule-of-thumb to q ≈ 6-8 based on `⌊4·(T/100)^(2/9)⌋` (Newey-West 1994 plug-in formula), so HAC(4) is on the low end. The pre-registered A12 ladder {4, 8, 12, 20} covers this — good. Note that kurt_exc=17.79 on oil_return and kurt_exc=8.51 on us_cpi_surprise are both within the finite-fourth-moment regime HAC asymptotics require, so no disqualifying fat-tail pathology exists, but the fat tails motivate the bandwidth-sensitivity check that A12 implements.

The **surprise-construction methodological heterogeneity** (AR(1) expanding for CPI, event-study for BanRep rate) is consistent, not contradictory: the two series have fundamentally different DGPs (drifting level process vs step function), and one-size-fits-all AR(1) on a step function would produce over-smoothed expectations. ABDV 2003 Table 4 is the precedent. However, the **interpretation implication** is subtle: the three surprise regressors (Colombian CPI, US CPI, BanRep rate) have different noise-to-signal ratios by construction. AR(1) expanding against a drifting level series has one measurement-error structure (regime-anchored bias on Colombian side); AR(1) against a well-behaved level series (US) is near-unbiased but fat-tailed; event-study against a step function is quasi-error-free at meeting dates but zero elsewhere. The three regressors are therefore **not** econometrically symmetric, and leave-one-out sensitivity (A11 in the pre-registered set) is the right tool to decompose each regressor's contribution — which it is.

---

## 3b. Simulator-handoff coherence (Layer 2)

Every Decision card includes a "Connection to simulator" paragraph that explains how the lock propagates into the RAN FHS simulator. I audited the internal consistency of these claims:

- **Decision #1 → simulator fit window.** FHS requires i.i.d. standardized residuals from a single-regime fit. The 2008-01-02 start is the earliest IBR-available date, so the simulator inherits a single unified window with no forced exclusions. Consistent.
- **Decision #2 → FHS innovation pool in cube-root space.** FHS resamples standardized residuals of the Column-6 OLS on RV^(1/3). Any transformation back to RV space requires the Jensen-inequality correction mentioned in §3. The decision card does not surface this explicitly, but it is an NB2 reconciliation concern, not NB1.
- **Decision #4 → CPI-surprise innovation pool inherits the 205/13 asymmetry.** FHS is exchangeability-preserving: draws from the empirical residual distribution reproduce the 205-negative / 13-positive imbalance. This is correct and honest — the simulator will not smooth away the asymmetry; product-facing simulation paths will reflect it.
- **Decision #6 → monetary-policy innovation pool is 88 events.** 88 nonzero weeks across 947 is a **sparse innovation pool** for FHS block-bootstrap. For stationary bootstrap (Politis-Romano 1994) the 88-event-driven policy-shock channel has limited resampling support. If NB3's FHS draws policy shocks uniformly from the empirical distribution, sampling-variance on the tail will be high. This is not a Phase 1 defect but Phase 3 NB3 should explicitly document its block-length choice and the resulting policy-shock coverage.
- **Decision #9 → intervention innovation pool is binary.** FHS block draws match the binary dummy construction cleanly. The S7 sensitivity drops 73 weeks from the innovation pool, which is a minor re-calibration for the product-pitch confidence interval but does not alter the binary-event architecture.

**Coherence verdict:** the simulator-handoff claims reconcile with the Decision locks. The only latent concern is the policy-shock sparsity (88 events), which is inherent to the EM monetary-policy setting, not a notebook defect.

---

## 4. Data-quality verdict

The audits are honest. The Colombian CPI asymmetry is the central data-quality puzzle in NB1, and the audit chain (alignment rate = 1.000 on live-reverified query; no imputation column on dane_ipc_monthly; 643 pre-sample months of warmup far beyond the 12-month requirement; regime mean MoM 1.23% pre-sample vs 0.41% in-sample) rules out three alternative explanations and accepts regime mismatch as the residual cause. I re-derived the regime means live: pre-sample 1954-2007 mean IPC MoM = **1.2308** vs in-sample 2008-2026 mean = **0.4053**. The roughly 3× ratio is real. The attenuation-bias implication for β̂_CPI is honestly flagged on the Decision #4 card.

The BanRep intervention data-freshness gap (max_date = 2024-10-04, 73 gap weeks = 7.7% of sample) is honest. The 22-events-prior-estimate for the gap is plausible given the 2024 partial-year 22.6% active rate applied to 73 weeks. The gap is scope-limited and the S7 sensitivity addresses it — subject to the S7 propagation issue.

All null counts and alignment rates in the notebook reconcile to live DuckDB queries. The fingerprint chain (decision_hash + weekly sha256 + daily sha256 in `nb1_panel_fingerprint.json`) is a reasonable tamper-evidence seal that NB2 will round-trip.

**Verdict:** Data quality is at the high end of what I see in applied macro-finance pipelines. The single scope-limited concern is the 73-week intervention gap, and it is disclosed.

---

## 5. Pre-registration audit

The pre-registration doc (`2026-04-18-nb3-sensitivity-preregistration.md`) enumerates A9, A12, S1, S2, S3, S4, S5, S6 and hashes them into a SHA-256 tamper-evidence seal. Each entry has motivating finding, frozen execution spec, pass condition, and relationship to NB1 Decisions.

**A9 (asymmetric response):** Motivated by §4a Trio 1 asymmetry finding. Sign-interaction + absolute-value + split-subsample renderings are the standard three. Pass condition is descriptive, not gating. Correctly bound.

**A12 (HAC bandwidth {4, 8, 12, 20}):** Motivated by §4b Trio 1 US CPI kurt_exc=8.51. Andrews 1991 data-dependent bandwidth argument is sound. Pass condition (point-estimate stability within 10% and SE monotonicity) is reasonable and falsifiable.

**S1 (60-month rolling AR(1)):** Motivated by Decision #4 audit (regime anchoring). Pass condition (sign-preserving + within 2 SE of primary) is the right robustness band.

**S2 (drop 2015-2017):** Colombia oil-collapse regime. Pass condition = T3b on reduced panel. Reasonable.

**S3 (drop 2020-2021):** COVID regime. Pass condition = T3b on reduced panel. Reasonable.

**S4 (CPI × intervention_dummy interaction):** Tests whether BanRep intervention absorbs CPI shocks mechanically. Pass condition is gate-component on main effect + descriptive on interaction. Correctly scoped.

**S5 (event-day RV ratio):** Non-parametric fallback for the product-pitch conditional-event-day story. Welch t-test with ρ > 1 and p < 0.05. This is the cleanest AR(1)-agnostic robustness check in the set.

**S6 (demeaned CPI surprise):** Attenuation-theory probe, labeled supplementary. The in-sample-mean caveat is correctly flagged.

**S7 — MISSING FROM PRE-REGISTRATION.** Decision #9's card names S7 as pre-registered, the digest's "Action items for Task 13/15" §157 lists S7 propagation as an explicit action item, but grep confirms the pre-registration doc does not mention S7, 2024-10-07, 2024-10, or freshness. Under the pre-registration's own §5 binding rule, the disk-mtime of the doc is the pre-commitment event. If NB2 runs without S7 in the pre-registration doc, S7 becomes a post-hoc addition that violates the pre-registration's own Simonsohn (2020) discipline. **This is the most material single finding in this review.**

**A1-A12 vs S1-S7 compatibility:** A9 and S1 are the two alternative CPI-surprise renderings (sign-asymmetric, rolling-window); A12 is the bandwidth robustness; S2-S3 are subsample drops; S4-S5 are mechanism probes; S6 is attenuation; S7 is data-freshness. No contradictions among them. A1 (daily-frequency from Rev 4 §8) is named in the spec but not repeated in the pre-registration doc — this is because A1-A8 are Rev 4 spec pre-commitments and A9-A12 + S1-S7 are additive motivated sensitivities. The partition is clean provided S7 lands.

---

## 6. Critical issues (blocks Phase 2 if unresolved)

1. **S7 propagation to `2026-04-18-nb3-sensitivity-preregistration.md`.** Decision #9 card (cell 90, last paragraph) explicitly names this as a required action. Grep confirms it has not happened. Without it, S7 is either (a) absent from the pre-registration on-disk state, which means under §5 it cannot be added after NB2's first β̂ observation; or (b) added after NB2 runs, which is p-hacking under the pre-registration's own Simonsohn (2020) discipline. The resolution is mechanical: append an S7 entry to §3 of the pre-registration doc before Task 13 freezes the NB3 spec, regenerate the SHA-256 fingerprint over the 9-line block (A9, A12, S1-S7), and update `nb1_panel_fingerprint.json` accordingly. Must be done before any NB2 cell evaluates Column-6 OLS. **Severity: HIGH. Blocks NB2 authoring.**

2. **references.bib must land Anzoátegui-Zapata & Galvis 2019 and Uribe-Gil & Galvis-Ciro 2022 (BIS WP 1022).** Decision #6 card explicitly names both as the grounding canon. Current bib has 35 entries; target is 37. `test_references_bib.py` must be updated to assert the new count. The Decision #6 card's `references_bib_gap` field already flags this. **Severity: MEDIUM-HIGH. A decision card citing references the bibliography does not supply is a material weakness. Fix before Task 15 closes.**

3. **Quantify KPSS rejection attribution for Decision #11.** 5 of 7 series reject KPSS stationarity at p < 0.05 (with 3 at the clipped p=0.01 floor). The notebook's prose attribution to heteroskedasticity + regime shifts is defensible but asserted. A wild-bootstrap KPSS (Cavaliere-Taylor 2005 or similar) on the same sample would empirically settle whether rejection is variance-break-driven or unit-root-like. If that check is infeasible in Phase 1, the interpretation paragraph should at least cite the specific regime breaks (2015 COP crisis, 2020 COVID) as candidate conditional-variance epochs and acknowledge that for vix_avg and intervention_dummy the near-unit-root behavior is genuine (vix lag-1 ACF=0.9435 per Decision #7 card). **Severity: MEDIUM. Does not block Phase 2 but should be strengthened before NB3.**

---

## 7. Minor issues (nice-to-have fixes)

1. **Decision #12 vs Decision #9 date inconsistency on S7 threshold.** Cell 108 Trio 1 interpretation refers to "weeks on or after 2024-10-01 ... n = 874"; Decision #9 card (cell 90) specifies `week_start >= 2024-10-07`. Pick one; they differ by 6 days and in principle could differ by 1 week in the n=874 count. Cross-check live: banrep_intervention_daily max_date = 2024-10-04, so the natural cutoff is any week_start > 2024-10-04 (which for ISO weekly grid is 2024-10-07 Monday). Decision #9's 2024-10-07 is the right anchor. Cell 108's "2024-10-01" should be corrected.

2. **Decision #5 card's sensitivity_alt conflates warmup-length with HAC-bandwidth sensitivity.** `sensitivity_alt: A12 HAC(12) bandwidth` is about residual autocorrelation, not warmup length. The warmup-length sensitivity (e.g., 24-month warmup) is not pre-registered. This is a minor documentation clarity issue.

3. **Decision #2 card's "OLS Gaussian-working-model tolerance band" claim.** At kurt_exc=2.77 on RV^(1/3), the band is generous. Tighter prose: "point estimate is consistent under OLS; HAC(4) SEs assume finite fourth moments, which are satisfied here." The current phrasing overstates how clean the tails are.

4. **Cell 30 three-way transform moment table:** the raw RV moments (|skew|≈6.29, kurt_exc≈59.42) are correctly reported but could use an explicit recognition that raw RV **fails** OLS Gaussian-working-model tolerance. The interpretation reads as if raw RV were a live candidate — it's not; Decision #2 was already pre-committed. Tightening the prose would clarify that the three-way comparison is a corroboration exercise, not a selection contest.

5. **Ledger emission (cell 116) lists commit SHAs that are text placeholders for Decisions #4-#9.** `commit_sha: "cpi_surp_ar1"` etc. rather than actual 9-character SHAs. The ledger is a handoff contract; placeholder SHAs reduce its tamper-evidence value. Should be real short-SHAs of the commit that locked each Decision (which the findings digest's §"Commit references for verification" actually supplies: `bfb52e8d0` for Decision #4, `53d0b4895` for Decision #5, etc.).

---

## 8. Strategic read on T3b goal

**Does the pre-committed spec give Abrigo's hedge-product thesis its best chance?**

The T3b gate is `β̂_CPI − 1.28·SE > 0` on the primary OLS (weekly RV^(1/3) on cpi_surprise_ar1 + 6 controls, HAC(4)). Four risk vectors for this gate (per the findings digest §"T3b risk assessment"):

1. **Attenuation bias on cpi_surprise_ar1** (Colombian regime anchoring pulls forecast upward systematically). Biases β̂ toward zero. Passing T3b despite attenuation = strong evidence. Failing T3b does NOT preclude the effect — it is consistent with attenuation masking it. **Risk assessment: real but falsification-useful.**

2. **Sign asymmetry** (205 neg / 13 pos): linear OLS fits the negative tail almost exclusively. Reduces effective identifying variation. A9 addresses this descriptively. **Risk assessment: genuine power loss, not a failure mode.**

3. **Fat tails on us_cpi_surprise (kurt_exc=8.5) and oil_return (kurt_exc=17.8).** HAC(4) is consistent in theory; A12 pre-registered to check empirical bandwidth sensitivity. **Risk assessment: low; the bandwidth ladder is appropriate.**

4. **Intervention data-freshness (73-week gap).** S7 addresses. **Risk assessment: scope-limited (8% of sample), S7 will falsify if the gap is driving the primary result.**

The design **gives the hedge product reasonable fighting room**:

- The primary is methodologically defensible and pre-committed, so passing T3b is scientifically uncontested.
- The conditional-event-day fallback (S5) is empirically independent of AR(1) misspec and supports the product pitch even if the linear primary fails.
- The two-track strategy (clean-primary story vs conditional-event-day story, pre-registered in §4 Interpretation Rules of the pre-registration doc) means a T3b failure is not catastrophic for the product thesis.

A failing T3b is **interpretable** under this design: the attribution (attenuation vs regime heterogeneity vs true null) can be decomposed across A9, S1, S5, S6. Uninterpretable failure would require A9, S1, S5, and S6 all failing simultaneously, which is possible but would constitute the pre-registered "negative result" branch.

**Verdict on strategic design:** The spec gives the hedge product its best reasonable chance. The design is not rigged to pass T3b (there are genuine scenarios that fail it, and the design honestly admits them), but the fallback pathway is real and scientifically defensible.

---

## 9. Uniquely-Model-QA findings

The prompt asks which findings the other two reviewers (Reality Checker, Technical Writer) are unlikely to reach independently. The following are primarily my prong's contribution:

- **Econometric-theory basis for RV^(1/3) (Wilson-Hilferty 1931, cube-root χ² normalization) and its implication for the simulator's Jensen-inequality correction when translating between RV^(1/3) space and RV space.** Reality Checker would likely flag that log(RV) is the empirical winner; Technical Writer would flag prose-clarity on the transform comparison. Neither would independently connect the Jensen-inequality implication for the RAN simulator's inverse-transform pathway.

- **Andrews 1991 data-dependent bandwidth calculation at T=947 (q ≈ 6-8 rule-of-thumb), implying HAC(4) is on the low end.** This is the econometric justification for A12 being necessary rather than precautionary. Neither other reviewer is likely to derive the q/T = 4/947 ≈ 4.2×10⁻³ argument independently.

- **The methodological-heterogeneity subtlety (AR(1) on drifting series vs event-study on step function) implying the three surprise regressors have systematically different noise-to-signal ratios.** This is what motivates A11 leave-one-out decomposition.

- **The wild-bootstrap KPSS recommendation for strengthening Decision #11.** The ADF-KPSS disagreement is a standard applied econometrics puzzle; the prose attribution is defensible; quantifying it via wild-bootstrap (Cavaliere-Taylor 2005) is a specific econometric improvement that the other prongs are unlikely to name.

- **Near-unit-root concern for vix_avg (lag-1 ACF = 0.9435) and intervention_dummy at clipped KPSS p=0.01.** The digest and notebook note lag-1 ACF of VIX but do not flag it as a near-unit-root concern for OLS inference; that is my prong's contribution.

The other findings (S7 gap, references.bib gap, date inconsistency between cells 90 and 108) are likely to be independently reached by Reality Checker, but the econometric weight-of-evidence (especially the HAC-bandwidth and Jensen-inequality reasoning) is Model QA's alone.

---

## 10. Reviewer sign-off recommendation

**CONDITIONAL PASS.**

**Conditions required before NB2 dispatch:**

1. Append S7 entry to §3 of `2026-04-18-nb3-sensitivity-preregistration.md`, regenerate SHA-256 fingerprint over the 9-line sensitivity block (A9, A12, S1, S2, S3, S4, S5, S6, S7), update `nb1_panel_fingerprint.json`. (HIGH severity; blocks NB2 authoring.)
2. Add `Anzoátegui-Zapata & Galvis 2019` and `Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022` to `references.bib`; update `test_references_bib.py` expected count 35 → 37. (MEDIUM-HIGH severity; blocks Task 15 close.)
3. Reconcile the S7-threshold prose discrepancy (cell 108 says 2024-10-01; cell 90 says 2024-10-07). Adopt 2024-10-07 as the canonical anchor. (MINOR; fix during Task 15 cleanup.)

**Recommended before NB3 authoring (not blocking Phase 2):**

4. Quantify Decision #11's KPSS-rejection attribution via wild-bootstrap KPSS on the 5 rejecting series, or tighten the prose attribution with specific regime-break citations.
5. Replace placeholder commit SHAs in cell 116 ledger with real short-SHAs from the digest §"Commit references".
6. Tighten Decision #2's "Gaussian-working-model tolerance band" prose.
7. Clarify Decision #5's sensitivity_alt field to distinguish warmup-length sensitivity from HAC-bandwidth sensitivity.

**Econometrically, the primary specification is defensible and the pre-commitment discipline is real.** The T3b gate is interpretable in both pass and fail directions. Subject to S7 propagation landing before NB2, Phase 2 can commence.

---

## 11. Appendix — live spot-check summary

The following numerics from NB1 were re-derived from the live DuckDB warehouse (`notebooks/fx_vol_cpi_surprise/Colombia/env.DUCKDB_PATH`) at the time of this review:

| Check | Cell | Claimed | Live re-derived | Match |
|---|---|---|---|---|
| Decision #1 n_weeks | 17 | 947 | 947 | exact |
| Decision #2 RV^(1/3) mean | 32 | 0.0585 | 0.0585 | exact |
| Decision #2 RV^(1/3) std | 32 | 0.0229 | 0.0229 | exact |
| Decision #2 RV^(1/3) skew | 32 | 1.1393 | 1.1393 | exact |
| Decision #2 RV^(1/3) kurt_exc | 32 | 2.7727 | 2.7727 | exact |
| Decision #4 Colombian CPI n_neg | 44 | 205 | 205 | exact |
| Decision #4 Colombian CPI n_pos | 44 | 13 | 13 | exact |
| Decision #4 mean_nonzero | 44 | −0.6878 | −0.6878 | exact |
| §4a audit pre-sample MoM mean | 41 | +1.23% | +1.2308% | exact |
| §4a audit in-sample MoM mean | 41 | +0.40% | +0.4053% | exact |
| Decision #6 banrep n_events | 74 | 88 | 88 | exact |
| Decision #6 corr(banrep, cpi) | 74 | +0.074 | +0.0739 | exact |
| Decision #7 VIX mean | 65 | 19.90 | 19.90 | exact |
| Decision #7 VIX kurt_exc | 65 | +8.51 | +8.51 | exact |
| Decision #7 VIX max | 65 | 74.62 | 74.62 | exact |
| Decision #8 oil mean | 80 | −0.0004 | −0.0004 | exact |
| Decision #8 oil kurt_exc | 80 | +17.79 | +17.7917 | exact |
| Decision #9 frac_active | 89 | 0.334 | 0.334 | exact |
| Decision #9 gap_weeks | 89 | 73 | 73 | exact |
| Decision #9 2008-2014 regime pct | 89 | 71.0% | 71.0% | exact |
| Decision #9 2015-2019 regime pct | 89 | 3.8% | 3.8% | exact |
| Decision #9 2020 regime pct | 89 | 63.5% | 63.5% | exact |
| Decision #9 2024 regime pct | 89 | 22.6% | 22.6% | exact |
| §5 max |Pearson| (vix×oil) | 92 | −0.142 | −0.1416 | exact |
| §5 corr(vix, rv_cuberoot) | 92 | +0.355 | +0.3551 | exact |
| §5 corr(intervention, rv) | 93 | −0.235 | −0.2353 | exact |
| §6 ADF banrep stat | 101 | −3.31 | −3.3122 | exact |
| §6 ADF banrep p-value | 101 | 0.0143 | 0.0143 | exact |
| references.bib count | n/a | 35 current / 37 target | 35 | gap confirmed |
| S7 in pre-registration doc | n/a | should be present | absent | **gap confirmed** |

Spot-check verdict: **every numeric claim I tested reconciles exactly.** The notebook's live-query discipline (each Decision card re-derives its numbers rather than caching them) is working as designed. Zero drift between prose, card, and warehouse on the 24 numerics I spot-checked.

---

*End of Model QA review.*
