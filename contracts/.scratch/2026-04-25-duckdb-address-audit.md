# DuckDB Table-to-Address Audit (MR-β.1 Sub-task 2)

**Date:** 2026-04-26.
**Authoring revision:** Rev-5.3.5 β-rescoped framing.
**Sub-plan anchor:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` — §C sub-task 2 + §I CORRECTIONS sub-task 2 rescope.
**Major-plan anchor:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` — Rev-5.3.5 CORRECTIONS block (file end).
**Sub-task 1 cross-reference:** `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` — §β-rescope.1 (in-scope inventory) + §β-rescope.2 (out-of-scope COPM-Minteo).
**DuckDB source-of-truth:** `contracts/data/structural_econ.duckdb` (read-only connection at audit time; no row mutations performed; consume-only invariant preserved per sub-plan §B-1 and §B-2).

---

## §1 — Pre-flight enumeration query result (live DuckDB authoritative inventory)

**Query executed (the ONE permitted SQL fragment per sub-plan §C sub-task 2):**

```
SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'onchain_%' ORDER BY table_name
```

**Result — 14 `onchain_*` tables returned (count is authoritative for coverage-completeness verification in §10):**

1. `onchain_carbon_arbitrages`
2. `onchain_carbon_tokenstraded`
3. `onchain_copm_address_activity_top400`
4. `onchain_copm_burns`
5. `onchain_copm_ccop_daily_flow`
6. `onchain_copm_daily_transfers`
7. `onchain_copm_freeze_thaw`
8. `onchain_copm_mints`
9. `onchain_copm_time_patterns`
10. `onchain_copm_transfers`
11. `onchain_copm_transfers_sample`
12. `onchain_copm_transfers_top100_edges`
13. `onchain_xd_weekly`
14. `onchain_y3_weekly`

The 14-table count matches the Reality Checker's pre-flight live-DuckDB probe at sub-plan-review time (sub-plan §H R-1 disposition); no table is silently omitted; coverage divergence is HALT-VERIFY per `feedback_pathological_halt_anti_fishing_checkpoint`.

---

## §2 — Coverage classification scheme (REQUIRED)

Per sub-plan §C sub-task 2 + §I sub-task 2 rescope, every `onchain_*` table is tagged with exactly ONE of four labels:

- **DIRECT** — consumes raw on-chain Transfer / event data scoped by `contract_address` (or fixed-address filter); records address(es) + linkage to sub-task 1's §β-rescope inventory.
- **DERIVATIVE** — computed from another `onchain_*` table (the parent); records the parent table + inheritance chain.
- **DEFERRED** — already deferred under prior Rev-5.3.x scope; records the prior scope decision.
- **DEFERRED-via-scope-mismatch** — Rev-5.3.5 β-resolution scope-mismatch; sourced from `0xc92e8fc2…` (Minteo-fintech, OUT of Mento-native scope under β); records the Rev-5.3.5 disposition memo + major-plan CORRECTIONS block.

**No table is dropped, renamed, or migrated under this audit.** All re-tagging is annotation-only (sub-plan §B-2 + §I sub-task 2 rescope).

---

## §3 — Coverage classification table (one row per table)

