# Code Reviewer — Task 11.O scope-update SPEC review (Rev-5.3.2 §B)

**Date:** 2026-04-25
**Reviewer role:** Code Reviewer (CR-only; per `feedback_three_way_review` this is one of three parallel reviews — RC + TW dispatched separately)
**Scope under review:** uncommitted edit to `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` against `HEAD = ac67eaf715cba07333a15c618e8e4eff11de765d`
**Diff size:** +18 / −5 (net +13 lines), 51 hunk-lines per `git diff HEAD | wc -l` — matches author summary
**Lens budget:** ≤12 tool uses; actual uses = 6 (1 diff, 2 greps, 1 wc+rev-parse, 2 reads of plan body)

---

## Verdict: **PASS**

All 8 CR lens checks pass. No blocking issues. Two non-blocking advisories and one nit recorded for trio deliberation; none rises to BLOCK or SHOULD-FIX.

---

## CR lens — 8-check breakdown

### Lens 1: Anti-fishing invariants preserved (PASS)

Verified byte-exact references in the updated 11.O body:

| Invariant | Cited value in 11.O update | Pre-existing canonical anchor |
|---|---|---|
| `N_MIN` | `75` (line 1219, "≥ `N_MIN = 75` from Rev-5.3.1 path α") | `75` per Rev-5.3.1 CORRECTIONS-Rev-2 block at line 1028; `project_rev531_n_min_relaxation_path_alpha` memory |
| `MDES_FORMULATION_HASH` | `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` (line 1222) | Same 64-hex-char value at line 1809 (Rev-5.3.2 §A path-rejection-table) and line 1824 (Rev-5.3.2 §A invariant-preservation table); `project_mdes_formulation_pin` memory |
| Rev-4 `decision_hash` | not directly cited in the 11.O update — but no edit touches line 1088 (Task 11.N.2c gate) or line 1158 (Task 11.N.2d gate) where it is canonically anchored as `6a5f9d1b…443c` | Preserved transitively: the edit does not modify any task that anchors decision_hash |

The pre-registered FAIL outcomes at n=65 and n=56 (Step 2b + Step 3) are explicitly framed as anti-fishing locks, not as pivot escape valves: line 1231 reads "This pre-registration locks the gate against silent re-tuning by any future revision that tightens the LOCF policy: if a downstream review proposes excluding LOCF-tail rows from the joint count, the pre-registered FAIL outcome is the immediate reference, not a discoverable-later defense." This is exactly the discipline `feedback_pathological_halt_anti_fishing_checkpoint` mandates.

### Lens 2: Methodology body untouched (PASS)

Step 1 functional-form definition preserved byte-exact:

> `Y_asset_leg_t = (Banrep_rate_t − Fed_funds_t)/52 + (TRM_t − TRM_{t-1})/TRM_{t-1}`

The only Step 1 addition is a trailing sentence anchoring the operative `n` for the regression's power calculations to the Rev-5.3.2 76-week panel. That is an input update (which the scope-update authority explicitly grants), not a methodology change. The `superpowers:structural-econometrics` skill invocation pattern, the 13-row resolution matrix discipline (Step 2 unchanged in its core), and the MDES compute path (`scipy.stats.ncf.ppf` root-finding) are all preserved verbatim. The Step 3 addition only enumerates the three operative `n` values (76 / 65 / 56) for the matched regression — it does not re-define how MDES is computed.

The line 2017 §B annotation note is explicit: "The structural-econometrics-skill invocation methodology and the existing 13-row resolution-matrix discipline are preserved byte-exact — only the panel inputs and pre-commitments have been updated." The diff confirms this claim.

### Lens 3: Three forwarded advisories all folded in (PASS)

| Advisory | Origin | Folded at |
|---|---|---|
| RC A3 (LOCF-tail-excluded sensitivity pre-registration) | RC review at `contracts/.scratch/2026-04-25-y3-rev532-review-reality-checker.md` (probe-5) | Line 1231 — Step 2b explicitly cites "addresses RC A3 / SD-RR-A2"; the 65-week FAIL is byte-exactly tied to the RC report |
| SD-RR-A1 (`load_onchain_y3_weekly` default flip + Step-7 test migration) | SD review at `contracts/.scratch/2026-04-25-y3-reframe-review-senior-developer.md` | Line 1228 — Step 0 explicitly cites "addresses SD-RR-A1"; both (a) default flip and (b) test migration are concrete with file path + line range (`scripts/tests/inequality/test_y3.py` lines 285–323 at fix-up commit `2a0377057`) |
| SD-A4 (admitted-set fold-to-provenance-dict) | Same SD review §2 | Line 1236 — Future-maintenance note explicitly cites "SD-A4 advisory in `contracts/.scratch/2026-04-25-y3-reframe-review-senior-developer.md` §2"; correctly framed as future-revision-only ("Track but do NOT refactor preemptively") |

All three advisories trace to specific scratch reports and are addressed at concrete plan locations.

