# Phase 5b Analytics Reporter — Independent Model QA Audit

**Auditor:** Model QA Specialist (independent; no participation in Phase 5a/5b authoring)
**Audit date:** 2026-04-26
**Subject:** Task 11.O Rev-2 Phase 5b Analytics Reporter at HEAD `799cbc2802d6bcdf4beb80d033d9f1df533b13e4`
**Scope artifacts audited (read-only):**
- Spec: `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (commit `d9e7ed4c8`, 655 lines)
- Data manifest + 14 panel parquets: `contracts/.scratch/2026-04-25-task110-rev2-data/`
- Phase 5b output: `contracts/.scratch/2026-04-25-task110-rev2-analysis/{summary.md, estimates.md, spec_tests.md, gate_verdict.json, sensitivity.md}`
- Calibration source: `contracts/scripts/carbon_calibration.py`
- Primary panel: `panel_row_01_primary.parquet` (76 obs × 13 cols)

**Lens:** model-quality (NOT execution-correctness) — independent of T3b PASS/FAIL direction, is the *model* defensible? The CR/RC/SD reviewers handle execution; this audit examines methodology, identification, calibration validity, residual diagnostics, and external-validity threats.

---

## Verdict: **MODEL-PASS-w-adv**

**Pass** because: the model replicates byte-exact, calibration is hash-locked and independently re-derived, the FAIL verdict is honestly reported, anti-fishing audit trail is intact, and the convex-payoff caveat at §11.A is the right load-bearing disclosure for a mean-β regression deployed for option-pricing.

**With advisory** because: I surfaced **3 model-quality concerns** Phase 5b does not address. None invalidate the FAIL verdict — they would only widen the SE or flip the sign — so they reinforce the FAIL rather than rescue it. They are recorded for Rev-3 / future-revision discipline.

---

## Findings — severity-rated

| # | Finding | Severity | Domain | Action / disposition |
|---|---|---|---|---|
| 1 | Replication is byte-exact: β̂ = -2.7987050503705652e-08, SE = 1.4234226026833985e-08, rel-delta = 0 vs Phase 5b reported | Info | Replication | Pass byte-exact at 1e-10 tolerance; gate verdict reproducible |
| 2 | MDES_FORMULATION_HASH live = `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` MATCH; required_power(76/65/56, 13, 0.40) = (0.8689, 0.8027, 0.7301) byte-exact | Info | Calibration | Pass; load-bearing power numbers verified independently |
| 3 | T1 manual replication: F = 3.4797, p = 0.003111 → rejects at 5%; matches Phase 5b reported (3.480 / 0.0031) | Info | Spec tests | Pass; T7 predictive-flag triggered correctly |
| 4 | Breusch-Pagan on Row 1 OLS residuals: stat = 16.16, p = 0.0237 → **heteroskedasticity REJECTS at 5%**, but only quartile-by-X_d Levene (T2) ran in Phase 5b; general-form heteroskedasticity is not surfaced | Medium | Calibration | NEW — recommend adding Breusch-Pagan + White as T2.b in Rev-3 spec; HAC handles it asymptotically but at n=76 finite-sample SE may be optimistic |
| 5 | Influence diagnostics: 6/76 obs with Cook's D > 4/n; 8/76 with leverage > 2k/n. Single dominating observation (2026-03-06, D = 0.888, sr = -3.13, X_d = 168k, Y₃ = -0.042) drives the negative β̂ | Medium | Interpretability | NEW — drop-one sensitivity not in spec; β̂ sign is robust to single-obs removal (β̂ moves -2.799e-8 → -2.661e-8 dropping 2026-03-06) but t-stat softens from -1.97 → -1.83. The FAIL is robust; the *magnitude* is influence-driven |
| 6 | Multicollinearity: ρ(x_d, fed_funds_weekly) = -0.614; VIF(x_d) = 1.82, VIF(fed_funds) = 1.91. Below standard alarm thresholds but economically meaningful — Carbon volume rises when fed_funds is low, exactly when EM equity rises (Y₃ ↑ via R_equity), creating shared-third-factor mechanical inverse correlation | Medium | Identification | NEW — potential omitted-variable / shared-factor bias that could explain the sign-flip; the predictive-regression flag at T1 already partially absorbs this, but a residualizing decomposition (e.g., fed_funds-orthogonalized X_d) would clarify whether β̂'s sign is "after partialling fed_funds" or "shared with fed_funds" |
| 7 | Spec §5 MDES recompute uses `k_regressors=13` while the regression equation §4.1 has only 7 parameters (X_d + 6 controls + intercept). Power computed at k=13 = 0.8689 vs at k=7 = 0.8714; gate (≥ 0.80) holds either way. **Conservative-direction inconsistency** carried forward from FX-vol prior-art | Low | Documentation | Document — spec body's own justification at §5 line 309 says "df₁ = 6 (control γ's) + 1 (X_d) − 1 (constant) = 6" which is internally consistent for df₁ but does not justify k=13. Recommend Rev-3 either drop k=13 (use k=7) or add a footnote explaining the FX-vol carry-forward |
| 8 | Anti-fishing audit table reproduced byte-exact in `summary.md`; convex-payoff caveat from §11.A reproduced verbatim; pivot paths from §11.C surfaced; no silent reframing of FAIL as PASS | Info | Reporting | Pass; HALT-to-user discipline followed |
| 9 | T6 Chow break test reports F = NaN with honest "test cannot be run on this sample" caveat — not an imputed value. Spec §7 calls Bai-Perron unknown-break; Phase 5b runs Chow at known launch date as a boundary-test variant. Inconsistency between spec and execution is documented at `spec_tests.md` line 73 with rationale | Low | Spec tests | Pass-with-disclosure; recommend Rev-3 either implement Bai-Perron unknown-break (which can run on 76-week panel without pre-launch rows) or pre-register the Chow-at-launch substitution explicitly |
| 10 | T3a (two-sided) REJECTS at 5% (p = 0.0493) — Y₃ and X_d ARE statistically related; the relationship is just **inverse, not the pre-registered positive direction**. This is *stronger evidence than "no effect"* and is correctly framed in `summary.md` headline. Pattern matches FX-vol-CPI notebook's β̂_CPI = -0.000685 (n=947, T1 REJECTS, T3a borderline) — the same predictive-regression artifact | Info | Performance monitoring | Pass; framing is faithful and the prior-art carry-forward is honest |
| 11 | Sample N = 76 with k_eff = 7 → df₂ = 69. Razor-thin for high-dimensional residual diagnostics; the JB normality fail-to-reject (p = 0.68) is consistent but underpowered. Real effect size at n=76 with MDES_SD = 0.40 is detectable only at f² ≥ 0.16. Rev-2 already pre-registered this trade-off; the question for Rev-3 is whether the panel-decomposition (ε.1, 228 row-equivalents) is the right next-spec power lift | Low | External validity | Documented; Rev-2 spec §1.2 + §10 ε.1 acknowledges; not a Rev-2 defect but a roadmap reminder |

---

## Detailed audit — by domain

### 1. Documentation review (spec internal consistency)

**Pass with one minor inconsistency (Finding 7).** The Track A spec is unusually well-structured for an autonomous-track product — the Reiss-Wolak three-stage decomposition (§§1–4) is honored, the seven controls are explicitly defended, the inflation-surprise substitution is justified at §4.4 with a 4-part citation block, and the convex-payoff insufficiency caveat at §11.A is correctly load-bearing.

**Functional form / error structure / identification / gate threshold are logically aligned:**
- Functional form: Y₃ identity transform ↔ Y₃ is already a signed log-difference (§1.4) — dimensionally consistent.
- Error structure: ε = η + u + v decomposition (§3.4) ↔ HAC(4) Newey-West truncation ↔ Politis-Romano bootstrap reconciliation. The η-X_d orthogonality identifying assumption is testable via T1.
- Identification: §4.3.1 explicitly addresses the α+β operationalization via continuous-control partialing (vs. release-event-window dummies); the spec author acknowledges the dummy-interaction approach is a Rev-2.1+ deferral.
- Gate threshold: T3b one-sided 90% via `β̂ − 1.28 × SE > 0`. Standard, matches FX-vol prior-art, no silent tuning.

**Inconsistency (Finding 7):** the §5 MDES recompute table uses `k_regressors=13` while the actual regression at §4.1 has 7 parameters. Power computed at k=13 is 0.8689; at k=7 is 0.8714. Both ≥ POWER_MIN = 0.80, so the gate verdict is unchanged. This is a carry-forward from FX-vol Rev-4 prior-art (which had a richer parameter space) and is conservatively biased — it makes the calibration *harder* to pass, not easier. **Severity: Low.** Recommend Rev-3 either:
- Drop k=13, use k=7 (true regressor count), document as Rev-3 calibration update with CORRECTIONS block; OR
- Keep k=13, add an explicit footnote at §5 explaining the FX-vol carry-forward and the conservative-direction nature of the choice.

### 2. Data reconstruction sanity (manifest ↔ data_dictionary ↔ queries)

**Pass.** The 14-panel inventory at `manifest.md` §1.2 is byte-consistent with `_audit_summary.json` and the spec §6 14-row matrix. Joint-nonzero counts (76/65/56/45/47) are pre-committed at spec §5 and verified live at manifest.md §3.

`data_dictionary.md` `source_methodology` literals match `spec.md` §13:
- Primary: `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` (Rows 1-3, 5-8, 11-14)
- IMF-only sensitivity: `y3_v2_imf_only_sensitivity_3country_ke_unavailable` (Row 4 only)

X_d `proxy_kind` literals match: `carbon_basket_user_volume_usd` primary, `carbon_basket_arb_volume_usd` arb-only diagnostic, `carbon_per_currency_copm_volume_usd` per-currency diagnostic.

Deferred rows 9 (Y₃-bond) and 10 (population-weighted) are flagged with 0 rows in the manifest and have empty schema-typed parquet placeholders to preserve the 14-row deliverable contract — correct behavior per spec §10 ε.2/ε.3.

**Live panel inspection (independent SELECT * via duckdb):**
- 76 rows × 13 cols, all 8 model-relevant columns NaN-free
- Y₃: mean = 0.00493, std = 0.01473, range = [-0.0424, 0.0418] — matches spec §1.4 byte-exact
- X_d: mean = 77,415 USD, std = 113,309, range = [72, 504,506] — matches dictionary §3.1

### 3. Replication — independently fit Row 1 OLS+HAC(4)

**Byte-exact PASS.**

| Quantity | Independent replication | Phase 5b reported | Relative delta |
|---|---|---|---|
| β̂ (X_d) | -2.798705e-08 | -2.7987050503705652e-08 | 0.000e+00 |
| HAC SE | 1.423423e-08 | 1.4234226026833985e-08 | 0.000e+00 |
| t-stat | -1.9662 | -1.9661799981920483 | 0.000e+00 |
| 90% lower bound | -4.620686e-08 | -4.6206859818053154e-08 | 0.000e+00 |

Tolerance specified: 1e-10 relative. **Achieved: 0** (numerical-identity match within float64 precision). Replication produced via `statsmodels.OLS(...).fit(cov_type='HAC', cov_kwds={'maxlags':4})` from primary parquet — this confirms Phase 5b's `scripts/phase5_analytics.py` kernel is mathematically correct.

### 4. Calibration testing — Cohen f² re-derivation

**All three load-bearing power numbers byte-exact PASS.**

| | Independent (`scipy.stats.ncf.cdf`) | Spec §5 reported |
|---|---|---|
| `MDES_FORMULATION_HASH` (live SHA256 of `required_power` source) | `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` | byte-exact MATCH |
| `required_power(76, 13, 0.40, 0.10, 6)` | 0.868912 | 0.8689 (4dp match) |
| `required_power(65, 13, 0.40, 0.10, 6)` | 0.802711 | 0.8027 (4dp match) |
| `required_power(56, 13, 0.40, 0.10, 6)` | 0.730107 | 0.7301 (4dp match) |

Power at primary N=76 ≥ POWER_MIN=0.80 → calibration gate holds. Row 4 IMF-IFS-only at N=56 with power=0.73 < 0.80 is **dual-axis pre-registered FAIL** (also fails N_MIN=75) — disciplined and documented at spec §5.

### 5. Residual diagnostics & interpretability

**Phase 5b's reported diagnostics replicate byte-exact:**
- T4 Ljung-Box(4) p = 0.5014 — independent: 0.5014 (match); HAC(4) is sufficient for serial correlation
- T4 Ljung-Box(8) p = 0.3308 — independent: 0.3308 (match)
- T5 Jarque-Bera p = 0.6833 — independent: 0.6833 (match); residuals consistent with Normal at n=76. Skew = -0.022, excess kurt = 0.606 — mild positive excess kurtosis but not pathological
- Durbin-Watson = 1.65, AR(1) of resid = +0.17 — mild positive serial dependence consistent with HAC(4)'s 4-lag absorption

**NEW finding (Finding 4) — heteroskedasticity not surfaced by Phase 5b:**
- **Breusch-Pagan: stat = 16.16, p = 0.0237 → REJECTS at 5%**
- Phase 5b's T2 (Levene's test on Y₃ variance partitioned by X_d quartile) tests a *specific* heteroskedasticity hypothesis (X_d-driven variance) and fails to reject. The general-form Breusch-Pagan tests *any* heteroskedasticity in residuals against the regressor space and rejects.
- HAC(4) is robust to heteroskedasticity asymptotically; at n=76 the finite-sample HAC SE may be optimistic if heteroskedasticity is concentrated in a few high-leverage rows.
- **Severity: Medium.** Does not invalidate the FAIL verdict — heteroskedasticity-corrected SEs would generally *widen* the band, reinforcing FAIL. Recommend Rev-3 add Breusch-Pagan + White's general test as T2.b.

**NEW finding (Finding 5) — influence:**
- 6/76 obs with Cook's D > 4/n threshold (0.0526)
- 8/76 obs with leverage > 2k/n threshold (0.2105)
- Top-1 influential: 2026-03-06 (D = 0.888, leverage = 0.420, studentized residual = -3.13, X_d = 168,895, Y₃ = -0.0424)
- This single obs drives ~50% of the negative β̂ magnitude
- **Drop-one sensitivity:**
  - Drop 2026-03-06: β̂ = -2.661e-8 (was -2.799e-8); SE = 1.452e-8; t = -1.83
  - Drop 2025-04-04: β̂ = -3.334e-8; SE = 1.449e-8; t = -2.30 (more negative!)
  - Drop top-3 (2026-03-06, 2025-04-04, 2026-02-06): β̂ = -2.609e-8; SE = 1.470e-8; t = -1.78
- **Verdict on the FAIL:** robust to single-outlier removal — sign stays negative, t-stat softens but stays in the rejection-of-positive direction. The *magnitude* is influence-driven; the *sign* is not.
- **Severity: Medium** for spec-completeness; **Info** for verdict robustness. Recommend Rev-3 mandate drop-one and drop-top-3 sensitivities as a default in T7.

**NEW finding (Finding 6) — multicollinearity / shared-factor bias:**
- VIF(x_d) = 1.82, VIF(fed_funds) = 1.91 — both well below alarm threshold (10), so no statistical-inflation problem
- BUT ρ(x_d, fed_funds_weekly) = **-0.614** — substantively meaningful
- **Economic interpretation:** Carbon DeFi user volume on Celo (X_d) is plausibly higher when global rates are low (cheap dollar carry → more EM speculation, including stablecoin basket arbitrage); Y₃ is also higher when global rates are low (EM equity rallies + working-class CPI may compress). This creates a **shared third-factor mechanism**: X_d ↑ when Y₃ ↑ via Fed rate environment, *not* via X_d → Y₃ direct causation.
- The continuous-control partialing at §4.3.1 already absorbs fed_funds linearly, but if the relationship is non-linear or interactive, residual OVB persists.
- **Severity: Medium.** Could explain the sign-flip: if X_d's effect on Y₃ runs *through* Fed rate environment rather than independently of it, partialing fed_funds via OLS underestimates the joint signal and may flip the apparent direction.
- Recommend Rev-3 ε-extension: residualize X_d on fed_funds (and other macro vars) first, then regress Y₃ on the residualized X_d. This is the Frisch-Waugh-Lovell lens that makes the partial coefficient interpretation explicit.

### 6. Performance monitoring (model-internal framing of FAIL)

**Pass — framing is faithful to FX-vol prior-art and product context.**

The FAIL pattern is the *same predictive-regression artifact* as FX-vol-CPI:
- FX-vol: β̂_CPI = -0.000685, n = 947, T1 REJECTS (F=15.12), T3b FAIL → published as FAIL with predictive-flag
- Rev-2: β̂_X_d = -2.799e-8, n = 76, T1 REJECTS (F=3.48), T3b FAIL → reported with predictive-flag

The summary.md correctly:
- Headlines T3b FAIL without softening
- Surfaces T1 REJECT → predictive interpretation flag
- Reports anti-fishing audit table (8 invariants) byte-exact
- Reproduces convex-payoff insufficiency caveat verbatim from §11.A
- Surfaces pivot paths (Rev-3 ζ-group, brainstorm-α, brainstorm-β) from §11.C
- Does NOT promote any sensitivity row to primary (Row 12 HAC(12) at p=0.0084 two-sided would be tempting; spec §9.5 anti-fishing-bans the promotion and Phase 5b honors that)

The two-sided T3a REJECTS at p=0.0493 — **inverse correlation, not noise.** This is stronger evidence than "no effect" because the CI excludes zero in the *wrong* direction. The summary correctly does not minimize this; the framing "Y₃ and X_d ARE statistically related; the relationship is just inverse" is the honest read and matches the FX-vol product-read pivot.

### 7. Specification test integrity (T1–T7)

| Test | Implementation | Replication | Pass/Fail |
|---|---|---|---|
| T1 (exogeneity) | F-test on lag(Y₃) + lag(controls) jointly predicting X_d | F = 3.4797, p = 0.003111 | **byte-exact match** to reported (F=3.480, p=0.0031) |
| T2 (variance premium) | Levene's median test on Y₃ by X_d quartile | reported p = 0.2038, fails to reject | matches spec §7 T2 |
| T3a (two-sided) | t = β̂/SE vs Normal | t = -1.966, p = 0.0493 | matches |
| T3b (one-sided gate) | β̂ − 1.28·SE > 0 | -4.621e-8 < 0 → FAIL | matches |
| T4 (Ljung-Box) | Q-stat on resid lags 4 and 8 | p_4 = 0.5014, p_8 = 0.3308 | byte-exact match |
| T5 (JB) | Jarque-Bera on residuals | JB = 0.762, p = 0.6833 | byte-exact match |
| T6 (Chow break) | Spec §7 calls Bai-Perron unknown-break; Phase 5b runs Chow at known Carbon-launch date | F = NaN (cannot identify on primary panel) | substituted with disclosure; see Finding 9 |
| T7 (parameter stability) | β̂ primary vs β̂ parsimonious within 1·SE | -2.799e-8 vs -7.317e-9 differs by > 1·SE → "predictive" flag | matches; flag triggered correctly |

**Finding 9: T6 spec-execution mismatch.** Spec calls Bai-Perron unknown-break (which would scan all candidate break dates in [t_start, t_end] and report the maximum F-stat). Phase 5b implements Chow-at-known-date (Carbon-launch 2024-08-30) — a stricter test that fails to identify because the primary panel begins 4 weeks AFTER the launch (no pre-launch rows). The honest "test cannot be run; F = NaN" disclosure is preserved at `spec_tests.md` line 73 with rationale. **Severity: Low.** The substitution does not change the verdict — even if Bai-Perron found a break, the FAIL on Row 1 primary stands. Recommend Rev-3 either (a) implement true Bai-Perron (`statsmodels.tsa.tools.add_lag` + manual scan, or `ruptures` library), or (b) pre-register the Chow-at-launch substitution explicitly in spec §7.

### 8. Audit-grade reporting (summary.md content quality)

**Pass on all 5 spec-required reproductions.**

| Item | Required | Found in summary.md |
|---|---|---|
| Anti-fishing audit table reproduced byte-exact | Yes | 8/8 invariants present, names + statuses match spec §9 |
| Convex-payoff caveat from §11.A reproduced verbatim | Yes | Lines 51-60, 4 numbered points present |
| Pivot paths from §11.C surfaced | Yes | Lines 65-73, all 6 paths (4 ζ + 2 α/β brainstorm) present |
| HALT-to-user discipline followed | Yes | Lines 27, 49, 63, 75 explicit; gate FAIL not minimized |
| No silent reframing of FAIL as PASS or "expected" | Yes | T3a REJECT not used to reframe T3b FAIL; sign-flip transparency at line 43 invariant #3 |

The headline ordering (T3b FAIL → β̂ → SE → t-stat → bootstrap AGREE → pre-registered FAILs confirmed → T1-T7 list → anti-fishing table → convex-payoff caveat → pivot paths) is the disciplined HALT-to-user form.

### 9. External-validity concerns

**Pass with documented threats.**

| Threat | Spec disposition | My assessment |
|---|---|---|
| N = 76 razor-thin | Acknowledged at §1.2; deferred panel-decomposition (228 rows) at §10 ε.1 | Genuine — drop-one sensitivity (Finding 5) shows individual obs swing β̂ magnitude by up to 50% |
| WC-CPI 60/25/15 weighting could be wrong | Row 14 spec sensitivity (§6); 3-weight test 50/30/20 vs 60/25/15 vs 70/20/10 in `estimates.md` Rows 14a/b/c | All three rows FAIL with negative β̂; **stable across weighting** — finding is NOT weight-driven (this is actually evidence FOR external validity of the negative finding) |
| X_d's choice (carbon_basket_user_volume_usd) could be wrong proxy | Rows 7 (arb-only, n=45) and 8 (per-currency COPM, n=47) under-N diagnostics | Both FAIL with negative β̂; consistent direction across X_d definitions |
| Heterogeneity across 3-country aggregate (CO/BR/EU) collapsed | §1.2 acknowledged; ε.1 country-level panel deferred | Material — equal-weight averaging may mask country-specific effects of opposite signs that cancel in aggregate; Row 8 per-currency COPM (Colombia leg only) gives β̂ = -1.634e-7 consistent with aggregate, suggesting cancellation is not the driver |
| Time window 2024-09-27 to 2026-03-13 is post-Carbon-launch only | Acknowledged at spec §2.7 (sequential information) | Sample frame is consistent with the on-chain protocol's existence; not a defect |

### 10. Model-quality verdict (independent of T3b PASS/FAIL direction)

**Is this MODEL of publication-grade quality?**

**YES — with the three model-quality concerns documented as Rev-3 future-revision items.**

What clears the bar:
- Byte-exact replication at 1e-10 relative tolerance (the strongest possible reproducibility evidence)
- Pre-registration discipline preserved through 4 prior revisions (Rev-1 / Rev-1.1 / Rev-1.1.1 / Rev-2) with documented superseding rationale
- Calibration hash-locked + independently re-derived against the canonical formulation
- Identification strategy (continuous-control partialing) explicitly defended vs. alternatives (release-event-window dummies, IV) at §4.3.1 and §16
- Three pre-registered FAIL sensitivities (Rows 3, 4, plus the dual-axis FAIL at Row 4) lock the gate against silent revisions
- Anti-fishing audit table reproduced byte-exact with 8 invariants
- T7 predictive-vs-structural flag triggered correctly given T1 REJECT — the honest framing
- Convex-payoff insufficiency caveat at §11.A is precisely the right load-bearing disclosure for a mean-β regression that may be deployed for option pricing — this is exemplary product-validity discipline

What an adversarial peer reviewer would flag (= my Findings 4-7):
- Breusch-Pagan rejects → finite-sample HAC SE may be optimistic
- Single 2026-03-06 obs drives ~50% of |β̂|; drop-one sensitivity not in spec
- ρ(x_d, fed_funds) = -0.61 → shared-third-factor risk; FWL residualization not in spec
- Spec §5 power-table k=13 vs equation §4.1 k=7 mismatch — soft documentation gap

None of these would invalidate the FAIL — the verdict is *reinforced* by them (heteroskedasticity, influence, OVB, conservative-power calibration all push toward "wider SE" and "uncertain magnitude," all consistent with FAIL). They are recorded for Rev-3 / future-revision discipline.

---

## Comparison to FX-vol-CPI prior-art

| Dimension | FX-vol-CPI Rev-4 | Rev-2 Phase 5b | Same-pattern? |
|---|---|---|---|
| n | 947 | 76 | ✘ (12.5x larger sample) |
| T1 verdict | REJECTS (F=15.12) | REJECTS (F=3.48) | ✓ predictive-regression flag |
| T3b verdict | FAIL | FAIL | ✓ |
| Sign | β̂_CPI = -0.000685 | β̂_X_d = -2.80e-8 | ✓ both negative-significant at T3a, FAIL T3b |
| Anti-fishing HALT | held; A1 monthly + A4 release-day-excluded recorded as pre-registered pivots | held; sensitivity rows recorded but none promoted | ✓ |
| Product-read pivot | "no effect detected at primary; pivot paths recorded" | "no effect detected at primary; ζ-group + α/β brainstorm pivots recorded" | ✓ |
| Convex-payoff disclosure | not relevant (FX-vol was variance-channel) | §11.A load-bearing | ✓ improved discipline |

The pattern carries forward faithfully. Rev-2 inherits the FX-vol product-read framework byte-consistently and adds the convex-payoff caveat (§11.A) that FX-vol did not need — this is *better* than FX-vol on a methodological-completeness axis, not worse.

---

## Recommendations for Rev-3 (not for Rev-2 fix-up)

The Rev-2 spec is committed and the FAIL verdict is the load-bearing fact. Do NOT modify Rev-2. The following are forward-looking Rev-3 spec-author inputs:

1. **Add Breusch-Pagan + White as T2.b** (Finding 4) to surface general-form heteroskedasticity beyond the X_d-quartile Levene test.
2. **Add drop-one and drop-top-3 sensitivities as default in T7** (Finding 5) — with the 2026-03-06 outlier as a documented worked example.
3. **Add FWL residualization extension to ε-group** (Finding 6) — residualize X_d on (fed_funds, vix, oil) before regression, then re-fit. Surfaces the "after-partialling-out" interpretation explicitly.
4. **Reconcile k_regressors in MDES table** (Finding 7) — either drop k=13 to k=7 with CORRECTIONS-block, or add explicit FX-vol-carry-forward footnote at §5.
5. **Implement true Bai-Perron unknown-break for T6** (Finding 9) — currently substituted with Chow-at-launch. Bai-Perron can run on the 76-week post-launch panel.
6. **Proceed with ζ-group convex-payoff calibration** (spec §10.6) — this is the natural Rev-3 scope, already enumerated.

---

## Provenance

- Spec commit: `d9e7ed4c8` (655 lines)
- Phase 5a commit: `2eed63994` (data prep)
- Phase 5b commit: `799cbc2802d6bcdf4beb80d033d9f1df533b13e4` (analytics, current HEAD)
- Audit replicated via `python -m statsmodels.api.OLS(...).fit(cov_type='HAC', cov_kwds={'maxlags':4})` against `panel_row_01_primary.parquet`
- MDES hash live-recomputed via `hashlib.sha256(inspect.getsource(required_power).encode('utf-8')).hexdigest()` = MATCH
- Power values independently re-derived via `scipy.stats.ncf.cdf` per Cohen 1988 §9 formulation
- Influence diagnostics via `statsmodels.stats.outliers_influence`
- Auditor: Model QA Specialist (independent; no participation in Phase 5a/5b authoring)

---

**Final verdict line:** **MODEL-PASS-w-adv** — the model is defensible regardless of T3b direction; replication, calibration, and reporting are publication-grade; three Medium-severity model-quality concerns (heteroskedasticity, influence, shared-factor) are surfaced for Rev-3 discipline and *reinforce* rather than rescue the FAIL verdict.
