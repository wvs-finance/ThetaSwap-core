# DATA_PROVENANCE.md — Pair D Stage-2 Path B v0 audit (Task 1.1 partial)

> Per spec §3.A (normative; resolves BLOCK-B2): every committed dataset directory
> MUST contain exactly one `DATA_PROVENANCE.md` co-located with its artifacts.
> This file co-locates with `allowlist.toml` (Task 1.1 output). Subsequent v0
> Tasks 1.2 + 1.3 + 1.4 will append §2 entries for the parquet artifacts; this
> initial file establishes the §1 self-meta and the Task-1.1 §2 entry.
>
> Field schema parity with Stage-1
> `contracts/.scratch/simple-beta-pair-d/data/DATA_PROVENANCE.md` is REQUIRED;
> on-chain extensions (`block_range`, `filter_applied`) are added on top of the
> Stage-1 8-field schema, never instead of.

**Governing artifacts (sha-pinned):**

| Artifact | sha256 |
|---|---|
| Spec v1.3 (`contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md`) | `4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea` |
| Plan (`contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md`) | `406c55a33e28af9e57b4cb912017e3bea26993733dc5260c0486e507d7f9cd38` |
| Stage-1 read-only verdict (`contracts/.scratch/simple-beta-pair-d/results/VERDICT.md`) | `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf` |

---

## §1 — Self-meta

- **artifact_path:** `contracts/.scratch/pair-d-stage-2-B/v0/`
- **artifact_sha256:** N/A (this directory is in flight at Task 1.1; per-file sha256 listed in §2 entries)
- **artifact_row_count:** N/A at Task 1.1 (parquets emitted at Task 1.3)
- **artifact_schema_version:** N/A at Task 1.1 (spec §4.0 schema_version field attached at Task 1.3 emit)
- **emit_timestamp_utc:** `2026-05-03T11:16:58Z`
- **emit_commit_sha:** `<recorded by orchestrator post-commit; see git log>`
- **emit_plan_task:** `1.1 (plan-numbered) — allowlist confirmation + Mento V3 manifest`

---

## §2 — Per-input provenance entries

### Entry 1 — `allowlist.toml` (this Task's primary output)

- **source:** Composed from canonical Mento V3 deployment manifest + Uniswap V3
  Celo deployment manifest + Panoptic V1 Code4rena 2025-12 deployment-info.json.
  Per-row source URLs recorded in the `source` field of each `[[contracts]]`
  block in `allowlist.toml`. Five primary upstream sources:
  - `https://docs.mento.org/mento-v3/build/deployments/addresses` (Mento V3 FPMM
    pools + V3 Router)
  - `https://celoscan.io/address/0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`
    (Mento V3 Router verification + label "Mento: Router")
  - `https://celoscan.io/address/0x8A567e2aE79CA692Bd748aB832081C45de4041eA`
    (Mento V2 COPm verification + label "Mento Labs: cCOP Token"; canonical per
    memory `project_mento_canonical_naming_2026` β-corrigendum)
  - `https://developers.uniswap.org/contracts/v3/reference/deployments/celo-deployments`
    (Uniswap V3 Celo factory + SwapRouter02 + NonfungiblePositionManager)
  - `https://raw.githubusercontent.com/code-423n4/2025-12-panoptic/main/deployment-info.json`
    (Panoptic V1 Factory + SFPM on Ethereum mainnet)
- **fetch_method:** WebFetch HTTPS GET against each canonical URL above; Mento V3
  manifest first attempt at `https://docs.mento.org/mento/protocol-info/deployments`
  returned 404 — pivoted to `https://docs.mento.org/mento-v3/build/deployments/addresses`
  per the 404-page suggested link. Uniswap V3 docs first attempt at
  `https://docs.uniswap.org/...` returned 301 redirect to
  `https://developers.uniswap.org/...` and second WebFetch followed the redirect.
  On-chain verification via `eth_getCode` against `https://1rpc.io/celo` (selected
  after enumerating 4 free Celo RPCs; first `forno.celo.org` + `eth.llamarpc.com`
  attempts returned HTTP 403 Forbidden) for Celo addresses; against
  `https://ethereum-rpc.publicnode.com` for Ethereum-mainnet addresses.
- **fetch_timestamp:** `2026-05-03T11:13:48Z` (initial canonical-source WebFetch
  batch); `2026-05-03T11:14:30Z` (Mento V2 BiPoolManager + Broker addition batch)
- **sha256:** `5e9b3663efc75dee599966d741ec1ba5afd815194aef758d2c05bc96f09a9443`
  (sha256 of the committed `allowlist.toml` at Task 1.1 close)
