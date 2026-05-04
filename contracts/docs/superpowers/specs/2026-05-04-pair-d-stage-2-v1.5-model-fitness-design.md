---
spec_path: pair-d-stage-2-v1.5-model-fitness-design
spec_version: v1.0 (initial design via brainstorming skill)
spec_author: orchestrator + user co-design 2026-05-04
spec_sha256: <to-be-pinned-after-recompute>
parent_spec_pin: 2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md (v1.4, sha fcebc95f923e1b55fbf2eaa22239b00bbde4a9f35bb031e8f32d090a4fb80d95)
parent_plan_pin: 2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md (v1.1, sha 7e2f43c211a314475c3fc2ef5890c268c7216efa55b0b7a9d2c8e5d8d95bca6b)
synthesis_memo_pin: contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/SYNTHESIS.md (commit e25131cd2)
cop_corridor_research_pin: contracts/.scratch/path-b-stage-2/phase-1/cop_corridor_aggregate_research/discovery.md (commit cdc844721)
gate_b1_review_pin: contracts/.scratch/path-b-stage-2/phase-1/gate_b1_review.md (commit b206b5cdc)
budget_pin: free_tier_only (preserved from CORRECTIONS-δ)
verifier_v1_0_wave1: pending (Reality Checker — 2-wave verification per `feedback_two_wave_doc_verification`)
verifier_v1_0_wave2: pending (Workflow Architect — 2-wave verification per `feedback_two_wave_doc_verification`)
---

# Pair D Stage-2 — v1.5 Empirical Model-Fitness Gate Design

## §1. Overview and scope

This design adds a hierarchical 3-step empirical model-fitness gate (v1.5) to the Path B implementation between v1 (CF^(a_l) reconstruction) and v2 (synthetic CF^(a_s) generation). v1.5 calibrates parameters of the simplest CPO model AND tests whether the model survives contact with observed COP-corridor reality before any synthetic generation proceeds.

**Goals**:
1. **Stage-2 v3 backtest fidelity** (goal a) — sharpen calibration of r_(a_l), q_t-family-fit, and K-equilibrium target so v3 hybrid backtest produces defensible numbers
2. **Model fitness check** (goal c) — test whether DRAFT.md's simplest-model assumptions (Π convexity, q_t shape, K equilibrium magnitude) actually fit observed COP-corridor reality; if assumptions fail, route to CORRECTIONS-block to re-derive rather than calibrate within a wrong framework

**Non-goals** (deferred):
- Goal (b) Stage-3 deployment priors — v1.5c surfaces equilibrium-feasibility implications but does not produce deployment economics; that's a Stage-3 design memo
- Goal (ii) a_l functional form testing — accepted per LVR distinction (LP NET = short variance; v1 measures gross fee component); not retested in v1.5
- Goal (v) small-ε perturbation testing — accepted; ε_t = 0.01 default per spec §3.B is in effect

**Hierarchy** (Approach 3 from brainstorming):
v1.5 tests assumptions in causal order — **payoff convexity first** (most fundamental; if wrong, everything else is moot), then **q_t schedule shape** (within accepted convexity), then **K equilibrium magnitude** (within accepted convexity + accepted schedule).

**Execution priority (per user direction 2026-05-04)**:
**Data-collection-first**. The most important deliverable is maximum aggregate data from all COP-corridor sources (CORRECTIONS-ζ substrate scope expansion). The 3-test methodology (v1.5a/b/c) operates on top of this aggregate and is **subject to tweaks based on what the data reveals** — including potential extension of the candidate functional-form set (v1.5a), q_t family set (v1.5b), or R-verdict thresholds (v1.5c). Tweaks happen via CORRECTIONS-block discipline (pre-pinned thresholds become updated thresholds with explicit re-verification), NOT silent threshold drift. Anti-fishing invariants in §6.1 hold even under tweaking — they are the discipline by which tweaks happen, not constraints that prevent them.

## §2. Architecture — v1.5 sequence

