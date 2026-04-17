# Data Schema & Acquisition Strategy: Structural Econometrics Pipeline

**Date:** 2026-04-16 (Rev 4: Priority 1b resolved — IBR verified, intervention extracted, EME unavailable → AR(1) confirmed primary)
**Upstream spec:** `2026-04-15-fx-vol-cpi-surprise.md` (Rev 4)
**Status:** Rev 4. Ready for implementation.
**Phase:** 5 Step A — data pipeline
**Reviewers:** Data Engineer, Reality Checker, Model QA Specialist (2 rounds)

---

**Rev 3 changelog (from Rev 2):**

- **DE-B1 (row-level audit):** Added `_ingested_at TIMESTAMP DEFAULT current_timestamp` to `banrep_trm_daily`, `dane_ipc_monthly`, `dane_ipp_monthly` for row-level provenance on INSERT OR REPLACE.
- **DE-B2 (daily_panel gaps):** Added `oil_log_level` to `daily_panel`. Added `banrep_rate_surprise` to daily_panel deferred columns for symmetry with weekly_panel.
- **RC-F1 (TRM verified):** TRM confirmed available on Datos Abiertos Colombia (Socrata API, dataset `32sa-8pi3`, 8,250 rows, 1991–present, no auth). Priority 1 split into 1a (TRM, verified — download immediately) and 1b (EME/IBR/SUAMECA, genuinely unverified).
- **RC-F2 (Socrata pagination):** Documented default 1,000-row limit; must set `$limit=50000` or paginate.
- **RC-F9 (upstream amendment):** TRM is verified (not "pending"); TRM eliminates (not "mitigates") the noon-rate measurement error.
- **DE-F1 (manifest append-only):** Manifest carved out from INSERT OR REPLACE — uses plain INSERT (append-only).
- **DE-F3 (BLS UNIQUE):** Added `UNIQUE(release_date)` to `bls_release_calendar`.
- **DE-F4 (daily first-row):** Documented first trading day has NULL return; estimation module drops during GARCH initialization.
- **DE-F5 (date-range filter):** Added explicit sample start for derived panels: first Monday after 12 months of DANE IPC warmup.
- **DE-F6 (pct_change source):** Documented `ipc_pct_change` / `ipp_pct_change` stored as published by DANE, not recomputed.
- **MQA-F3 (surprise placement):** Documented release-date convention for daily_panel; estimation module should test day-t vs day-t+1 as robustness.
- **MQA-F4 (0.0 mixture):** Documented that ~76% zeros inflate kurtosis; T5 should run on full sample AND release-week subsample.
- **MQA-F6 (seasonality):** Noted DANE IPC likely not seasonally adjusted; estimation module should test AR(1) vs AR(12)/seasonal AR.
- **MQA-F7 (same-day CPI+PPI):** Documented overlap treatment for Levene test bins.
- **MQA-F8 (VIX endogeneity):** Noted lagged VIX as estimation-spec sensitivity to break contemporaneous simultaneity.
- **RC-F5 (release_id precision):** Corrected "release 10 = CPI-U" to "release 10 = Consumer Price Index (BLS release covering CPI-U, CPI-W, etc.)."
- **RC-F10 (BanRep website):** Documented that BanRep's own website is NOT the correct programmatic source; Datos Abiertos is.
- **RC-F12 (TRM valor):** Added ingestion rule: `valor` (string) → DOUBLE cast.
- **RC-F13 (TRM date):** Documented `vigenciadesde` as the date field, implicit COT timezone.
- **RC-F14 (FRED release/dates format):** Added `&file_type=json` to BLS release dates endpoint.
- **MQA-N1 (AR(1) frequency):** AR(1) re-estimated monthly (each new observation).
- **MQA-N2 (MoM formula):** Documented raw MoM % change = (CPI_t / CPI_{t-1} - 1) * 100.
- **MQA-N3 (AR(1) boundary exception):** `cpi_surprise_ar1` documented as specification-invariant exception to the pipeline/estimation boundary.
- **DE-N1 (daily week_start):** Added `week_start` column to daily_panel for join convenience.
- **DE-N2 (degenerate weeks):** Documented weeks with n_trading_days <= 1 retained; estimation module filters.

**Rev 4 changelog (from Rev 3):**

- **P1b-IBR (VERIFIED):** IBR overnight confirmed via BanRep SDMX REST API (`DF_IBR_DAILY_HIST`, SUBJECT `IRIBRM00`). Daily from 2008-01-02. No auth. New raw table `banrep_ibr_daily` (§3.10). `banrep_rate_surprise` moved from deferred to active in both panels.
- **P1b-intervention (VERIFIED via Playwright):** FX intervention data extracted from SUAMECA Angular portal via Playwright. 1,674 daily records, 1999–2024, 8 intervention types. New raw table `banrep_intervention_daily` (§3.11). `intervention_dummy` moved from deferred to active in both panels. Raw data cached at `contracts/data/raw/banrep_fx_intervention.json`.
- **P1b-EME (UNAVAILABLE):** BanRep EME survey results are NOT available as machine-readable data. SUAMECA lists EME as metadata only (name, periodicity). No download link, no API, no Excel. BanRep old portal URLs return 404. Not on Datos Abiertos. be_1171 used Bloomberg (§2.4 fn.16). AR(1) fallback activated → `cpi_surprise_ar1` confirmed as primary RHS variable (no longer labeled "fallback"). `cpi_surprise_survey` removed from deferred columns (indefinitely deferred — requires Bloomberg or manual PDF digitization of ~260 monthly EME reports).
- **Priority 1b restructured:** Split into 1b (IBR + intervention, both verified) and 1c (EME, unavailable). Updated decision tree outcomes.
- **§3.9 updated:** Conflict resolution now covers `banrep_ibr_daily` and `banrep_intervention_daily`.
- **§5 pipeline flow updated:** Steps reflect IBR download via SDMX and intervention load from cached JSON.

