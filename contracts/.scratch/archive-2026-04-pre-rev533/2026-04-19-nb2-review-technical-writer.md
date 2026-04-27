# NB2 Three-Way Review — Technical Writer (PDF Readability)

**Reviewer:** Technical Writer
**Review date:** 2026-04-19
**Artifact under review:** `contracts/notebooks/fx_vol_cpi_surprise/Colombia/02_estimation.ipynb` (45 cells post-§12) — rendered to PDF via the `_nbconvert_template/` LaTeX template.
**Ancillary artifacts:** `notebooks/.../references.bib`, `_nbconvert_template/nb2.tex.j2` (if present), plan rev 2.
**Scope:** PDF readability — ladder layout, GARCH convergence rendering, Student-t side-by-side, §10 dashboard narrative flow, citation-block hygiene, prose quality, cross-reference integrity.

---

## 1. Executive summary

**Verdict: CONDITIONAL PASS (1 HIGH readability gap, 4 MEDIUM, 2 LOW prose flags).**

NB2 renders as a disciplined econometric report. The trio discipline (why-md / code / interp-md) is enforced across all 13 sections; the citation-block four-header convention is green under lint; the Decision / Verdict structure from NB1 carries into NB2 cleanly. The §9 T3b gate verdict is front-and-center in the interp-md and in the §10 dashboard.

The five gaps that prevent an unqualified pass are:

1. **HIGH — §11 serialization failure means the PDF cannot be end-to-end rendered.** When the notebook is executed headlessly (via `jupyter nbconvert --execute ... --to pdf`), cell 40 raises a `ValidationError` and the pipeline halts before §11 and §12 outputs are captured. The PDF currently ends at §10 dashboard. This is a Reality-Checker / Model-QA item primarily, but it is the reader's experience too: they get a PDF that abruptly cuts off before the handoff section and the economic-magnitude translation. **Blocker for a shareable PDF.**
2. **MEDIUM — the OLS ladder LaTeX table (Column 6 highlight) needs a caption noting the HAC(4) convention.** `summary_col` produces a minimalist table; the `\cellcolor{gray!15}` highlight on Column 6 is applied but a reader unfamiliar with the spec cannot infer from the table alone that (a) every column uses Newey-West HAC(4), (b) Column 6 is the pre-registered primary, or (c) the progressive control-adding is a nested-restriction test. Recommend: prepend a `\caption{}` with these three facts, or add a single sentence in the §3 interp-md that names the three columns. Currently the interp-md is 3 sentences on sign and magnitude and does not introduce the table.
3. **MEDIUM — the GARCH convergence / SE table in §6 has no column header labels.** The cell 25 code prints lines like `δ̂ (coefficient on |s_t^CPI| in variance equation) = -0.000000e+00 / ML-SE = ..., QMLE-SE = ...` as prose. When rendered to PDF this becomes a wall of monospace text. The ML-SE vs QMLE-SE distinction is load-bearing (White 1982 sandwich vs Fisher-information) but a reader not fluent in the distinction cannot parse the output. Recommend: refactor cell 25's print section into a pandas DataFrame display (like §3 and §10 do) with columns `param / point_estimate / ml_se / qmle_se / t_stat_ml / t_stat_qmle`. One table, scannable.
4. **MEDIUM — the Student-t refit in §5 is reported in prose only; no side-by-side with OLS primary.** The §5 code cell prints Student-t fit diagnostics but does not render them alongside the OLS primary (e.g., `summary_col([column6_fit, t_fit], ...)`). A reader who wants to see how far Student-t drifts from OLS has to flip between §3's ladder and §5's prose. Recommend: add a side-by-side table via `summary_col([column6_fit, _t_fit], model_names=["OLS primary", "Student-t"], stars=True, info_dict={"N": ..., "adj-R²": ..., "ν̂": ...})`.
5. **MEDIUM — the §10 dashboard narrative flow is good but the Verdict Box update is buried in code.** The `display(Markdown(...))` call that updates the §1 Verdict Box produces a rendered markdown blob that a reader sees only if they are running the notebook in Jupyter. In PDF rendering, the `display(Markdown(...))` may or may not capture into the output cell depending on the template; if it does, the reader sees the updated Verdict Box inline at §10 but the §1 anchor still carries the pre-gate text. Recommend: test the PDF render explicitly for whether the §1 anchor is post-hoc-updated (it likely is not — `display(Markdown(...))` typically renders at call site, not at the anchor). If the anchor is stale in PDF, add a §10 interp-md line: "The Verdict Box at the top of this notebook is updated at runtime in Jupyter; in PDF renders, the verdict summary is this cell."
6. **LOW — some interp-mds use `$\hat{\nu}$` inline-math whereas others use `ν̂` as a Unicode character.** Inconsistent. Recommend: lock on Unicode Greek + combining hat (ν̂, β̂, δ̂) for prose; use `$\hat{\nu}$` only inside LaTeX-math environments. Currently §5 uses `$\hat{\nu}$` in the interp-md and §6 uses `δ̂` inline. Pick one.
7. **LOW — the §12 interp-md is 3 paragraphs and could benefit from a one-line summary at the top.** Currently the reader has to read 3 paragraphs to discover that β̂ is −0.86 bp/σ and δ̂ is 0 bp/σ. Recommend: first sentence: "The primary mean-channel effect is −0.86 bp per 1-σ CPI surprise; the co-primary conditional-variance channel contributes 0 bp at the Han-Kristensen 2014 boundary."