### Lens 4: Pre-registered sensitivity rows are concrete, not hedged (PASS)

Step 2b mandates two pre-committed sensitivity rows in the Rev-2 spec body:

1. **LOCF-tail-excluded sensitivity:** "**65 weeks → FAIL by 10 weeks against `N_MIN = 75`**" — concrete, FAIL-direction-explicit, byte-exactly tied to RC probe-5 at `contracts/.scratch/2026-04-25-y3-rev532-review-reality-checker.md`
2. **IMF-IFS-only sensitivity:** "joint X_d × Y₃ overlap = 56 weeks; FAIL by 19 weeks against `N_MIN = 75`" (line 1220) — committed at Task 11.N.2d.1-reframe, comparison memo cited

Both rows enumerate (a) the operative `n`, (b) the gate-distance, (c) the FAIL verdict, (d) the source memo for live-reproduction. No hedging language ("may FAIL", "expected to FAIL"). The substance is fixed even though the spec author may name the row.

The Gate (line 1238) enumerates all three rows (76 / 65 / 56) as pre-committed sensitivity anchors that must populate the resolution matrix — this is the Step-2b commitment carried into the Gate condition without dilution.

### Lens 5: Code-agnostic per `feedback_no_code_in_specs_or_plans` (PASS)

The edited block contains zero Python or SQL code blocks. Identifier-name references appear in inline backticks consistent with the existing plan voice at this granularity:

- `load_onchain_y3_weekly` (function name)
- `_KNOWN_Y3_METHODOLOGY_TAGS` (constant name)
- `_Y3_METHODOLOGY_PROVENANCE: Final[dict[str, str]]` (proposed future-revision constant — type annotation included but no implementation)
- `source_methodology` (parameter name)
- `scipy.stats.ncf.ppf`, `statsmodels.stats.power.FTestPower` (library API references — same shape as existing Step 3 prose preserved from prior revisions)
- File paths (`scripts/tests/inequality/test_y3.py` with line range `285–323`)

No imperative Python statements, no SQL DDL/DML, no function bodies. The `_Y3_METHODOLOGY_PROVENANCE: Final[dict[str, str]]` mention is a type-signature reference, not code; this is the same shape as `MDES_SD: Final[float] = 0.40` references in the §0.3 MDES formulation pin block elsewhere in the plan — the plan voice already admits this granularity.

### Lens 6: Cross-references resolve (PASS — verified live against codebase)

Methodology tag literals confirmed byte-exact in `contracts/scripts/econ_query_api.py`:

```
72:_KNOWN_Y3_METHODOLOGY_TAGS: Final[frozenset[str]] = frozenset(
76:        "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable",
77:        "y3_v2_imf_only_sensitivity_3country_ke_unavailable",
```

Both literals match the strings cited at plan lines 1219 and 1220 character-for-character. The admitted-set holds 4 entries (visible at lines 72–78 of `econ_query_api.py`); the future-maintenance note's claim that "currently holds 4 entries (`y3_v1`, `y3_v1_3country_ke_unavailable`, `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`, `y3_v2_imf_only_sensitivity_3country_ke_unavailable`)" is byte-exactly accurate.

The Reality-Checker scratch file path at line 1231 (`contracts/.scratch/2026-04-25-y3-rev532-review-reality-checker.md`) and the Senior-Developer scratch file path at line 1236 (`contracts/.scratch/2026-04-25-y3-reframe-review-senior-developer.md`) are not verified for existence by this review (out of CR scope — RC will probe), but their naming conforms to the plan's existing scratch-file convention.

### Lens 7: §B annotation note is non-mutating cross-reference (PASS)

Line 2017 reads as a pure post-edit annotation enumerating six items (a–f) that the upstream 11.O body now incorporates. It does NOT introduce new substantive constraints — every item (a–f) is also present in the upstream edit. This is the appropriate use of the §B annotation slot per the plan's own protocol that CORRECTIONS blocks point forward to in-place edits rather than duplicating their substance.

The annotation explicitly states: "The structural-econometrics-skill invocation methodology and the existing 13-row resolution-matrix discipline are preserved byte-exact — only the panel inputs and pre-commitments have been updated." This wording matches the upstream Rev-5.3.2 banner at line 1213 verbatim, providing a strong cross-reference rather than an independent claim that could drift.

### Lens 8: Internal consistency — Step numbering + Gate enumeration (PASS)

Step ordering is monotone and gap-free: **Step 0 → 1 → 2 → 2b → 3 → 4 → 5**. The `2b` insertion sits between `2` and `3` consistent with the plan's existing convention at Task 11.N.2b / 11.N.2b.1 / 11.N.2b.2 etc. — "letter-suffix steps are pre-existing-step refinements within the same logical phase."

