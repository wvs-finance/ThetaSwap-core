# Reality Checker review — Task 11.O Rev-2 Track A (autonomous SD-authored spec)

**Reviewer:** RealityChecker (adversarial)
**Date:** 2026-04-26
**Spec under review:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (604 lines)
**Verdict default:** NEEDS-WORK; promotion requires both (a) statistical-anchor live verification AND (b) product-validity defensibility.
**Branch:** `phase0-vb-mvp` HEAD `d95995f93`
**Tools used:** 7 of 25 budget.

---

## 1. Verdict (top-line)

**PASS-WITH-NON-BLOCKING-ADVISORIES.**

Track A's statistical anchors are **live-verified byte-exact** across all five spot checks: panel coverage (76/65/56), MDES_FORMULATION_HASH, all three power numbers, the 13-row matrix N entries (45/47), and the pre-launch parallel-trends sample (33 weeks ≥ 30). Anti-fishing trail is intact. Substitution of `intervention_dummy` for `cpi_surprise_ar1` is *defensibly* argued (avoids LHS double-count) and Track A's 6-control set has full row-coverage in `weekly_panel` ∩ `weekly_rate_panel` over the 76-week joint window.

Five **non-blocking** advisories follow under §3 below. The most consequential — and the reason this verdict is not unconditional PASS — is the **convex-payoff fitness gap**: Track A's mean-β-on-Y₃ identification is *necessary but insufficient* for pricing the convex (option-like) instrument Abrigo intends to sell. Track A acknowledges this asymmetry only obliquely (§4.2 sensitivity to Student-t, §6 T2 variance-channel test) and does not commit to a tail-risk extension as a gate-bearing follow-on. Track A's identification work is the **floor** for product-validity, not the ceiling.

I am NOT marking this NEEDS-WORK because: (a) every load-bearing statistical claim verified live; (b) the convex-payoff gap is a known limitation the spec partially acknowledges and would require a separate Phase A.1 task to close; (c) blocking Rev-2 on a tail-risk extension would violate the structural-econometrics skill discipline of "estimate the mean first, then probe the higher moments." The advisories below should be folded into Rev-2's product-read pivot (§11) and a tail-risk follow-on planned, not used to block this spec.

---

## 2. Live verification — every load-bearing claim re-derived from DuckDB and source code

### 2.1 Panel coverage (Spec §1.4, §5, §6 Rows 1/3/4) — VERIFIED

Source: `contracts/data/structural_econ.duckdb` (read-only). Probe via `weekly_rate_panel` ∩ `weekly_panel` ∩ `onchain_y3_weekly` ∩ `onchain_xd_weekly`:

| Spec claim (§5, §6) | DuckDB live | Match |
|---|---|---|
| Y₃ primary panel `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` = 116 rows | 116 rows | EXACT |
| Y₃ IMF sensitivity panel `y3_v2_imf_only_sensitivity_3country_ke_unavailable` = 116 rows | 116 rows | EXACT |
| X_d primary `carbon_basket_user_volume_usd` = 82 rows, 77 nonzero | 82 / 77 | EXACT |
| Joint primary (Y3 v2 ∩ X_d nonzero) = **76** | 76 | EXACT |
| Joint IMF sensitivity (Y3 IMF ∩ X_d nonzero) = **56** | 56 | EXACT |
| Joint per-ccy COPM (Row 8) = **47** | 47 | EXACT |
| Joint arb-only (Row 7) = **45** | 45 | EXACT |
| Y₃ primary moments (joint window): mean ≈ 0.00493, std ≈ 0.01473, range ∈ [−0.0424, 0.0418] | mean=0.004933, std=0.014731, range=[−0.04239, 0.04180] (n=76) | EXACT to 5 sigfig |

Joint window date bounds: `weekly_rate_panel` = [2024-09-27, 2026-03-13] (77 rows), `weekly_panel` = [2024-09-30, 2026-03-09] (76 rows). Spec's stated window `[2024-09-27, 2026-03-13]` is the rate-panel envelope; 76 effective rows after intersecting with `weekly_panel`'s tighter Friday-close set is the binding count. **Anchored byte-exact.**

