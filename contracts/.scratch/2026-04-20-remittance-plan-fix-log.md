# Remittance Plan — Rev-2 Fix Log

**Plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
**Date:** 2026-04-20. Inputs: CR + RC + Senior PM reviews. Rev-1 severity: 6 BLOCKs + 14 FLAGs + 7 NITs (all PASS-WITH-FIXES).

## BLOCK (6)

| ID | Finding | Disposition | At |
|----|---------|-------------|----|
| CR B1 | T12 forward-refs T13 aux-column hashes | T12 scoped to primary-RHS hash; aux-hash moved into T13 | T12, T13 |
| CR B2 | T9 asserts aux + corridor columns from T13/T14 | T9 scoped to primary-RHS; `CleanedRemittancePanelV1/V2/V3` additive pattern; full validation deferred to T15 | T9, T13, T14, T15 |
| RC B1 | T11 "pinned Socrata endpoint" unverifiable (`mcec-87by` is TRM, not remittance) | Rewrote T11 as MPR-derived manual-compilation loader; Step-0 manual compile; `.SOURCE.md` provenance; re-pull = manual MPR re-parse | T11 |
| PM B1 | No Phase-3 intra-phase review gates | Inserted T18a (NB1), T21d (NB2), T24c (NB3); each = CR+RC+Senior Dev | T18a, T21d, T24c |
| PM B2 | T1 success criterion under-specified | T1 Step 4 requires 13-input resolution matrix (item \| resolution \| justification \| reviewer-checkable condition); T2-4 verdict row-by-row | T1, T2, T3, T4 |
| PM B3 | X-trio halts over-packed | T17→17a/b/c (4 decisions each); T21→21a/b/c; T22→22a/b; T24→24a/b; ≤4 trios/task | T17a-c, T21a-c, T22a-b, T24a-b |

## FLAG (14)

| ID | Finding | Disposition | At |
|----|---------|-------------|----|
| CR F1 | `nb3_forest.json` + `nb3_sensitivity_table.json` missing | Added to T23 Files + byte-determinism assertion | T23 |
| CR F2 | T7 Rev-4 `env.py` import ambiguous | T7 Step 3: absolute path + import statement + `sys.path` fallback | T7 |
| CR F3 | T22 tests assert only dict existence (silent-test-pass risk) | T22a/b require ≥1 numerical assertion per test (F-stat, Levene p, t-stat, Ljung-Box Q, JB, BP, spec-curve β̂) | T22a, T22b |
| CR F4 | T28 lacks per-reviewer focus | T28 Step 1 lists explicit CR/RC/Senior-Dev focus | T28 |
| CR F5 | T30 writes to MEMORY.md outside allow-list | Rule #4 Rev-2 exception for `~/.claude/projects/*/memory/` (scoped to T30a) citing Rev-4 precedent | Rules, T30a |
| RC F1 | Basco & Ojeda-Joya 1273 is cited-caveat, not recipe | T14 Step 0 pre-flight derives recipe; else documented-gap placeholder row | T14 |
| RC F2 | "A1 monthly" collides with CPI A1 | Renamed **A1-R** (remittance) vs A1-C (CPI); column `a1r_monthly_rebase`; forest labels + self-check updated | T13, T23 |
| RC F3 | T25 5-pattern coverage narrower than implied | T25 Step 1 enumerates 5 patterns + maps each to covering mechanism | T25 |
| PM F1 | T15 deadlocks if Rev-4 mod needed | Escalation branch: halt + escalate to user | T15 |
| PM F2 | T21/T24 bundle multiple subagents | T21→21a (DE helper) + 21b/c (AR); T24→24a/b (DE helper + AR, helper-first) | T21a-c, T24a-b |
| PM F3 | "Iterate to PASS" unbounded | Rule #13: 3-cycle cap then escalate; T27/T29 cite it | Rules, T27, T29 |
| PM F4 | T11/T12 artificially serialized | Parallelization note added to both headers | T11, T12 |
| PM F5 | nbconvert-execute deferred to T25 only | Phase-3 protocol: per-task inline `--inplace` + returncode=0 | Phase-3 preamble, Phase-3 tasks |
| PM F6 | T30 bundles 4+ workloads | T30→30a (memory, TW) + 30b (MEMORY.md + footer, TW) + 30c (final test + push) | T30a/b/c |

## NIT (addressed in same pass)

| ID | Disposition |
|----|-------------|
| CR N1 | Rule #11 exception for env/scaffold/fixture/integration-guard tests |
| CR N2 | T30c uses `chore(...)` not `close(...)` |
| CR N3 | T6 Step 1 mirrors Rev-4 `.gitignore` exactly |
| CR N4 | Alt-LHS + Dec-Jan distinct trios in T21c §10 |
| CR N5 | Resolved structurally via PM F2 splits |
| RC N1 | T1 Step 1 runs `git rev-parse` to pin design-doc hash |
| RC N2 | Self-check ordering intentional; RC accepted |
| PM N1 | Self-check compares "33/36 Rev-4 vs 41 Rev-2" |
| PM N2 | T7 Step 4 assumes Rev-4 conftest exists, fails loudly if not |
| PM N3 | T24b test asserts rendered README omits placeholder sentinel |
| PM N4 | T30c Step 2 = "verify clean git status + push branch to origin; no merge into main" |

## Structural deltas

- **Task count:** Rev-1 nominal 30 → Rev-2 **41** (Phases 0-4: 5, 5, 5, 18, 8).
- **Splits:** 17→17a/b/c; 21→21a/b/c; 22→22a/b; 24→24a/b; 30→30a/b/c.
- **Inserts:** 18a, 21d, 24c (intra-phase CR+RC+Senior-Dev review gates).
- **Phase-3 preamble** added: inline `--inplace` nbconvert-execute + review-gate index.
- **Rule #4** Rev-2 exception: `~/.claude/projects/*/memory/` completion-record writes (scoped to T30a).
- **Rule #11** exception: env/scaffold/fixture/integration-guard tests exempt from `test_nb*` naming.
- **Rule #13** new: 3-cycle reviewer-loop cap.
- **T1 Step 4** gating deliverable: 13-input resolution matrix.
- **T11** reworked: MPR-derived manual loader (no remittance API).
- **Revision history** block added under plan header.
- **Self-check** updated for split task refs + 41-task total.

## Preserved positives

Rev-4 inheritance; per-notebook integration-test split at T25; anti-fishing propagation; decision-hash extension invariant; 5-step TDD; spec-coverage self-check; Non-Negotiable Rules block; X-Trio protocol; T25 nbconvert guards; T26 determinism + mutation gauntlet; correct reviewer-trio assignments per memory rules; additive reuse of Rev-4 `scripts/`; all 7 Modify-file paths verified on disk; row-count 947 + Rev-4 decision-hash + 13-mandatory-inputs mapping all verified (RC).

## Word-count delta

Rev-1 plan: ~6,600 words. Rev-2 plan: 9,312 words. Delta: +2,712 words (inside +2,000 to +3,500 envelope).
