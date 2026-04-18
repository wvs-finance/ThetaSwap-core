# NB3 Sensitivity Pre-Registration

**Frozen date:** 2026-04-18
**Target notebook:** `contracts/notebooks/fx_vol_cpi_surprise/Colombia/03_tests_and_sensitivity.ipynb` (NB3)
**Plan tasks covered:** Tasks 24–31 of `contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md`
**Consumed by:** Task 13 (`cleaning.py` + fingerprint emission + pre-NB3 prep)
**Anchored in:** spec Rev 4 §8 (`2026-04-17-econ-notebook-design.md`), Phase 1 findings digest (`contracts/.scratch/2026-04-18-phase1-findings-digest.md`)

---

## 1. Pre-Registration Declaration

This document is the **frozen set** of specification-sensitivity analyses that NB3 will execute. The enumeration below is committed **before** any NB2 estimation run has been observed and before any point estimate of β̂_CPI exists outside of NB1 descriptive outputs.

**Binding rule.** Any sensitivity added to NB3 after the disk-mtime of this file, without an explicit amendment that (a) is dated, (b) is signed by the pipeline owner, (c) cites written rationale tied to a pre-amendment artifact (not a post-amendment β̂), and (d) is registered **strictly before** any NB2 point estimate is observed, constitutes p-hacking under the Simonsohn (2020) specification-curve convention and invalidates the T3b gate.

**Anti-fishing seal.** The list of sensitivity IDs below (A9, A12, S1, S2, S3, S4, S5, S6) is to be hashed into `nb1_panel_fingerprint.json` by Task 13 so that post-hoc additions or silent edits are detectable. The fingerprint hash becomes the tamper-evidence seal on this pre-registration.

**Atomic pre-commitment.** The presence of this file on disk — even before the git commit that will track it — is the pre-commitment event. Editing this file after any NB2 β̂ has been observed does not retroactively legalize additions; the original on-disk state governs. Amendments must follow §5 (Amendment Protocol) below.

---

## 2. Scope

This pre-registration governs the sensitivity battery in NB3 §8 (forest-plot rows) and §9 (material-mover spotlight tables). It does **not** govern:

- The NB2 primary OLS specification (locked in spec Rev 4 §7; already pre-committed via `spec_hash`).
- NB2 co-primary specifications (GARCH-X, decomposition-CPI, decomposition-PPI, three subsamples) — these are spec Rev 4 pre-commitments and are run unconditionally in NB2, not NB3.
- NB3 T1–T7 specification tests — these are spec Rev 4 pre-commitments and are run unconditionally.

This pre-registration adds explicit freezing of:

- **A9** (Asymmetric response): formalized execution spec for an anticipated-but-under-specified Rev 4 entry.
- **A12** (HAC bandwidth robustness): **new**. Not anticipated in Rev 4 §8 (which enumerates A1–A9 only). Added here ahead of NB2 on the strength of §4b Trio 1 evidence (US CPI kurt_exc = 8.51).
- **S1–S6** (six new motivated sensitivities): not anticipated in Rev 4. Motivated by NB1 findings surfaced in §4a and §4b.

**Relationship to Rev 4 §8.** Spec Rev 4 §8 enumerates A1–A9. A12 and S1–S6 are additive to that set. Their addition is pre-registered here, before any β̂ has been observed, and is therefore permitted under the Simonsohn (2020) regime provided the amendment protocol is respected for any further additions.

---

## 3. Sensitivities

Each entry below specifies: ID, short title, motivating finding with commit/cell citation, frozen execution specification, pass condition with explicit numerical threshold, and relationship to the Phase 1 Decisions locked in NB1.

Notation conventions across all entries:

- **Column-6 OLS** = the NB2 primary specification: `RV^(1/3)_t ~ cpi_surprise_ar1_t + 6 controls`, weekly frequency, HAC(4) standard errors, sample 2008-01-02 → 2026-03-01 (n_weeks = 947).
- **T3b pass criterion** = `β̂_CPI − 1.28·SE > 0` (one-sided 90%).
- **Significance at one-sided 90%** is the default gate unless otherwise noted.

### A9 — Asymmetric response in sign of Colombian CPI surprise

