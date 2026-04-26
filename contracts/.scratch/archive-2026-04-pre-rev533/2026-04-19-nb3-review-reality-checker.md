# NB3 Review — Reality Checker (Adversarial)

**Artifact under review:** `notebooks/fx_vol_cpi_surprise/Colombia/03_tests_and_sensitivity.ipynb` (34 cells, 1,888 JSON lines) + `scripts/gate_aggregate.py` (245 lines) + `scripts/render_readme.py` (300 lines) + `estimates/gate_verdict.json` + `README.md` (62 lines) + 7 NB3 test files + 3 end-to-end tests.

**Reviewer:** Reality Checker (third prong of Task 31 three-way gate).

**Default posture:** DOUBT. The review assumes premature approvals, silent-test-pass patterns, fantasy claims, and spurious significance until overwhelming evidence clears each concern.

---

## Verdict

**CONDITIONAL PASS.**

The gate-verdict claim (`gate_verdict = "FAIL"`) is internally consistent, numerically reproducible, and supported by byte-identical README regeneration against committed JSON. T3b FAIL is scientifically honest. The anti-fishing halt in §9 is well-grounded and text-verified. The integration tests run real `nbconvert --execute` subprocesses (not stubs).

BUT four material concerns land short of a clean PASS:

1. **A1 sample-window violation (methodological):** A1 monthly sensitivity silently includes 60 pre-sample observations (2003-2007) that violate Decision #1's pre-committed 2008-01-02 lower bound. Not tested. The A1 positive-significant CI is reported without the Decision-#1 filter.
2. **§10 cell source not executed live in tests:** `test_nb3_section10_gate.py` tests `build_gate_verdict` + `write_gate_verdict_atomic` against *synthetic* inputs only. The live §10 cell chain (verdict normalisation, bootstrap re-derivation, file write) is only exercised by `test_nb3_nbconvert_executes_cleanly` — which catches crashes but not silent logical drift.
3. **Prose-vs-code drift in §2 cell 8:** Interpretation text promises `t1_pvalue` and `t1_source` fields in `gate_verdict.json` that are NOT emitted by cell 31 code; also promises an Abrigo-simulator "predictive-regression interpretation flag" that does not exist in any downstream artifact.
4. **Forest-plot title drift between §8 and the committed PNG:** cell 25 (in-notebook) uses Unicode title "NB3 §8 forest plot — primary anchor + 12 sensitivities (engine: matplotlib-fallback)"; cell 33 (PNG written to `figures/forest_plot.png`) uses ASCII "NB3 sec 8 forest plot -- primary anchor + 12 sensitivities". README image caption "NB3 §8 sensitivity forest plot" matches neither.

None of the four BLOCK publication of the gate verdict. Items (1) and (2) deserve follow-up tasks; (3) and (4) are documentation polish.

---

## Top 5 BLOCKER findings

### BLOCKER 1 — A1 sample-window spec violation (cell 25, medium severity)

**File+cell:** `03_tests_and_sensitivity.ipynb` cell 25 (§8 sensitivity forest), lines reading `_monthly_panel = econ_query_api.get_monthly_panel(conn)` and the merge with `_monthly_surp`.

**Evidence (live, reproduced this review):**
```
A1 (2003-2026, full panel): beta=+0.013134, se=0.005551, n=280
  90% CI = [+0.004002, +0.022265]
A1 (2008-2026, Decision #1 spec window): beta=+0.015155, se=0.005730, n=220
  90% CI = [+0.005728, +0.024581]
```

The committed A1 row uses n=280, which includes 60 months of 2003-01 through 2007-12 (verified via `get_monthly_panel` direct query). Decision #1 pre-committed the sample to 2008-01-02 → 2026-03-01. The notebook's A1 therefore quietly expands the identifying sample by 27% (60/220) without a pre-registered deviation.

**Why it matters:** A1 is one of only TWO rows in the forest plot whose 90% CI excludes zero. The committed A1 headline number lives in the forest-plot PNG and is cited verbatim in cell 29 ("A1 monthly cadence and A4 release-day-excluded are the two rows with 90% CI excluding zero"). Both the plot and the prose would change on a spec-compliant refit. The verdict direction does not change on this specific sample expansion (both windows give positive-significant), but the prose is unaware that the reported sample is not spec-compliant.

**Severity:** MEDIUM. Does not flip gate verdict (T3b is primary; anti-fishing halt already blocks A1 from being spotlighted). Does expose the notebook to a future reviewer question "why is A1 n=280 when the spec window gives n=220?" that has no ready answer.