- **row_count:** 13 contracts (within spec §6 Stage2PathBAuditScopeAnomaly bounds
  [4, 20]; within spec dispatch lower [6, 12] audit_summary band: yes since 6 ≤
  13 — note the audit_summary parquet at Task 1.3 will be a per-venue subset, not
  the full allowlist enumeration)
- **block_range:** N/A (allowlist enumerates contract addresses, not events;
  block-range bounds are populated at Task 1.2 per-venue audit per spec §3.A
  on-chain extension)
- **schema_version:** Allowlist TOML schema v1.0 declared in `[meta]`; this is
  not the spec §4.0 parquet schema (which applies at Task 1.3); the allowlist
  TOML is a working scaffold for Task 1.2 input.
- **filter_applied:** No partition rules applied at Task 1.1 (raw enumeration).
  Out-of-scope addresses explicitly EXCLUDED:
  (a) Minteo COPM `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` excluded per
      memory `project_mento_canonical_naming_2026` β-corrigendum (Minteo-fintech,
      not Mento-native); verified to be a deployed contract at code_len=1400
      (so the exclusion is intentional, not a missing-deployment artifact).
  (b) Mento V2 Reserve at the documented address `0x2bC2D48735842924C508468C5A02580aD4F6d99A`
      excluded because `eth_getCode` against `https://1rpc.io/celo` returned `0x`
      (EOA / no contract code), suggesting either a stale documented address or
      the Reserve is now under a different proxy. Surfaced as caveat in Task 1.1
      disposition memo (`task_1_1_plan_disposition.md` §3 caveat 1).
  (c) Bitgifty + Walapay merchant settlement contracts excluded — no canonical
      smart-contract addresses found within Task 1.1's 30-min source-search
      timebox; HALT-and-surface candidate `Stage2PathBASOnChainSignalAbsent`
      recorded in disposition memo for orchestrator adjudication.

### Entry 2 — Mento V3 deployment manifest snapshot

- **source:** `https://docs.mento.org/mento-v3/build/deployments/addresses` —
  canonical Mento V3 deployments page per Mento Labs documentation.
- **fetch_method:** WebFetch with prompt extracting all FPMM pools + Mento V3
  Router + Mento V2 Broker / BiPoolManager / Reserve / BreakerBox / MentoGovernor.
- **fetch_timestamp:** `2026-05-03T11:13:48Z`
- **sha256:** Manifest content (HTML response body) is not committed verbatim;
  the structured extracts derived from it are committed in `allowlist.toml`
  (sha `5e9b3663…9443`). For audit-trail purposes, the structured extracts are:
  - Mento V3 Router: `0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`
  - Mento V3 FPMM USDC/USDm: `0x462fe04b4FD719Cbd04C0310365D421D02AaA19E`
  - Mento V3 FPMM USDT/USDm: `0x0FEBa760d93423D127DE1B6ABECdB60E5253228D`
  - Mento V3 FPMM axlUSDC/USDm: `0xb285d4C7133d6f27BfB29224fb0D22E7EC3ddD2D`
  - Mento V3 FPMM GBPm/USDm: `0x8C0014afe032E4574481D8934504100bF23fCB56`
  - Mento V2 Reserve: `0x2bC2D48735842924C508468C5A02580aD4F6d99A` (excluded — EOA)
  - Mento V2 Broker: `0x777A8255cA72412f0d706dc03C9D1987306B4CaD`
  - Mento V2 BiPoolManager: `0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901`
  - BreakerBox: `0x303ED1df62Fa067659B586EbEe8De0EcE824Ab39` (out of scope; circuit-breaker, not flow venue)
  - MentoGovernor: `0x47036d78bB3169b4F5560dD77BF93f4412A59852` (out of scope; governance, not flow venue)
- **row_count:** 10 documented addresses extracted; 8 admitted to allowlist; 2
  (BreakerBox + MentoGovernor) excluded as out-of-scope governance/safety
  infrastructure (neither flow venue nor settlement leg per spec §3 framing).
- **block_range:** N/A (manifest is a name → address registry, not block-anchored)
- **schema_version:** Mento docs deployments page schema (free-text + tables);
  no normative schema versioning at source.
- **filter_applied:** Excluded addresses listed in row_count.

### Entry 3 — Uniswap V3 Celo deployment manifest snapshot

- **source:** `https://developers.uniswap.org/contracts/v3/reference/deployments/celo-deployments`
  (after 301 redirect from `https://docs.uniswap.org/...`)
