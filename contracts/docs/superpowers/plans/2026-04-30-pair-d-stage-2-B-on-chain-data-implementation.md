---
plan_path: contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md
plan_version: v1.1 (CORRECTIONS-α — Phase 2/3/4 task substance updated to track spec v1.3 → v1.4 CORRECTIONS-ε synthetic-counterfactual reframe; Phase 0 / Phase 1 closures preserved)
plan_predecessor_version: v1.0
plan_predecessor_chain:
  v1_0: 406c55a33e28af9e57b4cb912017e3bea26993733dc5260c0486e507d7f9cd38
plan_author:
  - Data Engineer dispatch 2026-05-02 (v1.0; under user-explicit auto-mode authorization per `feedback_proceed_without_asking_auto_mode`)
  - Data Engineer dispatch 2026-05-03 (v1.1; CORRECTIONS-α; Phase 2/3/4 task substance reframe per spec v1.4 CORRECTIONS-ε; Phase 0/1 task substance preserved)
plan_sha256_v1_0: 406c55a33e28af9e57b4cb912017e3bea26993733dc5260c0486e507d7f9cd38
plan_sha256_v1_1: <to-be-pinned-after-2-wave-verify>
spec_sha256_pin: fcebc95f923e1b55fbf2eaa22239b00bbde4a9f35bb031e8f32d090a4fb80d95
spec_version_pin: v1.4 (CORRECTIONS-ε executed; synthetic-counterfactual reframe normative; on_chain_pins overhaul; §3.B q_t schedule families pre-committed; A→B v3 σ-distribution coupling promoted from OPTIONAL to NORMATIVE)
spec_predecessor_chain:
  v1_3: 4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea
spec_path: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md
companion_spec_path_path_a: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-A-fork-simulate-spec.md
companion_spec_sha_path_a: 1a4cc6a4 (v1.2.1; cross-path coupling awareness ONLY — Path A plan v1.0 untouched by this revision)
master_dispatch_brief: contracts/.scratch/2026-04-30-stage-2-m-sketch-dispatch-brief-pair-d.md
synthesis_memo_pin:
  path: contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/SYNTHESIS.md
  commit_sha: e25131cd2
  load_bearing_finding: "Abrigo is an a_s-INSTANTIATING product, not an a_s-hedging product. The CPO cannot be sold into an existing on-chain a_s population because that population doesn't exist on-chain. Product must DEPLOY the a_s side simultaneously."
internal_ladder: v0 (data-coverage audit + Mento swap-flow inventory) → v1 (empirical CF^a_l reconstruction; on-chain) → v2 (synthetic CF^a_s counterfactual generation; local Python compute under §3.B-pinned q_t families) → v3 (hybrid realized-+-synthetic CPO retrospective backtest)
deliverable_framing: structural-exposure characterization (per spec v1.3 CORRECTIONS-γ §1 framing-definition, PRESERVED through v1.4; behavioral demand / WTP is explicitly OUT OF SCOPE — Stage-3 question; v1.4 reaffirms — synthetic Δ^(a_s) under pre-pinned q_t schedules is structural-exposure characterization of a hypothetical-but-pre-committed cash-flow geometry, NOT a WTP estimate)
budget_pin: free_tier_only
budget_pin_provenance: spec v1.3/v1.4 frontmatter (inherited from CORRECTIONS-δ user directive 2026-05-02; PRESERVED verbatim under CORRECTIONS-ε; v1.4 v2 footprint shrinks to ZERO RPC calls because synthetic generation is local Python compute)
plan_verifier_v1_wave1: passed-on-v1_0 (Reality Checker against v1.0; v1.1 re-dispatches RC against CORRECTIONS-α scope per `feedback_two_wave_doc_verification`)
plan_verifier_v1_wave2: passed-on-v1_0 (Workflow Architect against v1.0; v1.1 re-dispatches WA against CORRECTIONS-α scope per `feedback_two_wave_doc_verification`)
plan_verifier_v1_1_wave1: pending (Reality Checker; charges: synthetic-counterfactual framing fidelity per spec v1.4 §1; q_t schedule pre-commitment honored verbatim from spec §3.B; A→B v3_handoff.json consume-when-available semantics correct; no on-chain a_s entity rehabilitation; free-tier-only PRESERVED; structural-exposure framing exclusively preserved)
plan_verifier_v1_1_wave2: pending (Workflow Architect; charges: Phase 2/3/4 task ordering reflects v1.4 reframe; Phase 1 v0 mento_swap_flow_inventory artifact wired into Phase 3 inputs; Phase 4 consume-when-available coupling correct; specialist coverage maintained; per-phase 3-way review hooks PRESERVED; trio-checkpoint discipline preserved on notebooks 02/03/04)
revision_history:
  - v1.0 2026-05-02 initial draft per Data Engineer dispatch grounded in spec v1.3 (sha 4e8905a9...)
    + dispatch brief + Stage-1 plan structural pattern
  - v1.1 2026-05-03 CORRECTIONS-α — Phase 2/3/4 task substance updated to track spec v1.4 CORRECTIONS-ε synthetic-counterfactual reframe (PR #84 spec merge; sha fcebc95f...);
    Phase 1 picks up new v0 deliverable mento_swap_flow_inventory.parquet per spec §4.0 Artifact 4;
    Phase 1 plan-Task 1.1 allowlist disposition memo references CORRECTIONS-ε resolution path;
    Phase 0 closures and free-tier discipline PRESERVED with no regression;
    Phase 4 v3_handoff.json consumption from Path A v3 added with consume-when-available semantics
stage1_pinned_chain:
  pair_d_spec_v1_3_1: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
  panel: 6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf
  primary_ols: d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf
  robustness_pack: 67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904
  verdict: 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf
on_chain_pins_inherited_v1_4:
  # ── a_l side substrates (NORMATIVE per spec v1.4 §3) ─
  mento_v3_router_celo: "0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6"
  mento_v2_bipool_manager_celo: "0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901"
  mento_v2_copm_celo: "0x8A567e2aE79CA692Bd748aB832081C45de4041eA"
  mento_v2_usdm_celo: "0x765DE816845861e75A25fCA122bb6898B8B1282a"
  mento_broker_celo: "0x777A8255cA72412f0d706dc03C9D1987306B4CaD"
  mento_v3_fpmm_usdm_cusd_pool_celo: "0x462fe04b4FD719Cbd04C0310365D421D02AaA19E"
  panoptic_factory_ethereum: "<resolved at v0 audit closure>"
  # ── Architectural template (NOT a substrate; methodology reference for §3.B q_t design only) ─
  impact_market_microcredit_celo: "0xEa4D67c757a6f50974E7fd7B5b1cc7e7910b80Bb"
on_chain_pins_deprecated_v1_4_do_not_consume:
  # ── DEPRECATED in spec v1.4; preserved here for predecessor-chain audit ONLY; v1.1 plan executors MUST NOT consume these ─
  bitgifty_settlement_celo: "DEPRECATED_v1_4 (no smart contracts deployed; consumer-rail-operator archetype confirmed off-chain across 4 research tracks per SYNTHESIS.md §3.1)"
  walapay_settlement_celo: "DEPRECATED_v1_4 (closed source; Dfns MPC custody; no Celo deployment; no Mento integration per SYNTHESIS.md §3.1)"
  mento_v3_fpmm_usdm_copm_pool_celo: "DEPRECATED_v1_4 (pool does not exist in Mento V3 deployment manifest; canonical USDm/COPm direct exchange is the V2 BiPool path)"
  uniswap_v3_usdc_usdm_pool_celo: "DEPRECATED_v1_4 (mis-named placeholder; canonical USD/USDm liquidity is Mento V3 FPMM USDm/cUSD pool)"
  uniswap_v3_factory_celo: "DEPRECATED_v1_4 (Uniswap V3 USD/USDm Celo pool reference retired; v1.4 a_l substrate is Mento-native only)"
on_chain_pins_a_s_note: "Per spec v1.4 §3 + SYNTHESIS.md §8.1, no on-chain a_s entity exists in any LATAM corridor researched. The a_s side is generated SYNTHETICALLY in Phase 3 (v2) per spec §3.B's pre-pinned q_t schedule families {F1, F2, F3, F4} and the §4.0 Artifact 5 a_s_counterfactual.parquet schema. The plan deliberately does NOT pin any on-chain a_s entity addresses; doing so would re-introduce the v1.0-v1.3 false-positive pattern (Bitgifty / Walapay placeholder pre-pinning produced 2/2 false-positive rate per SYNTHESIS.md §3.1 anti-fishing log entry)."
push_target: dev (per `feedback_push_origin_not_upstream` — origin = JMSBPP; NEVER upstream/wvs-finance)
---

# Pair D Stage-2 — Path B (On-Chain Data) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Per project convention `feedback_no_code_in_specs_or_plans`, this plan is code-agnostic; implementation specifics are deferred to executor sub-agents per task. Per `feedback_specialized_agents_per_task`, each task names the specialist owner. Per `feedback_strict_tdd`, no implementation lands without a failing test first. Per `feedback_real_data_over_mocks`, tests use real on-chain data; mocks are reserved for HTTP errors that cannot be reproduced.

## Change Log v1.0 → v1.1 (CORRECTIONS-α)

**Tag:** CORRECTIONS-α (plan-side companion to spec v1.3 → v1.4 CORRECTIONS-ε).

**Trigger:** Spec revision v1.3 (sha `4e8905a9...`) → v1.4 (sha `fcebc95f...`) merged at PR #84 on 2026-05-03 executes the synthetic-counterfactual reframe driven by `contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/SYNTHESIS.md` (commit `e25131cd2`). The load-bearing finding (per SYNTHESIS.md §8.1, user decision 2026-05-03): no on-chain a_s entity exists in any LATAM corridor researched; the consumer-rail-operator archetype is structurally off-chain (Bitgifty Tatum API custody, Walapay Dfns MPC, Pretium / Kotani Pay / Fonbnk / Yellow Card all confirmed off-chain across 4 independent research tracks); tokenized-fiat-issuers (MXNB / Juno, BRL1, wARS / Ripio) hold one-sided local-currency reserves with no FX exposure on the issuer's books; the AMM-LP-level a_s relocation was REJECTED because LP NET is structurally short-variance per LVR (Milionis-Moallemi-Roughgarden 2022). Abrigo is therefore an a_s-INSTANTIATING product, not an a_s-hedging product; the CPO cannot be sold into an existing on-chain a_s population because that population does not exist on-chain. The user-picked refinement (SYNTHESIS.md §8.2, OPTION 3) is synthetic counterfactual generation in v2 under pre-pinned q_t schedule families.

**Scope of CORRECTIONS-α (plan-side).** Phase 2 (v1 CF^a_l), Phase 3 (v2 CF^a_s), and Phase 4 (v3 CPO backtest) task substance is updated to reflect the v1.4 reframe. Phase 0 (environment scaffolding) and Phase 1 (v0 audit) closures are PRESERVED with a single Phase 1 additive task — emit `mento_swap_flow_inventory.parquet` per spec §4.0 Artifact 4 — required by Phase 3's synthetic generator as the bound-check input. Phase 1 plan-Task 1.1 (allowlist confirmation, already committed at `2483f08d3`) and Phase 1 TDD scaffold (committed at `6d9c8dfc6`) are NOT re-litigated; the plan-Task 1.1 disposition memo's allowlist placeholders that surfaced `Stage2PathBASOnChainSignalAbsent` are now resolved by spec v1.4's `on_chain_pins_a_s_note` (no on-chain a_s entity to pin) and the synthetic-counterfactual reframe.

**Per-section deltas.**

- **Frontmatter.** `plan_version` v1.0 → v1.1 with CORRECTIONS-α tag. `plan_predecessor_chain` extended with `v1_0: 406c55a3...`. `plan_predecessor_version` set to v1.0. `spec_sha256_pin` updated v1.3 sha → v1.4 sha (`fcebc95f...`). `spec_version_pin` v1.3 → v1.4. `spec_predecessor_chain.v1_3` records the v1.3 sha for audit. `plan_author` extended with the v1.1 Data Engineer entry. `plan_sha256_v1_0` pinned with the v1.0 sha. `plan_sha256_v1_1` placeholder per `<to-be-pinned-after-2-wave-verify>` convention. New `synthesis_memo_pin` block records the SYNTHESIS.md path + commit + verbatim load-bearing finding. `internal_ladder` updated to reflect v0 expansion (adds Mento swap-flow inventory) + v2 reframe (synthetic counterfactual generation, local Python compute) + v3 reframe (hybrid realized-+-synthetic). `deliverable_framing` PRESERVED with v1.4 reaffirmation that synthetic Δ^(a_s) under pre-pinned q_t schedules is structural-exposure characterization, NOT WTP. `on_chain_pins_inherited` field renamed to `on_chain_pins_inherited_v1_4` and overhauled per spec v1.4 §3 substrate set. New `on_chain_pins_deprecated_v1_4_do_not_consume` block preserves the v1.0-v1.3 placeholders for predecessor-chain audit with `DEPRECATED_v1_4` markers and explicit `MUST NOT consume` instruction. New `on_chain_pins_a_s_note` field declares the no-on-chain-a_s-entity finding with the false-positive-pattern anti-fishing reasoning.

- **§1 Overview.** Reframed from "v0 → v1 → v2 → v3 with v2 = on-chain Bitgifty / Walapay merchant-side Transfer extraction" to "v0 → v1 → v2 → v3 with v2 = synthetic counterfactual generation under spec §3.B-pinned q_t schedule families." v1 stays empirical / on-chain (a_l side substrate set updated to Mento V3 USDm/cUSD primary + Mento V2 BiPool USDm/COPm secondary). v3 becomes hybrid (realized Δ^(a_l) + synthetic Δ^(a_s) per family). The Abrigo-is-an-a_s-instantiating-product framing acknowledged. Free-tier discipline PRESERVED (v2 reframe shrinks the network footprint to ZERO RPC calls).

- **§2 Phase decomposition.** Phase 1 v0 picks up `mento_swap_flow_inventory.parquet` as a fourth artifact per spec §4.0 Artifact 4 (the v2 bound-check input). Phase 2 v1 substrate references updated to Mento V3 USDm/cUSD FPMM `0x462fe04b...` PRIMARY + Mento V2 BiPool USDm/COPm via BiPool manager `0x22d9db95...` SECONDARY; LP fee yield estimator unchanged in shape (FLAG-B1 PRESERVED). Phase 3 v2 reframed end-to-end from "extract on-chain settlement-leg Transfers" to "synthetically generate Δ^(a_s) under §3.B-pinned q_t families {F1 monthly, F2 weekly, F3 front-loaded, F4 back-loaded} sweeping over (f, s) tuples"; Phase 3 emits `a_s_counterfactual.parquet` per spec §4.0 Artifact 5. Phase 4 v3 reframed from "replay Π(σ_T) against empirical Δ^(a_s) + Δ^(a_l)" to "replay Π(σ_T) against synthetic Δ^(a_s) per family + empirical Δ^(a_l), with Path A v3 σ-distribution as NORMATIVE input where available."

- **§3 Tasks per phase.** Phase 0 tasks PRESERVED. Phase 1 tasks PRESERVED with one ADDITIVE sub-task (Task 1.3.b) emitting `mento_swap_flow_inventory.parquet`; the allowlist disposition memo at `task_1_1_plan_disposition.md` (committed at `2483f08d3`) is referenced and the CORRECTIONS-ε resolution path (no on-chain a_s entity to pin; synthetic generation pivot) is recorded. Phase 2 task substance updated for substrate-set clarity per spec v1.4 §3 + reference-price ladder revision per spec §7 (Mento V3 USDm/cUSD FPMM → Mento V2 BiPool USDm/COPm → Banrep TRM; Uniswap V3 USDC/USDm fallback RETIRED). LVR sensitivity decomposition `v1_lvr_decomposition.parquet` added as OPTIONAL Phase 2 deliverable per spec §4 v1 output bullet. Phase 3 fully rewritten: drop sub-tasks for Bitgifty / Walapay extraction (Tasks 3.1, 3.2, 3.3, 3.4, 3.5 from v1.0); add synthetic generation tasks (3.A through 3.D in v1.1) emitting `a_s_counterfactual.parquet` per spec §4.0 Artifact 5 with cross-family ±20% drift check per `Stage2PathBSyntheticDriftBeyondTolerance`; conditional optional Path A v3 σ-distribution replay artifact `a_s_counterfactual_pathA_replay.parquet` per spec §4.0 Artifact 6. Phase 4 task substance updated: Π(σ_T) replay against synthetic Δ^(a_s) (per family) + empirical Δ^(a_l); K_l = K_s simulated equilibrium check per (q_t family, σ-source) cross product; new sub-task to consume Path A's `v3_handoff.json` IF AVAILABLE at v3 entry (consume-when-available semantics; non-blocking if Path A v3 has not shipped); optional `a_s_counterfactual_pathA_replay.parquet` companion deliverable per spec §4.0 Artifact 6.

- **§4 Dependency graph.** Phase 1 → Phase 2 unchanged. Phase 2 → Phase 3 unchanged in topology but Phase 3 now consumes both v1 outputs AND v0's `mento_swap_flow_inventory.parquet` (cross-phase dependency added). Phase 3 → Phase 4 unchanged in topology. New optional cross-path consume edge: Path A `v3_handoff.json` → Phase 4 (consume-when-available; Phase 4 proceeds with historical-path-only backtest if not present per spec §8 semantics).

- **§5 Provenance discipline.** PRESERVED — `DATA_PROVENANCE.md` mirror per spec §3.A. EXTENSION: synthetic-generation tasks (Phase 3) require `q_t_schedule_family_pinned` field per spec v1.4 §3.A template extension (descriptive string identifying the §3.B family + parameter spec hash); the field is required when the artifact's `schema_version` corresponds to the v2 synthetic schema.

- **§6 Free-tier discipline.** PRESERVED — auto-pivot to paid services anti-fishing-banned per spec §6 + §5.A degradation Step 5. Phase 3 v2 budget projection downward: v1.0's "~50-75 SQD chunked queries per router × 2-3 routers; <30K Alchemy CU" is RETIRED; v1.4 v2 is local Python compute over v0 + Stage-1 panel inputs — ZERO RPC calls, ZERO additional Alchemy CU, ZERO additional Dune credits. Phase 1 v0 picks up the new `mento_swap_flow_inventory.parquet` artifact: aggregate Mento substrate swap-event volume per week × 3 substrates × 4 partitions ≈ 1620 rows; modest upward adjustment to v0 SQD query projection (the substrate-event extraction is already in scope for `event_inventory`; the inventory aggregation is a local DuckDB rollup of the same extracted events) — net incremental SQD load ≤ 25 additional queries; net incremental Alchemy CU ≤ 5K; well inside free-tier headroom.

- **§7 Cross-path coordination.** PRESERVED in spirit — defaults INDEPENDENT per spec §8 v1.0-v1.3 baseline. UPDATE: A → B v3 envelope coupling REFRAMED FROM OPTIONAL TO NORMATIVE per spec v1.4 §8. A new Phase 4 sub-task consumes Path A's `v3_handoff.json` IF AVAILABLE at Phase 4 entry per spec §8 v1.4 schema `{sigma_paths, path_source, path_count, sha256_of_path_a_v3_artifact}`; consume-when-available semantics — non-blocking if Path A v3 has not shipped at Phase 4 entry, in which case the historical-path-only hybrid backtest is the deliverable and Path-A-path-replay is deferred. B → A `r_al_handoff.json` coupling unchanged in topology; the `source_pool_address` field may be a list under v1.4 if both substrate r_(a_l)s are emitted to Path A v3.

- **§8 Self-review checklist.** Updated to reflect v1.4 spec inputs (synthesis-memo grounding; §3.B q_t pre-commitment; §4.0 Artifact 4 + 5 + 6 schemas; §6 `Stage2PathBSyntheticDriftBeyondTolerance`; §8 promoted A → B coupling; PRESERVED v1.0-v1.3 BLOCK / FLAG closures).

- **§9 Plan validation gates.** 2-wave plan re-verify (RC + WA) is the gate for the v1.1 plan write itself per `feedback_two_wave_doc_verification`. Per-phase 3-way implementation review (CR + RC + SD per `feedback_implementation_review_agents`) PRESERVED unchanged. Convergence gate at Phase 5 PRESERVED.

**No-regression assertion.** All v1.0 plan disciplines PRESERVED:
- Per-phase 3-way implementation review (CR + RC + SD; not Tech Writer) at every phase close.
- Trio-checkpoint discipline on notebook authoring (Phases 2, 3, 4) per `feedback_notebook_trio_checkpoint`.
- 4-part citation block discipline on every test / decision / spec choice in estimation or sensitivity notebooks per `feedback_notebook_citation_block`.
- Per-artifact `DATA_PROVENANCE.md` mirror discipline per spec §3.A (extended with `q_t_schedule_family_pinned` for v2 synthetic artifacts).
- Free-tier-only budget pin per spec §5 / §5.A; auto-pivot to paid services anti-fishing-banned.
- HALT-disposition discipline per `feedback_pathological_halt_anti_fishing_checkpoint` for every typed exception.
- Strict TDD per `feedback_strict_tdd` — failing tests first; Phase 1 TDD scaffold at `6d9c8dfc6` is the load-bearing reference; Phases 2-4 inherit trio-checkpoint structure as TDD analog.
- Real data over mocks per `feedback_real_data_over_mocks`; mocks reserved for HTTP errors that cannot be reproduced.
- Specialist coverage per `feedback_specialized_agents_per_task` — every task names a specialist owner.
- Code-agnosticism per `feedback_no_code_in_specs_or_plans`.
- Push to `dev` (origin = JMSBPP) per `feedback_push_origin_not_upstream`; NEVER upstream/wvs-finance.
- Stage-1 sha-pin chain READ-ONLY through Path B; no β re-litigation.
- No causal-channel claims for the BPO mechanism (RC FLAG #1 inheritance).
- No Stage-3 deployment claims; structural-exposure framing exclusively per CORRECTIONS-γ.
- 2-wave doc verification per `feedback_two_wave_doc_verification` for plan / spec / CLAUDE.md writes.

**Why CORRECTIONS-α is not threshold tuning.** CORRECTIONS-α is a downstream propagation of the spec-side CORRECTIONS-ε structural pivot: spec §3.B q_t schedule families are pre-committed BEFORE any v2 generation; the cross-family ±20% drift tolerance is pre-pinned in spec §6's `Stage2PathBSyntheticDriftBeyondTolerance`; the plan reflects these pre-commitments verbatim and adds no per-task tuning knobs. The Phase 3 reframe drops a non-existent on-chain extraction substrate (4-track research confirmed Bitgifty / Walapay / consumer-rail-operator archetype off-chain) and replaces it with a methodology that produces simulation, not measurement, under explicit anti-fishing constraints. The Phase 4 NORMATIVE A → B coupling is consume-when-available per spec §8 — Path B v3 does not block on Path A v3 delivery, and the historical-path-only fallback is the spec-pinned default. Auto-fitting q_t schedule families to chase a more favorable Δ^(a_s) is anti-fishing-banned per spec §7; auto-pivoting to a paid service to widen the synthetic search space is anti-fishing-banned per spec §5.A Step 5; both bans are recorded in the plan §6 / §8 sections preserved-and-extended below.

## §1 — Overview

Path B is the on-chain empirical-validation track for the Pair D Convex Payoff Option (CPO) Stage-2 M-sketch. The Stage-1 Pair D simple-β empirical validation closed PASS 2026-04-28 PM late evening (β_composite = +0.1367, p_one = 1.46×10⁻⁸, robustness 0/4 sign-flips); per the framework's stage-discipline clause the M-sketch step is unblocked. Per spec v1.4 (CORRECTIONS-ε), Path B's job is now twofold: (i) confirm — from realized on-chain history alone, with no simulation and no parameter free-fitting — that the **a_l (long-σ) leg** of the CPO exhibits the cash-flow shape the imported convex-payoff framework predicts for it on the Mento V3 USDm/cUSD FPMM pool primary substrate; and (ii) generate a **synthetic counterfactual** for the **a_s (short-σ) leg** under spec §3.B's pre-pinned q_t schedule families {F1 monthly, F2 weekly, F3 front-loaded, F4 back-loaded}, because the SYNTHESIS.md §8.1 finding (4 independent research tracks; user decision 2026-05-03) confirms no on-chain a_s entity exists in any LATAM corridor researched. Abrigo is therefore an a_s-INSTANTIATING product, not an a_s-hedging product: the CPO cannot be sold into an existing on-chain a_s population because that population does not exist on-chain; the product must DEPLOY the a_s side simultaneously at Stage-3. The Stage-1 sha-pin chain (spec v1.3.1, joint panel, primary OLS, robustness pack, VERDICT.md — all pinned in this plan's frontmatter) is READ-ONLY through Path B; any plan task that would invalidate them is OUT OF SCOPE.

Path B's deliverable IS **structural-exposure characterization** (per spec v1.3 CORRECTIONS-γ §1 framing-definition, PRESERVED through v1.4) — the cash-flow geometry yielding `|Δ^(a_l)|` (empirical, on-chain) and `|Δ^(a_s)|` (synthetic, under pre-pinned q_t schedules) magnitudes in $-notional that the CPO would neutralize on observed transaction flows. Behavioral demand / willingness-to-pay is **explicitly out of Path B's Stage-2 scope**: transaction archaeology cannot infer WTP for an instrument that does not yet exist in the market, because the existing transactions describe equilibrium under an option set in which the CPO is absent, and introducing the CPO would change that option set. WTP is a Stage-3 (deployment) question requiring a different evidence base (deployed pilot, surveyed demand, observed take-up at posted prices) and is the Phase-A.0 stage-drift failure mode the framework's anti-fishing discipline exists to prevent. The synthetic Δ^(a_s) trace under each (F1-F4, path-source) tuple is a structural-exposure characterization of a hypothetical-but-pre-committed cash-flow geometry — what Δ^(a_s) WOULD have been each week if a Stage-3 vault had been operating with the f-th schedule on the s-th observed COP/USD path. **Every plan task below produces structural-exposure outputs, not WTP inferences.** Executors implementing this plan MUST keep the deliverable framed as structural-exposure characterization throughout; any drift into WTP-inference language is a methodology error, not a documentation nit.

The plan decomposes the spec's v0 → v1 → v2 → v3 internal ladder into six dependency-ordered phases, each with multiple tasks dispatched to specialist subagents under the trio-checkpoint discipline (`feedback_notebook_trio_checkpoint`) where notebooks are the deliverable, the per-artifact `DATA_PROVENANCE.md` mirror discipline (spec §3.A; extended in v1.4 with `q_t_schedule_family_pinned` for v2 synthetic artifacts) where data parquets are the deliverable, and the typed-exception HALT pathway (spec §6) where the data substrate or tooling fails the spec's pre-pinned exit criteria. The free-tier-only budget pin (spec §5 / §5.A; SQD Network primary archive + Alchemy free-tier spot RPC under burst-rate discipline + The Graph subgraphs + Dune ad-hoc SQL + public-RPC consistency-degraded fallback) is enforced in every Phase-1+ task that issues network requests; auto-pivot to paid services is anti-fishing-banned per spec §5.A degradation Step 5. v1.4's v2 reframe SHRINKS the network footprint to ZERO RPC calls in Phase 3 (synthetic generation is local Python compute over v0's `mento_swap_flow_inventory.parquet` plus the Stage-1 panel). Cross-path coordination with Path A is **REVISED IN v1.4**: the B → A `r_al_handoff.json` emission at Phase 2 is PRESERVED unchanged; the A → B v3 σ-distribution coupling at Phase 4 is PROMOTED FROM OPTIONAL TO NORMATIVE per spec §8 — Phase 4 consumes Path A's `v3_handoff.json` IF AVAILABLE at Phase 4 entry to emit the optional Path-A-path-replay envelope artifact; Phase 4 proceeds with the historical-path-only hybrid backtest as the spec-pinned fallback if Path A v3 has not delivered.

