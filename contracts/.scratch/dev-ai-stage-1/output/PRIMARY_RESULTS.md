---
spec_sha256_v1_0_2: "d90f6302f9473aa938521ed0b7a9b58dc1c849cd74476cd90424f59f3bd3f37e"
spec_decision_hash: "7c72292516f58f3cf2d16464d4f84c3e7d7270ad2c5d3d8ed8fef6b3b2751f5a"
spec_relpath: "contracts/docs/superpowers/specs/2026-05-04-dev-ai-stage-1-simple-beta-design.md"
plan_sha256_v1_1_1: "772b52e1f4b4e9e0ed964c3068b1948c24d5cfe27afc109e8e589a1ea790c036"
plan_relpath: "contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md"
panel_combined_sha256: "451f4c615c89a481da4ca132c79a55b04e00eecb9199746f544b22561ba0740d"
emit_timestamp_utc: "TBD-AT-EXECUTION"
provisional_flag: true
sample_window:
  start: "2015-01"
  end: "2026-03"
n_realized: 134
n_min: 75
verdict: "TBD-AT-EXECUTION"
verdict_raw: "TBD-AT-EXECUTION"
branch_taken: "TBD-AT-EXECUTION"
status: SKELETON
---

# Dev-AI Stage-1 simple-β — PRIMARY_RESULTS

> **STATUS: SKELETON** — this file is a TEMPLATE emitted by the Phase 2 Task 2.3 Trio 3 authoring step
> (NB02 Trio 3 cell `nb02-trio3-code`). At notebook-execution time, this skeleton is OVERWRITTEN by
> the populated PRIMARY_RESULTS.md with computed numerics, verdict-tree trace, and §11.X disclosure
> content. Do NOT consume this skeleton as the canonical result — wait until the notebook executes
> and replaces it with the populated artifact (verdict ≠ "TBD-AT-EXECUTION").

## Skeleton structure (populated at execution)

The notebook code cell emits 7 sections per spec §9.17 + §9.16 disclosure pre-pin:

- **§1 Verdict outcome** — populated with `PROVISIONAL_<status>` label per spec §6 v1.0.2
  CORRECTIONS-κ (final status conditional on NB03 R1+R3 sign-AGREE).
- **§2 Primary numerics** — table with `β̂_composite`, `SE_composite_HAC`, `t_composite`,
  `p_one_HAC`, realized `N`, `N_MIN` gate per spec §3.6.
- **§3 Lag-pattern decomposition** — per-lag `β̂_6 / β̂_9 / β̂_12` table with HAC SE +
  share-of-composite percentages; Pair D contrast inheriting `β_composite = +0.13670985`,
  HAC SE `0.02465`, t = `+5.5456`, p_one = `1.46e-08`, β_6 ≈ 80% of composite (RC FLAG #3).
- **§4 Verdict-tree §8.1 trace** — bullet list of mapping rules applied in order (step 1 N gate,
  step 2 R-consistency, step 4 primary evaluation a-e); `branch_taken` label naming the §8.1 rule.
- **§5 Compositional-accounting disclosure (spec §9.16)** — three pre-pinned content blocks:
  - (a) ambiguity acknowledgment (Section J ⊂ Pair D Section G–T strict-subset);
  - (b) `β_composite_section_J` vs `β_composite_pair_D_inherited` comparison verbatim;
  - (c) flagged-not-resolved status on (i) dev-AI mechanism vs (ii) Section J's compositional
    contribution to Pair D PASS.
- **§6 CORRECTIONS-κ §11.X disclosure preview (spec §9.17)** — four pre-pinned content blocks:
  - (a) verbatim FLAG-A + FLAG-B citation (`cell_count [94, 267]`, `raw_share [0.014, 0.031]`,
    logit-derivative `[33, 73]`, 3-7× larger than v1.0.1 baseline 2.34×) + Trio-3 NB01
    disambiguation table cross-reference (linear within-range 2.78×–3.00× / cross-corner 6.52× /
    variance 7.73×–9.00× / 42.5× / combined 14400× worst-corner / 350× typical);
  - (b) primary-vs-R1-vs-R3 sign-AGREE-or-ESCALATE adjudication 3-row table-skeleton
    (R1 + R3 columns NB03-PENDING);
  - (c) 94-cell rare-month (2024-10-31) R1-coverage acknowledgment;
  - (d) Divisions 62-63 vs 58-61 sub-aggregate-substitutability ASR mapping for Stage-2.
- **§7 NB03 dispatch directive** — required next regardless of NB02 verdict; finalizes
  R-consistency + R1+R3 sign-AGREE adjudication + (if ESCALATE) §5.5 escalation suite.

## Pin-references (load-bearing)

The populated artifact will quote:

- Spec sha256 (v1.0.2): `d90f6302f9473aa938521ed0b7a9b58dc1c849cd74476cd90424f59f3bd3f37e`
- Spec decision_hash (v1.0.2): `7c72292516f58f3cf2d16464d4f84c3e7d7270ad2c5d3d8ed8fef6b3b2751f5a`
- Plan sha256 (v1.1.1): `772b52e1f4b4e9e0ed964c3068b1948c24d5cfe27afc109e8e589a1ea790c036`
- Panel sha256: `451f4c615c89a481da4ca132c79a55b04e00eecb9199746f544b22561ba0740d`
- Pair D spec sha256: `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`

per spec §9.7 sha256 governance — every downstream artifact MUST cite the pinned sha256.

---

**End of PRIMARY_RESULTS.md SKELETON.** Re-run `02_estimation.ipynb` to populate.