---

## 1. Acquisition Priority Order (Risk-First)

Data sources are ordered by **uncertainty of access**, not ease. The sources we know least about get investigated first — if they fail, we need to amend the upstream spec before building anything else. FRED is last because it's the safest.

### Priority 1a: BanRep TRM daily (VERIFIED — download immediately)

TRM is confirmed available as a free, unauthenticated Socrata JSON API on Colombia's Datos Abiertos portal:

- **Endpoint:** `https://www.datos.gov.co/resource/32sa-8pi3.json`
- **Row count:** ~8,250 rows (1991-12-02 to present, verified live)
- **Format:** JSON with fields `valor` (COP per USD, **string** — must cast to DOUBLE), `vigenciadesde` (date with `T00:00:00.000` suffix — use as date column, implicit COT timezone), `vigenciahasta`, `unidad`
- **Authentication:** None required (public dataset)
- **Pagination:** Socrata default limit is 1,000 rows. **Must** set `$limit=50000` or paginate with `$offset` + `$limit=5000` chunks. Without this, download silently truncates to most recent 1,000 observations.

BanRep's own website (`banrep.gov.co/es/estadisticas/trm`) returns 404 or bot protection. Datos Abiertos is the correct programmatic path.

**STOP condition retained as defensive coding:** If TRM is unavailable (endpoint changes, Datos Abiertos goes offline), no daily COP/USD = no RV = no model. Pipeline halts and escalates to user. No FRED fallback exists (DEXCOUS does not exist).

### Priority 1b: BanRep IBR + FX intervention (VERIFIED — download immediately)

Both sources investigated and verified (2026-04-16).

**IBR overnight rate** — confirmed via BanRep SDMX REST API:

- **Endpoint:** `https://totoro.banrep.gov.co/nsi-jax-ws/rest/data/ESTAT,DF_IBR_DAILY_HIST,1.0/all/ALL/?startPeriod=2008&endPeriod=2027&dimensionAtObservation=TIME_PERIOD&detail=full`
- **Date range:** 2008-01-02 to present (live-tested: IBR overnight ER = 11.249% on 2026-04-16)
- **Format:** SDMX-ML Generic Data v2.1 (XML). Filter for SUBJECT=`IRIBRM00` (overnight), UNIT_MEASURE=`ER` (effective rate).
- **Authentication:** None required
- **Caveat:** `endPeriod` is exclusive on year — set `endPeriod=2027` to get 2026 data.
- **Documentation:** https://suameca.banrep.gov.co/archivos/webservices/documento_tecnico_ws_consumo_sdmx.pdf (38 pages, v3.0)
- **Fallback:** Datos Abiertos Socrata dataset `b8fs-cx24` (shorter range: from 2012)

**FX intervention data** — extracted via Playwright from SUAMECA Angular portal:

