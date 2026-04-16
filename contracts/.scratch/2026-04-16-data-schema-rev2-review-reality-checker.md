# Reality Checker Review: Data Schema & Acquisition Strategy Rev 2

**Reviewer:** Reality Checker (Integration Agent)
**Date:** 2026-04-16
**Spec reviewed:** `contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md` (Rev 2)
**Upstream spec:** `contracts/notes/structural-econometrics/specs/2026-04-15-fx-vol-cpi-surprise.md` (Rev 4)
**Verification method:** Live HTTP requests to FRED, BanRep, Datos Abiertos Colombia APIs

---

## Issue 1: BanRep TRM is available on Datos Abiertos Colombia as a free Socrata API — spec does not mention this

**Classification: FLAG**

The spec treats TRM as "highest uncertainty" and describes a STOP condition if unavailable. In reality, TRM is available as a **free, unauthenticated Socrata JSON API** on Colombia's Datos Abiertos portal:

- **Endpoint:** `https://www.datos.gov.co/resource/32sa-8pi3.json`
- **Date range:** 1991-12-02 to present (verified live: today's value = 3603.19 COP)
- **Row count:** 8,250 rows (verified via `$select=count(*)`)
- **Format:** JSON with fields `valor` (COP per USD), `vigenciadesde` (date), `vigenciahasta` (date), `unidad` (always "COP")
- **Pagination:** Standard Socrata `$limit` and `$offset` — default limit is 1,000 rows, so the download script MUST set `$limit=10000` or paginate
- **Authentication:** None required (public dataset)
- **No rate limit observed** for single-client sequential requests

This is not "highest uncertainty." This is a confirmed, machine-readable, free data source with 34+ years of history. The spec should:

1. Document the exact Datos Abiertos endpoint and dataset ID (`32sa-8pi3`)
2. Downgrade TRM from "highest uncertainty" to "verified" in the priority ordering
3. Note the Socrata pagination requirement (default 1,000 row limit)
4. Note that `valor` is a string field that needs DOUBLE casting
5. Note that `vigenciadesde` includes a `T00:00:00.000` timestamp suffix requiring date parsing

The STOP condition is still sound in principle (no TRM = no pipeline), but the probability of the STOP condition activating is near zero given this verified endpoint.

**Recommendation:** Add the Datos Abiertos endpoint to the spec. Move TRM verification from "must be verified" to "verified" with the endpoint documented. Keep the STOP condition as defensive coding.

---

## Issue 2: Socrata API pagination not documented — risk of silent truncation to 1,000 rows

**Classification: FLAG**

The Datos Abiertos Socrata API defaults to returning only 1,000 rows per request. The TRM dataset has 8,250 rows. If the download script does not explicitly set `$limit=50000` (or paginate), it will silently return only the most recent 1,000 observations, producing a dataset starting around 2022 instead of 1991.

This is a known Socrata footgun. The spec should mandate either:
- `$limit=50000` (safe upper bound) in the request URL, OR
- Explicit pagination loop with `$offset` and `$limit=5000` chunks

**Recommendation:** Add a note to the spec about Socrata's default 1,000-row limit and the required `$limit` parameter.

---

## Issue 3: FRED series verification — all four confirmed real

**Classification: PASS (no issue)**

Verified via live HTTP requests to `fred.stlouisfed.org`:

| Series ID | Page title | Status |
|---|---|---|
| `VIXCLS` | "CBOE Volatility Index: VIX (VIXCLS)" | EXISTS. Range: 1990-01-02 to 2026-04-15. Daily. |
| `DCOILWTICO` | "Crude Oil Prices: West Texas Intermediate (WTI) - Cushing, Oklahoma (DCOILWTICO)" | EXISTS. Daily. |
| `DCOILBRENTEU` | "Crude Oil Prices: Brent - Europe (DCOILBRENTEU)" | EXISTS. Daily. |
| `CPIAUCSL` | "Consumer Price Index for All Urban Consumers: All Items in U.S. City Average (CPIAUCSL)" | EXISTS. Monthly. |

All four series exist and are accessible on FRED. The spec's claims are accurate.

---

## Issue 4: FRED `DEXCOUS` nonexistence — confirmed

**Classification: PASS (no issue — spec correctly identifies the problem)**

`https://fred.stlouisfed.org/series/DEXCOUS` returns an error page (`<title>Error - St. Louis Fed</title>`). The spec's claim that DEXCOUS does not exist is **verified**. Colombia is indeed not in the H.10 Foreign Exchange Rates program.

---

## Issue 5: FRED release_id=10 = Consumer Price Index — confirmed, with minor precision note

**Classification: NIT**

Verified via the FRED releases page: `<a href="/release?rid=10">Consumer Price Index</a>`. The `fred/release/dates` endpoint is documented and supports both XML and JSON output via `file_type` parameter.

The spec says "release 10 = CPI-U." Technically, release 10 = "Consumer Price Index" (the BLS release), which INCLUDES CPI-U (CPIAUCSL) as well as CPI-W, C-CPI-U, and others. The release dates for release_id=10 are the dates BLS published the CPI report, which covers ALL CPI variants simultaneously. Since CPIAUCSL is part of this release, the dates are correct for the spec's purpose.

**Recommendation:** Change "release 10 = CPI-U" to "release 10 = Consumer Price Index (BLS release covering CPI-U, CPI-W, and others; release dates apply to CPIAUCSL)" for precision.

---

## Issue 6: Row count estimates — reasonable

**Classification: PASS (no issue)**

The spec estimates ~5,500 rows per daily FRED series. Calculation:
- ~252 trading days/year x 23 years (2003-2025) = ~5,796 business days
- Minus ~10 US holidays/year x 23 years = ~230 days
- Net: ~5,566, with additional FRED missing-observation dots reducing further
- ~5,500 is a reasonable rounded estimate (within ~1% of the calculation)

Note: The spec says "earliest available" for FRED series start dates but estimates ~5,500 rows. VIXCLS starts 1990, which would yield ~9,000+ rows if downloaded from earliest available. The ~5,500 estimate is correct only if `observation_start` is set to ~2003. The spec should clarify: is the download from "earliest available" or from 2003? The weekly panel starts ~2003, but the raw table could store more data. This is a minor inconsistency.

**Recommendation:** Clarify whether FRED daily downloads start from "earliest available" (as stated in the Priority 3 table) or from ~2003 (as the row count implies). If from earliest available, update row count to ~9,000 for VIXCLS and ~10,000 for DCOILWTICO.

---

## Issue 7: DANE access reality — programmatic access is unreliable, manual download is the realistic path

**Classification: FLAG**

The spec correctly notes DANE's portal instability. I attempted to check DANE IPC on Datos Abiertos Colombia (`y75b-wh7y`) and received a 404 "dataset.missing" error, confirming that DANE data is NOT reliably available via Socrata API.

The spec's fallback to manual CSV download is the correct approach for ~260 monthly observations. However, the spec should note:
1. DANE's current data portal (`dane.gov.co`) uses a JavaScript-heavy frontend that makes programmatic scraping difficult
2. Historical IPC data is sometimes available as Excel files linked from DANE bulletin pages
3. The manual download is a one-time effort with incremental monthly updates — acceptable for this volume

The spec's Priority 2 ordering and manual fallback strategy are sound.

---

## Issue 8: Risk ordering soundness — correct in principle, but TRM uncertainty is overstated

**Classification: FLAG**

With TRM now confirmed available on Datos Abiertos (Issue 1), the real uncertainty ordering should be:

1. **BanRep EME, IBR, SUAMECA** (genuinely unverified — these are the true unknowns)
2. **DANE IPC/IPP** (known free, unreliable programmatic access)
3. **BanRep TRM** (now verified: free Socrata API, 8,250 rows, 1991-present)
4. **FRED** (lowest uncertainty, as stated)

The spec currently bundles TRM with EME/IBR/SUAMECA as "Priority 1: highest uncertainty." TRM should be separated from the genuinely unverified sources. The STOP condition for TRM is still valid defensively, but the pipeline implementation should attempt TRM download FIRST (it will succeed) and then proceed to verify EME/IBR/SUAMECA.

**Recommendation:** Split Priority 1 into:
- Priority 1a: TRM daily (verified, download immediately)
- Priority 1b: EME, IBR, SUAMECA (genuinely unverified, verify before designing tables)

---

## Issue 9: Upstream spec amendment (section 8) — accurate but incomplete

**Classification: FLAG**

The spec's section 8 correctly identifies that DEXCOUS does not exist on FRED and proposes three amendments to the upstream spec. However, the upstream spec has TWO references to DEXCOUS (line 17 and line 204 of `2026-04-15-fx-vol-cpi-surprise.md`), and section 8 mentions "section 0b, section 4.3 table" which corresponds to these locations. This is accurate.

However, the amendment should also note:
1. The replacement source (BanRep TRM via Datos Abiertos `32sa-8pi3`) is CONFIRMED free-tier, not just "unverified pending confirmation" — the status should be upgraded to verified given the evidence in Issue 1
2. The upstream spec's section 3.3 measurement error discussion about "FRED noon rate vs SET FX close" should be revised: TRM is computed from actual SET FX transactions, so this specific measurement error source is ELIMINATED (not just "partially mitigated" as the data schema spec states)

**Recommendation:** Strengthen the amendment: TRM is verified (not pending), and TRM eliminates (not merely mitigates) the noon-rate measurement error concern in upstream spec section 3.3.

---

## Issue 10: BanRep website returns 404 for `/es/estadisticas/trm`

**Classification: NIT**

The spec mentions "BanRep publishes TRM on their website" without providing a specific URL. When I tested `https://www.banrep.gov.co/es/estadisticas/trm`, it returned HTTP 404. The alternative path `/es/estadisticas/trm-historico` redirected to a bot-protection page (ShieldSquare/PerimeterX). BanRep's statistics portal (`totoro.banrep.gov.co/estadisticas-economicas/`) does reference TRM via a JavaScript-rendered PrimeFaces UI, which is not easily programmatically accessible.

The Datos Abiertos Socrata endpoint (`32sa-8pi3`) is the correct programmatic path, NOT the BanRep website directly.

**Recommendation:** The spec should document that BanRep's own website is NOT the right programmatic source — Datos Abiertos Colombia is. The BanRep website has bot protection and JavaScript-rendered content.

---

## Issue 11: `INSERT OR REPLACE` confirmed working in DuckDB 1.5.1

**Classification: PASS (no issue)**

Verified locally: DuckDB 1.5.1 (installed in `contracts/.venv`) supports `INSERT OR REPLACE` with PRIMARY KEY constraints. The upsert correctly replaces conflicting rows.

---

## Issue 12: TRM `valor` field is a string, not a number

**Classification: NIT**

The Datos Abiertos API returns TRM values as JSON strings (e.g., `"valor":"3603.19"`), not as JSON numbers. The download script must cast `valor` to DOUBLE explicitly. The spec's `banrep_trm_daily.trm` column is `DOUBLE NOT NULL`, which is correct, but the ingestion rule for string-to-double conversion should be documented alongside the FRED `"."` → NULL rule.

**Recommendation:** Add an ingestion rule for BanRep TRM: `valor` (string) must be cast to DOUBLE before INSERT.

---

## Issue 13: Timezone/date semantics for TRM

**Classification: NIT**

The Datos Abiertos response includes `vigenciadesde` and `vigenciahasta` with `T00:00:00.000` timestamps. Both fields contain the same date for TRM. The spec should clarify which field to use as the `date` column (either works; `vigenciadesde` is the natural choice). The timezone is implicitly COT (UTC-5) since these are Colombian business dates, but the API returns no timezone indicator. This is fine for daily data — the date is unambiguous.

**Recommendation:** Document that `vigenciadesde` (or equivalently `vigenciahasta`) is used as the date, with implicit COT timezone.

---

## Issue 14: Missing FRED API default format note

**Classification: NIT**

The FRED `fred/release/dates` endpoint defaults to XML format, not JSON. The spec's endpoint URL in section 3.7 does not include `&file_type=json`. The observations endpoint (section 1, Priority 3) correctly includes `&file_type=json`. The release dates endpoint should also specify JSON format explicitly.

**Recommendation:** Update the `bls_release_calendar` source URL in section 3.7 to include `&file_type=json`.

---

## Issue 15: Weekly panel row count validation — minor inconsistency with daily panel

**Classification: NIT**

Section 5 (Pipeline Flow, step 6) says `weekly_panel` should have ~1,100 rows and `daily_panel` should have ~5,500 rows. The daily panel is keyed on `banrep_trm_daily` dates (Colombian business calendar), which has 8,250 rows from 1991-present. If the sample starts 2003, that is approximately 23 years x ~247 Colombian business days/year = ~5,681 rows. The ~5,500 estimate is reasonable.

However, ~5,500 daily TRM observations / ~5 trading days per week = ~1,100 weeks. This is internally consistent. No issue.

---

## Summary of Findings

| # | Issue | Classification | Status |
|---|---|---|---|
| 1 | TRM available on Datos Abiertos as free Socrata API | FLAG | Spec must document the verified endpoint |
| 2 | Socrata pagination default limit = 1,000 rows | FLAG | Risk of silent truncation |
| 3 | FRED series (4 of 4) confirmed real | PASS | No action needed |
| 4 | DEXCOUS nonexistence confirmed | PASS | Spec correctly identifies this |
| 5 | release_id=10 = CPI (not specifically CPI-U) | NIT | Minor precision improvement |
| 6 | Row count ~5,500 reasonable | PASS | Clarify "earliest available" vs 2003 start |
| 7 | DANE programmatic access unreliable | FLAG | Manual fallback is correct strategy |
| 8 | Risk ordering: TRM uncertainty overstated | FLAG | Split Priority 1 into verified/unverified |
| 9 | Upstream amendment accurate but incomplete | FLAG | TRM is verified, measurement error is eliminated not mitigated |
| 10 | BanRep website returns 404 for TRM page | NIT | Datos Abiertos is the correct path |
| 11 | DuckDB INSERT OR REPLACE works | PASS | Verified on 1.5.1 |
| 12 | TRM `valor` is a string, needs casting | NIT | Document ingestion rule |
| 13 | TRM date field timezone semantics | NIT | Document `vigenciadesde` usage |
| 14 | FRED release/dates defaults to XML | NIT | Add `&file_type=json` |
| 15 | Row counts internally consistent | PASS | No action needed |

**BLOCKs: 0**
**FLAGs: 5** (Issues 1, 2, 7, 8, 9)
**NITs: 6** (Issues 5, 6, 10, 12, 13, 14)
**PASSes: 4** (Issues 3, 4, 11, 15)

---

## Overall Verdict: PASS WITH FLAGS

The spec is factually sound on all major claims. The DEXCOUS correction is accurate. All FRED series exist. The BLS release calendar approach is correct. DuckDB idempotency works. Row counts are reasonable.

The primary gap is that the spec treats TRM as "highest uncertainty" when it is in fact **already verified** — a free Socrata API on Datos Abiertos Colombia with 8,250 rows going back to 1991. The spec should document this endpoint, address pagination, and downgrade TRM's uncertainty level accordingly. The 5 FLAGs are all addressable without architectural changes.

No BLOCKs. The spec can proceed to implementation after addressing the FLAGs.
