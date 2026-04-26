# Phase 5b Analytics Reporter — Senior Developer Review (re-dispatch)

**Commit reviewed:** `799cbc280`
**Reviewer lens:** Senior Developer (API design, code organization, library choice, reproducibility, functional-Python compliance, forward readiness)
**Read-only:** confirmed. No code modified during this review.
**Tool budget:** 13 tool uses (under 15 cap).

---

## Verdict: **PASS-w-adv**

Phase 5b ships a clean, idiomatic, well-typed estimation kernel with sensible orchestration and faithful spec-§11.A discipline. The five forward-readiness advisories below are non-blocking; one cosmetic dead-code/unused-import cluster is flagged for the next refactor pass.

---

## 1. API design of `phase5_analytics.py` — **PASS**

The module is the single best-organized artifact in the Phase-5b drop:

- **Two frozen, slotted dataclasses** (`RegressionResult`, `GateVerdict`) at lines 97–165; both `frozen=True, slots=True` per `functional-python`.
- **Three free pure functions** (`fit_ols_hac`, `fit_bootstrap`, `fit_student_t`) at lines 197/274/346 — keyword-only after `df`, fully typed, no class state.
- **One verdict computer** (`compute_gate_verdict`, line 413) — pure, sign-locked, anti-fishing language baked into the docstring.
- **Estimator vs. serialization separation:** the kernel never produces markdown, never opens files, never imports `Path`. Serialization is entirely owned by the orchestrator. This is the right cut.
- **Public-API surface** is narrow and explicit — `test_public_api_symbols_exposed` (test line 52) pins it, so the contract is testable.

Docstrings are NumPy-style with Parameters/Attributes sections — consistent and readable.

---

## 2. Code-orchestration design (`run_phase5_analytics.py`) — **PASS-w-adv**

The 14-row runner is **idempotent**: writes to a fixed `_OUTPUT_DIR`; no append; `mkdir(parents=True, exist_ok=True)` at line 73. Re-running produces byte-identical output for a given panel + seed.

Row dispatch is cleanly factored into 14 `_build_row_N` functions (lines 993–1175), each producing a `RowOutcome`. Row 14 returns `list[RowOutcome]` for the three sub-rows (14a/14b/14c) — a slight asymmetry but documented in the docstring at line 1148. **Acceptable.**

**Advisory 1 (forward-readiness, non-blocking):** the 14 hand-rolled `_build_row_N` functions have ~80% boilerplate overlap (each calls `fit_ols_hac` with HAC=4, six controls, identical y_col/x_col, then wraps via `_outcome_from_fit`). A data-driven row registry — e.g., a `tuple[RowSpec, ...]` of (row_id, label, panel-filename, estimator, controls, transform, pre_committed_n, notes) plus a single dispatch loop — would collapse ~200 lines of orchestration into a 30-line table. **Not a blocker for Rev-2; flag for Rev-3** when ζ-group adds 4+ new estimators and the table-driven approach becomes load-bearing.

---

## 3. Estimator implementation choices — **PASS-w-adv**

| Estimator | Library used | Verdict |
|---|---|---|
| OLS + HAC(4)/HAC(12) | `statsmodels.api.OLS(...).fit(cov_type="HAC", cov_kwds={"maxlags": k})` | **PASS** — canonical |
| Politis-Romano stationary block bootstrap | hand-rolled `_stationary_block_indices` (line 254) | **PASS-w-adv** (Advisory 2) |
| Student-t MLE refit | `scipy.stats.t.fit(resid, floc=0.0)` + hand-rolled SE scaling | **PASS-w-adv** (Advisory 3) |
| Ljung-Box, Jarque-Bera | `statsmodels.stats.diagnostic.acorr_ljungbox`, `statsmodels.stats.stattools.jarque_bera` | **PASS** — canonical |
| Chow break F-test | hand-rolled pooled-vs-split F (line 355) | **PASS** — canonical |
| Levene's test | `scipy.stats.levene` | **PASS** — canonical |

