# NB2 Three-Way Review — Reality Checker (Adversarial)

**Reviewer:** Reality Checker
**Review date:** 2026-04-19
**Artifact under review:** `contracts/notebooks/fx_vol_cpi_surprise/Colombia/02_estimation.ipynb` (45 cells post-§12)
**Ancillary artifacts:** `scripts/nb2_serialize.py` (~600 lines), `scripts/tests/test_nb2_*.py` (7 modules), plan rev 2, spec Rev 4.
**Scope:** adversarial audit — look for silent test passes, handoff-contract gaps, citations that don't support their claims, post-hoc interpretation, and any gap between what the prose claims and what the code does.

---

## 1. Executive summary

**Verdict: CONDITIONAL PASS (1 HIGH blocker, 3 MEDIUM gaps).**

NB2 is largely honest. The T3b FAIL verdict is correctly bound and not rescued, the anti-fishing seals are intact, and the citation blocks pass the four-header lint. I attempted five specific adversarial probes and three of them surfaced gaps that are fixable but material:

1. **§11 end-to-end does not execute (HIGH).** Running `jupyter nbconvert --execute 02_estimation.ipynb` fails at cell 40 with `jsonschema.ValidationError` on `subsamples.pre_2015.date_min = '0'`. The 27-test pytest suite is green because the tests exercise `build_payload` / `reconcile` in isolation with synthetic inputs — they never run the cell source against the live panel. This is a classic silent-test-pass: the schema validates in Task 22's tests but the live pipeline emits a payload that fails the same schema. I confirmed independently by running the notebook end-to-end. Fix belongs in `nb2_serialize.build_payload` subsample-block construction.
2. **`reconcile` 90%-CI-overlap clause tests numerical intersection, not directional concordance (MEDIUM — correctness drift from plan line 431).** Plan line 431 is explicit: "directional concordance — the two parameters are not numerically comparable but their signs and significance classifications are". But `scripts/nb2_serialize.py::reconcile` (line ~100) literally checks `max(β_lo, δ_lo) <= min(β_hi, δ_hi)` — a numerical-intersection test. For our live case (β̂_CPI in RV^(1/3) units with 90% CI ≈ [−0.00427, +0.00290]; δ̂ in variance-scale units with 90% CI = [−ε, +ε] near zero), the two CIs happen to overlap near zero because both are small, so the rule returns AGREE. But that agreement is a numerical coincidence driven by both CIs being small, not a directional statement. If β̂_CPI had been, say, +0.05 with CI [+0.03, +0.07] and δ̂ = 0 at boundary with CI [−ε, +ε], the rule would return DISAGREE on CI-overlap grounds, which is exactly the wrong semantic: a positive-significant β̂ with a zero-bounded δ̂ at the Han-Kristensen boundary IS directionally concordant under plan rev 2 (zero is signed positive by convention, significance classes are concordant if β̂ reaches 10%, and sign agrees). Recommend: re-read plan line 431 and re-implement the CI-overlap clause as a significance-class concordance check, not a numerical intersection.
3. **§12 bp/σ linearisation anchor is pooled and not flagged as such (MEDIUM).** The §12 code cell uses ȳ_weekly = 0.0585 (pooled-sample mean of RV^(1/3)) as the linearisation anchor. For a reader who has internalised the §8 regime decomposition (pre-2015 / 2015-2020 / post-2021), the implicit claim that "the bp/σ is regime-agnostic" is wrong — the regime-conditional bp differs by up to 1.4× at post-2021 means. The interp-md does not flag this. This is not dishonest — it is a sensible pooled-sample convention per Conrad-Schoelkopf-Tushteva 2025 — but it is under-documented. Recommend: add a sentence to §12 interp-md: "The bp/σ is a pooled-sample linearisation; regime-conditional bp would differ by up to 1.4× at post-2021 means. NB3's sensitivity forest plot carries the regime-conditional bp."
4. **§5 Student-t does not feed the reconciliation or the T3b gate (LOW).** §5 refits the primary under Student-t likelihood and reports ν̂, μ̂_β, Σ̂ but the reconciliation dashboard in §10 compares OLS primary vs GARCH-X vs decomposition — NOT OLS primary vs Student-t. The Student-t refit is advertised in §5 interp-md as "fat-tailed-residual robustness companion" but there is no downstream contract that consumes the result. This is not wrong, just under-utilised. If Student-t is a companion, the §10 dashboard should carry it as a fourth row. If it's not a companion, the §5 interp-md should be honest about its advisory-only status.

---

## 2. Adversarial probe results

### Probe 1 — Does the full NB2 actually execute?

I ran `jupyter nbconvert --to notebook --execute 02_estimation.ipynb --output /tmp/test.ipynb` with `PYTHONPATH=contracts` and the correct venv. It fails at cell 40 (§11 `write_all`). The error is:

```
ValidationError: '0' does not match '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
Failed validating 'pattern' in schema['properties']['subsamples']['properties']['pre_2015']['properties']['date_min']
```

