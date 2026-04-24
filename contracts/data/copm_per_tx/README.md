# COPM Per-Transaction Data — Provenance & Schema

**Token**: Minteo COPM (Colombian-peso-pegged stablecoin on Celo)
**Token contract**: `0xA9d2927db8b83fCcAeB0a5Bd1aB34e4f7c30E9d6` (COPM v1) — inferred from `copm_token_v_1_celo.tokenv1_*` namespace
**Data pulled**: 2026-04-24 (fresh billing period)
**Task**: 11.M — Resume by fresh agent after original `aa0bf238c4ca1b501` stalled at 07:37 UTC

## Dune queries used (all temporary MCP queries, re-executable)

| Purpose | Query ID | Execution ID | Rows | Credits |
|---|---|---|---|---|
| Transfers (LIMIT 100 probe, then full)  | 7369028 | 01KPZVETGZGP4KDSTGKDNH1FY7 | 110,069 | 0.017 |
| Freeze/thaw/burnedfrozen UNION          | 7369029 | 01KPZVF00XMMHDJVNAZQKDDWWZ | 4       | 0.013 |
| Row count sanity                        | 7369030 | 01KPZVDSFC5HS1NY561NKJ4V57 | 4       | 0.017 |
| Transfer edges (from×to aggregate)      | 7369036 | 01KPZVHN0M5QK05WPZSR2HZXW4 | 4,145   | 0.012 |
| Daily totals                            | 7369037 | 01KPZVHQ12F5HHBC0PSC1N7SCQ | 522     | 0.025 |
| Address-level activity                  | 7369051 | 01KPZVPBP6EM35RGRSGC8RB7KN | 1,939   | 0.032 |
| DoW/DoM/month time patterns             | 7369052 | 01KPZVPDARP8ND47V4P6AXND0B | 86      | 0.056 |
| Mint-receiver aggregates                | 7369045 | 01KPZVN4DA1ZVR0DK0ZGKZCNK5 | 1       | 0.014 |
| Diffusion per first-receiver            | 7369047 | 01KPZVN688EP1382MSA5W3RGB9 | 1       | 0.022 |
| Edges/addresses/dates counts            | 7369039 | 01KPZVJHTNDYVGP38XX5YXQYKF | 3       | 0.023 |

**Total credits for Task 11.M extensions**: ≈ 0.26 (well under 10-credit budget)
**Billing period usage at task close**: 4.688 credits used of quota.

## Source Dune tables (decoded, category=decoded, blockchain=celo)

- `copm_token_v_1_celo.tokenv1_call_mint` — mint calls (caller, amount, `to`)
- `copm_token_v_1_celo.tokenv1_call_burn` — standard burn calls (caller, amount)
- `copm_token_v_1_celo.tokenv1_call_burnfrozen` — burnFrozen calls (caller, `account`, amount)
- `copm_token_v_1_celo.tokenv1_evt_transfer` — ERC-20 Transfer events (`from`, `to`, `value`)
- `copm_token_v_1_celo.tokenv1_evt_frozen` — Frozen events (`account`)
- `copm_token_v_1_celo.tokenv1_evt_thawed` — Thawed events (`account`)
- `copm_token_v_1_celo.tokenv1_evt_burnedfrozen` — BurnedFrozen events (`account`, `amount`)

Raw column names preserve Dune decoded-table conventions: `evt_block_date`, `evt_block_time`, `evt_tx_hash`, `evt_block_number` for events; `call_block_date`, `call_success`, `call_tx_from`, etc. for calls.

## Files