**Silent-test-pass class:** Same family as Task 22 E1. The sample-window filter is absent from the notebook AND absent from the test (`test_nb3_section7_8.py` only checks that `get_monthly_panel` is referenced, not that a start-date is passed).

### BLOCKER 2 — §10 cell live execution untested (cell 31, medium severity)

**File+cell:** `scripts/tests/test_nb3_section10_gate.py` + notebook cell 31.

**Evidence:** `test_nb3_section10_gate.py` executes:
- Lines 296-436: every test calls `build_gate_verdict(_synthetic_*_inputs())` — inputs are hand-authored dicts, NOT inputs derived from running the live notebook cells.
- Lines 500-557: every atomic-write test uses `tmp_path` + a synthetic `verdict_dict`, never the notebook's §10 output.
- Lines 562-606: three structural tests (cell count, `section:10` tag presence, ankelPeters2024 bib key). All parse JSON — no execution.

Compare to §5/§7/§8/§9 tests, which concatenate a `_make_bootstrap()` string with the cell source and run `exec(compile(...))` to actually invoke the cell code on the live PKL.

The only live execution of cell 31 is `test_nb3_nbconvert_executes_cleanly` which only asserts exit code 0 + stderr does not contain `NameError`.

**Failure mode that escapes coverage:**
- Cell 31 builds `_gate_inputs` dict with 12 keys from in-notebook variables (`_t1_final`, `_t2_final`, ..., `_bootstrap_hac`, `_reconciliation`, `_movers_count`, `pkl_degraded`).
- Any logical error in those normalisations (e.g. swapping the direction of T2's REJECT → PASS map, or mis-spelling `_levene_verdict` as `_t2_verdict` in the if/elif chain) would silently produce a wrong JSON and no test would flag it.
- The ONLY protection is `test_readme_byte_identical_to_committed`, which would fail if gate_verdict.json content drifts — but that test SKIPs when either file is missing (line 494-503). A CI environment that only clones but never runs NB3 would skip the diff check entirely and all 30+ synthetic-input tests pass green.

**Severity:** MEDIUM. The live JSON on disk is numerically correct (verified in this review). But the test suite's trust anchor is the committed artifacts, not a live derivation — so a mal-crafted notebook that emits a matching-but-wrong JSON and a matching-but-wrong README would pass all tests.

### BLOCKER 3 — Prose-vs-code drift in cell 8 (minor severity)

**File+cell:** cell 8 (markdown interpretation of §2 T1).

**Claim in cell 8:** "The gate verdict writer in §10 records `t1_pvalue = 1.3e-09, t1_verdict = REJECT, t1_source = s_cpi_lag1` into `gate_verdict.json`."

**Reality (committed gate_verdict.json):**
```json
{
  "bootstrap_hac_agreement": "AGREEMENT",
  "gate_verdict": "FAIL",
  "material_movers_count": 0,
  "pkl_degraded": false,
  "reconciliation": "AGREE",
  "t1_verdict": "FAIL",      ← only this T1 field
  ...
}
```

No `t1_pvalue`. No `t1_source`. Cell 31 code does NOT write those fields. The gate_aggregate `build_gate_verdict` signature also does not accept them.

Further claim in same cell: "the Abrigo simulator's CPI-response calibration carries a 'predictive-regression interpretation' flag alongside β̂ rather than the stricter 'impulse-response' flag" — this flag appears nowhere in the emitted JSON, the README, or any downstream artifact.

**Severity:** MINOR. Prose over-promises schema. Does not affect gate verdict correctness. Should be trimmed in a documentation task.

### BLOCKER 4 — Forest plot title drift between in-notebook and PNG (cosmetic)

**File+cells:** cell 25 (in-notebook render) vs cell 33 (PNG render saved to disk).

**Evidence:**
- Cell 25 `set_title`: `"NB3 §8 forest plot — primary anchor + 12 sensitivities (engine: {_engine})"` — Unicode § and em-dash, engine suffix.
- Cell 33 `set_title`: `"NB3 sec 8 forest plot -- primary anchor + 12 sensitivities"` — ASCII only, no engine info.
- README.md caption: `"NB3 §8 sensitivity forest plot — primary anchor + 12 sensitivities"` — different again (includes "sensitivity" word, no engine).

The PNG file on disk (`figures/forest_plot.png`, 93,779 bytes, 979×757) has the ASCII cell-33 title. A reader following the README's image link sees a title that neither matches the caption text nor the in-notebook rendering.

**Severity:** COSMETIC. The 14 data rows are identical across both renderings (verified by reading the PNG — 1 primary + 13 sensitivities in the expected vertical layout).

### BLOCKER 5 — Pre-flight pkl_degraded check silently misses venv misactivation

**File+cell:** cell 4 (§1 pre-flight, `pkl_degraded` detection).

**Evidence:** Running this review session's pre-venv-activation Python (`/usr/bin/python3`) showed major.minor mismatch: handoff pinned `3.13.5`, runtime `3.14`. Under `pkl_degraded = True`, cells §4-§9 skip their statsmodels/arch consumption and §10 maps every T-test to `SKIPPED`. The gate aggregator then requires T1=PASS, T2=PASS, T3b=PASS, T7=PASS to emit PASS; under SKIPPED for all, it emits FAIL. So the ultimate answer is still FAIL, but the JSON would contain `t1_verdict=SKIPPED`, `t4_verdict=SKIPPED`, ..., with `pkl_degraded=true`.

`test_nb3_nbconvert_executes_cleanly` uses `sys.executable` — whatever the pytest invoker ran under. In a venv-activated shell the test passes and the gate is derived from live PKL; in a bare-python shell the test passes AND emits a degraded JSON full of SKIPPED tokens. Both outcomes are "exit 0 + no NameError", so nothing raises.

**Severity:** LOW. The venv activation requirement is documented in CLAUDE.md and the project has existing guardrails. But this is a silent-test-pass class: a CI environment that does not activate the venv would commit a misleading gate_verdict.json and the test suite would stay green.

---

## Attack vectors A-H

### A. Silent-test-pass patterns

**Finding (supports BLOCKER 2).** The §10 gate tests do not execute cell 31 live. Specifically:
- `test_gate_aggregate_module_imports` through `test_gate_aggregate_fail_when_t7_fail` (lines 296-495): all 14 tests call `build_gate_verdict(synthetic_dict)`. None test that the dict the NOTEBOOK assembles at cell 31 runtime matches the synthetic shape.
- `test_atomic_write_*` (lines 500-557): use `tmp_path` + synthetic verdict. Do not test the real `env.GATE_VERDICT_PATH` write.
- `test_nb3_has_task29_cell_count` (lines 562-568): cell-count only. Does not execute.
- `test_nb3_section10_*` (lines 571-606): tag presence, citation bib key presence. Do not execute.
- `test_nb3_citation_lint_passes_after_task29` (lines 611-625): lint subprocess. Does not execute cells.

Contrast §5/§7/§8/§9 tests which call `exec(compile(bootstrap_source + cell_source, ...))` on the LIVE PKL. That pattern was adopted after Task 25/Task 27 taught the project what "structural only" tests miss. §10 is the one section that reverted to the synthetic-only pattern.

**Also:** `test_render_readme.py::test_readme_byte_identical_to_committed` SKIPS if `GATE_VERDICT_PATH.is_file()` is false (line 494). A cold-clone CI that has not run NB3 would skip this one load-bearing test entirely.

### B. Gate verdict claim integrity

**Finding: no drift.** Running `scripts/render_readme.py` against the committed JSONs produces a 3,429-byte output byte-identical to the committed `README.md`. The T3b FAIL determination (β̂ − 1.28·SE = −0.002981 < 0) is numerically consistent with the committed `ols_primary.beta.cpi_surprise_ar1 = −0.000685131999464896` and `ols_primary.se.cpi_surprise_ar1 = 0.0017935935601703335`. Verified: t ≈ −0.382, two-sided p ≈ 0.703, 90% CI = [−0.003636, +0.002265]. All published headline numbers reproduce.

### C. README byte-identical CI check

**Finding: test is real but brittle.** Verified:
- `test_render_readme_cli` (line 452-487) runs the actual CLI as a subprocess and compares stdout to the pure-function output. Good.
- `test_readme_byte_identical_to_committed` does a direct string comparison, NOT a `diff` subprocess. It reads both files with `encoding="utf-8"` and compares `committed == rendered`. Newline / BOM / encoding drift would surface.
- BUT: the test uses `pytest.skip()` when either JSON is missing (lines 494-503). Any CI mode that ships the committed README without running the JSON generators will skip this check silently.

No finding that makes the check "fake" — it genuinely compares bytes. One brittleness: the skip-on-missing pattern is itself a silent-test-pass vector.

### D. A1/A4 significant results — spurious?

**Finding (partial): A1 reported on an over-wide window (see BLOCKER 1).**
Live re-fit, this session:
- A1 with 2003-2026 (as notebook runs): β̂ = +0.013134, 90% CI = [+0.004, +0.022], n=280.
- A1 with 2008-2026 (Decision #1 spec): β̂ = +0.015155, 90% CI = [+0.006, +0.025], n=220.
- A4 release-day-excluded: β̂ = +0.003309, 90% CI = [+0.000464, +0.006155], n=947.

A4 uses the spec-compliant weekly window and its sign flip relative to primary is genuine: excluding release days, CPI surprise has a small but positive HAC-significant loading on non-release-day RV^(1/3). Economically unintuitive (one would expect release-day vol to CARRY the surprise loading) but reproducible.

A1 result is robust to the sample-window correction — the notebook's over-wide sample produces a slightly smaller positive coefficient than the spec-compliant one, not a spurious one. So the "A1 significant" headline is NOT spurious but IS reported on a methodologically nonconforming sample.

The anti-fishing halt in §9 correctly refuses to promote either A1 or A4 to a spotlight, citing Simonsohn-Simmons-Nelson 2020 and Ankel-Peters-Brodeur-Connolly 2024. That discipline is the decisive protection against spurious-result promotion, independent of any sample-window issue.

### E. Forest plot correctness

**Finding: plot depicts 14 rows correctly; title drift is the only issue (see BLOCKER 4).** Visual inspection of `figures/forest_plot.png` (979×757 RGBA PNG):
- Row 1 (primary, anchored above horizontal divider): "Primary (Column 6, HAC(4)) (n=947)" with CI bracketing zero around −0.000685.
- Rows 2-14 ordered by |β̂| descending: A1 monthly (top, CI clearly positive-excluding-zero), A9− negative-surprise, Subsample 2015-2021 (CI negative-excluding-zero), A9+ positive-surprise (wide whiskers, n=13 degrades spec via bivariate fallback), A4 release-day-excluded (CI just clears zero positive), 3 subsamples, A5 lagged-RV, A6 bivariate, A8 oil-level, Decomp β̂_CPI, Decomp β̂_PPI, GARCH-X δ̂_CPI (effectively zero-point with invisible whiskers due to QMLE 2.96e-37 variance floor).
- 14 total — 1 primary + 13 sensitivities. Matches the `_FOREST_EXPECTED_ROWS = 14` constant in `test_nb3_section7_8.py` line 155.

The rendering is correct. Only the PNG's title string differs from the in-notebook version and the README caption.

### F. Anti-fishing HALT correctness

**Finding: no drift.** Live T3b re-derivation in cell 28 reads `column6_fit.params["cpi_surprise_ar1"]` and `column6_fit.bse["cpi_surprise_ar1"]` directly from the PKL and recomputes `_t3b_statistic = _beta_cpi_primary - 1.28 * _se_cpi_primary`. Using the committed ols_primary values: −0.000685 − 1.28 × 0.001794 = −0.002981. Matches the NB2 §9 gate statement verbatim.

`T3B_GATE_VERDICT = "FAIL"` fires in cell 28 naturally from the live PKL; the halt branch binds `SPOTLIGHT_STATUS = "halted_on_gate_fail"` and `material_movers = []`. If a future reviewer hand-edited `gate_verdict.json` to `t3b_verdict = "PASS"` without also changing the PKL, §9 would still halt because it reads from `column6_fit`, not from the JSON. That's the right direction of coupling (live over static).

The synthetic PASS branch in `test_nb3_section9_helper_applies_two_pronged_rule_both_prongs` (lines 482-503) exercises the counterfactual. Note that `_compute_material_movers` IGNORES the `classification` key on the input dict and recomputes it via `_classify_t3b(beta, se)`; the synthetic fixture's passed-in classifications are therefore cosmetic. The test still passes because `s_both` has β̂ = −0.030 which clearly flips the primary's positive-significant class, regardless of the passed label. Design smell but not a bug.

### G. Citation integrity

**Finding: no drift.** Verified:
- Andersen-Bollerslev-Diebold-Vega 2003 → `@andersen2003micro` present in `references.bib` line 44.
- Simonsohn-Simmons-Nelson 2020 → `@simonsohn2020specification` present line 483.
- Ankel-Peters-Brodeur-Connolly 2024 → `@ankelPeters2024protocol` present line 93.
- Chow 1960 → `@chow1960tests` present line 225.
- Leamer 1983 "Let's Take the Con Out of Econometrics" AER 73(1):31-43 — REAL paper, correct title, correct journal, correct vol/issue/pages.
- Leamer 1985 "Sensitivity Analyses Would Help" AER 75(3):308-313 — REAL paper, correct title, correct journal, correct vol/issue/pages. Both papers are foundational in the EBA / extreme-bounds-analysis literature. Leamer citations appear in prose only (no bib key) in cells 27 and 30; `test_nb3_section9_citation_references_leamer` accepts either form.
- `scripts/lint_notebook_citations.py` exits 0 on NB3.

### H. Three integration tests actually integrated?

**Finding: all three are real subprocess tests.** Read each:
- `test_nb1_end_to_end_execution.py` lines 144-165: `subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", ...])` with real prerequisite checks (DuckDB file, pre-registration doc hash target) and `result.returncode == 0` + `"ModuleNotFoundError" not in result.stderr` + `"NameError" not in result.stderr` assertions.
- `test_nb2_end_to_end_execution.py`: same pattern (read the one for NB3 which mirrors it directly).
- `test_nb3_end_to_end_execution.py` lines 130-173: identical subprocess call, checks NB2 handoff JSON + PKL + DuckDB presence before invoking nbconvert.

Timeout is `env.NBCONVERT_TIMEOUT = 1800` (30 min) per test. Real `jupyter nbconvert --to notebook --execute` runs with `--ExecutePreprocessor.timeout=1800`. No mocks, no stubs. These tests are what they claim to be.

The only gap: they assert exit code 0 and absence of two specific error substrings (`NameError`, `ModuleNotFoundError`). They do NOT assert specific output values or check that `gate_verdict.json` was updated on disk. That coverage is spread across the per-section tests + the byte-identity README check.

---

## Silent-test-pass patterns found

1. **§10 cell source not live-executed** (see BLOCKER 2 + attack A). The single highest-risk pattern in the NB3 test suite.
2. **Byte-identity check skip-on-missing** (`test_readme_byte_identical_to_committed` line 494-503). A cold CI clone that does not run NB3 would skip this test silently.
3. **Venv activation assumption** (BLOCKER 5). Tests run under whatever Python invoked them; a misactivated venv turns every per-test verdict to SKIPPED and the notebook still exits 0.
4. **Synthetic classification shadowing in §9 helper test.** The `_compute_material_movers` helper ignores the `classification` key in input rows and recomputes via `_classify_t3b(beta, se)`. The synthetic fixture passes classifications that are *consistent* with the recomputed values for s_both, but if a future refactor broke the recomputation, the synthetic test might still pass because the passed classifications happen to be correct. Design smell; not a current bug.
5. **A1 sample-window silently wide** (BLOCKER 1). No test compares n_a1 against the Decision #1 spec window.

---

## Spot-check verifications run

| # | Claim | Result |
|---|---|---|
| 1 | Committed `gate_verdict.json` matches notebook emission | Verified by running `render_readme.py` — byte-identical README output (3,429 bytes both ways). |
| 2 | T3b statistic: β̂ − 1.28·SE = −0.002981 | Verified numerically from committed `nb2_params_point.json`. |
| 3 | Two-sided t-stat ≈ −0.382 | Verified: −0.000685131999464896 / 0.0017935935601703335 = −0.381988. |
| 4 | 90% HAC CI = [−0.003635, +0.002265] | Verified: ±1.645·SE brackets. |
| 5 | T7 ratio ≈ 0.91 ("TIGHT PASS") | Verified: \|−0.000685 − (+0.000940)\| / 0.001794 = 0.9058. |
| 6 | T6 break dates [2009-10-26, 2014-08-11, 2016-09-19] | Verified by re-running `ruptures.Binseg(model='rbf').fit(column6_fit.resid).predict(n_bkps=3)`. Exact match. |
| 7 | A1 monthly β̂ and CI | Verified live: β̂ = +0.013134, 90% CI = [+0.004002, +0.022265], n=280. |
| 8 | A4 release-day-excluded β̂ and CI | Verified live: β̂ = +0.003309, 90% CI = [+0.000464, +0.006155], n=947. |
| 9 | A1 spec-compliant window (2008-2026) | Re-fitted: β̂ = +0.015155, n=220 — confirms BLOCKER 1. |
| 10 | Forest plot PNG has 14 rows | Visually confirmed from 979×757 RGBA PNG. |
| 11 | References.bib has all cited keys | Verified: andersen2003micro, ankelPeters2024protocol, chow1960tests, simonsohn2020specification. Leamer intentionally prose-only. |
| 12 | Leamer 1983 and 1985 are real papers | Verified: both are foundational AER articles on extreme-bounds analysis, titles/volumes/pages correct. |
| 13 | `lint_notebook_citations.py` exits 0 on NB3 | Verified. |
| 14 | `get_rv_excluding_release_day` excludes both CPI and PPI days | Verified in SQL at `econ_query_api.py` line 507. |
| 15 | `get_monthly_panel` does NOT expose `us_cpi_surprise` or `banrep_rate_surprise` | Verified by column listing: only `month_start, rv_monthly, rv_monthly_cuberoot, rv_monthly_log, n_trading_days, dane_ipc_pct, dane_ipp_pct, vix_avg, oil_return, intervention_dummy, intervention_amount`. A1 scope reduction is forced by the query API, not a choice. |
| 16 | Venv runtime matches handoff metadata | Verified in the `.venv`: Python 3.13.5, statsmodels 0.14.6, arch 8.0.0, numpy 2.4.4, pandas 3.0.2, scipy 1.17.1. Outside venv (system Python 3.14): major.minor mismatch → pkl_degraded=True (BLOCKER 5). |
| 17 | Cell 31's `_gate_inputs` keys match the 12 required by `build_gate_verdict` | Verified via source read: t1_verdict, t2_verdict, t3a_verdict, t3b_verdict, t4_verdict, t5_verdict, t6_verdict, t7_verdict, material_movers_count, reconciliation, bootstrap_hac_agreement, pkl_degraded. All 12 present. |
| 18 | `_forest_table` flows cell 25 → 28 → 33 | Verified by source grep: cell 25 creates, cell 28 (§9) reads into `_appendix` and `_sens_rows`, cell 33 re-plots to PNG. Kernel-state coupling; safe under `nbconvert --execute`, fragile under partial re-runs. |
| 19 | `t3a_verdict = "FAIL TO REJECT"` is valid in the schema | Verified: `build_gate_verdict` accepts t3a as free string (no `_VALID_VERDICTS` check for that field). |
| 20 | Cell 31 atomic-write pattern matches `scripts.nb2_serialize` | Verified by reading `scripts/gate_aggregate.py` lines 182-245: `_fsync_dir` helper + stage → fsync → `os.replace` → fsync-dir sequence. Rollback on OSError with best-effort tmp cleanup. |

---

## Adversarial findings uniquely surfaced (not Model QA / Technical Writer territory)

1. **A1 sample-window spec violation** (BLOCKER 1) — pure methodological audit against Decision #1's pre-committed 2008-01-02 lower bound. Model QA would check the regression specification; Technical Writer would check prose clarity. Only a spec-adherence audit catches that `get_monthly_panel` pulls 60 pre-sample months and the notebook does not filter.

2. **§10 cell-level execution gap** (BLOCKER 2) — requires cross-comparing the NB3 test files' exec patterns. §5/§7/§8/§9 test files use `exec(compile(bootstrap + cell_source))`. §10 test file uses synthetic-dict-only. Only a test-architecture adversary spots that one file bucked the pattern.

3. **Prose-vs-code drift in cell 8** (BLOCKER 3) — cross-referencing interpretation prose against the actual JSON schema. Technical Writer would review prose for clarity; only a reality checker matching every promise against committed artifact schema spots the phantom `t1_pvalue`/`t1_source`/`predictive-regression-interpretation-flag` fields.

4. **Forest-plot title drift across three surfaces** (BLOCKER 4) — requires comparing the in-notebook render (cell 25), the disk PNG (cell 33), and the README image caption. None are wrong individually; they're mutually inconsistent. Visual-artifact audit specific to reality checking.

5. **Venv misactivation silent-pass** (BLOCKER 5) — requires testing outside the venv and noticing that pkl_degraded would silently cascade to all-SKIPPED verdicts that still exit 0. Process-environment adversary specific.

6. **`_compute_material_movers` shadowing its input classifications** (attack F finding) — the function signature accepts rows with `classification` keys but internally ignores them and recomputes. Passing synthetic fixtures with pre-computed classifications masks the bug where the function never needed the `classification` key at all. Test works; design smells.

---

## Recommendation

**NB3 deserves CONDITIONAL PASS for Task 31 merge.** The gate verdict claim FAIL is empirically correct, scientifically honest, and rendered byte-identically into the committed README. The T3b primary, T1/T2/T4/T5/T6/T7 gates, reconciliation status, bootstrap-HAC agreement flag, and material-mover count all reproduce on re-derivation. The anti-fishing discipline in §9 is the strongest protection in the entire pipeline against the kind of spurious-result promotion that would otherwise turn A1's positive monthly CI into a product headline.

Conditional on three follow-up items:

1. **Document the A1 sample-window deviation** (BLOCKER 1) — either refit A1 on the Decision #1 window (n=220, updating the PNG + prose), or add an explicit pre-registered deviation note to `.scratch/2026-04-18-nb3-sensitivity-preregistration.md` acknowledging that A1 uses the full monthly-panel span for power reasons and hashing that decision into the panel fingerprint. Either resolution is defensible; the current silent inclusion of 60 pre-sample months is not.

2. **Add live §10 execution test** (BLOCKER 2) — extend `test_nb3_section10_gate.py` with an `exec(compile(bootstrap + s4 + s5 + s6 + s10_source))` test that asserts the `gate_verdict_dict` bound by cell 31 has the expected shape under live PKL. Bring §10 into parity with §5/§7/§8/§9 coverage.

3. **Trim cell 8 prose** (BLOCKER 3) — remove the `t1_pvalue`/`t1_source`/`predictive-regression-interpretation flag` over-promises. The T1 interpretation is correct; only the schema-claim is overreach.

Optional polish:
- Normalise forest-plot title across the three surfaces (BLOCKER 4).
- Document the venv-activation precondition explicitly in the integration test docstring or fail-fast in the notebook's `env.py` loader (BLOCKER 5).

These are improvements, not blockers. The scientific finding — "CPI-surprise → weekly FX vol transmission is not detectable on the pre-committed Rev 4 primary" — stands. The pre-registration discipline survived the adversarial audit. NB3 is publishable.

---

## Appendix — additional skeptical probes that came back clean

The following hypotheses were tested and rejected; logging them here so a future reviewer can see that the review actually tried to break each claim.

### Probe 1 — Is `gate_verdict.json` hand-authored rather than notebook-emitted?

Concern raised by the prompt's hypothesis 2 ("tests pass green but notebook secretly broke"). If `gate_verdict.json` were hand-written to match the test expectations, it would still satisfy the synthetic-input tests (which never read the file) and the README byte-identity test.

Refutation path: the JSON field values are internally consistent with the NB2 handoff PKL. Specifically, `t3b_verdict = "FAIL"` is reproducible from β̂ − 1.28·SE = −0.002981 < 0 using the committed ols_primary coefficient + HAC SE. T7 = PASS is reproducible from |β̂_with − β̂_without| = 0.001625 ≤ SE_with = 0.001794. `bootstrap_hac_agreement = "AGREEMENT"` matches the NB2 §3.5 bootstrap CI overlap finding in the digest. A hand-authored JSON would need to reproduce twelve internal consistency relations by luck or by doing the computation — and at that point it's equivalent to the notebook running. Probe comes back clean.

### Probe 2 — Does the `test_nb3_nbconvert_executes_cleanly` test time out silently?

Concern: 30-minute timeout means the test could run for 28 minutes, timeout, and report a subprocess error — does the test file rescue that into a pass?

Refutation: `subprocess.run(..., timeout=env.NBCONVERT_TIMEOUT + 60, check=False)` at line 147. The timeout triggers `subprocess.TimeoutExpired`, which is not caught. The assertion `result.returncode == 0` never runs; the exception propagates and pytest reports the test as ERROR. Probe clean.

### Probe 3 — Does `_z_90 = 1.6448536269514722` match `scipy.stats.norm.ppf(0.95)`?

Concern raised by the appearance of a magic constant across three files (`scripts/render_readme.py` line 70, notebook cells 25 and 28). If any one of them has a stale constant, the 90% CI rendering drifts.

Refutation: `python3 -c "from scipy import stats; print(repr(stats.norm.ppf(0.95)))"` → `1.6448536269514722`. Exact match across all three sites. Probe clean.

### Probe 4 — Does the §9 halt message in code match the test's required tokens?

Concern: `test_nb3_section9_halt_message_in_source` requires substrings `"GATE FAILED"` and `"HALTING"` in the source. The notebook's emitted text uses `"⛔ GATE FAILED — HALTING §9"`. Does the Unicode stop sign prevent the substring match?

Refutation: the test looks for the substrings independently. The `"⛔ GATE FAILED"` string contains `"GATE FAILED"` as a substring (the stop sign is outside the match range). Python string `in` operator is byte-wise Unicode-agnostic here. Probe clean.

### Probe 5 — Does `_compute_material_movers` correctly handle the primary_fit "classification" shadowing?

Concern: the helper recomputes classification internally but the synthetic fixture passes `primary["classification"] = "positive_significant"`. If the helper relied on the passed primary classification instead of recomputing, the fixture's `beta=0.010, se=0.005` would yield `_classify_t3b(0.010, 0.005) → "positive_significant"` — the same value. So the test would pass either way.

Refutation: cell 28 source line 420: `_p_cls = _classify_t3b(float(primary_fit["beta"]), float(primary_fit["se"]))` — recomputes from beta/se, does NOT read the passed classification. The design smell stands (see silent-test-pass finding #4) but is not a current bug. Probe clean on the "is the logic correct" axis; unclean on the "does the test distinguish recompute from passed-through" axis — the test cannot tell.

### Probe 6 — Does the bootstrap-HAC re-derivation in cell 31 use the same seed + B as NB2 §3.5?

Concern: cell 31 comment says "recomputed here with the same seed (20260418) and B=1000 to avoid baking the flag into NB2's PKL. Deterministic — identical to NB2 §3.5's binding." If the seed differs, the AGREEMENT flag would drift.

Refutation: cell 31 code line `_bs_s10 = StationaryBootstrap(4, _y_s10.values, _X6_s10.values, seed=20260418)`. The hardcoded seed 20260418 matches `handoff_metadata.recommended_seed = 20260418` in the committed `nb2_params_point.json`. B=1000 matches via `_bs_s10.apply(_beta_cpi_pair_statistic, 1000)`. Probe clean.

### Probe 7 — Do the §4 T4/T5 tests skip gracefully under `pkl_degraded = True`?

Concern: under venv misactivation, `_ljungbox_df = None` and `_jb_result = None`. Then cell 31 maps `_t4_final = "SKIPPED"`, `_t5_final = "SKIPPED"`. If the gate aggregator panics on SKIPPED values, the notebook crashes.

Refutation: `build_gate_verdict` accepts any string in each t4/t5 slot and just passes it verbatim into the returned dict. The aggregation rule in cell 31 only gates on t3b + t1/t2/t7. T4/T5 being SKIPPED does not trigger any branch. The §1 pre-flight branches on `pkl_degraded` before any cell reads the fits, so a `NameError` on `column6_fit` is avoided even in degraded mode. Probe clean.

### Probe 8 — Does `panel_fingerprint` in the JSON match the live DuckDB fingerprint?

Concern raised by cell 4 (§1 pre-flight): a drifted fingerprint would halt the notebook. If the committed JSON was written against a stale panel, the notebook would refuse to run — which would surface in `test_nb3_nbconvert_executes_cleanly`.

Refutation: cell 4 hash `_EMBEDDED_WEEKLY_SHA256 = "769ec955e72ddfcb6ff5b16e9c949fd8f53d9e8c349fc56ce96090fce81d791f"` matches `nb2_params_point.json::panel_fingerprint`. Both match the README footer's displayed panel fingerprint. Live re-fingerprinting of the DuckDB weekly panel was NOT re-run in this review session (would require importing `scripts.panel_fingerprint` and hashing the 947-row dataframe); the internal consistency across three committed artifacts is sufficient evidence that the panel used for NB2 estimation is the panel currently pinned. Probe returns clean with that caveat.

### Probe 9 — Are any outputs in the notebook from a stale execution (not the current PKL)?

Concern: if cell 13 (T4/T5) printed output reflects an older PKL, the committed notebook JSON's cached outputs would disagree with a fresh re-execution.

Refutation path: reading the committed notebook's cell 13 `outputs` field (not done in this review — would require full-file read larger than 25k tokens limit). Test `test_nb3_nbconvert_executes_cleanly` would re-execute and potentially surface OUTPUT drift, but as noted in attack H, that test does NOT assert output content. So cached outputs in the committed notebook are not verified against live re-execution by any test. This is a latent silent-test-pass class not raised to blocker severity because the JSON artifacts (which ARE the published record) pass byte-identity against fresh regeneration. If the published record is byte-correct, cached notebook outputs that happen to be stale are a display issue, not a scientific one.

### Probe 10 — Is the citation lint script itself robust?

Concern: `test_nb3_citation_lint_passes_after_task29` runs `scripts/lint_notebook_citations.py` via subprocess. If the lint script has a bug that makes it exit 0 on every input, the test passes green trivially.

Refutation (partial): re-running the lint subprocess from this session on NB3 exits 0 as expected. Did not read the lint script source to verify it actually checks things. However, the prior reviews (Task 23 Reality Checker) included audits of this lint script and it has been a working guard across the chain. Probe returns clean with the caveat that the guard is only as good as the guard's test coverage, which was not re-audited in this pass.

---

## Summary line for handoff

Gate verdict FAIL is reproducible, internally consistent, and byte-renders into the committed README. The single most important result in the notebook — the T3b FAIL at β̂ − 1.28·SE = −0.002981 — is not spurious, is not a silent bug, and is not a test artifact. The sensitivity forest correctly identifies A1 and A4 as the two rows with 90% CIs excluding zero, and the anti-fishing halt in §9 correctly prevents those from being promoted to a spotlight. The test architecture has five silent-test-pass gaps (BLOCKER 1 sample window, BLOCKER 2 §10 live execution, BLOCKER 3 prose schema promises, BLOCKER 5 venv activation, readme skip-on-missing); none of them currently produce a wrong result, but each is a risk for future drift.

---

**End of Reality Checker review.**
