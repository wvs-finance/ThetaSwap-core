# Technical Writer — Task 11.O-scope-update (Rev-5.3.2 §B in-place edit)

**Date:** 2026-04-25
**Scope:** SPEC review per `feedback_three_way_review` (CR + RC + TW). TW lens = documentation-quality: internal consistency, prose clarity, style alignment with surrounding plan content.
**Mode:** Read-only audit of uncommitted plan-markdown edit.
**Target file:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
**Diff vs. HEAD `ac67eaf71`:** +18/−5 = +13 net lines across the Task 11.O body (lines 1213, 1217–1222, 1228–1232, 1236, 1238) and the §B annotation note (line 2017).

---

## Verdict — PASS-with-non-blocking-advisories

The eight TW-lens checks all return PASS with no blockers. Two non-blocking documentation-quality advisories surface:

- **TW-A1** (advisory, optional): the new Step-0 / Step-1 / Step-2 / Step-2b / Step-3 / Step-4 / Step-5 sequence is readable but `Step 2b` is a smell that the spec author may want to either (i) accept as a stable label by virtue of pre-registration appearing in scratch reviews and the §B annotation, or (ii) promote to `Step 3` with renumbering. Recommendation: accept as-is — the renumbering cost is non-zero (cross-references in `2026-04-25-y3-110-scope-update-review-code-reviewer.md` already cite line numbers for "Step 2b at line 1231"; renumbering would invalidate them). Documentation-quality cost is a one-character lexical irregularity.
- **TW-A2** (advisory, optional): the `Final[dict[str, str]]` annotation in the Future-maintenance note (line 1236) is borderline-prose-vs-borderline-code. After cross-checking against eleven prior occurrences in this plan body (lines 3, 1028, 1036, 1049, 1056, 1118–1125, 1174 — all `<NAME>: Final[<type>]` constant-declaration mentions in **prose context**), I conclude it is consistent with established plan voice. It is a documented constant declaration (not an imperative code block); the surrounding text reads as natural prose ("the natural fold is to a structured `_Y3_METHODOLOGY_PROVENANCE: Final[dict[str, str]]` provenance dict"); it does not cross the `feedback_no_code_in_specs_or_plans` line. Recommendation: accept as-is.

Cleared for orchestrator dispatch alongside the parallel CR (PASS) and RC findings.

---

## Lens-by-lens findings

### 1. Heading hierarchy — PASS

The edit introduces no new headings — only blockquote banner blocks (`> **…:**`), bold-italic step labels (`**Step 0 (…):**`), and the existing `**Inputs:**` / `**Files:**` / `**Future-maintenance note (…):**` / `**Gate:**` block-bold convention. The pre-existing `### Task 11.O:` (line 1211) is unchanged. No level skips, no h4-to-h2 jumps, no orphaned subsections. The blockquote banner at line 1213 mirrors the precedent in §B at line 2017 (both `> **<label>:**` opens followed by inline prose), and matches at least eight other banner-block precedents in the plan front-matter (lines 3–8 status banners) and the corrections-block headers. Heading hierarchy is intact.

### 2. Style alignment with surrounding plan content — PASS

The pre-edit Task 11.O body had a one-paragraph `**Inputs:**` clause; the post-edit body restructures `**Inputs:**` as a 5-bullet list. I cross-checked this restructuring against the immediate-neighbor task bodies:

- Task 11.N.2d at line 1100: `**Inputs:**` is a 5-bullet list (per-country equity, sovereign yield, WC-CPI, Rev-4 panel anchor, Y₃ design doc).
- Task 11.N.2d.1 at line 1170: `**Inputs:**` is a 4-bullet list.
- Task 11.N.2c at line 1043 (truncated read): `**Inputs:**` is a multi-bullet list pattern.
- Task 11.N.2b.1 / 11.N.2b.2: same multi-bullet pattern.

The 5-bullet-list `**Inputs:**` shape in the new edit is the **dominant style** in the surrounding Phase-1.5.5 task bodies. The pre-edit one-paragraph `**Inputs:**` was actually the outlier; the edit brings Task 11.O into line with the rest of the section. Style alignment is improved by the edit, not degraded.

