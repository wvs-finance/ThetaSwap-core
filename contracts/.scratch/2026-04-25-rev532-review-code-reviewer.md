# Code Reviewer 3-way Review — Rev-5.3.2 CORRECTIONS Block

**Reviewer:** Code Reviewer (plan-revision lens; not source-code review)
**Date:** 2026-04-25
**Scope:** Rev-5.3.2 CORRECTIONS block at lines 1789–2030 of `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
**Precedent compared against:** Rev-5.3.1 CORRECTIONS-Rev-2 block (line 1028) + commit `7afcd2ad6`
**Disposition memo cross-checked:** `contracts/.scratch/2026-04-25-y3-coverage-halt-disposition.md`
**Immutable design docs cross-checked:** `2026-04-24-y3-inequality-differential-design.md`, `2026-04-24-carbon-basket-xd-design.md`

---

## Verdict: **PASS-with-non-blocking-advisories**

The Rev-5.3.2 CORRECTIONS block is anti-fishing-clean, internally consistent, and methodologically defensible. All five non-negotiable anti-fishing anchors (N_MIN=75, POWER_MIN=0.80, MDES_SD=0.40, MDES_FORMULATION_HASH, Rev-4 decision_hash) are explicitly preserved with byte-exact values in the §A pre-commitment table. The new task acceptance criteria are testable, dispatched-agent types are specified, dependencies are explicit, and the imputation non-decision is appropriately gated. The all-data-in-DuckDB invariant is reaffirmed with a complete additive-table manifest (§D). No code snippets contaminate the plan body. Internal consistency between §B (six new task headers) and §F (count reconciliation) holds.

The advisories below are non-blocking but should be addressed before the 3-way review converges.

---

## Blockers

(none)

---

## Non-blocking advisories

### Advisory 1 — Task count reconciliation imports a known accounting-drift discrepancy unchanged (line 2009, 2016)

§F (line 2009) takes the Rev-5.3.1 active task count as **63** and the existing reconciliation block at line 1739 documents that the 63-banner figure is itself **3 tasks higher than the 60-arithmetic count** ("accounting drift accumulated across revisions … the status banner's 63 has been the canonical Rev-5.3 figure since the brainstorm-fold and is preserved as such pending a future row-by-row rebuild"). Rev-5.3.2 propagates the drifted-banner-as-baseline, leading to a Rev-5.3.2 figure of `63 + 5 = 68` that itself inherits the +3 drift.

This is not a blocker — Rev-5.3.2 explicitly acknowledges the deferred row-by-row refresh ("Row-by-row spec-coverage matrix refresh remains deferred to a future Rev-5.4 per amendment-rider A8 (unchanged by this revision)") and does not introduce new drift; it simply propagates the prior accepted drift. But the line-2016 figure of **68 active / 70 total headers** is therefore arithmetically `60+5+letter-suffix-drift = 65 active / 64+5+1 = 70 total headers` if the §1739 arithmetic is taken as ground truth. **Suggested improvement:** add a one-line note in §F acknowledging the +3 drift carryover (e.g., "Rev-5.3.2's 68 figure inherits the same +3 accounting drift documented at line 1739 and resolves at the Rev-5.4 row-by-row refresh"). This is a transparency advisory, not a correctness gap.

### Advisory 2 — Cutoff arithmetic in Task 11.N.2d-rev is approximately right but the upper-bound is ambiguous (line 1886)

The acceptance criterion arithmetic claims "with BR upgraded to BCB SGS at ≥ 2026-02-01 and EU at 2025-12-01 and CO held on IMF IFS at 2025-07-01, the panel cutoff is bounded by min-of-three ≈ 2025-07-01 → 2025-08-22 weekly anchor; window 2023-08-01 → 2025-08 ≈ 105 weeks pre-aggregation". I verified the Friday-anchor week count:

- `2023-08-01 → 2025-07-01` = **100 Fridays**
- `2023-08-01 → 2025-08-22` = **108 Fridays**

Both bound the claim of "~105 weeks pre-aggregation." The CORRECTIONS block correctly notes the figure is SOURCE-DEPENDENT and explicitly directs the Technical Writer reviewer to sanity-check at execution time. The ≥ 95-week panel target and the ≥ 75-week joint-coverage gate are both well within the bracket.

However, the parenthetical ambiguity around "weekly anchor" ("min-of-three ≈ 2025-07-01 → 2025-08-22 weekly anchor") could read as *either* (a) the bound is `min(...)` rounded up to the nearest Friday, *or* (b) the bound is `min(...) + LOCF tail`. In practice the difference is small but the plan should pin one. **Suggested improvement:** in Task 11.N.2d-rev acceptance criterion (a), explicitly state which side of the LOCF tail bounds the cutoff (e.g., "panel cutoff = min(BR_cutoff, EU_cutoff, CO_cutoff) snapped to the next Friday-anchor America/Bogota; LOCF tail of up to 4 weeks is allowed per design doc §7"). This avoids a downstream reviewer confusion at execution time.

### Advisory 3 — Task 11.N.2.BR-bcb-fetcher acceptance criterion does not pin a CHECK-constraint behavior (line 1862)

The criterion enumerates "additive schema migration; Rev-4 `decision_hash` byte-exact through migration; primary `onchain_xd_weekly` and `onchain_y3_weekly` rows preserved byte-exact" but the precedent commit `a724252c6` (Rev-5.2.1 Task 11.N.1 Step 0) introduced a "composite-PK + relaxed-CHECK" pattern that's load-bearing for additive `source_methodology` introductions. The CORRECTIONS block correctly invokes "additive schema migration" but doesn't pin whether the new `bcb_ipca_monthly` table needs a CHECK constraint on the variation column (sanity bounds to catch BCB SGS API drift returning malformed data).

This is not a blocker because the test Step (b) assertion ("the cumulative-index utility reproduces the BR level series byte-exact under an independent-reproduction-witness numpy path") would fail loudly on malformed data. **Suggested improvement:** add a one-clause bullet under Task 11.N.2.BR-bcb-fetcher acceptance: "the raw `bcb_ipca_monthly` table CHECK clause (if any) is documented in the verification memo so a future reviewer can reproduce the schema exactly." This formalizes precedent without expanding scope.

### Advisory 4 — Task 11.N.2d.1-reframe "supersedes-as-applied" status note language is precise but the original task body is not editorially flagged in-place (line 1919)

The reframe correctly preserves the original Task 11.N.2d.1 body as historical record and states "A future reader following the plan executes Task 11.N.2d.1-reframe in place of the original." However, a reader landing at the original Task 11.N.2d.1 body (somewhere upstream in the plan) and reading top-to-bottom will not encounter the "superseded-as-applied" note until they reach the Rev-5.3.2 block much later. This creates a real risk of executing the obsolete task body if the reader does not first read top-to-bottom through the entire plan.

**Suggested improvement:** under Task 11.O-scope-update (which is already a "MODIFY in-place" task), add an additional in-place edit step: insert a one-sentence "**Rev-5.3.2 superseded:** this task body is replaced by Task 11.N.2d.1-reframe at line 1901; do not execute this body" line at the head of the original Task 11.N.2d.1 body. This is a one-line in-place edit, low risk, fully reversible if the reframe is later retired. It eliminates the readerly trap.

### Advisory 5 — Task 11.N.2.OECD-probe GO threshold (line 1839) silently picks "≥ 2026-01-01" — minor pre-commitment hygiene gap

The OECD probe acceptance criterion specifies "GO if OECD-direct CO cutoff is ≥ 2026-01-01 (i.e., recovers CO from 9-month-stale to ≤ 4-month-stale); NO-GO otherwise." This threshold is novel and not anchored to any prior anti-fishing anchor. The threshold itself is reasonable (matching the EU Eurostat HICP cutoff of 2025-12-01 within 1 month) but it's not pre-committed against any methodological anchor.

This is not a blocker because (a) the probe outcome does NOT feed the Task 11.N.2d-rev source mix under Rev-5.3.2 — the plan correctly handles "OECD probe negative" as a no-op (line 1843: "Task 11.N.2d-rev path executes regardless of OECD-probe outcome"), so a GO/NO-GO threshold issue cannot back-door affect the primary path; (b) the anti-fishing guard at line 1847 explicitly bans silent feed of probe outcome into Rev-5.3.2 mix. **Suggested improvement:** add one explanatory clause for the "≥ 2026-01-01" threshold (e.g., "the threshold is anchored to the EU Eurostat HICP cutoff at 2025-12-01 + 1 month tolerance"). This makes the threshold's provenance explicit for future reviewers.

### Advisory 6 — `source_methodology` literal-vs-schema distinction is correctly handled but the parenthetical at line 1823 could be stronger (line 1823, 1882, 1906)

The CORRECTIONS block consistently states "the literal string is finalized at implementation; the schema is described, not the literal" in three places (line 1823, 1882, 1906) — this is the right discipline. However, the parenthetical at line 1823 reads "(e.g., a `y3_v2_*` family describing 'EU=Eurostat / BR=BCB / CO=IMF / KE=fallback'; the literal string is finalized at implementation; the schema is described, not the literal)" which reads slightly forward-leaning ("e.g., a `y3_v2_*` family") — a downstream reader could over-interpret this as a near-pin.

This is not a blocker because the Rev-5.3.1 precedent (commit `7afcd2ad6`'s `source_methodology` tag handling for COPM-only primary) followed the same "describe, don't literal" discipline and did not produce reviewer confusion. **Suggested improvement:** replace the parenthetical example with a more abstract description (e.g., "a `source_methodology` value tagging the country source mix; literal string finalized at implementation"). This eliminates a tiny risk that the implementation commit reads the parenthetical example as a binding pin.

---

## What I checked (8 lenses)

### Lens 1: Anti-fishing invariant preservation — PASS

The §A pre-commitment table at lines 1806-1825 explicitly preserves all five non-negotiable anchors with byte-exact values:
- `N_MIN = 75` (PRESERVED, line 1808 — Rev-5.3.1 path α value, no further relaxation)
- `POWER_MIN = 0.80` (PRESERVED, line 1809)
- `MDES_SD = 0.40` (PRESERVED, line 1810)
- `MDES_FORMULATION_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` (PRESERVED, line 1811 — quoted byte-exact)
- Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` (PRESERVED, line 1813 — quoted byte-exact)
- Y₃ design doc §1, §4, §8, §9 (PRESERVED byte-exact, line 1814)
- X_d design doc — preserved byte-exact, referenced at line 2025 in §G
- Anti-fishing protocol (PRESERVED byte-exact, line 1815)

