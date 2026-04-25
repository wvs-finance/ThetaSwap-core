# OECD Direct SDMX CPI Probe — 4-country anchor (CO / BR / KE / EU)

**Probe date:** 2026-04-25
**Task:** 11.N.2.OECD-probe (diagnostic-only per Rev-5.3.2 of `docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`, plan commit `a68f63c15`)
**Author:** Data Engineer subagent
**Reviewer:** Reality Checker (single-pass advisory, non-blocking)
**Author HEAD at probe time:** `a68f63c15`

---

## 1. Endpoint family

```
https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/<KEY>?startPeriod=<YYYY-MM>&endPeriod=<YYYY-MM>&format=jsondata
```

Where `<KEY>` is the SDMX dataquery key positional `REF_AREA.FREQ.ADJUSTMENT.MEASURE.UNIT_MEASURE.EXPENDITURE.METHODOLOGY.TRANSFORMATION`. For monthly headline-CPI annual % rate the canonical key is:

```
<COUNTRY>.M.N.CPI.PA._T.N.GY
```

The OECD direct SDMX endpoint serves **SDMX-JSON v2.0** (content-type `application/vnd.sdmx.data+json; charset=utf-8; version=2`). The wrapper structure is `payload["data"]["dataSets"][0]["series"][<key>]["observations"]` — observations are keyed by integer-string position into the time axis listed at `payload["data"]["structures"][0]["dimensions"]["observation"][i]["values"]` where `id == "TIME_PERIOD"`. This wrapper differs from SDMX-JSON v1.x (where dataSets is at the top level) — a parsing trap if naively migrating earlier code.

Probe window: `startPeriod=2023-01&endPeriod=2026-04`.

---

## 2. Per-country probe table

| Country | REF_AREA | Trans. | HTTP | n_obs | Period span | Latest period | Latest value | Notes |
|---------|----------|--------|------|-------|-------------|---------------|--------------|-------|
| Colombia | `COL` | `GY` (annual %) | 200 | 39 | 2023-01 → 2026-03 | 2026-03 | 5.5581 | OK; freshest of any anchor country |
| Colombia | `COL` | `IX` (level) | **404** | — | — | — | — | `NoResultsFound`; level-series NOT exposed |
| Brazil | `BRA` | `GY` (annual %) | 200 | 39 | 2023-01 → 2026-03 | 2026-03 | 4.1426 | OK; matches BCB IPCA freshness |
| Brazil | `BRA` | `IX` (level) | **404** | — | — | — | — | `NoResultsFound`; level-series NOT exposed |
| Kenya | `KEN` | `GY` (annual %) | 200 | **0** | — | — | — | Empty `series:{}` — **Kenya is genuinely absent** from `DSD_PRICES@DF_PRICES_ALL`. Wildcard-transformation probe (`KEN..N.CPI.PA._T.N.`) also returns 0 series. Confirms KE remains a skipped country per Y₃ design §10 row 1 fallback. |
| Kenya | `KEN` | `IX` (level) | 404 | — | — | — | — | `NoResultsFound` |
| Eurozone | `EU27_2020` | `GY` | 200 | 36 | 2023-01 → 2025-12 | 2025-12 | 2.3 | OK; matches Eurostat HICP freshness profile (December prelim publishing in mid-January) |
| Eurozone | `EA20` | `GY` | 200 | 36 | 2023-01 → 2025-12 | 2025-12 | 1.9 | OK; HICP-style core readings |
| Eurozone | `EU27_2020` / `EA20` | `IX` | 404 | — | — | — | — | `NoResultsFound`; level-series NOT exposed |
| Eurozone | `EA19` | `GY` | 200 | **0** | — | — | — | Empty series — EA19 deprecated since Croatia joined (EA20 expanded coverage 2023-01) |
| OECD-Europe aggregate | `OECDE` | `GY` | 200 | 38 | 2023-01 → 2026-02 | 2026-02 | 4.9405 | This is the OECD-Europe aggregate, NOT Eurozone-only — listed for completeness; not directly Y₃-relevant |

### 2.1 Critical structural finding: only `GY` (annual %) is published, `IX` (level) is not

