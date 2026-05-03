# Pair D Stage-2 Path B — Phase 1 Task 1.2 dispatch disposition

> **Status:** partial-halt
> **Generated:** 2026-05-03T23:41:09Z
> **Plan ref:** `contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md`
> **Plan task:** §3 Phase 1 Task 1.2 (per-venue on-chain audit)
> **Spec sha pin:** `4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea` (v1.3)

## §1 — Per-venue completion summary

Total venues: **13**
- `pass`: **3**
- `marginal`: **1**
- `halt`: **9**

| venue_id | role | network | event_count | feasibility_v1 | typed_exception |
|---|---|---|---|---|---|
| `mento_v3_router_mento_router_fork_of_aerodrome_velodrome_celo` | router | celo-mainnet | 0 | halt | Stage2PathBSqdNetworkCoverageInsufficient |
| `mento_v3_fpmm_usdc_usdm_pool_celo` | pool | celo-mainnet | 0 | halt | Stage2PathBMentoUSDmCOPmPoolDoesNotExist |
| `mento_v3_fpmm_usdt_usdm_pool_celo` | pool | celo-mainnet | 0 | halt | Stage2PathBSqdNetworkCoverageInsufficient |
| `mento_v3_fpmm_axlusdc_usdm_pool_celo` | pool | celo-mainnet | 0 | halt | Stage2PathBSqdNetworkCoverageInsufficient |
| `mento_v3_fpmm_gbpm_usdm_pool_celo` | pool | celo-mainnet | 0 | halt | Stage2PathBSqdNetworkCoverageInsufficient |
| `mento_v2_copm_stabletokencopproxy_celo` | token | celo-mainnet | 0 | halt | Stage2PathBSqdNetworkCoverageInsufficient |
| `mento_v2_usdm_stabletokenproxy_formerly_cusd_celo` | token | celo-mainnet | 1710650 | pass | — |
| `mento_v2_bipoolmanager_bipoolmanagerproxy_celo` | factory | celo-mainnet | 60011 | pass | — |
| `mento_v2_broker_celo` | router | celo-mainnet | 161381 | pass | — |
| `uniswap_v3_factory_celo_celo` | factory | celo-mainnet | 20 | marginal | — |
| `uniswap_v3_swaprouter02_celo_celo` | router | celo-mainnet | 0 | halt | Stage2PathBSqdNetworkCoverageInsufficient |
| `panoptic_factory_ethereum_mainnet_ethereum` | factory | ethereum-mainnet | 0 | halt | Stage2PathBSqdNetworkCoverageInsufficient |
| `panoptic_semifungiblepositionmanager_sfpm_ethereum_mainnet_ethereum` | factory | ethereum-mainnet | 0 | halt | Stage2PathBSqdNetworkCoverageInsufficient |


## §2 — Aggregate burst-rate compliance

- **Sample window (Celo):** blocks `20635912` to `61000848`
- **Sample window (Ethereum):** blocks `17817450` to `24559982`
- **Audit block (Celo):** `65915058`
- **Audit block (Ethereum):** `25017514`
- **Total SQD queries:** 170
- **Peak SQD req/sec:** 3.74 (cap = 5/sec sustained per spec §5.A)
- **Total Alchemy CU consumed (this run):** 0 / 30 000 000 monthly cap (~0.0000%)
- **Peak Alchemy req/sec:** 0 (cap = 25/sec)
- **Public RPC calls (Celo + Ethereum):** 0
- **Dune credits consumed:** 0 (Task 1.2 did not exercise Dune; reserved for Task 1.3 sanity-check if needed)

## §3 — Typed-exception firings (HALT-and-surface, per dispatch brief + spec §6)

- **Stage2PathBSqdNetworkCoverageInsufficient** — see venue-level `feasibility_notes` in `audit_metrics_raw.json` for the firing context.
- **Stage2PathBMentoUSDmCOPmPoolDoesNotExist** — see venue-level `feasibility_notes` in `audit_metrics_raw.json` for the firing context.

Per dispatch brief: HALT-and-surface, NOT auto-pivot. Awaiting orchestrator adjudication. Per `feedback_pathological_halt_anti_fishing_checkpoint`, each typed-exception firing requires (a) disposition memo with ≥3 user-enumerated pivots from spec §6 pivot lists, (b) user adjudication, (c) CORRECTIONS-block in plan revision if pivot lands, (d) 3-way review of CORRECTIONS revision.


## §4 — Notable findings per venue

### `mento_v3_router_mento_router_fork_of_aerodrome_velodrome_celo` (0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6)

