# Task 11.O Rev-2 Spec — Track A Code Reviewer Review (CORRECTED product framing)

**Date:** 2026-04-25 (corrected re-dispatch)
**Reviewer:** Code Reviewer agent
**Subject:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (604 lines, uncommitted)
**Track A status:** Re-dispatched with **CORRECTED** product memo `project_abrigo_convex_instruments_inequality.md`. Prior review used the incorrect `_microshocks` framing and is superseded by this file in-place.
**Verdict:** **PASS-with-non-blocking-advisories (standard CR) + NEEDS-WORK (product-validity, convex-payoff gap)**

The spec is structurally sound, anti-fishing-clean, and implementation-ready as a *mean-β identification spec*. Against the **CORRECTED** product purpose — Abrigo sells **CONVEX (option-like) instruments hedging MACROECONOMIC shocks viewed through the INEQUALITY lens** — Track A:

- **PASSES** the macro-shock identification requirement: its six controls (VIX, oil, US_CPI_surprise, BanRep_rate_surprise, Fed_funds_weekly, intervention_dummy) ARE the macro-shock identifying variation. The substitution of `intervention_dummy` for `cpi_surprise_ar1` is *more defensible* under the corrected framing than under the prior incorrect "microshocks" framing.
- **PASSES** the inequality-lens preservation requirement: Y₃'s `Δlog(WC_CPI)` 60/25/15 working-class bundle weighting is preserved on the LHS by construction; controls do not absorb the labor-income-tied differential.
- **FAILS** the convex-payoff requirement: the spec produces a first-moment / mean-β parameter only. Convex-instrument pricing requires conditional-variance, conditional-quantile, or tail-response evidence that Track A explicitly does NOT estimate.

This last gap is the same gap the prior review flagged, but the *reasoning* now correctly anchors on macro-shocks-with-inequality-lens (not micro-shocks). The recommended disposition is unchanged: commit the spec as-is for the mean-β work it does well, add concrete future-revision pointers for the variance/quantile co-primary extension, and explicitly flag for the user that Track A's mean-β output cannot directly calibrate a convex instrument premium without further work.

---

## SECTION 1 — Standard CR findings

### 1.1 Anti-fishing invariants — PASS (byte-exact, live-verified)

§5 audit table verified line-by-line at memo-write time. Live recomputation against `contracts/scripts/carbon_calibration.py`:

```
LIVE_HASH 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa
PIN_HASH  4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa
MATCH True
N_MIN 75
POWER_MIN 0.8
MDES_SD 0.4
required_power(76,13,0.40) = 0.8689122648203158   →  spec §5 row "0.8689" ✓ byte-exact
required_power(65,13,0.40) = 0.8027109865163895   →  spec §5 row "0.8027" ✓ byte-exact
required_power(56,13,0.40) = 0.7301068449997878   →  spec §5 row "0.7301" ✓ byte-exact
```

| Invariant | Spec value | Match prior commits / live |
|---|---|---|
| `N_MIN` | 75 | PASS (`project_rev531_n_min_relaxation_path_alpha`) |
| `POWER_MIN` | 0.80 | PASS |
| `MDES_SD` | 0.40 | PASS |
| `MDES_FORMULATION_HASH` | `4940360d…cefa` | PASS (LIVE recompute matches) |
| Rev-4 `decision_hash` | `6a5f9d1b…443c` | PASS (verified at `nb1_panel_fingerprint.json:23`) |
| Y₃ primary literal | `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` | PASS (commit `c5cc9b66b`) |
| Y₃ IMF-IFS-only literal | `y3_v2_imf_only_sensitivity_3country_ke_unavailable` | PASS |
| X_d primary `proxy_kind` | `carbon_basket_user_volume_usd` | PASS |
| HAC truncation lag | 4 | PASS (Newey-West / Andrews 1991) |
| Bootstrap mean block | 4 weeks | PASS (matches HAC(4)) |
| α one-sided | 0.10 | PASS (Rev-4 standard) |
| df₁ | 6 | PASS (6 controls + 1 X_d − 1 constant) |

§9 anti-fishing audit trail (8 items) is comprehensive. Rule #4 ("no mid-stream X_d swap") explicitly bans the post-hoc 79-week-vs-76-week swap to `b2b_to_b2c_net_flow_usd`. This matches `feedback_pathological_halt_anti_fishing_checkpoint` discipline.

