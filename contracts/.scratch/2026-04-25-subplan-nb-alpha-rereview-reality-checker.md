# Reality Checker — NB-α sub-plan fix-up RE-REVIEW

**Document under review**: `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` (467 lines, uncommitted)
**Prior review**: `contracts/.scratch/2026-04-25-subplan-nb-alpha-review-reality-checker.md` — verdict NEEDS-WORK, 3 critical defects
**Fix-up TW agent**: `ac7e5f48ea92db839`
**Re-review date**: 2026-04-26
**Re-reviewer**: Reality Checker (TestingRealityChecker)
**Tool budget consumed**: 5 / 10

---

## Verdict: **PASS**

The fix-up has resolved all three Reality-Checker-flagged defects against canonical sources. Sub-plan is **ready for commit + sub-task dispatch** under the binding ordering in §"Dispatch ordering" (env.py parents-fix lands first, then sub-task 1).

---

## Defect-by-defect verification

### Defect-1 (CRITICAL) — env.py parents-fix dependency: **FIXED**

**Required by prior review**: explicit BLOCKING-upstream gate so sub-task 1 cannot dispatch until `env.py parents[3] → parents[2]` lands.

**Sub-plan now contains**:
- Line 65 (sub-task 1 entry): "**BLOCKING upstream relation:** sub-task 1 cannot dispatch until the `env.py` `parents[3] → parents[2]` depth-adjustment fix lands at `notebooks/abrigo_y3_x_d/env.py`. That fix is OUT OF SCOPE for this sub-plan and is dispatched as a separate Senior Developer scaffolding-fix line under the major plan Task 11.O.NB-α body (lines 2170-2188); see §'Dispatch ordering' item 1 for the binding ordering. Without the fix, panel-load at NB1 §0 will resolve `_CONTRACTS_DIR` to the worktree root rather than `contracts/` and Block A will deadlock."
- Line 340 (Dispatch ordering item **0**): same BLOCKING gate restated, with explicit orchestrator-verification clause: "The orchestrator MUST verify the env.py fix has landed (post-fix `parents[2]` resolves to `contracts/`) before sub-task 1 dispatches."
- Line 419 (artifact register): `env.py` listed as "parents[3] → parents[2] depth adjustment pending; Senior Developer dispatch under separate scaffolding-fix line at major plan ... lines 2170-2188 within the Task 11.O.NB-α body".
- Line 455 (file scope): "Sub-plan execution will adjust `env.py` depth via Senior Developer dispatch under a separate line; this document does not perform that adjustment."

The fix is now stated **four times** at three load-bearing positions (sub-task entry + dispatch ordering item 0 + artifact register + file scope). Deadlock pathway is closed. Verified.

### Defect-2 (CRITICAL load-bearing) — wrong β̂ / n values: **FIXED**

**Canonical values from `notebooks/abrigo_y3_x_d/estimates/gate_verdict.json`** (Tool 1):
- `row_1_beta_hat` = `-2.7987050503705652e-08`
- `row_1_se` = `1.4234226026833985e-08`
- `row_1_t_stat` = `-1.9661799981920483`
- `row_1_n` = `76`
- `row_1_lower_90` = `-4.6206859818053154e-08`
- `row_1_p_two_sided` = `0.04927782209941108`

**Canonical window from `.scratch/2026-04-25-task110-rev2-data/manifest.md` row-summary** (Tool 5):
- Row-1 primary window: `2024-09-27` → `2026-03-13`, n = 76

**Stale-value grep** (Tool 1, command `grep -E "1\.13e|n = 86|2023-08-01"`): **0 matches**. The wrong values from the prior draft (β̂ = −1.13e−4, n = 86, window starting 2023-08-01) are completely absent.

