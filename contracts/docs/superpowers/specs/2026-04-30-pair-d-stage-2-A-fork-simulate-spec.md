---
spec_path: pair-d-stage-2-A-fork-simulate
spec_version: v1.2.2 (CORRECTIONS-ε — Ankr Ethereum RPC removal per Phase 0 + Gate B0 RC reproduction)
spec_author: Backend Architect dispatch 2026-04-30; v1.1 revision 2026-05-02; v1.2 revision 2026-05-02 (CORRECTIONS-δ); v1.2.1 micro-edit 2026-05-02 (CORRECTIONS-δ' — Alchemy 300M→30M CU/mo correction in 4 locations per Wave-2 verifier NIT); v1.2.2 micro-edit 2026-05-02 (CORRECTIONS-ε — Backend Architect, removal of stale `rpc.ankr.com/eth` reference now that the endpoint requires API-key authentication, verified by Phase 0 executor + Gate B0 Reality Checker reproduction 2026-05-02)
spec_sha256_v1_0: 56fa06b8222789eb6902227a09661728a899b464bc155036a3328d746d644665
spec_sha256_v1_1: de4e8cdcb1af99d96f7657f7e9b397c8caf9196e59d30d5e9afce8e72265128b
spec_sha256_v1_2: ab65fd2048ed048d56917f3b9ce9c0dec85ebd498a568dd466ec396073b62dd6
spec_sha256_v1_2_1: 1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78
spec_sha256_v1_2_2: <to-be-pinned-by-orchestrator-at-commit-time>
stage1_pinned_chain:
  spec_v1_3_1: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
  panel: 6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf
  primary_ols: d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf
  robustness_pack: 67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904
  verdict: 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf
tooling_budget_pending: false
budget_pin: free_tier_only
tooling_budget_committed: FREE-TIER ONLY (2026-05-02 user directive supersedes 2026-04-30 $49/mo Alchemy Growth pin)
internal_ladder: v0 (sympy) -> v1 (Mento+Uniswap fork) -> v2 (Panoptic strip fork) -> v3 (stochastic sigma MC)
convergence_point: v3 calibration with Path B v1 empirical sigma-distribution (default INDEPENDENT — see §12)
v3_baseline_pinned: GBM (Geometric Brownian Motion) — Ornstein-Uhlenbeck and jump-diffusion are optional escalations
verifier_v1_0_wave1: PASS-WITH-DEFECTS (Reality Checker — 2 BLOCKs / 6 FLAGs)
verifier_v1_0_wave2: PASS-WITH-DEFECTS (Software Architect — overlapping verdict)
verifier_v1_1_wave1: PASS-WITH-NITS
verifier_v1_1_wave2: PASS-WITH-NITS
verifier_v1_2_wave1: PASS-WITH-NITS (Software Architect)
verifier_v1_2_wave2: PASS-WITH-NITS (Software Architect — NIT N1 Alchemy CU figure mismatch addressed by v1.2.1)
verifier_v1_2_1_wave1: PASS-WITH-NITS (closed at v1.2.2 authoring per PR #79 verifier verdicts)
verifier_v1_2_1_wave2: PASS-WITH-NITS (closed at v1.2.2 authoring per PR #79 verifier verdicts)
verifier_v1_2_2_wave1: pending (Reality Checker — 2-wave verification per `feedback_two_wave_doc_verification`)
verifier_v1_2_2_wave2: pending (Software Architect — 2-wave verification per `feedback_two_wave_doc_verification`)
---

# Pair D Stage-2 — Path A "Fork-and-Simulate" Spec

## Change Log v1.2.1 → v1.2.2 (CORRECTIONS-ε)

**Tag.** CORRECTIONS-ε (fifth corrections-block in the Pair D Stage-2 Path A track; α/β/γ remain reserved for the Pair D parent-track sequence).

**Trigger.** Convergent flag from three independent sources during Path A Phase 0 + Gate B0 review (2026-05-02): (i) Phase 0 executor empirically reproduced `https://rpc.ankr.com/eth` returning `-32000: Unauthorized — You must authenticate your request with an API key`; (ii) Gate B0 Reality Checker independently reproduced the same error response; (iii) Gate B0 Code Reviewer NIT #3 + RC FLAG F2 + Senior Developer remediation #2 all pointed at the v1.2.1 §5 + §10.1 enumeration listing `rpc.ankr.com/eth` as a free Ethereum public-RPC fallback. The endpoint is no longer free-tier accessible without authentication, invalidating its standing under the v1.2 CORRECTIONS-δ free-tier-only budget pin.

**Scope.** Prose-only stale-reference scrub. v1.2.1 schema, typed-exception count (11), methodology, BLOCK/FLAG closures (BLOCK-D1 reproducibility, BLOCK-D2 Carr-Madan disambiguation, FLAG-F1 through FLAG-F6), free-tier-only budget pin (CORRECTIONS-δ), Alchemy 30M CU/mo correction (CORRECTIONS-δ'), §10.1 PRIMARY/FALLBACK ladder structure, §11 Carr-Madan disambiguation, §12 cross-path coupling default INDEPENDENT — all preserved verbatim. The v1.2.2 edit surface is exactly four prose locations naming `rpc.ankr.com/eth` plus one indirect reference (the §6 `Stage2PathAArchiveNodeDepthInsufficientFree` pivot iii which lists "Ankr public archive" as an example free-tier alternative).

**Specific deltas applied.**

- **Frontmatter.** `spec_version` v1.2.1 → v1.2.2; `spec_sha256_v1_2_1` pinned to `1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78`; `spec_sha256_v1_2_2` placeholder added; `spec_author` extended with v1.2.2 entry naming Backend Architect 2026-05-02 with empirical-verification basis; v1.2.1 verifier fields flipped from "not-required" → PASS-WITH-NITS (closing the v1.2.1 verification cycle per PR #79 verifier verdicts); v1.2.2 verifier fields set to pending.
- **§5 enumeration (line previously listing `https://eth.llamarpc.com` and `https://rpc.ankr.com/eth`).** Rewritten to single-PRIMARY: `https://eth.llamarpc.com` (verified working by Phase 0 executor + Gate B0 Reality Checker reproduction 2026-05-02). The `rpc.ankr.com/eth` mention is removed; verification basis is documented inline with the date.
- **§10.1 v2 FALLBACK RPC.** Same scrub: `https://eth.llamarpc.com` is now the single named free-tier Ethereum public-RPC fallback; `rpc.ankr.com/eth` removed. Per-rung selection-at-dispatch language unchanged; the typed-exception triggers (`Stage2PathAArchiveNodeDepthInsufficientFree`, `Stage2PathAPublicRPCDeterminismDegraded`) unchanged.
- **§3 v2 inputs enumeration.** Same scrub: enumeration of the §10.1 ladder is updated to drop `rpc.ankr.com/eth` from the FALLBACK list.
- **v1.1 → v1.2 change log §10.1 prose (historical record, line ≈46).** Same scrub for consistency: the historical change-log entry naming both `eth.llamarpc.com` and `rpc.ankr.com/eth` is rewritten to name only `eth.llamarpc.com`. The historical CORRECTIONS-δ deltas remain otherwise unchanged.
- **§6 `Stage2PathAArchiveNodeDepthInsufficientFree` pivot (iii).** "Ankr public archive" example removed from the free-tier-eligible-archive-RPC enumeration; "dRPC free, Chainstack free" retained as remaining example alternatives. Pivot mechanics unchanged.

**No regression of v1.0 → v1.2.1 closures.** BLOCK-D1, BLOCK-D2, FLAG-F1 through FLAG-F6 all preserved. CORRECTIONS-δ free-tier-only budget pin preserved (this CORRECTIONS-ε edit operates *under* that pin by removing a now-non-free endpoint that was incorrectly enumerated as free). CORRECTIONS-δ' Alchemy 30M CU/mo correction preserved verbatim. §10.1 PRIMARY/FALLBACK ladder structure preserved. §11 Carr-Madan disambiguation preserved. §12 cross-path coupling default INDEPENDENT preserved. Typed-exception count remains 11 in §6.

**Anti-fishing posture.** Per `feedback_pathological_halt_anti_fishing_checkpoint`: this is a stale-reference removal, NOT a threshold tuning, NOT a re-derivation of any analytical claim, NOT a substitution of unverified replacement endpoints. The single retained Ethereum free-tier fallback (`eth.llamarpc.com`) was empirically verified by two independent observers; no new free-tier service is introduced without verification.

**Path B coordination note.** Path B uses SQD primary indexer for Ethereum-side data and does NOT depend on the v1.2.1 §5 or §10.1 Ethereum-RPC enumeration; no equivalent CORRECTIONS-ε is required on the Path B spec. The §12 cross-path coupling table remains INDEPENDENT.

---

## Change Log v1.1 → v1.2 (CORRECTIONS-δ)

**Trigger.** User budget directive change post-v1.1 (2026-05-02): the AI-tooling budget is now **FREE-TIER ONLY**. No paid services authorized. The v1.1 frontmatter pin `tooling_budget_committed: $49/mo Alchemy Growth` is invalidated, and every prose reference that depended on Alchemy Growth quotas (archive-node throughput, RPC reliability, request-rate headroom) must be re-derived under free-tier constraints OR routed to a free public RPC alternative with the trade-off documented.

**Scope.** Budget pin scrub only. v1.1 BLOCK/FLAG closures (BLOCK-D1 reproducibility, BLOCK-D2 Carr-Madan disambiguation, FLAG-F1 through FLAG-F6) are NOT regressed. §10.2 library pins, §10.3 RNG pins, §10.4 symbolic-vs-numeric reconciliation, §10.5 Panoptic position-count pin, §11.a / §11.b error metrics, §12 cross-path coupling table — all preserved verbatim. The single edit surface is RPC source pins (§10.1), the budget-overrun typed exception (§6), the tooling stack prose (§5), the self-review pin reference (§9), and three new typed exceptions in §6 surfacing free-tier-specific failure modes.

**Tag.** CORRECTIONS-δ (fourth corrections-block in the Pair D Stage-2 Path A track; α/β/γ are reserved for the Pair D parent-track sequence).

**Specific deltas applied.**

- **Frontmatter.** New field `budget_pin: free_tier_only` added. Field `tooling_budget_committed` rewritten from `$49/mo Alchemy Growth (2026-04-30 user pin)` to `FREE-TIER ONLY (2026-05-02 user directive supersedes 2026-04-30 $49/mo Alchemy Growth pin)`. Predecessor pin `spec_sha256_v1_1: de4e8cdc…` recorded; `spec_sha256_v1_2` placeholder added. Verifier-status fields for v1.1 marked PASS-WITH-NITS (closing the v1.1 verification cycle); v1.2 verifier fields marked pending.
- **§5 Tooling stack and budget assumption.** Rewritten end-to-end. Committed budget switched to FREE-TIER ONLY. Permitted free-tier services enumerated explicitly with their effective quotas at revision time (Alchemy free ≈30M compute units/month + ≈25 req/sec (corrected v1.2.1 from v1.2's ≈300M figure per Path B WebFetch verification 2026-05-02 against alchemy.com/pricing); public Celo `https://forno.celo.org` and Ethereum `https://eth.llamarpc.com` mainnet RPCs as fallback (per CORRECTIONS-ε at v1.2.2 — the v1.2 enumeration's second `rpc.ankr.com/eth` mention has been removed because that endpoint now requires API-key authentication and is no longer free-tier-eligible); Foundry/Anvil local fork; SQD Network public gateways for Path B alignment; local QuantLib + numpy + scipy + sympy already pinned in §10.2). The trade-off (Alchemy free has predictable quotas + reliability; public RPCs are free but flakier and slower with unpredictable per-day rate caps) is documented as a per-rung dispatch decision, NOT a spec-level pre-commitment, because per-rung load profiles differ.
- **§6 typed exceptions.** Existing `Stage2PathABudgetOverrun` rewritten: trigger now fires if any version requires a paid service (rather than the retired $49/mo overrun threshold); pivots updated. Three new typed exceptions added per the v1.2 directive: (i) `Stage2PathAAlchemyFreeTierRateLimitExceeded` (≈25 req/sec sustained breach during heavy-activity v1/v2 fork operations); (ii) `Stage2PathAArchiveNodeDepthInsufficientFree` (Panoptic v2 needs Ethereum archive depth beyond what free Alchemy + free public RPC fallback support — see free-tier feasibility risk in this change log); (iii) `Stage2PathAPublicRPCDeterminismDegraded` (fallback public RPC produces non-deterministic re-runs because of upstream load-balancing or per-call result variation, breaking BLOCK-D1 reproducibility).
- **§10.1 Fork block heights, chainId, RPC source.** v1 Anvil RPC source switched from "Alchemy Growth Celo endpoint" to a primary/fallback ladder: PRIMARY = Alchemy free-tier Celo endpoint (≈25 req/sec); FALLBACK = public Celo RPC `https://forno.celo.org`; selection recorded in v1 manifest with rate-limit-headroom note. v2 Ethereum-side likewise: PRIMARY = Alchemy free-tier Ethereum endpoint; FALLBACK = `https://eth.llamarpc.com` (per CORRECTIONS-ε at v1.2.2 — the v1.2 enumeration's second `rpc.ankr.com/eth` mention has been removed because that endpoint now requires API-key authentication); selection recorded in v2 manifest. Degradation path documented: if PRIMARY hits rate-limit during fork heavy-activity, executor switches to FALLBACK and notes that determinism MAY degrade per `Stage2PathAPublicRPCDeterminismDegraded` (BLOCK-D1 reproducibility-pin compliance must be re-verified per the v1.1 §10.2 byte-identical-artifact rule, NOT relaxed).
- **§9 Self-review checklist.** Pin reference updated from "$49/mo Alchemy budget pin in §5" to "free-tier-only budget pin in §5". Typed-exception count updated from 8 to 11 per the §6 expansion. No other changes to the checklist substance.
- **§11.b GBM σ_0 ≈ 10% MC computation.** Confirmed pure-local-compute; numpy/scipy/sympy/QuantLib are local libraries with no external API calls; no §11.b changes required under CORRECTIONS-δ.

**Free-tier feasibility risk surfaced (orchestrator decision required at v2 dispatch — NOT a spec-level HALT).** Panoptic on Ethereum mainnet typically requires archive-node depth (state read at historical blocks; the fork itself needs full state at the pinned block height, NOT merely the latest). Alchemy free-tier supports archive-depth reads but the cumulative compute-unit budget (≈30M/month per v1.2.1 correction) MAY be exhausted by repeated forks if v2 is re-run multiple times during debugging. The public Ethereum RPC `eth.llamarpc.com` (per CORRECTIONS-ε at v1.2.2 — `rpc.ankr.com/eth` removed from this enumeration because that endpoint now requires API-key authentication) historically supports archive-depth reads but with no SLA, and may rate-limit archive queries more aggressively than head-state queries. The v1.2 spec does NOT pre-commit to whether v2 is feasible end-to-end on free-tier; it pre-pins the typed exception `Stage2PathAArchiveNodeDepthInsufficientFree` so that v2 dispatch surfaces the question to the orchestrator BEFORE silent degradation. If at v2 dispatch the executor finds archive depth insufficient under free-tier across both Alchemy and public-RPC options, the typed exception fires and the orchestrator adjudicates (pivot options enumerated in §6).

**Path B coordination note.** Path B is receiving the same-shape CORRECTIONS-δ revision in parallel. §12 cross-path coupling table is unchanged (default INDEPENDENT). No new coupling emerges from the budget change; both paths face the same external-service constraint independently. If Path B's CORRECTIONS-δ surfaces a free-tier coupling concern that affects Path A v3 (e.g., shared RPC quota across both paths' simultaneous execution), that concern will be raised at convergence-dispatch authoring time, NOT under this CORRECTIONS-δ.

**No regression of v1.1 closures.** BLOCK-D1 (§10) preserved; BLOCK-D2 (§11) preserved; FLAG-F1 (§10.4) preserved; FLAG-F2 (§3 v1 inputs) preserved; FLAG-F3 (§10.5) preserved; FLAG-F4 (§2 v3 GBM baseline + frontmatter pin) preserved; FLAG-F5 (§6 expansion to 8 typed exceptions) preserved AND extended to 11 under CORRECTIONS-δ; FLAG-F6 (§12 default INDEPENDENT) preserved.

---

## Change Log v1.0 → v1.1

This revision applies the Wave-1 (Reality Checker) + Wave-2 (Software Architect) verification matrix from the v1.0 review. v1.0 spec sha256 is pinned in frontmatter as `spec_sha256_v1_0` for reproducibility audit. Each delta below is tagged with the BLOCK or FLAG identifier it resolves.

**BLOCK-D1 — Reproducibility infrastructure underspecified.** v1.0 mentioned reproducibility but did not pin nondeterminism sources. v1.1 adds a new §10 "Reproducibility Pin" enumerating per-rung pins for: (a) Anvil/Hardhat fork block numbers + chainId + RPC source per ladder rung; (b) gas-price determinism strategy across forks; (c) numpy/scipy RNG seed pinning for v3 stochastic-σ MC using `np.random.default_rng(seed=...)` pattern (not legacy global state); (d) Sympy version pin for v0 symbolic ladder. Each rung must produce byte-identical artifacts on re-run. Resolution status: RESOLVED via §10.

**BLOCK-D2 — Carr-Madan 1e-6 tolerance is mathematically infeasible at 12 legs.** v1.0 §2 v0 exit criterion (e) and v2 exit criteria conflated two distinct error metrics. v1.1 adds §11 "Carr-Madan Error Metrics — Disambiguated" that splits the requirement into: (a) self-consistency (deterministic, code-vs-code) at machine-epsilon scale ≤ 1e-10 × N_legs; (b) truncation/discretization bound (analytic-vs-strip) at O(1e-2) to O(1e-3) σ-dependent, derived from the closed-form truncation expression for finite K_max + finite log-spacing. v0 exit criterion (e) and v2 exit criteria are amended to reference §11 thresholds. The 1e-6 figure from v1.0 is RETIRED. Resolution status: RESOLVED via §11; §2 v0 (e) and §2 v2 amended.

**FLAG-F1 — v0 sympy ladder symbolic-vs-numeric reconciliation criterion missing.** v1.0 §2 v0 specified five sub-criteria but did not specify the symbolic-vs-numeric equality test that confirms v0's symbolic Π matches v1+ numeric within tolerance. v1.1 adds §10.4 "v0 symbolic-vs-numeric reconciliation rule": the symbolic expression tree is evaluated at three pinned (ε, ω) test points, the resulting numeric values are compared against v1's harness-emitted CF^(a_l) at the same (ε, ω) points, and the relative-error tolerance follows §11.b for the Carr-Madan strip leg and ±5% for the LP-fee leg (matching v1's existing exit criterion). Resolution status: RESOLVED via §10.4 + §11.

**FLAG-F2 — v1 Mento+Uniswap fork pool address pin missing.** v1.0 §3 specified the Mento V3 router address but did not explicitly pin the Mento FPMM pool address used as the v1 reference. v1.1 §3 v1 inputs now explicitly pin: (i) Mento V3 router `0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`; (ii) canonical Mento V2 COPM token `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (per project memory `project_mento_canonical_naming_2026` β-corrigendum 2026-04-26); (iii) the FPMM pool address USDm/COPm to be resolved at fork-block height with the resolved address recorded in `results/path_a_v1_fork_manifest.md` and pinned in the v1.1 CORRECTIONS-block at v1 dispatch time. Note: `0xc92e8fc2…` (Minteo-fintech) is OUT of scope per the same memory. Resolution status: RESOLVED via §3 v1 inputs + manifest-recording requirement.

**FLAG-F3 — v2 Panoptic strip 5-leg-per-position vs 12-leg requirement reconciliation missing.** v1.0 §2 v2 required a 12-leg Carr-Madan strip but did not address Panoptic's 5-leg-per-position constraint. v1.1 §2 v2 now pins the position-count + leg-distribution scheme: 3 IronCondor positions × 4 legs each = 12 legs total. Each Panoptic position holds one IronCondor (4 legs: short-call + long-call + short-put + long-put), well under the 5-leg-per-position constraint. The three positions cover left-tail / ATM / right-tail strike regions per the Carr-Madan log-grid (`K_j ≈ S₀·exp(x_j)`, `w_j ∝ 1/K_j²`). The strip configuration JSON `results/path_a_v2_strip_config.json` records the position-by-position leg assignment + strike + weight. Resolution status: RESOLVED via §2 v2 amendment + §10.5 Panoptic position-count pin.

**FLAG-F4 — v3 stochastic σ MC variance process not pre-committed.** v1.0 §2 v3 listed GBM / OU / jump-diffusion / empirically-calibrated as variants without pinning a baseline. v1.1 §2 v3 pins **GBM as the v3 baseline** (simplest, well-understood, single-parameter calibration). OU and jump-diffusion are optional escalations available under the existing `Stage2PathAStochasticEnvelopeBreached` typed exception (§6). Empirically-calibrated remains a Path-B-conditional convergence-dispatch input. v3 exit criterion is evaluated against the GBM baseline FIRST; OU/jump-diffusion are required only if GBM fails the envelope-coverage threshold. Frontmatter `v3_baseline_pinned` field reflects this. Resolution status: RESOLVED via §2 v3 amendment + frontmatter pin.

**FLAG-F5 — Typed exception enumeration thin (only 5 in v1.0).** v1.1 §6 adds three new typed exceptions: `Stage2PathAPanopticStripIlliquidOnFork` (when v2 fork shows insufficient depth on the constructed condor strikes); `Stage2PathAMentoFPMMSlippageExceedsTolerance` (when v1 swap calls produce slippage > 5% relative to Mento spot oracle, breaking the deterministic σ-path drive); `Stage2PathAGasPriceDriftBeyondReproducibilityBound` (when fork gas pricing produces output drift exceeding the §10 reproducibility budget). Each new typed exception follows the existing protocol: pre-pinned trigger, disposition memo, ≥3 user-adjudicated pivots. Resolution status: RESOLVED via §6 expansion.

**FLAG-F6 — Cross-path coupling with Path B not specified.** v1.0 §8 mentioned convergence at v3 but did not specify which inputs (if any) hot-swap from Path B vs hold independent. v1.1 adds §12 "Path A ↔ Path B coupling — input-by-input pin": **DEFAULT IS INDEPENDENT** — Path A v0/v1/v2 are fully independent of Path B; only Path A v3's optional empirically-calibrated stochastic-process variant ingests Path B v1's σ-distribution as a READ-ONLY feed. All other Path A inputs (CF^(a_l), CF^(a_s), strike grids, fork-block heights, RNG seeds) are held independent. Path B's CF^a_l + CF^a_s estimates do NOT replace Path A's harness-realized values; cross-path reconciliation is a convergence-dispatch concern, NOT a Path A v3 concern. Resolution status: RESOLVED via §12.

No conflicts detected between FLAGs and BLOCKs during v1.1 authoring. The 1e-6 retirement (BLOCK-D2) was the only retirement of a v1.0 numerical assertion; it is documented per `feedback_pathological_halt_anti_fishing_checkpoint` posture (no silent threshold tuning; explicit acknowledgement in this change log).

---

## §1. Goal and scope

Path A is the **fork-and-simulate** verification track for the Pair D Convex Payoff Option (CPO) M-sketch authored under the Stage-2 dispatch brief at `contracts/.scratch/2026-04-30-stage-2-m-sketch-dispatch-brief-pair-d.md`. The goal is mechanical: take the CPO derivation imported from `contracts/notes/2026-04-29-macro-markets-draft-import.md`, drive deterministic and (later) stochastic FX paths through forked open-source contracts (Mento V3, Uniswap V3/V4 on Celo, Panoptic on Ethereum) on a local Anvil/Foundry sandbox, and verify that the realized cash flows produced under contract execution match the framework's analytical predictions for `Δ^(a_l)`, `Δ^(a_s)`, equilibrium `K_l = K_s`, and the Carr-Madan identity `Π(σ_T) ≈ K̂·σ_T` within the disambiguated error metrics defined in §11.

The Stage-1 anchor (load-bearing READ-ONLY input, NOT a re-test target) is the Pair D simple-β PASS verdict: β_composite = +0.13670985, HAC SE 0.02465, t = +5.5456, p_one = 1.46×10⁻⁸ (R-AGREE 0/4 flips); sha pin chain `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659` (v1.3.1) → `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf` (panel) → `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf` (primary OLS) → `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904` (robustness) → `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf` (VERDICT.md).

Framing held precisely: **Path A is mechanical verification of the framework's analytical claims under contract execution, NOT re-derivation of Stage-1 empirical results**. Stage-1 established the microeconomic risk admits a positive measurable beta on a Panoptic-eligible reference asset (COP/USD); Path A asks the orthogonal question — given the framework specifies a CPO that *would* settle this relationship, do real open-source contracts honor the framework's identities when driven by a known-shape FX path?

Path A converges with Path B (stochastic-process empirical-calibration) at v3: Path A v3 ingests a calibrated σ-distribution from Path B v1 if available, otherwise uses the GBM v3 baseline (FLAG-F4 pin) with OU and jump-diffusion as optional escalations. The convergence dispatch is a separate spec; Path A's exit gate is its own v3 envelope verification. See §12 for the input-by-input coupling pin.

## §2. Internal ladder (v0 → v1 → v2 → v3)

The Path A ladder is **simplicity-first**. Each version has a deterministic pre-pinned exit criterion and exits SAA — success, abort, or abort-with-specific-pivot — per the Phase-A.0 anti-fishing discipline. No exit criterion may be retroactively softened; tightening is permitted only via a CORRECTIONS block under post-hoc 3-way review.

**v0 — Pure symbolic math reproduction.** Scope: reproduce the framework's Δ derivation and equilibrium identity in a Sympy + numpy notebook. No smart contracts, no fork, no on-chain inputs. The notebook starts from `(X/Y)_t(ε,ω) = (1 + ε·(cos²(ωt) − 1/2))·(X/Y)̄`, derives `σ_T(ε,ω)`, inverts to `ε(σ_T)`, and computes `Δ^(a_l)` and `Δ^(a_s)` symbolically. Exit criterion: (a) `Δ^(a_l) > 0` over admissible `0 < ε < 1`; (b) `Δ^(a_s) < 0` over same domain; (c) `Π(σ_T) = -∫₀^σ_T Δ^(a)(u) du` yields closed form `K·√σ_T` both sides; (d) linearization `Π ≈ K̂·σ_T`, `K̂ = K*/(2√σ₀)` matches the import verbatim; (e) Carr-Madan strip identity `σ_T = ∫₀^S₀ P(K)/K² dK + ∫_{S₀}^∞ C(K)/K² dK` agrees with a discrete 12-leg IronCondor approximation at three grid resolutions per the **disambiguated tolerances of §11** (self-consistency ≤ 1e-10 × N_legs; strip-vs-analytic truncation bound per §11.b closed-form expression). The retired 1e-6 figure from v1.0 is replaced by the §11 split per BLOCK-D2 resolution. Inputs: imported framework note only. Outputs: sympy notebook (.ipynb) + LaTeX-exported derivation + sympy-pickled expression tree. v0 is the analytical proof-of-concept before any contract is touched.

**v1 — Forked Mento V3 + Uniswap V3 (open-source).** Scope: local Anvil forked against Celo mainnet at the §10.1 pinned fork-block height; exercise the Mento V3 FPMM router (`0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`), canonical Mento V2 COPM (`0x8A567e2aE79CA692Bd748aB832081C45de4041eA`), and a Uniswap V3 Celo USDC/USDm pool; drive a deterministic σ-path via actual swap calls using v0's `(X/Y)_t(ε,ω)` generator; measure realized swap fees as `CF^(a_l) = Σ_t r·|FX_t − FX_{t−1}|`; reconcile against v0's analytic `Δ^(a_l)` per §10.4. The USDm/COPm FPMM pool address is resolved at fork-block height and recorded in `results/path_a_v1_fork_manifest.md` per FLAG-F2 resolution. Exit criterion: for at least three independent `(ε,ω)` grid points (small / medium / large ε), realized cumulative LP fees agree with the v0 analytic prediction within ±5% relative error AND the numerical slope of `CF^(a_l)` against `σ_T` is strictly positive in all three. Inputs: v0 notebook (read-only); forked Celo mainnet at pinned block height per §10.1. Outputs: harness CSV one row per step `(t, X/Y_t, swap_fee_realized, cumulative_CF_a_l, σ_T_running)` + reconciliation report + fork manifest.

**v2 — Forked Panoptic (open-source).** Scope: extend v1 with forked Panoptic on Ethereum (Panoptic-on-Celo is Stage-3 — out of scope; see §6 typed exception); construct the **3-condor / 12-leg Carr-Madan strip per the §10.5 position-count pin (FLAG-F3 resolution)**: 3 Panoptic positions × 4 IronCondor legs each = 12 legs total, well under Panoptic's 5-leg-per-position constraint; strikes per `K_j ≈ S₀·exp(x_j)`, weights per `w_j ∝ 1/K_j²`; three condors covering left-tail / ATM / right-tail strike regions. Verify `Π(σ_T) ≈ K̂·σ_T` matches v0; verify `K_l = K_s` when both sides are authored against the same reference oracle. Exit criterion: realized strip premium `Π_realized(σ_T)` agrees with v0 analytic `K̂·σ_T` per the **§11.b truncation/discretization bound** (NOT the retired v1.0 ±10% blanket figure — the §11.b bound is σ-dependent and explicit) across the v1 grid points; supply-side `K_l` and demand-side `K_s` agree per the **§11.a self-consistency bound** (numerical drift only; algebraic equality is enforced by the equilibrium derivation). Inputs: v1 outputs; forked Ethereum at §10.1 pinned block height; forked Celo (Mento spot oracle). Outputs: strip configuration JSON `results/path_a_v2_strip_config.json` (12 strikes, weights, three condor geometries, position-by-position leg assignment) + premium-time-series CSV + `Π_realized` vs `K̂·σ_T` fit report.

**v3 — Stochastic σ-path Monte Carlo.** Scope: replace the deterministic driver with stochastic processes of increasing fidelity. **GBM is the v3 baseline (FLAG-F4 pin)** — single-factor Geometric Brownian Motion on the FX rate, parameterized by drift μ and volatility σ_BM calibrated to the v1 deterministic-path range. Optional escalations (only if GBM fails the envelope-coverage threshold): mean-reverting Ornstein-Uhlenbeck, jump-diffusion Merton-style, empirically-calibrated (if Path B v1 lands during v3 — see §12). Run `N ≥ 1000` paths per active variant under the §10.3 RNG seed pin. Verify the realized CPO P&L distribution stays consistent with `Π = K·√σ_T`. Exit criterion: per active variant, P&L mean tracks `K̂·E[σ_T]` per the **§11.b truncation/discretization bound** AND the 5th-95th percentile envelope brackets the analytic `K·√σ_T` curve at ≥95% of sampled `σ_T` values. Inputs: v0/v1/v2 outputs; OPTIONAL Path B v1 empirical σ-distribution (read-only feed per §12); synthetic processes parameterized internally otherwise. Outputs: per-variant MC P&L distribution histograms, envelope-coverage reports, final summary table determining stochastic CPO P&L bounds for the convergence dispatch.

The ladder enforces simplicity: v0 never imports contracts; v1 never imports Panoptic; v2 never imports stochastic libraries; v3 starts only after v2's exit verification is committed under `feedback_two_wave_doc_verification`.

## §3. Inputs (sha-pinned)

Path A inherits the Stage-2 dispatch brief sha-pin chain READ-ONLY (verbatim from dispatch brief §1): spec v1.3.1 `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`; joint panel `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`; primary OLS `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf`; robustness pack `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904`; VERDICT.md `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf`. The imported CPO framework at `contracts/notes/2026-04-29-macro-markets-draft-import.md` is byte-identical to source `~/learning/cfmm-theory/macro-markets/DRAFT.md`. Path A is a Stage-2 spec; it does NOT modify Stage-1 artifacts.

Per-version inputs layer monotonically. **v0** has no on-chain inputs; pure mathematics. **v1** adds (FLAG-F2 pin): (i) Mento V3 FPMM router `0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6` (Celo mainnet); (ii) canonical Mento V2 COPM token `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (per `project_mento_canonical_naming_2026` β-corrigendum 2026-04-26 — `0xc92e8fc2…` Minteo-fintech is OUT of scope); (iii) Mento USDm/COPm FPMM pool address — resolved at the §10.1 fork-block height, recorded in `results/path_a_v1_fork_manifest.md`, pinned in a v1 dispatch CORRECTIONS-block; (iv) Uniswap V3 Celo USDC/USDm pool address — resolved at the same fork-block height, recorded in the same manifest; (v) Anvil + Foundry version pins per §10.2; (vi) free-tier RPC source per the §10.1 PRIMARY/FALLBACK ladder (PRIMARY = Alchemy free-tier Celo; FALLBACK = `https://forno.celo.org`) per the v1.2 CORRECTIONS-δ free-tier-only budget pin. **v2** adds: Panoptic-on-Ethereum manifest (canonical contract addresses resolved at the §10.1 Ethereum fork-block height); forked Ethereum block height pinned within 24h of forked Celo block height to avoid cross-chain oracle drift; free-tier RPC source per the §10.1 PRIMARY/FALLBACK ladder (PRIMARY = Alchemy free-tier Ethereum; FALLBACK = `https://eth.llamarpc.com` per CORRECTIONS-ε at v1.2.2 — verified-working free-tier public endpoint for Ethereum mainnet). **v3** adds: optional read-only Path B v1 empirical σ-distribution feed per §12 (convergence point); GBM baseline parameter set; optional OU + jump-diffusion + empirical parameter sets pinned in the v3 implementation plan.

## §4. Outputs

Per-version outputs layer monotonically. **v0**: sympy-driven Jupyter notebook `notebooks/path_a_v0_symbolic.ipynb` with trio-checkpoint discipline per `feedback_notebook_trio_checkpoint`; LaTeX-exported derivation `notebooks/path_a_v0_derivation.tex`; sympy-pickled expression tree `notebooks/path_a_v0_derivation.pkl`; exit-criterion verification report `results/path_a_v0_exit_report.md` enumerating sub-criteria (a)-(e) from §2 with numerical evidence per criterion (criterion (e) cites the §11 disambiguated bounds explicitly). **v1**: forked-environment harness CSV `results/path_a_v1_harness.csv` (one row per simulation step); reconciliation-vs-v0 report `results/path_a_v1_reconciliation.md` enumerating per-grid-point relative-error and sign-of-Δ^(a_l) checks; fork-environment manifest `results/path_a_v1_fork_manifest.md` recording Anvil fork block heights, contract addresses (including the FPMM pool address resolved per FLAG-F2), Foundry pins, gas-price strategy per §10.2. **v2**: Panoptic strip configuration JSON `results/path_a_v2_strip_config.json` (12 strikes, weights, three condor geometries, **position-by-position leg assignment per FLAG-F3**); premium-time-series CSV `results/path_a_v2_premium_timeseries.csv`; fit report `results/path_a_v2_fit.md` documenting `Π_realized` vs `K̂·σ_T` envelope per §11.b and `K_l = K_s` numerical-drift checks per §11.a. **v3**: per-variant MC P&L histograms `results/path_a_v3_mc_distributions/{gbm,ou,jump_diffusion,empirical_calibrated}/` (gbm always present per FLAG-F4 baseline; others present only if active under §6 escalation); envelope-coverage report `results/path_a_v3_envelope_coverage.md`; final summary table `results/path_a_v3_summary.md` (Path A → convergence-dispatch handoff); reproducibility manifest `results/path_a_v3_reproducibility_manifest.md` recording RNG seeds, library version pins, fork-block heights per §10.

All outputs use scratch-directory conventions; nothing is committed under `src/`, `test/*.sol`, or `foundry.toml` per `feedback_scripts_only_scope`.

## §5. Tooling stack and budget assumption

Committed budget per the v1.2 CORRECTIONS-δ user directive: **FREE-TIER ONLY**. No paid services authorized. The frontmatter `budget_pin: free_tier_only` is the authoritative commitment; any service requiring a paid tier triggers HALT under `Stage2PathABudgetOverrun` (see §6) for user adjudication.

Permitted free-tier services (quotas verified at v1.2 revision time 2026-05-02; executor must re-verify current quotas at v-dispatch time, as upstream providers change limits without notice):

- **Alchemy free tier** — Celo + Ethereum endpoints; ≈30M compute units / month / app (corrected v1.2.1 from v1.2's ≈300M figure per WebFetch verification 2026-05-02 against alchemy.com/pricing); ≈25 requests / second sustained rate limit; ≈500 CU/sec rolling-window cap; archive-depth state reads supported within compute-unit budget. Primary RPC choice for v1 + v2 forks where determinism + reliability dominate.
- **Public Celo mainnet RPC** — `https://forno.celo.org` (cLabs-operated public endpoint); rate-limited (no published SLA; behaves as best-effort); used as fallback for v1 if Alchemy free-tier quota exhausts.
- **Public Ethereum mainnet RPC** — `https://eth.llamarpc.com` as the named free-tier fallback for v2 if Alchemy free-tier exhausts; the chosen endpoint is recorded in the v2 manifest. Best-effort, no SLA, may rate-limit archive queries more aggressively than head-state queries. Verification basis: Phase 0 executor + Gate B0 Reality Checker reproduction 2026-05-02 confirmed `eth.llamarpc.com` returns valid responses without authentication; the previously-listed `rpc.ankr.com/eth` was REMOVED at v1.2.2 (CORRECTIONS-ε) after both observers independently reproduced an `Unauthorized — You must authenticate your request with an API key` (-32000) response, invalidating its standing as a free-tier endpoint. Executors MAY enumerate and verify additional free-tier alternatives (e.g., dRPC public, Chainstack public) at v-dispatch time and record the choice in the v2 manifest, but no replacement endpoint may be elevated to spec-level enumeration without empirical verification per the anti-fishing posture in §7.
- **Foundry** — Anvil + Forge + Cast; local compute only; no external cost; Anvil local fork is the v1/v2 sandbox harness host.
- **SQD Network public gateways** — free per Path B's BLOCK-B3 resolution; available to Path A v1/v2 if cross-checking on-chain state against an independent indexer is needed (Path A primary is fork harness, NOT indexer).
- **Etherscan + Celoscan free tier** — verified-contract retrieval (ABI + source) for fork harness setup; throttle-limited (≈5 req/sec on free tier) but sufficient for one-shot setup at v-dispatch.
- **Tenderly free tier** — optional transaction-simulation + trace inspection (limited monthly simulations on free tier); usable for spot-debugging v1/v2 swap reverts; primary determinism path is Anvil + Foundry traces, NOT Tenderly.
- **Sympy + Jupyter + numpy + scipy** — local Python compute for v0 mathematics; no external API; pinned per §10.2.
- **QuantLib Python bindings** — local compute for v3 stochastic-process generation + Carr-Madan strip pricing benchmarks; no external API; pinned per §10.2.

Trade-off documented (per-rung dispatch decision, NOT spec-level pre-commitment because per-rung load profiles differ): Alchemy free-tier offers predictable quotas + archive-depth reliability but caps total monthly compute; public RPCs are unmetered per-account but flakier, slower, and may produce non-deterministic results if upstream load-balancing routes successive calls to different nodes. The §10.1 ladder (PRIMARY = Alchemy free; FALLBACK = public RPC) preserves determinism by default and degrades only when forced. Determinism degradation under fallback triggers `Stage2PathAPublicRPCDeterminismDegraded` (§6); rate-limit exhaustion under primary triggers `Stage2PathAAlchemyFreeTierRateLimitExceeded` (§6).

Any version-level tooling requirement that needs a paid tier — paid simulation-fork service, paid decompilation API, per-call-pricing oracle with non-trivial usage, paid Alchemy upgrade — triggers HALT under `Stage2PathABudgetOverrun` (§6) with user adjudication required before proceeding. Library version pins (sympy, numpy, scipy, QuantLib, Foundry, Anvil) are enumerated in §10.2 to support BLOCK-D1 reproducibility unchanged.

## §6. HALT discipline (typed exceptions)

Per `feedback_pathological_halt_anti_fishing_checkpoint`, foreseeable blockers are pre-pinned with a typed exception name, a disposition-memo path, and ≥3 user-adjudicated pivot options. Auto-pivot is anti-fishing-banned. Blockers not enumerated below must be surfaced as fresh typed exceptions under the same protocol. Disposition-memo paths follow `contracts/.scratch/2026-XX-XX-stage2-path-a-{version}-{slug}-disposition.md`.

**v0 — `Stage2PathAFrameworkInternallyInconsistent`.** Trigger: symbolic Δ-sign derivation does NOT reproduce the framework's prediction over the admissible domain, OR Carr-Madan strip identity numerically diverges beyond the §11 disambiguated bounds (NOT the retired 1e-6 figure — the trigger is now bounded by §11.a self-consistency for code-vs-code and §11.b truncation for analytic-vs-strip). Pivots: (i) re-import the framework from source `~/learning/cfmm-theory/macro-markets/DRAFT.md` and re-verify byte-identity (suspect import corruption); (ii) raise as framework-content question to user with the failing sub-criterion enumerated — auto-amendment is anti-fishing-banned; (iii) shrink Path A scope to the reproducible subset and exit early at v0 with partial-PASS gated on user acceptance.

**v1 — `Stage2PathAMentoUSDmCOPmPoolMissing`.** Trigger: Mento V3 FPMM USDm/COPm pool does NOT exist at fork-block, OR exists with zero liquidity, OR canonical Mento V2 COPM `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` is not paired against USDm. Pivots: (i) substitute Mento V2 BiPool if a USDm/COPm pool exists there; (ii) synthetic COP-leg via cUSD/cEUR cross-pool triangulation through an oracle-fed COP/EUR rate (lower fidelity, preserves architecture); (iii) substitute Uniswap V3 Celo USDC/USDm as v1 reference, synthesizing the COP leg from an oracle-fed COP/USD rate, recording deviation in a CORRECTIONS-block. Dispatch brief §4 authorizes Uniswap V3/V4 Celo Mento-pair as rank-2 supply-side — pre-documented fallback.

**v1 — `Stage2PathAMentoFPMMSlippageExceedsTolerance` (NEW per FLAG-F5).** Trigger: v1 swap calls produce realized slippage > 5% relative to Mento spot oracle, breaking the deterministic σ-path drive (`(X/Y)_t(ε,ω)` cannot be honored if swap impact exceeds the σ-path step magnitude). Pivots: (i) reduce per-step swap notional to bring slippage within tolerance and re-run with smaller σ-path amplitude; (ii) substitute a deeper Mento pool (e.g., USDm/cUSD) and synthesize the COP leg via oracle, recording deviation in a CORRECTIONS-block; (iii) downgrade v1 to Uniswap V3 Celo USDC/USDm only (rank-2 supply-side fallback per dispatch brief §4) where slippage profiles are better characterized.

**v2 — `Stage2PathACrossChainBridgingRequired`.** Trigger: Panoptic-on-Ethereum cannot reference a Mento Celo-side pool without bridging, AND no Panoptic-on-Celo deployment exists at v2 fork-block. Pivots: (i) substitute a Uniswap V3 Ethereum-mainnet FX-proxy pair as v2 reference oracle, deferring COP-specific calibration to v3; (ii) defer v2 to future Panoptic-on-Celo and exit early at v1 with partial-PASS gated on user acceptance (v3 MC still proceeds against v0+v1); (iii) construct a sandbox-only mock bridging oracle (pulls Mento spot at v1's forked Celo block, exposes on v2's forked Ethereum) — explicitly flagged as sandbox-only, NOT production architecture, in all artifacts.

**v2 — `Stage2PathAPanopticStripIlliquidOnFork` (NEW per FLAG-F5).** Trigger: forked Panoptic deployment shows insufficient liquidity to honor any of the 12 IronCondor legs at the constructed strikes (e.g., zero open interest at left-tail or right-tail strikes; pool depth below the position notional required for the §10.5 strip). Pivots: (i) shrink strike grid to ATM-only condor (degrades from 3 condors to 1, accepted under CORRECTIONS-block as partial coverage of the Carr-Madan strip with explicit truncation-bias acknowledgement); (ii) substitute a more-liquid Panoptic pool (e.g., ETH/USDC) as v2 reference, treating the FX-proxy mapping as scaffolding-only and deferring COP-specific calibration to v3; (iii) defer v2 entirely (partial-PASS at v1) and proceed to v3 with v0+v1 outputs only.

**v3 — `Stage2PathAStochasticEnvelopeBreached`.** Trigger: GBM baseline (FLAG-F4 pin) and any active escalation variants collectively fail to bracket realized historical σ-path values at the ≥95% envelope-coverage threshold. Pivots: (i) escalate from GBM-only to GBM + OU; (ii) escalate further to GBM + OU + jump-diffusion; (iii) augment with a regime-switching variant capturing the post-2014 oil + COVID + Fed-tightening regime mix per RC FLAG #6; (iv) shrink envelope target from ≥95% to ≥80% with explicit user acknowledgement of irreducible model-class limitation, under CORRECTIONS-block; (v) defer empirical calibration to convergence dispatch and exit v3 with partial-PASS narrative.

**Orthogonal — `Stage2PathABudgetOverrun` (REVISED v1.2 per CORRECTIONS-δ).** Trigger: any version requires a paid service to honor its exit criterion, where "paid" means any service tier above the explicit free tiers enumerated in §5 (paid Alchemy upgrade, paid simulation-fork service, paid decompilation API, per-call-pricing oracle with non-trivial usage, paid Tenderly tier, etc.). The retired $49/mo overrun threshold from v1.1 is replaced by the binary free-vs-paid distinction. Pivots: (i) reduce fork frequency / cache aggressively to fit free-tier compute-unit + rate-limit budgets; (ii) substitute a free-tier-eligible alternative (e.g., switch from Alchemy to public RPC for the affected calls) per §10.1 fallback ladder; (iii) request user adjudication on one-time budget exception with explicit figure, scope, and justification — no auto-escalation; (iv) descope the affected version's exit criterion within free-tier budget under CORRECTIONS-block.

**Orthogonal — `Stage2PathAAlchemyFreeTierRateLimitExceeded` (NEW v1.2 per CORRECTIONS-δ).** Trigger: v1 or v2 fork heavy-activity sustains >25 req/sec against the Alchemy free-tier endpoint (Celo or Ethereum), producing 429 responses or upstream throttling that breaks the v-dispatch run. Pivots: (i) introduce per-call rate-limiting in the harness (sleep + batching) to bring sustained load below 25 req/sec and re-run; (ii) switch to FALLBACK public RPC per §10.1 and accept potential determinism degradation under `Stage2PathAPublicRPCDeterminismDegraded`; (iii) split the v-dispatch into smaller chunks (fewer simulation steps per harness run) and aggregate outputs across chunks with explicit aggregation manifest; (iv) request user adjudication on one-time paid-tier exception under `Stage2PathABudgetOverrun`.

**Orthogonal — `Stage2PathAArchiveNodeDepthInsufficientFree` (NEW v1.2 per CORRECTIONS-δ).** Trigger: v2 Panoptic-on-Ethereum fork at the §10.1 pinned block height requires archive-depth state reads that exceed what free-tier providers (Alchemy free + public RPC fallback) can satisfy — either because the cumulative compute-unit budget exhausts mid-fork, or because the public RPC fallback rate-limits archive queries below usable throughput, or because the pinned block height is outside the providers' supported archive window. Pivots: (i) re-pin v2 Ethereum fork-block height to a more-recent block within the providers' supported archive window (with explicit CORRECTIONS-block documenting the re-pin and re-execution of v2 downstream artifacts per §10.1 "fork block heights are NEVER changed mid-version without a fresh CORRECTIONS-block"); (ii) cache archive-depth state reads aggressively in the harness so subsequent re-runs hit the cache, not the upstream RPC; (iii) substitute a free-tier-eligible archive-RPC provider (e.g., dRPC free, Chainstack free; Ankr public archive removed at v1.2.2 per CORRECTIONS-ε — Ankr's public Ethereum endpoint now requires API-key authentication and is no longer free-tier-eligible) and document SLA assumptions, with empirical verification of the chosen replacement before relying on it; (iv) request user adjudication on one-time paid-tier exception under `Stage2PathABudgetOverrun` (specifically: paid Alchemy upgrade for archive-throughput); (v) descope v2 to a smaller block-window range that fits within free-tier archive limits and document the truncation impact on `K_l = K_s` reconciliation in a CORRECTIONS-block; (vi) defer v2 entirely to a future paid-tier dispatch and exit early at v1 with partial-PASS gated on user acceptance.

**Orthogonal — `Stage2PathAPublicRPCDeterminismDegraded` (NEW v1.2 per CORRECTIONS-δ).** Trigger: a v-dispatch using FALLBACK public RPC per §10.1 (after PRIMARY Alchemy free-tier exhausted or unavailable) produces non-deterministic output across re-runs at the same pinned fork block, violating the BLOCK-D1 reproducibility-pin requirement (byte-identical artifacts on re-run). Common upstream causes: load-balancer routes successive calls to different backend nodes with slightly different state-snapshot timings; per-call result variation in `eth_call` ordering; subtle differences in archive-vs-head node responses for state at near-tip blocks. Pivots: (i) switch from FALLBACK public RPC back to PRIMARY Alchemy free-tier and absorb the rate-limit hit — accept slower runtime but recover determinism; (ii) pin a single public-RPC backend node by URL (some providers expose stable per-node endpoints) and re-verify byte-identical output across re-runs; (iii) cache the offending RPC responses on first run and replay from cache on subsequent runs (harness-level cache, NOT upstream cache); (iv) fall back to a different free public RPC provider and re-test determinism; (v) request user adjudication on one-time paid-tier exception under `Stage2PathABudgetOverrun` if no free-tier path achieves byte-identical re-runs.

**Orthogonal — `Stage2PathAGasPriceDriftBeyondReproducibilityBound` (NEW per FLAG-F5).** Trigger: forked-environment gas pricing produces output drift across re-runs exceeding the §10.2 reproducibility budget (e.g., realized swap output diverges by > 0.01% across two re-runs at the same fork block). Pivots: (i) pin gas price explicitly via Anvil `--gas-price` flag at the fork-block-resolved value and re-run; (ii) switch to `--no-base-fee` mode and document the architectural deviation in a CORRECTIONS-block; (iii) escalate to a third-party deterministic-fork tool within free-tier budget if Anvil cannot be made deterministic enough — escalation must be evaluated against `Stage2PathABudgetOverrun` (free-vs-paid binary) first.

## §7. Anti-fishing posture

Path A inherits the Pair D spec §9 anti-fishing discipline. The framework's mathematical claims are pre-pinned at spec-authoring time; v0's job is reproduction, NOT exploration. If v0 fails to reproduce, the response is HALT under `Stage2PathAFrameworkInternallyInconsistent` — NOT framework amendment. Amendment is out-of-scope for the executor; only the user (adjudicating a HALT memo) can authorize, and authorization triggers a fresh CORRECTIONS-block plus v0 re-dispatch.

Path A is a **verification path, not an exploration path**. Mathematical claims, v1/v2 contract behaviors (deterministic σ-paths produce predicted Δ-sign and strip premium), the §11 disambiguated tolerances, and the v3 ≥95% coverage threshold are all pre-pinned. No version may post-hoc soften a threshold to claim PASS; only HALT + disposition + user-adjudicated CORRECTIONS + re-dispatch is permitted.

Phase-3 RC FLAG inheritance into Path A:

- **NO BPO causal-channel claims (RC FLAG #1).** Output language describes the CPO as hedging the *correlation* between FX volatility and the empirical Y-series, NOT the BPO causal channel. No output may be framed as "BPO-mechanism hedge verification" or equivalent.
- **NO empirical β re-litigation.** Path A does not estimate β at any stage; Stage-1 PASS is immutable input.
- **NO Stage-3 deployment claims.** No version may include statements about real LP capital, user onboarding, KYC/regulatory, or marketing copy. The v2 sandbox-only mock-bridging scaffold (v2 pivot iii) is explicitly NOT a deployment architecture; outputs must say so.
- **NO new yield-vault creation.** a_l universe is Mento V3 LP / Uniswap V3 LP per dispatch brief §4. Path A *packages* an existing yield vault into a forked harness; it does NOT invent a new vault.
- **Lag-6 dominance honored (RC FLAG #3).** Wherever v1/v2/v3 calibration exposes a settlement-horizon parameter, the practical horizon biases toward 6-month re-tendering, not uniformly across 6-12mo. The ≈80%-at-lag-6 stylized fact is a calibration input, not a free hyperparameter.
- **Brief-vs-spec discipline (RC FLAG #5).** Executors must NOT smuggle any `marco2018_dummy`-equivalent post-data adjustment into v3 calibration inputs from Path B, and must NOT re-litigate the Stage-1 spec-vs-brief record from Pair D MEMO §5; that record is closed.
- **Regime-mix concern (RC FLAG #6).** The v3 stochastic-process universe accommodates regime-switching as a pivot under `Stage2PathAStochasticEnvelopeBreached`; the post-2014 oil + COVID + Fed-tightening regime mix is a Stage-3 maintenance concern.

## §8. Convergence with Path B

Path A v3 OPTIONALLY ingests an empirical σ-distribution feed from Path B v1 if available at v3 execution time per the §12 input-by-input coupling pin. If Path B v1 has not yet landed, Path A v3 proceeds with the GBM baseline (FLAG-F4 pin) and any active escalation variants under §6. The Path A → Path B convergence is a **separate dispatch**, NOT part of this spec; Path A v3's exit gate is the entry gate for the future convergence dispatch but does not author it. That convergence dispatch will compose Path A v3's stochastic envelope verification with Path B v1's empirical σ-distribution into a unified calibrated CPO P&L distribution.

The Stage-3 entry gate (real LP capital + execution on a live Panoptic deployment) is gated on *both* paths reaching v3 exit AND the convergence dispatch closing successfully. Path A alone does NOT unlock Stage-3.

## §9. Self-review checklist

Building blocks naturally integrated: **Background** (Stage-1 PASS verdict + sha-pin chain + CPO framework in §1-§3); **Context** (per-version dependencies, fork-block pinning, HALT-disposition conventions in §3, §4, §6, §10); **Tonal control** (verification-not-exploration voice in §1, §7); **User preferences** (free-tier-only budget pin in §5 per CORRECTIONS-δ, trio-checkpoint discipline in §4, auto-mode adjudication boundary in §6); **Tool use instructions** (per-version stack in §5, artifact locations in §3-§4 specifying when and how the executor invokes Foundry, Sympy, QuantLib, forked-environment harnesses; reproducibility-pin discipline in §10).

Complexity principles present: **Personality and tone** (verification-path framing in §1, §7); **Tool use and formatting guidance** (§5 stack + §4 artifact paths + §10 version pins); **Dynamic behavior scaling** (the v0→v1→v2→v3 ladder, each exit gating the next); **Non-negotiable facts** (sha-pin chain in §3, Stage-1 PASS numerics in §1, §10 reproducibility pins, §11 disambiguated tolerances, §12 coupling defaults override conflicting briefs, free-tier-only budget pin in §5); **Critical evaluation of user input** (RC FLAG inheritance in §7 licenses refusal of smuggled adjustments and surfacing of brief-vs-spec contradictions); **Application/entity context** (Mento V3 / Uniswap V3 / Panoptic manifests + fork-block pinning in §3, §6, §10); **Guardrails and safety** (typed-exception HALT discipline in §6 — now 11 typed exceptions per FLAG-F5 expansion + CORRECTIONS-δ free-tier triple, pre-pinned memos, ≥3 pivots per exception).

No XML tags. No code; spec is code-agnostic per `feedback_no_code_in_specs_or_plans`. Implementation specifics — contract addresses resolved at fork-block height, exact Anvil/Foundry invocations, Sympy expression-tree code, QuantLib pricing configuration — deferred to per-version sub-agents per `feedback_specialized_agents_per_task`. Quality metrics 1-8 honored: completeness, clarity (deterministic exit criteria, pre-pinned HALT triggers, enumerated pivots, disambiguated tolerances), consistency (no §1-§12 conflicts; v1.1 change log documents the only retired numerical assertion), purposefulness, naturalness (v0→v3 follows the framework's analytical-to-stochastic progression organically), comprehensiveness (what-and-when without how), safety (typed-exception HALT + anti-fishing + budget guard + reproducibility guard), user experience (unambiguous exit criteria, HALT triggers, artifact paths, deferred-implementation boundaries).

---

## §10. Reproducibility Pin (NEW v1.1 per BLOCK-D1)

This section enumerates per-rung pins for every nondeterminism source. Each ladder rung must produce byte-identical artifacts on re-run from the pinned configuration. Re-runs that produce non-identical artifacts trigger `Stage2PathAGasPriceDriftBeyondReproducibilityBound` (for fork-related drift) or HALT under the v0 typed exception (for symbolic-math drift).

### §10.1 Fork block heights, chainId, RPC source

Each version that touches a fork pins the following at v-dispatch time and records in the version's manifest. RPC source per rung uses a **PRIMARY / FALLBACK ladder** under the v1.2 CORRECTIONS-δ free-tier-only budget pin: PRIMARY is the determinism-favored free-tier endpoint (Alchemy free); FALLBACK is the public free-tier endpoint, accepted only when PRIMARY is exhausted or unavailable, with the determinism trade-off explicit and the BLOCK-D1 reproducibility-pin requirement re-verified per the §10.2 byte-identical-artifact rule (NOT relaxed).

- **v1 Anvil fork target**: Celo mainnet, chainId 42220, fork block height pinned at v1 dispatch (recorded in `results/path_a_v1_fork_manifest.md`).
  - PRIMARY RPC: Alchemy free-tier Celo endpoint (≈25 req/sec sustained, ≈30M compute units / month / app shared with v2 + concurrent work per v1.2.1 correction).
  - FALLBACK RPC: `https://forno.celo.org` (cLabs-operated public endpoint, no SLA, best-effort).
  - Selection at dispatch: PRIMARY by default; switch to FALLBACK only on rate-limit exhaustion (`Stage2PathAAlchemyFreeTierRateLimitExceeded` fires) or PRIMARY unavailability. Recorded in v1 manifest with rate-limit-headroom note (estimated peak req/sec for the dispatch run vs the 25 req/sec ceiling).

- **v2 Anvil fork target (Ethereum-side)**: Ethereum mainnet, chainId 1, fork block height pinned at v2 dispatch within ±24h of the v2 Celo-side fork to avoid cross-chain oracle drift, recorded in `results/path_a_v2_fork_manifest.md`.
  - PRIMARY RPC: Alchemy free-tier Ethereum endpoint. Archive-depth state reads required for forking Panoptic at the pinned height; archive-depth supported on Alchemy free-tier within the shared compute-unit budget. If the fork-block depth or v2 re-execution count exhausts the compute-unit budget, `Stage2PathAArchiveNodeDepthInsufficientFree` fires.
  - FALLBACK RPC: `https://eth.llamarpc.com` — single named free-tier Ethereum public-RPC fallback, recorded in the v2 manifest at v2 dispatch. Verification basis: Phase 0 executor + Gate B0 Reality Checker reproduction 2026-05-02 confirmed `eth.llamarpc.com` returns valid responses without authentication; the previously-listed `rpc.ankr.com/eth` was REMOVED at v1.2.2 (CORRECTIONS-ε) after both observers independently reproduced an `Unauthorized — You must authenticate your request with an API key` (-32000) response, invalidating its standing as a free-tier endpoint. Public Ethereum RPCs support archive-depth reads but with no SLA and may rate-limit archive queries more aggressively than head-state queries; if the fallback also cannot honor the archive depth, `Stage2PathAArchiveNodeDepthInsufficientFree` fires for orchestrator adjudication. Executors MAY enumerate and verify additional free-tier alternatives at v2 dispatch and record the choice in the v2 manifest, but no replacement endpoint may be elevated to spec-level enumeration without empirical verification per §7.
  - Determinism warning: switching to FALLBACK during a v2 dispatch run may produce non-deterministic re-runs per `Stage2PathAPublicRPCDeterminismDegraded` (upstream load-balancing across backend nodes; per-call result variation). The dispatch must re-verify byte-identical artifacts on a follow-up re-run if FALLBACK was used; the BLOCK-D1 pin is NOT relaxed.

- **v2 Anvil fork target (Celo-side, when needed for spot-oracle reads)**: same Celo fork as v1 OR a fresh fork at a re-pinned block height — choice recorded in v2 manifest with rationale. Same PRIMARY / FALLBACK ladder as v1.

- **v3 Anvil fork target (when MC integrates with v1/v2 fork state)**: re-uses the v1+v2 pins; if v3 runs purely off v1/v2 cached outputs without re-forking, this is documented as "no-fork v3" in the v3 manifest. Re-using cached v1/v2 outputs avoids re-spending Alchemy free-tier compute units on v3 paths and is the preferred posture under the free-tier budget.

Fork block heights are NEVER changed mid-version without a fresh CORRECTIONS-block and re-execution of all downstream artifacts. RPC source ladder switches (PRIMARY → FALLBACK) within a version are NOT changes to the fork block height and do NOT trigger the CORRECTIONS-block requirement, but they DO trigger the relevant typed exception (`Stage2PathAAlchemyFreeTierRateLimitExceeded` and/or `Stage2PathAPublicRPCDeterminismDegraded`) AND require re-verification of byte-identical artifacts per BLOCK-D1.

### §10.2 Library version pins + Anvil/Foundry pins + gas-price determinism

The following version pins are enumerated at v-dispatch time and recorded in each version's manifest:

- **Sympy** (v0): version pinned (e.g., `sympy==1.13.x`), exact value recorded in v0 manifest. Sympy nondeterminism arises from expression-canonicalization order; the pin guarantees identical canonicalized expression trees.
- **numpy + scipy** (v0, v1, v2, v3): version pins recorded.
- **QuantLib Python bindings** (v3): version pin recorded.
- **Foundry / Anvil**: version pin recorded (e.g., `forge 0.2.0 (commit hash)`); the commit hash is the determinism anchor.
- **Gas-price determinism strategy**: each fork-using version pins ONE of: (i) Anvil `--gas-price <fixed-value>` at the fork-block-resolved median; (ii) Anvil `--no-base-fee` mode; (iii) custom per-call gas-price override via Cast. Choice recorded in the version manifest with rationale. Drift exceeding 0.01% across re-runs triggers `Stage2PathAGasPriceDriftBeyondReproducibilityBound`.

### §10.3 RNG seed pinning (v3)

The v3 stochastic-σ MC uses `numpy.random.default_rng(seed=<pinned-seed>)` exclusively — NOT legacy `numpy.random.seed()` global state, which is process-global and leaks across modules. The pinned seed is recorded in `results/path_a_v3_reproducibility_manifest.md` along with:

- Per-variant seed (one pinned seed per active stochastic variant: GBM baseline always; OU/jump-diffusion/empirical only if active under §6 escalation).
- Path count `N` per variant (≥1000 per §2 v3).
- The seed-and-N pair must produce identical histograms on re-run.

Any code that calls `numpy.random` without going through the pinned `default_rng` instance is a v3 reproducibility-bug; the v3 manifest must include a grep-verification line confirming zero global-state RNG calls.

### §10.4 v0 symbolic-vs-numeric reconciliation rule (FLAG-F1)

The v0 symbolic expression tree (sympy-pickled at `notebooks/path_a_v0_derivation.pkl`) is evaluated at three pinned `(ε, ω)` test points (small / medium / large ε, identical to the v1 grid points per §2 v1). The numeric values produced by symbolic evaluation are reconciled against:

- v1 harness-emitted `CF^(a_l)` at the same `(ε, ω)` points: tolerance ±5% relative error (matches v1's existing exit criterion in §2 v1).
- v2 harness-emitted strip premium `Π_realized` at the same `(ε, ω)` points: tolerance per §11.b (truncation/discretization bound).

Reconciliation is documented in `results/path_a_v0_exit_report.md` (criterion (e) sub-section) AND in `results/path_a_v1_reconciliation.md` AND in `results/path_a_v2_fit.md`. Three-way agreement is required before v3 dispatch.

### §10.5 Panoptic position-count + leg-distribution pin (FLAG-F3)

The v2 Carr-Madan strip is constructed as **3 IronCondor positions × 4 legs each = 12 legs total**, well under Panoptic's 5-leg-per-position constraint:

- Position 1 (left-tail condor): 4 legs at strikes `K_{−2}, K_{−1}, K_0_low, K_0_high` (left wing of the log-grid).
- Position 2 (ATM condor): 4 legs at strikes `K_0_low, K_0_high, K_{+1}_low, K_{+1}_high` (centered on `S_0`).
- Position 3 (right-tail condor): 4 legs at strikes `K_{+1}_high, K_{+2}, K_{+3}_low, K_{+3}_high` (right wing of the log-grid).

Strike spacing follows `K_j ≈ S_0 · exp(x_j)` with `x_j` uniform on `[-x_max, +x_max]`, `x_max` chosen per §11.b truncation-bound target. Weights `w_j ∝ 1/K_j²` per Carr-Madan. The strip configuration JSON `results/path_a_v2_strip_config.json` records the exact position-by-position leg assignment, strikes, and weights at v2 dispatch.

If Panoptic at the v2 fork-block does NOT support 4-leg IronCondors directly (e.g., if the deployment is restricted to single-leg or 2-leg Strangles), the v2 dispatch must trigger `Stage2PathAPanopticStripIlliquidOnFork` rather than silently shrinking to a smaller strip.

---

## §11. Carr-Madan Error Metrics — Disambiguated (NEW v1.1 per BLOCK-D2)

The v1.0 spec asserted a 1e-6 reconciliation tolerance between the analytic `Π(σ_T) = K·√σ_T` and the discrete IronCondor strip replication. With only 3 condors / 12 legs, the truncation error from finite `K_max` + finite log-space discretization is bounded *well above* 1e-6; the v1.0 assertion would always fail. v1.1 disambiguates into two distinct error metrics with separate thresholds.

### §11.a Self-consistency check (deterministic, code-vs-code)

**Definition**: the IronCondor payoff coded one way (e.g., explicit per-leg long-call + short-call + long-put + short-put summation) equals the same payoff coded another way (e.g., sympy-derived closed-form payoff function evaluated at the same strikes) at machine-epsilon scale.

**Threshold**: ≤ 1e-10 × N_legs, where N_legs = 12 in the v2 / v3 strip. Numerically: ≤ 1.2e-9 absolute error per payoff evaluation.

**Application**: this metric applies to (i) v0's two independent symbolic implementations of the strip payoff (sympy direct sum vs sympy closed-form integration), (ii) v2's `K_l = K_s` numerical-drift check (algebraic equality enforced by equilibrium derivation; numerical drift only at this scale), (iii) v3's MC harness internal consistency (per-path payoff computed two ways must agree at this scale).

**Failure mode**: if §11.a fails, the failure is a code-bug, not a model-bug. Triage path is debugger / unit-test, NOT spec amendment.

### §11.b Truncation/discretization bound (analytic-vs-strip)

**Definition**: the discrete IronCondor strip approximation of `σ_T = ∫_0^{S_0} P(K)/K² dK + ∫_{S_0}^∞ C(K)/K² dK` differs from the closed-form analytic by an amount bounded by the truncation of the integration domain `[K_min, K_max]` and the log-spacing discretization step `Δx`.

**Closed-form bound expression** (derivation pinned at v0 dispatch, recorded in `notebooks/path_a_v0_derivation.tex`):

```text
ε_truncation ≤ E[(S_T − K_max)^+ · 1(S_T > K_max)] / S_0
             + E[(K_min − S_T)^+ · 1(S_T < K_min)] / S_0

ε_discretization ≤ (Δx)^2 · max_{K ∈ [K_min, K_max]} |∂²(P(K) or C(K))/∂(log K)²| · const

ε_total = ε_truncation + ε_discretization
```

For 3 condors covering `[K_min, K_max] ≈ S_0 · [exp(-3σ_0), exp(+3σ_0)]` (≈ ±3σ_0 in log-space) with log-spacing `Δx ≈ σ_0`, under a GBM assumption with σ_0 = 10% (representative of the pinned COP/USD historical range), the bound evaluates to:

- `ε_truncation` ≈ O(1e-3) to O(1e-2) depending on tail thickness.
- `ε_discretization` ≈ O(1e-3) for `Δx = σ_0`.
- `ε_total` ≈ O(1e-2) at 3-condor / 12-leg resolution.

**Threshold**: pre-committed at **5e-2 (5%) relative error** for the v0 / v2 strip-vs-analytic reconciliation under the §10.5 strike grid. This is the σ-dependent figure mentioned in BLOCK-D2 resolution; if v0's exact derivation of `ε_total` produces a tighter bound at the §10.5 grid, the threshold tightens to that bound (recorded in CORRECTIONS-block); it does NOT loosen.

**Application**: this metric applies to (i) v0 exit criterion (e), (ii) v2 exit criterion `Π_realized(σ_T)` vs `K̂·σ_T` reconciliation, (iii) v3 exit criterion P&L mean vs `K̂·E[σ_T]` reconciliation.

**Failure mode**: if §11.b fails, the failure is *expected* under coarser grids and *not expected* under the §10.5 grid + GBM σ_0 ≈ 10% baseline. Failure at the baseline grid + baseline σ_0 triggers `Stage2PathAFrameworkInternallyInconsistent` (v0) or `Stage2PathAStochasticEnvelopeBreached` (v3); failure at a stress-test grid (smaller K-range, coarser Δx) is a documented analytical limitation, not a HALT.

### §11.c Replacement of the retired 1e-6 figure

The v1.0 spec's 1e-6 figure appeared in v0 exit criterion (e) and implicitly in v2's exit criteria (the ±10% blanket figure was a softer proxy). Under v1.1:

- v0 (e) now references §11.a (self-consistency ≤ 1e-10 × N_legs) AND §11.b (truncation ≤ 5% relative).
- v2 strip-vs-analytic now references §11.b (5% relative).
- v2 `K_l = K_s` numerical drift now references §11.a (machine-epsilon × N_legs).
- v3 P&L mean reconciliation now references §11.b (5% relative).
- The blanket "±10%" v2 figure from v1.0 is RETIRED and replaced by §11.b's σ-dependent 5% bound (tighter, derived from the truncation expression).

No v1.1 numerical threshold is looser than its v1.0 counterpart except where v1.0's threshold was mathematically infeasible (the 1e-6 strip bound). This complies with `feedback_pathological_halt_anti_fishing_checkpoint`: no silent threshold tuning.

---

## §12. Path A ↔ Path B coupling — input-by-input pin (NEW v1.1 per FLAG-F6)

**Default coupling: INDEPENDENT.** Path A v0/v1/v2 are fully independent of Path B at every input. Path B's CF^a_l + CF^a_s estimates from real on-chain data do NOT replace Path A's harness-realized values at any rung. Cross-path reconciliation is a convergence-dispatch concern, NOT a Path A v3 concern.

Per-input coupling specification:

| Input | Path A source | Path B coupling |
|---|---|---|
| Stage-1 PASS verdict | `1efd0e34d…` (read-only) | INDEPENDENT — both paths consume identically |
| CPO framework derivation | `contracts/notes/2026-04-29-macro-markets-draft-import.md` | INDEPENDENT — both paths consume identically |
| `(X/Y)_t(ε,ω)` deterministic generator (v0, v1, v2) | Path A v0 internal | INDEPENDENT — Path A's deterministic σ-path is internal scaffolding |
| CF^(a_l) realized | Path A v1 forked-Mento-V3 harness | INDEPENDENT — Path B's CF^(a_l) is real on-chain, NOT swapped into Path A |
| CF^(a_s) realized | Path A v2 forked-Panoptic harness | INDEPENDENT — Path B's CF^(a_s) is real on-chain, NOT swapped into Path A |
| Strike grid (v2) | Path A §10.5 internal | INDEPENDENT — Path B's strikes (if any) are not swapped in |
| Fork block heights (v1, v2) | Path A §10.1 internal | INDEPENDENT |
| RNG seeds (v3) | Path A §10.3 internal | INDEPENDENT |
| Stochastic σ-process baseline (v3) | GBM (FLAG-F4 pin) | INDEPENDENT — GBM baseline is parameterized internally to v3 |
| Empirical σ-distribution (v3 OPTIONAL escalation) | OPTIONAL Path B v1 read-only feed | COUPLED *only if* Path B v1 has landed at v3 dispatch time |

The single coupling point is the v3 OPTIONAL empirical-calibrated stochastic-process variant: if Path B v1 has produced an empirical σ-distribution by Path A v3 dispatch, that distribution is read READ-ONLY and used to parameterize a fourth v3 variant (alongside GBM baseline + any active OU / jump-diffusion). If Path B v1 has not landed, the empirical-calibrated variant is skipped and v3 proceeds with GBM baseline + escalations only.

Cross-path reconciliation (does Path A's harness-realized CF^(a_l) match Path B's on-chain-realized CF^(a_l) within tolerance?) is the convergence-dispatch's job, NOT Path A's job. Path A v3's exit gate fires when Path A's own envelope coverage threshold is met, regardless of Path B's state.

---

**End of spec v1.2.2.** Authored 2026-04-30 PM under auto-mode; v1.1 revision 2026-05-02 under auto-mode applying the Wave-1 (Reality Checker) + Wave-2 (Software Architect) verification matrix from v1.0 (sha256 `56fa06b8222789eb6902227a09661728a899b464bc155036a3328d746d644665`); v1.2 revision 2026-05-02 under auto-mode applying CORRECTIONS-δ for the user budget directive change to FREE-TIER ONLY (predecessor v1.1 sha256 `de4e8cdcb1af99d96f7657f7e9b397c8caf9196e59d30d5e9afce8e72265128b`); v1.2.1 micro-edit 2026-05-02 under auto-mode applying CORRECTIONS-δ' (Alchemy 300M→30M CU/mo correction in 4 locations per Wave-2 verifier NIT; predecessor v1.2 sha256 `ab65fd2048ed048d56917f3b9ce9c0dec85ebd498a568dd466ec396073b62dd6`); v1.2.2 micro-edit 2026-05-02 under auto-mode applying CORRECTIONS-ε (Backend Architect — removal of stale `rpc.ankr.com/eth` reference now that the endpoint requires API-key authentication, verified by Phase 0 executor + Gate B0 Reality Checker reproduction 2026-05-02; predecessor v1.2.1 sha256 `1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78`). v1.1 / v1.2 / v1.2.1 verifier cycles PASS-WITH-NITS (closed). v1.2.2 pending fresh 2-wave verification (Reality Checker + Software Architect) per `feedback_two_wave_doc_verification` before commit, scoped to the Ankr-removal scrub surface (frontmatter + §3 + §5 + §6 + §10.1 + change-log) since v1.0 → v1.2.1 BLOCK/FLAG/CORRECTIONS closures elsewhere are not regressed. Spec sha256 to be pinned by orchestrator at commit time.
