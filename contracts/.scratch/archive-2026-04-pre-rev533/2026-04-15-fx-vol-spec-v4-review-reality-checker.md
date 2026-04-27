# Reality Checker Review: fx-vol-cpi-surprise Rev 4

**Verdict: NEEDS WORK**

---

## Issue 1: Cube-root is labeled BOTH "exploratory" AND "pre-committed primary"

**BLOCK.** Line 20 says "Exploratory" then immediately says "Pre-committed primary LHS despite exploratory label." These are mutually exclusive designations. A pre-committed primary is the opposite of exploratory -- the entire anti-fishing apparatus depends on this distinction. The spec must pick one. If cube-root is the primary, delete the exploratory label and commit to it unconditionally. If it is genuinely exploratory (because the chi-squared premise fails at n=5 for fat-tailed returns, as the spec itself admits), then it cannot be the gate specification.

## Issue 2: Pre-commitment does not solve fishing with ~15 sensitivity specs reported

**FLAG.** The spec claims "ONE test determines the gate" and calls the other ~15 specs "sensitivity/exploratory." But the spec will report all of them. A reader (or pitch deck author) can cherry-pick any significant sensitivity result and frame it as "additional evidence." Pre-commitment only works if the reporting protocol binds: the primary result must be stated first and prominently, with an explicit caveat that at 5% significance across 15+ tests, at least one spurious result is expected. The spec gestures at this (end of Section 1) but does not formalize reporting order or require a multiple-testing adjustment on the sensitivity battery.

## Issue 3: "CONDITIONALLY UNBLOCKED" has no fallback for data failure

**BLOCK.** The condition is "download artifacts must be produced during Phase 5 Step A." Three sources are flagged UNVERIFIED. The spec says "If any fails, the spec must be amended" but does not specify: (a) minimum acceptable sample period if BanRep EME only goes back to 2015 instead of 2003 (halving N from ~1100 to ~500), (b) whether the AR(1) fallback is itself a different pre-committed primary or a new exploratory spec, (c) who decides the amendment and whether it requires a new review cycle. "Must be amended" without a decision tree is not a fallback -- it is a punt.

## Issue 4: OLS vs GARCH-X reconciliation is theater in practice

**FLAG.** The protocol says if they disagree, "investigate and report both, do NOT claim the gate passed." In practice, OLS-on-RV^{1/3} and GARCH-X model fundamentally different objects (weekly transformed RV vs daily conditional variance). Disagreement is the expected outcome, not the exception. The reconciliation protocol needs to specify what constitutes "agreement" quantitatively (same sign? same significance level? overlapping CIs?) rather than leaving it as a qualitative judgment call.

## Issue 5: 10% threshold circular dependency

**NIT.** The tau_tick = 10% placeholder depends on Layer 2 power analysis, which depends on beta from Layer 1. The spec correctly labels this a placeholder and defers it. The circularity is acknowledged but not resolved. Acceptable for now since Layer 2 is explicitly deferred, but this must not silently become load-bearing.

## Issue 6: Complexity has increased substantially

**FLAG.** A minimal "regress RV on CPI surprise" requires 1 specification, 1 test, 0 protocols. Rev 4 contains: 3 LHS transforms, 2 co-primary estimators (OLS + GARCH-X), 1 co-primary decomposition, 9 sensitivity alternatives, 1 AR(1) fallback, 7 specification tests (T1-T7), 1 reconciliation protocol, 1 gate protocol (T3a+T3b), 3 unverified data conditions, and 1 deferred Layer 2 closure condition. Total: ~28 distinct items requiring execution. This is not inherently wrong, but the spec has grown 4x in complexity across revisions without a corresponding increase in the underlying economic question's difficulty. Each addition was individually justified, but the aggregate creates execution risk: a solo researcher cannot credibly run all of this.

---

**Summary:** Two BLOCKs (contradictory primary/exploratory label; no data-failure fallback), three FLAGs (fishing still partially possible via reporting; reconciliation protocol underspecified; complexity creep), one NIT (circular threshold). The spec is intellectually honest in many places but has accumulated contradictions that must be resolved before Phase 5.