| # | Table | Tag | Address(es) or parent | Scope status under β |
|---|---|---|---|---|
| 1 | `onchain_carbon_arbitrages` | DIRECT | CarbonController `0x66198711…` (BancorArbitrage `0x8c05ea30…` per `project_carbon_defi_attribution_celo`); 0 rows ingested at audit time | In-scope (Carbon DeFi MM platform, basket-counter-side); β-spec follow-up flagged in §7 |
| 2 | `onchain_carbon_tokenstraded` | DIRECT | CarbonController `0x66198711…`; trader-partition rule `trader = 0x8c05ea30…` per `project_carbon_user_arb_partition_rule`; 0 rows ingested at audit time | In-scope (Carbon DeFi MM platform, basket-counter-side); β-spec follow-up flagged in §7 |
| 3 | `onchain_copm_address_activity_top400` | DERIVATIVE | Parent: `onchain_copm_transfers` (top-400 reduction) | DEFERRED-via-scope-mismatch (inherits from `onchain_copm_transfers`) |
| 4 | `onchain_copm_burns` | DIRECT | COPM-Minteo `0xc92e8fc2…`; 121 rows | DEFERRED-via-scope-mismatch |
| 5 | `onchain_copm_ccop_daily_flow` | DIRECT | **Paired-source table** — see §6 explicit RC R-2 narrative; tracks BOTH COPM-Minteo `0xc92e8fc2…` (mint/burn columns) AND a separately-named `ccop_*` USDT-pairing source on Celo (USDT inflow/outflow columns) | DEFERRED-via-scope-mismatch (Minteo-COPM scope-mismatch dominates; the `_ccop_` legacy-slug fragment compounds the ambiguity — see §6) |
| 6 | `onchain_copm_daily_transfers` | DERIVATIVE | Parent: `onchain_copm_transfers` (daily aggregation: counts + distinct senders/receivers + total wei volume) | DEFERRED-via-scope-mismatch (inherits) |
| 7 | `onchain_copm_freeze_thaw` | DIRECT | COPM-Minteo `0xc92e8fc2…` (freeze/thaw events on the Minteo proxy); 4 rows | DEFERRED-via-scope-mismatch |
| 8 | `onchain_copm_mints` | DIRECT | COPM-Minteo `0xc92e8fc2…`; 146 rows | DEFERRED-via-scope-mismatch |
| 9 | `onchain_copm_time_patterns` | DERIVATIVE | Parent: `onchain_copm_transfers` (diurnal-pattern aggregation by `kind` × `bucket`); 86 rows | DEFERRED-via-scope-mismatch (inherits) |
| 10 | `onchain_copm_transfers` | DIRECT | COPM-Minteo `0xc92e8fc2…`; 110,253 rows; covers 2024-09-17 → 2026-04-25 | DEFERRED-via-scope-mismatch |
| 11 | `onchain_copm_transfers_sample` | DERIVATIVE | Parent: `onchain_copm_transfers` (10-row sample reduction) | DEFERRED-via-scope-mismatch (inherits) |
| 12 | `onchain_copm_transfers_top100_edges` | DERIVATIVE | Parent: `onchain_copm_transfers` (top-100 from→to edge aggregation) | DEFERRED-via-scope-mismatch (inherits) |
| 13 | `onchain_xd_weekly` | DIRECT (mixed) | Aggregation table over 10 `proxy_kind` values; 819 rows total; per-proxy address-source provenance enumerated in §5 | Mixed: 9 of 10 `proxy_kind` values in-scope under β; 1 of 10 (`carbon_per_currency_copm_volume_usd`) DEFERRED-via-scope-mismatch |
| 14 | `onchain_y3_weekly` | DIRECT | Y₃ inequality-differential panel (4-country: CO/BR/KE/EU); not address-scoped — methodology-scoped via `source_methodology` enumeration (`y3_v1_3country_ke_unavailable`, `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`, `y3_v2_imf_only_sensitivity_3country_ke_unavailable`); 291 rows | In-scope (Y panel; orthogonal to the X_d address-rescope under β) |

**Tag totals (verifiable in §10 coverage-completeness):**
- DIRECT (in-scope): 3 (`onchain_carbon_arbitrages`, `onchain_carbon_tokenstraded`, `onchain_y3_weekly`)
- DIRECT (mixed): 1 (`onchain_xd_weekly` — 9 of 10 `proxy_kind` values in-scope; 1 DEFERRED-via-scope-mismatch)
- DEFERRED-via-scope-mismatch: 10 (all `onchain_copm_*` tables, both DIRECT and DERIVATIVE)
- DERIVATIVE total (subset of above): 5 (`onchain_copm_address_activity_top400`, `onchain_copm_daily_transfers`, `onchain_copm_time_patterns`, `onchain_copm_transfers_sample`, `onchain_copm_transfers_top100_edges`)
- DEFERRED (prior Rev-5.3.x scope, not β-rescope): 0

Sum of unique-table tags = 14 = pre-flight enumeration count. Coverage HALT-clear.

---

## §4 — Per-table audit detail (DIRECT, DERIVATIVE, DEFERRED-via-scope-mismatch sections)

### §4.1 — DIRECT tables tracking Mento-native or basket-counter-side (in-scope under β)

#### `onchain_carbon_arbitrages` — DIRECT (Carbon DeFi MM platform, in-scope)

- **On-chain source.** CarbonController `0x66198711…` per `project_carbon_defi_attribution_celo`. The table also surfaces BancorArbitrage `0x8c05ea30…` rows via the `evt_tx_from`/`caller` fields when ingested.
- **Schema indicators of DIRECT tag.** `contract_address` BLOB column + raw event fields (`evt_tx_hash`, `evt_block_number`, `evt_block_time`, `evt_tx_from`, `caller`, `platformIds`, `protocolAmounts`, `rewardAmounts`, `sourceAmounts`, `sourceTokens`, `tokenPath`).
- **Row count.** 0 (audit time). The schema is provisioned; no events have been ingested yet under any Rev-5.3.x dispatch.
- **Linkage to sub-task 1 §β-rescope.** Carbon DeFi addresses are NOT enumerated in the in-scope Mento-native registry (sub-task 1 §β-rescope.1) — they are basket-counter-side platform addresses, not Mento-native stablecoins. The cross-reference is via `project_carbon_defi_attribution_celo` (load-bearing memory).
- **β-spec follow-up.** See §7 — the question whether Carbon DeFi MM routes Mento-basket trading via Minteo-COPM (`0xc92e8fc2…`) or Mento-native COPm (`0x8A567e2a…`) is OUT of scope for this sub-task and IN scope for Task 11.P.spec-β identification design.

#### `onchain_carbon_tokenstraded` — DIRECT (Carbon DeFi MM trades, in-scope)