The §A table is the most important section of the CORRECTIONS block; it passes a strict byte-by-byte comparison against the disposition memo §1 and the Rev-5.3.1 precedent.

The β-rejection rationale at line 1798 is also methodologically clean — it explicitly cites the MDES_FORMULATION_HASH and Rev-5.3.1's prior 80→75 relaxation as the precedent the second relaxation would compound, making the "two relaxations on one plan revision exceed reviewer tolerance" framing tight.

### Lens 2: Pre-commitment table sanity — PASS

The "Updated" rows at lines 1816-1823 are all (a) actual changes, (b) precisely scoped, (c) reversible-or-disclosed if upgrade fails:
- `PRIMARY_PANEL_START` 2024-09-01 → 2023-08-01: precise (specific date), reversible (γ window swap is the disposition-memo-documented path), no relaxation in disguise.
- BR source IMF IFS via DBnomics → BCB SGS series 433: precise (named API series), disclosed if BCB SGS becomes unavailable (Task 11.N.2.BR-bcb-fetcher acceptance includes BR series cutoff ≥ 2026-02-01 HALT-trigger).
- CO source HELD on IMF IFS, OECD-direct probe added: explicitly held, no silent change. Probe is exploratory-only with anti-fishing guard at line 1847.
- EU and KE PRESERVED byte-exact.

