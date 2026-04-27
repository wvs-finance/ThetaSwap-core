# Code Reviewer — Remittance-Surprise Implementation Plan Review

**Plan:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
**Date:** 2026-04-20
**Reviewer discipline:** Code Reviewer (file-paths, dependencies, test coverage, subagent assignment, allow-list, commit messages)

---

## 1. Executive verdict

**PASS-WITH-FIXES.** The plan is structurally sound — 5 phases × 30 tasks, specialized-subagent-per-task discipline is clear, X-trio protocol is pinned, integration-test guards are split per-notebook, the scripts-only allow-list is respected, and the decision-hash extension invariant is enforced. It inherits the proven Rev-4 scaffolding and names the Model QA Specialist unconditionally (matching the design doc). However, six items need resolution before execution: two inter-task forward-references that break strict dependency order, two artifact-path inconsistencies with the design doc's deliverables list, one silent-test-pass-risk in Task 22, and one ambiguous "Rev-4 `env.py`" cross-tree import path. None are methodology blockers; all are fixable mechanically by the Technical Writer.

---

## 2. BLOCK-severity findings (must fix before execution)

### B1 — Task 12 forward-references Task 13 auxiliary columns inside the decision-hash extension test
Task 12 test asserts "the extended decision-hash is a deterministic function of the Rev-4 hash + **the sorted remittance-column spec hashes**" and "any **mutation of an existing Rev-4 column** aborts with `FrozenPanelViolation`". But the auxiliary columns (`regime_post_2015`, `event_petro_trump_2025`, `a1_monthly_rebase`, `release_day_indicator`) are only created in Task 13. Task 12 therefore either tests against a hash that doesn't yet cover the auxiliary columns (causing Task 13 to silently re-break the hash), or it tests against columns the panel loader can't yet produce (test fails for the wrong reason). **Fix:** either (a) merge Tasks 12+13 into a single task so the extension test runs once against the full column set, or (b) split Task 12's test into two assertions — the Rev-4-hash-preservation assertion (testable now) and the auxiliary-hash extension (moved into Task 13's test).

### B2 — Task 9 declares `CleanedRemittancePanel` with auxiliary + quarterly-corridor columns before Tasks 13 and 14 exist
Task 9's test (Step 1) asserts the returned dataclass "mirror[s] `CleanedPanel` but with the remittance primary-RHS column, the **4 auxiliary columns** (regime-dummy, event-dummy, A1-monthly-rebase, release-day-indicator), and the **secondary quarterly-corridor column**." Those 5 ancillary columns are only materialized in Tasks 13 and 14. Either Task 9 has to be pared down to the primary-RHS column only, or Task 9 must be moved to run after Task 14. **Fix:** restrict Task 9 scope to the primary RHS column + decision-hash hook (no aux, no quarterly corridor), and have Tasks 13 and 14 each extend the dataclass additively. Name the intermediate types `CleanedRemittancePanelV1 / V2 / V3` or just test-extend field-by-field.

---

## 3. FLAG-severity findings (should fix, non-blocking)

### F1 — Artifact filename drift vs. design doc
The design doc §Deliverables §5 names `nb3_forest.json` and `nb3_sensitivity_table.json`. The plan never creates, references, or asserts these filenames in any task. Task 23 says "forest_plot.png" (figure, not JSON); Task 24 only creates `gate_verdict_remittance.json`. Either (a) the design doc's §5 deliverables must be down-scoped (forest data rolled into `gate_verdict_remittance.json`), or (b) Tasks 22–24 must add explicit asserts for the two missing JSON artifacts. The plan's §Spec-coverage self-check does not catch this.

### F2 — Task 7 "Rev-4 `env.py`" import path is ambiguous
Task 7 Step 3 says "Implement `env_remittance.py` **importing what it can from Rev-4 `env.py`**". But Rev-4's `env.py` lives at `contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py`, not in `contracts/scripts/`. A sibling directory import via `sys.path` manipulation or a relative-from-anchor pattern is needed; the plan leaves this to agent judgment. **Fix:** cite the absolute path of the source file in Task 7 Step 3 and specify the import strategy (e.g., `from contracts.notebooks.fx_vol_cpi_surprise.Colombia.env import pin_seed, NBCONVERT_TIMEOUT, REQUIRED_PACKAGES`).