**Status:** anticipated in spec Rev 4 §8 (enumerated as an A1–A9 entry); this document formalizes the execution specification.

**Motivating finding.** NB1 §4a Trio 1 (commit `0f9751bc6`) established that among 218 non-zero weekly Colombian CPI surprises, 205 (94%) are negative and only 13 (6%) are positive. The nonzero mean of `cpi_surprise_ar1` is −0.69 (strongly biased, not centered on zero). §4a Trio 2 (commit `6d3a130b4`) audited and ruled out three candidate methodological bugs and accepted the asymmetry as a genuine regime-anchoring property of the expanding-window AR(1) forecaster (pre-sample 1954–2007 mean MoM of +1.23% vs in-sample 2008–2026 mean of +0.40%). Linear OLS on this series fits what it sees, which is almost exclusively the negative tail; this collapses the effective identifying variation and is grounds for a formal symmetry test.

**Frozen execution specification.** Three alternative Column-6 specifications, each run independently on the full 2008–2026 weekly panel with HAC(4):

1. **Absolute-value rendering:** replace `cpi_surprise_ar1` with `|cpi_surprise_ar1|`. Reports β̂_abs.
2. **Sign-interaction rendering:** include both `cpi_surprise_ar1` and `cpi_surprise_ar1 × I(cpi_surprise_ar1 > 0)`. Reports β̂_neg on the main term and β̂_pos−β̂_neg on the interaction. Provides explicit β̂⁺ and β̂⁻ via linear combination.
3. **Split-subsample rendering:** estimate two OLS models separately on the `cpi_surprise_ar1 < 0` subsample (n = 205 events + zero-surprise weeks) and the `cpi_surprise_ar1 > 0` subsample (n = 13 events + zero-surprise weeks). Reports β̂_neg and β̂_pos.

Per Rev 4 §8 the forest plot renders (2) as two rows (β̂⁺, β̂⁻) for transparency.

**Pass condition.** A9 is descriptive, not a gate. Report convention:

- If `|β̂_pos − β̂_neg| / SE_diff > 1.645`, classify as **asymmetric response confirmed**.
- Otherwise, classify as **symmetry not rejected**.

No invalidation of T3b follows from either outcome; A9 documents the functional form the linear primary averages over.

**Relationship to NB1 Decisions.** Decision #4 (Colombian CPI surprise spec) pre-registered the `cpi_surprise_ar1` series as primary with the asymmetric alternative as sensitivity. A9 implements the asymmetric-alternative row of Decision #4.

---

### A12 — HAC bandwidth sensitivity

**Status:** **new (not in spec Rev 4 §8)**. Pre-registered here before any NB2 β̂ observation.

**Motivating finding.** NB1 §4b Trio 1 (commit `50da209f6`) reports that the US CPI surprise series (`cpi_surprise_ar1` operator applied to FRED CPIAUCSL) has `kurt_exc = 8.51` on nonzero surprises. Colombian series kurt_exc = 1.11, so the global panel inherits the US fat-tail regime through the CPI-orthogonality controls. Finite fourth moments hold and HAC(4) is Newey-West consistent in theory, but Andrews (1991) data-dependent bandwidth at T = 947 under AR(1)-equivalent residual dependence yields a rule-of-thumb optimum of q ≈ 6–8. HAC(4) is therefore narrow relative to the Andrews-optimal bandwidth. Bandwidth sensitivity is now empirically motivated rather than theoretically prudent.

**Frozen execution specification.** Re-run the Column-6 OLS with four HAC bandwidths: q ∈ {4, 8, 12, 20}. Report the full 4-row table of (β̂_CPI, SE_HAC(q), T3b one-sided statistic) for each q. Kernel family held fixed at Bartlett (Newey-West). All other specification elements identical to NB2 primary.

**Pass condition (both prongs must hold).**

1. **Point-estimate stability:** `max_q |β̂_CPI(q) − β̂_CPI(4)| / |β̂_CPI(4)| < 0.10`.
2. **SE monotonicity:** `SE_HAC(q)` is non-decreasing in q across {4, 8, 12, 20}, or any violation is a reversal of less than 5%.