```text
Phase 1 done                                                   v2 dispatch unblocked iff:
   │                                                              v1.5a verdict ≠ FAIL
   ├─> CORRECTIONS-ζ substrate scope expansion ──┐               v1.5b verdict ≠ FAIL
   │                                              │
   ├─> COP-corridor aggregate panel build ────────┤               v3 dispatch unblocked iff:
   │                                              │               v1.5c verdict ≠ INFEASIBLE
   ├─> v1 r_(a_l) reconstruction (Phase 2) ───────┤
   │                       │                      │
   │                       │                      │
   │                       │                      ├─> v1.5a Π convexity ──┐
   │                       │                      ├─> v1.5b q_t fit ──────┤
   │                       └──────────────────────────> v1.5c K equilibrium ┤
   │                                                                       │
   v2 synthetic Δ^(a_s) (gated by v1.5a + v1.5b) <────────────────────────┤
                       │                                                   │
                       └─> v3 hybrid backtest <───────────────────────────┘
```

**Parallelism**: v1.5a and v1.5b have no r_(a_l) dependency and run in parallel with v1. v1.5c needs v1's `r_al_handoff.json` emission and runs after v1.

**Inputs to v1.5** (all free-tier observable; sourced from prior Phase 1 outputs + CORRECTIONS-ζ substrate scope expansion + Stage-1 Banrep TRM):
- `audit_summary.parquet` + `mento_swap_flow_inventory.parquet` from Phase 1
- COP-corridor aggregate substrate panel — NEW artifact built post-CORRECTIONS-ζ (Mento V2 COPm + Minteo Celo + Minteo Polygon + Num nCOP Polygon + Wenia COPW Polygon + Daily DLYCOP Polygon/BSC + Minteo Solana)
- v1 emission `r_al_handoff.json` (consumed by v1.5c only)
- Stage-1 panel sha-pin chain (READ-ONLY)

**Outputs from v1.5**:
- Per-step parquet panels + findings memos (per §6 below)
- Aggregate `v1_5_calibration.parquet` — cross-step calibration anchors for v2/v3 input
- Aggregate `v1_5_findings.md` — narrative interpretation, Stage-3 implications

## §3. v1.5a — Π convexity test (Step 1, the most fundamental gate)

**Question**: Does observed (σ_realized, aggregate-COP-corridor-flow-volatility) follow K·√σ_T per DRAFT.md derivation, or a different convexity?

**Inputs**:
- σ_realized weekly: Banrep TRM rolling-4-week realized vol of log(COP/USD) returns
- σ-anchor cross-validation: Mento V2 BiPool USDm/COPm spot σ, Uniswap V3 Polygon Minteo/USDC spot σ
- Aggregate-flow-volatility: per-week stddev of weighted substrate net-position changes (CORRECTIONS-ζ aggregation methodology, audit-block-frozen weights)
- Sample window: 2023-08 → 2026-02 (135 weeks)

**Methodology**:
1. Build per-week panel: `(week, σ_realized_weekly, agg_flow_vol_weekly, distinct_holders, transfer_count)`
2. Fit 5 candidate functional forms via OLS+HAC SE:
   - F_a: `agg_flow_vol = a · √σ + b` (DRAFT.md hypothesis under test)
   - F_b: `agg_flow_vol = a · σ + b` (linear)
   - F_c: `agg_flow_vol = a · σ² + b` (quadratic / GARCH-flavored)
   - F_d: `agg_flow_vol = a · log(σ) + b` (log-convexity)
   - F_e: piecewise with regime break (e.g., quiet vs stress)
3. AIC/BIC model comparison; bootstrap 95% CI on slope `a`; residual Durbin-Watson autocorrelation test
4. Sensitivity sweep across σ-anchor sources (Banrep TRM vs Mento spot vs Polygon spot)

**Pre-pinned acceptance thresholds** (spec-locked, no post-data tuning):
- **PASS** for F_a (√σ): ΔAIC ≤ 2 vs best-fitting form, slope significant (t > 2), DW > 1.5
- **MARGINAL**: ΔAIC ∈ (2, 5]
- **FAIL**: ΔAIC > 5

