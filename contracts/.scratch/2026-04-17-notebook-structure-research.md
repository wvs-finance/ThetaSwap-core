# Econometric Notebook Structure Research

**Date:** 2026-04-17
**Purpose:** Ground the 3-notebook decision in real precedent before locking the design.

## Summary

The 3-notebook split is defensible but not a journal-mandated convention. Top journals (AEA, JAE, REStud via Social Science Data Editors) prescribe a `data/`+`code/`+`output/` repository structure with a single orchestration script; they take no position on notebook granularity. The dominant phase-numbered convention is Cookiecutter Data Science (0=exploration, 1=cleaning, 2=viz, extensible to 3=modeling, 4=diagnostics). The closest live exemplar in this exact problem space is Conrad, Schoelkopf, Tushteva 2025 ("Long-Term Volatility Shapes the Stock Market's Sensitivity to News"), plus Kevin Sheppard's `arch` example notebooks (nine topical files, one per task). "Data decision ledger" is not a named term; closest precedents are the Social Science Data Editors DAS, Gentzkow-Shapiro per-directory `readme.txt`, and the "cleaning rationale" pattern in Koenker-Zeileis 2009 JAE. Separating estimation from tests/sensitivities is appropriate given T1-T7 + A1-A9 is ~16 procedures.

## Key findings

1. **No journal mandates notebook splits.** AEA openICPSR and JAE/ZBW only require `data/` and `code/` separation plus a Social Science Data Editors README with data provenance, software versions, runtime, and expected outputs.

2. **Closest live exemplar for announcement-effect + GARCH**: Conrad, Schoelkopf, Tushteva (2025) — organized as `data/` + numbered scripts per table/figure, not a 3-way notebook split. Still, the per-table-per-script idea supports splitting analysis notebooks by purpose.

3. **Kevin Sheppard `arch` example notebooks**: nine topical notebooks (`univariate_volatility_modeling.ipynb`, `univariate_volatility_forecasting.ipynb`, `univariate_forecasting_with_exogenous_variables.ipynb`, etc.) — one notebook per conceptual task. This validates "estimation notebook" as a standalone deliverable.

4. **ABDV 2003**: no public replication archive located. Do not cite as structural precedent.

5. **Cookiecutter Data Science phase numbering**: the de facto phased convention. Phases 0=exploration, 1=cleaning, 2=viz, 3=modeling, 4=diagnostics. The user's 3-notebook plan collapses 0+1+2 into NB1 (defensible because the decision ledger explicitly documents cleaning).

6. **"Data decision ledger"** is not a named convention. Closest named precedents: Social Science Data Editors' "Data Availability Statement" (DAS); Koenker-Zeileis "On Reproducible Econometric Research" (JAE 2009); Gentzkow-Shapiro "Code and Data for the Social Sciences" which recommends a per-directory `readme.txt` recording every cleaning/merge decision. Reframe as "data provenance log" or "cleaning decisions log" for reviewer legibility.

## Verdict on the 3-notebook structure

Defensible and close to CCDS precedent. The separation of tests/sensitivities from estimation is the right call given T1-T7 + A1-A9 is ~16 procedures.

## Recommended per-notebook section ordering

- **NB1 (Data + EDA + Decision Ledger)**: sources/DAS → load raw → merge diagnostics → distributional EDA of CPI surprise + RV → outlier screens with rule justification → stationarity pre-checks (ADF/KPSS) foreshadowing T-tests → Decision Ledger table (choice/rationale/code anchor/alternative) → write `data/processed/panel.parquet`.
- **NB2 (Estimation)**: load processed panel → pre-committed primary (OLS RV^{1/3} on CPI surprise + 6 controls) first → GARCH(1,1)-X co-primary via `arch` → side-by-side coefficient tables → economic-magnitude interpretation under each result → serialize fitted models.
- **NB3 (Specification + Sensitivity)**: T1-T7 grouped by attack surface (distribution, dynamics, exogeneity) → A1-A9 grouped by robustness dimension (sample, transform, controls) → Reiss-Wolak unifying bound at the end → "what did/did not survive" narrative.

## Honest gaps

No canonical 3-vs-4 standard in top journals; no public ABDV 2003 code; no public Rincón-Torres (be_1171) code located. Strongest precedent anchor is CCDS phase numbering + Sheppard `arch` examples + Conrad et al. replication repo + Social Science Data Editors README.

## Sources

- [AEA Data Editor — Preparing for Data Deposit](https://aeadataeditor.github.io/aea-de-guidance/preparing-for-data-deposit)
- [JAE / ZBW Journal Data Archive](https://journaldata.zbw.eu/journals/jae)
- [Social Science Data Editors Template README](https://social-science-data-editors.github.io/template_README/)
- [Cookiecutter Data Science — Using the template](https://cookiecutter-data-science.drivendata.org/using-the-template/)
- [bashtage/arch — Examples folder](https://github.com/bashtage/arch/tree/main/examples)
- [Conrad, Schoelkopf, Tushteva 2025 replication](https://github.com/juliustheodor/long-term-volatility-news)
- [Koenker-Zeileis "On Reproducible Econometric Research" (JAE 2009)](http://www.econ.uiuc.edu/~roger/research/repro/JAE-RER.pdf)
- [Gentzkow-Shapiro "Code and Data for the Social Sciences"](https://web.stanford.edu/~gentzkow/research/CodeAndData.pdf)
