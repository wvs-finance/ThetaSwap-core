---
spec_path: pair-d-stage-2-v1.5-data-aggregation-design
spec_version: v1.0 (initial via CORRECTIONS-η decomposition from v1.5-original)
spec_author: orchestrator + user co-design 2026-05-04
spec_sha256: <to-be-pinned-after-recompute>
parent_spec_pin: 2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md (v1.4, sha fcebc95f923e1b55fbf2eaa22239b00bbde4a9f35bb031e8f32d090a4fb80d95)
parent_plan_pin: 2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md (v1.1, sha 7e2f43c211a314475c3fc2ef5890c268c7216efa55b0b7a9d2c8e5d8d95bca6b)
predecessor_spec_pin: 2026-05-04-pair-d-stage-2-v1.5-model-fitness-design.md (v1.5-original; SUPERSEDED-BY-DECOMPOSITION; sha 8a8ce0571bf7e5786048b13753991468c8fb63596c9dfe1a4d2b409e479a6514)
correction_block_pin: contracts/.scratch/path-b-stage-2/phase-1/corrections_eta_decomposition.md
discovery_pin: contracts/.scratch/path-b-stage-2/phase-1/cop_corridor_aggregate_research/discovery.md
aggregation_methodology_pin: contracts/.scratch/path-b-stage-2/phase-1/cop_corridor_aggregate_research/aggregation_methodology.md
gate_b1_review_pin: contracts/.scratch/path-b-stage-2/phase-1/gate_b1_review.md
synthesis_memo_pin: contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/SYNTHESIS.md (commit e25131cd2)
budget_pin: free_tier_only (preserved from CORRECTIONS-δ)
methodology_spec_link: <pending> v1.5-methodology spec — DEFERRED until v1.5-data execution delivers aggregate panel + n_informative_table + ar1_diagnostic + σ-anchor reality + cohort-N empirical floor
verifier_v1_0_wave1: pending (Reality Checker — 2-wave verification per `feedback_two_wave_doc_verification`)
verifier_v1_0_wave2: pending (Model QA Specialist — 2-wave verification per `feedback_two_wave_doc_verification`)
---

# Pair D Stage-2 — v1.5-data Aggregate COP-Corridor Substrate Design

## §1. Overview and scope

This design specifies the **substrate-aggregation tier** of the v1.5 model-fitness gate: the COP-corridor aggregate panel build, per-venue audit protocol, supply-share-weighted aggregation methodology, USD-equivalence pipeline, and N_INFORMATIVE measurement protocol. **No statistical methodology is committed to in this spec** — the 3-test gate (v1.5a Π convexity / v1.5b q_t empirical fit / v1.5c K equilibrium magnitude) is deferred to a separate v1.5-methodology spec authored AFTER v1.5-data execution lands.

**Why decomposed**: predecessor v1.5-original spec attempted to pin all methodological pre-commitments (AIC delta thresholds, K-means k-selection, bootstrap method, R-thresholds) before the aggregate substrate panel was built. 2-wave verify (RC + Model QA) found the spec assumed n=135 weeks but realized phase-1 substrate has n≈9-14 informative weeks for direct BiPool USDm/COPm — making every a-priori threshold fragile. Per CORRECTIONS-η, methodology choices are deferred until empirical anchors (realized n, AR(1), cohort size, σ-anchor coverage) are in hand. v1.5-data ships those anchors.

**Goals**:
1. **Substrate-aggregation deliverable** (PRIORITY-1 per user direction 2026-05-04) — exhaustively collect non_lp_user, mev_arb, lp_mint_burn flow across 7 COP-corridor venues; emit aggregate panel suitable for downstream methodology.
2. **N_INFORMATIVE measurement** — per-venue and aggregate count of weeks-with-non-zero-events; the table that lets v1.5-methodology pin a defensible N_INFORMATIVE floor.
3. **AR(1) diagnostic emission** — first-order autocorrelation of aggregate-flow series; the input that lets v1.5-methodology pin bootstrap block-length.
4. **σ-anchor reality assessment** — informative-weeks count per σ-anchor source (Banrep TRM / Mento V2 BiPool spot / Polygon Uniswap V3 spot); the input that lets v1.5-methodology pin σ-anchor primary specification.
5. **Anti-fishing discipline** — W1-W5 weight invariants pre-pinned at audit_block, never re-tuned post-data; substrate scope frozen at this spec's commit; no post-data substrate addition without CORRECTIONS-block.

**Non-goals (deferred to v1.5-methodology)**:
- 3-test gate (v1.5a Π convexity / v1.5b q_t empirical fit / v1.5c K equilibrium magnitude)
- AIC vs AICc + ΔAIC threshold pinning
- K-means k-selection rule + cohort filter sensitivity arm
- Bootstrap method (Politis-Romano vs i.i.d.) + block-length pinning
- R-ratio threshold motivation + CI-aware verdict rule
- Thesis-fitness verdict layer (non-convex Π winners → typed exception)
- Gate B1 (a)/(b)/(c) substrate-pivot adjudication block (this spec ships the data that informs the decision; the decision happens at v1.5-methodology authoring)

**Execution priority** (per user direction 2026-05-04, verbatim): *"the most important thing is to get the most data we can from all the sources of dark currency sources. Once we get the best of all the aggregates, we can just implement the model we are thinking for, just tweak it. subject to our needs. But we need to first collect the most of the data."*

