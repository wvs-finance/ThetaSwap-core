---
spec_sha256_v1_0_2: "d90f6302f9473aa938521ed0b7a9b58dc1c849cd74476cd90424f59f3bd3f37e"
spec_decision_hash: "7c72292516f58f3cf2d16464d4f84c3e7d7270ad2c5d3d8ed8fef6b3b2751f5a"
spec_relpath: "contracts/docs/superpowers/specs/2026-05-04-dev-ai-stage-1-simple-beta-design.md"
plan_sha256_v1_1_1: "772b52e1f4b4e9e0ed964c3068b1948c24d5cfe27afc109e8e589a1ea790c036"
plan_relpath: "contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md"
panel_combined_sha256: "451f4c615c89a481da4ca132c79a55b04e00eecb9199746f544b22561ba0740d"
emit_timestamp_utc: "2026-05-06T09:22:53Z"
provisional_flag: true
sample_window:
  start: "2015-01"
  end: "2026-03"
n_realized: 134
n_min: 75
verdict: "PROVISIONAL_FAIL"
verdict_raw: "FAIL"
branch_taken: "step 4(d) FAIL"
---

# Dev-AI Stage-1 simple-β — PRIMARY_RESULTS

**Status: PROVISIONAL_FAIL** (PROVISIONAL pending NB03 R-consistency finalization per spec §6 v1.0.2 CORRECTIONS-κ + §7.1 R-row classification)

## §1 Verdict outcome

The primary OLS specification per spec §5.3 (`Y_p_logit ~ X_lag6 + X_lag9 + X_lag12 + intercept`) with HAC SE `L=12` per spec §3.4 yields verdict-tree §8.1 mapping branch **step 4(d) FAIL** → raw verdict **FAIL**.

The verdict is **PROVISIONAL** pending NB03 R-consistency finalization per spec §6 v1.0.2 CORRECTIONS-κ tightening: R1 (2021 regime dummy on logit-Y per §6) AND R3 (raw-OLS no logit per §7) MUST sign-AGREE with primary or §3.3 Clause-A FIRES regardless of §7.1 aggregate AGREE/MIXED classification. Additionally, SUBSTRATE_TOO_NOISY (§3.5) MAY fire if R1-R4 R-DISAGREE in NB03.

## §2 Primary numerics