**Outputs**:
- `v1_5a_pi_convexity_panel.parquet` (~135 rows × ~10 columns)
- `v1_5a_pi_convexity_findings.md` (per-form fit table + bootstrap CIs + residual diagnostics + verdict)

**HALT routing per outcome**:
- **PASS** → proceed to v1.5b; v3 calibration uses K·√σ_T per spec
- **MARGINAL** → proceed to v1.5b; v3 emits BOTH `Π(σ_T)` under √σ AND best-fit alternative for sensitivity
- **FAIL** → HALT v2 dispatch; trigger CORRECTIONS-η on parent spec re-deriving Π under empirical functional form; 2-wave verify; re-dispatch v2 under corrected form

## §4. v1.5b — q_t empirical fit test (Step 2, schedule family validation)

**Question**: Do the 4 pre-pinned q_t families (F1 monthly / F2 weekly / F3 front-loaded / F4 back-loaded) capture observed user behavior, or are additional families needed?

**Inputs**:
- Per-substrate non_lp_user Transfer event panel (post-FLAG-B8 partition) across CORRECTIONS-ζ scope
- Per-event row: `(timestamp_utc, from_address, to_address, amount_usd_anchored, substrate, partition)`
- Sample window: 2023-08 → 2026-02

**Methodology**:
1. **Cohort filter**: addresses with ≥3 non_lp_user transfers in window (excludes one-shot accounts; pre-pinned)
2. **Per-cohort feature extraction**: inter-arrival time (median, IQR), transfer-size CV, calendar phase (day-of-month + day-of-week histograms), active duration
3. **Clustering**: K-means on (inter-arrival, size-CV, calendar-phase) feature space; K-range pre-pinned 4–8; silhouette validation
4. **Cluster-to-F mapping** per pre-pinned criteria:
   - F1 monthly: median inter-arrival ≈ 30d, low size-CV, end-of-month skew
   - F2 weekly: median inter-arrival ≈ 7d, low size-CV, weekday skew
   - F3 front-loaded: 2-active-period cluster, first-active-period < 2 weeks
   - F4 back-loaded: 2-active-period cluster, last-active-period > T-2 weeks
5. **Coverage analysis**: fraction of non_lp_user transfer notional captured by F1–F4 clusters
6. **Residual characterization**: clusters not matching F1–F4 → describe as candidate F5/F6 (quarterly tax pattern, bi-weekly payroll, year-end seasonal spike, Poisson arrival)

**Pre-pinned acceptance thresholds**:
- **PASS**: ≥80% of non_lp_user transfer notional captured by F1–F4 clusters
- **MARGINAL**: 60–80% captured (residual flagged for v3 sensitivity)
- **FAIL**: <60% captured

**Outputs**:
- `v1_5b_cohort_features.parquet` (per-address feature panel)
- `v1_5b_cluster_summary.parquet` (per-cluster statistics + F-mapping)
- `v1_5b_q_t_findings.md` (capture fraction, residual cluster characterization, recommended F5/F6 if any)

**HALT routing per outcome**:
- **PASS** → v2 generates synthetic Δ^(a_s) over F1–F4 per spec §3.B (no extension)
- **MARGINAL** → CORRECTIONS-block on parent spec §3.B extending pre-pinned set with empirically-motivated F5 (and possibly F6); 2-wave verify the spec extension; v2 generates over expanded set; v3 sensitivity reports both narrow-set and extended-set
- **FAIL** → HALT v2 dispatch; spec §3.B q_t pre-commitment is fundamentally incomplete; CORRECTIONS-η-equivalent overhaul of family set required

## §5. v1.5c — K equilibrium magnitude test (Step 3, equilibrium feasibility)

**Question**: Is the K_l = K_s magnitude condition empirically achievable at observed COP-corridor scale? Equivalently, does `r_(a_l) · S_l ≈ S_s` hold?