### F3 — Task 22 silent-test-pass risk — Rev-4 lesson #1 unmitigated
Task 22 Step 1 test spec: "Assert NB3 §1 … §2 (T1 exogeneity), §3 (T2 Levene), §4 (T3a … + T3b gate replay), §5 (T4 … ), §6 (T5 … + T6 … + T7 …). **Each test emits a verdict dict** compatible with `gate_aggregate.build_gate_verdict`." That is the exact pattern from the CPI-lessons memory silent-test-pass instance #1 ("test asserts a dict exists, not that its values are numerically correct"). **Fix:** require each T1–T7 assertion to also check at least one numerical field (e.g., T1 F-stat is finite and > 0; T2 Levene p-value is in [0, 1]; T3b `gate_stat` is not NaN). This is a 3-line addition to the test spec and prevents the exact bug Task 25's nbconvert guards are meant to catch.

### F4 — Task 28 dispatches "three parallel" reviewers but the "Files" block lists only three report paths, not the coverage matrix
The review files are declared but the plan doesn't say what source material each reviewer sees differently. Per memory `feedback_implementation_review_agents.md`, each reviewer has a distinct focus (Code Reviewer = file/deps, Reality Checker = claims, Senior Developer = architecture). **Fix:** add a one-line focus directive for each of the three reviewer dispatches under Step 1 (as the Rev-4 plan does).

### F5 — Task 30 modifies a memory file outside the allow-list
Task 30 modifies `~/.claude/projects/…/memory/MEMORY.md`, which is outside all three allow-list entries in rule #4. This is a de-facto exception (the Rev-4 plan did the same thing). The allow-list as stated in rule #4 does not include the memory tree; it should be amended explicitly to say "plus the global Claude memory tree at `~/.claude/projects/…/memory/` for completion-record-only writes." Otherwise rule-#4-strict enforcement will abort Task 30.

---

## 4. NIT-severity findings (polish)

- **N1 — Task 7 test-file naming:** rule #11 requires `test_nb{N}_remittance_section{FIRST}[_{LAST}].py`; Task 7's test is named `test_env_remittance.py`, which is fine (env is not a notebook section). Consider adding an exception line in rule #11: "env / scaffold / fixture tests exempt from the `test_nb*` convention."
- **N2 — Commit-message consistency:** Task 1 uses `spec(remittance): …`, Tasks 2–4 use `review(remittance): …`, Task 5 uses `spec(remittance): …` again. Tasks 27–29 also use `review(remittance): …`. That's internally consistent. However, Task 30 uses `close(remittance): …` — "close" is not a conventional-commits standard type. Prefer `docs(remittance): …` or `chore(remittance): close …`.
- **N3 — Task 6 gitkeep scope:** `_nbconvert_template` path pattern in the test is `**/_nbconvert_template/**/*.aux` — the Rev-4 convention doesn't seem to emit `_nbconvert_template/` subfolders in the CPI estimates dir. Cross-check with Rev-4 `.gitignore` for consistency; the plan references it but doesn't pin the exact rule text.
- **N4 — Spec-coverage table:** §"Spec-coverage self-check" maps "Dec-Jan seasonality → Task 21 §9" and "Alternate-LHS sensitivity → Task 21 §9 + Task 23 §7" — both map to the same notebook section. Either split Task 21 §9 into two sub-sections (9a alternate-LHS, 9b Dec-Jan) or cite them both in the plan body as distinct trios.
- **N5 — Task 21 "Dispatch Data Engineer sub-task" inside an Analytics Reporter task:** rule #2 says "each task below names exactly one subagent." Task 21 names Analytics Reporter but Step 2 also dispatches Data Engineer for `build_payload_remittance`. This is a legitimate pattern but violates the single-subagent-per-task rule literally. Either (a) split into 21a (Data Engineer: helper) + 21b (Analytics Reporter: notebook cells), or (b) amend rule #2 to permit helper-script sub-dispatches. Same issue applies to Task 24.

