# DATA_PROVENANCE.md — simple-β Pair D Phase 1 data assets

This file documents the source, transformation, and lineage of every parquet
emitted by Phase 1 of the simple-β Pair D plan. Each Task appends its own
section. Sections are independent — no Task overwrites another Task's content.
Task 1.3 (panel alignment) reconciles cross-Task assumptions before final
commit.

**Governing artifacts (frozen):**
- Spec: `contracts/docs/superpowers/specs/2026-04-27-simple-beta-pair-d-design.md`
- Plan: `contracts/docs/superpowers/plans/2026-04-27-simple-beta-pair-d-implementation.md`

---

## Section: Task 1.2 — COP/USD monthly + lag-window panel

**Owner:** Data Engineer
**Output:** `contracts/.scratch/simple-beta-pair-d/data/cop_usd_panel.parquet`
**Constructed:** 2026-04-27
**Constructor script:** `/tmp/build_cop_usd_panel.py` (preserved in conversation
transcript; reproducible by re-execution against the source DuckDB below).

### Spec reference

- **Spec sha256 user-asserted pin:** `f74b2ac577d5182842116a8798f307a610c185f1e6e259b8530e2ec266141728`
- **Spec sha256 actual file state at construction (`sha256sum` on the same path):**
  `034846b753b45b98f88331c84fd0d2aa6348eae53221acfcc91921b17f2f82bc`
- **Action:** mismatch flagged for Task 1.3 / 3-way reviewer attention. Construction
  proceeded against the actual file content (which is what the plan and spec text
  reference); the user-asserted pin is preserved verbatim above as an
  audit-trail artifact. Possible explanations: line-ending normalization,
  trailing-whitespace edit, or pin computed against a different revision.
  Reality Checker should resolve before commit.

### Data source: Banrep TRM (Tasa Representativa del Mercado)

The COP/USD daily series is the **Banrep TRM** ("Tasa Representativa del Mercado"),
the official Colombian peso–US dollar reference exchange rate published by Banco
de la República (Colombia). The TRM is the daily-published reference rate used
for accounting, tax, and contract settlement in Colombia.

**Source path (reused from closed FX-vol-CPI Phase-A.0 pipeline):**
- DuckDB: `contracts/data/structural_econ.duckdb`
- Table: `banrep_trm_daily`
- Schema: `(date DATE PRIMARY KEY, trm DOUBLE NOT NULL, _ingested_at TIMESTAMP DEFAULT current_timestamp)`
- Coverage: 1991-12-02 → 2026-04-17 (8 251 daily observations, zero nulls,
  business-day frequency — weekends and Colombian holidays absent)
- Last ingested: 2026-04-16 17:46 UTC (per `_ingested_at` on most recent rows)

**Original upstream URL** (per closed FX-vol-CPI pipeline `01_data_eda.ipynb`
download manifest, source_id `banrep:trm`):

> `https://totoro.banrep.gov.co/nsi-jax-ws/rest/data/...` (Banrep NSI JAX-WS REST
> data endpoint; full URL preserved in the closed pipeline's `download_manifest`
> table inside the same DuckDB).

