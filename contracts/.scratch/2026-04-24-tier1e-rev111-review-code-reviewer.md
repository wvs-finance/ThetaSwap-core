# Tier-1e Rev-1.1.1 spec review — Code Reviewer

**Date:** 2026-04-24
**Target:** `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` @ `ac5189363` (Rev-1.1.1)
**Companion:** `contracts/.scratch/2026-04-20-remittance-spec-rev1.1.1-fix-log.md`
**Plan tip:** `726ce8f74` (Rev-3.4), decision-gate rule line 343 (not 339; the prompt says 339, but the plan's Task 11.D Step 1 text sits at line 343 in the Rev-3.4 checkout — minor pointer drift).

## 1. Verdict

**REJECT — trigger `structural-econometrics` skill re-run before Rev-2.**

Patches 4 and 5 are mis-classified. A 1-D scalar primary X with a one-parameter two-sided t-gate and a 6-D vector primary X with a 6-df joint-F Wald gate are different statistical objects and different gate-function families. Plan line 343 names "kernel/method/parameter/number" — the joint-F is a **new test statistic** (not the same Wald-family kernel/method) and **6 new parameters** (β₁..β₆), not a cadence or data-source relabel. The Task 11.D Step 1 classifier's "cadence-or-source relabel under same method" escape hatch does not cover this. Patches 6 and 8 inherit mis-classification from patch 4/5 because they (a) re-derive MDES under the new test family, and (b) rewrite four §12 resolution-matrix rows on the back of the new primary. Patches 1, 2, 3, 7, 9, 10 are legitimate wording-only.

## 2. Per-patch classification audit

| # | Section | Fix-log label | Agree? | Rationale |
|---|---|---|---|---|
| 1 | Frontmatter `status` | Wording-only | AGREE | Pure label; no scientific content. |
| 2 | §0 supersedes banner | Wording-only | AGREE | Narrative prose citing Task 11.C; no new method. |
| 3 | §1 primary-X reinterpretation | Wording-only (source relabel) | AGREE-WITH-FLAG | Source relabel at research-question level is defensible *if* the X-object is held at scalar — which Patch 4 breaks. In isolation, §1 is a relabel. |
| 4 | §4.1 scalar → 6-channel vector | Wording-only | **DISAGREE (BLOCKER)** | 1-D population parameter β_Rem → 6-D vector (β₁..β₆) is a new primary statistical object, not a cadence relabel. New identification assumptions (6 channels linearly independent, no multicollinearity on N_eff=78), new interpretation of per-channel β̂ₖ as audit-only, new sample-boundary math (N 947 → N_eff ≈ 78-84). This is the canonical "change in primary X statistical object" the plan's decision-gate rule names explicitly. |
| 5 | §4.4 scalar t → joint F | Wording-only | **DISAGREE (BLOCKER)** | Joint-F is a different gate-function family: Wald-type F-test on a 6-df null is not the same as a scalar two-sided t-gate. The fix-log claim "α, kernel, verdict enum unchanged" is true for ancillaries but misses that the **test statistic itself changes**. Joint-F is inherently one-sided in F-space (fix-log silently drops the "two-sided T3b" label that row 1 of §12 still cites). Per-channel priors become diagnostic (§4.4 "sign-prior discussion retained as diagnostic") — this IS a methodology change, not a relabel. |
| 6 | §4.5 MDES recomputation | Wording-only | **DISAGREE (MAJOR)** | Label-as-wording is internally self-contradicting: fix-log admits the MDES is re-derived from the **joint-F non-centrality parameter** (a new formula, λ/(λ+N), vs Rev-1's 2.80/√N for scalar-t). That IS a new number AND a new formula AND at a new N. Plan line 331 only authorizes the **N_eff** numeric adjustment (200 → 78) as wording-only; it does NOT authorize simultaneously re-deriving the MDES formula from t to F. Two independent changes were bundled under one plan-line-331 waiver. |
| 7 | §6 S14 validation row | Wording-only | AGREE | Pre-registered sensitivity row; uses existing Task 10 AR(1) constructor + Rev-4 controls at quarterly cadence. No new method. |
| 8 | §12 rows 5/6/7/8 "supersedes" | Wording-only | **DISAGREE (MAJOR)** | Rows 5/6/7/8 are rewritten because the primary changed. Row 5 (Andrews bandwidth): "T substituted by realized N_eff" is true mechanically but the bandwidth now applies to a joint-F-Wald HAC covariance on 6 parameters, not a scalar HAC SE — non-trivial under Andrews 1991 (bandwidth is derived from residual AR(1) of a specific regression; the residual process is not the same after the primary change). Rows 6-8 are effectively demotions to sensitivity-row-only — that is a scope change, not a relabel. The matrix-integrity check (13 rows collectively pre-commit identification) has not been re-run. |
| 9 | §13 References + in-tree provenance | Wording-only | AGREE | Additions (NBER w26323 fn23, IMF OP 259, Task 11.A/B/C provenance) supplement; nothing substantive is retracted. |
| 10 | Frontmatter `revision_history` | Wording-only | AGREE | Metadata block. |

**Net:** patches 4, 5, 6, 8 require `structural-econometrics` skill re-invocation. Patches 1, 2, 3, 7, 9, 10 are safe.

## 3. Findings

**CR-E1 (BLOCKER, §4.1 + §4.4, fix-log table rows 4-5).** Patch 4 is a change in primary X statistical object; patch 5 is a change in gate-function family. Per plan line 343, both trigger `structural-econometrics` skill re-run. Fix: issue Rev-2, re-invoke skill on the joint-F design, have skill verify (a) the 6-channel basis is identification-justified on N_eff=78 without multicollinearity, (b) the Wald-F is the correct null-gate for the narrowed "crypto-rail income-conversion" mechanism, (c) per-channel priors are truly agnostic (§4.4 claims "two-sided by construction" — agreed, but each channel's sign-prior discussion was done in Rev-1 time for a different object).

**CR-E2 (BLOCKER, §4.5 MDES arithmetic).** Spec claims `λ ≈ 13` and "statsmodels `FTestPower` returns λ=12.97" at df₁=6, df₂=72, α=0.10, power=0.80. Independent verification via `scipy.stats.ncf` root-finding: **λ = 11.968** at df₂=72; λ = 12.06 at df₂=65. Spec's `λ ≈ 13` overstates by ~8%. Consequently MDES_R² ≈ 0.143 is wrong: recomputed values are 0.134 at N_eff=78 (df₂=65), 0.125 at N_eff=84 (df₂=71). The `statsmodels.stats.power.FTestPower` call signature cited in the spec also doesn't behave as claimed (its `effect_size` is Cohen's f, not λ; a direct λ-return requires manual construction). Fix: rerun the MDES derivation with correct noncentrality, update §4.5, update the `MDES_R² = 0.143` pre-commitment to `≈ 0.134` (or honestly accept the range 0.125-0.134 across the N_eff floor vs ceiling). Since this is a pre-committed numeric gate threshold, the error is load-bearing for FAIL vs INCONCLUSIVE verdict partitioning.

**CR-E3 (MAJOR, frontmatter vs fix-log, line 15 + fix-log table).** Frontmatter line 15 says "all nine in-place patches"; the enumerated list below has 9 items; the fix-log table has 13 rows (patches 8a/b/c/d split out + separate frontmatter `revision_history` row + no. 10); the prompt refers to "10 Rev-1.1.1 patches." Three different counts in three documents. Fix: reconcile to a single canonical count (recommend 10: enumerate §12 row edits as one patch #8 with four sub-items; keep frontmatter `revision_history` as patch #10; update frontmatter line 15 to "all ten").

**CR-E4 (MAJOR, §0 banner line 58).** Banner cites "plan line 343" for the decision gate; the prompt cites "line 339"; fix-log also cites "line 343." This is not an error per se (the plan text in `726ce8f74` sits at line 343), but inconsistency between the prompt's stated rule-location and the spec/fix-log suggests either a stale plan reference or a compaction artifact. Fix: confirm line number against `726ce8f74`.

**CR-E5 (MAJOR, §12 row 1 internal inconsistency).** Row 1 still reads "Two-sided T3b, α=0.10, critical |t|=1.645" as the pre-committed resolution for the economic-sign-prior matrix row. This is Rev-1 text. §4.4 now runs a joint-F (no scalar |t| at all for the primary gate). Rows 2 and 3 of §12 similarly carry Rev-1-era MDES and LHS-sensitivity framings keyed to a scalar β̂_Rem. The fix-log claims "§12 rows 1-4, 9-13 unchanged" — but rows 1 and 2 are now *stale*, not merely "unchanged in resolution text." Fix: either (a) update rows 1-2 of §12 to the joint-F framing, or (b) add explicit "superseded for primary by §4.4 joint-F; retained for S14 scalar validation only" qualifiers. Matrix-integrity is load-bearing per CR-E1's skill-re-run scope.

**CR-E6 (MINOR, §4.4 line 310).** Spec states "F_{0.10}(6, 72) ≈ 1.86; at df₂=65 it is ≈ 1.87." Verified: 1.858 at df₂=72, 1.867 at df₂=65. Correct. Nit: the ordering "1.86 … 1.87" at decreasing df is right, but reversed in the spec (larger df → smaller crit is the right direction). Text is fine as written.

**CR-E7 (MINOR, §13 references).** NBER w26323 is cited as "Dew-Becker, Giglio, and Kelly 2019" — correct (published NBER 2019, JFE 2021). IMF OP 259 Chami et al. 2008 — correct. In-tree commit hashes `bc12e3c30`, `2bff6d79f`, `91e5d2664` all resolve to the expected artifacts (verified via `git log --oneline`). Dune query `#7366593` is asserted but not verified against a live Dune resource in this review — I accept the reference provenance.

**CR-E8 (MINOR, §6 S14 vs §4.1 cross-ref).** §4.1 says "N_eff ≈ 78-84 on COPM+cCOP launch-window intersection with Rev-4 panel." §6 S14 says "N = 6-7 quarterly observations on the overlap window 2024-Q3 → 2025-Q4." The S14 spec is internally consistent (6-7 quarters × ~13 weeks ≈ 78-91 weeks — aligns with the primary N_eff). No numeric conflict.

**CR-E9 (MINOR, §9 decision-hash schema).** §9 still enumerates nine `remittance_col_spec_hashes` including "primary-RHS hash" (singular) and "AR(1) params hash." Under Rev-1.1.1, primary RHS is a 6-vector; the schema either needs (a) six per-channel hashes (changing the "nine column specifications" count), or (b) one composite vector-schema hash covering all 6 channels. Cross-reference integrity between §9 and §4.1 is broken. Fix: update §9's enumeration to match the 6-channel primary.

## 4. Internal-consistency check (per §)

| § | Pass/Fail | Note |
|---|---|---|
| Frontmatter | FAIL | "nine patches" count inconsistent with fix-log's 13-row table and prompt's "10 patches" (CR-E3). |
| §0 supersedes banner | PASS-WITH-FIX | Line-343 cite needs confirmation (CR-E4). |
| §1 research question | PASS | Primary-X relabel well-motivated; S14 demotion consistent. |
| §2-§3 economic/stochastic model | PASS | Unchanged from Rev-1. |
| §4.1 primary OLS | FAIL | Change-in-primary-object mis-classified (CR-E1). |
| §4.2 GARCH-X | PASS | Genuinely unchanged. |
| §4.3 reconciliation | PASS | Genuinely unchanged. |
| §4.4 T3b joint F | FAIL | Change-in-gate-family mis-classified (CR-E1). |
| §4.5 MDES | FAIL | Numerically wrong λ; formula change not covered by plan-line-331 waiver (CR-E2, CR-E1). |
| §4.6-§4.9 interpolation/AR/vintage/HAC | PASS-WITH-FIX | Text is Rev-1-era; §4.6 and §4.7 are now inapplicable to primary. Footnoting needed to match §12 rows 6/7. |
| §5 T1-T7 | PASS-WITH-FIX | T3a still cites "|β̂_Rem/SE|>1.645"; should reference joint-F for primary. |
| §6 sensitivity sweep + S14 | PASS | S14 definition is clean. |
| §7 event-study | PASS | Unchanged. |
| §8 Quandt-Andrews | PASS-WITH-FIX | Tests "single structural break in β_Rem" — scalar language stale under 6-channel primary. Needs joint-F or per-channel sup-Wald qualifier. |
| §9 decision-hash | FAIL | Schema enumerates single "primary-RHS hash"; 6-channel primary needs schema update (CR-E9). |
| §10 anti-fishing | PASS | Strengthened, not weakened, by narrowing. |
| §11 deliverables | PASS | |
| §12 resolution matrix | FAIL | Rows 1-2 stale under primary-change (CR-E5); rows 5-8 require skill re-run (CR-E1). |
| §13 references | PASS | Provenance resolves; hashes valid (CR-E7). |

**Summary:** 8 sections PASS, 5 PASS-WITH-FIX, 5 FAIL. The FAILs cluster in the primary-identification pathway (§4.1/§4.4/§4.5/§9/§12). Rev-2 is required; the `structural-econometrics` skill must vet patches 4, 5, 6, 8 before TW can re-consolidate. Plan Rule 13 cycle-counter should NOT advance on this rejection because the rejection is at the decision-gate classifier level (a methodology-error catch), which plan line 368 explicitly exempts from cycle-counting.