If both prongs hold, HAC(4) is classified **bandwidth-robust**. If prong (1) fails, the primary specification is demoted to a co-primary and the NB2 §3.5 bootstrap-HAC reconciliation flag is re-evaluated. If only prong (2) fails, flag as **bandwidth-irregular** and record in the gate verdict without demotion.

**Relationship to NB1 Decisions.** No Decision directly; A12 is a robustness check against the HAC(4) choice implicit in spec Rev 4 §7 (which cites Newey-West with default lag = 4 per Andersen et al. 2003 weekly-RV convention).

---

### S1 — 60-month rolling AR(1) surprise

**Status:** **new**. Pre-registered here. Sits in Decision #4 (NB1) as the pre-committed alternative surprise construction; this document formalizes the execution specification for NB3.

**Motivating finding.** NB1 §4a Trio 2 audit (commit `6d3a130b4`) accepted the root-cause of Colombian CPI-surprise asymmetry as the expanding-window AR(1) forecaster anchoring its intercept to the full 1954-present DANE IPC history, which includes the 1954–2007 high-inflation and hyperinflation episodes with mean MoM ≈ 1.23%. A rolling 60-month AR(1) window drops the pre-2003 history from the conditioning set once the rolling window leaves it behind, and after a 2008-start warm-up the forecaster conditions only on the modern BanRep inflation-targeting regime. This isolates whether the primary's identifying variation is regime-mixing artifact or genuine response.

**Frozen execution specification.** Construct an alternative surprise series `cpi_surprise_rolling60` as the one-month-ahead forecast error from an AR(1) estimated on a rolling 60-month window over DANE IPC MoM. Warm-up: discard the first 60 months after the series start; for the 2008-start weekly panel, warm-up is already satisfied. Re-run Column-6 OLS using `cpi_surprise_rolling60` in place of `cpi_surprise_ar1`, holding all 6 controls, HAC(4), and sample window constant.

**Pass condition.** `sign(β̂_rolling60) == sign(β̂_primary)` **and** `|β̂_rolling60 − β̂_primary| < 2 · max(SE_rolling60, SE_primary)`. Both prongs required.

**Relationship to NB1 Decisions.** Decision #4 pre-registered `cpi_surprise_rolling60` as the alternative surprise-construction sensitivity. S1 executes that row.

---

### S2 — 2015–2017 COP-crisis sub-sample drop

**Status:** **new**. Pre-registered here.

**Motivating finding.** The 2014–2016 oil-price collapse drove a COP/USD regime shock (TRM moved from ≈ 2000 to ≈ 3400, a near-70% depreciation), with persistent elevated realized volatility through 2017. §4a Trio 1 (commit `0f9751bc6`) and the product-strategy analysis both flag this as a dominant source of 2008–2026 TRM-vol variation. Whether β̂_CPI is identified on this one regime shock or on the broader 18-year sample is a material question; dropping the window isolates it.

**Frozen execution specification.** Drop all weekly observations with `week_start` in the closed interval [2015-01-01, 2017-12-31] (inclusive of both endpoints). Expected dropped rows: 156 weeks (52 × 3). Re-run Column-6 OLS on the reduced panel (n = 791 weeks), HAC(4), all 6 controls, with `cpi_surprise_ar1` as regressor.

**Pass condition.** `β̂_CPI,S2 − 1.28 · SE_HAC(4),S2 > 0` (one-sided 90%). Same functional form as the T3b gate.

**Relationship to NB1 Decisions.** None directly. S2 is a subsample-robustness probe against regime-concentrated identifying variation.

---

### S3 — 2020–2021 COVID sub-sample drop

**Status:** **new**. Pre-registered here.

**Motivating finding.** NB1 §4b Trio 1 (commit `50da209f6`) reports that the 2020 COVID shock and 2021–22 inflation spike are the dominant drivers of the US-CPI fat-tail kurtosis (kurt_exc = 8.51). The Phase 1 findings digest (§4b, disk mirror at `contracts/.scratch/2026-04-18-phase1-findings-digest.md`) also flags this window as a driver for COP/USD volatility. A subsample drop from the other regime-shock window (S2 drops the oil collapse; S3 drops the pandemic) completes the two-regime robustness probe.