- **On-chain source.** CarbonController `0x66198711…` per `project_carbon_defi_attribution_celo`. The trader-partition rule per `project_carbon_user_arb_partition_rule` requires partitioning rows on the row-level `trader` field: `trader = 0x8c05ea30…` → BancorArbitrage (arb-side); else → user-side. The partition is 17%/83% USD split with perfectly diagonal contingency (per the same memory file).
- **Schema indicators of DIRECT tag.** `contract_address` BLOB + `trader` BLOB + raw event fields (`sourceToken`, `targetToken`, `sourceAmount`, `targetAmount`, `tradingFeeAmount`, `byTargetAmount`, `source_amount_usd`).
- **Row count.** 0 (audit time). Schema provisioned; ingestion not yet executed.
- **Linkage to sub-task 1 §β-rescope.** Same as `onchain_carbon_arbitrages` — basket-counter-side platform; not in the Mento-native per-token registry.
- **β-spec follow-up.** See §7 (CarbonController routes Mento-basket trading via which COPM/COPm address).

#### `onchain_y3_weekly` — DIRECT (Y₃ inequality-differential panel, in-scope, methodology-scoped)

- **On-chain source.** This table is NOT address-scoped on Celo. It is methodology-scoped via `source_methodology`: three values enumerated at audit time (`y3_v1_3country_ke_unavailable` 59 rows; `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` 116 rows; `y3_v2_imf_only_sensitivity_3country_ke_unavailable` 116 rows). Y₃ aggregates 4-country weekly panel data (CO/BR/KE/EU; KE-unavailable in v1) per `project_y3_inequality_differential_design`.
- **Schema indicators.** `week_start` DATE + `y3_value` DOUBLE + per-country `*_diff` DOUBLE columns (`copm_diff`, `brl_diff`, `kes_diff`, `eur_diff`) + `source_methodology` VARCHAR.
- **Row count.** 291.
- **β-rescope impact.** None on the panel structure. The `copm_diff` column name follows the pre-rebrand legacy convention; the column tracks the Colombian-peso (COP) inequality-differential component computed from CO macro data (DANE / IMF), NOT from on-chain `0xc92e8fc2…` events. Slug-vs-on-chain-source asymmetry note: `copm_diff` is a column name in a methodology-scoped panel; it does not address-filter Minteo-fintech events. No rename requested under this sub-plan per §B-2.

### §4.2 — DIRECT-mixed table (`onchain_xd_weekly`)

`onchain_xd_weekly` aggregates 10 `proxy_kind` values; per-`proxy_kind` provenance + scope is enumerated in §5 (separate section). The table-level tag is DIRECT; the per-`proxy_kind` tags partition into 9 in-scope + 1 DEFERRED-via-scope-mismatch.

### §4.3 — DEFERRED-via-scope-mismatch tables (sourced from `0xc92e8fc2…` Minteo-fintech)

