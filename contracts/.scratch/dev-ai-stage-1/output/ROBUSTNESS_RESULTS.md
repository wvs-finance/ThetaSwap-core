---
spec_sha256_v1_0_2: "d90f6302f9473aa938521ed0b7a9b58dc1c849cd74476cd90424f59f3bd3f37e"
spec_decision_hash: "7c72292516f58f3cf2d16464d4f84c3e7d7270ad2c5d3d8ed8fef6b3b2751f5a"
spec_relpath: "contracts/docs/superpowers/specs/2026-05-04-dev-ai-stage-1-simple-beta-design.md"
plan_sha256_v1_1_1: "772b52e1f4b4e9e0ed964c3068b1948c24d5cfe27afc109e8e589a1ea790c036"
plan_relpath: "contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md"
panel_combined_sha256: "451f4c615c89a481da4ca132c79a55b04e00eecb9199746f544b22561ba0740d"
emit_timestamp_utc: "2026-05-06T09:34:22Z"
provisional_flag: false  # R1-R4 finalized; NB02 PRIMARY_RESULTS.md / gate_verdict.json provisional_flag flips to false on this trio's classification
sample_window:
  start: "2015-01"
  end: "2026-03"
n_realized: 134
n_min: 75
r_row_classification: "MIXED"
n_agree: 3
n_disagree: 1
substrate_too_noisy: false
kappa_pair_clears: true
routing_branch: "§3.3 Clause-B"
status: POPULATED  # this artifact is populated at execution time; skeleton-fields above are placeholders only at trio-authoring time
---

# Dev-AI Stage-1 simple-β — ROBUSTNESS_RESULTS

> **Trio 5 emission per plan v1.1.1 Task 2.4 Step 5**: §7.1 R-row consistency classification + §3.5 SUBSTRATE_TOO_NOISY check + §6 v1.0.2 κ-tightened pair determination + final routing per §8.1 step 2 + §3.3 + κ-overlay.

## §1 R-row sign tally (4-arm robustness universe)

| arm | β_composite | sign | sign-AGREE vs primary |
|-----|-------------|------|-----------------------|
| primary | -0.14613187 | -1 | (reference) |
| R1 (regime_2021 dummy) | -0.51294441 | -1 | True |
| R2 (Section M Y_s2)    | +0.45482801 | +1 | False |
| R3 (raw OLS, no logit) | -0.00339875 | -1 | True |
| R4 (HAC SE; same β̂)    | -0.14613187 | -1 | True (trivial per §7 R4) |

## §2 §7.1 R-row consistency classification

- `n_agree = 3/4`; `n_disagree = 1/4`
- **Classification: `MIXED`** per spec §7.1 verbatim threshold (AGREE = 4/4 sign-preserved; MIXED = 1 or 2 sign-flipped; DISAGREE = 3 or 4 sign-flipped).
- Pair D R-AGREE 0/4 sign-flips precedent (memory `project_pair_d_phase2_pass`); this iteration: MIXED 1/4 sign-flips.

## §3 §3.5 SUBSTRATE_TOO_NOISY check

- Trigger condition: `n_disagree ≥ 3` (spec §3.5 'more than 50% of 4 = strictly > 2/4').
- **SUBSTRATE_TOO_NOISY = `False`** (n_disagree = 1).

## §4 §6 v1.0.2 κ-tightened pair status (R1 + R3)

- R1 sign-AGREE: `True`
- R3 sign-AGREE: `True`
- **κ-pair clears (R1 AND R3 BOTH AGREE) = `True`**.
- κ-tightening overrides §7.1 aggregate per §6 v1.0.2 sub-paragraph: if R1 OR R3 sign-different from primary, Clause-A FIRES regardless of §7.1 AGREE/MIXED classification.

## §5 Final routing per §8.1 step 2 + §3.3 + §6 v1.0.2 κ-overlay

- routing_branch: `§3.3 Clause-B`
- final_routing: ESCALATE Clause-B per §3.3 step 2 (MIXED classification); §3.3 B-i+B-ii numerical check governs
- Decision flow (4-step deterministic, per Why-markdown §6 'Relevance to results'):
  1. SUBSTRATE_TOO_NOISY check → not fired
  2. κ-pair check → CLEARED
  3. §7.1 classification → MIXED
  4. Final → §3.3 Clause-B

## §6 NB02 Trio 3 PRIMARY_RESULTS.md / gate_verdict.json status update directive

- `provisional_flag` flips from `true` (PROVISIONAL_PENDING_NB03) to `false` (R1-R4 finalized) on this trio's classification.
- `r_consistency.status` field updates from `PENDING_NB03` to the final §7.1 classification: MIXED.
- NB02 Trio 3 verdict label resolves from `PROVISIONAL_<verdict>` to a final-resolved verdict per §8.1 verdict-tree branch determined by (R-consistency, primary β-sign, primary p-one, Clause-B-fires?) tuple. Final verdict to be emitted in NB02 Trio 3's POPULATED PRIMARY_RESULTS.md / gate_verdict.json on full notebook re-execution.

---

**Trio 5 STATUS:** authored; awaiting orchestrator review per `feedback_notebook_trio_checkpoint`. Per `feedback_notebook_trio_checkpoint` no further trio cells are authored in this dispatch. Trio 6 (CONDITIONAL escalation suite per spec §5.5 if §3.3 ESCALATE-trigger fires OR SUBSTRATE_TOO_NOISY) is NOT authored here; orchestrator decides whether to dispatch Trio 6 based on this trio's routing_branch outcome.
