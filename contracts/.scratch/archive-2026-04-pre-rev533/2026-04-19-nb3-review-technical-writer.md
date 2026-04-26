# NB3 Three-Way Review — Technical Writer Prong

**Reviewer:** Technical Writer (documentation + reproducibility)
**Review scope:** `03_tests_and_sensitivity.ipynb` (34 cells, 1888 JSON lines) + auto-rendered `README.md` + rendering infrastructure
**Read-only review.** No notebook edits, no commits.
**Date:** 2026-04-19

---

## 1. Verdict

**CONDITIONAL PASS.**

The narrative quality of NB3 is the strongest of the three-notebook chain. Citation blocks are complete and correctly structured, the anti-fishing halt in §9 is framed with the scientific discipline it deserves, and the gate aggregation in §10 emits a clean single source of truth. The README renders deterministically, matches the notebook's numeric outputs, and its footer provenance hashes (spec hash, panel fingerprint) are exactly the ones the notebook pre-flight check (§1) re-verifies.

Conditionality is driven by a single reader-experience gap that I judge material: the README, read in isolation, does not transmit the most discipline-laden fact the notebook teaches — that A1 and A4 sensitivities DID reject the null but were NOT promoted to the gate verdict because T3b FAILed upstream and post-hoc subset selection is ruled out by the pre-committed anti-fishing protocol. A skim-reader who reads only the README will miss the central scientific-discipline moment of the entire analysis. This is a documentation-visibility issue, not a correctness issue, and it is fixable by a single paragraph under "Forest Plot" in the README template. Details in §8 below.

Six secondary minor issues are listed in §11. None of them would block merging today; all should be addressed in the next narrative edit pass.

---

## 2. Narrative quality

**Story arc.** §1 through §10 reads as a single continuous argument. §1 establishes the replication-discipline envelope (spec hash, panel fingerprint, handoff JSON, version pins) and names its four pre-flight checks in plain language before any test runs — a reader who stops at §1 already knows what drifted-inputs-halt protection is and why it must fire before §2 does anything. §2-§7 then execute the seven specification tests (T1, T2, T4, T5, T6, T7, T3a) each in a self-contained citation-block + code-cell + interpretation triad. §8 binds the twelve sensitivities to a single forest-plot visual. §9 pivots from "what the tests say" to "what the gate rule says we can conclude" — and in §9 the scientific-discipline argument sharpens: the anti-fishing halt is not a bug, not a failure mode; it is the pre-committed guard that prevents the twelve sensitivities from becoming a post-hoc rehabilitation of a failed primary. §10 closes the loop by atomically emitting `gate_verdict.json` and re-rendering the README so the handoff artifact is self-consistent. A reader who follows the full §1→§10 arc walks away with a complete reproducibility story.

**Voice and reader empathy.** The notebook writes in present tense and active voice throughout. The second-person "you" is rare; instead the prose uses "we" for the analyst collective and "the reader" for the downstream consumer, which is appropriate for a technical-report register and reads cleanly. Complex concepts (HAC(4) wrapping, Bai-Perron endogenous break detection, Brown-Forsythe median-centering, QMLE inference for the GARCH-X wrapper) are introduced with a one-line accessibility bridge before their technical payload — for example, §3 says "we median-center (Brown-Forsythe) rather than mean-center because `rv_cuberoot` remains mildly skewed" before expanding on Conover-Johnson-Johnson 1981's Monte-Carlo evidence. A macro-finance PhD reader will find this register pitched correctly.

**§1 setup quality.** §1's four-check pre-flight is one of the cleanest reproducibility-infrastructure passages I have reviewed. It names each check (spec hash equality, panel fingerprint equality, handoff JSON self-consistency, version pin agreement), explains why each matters, explains the halting behaviour on failure (hard halt for a-c, soft degrade for d), and explains how the degraded flag propagates downstream to §4/§5/§6 with explicit cell-by-cell handling notes. The `pkl_degraded` path is defended as a design choice, not a hedge. This section alone would be excellent reading for any team building a reproducibility handoff envelope.

**§9 anti-fishing framing.** §9 is the single most important passage in the notebook and the prose rises to the occasion. The halt is framed positively: "a pre-committed guard that prevents twelve sensitivities from rehabilitating a failed primary." Simonsohn-Simmons-Nelson 2020, Ankel-Peters-Brodeur-Connolly 2024, and Leamer 1983/1985 are all cited in the single citation block for this section, establishing the historical continuity from Leamer's Extreme Bounds Analysis (1983) to modern specification-curve discipline (Simonsohn 2020) to the I4R robustness-reproduction contract (Ankel-Peters 2024). The cell 29 interpretation explicitly names the two rows that DID reject (A1 monthly, A4 release-excluded) and explicitly names why they are NOT promoted. This is scientific discipline communicated as a virtue rather than framed as regret. A reader learns that the FAIL verdict is the notebook's most credible output, not its least.

**§10 close.** The closing interpretation of §10 lands the full story in three sentences: `gate_verdict = FAIL`, driven by T3b binding; T7 tight PASS; T1/T2/T4/T5/T6 documented but non-binding per Rev 4 spec; `material_movers_count = 0` reflects the §9 halt. The honest closing paragraph ("under the pre-committed design, the CPI-surprise transmission to weekly FX realised volatility is not statistically detectable; the product thesis requires reframing... rather than rehabilitation through post-hoc sensitivity selection") is exactly the register a macro-finance reader needs.