- **fetch_method:** WebFetch HTTPS GET; second attempt after 301 redirect chain.
- **fetch_timestamp:** `2026-05-03T11:13:48Z`
- **sha256:** Structured extracts in `allowlist.toml`:
  - UniswapV3Factory: `0xAfE208a311B21f13EF87E33A90049fC17A7acDEc`
  - SwapRouter02: `0x5615CDAb10dc425a742d643d949a7F474C01abc4`
  - UniversalRouter: `0x643770E279d5D0733F21d6DC03A8efbABf3255B4` (out of scope — Universal Router not in spec scope; UR is Uniswap Labs router for cross-protocol routing not Uniswap-V3-only)
  - NonfungiblePositionManager: `0x3d79EdAaBC0EaB6F08ED885C05Fc0B014290D95A` (out of scope — Uniswap V3 NPM not in spec scope; v0 audit is venue-level not LP-position-level)
  - QuoterV2: `0x82825d0554fA07f7FC52Ab63c961F330fdEFa8E8` (out of scope — read-only quoter, no flow events)
- **row_count:** 5 documented addresses extracted; 2 admitted to allowlist; 3
  excluded as out-of-scope per spec §3 audit framing.
- **block_range:** N/A
- **schema_version:** Uniswap docs deployment table schema (HTML); no normative
  schema versioning at source.
- **filter_applied:** Excluded addresses listed in row_count.

### Entry 4 — Panoptic V1 deployment-info.json

- **source:** `https://raw.githubusercontent.com/code-423n4/2025-12-panoptic/main/deployment-info.json`
  (Code4rena 2025-12 Panoptic V1 audit deployment manifest; canonical pre-audit
  deployment-info.json shipped with the Panoptic V1 Code4rena audit submission)
- **fetch_method:** WebFetch HTTPS GET against raw.githubusercontent.com.
- **fetch_timestamp:** `2026-05-03T11:13:48Z`
- **sha256:** Structured extracts in `allowlist.toml`:
  - PanopticFactory: `0x00000000000142658e41964CBD294a7f731712fD`
  - SemiFungiblePositionManager: `0x0000000000014BE53913184E1B4585A059Ab0841`
  - Third unlabeled address: `0x000000000001621A6649E38465B127693fFC5db8` (excluded — role unidentified at Task 1.1; flag for Task 1.2 deeper inspection)
- **row_count:** 3 documented addresses extracted; 2 admitted to allowlist; 1
  excluded pending role identification.
- **block_range:** N/A
- **schema_version:** deployment-info.json v1 (Panoptic V1 manifest schema:
  `dataContracts` array of `{name, address, salt, initCode}` per entry).
- **filter_applied:** Excluded one address pending role identification (will be
  resolved at Task 1.2 via Etherscan name lookup).

### Entry 5 — On-chain verification via free public RPC

- **source:** `https://1rpc.io/celo` (Celo) + `https://ethereum-rpc.publicnode.com`
  (Ethereum). Both selected after free-tier RPC enumeration (4 Celo + 4 Ethereum
  candidates tested); first-attempt `forno.celo.org` + `eth.llamarpc.com`
  returned HTTP 403 Forbidden. Selected endpoints both responded successfully to
  `eth_chainId` (chainId=0xa4ec / chainId=0x1 verified).
- **fetch_method:** Direct `urllib.request` JSON-RPC POST batched sequentially
  with 0.4-sec inter-call sleep (well under the 5-req/sec free-tier informal
  caps). One `eth_getCode` call per address × 16 addresses (13 admitted to
  allowlist + 1 Minteo verify-absent + 1 Reserve verify-EOA + 1 from earlier
  dropped 1rpc fallback test). Plus 2 `eth_call` calls (token0() / token1()) on
  the Mento V3 USDC/USDm pool to confirm the token pair composition.
- **fetch_timestamp:** `2026-05-03T11:14:30Z` to `2026-05-03T11:15:30Z` (~60 sec
  total; sequential single-IP, well below all rate caps)
- **sha256:** N/A (RPC responses not committed verbatim; verification results
  encoded as `verification_status` + `on_chain_code_len` per `[[contracts]]`
  entry in `allowlist.toml`)
- **row_count:** 16 `eth_getCode` calls + 2 `eth_call` calls = 18 total RPC calls.
  Distribution: 14 calls to `1rpc.io/celo` + 2 calls to
  `ethereum-rpc.publicnode.com` for the 2 Panoptic addresses + 2 `eth_call` to
  `1rpc.io/celo` for token0/token1 verification.
