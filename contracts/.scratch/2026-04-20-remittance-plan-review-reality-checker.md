# Reality Checker — Phase-A.0 Remittance Implementation Plan Review

**Plan:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
**Reviewer:** Reality Checker (TestingRealityChecker discipline, evidence-first)
**Date:** 2026-04-20

---

## 1. Executive Verdict

**PASS-WITH-FIXES.** The plan is remarkably well-grounded: every shared-pipeline file it promises to `Modify` exists on disk with plausible mtimes, every memory-file it cites is present, the Rev-4 decision-hash and row-count claims verify exactly, the design-doc commit hash `437fd8bd2` is authoritative, and the 13-item Phase-0 mandatory-inputs enumeration is both present in the design doc and fully mapped in the plan's spec-coverage table. Anti-fishing provenance holds on filesystem evidence (mtime 2026-04-02 precedes CPI FAIL 2026-04-19 by 17 days). One BLOCK-grade data-source claim ("pinned public Socrata endpoint" for BanRep aggregate monthly *remittance*, Task 11) is unverifiable — the only Socrata endpoint documented in the corpus under that name points to the TRM exchange-rate feed, not remittance. Two FLAG-grade overstated claims concern the "Basco & Ojeda-Joya 2024 Borrador 1273 methodology" (the citation in the ranked-candidate report describes it as a reconstruction *caveat*, not an operational methodology) and the plan's task-count self-audit ("30 tasks" is exactly correct — verified). Fix BLOCK #1 before dispatching Task 11 and the plan is execution-ready.

---

## 2. BLOCK-severity findings

### B1. Task 11 "pinned public Socrata endpoint" for BanRep aggregate monthly remittance is unverified.

Plan Task 11 Step 3 asserts a pinned Socrata endpoint returns "a monthly DataFrame with columns `date` + `aggregate_inflow_usd` + `vintage_timestamp`." The only `BANREP_TRM_ACCESS.md` in the `liq-soldk-dev` corpus is at `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/BANREP_TRM_ACCESS.md`, and it documents `https://www.datos.gov.co/resource/mcec-87by.json` — the Tasa de Cambio Representativa del Mercado (TRM) feed, **not remittance**. Design-doc §"Scientific question" acknowledges that corridor breakdowns are "NOT as a single monthly corridor CSV" but asserts BanRep publishes "monthly family-remittance aggregates as a downloadable time series"; the concrete access path (URL, dataset ID, auth requirement) is absent from both the plan and the cited corpus file. Agent 3's ranked-candidate report (line 35) is softer still: "BanRep publishes monthly remittance aggregates with country-of-origin breakdown quarterly; corridor-level monthly not as a single CSV but reconstructable from Monetary Policy Report tables." **Fix:** Task 11 Step 1 must enumerate the actual endpoint URL (or HTML-scraping target if no API) and produce the fixture by hand before the test is written; alternatively, insert a Task 10b pre-Task-11 spike that resolves the endpoint question and writes the finding into the Rev-1 spec.

---

## 3. FLAG-severity findings

### F1. Task 14's "Basco & Ojeda-Joya 2024 Borrador 1273 methodology" is a reconstruction *aspiration*, not a documented replication target.

Agent 3's ranked-candidate report (line 35) and design-doc §"Scientific question" both describe Basco & Ojeda-Joya Borrador 1273 as the anchor *caveat* for corridor reconstruction — not a step-by-step documented methodology the plan can reproduce. Line 86 of the ranked-candidate report explicitly says this paper studies "remittance cyclicality, not vol causation." Task 14 therefore may find, on execution, that the paper's tables do not support a quarterly-corridor reconstruction with a propagated SE term. **Fix:** Task 14 Step 1 pre-flight must require the Data Engineer to read Borrador 1273 first and produce a one-page reconstruction recipe; if the recipe cannot be derived, Task 14 produces an empty-placeholder sensitivity row documenting the gap rather than silently omitting the row.

### F2. "A1 monthly-cadence re-aggregation" in Task 13 is *not* the same A1 pivot-candidate as in the CPI-FAIL memory.

The CPI completion memory (`project_fx_vol_econ_complete_findings.md` per memory index) identifies A1 as a pre-registered monthly-cadence panel built from CPI surprise; the plan imports the name "A1 monthly-cadence" but applies it to remittance surprise on the frozen weekly panel (re-aggregated up, not a separate panel). This conflation is cosmetic but could mislead reviewers auditing the anti-fishing-rescue claim. **Fix:** Task 13 Step 3 and the Rev-1 spec must rename or disambiguate: "A1-R" for the remittance variant vs "A1-C" for the CPI variant.

### F3. Task 25's "5-instance silent-test-pass pattern" count is verified exactly but the guard coverage is narrower than implied.

Per `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md` line 68, the CPI exercise catalogued five silent-test-pass instances. The plan's Task 25 installs three `nbconvert --execute` integration tests; the memory's §"three integration tests" (line 112) confirms this is the canonical guard, but the underlying five patterns are broader than notebook-execution failures (they include prose-vs-code drift and zero-assertion tests per line 69). **Fix:** Task 25 Step 1 should reference the five-pattern enumeration explicitly and assert each guard's failure mode, not only "returncode=0."

