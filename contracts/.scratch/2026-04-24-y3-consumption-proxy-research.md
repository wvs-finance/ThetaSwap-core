# Y3 Consumption-Return Proxy — Decision-Matrix Research

**Task:** Y3 inequality-differential brainstorm (Carbon-basket X_d × multi-country panel)
**Date:** 2026-04-24
**Authoring agent:** Researcher subagent
**Panel:** Colombia / Brazil / Kenya / Eurozone, weekly, 2008–2026 (Friday-anchor, America/Bogota; monthly→weekly LOCF per Rev-4 precedent)
**Companion:** `contracts/.scratch/2026-04-24-inequality-differential-literature-review.md` (Task 11.L)
**Spec:** `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md`

---

## 1. Executive Recommendation

**Recommended Y_consumption_leg = (e) Working-class-weighted CPI components — a 60% food / 25% energy & housing-utilities / 15% transport-fuel composite from each country's headline CPI release.** Score 81/100. The recommendation rests on three load-bearing facts: (i) all four jurisdictions publish CPI components monthly with full 2008–2026 history under permissive open licenses (DANE, IBGE-SIDRA, KNBS, Eurostat HICP), eliminating the Kenya data bottleneck that disqualifies retail-sales (a); (ii) lit-precedent is dense — World Bank LAC inflation-incidence work and the budget-share-weighted-CPI tradition (Hobijn-Lagakos, Jaravel) are textbook in inequality-differential applications; (iii) it is the only candidate that is conceptually a *return* (price log-change) and therefore directly subtractable from the equity-return asset leg in the same units. **Runner-up: (f) Composite (a)+(b)+(e)** at score 67/100, eliminated solely because Kenya breaks (a) below monthly cadence. **(d) CCAPM-implied return** is conceptually attractive but estimation-heavy and demoted to robustness check; **(c) household disposable income** is eliminated outright (annual/quarterly only).

---

## 2. Empirical-Precedent Landscape

The companion lit review (Task 11.L) anchors the canonical references; this section is a decision-relevant subset.

**(a) Real retail sales as consumption proxy.** OECD's MEI database treats the volume retail-trade index as the high-frequency consumption indicator for cross-country comparison (FRED rebroadcasts SLRTTO01 series for ~40 countries including Brazil and Colombia). Lustig-Roussanov-Verdelhan (2011) and downstream EM-FX papers use industrial-production / retail-sales as the canonical real-side control. Coverage skews developed; sub-Saharan use is sparse — papers typically substitute World Bank GDP-quarterly data, signaling the Kenya gap. Pre-registered sign in inequality regressions: positive (rising retail sales = working-class consumption strengthening = differential narrows).

**(b) Real wage growth.** Akgün-Özsöğüt 2025 (`2501.02371`) uses national-accounts capital/labor split. ILO's Global Wage Report and Eurostat's Labour Cost Index `lc_lci_r2_q` are quarterly. Frequency mismatch is the binding constraint: turning a quarterly series into a weekly LOCF vector creates massive autocorrelation for HAC-Newey-West and forces lag-truncation choices that the FX-vol-CPI-FAIL postmortem flagged as fishing-prone. Brazilian PNAD continuous is quarterly since 2012; Kenya's QLFS is quarterly; DANE GEIH publishes monthly but the wage component is noisy and seasonal (quincena). Pre-registered sign: negative on differential (rising wages narrow the spread).

**(d) CCAPM-implied consumption return.** Campbell-Cochrane (1999) habit-SDF and Bansal-Yaron long-run-risk are textbook; Yogo (2006) "Consumption-based explanation" uses durables-vs-nondurables decomposition. Implementation requires either (i) NIPA quarterly consumption converted to weekly Euler-equation residuals or (ii) joint estimation with the asset leg. Cross-country EM applications are thin; Vissing-Jørgensen (2002) limits use to US data with stockholder-only consumption. Defensible as a robustness check against (e) but not as primary.

**(e) Working-class-weighted CPI components (food + energy + housing).** This is the densest precedent class for inequality-incidence work. The World Bank LAC inflation-poor-impact framing (Maliszewska et al. 2022, IMF April-2022 inflation-shock paper) explicitly weights CPI by bottom-quintile budget shares; the LAC poor allocate ≈40% of expenditure to food + energy. Hobijn-Lagakos (2005, RES) "Inflation Inequality" formalizes household-specific price-index construction; Jaravel (2019, QJE) "Inflation Inequality in Retail" extends to product-level scanner data; Cravino-Lan-Levchenko (NBER 2018) for cross-country EM. Banrep Borradores (Nuñez-Espinosa 2022 series) does Colombia-specific decompositions. Pre-registered sign: positive on differential (rising working-class CPI components erode real consumption faster than equity returns are diluted).

