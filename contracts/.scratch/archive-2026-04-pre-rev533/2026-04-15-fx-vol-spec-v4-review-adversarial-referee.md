# Adversarial Referee Report: FX-Vol-CPI-Surprise Spec Rev 4

**Verdict: MINOR REVISION**

---

## 1. Does the pre-committed primary solve the fishing problem?

Partially. The reconciliation protocol creates a de facto joint gate: primary must pass AND confirmatory must not contradict. This is not a single pre-committed test -- it is a two-test conjunction where either failure kills the gate. The fishing problem is replaced by a conservatism problem: the Type II error rate is inflated because two independent tests must agree. This is defensible (erring on the side of caution for a product gate), but the authors should acknowledge the effective size of the rejection region and compute the joint power. As written, the spec claims "ONE test determines the gate" while the reconciliation protocol contradicts this. Fix: either (a) commit that OLS alone determines the gate and GARCH-X is purely informational, or (b) honestly state this is a two-test conjunction and justify the power tradeoff.

## 2. Cube-root LHS as pre-committed primary

The spec candidly admits the chi-squared premise fails for fat-tailed n=5 returns, then pre-commits to it anyway. A referee would ask: why not pre-commit to raw RV (no distributional assumption, direct pool mapping) and demote cube-root to sensitivity? The stated rationale -- "best available variance-stabilizer" -- is empirically testable but not theoretically grounded for the data at hand. This is a soft weakness, not a block. Recommend: add a sentence justifying why variance stabilization matters more than interpretability for the gate decision, or swap raw RV to primary.

## 3. T3b: 90% one-sided CI

The 90% one-sided threshold (z=1.28) is standard for economic significance in finance but below pharma standards. For a product gate that determines whether a financial product launches, 90% is borderline. The choice is not justified in the spec. Recommend: add two sentences explaining why 90% (not 95%) is appropriate given the downstream use case, or raise to 95%.

## 4. Specification count

Counting: 1 pre-committed primary + 1 confirmatory (GARCH-X) + 9 sensitivity/alternatives (A1-A9) + 3 exploratory LHS transforms + 1 AR(1) fallback = ~15 total. This is within the 10-15 manageable range. The anti-fishing fix is substantive, not cosmetic. Satisfactory.

## 5. Reconciliation asymmetry

The asymmetry (gate can fail even if primary passes) is conservative and intentional. It is justified for a product gate: false positives are costlier than false negatives. However, the asymmetry should be explicitly quantified -- what is the probability that OLS and GARCH-X disagree under the null of a true effect? Without this, the reconciliation protocol's bite is unknown.

## 6. Overall assessment

A competent econometrician could execute this spec with minimal ambiguity. Data sources are identified (with honest flags on three unverified ones). Estimation methods are fully specified. The specification test battery is complete. Two open choices remain: (a) the exact Newey-West lag (4 is stated but not justified beyond convention), and (b) GARCH-X convergence fallback if BFGS fails. Both are minor. The Layer 1 to Layer 2 mapping gap is honestly flagged as an open issue deferred to post-estimation -- this is the right call.

**Required revisions (minor):**
1. Resolve the "one test" vs "two-test conjunction" contradiction in the reconciliation protocol.
2. Justify the 90% significance level for the product gate.
3. Either justify cube-root as primary over raw RV or swap them.