**NB2 → NB3 narrative handoff.** NB3 references NB2 sections by explicit identifier throughout: "NB2 §3" (primary regression), "NB2 §4" (in-memory diagnostics that §4 re-runs against the PKL), "NB2 §8" (exogenous subsample split), "NB2 §9" (T3b gate), "NB2 §10" (A2/A3/A7 sensitivities carried forward). This is excellent cross-notebook navigation — a reader who wants the primary regression's full specification opens NB2 §3 with a known target; a reader who wants the in-memory T4/T5 diagnostics knows they are in NB2 §4 and the PKL round-trip is in NB3 §4. The prose explicitly acknowledges what IS and IS NOT re-computed in NB3 (for example, §4 re-runs Ljung-Box on the PKL-loaded residuals specifically to verify PKL integrity, NOT to re-compute the primary diagnostic; §8 annotates A2/A3/A7 as "see NB2" rather than re-authoring them). This anti-duplication discipline prevents the common failure mode of re-running tests in multiple notebooks with subtly different parameters. A reader never has to ask "which run of T4 is the canonical one" — NB2 §4 is the canonical T4, NB3 §4 is the PKL round-trip check, both produce the same numeric output, and both are explicitly labeled as such.

---

## 3. README render quality

**The five H2 sections.** The README ships with five H2 blocks: Primary Results, Reconciliation, Forest Plot, Per-Test Gate Table, Reports. This is the right set. They progress from concrete numbers (Primary Results) to cross-check agreement (Reconciliation) to visual sensitivity (Forest Plot) to structured test status (Per-Test Gate Table) to handoff artifacts (Reports). The ordering is logical — readers who want the headline stop after Primary Results, readers who want sensitivity walk the remaining three sections. Nothing needs reordering.

**Gate verdict headline.** Line 3 of the README is:

> **Gate Verdict: FAIL** — β̂_CPI = -0.000685 (HAC(4) SE = 0.001794, 90% CI = [-0.003635, 0.002265], n = 947).

This is exactly the right headline. Bold verdict, point estimate, SE, CI, and n in a single line. A reader scanning a dashboard of notebook outputs will see "FAIL" immediately. No improvement needed here.

**Primary Results table.** Four rows: Primary, GARCH-X, Decomposition β̂_CPI, Decomposition β̂_PPI. All use the identical format `β̂ | SE | 90% CI lo | 90% CI hi | n`. The GARCH-X row is exact zero (`0.000000 | 0.000000 | -0.000000 | 0.000000`) — this is correct per the live fit (δ̂ = 0 at a QMLE boundary) but a reader unfamiliar with GARCH-X boundary artifacts may find it startling. A one-sentence footnote under the table explaining that zero indicates a boundary-hit QMLE optimum would reduce reader confusion. See minor issue #1.

**Reconciliation table.** Two rows: "GARCH-X vs OLS primary sign/magnitude reconciliation: AGREE" and "Bootstrap vs HAC 90% CI agreement (NB2 §3.5): AGREEMENT". The explanatory paragraph underneath does a good job defining what AGREE means ("three top-level estimators... agree on sign and order of magnitude for the CPI-surprise loading") and what AGREEMENT means ("stationary-bootstrap 90% CI and the HAC(4) 90% CI overlap by at least 50%"). However, the two status words are close siblings — AGREE for reconciliation, AGREEMENT for bootstrap-HAC — and readers may wonder why the diction changes. The underlying domain distinction is real (one is sign/magnitude, the other is CI overlap), but the lexical near-duplication is a small readability snag. See minor issue #2.

**Forest plot embed.** The image loads (`figures/forest_plot.png`, 39 KB, confirmed rendered). The inline alt-text "NB3 §8 sensitivity forest plot — primary anchor + 12 sensitivities" does carry a caption and names the source section. The README paragraph beneath gives an accurate summary of the thirteen rows. The image title shown in the saved PNG is "NB3 sec 8 forest plot -- primary anchor + 12 sensitivities" (ASCII-safe, no section symbol) while the §8 live-render title uses "§8" — this is a deliberate ASCII safety choice for the saved PNG but creates a minor visual inconsistency between the PDF-rendered §8 and the README-embedded PNG. See minor issue #3.

**Per-Test Gate Table.** Eight rows (T1, T2, T3a, T3b, T4, T5, T6, T7) with a third "Role" column distinguishing "Auxiliary gate" from "Primary gate" from "Diagnostic". The auxiliary/primary/diagnostic distinction is IS the Rev 4 spec's pre-committed aggregation rule, and the explanatory paragraph beneath the table ("T3b FAIL ⇒ final FAIL regardless of other tests. T3b PASS plus all of (T1, T2, T7) PASS ⇒ final PASS. Diagnostic tests...") makes the rule concrete. This is clean. The one thing a reader may still ask is "what does 'FAIL TO REJECT' mean for a Diagnostic?" — T3a reads "FAIL TO REJECT" rather than "FAIL" or "PASS", because it is a two-sided null test not a one-sided gate. A footnote or a short in-row note clarifying the three-way verdict vocabulary (PASS / FAIL / FAIL TO REJECT) would help first-time readers. See minor issue #4.

**PDF links.** Line 52-54:

```
- [NB1 Data EDA PDF](pdf/01_data_eda.pdf)
- [NB2 Estimation PDF](pdf/02_estimation.pdf)
- [NB3 Tests and Sensitivity PDF](pdf/03_tests_and_sensitivity.pdf)
```

