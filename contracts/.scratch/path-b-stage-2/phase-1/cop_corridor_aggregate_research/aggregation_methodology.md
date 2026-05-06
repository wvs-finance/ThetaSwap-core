---
artifact_kind: cop_corridor_aggregation_methodology_proposal
spec_ref: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md (v1.4 sha fcebc95f923e1b55fbf2eaa22239b00bbde4a9f35bb031e8f32d090a4fb80d95)
plan_ref: contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md (v1.1 sha 7e2f43c211a314475c3fc2ef5890c268c7216efa55b0b7a9d2c8e5d8d95bca6b)
parent_task: Aggregate COP-corridor substrate methodology proposal
emit_timestamp_utc: 2026-05-04
constraints:
  - Anti-fishing — weights pre-pinned, not post-data tuned
  - Free-tier ONLY for any methodology that runs computation
  - Compatible with existing v0 BLOCK-B1 schema; minimal column additions
  - CORRECTIONS-γ structural-exposure framing preserved
---

# Aggregation Methodology — COP-corridor Aggregate Substrate

## §1. Objective

Combine N=4-5 independently-issued COP-pegged stablecoin substrates into a SINGLE r_(a_l)-equivalent aggregate measure for Pair D Stage-2 Path B v1 reconstruction, while preserving:

1. **Anti-fishing discipline** — weights pre-pinned at audit_block, not retro-fitted to a desired regression outcome.
2. **CORRECTIONS-γ structural-exposure framing** — no WTP / behavioral-demand inference; aggregator measures observable on-chain quantities (supply, transfer notional, mint/burn flow) only.
3. **Schema compatibility** — fits in the existing v0 `venue_id` partition + `audit_summary` Parquet (BLOCK-B1) with at most 1 added column.
4. **Provenance discipline per spec §3.A** — every weight + every USD-anchor decision is traceable to a pre-pinned source.

## §2. Method Class — Supply-Share-Weighted Panel

Among the candidate methods (equal-weight, supply-weighted, volume-weighted, holder-weighted), the chosen method is **supply-share-weighted with frozen audit-block weights**, justified as follows:

| Method | Pro | Con | Verdict |
|---|---|---|---|
| Equal-weight (1/N) | Simple, anti-fishing-clean | Inflates dormant DLYCOP / Solana SPL substrates to same level as $200M-volume Minteo Polygon | REJECT |
| Volume-weighted | Mirrors flow-magnitude reality | Volume is itself the dependent variable for the r_(a_l) reconstruction → endogenous weighting fishes the outcome | REJECT — anti-fishing ban |
| Holder-weighted | Attractive demographic interpretation | Holder data is most-divergent across explorers (DLYCOP shows 12K vs 113K from same explorer); free-tier accuracy too poor | REJECT |
| **Supply-weighted (audit-block-frozen)** | **Exogenous to volume; reflects committed-issuance stake; observable cleanly via `totalSupply()` at single block** | **Treasury-held supply over-represents; partially mitigated by velocity-floor exclusion** | **ACCEPT** |

**Formal definition:**
- For each substrate i ∈ {Mento V2 COPm Celo, Minteo Celo, Minteo Polygon, nCOP Polygon, COPW Polygon (if resolved)}:
  - w_i = totalSupply_i(audit_block) × decimals_i_normalizer × COPM_USD_anchor / Σ_j (same)
- Weights pinned at audit_block_celo = 65915058 (or updated audit-block per CORRECTIONS-ζ).
- Pre-aggregation velocity-floor exclusion: any substrate with <5% non-zero weeks over the analysis window is excluded entirely (w_i := 0); this excises DLYCOP-class artifacts.
- Sparse-week handling: for substrates passing velocity-floor but with <40% non-zero weeks, the per-week aggregator emits `aggregate_weight_i = 0` for that specific week (with `sparse_flag = TRUE`) rather than imputing.

## §3. USD-Equivalence Anchor

**Primary anchor:** Banrep TRM (Tasa Representativa del Mercado) — already pinned in Stage-1 chain; canonical and free-tier accessible via Banrep API.

**Backup anchor (for substrates without TRM coverage):** Mento V2 BiPool USDm/COPm direct-pair price at the exchange-id `0x1c9378bd…` (already discovered in Phase 1 Task 1.3.b; see `mento_swap_flow_inventory.parquet`). NOT Mento V3 FPMM USDm/cUSD pool (which is dormant, 0 events).

**Tertiary anchor (sanity-check):** Uniswap V3 Polygon Minteo COPM/USDC pool spot at audit_block.

**Anchor selection rule (deterministic):** prefer Banrep TRM where available; fall back to Mento V2 BiPool spot ONLY for off-Banrep dates (weekend, holidays); never fall back to issuer-self-reported price.

## §4. Sparse-Week Handling (per Reality Checker FLAG-F2 from Gate B1)

RC FLAG-F2 noted: "Broker non_lp_user sparse (14 of 136 weeks nonzero); Phase 3 q_t generator must accommodate." This pattern recurs across all individual substrates and is the primary motivation for aggregation.

