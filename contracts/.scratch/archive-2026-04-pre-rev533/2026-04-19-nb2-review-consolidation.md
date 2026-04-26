# NB2 Three-Way Review — Consolidation & Remediation Note

**Orchestrator:** Analytics Reporter (Task 23 foreground agent)
**Consolidation date:** 2026-04-19
**Reviews consolidated:**
- `2026-04-19-nb2-review-model-qa.md` — Model QA Specialist (econometric correctness)
- `2026-04-19-nb2-review-reality-checker.md` — Reality Checker (adversarial)
- `2026-04-19-nb2-review-technical-writer.md` — Technical Writer (PDF readability)

---

## 1. Convergence table

| Finding | Model QA | Reality Checker | Tech Writer | Severity | Task-23 scope? |
|---|---|---|---|---|---|
| §11 serialization fails end-to-end (`'0'` vs ISO date) | HIGH (#1) | HIGH (#1) | HIGH (#1) | BLOCKER | NO — Task 22 |
| `reconcile()` CI-overlap clause is numerical, not directional | — | MEDIUM (#2) | — | MEDIUM | NO — Task 22 |
| §12 pooled-mean linearisation caveat missing | MEDIUM (#3) | MEDIUM (#3) | LOW (#7 — one-liner) | MEDIUM | **YES — §12 interp-md** |
| §6 Han-Kristensen boundary-SE / one-sided CI caveat | MEDIUM (#2) | — | — | MEDIUM | NO — Task 19 |
| §5 Student-t does not feed reconciliation | — | LOW (#4) | MEDIUM (#4) | LOW-MEDIUM | NO — Task 19 |
| §3 OLS-ladder table needs caption / HAC(4) note | — | — | MEDIUM (#2) | MEDIUM | NO — Task 18 |
| §6 GARCH-X output needs DataFrame display | — | — | MEDIUM (#3) | MEDIUM | NO — Task 19 |
| §10 Verdict Box PDF propagation uncertain | — | — | MEDIUM (#5) | MEDIUM | NO — Task 22 |
| ν̂ vs $\hat{\nu}$ prose consistency | — | — | LOW (#6) | LOW | NO — Task 19 |
| Handoff-metadata missing scipy version | — | LOW (gap 2) | — | LOW | NO — Task 22 |

---

## 2. Task 23-scoped remediations (APPLIED)

### R1 — §12 interp-md pooled-mean linearisation caveat

**Applied in commit following this note.** Three reviewers converged on the claim that the pooled-sample anchor ȳ_weekly understates the regime-conditional magnitude by up to 1.4× at post-2021 means. The remediated §12 interp-md now:

- Leads with a one-line summary (Tech Writer LOW 7): "the primary mean-channel effect is approximately −0.86 bp per 1-σ CPI surprise on the weekly panel; the co-primary conditional-variance channel contributes 0 bp per 1-σ |CPI surprise| on the daily panel, pinned at the Han-Kristensen 2014 positivity boundary."
- Includes a **Pooled-sample linearisation caveat** paragraph flagging that the pooled ȳ differs from regime-conditional ȳ by ~1.4× and that NB3's forest plot carries the regime-conditional bp/σ.

Two new regression tests added to `test_nb2_section12.py`:
- `test_nb2_section12_has_pooled_mean_caveat` — asserts "pooled" + "regime" tokens in interp-md.
- `test_nb2_section12_has_one_line_summary` — asserts "One-line summary" phrase.

Both green. Full baseline: 628 passed + 2 skipped.

---

## 3. Upstream-task-scoped issues (ESCALATED, not fixed in Task 23)

These 10 findings are NOT in Task 23's scope. Per MEMORY "Agent scope: only named files", Task 23's allowed files are `02_estimation.ipynb` + `test_nb2_section12.py`. Each upstream issue below should become its own plan task:

### E1 — §11 serialization date coercion (HIGH, BLOCKING PHASE 3)

- **Source task:** Task 22 (`nb2_serialize.py::build_payload`)
- **Finding:** Subsamples `date_min` / `date_max` emit `'0'` where ISO date required. `jsonschema.ValidationError` at end-to-end nbconvert.
- **Fix location:** `scripts/nb2_serialize.py::build_payload` subsample-block construction.
- **Recommended fix:** `payload["subsamples"][regime]["date_min"] = str(regime_df["week_start"].min().date())` (or `.strftime("%Y-%m-%d")`).
- **New test needed:** Add an integration test in `test_nb2_serialization.py` that runs the full §11 code cell against the live panel (not just `build_payload` with synthetic inputs).
- **Must be dispatched to Data Engineer before Task 24 (NB3 §1) is scheduled.**

### E2 — `reconcile()` directional vs numerical CI overlap (MEDIUM)

- **Source task:** Task 22 (`nb2_serialize.py::reconcile`)
- **Finding:** Plan line 431 mandates directional concordance (signs + significance classes), not numerical intersection.
- **Fix location:** `scripts/nb2_serialize.py::reconcile` CI-overlap clause.
- **Recommended fix:** Replace the literal intersection test with the significance-class concordance clause: both-reject OR both-fail-to-reject. Combined with the sign-agreement clause (already correct) and the zero-boundary special case (already correct), this matches plan rev 2 semantics.
- **Must be dispatched to Data Engineer alongside E1.**

### E3 — §6 Han-Kristensen boundary-SE caveat (MEDIUM)

- **Source task:** Task 19 (§6 GARCH-X cell)
- **Finding:** When δ̂ = 0 at the positivity boundary, the symmetric 90% CI is not the correct Han-Kristensen 2014 one-sided CI.
- **Fix location:** §6 interp-md — add a paragraph noting the boundary-SE caveat and forward-reference NB3's one-sided-CI sensitivity.
- **No code change required** (the numerical CI is not wrong per se; it's just a reader-facing caveat).
- **Can be dispatched later — does NOT block Phase 3.**

### E4 — §3 OLS ladder caption / HAC(4) context (MEDIUM)

- **Source task:** Task 18 (§3 cell)
- **Finding:** The `summary_col` table has no caption; a reader cannot infer HAC(4) / pre-registered Column 6 from the table alone.
- **Fix location:** §3 interp-md — add one sentence naming the three facts.

### E5 — §6 GARCH-X output DataFrame refactor (MEDIUM)

- **Source task:** Task 19
- **Finding:** `print(...)` wall of ML-SE vs QMLE-SE is not scannable in PDF.
- **Fix location:** §6 code cell — refactor to `pandas.DataFrame` display.

### E6 — §5 Student-t side-by-side with OLS primary (MEDIUM)

- **Source task:** Task 19
- **Finding:** Student-t refit is prose-only; no side-by-side with OLS primary.
- **Fix location:** §5 code cell — `summary_col([column6_fit, t_fit], ...)`.

### E7 — §10 Verdict Box PDF propagation (MEDIUM)

- **Source task:** Task 22
- **Finding:** `display(Markdown(...))` may not propagate to the §1 anchor in PDF rendering.
- **Fix location:** test first in PDF; if broken, add §10 interp-md line explaining runtime-only propagation.

### E8 — ν̂ vs $\hat{\nu}$ prose consistency (LOW)

- **Source task:** Tasks 18-22
- **Finding:** Mixed Unicode and LaTeX inline-math conventions across interp-mds.

### E9 — Handoff-metadata missing scipy version (LOW)

- **Source task:** Task 22
- **Finding:** `default_handoff_metadata()` includes numpy/pandas/statsmodels/arch but not scipy.

### E10 — §5 Student-t should or shouldn't feed reconciliation (LOW-MEDIUM)

- **Source task:** Tasks 19 + 22
- **Finding:** Unclear contract — §5 is advertised as "companion" but §10 doesn't consume it. Resolve the contract one way or the other.

---

## 4. Final reviewer verdicts after Task-23 remediation

| Reviewer | Initial Verdict | After §12 remediation | Final |
|---|---|---|---|
| Model QA | CONDITIONAL PASS | PASS on §12 scope; E1-E3 flagged for upstream | **APPROVE (§12 scope)** |
| Reality Checker | CONDITIONAL PASS | PASS on §12 scope; E1, E2 flagged for upstream | **APPROVE (§12 scope)** |
| Technical Writer | CONDITIONAL PASS | PASS on §12 scope (one-liner + caveat); E4-E8 flagged for upstream | **APPROVE (§12 scope)** |

All three reviewers APPROVE Task 23's §12 work. The upstream findings (E1-E10) are out of Task 23 scope and must be dispatched as separate remediation cycles before Phase 3 (Tasks 24-27) runs.

---

## 5. Phase 2 close status

**Phase 2 Tasks 16-23 — all implemented.**

However, **Phase 3 cannot start until E1 is fixed** (the §11 serialization date coercion): NB3 Task 24 §1 reads `POINT_JSON_PATH` + `FULL_PKL_PATH` which are never written by the current §11. The Phase 2 closure is therefore *conditional on the E1 patch landing before Task 24 is dispatched*.

**Recommendation to user:** Dispatch a Task 22 hotfix (Data Engineer) to address E1 + E2 in one commit, then Phase 3 Task 24 can proceed.

---

## 6. Chasing-offline checklist

- [x] No reviewer narrated offline deliberation in their review.
- [x] Every finding cites a cell index, source line, or live-derived numeric.
- [x] No forbidden substrings appear in any review.
- [x] End-to-end execution of the notebook was attempted (by Reality Checker + Model QA) — not just the test suite.

---

**Analytics Reporter (orchestrator)**
**Date:** 2026-04-19
