# DATA_PROVENANCE.md — dev-AI Stage-1 simple-β Phase 1 data assets

This file documents the source, transformation, and lineage of every parquet
emitted by Phase 1 of the dev-AI Stage-1 simple-β plan. Each Task appends its
own section. Sections are independent — no Task overwrites another Task's
content. Task 1.3 (panel alignment) reconciles cross-Task assumptions before
final commit.

**Append-only convention:** Tasks 1.1 (DANE GEIH Y construction) and 1.2
(Banrep TRM X construction) dispatch in parallel; both append their own section
to this file. Whichever task writes first creates the header above; the other
appends below without modifying any prior content.

**Governing artifacts (frozen):**

- Plan: `contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md`
  - User-asserted pin (from dispatch brief): `6da9cce597abb7ed9da2a8f82700f502c04a0ba25d315d05c3085f7ebfe1f86b`
  - Realized file-content sha256 at construction: `cc6092228584451177b0cf6f9eddaea02a5c4f555b22586e0d97eea38a545824`
- Spec: `contracts/docs/superpowers/specs/2026-05-04-dev-ai-stage-1-simple-beta-design.md`
  - User-asserted decision_hash (from dispatch brief): `456ba39e188d00bb17471359a5803d6aa8a40de3b3788f17294bab828a968204`
  - Realized file-content sha256 at construction: `80262ff613a5e4a1eec4c46d66a0173b5620917192c25fed7532762bfe826113`
- **Note:** the spec decision_hash and the spec file-content sha256 are not the
  same artifact. The decision_hash is computed over the spec's `§3` falsification
  primitives (decision tree + numerics), not over the full markdown payload.
  The realized file sha256 is preserved as the audit-trail anchor for what
  governed Task 1.2 construction. Same audit-trail pattern as Pair D Task 1.2
  (`contracts/.scratch/simple-beta-pair-d/data/DATA_PROVENANCE.md` line 23-31).

---

## Section: Task 1.2 — COP/USD monthly + lag-window panel (with X-back-extension into 2014)

**Owner:** Data Engineer
**Output:** `contracts/.scratch/dev-ai-stage-1/data/cop_usd_panel.parquet`
**Constructed:** 2026-05-05
**Constructor script:** `contracts/.scratch/dev-ai-stage-1/scripts/build_cop_usd_panel.py`
- Constructor sha256: `1b16fe4546072f1f31573503770372161aee22d9dff5cbe9259c73d0affe3853`

### Spec / plan reference

- **Spec §4** sample-window pin: dependent-variable index 2015-01 → 2026-03
  inclusive (135 monthly rows expected).
- **Spec §4 v1.0.1 X-back-extension** (NEW vs Pair D, MQS FLAG-5 v1.0 closure):
  X panel extended to 2014-01 → 2014-12 to preserve Y_eff = 2015-01 → 2026-03 =
  135 mo. Banrep TRM is available continuously back to 1991-12; back-extension
  is mechanically trivial. Departure from Pair D's lag-loss accounting which
  started Y at 2016-01 with 12 leading X-panel months lost. See spec §4 lines
  138-139 for the formal justification.
- **Spec §5.2** X construction: end-of-month spot from Banrep TRM; lag panel
  k ∈ {6, 9, 12}.
- **Spec §9.14** Free-tier methodology only (CORRECTIONS-δ inheritance; SPM D11 +
  RC FLAG-4 v1.0 closure): this Task uses ONLY free-tier endpoints. No paid-tier
  substitution attempted; no rate-limit encountered.
- **Plan Task 1.2 Step 1** instruction: "Reuse Banrep series provenance from
  closed FX-vol-CPI pipeline … verbatim." Honored — see Data Source section
  below.

### Data source: Banrep TRM (Tasa Representativa del Mercado)