## §2 — Phase decomposition

The plan is six phases. Phases 0-5 align to the spec's v0 → v3 ladder plus environment scaffolding (Phase 0) and convergence-verdict authoring (Phase 5).

**Phase 0 — Environment scaffolding.** Stand up the Path B working directory (`contracts/.scratch/pair-d-stage-2-B/`) and notebook directory (`contracts/notebooks/pair_d_stage_2_path_b/`); pin Python + DuckDB + Parquet + SQD Network client + Alchemy free-tier client + public-RPC fallback config in `env.py` mirroring the Pair D Stage-1 pattern at `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/env.py`; author the per-artifact `DATA_PROVENANCE.md` template (spec §3.A 8-field schema; extended in v1.4 with `q_t_schedule_family_pinned` for v2 synthetic artifacts); pin the spec sha256 in this plan's frontmatter (already done above); commit scaffolding only. No data extraction yet. PRESERVED FROM v1.0.

**Phase 1 — v0 data-coverage audit (v1.4 substrate set + new mento_swap_flow_inventory artifact).** Audit the v1.4-pinned a_l-side allowlist (Mento V3 router `0x4861840C...`, Mento V2 BiPool manager `0x22d9db95...`, Mento V2 USDm `0x765DE816...`, Mento V2 COPm `0x8A567e2a...`, Mento broker `0x777A8255...`, Mento V3 USDm/cUSD FPMM pool `0x462fe04b...`, Panoptic factory Ethereum mainnet) for venue existence, deployment block, first/last event block, event count, cumulative volume USD, TVL snapshot. v0 audit MUST verify `0x462fe04b...` is canonical Mento V3 USDm/cUSD (NOT USDm/USDC); HALT-and-CORRECTIONS-ε' if mis-attributed. v0 audit MUST enumerate Mento V2 BiPool exchange IDs via the BiPool manager `getExchanges()` view and pin the USDm/COPm exchange ID before Phase 2 dispatch (per spec v1.4 §3 substrate clarification). Emit FOUR Parquet artifacts per spec v1.4 §4.0 normative schema: `audit_summary.parquet`, `address_inventory.parquet`, `event_inventory.parquet`, AND the v1.4-NEW `mento_swap_flow_inventory.parquet` (one row per (week, mento_substrate, partition) tuple; ~135 weeks × 3 substrates × 4 partitions ≈ 1620 rows for the 2023-08 → 2026-02 window; required as v2 bound-check input per spec §3.B). Co-locate `DATA_PROVENANCE.md` per spec §3.A. Frontmatter `on_chain_pins` validation against on-chain state (no longer "freezing" since v1.4 pins are pre-committed in spec text; v0 confirms each substrate has the documented event activity in the audit window). Findings memo (1-2 pp) recommending which a_l-side candidates graduate to Phase 2 with data-availability reasons (NOT result-shaping reasons), and documenting that the v1.0-v1.3 a_s-side audit task (Bitgifty / Walapay) is closed-without-substrate per the v1.4 SYNTHESIS.md acknowledgment. Anti-fishing-load-bearing: discovery beyond allowlist requires user-adjudicated typed-exception per FLAG-B7. Phase 1 plan-Task 1.1 (allowlist confirmation, committed at `2483f08d3`) and Phase 1 TDD scaffold (committed at `6d9c8dfc6`) PRESERVED with allowlist updated to v1.4 substrate set; the plan-Task 1.1 disposition memo's `Stage2PathBASOnChainSignalAbsent` HALT is now resolved by spec v1.4's `on_chain_pins_a_s_note` (no on-chain a_s entity to pin) and the synthetic-counterfactual reframe.

**Phase 2 — v1 CF^(a_l) reconstruction (v1.4 substrate set).** For each viable pool from Phase 1 (PRIMARY: Mento V3 USDm/cUSD FPMM `0x462fe04b...`; SECONDARY: Mento V2 BiPool USDm/COPm exchange routed via BiPool manager `0x22d9db95...`), extract historical swap events from SQD Network across the maximum-feasible window (Mento V3 deployment block ~2023-08 → 2026-02 PRIMARY; Mento V2 BiPool deeper history ~2020-onwards SECONDARY), apply the FLAG-B8 two-layer non-economic-transaction partition (MEV-bot allowlist drop + atomic-arb round-trip drop), compute the FLAG-B1-pinned TWAP-weighted realized fee yield estimator `r_(a_l) = (cumulative LP-fee accrual USD) / (cumulative |ΔP|-weighted swap-volume USD)` regressed via OLS with HAC SE per substrate. Bin daily-UTC primary; weekly aggregation as standard derivation (FLAG-B3). Reference price source per spec v1.4 §7 revised FLAG-B4 ladder: Mento V3 USDm/cUSD FPMM → Mento V2 BiPool USDm/COPm → Banrep TRM daily series (the v1.0-v1.3 Uniswap V3 USDC/USDm fallback is RETIRED in v1.4); per-row `price_source` column records partition. Emit per-substrate empirical `CF^(a_l)` daily-binned series, qualitative shape-check chart against `Σ r·|FX_t − FX_{t-1}|`, and `r_al_handoff.json` per FLAG-B9 schema (B → A coupling artifact; `source_pool_address` may be a list under v1.4 if both substrate r_(a_l)s are emitted). OPTIONAL `v1_lvr_decomposition.parquet` companion artifact per spec §4 v1 output bullet, decomposing LP IL / LVR cost from the same v1 panel for v3 sensitivity reporting (NOT in the v1 critical path; emit if §5 budget permits). Co-locate `DATA_PROVENANCE.md` per §3.A. Findings memo recommending whether Phase 3 proceeds (default YES under v1.4) or v1 alone provides sufficient empirical defensibility for the M-sketch a_l-side leg.

