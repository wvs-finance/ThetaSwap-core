# SUAMECA Portal Investigation: Three Data Sources for Structural Econometrics Model

**Date**: 2026-04-16
**Investigator**: Papa Bear (deep analysis agent)
**Portal**: https://suameca.banrep.gov.co/

---

## Executive Summary

Two of three target variables are verified accessible via programmatic API. The third (FX intervention) exists on BanRep's portal but is NOT available through the SDMX API and requires either browser-rendered dashboard scraping or an alternative source.

| Variable | Exists on SUAMECA? | Programmatic Access? | Status |
|---|---|---|---|
| IBR overnight (daily) | YES | YES -- SDMX REST API, verified live | VERIFIED |
| FX intervention I_t | Partially -- on banrep.gov.co, not on SDMX | NO direct API | NEEDS ALTERNATIVE |
| Machine-readability | YES for SDMX series | N/A | VERIFIED |

---

## 1. IBR Overnight Rate (Daily) -- VERIFIED

### Data Exists: YES

The IBR (Indicador Bancario de Referencia) overnight rate is published daily at 11:45 a.m. Colombia time. It is available as both nominal rate (NR) and effective rate (ER).

### Series Details

- **SUAMECA page**: https://suameca.banrep.gov.co/estadisticas-economicas/informacionSerie/241/tasas_interes_indicador_bancario_referencia_ibr
- **SDMX FLOW_ID (latest)**: `DF_IBR_DAILY_LATEST`
- **SDMX FLOW_ID (historical)**: `DF_IBR_DAILY_HIST`
- **SUBJECT codes**: `IRIBRM00` (overnight), `IRIBRM01` (1 month), `IRIBRM03` (3 months), `IRIBRM06` (6 months)
- **UNIT_MEASURE**: `NR` (nominal rate) or `ER` (effective rate)
- **FREQ**: `D` (daily)
- **Date range**: January 2, 2008 to present (confirmed via live test)

### Programmatic Access: YES -- Two Methods

**Method A: SDMX REST API (recommended)**

Base endpoint: `https://totoro.banrep.gov.co/nsi-jax-ws/rest/data`

Full URL pattern:
```
https://totoro.banrep.gov.co/nsi-jax-ws/rest/data/ESTAT,DF_IBR_DAILY_HIST,1.0/all/ALL/?startPeriod=2008&endPeriod=2027&dimensionAtObservation=TIME_PERIOD&detail=full
```

- Returns: SDMX-ML Generic Data v2.1 (XML)
- Authentication: NONE required (public, no registration)
- Live-tested 2026-04-16: HTTP 200, returned IBR overnight ER=11.249%, NR=10.516% for today
- Date format in response: YYYYMMDD
- No rate limits documented

IMPORTANT: `endPeriod` operates as a "less than" on the year. To get data through 2026, set `endPeriod=2027`.

**Method B: SOAP endpoint**

Endpoint: `https://totoro.banrep.gov.co/OCDEv1.0/Services/NSIStdV21WsService`

Python example provided in official documentation (see PDF reference below). Requires constructing XML body with FlowRef and query parameters.

**Method C: datos.gov.co Socrata API (fallback)**

Dataset ID: `b8fs-cx24`
URL: `https://www.datos.gov.co/resource/b8fs-cx24.json`

- Standard Socrata SODA API, supports JSON/CSV
- Available from August 1, 2012 onwards (shorter range than SDMX)
- Fields: fecha, tipo_tasa (Efectiva/Nominal), agente, plazo, excepcion, tasa

### For Our Model

We need IBR overnight to construct policy-rate surprises (delta_IBR around BanRep announcement dates). Use Method A with `SUBJECT=IRIBRM00` and `UNIT_MEASURE=ER` (effective rate) for the overnight tenor.

---

## 2. FX Intervention Data (I_t) -- NEEDS ALTERNATIVE SOURCE

### Data Exists on banrep.gov.co: YES, but NOT via SDMX API

The SDMX web service documentation (v3.0, August 2025) lists exactly 11 thematic series:

1. IBR (daily, various tenors)
2. CDT 90-day DTF (daily)
3. TRM -- Representative Market Exchange Rate (daily)
4. Monetary Policy Rate TPM (daily + monthly)
5. Interbank Rate TIB (daily)
6. COLCAP stock index (monthly)
7. Monetary aggregates M1/M2/M3 (monthly)
8. DTF quarterly forecast (daily)
9. CDT 90-day DTF monthly
10. UVR -- Real Value Unit (daily)

