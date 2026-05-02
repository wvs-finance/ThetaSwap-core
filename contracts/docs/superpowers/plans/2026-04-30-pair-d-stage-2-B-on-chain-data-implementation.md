---
plan_path: contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md
plan_version: v1.0
plan_author: Data Engineer dispatch 2026-05-02 (under user-explicit auto-mode authorization per `feedback_proceed_without_asking_auto_mode`)
plan_sha256_v1_0: <to-be-pinned-after-2-wave-verify>
spec_sha256_pin: 4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea
spec_version_pin: v1.3 (CORRECTIONS-γ executed; structural-exposure framing normative)
spec_path: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md
companion_spec_path_path_a: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-A-fork-simulate-spec.md
companion_spec_sha_path_a: 1a4cc6a4 (v1.2.1; cross-path coupling awareness ONLY — Path A is OUT OF SCOPE for this plan)
master_dispatch_brief: contracts/.scratch/2026-04-30-stage-2-m-sketch-dispatch-brief-pair-d.md
internal_ladder: v0 (data-coverage audit) → v1 (CF^a_l reconstruction) → v2 (CF^a_s reconstruction) → v3 (CPO retrospective backtest)
deliverable_framing: structural-exposure characterization (per spec v1.3 CORRECTIONS-γ §1 framing-definition; behavioral demand / WTP is explicitly OUT OF SCOPE — Stage-3 question)
budget_pin: free_tier_only
budget_pin_provenance: spec v1.3 frontmatter (inherited from CORRECTIONS-δ user directive 2026-05-02)
plan_verifier_v1_wave1: pending (Reality Checker; expected to charge against structural-exposure framing fidelity + free-tier-only enforcement + anti-fishing pivot HALT discipline)
plan_verifier_v1_wave2: pending (Workflow Architect; expected to charge against task ordering + dependency-graph correctness + specialist-coverage discipline + 3-way implementation review hooks per phase)
revision_history:
  - v1.0 2026-05-02 initial draft per Data Engineer dispatch grounded in spec v1.3 (sha 4e8905a9...)
    + dispatch brief + Stage-1 plan structural pattern
stage1_pinned_chain:
  pair_d_spec_v1_3_1: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
  panel: 6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf
  primary_ols: d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf
  robustness_pack: 67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904
  verdict: 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf
on_chain_pins_inherited:
  mento_v3_router_celo: "0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6"
  mento_v2_copm_celo: "0x8A567e2aE79CA692Bd748aB832081C45de4041eA"
  mento_v3_fpmm_usdm_copm_pool_celo: "<resolved at v0 audit closure or Stage2PathBMentoUSDmCOPmPoolDoesNotExist HALT>"
  uniswap_v3_factory_celo: "<resolved at v0 audit closure>"
  uniswap_v3_usdc_usdm_pool_celo: "<resolved at v0 audit closure>"
  panoptic_factory_ethereum: "<resolved at v0 audit closure>"
  bitgifty_settlement_celo: "<resolved at v0 audit closure or Stage2PathBASOnChainSignalAbsent HALT>"
  walapay_settlement_celo: "<resolved at v0 audit closure or Stage2PathBASOnChainSignalAbsent HALT>"
push_target: dev (per `feedback_push_origin_not_upstream` — origin = JMSBPP; NEVER upstream/wvs-finance)
---

# Pair D Stage-2 — Path B (On-Chain Data) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Per project convention `feedback_no_code_in_specs_or_plans`, this plan is code-agnostic; implementation specifics are deferred to executor sub-agents per task. Per `feedback_specialized_agents_per_task`, each task names the specialist owner. Per `feedback_strict_tdd`, no implementation lands without a failing test first. Per `feedback_real_data_over_mocks`, tests use real on-chain data; mocks are reserved for HTTP errors that cannot be reproduced.

## §1 — Overview

Path B is the on-chain empirical-validation track for the Pair D Convex Payoff Option (CPO) Stage-2 M-sketch. The Stage-1 Pair D simple-β empirical validation closed PASS 2026-04-28 PM late evening (β_composite = +0.1367, p_one = 1.46×10⁻⁸, robustness 0/4 sign-flips); per the framework's stage-discipline clause the M-sketch step is unblocked, and Path B's job is to confirm — from realized on-chain history alone, with no simulation and no parameter free-fitting — that the two real-world flows the dispatch brief identifies as the CPO's `a_l` (long-σ) supply side and `a_s` (short-σ) demand side actually exhibit the cash-flow shapes the imported convex-payoff framework predicts for them. The Stage-1 sha-pin chain (spec v1.3.1, joint panel, primary OLS, robustness pack, VERDICT.md — all pinned in this plan's frontmatter) is READ-ONLY through Path B; any plan task that would invalidate them is OUT OF SCOPE.

Path B's deliverable IS **structural-exposure characterization** (per spec v1.3 CORRECTIONS-γ §1 framing-definition) — the cash-flow geometry yielding `|Δ^(a_l)|` and `|Δ^(a_s)|` magnitudes in $-notional that the CPO would neutralize on observed transaction flows. Behavioral demand / willingness-to-pay is **explicitly out of Path B's Stage-2 scope**: transaction archaeology cannot infer WTP for an instrument that does not yet exist in the market, because the existing transactions describe equilibrium under an option set in which the CPO is absent, and introducing the CPO would change that option set. WTP is a Stage-3 (deployment) question requiring a different evidence base (deployed pilot, surveyed demand, observed take-up at posted prices) and is the Phase-A.0 stage-drift failure mode the framework's anti-fishing discipline exists to prevent. **Every plan task below produces structural-exposure outputs, not WTP inferences.** Executors implementing this plan MUST keep the deliverable framed as structural-exposure characterization throughout; any drift into WTP-inference language is a methodology error, not a documentation nit.

The plan decomposes the spec's v0 → v1 → v2 → v3 internal ladder into six dependency-ordered phases, each with multiple tasks dispatched to specialist subagents under the trio-checkpoint discipline (`feedback_notebook_trio_checkpoint`) where notebooks are the deliverable, the per-artifact `DATA_PROVENANCE.md` mirror discipline (spec §3.A) where data parquets are the deliverable, and the typed-exception HALT pathway (spec §6) where the data substrate or tooling fails the spec's pre-pinned exit criteria. The free-tier-only budget pin (spec §5 / §5.A; SQD Network primary archive + Alchemy free-tier spot RPC under burst-rate discipline + The Graph subgraphs + Dune ad-hoc SQL + public-RPC consistency-degraded fallback) is enforced in every Phase-1+ task that issues network requests; auto-pivot to paid services is anti-fishing-banned per spec §5.A degradation Step 5. Cross-path coordination with Path A is **DEFAULT INDEPENDENT** per spec §8 + FLAG-B9: the only B → A coupling permitted at Stage-2 is the Phase-2 emission of `r_al_handoff.json` (consumed by Path A v3 if/when it dispatches); A → B coupling at v3 is a convergence-dispatch concern outside this plan's scope.

## §2 — Phase decomposition

The plan is six phases. Phases 0-5 align to the spec's v0 → v3 ladder plus environment scaffolding (Phase 0) and convergence-verdict authoring (Phase 5).

**Phase 0 — Environment scaffolding.** Stand up the Path B working directory (`contracts/.scratch/pair-d-stage-2-B/`) and notebook directory (`contracts/notebooks/pair_d_stage_2_path_b/`); pin Python + DuckDB + Parquet + SQD Network client + Alchemy free-tier client + public-RPC fallback config in `env.py` mirroring the Pair D Stage-1 pattern at `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/env.py`; author the per-artifact `DATA_PROVENANCE.md` template (spec §3.A 8-field schema); pin the spec sha256 in this plan's frontmatter (already done above); commit scaffolding only. No data extraction yet.

**Phase 1 — v0 data-coverage audit.** Audit the fixed-allowlist set of contract addresses (Mento V3 router + USDm/COPm + USDm/cUSD pools, Uniswap V3 Celo USDC/USDm pool, Uniswap V4 Celo PoolManager if deployed, Panoptic factory Ethereum mainnet, Bitgifty + Walapay on-chain settlement contracts) for venue existence, deployment block, first/last event block, event count, cumulative volume USD, TVL snapshot. Emit three Parquet artifacts per spec §4.0 normative schema: `audit_summary.parquet`, `address_inventory.parquet`, `event_inventory.parquet`. Co-locate `DATA_PROVENANCE.md` per spec §3.A. Frontmatter `on_chain_pins` block frozen at v0 closure. Findings memo (1-2 pp) recommending which candidates graduate to v1 with data-availability reasons (NOT result-shaping reasons). Anti-fishing-load-bearing: discovery beyond allowlist requires user-adjudicated typed-exception per FLAG-B7.

**Phase 2 — v1 CF^(a_l) reconstruction.** For each viable pool from Phase 1, extract historical swap events from SQD Network, apply the FLAG-B8 two-layer non-economic-transaction partition (MEV-bot allowlist drop + atomic-arb round-trip drop), compute the FLAG-B1-pinned TWAP-weighted realized fee yield estimator `r_(a_l) = (cumulative LP-fee accrual USD) / (cumulative |ΔP|-weighted swap-volume USD)` regressed via OLS with HAC SE. Bin daily-UTC primary; weekly aggregation as standard derivation (FLAG-B3). Reference price source per FLAG-B4 ladder: Mento V3 FPMM USDm/COPm pool spot at daily-bin close-tick → Uniswap V3 USDC/USDm Celo pool spot → Banrep TRM daily series; per-row `price_source` column records partition. Emit per-pool empirical `CF^(a_l)` daily-binned series normalized to the Pair D 2015-2026 window, qualitative shape-check chart against `Σ r·|FX_t − FX_{t-1}|`, and `r_al_handoff.json` per FLAG-B9 schema (B → A coupling artifact). Co-locate `DATA_PROVENANCE.md` per §3.A. Findings memo recommending whether Phase 3 proceeds or v1 alone provides sufficient empirical defensibility for the M-sketch supply-side leg.

