# CR Review — Sub-plan Task 11.P.MR-β.1 (cCOP-vs-COPM provenance audit + on-chain registry lock)

**Reviewer**: Code Reviewer
**Date**: 2026-04-25
**Scope**: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (233 lines, uncommitted)
**Trio context**: per `feedback_three_way_review` — CR + RC + TW (TW agent `adf6407b053051a5c`)
**Tool budget**: ≤ 15 (used 8)
**Read-only**: confirmed; sub-plan not modified

---

## Verdict

**PASS-w-non-blocking-advisories**

The sub-plan is structurally sound, scope-disciplined, code-agnostic, and properly anchored to the major plan's Rev-5.3.4 CORRIGENDUM. Anti-fishing invariants are explicit, the Rev-5.3.3-vs-Rev-5.3.4 framing-supersession is correctly captured (Pre-commitment §6), and reviewer assignments respect the implementation-vs-spec boundary per `feedback_implementation_review_agents`.

Three non-blocking advisories below — none gate dispatch, all surface as small-text refinements during sub-task execution.

---

## §1. Standard CR-lens findings (8 lenses)

### Lens 1 — Sub-plan structure consistency: **PASS**

Section discipline matches major-plan precedent: A. Trigger / B. Pre-commitment / C. Sub-tasks / D. Acceptance / E. Reviewers / F. References / G. Out-of-scope reaffirmation. The §G out-of-scope reaffirmation is a **strengthening** beyond the typical major-plan pattern and is welcome — it explicitly enumerates 9 forbidden moves and routes any discovered need to a HALT, fully aligned with `feedback_pathological_halt_anti_fishing_checkpoint`.

### Lens 2 — 5 sub-tasks properly enumerated: **PASS**

Each of sub-tasks 1–5 carries a deliverable / acceptance / subagent / reviewers / dependency tuple. Sub-task 3 correctly carries the trio review (CR + RC + SD); sub-tasks 1, 2, 4, 5 correctly identify themselves as intermediate or editorial-only artifacts that do not need their own reviewer trio (the registry doc carries the convergent quality signal). Dependency chain is acyclic and well-formed: 1 → 2 → 3 → 4 → 5.

### Lens 3 — Cross-references resolve: **PASS** (with one advisory; see §3 Advisory C)

Verified live:
- Major-plan anchor at `2026-04-20-remittance-surprise-implementation.md` lines 2168–2387 contains the Rev-5.3.3 super-task body for Task 11.P.MR-β.1 (line 2233) AND the Rev-5.3.4 CORRIGENDUM (line 2370+) including the formal RESCOPE statement at line 2383. **Both anchors resolve as cited.**
- TR research file `contracts/.scratch/2026-04-25-mento-userbase-research.md` exists (434 lines, 31KB). Finding 3 correctly identified as the override target (sub-plan §A line 15 + sub-task 4 line 130).
- Carbon-basket X_d design doc exists at the cited path; cross-reference to `proxy_kind` enumeration confirmed (sub-plan §C sub-task 2 lines 80–90).
- Project-memory anchors (`project_mento_canonical_naming_2026`, `project_abrigo_mento_native_only`, `project_carbon_user_arb_partition_rule`, `project_carbon_defi_attribution_celo`, `project_usdt_celo_canonical_address`) all exist on disk under `~/.claude/projects/.../memory/`. The address citation `0xc92e8fc2…` matches the canonical-naming memory file line 13 (`COPM (Minteo, unchanged) — 0xc92e8fc2947e32f2b574cca9f2f12097a71d5606`).
- Address `0xc92e8fc2…` text-matches between sub-plan §A (line 15), sub-plan §B invariant 3 (line 38), sub-task 2 deliverable (line 79), memory anchor (line 13), and the major-plan Rev-5.3.4 CORRIGENDUM (line 2383). **All five citations agree.**

### Lens 4 — Code-agnostic body: **PASS**

No Python, SQL, or Solidity blocks anywhere. Backticked addresses, table names, paths, and source-citation hashes are present and acceptable per `feedback_no_code_in_specs_or_plans`. Two `decision_hash` / `MDES_FORMULATION_HASH` sha256 strings appear in §B invariant 1 — these are reference hashes for invariant-pin purposes, not code. Acceptable.

### Lens 5 — Anti-fishing invariants preserved: **PASS**

Seven explicit pre-commitments in §B; every one is consistent with prior anti-fishing precedent:
- Invariant 1 (DuckDB consume-only + decision_hash + MDES_FORMULATION_HASH immutable) — matches `feedback_pathological_halt_anti_fishing_checkpoint` and `project_mdes_formulation_pin`.
- Invariant 4 (memory edits append-only or section-replace-with-corrigendum, with HALT-on-discovered-need) — correctly enforces the `feedback_three_way_review` discipline of "no silent rewrites".
- Invariant 6 (Rev-5.3.4 RESCOPE supersedes Rev-5.3.3 framing; outputs reverting to old framing fail acceptance) — sharp and falsifiable; this is the strongest single invariant in the sub-plan and directly addresses the user-correction trigger.
- Invariant 7 (TR research preserved with corrigendum, not deleted; Findings 1/2/4 audit-trail-preserved) — correctly distinguishes audit-trail value from override scope.

