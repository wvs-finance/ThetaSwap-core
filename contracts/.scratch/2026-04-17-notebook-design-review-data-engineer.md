# Data Engineer Review: Econ Notebook Design (2026-04-17)

**Target:** `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md`
**Reviewer lens:** pipeline flow, handoff contracts, artifact consumability.

---

## Scope 1 — `cleaning.py` as wrapper (§4.1, §5.5)  NEEDS FIX

Architecturally sound in principle: `cleaning.py` is a pure module that imports `econ_query_api` and layers NB1-ledger transformations. However, §4.1 and §5.5 only *state* the rule ("query API is the only interface") — they do not *enforce* it. Risk: a future contributor adds `duckdb.connect(...).execute("SELECT ...")` inside `cleaning.py` and drift begins silently.

**Fix:** §4.1 must specify (a) `cleaning.py` exposes only functions whose signatures take `conn: duckdb.DuckDBPyConnection` and whose bodies contain *zero* `.execute(`/`.sql(`/`.read_sql(` calls; (b) a lint assertion in `contracts/scripts/tests/test_cleaning_purity.py` that greps `cleaning.py` for those substrings and fails CI if found; (c) every public function in `cleaning.py` is called through an `econ_query_api` function first, then post-processed in pandas only. Without this guard the "never drifts" claim is aspirational.

## Scope 2 — NB1 → NB2/NB3 handoff via module import (§9)  APPROVED WITH CHANGES

Module-based handoff is the right default (always-in-sync with DuckDB, no stale parquet). But §9 under-specifies *repeatability* guarantees: NB2 and NB3 must see the *identical* DataFrame NB1 saw.

**Fix:** add to §9 a non-negotiable contract row: `cleaning.load_clean_weekly_panel(conn)` is deterministic (same conn → byte-identical DataFrame: same dtypes, same row order sorted by `week_start`, no NaN-vs-NaT drift). Emit a lightweight fingerprint alongside the module handoff — `estimates/nb1_panel_fingerprint.json` containing `{rows, cols, week_start_min, week_start_max, sha256_of_sorted_csv}`. NB2/NB3 assert-match on load. This keeps parquet out of version control while closing the audit gap.

## Scope 3 — `nb2_params_point.json` completeness (§4.4)  NEEDS FIX

Missing fields Layer 2 will need:

1. **Residual series for GARCH-X** — filtered historical simulation (Barone-Adesi 2008, cited §14) requires the full standardized residual vector {ẑ_t}. JSON-embed as an array keyed by `week_start`.
2. **Conditional volatility series** from `arch.ARCHModelResult.conditional_volatility` — Layer 2 bootstrap starts from the last in-sample σ̂_T.
3. **Sample date range per block** — `ols_primary.sample_start`, `sample_end`, and identical for each subsample and GARCH-X fit. Without this, Layer 2 can't detect panel-version mismatch.
4. **Intervention-dummy coverage** — count of `intervention_dummy == 1` weeks per sample; T7 validity depends on this.
5. **Panel fingerprint** (from Scope 2) — cross-reference so Layer 2 rejects the JSON if Layer 2 pulls a different panel.
6. **HAC lag used** — §4.4 says HAC(4) but JSON should record `hac_lag: 4` explicitly.
7. **Seed metadata block** — the K=500 bootstrap lives in Layer 2, but NB2 JSON should record `random_seed_policy: "caller-provided"` and `bootstrap_draw_distribution: "multivariate_normal(theta_hat, Sigma_hat)"` so Layer 2 doesn't guess.

## Scope 4 — JSON + PKL dual-handoff (§4.4, §4.5)  APPROVED WITH CHANGES

Split is sensible: JSON is the *contract*, PKL is the *convenience*. Risks:
- **Drift:** NB2 could write JSON then mutate `fit_result` then write PKL. **Fix:** §4.5 must specify both are written inside a single function that takes the fit objects and emits both atomically.
- **PKL regen fails:** accepted cost; `make notebooks` must fail loudly when PKL regeneration errors.
- **Python incompat:** NB3 falls back to JSON-only-mode gracefully (T4/T5 residual diagnostics become "unavailable — rerun NB2 under <version>" in the verdict).

