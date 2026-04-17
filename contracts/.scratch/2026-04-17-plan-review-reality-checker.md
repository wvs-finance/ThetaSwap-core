# Reality Checker Review — Econ Notebook Implementation Plan (2026-04-17)

**Document:** `contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md`
**Upstream spec:** `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` (rev 2)
**Default posture:** NEEDS WORK
**Reviewer:** TestingRealityChecker (Codex will review this output)

---

## Per-Scope-Item Verdicts

### 1. TDD plausibility — NEEDS EVIDENCE (fake-TDD smell, multiple tasks)

Strict TDD requires the test to fail *behaviorally*, not merely fail on ImportError. Several tasks openly admit the first failure is "module not found" / "file not found":

- Task 1 Step 2: "Expected: ImportError or AttributeError because `env.py` does not yet exist" — ImportError-only failure.
- Task 3 Step 2: "Expected: module not found."
- Task 4 Step 2: explicitly instructs `pytest.skip` of real-file assertions until Task 12 — that is a skip, not a failing test, for the real target.
- Task 5 Step 2: "script does not exist."
- Task 20 Step 2/3: the atomic-emit sub-test requires inserting a test-only hook into the serialization routine to force mid-way exception — the hook is authored in Step 4, so the test as written in Step 1 cannot reach the hook and will fail on `ImportError` of `nb2_serialize`.

Per the strict-TDD memory rule, behavior-first failure is expected but ImportError-first is tolerated so long as the test asserts a real behavior once the module exists. Four of the five cases satisfy this; Task 4 is the weakest (real-file assertions deferred via skip to Task 13 means Task 4 is *really* testing only the synthetic violator, which is honest but the plan should say so).

**Flag:** Task 4 Step 3 says "the test passes by correctly detecting the synthetic violator; the real-file assertions skip gracefully until Task 12 creates `cleaning.py`" — Task 12 is not the `cleaning.py` creator; **Task 13** creates it (Task 12 is "NB1 §5-7"). Internal pointer error.

### 2. Session-decision fidelity — VERIFIED (all rev 2 locked decisions honored)

Spot-check of the 13 locked decisions:
- Q1 hybrid audience: exec README + per-notebook body + appendix — Task 1, Task 26 README render, Task 13/14/21/27 appendix pattern. VERIFIED.
- Q2 nbconvert PDF: Task 6 template + Task 1 `just notebooks` recipe. VERIFIED.
- Q3 three-notebook split: explicit in Phase 1/2/3. VERIFIED.
- Q4 pre-committed primary upfront + chasing offline: Task 15 spec-hash check + Rev 4 citation; Task 16 Column 6 highlighted. VERIFIED.
- Q5 `remove-input` tag: Task 6 template test. VERIFIED.
- Q6 forest plot + spotlight + appendix matrix: Task 25 + Task 26 §9 + appendix. VERIFIED.
- Q7 README auto-render + verdict boxes: Task 26 Jinja2 + Task 15/22 verdict placeholder. VERIFIED.
- Two-pronged material-mover rule: Task 26 Step 1 Test A explicit (β̂ outside CI AND T3b classification change) + halt-before-§9 on T3b fail. VERIFIED.
- GARCH-X parametric bootstrap from residuals: Task 20 schema includes "parametric bootstrap from fitted residuals … NOT Gaussian" per §4.4 schema; Task 18 fits GARCH-X. VERIFIED.
- §3.5 block-bootstrap HAC sanity check: Task 16 explicit. VERIFIED.
- NB3 §8 ordering T1→T2→T4/T5→T6→T7→T3a: Tasks 22→23→23→24→24→25. VERIFIED.
- A9 rendered as two rows: Task 25 Step 1 explicit. VERIFIED.
- `just notebooks` recipe in existing justfile: Task 1 Step 5 explicit "worktree `justfile`", confirmed by repo inspection (worktree root contains `justfile`). VERIFIED.

### 3. Memory-rule compliance — MIXED

