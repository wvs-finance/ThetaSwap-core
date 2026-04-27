# NB1 EDA Conventions — Evidence-Based Research (2026-04-17)

Scope: Three specific notebook-design questions for the structural-econ NB1 (Colombian CPI-surprise → COP/USD RV^{1/3}). Evidence drawn from public replication archives and library-author exemplars.

---

## Question 1 — Cleaning decision granularity (typical count in published work)

**Concrete precedent found.**
Conrad, Schoelkopf, Tushteva (2025, forthcoming *Journal of Econometrics*), "Long-Term Volatility Shapes the Stock Market's Sensitivity to News" — public replication bundle at github.com/juliustheodor/long-term-volatility-news.

- File: `code/2_Import_Dataset.do` (33 KB Stata do-file, dedicated solely to import + cleaning).
- Hand-count of distinct cleaning decisions in that file: **23** — 11 per-variable sample-period trims, 4 lagged-fill-with-L2 rules for intermittent series (VIX, Credit Spread, Risk Index, T-Bill), 1 winsorization (`Eurodollar`, `winsor2 cut(0 99)`), 3 missing-code substitutions (`"--" → .`) for Bloomberg fields, and 4 merge-alignment drops (`drop if MedianSurvey == .`, etc.).
- Each decision is one to three lines of Stata; no decision is bundled with another.

**Convention demonstrated.** In a realized-volatility + macro-announcement paper with a similar variable count to ours (RV, VIX, credit spread, output gap, ~20 macro-surprise series, futures), per-variable decisions dominate and the total count scales with the number of input series, not with the number of "cleaning categories." Conrad et al. trip 23 because they have ~15 input series at distinct native frequencies.

**Verdict for the 6-decision plan: too few — should revise to one cleaning decision per input series, not per category.**
The current list ("sample period, outlier, LHS transform, NA handling, collinearity, stationarity trim") is abstract categories — cleaner than the Conrad-et-al file but it conceals per-variable judgements. Expand to roughly 10–14 documented decisions for a 6-regressor + LHS-RV panel: sample window (1), LHS transform (1), per-regressor NA/imputation (6), per-regressor outlier/winsor policy (up to 6 — many will be "none"), collinearity (1), stationarity (1). Explicit "none" for a variable is still a decision and should be logged.

---

## Question 2 — Subplot convention for multi-series EDA

**Concrete precedent found.**

- Conrad et al. (2025), `code/3_Empirical Analysis.do`: figure-generation loops over announcements and exports one standalone `.png` per variable (`graph export "$user/figures/Figure_3_<announcement>.png"`). No `graph combine`, no subplot grid. Each announcement (NFP, CPI, Retail Sales, ...) gets its own full-context figure.
- Kevin Sheppard's `arch` library, `examples/univariate_volatility_modeling.ipynb`: single-axis `returns.plot()` for the headline series; model diagnostics use `result.plot()` which emits the built-in 2-panel (residual, conditional vol) pair — not a user-constructed subplot grid across regressors.
- `examples/univariate_forecasting_with_exogenous_variables.ipynb`: exogenous regressors are not individually plotted at all; only the dependent series is shown, at full width (`figsize=(16,6)`).
- `examples/unitroot_examples.ipynb`: each series gets its own `.plot()` + its own `acf.plot(kind="bar")`; no combined grid.

**Convention demonstrated.** Published replication archives and library exemplars both prefer standalone per-variable plots with full context (time series + ACF/distribution where relevant) over dense 3×2 grids. The 3×2 subplot grid is common in paper figures (for space) but rare in EDA working code where each variable is being interrogated individually.

**Verdict: option (a) — standalone per-variable plot with ACF + distribution inset — is the dominant convention. Recommend this over (b).**
Keep the 3×2 grid as a single late-NB1 "overview" figure if useful, but the per-regressor deep-dive cells should be standalone.

---

## Question 3 — EDA foreshadowing vs strict agnosticism

**Concrete precedent found.**
Conrad et al. (2025) Table 1 is generated in `3_Empirical Analysis.do` using only:

```stata
foreach s of local events830 {
    tab E_`s' if E_`s' == 1 & eightthirty == 1 & ten==0
    disp `"`s'"' ":" r(N)
}
```

That is: Table 1 reports **event counts only** — not announcement-day vs non-announcement-day means/SDs of the LHS. The release-vs-non-release comparisons appear later, embedded in the regression specifications (interaction terms, sub-sample estimators), **not** in descriptive tables.

Similarly, Sheppard's `arch` EDA cells never pre-compute a test-relevant comparison before the formal test is run.

**Convention demonstrated.** Published applied-econ event-study work keeps Table 1 descriptively agnostic (sample, frequencies, means, SDs for the full sample) and places any release-vs-non-release contrast inside the formal-test section — not in EDA. This protects the reader from anchoring on a pre-test eyeball comparison.

**Verdict: option (a) strict agnosticism — match Conrad-et-al.**
Do not put a release-vs-non-release RV boxplot in NB1. If you want to show heterogeneity hints, show the unconditional RV distribution and its ACF; let NB3 own the release/non-release contrast entirely. Option (b) "foreshadow with caption" is defensible but no precedent was found for it in the replication archives inspected — it is a stylistic choice for tutorials, not for econ replication packages.

---

## Summary: recommended changes to the NB1 plan

- **Cleaning decisions:** expand from 6 category-level decisions to roughly 10–14 per-variable decisions, logging explicit "no action" where applicable; match the granularity of Conrad et al. 2025 `2_Import_Dataset.do`.
- **Subplot layout:** default to standalone per-variable plots (time series + ACF + distribution) for each regressor; a single 3×2 overview grid at the end of NB1 is optional but not required. Do not use the 3×2 grid as the primary EDA vehicle.
- **Foreshadowing:** keep NB1 strictly agnostic. No release-week vs non-release-week boxplot in NB1; that comparison belongs in NB3 with the formal Levene test.

---

## Sources

- Conrad, Schoelkopf, Tushteva (2025) replication bundle: https://github.com/juliustheodor/long-term-volatility-news — `code/2_Import_Dataset.do` (cleaning), `code/3_Empirical Analysis.do` (tables/figures).
- SSRN paper: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4632733
- bashtage/arch examples: https://github.com/bashtage/arch/tree/main/examples — `univariate_volatility_modeling.ipynb`, `univariate_forecasting_with_exogenous_variables.ipynb`, `unitroot_examples.ipynb`.
- Koenker & Zeileis (2009), JAE: https://www.zeileis.org/papers/Koenker+Zeileis-2009.pdf — confirms literate-replication norms (per-variable flat-text + Sweave), no multi-panel EDA grids.
- Altavilla, Giannone, Modugno (2017) JME: https://www.sciencedirect.com/science/article/abs/pii/S0304393217300892 — public replication code not located via this research pass ("no strong precedent found" from this source specifically).
- ABDV (2003) AER: https://www.aeaweb.org/articles?id=10.1257/000282803321455151 — public replication code not located via this pass ("no strong precedent found" for code, though paper structure aligns with Conrad et al. convention).