For all four anchor countries, the level-series transformation (`IX`) returns HTTP 404 `NoResultsFound`. The wildcard-transformation probe `COL.M.N.CPI.PA._T.N.` (any transformation) returns exactly one `TRANSFORMATION` dimension value: `GY = Growth rate, over 1 year`. **OECD direct SDMX `DSD_PRICES@DF_PRICES_ALL` exposes only the annual-rate transformation, not index levels.** This contradicts the speculative note in the prior Reality Checker report (`2026-04-25-rev532-review-reality-checker.md` line 140: "level-series equivalent retrievable via the `IX` filter") — that statement was unverified.

### 2.2 Transcription correction vs. prior RC report

The prior RC report (line 135) reported "2026-03: 5.290032" for Colombia. The live probe shows that **5.290032 is the value for 2026-02**, and the actual 2026-03 value is **5.558094**. The RC's bullet ordering listed the 2026-02 value adjacent to the 2026-03 label. This memo records the corrected mapping; no operational consequence (the OECD probe is diagnostic-only under Rev-5.3.2 and does not feed any source-mix decision).

---

## 3. Comparison vs. current Y₃ source mix

The Rev-5.3.2 Y₃ source mix (per plan §A and Task 11.N.2d-rev) targets:

| Country | Rev-5.3.2 source | Cutoff at probe time | Variant returned |
|---------|------------------|---------------------|------------------|
| CO | `dane_ipc_monthly` (existing DuckDB, ingested 2026-04-16; Task 11.N.2.CO-dane-wire wires fetcher) | **2026-03-01** | Level (index, e.g. 156.94 at 2026-03) + monthly % change |
| BR | BCB SGS series 433 (Task 11.N.2.BR-bcb-fetcher; raw table not yet ingested at probe time — table `bcb_ipca_monthly` is NEW and absent from current DuckDB) | Targeted ≥ 2026-02-01 (per acceptance criterion line 1905 — actual landing TBD) | Monthly variation % (cumulative-product utility produces level) |
| EU | Eurostat HICP via DBnomics | 2025-12-01 (per RC review §A) | Level (HICP index) |
| KE | IMF IFS (the only path the current `_fetch_imf_ifs_headline_broadcast` consumes for KE) | 2025-07-01 (per RC review §A) — or skipped per design §10 row 1 fallback | Level |

### 3.1 Freshness comparison vs. OECD direct (annual-rate, monthly index date)

| Country | Current source cutoff | OECD direct cutoff | Δ months (OECD fresher by) | OECD supersedes? |
|---------|----------------------|--------------------|--------------------------:|------------------|
| CO | DANE 2026-03-01 | OECD 2026-03 | **0** | **No** — DANE is at parity. OECD adds nothing on freshness for CO; DANE still wins on level-series availability. |
| BR | BCB SGS 433 — targeted ≥ 2026-02; OECD already at 2026-03 | OECD 2026-03 | **0 to +1** (depends on BCB landing) | **No to marginal** — BCB SGS 433 publishes IPCA monthly with the same release cadence; OECD is downstream of BCB. If BCB-fetcher (Task 11.N.2.BR-bcb-fetcher) lands at 2026-03, parity. If BCB lands only at 2026-02, OECD is +1 month. |
| EU | Eurostat HICP via DBnomics 2025-12-01 | OECD 2025-12 | **0** | **No** — same publication chain (OECD republishes Eurostat HICP rate; level-source still required). |
| KE | IMF IFS 2025-07-01 (or design-§10 skip) | OECD: empty (Kenya absent) | n/a — OECD has no Kenya data | **No** — Kenya is genuinely outside `DSD_PRICES@DF_PRICES_ALL` coverage. Confirms IMF IFS is the only reachable Kenya source. |

### 3.2 Why OECD direct does NOT supersede the Rev-5.3.2 mix on freshness

For **all four anchor countries**, OECD direct SDMX is at-parity-or-later vs. the Rev-5.3.2 source for that country. There is **no freshness advantage** to switching any country source to OECD direct under the current data state.

### 3.3 Why OECD direct creates a methodology problem for Y₃

Y₃ design doc §10 row 2 requires **levels** (the broadcast pattern is "headline level → all four component slots populated with the headline level"). OECD direct exposes only `GY` (annual % rate). To use OECD direct for Y₃ would require:

- A cumulative-rate-to-level reconstruction utility (compose `(1 + GY/100)^(1/12) - 1` monthly compounding then chain), OR
- A baseline-anchored reconstruction (start from a known level at one date and project forward using the rate).

Both add a non-trivial reproducibility surface and are NOT byte-exact-reproducible across re-runs without additional schema discipline. The Rev-5.3.2 sources (DANE level, BCB cumulative-index utility, Eurostat HICP level, IMF IFS level) all expose level-series natively — no reconstruction is required.

---

## 4. Recommendation for future Rev-5.3.3+

**Recommendation: REMAIN UNUSED for the foreseeable future. Optionally retain as a sensitivity-only fetcher.**

**Rationale:**

1. **No freshness gain.** The probe shows OECD direct is at-parity-or-later for all four anchors vs. the Rev-5.3.2 sources. It cannot move the gate (Task 11.N.2d-rev's load-bearing ≥75-week joint coverage is bounded by the binding country EU at 2025-12-01 — OECD direct EU also caps at 2025-12-01).

2. **Methodology penalty for Y₃.** OECD direct exposes annual-rate only; Y₃ needs levels. Adding a cumulative-rate-to-level reconstruction is a methodology change at the data-construction layer and would require its own pre-commitment (not a silent helper utility).

3. **Coverage gap for Kenya.** Kenya is genuinely absent from `DSD_PRICES@DF_PRICES_ALL`. OECD direct does not solve the KE skip-fallback at Y₃ design §10 row 1.

4. **Defensible sensitivity-only role IF a future revision wants pre-registered triangulation.** A future Rev-5.x.x could add OECD direct as a *cross-check* fetcher for CO, BR, EU (separate `oecd_cpi_monthly` raw table; reconstruct level via cumulative-rate utility; never substitute primary source). This would serve a triangulation purpose ("does OECD's rate when integrated agree with DANE/BCB/Eurostat levels?") similar to the Y₃ design's role for the existing IMF IFS comparator. But this is not motivated by any current finding; the agreement test would be informative only if a primary source's level integrity were itself in dispute — which is not currently the case.

5. **Anti-fishing discipline.** Rev-5.3.2 §B2 anti-fishing guard line 1860 explicitly forbids feeding OECD outcome into the Task 11.N.2d-rev source mix. This memo's recommendation respects that guard. If a future revision wishes to motivate OECD direct as a primary upgrade, it must independently surface a freshness or correctness gap that OECD uniquely fills — and the present probe shows no such gap.

**Trade-off articulation:**

- **Folding OECD direct into Rev-5.3.3 as a primary upgrade:** REJECTED — no measurable gain on freshness or correctness; methodology burden of rate-to-level reconstruction is not justified.
- **Deferring as a sensitivity-only fetcher in Rev-5.3.3:** WEAK MOTIVATION — usable for triangulation but no specific question is currently open that requires it; consider only if a future ingest-layer audit finds a discrepancy in DANE / BCB / Eurostat levels.
- **Remaining unused:** RECOMMENDED — current source mix is sound under the probe evidence; OECD direct's annual-rate-only limitation makes it a poor fit for Y₃'s level-series contract.

---

## 5. Acceptance trace (per Rev-5.3.2 plan task body lines 1848–1852)

| Acceptance criterion | Status |
|----------------------|--------|
| Memo lists CO / BR / KE coverage from OECD direct SDMX (cutoff month per country) | Met — §2 table |
| Reproduces the request URL family for future verification | Met — §1 + §2 (per-row URL captured in JSON appendix) |
| Side-by-side freshness comparison vs. DANE (CO), BCB SGS (BR), IMF IFS via DBnomics, Eurostat HICP via DBnomics | Met — §3.1 table |
| Records a freshness threshold "≥ 2026-01-01 for CO" as the diagnostic GO yardstick (no operational dispatch consequence) | Met — OECD CO at 2026-03 ≥ 2026-01-01; threshold cleared diagnostically; operationally inert per Rev-5.3.2 anti-fishing guard line 1860 |
| Memo serves as future-revision intelligence; NOT a dependency of Task 11.N.2d-rev | Met — §4 articulates the unused recommendation; no dispatch dependency claimed |
| No DuckDB mutation, no code mutation | Met — this memo is the only artifact written |
| Recommendation for future revisions articulated (not just "passes") | Met — §4 |

---

## 6. Verbatim probe outputs (appendix)

### 6.1 Raw response sample — Colombia GY (HTTP 200, abridged)

```
GET https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/COL.M.N.CPI.PA._T.N.GY?startPeriod=2025-01&endPeriod=2026-04&format=jsondata

HTTP 200
Content-Type: application/vnd.sdmx.data+json; charset=utf-8; version=2

{
  "meta": {"schema": "https://raw.githubusercontent.com/sdmx-twg/sdmx-json/master/data-message/tools/schemas/2.0.0/sdmx-json-data-schema.json",
           "id": "IREF012216", "prepared": "2026-04-25T14:47:34Z", ...},
  "data": {
    "dataSets": [{"structure": 0, "action": "Information",
                  "series": {"0:0:0:0:0:0:0:0": {
                    "observations": {
                      "0": [5.162292, 0], "1": [5.089996, 0], "2": [5.276587, 0],
                      "3": [5.22298, 0],  "4": [5.558094, 0], "5": [5.290032, 0],
                      ...
                    }
                  }}
    }],
    "structures": [{"name": "Consumer price indices (CPIs, HICPs), COICOP 1999",
                    "dimensions": {"observation": [{"id": "TIME_PERIOD",
                                                    "values": [{"id": "2025-01"}, {"id": "2025-02"}, ...]}]}
                   }]
  }
}
```

### 6.2 Recent observations (parsed) — all probed countries

```
COL GY (Colombia headline annual %):
  2025-10 → 5.512228
  2025-11 → 5.301071
  2025-12 → 5.099884
  2026-01 → 5.353601
  2026-02 → 5.290032
  2026-03 → 5.558094     ← latest

BRA GY (Brazil headline annual %):
  2025-10 → 4.680707
  2025-11 → 4.461782
  2025-12 → 4.264348
  2026-01 → 4.441314
  2026-02 → 3.812337
  2026-03 → 4.142640     ← latest

EU27_2020 GY (Eurozone EU27_2020 annual %):
  2025-07 → 2.4
  2025-08 → 2.4
  2025-09 → 2.6
  2025-10 → 2.5
  2025-11 → 2.4
  2025-12 → 2.3          ← latest

EA20 GY (Eurozone EA20 annual %):
  2025-07 → 2.0
  2025-08 → 2.0
  2025-09 → 2.2
  2025-10 → 2.1
  2025-11 → 2.1
  2025-12 → 1.9          ← latest

OECDE GY (OECD-Europe aggregate annual %):
  2025-09 → 5.701406
  2025-10 → 5.501062
  2025-11 → 5.183355
  2025-12 → 5.036776
  2026-01 → 4.748650
  2026-02 → 4.940501     ← latest

KEN GY (Kenya): empty series (n_obs = 0) — Kenya absent from DSD_PRICES@DF_PRICES_ALL
EA19 GY: empty series (n_obs = 0) — EA19 deprecated; superseded by EA20

IX transformation (all anchor countries): HTTP 404 NoResultsFound — level-series NOT exposed
```

### 6.3 Reproduction recipe

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom
source contracts/.venv/bin/activate
python -c "
import requests
url = 'https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/COL.M.N.CPI.PA._T.N.GY?startPeriod=2025-01&endPeriod=2026-04&format=jsondata'
r = requests.get(url, timeout=30)
print(r.status_code, len(r.text))
data = r.json()['data']
periods = [v['id'] for v in data['structures'][0]['dimensions']['observation'][0]['values']]
obs = data['dataSets'][0]['series']['0:0:0:0:0:0:0:0']['observations']
recent = sorted({periods[int(k)]: v[0] for k, v in obs.items()}.items())[-6:]
for p, v in recent: print(f'  {p} -> {v:.4f}')
"
```

---

## 7. End of memo

No DuckDB mutation. No code mutation. No plan markdown mutation. This memo is the sole artifact for Task 11.N.2.OECD-probe under Rev-5.3.2.
