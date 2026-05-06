---
spec_sha256_v1_0_2: "d90f6302f9473aa938521ed0b7a9b58dc1c849cd74476cd90424f59f3bd3f37e"
spec_decision_hash: "7c72292516f58f3cf2d16464d4f84c3e7d7270ad2c5d3d8ed8fef6b3b2751f5a"
spec_relpath: "contracts/docs/superpowers/specs/2026-05-04-dev-ai-stage-1-simple-beta-design.md"
plan_sha256_v1_1_1: "772b52e1f4b4e9e0ed964c3068b1948c24d5cfe27afc109e8e589a1ea790c036"
plan_relpath: "contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md"
panel_combined_sha256: "451f4c615c89a481da4ca132c79a55b04e00eecb9199746f544b22561ba0740d"
emit_timestamp_utc: "TBD-AT-EXECUTION"
provisional_flag: false
sample_window:
  start: "2015-01"
  end: "2026-03"
n_realized: 134
n_min: 75
r_row_classification: "TBD-AT-EXECUTION"
n_agree: "TBD-AT-EXECUTION"
n_disagree: "TBD-AT-EXECUTION"
substrate_too_noisy: "TBD-AT-EXECUTION"
kappa_pair_clears: "TBD-AT-EXECUTION"
routing_branch: "TBD-AT-EXECUTION"
status: SKELETON
---

# Dev-AI Stage-1 simple-β — ROBUSTNESS_RESULTS

> **STATUS: SKELETON** — this file is a TEMPLATE emitted by the Phase 2 Task 2.4 Trio 5 authoring step
> (NB03 Trio 5 cell `nb03-trio5-code`). At notebook-execution time, this skeleton is OVERWRITTEN by
> the populated ROBUSTNESS_RESULTS.md with computed numerics, §7.1 classification, §3.5 SUBSTRATE
> check, §6 v1.0.2 κ-pair status, and final routing per §8.1 step 2 + §3.3 + κ-overlay. Do NOT consume
> this skeleton as the canonical robustness result — wait until the notebook executes and replaces it
> with the populated artifact (`status: POPULATED`; `r_row_classification ≠ "TBD-AT-EXECUTION"`).

## Skeleton structure (populated at execution)

The notebook code cell emits 6 sections per spec §9.17(b) Phase-3 result-memo §11.X(b) disclosure
pre-pin + §8.1 step 2 routing + §3.5 SUBSTRATE_TOO_NOISY check + §6 v1.0.2 κ-tightened pair check:

- **§1 R-row sign tally** — 5-row table with arm name, `β_composite`, sign, sign-AGREE flag for primary
  + R1 + R2 + R3 + R4. R4 is trivially-AGREE per spec §7 R4 verbatim "same point estimate" language.
- **§2 §7.1 R-row consistency classification** — `n_agree`, `n_disagree`, classification ∈
  {AGREE, MIXED, DISAGREE} per spec §7.1 verbatim threshold; Pair D R-AGREE 0/4 sign-flips precedent
  contrast.
- **§3 §3.5 SUBSTRATE_TOO_NOISY check** — trigger condition `n_disagree ≥ 3` per spec §3.5 verbatim;
  TRIGGERED / NOT-TRIGGERED state.
- **§4 §6 v1.0.2 κ-tightened pair status** — R1 + R3 individual sign-AGREE; κ-pair-clears boolean
  (BOTH AGREE required); κ-tightening overrides §7.1 aggregate per spec §6 v1.0.2 sub-paragraph.
- **§5 Final routing per §8.1 step 2 + §3.3 + §6 v1.0.2 κ-overlay** — 4-step deterministic decision
  flow: (1) SUBSTRATE_TOO_NOISY check; (2) κ-pair check; (3) §7.1 classification; (4) final
  routing_branch ∈ {`§3.5`, `§6 v1.0.2 κ-tightening`, `§8.1 step 2`, `§3.3 Clause-B`,
  `§8.1 step 4(a-e) primary`}.
- **§6 NB02 Trio 3 status update directive** — `provisional_flag` flips from `true` to `false`;
  `r_consistency.status` updates from `PENDING_NB03` to final §7.1 classification; verdict label
  resolves from `PROVISIONAL_<verdict>` to final-resolved verdict per §8.1 verdict-tree branch.

## Pre-pinned content blocks (populated at execution)

Per spec §9.17(b) Phase-3 result-memo §11.X(b) disclosure pre-pin VERBATIM: *"Comparison of primary
`β̂_composite` to R1 (2021 regime dummy) and R3 (raw-OLS) `β̂_composite` values, with explicit
sign-AGREE-or-ESCALATE adjudication per §6 v1.0.2 κ-tightened condition: report primary
`β̂_composite`, R1 `β̂_composite`, R3 `β̂_composite` as a 3-row table; classify each R-row as
sign-AGREE or sign-DIFFERENT relative to primary; if either R1 OR R3 is sign-DIFFERENT, the verdict
re-routes from PASS to ESCALATE per §6 v1.0.2 κ-tightening regardless of §7.1 aggregate
classification."* The §1 R-row sign tally + §4 κ-tightened pair status sections of this file supply
this 3-row table verbatim for Phase-3 result memo §11.X(b) inheritance.

## Trio-6 dispatch condition (populated at execution)

- **If routing_branch = `§3.5` (SUBSTRATE_TOO_NOISY) OR `§6 v1.0.2 κ-tightening` (Clause-A FIRES via
  κ-pair-not-clears) OR `§3.3 Clause-B` (MIXED + Clause-B numerical check)**: Trio 6 dispatch
  REQUIRED — §5.5 escalation suite must run per §3.4 disjunctive ESCALATE-PASS criteria.
- **If routing_branch = `§8.1 step 4(a-e) primary`** (R-AGREE + κ-pair-clears): Trio 6 dispatch NOT
  required for verdict integrity; orchestrator may author Trio 6 for §9.6 disjunction completeness
  per Pair D pre-authorization-evidence-not-rescue precedent.

---

**Trio 5 STATUS:** authored (skeleton); awaiting notebook execution to populate. Per
`feedback_notebook_trio_checkpoint` no further trio cells are authored in this dispatch. Trio 6
(CONDITIONAL escalation suite per spec §5.5 if §3.3 ESCALATE-trigger fires OR SUBSTRATE_TOO_NOISY) is
NOT authored here; the orchestrator decides whether to dispatch Trio 6 based on this trio's
routing_branch outcome.