The COP/USD daily series is the **Banrep TRM** ("Tasa Representativa del
Mercado"), the official Colombian peso–US dollar reference exchange rate
published by Banco de la República (Colombia). The TRM is the daily-published
reference rate used for accounting, tax, and contract settlement in Colombia.

**Source path (reused verbatim from closed FX-vol-CPI Phase-A.0 pipeline):**

- DuckDB: `contracts/data/structural_econ.duckdb`
- Table: `banrep_trm_daily`
- Schema: `(date DATE PRIMARY KEY, trm DOUBLE NOT NULL, _ingested_at TIMESTAMP DEFAULT current_timestamp)`
- Coverage: 1991-12-02 → 2026-04-17 (8 251 daily observations, zero nulls,
  business-day frequency — weekends and Colombian holidays absent)
- Last ingested: 2026-04-16 17:47 UTC (per `download_manifest.downloaded_at`
  for `source = 'banrep:trm'`)

**Free-tier upstream URL** (per `download_manifest` table row,
`source = 'banrep:trm'`):

> `https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=50000`

This is the **datos.gov.co** open public-data portal API (Socrata Open Data
backend) which republishes the Banrep TRM series. Free-tier, no auth, no rate
limit observed at ingestion time (8 251 rows pulled in a single request via
`$limit=50000`). This satisfies spec §9.14 free-tier-only requirement.

**Closed FX-vol-CPI pipeline cross-references (sha-pinned for audit trail):**

- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb`
  - sha256: `6c028228e568624b55653dd76b8589e7cf314faf9435196901a26d10684aad00`
  - Contains the original `download_manifest` row with `source_id = 'banrep:trm'`
    rendered in a Jupyter table cell (search keyword `banrep:trm`).
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json`
  - sha256: `2f640309ac452b58b6fc9ff1e3c1c29fabb3c9ab379ac627a789d18fa8ff2584`
- Pair D Task 1.2 precedent (same Banrep series, different sample window):
  - `contracts/.scratch/simple-beta-pair-d/data/cop_usd_panel.parquet`
  - sha256: `709625becadb2dfc888ae8e378c5aca59a9fb8b3a497865b58cad8dce5c6e803`
  - `contracts/.scratch/simple-beta-pair-d/data/DATA_PROVENANCE.md`
  - sha256: `fcb5cd50c5d0ea0eca5c5ffadb85c569e0e204101244ac1d93fedcc61477b8f2`

A fresh Banrep API re-pull was NOT performed for Task 1.2; the Phase-A.0
pipeline's cached series was reused per plan Task 1.2 Step 1 ("Reuse Banrep
series provenance from closed FX-vol-CPI pipeline verbatim"). Coverage
(1991-12 → 2026-04-17) extends through the dev-AI sample window
(2015-01 → 2026-03) plus the X-back-extension to 2014-01.

### Daily-to-monthly aggregation convention

**End-of-month spot rate = the LAST AVAILABLE business-day TRM observation
within each calendar month.** This matches:

- Spec §5.2 line 207 ("X is monthly end-of-month spot")
- Pair D §5.2 verbatim
- Closed FX-vol-CPI pipeline aggregation in `01_data_eda.ipynb`

Implementation: `daily.sort_values('date').groupby(['year', 'month']).agg(eom_business_date=('date', 'last'), trm_eom=('trm', 'last'))`.

**Spot-check (auditor reproduction key):**

- 2014-01 EOM business-day = 2014-01-31 (Friday); TRM = 2008.26;
  log(TRM) = 7.605024
- 2014-04 EOM business-day = 2014-04-30 (Wednesday); TRM = 1935.14;
  log(TRM) = 7.567935
- 2014-07 EOM business-day = 2014-07-31 (Thursday); TRM = 1872.43;
  log(TRM) = 7.534992
- 2025-09 EOM business-day = 2025-09-30; TRM = 3901.29; log(TRM) = 8.269063
- 2026-03 EOM business-day = 2026-03-31; TRM = 3669.96; log(TRM) = 8.207936

The 2015-01 panel row's `log_cop_usd_lag12` field equals 7.605024, exactly
matching the 2014-01 EOM log-TRM — confirming the X-back-extension wires the
lag-12 column to the back-extended 2014 observations.

### Lag panel construction (k ∈ {6, 9, 12})

Per spec §5.2 + §5.4 + plan Task 1.2 Step 2:

- For each contiguous monthly observation t in 2014-01 .. 2026-03 (147 EOM rows
  loaded), compute `log(COP_USD_t)`.
- For each lag `k ∈ {6, 9, 12}` months: compute `log(COP_USD_{t-k})` via
  positional shift on the contiguous monthly grid.
- Restrict the emitted parquet to dependent-variable index range
  `[2015-01, 2026-03]` inclusive — 135 rows.
- Lag-12 observations from 2014-01 .. 2014-12 are consumed as regressors but
  do NOT appear as dependent-variable rows. (This is the X-back-extension.)
- Drop rows with any NaN in the lag panel: realized drop count = 0 (the
  back-extension to 2014-01 fills every lag column for every t in [2015-01,
  2026-03]).

### Schema

Output parquet schema per plan Task 1.2 Step 3:

| column            | dtype             | description                                     |
| ----------------- | ----------------- | ----------------------------------------------- |
| year_month        | datetime64[ns]    | First day of calendar month (period stamp).    |
| log_cop_usd       | float64           | Natural log of EOM business-day TRM at month t. |
| log_cop_usd_lag6  | float64           | log(COP_USD_{t-6}).                             |
| log_cop_usd_lag9  | float64           | log(COP_USD_{t-9}).                             |
| log_cop_usd_lag12 | float64           | log(COP_USD_{t-12}).                            |

Note: the spec §5.3 primary OLS does not consume `log_cop_usd` directly (the
contemporaneous log-TRM at month t); the regressors are only the three lag
columns. `log_cop_usd` is included per plan-pinned schema for QC / diagnostic
use (e.g., NB01 EDA trio 4 ACF plot of log-TRM at lags 1-24 per plan Task 2.2
Step 4).

### Lag-window-loss expectation reconciliation

- Spec §4 line 139 expectation: "Realized N is therefore expected to be
  approximately 134 (one-month tolerance for end-of-window publication-lag
  drop)."
- Task 1.2 panel realized: **135 rows** (full 2015-01 → 2026-03 dep-var index,
  zero rows lost to lag-undefinedness because the X back-extension to 2014-01
  fills every lag column).
- **Reconciliation:** the spec's "≈134" expectation accounts for a possible
  end-of-window publication-lag drop (e.g., DANE GEIH may not yet have
  published the 2026-03 micro-data when Task 1.1 fetches it, in which case the
  joint Task 1.3 panel will drop 2026-03 to 134 rows). The X-side (this Task)
  has no publication-lag — Banrep TRM is published daily — so all 135 X rows
  are emitted. Joint-panel reconciliation occurs at Task 1.3 if Y is missing
  the 2026-03 cell.

### Output artifacts

- `cop_usd_panel.parquet`
  - sha256: `1151f711434101f7352c13320d709e397e8eb06183bf75f1f3184d61783cf97d`
  - bytes: 9 839
  - rows: 135
  - dep-var index range: 2015-01 → 2026-03 inclusive
  - X back-extension consumed: 2014-01 → 2014-12 (12 leading observations
    joined into lag columns of the 2015-01 row).

### HALT log

No HALTs surfaced in Task 1.2. All step-level checks PASSED:

- Step 1 (Banrep TRM EOM pull 2014-01 → 2026-03): PASS — 147 EOM rows loaded,
  contiguous monthly grid, no gaps; free-tier source confirmed.
- Step 2 (lag panel k ∈ {6, 9, 12}): PASS — N=135 emitted, all lag columns
  populated, zero NaN in lag rows.
- Step 3 (parquet emit + provenance): PASS — sha256 + URL + closed-pipeline
  reference recorded above.

### Reproducibility key

To regenerate this parquet:

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom
source contracts/.venv/bin/activate
python3 contracts/.scratch/dev-ai-stage-1/scripts/build_cop_usd_panel.py
```

Expected stdout includes `PARQUET_SHA256=1151f711434101f7352c13320d709e397e8eb06183bf75f1f3184d61783cf97d`.
If sha256 drifts, the upstream `banrep_trm_daily` table has changed since
`_ingested_at = 2026-04-16 17:47 UTC` — record the new sha + ingestion timestamp
in a new section below; do NOT silently overwrite this section's pin.

---

---

## Section: Task 1.1 — DANE GEIH Section J + Section M young-worker shares

**Owner:** Data Engineer
**Date emitted (UTC):** 2026-05-05
**Status:** PASS-WITH-DIAGNOSTIC-FLAGS (see §6 below). Parquet artifacts are well-formed; two diagnostic anomalies surfaced for Foreground Orchestrator §9.5 HALT-disposition adjudication.

### §1.A. Inputs

| Item | Value |
|---|---|
| Authority | DANE (Departamento Administrativo Nacional de Estadística) |
| Survey | GEIH (Gran Encuesta Integrada de Hogares) |
| Portal (free-tier) | https://microdatos.dane.gov.co/index.php/catalog/ |
| Auth required | None |
| Rate limit observed | None |
| Per spec §9.14 | Free-tier methodology only. **Compliance: 100%.** Public CSV ZIP downloads, no auth, no paid token, no paid mirror. |
| Realized window | 2015-01-31 → 2026-02-28 (134 monthly observations). Spec §4 target was 2015-01 → 2026-03 with one-month publication-lag tolerance; 2026-03 not yet published in DANE catalog at execution time, so the tolerance is consumed on the upper bound. |
| Filter (per spec §5.1) | Persona table inner-join PK = (DIRECTORIO, SECUENCIA_P, ORDEN, HOGAR); youth band P6040 ∈ [14, 28] inclusive (Ley 1622 de 2013); Ocupado employment status (file membership in Ocupados.CSV); FEX > 0. |
| Universe (per spec §4) | National aggregate (Cabecera + Resto + dispersed rural — sum across `AREA` strata; mirrors Pair D §5.1 verbatim). |
| Era partitioning | (a) `empalme_2015_2020` (72 months 2015-01 → 2020-12, FEX_C with DANE-published empalme); (b) `marco2018_sem_2021` (12 months 2021-01 → 2021-12, FEX_C18, semester archives); (c) `marco2018_native` (50 months 2022-01 → 2026-02, FEX_C18 native per-month publications). |

### §1.A.1 Pair D pipeline asset reuse (free-tier compliance preserved)

The Pair D pipeline downloaded all 58 GEIH zip archives (2015-01 → 2026-02, ~5.4GB cached). Dev-AI Stage-1 reuses these cached archives verbatim:

- Manifest: `contracts/.scratch/simple-beta-pair-d/data/dane_geih_manifest.json` (per-year/per-month catalog IDs + DANE download URLs).
- Downloads cache: `contracts/.scratch/simple-beta-pair-d/data/downloads/` (58 zip files; ~5.4 GB).
- Re-download URL availability: every URL is the canonical DANE Microdata portal URL (`https://microdatos.dane.gov.co/index.php/catalog/<id>/download/<file_id>`); the script's `_http_get()` no-ops when cache is present and re-downloads from these public URLs if not. No paid-tier substitution at any point.

### §1.A.2 Section-letter mapping reference

Per CIIU Rev. 4 A.C. (DANE Resolution 066 of 2012-01-31; ISIC Rev.4 lineage):

- **Section J** "Información y Comunicaciones": 4-digit codes whose 2-digit Division ∈ {58, 59, 60, 61, 62, 63}.
  - 58 Publishing; 59 Motion picture/video/TV; 60 Programming & broadcasting; 61 Telecommunications; 62 Computer programming, consultancy & related; 63 Information service activities.
- **Section M** "Actividades profesionales, científicas y técnicas": Divisions ∈ {69, 70, 71, 72, 73, 74, 75}.
  - 69 Legal & accounting; 70 Head office, mgmt consultancy; 71 Architecture, engineering, technical testing; 72 Scientific R&D; 73 Advertising & market research; 74 Other professional/scientific/technical; 75 Veterinary.
- Source: DANE CIIU Rev. 4 A.C. publication PDF (https://www.dane.gov.co/files/sen/nomenclatura/ciiu/CIIU_Rev_4_AC2022.pdf).
- Implementation: `_classify_section()` in `ingest_geih_section_jm.py` (lines 264-275) — division → letter via `SECTION_TO_2DIGITS` constant (lines 83-105).

### §2.A. Step 1 — Schema-stability pre-flight (PASS, INHERITED)

Per `feedback_schema_pre_flight_must_verify_values` (NON-NEGOTIABLE) the pre-flight must verify per-file `RAMA4D_R4` value-content against DANE-published Section table.

**INHERITANCE BASIS** (per spec §5.1 v1.0.1 line 193 + spec §6 line 250 + Pair D §9.10):

> "DANE's `RAMA4D_R4` field is value-content-verified for the entire 2015-2026 Empalme window."

Pair D's CORRECTIONS-α' Option-α' established:
- DANE pre-applied **Rev.4 sector coding** (`RAMA4D_R4` column) in Empalme catalogs only from 2015-01 onward (72 months).
- For 2010-2014 the Empalme files retain `RAMA4D` with **Rev.3 codes** — *out of scope* under the 2015-01 lower-bound window.

Pair D's Phase-2 pipeline operationally validated this: 134/134 months ingested cleanly with `RAMA4D_R4` mapped to canonical CIIU Rev.4 Section letters, producing the validated `geih_young_workers_services_share.parquet` (134 rows; `simple-beta-pair-d/data/`).

**Dev-AI Stage-1 inheritance:** this DE re-runs the same per-month CSV ingest pipeline over the same 134 cached zip files; the only methodological differences are: (a) Section restriction is a *single section* (J or M) rather than a {G..T} or {J,M,N} aggregate; (b) parquet schema is the dev-AI-stage-1 canonical `(year_month, raw_share, logit_share, cell_count, FEX_total)` schema. Schema-stability properties of `RAMA4D_R4` are unchanged.

**Empirical re-verification of inheritance:** 134/134 months produced canonical `RAMA4D_R4` 4-digit codes mapping to one of the 21 published CIIU Rev.4 Section letters (A through U) via `_classify_section()`. **ZERO** instances of unmappable codes triggering the `DevAIStage1RAMA4DRev4ContradictionPathological` typed exception.

**Verdict:** schema-stability pre-flight **PASS** (inherited). Typed exception did NOT fire.

### §3.A. Step 2 — DANE GEIH micro-data pull (PASS)

134 monthly files retrieved from cached zip archives (or re-downloaded from public DANE Microdata portal as needed). Per-month ingestion logic in `ingest_geih_section_jm.py::_ingest_month()`:

1. Open the cached zip for the month (era-specific layout: empalme annual zip → inner per-month sub-zip; 2021 semester zips with mixed folder naming; 2022-2026 per-month zips with heterogeneous filename conventions handled by tokenizer matcher inherited from Pair D verbatim).
2. Read CSV bytes for `Ocupados.CSV` + `Características generales (personas).CSV`.
3. Decode (UTF-8 then Latin-1 fallback per Pair D logic) and canonicalize columns (`RAMA4D_R4`, `FEX_C` or `FEX_C18`, P6040 across capitalization variants).
4. Inner-join Ocupados ↔ Características on PK = (DIRECTORIO, SECUENCIA_P, ORDEN, HOGAR), validate `m:1`.
5. Filter `P6040 ∈ [14, 28]` and `FEX > 0`.
6. Section-letter classify each row via `RAMA4D_R4` 4-digit → 2-digit-Division → Section letter.

**Per-month FEX denominators (sum of FEX over all young-employed):** [25,544,948 ; 41,989,664] across 134 months. Reasonable expansion-weighted population scale (Colombian young-employed population ~3-7M depending on year).

**Per-month n_young_employed (raw count of survey respondents):** [4,464 ; 8,974] across 134 months — matches Pair D `n_young_employed` exactly (same underlying micro-data, same youth + Ocupado filter).

### §4.A. Step 3 — Y_p (Section J) construction (PASS, with diagnostic flag)

For each month `t`:
- `raw_share = sum(FEX over young-employed in Section J) / sum(FEX over all young-employed)`
- `logit_share = log(raw_share / (1 - raw_share))`

Empalme handling per spec §6 primary disposition:
- 2015-01 → 2020-12 (72 months): `FEX_C` (DANE empalme-corrected expansion factor; nota técnica `Nota-tecnica-empalme-series-GEIH.pdf` covers 2010-01 → 2020-12).
- 2021-01 → 2026-02 (62 months): `FEX_C18` (Marco-2018 native).
- Empalme is **implicit in the FEX column choice** — DANE pre-applied empalme correction in `FEX_C` for the 2015-2020 catalogs; consumers do NOT multiply by an additional factor. Raw share `Y_t` is computed BEFORE the logit transform of §5.1.

**Realized Y_p statistics (Section J share, 134 months):**

| Statistic | raw_share | logit_share | cell_count |
|---|---|---|---|
| min | 0.014163 | -4.242824 | 94 |
| 25% | 0.020348 | -3.874231 | 128 |
| median | 0.022512 | -3.770924 | 145 |
| 75% | 0.024646 | -3.678167 | 179.5 |
| max | 0.031266 | -3.433473 | 267 |

### §4.B. Step 4 — Y_s2 (Section M) construction (PASS)

Same construction as Y_p but with Section M numerator. Used as R2 sensitivity row of §7.

**Realized Y_s2 statistics (Section M share, 134 months):**

| Statistic | raw_share | logit_share | cell_count |
|---|---|---|---|
| min | 0.018416 | -3.975963 | 136 |
| 25% | 0.023951 | -3.707495 | 177.25 |
| median | 0.027591 | -3.562278 | 195.5 |
| 75% | 0.030749 | -3.450692 | 211 |
| max | 0.040770 | -3.158189 | 245 |

Section M is empirically structurally similar to Section J in cell-count regime (~140-245 vs. ~94-267), and slightly higher in raw share (~2.8% vs ~2.3% median).


### §5.A. Step 5 — Cell-size reporting (DIAGNOSTIC; NOT auto-HALT)

Per plan Task 1.1 Step 5 + spec §6 v1.0.1 fallback (i) trigger: the cell-pathology trigger is NOT a pre-pinned numeric threshold; it is "executing specialist documenting observed cell-size pathology". This DE emits per-month cell counts as a **diagnostic** and surfaces visibly anomalous patterns to Foreground Orchestrator for §9.5 HALT-disposition adjudication. **No auto-HALT triggered by this DE.**

Per-month cell counts table emitted to: `contracts/.scratch/dev-ai-stage-1/data/logs/per_month_cell_counts.csv` (134 rows; columns: year_month, era, n_young_employed, n_young_in_section_j, n_young_in_section_m, Y_section_j_raw, Y_section_m_raw).

**Section J cell-count summary (134 months):**

| Stat | Section J cell_count | Section M cell_count |
|---|---|---|
| min | 94 | 136 |
| max | 267 | 245 |
| mean | ~155 | ~193 |
| std | 35 | 23 |
| coefficient of variation | 0.252 | 0.119 |
| month-to-month abs.median diff | 11 | (not computed) |
| year-on-year %change std | 18.9% | (not computed) |

**Comparison anchors (per Y feasibility memo §1.1 + Pair D Phase-2 actuals):**
- Y feasibility memo §1.1 baseline for Section J cell: **[700, 1200] per month** (estimate based on assumption Section J ≈ 10-15% of broad services).
- Pair D's broad-services (Section G–T) cell range: **[3,368 ; 6,556]** per month (CV = 0.127).
- Pair D's narrow (Sections J+M+N) cell range: not explicitly published in the parquet; would be ~30% of broad services ≈ 1,000-2,000.

### §6.A. **DIAGNOSTIC FLAGS surfaced to Foreground Orchestrator** (per plan Task 1.1 Step 5 + spec §9.5)

This DE surfaces **two diagnostic anomalies** to the Foreground Orchestrator. Per the plan, these are NOT auto-HALT-triggers — adjudication is delegated to the orchestrator. The DE proceeded to emit parquets per the plan; whether to continue to Phase 2 estimation is the orchestrator's call.

**FLAG-A (Section J cell-count below Y feasibility memo §1.1 baseline):**
- All 134 months have Section J cell_count outside the memo-pinned baseline of [700, 1200].
- Realized range: **[94, 267]** — a factor of ~5-7× below the memo baseline.
- One month has cell_count < 100 (94 individuals — borderline rare-event statistic territory; specifically, 2024-10-31 with n_young_in_section_j = 94).
- 74 of 134 months (55%) have cell_count < 150.

  **Operational implication:** the Y feasibility memo §1.1 estimate ("~700-1,200 per month") was apparently derived from an assumption that Section J is ~10-15% of broad services. Empirically Section J is ~3-4% of broad services (e.g., 2015-01: 249 in Section J vs. Pair D's 5,676 in Section G-T = 4.4%). **The memo's pre-pinned cell-count expectation does not match the realized data.** This was foreseeable from the spec §5.1 raw-share expectation `[~0.04, ~0.10]` — but the realized raw share is `[0.014, 0.031]`, so the same divergence afflicts the share-level expectation.

  **Logit-derivative amplification (per spec §5.1 v1.0.1 line 186-191):** spec acknowledges that at Section J's expected `[0.04, 0.10]` range, `d/dY[logit(Y)]` ranges from ~26 to ~11 (across-support ratio 2.34×). At the realized `[0.014, 0.031]` range, `d/dY[logit(Y)]` ranges from `1/(0.014 × 0.986) ≈ 72.5` at the lower bound to `1/(0.031 × 0.969) ≈ 33.3` at the upper bound — **across-support ratio 2.18×, but absolute magnitude ~3-7× larger than spec-anticipated**. A small raw-share level error (e.g., empalme residual after Marco-2018 frame change) maps to an even larger logit-Y level error than the spec acknowledged. The §6 R1 (2021 regime dummy) and §7 R3 (raw-OLS) hedges remain available; their relevance is *amplified* under the realized regime.

**FLAG-B (Section J raw_share below spec §5.1 expected range):**
- Spec §5.1 line 182: "Y_t is bounded in [0, 1] and empirically lives in roughly [0.04, 0.10] per Y feasibility memo §5 (Section J cell-size estimate)."
- Realized range: **[0.014, 0.031]** — 1.3-3× lower than spec-expected.
- **Logit-OLS validity check:** all 134 raw_share values are well-interior to (0, 1); logit_share is finite for every month (range -4.24 to -3.43); the logit-OLS choice over fractional-response GLM (per spec §5.1 line 184 Pair D MQS R3 v1) remains technically correct since the realized range is still well-interior, just lower than expected. The §5.1 line 184 justification ("empirical Y range [0.04, 0.10] is well-interior to (0, 1) — nowhere near the 0/1 boundary that motivates the fractional-response treatment") still applies — the realized range [0.014, 0.031] is also well-interior, just shifted downward.

**Anti-fishing rationale (per `feedback_pathological_halt_anti_fishing_checkpoint`):** the DE does NOT propose a fix or pivot. The plan Task 1.1 Step 5 is explicit that any pivot requires (1) typed exception by executing specialist, (2) disposition memo enumerating ≥3 pivot options, (3) user surface, (4) user picks, (5) CORRECTIONS block in plan revision, (6) 3-way review of CORRECTIONS revision. This DE has executed (1) — the cell-pathology observation is documented above as a typed flag, NOT a typed exception with HALT verdict — because the plan Task 1.1 Step 5 trigger language (plan v1.1 line 162) is "documenting observed cell-size pathology... and surfaces any visibly anomalous month to Foreground Orchestrator for §9.5 HALT-disposition adjudication" — which is a *surface* not a *halt*. The orchestrator decides whether to invoke §9.5 HALT-disposition.

**Pre-registered fallback options (per spec §6 line 262-263) — for orchestrator's reference, NOT activated by this DE:**
- Fallback (i): 3-month rolling-average Y_t (logit-transform on averaged share). Trigger requires §9.5 HALT-disposition unconditionally.
- Fallback (ii): quarterly aggregation. UNVIABLE (N drops below N_MIN); reserved as cross-validation only.
- Y_s2 promotion to primary (Section M): empirical evidence above shows Section M cell_count is also below memo baseline (range [136, 245]) but with lower CV (0.119 vs Section J 0.252) — promotion would reduce variance somewhat.
- Y_s1 EMS substitution: aggregate-index approach; window starts 2018-01 (loss of 36 months); not pre-empirically-validated.


### §7.A. Step 6 — Parquet emission

**Output 1: Y_p (Section J)**

| Item | Value |
|---|---|
| Path | `contracts/.scratch/dev-ai-stage-1/data/geih_young_workers_section_j_share.parquet` |
| Rows | 134 |
| Date range | 2015-01-31 → 2026-02-28 (UTC, month-end) |
| sha256 | `1bd70f872b3cd70333638a3b9ac3becc07409602ab2774feff4e0909b55a70db` |

Schema:

| Column | Type | Description |
|---|---|---|
| year_month | datetime64[us, UTC] | Month-end timestamp UTC; matches cop_usd_panel.parquet convention. |
| raw_share | float64 | sum(FEX over young-employed in Section J) / sum(FEX over all young-employed). |
| logit_share | float64 | log(raw_share / (1 - raw_share)). |
| cell_count | int64 | Count of distinct young-employed individuals with Section letter == J (numerator survey-respondent count). |
| FEX_total | float64 | sum(FEX over all young-employed) (denominator, expansion-weighted). |
| fex_section_j | float64 | DIAGNOSTIC: numerator FEX sum (= raw_share × FEX_total). Provided for reproducibility checks. |
| n_young_employed | int64 | DIAGNOSTIC: total survey-respondent count of young-employed. |
| era | string | One of {"empalme_2015_2020", "marco2018_sem_2021", "marco2018_native"}. |

**Output 2: Y_s2 (Section M)**

| Item | Value |
|---|---|
| Path | `contracts/.scratch/dev-ai-stage-1/data/geih_young_workers_section_m_share.parquet` |
| Rows | 134 |
| Date range | 2015-01-31 → 2026-02-28 (UTC, month-end) |
| sha256 | `5782aefab3338b0847b54f438081be3f2fbb86c2398fc2b06454d0050adcb30e` |

Schema (analogous to Output 1, with `cell_count` = Section M cell count and `fex_section_m` diagnostic column).

### §8.A. Reproducibility

To regenerate this Task 1.1 output:

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom
source contracts/.venv/bin/activate
python3 contracts/.scratch/dev-ai-stage-1/data/scripts/ingest_geih_section_jm.py
```

Expected output:
- 134 monthly observations ingested cleanly (zero failures).
- `Wrote .../geih_young_workers_section_j_share.parquet (134 rows)` with sha256 = `1bd70f872b3cd70333638a3b9ac3becc07409602ab2774feff4e0909b55a70db`.
- `Wrote .../geih_young_workers_section_m_share.parquet (134 rows)` with sha256 = `5782aefab3338b0847b54f438081be3f2fbb86c2398fc2b06454d0050adcb30e`.
- 134 diagnostic flags surfaced (Section J cell_count outside [700, 1200] memo baseline).

If sha256 drifts: either (a) a downstream DANE catalog re-publication updated one or more months' micro-data (each year's catalog has a stable `<id>` but DANE occasionally republishes corrected files at the same URL — re-pull the manifest and verify); or (b) cached zip files in `simple-beta-pair-d/data/downloads/` were modified. Record the new sha + investigation note in a new section below; do NOT silently overwrite this section's pin.

### §9.A. Cross-references

- Plan Task 1.1: `contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md` (lines 144-164).
- Spec §4 (sample-selection rules), §5.1 (Y construction), §6 (methodology-break disposition), §9.14 (free-tier methodology only): `contracts/docs/superpowers/specs/2026-05-04-dev-ai-stage-1-simple-beta-design.md`.
- Y feasibility memo: `contracts/.scratch/2026-05-04-dev-ai-y-feasibility.md` §1.1 (Section J baseline estimate; the realized data deviates from this estimate per FLAG-A above).
- Pair D Task 1.1 precedent (which validated `RAMA4D_R4` for the 2015-01 → 2026-02 window): `contracts/.scratch/simple-beta-pair-d/data/scripts/ingest_geih.py` + `step0_schema_findings.json` (verdict = HALT under Pair D Option-α' window restriction; once the window was restricted to 2015-01 onward, the schema was clean — 134/134 months produced).
- Co-emitted Task 1.2 artifact: `contracts/.scratch/dev-ai-stage-1/data/cop_usd_panel.parquet` (Banrep TRM monthly + lag panel; see §2 above of this DATA_PROVENANCE).
- Next: Task 1.3 (joint panel alignment) inner-joins Y_p + Y_s2 + X lag panel to produce `panel_combined.parquet`; expected N = 134 post-lag-12 (Y has 134 rows; X panel was pre-extended into 2014-01 → 2014-12 to cover lag-12 regressors at 2015-01 Y onset).