**Per-substrate sparseness mitigation in aggregator:**

1. **Compute `non_zero_week_pct_i = nonzero_weeks_i / total_analysis_weeks`** for each substrate at audit_block.
2. **Velocity-floor exclusion (ε_v = 0.05):** if non_zero_week_pct_i < 0.05, set w_i := 0 (substrate excluded entirely; DLYCOP-class).
3. **Sparse-flag (ε_s = 0.40):** if 0.05 ≤ non_zero_week_pct_i < 0.40, the substrate's per-week contribution emits `sparse_flag = TRUE` for that week's row.
4. **Aggregate per-week formula:** `q_t_aggregate(week) = Σ_i (q_t_i(week) × w_i × NOT(sparse_flag_i))` — sparse-flagged contributions zeroed, weights renormalized within the non-sparse subset for that week.
5. **Aggregator-NULL trigger:** if all non-sparse substrates' weights sum to <50% of frozen weights for a given week, emit `q_t_aggregate(week) = NULL` with `aggregator_null_reason = "majority_substrate_sparse"`. Downstream regression treats this as missing observation, not zero.

This three-tier (velocity-floor / sparse-flag / aggregator-NULL) discipline ensures the aggregator does not silently impute and does not silently up-weight thin substrates.

## §5. Anti-Fishing Safeguards (PRE-COMMITMENT INVARIANTS)

The methodology relies on FIVE pre-pinned invariants. Modifying any invariant requires a CORRECTIONS-block + 3-way review, mirroring the Phase-A.0 N_MIN-relaxation protocol.

| Invariant | Pre-pinned value | Modification cost |
|---|---|---|
| **W1 — Velocity floor ε_v** | 0.05 (5% non-zero weeks) | CORRECTIONS-block + RC + SD review |
| **W2 — Sparse-flag floor ε_s** | 0.40 (40% non-zero weeks) | CORRECTIONS-block + RC + SD review |
| **W3 — Weight drift threshold ε_w** | 0.25 (25% supply-share drift) | CORRECTIONS-block (any substrate change triggers re-pin) |
| **W4 — Aggregator-NULL trigger** | 50% non-sparse-weight-sum minimum | CORRECTIONS-block + RC + SD review |
| **W5 — Audit-block pinning** | One single block per chain, frozen | NEW audit_block requires CORRECTIONS-block + 3-way review (mirrors v0 audit_block discipline) |

**The cardinal anti-fishing rule:** weights are computed ONCE at audit_block from `totalSupply()` per substrate; they are NEVER re-tuned after seeing the regression coefficients. Any post-hoc weight adjustment fires `Stage2PathBAggregatorWeightTuningProhibited` typed exception.

## §6. Provenance Discipline (per spec §3.A)

For each cell in the per-week aggregator panel, the audit trail is:

- `aggregator_q_t_value` (final cell value)
- `substrates_in_aggregator_for_this_week` (list of i where w_i > 0 ∧ NOT sparse_flag_i)
- `weight_renormalization_applied_this_week` (boolean — TRUE if some substrates were sparse-flagged and weights re-normalized)
- `aggregator_null_reason` (NULL if cell is non-NULL; else one of {"majority_substrate_sparse", "no_audit_block_data", ...})
- `usd_anchor_source_this_week` (one of {"banrep_trm", "mento_v2_bipool_spot", "fallback"})
- `provenance_root_audit_metrics_raw_sha256` (sha256 of per-substrate `audit_metrics_raw.json` rows used to derive this cell)

This provides full per-cell provenance, traceable back to per-substrate raw event counts.

## §7. Worked Example

Consider three weeks of analysis at audit_block_celo = 65915058 with 4 active substrates (Mento V2 COPm, Minteo Celo, Minteo Polygon, nCOP Polygon). Assume DLYCOP and Wenia COPW are not yet included.

**Pre-pinned weights at audit_block (illustrative; actual values depend on real `totalSupply()` reads):**

```
Substrate                    | totalSupply  | × USD-anchor    | Weight (post-norm)
-----------------------------|--------------|-----------------|-------------------
Mento V2 COPm (Celo)         |    181M COPM | × $0.000277 USD | $50K notional → w_1 = 0.06
Minteo COPM (Celo)           |   1000M COPM | × $0.000277 USD | $277K notional → w_2 = 0.32
Minteo COPM (Polygon)        | (assume similar 800M for example) | $222K notional → w_3 = 0.26
Num Finance nCOP (Polygon)   |    180M nCOP | × $0.000277 USD | $50K notional → w_4 = 0.06
                                                              | renormalize → w_1=0.087, w_2=0.464, w_3=0.377, w_4=0.072
```

(Numbers above are illustrative — actual values pinned at re-dispatch via `eth_call totalSupply()` per substrate at audit_block.)

**Week 1: All 4 substrates active (non-zero events)**
- q_t_aggregate(week1) = 0.087 × q_t_MentoV2(w1) + 0.464 × q_t_MinteoCelo(w1) + 0.377 × q_t_MinteoPoly(w1) + 0.072 × q_t_nCOP(w1)

