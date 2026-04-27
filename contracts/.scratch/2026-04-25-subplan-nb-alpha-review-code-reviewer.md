# Code Reviewer pass — Task 11.O.NB-α sub-plan (Rev-2 notebook migration)

**Reviewer.** Code Reviewer agent (CR) under `feedback_three_way_review` for spec/sub-plan authoring.
**Document under review.** `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` (408 lines, uncommitted).
**TW prior pass.** Agent `a19a98dfaa494c38e` (Technical Writer) — read-only context.
**Date.** 2026-04-26.
**Tool budget.** 9 / 15 used.

---

## Verdict

**NEEDS-WORK** — One BLOCKING anti-fishing-relevant defect (cited gate-verdict numbers and panel `n` are inconsistent with the actual published `gate_verdict.json` and Phase 5a manifest, in five places). One non-blocking trio-checkpoint discipline ambiguity. Otherwise the sub-plan is well-structured and the lens items 1, 3, 4, 5, 6, 7, 8, 9, 10 are PASS or PASS-w-advisory.

The blocking defect is high-severity because it sits inside acceptance gates that the post-deliverable 3-way review will use to decide PASS vs BLOCK. If the cited values are not corrected, the executing agent will either (a) hard-fail acceptance criteria A2/A3 by reproducing the actual published numbers (and the sub-plan's own acceptance criteria will reject the deliverable), or (b) drift the analysis to match the sub-plan's wrong numbers (anti-fishing violation). Both outcomes are worse than the small editorial fix-up cost to correct now.

---

## Lens-by-lens findings

### Lens 1 — Sub-plan structure consistency (PASS)

The standard sub-plan sections are all present and well-organized:

- Trigger (lines 11-19)
- Pre-commitment (lines 23-39, 8 numbered binding items)
- Sub-task list (lines 43-276, 24 numbered entries across 4 blocks)
- Dispatch ordering (lines 280-291)
- Acceptance criteria (lines 295-307, 9 enumerated)
- Reviewers (lines 311-316)
- Reference paths (lines 320-388)
- Budget and scope (lines 392-397)
- Cross-references (lines 401-408)

The structure mirrors prior accepted sub-plans (e.g., 2026-04-25-task110-rev2 spec) and reads cleanly.

### Lens 2 — 24 sub-tasks properly enumerated (PASS)

Block counts confirm: A=7 (sub-tasks 1-7) + B=8 (sub-tasks 8-15) + C=8 (sub-tasks 16-23) + D=1 (sub-task 24) = 24. Numbering is sequential and correctly matches the lens's expected `7 + 8 + 8 + 1 = 24` decomposition. Section ordering inside each notebook (§0 → §1 → … → §7) tracks the FX-vol-CPI Colombia precedent.

### Lens 3 — Trio-checkpoint discipline preserved (PASS-w-advisory)

Pre-commitment 1 (lines 25) carries the NON-NEGOTIABLE discipline language and explicitly cites `feedback_notebook_trio_checkpoint`. Most sub-tasks tag `Analytics Reporter / 1 trio` cleanly.

**Advisory (non-blocking).** Three sub-tasks describe themselves as multi-trio dispatches:

- Sub-task 2 (NB1 §1, "1-2 trios")
- Sub-task 9 (NB2 §1, "1-2 trios")
- Sub-task 17 (NB3 §1, "7 trios")

Sub-tasks 2 and 9 are unambiguous because they explicitly state "user gates the second trio." But sub-task 17 (the seven-test specification block) describes itself as "7 trios sequential, user gates each" inside a single sub-task entry, which slightly weakens the dispatch atomicity. The `feedback_notebook_trio_checkpoint` rule is technically still satisfied because each trio is a separate Analytics Reporter dispatch and the user gates each — but a Reality-Checker-style audit could read sub-task 17 as a license to dispatch all 7 trios in one bulk authoring session. **Suggestion** (not required): split sub-task 17 into seven sub-tasks 17.1 through 17.7, one per specification test, to remove all ambiguity. Alternatively, retain the current structure but add an explicit note inside sub-task 17 reading "Each of the 7 trios is a SEPARATE Analytics Reporter dispatch; the agent HALTs after each trio for user review per `feedback_notebook_trio_checkpoint`; bulk-author across multiple trios in one dispatch is FORBIDDEN."

This is non-blocking because the underlying rule is restated in the pre-commitment block, and a reasonable orchestrator-agent will dispatch trio-by-trio. But locking the wording at the sub-task level removes a non-trivial misreading risk during execution.

### Lens 4 — Citation block discipline preserved (PASS)

Pre-commitment 2 (line 27) carries the NON-NEGOTIABLE 4-part citation block discipline citing `feedback_notebook_citation_block`. The four parts are correctly enumerated (reference / why used / relevance to results / connection to product). The `references.bib` already copied from FX-vol-CPI Colombia is correctly designated as the citation-source-of-truth with additions-only discipline.

Each analytical sub-task (1, 2, 3, 4, 5, 6, 7, 9-15, 17-23) inserts a `Citation block cites …` clause naming specific references. Header-only sub-tasks (1 §0, 8 §0, 16 §0) legitimately omit citation blocks per the FX-vol-CPI Colombia precedent. Acceptance A5 (line 303) explicitly verifies citation-block coverage at post-notebook 3-way review with "missing or generic citation blocks are a BLOCKING defect" wording. Discipline is enforced.

### Lens 5 — Convex-payoff caveat at NB3 §5 verbatim with cross-reference to Rev-3 ζ-α (PASS)

Sub-task 21 (lines 242-248) explicitly requires NB3 §5 to reproduce Rev-2 spec §11.A "VERBATIM (byte-exact prose lift, with quote markers)" and adds an explicit cross-reference to Task 11.O.ζ-α (Rev-3 ζ-group). The acceptance line ("§11.A prose is byte-exact against `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`; cross-reference to Rev-3 ζ-group is unambiguous; product-load-bearing claim is preserved") is the right gate.

I verified the source spec §11.A exists at `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` line 507 with substantive convex-payoff insufficiency content (lines 484-541 of that spec); the reproduction is feasible and the reference path resolves.

Acceptance A6 (line 304) restates the requirement at the deliverable level. Pre-commitment 5 (lines 33) reinforces it. Triple-anchored, well-protected.

### Lens 6 — Mento-native ONLY scope preserved (PASS)

Pre-commitment 6 (line 35) explicitly cites `project_abrigo_mento_native_only` and Rev-5.3.3 pre-commitment 6, identifies the X_d address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` as Mento-native cCOP, and clarifies that the cCOP-vs-COPM provenance audit (Task 11.P.MR-β.1) is a separate sub-plan and does NOT block this Rev-2 re-presentation. Scope discipline preserved.

### Lens 7 — Anti-fishing invariants (BLOCK)

Pre-commitment 3 (line 29) states the byte-exact-reproduction rule against the published 14-row matrix. The rule itself is correctly stated. **However, the sub-plan body cites specific gate-verdict numbers that are inconsistent with the actual published `gate_verdict.json`.** This is the blocking defect.

The sub-plan repeatedly cites:

- Trigger (line 13): `β̂_X_d = −1.13e−4`, 90% CI `[−1.18e−3, +9.51e−4]`.
- Sub-task 1 (line 59): "n=86 weeks for the primary panel" and window `[2023-08-01, 2026-04-24]`.
- Sub-task 9 (line 131): "reproduction of `β̂_X_d = −1.13e−4`, 90% CI `[−1.18e−3, +9.51e−4]` byte-exact"; "n=86".
- Sub-task 23 (line 260): "gate=FAIL, β̂=−1.13e−4, 90% CI `[−1.18e−3, +9.51e−4]`, n=86".
- Acceptance A2/A3 (lines 300-301): mention "byte-exact" reproduction targets without restating the values, but the values they reference upstream are wrong.

The actual published `gate_verdict.json` (verified at both `notebooks/abrigo_y3_x_d/estimates/gate_verdict.json` and `contracts/.scratch/2026-04-25-task110-rev2-analysis/gate_verdict.json` — byte-identical) reads:

- `row_1_beta_hat = −2.7987050503705652e−08`
- `row_1_lower_90 = −4.6206859818053154e−08`
- `row_1_se = 1.4234226026833985e−08`
- `row_1_n = 76`
- `gate_verdict = "FAIL"` (matches sub-plan)
- `t1_rejects = true`, `t3a_rejects = true`, `t3b_passes = false`, `t6_break_rejects = false` (these spec-test fields are not summarized in the sub-plan but available for NB3 §1 trios)

Cross-checking with `contracts/.scratch/2026-04-25-task110-rev2-data/manifest.md`:

- Row 1 primary panel: `n_rows = 76`, window `2024-09-27 → 2026-03-13` (NOT `2023-08-01 → 2026-04-24` as cited).
- All 14 rows have `n=76` at construction time (rows 5/13 drop to n=75 after Δ-transform at fit time).

**Severity:** BLOCK. The sub-plan's own pre-commitment 3 says "Any drift (rounding, library version skew, seed mismatch) is a BLOCKING defect; the post-notebook 3-way review will reject the deliverable." The sub-plan is asking the executing agent to "reproduce byte-exact" against numbers that DO NOT MATCH the actual published verdict. The agent will either hard-fail acceptance (correctly producing −2.7987e−8, n=76, and getting BLOCKED by the sub-plan's own stated targets), or drift the run to match the sub-plan's wrong −1.13e−4, n=86 numbers (which would be an anti-fishing violation that pre-commitment 3 is supposed to prevent).

**Required fix.** Before this sub-plan converges 3-way review, replace every occurrence of:

- `−1.13e−4` → `−2.7987e−8` (or the full `−2.7987050503705652e−08` per `gate_verdict.json`)
- `[−1.18e−3, +9.51e−4]` → `[−4.6207e−8, …]` (the JSON does not record `row_1_upper_90` directly; either compute as `β̂ + 1.645·SE = −2.7987e−8 + 1.645·1.4234e−8 ≈ −4.566e−9` and pin that, or reference the exact row/column source in the published `sensitivity.md`/`estimates.md` and quote that as the canonical value)
- `n = 86` → `n = 76`
- window `[2023-08-01, 2026-04-24]` → `[2024-09-27, 2026-03-13]`

Locations to fix: line 13 (Trigger), line 59 (sub-task 1), line 131 (sub-task 9), line 260 (sub-task 23). Acceptance A2/A3 (lines 300-301) do not cite specific values but the upstream targets they refer to must be corrected.

**Possible alternative explanation worth user verification.** It is possible the `−1.13e−4` numbers in the sub-plan trace to an older Phase 5b run that has since been superseded, OR they trace to a different scale convention (e.g., normalized X_d basis units vs raw USD basis units). If the sub-plan's cited `−1.13e−4` value is in fact the published value in some unit system that differs from `gate_verdict.json`'s raw `e−08` units, then this is not a number error — it is a missing units-disclosure that the sub-plan must spell out. Either way, the sub-plan as currently authored cites numbers that are inconsistent with the canonical JSON file under "byte-exact" reproduction language, and that inconsistency must be resolved before execution.

The Reality Checker pass should specifically verify whether the `−1.13e−4` figure traces to an older draft of the Phase 5b deliverable that has been overwritten, or whether it comes from a units-normalized presentation that the sub-plan failed to disclose. Either resolution requires sub-plan edits before this PASS.

### Lens 8 — Cross-references resolve (PASS)

I verified the following anchors resolve correctly:

- Major-plan Task 11.O.NB-α anchor at `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` lines 2170-2188 → confirmed (super-task body at line 2170 onward, with sub-plan pointer to this exact filename at the right place).
- Spec `d9e7ed4c8` is not directly referenced by hash in the sub-plan body, but `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` is the spec-A path referenced (line 326) and that file exists.
- Phase 5a artifacts (line 329-334): `contracts/.scratch/2026-04-25-task110-rev2-data/` with all 14 panel parquets, `manifest.md`, `data_dictionary.md`, `validation.md`, `_audit_summary.json` — confirmed all present.
- Phase 5b artifacts (line 337-341): `contracts/.scratch/2026-04-25-task110-rev2-analysis/` with `estimates.md`, `spec_tests.md`, `sensitivity.md`, `summary.md`, `gate_verdict.json` — confirmed all present.
- FX-vol-CPI Colombia precedent (line 350-357): all 7 paths confirmed at `contracts/notebooks/fx_vol_cpi_surprise/Colombia/`.
- Scaffolding stub (line 359-365): `notebooks/abrigo_y3_x_d/env.py`, `references.bib`, `_nbconvert_template/`, `estimates/gate_verdict.json`, `figures/`, `pdf/` — confirmed present.

All paths resolve. The cross-reference web is sound.

### Lens 9 — Code-agnostic body (PASS)

100% prose with backticked names, paths, hashes, mathematical expressions in inline math notation (`Y₃ = α + β · X_d + γ' · controls + ε`), and citation references. No Python code blocks, no SQL fenced blocks, no shell commands. Pre-commitment 7 (line 37) and Budget item 4 (line 397) explicitly assert code-agnostic discipline and the body delivers on it. Compliant with `feedback_no_code_in_specs_or_plans`.

### Lens 10 — `env.py` path-depth fix correctly out-of-scope (PASS)

The sub-plan correctly identifies `env.py` `parents[3] → parents[2]` adjustment as a separate Senior Developer scaffolding-fix dispatch, not work performed under this sub-plan. The discipline is consistent across four anchors:

- Trigger (line 17): "depth adjustment pending"
- Acceptance A7 (line 305): "Senior Developer dispatch under the existing scaffolding-fix line of the major plan, NOT under this sub-plan"
- Reference paths (line 360): "Senior Developer dispatch under separate scaffolding-fix line"
- Budget and scope (line 396): "Sub-plan execution will adjust `env.py` depth via Senior Developer dispatch under a separate line; this document does not perform that adjustment"

The file scope under the sub-plan authoring line is correctly bounded to creating ONLY `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md`, with no modifications to scaffolding under `notebooks/abrigo_y3_x_d/`. Compliant with `feedback_agent_scope`.

---

## Summary of required actions

**BLOCKING (must fix before sub-plan converges 3-way review):**

1. **Reconcile cited gate-verdict numbers with `gate_verdict.json`** in five locations (line 13 Trigger, line 59 sub-task 1, line 131 sub-task 9, line 260 sub-task 23, acceptance gates A2/A3). The JSON canonical source is `−2.7987e−8` / lower-90 `−4.6207e−8` / `n=76` / window `[2024-09-27, 2026-03-13]`. If the sub-plan's `−1.13e−4` / `n=86` numbers come from a different units convention or a superseded draft, that fact must be disclosed in the sub-plan or the numbers must be corrected. This is the most important fix — without it the executing agent will either hard-FAIL acceptance or drift toward an anti-fishing violation.

**NON-BLOCKING ADVISORIES:**

2. **Disambiguate sub-task 17's "7 trios" framing.** Either split into 17.1-17.7 (one per spec test), or insert an explicit one-sentence note that each of the 7 trios is a SEPARATE Analytics Reporter dispatch with HALT-for-user-review between trios, no bulk authoring. Removes a misreading risk during execution.

**OK as-is:**

3. Sub-plan structure, sub-task count (24), citation-block discipline, convex-payoff caveat verbatim preservation, Mento-native scope, code-agnostic body, env.py-out-of-scope discipline, cross-reference resolution.

---

## Recommendation to orchestrator

After the BLOCKING fix in item 1 (reconcile cited gate-verdict numbers), the sub-plan will convert from NEEDS-WORK to PASS for the CR lens. The fix-up is a small editorial pass (~5 line edits) that does not require sub-plan re-architecture.

The Reality Checker pass (sibling review under `feedback_three_way_review`) should be asked to specifically verify the unit-convention question: are `−1.13e−4` / `n=86` traceable to any artifact in the published Rev-5.3.2 deliverable, or are they entirely spurious? The Reality Checker has the right tooling lens for this verification (cross-checking against `estimates.md` / `sensitivity.md` line-by-line).

The Technical Writer pass (already complete by agent `a19a98dfaa494c38e`) can be asked to confirm prose-level consistency between the corrected numbers and any narrative descriptions of the Rev-2 result that may need parallel edits (e.g., the "FAIL" headline framing is unchanged, but any prose about effect-size magnitude needs a coherency check at the new `e−08` scale).

---

## Files referenced

- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` (under review)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (major-plan anchor verified at lines 2170-2188)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (Rev-2 spec; §11.A convex-payoff caveat at line 507)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-analysis/gate_verdict.json` (canonical published gate verdict; n=76, β̂=−2.7987e−8)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/abrigo_y3_x_d/estimates/gate_verdict.json` (byte-identical copy)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/manifest.md` (panel manifest; primary n=76, window 2024-09-27 → 2026-03-13)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/fx_vol_cpi_surprise/Colombia/` (binding 3-notebook precedent)

---

**End of CR pass.** Verdict: **NEEDS-WORK** (one BLOCKING numerical-reconciliation defect; one non-blocking trio-discipline advisory; eight lens items PASS).