**Advisory 2 (bootstrap library):** statsmodels does not ship a stationary-block bootstrap helper, but `arch.bootstrap.StationaryBootstrap` (`arch` package) does. The hand-rolled implementation in lines 254–271 is correct (geometric block lengths via `rng.geometric(p)`, circular wrap via `% n`), but it is a non-trivial routine the team will eventually want validated against `arch`'s reference. **Recommend** for Rev-3 either (a) a one-shot equivalence test against `arch.bootstrap.StationaryBootstrap`, OR (b) pin the seeded β̂_boot result as a regression-test fixture so future refactors cannot silently drift.

**Advisory 3 (Student-t SE construction):** `fit_student_t` lines 374–379 compute `σ_t² · (X'X)⁻¹` from the t-MLE scale, a reasonable Student-t-error analogue at the linear-model level. However, this is **not a full Student-t MLE refit of β̂** — β̂ is still OLS; only the SE/inference is heavy-tail-aware. The docstring at line 353 is honest about this ("OLS + Student-t MLE on residual variance"), and `statsmodels.miscmodels.tlinearmodel.TLinearModel` would be the canonical full-likelihood refit. **Acceptable for Rev-2** — but a one-line comment flagging the limitation vs. a true t-likelihood β̂ would help future maintainers.

---

## 4. Test fixture organization — **PASS-w-adv**

17 tests, organized into 9 numbered sections (Section 0 import contract → Section 9 anti-fishing constants), at the consumption seam (`scripts/tests/inequality/test_phase5b_analytics.py`). The seam is correct: tests live where they consume the kernel, not in a parallel test tree.

- **Real-data discipline:** Sections 1, 2, 4–7 read live Phase-5a parquets via `_read_panel_parquet` helper. **`feedback_real_data_over_mocks` satisfied.**
- **Synthetic admissions:** Section 3 (gate-classifier sanity) uses synthetic β/SE — but the docstring at file-line 8–10 explicitly justifies these as "gate-classifier sanity (a known synthetic case where the gate verdict is mathematically determinate)". **Acceptable.**
- **Schema contract test** (Section 8, line 277) defensively skips when `gate_verdict.json` doesn't exist (line 280–281). After a fresh re-run, the file exists and the assertion passes. The `_REQUIRED_GATE_VERDICT_KEYS` set (line 266) pins exactly what the contract guarantees.
- **17 tests / commit-message claims 17/17 passed.** Live count via `grep -c "^def test_"` → **17. Match.**

**Advisory 4 (forward-readiness):** `test_fit_bootstrap_returns_regression_result_on_primary` (line 207) constructs `np.random.default_rng(42)` but does NOT pin the resulting β̂_boot or se_boot to a known value. Adding `assert result.beta_hat == pytest.approx(EXPECTED_BOOT_BETA, rel=1e-9)` would lock the entire bootstrap + RNG plumbing as a regression test, catching any silent drift in `_stationary_block_indices`. **Recommend for Rev-3.**

---

## 5. Functional-Python compliance — **PASS**

| Rule | Status |
|---|---|
| Frozen dataclasses | ✓ both `RegressionResult` and `GateVerdict` are `frozen=True, slots=True` |
| Free pure functions | ✓ `fit_ols_hac`, `fit_bootstrap`, `fit_student_t`, `compute_gate_verdict` are all module-level free functions |
| Full typing | ✓ all signatures fully annotated; `Sequence[str]` for control_cols, `Final[float]` for constants, `np.random.Generator | None` for optional RNG |
| No inheritance | ✓ no `class Foo(Bar)` anywhere |
| Composition over hierarchy | ✓ `RowOutcome` composes `RegressionResult` + `GateVerdict` |

The orchestrator adds two more frozen/slotted dataclasses (`RowOutcome` line 114, `SpecTestResults` line 251) — same compliance.

---

## 6. Reproducibility (bootstrap seeding) — **PASS-w-adv**

`_build_row_2` at line 1004–1014 uses `rng = np.random.default_rng(20260426)` — a **fixed integer seed** (the dispatch date). The seed is hard-coded, not env-derived, not time-derived. The bootstrap is fully deterministic given:

1. Phase-5a Row-2 panel parquet (immutable; commit `2eed63994`)
2. Seed `20260426` (immutable; line 1005)
3. `n_resamples=10_000` (default constant)
4. `mean_block_length=4` (default constant)

