---
spec_path: pair-d-stage-2-A-fork-simulate
spec_version: v1.0 (initial draft)
spec_author: Backend Architect dispatch 2026-04-30
spec_sha256: <to-be-pinned-after-2-wave-verify>
stage1_pinned_chain:
  spec_v1_3_1: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
  panel: 6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf
  primary_ols: d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf
  robustness_pack: 67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904
  verdict: 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf
tooling_budget_pending: false
tooling_budget_committed: $49/mo Alchemy Growth (2026-04-30 user pin)
internal_ladder: v0 (sympy) -> v1 (Mento+Uniswap fork) -> v2 (Panoptic strip fork) -> v3 (stochastic sigma MC)
convergence_point: v3 calibration with Path B v1 empirical sigma-distribution
verifier_v1_wave1: pending
verifier_v1_wave2: pending
---

# Pair D Stage-2 — Path A "Fork-and-Simulate" Spec

## §1. Goal and scope

Path A is the **fork-and-simulate** verification track for the Pair D Convex Payoff Option (CPO) M-sketch authored under the Stage-2 dispatch brief at `contracts/.scratch/2026-04-30-stage-2-m-sketch-dispatch-brief-pair-d.md`. The goal is mechanical: take the CPO derivation imported from `contracts/notes/2026-04-29-macro-markets-draft-import.md`, drive deterministic and (later) stochastic FX paths through forked open-source contracts (Mento V3, Uniswap V3/V4 on Celo, Panoptic on Ethereum) on a local Anvil/Foundry sandbox, and verify that the realized cash flows produced under contract execution match the framework's analytical predictions for `Δ^(a_l)`, `Δ^(a_s)`, equilibrium `K_l = K_s`, and the Carr-Madan identity `Π(σ_T) ≈ K̂·σ_T`.

The Stage-1 anchor (load-bearing READ-ONLY input, NOT a re-test target) is the Pair D simple-β PASS verdict: β_composite = +0.13670985, HAC SE 0.02465, t = +5.5456, p_one = 1.46×10⁻⁸ (R-AGREE 0/4 flips); sha pin chain `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659` (v1.3.1) → `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf` (panel) → `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf` (primary OLS) → `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904` (robustness) → `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf` (VERDICT.md).

Framing held precisely: **Path A is mechanical verification of the framework's analytical claims under contract execution, NOT re-derivation of Stage-1 empirical results**. Stage-1 established the microeconomic risk admits a positive measurable beta on a Panoptic-eligible reference asset (COP/USD); Path A asks the orthogonal question — given the framework specifies a CPO that *would* settle this relationship, do real open-source contracts honor the framework's identities when driven by a known-shape FX path?

Path A converges with Path B (stochastic-process empirical-calibration) at v3: Path A v3 ingests a calibrated σ-distribution from Path B v1 if available, otherwise uses synthetic GBM / mean-reverting / jump-diffusion processes. The convergence dispatch is a separate spec; Path A's exit gate is its own v3 envelope verification.

## §2. Internal ladder (v0 → v1 → v2 → v3)

The Path A ladder is **simplicity-first**. Each version has a deterministic pre-pinned exit criterion and exits SAA — success, abort, or abort-with-specific-pivot — per the Phase-A.0 anti-fishing discipline. No exit criterion may be retroactively softened; tightening is permitted only via a CORRECTIONS block under post-hoc 3-way review.

**v0 — Pure symbolic math reproduction.** Scope: reproduce the framework's Δ derivation and equilibrium identity in a Sympy + numpy notebook. No smart contracts, no fork, no on-chain inputs. The notebook starts from `(X/Y)_t(ε,ω) = (1 + ε·(cos²(ωt) − 1/2))·(X/Y)̄`, derives `σ_T(ε,ω)`, inverts to `ε(σ_T)`, and computes `Δ^(a_l)` and `Δ^(a_s)` symbolically. Exit criterion: (a) `Δ^(a_l) > 0` over admissible `0 < ε < 1`; (b) `Δ^(a_s) < 0` over same domain; (c) `Π(σ_T) = -∫₀^σ_T Δ^(a)(u) du` yields closed form `K·√σ_T` both sides; (d) linearization `Π ≈ K̂·σ_T`, `K̂ = K*/(2√σ₀)` matches the import verbatim; (e) Carr-Madan strip identity `σ_T = ∫₀^S₀ P(K)/K² dK + ∫_{S₀}^∞ C(K)/K² dK` agrees within 1e-6 against a discrete 12-leg IronCondor approximation at three grid resolutions. Inputs: imported framework note only. Outputs: sympy notebook (.ipynb) + LaTeX-exported derivation + sympy-pickled expression tree. v0 is the analytical proof-of-concept before any contract is touched.

