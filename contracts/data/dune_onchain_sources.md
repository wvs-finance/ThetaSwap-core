# Dune On-Chain Flow Sources — Task 11.A Provenance Log

**Acquisition date:** 2026-04-24
**Acquirer:** Data Engineer subagent, Phase-1.5 Task 11.A
**Plan spec:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` Rev-3.1
**Output fixture:** `contracts/data/copm_ccop_daily_flow.csv` (585 rows, 2024-09-17 → 2026-04-24)

---

## Step 3 — Rev-3.1 Schema Verification (RC-F1)

Before any query execution, the three cached query IDs proposed by the Rev-3 plan
were fetched via `mcp__dune__getDuneQuery` and their titles + SQL inspected.

### Query #6941901 — **PARTIAL FIT: daily residual only, no mint/burn split**

- **Actual title:** "cCOP Residual Daily Flow v3 — Single Pass (Exercise 1)"
- **Actual target:** `stablecoins_multichain.transfers` filtered to
  `blockchain='celo' AND currency='COP' AND token_symbol IN ('cCOP', 'COPm')`,
  from 2024-10-01 onward, with address-level flags for Thursday-UBI / bot /
  campaign exclusion. Emits DAILY `gross_volume_usd`, `income_volume_usd`,
  `unique_senders`, etc.
- **Role match vs Task 11.A schema:** PARTIAL. The daily cadence matches, but:
  - The query emits CLEANED-RESIDUAL volumes (already stripped of UBI/bot/campaign
    cohorts), not raw transfer-level volumes required for the four-channel
    Task-11.A schema (mint/burn vs inflow/outflow).
  - The query does NOT split cCOP/COPm from COPM; it unions them, and COPM
    (Minteo) data is entirely absent (token_symbol filter excludes COPM).
  - No mint/burn breakdown emitted — mints/burns are not filtered by
    `from=0x0` / `to=0x0` in this query's projection.
- **Decision:** not suitable as the sole source. Superseded by query #7366593
  (see below).

### Query #6940691 — **SCHEMA MISMATCH: all-time aggregate, not daily**

- **Actual title:** "COPM: Transfer Activity vs cCOP vs COPm Comparison"
  (per Rev-3.1 RC-F1: the Rev-3 plan text mislabeled this as "COPM transfers").
- **Actual target:** `stablecoins_multichain.transfers` filtered to
  `blockchain='celo' AND currency='COP'`, grouped by `token_symbol` +
  `token_address` — emits ONE ROW PER TOKEN (3 rows total: cCOP old, COPm
  new, COPM Minteo) with lifetime aggregate stats (`total_transfers`,
  `unique_senders`, `mints`, `burns`, etc.).
- **Role match vs Task 11.A schema:** NO. This is an all-time summary,
  not a daily time series. Cannot be used for the Task-11.A daily schema.
- **Decision:** NOT executed for Task 11.A data-acquisition. However, the
  query's already-cached execution (ID `01KN785CJ2WF46VZEKY3BWPDN1`) was
  useful for establishing token-address ground truth and launch-date
  calibration — see "Ground Truth" section below.

### Query #6939814 — **SCHEMA MISMATCH: broker swaps, not token transfers**

- **Actual title:** "EM Stablecoin Selection: Mento Broker Swaps by Currency"
- **Actual target:** `mento_celo.broker_evt_swap` (swap-venue, NOT token-level),
  last 365 days, grouped by token pair. Emits one row per (token_in, token_out)
  pair with aggregate `swap_count`, `unique_traders`, `first_swap`, `last_swap`.
- **Role match vs Task 11.A schema:** NO. This queries the Mento broker
  contract `0x777a8255ca72412f0d706dc03c9d1987306b4cad` — a swap venue, NOT
  a token contract. Its events are swap-level, not `Transfer(from, to, amount)`.
  The Rev-3.1 RC-B2 disambiguation note explicitly calls this out: a subagent
  that confuses the Mento broker with the cCOP token contract will acquire
  categorically wrong data.
- **Decision:** NOT executed for Task 11.A. Broker swap data is downstream-
  relevant for Task 11.B weekly-aggregation (specifically the "flow_concentration"
  channel by venue) but is out of scope for the Task 11.A transfer-level fixture.

### Summary: all three cached queries fail to match the Task-11.A role

Per Rev-3.1 Step-3 body: "If the verified schema does not match the expected
per-role schema for this task, log the mismatch … and either (a) use
`executeQueryById` on a different cached query whose schema matches, or (b) use
`updateDuneQuery`/`createDuneQuery` only if existing-query modification is
required." Since no cached query matched the required schema and RC-N1 requires
preferring read-only strategies, Task 11.A elected option (b) and created a
new Dune query specifically for this task.

## Step 3b — New Dune query

**Query ID:** 7366593
**Title:** "Task 11.A: Daily COPM + cCOP/COPm On-Chain Flow (Rev-3.1)"
**URL:** https://dune.com/queries/7366593
**Privacy:** public, non-temporary
**SQL summary:** Single-pass over `stablecoins_multichain.transfers` filtered
to `blockchain='celo' AND currency='COP'`, with a six-column projection that
cuts transfers by token address (COPM vs cCOP/COPm) × direction (mint / burn /
inflow / outflow). Partition-pruned on `block_date >= 2024-09-01`. Executed once
on medium tier at 4.16 execution credits.

**Execution ID:** `01KPYR8NBKG4XV0V2VH55XJQ5F` (COMPLETED, 4.16 credits)

**Note on initial failed attempt:** The first SQL draft used hex-literal
token addresses directly in an `IN` clause and failed with a
`varchar/varbinary` coercion error from DuneSQL. The published final SQL
uses `LOWER(CAST(hex AS VARCHAR))` subqueries to normalize, which costs
nothing at query time. Both executions charged against this query's total
compute budget of 4.16 credits.

**Raw-page row counts:** 550 distinct dates-with-activity across pages
0-500 (6 pages × 100 + 1 page × 50). Calendar forward-fill to daily
from 2024-09-17 → 2026-04-24 = 585 rows in the committed fixture.

## Ground Truth — Token Addresses + Launch Dates (from Query #6940691 cached exec)

Query `#6940691` (execution ID `01KN785CJ2WF46VZEKY3BWPDN1`, completed
pre-Task-11.A, 3.61 credits charged against its owner not Task-11.A)
emits three rows verifying:

| Token Symbol | Token Address                                   | Lifetime first_seen (UTC)   | Mints  | Burns  | Unique Senders |
|--------------|-------------------------------------------------|-----------------------------|--------|--------|-----------------|
| cCOP         | 0x8a567e2ae79ca692bd748ab832081c45de4041ea      | 2024-10-31 16:35:48         | 12,197 | 13,851 | 4,913           |
| COPM (Minteo)| 0xc92e8fc2947e32f2b574cca9f2f12097a71d5606      | 2024-09-17 19:54:27         | 146    | 119    | 1,033           |
| COPm (new)   | 0x8a567e2ae79ca692bd748ab832081c45de4041ea      | 2026-01-25 00:41:48         | 1,409  | 2,620  | 181             |

**Load-bearing provenance finds (informed Task-11.A constants):**

1. **cCOP and COPm share the same contract address** `0x8a56...`. The
   2026-01-25 event at that address is a symbol rename cCOP → COPm, NOT a
   contract redeployment. This ratifies Rev-3.1 F-3.1-2's resolution of the
   corpus' internal date-inconsistency in favor of the line-163 "2026-01-25"
   value (line-27 "Jan 2025" is a typo in the corpus).
2. **The 4,913 sender figure is cCOP-OLD cohort lifetime stock** (pre-
   2026-01-25 migration). It is NOT a forward-looking post-Oct-2024 active
   population. Rev-3.1 RC-F2 clarification holds.
3. **COPM (Minteo) on-chain first transfer is 2024-09-17**, not "April 2024"
   as earlier Rev-3 rationale claimed. The Rev-3 "Apr-2024" framing was
   marketing-source, not Dune-verified. Rev-3.1 RC-N2 removed Apr-2024 from
   load-bearing rationale; this provenance log confirms the earliest on-chain
   calibration is 2024-09-17.

## Deviations from Rev-3.1 Plan

### D-1. `_MIN_ROW_COUNT` adjusted 720 → 580 (calendar-infeasibility)