**Phase 3 — v2 CF^(a_s) reconstruction.** Harder rung; most likely HALT site per spec §6 `Stage2PathBASOnChainSignalAbsent` typed exception. Attempt to extract the on-chain settlement-leg `Transfer` events (FLAG-B2: merchant-side local-stable Transfer, NOT user-side funding Transfer) for the top a_s candidates from dispatch brief §5 (Bitgifty bill-pay + airtime/data + Walapay cross-currency reels). Estimate fixed-obligation turnover plus realized FX-path cost (`Σ q_t / (X/Y)_t` term from the framework's a_s cash-flow definition). Reconcile against v1 at monthly cadence (FLAG-B5; `CF^(a_l)_t − CF^(a_s)_t` per calendar month overlap of v1 and v2 sample windows + cumulative-delta series). HALT-disposition per spec §6 if on-chain fingerprint too abstracted: PROCEED-without-v2-`CF^(a_s)` is pre-authorized — Path B graduates to Phase 4 with v1 alone as empirical anchor and findings memo records the asymmetry; the framework's `Δ^(a_s) < 0` shape can be argued symmetrically from `Δ^(a_l) > 0` plus the framework derivation. Co-locate `DATA_PROVENANCE.md` per §3.A.

**Phase 4 — v3 CPO retrospective backtest.** Replay the Pair D 2015-2026 window of realized COP/USD σ-paths through a theoretical `Π(σ_T) ≈ K̂·σ_T` replication using empirical `r_(a_l)` from Phase 2 and (if available) empirical `B_T` calibration from Phase 3. The σ_T input is **realized monthly log-return-squared from Stage-1 Pair D's COP/USD series** (FLAG-B6); implied vol is rejected as primary because no historical COP/USD option-market depth exists. Compute realized CPO P&L for both legs across the sample. Emit realized P&L envelope characterized by mean, SD, full quantile vector, max drawdown, plus regime-conditional decomposition keyed to the four regimes RC FLAG #6 identified (post-2014 oil shock, COVID, Fed tightening, normalcy). Calibration-handoff packet to Path A v3 ready (includes `r_al_handoff.json` already emitted at Phase-2 close + v3 envelope JSON). Co-locate `DATA_PROVENANCE.md` per §3.A.

**Phase 5 — Convergence + verdict authoring.** Synthesize the v0 → v3 outputs into a single structural-exposure characterization memo. Quantify `|Δ^(a_l)|` and `|Δ^(a_s)|` magnitudes in $-notional that the CPO would neutralize on observed transaction flows. Draft `MEMO.md` + machine-readable `gate_verdict.json`. 3-way implementation review per `feedback_implementation_review_agents` (Code Reviewer + Reality Checker + Senior Developer; Data Engineer for fixes). Surface to user via `DISPOSITION.md`. CLAUDE.md Active iteration block update under 2-wave verify per `feedback_two_wave_doc_verification`.

## §3 — Tasks per phase

> **Task numbering:** N.M where N = phase number, M = task within phase. Each task lists Goal, Inputs, Owner, Outputs, Success criteria, Dependencies, Typed-exception triggers from spec §6 that may fire. Per `feedback_specialized_agents_per_task` every task names a specialist owner.

### Phase 0 — Environment scaffolding

#### Task 0.1: Pin spec sha256 in this plan + verify spec immutability

**Goal:** Confirm spec v1.3 is committed, compute its sha256, pin in this plan's frontmatter; verify spec is unchanged from the dispatch reference (sha pin in plan frontmatter `spec_sha256_pin` field).

**Inputs:**
- spec at `contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md` (sha 4e8905a9... from plan frontmatter)

**Owner:** Foreground Orchestrator (no specialist dispatch — verification only)

**Outputs:**
- Plan frontmatter `spec_sha256_pin` field confirmed match
- Optionally a `provenance_note.md` in the working directory recording the sha-verification timestamp

**Success criteria:**
- Plan frontmatter sha matches the live spec file sha
- Spec immutability confirmed (no commits between dispatch and Phase 0 execution that touch the spec file)

**Dependencies:** none

**Typed-exception triggers:** none expected at this stage; if sha mismatch surfaces, HALT and surface to user (spec was modified between dispatch and execution; potential coordination issue with concurrent agent per memory `project_concurrent_agent_filesystem_interleaving`).

#### Task 0.2: Stand up Path B working directory + notebook directory

**Goal:** Create the Path B file scaffold mirroring the Pair D Stage-1 pattern.

**Inputs:**
- Pair D Stage-1 reference: `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/env.py` (parents-fix landed at HEAD `865402c2c`)
- Spec §4.0 normative schema (artifact paths)
- Spec §5 tooling stack (Jupyter + pandas + statsmodels + sympy + DuckDB + Parquet)

**Owner:** Data Engineer

**Outputs:**
- Directory: `contracts/.scratch/pair-d-stage-2-B/`
- Subdirectories: `v0/`, `v1/`, `v2/`, `v3/` (each will host parquets + DATA_PROVENANCE.md)
- Directory: `contracts/notebooks/pair_d_stage_2_path_b/`
- File: `contracts/notebooks/pair_d_stage_2_path_b/env.py` (Pair D pattern; paths point to Path B working directory; pinned dependencies: pandas, statsmodels, sympy, duckdb, pyarrow, requests, alchemy-sdk-py-equivalent OR raw HTTPS client, optional eth-utils for address checksumming)
- File: `contracts/notebooks/pair_d_stage_2_path_b/references.bib` (Mento V3 docs URL; Subsquid SQD Network docs URL; Alchemy free-tier pricing URL; Pair D Stage-1 spec sha-pin chain; this plan sha-pin; spec sha-pin)
- File: `contracts/notebooks/pair_d_stage_2_path_b/DATA_PROVENANCE_TEMPLATE.md` (8-field template per spec §3.A: source, fetch_method, fetch_timestamp, sha256, row_count, block_range, schema_version, filter_applied)
- Notebook skeletons (NO content yet, just header + section markers): `notebooks/01_v0_audit.ipynb`, `02_v1_cf_al.ipynb`, `03_v2_cf_as.ipynb`, `04_v3_backtest.ipynb`, `05_convergence_memo.ipynb`

**Success criteria:**
- All directories + files exist at the specified paths
- `env.py` paths-fix verified working (import test from a fresh Python session)
- `DATA_PROVENANCE_TEMPLATE.md` schema parity with Stage-1 Pair D's `DATA_PROVENANCE.md` (field names + dtypes match)

**Dependencies:** Task 0.1

**Typed-exception triggers:** none expected; filesystem errors HALT-and-surface.

#### Task 0.3: Pin free-tier-only network configuration

**Goal:** Codify the spec §5 free-tier-only tooling stack as an executable configuration artifact (NOT executable code per `feedback_no_code_in_specs_or_plans` — a config file is permissible, code is not).

**Inputs:**
- Spec §5 tooling stack
- Spec §5.A burst-rate discipline (Alchemy ≤25 req/sec, ≤500 CU/sec; SQD ≤5 req/sec; Dune ≤15 rpm low-limit + 40 rpm high-limit)
- Spec §6 typed exceptions (rate-limit + monthly-CU + public-RPC consistency)

**Owner:** Data Engineer

**Outputs:**
- File: `contracts/notebooks/pair_d_stage_2_path_b/network_config.toml` (or equivalent declarative config — TOML / YAML / JSON; NOT Python) recording:
  - SQD Network gateway URLs (Celo + Ethereum mainnet)
  - Alchemy free-tier endpoint pattern (with `<API_KEY>` placeholder; key sourced from environment variable, not committed)
  - Public RPC fallback URLs (forno.celo.org; eth.llamarpc.com; rpc.ankr.com/eth)
  - Rate-limit caps per source (req/sec, CU/sec, rpm) per spec §5.A
  - Inter-call sleep defaults (≥250 ms for SQD; ≥1 sec inter-batch for Alchemy receipt enrichment in 25-receipt windows)
  - Concurrency cap = 1 per source per spec §5.A
- File: `contracts/notebooks/pair_d_stage_2_path_b/.env.template` (placeholder for `ALCHEMY_API_KEY` — NEVER commit the actual key per `feedback_real_data_over_mocks` security caveat)

**Success criteria:**
- Config file parses cleanly via the chosen format's standard library
- All caps from spec §5.A reflected verbatim
- `.env.template` documents which secrets must be supplied (without leaking them)

**Dependencies:** Task 0.2

**Typed-exception triggers:** none at config-write time; the rate-limit + monthly-CU + public-RPC exceptions fire only at network-call time in Phase 1+.

#### Task 0.4: Pre-execution 2-wave plan verification HALT

**Goal:** Per `feedback_two_wave_doc_verification`, every write to `contracts/docs/superpowers/plans/` must run RC + purpose-matched specialist (Workflow Architect for plans) IN PARALLEL before commit. This task is the gate for the plan itself.

**Inputs:** This plan file (`contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md`)

**Owner:** Foreground Orchestrator dispatches; Reality Checker (Wave 1) + Workflow Architect (Wave 2) execute in parallel.

**Outputs:**
- Reality Checker verdict + defect list (if any)
- Workflow Architect verdict + defect list (if any)
- Integrated plan revision (if defects surfaced) with `plan_verifier_v1_wave1` + `plan_verifier_v1_wave2` frontmatter fields populated

**Success criteria:**
- Both verifiers return PASS or PASS-WITH-REVISIONS
- Any BLOCK-severity defect HALTS commit and re-dispatches; PASS-WITH-REVISIONS proceeds with integration
- Spec sha256 unchanged after verification (verification reads spec, never modifies)

**Dependencies:** Tasks 0.1, 0.2, 0.3 complete (so verifiers see the full scaffold context)

**Typed-exception triggers:** none defined in spec §6 for plan-verification failures; failure mode is conventional defect-list HALT.

### Phase 1 — v0 data-coverage audit

> **Sequential within phase:** Tasks 1.1 → 1.2 → 1.3 → 1.4 are dependency-chained (allowlist confirmation → on-chain audit per venue → schema-conformant Parquet emission → 3-way review). Task 1.5 is the phase-close gate.

#### Task 1.1: Confirm fixed allowlist + Mento V3 deployment manifest

**Goal:** Verify the spec's `on_chain_pins` allowlist is current as of v0 entry; pull the Mento V3 deployment manifest to enumerate all in-scope contract addresses (per FLAG-B7, discovery beyond allowlist requires typed-exception).

**Inputs:**
- Spec frontmatter `on_chain_pins` block
- Mento V3 deployment manifest (canonical source: Mento Labs GitHub or Celo block-explorer-verified reference)
- Memory: `project_no_mento_carbon_protocol_integration` (Mento V3 deployment manifest has zero Carbon/Bancor references — informs in-scope contract surface)
- Memory: `project_mento_canonical_naming_2026` β-corrigendum (`0xc92e8fc2…` is Minteo-fintech, OUT of scope; canonical Mento-native COPm = `0x8A567e2aE79CA692Bd748aB832081C45de4041eA`)

**Owner:** Data Engineer

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v0/allowlist.toml` enumerating all in-scope contract addresses with role labels (router, factory, pool, token, fee_collector, merchant, mev_bot proxy, other) and network attribution (celo-mainnet vs ethereum-mainnet)
- Section in `DATA_PROVENANCE.md` recording manifest source URL + fetch_timestamp + manifest sha256

**Success criteria:**
- Allowlist contains ≥6 contracts (lower bound triggers `Stage2PathBAuditScopeAnomaly` per spec §4.0)
- Allowlist contains ≤20 contracts (upper bound triggers same exception)
- Mento V2 COPM canonical address `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` present; Minteo-fintech `0xc92e8fc2…` ABSENT (memory β-corrigendum)
- All addresses 0x-prefixed checksummed

**Dependencies:** Phase 0 complete

**Typed-exception triggers:**
- `Stage2PathBAuditScopeAnomaly` if allowlist row count violates 4-20 range
- HALT-and-surface if Mento V3 deployment manifest is unreachable from documented sources (spec §6 has no specific exception for manifest unreachability; treat as user-adjudicated HALT)

#### Task 1.2: Per-venue on-chain audit (parallel within budget)

**Goal:** For each in-scope contract from Task 1.1, query SQD Network + Alchemy free-tier + Celoscan/Etherscan to produce per-venue audit metrics (deployment_block, first_event_block, last_event_block, event_count, cumulative_volume_usd, tvl_usd_snapshot, snapshot_timestamp_utc, audit_block, data_source_primary, feasibility_v1).

**Inputs:**
- `allowlist.toml` from Task 1.1
- `network_config.toml` from Task 0.3 (rate-limit caps + endpoint URLs)
- Spec §4.0 schema for `audit_summary.parquet` (column dtypes + nullability)
- Spec §5.A burst-rate discipline (Alchemy ≤25 req/sec, ≤500 CU/sec; SQD ≤5 req/sec; concurrency cap = 1)
- Spec §5.A v0 audit volume projection (~5000 Alchemy CU + ~50 SQD queries + 0-5 Dune credits)

**Owner:** Data Engineer

**Outputs:**
- Working file: `contracts/.scratch/pair-d-stage-2-B/v0/audit_metrics_raw.json` (one entry per venue with all fields) — staging for the Parquet emission in Task 1.3
- Per-venue cumulative_volume_usd computed from SQD Network swap-event extraction (USD-equivalent via on-chain price at swap time; if reference price unavailable for the swap block, mark cell null with `feasibility_notes` recording the gap)
- Per-venue tvl_usd_snapshot from Alchemy `eth_call` against current pool state at audit_block
- DATA_PROVENANCE.md updates per source (SQD endpoint URL + chunked block-range; Alchemy method + block; Celoscan/Etherscan URL if used for human-readable verification)

**Success criteria:**
- Every venue from allowlist has an entry in `audit_metrics_raw.json` (no silent drops)
- For each venue, either the metrics are populated OR `feasibility_v1` = `halt` with `feasibility_notes` documenting why
- Network-side burst rate stays below caps per `network_config.toml`; per-minute `req_per_sec` + `cu_per_sec` audit log emitted to `contracts/.scratch/pair-d-stage-2-B/v0/burst_rate_log.csv` per spec §5.A
- Provenance discipline: every fetch's `fetch_timestamp`, source URL/contract, and raw-payload sha256 recorded in DATA_PROVENANCE.md before parquet emission

**Dependencies:** Task 1.1

**Typed-exception triggers:**
- `Stage2PathBSqdNetworkCoverageInsufficient` if a venue with confirmed on-chain activity returns zero or fewer-than-100 events from SQD Network
- `Stage2PathBSqdNetworkThrottled` if SQD Network returns rate-limit responses inside its free bounds
- `Stage2PathBAlchemyFreeTierRateLimitExceeded` if Alchemy burst exceeds 25 req/sec or 500 CU/sec rolling-window
- `Stage2PathBAlchemyFreeTierMonthlyCUExceeded` if cumulative Alchemy CU usage in calendar month exceeds 30M cap
- `Stage2PathBPublicRPCConsistencyDegraded` if fallback to public RPC produces inconsistent cross-call data
- `Stage2PathBMentoUSDmCOPmPoolDoesNotExist` if Mento V3 FPMM USDm/COPm pool returns zero events OR fewer than 100 events (pre-pinned floor)

Each typed exception triggers HALT-disposition memo per `feedback_pathological_halt_anti_fishing_checkpoint`: typed exception → disposition memo enumerating ≥3 user-enumerated pivots (sourced from spec §6 pivot lists) → user adjudication → CORRECTIONS-block in plan revision if pivot lands → 3-way review of CORRECTIONS revision. Auto-pivot is anti-fishing-banned.

#### Task 1.3: Emit v0 Parquet artifacts conforming to spec §4.0 schema

**Goal:** Transform `audit_metrics_raw.json` into the three normative Parquet artifacts (`audit_summary.parquet`, `address_inventory.parquet`, `event_inventory.parquet`) with exact column names, dtypes, primary keys, and Snappy compression per spec §4.0.

**Inputs:**
- `audit_metrics_raw.json` from Task 1.2
- Spec §4.0 column dtype + nullability tables for all three artifacts
- Spec §4.0 row-count expectations (audit_summary 6-12 typical; <4 or >20 triggers HALT-review; address_inventory 10-200, <5 triggers HALT-review; event_inventory 2-8 per venue)

**Owner:** Data Engineer

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v0/audit_summary.parquet` (Snappy compressed; schema_version metadata field hashing column-set + dtypes)
- File: `contracts/.scratch/pair-d-stage-2-B/v0/address_inventory.parquet` (Snappy; schema_version metadata)
- File: `contracts/.scratch/pair-d-stage-2-B/v0/event_inventory.parquet` (Snappy; schema_version metadata)
- DATA_PROVENANCE.md final entries: per-artifact `sha256` + `row_count` + `schema_version` + `filter_applied` populated

**Success criteria:**
- Schema parity verified (column names + dtypes + nullability match spec §4.0 exactly; no extra columns; no missing columns)
- Primary-key uniqueness verified (audit_summary unique on `venue_id`; address_inventory unique on `(network, address)`; event_inventory unique on `(venue_id, topic0)`)
- Foreign-key referential integrity verified (address_inventory.venue_id ⊆ audit_summary.venue_id; event_inventory.venue_id ⊆ audit_summary.venue_id)
- Row counts within spec §4.0 expectations OR `Stage2PathBAuditScopeAnomaly` raised
- DATA_PROVENANCE.md schema parity with Stage-1 Pair D template (8-field schema + on-chain extensions `block_range` + `filter_applied`)

**Dependencies:** Task 1.2

**Typed-exception triggers:**
- `Stage2PathBAuditScopeAnomaly` if row counts out of range
- `Stage2PathBProvenanceMismatch` if sha256 of re-execution differs by >0.01% row delta inside frozen block range OR schema_version drift unreconcilable to known new-block additions

#### Task 1.4: TDD test suite for v0 Parquet artifacts

**Goal:** Per `feedback_strict_tdd`, every Phase 1 deliverable must have a failing test written first that the implementation then satisfies. This task is mostly a retrospective TDD compliance — write tests that the artifacts from Task 1.3 must pass.

**Inputs:**
- Three Parquet artifacts from Task 1.3
- Spec §4.0 schema definitions

**Owner:** Data Engineer (test author) + Code Reviewer (verifier)

**Outputs:**
- File: `contracts/notebooks/pair_d_stage_2_path_b/tests/test_v0_artifacts.py` (or equivalent — pytest-style; uses real Parquet files via DuckDB or pandas, NO mocks per `feedback_real_data_over_mocks`)
- Tests covering:
  - Schema parity per artifact (all expected columns present, dtypes match, nullability match)
  - Primary-key uniqueness per artifact
  - Foreign-key referential integrity across artifacts
  - Row-count bounds per spec §4.0
  - sha256 stability (re-read parquet, verify sha matches DATA_PROVENANCE.md entry within ±0.01% row delta)
  - Spec §4.0 `data_source_primary` enum value validation (one of `sqd_network`, `alchemy_free`, `dune`, `the_graph`, `celoscan`, `etherscan` per v1.2.1 correction)

**Success criteria:**
- All tests pass against the Task 1.3 artifacts
- Tests fail (RED) when artifacts are intentionally corrupted (e.g., remove a row, change a dtype, mutate sha) — verify the test suite catches the corruption

**Dependencies:** Task 1.3

**Typed-exception triggers:** none; test failures HALT and re-dispatch Data Engineer to fix.

#### Task 1.5: Phase 1 close — 3-way implementation review + freeze on_chain_pins

**Goal:** Per `feedback_implementation_review_agents`, every phase concludes with Code Reviewer + Reality Checker + Senior Developer review IN PARALLEL. Data Engineer fixes; no Tech Writer at implementation reviews. Update spec frontmatter `on_chain_pins` block freezing the audited addresses (this is the spec's only permitted edit during Path B execution — a frontmatter pin update for resolved-at-v0 fields, NOT a methodology change).

**Inputs:**
- All Phase 1 outputs (allowlist.toml, audit_metrics_raw.json, three Parquets, DATA_PROVENANCE.md, burst_rate_log.csv, test suite)
- Spec frontmatter `on_chain_pins` block (with `<to-be-pinned-at-v0-audit-closure>` placeholders)

**Owner:** Foreground Orchestrator dispatches; Code Reviewer (charge: implementation matches spec §4.0 schema; no silent-test-pass per `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons` 5-instance catalogue; trio-checkpoint citation discipline if notebook cells exist) + Reality Checker (charge: every audit_summary row supported by the underlying SQD/Alchemy fetches in DATA_PROVENANCE.md; no synthesized data; feasibility_v1 verdicts honest) + Senior Developer (charge: production-readiness — could a fresh engineer re-run with only the spec + allowlist + network_config?). Data Engineer is on-call for fixes.

**Outputs:**
- Three reviewer verdicts + defect lists
- Integrated phase-close fixes (if defects)
- Spec frontmatter `on_chain_pins` block updated with concrete addresses for resolved fields (`mento_v3_fpmm_usdm_copm_pool_celo`, `mento_v2_usdm_celo`, `uniswap_v3_factory_celo`, `uniswap_v3_usdc_usdm_pool_celo`, `panoptic_factory_ethereum`, `bitgifty_settlement_celo`, `walapay_settlement_celo`) — NOT a methodology amendment, just resolution of pinned-at-v0-closure fields per spec design
- Findings memo (1-2 pp) at `contracts/.scratch/pair-d-stage-2-B/v0/findings.md` recommending which candidates graduate to Phase 2 with data-availability reasons (NOT result-shaping reasons)
- Commit with `Doc-Verify: code=<CR-id> reality=<RC-id> senior=<SD-id>` trailer

**Success criteria:**
- All three reviewers return PASS or PASS-WITH-REVISIONS
- BLOCK-severity defect from any reviewer HALTS commit and re-dispatches Data Engineer
- Spec frontmatter `on_chain_pins` update contains only address resolutions, no methodology drift; spec sha256 re-computed and pinned in plan frontmatter (this is the only permitted spec-side change during Path B)
- Findings memo cites data-availability reasons exclusively; any result-shaping language flagged by Reality Checker triggers HALT-disposition

**Dependencies:** Task 1.4

**Typed-exception triggers:**
- `Stage2PathBMentoUSDmCOPmPoolDoesNotExist` if v0 confirms Mento V3 FPMM has no USDm/COPm pool OR pool exists with fewer than 100 swap events — spec §6 pre-pinned pivots: (a) check Mento V2 BiPool USDm/COPm legacy pool as supply-side reference; (b) accept cUSD/cEUR or USDC/USDm as σ-pattern proxy with explicit CORRECTIONS-block; (c) reframe Path B around USDm/EURm or GBPm/USDm pools with explicit documentation that the Pair-D-specific COP/USD anchor cannot be reproduced on-chain at the supply side

### Phase 2 — v1 CF^(a_l) reconstruction

> **Trio-checkpoint discipline (NON-NEGOTIABLE per `feedback_notebook_trio_checkpoint`):** Phase 2 deliverables are notebooks. Each notebook authoring step is `(why-markdown → code-cell → interpretation-markdown)` with HALT after each trio for orchestrator review. The 4-part citation block (`feedback_notebook_citation_block`) precedes every test/decision/spec-choice in estimation or sensitivity notebooks: (1) reference / (2) why used / (3) relevance to results / (4) connection to simulator.

#### Task 2.1: Notebook 02 scaffolding — load v0 audit + per-pool extraction prep

**Goal:** Set up notebook `02_v1_cf_al.ipynb` with loaded v0 outputs, per-pool extraction config, and the four-part citation block establishing the FLAG-B1 estimator and FLAG-B4 reference-price ladder.

**Inputs:**
- v0 outputs (`audit_summary.parquet`, `address_inventory.parquet`, `event_inventory.parquet`)
- Spec §3 FLAG-B1 normative `r_(a_l)` estimator definition
- Spec §3 FLAG-B4 reference-price ladder (Mento V3 FPMM → Uniswap V3 Celo USDC/USDm → Banrep TRM)
- Spec §3 FLAG-B3 daily-UTC binning normative
- Spec §3 FLAG-B8 two-layer non-economic-transaction partition rule
- v0 `findings.md` enumerating which pools graduated to Phase 2

**Owner:** Analytics Reporter (notebook author with mandatory trio HALTs)

**Outputs:**
- Notebook `contracts/notebooks/pair_d_stage_2_path_b/notebooks/02_v1_cf_al.ipynb` populated with:
  - Section 0: 4-part citation block per spec §3 FLAG-B1 (reference: imported framework `DRAFT.md`; why used: pinned by spec; relevance to results: drives `r_(a_l)` estimate; connection to simulator: feeds `r_al_handoff.json` for Path A v3 calibration)
  - Section 1 first trio: load v0 outputs + per-pool extraction config (which pools, which block ranges, FLAG-B7 allowlist enforcement)
- Commit notebook 02 scaffolding only

**Success criteria:**
- Notebook opens cleanly; section 0 citation block is complete (4 parts present)
- Section 1 trio HALTs before code execution (orchestrator reviews the why-block before code lands)
- Notebook commit trailer: `Doc-Verify: orchestrator-only-pre-Phase-5 (3-way review deferred to Task 5.2)` per Stage-1 Pair D plan trailer convention

**Dependencies:** Phase 1 close

**Typed-exception triggers:** none at scaffolding stage

#### Task 2.2: Notebook 02 — swap-event bulk extraction per pool (trio-checkpointed)

**Goal:** For each pool that graduated from Phase 1, bulk-extract historical swap events from SQD Network across the maximum-feasible window (Mento V3 deployment block → 2026-02-28; or pool-specific deployment block if later). Apply FLAG-B8 two-layer non-economic-transaction partition before any downstream computation.

**Inputs:**
- Per-pool extraction config from Task 2.1
- Spec §5.A v1 volume projection (~25-75 SQD chunked queries per pool × 1-3 pools; ~500K block chunk size; ≥250 ms inter-call sleep)
- FLAG-B8 layer-1 MEV-bot allowlist (snapshotted at Phase 2 entry from Eigenphi free-tier OR Flashbots `mev-inspect-py` labelled-address sets / LibMEV / zeromev.org per spec §5 paid-escalation note)
- FLAG-B8 layer-2 atomic-arb fingerprint (paired swap-in/swap-out within single tx)

**Owner:** Analytics Reporter (notebook author + trio HALT discipline) supported by Data Engineer for bulk extraction

**Outputs:**
- Per-pool swap-event Parquet at `contracts/.scratch/pair-d-stage-2-B/v1/<pool_slug>_swaps_raw.parquet` (pre-partition)
- Per-pool partitioned swap-event Parquet at `contracts/.scratch/pair-d-stage-2-B/v1/<pool_slug>_swaps_partitioned.parquet` (post-FLAG-B8)
- Audit metadata in `contracts/.scratch/pair-d-stage-2-B/v1/partition_summary.csv`: per-pool dropped-row count + dropped-volume fraction (layer-1 + layer-2)
- DATA_PROVENANCE.md updates: per-pool SQD chunked block-range list + FLAG-B8 layer-1 MEV-bot allowlist source URL + sha256
- Notebook trios:
  - Trio A: bulk extraction (why → code → interpretation reporting raw row count per pool); HALT
  - Trio B: FLAG-B8 layer-1 MEV-bot drop (why → code → interpretation reporting dropped row count + volume); HALT
  - Trio C: FLAG-B8 layer-2 atomic-arb drop (why → code → interpretation reporting dropped row count + volume); HALT

**Success criteria:**
- Per-pool raw row counts match SQD-side claimed counts (cross-check via 3 random block-range spot-checks against alternate source — Celoscan or Alchemy `eth_getLogs`)
- Per-pool partition_summary report meets sanity bounds (typical drop fractions: layer-1 1-15% on Celo per memory `project_carbon_user_arb_partition_rule` analog; layer-2 0.1-2%; outliers >30% trigger HALT-review for FLAG-B8 calibration)
- Network burst rate stays below caps; per-minute audit log emitted
- Trio HALTs occur after each (why, code, interpretation) cycle; orchestrator-reviewed before next trio dispatches

**Dependencies:** Task 2.1

**Typed-exception triggers:**
- `Stage2PathBSqdNetworkThrottled` if SQD bulk extraction hits rate-limit
- `Stage2PathBSqdNetworkCoverageInsufficient` if a pool returns far fewer events than v0 audit projected
- `Stage2PathBAlchemyFreeTierRateLimitExceeded` if cross-check enrichment via Alchemy hits cap
- `Stage2PathBProvenanceMismatch` if re-extraction yields >0.01% row delta inside frozen block range

#### Task 2.3: Notebook 02 — `r_(a_l)` estimation per FLAG-B1 (trio-checkpointed)

**Goal:** Compute the FLAG-B1-pinned TWAP-weighted realized fee yield estimator on the post-partition swap data, per pool. Estimator: numerator = cumulative LP-fee accrual USD; denominator = cumulative |ΔP|-weighted swap-volume USD; OLS regression form on the fee-accrual-on-|ΔP|-volume specification with HAC SE.

**Inputs:**
- Per-pool partitioned swap data from Task 2.2
- Per-pool `Mint`/`Burn` events for fee-accrual computation (extracted via SQD Network in same chunked pull as swaps; if not available locally, re-extract under burst-rate discipline)
- Reference-price source per FLAG-B4 ladder (Mento V3 FPMM USDm/COPm pool spot at daily-bin close-tick → Uniswap V3 USDC/USDm Celo pool spot → Banrep TRM)
- Spec §3 FLAG-B3 daily-UTC binning normative

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- Per-pool LP-fee accrual time series Parquet at `contracts/.scratch/pair-d-stage-2-B/v1/<pool_slug>_lp_fees.parquet` (daily-binned UTC)
- Per-pool |ΔP|-weighted swap-volume time series Parquet at `contracts/.scratch/pair-d-stage-2-B/v1/<pool_slug>_dp_weighted_volume.parquet` (daily-binned UTC)
- Per-pool reference-price time series Parquet at `contracts/.scratch/pair-d-stage-2-B/v1/<pool_slug>_reference_price.parquet` with per-row `price_source` column (FLAG-B4 partition record)
- Per-pool `r_(a_l)` estimate JSON at `contracts/.scratch/pair-d-stage-2-B/v1/<pool_slug>_r_al.json`: `{r_al_point, r_al_hac_se, sample_n, sample_window_start, sample_window_end, source_pool_address, fit_diagnostics}`
- Notebook trios:
  - Trio A: LP-fee accrual reconstruction (why → code → interpretation reporting cumulative fees per pool); HALT
  - Trio B: |ΔP|-weighted volume computation (why → code → interpretation reporting cumulative weighted volume); HALT
  - Trio C: OLS fit + HAC SE (why → code → interpretation reporting `r_(a_l)` point + HAC SE per pool); HALT

**Success criteria:**
- Per-pool `r_(a_l)` estimate is finite, sign-positive (LP fees are positive by construction; sign-negative would indicate methodology error)
- HAC SE is finite and positive
- Sample N matches expected daily-bin count from window
- 4-part citation block preceding the OLS trio cites: (1) FLAG-B1 pin in spec §3; (2) why used = pre-pinned methodology; (3) relevance to results = direct estimator for `r_(a_l)`; (4) connection to simulator = feeds `r_al_handoff.json` for Path A v3 calibration

**Dependencies:** Task 2.2

**Typed-exception triggers:**
- `Stage2PathBALCashFlowContaminated` if observed LP-fee accrual is materially mixed with non-σ-driven incentive emissions (Mento liquidity mining, Uniswap UNI emissions, third-party rewards) — spec §6 pre-pinned pivots: (a) net out incentive emissions and report `r_(a_l)` as fee-only residual; (b) drop contaminated pool and elevate rank-2 candidate; (c) report `r_(a_l)` as confidence interval and pass wider uncertainty into v3
- `Stage2PathBSqdNetworkCoverageInsufficient` if `Mint`/`Burn` events return zero counts on a pool with confirmed swap activity (fee accrual would be unreconstructable)

#### Task 2.4: Notebook 02 — `CF^(a_l)` daily series reconstruction + qualitative shape check (trio-checkpointed)

**Goal:** Compute the per-pool `CF^(a_l)_T = Σ_t r_(a_l) · |(X/Y)_t − (X/Y)_{t-1}|` daily-binned series normalized to the Pair D 2015-2026 window. Generate qualitative shape-check chart against `Σ r·|FX_t − FX_{t-1}|` framework prediction. Sign-and-magnitude pattern only; no goodness-of-fit threshold (no honest threshold exists absent reference baselines per spec §2 v1 Exit).

**Inputs:**
- Per-pool `r_(a_l)` from Task 2.3
- Per-pool reference-price time series from Task 2.3
- Pair D Stage-1 COP/USD series (READ-ONLY; sourced from `contracts/notebooks/fx_vol_cpi_surprise/Colombia/` per spec §3 Stage-1 input)

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- Per-pool `CF^(a_l)` daily series Parquet at `contracts/.scratch/pair-d-stage-2-B/v1/<pool_slug>_cf_al.parquet`
- Per-pool qualitative shape-check chart PNG at `contracts/.scratch/pair-d-stage-2-B/v1/<pool_slug>_shape_check.png`
- Notebook trios:
  - Trio A: per-pool `CF^(a_l)` series construction (why → code → interpretation reporting series mean/SD/quantiles); HALT
  - Trio B: shape-check chart against framework's `Σ r·|FX_t − FX_{t-1}|` prediction (why → code → interpretation reporting qualitative pattern match: same sign? same broad magnitude order?); HALT

**Success criteria:**
- Per-pool `CF^(a_l)` series spans the maximum-feasible overlap with Pair D 2015-2026 window (window-trim forced by Mento V3 deployment block is acceptable per spec §3; window-curation chosen post-data is anti-fishing-banned)
- Shape-check chart generated; qualitative interpretation reports match-or-mismatch as qualitative observation, NOT goodness-of-fit p-value (anti-fishing — no synthetic threshold)

**Dependencies:** Task 2.3

**Typed-exception triggers:** none specific to this task; broader Phase 2 exceptions (`Stage2PathBPublicRPCConsistencyDegraded` if Banrep TRM fallback path engaged and yields inconsistent data) may surface

#### Task 2.5: Emit `r_al_handoff.json` per FLAG-B9 schema (B → A coupling artifact)

**Goal:** Emit the cross-path handoff packet at `contracts/.scratch/pair-d-stage-2-B/v1/r_al_handoff.json` per FLAG-B9 schema. This is the SOLE B → A coupling artifact at Stage-2; consumed by Path A v3 IF/WHEN it dispatches (Path A v3 is OPTIONALLY-coupled to this artifact per Path A spec §12; if Path B v1 has not landed at Path A v3 dispatch, Path A v3 proceeds with GBM baseline only).

**Inputs:**
- Per-pool `r_(a_l)` JSON from Task 2.3 (one per graduated pool)
- Pair D Stage-1 sha-pin chain (joint panel sha for `sha256_of_input_panel` field)
- Spec §3 FLAG-B9 schema: `{r_al_point, r_al_hac_se, sample_n, sample_window, source_pool_address, sha256_of_input_panel}`

**Owner:** Data Engineer

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v1/r_al_handoff.json` with FLAG-B9 schema fields populated
- If multiple pools graduated, one handoff JSON per pool OR a single handoff JSON with array-typed fields (decision pinned at task start by orchestrator; default = one JSON per pool for clarity)
- DATA_PROVENANCE.md update: handoff sha256, generation timestamp, source `r_(a_l)` JSON sha256

**Success criteria:**
- Handoff schema parity with FLAG-B9 spec §3 normative (all six fields present, dtypes correct)
- `sha256_of_input_panel` matches the Stage-1 joint panel sha pinned in this plan's frontmatter (`6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`); mismatch HALTS — Stage-1 pin chain is READ-ONLY through Path B
- `r_al_point` is finite positive; `r_al_hac_se` finite positive; `sample_n` integer ≥ 1
- Handoff is self-contained: a Path A v3 executor reading ONLY this JSON + the Stage-1 panel sha can re-verify the calibration anchor without traversing Path B internals

**Dependencies:** Task 2.4

**Typed-exception triggers:** none specific; if Stage-1 panel sha mismatch detected, HALT-and-surface (potential Stage-1 pin-chain corruption — surface to user, do NOT auto-update)

#### Task 2.6: Phase 2 close — 3-way implementation review

**Goal:** Per `feedback_implementation_review_agents`, Phase 2 close gate. Code Reviewer + Reality Checker + Senior Developer review IN PARALLEL. Data Engineer + Analytics Reporter on-call for fixes.

**Inputs:** All Phase 2 outputs (notebook 02 + per-pool parquets + per-pool charts + r_al_handoff.json + DATA_PROVENANCE.md updates + partition_summary.csv)

**Owner:** Foreground Orchestrator dispatches; Code Reviewer (charge: notebook trios respect 4-part citation block discipline; no silent-test-pass; FLAG-B8 partition correctly applied; OLS HAC SE computed correctly per `statsmodels` HAC convention) + Reality Checker (charge: every `r_(a_l)` estimate supported by underlying SQD/Alchemy data per DATA_PROVENANCE.md; shape-check interpretations honest — no over-claiming or under-claiming the qualitative match; framework FLAG inheritance respected — RC FLAG #1 no causal-channel claims, RC FLAG #6 regime-mix flagged) + Senior Developer (charge: production-readiness — could a fresh engineer re-run the v1 pipeline with only spec + v0 outputs + network_config?)

**Outputs:**
- Three reviewer verdicts + defect lists
- Integrated phase-close fixes (if defects)
- Findings memo at `contracts/.scratch/pair-d-stage-2-B/v1/findings.md` recommending whether Phase 3 proceeds OR v1 alone provides sufficient empirical defensibility for the M-sketch supply-side leg
- Commit with `Doc-Verify: code=<CR-id> reality=<RC-id> senior=<SD-id>` trailer

**Success criteria:**
- All three reviewers PASS or PASS-WITH-REVISIONS
- BLOCK-severity defect from any reviewer HALTS
- Findings memo states Phase 3 disposition (proceed vs v1-alone) with structural-exposure framing exclusively (NO WTP language)

**Dependencies:** Task 2.5

**Typed-exception triggers:** none specific to review; reviewer-flagged drift into WTP-inference language triggers HALT-disposition (anti-fishing-load-bearing — CORRECTIONS-γ framing fidelity is non-negotiable)

### Phase 3 — v2 CF^(a_s) reconstruction

> **Most-likely HALT site per spec §6.** v2 is harder than v1; bill-pay flows are partially abstracted (a Bitgifty / Walapay user pays USD-stable in their wallet and the merchant receives local-stable somewhere downstream, possibly through an off-chain corridor with no usable on-chain fingerprint). The HALT is expected with non-trivial probability and does not invalidate Path B; spec §6 pre-authorizes PROCEED-without-v2-`CF^(a_s)` as the default disposition. This phase's tasks are conditional on v0 confirming Bitgifty / Walapay on-chain footprint per Phase 1 Task 1.5 findings memo.

#### Task 3.1: Conditional execution gate — v0 footprint review

**Goal:** Read Phase 1 findings memo for Bitgifty / Walapay on-chain footprint verdict. If v0 confirmed footprint absent or uninterpretable, HALT Phase 3 and proceed directly to Phase 4 with v1-only anchor. Document the skip in Phase 5 MEMO.md.

**Inputs:**
- Phase 1 `findings.md` (Bitgifty + Walapay on-chain footprint feasibility verdict)

**Owner:** Foreground Orchestrator

**Outputs:**
- Decision artifact: `contracts/.scratch/pair-d-stage-2-B/v2/phase3_gate_decision.md` recording PROCEED vs SKIP with reasoning
- If SKIP: typed-exception HALT pre-emptive memo at `contracts/.scratch/pair-d-stage-2-B/v2/Stage2PathBASOnChainSignalAbsent_premptive.md` per spec §6 pre-pinned disposition (PROCEED-without-v2-`CF^(a_s)` is acceptable; documented explicitly for Phase 4 anchor)
- If PROCEED: Phase 3 Tasks 3.2-3.5 dispatch; if SKIP: Phase 3 closes here

**Success criteria:**
- Decision is grounded in Phase 1 findings; no auto-pivot to PROCEED if Phase 1 flagged absence
- HALT-disposition memo (if SKIP) names ≥3 user-enumerated pivots from spec §6 `Stage2PathBASOnChainSignalAbsent` pivot list: (a) source off-chain Bitgifty / Walapay aggregate volume statistics from publicly available reports as upper-bound proxy (structural-exposure CEILING per CORRECTIONS-γ §6 inline-framing rewrite — NOT a behavioral-demand or WTP estimate); (b) substitute Walapay's published Africa-side cross-currency reels as geography substitute; (c) drop v2 and explicitly scope Path B to supply-side empirical validation only

**Dependencies:** Phase 2 close (Task 2.6)

**Typed-exception triggers:**
- `Stage2PathBASOnChainSignalAbsent` (preemptive issuance if SKIP path taken)

#### Task 3.2: Bill-paid lifecycle event extraction (Bitgifty + Walapay merchant-side Transfers)

**Goal:** Extract on-chain settlement-leg `Transfer` events per FLAG-B2 (merchant-side local-stable Transfer, NOT user-side funding Transfer, NOT off-chain payment-completion confirmation). Per spec §3 FLAG-B2 normative, the funding-leg `Transfer` of USD-stable into the Bitgifty / Walapay router is recorded as a co-observation per-q_t input cost but does NOT alone constitute q_t.

**Inputs:**
- Bitgifty + Walapay router contract addresses (resolved at Phase 1 close in spec frontmatter `on_chain_pins`)
- SQD Network Celo gateway URL + Alchemy free-tier endpoint
- Spec §5.A v2 volume projection (~50-75 SQD chunked queries per router × 2-3 routers; <30K Alchemy CU)

**Owner:** Data Engineer (extraction) + Analytics Reporter (notebook 03 author with trio discipline)

**Outputs:**
- Per-router merchant-side Transfer Parquet at `contracts/.scratch/pair-d-stage-2-B/v2/<router_slug>_settlement_transfers.parquet`
- Per-router funding-leg Transfer Parquet at `contracts/.scratch/pair-d-stage-2-B/v2/<router_slug>_funding_transfers.parquet` (co-observation)
- Per-router merchant-address inventory at `contracts/.scratch/pair-d-stage-2-B/v2/<router_slug>_merchants.parquet`
- DATA_PROVENANCE.md updates per router (SQD chunked block-range list; sha256 per parquet)
- Notebook 03 trios:
  - Trio A: bulk extraction of all router-emitted Transfer events (why → code → interpretation reporting raw row counts); HALT
  - Trio B: FLAG-B2 partition (merchant-side vs funding-side classification by direction-of-flow + token-type) (why → code → interpretation reporting per-class row counts); HALT
  - Trio C: merchant-address inventory + per-merchant turnover summary (why → code → interpretation reporting top-10 merchants by turnover); HALT

**Success criteria:**
- Per-router row counts match SQD-side claimed counts (cross-check via 3 random block-range spot-checks)
- FLAG-B2 partition correctly applied (merchant-side Transfers are local-stable to merchant address; funding-side Transfers are USD-stable to router address; classification rule documented in notebook trio B's why-block)
- Network burst rate stays below caps

**Dependencies:** Task 3.1 (PROCEED path)

**Typed-exception triggers:**
- `Stage2PathBASOnChainSignalAbsent` if extracted Transfer events do not fit the FLAG-B2 q_t observation pattern (e.g., all settlements aggregated into a single batched Transfer with no per-bill granularity, OR settlements occur off-chain via permissioned bridge with no on-chain merchant-side Transfer)
- `Stage2PathBSqdNetworkCoverageInsufficient` if a router with confirmed Phase 1 activity returns zero or fewer-than-100 events
- `Stage2PathBProvenanceMismatch` on re-extraction sha drift

#### Task 3.3: `q_t` series reconstruction + `Σ q_t / (X/Y)_t` realized FX-path cost (trio-checkpointed)

**Goal:** Reconstruct per-router daily-binned `q_t` series from merchant-side Transfers; compute the realized FX-path cost `Σ q_t / (X/Y)_t` per the framework's a_s cash-flow definition. Reference price `(X/Y)_t` per FLAG-B4 ladder (same as v1).

**Inputs:**
- Per-router merchant-side Transfer Parquet from Task 3.2
- Per-router reference-price time series (re-use from v1 `<pool_slug>_reference_price.parquet`; cross-pool source consistency required)
- Spec §3 FLAG-B3 daily-UTC binning normative
- Spec §3 FLAG-B5 monthly reconciliation cadence

**Owner:** Analytics Reporter (notebook 03 author + trio HALT discipline)

**Outputs:**
- Per-router daily `q_t` series Parquet at `contracts/.scratch/pair-d-stage-2-B/v2/<router_slug>_q_t.parquet`
- Per-router daily `q_t / (X/Y)_t` series Parquet at `contracts/.scratch/pair-d-stage-2-B/v2/<router_slug>_q_over_xy.parquet`
- Per-router monthly cumulative `Σ q_t / (X/Y)_t` Parquet at `contracts/.scratch/pair-d-stage-2-B/v2/<router_slug>_cumulative_fx_cost_monthly.parquet`
- Notebook trios:
  - Trio A: daily-binned `q_t` series construction (why → code → interpretation reporting series mean/SD/quantiles); HALT
  - Trio B: per-day `q_t / (X/Y)_t` computation with per-row `price_source` partition recorded (why → code → interpretation reporting per-source breakdown); HALT
  - Trio C: monthly aggregation per FLAG-B5 (why → code → interpretation reporting monthly cumulative); HALT

**Success criteria:**
- Per-router daily `q_t` series spans maximum-feasible overlap with Pair D 2015-2026 window
- Per-row `price_source` recorded; FLAG-B4 ladder respected; downstream consumers can partition by source
- Monthly aggregation conforms to FLAG-B5 (Mon-anchored months OR calendar months — pinned at trio C why-block per Stage-1 plan convention)

**Dependencies:** Task 3.2

**Typed-exception triggers:** none specific; broader Phase 3 exceptions (`Stage2PathBPublicRPCConsistencyDegraded` if Banrep TRM fallback engaged) may surface

#### Task 3.4: `CF^(a_s)` series + Δ-shape vs σ characterization (trio-checkpointed)

**Goal:** Compute per-router `CF^(a_s)` daily series; characterize the realized Δ^(a_s) shape against realized σ in the Pair D 2015-2026 window. Per spec §2 v2 Exit: directional evidence of `Δ^(a_s) < 0` shape against realized σ in the same sample window.

**Inputs:**
- Per-router `q_t / (X/Y)_t` time series from Task 3.3
- Per-router monthly cumulative from Task 3.3
- Pair D Stage-1 COP/USD monthly log-return-squared σ_T series (READ-ONLY from Stage-1)
- Spec §2 v2 Exit normative

**Owner:** Analytics Reporter (notebook 03 author + trio HALT discipline)

**Outputs:**
- Per-router `CF^(a_s)` daily series Parquet at `contracts/.scratch/pair-d-stage-2-B/v2/<router_slug>_cf_as.parquet`
- Per-router Δ^(a_s)-vs-σ shape-check chart PNG at `contracts/.scratch/pair-d-stage-2-B/v2/<router_slug>_delta_as_shape.png`
- Per-router structural-exposure |Δ^(a_s)| in $-notional summary at `contracts/.scratch/pair-d-stage-2-B/v2/<router_slug>_structural_exposure_summary.json` (per CORRECTIONS-γ deliverable framing — characterizes the magnitude the CPO would neutralize on observed transaction flows; explicitly NOT a WTP estimate)
- Notebook trios:
  - Trio A: per-router `CF^(a_s)` daily series (why → code → interpretation reporting series mean/SD/sign); HALT
  - Trio B: Δ^(a_s)-vs-σ chart + interpretation (qualitative direction-of-fit only; no goodness-of-fit threshold per anti-fishing); HALT
  - Trio C: |Δ^(a_s)| $-notional summary (structural-exposure characterization framing; per-router magnitude); HALT

**Success criteria:**
- Per-router `CF^(a_s)` daily series sign-negative on average (framework prediction `Δ^(a_s) < 0`); sign-positive triggers HALT-review
- Δ^(a_s)-vs-σ qualitative shape-check reports as qualitative observation; NO post-hoc threshold tuning (anti-fishing)
- Structural-exposure summary JSON uses structural-exposure framing exclusively; any WTP-implying language triggers HALT-disposition

**Dependencies:** Task 3.3

**Typed-exception triggers:**
- `Stage2PathBASOnChainSignalAbsent` if `CF^(a_s)` series cannot be cleanly reconstructed (e.g., series sign-positive on average, indicating FLAG-B2 partition error — the "merchant-side" classification was wrong, OR the Bitgifty / Walapay flow is structurally not a fixed-local-currency obligation as the framework presumed)
- HALT-disposition: PROCEED-without-v2-`CF^(a_s)` per spec §6 pre-pinned, OR pivot per spec §6 enumerated options

#### Task 3.5: v1 ↔ v2 monthly reconciliation per FLAG-B5

**Goal:** Compute `CF^(a_l)_t − CF^(a_s)_t` per calendar month overlap of v1 and v2 sample windows; emit cumulative-delta series as standard derivation. Per spec §3 FLAG-B5 normative: per-month surfacing required to expose regime-conditional asymmetry (RC FLAG #6 inheritance).

**Inputs:**
- Per-pool `CF^(a_l)` daily series from Task 2.4 (re-aggregated to monthly)
- Per-router `CF^(a_s)` daily series from Task 3.4 (re-aggregated to monthly)
- Spec §3 FLAG-B5 monthly cadence normative

**Owner:** Analytics Reporter (notebook 03 author + trio HALT discipline)

**Outputs:**
- Per-(pool, router) pair monthly reconciliation Parquet at `contracts/.scratch/pair-d-stage-2-B/v2/reconciliation_<pool>_<router>_monthly.parquet`
- Per-pair cumulative-delta series Parquet at `contracts/.scratch/pair-d-stage-2-B/v2/reconciliation_<pool>_<router>_cumulative.parquet`
- Notebook trios:
  - Trio A: monthly aggregation alignment (why → code → interpretation reporting per-month overlap count); HALT
  - Trio B: cumulative-delta series + qualitative interpretation (regime-conditional asymmetry per RC FLAG #6); HALT

**Success criteria:**
- Monthly reconciliation spans maximum-feasible overlap window
- Cumulative-delta series + per-month series both emitted (per FLAG-B5 normative requirement for both forms)
- Regime-conditional asymmetry flagged in interpretation per RC FLAG #6 inheritance

**Dependencies:** Task 3.4 + Task 2.4 (cross-phase dependency)

**Typed-exception triggers:** none specific; reconciliation-stage anomalies (e.g., negative cumulative pre-2020 + positive post-2020 indicating regime shift) are reported as observations, NOT triggers for spec amendment

#### Task 3.6: Phase 3 close — 3-way implementation review

**Goal:** Per `feedback_implementation_review_agents`, Phase 3 close gate.

**Inputs:** All Phase 3 outputs (notebook 03 + per-router parquets + per-router charts + per-router structural-exposure summaries + reconciliation parquets + DATA_PROVENANCE.md updates)

**Owner:** Foreground Orchestrator dispatches; Code Reviewer + Reality Checker + Senior Developer (charges parallel to Task 2.6, with extra Reality Checker emphasis on CORRECTIONS-γ structural-exposure framing fidelity throughout — NO WTP-inference drift). Data Engineer + Analytics Reporter for fixes.

**Outputs:**
- Three reviewer verdicts + defect lists
- Integrated phase-close fixes
- Findings memo at `contracts/.scratch/pair-d-stage-2-B/v2/findings.md` summarizing v2 verdict (success vs HALT-with-PROCEED-without-v2) and recommending Phase 4 disposition
- Commit with `Doc-Verify: code=<CR-id> reality=<RC-id> senior=<SD-id>` trailer

**Success criteria:**
- All three reviewers PASS or PASS-WITH-REVISIONS
- BLOCK-severity defect HALTS
- Findings memo states Phase 4 disposition with structural-exposure framing exclusively

**Dependencies:** Task 3.5 (PROCEED path) OR Task 3.1 SKIP path (in which case Phase 3 close is the SKIP-disposition memo only)

**Typed-exception triggers:** none specific to review

### Phase 4 — v3 CPO retrospective backtest

#### Task 4.1: Notebook 04 scaffolding — load v1 + v2 outputs (trio-checkpointed)

**Goal:** Set up notebook `04_v3_backtest.ipynb` with loaded v1 + v2 outputs (or v1-only if Phase 3 SKIPPED), framework `Π(σ_T) ≈ K̂·σ_T` linearization, and the four-part citation block establishing the FLAG-B6 realized-σ_T input pin and the imported framework's `Δ^(a)` derivation.

**Inputs:**
- v1 outputs: per-pool `CF^(a_l)` series, per-pool `r_(a_l)` JSON, `r_al_handoff.json`
- v2 outputs (if Phase 3 PROCEEDED): per-router `CF^(a_s)` series, per-router structural-exposure summaries, monthly reconciliation
- Pair D Stage-1 COP/USD monthly log-return-squared σ_T series (FLAG-B6 pin)
- Imported CPO framework: `contracts/notes/2026-04-29-macro-markets-draft-import.md`

**Owner:** Analytics Reporter (notebook author with mandatory trio HALTs)

**Outputs:**
- Notebook `contracts/notebooks/pair_d_stage_2_path_b/notebooks/04_v3_backtest.ipynb` populated with:
  - Section 0: 4-part citation block per FLAG-B6 (reference: imported framework Π(σ_T) derivation; why used: pinned by spec; relevance: defines theoretical CPO P&L; connection: feeds calibration-handoff packet for Path A v3)
  - Section 1 first trio: load v1 + v2 outputs + Stage-1 σ_T series + framework constants

**Success criteria:**
- Notebook opens cleanly; section 0 citation block complete (4 parts)
- Section 1 trio HALTs before code execution

**Dependencies:** Phase 2 close + (Phase 3 close OR Phase 3 SKIP)

**Typed-exception triggers:** none at scaffolding

#### Task 4.2: Notebook 04 — Π(σ_T) replay + per-month realized P&L (trio-checkpointed)

**Goal:** Replay the Pair D 2015-2026 window of realized COP/USD σ-paths through `Π(σ_T) ≈ K̂·σ_T` using the empirical `r_(a_l)` from Phase 2 and (if available) empirical `B_T` calibration from Phase 3. Compute realized CPO P&L for both legs per month across the sample.

**Inputs:**
- Notebook 04 from Task 4.1 (loaded inputs)
- Spec §2 v3 normative + FLAG-B6 normative

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- Per-month realized CPO P&L Parquet at `contracts/.scratch/pair-d-stage-2-B/v3/cpo_pnl_monthly.parquet` with columns: `month_start`, `realized_sigma_T`, `K_hat`, `Pi_realized`, `cf_al_monthly`, `cf_as_monthly` (null if v2 SKIP), `cpo_pnl_al_leg`, `cpo_pnl_as_leg` (null if v2 SKIP)
- Notebook trios:
  - Trio A: K̂ calibration anchor σ_0 selection (why-block cites spec §2 v3 + framework derivation; pre-pinned per anti-fishing posture; no post-data tuning); HALT
  - Trio B: per-month Π(σ_T) replay (why → code → interpretation); HALT
  - Trio C: per-leg P&L decomposition (why → code → interpretation reporting envelope characterization seed); HALT

**Success criteria:**
- Per-month series spans maximum-feasible overlap with 2015-2026 window
- σ_T input is the Stage-1 realized monthly log-return-squared (NOT implied vol per FLAG-B6 anti-fishing)
- K̂ anchor selection is pre-pinned at trio A (anti-fishing — no post-data tuning)
- v2 SKIP path correctly nulls `cf_as_monthly` + `cpo_pnl_as_leg` columns; supply-side-only envelope is the deliverable per spec §6 PROCEED-without-v2

**Dependencies:** Task 4.1

**Typed-exception triggers:** none specific; if FLAG-B6 σ_T input cannot be loaded from Stage-1, HALT-and-surface (Stage-1 pin chain corruption)

#### Task 4.3: Realized P&L envelope characterization + regime-conditional decomposition (trio-checkpointed)

**Goal:** Characterize the realized P&L envelope by mean, SD, full quantile vector, max drawdown. Decompose by the four regimes RC FLAG #6 identified as over-represented in the 2015-2026 window: post-2014 oil shock, COVID, Fed tightening, normalcy.

**Inputs:**
- Per-month realized CPO P&L from Task 4.2
- Pair D Stage-1 regime classifications (from MEMO §6 / RC FLAG #6 inheritance)

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- Envelope summary JSON at `contracts/.scratch/pair-d-stage-2-B/v3/envelope_summary.json` with fields: `mean`, `sd`, `quantiles_p1_p5_p10_p25_p50_p75_p90_p95_p99`, `max_drawdown`, `min`, `max`
- Regime-conditional decomposition Parquet at `contracts/.scratch/pair-d-stage-2-B/v3/regime_decomposition.parquet` with columns: `regime`, `n_months`, `mean_pnl`, `sd_pnl`, `min_pnl`, `max_pnl`, `cumulative_pnl`
- Envelope chart PNG at `contracts/.scratch/pair-d-stage-2-B/v3/envelope_chart.png`
- Notebook trios:
  - Trio A: aggregate envelope characterization (why → code → interpretation reporting mean/SD/quantiles/MDD); HALT
  - Trio B: regime classification + per-regime decomposition (why → code → interpretation reporting per-regime statistics + flag for regime over-representation per RC FLAG #6); HALT

**Success criteria:**
- Envelope summary JSON populated with all required fields
- Regime decomposition spans the four regimes
- Notebook interpretation cites RC FLAG #6 explicitly (regime over-representation flagged for downstream Stage-3 calibration cadence)
- Per RC FLAG #3 inheritance: lag-6 dominance honored — Π(σ_T) replay uses 6-month-dominant lag pattern, NOT uniform 6-12mo (anti-fishing)

**Dependencies:** Task 4.2

**Typed-exception triggers:** none specific

#### Task 4.4: Calibration-handoff packet for Path A v3 (cross-path coupling artifact #2)

**Goal:** Emit the v3 calibration-handoff packet at `contracts/.scratch/pair-d-stage-2-B/v3/v3_handoff.json` containing the empirical `r_(a_l)` carried forward from v1's `r_al_handoff.json`, the `B_T` calibration (or v2 HALT artifact reference), and the realized envelope summary. Convergence dispatch (separate work item, OUT OF SCOPE for this plan) consumes both Path B v3 handoff + Path A v3 envelope to compare bounds.

**Inputs:**
- v1 `r_al_handoff.json` from Task 2.5
- v2 SKIP-marker OR empirical `B_T` from Phase 3
- Envelope summary JSON from Task 4.3

**Owner:** Data Engineer

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v3/v3_handoff.json` with fields: `r_al_point`, `r_al_hac_se`, `B_T_calibration` (null if v2 SKIP), `v2_skip_reason` (populated if v2 SKIPPED), `envelope_summary` (inlined from Task 4.3 JSON), `regime_decomposition_path` (relative path to regime decomposition parquet), `sample_window`, `source_pool_addresses` (list), `sha256_of_v1_handoff`, `stage1_panel_sha256`

**Success criteria:**
- All required fields populated; v2 SKIP path correctly nulls `B_T_calibration` + populates `v2_skip_reason`
- `sha256_of_v1_handoff` matches `r_al_handoff.json` sha
- `stage1_panel_sha256` matches Stage-1 pinned panel sha (READ-ONLY chain integrity)
- Handoff is self-contained: a convergence-dispatch executor reading ONLY this JSON + Path A v3 envelope JSON can compute the convergence comparison without traversing Path B internals

**Dependencies:** Task 4.3

**Typed-exception triggers:** none specific

#### Task 4.5: Phase 4 close — 3-way implementation review

**Goal:** Per `feedback_implementation_review_agents`, Phase 4 close gate.

**Inputs:** All Phase 4 outputs (notebook 04 + per-month P&L parquet + envelope summary + regime decomposition + envelope chart + v3 handoff JSON)

**Owner:** Foreground Orchestrator dispatches; Code Reviewer + Reality Checker + Senior Developer (charges parallel to Task 2.6, with Reality Checker emphasis on RC FLAG #1 — no causal-channel claims for the BPO mechanism — and RC FLAG #5 — no smuggled `marco2018_dummy`-equivalent post-data adjustment in v3 calibration). Data Engineer + Analytics Reporter for fixes.

**Outputs:**
- Three reviewer verdicts + defect lists
- Integrated phase-close fixes
- Findings memo at `contracts/.scratch/pair-d-stage-2-B/v3/findings.md` characterizing the realized P&L envelope and flagging convergence questions for the convergence-dispatch (separate work item)
- Commit with `Doc-Verify: code=<CR-id> reality=<RC-id> senior=<SD-id>` trailer

**Success criteria:**
- All three reviewers PASS or PASS-WITH-REVISIONS
- BLOCK-severity defect HALTS
- Findings memo states convergence-dispatch readiness (does Path B v3 have everything needed for convergence — yes/no/partial)

**Dependencies:** Task 4.4

**Typed-exception triggers:** none specific

### Phase 5 — Convergence + verdict authoring

#### Task 5.1: Synthesize structural-exposure characterization MEMO

**Goal:** Synthesize the v0 → v3 outputs into a single structural-exposure characterization memo. Quantify `|Δ^(a_l)|` and `|Δ^(a_s)|` magnitudes in $-notional that the CPO would neutralize on observed transaction flows. Frame exclusively as structural-exposure per CORRECTIONS-γ; NO WTP-inference language anywhere.

**Inputs:** All Phase 0-4 outputs (audits, v1 CF^(a_l), v2 CF^(a_s) or SKIP, v3 envelope, handoff packets, findings memos per phase)

**Owner:** Analytics Reporter (memo author)

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/MEMO.md` with sections:
  - §1 Spec sha256 pin (quoted from this plan frontmatter)
  - §2 Stage-1 sha-pin chain (READ-ONLY through Path B; quoted verbatim)
  - §3 v0 audit summary (which venues confirmed, which HALT-ed; on_chain_pins frozen at v0 close)
  - §4 v1 supply-side structural-exposure: per-pool `r_(a_l)` + `|Δ^(a_l)|` $-notional summary
  - §5 v2 demand-side structural-exposure (or SKIP disposition): per-router `|Δ^(a_s)|` $-notional summary OR PROCEED-without-v2 record
  - §6 v3 realized P&L envelope (mean, SD, quantiles, MDD; regime-conditional decomposition)
  - §7 Honest interpretation: do the realized cash-flow shapes match the framework's qualitative predictions (`Δ^(a_l) > 0`, `Δ^(a_s) < 0` if v2 PROCEEDED)? Sign-and-magnitude qualitative observation only — NO post-hoc goodness-of-fit threshold (anti-fishing per spec §7)
  - §8 Convergence questions for the (separate, OUT OF SCOPE for this plan) convergence-dispatch: does Path A v3's MC envelope contain Path B v3's realized envelope? What disagreements would be informative?
  - §9 Anti-fishing inheritance: RC FLAG #1 / #3 / #5 / #6 honored; structural-exposure framing exclusively per CORRECTIONS-γ; no WTP claims anywhere
  - §10 Stage-3 implications: explicitly OUT OF SCOPE; Path B characterizes realized history and produces calibration-handoff packets, does not recommend deployment, propose LP capital sourcing, scope onboarding, or describe regulatory framing
- File: `contracts/.scratch/pair-d-stage-2-B/gate_verdict.json` with fields: `spec_sha256`, `r_al_point`, `r_al_hac_se`, `cf_al_qualitative_match` (one of `match`, `partial_match`, `mismatch`), `v2_status` (one of `proceeded`, `skipped`, `halted_with_pivot`), `cf_as_qualitative_match` (one of `match`, `partial_match`, `mismatch`, `na_skip`), `envelope_mean`, `envelope_sd`, `envelope_quantiles`, `envelope_max_drawdown`, `regime_decomposition_path`, `convergence_dispatch_ready` (bool), `recommended_next_step` (one of `convergence_dispatch`, `stage3_pre_check`, `pair_d_killed_with_pivot`)

**Success criteria:**
- MEMO §1-§10 complete; all sections populated
- Structural-exposure framing exclusively (NO WTP language anywhere; Reality Checker spot-check confirms)
- gate_verdict.json schema parity with above field list; all fields populated (nulls explicit if v2 SKIP)

**Dependencies:** Phase 4 close

**Typed-exception triggers:** none specific; reviewer-flagged drift into WTP-inference language at Task 5.2 triggers HALT-disposition

#### Task 5.2: Three-way implementation review on MEMO + gate_verdict

**Goal:** Per `feedback_implementation_review_agents`, the convergence-verdict review.

**Inputs:** MEMO.md + gate_verdict.json + all Phase 0-4 outputs (reviewers may traverse upstream artifacts)

**Owner:** Foreground Orchestrator dispatches; Code Reviewer (charge: notebooks 01-04 implementations match spec methodology; no silent-test-pass; trio-checkpoint citation discipline; FLAG-B1 / B2 / B3 / B4 / B5 / B6 / B7 / B8 partition rules correctly applied per spec §3 normatives) + Reality Checker (charge: every MEMO claim supported by underlying parquet / chart / DATA_PROVENANCE.md; no narrative softening of v2 SKIP or qualitative mismatch; CORRECTIONS-γ structural-exposure framing exclusively respected — flag any WTP drift; RC FLAG #1 / #3 / #5 / #6 honored throughout) + Senior Developer (charge: production-readiness — could a fresh engineer re-run the v0 → v3 ladder with only the spec + Stage-1 panel sha + network_config + this plan; convergence-dispatch readiness — does Path B v3 ship everything the convergence dispatch needs).

**Outputs:**
- Three reviewer verdicts + defect lists
- Integrated revisions (if defects)
- HALT-disposition memo if any reviewer flags methodology-error class defect (e.g., post-hoc threshold tuning, WTP-inference drift, partition-rule violation, anti-fishing breach)

**Success criteria:**
- All three reviewers PASS or PASS-WITH-REVISIONS
- BLOCK-severity defect HALTS commit and re-dispatches Data Engineer / Analytics Reporter
- HALT-disposition triggered for any anti-fishing breach (no auto-correction; user adjudication required)

**Dependencies:** Task 5.1

**Typed-exception triggers:** none defined in spec §6 for review-stage methodology-error class; failure mode is HALT-disposition memo per `feedback_pathological_halt_anti_fishing_checkpoint`

#### Task 5.3: Final commit + CLAUDE.md update under 2-wave verify

**Goal:** Apply post-review revisions; commit final MEMO + gate_verdict + all Phase artifacts; update CLAUDE.md Active iteration block under 2-wave verify per `feedback_two_wave_doc_verification`.

**Inputs:**
- Post-review revisions
- CLAUDE.md Active iteration block diff (proposed text update)

**Owner:** Foreground Orchestrator dispatches; Reality Checker (Wave 1) + Workflow Architect (Wave 2) for CLAUDE.md update

**Outputs:**
- Final commit of MEMO.md + gate_verdict.json + all Phase artifacts with `Doc-Verify: code=<CR-id> reality=<RC-id> senior=<SD-id>` trailer
- CLAUDE.md Active iteration block updated with verdict + convergence-dispatch readiness pointer
- CLAUDE.md commit with `Doc-Verify: wave1=<RC-id> wave2=<WA-id>` trailer per `feedback_two_wave_doc_verification`

**Success criteria:**
- CLAUDE.md update is factual + scoped to Path B disposition; does NOT make WTP claims; does NOT make Stage-3 deployment claims; does NOT re-litigate Stage-1 pin chain
- 2-wave verify both PASS or PASS-WITH-REVISIONS
- Push to `dev` (origin = JMSBPP per `feedback_push_origin_not_upstream`)

**Dependencies:** Task 5.2

**Typed-exception triggers:** none specific

#### Task 5.4: User disposition (DISPOSITION.md)

**Goal:** Surface MEMO + gate_verdict to user; user decides next step.

**Inputs:** MEMO.md + gate_verdict.json

**Owner:** Foreground Orchestrator

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/DISPOSITION.md` with timestamp + chosen-next-step + verbatim user-rationale paragraph
- Disposition options (orchestrator surfaces to user):
  - **Convergence-dispatch ready** → user authorizes the (separate, OUT OF SCOPE for this plan) convergence dispatch comparing Path A v3 envelope vs Path B v3 envelope
  - **Convergence-dispatch ready, defer convergence** → Path B closes; convergence dispatch deferred to user discretion; gate_verdict + handoff packets remain available
  - **Stage-3 pre-check** → user authorizes a separate Stage-3 entry-gate review (LP capital + execution test on live Panoptic deployment; out of scope for this plan)
  - **Pair D killed with pivot** → user invokes the BPO research note 5-pair re-rank for the next iteration's Phase 0

**Success criteria:**
- User decision recorded in DISPOSITION.md with timestamp + rationale
- Decision is the user's, not auto-selected by orchestrator (auto-pivot anti-fishing-banned)

**Dependencies:** Task 5.3

**Typed-exception triggers:** none

## §4 — Dependency graph (text DAG)

Phases are sequential at the phase-close gate; tasks within a phase are partially parallelizable per the per-task Dependencies field.

```
Phase 0:
  0.1 (sha pin verify)
    → 0.2 (working dir + notebook scaffolding)
      → 0.3 (network_config.toml)
        → 0.4 (2-wave plan verify HALT — pre-execution gate)

Phase 1 (after 0.4):
  1.1 (allowlist + manifest)
    → 1.2 (per-venue audit)
      → 1.3 (Parquet emission)
        → 1.4 (TDD test suite)
          → 1.5 (3-way review + freeze on_chain_pins)

Phase 2 (after 1.5):
  2.1 (notebook 02 scaffolding)
    → 2.2 (swap-event extraction + FLAG-B8 partition)
      → 2.3 (r_(a_l) estimation per FLAG-B1)
        → 2.4 (CF^(a_l) series + shape-check)
          → 2.5 (r_al_handoff.json — B → A coupling artifact #1)
            → 2.6 (3-way review)

Phase 3 (after 2.6):
  3.1 (conditional gate — PROCEED vs SKIP)
    if PROCEED:
      → 3.2 (settlement-leg Transfer extraction)
        → 3.3 (q_t reconstruction + Σq_t/(X/Y)_t)
          → 3.4 (CF^(a_s) series + Δ-shape-check)
            → 3.5 (v1 ↔ v2 monthly reconciliation; CROSS-PHASE: depends on 2.4)
              → 3.6 (3-way review)
    if SKIP:
      → 3.6 (3-way review on SKIP-disposition memo)

Phase 4 (after 3.6 OR after 3.1 SKIP):
  4.1 (notebook 04 scaffolding)
    → 4.2 (Π(σ_T) replay)
      → 4.3 (envelope characterization + regime decomposition)
        → 4.4 (v3 handoff JSON — B → A coupling artifact #2)
          → 4.5 (3-way review)

Phase 5 (after 4.5):
  5.1 (synthesize MEMO + gate_verdict)
    → 5.2 (3-way implementation review)
      → 5.3 (final commit + CLAUDE.md 2-wave verify)
        → 5.4 (user DISPOSITION.md)
```

**Cross-path coupling artifacts (B → A):**
- `r_al_handoff.json` emitted at Task 2.5 (v1 calibration anchor; OPTIONALLY consumed by Path A v3)
- `v3_handoff.json` emitted at Task 4.4 (v3 envelope; consumed by separate convergence-dispatch)

**No A → B coupling at any task in this plan** (per spec §8 + FLAG-B9; A → B v3 envelope coupling is a convergence-dispatch concern OUT OF SCOPE for this plan).

## §5 — Provenance + reproducibility discipline

Per spec §3.A normative, every committed dataset is accompanied by a `DATA_PROVENANCE.md` file in the same directory recording per-input fields:

- `source` (URL or contract address + chain)
- `fetch_method` (tool + parameters)
- `fetch_timestamp` (ISO-8601 UTC)
- `sha256` (raw fetched payload pre-transformation AND committed parquet)
- `row_count` (post-fetch)
- `block_range` (`(first_block, last_block)` of on-chain query window)
- `schema_version` (hash of column-set + dtypes per spec §4.0)
- `filter_applied` (descriptive string of partition rules — e.g., `FLAG-B8-layer-1+layer-2 applied; dropped 412 rows / 0.8% volume`)

**HALT-on-mismatch protocol (spec §3.A normative):**

Re-execution of the same fetch must produce a sha256 within ±0.01% row count tolerance and identical schema_version. The row tolerance accommodates new on-chain blocks since the previous fetch. A non-trivial schema_version drift, a >0.01% row delta inside a frozen block range, or a sha256 change that cannot be reconciled to known new-block additions triggers `Stage2PathBProvenanceMismatch` typed exception per spec §6.

Per-task disposition on `Stage2PathBProvenanceMismatch`:
- (a) investigate whether SQD Network re-indexed the affected block range (legitimate cause; document in DATA_PROVENANCE.md and proceed)
- (b) investigate whether a partition rule (FLAG-B8) was inadvertently changed (methodology error; HALT and revert)
- (c) full re-extraction with fresh fetch_timestamp and side-by-side diff (anti-fishing-load-bearing — silent re-run without sha audit is banned)

**DATA_PROVENANCE.md template (Task 0.2 deliverable; mirrors Stage-1 Pair D template at `contracts/.scratch/simple-beta-pair-d/data/DATA_PROVENANCE.md`):**

The 8-field schema above is the floor; per-artifact extensions for on-chain extraction (`block_range`, `filter_applied`) are added on top, never instead of, the Stage-1 fields. A `DATA_PROVENANCE.md` file with fewer than 8 base fields is a methodology violation flagged by Reality Checker at every phase-close 3-way review.

**Reproducibility floor:** A fresh engineer reading ONLY the spec + this plan + the network_config + Stage-1 sha-pin chain must be able to re-execute every Phase 1-4 task and reproduce the parquet outputs within ±0.01% row delta + identical schema_version. Failure to meet this floor at any phase close triggers HALT-disposition; Senior Developer charge at every 3-way review explicitly tests against this floor.

## §6 — Free-tier-only budget enforcement

Per spec §5 `budget_pin: free_tier_only` (CORRECTIONS-δ user directive 2026-05-02; supersedes v1.1's $49/mo Alchemy Growth pin). Auto-pivot to paid services is anti-fishing-banned per spec §5.A degradation Step 5; any escalation to paid services requires user-adjudicated typed-exception HALT.

**Tooling stack (spec §5):**
- **SQD Network public gateways** (PRIMARY for bulk archive extraction; FREE; Celo + Ethereum mainnet support; ~5 req/sec per IP per docs.sqd.ai 2025-02-23 notice)
- **Alchemy free tier** (SECONDARY for spot RPC + receipts; FREE; 30M CU/month, 25 req/sec, 500 CU/sec rolling-window cap; verified via WebFetch 2026-05-02)
- **The Graph hosted-service** (free for pre-existing subgraphs; preferred over raw `eth_getLogs` where coverage exists AND SQD does not give cleaner schema)
- **Dune Analytics free tier** (~2500 credits/month working assumption; rate limits 15 rpm low-limit + 40 rpm high-limit; ad-hoc analytical SQL only; NOT for bulk extraction)
- **Public RPC fallback** (forno.celo.org for Celo; eth.llamarpc.com / rpc.ankr.com/eth for Ethereum; FALLBACK ONLY under `Stage2PathBPublicRPCConsistencyDegraded` HALT-and-flag discipline)
- **Celoscan + Etherscan free-tier API** (5 req/s; ad-hoc human-readable verification only; NEVER for bulk extraction)

**Per-phase rate-limit + monthly-CU projection (spec §5.A):**

| Phase | SQD queries (lifetime) | Alchemy CU (monthly aggregate) | Dune credits (monthly aggregate) | Public RPC | Burst-rate binding constraint |
|---|---|---|---|---|---|
| Phase 0 (scaffolding) | 0 | 0 | 0 | none | none |
| Phase 1 (v0 audit) | ~50 | <5K | 0-5 | none expected | sequential issuance well below caps |
| Phase 2 (v1 CF^a_l) | ~25-225 | ~15-50K | ~20-50 | none expected | Alchemy 25 req/sec on receipt enrichment batches |
| Phase 3 (v2 CF^a_s) | ~50-75 | <30K | ~5-10 | none expected | sequential SQD 5 req/sec |
| Phase 4 (v3 backtest) | 0 | 0 | 0 | none | pure local computation |
| Phase 5 (memo + verdict) | 0 | 0 | 0 | none | pure local + review |
| **Aggregate Path B** | **~125-345** | **~30-95K (~0.1-0.3% of 30M cap)** | **<100 (~4% of ~2500/mo)** | **opportunistic** | **Alchemy 25 req/sec sustained** |

**Burst-rate discipline (spec §5.A binding-constraint pin):**
- All Alchemy receipt enrichment batched into ≤25-receipt request windows separated by ≥1 second sleep, regardless of total receipt budget. Concurrency cap = 1 (sequential)
- All SQD Network chunked queries issued sequentially with ≥250 ms inter-call sleep. Concurrency cap = 1 per IP
- All Dune queries sequential; pre-flight cost-estimate inspection before each execution
- Rolling-window monitoring: executor MUST log `req_per_sec` and `cu_per_sec` to a local audit log per data source per minute (`burst_rate_log.csv` per phase); spike >80% of either cap surfaces a warning and pauses next batch ≥5 sec
- Exceedance triggers `Stage2PathBAlchemyFreeTierRateLimitExceeded` typed exception with disposition: pause, reduce concurrency / chunk size, retry; if exceedance recurs after retry, HALT-and-flag

**Auto-pivot ban:** auto-pivot through SQD → The Graph → Alchemy free → Dune → public-RPC fallback (spec §5.A degradation Steps 1-4) is permitted (all free-tier; tooling fallback, not result-shaping). Auto-pivot to Step 5 (paid Subsquid Cloud OR paid Alchemy tier OR Dune Analyst OR paid Eigenphi API) is **anti-fishing-banned** and requires explicit user adjudication via typed-exception HALT.

## §7 — Cross-path coordination

Per spec §8 + FLAG-B9: paths A and B are **DEFAULT INDEPENDENT** at all rungs. The two coupling points are emission-side artifacts only; this plan does NOT consume any Path A artifact at any task.

**B → A coupling emission contracts (this plan emits, Path A v3 OPTIONALLY consumes):**

- **Phase 2 emission:** `r_al_handoff.json` per FLAG-B9 schema with fields:
  - `r_al_point` (float; OLS point estimate)
  - `r_al_hac_se` (float; Newey-West HAC standard error)
  - `sample_n` (int; daily-bin count)
  - `sample_window` (string; ISO-8601 date range, e.g., `"2023-08-15/2026-02-28"`)
  - `source_pool_address` (string; 0x-prefixed checksummed)
  - `sha256_of_input_panel` (string; sha256 of the per-pool partitioned swap parquet)
  - Path A v3 OPTIONALLY consumes this packet as the calibration anchor for its stochastic-σ MC empirical-calibrated variant (per Path A spec §12 + FLAG-F4 baseline pin); if Path B v1 has not landed by Path A v3 dispatch time, Path A v3 proceeds with GBM baseline + escalations only.

- **Phase 4 emission:** `v3_handoff.json` (extended schema; convergence-dispatch consumption) with fields:
  - All `r_al_handoff.json` fields (carried forward)
  - `B_T_calibration` (float; null if v2 SKIPPED)
  - `v2_skip_reason` (string; populated if v2 SKIPPED)
  - `envelope_summary` (object; mean / SD / quantiles / max_drawdown — inlined from Task 4.3)
  - `regime_decomposition_path` (string; relative path to regime decomposition parquet)
  - `stage1_panel_sha256` (string; for cross-stage chain-integrity verification)
  - The convergence-dispatch (separate work item OUT OF SCOPE for this plan) consumes this packet alongside Path A v3's MC envelope JSON to compute the convergence comparison.

**A → B coupling at any phase: NONE per FLAG-B9.** Path B does not consume Path A's parametric assumptions, σ-path decomposition, position-geometry choices, or v3 envelope JSON at any task in this plan. Cross-path reconciliation (does Path A's harness-realized CF^(a_l) match Path B's on-chain-realized CF^(a_l) within tolerance?) is the convergence-dispatch's job, NOT Path B's job.

**Convergence-dispatch is OUT OF SCOPE for this plan.** When both Path A v3 and Path B v3 deliver their respective handoff packets, the orchestrator dispatches a separate convergence comparison work item; that work item is its own plan, not a Path B task.

## §8 — Self-review checklist (run by orchestrator before commit of THIS plan)

- **Spec coverage:** does every spec §1-§9 normative requirement map to a task here?
  - §1 framing-definition (structural-exposure) → §1 Overview + repeated reminders in every Phase 2-5 task description; §2 Phase decomposition Phase 5 explicit deliverable
  - §2 internal ladder (v0/v1/v2/v3) → Phases 1/2/3/4 (1:1 mapping)
  - §3 inputs (Stage-1 sha pins, on-chain pre-pins, FLAG-B1/B2/B3/B4/B5/B6/B7/B8/B9) → all FLAGs cited in per-task Inputs fields; Stage-1 sha pins frozen in plan frontmatter
  - §3.A provenance discipline → §5 dedicated section + per-task Outputs fields cite DATA_PROVENANCE.md
  - §4 outputs → per-phase per-task Outputs fields enumerate all spec §4 deliverables
  - §4.0 v0 schema (3 Parquet artifacts) → Tasks 1.3 + 1.4 (TDD)
  - §5 + §5.A free-tier-only tooling stack → §6 dedicated section + Task 0.3 network_config.toml
  - §6 typed exceptions (10 enumerated) → per-task Typed-exception triggers fields
  - §7 anti-fishing posture → §1 Overview + repeated CORRECTIONS-γ reminders + Task 2.6 / 3.6 / 4.5 / 5.2 Reality Checker charges
  - §8 convergence with Path A → §7 dedicated section
  - §9 self-review checklist → spec-side, mirrored in this plan §8

- **Placeholder scan:** zero "TBD" / "TODO" / "fill in details" / "similar to Task N" / "implement appropriate handling" — verify by full-text grep before commit.

- **Code-agnosticism:** zero executable code blocks per `feedback_no_code_in_specs_or_plans`. Schema definitions, address pins, mathematical formulas (in inline notation), configuration parameters (in TOML/YAML/JSON form), and dependency lists are permitted; actual Python / SQL / JavaScript implementation is not.

- **Specialist coverage:** every task names an owner per `feedback_specialized_agents_per_task`. Distribution: Foreground Orchestrator (verification + dispatch + final commit); Data Engineer (extraction + parquet emission + tests + scaffolding); Analytics Reporter (notebook authorship + memo authorship + trio HALT discipline); Code Reviewer + Reality Checker + Senior Developer (per-phase 3-way review); Workflow Architect (Wave 2 plan-verification + CLAUDE.md update Wave 2).

- **Anti-fishing discipline:** spec sha256 pin frozen in plan frontmatter; Stage-1 sha-pin chain READ-ONLY through Path B; no auto-pivot to paid services; auto-pivot through free-tier degradation Steps 1-4 permitted with explicit logging; HALT-disposition path per `feedback_pathological_halt_anti_fishing_checkpoint` for every typed exception; no post-hoc threshold tuning; no curve-fitting to frame results; no causal-channel claims for BPO mechanism (RC FLAG #1); no β re-litigation of Stage-1 result; no Stage-3 deployment claims; structural-exposure framing exclusively per CORRECTIONS-γ — NO WTP-inference language anywhere in plan.

- **2-wave doc verification:** plan write triggers RC + Workflow Architect (Task 0.4); spec frontmatter `on_chain_pins` update at Task 1.5 triggers RC + Model QA Specialist (spec write per `feedback_two_wave_doc_verification`); CLAUDE.md update triggers RC + Workflow Architect (Task 5.3).

- **3-way implementation review per phase:** Code Reviewer + Reality Checker + Senior Developer (per `feedback_implementation_review_agents`; Tech Writer NOT used at implementation reviews) — Phase 1 close (Task 1.5), Phase 2 close (Task 2.6), Phase 3 close (Task 3.6), Phase 4 close (Task 4.5), Phase 5 (Task 5.2).

- **Real data over mocks:** Per `feedback_real_data_over_mocks`, every test uses real on-chain data via SQD / Alchemy / public RPC; mocks are reserved exclusively for HTTP errors that cannot be reproduced (e.g., simulating a 429 rate-limit response that Alchemy is not currently issuing).

- **Strict TDD:** Per `feedback_strict_tdd`, no implementation lands without a failing test first. Phase 1 has explicit TDD task (1.4); Phase 2-4 notebook trios have implicit TDD via the trio-checkpoint structure (the `interpretation` markdown asserts what the `code` cell should produce; if `code` does not produce it, the trio HALTs and re-dispatches).

- **Push to dev not upstream:** Per `feedback_push_origin_not_upstream`, all commits push to `origin` (JMSBPP), NEVER `upstream` (wvs-finance). Plan frontmatter `push_target: dev` reflects this.

- **No code in plan:** verified — equation notation in §3 is methodology specification (LaTeX-style inline `Π(σ_T) ≈ K̂·σ_T`); SQL query templates in `text` blocks are permitted but not used in this plan (no pre-formed query templates needed — executor discretion bounded by spec §3 normatives); actual Python BANNED.

- **Deliverable framing:** structural-exposure characterization throughout per CORRECTIONS-γ — verified at every Phase 2-5 task description; "demand-side" preserved only as economic-leg terminology naming the a_s leg of the framework decomposition (per spec §1 framing-definition + spec v1.3 §1 framing rewrite + spec §4 v2 output bullet simplification).

## §9 — Plan validation gates

**Pre-execution (before Phase 0):** This plan must pass 2-wave verification per `feedback_two_wave_doc_verification`:
- Wave 1: Reality Checker (charge: structural-exposure framing fidelity per CORRECTIONS-γ; free-tier-only enforcement; anti-fishing pivot HALT discipline; no WTP-inference language)
- Wave 2: Workflow Architect (charge: task ordering + dependency-graph correctness; specialist-coverage discipline; 3-way implementation review hooks per phase; cross-path coupling emission-only constraint)

Both verifiers must return PASS or PASS-WITH-REVISIONS before Phase 0 execution begins. BLOCK-severity defect from either wave HALTS commit and re-dispatches.

**Per-phase (Phase 1-4 close):** Each phase concludes with 3-way implementation review per `feedback_implementation_review_agents`:
- Code Reviewer (charge: implementation matches spec methodology; no silent-test-pass per `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons` 5-instance catalogue; trio-checkpoint citation discipline; FLAG partition rules correctly applied)
- Reality Checker (charge: every output supported by underlying data per DATA_PROVENANCE.md; no narrative softening; CORRECTIONS-γ structural-exposure framing exclusively; RC FLAG #1 / #3 / #5 / #6 honored)
- Senior Developer (charge: production-readiness — could a fresh engineer re-run the phase with only spec + upstream phase outputs + network_config?)

Data Engineer + Analytics Reporter on-call for fixes. BLOCK-severity defect HALTS phase close.

**Convergence gate (Phase 5 close):** 3-way implementation review on MEMO + gate_verdict (Task 5.2) must PASS or PASS-WITH-REVISIONS. CLAUDE.md update at Task 5.3 must pass 2-wave verify per `feedback_two_wave_doc_verification`. User disposition at Task 5.4 records final next-step decision.

**HALT-disposition discipline (every gate):** Per `feedback_pathological_halt_anti_fishing_checkpoint`, every HALT (typed exception, BLOCK reviewer defect, methodology error) triggers:
1. Typed exception (named per spec §6 OR newly-named for review-stage methodology errors)
2. Disposition memo enumerating ≥3 user-enumerated pivots (sourced from spec §6 pivot lists where applicable)
3. User adjudication
4. CORRECTIONS-block in plan revision if pivot lands
5. 3-way review of CORRECTIONS revision before re-dispatch

Auto-pivot is anti-fishing-banned at every HALT.

---

## Execution handoff

Plan complete pending Task 0.4 2-wave verification per `feedback_two_wave_doc_verification`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — orchestrator dispatches a fresh specialist per task per the named owners, reviews between tasks, mandatory trio-checkpoint HALTs in Phases 2-4 notebook authoring.

2. **Inline Execution** — execute tasks in this session via `superpowers:executing-plans`, batch with checkpoints. Higher context burn; harder to enforce specialist discipline; trio-checkpoint discipline harder to enforce on notebook authoring.

**Recommended: Subagent-Driven**, given the trio-checkpoint discipline mandated by `feedback_notebook_trio_checkpoint`, the multi-specialist design of the plan (Data Engineer + Analytics Reporter + Code Reviewer + Reality Checker + Senior Developer + Workflow Architect roles all required), and the free-tier-only burst-rate discipline that benefits from per-task execution boundaries.

**End of plan body.** Frontmatter `plan_verifier_v1_wave1` and `plan_verifier_v1_wave2` fields are pending Task 0.4 dispatch.