Per Rev-5.3.5 β-resolution + sub-plan §I sub-task 2 rescope, the following 10 tables are tagged DEFERRED-via-scope-mismatch. The Mento-native COPm address `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (sub-task 1 §β-rescope.1 entry 1) is the canonical Mento-native Colombian-peso address; the legacy `onchain_copm_*` tables track the OUT-of-scope Minteo-fintech `0xc92e8fc2…` address (sub-task 1 §β-rescope.2 entry).

**Disposition source documents.** Major-plan Rev-5.3.5 CORRECTIONS block; sub-plan §I sub-task 2 rescope; HALT-resolution disposition memo at `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` (commit `00790855b`); 3-way disposition review trio at `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-{code-reviewer,reality-checker,technical-writer}.md`; trio convergence at commit `b4a6a50e6`.

#### DIRECT tables (Minteo-COPM raw events; DEFERRED-via-scope-mismatch)

- **`onchain_copm_transfers`** — DIRECT. COPM-Minteo `0xc92e8fc2…` Transfer events; 110,253 rows; coverage 2024-09-17 → 2026-04-25. Schema: `evt_block_date`, `evt_block_time`, `evt_tx_hash`, `from_address`, `to_address`, `value_wei`, `evt_block_number`, `log_index`. Slug-vs-on-chain-source asymmetry note: the table name `_copm_` is a pre-rebrand legacy artifact preserved for migration-stability per `project_mento_canonical_naming_2026`; the table tracks Minteo-fintech COPM (uppercase final M, `0xc92e8fc2…`), NOT Mento-native COPm (lowercase final m, `0x8A567e2a…`). No rename under this sub-plan per §B-2.
- **`onchain_copm_burns`** — DIRECT. Minteo-fintech burn calls; 121 rows; schema includes `burn_kind` (likely partition: standard burn vs. freeze-burn vs. timelock-burn). Sourced via call traces on `0xc92e8fc2…`.
- **`onchain_copm_mints`** — DIRECT. Minteo-fintech mint calls; 146 rows; schema includes `to_address` recipient + `tx_from` caller. Sourced via call traces on `0xc92e8fc2…`.
- **`onchain_copm_freeze_thaw`** — DIRECT. Minteo-fintech freeze/thaw events; 4 rows; schema includes `event_type` partition (freeze | thaw). Sourced via event logs on `0xc92e8fc2…`.
- **`onchain_copm_ccop_daily_flow`** — DIRECT (paired source); explicit RC R-2 narrative treatment in §6. Tracks BOTH `0xc92e8fc2…` Minteo-COPM mint/burn AND a separately-named `ccop_*` USDT-pairing source. 585 rows. Per §I sub-task 2 rescope, this table is DEFERRED-via-scope-mismatch (Minteo-COPM scope-mismatch dominates).

#### DERIVATIVE tables (computed from `onchain_copm_transfers`; DEFERRED-via-scope-mismatch by inheritance)

- **`onchain_copm_daily_transfers`** — DERIVATIVE. Parent: `onchain_copm_transfers` (daily aggregation per `evt_block_date`: `n_transfers`, `n_tx`, `n_distinct_from`, `n_distinct_to`, `total_value_wei`). 522 rows. Inheritance chain: `onchain_copm_transfers` (raw events) → daily-aggregation reduction.
- **`onchain_copm_time_patterns`** — DERIVATIVE. Parent: `onchain_copm_transfers`. Schema (`kind`, `bucket`, `n`, `wei`) suggests diurnal / hour-of-day / day-of-week pattern aggregation. 86 rows. Inheritance chain: `onchain_copm_transfers` → time-pattern reduction.
- **`onchain_copm_address_activity_top400`** — DERIVATIVE. Parent: `onchain_copm_transfers`. Top-400 (300 actually present at audit time; the `_top400` slug is a target-cap, not a strict count) sender/receiver activity reduction (`n_inbound`, `inbound_wei`, `n_outbound`, `outbound_wei`). Inheritance chain: `onchain_copm_transfers` → address-activity reduction.
- **`onchain_copm_transfers_sample`** — DERIVATIVE. Parent: `onchain_copm_transfers`. 10-row sample (likely random or first-N). Inheritance chain: `onchain_copm_transfers` → sample reduction.
- **`onchain_copm_transfers_top100_edges`** — DERIVATIVE. Parent: `onchain_copm_transfers`. Top-100 from→to edge aggregation (`from_address`, `to_address`, `n_transfers`, `total_value_wei`, `first_time`, `last_time`). 100 rows. Inheritance chain: `onchain_copm_transfers` → edge-aggregation reduction.

All five DERIVATIVE tables inherit the `0xc92e8fc2…` address attribution from `onchain_copm_transfers`; the DEFERRED-via-scope-mismatch tag flows through with no separate address audit required.

### §4.4 — DEFERRED tables (prior Rev-5.3.x scope; not β-rescope)

**Count: 0.** No table at audit time is DEFERRED purely under prior Rev-5.3.x scope (e.g., authored ahead of need but not yet consumed). All 14 tables are either (a) DIRECT in-scope, (b) DIRECT mixed-scope per `proxy_kind`, (c) DERIVATIVE (inheriting), or (d) DEFERRED-via-scope-mismatch under Rev-5.3.5 β. The pure-DEFERRED bucket is empty.

---

## §5 — `onchain_xd_weekly` proxy_kind enumeration (10 active values, per Rev-5.3.2 design doc §3 row table)

Pre-flight `SELECT proxy_kind, COUNT(*) FROM onchain_xd_weekly GROUP BY proxy_kind ORDER BY proxy_kind` confirms 10 distinct `proxy_kind` values matching the sub-plan §C sub-task 2 expected list. Per-`proxy_kind` provenance + Mento-native scope status under β:

| # | proxy_kind | Row count | On-chain source(s) | Mento-native scope under β |
|---|---|---|---|---|
| 1 | `carbon_basket_user_volume_usd` | 82 | Carbon DeFi user-side basket volume; `onchain_carbon_tokenstraded` filtered to `trader != 0x8c05ea30…` per `project_carbon_user_arb_partition_rule`; basket = Mento-native stablecoin family (USDm/EURm/BRLm/KESm/XOFm + future COPm) | **In-scope** (primary X_d under Rev-5.3.2; basket-internal flows on Mento-native side; Carbon DeFi as MM platform) |
| 2 | `carbon_basket_arb_volume_usd` | 82 | Carbon DeFi arbitrageur-side basket volume; `onchain_carbon_tokenstraded` filtered to `trader = 0x8c05ea30…` (BancorArbitrage) per `project_carbon_user_arb_partition_rule` | **In-scope** (arb-side diagnostic; same basket scope as user-side) |
| 3 | `b2b_to_b2c_net_flow_usd` | 79 | Supply-channel diagnostic (B2B-issued stables flowing to B2C wallets via Mento Reserve broker / minter-partition heuristic); pre-existing under Rev-5.3.2 scope | **In-scope** (Mento-native supply-channel diagnostic; address-source remains Mento Reserve / Mento-native StableTokenV2 contracts per sub-task 1 §β-rescope.1) |
| 4 | `net_primary_issuance_usd` | 84 | Supply-channel diagnostic (net new issuance against Mento Reserve over the week); pre-existing under Rev-5.3.2 scope | **In-scope** (Mento-native primary-issuance diagnostic; address-source = Mento Reserve / Mento-native StableTokenV2 contracts) |
| 5 | `carbon_per_currency_copm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to the COPM-Minteo address `0xc92e8fc2…` (Rev-2 source) | **DEFERRED-via-scope-mismatch under β** — the slug `_copm_` (lowercase) refers to Minteo-fintech COPM at `0xc92e8fc2…`, NOT Mento-native COPm at `0x8A567e2a…` per Rev-5.3.5 β-disposition; sub-plan §I sub-task 2 rescope |
| 6 | `carbon_per_currency_brlm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to BRLm `0xe8537a3d…` (sub-task 1 §β-rescope.1 entry 4) | **In-scope** (BRLm Mento-native, basket-active) |
| 7 | `carbon_per_currency_eurm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to EURm `0xD8763CBa…` (sub-task 1 §β-rescope.1 entry 3) | **In-scope** (EURm Mento-native, basket-active) |
| 8 | `carbon_per_currency_kesm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to KESm `0x456a3D04…` (sub-task 1 §β-rescope.1 entry 5) | **In-scope** (KESm Mento-native, basket-active) |
| 9 | `carbon_per_currency_usdm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to USDm `0x765DE816…` (sub-task 1 §β-rescope.1 entry 2) | **In-scope** (USDm Mento-native, basket-active) |
| 10 | `carbon_per_currency_xofm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to XOFm `0x73F93dcc…` (sub-task 1 §β-rescope.1 entry 6) | **In-scope** (XOFm Mento-native, basket-active) |

**In-scope per-`proxy_kind` count: 9 of 10.** The single DEFERRED-via-scope-mismatch is `carbon_per_currency_copm_volume_usd`. The Rev-5.3.2 published estimates against `carbon_basket_user_volume_usd` (primary X_d) remain byte-exact-immutable per anti-fishing invariants (`decision_hash = 6a5f9d1b05c1…443c`); the per-currency COPM proxy was a diagnostic, not the primary X_d, so the scope-mismatch does NOT propagate to the primary estimates.

**Slug-vs-canonical-ticker note (per sub-plan §C sub-task 2 acceptance line 132).** All `proxy_kind` slugs use lowercase canonical post-rebrand tickers (`copm`, `brlm`, `eurm`, `kesm`, `usdm`, `xofm`), matching the Reality Checker's pre-flight `SELECT DISTINCT proxy_kind` probe at sub-plan-review time. The lowercase `copm` slug in `carbon_per_currency_copm_volume_usd` resolves to Minteo-fintech `0xc92e8fc2…` under the audit-time data ingestion (Rev-2 source), NOT to Mento-native COPm at `0x8A567e2a…` (which has zero events ingested at audit time per sub-task 1 §β-rescope.1 entry 1's "0 events ingested" clause). Future-revision rename recommendation if this pattern becomes confusing: a separate `proxy_kind` slug could be authored for Mento-native COPm flows once ingestion plumbing lands (e.g., `carbon_per_currency_copm_mento_volume_usd`); NOT executed under this sub-plan per §B-2; recommendation only.

---

## §6 — `onchain_copm_ccop_daily_flow` explicit narrative treatment (RC R-2)

Per RC R-2 in sub-plan §H CORRECTIONS, this table receives explicit narrative treatment because its name literally embeds the cCOP-vs-COPM ambiguity that Rev-5.3.5 β-resolution exists to lock down.

### §6.1 — Table content + filter verification

**Schema** (8 substantive columns + audit timestamp):

- `date` DATE — daily bucket; coverage 2024-09-17 → 2026-04-24 (585 rows).
- `copm_mint_usd` VARCHAR — daily Minteo-COPM mint volume in USD (sourced from Minteo `0xc92e8fc2…` mint events).
- `copm_burn_usd` VARCHAR — daily Minteo-COPM burn volume in USD (sourced from Minteo `0xc92e8fc2…` burn events).
- `copm_unique_minters` UINTEGER — daily distinct minter address count for Minteo-COPM.
- `ccop_usdt_inflow_usd` VARCHAR — daily USDT inflow paired with a token referred to as `ccop` (separately-named, distinct from COPM).
- `ccop_usdt_outflow_usd` VARCHAR — daily USDT outflow paired with the same `ccop` token.
- `ccop_unique_senders` UINTEGER — daily distinct sender count for the `ccop` token.
- `source_query_ids` VARCHAR — Dune query ID provenance (audit-time value: single distinct ID `7366593`).

**Null-pattern probe.** 585 total rows; `copm_*` columns 100% non-null (585/585); all three `ccop_*` columns (`ccop_usdt_inflow_usd`, `ccop_usdt_outflow_usd`, `ccop_unique_senders`) 92.5% non-null (541/585). The asymmetric null pattern between `copm_*` (100%) and `ccop_*` (92.5%) confirms the table is a join of ≥2 separate sub-queries on `date`, not a single-source filter — and the uniform 92.5% non-null rate across all three `ccop_*` columns confirms they share the same source sub-query (Dune query `7366593` USDT-paired historical-cCOP). [Corrected per RC sub-task 2 spot-check 2026-04-26: prior version of this paragraph mis-stated `ccop_unique_senders` as 100% non-null; live re-probe confirms 541/585 = 92.5%, which strengthens rather than weakens the paired-source conclusion. Scope tag DEFERRED-via-scope-mismatch and structural conclusion are unaffected.]

**Sample rows** (most-recent 3, abbreviated):

- 2026-04-24: `copm_mint_usd=0.000000`, `copm_burn_usd=0.000000`, `copm_unique_minters=0`, `ccop_usdt_inflow_usd=0.000000`, `ccop_usdt_outflow_usd=0.000000`, `ccop_unique_senders=9`. (COPM mint/burn idle; ccop-USDT-pairing idle; 9 distinct senders on the `ccop` side suggests micro-flows below USD-rounding threshold.)
- 2026-04-23: similar idle pattern; `ccop_unique_senders=20`.
- 2026-04-22: `copm_*` idle; `ccop_usdt_inflow_usd=1786.55`, `ccop_usdt_outflow_usd=2543.92`; `ccop_unique_senders=16`. (Positive `ccop` USDT-pairing volume; positive sender count.)

### §6.2 — Filter-address determination

**The table is a paired-source artifact tracking TWO distinct on-chain identities joined on `date`:**

1. **COPM side** (`copm_*` columns, 585/585 non-null): sourced from Minteo-fintech `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` mint/burn call traces. **OUT of Mento-native scope under β.**
2. **`ccop` side** (`ccop_*` columns, 541/585 USDT-pairing non-null + 585/585 sender-count non-null): sourced from a token referred to in the schema as `ccop`, paired with USDT inflow/outflow. The schema does NOT pin a contract address; the source is the upstream Dune query ID `7366593`. The `ccop_*` token is **a separate identity from `copm_*`** (different non-null cardinality; different aggregation columns; different USDT-pairing semantic).

**Sub-plan §C sub-task 2 acceptance line 130 question — "single-address Minteo-COPM vs. paired vs. another configuration?" — RESOLVED: paired.**

The `ccop` side's address-level identity is NOT directly determinable from DuckDB schema introspection alone; the pre-flight Dune query `7366593` would resolve it. Per the audit's read-only / no-row-mutation hard constraint, this is recorded as a forward-pointer for downstream work (β-spec or future RC re-review): the `ccop` side may resolve to (a) a historical Curve / Uniswap pool involving a token labeled `cCOP` on Celo, (b) a Dune-hosted aggregation across multiple cCOP-historical token contracts, or (c) something else entirely. **At audit time, what is verifiable is that the `ccop` columns are NOT sourced from `0xc92e8fc2…` — they are a separate source paired by date.**

### §6.3 — Scope tag under β

**Tag: DEFERRED-via-scope-mismatch.** Reasoning:

- The `copm_*` half of the table is unambiguously OUT of Mento-native scope (Minteo-fintech `0xc92e8fc2…`).
- The `ccop_*` half is unspecified-address-source under audit-time read-only verification; it is ALSO not Mento-native COPm at `0x8A567e2a…` (no Dune query ID at audit time targets that address; the Mento-native COPm Dune attribution path was authored under sub-task 1 re-dispatch via separate query IDs 7378788/7379527/7379530).
- Both halves of the paired source are NON-Mento-native under β disposition. The DEFERRED-via-scope-mismatch tag applies to the table as a whole.

### §6.4 — Future-revision rename recommendation (per sub-plan §C sub-task 2 acceptance line 130 + §I sub-task 2 rescope strengthening)

**Recommendation (NOT executed under this sub-plan; sub-plan §B-2 prohibits renames):**

- **Drop the `_ccop_` slug fragment** — the fragment is a pre-rebrand legacy artifact meaningless under the post-rebrand corrected naming per `project_mento_canonical_naming_2026` and ambiguous under Rev-5.3.5 β-disposition.
- **Re-slug as `onchain_copm_minteo_daily_flow`** — pinning the `_minteo_` qualifier makes the Minteo-fintech scope explicit at the table-name level and prevents future readers from conflating with Mento-native COPm.
- **If the `ccop_*` side later requires preservation in a separate table**, author a new artifact (e.g., `onchain_celo_ccop_historical_usdt_flow`) with a name that pins the historical / pre-rebrand semantic and the USDT-pairing nature, rather than overloading a single table with two source identities.

The recommendation is recorded for a future revision's consideration; sub-plan §B-2's "no rename, no schema migration" invariant binds this sub-task.

### §6.5 — Slug-asymmetry note (per sub-plan §C sub-task 2 acceptance line 131)

The table-name `onchain_copm_ccop_daily_flow` carries TWO mutually-conflicting slug fragments under Rev-5.3.5 β-disposition:

- `_copm_` — under post-rebrand canonical naming this would suggest Mento-native COPm (`0x8A567e2a…`); under audit-time live ingestion it actually resolves to Minteo-fintech COPM (`0xc92e8fc2…`).
- `_ccop_` — pre-rebrand legacy fragment with no canonical address under post-rebrand naming; ambiguously refers to "some historical cCOP-named token on Celo" without address-level pinning.

**Slug-asymmetry note recorded; no rename request under this sub-plan per §B-2.** The RC R-2 explicit-narrative-treatment requirement is satisfied by §6.1 + §6.2 + §6.3 + §6.4 + this §6.5.

---

## §7 — `onchain_carbon_*` follow-up forward-pointer for β-spec (Task 11.P.spec-β)

Per sub-plan §I sub-task 2 rescope third paragraph: the `onchain_carbon_*` tables remain DIRECT in scope; their coverage of Mento-basket internal flows uses the `0xc92e8fc2…` address as one of the basket-counter-sides under the (now-corrected) prior assumption. The audit memo records this as a **forward-pointer for β-spec identification design**:

- **Open question.** When CarbonController `0x66198711…` and BancorArbitrage `0x8c05ea30…` route Mento-basket trading involving the Colombian-peso side, do they swap against Minteo-fintech COPM at `0xc92e8fc2…` (the Rev-2 X_d source for `carbon_per_currency_copm_volume_usd`) or against Mento-native COPm at `0x8A567e2a…` (the Rev-5.3.5 β-disposition canonical Mento-native address) or both?
- **Why it matters.** Task 11.P.spec-β must decide whether the `carbon_per_currency_copm_volume_usd` proxy_kind needs (a) re-derivation against `0x8A567e2a…` for Mento-native scope (creating a NEW proxy_kind slug while preserving the old DEFERRED-via-scope-mismatch one), (b) preservation as a DEFERRED-via-scope-mismatch diagnostic only, or (c) both — depending on whether Carbon DeFi MM trades on Mento-native COPm yet, given the Mento-native COPm address has 285,390 transfers (sub-task 1 §β-rescope.1 entry 1) and zero rows ingested into `onchain_carbon_*` at audit time.
- **Out of scope for sub-task 2.** The empirical resolution requires a Dune query against `mento_celo.*` decoded tables joined to `onchain_carbon_tokenstraded` filtered by `sourceToken` ∈ {`0xc92e8fc2…`, `0x8A567e2a…`} — that probe is identification-design work, not table-audit work.
- **In scope for Task 11.P.spec-β.** The β-spec must enumerate the candidate X_d address-source set (Mento-native-only vs. Minteo-and-Mento-native vs. Mento-native-only-with-Minteo-as-DEFERRED-diagnostic) and pre-commit to one before any β estimation runs; this prevents the silent-X_d-swap anti-fishing failure mode flagged under `feedback_pathological_halt_anti_fishing_checkpoint`.

The forward-pointer is recorded; β-spec authoring is OUT of scope under MR-β.1.

---

## §8 — Slug-asymmetry consolidated table (no rename requests)

| Slug fragment surfaced | Slug location | On-chain identity at audit time | Slug-vs-source asymmetry note |
|---|---|---|---|
| `_copm_` | 12 of 14 table names + 1 `proxy_kind` | Minteo-fintech `0xc92e8fc2…` | Pre-rebrand legacy slug; under post-rebrand canonical naming would suggest Mento-native COPm `0x8A567e2a…`; preserved for migration-stability per `project_mento_canonical_naming_2026` |
| `_ccop_` | 1 of 14 table names (`onchain_copm_ccop_daily_flow`) | Separately-named historical-cCOP token (address unspecified at audit-time read-only verification) | Pre-rebrand legacy slug with no canonical post-rebrand address attribution; future-revision rename recommended in §6.4; no rename under §B-2 |
| `copm_diff` (column name) | `onchain_y3_weekly` schema | Methodology-scoped Y panel CO-component (DANE / IMF macro data); NOT address-filtered to any Celo contract | Column name follows pre-rebrand legacy convention; column tracks macro-data-derived inequality differential, not on-chain Minteo-fintech events |
| `carbon_per_currency_copm_volume_usd` | `onchain_xd_weekly` proxy_kind | Minteo-fintech `0xc92e8fc2…` Carbon-DeFi-traded volume | Same as `_copm_` table-name slug pattern; legacy slug; β-rescope DEFERRED-via-scope-mismatch |
| `carbon_per_currency_{usdm,eurm,brlm,kesm,xofm}_volume_usd` | `onchain_xd_weekly` proxy_kinds | Mento-native StableTokenV2 addresses per sub-task 1 §β-rescope.1 entries 2-6 | Slug matches canonical post-rebrand tickers; no asymmetry; in-scope under β |

**No rename requests are issued under this audit.** Slug-asymmetry notes are documentation-only per sub-plan §B-2 + §I sub-task 2 rescope's annotation-only discipline.

---

## §9 — Coverage-completeness verification

**Acceptance line 9 (sub-plan §C sub-task 2):** count(tagged tables) MUST equal count(rows from pre-flight enumeration query). Any divergence HALTS.

**Pre-flight enumeration query result (§1):** 14 `onchain_*` tables.

**Audit tagging tally (§3):**

- DIRECT in-scope: 3 (`onchain_carbon_arbitrages`, `onchain_carbon_tokenstraded`, `onchain_y3_weekly`)
- DIRECT mixed-scope: 1 (`onchain_xd_weekly`; 9-of-10 `proxy_kind` in-scope, 1-of-10 DEFERRED-via-scope-mismatch)
- DIRECT DEFERRED-via-scope-mismatch: 5 (`onchain_copm_transfers`, `onchain_copm_burns`, `onchain_copm_mints`, `onchain_copm_freeze_thaw`, `onchain_copm_ccop_daily_flow`)
- DERIVATIVE DEFERRED-via-scope-mismatch (inheriting): 5 (`onchain_copm_address_activity_top400`, `onchain_copm_daily_transfers`, `onchain_copm_time_patterns`, `onchain_copm_transfers_sample`, `onchain_copm_transfers_top100_edges`)
- DEFERRED (prior Rev-5.3.x scope, not β): 0

Sum: 3 + 1 + 5 + 5 + 0 = **14**. **Matches pre-flight enumeration count of 14. Coverage HALT-clear.**

Per-`proxy_kind` tally for `onchain_xd_weekly` (§5): 9 in-scope + 1 DEFERRED-via-scope-mismatch = 10 distinct proxy_kinds = pre-flight `SELECT DISTINCT proxy_kind` count. **Per-`proxy_kind` HALT-clear.**

---

## §10 — HALT-VERIFY discipline reaffirmation

Per `feedback_pathological_halt_anti_fishing_checkpoint`:

- **No row mutations.** All DuckDB queries this audit ran were schema-introspection (`information_schema.tables`, `information_schema.columns`), aggregation (`COUNT(*)`, `GROUP BY proxy_kind`, null-pattern probes), or sample retrieval (3-row `LIMIT`). No `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, or `DROP` was issued. Read-only invariant preserved.
- **No table renames; no schema migrations.** Slug-asymmetry notes are documentation-only; future-revision rename for `onchain_copm_ccop_daily_flow` is a recommendation (§6.4), not an execution. Per sub-plan §B-2.
- **No spec / plan / sub-plan edits; no project-memory edits.** This audit memo is a new file at `contracts/.scratch/2026-04-25-duckdb-address-audit.md`; no other files were modified by the act of authoring this audit.
- **No anti-fishing invariant relaxed.** N_MIN = 75, POWER_MIN = 0.80, MDES_SD = 0.40, MDES_FORMULATION_HASH = `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa`, decision_hash = `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`, Rev-2 14-row resolution matrix all unchanged. The β-rescope is a scope correction, not a threshold relaxation.
- **No discrepancy fired.** The 14 pre-flight returned tables match the sub-plan §C sub-task 2 expected list (10 `onchain_copm_*` + 2 `onchain_carbon_*` + `onchain_xd_weekly` + `onchain_y3_weekly` = 14). The 10 `proxy_kind` values match the sub-plan §I sub-task 2 expected enumeration. The `onchain_copm_ccop_daily_flow` paired-source finding is NEW empirical evidence (paired vs. single-address question per sub-plan §C sub-task 2 acceptance line 130 RESOLVED to paired) but does NOT trigger HALT — it is exactly the kind of disambiguation the RC R-2 explicit-narrative-treatment requirement was authored to surface.

