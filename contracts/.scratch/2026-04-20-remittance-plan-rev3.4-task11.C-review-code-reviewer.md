# Task 11.C Code-Reviewer Review — Rev-3.4 Bridge-Validation Notebook

**Reviewer:** Code Reviewer
**Commit:** `91e5d2664` on `phase0-vb-mvp`
**Worktree:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/`
**Date:** 2026-04-23

## 1. Verdict

**SPEC COMPLIANT.** The pre-commitment is genuine, the N=6 correction is factually correct, the sign-concordance operationalization is defensible and textually anchored in the preamble before any ρ is computed, and the FAIL-BRIDGE verdict follows mechanically from the committed gate. Anti-fishing discipline holds.

## 2. Anti-fishing audit (critical section)

### 2.1 Cell-execution-order pre-commitment (item 1)

The 13-cell notebook has a flat, linear authorship order: cell 0 (preamble markdown) → cells 1–3 (§1) → cells 4–6 (§2) → cells 7–9 (§3) → cells 10–12 (§4). The **gate logic table** — PASS / INCONCLUSIVE / FAIL thresholds plus the explicit "sign-concordant ≡ ≥ 3 of 5 transitions" operationalization — is in cell 0, the preamble markdown, under an explicit header "Anti-fishing: Pre-registered Bridge Gate (Rev-3 plan line 316-319)". No code executes before cell 2 (§1 data-load), and ρ is computed only in cell 8 (§3). **The gate is committed before any ρ computation in strict textual order.** The preamble also carries the load-bearing disclaimer "The notebook-author MUST NOT adjust the thresholds after observing ρ".

**Verdict: pre-commitment is genuine.**

### 2.2 Sign-concordance operationalization (item 2)

The plan text is terse ("sign-concordant on Δ quarter-over-quarter"). The implementer operationalized this as "strict majority — at least ⌈(K+1)/2⌉ of K transitions agree; K=5 ⇒ ≥ 3 of 5", committed in the preamble gate table. This operationalization is:
- **Defensible**: "sign-concordant" in a small-sample setting is conventionally strict-majority; the ⌈(K+1)/2⌉ formula is invariant under off-by-one on N, which the preamble explicitly calls out as a feature ("stable under off-by-one on N"). Any weaker threshold (≥ 2 of 5, i.e. "at least two agree") would render the concordance gate toothless; any stricter threshold (≥ 4 of 5) would be an ad-hoc tightening.
- **Pre-committed before ρ**: the rule is in cell 0, fixed in text, before cells 8/11 evaluate it. The N=6-vs-N=7 escalation appears in the same preamble and does NOT modify the gate — it only documents the observed overlap count.
- **Not retrofitted to produce FAIL-BRIDGE**: with observed concordance = 2/5, the alternative threshold "≥ 2 of 5" would flip the verdict to PASS-BRIDGE. If the implementer were fishing for FAIL, they would have had every incentive to pick ≥ 2; choosing strict-majority is the anti-fishing-consistent choice regardless of direction.

**Verdict: operationalization defensible and pre-committed.**

### 2.3 N=7 vs N=6 (item 3)

Direct inspection of `contracts/data/banrep_remittance_aggregate_monthly.csv` (118 lines) shows quarter-end rows in 2024+2025 spanning 2024-03-31 → 2025-12-31 (8 quarters total). The overlap window begins at Task-11.A's first-obs 2024-09-17 (which falls in 2024-Q3, quarter-end 2024-09-30) and ends at BanRep's last observation 2025-12-31. Enumerating the six quarter-end rows from 2024-09-30 to 2025-12-31 gives exactly **N = 6 observations, K = 5 Q-over-Q transitions**. The plan's "N=7" is aspirational/wrong (plausibly confusing transitions with observations, or including a phantom 2024-Q2). The implementer's correction is factually correct and loudly documented in both preamble and scratch log. **No data silently dropped.**

**Verdict: N=6 is correct; plan N=7 was an off-by-one; implementer's documentation is complete.**

### 2.4 Verdict arithmetic (item 4)

Observed statistics: ρ = +0.7554, concordance = 2/5.

- `rho_above_pass` = True (0.7554 > 0.5)
- `rho_in_inconclusive_band` = False (0.7554 > 0.5)
- `rho_at_or_below_fail` = False (0.7554 > 0.3)
- `is_sign_concordant` = False (2 < 3)

Classifier: `if rho_at_or_below_fail or (not sign_concordant): return "FAIL-BRIDGE"`. The second disjunct `not sign_concordant` = True fires → FAIL-BRIDGE. This matches the preamble gate table: "FAIL-BRIDGE: ρ ≤ 0.3 OR sign-discordant (strict-minority concordance count)." The OR-clause semantics ("sign-discordant" ≡ `not sign_concordant` ≡ concordance < 3) are consistent between the preamble text and the classifier code. The PASS rule (ρ > 0.5 AND concordant) requires both conjuncts; ρ alone is insufficient, and the implementer correctly did NOT carve out a "ρ > 0.5 dominates" escape hatch.

**Verdict: arithmetic matches the gate; no post-hoc escape hatch.**

### 2.5 Bottom line

All four anti-fishing checks pass. The pre-commitment is textual, ordered, and load-bearing; the sign-concordance threshold is defensible and invariant under off-by-one; N=6 is correct; the verdict is mechanically derived. This is the discipline the CPI-surprise exercise established, carried forward intact.

## 3. Standard checkpoints

| # | Check | Status | Evidence |
|---|---|---|---|
| 5 | All 3 files created | PASS | `ls` confirms notebook (57 KB), scratch log (4.3 KB), test (10.4 KB) |
| 6 | 4-X-trio structure | PASS | 13 cells: §1/§2/§3/§4 each follow markdown-code-markdown pattern |
| 7 | nbconvert clean execution | PASS | pytest `test_notebook_executes_cleanly_via_nbconvert` PASSED |
| 8 | All 6 tests pass | PASS | 6 passed in 4.16s |
| 9 | Scratch log contents | PASS | Verdict + ρ + concordance 2/5 + N=6 + timestamp all present |
| 10 | NaN-ambiguity rule honored | PASS | §2 code drops `partial_week`, `fillna(0.0)` on the remainder; log confirms 1 partial dropped, 2 all-zero retained |
| 11 | No 11.A/11.B artifacts modified | PASS | `git diff --name-only` shows exactly 3 new files; no mutations |
| 12 | Commit message format | PASS | Matches required phrasing verbatim |

## 4. Findings

### BLOCK
None.

### FLAG
None.

### NIT

- **NIT-1 (cosmetic, non-blocking).** The `if verdict == "PASS-BRIDGE" ... elif verdict == "FAIL-BRIDGE" ... else: INCONCLUSIVE` narrative block in cell 11 is written in the FAIL branch assuming Task 11.D is a wording-only patch. If a future reviewer disagrees with the wording-only classification, that sentence will need to be re-read in context. Consider, in Task 11.D, adding a short note in the scratch log acknowledging the FAIL-BRIDGE narrative was implementer-drafted at implementation time, not yet reviewer-sanctioned.

- **NIT-2 (documentation).** The preamble claim "84 weekly rows (2024-09-20 → 2026-04-24)" is mirrored in the scratch log with the same count; this is not machine-verified by the test suite (the test only asserts presence of verdict-enum string + N=6 documentation). If Task-11.B's weekly count ever changes, this numeric claim could drift silently. Low priority since the exact count is not load-bearing for the verdict.

## 5. Files reviewed (absolute paths)

- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/fx_vol_remittance_surprise/Colombia/0B_bridge_validation.ipynb`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/tests/remittance/test_nb0B_bridge_validation.py`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-onchain-banrep-bridge-result.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/data/banrep_remittance_aggregate_monthly.csv` (read-only, for N-verification)

## 6. Recommendation

Task 11.C is **cleared to proceed to Task 11.D** (the Rev-1.1.1 spec-patch gate). The FAIL-BRIDGE verdict is legitimately earned, not fished. The narrative shift from "remittance" to "crypto-rail income-conversion" is a defensible post-FAIL relabel consistent with Rev-3.1 recovery protocol item 1.
