# Manifest — Task 11.O Rev-2 Phase 5a Data Engineer Artifacts

**Spec:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (commit `d9e7ed4c8`, 655 lines)
**Output dir:** `contracts/.scratch/2026-04-25-task110-rev2-data/`
**Phase:** 5a (Data Engineer panel-prep)
**Next phase:** 5b (Analytics Reporter — OLS+HAC fit + bootstrap reconciliation per spec §4 + Tests T1–T7 per spec §7)

This file indexes every artifact in this directory and presents the row-level summary table that the Analytics Reporter consumes as their input contract.

---

## 1. File inventory

### 1.1 Documentation (4 files)

| File | Purpose |
|---|---|
| `queries.md` | DuckDB SQL queries with descriptions for each of the 14 matrix rows. JOIN logic + Friday-anchor reconciliation. |
| `data_dictionary.md` | Variable definitions, sources, units, cleaning steps. Every variable used in the 14 rows. |
| `validation.md` | Data-quality checks per row: joint-nonzero counts vs. spec, time-alignment, missing data, outliers, sample-size summary. |
| `manifest.md` | This file — index + row-level summary table. |

### 1.2 Panel artifacts (14 files)

All parquet files use ZSTD compression (DuckDB native writer; no pyarrow / fastparquet dependency). Schema is consistent across rows: `(week_start, y3_value, copm_diff, brl_diff, kes_diff, eur_diff, x_d, <controls>)`.

| Row | File | Bytes | n_obs |
|---|---|---|---|
| Row 1 | `panel_row_01_primary.parquet` | 6,845 | 76 |
| Row 2 | `panel_row_02_bootstrap_recon.parquet` | 6,845 | 76 |
| Row 3 | `panel_row_03_locf_tail_excluded.parquet` | 6,179 | 65 |
| Row 4 | `panel_row_04_imf_only_sensitivity.parquet` | 5,555 | 56 |
| Row 5 | `panel_row_05_lag_sensitivity.parquet` | 6,845 | 76 |
| Row 6 | `panel_row_06_parsimonious_controls.parquet` | 5,876 | 76 |
| Row 7 | `panel_row_07_arb_only.parquet` | 4,890 | 45 |
| Row 8 | `panel_row_08_per_currency_copm.parquet` | 4,999 | 47 |
| Row 9 | `panel_row_09_y3_bond_diagnostic.parquet` | 387 | 0 (DEFERRED) |
| Row 10 | `panel_row_10_population_weighted.parquet` | 387 | 0 (DEFERRED) |
| Row 11 | `panel_row_11_student_t.parquet` | 6,845 | 76 |
| Row 12 | `panel_row_12_hac12_bandwidth.parquet` | 6,845 | 76 |
| Row 13 | `panel_row_13_first_differenced.parquet` | 6,845 | 76 |
| Row 14 | `panel_row_14_wc_cpi_weights_sens.parquet` | 6,845 | 76 |

### 1.3 Audit summary (1 file)

| File | Purpose |
|---|---|
| `_audit_summary.json` | Machine-readable per-row audit (n_obs, dt_min, dt_max, methodology metadata, deferred flags). Consumed by Analytics Reporter to construct the manifest table programmatically. |

### 1.4 Total: 19 artifacts

(4 docs + 14 panels + 1 JSON summary)

---

## 2. Row-level summary table (Analytics Reporter input contract)

| # | Row label | x_d kind | y3 methodology | controls | locf cutoff | n_obs | n_x_d_nonzero | dt_min | dt_max | Pre-committed verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Primary (gate-bearing)** | `carbon_basket_user_volume_usd` | y3_v2 primary | full 6-ctrl | none | **76** | 76 | 2024-09-27 | 2026-03-13 | OPEN (gate target) |
| 2 | Bootstrap reconciliation | `carbon_basket_user_volume_usd` | y3_v2 primary | full 6-ctrl | none | 76 | 76 | 2024-09-27 | 2026-03-13 | AGREE/DISAGREE with row 1 |
| 3 | **LOCF-tail-excluded sensitivity** | `carbon_basket_user_volume_usd` | y3_v2 primary | full 6-ctrl | 2025-12-31 | **65** | 65 | 2024-09-27 | 2025-12-26 | **FAIL pre-registered** (N < 75) |
| 4 | **IMF-IFS-only sensitivity** | `carbon_basket_user_volume_usd` | y3_v2 IMF-only | full 6-ctrl | none | **56** | 56 | 2024-09-27 | 2025-10-24 | **FAIL pre-registered** (dual-axis) |
| 5 | Lag sensitivity (X_d{t-1}) | `carbon_basket_user_volume_usd` | y3_v2 primary | full 6-ctrl | none | 76 | 76 | 2024-09-27 | 2026-03-13 | OPEN (one-period lag at fit time → 75) |
| 6 | Parsimonious controls | `carbon_basket_user_volume_usd` | y3_v2 primary | 3-ctrl (vix, oil, intervention) | none | 76 | 76 | 2024-09-27 | 2026-03-13 | OPEN (collinearity diagnostic) |
| 7 | Arb-only diagnostic | `carbon_basket_arb_volume_usd` | y3_v2 primary | full 6-ctrl | none | 45 | 45 | 2024-08-30 | 2025-07-04 | OPEN (under-N diagnostic) |
| 8 | Per-currency COPM diagnostic | `carbon_per_currency_copm_volume_usd` | y3_v2 primary | full 6-ctrl | none | 47 | 47 | 2024-10-04 | 2025-09-26 | OPEN (under-N diagnostic) |
| 9 | Y₃-bond diagnostic | — | — | — | — | **0** | 0 | — | — | **DEFERRED** (spec §10 ε.2; bond fetcher unbuilt) |
| 10 | Population-weighted Y₃ | — | — | — | — | **0** | 0 | — | — | **DEFERRED** (spec §10 ε.3; aggregator unbuilt) |
| 11 | Student-t innovations | `carbon_basket_user_volume_usd` | y3_v2 primary | full 6-ctrl | none | 76 | 76 | 2024-09-27 | 2026-03-13 | OPEN (heavy-tail robustness; refit at fit time) |
| 12 | HAC(12) bandwidth | `carbon_basket_user_volume_usd` | y3_v2 primary | full 6-ctrl | none | 76 | 76 | 2024-09-27 | 2026-03-13 | OPEN (bandwidth robustness) |
| 13 | First-differenced (Δlog X_d, ΔY₃) | `carbon_basket_user_volume_usd` | y3_v2 primary | full 6-ctrl | none | 76 | 76 | 2024-09-27 | 2026-03-13 | OPEN (Δ at fit time → 75; stationarity robustness) |
| 14 | WC-CPI weights sensitivity | `carbon_basket_user_volume_usd` | y3_v2 primary | full 6-ctrl | none | 76 | 76 | 2024-09-27 | 2026-03-13 | OPEN (inequality-lens identification robustness; alt-weights at fit time) |