**Anti-fishing reproducibility requirement satisfied.** The `gate_verdict.json` `bootstrap_reconciliation.beta_hat = -2.7987050503705652e-08` is bit-exactly reproducible.

**Advisory 5 (provenance):** `gate_verdict.json` should include `bootstrap_reconciliation.seed = 20260426` (currently absent). RC and CR will reach for this when independently reproducing the bootstrap; today they have to read line 1005 of the orchestrator. **Trivial JSON-emit fix; non-blocking; flag for Rev-3 cleanup.**

---

## 7. Pre-existing-failure disclosure — **PASS**

Per Phase-5a RC's advisory, `test_y3_br_bcb_wire.py` carries a fixture-collision footgun. Phase 5b adds **only** `test_phase5b_analytics.py` (17 new tests in `scripts/tests/inequality/`); it does NOT modify `test_y3_br_bcb_wire.py` or any other existing test file. Verified via `git show 799cbc280 --stat` — only `test_phase5b_analytics.py` is added under `tests/`.

**No new failures introduced.** The pre-existing fixture-collision footgun is unchanged. Scope discipline (`feedback_agent_scope`, `feedback_scripts_only_scope`) preserved: only `scripts/`, `scripts/tests/`, and `.scratch/` touched.

---

## 8. Convex-payoff caveat handling (`summary.md` §11.A reproduction) — **PASS (cosmetic nit)**

`summary.md` lines 51–60 reproduce the spec §11.A discipline faithfully across all four numbered points. Framing is correct: "Mean-β identification is necessary-but-insufficient for convex-payoff pricing." No over-claim ("FAIL means thesis is wrong") detected — the report consistently frames FAIL as "consistent with predictive-not-structural-and-mean-β-not-tail-β" via the T1-rejects + §11.A combination.

The convex-payoff caveat in `gate_verdict.json` line 9 is also faithfully reproduced.

**Cosmetic nit (NON-BLOCKING):** `summary.md` line 58 reads:

> 4. **Honest interpretation of the T3b PASS result:** "Y₃'s mean shifts with X_d in a direction consistent with the linear-hedge thesis" — NOT "Abrigo can price options from this β̂."