**Sub-plan citations (sample, all correct)**:
- Line 13 (Anchor §): "primary Row-1 `β̂_X_d = −2.7987e−8` with HAC(4) SE `1.4234e−8`, t-stat `−1.9662`, two-sided p `0.0493`, one-sided 90% lower bound `−4.6207e−8`, n = 76, window `[2024-09-27, 2026-03-13]`"
- Line 61 (sub-task 1 deliverable): "primary panel window `[2024-09-27, 2026-03-13]`; n = 76 weeks for the primary panel"
- Line 126 (NB2 §0 acceptance): "n = 76 rows, window `[2024-09-27, 2026-03-13]`"
- Line 133 (NB2 §1, the LOAD-BEARING citation): full byte-exact reproduction `β̂_X_d = −2.7987050503705652e−08`, HAC(4) SE `1.4234226026833985e−08`, t-stat `−1.9661799981920483`, two-sided p `0.04927782209941108`, one-sided 90% lower bound `−4.6206859818053154e−08`, n = 76, window `[2024-09-27, 2026-03-13]`. **Full 16-significant-digit precision**, exactly matching `gate_verdict.json`.
- Line 308 (NB3 §7): same canonical values plus T1 p = 0.003111, T3a p = 0.04928, T3b passes = false, T6 break-rejects = false, T7 = predictive — every value present in `gate_verdict.json` `spec_tests` block.
- Line 331 (README §6 acceptance): `β̂ = −2.7987e−8`, HAC(4) SE = `1.4234e−8`, lower-90 = `−4.6207e−8`, n = 76, window `[2024-09-27, 2026-03-13]`.

The reproducibility contract is now byte-exact and cited consistently throughout the sub-plan. The "Any divergence ... is a BLOCKING defect" clause at line 13 makes the contract enforceable at 3-way review. Verified.

### Defect-3 (MEDIUM) — re-estimation missing from §A7 forbidden list: **FIXED**

**Sub-plan §A7 (line 364) now reads**:
"**Categorically forbidden under this sub-plan:** (i) re-estimation of any panel row — every numeric output in NB1 / NB2 / NB3 is byte-exact reproduction from the Phase 5a parquets and the published `gate_verdict.json`; running an estimator with intent to produce new numbers (even with identical seed and library versions) is forbidden; (ii) modification of any panel parquet under `contracts/.scratch/2026-04-25-task110-rev2-data/`; (iii) modification of any JSON / markdown artifact under `contracts/.scratch/2026-04-25-task110-rev2-analysis/`; (iv) silent threshold tuning, row reordering, or row exclusion (per `feedback_pathological_halt_anti_fishing_checkpoint`); (v) editorial compression of the convex-payoff caveat at NB3 §5 (per pre-commitment 5)."

Five categorically-forbidden items, with re-estimation as item **(i)** in the load-bearing slot. The qualifier "even with identical seed and library versions" closes the loophole where someone could argue a deterministic re-run is just reproduction. Verified. Anti-fishing trail intact: no Rev-5.3.x invariant relaxed.

---

## Cross-checks against TW fix-up summary

### Sub-task split structure (CR Advisory)

**Claimed**: sub-task 17 split into 17.1-17.7 + sub-task 24 split into 24a/24b → **31 dispatch units total**.

**Verified at line 43**: "Sub-task list (31 entries — sub-task 17 split into 17.1-17.7; sub-task 24 split into 24a/24b per CR + TW advisories applied 2026-04-26)" and at line 47: "The pre-fix-up count was 24; the post-fix-up count is 31 (24 base + 6 sub-tasks added by 17→17.1-17.7 split + 1 sub-task added by 24→24a/24b split). The original sub-task numbering (1-16, 18-23) is preserved; only sub-tasks 17 and 24 are decomposed."

Arithmetic check: 24 base + 6 (sub-task 17 splits into 7 units, +6 net) + 1 (sub-task 24 splits into 2 units, +1 net) = **31**. Consistent.

Block-C dispatch sequence explicitly enumerates each split (line 345): "Sub-tasks 16 → 17.1 → 17.2 → 17.3 → 17.4 → 17.5 → 17.6 → 17.7 (each a single-trio dispatch; user gates each individually) → 18 → 19 → 20 → 21 → 22 → 23." Block-D similarly enumerates 24a → 24b at line 347. Each sub-task 17.* carries its own dispatch dependency on the prior 17.* (verified at lines 221, 232, 240, 248, 256, 264). No bulk-authoring misreading risk remains.

