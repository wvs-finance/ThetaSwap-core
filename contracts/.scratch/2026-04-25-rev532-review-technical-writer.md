# Rev-5.3.2 CORRECTIONS Block — Technical Writer Peer Review

**Reviewer**: Technical Writer (peer reviewer of authoring TW)
**Date**: 2026-04-25
**Scope**: lines 1789–2030 of `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (the Rev-5.3.2 CORRECTIONS block ONLY)
**Charter**: documentation-quality lens (style, internal consistency, cross-reference resolution, code-cleanliness, prose clarity, heading hygiene); explicitly NOT semantic correctness, anti-fishing math, or coverage arithmetic (those are CR's and RC's lanes).

---

## Verdict

**PASS-with-non-blocking-advisories.**

The Rev-5.3.2 CORRECTIONS block is well-organized, internally consistent, and resolvable. It uses a heavier formal structure (section labels A–G with a top-level `## ` heading) than the Rev-5.3.1 precedent (which is a single inline bold-title paragraph at line 1028). This is a deliberate and defensible upgrade given the larger payload — five new tasks plus a deliberate non-task plus a §C imputation discussion plus a §D table plus a §F reconciliation. No blockers; nine non-blocking advisories listed below for polish.

All cross-document references resolve. All cited commit hashes appear in the worktree's git log. All Y₃ design-doc section references (§1, §4, §8, §9, §10 row 1) are present in the design doc on disk. The disposition memo's path-letter enumeration (β / γ / δ / ε / ζ) matches the CORRECTIONS-block enumeration byte-exact. No blocking style or hygiene defects found.

---

## Blockers

*(none)*

---

## Non-blocking advisories

1. **§F task-count double-classification of `Task 11.O-scope-update`** (lines 2011 and 2014).
   §F lists `Task 11.O-scope-update` as a "**+5 new task**" in the first bullet, but the next bullet acknowledges "**0 modified tasks at the body level besides Task 11.O**." Both statements are true under different framings (new task ID with a MODIFY-target-body deliverable), but they read as mildly contradictory at first pass. *Suggested polish:* split the bullet to distinguish "**+4 new task IDs with new bodies**" (OECD-probe, BR-bcb-fetcher, 11.N.2d-rev, 11.N.2d.1-reframe) from "**+1 new task ID with MODIFY-target deliverable**" (11.O-scope-update). The arithmetic to `63 + 5 = 68` is unaffected.

2. **§B Task 11.N.2.OECD-probe GO threshold sentence** (line 1839).
   The sentence "GO if OECD-direct CO cutoff is ≥ 2026-01-01 (i.e., recovers CO from 9-month-stale to ≤ 4-month-stale)" — the parenthetical "9-month-stale" is computed against the trigger paragraph's ~April-2026 date, but the math `(2026-04 minus 2025-07) = 9 months` and the implied target `(2026-04 minus 2026-01) = ~4 months` is not stated explicitly. *Suggested polish:* add ", relative to the 2026-04-25 authoring date" once at the §A table to anchor staleness arithmetic for the entire block.

3. **§A row "Y₃ `source_methodology` tag for the Rev-5.3.2 panel"** (line 1823).
   The cell text is unusually long for the table (~3 lines) and breaks visual scan rhythm. The other table rows fit roughly 1–2 lines. *Suggested polish:* hoist the parenthetical "(e.g., a `y3_v2_*` family describing 'EU=Eurostat / BR=BCB / CO=IMF / KE=fallback'; the literal string is finalized at implementation; the schema is described, not the literal)" into a footnote reference (e.g., "see footnote a" with a footnote at the end of §A) — the inline parenthetical is the longest single cell in the table.

4. **§B Task 11.N.2d-rev acceptance-criteria self-aware-arithmetic clause** (line 1886).
   The "(target: cutoff is bounded by whichever country has the latest CPI cutoff; with BR upgraded to BCB SGS at ≥ 2026-02-01 and EU at 2025-12-01 and CO held on IMF IFS at 2025-07-01, the panel cutoff is bounded by min-of-three ≈ 2025-07-01 → 2025-08-22 weekly anchor; window 2023-08-01 → 2025-08 ≈ 105 weeks pre-aggregation; SOURCE-DEPENDENT — Technical Writer reviewer should sanity-check this arithmetic at execution time and challenge if the actual landed count diverges)" is methodologically valuable but is a 100+ word parenthetical embedded in an acceptance-criterion bullet. *Suggested polish:* hoist this into a separate unbulleted sub-paragraph below the bulleted acceptance criteria, labeled as "Arithmetic note (informational; sanity-check at execution time)." The TW reviewer call-out within the acceptance criterion creates a secondary surface area for confusion (a reader could read the meta-instruction as a checkbox to be discharged at acceptance time, rather than at execution time as the parenthetical actually intends).