**Inputs**:
- v1 emission `r_al_handoff.json` (r_(a_l) point + HAC SE)
- COP-corridor aggregate panel: S_s computation (Σ_substrates non_lp_user_balance × USD_anchor at audit_block)
- LP-side data: Mento V2 BiPool USDm/COPm reserves (BiPoolManager state) + post-CORRECTIONS-ζ Polygon Uniswap V3 Minteo/USDC LP positions + nCOP/USDC LP positions
- Stage-1 Banrep TRM (USD anchoring)

**Methodology**:
1. Compute **S_s empirical**: Σ_substrates (non_lp_user_balance × USD_anchor) at audit_block
2. Compute **S_l empirical**: Σ_COP_corridor_LPs (USDm-side balance × USD_anchor) at audit_block
3. Compute **r_(a_l) · S_l** using v1 emission
4. Compute **R = r_(a_l) · S_l / S_s**
5. Bootstrap CI on R via week-subsampling (135 weeks → 1000 bootstrap resamples)
6. Per-substrate exclusion sensitivity (drop substrate-i, recompute R)
7. Cross-corridor sanity: compute MXN-corridor R using MXNB/Juno LP data on Arbitrum

**Pre-pinned verdict thresholds**:
- **BALANCED** (0.5 ≤ R ≤ 2.0): structural feasibility; v3 hybrid backtest proceeds with K = ½·(K_l + K_s) as empirical target
- **DEMAND-DOMINATED** (0.1 ≤ R < 0.5): hedge demand >> LP supply; high-premium scenario; Stage-3 LP recruitment load-bearing
- **SUPPLY-DOMINATED** (2.0 < R ≤ 10): LP capacity >> demand; low-premium scenario; Stage-3 a_s vault scaling load-bearing
- **INFEASIBLE** (R < 0.1 or R > 10): extreme imbalance; CPO viability questionable at COP scale

**Outputs**:
- `v1_5c_equilibrium_panel.parquet` (per-substrate S_s + S_l components, per-substrate-exclusion sensitivity coefficients)
- `v1_5c_equilibrium_findings.md` (R point + bootstrap CI + sensitivity table + cross-corridor comparison + Stage-3 implication)

**HALT routing per outcome**:
- **BALANCED** → v3 proceeds with K-equilibrium as empirical target
- **DEMAND-DOMINATED / SUPPLY-DOMINATED** → v3 proceeds; MEMO §10 documents Stage-3 design constraint; v3 sensitivity under both observed-imbalance and target-balanced scenarios
- **INFEASIBLE** → HALT v3 dispatch; product-design re-evaluation memo; potentially cross-corridor pivot OR Stage-3 deployment scaling assumption revision

## §6. Cross-cutting concerns

### §6.1 Anti-fishing pre-pinned invariants

| Invariant | Specification |
|-----------|---------------|
| 5 candidate Π-convexity forms (F_a–F_e) | Pre-pinned in spec — no post-data form selection |
| AIC delta thresholds (2 / 5) | Pre-pinned for v1.5a |
| q_t cohort filter (≥3 transfers) and K-range (4–8) | Pre-pinned for v1.5b |
| q_t capture-fraction thresholds (80% / 60%) | Pre-pinned for v1.5b |
| R-ratio thresholds (0.5 / 2.0 / 0.1 / 10) | Pre-pinned for v1.5c |
| Bootstrap CI mandatory at all 3 steps | All sub-tests run unconditionally |
| Per-substrate exclusion sensitivity at v1.5c | Mandatory robustness check |
| All 5 Π-forms get fitted regardless of which "wins" | No early-termination optimization (Phase 1 max_chunks bug lesson) |
| Each test's HALT routes to CORRECTIONS-block | Never silent threshold-tuning or auto-pivot |
| CORRECTIONS-ζ substrate weights audit-block-frozen | v1.5 cannot recompute weights mid-test |

### §6.2 Output format conventions