- **role / venue_kind:** router / mento_broker
- **network:** celo-mainnet
- **event_count (sample window):** 0
- **feasibility_v1:** halt
- **feasibility_notes:** Zero events from SQD over 6 chunks (20635912-29635911); contract verified deployed (code_len=26464). If venue has confirmed on-chain activity per Celoscan, this fires Stage2PathBSqdNetworkCoverageInsufficient.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 0 events`
  - `chunk 22135912-23635911: 0 events`
  - `chunk 23635912-25135911: 0 events`

### `mento_v3_fpmm_usdc_usdm_pool_celo` (0x462fe04b4FD719Cbd04C0310365D421D02AaA19E)

- **role / venue_kind:** pool / mento_fpmm
- **network:** celo-mainnet
- **event_count (sample window):** 0
- **feasibility_v1:** halt
- **feasibility_notes:** Mento V3 USDC/USDm FPMM has only 0 events (sample window). Spec §6 Stage2PathBMentoUSDmCOPmPoolDoesNotExist fires (REFRAMED v1.4 to trigger on USDm/cUSD substrate). Pivot path per spec §6 line 1034-1036: fall back to Mento V2 BiPool USDm/COPm exchange ID via BiPool manager.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 0 events`
  - `chunk 22135912-23635911: 0 events`
  - `chunk 23635912-25135911: 0 events`

### `mento_v3_fpmm_usdt_usdm_pool_celo` (0x0FEBa760d93423D127DE1B6ABECdB60E5253228D)

- **role / venue_kind:** pool / mento_fpmm
- **network:** celo-mainnet
- **event_count (sample window):** 0
- **feasibility_v1:** halt
- **feasibility_notes:** Zero events from SQD over 6 chunks (20635912-29635911); contract verified deployed (code_len=4288). If venue has confirmed on-chain activity per Celoscan, this fires Stage2PathBSqdNetworkCoverageInsufficient.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 0 events`
  - `chunk 22135912-23635911: 0 events`
  - `chunk 23635912-25135911: 0 events`

### `mento_v3_fpmm_axlusdc_usdm_pool_celo` (0xb285d4C7133d6f27BfB29224fb0D22E7EC3ddD2D)

- **role / venue_kind:** pool / mento_fpmm
- **network:** celo-mainnet
- **event_count (sample window):** 0
- **feasibility_v1:** halt
- **feasibility_notes:** Zero events from SQD over 6 chunks (20635912-29635911); contract verified deployed (code_len=4288). If venue has confirmed on-chain activity per Celoscan, this fires Stage2PathBSqdNetworkCoverageInsufficient.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 0 events`
  - `chunk 22135912-23635911: 0 events`
  - `chunk 23635912-25135911: 0 events`

### `mento_v3_fpmm_gbpm_usdm_pool_celo` (0x8C0014afe032E4574481D8934504100bF23fCB56)

- **role / venue_kind:** pool / mento_fpmm
- **network:** celo-mainnet
- **event_count (sample window):** 0
- **feasibility_v1:** halt
- **feasibility_notes:** Zero events from SQD over 6 chunks (20635912-29635911); contract verified deployed (code_len=4288). If venue has confirmed on-chain activity per Celoscan, this fires Stage2PathBSqdNetworkCoverageInsufficient.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 0 events`
  - `chunk 22135912-23635911: 0 events`
  - `chunk 23635912-25135911: 0 events`

### `mento_v2_copm_stabletokencopproxy_celo` (0x8A567e2aE79CA692Bd748aB832081C45de4041eA)

- **role / venue_kind:** token / mento_fpmm
- **network:** celo-mainnet
- **event_count (sample window):** 0
- **feasibility_v1:** halt
- **feasibility_notes:** Zero events from SQD over 6 chunks (20635912-29635911); contract verified deployed (code_len=4824). If venue has confirmed on-chain activity per Celoscan, this fires Stage2PathBSqdNetworkCoverageInsufficient.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 0 events`
  - `chunk 22135912-23635911: 0 events`
  - `chunk 23635912-25135911: 0 events`

### `mento_v2_usdm_stabletokenproxy_formerly_cusd_celo` (0x765DE816845861e75A25fCA122bb6898B8B1282a)

- **role / venue_kind:** token / mento_fpmm
- **network:** celo-mainnet
- **event_count (sample window):** 1710650
- **first_event_block / last_event_block:** 20635914 / 28138959
- **feasibility_v1:** pass
- **feasibility_notes:** 1710650 events over 6 chunks (window 20635912-29635911); first_blk=20635914, last_blk=28138959; primary source SQD Network.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 105140 events`
  - `chunk 22135912-23635911: 207164 events`
  - `chunk 23635912-25135911: 126137 events`

### `mento_v2_bipoolmanager_bipoolmanagerproxy_celo` (0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901)

- **role / venue_kind:** factory / mento_v2_bipool
- **network:** celo-mainnet
- **event_count (sample window):** 60011
- **first_event_block / last_event_block:** 20635933 / 28171420
- **feasibility_v1:** pass
- **feasibility_notes:** 60011 events over 6 chunks (window 20635912-29635911); first_blk=20635933, last_blk=28171420; primary source SQD Network.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 14745 events`
  - `chunk 22135912-23635911: 18659 events`
  - `chunk 23635912-25135911: 9750 events`

### `mento_v2_broker_celo` (0x777A8255cA72412f0d706dc03C9D1987306B4CaD)

