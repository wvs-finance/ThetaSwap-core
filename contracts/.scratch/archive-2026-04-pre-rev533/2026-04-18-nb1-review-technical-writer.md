# NB1 Three-Way Review — Technical Writer Prong

**Scope:** `contracts/notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb`
(118 cells, 39 code / 79 markdown) + `references.bib` (35 entries) +
`scripts/lint_notebook_citations.py` + `estimates/nb1_panel_fingerprint.json`.
Read-only review. No code or notebook edits performed; no git commits.

**Reviewer role:** documentation quality, narrative flow, citation hygiene,
reproducibility artifacts, PDF rendering readiness, honest-caveat visibility.
Econometric correctness and adversarial correctness are out of scope (Model QA
and Reality Checker own those prongs).

---

## 1. Verdict

**CONDITIONAL PASS.** NB1 is a genuinely impressive piece of reproducible
macro-finance documentation — citation-block discipline is watertight, every
Decision card is structurally intact, honest caveats are visible and
cross-referenced, and the nbconvert tagging is complete. The pre-commit lint
(`lint_notebook_citations.py`) passes (exit 0). However, three blocking
structural issues must be fixed before the notebook is reader-ready for a
PDF export:

1. Sections 5, 6, 7, 8 have no `##` heading — they exist only at `###` depth
   and therefore appear as sub-sections of §4 in any TOC / PDF bookmarks.
2. §4c Trio 2 and Trio 3 (cells 70, 73) are physically placed **after** §4d
   (VIX) — the BanRep-rate narrative is split across the VIX section.
3. `nb1_panel_fingerprint.json` ships with no `schema_version` field — NB2's
   pre-flight parser has no way to detect silent schema drift.