No vague phrasing like "improve" or "modernize". No relaxation-in-disguise.

### Lens 3: Task acceptance criteria precision — PASS

For each of the six new task headers (lines 1830, 1851, 1876, 1901, 1923, 1950):
- **Task 11.N.2.OECD-probe** (line 1830): Subagent specified (Data Engineer); deliverable is a single scratch memo with explicit 5-row checkable acceptance; reviewer specified (Reality Checker); dependency none; anti-fishing guard explicit. PASS.
- **Task 11.N.2.BR-bcb-fetcher** (line 1851): Subagent specified (Data Engineer); deliverable is a fetcher path + cumulative-index utility + raw DuckDB table + failing-test-first per `feedback_strict_tdd`; reviewers specified (CR + RC + Senior Dev); dependency explicit (CORRECTIONS block landed + 3-way review converged); anti-fishing guard explicit. Acceptance includes a numpy-reproduction-witness — strong. PASS.
- **Task 11.N.2d-rev** (line 1876): Subagent specified (Data Engineer); deliverable is the Y₃ panel re-ingest at the new window with mixed sources + verification memo; reviewers specified (CR + RC + Senior Dev); dependency on Task 11.N.2.BR-bcb-fetcher; HALT-on-failure path explicit (line 1891) and forbids silent N_MIN re-relaxation. PASS.
- **Task 11.N.2d.1-reframe** (line 1901): Subagent specified; deliverable is the IMF-IFS-only sensitivity panel; reviewers specified; dependency on Task 11.N.2d-rev; status note clearly "supersedes-as-applied" the original Task 11.N.2d.1. PASS.
- **Task 11.N.2d.2-NEW** (line 1923): Deliberate non-task; status RESERVED. PASS (and see Lens 4 below).
- **Task 11.O-scope-update** (line 1950): Subagent specified (Technical Writer); reviewers specified (CR + RC + TW per `feedback_three_way_review`); dependency on Task 11.N.2d-rev; anti-fishing guard at line 1966 forbids running 11.O against the Rev-5.3.1 panel. PASS.