Rev-3.1 CR-F1 prescribed the Step-1 test row-count threshold `>= 720` on the
premise of "24 months × 30 days" of daily data. Measured from COPM's verified
launch (2024-09-17) to Task-11.A acquisition (2026-04-24), only 585 calendar
days have elapsed — honoring the 720 threshold would require zero-padding to
a synthetic pre-launch window. Zero-padding is exactly the anti-pattern that
Rev-3.1 CR-F1's companion non-zero assertion is designed to forbid.

Task 11.A adjusted the calendar-day threshold to `>= 580`, a conservative
COPM-launch-anchored floor that excludes zero-padding but still admits the
modest date-off-by-a-few-days variance that re-executions at slightly different
sampling times would produce. The economic-load-bearing `>= 500 non-zero rows`
assertion is preserved verbatim from Rev-3.1 and passes at 533 non-zero rows.

The full calibration rationale is documented as a module-level docstring on
`_MIN_ROW_COUNT` in
`contracts/scripts/tests/remittance/test_dune_onchain_flow_fetcher.py`.

### D-2. `ccop_usdt_inflow_usd` / `ccop_usdt_outflow_usd` semantics

The Rev-3.1 plan schema labels two cCOP channels as "inflow" and "outflow" but
does not define the cut precisely. Task-11.A's implementation interprets these
as the `to`-side and `from`-side gross volumes of cCOP/COPm transfers with
mint/burn events respectively excluded, i.e.:

- `ccop_usdt_inflow_usd`  = sum of `amount_usd` for transfers with
  `to_address != 0x0` (user-receiving-cCOP side, mints excluded)
- `ccop_usdt_outflow_usd` = sum of `amount_usd` for transfers with
  `from_address != 0x0` (user-sending-cCOP side, burns excluded)

The "usdt" phrasing in the column names is inherited from the Rev-3.1 plan
text and is a labelling convention (not a literal USDT↔cCOP swap ledger,
which would require Mento broker data from query #6939814 — out of scope).

### D-3. COPM query `source_query_ids` field

The Rev-3.1 CSV schema specifies `source_query_ids` as a column. Task-11.A
populates every row uniformly with `"7366593"` (the single Dune query used).
Future refreshes that add a secondary Alchemy-RPC sanity-check path (per
PM-F1 recovery protocol 1b) may populate this field with a pipe-separated
list `"7366593|alchemy-celo-rpc"`; the loader and schema tolerate either.

## Pre-Committed Downstream N (RC-F3)

This fixture supplies the daily-cadence inputs for Task 11.B weekly
aggregation (`weekly_onchain_flow_vector.py`). The pre-committed analytical
sample size for downstream T3b critical values and bridge-gate power
analysis is **N = 95 weekly observations**, anchored at the Feb-2026
Rev-4-panel-end floor. Any additional weekly-equivalent rows from this
585-day fixture are retained but not used in the pre-committed test
statistic; they are reserved for sensitivity analysis only.

## Credit Budget

- **Budget:** ≤ 30 credits (Rev-3.1 plan spec).
- **Consumed by Task 11.A:** 4.16 credits on execution `01KPYR8NBKG4XV0V2VH55XJQ5F`
  (a second execution for the coercion-fix retry produced the 4.16 figure;
  no separate charge was levied per the Dune MCP `executionCostCredits`
  field).
- **Credits used pre-task:** 3.61 on `#6940691` (owner-attributed), not
  charged against the Task-11.A budget.
- **Remaining Task-11.A budget:** 25.84 credits for re-execution if needed.

## Future Refresh Protocol

To re-materialize the fixture at a later sampling time:

1. Check Dune MCP credit balance via `mcp__dune__getUsage`.
2. Re-run `mcp__dune__executeQueryById(query_id=7366593)` at the desired
   performance tier (medium recommended).
3. Paginate through the result set via `mcp__dune__getExecutionResults`
   at `limit=100`, `offset=0,100,200,...` until an empty page is returned.
4. Concatenate all rows, forward-fill to a daily calendar from 2024-09-17
   onward, and zero-fill missing days; write NaN for dates before
   2024-10-31 in cCOP columns.
5. Update `source_query_ids` if any additional queries are joined.
6. Re-run `pytest scripts/tests/remittance/test_dune_onchain_flow_fetcher.py`
   and confirm all tests pass.

An expected Dune credit cost at medium tier is ~4-5 credits per full
re-execution, well inside the 30-credit budget.
