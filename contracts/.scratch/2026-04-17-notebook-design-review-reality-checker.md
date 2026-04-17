# Reality Checker Review — Econ Notebook Design (2026-04-17)

**Document:** `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md`
**Default verdict posture:** NEEDS WORK
**Reviewer:** TestingRealityChecker

---

## Per-Scope-Item Verdicts

### 1. Research-report fidelity — VERIFIED WITH MINOR OVERSTATEMENTS

Design §2 claims "Conrad et al. 2025 replication + Cookiecutter Data Science phase-numbered convention" — this matches nb-structure-research §Key-findings ##2, ##5. Design §6 "12 ledger decisions … scale to 12 for our 7 input series" — nb1-research Q1 recommends "roughly 10–14 documented decisions for a 6-regressor + LHS-RV panel"; 12 sits inside that range, VERIFIED. Design §7 NB2 section order (1–12) is a near-verbatim lift of nb2-research §Locked-recommendations item 1, VERIFIED. Design §8 NB3 grouping + material-mover rule matches nb3-research §Final-recommendations, VERIFIED.

Overstatement: design §6 attributes the standalone-per-variable plot convention to "Kevin Sheppard `arch` examples + Conrad 2025 replication precedent." nb1-research Q2 is the correct source; Conrad's evidence is figure-export loops, which is weaker than implied. Minor.

### 2. Reference-list spot-check — ONE FALSE CLAIM

**Han-Kristensen (2014, JE)** — FALSE. The paper is in **Journal of Business & Economic Statistics 32(3):416–429**, not Journal of Econometrics. Both the design §14 bullet and §7 NB2 "(Han-Kristensen 2014)" citation carry the wrong journal. Fix required before publishing BibTeX.

**Wilson, Hilferty (1931, PNAS)** — VERIFIED. *PNAS* 17:684–688, "The Distribution of Chi-Square."

**Conrad, Schoelkopf, Tushteva (2025)** — VERIFIED via replication repo (github.com/juliustheodor/long-term-volatility-news); nb-structure-research ##2 confirms. Forthcoming journal cited as "Journal of Econometrics" in nb1-research Q1 but design §14 omits venue. Acceptable.

**Ankel-Peters, Brodeur et al. (2024, Q Open)** — VERIFIED. nb3-research cites `academic.oup.com/qopen/article/5/3/qoaf004`.

**aeturrell/specification_curve** — VERIFIED MIT Python (primary language 99.1%). Statsmodels dependency was NOT confirmed by the GitHub landing page; nb3-research asserts "statsmodels-based" without direct citation. NEEDS EVIDENCE: either check `pyproject.toml` or soften design §2 "statsmodels-based" to "OLS-regression-based."

### 3. Material-mover collapse argument — VERIFIED WITH EDGE CASE

nb3-research §Question-3 explicitly derives the collapse: "(ii) and (iii) are strictly implied by (i) when the primary's CI excludes zero (which it does under H1; if H1 fails at gate, NB3 halts anyway)." Design §8 footnote reproduces this. VERIFIED.

**Edge case not disclosed in design:** collapse assumes the primary's 90% CI excludes zero AND is one-sided-positive. If a sensitivity spec's point estimate lies INSIDE primary's CI but on the opposite side of zero — possible only if primary CI straddles zero, which gate T3b forbids — rule (ii) could fire without (i). Pre-commitment forecloses this via T3b halt, so the collapse holds operationally, but the design should state the "T3b pass is prerequisite for collapse" condition explicitly. Minor edge-case disclosure gap.

### 4. Forest-plot provenance — VERIFIED (partial)

MIT + Python confirmed via GitHub. "statsmodels-based" unverified from landing page; see item 2.

### 5. Hansen-Lunde 2005 handoff claim — PARAPHRASE, NOT VERBATIM

Design §4.4 says "plug-in point estimates + full covariance matrix is the dominant convention … (Heston-Nandi, Duan, Hansen-Lunde 2005 JAE)." nb2-research §Question-2 Precedent-2c says Hansen-Lunde "point estimates of each of the 330 fits passed forward; no posterior, no covariance." That is the opposite of "full covariance matrix" — HL 2005 does NOT propagate Σ̂. The design overstates HL's role. The covariance-matrix claim is actually grounded in Heston-Nandi (edoberton repo keeps `hess_inv`) per Precedent-2a; HL 2005 supports only the point-estimate half. NEEDS REVISION: split the two claims or drop HL from the covariance-propagation citation.