T6 / T7 anchor relationships (sub-task 17.6 → sub-task 19; sub-task 17.7 → sub-task 20) are explicitly stated at lines 252 and 260 with "anchor for sub-task NN" headers. Sub-task 19 dependency on 17.6 (line 280) and sub-task 20 dependency on 17.7 (line 288) are pinned.

### Anti-fishing trail (NON-NEGOTIABLE)

- No Rev-5.3.x invariant relaxed: the sub-plan explicitly preserves the Rev-5.3.2 published estimates byte-exact and forbids re-estimation, threshold tuning, row reordering, row exclusion (§A7 i / iv).
- Pre-commitment 3 ("No re-estimation drift", line 29): standalone statement, BLOCKING-defect clause attached.
- Pre-commitment 5 (line 364 §A7 v): convex-payoff caveat preservation explicitly forbidden from editorial compression.
- The sub-plan does NOT propose re-running estimation. Verified.

---

## Notes / minor observations (non-blocking, not advisories)

1. **The sub-plan correctly disclaims the env.py adjustment is OUT OF SCOPE** for this sub-plan — the fix is dispatched at the major-plan level. This is the right scope discipline; do not modify.
2. **The "BLOCKING defect" language is used 5+ times** across reproduction, citation-coverage, env.py, byte-exactness, and convex-payoff caveat — load-bearing repetition that aligns with how the post-notebook 3-way review should triage findings.
3. **The 16-significant-digit canonical citation at line 133** is the single most load-bearing reproducibility anchor in the sub-plan. Future fix-ups should preserve this verbatim (do not round).
4. **Stale-grep was performed** with the original review's exact failing pattern (`1\.13e|n = 86|2023-08-01`). Zero matches confirms the prior draft's defective values are wholly excised; no stale residue remained.

---

## Tool-use ledger

| # | Tool | Purpose | Result |
|---|------|---------|--------|
| 1 | Bash (cat gate_verdict.json) | Read canonical Row-1 + spec_tests values | Confirmed β̂=−2.7987...e−08, n=76, all spec-test verdicts |
| 1 | Bash (cat notebooks manifest.md) | Read panel window | File not present at notebooks path; fell back to .scratch manifest at Tool 5 |
| 1 | Bash (grep stale values) | Test Defect-2 stale residue | 0 matches — clean |
| 2 | Bash (grep env.py BLOCKING) | Test Defect-1 dependency text | 4 reinforcing citations across 3 load-bearing positions |
| 3 | Bash (grep §A7 forbidden) | Test Defect-3 ban list | 5 categorical bans, re-estimation as item (i) |
| 4 | Bash (grep 17.x / 24a/24b) | Test sub-task split structure | 31 entries confirmed; 17.1-17.7 + 24a/24b verified |
| 5 | Bash (grep panel window in sub-plan + Phase 5a manifest) | Cross-validate window + n = 76 against canonical source | Sub-plan window matches manifest row-summary table byte-exact |

5 tool calls used out of 10 budget.

---

## Verdict summary

**PASS** — fix-up TW agent `ac7e5f48ea92db839` resolved all 3 Reality-Checker-flagged defects. Canonical-source verification (`gate_verdict.json` + Phase 5a `manifest.md`) confirms byte-exact reproduction. Anti-fishing trail intact. Sub-plan is **ready for commit + sub-task dispatch** under the binding ordering in §"Dispatch ordering" (env.py parents-fix dispatched as a separate Senior Developer line under major plan Task 11.O.NB-α body lines 2170-2188 lands first; sub-task 1 dispatches second; subsequent sub-tasks per Blocks A/B/C/D ordering).

**No NEEDS-WORK items remain from the Reality Checker perspective.** Other reviewers (Code Reviewer, Technical Writer) may have separate findings on their respective concerns, but those are out of scope for this Reality Checker re-review.

---
**Reality Checker** — re-review complete 2026-04-26
**Evidence Location**: `contracts/notebooks/abrigo_y3_x_d/estimates/gate_verdict.json`, `contracts/.scratch/2026-04-25-task110-rev2-data/manifest.md`
**Re-assessment Required**: NO — sub-plan is committable as-is from the reproducibility-anti-fishing perspective.