**No HALT-VERIFY GATE fires under this audit.**

---

## §11 — Audit-trail cross-references

- This audit memo: `contracts/.scratch/2026-04-25-duckdb-address-audit.md`
- Sub-task 1 inventory (cross-checked for in-scope addresses): `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` — §β-rescope.1 (in-scope 6 tokens) + §β-rescope.2 (out-of-scope COPM-Minteo) + §β-rescope.4 (audit-trail cross-references)
- Sub-task 1 re-dispatch + RC spot-check: commits `b6d320429` + `eb72f7133`
- Sub-plan trio convergence: commit `b4a6a50e6`
- Sub-plan source-of-truth: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` — §C sub-task 2 + §I sub-task 2 rescope + §H R-1 / R-2 / R-5 dispositions
- Major plan Rev-5.3.5 CORRECTIONS block: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (file end)
- HALT-resolution disposition memo (β path): `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` (commit `00790855b`)
- 3-way disposition review trio: `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-{code-reviewer,reality-checker,technical-writer}.md`
- Live DuckDB at audit-authoring time: `contracts/data/structural_econ.duckdb` (read-only connection; no row mutations)
- Project-memory anchors load-bearing on this audit:
  - `project_mento_canonical_naming_2026` — canonical post-rebrand tickers + addresses; β-corrigendum block at file top
  - `project_abrigo_mento_native_only` — Abrigo scope = Mento-native ONLY; β-corrigendum extension
  - `project_carbon_defi_attribution_celo` — CarbonController `0x66198711…` and BancorArbitrage `0x8c05ea30…` attribution
  - `project_carbon_user_arb_partition_rule` — `trader = 0x8c05ea30…` row-level partition for `onchain_carbon_tokenstraded` user-vs-arb USD split
  - `project_y3_inequality_differential_design` — 4-country Y₃ panel methodology (orthogonal to X_d address rescope under β)
  - `feedback_pathological_halt_anti_fishing_checkpoint` — HALT-on-discrepancy invariant
  - `feedback_no_code_in_specs_or_plans` — code-agnostic body discipline; one permitted SQL fragment in §1
- Future research safeguard reference (sub-plan §C sub-task 5): `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md` (forward-pointer; sub-task 5 deliverable not yet authored at this audit's authoring time)

**End of DuckDB table-to-address audit (MR-β.1 sub-task 2).**
