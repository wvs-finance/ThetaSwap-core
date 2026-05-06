---
artifact_kind: corrections_theta_substrate_scope_clarification_memo
correction_id: CORRECTIONS-θ
parent_spec: contracts/docs/superpowers/specs/2026-05-04-pair-d-stage-2-v1.5-data-aggregation-design.md (v1.1 sha 8deffe5c6ab4033454f45a1c837f686c8f3a7b6a16dadd5556283c2127c89a0f)
emit_timestamp_utc: 2026-05-04
trigger: user hypothesis confirmed 2026-05-04 — most LATAM developers pay AI APIs via fiat (Visa/Mastercard → COP debit card → bank-spread COP→USD conversion), NOT crypto rails
authority: feedback_pathological_halt_anti_fishing_checkpoint (HALT + disposition + user adjudication + CORRECTIONS-block + post-hoc verify)
companion_corrections: CORRECTIONS-η (decomposition; corrections_eta_decomposition.md)
---

# CORRECTIONS-θ — v1.5-data substrate-panel scope-claim sharpening

## §1. Why this CORRECTIONS-block fires

User raised the hypothesis 2026-05-04: "**Most Colombian developers pay through fiat, not crypto.**" Confirmed and load-bearing. The on-chain COP corridor (Mento V2 BiPool USDm/COPm, Mento V2 Broker, Minteo COPM Polygon, Num nCOP, Wenia COPW) flows are dominated by Littio/Minteo neobank settlement, remittances, merchant payments, and mev_arb — **NOT developer AI-API-spend transactions**. As a 2026 point-estimate, on-chain COP-corridor flow is empirically uncorrelated with developer AI tooling cost.

This challenges what v1.5-data's aggregate substrate panel CLAIMS to measure. Specifically: if v1.5-data were framed as "a_s developer-AI-spend observability for the dev-AI-cost iteration," that framing is EMPIRICALLY FALSE. CORRECTIONS-θ sharpens the scope claim to what the panel actually measures.

## §2. The scope-claim sharpening

### Old framing (v1.0 + v1.1 + EVM revisions)

Per CORRECTIONS-γ, the panel measured "structural exposure" (replacing the prior "behavioral demand" framing). This was an improvement over WTP-style language but left ambiguous *which* iteration's a_s the structural exposure mapped to. A future reader could (incorrectly) infer that v1.5-data substrate-aggregate measures developer-AI-cost a_s if the iteration pivot lands on the dev-AI-cost track.

### New framing (this CORRECTIONS-θ)

The v1.5-data substrate panel measures **COP-corridor LP/settlement-rail activity**:

1. **LP-side capacity**: how much aggregate stablecoin liquidity is deployable across the COP-corridor venues at audit_block (the LP-side of any USD/COP CPO settles into this corridor regardless of which population the hedge serves)
2. **Settlement-rail throughput**: per-venue weekly flow as a measure of **available infrastructure capacity** for hedge premium / payout cash-flow
3. **X-side reference panel**: COP/USD spot price discovery via Mento V2 BiPool (already pinned as USD-anchor backup at v1.5-data §6)

The panel does NOT measure:
- **a_s developer-AI-spend observability** for the dev-AI-cost iteration — that activity is overwhelmingly fiat-rail today
- **a_s any-population observability** for any iteration where the population's structural exposure is denominated in fiat-rail spend rather than crypto-rail spend
- **General Colombian economic activity** — flows are issuer-concentrated (Mento protocol-side, Minteo neobank, Wenia institutional-treasury, Num yield-bearing) and don't represent population-broad economic exposure

## §3. Why Pair D Stage-1 PASS is unaffected

Pair D Stage-1 β=+0.137 (p=1.46e-08, 2026-04-28) used:
- **Y**: Colombian young-worker services-sector employment share, sourced from **DANE GEIH** monthly micro-data (off-chain labor survey)
- **X**: COP/USD lagged 6-12mo, sourced from **Banrep TRM** API (off-chain FX reference)

Neither variable required on-chain observability. The fiat-vs-crypto question doesn't compromise the Stage-1 result.

The v1.5-data substrate panel was always part of the **M-side / settlement-rail design space**, not the Stage-1 empirical input. CORRECTIONS-η §1 records this scope explicitly: v1.5-data scope is "data collection ONLY: substrate scope + per-venue audit + aggregation methodology + USD-equivalence pipeline + N_INFORMATIVE measurement protocol + AR(1) diagnostic emission + σ-anchor coverage assessment. NO statistical methodology pre-commits." None of that text claims a_s observability.