| Quantity | Value |
|---|---|
| `β̂_composite` (= β_6 + β_9 + β_12, SUM per spec §3.5) | `-0.14613187` |
| `SE_composite_HAC` (linear restriction `c'Σ̂c`, c=(0,1,1,1)') | `0.08468266` |
| `t_composite` | `-1.725641` |
| `p_one_HAC` (large-N normal `1 - Φ(t)`) | `9.577940e-01` |
| Realized N | `134` |
| N_MIN gate (spec §3.6) | `75` |
| N gate pass | `True` |

## §3 Lag-pattern decomposition

| Lag | β̂ | HAC SE | Share of composite |
|---|---|---|---|
| `β_6`  | `-0.01604213` | `0.208007` | `+10.98%` |
| `β_9`  | `-0.00931995` | `0.195784` | `+6.38%` |
| `β_12` | `-0.12076979` | `0.161239` | `+82.64%` |

**Pair D contrast (memory `project_pair_d_phase2_pass`):** β_composite = +0.13670985 (HAC SE 0.02465; t = +5.5456; p_one = 1.46e-08); β_6 ≈ 80% of composite (RC FLAG #3 inheritance into Stage-2 dispatch brief). This iteration's `Δβ_composite = -0.28284172` (= -1.0689× Pair D). Lag-pattern divergence (if any) is reported in §11.X(b) of the Phase-3 result memo per spec §9.17(b).

## §4 Verdict-tree §8.1 trace

The verdict was derived by applying spec §8.1 mapping rules in order:

- Step 1: N gate PASS (N=134 >= N_MIN=75).
- Step 2: R-consistency = PENDING_NB03 (placeholder; NB03 finalizes per §7.1).
- Step 4(d): β̂_composite <= 0 AND p_one_HAC > 0.05 AND Clause B does NOT fire; routes to FAIL.

**Branch taken:** `step 4(d) FAIL` → raw verdict `FAIL`.

**Provisional status rationale:** R-consistency = `PENDING_NB03` (NB03 Task 2.4 R1+R2+R3+R4 sign-row classification per spec §7.1 finalizes; spec §6 v1.0.2 CORRECTIONS-κ tightens R1+R3 sign-AGREE to MANDATORY ESCALATE if either disagrees). The `PROVISIONAL_FAIL` label upgrades to `FAIL` (final) iff NB03 confirms R1+R3 sign-AGREE AND aggregate R-consistency ∈ {AGREE, MIXED}.

**Clause-B numerics (spec §3.3 / §8.1 steps 4(c)+4(d)):**

| Numeric | Value | Threshold | Fires? |
|---|---|---|---|
| `B-i: |β̂_composite|/SE_composite` | `1.7256` | `< 0.5` | `False` |
| `B-ii: |skew(resid)|` | `0.3393` | `> 1.0` | `False` |
| `B-ii: excess kurtosis(resid)` | `+0.3223` | `> 3.0` | `False` |
| **Clause B (B-i AND B-ii)** | — | — | **`False`** |

## §5 Compositional-accounting disclosure (spec §9.16)

Per spec §9.16 Section J ⊂ Pair D Section G–T strict-subset relationship:

- **(a) Compositional-accounting ambiguity acknowledged.** A positive `β_composite` on Y_p (Section J) is consistent with EITHER (i) the dev-AI-cost transmission mechanism firing independently at the ICT-narrow subsector level, OR (ii) Section J's compositional contribution to Pair D's broad-services PASS — i.e., re-discovery of the Pair D signal aggregated up to ICT.
- **(b) β-comparison to Pair D inherited.** Pair D PASS verdict precedent (verbatim from project memory `project_pair_d_phase2_pass`): `β_composite_pair_D = +0.13670985`; HAC SE = 0.02465; t = +5.5456; p_one = 1.46e-08; R-AGREE 0/4 sign-flips at PASS verdict 2026-04-28. Pair D spec sha256 `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`. This iteration's `β_composite_section_J = -0.14613187`; ratio `-1.0689× Pair D`; Δ `-0.28284172`.
- **(c) Flagged-not-resolved status.** The Stage-1 verdict CANNOT distinguish (i) from (ii) without a Section-J-vs-Section-(G–T-minus-J) decomposition. The R5 robustness arm "primary spec on (Sections G–T minus J)" is PRE-AUTHORIZED for v1.1 spec revision per spec §9.16 conditional gate (user explicitly invokes design change OR Stage-2 dispatch surfaces the need). Stage-2 M-sketch hedge geometry MUST address the decomposition explicitly per §9.16 promotion-gate (calibrate against ICT-services-direct sub-component Divisions 62-63 per §1 sub-aggregate-substitutability flag rather than Section J aggregate β_composite).

## §6 CORRECTIONS-κ §11.X disclosure preview (spec §9.17)

Per spec §9.17 binding the Phase-3 result memo to a NEW §11.X section "Realized-vs-anticipated data gap disclosure (CORRECTIONS-κ)" with 4 pre-pinned content blocks:

- **(a) Verbatim FLAG-A + FLAG-B citation.** Section J `cell_count` realized `[94, 267]` (median 145) vs Y feasibility memo §1.1 baseline `[700, 1200]` (5-7× below; 1 month at `cell_count = 94` at 2024-10-31, 55% of months below 150). Section J `raw_share` realized `[0.014, 0.031]` vs spec §5.1 v1.0.1 expected `[0.04, 0.10]` (1.3-3× below). Logit-derivative `d/dY[logit(Y)] = 1/[Y(1-Y)]` at the realized range maps to `[33, 73]` (3-7× larger amplification than the v1.0.1-anticipated 2.34× across-support ratio). Trio-3 NB01 disambiguation table values inheritable into §11.X(a) verbatim per spec §9.17(a) verbatim-citation requirement: linear within-range `2.78×–3.00×` / cross-corner `6.52×` / variance `7.73×–9.00×` / `42.5×` / combined `14400×` worst-corner / `350×` typical. The Phase-3 result memo §11.X(a) MUST verbatim-cite this disambiguation table.
- **(b) Primary-vs-R1-vs-R3 sign-AGREE-or-ESCALATE adjudication table (NB03-PENDING).**

| Row | β̂_composite | sign-AGREE relative to primary? |
|---|---|---|
| Primary (this NB02) | `-0.14613187` | (reference) |
| R1 (2021 regime dummy on logit-Y per §6) | NB03-PENDING | NB03-PENDING |
| R3 (raw-OLS no logit per §7) | NB03-PENDING | NB03-PENDING |

Per spec §6 v1.0.2 κ-tightened condition: if either R1 OR R3 is sign-DIFFERENT, the verdict re-routes from PASS to ESCALATE per §3.3 Clause-A regardless of §7.1 aggregate AGREE/MIXED classification.

- **(c) 94-cell rare-month R1-coverage acknowledgment.** The 94-cell rare-month observation (2024-10-31) is post-2021 era and therefore captured by R1's regime-dummy interaction term specifically — this is a positive design feature of R1 under realized κ-amplification (R1 catches the methodology-break × rare-event interaction in the post-2021 era), NOT a confound. The Phase-3 result memo §11.X(c) MUST state this explicitly to avoid the methodologically-incorrect reading "R1 didn't address the 94-cell observation."
- **(d) Sub-aggregate-substitutability ASR mapping.** If primary PASSes, the Phase-3 result memo §11.X(d) flags whether the result was driven by BPO-relevant CIIU Rev. 4 Divisions 62-63 (Computer programming + Information service activities; ICT-services-direct per §1 sub-aggregate-substitutability flag) vs non-BPO Divisions 58-61 (Publishing, Motion picture/video, Programming & broadcasting, Telecommunications). Sub-component decomposition is NOT in Stage-1 scope per §9.11; §11.X(d) defers the empirical answer to Stage-2 and binds Stage-2 M-sketch hedge geometry to Divisions 62-63 per §9.16 already-pinned discipline.

## §7 NB03 dispatch directive

NB03 Task 2.4 (R1+R2+R3+R4 robustness arms per spec §7) is REQUIRED next regardless of this Trio 3 raw verdict:

- On a provisional **PASS**: R1+R3 sign-AGREE check is MANDATORY per spec §6 v1.0.2 κ-tightening to clear §3.3 Clause-A.
- On a provisional **FAIL** / **ESCALATE-A** / **ESCALATE-B**: R-consistency is required for transparency + disposition memo authoring + §11.X disclosure population.
- On a provisional **HALT-N_MIN**: §9.5 HALT-disposition path; NB03 dispatch typically deferred until disposition memo lands.

NB03 finalizes:

1. R1 / R2 / R3 / R4 individual `β̂_composite` + sign-vs-primary classification per spec §7.1.
2. Aggregate R-consistency ∈ {AGREE, MIXED, DISAGREE} per spec §7.1 + §3.5 (>50% sign-flipped → SUBSTRATE_TOO_NOISY).
3. CORRECTIONS-κ §11.X(b) primary-vs-R1-vs-R3 3-row table populated with R1 + R3 numerics.
4. (If ESCALATE) §5.5 escalation suite (D-i quantile τ=0.90 + D-ii GARCH-X composite + D-iii EVT POT) + ESCALATE-PASS / ESCALATE-FAIL classification per spec §3.4.

After NB03 lands, Phase-3 result memo authoring dispatches per plan Task 3.1 with `PRIMARY_RESULTS.md` (this artifact) + `ROBUSTNESS_RESULTS.md` (NB03) + `ESCALATION_RESULTS.md` (if §5.5 fires) as canonical inputs per spec §9.7 sha256 governance + §9.17 promotion-gate.

---

**End of PRIMARY_RESULTS.md.** Pair D MEMO precedent: PRIMARY_RESULTS + ROBUSTNESS_RESULTS feed Phase-3 memo §10 (verdict statement) + §11.X (CORRECTIONS-κ disclosure) verbatim per spec §9.17(a)-(d) content-block requirements.
