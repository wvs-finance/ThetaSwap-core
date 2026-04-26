# Task 11.N.2d.1-reframe — IMF-IFS-only sensitivity Y₃ panel comparison memo

**Date:** 2026-04-25
**Plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` §Task 11.N.2d.1-reframe (line 1957)
**Predecessor commits:**
- `c5cc9b66b` — Task 11.N.2d-rev (primary panel, gate cleared at 76 weeks)
- `2a0377057` — admitted-set fix-up (`_KNOWN_Y3_METHODOLOGY_TAGS` + ValueError guard)
- `d730c39ac` — 3-way review converged
**Author:** Data Engineer subagent under foreground orchestrator
**Reviewer ack required:** see §6 (methodology literal)

---

## 0. Headline finding

The IMF-IFS-only sensitivity panel — recomputed against the pre-Rev-5.3.2 source mix `{CO=IMF-IFS, BR=IMF-IFS, EU=Eurostat, KE=skip}` over the same primary window `[2023-08-01, 2026-04-24]` — **fails the load-bearing 75-week joint X_d × Y₃ gate** for `proxy_kind = "carbon_basket_user_volume_usd"`:

| Panel                          | Joint nonzero weeks | Gate ≥ 75 |
|--------------------------------|---------------------|-----------|
| PRIMARY (mixed-source Rev-5.3.2) | **76**              | **PASS** |
| SENSITIVITY (IMF-IFS-only)        | **56**              | **FAIL** |

**Coverage delta = 20 weeks.** This is the diagnostic point of the comparison: without the Rev-5.3.2 CO→DANE and BR→BCB source upgrades (Tasks 11.N.2.CO-dane-wire and 11.N.2.BR-bcb-fetcher), the panel would not have cleared the gate, and Task 11.O Rev-2 spec authoring would have been blocked under the path-ζ HALT clause (plan line 1932). The source upgrades are load-bearing.

The sensitivity panel is persisted under the methodology literal `y3_v2_imf_only_sensitivity_3country_ke_unavailable` (composite-PK isolated; primary 116-row panel and Rev-5.3.1 59-row panel both preserved byte-exact — see §3.4 row-count fingerprints).

---

## 1. Implementation summary

### 1.1 API design choice — `source_mode` keyword-only parameter

`scripts.econ_pipeline.ingest_y3_weekly` was extended with a new keyword-only parameter:

```python
def ingest_y3_weekly(
    conn: "duckdb.DuckDBPyConnection",
    *,
    start: date | None = None,
    end: date | None = None,
    source_methodology: str = "y3_v1",
    source_mode: str = "primary",      # NEW — Task 11.N.2d.1-reframe
) -> dict[str, int]:
```

`source_mode` admits `{"primary", "imf_only_sensitivity"}`; an unknown value raises `ValueError` with admitted-set context (matches the `_KNOWN_Y3_METHODOLOGY_TAGS` validation discipline established in the Rev-5.3.2 fix-up commit `2a0377057`).

The dispatch is a one-line change at the WC-CPI fetcher call site:

```python
wc_conn = conn if source_mode == "primary" else None
comp = fetch_country_wc_cpi_components(country, start, end, conn=wc_conn)
```

When `source_mode == "imf_only_sensitivity"`, the call site forwards `conn=None` to `fetch_country_wc_cpi_components`. The kwarg-aware dispatch in `y3_data_fetchers.py` lines 295–299 then routes:
- `EU` → `_fetch_eu_hicp_split` (unconditional first branch — preserved byte-exact from primary)
- `CO` → `_fetch_imf_ifs_headline_broadcast` (conn-None fallback path)
- `BR` → `_fetch_imf_ifs_headline_broadcast` (conn-None fallback path)
- `KE` → `_fetch_imf_ifs_headline_broadcast` (KE always; no-equity-ticker eligibility check then drops it per §10 row 1)

### 1.2 Why the `source_mode` parameter (vs alternatives)

Three designs were considered:

1. **`source_mode` boolean / Literal** (chosen). Cleanest under functional-Python style: the mode is an explicit caller-visible enum; the IMF-IFS path is preserved byte-exact in the fetcher (no dispatch logic duplicated at the pipeline layer); composite-PK + admitted-set discipline applies uniformly to both panels via the shared methodology literal infrastructure.
2. **Two separate functions (`ingest_y3_weekly_primary` / `ingest_y3_weekly_imf_only`)**. Rejected — duplicates ~120 lines of orchestration logic; downstream readers would have to grep two implementations to verify consumer-contract preservation; adds maintenance surface area.
3. **Inline `conn=None` override at call sites**. Rejected — bypasses the validation guard; the whole Task 11.N.2d-rev fix-up cycle exists to prevent silent dispatch drift, so extending that contract with an explicit mode parameter aligns with the established discipline.

Choice: design (1). The change is additive (default `"primary"`) and preserves backward-compat with all existing callers byte-exact.

### 1.3 Sensitivity ingest invocation

```python
ingest_y3_weekly(
    conn,                                  # canonical structural_econ.duckdb (read-write)
    start=date(2023, 8, 1),                # Rev-5.3.2 §A pre-commitment (γ backward extension)
    end=date(2026, 4, 24),                 # Rev-5.3.2 §A pre-commitment
    source_methodology="y3_v2_imf_only_sensitivity",
    source_mode="imf_only_sensitivity",
)
```

**Return value:** `{'y3_rows_written': 116, 'countries_landed': 3, 'countries_skipped': 1}`

The runtime-appended `_3country_ke_unavailable` suffix (KE skipped per §10 row 1) yields the stored literal `y3_v2_imf_only_sensitivity_3country_ke_unavailable`.

---

## 2. Failing-first TDD record

`scripts/tests/inequality/test_y3_imf_only_sensitivity.py` (NEW, 7 tests):

| Section | Test                                                                                        | Pre-patch verdict | Post-patch verdict |
|---------|---------------------------------------------------------------------------------------------|-------------------|--------------------|
| 1       | `test_ingest_y3_weekly_signature_has_source_mode_kwarg`                                     | RED (AssertionError) | GREEN |
| 1       | `test_ingest_y3_weekly_rejects_unknown_source_mode`                                         | RED (TypeError) | GREEN |
| 2       | `test_primary_mode_forwards_conn_to_wc_cpi_fetcher` (regression guard)                      | RED (TypeError) | GREEN |
| 3       | `test_imf_only_sensitivity_passes_conn_none_to_wc_cpi_fetcher`                              | RED (TypeError) | GREEN |
| 4       | `test_known_y3_methodology_tags_contains_sensitivity_literal`                               | RED (AssertionError) | GREEN |
| 4       | `test_load_onchain_y3_weekly_accepts_sensitivity_literal_against_canonical_db`              | RED (empty rows) | GREEN |
| 4       | `test_primary_panel_rows_unchanged_post_sensitivity_ingest` (byte-exact preservation guard) | RED→implicit (ingest first must run) | GREEN (116 rows) |

Red verified by running the test against the unchanged source tree (Section 1's first test failed on `assert "source_mode" in sig.parameters`); green verified after the patch + ingest landed.

---

## 3. Verification metrics

### 3.1 Per-country WC-CPI source cutoffs (sensitivity panel)

| Country | Source                                                       | Min date    | Max date    | Rows |
|---------|--------------------------------------------------------------|-------------|-------------|------|
| CO      | IMF IFS via DBnomics (`IMF/IFS/M.CO.PCPI_IX`)                | 2023-08-01  | **2025-07-01** | 24 |
| BR      | IMF IFS via DBnomics (`IMF/IFS/M.BR.PCPI_IX`)                | 2023-08-01  | **2025-07-01** | 24 |
| EU      | Eurostat HICP via DBnomics (preserved from primary)          | 2023-08-01  | 2025-12-01  | 29 |
| KE      | (skipped — design doc §10 row 1; no equity ticker on Yahoo)  | —           | —           | —    |

**Binding country: CO and BR (tied) at 2025-07-01.** This is the load-bearing finding: under the IMF-IFS-only mix, both LATAM countries cap the panel five months earlier than under the DANE/BCB Rev-5.3.2 upgrades (CO+BR at 2026-03-01 each). The matched task description's prediction (CO/BR cap at 2025-07-01) is byte-exact confirmed.

### 3.2 Y₃ panel row counts

| `source_methodology`                                                              | Rows | Min `week_start` | Max `week_start` |
|-----------------------------------------------------------------------------------|------|------------------|------------------|
| `y3_v1_3country_ke_unavailable` (Rev-5.3.1, untouched)                            | 59   | 2024-09-13       | 2025-10-24       |
| `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` (Rev-5.3.2 primary) | 116 | 2024-01-12       | 2026-03-27       |
| `y3_v2_imf_only_sensitivity_3country_ke_unavailable` (Rev-5.3.2 sensitivity)      | **116** | **2023-08-11**   | **2025-10-24**   |
| **TOTAL `onchain_y3_weekly`**                                                       | **291** | —              | —              |

**Sensitivity row count = 116** — this is higher than the task description's expected 57-60 range. The reason is the composite of (a) the γ window swap to `start = 2023-08-01` extends the panel backward by ~5 months over the IMF-IFS earliest data, and (b) the LOCF-tail-forward extension (`y3_compute.py:144`'s `+120 days`) pushes the panel forward beyond the binding 2025-07-01 cutoff.

The panel cutoff calc:
- Binding country = min(CO=2025-07-01, BR=2025-07-01, EU=2025-12-01) = **2025-07-01**
- Plus 120-day LOCF tail = **2025-10-29**
- Last Friday-anchor before 2025-10-29 = **2025-10-24** (matches observed)

The panel-row count therefore lives in the row count (116 weeks under `_imf_only`) but **not in the joint nonzero count for `carbon_basket_user_volume_usd`** — see §3.3, where the joint count drops to 56 because X_d only has carbon protocol activity from 2024-08-30 onwards, so the early-window γ backward extension contributes zero joint nonzero weeks. This is the same mechanism flagged in the corrigendum to the primary memo (`2026-04-25-y3-rev532-ingest-result.md` §CORRIGENDUM): **panel-row count and joint-nonzero count are disjoint metrics**.

### 3.3 Joint nonzero X_d × Y₃ overlap by `proxy_kind` (sensitivity vs primary)

INNER JOIN on `(week_start)` between `onchain_xd_weekly` and `onchain_y3_weekly` filtered to the methodology tag; nonzero filter = `CAST(value_usd AS DOUBLE) > 0` AND `y3_value IS NOT NULL`.

| `proxy_kind`                              | PRIMARY weeks | SENSITIVITY weeks | Δ (primary − sensitivity) |
|-------------------------------------------|---------------|-------------------|---------------------------|
| **`carbon_basket_user_volume_usd`** ★     | **76** (PASS) | **56** (FAIL)     | **+20**                   |
| `b2b_to_b2c_net_flow_usd`                 | 59            | 41                | +18                       |
| `carbon_per_currency_copm_volume_usd`     | 47            | 47                | 0                         |
| `carbon_basket_arb_volume_usd`            | 45            | 45                | 0                         |
| `carbon_per_currency_brlm_volume_usd`     | 43            | 23                | +20                       |
| `carbon_per_currency_eurm_volume_usd`     | 41            | 21                | +20                       |
| `net_primary_issuance_usd`                | 38            | 24                | +14                       |
| `carbon_per_currency_kesm_volume_usd`     | 30            | 16                | +14                       |
| `carbon_per_currency_usdm_volume_usd`     | 2             | 0                 | +2                        |

★ = primary X_d gate target per Rev-5.3.2 §A.

**Joint primary window detail (`carbon_basket_user_volume_usd`):**
- PRIMARY: first joint nonzero week = `2024-09-27`; last = `2026-03-13`; count = 76.
- SENSITIVITY: first joint nonzero week = `2024-09-27` (same); last = `2025-10-24` (binding-country-LOCF-tail capped); count = 56.

The 20-week loss is concentrated entirely in the post-2025-10-24 window — i.e., the months where IMF-IFS CO+BR are stale at 2025-07-01 + 120-day LOCF tail = 2025-10-29 (last Friday = 2025-10-24). Under the primary (DANE+BCB) mix, the panel runs 18 weeks past that date (through 2026-03-13 on the joint metric).

### 3.4 Composite-PK byte-exact preservation audit

| Methodology tag                                                              | Pre-task rows | Post-task rows | Byte-exact preservation |
|------------------------------------------------------------------------------|---------------|----------------|--------------------------|
| `y3_v1_3country_ke_unavailable`                                              | 59            | 59             | YES                      |
| `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`            | 116           | 116            | YES                      |
| `y3_v2_imf_only_sensitivity_3country_ke_unavailable`                         | 0 (new)       | 116            | additive INSERT          |

The composite PK `(week_start, source_methodology)` admits the new tag without mutating any prior row.

### 3.5 Per-week deviation (primary − sensitivity) — Y₃ value

Overlapping weeks (where both primary and sensitivity have a row): **94**.

| Statistic           | Value         |
|---------------------|---------------|
| Mean deviation      | −0.000041     |
| Std deviation       | 0.000292      |
| Min deviation       | −0.002676     |
| Max deviation       | 0.000013      |
| Weeks abs > 1 SD    | 2 (informational) |

**Interpretation.** The Y₃ values are nearly identical week-by-week (mean deviation ~4×10⁻⁵, std ~3×10⁻⁴) — i.e., the IMF-IFS-vs-DANE/BCB substitution does NOT materially shift Y₃ values for the weeks where both sources publish data. The 20-week coverage delta is driven by **panel cutoff differences, not value drift**.

The two outliers (>1 SD):
| `week_start` | primary Y₃ | sensitivity Y₃ | deviation  |
|--------------|------------|----------------|------------|
| 2025-09-05   | 0.006991   | 0.004315       | −0.002676  |
| 2025-10-03   | 0.005305   | 0.004390       | −0.000915  |

These weeks fall in the IMF-IFS LOCF-tail window where DANE/BCB still publish fresh data but IMF-IFS is held at its 2025-07-01 last observation. The deviation reflects that the LOCF-extended IMF-IFS series is increasingly stale relative to the actively-updated DANE/BCB series. **This is informational only** — it is NOT a gate-bearing finding (the load-bearing gate is the joint-coverage gate, not a value-deviation gate; the comparison memo records the deviation per the task's acceptance criterion (b)).

The `y3_v1_3country_ke_unavailable` Rev-5.3.1 panel (59 rows; min 2024-09-13, max 2025-10-24) does **not** overlap with the primary's 2024-01-12 minimum at all weeks — only the panels' overlapping range 2024-09-13 → 2025-10-24 is comparable. Within that range, the deviation pattern matches the sensitivity panel's pattern: minor differences at the LOCF-tail boundary, identical values for the bulk window.

---

## 4. Gate decision

| Gate (per Task 11.N.2d.1-reframe acceptance criteria, plan line 1965)                                       | Threshold | Actual | Verdict |
|--------------------------------------------------------------------------------------------------------------|-----------|--------|---------|
| Sensitivity panel persists in `onchain_y3_weekly` with distinct `source_methodology`                         | exact     | `y3_v2_imf_only_sensitivity_3country_ke_unavailable` | PASS |
| Composite PK preserves Task 11.N.2d-rev primary rows byte-exact                                              | exact     | 116 rows preserved | PASS |
| Composite PK preserves Rev-5.3.1 rows byte-exact (additional regression guard)                               | exact     | 59 rows preserved | PASS |
| Comparison memo documents the deviation                                                                      | exists    | this memo §3.5 | PASS |
| Methodology tag literal added to `_KNOWN_Y3_METHODOLOGY_TAGS`                                                | exact     | added (§5) | PASS |
| Existing tests under `scripts/tests/inequality/` remain green                                                | 100%      | 98 passed, 1 skipped | PASS |
| `pytest scripts/tests/` exits 0 modulo 2 pre-existing remittance Task-9 stub failures                        | green     | 1032 passed, 7 skipped, 2 pre-existing failures | PASS (scope) |
| Rev-4 `decision_hash` byte-exact preserved (no schema mutation; pure additive INSERT under composite PK)     | exact     | preserved | PASS |

**Gate verdict: CLEARED.** This task is itself non-gate-bearing on the joint X_d × Y₃ count for `carbon_basket_user_volume_usd` — the FAIL at 56 weeks under sensitivity is the diagnostic finding, not a blocker for this task. The downstream Task 11.O Rev-2 spec is unblocked by Task 11.N.2d-rev's gate clearance (76 ≥ 75); this sensitivity exists to lock that gate against silent re-tuning later.

---

## 5. Methodology literal value (RC advisory A6 — REVIEWER ACK REQUIRED)

The literal `source_methodology` value landed in `onchain_y3_weekly`:

> **`y3_v2_imf_only_sensitivity_3country_ke_unavailable`**

The base portion (`y3_v2_imf_only_sensitivity`) was passed in via the `source_methodology` kwarg; `ingest_y3_weekly`'s recovery-semantics layer auto-appended the `_3country_ke_unavailable` suffix when KE was the only skipped country (per design doc §10 row 1).

Decomposition:
- `y3_v2` — schema generation tag (matches the Rev-5.3.2 primary panel's generation; the schema and aggregation logic are byte-identical, only the source mix differs).
- `imf_only_sensitivity` — sensitivity-name flag indicating the pre-Rev-5.3.2 source mix (CO/BR routed via IMF-IFS rather than DANE/BCB).
- `_3country_ke_unavailable` — runtime-appended suffix flagging the 3-country aggregate variant (KE skipped).

**Added to `_KNOWN_Y3_METHODOLOGY_TAGS`** in `scripts/econ_query_api.py` (admitted-set is now `{"y3_v1", "y3_v1_3country_ke_unavailable", "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable", "y3_v2_imf_only_sensitivity_3country_ke_unavailable"}`).

**Reviewer-ack checkbox** (per RC advisory A6): the foreground orchestrator's CR + RC + SD reviewers ack this literal in their review reports.

- [ ] **Code Reviewer ack** — pending review of this commit.
- [ ] **Reality Checker ack** — pending review of this commit.
- [ ] **Senior Developer ack** — pending review of this commit.

---

## 6. Anti-fishing audit trail

- The IMF-IFS path body (`_fetch_imf_ifs_headline_broadcast`) is **byte-exact preserved**. The sensitivity is constructed by routing existing dispatch paths, not by introducing any new value-mutating code.
- `N_MIN` was **not** silently relaxed. The Rev-5.3.1 path-α relaxation 80→75 (recorded in `MEMORY.md::rev531_n_min_relaxation_path_alpha`) holds. The sensitivity's FAIL at 56 weeks is the **diagnostic finding** that justifies the source upgrades — it does NOT trigger any retroactive gate adjustment.
- The methodology tag literal (`y3_v2_imf_only_sensitivity_3country_ke_unavailable`) was finalized at implementation time per plan §A footnote-a and added to the admitted set BEFORE the ingest landed (the failing-first test for the admitted-set extension was red pre-patch; green post-patch).
- The 20-week coverage delta (76 PRIMARY → 56 SENSITIVITY) is the load-bearing transparency claim: under the pre-Rev-5.3.2 mix, the path-ζ disposition would NOT have cleared. This memo records that finding without re-tuning anything.
- 2 pre-existing remittance Task-9 stub failures (`scripts/tests/remittance/test_cleaning_remittance.py`) are **not introduced** by this commit and are out of scope per `feedback_agent_scope` (intentional `NotImplementedError` seams in `cleaning.py`).

---

## 7. Provenance statement

This memo is authored by the Rev-5.3.2 Task 11.N.2d.1-reframe Data Engineer subagent. **No fresh symbols are introduced** beyond:
- One new `source_mode` keyword-only parameter on `scripts.econ_pipeline.ingest_y3_weekly` (default `"primary"`; backward-compat preserved).
- One new methodology literal (`y3_v2_imf_only_sensitivity_3country_ke_unavailable`) in the `_KNOWN_Y3_METHODOLOGY_TAGS` admitted-set in `scripts.econ_query_api`.
- One new test file (`scripts/tests/inequality/test_y3_imf_only_sensitivity.py`, 7 tests, file-scoped to this task).
- 116 new rows in `onchain_y3_weekly` under the new `source_methodology` value (additive INSERT under composite PK).

The IMF-IFS dispatch path body, the EU Eurostat path, the equity fetcher, the WC-CPI weighted-composite computation, the LOCF-tail logic, the per-country differential aggregation, and the Y₃ aggregate computation are all **preserved byte-exact** — no production-code mutation outside `ingest_y3_weekly`'s signature + 3-line dispatch tweak.

The actual sensitivity-panel joint X_d × Y₃ count of 56 weeks (vs the task description's projected 57-60 range) is consistent with the binding-country IMF-IFS cutoff at 2025-07-01 plus the LOCF-tail constant at 120 days. The 5-week post-October-24 gap to the projected 60 floor is explained by the LOCF tail not extending the panel beyond the carbon protocol's joint-with-X_d window — i.e., the X_d ceiling of 2026-04-03 does not bind here because the Y₃ ceiling at 2025-10-24 is the binding side.

---

## 8. Downstream dispatch readiness

- **Task 11.O-scope-update** is unblocked. The Senior Developer authoring the spec update should consume:
  - PRIMARY methodology literal: `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` (76-week joint-coverage panel, gate PASS).
  - SENSITIVITY methodology literal: `y3_v2_imf_only_sensitivity_3country_ke_unavailable` (56-week joint-coverage panel, gate FAIL — pre-registered as the lock against silent source-upgrade reversal).
- **Task 11.O Rev-2 spec** should pre-register the sensitivity panel as a **mandatory cross-validation step** — any future revision that proposes reverting CO→IMF-IFS or BR→IMF-IFS must explain why the 20-week joint-coverage loss is acceptable.
- The HALT-with-disposition path (plan line 1932) is **not exercised**. No disposition-options memo is authored under this task.

---

## 9. Files modified (per `feedback_agent_scope`)

In-scope:
- `contracts/scripts/econ_pipeline.py` — extended `ingest_y3_weekly` with `source_mode` keyword-only parameter (~12 lines added: signature change, docstring updates, value validation, dispatch tweak at WC-CPI fetcher call site).
- `contracts/scripts/econ_query_api.py` — extended `_KNOWN_Y3_METHODOLOGY_TAGS` to include `y3_v2_imf_only_sensitivity_3country_ke_unavailable` (1 set-element addition + 14-line docstring block describing the new tag).
- `contracts/scripts/tests/inequality/test_y3_imf_only_sensitivity.py` — NEW test file (7 tests, file-scoped to this task).
- `onchain_y3_weekly` DuckDB table — additive INSERT of 116 rows under the new `source_methodology` value (no schema mutation; composite PK preserves all prior rows byte-exact).
- This memo (`contracts/.scratch/2026-04-25-y3-imf-only-sensitivity-comparison.md`).

Untouched:
- `scripts/y3_compute.py` (recently-converged; no logic change required).
- `scripts/y3_data_fetchers.py` (the existing kwarg-aware dispatch in `fetch_country_wc_cpi_components` already supports both branches; the new sensitivity simply selects the `conn=None` branch).
- `scripts/econ_schema.py` (no schema migration; existing `onchain_y3_weekly` schema admits the new tag).
- `scripts/carbon_calibration.py`.
- The IMF-IFS path body (`_fetch_imf_ifs_headline_broadcast` in `y3_data_fetchers.py`) — byte-exact preserved.
- The plan markdown and spec docs.
- Any prior `y3_v1_*` or `y3_v2_*` rows in DuckDB (composite PK protects them; row counts pre/post commit verified equal in §3.4).
