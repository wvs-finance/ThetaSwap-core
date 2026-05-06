# Task 1.3.b Dispatch Disposition

**Plan:** `contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md` (sha256 `7e2f43c211a314475c3fc2ef5890c268c7216efa55b0b7a9d2c8e5d8d95bca6b`)
**Spec:** `contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md` (sha256 `fcebc95f923e1b55fbf2eaa22239b00bbde4a9f35bb031e8f32d090a4fb80d95`)
**Plan task:** Phase 1 plan-Task 1.3.b (NEW v1.1; emit `mento_swap_flow_inventory.parquet` per spec §4.0 Artifact 4)
**Emit timestamp UTC:** 2026-05-04T12:20:56Z
**Status:** SUCCESS (no HALT)

## §[A] BiPool exchange-id discovery (sub-deliverable)

- **Method:** `getExchanges()` view function called on Mento V2 BiPoolManager `0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901` via Forno eth_call (free public RPC).
- **Discovery block:** 65915058
- **Total exchanges returned:** 16
- **USDm/COPm exchange_id (PINNED):** `0x1c9378bd0973ff313a599d3effc654ba759f8ccca655ab6d6ce5bd39a212943b`
  - assets: [USDm `0x765de816845861e75a25fca122bb6898b8b1282a`, COPm `0x8a567e2ae79ca692bd748ab832081c45de4041ea`]
  - This is exchange index 15 of 16 returned by getExchanges().
- **USDm-paired non-COPm exchange_ids:** 14 exchanges (used for `mento_broker` substrate)
- **Output file:** `contracts/.scratch/pair-d-stage-2-B/v0/mento_v2_bipool_exchange_ids.json`
  - sha256 `4b3c0342a703947a068a455427797cc39726daef12935ac818568b9dae2127ec`

NO HALT. Stage2PathBSqdNetworkCoverageInsufficient did NOT fire — USDm/COPm exchange exists in V2 BiPool.

## §[B] FLAG-B8 partition rule disposition