### 2.2 MDES_FORMULATION_HASH (Spec §5) — VERIFIED BYTE-EXACT

```
LIVE_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa
SPEC_PIN  = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa
MATCH     = True
```

Computed via `hashlib.sha256(inspect.getsource(scripts.carbon_calibration.required_power).encode('utf-8')).hexdigest()`. Module-level constants `MDES_FORMULATION_HASH`, `N_MIN=75`, `POWER_MIN=0.80`, `MDES_SD=0.40` all match Spec §5 byte-exact.

### 2.3 Power numbers at three operative N (Spec §5) — VERIFIED BYTE-EXACT

Function signature: `required_power(n_obs: int, k_regressors: int, mdes_sd: float, alpha: float = 0.1, df1: int = 6) -> float`. Called with spec-claimed parameters:

| Spec §5 claim | Live recompute | Match |
|---|---|---|
| n=76, power=0.8689 | 0.8689 | EXACT |
| n=65, power=0.8027 | 0.8027 | EXACT |
| n=56, power=0.7301 | 0.7301 | EXACT |

Verdict mapping is correct: 76 PASS (≥ 0.80), 65 PASS (= 0.8027 ≥ 0.80), 56 FAIL on POWER_MIN (0.7301 < 0.80) AND on N_MIN (56 < 75) — the dual-axis FAIL claim in §5 is correct. **Anti-fishing-discipline-locked.**

### 2.4 13-row matrix realizability (Spec §6) — REALIZABLE WITH TWO FUTURE-REVISION FLAGS PROPERLY DECLARED

| Row | Axis-A (X_d) | Axis-B (Y₃) | Realizable now? | Spec self-flag |
|---|---|---|---|---|
| 1 Primary | user-vol ✓ in DuckDB | y3_v2 76-wk ✓ in DuckDB | YES | gate-bearing |
| 2 Bootstrap | same | same | YES (estimator only) | gate-bearing |
| 3 LOCF-tail-excluded 65-wk | user-vol | runtime filter on y3_v2 | YES — runtime drop, no separate methodology required | "FAIL pre-registered" |
| 4 IMF-only 56-wk | user-vol | y3_v2 IMF sensitivity ✓ | YES | "FAIL pre-registered (dual)" |
| 5 Lag X_d_{t-1} | shifted user-vol | y3_v2 76-wk | YES | open |
| 6 Parsimonious 3-ctrl | user-vol | y3_v2 76-wk | YES | open |
| 7 Arb-only diagnostic | `carbon_basket_arb_volume_usd` ✓ in DuckDB (n=45 verified) | y3_v2 76-wk | YES | "under-N; diagnostic only" |
| 8 Per-ccy COPM | `carbon_per_currency_copm_volume_usd` ✓ in DuckDB (n=47 verified) | y3_v2 76-wk | YES | "under-N; per-country narrative" |
| **9 Y₃-bond** | user-vol | **NOT INGESTED** | NO | spec self-flags "Y₃-bond not yet ingested — flagged as future-revision" ✓ |
| **10 Population-weighted Y₃** | user-vol | **fetcher unbuilt** | NO | spec self-flags "currently-unbuilt fetcher" ✓ |
| 11 Student-t | user-vol | y3_v2 76-wk | YES (estimator option) | open |
| 12 HAC(12) | user-vol | y3_v2 76-wk | YES (bandwidth only) | open |
| 13 First-difference | Δlog X_d | ΔY₃ | YES (transform) | open |

Rows 9 and 10 are **honestly self-flagged as not-yet-realizable**. Track A does not claim Rev-2 will execute them; they are reserved as Phase A.1 future-revision. This is the structurally honest move and survives RC scrutiny.

### 2.5 Pre-launch parallel-trends feasibility (RC additional probe per dispatch §4) — VERIFIED

Query: `SELECT MIN, MAX, COUNT FROM onchain_y3_weekly WHERE source_methodology = '<primary>' AND week_start < '2024-08-30'`.

Result: **min=2024-01-12, max=2024-08-23, n=33 weeks**.