**v1 — Forked Mento V3 + Uniswap V3 (open-source).** Scope: local Anvil forked against Celo mainnet; exercise the Mento V3 FPMM router (`0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`) and a Uniswap V3 Celo USDC/USDm pool; drive a deterministic σ-path via actual swap calls using v0's `(X/Y)_t(ε,ω)` generator; measure realized swap fees as `CF^(a_l) = Σ_t r·|FX_t − FX_{t−1}|`; reconcile against v0's analytic `Δ^(a_l)`. Exit criterion: for at least three independent `(ε,ω)` grid points (small / medium / large ε), realized cumulative LP fees agree with the v0 analytic prediction within ±5% relative error AND the numerical slope of `CF^(a_l)` against `σ_T` is strictly positive in all three. Inputs: v0 notebook (read-only); forked Celo mainnet at pinned block height. Outputs: harness CSV one row per step `(t, X/Y_t, swap_fee_realized, cumulative_CF_a_l, σ_T_running)` + reconciliation report.

**v2 — Forked Panoptic (open-source).** Scope: extend v1 with forked Panoptic on Ethereum (Panoptic-on-Celo is Stage-3 — out of scope; see §6 typed exception); construct the 3-condor / 12-leg Carr-Madan strip per `K_j ≈ S₀·exp(x_j)`, `w_j ∝ 1/K_j²`, three condors covering left-tail / ATM / right-tail; verify `Π(σ_T) ≈ K̂·σ_T` matches v0; verify `K_l = K_s` when both sides are authored against the same reference oracle. Exit criterion: realized strip premium `Π_realized(σ_T)` agrees with v0 analytic `K̂·σ_T` within ±10% across the v1 grid points; supply-side `K_l` and demand-side `K_s` agree within ±2% (numerical drift; algebraic equality is enforced by the equilibrium derivation). Inputs: v1 outputs; forked Ethereum at pinned block height; forked Celo (Mento spot oracle). Outputs: strip configuration JSON (12 strikes, weights, three condor geometries) + premium-time-series CSV + `Π_realized` vs `K̂·σ_T` fit report.

**v3 — Stochastic σ-path Monte Carlo.** Scope: replace the deterministic driver with stochastic processes of increasing fidelity (GBM → mean-reverting Ornstein-Uhlenbeck → jump-diffusion Merton-style → empirically-calibrated if Path B v1 lands during v3); run `N ≥ 1000` paths per variant; verify the realized CPO P&L distribution stays consistent with `Π = K·√σ_T`. Exit criterion: per variant, P&L mean tracks `K̂·E[σ_T]` within ±15% AND the 5th-95th percentile envelope brackets the analytic `K·√σ_T` curve at ≥95% of sampled `σ_T` values. Inputs: v0/v1/v2 outputs; optional Path B v1 empirical σ-distribution (read-only feed); synthetic processes parameterized internally otherwise. Outputs: per-variant MC P&L distribution histograms, envelope-coverage reports, final summary table determining stochastic CPO P&L bounds for the convergence dispatch.

The ladder enforces simplicity: v0 never imports contracts; v1 never imports Panoptic; v2 never imports stochastic libraries; v3 starts only after v2's exit verification is committed under `feedback_two_wave_doc_verification`.

## §3. Inputs (sha-pinned)

Path A inherits the Stage-2 dispatch brief sha-pin chain READ-ONLY (verbatim from dispatch brief §1): spec v1.3.1 `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`; joint panel `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`; primary OLS `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf`; robustness pack `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904`; VERDICT.md `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf`. The imported CPO framework at `contracts/notes/2026-04-29-macro-markets-draft-import.md` is byte-identical to source `~/learning/cfmm-theory/macro-markets/DRAFT.md`. Path A is a Stage-2 spec; it does NOT modify Stage-1 artifacts.

