# Reality Checker Review: FX-Vol CPI-Surprise Spec v3

**Verdict: NEEDS WORK** -- 2 BLOCKs, 2 FLAGs, 2 NITs.

---

## 1. "All 3 data sources verified free-tier" -- BLOCK

The status line claims Phase 5 UNBLOCKED with all 3 sources verified on 2026-04-15. But the table in section 4.3 still marks all three as "UNVERIFIED" with orange warnings. These contradict within the same document. More critically: "verified" means someone opened the URL, downloaded a file, and confirmed machine-readable rows with date coverage back to ~2003. The parenthetical "(banrep.gov.co historical tables)" reads like a search-result description, not a download confirmation. No sample row, no date range, no file format is cited. If someone actually downloaded BanRep EME consensus data, the spec should say: "Downloaded [filename] from [URL], format [CSV/XLS], date range [YYYY-MM to YYYY-MM], N=[X] monthly observations." Absent that, "verified" is self-certification without evidence.

## 2. Combinatorial explosion = fishing expedition -- BLOCK

The spec now contains: 2 co-primary estimation approaches (OLS on transformed RV + GARCH-X) x 3 co-primary LHS transforms (cube-root, log, raw) x 2 co-primary surprise constructions (survey + AR(1)) x 2 co-primary decompositions (CPI-only + CPI-vs-PPI) = 24 co-primary specifications. Plus 9 alternatives (A1-A9) and 2 robustness variants. "Co-primary" means you report all of them -- but with 24+ specifications, the probability of finding at least one significant beta at 5% is near certainty by chance. The spec has no pre-registration, no multiple-testing correction (Bonferroni, FDR), and no decision rule for what happens when specifications disagree. This is not rigor; it is a fishing expedition wearing a lab coat. Pick ONE primary specification with a pre-committed decision rule, demote the rest to sensitivity.

## 3. 10% tick-concentration threshold is arbitrary -- FLAG

Section 4.5 requires g(i_S)/g(i_T) to differ by "at least 10%" during surprise vs non-surprise weeks. Where does 10% come from? No model, no calibration, no reference. If the true economic threshold is 2%, the test is too conservative and kills a viable product. If it is 25%, the test is too lax and greenlights a worthless one. An arbitrary threshold on a deferred Layer 2 simulation creates fake falsifiability -- it looks rigorous but the number is made up.

## 4. Ambiguous bias + positive product gate = unguarded -- FLAG

Section 3.4 now correctly says net bias is AMBIGUOUS and that a significant beta-hat is not guaranteed to be a lower bound. But the product gate T3b still checks only sign (beta > 0). If stale consensus inflates the surprise (S1 channel), beta could be positive and large purely from measurement artifact. T3b does not guard against this. The spec says "depends on T1 passing" -- but T1 tests consensus PREDICTABILITY (lagged predictors), not consensus STALENESS. A consensus that is unpredictable but systematically stale (e.g., anchored to last month's print) passes T1 while still inflating beta. The upward-bias channel has no dedicated test.

## 5. BanRep EME historical depth -- NIT

The search result mentioned monthly survey results but did not confirm the archive starts in 2003. If it starts in 2010, you lose 84 monthly observations and 7 years of weekly sample. The spec assumes N~1100 weeks from ~2003. This should be verified before Phase 5, not discovered during data pipeline construction.

## 6. GARCH-X absolute value fix is good but creates asymmetry ambiguity -- NIT

Rev 3 correctly uses |s_t| in the variance equation. But the asymmetric extension uses s_t^+ and |s_t^-| separately. This means the GARCH-X symmetric and asymmetric versions test slightly different hypotheses (magnitude vs direction). Fine as sensitivity, but the spec does not flag which GARCH-X variant is co-primary.

---

**Summary of v2 fix status:**
- v2 BLOCK 1 (unverified data): Status line claims fixed, but table contradicts. NOT RESOLVED. Remains BLOCK.
- v2 BLOCK 2 (Layer 1-2 gap): Fixed -- gate language now says "necessary but not sufficient." RESOLVED.
- v2 FLAG 3 (beta comparability): Fixed -- PPI now standardized. RESOLVED.
- v2 FLAG 4 (oil functional form): Partially fixed -- A8 adds oil level. But A8 is alternative, not in the primary spec. DOWNGRADED to NIT.
- v2 FLAG 5 (ambiguous bias): Acknowledged in prose but product gate still unguarded. PERSISTS as FLAG.
- v2 NIT 6 (T3 two-sided vs one-sided): Fixed -- T3a is two-sided statistical, T3b is one-sided product gate. RESOLVED.
- v2 NIT 7 (GARCH-X importance): Fixed -- promoted to co-primary. RESOLVED but created new BLOCK (combinatorial explosion).

**Reality Checker**: TestingRealityChecker
**Date**: 2026-04-16
