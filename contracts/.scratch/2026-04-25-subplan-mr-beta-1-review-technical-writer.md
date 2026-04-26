# Technical Writer Peer Review — MR-β.1 Sub-plan (Task 11.P.MR-β.1)

**Reviewer:** Technical Writer (peer review pass)
**Review date:** 2026-04-26
**Sub-plan under review:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (233 lines, uncommitted)
**Authoring agent:** `adf6407b053051a5c`
**Verdict:** **PASS-w-non-blocking-advisories**

---

## Verdict summary

The sub-plan is structurally sound, code-agnostic, internally consistent, and reviewer-actionable. The Rev-5.3.4 RESCOPE vs. Rev-5.3.3 framing distinction is explicit and load-bearing. The five sub-tasks are sequentially dispatchable without re-derivation of scope. The BLOCKING relation to Task 11.P.spec-β is unambiguous (cited in §D.8 and §F's sibling-sub-plan list). The CORRECTIONS-block precedent from the major plan is honored at §E (post-trio CORRECTIONS-block escalation path).

I record **6 non-blocking advisories** below. None block the spec-review trio convergence; all are stylistic, citation-completeness, or minor consistency notes that the author may choose to fold into a single Rev-5.3.4-r1 minor-edit pass before sub-task dispatch, or defer to sub-task-level notes.

---

## Standard TW lens — line-item verification

### 1. Style consistency with the major plan's CORRECTIONS-block precedent — PASS

§E ("Reviewers") explicitly cites the Rev-5.3.x CORRECTIONS-block pattern for the divergence escalation path: *"If the trio diverges, a CORRECTIONS block is appended to this sub-plan (analogous to the major-plan Rev-5.3.x CORRECTIONS pattern) before sub-task dispatch."* (line 187). This matches the major-plan precedent and is the correct format-borrow.

### 2. Heading hierarchy monotonic — PASS

H1 = title (line 1); H2 = §A through §G (lines 13, 32, 46, 164, 179, 193, 219); H3 = sub-task headers under §C (lines 50, 73, 101, 123, 143). No skipped levels; no sibling-conflict; renderer-stable.

### 3. Section labelling internally consistent — PASS

Lettered sections A–G; sub-tasks numbered 1–5 within §C. Consistent throughout. The "Sub-task N" prefix is used uniformly in §D's acceptance enumeration (lines 168–172) and in the sub-task headers themselves.

### 4. Cross-references resolve — PASS-w-advisory-A1

- Major-plan path `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` — cited at lines 7 and 195; consistent.
- TR research file `contracts/.scratch/2026-04-25-mento-userbase-research.md` — cited at lines 28, 125, 132, 171, 196; consistent.
- Sibling sub-plan paths — cited at lines 212–215; format consistent with §F's other path citations.
- Project-memory anchors — all six load-bearing memory files cited by their canonical filename per `feedback_notebook_citation_block`'s spirit (cite-by-filename for project memory).
- Commit hashes — `799cbc280` (Rev-5.3.2 baseline, line 209), `6b1200dcb`, `f38f1aad3` (4-reviewer-gate close-out, line 210). Hashes are appropriate-length (9 hex chars, full-resolvable in this repo).
- Sha256 hashes — `decision_hash` and `MDES_FORMULATION_HASH` cited at line 36 with full 64-char strings; consistent with `project_mdes_formulation_pin` precedent.

**Advisory A1 (non-blocking).** The Rev-5.3.4 CORRIGENDUM block in the major plan is cited (lines 7, 17, 195) but not pinned to a major-plan line range or section anchor. A reviewer following the cross-reference must scan the Rev-5.3.3 CORRECTIONS area to find the Rev-5.3.4 CORRIGENDUM. Optional improvement: cite the major-plan section anchor (e.g., "§ Rev-5.3.4 CORRIGENDUM, immediately following the Rev-5.3.3 CORRECTIONS block") explicitly. Current phrasing at line 17 ("immediately following the Rev-5.3.3 CORRECTIONS block") partially does this; tighter would be a line-number range. Non-blocking because the Rev-5.3.x CORRECTIONS pattern is well-established and reviewers can locate the block by convention.

### 5. Code-agnostic body — PASS

Editorial scope at line 9 is explicit: *"code-agnostic; no Python or SQL bodies; backticked addresses, paths, table names, and source-citation hashes are permitted."* Verified line-by-line: all backticked tokens are addresses, file paths, table/column names, project-memory filenames, ticker symbols, sha256 hashes, or commit hashes. No Python expressions, SQL statements, or Solidity fragments. Compliant with `feedback_no_code_in_specs_or_plans`.

### 6. Internal consistency — PASS-w-advisory-A2

- Sub-task IDs (1–5): consistent in §C headers, §D acceptance (lines 168–172), and §E review-trio assignments.
- Deliverable paths: each sub-task's deliverable path is cited once in the sub-task body and once in §D acceptance. Cross-checked:
  - Sub-task 1: `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` (line 52, line 168) — match.
  - Sub-task 2: `contracts/.scratch/2026-04-25-duckdb-address-audit.md` (line 75, line 169) — match.
  - Sub-task 3: `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` (line 103, line 170, line 131) — match across three citations.
  - Sub-task 4: `contracts/.scratch/2026-04-25-mento-userbase-research.md` (line 125, line 171) — match (corrigendum target).
  - Sub-task 5: `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md` (line 145, line 172) — match.
- Dependency chain: Sub-task 1 → 2 → 3 → 4 → 5; sequential; documented at lines 71, 99, 121, 141, 160. Consistent.
- Subagent assignments: Data Engineer (sub-tasks 1–4), Technical Writer (sub-task 5). Documented at lines 67, 95, 117, 137, 156. Internally consistent; rationale is given at line 156 (TW for process-discipline content).

**Advisory A2 (non-blocking).** Sub-task 3's subagent assignment at line 117 is stated as "Data Engineer authors the registry doc body; Technical Writer is OPTIONALLY consulted for clarity/structure pass before the spec-review trio." The optionality is a soft assignment that may create ambiguity at dispatch time (does the orchestrator dispatch TW or not?). Optional improvement: state the optionality decision criterion explicitly — e.g., "TW is consulted IF the registry-doc draft exceeds N pages OR contains mixed-tier content" — or remove the optionality entirely. Non-blocking because the field-operator (orchestrator) can adjudicate at dispatch time and the sub-plan's three-way-review-trio convergence does not depend on this resolution.

### 7. Citation discipline per `feedback_notebook_citation_block` — N/A-but-PASS-by-spirit

The feedback rule applies to estimation/sensitivity *notebooks*; this is a sub-plan, not a notebook, so the rule's strict 4-part-markdown-block format does not apply. By spirit, the sub-plan cites every load-bearing project-memory anchor by its canonical filename (lines 198–208) and cross-references each rule (`feedback_three_way_review`, `feedback_implementation_review_agents`, `feedback_specialized_agents_per_task`, `feedback_no_code_in_specs_or_plans`, `feedback_pathological_halt_anti_fishing_checkpoint`) at the point where the rule is load-bearing. Compliant by spirit.

---

## Specific checks (user-requested)

### Check 1 — Rescoped Rev-5.3.4 vs. Rev-5.3.3 framing distinction — PASS

The two framings are quoted verbatim and labeled at lines 19 and 21:

- Line 19: *"Original framing (Rev-5.3.3, now superseded). 'Correct the project memory naming error and update DuckDB schema docs to reflect that onchain_copm_transfers tracks Mento-native cCOP.'"*
- Line 21: *"Rescoped framing (Rev-5.3.4, authoritative). 'Formally lock the on-chain address registry for the Mento-native basket … with a single canonical reference document, and append a corrigendum to the Trend Researcher report …'"*

Pre-commitment §B.6 (line 41) reinforces the supersession: *"Wherever a Rev-5.3.3 phrase implies a project-memory naming error needs correction, treat that phrase as superseded — the memory was correct; the agent's brief Rev-5.3.3 attribution flip was wrong; the user has already corrected it; the registry-lock is the rescoped deliverable."*

§D.7 (line 174) repeats the supersession at the acceptance level: *"Rev-5.3.4 RESCOPE honored — no sub-task output reverts to the Rev-5.3.3 framing of 'correct the project-memory naming error'; the registry-lock framing is the authoritative deliverable."*

Three-fold reinforcement (definition, pre-commitment invariant, acceptance criterion) is over-determined in the right direction. Distinction is unambiguous.

### Check 2 — Five sub-tasks sequentially dispatchable without scope re-derivation — PASS

Each sub-task carries a complete dispatch packet:

- **Deliverable** — what file lands where (explicit path).
- **Acceptance** — explicit falsifiable criteria.
- **Subagent** — named agent role with rule citation.
- **Reviewers** — named reviewer trio (or "None at sub-task level" with rationale).
- **Dependency** — explicit upstream sub-task or "None internal."

Verified for sub-tasks 1 (lines 50–71), 2 (73–99), 3 (101–121), 4 (123–141), 5 (143–160). Format is uniform; a downstream Data Engineer can dispatch sub-task 1 today without re-reading the major plan, and each subsequent sub-task's dependency note tells the orchestrator which deliverable must land before the next dispatch.

The acceptance bullets in sub-task 1 (line 65) and sub-task 2 (line 93) explicitly include the HALT-on-discrepancy escape hatch citing `feedback_pathological_halt_anti_fishing_checkpoint`, which makes the sub-task self-contained against discovery edge-cases.

### Check 3 — BLOCKING relation to Task 11.P.spec-β explicit and unambiguous — PASS

Two explicit citations:

- §D.8 (line 175): *"Downstream β-spec unblocking — Task 11.P.spec-β can now author a Mento-native-only retail-only hypothesis citing the registry spec doc as the on-chain-identity authority. The β-spec dependency on Task 11.P.MR-β.1 is satisfied."* (acceptance criterion explicitly ties β-spec unblocking to this sub-plan's completion).
- §F sibling-sub-plan list (line 214): *"`contracts/docs/superpowers/sub-plans/2026-04-25-beta-spec.md` (Task 11.P.spec-β; BLOCKED on this sub-plan's completion)"* (explicit BLOCKED marker; format-uniform with line 215's `Task 11.P.exec-β; BLOCKED on Task 11.P.spec-β convergence`).

The BLOCKED-on-this-sub-plan relation is stated in two places (acceptance + reference-paths sibling list). Unambiguous.

### Check 4 — Five TW pre-flight findings clearly flagged for reviewers — N/A-with-clarification

The user's question references "TW's 5 pre-flight findings." I do not see a numbered "5 pre-flight findings" block within the sub-plan body itself; the sub-plan §E (line 187) refers to the post-author trio review (CR + RC + TW) as the convening reviewers but does not enumerate pre-flight findings inside the sub-plan.

Two interpretations:

1. **The user means: did the sub-plan's authoring agent surface 5 pre-flight findings to the TW peer reviewer (this review)?** If so, those findings would have been transmitted out-of-band (in the dispatch envelope) rather than embedded in the sub-plan body. I do not have visibility into the dispatch envelope; this peer review treats the sub-plan body as the sole artifact under review.
2. **The user means: the sub-plan should clearly flag the load-bearing "anti-error" findings (e.g., the Rev-5.3.3 attribution flip, the consume-only invariants, the no-rename invariants) so a downstream reviewer reads them at the top.** Under this reading, the sub-plan **does** flag these prominently:
   - §A "Trigger" lines 13–28 — flags the inverted-attribution episode and the user correction.
   - §B "Pre-commitment" lines 32–42 — enumerates 7 invariants (numbered 1–7), each of which is a pre-flight finding the trio must verify.
   - §G "Out-of-scope reaffirmation" lines 219–233 — enumerates 9 explicit out-of-scope items.

If the user intended interpretation 2, the sub-plan **passes** — pre-flight findings are flagged prominently in §A, §B, and §G with monotonic numbering and explicit "do not silently revert" framing. If the user intended interpretation 1, the dispatch envelope sits outside this peer review's scope; I cannot adjudicate.

**Advisory A3 (non-blocking, clarification-pending).** The phrase "TW's 5 pre-flight findings" is not anchored in the sub-plan body. If the dispatch envelope contained 5 numbered pre-flight findings that were intended to be cross-referenced inside the sub-plan, the cross-reference is missing; if the 5 findings are to be inferred from §B's 7 pre-commitment invariants (a reader could plausibly identify the 5 most-load-bearing of the 7), the inference is left to the reviewer. Optional improvement: if there is a canonical "TW pre-flight findings" document upstream of this sub-plan, cross-reference it in §F. Non-blocking because the sub-plan's §B + §G already over-determine the anti-error scaffolding regardless of which interpretation is correct.

---

## Additional non-blocking advisories

### Advisory A4 — Sub-task 5's "≤ 2 pages" acceptance criterion is non-falsifiable in markdown

Line 154's acceptance bullet for sub-task 5 reads: *"is short (≤ 2 pages)."* Markdown documents do not have an intrinsic page concept; "page" is a render-target artifact. Optional improvement: replace with a falsifiable criterion (e.g., "≤ 100 lines" or "≤ 2,000 words"). Non-blocking because reviewers can adjudicate "short" by convention.

### Advisory A5 — §G "Out-of-scope" §G.6 Rev-5.3.2 14-row resolution-matrix citation lacks anchor

Line 229: *"Re-open the Rev-5.3.2 published estimates or the Rev-5.3.2 14-row resolution-matrix scope."* The 14-row resolution-matrix is a specific Rev-5.3.2 artifact; a reviewer reading this sub-plan cold may not know where to find the 14-row matrix. Optional improvement: cite the major-plan section or the Rev-5.3.2 spec-doc path where the 14-row matrix lives. Non-blocking because Rev-5.3.2 is well-established context for the trio reviewers; a fresh reviewer would query the major plan.

### Advisory A6 — Sub-task 3's "byte-exact-immutable post-converge" claim is strong; recommend softening or qualifying

Line 107 (header invariant): *"the registry is the source-of-truth post-converge; future address additions land as appendix sections, never as in-place edits to the existing entries."* Line 115 (acceptance): *"The doc is byte-exact-immutable post-converge; future address additions land as new appendix sections."*

The byte-exact-immutability claim is uncommon for a documentation artifact (typically reserved for published estimates and decision-hash-pinned deliverables). A future correction (e.g., a token's deployment-date provenance is found to be wrong, or a new Mento-native token is added to the basket) would in principle land as an appendix per the stated discipline, but a typo correction in an existing per-token section would conflict with byte-exact-immutability.

Optional improvement: distinguish between "byte-exact-immutable for the per-token canonical-address fields" (the load-bearing immutability is on the address-vs-ticker mapping) and "in-place-editable for typographical and provenance-citation refinements." Non-blocking because the §E + sub-task-3 acceptance trio review can adjudicate the immutability scope at convergence.

---

## Reviewer-actionable summary

**Verdict:** PASS-w-non-blocking-advisories.

The sub-plan is ready for the spec-review trio (CR + RC + TW). All load-bearing structural, citation-resolution, code-agnostic, and internal-consistency checks pass. The 6 non-blocking advisories (A1–A6) can be addressed in a Rev-5.3.4-r1 minor-edit pass at the author's discretion or deferred to sub-task-level execution notes.

The 4 user-requested specific checks are answered:

- Rescope distinction: clearly stated, three-fold reinforced, unambiguous.
- Sub-task sequentiality: complete dispatch packets per sub-task; no scope re-derivation needed.
- β-spec BLOCKING relation: explicit in §D.8 + §F sibling-list with BLOCKED marker.
- "TW's 5 pre-flight findings": ambiguous source (in-sub-plan §B's 7 invariants vs. dispatch-envelope upstream); under the in-sub-plan interpretation, prominently flagged; under the dispatch-envelope interpretation, out of this peer review's scope.

No BLOCK or NEEDS-WORK issue identified. Sub-plan can proceed to spec-review trio convergence.

---

## Reviewer signature

**Technical Writer (peer review)** — `2026-04-26`
Tool budget: 2 of ≤ 10 used (Read on the sub-plan, Write of this review).
Read-only review per dispatch instruction; sub-plan body unchanged.
