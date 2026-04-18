# Phase 1 NB1 findings digest (2026-04-18)

Disk-local mirror of the persistent-memory digest at
`~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_phase1_findings_digest.md`.

This version is git-tracked and travels with the repo. Prefer it after compaction when a commit-anchored context is needed.

## Context (one paragraph)

Structural econometrics pipeline testing whether Colombian CPI surprises cause COP/USD (TRM) realized volatility. Ultimate product goal: ground the "Abrigo" macro-hedge product (permissionless FX vol insurance for underserved-FX countries via Mento stablecoins). The scientific gate is **T3b: β̂_CPI − 1.28·SE > 0** on the primary OLS. Passing = clean empirical support for the hedge product. Spec Rev 4 pre-committed the primary: OLS on RV^{1/3}, weekly frequency, with 6 controls and HAC(4) SEs. Sample: 2008-01-02 → 2026-03-01, n_weeks=947.

## Four Decisions locked in Phase 1

| # | scope | primary | sensitivity alt |
|---|---|---|---|
| 1 | sample window | 2008-01-02 → 2026-03-01, n_weeks=947 | n/a |
| 2 | LHS transform | RV^(1/3) | log(RV) |
| 3 | frequency | weekly | daily |
| 4 | Colombian CPI surprise spec | `cpi_surprise_ar1` (ABDV 2003 AR(1) expanding-window over 1954-present DANE IPC) | A9 asymmetric + 60-month rolling AR(1) |

All four respect spec Rev 4 pre-commitments with `anti_fishing_binding = True`.

## Material finding 1: Colombian CPI surprise asymmetry (§4a)

- **Event density:** 218 / 947 weeks = 23.0%
- **Sign balance:** 205 negative / 13 positive — ~94% negative. Extreme.
- **Nonzero mean:** −0.69 (strongly biased, NOT centered on zero)
- **Nonzero |skew|:** 0.90, kurt_exc: +1.11

### Root-cause audit (Trio 2, commit `6d3a130b4`)

The §4a audit ruled out three candidate bugs before accepting the asymmetry as a genuine design property:

1. **Alignment:** rate = **1.000** → release-date alignment is methodologically correct. Not a calendar bug.
2. **Imputation contamination:** no evidence in surprise series.
3. **Warm-up adequacy:** 643 months pre-sample vs 12-month threshold → far beyond adequate.

Root-cause (accepted): **regime mismatch.** AR(1) expanding-window anchors intercept to 1954-present history.
- Pre-sample mean MoM (1954-2007, incl. hyperinflation episodes): **+1.23%**
- In-sample mean MoM (2008-2026, modern BanRep inflation-targeting regime): **+0.40%**
- Ratio: ~3× → forecast systematically pulled above modern reality → systematic negative surprises.
- Correlation(surprise, CPI level) = **+0.37**

## Material finding 2: US CPI fat tails (§4b Trio 1, commit `50da209f6`)

Same `cpi_surprise_ar1` operator applied to FRED CPIAUCSL (swap DANE IPC for FRED CPIAUCSL, hold operator constant):

- **Event density:** 217 / 947 weeks = 22.9% (≈ identical to Colombian, monthly release cadence)
- **Sign balance:** 110 positive / 107 negative — **symmetric**
- **Nonzero mean:** +0.0025 (centered on zero)
- **Nonzero |skew|:** 1.31 (opposite sign: **left-skewed**)
- **Nonzero kurt_exc:** **+8.51** (much fatter tails than Colombian)

**Interpretation:** same operator applied to US data is unbiased → **confirms Colombian asymmetry is regime-specific (hyperinflation anchoring), NOT a methodological bug.** US fat tails are driven by 2008-2009 deflationary scare, 2020 COVID shock, and 2021-22 inflation surge outliers.

## T3b risk assessment

Three risk vectors for the primary gate `β̂_CPI − 1.28·SE > 0`:

1. **Attenuation bias on Colombian CPI surprise.** Measurement error in the regressor (AR(1) misspec relative to true market expectations) biases β̂ toward zero. Passing T3b despite attenuation = strong evidence. Failing T3b does NOT preclude the effect — it is consistent with attenuation masking it.
2. **Sign asymmetry reduces effective identifying variation.** 205 neg / 13 pos means the linear OLS fits the negative tail almost exclusively. Motivates asymmetric sensitivity (A9).
3. **US CPI fat tails (kurt_exc=8.51).** Finite-fourth-moment holds, HAC(4) consistent, but bandwidth sensitivity to HAC(12) is now empirically motivated, not just theoretically prudent.

## Strategic product read

- **Clean primary story** ("CPI surprise linearly moves TRM vol by β") is at material risk given Colombian asymmetry + attenuation.
- **Conditional-event-day story** ("TRM is more volatile on CPI release days; large surprises move it much more") is robust — grounded on event-day vol ratios + tail analysis (Phase 3 NB3 sensitivity).
- Both serve the Abrigo product pitch. The research pipeline honors the clean-primary framing for scientific integrity; product pitch has flexibility the research does not.

## Motivated sensitivities for Task 13 to pre-register

These should be **frozen in Task 13 (cleaning.py + fingerprint + pre-NB3 prep) before any NB2 estimation runs**, while no β̂ has been observed. This preserves the `anti_fishing_binding = True` seal.

| ID | sensitivity | motivating finding |
|---|---|---|
| A9 | asymmetric response (\|surprise\|, pos-only, neg-only) | Colombian 94% negative asymmetry (§4a) |
| A12 | HAC bandwidth robustness (HAC(12) alongside HAC(4)) | US CPI kurt_exc=8.51 (§4b Trio 1) |
| new-S1 | 60-month rolling AR(1) surprise | alternative to full-history anchoring (already in Decision #4 pre-registered alt) |
| new-S2 | 2015-2017 COP-crisis sub-sample drop | Colombian regime shock sub-period |
| new-S3 | 2020-2021 COVID sub-sample drop | US fat-tail outlier concentration |
| new-S4 | CPI_surprise × intervention_dummy interaction | does BanRep FX intervention mechanically absorb CPI shocks? |
| new-S5 | event-day vol ratio (mean(\|TRM return\|) on release days ÷ non-release) | product-facing statistic; robust to AR(1) misspec |

**Status:** A9 and A12 are already anticipated in spec Rev 4. S1 sits in Decision #4's sensitivity row. **S2-S5 are NEWLY motivated by Phase 1 findings and need to land in Task 13 before NB3 is authored.**

## How to apply

When Phase 1 NB1 closes (Task 15 review gate) and Phase 2 NB2 kicks off:

1. **Before NB2 estimation runs:** Task 13 (cleaning.py + fingerprint + pre-NB3 prep) must consolidate all motivated sensitivities into a frozen pre-registration document. The agent executing Task 13 should:
   - Read this file + the `anti_fishing_binding` section of spec Rev 4
   - Enumerate A9, A12, S1-S5 as pre-registered sensitivity runs in the NB3 scaffold
   - Hash the sensitivity list into the panel fingerprint so post-hoc additions are detectable
2. **NB3 authoring (Phase 3):** every sensitivity above gets a dedicated subsection. NB3 executes them only after NB2 primary β̂ is frozen.
3. **Product pitch (separate from research):** even if primary T3b fails, the conditional-event-day story (supported by new-S5) can still ground the Abrigo pitch; this is a deliberate two-track strategy.

## Commit references for verification

- §4a Trio 1 (Colombian CPI inspection): `0f9751bc6`
- §4a Trio 2 (alignment + imputation audit): `6d3a130b4`
- §4a Trio 3 (Decision #4 lock): `bfb52e8d0`
- §4b Trio 1 (US CPI inspection): `50da209f6`
