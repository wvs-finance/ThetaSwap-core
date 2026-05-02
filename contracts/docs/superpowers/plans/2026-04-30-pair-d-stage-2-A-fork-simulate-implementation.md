---
plan_path: pair-d-stage-2-A-fork-simulate-implementation
plan_version: v1.0
plan_author: Backend Architect dispatch 2026-05-02 (post spec v1.2.1 commit)
plan_sha256_v1_0: <to-be-pinned-by-orchestrator-at-commit>
spec_sha256_pin: 1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78
spec_version_pin: v1.2.1 (CORRECTIONS-δ' Alchemy CU figure correction; supersedes v1.2 ab65fd20… → v1.1 de4e8cdc… → v1.0 56fa06b8…)
spec_path: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-A-fork-simulate-spec.md
internal_ladder_pin: v0 (sympy) → v1 (Mento+Uniswap fork) → v2 (Panoptic strip fork) → v3 (stochastic-σ MC, GBM baseline)
budget_pin: free_tier_only (per spec §5 + CORRECTIONS-δ; supersedes 2026-04-30 $49/mo Alchemy Growth pin)
stage1_pinned_chain:
  spec_v1_3_1: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
  panel: 6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf
  primary_ols: d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf
  robustness_pack: 67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904
  verdict: 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf
companion_path_b_spec_sha256_advisory_only: 4e8905a9 (Path B v1.3 — referenced for §7 cross-path-coordination awareness ONLY; this plan does NOT plan for Path B)
plan_verifier_v1_wave1: pending (Reality Checker — pre-execution gate per §9)
plan_verifier_v1_wave2: pending (Workflow Architect — pre-execution gate per §9)
notebook_trailer_convention: Phase 1-4 notebook commits use `Doc-Verify: orchestrator-only-pre-phase-5 (3-way review deferred to Phase 5 convergence audit)` trailer; Phase 5 convergence-verdict commit uses standard `Doc-Verify: cr=<id>/rc=<id>/sd=<id>` 3-way trailer per `feedback_implementation_review_agents`. Plan / spec / CLAUDE.md commits use 2-wave `Doc-Verify: wave1=<RC-id> wave2=<WA-id>` per `feedback_two_wave_doc_verification`.
---

# Pair D Stage-2 — Path A (Fork-and-Simulate) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Per project convention `feedback_no_code_in_specs_or_plans`, this plan is code-agnostic; implementation specifics are deferred to executor sub-agents per task. Per `feedback_specialized_agents_per_task`, each task names the specialist owner. Per `feedback_strict_tdd`, every implementation task has a failing-test-first sub-task before the implementation sub-task.

---

## §1. Overview

This plan operationalizes the **Path A (fork-and-simulate)** verification track for the Pair D Convex Payoff Option (CPO) M-sketch. The Stage-1 empirical validation closed PASS on 2026-04-28 (β_composite = +0.13670985, HAC SE 0.02465, t = +5.5456, p_one = 1.46×10⁻⁸; R-AGREE 0/4 flips); this plan does NOT re-test that result. Per CLAUDE.md framework Stage-2 ideal-scenario clause, Path A's job is **mechanical verification of the CPO framework's analytical identities under contract execution** — we drive deterministic and stochastic FX paths through forked open-source contracts (Mento V3, Uniswap V3 on Celo, Panoptic on Ethereum) and verify that realized cash flows match the framework's predictions for `Δ^(a_l) > 0`, `Δ^(a_s) < 0`, equilibrium `K_l = K_s`, and the Carr-Madan replication identity `Π(σ_T) ≈ K̂·σ_T` within the §11 disambiguated tolerances.

The spec (sha `1a4cc6a4…`, v1.2.1) prescribes a four-rung internal ladder — v0 (pure sympy mathematics, no contracts) → v1 (Mento+Uniswap forked Celo) → v2 (Panoptic strip on forked Ethereum, 3 condors / 12 legs) → v3 (stochastic-σ Monte Carlo with GBM baseline, ≥1000 paths). Each rung has pre-pinned exit criteria; SAA discipline (Success / Abort / Abort-with-pivot) per the Phase-A.0 anti-fishing posture. The v3 GBM baseline is non-negotiable per FLAG-F4; Ornstein-Uhlenbeck and jump-diffusion are optional escalations only available under the §6 typed-exception protocol. Reproducibility is pinned at byte-identical-artifact granularity per BLOCK-D1: per-version manifests record fork block heights, RPC source ladder (PRIMARY = Alchemy free-tier; FALLBACK = public RPC), Foundry/Anvil version pin, gas-price determinism strategy, and per-variant RNG seeds for v3.

The framing line that constrains every task in this plan: **Path A is a verification path, NOT an exploration path**. The framework's mathematical claims, the §11.b 5% truncation bound, the §11.a self-consistency machine-epsilon × N_legs bound, the v3 ≥95% envelope-coverage threshold, and the 11 typed exceptions in §6 are all pre-pinned at spec-authoring time. Executors do NOT amend any of these post-data; HALT under the appropriate typed exception is the only legal response when an exit criterion fails. Path A is **DEFAULT INDEPENDENT** of Path B per §12 (only v3's optional empirical-σ-distribution variant is conditionally coupled, READ-ONLY); convergence reconciliation is a separate downstream dispatch. Stage-3 deployment (real LP capital, user onboarding, KYC) is explicitly out of scope.

---

## §2. Phase decomposition

The five phases below mirror the v0→v3 ladder structure plus an environment-scaffolding bootstrap and a final convergence-audit phase. Phase boundaries are also commit boundaries: each phase produces a commit-able artifact set under the per-phase trailer convention pinned in the frontmatter.

- **Phase 0 — Environment scaffolding.** Foundry/Anvil install + version pin, Python venv with sympy + numpy + scipy + QuantLib + Jupyter pinned per spec §10.2, free-tier RPC endpoint registration (Alchemy free-tier app for Celo + Ethereum, public RPC fallback URLs verified reachable), test-directory layout (`results/`, `notebooks/`, `tests/` under the scratch root), notebook scaffolding mirroring `contracts/notebooks/fx_vol_cpi_surprise/Colombia/` 3-NB pattern with the `env.py` parents-fix convention. Outputs: dependency manifest, scratch-root README, environment-smoke-test report. Phase 0 produces **no analytical artifact**; its job is to make Phase 1 dispatch executable.

- **Phase 1 — v0 sympy ladder.** Pure-mathematics implementation of the framework's CPO derivation: symbolic Δ derivation over the admissible `(ε, ω)` domain, closed-form `Π(σ_T) = K·√σ_T` derivation, linearization to `Π ≈ K̂·σ_T`, Carr-Madan strip identity `σ_T = ∫ P(K)/K² dK + ∫ C(K)/K² dK`, and discrete 12-leg IronCondor approximation reconciliation against the analytic at three grid resolutions per the §11 disambiguated tolerances. Three notebooks under trio-checkpoint discipline (`feedback_notebook_trio_checkpoint`); LaTeX-exported derivation; sympy-pickled expression tree as the artifact handed to Phase 2 + Phase 4 reconciliation. v0 NEVER imports contracts. Exit criterion is the §2 v0 exit specified in the spec.

- **Phase 2 — v1 Mento+Uniswap fork.** Local Anvil forked against Celo mainnet at the §10.1-pinned fork-block height; exercise the Mento V3 FPMM router (`0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`) + canonical Mento V2 COPM token (`0x8A567e2aE79CA692Bd748aB832081C45de4041eA`) + Uniswap V3 Celo USDC/USDm pool; resolve the USDm/COPm pool address at fork-block height; drive a deterministic σ-path via `(X/Y)_t(ε,ω)` actual swap calls; measure realized swap fees as `CF^(a_l) = Σ_t r·|FX_t − FX_{t−1}|`; reconcile against v0 analytic per §10.4. v1 exit criterion: ±5% relative-error agreement at three grid points + sign-of-`CF^(a_l)`-slope strictly positive.

- **Phase 3 — v2 Panoptic IronCondor strip on forked Ethereum.** Extend v1 with Panoptic-on-Ethereum forked at a block height within ±24h of the Celo-side fork to avoid cross-chain oracle drift; construct the **3 IronCondor positions × 4 legs each = 12 legs total** strip per §10.5 (left-tail / ATM / right-tail condors, strikes per `K_j ≈ S₀·exp(x_j)`, weights per `w_j ∝ 1/K_j²`); verify `Π(σ_T) ≈ K̂·σ_T` matches v0 per §11.b 5% truncation bound; verify `K_l = K_s` per §11.a machine-epsilon-×-N_legs self-consistency bound. v2 exit criterion: per-grid-point premium reconciliation + numerical-drift check on the equilibrium identity.

