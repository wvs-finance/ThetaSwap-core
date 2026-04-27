# Reality Checker Review: Data Schema & Acquisition Strategy (2026-04-16)

**Spec reviewed:** `contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md`
**Upstream spec:** `contracts/notes/structural-econometrics/specs/2026-04-15-fx-vol-cpi-surprise.md` (Rev 4)
**Reviewer:** RealityIntegration (Integration Agent)
**Date:** 2026-04-16

---

## Issue 1: DEXCOUS Does Not Exist on FRED

**Classification: BLOCK**

The spec's entire RV pipeline depends on FRED series `DEXCOUS` for daily COP/USD exchange rates (referenced in sections 1, 3.1, 4.1, and 5). This series does not exist. HTTP GET to `https://fred.stlouisfed.org/series/DEXCOUS` returns 404.

FRED's H.10 Foreign Exchange Rates program publishes daily spot rates for approximately 22 currencies. Colombia is not among them. The full set of DEX* series is: DEXBZUS (Brazil), DEXCAUS (Canada), DEXCHUS (China), DEXDNUS (Denmark), DEXHKUS (Hong Kong), DEXINUS (India), DEXJPUS (Japan), DEXKOUS (South Korea), DEXMAUS (Malaysia), DEXMXUS (Mexico), DEXNOUS (Norway), DEXSDUS (Sweden), DEXSFUS (South Africa), DEXSIUS (Singapore), DEXSLUS (Sri Lanka), DEXSZUS (Switzerland), DEXTAUS (Taiwan), DEXTHUS (Thailand), DEXUSAL (Australia), DEXUSEU (Euro), DEXUSNZ (New Zealand), DEXUSUK (UK), DEXVZUS (Venezuela).

The only COP/USD series available on FRED are OECD-sourced monthly or quarterly aggregates (COLCCUSMA02STM, COLCCUSSP02STM, COLCCUSMA02STQ, COLCCUSSP02STQ). These are monthly/quarterly frequency and cannot be used for weekly realized volatility construction from daily returns.

**Impact:** The entire RV computation pipeline is built on a nonexistent data source. This also propagates to the upstream spec (Rev 4 section 0b, 4.3 table) which references FRED DEXCOUS and marks it as confirmed free-tier.

**Required fix:** The daily COP/USD source must change. The correct source is BanRep's TRM (Tasa Representativa del Mercado), published daily by the Banco de la Republica. BanRep publishes this as a downloadable time series going back to at least 1991. This means:
1. COP/USD daily data must move from Priority 3 (FRED, safe) to Priority 1 or Priority 2 (BanRep, needs verification of programmatic access).
2. The `fred_daily` table's `series_id` values must remove `DEXCOUS`.
3. A new raw table (e.g., `banrep_trm_daily`) must be added.
4. The entire risk ordering changes: the single most important input to the model (daily FX rate for RV construction) is no longer from FRED. It depends on BanRep access.
5. The upstream spec must also be amended -- DEXCOUS is referenced there too and marked as free-tier confirmed.

**Note:** be_1171 (the BanRep paper the upstream spec relies on) uses TRM directly, not FRED DEXCOUS. This confirms the correct source is BanRep, not FRED.

---

## Issue 2: Row Count Estimates for DEXCOUS Are Moot, but ~22K Is Too High Regardless

**Classification: FLAG**

The spec claims ~22K daily rows per FRED series since 2003. For a daily business-day series from 2003 to 2025, the actual count is approximately 252 trading days/year x 22 years = ~5,544 rows. Even from 1971 (DEXUSAL start), that would be ~252 x 54 = ~13,600 rows. The ~22K figure is unrealistically high for any single daily FRED series. For VIXCLS (available since 1990), the count would be ~252 x 35 = ~8,800 rows.

This is moot for DEXCOUS (which does not exist), but the row count estimate should be corrected for the remaining FRED daily series (VIXCLS, DCOILWTICO, DCOILBRENTEU) so that validation step 5 uses realistic thresholds.

**Required fix:** Replace "~22K daily rows per FRED series since 2003" with realistic estimates: ~5,500 rows per daily series for 2003-2025.

---

## Issue 3: FRED Missing Value Handling Not Specified

**Classification: FLAG**

FRED returns the string `"."` for missing observations (holidays, data gaps). The spec defines `value DOUBLE` with "NULL = FRED missing/holiday marker" but does not specify how `"."` strings in the JSON response get converted to SQL NULLs during ingestion. This is a common source of silent data corruption -- if the ingestion script parses `"."` as a string and DuckDB casts it, the behavior depends on the CAST implementation (could be NULL, could error, could be 0.0).

**Required fix:** Add explicit ingestion rule: "FRED observations with value = '.' must be stored as SQL NULL. The download script must handle this before INSERT."

---