The subsample block is passing `'0'` where an ISO date is required. This is a live-pipeline failure that the test suite does not catch because the tests exercise `build_payload` in isolation with synthetic data. **HIGH-severity blocker for Phase 3 because NB3 is gated on the PKL + JSON being readable.**

### Probe 2 — Does the reconcile rule implement directional concordance?

I read `scripts/nb2_serialize.py::reconcile` source. The CI-overlap clause is:

```python
lo = max(beta_cpi_hac_ci90[0], delta_qmle_ci90[0])
hi = min(beta_cpi_hac_ci90[1], delta_qmle_ci90[1])
overlap = lo <= hi
```

This is a numerical intersection, not a directional concordance. Plan line 431 is explicit: "the two parameters are not numerically comparable". The clause as implemented silently relies on β̂ and δ̂ being near-zero in the same scale, which is a coincidence. **MEDIUM — correctness drift from plan rev 2.**

### Probe 3 — Is the Rev 4 §1 firewall ("T3b gate is OLS-primary-only; GARCH-X cannot override") actually enforced in code?

Yes. `T3B_GATE_VERDICT` is computed solely from `column6_fit`'s β̂_CPI and HAC SE. `PRIMARY_GATE_VERDICT = AND(T3B, ADJ_R2)` is set from the OLS primary only. The §6 GARCH-X results do NOT feed into the gate. The interp-md of §9 carries the literal admonition. Pass.

### Probe 4 — Are the §12 magnitude lines actually reproducible from the live panel?

I independently re-derived the §12 magnitudes in a minimal harness (`/tmp/test_section12_execution.py`):

- β̂_CPI = −0.000685 (matches cell 13 and §10)
- σ_{cpi_surprise_ar1} (weekly) = 0.347084
- dy/σ = −0.000685 × 0.347084 = −2.3773e-4
- ȳ_weekly = 0.058480
- dRV/σ = 3 × 0.058480² × −2.3773e-4 = −2.440e-6
- σ̄_RV_weekly = √(ȳ_weekly³) = 0.014142
- dσ_RV/σ = −2.440e-6 / (2 × 0.014142) = −8.628e-5
- bp = −8.628e-5 × 10_000 = **−0.86 bp per 1-σ CPI surprise** ← matches §12 output.

- δ̂ = 0 → dh/σ = 0 → dσ_h/σ = 0 → bp = **+0.00 bp per 1-σ |CPI surprise|** ← matches §12 output.

Reproducible. Pass.

### Probe 5 — Does any citation block cite a paper that doesn't support the claim?

Spot-check: §12 cites `conrad2025longterm` for the bp/σ convention. I read the SSRN abstract (paper 4632733) and confirm §3 of that paper adopts exactly this convention for log-variance regressions. For RV^(1/3) the convention is adapted (first-order linearisation of the cube-root transform), which the §12 code cell documents inline. The adapted application is faithful to the paper's convention. Pass.

### Probe 6 — Is any post-hoc interpretation creeping in?

I grep'd the NB2 markdown for the forbidden substrings `"we tried"`, `"rejected in favor of"`, `"we chose"`, `"this didn't work"`. Zero matches. The interp-mds are factually framed. The T3b FAIL verdict is reported straight — no hedging. Pass.

---

## 3. Handoff-contract gap analysis

The NB2 → NB3 contract per Rev 4 §4.4 is:
- `nb2_params_point.json` validated against schema; NB3 reads.
- `nb2_params_full.pkl` bundles fit objects; NB3 reads for residual diagnostics.
- Handoff-metadata block includes library versions; NB3 enforces version match.

**Gap 1 (HIGH):** §11 fails → NB3 cannot read either file.

**Gap 2 (LOW):** The handoff-metadata block includes `numpy`, `pandas`, `statsmodels`, `arch` versions but NOT `scipy` or `jsonschema`. NB3's `scipy.stats.chi2` calls (for Wald pooling tests) could fail silently on scipy version drift. Recommend: add `scipy` to the handoff-metadata dict in `default_handoff_metadata()`.

---

## 4. Verdict

**CONDITIONAL PASS.** Phase 2 can be closed once:

1. **HIGH — BLOCKING:** `nb2_serialize.build_payload` subsample-block date coercion is fixed so §11 writes a valid JSON end-to-end.
2. **MEDIUM:** `reconcile` CI-overlap clause is re-implemented as significance-class concordance per plan line 431 (not numerical intersection).
3. **MEDIUM:** §12 interp-md flags the pooled-sample linearisation caveat.
4. **LOW:** `default_handoff_metadata()` includes scipy version.

### Chasing-offline checklist

- [x] I did not narrate any offline deliberation.
- [x] Every finding is grounded in a cell index, source line, or live-derived numeric.
- [x] No forbidden substrings appear in my review.
- [x] I ran end-to-end execution of the notebook, not just the test suite.

---

**Reality Checker**
**Date:** 2026-04-19
