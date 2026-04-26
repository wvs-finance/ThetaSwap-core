# Task 11.O Rev-2 Gate-FAIL — Disposition Memo

**Author**: foreground orchestrator
**Date**: 2026-04-25
**Trigger**: Phase 5b Analytics Reporter committed `799cbc280` with gate verdict T3b = FAIL on Row 1 primary spec.
**4-reviewer gate**: CLOSED with all PASS-class (CR PASS, RC PASS, SD PASS-w-adv, Model QA MODEL-PASS-w-adv).
**Status**: HALT to user per spec §11.C and `feedback_pathological_halt_anti_fishing_checkpoint`. NO further task dispatch (Rev-3 ζ-group, brainstorm-α, brainstorm-β, etc.) until user picks a disposition.

---

## 1. Headline finding

| Metric | Value |
|---|---|
| β̂_X_d (Row 1 primary, OLS+HAC(4)) | **−2.799 × 10⁻⁸** (sign-flipped from pre-registered β > 0) |
| HAC(4) SE | 1.423 × 10⁻⁸ |
| 90% one-sided lower bound | −4.621 × 10⁻⁸ (≤ 0 ⇒ T3b FAIL) |
| t-stat / p-value | −1.966 / 0.0493 (two-sided, sign-flipped direction) |
| n | 76 (matches pre-commitment) |
| T1 exogeneity | **REJECTS** (F=3.480, p=0.0031) — predictive not structural |
| Pre-registered FAILs (Rows 3, 4) | confirmed FAIL as predicted |
| Anti-fishing invariants | 8/8 preserved byte-exact |

**Same analytical-discipline-vindication pattern as the FX-vol-CPI notebook (closed FAIL)**: honest sign-flip rejection with CI excluding zero in the wrong direction; T1 REJECTS confirms predictive-not-structural; no silent threshold tuning, no rescue claims.

## 2. Why this is a HALT, not a "just-run-Rev-3" event

Per `feedback_pathological_halt_anti_fishing_checkpoint` and `feedback_strict_tdd`:

- The gate threshold (T3b 90% one-sided) was pre-committed at spec §7
- Running Rev-3 ζ-group at this point without an explicit disposition pivot is **silent threshold-mode-shifting** — the convex-payoff caveat at spec §11.A says ζ-group is for "convex-instrument pricing readiness," NOT for re-litigating the mean-β FAIL with different statistical machinery
- The CORRECTIONS-block protocol requires:
  (a) HALT,
  (b) disposition memo (this document),
  (c) user-enumerated pivot,
  (d) post-hoc 3-way review of the picked path

This memo satisfies (a)+(b). Awaiting user input on (c).

## 3. New analytical findings to factor into the disposition

Three Rev-3-forward findings from Model QA + RC's adversarial probe ALL reinforce the FAIL rather than rescue it:

1. **Breusch-Pagan p = 0.0237 → heteroskedasticity REJECTS at 5%**. Phase 5b's Levene T2 was quartile-by-X_d; Model QA's BP test is on the residuals against fitted-value variance. Implications: HAC(4) SE may be optimistic; Student-t innovations refit was on Row 11 but didn't propagate to Row 1 primary's interpretation.