**Week 2: nCOP sparse-flagged (this week's events = 0, but non_zero_week_pct_4 = 0.30 > velocity-floor)**
- Active weights = {w_1, w_2, w_3} = {0.087, 0.464, 0.377}; renormalize over active = {0.094, 0.500, 0.406}
- q_t_aggregate(week2) = 0.094 × q_t_MentoV2(w2) + 0.500 × q_t_MinteoCelo(w2) + 0.406 × q_t_MinteoPoly(w2)
- Emit row with `sparse_flag_nCOP = TRUE, weight_renormalization_applied = TRUE`

**Week 3: nCOP + MentoV2 both sparse-flagged. Active sum = 0.464 + 0.377 = 0.841 ≥ 0.50 (above aggregator-NULL trigger)**
- Active weights = {w_2, w_3} renormalize to {0.552, 0.448}
- q_t_aggregate(week3) computed
- Emit row with `sparse_flag_nCOP = TRUE, sparse_flag_MentoV2 = TRUE, weight_renormalization_applied = TRUE`

**Hypothetical Week 4: 3 of 4 substrates sparse, active sum = 0.377 < 0.50 (BELOW aggregator-NULL trigger)**
- q_t_aggregate(week4) = NULL
- Emit row with `aggregator_null_reason = "majority_substrate_sparse"`

The downstream regression treats Week 4 as a missing observation (drop from sample), Week 2/3 as valid observations with the per-week-renormalized aggregator value.

## §8. Compatibility with Path A

Path A (`r_al_handoff.json`) consumes Path B's r_(a_l) reconstruction. The aggregate-substrate methodology produces a **single** r_(a_l) time-series identical in shape to the prior Mento-native-only series; only the per-cell value is now an aggregate. Path A's cross-handoff contract (schema, provenance fields) is unchanged.

## §9. Compatibility with v0 BLOCK-B1 Schema

The existing per-venue `audit_summary.parquet` Parquet schema accommodates per-substrate aggregator inputs natively via the `venue_id` partition. Aggregation produces a NEW Parquet artifact:

- `aggregate_audit_summary.parquet` — one row per week, columns:
  - `week_start_utc` (DATE)
  - `q_t_aggregate` (FLOAT)
  - `substrates_in_aggregator` (ARRAY<STRING>)
  - `weight_renormalization_applied` (BOOL)
  - `aggregator_null_reason` (STRING, nullable)
  - `usd_anchor_source` (STRING)
  - `audit_block_celo`, `audit_block_polygon`, `audit_block_solana` (INT64, frozen)
  - `provenance_root_audit_metrics_raw_sha256` (STRING)

This is a NEW artifact, parallel to the existing `audit_summary.parquet` (per-substrate) and `mento_swap_flow_inventory.parquet` (per-pool partition). The existing artifacts are retained unchanged.

## §10. Estimated Free-Tier Cost for Aggregator Implementation

- 5-6 new substrate audits × 134 weeks × 3 partition rows (non_lp_user / mev_arb / lp_mint_burn) ≈ 2,000-2,500 new rows.
- SQD Network coverage: Polygon + Celo (already covered for Mento); Solana NOT covered (defer Solana substrate per §1 priority assessment).
- Estimated SQD requests: 30-40 chunks × 5 substrates = 150-200 requests over Phase 1 re-execution.
- Estimated Alchemy CU: 5-10 CU for `eth_call totalSupply()` × 5 substrates × audit_block per chain.
- Total: well within the project's existing free-tier budget (peak SQD 3.75 req/s under 5/s cap was observed in original Phase 1; this re-run is comparable or smaller).

## §11. Risk Assessment

| Risk | Mitigation | Residual |
|---|---|---|
| Wenia COPW token address unfindable | HALT-and-surface at Phase 2 Task 2.1; aggregator can run with 4 substrates if 5th fails | LOW |
| Minteo Polygon $200M monthly volume self-reported, not on-chain-verified | Direct Uniswap V3 COPM/USDC pool query at audit_block + monthly aggregation | MEDIUM |
| Cross-chain Minteo COPM Celo+Polygon supply double-counted (bridge between them) | No public bridge attested as of 2026-05; treat as separate substrates; audit at re-dispatch for any bridge events | LOW |
| Solana SPL substrate excluded shrinks aggregate by ~20-30% | Acceptable per W3 (weight drift); Solana inclusion requires independent data-pipeline branch | LOW (acceptable scope reduction) |
| Issuer-mint EOA unattributable for Minteo / nCOP / Wenia | Use `Mint`/`Burn` event signatures + Transfer-from-zero / Transfer-to-zero pattern; Wenia uniquely has Chainlink-PoR-gated mint | LOW |
| Aggregator weight drift exceeds 25% during analysis window | CORRECTIONS-block fires; user-adjudicated re-weighting at next audit_block | EXPECTED-AND-HANDLED |

End of aggregation_methodology.md.