This bullet was authored as a hypothetical-PASS framing, but the actual T3b verdict is FAIL. The bullet is literal-correct (it's about "the T3b PASS result" hypothetically), but a future skim-reader could briefly think a PASS was achieved. The headline at line 11 ("**FAIL**") and the §11.A framing at line 53 ("A T3b PASS at the mean-β level is **necessary but NOT sufficient**") are unambiguous, so this is purely cosmetic. Suggest "Honest interpretation of the T3b verdict (PASS or FAIL)" in a future polish pass.

---

## 9. HALT discipline (T1 + T3b → user routing) — **PASS**

Both HALT-to-user paths are routed correctly:

- **T1 REJECTS → predictive-flag (FX-vol Finding 14):** `summary.md` line 26 → "β̂ is **PREDICTIVE**". `spec_tests.md` lines 681–684 carry the explicit HALT discipline section: *"Per FX-vol Finding 14, β̂ is now interpreted as a *predictive-regression* coefficient, NOT a strict-impulse parameter. Product framing must update to reflect this; the simulator-calibration claim at spec §12 is bounded by this interpretation."* `gate_verdict.json` field `spec_tests.t7_predictive_or_structural = "predictive"`. **Routed.**
- **T3b FAIL → gate-FAIL discipline:** `summary.md` line 11 ("**FAIL**"); `gate_verdict.json` `gate_verdict = "FAIL"`; `summary.md` Pivot Paths section (lines 63–75) explicitly enumerates Rev-3 ζ-group + brainstorm-α/β paths. **Routed.**

The anti-fishing audit (lines 39–48 of `summary.md`) re-asserts all 8 invariants verbatim. No silent-glossing detected.

---

## 10. Forward readiness for Rev-3 ζ-group — **PASS-w-adv**

The Phase-5b kernel is shaped correctly to host Rev-3 ζ-group estimators:

- New estimators (quantile regression, GARCH(1,1)-X, lower-tail conditional, option-IV surface) all return a single β̂ + SE + inference object → they fit the existing `RegressionResult` shape.
- The gate is sign-locked at `compute_gate_verdict` — Rev-3 quantile regressions can call the same gate with a per-τ β̂.
- The orchestrator's row-dispatch pattern extends naturally (the `_build_row_N` functions are independent units).

**What's MISSING for Rev-3 ζ-group (gap flag):**

1. **Quantile-regression adapter** — `statsmodels.regression.quantile_regression.QuantReg` is the canonical hook; no current adapter in `phase5_analytics.py`. **Net-new estimator; expected.**
2. **GARCH(1,1)-X adapter** — `arch.univariate.ConstantMean` + `arch.univariate.GARCH` is the canonical hook; no current adapter. **Net-new estimator; expected.**
3. **Multi-τ output schema** — current `gate_verdict.json` is single-row (Row-1) shaped. Rev-3 will need to emit a **per-τ** verdict array (or a `gate_verdict_zeta.json` companion). **Trivial schema extension; flag for Rev-3 spec.**
4. **Bootstrap seed in JSON** — see Advisory 5.

None of these block Rev-2 sign-off. They define the Rev-3 entry-task.

---

## Cosmetic / housekeeping flags (non-blocking)

These minor smells do **not** affect correctness, gate verdict, or anti-fishing invariants. Listed for the next refactor pass:

1. **Dead helper:** `_design_matrix` at `phase5_analytics.py` lines 173–189 is never called from anywhere in the codebase (verified via `grep "_design_matrix"`). The body contains odd defensive code (`if False:` guard at line 181, unused `del y` at line 182, double-assignment of `y_series` at lines 183 and 185). **Remove the entire helper.**
2. **Unused imports** in `run_phase5_analytics.py` (verified via `grep`):
   - `from dataclasses import ... field, asdict` — `asdict` and `field` are never called
   - `from statsmodels.stats.diagnostic import ... het_breuschpagan, linear_reset` — neither is used (Model QA's BP heteroskedasticity finding is downstream, not in this script)
   - `from scripts.phase5_analytics import ALPHA_ONE_SIDED` — imported but not referenced
3. **Test-count framing in `summary.md` line 87:** reads "16 passed, 1 schema-conformance check" — the actual file has 17 `def test_` functions (including the schema-conformance check). The "16 + 1 = 17" framing is fine but slightly opaque. The commit-message claim "17/17 passed" is more accurate; align.

---

## Summary scorecard

| Lens | Verdict |
|---|---|
| 1. API design of `phase5_analytics.py` | PASS |
| 2. Code orchestration (`run_phase5_analytics.py`) | PASS-w-adv (Adv 1: row-registry refactor for Rev-3) |
| 3. Estimator library choice | PASS-w-adv (Adv 2: arch.bootstrap parity test; Adv 3: Student-t SE limitation comment) |
| 4. Test fixture organization | PASS-w-adv (Adv 4: pin a seeded β̂_boot regression value) |
| 5. Functional-Python compliance | PASS |
| 6. Reproducibility (bootstrap seed) | PASS-w-adv (Adv 5: emit seed into gate_verdict.json) |
| 7. Pre-existing-failure disclosure | PASS — no new failures introduced |
| 8. Convex-payoff caveat handling | PASS (cosmetic nit on §11.A bullet 4 wording) |
| 9. HALT discipline (T1 + T3b → user) | PASS |
| 10. Forward readiness for Rev-3 ζ-group | PASS-w-adv (gap: per-τ schema, GARCH/quantile adapters) |

**Overall: PASS-w-adv.** Five forward-readiness advisories captured. None gate-bearing. The Phase-5b drop is production-quality kernel + orchestrator code, faithfully ships the spec §11.A discipline, preserves all 8 anti-fishing invariants, and routes both HALT signals (T1 REJECTS → predictive-flag, T3b FAIL → gate-FAIL discipline) to the user via the artifacts. Recommend proceeding with the Rev-3 ζ-group entry-task once CR re-dispatch lands.

---

## Files reviewed (absolute paths)

- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/phase5_analytics.py` (433 lines)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/run_phase5_analytics.py` (1362 lines)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/tests/inequality/test_phase5b_analytics.py` (325 lines, 17 tests)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-analysis/summary.md` (90 lines)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-analysis/gate_verdict.json` (39 lines)

**Reviewer signature:** Senior Developer (re-dispatch); 2026-04-26.