## Issue 4: DANE Programmatic Access Is Historically Unreliable -- No Specific Endpoint Documented

**Classification: FLAG**

The spec correctly notes that "DANE data (CPI index, PPI index) is confirmed free but programmatic access is historically unreliable" and has a manual CSV fallback. This is accurate. However, the spec provides no specific URL, API endpoint, or portal path for DANE. DANE has changed its data portal at least three times (DANE Web, SEN, DANE Datos Abiertos at datos.gov.co). The current primary entry point is https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/indice-de-precios-al-consumidor-ipc for CPI data downloads.

The fallback to manual CSV download for ~260 rows is practical and well-sized. This is not a BLOCK because the fallback is adequate, but documenting the known entry points would save implementation time.

**Suggested improvement:** Add known DANE URLs in a comment or note for the implementer, even if they may change.

---

## Issue 5: Release Calendar Compilation -- 520 Rows Is Feasible but Labor-Intensive and May Have Gaps Pre-2010

**Classification: FLAG**

The spec requires manually compiling ~520 DANE release dates (CPI + PPI, 2003-2025). DANE publishes annual release calendars ("calendario de difusion" or "calendario de publicaciones"), but:

1. Historical calendars before roughly 2010-2012 may not be available on the current DANE website. The Wayback Machine may be needed.
2. Even when available, calendars are typically published as PDF or image files, not machine-readable tables.
3. The actual release date may differ from the scheduled date (DANE has occasionally delayed releases). The spec does not distinguish between scheduled and actual release dates.
4. For PPI specifically, DANE's publication schedule has changed over the years (base-year rebasing in 2014 from IPP base 1999 to IPP base 2014). Release timing may have shifted.

For weeks where the exact release date cannot be determined (pre-2010 gaps), the `is_release_week` flag would be wrong, which directly impacts the identification strategy (upstream spec section 4.4).

**Required fix:** Add a note about expected gaps in historical release calendars and a strategy for handling them (e.g., assume first-week-of-month for months where the exact date is unavailable, and flag those as imputed).

---

## Issue 6: Holiday Calendar Mismatch Between Colombia and US

**Classification: FLAG**

The weekly RV computation aggregates daily COP/USD returns within Monday-Friday windows. Colombian and US markets have different holiday calendars. If COP/USD data comes from BanRep TRM (the correct source per Issue 1), it follows the Colombian holiday calendar. Meanwhile, VIXCLS and WTI follow the US calendar. This means:

1. Some weeks will have 5 COP/USD observations but only 4 VIX observations (Colombian workday, US holiday) or vice versa.
2. The `n_trading_days` column tracks COP/USD days, but VIX averaging uses a potentially different day count.
3. Cross-week log returns for oil (Friday-to-Friday) may hit a US holiday where the prior "Friday close" is actually Thursday's close.

The spec does not address this. At weekly frequency this is likely a minor issue, but it should be documented.

**Required fix:** Add a note on holiday calendar mismatch handling. At minimum: "VIX and oil weekly aggregates use whatever observations are available in the Monday-Friday window from each respective source; day-count mismatches between Colombian and US calendars are accepted at weekly frequency."

---

## Issue 7: Risk-First Priority Ordering Is Sound but Incomplete After Issue 1

**Classification: FLAG**

The risk-first ordering (BanRep/SUAMECA first, DANE second, FRED last) was sound under the assumption that FRED was safe. With DEXCOUS nonexistent, the daily COP/USD exchange rate -- the single most critical input (it builds the LHS variable) -- is now a BanRep dependency. This changes the risk profile fundamentally:

- Priority 1 should include BanRep TRM daily (not just EME, IBR, SUAMECA).
- If BanRep's TRM daily is unavailable programmatically, the entire model cannot be estimated at weekly frequency. There is no FRED fallback for daily COP/USD.
- The decision tree (section 1, Priority 1) needs a branch for "TRM daily unavailable" with an appropriate fallback or STOP condition.

**Required fix:** Add BanRep TRM daily to Priority 1. Add a STOP/BLOCK condition if TRM daily is not obtainable -- without it, the pipeline produces nothing.

---

## Issue 8: US CPI AR(1) Surprise Needs BLS Release Calendar

**Classification: NIT**

The spec mentions that US CPI surprise is "mapped to the week containing the BLS release date (BLS publishes a release calendar analogous to DANE's)" but does not include a BLS release calendar table or acquisition step. The BLS release schedule is available at https://www.bls.gov/schedule/news_release/cpi.htm and is machine-readable, but the spec does not allocate a raw table for it or include it in the pipeline flow.

For ~260 monthly US CPI releases over 2003-2025, this is a small but necessary data source that is currently missing from the schema.

**Required fix:** Add a `bls_release_calendar` table (or equivalent) and include BLS release schedule acquisition in the pipeline flow.

---