**Phase 3 — v2 synthetic CF^(a_s) counterfactual generation (v1.4 REFRAMED per CORRECTIONS-ε; ZERO RPC calls).** v1.0's v2 task (extract on-chain settlement-leg `Transfer` events from Bitgifty / Walapay merchant flows) is RETIRED — no on-chain a_s entity exists per SYNTHESIS.md §8.1. v1.1 v2 generates a synthetic Δ^(a_s) trace under (a) historical Mento swap-flow inventory from Phase 1 v0's `mento_swap_flow_inventory.parquet` (real, observable; bound-check input), (b) pre-pinned q_t schedule families from spec §3.B {F1 monthly fixed (T=12), F2 weekly fixed (T=52), F3 front-loaded two-payment (T=12), F4 back-loaded two-payment (T=12)} (synthetic; NO post-hoc fitting), (c) observed COP/USD path (Banrep TRM + Mento V3 spot per FLAG-B4 ladder; Stage-1 panel inheritance), (d) the framework's `Δ^(a_s)_t(f, s) = (4 / ((X/Y)̄_t · ε_t · σ_t)) · Σ_{τ ∈ schedule(f, t)} q_τ · f_τ · (X/Y)_τ^{-2}` evaluated point-by-point per spec §3.B. Per-week f_τ default = 1 (path-modulating variant deferred to v3 sensitivity per ε_t pattern; this default is inherited from spec §3.B v1.4.1 micro-edit recommended treatment). ε_t pinned to 0.01 (1% spot-perturbation) per spec §3.B; sensitivity to ε_t = 0.005 + 0.02 reported as v3-side robustness companion. (X/Y)̄_t computed as trailing-4-week mean. Sweep over ALL combinations of f ∈ {F1, F2, F3, F4} and s ∈ {Banrep TRM, Mento V3 spot} per spec §3.B sensitivity-sweep normative; emit `a_s_counterfactual.parquet` per spec §4.0 Artifact 5 with one row per (f, s, week) tuple (~4 families × 2 path sources × ~135 weeks ≈ 1080 rows for 2023-08 → 2026-02 sample window). Cross-family ±20% drift check per `Stage2PathBSyntheticDriftBeyondTolerance` — fires if `(max_f|cum Δ^(a_s)(f, s_primary)| − min_f|cum Δ^(a_s)(f, s_primary)|) / mean_f(...) > 0.20`; HALT-and-disposition per established pattern with 5 spec-pinned pivots {(a) tighten q_t family pre-commitment to single Stage-3-deployment-aligned family with explicit CORRECTIONS-block; (b) document spread in v3 sensitivity reporting as known synthetic-methodology-sensitivity result; (c) narrow to {F1, F3} cross only with explicit CORRECTIONS-block; (d) escalate to user adjudication for re-pinning of §3.B family set with anti-fishing audit; (e) defer Path B convergence — emit v1 `r_al_handoff.json` only, defer v2 + v3, flag synthetic-methodology non-robustness for Stage-3}. Per-week bound-check: synthetic `|Δ^(a_s)|` * scale_factor MAY NOT exceed weekly aggregate `non_lp_user` Mento substrate notional from `mento_swap_flow_inventory.parquet`; rows that violate are flagged via `delta_a_s_synthetic_bound_violation: bool` column per spec §4.0 Artifact 5 schema. CONDITIONAL OPTIONAL: if Path A v3's `v3_handoff.json` is available at Phase 3 entry per spec §8 v1.4 NORMATIVE coupling, ALSO emit `a_s_counterfactual_pathA_replay.parquet` per spec §4.0 Artifact 6 (one row per (f, path_a_path_idx, week) tuple replaying Δ^(a_s) under Path A's MC σ-paths instead of historical observed COP/USD path). v1 ↔ v2 monthly reconciliation per FLAG-B5 PRESERVED in spirit, now under v1 realized × v2 synthetic per (f, s) combination producing one reconciliation series per family-source combination. Co-locate `DATA_PROVENANCE.md` per §3.A with `q_t_schedule_family_pinned` field populated per spec §3.A v1.4 template extension. Local Python compute ONLY: ZERO RPC calls; ZERO additional Alchemy CU; ZERO additional Dune credits per spec §5.A v1.4 v2 retired-network-projection. Anti-fishing posture per spec §7: q_t schedule families pre-committed in spec §3.B BEFORE any v2 generation; tightening or expanding the family set post-data is anti-fishing-banned; the §3.B 20% drift tolerance is pre-committed and may not be tightened to force a HALT or loosened to absorb a sweep that revealed schedule-choice was the dominant signal.

**Phase 4 — v3 hybrid realized-+-synthetic CPO retrospective backtest (v1.4 reframe).** Replay the Mento-V3-availability-window slice 2023-08 → 2026-02 of realized COP/USD σ-paths through a theoretical `Π(σ_T) = K · √σ_T` replication using the empirical `r_(a_l)` from Phase 2 (realized) AND the synthetic Δ^(a_s) trace from Phase 3 (synthetic, per (f, s) combination). σ_T input is realized monthly log-return-squared from Stage-1 Pair D's COP/USD series (FLAG-B6 PRESERVED); implied vol rejected as primary per spec §7 anti-fishing. K_l = K_s simulated equilibrium check per (q_t family, σ-source) cross product: K_l calibrated to v1's empirical r_(a_l); K_s solved per family from v2's synthetic Δ^(a_s); per-(f, s) residual K_l − K_s reported (the dispatch brief §6.8 K equilibrium question becomes a SIMULATED equilibrium per spec §2 v3 reframe). NEW v1.1 sub-task per spec §8 v1.4 NORMATIVE A → B coupling: consume Path A v3's `v3_handoff.json` IF AVAILABLE at Phase 4 entry (consume-when-available semantics; non-blocking if Path A v3 has not shipped). When `v3_handoff.json` available: ALSO replay the same hybrid backtest using Path A v3's MC σ-paths instead of (or alongside) the realized COP/USD σ-path, producing a parametric P&L distribution under Path A's stochastic-σ assumptions; emit OPTIONAL `a_s_counterfactual_pathA_replay.parquet` companion deliverable per spec §4.0 Artifact 6 (cross-listed from Phase 3 OPTIONAL output if not already emitted). When `v3_handoff.json` unavailable: historical-path-only hybrid envelope is the deliverable per spec §8 consume-when-available default. Compute hybrid CPO P&L for both legs across sample per (f, s) combination. Emit hybrid P&L envelope per (f, s) characterized by mean, SD, full quantile vector, max drawdown, plus regime-conditional decomposition keyed to four regimes RC FLAG #6 identified (post-2014 oil shock, COVID, Fed tightening, normalcy; subset to Mento-V3-availability slice with regime-coverage caveat). Calibration-handoff packet `v3_handoff.json` (Path B side; distinct from the Path A → B handoff of the same name) ready: includes `r_al_handoff.json` already emitted at Phase 2 + per-(f, s) hybrid envelope JSON + (if Path A v3 consumed) per-(f, s) Path-A-path-replay envelope JSON. Co-locate `DATA_PROVENANCE.md` per §3.A.

**Phase 5 — Convergence + verdict authoring.** Synthesize the v0 → v3 outputs into a single structural-exposure characterization memo. Quantify `|Δ^(a_l)|` (empirical, on-chain) and `|Δ^(a_s)|` (synthetic, per (f, s) combination) magnitudes in $-notional that the CPO would neutralize on observed transaction flows. Draft `MEMO.md` + machine-readable `gate_verdict.json` (extended in v1.1 with per-(f, s) fields and `path_a_v3_consumed: bool` field reflecting consume-when-available coupling). 3-way implementation review per `feedback_implementation_review_agents` (Code Reviewer + Reality Checker + Senior Developer; Data Engineer for fixes). Surface to user via `DISPOSITION.md`. CLAUDE.md Active iteration block update under 2-wave verify per `feedback_two_wave_doc_verification`.

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

#### Task 1.1: Confirm v1.4 fixed allowlist + Mento V3 deployment manifest + Mento V2 BiPool exchange-id pinning

**Status:** plan-Task 1.1 already executed against v1.0 plan (committed at `2483f08d3`); this v1.1 entry RE-PINS the allowlist content to the v1.4 substrate set per spec §3 and records the CORRECTIONS-ε resolution path for the original `Stage2PathBASOnChainSignalAbsent` HALT surfaced by the v1.0 execution.

**Goal:** Verify the spec v1.4 `on_chain_pins` allowlist is current as of v0 entry; pull the Mento V3 deployment manifest to enumerate all in-scope contract addresses (per FLAG-B7, discovery beyond allowlist requires typed-exception). Per spec v1.4 §3 substrate clarification: enumerate Mento V2 BiPool exchange IDs via the BiPool manager `getExchanges()` view function and pin the USDm/COPm exchange ID before Phase 2 dispatch. Verify `0x462fe04b...` is canonical Mento V3 USDm/cUSD (NOT USDm/USDC); HALT-and-CORRECTIONS-ε' if mis-attributed.

**Inputs:**
- Spec v1.4 frontmatter `on_chain_pins` block (NORMATIVE substrate set)
- Spec v1.4 `on_chain_pins_a_s_note` (records no on-chain a_s entity exists; resolves v1.0 plan-Task 1.1 `Stage2PathBASOnChainSignalAbsent` HALT)
- Mento V3 deployment manifest (canonical source: Mento Labs GitHub or Celo block-explorer-verified reference)
- Mento V2 BiPool manager `0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901` `getExchanges()` view return value
- Existing v1.0 plan-Task 1.1 disposition memo at `contracts/.scratch/path-b-stage-2/phase-1/task_1_1_plan_disposition.md` (committed `2483f08d3`)
- Memory: `project_no_mento_carbon_protocol_integration` (Mento V3 deployment manifest has zero Carbon/Bancor references — informs in-scope contract surface)
- Memory: `project_mento_canonical_naming_2026` β-corrigendum (`0xc92e8fc2…` is Minteo-fintech, OUT of scope; canonical Mento-native COPm = `0x8A567e2aE79CA692Bd748aB832081C45de4041eA`)

**Owner:** Data Engineer

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v0/allowlist.toml` enumerating all in-scope contract addresses with role labels (router, bipool_manager, broker, fpmm_pool, token, fee_collector, panoptic_factory, other) and network attribution (celo-mainnet vs ethereum-mainnet); a_s-side row count is exactly ZERO per spec v1.4 `on_chain_pins_a_s_note`
- File: `contracts/.scratch/pair-d-stage-2-B/v0/mento_v2_bipool_exchanges.json` enumerating Mento V2 BiPool exchanges per `getExchanges()` view with USDm/COPm exchange ID pinned + sha256 + audit_block + verification timestamp
- File: `contracts/.scratch/pair-d-stage-2-B/v0/mento_v3_fpmm_usdm_cusd_attribution_verify.json` confirming `0x462fe04b...` token0 + token1 are USDm + cUSD (NOT USDC); HALT-and-CORRECTIONS-ε' if mis-attributed
- Update existing v1.0 plan-Task 1.1 disposition memo at `task_1_1_plan_disposition.md` recording CORRECTIONS-ε resolution path: spec v1.4 `on_chain_pins_a_s_note` resolves the v1.0 `Stage2PathBASOnChainSignalAbsent` HALT (no on-chain a_s entity to pin; synthetic counterfactual reframe is the v2 methodology); the v1.0 disposition memo's allowlist placeholders for Bitgifty / Walapay are now DEPRECATED per spec v1.4 frontmatter
- Section in `DATA_PROVENANCE.md` recording manifest source URL + `getExchanges()` view block + fetch_timestamp + manifest sha256

**Success criteria:**
- Allowlist contains ≥6 a_l-side contracts per spec v1.4 substrate set (lower bound triggers `Stage2PathBAuditScopeAnomaly` per spec §4.0)
- Allowlist contains ≤20 contracts (upper bound triggers same exception)
- a_s-side allowlist row count = 0 per spec v1.4 `on_chain_pins_a_s_note`
- Mento V2 USDm/COPm BiPool exchange ID pinned with non-zero `tradingLimitConfig` evidence
- Mento V3 USDm/cUSD pool `0x462fe04b...` token-pair attribution confirmed
- Minteo-fintech `0xc92e8fc2…` ABSENT (memory β-corrigendum)
- All addresses 0x-prefixed checksummed

**Dependencies:** Phase 0 complete

**Typed-exception triggers:**
- `Stage2PathBAuditScopeAnomaly` if a_l-side allowlist row count violates 6-20 range
- HALT-and-CORRECTIONS-ε' (NEW pre-pinned trigger per v1.1) if `0x462fe04b...` token-pair is USDm/USDC instead of USDm/cUSD; user-adjudicated typed exception with substrate re-pinning
- HALT-and-surface if Mento V3 deployment manifest OR Mento V2 BiPool `getExchanges()` view is unreachable from documented sources (spec §6 has no specific exception for manifest unreachability; treat as user-adjudicated HALT)
- `Stage2PathBASOnChainSignalAbsent` MUST NOT be raised by v1.1 executors (DEPRECATED per spec v1.4 §6); if raised, orchestrator routes to spec v1.3 → v1.4 Change Log explanation and executor proceeds under v1.4 v2 reframe

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

#### Task 1.3.b: Emit mento_swap_flow_inventory.parquet (v1.4 NEW per CORRECTIONS-α; spec §4.0 Artifact 4)

**Goal:** Aggregate Phase 1 swap-event extraction into the v1.4-NEW `mento_swap_flow_inventory.parquet` per spec §4.0 Artifact 4 schema. This is the load-bearing input for Phase 3 v2 synthetic generation: per-week aggregate `non_lp_user` partition notional is the bound-check ceiling (synthetic |Δ^(a_s)| × scale_factor MAY NOT exceed weekly aggregate `non_lp_user` Mento substrate notional per spec §3.B + §4.0 Artifact 5 `delta_a_s_synthetic_bound_violation` semantics).

**Inputs:**
- Per-substrate swap events extracted in Task 1.2 for the three Mento substrates: `mento_v3_fpmm_usdm_cusd` (Mento V3 USDm/cUSD FPMM pool), `mento_v2_bipool_usdm_copm` (Mento V2 BiPool USDm/COPm exchange), `mento_broker` (Mento V2 broker swap events filtered to USDm/COPm + USDm/cUSD pairs)
- FLAG-B8 partition rules (MEV-bot allowlist + atomic-arb round-trip — same rules as Phase 2 v1; partition outputs: `non_lp_user`, `lp_mint_burn`, `mev_arb`, `total`)
- Reference-price source per FLAG-B4 ladder for USD-equivalent notional conversion at swap-time
- Spec §4.0 Artifact 4 column dtype + nullability tables + primary-key + row-count expectations

**Owner:** Data Engineer

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v0/mento_swap_flow_inventory.parquet` (Snappy compressed; schema_version metadata field hashing column-set + dtypes; ~135 weeks × 3 substrates × 4 partitions ≈ 1620 rows expected for 2023-08 → 2026-02 window)
- DATA_PROVENANCE.md updates: per-substrate FLAG-B8 partition rule sha256 + per-week USD-conversion reference-price source partition

**Success criteria:**
- Schema parity verified (column names + dtypes + nullability match spec §4.0 Artifact 4 exactly: `week`, `mento_substrate`, `partition`, `swap_count_week`, `notional_usd_week`, `non_lp_user_share`, `data_source_primary`)
- Primary-key uniqueness verified (`(week, mento_substrate, partition)` unique within file)
- Row count within ±50% of expected ~1620 rows; >5x deviation triggers HALT-review per `Stage2PathBAuditScopeAnomaly`
- `non_lp_user_share` populated only on `partition == 'total'` rows; null otherwise
- For each (week, mento_substrate) tuple, the four partition rows sum to the `total` partition row's notional (FLAG-B8 partition exhaustiveness invariant)
- `data_source_primary` enum values match the spec §4.0 enum (one of `sqd_network`, `alchemy_free`, `dune`, `the_graph`, `celoscan`, `etherscan`)

**Dependencies:** Task 1.3 (mento substrate event extraction is also a Task 1.2 byproduct; this task aggregates rather than re-extracts)

**Typed-exception triggers:**
- `Stage2PathBAuditScopeAnomaly` if row count out of expected bound
- `Stage2PathBProvenanceMismatch` if FLAG-B8 partition exhaustiveness invariant is violated (partitions don't sum to total within tolerance)

#### Task 1.4: TDD test suite for v0 Parquet artifacts

**Goal:** Per `feedback_strict_tdd`, every Phase 1 deliverable must have a failing test written first that the implementation then satisfies. This task is mostly a retrospective TDD compliance — write tests that the artifacts from Tasks 1.3 + 1.3.b must pass. The Phase 1 RED-stage TDD scaffold for Tasks 1.3 artifacts is committed at `6d9c8dfc6` (5 RED tests against v0 audit deliverables); v1.1 EXTENDS this with tests for the new Task 1.3.b `mento_swap_flow_inventory.parquet` artifact.

**Inputs:**
- FOUR Parquet artifacts from Task 1.3 + Task 1.3.b: `audit_summary.parquet`, `address_inventory.parquet`, `event_inventory.parquet`, `mento_swap_flow_inventory.parquet`
- Spec v1.4 §4.0 schema definitions (Artifacts 1-4)
- Existing TDD scaffold at `6d9c8dfc6` (per the v1.0 plan-Task 1.4 pattern; covers Artifacts 1-3)

**Owner:** Data Engineer (test author) + Code Reviewer (verifier)

**Outputs:**
- File: `contracts/notebooks/pair_d_stage_2_path_b/tests/test_v0_artifacts.py` (or equivalent — pytest-style; uses real Parquet files via DuckDB or pandas, NO mocks per `feedback_real_data_over_mocks`); EXTENDED in v1.1 with `test_mento_swap_flow_inventory_*` tests
- Tests covering:
  - Schema parity per artifact (all expected columns present, dtypes match, nullability match) — including new Artifact 4
  - Primary-key uniqueness per artifact (Artifact 4 PK = `(week, mento_substrate, partition)`)
  - Foreign-key referential integrity across artifacts (Artifact 4 `mento_substrate` values implicitly map to `audit_summary.venue_id`)
  - Row-count bounds per spec §4.0 (Artifact 4: ~1620 rows ±50%)
  - FLAG-B8 partition exhaustiveness invariant: per (week, mento_substrate) tuple, the four partition-row notionals sum to the `total` partition row's notional (within float-rounding tolerance)
  - sha256 stability (re-read parquet, verify sha matches DATA_PROVENANCE.md entry within ±0.01% row delta)
  - Spec §4.0 `data_source_primary` enum value validation (one of `sqd_network`, `alchemy_free`, `dune`, `the_graph`, `celoscan`, `etherscan` per v1.2.1 correction)

**Success criteria:**
- All tests pass against the Task 1.3 + Task 1.3.b artifacts
- Tests fail (RED) when artifacts are intentionally corrupted (e.g., remove a row, change a dtype, mutate sha, break partition-sum invariant) — verify the test suite catches the corruption

**Dependencies:** Task 1.3

**Typed-exception triggers:** none; test failures HALT and re-dispatch Data Engineer to fix.

#### Task 1.5: Phase 1 close — 3-way implementation review + validate v1.4 on_chain_pins

**Goal:** Per `feedback_implementation_review_agents`, every phase concludes with Code Reviewer + Reality Checker + Senior Developer review IN PARALLEL. Data Engineer fixes; no Tech Writer at implementation reviews. v1.4 spec frontmatter `on_chain_pins` block is PRE-COMMITTED in spec text; Task 1.5 validates each substrate has documented event activity in the audit window (no longer "freezing" pins because they are already pinned in spec v1.4 §3 — the v1.0 plan's "freeze on_chain_pins" semantics is RETIRED in v1.1).

**Inputs:**
- All Phase 1 outputs (allowlist.toml, mento_v2_bipool_exchanges.json, mento_v3_fpmm_usdm_cusd_attribution_verify.json, audit_metrics_raw.json, FOUR Parquets including `mento_swap_flow_inventory.parquet`, DATA_PROVENANCE.md, burst_rate_log.csv, test suite)
- Spec v1.4 frontmatter `on_chain_pins` block (PRE-COMMITTED; this task validates rather than freezes)
- Existing v1.0 plan-Task 1.1 disposition memo at `task_1_1_plan_disposition.md` (UPDATED in Task 1.1 v1.1 to record CORRECTIONS-ε resolution path)

**Owner:** Foreground Orchestrator dispatches; Code Reviewer (charge: implementation matches spec v1.4 §4.0 schema for all four artifacts; no silent-test-pass per `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons` 5-instance catalogue; trio-checkpoint citation discipline if notebook cells exist; FLAG-B8 partition exhaustiveness invariant verified for `mento_swap_flow_inventory.parquet`) + Reality Checker (charge: every audit_summary row supported by the underlying SQD/Alchemy fetches in DATA_PROVENANCE.md; no synthesized data; feasibility_v1 verdicts honest; spec v1.4 substrate-set attribution verified — `0x462fe04b...` confirmed USDm/cUSD not USDm/USDC; Mento V2 BiPool USDm/COPm exchange ID confirmed via `getExchanges()` view; CORRECTIONS-ε resolution path correctly documented in updated plan-Task 1.1 disposition memo) + Senior Developer (charge: production-readiness — could a fresh engineer re-run with only spec v1.4 + allowlist + network_config + `mento_swap_flow_inventory.parquet` ready as v2 input?). Data Engineer is on-call for fixes.

**Outputs:**
- Three reviewer verdicts + defect lists
- Integrated phase-close fixes (if defects)
- Findings memo (1-2 pp) at `contracts/.scratch/pair-d-stage-2-B/v0/findings.md` recommending which a_l-side candidates graduate to Phase 2 with data-availability reasons (NOT result-shaping reasons), confirming `mento_swap_flow_inventory.parquet` is ready as Phase 3 input, and documenting that the v1.0-v1.3 a_s-side audit task (Bitgifty / Walapay) is closed-without-substrate per spec v1.4 SYNTHESIS.md acknowledgment
- Commit with `Doc-Verify: code=<CR-id> reality=<RC-id> senior=<SD-id>` trailer

**Success criteria:**
- All three reviewers return PASS or PASS-WITH-REVISIONS
- BLOCK-severity defect from any reviewer HALTS commit and re-dispatches Data Engineer
- v1.4 `on_chain_pins` validated against on-chain state per spec §4 v0 normative; no spec-side edit required (v1.4 pre-commits the pin set)
- Findings memo cites data-availability reasons exclusively; any result-shaping language flagged by Reality Checker triggers HALT-disposition
- `mento_swap_flow_inventory.parquet` available at the path expected by Phase 3 v2 synthetic generator

**Dependencies:** Task 1.4

**Typed-exception triggers:**
- `Stage2PathBMentoUSDmCOPmPoolDoesNotExist` (REFRAMED in v1.4 per spec §6) — fires if v0 confirms the v1.4 PRIMARY substrate (Mento V3 USDm/cUSD FPMM pool `0x462fe04b...`) is missing OR has fewer than 100 swap events; spec v1.4 §6 pre-pinned pivots: (a) fall back to the SECONDARY substrate (Mento V2 BiPool USDm/COPm via BiPool manager) as primary a_l-side substrate with explicit CORRECTIONS-block; (b) accept cUSD/cEUR or USDm/EURm as σ-pattern proxy with explicit CORRECTIONS-block recording substrate-substitution rationale and audit that proxy substrate was not selected to produce a more favorable r_(a_l); (c) reframe Path B around USDm/EURm or USDm/GBPm pools that DO exist and document Pair-D-specific COP/USD anchor cannot be reproduced on-chain at a_l side
- HALT-and-CORRECTIONS-ε' if `0x462fe04b...` token-pair is NOT USDm/cUSD per Task 1.1 verification

### Phase 2 — v1 CF^(a_l) reconstruction

> **Trio-checkpoint discipline (NON-NEGOTIABLE per `feedback_notebook_trio_checkpoint`):** Phase 2 deliverables are notebooks. Each notebook authoring step is `(why-markdown → code-cell → interpretation-markdown)` with HALT after each trio for orchestrator review. The 4-part citation block (`feedback_notebook_citation_block`) precedes every test/decision/spec-choice in estimation or sensitivity notebooks: (1) reference / (2) why used / (3) relevance to results / (4) connection to simulator.

#### Task 2.1: Notebook 02 scaffolding — load v0 audit + per-pool extraction prep

**Goal:** Set up notebook `02_v1_cf_al.ipynb` with loaded v0 outputs, per-pool extraction config, and the four-part citation block establishing the FLAG-B1 estimator and FLAG-B4 reference-price ladder.

**Inputs:**
- v0 outputs (FOUR artifacts: `audit_summary.parquet`, `address_inventory.parquet`, `event_inventory.parquet`, `mento_swap_flow_inventory.parquet`)
- Spec v1.4 §3 FLAG-B1 normative `r_(a_l)` estimator definition
- Spec v1.4 §7 revised FLAG-B4 reference-price ladder (Mento V3 USDm/cUSD FPMM → Mento V2 BiPool USDm/COPm → Banrep TRM; the v1.0-v1.3 Uniswap V3 USDC/USDm Celo fallback is RETIRED in v1.4)
- Spec §3 FLAG-B3 daily-UTC binning normative
- Spec §3 FLAG-B8 two-layer non-economic-transaction partition rule
- v0 `findings.md` enumerating which a_l-side substrates graduated to Phase 2 (PRIMARY: Mento V3 USDm/cUSD FPMM `0x462fe04b...`; SECONDARY: Mento V2 BiPool USDm/COPm via BiPool manager `0x22d9db95...`)

**Owner:** Analytics Reporter (notebook author with mandatory trio HALTs)

**Outputs:**
- Notebook `contracts/notebooks/pair_d_stage_2_path_b/notebooks/02_v1_cf_al.ipynb` populated with:
  - Section 0: 4-part citation block per spec v1.4 §3 FLAG-B1 (reference: imported framework `DRAFT.md`; why used: pinned by spec; relevance to results: drives `r_(a_l)` estimate per substrate; connection to simulator: feeds `r_al_handoff.json` for Path A v3 calibration; v1.4 substrate clarification: Mento V3 USDm/cUSD primary + Mento V2 BiPool USDm/COPm secondary)
  - Section 1 first trio: load v0 outputs + per-substrate extraction config (which substrates, which block ranges, FLAG-B7 allowlist enforcement)
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

**Goal:** Compute the FLAG-B1-pinned TWAP-weighted realized fee yield estimator on the post-partition swap data, per substrate. Estimator: numerator = cumulative LP-fee accrual USD; denominator = cumulative |ΔP|-weighted swap-volume USD; OLS regression form on the fee-accrual-on-|ΔP|-volume specification with HAC SE.

**Inputs:**
- Per-substrate partitioned swap data from Task 2.2
- Per-substrate `Mint`/`Burn` events for fee-accrual computation (extracted via SQD Network in same chunked pull as swaps; if not available locally, re-extract under burst-rate discipline)
- Reference-price source per spec v1.4 §7 revised FLAG-B4 ladder (Mento V3 USDm/cUSD FPMM spot at daily-bin close-tick → Mento V2 BiPool USDm/COPm spot → Banrep TRM; Uniswap V3 USDC/USDm fallback RETIRED)
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

#### Task 2.3.b (OPTIONAL per CORRECTIONS-α): LVR decomposition v1_lvr_decomposition.parquet

**Goal:** Per spec v1.4 §4 v1 output bullet, OPTIONALLY emit `v1_lvr_decomposition.parquet` decomposing LP IL / LVR cost from the same v1 panel for v3 sensitivity reporting. Spec v1.4 `lvr_acknowledgment_v1_4` notes that Path B v1 measures the LP GROSS FEE INCOME side (∝ |ΔFX|) — the observable empirical anchor — while LP NET = gross fee − LVR cost is structurally short-variance per Milionis-Moallemi-Roughgarden 2022. The IL / LVR cost is decomposable from the same v1 panel (per-Mint/Burn-event reserve snapshots + spot-price path) but is NOT in the v1 critical path. Emit IF AVAILABLE within §5 free-tier budget; SKIP without prejudice if budget is tight.

**Inputs:**
- Per-substrate partitioned swap data from Task 2.2
- Per-substrate `Mint`/`Burn` event extraction (already extracted in Task 2.3 fee-accrual pipeline)
- Per-substrate reference-price time series from Task 2.3 (Mento V3 spot × Banrep TRM ladder per FLAG-B4)
- Spec v1.4 `lvr_acknowledgment_v1_4` for methodology framing

**Owner:** Analytics Reporter (notebook author + trio HALT discipline) supported by Data Engineer

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v1/<substrate_slug>_lvr_decomposition.parquet` (per-substrate; columns: `day_utc`, `gross_fee_income_usd`, `lvr_cost_usd`, `lp_net_usd`, `delta_fx_abs_usd`, `instant_sigma_squared`, `reserve_snapshot_sha256`); OR explicit SKIP marker `v1_lvr_decomposition_skipped.md` recording the budget-or-feasibility reason
- DATA_PROVENANCE.md update reflecting reserve-snapshot extraction provenance
- Notebook trios:
  - Trio A: per-Mint/Burn reserve-snapshot reconstruction (why → code → interpretation reporting per-day reserve trajectories); HALT
  - Trio B: LVR cost computation per the LVR formula (Milionis-Moallemi-Roughgarden 2022); per-day LVR cost decomposition (why → code → interpretation reporting cumulative LVR vs cumulative gross fee comparison); HALT

**Success criteria:**
- IF EMITTED: per-substrate LVR decomposition spans the v1 sample window; LVR cost is non-negative; LP NET = gross fee − LVR cost identity verified within float-rounding tolerance; 4-part citation block cites spec v1.4 `lvr_acknowledgment_v1_4` + Milionis-Moallemi-Roughgarden 2022 LVR paper
- IF SKIPPED: skip-marker memo states the reason explicitly (budget exceeded; substrate event coverage insufficient; technical blocker requiring separate dispatch); SKIP MUST NOT be silent

**Dependencies:** Task 2.3

**Typed-exception triggers:** none specific to this task; if reserve-snapshot reconstruction surfaces inconsistencies, surfaces as `Stage2PathBProvenanceMismatch` (same as Task 2.2 / 2.3)

#### Task 2.4: Notebook 02 — `CF^(a_l)` daily series reconstruction + qualitative shape check (trio-checkpointed)

**Goal:** Compute the per-substrate `CF^(a_l)_T = Σ_t r_(a_l) · |(X/Y)_t − (X/Y)_{t-1}|` daily-binned series; window scope is the Mento-V3-availability slice 2023-08 → 2026-02 PRIMARY (per spec v1.4 §2 Block-range bounds revision; the full Pair D 2015-2026 window is NOT reachable on-chain because Mento V3 deployment block postdates 2015). Generate qualitative shape-check chart against `Σ r·|FX_t − FX_{t-1}|` framework prediction. Sign-and-magnitude pattern only; no goodness-of-fit threshold (no honest threshold exists absent reference baselines per spec §2 v1 Exit).

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

### Phase 3 — v2 synthetic CF^(a_s) counterfactual generation (v1.4 REFRAMED per CORRECTIONS-ε)

> **Substantive rewrite per CORRECTIONS-α.** v1.0's Phase 3 (extract on-chain settlement-leg Transfers from Bitgifty / Walapay merchant flows) is RETIRED in v1.1 because no on-chain a_s entity exists per SYNTHESIS.md §8.1 (4 independent research tracks; user decision 2026-05-03). v1.1 Phase 3 is **synthetic counterfactual generation**: produce a simulated time series of Δ^(a_s) under (a) historical Mento swap-flow inventory from Phase 1 v0 (real, observable), (b) pre-pinned q_t schedule families from spec v1.4 §3.B {F1 monthly, F2 weekly, F3 front-loaded, F4 back-loaded} (synthetic; NO post-hoc fitting), (c) observed COP/USD path (Banrep TRM + Mento V3 spot per FLAG-B4 ladder), (d) optionally Path A v3's σ-distribution per spec §8 v1.4 NORMATIVE coupling (consume-when-available). Output is simulation, NOT measurement; framing per spec v1.4 §1 + CORRECTIONS-γ inheritance: structural-exposure characterization of a hypothetical-but-pre-committed cash-flow geometry under pre-pinned q_t schedules, NOT a WTP estimate. Phase 3 has ZERO RPC calls — local Python compute only per spec §5.A v1.4 v2 retired-network-projection. The v1.0 typed-exception trigger `Stage2PathBASOnChainSignalAbsent` is DEPRECATED per spec §6 v1.4; v1.1 introduces `Stage2PathBSyntheticDriftBeyondTolerance` as the v2 HALT-and-flag mechanism.

> **Trio-checkpoint discipline (NON-NEGOTIABLE per `feedback_notebook_trio_checkpoint`):** Phase 3 deliverable is notebook `03_v2_cf_as.ipynb`. Each notebook authoring step is `(why-markdown → code-cell → interpretation-markdown)` with HALT after each trio for orchestrator review. The 4-part citation block (`feedback_notebook_citation_block`) precedes every test / decision / spec choice: (1) reference / (2) why used / (3) relevance to results / (4) connection to simulator.

#### Task 3.A: Notebook 03 scaffolding — load v0 swap-flow inventory + Stage-1 panel + spec §3.B q_t pre-commitment recording

**Goal:** Set up notebook `03_v2_cf_as.ipynb` with loaded v0 outputs (especially `mento_swap_flow_inventory.parquet`), Stage-1 panel inheritance (COP/USD daily/weekly series; realized weekly σ from FLAG-B6), spec v1.4 §3.B q_t schedule family pre-commitment recorded verbatim in citation blocks, and the framework Δ^(a_s) sensitivity formula citation per spec §3.B. Conditional load of Path A v3 `v3_handoff.json` (consume-when-available) per spec §8 v1.4 NORMATIVE A → B coupling.

**Inputs:**
- v0 outputs: `mento_swap_flow_inventory.parquet` (per spec §4.0 Artifact 4; PRIMARY input for synthetic generation bound-check)
- Stage-1 outputs: COP/USD daily + weekly series; realized weekly σ_T from joint panel sha `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`
- Spec v1.4 §3.B q_t schedule family pre-commitment (verbatim citation; NO redefinition in plan)
- Spec v1.4 §3.B ε_t = 0.01 default + (X/Y)̄_t trailing-4-week mean discretization
- Spec v1.4 §3.B sample-window scope normative (Mento-V3-availability window 2023-08 → 2026-02)
- Spec v1.4 §3.B 20% cross-family spread tolerance pre-commitment
- Conditional input: Path A v3 `v3_handoff.json` IF AVAILABLE at Phase 3 entry (per spec §8 v1.4 schema `{sigma_paths, path_source, path_count, sha256_of_path_a_v3_artifact}`)

**Owner:** Analytics Reporter (notebook author with mandatory trio HALTs)

**Outputs:**
- Notebook `contracts/notebooks/pair_d_stage_2_path_b/notebooks/03_v2_cf_as.ipynb` populated with:
  - Section 0: 4-part citation block per spec v1.4 §3.B (reference: imported framework `DRAFT.md` Δ^(a_s) sensitivity definition + Milionis-Moallemi-Roughgarden 2022 LVR for a_l-side complementarity; why used: pre-pinned by spec §3.B {F1, F2, F3, F4} family set + ε_t = 0.01 + 20% drift tolerance; relevance to results: drives synthetic Δ^(a_s) trace per (f, s) tuple; connection to simulator: feeds `a_s_counterfactual.parquet` for v3 hybrid backtest)
  - Section 1 first trio: load v0 `mento_swap_flow_inventory.parquet` + Stage-1 panel + spec §3.B q_t pre-commitment (verbatim) + (conditional) Path A v3 `v3_handoff.json`; HALT
- Conditional-input load decision recorded: `path_a_v3_handoff_consumed: bool` field in notebook metadata

**Success criteria:**
- Notebook opens cleanly; section 0 citation block is complete (4 parts; cites spec §3.B verbatim; cites SYNTHESIS.md §8.1 / §8.2 for the v1.4 reframe rationale)
- Section 1 trio HALTs before code execution (orchestrator reviews the why-block before code lands)
- Conditional Path A v3 handoff load is non-blocking: notebook proceeds either way
- Notebook commit trailer: `Doc-Verify: orchestrator-only-pre-Phase-5 (3-way review deferred to Task 5.2)` per Stage-1 Pair D plan trailer convention

**Dependencies:** Phase 2 close

**Typed-exception triggers:** none at scaffolding stage

#### Task 3.B: Synthetic Δ^(a_s) generation per (f, s) tuple emitting a_s_counterfactual.parquet (trio-checkpointed)

**Goal:** For each q_t schedule family f ∈ {F1, F2, F3, F4} and each observed COP/USD path source s ∈ {Banrep TRM, Mento V3 spot}, generate the per-week synthetic Δ^(a_s)_t(f, s) trace per the spec §3.B framework formula. Apply per-week bound-check against `mento_swap_flow_inventory.parquet` `non_lp_user` partition (synthetic |Δ^(a_s)| × scale_factor MAY NOT exceed weekly aggregate `non_lp_user` Mento substrate notional). Emit `a_s_counterfactual.parquet` per spec §4.0 Artifact 5 schema.

**Inputs:**
- Notebook 03 from Task 3.A (loaded inputs)
- Spec v1.4 §3.B framework formula `Δ^(a_s)_t(f, s) = (4 / ((X/Y)̄_t · ε_t · σ_t)) · Σ_{τ ∈ schedule(f, t)} q_τ · f_τ · (X/Y)_τ^{-2}` < 0
- Spec v1.4 §3.B per-family schedule definitions: F1 (q_τ = B_T / 12, monthly), F2 (q_τ = B_T / 52, weekly), F3 (q_1 = q_T = 0.5·B_T at τ = 1 + τ = 12), F4 (q_{T-1} = q_T = 0.5·B_T at τ = 11 + τ = 12)
- Spec v1.4 §3.B per-family schedule cadence rules: F1 (q_τ lands first week of each calendar month), F2 (q_τ lands every Monday), F3 (q_τ at week 1 + week 52), F4 (q_τ at week 47 + week 52 of each rolling 52-week horizon)
- Spec v1.4 §3.B B_T baseline: B_T = 1 unit of local currency (COP) for synthetic-generation primary; reporting in dimensionless ratios that scale linearly with deployment-time B_T choice
- Spec v1.4 §3.B f_τ default = 1 (path-modulating variant deferred to v3 sensitivity)
- Spec v1.4 §4.0 Artifact 5 schema (column dtype + nullability + primary key)

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v2/a_s_counterfactual.parquet` (Snappy compressed; schema_version metadata field hashing column-set + dtypes per spec §4.0 v1.4 Artifact 5; expected ~4 families × 2 path sources × ~135 weeks ≈ 1080 rows for 2023-08 → 2026-02 window)
- DATA_PROVENANCE.md update with `q_t_schedule_family_pinned` field populated per spec §3.A v1.4 template extension (descriptive string identifying the §3.B family + parameter spec hash sha256)
- Notebook trios:
  - Trio A: per-family q_τ schedule construction (verbatim from spec §3.B; why → code → interpretation reporting per-family schedule trace); HALT
  - Trio B: per-(f, s, week) Δ^(a_s) computation via spec §3.B framework formula (why → code → interpretation reporting per-(f, s) cumulative magnitude); HALT
  - Trio C: per-week bound-check against `non_lp_user` partition (why → code → interpretation reporting bound-violation count per (f, s) tuple; populates `delta_a_s_synthetic_bound_violation` column); HALT

**Success criteria:**
- Per-(f, s, week) Δ^(a_s) is finite negative (framework prediction Δ^(a_s) < 0; sign-positive triggers HALT-review for spec §3.B formula implementation error)
- Schema parity verified (column names + dtypes + nullability match spec v1.4 §4.0 Artifact 5 exactly)
- Primary-key uniqueness verified (`(q_t_schedule_family, week, cop_usd_path_source)` unique within file)
- Foreign-key referential integrity verified (`week` × Mento substrate selection maps to `mento_swap_flow_inventory.parquet`)
- Row count within ±5% of expected ~1080 rows
- 4-part citation block preceding the per-(f, s, week) Δ^(a_s) computation cell cites: (1) spec §3.B framework formula; (2) why used = pre-pinned methodology + spec-text verbatim; (3) relevance to results = direct synthetic estimator for Δ^(a_s); (4) connection to simulator = feeds v3 hybrid backtest + (consume-when-available) Path A v3 σ-path replay

**Dependencies:** Task 3.A

**Typed-exception triggers:**
- `Stage2PathBProvenanceMismatch` if re-generation of `a_s_counterfactual.parquet` produces sha drift outside identical-input expectation (synthetic generation should be deterministic given pinned inputs)

#### Task 3.C (CONDITIONAL OPTIONAL per spec §8 v1.4 NORMATIVE A → B coupling): Path A v3 σ-path replay → a_s_counterfactual_pathA_replay.parquet

**Goal:** IF Path A v3's `v3_handoff.json` was loaded at Task 3.A (consume-when-available semantics), ALSO generate the synthetic Δ^(a_s) trace under each of Path A's MC σ-paths instead of (or alongside) the historical observed COP/USD path. Emit `a_s_counterfactual_pathA_replay.parquet` per spec §4.0 Artifact 6 schema. SKIP without prejudice if Path A v3 has not delivered.

**Inputs:**
- Notebook 03 from Tasks 3.A + 3.B (loaded inputs + base synthetic generation pipeline)
- Path A v3 `v3_handoff.json` per spec §8 v1.4 schema (from Task 3.A conditional load)
- Spec v1.4 §4.0 Artifact 6 schema (mirrors Artifact 5 with `cop_usd_path_source` replaced by `path_a_path_idx` int64 in `[0, path_a_v3_handoff.path_count − 1]`)

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v2/a_s_counterfactual_pathA_replay.parquet` (one row per (q_t_schedule_family, path_a_path_idx, week) tuple) — emitted IF Path A v3 consumed; SKIP-marker memo `pathA_replay_skipped.md` recording the SKIP reason if Path A v3 not consumed
- DATA_PROVENANCE.md update with Path A v3 handoff sha256 + Path A v3 source notebook output sha256 (both from `v3_handoff.json` `sha256_of_path_a_v3_artifact` field)
- Notebook trios (CONDITIONAL on Path A v3 consumption):
  - Trio A: Path A v3 σ-path matrix load + integrity verification (why → code → interpretation reporting per-path σ trace shape + sha256 verification); HALT
  - Trio B: per-(f, path_idx, week) Δ^(a_s) computation reusing Task 3.B formula (why → code → interpretation reporting per-family magnitude distribution across paths); HALT

**Success criteria:**
- IF EMITTED: schema parity verified per spec §4.0 Artifact 6; primary key unique; row count = 4 families × `path_count` × ~135 weeks; `path_a_v3_handoff` sha matches `sha256_of_path_a_v3_artifact` field
- IF SKIPPED: skip-marker memo states the reason explicitly (Path A v3 has not delivered `v3_handoff.json` at Phase 3 entry); SKIP MUST NOT be silent
- Anti-fishing per spec §7: SAME §3.B-pinned q_t families {F1, F2, F3, F4} used; NO substitution of family set under Path A's paths to produce a more agreeable convergence

**Dependencies:** Task 3.B + (conditional) Task 3.A handoff load

**Typed-exception triggers:** none specific; if Path A v3 sha verification fails, HALT-and-surface (potential cross-path provenance corruption)

#### Task 3.D: Cross-family ±20% drift check per spec §3.B + monthly v1 ↔ v2 reconciliation per FLAG-B5 (trio-checkpointed)

**Goal:** Compute the cross-family spread tolerance check per spec §3.B + §6 `Stage2PathBSyntheticDriftBeyondTolerance`: `(max_f|cum Δ^(a_s)(f, s_primary)| − min_f|cum Δ^(a_s)(f, s_primary)|) / mean_f(...) > 0.20`. Per FLAG-B5 PRESERVED: compute monthly reconciliation under v1 realized × v2 synthetic per (f, s) combination producing one reconciliation series per family-source combination.

**Inputs:**
- `a_s_counterfactual.parquet` from Task 3.B
- (conditional) `a_s_counterfactual_pathA_replay.parquet` from Task 3.C
- Per-substrate `CF^(a_l)` daily series from Task 2.4 (re-aggregated to monthly)
- Spec v1.4 §3.B 20% cross-family spread tolerance pre-commitment
- Spec v1.4 §6 `Stage2PathBSyntheticDriftBeyondTolerance` HALT-disposition pre-commitment + 5 pre-pinned pivots

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v2/cross_family_drift_check.json` with fields: `cumulative_per_family` (object: F1/F2/F3/F4 → cumulative |Δ^(a_s)|), `family_mean`, `family_max`, `family_min`, `cross_family_spread_ratio`, `tolerance_threshold: 0.20`, `tolerance_violated: bool`
- Per-(f, s) monthly reconciliation Parquet at `contracts/.scratch/pair-d-stage-2-B/v2/reconciliation_<substrate>_<f>_<s>_monthly.parquet`
- Per-(f, s) cumulative-delta series Parquet at `contracts/.scratch/pair-d-stage-2-B/v2/reconciliation_<substrate>_<f>_<s>_cumulative.parquet`
- Per-(f, s) structural-exposure |Δ^(a_s)| in $-notional summary at `contracts/.scratch/pair-d-stage-2-B/v2/structural_exposure_summary_<f>_<s>.json` (per CORRECTIONS-γ deliverable framing — characterizes magnitude the CPO would neutralize on observed-flow-bounded synthetic counterfactual; explicitly NOT a WTP estimate)
- IF `tolerance_violated == true`: typed-exception HALT memo at `contracts/.scratch/pair-d-stage-2-B/v2/Stage2PathBSyntheticDriftBeyondTolerance_disposition.md` per spec §6 5-pivot enumeration; orchestrator routes to user adjudication; no auto-pivot
- Notebook trios:
  - Trio A: cross-family spread computation + tolerance check (why → code → interpretation reporting per-family cumulative + spread ratio + tolerance verdict); HALT
  - Trio B: per-(f, s) monthly reconciliation aggregation (why → code → interpretation reporting per-month overlap count + cumulative-delta shape); HALT
  - Trio C: per-(f, s) structural-exposure $-notional summary (structural-exposure characterization framing; per-(f, s) magnitude); HALT

**Success criteria:**
- Cross-family spread tolerance computed per spec §3.B formula verbatim; verdict (within / outside ±20%) is the v2 PASS / HALT determination per spec §3.B
- IF tolerance respected: v2 PASSES; proceed to Phase 4
- IF tolerance violated: typed-exception HALT fires with 5-pivot disposition memo per spec §6; user adjudication required; auto-pivot through pivots (a)-(c) anti-fishing-banned; pivot (d) requires explicit user adjudication for §3.B family-set re-pinning with anti-fishing audit; pivot (e) is the cleanest HALT-and-park option (defer Path B convergence; emit v1 `r_al_handoff.json` only)
- Monthly reconciliation conforms to FLAG-B5 (per-(f, s) overlap with v1 realized series; cumulative-delta + per-month forms both emitted)
- All structural-exposure summary JSONs use structural-exposure framing exclusively; any WTP-implying language flagged by Reality Checker triggers HALT-disposition

**Dependencies:** Task 3.B + Task 2.4 (cross-phase dependency); conditional dependency on Task 3.C (if Path A v3 consumed)

**Typed-exception triggers:**
- `Stage2PathBSyntheticDriftBeyondTolerance` (CENTRAL v2 HALT mechanism) per spec §6 v1.4

#### Task 3.E: Phase 3 close — 3-way implementation review

**Goal:** Per `feedback_implementation_review_agents`, Phase 3 close gate.

**Inputs:** All Phase 3 outputs (notebook 03 + `a_s_counterfactual.parquet` + (conditional) `a_s_counterfactual_pathA_replay.parquet` + `cross_family_drift_check.json` + per-(f, s) reconciliation parquets + per-(f, s) structural-exposure summaries + DATA_PROVENANCE.md updates)

**Owner:** Foreground Orchestrator dispatches; Code Reviewer (charge: notebook trios respect 4-part citation block discipline; no silent-test-pass per `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons` 5-instance catalogue; spec §3.B q_t schedule families implemented verbatim — F1/F2/F3/F4 schedule rules per spec; ε_t = 0.01 default + f_τ = 1 default honored; per-week bound-check against `non_lp_user` partition correctly populated; cross-family spread formula matches spec §3.B verbatim) + Reality Checker (charge: every synthetic Δ^(a_s) per-(f, s, week) value supported by underlying `mento_swap_flow_inventory.parquet` + Stage-1 panel inputs per DATA_PROVENANCE.md; no synthesized data outside the spec §3.B-pinned families; structural-exposure framing exclusively respected — flag any WTP drift; SYNTHESIS.md §8 user-decision finding correctly reflected — no on-chain a_s entity rehabilitation; q_t schedule families correctly attributed to spec §3.B pre-commitment NOT to post-data fitting; cross-family drift check verdict honest) + Senior Developer (charge: production-readiness — could a fresh engineer re-run the v2 synthetic pipeline with only the spec + v0 outputs + Stage-1 panel + (conditional) Path A v3 handoff?). Data Engineer + Analytics Reporter for fixes.

**Outputs:**
- Three reviewer verdicts + defect lists
- Integrated phase-close fixes (if defects)
- Findings memo at `contracts/.scratch/pair-d-stage-2-B/v2/findings.md` summarizing v2 verdict (PASS vs `Stage2PathBSyntheticDriftBeyondTolerance`-HALT-with-pivot) and recommending Phase 4 disposition
- Commit with `Doc-Verify: code=<CR-id> reality=<RC-id> senior=<SD-id>` trailer

**Success criteria:**
- All three reviewers PASS or PASS-WITH-REVISIONS
- BLOCK-severity defect from any reviewer HALTS
- Findings memo states Phase 4 disposition with structural-exposure framing exclusively (NO WTP language) and explicitly records Path A v3 consume-status (`path_a_v3_handoff_consumed: bool`) for Phase 4 handoff continuity

**Dependencies:** Task 3.D

**Typed-exception triggers:** none specific to review; reviewer-flagged drift into WTP-inference language triggers HALT-disposition (anti-fishing-load-bearing — CORRECTIONS-γ framing fidelity is non-negotiable through v1.4 reframe)

### Phase 4 — v3 hybrid realized-+-synthetic CPO retrospective backtest (v1.4 reframe per CORRECTIONS-α)

> **v1.1 substantive scope shift.** v1.0's Phase 4 ("replay Π(σ_T) against empirical Δ^(a_s) + Δ^(a_l)") is REFRAMED to "replay Π(σ_T) against SYNTHETIC Δ^(a_s) (per (f, s) family-source combination) + EMPIRICAL Δ^(a_l)". The K_l = K_s equilibrium check becomes a SIMULATED equilibrium per (q_t family, σ-source) cross product. Path A v3 σ-distribution is NORMATIVE input per spec §8 v1.4 (was OPTIONAL under v1.0-v1.3); a new Phase 4 sub-task consumes Path A's `v3_handoff.json` IF AVAILABLE at v3 entry to emit the optional Path-A-path-replay envelope, and the historical-path-only hybrid backtest is the spec-pinned fallback if Path A v3 has not delivered.

#### Task 4.1: Notebook 04 scaffolding — load v1 + v2 outputs + (conditional) Path A v3 handoff (trio-checkpointed)

**Goal:** Set up notebook `04_v3_backtest.ipynb` with loaded v1 + v2 outputs (PRESERVED REQUIRED dependencies under v1.1 — Phase 3 v2 emits `a_s_counterfactual.parquet` always; the v1.0 SKIP path is RETIRED because synthetic generation cannot fail in the same way on-chain extraction could), framework `Π(σ_T) = K · √σ_T` replication, and the four-part citation block establishing the FLAG-B6 realized-σ_T input pin, the imported framework's `Δ^(a)` derivation, and the spec §3.B {F1, F2, F3, F4} pre-pinned q_t schedule families. Conditional load of Path A v3 `v3_handoff.json` per spec §8 v1.4 NORMATIVE coupling (consume-when-available).

**Inputs:**
- v1 outputs: per-substrate `CF^(a_l)` series, per-substrate `r_(a_l)` JSON, `r_al_handoff.json`
- v2 outputs (REQUIRED in v1.1): `a_s_counterfactual.parquet`, per-(f, s) reconciliation parquets, per-(f, s) structural-exposure summaries; (conditional) `a_s_counterfactual_pathA_replay.parquet` if Path A v3 was consumed at Phase 3
- Pair D Stage-1 COP/USD monthly log-return-squared σ_T series (FLAG-B6 pin)
- Imported CPO framework: `contracts/notes/2026-04-29-macro-markets-draft-import.md`
- Conditional input: Path A v3 `v3_handoff.json` IF AVAILABLE at Phase 4 entry per spec §8 v1.4 NORMATIVE A → B coupling (non-blocking; Phase 4 proceeds with historical-path-only if not present)
- Phase 3 findings memo at `contracts/.scratch/pair-d-stage-2-B/v2/findings.md` recording `path_a_v3_handoff_consumed: bool` for handoff continuity from Phase 3 to Phase 4

**Owner:** Analytics Reporter (notebook author with mandatory trio HALTs)

**Outputs:**
- Notebook `contracts/notebooks/pair_d_stage_2_path_b/notebooks/04_v3_backtest.ipynb` populated with:
  - Section 0: 4-part citation block per FLAG-B6 + spec §3.B (reference: imported framework Π(σ_T) replication + spec §3.B q_t pre-commitment; why used: pinned by spec; relevance: defines theoretical hybrid CPO P&L per (f, s); connection: feeds Path B v3 handoff packet to convergence dispatch + (consume-when-available) Path-A-path-replay envelope)
  - Section 1 first trio: load v1 + v2 outputs + Stage-1 σ_T series + framework constants + (conditional) Path A v3 handoff
- Conditional-input load decision recorded: `path_a_v3_handoff_consumed: bool` field in notebook metadata (consistent with Phase 3 record)

**Success criteria:**
- Notebook opens cleanly; section 0 citation block complete (4 parts)
- Section 1 trio HALTs before code execution
- Conditional Path A v3 handoff load is non-blocking: notebook proceeds either way; if Path A v3 delivered, the same handoff sha consumed at Phase 3 is re-verified for cross-phase consistency

**Dependencies:** Phase 2 close + Phase 3 close (Phase 3 SKIP is RETIRED in v1.1; v2 always produces `a_s_counterfactual.parquet`)

**Typed-exception triggers:** none at scaffolding; if Phase 3 fired `Stage2PathBSyntheticDriftBeyondTolerance` and pivot (e) was selected (defer Path B convergence; emit v1 `r_al_handoff.json` only), Phase 4 is BYPASSED per pivot (e) disposition; orchestrator routes to Phase 5

#### Task 4.2: Notebook 04 — Π(σ_T) replay + per-(f, s, month) hybrid P&L (trio-checkpointed)

**Goal:** Replay the Mento-V3-availability slice 2023-08 → 2026-02 of realized COP/USD σ-paths through `Π(σ_T) = K · √σ_T` using the empirical `r_(a_l)` from Phase 2 (realized) AND the synthetic Δ^(a_s) per (f, s) combination from Phase 3 (synthetic). Compute hybrid CPO P&L for both legs per month across the sample window per (f, s) combination.

**Inputs:**
- Notebook 04 from Task 4.1 (loaded inputs)
- Spec v1.4 §2 v3 normative + FLAG-B6 normative
- Spec v1.4 §3.B q_t family pre-commitment for K_s solving

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- Per-(f, s, month) hybrid CPO P&L Parquet at `contracts/.scratch/pair-d-stage-2-B/v3/cpo_pnl_monthly.parquet` with columns: `q_t_schedule_family`, `cop_usd_path_source`, `month_start`, `realized_sigma_T`, `K_hat`, `Pi_realized`, `cf_al_monthly` (empirical, from v1), `cf_as_monthly` (synthetic, from v2 per (f, s)), `cpo_pnl_al_leg`, `cpo_pnl_as_leg`
- Notebook trios:
  - Trio A: K̂ calibration anchor σ_0 selection (why-block cites spec §2 v3 + framework derivation; pre-pinned per anti-fishing posture; no post-data tuning); HALT
  - Trio B: per-(f, s, month) Π(σ_T) replay (why → code → interpretation reporting per-(f, s) Pi_realized distribution); HALT
  - Trio C: per-(f, s, leg) hybrid P&L decomposition (why → code → interpretation reporting envelope characterization seed per family-source); HALT

**Success criteria:**
- Per-(f, s, month) series spans maximum-feasible overlap with the Mento-V3-availability slice 2023-08 → 2026-02
- σ_T input is the Stage-1 realized monthly log-return-squared (NOT implied vol per FLAG-B6 anti-fishing)
- K̂ anchor selection is pre-pinned at trio A (anti-fishing — no post-data tuning)
- All four (F1, F2, F3, F4) families × two (Banrep TRM, Mento V3 spot) path sources represented; row count 4 × 2 × ~30 months ≈ 240 rows

**Dependencies:** Task 4.1

**Typed-exception triggers:** none specific; if FLAG-B6 σ_T input cannot be loaded from Stage-1, HALT-and-surface (Stage-1 pin chain corruption)

#### Task 4.2.b: K_l = K_s simulated equilibrium check per (f, σ-source) cross product (trio-checkpointed; v1.4 NEW per CORRECTIONS-α)

**Goal:** Per spec v1.4 §2 v3 reframe + dispatch brief §6.8 K equilibrium-pricing question, compute the SIMULATED equilibrium check K_l = K_s per (q_t family, σ-source) cross product. K_l is calibrated to v1's empirical r_(a_l); K_s is solved per family from v2's synthetic Δ^(a_s); per-(f, s) residual K_l − K_s is reported. Convergence dispatch (separate work item OUT OF SCOPE for this plan) decides which (f, s) combinations satisfy the equilibrium constraint within tolerance.

**Inputs:**
- Per-(f, s, month) hybrid P&L from Task 4.2
- v1 `r_al_handoff.json` (`r_al_point` + `r_al_hac_se` for K_l calibration anchor)
- Spec v1.4 §2 v3 K_l = K_s SIMULATED equilibrium normative
- Imported framework: K equilibrium-pricing definition (DRAFT.md §6.8 reference)

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v3/k_equilibrium_per_fs.parquet` with columns: `q_t_schedule_family`, `cop_usd_path_source`, `K_l`, `K_s`, `K_l_minus_K_s`, `K_l_minus_K_s_pct`, `equilibrium_within_tolerance: bool` (where tolerance is convergence-dispatch-defined and propagated forward; this plan reports the residual without imposing a verdict)
- Notebook trios:
  - Trio A: K_l calibration from v1's empirical r_(a_l) (why → code → interpretation reporting per-substrate K_l point + HAC-derived uncertainty); HALT
  - Trio B: K_s solving per family from v2 synthetic Δ^(a_s) (why → code → interpretation reporting per-(f, s) K_s point); HALT
  - Trio C: per-(f, s) residual K_l − K_s + percent-residual + (placeholder) within-tolerance flag (why → code → interpretation reporting per-family equilibrium spread); HALT

**Success criteria:**
- Per-(f, s) K_l, K_s, K_l − K_s, K_l − K_s percent are finite
- `equilibrium_within_tolerance` field is left as a placeholder pending convergence dispatch (this plan does not impose a tolerance threshold; it emits the residual)
- 4-part citation block cites spec v1.4 §2 v3 reframe + dispatch brief §6.8

**Dependencies:** Task 4.2

**Typed-exception triggers:** none specific

#### Task 4.3: Hybrid P&L envelope characterization + regime-conditional decomposition (trio-checkpointed)

**Goal:** Characterize the hybrid P&L envelope per (f, s) combination by mean, SD, full quantile vector, max drawdown. Decompose by the four regimes RC FLAG #6 identified as over-represented in the 2015-2026 window: post-2014 oil shock, COVID, Fed tightening, normalcy (subset to the Mento-V3-availability slice with regime-coverage caveat per spec v1.4 §2 v3 Exit normative).

**Inputs:**
- Per-(f, s, month) hybrid P&L from Task 4.2
- Per-(f, s) K equilibrium from Task 4.2.b
- Pair D Stage-1 regime classifications (from MEMO §6 / RC FLAG #6 inheritance)
- Spec v1.4 §2 v3 hybrid Exit normative

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- Per-(f, s) envelope summary JSON at `contracts/.scratch/pair-d-stage-2-B/v3/envelope_summary_<f>_<s>.json` with fields: `mean`, `sd`, `quantiles_p1_p5_p10_p25_p50_p75_p90_p95_p99`, `max_drawdown`, `min`, `max`, `n_months`
- Per-(f, s) regime-conditional decomposition Parquet at `contracts/.scratch/pair-d-stage-2-B/v3/regime_decomposition_<f>_<s>.parquet` with columns: `regime`, `n_months`, `mean_pnl`, `sd_pnl`, `min_pnl`, `max_pnl`, `cumulative_pnl`
- Per-(f, s) envelope chart PNG at `contracts/.scratch/pair-d-stage-2-B/v3/envelope_chart_<f>_<s>.png`
- Notebook trios:
  - Trio A: per-(f, s) aggregate envelope characterization (why → code → interpretation reporting per-family mean / SD / quantiles / MDD); HALT
  - Trio B: per-(f, s) regime classification + per-regime decomposition (why → code → interpretation reporting per-regime statistics + flag for regime over-representation per RC FLAG #6 + Mento-V3-availability slice subsetting caveat); HALT

**Success criteria:**
- Per-(f, s) envelope summary JSON populated with all required fields; 4 families × 2 path sources × N months
- Per-(f, s) regime decomposition spans the four regimes (with subsetting caveat where regime under-represented in slice)
- Notebook interpretation cites RC FLAG #6 explicitly (regime over-representation flagged for downstream Stage-3 calibration cadence)
- Per RC FLAG #3 inheritance: lag-6 dominance honored — Π(σ_T) replay uses 6-month-dominant lag pattern, NOT uniform 6-12mo (anti-fishing)

**Dependencies:** Task 4.2 + Task 4.2.b

**Typed-exception triggers:** none specific

#### Task 4.4 (v1.4 NEW per CORRECTIONS-α): Path A v3 σ-distribution scenario replay → per-(f, s) Path-A-path-replay envelope (CONDITIONAL OPTIONAL)

**Goal:** IF Path A v3's `v3_handoff.json` was loaded at Task 4.1 (consume-when-available semantics per spec §8 v1.4 NORMATIVE coupling), ALSO replay the same hybrid backtest using Path A v3's MC σ-paths instead of (or alongside) the realized COP/USD σ-path. Produces a parametric P&L distribution under Path A's stochastic-σ assumptions, comparable directly against Path A's own MC envelope. SKIP without prejudice if Path A v3 has not delivered.

**Inputs:**
- Notebook 04 from Tasks 4.1 + 4.2 (loaded inputs + base hybrid P&L pipeline)
- Path A v3 `v3_handoff.json` per spec §8 v1.4 schema `{sigma_paths, path_source, path_count, sha256_of_path_a_v3_artifact}` (from Task 4.1 conditional load)
- Phase 3's `a_s_counterfactual_pathA_replay.parquet` (cross-listed from Phase 3 OPTIONAL output if emitted)
- Spec v1.4 §2 v3 hybrid backtest Path-A-path-replay normative

**Owner:** Analytics Reporter (notebook author + trio HALT discipline)

**Outputs:**
- IF EMITTED: Per-(f, path_idx, month) Path-A-path-replay hybrid P&L Parquet at `contracts/.scratch/pair-d-stage-2-B/v3/cpo_pnl_pathA_replay.parquet` (one row per (q_t_schedule_family, path_a_path_idx, month) tuple)
- Per-(f) Path-A-path-replay envelope summary JSON at `contracts/.scratch/pair-d-stage-2-B/v3/envelope_summary_pathA_replay_<f>.json` with same envelope fields as Task 4.3 + `path_count` + `path_source`
- IF SKIPPED: skip-marker memo `contracts/.scratch/pair-d-stage-2-B/v3/pathA_replay_v3_skipped.md` recording the reason explicitly (Path A v3 has not delivered `v3_handoff.json` at Phase 4 entry); SKIP MUST NOT be silent
- DATA_PROVENANCE.md update with Path A v3 handoff sha256 + cross-phase consistency verification (Phase 3 vs Phase 4 same handoff sha)
- Notebook trios (CONDITIONAL on Path A v3 consumption):
  - Trio A: Path A v3 σ-path matrix re-verification (cross-phase consistency with Phase 3 consumption); HALT
  - Trio B: per-(f, path_idx, month) hybrid P&L computation reusing Task 4.2 Π(σ_T) replication formula but with Path A's σ-paths in place of realized σ_T (why → code → interpretation reporting per-family P&L distribution across paths); HALT

**Success criteria:**
- IF EMITTED: schema parity verified per spec §2 v3 hybrid Path-A-path-replay normative; cross-phase Path A v3 handoff sha consistent with Phase 3 consumption record; envelope summaries comparable directly against Path A's own MC envelope
- IF SKIPPED: skip-marker memo states the reason; SKIP MUST NOT be silent
- Anti-fishing per spec §7: SAME §3.B-pinned q_t families {F1, F2, F3, F4} used across the Path-A-path-replay; NO substitution of family set under Path A's paths to produce a more agreeable convergence

**Dependencies:** Task 4.3 + (conditional) Task 4.1 handoff load + (conditional) Phase 3 Task 3.C `a_s_counterfactual_pathA_replay.parquet`

**Typed-exception triggers:** none specific; if Path A v3 sha cross-phase consistency fails (Phase 3 consumed sha ≠ Phase 4 consumed sha), HALT-and-surface (potential cross-path provenance drift)

#### Task 4.5: Calibration-handoff packet for convergence dispatch (cross-path coupling artifact #2)

**Goal:** Emit the v3 calibration-handoff packet at `contracts/.scratch/pair-d-stage-2-B/v3/v3_handoff.json` (Path B side; distinct from the Path A → B handoff of the same name consumed at Tasks 3.C / 4.4) containing the empirical `r_(a_l)` carried forward from v1's `r_al_handoff.json`, per-(f, s) hybrid envelope summaries, per-(f) Path-A-path-replay envelope summaries (if Path A v3 consumed), and the K equilibrium per-(f, s) residual table. Convergence dispatch (separate work item, OUT OF SCOPE for this plan) consumes both Path B v3 handoff + Path A v3 envelope to compare bounds.

**Inputs:**
- v1 `r_al_handoff.json` from Task 2.5
- Per-(f, s) envelope summaries from Task 4.3
- Per-(f) Path-A-path-replay envelope summaries from Task 4.4 (if emitted)
- K equilibrium per-(f, s) residual from Task 4.2.b

**Owner:** Data Engineer

**Outputs:**
- File: `contracts/.scratch/pair-d-stage-2-B/v3/v3_handoff.json` with fields: `r_al_point`, `r_al_hac_se`, `per_fs_envelope_summaries` (object: (f, s) → envelope summary; PRESERVED structural-exposure framing — NOT WTP), `per_f_pathA_replay_envelope_summaries` (object: f → Path-A-path-replay envelope summary; null if Path A v3 not consumed), `path_a_v3_consumed: bool`, `path_a_v3_handoff_sha256` (null if not consumed), `k_equilibrium_per_fs` (object: (f, s) → K_l, K_s, K_l_minus_K_s residual), `sample_window`, `source_pool_addresses` (list per spec v1.4 substrate set), `sha256_of_v1_handoff`, `stage1_panel_sha256`

**Success criteria:**
- All required fields populated; `path_a_v3_consumed` correctly reflects consume-when-available semantics
- `sha256_of_v1_handoff` matches `r_al_handoff.json` sha
- `stage1_panel_sha256` matches Stage-1 pinned panel sha (READ-ONLY chain integrity)
- IF Path A v3 consumed: `path_a_v3_handoff_sha256` matches the sha consumed at Tasks 3.C + 4.4 (cross-phase consistency)
- Handoff is self-contained: a convergence-dispatch executor reading ONLY this JSON + Path A v3 envelope JSON can compute the convergence comparison without traversing Path B internals; per-(f, s) granularity preserved for the convergence dispatch's per-family analysis

**Dependencies:** Task 4.3 + Task 4.4 + Task 4.2.b

**Typed-exception triggers:** none specific

#### Task 4.6: Phase 4 close — 3-way implementation review

**Goal:** Per `feedback_implementation_review_agents`, Phase 4 close gate.

**Inputs:** All Phase 4 outputs (notebook 04 + per-(f, s, month) hybrid P&L parquet + K equilibrium per-(f, s) parquet + per-(f, s) envelope summaries + per-(f, s) regime decomposition + per-(f, s) envelope charts + (conditional) Path-A-path-replay envelope summaries + v3 handoff JSON)

**Owner:** Foreground Orchestrator dispatches; Code Reviewer (charge: notebook trios respect 4-part citation block discipline; no silent-test-pass; spec §3.B q_t pre-commitment honored throughout v3 backtest; FLAG-B6 σ_T input correctly sourced from Stage-1 realized monthly log-return-squared; K equilibrium per-(f, s) computation matches spec v1.4 §2 v3 reframe verbatim; Path-A-path-replay reuses identical Δ^(a_s) families {F1, F2, F3, F4} as Path B — no family substitution under Path A's σ-paths) + Reality Checker (charge: every hybrid P&L per-(f, s, month) value supported by underlying v1 + v2 panels per DATA_PROVENANCE.md; CORRECTIONS-γ structural-exposure framing exclusively respected through v3 hybrid envelope characterization — flag any WTP drift; RC FLAG #1 / #3 / #5 / #6 honored throughout; cross-phase Path A v3 handoff sha consistent between Phase 3 and Phase 4 consumption records; no smuggled `marco2018_dummy`-equivalent post-data adjustment in v3 calibration) + Senior Developer (charge: production-readiness — could a fresh engineer re-run the hybrid v3 pipeline with only spec v1.4 + v1 + v2 outputs + Stage-1 panel + (conditional) Path A v3 handoff?). Data Engineer + Analytics Reporter for fixes.

**Outputs:**
- Three reviewer verdicts + defect lists
- Integrated phase-close fixes
- Findings memo at `contracts/.scratch/pair-d-stage-2-B/v3/findings.md` characterizing the per-(f, s) hybrid P&L envelope and flagging convergence questions for the convergence-dispatch (separate work item)
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
- File: `contracts/.scratch/pair-d-stage-2-B/MEMO.md` with sections (v1.1 revised per CORRECTIONS-α):
  - §1 Spec sha256 pin (v1.4; quoted from this plan frontmatter)
  - §2 Stage-1 sha-pin chain (READ-ONLY through Path B; quoted verbatim)
  - §3 v0 audit summary (which a_l-side substrates confirmed, which HALT-ed; v1.4 on_chain_pins validation; mento_swap_flow_inventory.parquet ready as v2 bound-check input; a_s-side audit closed-without-substrate per SYNTHESIS.md §8.1 acknowledgment)
  - §4 v1 a_l-side empirical structural-exposure: per-substrate `r_(a_l)` + `|Δ^(a_l)|` $-notional summary; OPTIONAL LVR decomposition reference if Task 2.3.b emitted
  - §5 v2 a_s-side synthetic structural-exposure: per-(f, s) `|Δ^(a_s)|` $-notional summary; cross-family ±20% drift check verdict (PASS or `Stage2PathBSyntheticDriftBeyondTolerance` HALT-with-pivot disposition); (conditional) Path-A-path-replay summary if Task 3.C emitted
  - §6 v3 hybrid realized-+-synthetic P&L envelope per (f, s) (mean, SD, quantiles, MDD; per-(f, s) regime-conditional decomposition); K_l = K_s simulated equilibrium check residual per (f, s); (conditional) Path-A-path-replay envelope per (f) if Task 4.4 emitted
  - §7 Honest interpretation: do the empirical cash-flow shapes match the framework's qualitative predictions (`Δ^(a_l) > 0` empirical; `Δ^(a_s) < 0` synthetic per (f, s))? Sign-and-magnitude qualitative observation only — NO post-hoc goodness-of-fit threshold (anti-fishing per spec §7); cross-family spread interpretation per spec §3.B
  - §8 Convergence questions for the (separate, OUT OF SCOPE for this plan) convergence-dispatch: does Path A v3's MC envelope contain Path B v3's per-(f, s) hybrid envelope? Does the historical-path hybrid envelope agree with the Path-A-path-replay envelope (if emitted)? Do K_l = K_s residuals satisfy the equilibrium constraint within convergence-dispatch tolerance? Which (f, s) combinations are most defensible?
  - §9 Anti-fishing inheritance: RC FLAG #1 / #3 / #5 / #6 honored; structural-exposure framing exclusively per CORRECTIONS-γ + CORRECTIONS-ε; no WTP claims anywhere; spec §3.B q_t pre-commitment honored verbatim throughout; no on-chain a_s entity rehabilitation
  - §10 Stage-3 implications: explicitly OUT OF SCOPE; Path B characterizes realized history (a_l side) + hypothetical-but-pre-committed counterfactual (a_s side) and produces calibration-handoff packets; does not recommend deployment, propose LP capital sourcing, scope onboarding, or describe regulatory framing; the Abrigo-is-a_s-instantiating-product framing per SYNTHESIS.md §8.1 is recorded as Stage-3 design constraint, not Stage-2 deliverable
- File: `contracts/.scratch/pair-d-stage-2-B/gate_verdict.json` with fields (v1.1 revised per CORRECTIONS-α): `spec_sha256` (v1.4), `r_al_point`, `r_al_hac_se`, `cf_al_qualitative_match` (one of `match`, `partial_match`, `mismatch`), `v2_status` (one of `passed`, `halted_with_pivot_a`, `halted_with_pivot_b`, `halted_with_pivot_c`, `halted_with_pivot_d`, `halted_with_pivot_e`; the v1.0 `skipped` enum is RETIRED in v1.1 because synthetic generation cannot fail in the same way on-chain extraction could; the new pivot enum reflects spec §6 `Stage2PathBSyntheticDriftBeyondTolerance` 5-pivot disposition), `per_fs_cf_as_qualitative_match` (object: (f, s) → one of `match`, `partial_match`, `mismatch`), `cross_family_spread_ratio`, `cross_family_drift_within_tolerance` (bool), `per_fs_envelope_mean`, `per_fs_envelope_sd`, `per_fs_envelope_quantiles`, `per_fs_envelope_max_drawdown`, `per_fs_regime_decomposition_path`, `path_a_v3_consumed` (bool; v1.4 NEW), `path_a_v3_handoff_sha256` (string or null; v1.4 NEW), `per_f_pathA_replay_envelope_summaries_path` (string or null), `k_equilibrium_per_fs_path`, `convergence_dispatch_ready` (bool), `recommended_next_step` (one of `convergence_dispatch`, `stage3_pre_check`, `pair_d_killed_with_pivot`, `defer_v2_v3_per_pivot_e`)

**Success criteria:**
- MEMO §1-§10 complete; all sections populated
- Structural-exposure framing exclusively (NO WTP language anywhere; Reality Checker spot-check confirms)
- gate_verdict.json schema parity with above field list; all fields populated (nulls explicit if Path A v3 not consumed; nulls explicit if `Stage2PathBSyntheticDriftBeyondTolerance` HALT pivot (e) selected and v2/v3 deferred)

**Dependencies:** Phase 4 close

**Typed-exception triggers:** none specific; reviewer-flagged drift into WTP-inference language at Task 5.2 triggers HALT-disposition

#### Task 5.2: Three-way implementation review on MEMO + gate_verdict

**Goal:** Per `feedback_implementation_review_agents`, the convergence-verdict review.

**Inputs:** MEMO.md + gate_verdict.json + all Phase 0-4 outputs (reviewers may traverse upstream artifacts)

**Owner:** Foreground Orchestrator dispatches; Code Reviewer (charge: notebooks 01-04 implementations match spec v1.4 methodology; no silent-test-pass; trio-checkpoint citation discipline; FLAG-B1 / B2 / B3 / B4 / B5 / B6 / B7 / B8 partition rules correctly applied per spec §3 normatives with v1.4 substrate updates; spec §3.B q_t pre-commitment {F1, F2, F3, F4} implemented verbatim; spec §8 v1.4 NORMATIVE A → B coupling implemented with consume-when-available + cross-phase consistency) + Reality Checker (charge: every MEMO claim supported by underlying parquet / chart / DATA_PROVENANCE.md; no narrative softening of `Stage2PathBSyntheticDriftBeyondTolerance` HALT-with-pivot disposition or qualitative mismatch; CORRECTIONS-γ + CORRECTIONS-ε structural-exposure framing exclusively respected — flag any WTP drift; RC FLAG #1 / #3 / #5 / #6 honored throughout; SYNTHESIS.md §8 user-decision finding correctly reflected — Abrigo-is-a_s-instantiating-product recorded as Stage-3 design constraint not Stage-2 deliverable; q_t schedule families correctly attributed to spec §3.B pre-commitment NOT to post-data fitting) + Senior Developer (charge: production-readiness — could a fresh engineer re-run the v0 → v3 ladder with only spec v1.4 + Stage-1 panel sha + network_config + this plan + (conditional) Path A v3 handoff; convergence-dispatch readiness — does Path B v3 ship everything the convergence dispatch needs at per-(f, s) granularity).

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

## §4 — Dependency graph (text DAG; v1.1 revised per CORRECTIONS-α)

Phases are sequential at the phase-close gate; tasks within a phase are partially parallelizable per the per-task Dependencies field.

```
Phase 0:
  0.1 (sha pin verify)
    → 0.2 (working dir + notebook scaffolding)
      → 0.3 (network_config.toml)
        → 0.4 (2-wave plan verify HALT — pre-execution gate)

Phase 1 (after 0.4):
  1.1 (v1.4 allowlist + manifest + Mento V2 BiPool exchange-id pinning)
    → 1.2 (per-venue audit)
      → 1.3 (Parquet emission — Artifacts 1-3)
        → 1.3.b (mento_swap_flow_inventory.parquet — v1.4 NEW Artifact 4)
          → 1.4 (TDD test suite — extended for Artifact 4)
            → 1.5 (3-way review + validate v1.4 on_chain_pins)

Phase 2 (after 1.5; v1.4 substrate set):
  2.1 (notebook 02 scaffolding)
    → 2.2 (swap-event extraction per substrate + FLAG-B8 partition)
      → 2.3 (r_(a_l) estimation per FLAG-B1)
        → 2.3.b OPTIONAL (v1_lvr_decomposition.parquet)
        → 2.4 (CF^(a_l) series + shape-check; Mento-V3-availability slice scope)
          → 2.5 (r_al_handoff.json — B → A coupling artifact #1; PRESERVED unchanged)
            → 2.6 (3-way review)

Phase 3 (after 2.6; v1.4 SYNTHETIC GENERATION; ZERO RPC calls):
  3.A (notebook 03 scaffolding — load v0 swap-flow inventory + Stage-1 panel + spec §3.B
        + conditional Path A v3 handoff per spec §8 v1.4 NORMATIVE consume-when-available)
    → 3.B (synthetic Δ^(a_s) generation per (f, s) tuple → a_s_counterfactual.parquet
            per spec §4.0 Artifact 5; CROSS-PHASE: consumes Phase 1 v0 mento_swap_flow_inventory.parquet)
      → 3.C CONDITIONAL OPTIONAL (Path A v3 σ-path replay → a_s_counterfactual_pathA_replay.parquet
            per spec §4.0 Artifact 6; SKIP-without-prejudice if Path A v3 not delivered)
        → 3.D (cross-family ±20% drift check per spec §3.B + §6 Stage2PathBSyntheticDriftBeyondTolerance
              + monthly v1 ↔ v2 reconciliation per FLAG-B5; CROSS-PHASE: depends on 2.4)
          → 3.E (3-way review)
            ALTERNATIVE: if Stage2PathBSyntheticDriftBeyondTolerance fires + pivot (e) selected
                        (defer Path B convergence — emit v1 r_al_handoff.json only),
                        Phase 4 is BYPASSED; orchestrator routes to Phase 5

Phase 4 (after 3.E; v1.4 HYBRID realized + synthetic):
  4.1 (notebook 04 scaffolding — load v1 + v2 outputs + conditional Path A v3 handoff
        with cross-phase consistency to Phase 3 consumption record)
    → 4.2 (Π(σ_T) replay per (f, s, month) hybrid P&L)
      → 4.2.b (K_l = K_s simulated equilibrium check per (f, σ-source) cross product;
              v1.4 NEW per CORRECTIONS-α + spec §2 v3 reframe)
        → 4.3 (per-(f, s) hybrid envelope characterization + per-(f, s) regime decomposition)
          → 4.4 CONDITIONAL OPTIONAL (Path A v3 σ-distribution scenario replay → per-(f) Path-A-path-replay
                envelope; v1.4 NEW per CORRECTIONS-α + spec §8 NORMATIVE coupling;
                SKIP-without-prejudice if Path A v3 not delivered;
                CROSS-PHASE: cross-phase Path A v3 handoff sha consistency to Phase 3 Task 3.C)
            → 4.5 (v3 handoff JSON — B → A coupling artifact #2;
                  per-(f, s) granularity preserved for convergence dispatch)
              → 4.6 (3-way review)

Phase 5 (after 4.6 OR after Phase 3 pivot-(e) HALT path):
  5.1 (synthesize MEMO + gate_verdict)
    → 5.2 (3-way implementation review)
      → 5.3 (final commit + CLAUDE.md 2-wave verify)
        → 5.4 (user DISPOSITION.md)
```

**Cross-path coupling artifacts (B → A; PRESERVED from v1.0):**
- `r_al_handoff.json` emitted at Task 2.5 (v1 calibration anchor; consumed by Path A v3 if/when it dispatches; under v1.4 the `source_pool_address` field may be a list if both substrate r_(a_l)s are emitted)
- `v3_handoff.json` (Path B side; distinct from Path A → B handoff of same name) emitted at Task 4.5 (v3 per-(f, s) envelope; consumed by separate convergence-dispatch)

**A → B coupling (v1.4 NORMATIVE per CORRECTIONS-α + spec §8; consume-when-available):**
- Path A's `v3_handoff.json` (`{sigma_paths, path_source, path_count, sha256_of_path_a_v3_artifact}` per spec §8 v1.4 schema) consumed at Task 3.A (loaded into Phase 3) AND at Task 4.1 (loaded into Phase 4 for Phase 4 consumption); cross-phase consistency check at Task 4.4 (Phase 3 consumed sha must equal Phase 4 consumed sha)
- Consume-when-available semantics: non-blocking if Path A v3 has not delivered; Phase 3 produces `a_s_counterfactual.parquet` only (Task 3.C SKIP-marker); Phase 4 produces historical-path-only hybrid envelope (Task 4.4 SKIP-marker)
- Anti-fishing per spec §7: SAME §3.B-pinned q_t families {F1, F2, F3, F4} used across the Path-A-path-replay; NO substitution of family set under Path A's paths to produce a more agreeable convergence

**Convergence-dispatch is OUT OF SCOPE for this plan.** When both Path A v3 and Path B v3 deliver their respective handoff packets, the orchestrator dispatches a separate convergence comparison work item; that work item is its own plan, not a Path B task.

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
- `q_t_schedule_family_pinned` (NEW IN v1.4 per CORRECTIONS-α; descriptive string identifying the spec §3.B family + parameter spec hash; REQUIRED for v2 synthetic artifacts `a_s_counterfactual.parquet` and `a_s_counterfactual_pathA_replay.parquet` per spec v1.4 §3.A template extension; the field documents the pre-commitment string per artifact)

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

**Per-phase rate-limit + monthly-CU projection (spec §5.A; v1.1 revised per CORRECTIONS-α):**

| Phase | SQD queries (lifetime) | Alchemy CU (monthly aggregate) | Dune credits (monthly aggregate) | Public RPC | Burst-rate binding constraint |
|---|---|---|---|---|---|
| Phase 0 (scaffolding) | 0 | 0 | 0 | none | none |
| Phase 1 (v0 audit + v1.4 mento_swap_flow_inventory aggregation) | ~50-75 | <5-10K | 0-5 | none expected | sequential issuance well below caps |
| Phase 2 (v1 CF^a_l; v1.4 substrate set) | ~25-225 | ~15-50K | ~20-50 | none expected | Alchemy 25 req/sec on receipt enrichment batches |
| Phase 3 (v2 SYNTHETIC; v1.4 RETIRED RPC FOOTPRINT) | **0 (RETIRED)** | **0 (RETIRED)** | **0 (RETIRED)** | none | pure local Python compute over v0 + Stage-1 panel inputs |
| Phase 4 (v3 hybrid backtest; v1.4 NORMATIVE Path A v3 consume-when-available) | 0 | 0 | 0 | none | pure local computation; Path A v3 handoff is local-file consumed input |
| Phase 5 (memo + verdict) | 0 | 0 | 0 | none | pure local + review |
| **Aggregate Path B (v1.1 revised)** | **~75-300 (down from v1.0 ~125-345; v2 ~50-75 retired)** | **~20-60K (down from v1.0 ~30-95K; ~0.07-0.20% of 30M cap)** | **~25-55 (down from v1.0 <100; ~2% of ~2500/mo)** | **opportunistic** | **Alchemy 25 req/sec sustained** |

**v1.1 budget delta vs v1.0.** Phase 3 v2 network footprint REMOVED (~50-75 SQD queries + <30K Alchemy CU + ~5-10 Dune credits; spec §5.A v1.4 v2 retired-network-projection). Phase 1 v0 picks up the new `mento_swap_flow_inventory.parquet` aggregation: net incremental SQD load ≤ 25 additional queries (the substrate-event extraction is already in scope for `event_inventory`; the inventory aggregation is a local DuckDB rollup of the same extracted events); net incremental Alchemy CU ≤ 5K. Aggregate Path B network footprint SHRINKS by ~25-50 SQD queries + ~10-25K Alchemy CU + ~0-5 Dune credits in v1.1; comfortable headroom under all free-tier caps PRESERVED.

**Burst-rate discipline (spec §5.A binding-constraint pin):**
- All Alchemy receipt enrichment batched into ≤25-receipt request windows separated by ≥1 second sleep, regardless of total receipt budget. Concurrency cap = 1 (sequential)
- All SQD Network chunked queries issued sequentially with ≥250 ms inter-call sleep. Concurrency cap = 1 per IP
- All Dune queries sequential; pre-flight cost-estimate inspection before each execution
- Rolling-window monitoring: executor MUST log `req_per_sec` and `cu_per_sec` to a local audit log per data source per minute (`burst_rate_log.csv` per phase); spike >80% of either cap surfaces a warning and pauses next batch ≥5 sec
- Exceedance triggers `Stage2PathBAlchemyFreeTierRateLimitExceeded` typed exception with disposition: pause, reduce concurrency / chunk size, retry; if exceedance recurs after retry, HALT-and-flag

**Auto-pivot ban:** auto-pivot through SQD → The Graph → Alchemy free → Dune → public-RPC fallback (spec §5.A degradation Steps 1-4) is permitted (all free-tier; tooling fallback, not result-shaping). Auto-pivot to Step 5 (paid Subsquid Cloud OR paid Alchemy tier OR Dune Analyst OR paid Eigenphi API) is **anti-fishing-banned** and requires explicit user adjudication via typed-exception HALT.

## §7 — Cross-path coordination (v1.1 revised per CORRECTIONS-α + spec §8 v1.4 NORMATIVE A → B promotion)

Per spec v1.0-v1.3 §8 + FLAG-B9, paths A and B were DEFAULT INDEPENDENT at all rungs. Spec v1.4 §8 PROMOTES the A → B v3 σ-distribution coupling FROM OPTIONAL TO NORMATIVE per CORRECTIONS-ε; this plan reflects that promotion. The B → A coupling emissions are PRESERVED unchanged in topology.

**B → A coupling emission contracts (this plan emits; Path A v3 consumes if/when it dispatches; PRESERVED FROM v1.0):**

- **Phase 2 emission:** `r_al_handoff.json` per FLAG-B9 schema with fields:
  - `r_al_point` (float; OLS point estimate; under v1.4 may be a list if both Mento V3 USDm/cUSD primary AND Mento V2 BiPool USDm/COPm secondary substrate r_(a_l)s are emitted)
  - `r_al_hac_se` (float; Newey-West HAC standard error; same list-or-scalar treatment as `r_al_point`)
  - `sample_n` (int; daily-bin count)
  - `sample_window` (string; ISO-8601 date range, e.g., `"2023-08-15/2026-02-28"`)
  - `source_pool_address` (string OR list of strings under v1.4; 0x-prefixed checksummed)
  - `sha256_of_input_panel` (string; sha256 of the per-substrate partitioned swap parquet)
  - Path A v3 consumes this packet as the calibration anchor for its stochastic-σ MC empirical-calibrated variant (per Path A spec §12 + FLAG-F4 baseline pin); if Path B v1 has not landed by Path A v3 dispatch time, Path A v3 proceeds with GBM baseline + escalations only.

- **Phase 4 emission:** `v3_handoff.json` (Path B side; distinct from Path A → B handoff of same name; convergence-dispatch consumption) with fields per Task 4.5:
  - `r_al_point`, `r_al_hac_se` (carried forward from v1)
  - `per_fs_envelope_summaries` (object: (f, s) → envelope summary; PRESERVED structural-exposure framing — NOT WTP)
  - `per_f_pathA_replay_envelope_summaries` (object: f → Path-A-path-replay envelope summary; null if Path A v3 not consumed)
  - `path_a_v3_consumed: bool`
  - `path_a_v3_handoff_sha256` (null if not consumed)
  - `k_equilibrium_per_fs` (object: (f, s) → K_l, K_s, K_l_minus_K_s residual)
  - `sample_window`, `source_pool_addresses`, `sha256_of_v1_handoff`, `stage1_panel_sha256`
  - The convergence-dispatch (separate work item OUT OF SCOPE for this plan) consumes this packet alongside Path A v3's MC envelope JSON to compute the convergence comparison; per-(f, s) granularity preserved for the convergence dispatch's per-family analysis.

**A → B coupling at Phase 3 + Phase 4 (v1.4 NORMATIVE per CORRECTIONS-α; consume-when-available):**

- **Path A's `v3_handoff.json`** consumed at Tasks 3.A + 4.1 (loaded into Phase 3 Task 3.C OPTIONAL Path-A-path-replay artifact + Phase 4 Task 4.4 OPTIONAL Path-A-path-replay envelope). Schema per spec §8 v1.4: `{sigma_paths: float64[N_paths × T_steps], path_source: "path_a_v3_gbm_mc" or evolving tag, path_count: int, sha256_of_path_a_v3_artifact: string}`.
- **Consume-when-available semantics**: non-blocking if Path A v3 has not delivered at Phase 3 / Phase 4 entry. Phase 3 produces `a_s_counterfactual.parquet` only (Task 3.C SKIP-marker memo `pathA_replay_skipped.md` recording the SKIP reason); Phase 4 produces historical-path-only hybrid envelope (Task 4.4 SKIP-marker memo `pathA_replay_v3_skipped.md`). The historical-path-only fallback is the spec-pinned default per spec §8 v1.4.
- **Cross-phase consistency check** at Task 4.4: Phase 3 consumed Path A v3 handoff sha must equal Phase 4 consumed sha; mismatch is HALT-and-surface (potential cross-path provenance drift).
- **Anti-fishing** per spec §7: SAME §3.B-pinned q_t families {F1, F2, F3, F4} used across both historical-path and Path-A-path-replay; NO substitution of family set under Path A's σ-paths to produce a more agreeable convergence; this is recorded in Phase 3 + Phase 4 trio-checkpoint citation blocks.
- **No additional A → B coupling permitted** beyond the v3_handoff.json σ-path matrix consumption: Path B v3 does NOT consume Path A's K_l calibration, position-geometry choices, or v3 envelope JSON at any other task in this plan. Cross-path reconciliation (does Path A's harness-realized CF^(a_l) match Path B's on-chain-realized CF^(a_l) within tolerance?) is the convergence-dispatch's job, NOT Path B's job.

**Convergence-dispatch is OUT OF SCOPE for this plan.** When both Path A v3 and Path B v3 deliver their respective handoff packets, the orchestrator dispatches a separate convergence comparison work item; that work item is its own plan, not a Path B task.

## §8 — Self-review checklist (run by orchestrator before commit of THIS plan; v1.1 revised per CORRECTIONS-α)

- **Spec coverage (v1.4):** does every spec §1-§9 normative requirement map to a task here?
  - §1 framing-definition (structural-exposure; v1.4 reaffirms — synthetic Δ^(a_s) is structural-exposure characterization NOT WTP) → §1 Overview + repeated reminders in every Phase 2-5 task description; §2 Phase decomposition Phase 5 explicit deliverable
  - §2 internal ladder (v0/v1/v2/v3; v1.4 v2 reframed to synthetic generation; v3 reframed to hybrid realized-+-synthetic) → Phases 1/2/3/4 (1:1 mapping with v1.4 reframes reflected in Phase 3 + Phase 4 task substance)
  - §3 inputs (Stage-1 sha pins; on-chain pre-pins for a_l side; FLAG-B1/B2/B3/B4/B5/B6/B7/B8/B9 with v1.4 substrate updates) → all FLAGs cited in per-task Inputs fields; Stage-1 sha pins frozen in plan frontmatter; on_chain_pins overhauled in plan frontmatter per spec v1.4 §3
  - §3.A provenance discipline (extended in v1.4 with `q_t_schedule_family_pinned` for v2 synthetic artifacts) → §5 dedicated section + per-task Outputs fields cite DATA_PROVENANCE.md; v1.1 §5 records the v1.4 extension
  - §3.B q_t schedule family pre-commitment (NEW IN v1.4 — F1, F2, F3, F4 + ε_t = 0.01 + (X/Y)̄_t trailing-4-week + 20% drift tolerance + B_T = 1 baseline) → cited verbatim in Tasks 3.A + 3.B + 3.D Inputs fields; NOT redefined in plan
  - §4 outputs (v1.4-additive: Artifacts 4 + 5 + 6) → per-phase per-task Outputs fields enumerate all spec §4 deliverables including Artifacts 4 (Phase 1 Task 1.3.b), 5 (Phase 3 Task 3.B), 6 (Phase 3 Task 3.C OPTIONAL + Phase 4 Task 4.4 OPTIONAL)
  - §4.0 schema → Tasks 1.3 + 1.3.b (Artifact 4 NEW IN v1.4) + 1.4 (TDD extended) + 3.B (Artifact 5 NEW IN v1.4) + 3.C (Artifact 6 OPTIONAL NEW IN v1.4)
  - §5 + §5.A free-tier-only tooling stack (PRESERVED through v1.4; v2 RPC footprint RETIRED) → §6 dedicated section + Task 0.3 network_config.toml; §6 budget table revised in v1.1 to reflect v2 retirement
  - §6 typed exceptions (10 enumerated in v1.0-v1.3; v1.4 DEPRECATES `Stage2PathBASOnChainSignalAbsent` + ADDS `Stage2PathBSyntheticDriftBeyondTolerance`) → per-task Typed-exception triggers fields; Phase 1 Task 1.1 records `Stage2PathBASOnChainSignalAbsent` MUST NOT be raised under v1.1; Task 3.D records `Stage2PathBSyntheticDriftBeyondTolerance` as central v2 HALT mechanism
  - §7 anti-fishing posture (v1.4 ADDS q_t pre-commitment + 20% drift tolerance + on-chain a_s entity rehabilitation ban) → §1 Overview + repeated CORRECTIONS-γ + CORRECTIONS-ε reminders + Task 2.6 / 3.E / 4.6 / 5.2 Reality Checker charges; §6 records `q_t schedule families pre-committed in spec text BEFORE any v2 generation` invariant
  - §8 convergence with Path A (v1.4 PROMOTES A → B v3 σ-distribution coupling FROM OPTIONAL TO NORMATIVE) → §7 dedicated section in v1.1 reflecting promotion + Tasks 3.A + 3.C + 4.1 + 4.4 implementing consume-when-available semantics
  - §9 self-review checklist → spec-side, mirrored in this plan §8

- **Placeholder scan:** zero "TBD" / "TODO" / "fill in details" / "similar to Task N" / "implement appropriate handling" — verify by full-text grep before commit.

- **Code-agnosticism:** zero executable code blocks per `feedback_no_code_in_specs_or_plans`. Schema definitions, address pins, mathematical formulas (in inline notation), configuration parameters (in TOML/YAML/JSON form), and dependency lists are permitted; actual Python / SQL / JavaScript implementation is not.

- **Specialist coverage:** every task names an owner per `feedback_specialized_agents_per_task`. Distribution: Foreground Orchestrator (verification + dispatch + final commit); Data Engineer (extraction + parquet emission + tests + scaffolding); Analytics Reporter (notebook authorship + memo authorship + trio HALT discipline); Code Reviewer + Reality Checker + Senior Developer (per-phase 3-way review); Workflow Architect (Wave 2 plan-verification + CLAUDE.md update Wave 2).

- **Anti-fishing discipline:** spec sha256 pin frozen in plan frontmatter (v1.4 sha `fcebc95f...`); Stage-1 sha-pin chain READ-ONLY through Path B; no auto-pivot to paid services; auto-pivot through free-tier degradation Steps 1-4 permitted with explicit logging; HALT-disposition path per `feedback_pathological_halt_anti_fishing_checkpoint` for every typed exception; no post-hoc threshold tuning (including no tuning of spec §3.B 20% drift tolerance to force HALT or absorb sweep); no curve-fitting to frame results; no causal-channel claims for BPO mechanism (RC FLAG #1); no β re-litigation of Stage-1 result; no Stage-3 deployment claims; structural-exposure framing exclusively per CORRECTIONS-γ + CORRECTIONS-ε — NO WTP-inference language anywhere in plan; spec §3.B q_t schedule families {F1, F2, F3, F4} pre-committed and may NOT be tightened, expanded, or re-parameterized post-data; no on-chain a_s entity rehabilitation per spec §7 v1.4 (re-introducing speculative a_s placeholder requires three independent research-track confirmations equivalent to SYNTHESIS.md §2 4-track standard PLUS user adjudication).

- **2-wave doc verification:** plan v1.0 write triggered RC + Workflow Architect (Task 0.4 v1.0 — passed); plan v1.1 write triggers RC + Workflow Architect re-dispatch per `feedback_two_wave_doc_verification` charging against CORRECTIONS-α scope; spec v1.4 frontmatter is pre-pinned (v1.0 plan's Task 1.5 spec frontmatter edit semantics is RETIRED in v1.1); CLAUDE.md update triggers RC + Workflow Architect (Task 5.3).

- **3-way implementation review per phase:** Code Reviewer + Reality Checker + Senior Developer (per `feedback_implementation_review_agents`; Tech Writer NOT used at implementation reviews) — Phase 1 close (Task 1.5), Phase 2 close (Task 2.6), Phase 3 close (Task 3.E; renumbered from v1.0's Task 3.6), Phase 4 close (Task 4.6; renumbered from v1.0's Task 4.5), Phase 5 (Task 5.2).

- **Real data over mocks:** Per `feedback_real_data_over_mocks`, every test uses real on-chain data via SQD / Alchemy / public RPC; mocks are reserved exclusively for HTTP errors that cannot be reproduced (e.g., simulating a 429 rate-limit response that Alchemy is not currently issuing).

- **Strict TDD:** Per `feedback_strict_tdd`, no implementation lands without a failing test first. Phase 1 has explicit TDD task (1.4); Phase 2-4 notebook trios have implicit TDD via the trio-checkpoint structure (the `interpretation` markdown asserts what the `code` cell should produce; if `code` does not produce it, the trio HALTs and re-dispatches).

- **Push to dev not upstream:** Per `feedback_push_origin_not_upstream`, all commits push to `origin` (JMSBPP), NEVER `upstream` (wvs-finance). Plan frontmatter `push_target: dev` reflects this.

- **No code in plan:** verified — equation notation in §3 is methodology specification (LaTeX-style inline `Π(σ_T) ≈ K̂·σ_T`); SQL query templates in `text` blocks are permitted but not used in this plan (no pre-formed query templates needed — executor discretion bounded by spec §3 normatives); actual Python BANNED.

- **Deliverable framing:** structural-exposure characterization throughout per CORRECTIONS-γ — verified at every Phase 2-5 task description; "demand-side" preserved only as economic-leg terminology naming the a_s leg of the framework decomposition (per spec §1 framing-definition + spec v1.3 §1 framing rewrite + spec §4 v2 output bullet simplification).

## §9 — Plan validation gates (v1.1 revised per CORRECTIONS-α)

**Pre-execution (before Phase 0; v1.1 RE-DISPATCH per `feedback_two_wave_doc_verification`):** v1.0 passed 2-wave verification at Task 0.4; v1.1 plan write under CORRECTIONS-α RE-DISPATCHES 2-wave verification charging against the CORRECTIONS-α scope:
- Wave 1: Reality Checker (charge: synthetic-counterfactual framing fidelity per spec v1.4 §1; q_t schedule pre-commitment honored verbatim from spec §3.B; A → B v3_handoff.json consume-when-available semantics correct; no on-chain a_s entity rehabilitation; free-tier-only PRESERVED; structural-exposure framing exclusively preserved through v1.4 reframe; SYNTHESIS.md §8 user-decision finding correctly reflected)
- Wave 2: Workflow Architect (charge: Phase 2/3/4 task ordering reflects v1.4 reframe; Phase 1 v0 mento_swap_flow_inventory artifact wired into Phase 3 inputs; Phase 4 consume-when-available coupling correct; specialist coverage maintained; per-phase 3-way review hooks PRESERVED; trio-checkpoint discipline preserved on notebooks 02/03/04)

Both verifiers must return PASS or PASS-WITH-REVISIONS before Phase 0 execution resumes. BLOCK-severity defect from either wave HALTS commit and re-dispatches. v1.0's prior PASS verdicts are recorded in frontmatter `plan_verifier_v1_wave1` + `plan_verifier_v1_wave2` fields; v1.1 verdicts pending in `plan_verifier_v1_1_wave1` + `plan_verifier_v1_1_wave2` fields.

**Per-phase (Phase 1-4 close; PRESERVED FROM v1.0):** Each phase concludes with 3-way implementation review per `feedback_implementation_review_agents`:
- Code Reviewer (charge: implementation matches spec v1.4 methodology; no silent-test-pass per `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons` 5-instance catalogue; trio-checkpoint citation discipline; FLAG partition rules correctly applied; spec §3.B q_t pre-commitment honored verbatim in Phase 3; spec §8 v1.4 NORMATIVE A → B coupling implemented correctly in Phase 3 + Phase 4)
- Reality Checker (charge: every output supported by underlying data per DATA_PROVENANCE.md; no narrative softening; CORRECTIONS-γ + CORRECTIONS-ε structural-exposure framing exclusively; RC FLAG #1 / #3 / #5 / #6 honored; no on-chain a_s entity rehabilitation; q_t schedule families correctly attributed to spec §3.B pre-commitment NOT to post-data fitting)
- Senior Developer (charge: production-readiness — could a fresh engineer re-run the phase with only spec v1.4 + upstream phase outputs + network_config + (conditional) Path A v3 handoff?)

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
