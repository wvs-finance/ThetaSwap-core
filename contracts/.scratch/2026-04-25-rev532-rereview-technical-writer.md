# Rev-5.3.2 CORRECTIONS Block — Technical Writer Peer RE-REVIEW

**Reviewer**: Technical Writer (peer reviewer of authoring TW)
**Date**: 2026-04-25
**Pass**: SECOND (re-review of the post-fix-up rewrite addressing RC blockers B1/B2/B3 + selected CR/RC/TW advisories)
**Scope**: lines 1789–2097 of `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (the rewritten Rev-5.3.2 CORRECTIONS block ONLY)
**Charter**: documentation-quality lens (style, internal consistency, cross-reference resolution, code-cleanliness, prose clarity, heading hygiene); explicitly NOT semantic correctness, anti-fishing math, or coverage arithmetic (those remain CR's and RC's lanes).
**Prior review**: `contracts/.scratch/2026-04-25-rev532-review-technical-writer.md` (PASS-with-non-blocking-advisories; 9 advisories listed).

---

## Verdict

**PASS.**

The rewrite is clean and fully addresses every TW advisory the authoring agent committed to addressing (TW-1, TW-2, TW-3, TW-4, TW-5, TW-6, TW-9). The two declined advisories (TW-7 inline reviewer charters; TW-8 heterogeneous reference forms in §G) were declined with cosmetic-only justification consistent with Rev-5.3.1 precedent — I accept both declines without further pushback. The +67-line growth (2030 → 2097) is wholly justified by the new "Risk note" honesty paragraph in Task 11.N.2d-rev (~12 lines), the explicit footnote-a definition (3 lines), the canonical four-condition list relocation to §C with the "Anti-fishing tightening" RC-A5 sub-paragraph (~10 lines), the dispatch-ordering paragraph in §B (~6 lines), and the staleness-anchor sentence opening §A (3 lines), plus prose tightening across multiple cells. None of the additions introduces stylistic drift from the Rev-5.3.1 precedent.

Heading hierarchy remains monotonic. Cross-references resolve. No code crept in during the rewrite. The honesty framing in the new Risk note is exemplary — it surfaces bad news (projected ~65 weeks vs. ≥75 gate) at the top of a labeled "Risk note (transparency, not optimism)" sub-paragraph rather than burying it in a parenthetical. A future maintainer reading top-to-bottom cannot miss this.

No remaining blockers; no remaining non-blocking advisories beyond the two previously-declined ones (which I am NOT re-raising).

---

## Blockers

*(none)*

---

## Re-check results

### 1. Heading hierarchy still monotonic — VERIFIED

Headers in scope (extracted via `grep -n -E "^#{1,6} "` over lines 1789–2097):

| Line | Level | Heading |
|---|---|---|
| 1792 | `##` | CORRECTIONS — Rev-5.3.2 |
| 1796 | `###` | Why ζ over the alternatives |
| 1804 | `###` | A. Pre-commitment update |
| 1830 | `###` | B. New / modified plan tasks |
| 1842 | `####` | Task 11.N.2.OECD-probe |
| 1864 | `####` | Task 11.N.2.CO-dane-wire |
| 1890 | `####` | Task 11.N.2.BR-bcb-fetcher |
| 1916 | `####` | Task 11.N.2d-rev |
| 1957 | `####` | Task 11.N.2d.1-reframe |
| 1979 | `####` | Task 11.N.2d.2-NEW |
| 2004 | `####` | Task 11.O-scope-update |
| 2026 | `###` | C. Imputation discussion |
| 2045 | `###` | D. All-data-in-DuckDB invariant |
| 2060 | `###` | E. Acceptance criteria for the CORRECTIONS block ITSELF |
| 2072 | `###` | F. Task count + status reconciliation |
| 2086 | `###` | G. Reference paths |

`##` → `###` → `####` with no skips. Identical hierarchy shape to the prior version, plus three new `####` task headers (CO-dane-wire NEW, OECD-probe rewritten as diagnostic-only, 11.O-scope-update reframed as MODIFY-target). MATCH.

### 2. Style alignment with Rev-5.3.1 precedent still holds — VERIFIED

The +67-line growth distributes across functional additions, not stylistic drift:

- **Risk note** in Task 11.N.2d-rev (~12 lines): introduces a new prose pattern ("transparency, not optimism") not present in the prior version. The pattern is consistent with the "Honesty note" prose introduced in §"Why ζ" (also new in this rewrite). Both paragraphs use the same labeled-sub-paragraph form (`**Label.** Body...`) consistent with Rev-5.3.1's "Anti-fishing guard" / "Status note" labelling style. MATCH.
- **Footnote a** definition (line 1828, ~3 lines): introduces a `**Footnote a (label).** Body...` pattern. Not present in Rev-5.3.1, but the Rev-5.3.1 block had no tables and thus no need for footnotes. The pattern is markdown-compatible (manual anchor matching the inline `see footnote a` reference). MATCH given the new context.
- **Dispatch ordering paragraph** in §B (lines 1834–1840, ~6 lines): adds an enumerated list of three Data Engineer dispatches in serial order. Numbered list in markdown; consistent with the "1. ... 2. ... 3. ..." ordering convention used in plan task bodies elsewhere. MATCH.
- **Anti-fishing tightening** sub-paragraph in §C (lines 2039, ~3 lines as a single paragraph + introductory sentence): consistent with the "Anti-fishing guard" labelling pattern used in §B task bodies. MATCH.
- **Staleness anchor sentence** (line 1806, 1 sentence): exactly the polish I requested in TW-2. MATCH.

No prose-voice drift. Second person + present tense + active voice throughout. Bold-label sub-paragraphs preserved for callout (Status, Subagent, Deliverable, Acceptance criteria, Reviewers, Dependency, Anti-fishing guard, Risk note, Arithmetic note). MATCH.

### 3. Internal cross-references — VERIFIED

The new `Task 11.N.2.CO-dane-wire` ID appears 12 times in the block, consistently formatted:

- Line 1822 (§A CO-source row, body of cell)
- Line 1826 (§A all-data-in-DuckDB row, body of cell)
- Line 1834 + 1837 + 1840 (§B dispatch-ordering paragraph)
- Line 1851 (Task 11.N.2.OECD-probe acceptance criteria, "the CO upgrade path is Task 11.N.2.CO-dane-wire, not OECD")
- Line 1864 (header)
- Line 1884 (Task 11.N.2.CO-dane-wire's own dependency clause; meta-clarifying independence vs. BR-bcb-fetcher)
- Line 1921 + 1951 (Task 11.N.2d-rev — both deliverable and dependency)
- Line 1998 (§B Task 11.N.2d.2-NEW — primary path summary)
- Line 2030 (§C — primary path summary, duplicate of §B's primary path summary; deliberate per RC ack)
- Line 2052 (§D table cell)
- Line 2076 (§F task count enumeration)

All references resolve. The §C deduplication (TW-6) properly defers from §B to §C: §B Task 11.N.2d.2-NEW line 1996 says "must satisfy the four conditions enumerated canonically in §C below" — this is the correct direction (§B as placeholder, §C as authoritative). Line 1996 explicitly cites the deduplication rationale: "to prevent future-maintenance drift between two locations (per TW peer advisory 6)." VERIFIED — exactly what I requested.

The "Reframe" / "REFRAME of an existing task" / "superseded-banner" / "supersede" forms in Task 11.N.2d.1-reframe and Task 11.O-scope-update are mutually consistent. Both point at the same upstream Task 11.N.2d.1 body and use the same vocabulary. MATCH.

### 4. Footnote a — VERIFIED (renders correctly + referenced from right cells)

Footnote `a` is defined at line 1828:

> **Footnote a (`source_methodology` literal-vs-schema discipline).** The CORRECTIONS block describes the schema of the new tag (a non-`y3_v1` value distinguishing the Rev-5.3.2 mixed-source mix from the prior `y3_v1` panel). The literal string itself is finalized at implementation time and recorded in the Task 11.N.2d-rev verification memo (see Task 11.N.2d-rev acceptance criterion (d) below). Reviewers ack the chosen literal in that memo before any downstream task dispatches.

It is referenced from:
- Line 1825 (§A `source_methodology` row, "see footnote a")
- Line 1886 (Task 11.N.2.CO-dane-wire anti-fishing guard, "per §A footnote a")
- Line 1922 (Task 11.N.2d-rev deliverable, "per §A footnote a")

This is **not** standard markdown footnote syntax (`[^a]` ... `[^a]:`) — it's a manually-anchored callout style (`see footnote a` referring to a prose paragraph labeled `**Footnote a (...).**`). This is acceptable in plan/spec writing where machine-rendered footnote tooltips are not the primary reading mode (the doc is read top-to-bottom by reviewers, not via web-rendered tooltips). The label "Footnote a" is unique within the block (single anchor), and the three references all use lowercase "footnote a" / "§A footnote a" form, which matches the bold-prefix label after the definition is found.

Trade-off: a future Docusaurus or MkDocs render would NOT auto-link these. If the plan ever ships to a docs site, a small follow-up pass converting to `[^a]` syntax would render properly. Non-blocking under current convention.

VERIFIED — renders correctly under current plan-prose convention; references resolve unambiguously.

### 5. Honesty / transparency framing in Task 11.N.2d-rev — VERIFIED (readable, NOT buried)

The new "Risk note" paragraph at line 1940–1945:

> **Risk note (transparency, not optimism).** Under the documented mix, the projected joint coverage is approximately **65 weeks** — still below the load-bearing ≥75 gate. The DANE wire-up (Task 11.N.2.CO-dane-wire) raises the ceiling from path-ζ-as-originally-written's 47 weeks to ~65 weeks, but does not by itself reach 75. The HALT clause above is the protective net for this case. If the gate does not clear under the actual landed mix, two follow-up paths are visible at this writing:
> - **(a)** A δ-EU upgrade. ...
> - **(b)** Escalation to user. ...

A future maintainer reading top-to-bottom encounters this paragraph immediately after the "Arithmetic note" (which itself sets up the projected count of ~65 weeks via RC's live DuckDB query result). The label "Risk note (transparency, not optimism)" is unambiguous about its function — it is a NEGATIVE-FINDING callout, not a hedge or qualifier on a positive finding.

Two structural decisions make this readable:

1. **Bold-label-prefix convention** ("**Risk note (transparency, not optimism).**") — consistent with the Rev-5.3.1 "Anti-fishing guard" pattern; reviewers know to read these as load-bearing.
2. **The note appears BEFORE the acceptance-criteria HALT clause is restated** ("The HALT clause above is the protective net for this case") — making explicit that the mechanism for handling the bad news is already in place, not invented after the fact.

The follow-up paths (a) and (b) are listed as bullets directly below, structurally separate from the prose. (a) names a concrete next move (δ-EU upgrade with quantified joint-coverage estimate ~76 weeks); (b) routes to user. The reader cannot finish this paragraph believing the plan is over-optimistic.

The closing line 1945 ("This risk note is informational. The plan's job is to reach the truth, not to promise success. The Rev-5.3.2 acceptance criteria do NOT relax in response to this risk; the gate stays at ≥75; the HALT stays in place.") is exemplary anti-fishing-discipline-respecting honesty framing. The plan body explicitly refuses to use the risk note as a back-door rationale for relaxing the gate — exactly the discipline that the `feedback_pathological_halt_anti_fishing_checkpoint` MEMORY entry demands.

VERIFIED — the bad news is fully readable; the framing is honest; a future maintainer cannot misread it as optimism.

The §"Why ζ over the alternatives" "Honesty note" at lines 1802 contains the same disclosure, framed for the Trigger paragraph audience (reviewer reading the block top-to-bottom for the first time). This is a deliberate redundancy — the bad news appears once at the top (decision-rationale section) and once again at the relevant task body (acceptance-criteria section). Defensible duplication; readers entering at either point see the same disclosure.

### 6. Prior advisory status — ALL CLAIMED-ADDRESSED VERIFIED

| Advisory | Claim | Verification | Status |
|---|---|---|---|
| **TW-1** (§F double-classification) | Addressed via bullet split | Line 2076 "+5 new task IDs with new bodies" + Line 2077 "+1 new task ID with MODIFY-target deliverable" — exact split I requested | **VERIFIED** |
| **TW-2** (staleness anchor sentence) | Added | Line 1806 "All staleness arithmetic in this section is anchored to the Rev-5.3.2 authoring date **2026-04-25**." — exactly the anchor I requested at the top of §A | **VERIFIED** |
| **TW-3** (§A `source_methodology` cell hoisted) | Addressed | Line 1825 cell now reads compactly with "see footnote a"; Footnote a defined at line 1828 — exactly the hoist I requested | **VERIFIED** |
| **TW-4** (Task 11.N.2d-rev arithmetic hoisted) | Addressed | The 100+-word parenthetical that was inside the bulleted acceptance criterion is gone; in its place are two labeled sub-paragraphs ("Arithmetic note (informational; sanity-check at execution time)" at line 1934, "Risk note" at line 1940) — exactly the hoist I requested, plus a TW-reviewer call-out moved to a single sentence at line 1947 outside the bullets | **VERIFIED** (and improved beyond what I requested — the addition of the Risk note is a substantive honesty upgrade) |
| **TW-5** (PM-N4 commit-boundary guard naming) | Addressed | Both `pytest contracts/scripts/tests/` exits 0 clauses now read "(PM-N4 commit-boundary guard)" — line 1877 (Task 11.N.2.CO-dane-wire), line 1931 (Task 11.N.2d-rev) | **VERIFIED** |
| **TW-6** (imputation 4-condition deduplication) | Addressed | §B Task 11.N.2d.2-NEW line 1996 explicitly defers to §C ("must satisfy the four conditions enumerated canonically in §C below"); §C line 2032 anchors the canonical four-condition list ("**Canonical four-condition list (authoritative; §B Task 11.N.2d.2-NEW references this list).**") | **VERIFIED** — exactly the §C-canonical / §B-deferring resolution I outlined |
| **TW-7** (§E reviewer charters as bullets) | Explicitly declined | §E reviewer charters remain inline `(a)/(b)/(c)` parenthetical-numbered prose | **DECLINE ACCEPTED** (consistent with Rev-5.3.1 precedent; cosmetic only) |
| **TW-8** (§G heterogeneous reference forms) | Explicitly declined | §G remains in mixed-form list (file paths, commit hashes, named constants); references all resolve | **DECLINE ACCEPTED** (cosmetic only; references remain functional) |
| **TW-9** (BR row tightening) | Addressed | Line 1821 BR row now reads "...BCB SGS direct API series 433 (IPCA monthly variation %), per the level-series contract consumed by the BR `fetch_country_wc_cpi_components` dispatch" — exactly the tightening I suggested ("..., per the level-series contract consumed by the BR `fetch_country_wc_cpi_components` dispatch") | **VERIFIED** |

7-of-9 addressed (the two declines accepted with cosmetic-only rationale). No advisory regression introduced.

### 7. No code in plan body — VERIFIED

`grep -E "^\`\`\`"` over lines 1789–2097: ZERO fenced code blocks.

Inline backticked tokens are all named-identifiers / named-constants / named-table-names / named-paths (consistent with Rev-5.3.1 precedent):
- `N_MIN`, `POWER_MIN`, `MDES_SD`, `MDES_FORMULATION_HASH`, `PC1_LOADING_FLOOR`, `decision_hash` — named constants
- `PRIMARY_PANEL_START`, `PRIMARY_PANEL_END`, `SENSITIVITY_PANEL_START` — named pipeline parameters
- `date(2026, 4, 24)`, `date(2024, 9, 1)`, `date(2023, 8, 1)` — named-value literals (acceptable per Rev-5.3.1 precedent)
- `dane_ipc_monthly`, `bcb_ipca_monthly`, `oecd_cpi_monthly`, `onchain_y3_weekly`, `onchain_xd_weekly` — DuckDB table names
- `fetch_country_wc_cpi_components`, `_fetch_imf_ifs_headline_broadcast`, `econ_query_api`, `load_onchain_y3_weekly()`, `required_power(n, k, mdes_sd)` — function names (named-symbol references, not function bodies)
- `proxy_kind = "carbon_basket_user_volume_usd"` — named-value literal in prose
- `(week_start, source_methodology)`, `(date, ipc_value, monthly_variation_pct, _ingested_at)` — schema descriptions in prose form
- File paths under `contracts/...` — repo-relative paths
- Commit hashes — short-form anchors

NONE of the new content (rewritten section A table cells, rewritten task bodies, new "Risk note" paragraph, new footnote-a definition, new "Anti-fishing tightening" §C sub-paragraph, new dispatch-ordering paragraph, new four-condition canonical list at §C) introduces inline Python statements, SQL statements, or fenced code blocks. MATCH with the `feedback_no_code_in_specs_or_plans` discipline.

VERIFIED — code-clean throughout the rewrite.

---

## Style-alignment check (Rev-5.3.1 vs. Rev-5.3.2 — re-evaluation after rewrite)

| Lens | Rev-5.3.1 (precedent) | Rev-5.3.2 (rewritten) | Match? |
|---|---|---|---|
| **Heading style** | Inline bold-paragraph title at L1028 | `## CORRECTIONS — Rev-5.3.2 ...` top-level heading at L1792 | **DIVERGENT but defensible** (scope-driven; same as prior pass) |
| **Section labelling** | Single dense paragraph | Letter-labeled sub-sections A / B / C / D / E / F / G + "Why ζ" rationale | **DIVERGENT but defensible** (scope-driven) |
| **Table conventions** | No tables | Two tables (§A 18-row anchor table; §D 4-row data manifest) | **NEW but well-formed** |
| **Cross-reference resolvability** | All cited paths and hashes resolve | All cited paths + commits + advisory IDs resolve; new "Footnote a" anchor matches three reference points | **MATCH** |
| **Code-cleanliness** | Backticked named constants only; zero fenced code blocks | Backticked named constants + table names + paths only; zero fenced code blocks; zero new Python/SQL | **MATCH** |
| **Heading hierarchy hygiene** | n/a | `##` → `###` → `####`, no skips | **MATCH** |
| **Voice / tense / person** | Second person + present tense + active voice | Second person + present tense + active voice (verified across the new "Risk note", "Honesty note", footnote-a, four-condition canonical list, dispatch-ordering paragraph) | **MATCH** |
| **Bold-label sub-paragraph callouts** | Used for "Anti-fishing guard" and "Status note" | Used for "Subagent / Deliverable / Acceptance criteria / Reviewers / Dependency / Anti-fishing guard / Status / Status note / Risk note / Arithmetic note / Honesty note / Footnote a / Anti-fishing tightening / Canonical four-condition list / Dispatch ordering" | **MATCH (expanded vocabulary; defensible)** |
| **Anti-fishing-guard explicit framing** | One paragraph at the inline block end | Anti-fishing guard sub-bullet under each of the 6 new task bodies; §F task-count, §E reviewer charter, §C four-condition list, §"Why ζ" Honesty note, Task 11.N.2d-rev Risk note all reinforce | **STRONGER — defensible upgrade given expanded payload and the load-bearing nature of the disposition** |

---

## Verification trail

Files read in full:
- `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` lines 1789–2097 (Rev-5.3.2 CORRECTIONS block, post-rewrite)

Files read for re-validation comparison (subset):
- Prior TW review at `contracts/.scratch/2026-04-25-rev532-review-technical-writer.md` (full)

Header extraction:
- `grep -n -E "^#{1,6} "` over the block — 16 headers extracted, hierarchy verified monotonic

Code-cleanliness check:
- `awk 'NR>=1789 && NR<=2097 && /^\`\`\`/'` — zero fenced code blocks

Cross-reference scan:
- `grep -n -E "(Task 11\.N\.2\.CO-dane-wire|footnote a|Footnote a|TW peer advisory|RC advisory)"` over the block — 27 references, all resolve

Cross-checked claims (carried forward from prior pass; no regression):
- Rev-5.3.1 active task count `63` → matches Rev-5.3.2 §F starting figure ✓
- Disposition memo path-letter enumeration `β / γ / δ / ε / ζ` → matches §"Why ζ" ✓
- `MDES_FORMULATION_HASH` value preserved byte-exact ✓
- Rev-4 `decision_hash` value preserved byte-exact ✓

New cross-checks (this pass):
- Footnote a defined once (line 1828); referenced three times (lines 1825, 1886, 1922); zero ambiguity ✓
- TW peer advisory references in plan body (TW-6 at line 1996, TW-1 at line 2077) cite specific advisory numbers from prior pass — accurate citation ✓
- RC advisory references in plan body (A2 at lines 2006, 2018; A3 at line 1926; A4 at line 1834; A5 at lines 2000, 2039; A6 at line 1923) — citation pattern consistent ✓
- §F task count arithmetic shifted from "63 + 5 = 68" (prior version) to "63 + 6 = 69" (rewrite) reflecting CO-dane-wire's promotion to a NEW task; the count is internally consistent with the §F bullet enumeration (5 new task IDs with new bodies + 1 with MODIFY-target deliverable = 6) ✓ (note: not a TW lane to verify task-count accuracy beyond internal consistency; CR/RC own the count semantics)

---

## Summary

The fix-up rewrite addresses every TW advisory the authoring agent committed to addressing (7 of 9), with two declines accepted as cosmetic. No regression introduced. The +67-line growth is functionally justified — every new line has clear purpose (RC-blocker fixes, the honesty-framing Risk note, the staleness anchor sentence, the §C canonicalization, the dispatch-ordering paragraph). Heading hygiene is preserved, code-cleanliness discipline is maintained, cross-references resolve, prose voice is consistent. The Risk note's honesty framing in Task 11.N.2d-rev is exemplary anti-fishing-respecting transparency — a future maintainer reading top-to-bottom cannot misread the projected ~65-vs-75-week gap as optimism.

PASS. Block is ready for landing pending CR + RC re-reviews on their respective lanes.

---

**Reviewer note**: This re-review covers TW lane only. The rewrite's RC blocker fixes (B1 OECD-direct mis-claim → corrected to DANE-via-existing-table; B2 imputation §B-vs-§C duplication → §C canonical / §B deferring; B3 disposition-memo path-mismatch → "Honesty note" at §"Why ζ" plus parenthetical correction throughout) are RC's lane to verify; my pass confirms only that the documentation-quality artifacts of those fixes (cross-references, heading hygiene, prose clarity, advisory citation accuracy) are clean.