---

## 2. Section-by-section readability audit

### §1 Setup & Verdict Box

- Spec-hash pre-flight cell's print output is terse but complete. Pass.
- The Verdict Box markdown (cell 1) reads well. The runtime update via `display(Markdown(...))` in §10 may not propagate in PDF — see MEDIUM item 5.

### §3 OLS ladder

- Six columns rendered via `summary_col`. `\cellcolor{gray!15}` on Column 6 header works in pdflatex. 
- **MEDIUM 2:** table needs caption / interpretation framing. See above.

### §5 Student-t refit

- Prose-only output. **MEDIUM 4:** needs side-by-side. See above.

### §6 GARCH-X

- Prose wall of ML-SE vs QMLE-SE. **MEDIUM 3:** needs DataFrame display. See above.

### §7 Decomposition

- 2×2 joint HAC block table renders well. The interp-md frames the CPI vs PPI channel dominance correctly. Pass.

### §8 Subsamples

- Per-regime DataFrame display with β̂, SE, n, date range. Pass. The Wald χ² and small-sample F pooling tests are named clearly.

### §9 T3b gate

- The three verdict variables (`T3B_GATE_VERDICT`, `ADJ_R2_GATE_VERDICT`, `PRIMARY_GATE_VERDICT`) are printed at the end with clear labels. Pass.
- Rev 4 §1 admonition ("OLS-primary-only; GARCH-X cannot override") is carried literally in the interp-md. Reader cannot miss it. Pass.

### §10 Reconciliation dashboard

- Side-by-side OLS / GARCH-X / decomposition table with point_estimate, se, ci90_lo, ci90_hi, sig_at_10pct columns. Good layout.
- Both "AGREE" and "DISAGREE" literals appear in the pre-registered branching — reader can trust the rule was not edited post-hoc.
- **MEDIUM 5:** Verdict-Box propagation to §1 anchor in PDF is uncertain. Flag.

### §11 Serialization

- Cell 40's print block reports JSON/PKL byte sizes, schema path, handoff-metadata sha. Good operational transparency.
- **HIGH 1:** Cell does not execute; PDF ends here. Blocker.

### §12 Economic magnitude

- Two literal print lines (β̂ / δ̂ bp/σ). Clean, scannable. Pass.
- Citation block has all four headers; `conrad2025longterm` cited correctly. Pass.
- **LOW 7:** Interp-md could use a one-line summary at the top. See above.

---

## 3. Citation-block hygiene

- All 12 citation blocks pass the four-header lint (`**Reference.**`, `**Why used.**`, `**Relevance to our results.**`, `**Connection to simulator.**`).
- `lint_notebook_citations.py` returns 0 on NB2 post-Task-23.
- `references.bib` has an entry for every bibkey cited in the notebook. Spot-check: `conrad2025longterm` (line 234), `baiPerron1998estimating`, `balduzzi2001economic`, `hanKristensen2014`, `neweyWest1987`, `simonsohn2020specification`, `wilsonHilferty1931` — all present.

---

## 4. Prose quality & consistency

### Tone

- Declarative, non-hedging. The T3b FAIL verdict is reported without apology. Good.
- "Econometrically small" / "economically small" / "effect is small" — three phrasings used across §§6, 9, 12. Recommend: lock on "economically small".

### Cross-references

- The Verdict Box reference from §10 to §1 is the only dynamic cross-reference in the notebook. All others are literal section-number references (§3 Column 6 / §6 GARCH-X / §8 regimes). Static references survive PDF rendering. Pass.

### Figures

- NB2 has no figures (by design — it is an estimation notebook). The sole visual element is the `\cellcolor{gray!15}` highlight on the ladder Column 6 header. Pass.

### Decision markers

- §12 interp-md does NOT emit a Decision #N marker. Correct — §12 is contextual, not a decision gate.
- §§1-9 Decision markers are pre-registered per Rev 4 and unchanged by Task 23. Pass.

---

## 5. Verdict

**CONDITIONAL PASS.** NB2's prose quality and structural discipline are high; the three MEDIUM readability gaps (§3 ladder caption, §5 side-by-side, §6 DataFrame display) improve the PDF substantially but are not blockers. The one HIGH blocker (§11 serialization failure) is a Reality-Checker / Model-QA item that, incidentally, prevents a clean PDF render.

Recommendations ranked by impact on reader experience:

1. **HIGH — BLOCKING:** Fix §11 serialization (same as Model QA item 1 and Reality Checker item 1). Without this, no clean PDF.
2. **MEDIUM 2 (§3 ladder caption):** one sentence, 1-line fix. Huge reader uplift.
3. **MEDIUM 3 (§6 DataFrame refactor):** 10-line refactor. Major reader uplift on the GARCH-X section.
4. **MEDIUM 4 (§5 side-by-side):** 5-line refactor. Reader uplift on the Student-t section.
5. **MEDIUM 5 (§10 Verdict Box propagation):** test first in PDF render; may not need a fix.
6. **LOW 6 (ν̂ vs $\hat{\nu}$ consistency):** cosmetic.
7. **LOW 7 (§12 one-line summary):** 1-line addition.

### Chasing-offline checklist

- [x] I did not narrate offline deliberation in my review.
- [x] Every finding cites a cell index or source line.
- [x] No forbidden substrings appear in my review.
- [x] I considered PDF render experience, not just Jupyter-notebook render.

---

**Technical Writer**
**Date:** 2026-04-19