Minor issues (cell 9's duplicate H2 header, heading depth mismatch in §4f,
two missing bib entries for Decision #6, 5 figures lacking `suptitle`) are
cleanup-grade and not gate-blocking.

None of the blockers invalidate the scientific content. All three are
mechanical structural fixes.

---

## 2. Narrative quality assessment

**The body prose is excellent.** Citation blocks read as genuine academic
justification rather than checkbox compliance — the four-header structure
(`Reference` / `Why used` / `Relevance to our results` / `Connection to
simulator`) is populated with concrete, per-decision content on every gated
cell, and the "Connection to simulator" field consistently ties back to
`Rev 4 spec §n` or the Layer 2 FHS calibration rather than generic
boilerplate. Decision cards are long but readable — each spells out
`Consequences`, the sensitivity alternative, the `Ledger status`, and
(where applicable) an `Honest footnote`. The reader is rarely asked to
infer a connection that is not stated explicitly.

**Section-level framing is weak at the opening and non-existent at the
close.** Cell 0 is a one-paragraph title + a stale "skeleton (Task 1c)"
status note; cell 1 is a placeholder `Gate Verdict` admonition; cell 2
plunges directly into `## 1. Setup and DAS`. Nowhere does the notebook
tell the reader up-front what §1-§8 will establish, what Decisions will
be locked, or what the structural-econometric argument flow is. A macro-
finance PhD student encountering this cold would not know, from cell 0,
that this is a 12-decision pre-registration. The "Status: skeleton" line
is now factually incorrect (the notebook is complete) and actively
misleads the reader in the first 30 seconds of contact. The closing
cell 117 is a competent §8b interpretation but it is not a §8-level
summary of all twelve decisions, and there is no "what NB1 established"
retrospection before NB2 hand-off.

**Transitions between §3 → §4 → §5 are smooth.** Decision #3 (cell 36)
explicitly closes §3 with "This closes §3. With Decisions #1 (window),
#2 (RV^(1/3) transform), and #3 (weekly frequency) all locked, the LHS
and sampling side of the primary specification is fully pre-registered;
§4 proceeds to the RHS per-variable inspection." This is exactly the
kind of hinge the opening cells fail to provide. §4 → §5 → §6 → §7 → §8
do not carry equivalent closing hinges, so the mid-notebook reading
experience is a sequence of similarly-structured audit trios with
limited gearing between them.

**The §4 sub-section ordering is disordered.** Cells 55, 58-66, 67-69,
70-75, 76-81, 82-90 are interleaved so that §4c Trio 1 (BanRep rate
surprise) appears before §4d (VIX), but §4c Trio 2 and Trio 3 (audit +
Decision #6) appear **after** §4d and **before** §4e Trio 2. The
BanRep narrative is split across the VIX section, which is disorienting
for a linear reader and will produce a non-linear TOC in the PDF.

---

## 3. Citation block compliance — spot check

Lint status: `python3 scripts/lint_notebook_citations.py NB1.ipynb` exits
0. 38 markdown cells contain all four required headers. Spot-checks:

| Cell | Pre-gated code | All 4 headers? | Prose specific (not boilerplate)? | Bib keys cited |
|---|---|---|---|---|
| 2 (pre-cell 3) | Manifest bootstrap | yes | yes — SSDE 2024 Q Open template, per-source audit trail | ankelPeters2024protocol |
| 37 (pre-cell 38) | CPI-surprise EDA | yes | yes — ABDV 2003, Balduzzi-Elton-Green 2001 | andersen2003micro, balduzzi2001economic |
| 40 (pre-cell 41) | CPI audit | yes | yes — Trio 1 result explicitly threaded forward | ankelPeters2024protocol |
| 61 (pre-cell 62) | VIX aggregation | yes | yes — explicit reference to econ_panels.py line numbers | ankelPeters2024protocol, andersen2001distribution |
| 91 (pre-cell 92) | §5 correlation | yes | yes — BKW thresholds named with page reference | belsley1980regression, andersen2003micro |
| 100 (pre-cell 101) | §6 ADF+KPSS | yes | yes — ERS 1996 + KPSS 1992 + replication protocol | elliott1996efficient, kwiatkowski1992kpss |
| 106 (pre-cell 107) | §7 missingness | yes | yes — Conrad 2025 + replication protocol | conrad2025longterm, ankelPeters2024protocol |
| 115 (pre-cell 116) | §8b handoff | yes | yes — ties handoff JSON to Simonsohn 2020 pre-commitment | ankelPeters2024protocol, simonsohn2020specification |

All eight spot-checks are compliant. The prose is not generic — each
block names the specific paper, the specific result, and the specific
downstream consumer in the pipeline. 11 distinct bib keys are threaded
through the citation prose; every referenced key resolves to an entry
in `references.bib`.

---

## 4. DAS compliance against SSDE 2024

Cell 9 is the formal Data Availability Statement. Compliance grid against
the Social Science Data Editors 2024 Replication Package Template:

| SSDE requirement | Present? | Cell evidence |
|---|---|---|
| Machine-readable statement | yes | explicit "satisfies the machine-readability requirement" paragraph |
| Every source named | yes | 9 sources enumerated as bullet list |
| Retrieval timestamp | yes | every bullet carries `Retrieved 2026-04-16` |
| License / access terms | yes | every bullet carries free-to-access + API-key note |
| Canonical URL | yes | every bullet carries a URL |
| SHA-256 back-reference | yes | every bullet carries `SHA-256 hash recorded in manifest row ...` |
| Cross-reference to manifest (Trio 1) | yes | §1 Trio 1 cross-reference explicit in first paragraph |
| Reproducibility statement | yes | closing "Reproducibility" sub-paragraph naming cleaning.py |
| Documented drift source | yes | explicit FRED vintage + DANE retrospective corrections note |

**Verdict: full SSDE 2024 compliance.** The DAS is one of the strongest
pieces of prose in the notebook — it is the single document that a
replicator would read first and it delivers everything required to
attempt a byte-level reproduction.

Minor nit: cell 9 uses `## Data Availability Statement` as its own H2,
which creates a duplicate-numbering issue with §1 (which should
logically contain it). See §10 critical issues.

---

## 5. Decision card structural audit

Twelve Decision cards audited against five required dimensions:

| # | Cell | Bold heading | Primary value | Consequences ≥3 | Sensitivity alt named | Pre-commit source | Honest footnote |
|---|---|---|---|---|---|---|---|
| 1 | 18 | yes | 2008-01-02 → 2026-03-01, n=947 | 5 bullets | "separate decision card in a dedicated sensitivity trio" | `banrep_ibr_daily.date_min` | none required |
| 2 | 33 | yes | RV^(1/3) | 4 bullets | log(RV), Student-t OLS (NB3) | spec Rev 4 §6 NB1.3 | documents `|skew|` and kurt trade-off |
| 3 | 36 | yes | weekly | 4 bullets | A1 daily companion (NB3) | spec Rev 4 pre-commit | none required |
| 4 | 45 | yes | cpi_surprise_ar1 | 4 bullets | A9 asymmetric, 60-mo rolling | spec Rev 4 pre-commit | 94%-negative asymmetry + attenuation |
| 5 | 54 | yes | us_cpi_surprise_ar1_warmup_12m | 3 bullets | 6-mo warmup (NB3) | spec Rev 4 pre-commit | fat tails map to real events |
| 6 | 75 | yes | event_study_delta_ibr_meeting_sum | 4 bullets | Bloomberg OIS surprise | 2026-04-18 methodology research | bib-entry gap flagged in-card |
| 7 | 66 | yes | vix_avg_weekly_mean | 4 bullets | Friday-close (not pre-reg) | spec Rev 4 pre-commit | none required |
| 8 | 81 | yes | oil_return_weekly_lastpositive | 4 bullets | arithmetic mean of log-returns | spec Rev 4 pipeline contract | 2020-03-30 small-denominator |
| 9 | 90 | yes | intervention_dummy | 4 bullets | signed + abs amount, S7 | literature + Trio 2 info analysis | 73-week data-freshness gap |
| 10 | 96 | yes | none_max_vif_1p04 | 4 bullets | orthogonalize (not triggered) | §5 Trios 1-3 | none required |
| 11 | 105 | yes | levels_no_differencing | 4 bullets | first-diff (not pre-reg) | spec Rev 4 pre-commit | KPSS over-rejection documented |
| 12 | 114 | yes | listwise_complete_case | 4 bullets | forward-fill, MICE | spec Rev 4 + Task 12 §7 | none required |

All twelve Decision cards pass structural audit. Bold-heading convention
(`**Decision #N — ...**`) is uniform. Consequences lists consistently hit
3-5 bullets. Sensitivity alternatives are named explicitly and trace to
the Task 13 pre-registration document that Reality Checker/Model QA will
audit. `Ledger status: committed (irreversible)` closes every card.

**Positive finding unique to documentation review:** Decisions #6 and
#9 self-document their own open loose ends (`references.bib cleanup
pending`, `S7 pre-registration amends contracts/.scratch/...`). This is
the right author behavior — no silence on known gaps — and the flags
act as a to-do list that the Task 15 reviewer can action directly.

---

## 6. Reproducibility artifact review — `nb1_panel_fingerprint.json`

Top-level keys present:
`daily_panel`, `decision_hash`, `decisions`, `generated_at`, `ledger_table`,
`weekly_panel`.

| Field | Present | Content |
|---|---|---|
| `decisions` (dict of locked values) | yes | 13 keys (matches LockedDecisions dataclass) |
| `decision_hash` | yes | 64-char SHA-256 |
| `weekly_panel.sha256` | yes | 64-char SHA-256 |
| `weekly_panel.row_count` / `date_min` / `date_max` / `column_dtypes` | yes | 947, 2008-01-07, 2026-02-23, 18 columns |
| `daily_panel.sha256` | yes | 64-char SHA-256 |
| `daily_panel.row_count` / `date_min` / `date_max` / `column_dtypes` | yes | 4306, 2008-01-03, 2026-02-27, 12 columns |
| `ledger_table` (12 rows) | yes | one per Decision, commit_sha + cell_index + anti_fishing_binding populated |
| `generated_at` | yes | ISO 8601 with tz |
| **`schema_version`** | **NO** | — |

**Reproducibility verdict: functionally complete, missing one defensive
field.** NB2's pre-flight re-computes the three fingerprints and asserts
bit-equality. That is sufficient to detect data drift. But NB2 has no
way to detect **schema drift** — a future author adding, removing, or
renaming a top-level key in the fingerprint would silently break NB2's
parser in ways that may or may not raise depending on how defensively
NB2 reads the JSON. A single `"schema_version": "1.0.0"` top-level field
(and a `SCHEMA_VERSION = "1.0.0"` constant in `cleaning.py`) would close
this gap for a one-line emit change.

Everything else is correct. The `ledger_table` cell-index values
(18, 33, 36, 45, 54, 75, 66, 81, 90, 96, 105, 114) round-trip against
the notebook's actual Decision-card cell positions. The `commit_sha`
values are populated (though four of them are human-readable labels
like `cpi_surp_ar1` rather than git SHAs, which is a minor
reproducibility nit — see minor issues).

---

## 7. references.bib hygiene

- **Entry count:** 35 (not 37 as claimed in the Task 15 digest).
- **Duplicates:** none.
- **Unescaped `&`:** none detected — all `&` tokens in titles are
  escaped as `\&`.
- **DOI or URL on every entry:** yes. Entries that legitimately lack a
  DOI (Belsley-Kuh-Welsch 1980, Campbell-Lo-MacKinlay 1997, Conrad 2025
  SSRN, Fuentes 2014 BIS WP, Levene 1960, Mincer-Zarnowitz 1969,
  Rincón-Torres 2021, Wilson-Hilferty 1931) carry an explicit `url`
  field with a justifying inline comment (`"no DOI on the 1980
  edition; WorldCat/Wiley retains a canonical product URL"`).
  This is the right hygiene for BibTeX.
- **Reference metadata quality:** high. Explicit `note` fields
  distinguish working papers from journal-of-record entries
  (Conrad 2025: `"Forthcoming. Working-paper copy: SSRN 4632733."`),
  and correction comments are visible (`"PLAN REV 2 CORRECTION:
  Han-Kristensen 2014 journal is JBES, not JoE."`).

**Gap flagged at Decision #6 and Decision #9:** the phase-1 findings
digest and the Decision #6 prose (cell 75) and Decision #9 prose
(cell 90) both cite Anzoátegui-Zapata & Galvis 2019 and Uribe-Gil
& Galvis-Ciro 2022 BIS WP 1022 as methodological grounding for the
BanRep event-study construction. Neither entry exists in
`references.bib`. The Decision #6 card itself flags this
("Anzoátegui-Zapata & Galvis 2019; Uribe-Gil & Galvis-Ciro 2022
BIS WP 1022 — not yet in references.bib") and lists "references.bib
cleanup pending" as a closing line. The digest says `test_references_bib.py
count 35 → 37`.

This is a known, explicitly-flagged gap. It must be closed before
the Task 15 review gate actually passes.

---

## 8. PDF rendering readiness

| Check | Status |
|---|---|
| All 39 code cells tagged `remove-input` | yes — 39 / 39 |
| Forbidden chasing-offline phrases absent | yes — 0 hits |
| lint exits 0 | yes |
| Figures titled with `fig.suptitle` | partial — 12 of 17 figures have suptitle |
| All axes labelled | yes (spot-check on cells 20, 38, 47, 62, 92, 101) |
| DataFrames truncation-safe | partial — many cells rely on `print(df.to_string(index=False))` (safe) but no `pd.set_option('display.max_columns', ...)` at the top of the notebook. If cells print via `display(df)` under nbconvert with default `max_columns`, wide tables (12+ cols) may wrap awkwardly. |
| Output size | not spot-verified — table outputs are all bounded (`n=947`, summary tables) so unlikely to exceed nbconvert default |

**Figures missing suptitle (5 code cells):** cells 41, 50, 62, 92, 101.
These are `fig, axes = plt.subplots(...)` blocks where only per-axis
`ax.set_title(...)` is called. In PDF export they will render with
sub-titles but no overarching figure title, which weakens the figure's
self-containment. Cell 98 has a suptitle but no per-axis set_title —
opposite failure mode.

This is not a correctness issue and not a lint failure (no lint exists
for figure titles). It is a polish gap that Tech Writer flags because
PDF review downstream will see figures with no top-level caption.

---

## 9. Honest-caveat visibility audit

Four documented caveats. All cross-referenced across multiple cells:

| Caveat | Primary cell | Cross-reference cells | Framed as limitation? |
|---|---|---|---|
| Colombian CPI 94%-negative asymmetry | 45 (Decision #4) | 34, 37, 39, 40, 42, 43, 46, 48, 51, 73, 75, 87, 88, 99 | yes — attenuation risk explicit, regime-specific root cause named |
| Intervention data-freshness gap | 90 (Decision #9) | 84, 85, 87, 88, 108, 109, 112, 114 | yes — 73-week gap quantified, S7 sensitivity cross-linked |
| KPSS caveats | 105 (Decision #11) | 100, 102, 103 | yes — over-rejection under heteroskedasticity documented |
| Oil 2020-03-30 small-denominator | 81 (Decision #8) | 69, 72, 78 | yes — framed as known log-return property |

Every caveat is:
- Surfaced where the reader first meets the underlying statistic
  (Trio 1 descriptive cell).
- Re-iterated in the Decision card that locks the associated primary.
- Cross-referenced from the §5, §6, §7, §8 downstream discussions
  where the caveat could attenuate or invalidate an inference.

This is textbook honest-footnote practice. There is no "hand-waving"
language; every caveat is paired with either a sensitivity-run
pre-registration (S7) or an explicit attenuation-direction statement
("passing T3b despite attenuation strengthens the result; failing T3b
does not preclude the effect"). The reader cannot miss them — every
caveat surfaces at least three times in the flow.

---

## 10. Critical issues (blocking reader comprehension or PDF export)

### C1. §5, §6, §7, §8 have no `##` heading — they render as sub-sections of §4

`##` H2 headings exist only for §1, §2, §3, §4, and for the
Data-Availability-Statement cell 9. §5 through §8 are introduced only
at `###` H3 level (first appearance at cells 91, 100, 106, 115). In
any PDF TOC, Jupyter sidebar, or nbconvert LaTeX bookmark tree, §5
"Joint regressor diagnostics," §6 "Stationarity," §7 "Missingness,"
and §8 "Handoff" will nest under §4 "RHS EDA" — visually suggesting
the joint/correlation/stationarity work is a sub-audit of a single
regressor rather than standalone specification-lock sections.

**Fix:** insert four `##` section-header markdown cells before the
first `###` of each of §5, §6, §7, §8. Each should carry a one-sentence
orientation ("§5 locks Decision #10 on collinearity," etc.). Cost:
4 markdown-cell inserts.

### C2. §4c Trio 2 and Trio 3 are physically out of order

Cell ordering in §4 reads: `§4a (40-45) → §4b (46-54) → §4c Trio 1
(55-57) → §4d Trio 1 (58-60) → §4d Trio 2 (61-63) → §4d Trio 3 (64-66)
→ §4e Trio 1 (67-69) → §4c Trio 2 (70-72) → §4c Trio 3 (73-75) →
§4e Trio 2 (76-78) → §4e Trio 3 (79-81)`.

The BanRep-rate-surprise narrative is therefore split by VIX and oil.
A linear reader who reaches Decision #6 at cell 75 will have last seen
the BanRep Trio 1 at cell 55 — 20 cells prior. The Decision #6 card
assumes the reader just read Trios 1-2, which on the physical ordering
is false.

**Fix:** move cells 70, 71, 72, 73, 74, 75 (§4c Trios 2-3 +
Decision #6) to appear immediately after cell 57 (the §4c Trio 1
interpretation cell). Cost: cell-order reshuffle, no content change.

### C3. `nb1_panel_fingerprint.json` has no `schema_version`

The fingerprint JSON is the NB1 → NB2 → NB3 handoff contract. NB2
re-computes the three hashes and asserts bit-equality, which catches
data drift. There is no mechanism to detect schema drift: if a future
refactor renames `weekly_panel.sha256` to `weekly_panel.hash`, NB2
will silently load an undefined field and may default-through a
nonsense comparison. A top-level `"schema_version": "1.0.0"` (mirrored
as a module constant in `cleaning.py` and asserted at NB2 load) closes
this gap.

**Fix:** one-line addition in `_LEDGER_ROWS` emission logic (cell 116)
and a corresponding constant + assert in `scripts/cleaning.py`.
Cost: one-line JSON emit + one assert.

### C4. `references.bib` missing Decision #6 grounding citations

Anzoátegui-Zapata & Galvis 2019 and Uribe-Gil & Galvis-Ciro 2022 BIS
WP 1022 are cited in prose (cells 75, 90) as the methodological
grounding for the event-study construction. Neither is in
`references.bib`. Under nbconvert LaTeX export, any `\cite{}` to these
keys would throw "citation undefined" warnings. The Task 15 digest
explicitly lists closing this gap as action item #1.

**Fix:** add two `@techreport` or `@article` entries. Cost: two bib
entries + `test_references_bib.py` count update 35 → 37.

---

## 11. Minor issues (prose cleanups, formatting nits)

- **Cell 0 "Status: skeleton (Task 1c)":** factually incorrect on a
  complete notebook. Strip or replace with "Status: Phase 1 complete
  (Task 15 review in progress)."
- **Cell 1 placeholder admonition:** explicit "placeholder" framing is
  honest but weakens the executive-summary layer. Consider a `Gate
  Verdict: pending NB2/NB3` with a one-line explanation of what the
  gate tests.
- **Cell 9 uses `## Data Availability Statement`:** duplicate-numbering
  within §1 scope. Demote to `### Data Availability Statement` so §1
  contains it cleanly, or alternatively elevate DAS to a standalone
  "DAS — Full Statement" ## with §1 narrowed to "Setup and Provenance."
- **§4f uses `####` (H4) for Trios 2 and 3 (cells 85, 88):** every
  other trio in §4a through §4e uses `###`. Normalize to `###`.
- **No up-front roadmap cell:** between cell 1 and cell 2, insert a
  150-300 word "what NB1 establishes" roadmap naming the 12 Decisions
  by scope and the handoff artifact path. The reader who opens the
  PDF cold needs this.
- **No §8 summary:** cell 117 is a §8b-specific interpretation. A
  final closing cell retrospecting "what NB1 established and what NB2
  inherits" would mirror the strong Decision #3 closing in cell 36
  and give the PDF a proper ending.
- **Figure titling inconsistency:** cells 41, 50, 62, 92, 101 lack
  `fig.suptitle(...)`; cell 98 lacks per-axis `ax.set_title(...)`.
  Either convention is acceptable; pick one and normalize.
- **Ledger `commit_sha` field is mixed git SHA + human label:**
  Decisions 1, 2, 3 have real 9-char SHAs (`0d4fc1bec`, `ff1ac5bdd`,
  `9eb38ab46`); Decisions 4-12 have human-readable labels
  (`cpi_surp_ar1`, `us_cpi_w12m`, `banrep_evt_sum`, ...). For a
  strict reproducibility artifact, replace labels with the actual
  commit SHA of the commit that locked each Decision, or rename the
  field to `lock_label` to signal intent.
- **Cell 115 (§8b reference block) cites Ankel-Peters 2024 as
  "replication protocol" and Simonsohn 2020:** the bib-key
  `simonsohn2020specification` actually points to Nature Human
  Behaviour 2020 (Specification Curve Analysis). The prose correctly
  maps. Nit: `[ankelPeters2024protocol]` square-bracket citation style
  is inconsistent with the plain-prose style used in most other
  citation blocks ("Andersen, Bollerslev, Diebold and Vega (2003, ...)
  — bib key `andersen2003micro`"). Harmonize.
- **Stale phrase at cell 18 mentions "§7 Decision-ledger semantics":**
  §7 is the missingness section; the Decision ledger lives in §8b.
  Replace with "§8 Decision-ledger semantics."

---

## 12. Recommendation

**CONDITIONAL PASS** — merge only after C1-C4 are closed. None of the
blockers are content-level; all four are mechanical structural fixes
that should take under an hour of authoring work.

**Minimal closure list for unconditional PASS:**

1. Insert four `## 5 / 6 / 7 / 8` section-header markdown cells
   (C1). ~20 min.
2. Reshuffle cells 70-75 to after cell 57 (C2). ~15 min + lint re-run.
3. Add `"schema_version": "1.0.0"` to fingerprint emit + NB2 pre-flight
   assert (C3). ~15 min.
4. Add two missing bib entries (Anzoátegui-Zapata 2019, Uribe-Gil 2022
   BIS WP 1022) + update `test_references_bib.py` count (C4). ~15 min.

**Recommended but non-blocking (minor issues):**

5. Strip "skeleton (Task 1c)" stale status from cell 0, insert
   150-300 word roadmap cell after cell 1, add §8 summary closing
   cell after cell 117.
6. Normalize §4f H4 → H3 depth (cells 85, 88).
7. Demote cell 9 DAS heading H2 → H3 (or elevate DAS outside §1).
8. Add suptitle to cells 41, 50, 62, 92, 101; add set_title to cell 98.
9. Replace Decision ledger commit_sha labels 4-12 with real SHAs, or
   rename field to `lock_label`.
10. Harmonize citation-style (prose vs square-bracket) across §6, §7,
    §8b citation blocks.

**Documentation-quality verdict unique to Tech Writer prong:** the
citation-block discipline in NB1 is the strongest I have seen in a
Jupyter notebook outside of formal journal-submitted replication
packages. The four-header rule is not merely satisfied mechanically —
it has visibly forced the author to justify every gated decision
against specific literature, name the downstream consumer in the
simulator, and flag honest limitations. A macro-finance PhD student
unfamiliar with the RAN project would be able to read this notebook
and reconstruct the full specification-lock argument without
external context. That is the true test of a reproducibility
package, and NB1 passes it.

Model QA and Reality Checker will independently assess econometric
validity and adversarial correctness; those are out of Tech Writer's
scope. The documentation prong is ready to sign off once C1-C4 are
closed.