5. **§B Task 11.N.2d-rev acceptance-criteria fifth bullet** (line 1890): "All prior tests under `contracts/scripts/tests/inequality/` remain green; `pytest contracts/scripts/tests/` exits 0."
   Both clauses are true and operationally identical to the Rev-5.3.1 precedent's "PM-N4" guard, but Rev-5.3.1 names the guard explicitly ("`pytest contracts/scripts/tests/` exits 0 at commit boundary"). *Suggested polish:* append "(PM-N4 commit-boundary guard)" for symmetric named-rule cross-reference with the precedent.

6. **§C "imputation discussion" four-condition list duplication with §B Task 11.N.2d.2-NEW** (lines 1940–1944 vs. 1976).
   The four conditions for any future imputation revision are stated twice — once in §B Task 11.N.2d.2-NEW and once in §C. The lists are byte-identical in semantics (literature citation / sha256 anchor / sensitivity comparison / 3-way review). *Suggested polish:* either (a) make §C the canonical authoritative location and have §B Task 11.N.2d.2-NEW reference back to §C ("Four conditions enumerated in §C"); or (b) make §B canonical and have §C reference back. The duplication creates a future-maintenance hazard if a Rev-5.3.3 author updates one location but forgets the other.

7. **§E Reviewer-charter cross-references** (lines 1999–2001).
   §E lists CR / RC / TW review charters embedded inline within prose (e.g., "**Code Reviewer:** Verify (a) ... (b) ... (c) ..."). Each charter is a multi-clause list; readability would improve with a sub-bulleted layout per reviewer rather than inline (a)/(b)/(c) parenthetical numbering. *Suggested polish:* convert each charter's enumerated clauses to a sub-bullet list under a sub-heading (e.g., "**Code Reviewer charter:**" then a sub-bulleted list of five items). Non-blocking — the inline form is readable and matches Rev-5.3.1 precedent style.

8. **§G "Reference paths" — heterogeneous reference-form** (lines 2022–2030).
   §G mixes six reference types: file paths (with absolute repo-relative form `contracts/...`), commit hashes (truncated 7-char form), commit hash + parenthetical descriptor, and named constants (`MDES_FORMULATION_HASH`). The list is functional but inconsistent: e.g., "Y₃ design doc (immutable; preserved byte-exact): `...md` (commit `23560d31b`)" has the commit hash in parens; whereas "Last clean commit before Rev-5.3.2 dispatch: `765b5e203` (Task 11.N.2d primary panel landing)" has the commit-hash-first form. *Suggested polish:* standardize to "**Item type — full path/hash — descriptor**" pattern for all eight rows. Non-blocking — references resolve correctly as written.

9. **§A row "BR (Brazil) WC-CPI source"** (line 1819).
   The cell mentions "cumulative-index materialization required to satisfy the level-series contract `fetch_country_wc_cpi_components` consumes" — this is the only place in the CORRECTIONS block that names a Python function symbol (`fetch_country_wc_cpi_components`) by its source-code-level identifier, in plain prose without backticks-as-code framing. The Rev-5.3.1 precedent uses backticked source-code identifiers similarly (e.g., `compute_basket_calibration()`, `MDES_SD: Final[float] = 0.40`). This is consistent with precedent and not a code-violation per the "name + value" rule, but two small things:
   - the function name is referenced again in §B Task 11.N.2.BR-bcb-fetcher line 1864 as a "consumer contract" — fine;
   - the function name is referenced a third time in disposition-memo discussion in §A line 1819 — fine.
   *Suggested polish:* none required, but if a stylistic tightening pass is welcome, the §A cell could end with "..., per the level-series contract consumed by the BR `fetch_country_wc_cpi_components` dispatch" — slightly tighter and matches the §B framing.

---

## Style-alignment check (Rev-5.3.1 vs. Rev-5.3.2)