The `pdf/` directory exists but is empty in the current worktree. The README does say the PDFs "are produced by the `just notebooks` recipe," which is an honest "these are generated" caveat, but a reader who clicks the links today will get a 404. If these links ship before `just notebooks` has been run, readers will be confused. See critical issue #1.

**Spec-hash footer.** Line 60-62:

```
*Spec hash: `5d86d01c5d2ca58587f966c2b0a66c942500107436ecb91c11d8efc3e65aa2c6`*

*Panel fingerprint: `769ec955e72ddfcb6ff5b16e9c949fd8f53d9e8c349fc56ce96090fce81d791f`*
```

This footer is useful for reproducibility — a reader checking out the repo at a later date can run `python scripts/panel_fingerprint.py` and `sha256sum specs/.../econ-notebook-spec-rev4.md` (or the equivalent) and compare against the README to confirm the artifacts they are reading still correspond to the spec and panel that generated them. The two hashes are the exact values emitted in `nb2_params_point.json`, and §1 of NB3 re-verifies both at pre-flight, so there is a closed loop between the README footer, the JSON handoff, and the notebook pre-flight check. Good reproducibility hygiene. One small improvement: a leading sentence naming what readers can DO with these hashes ("re-verify you are reading the README that corresponds to a specific spec + panel version") would help a first-time reader who does not already know what a spec hash IS. See minor issue #5.

**Material movers sentence.** Line 46: "Material movers from NB3 §9 two-pronged rule: 0. PKL degraded (NB2→NB3 version drift): False." This sentence is a stranded one-liner between the Per-Test Gate Table and the aggregation-rule paragraph. It is not under a subheading, it does not have narrative context, and the reader who has not read §9 will not know what "two-pronged rule" refers to. This is the single weakest line in the rendered README. See minor issue #6.

---

## 4. Citation compliance (spot-check)

Every section header in NB3 (§1 through §10) carries a complete 4-part citation block — **Reference**, **Why used**, **Relevance to our results**, **Connection to simulator** — verified by structured grep across all markdown cells. Ten of ten passes.

**Spot-checks:**

- **§1 (Ankel-Peters-Brodeur-Connolly 2024 + Simonsohn-Simmons-Nelson 2020).** All 4 headers present. Bib keys `ankelPeters2024protocol` and `simonsohn2020specification` resolve against `references.bib`. Prose explains the handoff-envelope / anti-fishing pairing and ties both papers to the specific pre-flight checks that run in §1. Clear connection to simulator (the coefficient that flows to the Abrigo calibration only moves if the gate verdict is written, which the pre-flight guards). PASS.

- **§2 (Mincer-Zarnowitz 1969 + Balduzzi-Elton-Green 2001).** All 4 headers present. Bib keys `mincerZarnowitz1969evaluation` and `balduzzi2001economic` resolve. Prose explains why the AR(1) residual is a Balduzzi-Elton-Green analogue under Mincer-Zarnowitz rationality, and why the test regressors (lagged surprise, lagged RV, lagged VIX) are the right information set. Connection to simulator explains the "rational-expectations compatible" vs "predictive-regression interpretation" flag. PASS.

- **§5 (Chow 1960 + Bai-Perron 1998/2003 + ruptures).** All 4 headers present. Four bib keys referenced (`chow1960tests`, `baiPerron1998estimating`, `baiPerron2003computation`, and `ruptures` is named inline without a bib key — acceptable, it is a software library, not an academic reference). Prose chains Chow → Bai-Perron → computational refinement → ruptures implementation, with precise rationale for why residuals (not RV) are the detection target. Connection to simulator explains the UNALIGNED flag on the output CSV. PASS.

- **§9 (Simonsohn-Simmons-Nelson 2020 + Ankel-Peters-Brodeur-Connolly 2024 + Leamer 1983/1985).** All 4 headers present. Bib keys resolve; Leamer 1983 and 1985 are named inline with venue ("*AER* 73(1):31-43" and "*AER* 75(3):308-313") rather than bib-keyed — acceptable for a two-line historical-precedent reference but a full bib entry would be more consistent. Prose establishes the Leamer → Simonsohn → Ankel-Peters lineage cleanly. Connection to simulator explains the halt-on-FAIL calibration consequence. PASS with a minor bib-completeness note (see minor issue #7).

- **§10 (Ankel-Peters-Brodeur-Connolly 2024 + Leamer 1983).** All 4 headers present. Ankel-Peters resolves. Leamer 1983 again named inline. Prose connects the I4R output contract to the atomic-write pattern and the aggregation rule. Connection to simulator explains the `gate_verdict = FAIL → β̂ = 0` loading for the CPI channel. PASS.

**Bib resolution.** All 14 citation keys used anywhere in NB3 markdown resolve against `references.bib` (39 total entries). Zero unresolved citations.

**Chasing-offline compliance.** No forbidden phrases ("we tried", "rejected in favor of", "we chose", "this didn't work") appear in any NB3 markdown cell.

---

## 5. Decision-marker audit

NB3 references Decisions #1 and #3 in markdown cells (cell 6 references #3, cell 8 references both). Both are existing locked Decisions:

- Decision #1: weekly-panel cadence lock (NB1)
- Decision #3: RV^(1/3) transformation + AR(1) CPI-surprise construction (NB1)

NB3 emits **zero new Decisions**, which is correct per the notebook's scope (all 12 methodology decisions are locked in NB1 and NB2). The notebook references existing locked decisions only for downstream interpretation (e.g. §2's "Decision #3 construction is an AR(1) fit to DANE CPI YoY"). PASS.

