# Carbon DeFi Celo — Mento ↔ Global Basket Boundary Panel

**Generated:** 2026-04-25
**Task:** 11.N.2b.2 (Rev-5.3)
**Plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`

## Files

- `weekly_basket_panel.csv` — 253 rows; one per `(week_friday, mento_currency, partition)` tuple. Pre-aggregated SQL-side from Dune.

## Source

| field | value |
|---|---|
| Dune query ID | `7372282` |
| Query name | "11.N.2b.2 Step 1 final — weekly Carbon basket panel (USD-priced, partitioned)" |
| Dune execution ID | `01KQ1ZZGYYMFKADNZDB8Z4ECDY` |
| Execution credits | 0.642 |
| Date range | 2024-08-30 → 2026-04-03 (Friday anchors; basket activity bounded by Carbon DeFi Celo deployment 2024-09-01 + corrigendum panel range 2024-09-01..2026-04-25) |

## Schema

| column | dtype | description |
|---|---|---|
| `week_friday` | DATE | ISO-week Friday anchor (`DATE_TRUNC('week', evt_block_date) + INTERVAL '4' DAY`). |
| `mento_sym` | VARCHAR(4) | Mento basket symbol: COPM, USDm, EURm, BRLm, KESm, XOFm. |
| `partition` | VARCHAR(4) | `user` or `arb`. `arb` = `trader = 0x8c05ea305235a67c7095a32ad4a2ee2688ade636` (BancorArbitrage contract). See corrigendum §3 for empirical derivation of this rule. |
| `n_events` | BIGINT | Number of `tokenstraded` events in the cell. |
| `sum_usd_volume` | DOUBLE | Σ ABS(source_amount_usd) — volume-weighted USD magnitude per the X_d formula. |
| `min_event_usd` | DOUBLE | Smallest event USD value in the cell (diagnostic). |
| `max_event_usd` | DOUBLE | Largest event USD value in the cell (diagnostic). |

## Aggregation Recipe (SQL)

```sql
-- Boundary filter (Mento ↔ global)
WHERE (sourceToken ∈ Mento AND targetToken ∈ global)
   OR (sourceToken ∈ global AND targetToken ∈ Mento)

-- USD pricing (global-leg numeraire)
source_amount_usd = CASE
    WHEN global_sym IN ('USDT', 'USDC')
         THEN global_leg_amount / 1e6
    WHEN global_sym = 'WETH'
         THEN global_leg_amount / 1e18 * eth_usd_daily_avg
    ELSE NULL
END

-- Friday-of-ISO-week
week_friday = DATE_TRUNC('week', evt_block_date) + INTERVAL '4' DAY

-- Partition
partition = CASE WHEN trader = 0x8c05ea305...ade636 THEN 'arb' ELSE 'user' END
```

Pricing data: `prices.usd` (Dune) for ETH/USD daily mean per Celo blockchain.
Basket addresses: gate memo §1 (Celo token list + Celoscan verified canonical).

## Pre-aggregation rationale

Per-event ingestion (175,005 rows) would require 1,751 MCP-paginated calls.
The Dune MCP cannot paginate via streaming; the CSV download endpoint
requires a `DUNE_API_KEY` not present in this environment. SQL-side weekly
aggregation reduces the canonical-DB row count from 175,005 to 253 while
preserving all information needed for the X_d weekly panel + per-currency
PCA cross-validation in Task 11.N.2c. Trade-off: the
`onchain_carbon_tokenstraded` per-event table (created in 11.N.2b.1
schema migration) is left empty — future agents that need per-event
detail can re-execute Dune query 7372280 at any time.

## Cardinality

| metric | value | source |
|---|---|---|
| Total events ingested | 175,005 | sum of `n_events` |
| User events | 123,511 | sum where `partition='user'` |
| Arb events | 51,494 | sum where `partition='arb'` |
| Unique Friday anchors | 82 | distinct `week_friday` |
| User-only USD volume total | $5,883,539 | sum where `partition='user'` |
| Arb-only USD volume total | $1,019,184 | sum where `partition='arb'` |

These exactly match the corrigendum §4 cardinalities (175,005 boundary
events / 51,494 arb-routed = 29.4% arb share / 123,511 user / 82 weeks).

## Provenance trail

- Step-0 partition probe: Dune queries 7372237, 7372241, 7372243, 7372247
  (corrigendum §2) — empirically verifies `trader = 0x8c05ea…` as the
  canonical user-vs-arb partition rule (equivalent to tx-hash JOIN
  against `bancorarbitrage_evt_arbitrageexecuted`, but cheaper to compute
  and robust to arb-table staleness).
- Step-1 currency probe: Dune query 7372274 — confirms 23 distinct
  (mento, global, partition) cells; XOFm has zero user activity; CELO has
  zero boundary activity.
- Step-1 ETH/USD probe: Dune query 7372275 — confirms `prices.usd` Celo
  WETH coverage 2024-10-15 → 2026-04-25 (45-day pre-2024-10-15 gap
  affects only the first 4 weeks; minimal user activity in those weeks).
