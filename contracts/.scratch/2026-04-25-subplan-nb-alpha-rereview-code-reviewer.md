# NB-α Sub-plan Fix-up — Code Reviewer Re-Review

**Artifact under review:** `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` (467 lines, fix-up by TW agent `ac7e5f48ea92db839`).

**Prior verdict:** NEEDS-WORK — 1 BLOCKING (Defect 2 wrong gate-verdict values, 8 occurrences) + 1 advisory (split sub-task 17 into T1-T7).

**Re-review date:** 2026-04-26.

**Verdict: PASS**

The sub-plan is ready for commit + sub-task dispatch.

---

## Verification matrix (8/8 PASS)

### 1. Stale wrong-value occurrences fully purged — PASS

`grep -nE "−1\.13e−4|n = 86|2023-08-01.*2026-04-24|β̂_CPI = −0\.000685|β̂ = −1\.13"` returns **zero matches** across the entire 467-line sub-plan. The prior-review BLOCKING defect (the 8 stale-value occurrences quoting Phase 5b's pre-Rev-5.3.2 estimate `β̂ = −1.13e−4`, `n = 86`, and the off-window date range) is fully resolved.

Note on the single remaining `n = 86` reference at line 109: this appears in sub-task 7 NB1 §6 ("the Rev-5.3.2 pre-commitment is to retain all 86 weeks"), referring to the **panel-construction frame size before the post-overlap-restriction n = 76 estimation window**. Read in context, this is the 86-week panel that NB1 diagnoses, with NB2/NB3 estimating on the 76-week analytic subset. This is internally consistent with sub-task 1's panel-fingerprint claim and sub-task 8/9's regression-frame n = 76. Not a defect; the grep test was over-broad. (If the major plan or Rev-2 spec ever consolidates to a single canonical n the diagnostic and analytic frames should be re-aligned, but this is out of scope here.)

### 2. Canonical Rev-5.3.2 values present — PASS

`grep -cE "−2\.7987e−8|n = 76|2024-09-27|2026-03-13"` returns **9 matches**. The canonical primary coefficient (`β̂ = −2.7987e−8`), the analytic-frame size (`n = 76`), and the canonical date window (`2024-09-27` start, `2026-03-13` end) appear at every load-bearing site:
- §A2 acceptance gate (sub-task 24b deliverable): "Row-1 primary `β̂ = −2.7987e−8`, HAC(4) SE = `1.4234e−8`, n = 76"
- Pre-registered FAIL rows (3, 4) carry their own Rev-5.3.2 sample sizes (n = 65 LOCF-tail-excluded, n = 56 IMF-only).

### 3. env.py BLOCKING dependency explicitly stated — PASS

§Dispatch ordering item **0** at line 340 declares verbatim:

> "**BLOCKING upstream — env.py scaffolding fix.** Block A sub-task 1 cannot dispatch until the `env.py` `parents[3] → parents[2]` depth-adjustment fix lands at `notebooks/abrigo_y3_x_d/env.py` … The orchestrator MUST verify the env.py fix has landed (post-fix `parents[2]` resolves to `contracts/`) before sub-task 1 dispatches."

A second redundant copy of the same dependency is embedded directly in **Sub-task 1's Dependency clause** (line 65), so the binding ordering is enforced both globally (Dispatch ordering §) and locally (sub-task 1 itself). This double-mention is appropriate redundancy for a BLOCKING dependency; not a duplication defect. RC's Defect-1 is closed.

### 4. Re-estimation categorically forbidden — PASS

§A7 (line 364) enumerates five forbidden categories:
- (i) re-estimation of any panel row — even with identical seed/library versions;
- (ii) panel-parquet modification;
- (iii) JSON/markdown analysis-artifact modification;
- (iv) silent threshold tuning, row reordering, row exclusion;
- (v) editorial compression of the convex-payoff caveat at NB3 §5.

(i) is leading. The `gate_verdict.json` and Phase 5a parquets are byte-exact reproduction sources only. RC's Defect-3 is closed.

### 5. Sub-task 17 split into 17.1–17.7 — PASS

Distinct headers present at lines 207, 215, 223, 234, 242, 250, 258 — one per T1 (exogeneity), T2 (Levene), T3 (placebo + primary gate), T4 (Ljung-Box), T5 (Jarque-Bera), T6 (Chow), T7 (predictive-vs-structural). Each has its own subagent + dependency clause; sub-task 18 declares "Sub-task 17.7 closed (all seven specification-test trios complete)" as its dependency, correctly anchoring the cascade. The CR Advisory-2 from the prior review is closed.

Note (minor, advisory only): sub-task 17 itself (line 203) remains as a meta-header that introduces 17.1–17.7. This is benign documentation but technically reads as if there are 8 entries (17, 17.1, …, 17.7); for downstream dispatch the orchestrator should treat 17.1–17.7 as the only dispatch units. The §Sub-task list line at line 43 already calls this out: "31 entries — sub-task 17 split into 17.1–17.7." Acceptable as-is.

### 6. Sub-task 24 split into 24a (Senior Developer) + 24b (Analytics Reporter) — PASS

Lines 320 (24a — README Jinja2 template authoring; Senior Developer) and 328 (24b — README render + post-render verification; Analytics Reporter). 24b's Dependency clause (line 334) correctly gates on 24a closure. The TW Advisory-4 dual-subagent ambiguity is closed.

### 7. Total dispatch units = 31 — PASS

Counted distinct dispatch sub-tasks: 1, 2, 3, 4, 5, 6, 7 (Block A NB1 = 7) + 8, 9, 10, 11, 12, 13, 14, 15 (Block B NB2 = 8) + 16, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 18, 19, 20, 21, 22, 23 (Block C NB3 = 14) + 24a, 24b (Block D README = 2) = **31 total**. Matches TW's reported count and §Sub-task list announcement at line 43.

### 8. §A7 categorically-forbidden list contains 5 items — PASS

Verified by visual inspection at line 364: items (i)-(v) are present in the order announced and span the full forbidden surface (re-estimation, parquet modification, JSON/markdown modification, silent threshold tuning, caveat compression).

---

## Praise (specific)

1. **Defense-in-depth on the env.py BLOCKING dependency.** The fix-up redundantly states the env.py-fix-must-land-first ordering at three sites (Sub-task 1 Dependency, §Dispatch ordering item 0, §File scope) — appropriate for a deadlock-class dependency. A junior orchestrator missing the global Dispatch ordering will still hit the warning in Sub-task 1 itself.

2. **Anti-fishing wording in §A7(i).** "Running an estimator with intent to produce new numbers (even with identical seed and library versions) is forbidden" — this preempts the Honest Mistake failure mode where someone re-runs the regression to "double-check" Rev-5.3.2 reproducibility and then has to decide what to do when a tiny floating-point drift surfaces. The categorical ban removes that decision.

3. **Sub-task 17 split with cascade dependencies.** Each 17.x's Dependency clause names the prior 17.(x-1), and sub-tasks 18, 19, 20 anchor on the specific 17.x they depend on (17.7 for 18; 17.6 for 19; 17.7 for 20). This makes the BTS execution graph linear within sub-task 17 but allows downstream NB3 sub-tasks to fork on the right T-test ancestor.

4. **24a/24b separation by subagent class.** Senior Developer authors the Jinja2 template (touches code semantics — control-flow, escaping); Analytics Reporter renders + verifies (exercises the template with `gate_verdict.json` data). Correct subagent-by-deliverable mapping.

---

## Outstanding (advisory, non-blocking)

**Advisory-1 — sub-task 17 meta-header bookkeeping.** Sub-task 17 at line 203 introduces 17.1-17.7 but is itself never dispatched. The §Sub-task list announcement clarifies this as "sub-task 17 split into 17.1-17.7", but it might confuse a fresh orchestrator scanning headers. Consider in a future revision: rename sub-task 17 to "Sub-task 17 (umbrella) — T1-T7 specification tests" or strip the umbrella header entirely. Non-blocking.

**Advisory-2 — n = 86 vs n = 76 frame distinction.** The single line 109 reference to "all 86 weeks" (panel-construction frame in NB1 §6 outlier diagnostics) is correct against the design but jars against the n = 76 estimation-frame quoted at sub-tasks 1, 8, 9, 24b. The sub-plan correctly separates "diagnostic frame" (NB1) from "analytic frame" (NB2/NB3), but a one-line note in the §Block A intro reminding the reader of the two frame sizes (86 panel-construction → 76 post-overlap-restriction) would prevent the orchestrator from mistaking the two for an inconsistency. Non-blocking.

---

## Disposition

The sub-plan is **ready for commit and sub-task dispatch**. Both prior CR defects (BLOCKING wrong-values, advisory sub-task 17 split) are fully resolved. RC's Defect-1 (env.py BLOCKING) and Defect-3 (re-estimation forbidden) are also resolved. The two advisories above are bookkeeping improvements and do not block.

Recommended next steps:
1. Commit the sub-plan at the current 467-line state.
2. Dispatch the env.py `parents[3] → parents[2]` Senior Developer fix under the major plan's existing scaffolding-fix line (lines 2170-2188).
3. Verify env.py fix landed (orchestrator visual check that `parents[2]` resolves to `contracts/`).
4. Dispatch sub-task 1 (NB1 §0) under STRICT trio-checkpoint HALT discipline.