**FX intervention data is NOT among the 11 SDMX-accessible series.**

### Where FX Intervention Data Lives

BanRep publishes FX intervention statistics at:
- **Main page**: https://www.banrep.gov.co/es/estadisticas/intervencion-mercado-cambiario
- **Sub-pages**: 
  - https://www.banrep.gov.co/es/estadisticas/subastas-call-para-control-volatilidad (call options for volatility control)
  - https://www.banrep.gov.co/es/estadisticas/subastas-put-para-control-volatilidad (put options for volatility control)
  - https://www.banrep.gov.co/es/estadisticas/subasta-opciones (option auctions)

These pages describe:
- Put options: right to sell USD to BanRep (reserve accumulation). Exercise condition: TRM < 20-day moving average.
- Call options: right to buy USD from BanRep (reserve decumulation / volatility control).
- Direct interventions: discretionary USD purchases/sales.
- Forward NDF positions.

### Machine Readability: POOR

- The banrep.gov.co pages are protected by ShieldSquare bot detection (curl returns a block page, confirmed in live test)
- The SUAMECA "Reportes OAC" pages (e.g., balanza cambiaria) render via Oracle Analytics Cloud JavaScript embedding -- not scrapable without a headless browser
- Historical data is reportedly available in attached Excel files on the BanRep intervention pages, but these are behind the bot-protection wall

### Alternative Sources for I_t

1. **BanRep Boletines**: https://suameca.banrep.gov.co/estadisticas-economicas/boletines -- includes "Informe de operaciones de compra venta de divisas por parte del Banco" with annual and monthly periodicity since 2000. These are PDF/Excel reports, not API-accessible.

2. **Balanza cambiaria (exchange balance)**: Available at SUAMECA under path `4_Sector_Externo_tasas_de_cambio_y_derivados/2_Sector_Externo/9_Balanza_cambiaria/1_Serie_historica_mensual_balanza_cambiaria`. Monthly frequency only (not daily).

3. **Manual download + cache**: Download the Excel files from the intervention pages using a real browser session, then cache them locally. This is a one-time operation since BanRep updates intervention data monthly/quarterly.

4. **IMF IFS or BIS**: May have monthly Colombian FX intervention data in machine-readable format.

### Impact on Model

For the daily intervention dummy I_t, SUAMECA/SDMX cannot provide this variable. Options:
- Construct I_t from BanRep press releases / announcement dates (web scraping with bot-bypass)
- Use the monthly balanza cambiaria net purchases as a monthly proxy
- Manually download the Excel files once and maintain them in the data pipeline

---

## 3. Machine-Readability and Programmatic Access -- VERIFIED

### SDMX API (Primary Channel)

**REST endpoint**: `https://totoro.banrep.gov.co/nsi-jax-ws/rest/data`