### Lens 6 — Memory-edit constraint: **PASS**

§A (line 28) is explicit: "This sub-plan therefore does NOT modify either of those memory files; it consumes them as authoritative inputs." §B invariant 4 reaffirms with HALT enforcement. §G out-of-scope (lines 223–224) lists the two memory files first. **The sub-plan correctly does NOT silently modify any project-memory file at authoring time** — TW pre-flight Finding 2 is satisfied.

### Lens 7 — Out-of-scope clarity: **PASS**

§G enumerates 9 forbidden moves explicitly, including the highest-risk ones: no analytical / notebook authoring, no spec-revision of upstream Rev-5.3.x specs, no DuckDB row mutation, no Solidity work, no β-spec hypothesis-decision pre-commitment. The "if discovered, HALTS to user" routing is appropriate.

### Lens 8 — Reviewer assignment correctness: **PASS** (with one micro-advisory; see §3 Advisory A)

- Sub-task 3 (registry spec doc, the implementation-adjacent corrigendum work): **CR + RC + Senior Developer** per `feedback_implementation_review_agents`. **Correct.** The justification on line 189 ("the registry doc is implementation-adjacent corrigendum work rather than spec-authoring of analytical content") is precise and aligned with the feedback memory.
- Sub-task 5 (future-research safeguard memo, editorial-only): no sub-task-level review; appropriately scope-bounded. Subagent = Technical Writer (correct: process-discipline content per `feedback_specialized_agents_per_task`).
- Sub-tasks 1, 2, 4: no sub-task-level review; correctly identified as intermediate/editorial-only artifacts whose quality signal flows through sub-task 3's trio review. **Acceptable.**

---

## §2. TW pre-flight finding evaluations

**TW Finding 1 — proxy_kind enumeration count, ticker convention mismatch (design-doc vs user-prompt vs live DuckDB)**

**Verdict: PASS — substantively well-handled.**

Cross-checked three sources:
- **Design doc** (`2026-04-24-carbon-basket-xd-design.md` line 56): enumerates extension keys as `carbon_basket_user_volume_usd`, `carbon_basket_arb_volume_usd`, and `carbon_per_currency_<COPM|cUSD|cEUR|cREAL|cKES|XOFm>_volume_usd` — **uses LEGACY tickers** (cUSD/cEUR/cREAL/cKES) for per-currency slugs.
- **Live-DuckDB memory** (`project_duckdb_xd_weekly_state_post_rev531`): "10 distinct `proxy_kind` values across ~80 Friday-anchored weeks" with "6 × `carbon_per_currency_<TICKER>_volume_usd` (legacy slugs cUSD/cEUR/cREAL/cKES/COPM/XOFm preserved)". **Live state uses legacy slugs.**
- **Sub-plan** (lines 80–90): enumerates 10 `proxy_kind` values, but uses **CANONICAL tickers** for per-currency slugs (`carbon_per_currency_copm_volume_usd`, `…_brlm_…`, `…_eurm_…`, `…_kesm_…`, `…_usdm_…`, `…_xofm_…`).

The **count agrees**: 2 basket + 6 per-currency + 2 supply-channel diagnostics (`b2b_to_b2c_net_flow_usd`, `net_primary_issuance_usd`) = 10. ✓

The **slug-vs-canonical-ticker mismatch is real but the sub-plan handles it correctly**:
- §C sub-task 2 acceptance criterion (line 91, lines 93) explicitly anticipates the asymmetry: *"Per `project_mento_canonical_naming_2026`, the slugs may follow legacy tickers (`carbon_per_currency_<LEGACY>_volume_usd`) for migration-disruption reasons; the audit documents the slug-vs-canonical-ticker mapping in the loader docstring without renaming."*
- §C sub-task 3 makes a **slug-vs-canonical-ticker mapping table** an explicit deliverable (line 111).

**However, the sub-plan's own enumeration in lines 85–90 uses canonical tickers, which is INCONSISTENT with the live DuckDB state.** This is a **substantive presentation defect** but it does NOT break the sub-task: sub-task 2 explicitly directs the auditor to *document* the slug-vs-canonical asymmetry, so the auditor will discover and reconcile during execution. **See §3 Advisory B** for the recommended (non-blocking) refinement.

**TW Finding 2 — Two memory files require NO edits at authoring time: PASS.** Confirmed under Lens 6 above. §A (line 28), §B invariant 4 (line 39), and §G out-of-scope §223–224 collectively make this airtight.

**TW Finding 3 — Sub-task 4 corrigendum placement (prefix vs append) not pre-decided: PASS-as-designed.** Sub-task 4 (line 125) explicitly delegates the placement choice to the dispatched subagent + reviewers, with a **stated preference for prefix** (line 125: *"with preference for the prefix-block placement because future readers encounter the corrigendum before reading Finding 3's body"*). This is a **well-considered editorial micro-decision** appropriately scoped to execution time. Acceptable.