### 6. Cell-count math (§10) — PLAUSIBLE

NB1: 12 decisions × 2 cells (markdown + code) = 24; 6 variable blocks × 2 = 12; setup/footer ≈ 2; total 38. Arithmetic checks. NB2: 12 sections × ~4.5 = 54. NB3: 7 tests × 3 + forest + spotlight + gate ≈ 50. Numbers are coherent estimates, not measurements. VERIFIED as estimates with "approximate" caveat already stated.

### 7. Citation-block practicality — ASPIRATIONAL

Design §5.1 mandates 4-part block (reference / why / relevance / Layer-2 connection) before every decision/test. Counting: 12 NB1 decisions + 12 NB2 sections + 9 NB3 sections = 33 blocks minimum, plus ~6 spec-choice cells = ~40. Each block is 4 numbered items; the "Layer 2 connection" item will frequently be "Does not feed Layer 2" for NB1/NB3 diagnostic work. NEEDS EVIDENCE: the design claims Analytics Reporter enforces this during authoring but provides no enforcement mechanism (no linter, no CI check, no review gate). Realistic but fragile. Recommend a pre-commit lint script or a review checklist.

### 8. Layer 2 mapping gap — VERIFIED

Design §1 ("Scope excludes … spec §4.5 Layer 1 → Layer 2 mapping gap remains deferred") and §13 ("No tick-concentration analysis … mapping gap stays deferred") are explicit and consistent. No accidental solution-claim detected. VERIFIED.

### 9. Branch rules — VIOLATION

`thetaSwap-core-dev/CLAUDE.md` Rule 1 (Branch-scoped plans) requires plans in `docs/plans/YYYY-MM-DD-<topic>.md`. Design sits at `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` — NOT `docs/plans/`. Additionally, this is the `phase0-vb-mvp` branch (not 001/002/003), so Rule 1's branch-feature mapping does not cover it; but the `docs/plans/` location is unambiguous. NEEDS EVIDENCE / FALSE location claim: confirm with user whether `contracts/docs/superpowers/specs/` is an approved alternate location for this worktree. If not, move to `docs/plans/`.

### 10. No-code rule (memory: specs must be 100% code-agnostic) — VIOLATION

Design contains code-like content:
- §4.4 JSON fragment with field names (`ols_primary`, `garch_x`, etc.) — borderline; arguably schema, not code
- §7 bullet: "`|s_t^CPI|` in variance equation" — LaTeX-math, allowed
- §9: "`cleaning.load_clean_weekly_panel(conn)` + `load_clean_daily_panel(conn)`" — **Python function signatures**, violates rule
- §3 folder-layout contains file names (`env.py`, `cleaning.py`) — file-structure, borderline
- §5.2: "`remove-input`" tag — configuration identifier, borderline

The JSON schema in §4.4 and function signatures in §9 are the clearest violations. The memory rule is strict ("100% code-agnostic"). NEEDS REVISION: rewrite §4.4 and §9 in prose ("the JSON handoff contract contains six top-level keys: primary OLS block, GARCH-X block, …").

---

## Top-Level Verdict: **APPROVED WITH CHANGES**

Required before implementation:
1. Fix Han-Kristensen journal (JE → JBES) in §7 and §14.
2. Split the Hansen-Lunde 2005 citation in §4.4 — HL supports point-estimate convention, NOT covariance propagation.
3. Resolve spec location vs. branch Rule 1 (`docs/plans/` vs. current path).
4. Remove Python function signatures and JSON code fragments per no-code-in-specs memory rule; rewrite as prose.
5. Soften "statsmodels-based" claim for specification_curve until pyproject.toml confirms.
6. Add explicit T3b-prerequisite note to the material-mover collapse argument.
7. Add enforcement mechanism (or downgrade to "expected practice") for the 40+ citation blocks.

Fidelity to research reports is strong; the design does not invent evidence. Violations are concentrated in (a) venue error, (b) rule-of-project adherence (location + no-code), and (c) one overstatement (HL 2005 covariance). Not fantasy-level failure, but material enough to block merge without these fixes.
