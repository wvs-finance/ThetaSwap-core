# Y₃ Inequality-Differential Structural Design

**Date:** 2026-04-24
**Status:** Brainstorm-converged; awaiting plan-fold + 3-way review.
**Trigger:** Carbon-basket X_d design at `2026-04-24-carbon-basket-xd-design.md` committed primary X_d as basket-aggregate (regional scope, 6 Mento stablecoins × 4 global tokens). The previous Colombia-specific Y_asset_leg = `(Banrep − Fed)/52 + ΔTRM/TRM` no longer matches X_d's regional scope. This document specifies a regional-pan-EM inequality-differential Y₃ that pairs cleanly with the basket-aggregate X_d.
**Brainstorm trail:** five questions Q1-Q5 in this session's continuation of `superpowers:brainstorming`; user approvals on each: (b) 4 anchors / (α) per-country equity primary + (β) bond diagnostic / (e) WC-weighted CPI primary per consumption-proxy research / (I) equal-weighted aggregation / (a) overlap-only primary + (d) +1-year-pre-period sensitivity.

---

## 1. Construct definition

Per-country inequality differential, weekly:

```
Δ_country_t  =  R_equity_country_t  +  Δlog(WC_CPI_country_t)
```

where the rich-side `R_equity_country_t` and working-class-side `−Δlog(WC_CPI_country_t)` (sign-flipped because rising cost-of-living = falling working-class real return) combine into a single differential. The sign convention: `Δ_country_t` rises whenever inequality widens via either channel — rich-equity gains OR working-class cost-of-living squeeze — capturing inequality from both sides.

Pan-regional Y₃ aggregates equal-weighted across the 4 anchor countries:

```
Y₃_t  =  (1/4) × ( Δ_CO_t  +  Δ_BR_t  +  Δ_KE_t  +  Δ_EU_t )
```

---

## 2. Country scope (locked at brainstorm Q1)

| Country | Mento stablecoin | Mento adoption rationale |
|---|---|---|
| Colombia | COPM | Pilot scope per `project_abrigo_inequality_hedge_thesis.md` |
| Brazil | BRLm | Largest LATAM economy on Mento; second-richest equity index history (IBOVESPA) |
| Kenya | KESm | Sub-Saharan Africa anchor; second-largest active Mento user community |
| Eurozone | EURm | Western-Europe anchor; widest-coverage Eurostat data + STOXX 600 |

**Excluded with rationale:** WAEMU/Senegal (XOFm) — KNBS-equivalent agencies in WAEMU publish CPI quarterly best, breaking the weekly-anchored panel; USDm "USD-zone" — too aggregated to test as a single country, and Y₃ is regional-vs-global by construction so the global side belongs to X_d not Y.

---

## 3. Rich asset-return side (locked at brainstorm Q2)

**Primary (in Y₃ definition):**
- `R_equity_country_t = Δlog(equity_index_country_t)` weekly, Friday-anchored America/Bogota
- Per-country indices:
  - Colombia: COLCAP (Banco de la República, daily quotation)
  - Brazil: IBOVESPA (B3, daily quotation)
  - Kenya: NSE 20 (Nairobi Securities Exchange, daily quotation)
  - Eurozone: STOXX 600 (Eurostat / Refinitiv, daily quotation)
- Weekly-aggregation rule: log-return from Friday close to Friday close (or last trading day of the Friday-anchored America/Bogota week)

**Diagnostic (run alongside but not primary):**
- 10Y sovereign-bond yield-change per country, weekly:
  - Colombia: TES 10Y (Banrep)
  - Brazil: NTN-B 10Y (BCB)
  - Kenya: 10Y T-bond (CBK)
  - Eurozone: German Bund 10Y (Bundesbank)

The bond-yield diagnostic captures the EM-rich-portfolio reading where sovereign-bond holdings are top-decile-concentrated; runs as a parallel Y₃_bond_t in Task 11.O resolution matrix without replacing the equity-anchored primary.

**Crypto explicitly excluded from rich-side per Q2 ruling:** crypto-portfolio returns conflate "what drives X_d" (CELO/global-crypto vol per Task 11.N.2 macro-driver finding) with "what rich households' wealth is in" (which is equity/bond/real-estate, <2% crypto per 2024 OECD). Crypto-vol can return as its own Y candidate at Task 11.O if the structural-econometrics skill flags it; not pre-committed here.