The `**Files:**` block (lines 1224–1226) is unchanged. The `- [ ] **Step N (…):**` checkbox-step convention is preserved. The `**Future-maintenance note (…):**` block (line 1236) introduces a new boldface-block label, but this convention is precedented at Task 11.Q's `**Tier-2 parallel note (out of current phase scope):**` (line 1270), Task 11.N.2d's `**Step Atomicity Protocol (…):**` / `**Collapse-rejected rationale (…):**` / `**Dependency discipline (…):**` / `**Non-negotiable rules (…):**` / `**Recovery protocols (…):**` / `**DAG clarification (…):**` (lines 1138–1160), and ten-plus other places. The label-pattern `**<NAMED-NOTE> (<scope-clause>):**` is established plan idiom. The Future-maintenance note's prose voice (third person describing the artifact, with imperative `Track but do NOT refactor preemptively`) matches the surrounding directive-prose voice in those neighbors.

The new banner block at line 1213 (`> **Rev-5.3.2 scope-update applied:** …`) matches the `> **<revision>:** …` blockquote-banner convention at lines 3–8 (status banners) and at line 298 (`> **Rev-3.1 F-3.1-1 reconciliation note**: …`). Banner-block style is consistent.

The §B annotation at line 2017 (`> **Annotation note (post-edit, 2026-04-25):** …`) likewise matches blockquote-banner convention. The single-paragraph dense-(a)–(f) enumeration prose voice is heavier than the surrounding §B body prose (which uses paragraph breaks plus fenced-bullet lists), but it is appropriate for an annotation-banner whose purpose is to summarize edits already explicit elsewhere in the section. No alignment issue.

### 3. Internal cross-references — (a)–(f) mapping — PASS

The §B annotation at line 2017 enumerates six categories of upstream edits. Each maps to a specific edit in the upstream body:

- **(a)** Rev-5.3.2 primary `source_methodology` literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` → upstream edit at line 1219 (Inputs bullet 2): "Rev-5.3.2 primary Y₃ panel under `source_methodology` literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`". MATCH.
- **(b)** Rev-5.3.2 panel window `[2023-08-01, 2026-04-24]` → upstream edit at line 1219: "over the primary panel window `[2023-08-01, 2026-04-24]`". MATCH.
- **(c)** Actual landed gate-clearance count of 76 joint nonzero X_d × Y₃ weeks (≥ `N_MIN = 75` from Rev-5.3.1 path α) → upstream edit at line 1219: "Joint nonzero X_d × Y₃ overlap landed at **76 weeks** (≥ `N_MIN = 75` from Rev-5.3.1 path α; 1-week margin)" + line 1213 banner reaffirmation. MATCH.
- **(d)** Pre-registered LOCF-tail-excluded sensitivity row in the Rev-2 spec (RC A3 / SD-RR-A2; expected 65-week FAIL) plus the IMF-IFS-only sensitivity (56-week FAIL) → upstream edit at line 1231 (Step 2b) for LOCF-tail-excluded; line 1220 (Inputs bullet 3) for IMF-IFS-only sensitivity; both surface in the extended Gate at line 1238. MATCH.
- **(e)** Step-0 precondition flipping the `load_onchain_y3_weekly` default `source_methodology` to the v2 literal and migrating the Step-7 round-trip test to pass an explicit tag (SD-RR-A1) → upstream edit at line 1228 (Step 0). MATCH.
- **(f)** Future-maintenance note about the admitted-set fold-to-provenance-dict at ~6-tag threshold (SD-A4 from `contracts/.scratch/2026-04-25-y3-reframe-review-senior-developer.md`) → upstream edit at line 1236 (Future-maintenance note block). MATCH.

All six annotation categories resolve to specific upstream edits. No dangling references, no unmatched annotations, no upstream edits omitted from the annotation. The annotation is faithful to the upstream body.

### 4. Step numbering coherence — PASS-with-advisory

The new step sequence is `Step 0 (precondition) → Step 1 (skill invocation) → Step 2 (resolution-matrix derivation) → Step 2b (pre-registered sensitivity) → Step 3 (MDES) → Step 4 (lit re-check) → Step 5 (commit)`. The `2b` insertion is the only mild irregularity.

**Pre-edit shape:** Step 1 → Step 2 → Step 3 → Step 4 → Step 5 (5 monotone steps).

**Post-edit shape:** Step 0 → Step 1 → Step 2 → Step 2b → Step 3 → Step 4 → Step 5 (6 conceptual steps with one `2b` half-step label).