### 2.1 Gate-bearing rows (highlighted)

* **Row 1** — primary gate target. T3b is the load-bearing one-sided 90% test (`β̂ − 1.28·HAC SE > 0`).
* **Row 3** — LOCF-tail-excluded pre-registered FAIL (N < 75). Locks the gate against silent LOCF-policy revision.
* **Row 4** — IMF-IFS-only pre-registered FAIL (dual-axis: N < 75 AND power < 0.80). Locks the gate against silent source-mix revision.

### 2.2 Deferred rows (Rows 9 + 10)

Per spec §10 ε.2 and ε.3, these rows are flagged as future-revision items and out of scope for Rev-2. The empty schema-typed parquet files preserve the 14-row deliverable contract; Analytics Reporter must skip them with a `"deferred"` tag in the forest plot.

---

## 3. Joint-nonzero pre-commitment audit

| Spec pre-commitment | Live verification | Match |
|---|---|---|
| Row 1 (primary) = 76 | 76 | OK |
| Row 3 (LOCF-excluded) = 65 | 65 | OK |
| Row 4 (IMF-only) = 56 | 56 | OK |
| Row 7 (arb-only) = 45 | 45 | OK |
| Row 8 (per-ccy COPM) = 47 | 47 | OK |

All five pre-commitments verified byte-exact. Mechanism: `test_build_panel_row_*_returns_*_rows` in the TDD suite.

---

## 4. TDD evidence

```
$ PYTHONPATH=. python -m pytest scripts/tests/inequality/test_phase5_data_prep.py -v
============================ test session starts ============================
collected 18 items

scripts/tests/inequality/test_phase5_data_prep.py ..................   [100%]

============================== 18 passed in 0.31s ===========================
```

Pre-implementation (red phase): 12 of 18 fail with `ModuleNotFoundError: No module named 'scripts.phase5_data_prep'`. The 6 schema/anchor-invariant tests pass on red because they audit the live DuckDB schema, not the panel-builder.

Post-implementation (green phase): 18 of 18 pass.

---

## 5. Provenance

### 5.1 New symbols introduced in this commit

* `scripts.phase5_data_prep.PRIMARY_XD_KIND` — string constant `'carbon_basket_user_volume_usd'`.
* `scripts.phase5_data_prep.SIX_CONTROLS` — tuple of 6 control column names per spec §4.1.
* `scripts.phase5_data_prep.THREE_PARSIMONIOUS_CONTROLS` — tuple of 3 controls per spec Row 6.
* `scripts.phase5_data_prep.PanelAuditReport` — frozen dataclass for the audit summary.
* `scripts.phase5_data_prep.build_panel(conn, *, x_d_kind, y3_methodology, controls, locf_tail_cutoff=None) -> pd.DataFrame` — public panel-builder.
* `scripts.phase5_data_prep.audit_panel(panel) -> PanelAuditReport` — public audit summarizer.
* `scripts.phase5_data_prep.write_panel_parquet(conn, panel, output_path) -> None` — DuckDB-native parquet writer.

### 5.2 Modified symbols

None. This commit only ADDS files; it does not modify any existing module, plan, design doc, DuckDB table, or `_KNOWN_Y3_METHODOLOGY_TAGS` admitted set.

### 5.3 Live SHA verification

* `MDES_FORMULATION_HASH` (in `scripts/carbon_calibration.py`): `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` byte-exact (verified at spec-author time per spec §5).
* Predecessor commits: `c5cc9b66b` (Rev-5.3.2 primary panel) and `2a0377057` (admitted-set fix-up).

---

## 6. Handoff to Analytics Reporter (Phase 5b)

The Analytics Reporter consumes:

1. **Panel artifacts** — all 14 `panel_row_*.parquet` files. Read via `duckdb.connect().sql("SELECT * FROM 'panel_row_01_primary.parquet'")` or pandas `pd.read_parquet` (pyarrow-required for the latter).
2. **Audit summary** — `_audit_summary.json` for the manifest-table programmatic construction.
3. **Data dictionary** — `data_dictionary.md` for variable provenance and unit conventions.
4. **Spec** — `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` for §4 estimation strategy and §7 specification tests T1–T7.

The Analytics Reporter MUST NOT re-construct panels from raw DuckDB tables; doing so risks introducing silent column-drift between the Phase 5a contract and the Phase 5b regression. If the panel artifacts are insufficient, the reporter must request a Phase 5a revision rather than re-implement the JOINs.