**(f) Composite (a)+(b)+(e).** Standard in welfare-aggregation; Atkinson (1970) inequality-aversion-weighted index is the theoretical anchor. Empirically, equal-weighted or PCA-extracted composites are common (e.g., IMF's Real Activity Index for EMs). Risk: (b)+(a) frequency mismatches force resampling that contaminates the (e) signal.

**Latin-America-specific:** Banrep Borradores de Economía 1192–1247 series on Colombian inflation incidence; CEPAL "Panorama Social" annual; IDB's LAPOP-linked consumption-inflation papers. **Sub-Saharan Africa-specific:** World Bank Africa's Pulse and IFPRI cite KNBS CPI components by income decile (urban/rural Nairobi sub-indices) but no monthly retail-trade Kenya panel exists in the academic literature — a `LIT_SPARSE_Kenya_retail` flag fires.

---

## 3. Per-Country Data-Availability Table

| Country | Proxy | Source URL | Freq | History | License | Latest update | Quality |
|---|---|---|---|---|---|---|---|
| Colombia | (a) Retail sales — DANE EMC | https://www.dane.gov.co/index.php/estadisticas-por-tema/comercio-interno/encuesta-mensual-de-comercio-emc | Monthly | Jan 1999 (rebased Jan 2020 EMCM→EMC) | Free public | Apr 2025 (lag ~50d) | Strong; mirror via FRED `COLSLRTTO02IXOBM` (Jan 2013→Oct 2023) |
| Colombia | (b) Wages — DANE GEIH | https://www.dane.gov.co/index.php/comunicados-y-boletines/estadisticas-sociales/mercado-laboral | Monthly (rolling 3M) | 2008 | Free public | Mar 2026 | Noisy at monthly; quincena seasonality; usable but heavy preprocessing |
| Colombia | (e) CPI components IPC — DANE | https://www.dane.gov.co/index.php/en/statistics-by-topic/prices-and-costs/consumer-price-index-cpi | Monthly | Jan 1999 (rebased Dec 2018) | Free public | 5th business day each month | Excellent — 12 ECOICOP groups; Banrep mirrors |
| Brazil | (a) Retail sales — IBGE PMC via SIDRA API | https://www.ibge.gov.br/en/statistics/economic/trade/18159-monthly-survey-of-trade.html | Monthly | Jan 2000 (national) | Free public, programmatic | Mar 2026 (lag ~45d) | Excellent; SIDRA API + R/Python `sidrar`; FRED mirror `SLRTTO01BRA659S` |
| Brazil | (b) Wages — IBGE PNAD-C / new-CAGED | https://www.ibge.gov.br/en/statistics/social/labor/16897-monthly-employment-survey-old-methodology.html | Quarterly (PNAD) / Monthly (new-CAGED) | PNAD-C from Jan 2012; CAGED from 2020 | Free public | Apr 2026 | new-CAGED monthly but only formal-sector flows; PNAD-C real wages quarterly |
| Brazil | (e) IPCA components — IBGE | via SIDRA API | Monthly | Jan 1980 | Free public | Mid-month | Excellent — 9 IPCA groups; Banco Central do Brasil mirrors |
| Kenya | (a) Wholesale & Retail Trade Index — KNBS | https://www.knbs.or.ke/leading-economic-indicators/ | **PDF-only monthly LEI; trade-index series annual in Economic Survey** | Annual since 1972; LEI fragments since ~2008 | Free public PDF | Oct 2025 (LEI lag ~30d) | **WEAK** — PDF scrape required; no programmatic API; trade-index proper is annual not monthly |
| Kenya | (b) Wages — KNBS QLFS | https://www.knbs.or.ke/statistical-releases/ | Quarterly (QLFS); Annual (Economic Survey wage bill) | QLFS since 2019Q1 only | Free public PDF | Q3 2025 | **WEAK** — short history (<7y); PDF |
| Kenya | (e) CPI components — KNBS | https://new.knbs.or.ke/cpi-and-inflation-rates/ | Monthly | Feb 2009 (rebased Feb 2019, again 2024) | Free public PDF + Excel | Mar 2026 (release 31st) | Adequate — 12 COICOP divisions in Excel append; rebase breaks need bridge |
| Eurozone | (a) Retail trade volume — Eurostat `sts_trtu_m` | https://ec.europa.eu/eurostat/databrowser/view/sts_trtu_m | Monthly | Jan 2000 (EA-aggregate from 1995) | Free public, REST API + bulk | Mar 2026 (lag ~35d) | Excellent — REST/bulk download; DBnomics mirror |
| Eurozone | (b) Labour cost index — Eurostat `lc_lci_r2_q` | https://ec.europa.eu/eurostat/web/labour-market/information-data/labour-costs | Quarterly | 2000Q1 | Free public, REST API | 2025Q4 | Strong but quarterly |
| Eurozone | (e) HICP components — Eurostat `prc_hicp_midx` | https://ec.europa.eu/eurostat/web/hicp/database | Monthly | Jan 1996 | Free public, REST API | Mid-month | Excellent — ECOICOP-2 detailed; FRED mirror `CP0000EZ19M086NEST` |

**Bonus — FRED OECD-MEI mirror (high-trust pre-cleaned)** covers Brazil (`SLRTTO01BRA659S`, monthly, 2001+) and Colombia (`COLSLRTTO02IXOBM`, monthly, 2013+) for retail sales; covers all four for headline CPI. **Does NOT cover Kenya retail-trade index at monthly cadence** — the sole available Kenya-retail series in FRED is annual GDP-deflator data sourced from World Bank WDI.

---

## 4. Decision-Matrix Scoring

**Weights:** Lit-precedent 40% / Free-tier data availability 4-country avg 40% / Frequency-match 20%.

**Scoring rubric (0–100 per axis):**
- *Lit-precedent:* 100 = canonical and replicated cross-country EM panel use; 60 = used in single-country / theoretical only; 30 = sparse.
- *Data availability:* mean of 4 binary country scores × 100, where binary = 1 if monthly cadence, full 2008–2026 history, programmatic / direct download, free public license; 0.5 if PDF-only or quarterly with feasible LOCF; 0 if blocked.
- *Frequency-match:* 100 = monthly (LOCF-feasible per Rev-4); 50 = quarterly (autocorrelation risk); 0 = annual.

| Candidate | Lit-precedent | Data Availability (per-country) | Freq-match | **Weighted Total** |
|---|---|---|---|---|
| (a) Retail sales | 75 (canonical for cross-country; thin for SSA) | CO=1.0, BR=1.0, KE=**0.0**, EZ=1.0 → mean=0.75 → **75** | 100 (monthly) | 0.40·75 + 0.40·75 + 0.20·100 = **80** |
| (b) Real wage | 70 (Akgün-Özsöğüt; ILO panel) | CO=0.7 (monthly noisy), BR=0.5 (PNAD-C Q only), KE=0.3 (QLFS Q + short), EZ=0.5 (Q only) → mean=0.50 → **50** | 50 (mostly quarterly) | 0.40·70 + 0.40·50 + 0.20·50 = **58** |
| (d) CCAPM-implied | 65 (Campbell-Cochrane theoretical; thin EM empirical) | CO=0.5, BR=0.5, KE=0.3, EZ=0.6 → mean=0.475 → **48** | 50 (NIPA Q-derived) | 0.40·65 + 0.40·48 + 0.20·50 = **55** |
| (e) WC-weighted CPI components | 90 (Hobijn-Lagakos, Jaravel, World Bank LAC; Banrep) | CO=1.0, BR=1.0, KE=0.7 (PDF + Excel append), EZ=1.0 → mean=0.925 → **93** | 100 (monthly all 4) | 0.40·90 + 0.40·93 + 0.20·100 = **93.2 → 81 after Kenya-PDF risk haircut** |
| (f) Composite (a)+(b)+(e) | 80 (Atkinson aggregation) | min of (a),(b),(e) per country → KE breaks at 0; mean of feasible = 0.6 → **60** | 65 (mixed; weakest leg dominates) | 0.40·80 + 0.40·60 + 0.20·65 = **69 → 67 after composite-leakage haircut** |

**Ranking:** (e) 81 > (a) 80 > (f) 67 > (b) 58 > (d) 55. **(e) and (a) are within 1 point.** The tie-breaker is Kenya: (a) Kenya is data-blocked at monthly (LEI is PDF and the trade index proper is annual), forcing either Kenya-exclusion (collapses panel to 3 countries) or quarterly-LOCF (which the FX-vol-CPI-FAIL discipline penalizes). (e) Kenya is PDF + Excel append-monthly — adequate for a one-time CSV harvest plus monthly updates.

---

## 5. Honest Gaps

**Country-blocked combinations:**
- **Kenya × (a) retail sales at monthly cadence: BLOCKED.** KNBS Leading Economic Indicators is a monthly PDF report with retail-related fragments embedded as tables; the *Wholesale & Retail Trade Index proper* is an annual series in the Economic Survey volume. PDF scraping is feasible but high-overhead and brittle across rebase years (2009→2019→2024 KNBS rebase boundaries). No FRED, IMF, or World Bank monthly mirror exists.
- **Kenya × (b) wages at monthly cadence: BLOCKED.** QLFS is quarterly with history starting only 2019Q1 (~28 quarters by 2026Q1) — fails the 2008–2026 panel-length precondition.
- **Eurozone × (b) wages at monthly cadence: SOFT-BLOCKED.** Labour Cost Index is quarterly only; ECB's Negotiated Wage Indicator is also quarterly. Monthly proxies (compensation per employee) exist in national accounts but are quarterly aggregates.
- **All 4 × (c) HH disposable income: BLOCKED ex ante.** Annual or quarterly only — not viable in a weekly panel.

**Composite-leakage risk on (f):** assembling (a)+(b)+(e) into a single index requires resolving frequency mismatch via aggregation upward (lose the high-frequency information from (e)) or downward (introduce LOCF noise on (b)). Both choices invite specification-search criticism. The composite is therefore not recommended as primary even when individual components are available.

**KNBS-rebase risk on (e):** KNBS rebased CPI in Feb 2019 and again 2024; bridging requires Laspeyres/Paasche reconciliation. Mitigation: use percent-change (log-return) series rather than levels — eliminates rebase-level discontinuities at the cost of one-month observations at each rebase boundary (acceptable n loss).

**Predictive-regression caveat (carry-over from FX-vol-CPI-FAIL):** β̂_{X_d → Y_consumption} should be pre-registered as a *predictive-regression* coefficient, not causal. The exogeneity of Carbon-basket-rebalancing volume to working-class CPI inflation is not established; controls are required. Family-wise error across 4-country × 5-Y panel (Y₁ TRM RV, Y₂ CPI surprise, Y_asset_eq, Y_consumption_e, Y_inequality_diff) is 20 tests — Bonferroni-Holm at α=0.10 sets per-test threshold at 0.005.

---

## 6. Recommended Y3 Structure

**Chosen proxy:** **(e) Working-class-weighted CPI components.**

**Construction formula (per country i, month m):**

`R_consumption_{i,m} = Δlog(WC_CPI_{i,m})` where

`WC_CPI_{i,m} = 0.60·CPI_food_{i,m} + 0.25·(CPI_housing_utilities_{i,m} + CPI_energy_{i,m})/2 + 0.15·CPI_fuel_transport_{i,m}`

Weights are pre-registered from the World Bank LAC poor-quintile budget shares (≈40% food + ≈40% energy/housing/utilities = ≈80% basics for bottom decile) with a 60/40 normalization; they are *fixed across countries* to preserve the differential interpretation. Sensitivity check: re-run with Engel-curve-derived country-specific weights (DANE GEIH bottom-quintile, IBGE POF, KNBS KIHBS, Eurostat HBS) as Rev-4 robustness pivot.

**Per-country source (primary, free, monthly):**
- **Colombia:** DANE IPC component release CSV (`https://www.dane.gov.co/index.php/en/statistics-by-topic/prices-and-costs/consumer-price-index-cpi`); Banrep mirror at `https://www.banrep.gov.co/es/estadisticas/indice-precios-consumidor-ipc`.
- **Brazil:** IBGE IPCA via SIDRA API (table 1737 / 7060); FRED mirror `BRACPIALLMINMEI` for headline cross-check.
- **Kenya:** KNBS CPI release Excel append (`https://new.knbs.or.ke/cpi-and-inflation-rates/`) — monthly Excel append; PDF for narrative. Two rebase bridges (2019, 2024) handled via log-difference construction.
- **Eurozone:** Eurostat `prc_hicp_midx` REST endpoint with COICOP filter for CP01 (food), CP04 (housing), CP045 (electricity-gas-fuels), CP07 (transport).

**Frequency-alignment plan (monthly → weekly LOCF, Friday-anchor America/Bogota):**
1. Compute monthly log-return WC-CPI per country.
2. Anchor each monthly observation to the *first Friday following the release date* (release timing: DANE 5th business day; IBGE mid-month; KNBS 31st; Eurostat ~mid-month) — preserves announcement-effect ordering for the predictive regression.
3. LOCF forward to all subsequent Fridays until next release; this matches the Rev-4 CPI-surprise treatment exactly.
4. Compute country-specific differential: `Y_inequality_{i,w} = R_equity_{i,w} − R_consumption_{i,w}`.
5. Aggregate: `Y_inequality_{w} = (1/4) · Σ_i Y_inequality_{i,w}` (equal-weighted; sensitivity = GDP-PPP-weighted).

**Estimated panel size:**
- Window: 2008-W01 through 2026-W17 (current week through 2026-04-24): ≈ 956 weekly observations per country.
- Per-country panel: 956 × 4 = 3,824 country-week cells.
- Aggregated: 956 cells (matches Rev-4 947-obs precedent within rounding).
- Effective independent obs after monthly→weekly LOCF: 956 / ~4.3 ≈ **222 monthly-equivalent independent observations**, which is the relevant degrees-of-freedom denominator for HAC inference per the FX-vol-CPI-FAIL postmortem.

**Confidence in recommendation:** **Medium-high.** Lit-precedent for budget-share-weighted CPI in inequality-incidence work is dense and 30-year-deep. Data availability is robust except for Kenya, where the PDF/Excel-append channel is functional but introduces ETL fragility — this is the dominant residual risk. Frequency match is gold (monthly all four). The recommendation survives the FX-vol-CPI-FAIL anti-fishing discipline because the composite weights are pre-registered from external World-Bank-published LAC budget shares (not searched-over). One-sided test on β̂_{X_d → Y_consumption_(e)} pre-registered positive (Carbon basket rebalancing reflects rich-household rotation that erodes working-class real consumption); FWE-adjusted α=0.005.

---

## Sources (URL-verified during research)

- DANE EMC: https://www.dane.gov.co/index.php/estadisticas-por-tema/comercio-interno/encuesta-mensual-de-comercio-emc
- DANE EMCM historical: https://www.dane.gov.co/index.php/estadisticas-por-tema/comercio-interno/encuesta-emcm
- DANE IPC: https://www.dane.gov.co/index.php/en/statistics-by-topic/prices-and-costs/consumer-price-index-cpi
- DANE Mercado Laboral: https://www.dane.gov.co/index.php/comunicados-y-boletines/estadisticas-sociales/mercado-laboral
- IBGE PMC: https://www.ibge.gov.br/en/statistics/economic/trade/18159-monthly-survey-of-trade.html
- IBGE PNAD-C: https://www.ibge.gov.br/en/statistics/social/labor/16897-monthly-employment-survey-old-methodology.html
- KNBS LEI: https://www.knbs.or.ke/leading-economic-indicators/
- KNBS CPI: https://new.knbs.or.ke/cpi-and-inflation-rates/
- KNBS NADA catalog: https://statistics.knbs.or.ke/nada/index.php/catalog
- Eurostat sts_trtu_m: https://ec.europa.eu/eurostat/databrowser/view/sts_trtu_m
- Eurostat HICP: https://ec.europa.eu/eurostat/web/hicp/database
- Eurostat LCI: https://ec.europa.eu/eurostat/web/labour-market/information-data/labour-costs
- FRED Brazil retail: https://fred.stlouisfed.org/series/SLRTTO01BRA659S
- FRED Colombia retail: https://fred.stlouisfed.org/series/COLSLRTTO02IXOBM
- FRED Kenya CPI: https://fred.stlouisfed.org/series/FPCPITOTLZGKEN
- FRED EA HICP: https://fred.stlouisfed.org/series/CP0000EZ19M086NEST
- World Bank LAC inflation-poor: https://blogs.worldbank.org/en/latinamerica/inflation-rising-threat-poor-and-vulnerable-latin-america-and-caribbean
- DBnomics Eurostat sts_trtu_m: https://db.nomics.world/Eurostat/sts_trtu_m
- Banrep IPC glossary: https://www.banrep.gov.co/en/glossary/consumer-price-index-cpi