Gate enumeration (line 1238) names exactly the three sensitivity panels Step 2b + Step 3 require: `primary 76-week + LOCF-tail-excluded sensitivity 65-week + IMF-IFS-only sensitivity 56-week`. All three trace back to either Step 2b (which enumerates two of three) or Step 1's operative-`n` claim (76) plus Step 3's three operative-`n` enumeration (76/65/56). The Gate is consistent with the body.

The Future-maintenance note's threshold claim (4 OK, 5 acceptable, 6+ fold) is internally consistent with itself: "the current shape is fine for 4 entries and remains acceptable through 5. The fold becomes strictly better at 6+." No off-by-one risk against the SD-A4 trigger rule.

---

## Non-blocking observations (advisory only — for trio deliberation, not BLOCK candidates)

### CR-A1 (NON-BLOCKING ADVISORY): Step 0 commit-message convention not specified

Step 0 mandates a Data-Engineer follow-up with two concrete deliverables (default flip + test migration) but does NOT specify a commit-message format for the resulting commit, in contrast to Step 5 which mandates `spec(abrigo): Rev-2 inequality-differential functional equation via structural-econometrics (Rev-5 Task 11.O)`. The Rev-5.3.1 N_MIN-relaxation correction at line 1028 establishes that anti-fishing-anchor changes carry conventional commit-message tags. Step 0 changes a default that the SD-RR-A1 advisory characterizes as a "silent-empty-tuple footgun" — eliminating it has anti-fishing significance comparable to the relaxation precedent.

**Suggestion (not a BLOCK):** consider adding a commit-message convention such as `chore(query-api): flip load_onchain_y3_weekly default to v2 primary literal + migrate test_y3.py round-trip to explicit tag (Rev-5.3.2 §B Task 11.O Step 0 / SD-RR-A1)`. Reviewers may also leave this to the Data-Engineer subagent's discretion.

### CR-A2 (NON-BLOCKING ADVISORY): Future-maintenance note threshold rule has a soft edge at n=5

The note states the admitted-set "remains acceptable through 5" but the SD-A4 trigger rule per the cited scratch report is `at ~6 entries the natural fold is to a structured _Y3_METHODOLOGY_PROVENANCE`. If a Rev-5.3.3 lands a 5th tag (e.g., LOCF-tail-excluded), the implementer reading this note's "acceptable through 5" guidance might defer the fold to 6+; whereas a Rev-5.3.4 lander of a 6th tag would then be on the hook for the fold without explicit allocation in this plan. This is forwarded-for-future consideration by design — but the plan does not specify which task in which future revision owns the fold.

**Suggestion (not a BLOCK):** consider amending to "The fold MUST be planned (not executed) as part of any plan revision that introduces the 5th tag, and executed as part of the revision that introduces the 6th." This makes the responsibility explicit. Alternatively the SD-A4 future-maintenance review trio in Rev-5.3.3+ can decide. Either resolution is acceptable.

### CR-N1 (NIT — DOCUMENTATION POLISH ONLY)

Line 1228 sentence-length: the Step 0 paragraph is a single 6-sentence run-on block (≈250 words). The current plan voice tolerates this density at the §0.3 MDES formulation pin block (similar paragraph density at line 1038), so CR does not flag this as a TW concern — but Technical Writer reviewing the trio may have its own view.

---

## Out-of-scope items (intentionally not reviewed by this CR pass)

- Whether the Rev-5.3.2 panel landing commits `c5cc9b66b` and `2a0377057` actually contain the claimed 76-week joint coverage (RC empirical probe scope).
- Whether the Reality Checker's probe-5 byte-exact verification of "65 weeks → FAIL by 10 weeks" matches DuckDB live state (RC scope).
- Whether the Step-1 functional form `Y_asset_leg_t = (Banrep_rate_t − Fed_funds_t)/52 + (TRM_t − TRM_{t-1})/TRM_{t-1}` is structurally appropriate for the inequality-differential research question (out of scope; this is the Rev-2 spec author's decision to make under the structural-econometrics skill, with the lens of Task 11.L literature support — guarded by the trio's review at Task 11.P).

---

## Reviewer's summary statement

This is a clean, surgical, scope-respecting plan edit. The author confined the changes to inputs / preconditions / sensitivities exactly as the scope-update title claims; the methodology body (the part the Rev-2 spec author owns) is preserved byte-exact. All three forwarded advisories are folded in with concrete, audit-able language. Anti-fishing invariants pass byte-comparison. Cross-references resolve against the live codebase. The two non-blocking advisories (CR-A1, CR-A2) and the nit (CR-N1) do not gate downstream dispatch.

**Verdict: PASS.** Ready to be combined with RC and TW reports for the Rev-5.3.2 Task 11.O-scope-update three-way review consolidation.

---

**Reviewer:** Code Reviewer (foreground sub-agent)
**File reviewed:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (uncommitted working-tree state vs. HEAD `ac67eaf71`)
**Cross-reference verified against:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/econ_query_api.py` (lines 72–78, 1534–1565)
**Tool budget consumed:** 6 of 12 allotted