---

## 6. Reproducibility artifact review

**`estimates/gate_verdict.json`** (13 keys). Correctly named, correctly located under `estimates/`, self-contained (no references to external files or in-memory objects). All 13 keys are named with a consistent `t{N}_verdict` or `{noun}_verdict` convention. The file is atomic-write emitted (§10 code stages to `.tmp`, fsyncs, renames) so a concurrent reader never sees a half-written JSON. A minor naming note: the six test verdicts use three distinct verdict vocabularies — PASS / FAIL / "FAIL TO REJECT" — which is correct (T3a is a two-sided null failing to reject ≠ PASS), but a reader of the raw JSON without the notebook at hand may need to know that "FAIL TO REJECT" is a specific econometric verdict word and not an error. Not a blocker; a schema file clarifying the verdict vocabulary would be a nice future addition.

**`estimates/nb2_params_point.json`** (13 top-level keys, with accompanying `nb2_params_point.schema.json`). Schema file is well-structured: uses JSON Schema draft 2020-12, specifies `additionalProperties: false` (strict), and defines a reusable `$defs/named_covariance` type to encode (row-index name, matrix) pairs so parameter ordering is explicit in every covariance block. The title ("NB2 Layer 1 → Layer 2 handoff contract") and description ("Authoritative JSON Schema for the structural-econometrics NB2 parameter handoff. Every covariance block is a {param_names, matrix} pair so row/column ordering is explicit and cannot silently drift on library upgrades. Locked against Rev 4 §4.4.") tell a reader exactly what the file is, why the shape is the way it is, and what it is locked against. This is excellent handoff-schema documentation.

**`figures/forest_plot.png`** (39 KB, PNG rendered at 110 DPI, bbox_inches='tight'). The figure loads cleanly when embedded in the README. Thirteen rows, clear black dots for point estimates, gray whiskers for 90% HAC CIs, red dotted vertical line at β̂ = 0, horizontal black line below the primary anchor to visually separate the anchor from the twelve sensitivities. The y-axis labels include sample size `n=...` in each label — a small detail that dramatically improves reader interpretability (a reader sees at a glance that A9⁺ carries n=13, and can immediately understand why the whiskers on that row are ±0.03 wide). The axis labels are ASCII ("beta_CPI (90% HAC CI whiskers)") rather than Unicode (`β̂_CPI`) — a deliberate robustness choice for the saved PNG but, as noted above, a visual inconsistency between the PDF-rendered §8 and the embedded README PNG. A font-size pass could help (the y-tick labels at 110 DPI start to crowd at the bottom of the plot), but this is polish, not a blocker. The figure does NOT carry a statistical-test "legend" or caption directly on the image; it relies on the README markdown caption for context. Acceptable for a README embed but may read as under-captioned in a standalone publication setting.

**Spec hash in README footer.** The footer emits `spec_hash: 5d86d01c5d2ca58587f966c2b0a66c942500107436ecb91c11d8efc3e65aa2c6` which is the hash of the Rev 4 econ-notebook design spec. Because `render_readme.py` reads this value directly from `nb2_params_point.json`, and NB3 §1 re-verifies that JSON against the filesystem, the README footer is guaranteed to correspond to the spec version the pipeline was run under. A reader who wants to verify can re-compute the hash against the spec file and compare. This is exactly the correct reproducibility semantics. The only caveat (which is not in the README): the footer hash says NOTHING about the *code* versions — the library pins live in `handoff_metadata.package_pins` inside `nb2_params_point.json`, not in the README. A reader who wants full reproducibility must open the JSON. This is a documentation-depth trade-off (footer brevity vs. full pin visibility) and I think the current design is correct, but a one-line "See nb2_params_point.json → handoff_metadata for package pins" would close the loop.