- Per-step: `v1_5{a,b,c}_<topic>_panel.parquet` + `v1_5{a,b,c}_<topic>_findings.md` + per-step verdict-as-JSON for orchestrator consumption
- Aggregate: `v1_5_calibration.parquet` (cross-step calibration anchors for v2/v3 input)
- Aggregate: `v1_5_findings.md` (~3000-5000 word memo: per-test interpretation + cross-test consistency + Stage-3 design implications)
- Per-artifact provenance entry per parent spec §3.A 8-field schema

### §6.3 DuckDB integration

Parquet remains canonical. Optional view-only DuckDB at `contracts/.scratch/pair-d-stage-2-B/v0/v1_5_calibration.duckdb` IF v3 hybrid backtest needs efficient cross-test joins — defer to v3 dispatch decision per `project_duckdb_xd_weekly_state_post_rev531`.

### §6.4 Failure cascade handling

| Failure | Handling |
|---------|----------|
| v1.5a FAIL | HALT v2; CORRECTIONS-η on Π form; re-derive K_l = K_s identity under empirical convexity; 2-wave verify; re-dispatch v2 |
| v1.5b FAIL | HALT v2; CORRECTIONS-block on parent spec §3.B family set; 2-wave verify; re-dispatch v2 over expanded set |
| v1.5c INFEASIBLE | HALT v3; product-design re-evaluation memo |
| v1.5b MARGINAL with residual cluster ≥ 20% | CORRECTIONS-block extending family set BEFORE v2 (don't proceed with known incomplete coverage) |

## §7. Spec / plan revision footprint

This design is implemented via:

### §7.1 CLAUDE.md framework section update (~30-40 lines)
Rev-5.3.5 "Mento-native ONLY" reversal corrigendum; substrate scope expansion to "aggregate COP-corridor"; references to SYNTHESIS.md-style discovery findings + aggregation methodology.

### §7.2 Parent spec v1.4 → v1.5 (CORRECTIONS-ζ) (~120-150 lines)
- Frontmatter `on_chain_pins` additions ×6 (Minteo Polygon, Num nCOP Polygon, Wenia COPW Polygon, Daily DLYCOP Polygon + BSC, Minteo Solana)
- §1 prose: substrate scope expansion + v1.5 model-fitness-gate framing
- §3 v1 substrate update: multi-substrate r_(a_l) aggregation
- **NEW §3.C** v1.5 Empirical Model-Fitness Gate methodology (or reference to this design + sub-plan)
- §4.0 schema additions for v1.5 calibration panels
- §6 typed exceptions: `Stage2PathBPiConvexityRejected` (v1.5a FAIL), `Stage2PathBQtFamilyCoverageInsufficient` (v1.5b FAIL), `Stage2PathBKEquilibriumInfeasible` (v1.5c INFEASIBLE), `Stage2PathBAggregateSubstrateThinness` (CORRECTIONS-ζ floor not met)

### §7.3 Parent plan v1.1 → v1.2 (CORRECTIONS-β') main-plan pointer (~40-60 lines)
- Phase 2.5 placeholder (between Phase 2 v1 and Phase 3 v2) referencing sub-plan
- Updated Phase 2/3 dependencies: Phase 3 now blocks on Gate B1.5 PASS
- Pre-existing Phase 2/3 tasks unchanged in substance

### §7.4 NEW sub-plan (~600-800 lines, ~22-25 tasks)
`contracts/docs/superpowers/sub-plans/2026-05-04-pair-d-stage-2-path-b-v1.5-model-fitness-subplan.md`

Sub-phases:
- Substrate-scope expansion under CORRECTIONS-ζ (~6-8 tasks; allowlist update + audit re-run + Parquet emission for new substrates + provenance)
- v1.5a Π convexity (~5 tasks)
- v1.5b q_t empirical fit (~5 tasks)
- v1.5c K equilibrium magnitude (~5 tasks)
- Gate B1.5 3-way review (1 dispatch task)

### §7.5 Verification gates (per `feedback_two_wave_doc_verification`)
- CLAUDE.md framework update: RC + WA in parallel
- Spec v1.5 CORRECTIONS-ζ: RC + WA in parallel
- Plan v1.2 CORRECTIONS-β' main-plan pointer: RC + WA in parallel
- Sub-plan v1.5: RC + WA in parallel (separate dispatch from main plan)

### §7.6 Sequencing — data-first, model-tweaking second

1. CLAUDE.md framework update → 2-wave verify → commit
2. Parent spec v1.5 CORRECTIONS-ζ → 2-wave verify → commit → PR + merge
3. Sub-plan v1.5 + main-plan pointer (parallel authoring) → 2-wave verify each → commit → PR + merge
4. **PRIORITY-1 EXECUTION: substrate-scope expansion audits** — exhaustively collect Mento V2 COPm + Minteo Celo + Minteo Polygon + Num nCOP + Wenia COPW + Daily DLYCOP + Minteo Solana data; build aggregate panel; verify aggregation methodology; emit Parquet artifacts. This is the load-bearing data-collection phase per user direction 2026-05-04.
5. **PRIORITY-2 EXECUTION: v1.5 test execution** — only after the aggregate panel is complete: v1.5a + v1.5b in parallel; v1.5c after v1 complete; Gate B1.5 close.
6. **Model tweaking based on data findings** — if v1.5a/b/c reveal patterns motivating threshold adjustments or candidate-set extensions, route via CORRECTIONS-block discipline (re-verify, re-pin, re-execute) — NOT silent threshold drift.

## §8. Self-review checklist

- [ ] No placeholders / TBD / TODO outside the explicit `<to-be-pinned-after-recompute>` sentinel
- [ ] All thresholds (AIC deltas, capture fractions, R-ratios) pre-pinned with specific numerical values
- [ ] All 3 tests have explicit PASS / MARGINAL / FAIL routing
- [ ] HALT cascades route to CORRECTIONS-block paths (no auto-pivot)
- [ ] Anti-fishing invariants enumerated in §6.1
- [ ] CORRECTIONS-γ structural-exposure framing preserved (no WTP / behavioral-demand language)
- [ ] Free-tier-only budget pin preserved (CORRECTIONS-δ inheritance)
- [ ] Stage-1 sha-pin chain READ-ONLY
- [ ] Cross-substrate weights audit-block-frozen per CORRECTIONS-ζ
- [ ] All 5 Π-forms fitted unconditionally (no early-termination)
- [ ] Bootstrap CIs mandatory at all 3 steps
- [ ] Per-substrate exclusion sensitivity at v1.5c mandatory
- [ ] Cross-corridor sanity check (MXN R) optional but recommended

## §9. Pre-commitment invariants (spec-locked)

1. **Π-form candidate set**: F_a (√σ) + F_b (linear) + F_c (quadratic) + F_d (log) + F_e (piecewise regime). NO post-data extension or substitution.
2. **AIC delta thresholds**: PASS at ΔAIC ≤ 2; MARGINAL at ΔAIC ∈ (2, 5]; FAIL at ΔAIC > 5. NO post-data tuning.
3. **q_t cohort filter**: ≥3 transfers in window. NO post-data relaxation.
4. **q_t K-range**: 4–8 K-means clusters. NO post-data extension.
5. **q_t capture thresholds**: PASS ≥80%; MARGINAL 60–80%; FAIL <60%. NO post-data tuning.
6. **R-ratio verdicts**: BALANCED 0.5–2.0; DEMAND 0.1–0.5; SUPPLY 2.0–10; INFEASIBLE outside. NO post-data tuning.
7. **Bootstrap discipline**: 1000 resamples minimum at all 3 steps. NO sub-1000 fast-path.
8. **CORRECTIONS-ζ aggregation weights**: audit-block-frozen at substrate-discovery time. NO mid-v1.5 weight recomputation.
9. **Sub-test unconditional execution**: all 5 Π-forms, all K values 4–8, all R bootstrap resamples computed regardless of intermediate results. NO early-termination.
10. **HALT cascade discipline**: every test's FAIL/INFEASIBLE outcome routes to a CORRECTIONS-block path with explicit user adjudication. NO silent pivots, NO auto-extensions, NO threshold relaxation post-data.

End of design.