---

## 5. Dependency-order audit

| Task | Depends on | Claim OK? |
|------|-----------|-----------|
| 1 | design doc at `437fd8bd2` | ✓ |
| 2–4 | Rev-1 spec from T1 | ✓ |
| 5 | T2+T3+T4 reports | ✓ |
| 6 | T5 Rev-1 spec accepted | ✓ (implicit) |
| 7 | T5 + Rev-4 `env.py` | **F2** (import path ambiguous) |
| 8 | T5 (anti-fishing text source) | ✓ |
| 9 | T7 env constants | **B2** (references aux columns from T13, corridor from T14) |
| 10 | T5, T7 | ✓ |
| 11 | T5 | ✓ |
| 12 | T9 | **B1** (test asserts column-hash coverage from T13) |
| 13 | T12 hash-extension function | ✓ (once B1 is resolved) |
| 14 | T9, T11 | ✓ |
| 15 | T9–14 | ✓ |
| 16 | T6–15 | ✓ |
| 17 | T16 | ✓ |
| 18 | T16 | ✓ |
| 19 | T16, T17, T18 | ✓ |
| 20 | T19 | ✓ |
| 21 | T19, T20 + `nb2_serialize.build_payload_remittance` (Data Eng sub-dispatch) | **N5** (multi-subagent) |
| 22 | T21 `nb2_full.pkl` | ✓ |
| 23 | T22 | ✓ |
| 24 | T22, T23 | **N5** (multi-subagent) |
| 25 | T16–24 | ✓ |
| 26 | T25 | ✓ |
| 27–29 | T16–26 | ✓ |
| 30 | T27–29 | **F5** (touches memory tree outside rule #4) |

---

## 6. Positive findings (preserve through fixes)

- **Clean inheritance narrative.** The plan explicitly calls out Rev-4 patterns it reuses (`load_cleaned_panel`, `_compute_decision_hash`, `reconcile`, `write_gate_verdict_atomic`, Jinja2 template, 3-integration-test guard) and marks them "additive only." This is exactly the discipline the design doc demands.
- **Integration-test split is correct.** Task 25 writes three separate nbconvert-execute tests (not one collapsed all-notebooks test), per the 5-instance silent-test-pass catalogue. Returncode-asserted, timeout-pinned, CI-enforced, not-skipped.
- **Anti-fishing framing is propagated.** Tasks 8, 22, 23, and 30 each carry the anti-fishing disclaimer forward. Rule #8 enforces it in commit messages. This survives a reviewer spot-check.
- **Decision-hash extension invariant is enforced pre-load.** Task 12's `FrozenPanelViolation` abort is the right place to catch Rev-4-panel mutation; the test wires it into the panel-load path, not as an afterthought.
- **Strict TDD is uniformly applied.** Every implementation task has the 5-step (write failing test → confirm failure → implement → confirm pass → commit) structure, verbatim, without drift.
- **Subagent naming is mostly unambiguous.** 28 of 30 tasks name a single subagent; N5 flags the two legitimate helper-script sub-dispatches. Data Engineer is correctly named for all pipeline/fixture/test-harness work, Analytics Reporter for all notebook authoring, Technical Writer for doc polish.
- **X-trio discipline is explicit at the protocol level**, not just invoked by name — the "HALT after every trio" + "Bulk authoring forbidden" is codified for every notebook-authoring task.
- **Spec-coverage self-check at end of plan** maps 13 mandatory inputs to downstream tasks. Catches all 13 (I verified each).

---

**Report length:** ~1,180 words.
**Recommended next step:** Technical Writer resolves B1, B2, F1–F5; NITs deferred to author discretion. No methodology issues in scope; Model QA will catch those in Phase 4 per the plan's own Task 27.