---

## 4. Working-class consumption-return side (locked at brainstorm Q3 + research)

**Primary (in Y₃ definition):**
- `Δlog(WC_CPI_country_t)` weekly, Friday-anchored America/Bogota with monthly→weekly LOCF interpolation
- WC-CPI computed per country with **pre-registered budget-share weights**: 60% food / 25% energy+housing-utilities / 15% transport-fuel (World Bank LAC bottom-quintile basket per `2026-04-24-y3-consumption-proxy-research.md` §4 lit-grounded weights)
- Per-country source:
  - Colombia: Banrep CPI components (food, energy, housing utilities, transport-fuel) — programmatic via Banrep open-data
  - Brazil: IBGE IPCA components — programmatic via SIDRA API
  - Kenya: KNBS CPI components — Excel-append monthly (no programmatic API; manual fetch with bridge-series for 2024 rebase NOT needed since post-Sep-2024 series is monolithic)
  - Eurozone: Eurostat HICP components — programmatic via Eurostat REST API

**Sign convention:** `Δlog(WC_CPI)` enters the per-country differential with a `+` sign because WC-CPI is an inverse proxy (rising WC-CPI = falling working-class purchasing power). The differential `Δ_country = R_equity + Δlog(WC_CPI)` rises when inequality widens via either rich-side gains or working-class loss.

**Eliminated outright per research:**
- Real wages: Kenya QLFS quarterly + history start 2019Q1 — fatal frequency mismatch + fatal history depth
- Real disposable income: annual/quarterly only across all 4 countries
- CCAPM consumption-based imputed: requires national-accounts consumption (quarterly); too slow

---

## 5. Aggregation (locked at brainstorm Q4)

**Equal-weight across countries:** `Y₃_t = (1/4) × (Δ_CO + Δ_BR + Δ_KE + Δ_EU)`.

**Rationale (from brainstorm Q4 reasoning):**
1. Each country contributes equally to the regional inequality story.
2. Population-weighted (II) would make Y₃ ≈ Eurozone-weighted (51% population) — defeats the regional-pilot purpose.
3. Carbon-flow-weighted (V) creates X-Y entanglement — anti-fishing-disqualifying.
4. Standard precedent in LAC-comparative literature (Banrep Borradores, IDB working papers).

**Sensitivity** (Task 11.O resolution matrix, NOT primary): population-weighted Y₃ as alternative.

---

## 6. Sample period (locked at brainstorm Q5)

**Primary panel:**
- **Sep-2024 → 2026-04-24**, ~84 weekly observations
- Matches Carbon X_d's overlap window exactly
- Avoids Kenya CPI 2019 rebase (post-Sep-2024 series is monolithic; rebase happened pre-X_d-launch)

**Sensitivity panel** (committed in Task 11.O):
- **Aug-2023 → 2026-04-24**, ~140 weekly observations
- +1-year pre-X_d-launch baseline
- Tests whether Y₃ exhibits different statistical properties in pre-X_d vs post-X_d windows (sanity check against trivial mean-reversion)

**Out of scope for current exercise:**
- Full Rev-4-panel-matched 2008-2026 historical extension — deferred to a future Phase A.1 robustness exercise if Phase 1.5.5 lands a positive-signal verdict at Task 11.O. Would require Kenya CPI 2019 rebase bridging.

---

## 7. Frequency alignment

All Y₃ inputs land at weekly Friday-anchored America/Bogota frequency:

| Component | Native frequency | Alignment |
|---|---|---|
| Per-country equity index | Daily | Last-trading-day-of-week, log-return Friday-to-Friday |
| Per-country sovereign bond yield | Daily | Same — Friday yield-change |
| Per-country WC-CPI (food / energy / housing / transport-fuel) | Monthly | LOCF Friday-anchored America/Bogota interpolation; weekly CPI = last published monthly value as of that Friday |

**LOCF rationale:** matches Banrep IBR weekly extraction in Task 11.M.6 (commit `fff2ca7a3`); inherits Rev-4 CPI panel's weekly-from-monthly discipline; documented limitation: introduces autocorrelation in the WC-CPI weekly series that the structural-econometrics skill must account for in residual modeling at Task 11.O.

---

## 8. Components and I/O contracts