**Frozen execution specification.** Drop all weekly observations with `week_start` in the closed interval [2020-03-01, 2021-12-31] (inclusive of both endpoints). Expected dropped rows: ≈ 94 weeks. Re-run Column-6 OLS on the reduced panel (n ≈ 853 weeks), HAC(4), all 6 controls, with `cpi_surprise_ar1` as regressor.

**Pass condition.** `β̂_CPI,S3 − 1.28 · SE_HAC(4),S3 > 0` (one-sided 90%). Same functional form as the T3b gate.

**Relationship to NB1 Decisions.** None directly. S3 complements S2 on the other regime-shock window.

---

### S4 — CPI_surprise × intervention_dummy interaction

**Status:** **new**. Pre-registered here.

**Motivating finding.** NB1 §4a analysis and the product-strategy read (Phase 1 findings digest §"Strategic product read") both flag the hypothesis that Banrep's FX-intervention policy — captured by the `intervention_dummy` control — mechanically absorbs CPI shocks before they reach TRM volatility. If true, β̂_CPI on non-intervention weeks should be systematically larger in magnitude than on intervention weeks, and the interaction coefficient should carry the sign opposite to the main effect. This is a direct economic-mechanism test complementing T7 (which tests whether `intervention_dummy` as a linear control adequately captures the intervention signal, but does not test its interaction with CPI).

**Frozen execution specification.** Add the interaction term `cpi_surprise_ar1 × intervention_dummy` to Column-6, keeping the main `cpi_surprise_ar1` term and all 6 controls. Estimate with HAC(4) on the full 2008–2026 weekly panel. Report:

1. Main effect β̂_CPI (interpretation: response on non-intervention weeks).
2. Interaction coefficient β̂_interact.
3. Joint F-test of `H0: β̂_CPI = β̂_interact = 0`.

**Pass condition (descriptive + gate-component).**

- **Gate-component:** main effect retains T3b significance on non-intervention weeks, i.e. `β̂_CPI,S4 − 1.28 · SE_HAC(4),S4 > 0`.
- **Descriptive:** sign and significance of β̂_interact reported; no gate condition on interaction sign.

**Relationship to NB1 Decisions.** None directly. S4 is a policy-mechanism probe against the implicit-linearity assumption in the NB2 primary.

---

### S5 — Event-day realized volatility ratio

**Status:** **new**. Pre-registered here.

