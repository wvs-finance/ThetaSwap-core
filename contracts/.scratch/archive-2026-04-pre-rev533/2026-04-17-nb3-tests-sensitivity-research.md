# NB3 Design Research: Spec-Test Grouping, Forest Plots, Material-Mover Threshold

Date: 2026-04-17
Scope: Evidence-based precedents for three NB3 design choices — (1) ordering/grouping of T1–T7, (2) forest-plot convention across A1–A9, (3) material-mover threshold for "spotlight" detail tables.

---

## Question 1 — Grouping of spec tests (T1–T7)

### Evidence

- **Conrad, Schoelkopf, Tushteva (2025)** replication bundle (github.com/juliustheodor/long-term-volatility-news, file `code/3_Empirical Analysis.do`): the do-file is organized in **numbered sequential sections** by *paper artifact* (Figure 2, Table 2, Figure 3, Table 3, Table 4, Figure 4, Figure 5, Table 5). Table 5 is split into *Panels A–D* by **economic dimension** (A: low-freq macro; B: high-freq financial; C: uncertainty; D: stock-market vol). There are **no "distribution / dynamics / exogeneity / effect" attack-surface labels** in the do-file. Panel naming is substantive (what the regressor measures), not a spec-test taxonomy.
- **Ankel-Peters, Brodeur et al. (2024, I4R protocol)** — "A Protocol for Structured Robustness Reproductions and Replicability Assessments" (academic.oup.com/qopen/article/5/3/qoaf004): robustness checks are reported via (a) Dreber–Johannesson reproducibility indicators, (b) a sign/significance dashboard, and (c) specification curves. Groupings in I4R reports cluster by **analytic-choice family** (sample, estimator, controls) — closest to "attack surface" but named in domain terms, not statistical-property terms.
- **Simonsohn, Simmons, Nelson (2020)** "Specification Curve Analysis" (Nature Human Behaviour 4: 1208–1214): the "dashboard" below the curve groups specifications by *analytic choice dimension*, e.g. "sample filter", "control set", "functional form" — again, domain-substantive, not "distribution vs dynamics".

### Convention demonstrated

Published replication code groups tests/specs by **substantive analytic-choice dimension** (sample, estimator, controls, econ dimension), NOT by statistical attack-surface labels like "distribution / dynamics / exogeneity". Numbered sequential order tied to paper artifacts is the default.

### Verdict

**Deviate from strict T1–T7 numeric order; group by diagnostic target, BUT use substantive names, not attack-surface jargon.** Recommended grouping:
- **Residual diagnostics:** T4 (Ljung-Box), T5 (Jarque-Bera)
- **Stability & regime:** T6 (Chow/Bai-Perron), T7 (intervention-control adequacy)
- **Effect-sign & heterogeneity:** T3a (β-sign; T3b already in NB2)
- **Variance heterogeneity:** T2 (Levene release vs non-release)
- **Exogeneity of forecast construction:** T1 (consensus rationality F-test)

Numeric IDs stay in subsection titles for traceability to the spec.

---

## Question 2 — Forest plot across specifications

### Evidence

- **Conrad et al. (2025)**: do-file produces **no forest/coefficient plot for robustness**. Robustness visuals are *conditional marginal effect plots* (Figure 3, A.5 series) showing how a single coefficient varies with state variables. Tables (A.3, A.5, A.6, A.13) carry the spec-by-spec coefficient comparisons.
- **Simonsohn–Simmons–Nelson (2020)**: the canonical specification curve *is* a forest-style plot of β̂ ± CI across all defensible specifications. Default ordering is **by magnitude of the point estimate (ranked/sorted)**, not by spec index or by group. Quote from Simonsohn's companion materials (urisohn.com/specification-curve and Nature paper §2): specifications are "sorted by magnitude" with a "dashboard" below the curve annotating which analytic choices correspond to each bar.
- **specr (R)** — `plot_curve()` reference (masurp.github.io/specr/reference/plot_curve.html): default is ranked specification curve, `desc` argument toggles direction. Estimate is the sort key.
- **aeturrell/specification_curve (Python)** — same convention (aeturrell.github.io/specification_curve): ranked by coefficient magnitude by default.

### Convention demonstrated

A 12-row forest plot of β̂ ± 90% CI (primary + GARCH-X + decomposition + A1/A4/A5/A6/A8/A9; A2/A3/A7 cross-referenced to NB2) is **exactly the specification-curve convention**. Magnitude-ranking is the documented default in both specr and specification_curve.

### Verdict