| Lens | Rev-5.3.1 (precedent) | Rev-5.3.2 (under review) | Match? |
|---|---|---|---|
| **Heading style** | Inline bold-paragraph title (`**CORRECTIONS-Rev-2 block (Rev-5.3.1, ...)**`) at L1028 | `## CORRECTIONS — Rev-5.3.2 ...` top-level heading at L1792 | **DIVERGENT but defensible** — Rev-5.3.2's payload (~240 lines, 6 new task bodies, 6 sections A–G) is roughly 8× the Rev-5.3.1 payload (~6 lines, single dense paragraph); the heading-level upgrade reflects scope, not stylistic drift |
| **Section labelling** | Single dense paragraph, no sub-sections | Letter-labeled sub-sections A / B / C / D / E / F / G | **DIVERGENT but defensible** — same scope-driven justification |
| **Table conventions** | No tables (single paragraph) | Two markdown tables (§A 18-row anchor table; §D 4-row data manifest) | **NEW but well-formed** — tables use 3-column / 4-column structure; alignment is uniform; bold cell-headers used for status (PRESERVED / UPDATED / NEW); precedent-consistent |
| **Cross-reference resolvability** | All cited paths and hashes resolve in worktree | All cited paths (disposition memo, Y₃ design doc, X_d design doc, calibration memo) resolve; all cited commits (`7afcd2ad6`, `cefec08a7`, `765b5e203`, `13cfe5f56`, `23560d31b`) appear in `git log` | **MATCH** |
| **Code-cleanliness in plan body** | Uses backticked named constants (`N_MIN`, `MDES_FORMULATION_HASH`) and function names (`required_power`); no fenced code blocks; no inline Python statements | Uses backticked named constants and function names; ZERO fenced code blocks; ZERO Python statements; ZERO SQL statements; one PEP-8-shaped literal `date(2026, 4, 24)` (acceptable as named-value, not as code) | **MATCH** |
| **Heading hierarchy hygiene** | n/a (single heading level) | `##` → `###` (§A through §G + "Why ζ" rationale) → `####` (Task 11.N.2.X bodies) — no skips, monotonic | **MATCH** |
| **Voice / tense / person** | Second person + present tense + active voice ("user reviewed", "user selected") | Second person + present tense + active voice ("Rev-5.3.2 deliberately does NOT pre-commit", "user has explicitly approved", "the orchestrator authored the disposition memo") | **MATCH** |
| **Anti-fishing-guard explicit framing** | One paragraph at the inline block end | Anti-fishing guard sub-bullet under each of the 5 new tasks (Task 11.N.2.OECD-probe, 11.N.2.BR-bcb-fetcher, 11.N.2d-rev, 11.O-scope-update); §F task-count, §E reviewer charter, §C four-condition-list all reinforce | **STRONGER — defensible upgrade given expanded payload** |

---

## Verification trail

Files read in full:
- `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` lines 1789–2030 (Rev-5.3.2 CORRECTIONS block)
- `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` lines 1024–1092 (Rev-5.3.1 precedent + upstream Task 11.N.2c body)
- `contracts/.scratch/2026-04-25-y3-coverage-halt-disposition.md` (full file — disposition memo with path β / γ / δ / ε / ζ enumeration)
- `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` lines 163–187 (verifying §10 row 1, §11 references)

Files verified to exist on disk (resolvability check; not read in full):
- `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` (Y₃ design doc, immutable per Rev-5.3.2 §A)
- `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` (X_d design doc, §1–§8 headers verified)
- `contracts/.scratch/2026-04-25-carbon-basket-calibration-result-rev2.md` (Rev-5.3.1 N_MIN-relaxation rationale memo, cited in §G)

Commit hashes verified against `git log` of worktree `phase0-vb-mvp` branch:
- `7afcd2ad6` — `plan(abrigo): Rev-5.3.1 — N_MIN relaxation 80→75 (path α from pathological-HALT)` ✓
- `cefec08a7` — `halt(abrigo): Rev-5.3.1 Task 11.O — Y₃ × X_d coverage HALT disposition memo` ✓
- `765b5e203` — `feat(abrigo): Rev-5.3.1 Task 11.N.2d — Y₃ 4-country inequality-differential dataset` ✓
- `13cfe5f56` — `halt(abrigo): Rev-5.3 Task 11.N.2c — pathological-HALT (basket-aggregate 77 non-zero weeks < N_MIN=80)` ✓ (referenced in upstream Rev-5.3.1 block, not Rev-5.3.2)
- `23560d31b` — `spec(abrigo): X_d + Y₃ design docs (brainstorm-converged, pre-plan-fold)` ✓

Cross-checked claims:
- Rev-5.3.1 active task count `63` (per upstream §F-equivalent reconciliation block at the line 1028 anchor) → matches Rev-5.3.2 §F starting figure ✓
- Disposition memo path-letter enumeration `β / γ / δ / ε / ζ` (memo §3) → matches Rev-5.3.2 §"Why ζ over the alternatives" enumeration ✓
- `MDES_FORMULATION_HASH` value `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` → matches the upstream Task 11.N.2c MDES-pin block at line 1036 ✓
- Rev-4 `decision_hash` value `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` → matches upstream usage at lines 1068, 1088 ✓

---

**Reviewer note**: This review covers TW lane only. CR is reviewing anti-fishing invariant preservation + dependency DAG + STRICT-TDD acceptance criteria; RC is reviewing coverage arithmetic + cutoff-date reproducibility + N≥75 feasibility math. None of the advisories above conflict with what CR/RC may surface independently.