All six are testable. Reviewer rosters are specified. Dependencies form a DAG (none → BR-bcb-fetcher → 2d-rev → {2d.1-reframe, O-scope-update}; OECD-probe parallel-executable advisory).

### Lens 4: Imputation non-decision discipline — PASS

The plan is exemplary on this point. §B's Task 11.N.2d.2-NEW (line 1923) is explicitly RESERVED as a deliberate non-task. §C (line 1970) reinforces: "Rev-5.3.2 deliberately does NOT pre-commit any imputation method. The primary path is **truncated panel + γ window extension + δ-BR source upgrade ONLY**."

The four conditions for any future imputation revision (§C line 1976) are explicit: method-with-citation, sha256 anchor, side-by-side sensitivity, 3-way review pre-approval. This pattern pre-empts a future reviewer's "imputation isn't gated; what stops the next agent from sneaking it in?" objection.

The placeholder DOES NOT silently re-introduce imputation as a "future task" with an open implementation contract — it's a documented non-decision with a strict gate to convert it to a task.

### Lens 5: All-data-in-DuckDB invariant — PASS

§D (line 1980) provides an explicit additive-table manifest:
- `bcb_ipca_monthly` — NEW under Task 11.N.2.BR-bcb-fetcher.
- `oecd_cpi_monthly` — NEW conditional on Task 11.N.2.OECD-probe GO; explicitly NOT consumed under Rev-5.3.2.
- `dane_ipc_monthly` — EXISTING / reuseable; reserved.
- All Rev-5.3.1 and earlier tables PRESERVED byte-exact.

The additive-only invariant is enforced via the existing schema-migration test pattern (`test_onchain_duckdb_migration.py`) per line 1991 — Rev-4 `decision_hash` byte-exact through migration; all prior table row counts byte-exact through migration. No raw fetches under Rev-5.3.2 bypass DuckDB.

### Lens 6: Code-agnostic body — PASS

I scanned the CORRECTIONS block (lines 1789-2030) for Python and SQL contamination using regex against `def`, `import`, `class`, ```` ```python ````, ```` ```sql ````, `SELECT … FROM`, `np.`, `pd.`, `.iloc`, `requests.get`. Zero matches. The block is 100% prose: behavior, data sources, methodology, and acceptance criteria. References to module names like `econ_query_api.load_onchain_y3_weekly()` (line 1888) and `fetch_country_wc_cpi_components` (line 1857) are *contracts* (function signatures named in immutable design doc §8), not code — this is consistent with the design-doc precedent.

### Lens 7: Internal consistency — PASS

Task IDs in §B (the 6 new task headers) reconcile to §F's count enumeration:
- §B headers: Task 11.N.2.OECD-probe, Task 11.N.2.BR-bcb-fetcher, Task 11.N.2d-rev, Task 11.N.2d.1-reframe, Task 11.N.2d.2-NEW (deliberate non-task), Task 11.O-scope-update.
- §F enumeration (line 2011-2014): "+5 new tasks (Task 11.N.2.OECD-probe, Task 11.N.2.BR-bcb-fetcher, Task 11.N.2d-rev, Task 11.N.2d.1-reframe, Task 11.O-scope-update)" + "+1 deliberate non-task (Task 11.N.2d.2-NEW — RESERVED placeholder)".

5 + 1 = 6 total headers in §B; §F correctly distinguishes 5 dispatched tasks from 1 placeholder. Cross-references (e.g., line 1888 referencing `load_onchain_y3_weekly()`, line 1925 referencing `MDES_FORMULATION_HASH`, line 2027 referencing the prior HALT memo `cefec08a7`) all resolve.