## Issue 9: FRED API Rate Limits Not Documented

**Classification: NIT**

FRED API has a rate limit of 120 requests per 60 seconds per API key. With 5 series to download, this is not a practical concern for initial download (5 requests). However, if the pipeline is re-run frequently or extended with additional series, the rate limit should be documented.

**Required fix:** Add a note: "FRED API rate limit: 120 requests/minute. Not a binding constraint for this pipeline."

---

## Issue 10: AR(1) Fallback for BanRep EME Is Well-Specified but Carries a Subtle Issue

**Classification: NIT**

The AR(1) fallback for CPI surprise (section 4.1 of upstream spec, referenced in section 1 of this spec) is conceptually sound and well-documented as a "different object." However, the AR(1) model on monthly CPI MoM changes requires a warmup period. The spec says CPIAUCSL starts "1yr before DEXCOUS start" for warmup, which is for US CPI. If the Colombian CPI AR(1) fallback is activated, the Colombian IPC series also needs warmup rows (at least 12 months before the estimation sample starts). The current `dane_ipc_monthly` table has no explicit provision for pre-sample warmup rows.

**Required fix:** Note that if the AR(1) fallback is activated for Colombian CPI, the DANE IPC download must start at least 12 months before the estimation sample (i.e., 2002 if sample starts 2003).

---

## Issue 11: DuckDB Version Pinning Is Good Practice

**Classification: NIT**

The spec pins DuckDB 1.5.1, which is good. No issue here; just noting it as a positive.

---

## Issue 12: weekly_panel RV Computation -- Cross-Week Return at Week Boundaries

**Classification: NIT**

The RV computation collects daily COP/USD observations within Monday-Friday and computes log-returns r_d = log(P_d / P_{d-1}). On the first trading day of the week (typically Monday), P_{d-1} is the previous Friday's close, which belongs to the prior week. The spec does not clarify whether this cross-week return is included in the current week's RV or excluded.

If included (standard practice): the Monday return captures weekend information, which is desirable. If excluded: the first day of each week contributes no return, systematically reducing RV. The spec should be explicit.

**Suggested improvement:** State explicitly: "The first log-return of each week uses the prior week's last trading day close as P_{d-1}. This cross-week return is included in the current week's RV."

---

## Summary Table

| # | Issue | Classification | Status |
|---|---|---|---|
| 1 | DEXCOUS does not exist on FRED | BLOCK | Must fix before implementation |
| 2 | Row count estimate ~22K is wrong (~5.5K realistic) | FLAG | Correct for validation accuracy |
| 3 | FRED "." missing value handling unspecified | FLAG | Add explicit ingestion rule |
| 4 | DANE endpoint URLs not documented | FLAG | Add known URLs for implementer |
| 5 | Release calendar gaps pre-2010 likely | FLAG | Add imputation strategy |
| 6 | Holiday calendar mismatch (Colombia vs US) | FLAG | Document accepted limitation |
| 7 | Risk ordering must include TRM daily in Priority 1 | FLAG | Restructure priorities |
| 8 | BLS release calendar table missing | NIT | Add table and pipeline step |
| 9 | FRED rate limits undocumented | NIT | Add note |
| 10 | Colombian AR(1) fallback needs warmup rows | NIT | Add pre-sample note |
| 11 | DuckDB version pinning (positive) | NIT | No action |
| 12 | Cross-week return boundary unclear | NIT | Clarify explicitly |

---

## Overall Verdict: NEEDS WORK

**One BLOCK, six FLAGs, five NITs.**

The BLOCK is fatal: the spec's primary data source for the dependent variable (FRED DEXCOUS for daily COP/USD) does not exist. This is not a minor parameter error -- it invalidates the entire pipeline as written and forces a redesign of the acquisition priority ordering. The correct source (BanRep TRM daily) moves the LHS variable from "safe, do-last" to "must-verify-first," which is a fundamental change to the spec's risk architecture.

The FLAGs are individually manageable but collectively indicate the spec was written with insufficient verification of the data sources it claims to use. The DANE and BanRep sections show appropriate caution; the FRED section shows overconfidence.

**Recommended next steps:**
1. Fix the BLOCK: Replace DEXCOUS with BanRep TRM daily. Restructure Priority 1 to include TRM. Add a STOP condition if TRM is unavailable.
2. Address FLAGs in a revision pass.
3. Re-verify that the upstream spec (Rev 4) also corrects its DEXCOUS references.
4. Re-submit for review after fixes.

---

**Reviewer:** RealityIntegration
**Evidence method:** HTTP status code verification of FRED series URLs (curl -s -o /dev/null -w "%{http_code}"), FRED search results page scraping for DEX* series enumeration
**Confidence in BLOCK finding:** HIGH -- 404 is unambiguous; full DEX* enumeration confirms Colombia is not in the H.10 program