Per-version inputs layer monotonically. **v0** has no on-chain inputs; pure mathematics. **v1** adds: Mento V3 deployment manifest (FPMM router + USDm/COPm pool address resolved at fork-block height); Uniswap V3 Celo manifest (USDC/USDm pool); Anvil + Foundry version pins; Alchemy Growth RPC. **v2** adds: Panoptic-on-Ethereum manifest (canonical contract addresses resolved during v2 implementation); forked Ethereum block height pinned within 24h of forked Celo block height to avoid cross-chain oracle drift. **v3** adds: optional read-only Path B v1 empirical σ-distribution feed (convergence point); synthetic stochastic-process parameter sets (GBM, OU, jump-diffusion) pinned in the v3 implementation plan.

## §4. Outputs

Per-version outputs layer monotonically. **v0**: sympy-driven Jupyter notebook `notebooks/path_a_v0_symbolic.ipynb` with trio-checkpoint discipline per `feedback_notebook_trio_checkpoint`; LaTeX-exported derivation `notebooks/path_a_v0_derivation.tex`; sympy-pickled expression tree `notebooks/path_a_v0_derivation.pkl`; exit-criterion verification report `results/path_a_v0_exit_report.md` enumerating sub-criteria (a)-(e) from §2 with numerical evidence per criterion. **v1**: forked-environment harness CSV `results/path_a_v1_harness.csv` (one row per simulation step); reconciliation-vs-v0 report `results/path_a_v1_reconciliation.md` enumerating per-grid-point relative-error and sign-of-Δ^(a_l) checks; fork-environment manifest `results/path_a_v1_fork_manifest.md` recording Anvil fork block heights, contract addresses, Foundry pins. **v2**: Panoptic strip configuration JSON `results/path_a_v2_strip_config.json` (12 strikes, weights, three condor geometries); premium-time-series CSV `results/path_a_v2_premium_timeseries.csv`; fit report `results/path_a_v2_fit.md` documenting `Π_realized` vs `K̂·σ_T` envelope and `K_l = K_s` numerical-drift checks. **v3**: per-variant MC P&L histograms `results/path_a_v3_mc_distributions/{gbm,ou,jump_diffusion,empirical_calibrated}/`; envelope-coverage report `results/path_a_v3_envelope_coverage.md`; final summary table `results/path_a_v3_summary.md` (Path A → convergence-dispatch handoff).

All outputs use scratch-directory conventions; nothing is committed under `src/`, `test/*.sol`, or `foundry.toml` per `feedback_scripts_only_scope`.

## §5. Tooling stack and budget assumption

Committed budget: **$49/mo Alchemy Growth (RPC reliability for forked Celo + Ethereum at archive-node throughput) plus free-tier everything else**. Free-tier components: Foundry (Anvil + Forge + Cast); Tenderly free tier (transaction simulation + trace inspection); Etherscan + Celoscan free tier (verified-contract retrieval); Sympy + Jupyter + numpy + scipy (v0 mathematics); QuantLib Python bindings (stochastic-process generation + Carr-Madan strip pricing benchmarks in v3). The frontmatter pin is the authoritative commitment and may not be exceeded without explicit user adjudication and a CORRECTIONS block. Any version-level tooling requirement that would exceed this budget — paid simulation-fork service, paid decompilation API, per-call-pricing oracle with non-trivial usage — triggers HALT under the budget-overrun typed exception (see §6).

## §6. HALT discipline (typed exceptions)

Per `feedback_pathological_halt_anti_fishing_checkpoint`, foreseeable blockers are pre-pinned with a typed exception name, a disposition-memo path, and ≥3 user-adjudicated pivot options. Auto-pivot is anti-fishing-banned. Blockers not enumerated below must be surfaced as fresh typed exceptions under the same protocol. Disposition-memo paths follow `contracts/.scratch/2026-XX-XX-stage2-path-a-{version}-{slug}-disposition.md`.

**v0 — `Stage2PathAFrameworkInternallyInconsistent`.** Trigger: symbolic Δ-sign derivation does NOT reproduce the framework's prediction over the admissible domain, OR Carr-Madan strip identity numerically diverges beyond 1e-6. Pivots: (i) re-import the framework from source `~/learning/cfmm-theory/macro-markets/DRAFT.md` and re-verify byte-identity (suspect import corruption); (ii) raise as framework-content question to user with the failing sub-criterion enumerated — auto-amendment is anti-fishing-banned; (iii) shrink Path A scope to the reproducible subset and exit early at v0 with partial-PASS gated on user acceptance.

