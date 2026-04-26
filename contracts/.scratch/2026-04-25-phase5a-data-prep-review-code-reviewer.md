# Phase 5a Data Engineer — Code Reviewer Review

**Commit:** `2eed63994` — feat(abrigo): Rev-5.3.2 Task 11.O Rev-2 Phase 5a — Data Engineer prep (14-row panels for Analytics Reporter)
**Branch:** `phase0-vb-mvp`
**Spec:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (committed at `d9e7ed4c8`)
**Reviewer:** Code Reviewer (CR pass of CR + RC + SD trio per `feedback_implementation_review_agents`)
**Review date:** 2026-04-26
**Review scope:** READ-ONLY — no code modified.

---

## Verdict: **PASS**

All ten CR-lens checks pass cleanly. Five spec-pre-committed joint-nonzero counts reproduce byte-exact from live DuckDB. Friday-anchor invariant holds on every non-empty panel. TDD red→green is documented and reproducible (18/18 green observed live). Functional-Python compliance is clean. Provenance integrity is verified (zero modifications to existing modules). No blockers; no advisories.

---

## Evidence per check

### 1. Joint-nonzero pre-commitments byte-exact — **PASS**

Live-queried each parquet file via DuckDB `SELECT COUNT(*)`:

| Row | Spec pre-commitment | Live count | Match |
|---|---|---|---|
| Row 1 (primary) | 76 (spec lines 257, 320, 342) | 76 | OK |
| Row 3 (LOCF-tail-excluded) | 65 (spec lines 321, 344, 367) | 65 | OK |
| Row 4 (IMF-IFS-only) | 56 (spec lines 322, 345, 368) | 56 | OK |
| Row 7 (arb-only) | 45 (spec line 348) | 45 | OK |
| Row 8 (per-ccy COPM) | 47 (spec line 349) | 47 | OK |

All five byte-exact. Drift on any of these would silently corrupt the gate-bearing sample size and falsify the spec's pre-registered FAIL gates; the byte-exact match is the correct anti-fishing invariant.

Bonus: rows 2/5/11/12/13/14 = 76 (same panel as Row 1; estimator differs at fit time per spec §6) and rows 9/10 = 0 (deferred per spec §10 ε.2/ε.3).

### 2. Friday-anchor reconciliation correctness — **PASS**

`build_panel` translates `weekly_panel.week_start` (Monday-anchored, isodow=1) to Friday via `(week_start + INTERVAL 4 DAY)::DATE` inside the `wp_friday` CTE before the join key match. Translation is correct: Mon + 4 days = Fri.

Live verified `EXTRACT(isodow FROM week_start) = 5` on all 12 non-empty panels (76+76+65+56+76+76+45+47+76+76+76+76 = 841 rows; all isodow=5).

Three TDD invariants enforce this:
- `test_weekly_panel_is_monday_anchored` (line 176): asserts source isodow==[(1,)]
- `test_other_weekly_tables_are_friday_anchored` (line 189): asserts the 3 other tables isodow==[(5,)]
- `test_build_panel_returns_friday_anchored_rows_only` (line 335): asserts output isodow==[5]

The defensive trio is the right shape: it catches both upstream anchor drift AND build-time anchor regression. Code comment at queries.md:78 explicitly documents the failure mode this guards against ("we observed exactly this behavior pre-fix: WHERE wp.vix_avg IS NOT NULL yielded n=0 because all wp.week_start were Monday and never matched the Friday-anchored xd/y3 rows"). The comment is load-bearing — preserve it.

### 3. TDD discipline (red → green) — **PASS**

Live invocation:
```
$ pytest scripts/tests/inequality/test_phase5_data_prep.py -v
============================== 18 passed in 0.32s ==============================
```

Test breakdown:
- 4 schema tests (column-name drift defense — query live DuckDB DESCRIBE)
- 2 anchor-invariant tests
- 5 joint-nonzero count tests (Rows 1, 3, 4, 7, 8 — the spec pre-commitments)
- 4 output-contract tests (week_start, x_d>0, no NULL controls, columns)
- 1 audit-helper test (PanelAuditReport dataclass)
- 1 admitted-set guard test (ValueError on typo)