- **Layer-1 (MEV-bot allowlist):** Eigenphi free-tier API access verified paywalled as of 2026-05-04T12:20:56Z. Per spec §6 `Stage2PathBASOnChainSignalAbsent` fallback path: empty allowlist (size 0). Layer-1 contributes zero MEV bot classifications. Documented in DATA_PROVENANCE.md Entry 11 `filter_applied`.
- **Layer-2 (atomic-arb intra-tx round-trip):** Computed locally from extracted swap set. Atomic-arb (transaction_hash, trader) pairs flagged: 19967. Rule: same trader has both a USDm-out and a USDm-in (or any token-pair round-trip) within the same transaction.
- **`lp_mint_burn` partition:** Always zero-count for Mento V2 Broker substrates (BiPool reserves are protocol-governed via expansion / contraction events, NOT user-LP'd; user surface only sees Swap events). Zero-count rows still emitted for partition exhaustiveness per spec §4.0 Artifact 4 row-count expectation.

## §[C] Per-substrate row-count + volume_usd aggregate

  - mento_v3_fpmm_usdm_cusd: rows=544, total_events=0, total_notional_usd=0.00
  - mento_v2_bipool_usdm_copm: rows=544, total_events=302, total_notional_usd=118658.98
  - mento_broker: rows=544, total_events=94186, total_notional_usd=776988598.99

## §[D] Per-partition row-count distribution

  - non_lp_user: rows=408, total_events=59074, total_notional_usd=305270875.44
  - lp_mint_burn: rows=408, total_events=0, total_notional_usd=0.00
  - mev_arb: rows=408, total_events=35414, total_notional_usd=471836382.54
  - total: rows=408, total_events=94488, total_notional_usd=777107257.97

### Per-(substrate, partition) breakdown

    - (mento_v3_fpmm_usdm_cusd, non_lp_user): rows=136, events=0, notional_usd=0.00
    - (mento_v3_fpmm_usdm_cusd, lp_mint_burn): rows=136, events=0, notional_usd=0.00
    - (mento_v3_fpmm_usdm_cusd, mev_arb): rows=136, events=0, notional_usd=0.00
    - (mento_v3_fpmm_usdm_cusd, total): rows=136, events=0, notional_usd=0.00
    - (mento_v2_bipool_usdm_copm, non_lp_user): rows=136, events=224, notional_usd=75333.71
    - (mento_v2_bipool_usdm_copm, lp_mint_burn): rows=136, events=0, notional_usd=0.00
    - (mento_v2_bipool_usdm_copm, mev_arb): rows=136, events=78, notional_usd=43325.27
    - (mento_v2_bipool_usdm_copm, total): rows=136, events=302, notional_usd=118658.98
    - (mento_broker, non_lp_user): rows=136, events=58850, notional_usd=305195541.73
    - (mento_broker, lp_mint_burn): rows=136, events=0, notional_usd=0.00
    - (mento_broker, mev_arb): rows=136, events=35336, notional_usd=471793057.26
    - (mento_broker, total): rows=136, events=94186, notional_usd=776988598.99

## §[E] Extraction stats

- SQD queries issued: 10
- Forno eth_call (public RPC) calls: 2
- Raw Broker Swap events fetched: 101638
- Parsed in-scope events: 101638
- USDm/COPm (mento_v2_bipool_usdm_copm) events: 332
- USDm-paired non-COPm (mento_broker) events: 101306
- V3 FPMM USDC/USDm (mento_v3_fpmm_usdm_cusd) events: 0 (CONFIRMED via prior audit + re-probe; substrate emits zero-count rows for completeness)

## §[F] Burst-rate compliance

- SQD: 9 chunked queries × 5M blocks each over Celo 20.6M-65.9M; ≥300ms inter-call sleep enforced; concurrency=1; well below the 5 req/sec sustained ceiling per spec §5.A.
- Forno (free public RPC): 2 calls (1 getExchanges + 1 block_number); ≥500ms inter-call sleep; well below the 100 req/sec public-RPC ceiling per spec §5.A.
- Alchemy: 0 CU consumed (Alchemy NOT used for this task per `feedback_real_data_over_mocks` + project_alchemy_celo_403_blocked).
- Dune: 0 credits consumed.

Per-call entries appended to `contracts/.scratch/path-b-stage-2/phase-0/burst_rate_log.csv`.

## §[G] HALT-and-surface items

NONE.

- Stage2PathBSqdNetworkCoverageInsufficient did NOT fire (USDm/COPm exchange present in V2 BiPool).
- Stage2PathBAuditScopeAnomaly: row count = 1632, expected ~1620 ± 50%; deviation = 0.7% (within spec §4.0 ±50% tolerance band; >5x deviation would have triggered HALT).
- Stage2PathBProvenanceMismatch: FLAG-B8 partition exhaustiveness invariant verified — for every (week, substrate) tuple, the 3 individual partition rows (non_lp_user, lp_mint_burn, mev_arb) sum to the `total` row's notional within float-rounding tolerance. Test extension in Task 1.4 covers this.
- Stage2PathBASOnChainSignalAbsent: Layer-1 MEV-bot allowlist empty per spec §6 fallback (Eigenphi free-tier paywalled); documented in DATA_PROVENANCE.md Entry 11 + §[B] above; this is the spec-pinned non-HALT path, NOT a silent failure.

## §[H] Output artifacts

- `contracts/.scratch/pair-d-stage-2-B/v0/mento_swap_flow_inventory.parquet`
  - sha256 `a715129bbb5427110e709db364df92407951345ad644d22b707afe7d66c799c3`
  - rows = 1632
  - schema_version metadata (sha256 of col-set + dtypes per spec §4.0): see DATA_PROVENANCE.md Entry 11
- `contracts/.scratch/pair-d-stage-2-B/v0/mento_v2_bipool_exchange_ids.json`
  - sha256 `4b3c0342a703947a068a455427797cc39726daef12935ac818568b9dae2127ec`
- `contracts/.scratch/pair-d-stage-2-B/v0/DATA_PROVENANCE.md` (Entries 10 + 11 appended)
- `contracts/.scratch/path-b-stage-2/phase-0/burst_rate_log.csv` (per-call entries appended)

## §[I] Path A files untouched

This dispatch ONLY wrote to `contracts/.scratch/pair-d-stage-2-B/v0/` and `contracts/.scratch/path-b-stage-2/`. No Path A files (`contracts/.scratch/pair-d-stage-2-A/...`) were touched. Verify via `git status` post-commit.

## §[J] DuckDB convenience view

NOT created. Per project memory `project_duckdb_xd_weekly_state_post_rev531`, DuckDB is a view-only mirror at most; canonical store is Parquet. The Phase 3 v2 synthetic generator can read `mento_swap_flow_inventory.parquet` directly via `pq.read_table` with the same trivial join cost as a DuckDB view; creating a `.duckdb` file would add no material query-performance benefit at the (week, substrate, partition) granularity (1620 rows). Decision documented here per dispatch brief WORKFLOW step 7.