---

## 4. NIT-severity findings

### N1. Design-doc commit hash citation in plan header (`437fd8bd2`) — verified exact, but the plan should also pin the hash via `git rev-parse` in Task 1 Step 1 rather than relying on a static reference.

### N2. Plan's §"Spec-coverage self-check" lines 504–519 enumerate the 13 items and map each to a task; verified item-by-item against design-doc §"Mandatory inputs" lines 123–147. Ordering differs (plan permutes items within the table for readability), not a defect, but worth noting.

---

## 5. Fact-audit table

| # | Claim | Verified-in (file:line) | Verdict |
|---|---|---|---|
| 1 | `contracts/scripts/cleaning.py` exists | filesystem, mtime Apr 18 | TRUE |
| 2 | `contracts/scripts/nb2_serialize.py` exists | filesystem, mtime Apr 19 | TRUE |
| 3 | `contracts/scripts/gate_aggregate.py` exists | filesystem, mtime Apr 19 | TRUE |
| 4 | `contracts/scripts/render_readme.py` exists | filesystem, mtime Apr 19 | TRUE |
| 5 | `contracts/.gitignore` exists | filesystem | TRUE |
| 6 | `nb1_panel_fingerprint.json` exists with decision_hash `6a5f9d1b05c18def…` | `…/estimates/nb1_panel_fingerprint.json:23` | TRUE (full hash: `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`) |
| 7 | Rev-4 panel row_count = 947 | `nb1_panel_fingerprint.json:188` + `project_fx_vol_cpi_notebook_complete.md:41` | TRUE |
| 8 | Design doc has 13 mandatory-inputs items | `2026-04-20-remittance-surprise-trm-rv-design.md:125-146` | TRUE (items 1–13 enumerated inline) |
| 9 | Plan spec-coverage table maps all 13 items | `…-remittance-surprise-implementation.md:504-519` | TRUE |
| 10 | `feedback_no_code_in_specs_or_plans.md` exists | memory dir | TRUE |
| 11 | `feedback_notebook_trio_checkpoint.md` exists | memory dir | TRUE |
| 12 | `feedback_specialized_agents_per_task.md` exists | memory dir | TRUE |
| 13 | `feedback_scripts_only_scope.md` exists | memory dir | TRUE |
| 14 | `feedback_implementation_review_agents.md` exists | memory dir | TRUE |
| 15 | `feedback_push_origin_not_upstream.md` exists | memory dir | TRUE |
| 16 | "5-instance silent-test-pass pattern" | `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md:68` | TRUE |
| 17 | Design doc committed at `437fd8bd2` | `git log` on the file | TRUE |
| 18 | Total task count = 30 | `grep -c "^### Task "` on the plan | TRUE |
| 19 | `REMITTANCE_VOLATILITY_SWAP.md` mtime 2026-04-02 (predates CPI FAIL 2026-04-19) | `ls -la /home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/REMITTANCE_VOLATILITY_SWAP.md` → "Apr 2 16:40" | TRUE |
| 20 | Task 11 "pinned public Socrata endpoint" for aggregate monthly remittance | `BANREP_TRM_ACCESS.md` documents TRM endpoint only; no remittance URL in corpus or plan | **UNVERIFIABLE → BLOCK (B1)** |
| 21 | Task 14 "Basco & Ojeda-Joya 2024 Borrador 1273 methodology" is reproducible | ranked-candidate report line 35, 86, 123 describes it as caveat/anchor, not operational recipe | **NEEDS-CAVEAT (F1)** |
| 22 | "A1 monthly-cadence" cleanly distinct from CPI-A1 | plan Task 13 silent on disambiguation | **NEEDS-CAVEAT (F2)** |
| 23 | Agent 3's ranked-candidate report exists | `contracts/.scratch/2026-04-20-colombia-next-primary-candidate-ranked.md` | TRUE |

---

## 6. Positive findings (cleanly-cited claims to preserve)

- **P1.** Decision-hash preservation discipline (Task 12) correctly names the authoritative Rev-4 hash value with a forward-compatible "or current value" hedge; the hash verifies exactly.
- **P2.** Row-count invariant (Task 15 "row count = 947") matches both the fingerprint JSON (line 188) and the CPI completion memory (line 41).
- **P3.** Memory-rule citation density is high and every cited file exists in the memory directory — no hallucinated memory references.
- **P4.** Anti-fishing provenance is filesystem-verifiable (mtime 2026-04-02 vs CPI-FAIL 2026-04-19); the plan does not hand-wave the timeline.
- **P5.** The plan's §"Spec-coverage self-check" correctly maps all 13 Phase-0 mandatory inputs to downstream tasks — no orphan items.
- **P6.** Total task count self-claim ("30, slightly leaner than Rev-4's 33") is correct to the task.
- **P7.** `feedback_implementation_review_agents.md` pairing at Task 28 (Code Reviewer + Reality Checker + Senior Developer) honors the memory rule precisely.
- **P8.** `feedback_push_origin_not_upstream.md` cited at Task 30 is correct per the rule's NON-NEGOTIABLE phrasing.

---

**End report.** BLOCK count: 1. FLAG count: 3. NIT count: 2. Ready for TW consolidation pending B1 resolution.