- **role / venue_kind:** router / mento_broker
- **network:** celo-mainnet
- **event_count (sample window):** 161381
- **first_event_block / last_event_block:** 20635932 / 28171427
- **feasibility_v1:** pass
- **feasibility_notes:** 161381 events over 6 chunks (window 20635912-29635911); first_blk=20635932, last_blk=28171427; primary source SQD Network.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 19197 events`
  - `chunk 22135912-23635911: 74175 events`
  - `chunk 23635912-25135911: 16363 events`

### `uniswap_v3_factory_celo_celo` (0xAfE208a311B21f13EF87E33A90049fC17A7acDEc)

- **role / venue_kind:** factory / uniswap_v3_pool
- **network:** celo-mainnet
- **event_count (sample window):** 20
- **first_event_block / last_event_block:** 20717779 / 26831948
- **feasibility_v1:** marginal
- **feasibility_notes:** Only 20 events over 6 chunks; below the 100-event floor for Stage2PathBSqdNetworkCoverageInsufficient. Sample coverage may be insufficient for downstream substrate work.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 5 events`
  - `chunk 22135912-23635911: 2 events`
  - `chunk 23635912-25135911: 3 events`

### `uniswap_v3_swaprouter02_celo_celo` (0x5615CDAb10dc425a742d643d949a7F474C01abc4)

- **role / venue_kind:** router / uniswap_v3_pool
- **network:** celo-mainnet
- **event_count (sample window):** 0
- **feasibility_v1:** halt
- **feasibility_notes:** Zero events from SQD over 6 chunks (20635912-29635911); contract verified deployed (code_len=48996). If venue has confirmed on-chain activity per Celoscan, this fires Stage2PathBSqdNetworkCoverageInsufficient.
- **diagnostic_log (first 3 entries):**
  - `chunk 20635912-22135911: 0 events`
  - `chunk 22135912-23635911: 0 events`
  - `chunk 23635912-25135911: 0 events`

### `panoptic_factory_ethereum_mainnet_ethereum` (0x00000000000142658e41964CBD294a7f731712fD)

- **role / venue_kind:** factory / panoptic_factory
- **network:** ethereum-mainnet
- **event_count (sample window):** 0
- **feasibility_v1:** halt
- **feasibility_notes:** Zero events from SQD over 5 chunks (17817450-24559982); contract verified deployed (code_len=48664). If venue has confirmed on-chain activity per Celoscan, this fires Stage2PathBSqdNetworkCoverageInsufficient.
- **diagnostic_log (first 3 entries):**
  - `chunk 17817450-19317449: 0 events`
  - `chunk 19317450-20817449: 0 events`
  - `chunk 20817450-22317449: 0 events`

### `panoptic_semifungiblepositionmanager_sfpm_ethereum_mainnet_ethereum` (0x0000000000014BE53913184E1B4585A059Ab0841)

- **role / venue_kind:** factory / panoptic_factory
- **network:** ethereum-mainnet
- **event_count (sample window):** 0
- **feasibility_v1:** halt
- **feasibility_notes:** Zero events from SQD over 5 chunks (17817450-24559982); contract verified deployed (code_len=41340). If venue has confirmed on-chain activity per Celoscan, this fires Stage2PathBSqdNetworkCoverageInsufficient.
- **diagnostic_log (first 3 entries):**
  - `chunk 17817450-19317449: 0 events`
  - `chunk 19317450-20817449: 0 events`
  - `chunk 20817450-22317449: 0 events`



## §5 — Path A files untouched verification

This dispatch touches ONLY:
- `contracts/.scratch/pair-d-stage-2-B/v0/audit_metrics_raw.json`
- `contracts/.scratch/pair-d-stage-2-B/v0/DATA_PROVENANCE.md` (appended §2 entry 6)
- `contracts/.scratch/path-b-stage-2/phase-0/burst_rate_log.csv` (appended)
- `contracts/.scratch/path-b-stage-2/phase-1/task_1_2_dispatch_disposition.md` (this file)
- `contracts/.scratch/path-b-stage-2/phase-1/scripts/run_task_1_2_audit.py` (driver)

Path A files (`contracts/notebooks/abrigo_y3_x_d/`, `contracts/.scratch/2026-04-25-task110-rev2-*`,
etc.) are NOT modified per concurrent-agent serialization discipline.

## §6 — Hand-off to Task 1.3

Task 1.3 (parquet emission per spec §4.0 schema) consumes `audit_metrics_raw.json` and
emits the three normative parquet artifacts (`audit_summary.parquet`,
`address_inventory.parquet`, `event_inventory.parquet`) plus the v1.4-additive
`mento_swap_flow_inventory.parquet` (Task 1.3.b). The diagnostic_log and typed_exception
fields in `audit_metrics_raw.json` are STAGING ONLY and are stripped at parquet emit
to honor the spec §4.0 normative column set.

For halt/marginal venues: Task 1.3 SHOULD emit them in `audit_summary.parquet` with
`feasibility_v1 ∈ {'halt', 'marginal'}` and populated `feasibility_notes` per spec §4.0
(no silent drops, per dispatch brief success criterion).