The Step 0 prefix (precondition) is the well-established convention across Phase-1.5.5 task bodies — every recent task uses Step 0 for a pre-flight precondition or pre-commit constants block (Task 11.N.2d Step 0 at line 1128 = "pre-commit constants + failing-first test"; Task 11.N.2d.1 Step 0 at line 1182 = "failing-first sensitivity test"; Task 11.N.2c Step 0 at line 1056 = "pre-commit thresholds"). So Step 0 prepended in the new edit is consistent.

The `Step 2b` insertion is mildly atypical. Rationale to keep it labeled `2b` rather than promote to `Step 3` with renumbering:

1. Step 2b is a structurally **conditional sub-step of the resolution-matrix derivation** in Step 2 (it pre-registers a sensitivity row that lives **inside** the resolution matrix — Step 2 is the matrix; Step 2b enumerates one specific row of that matrix). The `2b` label captures the parent-child relationship semantically.
2. Renumbering would shift the existing pre-edit `Step 3 (MDES)` → `Step 4 (MDES)`, `Step 4 (lit re-check)` → `Step 5 (lit re-check)`, `Step 5 (commit)` → `Step 6 (commit)`, breaking external scratch-file cross-references that already cite "Step 3 (MDES — fixes Rev-1.1.1 CR-E2)" by exact line number (e.g., the CR scratch review at `contracts/.scratch/2026-04-25-y3-110-scope-update-review-code-reviewer.md` cites "Step 3, line 1232" verbatim).
3. The `2b` label makes the diff smaller and more reviewer-auditable: an external reader following the diff sees one inserted half-step rather than four shifted line numbers.

Recommendation: **accept `Step 2b` as-is**. The semantic-parent-child rationale, the renumbering cost, and the auditable-diff argument all favor stability over a full renumber.

(This is TW-A1, repeated here for completeness; non-blocking.)

### 5. Pre-registered sensitivity rows readability (Step 2b) — PASS

Step 2b at line 1231 is dense (one ~250-word paragraph) but each enumerated row is labeled clearly:

- The **primary** anchor (76 weeks) is named in Inputs bullet 2 (line 1219) and re-anchored at Step 1 (line 1229: "the operative `n` for all power calculations") and at Gate (line 1238).
- The **`LOCF-tail-excluded`** sensitivity (65 weeks → FAIL by 10 weeks) is labeled in bold (`**`LOCF-tail-excluded` sensitivity row**`) at line 1231, with the operational definition ("re-count joint nonzero X_d × Y₃ overlap after truncating Y₃ at the EU 2025-12-01 binding cutoff …") and the pre-committed verdict ("65 weeks → FAIL by 10 weeks against `N_MIN = 75`") spelled out. Cross-reference to RC scratch probe-5 anchored at `contracts/.scratch/2026-04-25-y3-rev532-review-reality-checker.md`.
- The **IMF-IFS-only** sensitivity (56 weeks → FAIL by 19 weeks) is labeled in bold (`**Rev-5.3.2 IMF-IFS-only sensitivity Y₃ panel**`) at line 1220 (Inputs bullet 3), with operational definition (`source_methodology` literal `y3_v2_imf_only_sensitivity_3country_ke_unavailable`, same window, 56-week joint coverage, FAIL by 19) and provenance pointer to `contracts/.scratch/2026-04-25-y3-imf-only-sensitivity-comparison.md`. Step 2b also re-cites this row in its closing sentence: "The pre-registered IMF-IFS-only sensitivity (Rev-5.3.2 Task 11.N.2d.1-reframe; 56-week FAIL) is enumerated alongside as a separate sensitivity row guarding against silent source-upgrade reversal."

The Gate enumeration at line 1238 anchors all three rows in a single sentence: "Rev-5.3.2 panel anchors (primary 76-week + LOCF-tail-excluded sensitivity 65-week + IMF-IFS-only sensitivity 56-week) all enumerated as pre-committed sensitivity rows."

A future maintainer reading the post-edit Task 11.O body top-to-bottom encounters each row (i) named in bold at first mention, (ii) operationally defined, (iii) pre-committed verdict spelled out, (iv) provenance pointer to a scratch file, and (v) reaffirmed in the Gate. The chain of references is closed.