| Component | Type | Inputs | Outputs |
|---|---|---|---|
| `fetch_country_equity()` | pure free function (`y3_data_fetchers.py` NEW) | country code + date range | `pd.DataFrame[date, equity_close, equity_log_return_weekly]` |
| `fetch_country_sovereign_yield()` | pure free function (same module) | country code + date range | `pd.DataFrame[date, yield_pct, yield_change_weekly_bps]` |
| `fetch_country_wc_cpi_components()` | pure free function (same module) | country code + date range | `pd.DataFrame[date, food_cpi, energy_cpi, housing_cpi, transport_cpi]` (monthly raw) |
| `compute_wc_cpi_weighted()` | pure free function (`y3_compute.py` NEW) | per-country CPI components DataFrame + locked weights (60/25/15) | `pd.DataFrame[date, wc_cpi]` (monthly) |
| `interpolate_monthly_to_weekly_locf()` | pure free function (same module) | monthly DataFrame + Friday-anchor tz | `pd.DataFrame[friday_anchor, value_locf]` |
| `compute_per_country_differential()` | pure free function (same module) | weekly equity returns + weekly WC-CPI changes (per country) | `pd.DataFrame[friday_anchor, country_diff]` |
| `compute_y3_aggregate()` | pure free function (same module) | 4 per-country differential series | frozen-dataclass `Y3Panel{weeks, y3_value, per_country_diff_dict, n_observations}` |
| `onchain_y3_weekly` | DuckDB table (NEW) | output of `compute_y3_aggregate()` ingested via `econ_pipeline.py` additive path | columns: `week_start DATE PK, y3_value DOUBLE NOT NULL, copm_diff DOUBLE, brl_diff DOUBLE, kes_diff DOUBLE, eur_diff DOUBLE, source_methodology VARCHAR DEFAULT 'y3_v1'` |
| `load_onchain_y3_weekly()` | pure loader (NEW in `econ_query_api.py`) | none | frozen-dataclass `OnchainY3Weekly` |

All functions: pure, frozen-dataclass outputs, full typing per `functional-python` skill.

---

## 9. Pre-committed parameters (the only fixed numbers)

| Parameter | Value | Anchor |
|---|---|---|
| WC-CPI food weight | 60% | World Bank LAC bottom-quintile budget share per `2026-04-24-y3-consumption-proxy-research.md` |
| WC-CPI energy+housing-utilities weight | 25% | Same source |
| WC-CPI transport-fuel weight | 15% | Same source |
| Country aggregation weight | 1/4 each (equal) | Brainstorm Q4 ruling, anti-fishing-clean per LAC-comparative-literature precedent |
| Primary panel start | 2024-09-01 (first full week of post-X_d-launch period) | Carbon X_d ingestion start window |
| Primary panel end | 2026-04-24 (current date) | Latest-available-data |
| Sensitivity panel start | 2023-08-01 (one year pre-X_d-launch) | Brainstorm Q5 sensitivity ruling |
| LOCF anchor timezone | America/Bogota | Inheritance from Task 11.M.6 + Task 11.B convention |

Anti-fishing guarantee: these parameters are committed in this design doc + in `y3_compute.py` source as module-level Final constants BEFORE any data is ingested. Modification requires a new design-doc revision + 3-way review cycle. Same discipline as Carbon X_d design §3.

---

## 10. Decision branches (how Y₃ behaves under data pathologies)

| State | Y₃ output | Spec narrative |
|---|---|---|
| All 4 countries land clean WC-CPI components + equity data | Y₃ standard, per design above | Rev-2 spec runs Task 11.O regression Y₃ ~ X_d |
| Kenya WC-CPI ETL fails (PDF parse fragility per research warning) | Y₃ computed from 3 countries (CO/BR/EU); Kenya marked missing | Documented limitation: "Kenya inclusion deferred to tier-2 cleanup; regional aggregate computed across remaining 3 anchor countries" |
| Eurozone HICP component split unavailable for transport-fuel | substitute with `(transport CPI − food/energy double-count adjustment)`; document the substitution | Acceptable per Eurostat HICP documentation |
| Equity holiday calendar misalignment | Friday log-return rolled to last trading day of the week per country (e.g., Brazil Carnival weeks roll to Wednesday) | Matches IBOVESPA daily convention |
| Y₃ has fewer than N_min weekly non-zero observations | HALT — escalate per Carbon X_d design §4 row-4 pattern | Same kill-criterion logic |