**v1 — `Stage2PathAMentoUSDmCOPmPoolMissing`.** Trigger: Mento V3 FPMM USDm/COPm pool does NOT exist at fork-block, OR exists with zero liquidity, OR canonical Mento V2 COPM `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` is not paired against USDm. Pivots: (i) substitute Mento V2 BiPool if a USDm/COPm pool exists there; (ii) synthetic COP-leg via cUSD/cEUR cross-pool triangulation through an oracle-fed COP/EUR rate (lower fidelity, preserves architecture); (iii) substitute Uniswap V3 Celo USDC/USDm as v1 reference, synthesizing the COP leg from an oracle-fed COP/USD rate, recording deviation in a CORRECTIONS-block. Dispatch brief §4 authorizes Uniswap V3/V4 Celo Mento-pair as rank-2 supply-side — pre-documented fallback.

**v2 — `Stage2PathACrossChainBridgingRequired`.** Trigger: Panoptic-on-Ethereum cannot reference a Mento Celo-side pool without bridging, AND no Panoptic-on-Celo deployment exists at v2 fork-block. Pivots: (i) substitute a Uniswap V3 Ethereum-mainnet FX-proxy pair as v2 reference oracle, deferring COP-specific calibration to v3; (ii) defer v2 to future Panoptic-on-Celo and exit early at v1 with partial-PASS gated on user acceptance (v3 MC still proceeds against v0+v1); (iii) construct a sandbox-only mock bridging oracle (pulls Mento spot at v1's forked Celo block, exposes on v2's forked Ethereum) — explicitly flagged as sandbox-only, NOT production architecture, in all artifacts.

**v3 — `Stage2PathAStochasticEnvelopeBreached`.** Trigger: stochastic-process variants collectively fail to bracket realized historical σ-path values at the ≥95% envelope-coverage threshold. Pivots: (i) augment with a regime-switching variant capturing the post-2014 oil + COVID + Fed-tightening regime mix per RC FLAG #6; (ii) shrink envelope target from ≥95% to ≥80% with explicit user acknowledgement of irreducible model-class limitation, under CORRECTIONS-block; (iii) defer empirical calibration to convergence dispatch and exit v3 with partial-PASS narrative.

**Orthogonal — `Stage2PathABudgetOverrun`.** Triggers if any version exceeds the $49/mo Alchemy Growth budget. Pivots: (i) reduce fork frequency / cache aggressively to fit free-tier limits; (ii) request user adjudication on one-time budget exception with explicit figure and justification; (iii) descope the affected version's exit criterion within budget under CORRECTIONS-block.

## §7. Anti-fishing posture

Path A inherits the Pair D spec §9 anti-fishing discipline. The framework's mathematical claims are pre-pinned at spec-authoring time; v0's job is reproduction, NOT exploration. If v0 fails to reproduce, the response is HALT under `Stage2PathAFrameworkInternallyInconsistent` — NOT framework amendment. Amendment is out-of-scope for the executor; only the user (adjudicating a HALT memo) can authorize, and authorization triggers a fresh CORRECTIONS-block plus v0 re-dispatch.

Path A is a **verification path, not an exploration path**. Mathematical claims, v1/v2 contract behaviors (deterministic σ-paths produce predicted Δ-sign and strip premium), and the v3 ≥95% coverage threshold are all pre-pinned. No version may post-hoc soften a threshold to claim PASS; only HALT + disposition + user-adjudicated CORRECTIONS + re-dispatch is permitted.

Phase-3 RC FLAG inheritance into Path A:

- **NO BPO causal-channel claims (RC FLAG #1).** Output language describes the CPO as hedging the *correlation* between FX volatility and the empirical Y-series, NOT the BPO causal channel. No output may be framed as "BPO-mechanism hedge verification" or equivalent.
- **NO empirical β re-litigation.** Path A does not estimate β at any stage; Stage-1 PASS is immutable input.
- **NO Stage-3 deployment claims.** No version may include statements about real LP capital, user onboarding, KYC/regulatory, or marketing copy. The v2 sandbox-only mock-bridging scaffold (v2 pivot iii) is explicitly NOT a deployment architecture; outputs must say so.
- **NO new yield-vault creation.** a_l universe is Mento V3 LP / Uniswap V3 LP per dispatch brief §4. Path A *packages* an existing yield vault into a forked harness; it does NOT invent a new vault.
- **Lag-6 dominance honored (RC FLAG #3).** Wherever v1/v2/v3 calibration exposes a settlement-horizon parameter, the practical horizon biases toward 6-month re-tendering, not uniformly across 6-12mo. The ≈80%-at-lag-6 stylized fact is a calibration input, not a free hyperparameter.
- **Brief-vs-spec discipline (RC FLAG #5).** Executors must NOT smuggle any `marco2018_dummy`-equivalent post-data adjustment into v3 calibration inputs from Path B, and must NOT re-litigate the Stage-1 spec-vs-brief record from Pair D MEMO §5; that record is closed.
- **Regime-mix concern (RC FLAG #6).** The v3 stochastic-process universe accommodates regime-switching as a pivot under `Stage2PathAStochasticEnvelopeBreached`; the post-2014 oil + COVID + Fed-tightening regime mix is a Stage-3 maintenance concern.

## §8. Convergence with Path B

Path A v3 ingests an optional empirical σ-distribution feed from Path B v1 if available at v3 execution time. If Path B v1 has not yet landed, Path A v3 proceeds with synthetic stochastic processes and the empirical-calibrated variant defers to the convergence dispatch. The Path A → Path B convergence is a **separate dispatch**, NOT part of this spec; Path A v3's exit gate is the entry gate for the future convergence dispatch but does not author it. That convergence dispatch will compose Path A v3's stochastic envelope verification with Path B v1's empirical σ-distribution into a unified calibrated CPO P&L distribution.

The Stage-3 entry gate (real LP capital + execution on a live Panoptic deployment) is gated on *both* paths reaching v3 exit AND the convergence dispatch closing successfully. Path A alone does NOT unlock Stage-3.

## §9. Self-review checklist

Building blocks naturally integrated: **Background** (Stage-1 PASS verdict + sha-pin chain + CPO framework in §1-§3); **Context** (per-version dependencies, fork-block pinning, HALT-disposition conventions in §3, §4, §6); **Tonal control** (verification-not-exploration voice in §1, §7); **User preferences** ($49/mo Alchemy budget pin in §5, trio-checkpoint discipline in §4, auto-mode adjudication boundary in §6); **Tool use instructions** (per-version stack in §5, artifact locations in §3-§4 specifying when and how the executor invokes Foundry, Sympy, QuantLib, forked-environment harnesses).

Complexity principles present: **Personality and tone** (verification-path framing in §1, §7); **Tool use and formatting guidance** (§5 stack + §4 artifact paths); **Dynamic behavior scaling** (the v0→v1→v2→v3 ladder, each exit gating the next); **Non-negotiable facts** (sha-pin chain in §3 and Stage-1 PASS numerics in §1 override conflicting briefs); **Critical evaluation of user input** (RC FLAG inheritance in §7 licenses refusal of smuggled adjustments and surfacing of brief-vs-spec contradictions); **Application/entity context** (Mento V3 / Uniswap V3 / Panoptic manifests + fork-block pinning in §3, §6); **Guardrails and safety** (typed-exception HALT discipline in §6, pre-pinned memos, ≥3 pivots per exception).

No XML tags. No code; spec is code-agnostic per `feedback_no_code_in_specs_or_plans`. Implementation specifics — contract addresses resolved at fork-block height, exact Anvil/Foundry invocations, Sympy expression-tree code, QuantLib pricing configuration — deferred to per-version sub-agents per `feedback_specialized_agents_per_task`. Quality metrics 1-8 honored: completeness, clarity (deterministic exit criteria, pre-pinned HALT triggers, enumerated pivots), consistency (no §1-§8 conflicts), purposefulness, naturalness (v0→v3 follows the framework's analytical-to-stochastic progression organically), comprehensiveness (what-and-when without how), safety (typed-exception HALT + anti-fishing + budget guard), user experience (unambiguous exit criteria, HALT triggers, artifact paths, deferred-implementation boundaries).

---

**End of spec.** Authored 2026-04-30 PM under auto-mode. Pending 2-wave verification (Reality Checker + Workflow Architect) per `feedback_two_wave_doc_verification` before commit. Spec sha256 to be pinned by orchestrator at commit time.
