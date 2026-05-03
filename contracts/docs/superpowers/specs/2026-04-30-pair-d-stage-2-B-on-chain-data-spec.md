---
spec_path: pair-d-stage-2-B-on-chain-data
spec_version: v1.4 (CORRECTIONS-ε — synthetic counterfactual reframe per a_s on-chain entity
  non-existence; Path B v2 reframed from on-chain a_s extraction (impossible) to synthetic
  Δ^(a_s) generation under pre-pinned q_t schedule families; Path A v3 σ-distribution handoff
  promoted from OPTIONAL to NORMATIVE input)
spec_predecessor_version: v1.3 (CORRECTIONS-γ behavioral-demand → structural-exposure rename;
  sha256 `4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea`)
spec_predecessor_chain:
  v1_0: 7af22dd4f95324d777639d509f782efe41560469e29ca037f65c8940c0ee6997
  v1_1: c4fa24369485f107da7b26531b3771aa3f4cd824a457b69d19d1b779c4ea0714
  v1_2: b3b41e3042cf91563977e6c0222cfe75d8b293d9b4379758a5721b090420c42c
  v1_2_1: 86830209130b7833cb820531add8851513cf4831dc9a60b19c73bf7c076f4a17
  v1_3: 4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea
spec_author: Data Engineer dispatch 2026-04-30 (v1.0); Data Engineer dispatch 2026-05-02 (v1.1);
  Data Engineer dispatch 2026-05-02 (v1.2 — CORRECTIONS-δ);
  foreground micro-edit 2026-05-02 (v1.2.1 — CORRECTIONS-δ' per Wave-2 verifier NITs N1+N2);
  Data Engineer dispatch 2026-05-02 (v1.3 — CORRECTIONS-γ behavioral-demand →
  structural-exposure rename per anticipated-rename inventory);
  Data Engineer dispatch 2026-05-03 (v1.4 — CORRECTIONS-ε synthetic-counterfactual reframe
  per SYNTHESIS.md §8 user-decision OPTION 3; on_chain_pins overhaul; §1/§2/§3/§4/§6/§8
  substantive revision)
spec_sha256: <to-be-pinned-after-recompute>
stage1_pinned_chain:
  spec_v1_3_1: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
  panel: 6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf
  primary_ols: d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf
  robustness_pack: 67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904
  verdict: 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf
synthesis_memo_pin:
  path: contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/SYNTHESIS.md
  commit_sha: e25131cd2
  load_bearing_finding: "Abrigo is an a_s-INSTANTIATING product, not an a_s-hedging product.
    The CPO cannot be sold into an existing on-chain a_s population because that population
    doesn't exist on-chain. Product must DEPLOY the a_s side simultaneously."
on_chain_pins:
  # ── a_l side substrates (NORMATIVE; all addresses verified via prior allowlist research) ─
  mento_v3_router_celo: "0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6"
  mento_v2_bipool_manager_celo: "0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901"
  mento_v2_copm_celo: "0x8A567e2aE79CA692Bd748aB832081C45de4041eA"
  mento_v2_usdm_celo: "0x765DE816845861e75A25fCA122bb6898B8B1282a"
  mento_broker_celo: "0x777A8255cA72412f0d706dc03C9D1987306B4CaD"
  mento_v3_fpmm_usdm_cusd_pool_celo: "0x462fe04b4FD719Cbd04C0310365D421D02AaA19E"
  panoptic_factory_ethereum: "<to-be-pinned-at-v0-audit-closure>"
  # ── Architectural template (NOT a substrate; methodology reference only) ─
  impact_market_microcredit_celo: "0xEa4D67c757a6f50974E7fd7B5b1cc7e7910b80Bb"
  # ── DEPRECATED in v1.4 (preserved for predecessor-chain audit; do NOT consume) ─
  bitgifty_settlement_celo: "DEPRECATED_v1_4 (no smart contracts deployed; Tatum API custody
    per SYNTHESIS.md §3.1; consumer-rail-operator archetype confirmed off-chain across
    4 research tracks)"
  walapay_settlement_celo: "DEPRECATED_v1_4 (closed source; Dfns MPC custody; no Celo
    deployment; no Mento integration per SYNTHESIS.md §3.1)"
  mento_v3_fpmm_usdm_copm_pool_celo: "DEPRECATED_v1_4 (pool does not exist in Mento V3
    deployment manifest; canonical USDm/COPm direct exchange is the V2 BiPool path
    routed via mento_v2_bipool_manager_celo, not a Mento V3 FPMM pool)"
  uniswap_v3_usdc_usdm_pool_celo: "DEPRECATED_v1_4 (mis-named placeholder; canonical
    USD/USDm liquidity surface on Celo is Mento V3 FPMM USDm/cUSD pool routed at
    mento_v3_fpmm_usdm_cusd_pool_celo, not a Uniswap V3 pool)"
  uniswap_v3_factory_celo: "DEPRECATED_v1_4 (Uniswap V3 USD/USDm Celo pool reference
    retired with the mis-named placeholder above; v1.4 a_l substrate is Mento-native only)"
on_chain_pins_a_s_note: "Per SYNTHESIS.md §8.1 (user decision 2026-05-03), no on-chain a_s
  entity exists in any LATAM corridor researched. The a_s side of the CPO is generated
  SYNTHETICALLY in v2 per the §3.B / §4.0 a_s_counterfactual schema methodology, NOT
  extracted from on-chain transaction history. v1.4 deliberately does NOT pin any
  on-chain a_s entity addresses; doing so would re-introduce the v1.0-v1.3 false-positive
  pattern (Bitgifty / Walapay placeholder pre-pinning produced 2/2 false-positive rate per
  SYNTHESIS.md §3.1 anti-fishing log entry)."
budget_pin: free_tier_only
budget_pin_provenance: 2026-05-02 user directive — supersedes v1.1's $49/mo Alchemy Growth
  pin; no paid services authorized; any escalation to paid tier requires typed-exception
  with HALT-and-ask-user disposition
tooling_budget_committed: free-tier only (no paid services); SQD Network public gateways +
  Alchemy free tier (30M CU/mo, 25 req/sec, 500 CU/sec rolling-window cap) + Dune free
  tier (~2500 credits/mo, 15-40 rpm per endpoint class) + The Graph hosted-service free +
  public Celo/Ethereum RPC fallbacks (rate-limited)
tooling_budget_pending: false
primary_data_path_v1_2: SQD Network public gateway (free; observed rate limit
  50 req / 10s per IP per docs.sqd.ai 2025-02-23 notice) for bulk archive extraction;
  Alchemy free tier (30M CU/mo, 25 req/sec) for spot RPC + receipts under batched +
  rate-limited execution discipline per §5.A; The Graph hosted-service for typed-event
  subgraphs where coverage exists; Dune free tier (~2500 credits/mo, 15-40 rpm) for
  ad-hoc analytical queries against pre-existing community datasets; public RPCs
  (forno.celo.org, eth.llamarpc.com, rpc.ankr.com/eth) as flaky fallback only with §6
  consistency-degraded typed exception
free_tier_quota_observations_2026_05_02:
  alchemy_free_cu_per_month: 30000000
  alchemy_free_rate_limit_req_per_sec: 25
  alchemy_free_rolling_cu_per_sec: 500
  alchemy_free_celo_support: "all mainnets and testnets per alchemy.com/pricing as of
    2026-05-02; v0 audit re-verifies Celo presence in Alchemy chain directory at session
    start"
  dune_free_credits_per_month: 2500
  dune_free_credits_per_month_source: "the 2500/mo number is the dispatch-brief reference;
    docs.dune.com/api-reference/overview/billing does NOT publish a numeric monthly cap on
    the free tier (verified 2026-05-02); only documented numeric limits are 15 rpm
    (low-limit endpoints) + 40 rpm (high-limit endpoints) per
    docs.dune.com/api-reference/overview/rate-limits; the 2500-credit figure is therefore
    a working assumption inherited from the dispatch brief and is re-verified at v0 entry
    via dashboard inspection"
  sqd_network_documented_rate_limit: "50 requests per 10 seconds per IP per
    docs.sqd.ai/subsquid-network/reference/networks/ 2025-02-23 notice; documentation
    indicates higher bandwidths via public network expanding but no stricter or looser
    limit published as of 2026-05-02 verification"
  the_graph_hosted_service_free: "free for pre-existing subgraphs; no monthly cap
    published; informal rate limits apply"
  observation_method: "WebFetch on 2026-05-02 against alchemy.com/pricing,
    alchemy.com/docs/reference/throughput, docs.dune.com/api-reference/overview/billing,
    docs.dune.com/api-reference/overview/rate-limits,
    docs.sqd.ai/subsquid-network/reference/networks/"
  delta_vs_v1_1_assumed: "v1.1 §5.A projected against $49/mo Alchemy Growth (49M CU/day
    ≈ 1.47B CU/month). v1.2 free-tier cap is 30M CU/MONTH (49× tighter). Projection in
    §5.A re-derived; v1 + v2 projected ~165K-285K CU/month total stays inside cap with
    >100× headroom, but the burst rate (25 req/sec) becomes the binding constraint, not
    monthly CU. Burst-rate analysis added as §5.A sub-clause."
internal_ladder: v0 (data audit) → v1 (CF^a_l) → v2 (CF^a_s) → v3 (CPO backtest)
convergence_point: v3 realized P&L envelope check on Path A v3 MC bounds
verifier_v1_wave1: pending (re-run on v1.2)
verifier_v1_wave2: pending (re-run on v1.2)
corrections_gamma_status: EXECUTED in v1.3 — deliverable framing renamed throughout from
  "behavioral demand" / "willingness-to-pay" to "structural exposure" (cash-flow geometry
  yielding |Δ^(a_l)| and |Δ^(a_s)| in $-notional that the CPO would neutralize on observed
  transaction flows). Transaction archaeology cannot infer WTP for an instrument that does
  not yet exist in the market; existing transactions describe equilibrium under the option
  set without the CPO, so the inference would be broken. Behavioral demand / WTP is a
  Stage-3 (deployment) question, outside Path B's Stage-2 scope. The Stage-2 ideal-scenario
  clause (per project CLAUDE.md "Instrument family" paragraph) authorizes assuming
  liquidity / market exists; estimating behavioral demand at Stage-2 is the Phase-A.0
  stage-drift failure mode and is anti-fishing-banned. v1.3 is a prose-rename pass only —
  no schema, methodology, typed-exception, or quota changes; the underlying ladder still
  produces |Δ^(a_l)| and |Δ^(a_s)| as v1.0 → v1.2.1 always did.
corrections_epsilon_status: EXECUTED in v1.4 — Path B v2 reframed from on-chain a_s
  extraction (impossible per SYNTHESIS.md §8.1; no on-chain a_s entity exists in any
  LATAM corridor researched) to SYNTHETIC COUNTERFACTUAL generation. v2 now produces a
  simulated Δ^(a_s) trace under (a) historical Mento V3 / V2 swap flows (real, observable),
  (b) pre-pinned q_t schedule families enumerated in §3.B (parametric; no post-hoc fitting),
  (c) observed COP/USD path (Banrep TRM + Mento V3 spot per FLAG-B4 ladder). The CPO's
  K_l = K_s equilibrium check at v3 becomes a SIMULATED equilibrium under each q_t schedule,
  not an empirical measurement of two existing parties. Path A v3 σ-distribution handoff
  promoted from OPTIONAL to NORMATIVE input to v2 synthetic counterfactual (allowing
  scenario-replay over Path A's simulated FX paths). LVR (Milionis-Moallemi-Roughgarden 2022)
  acknowledged: LP NET = short variance; Path B v1's CF^(a_l) reconstruction models LP gross
  fee income (∝ |ΔFX|) which is the observable empirical anchor; LP impermanent-loss
  characterization is separately derivable from the v1 panel and is not in the v1 critical
  path. Substantive scope: frontmatter on_chain_pins overhaul (DEPRECATE 4 placeholders;
  ADD 6 verified addresses); §1 framing redefinition (a_l characterization on-chain + a_s
  synthetic counterfactual); §2 ladder semantic update (v2 reframed; v3 equilibrium check
  simulated); §3 Inputs revision (a_s side inputs are pre-pinned q_t families + observed
  paths + historical flows); §3.B NEW SECTION q_t schedule family pre-commitment; §4.0
  schema additions (a_s_counterfactual.parquet); §6 typed-exception inventory updated
  (DEPRECATE Stage2PathBASOnChainSignalAbsent; ADD Stage2PathBSyntheticDriftBeyondTolerance);
  §8 cross-path handoff promotes A→B σ-distribution to NORMATIVE input. Anti-fishing
  preservation: q_t schedule families MUST be pre-committed in spec text; sensitivity
  sweep over the family is mandatory; new typed exception fires if q_t-choice dominates
  signal. v1.0 → v1.3 BLOCK-B1/B2/B3 closures and FLAG-B1 through FLAG-B9 closures
  PRESERVED with substrate references updated to a_l-side only (FLAG-B2 q_t source
  reframed from on-chain settlement-leg observation to pre-pinned synthetic schedule;
  FLAG-B4 reference-price ladder unchanged; FLAG-B7 allowlist discipline unchanged but
  scoped to a_l-side only). CORRECTIONS-γ structural-exposure framing PRESERVED (synthetic
  Δ^(a_s) is structural-exposure characterization under hypothetical-but-pre-committed
  q_t schedules, NOT WTP). CORRECTIONS-δ free-tier-only budget pin PRESERVED verbatim
  (synthetic generation is local Python compute, ZERO RPC calls; v0 + v1 unchanged
  free-tier budget). CORRECTIONS-δ' Alchemy 30M CU/mo correction PRESERVED.
lvr_acknowledgment_v1_4: "Per Milionis-Moallemi-Roughgarden 2022 (Loss-Versus-Rebalancing,
  ACM EC 2024), the LP NET position in a CFMM with respect to a single underlying asset
  is structurally SHORT VARIANCE: LP NET = LP gross fee income − LVR cost where
  LVR > 0 ∝ instantaneous σ². Path B v1's CF^(a_l) reconstruction models the LP GROSS
  FEE INCOME side (proportional to |ΔFX| via the framework's `r·|FX_t − FX_{t-1}|`
  shape); this is the observable empirical anchor that v1 measures and emits to Path A
  v3 via r_al_handoff.json. The LP IL (impermanent loss / LVR) cost is decomposable from
  the same v1 panel (per-Mint/Burn-event reserve snapshots + spot-price path) but is NOT
  in the v1 critical path under v1.4 — it is a derived sensitivity available for v3
  characterization if needed. The v1.4 reframe DOES NOT reposition the a_l side as
  short-variance; it acknowledges that the LP's net economic position is short-variance
  while v1's empirical extraction targets the long-σ-flavored gross-fee component the
  framework's CF^(a_l) definition isolates."
---

# Pair D — Stage-2 Path B — On-Chain Data Empirical-Validation Spec

## Change Log v1.3 → v1.4 (CORRECTIONS-ε)

This revision integrates the unified synthesis of four parallel research tracks committed
2026-05-02 → 2026-05-03 (Bitgifty / Walapay code archaeology, discovery sweep, category-(ii)
deep-dive, category-(iv) discovery), recorded at
`contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/SYNTHESIS.md` (commit
`e25131cd2`). The driving finding is **load-bearing and architectural**: per SYNTHESIS.md
§8.1 (user decision 2026-05-03), *no on-chain a_s entity exists in any LATAM corridor
researched.* The DRAFT.md simplified two-party model — in which a_s is a payment-rail
operator with a fixed B_T obligation in local currency, sourced from Y reserves, on an
on-chain treasury — does not have an empirical referent. Consumer-rail operators (Bitgifty,
Walapay, Pretium, Kotani Pay, Fonbnk, Yellow Card) settle off-chain via Tatum API custody
or MPC (SYNTHESIS.md §3.1). Tokenized-fiat issuers (MXNB / Juno, BRL1 consortium, wARS /
Ripio) hold one-sided local-currency reserves and have no FX exposure on the issuer's books
(SYNTHESIS.md §3.2). The category-(ii) architectural correction — that the a_s could be
relocated to the AMM-LP level (e.g., MXNB/USDC LP) — was REJECTED by the user 2026-05-03
under SYNTHESIS.md §8 because LP NET is structurally **short variance** per LVR
(Milionis-Moallemi-Roughgarden 2022 LVR), making LP positions a_l-flavored not a_s-flavored;
and Aave V3 USDm is decoupled from FX entirely.

The user's load-bearing inference (SYNTHESIS.md §8.1): **Abrigo is an a_s-INSTANTIATING
product, not an a_s-hedging product.** The CPO cannot be sold into an existing on-chain
a_s population because that population doesn't exist on-chain. The product must DEPLOY the
a_s side simultaneously — a vault that accepts Y-stable deposits from wage earners, creates
a fixed-T X-denominated obligation (commits to delivering COPm monthly per a pre-committed
schedule), acts as the a_s itself (vault operator sources COP from USD reserves over time),
buys CPO Π hedge from the LP side (a_l) to neutralize FX vol exposure, and charges margin
to the wage earner with the CPO premium funding the LP-side counterparty. This matches the
project CLAUDE.md "premium-funded ratchet (self-LBM)" framing: the instrument doesn't
merely hedge an existing position, it CREATES the position that gets hedged.

The user-picked refinement (SYNTHESIS.md §8.2): **OPTION 3 — synthetic counterfactual
generation.** Path B v2 reframes from on-chain a_s extraction (impossible) to simulation
of Δ^(a_s) under (a) historical Mento V3 / V2 swap flows (real, observable; 2023-08 →
present, 134 weekly observations), (b) parametric q_t schedule families pre-committed in
spec text and enumerated in the new §3.B, (c) observed COP/USD path (Banrep TRM + Mento
on-chain spot per the existing FLAG-B4 ladder). The output is simulation, NOT measurement.
Anti-fishing posture: q_t schedules pre-committed before observation; sensitivity sweep
over the pre-pinned schedule families is mandatory; the new typed exception
`Stage2PathBSyntheticDriftBeyondTolerance` fires if the schedule choice is dominating the
signal, indicating non-robustness.

**Per-section delta surface (substantive prose revision, not micro-edit):**

1. **Frontmatter `on_chain_pins` overhaul.** DEPRECATE (with reason strings preserved
   for predecessor-chain audit; do NOT consume): `bitgifty_settlement_celo`,
   `walapay_settlement_celo`, `mento_v3_fpmm_usdm_copm_pool_celo`,
   `uniswap_v3_usdc_usdm_pool_celo`, `uniswap_v3_factory_celo`. ADD (a_l side, all
   addresses verified via prior allowlist research per SYNTHESIS.md §5.1):
   `mento_v2_bipool_manager_celo`, `mento_v2_usdm_celo`, `mento_broker_celo`,
   `mento_v3_fpmm_usdm_cusd_pool_celo`. ADD (architectural template only, NOT a substrate):
   `impact_market_microcredit_celo` for q_t aggregation methodology reference. NEW
   frontmatter field `on_chain_pins_a_s_note` explicitly declares no on-chain a_s entity
   addresses are pinned and explains why; this is anti-fishing-load-bearing because
   re-introducing speculative a_s placeholders would re-create the v1.0-v1.3
   false-positive pattern (Bitgifty / Walapay placeholders produced 2/2 false positive
   per SYNTHESIS.md §3.1 anti-fishing log entry).

2. **Frontmatter NEW fields.** `synthesis_memo_pin` records the SYNTHESIS.md path,
   commit sha, and the load-bearing finding verbatim. `corrections_epsilon_status`
   documents the EXECUTED status, scope, anti-fishing preservation, BLOCK / FLAG
   no-regression assertion, and the LVR acknowledgment cross-reference.
   `lvr_acknowledgment_v1_4` records the Milionis-Moallemi-Roughgarden 2022 LVR result
   verbatim and pins how Path B v1 relates to it (v1 measures the LP GROSS FEE INCOME
   side proportional to |ΔFX|; LP IL is decomposable from the same v1 panel but not in
   the v1 critical path under v1.4).