## Scope 5 — Covariance matrix serialization (§4.4)  NEEDS FIX

JSON handles 6×6–7×7 fine, but §4.4 does not specify layout. **Fix:** pin format: each Σ̂ stored as `{"param_names": [...], "matrix": [[...], ...]}` (row-major, param_names aligned with `beta_hat.keys()`). Forbid plain nested-list-only (param order becomes implicit and breaks on statsmodels upgrades). This applies to all 4–5 matrix blocks: OLS primary, GARCH-X QMLE, decomposition, and each of the 3 subsamples.

## Scope 6 — Pickle version guard (§9)  NEEDS FIX

Design says "asserts compatibility on load" — ambiguous. **Fix:** exact-match on `python`, `statsmodels`, `arch`, `numpy`, `pandas` major.minor (not patch). On mismatch NB3 logs WARNING, skips PKL-dependent cells (T4/T5 residual plots), and emits `gate_verdict.json` with `"pkl_degraded": true`. Gate verdict remains valid from JSON contract alone.

## Scope 7 — `gate_verdict.json` → README (§12)  APPROVED WITH CHANGES

§12 flags this unresolved; recommend **auto-generation**. The README is a deterministic Jinja2 (or f-string) render of `gate_verdict.json` + `nb2_params_point.json`, written by NB3's final cell. Manual curation violates reproducibility and creates merge conflicts. Commit the rendered README; CI diff-checks it against a fresh render.

## Scope 8 — Folder layout + `.gitignore` (§3)  NEEDS FIX

Proposed: `estimates/nb2_params_full.pkl` gitignored, `estimates/*.json` tracked. Current `contracts/.gitignore` has no PKL rule — needs an addition. **Fix:** add scoped rule `contracts/notebooks/fx_vol_cpi_surprise/**/estimates/*.pkl` and `contracts/notebooks/fx_vol_cpi_surprise/**/pdf/` — not a global `*.pkl` (would mask future intentional PKL fixtures). Also ignore `_nbconvert_template/**/*.aux` style LaTeX build artifacts. No collision with existing `contracts/data/` which already ignores `*.duckdb`/`*.parquet`.

## Scope 9 — `make notebooks` target  BLOCKER

**No top-level Makefile exists** in the Angstrom worktree (`test -f Makefile` fails at both worktree root and `contracts/`). §9 mentions `make notebooks` as if present. This is a silent new Make dependency. **Fix:** design must either (a) introduce `contracts/Makefile` with `notebooks:` target running `jupyter nbconvert --to notebook --execute` for all three, OR (b) use `just notebooks` (justfile exists at worktree root) and add a recipe there. Option (b) aligns with Angstrom's existing `justfile` convention. Pick one, document in §3.

## Scope 10 — Reproducibility (§4.3)  NEEDS FIX

§4.3 says "version pins documented alongside" — insufficient. **Fix:** (a) `env.py` exports `REQUIRED_PYTHON = "3.12.x"`, `REQUIRED_PACKAGES = {"statsmodels": "0.14.x", "arch": "7.x", ...}` as tuples asserted on import; (b) pins mirrored in `contracts/requirements.txt` (already exists); (c) the K=500 bootstrap seed lives in Layer 2, but NB2 must write `"random_seed_recommendation": 20260417` (date-derived, deterministic) so Layer 2 consumers have a canonical default; (d) nbconvert run uses `--ExecutePreprocessor.timeout=600` pinned in `_nbconvert_template/`. Cold-start reproducibility requires all four.

---

## Top-level verdict: **APPROVED WITH CHANGES**

Pipeline architecture is sound: query-API-only data access, three-notebook phase split, JSON-contract + PKL-convenience dual handoff, and exec-layer README all match lakehouse-style separation-of-concerns. Blockers are concrete and addressable: (1) **no Makefile/justfile target exists** for `make notebooks` — must be specified; (2) `cleaning.py` purity needs a CI-enforced lint not just a prose rule; (3) `nb2_params_point.json` schema is under-specified for Layer 2's filtered-historical-simulation needs (residuals, conditional volatility, sample ranges, panel fingerprint). Fix these and the design clears for implementation planning.