**Motivating finding.** Product positioning analysis (Phase 1 findings digest §"Strategic product read") observes that if the NB2 primary fails T3b due to measurement error in the constructed surprise series (a known attenuation-bias risk flagged in the T3b risk assessment, and a possibility reinforced by §4a's asymmetry finding), a simpler non-parametric test — "TRM is more volatile on Colombian CPI release days than on non-release days" — survives as empirical support for the Abrigo hedge product. This statistic is robust to AR(1) misspecification because it does not use the surprise magnitude at all, only the release-date indicator. It is therefore a structurally independent fallback.

**Frozen execution specification.** Partition the 2008–2026 weekly panel into two sets by the `cpi_release_this_week` indicator:

- **Release weeks:** weeks containing a Colombian DANE IPC release date (n ≈ 218 by §4a event-density).
- **Non-release weeks:** weeks without a Colombian CPI release (n ≈ 729).

Compute mean `RV^(1/3)` on each subset. Compute the ratio `ρ = mean_release / mean_non-release`. Report `ρ` with a Welch two-sample t-test (unequal variances) of `H0: mean_release = mean_non-release` against the two-sided alternative. Report both the Welch t-statistic and p-value.

**Pass condition.** `ρ > 1` **and** Welch p-value `< 0.05` (two-sided). Both prongs required.

**Relationship to NB1 Decisions.** None directly. S5 is a model-independent product-facing statistic that serves the conditional-event-day fallback narrative.

---

### S6 — De-meaned Colombian CPI surprise

**Status:** **new**. Pre-registered here. **Supplementary only**; see caveat below.

**Motivating finding.** A subagent-proposed probe (ZK Steward signal-processing Gegenrede on the Phase 1 findings digest) observes that if `cpi_surprise_ar1` has a known in-sample mean offset (§4a: nonzero mean = −0.69), subtracting the in-sample mean before regression recovers a less-attenuation-biased point estimate of the response slope, at the cost of using in-sample information in the regressor construction. Classical attenuation theory predicts that a centered regressor (with the deterministic offset removed) should deliver a larger `|β̂|` than the uncentered regressor if measurement error is additive and the offset is non-informative.

**Frozen execution specification.** Construct `cpi_surprise_ar1_demeaned = cpi_surprise_ar1 − in_sample_mean(cpi_surprise_ar1)`, where the in-sample mean is computed over the full 2008–2026 weekly panel (n = 947, not restricted to nonzero events). Re-run Column-6 OLS with `cpi_surprise_ar1_demeaned` in place of `cpi_surprise_ar1`. HAC(4), 6 controls, same sample window.

**Pass condition (descriptive).**

- **Direction:** `|β̂_CPI,S6| > |β̂_CPI,primary|` (point estimate moves in the direction predicted by attenuation theory).
- **Sign:** `sign(β̂_CPI,S6) == sign(β̂_CPI,primary)` (unchanged).

S6 does **not** gate T3b. It is reported as supplementary evidence on the attenuation-bias risk vector.

**Caveat (in-sample information leakage).** Because the in-sample mean is computed on the same 2008–2026 sample used for estimation, S6 uses in-sample information in the regressor construction. This is a mild methodological compromise relative to the primary, which uses only the expanding-window pre-sample history. S6 is therefore explicitly labelled **supplementary** in the NB3 forest plot and is **not** a material-mover candidate under the §9 spotlight rule. Its role is descriptive: it quantifies the lower bound on attenuation-induced downward bias in the primary, not a free-standing estimate of the response.

**Relationship to NB1 Decisions.** None directly. S6 is an internal-validity probe against attenuation bias.

---

## 4. Interpretation Rules

NB3 produces eight sensitivity outcomes (A9, A12, S1, S2, S3, S4, S5, S6) plus the T3b gate from NB2 and the T1–T7 specification tests. The following interpretation table maps combinations of pass/fail onto three product-facing narratives. This table is itself pre-registered; the narrative selected at gate time must be the one this table designates, not one chosen post-hoc.

### (a) Clean-primary story

**Narrative:** "Colombian CPI surprise linearly moves TRM realized volatility; the effect is signed, significant, and stable across regimes and functional forms."

**Required conditions (all must hold):**

- T3b passes on NB2 primary.
- T1 (consensus rationality), T6 (structural-break stability) pass.
- A12 classified as **bandwidth-robust** (both prongs).
- S1 passes (sign-unchanged, within 2·SE of primary).
- At least one of {S2, S3} passes (β̂ retains T3b significance on the regime-dropped subsample).
- S4 main effect retains T3b significance.
- A9 may classify as symmetric or asymmetric; does not gate the clean story.

### (b) Conditional-event-day story

**Narrative:** "TRM is more volatile on Colombian CPI release days than on non-release days; large-magnitude surprises move it substantially. The linear specification is a lower bound on the response because of attenuation from measurement error in the surprise construction."

**Required conditions (all must hold):**

- T3b **may fail** on NB2 primary, but need not.
- S5 passes (event-day vol ratio > 1 with p < 0.05).
- A9 classifies as **asymmetric response confirmed**, OR the absolute-value rendering (A9 spec 1) passes T3b.
- S6 sign-unchanged; direction-of-change descriptive flag reported.

This story is the product-pitch fallback: it supports the Abrigo hedge empirically even when the linear primary fails the scientific gate.

### (c) Negative result

**Narrative:** "The evidence does not support a robust linear response of TRM realized volatility to Colombian CPI surprises on the 2008–2026 weekly sample."

**Conditions triggering negative result:**

- T3b fails on NB2 primary, **and**
- S5 fails (no event-day vol elevation), **and**
- A9 absolute-value rendering fails T3b, **and**
- Both of {S2, S3} fail in the subsample-drop direction.

Negative result is declared only when the conditional-event-day fallback (b) also fails. The two-track strategy (research integrity + product empirical support) requires both tracks to fail before a negative result is publishable.

### Edge cases

- **Clean-story required conditions partially met:** if T3b passes but (e.g.) A12 classifies as bandwidth-irregular or S1 fails, the narrative is **"qualified clean story"** and the qualification must be explicit in the gate-verdict README. The material-mover spotlight (§9) is responsible for enumerating the sensitivity that broke the full-clean condition.
- **Conflict between (a) and (b) conditions met simultaneously:** default to the clean-primary narrative and report the event-day statistic as corroborating evidence in the product pitch. Do not escalate to (b) when (a) is available.

---

## 5. Amendment Protocol

This pre-registration is frozen as of the disk mtime of this file on 2026-04-18. Amendments are permitted only under the following conditions.

### Permitted amendment window

Amendments (adding a sensitivity, tightening a pass condition, narrowing a sample window) may be accepted strictly between the disk-mtime of this file and the moment of the first NB2 β̂ observation. Operationally, the "first NB2 β̂ observation" is the wall-clock time at which any NB2 notebook cell that evaluates the Column-6 primary OLS completes execution and returns a coefficient. Once that event occurs, this pre-registration is frozen in the stronger sense: no further additions, tightenings, or narrowings are permitted.

### Forbidden at any time

The following edits are p-hacking regardless of timing and are forbidden even before any NB2 run:

- Loosening a pass condition (e.g. from one-sided 90% to one-sided 80%).
- Removing a sensitivity from the set.
- Changing a pass condition after seeing a NB1 descriptive statistic that directly motivated it (this creates a data-driven specification selection loop).
- Reclassifying a gate-component sensitivity as descriptive-only.

### Required artifacts for an amendment

Any permitted amendment must produce:

1. **Amendment block** appended to this file, dated, with written rationale tied to a specific pre-amendment artifact (NB1 cell, subagent-review document, methodology paper). The rationale may not cite any NB2 output.
2. **Re-hashed fingerprint** registered by Task 13 into `nb1_panel_fingerprint.json`; the old hash is invalidated and the new hash takes effect.
3. **Pipeline-owner signature line** at the bottom of the amendment block: `[signed: <owner>, date: YYYY-MM-DD, pre-NB2: true]`. The `pre-NB2: true` flag is a cryptographic-in-spirit attestation that the first NB2 β̂ has not yet been observed; violating the attestation retroactively invalidates the T3b gate.

### Reference protocol

The amendment protocol follows the Simonsohn (2020) specification-curve convention: the pre-registered set is the universe of specifications evaluated, and the forest plot renders every member. Post-hoc additions inflate the false-discovery rate of the multiple-comparison adjustment implicit in the specification-curve p-value. This is the formal statistical reason for the ban.

---

## 6. References (external, evidence-backing)

The following bib keys in `contracts/notebooks/fx_vol_cpi_surprise/Colombia/references.bib` ground the methodological choices in this pre-registration:

- **`andrews1991heteroskedasticity`** — data-dependent HAC bandwidth selection; motivates the A12 bandwidth ladder {4, 8, 12, 20}.
- **`andersen2003micro`** — weekly realized-volatility convention including the default Newey-West lag = 4; motivates the HAC(4) baseline against which A12 tests bandwidth sensitivity.
- **`simonsohn2020specification`** — specification-curve convention, pre-registration discipline, and the ban on post-hoc specification additions; motivates §1 (pre-registration declaration) and §5 (amendment protocol).

---

## 7. Fingerprint Payload

Task 13 must hash the following ordered list of sensitivity IDs and their pass-condition strings into `nb1_panel_fingerprint.json` under the key `sensitivity_preregistration_hash`:

```
A9  |  A9_descriptive  |  sign_or_split_rendering
A12 |  bandwidth_ladder_{4,8,12,20}  |  point_stable_10pct_and_SE_monotonic
S1  |  rolling60_AR1 |  sign_unchanged_within_2SE
S2  |  drop_2015_2017 |  T3b_90pct_onesided
S3  |  drop_2020_2021 |  T3b_90pct_onesided
S4  |  surprise_x_intervention |  main_effect_T3b_90pct
S5  |  event_day_ratio |  ratio_gt_1_and_Welch_p_lt_0p05
S6  |  demeaned_surprise |  supplementary_direction_and_sign
```

The hash algorithm is SHA-256 over the UTF-8 encoding of the above 8-line block, newlines as LF, no trailing newline. Task 13 records the hash and rejects any downstream fingerprint mismatch as a p-hacking detection event.

---

*End of pre-registration.*
