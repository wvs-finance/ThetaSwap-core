# Stage-2 M-sketch dispatch brief — Pair D CPO

**Date:** 2026-04-30 PM
**Status:** ready for M-sketch agent dispatch (Backend Architect or Panoptic-domain specialist)
**Authoritative inputs (sha-pinned, all on `phase0-vb-mvp`, post-merged at upstream PR #77):**

| Artifact | sha256 | Path |
|---|---|---|
| Pair D spec v1.3.1 | `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659` | `contracts/docs/superpowers/specs/2026-04-27-simple-beta-pair-d-design.md` |
| Pair D plan v2.4 | (no sha; revision-history-pinned) | `contracts/docs/superpowers/plans/2026-04-27-simple-beta-pair-d-implementation.md` |
| Joint panel | `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf` | `contracts/.scratch/simple-beta-pair-d/data/panel_combined.parquet` |
| Primary OLS results | `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf` | `contracts/.scratch/simple-beta-pair-d/results/primary_ols.json` |
| Robustness pack | `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904` | `contracts/.scratch/simple-beta-pair-d/results/robustness_pack.json` |
| VERDICT.md | `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf` | `contracts/.scratch/simple-beta-pair-d/results/VERDICT.md` |
| MEMO.md (post-Phase-3 narrative tightening + §7 CPO revision) | (re-compute on commit) | `contracts/.scratch/simple-beta-pair-d/results/MEMO.md` |
| Imported CPO framework (`DRAFT.md` from `~/learning/cfmm-theory/macro-markets/`) | byte-identical to source | `contracts/notes/2026-04-29-macro-markets-draft-import.md` |
| Pair D notebooks (executed) | per env.py pin chain | `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/` |

---

## §1. Mandate

Author the **ideal-scenario M-sketch** (Stage-2 deliverable per CLAUDE.md framework) for the Pair D Convex Payoff Option (CPO). The CPO intermediates between two real-world flows already present in the Celo ecosystem:

- **Demand side (a_s):** Colombian wage-earner pays fixed-local-currency obligations (bills, airtime, data, remittance) while holding USD-pegged stable; exposed to σ(COP/USD) — Δ < 0
- **Supply side (a_l):** DeFi LP earns swap fees from local-stable ↔ USD-stable turnover on Mento V3 FPMM (or Uniswap V3/V4 concentrated-liquidity equivalent); exposed to σ(COP/USD) — Δ > 0

The M-sketch packages the existing supply-side cash-flow shape `CF^(a_l) = Σ r·|FX_t − FX_{t−1}|` as a tradable convex hedge `Π(σ_T)` that the demand-side a_s can purchase. Equilibrium per the imported framework: `K_l = K_s`. Replication via Carr-Madan as a strip of OTM puts and calls, implemented as IronCondors on Panoptic.

**Stage-2 closure criterion:** a deployable position-construction specification that *would* settle the empirically-confirmed Y-on-X relationship if LP capital existed. Liquidity sourcing is **explicitly out of scope** (Stage-3).

---

## §2. Empirical anchor (load-bearing input from Stage-1)

Pair D simple-β empirical validation closed PASS 2026-04-28 PM late evening:

- **β_composite = +0.13670985, HAC SE 0.02465, t = +5.5456, p_one = 1.46×10⁻⁸**
- Lag pattern β_6/β_9/β_12 = +/+/+ (β_6 alone ≈ 80% of composite → **lag-6 dominance**, RC FLAG #3)
- Robustness R1-R4 all sign-AGREE (0/4 flips per spec §7.1); SUBSTRATE_TOO_NOISY does not fire
- §3.3 Clause-A ESCALATE does not fire; §3.4 Clause-B / B-ii do not fire
- Joint per spec §8.1 step 4(a): **PASS, Stage-2 unblocked**

**The empirical claim that travels into the M-sketch:** A 1% peso devaluation today is associated with a measurable rise in the young-worker services share *concentrated at the 6-month horizon, within (but not uniformly across) the 6-12mo BPO-contracting window*. The relationship is statistically extremely strong AND the *correlation* is identified; the *causal channel* is not (RC FLAG #1).

---

## §3. CPO mathematical framework (from imported `DRAFT.md`)

**Cash-flow definition:**
```
CF^(a)_T = inflow I^(a)_T(σ(X/Y)) − outflow O^(a)_T(σ(X/Y))
Δ^(a)   = ∂CF/∂σ(X/Y)
Γ^(a)   = ∂²CF/∂σ(X/Y)²
```

**Two agent specifications (a_s and a_l):**
- a_s ("Pay Bill in X using MiniPay"): Δ^(a_s) < 0 (fixed local-currency obligation, hurt by σ)
- a_l ("US Yield MiniApp"): Δ^(a_l) > 0 (yield from FX turnover, helped by σ)

**Simplest deterministic instantiation (imported framework §"Models"):**
- a_l yield: `CF^(a_l)_T = Σ_t r_(a_l) · |(X/Y)_t − (X/Y)_{t-1}|`
- a_s obligation: `CF^(a_s)_T = Υ_T(r, θ·D₀^(Y), T) − Σ_t q_t / (X/Y)_t`
  where `Υ` is the yield-vault portion at allocation θ, and `Σ q_t·(X/Y)_t = B_T` is the path-dependent cost-minimization objective

**Deterministic perturbation path (imported framework):**
```
(X/Y)_t(ε,ω) = (1 + ε·(cos²(ωt) − 1/2)) · (X/Y)̄
σ_T = (1/T) Σ ((X/Y)_t − (X/Y)̄)²
ε(σ_T) = √(8·σ_T / (X/Y)̄²)
```

**Δ derivation (imported framework, key identity):**
```
Δ^(a_l) = (4·r_(a_l) / ((X/Y)̄·ε(σ_T))) · Σ |f_t − f_{t-1}|  > 0
Δ^(a_s) = (4 / ((X/Y)̄·ε(σ_T))) · Σ q_t · f_t / (X/Y)_t²    < 0
where f_t := cos²(ωt) − 1/2
```

**CPO equilibrium (imported framework):**
```
Δ^(a_l + Π) = Δ^(a_l) + ∂Π/∂σ_T = 0
Δ^(a_s − Π) = Δ^(a_s) − ∂Π/∂σ_T = 0
⟹  Π(σ_T) = K·√σ_T   (with K_l = K_s for equilibrium)
```

**Carr-Madan replication (imported framework):**
After linearizing `√σ_T ≈ √σ₀ + (σ_T − σ₀)/(2√σ₀)`:
```
Π(σ_T) ≈ K̂·σ_T  where  K̂ := K*/(2√σ₀)
σ_T = ∫₀^S₀ P(K)/K² dK + ∫_S₀^∞ C(K)/K² dK
⟹  Π = K̂·(∫ OTM puts + ∫ OTM calls weighted 1/K²)
```

**Discrete Panoptic implementation:**
```
∫ OTM options ≈ Σ_{j=1}^N w_j · IronCondor_j
K_j ≈ S₀·exp(x_j),  Δ_K_j chosen,  w_j ∝ 1/K_j²
N = 3 condors (left-tail / ATM / right-tail) = 12 legs total
```

The imported framework explicitly notes "4 per position constraint is respected" — this maps cleanly onto Panoptic's per-position leg limits.

---

## §4. a_l candidate ranking (top-3 from 2026-04-30 catalog scan)

Top supply-side candidates by Δ-fit × deployment-readiness on Celo:

| Rank | Candidate | F (Δ-fit) | Deployment-readiness | Note |
|---|---|---|---|---|
| 1 | **Mento V3 FPMM LP on USDm/COPm pool** | 0.95 | V3 FPMM router live (`0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`); USDm/COPm pool existence to be confirmed by M-sketch agent | Direct Pair-D match: the X = COP/USD that Pair D validated IS the σ that drives this LP's fees. Mento V2 COPM = `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (canonical Mento-native; NOT `0xc92e8fc2…` Minteo-fintech) |
| 2 | **Uniswap V3/V4 concentrated-liquidity LP on Celo Mento-pair** (e.g., USDC/USDm, cUSD/cEUR) | 0.95 | Live; existing pools | Capital-efficient supply-side complement; range strategy pinned to lag-6-dominance (RC FLAG #3) |
| 3 | **Panoptic LP writing options on Celo Uniswap FX-pool** | 0.85 | Panoptic on Ethereum (per CLAUDE.md M-search 2026-04-27); Celo deployment is Stage-3 | Formal match to Π(σ_T) — premium income IS σ-priced revenue. Same protocol on both legs (LP supply + Π intermediation) |

Detailed enumeration: see "Yield-vault expanded universe" deliberation in conversation 2026-04-30 (also `contracts/notes/2026-04-29-macro-markets-draft-import.md` for the formal CF^(a_l) reference).

---

## §5. a_s candidate ranking (top-3 from 2026-04-30 catalog scan)

Top demand-side candidates by F × L (fit × liquidity) on MiniPay catalog:

| Rank | Candidate | Publisher | F | L | Note |
|---|---|---|---|---|---|
| 1 | **Bill Payments** | Bitgifty | 1.00 | high | Textbook CF^(a_s); fixed local-currency obligation; user holds USD-stable |
| 2 | **Airtime + Cheap Data Bundles** | Bitgifty | 0.90 | high | Recurring high-frequency local-currency micro-obligations; high σ exposure per dollar |
| 3 | **Walapay** | Walapay.io | 0.95 | NG/KE/GH/ZA/UG/NO/AE/SE | Cross-currency remittance reel (CO not yet covered; closest Africa-side proxy) |

Bitgifty publishes 4 of top-5 a_s slots → **natural integration counterparty for the demand-side leg**.

---

## §6. M-sketch deliverable scope

Author a code-agnostic spec (per `feedback_no_code_in_specs_or_plans`) covering:

1. **Position geometry.** Strike-grid `{K_j}` selection per Carr-Madan log-spacing `K_j = S₀·exp(x_j)`; weights `w_j ∝ 1/K_j²`; condor widths `Δ_K_j`. Three condors (left-tail / ATM / right-tail) = 12 Panoptic legs. Concrete proposal: pin `S₀` to current month-end COP/USD; pin `Δ_K_j` to spec-style σ-percentile bands derived from Pair-D residual variance.

2. **Payoff shape.** `Π(σ_T) ≈ K̂·σ_T` linearization with K̂ = K*/(2√σ₀). Sketch must specify (a) anchor `σ₀` (standing realized vol over what window?), (b) target `K̂` calibration (strike-spacing-implied vs explicit-fee-target).

3. **Reference-asset oracle structure.** Spec MUST settle against an on-chain price (NOT against Y directly — Y is monthly DANE GEIH, not on-chain). The oracle is **Mento V3 FPMM USDm/COPm pool spot price** for option (a) above, OR **Uniswap V3/V4 USDC/USDm pool spot** for option (b). Specify which AND specify the time-weighted-average-price (TWAP) window for settlement.

4. **Premium-funding cadence.** Wage-earner pays a recurring premium denominated in **COPm or USDm** (per CLAUDE.md "Iteration order"). Cadence: monthly aligned with bill-pay cycle. Premium budget envelope: ~$5-15 USD/month implied by Colombian young-worker median wage ~$300-500/month (small fraction).

5. **Term structure.** Single perpetual (Panoptic-native) vs roll-strategy on monthly-tenor positions. Imported framework explicitly notes "T is user-defined or defined by the demand side subject to its fixed-time obligations" — bias toward demand-side cadence (monthly, matching bill cycle).

6. **Convex-payoff direction.** Long-X (long COP-devaluation) per imported framework `Δ^(a_l) > 0` + `Δ^(a_s) < 0`. NO short-X leg in v1 (RC FLAG: symmetry test pending; one-sided-only is the safe v1 default until symmetry is validated).

7. **Funding-rate dynamics.** Panoptic perpetual options pay funding from longs to shorts; M-sketch must show that the wage-earner's premium-funded ratchet nets positive over the life-cycle. Out-of-scope to fully model funding-rate path; sketch must specify the *constraint* and flag funding-rate sensitivity for Stage-3 verification.

8. **Equilibrium-pricing framework.** `K_l = K_s` condition. Sketch must specify the price-discovery mechanism — does the Mento-LP fee yield (a_l) and the Bitgifty bill-pay-hedge premium (a_s) clear at the same `Π(σ_T)` price endogenously, or does the CPO need an active-market-maker layer? **This is the most important Stage-2 architectural decision.**

9. **CPO contract surface.** What does the user-facing contract look like? Sketch enumerates: subscription (a_s buys hedge), settlement (CPO fires when σ_T crosses threshold), payout currency, exit/redemption, edge cases (oracle deviation, Mento pool depeg, Panoptic-side liquidity exhaustion). Code-agnostic prose only.

10. **Anti-fishing inheritance from Pair D Phase-3 review (NON-NEGOTIABLE).**
    - **RC FLAG #1:** hedge the *correlation* between X and Y, NOT the *BPO causal channel*. M-sketch language must use "FX-vol-driven services-share movement" framing, NOT "BPO-mechanism hedge" framing.
    - **RC FLAG #3:** lag-6 dominance honored; settlement horizon biased toward 6-month, not uniformly 6-12mo.
    - **RC FLAG #5:** verdict-sensitive to brief-vs-spec; sketch must NOT smuggle a `marco2018_dummy`-equivalent post-data adjustment into the empirical anchor.
    - **RC FLAG #6:** window 2015-2026 over-represents post-2014 oil + COVID + Fed-tightening regimes; M-sketch must acknowledge that the CPO calibration inherits this regime-mix concern and flag re-calibration cadence as Stage-3 maintenance.

---

## §7. Hard constraints (NON-NEGOTIABLE per CLAUDE.md + spec §1 stage-discipline + Phase-A.0 lessons)

- **NO Stage-3 deployment claims.** Liquidity sourcing, LP-capital recruitment, wallet-onboarding flow, KYC/regulatory framing, marketing copy — all out of scope.
- **NO alternative (Y, X) pairs.** Pair D is the committed iteration; the M-sketch is for Pair D specifically.
- **NO empirical β re-litigation.** The Stage-1 PASS verdict is the load-bearing input; Stage-2 builds on it.
- **NO causal-channel claims for the BPO mechanism** (RC FLAG #1).
- **NO ζ-group escalation speculation.** The mean-OLS gate did not fire ESCALATE; speculation about hypothetical convex-payoff escalation findings is anti-fishing-banned per spec §9.
- **NO new yield-vault creation** (the imported framework explicitly identifies a_l as already existing in the Mento-LP universe; the M-sketch packages, does not invent).
- **NO Panoptic deployment work** (sketch only specifies the position geometry; actual deployment is Stage-3).
- **Stage-1 sha256 pin chain MUST remain frozen.** Any spec edit that would invalidate the v1.3.1 spec sha or the Phase-2 JSON shas is OUT OF SCOPE — the M-sketch is its own document, NOT a Stage-1 spec revision.
- **Code-agnostic per `feedback_no_code_in_specs_or_plans`.** Implementation specifics deferred to executor sub-agents per task.
- **HALT discipline applies** if the M-sketch agent encounters: (a) Mento V3 FPMM USDm/COPm pool does NOT exist (typed exception to surface to orchestrator → user-pivot disposition memo with ≥3 options); (b) Panoptic-on-Ethereum cannot reference a Mento Celo-side pool without bridging (typed exception → cross-chain feasibility memo); (c) any other architectural block requiring user adjudication. Auto-pivot is anti-fishing-banned.

---

## §8. Dispatch suggestion

**Owner:** Backend Architect (preferred — has Panoptic protocol depth) OR a Panoptic-domain specialist if available.
**Output location:** `contracts/docs/superpowers/specs/2026-04-XX-pair-d-stage-2-cpo-m-sketch.md` (NEW spec, NOT a revision of the Stage-1 Pair D spec). Plan revision can follow as `contracts/docs/superpowers/plans/2026-04-XX-pair-d-stage-2-cpo-implementation.md`.
**2-wave doc verification:** per `feedback_two_wave_doc_verification`, spec writes require Reality Checker + Workflow Architect parallel review before commit. Auto-mode override may be applied per user discretion.
**Initial focus order (orchestrator suggestion):**
1. §6.3 oracle structure (settle against which pool — most architecturally consequential)
2. §6.8 equilibrium-pricing mechanism (does K_l = K_s endogenously, or need MM?)
3. §6.1 + §6.2 position geometry + payoff shape (the Carr-Madan strip mechanics)
4. §6.5 term structure + §6.4 premium cadence (user-facing parameters)
5. §6.6 + §6.7 directional bias + funding-rate constraint
6. §6.9 contract surface (consolidation)
7. §6.10 anti-fishing inheritance check (final pass)

**Stage-3 entry gate (out of scope but for context):** real LP capital + execution test on a live Panoptic deployment (Ethereum-side or Celo-side after Panoptic-on-Celo deployment lands).

---

## §9. Cross-references

- Pair D MEMO §7 (post-2026-04-30 CPO revision): `contracts/.scratch/simple-beta-pair-d/results/MEMO.md`
- Pair D VERDICT.md: `contracts/.scratch/simple-beta-pair-d/results/VERDICT.md`
- Imported CPO framework: `contracts/notes/2026-04-29-macro-markets-draft-import.md`
- Pair D notebooks (executed): `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/`
- BPO research note (literature anchors): `contracts/.scratch/2026-04-27-colombian-bpo-non-industrialization-hedge-research.md`
- DANE GEIH feasibility report: `contracts/.scratch/2026-04-27-dane-geih-y-feasibility.md`
- Memory: `project_pair_d_phase2_pass` (verdict + sha-pin chain + Stage-2 inheritance)
- Memory: `project_abrigo_convex_instruments_inequality` (broader product thesis)
- Memory: `feedback_pathological_halt_anti_fishing_checkpoint` (HALT protocol)
- Memory: `feedback_two_wave_doc_verification` (spec-write verification)

---

**End of dispatch brief.** Authored 2026-04-30 PM under user-explicit auto-mode authorization. Ready for M-sketch agent dispatch on user signal.