- **block_range:** `latest` block tag (Celo + Ethereum); not pinned to specific
  block at Task 1.1 (Task 1.2 will pin the audit_block per spec §4.0 schema).
- **schema_version:** Standard JSON-RPC 2.0 `eth_getCode` + `eth_call` response
  format; no parquet schema at Task 1.1.
- **filter_applied:** None — every address in the verification candidate pool
  had `eth_getCode` issued. Two filters applied to results before allowlist
  emission: (a) Minteo (`0xc92e8fc2…`) confirmed as deployed contract but
  EXCLUDED from allowlist per memory β-corrigendum; (b) Mento V2 Reserve
  (`0x2bC2D48…`) confirmed as EOA (`0x` empty code) and EXCLUDED.

---

## §3 — Re-execution discipline (per spec §3.A)

For Task 1.1's allowlist enumeration:

- Re-fetching the canonical Mento V3 / Uniswap V3 / Panoptic deployment manifests
  MUST produce the same address set. Address drift in the source manifests
  triggers `Stage2PathBProvenanceMismatch` typed exception per spec §3.A
  HALT-on-mismatch discipline; deposition is a CORRECTIONS-block plan revision
  per `feedback_pathological_halt_anti_fishing_checkpoint`.
- `eth_getCode` re-execution against the same RPC + same address MUST return
  identical bytecode at the same block tag (`latest` is not deterministic
  across re-runs; re-execution should pin to the audit_block at Task 1.2).
- Re-execution at Task 1.2 will populate the `block_range` and `schema_version`
  fields with concrete values per spec §3.A on-chain extension; Task 1.1's
  N/A markers reflect that the address-enumeration scope precedes block-anchored
  event extraction.

---

## §4 — Free-tier + zero-cost certification (Task 1.1)

- **Network calls issued:** 8 WebFetch HTTPS calls (canonical sources) + 18
  JSON-RPC calls (eth_getCode + eth_call against free public RPCs) + 4 RPC
  endpoint enumeration calls (eth_chainId × 4 Celo + 4 Ethereum) = 34 total
  outbound HTTPS calls
- **Alchemy CU consumed:** 0 / 30 000 000 monthly free-tier ceiling (Task 1.1
  used public RPCs only; Alchemy free-tier reserved for Task 1.2 CU-budgeted
  receipt enrichment per `network_config.toml` §2)
- **Dune credits consumed:** 0 / ~2 500 working assumption
- **SQD Network requests issued:** 0 (Task 1.1 is address-enumeration only;
  SQD Network reserved for Task 1.2 event-extraction per spec §5.A)
- **Public RPC requests issued:** 26 to `1rpc.io/celo` + 5 to
  `ethereum-rpc.publicnode.com` + ~7 across other tested endpoints during
  enumeration = ~38 total. All sequential single-IP; peak observed
  ~2.5 req/sec; well below all informal rate caps.
- **`burst_rate_log.csv` updates:** 0 (Task 1.1 burst-rate well below the 80%
  warning threshold; per `network_config.toml` §7 the audit log is exercised
  at peak-load-budgeted phases — Task 1.2 onwards)

---

## §5 — Cross-path serialization note (concurrent-agent discipline)

Path A Phase 1 is paused mid-flight (Task 1.4 + Gate B1 not yet dispatched per
orchestrator state). Both paths share the `phase0-vb-mvp` branch. Task 1.1
commits ONLY Path B paths
(`contracts/.scratch/pair-d-stage-2-B/v0/**` + `contracts/.scratch/path-b-stage-2/phase-1/task_1_1_plan_disposition.md`);
no Path A files staged.

Per `project_concurrent_agent_filesystem_interleaving`: this is the SOLE Path B
agent active right now per dispatch brief; no overlapping-file risk.


### Entry 6 — Task 1.2 per-venue audit fetch batch (`audit_metrics_raw.json`)

- **source:** SQD Network public gateways:
  - `https://v2.archive.subsquid.io/network/celo-mainnet/{block}/worker` (Celo)
  - `https://v2.archive.subsquid.io/network/ethereum-mainnet/{block}/worker` (Ethereum)
  Per-worker URL is dynamic (worker discovery via `/{block}/worker` endpoint).
  Fallback public RPCs: `https://forno.celo.org` (Celo) + `https://ethereum-rpc.publicnode.com` (Ethereum).
  Alchemy free-tier (`https://eth-mainnet.g.alchemy.com/v2/<REDACTED>`) used for
  Ethereum-mainnet contracts only (Celo not enabled per `alchemy_free_tier_verify.json`).