---

## 11. Testing strategy (TDD invariants)

Per `feedback_strict_tdd.md`:

1. **Failing-first** for each component (`fetch_country_equity`, `fetch_country_wc_cpi_components`, `compute_wc_cpi_weighted`, `compute_per_country_differential`, `compute_y3_aggregate`).
2. **Independent reproduction witness** for the Y₃ aggregation — second SQL or pandas path must match the module output to the cent.
3. **Fixed-fixture golden test** per country for one specific Friday slice — values pinned in test (e.g., 2025-W45 Δ_CO_t = X.XXX, with Banrep CPI components + COLCAP closes hard-coded).
4. **Decision-hash preservation** — Rev-4 `decision_hash = 6a5f9d1b…` byte-exact through all schema migrations.
5. **Idempotent migration** for the new `onchain_y3_weekly` table.
6. **Real-data over mocks** — all tests hit real DuckDB ingested data; mocks reserved for HTTP failure modes that can't be reproduced (`feedback_real_data_over_mocks.md`).

---

## 12. Out-of-scope (deferred)

- **Full historical Y₃** (2008-2026): tier-2 if Phase 1.5.5 produces signal at Task 11.O.
- **Population-weighted aggregation**: Task 11.O sensitivity row only, never primary.
- **Other Mento countries** (WAEMU/Senegal, USD-zone): excluded by design; could re-enter if Mento adds new stablecoins or data quality improves.
- **Wage-based consumption proxy**: eliminated per research due to Kenya history depth.
- **CCAPM consumption-based imputed return**: eliminated per research due to data frequency.
- **Bond-yield primary** (instead of equity-primary): equity is locked as primary per Q2; bond is diagnostic only.
- **Crypto-portfolio rich-side**: explicitly excluded per Q2 ruling on circularity with X_d driver.

---

## 13. Inputs to plan-fold (Technical Writer's brief — Rev-5.3)

This design produces the content for the Rev-5.3 plan revision's deferred amendment-rider A1 (Y-target shift). Per PM-CF-1 finding from the prior 3-way review, A1 is no longer optional — it's required and comes forward into Rev-5.3 as **Task 11.N.2d: Y₃ inequality-differential dataset construction**.

Plan-fold instructions:
- Insert Task 11.N.2d after Task 11.N.2c (calibration exercise) and before Task 11.O (structural-econometrics spec).
- Task 11.N.2d's body specifies: ingest equity + bond + WC-CPI-components data for the 4 anchor countries; compute per-country differentials + Y₃ aggregate; persist to `onchain_y3_weekly` DuckDB table.
- Update Task 11.O Step 1: primary Y target = `Y₃_t` (per this design); diagnostic Y's = per-country differentials + bond-anchored Y₃_bond + supply-channel surrogate (Rev-5.1) + distribution-channel (11.N.1b) for cross-validation.
- Retire amendment-rider A1 (now applied as Task 11.N.2d).
- Update task count: 61 → 62.

---

## 14. References

- **Sister design doc** (X_d structural design): `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md`
- **Consumption-proxy research**: `contracts/.scratch/2026-04-24-y3-consumption-proxy-research.md`
- **Bot-attribution research** (X_d trigger): `contracts/.scratch/2026-04-24-copm-bot-attribution-research.md`
- **Lit landscape** (Y₃ + X_d both): `contracts/.scratch/2026-04-24-inequality-differential-literature-review.md`
- **Memory**: `project_abrigo_inequality_hedge_thesis.md` (updated 2026-04-24); `feedback_onchain_native_priority.md`
- **Plan**: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `1d059e3fa` (Rev-5.2.1)
- **Plan draft**: `contracts/.scratch/2026-04-24-plan-rev5.3-draft.md` (TW fix-pass + brainstorm-fold; pending consolidated Rev-5.3.1 fixes + Y₃ fold)
- **Code precedents**: Task 11.M.5 commit `af98bb659` (DuckDB type discipline + LOCF); Task 11.M.6 commit `fff2ca7a3` (panel extension via `econ_pipeline.py`); Task 11.N.1 Step 0 commit `a724252c6` (composite-PK + relaxed-CHECK schema migration)