CORRECTIONS-θ sharpens the scope claim consistent with what the spec already does, removing ambiguity that could drift toward a false a_s-observability claim.

## §4. Implications for the dev-AI-cost iteration

The user's hypothesis-confirmation 2026-05-04 anchors a NEW iteration sketch:
- **Population**: LATAM developers paying USD-denominated AI APIs / AI tooling (Colombia primary; Mexico, Brazil, Argentina, Peru, Chile broader)
- **a_s exposure**: AI tooling cost in USD; payment rail TODAY is fiat-dominated
- **X candidate**: USD/COP (or USD/local-FX) — same axis as Pair D, different transmission

For Stage-1 β work on this iteration:
- Y data is **off-chain** (parallel to Pair D's DANE GEIH approach):
  - Colombia: DANE ICT-sector wage + employment series; Banrep trade-in-services import data (AI APIs as service imports)
  - Mexico: INEGI ICT-sector
  - Brazil: IBGE ICT-sector + Banco Central trade-in-services
  - Argentina: INDEC ICT
  - Cross-LATAM: Stack Overflow Developer Survey LATAM AI-tooling adoption series; GitHub Octoverse LATAM activity
- The v1.5-data substrate panel **does NOT serve as Stage-1 empirical input** for this iteration. It serves as **future-iteration LP/settlement-rail readiness panel** IF the dev iteration progresses to Stage-2 / Stage-3.

The Superfluid + X402 protocol research dispatched 2026-05-04 maps the **on-chain trajectory** for AI-spend payment rails — not current substrate observability. Per CLAUDE.md Abrigo "ideal-scenario clause": empirical β-estimation is independent of on-chain deployment; the ideal-scenario M-sketch step requires a Panoptic-position construction that *would* settle the empirical β if deployed; only the deployment step requires real LP capital + rail-adoption.

## §5. Preserved guarantees

CORRECTIONS-θ is a **scope-claim sharpening**, not a structural change. The following are PRESERVED VERBATIM:

- W1-W5 weight invariants (§5.2 + §12)
- Per-venue audit thresholds PASS / MARGINAL / HALT (§4)
- Output deliverables schema (§10)
- Free-tier budget pin (§11; CORRECTIONS-δ inheritance)
- Anti-fishing typed exceptions (§12)
- All 11 pre-commitment invariants from §13
- §16 pre-conditions for v1.5-methodology authoring
- Stage-3 forward-note firewall (§13 invariant 11)
- HyperEVM/MegaETH discovery NULL closure (§3 rows 11-12; §16 #9)

The CHANGES are limited to:
- §1 add a "Substrate-panel scope claim" subsection (~200 words)
- §13 add invariant 12: substrate panel measures LP/settlement-rail activity, NOT a_s observability for any iteration
- §17 (NEW) add explicit cross-iteration applicability table:
  - Pair D iteration (Y₁ = young-worker services share): substrate panel = M-side / settlement-rail readiness; Stage-1 β PASS already complete via off-chain DANE+Banrep
  - Dev-AI-cost iteration (Y₂ = TBD pending feasibility research): substrate panel = future-iteration LP/settlement-rail readiness IF iteration progresses; Stage-1 β work uses off-chain LATAM ICT-sector data

## §6. Anti-fishing invariant: this CORRECTIONS-block is itself anti-fishing-proof

Per `feedback_pathological_halt_anti_fishing_checkpoint`, a CORRECTIONS-block is valid only when:
- (a) Triggered by an external signal — ✓ (user hypothesis 2026-05-04)
- (b) Disposition with ≥3 pivot options enumerated — N/A (this is a SCOPE CLARIFICATION, not a substantive pivot; methodologically nothing changes; pivot enumeration would be theater)
- (c) User adjudication — ✓ (user confirmed 2026-05-04 verbatim "confirmed")
- (d) Old + new + preserved-guarantees argument — ✓ (§2 + §5 above)
- (e) Post-hoc verify on the result — ✓ (queued: single-wave RC diff-verify on the v1.5-data v1.1 → v1.2 delta)

NO threshold was relaxed. NO methodology was weakened. The scope claim is SHARPENED to what the spec already does, removing ambiguity that could drift toward a false a_s-observability claim under future iterations.

End of CORRECTIONS-θ.
