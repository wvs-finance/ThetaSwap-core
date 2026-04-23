# BanRep Remittance Fixture — Source Provenance Log

**Compiled:** 2026-04-23 (Task 11 of the Phase-A.0 remittance-surprise
implementation plan).
**Fixture file:** `contracts/data/banrep_remittance_aggregate_monthly.csv`.
**Loader:** `contracts/scripts/banrep_remittance_fetcher.py`.

## Rev-2 Real-World Constraint (Authoritative Finding)

The original Task-11 plan line 214 asserted a pinned public Socrata endpoint
for aggregate monthly remittance — this was factually wrong
(`datos.gov.co/resource/mcec-87by.json` is the TRM exchange-rate feed, not
remittance). The Rev-2 fallback specified quarterly MPR PDF / Excel annex
compilation.

**Further finding during Task-11 acquisition:** the BanRep Monetary Policy
Report (IPM / Informe de Política Monetaria) Excel annexes — even in the
most recent 2025-Q4/2026-Q1 editions — publish **macroeconomic forecast
variables** (quarterly GDP, current-account aggregates, inflation
projections) but do **not** contain a disaggregated monthly or quarterly
remittance time series. The MPR's narrative chapters cite remittance
qualitatively ("niveles altos," "dinámico") with a footnote to BanRep's
statistics portal.

The **only** BanRep-published remittance time series accessible as
structured data is the official **quarterly** series on BanRep's statistical
portal (suameca.banrep.gov.co). BanRep's own methodological documentation
(`ficha-metodologica-remesas.pdf`, 2019) says the Bank captures monthly
inflow data internally but publishes it as a **quarterly** aggregate in
the Balance-of-Payments release.

**Consequence for Task 11:** `reference_period` rows in the committed CSV
fall on **quarter-end** dates (YYYY-03-31, YYYY-06-30, YYYY-09-30,
YYYY-12-31). The CSV filename retains `aggregate_monthly` per the original
Task-11 data-contract anchor referenced in the Rev-1 spec §4.8 and by the
`cleaning.py` V1 seam (Task 9); periodicity-aware downstream handling is the
responsibility of Task 13 (auxiliary `a1r_monthly_rebase` column) and Task
15 (panel-integration smoke test).

## Authoritative Source

* **Series name:** Ingresos de Remesas de trabajadores, trimestral
* **BanRep series id:** 4150
* **BanRep plan id:** `REMESAS_TRIMESTRAL`
* **Periodicidad:** Trimestral (quarterly)
* **Unit:** Millones de USD (USD millions)
* **Fuente:** Banco de la República (Colombia)
* **Geography:** Nacional
* **Price basis:** Precios corrientes (current prices)

* **Human-readable landing URL:**
  `https://suameca.banrep.gov.co/estadisticas-economicas/informacionSerie/4150/remesas_trabajadores`
* **Backing REST endpoint (machine-readable):**
  `https://suameca.banrep.gov.co/estadisticas-economicas-back/rest/estadisticaEconomicaRestService/consultaMenuXId?idMenu=4150`

* **Methodological note (BanRep):**
  `https://www.banrep.gov.co/sites/default/files/ficha-metodologica-remesas.pdf`

## Snapshot Vintage

* **fechaInicial:** 31 de marzo de 2000 (Q1 2000)
* **fechaFinal:** 31 de diciembre de 2025 (Q4 2025)
* **fechaUltimoCargue:** 06 de marzo de 2026 — BanRep's own most-recent
  data-load timestamp. This is the value committed to every row's
  `mpr_vintage_date` column in the CSV, representing the **current-vintage**
  read of the series as of the Task-11 acquisition date. First-print vintage
  dates for each quarter (i.e., the original release date of each quarterly
  observation) are NOT currently recoverable for the full 2000-Q1→2025-Q4
  span without a revision-history archive; per Rev-1 spec §4.8 the
  current-vintage snapshot supports the `vintage_policy="current-vintage"`
  sensitivity branch. The `vintage_policy="real-time"` primary branch
  requires a future first-print backfill from BanRep quarterly bulletins
  — flagged in Rev-1 spec §4.8 escalation as "Phase-1 empirical-recovery
  protocol."

* **Snapshot row count:** 104 quarters (= (2025 − 2000 + 1) × 4 = 104;
  matches BanRep's reported `count`).

## MPR Editions Consulted During Task-11 Acquisition

The MPR / Informe de Política Monetaria chain was checked end-to-end before
pivoting to the suameca quarterly series. No MPR edition contained a
disaggregated remittance time series; the quarterly Excel annexes publish
*forecast* variables, not historical remittance rows. The following editions
were accessed (DOI-resolved canonical URLs preserved for audit):

| Edition | Publication date | PDF DOI | Excel annex DOI |
|---|---|---|---|
| IPM January 2026 (TR1-2026) | 2026-02-03 | `https://doi.org/10.32468/INF-POL-MONT-SPA.TR1-2026` | `https://doi.org/10.32468/INF-POL-MONT-SPA.EXCEL1.TR1-2026` |
| IPM October 2025 (TR4-2025) | 2025-11-05 | `https://doi.org/10.32468/INF-POL-MONT-ENG.TR4-2025` | `https://doi.org/10.32468/INF-POL-MONT-ENG.TR4.ANEX1-2025` |
| IPM July 2025 (TR3-2025) | 2025-09-19 | `https://doi.org/10.32468/INF-POL-MONT-ENG.TR3-2025` | `https://doi.org/10.32468/INF-POL-MONT-ENG.EXCEL1.TR3-2025` |
| IPM April 2025 (TR2-2025) | 2025-06-20 | `https://doi.org/10.32468/INF-POL-MONT-ENG.TR2-2025` | `https://doi.org/10.32468/INF-POL-MONT-ENG.TR2-ANEX1-2025` |
| IPM January 2025 (TR1-2025) | 2025-03-17 | `https://doi.org/10.32468/INF-POL-MONT-ENG.TR1-2025` | `https://doi.org/10.32468/INF-POL-MONT-ENG.TR1-MAINMACRO-2025` |

Finding: MPR Excel annexes emit row "C. Ingresos secundarios (transferencias
corrientes)" at annual / quarterly cadence. This row is **total current
transfers** (remittances + other transfers, e.g., official aid inflows);
it is not a clean remittance series. The suameca series 4150 is the
Bank's official disaggregated remittance publication and is therefore the
authoritative Task-11 source.

## Future-Maintenance Protocol

When a new BanRep quarterly release drops (typically ~60 days after
quarter-end):

1. Re-fetch the backing REST endpoint (see above) to obtain a fresh
   snapshot.
2. Update every row's `mpr_vintage_date` to the new `fechaUltimoCargue`.
3. Append any new quarter-end rows with the updated `value_usd` values
   (BanRep frequently revises historical quarters on each release — this is
   why the snapshot-vintage discipline matters for the Rev-1 spec §4.8
   sensitivity branch).
4. Update this provenance log's snapshot-vintage section.
5. Run `pytest scripts/tests/remittance/test_banrep_remittance_fetcher.py`
   to verify the refreshed CSV still passes the loader contract.

There is **no public API** for "give me the first-print value of Q3-2008";
BanRep does not publish a revision archive. Recovering first-print values
for the full 2000-Q1→2025-Q4 span is a Phase-1 empirical-recovery
exercise, out of scope for Task 11.