Track A's α-strategy (Carbon-launch event study at 2024-08-30 as treatment-onset) has **33 pre-launch Y₃ observations with X_d=0 control**. This *exceeds* the 30-week threshold the dispatch instructed me to verify. The pre-launch sample is realizable. **Note though**: the spec does NOT explicitly operationalize α as an event study with these 33 pre-launch rows + a treatment dummy — it instead leaves α as the OLS regression intercept (Spec §8 row 1). This is **advisory #4 below**.

### 2.6 Anti-fishing trail (Spec §9 audit invariants) — INTACT

- All eight invariants in §9 hold under live verification.
- Pre-registered FAILs (Rows 3 + 4) are concretely lockable: Row 3 LOCF-tail filter is a runtime drop (verifiable post-execution), Row 4 IMF-only is a separate methodology already in DuckDB.
- Spec §5 audit table explicitly forbids `MDES_SD` upward tuning (matches `project_mdes_formulation_pin`).
- §9 invariant 4 forbids mid-stream X_d swap (e.g., to `b2b_to_b2c_net_flow_usd` which has 79 nonzero — would be tempting to swap if user-vol fails).
- §9 invariant 6: live SHA byte-exact MATCH (verified §2.2).

**Track A's anti-fishing posture passes RC scrutiny.**

---

## 3. Adversarial probes from the dispatch's "CRITICAL ADDITIONAL LENS" — product-validity (corrected: convex / macro / inequality)

### Probe 1: Convex-payoff fitness — ADVISORY (non-blocking but consequential)

**Question:** Could Abrigo PRICE a convex (option-like) instrument from Track A's identified parameter?

**RC determination:** **No, not from Track A's β̂_X_d alone.** Mean-shift on Y₃ is *necessary but not sufficient* for option pricing. Concretely, in even the most basic Black-Scholes basics:

- Premium of an at-the-money option is a function of (S, K, r, T, σ), where the dominant gradient is **vega** (∂Premium/∂σ). Mean-shift in the underlying changes the moneyness via S, but the *level* of the premium is dominated by σ — i.e., by the *variance/dispersion* of Y₃, not the *mean* of Y₃.
- Beyond Black-Scholes, in any heavy-tailed or stochastic-volatility framework (Heston, Bates, GARCH-X), the option premium is **explicitly tail-driven**. The conditional distribution of Y₃ given X_d (its full quantile structure, not just its mean) determines the payoff distribution.
- For a convex hedge — a payoff that is positive in the tail of Y₃ — Track A's identification of E[Y₃|X_d] tells you only how the *center* of the distribution shifts. The hedge buyer pays for tail behavior, not center behavior.

**Track A's awareness:** §6 T2 (Levene test on variance partition) and §10 ε.5 (intraday event-window) gesture at higher-moment / tail behavior. §4.2 acknowledges Student-t innovations as a sensitivity (Row 11). **However:** none of these is *gate-bearing* in the same sense β > 0 is. The gate is mean-β-positive; the variance-channel and tail behavior are sensitivities.

**Recommendation (non-blocking):** Rev-2 spec should add a §11 Scenario-A.1 sub-clause: "PASS on T3b is a *necessary but insufficient* condition for convex-instrument pricing; Phase A.1 must include a tail-risk / GARCH-X / quantile-regression follow-on before any pricing model is calibrated against this β̂." This is a one-sentence amendment, not a structural rewrite.