| File | Rows | Purpose | Schema |
|---|---|---|---|
| `copm_mints.csv` | 146 | Mint calls (from original `aa0bf238` agent) | `call_block_date, call_block_time, call_tx_hash, call_tx_from, to_address, amount_wei, call_success, call_block_number` |
| `copm_burns.csv` | 121 | Burn + burnFrozen UNION (from original agent) | `call_block_date, call_block_time, call_tx_hash, call_tx_from, account, amount_wei, call_success, call_block_number, burn_kind` |
| `copm_transfers.csv` | 10 sample + caveat header | **See caveat below**; first 10 rows preserved as shape reference | `evt_block_date, evt_block_time, evt_tx_hash, from_address, to_address, value_wei, evt_block_number` |
| `copm_freeze_thaw.csv` | 4 | UNION of frozen+thawed+burnedfrozen events | `evt_block_date, evt_block_time, evt_tx_hash, account, amount_wei, event_type, evt_block_number` |
| `copm_transfers_top100_edges.csv` | 91 | Top edges by transfer count (covers >80% of volume) | `from_address, to_address, n_transfers, total_value_wei, first_time, last_time` |
| `copm_daily_transfers.csv` | 522 | Daily transfer totals (full date range) | `evt_block_date, n_transfers, n_tx, n_distinct_from, n_distinct_to, total_value_wei` |
| `copm_address_activity_top400.csv` | 400 | Top-400 addresses by n_inbound + n_outbound | `address, n_inbound, inbound_wei, n_outbound, outbound_wei` |
| `copm_time_patterns.csv` | 86 | DoW/DoM/Month aggregates (mints + transfers) | `kind, bucket, n, wei` |

Data types: addresses lowercase `0x`-prefixed 40-hex; `*_wei` / `amount` / `value` kept as decimal-string-of-digits (preserves uint256 precision; load with `dtype={"amount_wei":"string"}` / `dtype={"value_wei":"string"}` in pandas).

## Date ranges (observed)

- **Mints**: 2024-09-17 → 2026-03-24
- **Burns**: 2024-10-10 → 2026-04-14
- **Transfers**: 2024-09-17 → 2026-04-24 (522 distinct dates)
- **Freeze/thaw**: 2024-12-13 → 2024-12-16 (single account)

## IMPORTANT CAVEAT — Raw transfers CSV incomplete

The full 110,069-row raw transfer dataset exceeded the practical limit of Dune MCP pagination
(100 rows per `getExecutionResults` call → ~1,101 paginated calls would be required, each
returning ~17KB JSON = ~18 MB of agent context just for a single raw dump).

**Resolution**: `copm_transfers.csv` contains only the first 10 rows as a schema/shape reference.
For the full dataset, re-execute Dune query 7369028 and export via the Dune web UI
(https://dune.com/queries/7369028) "Download CSV" button, which streams all 110k rows in one
HTTP response (not subject to the MCP 100-row batch cap).

**Why this is still adequate for the profile report**: all aggregation questions (volume,
concentration, diffusion, network structure, time patterns, freeze activity, usage
classification) reduce to SQL-side aggregates that are computed in Dune and saved as the
smaller supporting CSVs above. The per-tx raw rows are not used by the profile analysis
beyond spot-checks; they would only be needed for per-tx labelling (e.g. identifying a
specific swap on DEX-X on date-Y), which is out of scope for Task 11.M.

## Known irregularities

- **`copm_burns.csv` has 1 `burnFrozen` row** (2024-12-16, account `0x1ca33cff...`, 30.67M wei).
  Matching pair of `frozen` (2024-12-13) + `frozen` + `thawed` + `burnedfrozen` events visible
  in `copm_freeze_thaw.csv`. Single-account compliance action.
- **Mint receiver is unique**: all 146 mints go to `0x0155b191ec52728d26b1cd82f6a412d5d6897c04`
  (Minteo primary-issuance wallet). Mint-call `call_tx_from` varies across 6-7 role-holder EOAs.
- **Distribution-hub shift**: primary downstream distributor was `0x0155b19...` (Sept 2024 →
  mid-2025), then activity shifted to `0x5bd35ee3c1975b2d735d2023bd4f38e3b0cfc122` (late-2025 →
  present) as a new retail fan-out node. Both are reached by going through the `0x6619/0x8c05`
  B2B oscillation cluster.

## Re-execution

All queries are temporary MCP queries owned by the authenticated customer context; any re-run
would use `mcp__dune__executeQueryById(query_id=<id>)` → `mcp__dune__getExecutionResults`.
Fresh executions cost roughly the same as the originals (≤0.06 credits per query).