**`render_readme.py` design review.** The module is a textbook pure-function rendering pipeline. Three design choices stand out as exemplary and worth flagging as patterns the project could reuse in other rendering layers:

  - `jinja2.StrictUndefined` as the undefined-policy. A missing JSON key surfaces as a loud `UndefinedError` at render time, not as a silent empty string in the rendered markdown. For a pipeline where the README is the PRIMARY human-readable summary, silent drift between JSON and README would be the worst failure mode available — this configuration eliminates it by construction.

  - `_FLOAT_FMT = "{:.6f}"` routed through a single `_fmt_float` helper. Every numeric value displayed in the README passes through this one function. A reader can grep for `_fmt_float` and know exactly where every displayed number in the README was formatted. This prevents locale-dependent formatting (e.g. a non-US decimal separator from `str(x)`) and prevents Python-version drift (e.g. Python 3.13's repr heuristics changing between point releases — the module docstring explicitly calls this out).

  - Zero numpy / scipy imports. The module explicitly hard-codes the 90%-CI z-critical value at full 64-bit precision (`1.6448536269514722`) rather than calling `scipy.stats.norm.ppf(0.95)` at render time. The trade-off is deliberate: a rendering module that runs in a minimal packaging layer (pre-commit hook, standalone docker image, CI lint stage) should not pull in the heavy econometrics stack. The hard-coded constant is documented to match scipy's value exactly, so any reader who wants to verify can cross-check once and the constant is then self-documenting.

These three choices collectively make the README deterministic by construction: identical inputs + identical template always produce byte-identical output. This is the precondition Task 32 needs for the CI-diff staleness check to work, and the module docstring explicitly calls this out. Excellent pattern.

**Forest-plot emission path.** The forest PNG is generated in cell 33 (the README-render cell), not in cell 25 (the §8 primary forest plot). Cell 33 re-plots the same `_forest_table` DataFrame that cell 25 assembled — so the data-substrate is shared — but the two plot calls are independent matplotlib Figure objects with slightly different axis-label strings (cell 25 uses `"β̂_CPI (90% HAC CI whiskers)"` with Unicode, cell 33 uses `"beta_CPI (90% HAC CI whiskers)"` with ASCII safety for the saved PNG). This is a small risk surface: if cell 25's plot code is edited in the future without a mirrored edit in cell 33, the in-notebook §8 figure and the README-embedded PNG will silently diverge. Suggest factoring the forest-plot drawing into a shared helper (`_draw_forest_plot(ax, forest_table, title_str)`) that both cells call — this would eliminate the divergence risk by construction. Not a blocker; a refactor recommendation for a future edit pass.

---

## 7. PDF rendering readiness

**remove-input tags.** All 12 code cells in NB3 carry the `remove-input` tag (verified by scripted cell-metadata scan). When `jupyter nbconvert --to pdf` or `just notebooks` runs, every code cell will be hidden and only the markdown (citation blocks, interpretations) plus the `_ax.set_xlabel / set_title` figure outputs and `print(...)` stdout will render. A reader of the PDF will see the citation-block-then-interpretation narrative uninterrupted by import blocks and data-munging code. PASS.

**Figure readiness.** The §8 forest plot code sets a figsize `(9, 7)`, an explicit xlabel (`β̂_CPI (90% HAC CI whiskers)`), and an explicit title (`NB3 §8 forest plot — primary anchor + 12 sensitivities (engine: ...)`). The saved PNG strips these (ASCII) and applies its own title. The in-notebook figure (what the PDF-rendered §8 shows) is correctly titled, axis-labeled, and carries the red vertical line at zero for visual calibration. Acceptable.

**DataFrame formatting.** The `_forest_table.to_string(index=False)` and `_top3.to_string(index=False)` calls output pandas DataFrames as plain-text ASCII tables (no HTML), which renders cleanly in both PDF and Jupyter HTML contexts. The column widths are chosen by pandas defaults which are adequate for a 13-row × 5-column table. Acceptable.

**LaTeX inline math.** NB3 markdown uses raw Unicode `β̂` (67 occurrences) rather than the LaTeX-compatible `$\hat{\beta}$` convention per Task 23's E9-E10 hardening note. The Unicode rendering will work in MathJax-enabled browsers and most modern PDF pipelines (pandoc + xelatex picks up the `β̂` glyph correctly assuming a Unicode-compatible font like TeX Gyre Pagella or Linux Libertine is in the preamble), but fall back to a garbled `?` or box in older pdflatex-only toolchains. Because the PDF output target is xelatex / pandoc (implied by `just notebooks`), the current raw-Unicode approach is operational, but if the project ever migrates to pdflatex-only the glyphs will fail. This is a PDF-rendering-risk observation, not a blocker at current tooling. See minor issue #8.

**Stdout-output visibility.** The `remove-input` tag hides the code but not the stdout. For the §8 forest-plot cell, stdout includes the count of rows whose CI excludes zero and — if non-zero — a small DataFrame listing those row labels. In the PDF render, this stdout block becomes a visible piece of analyst-facing evidence. This is the ONLY place in the PDF where a reader sees A1 and A4 named alongside "rows with 90% CI EXCLUDING zero" as the structured evidence. §9 markdown then explains the anti-fishing halt. A PDF reader gets a clean evidence-then-discipline pairing. Acceptable.

**Cross-cell state dependencies in PDF render.** Multiple §8+ cells assume `_forest_table` is in kernel state from cell 25. In a fresh-kernel PDF render (which `just notebooks` performs), cells execute in sequence so this is not a problem. A reader running cells out-of-order manually in JupyterLab could hit an `NameError` at cell 33 — but such a reader is outside the PDF-render path and outside the CI pipeline, so this is not a reproducibility-review concern.

---

## 8. Honest-caveat visibility — the A1/A4 significant-but-not-rescue rows (CRITICAL)

The single most important discipline-moment in NB3 is this: **A1 (monthly cadence) and A4 (release-day-excluded) sensitivities carry 90% HAC CIs that DO exclude zero, yet the gate verdict is FAIL and neither row is promoted to a spotlight.** This is the pre-committed anti-fishing protocol in action: when the primary T3b gate FAILs, no sensitivity — no matter how econometrically rejecting — can rehabilitate the primary, because doing so would be post-hoc subset selection.

**Where the reader learns this.**

- **§8 interpretation (cell 26)** mentions A1 and A4 by name but does NOT flag that their CIs exclude zero. It says A1 uses a reduced control set because the monthly panel does not carry the us_cpi_surprise / banrep_rate_surprise regressors, and A4 is "release-day-excluded." A reader who stops at §8 sees the two rows and reads about reduced controls, but does not learn that these are the two rows that DID reject the null.

- **§8 code output** prints the count of "rows with 90% CI EXCLUDING zero" and — if the count is nonzero — prints the names of those rows. So a reader who reads the PDF render of §8 with code output VISIBLE (which defeats the `remove-input` setting, but stdout stays) sees "rows with 90% CI EXCLUDING zero : 2 of 13" and "A1 monthly cadence ... / A4 release-day-excluded ...". This is the raw evidence.

- **§9 interpretation (cell 29)** explicitly names A1 and A4 as the two rows that excluded zero, and explicitly says they are NOT promoted to a spotlight because of the anti-fishing halt. This is the critical paragraph. It frames the halt positively and cites Ankel-Peters 2024 and Simonsohn et al. 2020.

- **§10 interpretation (cell 32)** restates `material_movers_count = 0` and says this "reflects §9's anti-fishing halt on the T3b FAIL branch." Reader sees the halt consequence but not the A1/A4 specifics by name.

- **README** does NOT mention A1 or A4 anywhere. The Forest Plot section says "Thirteen specifications are plotted... the primary Column-6 anchor at the top..., then A1/A4/A5/A6/A8/A9+/A9- refits, three subsample regimes, the GARCH-X loading, and the PPI decomposition rows." A1 and A4 are named as forest-plot rows, but the README does NOT tell the reader that these are the two rows whose CIs excluded zero.

**The gap.** A reader who reads only the README learns:

  1. The gate verdict is FAIL.
  2. Thirteen specifications were plotted.
  3. Per-test verdicts (T1-T7).
  4. The aggregation rule: T3b FAIL ⇒ final FAIL.

The reader does NOT learn:

  5. Two of the thirteen sensitivities DID reject the null.
  6. The anti-fishing protocol is why those two are not promoted to the gate verdict.

This is the single most important scientific-discipline moment in the analysis. A reader who reads only the README gets a clean "FAIL" headline but does not learn WHY the FAIL is a credible, pre-committed result rather than a simple negative finding. The tension — "sensitivities exist that reject the null, yet the gate says FAIL" — is where the pre-registration protocol earns its keep, and the README is currently silent on it.

**Recommended remediation.** Add a one-paragraph "Anti-fishing discipline" subsection to the README template beneath the Forest Plot section. Suggested template insertion at line 31 (after the "Thirteen specifications are plotted..." paragraph):

> Two of the twelve sensitivity rows carry 90% HAC confidence intervals that exclude zero: the A1 monthly-cadence refit and the A4 release-day-excluded refit. Per the pre-committed anti-fishing protocol (Simonsohn, Simmons & Nelson 2020; Ankel-Peters, Brodeur & Connolly 2024), these rows are NOT promoted to the gate verdict — a rejecting sensitivity cannot rehabilitate a failed primary, because doing so would constitute post-hoc subset selection. The FAIL verdict is the honest reading of the pre-registered design.

This is a single paragraph under a single H3 subhead. It is the single highest-ROI README edit available. Without it the README reads as a clean FAIL; with it the README reads as a DISCIPLINED FAIL. That distinction is the difference between "the product doesn't work" and "we pre-committed to a test that prevents us from rehabilitating a failing product through cherry-picking." The latter is exactly what macro-finance PhDs reading this notebook need to see.

**This is the single conditional-pass blocker.** If this README edit ships, my verdict moves to unconditional PASS.

**Reader-journey simulation.** To make the impact concrete, imagine three reader personas approaching the artifact cold:

1. *Portfolio manager scanning GitHub.* Opens the README on the repo homepage. Sees "Gate Verdict: FAIL". Scrolls to the per-test table, sees seven FAILs and one PASS. Decides the CPI-surprise channel is not identified on the Colombia panel. Closes the tab. **Outcome:** correct conclusion on the headline; zero exposure to the pre-registration discipline that makes the result credible. Walks away thinking "analysis ran, analysis failed."

2. *Econometrics-sophisticated reviewer.* Reads the README, then clicks through to the notebook PDFs (if they exist). Reads the forest plot caption naming A1/A4/A5/A6/A8/A9+/A9-. Notes the A1 and A4 dots sit to the right of the zero line with CIs not touching zero (visible in the PNG). Wonders: "if A1 and A4 reject, why is the verdict FAIL?" Must open NB3 §8 or §9 to resolve. **Outcome:** correct conclusion, but takes 10-15 minutes of extra reading to reconstruct the scientific-discipline argument the README could deliver in three sentences.

3. *Macro-finance PhD evaluating the methodology for a similar project.* Reads the README end-to-end, concludes "these authors ran a pre-registered specification curve, did the work, and reported the primary as FAIL per the pre-committed rule." Wants to adopt the methodology in their own work. **Outcome:** correct conclusion, but the single README-level paragraph that would let this reader cite the anti-fishing protocol by name (and cite Simonsohn 2020 / Ankel-Peters 2024 alongside) is missing.

Adding the one-paragraph remediation promotes persona 1 from "correct headline, no depth" to "correct headline plus scientific-discipline flag"; promotes persona 2 from "must read the notebook" to "gets the full story from the README"; and gives persona 3 the citation shortcut they need.

**Why this is not a Model QA or Reality Checker finding.** This finding is uniquely in the documentation-quality review space because: (a) the notebook content is correct — §9 does frame the halt precisely, cites the right sources, and names A1 and A4 explicitly; (b) the gate verdict is correct — FAIL is the right answer given T3b FAIL; (c) the README is numerically consistent with the notebook — no figure or value is wrong. The issue is a *reader-journey* gap: information that exists in the source is not being propagated to the most-visible summary. Only a Technical Writer review catches this, because it requires simulating the reader's path through the artifact stack and noting where key information falls out of the summary layer.

---

## 9. README-notebook consistency check

**Primary coefficient values.**

- README line 3 / line 11: β̂ = -0.000685, SE = 0.001794, CI = [-0.003635, 0.002265], n = 947. Source: `nb2_params_point.json → ols_primary.beta.cpi_surprise_ar1 = -0.000685131999464896` formatted to 6 decimal places via `_fmt_float`. Matches.
- §7 interpretation: "T3a reports a t-statistic of ≈ -0.382 on the primary β̂_CPI = -0.000685 with HAC(4) SE = 0.001794". Matches README.
- §6 interpretation: "T7 reports β̂_CPI = -0.000685 (primary, with intervention dummy)". Matches README.

**Decomposition row values.** README line 13-14: β̂_CPI (+ IPP) = -0.000605, SE = 0.001838, 90% CI = [-0.003628, 0.002417], n = 947; β̂_PPI (ipp_std) = 0.000245, SE = 0.000682, 90% CI = [-0.000877, 0.001367], n = 947. Source: `nb2_params_point.json → decomposition.beta = {cpi_surprise_ar1: -0.0006051799..., ipp_std: 0.00024510518...}`. Matches.

**GARCH-X row.** README line 12: δ̂ = 0.000000, SE = 0.000000, CI = [-0.000000, 0.000000], n = 947. Source: `nb2_params_point.json → garch_x.theta.delta = 0.0`. Matches exactly (QMLE boundary-hit). This is a correctness match; whether the README should annotate the boundary hit is a style question — see minor issue #1.

**Per-test gate table.** README lines 36-45 match `gate_verdict.json` exactly: T1 FAIL, T2 FAIL, T3a FAIL TO REJECT, T3b FAIL, T4 FAIL, T5 FAIL, T6 FAIL, T7 PASS. All eight rows match. The "Role" column (Auxiliary gate / Primary gate / Diagnostic) is applied consistently with the Rev 4 spec's aggregation rule.

**Material movers + PKL degraded.** README line 46 reports `Material movers from NB3 §9 two-pronged rule: 0. PKL degraded: False.` Matches `gate_verdict.json → material_movers_count: 0, pkl_degraded: false`. Matches; the sentence is grammatically cramped (see minor issue #6) but factually correct.

**Forest plot image.** The PNG embedded in the README is generated at cell 33 of NB3 (the same cell that calls `render_readme`), so it is emitted from the SAME `_forest_table` DataFrame that §8 assembles. The image rows (thirteen, with primary on top and twelve sensitivities sorted by |β̂|) match the README description and match what §8 interprets. Matches.

**Spec hash and panel fingerprint.** README footer: `5d86d01c...` (spec) and `769ec955...` (panel). Both exactly match `nb2_params_point.json`. §1 of NB3 re-verifies both at pre-flight. Full closed loop. Matches.

**Summary.** README and notebook are byte-level consistent on every numeric and every verdict value. The `render_readme.py` module's `StrictUndefined` Jinja2 environment and `_FLOAT_FMT = "{:.6f}"` fixed-precision formatting make this guaranteed by construction — a missing JSON key would fail the render loudly, a locale-dependent float repr would drift. This is deterministic rendering done correctly.

---

## 10. Critical issues

1. **[C1] README PDF links are live but PDFs do not yet exist.** The README section "Reports" lists three `pdf/...` links, and the `pdf/` directory is currently empty in the committed worktree. Clicking any of the three links produces a 404. The README text does say "PDFs are produced by the `just notebooks` recipe" which is an honest caveat, but the links themselves are clickable and will be broken for any reader who attempts to navigate to a PDF before `just notebooks` has been run. Either (a) commit the PDFs, (b) commit a placeholder PDF per link, or (c) change the links to non-clickable text ("After `just notebooks`: `pdf/01_data_eda.pdf`, `pdf/02_estimation.pdf`, `pdf/03_tests_and_sensitivity.pdf`") until PDFs are committed. This is user-visible and blocks a clean ship.

2. **[C2] A1 and A4 rejecting rows are not surfaced in the README.** See §8 above. A reader who reads only the README does not learn that the anti-fishing protocol is what prevents A1/A4 from becoming a rescue. This is the scientific-discipline moment of the analysis; the README should communicate it. Suggested one-paragraph insertion provided in §8 above. This is the single README edit I would require before shipping.

---

## 11. Minor issues

1. **[M1] GARCH-X δ̂ = 0 boundary artifact not annotated.** The GARCH-X row in the Primary Results table reads `0.000000 | 0.000000 | -0.000000 | 0.000000`. A reader unfamiliar with QMLE boundary artifacts will find this strange. A single footnote under the table ("The GARCH-X row reports a zero loading because the QMLE hit a parameter boundary at δ=0; see NB2 §11 for the reconciliation analysis.") would resolve reader confusion.

2. **[M2] AGREE vs AGREEMENT.** The Reconciliation table uses the word "AGREE" for OLS-vs-GARCH-X sign/magnitude reconciliation and "AGREEMENT" for bootstrap-vs-HAC CI overlap. The two are domain-appropriate but lexically close; consider unifying to "AGREE / DISAGREE" for both flags.

3. **[M3] Forest plot title differs between live §8 and saved PNG.** The live §8 notebook display uses the title "NB3 §8 forest plot — primary anchor + 12 sensitivities (engine: {_engine})" with a Unicode section symbol and an em dash. The saved PNG (cell 33 code) uses "NB3 sec 8 forest plot -- primary anchor + 12 sensitivities" with ASCII safety. A reader who compares the PDF-rendered §8 figure against the README-embedded PNG will see the two titles differ. Unify on one title string, or accept the ASCII-safe PNG title everywhere.

4. **[M4] Verdict vocabulary footnote.** The Per-Test Gate Table uses three verdict words — PASS, FAIL, FAIL TO REJECT. T3a reads "FAIL TO REJECT" because it is a two-sided null test not a one-sided gate. A reader seeing "FAIL TO REJECT" next to "FAIL" will wonder whether FAIL TO REJECT is a third verdict category, an error, or something else. A brief one-sentence footnote under the table clarifying that PASS/FAIL are gate verdicts and FAIL TO REJECT is the two-sided null-hypothesis verdict on a diagnostic test would resolve this.

5. **[M5] Spec hash footer needs a lead-in.** The footer lines `*Spec hash: ...*` and `*Panel fingerprint: ...*` are useful for reproducibility-aware readers but mystify first-time readers. A leading sentence ("*To verify you are reading the README for a specific spec + panel version, compare these hashes against the design spec and the panel fingerprint:*") would onboard the feature.

6. **[M6] Material-movers one-liner reads awkwardly.** README line 46 ("Material movers from NB3 §9 two-pronged rule: 0. PKL degraded (NB2→NB3 version drift): False.") is a stranded sentence between the Per-Test Gate Table and the aggregation-rule paragraph. It has no subhead, no narrative context, and the phrase "two-pronged rule" is unexplained. Consider either (a) deleting this line entirely (the §9 halt is implicit in the FAIL verdict), or (b) promoting it to a short standalone subhead "Anti-fishing discipline" with the narrative paragraph suggested in §8 above.

7. **[M7] Leamer 1983/1985 not in bib.** §9 cites Leamer 1983 and Leamer 1985 inline with venue but without a bib-key `@leamer...` entry in `references.bib`. This is acceptable (the citation is complete in-prose) but inconsistent with every other reference in NB3, all of which use bib-keys. Either add the bib entries or change the style note to permit inline venue citations for historical precedents.

8. **[M8] Unicode `β̂` vs LaTeX `\hat{\beta}`.** NB3 uses raw Unicode `β̂` throughout (67 occurrences), rather than `$\hat{\beta}$`. This works in xelatex and modern PDF tooling but will fail in pdflatex-only pipelines. Not a blocker today; if the project ever migrates build tooling this will silently break.

9. **[M9] The README does not cross-link to the schema file.** The `estimates/nb2_params_point.schema.json` is an excellent piece of self-documenting infrastructure (JSON Schema draft 2020-12, strict `additionalProperties: false`, reusable `named_covariance` type definition) but the README's Reports section lists only the PDF links and the four JSON / PKL artifact names in prose. A direct link to the schema file would help a reader who wants to inspect the handoff contract before reading the JSON content. Suggested bullet under Reports: "- [NB2 handoff-contract schema](estimates/nb2_params_point.schema.json)".

10. **[M10] "FAIL TO REJECT" capitalisation inconsistency.** The README Per-Test Gate Table capitalises "FAIL TO REJECT" (three words, all caps) for T3a. The notebook §7 interpretation uses the same all-caps form. The notebook §10 interpretation uses lowercase ("two-sided test on the same coefficient also fails to reject"). Neither form is wrong; style-guide consistency would pin one form. Prefer the all-caps form in all gate-verdict / per-test-verdict contexts since it matches the other verdict vocabulary (PASS, FAIL).

---

## 12. Reviewer sign-off

**Verdict:** CONDITIONAL PASS.

**Single blocking condition:** add a one-paragraph "Anti-fishing discipline" or "Honest caveat" subsection to the README template that names A1 and A4 as the two rejecting sensitivities and explains that they are not promoted to the gate verdict because of the pre-committed anti-fishing protocol. This is the single highest-ROI README edit available and it converts the README from a clean-FAIL document into a disciplined-FAIL document.

**Also recommend (non-blocking):** decide how to present the empty `pdf/` directory — either commit placeholder PDFs, non-clickify the links, or make it clear in the README text that PDFs are post-`just-notebooks` artifacts. All other items in §11 are polish.

**What makes this review a pass at all.** The notebook narrative is excellent. The citation-block compliance is flawless (10 of 10 sections). The reproducibility artifacts (`gate_verdict.json`, `nb2_params_point.json`, `forest_plot.png`, README footer hashes) form a complete closed loop with NB3 §1 pre-flight verification. The anti-fishing discipline in §9 is framed as a scientific virtue, not a failure mode. The §10 close lands the FAIL verdict with honesty and specificity. The rendering infrastructure (`render_readme.py`) is deterministic by construction and the pipeline is wired for CI diff detection against drift.

A macro-finance PhD reading this notebook end-to-end would walk away understanding the analysis, the discipline, and the result. That reader opening only the README would understand the result but miss the discipline. Closing that gap is the one narrative edit between us and publishable reproducibility-track quality.

**Reviewer:** Technical Writer
**Scope:** Documentation + reproducibility (narrative, README render, citation hygiene, PDF readiness, artifact quality)
**Non-scope:** Econometric correctness (Model QA), adversarial correctness (Reality Checker)
**Read-only review complete. No notebook edits, no commits.**
