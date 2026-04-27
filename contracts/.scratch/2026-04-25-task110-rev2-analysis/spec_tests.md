# Specification Tests T1–T7 — Task 11.O Rev-2 Phase 5b

**Spec:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` §7  
**Run on:** Row 1 primary panel (n = 76); T7 cross-references Row 6 parsimonious  

---

## 4-part decision-citation block (per `feedback_notebook_citation_block`)

**Reference:** Newey & West 1987; Andrews 1991; Hausman 1978; Box-Cox 1964;  
Politis-Romano 1994; Cohen 1988 §9; Bai-Perron 1998; Self-Liang 1987.  
**Why used:** weekly Y₃ panel exhibits LOCF-induced autocorrelation, heavy-tail  
innovations, and a known structural-break boundary at Carbon-protocol launch.  
Spec §7 T1–T7 was pre-committed at Rev-2 commit `d9e7ed4c8`; this block executes  
the pre-registered tests byte-exact, no re-tuning.  
**Relevance to results:** T1 verdict re-flags β̂ as predictive vs structural —  
load-bearing for the §11.A convex-payoff caveat. T2/T4/T5 surface variance and  
tail-distribution risks that would invalidate Normal-based HAC inference.  
**Connection to product:** T3b is the gate; T1 + §11.A together determine whether  
β̂ is admissible into the simulator's *linear-payoff* hedge calibration. Convex-  
payoff calibration is **deferred to Rev-3 ζ-group regardless of T3b verdict**  
(spec §11.A).  

---

## T1 — X_d strict exogeneity (Hausman / Wu-Hausman style joint F-test)

- **Test statistic:** F = 3.480
- **p-value:** 0.0031
- **Rejects at 5%:** True
- **Interpretation:** β̂_X_d is **predictive** (lagged Y₃/controls jointly predict X_d → predictive-regression bias active).
- **FX-vol prior-art carry-forward:** FX-vol's CPI-surprise REJECTED at F=15.12; this row's X_d on Carbon protocol **also REJECTS** — the prior expectation was less likely to reject because Carbon settles at sub-weekly cadence.

## T2 — Announcement-window variance premium (Levene's median test)

- **Test statistic:** 1.675
- **p-value:** 0.2038
- **Rejects at 5%:** False
- **Interpretation:** Y₃ variance is statistically indistinguishable between top and bottom quartiles of X_d; no variance-channel evidence at primary spec.

## T3a — Two-sided coefficient test (α = 0.05)

- **t-statistic:** -1.966
- **p (two-sided):** 0.0493
- **Rejects at 5%:** True

## T3b — One-sided gate (α = 0.10) — **PRIMARY GATE**

- **β̂ − 1.28·SE:** -4.621e-08
- **Gate verdict:** **FAIL**
- **Pre-registered sign:** β > 0 (rising X_d → rising inequality differential).

## T4 — Ljung-Box residual serial correlation

- **p-value (lag 4):** 0.5014
- **p-value (lag 8):** 0.3308
- **Serial correlation present (lag 4):** False
- **Interpretation:** HAC(4) is sufficient at the 5% level.

## T5 — Jarque-Bera normality of residuals

- **JB statistic:** 0.762
- **p-value:** 0.6833
- **Normality rejected at 5%:** False
- **Interpretation:** Residuals consistent with Normal innovations.

## T6 — Chow structural-break test at Carbon-launch (2024-08-30)

- **F-statistic:** NaN
- **p-value:** NaN
- **Break rejects at 5%:** False
- **Interpretation:** No structural break detected at the launch boundary; full-sample is the binding read.
- **Caveat:** spec §7 T6 nominally calls Bai-Perron unknown-break; this Chow at
  the known launch date is a boundary-test variant. The 76-week panel begins 4
  weeks AFTER 2024-08-30 (live primary dt_min = 2024-09-27), so by construction
  there is no pre-launch row in the primary panel. We compute the test using the
  2-week pre-launch window from the arb-only diagnostic (Row 7) which begins
  2024-08-30 — but the test is identified only when both sub-panels are non-empty.
  When the test cannot be identified on the primary panel (no pre-launch rows),
  the F-statistic is reported as NaN — an honest 'test cannot be run on this
  sample' rather than an imputed value.

## T7 — Parameter stability across primary vs. parsimonious controls

- **β̂ (primary, 6 ctrl):** -2.799e-08
- **β̂ (parsimonious, 3 ctrl):** -7.317e-09
- **SE (primary):** 1.423e-08
- **|Δβ̂| ≤ 1·SE (within tolerance):** False
- **Predictive-vs-structural flag (FX-vol Finding 14 carry-forward):** **PREDICTIVE**
- **Interpretation:** Specifications diverge by > 1·SE → parsimonious is the alternative-primary candidate; full-control may over-fit.

---

## HALT discipline (per Phase 5b dispatch + spec §9.5)

- **T1 verdict:** REJECTS.
  - Per FX-vol Finding 14, β̂ is now interpreted as a *predictive-regression* coefficient, NOT a strict-impulse parameter. Product framing must update to reflect this; the simulator-calibration claim at spec §12 is bounded by this interpretation.