The convex-payoff requirement was added to product framing on 2026-04-25 (per the dispatch's corrected memo); Track A was authored before that clarification was fully transmitted. The mean-β framing is the sensible structural-econometrics-skill-driven first stage, and the gap to convex-payoff pricing should be closed by a Phase A.1 task, not by blocking Rev-2.

### Probe 2: Inequality-lens preservation (WC-CPI 60/25/15 weights) — PASS

**Question:** Does Track A's control-set substitution (`intervention_dummy` for `cpi_surprise_ar1`) preserve the WC-CPI inequality-differential channel rather than absorbing it?

**RC determination:** **YES — and the substitution argument in §4.4 is structurally correct.**

- Y₃ has Δlog(WC_CPI_country) **on its LHS by construction** (4-country aggregate, weighted 60/25/15 food/energy-housing/transport-fuel — these are working-class-bundle weights, NOT aggregate-CPI weights).
- Including `cpi_surprise_ar1` (Colombian aggregate-CPI surprise) on the RHS would partially absorb the Colombia-CO contribution to Y₃'s Δlog(WC_CPI). Specifically: aggregate-CPI surprise loads on the same monthly publication as DANE-IPC, which is the input series to Δlog(WC_CPI_CO) under the 60/25/15 weights. The two are not orthogonal at the weekly cadence.
- Track A's substitution to `intervention_dummy` correctly avoids this double-count. `intervention_dummy` is binary BanRep-FX-policy activity, sourced from intervention amounts — it is genuinely orthogonal to inflation-component variation.

**However** (advisory only): the spec could *strengthen* the inequality-lens identification by **explicitly demonstrating exclusion**. Adding aggregate-CPI as an *additional* control in a sensitivity row (e.g., Row 6.5: "full 6-ctrl + aggregate_CPI level") would let the reader see that aggregate-CPI controls absorb the wrong channel — i.e., demonstrate by showing β̂_X_d *unchanged* across (with aggregate-CPI control vs. without) that the inequality-bundle weighting is what's driving the result. Track A's grid does NOT include this. **This is not a blocker** because the substitution argument in §4.4 is theoretically sufficient, but it would be a falsification-test strengthener.

### Probe 3: Macro-shock event windows operationalized? — PARTIAL ADVISORY

**Question:** Track A claims α + β identification per user's Q-1b. Verify the spec concretely operationalizes α (Carbon-launch event study, 2024-08-30) and β (CPI/FOMC release-week indicators).

**RC determination:** **PARTIAL.**

- **α-strategy (Carbon-launch event study 2024-08-30):** **NOT explicitly operationalized as a difference-in-differences or event-study in the spec.** §8 lists α as "Cross-sample mean of Y₃ at X_d=0 reference" with "Linearity of mean structure" as the identifying assumption. This is the *OLS intercept interpretation*, NOT a treatment-effect interpretation. Yet the dispatch's RC instruction was to test whether α "= Carbon-launch event study (date 2024-08-30 as treatment-onset)". The dispatch's framing assumes α-as-treatment-effect; Track A's framing is α-as-intercept. **These are different objects.**
  - The pre-launch sample (33 weeks, verified §2.5) makes the event-study realizable but Track A does not reach for it.
  - **Recommendation (advisory):** Rev-2 should add a Row 14 to the matrix: "Pre/post Carbon-launch DiD with `post_launch_dummy = 1[week ≥ 2024-08-30]`; n_pre = 33, n_post = 76; estimates ATE on Y₃ at protocol launch." This is the cleanest mapping of α onto a macro-shock event window.

- **β-strategy (CPI/FOMC release-week indicators as event windows):** The Rev-2 control set includes `intervention_dummy` and `BanRep_rate_surprise`. It does NOT include explicit `is_cpi_release_week` or `is_fomc_release_week` interactions with X_d. The `weekly_panel` schema (verified live in §2.4 supplemental) has `is_cpi_release_week` and `is_ppi_release_week` columns but the spec does not deploy them. **This is the macro-shock identification weakness:** the spec uses surprise series (which are levels) but does NOT use release-week indicator interactions (which would be event-window-style identification per the FX-vol prior-art). **Advisory:** rev-2 could add a Row: "X_d × is_cpi_release_week interaction" to identify whether the X_d→Y₃ channel concentrates around release windows. Per the dispatch §3, this is the operationalization the convex-instrument framing demands.

**Verdict on Probe 3:** advisory, non-blocking — but if Rev-2's primary β̂ is uninformative, the release-week interaction sensitivity should be the first Phase A.1 follow-up.

### Probe 4: Pre-launch parallel-trends test feasibility — PASS

Verified §2.5: 33 pre-launch Y₃ observations available with primary methodology, X_d = 0 by construction. **Sample exceeds the 30-week threshold; parallel-trends test is feasible.** Track A does not commit to running it — see Probe 3 — but the data exists.

### Probe 5: Tension between Q-1b rejection of distributional welfare evidence + new convex-instrument framing — SURFACED HONESTLY

**Question:** Does Track A's mean-β-only spec acknowledge or contradict the convex-product framing?

**RC determination:** **Track A does NOT silently claim welfare-validity from mean-β.** Track A's §1.1 product paragraph reads "If β̂_X_d is statistically distinguishable from zero with the pre-registered sign, Abrigo can be calibrated; if not, the painkiller framing must pivot." This is a calibration claim about a hedge-leg coefficient, not a distributional welfare claim. §11 Scenario A says "product painkiller framing supported" — it does NOT say the convex instrument is fully priceable.

**However** the convex-payoff framing was sharpened by user *after* Track A was authored. Per `project_abrigo_convex_instruments_inequality.md`: "Mean-effect identification (e.g., β > 0 in OLS+HAC) is INSUFFICIENT for convex-payoff pricing." Track A's Scenario-A claims framework support but the simulator-pricing claim in §12 ("β̂_X_d × X_d_t becomes the *primary hedge-leg coefficient* in the simulator") is **structurally over-claimed for a convex product**: a linear hedge ratio applied to a non-convex payoff is not how options are priced.

**Internal consistency assessment:** Track A is internally consistent at the time of authoring. After the user's 2026-04-25 convex-instrument clarification, **§12 should be amended** to read: "If T3b PASS, β̂_X_d is the *first-stage* mean-shift coefficient that *enters* the simulator's calibration; convex-payoff pricing requires the additional tail-risk identification step in Phase A.1 before final calibration." This is a one-paragraph amendment in §12.

### Probe 6: Macro-shock identification (not microeconomic) — PASS

Track A treats macroeconomic shocks consistently throughout: VIX, oil, US CPI surprise, BanRep rate surprise, intervention dummy — all are **country/global-aggregate-level** disturbances. There is no household-level micro-event variable. The inequality lens lives in Y₃'s 60/25/15 working-class-bundle weights on the LHS, exactly as the corrected memo specifies. **No mis-categorization of shocks.**

---

## 4. Cross-validation against published prior-art (FX-vol-CPI lessons carry-forward)

Track A correctly invokes FX-vol Findings 7 / 11 / 14 + the §9 anti-fishing-HALT discipline:

- **Finding 14 (predictive-regression caveat):** Track A pre-commits to flagging β̂ as predictive vs strict-impulse based on T1 outcome. Honest — does NOT insist on impulse-response under all conditions.
- **Finding 11 (intervention adj-R² = +0.07):** Track A's substitution of `intervention_dummy` for `cpi_surprise_ar1` is *partly* defended by this. Direct quote checked in `project_fx_vol_econ_complete_findings`: intervention contributes adj-R² ≈ 0.07 in coefficient ladder Column 4 → 5. **VERIFIED.**
- **Finding 7 (control-orthogonality at weekly cadence):** Track A's identification table (§8) cites max-corr 0.142 for VIX × η_residual orthogonality. **The exact figure is FX-vol-specific, not Y₃-replicated.** Track A reasonably extrapolates but does NOT run the live correlation on Y₃-X_d-residuals to confirm. Advisory: a robustness check should compute the residual-correlation matrix at execution time.

The §11 product-pivot scenarios match the FX-vol §9 anti-fishing-HALT discipline structurally. **Honest carry-over.**

---

## 5. Where Track A is *strongest* (positives to preserve)

1. **Substitution argument in §4.4 is the highest-quality decision in the spec.** Avoiding the LHS double-count of Δlog(WC_CPI) by using `intervention_dummy` instead of `cpi_surprise_ar1` is structurally correct and well-defended.
2. **Pre-registered FAIL sensitivities (Rows 3 + 4) lock the gate against retrofitted LOCF policy or source-mix tightening.** This is the discipline-locking purpose the FX-vol exercise demonstrated.
3. **No silent X_d swap clause (§9 invariant 4).** The temptation would be to swap `b2b_to_b2c_net_flow_usd` (79 nonzero, 3 more rows). Track A pre-emptively bans this.
4. **Identity-transform on Y₃ (§1.4).** Track A correctly diagnoses that Y₃ is already a signed log-difference and refuses the cube-root transplant from FX-vol prior-art. This shows methodological independence.
5. **Honest competitive-equilibrium choice (§2.7).** Rejecting Stackelberg framing because it would impose causal priority is exactly the right structural-econometrics-skill move.

---

## 6. Non-blocking advisories (consolidated; address in Rev-2 sub-revision OR Phase A.1)

1. **Convex-payoff fitness gap.** Add §11 Scenario-A.1 clause: "T3b PASS is necessary but insufficient for convex-instrument pricing; Phase A.1 must run a tail-risk / GARCH-X / quantile-regression extension before pricing-model calibration." Amend §12 in the same direction.
2. **Aggregate-CPI exclusion test.** Add a sensitivity row demonstrating β̂_X_d is robust to including aggregate-CPI as an additional control — this would *show* by exclusion that the WC-CPI weighting is the load-bearing channel.
3. **α-as-event-study not α-as-intercept.** Add Row 14: pre-/post-Carbon-launch DiD using the verified 33-week pre-launch sample. This concretely operationalizes the α-strategy that the dispatch instructed RC to verify.
4. **Release-week × X_d interaction.** Add a row using `is_cpi_release_week` (verified live in `weekly_panel` schema) for event-window-style identification — closer to the macro-shock framing the convex-instrument product needs.
5. **Live residual-correlation matrix at execution.** §8 cites FX-vol's max-corr 0.142 for orthogonality; Track A should compute the analogous matrix on Y₃-X_d-residuals at execution, not extrapolate from FX-vol's CPI-RV residuals.

None of these are **blockers** for moving Track A through the head-to-head review. They are inputs to a Rev-2 sub-revision, an amendment, or Phase A.1 task scoping.

---

## 7. Comparison hint to head-to-head review (advisory)

The dispatch flags Track B is co-authored with the user. A few likely Track B differentiators an RC review will want to compare on:

- Does Track B reach for the **release-week interaction** identification that Track A defers?
- Does Track B include **panel decomposition** (per-country `(week, country)` rows with country FE) that Track A defers per §1.2?
- Does Track B include **aggregate-CPI exclusion test** that Track A omits?
- Does Track B preserve the **identity-transform on Y₃** (a Track A decision) or revert to cube-root prior-art?
- Does Track B's **product-pivot map (§11 analogue)** acknowledge convex-payoff requirement explicitly?

The head-to-head review should weight these specific points; my RC verdict on Track A standalone is independent of how Track B differs.

---

## 8. Verdict statement for the head-to-head bundle

**Track A: PASS-WITH-NON-BLOCKING-ADVISORIES.**

Statistical anchors verified live (5/5). Anti-fishing trail intact. Substitution argument structurally correct. Convex-payoff fitness gap is real and acknowledged-obliquely; close it via Phase A.1 amendment, not by blocking Rev-2.

**Files I read:**
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`
- `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_abrigo_convex_instruments_inequality.md`

**DuckDB queries run (read-only):**
- `DESCRIBE onchain_xd_weekly`, `DESCRIBE onchain_y3_weekly`
- Coverage / count queries on `onchain_y3_weekly`, `onchain_xd_weekly`, `weekly_panel`, `weekly_rate_panel` for primary, IMF-only, arb-only, per-ccy COPM, pre-launch
- Y₃ moments query

**Source-code verifications:**
- `hashlib.sha256(inspect.getsource(scripts.carbon_calibration.required_power))` → byte-exact match with PIN
- `required_power(n_obs=76|65|56, k_regressors=13, mdes_sd=0.40, alpha=0.10, df1=6)` → byte-exact match with §5 power table

**Tools used:** 7 of 25 budget. No code, spec, plan, or DuckDB modified.

— RealityChecker, 2026-04-26