**TW Finding 4 — No notebook/analytical work in scope: PASS.** §B invariant 5 (line 40) and §G out-of-scope reaffirmation (lines 226–230) together close this hole. No sub-task deliverable is a notebook, schema migration, analytical estimation, or notebook authoring.

**TW Finding 5 — Downstream β-spec dependency BLOCKING in §D: PASS.** §D acceptance criterion 8 (line 175) is explicit: *"Task 11.P.spec-β can now author a Mento-native-only retail-only hypothesis citing the registry spec doc as the on-chain-identity authority. The β-spec dependency on Task 11.P.MR-β.1 is satisfied."* The forward-pointer in §F line 214 also flags `2026-04-25-beta-spec.md` as **BLOCKED on this sub-plan's completion**. The dependency is explicit, bidirectional, and falsifiable.

---

## §3. Non-blocking advisories

### Advisory A — Sub-task 3 reviewer-trio asymmetry note (cosmetic)

§E sub-plan-level reviewers (lines 181–186) lists **CR + RC + TW**, while sub-task 3 reviewers (line 119) list **CR + RC + Senior Developer**. The **distinction is correct** (per the explicit explanation on lines 188–189), but a **first-time reader could conflate the two trios**. Suggestion: tighten the §E paragraph that explains the dual-trio distinction (line 187–189) by leading with the bottom line — e.g., "Two distinct trios apply at different stages: a TW-flavored trio for sub-plan structure, an SD-flavored trio for the registry spec doc itself."

**Not blocking.** Editorial readability only.

### Advisory B — Sub-task 2 proxy_kind enumeration: legacy-vs-canonical slug consistency

In §C sub-task 2 lines 85–90, the per-currency `proxy_kind` slugs are written with canonical tickers (`copm`, `brlm`, `eurm`, `kesm`, `usdm`, `xofm`). The **live DuckDB `proxy_kind` keys use legacy slugs** (`cUSD`, `cEUR`, `cREAL`, `cKES`, plus `COPM` and `XOFm`) per `project_duckdb_xd_weekly_state_post_rev531` and per the carbon-basket design doc line 56. The discrepancy between the sub-plan's enumeration and the actual DuckDB key strings is purely descriptive — the auditor will discover and reconcile during sub-task 2 execution because line 91 and the slug-vs-canonical-ticker mapping table in sub-task 3 (line 111) are both explicit.

**Suggestion (non-blocking):** add a one-line clarifier at line 90 along the lines of *"slug strings shown here use canonical tickers for readability; the live DuckDB keys preserve the pre-rebrand legacy slugs (`cUSD`, `cEUR`, `cREAL`, `cKES`) per `project_mento_canonical_naming_2026` and will be enumerated verbatim in the audit deliverable."*

**Not blocking.** Sub-task 2's acceptance criterion already routes the auditor to the slug-asymmetry surface; this advisory only avoids a double-take during execution.

### Advisory C — Cross-reference completeness: sibling sub-plans noted but not validated

§F lines 211–215 forward-points to four sibling sub-plans (`2026-04-25-rev2-notebook-migration.md`, `…-rev3-zeta-group.md`, `…-beta-spec.md`, `…-beta-execution.md`). Two of these may not yet exist on disk (the β-spec sub-plan is explicitly flagged BLOCKED on this sub-plan; the β-execution sub-plan is BLOCKED on β-spec). Forward-pointing to not-yet-authored sibling sub-plans is **acceptable** in the sub-plan-discipline pattern (the sibling sub-plans will be authored under their own super-tasks), but it would be a **PRE-DISPATCH micro-action** to verify the two definitely-exist sibling sub-plans (`…-rev2-notebook-migration.md` and `…-rev3-zeta-group.md`) are on disk before dispatching this sub-plan's first sub-task — to avoid a stale-citation surprise.

**Not blocking.** This is a hygiene check during sub-plan dispatch (Reality Checker's lane in the trio).

---

## §4. Conclusion

The sub-plan is **PASS-w-non-blocking-advisories**. All eight CR lenses pass. All five TW pre-flight findings are correctly handled, with TW Finding 1 (the substantive one) addressed via the explicit slug-vs-canonical-ticker mapping requirement in sub-task 3's deliverable. The Rev-5.3.4 RESCOPE invariant (§B-6) is the strongest single anti-fishing pre-commitment in the sub-plan and directly resolves the user-correction trigger.

The three non-blocking advisories are all editorial / readability refinements that can land during sub-task execution without re-review of this sub-plan. **Recommend trio convergence and proceed to sub-task 1 dispatch.**

If RC and TW concur, append a CORRECTIONS block to the sub-plan with the three advisories incorporated as small-text edits (analogous to the major-plan Rev-5.3.x CORRECTIONS pattern referenced on line 187), then proceed.

---

## Tool-use accounting

- 1× Read (sub-plan body)
- 5× Bash (memory file directory listing, major-plan grep for Rev-5.3.4 anchors, TR file existence + size, design doc cross-ref, live-DuckDB memory state grep)
- 1× Read (project_mento_canonical_naming_2026 memory)
- 1× Read (TR research file head)
- 1× Write (this review)

**Total: 9 tool uses (≤ 15 budget).** Read-only enforcement: confirmed; sub-plan untouched.