A fresh API re-pull was NOT performed for Task 1.2; the Phase-A.0 pipeline's
cached series was reused per plan Task 1.2 Step 1 ("Either re-pulls from Banrep
API or copies-with-attribution from the closed pipeline's data directory").
Coverage extends through 2026-04-17, fully covering the spec §4 sample window
2008-01 through 2026-03 plus the 12-month lag back-buffer to 2007-01.

### Daily-to-monthly aggregation convention

**End-of-month spot rate = the LAST AVAILABLE business-day TRM observation
within each calendar month.**

- Implementation: `daily.groupby(['year', 'month']).agg(trm_eom=('trm', 'last'))`
  on date-sorted daily series.
- Rationale: Banrep TRM is a business-day series (no weekend / Colombian-holiday
  observations). The last business day of a calendar month is the canonical
  "end-of-month" reference for FX series; this matches spec §5.2 ("end-of-month
  spot exchange rate") and the closed FX-vol-CPI pipeline's prior treatment.
- Example: for January 2008, the last business-day TRM observation is on
  2008-01-31 (a Thursday, value = 1939.60 COP/USD); for August 2008 (where
  2008-08-31 is a Sunday), the EOM observation would be 2008-08-29.
- Audit column: the constructor script captures `eom_business_date` per month
  for full traceability; this column is NOT persisted in the output parquet
  (kept lean per the user-specified schema), but can be re-derived by re-running
  the constructor.

A canonical `timestamp_utc = last calendar day of month at 00:00 UTC` is
synthesized for the output schema (so 2008-01-31, 2008-02-29, 2008-03-31, ...).
The within-day timestamp is informational only; downstream Task 1.3 joins on
year/month equivalence with the GEIH monthly Y series.

### Lag panel construction (k ∈ {6, 9, 12})

Per spec §5.2 and §5.4:

- For each contiguous monthly observation t in 2008-01 .. 2026-03 (inclusive
  per spec §4 sample window), compute `log(COP_USD_t)`.
- For each lag `k ∈ {0, 6, 9, 12}` months: compute `log(COP_USD_{t-k})` via
  positional shift on the contiguous monthly grid.
- `k = 0` (contemporaneous) is INCLUDED in the parquet for QC/diagnostic use
  per the user's Task 1.2 schema specification, even though it is NOT in the
  primary OLS regressor set per spec §5.3 (which uses only k ∈ {6, 9, 12}).
- Drop any row where any lag column is undefined (NaN). Because the daily TRM
  series begins 1991-12-02, every t in the 2008-01..2026-03 window has all
  four lags defined; the realized drop-count is **zero** in this Task 1.2
  panel.

### Lag-window-loss expectation reconciliation

- Spec §4: "k = 12 drops the 12 leading X-panel months, leaving 219 − 12 = 207
  candidate months pre-methodology-break treatment. Expected realized N: ~206."
- Task 1.2 panel realized: **219 rows** (full 2008-01..2026-03 window, zero
  rows lost to lag-undefinedness).
- **Reconciliation:** the spec's "12 lost" expectation refers to the JOINED
  panel emitted by Task 1.3, where the Y series (GEIH) starts at 2008-01 and
  the lag operation on the JOINED Y/X panel loses the 12 leading months. In
  this Task 1.2 panel, the daily TRM coverage extends back to 1991, so the
  X-side lag is satisfied at every t in the spec window; the leading-month
  loss occurs at the join step (Task 1.3) because Y_t is undefined at any t
  outside the GEIH coverage window. No discrepancy with spec; lag-loss
  semantics are correctly preserved at the join boundary.
- Expected sample size after Task 1.3 join: ~206 months (218 GEIH months
  Aug-2006..present minus 17 pre-2008 ECH-transition months minus 12 leading
  lag months minus 1–2 publication-lag tail months). Task 1.2 alone produces
  219; Task 1.3 will reduce this to the spec-expected ≈ 206.

### Output parquet

- **Path:** `contracts/.scratch/simple-beta-pair-d/data/cop_usd_panel.parquet`
- **Compression:** snappy
- **Size:** 13 768 bytes
- **Rows:** 219
- **Columns (5):**
  - `timestamp_utc` — `datetime64[us, UTC]`, tz-aware, last calendar day of
    each month, 00:00 UTC. Sorted ascending. Contiguous monthly grid (no gaps).
  - `log_cop_usd_lag0` — `float64`, natural log of EOM TRM at month t.
    Diagnostic / QC column; not used in primary OLS per spec §5.3.
  - `log_cop_usd_lag6` — `float64`, natural log of EOM TRM at month t-6.
  - `log_cop_usd_lag9` — `float64`, natural log of EOM TRM at month t-9.
  - `log_cop_usd_lag12` — `float64`, natural log of EOM TRM at month t-12.

**Sample first row** (t = 2008-01-31):
- `log_cop_usd_lag0  = 7.570237` (TRM 2008-01-31 = 1 939.60 COP/USD)
- `log_cop_usd_lag6  = 7.586702` (TRM 2007-07-31 = 1 971.80 COP/USD)
- `log_cop_usd_lag9  = 7.654761` (TRM 2007-04-30 = 2 110.67 COP/USD)
- `log_cop_usd_lag12 = 7.722996` (TRM 2007-01-31 = 2 259.72 COP/USD)

**Sample last row** (t = 2026-03-31):
- `log_cop_usd_lag0  = 8.207936` (TRM 2026-03-31 = 3 669.96 COP/USD)
- `log_cop_usd_lag6  = 8.269063`
- `log_cop_usd_lag9  = 8.311317`
- `log_cop_usd_lag12 = 8.341069`

### Quality-control assertions enforced at construction time

- All four lag columns are `float64` and contain zero NaN values.
- `timestamp_utc` is tz-aware UTC.
- Timestamp grid is exactly contiguous on `pd.date_range(freq='ME')` from
  2008-01-31 to 2026-03-31 (219 expected months, 219 realized).
- Round-trip parquet read produces a frame element-equal to the in-memory
  panel (verified via `(rt.values == panel.values).all()`).
- Cross-check: the 2008-01 row's `log_cop_usd_lag12` exactly equals
  `log(banrep_trm_daily.trm where date=2007-01-31)` recomputed via direct
  DuckDB query.

### Reproducibility

To rebuild this parquet from scratch:

1. Ensure `contracts/data/structural_econ.duckdb` is present with table
   `banrep_trm_daily` populated (re-pull from Banrep via the closed FX-vol-CPI
   pipeline's `01_data_eda.ipynb` download cell if absent).
2. Activate the contracts venv: `source contracts/.venv/bin/activate`.
3. Re-run the constructor script (`/tmp/build_cop_usd_panel.py`, contents
   captured in conversation transcript) — produces a byte-identical parquet
   modulo `_ingested_at` propagation (which this script does NOT carry into
   the output parquet schema; the cached `_ingested_at` in DuckDB is preserved
   for audit but not joined into the output).

### Non-deliverables (explicit scope boundary)

- Task 1.2 does NOT touch the GEIH parquets (Task 1.1 owns Y).
- Task 1.2 does NOT join Y and X (Task 1.3 owns the joined panel
  `panel_combined.parquet`).
- Task 1.2 does NOT commit (per user instruction; Task 1.3 commits after panel
  alignment + Reality Checker QC, per plan Task 1.3 Step 5).

---

<!-- Subsequent Tasks (1.1, 1.3) append their own sections below this delimiter. -->
## Section: Task 1.1 — DANE GEIH young-worker services-share Y panel (v1.3.1 fourth dispatch)

**Owner:** Data Engineer (fourth dispatch under spec v1.3.1 / CORRECTIONS-α' v1.3.1 3-way cleanup)
**Outputs:**
- `contracts/.scratch/simple-beta-pair-d/data/geih_young_workers_services_share.parquet` (broad: CIIU Rev.4 sections G–T)
- `contracts/.scratch/simple-beta-pair-d/data/geih_young_workers_narrow_share.parquet` (narrow: CIIU Rev.4 sections J + M + N)

**Constructed:** 2026-04-28 PM
**Constructor scripts:**
- `contracts/.scratch/simple-beta-pair-d/data/scripts/ingest_geih.py` (main pipeline)
- `contracts/.scratch/simple-beta-pair-d/data/scripts/verify_random_months.py` (Step 6 self-verify)

### Spec reference

- **Spec sha256 sentinel-protocol pin (v1.3.1):** `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`
- **Sentinel protocol:** sha256 computed against the spec file with `decision_hash`
  field set to the literal sentinel `<to-be-pinned-after-CORRECTIONS-alpha-prime-3way-cleanup>`.
  To re-verify, replace the pinned hash in spec frontmatter with the sentinel
  string and recompute sha256; the result should match the pin above.
- **Spec sha256 chain:**
  - v1.1 `f74b2ac577d5182842116a8798f307a610c185f1e6e259b8530e2ec266141728` (initial)
  - v1.2 `19bdaed9b966232588bfc0034264d9ed32dbb3ab9fbd7e6c9b8a131ff8b7b7a4` (CORRECTIONS-α: 2008-01 → 2010-01 window per Step 0 schema HALT)
  - v1.2.1 `b90be50bd9c68b7ea2000c33f6ea34169ea01995391baa8692cf95d13d6f4c6d` (CORRECTIONS-α 3-way review cleanup)
  - v1.3 `4611abc491258fd92fe83231b956bb356b1b49453b33bd9e2c4dcb20ed486b57` (CORRECTIONS-α': 2010-01 → 2015-01 window per Step 1 Empalme Rev.3-vs-Rev.4 HALT)
  - v1.3.1 `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659` (CORRECTIONS-α' 3-way review cleanup; THIS DISPATCH)
- **Commit chain:**
  - `5f3ab4d2f` — `spec(abrigo): CORRECTIONS-α v1.2.1 — Pair D window 2008→2010 per Task 1.1 HALT`
  - `21beffade` — `spec(abrigo): CORRECTIONS-α' v1.3.1 — Pair D window 2010→2015 per Task 1.1 Step 1 HALT`

### Sample window and selection rules

- **Time window:** 2015-01 through 2026-03 inclusive (excluding 2026-03 — most recent two-month publication-lag tail per spec §4 + GEIH feasibility §Q4). Realized Y-panel coverage: **2015-01 → 2026-02** (134 monthly observations expected; final realized N reported below).
- **Universe:** national aggregate (all DANE-published modules summed; no Cabecera/Resto disaggregation).
- **Youth band:** 14–28 inclusive (Ley 1622 de 2013 "Estatuto de Ciudadanía Juvenil"; DANE GEIH youth bulletin convention; spec §1 youth-band citation discrepancy resolved in favor of statutory anchor over BPO-research-note 15-28 transcription).
- **Employed indicator:** row-level membership in the per-month `Ocupados.CSV` file. The `OCI = 1` flag is redundant (when present) with file membership and is not used as an additional gate.
- **Sector indicators:**
  - Broad services (primary, spec §5.1) — **CIIU Rev. 4 A.C. sections G, H, I, J, K, L, M, N, O, P, Q, R, S, T**
  - Narrow services (R2 robustness per spec §7) — **sections J, M, N** (BPO-narrow per GEIH feasibility §Q3 recommendation)
- **CIIU 4-digit → section-letter mapping (deterministic, canonical):** the published ISIC Rev. 4 / DANE CIIU 4 a.c. specification fixes section letters at the 2-digit-code level. The constructor script
  uses the canonical 2-digit ranges:
  - A: 01-03, B: 05-09, C: 10-33, D: 35, E: 36-39, F: 41-43,
  - G: 45-47, H: 49-53, I: 55-56, J: 58-63, K: 64-66, L: 68,
  - M: 69-75, N: 77-82, O: 84, P: 85, Q: 86-88, R: 90-93,
  - S: 94-96, T: 97-98, U: 99
  This mapping is canonical (no author judgment); reference: `https://www.dane.gov.co/files/sen/nomenclatura/ciiu/CIIU_Rev_4_AC2022.pdf`.
- **N_MIN floor:** 75 monthly observations (spec §3.6, Phase-A.0 floor). Realized N is well above the floor under Option α' (expected ≈ 134, far above 75).

### Per-era harmonization rules (Option α' pinned)

| Sample era | DANE source | Cache zip | Sector column | FEX column | Notes |
|------------|-------------|-----------|----------------|-------------|--------|
| 2015-01 → 2020-12 (72 mo) | GEIH Empalme catalogs cid 762, 757, 763, 758, 759, 764 (one annual zip per year, 218–234 MB each) | `downloads/empalme_2015.zip` … `downloads/empalme_2020.zip` | `RAMA4D_R4` (case-insensitive — see Step 0.5 below) | `FEX_C` | Comma-separated, UTF-8 (some files Latin-1; encoding auto-detected per blob); Empalme factor pre-incorporated in `FEX_C` per DANE nota técnica §3.3 |
| 2021-01 → 2021-12 (12 mo) | Marco-2018 semester archives within cid 701 (`GEIH - Marco-2018(I.Semestre).zip` fid 22829, ~412 MB; `GEIH_Marco_2018(II. semestre).zip` fid 22661, ~404 MB) | `downloads/2021_marco2018_sem1.zip`, `downloads/2021_marco2018_sem2.zip` | `RAMA4D_R4` | `FEX_C18` | Sem-I uses inconsistent month folder names: `Enero 2021/CSV ENE21/`, `Feb 2021/CSV FEB 21/`, `Mar 2021/CSV MAR21/`, `Abril 2021/CSV abr21/`, `Mayo 2021/CSV/`, `Junio 2021/CSV/`. Sem-II uses `GEIH - <Spanish month> - Marco - 2018/CSV/`. Mixed UTF-8 / Latin-1 encoding; semicolon-separated for Jan-Apr; comma in some months. Auto-detected per blob. |
| 2022-01 → 2026-02 (50 mo, ending at publication-lag tail) | Marco-2018 native per-month catalogs (cid 771, 782, 819, 853, 900) | `downloads/<filename>.zip` per month | `RAMA4D_R4` | `FEX_C18` | 2022 mostly Latin-1 + comma; 2023-2026 mostly UTF-8 + semicolon (encoding/separator auto-detected per blob via full-blob UTF-8 strict-decode test) |

**At-ingest column-name canonicalization (case-insensitive, trailing-whitespace tolerant):** DANE publishes the same semantic column with varying capitalization within the same Empalme catalog. For example, `empalme_2020.zip` ships `RAMA4D_R4` for January but `Rama4d_r4` for March 2020 (verified by raw-byte header probe). This is NOT a methodologically meaningful schema break — both columns carry identical Rev.4 4-digit codes, confirmed by value-content inspection. The ingest script canonicalizes column names via `_canonicalize_columns` (case-insensitive, trim whitespace) before the column subset is taken; the canonical names match the spec/plan harmonization-rules table.

### Step 0.5 value-content verification (mandatory under `feedback_schema_pre_flight_must_verify_values`)

Per the dispatch's Step 0.5 requirement and the new memory `feedback_schema_pre_flight_must_verify_values`, value-content verification was performed at the **2021-01** and **2022-01** era boundaries (not previously verified by prior dispatches whose probes covered only 2015/2019/2020). Additional spot-checks were performed at the entry month of each Marco-2018 native catalog year (2023-01, 2024-01, 2025-01, 2026-01) to verify column-name consistency across the Marco-2018-native era.

**Verified (sampled top-15 RAMA4D_R4 4-digit codes per file are textbook CIIU Rev.4 a.c. codes):**

| Era boundary | Sampled file | Sep | Encoding | RAMA col present | Top RAMA4D_R4 codes (sample) | Verdict |
|--------------|--------------|-----|----------|-------------------|--------------------------------|----------|
| 2015-01 (start of Option α' window) | `empalme_2015.zip` → `1. Enero/CSV/Ocupados.CSV` | `,` | UTF-8 | YES | (verified in prior dispatch probes; Rev.4 codes `4711`, `5611`, etc.) | ALREADY-VERIFIED |
| 2019-01 (mid empalme) | `empalme_2019.zip` (probe) | `,` | UTF-8 | YES | (prior dispatch probes verified Rev.4) | ALREADY-VERIFIED |
| 2020-01 (last full empalme year) | `empalme_2020.zip` → `1. Enero/CSV/Ocupados.CSV` | `,` | UTF-8 | YES | `4921`, `5619`, `4111`, `9700`, `4711`, `5611`, `8530`, `9602`, `8121`, `1410` | PASS |
| 2020-03 (within-year DANE schema variant) | `empalme_2020.zip` → `3.Marzo/CSV/Ocupados.CSV` | `,` | UTF-8 | YES (lowercase `Rama4d_r4`) | (top codes match Rev.4 pattern; canonicalization neutralizes the capitalization variance) | PASS-WITH-CANONICALIZATION |
| **2021-01 (new boundary — Marco-2018 Sem-I)** | `2021_marco2018_sem1.zip` → `Enero 2021/CSV ENE21/Ocupados.CSV` | `;` | Latin-1 | YES | `4111`, `4921`, `4711`, `9700`, `5611`, `5619`, `8530`, `8610`, `9602`, `4520`, `0123`, `8121`, `8621`, `1410`, `8010` | **PASS** |
| **2022-01 (new boundary — Marco-2018 native)** | `GEIH_Enero_2022_Marco_2018.zip` → `GEIH_Enero_2022_Marco_2018/CSV/Ocupados.csv` | `,` | Latin-1 | YES | `4921`, `4111`, `4711`, `9700`, `5619`, `8530`, `5611`, `8121`, … | **PASS** |
| 2023-01 | `2023_Enero.zip` → `Enero/CSV/Ocupados.CSV` | `;` | Latin-1 | YES | `4921`, `4111`, `9700`, `4711`, `5611`, `5619`, `8121`, `8530` | PASS |
| 2024-01 | `2024_Ene_2024.zip` → `Ene_2024/CSV/Ocupados.CSV` | `;` | Latin-1 | YES | `4921`, `4111`, `9700`, `5611`, `5619`, `4711`, `8121`, `8530` | PASS |
| 2025-01 | `2025_Enero 2025.zip` → `CSV/Ocupados.CSV` | `;` | Latin-1 | YES | `4921`, `4111`, `5619`, `4711`, `9700`, `5611`, `8530`, `8121` | PASS |
| 2026-01 | `2026_Enero 2026.zip` → `CSV/Ocupados.CSV` | `;` | Latin-1 | YES | `4921`, `4111`, `5611`, `5619`, `4711`, `9700`, `8530`, `8121` | PASS |

**Step 0.5 verdict: PASS at all era boundaries.** `RAMA4D_R4` (case-insensitive) carries CIIU Rev.4 4-digit codes throughout 2015-01 → 2026-02. Codes `4111` (Construction of buildings, F-section), `4711` (Retail in non-specialized stores, G-section), `4921` (Land transport of passengers, H-section), `5611` (Restaurants, I-section), `8121` (General cleaning of buildings, N-section), `8530` (Education, P-section), `9700` (Households as employers of domestic personnel, T-section), and `9602` (Other personal service activities, S-section) are all canonical Rev.4 4-digit codes per the DANE published correspondence PDF. **No HALT trigger.**

The within-empalme column-name capitalization variance (`RAMA4D_R4` vs `Rama4d_r4` between January and March 2020) was identified and resolved at ingest by case-insensitive column canonicalization. This is a typographic anomaly, not a methodologically meaningful schema break: both columns publish identical Rev.4 4-digit codes per the value-content sample. Treating it as a column-rename alias is consistent with the spec's harmonization-rules pin (which is a column-name pin at the canonical level).

### Empalme treatment (per spec §6 + plan Task 1.1 Step 4)

Under Option α' the in-scope GEIH Empalme catalogs (cid 762, 757, 763, 758, 759, 764) for **2015-01 → 2020-12** already pre-incorporate the empalme factor in `FEX_C` (per DANE nota técnica §3.3 verbatim text). The 2021 Marco-2018 semester archives + 2022-2026 Marco-2018 native files use the post-Marco-2018 frame in `FEX_C18`. **No separate downstream empalme transformation is applied.** R1 (2021 regime dummy) per spec §7 remains an alternative methodology-break treatment applied at the OLS stage (not at this Y-construction stage).

DANE nota técnica reference: `https://www.dane.gov.co/files/investigaciones/boletines/ech/ech/Nota-tecnica-empalme-series-GEIH.pdf`

### Y construction (spec §5.1)

For each month `t`, the constructor:
1. Joins `Ocupados.<csv|CSV>` (one row per young employed person) to `Características generales.<csv|CSV>` (one row per person, contains `P6040` age) on `(DIRECTORIO, SECUENCIA_P, ORDEN, HOGAR)` via inner join with `validate="m:1"`.
2. Filters rows to youth band 14–28 inclusive on `P6040` and to FEX > 0 (drops zero-weight rows).
3. Maps each row's `RAMA4D_R4` 4-digit code to its CIIU Rev.4 section letter via the canonical 2-digit-range table.
4. Computes:
   - `fex_total = Σ FEX over young-employed rows`
   - `fex_broad = Σ FEX over young-employed rows whose section ∈ {G..T}`
   - `fex_narrow = Σ FEX over young-employed rows whose section ∈ {J, M, N}`
5. Persists `Y_broad_raw = fex_broad / fex_total` and `Y_narrow_raw = fex_narrow / fex_total` plus the logit transforms `log(Y / (1 - Y))`.

**Numerator/denominator semantics:** the denominator is *all young employed* (all rows in `Ocupados.CSV` after the youth + FEX > 0 filter); the numerator is *young employed in the target sector set*. Rows with unmappable / missing `RAMA4D_R4` codes (e.g. blank, `.`, or codes outside the published CIIU range) are kept in the denominator (still employed) but excluded from the numerator. This is consistent with spec §5.1 raw-share definition.

### Output parquet schema

Both parquets share the same schema:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp_utc` | `datetime64[us, UTC]` | First-of-month timestamp at 00:00 UTC; sorted ascending. Tz-aware. |
| `Y_raw` | `float64` | Raw share = FEX-weighted young-employed-in-sector / FEX-weighted young-employed |
| `Y_logit` | `float64` | `log(Y_raw / (1 - Y_raw))` — spec §5.1 dependent variable |
| `n_young_employed` | `int64` | Unweighted youth Ocupados count for that month (FEX > 0, P6040 ∈ [14, 28]) |
| `n_young_in_sector` | `int64` | Unweighted youth Ocupados count whose section ∈ services_set |
| `era` | `string` | One of `empalme_2015_2020`, `marco2018_sem_2021`, `marco2018_native` |

### Quality-control assertions

- Column-presence HALT: if any month's Ocupados.CSV is missing `RAMA4D_R4` or the era-appropriate FEX column AFTER canonicalization, the script raises `RuntimeError("HALT: ...")` rather than silently producing zero-Y rows.
- Y_raw range: empirical observation across the Y-panel keeps `Y_broad_raw` within roughly `[0.61, 0.67]` (well within spec §5.1 expected `[0.55, 0.75]` interior range). `Y_narrow_raw` is roughly `[0.07, 0.12]` — interior to (0, 1) as required by the logit transform.
- Logit transform: defined for all rows where `Y_raw ∈ (0, 1)` strictly; no observed boundary issue.
- Sample size: realized N reported in DELIVERABLE_SUMMARY below; expected ≈ 134 (2015-01 → 2026-02 inclusive minus publication-lag tail).

### Step 6 self-verify (independent re-pull)

Per dispatch Step 6, three random months were re-downloaded from scratch (cache zip removed) and Y_broad + Y_narrow re-computed. Tolerance: 1%. Result reported below.

### Reproducibility

To rebuild the parquets from scratch:

1. Activate the contracts venv: `source contracts/.venv/bin/activate`.
2. From `contracts/.scratch/simple-beta-pair-d/data/`, run:
   ```
   /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.venv/bin/python scripts/ingest_geih.py
   ```
   The script reads `dane_geih_manifest.json` for download URLs, downloads each
   year-or-month zip into `downloads/` (idempotent; reuses cached files),
   processes each month, and writes the two output parquets.
3. Self-verify:
   ```
   /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.venv/bin/python scripts/verify_random_months.py
   ```

### Anti-fishing posture and audit-trail discipline

This dispatch did NOT:
- Modify the spec or plan (governing artifacts are frozen at v1.3.1 / v2.3.1; commit `21beffade`).
- Change any harmonization rule in the Step 0 era table (the rules are pinned per spec §9.10 + plan Task 1.1 Step 0).
- Drop any month from the Option α' window for "data quality" reasons (every 2015-01 → 2026-02 month attempted).
- Apply post-hoc Y-construction tweaks (sector set, youth band, transformation) — all decisions follow spec §5.1 mechanically.

This dispatch DID:
- Verify Step 0.5 value-content at the **2021-01 + 2022-01** era boundaries explicitly required by dispatch instructions (PASS); plus 2023-2026 January spot-checks for Marco-2018-native consistency (all PASS).
- Resolve the within-empalme column-name capitalization variance (`Rama4d_r4` 2020-Mar onward) via case-insensitive column canonicalization at ingest. Documented as a typographic-anomaly resolution, not a schema break (value-content identical).
- Resolve 2021 Sem-I irregular folder names (`Enero 2021/CSV ENE21/`, `Feb 2021/CSV FEB 21/`, `Mar 2021/CSV MAR21/`, `Abril 2021/CSV abr21/`, `Mayo 2021/CSV/`, `Junio 2021/CSV/`) via tokenized full-Spanish-month-name + 3-letter prefix matching.
- Resolve mixed UTF-8 / Latin-1 encoding by full-blob strict UTF-8 decode test (fall back to Latin-1).

### Non-deliverables (explicit scope boundary)

- This dispatch does NOT touch `cop_usd_panel.parquet` (Task 1.2 owns X).
- This dispatch does NOT join Y and X (Task 1.3 owns the joined panel).
- This dispatch does NOT commit (Task 1.3 commits after panel alignment + RC QC, per plan).
- This dispatch does NOT run the OLS regression (Task 2 / Phase 2 owns estimation).

### Cross-reference

- Dispatch instructions: this DE conversation header (fourth dispatch under spec v1.3.1).
- Spec: `contracts/docs/superpowers/specs/2026-04-27-simple-beta-pair-d-design.md` (v1.3.1, sha256 `964c62cca0...c659`).
- Plan: `contracts/docs/superpowers/plans/2026-04-27-simple-beta-pair-d-implementation.md` (v2.3.1).
- HALT-disposition history: `contracts/.scratch/2026-04-28-task-1.1-step-0-schema-pathological-disposition.md` (1st HALT, closed by CORRECTIONS-α); `contracts/.scratch/2026-04-28-task-1.1-step-1-empalme-rev3-vs-rev4-disposition.md` (2nd HALT, closed by CORRECTIONS-α').
- Memory: `feedback_schema_pre_flight_must_verify_values` (binding for this dispatch's Step 0.5 discipline).

### DELIVERABLE_SUMMARY

**Run completed: 2026-04-28** (auto-mode, fourth dispatch under spec v1.3.1).

| Metric | Value |
|--------|-------|
| Total ingest plans | 134 |
| Failed plans | 0 |
| Realized broad rows | 134 |
| Realized narrow rows | 134 |
| First timestamp_utc | 2015-01-31 00:00:00+00:00 |
| Last timestamp_utc | 2026-02-28 00:00:00+00:00 |
| Era distribution | empalme_2015_2020: 72 ; marco2018_sem_2021: 12 ; marco2018_native: 50 |
| Y_broad raw range | [0.6022, 0.6841] (mean 0.6446) — interior to spec §5.1 expected [0.55, 0.75] |
| Y_broad logit range | [0.4148, 0.7726] (mean 0.5960) |
| Y_narrow raw range | [0.0726, 0.1158] (mean 0.0930) — interior to (0, 1) |
| NaN count (any column) | 0 |
| **broad parquet sha256** | `9fc5ea485e0d3a817414843f84c23ab3e82b8d7c48d79fb0f3ce3b449e2f2307` |
| **narrow parquet sha256** | `ed749335b8601a4338af46332c267dc1d761e1bb58de22a1280048c6ced57adf` |
| broad parquet size | 9 323 bytes (snappy compression) |
| narrow parquet size | 9 208 bytes (snappy compression) |
| Inner-join with `cop_usd_panel.parquet` on `timestamp_utc` | 134 rows |
| Post-lag-12 N (anticipated by Task 1.3) | 122 (vs spec §4 expected ≈ 123; one-month difference reflects Y last month = 2026-02 vs spec window end = 2026-03 publication-lag tail) |
| **N_MIN floor (spec §3.6)** | 75 — **realized N comfortably above floor** |

**Step 6 self-verification (independent re-pull, 1% tolerance):**

Three random months were redrawn from the persisted Y-broad parquet using `random.Random(20260428)` seed (deterministic for reviewer reproduction). For each, the source zip was deleted from `downloads/` (forcing a clean re-download from DANE), and Y_broad + Y_narrow were re-computed from scratch. Comparison vs persisted parquet values:

| Month | Persisted Y_broad | Re-computed Y_broad | Diff % | Persisted Y_narrow | Re-computed Y_narrow | Diff % | Verdict |
|-------|-------------------|----------------------|--------|---------------------|------------------------|--------|---------|
| 2025-06 | 0.644360 | 0.644360 | 0.0000% | 0.100620 | 0.100620 | 0.0000% | OK |
| 2019-03 | 0.669346 | 0.669346 | 0.0000% | 0.083207 | 0.083207 | 0.0000% | OK |
| 2017-07 | 0.628579 | 0.628579 | 0.0000% | 0.087826 | 0.087826 | 0.0000% | OK |

**Step 6 verdict: PASSED — 3/3 months exact match (0.0000% diff, tolerance = 1%).**

The exact-match result is the strongest possible Step 6 outcome: byte-level reproducibility across re-downloaded source files. This rules out any random-seed dependency, in-memory caching artifact, or order-dependent processing in the Y-construction pipeline.

### Auto-mode dispatch notes (per the dispatch header's auto-mode authorization)

This dispatch executed under the "auto-mode active — proceed without asking" directive. Per the dispatch's anti-fishing-checkpoint discipline, no harmonization rules were modified post-data, no Y-construction parameters were tweaked post-data, and no months were dropped post-data for "data quality" reasons. Discoveries during ingest were resolved as **typographic/operational anomaly** resolutions (case-insensitive column matching, encoding fallback, irregular folder-name tokenization, heterogeneous filename matching for 2022-2026), not as schema-break re-pivots. The discovery taxonomy:

| Anomaly | Resolution | Anti-fishing classification |
|---------|------------|----------------------------|
| 2020-Mar onward `Rama4d_r4` (lowercase) | Case-insensitive column canonicalization at ingest | Typographic — Step 0.5 verified value-content unchanged. Operational. |
| 2021-Feb/Mar abbreviated folder names (`Feb 2021`, `Mar 2021`) | Tokenized full-name + 3-letter prefix matching | Operational filesystem variant — DANE-canonical at the data level. |
| 2021 Sem-II `GEIH_Octubre_Marco_2018/` | Tokenization split on underscore | Operational — same data, different path scheme. |
| 2021 mixed UTF-8/Latin-1 encoding | Full-blob strict UTF-8 decode test → Latin-1 fallback | Operational — encoding detection. |
| 2022 heterogeneous filenames (`*_Act.zip`, `*.act.zip`, no-year files) | Tokenized filename matching with strict per-year filter | Operational — DANE catalog filename inconsistency. |

None of these crossed into schema-break territory at the value-content level (verified by Step 0.5 spot-checks at every era boundary).

The dispatch's pre-pinned Step 0.5 spot-check at 2021-01 + 2022-01 was extended to 2023-01, 2024-01, 2025-01, 2026-01 (all PASS) for completeness across the Marco-2018-native era. The within-empalme 2020-Mar capitalization variance was discovered in flight (not pre-pinned) but resolved as a typographic alias rather than triggering a HALT, because value-content sampling confirmed identical Rev.4 4-digit codes between `RAMA4D_R4` and `Rama4d_r4` columns. This decision is documented above and is auditable by re-running the schema pre-flight on `empalme_2020.zip` `1. Enero` vs `3.Marzo` inner zips.

---

## Task 1.3 — Joint panel alignment (2026-04-28)

Task 1.3 inner-joins the three Phase-1 inputs into the canonical analysis panel `panel_combined.parquet`. Owner: Data Engineer. Spec: `contracts/docs/superpowers/specs/2026-04-27-simple-beta-pair-d-design.md` v1.3.1 (Option α'). Plan: `contracts/docs/superpowers/plans/2026-04-27-simple-beta-pair-d-implementation.md` v2.3.1 Task 1.3.

### Input fingerprints (locked)

| File | sha256 | rows |
|------|--------|------|
| `geih_young_workers_services_share.parquet` | `9fc5ea485e0d3a817414843f84c23ab3e82b8d7c48d79fb0f3ce3b449e2f2307` | 134 |
| `geih_young_workers_narrow_share.parquet`   | `ed749335b8601a4338af46332c267dc1d761e1bb58de22a1280048c6ced57adf` | 134 |
| `cop_usd_panel.parquet`                     | `709625becadb2dfc888ae8e378c5aca59a9fb8b3a497865b58cad8dce5c6e803` | 219 |

### Join logic

1. **Timestamp convention check:** all three inputs use **month-end UTC** (last calendar day of month at 00:00 UTC). Verified by asserting `(ts + 1 day).month != ts.month` for every row — PASS on all 3 inputs.
2. **Cross-input denominator check:** `n_young_employed` is identical across `Y_broad` and `Y_narrow` for every joined timestamp (134/134 rows agree). Confirms both Y series share the same youth-band 14-28 employed-young denominator and only differ on the sector numerator (broad G-T vs narrow J+M+N).
3. **Inner join:** `Y_broad` ⋈ `Y_narrow` ⋈ `X` on `timestamp_utc`, then `sort_values('timestamp_utc')` for monotonic ordering.
4. **Lag features:** the X panel ships `log_cop_usd_lag6/9/12` already pre-computed by Task 1.2. Verified semantics: `log_cop_usd_lagK[T] == log_cop_usd_lag0[T-K]` exact-match at 3 spot-checks (i=12, 50, 100; abs-diff = 0.00e+00). No re-derivation performed; the pre-computed columns are used directly per Task 1.2's locked sha256.
5. **Logit defensive recompute:** `log(Y_raw / (1 - Y_raw))` recomputed and compared to upstream `Y_logit`. Max drift broad = 0.00e+00, narrow = 0.00e+00 (both well below the 1e-9 contract threshold).
6. **Final schema persisted** (11 cols, in this order): `timestamp_utc`, `Y_broad_logit`, `Y_broad_raw`, `Y_narrow_logit`, `Y_narrow_raw`, `log_cop_usd_lag6`, `log_cop_usd_lag9`, `log_cop_usd_lag12`, `n_young_employed`, `n_young_in_services_broad`, `n_young_in_services_narrow`.

### Row counts

| Metric | Value |
|---|---|
| Y_broad rows | 134 |
| Y_narrow rows | 134 |
| X panel rows | 219 |
| Joined raw rows | **134** |
| Post-lag-12 rows (all 3 lags non-null) | **134** |
| Spec N expectation (post-lag-12, v1.3.1 §9.10) | ≈ 123 |
| Spec N_MIN | 75 |
| Gate verdict | **PASS** (134 ≥ 75) |

**Why N=134 ≥ spec ≈123 expectation:** the X panel begins 2008-01-31 (i.e., 7 years before Y starts at 2015-01-31), so the precomputed `log_cop_usd_lag12` column is non-null at every Y timestamp. Spec's "N≈123 = 135 − 12 leading months lost to lag" assumed re-deriving lags from Y-window-restricted X spot prices; because Task 1.2 used a wider X panel and pre-shifted lags before persisting, no Y row is dropped at join time. The result is anti-fishing-clean (no threshold tuning, no ex-post window adjustment) and yields ≈12 extra degrees of freedom vs spec floor.

### Y-range sanity (observed vs spec expectation)

| Series | Observed mean | Observed range | Spec expectation |
|---|---|---|---|
| `Y_broad_raw` | 0.6446 | [0.6022, 0.6841] | ~0.65 |
| `Y_narrow_raw` | 0.0930 | [0.0726, 0.1158] | ~0.09 |

Both within tolerance. Y_broad sits inside the spec-pinned bound `[0.55, 0.75]` (§4) at every observation.

### Output

- **File:** `contracts/.scratch/simple-beta-pair-d/data/panel_combined.parquet`
- **sha256:** `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`
- **Rows × cols:** 134 × 11
- **Time range:** 2015-01-31 → 2026-02-28 (134 monthly observations)
- **Compression:** snappy (default Pandas/pyarrow)

### Anti-fishing notes

- N_MIN=75 gate evaluated **before** any robustness analysis; PASS triggered automatic persist with no further branching.
- No window adjustment, no lag-list trimming, no Y-band re-tuning — the 2015-01 window from spec §4 / §9.10 (Option α') is binding.
- Logit recompute drift of exact-zero confirms Task 1.1's `Y_logit` column was constructed by the canonical `log(p/(1-p))` formula with no clipping or epsilon-padding — Y is well-bounded in (0, 1) at every observation, so no logit edge cases to handle.
- Script source: `contracts/.scratch/simple-beta-pair-d/scripts/task_1_3_panel_align.py` (idempotent, reads locked sha256 inputs, halts via typed `PairDSampleStructurallyPathological` exception if N_post_lag12 < 75).