3. **§1 framing redefinition (NORMATIVE).** Path B's deliverable is rewritten as
   **"a_l characterization (on-chain, observable) + a_s synthetic counterfactual
   (simulated)."** The CPO's K_l = K_s equilibrium becomes a SIMULATED equilibrium
   under each q_t schedule, not an empirical measurement of two existing parties. New
   normative paragraph acknowledges that Abrigo is an a_s-instantiating product per
   SYNTHESIS.md §8.1 and that Stage-2 quantifies the addressable structural exposure
   that the CPO would neutralize once the a_s vault is deployed in Stage-3. New
   normative paragraph on LVR (LP NET = short variance; v1 measures gross-fee
   long-σ-flavored component; LP IL separately characterized).

4. **§2 ladder semantics rewrite (NORMATIVE).** v0 and v1 unchanged in spirit (data-
   coverage audit + a_l reconstruction respectively); v2 reframed to synthetic
   generation under pre-pinned q_t schedule families with observed COP/USD path and
   historical Mento swap flow inventory; v3 updated such that Π(σ_T) replays against
   synthetic Δ^(a_s) plus observed Δ^(a_l), and the K_l = K_s equilibrium check becomes
   simulated. Path A v3 σ-distribution handoff promoted from OPTIONAL to NORMATIVE input
   to v2.

5. **§3 Inputs revision.** a_l side inputs (on-chain) re-pinned to the v1.4 substrate
   set: Mento V3 router + Mento V2 broker + Mento V3 USDm/cUSD FPMM pool + Mento V2
   BiPool COPm exchange routed via the BiPool manager. a_s side inputs (synthetic):
   pre-pinned q_t schedule families enumerated in §3.B; observed COP/USD path (Banrep
   TRM + Mento V3 spot via Stage-1 chain pin); historical Mento swap flow inventory
   from v0 / v1 outputs.

6. **§3.B NEW SECTION — q_t schedule family pre-commitment (NORMATIVE).** Four pre-pinned
   parametric families with their parameter spaces fixed in spec text BEFORE any v2
   generation: F1 (monthly fixed), F2 (weekly fixed), F3 (front-loaded two-payment),
   F4 (back-loaded two-payment). Sensitivity sweep over F1-F4 is mandatory; the new
   `Stage2PathBSyntheticDriftBeyondTolerance` exception in §6 fires if the cross-family
   spread of synthetic Δ^(a_s) exceeds ±20% (indicating schedule choice is dominating
   the signal).

7. **§4.0 Parquet schema additions.** Existing `audit_summary`, `address_inventory`,
   `event_inventory` schemas are PRESERVED (BLOCK-B1 closure intact). NEW artifact
   `a_s_counterfactual.parquet` is added with the v1.4-pinned schema (q_t schedule
   family + params, week, COP/USD path source, simulated Δ^(a_s), realized weekly σ,
   aggregated Mento swap flow, schema version metadata). DATA_PROVENANCE.md template
   extended with `q_t_schedule_family_pinned` field documenting the pre-commitment
   string per artifact.

8. **§5 + §5.A — free-tier-only budget pin PRESERVED.** Synthetic generation is local
   Python compute with ZERO RPC calls; v0 + v1 free-tier projection unchanged. v2's
   network footprint shrinks under v1.4 (the prior v1.3 v2 = bill-pay extraction has
   non-zero RPC fingerprint; v1.4 v2 = synthetic generation has no on-chain calls).
   Burst-rate analysis unchanged. CORRECTIONS-δ' Alchemy 30M CU/mo correction
   PRESERVED.

9. **§6 typed-exception inventory revision.** DEPRECATE `Stage2PathBASOnChainSignalAbsent`
   (resolved by SYNTHESIS.md acknowledgment that no on-chain a_s entity exists; the pivot
   to synthetic counterfactual is the framework's response to that acknowledgment and
   is recorded in v1.4 not as a HALT but as the v2 design). ADD
   `Stage2PathBSyntheticDriftBeyondTolerance` — fires if cross-family Δ^(a_s) spread
   exceeds ±20% across the §3.B-pinned q_t families; 5 user-enumerated pivots pre-pinned.
   All other typed exceptions PRESERVED.

10. **§8 Cross-path handoff revision.** B → A `r_al_handoff.json` schema PRESERVED
    (Path A v3 still consumes empirical r_(a_l) + HAC SE for stochastic-σ MC
    calibration). A → B v3 envelope handoff REFRAMED FROM OPTIONAL TO NORMATIVE: Path
    A v3 σ-distribution becomes a required input to Path B v2 synthetic counterfactual
    enabling scenario-replay over Path A's simulated FX paths. New `v3_handoff.json`
    schema pinned with fields `{sigma_paths, path_source, path_count,
    sha256_of_path_a_v3_artifact}`. The §8 cross-path naming-asymmetry NIT (Path A §12
    "σ-distribution" vs Path B FLAG-B9 "r_(a_l) point + HAC SE") is carried forward to
    the convergence-dispatch work item per the v1.3 deferral.