- **Phase 4 — v3 stochastic-σ MC under GBM baseline.** Replace the deterministic driver with a Geometric Brownian Motion process on the FX rate (FLAG-F4 pin: GBM is the v3 baseline; OU and jump-diffusion are only triggered if GBM fails the envelope-coverage threshold under `Stage2PathAStochasticEnvelopeBreached`). Calibrate GBM parameters (μ, σ_BM) to the v1 deterministic-path range. Run N ≥ 1000 paths under §10.3 RNG seed pin (`numpy.random.default_rng(seed=…)`, NOT legacy global state). Compute realized CPO P&L distribution; verify mean tracks `K̂·E[σ_T]` per §11.b and 5th-95th percentile envelope brackets the analytic `K·√σ_T` curve at ≥95% of sampled `σ_T` values. v3 exit criterion: GBM-baseline envelope coverage ≥95% OR §6 escalation triggered with explicit pivot disposition.

- **Phase 5 — Convergence + verdict authoring.** Per-rung exit-criterion audit (do v0/v1/v2/v3 outputs satisfy their pre-pinned exit criteria byte-identically across re-runs?); compose Path A result memo `path_a_verdict_memo.md` mirroring the Pair D Stage-1 MEMO §1-§10 structure; emit machine-readable `path_a_verdict.json`; surface to Path B convergence-dispatch handoff (does NOT author the convergence dispatch — that is downstream). 3-way implementation review per `feedback_implementation_review_agents` (Code Reviewer + Reality Checker + Senior Developer) on the full Path A artifact bundle.

---

## §3. Tasks per phase

### Phase 0 — Environment scaffolding

#### Task 0.1: Foundry / Anvil install + version pin

**Goal:** Install Foundry (Anvil + Forge + Cast) at a pinned commit hash; verify Anvil can fork against Celo mainnet and Ethereum mainnet via free-tier RPC; record the pinned versions in the scratch-root environment manifest.

**Inputs:**
- Spec §5 (free-tier-only budget pin) and §10.2 (library + Foundry version pin requirement).
- Companion Stage-1 plan reference `contracts/docs/superpowers/plans/2026-04-27-simple-beta-pair-d-implementation.md` (file-structure precedent).

**Owner:** Senior Developer (DevOps-aware backend specialist).

**Outputs:**
- `contracts/.scratch/pair-d-stage-2-path-a/environment_manifest.md` — Foundry commit hash, Anvil version string, OS+arch, Python version, sympy / numpy / scipy / QuantLib pin chain, Alchemy free-tier app IDs (Celo + Ethereum), public-RPC fallback URLs verified reachable.
- `contracts/.scratch/pair-d-stage-2-path-a/environment_smoke_test.md` — output of one-shot Anvil forks (1 against Celo mainnet, 1 against Ethereum mainnet) at a recent block height, demonstrating fork-up + a single `eth_blockNumber` RPC succeeds under both PRIMARY (Alchemy) and FALLBACK (public RPC) per §10.1 ladder.

**Success criteria:**
- All version pins recorded in the manifest are reproducible (re-install at the pinned commit produces identical version strings).
- Smoke test demonstrates Alchemy free-tier reachability AND public-RPC fallback reachability for both chains.
- Free-tier compute-unit baseline reading captured (current Alchemy app CU balance for the month, to budget Phase 2 + Phase 3 fork operations).

**Dependencies:** None — Phase 0 is the bootstrap.

**Typed-exception triggers in scope:** `Stage2PathABudgetOverrun` (if Foundry or any pinned dependency requires a paid service to install/run); none of the version-specific typed exceptions (Alchemy rate limit, archive-node depth, public-RPC determinism) fire at Phase 0.

#### Task 0.2: Python environment + notebook scaffolding

**Goal:** Pin Python venv with sympy + numpy + scipy + QuantLib Python bindings + Jupyter; create the notebook scaffolding directory tree mirroring the `contracts/notebooks/fx_vol_cpi_surprise/Colombia/` 3-NB pattern AND the `bpo_offshoring_fx_lag/Colombia/` `env.py` parents-fix convention; create empty `references.bib` for spec sha pin + framework citation.

**Inputs:**
- Spec §10.2 library pins.
- Stage-1 plan precedent for `env.py` pattern (Pair D notebook scaffolding under `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/`).

**Owner:** Analytics Reporter (notebook-discipline owner).

**Outputs:**
- `contracts/notebooks/pair_d_stage_2_path_a/env.py` — paths-to-data + dependency-import + 4-part-citation-template (`feedback_notebook_citation_block`) following the parents-fix convention from `contracts/notebooks/abrigo_y3_x_d/env.py` (commit `865402c2c`).
- `contracts/notebooks/pair_d_stage_2_path_a/references.bib` — entries for: (i) spec sha pin `1a4cc6a4…`; (ii) Stage-1 verdict pin `1efd0e34…`; (iii) imported CPO framework path; (iv) Carr-Madan 1998 (replication identity); (v) Panoptic protocol whitepaper (per Panoptic-domain reference convention); (vi) Mento V3 documentation reference.
- Skeleton notebooks (Phase 1 + 2 + 3 + 4 placeholders): `01_v0_symbolic_derivation.ipynb`, `02_v0_strip_reconciliation.ipynb`, `03_v0_exit_report.ipynb`, `04_v1_mento_uniswap_fork.ipynb`, `05_v1_reconciliation.ipynb`, `06_v2_panoptic_strip_fork.ipynb`, `07_v2_fit.ipynb`, `08_v3_gbm_baseline.ipynb`, `09_v3_envelope_audit.ipynb`. Phase 5 produces a non-notebook memo, not a notebook.
- `contracts/.scratch/pair-d-stage-2-path-a/README.md` — directory-tree map + per-rung output-artifact location pin.

**Success criteria:**
- Notebook skeletons import `env.py` cleanly (parents-fix verified).
- `references.bib` parses under standard BibTeX tooling (`bibtex` / Pandoc).
- Directory tree matches the location pins in spec §4.