One minor advisory (non-blocking, embedded in the existing prose so already covered): Step 2b says "the sensitivity row name is the spec author's choice; the substance is fixed." This is good — it gives the spec author lexical flexibility while pre-committing the substantive verdict. The same flexibility is implicitly extended to the IMF-IFS-only row by virtue of the source-upgrade comparison memo holding the operational definition. Readability passes.

### 6. Identifier-name references — PASS

The new edit cites the following identifiers from `scripts/econ_query_api.py` and adjacent modules:

- `load_onchain_y3_weekly` (function name; lines 1228, 1236) — a referenced module-level identifier per project convention; cited byte-exact.
- `source_methodology` (parameter name AND DuckDB column name; lines 1219, 1220, 1228) — cited byte-exact in every reference.
- `_KNOWN_Y3_METHODOLOGY_TAGS` (module-level admitted-set frozenset; line 1236) — cited byte-exact (CR review confirms it matches `econ_query_api.py:72`).
- `_Y3_METHODOLOGY_PROVENANCE` (proposed future module-level dict; line 1236) — cited as a forward-looking name; matches the SD-A4 advisory phrasing in `contracts/.scratch/2026-04-25-y3-reframe-review-senior-developer.md` §2.
- `MDES_FORMULATION_HASH` (line 1222) — cited byte-exact.
- `y3_v1` / `y3_v1_3country_ke_unavailable` / `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` / `y3_v2_imf_only_sensitivity_3country_ke_unavailable` (string literals; lines 1228, 1236) — all four cited byte-exact, all four enumerated as the current 4-entry admitted-set.
- `scripts/tests/inequality/test_y3.py` line range `285–323` (line 1228) — specific line range cited; CR review confirms the line range matches at fix-up commit `2a0377057`.

All identifier-name references are factual, byte-exact, and resolved against actual module identifiers in the codebase per the parallel CR review's spot-check.

The annotation `Final[dict[str, str]]` in the Future-maintenance note (line 1236) is a Python typing annotation embedded in a constant-declaration mention. This pattern is precedented eleven times elsewhere in this plan body (see TW-A2 above). It does not cross into executable code (no function bodies, no import statements, no statements with side effects). It is documentation prose describing a future module-level constant in the same shape that the surrounding plan already uses for `MDES_FORMULATION_HASH: Final[str]`, `WC_CPI_FOOD_WEIGHT: Final[float]`, etc.

### 7. Code-agnosticism per `feedback_no_code_in_specs_or_plans` — PASS

I scanned the diff for executable code blocks (triple-fenced `````python` / `bash` / `sql`), function definitions (`def …:`), control-flow statements (`if … else`), loops, imports, and procedural blocks. None present in the new edit.

What IS present:

- **Identifier-name citations** (function names, table names, column names, literal string values, sha256 anchors) — all in inline backticks, all describing existing or pre-committed module-level artifacts. This is standard plan voice and explicitly permitted by `feedback_no_code_in_specs_or_plans` (the rule forbids code, not documented references to code).
- **Equations cited as inline math** — `Y_asset_leg_t = (Banrep_rate_t − Fed_funds_t)/52 + (TRM_t − TRM_{t-1})/TRM_{t-1}` at line 1229 (unchanged from pre-edit body); precedented by neighbor tasks.
- **Type annotations** — `Final[dict[str, str]]` at line 1236; precedented eleven-plus times in this plan.
- **Filesystem path references** — `scripts/econ_query_api.py`, `contracts/.scratch/<…>.md`, etc.; standard plan voice.

Nothing in the new edit crosses the code-agnosticism line. The §B annotation explicitly states "the structural-econometrics-skill invocation methodology is unchanged byte-exact" — i.e., the skill is the implementation surface, not the plan body.

### 8. Gate enumeration accuracy (line 1238) — PASS

The pre-edit Gate read: "Rev-2 spec committed with functional equation + pre-committed null + scipy-correct MDES + literature-grounded identification assumptions. All 13 resolution-matrix rows populated."

The post-edit Gate reads: "Rev-2 spec committed with functional equation + pre-committed null + scipy-correct MDES + literature-grounded identification assumptions + Rev-5.3.2 panel anchors (primary 76-week + LOCF-tail-excluded sensitivity 65-week + IMF-IFS-only sensitivity 56-week) all enumerated as pre-committed sensitivity rows. All 13 resolution-matrix rows populated."

