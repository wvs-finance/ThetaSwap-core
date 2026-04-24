# Phase-A.0 EXIT Disposition Memo

**Date:** 2026-04-24
**Plan reference:** Rev-4.1, Task 11.K Step 4 (`contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `28e0ba227`)
**Verdict:** `EXIT_NON_REMITTANCE`
**Decision maker:** user, 2026-04-24
**Pivot direction:** open — brainstorm under way for "payments mirroring consumption" niche

---

## Kill criteria fired

Evaluated against Task 11.F Axis-1 evidence at `contracts/.scratch/2026-04-24-ccop-peak-day-event-research.md` and cumulative prior-research corpus. Axes 2–5 were NOT completed because Axis-1 evidence was already overwhelming.

### k1 (intent non-remittance dominant) — FIRE

Task 11.F Axis 1 classified the top 30 single-day flow events. **Zero of 30 days show a remittance fingerprint.** Breakdown:

| Classification | Days | Share |
|---|---|---|
| TRM-arbitrage alignment (≥\|25\| COP daily BanRep move) | 11 | 37% |
| Treasury/bot roundtripping (inflow ≈ outflow to <1%, low unique senders) | 15 | 50% |
| Campaign/airdrop outlier (2025-07-31, 2,402 senders vs median ~30) | 1 | 3% |
| Event / conference (Blockchain Summit Latam Medellín 2025-11-12/14) | 1 | 3% |
| Ambiguous / unclassified | 2 | 7% |

Minimum non-remittance volume share: 87% of peak-day volume is TRM-arbitrage + treasury/bot + campaigns. The k1 threshold (>70% non-remittance) is fired at a conservative lower bound.

### k2 (data-source provenance) — PARTIAL FIRE

Task 11.F surfaced that the `CCOP_COPM_MIGRATION_DATE = 2026-01-25` constant in `contracts/scripts/dune_onchain_flow_fetcher.py` is **uncorroborated by public Celo/Mento governance records**:

- MGP-12 (cCOP migration vote) went live 2025-12-05 — not 2026-01-25.
- MGP-16 (cCOP/BRLm renaming proposal) posted 2026-02-13 — not 2026-01-25.
- Source: `contracts/.scratch/2026-04-24-ccop-peak-day-event-research.md` citing `forum.celo.org` and `forum.mento.org` threads.

This is a load-bearing provenance error in the spec Rev-1.1.1 F-3.1-2 footnote. It does not alone reach the 2× double-counting k2 threshold, but combined with the absence of a completed Axis-3 verification audit, the data-source trust chain is compromised enough to qualify as `DATA_SOURCE_SUSPECT`.

### k3 (filter argmax) — NOT EVALUATED

Phase 1.5.5 did not proceed to Task 11.H. k3 is moot under this EXIT.

### k4 (tx-size payment-not-remittance) — STRONGLY IMPLIED (not formally evaluated)

Panel cumulative volume ($35.8M cCOP + $1.2M COPM = ~$37M) versus Mento protocol's cCOP TVL ~$75k as of June 2025 (per `CELO_ECOSYSTEM_USERS.md:153`) implies volume/TVL ratio ≈ 500×. Interpretations:

- High-velocity payments usage (consistent with k1's classification)
- OR double-counting in the Dune transfer aggregation (consistent with k2)

Either interpretation rules out remittance as the dominant use case (remittance transactions are infrequent, not 500× velocity).

### Additional corroborating evidence (cumulative across the exercise)

- Task 11.C FAIL-BRIDGE at `contracts/notebooks/fx_vol_remittance_surprise/Colombia/0B_bridge_validation.ipynb` — ρ=+0.7554 at quarterly levels but 2-of-5 quarter-over-quarter sign-concordance. Levels correlated with secular trend; deltas do not co-move.
- Top-5 single-day events balanced to 7th decimal: 2025-09-18 inflow=$429,592.26 / outflow=$429,592.27 — textbook roundtripping.
- Prior research corpus explicitly warned against this failure mode:
  - `CELO_ECOSYSTEM_USERS.md:157`: "cCOP user base is small and concentrated in Medellín-area early adopters"
  - `2026-04-02-ccop-qa-audit.md:73`: "56 addresses with 1,300-1,600 txns each — power users, likely apps or payment processors, NOT representative of the typical income converter"
  - `2026-04-02-ccop-cop-usd-flow-response.md:74`: "The on-chain sample is not representative of ALL Colombian income converters"
  - Pre-registered mitigation "S3 top-22-power-user exclusion" in prior spec was NOT inherited into Rev-1/1.1/1.1.1.

---

## EXIT disposition

Phase-A.0's original question — "does an on-chain remittance-proxy flow signal predict COP/USD realized volatility?" — is **CLOSED** with verdict `EXIT_NON_REMITTANCE`.

The closure is NOT a failure of the CPI-style gate test; it is a failure upstream at the X-construction stage. The on-chain cCOP/COPM aggregate from Dune query #7366593 does not measure household remittance. It measures a mixture of TRM-arbitrage, treasury operations, bot roundtripping, campaign/airdrop events, and a small tail of legitimate retail activity. No filter applied post-hoc to this aggregate can reconstruct a remittance signal that was not captured at the source.

This is the same intellectual-honesty discipline that closed the CPI-surprise exercise on 2026-04-19 (`project_fx_vol_cpi_notebook_complete.md`). "No signal here" is a valid scientific outcome.

---

## Artifacts preserved (reusable under pivot)

Infrastructure built for Phase-A.0 remittance remains usable under any pivot that works with daily on-chain flow as X:

- `contracts/scripts/dune_onchain_flow_fetcher.py` (Task 11.A) — Dune loader; requires migration-date constant re-verification before reuse
- `contracts/data/copm_ccop_daily_flow.csv` — 585 daily rows raw data
- `contracts/scripts/weekly_onchain_flow_vector.py` (Task 11.B) — 6-channel weekly aggregator
- `contracts/scripts/cleaning.py` extensions (Task 9), `surprise_constructor.py` (Task 10), decision-hash scaffolding
- Rev-4.1 Phase-1.5.5 plan template (Tasks 11.F/K structure — research + kill criterion — is reusable under any X-construction pivot)

## Artifacts retired

- Rev-1, Rev-1.1, Rev-1.1.1 specs at `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` and `-design.md` — SUPERSEDED + RETIRED
- Task 11.C bridge-validation notebook — retire in-place, archive at current commit; any pivot builds a new bridge against a new Y (not BanRep remittance)
- Task 11.D spec patches, Task 11.E 3-way reviews — archive in `.scratch`, no further action
- Plan Tasks 11.G/H/I/J as written — retire; pivot may re-use the brainstorm → iterate → spec → review structure under a new Y

---

## Pivot direction (user-directed, 2026-04-24)

User approved EXIT and directed next step toward "payments mirroring consumption" niche: where does cCOP/COPM data legitimately map to a Colombian economic observable?

Leading hypotheses for the brainstorming session that follows this memo:

1. **Retail-payment surprise → TRM-RV** (Pivot-α from Rev-4.1 plan): on-chain retail-sized transaction activity (filtered to the $10–$50 range per `CELO_ECOSYSTEM_USERS.md:127`) as an X proxy for Colombian retail consumption; validation anchor = DANE EMCM retail-sales monthly or BanRep Colombian Consumer Confidence Index (ICCE).
2. **TRM-arbitrage intensity → TRM-RV**: the 37% TRM-move-aligned peak days are evidence that on-chain flow RESPONDS to TRM shocks; inverting the causal direction yields a different exercise — "does on-chain arbitrage intensity predict subsequent RV?" This is a market-microstructure question, not a macro one.
3. **Bot-flow concentration → nothing meaningful** — if flows are dominantly automated, there is no macro observable to extract.
4. **Completely different Y×X cell** from `project_colombia_yx_matrix.md` — abandon cCOP entirely, pick a cell that doesn't depend on cCOP's narrow user base.

Next session: invoke `superpowers:brainstorming` skill to evaluate these hypotheses against the data we already have + what additional data would be required.

---

## Memory-file updates (this commit)

- `project_phase_a0_remittance_execution_state.md` → mark CLOSED with EXIT_NON_REMITTANCE verdict; preserve resume-state history for audit
- NEW: `project_phase_a0_exit_verdict.md` → summary-level pointer to this memo
- `project_colombia_yx_matrix.md` → annotate the remittance cell as CLOSED_NON_REPRESENTATIVE (pending — to be updated at next memory-update pass)

## Related commits

- Plan Rev-4.1 at `28e0ba227`
- Plan Rev-4 at `dded7d637`
- Rev-1.1.1 spec at `ac5189363` (SUPERSEDED)
- Task 11.C FAIL-BRIDGE notebook at `91e5d2664`
- Task 11.B weekly aggregator at `2bff6d79f`
- Task 11.A Dune loader at `bc12e3c30`
- Task 11 BanRep quarterly fixture at `939df12e1`
