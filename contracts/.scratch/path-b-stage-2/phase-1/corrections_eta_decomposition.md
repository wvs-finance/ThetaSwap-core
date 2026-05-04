---
artifact_kind: corrections_eta_decomposition_memo
correction_id: CORRECTIONS-η
parent_spec: contracts/docs/superpowers/specs/2026-05-04-pair-d-stage-2-v1.5-model-fitness-design.md (committed at 26cfff3f2; SUPERSEDED-BY-DECOMPOSITION)
parent_spec_sha256: 8a8ce0571bf7e5786048b13753991468c8fb63596c9dfe1a4d2b409e479a6514
emit_timestamp_utc: 2026-05-04
trigger: 2-wave doc verify on v1.5 spec returned REJECT (Model QA 6 BLOCKs) + ACCEPT_WITH_FLAGS (RC 2 BLOCKs)
disposition_picked: γ (decompose into v1.5-data + v1.5-methodology)
user_pick_received: 2026-05-04 (verbatim message: "\gammma")
authority: feedback_pathological_halt_anti_fishing_checkpoint (HALT + disposition memo + user-enumerated pivot + CORRECTIONS-block + post-hoc 2-wave verify on the result)
---

# CORRECTIONS-η — v1.5 → (v1.5-data + v1.5-methodology) decomposition

## §1. Why this CORRECTIONS-block fires

`feedback_pathological_halt_anti_fishing_checkpoint` requires that any non-trivial change to a verified spec proceed via:
1. HALT-and-surface (no auto-fix)
2. Disposition memo enumerating ≥3 pivot options
3. User adjudication
4. CORRECTIONS-block in next spec revision recording the change with full carry-forward / defer matrix and preserved-guarantees argument
5. Post-hoc 2-wave verify on the result

Step 1 fired implicitly when the 2-wave verifier verdicts came back REJECT/ACCEPT_WITH_FLAGS. Steps 2 and 3 fired in the prior conversation turn (4 pivots α/β/γ/δ presented; user picked γ). This memo executes step 4. Step 5 happens after v1.5-data spec authoring lands.

## §2. The 8 BLOCK-class findings being addressed

### Reality Checker (Wave-1) — `/tmp/wave1_rc_v1_5_design.md`

- **RC-BLOCK-1**: Gate B1 (a)/(b)/(c) substrate-pivot user adjudication silently absorbed. v1.5 implicitly adopts Option (a) BiPool aggregate without explicit user adjudication block. Anti-fishing-banned auto-pivot per `feedback_pathological_halt_anti_fishing_checkpoint`.
- **RC-BLOCK-2**: v1.5a candidate set admits non-convex winners as PASS-with-sensitivity rather than thesis-defeats. Linear F_b winning routes MARGINAL with a sensitivity bandage; under `project_abrigo_convex_instruments_inequality` this should fire a thesis-fitness HALT, not a methodology-tweak.

### Model QA Specialist (Wave-2) — `/tmp/wave2_modelqa_v1_5_design.md`

- **MQ-BLOCK-1** (load-bearing): Spec assumes n=135 weeks; substrate panel reality is n≈9-14 informative weeks for direct BiPool USDm/COPm. Framework's `N_MIN=75 / POWER_MIN=0.80 / MDES_SD=0.40` invariants absent from v1.5 entirely.
- **MQ-BLOCK-2**: AIC k-penalty collapses (4 of 5 forms 2-parameter, observationally near-collinear over realistic σ ∈ [0.005, 0.04]; corr(√σ,σ)≈0.99). AIC must become AICc when n/k<40.
- **MQ-BLOCK-3**: No "AIC-INDISTINGUISHABLE" verdict; F_a-passing-while-other-also-passes silently routes PASS for F_a.
- **MQ-BLOCK-4**: K-means selected-k unpinned. "K-range 4-8 + silhouette validation" gives no deterministic rule; classic K-means fishing knob (random_state, init, scaling also unpinned).
- **MQ-BLOCK-5**: Bootstrap method unpinned. i.i.d. on autocorrelated weekly RV series under-covers by 5-15pp. Need stationary bootstrap (Politis-Romano), BCa, n=10000, AR(1)-aware block-length.
- **MQ-BLOCK-6**: R-verdict ignores bootstrap CI. Intermediate R-zones [0.1, 0.5] and [2.0, 10] under-mapped; threshold motivation unstated.

## §3. Why γ (decomposition) wins over α/β/δ

The 8 BLOCKs partition cleanly into two classes:

**Class S (Substrate / data-collection)** — 1 of 8:
- MQ-BLOCK-1 partial: substrate-thinness (n=9 today; CORRECTIONS-ζ aggregation expansion targets n≥75 across 7-venue aggregate)

**Class M (Methodology / statistical-discipline)** — 7 of 8:
- RC-BLOCK-1 (substrate-pivot adjudication block)
- RC-BLOCK-2 (thesis-fitness verdict layer)
- MQ-BLOCK-1 floor-pinning (which form does the floor take? depends on aggregate-panel realized n)
- MQ-BLOCK-2 (AIC vs AICc threshold)
- MQ-BLOCK-3 (AIC-INDISTINGUISHABLE verdict)
- MQ-BLOCK-4 (K-means k-selection rule)
- MQ-BLOCK-5 (bootstrap method)
- MQ-BLOCK-6 (CI-aware R-verdict + threshold motivation)

The 7 Class-M BLOCKs are **better resolved with empirical anchors in hand**. Specifically:
- AICc vs AIC depends on realized n/k ratio — pin after aggregate panel built
- K-means k-selection rule depends on observed cohort size and feature-space separability
- Bootstrap block-length depends on realized AR(1) on aggregate R-series
- R-thresholds [0.5, 2.0] etc. need motivation from realized data shape, not a-priori guesses

α (full CORRECTIONS-η-prime patching all 8 BLOCKs in one v1.6 revision) → forces a-priori choices on Class M without empirical anchors → leaves the spec exposed to "we picked thresholds before seeing data, but not for principled reasons." α is rhetorically rigorous but methodologically fragile.

β (admissibility-minimum patch covering RC-BLOCK-1/2 + MQ-BLOCK-1/5) → ships v1.5 with technical debt routed through plan-level rigor; risks plan-level pre-commits drifting away from spec-level discipline.

δ (park v1.5 entirely, expand parent plan with substrate-aggregation tasks only) → loses the formal model-fitness gate that justified v1.5's existence in the first place.

γ aligns with:
- User's explicit data-first reframe: "the most important thing is to get the most data we can from all the sources of dark currency sources... we need to first collect the most of the data" (2026-05-04)
- Model QA's substrate-reality finding: pinning n=9 vs n=135 changes every methodological choice
- Anti-fishing discipline: defer Class-M choices until empirical anchors are in hand, then pin them with motivation rooted in realized data shape

## §4. Decomposition — what carries forward to v1.5-data

The v1.5-data spec inherits VERBATIM from v1.5-original:

| v1.5-original section | Disposition | Notes |
|---|---|---|
| §1 Overview (data-first paragraph) | CARRY (rewritten) | Reframed for data-only scope |
| §2 Architecture diagram | CARRY (modified) | Drops v1.5a/b/c branches; keeps substrate-expansion + aggregate-panel-build |
| §3 v1.5a Π convexity test | DEFER to v1.5-methodology | Class M |
| §4 v1.5b q_t empirical fit | DEFER to v1.5-methodology | Class M |
| §5 v1.5c K equilibrium | DEFER to v1.5-methodology | Class M |
| §6.1 Anti-fishing invariants | CARRY (filtered) | Substrate-side rows kept; methodology-side rows DEFER |
| §6.2 Output format conventions | CARRY (data-only deliverables) | |
| §6.3 DuckDB integration | CARRY | Data-tier-relevant |
| §6.4 Failure cascades | CARRY (filtered) | Substrate-side failures only; methodology cascades DEFER |
| §7.1 CLAUDE.md update | CARRY (substrate-expansion-scope-only) | Mento-native ONLY relaxation language preserved |
| §7.2 Parent spec CORRECTIONS-ζ scope | CARRY | Same TOML pin additions for 5 new substrates |
| §7.3 Parent plan main-plan pointer | RE-AUTHOR | Smaller scope; data-only sub-plan |
| §7.4 Sub-plan footprint | SHRINK | ~10-15 tasks (was 22-25) for data-only sub-plan |
| §7.5 Verification gates | CARRY | 2-wave per artifact |
| §7.6 Sequencing PRIORITY-1 | CARRY | This IS the v1.5-data scope |
| §7.6 Sequencing PRIORITY-2 + Model tweaking | DEFER to v1.5-methodology | Class M |
| §8 Self-review checklist | CARRY (filtered) | Substrate-side items kept |
| §9 Pre-commitment invariants 1-7 | DEFER (Class M thresholds) | F-set, AIC deltas, q_t cohort filter, K-range, capture thresholds, R-ratio thresholds, bootstrap discipline → all Class M |
| §9 Pre-commitment invariant 8 (CORRECTIONS-ζ aggregation weights audit-block-frozen) | CARRY | Substrate-side; load-bearing for v1.5-data |
| §9 Pre-commitment invariant 9 (Sub-test unconditional execution) | DEFER (Class M) | |
| §9 Pre-commitment invariant 10 (HALT cascade discipline) | CARRY | Universal anti-fishing |