2. **Single observation 2026-03-06 (Cook's D = 0.888, studentized residual = −3.13) drives ~50% of |β̂|**. The sign-flip FAIL is **robust to drop-one removal** but the magnitude is heavily influence-driven. Implications:
   - The wrong-sign rejection is real (significant negative even after dropping the influential observation)
   - But the magnitude (-2.799e-8) is unstable; published claim should be "negative coefficient with single-observation leverage" not "magnitude estimate"
   - Rev-3 must address via studentized-residual diagnostics + drop-one CI

3. **ρ(X_d, fed_funds_weekly) = −0.614** (shared-third-factor risk). X_d (Mento basket user volume on Celo) and fed_funds_weekly (US monetary policy) are negatively correlated at -0.614, which is high. Implications:
   - The sign-flip could be confounded by US monetary cycle (rising fed_funds → falling X_d → falling Y_3, all driven by US-side macro environment)
   - FWL (Frisch-Waugh-Lovell) residualization not in spec; Rev-3 should add
   - Identification is NOT fully macroeconomic-shock-driven as spec §4 claimed; US monetary cycle is a confounder

## 4. Disposition options

Each option below lists: action, statistical implication, anti-fishing risk, downstream cascade, alignment with Abrigo product purpose.

### Option α — Rev-3 ζ-group: convex-payoff extensions

**Action**: Author Rev-3 spec covering the 4 ζ-group rows (ζ.1 quantile β̂(τ), ζ.2 GARCH(1,1)-X, ζ.3 lower-tail conditional, ζ.4 option-implied vol surface fitting) per spec §10.6. New plan revision Rev-5.3.3 adds 4 dispatch tasks; new spec authored (TW or SD per `feedback_three_way_review`); Phase 5a/5b cycles repeat per ζ row.
**Statistical implication**: Tail-risk / asymmetric-response / variance-amplification evidence. Mean-β FAIL is ORTHOGONAL to convex-payoff fitness — a mean-β can be zero (or wrong-signed) while quantile β(τ) is significantly non-zero at the tails. This is the analytically-correct path forward IF the convex-instrument product purpose holds.
**Anti-fishing risk**: LOW. ζ-group is pre-registered in spec §10.6; running it after a mean-β FAIL is exactly what the spec prescribed.
**Cascade**: Substantial — multi-week dispatch cycle (4 spec authoring rounds × 4 review trios + 4 Phase 5a + 4 Phase 5b).
**Product alignment**: HIGHEST — directly addresses convex-instrument pricing readiness.

### Option β — Brainstorm-α: payments/consumption pivot

**Action**: Per the closed `project_phase_a0_exit_verdict` memo (2026-04-24, original Phase-A.0 EXIT_NON_REMITTANCE verdict mentioned brainstorm-α as a payments/consumption pivot candidate), reframe the entire X_d hypothesis. Mento basket user volume may NOT be a hedge-demand signal; it may be a payments / consumption signal. Y₃ might be the wrong LHS for a payments-driven X_d.
**Statistical implication**: Throw out Rev-2's X_d definition; restart at Phase A.1 brainstorm with new Y/X candidates.
**Anti-fishing risk**: MEDIUM — pivoting after FAIL is acceptable IF the pivot is honest (new hypothesis, not p-hacking). Must pre-commit new spec before any data exploration on the new variables.
**Cascade**: Largest reset — back to brainstorm phase. Estimated weeks of work.
**Product alignment**: VARIES — depends on whether the payments/consumption pivot leads to a hedgeable convex-instrument thesis or to a different product altogether.

### Option γ — Brainstorm-β: per-currency Mento focus

**Action**: Drop the basket-aggregate X_d in favor of per-currency X_d (e.g., COPM-only, BRLm-only, EURm-only). Per spec §6 Row 8, per-currency COPM showed n=47 with under-N joint X_d × Y_3 — could be informative if the basket-aggregate masked currency-specific signals.
**Statistical implication**: 3 separate regressions (one per currency), each with its own n. Lower N per regression but isolates currency-specific transmission.
**Anti-fishing risk**: MEDIUM-HIGH — switching to per-currency AFTER seeing the basket-aggregate FAIL is suggestive of cherry-picking. Must explicitly pre-commit hypothesis (e.g., "BRLm shows strong inflation-hedge signal because BR is highest-inflation country in the panel") BEFORE estimating.
**Cascade**: Moderate — 3 spec sub-rows, 3 Phase 5a panels (already prepared), 3 Phase 5b runs.
**Product alignment**: MEDIUM — informs which currency to launch convex instruments on first.

### Option δ — Accept FAIL and EXIT

**Action**: Close Rev-2 with FAIL verdict; document per project pattern (`project_fx_vol_cpi_notebook_complete` precedent). Update Abrigo's product framing to reflect the negative-or-null evidence on the X_d → Y_3 hedge-demand thesis. Pivot product strategy.
**Statistical implication**: No further estimation. The Rev-2 FAIL stands.
**Anti-fishing risk**: NONE — the gate FAIL is honored as the analytical close-out.
**Cascade**: Smallest — close-out artifact (similar to FX-vol notebook EXIT closure) + memory-note update.
**Product alignment**: HIGH — honest product-strategy update based on rigorous analytical FAIL.

### Option ε — User-driven structural-econometrics flow (deferred earlier)

**Action**: User runs the structural-econometrics skill interactively with the orchestrator (the deferred Track B). Use the 19-AskUserQuestion flow to potentially RE-DERIVE a different specification with the user as primary decision-maker. May converge to a Rev-2.1 spec OR a fundamentally different identification strategy.
**Statistical implication**: User-controlled — could lead anywhere from a marginal Rev-2.1 amendment to a complete reframe.
**Anti-fishing risk**: LOW (user-controlled).
**Cascade**: User-bounded.
**Product alignment**: VARIES — depends on user's analytical preferences.

## 5. Recommendation

**Option α (Rev-3 ζ-group)** is the analytically-correct path IF the convex-instrument product purpose holds. Mean-β FAIL is orthogonal to convex-payoff fitness; the tail-risk evidence is the load-bearing test for the actual product Abrigo is selling.

**Option δ (EXIT)** is the cheapest, anti-fishing-cleanest path IF the analytical evidence is sufficient to pivot product strategy.

**Option ε (interactive structural-econometrics)** was the user's explicit prior preference ("I'll have to just run the structural econometrics skill with you later on") and may be where the user is heading regardless.

Avoid Option γ (cherry-picking after seeing the basket FAIL) unless explicit pre-commitment.

## 6. Action gate

**Awaiting user pick: α / β / γ / δ / ε.**

No agent dispatch (Rev-3 ζ-group plan revision, Rev-3 spec authoring, brainstorm-α restart, etc.) until disposition is locked.

---

## Appendix — Phase 5b commit chain

| Commit | Subject |
|---|---|
| `d9e7ed4c8` | spec(abrigo): Rev-5.3.2 Task 11.O Rev-2 — Track A spec landed |
| `2eed63994` | feat(abrigo): Phase 5a Data Engineer prep (14-row panels) |
| `777596b8e` | review(abrigo): Phase 5a 3-way converged (PASS) |
| `799cbc280` | feat(abrigo): Phase 5b Analytics Reporter (gate FAIL verdict + 14-row estimates + T1-T7) |
| `6b1200dcb` | review(abrigo): Phase 5b RC PASS + Model QA MODEL-PASS-w-adv (CR + SD pending credit reset) |
| `f38f1aad3` | review(abrigo): Phase 5b 4-reviewer gate CLOSED (CR + SD landed; gate FAIL stands) |