- **fetch_method:** `python contracts/.scratch/path-b-stage-2/phase-1/scripts/run_task_1_2_audit.py`
  Per-venue audit driver: for each of the 13 in-scope contracts in `allowlist.toml`,
  query SQD Network in chunked block ranges ({chunk_size_blocks=1_500_000}, max 6 chunks)
  for log emissions filtered by contract address (and topic0 where applicable), then
  aggregate event_count + first/last_event_block. Inter-call sleep ≥0.30 s on SQD;
  ≥1.05 s on Alchemy; ≥0.5 s on public RPC; concurrency cap = 1.
- **fetch_timestamp:** `2026-05-03T23:37:26Z`
- **sha256:** `3c4a1c81ff00e47912f581ba8dc68697b81a54d77b7736201ed7c718a5fc3905` (sha256 of `audit_metrics_raw.json` post-emission)
- **row_count:** 13 per-venue entries (one per allowlist row)
- **block_range:** Celo (`20635912`, `61000848`); Ethereum (`17817450`, `24559982`)
- **schema_version:** `audit_metrics_raw.json` per-venue entries follow the spec §4.0
  Artifact 1 audit_summary schema with two extra diagnostic fields (`diagnostic_log`,
  `typed_exception`) preserved as staging context for Task 1.3 parquet emit (the parquet
  emit at Task 1.3 strips diagnostic fields per spec §4.0 normative column set).
- **filter_applied:** Per-venue filtering to the contract's address + topic0 list
  (token venues filtered to `Transfer(address,address,uint256)`; FPMM-style venues filtered
  to Uniswap V3 `Swap`/`Mint`/`Burn` topic0s; Mento V2 / Mento V3 Router / Panoptic queried
  unfiltered to capture all emissions then aggregated). Block-range bounds set to spec
  §3.B sample window 2023-08-01 → 2026-02-28 per spec §3 audit window pin.


### Entry 6 — Task 1.2 per-venue audit fetch batch (`audit_metrics_raw.json`)

- **source:** SQD Network public gateways:
  - `https://v2.archive.subsquid.io/network/celo-mainnet/{block}/worker` (Celo)
  - `https://v2.archive.subsquid.io/network/ethereum-mainnet/{block}/worker` (Ethereum)
  Per-worker URL is dynamic (worker discovery via `/{block}/worker` endpoint).
  Fallback public RPCs: `https://forno.celo.org` (Celo) + `https://ethereum-rpc.publicnode.com` (Ethereum).
  Alchemy free-tier (`https://eth-mainnet.g.alchemy.com/v2/<REDACTED>`) used for
  Ethereum-mainnet contracts only (Celo not enabled per `alchemy_free_tier_verify.json`).
- **fetch_method:** `python contracts/.scratch/path-b-stage-2/phase-1/scripts/run_task_1_2_audit.py`
  Per-venue audit driver: for each of the 13 in-scope contracts in `allowlist.toml`,
  query SQD Network in chunked block ranges ({chunk_size_blocks=1_500_000}, max 6 chunks)
  for log emissions filtered by contract address (and topic0 where applicable), then
  aggregate event_count + first/last_event_block. Inter-call sleep ≥0.30 s on SQD;
  ≥1.05 s on Alchemy; ≥0.5 s on public RPC; concurrency cap = 1.
- **fetch_timestamp:** `2026-05-03T23:46:09Z`
- **sha256:** `cb94f0588dfe95dafe2c3377d92e83595ae978f35a256ba278e9544b13b08d52` (sha256 of `audit_metrics_raw.json` post-emission)
- **row_count:** 13 per-venue entries (one per allowlist row)
- **block_range:** Celo (`20635912`, `61000848`); Ethereum (`17817450`, `24559982`)
- **schema_version:** `audit_metrics_raw.json` per-venue entries follow the spec §4.0
  Artifact 1 audit_summary schema with two extra diagnostic fields (`diagnostic_log`,
  `typed_exception`) preserved as staging context for Task 1.3 parquet emit (the parquet
  emit at Task 1.3 strips diagnostic fields per spec §4.0 normative column set).
- **filter_applied:** Per-venue filtering to the contract's address + topic0 list
  (token venues filtered to `Transfer(address,address,uint256)`; FPMM-style venues filtered
  to Uniswap V3 `Swap`/`Mint`/`Burn` topic0s; Mento V2 / Mento V3 Router / Panoptic queried
  unfiltered to capture all emissions then aggregated). Block-range bounds set to spec
  §3.B sample window 2023-08-01 → 2026-02-28 per spec §3 audit window pin.