- Standard: SDMX-ML Generic Data v2.1
- Protocol: HTTP GET
- Format: XML only (no JSON option from BanRep's endpoint)
- Authentication: NONE -- publicly accessible, no registration required
- URL structure: `{endpoint}/flowref[AGENCY_ID,FLOW_ID,VERSION]/key/provider/?parameters`
- Date filtering: `startPeriod` and `endPeriod` query parameters (YYYY, YYYY-MM, or YYYY-MM-DD)
- Official documentation: https://suameca.banrep.gov.co/archivos/webservices/documento_tecnico_ws_consumo_sdmx.pdf (38 pages, v3.0, August 2025)
- TRM-specific guide: https://suameca.banrep.gov.co/archivos/webservices/documento_tecnico_ws_consumo_sdmx_trm.pdf (3 pages, v2.0, October 2024)

**SOAP endpoint**: `https://totoro.banrep.gov.co/OCDEv1.0/Services/NSIStdV21WsService`

- WSDL: append `?wsdl` to endpoint
- Content-Type: `text/xml; charset=utf-8`
- Python example in official docs using `requests.post()`

### SUAMECA Web Portal (Secondary Channel)

- URL: https://suameca.banrep.gov.co/
- Framework: Angular SPA with Oracle Analytics Cloud dashboards
- NOT directly scrapable -- requires JavaScript rendering
- Multiple data download: https://suameca.banrep.gov.co/descarga-multiple-de-datos/ -- browser-only, JS-rendered
- Series search: https://suameca.banrep.gov.co/buscador-de-series/ -- browser-only

### datos.gov.co Socrata API (Tertiary Channel)

- IBR Overnight dataset: `https://www.datos.gov.co/resource/b8fs-cx24.json`
- Standard Socrata SODA API with JSON/CSV output
- Shorter date range (from 2012) than SDMX (from 2008)

### Error Codes (SDMX)

| Code | Meaning |
|---|---|
| 400 | Syntax/semantic error in parameters |
| 404 | No results matching query |
| 500 | Internal server error |
| 503 | Service temporarily unavailable |

---

## Complete SDMX Flow ID Reference

All available series via the SDMX API (exhaustive list from official v3.0 documentation):

| Series | Frequency | FLOW_ID Latest | FLOW_ID Historical |
|---|---|---|---|
| IBR | Daily (all tenors) | DF_IBR_DAILY_LATEST | DF_IBR_DAILY_HIST |
| CDT 90d DTF | Daily | DF_DTF_DAILY_LATEST | DF_DTF_DAILY_HIST |
| TRM (COP/USD) | Daily | DF_TRM_DAILY_LATEST | DF_TRM_DAILY_HIST |
| Policy Rate TPM | Daily | DF_CBR_DAILY_LATEST | DF_CBR_DAILY_HIST |
| Policy Rate TPM | Monthly avg | DF_CBR_MONTHLY_LATEST | DF_CBR_MONTHLY_HIST |
| Interbank Rate TIB | Daily | DF_IR_DAILY_LATEST | DF_IR_DAILY_HIST |
| COLCAP index | Monthly | DF_COLCAP_MONTHLY_LATEST | DF_COLCAP_MONTHLY_HIST |
| Monetary agg M1/M2/M3 | Monthly | DF_MONAGG_MONTHLY_LATEST | DF_MONAGG_MONTHLY_HIST |
| DTF Quarterly forecast | Daily | DF_DTF_TRIM_ANTICIPADO_LATEST | DF_DTF_TRIM_ANTICIPADO_HIST |
| CDT 90d DTF Monthly | Monthly | DF_DTF_MONTHLY_LATEST | DF_DTF_MONTHLY_HIST |
| UVR | Daily | DF_UVR_DAILY_LATEST | DF_UVR_DAILY_HIST |

---

## Recommendations for Data Pipeline

### IBR Overnight (VERIFIED -- ready for pipeline)

```python
# Minimal Python to fetch IBR overnight historical via REST
import requests
from xml.etree import ElementTree

url = (
    "https://totoro.banrep.gov.co/nsi-jax-ws/rest/data/"
    "ESTAT,DF_IBR_DAILY_HIST,1.0/all/ALL/"
    "?startPeriod=2008&endPeriod=2027"
    "&dimensionAtObservation=TIME_PERIOD&detail=full"
)
resp = requests.get(url)
# Parse XML, filter for SUBJECT=IRIBRM00, UNIT_MEASURE=ER
```

### FX Intervention (NOT on SDMX -- needs workaround)

Three options, in order of preference:
1. **Check if BanRep Excel files have stable URLs** -- download once, cache, update quarterly
2. **Use Selenium/Playwright** to bypass ShieldSquare and scrape the intervention page Excel attachments
3. **Manually download** the Excel files from BanRep and commit to `research/data/`

### Bonus: TRM also available via SDMX

The COP/USD TRM is available daily via `DF_TRM_DAILY_HIST` -- this could supplement or replace any other TRM source in the pipeline.

---

## Key References

- SDMX Technical Guide (v3.0): https://suameca.banrep.gov.co/archivos/webservices/documento_tecnico_ws_consumo_sdmx.pdf
- SDMX TRM Guide (v2.0): https://suameca.banrep.gov.co/archivos/webservices/documento_tecnico_ws_consumo_sdmx_trm.pdf
- SUAMECA Web Service page: https://suameca.banrep.gov.co/estadisticas-economicas/webService
- SUAMECA Catalog: https://suameca.banrep.gov.co/estadisticas-economicas/catalogo
- BanRep FX Intervention: https://www.banrep.gov.co/es/estadisticas/intervencion-mercado-cambiario
- datos.gov.co IBR Overnight: https://www.datos.gov.co/widgets/b8fs-cx24