### 1.2 13-row resolution matrix — PASS-with-advisory

§6 matrix is concrete (5 axes labeled, 13 rows enumerated, gate-bearing rows locked, pre-committed verdicts named). The three pre-registered FAIL rows are explicit:

- Row 3 (LOCF-tail-excluded, n=65, FAIL on N_MIN by 10 weeks)
- Row 4 (IMF-IFS-only, n=56, dual-axis FAIL on N_MIN AND POWER_MIN — discipline-locking, not defect)
- Row 7 (arb-only diagnostic, n=45, "diagnostic only" — implicitly under-N)

🟡 **Advisory (non-blocking):** the user's dispatch wording "Three FAIL sensitivity rows pre-committed (76 / 65 / 56)" appears to misnumber. n=76 is the PRIMARY (gate-target, cannot pre-commit FAIL by definition); the actual pre-committed FAIL trio is n=65 (Row 3), n=56 (Row 4), and arguably n=45 (Row 7 arb-only). Track A's matrix is internally consistent; the user's "76" reference is most plausibly read as "n=76 primary alongside the two FAIL sensitivities" — the only interpretation that makes structural sense.

🟡 **Advisory (non-blocking):** Rows 9 ("Y₃-bond diagnostic" — TBD operative N) and 10 ("Population-weighted Y₃" — flagged as "currently-unbuilt fetcher in design doc §5") are listed in the matrix but are not currently runnable. The matrix should distinguish "runnable at Rev-2 commit" (rows 1-8, 11-13) from "deferred-future-revision-pointer" (rows 9-10) more sharply, or move 9-10 wholly into §10 ε-pointers. Mixing runnable and unbuildable rows in one matrix dilutes the operational clarity reviewers need at execution time.

### 1.3 Functional form preservation — PASS (byte-exact)

The asset-leg legacy equation in §0 is byte-exact:

```
Y_asset_leg_t = (Banrep_rate_t − Fed_funds_t)/52 + (TRM_t − TRM_{t-1})/TRM_{t-1}
```

Cross-reference: this appears as the per-country diagnostic input to Colombia's `copm_diff` rich-side, NOT as the gate target. The supersession banner (§0) is honest about Rev-1/1.1/1.1.1 retirement. No silent retconning.

The primary regression equation in §4.1 / §4.3 preserves the Rev-4 control-set shape (six controls + intercept + structural error) byte-exact except for the explicit `cpi_surprise_ar1 → intervention_dummy` substitution defended in §4.4. See §1.4 below for substitution audit.

### 1.4 Control-set substitution audit — PASS