NEW content authored in v1.5-data (NOT inherited from v1.5-original):
- Per-venue audit protocol with explicit PASS/MARGINAL/HALT thresholds (mirrors Phase 1 audit script structure with venue-specific thresholds)
- Per-venue substrate inclusion table (resolves RC FLAG-7 from Wave-1 verdict — verdict / pending-action / velocity-floor disposition per venue)
- N_INFORMATIVE measurement protocol (NEW — addresses MQ-BLOCK-1's substrate-side half: how to count informative weeks across the aggregate panel; the FLOOR threshold itself is DEFERRED to v1.5-methodology since it depends on realized n)
- W1-W5 aggregation invariants embedded directly in v1.5-data §9 (was only in companion `aggregation_methodology.md`; RC FLAG-8 promotion)
- audit_block freezing protocol with sha256-pinned timestamps (formalizing what `aggregation_methodology.md` §5 had as W5)
- `cop_corridor_aggregate_panel.parquet` schema definition (new artifact; prior was only described prose in `aggregation_methodology.md` §9)

## §5. Decomposition — what defers to v1.5-methodology

v1.5-methodology spec authoring is BLOCKED until v1.5-data delivers:

1. `cop_corridor_aggregate_panel.parquet` — built (Phase 2 v1.5-data sub-plan execution)
2. `n_informative_table.parquet` — emitted; rows per venue and aggregate; columns include `weeks_with_nonzero_events`, `weeks_with_active_holders`, `non_zero_week_pct`
3. AR(1) coefficient computed on aggregate R-numerator series; emitted to `ar1_diagnostic.json` (informs bootstrap block-length pinning in v1.5-methodology)
4. σ-anchor reality check per anchor (Banrep TRM availability, Mento V2 BiPool spot informative weeks, Polygon Uniswap V3 spot informative weeks); informs σ-anchor primary specification in v1.5-methodology
5. Cohort-N empirical floor measurement: how many addresses survive the ≥3-transfers filter on the aggregate panel; informs cohort floor + survivorship sensitivity arm in v1.5-methodology

When v1.5-methodology is authored (post-v1.5-data execution), it resolves:

| BLOCK | How v1.5-methodology resolves with empirical anchors |
|---|---|
| RC-BLOCK-1 | §0 explicit Gate B1 substrate-pivot adjudication block now references the realized aggregate panel (so the (a)/(b)/(c) options are evaluated with real numbers, not prior-Phase-1 thinness) |
| RC-BLOCK-2 | §3 thesis-fitness verdict layer added: AIC-winning forms that are non-convex in σ (linear, concave) FAIL the thesis-fitness check regardless of ΔAIC magnitude; F_b-wins fires `Stage2PathBPiNotConvex` typed exception |
| MQ-BLOCK-1 | §6.1 N_INFORMATIVE floor pinned at concrete value (75 if framework precedent holds, or justified alternative based on realized aggregate n); §9 includes the floor; HALT routing on n<floor |
| MQ-BLOCK-2 | §3 AICc replaces AIC when n/k<40; small-n correction explicit; published power table for each form-pair contrast at α=0.05, β=0.20 over realistic σ-range |
| MQ-BLOCK-3 | §3 PASS/PASS-WEAK/MARGINAL/FAIL routing covers AIC-INDISTINGUISHABLE explicitly |
| MQ-BLOCK-4 | §4 K-means selected-k via deterministic argmax silhouette with seed pin + multi-criterion cross-check (silhouette / elbow / Davies-Bouldin / Calinski-Harabasz); per-k capture fraction emitted regardless |
| MQ-BLOCK-5 | §5 stationary bootstrap (Politis-Romano), BCa CI, n=10000, block-length = 1/(1-ρ̂) capped at 26 weeks where ρ̂ from §4 of v1.5-data emission |
| MQ-BLOCK-6 | §5 CI-aware R-verdict: bootstrap 95% CI must lie within single band; CI straddling routes MARGINAL toward conservative band; threshold motivation cited (AMM-concentration, option-market-making, or Stage-3 economics — pinned in §9 with citation) |

## §6. Preserved guarantees argument

This decomposition preserves:

1. **Anti-fishing discipline**: every Class M choice is deferred until empirical anchors land, then pinned with motivation rooted in realized data shape — NOT post-hoc tuning. The discipline gets STRONGER, not weaker, because pre-commits are anchored to empirical reality rather than a-priori guesses.

2. **Convex-instrument thesis** (`project_abrigo_convex_instruments_inequality`): RC-BLOCK-2 thesis-fitness verdict layer is preserved as a v1.5-methodology hard requirement, not lost in decomposition. F_b-wins fires a typed exception in v1.5-methodology, not a sensitivity bandage.

3. **Gate B1 substrate-pivot adjudication** (`feedback_pathological_halt_anti_fishing_checkpoint`): RC-BLOCK-1 user adjudication block becomes a v1.5-methodology pre-condition. v1.5-data SHIPS the aggregate panel, which is what informs the (a)/(b)/(c) decision; the decision itself happens at v1.5-methodology authoring time, with realized substrate data in hand.

4. **Free-tier budget pin** (CORRECTIONS-δ): preserved in v1.5-data §7. v1.5-methodology will preserve it too (pure data analysis, no on-chain re-reads).

5. **CORRECTIONS-γ structural-exposure framing**: preserved across both child specs.

6. **Stage-1 sha-pin chain READ-ONLY**: preserved.

7. **Two-wave doc verification on every artifact** (`feedback_two_wave_doc_verification`): v1.5-data gets RC + Model QA; v1.5-methodology gets RC + Model QA when authored.

## §7. Implementation order

1. **THIS MEMO** — committed
2. **v1.5-original spec** — header marked SUPERSEDED-BY-DECOMPOSITION pointing to v1.5-data + v1.5-methodology-pending
3. **v1.5-data spec** — authored fresh; self-review; user review (per `superpowers:brainstorming` skill flow)
4. Single commit with all three (memo + SUPERSEDED header + v1.5-data spec); push to dev
5. Surface to user
6. On user approval: 2-wave verify v1.5-data (RC + Model QA in parallel)
7. Integrate Wave-1+2 findings on v1.5-data → commit revision
8. Author CLAUDE.md framework update (Rev-5.3.5 substrate-expansion corrigendum) → 2-wave verify → commit
9. Author parent spec CORRECTIONS-ζ (data-only scope: substrate TOML pins + §1/§3/§4/§6 prose) → 2-wave verify → commit
10. Author parent plan CORRECTIONS-β' (data-only scope: substrate-expansion tasks; methodology tasks DEFERRED placeholder) → 2-wave verify → commit
11. Author v1.5-data sub-plan via writing-plans skill → 2-wave verify → commit
12. PR + merge to upstream
13. EXECUTE v1.5-data sub-plan: substrate-expansion audits + aggregate panel build + N_INFORMATIVE measurement + AR(1) emission
14. Once v1.5-data deliverables land, author v1.5-methodology spec (BLOCKED until step 13 completes); self-review; 2-wave verify; sub-plan; etc.

## §8. Cost

- Authoring v1.5-data: ~1 spec authoring session (~600-800 lines)
- Re-running 2-wave verify on v1.5-data: comparable to v1.5-original's verify run (~10-15 min wall clock per wave, parallel)
- Net delay vs α (full v1.6 patch): roughly +1 verify cycle (~30 min) but with substantially lower technical-debt exposure
- Net velocity vs δ (park v1.5 entirely): comparable; γ keeps the formal model-fitness gate alive at v1.5-methodology

## §9. Anti-fishing invariant: this CORRECTIONS-block is itself anti-fishing-proof

Per `feedback_pathological_halt_anti_fishing_checkpoint`, a CORRECTIONS-block is valid only when:
- (a) Triggered by an external signal (verifier verdict, HALT, etc.) — ✓ (2-wave verify REJECT)
- (b) Disposition memo with ≥3 pivot options — ✓ (α/β/γ/δ presented)
- (c) User adjudication — ✓ (γ picked verbatim)
- (d) Old + new + preserved-guarantees argument — ✓ (§4-§6 above)
- (e) Post-hoc verify on the result — ✓ (queued: v1.5-data 2-wave verify after authoring)

NO threshold was relaxed in this CORRECTIONS-block. NO methodology was weakened. Class-M discipline was DEFERRED until empirical anchors land — strengthening, not weakening, the eventual pre-commits.

End of CORRECTIONS-η.