- **Source page:** `https://suameca.banrep.gov.co/estadisticas-economicas/informacionSerie/3300/operaciones_mercado_cambiario_resumen`
- **Records:** 1,674 daily intervention entries, 1999-12-01 to 2024-10-04
- **Columns (8 intervention types):** Intervención discrecional (294 days), Compra directa (1,098 days), Opciones put/call para control volatilidad (41+34 days), Opciones put/call para acumulación/desacumulación reservas (122+8 days), NDF (78 days), FX Swaps (4 days)
- **Format:** Extracted as JSON (`contracts/data/raw/banrep_fx_intervention.json`) and TSV (`contracts/data/raw/banrep_fx_intervention.tsv`)
- **Access method:** Playwright JS evaluation (SUAMECA is Angular SPA; BanRep's own website has ShieldSquare bot protection). Table data rendered in DOM, extracted via `document.querySelectorAll('table')[1]`.
- **Update cadence:** Quarterly manual re-extraction via Playwright, or scripted with headless browser.

### Priority 1c: BanRep EME consensus (UNAVAILABLE — AR(1) confirmed primary)

The BanRep Encuesta Mensual de Expectativas (EME) survey results are **not available as machine-readable data**:

- SUAMECA lists EME under "Encuestas sobre expectativas económicas" as metadata only ("Periodicidad: Mensual, disponible desde: septiembre de 2003") — no download link, no data table, no API
- BanRep old portal URLs (`banrep.gov.co/es/estadisticas/encuesta-mensual-*`) all redirect to 404 (migrated to SUAMECA)
- Not on Datos Abiertos Colombia (searched via Socrata API — no results)
- Not in the SDMX API (only 11 series exposed; EME is not among them)
- be_1171 (the upstream paper) used Bloomberg for CPI expectations (§2.4 fn.16)
- EME results are published as monthly PDF reports (medians/means/ranges of analyst CPI expectations). Constructing a historical time series would require manual digitization of ~260 PDFs (2003–2025).

**Consequence:** The AR(1) CPI surprise (`cpi_surprise_ar1`) is the **confirmed primary** RHS variable, not a fallback. The upstream spec (Rev 4 §4.1) correctly documents AR(1) as a "different object" from the survey-based surprise — it tests "does CPI deviate from its own recent trend predict FX vol?" rather than "does CPI deviate from market expectations predict FX vol?" Both are valid but measure different things. The survey-based surprise column (`cpi_surprise_survey`) is indefinitely deferred — it would require Bloomberg access or manual PDF digitization.

### Priority 2: DANE (medium uncertainty)

DANE data (CPI index, PPI index) is confirmed free but programmatic access is historically unreliable. DANE has changed its portal at least three times (DANE Web, SEN, Datos Abiertos). DANE IPC on Datos Abiertos (`y75b-wh7y`) has been observed returning 404/"dataset.missing" errors. Known entry points for manual download: `https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/indice-de-precios-al-consumidor-ipc` (CPI), similar path for PPI. Historical IPC data sometimes available as Excel files linked from DANE bulletin pages.

| Variable | Source | Approach |
|---|---|---|
| IPC monthly (Colombian CPI) | DANE data portal | Programmatic first; fallback to manual CSV/Excel download |
| IPP monthly (Colombian PPI) | DANE data portal | Same |
| Release calendar | DANE annual calendars | Manual compilation (~520 rows for CPI+PPI, 2003–2025) |

~260 monthly observations per series. Manual download for this volume is a one-time effort with incremental monthly updates — perfectly acceptable.

DANE IPC download must start at least 12 months before the estimation sample (i.e., 2002-01-01 if sample starts 2003) to provide warmup for the Colombian CPI AR(1) fallback surprise construction.

### Priority 3: FRED (lowest uncertainty)

FRED has a well-documented REST API with stable endpoints and an API key is already provisioned. All 4 series verified to exist on FRED. Rate limit: 120 requests/minute — not a binding constraint for this pipeline (4 daily + 1 monthly + 1 release dates = 6 requests).

| Series ID | Variable | Frequency | Start | Est. rows (from 2003) |
|---|---|---|---|---|
| `VIXCLS` | CBOE VIX close | Daily | earliest available | ~5,500 |
| `DCOILWTICO` | WTI crude oil spot price (primary) | Daily | earliest available | ~5,500 |
| `DCOILBRENTEU` | Brent crude oil spot price (sensitivity) | Daily | earliest available | ~5,500 |
| `CPIAUCSL` | US CPI-U index (all items) | Monthly | 1yr before TRM start (AR(1) warmup) | ~280 |

Observations endpoint: `GET /fred/series/observations?series_id=X&api_key=$FRED_API_KEY&file_type=json&observation_start=YYYY-MM-DD`

BLS release dates endpoint: `GET /fred/release/dates?release_id=10&file_type=json` (release 10 = Consumer Price Index — BLS release covering CPI-U, CPI-W, and others; release dates apply to CPIAUCSL)

**Ingestion rule:** FRED returns the string `"."` for missing observations (holidays, data gaps). The download script must convert `"."` to SQL NULL before INSERT. No silent type-casting.

**Row count note:** "earliest available" for FRED series means raw tables may contain more rows than ~5,500 (VIXCLS starts 1990 → ~9,000 rows; oil starts earlier). The ~5,500 estimate applies to the ~2003–2025 estimation window. Raw tables store all available data; derived panels filter to the estimation window (§4.5).

Authentication: `FRED_API_KEY` environment variable.

---

## 2. Database

**File:** `contracts/data/structural_econ.duckdb`

Separate from the existing `ran_accumulator.duckdb` (on-chain Angstrom pool data). Different data domains, different update cadences, different concerns.

**Runtime:** Python via `contracts/.venv` (duckdb 1.5.1, pandas, requests, statsmodels, numpy, scipy available). Requires duckdb >= 1.2.0 for PK constraint enforcement at INSERT time.

---

## 3. Raw Tables (Native Frequency)

Raw tables store data at its source frequency. Conflict resolution: `INSERT OR REPLACE` for all raw tables except `download_manifest` (§3.9).

### 3.1 banrep_trm_daily

Daily COP/USD exchange rate from Datos Abiertos Colombia (Socrata dataset `32sa-8pi3`). This is the LHS variable source — it constructs realized volatility.

| Column | Type | Constraint | Notes |
|---|---|---|---|
| date | DATE | PRIMARY KEY | Trading day (Colombian business calendar). Sourced from `vigenciadesde` field. |
| trm | DOUBLE | NOT NULL | COP per 1 USD. Sourced from `valor` field (string → DOUBLE cast). |
| _ingested_at | TIMESTAMP | NOT NULL DEFAULT current_timestamp | Row-level audit: updated on INSERT OR REPLACE. Tracks when this value was last written. |

**Ingestion rule:** Socrata returns `valor` as a JSON string (e.g., `"3603.19"`). Must cast to DOUBLE before INSERT. `vigenciadesde` includes `T00:00:00.000` suffix — parse as DATE, implicit COT timezone.

**Known measurement note:** TRM is Colombia's official benchmark, computed from actual interbank transactions on SET FX. Unlike a noon indicative rate (which DEXCOUS would have been), TRM reflects real traded prices. This eliminates the "FRED noon rate vs SET FX close" measurement error concern in upstream spec §3.3. TRM is a single daily rate — intraday price discovery is not captured. DANE releases typically published between 6–8pm COT; the reaction appears in the NEXT business day's TRM.

### 3.2 fred_daily

FRED daily series in long format. One table, `series_id` column distinguishes series.

| Column | Type | Constraint | Notes |
|---|---|---|---|
| series_id | VARCHAR | NOT NULL, CHECK (series_id IN ('VIXCLS', 'DCOILWTICO', 'DCOILBRENTEU')) | Series discriminator |
| date | DATE | NOT NULL | Trading day |
| value | DOUBLE | | Observation value (NULL = FRED missing/holiday `"."`) |
| | | PRIMARY KEY | (series_id, date) |

### 3.3 fred_monthly

US CPI for AR(1) surprise construction.

| Column | Type | Constraint | Notes |
|---|---|---|---|
| series_id | VARCHAR | NOT NULL, CHECK (series_id IN ('CPIAUCSL')) | Series discriminator |
| date | DATE | NOT NULL | First of month |
| value | DOUBLE | | Index level |
| | | PRIMARY KEY | (series_id, date) |

### 3.4 dane_ipc_monthly

Colombian CPI (IPC) as published by DANE. Download starts 2002-01-01 (12-month warmup for AR(1) fallback).

| Column | Type | Constraint | Notes |
|---|---|---|---|
| date | DATE | PRIMARY KEY | Reference month (first of month) |
| ipc_index | DOUBLE | | IPC index level |
| ipc_pct_change | DOUBLE | | Month-over-month % change **as published by DANE** (not recomputed from index). If DANE does not publish % change directly, compute as (ipc_index / lag(ipc_index) - 1) * 100 and document in manifest notes. |
| _ingested_at | TIMESTAMP | NOT NULL DEFAULT current_timestamp | Row-level audit |

### 3.5 dane_ipp_monthly

Colombian PPI (IPP) as published by DANE.

| Column | Type | Constraint | Notes |
|---|---|---|---|
| date | DATE | PRIMARY KEY | Reference month (first of month) |
| ipp_index | DOUBLE | | IPP index level |
| ipp_pct_change | DOUBLE | | Month-over-month % change **as published by DANE** (same rule as §3.4) |
| _ingested_at | TIMESTAMP | NOT NULL DEFAULT current_timestamp | Row-level audit |

### 3.6 dane_release_calendar

Maps each monthly CPI/PPI release to its actual publication date. Critical for identification (upstream spec §4.4: "DANE pre-schedules releases").

| Column | Type | Constraint | Notes |
|---|---|---|---|
| year | SMALLINT | NOT NULL | Release year |
| month | SMALLINT | NOT NULL | Reference month of the data |
| release_date | DATE | NOT NULL | Actual date DANE published the figure |
| series | VARCHAR | NOT NULL, CHECK (series IN ('ipc', 'ipp')) | Which index |
| imputed | BOOLEAN | NOT NULL DEFAULT FALSE | TRUE if release_date is estimated (pre-2010 gaps) |
| | | PRIMARY KEY | (year, month, series) |
| | | UNIQUE | (release_date, series) |

~520 rows (CPI + PPI, 2003–2025). Manually compiled from DANE annual release calendars ("calendario de difusion").

**Pre-2010 gap strategy:** Historical DANE calendars before ~2010 may not be available on the current website (Wayback Machine may be needed). For months where the exact release date cannot be determined: assume the 5th business day of the following month (DANE's typical pattern) and mark `imputed = TRUE`. Imputed dates are usable for weekly assignment but should be flagged in estimation diagnostics.

**Same-day CPI+PPI releases:** DANE typically publishes CPI and PPI on the same day (upstream spec §4.4). When both release on the same date, both `is_cpi_release_week` and `is_ppi_release_week` are TRUE for that week. This is the correct behavior for the decomposition equation (both regressors active). The Levene test T2 should classify such weeks as "both" rather than double-counting in CPI-only and PPI-only bins — this is an estimation-module concern documented here for awareness.

### 3.7 bls_release_calendar

Maps each US CPI release to its publication date. Required for assigning `us_cpi_surprise` to the correct week.

| Column | Type | Constraint | Notes |
|---|---|---|---|
| year | SMALLINT | NOT NULL | Release year |
| month | SMALLINT | NOT NULL | Reference month of the CPI data |
| release_date | DATE | NOT NULL | Date BLS published the figure |
| | | PRIMARY KEY | (year, month) |
| | | UNIQUE | (release_date) |

Source: FRED release dates API: `GET /fred/release/dates?release_id=10&file_type=json` (release 10 = Consumer Price Index — BLS release covering CPI-U, CPI-W, and others; release dates apply to CPIAUCSL). Machine-readable, free, no additional API key needed beyond `FRED_API_KEY`.

### 3.8 download_manifest

Audit trail for every download attempt. Satisfies upstream spec's Phase 5 Step A requirement: "download artifacts (filename, row count, date range) must be produced."

| Column | Type | Constraint | Notes |
|---|---|---|---|
| source | VARCHAR | NOT NULL | e.g., `banrep:trm`, `fred:VIXCLS`, `dane:ipc`, `banrep:eme` |
| downloaded_at | TIMESTAMP | NOT NULL | When the download ran (microsecond precision via Python `datetime.now()`) |
| row_count | INTEGER | | Rows fetched |
| date_min | DATE | | Earliest observation in batch |
| date_max | DATE | | Latest observation in batch |
| sha256 | VARCHAR | | Hash of raw response body for reproducibility |
| url_or_path | VARCHAR | | Exact URL or filesystem path used for retrieval |
| status | VARCHAR | NOT NULL | See lifecycle below |
| notes | VARCHAR | | Error message, fallback activated, or verification notes |
| | | PRIMARY KEY | (source, downloaded_at) |

**Append-only:** Unlike other raw tables, `download_manifest` uses plain `INSERT` (not INSERT OR REPLACE). Each pipeline run appends a new row. PK collisions are prevented by microsecond-precision timestamps.

**Status lifecycle:**
- `verified` — source confirmed accessible, no data downloaded yet (Priority 1b verification step)
- `success` — data downloaded and inserted into raw table
- `failure` — download attempted and failed
- `unavailable` — source confirmed not machine-readable; fallback activated

A single source may have multiple manifest rows (e.g., one `verified`, then one `success`). This is intended — the manifest is an audit trail.

### 3.9 Conflict Resolution (Idempotency)

**Raw tables (banrep_trm_daily, banrep_ibr_daily, banrep_intervention_daily, fred_daily, fred_monthly, dane_ipc_monthly, dane_ipp_monthly):** `INSERT OR REPLACE` on conflict with the primary key. The upstream source is the authority — if a re-download produces different values for the same PK, the newer value wins. The `_ingested_at` column (where present) records when the overwrite occurred.

**Calendar tables (dane_release_calendar, bls_release_calendar):** `INSERT OR REPLACE` — same rationale. Calendar data is manually compiled or API-sourced; corrections overwrite.

**download_manifest:** `INSERT` only (append). Never overwrites.

**Derived tables (weekly_panel, daily_panel):** Recomputed via `CREATE OR REPLACE TABLE ... AS (SELECT ...)`. This is atomic in DuckDB — no partial states.

### 3.10 banrep_ibr_daily

Daily IBR overnight effective rate from BanRep SDMX REST API (`DF_IBR_DAILY_HIST`). Used to construct BanRep policy-rate surprises (change in IBR around BanRep announcement dates).

| Column | Type | Constraint | Notes |
|---|---|---|---|
| date | DATE | PRIMARY KEY | Trading day. Parsed from SDMX TIME_PERIOD (format: YYYYMMDD). |
| ibr_overnight_er | DOUBLE | NOT NULL | IBR overnight effective rate (%). SUBJECT=`IRIBRM00`, UNIT_MEASURE=`ER`. |
| _ingested_at | TIMESTAMP | NOT NULL DEFAULT current_timestamp | Row-level audit |

**Ingestion rule:** SDMX response is XML (SDMX-ML Generic Data v2.1). Parse `ObsValue` for the rate, `TIME_PERIOD` for the date. Filter dimensions: SUBJECT=`IRIBRM00`, UNIT_MEASURE=`ER`. Date range: 2008-01-02 to present.

**Rate-surprise construction (estimation module):** The BanRep rate surprise is computed as the change in IBR overnight around BanRep board meetings (typically last Friday of each month). s_t^BanRep = IBR(meeting_day+1) - IBR(meeting_day-1). This requires a BanRep meeting calendar (analogous to `dane_release_calendar`). The meeting calendar is NOT defined in this spec — it is an estimation-module input. The pipeline provides the raw daily IBR series; the estimation module constructs the surprise.

### 3.11 banrep_intervention_daily

Daily FX intervention data from SUAMECA, extracted via Playwright. Records BanRep's USD purchases/sales across 8 intervention mechanisms.

| Column | Type | Constraint | Notes |
|---|---|---|---|
| date | DATE | PRIMARY KEY | Intervention date (only dates with intervention activity appear) |
| discretionary | DOUBLE | | Intervención discrecional (millions USD). NULL if no activity. |
| direct_purchase | DOUBLE | | Compra directa (millions USD) |
| put_volatility | DOUBLE | | Opciones put para control volatilidad (millions USD) |
| call_volatility | DOUBLE | | Opciones call para control volatilidad (millions USD). Negative = BanRep selling USD. |
| put_reserve_accum | DOUBLE | | Opciones put para acumulación de reservas (millions USD) |
| call_reserve_decum | DOUBLE | | Opciones call para desacumulación de reservas (millions USD) |
| ndf | DOUBLE | | NDF (Non delivery forward) sales (millions USD) |
| fx_swaps | DOUBLE | | FX Swaps sales (millions USD) |
| _ingested_at | TIMESTAMP | NOT NULL DEFAULT current_timestamp | Row-level audit |

**Source:** Cached at `contracts/data/raw/banrep_fx_intervention.json` (extracted via Playwright from SUAMECA on 2026-04-16). 1,674 records, 1999-12-01 to 2024-10-04.

**Ingestion rule:** Load JSON, parse date from `YYYY/MM/DD` format, cast amount strings to DOUBLE (empty string → NULL). Only dates with at least one non-empty intervention column appear in the source data.

**Intervention dummy construction:** For the weekly/daily panels, `intervention_dummy = 1` if ANY intervention column is non-NULL on that date (or within that week for the weekly panel). The amounts are also available for continuous intervention controls if the estimation module wants to test intervention magnitude rather than a binary dummy.

**Update cadence:** Quarterly manual re-extraction via Playwright script. The SUAMECA portal is an Angular SPA that requires a browser runtime — `curl`/`requests` cannot access the rendered table data.

---

## 4. Derived Tables

### 4.1 weekly_panel

The estimation-ready dataset for OLS primary and sensitivity specs. One row per Monday-to-Friday week. Recomputed from raw tables via `CREATE OR REPLACE TABLE` — never manually edited.

| Column | Type | Notes |
|---|---|---|
| week_start | DATE | Monday of the week (PK) |
| rv | DOUBLE | Realized vol: sum of squared daily COP/USD log-returns |
| rv_cuberoot | DOUBLE | rv^(1/3) — pre-committed primary LHS |
| rv_log | DOUBLE | log(rv) — exploratory LHS |
| n_trading_days | SMALLINT | Number of daily returns in RV (typically 3–5; no scaling applied) |
| vix_avg | DOUBLE | Weekly average of VIXCLS daily closes |
| vix_friday_close | DOUBLE | VIXCLS on last available US trading day of the week |
| oil_return | DOUBLE | Weekly WTI log-return: log(last_price_this_week / last_price_prior_week) |
| oil_log_level | DOUBLE | log(WTI last available price this week) — sensitivity A8 |
| us_cpi_surprise | DOUBLE | AR(1) residual of CPIAUCSL MoM % change; **0.0** on non-release weeks |
| cpi_surprise_ar1 | DOUBLE | AR(1) residual of DANE IPC MoM % change; **0.0** on non-release weeks. **Confirmed primary RHS variable** (EME survey data unavailable — see §1 Priority 1c). |
| dane_ipc_pct | DOUBLE | IPC MoM % change on release week; **0.0** on non-release weeks |
| dane_ipp_pct | DOUBLE | IPP MoM % change on release week; **0.0** on non-release weeks |
| banrep_rate_surprise | DOUBLE | Change in IBR overnight around BanRep board meeting; **0.0** on non-meeting weeks. Constructed from `banrep_ibr_daily`. Available from 2008. |
| intervention_dummy | SMALLINT | 1 if BanRep intervened in FX market this week (any type); 0 otherwise. From `banrep_intervention_daily`. |
| intervention_amount | DOUBLE | Total net intervention amount (millions USD) this week; 0.0 on non-intervention weeks. Sum across all 8 types. |
| is_cpi_release_week | BOOLEAN | TRUE if DANE CPI was published this week (per release calendar) |
| is_ppi_release_week | BOOLEAN | TRUE if DANE PPI was published this week (per release calendar) |

**Indefinitely deferred (requires Bloomberg or manual PDF digitization):**
- `cpi_surprise_survey` — BanRep EME consensus-based CPI surprise. EME data is not machine-readable (see §1 Priority 1c).

**NULL vs 0 semantics:** Surprise and release-indicator columns store **0.0** on non-release weeks (no news = no surprise). This is the correct econometric value — OLS cannot operate on NULLs, and "no release occurred" is informative, not missing. NULL is reserved for genuinely missing/unknown data (e.g., a FRED series gap where the observation should exist but doesn't).

**0.0 mixture distribution note:** With ~260 release weeks out of ~1,100 total, approximately 76% of surprise observations are 0.0 (point mass at zero). This inflates kurtosis. The Jarque-Bera test (T5) may reject normality partly due to the zero-inflation, not genuine non-normality of the error term. **Estimation module should run T5 on the full sample AND on the release-week subsample separately** to distinguish structural zero-inflation from distributional problems. For the GARCH-X daily panel, the effect is more extreme (~4.5% release days), but GARCH-X standard errors on delta already account for sparse exogenous variables.

**RV computation:** For each week, collect all daily COP/USD prices from `banrep_trm_daily` within the Monday–Friday window. Compute log-returns: r_d = log(P_d / P_{d-1}), where P_{d-1} is the **last available prior price regardless of week boundary** (Monday's return uses the prior week's last trading day). Multi-day gaps from holidays are NOT adjusted — the return absorbs the full gap. This is standard per Andersen et al. 2003. RV = sum(r_d^2) over all returns whose "current" day falls within the week.

The first week in the sample has no prior price for its first return; it is dropped from the panel.

**Degenerate weeks:** Weeks with `n_trading_days <= 1` (zero or one return) have undefined or degenerate RV (sum of zero or one squared return). These weeks are retained in the panel for completeness; the estimation module should filter or flag them.

**Oil return computation:** log(last available WTI price this week / last available WTI price prior week), using `fred_daily` WHERE `series_id = 'DCOILWTICO'`. "Last available" means the latest non-NULL trading day within the Monday–Friday window. WTI is primary; Brent is available in `fred_daily` for ad-hoc sensitivity but does not appear in the weekly panel.

**US CPI surprise construction:** AR(1) on monthly CPIAUCSL MoM % changes. MoM % change = (CPI_t / CPI_{t-1} - 1) * 100 (raw, not annualized). Expanding-window estimation: AR(1) coefficients re-estimated monthly using all data up to t-1. First 12 months are warmup — their surprises are not used. Surprise = actual − AR(1) forecast. Mapped to the week containing the BLS release date via `bls_release_calendar`. 0.0 on all non-release weeks.

**Colombian CPI AR(1) surprise construction:** Same method applied to DANE IPC MoM % changes from `dane_ipc_monthly`. Mapped to release week via `dane_release_calendar`. 0.0 on non-release weeks. First 12 months of DANE IPC are warmup.

**Seasonality note:** DANE IPC is likely NOT seasonally adjusted. A simple AR(1) may not capture seasonal autocorrelation in Colombian CPI (especially food prices in January), leading to systematic under/over-prediction in certain months and inflating the "surprise" with predictable seasonality. **The estimation module should test AR(1) vs AR(12) or seasonal AR(1) on the DANE IPC series** and report which produces residuals with no seasonal autocorrelation. If AR(12) is needed, the pipeline warmup extends to 24 months (2001-01-01 start for DANE IPC).

**Week-to-release mapping:** Join `dane_release_calendar.release_date` to determine which `week_start` each DANE release falls in. Same for `bls_release_calendar`.

### 4.2 daily_panel

The estimation-ready dataset for GARCH(1,1)-X co-primary. One row per COP/USD trading day. Recomputed from raw tables via `CREATE OR REPLACE TABLE`.

| Column | Type | Notes |
|---|---|---|
| date | DATE | Trading day (PK), from `banrep_trm_daily` |
| week_start | DATE | Monday of the week containing this date (`date_trunc('week', date)::DATE`). For join convenience with weekly_panel. |
| cop_usd_return | DOUBLE | log(TRM_d / TRM_{d-1}) — daily COP/USD log-return. **NULL on the first trading day** (no prior TRM); estimation module drops during GARCH initialization. |
| abs_cpi_surprise | DOUBLE | |s_t^CPI| placed on the **exact release date** (from `dane_release_calendar`); 0.0 on all other days |
| cpi_surprise_ar1_daily | DOUBLE | AR(1) CPI surprise (signed) on release date; 0.0 otherwise |
| vix | DOUBLE | VIXCLS daily close (NULL if US holiday — Colombia/US calendar mismatch) |
| oil_return | DOUBLE | Daily WTI log-return (NULL if no WTI observation) |
| oil_log_level | DOUBLE | log(WTI daily price) — for GARCH-X sensitivity A8 (NULL if no WTI observation) |
| banrep_rate_surprise | DOUBLE | Change in IBR overnight on BanRep board meeting day; 0.0 otherwise. From `banrep_ibr_daily`. |
| intervention_dummy | SMALLINT | 1 if BanRep intervened on this date (any type); 0 otherwise. From `banrep_intervention_daily`. |
| is_cpi_release_day | BOOLEAN | TRUE on exact DANE CPI release date |
| is_ppi_release_day | BOOLEAN | TRUE on exact DANE PPI release date |

**Indefinitely deferred:**
- `abs_cpi_surprise_survey` — |survey-based surprise| on release day. Requires Bloomberg or PDF digitization.

The GARCH(1,1)-X variance equation is: h_t = omega + alpha_1 * epsilon_{t-1}^2 + beta_1 * h_{t-1} + delta * abs_cpi_surprise. The surprise enters on the EXACT release date, not spread across the week. On non-release days, the exogenous term is 0 and the conditional variance evolves purely from its own autoregressive dynamics.

**Surprise placement convention:** The pipeline places |s_CPI| on the DANE release date itself (day t). However, TRM on day t does not yet reflect the release (DANE publishes at 6–8pm COT; TRM is computed from earlier trading). The market reaction appears in day t+1's TRM. **The estimation module should test both day-t and day-t+1 surprise placement as robustness.** The day-t convention is the pipeline default; the estimation module can trivially lag the surprise column by one for the t+1 test. This is documented as a deliberate design choice, not an oversight.

### 4.3 Standardization Boundary

The pipeline provides **raw inputs** in both panels. Standardization (mean-subtraction + sigma-division) for the co-primary decomposition's standardized PPI change ($\tilde{s}_t^{\text{PPI}}$) is performed by the **estimation module**, not the data pipeline. The pipeline stores `dane_ipp_pct` (raw MoM % change). The estimation module computes: (dane_ipp_pct - mean(dane_ipp_pct)) / std(dane_ipp_pct) at estimation time.

This boundary is deliberate: the pipeline's job is faithful data acquisition and aggregation. The estimation module owns all statistical transforms that depend on sample selection (e.g., standardization parameters change if the sample window changes for sub-sample splits in sensitivity A3).

**Exception: `cpi_surprise_ar1` and `us_cpi_surprise`.** These AR(1) residuals are sample-dependent (expanding-window coefficients). Strictly, they could belong in the estimation module. They are placed in the pipeline because: (a) the surprise construction is specification-invariant — every spec variant (primary, decomposition, GARCH-X, all sensitivities) uses the same surprise series, and (b) computing once avoids redundant re-estimation across specs. The AR(1) construction is documented here and in the estimation spec for traceability.

### 4.4 Holiday Calendar Mismatch (Colombia vs US)

BanRep TRM follows the Colombian business calendar. VIXCLS and DCOILWTICO follow the US calendar. Mismatches are accepted at weekly frequency:

- Some weeks will have 5 TRM observations but only 4 VIX/oil observations (Colombian workday, US holiday) or vice versa.
- `vix_avg` averages whatever US trading days fall in the week. `vix_friday_close` uses the last available US trading day.
- `oil_return` uses the last available WTI price in each week regardless of whether it falls on the same day as the last TRM observation.
- `n_trading_days` counts COP/USD trading days only (the LHS variable's day count).
- In the daily_panel, `vix` and `oil_return` are NULL on days where US markets are closed but Colombian markets are open. The GARCH-X estimation handles NULLs in control columns appropriately (typically: carry forward or omit the control on that day).

At weekly aggregation, these mismatches introduce negligible noise. No cross-calendar alignment is attempted.

### 4.5 Sample Window for Derived Panels

Raw tables store all available data from each source (TRM from 1991, VIXCLS from 1990, etc.). Derived panels are filtered to the estimation window:

**Start date:** The first Monday after 12 months of DANE IPC data are available. If DANE IPC download starts 2002-01-01, the first usable AR(1) surprise is approximately 2003-01-01, and the first `week_start` in weekly_panel is the Monday of or after 2003-01-01. This ensures AR(1) warmup is complete. If the estimation module needs AR(12)/seasonal AR (per the seasonality note in §4.1), the warmup extends to 24 months — DANE IPC download should start 2001-01-01, pushing the sample start to approximately 2003-01-01 regardless.

**End date:** The last Monday–Friday week for which all required raw data exists (TRM, VIX, oil, DANE releases). Typically the most recent complete week.

This makes the derivation deterministic regardless of how much raw data is loaded.

### 4.6 VIX Endogeneity Note

The weekly_panel provides both `vix_avg` (contemporaneous weekly average) and `vix_friday_close` (point-in-time). These are robustness alternatives but neither fully addresses contemporaneous endogeneity — if a global risk-off event simultaneously raises VIX and COP/USD vol, contemporaneous VIX absorbs some of the CPI-surprise effect that operates through the global risk channel. **The estimation spec should include lagged VIX (prior week's value) as an explicit sensitivity** to break simultaneity. The data pipeline supports this trivially (lag computable from the panel), but it is an estimation-module concern.

---

## 5. Pipeline Flow

```
1. Download Priority 1a (BanRep TRM — verified)
   → fetch from Datos Abiertos Socrata API ($limit=50000)
   → cast valor (string) → DOUBLE, parse vigenciadesde → DATE
   → INSERT OR REPLACE into banrep_trm_daily
   → log manifest (success)
   → if endpoint fails → STOP (escalate to user)

2. Download Priority 1b (BanRep IBR + intervention — verified)
   → IBR: fetch from SDMX REST API (DF_IBR_DAILY_HIST, IRIBRM00, ER)
     → parse XML, extract date + rate
     → INSERT OR REPLACE into banrep_ibr_daily
     → log manifest
   → Intervention: load from cached contracts/data/raw/banrep_fx_intervention.json
     → parse dates (YYYY/MM/DD), cast amounts (empty → NULL)
     → INSERT OR REPLACE into banrep_intervention_daily
     → log manifest
   → EME: log manifest (status=unavailable, notes="PDF-only, no API/download")

3. Download Priority 2 (DANE IPC, IPP)
   → programmatic or manual CSV/Excel fallback
   → INSERT OR REPLACE into dane_ipc_monthly, dane_ipp_monthly
   → compile dane_release_calendar (flag imputed pre-2010 dates)
   → log manifest

4. Download Priority 3 (FRED: VIXCLS, DCOILWTICO, DCOILBRENTEU, CPIAUCSL)
   → convert "." → NULL
   → INSERT OR REPLACE into fred_daily, fred_monthly
   → fetch BLS release dates (release_id=10, file_type=json)
     → INSERT OR REPLACE into bls_release_calendar
   → log manifest

5. Compute derived tables from raw (§4.5 sample window)
   → weekly_panel: RV from TRM, VIX avg + Friday close, oil return + level,
     US CPI AR(1) surprise, Colombian CPI AR(1) surprise (confirmed primary),
     BanRep rate surprise from IBR, intervention dummy + amount,
     DANE release mapping, release-week flags
   → daily_panel: daily returns, week_start, daily surprise placement,
     daily VIX/oil/oil-level, daily IBR rate surprise, daily intervention,
     release-day flags

6. Validate derived tables
   → weekly_panel: row count ≈ 1,100; date range ~2003–2025; no duplicates;
     RV > 0; n_trading_days in [1, 5]; 0.0 not NULL on non-release weeks;
     intervention_dummy in {0, 1}; banrep_rate_surprise = 0.0 on non-meeting weeks
   → daily_panel: row count ≈ 5,500; returns computable (first row NULL);
     surprise only on release dates; intervention_dummy in {0, 1};
     week_start matches date
```

Each step is idempotent. Raw tables use `INSERT OR REPLACE` (except manifest: `INSERT`). Derived tables use `CREATE OR REPLACE TABLE AS (...)`. Re-running the pipeline produces the same result.

---

## 6. Code Location

All new modules in `contracts/scripts/` following existing functional-python style (frozen dataclasses, pure functions, full typing). Tests in `contracts/scripts/tests/`.

Scope constraint: pipeline work touches ONLY `scripts/`, `data/`, `.gitignore`. Never `src/`, `test/*.sol`, `foundry.toml`, or any Solidity.

---

## 7. What This Spec Does NOT Cover

- Estimation code (OLS, GARCH-X, specification tests) — separate spec after data pipeline is validated
- Layer 2 pool parameterization — deferred until β estimated
- BanRep EME survey-based CPI surprise — indefinitely deferred (PDF-only, no machine-readable data; see §1 Priority 1c)
- BanRep meeting calendar for rate-surprise construction — estimation-module input, not defined in this spec
- DANE release calendar compilation — the table schema is defined here; the actual data entry is a separate task
- Sensitivity A4 (release-day exclusion) RV recomputation — the raw daily data supports this; the estimation module handles the exclusion logic
- Sensitivity A1 (monthly horizon) panel — computable from raw tables; estimation module aggregates
- Brent oil as alternative to WTI — raw Brent data is in `fred_daily`; estimation module can compute ad-hoc
- Lagged VIX as endogeneity sensitivity — computable from panel; estimation module concern (§4.6)
- AR(1) vs AR(12)/seasonal AR choice — pipeline provides AR(1); estimation module tests alternatives (§4.1 seasonality note)

---

## 8. Upstream Spec Amendment Required

The upstream spec (`2026-04-15-fx-vol-cpi-surprise.md`, Rev 4) references FRED `DEXCOUS` in §0b, §4.3 table, and marks it as "confirmed free-tier ✓". This series does not exist on FRED — Colombia is not in the H.10 Foreign Exchange Rates program (verified: HTTP 404 on `fred.stlouisfed.org/series/DEXCOUS`; full DEX* enumeration confirms absence).

The upstream spec must be amended to:
1. Replace `DEXCOUS` with BanRep TRM (Datos Abiertos dataset `32sa-8pi3`) as the daily COP/USD source
2. Change the free-tier status to ✓ VERIFIED — TRM is free, unauthenticated, machine-readable (Socrata JSON API, 8,250 rows, 1991–present)
3. Revise §3.3 measurement error discussion: TRM is computed from actual SET FX interbank transactions. The "FRED noon rate vs SET FX close" measurement error source is **eliminated** (not merely mitigated) — TRM IS the SET FX benchmark. The remaining measurement error is TRM's single-daily-rate granularity vs continuous price discovery.
4. Update §4.3 variable table: BanRep EME consensus status from "⚠️ UNVERIFIED" to "UNAVAILABLE (PDF-only)" — AR(1) is the confirmed primary, not fallback
5. Update §4.3 variable table: IBR status from "⚠️ UNVERIFIED" to "✓ VERIFIED (SDMX API, from 2008)"
6. Update §4.3 variable table: SUAMECA intervention status from "⚠️ UNVERIFIED" to "✓ VERIFIED (Playwright extraction, 1,674 records)"