**Matches convention.** Use `aeturrell/specification_curve` (pure Python, MIT-licensed, matches your stack — statsmodels-based) to render the robustness forest. Highlight the pre-committed primary row with a distinct color/marker; do NOT let magnitude-sorting bury it — put it at top as an anchor row, with remaining 11 sorted by β̂ magnitude below a horizontal divider. This preserves the Simonsohn convention *and* the pre-commitment semantics.

---

## Question 3 — "Material mover" threshold

### Evidence

- **Leamer extreme-bounds analysis** (Wikipedia summary; cran.r-project.org/web/packages/ExtremeBounds): a covariate is "robust" iff the extreme bounds across specifications preserve **sign** at the chosen confidence level (typically 95%). Threshold = sign change at 95% CI.
- **Ankel-Peters, Brodeur et al. (2024, I4R protocol, §3 Visual Dashboard)**: the dashboard classifies each robustness check against the original on **(a) sign agreement** and **(b) significance agreement at 5%**. These are the two binary criteria the I4R replicator network uses. No magnitude-percent threshold is codified.
- **Brodeur, Cook, Heyes (2020 AER)**: focuses on distribution of z-statistics across the literature; does not define a per-paper "material change" threshold.
- **DellaVigna & Linos (2022 Econometrica)**: no codified material-change threshold; compares effect-size distributions across samples.
- **No published "50% magnitude change" rule found.** This is a heuristic, not a precedent.

### Convention demonstrated

Two rules dominate published practice: **sign preservation** (Leamer) and **sign + significance-class preservation** (I4R 2024). Magnitude-percent and adj-R² thresholds are not canonical.

### Verdict

**Revise.** Replace the candidate list with the I4R two-pronged rule, adapted to your pre-committed 90% CI frame:

> A sensitivity is "material" iff ANY of: (i) β̂ falls outside the primary's 90% CI, OR (ii) β̂ changes sign, OR (iii) the null-rejection decision at 10% flips.

This collapses to a **single CI-containment check** because (ii) and (iii) are strictly implied by (i) when the primary's CI excludes zero (which it does under H1; if H1 fails at gate, NB3 halts anyway). So operationally: **material = β̂ outside primary's 90% CI**.

---

## Final recommendations

### 1. NB3 section ordering

1. Load `nb2_params_point.json` + residuals + robustness grid; assert gate prerequisites.
2. **Residual diagnostics** — T4 Ljung-Box, T5 Jarque-Bera.
3. **Stability & regime** — T6 Chow/Bai-Perron, T7 intervention-control adequacy.
4. **Effect sign & heterogeneity** — T3a (re-ref T3b from NB2).
5. **Variance heterogeneity** — T2 Levene release vs non-release.
6. **Exogeneity of forecast construction** — T1 consensus rationality F-test.
7. **Sensitivity forest plot** — 12 rows, primary anchored on top, remaining sorted by |β̂| descending.
8. **Material-mover spotlight tables** — regression tables only for specs where β̂ exits primary's 90% CI.
9. **Final gate verdict** — PASS/FAIL with per-test reasons; write JSON + exec-layer README summary.

### 2. Material-mover threshold

**β̂ outside the primary's 90% CI.** Single rule. Grounded in I4R 2024 dashboard logic collapsed under a pre-committed one-sided framing.

### 3. Forest-plot ordering rule

**Primary anchored at row 1** (highlighted marker, horizontal divider beneath). **Remaining 11 rows sorted by |β̂| descending** (Simonsohn 2020 convention). No grouping by A-number; the anchor-plus-magnitude layout preserves both pre-commitment and the published specification-curve convention.

---

## Sources

- [Conrad et al. 2025 replication bundle](https://github.com/juliustheodor/long-term-volatility-news)
- [Simonsohn, Simmons, Nelson (2020) Nature Human Behaviour](https://www.nature.com/articles/s41562-020-0912-z)
- [Simonsohn specification curve resources](https://urisohn.com/specification-curve/)
- [specr R package (Masur)](https://masurp.github.io/specr/)
- [specification_curve Python package (Turrell)](https://github.com/aeturrell/specification_curve)
- [Ankel-Peters, Brodeur et al. 2024 I4R Protocol (Q Open)](https://academic.oup.com/qopen/article/5/3/qoaf004/8090197)
- [Brodeur, Cook, Heyes 2020 AER](https://www.aeaweb.org/articles?id=10.1257/aer.20190687)
- [ExtremeBounds R package (Hlavac)](https://cran.r-project.org/web/packages/ExtremeBounds/)
- [DellaVigna & Linos 2022 Econometrica](https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA18709)