Red-phase claim: 12 of 18 fail with `ModuleNotFoundError: No module named 'scripts.phase5_data_prep'` — this is a legitimate red (module didn't exist when tests were authored), not a trivial "import succeeds" no-op. The 6 schema/anchor tests pass on red because they audit live DuckDB schema, not the panel-builder; this is correct — they're upstream-drift defenses, not module-presence defenses.

Real-data integration: every test consumes the session-scoped `conn` fixture from `scripts/tests/conftest.py` (`@pytest.fixture(scope="session") def conn()`). Zero synthetic panel fixtures. Complies with `feedback_real_data_over_mocks`.

### 4. Functional-Python compliance — **PASS**

Source structure (`scripts/phase5_data_prep.py`):
- `PanelAuditReport` (line 110): `@dataclass(frozen=True, slots=True)` — frozen, slots, no inheritance (`class PanelAuditReport:` not `class PanelAuditReport(SomeBase):`).
- Free functions: `_validate_controls`, `_validate_y3_methodology`, `_build_select_columns_sql`, `_build_where_clause`, `build_panel`, `audit_panel`, `write_panel_parquet`.
- No mutable module-level state (only `Final[...]` constants).
- Full typing including `Final`, `Sequence`, `frozenset`, `date | None`.
- No inheritance found anywhere (`grep -nE "class\s+\w+\(.*\)"` returns empty).

Complies with `functional-python` skill standard.

### 5. Anti-fishing — admitted-set & methodology literals untouched — **PASS**

`git show 2eed63994 --stat` returns ADDS only — zero modifications to:
- `contracts/scripts/econ_query_api.py`
- `contracts/scripts/econ_pipeline.py`
- `contracts/scripts/y3_compute.py`
- `contracts/scripts/y3_data_fetchers.py`
- `contracts/scripts/econ_schema.py`
- `contracts/scripts/carbon_calibration.py`

`git show 2eed63994 -- <those six files> | wc -l` = 0.

`_KNOWN_Y3_METHODOLOGY_TAGS` membership in `econ_query_api.py:72-79` still holds 4 tags byte-exact:
- `y3_v1`
- `y3_v1_3country_ke_unavailable`
- `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`
- `y3_v2_imf_only_sensitivity_3country_ke_unavailable`

`phase5_data_prep.py` imports the admitted set rather than re-defining it, so any drift would be caught at import time. This is the right pattern.

### 6. Output column contract — **PASS**

Row 1 (primary) live DuckDB `DESCRIBE`:

```
week_start            DATE
y3_value              DOUBLE
copm_diff             DOUBLE
brl_diff              DOUBLE
kes_diff              DOUBLE
eur_diff              DOUBLE
x_d                   DOUBLE
vix_avg               DOUBLE
oil_return            DOUBLE
us_cpi_surprise       DOUBLE
banrep_rate_surprise  DOUBLE
fed_funds_weekly      DOUBLE
intervention_dummy    SMALLINT
```

13 columns: 1 index + 1 outcome + 4 per-country diagnostics + 1 X_d + 6 controls. Matches the spec §4.1 equation contract.

Row 6 (parsimonious) drops 3 controls (us_cpi_surprise, banrep_rate_surprise, fed_funds_weekly) and keeps 3 (vix_avg, oil_return, intervention_dummy) — matches `THREE_PARSIMONIOUS_CONTROLS` constant and spec §6 row 6. The per-country diagnostics are preserved on every panel for Row 14's alt-weight re-aggregation.

First-row spot check (Row 1, week_start=2024-09-27): y3_value=0.014237, x_d=4604.16, vix_avg=15.804, fed_funds_weekly=4.83 — all values within published distributions.

### 7. Deferred-rows handling — **PASS**

Rows 9 and 10:
- `panel_row_09_y3_bond_diagnostic.parquet` — 0 rows, 14-column schema preserved + extra `deferred_reason VARCHAR` column.
- `panel_row_10_population_weighted.parquet` — 0 rows, same structure.

Both files exist (matches DE's claim that Analytics Reporter contract requires the parquet exist even if empty). The schema-typed empty parquets are the correct shape: they carry forward the column contract for downstream consumers without exposing them to file-existence branching. The `deferred_reason` column is an honest signal — Analytics Reporter sees the deferred state without having to read the manifest.

Manifest §2.2 documents the deferred convention: "Analytics Reporter must skip them with a `'deferred'` tag in the forest plot."

### 8. Outlier flagging discipline — **PASS**

`validation.md` §4 documents outliers via |z|>3 counts on the primary panel WITHOUT prescribing removal. Explicit text: "outliers are flagged and surfaced; they are NOT removed. The Analytics Reporter at Phase 5b is the deciding party." Matches `feedback_pathological_halt_anti_fishing_checkpoint` discipline (DE flags, doesn't trim; downstream reporter decides at fit time with documentation).

§4.1 contextualizes each flagged value (heavy right-tail X_d → suggests log-X_d for variance heterogeneity at fit time; high-VIX week 2025-Q3 → real macro stress not data error; ~100bp BanRep surprise → real cutting-cycle reversal). This is constructive: it gives Phase 5b the information needed to make a defensible robustness decision without forcing the data-prep stage to make an econometric call out of scope.

### 9. Provenance integrity — **PASS**

`git show 2eed63994 --stat` shows 21 files, 1775 insertions, 0 deletions. Zero modifications to existing files. Every file is a NEW file under either:
- `contracts/.scratch/2026-04-25-task110-rev2-data/` (output dir)
- `contracts/scripts/phase5_data_prep.py` (new module)
- `contracts/scripts/tests/inequality/test_phase5_data_prep.py` (new test file)

DE's provenance statement (commit message + manifest §5.2) "ADDS files only; does NOT modify any existing module" is verified byte-exact.

### 10. Cross-file references — **PASS**

`manifest.md` references resolve:
- `panel_row_*.parquet` — all 14 files present in output dir.
- `phase5_data_prep.py` — module exists at `contracts/scripts/phase5_data_prep.py`.
- `test_phase5_data_prep.py` — exists at `contracts/scripts/tests/inequality/test_phase5_data_prep.py`.
- Spec ref `2026-04-25-task110-rev2-spec-A-autonomous.md` — exists at the cited path.
- RC probe-5 ref `2026-04-25-y3-rev532-review-reality-checker.md` — cited as the source for the 65-week LOCF-tail-excluded count; not verified for existence (out of scope for this CR pass; flag for RC pass to triangulate).
- Predecessor commits `c5cc9b66b` and `2a0377057` — cited correctly per branch history.

`queries.md` master JOIN template (lines 16-61) matches the SQL composed by `_build_select_columns_sql` + `_build_where_clause` + `build_panel`'s f-string CTE byte-exact in structure.

---

## Strengths called out

1. **The Friday-anchor reconciliation is the right shape.** The Monday→Friday shift is encapsulated in a private CTE, has three complementary tests (source / OUTPUT / sibling tables), and is documented at three layers (queries.md §1.2, validation.md §2.1, source code comment lines 18-21 + 89-90). Future maintainers will not silently regress this.

2. **Importing `_KNOWN_Y3_METHODOLOGY_TAGS` rather than redefining it.** This is exactly the right anti-fishing pattern: the admitted set lives in one place (`econ_query_api.py`), and `phase5_data_prep` defers to it. Any future tag drift surfaces at the import-time test rather than via silent regression.

3. **Deferred-row schema preservation.** Empty parquets with the full schema (including a `deferred_reason VARCHAR` column) maintain the 14-row deliverable contract without forcing Phase 5b to special-case file-existence branching. This is a small but correct interface decision.

4. **Outlier flagging discipline.** Surfacing |z|>3 counts WITH contextual narrative ("real macro spike, not data error") gives Phase 5b actionable information without violating the data-prep scope. Compare to the alternative (silently trim outliers in `build_panel`), which would be anti-fishing-banned.

5. **DuckDB-native parquet writer.** Using `COPY ... TO ... (FORMAT PARQUET, COMPRESSION ZSTD)` avoids the pyarrow/fastparquet dependency that isn't in the contracts venv. Pragmatic and correct.

---

## Non-blocking observations (informational only — do NOT act in this commit)

These are observations the RC + SD passes may want to triangulate; they are not BLOCK or ADVISORY for the CR pass.

- **Outlier table column-header markdown rendering.** `validation.md` line 88 has `||z| > 3|` — the inner `|` characters may render unusually in some Markdown viewers. This is a doc-cosmetic note only, not a content issue.

- **Row 5 lag sensitivity panel size.** Spec §6 row 5 cell says `n=75` (after lag application at fit time), but the parquet stores n=76 because the lag is applied at fit time (Phase 5b), not data-prep time (Phase 5a). The audit_summary `notes` field for row_05 should arguably surface this "panel-size will reduce by 1 at fit time after X_d{t-1} construction" so Phase 5b sees the same expectation. Not a defect — just a Phase 5b orientation aid the data dictionary could carry.

- **Row 13 first-differenced same caveat.** n=76 stored; will become 75 after Δlog at fit time. Same orientation aid suggestion.

These are entirely Phase 5b concerns and live downstream of the data-prep contract. Do not block this commit.

---

## Files relevant to this review

- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/phase5_data_prep.py`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/tests/inequality/test_phase5_data_prep.py`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/manifest.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/validation.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/queries.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/data_dictionary.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/_audit_summary.json`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/panel_row_*.parquet` (14 files)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (spec; not modified, only read)

---

## Hand-off to RC + SD

CR pass complete with verdict PASS. Hand-off notes:

- **For Reality Checker:** The five joint-nonzero counts (76/65/56/45/47) are the gate of this stage. Triangulate against the RC probe-5 cutoff sweep at `2026-04-25-y3-rev532-review-reality-checker.md` to confirm the 65-week LOCF-tail-excluded count is the same boundary RC originally established. Also worth a probe of the audit summary for any silent-drift in dt_min/dt_max across rows that share the primary panel.
- **For Senior Developer:** Architectural review focus — does the `_validate_controls` admitted-set design (frozenset of legal control columns split across `weekly_panel` vs `weekly_rate_panel`) extend cleanly when Task 11.O Phase 5b adds release-event-window dummies (Rev-2.1 future revision per spec §4.4)? And does the parquet writer's `COPY ... TO ... (FORMAT PARQUET)` handle the deferred-row empty-DataFrame case via the `deferred_reason` column without breaking the schema contract on Phase 5b's pandas reader?

CR signature: PASS. No code changes requested.