**Dependencies:** Task 0.1 complete (Python venv depends on Foundry-adjacent decisions about local-compute layout, but functionally independent — can run in parallel after Task 0.1's manifest lands).

**Typed-exception triggers in scope:** `Stage2PathABudgetOverrun` (if any pinned Python dependency requires a paid service); none of the fork-specific typed exceptions.

#### Task 0.3: Phase 0 implementation review (3-way)

**Goal:** Validate Phase 0 outputs are reproducible and complete before Phase 1 dispatch.

**Owner:** Foreground Orchestrator dispatches Code Reviewer + Reality Checker + Senior Developer in parallel per `feedback_implementation_review_agents`.

**Inputs:** All Phase 0 outputs.

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/phase_0_review.md` — three-reviewer verdict matrix.

**Success criteria:** All three reviewers PASS-WITH-AT-MOST-NITS; any BLOCK halts and re-dispatches Backend Architect for fixes per the implementation-review-agents convention.

**Dependencies:** Task 0.1 + Task 0.2 complete.

**Typed-exception triggers in scope:** None at the review stage; reviewers may flag setup-level deviations from spec §5 / §10 that trigger one of the budget / archive / RPC typed exceptions when re-cast as a HALT for Phase 1.

---

### Phase 1 — v0 sympy ladder (symbolic + Carr-Madan strip)

#### Task 1.1: Failing-test scaffold for v0 exit criteria

**Goal:** Per `feedback_strict_tdd`, write a failing test suite that encodes the spec §2 v0 exit criteria (sub-criteria a-e) before any sympy code is written. The test suite asserts: (a) `Δ^(a_l) > 0` over admissible domain; (b) `Δ^(a_s) < 0` over same; (c) `Π(σ_T) = K·√σ_T` closed-form match; (d) linearization `Π ≈ K̂·σ_T` with `K̂ = K*/(2√σ₀)` matches the import verbatim; (e) Carr-Madan 12-leg strip vs analytic per §11.a + §11.b at three grid resolutions.

**Inputs:** Spec §2 v0 exit criteria; spec §11.a + §11.b tolerances; imported CPO framework note.

**Owner:** Senior Developer (TDD discipline).

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/tests/test_v0_exit_criteria.py` — pytest suite with 5 sub-test groups (a-e), all FAILING (no implementation yet).

**Success criteria:** Test suite imports cleanly; all 5 sub-test groups produce explicit FAIL (not ERROR) under `pytest --tb=short`; failure messages cite spec §2 v0 sub-criterion verbatim.

**Dependencies:** Task 0.3 PASS.

**Typed-exception triggers in scope:** None — pure-Python local test scaffold.

#### Task 1.2: Notebook 01 — symbolic Δ derivation (v0 trio 1-3)

**Goal:** Implement the framework's symbolic Δ derivation in `01_v0_symbolic_derivation.ipynb` under trio-checkpoint discipline. Trio 1: load framework + assert `(X/Y)_t(ε,ω)` form matches import; Trio 2: derive `σ_T(ε,ω)` and invert to `ε(σ_T)`; Trio 3: derive `Δ^(a_l)` and `Δ^(a_s)` symbolically and verify sign over admissible `0 < ε < 1`.

**Inputs:** Spec §2 v0 sub-criteria (a) + (b); imported CPO framework note; failing test from Task 1.1.

**Owner:** Analytics Reporter (notebook-trio discipline) with Senior Developer pair-review on each trio HALT.

**Outputs:**
- Filled notebook `notebooks/pair_d_stage_2_path_a/01_v0_symbolic_derivation.ipynb` with 3 completed trios (each = why-markdown + code-cell + interpretation-markdown).
- Sympy-pickled intermediate: `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v0_delta_expressions.pkl` — pickled `Δ^(a_l)` and `Δ^(a_s)` sympy expression trees.

**Success criteria:** Sub-tests (a) + (b) from Task 1.1 PASS when pointed at the exported pickled expressions. Trio HALTs all logged in the orchestrator review trail per `feedback_notebook_trio_checkpoint` (NON-NEGOTIABLE per memory).

**Dependencies:** Task 1.1 (failing tests must exist first per TDD).

**Typed-exception triggers in scope:** `Stage2PathAFrameworkInternallyInconsistent` if symbolic derivation does not produce the framework-predicted Δ-signs.

#### Task 1.3: Notebook 02 — Π closed form + Carr-Madan strip reconciliation (v0 trio 4-6)

**Goal:** Implement `Π(σ_T) = K·√σ_T` closed-form derivation, linearization to `Π ≈ K̂·σ_T`, and Carr-Madan 12-leg strip approximation + analytic reconciliation per §11.a + §11.b. Three trios: Trio 4: closed-form Π derivation + linearization match-to-import; Trio 5: 12-leg IronCondor strip approximation construction (3 condors × 4 legs per §10.5); Trio 6: numerical reconciliation at three grid resolutions per §11.a (≤1e-10 × N_legs self-consistency) and §11.b (≤5% relative-error truncation).

**Inputs:** Task 1.2 outputs (pickled Δ expressions); spec §2 v0 sub-criteria (c) + (d) + (e); spec §10.5 strip pin; spec §11.a + §11.b tolerances.

**Owner:** Analytics Reporter (notebook-trio discipline).

**Outputs:**
- Filled notebook `02_v0_strip_reconciliation.ipynb` with 3 completed trios.
- Sympy-pickled final: `contracts/.scratch/pair-d-stage-2-path-a/notebooks/path_a_v0_derivation.pkl` — full sympy expression tree.
- LaTeX export: `contracts/.scratch/pair-d-stage-2-path-a/notebooks/path_a_v0_derivation.tex` — printable derivation including the §11.b closed-form bound expression `ε_total ≤ ε_truncation + ε_discretization`.

**Success criteria:** Sub-tests (c) + (d) + (e) from Task 1.1 PASS at three grid resolutions; §11.a self-consistency holds at ≤1.2e-9 absolute error per payoff evaluation; §11.b truncation/discretization bound holds at ≤5% relative error at the §10.5 grid + GBM σ₀ ≈ 10% baseline.

**Dependencies:** Task 1.2 complete.

**Typed-exception triggers in scope:** `Stage2PathAFrameworkInternallyInconsistent` if Carr-Madan strip identity diverges beyond §11 bounds at the §10.5 grid.

#### Task 1.4: Notebook 03 — v0 exit report

**Goal:** Synthesize Notebooks 01 + 02 into a single exit-criterion verification report enumerating sub-criteria (a)-(e) from §2 v0 with explicit numerical evidence per criterion (criterion (e) cites the §11 disambiguated bounds explicitly).

**Inputs:** Tasks 1.2 + 1.3 outputs.

**Owner:** Analytics Reporter.

**Outputs:**
- Notebook `03_v0_exit_report.ipynb` — single-purpose summary notebook.
- Markdown report `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v0_exit_report.md` — sub-criteria (a)-(e) PASS/FAIL table with numerical evidence and §10.4 reconciliation cross-pin.

**Success criteria:** Report is human-readable; all 5 sub-criteria marked PASS; §10.4 reconciliation block enumerates the three pinned `(ε, ω)` test points and their numeric values.

**Dependencies:** Tasks 1.2 + 1.3 complete.

**Typed-exception triggers in scope:** None at the synthesis stage.

#### Task 1.5: Phase 1 implementation review (3-way)

**Goal:** Validate v0 outputs satisfy spec §2 v0 exit criteria + §11 tolerances + reproducibility per §10.

**Owner:** Foreground Orchestrator dispatches Code Reviewer + Reality Checker + Senior Developer in parallel.

**Inputs:** All Phase 1 notebook + report + pickle outputs.

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/phase_1_review.md` with 3-reviewer verdicts.

**Success criteria:** All three PASS-WITH-AT-MOST-NITS; any BLOCK halts and re-dispatches Backend Architect for fixes.

**Dependencies:** Task 1.4 complete.

**Typed-exception triggers in scope:** None at review; reviewers may surface a `Stage2PathAFrameworkInternallyInconsistent` HALT-disposition if Phase 1 outputs do not actually satisfy the spec.

---

### Phase 2 — v1 Mento+Uniswap fork (Celo)

#### Task 2.1: Failing-test scaffold for v1 exit criteria

**Goal:** Per `feedback_strict_tdd`, write a failing test suite encoding the spec §2 v1 exit criterion: (a) ±5% relative-error agreement between v1-realized `CF^(a_l)` and v0 analytic prediction at three pinned `(ε, ω)` grid points (small / medium / large ε); (b) sign-of-`CF^(a_l)`-slope strictly positive at all three points.

**Inputs:** Spec §2 v1 exit criterion; v0 outputs from Phase 1 (read-only).

**Owner:** Senior Developer (TDD discipline) with Backend Architect consultation on harness-shape.

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/tests/test_v1_exit_criteria.py` — pytest suite with 2 sub-test groups (a + b), all FAILING.

**Success criteria:** Test suite imports cleanly; both sub-tests produce explicit FAIL referencing spec §2 v1.

**Dependencies:** Phase 1 PASS.

**Typed-exception triggers in scope:** None — local test scaffold.

#### Task 2.2: v1 fork manifest + pool-address resolution

**Goal:** Pin Celo mainnet fork-block height; resolve the Mento USDm/COPm FPMM pool address at fork-block height (per FLAG-F2 resolution); resolve the Uniswap V3 Celo USDC/USDm pool address at the same fork-block height; record the §10.1 PRIMARY/FALLBACK RPC ladder selection with rate-limit-headroom note.

**Inputs:** Spec §3 v1 inputs (Mento V3 router `0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`, Mento V2 COPM `0x8A567e2aE79CA692Bd748aB832081C45de4041eA`); spec §10.1 RPC ladder.

**Owner:** Backend Architect (Mento + Uniswap protocol expertise).

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v1_fork_manifest.md` — Anvil fork-block height + chainId 42220 + RPC selection + resolved USDm/COPm pool address + resolved USDC/USDm pool address + Foundry/Anvil version pin from Phase 0 manifest + gas-price determinism strategy choice (one of the three options in §10.2).

**Success criteria:**
- Manifest is committable as a CORRECTIONS-block-equivalent v1 dispatch artifact per spec §3 v1 (iii).
- Pool-address resolution is reproducible (re-running the resolution at the same fork-block produces the same pool addresses byte-for-byte).
- Rate-limit-headroom note quantifies estimated peak req/sec for the v1 dispatch run vs the 25 req/sec ceiling.

**Dependencies:** Task 2.1 complete (TDD ordering).

**Typed-exception triggers in scope:**
- `Stage2PathAMentoUSDmCOPmPoolMissing` — fires if the USDm/COPm FPMM pool does not exist at fork-block, or has zero liquidity, or canonical Mento V2 COPM is not paired against USDm. Pivots per spec §6 (Mento V2 BiPool / cUSD-cEUR triangulation / Uniswap V3 USDC/USDm fallback).
- `Stage2PathABudgetOverrun` — fires if pool-address resolution requires paid Etherscan/Celoscan API access beyond free-tier ≈5 req/sec.

#### Task 2.3: v1 harness construction (deterministic σ-path driver)

**Goal:** Build the Anvil-fork harness that: (i) forks Celo mainnet at the Task 2.2 pinned block; (ii) iterates `(X/Y)_t(ε,ω)` from v0's deterministic generator over a step grid (per spec §2 v1 the exact step count is implementation-detail; the harness must produce ≥30 steps per `(ε, ω)` point to meaningfully estimate `Σ_t r·|FX_t − FX_{t−1}|`); (iii) at each step, executes a swap on the Mento USDm/COPm FPMM (or Uniswap V3 USDC/USDm fallback if `Stage2PathAMentoUSDmCOPmPoolMissing` fired) sized to drive the pool spot toward the target `(X/Y)_t`; (iv) records realized swap fees per step; (v) emits `path_a_v1_harness.csv` with one row per step.

**Inputs:** Task 2.2 fork manifest; v0 outputs (deterministic generator from Phase 1).

**Owner:** Backend Architect (Anvil-fork + swap-call expertise).

**Outputs:**
- Harness CSV `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v1_harness.csv` with columns `(grid_point_id, t, X_over_Y_target, X_over_Y_realized, swap_fee_realized, cumulative_CF_a_l, sigma_T_running)`.
- Harness source committed under `contracts/.scratch/pair-d-stage-2-path-a/scripts/path_a_v1_harness.{py|sh}` (or equivalent).

**Success criteria:**
- Harness produces ≥30 steps × 3 grid points = 90 rows.
- Realized `X/Y` matches target within harness-tolerance (per §2 v1, tolerance is implementation-detail; if realized swap impact exceeds 5% slippage relative to Mento spot oracle, `Stage2PathAMentoFPMMSlippageExceedsTolerance` fires per §6).
- Harness re-run at the same fork-block produces byte-identical CSV per §10.1 + §10.2.

**Dependencies:** Task 2.2 complete; Phase 1 outputs available (deterministic generator).

**Typed-exception triggers in scope:**
- `Stage2PathAMentoFPMMSlippageExceedsTolerance` — fires if per-step swap realized slippage > 5% relative to Mento spot oracle. Pivots per spec §6 (reduce notional / substitute deeper pool / downgrade to Uniswap V3 USDC/USDm fallback).
- `Stage2PathAAlchemyFreeTierRateLimitExceeded` — fires if heavy-activity sustained > 25 req/sec against Alchemy free-tier endpoint. Pivots per spec §6 (rate-limit harness / switch to FALLBACK / split into chunks / paid-tier escalation under `Stage2PathABudgetOverrun`).
- `Stage2PathAPublicRPCDeterminismDegraded` — fires if FALLBACK public RPC was used and re-run produces non-byte-identical CSV.
- `Stage2PathAGasPriceDriftBeyondReproducibilityBound` — fires if forked gas pricing produces > 0.01% drift across re-runs at the same fork-block.

#### Task 2.4: v1 reconciliation against v0

**Goal:** Compare v1-realized `CF^(a_l)` against v0 analytic prediction at the three pinned `(ε, ω)` grid points per §10.4; verify ±5% relative error AND strictly positive `CF^(a_l)`-slope at each point.

**Inputs:** Task 2.3 harness CSV; Phase 1 v0 sympy-pickled expressions.

**Owner:** Analytics Reporter (notebook-trio discipline) for the reconciliation notebook; Backend Architect on harness-output interpretation if anomalies.

**Outputs:**
- Notebook `04_v1_mento_uniswap_fork.ipynb` — harness execution narrative with trio-checkpoint discipline.
- Notebook `05_v1_reconciliation.ipynb` — reconciliation table with 3 grid points × {analytic, harness, relative-error, slope-sign} columns.
- Markdown report `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v1_reconciliation.md` — final per-grid-point PASS/FAIL table.

**Success criteria:** v1 exit-criteria sub-tests (a) + (b) from Task 2.1 PASS at all three grid points; relative error ≤5%; slope strictly positive.

**Dependencies:** Task 2.3 complete.

**Typed-exception triggers in scope:** `Stage2PathAFrameworkInternallyInconsistent` if v1-realized `CF^(a_l)` does not match v0 analytic within ±5% at the §10.5 grid + reconciled grid points (suggests either harness-bug, pool-data anomaly, or framework-vs-realized mismatch — disposition memo enumerates pivot options).

#### Task 2.5: Phase 2 implementation review (3-way)

**Goal:** Validate v1 outputs satisfy spec §2 v1 exit criteria + §10.4 reconciliation rule + §10.1 PRIMARY/FALLBACK ladder discipline.

**Owner:** Foreground Orchestrator dispatches Code Reviewer + Reality Checker + Senior Developer in parallel.

**Inputs:** All Phase 2 outputs (manifest + harness CSV + reconciliation report + notebooks).

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/phase_2_review.md` with 3-reviewer verdicts.

**Success criteria:** All three PASS-WITH-AT-MOST-NITS; any BLOCK halts and re-dispatches Backend Architect for fixes.

**Dependencies:** Task 2.4 complete.

**Typed-exception triggers in scope:** None at review; reviewers may surface fresh HALT-disposition memos if a §6 typed exception was missed.

---

### Phase 3 — v2 Panoptic IronCondor strip (Ethereum)

#### Task 3.1: Failing-test scaffold for v2 exit criteria

**Goal:** Per `feedback_strict_tdd`, write a failing test suite encoding the spec §2 v2 exit criterion: (a) `Π_realized(σ_T)` matches v0 analytic `K̂·σ_T` per §11.b (5% relative error) at the v1 grid points; (b) `K_l = K_s` numerical drift per §11.a (machine-epsilon × N_legs).

**Inputs:** Spec §2 v2 exit criterion; spec §11.a + §11.b; v0 + v1 outputs (read-only).

**Owner:** Senior Developer (TDD discipline) with Backend Architect consultation.

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/tests/test_v2_exit_criteria.py` — pytest suite with 2 sub-test groups, all FAILING.

**Success criteria:** Test suite produces explicit FAIL referencing spec §2 v2 + §11.a + §11.b.

**Dependencies:** Phase 2 PASS.

**Typed-exception triggers in scope:** None.

#### Task 3.2: v2 fork manifest + Panoptic deployment resolution

**Goal:** Pin Ethereum mainnet fork-block height within ±24h of the Phase 2 Celo fork-block height (per §3 v2); resolve canonical Panoptic contract addresses at the pinned Ethereum block height; pin the §10.1 PRIMARY/FALLBACK Ethereum RPC ladder (PRIMARY = Alchemy free-tier Ethereum; FALLBACK = `https://eth.llamarpc.com` or `https://rpc.ankr.com/eth`); record archive-depth feasibility check per `Stage2PathAArchiveNodeDepthInsufficientFree`.

**Inputs:** Spec §3 v2 inputs; spec §10.1 Ethereum RPC ladder; Phase 2 Celo fork-block-height pin.

**Owner:** Backend Architect (Panoptic + Ethereum-archive expertise).

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v2_fork_manifest.md` — Anvil fork-block height + chainId 1 + RPC selection + Panoptic contract addresses + Foundry/Anvil version pin + gas-price determinism strategy + archive-depth feasibility note.

**Success criteria:**
- Manifest documents that PRIMARY Alchemy free-tier Ethereum endpoint can satisfy archive-depth state reads at the pinned block within the available compute-unit budget; OR documents the fallback path AND triggers `Stage2PathAArchiveNodeDepthInsufficientFree` for orchestrator adjudication.
- Cross-chain block-height drift ≤24h between Celo and Ethereum forks.

**Dependencies:** Task 3.1 complete.

**Typed-exception triggers in scope:**
- `Stage2PathACrossChainBridgingRequired` — fires if Panoptic-on-Ethereum cannot reference a Mento Celo-side pool without bridging AND no Panoptic-on-Celo deployment exists at v2 fork-block. Pivots per spec §6 (Uniswap V3 Ethereum FX-proxy / defer v2 to partial-PASS / sandbox-only mock-bridging oracle).
- `Stage2PathAArchiveNodeDepthInsufficientFree` — fires per spec §6 if free-tier providers cannot honor archive-depth reads. Pivots per spec §6 (re-pin block height / cache aggressively / substitute free-tier archive provider / paid-tier escalation / descope window / defer v2).

#### Task 3.3: v2 strip configuration (3 condors / 12 legs)

**Goal:** Construct the Carr-Madan strip configuration per §10.5: 3 IronCondor positions × 4 legs each = 12 legs total; left-tail / ATM / right-tail strike regions; strikes per `K_j ≈ S₀·exp(x_j)` with `x_j` uniform on `[-x_max, +x_max]`, `x_max` chosen per §11.b truncation-bound target; weights `w_j ∝ 1/K_j²`. Pre-deployment dry-run: verify all 12 legs are constructible at the pinned Ethereum fork-block (i.e., Panoptic supports IronCondors at the chosen strikes with non-zero open interest / pool depth).

**Inputs:** Task 3.2 fork manifest; v0 outputs (analytic strike-grid derivation from Phase 1); spec §10.5.

**Owner:** Backend Architect (Panoptic strip-construction expertise).

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v2_strip_config.json` — 12 strikes + 12 weights + 3 condor geometries + position-by-position leg assignment per FLAG-F3 + chosen `S₀` reference (current month-end COP/USD on the pinned Ethereum block, sourced via the Mento spot oracle from the Phase 2 Celo fork or via the v2 §6 cross-chain pivot-iii sandbox-mock if `Stage2PathACrossChainBridgingRequired` fired).

**Success criteria:**
- All 12 legs are constructible at the pinned Ethereum fork-block per the dry-run.
- Strike-grid + weights match the §10.5 prescription byte-for-byte (re-running the construction at the same fork-block produces the same JSON).

**Dependencies:** Task 3.2 complete.

**Typed-exception triggers in scope:**
- `Stage2PathAPanopticStripIlliquidOnFork` — fires if Panoptic shows insufficient liquidity at the constructed strikes (zero open interest at left-tail or right-tail; pool depth below position notional). Pivots per spec §6 (shrink to ATM-only condor / substitute more-liquid pool / defer v2).

#### Task 3.4: v2 harness execution + premium time-series

**Goal:** Drive the v0 deterministic σ-path through the v2 strip (3 condors × 4 legs); at each path step, value the strip per its on-chain state (premium = sum of leg-by-leg Panoptic premium reads); emit premium time-series CSV.

**Inputs:** Task 3.2 fork manifest; Task 3.3 strip config JSON; v0 deterministic generator + analytic strip closed-form.

**Owner:** Backend Architect.

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v2_premium_timeseries.csv` with columns `(grid_point_id, t, sigma_T_target, sigma_T_realized, premium_realized, K_hat_sigma_T_analytic, relative_error)`.

**Success criteria:**
- Premium time-series produced at three grid points × ≥30 steps = 90 rows.
- Re-run at the same fork-block produces byte-identical CSV per §10.1 + §10.2.

**Dependencies:** Task 3.3 complete.

**Typed-exception triggers in scope:**
- `Stage2PathAPanopticStripIlliquidOnFork` (escalated from dry-run if liquidity exhausts mid-execution).
- `Stage2PathAAlchemyFreeTierRateLimitExceeded` (heavy-activity v2 may breach 25 req/sec on Ethereum endpoint).
- `Stage2PathAArchiveNodeDepthInsufficientFree` (cumulative compute-unit budget may exhaust mid-execution).
- `Stage2PathAPublicRPCDeterminismDegraded` (if FALLBACK was used).
- `Stage2PathAGasPriceDriftBeyondReproducibilityBound`.

#### Task 3.5: v2 fit report + K_l = K_s reconciliation

**Goal:** Reconcile v2 realized `Π_realized(σ_T)` against v0 analytic `K̂·σ_T` per §11.b at three grid points; reconcile `K_l = K_s` per §11.a (numerical drift only — algebraic equality enforced by equilibrium derivation; numerical drift bounded by machine-epsilon × N_legs = 12).

**Inputs:** Task 3.4 premium time-series; Phase 1 v0 outputs.

**Owner:** Analytics Reporter (notebook-trio discipline).

**Outputs:**
- Notebook `06_v2_panoptic_strip_fork.ipynb` — harness narrative with trio-checkpoint discipline.
- Notebook `07_v2_fit.ipynb` — reconciliation table.
- Markdown report `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v2_fit.md` — per-grid-point `Π_realized` vs `K̂·σ_T` envelope (§11.b) + `K_l = K_s` numerical-drift check (§11.a).

**Success criteria:** v2 exit-criteria sub-tests (a) + (b) from Task 3.1 PASS; §11.a self-consistency holds; §11.b 5% truncation bound holds.

**Dependencies:** Task 3.4 complete.

**Typed-exception triggers in scope:** `Stage2PathAFrameworkInternallyInconsistent` if reconciliation fails at the §10.5 grid + GBM σ₀ ≈ 10% baseline.

#### Task 3.6: Phase 3 implementation review (3-way)

**Goal:** Validate v2 outputs satisfy spec §2 v2 + §10.5 + §11.a + §11.b; verify §10.1 RPC ladder discipline + archive-depth feasibility documented honestly.

**Owner:** Foreground Orchestrator dispatches Code Reviewer + Reality Checker + Senior Developer in parallel.

**Inputs:** All Phase 3 outputs.

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/phase_3_review.md` with 3-reviewer verdicts.

**Success criteria:** All three PASS-WITH-AT-MOST-NITS.

**Dependencies:** Task 3.5 complete.

**Typed-exception triggers in scope:** None at review; reviewers may surface fresh HALT-disposition memos.

---

### Phase 4 — v3 stochastic-σ MC (GBM baseline)

#### Task 4.1: Failing-test scaffold for v3 exit criteria

**Goal:** Per `feedback_strict_tdd`, write a failing test suite encoding spec §2 v3 exit criterion (per active variant): (a) P&L mean tracks `K̂·E[σ_T]` per §11.b; (b) 5th-95th percentile envelope brackets the analytic `K·√σ_T` curve at ≥95% of sampled `σ_T` values.

**Inputs:** Spec §2 v3 exit criterion; spec §10.3 RNG seed pin requirements; spec §11.b.

**Owner:** Senior Developer (TDD discipline).

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/tests/test_v3_exit_criteria.py` — pytest suite with 2 sub-test groups, all FAILING. Tests parameterized over active variants (GBM always; OU/jump-diffusion/empirical conditional on §6 escalation status).

**Success criteria:** Test suite produces explicit FAIL referencing spec §2 v3 + §11.b.

**Dependencies:** Phase 3 PASS.

**Typed-exception triggers in scope:** None.

#### Task 4.2: GBM baseline calibration + RNG-seed manifest

**Goal:** Calibrate GBM parameters (drift μ, volatility σ_BM) to the v1 deterministic-path range per FLAG-F4 baseline pin; pin per-variant RNG seeds via `numpy.random.default_rng(seed=...)` (NEVER legacy `numpy.random.seed()` — see §10.3); pin path count `N ≥ 1000`; record everything in the v3 reproducibility manifest.

**Inputs:** Phase 2 v1 outputs (deterministic-path range from harness CSV); spec §10.3.

**Owner:** Backend Architect (GBM calibration expertise) with Analytics Reporter on the manifest.

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v3_reproducibility_manifest.md` — μ, σ_BM, N, pinned per-variant seed (GBM seed always; OU + jump-diffusion + empirical seeds populated only if §6 escalation triggers); grep-verification line confirming zero global-state RNG calls per spec §10.3.

**Success criteria:**
- Calibration produces μ, σ_BM values consistent with v1 deterministic-path empirical range.
- RNG-seed pin survives a re-run byte-identity check.
- Grep verification confirms no `numpy.random.seed(...)` calls anywhere in the v3 codebase.

**Dependencies:** Task 4.1 complete; Phase 2 v1 outputs available.

**Typed-exception triggers in scope:** None at calibration; downstream v3 dispatch may trigger `Stage2PathAStochasticEnvelopeBreached`.

#### Task 4.3: v3 GBM MC harness execution

**Goal:** Run N ≥ 1000 GBM paths under the Task 4.2 RNG seed; at each path × step, compute realized CPO P&L using the v2 strip closed-form (re-using v2's analytic premium function — does NOT re-fork v2 unless v3 manifest pins "no-fork v3" alternative per §10.1 v3 posture); emit per-path P&L distribution.

**Inputs:** Task 4.2 calibration manifest; Phase 3 v2 strip closed-form (cached from `path_a_v2_strip_config.json` + `path_a_v2_premium_timeseries.csv`).

**Owner:** Backend Architect (MC harness expertise).

**Outputs:**
- Per-variant histogram: `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v3_mc_distributions/gbm/histogram.csv` (1000+ rows of per-path P&L).
- Histogram visualization: `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v3_mc_distributions/gbm/histogram.png`.
- Quantile summary: `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v3_mc_distributions/gbm/quantiles.json` (5th, 25th, 50th, 75th, 95th percentile P&L).

**Success criteria:**
- N ≥ 1000 paths committed.
- Re-run produces byte-identical histogram per §10.3.
- Per-path payoff computed two ways agrees per §11.a (machine-epsilon × N_legs).

**Dependencies:** Task 4.2 complete.

**Typed-exception triggers in scope:** `Stage2PathAStochasticEnvelopeBreached` (deferred to envelope-audit step in Task 4.4 — Task 4.3 just produces the distribution).

#### Task 4.4: v3 envelope-coverage audit + GBM PASS / escalation decision

**Goal:** Compute envelope-coverage statistic: at how many of the sampled `σ_T` values does the 5th-95th percentile P&L envelope bracket the analytic `K·√σ_T` curve? Compare to ≥95% threshold per spec §2 v3. If GBM PASSES, exit Phase 4. If GBM FAILS, trigger `Stage2PathAStochasticEnvelopeBreached` and surface disposition memo per spec §6 (escalate to GBM + OU; further to GBM + OU + jump-diffusion; further to regime-switching; descope envelope to ≥80% with explicit acknowledgement; or partial-PASS exit).

**Inputs:** Task 4.3 distributions; v0 analytic `K·√σ_T` from Phase 1; spec §2 v3 + §6 + §11.b.

**Owner:** Analytics Reporter (notebook-trio discipline) for the audit notebook; Backend Architect on escalation-pivot if §6 triggers.

**Outputs:**
- Notebook `08_v3_gbm_baseline.ipynb` — MC narrative with trio-checkpoint discipline.
- Notebook `09_v3_envelope_audit.ipynb` — envelope-coverage statistic + PASS/escalation decision.
- Markdown report `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v3_envelope_coverage.md`.
- Per-variant disposition memo if §6 escalation triggers: `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v3_escalation_disposition.md` (only created if envelope-coverage < 95%).

**Success criteria:** v3 exit-criteria sub-tests (a) + (b) from Task 4.1 PASS for GBM baseline; OR explicit `Stage2PathAStochasticEnvelopeBreached` HALT with user-adjudicated disposition.

**Dependencies:** Task 4.3 complete.

**Typed-exception triggers in scope:** `Stage2PathAStochasticEnvelopeBreached` per spec §6.

#### Task 4.5: Optional Path B v1 empirical-σ-distribution coupling check

**Goal:** Per spec §12 cross-path coupling: check if Path B v1 has landed at v3 dispatch time. If yes, ingest the empirical σ-distribution as a READ-ONLY feed and run a fourth v3 variant ("empirical_calibrated") alongside the GBM baseline. If no, document the skip and proceed with GBM-only (plus any §6 escalation variants if Task 4.4 triggered them).

**Inputs:** Spec §12 coupling table; Path B v1 output if it exists at dispatch time (path: per Path B spec — NOT this plan's responsibility to author).

**Owner:** Analytics Reporter (coupling-check notebook); Backend Architect (empirical variant calibration if active).

**Outputs:**
- Decision artifact: `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v3_path_b_coupling_check.md` — explicit "Path B v1 landed: yes/no" + rationale + (if yes) ingested-data-source pin.
- (Conditional) Per-variant histogram + quantile summary under `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_v3_mc_distributions/empirical_calibrated/` mirroring the GBM structure.

**Success criteria:**
- Coupling decision is explicit and auditable.
- If empirical variant runs, it satisfies the same §10.3 RNG-seed pin discipline as GBM.

**Dependencies:** Task 4.4 complete.

**Typed-exception triggers in scope:** None at this step; the empirical variant if active inherits all v3 typed exceptions.

#### Task 4.6: Phase 4 implementation review (3-way)

**Goal:** Validate v3 outputs satisfy spec §2 v3 + §10.3 + §11.b; verify cross-path coupling decision was honestly recorded per §12.

**Owner:** Foreground Orchestrator dispatches Code Reviewer + Reality Checker + Senior Developer in parallel.

**Inputs:** All Phase 4 outputs.

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/phase_4_review.md` with 3-reviewer verdicts.

**Success criteria:** All three PASS-WITH-AT-MOST-NITS.

**Dependencies:** Task 4.4 (and Task 4.5 if Path B v1 coupling activated).

**Typed-exception triggers in scope:** None at review.

---

### Phase 5 — Convergence + verdict authoring

#### Task 5.1: Per-rung exit-criterion audit

**Goal:** Audit all four rungs (v0 + v1 + v2 + v3) against their pre-pinned exit criteria from spec §2; verify per-version manifest reproducibility (re-run produces byte-identical artifacts per §10); verify all triggered §6 typed exceptions have associated disposition memos with user-adjudicated CORRECTIONS-blocks (no auto-pivot per `feedback_pathological_halt_anti_fishing_checkpoint`).

**Inputs:** All Phase 1 + 2 + 3 + 4 outputs; per-phase review reports.

**Owner:** Reality Checker (audit-discipline owner) — fresh instance not previously involved in any Phase 1-4 review per the freshness convention.

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_per_rung_audit.md` — per-rung PASS/FAIL/PARTIAL-PASS table with explicit citation of each exit criterion + each typed-exception disposition trail.

**Success criteria:** Audit table is exhaustive (every exit criterion + every fired typed exception accounted for).

**Dependencies:** Phase 4 complete.

**Typed-exception triggers in scope:** None at audit.

#### Task 5.2: Path A verdict memo + machine-readable verdict JSON

**Goal:** Compose Path A result memo `path_a_verdict_memo.md` mirroring the Pair D Stage-1 MEMO §1-§10 structure; emit machine-readable `path_a_verdict.json`.

**Inputs:** Task 5.1 audit; all Phase 1-4 outputs.

**Owner:** Analytics Reporter (memo-authoring); Backend Architect on technical-substantive review.

**Outputs:**
- `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_verdict_memo.md` — sections: §1 Spec sha pin + Stage-1 PASS verdict pin (READ-ONLY anchor); §2 Per-rung exit-criterion summary; §3 Sample of CF^(a_l) realized vs analytic at three grid points; §4 §10.5 strip configuration summary; §5 §11.a + §11.b reconciliation table; §6 v3 envelope-coverage statistic; §7 Path B coupling decision (per §12); §8 Triggered typed exceptions (if any) + disposition trail; §9 Honest interpretation: did fork-and-simulate verification confirm the framework's analytical claims?; §10 Implications for Path B convergence dispatch + Stage-3 entry-gate readiness.
- `contracts/.scratch/pair-d-stage-2-path-a/results/path_a_verdict.json` — fields: `spec_sha256`, `per_rung_status` (object with v0/v1/v2/v3 values), `stage_1_anchor_sha`, `path_b_coupling_active`, `triggered_typed_exceptions` (list), `convergence_dispatch_unblocked` (boolean), `stage_3_entry_gate_status` ("not unlocked by Path A alone — convergence dispatch required").

**Success criteria:**
- Memo §9 honestly interprets the per-rung outcomes; no narrative softening of any FAIL or PARTIAL-PASS per `feedback_pathological_halt_anti_fishing_checkpoint` posture.
- JSON parses cleanly and matches memo §1-§10 facts byte-for-byte.

**Dependencies:** Task 5.1 complete.

**Typed-exception triggers in scope:** None at memo authoring.

#### Task 5.3: Phase 5 three-way implementation review

**Goal:** Per `feedback_implementation_review_agents`, dispatch Code Reviewer + Reality Checker + Senior Developer in parallel on the full Path A artifact bundle (all phases + Phase 5 verdict memo + JSON).

**Owner:** Foreground Orchestrator dispatches.

**Inputs:** All Path A artifacts.

**Outputs:** `contracts/.scratch/pair-d-stage-2-path-a/phase_5_review.md` — three-reviewer verdict matrix.

**Success criteria:**
- Code Reviewer PASS-WITH-AT-MOST-NITS on notebook + script implementation.
- Reality Checker PASS-WITH-AT-MOST-FLAGS on memo + JSON evidence-grounding.
- Senior Developer PASS-WITH-AT-MOST-REMEDIATION on production-readiness ("could a fresh engineer re-run with only the spec + this artifact bundle?").
- Any BLOCK-severity defect halts and re-dispatches Backend Architect for fixes; per the implementation-review-agents convention.

**Dependencies:** Task 5.2 complete.

**Typed-exception triggers in scope:** None.

#### Task 5.4: Final commit + CLAUDE.md update + Path B convergence handoff

**Goal:** Apply review revisions (only those that don't change verdict, tune thresholds, or re-derive any quantity); commit Path A artifact bundle with `Doc-Verify: cr=<id>/rc=<id>/sd=<id>` 3-way trailer per Phase 5 convention; update CLAUDE.md "Pair D" Active iteration block with Path A verdict + Stage-2 Path A → convergence-dispatch handoff pointer; CLAUDE.md edit triggers Reality Checker + Workflow Architect 2-wave per `feedback_two_wave_doc_verification`.

**Owner:** Foreground Orchestrator.

**Inputs:** Phase 5 outputs.

**Outputs:**
- Final commit of `contracts/.scratch/pair-d-stage-2-path-a/` with 3-way trailer.
- CLAUDE.md update with 2-wave trailer.
- Memory entry: `~/.claude/.../memory/project_pair_d_stage_2_path_a_complete.md` (per Stage-1 precedent — memory writes are out of scope for the 2-wave rule).

**Success criteria:**
- Commit lands cleanly on `phase0-vb-mvp` branch (push to **origin** per `feedback_push_origin_not_upstream`, NEVER upstream).
- CLAUDE.md diff is reviewed by RC + WA before commit; both PASS-WITH-AT-MOST-NITS.
- Memory entry captures verdict + key sha pins + per-rung status for future-session resume.

**Dependencies:** Task 5.3 PASS.

**Typed-exception triggers in scope:** None.

---

## §4. Dependency graph

The plan executes as a topologically-ordered DAG. Phase boundaries are sequential gates; within each phase, some tasks may parallelize.

```text
Phase 0 (bootstrap)
  Task 0.1 (Foundry pin)  ───┐
                              ├──→ Task 0.3 (Phase 0 review)
  Task 0.2 (Python+nb pin) ───┘

Phase 0 review PASS
  ↓
Phase 1 (v0 sympy)
  Task 1.1 (failing tests)
    ↓
  Task 1.2 (Notebook 01: Δ derivation)
    ↓
  Task 1.3 (Notebook 02: Π + Carr-Madan strip)
    ↓
  Task 1.4 (Notebook 03: v0 exit report)
    ↓
  Task 1.5 (Phase 1 review)

Phase 1 review PASS
  ↓
Phase 2 (v1 Mento+Uniswap fork)
  Task 2.1 (failing tests)
    ↓
  Task 2.2 (v1 fork manifest + pool resolution)
    ↓
  Task 2.3 (v1 harness execution)
    ↓
  Task 2.4 (v1 reconciliation vs v0)
    ↓
  Task 2.5 (Phase 2 review)

Phase 2 review PASS
  ↓
Phase 3 (v2 Panoptic strip on Ethereum)
  Task 3.1 (failing tests)
    ↓
  Task 3.2 (v2 fork manifest + Panoptic resolution)
    ↓
  Task 3.3 (v2 strip config: 3 condors / 12 legs)
    ↓
  Task 3.4 (v2 harness execution + premium time-series)
    ↓
  Task 3.5 (v2 fit report + K_l = K_s reconciliation)
    ↓
  Task 3.6 (Phase 3 review)

Phase 3 review PASS
  ↓
Phase 4 (v3 GBM MC)
  Task 4.1 (failing tests)
    ↓
  Task 4.2 (GBM calibration + RNG-seed manifest)
    ↓
  Task 4.3 (v3 GBM MC harness execution)
    ↓
  Task 4.4 (v3 envelope-coverage audit + GBM PASS / escalation)
    ↓
  Task 4.5 (Path B v1 coupling check — OPTIONAL conditional)
    ↓
  Task 4.6 (Phase 4 review)

Phase 4 review PASS
  ↓
Phase 5 (convergence + verdict)
  Task 5.1 (per-rung exit-criterion audit)
    ↓
  Task 5.2 (verdict memo + JSON)
    ↓
  Task 5.3 (3-way implementation review)
    ↓
  Task 5.4 (final commit + CLAUDE.md update + handoff)
```

**Parallelizable opportunities:**
- Phase 0: Tasks 0.1 and 0.2 are independent and may dispatch in parallel (one Senior Developer for Foundry, one Analytics Reporter for Python+notebook scaffolding).
- Within each Phase 1-5 review (Tasks 0.3, 1.5, 2.5, 3.6, 4.6, 5.3): Code Reviewer + Reality Checker + Senior Developer dispatch in parallel per `feedback_implementation_review_agents`.
- All other intra-phase tasks are sequential (TDD ordering forces failing-test-first; harness output feeds reconciliation; manifest pins precede execution).

**Cross-phase parallelism:** None permitted. Each phase gates the next at its review-PASS boundary; Phase N+1 dispatch is anti-fishing-banned before Phase N review PASSes (otherwise rung exit criteria are unverified inputs to the next rung).

---

## §5. Reproducibility discipline

Per spec §10 BLOCK-D1 resolution, every per-version output must be byte-identical on re-run from the pinned configuration. This plan enforces the discipline at three levels.

**Level 1 — Per-version manifests (REQUIRED per phase using a fork).** Phase 2 produces `results/path_a_v1_fork_manifest.md` per Task 2.2; Phase 3 produces `results/path_a_v2_fork_manifest.md` per Task 3.2; Phase 4 produces `results/path_a_v3_reproducibility_manifest.md` per Task 4.2. Each manifest enumerates: fork block height + chainId, RPC source ladder selection (PRIMARY/FALLBACK), Foundry/Anvil version pin (commit hash), gas-price determinism strategy choice (one of three options in §10.2), and (for v3) per-variant RNG seed.

**Level 2 — Byte-identical artifact rule (per §10.2 + §10.3).** Every CSV, JSON, parquet, pickle, or histogram artifact produced by Phases 2-4 must hash byte-identically across re-runs from the manifest. Re-run failures trigger `Stage2PathAGasPriceDriftBeyondReproducibilityBound` (fork-related) or `Stage2PathAPublicRPCDeterminismDegraded` (RPC-related) per spec §6; HALT-disposition with ≥3 user-adjudicated pivots required before proceeding. Phase 5 Task 5.1 audit must include re-run hash verification for at least one randomly-selected artifact per rung.

**Level 3 — RNG seed pinning (per §10.3, v3 specifically).** v3 stochastic-σ MC uses `numpy.random.default_rng(seed=<pinned-seed>)` exclusively; legacy `numpy.random.seed()` global state is BANNED. Each active variant (GBM always; OU/jump-diffusion/empirical only if active) carries its own pinned seed in the v3 reproducibility manifest. The harness must include a grep-verification line confirming zero legacy global-state RNG calls anywhere in the v3 codebase. Re-run with the same seed-and-N pair must produce identical histograms byte-for-byte.

**Anti-fishing discipline (per `feedback_pathological_halt_anti_fishing_checkpoint`).** Fork block heights are NEVER changed mid-version without a fresh CORRECTIONS-block and re-execution of all downstream artifacts (per spec §10.1). RPC source ladder switches (PRIMARY → FALLBACK) within a version do NOT trigger CORRECTIONS-block but DO trigger the relevant typed exception AND require re-verification of byte-identical artifacts.

---

## §6. Free-tier-only budget enforcement

Per spec §5 + CORRECTIONS-δ, every phase must declare projected free-tier resource consumption at dispatch time and verify against the available budget. **No auto-pivot to paid services** — `Stage2PathABudgetOverrun` triggers HALT for user adjudication before any paid-tier escalation.

**Per-phase free-tier resource projection (executor responsibility at dispatch):**

- **Phase 0:** Local compute only (Foundry install + Python venv setup). Alchemy free-tier app-creation overhead ≈0 CU. Public RPC reachability check ≈10 RPC calls total. **Projected free-tier cost: negligible.**

- **Phase 1:** Pure-Python local compute (sympy + numpy + scipy). No fork operations. **Projected free-tier cost: zero.**

- **Phase 2:** v1 Anvil fork against Celo mainnet at pinned block. Per-grid-point harness ≈30 steps × 3 grid points = 90 swaps + 90 spot-oracle reads + manifest-time pool-address resolution ≈ 200 RPC calls. Estimated peak req/sec ≤5 (well under 25 req/sec ceiling per §10.1). Compute-unit burn ≈ 200 calls × ~50 CU/call = ~10K CU per dispatch run. **Projected free-tier cost: 10K CU per Phase 2 run; budget headroom on Alchemy free-tier ≈30M CU/month ≫ 10K.**

- **Phase 3:** v2 Anvil fork against Ethereum mainnet at pinned block (archive-depth read for Panoptic state). Per-grid-point harness ≈30 steps × 3 grid points × 12 legs = 1080 leg-premium reads + manifest-time Panoptic-address resolution + dry-run liquidity check ≈ 1500 RPC calls. Archive-depth state reads are heavier (~200 CU/call vs ~50 CU/call for head-state). Compute-unit burn ≈ 1500 × 200 = ~300K CU per dispatch run; budget headroom ≈30M/month / 300K ≈ ≤100 dispatch runs/month. **Projected free-tier cost: 300K CU per Phase 3 run.** Risk: re-run debugging may multiply this; Task 3.2 manifest must record CU baseline before Phase 3 starts and check post-run consumption against budget.

- **Phase 4:** v3 GBM MC is pure-local-compute (no fork operations per spec §10.1 v3 posture "no-fork v3 preferred under free-tier budget"). **Projected free-tier cost: zero.** If §6 escalation triggers OU/jump-diffusion/empirical variants and the empirical variant requires re-fork against Ethereum, recompute Phase 3 budget projection.

- **Phase 5:** No fork operations; pure documentation + 3-way review. **Projected free-tier cost: zero.**

**Per-task surfacing requirement (per `feedback_pathological_halt_anti_fishing_checkpoint`):** at dispatch time, the executor must record the per-task estimated CU consumption AND the post-task actual consumption in the relevant manifest (`environment_manifest.md` for Phase 0; `path_a_v1_fork_manifest.md` for Phase 2; `path_a_v2_fork_manifest.md` for Phase 3). If actual exceeds estimated by > 2x, HALT and surface to orchestrator before next phase.

**Paid-tier escalation HALT protocol (per `Stage2PathABudgetOverrun`):** any task that requires paid Alchemy upgrade, paid Etherscan/Celoscan API beyond ≈5 req/sec, paid Tenderly tier, paid simulation-fork service, paid decompilation API, or per-call-pricing oracle with non-trivial usage MUST surface a HALT-disposition memo with the explicit paid figure, scope, and justification. User adjudication is REQUIRED before any paid-tier dispatch. Auto-escalation is anti-fishing-banned.

---

## §7. Cross-path coordination

Per spec §12 input-by-input coupling pin: **DEFAULT IS INDEPENDENT.** Path A v0 + v1 + v2 are fully independent of Path B at every input. The only coupling point is Task 4.5 (Phase 4): Path A v3's OPTIONAL empirical-σ-distribution variant ingests a READ-ONLY feed from Path B v1 IF Path B v1 has landed by Phase 4 dispatch time.

**This plan does NOT plan for Path B execution.** Path B has its own spec (`contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md`, sha `4e8905a9…`, v1.3) and its own implementation plan (separately authored, NOT this plan's responsibility).

**Coordination touchpoint (Task 4.5):**
- The orchestrator dispatching Phase 4 must check (one-shot, not blocking) whether the Path B v1 output exists at the canonical Path B output location at the time Phase 4 starts.
- If yes: Task 4.5 ingests the Path B v1 σ-distribution as READ-ONLY and runs the empirical_calibrated v3 variant alongside the GBM baseline. The Path B output sha is pinned in the Task 4.5 decision artifact.
- If no: Task 4.5 documents the skip explicitly and Phase 4 proceeds with GBM-only (plus any §6 escalation variants if Task 4.4 triggered them).

**No back-pressure from Path A to Path B.** Path A does NOT delay or accelerate Path B; Path A v3 PASSes or escalates per its own envelope-coverage statistic on the GBM baseline regardless of Path B's state.

**Convergence dispatch is downstream.** Cross-path reconciliation (does Path A's harness-realized CF^(a_l) match Path B's on-chain-realized CF^(a_l) within tolerance?) is the convergence-dispatch's job, NOT this plan's. Path A's exit gate is its own per-rung audit (Phase 5 Task 5.1) and 3-way review (Task 5.3) PASS — Stage-3 entry-gate readiness is signaled by the convergence dispatch closing successfully, NOT by Path A alone.

---

## §8. Self-review checklist

Run by the orchestrator before commit of THIS plan.

**Placeholder scan:** zero "TBD" / "TODO" / "fill in details" / "similar to Task N" / "implement appropriate handling". Every task names a specialist deliverable or dispatches with explicit charge per `feedback_specialized_agents_per_task`. **To be verified at orchestrator review.**

**Code-agnosticism (per `feedback_no_code_in_specs_or_plans`):** zero executable code blocks; only `text` blocks containing pseudo-code (DAG diagram in §4) or configuration parameter lists (no Solidity, no Python, no Bash actually intended for execution); equation notation in §1-§3 is methodology specification per the spec's own discipline. **To be verified at orchestrator review.**

**Contradictions (per `feedback_pathological_halt_anti_fishing_checkpoint` posture):** zero internal contradictions. The free-tier-only budget pin is consistent across §1, §3, §6 budget enforcement; the spec sha pin `1a4cc6a4…` is consistent across frontmatter, §1, §3 task references, §5 reproducibility discipline. The Stage-1 PASS verdict pin chain is READ-ONLY everywhere. **To be verified at orchestrator review.**

**Scope creep guardrail:** plan executes Stage-2 Path A only. Stage-2 Path B is explicitly out of scope (§7 documents the coordination touchpoint but does not plan for Path B). Stage-3 deployment is explicitly out of scope (no LP capital, no user onboarding, no KYC, no marketing copy). Convergence dispatch is downstream and authored separately. **Verified — frontmatter + §1 + §7 + Phase 5 Task 5.4 routing.**

**Ambiguity scan:** every task has Goal / Inputs / Owner / Outputs / Success criteria / Dependencies / Typed-exception triggers in scope. Every "Success criteria" entry is binary-evaluable (no "approximately satisfactory" or "reasonably good" language). Every "Typed-exception triggers in scope" enumerates by name from the spec §6 catalogue (11 typed exceptions total). **To be verified at orchestrator review.**

**Specialist coverage (per `feedback_specialized_agents_per_task`):** Tasks 0.1, 1.1, 2.1, 3.1, 4.1 → Senior Developer (TDD + DevOps). Task 0.2 → Analytics Reporter. Tasks 1.2-1.4, 2.4, 3.5, 4.4-4.5, 5.2 → Analytics Reporter (notebook-trio + memo). Tasks 2.2-2.3, 3.2-3.4, 4.2-4.3 → Backend Architect (Mento + Panoptic + Anvil-fork + MC harness). Tasks 0.3, 1.5, 2.5, 3.6, 4.6, 5.3 → Foreground Orchestrator dispatching Code Reviewer + Reality Checker + Senior Developer in parallel. Task 5.1 → Reality Checker (fresh instance). Task 5.4 → Foreground Orchestrator (with RC + WA on CLAUDE.md edit). **Verified.**

**Anti-fishing discipline:** spec sha pin in frontmatter; Stage-1 PASS verdict pin chain READ-ONLY; HALT-disposition path enumerated for every phase via §6 typed-exception inheritance; 3-way implementation review per phase per `feedback_implementation_review_agents`; per-rung exit criteria pre-pinned and not amenable to post-hoc softening; budget pin enforced via §6 with paid-tier escalation requiring user adjudication. **Verified.**

**Strict TDD (per `feedback_strict_tdd`):** every implementation task is preceded by a failing-test-first sub-task. Tasks 1.1, 2.1, 3.1, 4.1 explicitly produce failing test scaffolds before any implementation. **Verified.**

**Type / name consistency:** `path_a_v0_*`, `path_a_v1_*`, `path_a_v2_*`, `path_a_v3_*` artifact-name prefix consistent across §3 outputs and §5 reproducibility discipline; `Stage2PathA*` typed-exception names consistent with spec §6; `K_l = K_s` notation consistent with spec §11.a. **To be verified at orchestrator review.**

**2-wave + 3-way trailer convention:** plan / spec / CLAUDE.md commits use 2-wave `Doc-Verify: wave1=<RC-id> wave2=<WA-id>`; Phase 1-4 notebook commits use orchestrator-only-pre-phase-5 trailer; Phase 5 verdict commit uses 3-way `Doc-Verify: cr=<id>/rc=<id>/sd=<id>`. **Verified — frontmatter + §3 task review steps + §3 Task 5.4.**

---

## §9. Plan validation gates

**Gate A — Pre-execution (this plan, before any task dispatches).** Per `feedback_two_wave_doc_verification`, the orchestrator dispatches Reality Checker (Wave 1) + Workflow Architect (Wave 2) in parallel on this plan BEFORE any Phase 0 task dispatches. Wave 1 charge: evidence grounding (every spec citation actually maps to spec §; every Stage-1 anchor citation actually maps to the Stage-1 sha pin chain; anti-fishing rigor — no soft thresholds, no escape hatches, methodology-pinning honored). Wave 2 charge: workflow integrity (DAG topological soundness, per-task specialist coverage per `feedback_specialized_agents_per_task`, 3-way + 2-wave trailer convention compliance, free-tier budget projection plausibility per §6, cross-path coordination boundary per §7 honestly held). Both waves must PASS-WITH-AT-MOST-NITS before Phase 0 dispatches. Plan revisions (CORRECTIONS-ε, etc.) follow the same protocol on re-dispatch.

**Gate B — Per-phase implementation review (between phases).** Per `feedback_implementation_review_agents`, each phase ends with a 3-way review (Code Reviewer + Reality Checker + Senior Developer) in parallel: Tasks 0.3, 1.5, 2.5, 3.6, 4.6 each represent the gate-B checkpoint for their phase. Backend Architect handles fixes if any reviewer flags BLOCK-severity defects. The next phase does NOT dispatch until the prior phase's gate-B PASSes.

**Gate C — Convergence verdict acceptance (Phase 5).** Task 5.3 is the gate-C 3-way implementation review on the full Path A artifact bundle. Code Reviewer audits notebook + script implementation; Reality Checker audits memo + JSON evidence-grounding; Senior Developer audits production-readiness ("could a fresh engineer re-run with only the spec + this artifact bundle?"). PASS-WITH-AT-MOST-NITS on all three is the convergence gate; any BLOCK halts and re-dispatches Backend Architect. Task 5.4 final commit follows ONLY after gate-C PASS.

**Gate D — CLAUDE.md update (post-Phase 5).** Task 5.4 includes a CLAUDE.md update; the diff is reviewed by Reality Checker + Workflow Architect 2-wave per the v2 default for governance writes (`feedback_two_wave_doc_verification`). Both PASS-WITH-AT-MOST-NITS before commit. Memory entry write is out of scope for the 2-wave rule per Stage-1 precedent.

---

## §10. Execution handoff

Plan complete pending Gate A 2-wave verification per `feedback_two_wave_doc_verification`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — orchestrator dispatches a fresh specialist per task per the named owners, reviews between tasks, mandatory trio-checkpoint HALTs in Phases 1-4 notebook tasks per `feedback_notebook_trio_checkpoint` (NON-NEGOTIABLE), per-phase gate-B review, gate-C convergence review, gate-D CLAUDE.md verification.

2. **Inline Execution** — execute tasks in this session via `superpowers:executing-plans`, batch with checkpoints. Higher context burn; harder to enforce specialist discipline; trio-checkpoint HALT compliance becomes orchestrator-self-discipline rather than fresh-agent-enforced.

**Recommended: Subagent-Driven**, given (a) the trio-checkpoint discipline mandated by `feedback_notebook_trio_checkpoint` for the Phase 1-4 notebook tasks, (b) the multi-specialist design of the plan (Senior Developer + Backend Architect + Analytics Reporter + Code Reviewer + Reality Checker + Workflow Architect — 6 distinct specialist roles), and (c) the free-tier budget enforcement requiring honest per-task surfacing per `feedback_pathological_halt_anti_fishing_checkpoint`.

**Push discipline (per `feedback_push_origin_not_upstream`):** all commits push to **origin** (JMSBPP), NEVER upstream (wvs-finance). Branch is `phase0-vb-mvp`.