**No-regression assertion (BLOCK / FLAG inheritance).** All v1.0 → v1.3 BLOCK closures
intact: BLOCK-B1 (§4.0 base schema for audit_summary / address_inventory /
event_inventory) preserved with ADDITIONS only (the new a_s_counterfactual.parquet
artifact does not modify existing schemas); BLOCK-B2 (§3.A provenance discipline)
preserved with the DATA_PROVENANCE.md template extended for the new q_t-pinning field;
BLOCK-B3 (SQD vs Subsquid Cloud structural distinction) preserved verbatim. All FLAGs
B1-B9 closures intact in spirit; substrate references updated to a_l-side only:
FLAG-B2 (q_t observation source) is reframed from on-chain settlement-leg observation to
pre-pinned synthetic schedule, but the FLAG closure mechanism (q_t is unambiguously
sourced from the spec's §3.B pre-commitment) is preserved; FLAG-B4 reference-price
ladder unchanged; FLAG-B7 allowlist discipline unchanged but scoped to the a_l-side
substrate set; FLAG-B8 MEV-bot / atomic-arb partition rule unchanged for v1
fee-yield extraction; FLAG-B9 cross-path coupling pin updated to reflect the v1.4
A → B promotion. Anti-fishing posture preserved verbatim: §3.B q_t schedule
pre-commitment is the v1.4 anti-fishing addition; the new `Stage2PathBSyntheticDriftBeyondTolerance`
exception is the safety mechanism guarding the synthetic methodology against
schedule-choice fitting.

**Why CORRECTIONS-ε is not micro-tuning.** Threshold tuning is when one moves a
pre-pinned numeric to make a result land. v1.4 does not move any pre-pinned numeric.
v1.4 acknowledges that the v1.0-v1.3 substrate hypothesis (on-chain a_s entity exists in
some Mento-corridor consumer-rail operator's contract) was empirically falsified by 4
independent research tracks (SYNTHESIS.md §2 / §3.1 / §3.2 / §3.3) and pivots to a
methodology — synthetic counterfactual generation under pre-pinned q_t families — that
acknowledges the falsification and proposes a different evidence path. The pivot is
structurally motivated, not threshold-tuned. The pre-commitment of q_t schedule families
in §3.B BEFORE any v2 generation is the anti-fishing safeguard that prevents the
methodology from sliding back into post-hoc fitting. The new typed exception is the
HALT-and-flag mechanism that surfaces non-robustness rather than absorbing it.

## Change Log v1.2.1 → v1.3 (CORRECTIONS-γ)

This revision executes the rename queued from v1.1 onward (and explicitly flagged in v1.2's
"Anticipated future revision" subsection plus v1.2.1's `anticipated_corrections_gamma`
frontmatter field): every prose location that named Path B's deliverable as "behavioral
demand" or "willingness-to-pay" is renamed to **"structural exposure"** — i.e., the
cash-flow geometry yielding `|Δ^(a_l)|` and `|Δ^(a_s)|` magnitudes in $-notional that the
CPO would neutralize on observed transaction flows. v1.3 is a prose-rename pass ONLY: no
frontmatter pin moves, no schema field changes, no new typed exceptions, no quota changes,
no methodology changes. The underlying v0 → v1 → v2 → v3 ladder still produces `|Δ^(a_l)|`
and `|Δ^(a_s)|` as v1.0 → v1.2.1 always did; v1.3 just NAMES that output correctly.

**Why it matters (the load-bearing rationale).** Transaction archaeology cannot infer
willingness-to-pay for an instrument that does not yet exist in the market. Path B reads
the existing on-chain history of a_l-side LP behavior (Mento V3 / Uniswap V3 swap-and-fee
flows) and a_s-side bill-pay behavior (Bitgifty / Walapay settlement-leg `Transfer`
events). Those transactions describe equilibrium under the *current* option set —
specifically, an option set in which the CPO does not exist. Introducing the CPO would
change the option set facing both sides, which would change observed transaction
behavior, which means the existing-transaction inference cannot be lifted to a WTP claim
about the new equilibrium. What the existing-transaction inference CAN do is characterize
the **structural exposure** the CPO would neutralize: the realized magnitude of the
cash-flow geometry that the framework predicts the CPO covers. That is a load-bearing,
pre-deployment, M-sketch-fitness question; behavioral demand / WTP is a Stage-3
(deployment) question that requires a different evidence base (deployed pilot, surveyed
demand, observed take-up at posted prices).

The framework's Stage-2 ideal-scenario clause (per project CLAUDE.md "Instrument family"
paragraph: *"The framework permits — and at this stage requires — modeling the ideal
scenario in which the proposed instrument settles cleanly with adequate liquidity"*)
explicitly authorizes assuming the market exists; the M-design step proposes the ideal
settlement architecture and only the deployment step requires real LP capital. Trying to
estimate behavioral demand at Stage-2 is exactly the Phase-A.0 stage-drift failure mode
that produced the over-engineered slow-lane apparatus that eventually parked, and is
anti-fishing-banned. v1.3 corrects the prose to reflect the stage-correct framing the
ladder always implemented.

**Per-location list of changes (8 prose locations executed).**

1. Frontmatter `anticipated_corrections_gamma` block → renamed to `corrections_gamma_status`
   and updated from anticipated-status placeholder to EXECUTED record citing the
   ideal-scenario clause and the stage-discipline rationale above.
2. §1 framing-reminder paragraph (was "CORRECTIONS-γ-anticipated, not yet applied"; was
   instructing executors to *treat* the deliverable as structural-exposure pending future
   prose reconciliation) → rewritten as a normative definition: Path B's deliverable IS
   structural-exposure characterization; behavioral demand / WTP is explicitly out of
   Path B's Stage-2 scope; the framework's Stage-2 ideal-scenario clause permits assuming
   the market exists.
3. §1 "Path B's purpose" paragraph (was "revealed-preference evidence of cash-flow
   geometry") → tightened to "structural-exposure characterization of realized cash-flow
   geometry" — the revealed-preference framing risked sliding back into WTP-language;
   structural-exposure is the load-bearing term.
4. §4 v2 output bullet (was "demand-side / structural-exposure cash-flow series") →
   simplified to "structural-exposure cash-flow series" — the dual naming inherited from
   v1.1 prose dropping a transitional hedge; the a_s side IS the structural-exposure side
   regardless of the supply-vs-demand economic-leg terminology.
5. §6 `Stage2PathBASOnChainSignalAbsent` pivot (a) parenthetical (was "(NOTE: this is
   structural-exposure proxy not WTP per CORRECTIONS-γ-anticipation)") → rewritten as
   inline framing without the anticipation-flag: "the upper-bound proxy is a
   structural-exposure ceiling — characterizing the realized magnitude of the CF^(a_s)
   shape the CPO would neutralize, NOT a behavioral-demand or WTP estimate, which is a
   Stage-3 question outside Path B's scope."
6. Existing v1.0 → v1.1 Change Log "Anticipated future revision" paragraph (was naming
   CORRECTIONS-γ as a future dispatch and noting v1.1 deliberately did not introduce the
   rename) → updated tense to record CORRECTIONS-γ EXECUTED in v1.3 with sha-pin
   crosslink to the predecessor v1.2.1 (the lineage record is preserved; only the
   pending/executed marker flips).
7. Change Log v1.1 → v1.2 "Preserved from v1.1" bullet (was naming CORRECTIONS-γ
   anticipated rename as a kept-as-anticipated item) → updated to record CORRECTIONS-γ
   EXECUTED in v1.3, no longer anticipated.
8. §8 closing paragraph (was "Demand-side / structural-exposure-side convergence remains
   an open question for downstream Stage-3 work") → simplified to "Structural-exposure-side
   convergence remains an open question for downstream Stage-3 work" — preserves the
   convergence-deferral substance while dropping the WTP-adjacent "demand-side" framing
   for the open-question phrasing.

**Preserved from v1.0 → v1.2.1 (no regression).** All BLOCK closures (BLOCK-B1 §4.0
schema, BLOCK-B2 §3.A provenance, BLOCK-B3 SQD vs Subsquid Cloud structural distinction)
intact. All FLAG closures (FLAG-B1 through FLAG-B9) intact. v1.2 CORRECTIONS-δ
free-tier-only budget pin (§5 / §5.A burst-rate analysis with three new typed exceptions)
intact. v1.2.1 CORRECTIONS-δ' fixes (`alchemy_free` enum value in §4.0 `data_source_primary`,
Step-5 cross-reference in §5 + §6) intact. §8 cross-path handoff schema (B→A
`r_al_handoff.json`; A→B v3 envelope) intact. The known cross-path handoff naming
asymmetry (Path A §12 "σ-distribution" vs Path B FLAG-B9 "r_(a_l) point + HAC SE") is left
for the convergence-dispatch work item — v1.3 does not touch §8 handoff fields.
Anti-fishing discipline (no auto-pivot to paid services; no silent threshold tuning) intact.

**Domain-correct terminology preserved.** Several locations use "demand-side" as standard
economic terminology naming the a_s leg of the CPO (the demand-side of the framework's
supply-side / demand-side decomposition); this is contextually correct and is preserved
unchanged. Specifically: §1 "`a_s` (short-σ) demand side" describing the framework's
named legs; §4 "demand-side / structural-exposure cash-flow series" was renamed in
location-4 above to drop the dual phrasing (NOT because "demand-side" is wrong as
economic terminology, but because the dual hedge created ambiguity between
economic-leg-naming and deliverable-naming); §6 `Stage2PathBASOnChainSignalAbsent`
disposition prose using "demand-side" to name the a_s leg of the framework decomposition
preserved. The rename is targeted at WTP-implying language about the *deliverable*, not at
the supply-vs-demand economic terminology naming the *legs*.

**No-regression assertion.** v1.2 + v1.2.1 BLOCK / FLAG closures unchanged; v1.2 + v1.2.1
typed exception inventory unchanged; §3.A provenance discipline unchanged; §4.0 schema
unchanged; §5 + §5.A free-tier-only architecture unchanged; §6 disposition pivots
unchanged except for the location-5 inline-framing rewrite of one parenthetical;
§7 anti-fishing posture unchanged; §8 cross-path handoff schema unchanged. v1.3 diff
surface is ≤8 prose locations as anticipated by the v1.2.1 inventory.

## Change Log v1.1 → v1.2 (CORRECTIONS-δ)

This revision integrates a single user directive issued 2026-05-02: **AI-tooling budget is
FREE-TIER ONLY**. No paid services authorized. The v1.1 budget pin (`$49/mo Alchemy Growth`)
is invalidated. Every section that quoted or implicitly relied on the Growth-tier cap (49M
CU/day ≈ 1.47B CU/month) is re-derived against the Alchemy free-tier cap (30M CU/month, 25
req/sec, 500 CU/sec rolling window) verified via WebFetch against alchemy.com/pricing on
2026-05-02. v1.1 BLOCK and FLAG closures are PRESERVED — none regressed; only the
Alchemy-quota assumptions inside §5 / §5.A / §6 change, and §6 gains three new typed
exceptions specific to free-tier failure modes.

**Scope of CORRECTIONS-δ.**

- Frontmatter: `tooling_budget_committed`, `primary_data_path_v1_1` → `primary_data_path_v1_2`,
  new `budget_pin: free_tier_only`, new `budget_pin_provenance`, new
  `free_tier_quota_observations_2026_05_02` block recording WebFetch-verified quotas with
  observation method + delta-vs-v1.1 commentary, predecessor chain expanded.
- §3 prose: replace "$49/mo Alchemy Growth" / "49M CU / day" framing with free-tier
  framing; preserve the Subsquid-Cloud-vs-SQD-Network distinction (BLOCK-B3 structural
  resolution).
- §5: re-pin the tooling stack to free-tier-only. SQD Network public gateways remain
  primary. Alchemy demoted from "Growth committed" to "free tier with batched + rate-limited
  execution discipline." Dune ceiling (~2500/mo working assumption) re-affirmed with the
  caveat that the docs.dune.com billing page does not publish a numeric monthly cap.
  Public RPCs (forno.celo.org, eth.llamarpc.com, rpc.ankr.com/eth) added explicitly as
  flaky fallback. Paid escalation list expanded to include "Alchemy paid tier above free"
  (in v1.1 only Subsquid Cloud + Dune Analyst were paid-only; in v1.2 the entire paid
  Alchemy ladder is paid-only).
- §5.A: re-derive every projection sub-block. Add a new "Burst-rate analysis" sub-clause
  pinning the 25 req/sec free-Alchemy cap as the binding constraint when monthly CU is
  abundant; pin a batched-extraction discipline (chunked event-window queries with explicit
  inter-call sleep) for v1 fee-yield extraction and v2 settlement-leg extraction.
  Document that monthly-CU headroom is >100× even on free tier (165K-285K CU vs 30M cap),
  so CU-cap exceedance is unlikely; rate-limit exceedance is the realistic risk.
  Re-affirm SQD Network has its own (50 req / 10s per IP) limit which now applies to
  v1.2's primary data path; add an explicit batched-window discipline for SQD too.
- §6: add three new typed exceptions:
  - `Stage2PathBAlchemyFreeTierRateLimitExceeded` — burst pattern exceeds 25 req/sec
  - `Stage2PathBAlchemyFreeTierMonthlyCUExceeded` — CU/month > 30M (low risk per §5.A
    projection but pre-pinned for safety; will most likely trigger only under repeated
    sensitivity re-runs)
  - `Stage2PathBPublicRPCConsistencyDegraded` — fallback public RPCs return inconsistent
    block / receipt / log responses across calls; degradation policy is HALT-and-flag,
    not silent merge
  - Preserve `Stage2PathBSqdNetworkThrottled` from v1.1 (formerly named
    `Stage2PathBSqdNetworkRateLimitedRetroactively` in some review prose; kept under v1.1
    name)
  - Update the §5.A degradation Step 4 disposition: any escalation to a paid Alchemy
    tier OR paid Subsquid Cloud OR paid Dune Analyst tier requires a typed-exception HALT
    with user-adjudicated re-budgeting; previously v1.1 had Alchemy Growth as a permitted
    landing; that is no longer authorized.
- Anywhere "$49 / Alchemy Growth" appeared in v1.1 prose: scrubbed and replaced with
  free-tier framing.

**Free-tier-feasibility risk assessment.** All v1.1 ladder rungs (v0 → v1 → v2 → v3) remain
feasible under v1.2's free-tier-only constraint per §5.A re-projection. Specific risks
flagged for orchestrator awareness but NOT requiring spec-level downgrade:

1. **Eigenphi MEV-bot allowlist (FLAG-B8 layer-1).** Eigenphi's free-tier API access for
   MEV-bot enumeration must be re-verified at v1 entry. If Eigenphi has paywalled the
   bot-list since the dispatch brief was authored, FLAG-B8 layer-1 falls back to a
   community-maintained free-tier MEV-bot list (e.g., the Flashbots-published mev-inspect-py
   labelled-address sets, or the LibMEV or zeromev.org public registries). The
   Layer-2 atomic-arb partition is unaffected (it is computed locally from extracted swap
   events).
2. **CRC archive depth for v1 historic LP fee accrual.** Alchemy free tier provides full
   archive node depth on most chains by default; whether Celo archive is included on free
   tier is verified at v0 audit start. If archive depth is paid-tier-gated for Celo, the v1
   bulk extraction shifts to SQD Network (which is the primary data path in v1.2 anyway,
   so no architectural change required) and the Alchemy-side spot RPC narrows to non-archive
   `eth_call` against current state only.
3. **Burst-rate vs SQD Network.** Both Alchemy free (25 req/sec) and SQD Network (5 req/sec
   per IP per docs.sqd.ai notice) impose modest rate caps. v1 bulk extractions are
   request-volume-modest (one bulk extraction per pool returns the full event list in a
   single response from SQD Network's archive query interface), so the binding constraint
   is local-side processing throughput, not the network-side rate cap. Pre-flight estimation
   per query window in §5.A.

If at v0 audit any of these risks materialize as an actual blocker, the disposition path is
the typed-exception HALT pathway in §6 with explicit user adjudication. Auto-pivot up the
free-tier ladder is permitted (a tooling fallback within free tier); auto-pivot to a paid
service is anti-fishing-banned and requires user re-budgeting.

**Preserved from v1.1 (not changed in v1.2).**

- §3.A DATA_PROVENANCE.md mirror discipline (BLOCK-B2 closure)
- §4.0 Parquet artifact schema (BLOCK-B1 closure)
- §5 SQD Network vs Subsquid Cloud structural distinction (BLOCK-B3 structural resolution;
  only the Alchemy quota assumptions inside it change)
- All FLAG-B1 through FLAG-B9 closures
- §8 + FLAG-B9 cross-path handoff (B→A r_al_handoff.json; A→B v3 MC envelope)
- CORRECTIONS-γ rename — recorded as anticipated through v1.2.1; **EXECUTED in v1.3**
  (frontmatter `corrections_gamma_status` field + new Change Log v1.2.1 → v1.3 section
  + §1 framing-reminder rewrite + §1 "Path B's purpose" tightening + §4 v2 output
  bullet simplification + §6 inline-framing rewrite + §8 closing paragraph
  simplification). v1.2's no-execution-in-v1.2 stance is preserved as historical record;
  v1.3 carries out the rename per the prose-only scope pinned in the v1.2.1
  `anticipated_corrections_gamma` frontmatter field.

## Change Log v1.0 → v1.1

This revision integrates the 3 BLOCKs and 9 FLAGs surfaced by the 2-wave doc-write
verification (Wave-1 Reality Checker + Wave-2 Workflow Architect) on v1.0. v1.0
structure is preserved; new normative content is additive (new subsections §4.0, §3.A,
§5.A) plus targeted edits in §3, §5, §6 to resolve BLOCK-B3 and FLAG items 1-9.

**BLOCK resolutions:**

- **BLOCK-B1** (v0 output schema not concretely pinned) → resolved by new §4.0 "v0
  Output Schema (normative)" pinning canonical column lists, dtypes, primary keys,
  row-count expectations, file format, and naming convention for `audit_summary`,
  `address_inventory`, and `event_inventory` artifacts.
- **BLOCK-B2** (DATA_PROVENANCE.md mirror requirement missing) → resolved by new §3.A
  "Provenance Discipline (normative)" requiring per-artifact `DATA_PROVENANCE.md`
  alongside every committed dataset, mirroring the Stage-1 Pair D pattern; HALT-on-sha-
  mismatch behavior pinned.
- **BLOCK-B3** (Subsquid "free in compute" claim contradicts $49 budget pin) → resolved
  by §5 rewrite distinguishing **SQD Network** (decentralized data lake; FREE for
  archive extraction; supports Celo + Ethereum mainnet via documented public gateways)
  from **Subsquid Cloud** (hosted indexer-as-a-service; PAID above playground tier).
  Primary high-volume data path REPLACED: SQD Network public gateways become the
  primary archive surface; Alchemy Growth handles spot RPC + receipts; Dune handles
  ad-hoc SQL against pre-existing community tables. Subsquid Cloud is removed from the
  free-tier pivot ladder and listed only as paid escalation with explicit cost ceiling.
  Concrete query-volume projection pinned in new §5.A. Affected typed-exception
  pivots (§6) updated.

**FLAG resolutions** (tag each in §6 / §7 / §3 prose where pre-commit lives):

- **FLAG-B1** (`r_(a_l)` estimator method not pinned) → §3 +
  §6.v1.exception clauses: pre-commit **TWAP-weighted realized fee yield**:
  `r_(a_l) = (cumulative LP fee accrual in USD) / (cumulative |ΔP|-weighted
  swap-volume in USD)` over the v1 sample window, regressed via OLS with HAC SE.
  Gas-deducted variant is sensitivity, not primary. Position-weighted (per-LP-share)
  is out-of-scope (requires per-LP attribution; v1 stays pool-aggregate).
- **FLAG-B2** ({q_t} obligation extraction from a_s ambiguous) → §3 +
  §6.v2.exception clauses: pre-commit **bill-paid lifecycle event** as the q_t
  observation — specifically the on-chain settlement-leg `Transfer` of local-stable
  to the merchant address (not the user-side wallet debit, not the payment-completion
  off-chain confirmation). Funding-leg `Transfer` of USD-stable into the
  Bitgifty/Walapay router contract is a co-observation but does NOT constitute q_t
  alone (it is the input cost, not the obligation).
- **FLAG-B3** (time-binning resolution unspecified) → §3 + §4 bins normative:
  **daily aligned to UTC 00:00:00** as primary cadence; weekly aggregation
  (Mon-anchored) as standard derivation. Per-block resolution is rejected as
  introducing non-uniform temporal weighting that contaminates the
  `Σ |FX_t − FX_{t-1}|` shape check.
- **FLAG-B4** ((X/Y)_t reference price source unpinned) → §3 + §4 normative:
  primary **on-chain Mento V3 FPMM USDm/COPm pool spot price** sampled at the
  daily-bin close-tick; if pool absent (v0 HALT), fallback to **Uniswap V3 USDC/USDm
  Celo pool spot**; further fallback to **Banrep TRM daily series** (off-chain,
  same source as Pair D Stage-1 X). Source-of-record per observation is recorded in
  the per-row `price_source` column.
- **FLAG-B5** (CF reconciliation between v1 and v2 cadence) → §3 normative: CF
  reconciliation occurs at **monthly bin** (CF^(a_l)_t − CF^(a_s)_t for each calendar
  month overlap of v1 and v2 sample windows), with a cumulative-delta series as
  standard derivation. Per-period reconciliation is preferred over cumulative-only
  to surface regime-conditional asymmetries (RC FLAG #6 inheritance).
- **FLAG-B6** (v3 backtest harness — realized vs implied σ_T) → §3 + §6.v3 normative:
  **realized σ_T from Stage-1 Pair D 2015-2026 monthly COP/USD log-return-squared**
  is the primary input. Implied vol from Panoptic option markets is NOT used (no
  COP/USD option market exists at the relevant historical depth; using a proxy implied
  vol would inject a free-fitting parameter the framework does not authorize).
- **FLAG-B7** (address allowlist vs discovery) → §3 + new §4.0 normative: v0 operates
  on a **fixed allowlist** of contracts named in this spec's `on_chain_pins`
  frontmatter plus the Mento V3 deployment manifest. Discovery is OUT OF SCOPE for
  v0; if a candidate venue is missing from the allowlist, the executor surfaces a
  user-adjudicated typed-exception rather than auto-expanding the audit surface.
  This rule is anti-fishing-load-bearing (auto-discovery introduces selection bias
  on whatever surface produces nicer data).
- **FLAG-B8** (filter for non-economic transactions — MEV / arb / wash) → new §3
  paragraph + §6.v1 normative: pre-commit **two-layer partition rule** for swap
  events. Layer 1: drop swaps where `tx.from` is on a published MEV-bot allowlist
  (Eigenphi or equivalent free-tier list, snapshotted at v1 entry). Layer 2: drop
  swaps where the `(swap_in, swap_out)` round-trips inside a single transaction
  (atomic arb fingerprint). Wash-trading detection (across-tx repeated-counterparty
  cycles) is OUT OF SCOPE for v1 due to Celo's lower MEV depth vs Ethereum; flagged
  as v3 sensitivity. Echoes the Carbon V1/V2 user-vs-arb partition discipline pinned
  in memory `project_carbon_user_arb_partition_rule`.
- **FLAG-B9** (cross-path coupling with Path A) → §8 expansion: paths are **DEFAULT
  INDEPENDENT**. The single permitted Path A → Path B handoff is at v3: Path A
  produces the stochastic-σ Monte-Carlo `Π(σ_T)` price distribution; Path B replays
  realized σ paths through the same parametric `Π(σ_T) ≈ K̂·σ_T` form WITHOUT
  consuming Path A's `K̂` calibration (each path estimates `K̂` independently from
  its own data). Convergence dispatch (separate work item) compares the two
  envelopes. The single permitted Path B → Path A handoff is the empirical
  `r_(a_l)` from v1: Path A v3 may consume Path B v1's `r_(a_l)` point estimate +
  HAC SE as the calibration anchor for its stochastic-σ MC. Handoff schema:
  `r_al_handoff.json` with fields `{r_al_point, r_al_hac_se, sample_n, sample_window,
  source_pool_address, sha256_of_input_panel}`. Any other coupling (Path B
  consuming Path A's parametric assumptions, Path A consuming Path B's σ-path
  decomposition) is anti-fishing-banned.

**Anticipated future revision (EXECUTED in v1.3, sha-pin lineage preserved).** A
`CORRECTIONS-γ` block (originally scoped as a separate dispatch; ultimately landed via
Data Engineer dispatch 2026-05-02 on top of v1.2.1 sha256
`86830209130b7833cb820531add8851513cf4831dc9a60b19c73bf7c076f4a17`) renames Path B's
deliverable framing from "behavioral demand" / "willingness-to-pay" to
**"structural exposure"** — i.e., cash-flow geometry yielding `|Δ^(a_l)|` and
`|Δ^(a_s)|` in $-notional that the CPO would neutralize on observed transaction flows.
Transaction archaeology cannot infer WTP for an instrument that does not yet exist in
the market; existing transactions describe equilibrium under the option set without the
CPO, so the inference would be broken. v1.1 deliberately did NOT introduce this rename
to keep the v1.0 → v1.1 diff scoped to the verification matrix, and v1.2 + v1.2.1
preserved that scoping for the same reason; v1.3 finally executes the rename as a
prose-only pass per the v1.2.1 `anticipated_corrections_gamma` frontmatter
specification. See the Change Log v1.2.1 → v1.3 section above for the per-location
list, the load-bearing rationale, and the no-regression assertion.

## §1 — Goal + scope

Path B is the on-chain empirical-validation track for the Pair D Convex Payoff Option (CPO)
Stage-2 M-sketch dispatch brief at
`contracts/.scratch/2026-04-30-stage-2-m-sketch-dispatch-brief-pair-d.md`. Under v1.4
(CORRECTIONS-ε), Path B's goal is split into two empirically distinct halves:

- **a_l side — empirical, on-chain, observable.** Confirm — from realized on-chain history
  alone, with no simulation and no parameter free-fitting — that the LP-side flow the
  dispatch brief identifies as the CPO's `a_l` (long-σ-flavored gross-fee) component
  actually exhibits the cash-flow shape `CF^(a_l)_T = Σ r_(a_l) · |(X/Y)_t − (X/Y)_{t-1}|`
  the imported convex-payoff framework predicts.
- **a_s side — synthetic, simulated, counterfactual.** Generate a counterfactual time
  series of `Δ^(a_s)` under (a) historical Mento V3 / V2 swap flows (real, observable;
  empirical anchor), (b) parametric q_t schedule families pre-committed in §3.B
  (synthetic; no post-hoc fitting), and (c) observed COP/USD path (Banrep TRM + Mento
  on-chain spot per FLAG-B4). The output simulates what a hypothetical Stage-3 a_s vault
  WOULD have produced, NOT what an existing on-chain a_s entity DOES produce.

The reason for the split is load-bearing and recorded in the v1.4 Change Log above plus
the SYNTHESIS.md memo at
`contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/SYNTHESIS.md` (commit
`e25131cd2`): four parallel research tracks (Bitgifty / Walapay code archaeology, discovery
sweep, category-(ii) deep-dive, category-(iv) discovery) jointly confirm that **no on-chain
a_s entity exists in any LATAM corridor researched.** Consumer-facing payment-rail
operators settle off-chain via API custody or MPC; tokenized-fiat issuers hold one-sided
local-currency reserves with no FX exposure on the issuer's books; the LP-level
relocation candidate (e.g., MXNB/USDC LP) is rejected because LP NET is structurally
**short variance** per LVR (Milionis-Moallemi-Roughgarden 2022), making LP positions
a_l-flavored not a_s-flavored. The DRAFT.md simplified two-party model — in which a_s
is a payment-rail operator with a fixed B_T obligation in local currency, sourced from Y
reserves, on an on-chain treasury — does not have an empirical referent.

**Abrigo is an a_s-instantiating product, not an a_s-hedging product (NORMATIVE).** Per
SYNTHESIS.md §8.1 and project CLAUDE.md "premium-funded ratchet (self-LBM)" framing, the
CPO cannot be sold into an existing on-chain a_s population because that population
doesn't exist on-chain. The product must DEPLOY the a_s side simultaneously: a Stage-3
vault that accepts Y-stable deposits from wage earners, creates a fixed-T X-denominated
obligation (commits to delivering COPm monthly per a pre-committed schedule), acts as the
a_s itself (vault operator sources COP from USD reserves over time), buys CPO Π hedge
from the LP side (a_l) to neutralize FX vol exposure, and charges margin to the wage
earner with the CPO premium funding the LP-side counterparty. Stage-2 quantifies the
addressable structural exposure that the CPO would neutralize once the a_s vault is
deployed in Stage-3. The a_s side is methodologically a forward-looking specification at
Stage-2 (the synthetic counterfactual generated by v2), not a backward-looking measurement
of an existing on-chain entity.

**LVR acknowledgment (NORMATIVE).** Per Milionis-Moallemi-Roughgarden 2022 (LVR), the LP
NET position in a CFMM is structurally SHORT VARIANCE: LP NET = LP gross fee income −
LVR cost where LVR > 0 ∝ instantaneous σ². Path B v1's `CF^(a_l)` reconstruction models
the LP GROSS FEE INCOME side (proportional to `|ΔFX|` via the framework's
`r·|FX_t − FX_{t-1}|` shape); this is the observable empirical anchor v1 measures and
emits to Path A v3 via `r_al_handoff.json`. The LP IL (impermanent loss / LVR) cost is
decomposable from the same v1 panel (per-Mint / Burn-event reserve snapshots + spot-price
path) but is NOT in the v1 critical path under v1.4 — it is a derived sensitivity
available for v3 characterization if needed. The v1.4 reframe DOES NOT reposition the
a_l side as short-variance; it acknowledges that the LP's net economic position is
short-variance while v1's empirical extraction targets the long-σ-flavored gross-fee
component the framework's `CF^(a_l)` definition isolates. The Stage-3 vault hedge design
will need to revisit whether the LP-side counterparty wants gross-fee yield only (in
which case the LP eats the LVR cost separately) or a wrapped position that absorbs the
LVR cost into the CPO premium structure; that is a Stage-3 question outside v1.4's
scope.

**v1.4 v0 → v3 ladder (revised) confirms — for the a_l side from realized on-chain
history alone, with no simulation and no parameter free-fitting — that the LP-side flow
exhibits the gross-fee cash-flow shape the framework predicts; AND simulates — for the
a_s side under pre-committed q_t schedule families with the realized COP/USD path and
the observed historical Mento swap flow inventory — what the Δ^(a_s) trace WOULD have
been if a Stage-3 vault had been deployed at the start of the sample window.**

The Stage-1 anchor is the Pair D simple-β PASS verdict committed 2026-04-28 PM late evening, with
sha-pin chain quoted verbatim from the dispatch brief §3:

- Pair D spec v1.3.1: `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`
- Joint panel: `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`
- Primary OLS results: `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf`
- Robustness pack: `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904`
- VERDICT.md: `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf`

These pins are READ-ONLY through Path B. Any spec edit that would invalidate them is OUT OF
SCOPE; this is a separate document, not a Stage-1 revision.

Path B's purpose under v1.4 is **structural-exposure characterization** of (a) realized
a_l cash-flow geometry from on-chain history and (b) synthetic a_s cash-flow geometry from
pre-pinned q_t schedules — what magnitude of `|Δ^(a_l)|` is *already* measurable in the
existing on-chain history of the a_l-side venues plus what magnitude of `|Δ^(a_s)|` a
hypothetical Stage-3 vault WOULD have produced under the pre-committed schedule families,
both expressed in $-notional — rather than the analytical claim that Path A constructs by
stochastic / Monte-Carlo modeling of the same underlying CPO mechanics. The
structural-exposure framing is load-bearing: realized transactions characterize the
cash-flow shape the CPO would neutralize on the a_l side, AND pre-pinned synthetic
schedules characterize the cash-flow shape the CPO would neutralize on the a_s side once
deployed, NEITHER claim what users would pay for the CPO if it existed (which is a
Stage-3 question, see the framing definition below). The two paths are coupled at v3
under v1.4 (FLAG-B9 updated): Path B reconstructs the realized `CF^(a_l)`, generates
synthetic `CF^(a_s)` under pre-pinned q_t families optionally seeded by Path A v3's
σ-path distribution, and replays them through the framework's `Π(σ_T)` to get a hybrid
realized-+-simulated CPO P&L envelope; Path A produces a stochastic-bound P&L distribution
under the same framework. The convergence dispatch (separate from this spec) checks
whether Path A's bounds contain Path B's hybrid envelope under each q_t family.
Disagreement is informative; agreement upgrades the M-sketch's empirical defensibility.

Path B is intentionally narrower than the dispatch brief itself. The dispatch brief authors a
*deployable* position-construction sketch on Panoptic; Path B does not. Path B audits whether the
flows the M-sketch presupposes are present and measurable on-chain. If they are not, the
M-sketch inherits an architectural risk that propagates into Stage-3.

**Framing definition (CORRECTIONS-γ EXECUTED in v1.3; CORRECTIONS-ε REFINED in v1.4;
normative).** Path B's deliverable IS **structural-exposure characterization** of (a) the
realized on-chain history of the a_l side and (b) the synthetic counterfactual of the a_s
side — specifically, the cash-flow geometry yielding `|Δ^(a_l)|` and `|Δ^(a_s)|`
magnitudes in $-notional that the CPO would neutralize on observed (a_l) and hypothesized
under pre-committed q_t schedule families (a_s) transaction flows. The ladder produces
those magnitudes from realized fee-yield extraction (v1, on-chain) and synthetic
counterfactual generation under pre-pinned q_t schedules with realized FX path and
historical swap-flow inventory (v2, simulated), replays them through the framework's
`Π(σ_T)` to get a hybrid realized-+-simulated P&L envelope (v3), and emits a
calibration-handoff packet for Path A v3 convergence (§8). The v2 simulation IS a form of
structural-exposure characterization — it characterizes the realized magnitude of the
`CF^(a_s)` shape the CPO would neutralize once a Stage-3 vault instantiates the a_s side,
*conditional on each pre-committed q_t schedule*. Behavioral demand / willingness-to-pay
remains **explicitly out of Path B's Stage-2 scope**: transaction archaeology cannot infer
WTP for an instrument that does not yet exist in the market; the existing transactions
describe equilibrium under the *current* option set (an option set in which the CPO is
absent), and introducing the CPO would change the option set facing both sides, breaking
the inference. Synthetic counterfactual generation under pre-pinned q_t schedules is also
NOT WTP — it characterizes structural exposure under a pre-committed deployment design,
not realized take-up at a posted price. The framework's Stage-2 ideal-scenario clause
(per project CLAUDE.md "Instrument family" paragraph) permits assuming the market exists
for M-design purposes; behavioral demand / WTP is a Stage-3 (deployment) question
requiring a different evidence base (deployed pilot, surveyed demand, observed take-up at
posted prices) and is the Phase-A.0 stage-drift failure mode the framework's anti-fishing
discipline is designed to prevent. Executors implementing this spec MUST keep the
deliverable framed as structural-exposure characterization throughout; any drift into
WTP-inference language is a methodology error, not a documentation nit.

## §2 — Internal ladder (v0 / v1 / v2 / v3)

Each version has a pre-pinned exit criterion and SAA disposition (Success → next version; Abort
→ typed exception → user-pivot disposition memo per
`feedback_pathological_halt_anti_fishing_checkpoint`; Abort-with-Pivot → user-enumerated
alternative; auto-pivot is anti-fishing-banned).

**v0 — Data-coverage audit (v1.4 substrate set).** Confirm Mento V3 router + Mento V2
BiPool manager + Mento V2 USDm + Mento V2 COPm + Mento V3 USDm/cUSD FPMM pool + Mento
broker addresses are reachable on Celo and have non-trivial event activity in the
2023-08 → 2026-02 window. Confirm Panoptic factory deployment on Ethereum mainnet and the
existence of any FX-pair option market that establishes the Panoptic-side architecture is
reachable. For each confirmed venue: TVL snapshot, cumulative swap / exchange / broker
volume, first-event block, last-event block, swap-event count. Build the historical Mento
swap flow inventory required by v2 (per-week aggregate of USDm ↔ cUSD swap volume on the
Mento V3 FPMM, per-week aggregate of USDm ↔ COPm exchange volume on the Mento V2 BiPool,
per-week aggregate of broker activity routed through the Mento broker). Bitgifty / Walapay
on-chain footprint audit is RETIRED in v1.4: per SYNTHESIS.md §3.1, four research tracks
confirmed both operators settle off-chain via API custody / MPC and have no Celo Mento
integration; the v1.0-v1.3 audit task is documented as closed-without-substrate in the
v0 findings memo.

v0 operates on the **fixed allowlist** of contract addresses listed in this spec's
v1.4 `on_chain_pins` frontmatter (a_l-side substrate set) plus the addresses enumerated in
the Mento V3 deployment manifest (per memory `project_no_mento_carbon_protocol_integration`).
Discovery beyond the allowlist requires user-adjudicated typed exception (FLAG-B7).
**No on-chain a_s entity addresses are pinned or audited in v0** per the v1.4
`on_chain_pins_a_s_note` frontmatter declaration; the a_s side is generated synthetically
in v2.

**Exit:** feasibility yes/no per data source, with sha-pinned snapshot of pool / exchange /
broker addresses, cumulative metrics, and block-range bounds. Historical Mento swap flow
inventory frozen and emitted as a v0 artifact (`mento_swap_flow_inventory.parquet`,
schema additive per §4.0). Frontmatter `on_chain_pins` block validated against on-chain
state. v0 output artifacts conform to §4.0 normative schema.

**v1 — Empirical `CF^(a_l)` reconstruction (a_l-side substrate; v1.4 substrate set
clarified).** For each viable a_l-side venue from v0 (primary substrate: Mento V3
USDm/cUSD FPMM pool routed via the Mento V3 router; secondary substrate: Mento V2 USDm /
COPm exchange routed via the Mento V2 BiPool manager and the Mento broker), extract
historical swap / exchange events and reconstruct LP-side cash flow per the framework
definition `CF^(a_l)_T = Σ_t r_(a_l) · |(X/Y)_t − (X/Y)_{t-1}|`. The `r_(a_l)` parameter
is **derived from data** via the FLAG-B1-pinned **TWAP-weighted realized fee yield**
estimator: cumulative LP fee accrual in USD divided by cumulative |ΔP|-weighted
swap-volume in USD over the v1 sample, regressed via OLS with HAC SE. Gas-deducted is a
sensitivity (one of the R1-R4 robustness slots), not the primary. No curve-fitting;
`r_(a_l)` comes out where it comes out.

**Substrate clarification (v1.4 NORMATIVE).** The v1.0-v1.3 prose pinned a Mento V3 FPMM
USDm/COPm pool as the v1 primary; that pool does not exist in the Mento V3 deployment
manifest (DEPRECATED in v1.4 frontmatter). The v1.4 primary v1 substrate is the Mento V3
USDm/cUSD FPMM pool at `0x462fe04b4FD719Cbd04C0310365D421D02AaA19E`; the secondary v1
substrate is the Mento V2 BiPool USDm/COPm exchange routed via the BiPool manager at
`0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901`. The v1 reconstruction extracts r_(a_l) on
each of the two substrates independently and reports both; the v1 `r_al_handoff.json` for
Path A v3 carries the Mento V3 USDm/cUSD r_(a_l) as the primary and the Mento V2 USDm/COPm
r_(a_l) as the secondary, with the convergence dispatch responsible for the consolidation
choice. Note: on the Mento V2 BiPool, "fee accrual" maps to the BiPool's
spread-and-protocol-fee structure rather than a Uniswap-style fee tier; the FLAG-B1
estimator is applied with that distinction recorded in the audit metadata.

The `(X/Y)_t` reference price (FLAG-B4) is the on-chain Mento V3 USDm/cUSD FPMM pool spot
price sampled at the daily-bin close-tick (FLAG-B3) on the Mento V3 substrate, and the
Mento V2 BiPool USDm/COPm exchange-rate snapshot at the daily-bin close-tick on the
Mento V2 substrate; fallback ladder per FLAG-B4 (now flowing to Banrep TRM as Fallback-2
since Uniswap V3 USDC/USDm Celo pool is RETIRED in v1.4 along with the
`uniswap_v3_factory_celo` and `uniswap_v3_usdc_usdm_pool_celo` placeholder).

Non-economic transaction filtering follows the FLAG-B8 two-layer partition rule (MEV-bot
allowlist + atomic-arb round-trip detection); pre-filter applied before fee-yield estimation;
the dropped-row count and dropped-volume fraction are reported as audit metadata in
`audit_summary` per §4.0.

**LVR-side derivation (v1.4 SENSITIVITY, not primary).** Per the v1.4 LVR acknowledgment in
§1, the LP IL / LVR cost is decomposable from the same v1 panel via per-Mint / Burn-event
reserve snapshots aligned to the spot-price path; the resulting LP NET = LP gross fee
income − LVR cost is a sensitivity available for v3 characterization but is NOT in the
v1 critical path. Executors implementing v1 SHOULD emit a `v1_lvr_decomposition.parquet`
companion artifact when the per-Mint / Burn data are within the §5.A free-tier budget
(~5K-15K additional Alchemy CU), but MAY defer it to v3 if the v0 audit shows the
per-Mint / Burn extraction would exceed the §5 budget envelope. Either way, this is a
derived sensitivity, not a primary v1 deliverable; the primary v1 deliverable remains the
gross-fee r_(a_l) per the framework's `CF^(a_l)` definition.

**Exit:** per-substrate empirical `CF^(a_l)` realized series (daily-binned per FLAG-B3,
normalized to the Mento-V3-availability window 2023-08 → 2026-02 as the binding outer
envelope per §3 Block-range bounds; full Pair D 2015-2026 window not reachable on-chain
because Mento V3 deployment block postdates 2015), estimated `r_(a_l)` with HAC-corrected
SE per substrate. Qualitative shape check against the framework's
`Σ r·|FX_t − FX_{t-1}|` shape; sign-and-magnitude pattern only, no goodness-of-fit
threshold (no honest threshold exists absent reference baselines). `r_al_handoff.json`
(FLAG-B9 schema) emitted for Path A v3 consumption with both substrate r_(a_l)s present.
Optional `v1_lvr_decomposition.parquet` if §5 budget permits.

**v2 — Synthetic `CF^(a_s)` counterfactual generation (v1.4 REFRAMED per CORRECTIONS-ε).**
The v1.0-v1.3 v2 task — extract on-chain settlement-leg events from Bitgifty / Walapay
merchant flows — is RETIRED in v1.4. Per SYNTHESIS.md §8.1, no on-chain a_s entity exists;
extraction is structurally impossible because the data source does not exist. v1.4 v2 is
re-defined as **synthetic counterfactual generation**: produce a simulated time series of
`Δ^(a_s)` under (a) historical Mento V3 / V2 swap flows (real, observable; from v0's
`mento_swap_flow_inventory.parquet`), (b) parametric q_t schedule families pre-committed
in §3.B (synthetic; no post-hoc fitting), (c) observed COP/USD path (Banrep TRM + Mento
on-chain spot per FLAG-B4), and (d) optionally Path A v3's σ-path Monte-Carlo distribution
per §8 v3_handoff.json (NORMATIVE under v1.4; was OPTIONAL under v1.0-v1.3).

**Synthetic generation methodology (NORMATIVE).** For each q_t schedule family `f` in
§3.B's pre-pinned set {F1, F2, F3, F4} and for each observed COP/USD path source `s` in
{Banrep TRM, Mento V3 spot}, generate the per-week time series:

`Δ^(a_s)_t(f, s) = (4 / ((X/Y)̄_t · ε_t · σ_t)) · Σ_{τ ∈ schedule(f, t)} q_τ · f_τ · (X/Y)_τ^{-2}`

where the framework's Δ^(a_s) sensitivity definition (DRAFT.md eq. for `Δ^(a_s)` < 0 from
the imported CPO mathematical framework) is evaluated point-by-point with: q_τ drawn from
the f-th schedule family's pre-pinned parameter spec; (X/Y)_τ drawn from the s-th observed
path; σ_t the realized weekly COP/USD vol from the Stage-1 panel; ε_t and (X/Y)̄_t
computed from the §3.B-pinned discretization. The output is a counterfactual trace of
what Δ^(a_s) WOULD have been each week if a Stage-3 vault had been operating with the
f-th schedule on the s-th observed path. The v0 historical Mento swap flow inventory
serves as a BOUND on the synthetic Δ^(a_s) magnitude — synthetic Δ^(a_s) per week may not
exceed the absolute notional of weekly aggregate non-LP swap flow on the relevant Mento
substrate (this is the "addressable structural exposure" cap from §1 and prevents the
synthetic methodology from claiming a counterfactual magnitude larger than the realized
Mento corridor could plausibly absorb).

**Sensitivity sweep (NORMATIVE).** v2 generates Δ^(a_s)_t(f, s) for ALL combinations of
f ∈ {F1, F2, F3, F4} and s ∈ {Banrep TRM, Mento V3 spot}; results are emitted to
`a_s_counterfactual.parquet` per §4.0 with one row per (f, s, week) tuple. Cross-family
spread of the cumulative simulated Δ^(a_s) over the sample window is computed; if the
cross-family spread exceeds ±20% of the family-mean magnitude, the typed exception
`Stage2PathBSyntheticDriftBeyondTolerance` per §6 fires (indicating schedule choice is
dominating signal; non-robust). Anti-fishing posture: the schedule families F1-F4 are
pre-committed in §3.B BEFORE any v2 generation; tightening or expanding the family set
post-data to chase the ±20% threshold is anti-fishing-banned per §7.

**Path A v3 σ-path coupling (v1.4 NORMATIVE; promoted from OPTIONAL).** Path A v3's MC
σ-path distribution is consumed via `v3_handoff.json` per §8 to enable a scenario-replay
of the synthetic Δ^(a_s) under Path A's simulated FX paths. This produces a secondary
`a_s_counterfactual_pathA_replay.parquet` artifact: one row per (f, path_a_path_idx,
week) tuple, providing the synthetic Δ^(a_s) trace under each of Path A's MC σ-paths
instead of (or alongside) the historical observed path. This coupling is the
v1.4-substantive cross-path handoff change; the convergence dispatch then has two
artifacts to compare against Path A's MC envelope: (i) the historical-path synthetic
Δ^(a_s) and (ii) the Path-A-path-replayed synthetic Δ^(a_s).

CF^(a_l) − CF^(a_s) reconciliation cadence is **monthly** (FLAG-B5), with cumulative-delta
series as standard derivation; per-month surfacing is required to expose regime-conditional
asymmetry (RC FLAG #6 inheritance). Under v1.4 the reconciliation uses (i) realized
CF^(a_l) from v1 against (ii) synthetic CF^(a_s) from v2 per (f, s) combination, producing
one reconciliation series per family-source combination.

**Exit:** `a_s_counterfactual.parquet` emitted with one row per (f, s, week) covering the
v1 sample window; cross-family spread of cumulative Δ^(a_s) computed and reported; if
within the ±20% tolerance, v2 PASSES and proceeds to v3; if outside, the
`Stage2PathBSyntheticDriftBeyondTolerance` typed exception fires per §6 with 5
user-enumerated pivots pre-pinned. Optional `a_s_counterfactual_pathA_replay.parquet`
emitted if Path A v3's `v3_handoff.json` is available at v2 entry. The
`Stage2PathBASOnChainSignalAbsent` exception from v1.0-v1.3 is RETIRED in v1.4 (per the
v1.4 Change Log no-regression assertion: the v1.0-v1.3 expected v2 HALT is RESOLVED by
the synthetic-counterfactual reframe, not by relaxing the standard). The dispatch brief
§6.8 K_l = K_s equilibrium-pricing question becomes a SIMULATED equilibrium under each
(f, s) combination, propagated into v3.

**v3 — CPO P&L retrospective backtest (v1.4 hybrid realized-+-simulated).** Replay the
Mento-V3-availability-window slice of Pair D's realized COP/USD σ-paths through a
theoretical `Π(σ_T) = K · √σ_T` replication using the empirical `r_(a_l)` from v1
(realized) and the synthetic `B_T` calibration / Δ^(a_s) trace from v2 (synthetic, per
(f, s) combination). The σ_T input is **realized monthly log-return-squared from Stage-1
Pair D's COP/USD series** (FLAG-B6); implied vol is rejected as primary because no
historical COP/USD option-market depth exists, making implied a free-fitting parameter
not authorized by the framework. Compute the hybrid CPO P&L for both legs across the
sample window per (f, s) combination — observed Δ^(a_l) realized + simulated Δ^(a_s) per
schedule family. The CPO equilibrium pricing check K_l = K_s (dispatch brief §6.8) becomes
a SIMULATED equilibrium under each (f, s) combination: K_l is calibrated to v1's
empirical r_(a_l); K_s is solved per family from the v2 synthetic Δ^(a_s); the v3 output
reports per-(f, s) the residual K_l − K_s and the convergence dispatch is responsible for
deciding which (f, s) combinations satisfy the equilibrium constraint within tolerance.

**Path A v3 σ-distribution scenario replay (v1.4 NORMATIVE).** v3 ALSO replays the same
hybrid backtest using Path A v3's MC σ-paths (per `v3_handoff.json` per §8) instead of
(or alongside) the realized COP/USD σ-path. This produces a parametric P&L distribution
under Path A's stochastic-σ assumptions, comparable directly against Path A's own MC
envelope. The convergence dispatch then has three quantities to compare per (f, s): (i)
historical-path hybrid envelope from v3, (ii) Path-A-path-replayed hybrid envelope from
v3, and (iii) Path A's pure MC envelope; agreement across all three is the strongest
convergence evidence.

**Exit:** hybrid P&L envelope per (f, s) combination characterized by mean, SD, full
quantile vector, max drawdown, plus a regime-conditional decomposition keyed to the four
regimes RC FLAG #6 identified as over-represented in the 2015-2026 window (subset to the
Mento-V3-availability slice 2023-08 → 2026-02 with regime-coverage caveat). K_l = K_s
residual reported per (f, s). Calibration-handoff packet to Path A v3 ready (includes
`r_al_handoff.json` already emitted at v1 Exit + the v3 envelope JSON per (f, s) + the
Path-A-path-replay envelope JSON per (f, s)).

## §3 — Inputs (sha-pinned + on-chain)

**Stage-1 sha pins (READ-ONLY).** Quoted verbatim in §1 above. The dispatch brief itself at
`contracts/.scratch/2026-04-30-stage-2-m-sketch-dispatch-brief-pair-d.md` is the master input
that prioritizes which candidate flows Path B audits first.

**On-chain pre-pins (a_l side; v1.4 substrate set NORMATIVE).**

- Mento V3 router (Celo): `0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`
- Mento V2 BiPool manager (Celo): `0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901`
- Mento V2 StableTokenCOP (canonical Mento-native COPm per memory
  `project_mento_canonical_naming_2026` β-corrigendum):
  `0x8A567e2aE79CA692Bd748aB832081C45de4041eA`
- Mento V2 StableTokenUSD (Mento-native USDm): `0x765DE816845861e75A25fCA122bb6898B8B1282a`
- Mento broker (Celo; per memory `project_no_mento_carbon_protocol_integration` β-track
  Rev-3 X_d pivot): `0x777A8255cA72412f0d706dc03C9D1987306B4CaD`
- Mento V3 USDm/cUSD FPMM pool (Celo; v1 primary substrate per the v1.4 substrate
  clarification in §2):
  `0x462fe04b4FD719Cbd04C0310365D421D02AaA19E`
- Panoptic factory on Ethereum mainnet: pinned at v0 audit completion. Fixed-allowlist
  discipline per FLAG-B7.

**On-chain pre-pins (a_s side; v1.4 NORMATIVE).** None. Per SYNTHESIS.md §8.1 (user
decision 2026-05-03), no on-chain a_s entity exists in any LATAM corridor researched. The
a_s side is generated synthetically in v2 per §3.B's pre-pinned q_t schedule families and
the §4.0 `a_s_counterfactual.parquet` schema methodology. Pinning speculative a_s
placeholders here would re-create the v1.0-v1.3 false-positive pattern (Bitgifty / Walapay
placeholder pre-pinning produced 2/2 false positive per SYNTHESIS.md §3.1 anti-fishing log
entry); v1.4 deliberately does NOT do that. The DEPRECATED `bitgifty_settlement_celo`,
`walapay_settlement_celo`, `mento_v3_fpmm_usdm_copm_pool_celo`,
`uniswap_v3_usdc_usdm_pool_celo`, and `uniswap_v3_factory_celo` placeholders from v1.0-v1.3
are preserved in the frontmatter `on_chain_pins` block with `DEPRECATED_v1_4` marker and
non-empty reason string for predecessor-chain audit; they MUST NOT be consumed by v0 / v1
/ v2 / v3 executors.

**Architectural template (NOT a substrate; methodology reference only).**

- impactMarket Microcredit (Celo): `0xEa4D67c757a6f50974E7fd7B5b1cc7e7910b80Bb` — used as
  a design reference for the per-loan maturity T + per-installment q_t encoding pattern
  per SYNTHESIS.md §4.3. Informs the §3.B q_t-schedule-family pre-commitment by providing
  a concrete on-chain primitive structure for time-T obligation aggregation. NOT in the
  v0 / v1 audit allowlist; NOT consumed by v2 synthetic generation.

**Block-range bounds (v1.4 revised).** Mento V3 deployment block is the lower bound for
the USDm/cUSD FPMM pool sample (~2023-08); the Mento V2 BiPool USDm/COPm exchange has
deeper history (~2020-onwards) but is the secondary v1 substrate per §2's substrate
clarification. The Pair D 2015-01-31 → 2026-02-28 window is the analytical reference but
the Mento-V3-availability slice 2023-08 → 2026-02 is the binding outer envelope for the
v1 primary substrate. Pre-Mento-V3 history is reachable only through Mento V2 BiPool or
earlier constructions; the Mento V2 secondary substrate extends the reachable window
upstream where the substrate's fee-and-spread structure is known. The fact that the
Mento-V3-availability slice trims the Pair D window is recorded explicitly and does not
constitute anti-fishing window-curation because the trim is forced by data availability
not chosen post-data to improve a result (per §7).

**Time-binning (FLAG-B3, normative).** Daily bins aligned to UTC 00:00:00 are primary. Weekly
aggregation (Mon-anchored) is a standard derivation. Per-block resolution is rejected — it
introduces non-uniform temporal weighting that contaminates the `Σ |FX_t − FX_{t-1}|` shape
check.

**(X/Y)_t reference price (FLAG-B4, normative; v1.4 ladder revised).** Primary: on-chain
Mento V3 USDm/cUSD FPMM pool spot price at daily-bin close-tick (v1.4 substrate
clarification per §2). Fallback-1 if v0 confirms FPMM pool inactive at the relevant
sample: on-chain Mento V2 BiPool USDm/COPm exchange-rate snapshot at daily-bin
close-tick. Fallback-2 if both Mento substrates unusable: Banrep TRM daily series
(off-chain; same source as Pair D Stage-1 X). The v1.0-v1.3 Uniswap V3 USDC/USDm Celo
pool fallback is RETIRED in v1.4 (the placeholder did not correspond to any deployed
Uniswap V3 pool; the canonical USD/USDm liquidity surface on Celo is the Mento V3 FPMM
USDm/cUSD pool). Per-row `price_source` column records source-of-record per observation;
downstream consumers must respect the partition. The v2 synthetic counterfactual generates
Δ^(a_s)_t per (f, s) combination where s ∈ {Banrep TRM, Mento V3 FPMM USDm/cUSD spot}; the
synthetic methodology takes both observed paths through the same q_t schedule families,
producing an additional dimension of sensitivity beyond the family sweep.

**`r_(a_l)` estimator (FLAG-B1, normative).** TWAP-weighted realized fee yield. Estimator
form: numerator = cumulative LP-fee accrual denominated in USD over the v1 sample; denominator
= cumulative |ΔP|-weighted swap-volume denominated in USD over the same sample; regression
form OLS with HAC SE on the fee-accrual-on-|ΔP|-volume specification. Gas-deducted variant is
slot R3 of the v1 robustness pack. Position-weighted (per-LP attribution) is OUT OF SCOPE for
v1 — Path B stays pool-aggregate.

**`q_t` source for a_s (FLAG-B2, normative; v1.4 reframed).** The v1.0-v1.3 q_t source
— on-chain settlement-leg `Transfer` of local-stable to the merchant address from
Bitgifty / Walapay flows — is RETIRED in v1.4. Per SYNTHESIS.md §8.1, no on-chain a_s
entity exists; extraction is structurally impossible because the data source does not
exist. The v1.4 q_t source is the **pre-pinned q_t schedule families enumerated in §3.B**:
F1 (monthly fixed), F2 (weekly fixed), F3 (front-loaded two-payment), F4 (back-loaded
two-payment), with the family parameter spaces fixed in §3.B BEFORE any v2 generation. The
v2 synthetic methodology generates Δ^(a_s)_t under each family on each observed (X/Y)_t
path per FLAG-B4. The FLAG-B2 closure mechanism is preserved in v1.4: q_t is unambiguously
sourced from the spec's pre-commitment in §3.B, not from post-data fitting; the
load-bearing question (where does q_t come from?) is answered by §3.B's pre-pinned
schedule families. Off-chain payment-completion confirmations (webhook responses, bill
provider acknowledgements) are NOT authorized inputs for v2 (preserved from v1.0-v1.3).
The architectural template impactMarket Microcredit `0xEa4D67c757a6f50974E7fd7B5b1cc7e7910b80Bb`
is a methodology reference for how the §3.B families were designed (per-loan maturity T +
per-installment q_t encoding pattern per SYNTHESIS.md §4.3) but is NOT consumed by v2 as
a substrate.

**v1 ↔ v2 reconciliation cadence (FLAG-B5, normative).** Monthly bins. Per-month CF^(a_l)_t
− CF^(a_s)_t reconciliation is primary; cumulative-delta series is standard derivation.
Per-month surfacing is required to expose regime-conditional asymmetry (RC FLAG #6).

**Non-economic transaction partition (FLAG-B8, normative).** Two-layer rule applied to swap
events before fee-yield estimation. Layer-1: drop swaps where `tx.from` is on the Eigenphi (or
equivalent free-tier) MEV-bot allowlist snapshotted at v1 entry. Layer-2: drop swaps where
the same wallet executes paired swap-in / swap-out within a single transaction (atomic-arb
fingerprint). Wash-trading (cross-tx repeated-counterparty cycles) is NOT detected at v1
(Celo MEV depth is materially lower than Ethereum; cost of wash detection exceeds expected
contamination); flagged as v3 sensitivity. Echoes the Carbon V1/V2 user-vs-arb partition
discipline pinned in memory `project_carbon_user_arb_partition_rule`. Dropped-row count and
dropped-volume fraction reported in `audit_summary` per §4.0.

**Data-source candidates (revised per BLOCK-B3 in v1.1; budget-pin re-derived in v1.2
under CORRECTIONS-δ).** Free-tier-only on-chain data sources. The v1.2 budget pin is
**FREE-TIER ONLY** (user directive 2026-05-02) — no paid services authorized. The full
revised tooling stack is in §5 below. The salient v1.0 → v1.1 → v1.2 architectural arc:
**SQD Network public gateways** (FREE; ~5 req/sec per docs.sqd.ai 2025-02-23 notice;
documented Celo + Ethereum mainnet support) is the primary high-volume archive surface,
replacing v1.0's misnamed "Subsquid as escalation" framing (BLOCK-B3 structural fix in
v1.1). Alchemy is now the **free tier** (30M CU/month, 25 req/sec, 500 CU/sec
rolling-window) — v1.1's Growth-tier commitment is rescinded under CORRECTIONS-δ; the
Alchemy role narrows to spot RPC + receipt enrichment under batched + rate-limited
execution discipline pinned in §5.A. The ~2500-credit Dune ceiling (working assumption per
dispatch brief; not formally published on docs.dune.com) is not load-bearing for bulk
extraction (SQD Network absorbs that load) but remains load-bearing for ad-hoc analytical
SQL against pre-existing community tables. Public Celo + Ethereum RPCs (forno.celo.org,
eth.llamarpc.com, rpc.ankr.com/eth) added explicitly in v1.2 as flaky fallback only,
governed by the new `Stage2PathBPublicRPCConsistencyDegraded` typed exception in §6.

## §3.A — Provenance Discipline (normative; resolves BLOCK-B2)

Path B inherits the per-artifact `DATA_PROVENANCE.md` discipline from Stage-1 Pair D. Every
committed dataset (v0 audit artifact, v1 panel, v2 panel, v3 backtest output) MUST be
accompanied by a `DATA_PROVENANCE.md` file in the same directory recording, for each input:

- **source**: data origin URL or contract address + chain (e.g.,
  `sqd_network_gateway://celo-mainnet/contract=0x8A56...41eA/topic0=Transfer`,
  `dune.com/queries/<id>`, `alchemy://eth_getLogs/<block-range>`)
- **fetch_method**: tool + parameters (e.g.,
  `sqd-archive-cli v0.X.Y --network celo-mainnet --block-range 12345-67890`,
  `python sql_alchemy/dune_client.py --query-id 12345`)
- **fetch_timestamp**: ISO-8601 UTC of the fetch
- **sha256**: of the raw fetched payload (pre-transformation) AND of the committed parquet
- **row_count**: post-fetch row count
- **block_range**: `(first_block, last_block)` of the on-chain query window
- **schema_version**: hash of the column-set + dtypes (per §4.0 schema)
- **filter_applied**: descriptive string of any partition rules (e.g.,
  `FLAG-B8-layer-1+layer-2 applied; dropped 412 rows / 0.8% volume`)

**HALT-on-mismatch.** Re-execution of the same fetch must produce a sha256 within ±0.01% row
count and identical schema_version (the row tolerance accommodates new on-chain blocks since
the previous fetch; a non-trivial schema_version drift, a >0.01% row delta inside a frozen
block range, or a sha256 change that cannot be reconciled to known new-block additions
triggers `Stage2PathBProvenanceMismatch` typed exception per §6).

The `DATA_PROVENANCE.md` file format mirrors the Stage-1 Pair D pattern at
`contracts/.scratch/simple-beta-pair-d/data/DATA_PROVENANCE.md`. Field-by-field schema
parity is required; new fields specific to on-chain extraction (`block_range`,
`filter_applied`) are added on top, never instead of, the Stage-1 fields. v1.4 adds a
synthetic-counterfactual provenance field `q_t_schedule_family_pinned` (descriptive
string identifying the §3.B family + parameter spec hash) to the DATA_PROVENANCE.md
template for v2's `a_s_counterfactual.parquet` artifact; the field documents the
pre-commitment string per artifact and is required when the artifact's
`schema_version` field corresponds to the v2 synthetic schema.

## §3.B — q_t schedule family pre-commitment (NORMATIVE; resolves v1.4 a_s reframe)

This section pre-commits the parametric q_t schedule families used by v2 synthetic
counterfactual generation. The pre-commitment is the load-bearing v1.4 anti-fishing
addition: the family set is fixed in spec text BEFORE any v2 generation; the family
parameter spaces are fixed; the sensitivity-sweep tolerance is fixed in §6's typed
exception. Tightening, expanding, or re-parameterizing the family set post-data to chase
either a result or the §6 exception threshold is anti-fishing-banned per §7.

The framework's a_s cash-flow definition (DRAFT.md):

`CF^(a_s)_T = Υ_T(r, θ·D₀^(Y), T) − Σ_t q_t / (X/Y)_t`

with the constraint `Σ_t q_t · (X/Y)_t = B_T` (path-dependent cost-minimization objective)
and `q_t > 0 ∀_t`. The q_t schedule represents the per-period local-currency disbursement
the Stage-3 vault commits to delivering. v2 simulates Δ^(a_s) under each pre-pinned
schedule using the framework's sensitivity definition:

`Δ^(a_s)_t = (4 / ((X/Y)̄_t · ε_t · σ_t)) · Σ_{τ ∈ schedule(f, t)} q_τ · f_τ · (X/Y)_τ^{-2}` < 0

**Pinned family set {F1, F2, F3, F4}.** The four families are pre-committed below. Each
family fixes (a) the schedule shape (per-period disbursement count and timing), (b) the
horizon T, and (c) the per-period notional in local-currency-units relative to a baseline
B_T notional. The baseline B_T is normalized to 1 unit of local currency for synthetic
generation; reporting is in dimensionless ratios that scale linearly with deployment-time
B_T choice.

- **F1 — monthly fixed (T = 12).** Twelve per-period disbursements at uniform monthly
  cadence. q_τ = B_T / 12 for τ ∈ {1, 2, ..., 12} months. Schedule horizon T = 12 months.
  Rationale: prototypical wage-earner monthly-bill-pay schedule (e.g., rent, utilities);
  matches the dispatch-brief Phase-A.0 Y target population (Colombian young workers in
  services with monthly wage cadence per Pair D Stage-1 PASS verdict's Y design).
- **F2 — weekly fixed (T = 52).** Fifty-two per-period disbursements at uniform weekly
  cadence. q_τ = B_T / 52 for τ ∈ {1, 2, ..., 52} weeks. Schedule horizon T = 52 weeks
  (≈12 months). Rationale: prototypical groceries / household-goods cadence; tests
  whether finer-grained q_t partitioning materially changes Δ^(a_s) magnitude relative
  to the monthly-bin F1 baseline.
- **F3 — front-loaded two-payment (T = 12).** Two disbursements: q_1 = 0.5·B_T at τ = 1,
  q_T = 0.5·B_T at τ = T = 12. Schedule horizon T = 12 months. Rationale: prototypical
  semester-payment schedule (e.g., tuition, insurance) where a large initial obligation
  is followed by a deferred residual; tests sensitivity to early concentrated FX-exposure.
- **F4 — back-loaded two-payment (T = 12).** Two disbursements: q_{T-1} = 0.5·B_T at
  τ = T − 1 = 11, q_T = 0.5·B_T at τ = T = 12. Schedule horizon T = 12 months.
  Rationale: prototypical balloon-payment schedule (e.g., end-of-year tax obligation,
  deferred lump-sum) where the bulk obligation lands late in the horizon; tests
  sensitivity to late concentrated FX-exposure under the realized COP/USD path's
  end-of-horizon regime.

The four families span the {uniform, two-payment} × {early, late} parameter cross. They
are NOT exhaustive of the schedule-family space; they are the v1.4-pinned representative
set chosen ex-ante to test (i) cadence sensitivity (F1 vs F2) and (ii) timing-concentration
sensitivity (F3 vs F4). Adding additional families post-data — e.g., a geometric schedule,
a quarterly-fixed schedule, a stochastic-amortization schedule — requires a CORRECTIONS-block
revision of this spec with explicit anti-fishing audit (the new family set must be
pre-committed BEFORE re-running v2; the new family must not be selected because it
produces a more favorable Δ^(a_s) on the existing data).

**ε_t and (X/Y)̄_t discretization (NORMATIVE).** ε_t (small-perturbation parameter from the
DRAFT.md derivation) is fixed to 0.01 (1% spot-perturbation) for all weeks; sensitivity
to ε_t = 0.005 and ε_t = 0.02 is reported as a v3-side robustness companion but does not
change v2 primary output. (X/Y)̄_t is the trailing-4-week mean of (X/Y)_t per the chosen
path source s; window edges use the maximum-available trailing window.

**Synthetic generation cadence (NORMATIVE).** v2 generates Δ^(a_s)_t at WEEKLY cadence
aligned to UTC Monday 00:00:00, matching the §3 Time-binning weekly-derivation cadence.
This is consistent with the FLAG-B5 monthly reconciliation cadence (4-5 weeks per
calendar month) and the Stage-1 panel cadence; q_τ disbursements are temporally
distributed across weeks per family-specific rules (F1: q_τ lands in the first week of
each calendar month; F2: q_τ lands every Monday; F3: q_τ at week 1 and week 52; F4: q_τ
at week 47 and week 52 of each rolling 52-week horizon).

**Sample-window scope for v2 (NORMATIVE).** v2 generates Δ^(a_s) over the
Mento-V3-availability window 2023-08 → 2026-02 (binding outer envelope per §3
Block-range bounds revised in v1.4); the Pair D 2015-2026 window is NOT in v2's scope
because (a) v0's `mento_swap_flow_inventory.parquet` is not extractable pre-Mento-V3
deployment and (b) the v2 bound check (synthetic Δ^(a_s) per week ≤ weekly aggregate
non-LP swap flow) requires the inventory.

**B_T baseline (NORMATIVE).** B_T is normalized to 1 unit of local currency (COP) for the
synthetic-generation primary; the simulated Δ^(a_s) trace is dimensionless and scales
linearly with deployment-time B_T choice. The v3 reporting layer optionally rescales
Δ^(a_s) to USD-notional using a baseline scaling factor B_T = 1 USD-equivalent (COP)
where the conversion uses the (X/Y)̄_t under the corresponding path source.

**Cross-family spread tolerance (NORMATIVE).** Cross-family spread of cumulative
simulated Δ^(a_s) over the v2 sample window is computed as
`max_f(|Σ_t Δ^(a_s)_t(f, s_primary)|) − min_f(|Σ_t Δ^(a_s)_t(f, s_primary)|)` divided by
the family-mean magnitude. If this ratio exceeds 0.20 (i.e., ±20% spread), the typed
exception `Stage2PathBSyntheticDriftBeyondTolerance` per §6 fires. The 20% threshold is
pre-committed in v1.4; tightening it to 10% to force a HALT on a clean synthetic, or
loosening it to 50% to absorb a sweep that revealed the schedule-choice was the dominant
signal, is anti-fishing-banned per §7.

## §4 — Outputs

**v0:** data-coverage audit report conforming to §4.0 normative schema (FOUR artifacts under
v1.4: the existing `audit_summary.parquet`, `address_inventory.parquet`,
`event_inventory.parquet` PLUS the new `mento_swap_flow_inventory.parquet` required by v2
per §3.B's bound-check) plus co-located `DATA_PROVENANCE.md` per §3.A. Frontmatter
`on_chain_pins` validated against on-chain state (no longer "freezing" since v1.4 pins are
already pre-committed in spec text; v0 confirms each substrate has the documented event
activity in the audit window). Findings memo (1-2 pp) recommending which a_l-side
candidates graduate to v1 with data-availability reasons (not result-shaping reasons), and
documenting that the v1.0-v1.3 a_s-side audit task (Bitgifty / Walapay) is closed-without-
substrate per the v1.4 SYNTHESIS.md acknowledgment.

**v1:** per-substrate empirical `CF^(a_l)` time series (daily-binned per FLAG-B3,
constrained to the Mento-V3-availability window 2023-08 → 2026-02 per §3 v1.4 Block-range
revision), estimated `r_(a_l)` with HAC SE per substrate (Mento V3 USDm/cUSD primary;
Mento V2 USDm/COPm secondary), qualitative shape-check chart against
`Σ r·|FX_t − FX_{t-1}|`, `r_al_handoff.json` per FLAG-B9 schema (carrying both substrate
r_(a_l)s), plus co-located `DATA_PROVENANCE.md` per §3.A. Optional
`v1_lvr_decomposition.parquet` if §5 budget permits. Findings memo recommending whether
v2 synthetic generation proceeds (default YES under v1.4) or v1 alone provides sufficient
empirical defensibility for the M-sketch a_l-side leg.

**v2 (v1.4 REFRAMED per CORRECTIONS-ε):** synthetic structural-exposure cash-flow series
for the a_s leg, generated per §3.B's pre-pinned q_t schedule families {F1, F2, F3, F4}
on each observed (X/Y)_t path source s ∈ {Banrep TRM, Mento V3 spot}, emitted as the
`a_s_counterfactual.parquet` artifact per the §4.0 v1.4-additive schema. Cross-family
spread of cumulative Δ^(a_s) computed and reported in the findings memo; if within the
±20% tolerance per §3.B, v2 PASSES; if outside, the
`Stage2PathBSyntheticDriftBeyondTolerance` typed exception fires per §6 with 5
pre-pinned pivots. Optional `a_s_counterfactual_pathA_replay.parquet` companion artifact
emitted if Path A v3's `v3_handoff.json` is available at v2 entry per §8 v1.4-promoted
handoff. Co-located `DATA_PROVENANCE.md` per §3.A with the v1.4 `q_t_schedule_family_pinned`
field populated. The deliverable is structural-exposure characterization of the
hypothetical a_s leg's cash-flow geometry under pre-pinned schedules, NOT a
behavioral-demand or WTP estimate (see §1 framing definition); see the v1.4 Change Log
for why the v1.0-v1.3 v2 HALT site (`Stage2PathBASOnChainSignalAbsent`) is RETIRED in
v1.4.

**v3 (v1.4 hybrid realized-+-simulated):** hybrid CPO P&L distribution per (f, s)
combination over the Mento-V3-availability-window slice 2023-08 → 2026-02, characterized
by mean, SD, full quantile vector, max drawdown, plus regime-conditional decomposition
keyed to RC FLAG #6 regimes (subset to the slice with regime-coverage caveat).
K_l = K_s residual reported per (f, s). Calibration-handoff packet to Path A v3
(empirical `r_(a_l)` carried forward from v1's `r_al_handoff.json`, the v2-emitted
synthetic Δ^(a_s) trace per family for the K_s side, hybrid envelope) as JSON plus tabular
CSV per (f, s). If Path A v3's `v3_handoff.json` is consumed at v3 entry per §8 v1.4
NORMATIVE coupling, an additional Path-A-path-replay envelope per (f, s) is emitted as
companion JSON. Findings memo characterizing the envelope and flagging convergence
questions per (f, s) combination.

## §4.0 — v0 Output Schema (normative; resolves BLOCK-B1; v1.4-additive: new venue_kind
enum entries + new `mento_swap_flow_inventory.parquet` artifact + new
`a_s_counterfactual.parquet` artifact for v2)

Under v1.4 the v0 emission expands from three artifacts to FOUR; v2 emits an additional
`a_s_counterfactual.parquet` per the schema below. The v1.0 → v1.3 schemas for
`audit_summary.parquet`, `address_inventory.parquet`, `event_inventory.parquet` are
PRESERVED — BLOCK-B1 closure is preserved with ADDITIONS only. Naming is fixed; column
order is fixed; dtypes are fixed.

All artifacts emitted in `parquet` format (per Pair D notebook convention) at
`contracts/.scratch/pair-d-stage-2-B/v0/` (for v0 artifacts) or
`contracts/.scratch/pair-d-stage-2-B/v2/` (for v2 artifacts).

**Artifact 1: `audit_summary.parquet`** — one row per audited venue.

| column | dtype | nullable | description |
|---|---|---|---|
| `venue_id` | string | NO | stable slug, e.g., `mento_v3_fpmm_usdm_cusd_celo` (v1.4 example reflects v1.4 substrate clarification) |
| `venue_name` | string | NO | human-readable, e.g., `Mento V3 FPMM USDm/cUSD` |
| `network` | string | NO | one of `celo-mainnet`, `ethereum-mainnet` |
| `contract_address` | string | NO | 0x-prefixed checksummed address |
| `venue_kind` | string | NO | one of `mento_fpmm`, `mento_v2_bipool` (v1.4 NEW), `mento_broker` (v1.4 NEW), `uniswap_v3_pool` (DEPRECATED v1.4 — preserved for predecessor-chain audit), `uniswap_v4_pool`, `panoptic_factory`, `bill_pay_router` (DEPRECATED v1.4 — no on-chain a_s entity exists per SYNTHESIS.md §8.1), `remittance_router` (DEPRECATED v1.4 — same reason) |
| `deployment_block` | int64 | NO | block number of contract deployment |
| `first_event_block` | int64 | YES | block of first relevant event; null if no events |
| `last_event_block` | int64 | YES | block of last relevant event in audit window; null if no events |
| `event_count` | int64 | NO | count of relevant events in audit window (0 allowed; triggers HALT review per §6) |
| `cumulative_volume_usd` | float64 | YES | sum of swap-volume USD-equivalent if applicable; null for non-pool venues |
| `tvl_usd_snapshot` | float64 | YES | TVL at snapshot timestamp; null where N/A |
| `snapshot_timestamp_utc` | timestamp[ns,UTC] | NO | ISO-8601 UTC of the audit snapshot |
| `audit_block` | int64 | NO | block number used as the audit's "now" |
| `data_source_primary` | string | NO | one of `sqd_network`, `alchemy_free`, `dune`, `the_graph`, `celoscan`, `etherscan` (v1.2.1 corrects `alchemy_growth` → `alchemy_free` to align with §5 free-tier-only stack) |
| `feasibility_v1` | string | NO | one of `pass`, `marginal`, `halt` |
| `feasibility_notes` | string | YES | freeform; required if `feasibility_v1` is `marginal` or `halt` |

Primary key: `(venue_id)`. Uniqueness constraint: `venue_id` unique within file.
Row-count expectation: 6-12 rows (the named pre-pins + Mento V3 manifest entries); <4 or >20
triggers HALT-review per §6 (`Stage2PathBAuditScopeAnomaly`).

**Artifact 2: `address_inventory.parquet`** — one row per unique on-chain address discovered
within the audit allowlist. Distinct from `audit_summary` because a venue can involve multiple
addresses (router, factory, pool implementation, fee collector).

| column | dtype | nullable | description |
|---|---|---|---|
| `address` | string | NO | 0x-prefixed checksummed |
| `network` | string | NO | one of `celo-mainnet`, `ethereum-mainnet` |
| `venue_id` | string | NO | foreign key to `audit_summary.venue_id` |
| `address_role` | string | NO | one of `router`, `factory`, `pool`, `token`, `fee_collector`, `merchant`, `user_eoa`, `mev_bot`, `other` |
| `is_contract` | bool | NO | true if `eth_getCode` returns nonempty |
| `first_seen_block` | int64 | NO | block of first inbound or outbound transaction |
| `last_seen_block` | int64 | NO | block of last inbound or outbound transaction in audit window |
| `tx_count_window` | int64 | NO | total transactions in audit window |

Primary key: `(network, address)`. Foreign key: `(venue_id)` references
`audit_summary.venue_id`. Row-count expectation: 10-200 rows; <5 triggers HALT review.

**Artifact 3: `event_inventory.parquet`** — one row per (venue, event_topic) pair recording
event-frequency in audit window.

| column | dtype | nullable | description |
|---|---|---|---|
| `venue_id` | string | NO | foreign key to `audit_summary.venue_id` |
| `event_signature` | string | NO | canonical event signature, e.g., `Swap(address,uint256,uint256,uint256,uint256,address)` |
| `topic0` | string | NO | keccak256 of event signature, 0x-prefixed |
| `event_count` | int64 | NO | count of emissions in audit window |
| `first_emit_block` | int64 | YES | null if `event_count == 0` |
| `last_emit_block` | int64 | YES | null if `event_count == 0` |
| `relevance_v1` | string | NO | one of `cf_al_input`, `cf_as_input`, `oracle_input`, `metadata`, `unused` |

Primary key: `(venue_id, topic0)`. Row-count expectation: 2-8 rows per venue.

**Artifact 4 (v1.4 NEW): `mento_swap_flow_inventory.parquet`** — emitted by v0 — one row
per (week, mento_substrate, partition) tuple recording aggregate Mento swap-flow notional
required as the v2 bound-check input per §3.B. Distinct from `event_inventory.parquet`
because that artifact is one-row-per-(venue, topic) for audit purposes; this one is
per-week aggregated USD-equivalent flow used by the v2 synthetic generator.

| column | dtype | nullable | description |
|---|---|---|---|
| `week` | timestamp[ns,UTC] | NO | UTC Monday 00:00:00 anchor of the week |
| `mento_substrate` | string | NO | one of `mento_v3_fpmm_usdm_cusd`, `mento_v2_bipool_usdm_copm`, `mento_broker` |
| `partition` | string | NO | one of `non_lp_user`, `lp_mint_burn`, `mev_arb`, `total` (FLAG-B8 partition discipline applied) |
| `swap_count_week` | int64 | NO | count of swap / exchange events in week within the partition |
| `notional_usd_week` | float64 | NO | aggregate USD-equivalent notional flow in week within the partition |
| `non_lp_user_share` | float64 | YES | when `partition == 'total'`, the fraction of notional attributable to `non_lp_user`; null otherwise |
| `data_source_primary` | string | NO | matches `audit_summary.data_source_primary` enum |

Primary key: `(week, mento_substrate, partition)`. Foreign key implicit:
`mento_substrate` values map to corresponding `audit_summary.venue_id`s. Row-count
expectation: ~135 weeks × 3 substrates × 4 partitions ≈ 1620 rows for the
2023-08 → 2026-02 window; ±50% deviation acceptable; >5x deviation triggers a HALT
review under `Stage2PathBAuditScopeAnomaly`.

**Artifact 5 (v1.4 NEW): `a_s_counterfactual.parquet`** — emitted by v2 — one row per
(q_t_schedule_family, schedule_params, week, cop_usd_path_source) tuple recording the
synthetic Δ^(a_s) trace under each (f, s) combination per §3.B. This is the v1.4
substantive schema addition that replaces the v1.0-v1.3 v2 panel (which was scoped to
on-chain settlement-leg `Transfer` extraction; never realized; RETIRED in v1.4).

| column | dtype | nullable | description |
|---|---|---|---|
| `q_t_schedule_family` | string | NO | one of `F1_monthly_fixed`, `F2_weekly_fixed`, `F3_front_loaded_two_payment`, `F4_back_loaded_two_payment` per §3.B pre-commitment |
| `q_t_schedule_params` | string | NO | JSON-encoded family-specific parameter spec hash (e.g., `{"T_months":12,"per_period_share":0.0833}` for F1); the hash is a content-addressed sha256 of the canonical-form JSON for cross-artifact provenance discipline |
| `week` | timestamp[ns,UTC] | NO | UTC Monday 00:00:00 anchor of the week the synthetic Δ^(a_s) is evaluated for |
| `cop_usd_path_source` | string | NO | one of `banrep_trm` (off-chain Stage-1 daily series resampled to weekly close), `mento_v3_spot` (Mento V3 USDm/cUSD FPMM spot at weekly close-tick) |
| `delta_a_s_synthetic` | float64 | NO | simulated dimensionless Δ^(a_s) magnitude under (family, params, week, path_source); per-week framework-evaluated value < 0 |
| `sigma_realized_weekly` | float64 | NO | realized weekly COP/USD log-return-squared from Stage-1 panel (FLAG-B6 cadence); used in the framework's Δ^(a_s) sensitivity formula |
| `mento_swap_flow_usd` | float64 | NO | aggregate USD-equivalent notional of `non_lp_user` partition for the relevant Mento substrate from `mento_swap_flow_inventory.parquet`, used as the v2 bound-check |
| `delta_a_s_synthetic_bound_violation` | bool | NO | true if `abs(delta_a_s_synthetic) * scale_factor > mento_swap_flow_usd`, where `scale_factor` is the deployment-time B_T choice (default 1 USD-equivalent COP); flags weeks where the synthetic methodology claims a counterfactual magnitude larger than the realized Mento corridor could plausibly absorb |
| `epsilon_t_pinned` | float64 | NO | small-perturbation parameter from §3.B discretization, default 0.01 |
| `xy_bar_t_pinned` | float64 | NO | trailing-4-week mean of (X/Y)_t per the path source |
| `schema_version` | string | NO | hash of column-set + dtypes; v1.4-pinned value matches the v1.4 a_s_counterfactual schema |

Primary key: `(q_t_schedule_family, week, cop_usd_path_source)`. Foreign key:
(`week`, mapped via §3.B Mento substrate selection) → `mento_swap_flow_inventory`.
Row-count expectation: 4 families × 2 path sources × ~135 weeks ≈ 1080 rows for the
2023-08 → 2026-02 window. The cross-family spread tolerance per §3.B is computed
post-emission from this artifact; if the §3.B ±20% threshold is exceeded, the
`Stage2PathBSyntheticDriftBeyondTolerance` typed exception per §6 fires before any
downstream v3 consumption.

**Artifact 6 (v1.4 OPTIONAL): `a_s_counterfactual_pathA_replay.parquet`** — emitted by v2
when Path A v3's `v3_handoff.json` is available at v2 entry per §8 v1.4-promoted handoff
— one row per (q_t_schedule_family, path_a_path_idx, week) tuple recording the synthetic
Δ^(a_s) trace under Path A's MC σ-paths instead of (or alongside) the historical observed
path. Schema mirrors Artifact 5 with `cop_usd_path_source` replaced by `path_a_path_idx`
(int64 range [0, path_a_v3_handoff.path_count − 1]); preserves the v1.4 v3 hybrid
backtest's optional Path-A-path-replay envelope.

**File format.** Apache Parquet with Snappy compression (project convention from Pair D
notebooks). Schema metadata MUST include `schema_version` field hashing the column-set +
dtypes; consumers MUST verify match before reading.

**Naming.** Exact filenames `audit_summary.parquet`, `address_inventory.parquet`,
`event_inventory.parquet`, `mento_swap_flow_inventory.parquet` in
`contracts/.scratch/pair-d-stage-2-B/v0/`. v2 artifacts `a_s_counterfactual.parquet` and
optional `a_s_counterfactual_pathA_replay.parquet` in
`contracts/.scratch/pair-d-stage-2-B/v2/`.

## §5 — Tooling stack + budget pin (revised per BLOCK-B3 in v1.1; CORRECTIONS-δ in v1.2)

The Path B tooling budget pin is **FREE-TIER ONLY** (user directive 2026-05-02; supersedes
v1.1's `$49/mo Alchemy Growth` commitment). No paid services authorized under v1.2; any
escalation requires typed-exception HALT with user-adjudicated re-budgeting per §6 and the
§5.A degradation Step 5 protocol (v1.2.1 corrects v1.2's stale Step 4 reference; under
CORRECTIONS-δ public-RPC fallback was inserted as Step 4 and paid-escalation moved to Step 5). v1.0 listed Subsquid as "free in compute" — v1.1
disambiguated this (Subsquid Cloud is paid hosted indexer; SQD Network is the free
decentralized data lake; structural distinction PRESERVED in v1.2).

**Primary high-volume archive surface: SQD Network public gateways (FREE).**

- SQD Network is the decentralized data lake at the foundation of the Subsquid ecosystem.
  Public gateways documented at https://docs.sqd.ai/subsquid-network/reference/networks/.
- Celo mainnet gateway: `https://v2.archive.subsquid.io/network/celo-mainnet`
- Ethereum mainnet gateway: `https://v2.archive.subsquid.io/network/ethereum-mainnet`
- Cost model per official documentation 2026-05-02 verification: free public access; rate
  limit `50 requests / 10 seconds per IP` per the 2025-02-23 notice on the networks
  reference page (effective ~5 req/sec sustained per IP). Documentation indicates "higher
  bandwidths will soon become available via the public network" but no looser limit is
  published as of v1.2 verification.
- Use case in Path B: bulk extraction of swap events, transfer events, pool-deployment
  events for v0 + v1 + v2. SQD Network is the v1.2 primary archive surface — its bulk
  extraction model returns full event lists in a single HTTPS call per query window, so
  the 5 req/sec rate limit is rarely the binding constraint for bulk pulls; it matters only
  if multiple chunked windows are issued in tight succession.
- Throttling response: per §6 typed exception `Stage2PathBSqdNetworkThrottled`; degradation
  ladder per §5.A.

**Spot RPC + receipts: Alchemy free tier (30M CU/month, 25 req/sec, 500 CU/sec
rolling-window cap; verified 2026-05-02).**

- v1.2 demotes Alchemy from v1.1's Growth-tier commitment to the free tier. The role
  narrows: spot-check `eth_call` for current-state snapshots (TVL, pool prices) in v0,
  transaction-receipt fetching where event extraction needs `tx.from` for FLAG-B8 layer-1
  partitioning, fallback enrichment when SQD Network does not surface a needed field.
- Celo network support: per alchemy.com/pricing 2026-05-02, free tier covers "all mainnets
  and testnets." v0 audit re-verifies Celo is enumerated in the Alchemy chain directory
  before committing FLAG-B8 layer-1 partitioning to the Alchemy path; if Celo archive
  depth is paid-tier-gated, FLAG-B8 layer-1 partitioning relies on `tx.from` field already
  present in the SQD Network swap event payload (no external enrichment needed).
- Burst-rate discipline: see §5.A burst-rate analysis sub-clause. Path B execution must
  smooth request bursts to stay below 25 req/sec sustained and 500 CU/sec rolling-window;
  exceedance triggers `Stage2PathBAlchemyFreeTierRateLimitExceeded` typed exception per §6.
- Monthly-CU discipline: see §5.A projection. Aggregate Path B usage projected at ~165K-285K
  CU/month — ~0.5-1% of 30M cap — comfortable headroom; CU-cap exceedance is low-risk and
  governed by `Stage2PathBAlchemyFreeTierMonthlyCUExceeded` typed exception per §6.

**Ad-hoc analytical SQL: Dune Analytics free tier (~2500 credits/month working assumption;
docs.dune.com does not publish a numeric monthly cap; rate limits 15 rpm low-limit endpoint
+ 40 rpm high-limit endpoint per docs.dune.com/api-reference/overview/rate-limits verified
2026-05-02).**

- Pre-existing community tables on Dune (e.g., `mento.swaps`, `uniswap_v3_celo.swaps`,
  `panoptic_ethereum.events` where coverage exists) provide ad-hoc analytical surfaces
  useful for spot-checks and findings-memo charts.
- The ~2500-credit ceiling is the dispatch-brief working assumption; Dune does not publish
  a numeric monthly free-tier cap on docs.dune.com/api-reference/overview/billing as of
  2026-05-02 verification. Re-verified at v0 entry via dashboard inspection. The ceiling
  is NOT load-bearing for bulk extraction (SQD Network absorbs that load) but IS
  load-bearing for ad-hoc SQL: a careless query scanning multiple months of swap data can
  consume 50-200 credits. Pre-flight cost estimation required before each Dune query
  (Dune surfaces estimated cost at query-edit time).
- Pivot if exhausted: switch to Flipside Crypto free SQL credits, or write the same query
  against SQD Network primitives. Paid Dune Analyst tier is explicitly NOT authorized under
  v1.2 free-tier-only pin.

**Subgraphs: The Graph hosted service (free for pre-existing subgraphs).**

- Mento V3, Uniswap V3 Celo, and Panoptic Ethereum all have community subgraphs as of
  2026-04. v0 confirms subgraph existence per venue; preferred over raw `eth_getLogs` where
  coverage exists AND where SQD Network does not give cleaner schema.
- Use case in Path B: ergonomic typed-event access for findings-memo prep when SQD Network
  raw-log extraction is heavier than needed; degradation fallback per §5.A Step 1 if SQD
  Network throttles or has a coverage gap.

**Block explorer: Celoscan + Etherscan free-tier API (5 req/s).**

- Ad-hoc verification, source-code lookup, transaction decoding for human-readable audit
  notes only. NEVER for bulk extraction.

**Public RPC fallback: forno.celo.org (Celo), eth.llamarpc.com + rpc.ankr.com/eth
(Ethereum). NEW IN v1.2.**

- Free; rate-limited (limits not published; observed flakiness common); intermittent
  consistency. Used ONLY when Alchemy free tier is exhausted (CU or rate limit) AND SQD
  Network is unreachable AND The Graph subgraph is unavailable. Governed by the new
  `Stage2PathBPublicRPCConsistencyDegraded` typed exception in §6 — when public RPCs
  return inconsistent data across calls (different block heights, missing logs,
  receipt-vs-trace mismatches), the disposition is HALT-and-flag, not silent merge.

**Notebook stack: Jupyter + pandas + statsmodels + sympy (free; local).**

- Inherited from the Pair D notebook environment at
  `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/`. Path B notebooks live at
  `contracts/notebooks/pair_d_stage_2_path_b/` (subdirectory pinned at v0 entry).

**Local data substrate: DuckDB + Parquet (free; local).**

- All extracted on-chain data persists to local Parquet artifacts per §4.0 schema; analytical
  queries against the local panel use DuckDB. No network round-trips, no rate limits, no
  cost. Inherited from the Pair D Stage-1 architecture.

**Paid escalation only — NOT authorized under v1.2 spec without explicit user re-budgeting:**

- Subsquid Cloud (hosted indexer-as-a-service) — pay-as-you-go above free playground tier.
  Re-authorization requires typed-exception HALT per §6 with user-adjudicated cost
  ceiling.
- Dune Analyst tier ($89/mo) — credit ceiling lifted; not auto-authorized.
- Alchemy paid tier above free (Growth, Scale, Enterprise) — explicitly NOT authorized
  under v1.2; v1.1's Growth commitment is rescinded under CORRECTIONS-δ. If the Alchemy
  free-tier CU or rate-limit cap is hit, the v1.2 fallback is to lean harder on SQD Network
  + The Graph subgraphs + public-RPC fallback (in that order, per §5.A degradation ladder)
  rather than upgrade Alchemy.
- Eigenphi paid API for FLAG-B8 layer-1 MEV-bot list — if Eigenphi free-tier access has
  been retired since the dispatch brief was authored, the fallback is the
  Flashbots-published mev-inspect-py labelled-address sets / LibMEV / zeromev.org public
  registries (all free); paid Eigenphi access requires explicit user re-budgeting.

Frontmatter records `tooling_budget_pending: false; budget_pin: free_tier_only;
tooling_budget_committed: free-tier only; primary_data_path_v1_2: SQD Network public
gateway`.

**v1.4 budget impact (PRESERVED FREE-TIER-ONLY).** Synthetic counterfactual generation in
v2 is local Python compute over the v0-emitted `mento_swap_flow_inventory.parquet` plus
the Stage-1 panel; ZERO RPC calls; ZERO additional Alchemy CU; ZERO additional Dune
credits. The v1.4 v2 footprint is materially smaller than the v1.0-v1.3 v2 footprint
(which scoped on-chain settlement-leg `Transfer` extraction at ~50-75 SQD queries +
<30K Alchemy CU per the §5.A v1.0-v1.3 v2 projection); the v1.4 v2 line in §5.A's
"v2 CF^(a_s) extraction volume projection" is therefore RETIRED — the new v2 is local
compute and does not appear in the §5.A network-side projections. v0 + v1 free-tier
projections remain UNCHANGED (the Mento-substrate pin overhaul does not change the
order-of-magnitude swap-event counts; v1's Mento V3 USDm/cUSD substrate has comparable
event-count to v1.0-v1.3's mis-named "Mento V3 USDm/COPm" placeholder).

## §5.A — Query-volume projection + budget reconciliation (normative; resolves BLOCK-B3 in v1.1; re-derived under CORRECTIONS-δ in v1.2)

Concrete projection of Path B query volume per data source, used to verify the v1.2
free-tier-only architecture is feasible. v1.1's projection assumed $49/mo Alchemy Growth
(49M CU/day ≈ 1.47B CU/month). v1.2 re-derives against Alchemy free tier (30M CU/MONTH;
49× tighter on monthly CU) plus the SQD Network 5 req/sec rate cap that was previously
treated as "no documented limit." Monthly-CU headroom remains comfortable; the binding
constraint shifts from monthly-CU to burst rate.

**v0 audit volume projection (free-tier).**

- `address_inventory` discovery within allowlist: ~10 contracts × 1 RPC call each
  (`eth_getCode` + first/last block scan) ≈ 30-50 Alchemy CU per contract = ~500 CU total.
  Negligible vs 30M/month free cap (~0.002%).
- `event_inventory` topic-frequency scan: ~10 contracts × 5 topics × 1 SQD Network archive
  query each = ~50 SQD queries spread across one v0 session; FREE; well below 5 req/sec
  with sequential issuance.
- `audit_summary` aggregation: ~10 venues × cumulative-volume + TVL = 20-30 Alchemy
  `eth_call`s ≈ 1000 CU. Negligible.
- v0 total: <5000 Alchemy CU (single-day, well inside 30M/mo); ~50 SQD queries spread
  across minutes (well below 5 req/sec); 0-5 Dune credits (only if a community-table-backed
  sanity-check query is convenient).

**v1 CF^(a_l) extraction volume projection (free-tier; v1.4 substrate set).**

- Mento V3 USDm/cUSD FPMM pool swap events (v1.4 primary substrate per §2 clarification)
  over Mento-V3-deployment to 2026-02-28 window: estimate 100K-500K swaps depending on
  pool age + activity. SQD Network archive query returns the full event list per chunked
  block-range query — pre-pin chunk size of ~500K blocks per query (Celo block time ~5 sec
  → ~29 days per chunk; Mento V3 history is ~2 yrs at most → ~25 chunks); FREE; sequential
  issuance with ~250 ms inter-call sleep keeps issuance well below 5 req/sec.
- Mento V2 BiPool USDm/COPm exchange events (v1.4 secondary substrate per §2
  clarification) over Mento-V2-deployment-relevant slice: similar order of magnitude;
  same chunked SQD Network surface; FREE. The v1.0-v1.3 "Uniswap V3 USDC/USDm Celo pool"
  projection is RETIRED in v1.4 (placeholder DEPRECATED in frontmatter `on_chain_pins`).
- Per-event LP-fee accrual computation requires either: (a) on-chain `Mint`/`Burn` events
  (also extractable via SQD Network in the same chunked pull; FREE), OR (b) per-block
  reserve snapshots (more expensive but not needed if approach (a) is sufficient).
- FLAG-B8 layer-1 partition (MEV-bot allowlist): `tx.from` is included in the SQD Network
  swap event payload; no Alchemy receipt enrichment needed. If a small subset of swaps
  requires receipt-level confirmation (e.g., 1000 ambiguous swaps), Alchemy
  `alchemy_getTransactionReceipts` at 15 CU per receipt × 1000 receipts = 15K CU
  (~0.05% of free cap), batched in 25-receipt windows at 1 batch/sec to stay below 25
  req/sec.
- FLAG-B8 layer-2 partition (atomic-arb round-trip): per-tx event grouping computed
  locally from the SQD Network bulk extract; FREE.
- v1 total: ~25-75 SQD Network chunked queries per pool × 1-3 pools = ~25-225 SQD queries
  total spread across ~5-30 minutes of execution (well below 5 req/sec); ~15K-50K Alchemy
  CU for spot-check enrichment if needed; ~20-50 Dune credits for findings-memo charts.

**v2 CF^(a_s) projection (v1.4 RETIRED; replaced by synthetic-counterfactual local
compute).** Per the v1.4 reframe in §2 + §3.B + §4.0 Artifact 5, v2 no longer extracts
on-chain settlement-leg `Transfer` events from Bitgifty / Walapay because those entities
do not exist on-chain (SYNTHESIS.md §3.1 / §8.1). v2 is now local Python compute over the
v0-emitted `mento_swap_flow_inventory.parquet` plus the Stage-1 panel, generating Δ^(a_s)
under the §3.B-pinned q_t schedule families and observed (X/Y)_t paths. ZERO RPC calls;
ZERO additional Alchemy CU; ZERO additional Dune credits. The v1.0-v1.3 v2 projection of
~50-75 SQD Network queries + <30K Alchemy CU is RETIRED — those numbers no longer apply
under v1.4. Optional `a_s_counterfactual_pathA_replay.parquet` artifact emission also has
zero network footprint (Path A v3's `v3_handoff.json` is a local-file consumed input).

**v3 backtest computational load.**

- Pure local computation (Python + statsmodels + numpy + DuckDB) over v1 + v2 extracted
  panels. Zero on-chain queries; zero Alchemy CU; zero Dune credits.

**Aggregate monthly usage estimate (v1.4 revised: v2 footprint removed).**

- SQD Network: ~75-270 queries total across v0 + v1 spread across multi-hour execution
  windows (v1.4 retires the v1.0-v1.3 v2 ~50-75-query block; v1.4 v2 is local compute);
  FREE; sustained issuance well below 5 req/sec per IP; throttling risk LOW given chunked
  sequential pattern, mitigated by §6's `Stage2PathBSqdNetworkThrottled` typed exception
  if exceeded.
- Alchemy free tier: ~20K-65K CU total across v0 + v1 (v1.4 retires the v1.0-v1.3 v2
  ~10-30K CU receipt-enrichment block); ~0.07-0.22% of 30M monthly cap with >150× headroom;
  rate-limit risk LOW given batched 25-receipt windows at 1 batch/sec (well below 25
  req/sec sustained); CU-cap risk LOW per projection but pre-pinned exception
  `Stage2PathBAlchemyFreeTierMonthlyCUExceeded` covers re-run accumulation.
- Dune: <80 credits total (v1.4 reduces from <100 by retiring v2's findings-memo Dune
  charts that no longer have a panel substrate); ~3% of working ~2500/mo assumption;
  ample headroom; rate limit risk LOW given sub-15 rpm interactive query cadence.
- The Graph: opportunistic free queries; bounded by community-subgraph availability.
- Celoscan + Etherscan: ad-hoc only; bounded by 5 req/s.
- Public RPC fallback: opportunistic; flakiness governed by
  `Stage2PathBPublicRPCConsistencyDegraded` typed exception.

**Burst-rate analysis sub-clause (NEW IN v1.2; binding-constraint pinning).**

The Alchemy free-tier 25 req/sec cap (and 500 CU/sec rolling-window cap) is the binding
constraint on Path B execution under v1.2's free-tier-only pin, NOT the monthly-CU cap.
v1 fee-yield extraction and v2 settlement-leg extraction both have low total-CU
fingerprints but can produce burst patterns if implemented naively (e.g., a parallel
asyncio fan-out of 100 receipt fetches in a single second would exceed the cap).

Path B execution discipline (binding):

- All Alchemy receipt enrichment batched into ≤25-receipt request windows separated by
  ≥1 second sleep, regardless of total receipt budget. Concurrency cap = 1 (sequential).
- All SQD Network chunked queries issued sequentially with ≥250 ms inter-call sleep.
  Concurrency cap = 1 per IP.
- All Dune queries sequential; pre-flight cost-estimate inspection before each execution.
- Rolling-window monitoring: executor MUST log `req_per_sec` and `cu_per_sec` to a local
  audit log per data source per minute; monitoring spike >80% of either cap surfaces a
  warning and pauses next batch ≥5 sec.
- Exceedance of either cap triggers `Stage2PathBAlchemyFreeTierRateLimitExceeded` typed
  exception per §6 with disposition = pause, reduce concurrency / chunk size, retry; if
  exceedance recurs after retry, HALT-and-flag.

This batched-extraction strategy smooths req/sec over the day so the Path B compute
fingerprint stays well within 25 req/sec sustained; the projected ~125-345 SQD queries +
~30-95K Alchemy CU + <100 Dune credits over a multi-hour execution window translates to
a sub-1 req/sec sustained issuance rate across all surfaces combined.

**Conclusion.** The v1.2 architecture (SQD Network primary archive + Alchemy free spot RPC
under batched discipline + The Graph subgraphs + Dune ad-hoc SQL + public-RPC fallback
under consistency-degraded HALT) fits comfortably inside the FREE-TIER-ONLY budget pin
with substantial headroom for re-runs, sensitivity passes, and CORRECTIONS-block
iterations. The CORRECTIONS-δ re-derivation REPLACES (not supplements) v1.1's projection;
no paid services are required for the v0 → v3 ladder. BLOCK-B3 closure (SQD vs Subsquid
Cloud structural distinction) is preserved; only the Alchemy quota assumptions inside it
change.

**Budget-aware degradation path (revised under CORRECTIONS-δ).** If SQD Network throttles
or has a coverage gap:
Step 1: switch to The Graph hosted-service subgraph for the affected venue (FREE if
subgraph exists).
Step 2: switch to Alchemy free-tier `eth_getLogs` for the affected block range (free CU
inside the 30M cap; subject to 25 req/sec discipline).
Step 3: switch to Dune SQL against the relevant community table (free credits, watch the
~2500/mo working ceiling).
Step 4: switch to public RPC fallback (forno.celo.org / eth.llamarpc.com / rpc.ankr.com/eth)
under `Stage2PathBPublicRPCConsistencyDegraded` discipline — HALT-and-flag on any
cross-call inconsistency.
Step 5 (only if Steps 1-4 jointly insufficient): typed-exception HALT requesting user
re-budgeting for paid services (Subsquid Cloud, Alchemy paid tier, Dune Analyst, or
Eigenphi paid API). Auto-pivot through Steps 1-4 is permitted (all free-tier; tooling
fallback, not result-shaping); auto-pivot to Step 5 is anti-fishing-banned and requires
explicit user adjudication.

## §6 — HALT discipline

Path B inherits the Phase-A.0 HALT-disposition discipline from
`feedback_pathological_halt_anti_fishing_checkpoint`: every typed-exception HALT surfaces a
disposition memo to the orchestrator with ≥3 user-enumerated pivots; auto-pivot is
anti-fishing-banned; CORRECTIONS-block discipline applies on the chosen pivot.

Pre-pinned typed exceptions:

- **v0 — `Stage2PathBMentoUSDmCOPmPoolDoesNotExist`.** **REFRAMED in v1.4.** The original
  v1.0-v1.3 trigger condition (Mento V3 FPMM has no USDm/COPm pool) is now an EX-ANTE
  acknowledged truth recorded in the v1.4 frontmatter `on_chain_pins` block: the
  `mento_v3_fpmm_usdm_copm_pool_celo` placeholder is DEPRECATED in v1.4 because the pool
  does not exist in the Mento V3 deployment manifest. Under v1.4, this exception triggers
  if v0 confirms the v1.4 substrate set (Mento V3 USDm/cUSD FPMM pool at
  `0x462fe04b4FD719Cbd04C0310365D421D02AaA19E` per §3 v1.4 substrate clarification) is
  ALSO missing or has fewer than 100 swap events (pre-pinned floor). Pivots: (a) fall
  back to the secondary v1 substrate (Mento V2 BiPool USDm/COPm exchange via
  `mento_v2_bipool_manager_celo`) as the primary a_l-side substrate with explicit
  CORRECTIONS-block; (b) accept cUSD/cEUR or USDm/EURm as σ-pattern proxy with explicit
  CORRECTIONS-block recording the substrate-substitution rationale and an audit that the
  proxy substrate was not selected to produce a more favorable r_(a_l); (c) reframe Path
  B around USDm/EURm or USDm/GBPm pools that DO exist and document that the
  Pair-D-specific COP/USD anchor cannot be reproduced on-chain at the a_l side. The
  exception name is preserved here for predecessor-chain audit; under v1.4 the trigger
  is on the v1.4 primary substrate (Mento V3 USDm/cUSD), not the v1.0-v1.3 mis-named
  USDm/COPm placeholder.

- **v0 — `Stage2PathBAuditScopeAnomaly`.** Triggers if §4.0 row-count expectations
  fail (audit_summary <4 or >20 rows; address_inventory <5 rows). Pivots: (a) re-run with
  expanded allowlist (requires user-adjudicated FLAG-B7 exception); (b) document scope as
  unexpectedly narrow / broad and proceed with explicit notes; (c) split the audit into
  per-network sub-audits and re-evaluate row counts per network.

- **v0 — `Stage2PathBSqdNetworkCoverageInsufficient`.** Triggers if SQD Network gateway returns
  zero or fewer-than-100 events for a venue that on-chain explorers confirm has activity (i.e.,
  archive-side coverage gap). Pivots: (a) The Graph community subgraph for the affected venue;
  (b) Alchemy free-tier `eth_getLogs` for the affected block range under the §5.A burst-rate
  discipline (CU cost inside the 30M/mo cap, sequential issuance below 25 req/sec); (c) Dune
  SQL against the relevant community table within the working ~2500-credit ceiling.

- **v0 — `Stage2PathBSqdNetworkThrottled`.** Triggers if SQD Network gateway returns
  documented or undocumented rate-limit responses on a query that should be inside its free
  bounds (5 req/sec per IP per docs.sqd.ai 2025-02-23 notice). Pivots: (a) reduce query window
  and chunk size, increase inter-call sleep beyond the §5.A baseline 250 ms; (b) switch to The
  Graph hosted-service subgraph for the affected venue; (c) switch to Alchemy free-tier
  `eth_getLogs` (CU cost inside the 30M/mo cap, subject to 25 req/sec discipline); (d)
  escalation to paid Subsquid Cloud requires user re-budgeting per §5.A degradation Step 5
  (Step 5 in v1.2 numbering after public-RPC fallback was inserted as Step 4).

- **v0/v1/v2 — `Stage2PathBAlchemyFreeTierRateLimitExceeded` (NEW IN v1.2).** Triggers if
  Path B execution exceeds the Alchemy free-tier 25 req/sec sustained rate or the 500 CU/sec
  rolling-window cap, regardless of whether monthly CU headroom remains. Detected by the
  per-minute `req_per_sec` / `cu_per_sec` audit log mandated in §5.A burst-rate analysis
  sub-clause; warning at >80% of either cap, exception at exceedance. Pivots: (a) pause the
  in-flight batch ≥5 sec, reduce concurrency to 1, reduce batch size (e.g., 25 receipts → 10
  receipts per window), and retry; (b) shift the affected query class from Alchemy spot RPC
  to SQD Network bulk extraction where the field is available without receipt enrichment;
  (c) shift to The Graph hosted-service subgraph for typed-event surfaces; (d) shift to
  public-RPC fallback under `Stage2PathBPublicRPCConsistencyDegraded` discipline. If the
  exceedance recurs after Pivot (a), HALT-and-flag — escalation to a paid Alchemy tier
  requires user re-budgeting per §5.A Step 5 and is anti-fishing-banned as auto-pivot.

- **v0/v1/v2 — `Stage2PathBAlchemyFreeTierMonthlyCUExceeded` (NEW IN v1.2).** Triggers if
  cumulative Alchemy CU usage in a calendar month exceeds the 30M free-tier cap. Pre-pinned
  for safety; per §5.A projection (~30K-95K CU/mo aggregate), exceedance is low-risk under a
  single execution pass and would only realistically arise under repeated sensitivity re-runs
  or CORRECTIONS-block iterations within the same calendar month. Pivots: (a) pause Alchemy
  usage until the next calendar-month reset; (b) shift remaining query volume to SQD Network
  primary archive surface for the affected query class; (c) shift to The Graph hosted-service
  subgraph for typed-event surfaces; (d) shift to public-RPC fallback under
  `Stage2PathBPublicRPCConsistencyDegraded` discipline; (e) defer the affected work item
  until calendar-month rollover. Escalation to a paid Alchemy tier requires user
  re-budgeting per §5.A Step 5 and is anti-fishing-banned as auto-pivot.

- **v0/v1/v2 — `Stage2PathBPublicRPCConsistencyDegraded` (NEW IN v1.2).** Triggers when the
  public-RPC fallback path (forno.celo.org for Celo; eth.llamarpc.com / rpc.ankr.com/eth for
  Ethereum) returns inconsistent data across calls — e.g., `eth_blockNumber` reporting two
  different heights within seconds, `eth_getLogs` for a frozen block range returning a
  different log set on retry, receipt-vs-trace mismatches for the same `tx_hash`, or a
  schema_version drift on a Parquet artifact written from public-RPC-sourced input that
  cannot be reconciled to known new-block additions. Disposition is **HALT-and-flag, not
  silent merge** — public-RPC inconsistency MUST surface to the orchestrator before the
  affected artifact is committed. Pivots: (a) re-issue against a different public-RPC
  endpoint (forno.celo.org → public Cloudflare Celo RPC; eth.llamarpc.com → rpc.ankr.com/eth
  → publicnode.com) and require 2-of-3 agreement on the contested field before treating the
  result as authoritative; (b) wait ≥1 minute and re-issue against the same endpoint to
  rule out transient public-node desync; (c) substitute SQD Network bulk extraction for the
  affected block range if the data class is event-archival; (d) substitute Alchemy free-tier
  spot RPC subject to 25 req/sec discipline. Escalation to a paid RPC tier requires user
  re-budgeting per §5.A Step 5 and is anti-fishing-banned as auto-pivot.

- **v0/v1/v2/v3 — `Stage2PathBProvenanceMismatch`.** Triggers if §3.A re-execution discipline
  surfaces a sha256 / row-count / schema_version delta that cannot be reconciled to known
  new-block additions. Pivots: (a) investigate whether SQD Network re-indexed the
  affected block range (legitimate cause; document and proceed); (b) investigate whether a
  partition rule (FLAG-B8) was inadvertently changed; (c) full re-extraction with a fresh
  fetch_timestamp and side-by-side diff.

- **v1 — `Stage2PathBALCashFlowContaminated`.** Triggers if observed LP-fee accrual is materially
  mixed with non-σ-driven incentive emissions (Mento liquidity mining, Uniswap UNI emissions,
  third-party rewards) such that `r_(a_l)` cannot be cleanly attributed to σ-tracking turnover.
  Pivots: (a) net out incentive emissions by parsing reward distributions per LP and report
  `r_(a_l)` as a fee-only residual; (b) drop the contaminated pool and elevate the rank-2
  candidate from dispatch brief §4; (c) report `r_(a_l)` as a confidence interval rather than a
  point estimate and pass wider uncertainty into v3.

- **v2 — `Stage2PathBASOnChainSignalAbsent`.** **DEPRECATED in v1.4** — see the v1.3 → v1.4
  Change Log. The v1.0-v1.3 expected v2 HALT site (no on-chain a_s settlement-leg fingerprint)
  is RESOLVED by the SYNTHESIS.md §8.1 acknowledgment that no on-chain a_s entity exists in
  any LATAM corridor researched. v1.4 v2 is reframed as synthetic counterfactual generation
  per §3.B's pre-pinned q_t schedule families; the v1.0-v1.3 PROCEED-without-v2-`CF^(a_s)`
  and pivot enumeration are no longer load-bearing because v2 no longer attempts on-chain
  extraction. The exception name is preserved here for predecessor-chain audit but MUST NOT
  be raised by v1.4 executors; if raised, the orchestrator routes to the Change Log v1.3 →
  v1.4 explanation and the executor proceeds under the v1.4 v2 reframe.

- **v2 — `Stage2PathBSyntheticDriftBeyondTolerance` (NEW IN v1.4).** Triggers if cross-family
  spread of cumulative simulated Δ^(a_s) over the v2 sample window exceeds the §3.B-pinned
  ±20% tolerance:
  `(max_f|cum Δ^(a_s)(f, s_primary)| − min_f|cum Δ^(a_s)(f, s_primary)|) / mean_f(...) > 0.20`.
  Indicates the q_t schedule choice is dominating the synthetic Δ^(a_s) signal and the
  methodology is non-robust against the sweep over §3.B's pre-pinned family set
  {F1, F2, F3, F4}. Pre-pinned disposition: HALT-and-flag; orchestrator routes to user
  adjudication. Pivots:
  (a) tighten q_t family pre-commitment by selecting the family closest to the
      Stage-3-deployment-design choice (e.g., if F1 monthly-fixed best matches the planned
      vault disbursement schedule, restrict to F1 with explicit CORRECTIONS-block recording
      the family-selection rationale and an audit that no other family-choice would have
      been preferred under different methodology preferences);
  (b) document the cross-family spread in v3 sensitivity reporting as the load-bearing
      methodology caveat — v3 envelope is reported per (f, s) with the ±20% spread surfaced
      in the findings memo as a known synthetic-methodology-sensitivity result rather than
      as a HALT;
  (c) narrow the schedule sweep to the {F1, F3} cross only (drop F2 weekly cadence and
      F4 back-loading) under explicit CORRECTIONS-block discipline justifying the
      sub-family selection;
  (d) escalate to user adjudication for a re-pinning of the §3.B family set with the
      anti-fishing audit that the new family set is selected based on
      Stage-3-deployment-design considerations, not based on producing a more favorable
      cross-family spread on the existing data;
  (e) defer Path B convergence — emit v1 `r_al_handoff.json` only, defer v2 + v3, and
      flag the synthetic-methodology non-robustness for the Stage-3 design dispatch.
  Auto-pivot through (a)-(c) is anti-fishing-banned because each requires CORRECTIONS-block
  discipline; pivot (d) requires explicit user adjudication; pivot (e) is the cleanest
  HALT-and-park option for cases where the synthetic methodology cannot deliver a
  defensible Δ^(a_s) trace within the v1.4 design.

Each HALT requires a typed-exception memo, a disposition memo with ≥3 user-enumerated pivots,
and explicit user adjudication before any pivot is taken. The v1.0 `Stage2PathBDuneCoverageInsufficient`
and `Stage2PathBDuneCreditCapHit` typed exceptions from v1.0 §6 are RETIRED in v1.1 (Dune is
no longer the primary high-volume surface; SQD-Network-side exceptions above replace them);
Dune-credit exhaustion at the residual ad-hoc-SQL volume is handled inside the §5.A
degradation path without a typed exception. The v1.0-v1.3 `Stage2PathBASOnChainSignalAbsent`
exception is DEPRECATED in v1.4 per the entry above.

## §7 — Anti-fishing posture

Path B inherits the full Pair D Phase-3 anti-fishing posture and adds Path-B-specific invariants:

- **Pool selection follows the dispatch brief candidate ranking.** §4 + §5 of the dispatch
  brief rank candidate venues by Δ-fit × deployment-readiness; v0 audits them in that order. A
  post-data swap to a venue with nicer data is anti-fishing-banned. If rank-1 HALTs at v0,
  substitution is a typed-exception event with user adjudication, not a silent pivot.
- **Allowlist-only audit (FLAG-B7).** v0 operates on a fixed allowlist; auto-discovery is
  banned. If a candidate venue is missing from the allowlist, the executor surfaces a
  user-adjudicated typed exception rather than auto-expanding the audit surface.
- **σ-period matches Pair D's 2015-01-31 → 2026-02-28 window.** Restricting to a "cleaner"
  sub-period to improve qualitative shape match is anti-fishing-banned. If on-chain block-range
  cannot cover the full window (Mento V3 was deployed after 2015), the Path B sample is the
  maximum feasible overlap, and the gap is recorded explicitly. Window-trim forced by data is
  acceptable; window-curation chosen to improve a result is not.
- **`r_(a_l)` is computed via the FLAG-B1-pinned TWAP-weighted realized-fee-yield estimator,
  as-is from realized fee data.** No curve-fitting to frame the result. Estimated parameter is
  reported with HAC SE and propagated into v3 unchanged. Substituting an alternative estimator
  post-data (gas-deducted, position-weighted) requires CORRECTIONS-block discipline.
- **Time-binning (FLAG-B3) is daily-UTC primary; switching to a different cadence post-data
  to improve qualitative shape match is anti-fishing-banned.** Weekly aggregation as
  derivation is acceptable.
- **Reference price (FLAG-B4) follows the v1.4 pinned ladder (Mento V3 USDm/cUSD FPMM →
  Mento V2 BiPool USDm/COPm → Banrep TRM); the v1.0-v1.3 Uniswap V3 USDC/USDm Celo pool
  fallback is RETIRED in v1.4 per §3 v1.4 ladder revision. Swapping mid-analysis to
  whichever source produces nicer data is anti-fishing-banned.** Per-row `price_source`
  records the partition.
- **Non-economic transaction filter (FLAG-B8) is applied uniformly across the v1 sample;
  per-period adjustment of the partition rule to retain or exclude swaps is
  anti-fishing-banned.**
- **CF reconciliation cadence (FLAG-B5) is monthly, fixed at v1 entry; switching to per-week
  or quarterly post-data to improve agreement is anti-fishing-banned.**
- **v3 σ_T input (FLAG-B6) is realized monthly log-return-squared from Stage-1's COP/USD;
  substituting implied vol or a different realization window post-data is
  anti-fishing-banned.**
- **No causal-channel claims (RC FLAG #1 inheritance).** Path B language uses "FX-vol-driven
  services-share movement" and "a_l-side σ-tracking LP fee yield" (v1.4 substrate-set
  language; the v1.0-v1.3 Bitgifty-bill-pay channel claim is RETIRED with the v1.4 a_s-side
  reframe). It does not claim that Mento V3 / V2 swap flows reflect the BPO offshoring
  channel, nor that the synthetic Δ^(a_s) traces under §3.B's pre-pinned q_t schedule
  families identify the BPO mechanism. The CPO hedges the *correlation* established by
  Pair D Stage-1; it does not identify the *channel*.
- **No empirical β re-litigation.** Pair D Stage-1 PASS is the load-bearing input. Path B does
  not re-estimate β, re-run robustness, or propose a refined Y or X. Stage-1 sha pins are
  immutable through Path B.
- **No Stage-3 deployment claims.** Path B characterizes realized history; it does not
  recommend deployment, propose LP capital sourcing, scope onboarding, or describe regulatory
  framing. All deployment-adjacent reasoning is Stage-3 and out of scope.
- **RC FLAG #3 inheritance — lag-6 dominance honored in v3 backtest.** The v3 P&L envelope is
  computed under the Pair D-pinned 6-month-dominant lag pattern, not a uniform 6-12mo lag. If
  the backtest naturally surfaces a different best-fit lag-distribution, that is reported as an
  *observation* not as a re-specification of the empirical anchor.
- **RC FLAG #5 inheritance — verdict-sensitive to brief-vs-spec.** Path B treats the dispatch
  brief and this spec as the joint source of truth; if a v0-v3 finding contradicts one but not
  the other, the typed-exception HALT pathway is engaged before any disposition.
- **RC FLAG #6 inheritance — regime mix flagged.** The v3 envelope decomposition explicitly
  partitions realized P&L across the four regimes (post-2014 oil shock, COVID, Fed tightening,
  normalcy) and flags regime over-representation for downstream Stage-3 calibration cadence.
- **No post-data threshold tuning.** The 100-event v0 floor, the §4.0 row-count expectations,
  the SQD-Network-primary tooling architecture, and the v0-v3 SAA dispositions are pre-pinned
  at authoring time and do not move post-data. Free-tuning a threshold to avoid a HALT is
  exactly the failure mode `feedback_pathological_halt_anti_fishing_checkpoint` exists to
  prevent.
- **q_t schedule families (§3.B) are pre-committed in spec text BEFORE any v2 generation
  (v1.4 NEW).** The four families {F1 monthly fixed, F2 weekly fixed, F3 front-loaded
  two-payment, F4 back-loaded two-payment} are fixed at v1.4 authoring time per §3.B
  pre-commitment. Tightening, expanding, or re-parameterizing the family set post-data to
  chase either a more favorable Δ^(a_s) result or the §6
  `Stage2PathBSyntheticDriftBeyondTolerance` ±20% threshold is anti-fishing-banned. Adding
  additional families (e.g., geometric, quarterly-fixed, stochastic-amortization) requires
  a CORRECTIONS-block revision of §3.B with explicit anti-fishing audit recording why the
  new family set was selected ex-ante on Stage-3-deployment-design grounds, not ex-post on
  data-fitting grounds.
- **Synthetic-drift tolerance (§3.B / §6) ±20% is pre-committed in v1.4 (v1.4 NEW).** The
  cross-family spread tolerance is fixed at 20%; tightening to 10% to force a HALT on a
  clean synthetic, or loosening to 50% to absorb a sweep that revealed schedule-choice
  was the dominant signal, is anti-fishing-banned.
- **Path A v3 σ-distribution coupling is one-way A→B for synthetic generation; Path B does
  NOT alter the §3.B family set or the §3.B parameter spaces based on Path A's σ-paths
  (v1.4 NEW).** The Path-A-path-replay artifact `a_s_counterfactual_pathA_replay.parquet`
  is generated under the SAME §3.B-pinned q_t families {F1, F2, F3, F4}; substituting a
  different family set under Path A's paths to produce a more agreeable convergence is
  anti-fishing-banned.
- **No on-chain a_s entity rehabilitation (v1.4 NEW).** Per SYNTHESIS.md §8.1 + the
  v1.4 frontmatter `on_chain_pins_a_s_note`, no on-chain a_s entity exists in any LATAM
  corridor researched. Re-introducing a speculative a_s placeholder address (e.g., a newly
  surfaced consumer-rail operator's contract that appears to settle on-chain) requires
  three independent research-track confirmations equivalent to the SYNTHESIS.md §2
  4-track standard PLUS user adjudication; auto-pivot to "we found an on-chain a_s after
  all" is anti-fishing-banned because the v1.0-v1.3 Bitgifty / Walapay false-positive
  pattern is the failure mode this constraint exists to prevent.
- **No silent path-coupling with Path A beyond FLAG-B9 + v1.4 §8 promotion.** The
  permitted handoffs under v1.4 are: (B → A) `r_al_handoff.json`; (A → B) `v3_handoff.json`
  σ-path matrix consumed by v2 + v3 per §8 v1.4 NORMATIVE coupling. Any additional
  coupling (Path B v2 consuming Path A's K_l calibration; Path B v3 consuming Path A's
  position-geometry choices; etc.) requires explicit spec amendment.

## §8 — Convergence with Path A (v1.4 cross-path coupling revised)

Paths A and B were DEFAULT INDEPENDENT under v1.0-v1.3 (FLAG-B9). Under v1.4 (CORRECTIONS-ε),
the cross-path coupling expands: the Path A → Path B v3 σ-distribution handoff is promoted
from OPTIONAL to NORMATIVE because v2 synthetic counterfactual generation under §3.B's
pre-pinned q_t schedule families benefits materially from scenario-replay over Path A's MC
σ-paths. The other v1.0-v1.3 cross-path constraints PRESERVED: the single permitted Path B
→ Path A handoff remains the empirical `r_(a_l)` from v1; v1.4 v2 / v3 do not consume Path
A's parametric assumptions, position-geometry choices, or K_l calibration directly (only
Path A's σ-path distribution as enumerated below).

**Path B → Path A handoff (PRESERVED FROM v1.0-v1.3): `r_al_handoff.json`.** Schema
unchanged: `{r_al_point, r_al_hac_se, sample_n, sample_window, source_pool_address,
sha256_of_input_panel}`. Under v1.4 the `source_pool_address` field carries the v1.4
substrate set (Mento V3 USDm/cUSD FPMM as primary; Mento V2 BiPool USDm/COPm as
secondary); the field may be a list under v1.4 if both substrate r_(a_l)s are emitted to
Path A v3.

**Path A → Path B handoff (v1.4 NORMATIVE; promoted from OPTIONAL): `v3_handoff.json`.**
Schema:
`{sigma_paths: float64[N_paths × T_steps], path_source: "path_a_v3_gbm_mc",
path_count: int, sha256_of_path_a_v3_artifact: string}`.
Field semantics: `sigma_paths` is a `N_paths × T_steps` matrix of MC-simulated weekly
realized σ values per path; `path_source` is a string tag identifying the Path A v3
parametric model (default `"path_a_v3_gbm_mc"`; updated if Path A v3 evolves); `path_count`
matches the first dimension of `sigma_paths`; `sha256_of_path_a_v3_artifact` is the sha256
of the Path A v3 source notebook output for provenance discipline. Path B v2 consumes
this handoff to generate the optional `a_s_counterfactual_pathA_replay.parquet` artifact
per §4.0 Artifact 6, replaying Δ^(a_s) under each of Path A's MC σ-paths instead of (or
alongside) the historical observed COP/USD path. Path B v3 also consumes this handoff for
the Path-A-path-replay envelope per §2 v3 hybrid backtest revision.

The §8 cross-path naming-asymmetry NIT (Path A §12 "σ-distribution" vs Path B
FLAG-B9 "r_(a_l) point + HAC SE") is carried forward to the convergence-dispatch work
item per the v1.3 deferral; v1.4 adds "Path A v3 σ-distribution becomes NORMATIVE input
to Path B v2 synthetic counterfactual" to the convergence-dispatch backlog.

Path A produces a stochastic / Monte-Carlo P&L distribution under the same CPO mechanics
that Path B characterizes (empirically on the a_l side; synthetically on the a_s side). The
convergence point is at v3: Path B's hybrid realized-+-synthetic P&L envelope per (f, s)
combination should fall *inside* Path A's Monte-Carlo bounds if the framework's analytical
assumptions hold in realized history AND the §3.B-pinned synthetic methodology produces
defensible Δ^(a_s) traces. Disagreement is informative — it indicates either a Path-A
modeling assumption that does not match realized behavior, a Path-B data-construction
artifact on the a_l side that distorts the realized envelope, or a §3.B q_t-schedule
choice that produces a Δ^(a_s) trace the Path A model does not anticipate.

The convergence dispatch is a separate work item, not within Path B's scope. Path B v3
closes when the hybrid envelope per (f, s) is characterized and the calibration-handoff
packet is produced (v1.4: `r_al_handoff.json` + per-(f, s) v3 envelope JSON +
optional Path-A-path-replay envelope JSON). The orchestrator dispatches the convergence
comparison after both Path A v3 and Path B v3 deliver their respective handoff packets.

If Path B v2 fires `Stage2PathBSyntheticDriftBeyondTolerance` per §6, the v3 envelope
characterization is contingent on the chosen pivot disposition. Per pivot (e) — defer
Path B convergence — v3 reports the a_l-side empirical envelope only and the convergence
dispatch checks Path A's a_l-side bounds against Path B's realized a_l-side envelope.
Synthetic-Δ^(a_s)-side convergence remains an open question for downstream Stage-3 work
when (e) is the chosen pivot. The v1.0-v1.3 `Stage2PathBASOnChainSignalAbsent`
PROCEED-without-v2 disposition is DEPRECATED per §6 v1.4 entry and does not appear here.

## §9 — Self-review checklist

- **≥4 of 5 building blocks:** Background Information (Stage-1 sha pins + dispatch brief
  lineage + v0 schema + provenance discipline); Context Information (Pair D PASS verdict +
  framework imports + on-chain pin scaffolding + budget-aware degradation path); Tonal Control
  (reliability-obsessed Data Engineer voice; precise quantification; no marketing copy); Tool
  Use Instructions (free-tier-only tooling stack + SQD-Network-primary architecture + Alchemy
  free-tier batched discipline + Dune ceiling + public-RPC fallback + degradation ladder).
  User Preferences emerges through the inherited RC FLAG handling and HALT discipline.
  Coverage: 4 of 5 explicit + 1 implicit-through-inheritance.
- **≥6 of 7 complexity principles:** Define Personality and Tone; Guide Tool Use and Response
  Formatting (SQD / Alchemy free / Dune free / Subgraph free / public-RPC fallback / paid-only
  escalation ladder with pre-pinned ceilings); Implement Dynamic Behavior Scaling (v0-v3
  ladder with per-version exit criteria; v1.4 v2 reframed to local-compute synthetic
  generation under §3.B-pinned q_t families); Inject Critical Non-Negotiable Facts (Stage-1
  sha pin chain, on-chain address pins for a_l-side substrate set under v1.4, FREE-TIER-ONLY
  budget pin per CORRECTIONS-δ, SQD Network FREE classification, Alchemy free-tier 30M CU/mo
  + 25 req/sec caps, v1.4 SYNTHESIS.md §8.1 acknowledgment that no on-chain a_s entity
  exists, v1.4 LVR acknowledgment per Milionis-Moallemi-Roughgarden 2022); Instruct Critical
  Evaluation (no causal claims, no β re-litigation, no curve-fitting, no post-data threshold
  tuning, no silent path-coupling, no auto-pivot to paid services, v1.4 no on-chain a_s
  entity rehabilitation, v1.4 no §3.B q_t family set tuning); Provide Context Information
  (full inheritance from dispatch brief + MEMO §7 + VERDICT.md + v1.4 SYNTHESIS.md memo
  per `synthesis_memo_pin` frontmatter); Set Clear Guardrails (typed-exception HALT pathway
  with ≥3 pre-pinned pivots per HALT including 3 new free-tier-failure-mode exceptions in
  v1.2 + 1 new synthetic-drift exception in v1.4, anti-fishing posture with v1.4
  q_t-pre-commitment + drift-tolerance pre-commitment + on-chain-a_s-rehabilitation ban,
  Stage-3 out-of-scope, CORRECTIONS-γ + CORRECTIONS-ε scoping reminders). Coverage: 7 of 7.
- **No XML tags.** Section headers and bullet points only.
- **No code.** Code-agnostic per `feedback_no_code_in_specs_or_plans`. Schema definitions,
  address pins, mathematical formulas, configuration parameters, and dependency lists are
  permitted; actual Python/SQL/JavaScript implementation is not.
- **Quality metrics 1-8.** Completeness (4+ building blocks, 6+ principles, 3 BLOCKs +
  9 FLAGs resolved with v1.4 substrate-set additions to FLAG-B2 / FLAG-B4); clarity (each
  section is unambiguous and actionable; new schema + provenance + §3.B q_t pre-commitment
  sections are tabular and testable); consistency (no conflicting directives — Stage-3
  out-of-scope is repeated wherever it could be ambiguous; CORRECTIONS-γ is preserved
  per v1.3 prose-rename closure; CORRECTIONS-ε reframes v2 substantively but preserves
  all v1.0-v1.3 BLOCK / FLAG closures with substrate updates only); purposefulness (every
  section serves the v0-v3 ladder, the budget-pin reconciliation, the v1.4 a_s-side
  reframe, or inherited anti-fishing); naturalness (Data Engineer voice is consistent and
  Phase-A.0 discipline integrates organically); comprehensiveness (dense, no filler);
  safety (HALT pathway is the load-bearing safety mechanism with the v1.4 synthetic-drift
  exception added; provenance discipline is the audit-incompatibility safeguard with the
  v1.4 q_t pre-commitment field added; budget-aware degradation is the cost-discipline
  safeguard; v1.4 LVR + on-chain-a_s-rehabilitation guards are the methodology safeguards);
  user experience (clear ladder with pre-pinned exits and pre-pinned pivots; explicit
  free-vs-paid cost classifications; v1.4 q_t schedule families are explicit and
  bounded).

End of spec body. Frontmatter `verifier_v1_wave1` and `verifier_v1_wave2` fields are pending
re-run of the 2-wave doc-write verification on v1.4 per
`feedback_two_wave_doc_verification`. v1.4 scope is substantive (a_s-side reframe per
SYNTHESIS.md §8 OPTION 3; on_chain_pins overhaul; new §3.B q_t pre-commitment; new §4.0
artifacts; new §6 typed exception; §8 cross-path coupling promoted) and the 2-wave
verification is expected to focus on (i) the SYNTHESIS.md memo grounding and the
on_chain_pins overhaul rationale, (ii) the §3.B q_t schedule family pre-commitment and the
±20% drift tolerance pre-commitment, (iii) the new §4.0 a_s_counterfactual.parquet schema
and provenance discipline integration, (iv) the §6 Stage2PathBSyntheticDriftBeyondTolerance
exception and 5-pivot enumeration, (v) the §8 v3_handoff.json schema and the
B-consumes-A-σ-paths coupling acceptability, and (vi) preservation of all v1.0-v1.3 BLOCK /
FLAG closures with substrate updates. v1.1 had passed Wave-2 re-verify with NITs only; v1.2
scope is narrow (free-tier-only budget pin re-derivation; three new typed exceptions; no
v1.1 BLOCK or FLAG closure regressed) and the re-verify is expected to focus on the
free-tier-feasibility risk assessment in the Change Log v1.1 → v1.2 section, the §5.A
burst-rate analysis sub-clause, and the three new §6 typed exceptions.