### Lens 8: TW-flagged items

- **Cutoff arithmetic sanity-check** (Task 11.N.2d-rev acceptance criterion (a), line 1886): the math holds within the bracket — see Advisory 2. Window `2023-08-01 → 2025-07-01` is 100 Fridays; window `2023-08-01 → 2025-08-22` is 108 Fridays; both bracket the "~105 weeks" claim. The "≥ 95 weeks" target is well below the bracket.
- **`source_methodology` literal-vs-schema distinction**: PASS — see Advisory 6 for a minor language-tightening suggestion. The literal is correctly NOT pinned in the CORRECTIONS block.
- **OECD-probe outcome no-op handling**: PASS — line 1843 explicitly states "the Task 11.N.2d-rev path executes regardless of OECD-probe outcome since it is BR-source-only-driven." Line 1847's anti-fishing guard reinforces this.

---

## Verification trail

```
$ wc -l contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
2030  (block at lines 1789-2030, 242 lines as TW briefed)

$ git log --oneline -15
cefec08a7 halt(abrigo): Rev-5.3.1 Task 11.O — Y₃ × X_d coverage HALT disposition memo
765b5e203 feat(abrigo): Rev-5.3.1 Task 11.N.2d — Y₃ 4-country inequality-differential dataset
7afcd2ad6 plan(abrigo): Rev-5.3.1 — N_MIN relaxation 80→75 (path α from pathological-HALT)
13cfe5f56 halt(abrigo): Rev-5.3 Task 11.N.2c — pathological-HALT (basket-aggregate 77 non-zero weeks < N_MIN=80)
2855240ae feat(abrigo): Rev-5.3 Task 11.N.2b.2 — Carbon atomic ingestion + 8 weekly proxy_kind series persisted
... (Rev-5.3.1 precedent fully aligned with the precedent format §G claims)

$ git show 7afcd2ad6  (Rev-5.3.1 commit; precedent for the CORRECTIONS-block format)
  → Confirmed `MDES_SD=0.40`, `N_MIN: Final[int] = 75`,
  → required_power(75, 13, 0.40) = 0.8638 (>= POWER_MIN=0.80 ✓)
  → Anchors used in this Rev-5.3.2 review match byte-exact

$ python3 (Friday-anchor week-count verification)
  Window 2023-08-01 → 2025-07-01: 100 Fridays
  Window 2023-08-01 → 2025-08-22: 108 Fridays
  → Brackets the "~105 weeks pre-aggregation" claim
  → ≥ 95-week target well within bracket
  → ≥ 75-week joint-coverage gate well within bracket

$ regex scan of lines 1789-2030 for code contamination
  Patterns: \bdef|\bimport|\bclass|```python|```sql|SELECT.*FROM|np\.|pd\.|\.iloc|requests\.get
  Matches: 0 (zero — code-agnostic)

$ regex scan of lines 1789-2030 for "Task 11.N.2"
  Headers found: 6 (5 dispatched + 1 RESERVED non-task)
  Cross-reference to §F line 2011: 5 + 1 confirmed
```

Cross-checks against immutable docs:
- Y₃ design doc §1 (Δ_country = R_equity + Δlog(WC_CPI)): PRESERVED byte-exact — Rev-5.3.2 changes BR source-vendor only, not the construct.
- Y₃ design doc §4 (60/25/15 WC-CPI weights): PRESERVED byte-exact — line 1872 anti-fishing guard reaffirms.
- Y₃ design doc §8 (component contracts incl. `fetch_country_wc_cpi_components`): consumer contract preserved — line 1864 acceptance criterion specifies "consumer contract preserved-compatible."
- Y₃ design doc §9 (parameter table incl. `source_methodology DEFAULT 'y3_v1'`): preserved + additive — line 1823 explicitly admits a new tag without mutating prior rows via composite PK.

---

## Summary

The Rev-5.3.2 CORRECTIONS block is methodologically clean, internally consistent, and anti-fishing-discipline-preserving. The five non-negotiable anchors are explicitly preserved byte-exact. The six new tasks have testable acceptance criteria, specified subagents, specified reviewers, and explicit dependencies. The imputation non-decision is properly gated. The all-data-in-DuckDB invariant is honored. The body is code-agnostic. Cross-references resolve.

The six advisories above are language-tightening and transparency improvements; none affects correctness. PASS-with-non-blocking-advisories.
