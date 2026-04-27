# Model QA Review — Phase-A.0 Remittance-surprise → TRM RV design

**Reviewer:** Model QA Specialist
**Design doc:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md`
**Date:** 2026-04-20

---

## 1. Executive verdict

**PASS-WITH-FIXES.** The design inherits Rev-4 methodology faithfully and preserves the pre-commitment/anti-fishing architecture that vindicated the CPI FAIL. However, five econometric choices are under-specified in ways that would either make the gate unreproducible (AR order, HAC bandwidth rule, step-interpolation side) or pre-determine the verdict regardless of economics (one-sided sign prior on an ambiguous-direction mechanism; power unspecified at effective N ≈ 200–250). These are fixable in a Rev-1 spec without structural redesign. The design has also carried forward, without re-examination, the exact LHS that just produced a null — a diagnostic risk the reviewer cannot clear without a power calculation.

---

## 2. BLOCK-severity findings

### BLOCK-1 — One-sided gate with no economic sign prior

Design fixes `H1: β̂_Rem > 0` (line 58) but Agent 3's own report (lines 52, 111) cites the IMF GIV mechanism as "+40 bps parity deviation" — i.e. remittance inflows causing **depreciation-volatility**, which is a *level* prediction on TRM, not an unambiguous *volatility* prediction. Remittance inflows are plausibly volatility-**reducing** as a stabilizing income stream or volatility-**increasing** as a stress-response inflow during depreciation episodes. With no pre-registered economic reasoning that isolates the sign, a one-sided gate is econometrically indefensible — it halves the rejection region for the wrong reason. If the true effect is negative and large, the gate FAILs, and the FAIL is uninformative.

### BLOCK-2 — Power / minimum detectable effect not pre-committed

Design caveat (line 160) says "effective N drops toward ~200–250" under HAC but nowhere commits to an ex-ante minimum-detectable-effect-size (MDES). At N_eff = 200, one-sided α = 0.10, 80% power, the MDES is ~0.17 SD of the residualized RV^{1/3}. Without a pre-registered economic-magnitude benchmark, a FAIL cannot distinguish "no effect" from "underpowered to detect an economic effect" — which is precisely the diagnostic failure mode the CPI exercise *almost* had. The gate must commit to an MDES *and* to an interpretive rule ("FAIL with β̂ > MDES/2 is inconclusive, not rejection").

### BLOCK-3 — Step-interpolation side & HAC bandwidth rule unspecified

"Friday-anchored step-function" (line 45) does not specify:
(a) last-observation-carried-forward vs next-observation-back-filled (these differ in timing of the shock embedding);
(b) whether release-day falls on the week of release or the following week.
"HAC Newey-West SE with Andrews 1991 optimal bandwidth" (line 53) does not specify the kernel (Bartlett vs Quadratic-Spectral) — Andrews 1991 gives different optimal bandwidths per kernel. Two independent replicators will produce different β̂ SEs. The spec-hash (line 82) locks the *choice* only if the choice is written down.

### BLOCK-4 — LHS low-power diagnosis not addressed

The Rev-4 CPI exercise produced a null on this identical LHS (RV^{1/3} of TRM). Re-using the LHS without a pre-registered power check leaves open: is TRM RV^{1/3} a **low-power outcome on this panel for all macro surprises**? The design should pre-register at least one alternative LHS (log-RV, GARCH-filtered residual vol, or intraday-range Parkinson vol) as a sensitivity row — not to rescue a FAIL, but to distinguish "remittance has no effect on TRM vol" from "TRM RV^{1/3} has no statistical room to move on this panel."

---

## 3. FLAG-severity findings

### FLAG-1 — AR(1) order not justified

Dallas Fed / IDB literature on Latin-American remittances finds strong 12-month seasonality (December/Mother's-Day surges). AR(1) on `ΔlogRem_m` likely leaves seasonal autocorrelation in the residual, contaminating the "surprise." Pre-register AR(1) with seasonal-dummies, or SARIMA(1,0,0)(1,0,0)_12, or test AR(p) for p ∈ {1,2,3,12} and pre-commit to BIC selection before any β̂.

### FLAG-2 — Real-time vs current-vintage handling under-specified

Caveat §1 (line 159) flags vintage risk but methodology (§Scientific question) does not specify the vintage discipline: which release cycle, what revision window, how retrospectively-revised values are treated in the AR(1) training set. This is the single most common failure mode in surprise-identification econometrics (Orphanides 2001). Must be a Rev-1 spec clause, not a caveat.

### FLAG-3 — Reconciliation rule under OLS-vs-GARCH-X heteroskedasticity

Design inherits Rev-4 `reconcile()` (sign + CI-contains-zero + significance concordance, line 60). Under heteroskedasticity that GARCH-X corrects but OLS does not, the two point estimates can *legitimately* disagree on significance while agreeing on sign. Pre-register a numerical-intersection alternative (e.g., "both 90% CIs must exclude zero on the same side") as a secondary reconciliation check.

### FLAG-4 — Pre/post-2015 split post-hoc-looking

Venezuelan-migration-onset as the 2015 split (line 62) is economically plausible but *also* happens to be where a structural break in the remittance-GDP-share series visibly lies. Pre-register a Quandt-Andrews test with un-known break-point on pre-sample data; if the estimated break is within ±12 months of 2015, keep the split; otherwise use the data-driven break.

### FLAG-5 — GARCH-X in-mean/in-variance ambiguity

Design says "surprise in the mean equation" (line 60). Remittance inflows plausibly enter the **variance** equation (stress-response hypothesis), not the mean. Pre-register a GARCH(1,1)-X with surprise in **both** equations as a robustness row, or document why mean-only is the preferred channel.

### FLAG-6 — No December-January seasonal sensitivity

Colombian remittance is highly seasonal (quincena + December-holiday surge). If the A1 monthly sweep preserves this seasonality but the weekly primary does not (step-interpolation smooths it), the two specifications test different economics. Add a December-January-excluded sensitivity row.

### FLAG-7 — Basco & Ojeda-Joya precedent is cyclicality, not vol-causation

Agent 3's caveat (§5) is explicit: the cited literature studies remittance **cyclicality**, not **volatility causation**. The design should acknowledge this is a *novel* identification claim and pre-register a higher evidentiary bar (e.g., require PASS on the primary gate *and* on the event-study co-primary Agent 3 proposed in §4 #1).

---

## 4. NIT-severity findings

- **NIT-1** — "HAC Newey-West" is a slight misnomer; Andrews 1991 is an *alternative* bandwidth selector (plug-in) to Newey-West 1994 (data-driven). Cite both or pick one.
- **NIT-2** — Spec should commit to `numpy`/`scipy` version pins in the environment fingerprint (Rev-4 had `scipy` L-BFGS-B convergence drift across versions).
- **NIT-3** — `gate_verdict_remittance.json` (line 32) — recommend identical schema to Rev-4 `gate_verdict.json` for byte-level diff-ability across exercises.
- **NIT-4** — Success-criteria item 4 ("byte-identical" Jinja2 README) is stricter than necessary; allow Unicode-normalization diffs.

---

## 5. Proposed spec additions (per finding)

- **BLOCK-1** — Add two-sided T3b as pre-committed gate, OR add an economic-sign-derivation subsection (≤10 lines) citing a specific transmission mechanism locking sign; pre-register the one-sided rule only if the mechanism is identified.
- **BLOCK-2** — Add MDES calculation: "At N_eff, α, 80% power, MDES = X SD of residualized RV^{1/3}; FAIL with |β̂| > MDES/2 is reported as *inconclusive* in `gate_verdict_remittance.json`."
- **BLOCK-3** — Specify "last-observation-carried-forward through Friday of the release-week" and "Bartlett kernel, Andrews 1991 plug-in bandwidth with AR(1) pre-whitening."
- **BLOCK-4** — Add sensitivity row: alternate LHS ∈ {log-RV, GARCH(1,1)-filtered residual vol}; report β̂ + 90% CI but do not gate on it.
- **FLAG-1** — Pre-register SARIMA(1,0,0)(1,0,0)_12 with BIC fallback to AR(p) for p ∈ {1,2,3,12}.
- **FLAG-2** — Add ≤15-line subsection on vintage discipline: training-set vintage frozen at spec-commit date, residual computed on first-release values only.
- **FLAG-3** — Add numerical-intersection reconciliation as secondary check.
- **FLAG-4** — Pre-register Quandt-Andrews data-driven break with ±12-month window check on 2015.
- **FLAG-5** — Add GARCH-X variance-equation row as a pre-committed robustness.
- **FLAG-6** — Add December-January-excluded sensitivity row.
- **FLAG-7** — Add event-study co-primary (BanRep release-date windows) with its own gate threshold.

---

## 6. Positive findings (preserve)

1. **Pre-commitment architecture intact** — spec-hash-first, three-way review, integration-test guard against silent-test-pass are all inherited verbatim (§Pre-commitment discipline items 1–11). This is the single most important asset from Rev-4 and the design carries it forward without dilution.
2. **Anti-fishing framing is explicit** (§Risks #5, §Pre-commitment #11) — the distinction from CPI-FAIL is asserted in spec, notebooks, and verdict file. Good discipline; strengthening per FLAG-7 will make it even harder to mis-frame.
3. **Additive-only scope discipline** — new panel column, extended decision-hash, no mutation of Rev-4 artifacts. Reproducibility of the CPI FAIL is preserved.
4. **Parallel-artifact emission** — `gate_verdict_remittance.json` mirrors Rev-4 schema, supporting cross-exercise audit.
5. **Explicit revision-vintage caveat** (§Risks #1) — acknowledges the correct failure mode even if the remediation needs sharpening (FLAG-2).
6. **Conditional Phase-A.1 branching** — engine-registry refactor gated on Phase-A.0 PASS; avoids premature scaling.
7. **Scripts-only scope** preserved — no Solidity, no foundry.toml, consistent with project-memory rule.

---

## 7. Summary for consolidator

The design is structurally sound and preserves the Rev-4 discipline asset. BLOCK-1 (one-sided sign prior), BLOCK-2 (no MDES), BLOCK-3 (unspecified interpolation/kernel), and BLOCK-4 (no LHS-power sensitivity) are the four items that would make the gate verdict non-diagnostic or unreproducible if left unspecified. All four are fixable in Rev-1 without structural redesign. FLAG-1 through FLAG-7 should be addressed for rigor but do not block writing-plans dispatch. Agent 3's own ranking report flagged items congruent with BLOCK-1 (ambiguous sign) and FLAG-7 (cyclicality vs vol-causation gap) — the design has not yet propagated those caveats into the gate specification.

**Word count: ≈ 1,190.**