- **No literal code in plan:** VERIFIED. Plan contains no Python/SQL/Solidity; all tasks described in prose. Function names (`load_clean_weekly_panel`, `get_manifest`, `arch.arch_model`) appear as *references* to query-API endpoints and libraries, not code snippets — borderline but consistent with how the rev 2 spec handled the same items.
- **Specialized subagent per task:** VERIFIED. Every task names one. Task 21 and Task 26 correctly split authorship between Analytics Reporter + reviewer / Data Engineer + Analytics Reporter.
- **Strict TDD pattern:** VERIFIED structurally, see item 1 caveat.
- **Real data over mocks:** VERIFIED mostly — Tasks 13/15/16/18 hit real DuckDB via cleaning.py; Tasks 4, 5, 20 use synthetic fixtures for lint/schema/atomicity testing (legitimate per the memory rule's "mocks only for what can't be reproduced" exception — you cannot reproduce a mid-serialization crash without a hook).
- **Scripts-only scope:** POTENTIAL VIOLATION. Task 1 Step 5 modifies `justfile` at **worktree root** — that is one level up from `contracts/`. Per scripts-only memory, allowed surface is `contracts/scripts/`, `contracts/data/`, `contracts/.gitignore`. The worktree-root `justfile` is OUTSIDE `contracts/`. NEEDS USER DECISION: either (a) user approves expanding scope to include worktree-root `justfile`, or (b) the recipe lives in a `contracts/justfile` or a `contracts/scripts/run_notebooks.sh`. The plan itself should surface this scope question.
- **Push to origin not upstream:** VERIFIED. Non-Negotiable Rule 6 explicit. No task commits to upstream.
- **Citation-block rule:** VERIFIED. Task 5 pre-commit lint + every NB task's Step 3 author citation blocks + Task 7/8/9/10/11/12/15/16/17/18/19/22/23/24/25 all reference the four-part block.

### 4. Cross-task artifact coherence — VERIFIED WITH ONE INCONSISTENCY

- `nb1_panel_fingerprint.json`: Task 13 writes `estimates/nb1_panel_fingerprint.json`; Task 15 reads same path; Task 22 reads same path. COHERENT.
- `nb2_params_point.json`: Task 20 writes `estimates/nb2_params_point.json`; Task 22 reads same; Task 26 reads same for README render. COHERENT.
- `gate_verdict.json`: Task 26 writes `estimates/gate_verdict.json`; Task 28 reads same. COHERENT.
- `cleaning.py`: Task 13 creates at `contracts/notebooks/fx_vol_cpi_surprise/Colombia/cleaning.py`; Task 15/22 import same module. COHERENT.
- `references.bib`: Task 2 creates at `contracts/notebooks/fx_vol_cpi_surprise/Colombia/references.bib`; all subsequent tasks reference it. COHERENT.
- **Inconsistency:** Task 4 Step 3 says "real-file assertions skip gracefully until **Task 12** creates `cleaning.py`" but Task 13 is the creator. Fix pointer.

### 5. Citation completeness — FIVE SPOT-CHECKS, ONE MILD MIS-CITE

- Task 9 cites Wilson-Hilferty 1931 + Andersen-Bollerslev-Diebold-Ebens 2001 for RV^{1/3}. Wilson-Hilferty PNAS 1931 is correct (cube-root normal approx); ABDE 2001 (*JFE* "Distribution of Realized Exchange Rate Volatility") supports log-RV — weaker fit for RV^{1/3} but still canonical. VERIFIED.
- Task 17 cites Jarque-Bera 1987, Breusch-Pagan 1979, Durbin-Watson 1951, Ljung-Box 1978. All correct authors/years/topics. VERIFIED.
- Task 18 cites Han-Kristensen 2014 JBES, Bollerslev 1986, Bollerslev-Wooldridge 1992. Han-Kristensen journal is now JBES (rev 2 fix applied). VERIFIED.
- Task 24 cites Bai-Perron 1998 & 2003 (T6) and BIS 462 Fuentes-Pincheira-Julio-Rincón 2014 + be_1171 (T7). VERIFIED.
- Task 25 cites Simonsohn-Simmons-Nelson 2020 for forest plot. VERIFIED.
- **Mild mis-cite:** Task 11 Decision #8 invokes "Ederer-Nordhaus 2020 on the negative-price episode." No such paper exists in the rev 2 §14 reference list. Provenance unverified — recommend Fleming 2020 (CME Group note) or a WTI-negative-price paper by Omura or Chen; or drop citation and rely on the DuckDB `CASE WHEN value > 0` guard already in the query API. NEEDS EVIDENCE.
- Task 11 also cites "Ang-Hodrick-Xing-Zhang 2006" for VIX as global-risk proxy; correct topic but the rev 2 §14 bib does not include AHXZ 2006. Either Task 2 must add it or Task 11 must drop it. Citation-list completeness gap.
- Task 12 cites Belsley-Kuh-Welsch 1980 and Elliott-Rothenberg-Stock 1996 + Kwiatkowski et al. 1992 — neither appears in §14. Same completeness gap.

### 6. Review-report rev 2 fidelity — VERIFIED

- Han-Kristensen = JBES: Task 2 Step 1 explicit assertion; Task 18 Step 1 citation. VERIFIED (rev 1 regression avoided).
- Hansen-Lunde split from Heston-Nandi: Task 2 Step 1 lists both entries separately; design §4.4 carries the split. VERIFIED.
- Two-pronged material-mover: Task 26 Step 1 Test A. VERIFIED.
- Block-diagonal Σ̂ documented: Task 20 handoff metadata references bootstrap distribution description per §4.4. VERIFIED (indirect but present via §4.4 schema reference).
- Parametric bootstrap from residuals: Task 18 Step 1 + Task 20 schema. VERIFIED.

---

## Top-Level Verdict: **APPROVED WITH CHANGES**

Required before dispatch:
1. Fix Task 4 Step 3 pointer: "Task 12" → "Task 13" (creator of `cleaning.py`).
2. Resolve scripts-only-scope question on worktree-root `justfile` modification (Task 1 Step 5). Either user approves the scope expansion explicitly, or move the recipe to `contracts/` or a `scripts/run_notebooks.sh`.
3. Task 11: either add AHXZ 2006 and Ederer-Nordhaus 2020 (if real) to Task 2's references.bib assertion list, or drop/replace these citations.
4. Task 12: add Belsley-Kuh-Welsch 1980, Elliott-Rothenberg-Stock 1996, Kwiatkowski 1992 to Task 2's bib assertion list (or drop).
5. Minor: clarify Task 4 test is only honestly testing the synthetic violator until Task 13; not a blocker.

Plan is materially faithful to rev 2 spec, honors all 13 locked decisions, applies strict-TDD + specialized-subagent + citation-block rules consistently, and preserves artifact-path coherence. Remaining issues are bibliography-completeness gaps and one scope-boundary question. Not fantasy-level failure.