This spec is the data-collection-first instantiation.

**Chain scope rule (per user direction 2026-05-04, verbatim)**: *"Only EVM chains. Include new chains like HyperEVM and MegaETH."*

EVM-only is now an explicit pre-commitment (§13.1.bis). Solana is EXCLUDED (row 10 of §3) under this rule. New / emerging EVM chains (HyperEVM, MegaETH) are added to v1.5-data substrate research scope as RESEARCH_PENDING_DISCOVERY rows; if COP-pegged tokens are confirmed on those chains via the research dispatch (§3.bis), they enter the aggregator under the standard §4 audit gate. **Stage-3 forward note**: HyperEVM is additionally flagged as a deployment-target candidate for Panoptic-style options venue (out of scope for v1.5-data substrate-side; recorded here as user's expressed interest 2026-05-04 to inform future M-side dispatch).

## §2. Architecture — v1.5-data flow

```text
Phase 1 done (Mento-native baseline)
   │
   ├─> CORRECTIONS-ζ substrate-scope expansion (NEW)
   │       │
   │       ├─> Add 5 venues to allowlist (Minteo Polygon + Num nCOP + Wenia COPW + DLYCOP + Minteo Solana per inclusion table)
   │       ├─> Re-run Phase 1 audit on expanded set
   │       └─> Per-venue PASS / MARGINAL / HALT verdict per §3 thresholds
   │
   ├─> Aggregate panel build (NEW)
   │       │
   │       ├─> Pin audit_block per chain (Celo / Polygon / BSC / Solana)
   │       ├─> Compute supply-share weights at audit_block per W1-W5
   │       ├─> Per-week aggregator with sparse-flag + aggregator-NULL discipline
   │       └─> Emit cop_corridor_aggregate_panel.parquet
   │
   ├─> N_INFORMATIVE measurement (NEW)
   │       │
   │       ├─> Per-venue weeks-with-non-zero-events count
   │       ├─> Aggregate weeks-with-non-NULL-aggregator count
   │       └─> Emit n_informative_table.parquet
   │
   ├─> AR(1) diagnostic (NEW)
   │       │
   │       └─> Emit ar1_diagnostic.json on aggregate-flow series
   │
   ├─> σ-anchor reality assessment (NEW)
   │       │
   │       └─> Emit sigma_anchor_coverage.json (per-anchor informative weeks)
   │
   └─> Gate B1.5-data 3-way review
           │
           └─> v1.5-methodology authoring UNBLOCKED iff Gate B1.5-data PASSES
```

**Inputs (all free-tier observable; sourced from prior Phase 1 outputs + CORRECTIONS-ζ substrate scope expansion + Stage-1 Banrep TRM)**:
- Phase 1 outputs: `audit_summary.parquet` + `address_inventory.parquet` + `event_inventory.parquet` + `mento_swap_flow_inventory.parquet` (READ-ONLY; not modified by v1.5-data)
- CORRECTIONS-ζ allowlist additions: 5 venue contract addresses (per §3 inclusion table)
- Stage-1 panel sha-pin chain (READ-ONLY)
- Banrep TRM API (already pinned in Stage-1)

**Outputs from v1.5-data** (consumed by v1.5-methodology):
- `cop_corridor_aggregate_panel.parquet` — per-week aggregate flow + per-substrate contributions (load-bearing artifact)
- `n_informative_table.parquet` — per-venue + aggregate informative-weeks count
- `ar1_diagnostic.json` — AR(1) coefficient on aggregate-flow series
- `sigma_anchor_coverage.json` — per-anchor informative-weeks count
- `audit_block_pin.json` — frozen audit_block per chain with sha256-pinned timestamps
- `v1_5_data_findings.md` — narrative interpretation; substrate-pivot adjudication input
- Per-venue augmented `audit_metrics_raw.json` (extending Phase 1 schema for the 5 new venues)

## §3. Substrate scope and inclusion table

The v1.5-data substrate scope is FROZEN at this spec's commit. Post-commit substrate additions require CORRECTIONS-block + 2-wave verify.

| # | Venue | Chain | Address | Inclusion verdict | Resolution-pending action | Velocity-floor disposition |
|---|---|---|---|---|---|---|
| 1 | Mento V2 COPm baseline | Celo | `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` | INCLUDED (Phase 1 baseline) | None | Velocity-floor PASS at Phase 1 (51,802 events) |
| 2 | Mento V2 BiPool USDm/COPm exchange | Celo | exchange_id `0x1c9378bd0973ff313a599d3effc654ba759f8ccca655ab6d6ce5bd39a212943b` | INCLUDED (Phase 1 baseline) | None | Velocity-floor MARGINAL at Phase 1 (302 swaps); retained per spec §6 secondary fall-back authorization |
| 3 | Mento V2 Broker | Celo | `0x777A8255B25Be7d7AF8a90c8AEDdcb53A1ad017f` | INCLUDED (Phase 1 baseline; broker-routed flow proxy) | None | Velocity-floor PASS at Phase 1 (672K events) |
| 4 | Minteo COPM Celo | Celo | `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` | INCLUDED (re-include per substrate-expansion) | Phase 1 audit re-run on this venue | Pre-audit |
| 5 | Minteo COPM Polygon | Polygon | `0x12050c705152931cFEe3DD56c52Fb09Dea816C23` | INCLUDED (HIGH PRIORITY per discovery.md §1.3 — $200M+ monthly attested) | Phase 1 audit on Polygon SQD endpoint | Pre-audit |
| 6 | Num Finance nCOP Polygon | Polygon | `0x0856f80fF4dE8F2bF89872B27ba6e9Fb45d96Ae3` | INCLUDED (independent issuer; 2023 launch; 180M supply) | Phase 1 audit on Polygon SQD endpoint | Pre-audit |
| 7 | Wenia COPW Polygon | Polygon | `<PENDING_TOKEN_RESOLUTION_VIA_POR_FEED_PROBE>` | CONDITIONAL_INCLUDE (token address pending) | 1-call eth_call eth_getStorageAt on PoR feed `0x1d22c334621364F16f050076eE15Acd5eb8225Ce` to extract bound token contract; HALT-and-surface if free-tier resolution fails within sub-plan Task 2.1 budget | Pre-audit; resolution required before audit |
| 8 | Daily COP DLYCOP Polygon | Polygon | `0x1659fFb2d40DfB1671Ac226A0D9Dcc95A774521A` | CONDITIONAL_INCLUDE (substrate-floor reference; not primary aggregator weight) | Phase 1 audit; expected to fail W1 velocity floor (24h vol $75) | Likely velocity-floor exclusion → w_DLYCOP = 0 in aggregator |
| 9 | Daily COP DLYCOP BSC | BSC | `0xE9C6824508c19bc98b162BbcD7c940bFA4287e27` | EXCLUDED (EVM-eligible per user EVM-only directive but free-tier SQD coverage thin → future-iteration) | None | N/A |
| 10 | Minteo SPL Solana | Solana | `Copm5KwCLXDTWYgXJYmo6ixmMZrxd1wabkujkcuaK47C` | EXCLUDED (non-EVM; user EVM-only directive 2026-05-04 confirms permanent exclusion from v1.5-data scope) | None | N/A |
| 11 | HyperEVM (Hyperliquid L1 EVM) — COP-pegged tokens | HyperEVM | TBD via §3.bis discovery dispatch | RESEARCH_PENDING_DISCOVERY | Trend Researcher dispatch for COP-pegged token deployments (Mento V3 multi-chain bridge, Minteo HyperEVM deployment, Wenia HyperEVM, Num Finance HyperEVM, native HyperEVM-issued COP) | Pre-discovery |
| 12 | MegaETH (high-throughput L2) — COP-pegged tokens | MegaETH | TBD via §3.bis discovery dispatch | RESEARCH_PENDING_DISCOVERY | Trend Researcher dispatch for COP-pegged token deployments | Pre-discovery |

**v1.5-data effective substrate set**:
- **Confirmed in scope (rows 1-8)**: 8 venues (4 confirmed EVM tokens + 1 conditional Wenia + 1 conditional DLYCOP + 2 Mento V2 settlement venues + 1 Mento V2 baseline)
- **Research-pending (rows 11-12)**: HyperEVM + MegaETH; if discovery returns positive COP-pegged token deployments, those tokens enter the aggregator under the standard §4 audit gate via CORRECTIONS-block-style spec amendment (substrate addition triggers CORRECTIONS-block + 2-wave verify per §13 invariant 1)
- **Excluded (rows 9-10)**: BSC DLYCOP (free-tier coverage thin), Solana Minteo (non-EVM)

Wenia COPW (row 7) is CONDITIONAL on PoR-feed probe success; if the probe fails to resolve the token address within free-tier budget, v1.5-data ships with 7 venues and a HALT-and-surface entry in `v1_5_data_findings.md`.

### §3.bis Future-iteration EVM substrate research targets

Per user direction 2026-05-04 ("Only EVM chains. Include new chains like HyperEVM and MegaETH"), the v1.5-data scope opens an EVM-only research-pending category alongside the confirmed Polygon + Celo set. Two emerging EVM chains are seeded as priority research targets:

- **HyperEVM (Hyperliquid L1 EVM)**: Hyperliquid's EVM execution layer (launched 2025); user-flagged as priority EVM ecosystem with high developer attention. Concurrent **Stage-3 deployment-target interest**: HyperEVM is also flagged for future Panoptic-style options venue evaluation (this is M-side Stage-2 work, NOT v1.5-data substrate-side; recorded for future M-dispatch). For v1.5-data, the question is narrowly: does any COP-pegged token deploy on HyperEVM as of audit_block?
- **MegaETH**: High-throughput EVM L2/L3 (testnet → mainnet trajectory in 2026); emerging ecosystem. Question for v1.5-data: any COP-pegged token deployment as of audit_block?

**Discovery methodology** (mirrors `cop_corridor_aggregate_research/discovery.md` §1 pattern):
- WebSearch for "HyperEVM COP stablecoin", "HyperEVM Colombian peso", "MegaETH stablecoin", "MegaETH COP", and Mento / Minteo / Wenia / Num Finance multichain deployment announcements
- Native chain explorers: HyperEVM explorer (purrsec.com / hyperliquid.xyz), MegaETH explorer
- GeckoTerminal / DEXScreener filters by chain
- Mento V3 multichain registry (if any cross-chain BiPool deployment registers HyperEVM/MegaETH)

**Inclusion gate**: any discovered COP-pegged token must (a) be free-tier observable via SQD or public RPC on its chain, (b) pass §4 per-venue audit thresholds, (c) trigger CORRECTIONS-block + 2-wave verify on this spec for substrate-scope amendment before entering the aggregator.

**Discovery dispatch**: queued in parallel with v1.5-data spec 2-wave verify (Trend Researcher dispatched 2026-05-04).

## §4. Per-venue audit protocol

Each new venue (rows 4-8 above) runs through the Phase 1 audit script (`contracts/.scratch/path-b-stage-2/phase-1/scripts/run_task_1_2_audit.py`) extended with venue-specific block-window endpoints and partition-extraction logic.

**Audit deliverables per venue** (extending Phase 1 schema):
- Total event count over sample window
- Per-partition event count (non_lp_user / mev_arb / lp_mint_burn) where applicable
- Per-week event histogram
- Holders inventory (top-N from Transfer events)
- Mint/Burn event count (issuer-side observability)
- USD-anchored notional per partition

**Per-venue verdict thresholds** (mirroring Phase 1 PASS/MARGINAL/HALT but extended for non-Mento venues):

| Verdict | Criterion | Routing |
|---|---|---|
| **PASS** | Total events ≥ 1000 over sample window AND non_lp_user partition non_zero in ≥ 30% of weeks | Include in aggregate with full weight; emit normal audit row |
| **MARGINAL** | Total events ∈ [100, 1000) OR non_lp_user non_zero in [10%, 30%) of weeks | Include in aggregate with sparse-flag handling per W2; emit MARGINAL audit row |
| **HALT** | Total events < 100 OR non_lp_user non_zero in < 5% of weeks (W1 velocity-floor exclusion) | Set w_venue = 0 in aggregator; emit HALT audit row with structural-truth reasoning |

**Anti-fishing**: per-venue thresholds are pre-pinned in this spec. Post-data threshold relaxation (e.g., "DLYCOP is 6% non-zero, let's lower the floor to 5%") fires `Stage2PathBPerVenueThresholdTuningProhibited` typed exception.

**Free-tier budget per venue audit**: ~30-40 SQD requests per venue × 5 new venues = 150-200 SQD requests over Phase 2 v1.5-data sub-plan execution. Estimated Alchemy CU: 5-10 CU for `eth_call totalSupply()` + token0/token1 sanity checks. Total: well within preserved CORRECTIONS-δ free-tier budget.

## §5. Aggregation methodology (W1-W5 invariants embedded)

The aggregator implementation is supply-share-weighted with audit-block-frozen weights, mirroring `aggregation_methodology.md` §2 verbatim. The 5 anti-fishing invariants W1-W5 are embedded in this spec rather than only in the companion file (resolves predecessor RC FLAG-8).

### §5.1 Weight computation — TOKENS only

The aggregator weights apply to TOKENS (rows 1, 4, 5, 6, 7, 8 of the §3 inclusion table) — i.e., entities with their own `totalSupply()`. Rows 2 (Mento V2 BiPool exchange) and 3 (Mento V2 Broker) are SETTLEMENT VENUES that route COPm flows; their events are flow-partition inputs to the per-token panel, not separate aggregator weights.

For each in-scope TOKEN t ∈ {Mento V2 COPm Celo, Minteo COPM Celo, Minteo COPM Polygon, Num nCOP Polygon, Wenia COPW Polygon (if resolved), DLYCOP Polygon (if PASS audit)}:

```
w_t = totalSupply_t(audit_block_chain_t) × decimals_t_normalizer × COPM_USD_anchor / Σ_s (same)
```

Effective token count at v1.5-data execution: 4 confirmed (rows 1, 4, 5, 6) + up to 2 conditional (row 7 Wenia COPW pending PoR-feed probe; row 8 DLYCOP expected W1 velocity-floor exclusion). Worst case (Wenia unresolved + DLYCOP excluded): 4 tokens. Best case: 6 tokens.

Settlement-venue events (rows 2, 3) are routed to per-token partitions: BiPool USDm/COPm swaps map to Mento V2 COPm Celo token's flow; Mento V2 Broker token-traded events map to whichever Mento V2 stable token is the source/destination of the trade.

Weights pinned at:
- `audit_block_celo` = pinned in `audit_block_pin.json` at sub-plan execution time
- `audit_block_polygon` = pinned in `audit_block_pin.json` at sub-plan execution time
- `audit_block_solana` = N/A (Solana excluded per §3)

Audit-block timestamps are sha256-pinned at the moment of computation; `audit_block_pin.json` includes `block_number`, `block_hash`, `block_timestamp_utc` per chain.

### §5.2 Pre-pinned weight invariants (W1-W5)

| Invariant | Pre-pinned value | Modification cost |
|---|---|---|
| **W1 — Velocity floor ε_v** | 0.05 (5% non-zero weeks; below this, w_i := 0) | CORRECTIONS-block + RC + Model QA review |
| **W2 — Sparse-flag floor ε_s** | 0.40 (40% non-zero weeks; below this, sparse_flag = TRUE for affected weeks) | CORRECTIONS-block + RC + Model QA review |
| **W3 — Weight drift threshold ε_w** | 0.25 (25% supply-share drift between audit_block and analysis end; above this, CORRECTIONS-block triggered) | CORRECTIONS-block (any substrate change triggers re-pin) |
| **W4 — Aggregator-NULL trigger** | 50% non-sparse-weight-sum minimum per week; below this, q_t_aggregate(week) = NULL with `aggregator_null_reason = "majority_substrate_sparse"` | CORRECTIONS-block + RC + Model QA review |
| **W5 — Audit-block pinning** | One single block per chain, frozen at sub-plan execution start | NEW audit_block requires CORRECTIONS-block + 3-way review (mirrors v0 audit_block discipline) |

**Cardinal anti-fishing rule** (preserved from `aggregation_methodology.md` §5): weights are computed ONCE at audit_block from `totalSupply()` per substrate; they are NEVER re-tuned after seeing any downstream regression coefficients. Any post-hoc weight adjustment fires `Stage2PathBAggregatorWeightTuningProhibited` typed exception.

### §5.3 Per-week aggregator formula

```
q_t_aggregate(week) =
    Σ_t [ q_t_token(week) × w_t × NOT(sparse_flag_t(week)) ]   if non_sparse_weight_sum ≥ W4
    NULL                                                       otherwise
```

with weights renormalized within the non-sparse subset for that week (i.e., active weights re-sum to 1.0 over the non-sparse tokens). Iteration is over the 4-6 TOKEN set per §5.1, not the full 8-row inclusion set.

### §5.4 Sparse-week handling

Per Phase 1 RC FLAG-F2 finding (Broker non_lp_user sparse 14/136 weeks): aggregator does NOT impute, does NOT interpolate. Three-tier discipline:

1. **Velocity-floor exclusion (W1)**: if `non_zero_week_pct_i < 0.05`, set `w_i := 0` for entire window
2. **Sparse-flag (W2)**: if `0.05 ≤ non_zero_week_pct_i < 0.40`, the substrate's per-week contribution emits `sparse_flag_i = TRUE` for that specific week
3. **Aggregator-NULL (W4)**: if all non-sparse substrates' weights sum to < 50% for a given week, emit `q_t_aggregate(week) = NULL`; downstream methodology treats as missing observation

## §6. USD-equivalence anchor pipeline

Mirrors `aggregation_methodology.md` §3 verbatim, embedded here as load-bearing for v1.5-data:

**Primary anchor**: Banrep TRM (Tasa Representativa del Mercado) — already pinned in Stage-1 chain; canonical and free-tier accessible via Banrep API.

**Backup anchor (for off-Banrep dates)**: Mento V2 BiPool USDm/COPm direct-pair price at exchange-id `0x1c9378bd0973ff313a599d3effc654ba759f8ccca655ab6d6ce5bd39a212943b` (already discovered in Phase 1 Task 1.3.b; see `mento_swap_flow_inventory.parquet`). NOT Mento V3 FPMM USDm/cUSD pool (which is dormant, 0 events).

**Tertiary anchor (sanity-check only, NEVER primary)**: Uniswap V3 Polygon Minteo COPM/USDC pool spot at audit_block.

**Anchor selection rule (deterministic)**:
- For weekday business hours: PRIMARY (Banrep TRM)
- For weekend / Banrep holidays / TRM-API-failure: BACKUP (Mento V2 BiPool spot)
- Tertiary anchor: emitted alongside primary for sanity-check column in panel; never used as primary or backup
- Issuer-self-reported price: NEVER used

## §7. N_INFORMATIVE measurement protocol

Per-venue and aggregate count of weeks with non-zero observable events. Resolves predecessor MQ-BLOCK-1's substrate-side half (the FLOOR threshold itself is DEFERRED to v1.5-methodology since it depends on realized n).

**`n_informative_table.parquet` schema**:

| column | type | description |
|---|---|---|
| `venue_id` | STRING | One row per venue + one row `aggregate` |
| `chain` | STRING | celo / polygon / aggregate |
| `total_weeks_in_window` | INT | Sample window weeks (denominator) |
| `weeks_with_nonzero_events` | INT | Numerator for venue rows |
| `weeks_with_nonzero_non_lp_user` | INT | Subset; load-bearing for v1.5-methodology q_t fit |
| `weeks_with_nonzero_mev_arb` | INT | Subset |
| `weeks_with_nonzero_lp_mint_burn` | INT | Subset; expected 0 for Mento V2 BiPool (no user-LP surface) |
| `weeks_with_active_holders` | INT | Distinct addresses transferring per week |
| `non_zero_week_pct` | FLOAT | weeks_with_nonzero / total_weeks_in_window |
| `velocity_floor_status` | STRING | "PASS" / "MARGINAL" / "EXCLUDED" per W1+W2 |
| `aggregate_weight_at_audit_block` | FLOAT | w_i pinned at audit_block; NULL for `aggregate` row |
| `audit_block_chain` | INT | Frozen audit_block per chain |
| `audit_block_timestamp_utc` | TIMESTAMP | Frozen audit_block timestamp |

**Aggregate row** uses W4 trigger: `weeks_with_nonzero_events` for the aggregate is the count of weeks where `q_t_aggregate(week) ≠ NULL` per W4.

**v1.5-methodology pre-condition**: this file ships before v1.5-methodology authoring begins. v1.5-methodology pins N_INFORMATIVE floor based on aggregate row's realized count.

## §8. AR(1) diagnostic

Emit first-order autocorrelation coefficient on aggregate-flow series; load-bearing for v1.5-methodology bootstrap block-length pinning (resolves predecessor MQ-BLOCK-5 substrate-side input).

**`ar1_diagnostic.json` schema**:

```json
{
  "series_name": "q_t_aggregate_weekly",
  "n_observations": <integer; from n_informative_table aggregate row>,
  "ar1_coefficient": <float in [-1.0, 1.0]>,
  "ar1_se_hac_newey_west": <float; HAC-corrected SE>,
  "ar1_pvalue_two_sided": <float>,
  "ljung_box_q_stat_lag_4": <float>,
  "ljung_box_q_stat_lag_12": <float>,
  "computed_at_audit_block_celo": <int>,
  "computed_at_audit_block_polygon": <int>,
  "computation_method": "OLS-AR(1)-on-non-NULL-aggregate-weeks",
  "computation_sha256": <sha256 of aggregate panel input>
}
```

Methodology: regress `q_t_aggregate(week_t)` on `q_t_aggregate(week_{t-1})` over the subset of non-NULL weeks; report coefficient + HAC SE + Ljung-Box at lags 4 and 12. NO bootstrap at this stage (deferred to v1.5-methodology).

**v1.5-methodology pre-condition**: bootstrap block-length pinned at `1 / (1 - ρ̂)` capped at 26 weeks where `ρ̂` = `ar1_coefficient` from this emission.

## §9. σ-anchor reality assessment

Emit per-anchor informative-weeks count for the three σ-anchor candidates; load-bearing for v1.5-methodology σ-anchor primary specification (resolves predecessor MQ-FLAG-9 substrate-side input).

**`sigma_anchor_coverage.json` schema**:

```json
{
  "banrep_trm": {
    "informative_weeks": <int>,
    "first_week_utc": <date>,
    "last_week_utc": <date>,
    "missing_weeks_count": <int>,
    "free_tier_status": "OK"
  },
  "mento_v2_bipool_usdm_copm_spot": {
    "informative_weeks": <int>,
    "weeks_with_geq_10_swap_events": <int>,
    "first_observation_utc": <date>,
    "last_observation_utc": <date>,
    "free_tier_status": "OK"
  },
  "uniswap_v3_polygon_minteo_usdc_spot": {
    "informative_weeks": <int>,
    "weeks_with_geq_10_swap_events": <int>,
    "first_observation_utc": <date>,
    "last_observation_utc": <date>,
    "free_tier_status": "OK or PENDING"
  }
}
```

**v1.5-methodology pre-condition**: σ-anchor primary pinned based on this emission's informative-weeks counts; whichever anchor has highest coverage with cleanest microstructure becomes primary.

## §10. Output deliverables

| Artifact | Path | Purpose |
|---|---|---|
| `cop_corridor_aggregate_panel.parquet` | `contracts/.scratch/pair-d-stage-2-B/v1_5_data/` | Per-week aggregate flow + per-substrate contributions |
| `n_informative_table.parquet` | same | Per-venue + aggregate informative-weeks count |
| `ar1_diagnostic.json` | same | AR(1) coefficient on aggregate-flow series |
| `sigma_anchor_coverage.json` | same | Per-anchor informative-weeks count |
| `audit_block_pin.json` | same | Frozen audit_block per chain with sha256-pinned timestamps |
| `audit_metrics_raw.json` (5 new venues) | same | Per-venue audit results extending Phase 1 schema |
| `v1_5_data_findings.md` | same | Narrative interpretation; substrate-pivot adjudication input |

Per spec §3.A 8-field provenance entry for every artifact. All artifacts sha256-pinned in `v1_5_data_findings.md` frontmatter.

## §11. Free-tier budget

Preserved from CORRECTIONS-δ:
- SQD Network: 5 req/sec cap; 150-200 requests over sub-plan execution = ~30-40 sec wall time
- Alchemy: 30M CU/mo budget; v1.5-data uses 5-10 CU for `eth_call totalSupply()` + token0/token1 sanity checks per chain × 4 chains = ≤40 CU total
- Forno Celo public RPC: free; used for COPm + Mento Broker corroboration
- Banrep TRM API: free, no rate limit observed
- Solana RPC: N/A (Solana excluded per §3)

Total v1.5-data execution cost: well under 1% of any monthly budget.

## §12. Anti-fishing pre-pinned invariants

| Invariant | Specification |
|---|---|
| **W1** — Velocity floor ε_v = 0.05 | Pre-pinned; modification requires CORRECTIONS-block + RC + Model QA review |
| **W2** — Sparse-flag floor ε_s = 0.40 | Pre-pinned; modification requires CORRECTIONS-block + RC + Model QA review |
| **W3** — Weight drift threshold ε_w = 0.25 | Pre-pinned; substrate change triggers re-pin |
| **W4** — Aggregator-NULL trigger ≥ 0.50 | Pre-pinned; modification requires CORRECTIONS-block + RC + Model QA review |
| **W5** — Audit-block pinning | One block per chain, frozen at sub-plan execution start |
| Substrate scope frozen | 8 in-scope venues per §3 inclusion table; post-commit additions require CORRECTIONS-block |
| Per-venue audit thresholds frozen | PASS / MARGINAL / HALT thresholds in §4 pre-pinned; post-data tuning prohibited |
| USD-anchor selection rule deterministic | Banrep TRM primary; Mento V2 BiPool backup; tertiary sanity-only; issuer-self never used |
| `Stage2PathBAggregatorWeightTuningProhibited` typed exception | Fires on any post-hoc weight adjustment |
| `Stage2PathBPerVenueThresholdTuningProhibited` typed exception | Fires on any post-hoc per-venue audit threshold relaxation |
| `Stage2PathBAggregateSubstrateThinness` typed exception | Fires when aggregate `weeks_with_nonzero_events < 50` (load-bearing pre-condition for v1.5-methodology N_INFORMATIVE floor at 75; this floor itself defers to v1.5-methodology) |

## §13. Pre-commitment invariants (spec-locked)

1. **Substrate scope**: 8 in-scope venues per §3 (rows 1-8); rows 9-10 EXCLUDED (BSC free-tier-coverage / Solana non-EVM); rows 11-12 RESEARCH_PENDING_DISCOVERY (HyperEVM / MegaETH per §3.bis). NO post-data substrate addition without CORRECTIONS-block + 2-wave verify; this includes any HyperEVM/MegaETH token discovered via §3.bis dispatch.

1.bis. **EVM-only chain scope** (per user direction 2026-05-04): only EVM-compatible chains are admissible substrate hosts. Solana / SVM / non-EVM L1/L2s are PERMANENTLY EXCLUDED from v1.5-data and v1.5-methodology aggregator scope. Future-iteration cross-chain non-EVM expansion (e.g., reactivating Solana Minteo) requires explicit CORRECTIONS-block reversing this invariant + 2-wave verify; CANNOT be silent.
2. **Per-venue audit thresholds**: PASS ≥ 1000 events AND ≥ 30% non-zero weeks for non_lp_user; MARGINAL ∈ [100, 1000) events OR ∈ [10%, 30%) non-zero weeks; HALT < 100 events OR < 5% non-zero weeks. NO post-data tuning.
3. **W1-W5 weight invariants**: as pre-pinned in §5.2 + §12. NO post-data tuning.
4. **Audit-block freezing**: one block per chain pinned at sub-plan execution start; frozen via sha256 pin in `audit_block_pin.json`. NO post-data re-pinning unless CORRECTIONS-block fires.
5. **USD-anchor selection rule**: Banrep TRM primary, Mento V2 BiPool spot backup, tertiary sanity-only. NO post-data anchor swap.
6. **AR(1) computation method**: OLS-AR(1) on non-NULL aggregate weeks with HAC SE + Ljung-Box at lags 4 + 12. NO post-data method swap.
7. **σ-anchor reality assessment**: emit per-anchor informative-weeks count for all three candidates regardless of which "wins"; primary selection happens at v1.5-methodology authoring, not here.
8. **Substrate-pivot adjudication block**: NOT resolved in v1.5-data; surfaces at v1.5-methodology authoring with realized aggregate panel as input. Recorded in `v1_5_data_findings.md` as "v1.5-methodology pre-condition: Gate B1 (a)/(b)/(c) substrate-pivot user adjudication required before v1.5-methodology spec finalization."
9. **HALT cascade discipline**: every per-venue HALT outcome routes to a CORRECTIONS-block path with explicit user adjudication. NO silent pivots, NO auto-extensions, NO threshold relaxation post-data.
10. **Decomposition discipline**: methodology choices (3-test gate, AICc/AIC, K-means k-selection, bootstrap method, R-thresholds, thesis-fitness verdict layer) are EXPLICITLY out of scope for v1.5-data. Any in-scope creep into methodology fires `Stage2PathBSpecScopeViolation` typed exception.

## §14. Spec / plan revision footprint

This design is implemented via:

### §14.1 CLAUDE.md framework section update (~30-40 lines)

Rev-5.3.5 "Mento-native ONLY" reversal corrigendum; substrate scope expansion to "aggregate COP-corridor"; references to discovery.md + aggregation_methodology.md + this spec. Substrate-expansion-only scope (NO methodology language).

### §14.2 Parent spec v1.4 → v1.5 (CORRECTIONS-ζ) (~80-100 lines, data-only)

- Frontmatter `on_chain_pins` additions ×5 (Minteo Polygon, Num nCOP Polygon, Wenia COPW Polygon (PENDING), DLYCOP Polygon)
- §1 prose: substrate scope expansion; explicit reference that v1.5-data + v1.5-methodology supersede prior single v1.5 framing
- §3 v1 substrate update: multi-substrate aggregation note pointing to v1.5-data spec
- §4.0 schema additions: `substrate_weight_at_audit_block` column
- §6 typed exceptions: `Stage2PathBAggregateSubstrateThinness`, `Stage2PathBAggregatorWeightTuningProhibited`, `Stage2PathBPerVenueThresholdTuningProhibited`, `Stage2PathBSpecScopeViolation`

### §14.3 Parent plan v1.1 → v1.2 (CORRECTIONS-β') main-plan pointer (~30-40 lines)

- Phase 1.5 placeholder (between Phase 1 and Phase 2 v1) referencing v1.5-data sub-plan
- Phase 2 v1 dependencies unchanged in substance
- Phase 2.5 / Phase 3 dependencies UPDATED to block on Gate B1.5-data PASS (was B1.5)
- v1.5-methodology placeholder between v1.5-data and v2 dispatch — "DEFERRED until v1.5-data execution delivers aggregate panel + n_informative_table + ar1_diagnostic + σ-anchor coverage"

### §14.4 NEW v1.5-data sub-plan (~10-15 tasks, ~400-500 lines)

`contracts/docs/superpowers/sub-plans/2026-05-04-pair-d-stage-2-path-b-v1.5-data-subplan.md`

Sub-phases:
- 14.4.1 Substrate-scope expansion allowlist update + PoR-feed probe for Wenia COPW (~3 tasks)
- 14.4.2 Per-venue audit re-run on 5 new venues (~3 tasks; Polygon SQD endpoint, BSC excluded, Solana excluded per §3)
- 14.4.3 Audit-block pinning + W1-W5 weight computation + aggregator panel build (~3 tasks)
- 14.4.4 N_INFORMATIVE table + AR(1) diagnostic + σ-anchor coverage emissions (~3 tasks)
- 14.4.5 Gate B1.5-data 3-way review + v1_5_data_findings.md authoring (~2 tasks)
- 14.4.6 v1.5-methodology authoring pre-condition checklist (1 task)

### §14.5 Verification gates (per `feedback_two_wave_doc_verification`)

- CLAUDE.md framework update: RC + Workflow Architect in parallel
- Parent spec v1.5 CORRECTIONS-ζ (data-only scope): RC + Workflow Architect in parallel
- Parent plan v1.2 CORRECTIONS-β' main-plan pointer: RC + Workflow Architect in parallel
- v1.5-data sub-plan: RC + Workflow Architect in parallel
- THIS spec (v1.5-data): RC + Model QA Specialist in parallel (queued post-user-review)

### §14.6 Sequencing — data-first

1. CLAUDE.md framework update → 2-wave verify → commit
2. Parent spec v1.5 CORRECTIONS-ζ data-only → 2-wave verify → commit → PR + merge
3. Parent plan v1.2 CORRECTIONS-β' main-plan pointer → 2-wave verify → commit
4. v1.5-data sub-plan → 2-wave verify → commit → PR + merge
5. **EXECUTE v1.5-data sub-plan**: substrate-expansion audits + aggregate panel build + N_INFORMATIVE measurement + AR(1) emission + σ-anchor coverage
6. Gate B1.5-data 3-way review (CR + RC + SD per `feedback_implementation_review_agents`)
7. v1.5-methodology spec authoring UNBLOCKED — author with realized data anchors

## §15. Self-review checklist

- [ ] No placeholders / TBD / TODO outside the explicit `<to-be-pinned-after-recompute>` (line 5 sha sentinel) and `<PENDING_TOKEN_RESOLUTION_VIA_POR_FEED_PROBE>` (Wenia COPW, surfaced at §3 with explicit resolution-pending action)
- [ ] All per-venue audit thresholds (PASS/MARGINAL/HALT) pre-pinned with specific numerical values (§4)
- [ ] All W1-W5 invariants pre-pinned with specific numerical values (§5.2 + §12)
- [ ] HALT cascades route to CORRECTIONS-block paths (no auto-pivot)
- [ ] CORRECTIONS-γ structural-exposure framing preserved (no WTP / behavioral-demand language)
- [ ] Free-tier-only budget pin preserved (CORRECTIONS-δ inheritance) (§11)
- [ ] Stage-1 sha-pin chain READ-ONLY
- [ ] Cross-substrate weights audit-block-frozen per W5
- [ ] No statistical-methodology pre-commits (3-test gate, AIC, K-means, bootstrap, R-thresholds) — all DEFERRED to v1.5-methodology
- [ ] Substrate-pivot adjudication explicit DEFERRAL recorded (§13 invariant 8)
- [ ] N_INFORMATIVE floor itself NOT pinned in this spec (deferred to v1.5-methodology); only the measurement protocol is pinned (§7)
- [ ] AR(1) computation method pinned but bootstrap method NOT pinned (deferred)
- [ ] σ-anchor primary selection NOT pinned (deferred); only per-anchor coverage measurement is pinned (§9)

## §16. Pre-conditions for v1.5-methodology authoring

v1.5-methodology spec authoring is BLOCKED until v1.5-data execution delivers all of:

1. ✗ `cop_corridor_aggregate_panel.parquet` — per-week aggregate flow + per-substrate contributions
2. ✗ `n_informative_table.parquet` — per-venue + aggregate informative-weeks count
3. ✗ `ar1_diagnostic.json` — AR(1) coefficient on aggregate-flow series
4. ✗ `sigma_anchor_coverage.json` — per-anchor informative-weeks count
5. ✗ `audit_block_pin.json` — frozen audit_block per chain with sha256-pinned timestamps
6. ✗ Per-venue augmented `audit_metrics_raw.json` for 5 new venues
7. ✗ `v1_5_data_findings.md` — substrate-pivot adjudication input + Gate B1.5-data 3-way review verdict
8. ✗ Cohort-N empirical floor measurement: how many addresses survive ≥3-transfers filter on aggregate panel
9. ✗ HyperEVM/MegaETH §3.bis discovery report — substrate-scope-amendment input (if positive COP-pegged tokens found, triggers CORRECTIONS-block + 2-wave verify before v1.5-methodology authoring; if null, recorded as "no EVM-emerging substrate addition for this iteration")

When all 8 land, v1.5-methodology authoring resolves the 8 BLOCKs from v1.5-original 2-wave verify (RC-BLOCK-1/2 + MQ-BLOCK-1/2/3/4/5/6) with empirical anchors per CORRECTIONS-η §5 mapping.

End of v1.5-data design.