Track A substitutes `cpi_surprise_ar1` (Rev-4 Decision #4) with `intervention_dummy` (Rev-4 Decision #9 form). Justification (§4.4):

1. Y₃ already contains `Δlog(WC_CPI)` directly on the LHS as part of its construction.
2. Re-including a Colombian CPI surprise on the RHS would double-count the Colombian inflation channel.
3. `intervention_dummy` is the orthogonal Colombian-policy shock not embedded in Y₃; FX-vol Finding 11 attributes adj-R² = +0.07 to it.

This is a **substantively defensible** substitution. The Rev-4 `decision_hash = 6a5f9d1b…` is preserved as a *referenced anchor* (nb1_panel_fingerprint.json:23), not as a constraint that the Rev-2 control set must match Rev-4 byte-exact. Rev-4's `cpi_surprise_ar1` was in service of an FX-vol LHS (RV^(1/3)) that did NOT contain WC-CPI; transplanting that control to a Y₃ LHS that DOES contain WC-CPI is the very double-counting Track A guards against.

🟢 **Note:** under the CORRECTED product framing (macro shocks viewed through inequality lens), this substitution is *more* defensible than under the prior incorrect "microshocks" framing — see §2.3 below.

### 1.5 No code in spec body — PASS

No Python source, no Solidity. The mathematical equation (§4.1, §4.3) is in display-math notation, not executable code, which `feedback_no_code_in_specs_or_plans` permits. The §5 audit-table verification text references `scripts.carbon_calibration.required_power(n, 13, 0.40)` as a *citation*, not an in-spec implementation — this is acceptable.

### 1.6 Cross-reference resolvability — PASS-with-advisory

Spot-checked references (sample, all live-resolved):
- `c5cc9b66b` — verified in prior memos ✓
- `2a0377057` — admitted-set fix-up, verified ✓
- `nb1_panel_fingerprint.json:23` — line-anchored citation; live file confirms `decision_hash` at line 23 byte-exact ✓
- `project_rev531_n_min_relaxation_path_alpha` — memory file present ✓
- `project_mdes_formulation_pin` — memory file present ✓
- `2026-04-25-y3-imf-only-sensitivity-comparison.md` — explicit path ✓
- `2026-04-25-y3-rev532-ingest-result.md` — explicit path ✓
- Plan §Task 11.O reference — verified in `2026-04-20-remittance-surprise-implementation.md` Step 2b body (LOCF-tail-excluded sensitivity matches byte-exact)

🟡 **Advisory (non-blocking):** §13 lists `weekly_panel` and `weekly_rate_panel` as Rev-4 / Task 11.M.6 sources but does not give a commit hash or fingerprint at memo-write time. If the panel mutates between spec-commit and Phase-5 consumption (e.g., new BanRep release, new FRED DFF refresh), the spec's "live" `n=76 joint` could shift. Recommendation: add a one-line "as-of" commit ref or fingerprint hash for `weekly_panel` and `weekly_rate_panel` at the §13 level so Phase-5 consumers can detect drift between spec-commit and execution.

### 1.7 Reiss-Wolak structural-econometrics application — PASS

Phase 0 (§1), Phase 1 (§2 economic model with all 7 components), Phase 2 (§3 stochastic decomposition into η, u, v), Phase 3 (§4 estimation, §6 specification-test grid, §7 spec tests T1-T7). Phase 4 (sensitivity, §10) is present though the operative grid is in §6 and §10 holds future-revision pointers ε.1–ε.5.

§2.7 equilibrium concept defense (competitive over Stackelberg/Nash) is principled and matches the structural-econ skill's discipline against pre-committing causal priority before T1 tests it.

§3.4 error decomposition `ε_t = η_t + u_t + v_t` with `E[η · X_d] = 0` as the testable identifying assumption (defended via T1 in §7) is the correct Reiss-Wolak structure.

§7 specification-test grid (T1 strict exogeneity / T2 announcement-window variance / T3a-b gate / T4 Ljung-Box / T5 JB / T6 Bai-Perron / T7 control-robustness) is comprehensive.

### 1.8 Pre-registered sign — PASS

§7 T3b locks **β > 0** (rising X_d → rising inequality differential). Rationale cites the inequality-hedge thesis: more cross-class capital flow on Carbon DeFi → more observable inequality pressure off-chain. The sign is non-trivial — it could plausibly go negative if Mento basket adoption REDUCES dollar-shortage pressure on the working class, in which case Y₃ would fall as X_d rises. Pre-committing the sign means a negative-significant β̂ would be reported as a **counter-finding** (per §9 rule #3) — consistent with FX-vol's discipline on β̂_CPI = −0.000685.

### 1.9 Standard-CR summary

| Category | Verdict |
|---|---|
| Anti-fishing invariants byte-exact | PASS (live-verified) |
| 13-row matrix concrete & pre-registered | PASS-with-advisory (rows 9-10 unrunnable; mixed with runnable) |
| Three FAIL sensitivities pre-committed | PASS (rows 3 n=65, 4 n=56; user's dispatch may have misnumbered "76" — see §1.2) |
| Functional form preserved byte-exact | PASS |
| Control-set substitution defensible | PASS (more defensible under corrected framing) |
| No code in spec body | PASS |
| Cross-references resolve | PASS (advisory: panel fingerprint missing) |
| Reiss-Wolak structure complete | PASS |

**Standard-CR verdict: PASS-with-non-blocking-advisories.**

---

## SECTION 2 — Product-validity findings (CORRECTED LENS)

The user's clarification (`project_abrigo_convex_instruments_inequality.md`) reframes Abrigo's product as **convex (option-like) instruments hedging MACROECONOMIC shocks viewed through the INEQUALITY lens**. This corrects the prior dispatch's "microeconomic shocks" wording — the shocks themselves ARE macro; the inequality lens lives in Y₃'s 60/25/15 working-class consumption bundle weighting.

This reframing changes some Section 2 conclusions of the prior review and preserves others. Each question is re-evaluated below against the **corrected** framing.

### 2.1 Question 1 — Does the spec produce a parameter Abrigo can use to price convex instruments?

🔴 **CRITICAL GAP — BLOCKER for product-validity (NOT BLOCKER for spec commit). UNCHANGED from prior review; corrected framing does not rescue this gap.**

Track A delivers `β̂_X_d` (mean OLS coefficient with HAC(4) SE) plus a 90% CI. This is a **first-moment / mean-effect** parameter. Convex-instrument pricing requires:

1. **Tail / extreme-quantile behavior:** What is `P(Y₃_t > q | X_d_t = x)` at high quantiles? Mean β does not characterize tails.
2. **Variance-amplification / ARCH-type response:** Does X_d shift the conditional variance σ²(Y₃ | X_d) in addition to the mean? An option premium is materially driven by variance, not just drift.
3. **Asymmetric / sign-dependent response:** Do high-X_d weeks vs low-X_d weeks have different *kurtosis*, not just different means?
4. **Hedge-payoff convexity:** A convex instrument's payoff is `max(Y₃ − K, 0)`-like; calibrating its premium needs the conditional distribution of Y₃, not just `E[Y₃ | X_d]`.

The spec produces NONE of these. Specifically:

- §1.4 fixes identity transform on Y₃ — appropriate for mean-β estimation, but identity OLS does not characterize tails.
- §6 row 11 (Student-t innovations) acknowledges fat tails exist but uses Student-t only for *β̂'s SE robustness*, not for *Y₃'s conditional distribution under X_d*.
- §6 row 12 (HAC(12)) is bandwidth robustness, not variance-channel.
- §7 T2 (Levene's test on variance partitioned by X_d quartile) is the ONLY component that touches a variance channel — and it is a *test* (REJECT yes/no), not a *parameter* the simulator can calibrate.
- §12 ("Connection to Layer-2 RAN simulator") explicitly says "β̂_X_d × X_d_t becomes the *primary hedge-leg coefficient*" — a linear hedge, not a convex one.

**Implication:** even if T3b PASSES (β̂ > 0 with 90% one-sided), Abrigo cannot price a convex option on Y₃ from this spec alone. The spec gives Abrigo a "linear hedge / forward-like" calibration, not an "option / convex" calibration.

**Why the corrected framing does not rescue this gap:** the inequality LENS lives in Y₃ (the LHS), but the convex PAYOFF lives in the response surface — i.e., how Y₃'s *distribution* (not just its mean) shifts as a function of X_d. Whether the shocks driving identification are micro or macro is irrelevant to whether the *response surface* is characterized by mean alone. Mean-β is insufficient for convex pricing under either framing.

**Recommended fix (deferred to future revision, not blocker for Rev-2 commit):**

1. Add a §10 ε.6 future-revision pointer for **GARCH(1,1)-X co-primary** — the FX-vol notebook already ran this as co-primary (Reconciliation T3b in the FX-vol Rev-4 spec). For Y₃ × X_d, GARCH(1,1)-X gives `σ²_t(Y₃ | X_d_{t-1}, σ²_{t-1})`, which is the variance-channel parameter convex pricing needs.
2. Add a §10 ε.7 future-revision pointer for **conditional quantile regression** (Koenker-Bassett 1978) at quantiles {0.10, 0.50, 0.90} of Y₃ on X_d. This characterizes the tail response.
3. Add an explicit acknowledgment in §12 ("Connection to simulator") that Rev-2's β̂_X_d is the **linear-hedge calibration only**; convex-instrument calibration requires a Rev-3 spec extension.

### 2.2 Question 2 — Are macroeconomic shocks the identifying variation?

🟢 **PASS (CORRECTED — UPGRADED from prior review's PARTIAL).**

Under the corrected framing, the shocks ARE macro: CPI release surprises, FOMC decisions, oil-price moves, FX shocks, growth-news, intervention-day events. Track A's six controls map onto the macro-shock identifying-variation requirement byte-clean:

| Track A control | Macro-shock category | Mapping |
|---|---|---|
| `VIX_avg` | Global risk-sentiment shock | ✓ |
| `oil_return` | Oil-price shock | ✓ |
| `US_CPI_surprise` | US monetary-policy shock (CPI release surprise channel) | ✓ |
| `BanRep_rate_surprise` | Colombian monetary-policy shock (event-study ΔIBR sum) | ✓ |
| `Fed_funds_weekly` | Global rate environment | ✓ |
| `intervention_dummy` | Colombian FX-policy shock (intervention-day binary) | ✓ |

All six are macro shocks. Track A's primary specification correctly captures macro-shock identifying variation. The spec also pre-registers **Carbon-protocol launch (2024-08-30+)** as the post-launch sample window (§1.4 / §6 T6 Bai-Perron) — implicitly the α-strategy "Carbon-launch event study" the user's Q-1b decision named.

🟡 **Advisory (non-blocking but user-resolvable):** the user's dispatch language "α (Carbon-launch event study) + β (CPI/FOMC release-event windows) per the user's Q-1b decision" suggests the macro-shock identification should be made *operationally explicit* in the spec — i.e., named release-day event windows for CPI/FOMC, not just average-control regressors. Track A's controls operationalize the *level* of the macro-shock variables (US_CPI_surprise as a continuous AR(1) residual, Fed_funds_weekly as the weekly mean rate), but it does NOT carve out **release-day event-window dummies** as separate identifying-variation artifacts.

The implication: Track A's spec identifies β̂_X_d using the *cumulative residual variation* in macro shocks. The α+β decomposition the user described would identify it using the *event-window jumps* around CPI/FOMC release days. These are not equivalent — event-window identification is usually narrower-bandwidth and more credibly causal, while continuous-control identification gives more sample but weaker exogeneity claims.

🟡 **Track A does NOT explicitly operationalize a "β-strategy CPI/FOMC release-event window" identification.** It treats the macro shocks as *continuous controls* in a partialing-out OLS, not as *event-window dummies* identifying a Δ_t-specific impulse. If the user's Q-1b decision was that the spec must use *release-event-window* identification (not partialing-out), Track A as written is mis-scoped. **Surface to user before commit (Section 3.3 below).**

### 2.3 Question 3 — Is the inequality lens (Y₃'s 60/25/15 WC-CPI weighting) preserved?

🟢 **PASS — preserved by construction; controls do not absorb the labor-income-tied differential.**

Y₃ is built from `R_equity + Δlog(WC_CPI)` per `project_y3_inequality_differential_design`, where WC_CPI uses 60/25/15 working-class bundle weights (food / energy-housing / transport-fuel). This is the inequality-focus marker. Track A's spec preserves this byte-exact:

- §1.3 defines `Δ_country = R_equity_country + Δlog(WC_CPI_country)` with the sign convention "rises when inequality widens via either rich-side gains OR working-class cost-of-living squeeze."
- §2.2 names "working-class consumers" as Actor 3, distinct from aggregate consumers; "equity-holding rich" as a separate actor class.
- §3.1 lists "working-class household-level basket-share heterogeneity that the pre-registered 60/25/15 weights average over" as an η component — explicitly acknowledging that even the 60/25/15 weighting is itself a coarsening, so the spec is honest about the lens it preserves.
- §4.4 substitution rationale: `cpi_surprise_ar1` is removed precisely to avoid double-counting the Colombian inflation channel that Y₃ already contains via `Δlog(WC_CPI_CO)`.

Critically, **the spec's controls do NOT include an aggregate-CPI surprise that would absorb the labor-income-tied differential.** The substitution `cpi_surprise_ar1 → intervention_dummy` (§4.4) actively guards against this absorption. Under the corrected framing, this substitution is the inequality-lens-preserving move: keeping `cpi_surprise_ar1` on the RHS would have partialed out the very working-class-CPI variation that makes Y₃ inequality-focused.

🟢 **Result:** the inequality lens is structurally preserved. The product-validity concern on this axis is fully resolved.

### 2.4 Question 4 — Is the convex-payoff (asymmetric / tail / variance-amplification) interpretation present anywhere?

🔴 **CRITICAL GAP — NEEDS-WORK for product-validity. UNCHANGED from prior review.**

The spec is purely linear / mean-effect / first-moment. The only places convexity-adjacent concepts appear:

1. §6 row 11 (Student-t) — heavy-tailed *innovations* (acknowledges Y₃ residual has fat tails), but does NOT estimate a convex *response*.
2. §7 T2 (Levene variance test) — partitions Y₃ variance by X_d quartile, but is a *yes/no test*, not a *parameter*.
3. §10 (sensitivity grid future-revision pointers ε.1–ε.5) — no GARCH-X, no quantile regression, no variance-channel co-primary.
4. §11 Scenario A (PASS) — "Abrigo can position as on-chain inequality-differential hedge, calibrated on β̂_X_d" — β̂ alone is the calibration. No tail-risk premium.
5. §12 ("Connection to simulator") — `β̂_X_d × X_d_t` is the hedge-leg, plain linear.

**Track A explicitly defers tail-risk to a future revision in only one indirect way:** §10 ε.5 ("Intraday event-window") which is a *cadence* extension, not a *moment-structure* extension. This is not a defensible deferral for convex pricing. The spec does NOT contain text like "Rev-3 will add GARCH-X / quantile regression for variance-channel transmission" — that pointer is missing.

**Concrete recommendation:** add §10 ε.6 — "GARCH-X co-primary for variance-channel transmission" — explicitly named, with a one-paragraph defense that the FX-vol notebook already ran this protocol successfully (FX-vol Rev-4 spec §3.5 reconciliation block). Add §10 ε.7 — "Conditional quantile regression at q ∈ {0.10, 0.50, 0.90}" — for tail characterization. The pointers should be concrete enough that downstream review can verify they point at real follow-up scope, not vapor.

### 2.5 Question 5 — Are the 13-row matrix entries product-decision-informative?

🟡 **MIXED — most rows are statistical, few are product-level.**

Row-by-row product-decision audit:

| Row | Product-decision relevance | Verdict |
|---|---|---|
| 1 Primary | YES — gate-target for "is the linear hedge calibrable" | High |
| 2 Bootstrap reconciliation | LOW — purely SE-method robustness | Statistical |
| 3 LOCF-tail-excluded FAIL | YES — locks against silent LOCF policy tuning (anti-fishing) | High (discipline) |
| 4 IMF-IFS-only FAIL | YES — locks against silent source-mix tuning | High (discipline) |
| 5 Lag (X_d_{t-1}) | YES — tells Abrigo whether hedge timing is contemporaneous or 1-week-ahead | Medium (timing) |
| 6 Parsimonious controls | LOW — collinearity diagnostic | Statistical |
| 7 Arb-only diagnostic | YES — tells Abrigo whether arb-volume contains the same signal | Medium (signal selection) |
| 8 Per-currency COPM | YES — tells Abrigo which Mento currency leg drives the signal (CO/BR/EU) | Medium (per-country) |
| 9 Y₃-bond diagnostic | UNRUNNABLE at Rev-2 — fetcher missing | N/A (deferred) |
| 10 Pop-weighted Y₃ | UNRUNNABLE — fetcher missing | N/A (deferred) |
| 11 Student-t | LOW — purely innovations robustness | Statistical |
| 12 HAC(12) | LOW — bandwidth robustness | Statistical |
| 13 First-differenced | LOW — stationarity robustness | Statistical |

**Score:** 5 high product-relevance (1, 3, 4, 5, 8) + 1 medium (7) + 5 low/statistical (2, 6, 11, 12, 13) + 2 unrunnable (9, 10).

**Advisory (non-blocking):** the matrix is **statistically thorough but product-thin** in the second half. Consider replacing rows 11/12/13 (purely SE / bandwidth / stationarity robustness) with rows that vary product-decision-relevant axes:

- A row that varies the **WC-CPI bundle weights** (e.g., 50/30/20 vs 60/25/15 vs 70/20/10) — product-relevant because it tells Abrigo how sensitive the calibration is to the underlying cost-of-living-bundle definition.
- A row that varies the country aggregation (CO-only vs BR-only vs equal-weight) — product-relevant because it tells Abrigo whether per-country contracts can be calibrated separately.
- A row that variance-decomposes the Y₃ rich-side (R_equity-only vs Δlog(WC_CPI)-only vs combined) — product-relevant because rich-side and working-class-side may need separate hedge legs.

🟡 **Under the CORRECTED framing**, the WC-CPI-weights-sensitivity row is the **most important** addition, because the inequality lens IS the 60/25/15 weighting; varying it tells Abrigo whether the calibration is robust to plausible alternative working-class-bundle definitions. Under the corrected framing this row migrates from "nice-to-have" to "first-class product-validity instrumentation."

### 2.6 Question 6 — Tension with user's Q-1b rejection of distributional welfare evidence

🟡 **TENSION REMAINS — but the corrected memo itself acknowledges it; salvageability path exists.**

Earlier in the session, the user rejected the distributional welfare option at Q-1b in favor of α+β identification ONLY. The corrected product memo (`project_abrigo_convex_instruments_inequality.md`) reframes the product as **convex / option-like / hedging macro shocks viewed through inequality lens** — and the memo explicitly states:

> *"Distributional welfare evidence (quantile shifts, variance amplification, lower-tail stabilization) — which the user earlier rejected at Q-1b — IS analytically required for the convex-instrument purpose. Future spec revisions may need to revisit this."*

So the corrected memo itself acknowledges the tension. The pivot is:

- **Q-1b (earlier in session):** distributional welfare REJECTED in favor of α+β.
- **Corrected product memo (now):** distributional welfare IS required for convex pricing — but as a Rev-3 / future-revision extension, NOT as a Rev-2 scope-extension.

**Resolution under corrected framing:** Track A's α+β identification is **salvageable** for Rev-2 commit on the explicit understanding that:

1. Rev-2 delivers the **mean-β linear-hedge calibration** (correctly scoped under Q-1b).
2. A separately-scoped Rev-3 (or a Phase-2b extension) delivers the **variance-channel / quantile / convex-pricing extension** — which IS the distributional-welfare evidence the corrected memo says is required.
3. The Q-1b decision's α+β-only ruling **applied to Rev-2 scope only**; it does not preclude Rev-3 from re-introducing distributional welfare as a separate spec.

🟡 **Recommendation:** add §10 ε.6 / ε.7 pointers (per §2.4 above) AND add explicit text in §11 Scenario A noting that "T3b PASS supports the **linear-hedge calibration**; a Rev-3 spec extension is required to support **convex-instrument pricing** (variance-channel + quantile-regression evidence per ε.6/ε.7 — distributional welfare evidence deferred from Q-1b)." This makes the salvageability path explicit and lets the user see how Rev-2 mean-β chains forward to convex-pricing.

If the user wants Rev-2 itself to deliver convex-pricing evidence, the spec must be re-scoped before commit (extend §4 to include GARCH-X co-primary, extend §6 matrix to include quantile-regression rows, extend §11 Scenario A to handle GARCH-X verdict).

### 2.7 Product-validity summary table (CORRECTED vs prior incorrect-framing review)

| Question | Prior review (incorrect _microshocks_ framing) | This review (corrected _inequality_ framing) |
|---|---|---|
| 1. Mean-β sufficient for convex pricing? | 🔴 NO — gap | 🔴 NO — gap unchanged |
| 2. Macro-shock identifying variation? | 🟡 PARTIAL (X_d aggregate concern) | 🟢 PASS (controls ARE macro shocks); 🟡 advisory on event-window vs continuous-control operationalization |
| 3. Inequality lens (60/25/15 WC-CPI) preserved? | (asked under wrong framing as "microshocks") | 🟢 PASS (preserved by construction; controls don't absorb labor-CPI) |
| 4. Convex-payoff interpretation present? | 🔴 NO — gap | 🔴 NO — gap unchanged |
| 5. 13-row matrix product-informative? | 🟡 MIXED | 🟡 MIXED (under corrected framing, WC-weights sensitivity row is first-class product instrumentation) |
| 6. Q-1b vs convex-product tension | 🔴 PRESENT | 🟡 SALVAGEABLE — Rev-2 mean-β + Rev-3 distributional follow-on; corrected memo itself acknowledges |

**Note on Question 2 X_d-aggregate concern:** the prior review's concern (Carbon protocol user volume aggregates retail + sophisticated non-arb traders) is partially independent of the macro-vs-micro framing. Under the corrected framing it is downgraded but not eliminated: if Abrigo's product hypothesis is that *retail demand for protection* drives X_d, even macro-shock identification leaves the question of whether retail X_d-signal is dominant in the aggregate. Recommend retaining a §10 ε.8 future-revision pointer on trade-size-quantile decomposition of X_d. Not a Rev-2 blocker.

---

## SECTION 3 — Reviewer recommendations

### 3.1 Standard CR (technical) — three non-blocking advisories

1. **Panel-state fingerprint at §13** — add a one-line "as-of" commit hash or fingerprint for `weekly_panel` and `weekly_rate_panel` so Phase-5 consumers can detect drift between spec-commit and execution.
2. **Matrix runnable-vs-deferred separation (§6)** — distinguish runnable-at-Rev-2 rows (1-8, 11-13) from deferred-future-revision-pointers (rows 9-10), or move 9-10 wholly into §10 ε-pointers.
3. **Misnumbered FAIL trio in dispatch** — confirm with the user that "76 / 65 / 56" was meant as "n=76 primary + (n=65, n=56 FAILs)" and not three separate FAIL rows. Spec is internally consistent under that reading.

### 3.2 Product-validity — two recommended additions before commit

1. **Add §10 ε.6 (GARCH-X co-primary) + ε.7 (conditional quantile regression at q ∈ {0.10, 0.50, 0.90}) future-revision pointers** with one-paragraph defenses each. This makes the convex-pricing path-forward concrete and auditable. Without these pointers, Rev-2's product implication is opaque.
2. **Add explicit text in §11 Scenario A** noting that T3b PASS supports the linear-hedge calibration *only*, and that a Rev-3 spec is required for convex-pricing evidence. This makes the Rev-2 → Rev-3 chain explicit.

### 3.3 Product-validity — one user-resolution item before commit

**Confirm the α+β identification operationalization.** The dispatch's wording suggests release-event-window dummies (β-strategy: CPI/FOMC release weeks); Track A operationalizes macro shocks as continuous controls. These are not equivalent. Either:

- (a) Confirm continuous-control partialing is the intended α+β operationalization, OR
- (b) Re-scope Track A's §4 to include explicit release-event-window dummies (e.g., `is_cpi_release_week × X_d` interactions, separate event-window OLS).

This is the one Section-2 finding that requires user input before commit; the others are deferred-future-revision pointers that can be added by Track A author at the same commit.

---

## SECTION 4 — Final verdict

| Track | Verdict | Notes |
|---|---|---|
| Standard CR | **PASS-with-non-blocking-advisories** | 3 advisories: panel fingerprint, matrix runnable-vs-deferred, dispatch misnumbering. None blocks commit. |
| Product-validity | **NEEDS-WORK** | Convex-payoff gap remains; Rev-2 mean-β salvageable as linear-hedge calibration with explicit Rev-3 deferral; Q-1b tension acknowledged in corrected memo and resolvable via Rev-2/Rev-3 split. |

**Recommended disposition for the user:**

1. **Commit Track A as Rev-2 (mean-β linear-hedge calibration spec).** Anti-fishing-clean, Reiss-Wolak-clean, structurally sound. The math is right.
2. **Before commit, ask Track A author to add §10 ε.6 + ε.7 future-revision pointers and the §11 Scenario A "linear-hedge only" text** (Section 3.2 above). These are minor additions, not re-scopes.
3. **Before commit, confirm with user the α+β operationalization** (Section 3.3 above) — continuous-control vs release-event-window dummies. If user confirms continuous-control, no spec change needed. If user wants release-event-window, Track A author must add §4.5.
4. **Schedule Rev-3 / Phase-2b for convex-pricing extension** (GARCH-X + quantile regression). The corrected memo flags distributional welfare as required; Rev-3 is the place to deliver it.

The corrected product framing (macro shocks, inequality lens) is **better aligned with Track A's spec architecture** than the prior incorrect "microshocks" framing was. Track A's controls were always macro shocks; under the corrected framing they are exactly right. The remaining gap is the convex-payoff one — which is real, deferred-resolvable, and not a defect in Track A's authoring.

**End of corrected review. Track A is recommendable for commit subject to the two minor additions in §3.2 and the one user-resolution in §3.3.**