The four pre-existing acceptance criteria (functional equation, pre-committed null, scipy-correct MDES, literature-grounded identification) are preserved verbatim. The new fifth criterion — "Rev-5.3.2 panel anchors … all enumerated as pre-committed sensitivity rows" — is the additive Gate update.

I cross-checked the three panel-anchor counts in the Gate against the upstream body:

- **76-week primary** matches Inputs bullet 2 (line 1219), Step 1 operative-`n` clause (line 1229), Step 3 N_eff enumeration (line 1232: "76 under primary Rev-5.3.2 panel"), and the line-1213 banner ("76 ≥ 75 weeks").
- **65-week LOCF-tail-excluded sensitivity** matches Step 2b pre-committed verdict (line 1231: "65 weeks → FAIL by 10 weeks against `N_MIN = 75`") and Step 3 N_eff enumeration (line 1232: "65 under LOCF-tail-excluded sensitivity").
- **56-week IMF-IFS-only sensitivity** matches Inputs bullet 3 (line 1220: "joint X_d × Y₃ overlap = 56 weeks; FAIL by 19 weeks against `N_MIN = 75`") and Step 3 N_eff enumeration (line 1232: "56 under IMF-IFS-only sensitivity").

All three anchor counts are internally consistent across the four occurrences in the post-edit body. The Gate prose accurately summarizes the pre-registration. The "All 13 resolution-matrix rows populated" closing clause is preserved byte-exact, which means the resolution-matrix discipline is preserved and the gate continues to require the existing 13-row population.

The `13` in the Gate is the standing 13-row resolution-matrix count from the original Task 11.O body (Step 2 pre-edit and post-edit both say "all 13 rows"); not to be confused with the three pre-registered sensitivity rows enumerated in the new edit. A reader could conceivably confuse "13 resolution-matrix rows" with the new "3 sensitivity rows," but Step 2b explicitly disambiguates: "the Rev-2 spec MUST pre-register a `LOCF-tail-excluded` sensitivity row in the resolution matrix or sensitivity panel (the sensitivity row name is the spec author's choice …)." The sensitivity panel is described as a sibling-or-subsection of the resolution matrix; Step 2 retains the 13-row mandate; Step 2b adds two pre-registered rows that may or may not occupy slots within the 13 (spec-author choice). The disambiguation is sufficient — no advisory needed.

---

## What the TW lens did NOT cover (per assignment scope)

Per the orchestrator's assignment, the following are explicitly out of scope for this TW review:

- **Anti-fishing invariant preservation** — Code Reviewer's lane. (CR returned PASS at lens 1; verified `N_MIN = 75`, `MDES_FORMULATION_HASH = 4940360d…cefa`, `MDES_SD = 0.40`, `POWER_MIN = 0.80` byte-exact across the edit.)
- **Coverage arithmetic verification** — Reality Checker's lane (live DB queries against canonical DuckDB).
- **Implementation feasibility** — out of scope for a SPEC review per `feedback_three_way_review`.

I did not verify any of the above; my verdict is conditional on CR + RC clearing them in their parallel reviews.

---

## Summary

**Verdict:** PASS-with-non-blocking-advisories.

The Task 11.O scope-update edit is a faithful, well-styled, internally-consistent in-place plan-markdown amendment. The new banner blocks, the restructured Inputs list, the inserted Step 0 / Step 2b, the Future-maintenance note, and the extended Gate all align with established plan voice (precedented in Tasks 11.N.2d / 11.N.2d.1 / 11.N.2c / 11.Q and the surrounding Phase-1.5.5 corrections-block prose). The §B annotation note's (a)–(f) enumeration maps byte-exactly to specific upstream edits with no dangling references and no omitted edits. Identifier-name references are factual and code-agnostic per `feedback_no_code_in_specs_or_plans`. The three pre-registered sensitivity-row counts (76 / 65 / 56 weeks) are internally consistent across all four occurrences in the post-edit body.

Two non-blocking advisories — the `Step 2b` half-step label and the `Final[dict[str, str]]` annotation — are both within the established plan idiom and recommend **accept-as-is** rather than mutation.

The edit is cleared for orchestrator dispatch alongside the parallel CR (PASS) and RC reviews.
