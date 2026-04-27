# RC Review — Task 11.N.2.CO-dane-wire (commit `f7b03caac`)

**Reviewer**: TestingRealityChecker
**Date**: 2026-04-25
**Verdict**: **PASS-with-non-blocking-advisories**
**Default-fail discipline**: Promotion justified by 5/5 live-query passes against author claims; advisories are documentation/dtype hygiene, not correctness.

---

## Live evidence (all five probes executed against `contracts/data/structural_econ.duckdb`)

### 1. Smoke-test cutoff + headline-broadcast invariant — **PASS**
```
[CO+conn DANE] shape=(27, 5), max_date=2026-03-01, min_date=2024-01-01
columns: ['date', 'food_cpi', 'energy_cpi', 'housing_cpi', 'transport_cpi']
cutoff gate (≥ 2026-02-01): True
4-component row-wise byte-exact equality: True
```
- Cutoff `2026-03-01` clears the `≥ 2026-02-01` gate (~1.8mo stale at 2026-04-25, consistent with monthly DANE release cadence).
- `food_cpi == energy_cpi == housing_cpi == transport_cpi` row-wise across all 27 rows (`nunique(axis=1)==1` everywhere). Y₃ §10 row-2 broadcast pattern preserved.

### 2. DANE value-fidelity (DE's strongest claim) — **PASS**
```
merge with dane_ipc_monthly: {'both': 27, 'left_only': 0, 'right_only': 0}
food_cpi == ipc_index 1:1: True
```
Every fetched row corresponds 1:1 to `dane_ipc_monthly.ipc_index` over `[2024-01-01, 2026-04-24]`. No interpolation, no truncation, no off-by-one.

### 3. Consume-only contract — **PASS**
```
PRE-FETCH:  n=861, max=2026-03-01, max_ingest=2026-04-16 18:00:22.057738
POST-FETCH: n=861, max=2026-03-01, max_ingest=2026-04-16 18:00:22.057738
```
Row count, max date, AND ingest timestamp byte-exact pre/post. Read-only `conn` honored — table is unmutated by the new fetcher path.

### 4. IMF-IFS preservation (CO `conn=None`) — **PASS**
```
[CO no-conn → IMF IFS]: shape=(19, 5), max_date=2025-07-01
```
Calling without `conn` routes to legacy IMF-IFS-via-DBnomics path; cutoff `2025-07-01` matches expected pre-Rev-5.3.2 stale-by-9-months baseline. The single-source-IMF sensitivity comparator for Task 11.N.2d.1-reframe is preserved.

### 5. Other-countries safety (BR `conn=conn`) — **PASS**
```
[BR+conn]: shape=(19, 5), max_date=2025-07-01, value=235.41 (IMF IFS Brazil headline range)
```
BR with `conn=` set still routes to IMF IFS (not DANE). Identical shape and cutoff to CO no-conn. Confirms the new branch is gated on `country_code == 'CO'` AND `conn is not None`, not on `conn` alone. No accidental cross-country DANE leakage.

### 6. EU-binding joint-coverage projection — **PASS**
```
SELECT COUNT(*) FROM onchain_xd_weekly
WHERE proxy_kind='carbon_basket_user_volume_usd' AND value_usd != 0
  AND value_usd IS NOT NULL AND week_start <= '2025-12-31'
→ 65
```
Matches the plan's pre-registered projection exactly. Aligns with `project_duckdb_xd_weekly_state_post_rev531` (carbon ~80 weeks, 77 non-zero; cutoff at 2025-12-31 trims to 65).

### 7. Pre-existing-failure attestation — **PASS**
`scripts/tests/remittance/test_cleaning_remittance.py` last touched at `28d76cbb0` (commit predates `f7b03caac` per `git log`). The 2 failing tests reside inside that file. Out of scope per `feedback_agent_scope`. DE memo correctly flagged this.

---

## Cross-validation against DE memo + sibling CR PASS

| Claim | DE memo | CR review | RC live-probe |
|---|---|---|---|
| Cutoff ≥ 2026-02-01 | asserted | accepted | **2026-03-01 verified** |
| 4-col byte-exact broadcast | asserted | accepted | **verified row-wise** |
| `dane_ipc_monthly` consume-only | asserted | accepted | **verified n/max/ingest pre==post** |
| IMF path preserved (no `conn`) | asserted | accepted | **verified shape/cutoff** |
| BR not impacted by `conn=` | not explicitly tested | flagged for spot-check | **verified — IMF route held** |
| Joint coverage = 65 | plan-projected | not re-verified | **verified = 65 exactly** |

No DE claim contradicted by live data. No CR finding overturned. The "fantasy approval" risk is absent here — every assertion is grounded in observable DuckDB state.

---

## Non-blocking advisories (do NOT block promotion)

1. **`fetch_country_wc_cpi_components` returns mixed `date` dtypes across paths.** DANE path emits `python date` objects; the IMF path appears to do the same, but the merge with a DuckDB `df()` result required explicit `pd.to_datetime` coercion in my probe. This is not a bug in `f7b03caac` — it surfaces only when a downstream caller mixes the fetcher output with a raw DuckDB read. Worth noting for whoever writes the §10 panel-builder consumer (Task 11.N.2d).

2. **Plan-language sanity check for "byte-exact" broadcast.** The 4-col equality is tested over `nunique==1`. Strictly speaking, this is *value-equal* across columns, not "byte-exact" at the binary representation layer (Python floats are doubles regardless). The plan's terminology is colloquial — accepted, but if a future reviewer interprets it literally, they'll need to re-confirm bit-pattern equality (which `nunique==1` does imply for IEEE-754 doubles produced by the same broadcast).

3. **No assertion in this commit that DANE max-date drift is monitored.** When DANE publishes 2026-04-01, the test cutoff `≥ 2026-02-01` will continue to pass even if the table goes stale at 2026-03-01 for months. Recommend a future hygiene task: monitor `max(_ingested_at) ≥ NOW() - 60d` separately from the data-cutoff gate.

---

## Deployment readiness

- **Status**: ready to merge for the in-scope CO-DANE wireup.
- **Blocking issues**: none.
- **Required follow-ups**: pre-existing remittance test failures (commit `28d76cbb0`) remain — out of scope for this task per `feedback_agent_scope`, but eventually need their own ticket.

**Evidence basis**: 6 live DuckDB queries + 3 live `fetch_country_wc_cpi_components` calls + 1 `git log` lineage check. Total tool uses: 5 (well under 20 budget).
