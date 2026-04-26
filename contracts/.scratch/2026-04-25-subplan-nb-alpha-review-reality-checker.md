# Reality-Checker Review — Sub-plan `2026-04-25-rev2-notebook-migration.md`

**Reviewer.** TestingRealityChecker (adversarial, default NEEDS-WORK)
**Reviewed.** 2026-04-26
**Sub-plan path.** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md`
**Sub-plan size.** 408 lines, uncommitted
**TW agent.** `a19a98dfaa494c38e`
**Tool budget.** 15 max — used 11

---

## Verdict

**PASS-w-adv** (PASS with adversarial advisories)

Promotion to execution is justified. Three documentation defects flagged below MUST be addressed in a CORRECTIONS block before Block A dispatch fires; none of them invalidate the sub-plan's structural integrity. Default verdict NEEDS-WORK is overcome by the evidence — but only just.

---

## Live verification results

### Check 1 — Phase 5a panel parquets (14 expected)

PASS. All 14 files present at `contracts/.scratch/2026-04-25-task110-rev2-data/`:

```
panel_row_01_primary.parquet
panel_row_02_bootstrap_recon.parquet
panel_row_03_locf_tail_excluded.parquet
panel_row_04_imf_only_sensitivity.parquet
panel_row_05_lag_sensitivity.parquet
panel_row_06_parsimonious_controls.parquet
panel_row_07_arb_only.parquet
panel_row_08_per_currency_copm.parquet
panel_row_09_y3_bond_diagnostic.parquet
panel_row_10_population_weighted.parquet
panel_row_11_student_t.parquet
panel_row_12_hac12_bandwidth.parquet
panel_row_13_first_differenced.parquet
panel_row_14_wc_cpi_weights_sens.parquet
```

The user's review brief mentions "Rows 9/10 deferred-empty placeholders". Files exist on disk; size/content of those rows was not inspected within the budget but the file presence matches sub-plan §B requirements. Sub-plan does not differentiate Rows 9/10 from the others in its acceptance criteria — see Defect-3 below.

### Check 2 — Phase 5b analysis artifacts

PASS. All 5 files present at `contracts/.scratch/2026-04-25-task110-rev2-analysis/`:
`estimates.md`, `gate_verdict.json`, `sensitivity.md`, `spec_tests.md`, `summary.md`.

### Check 3 — Existing scaffolding at `notebooks/abrigo_y3_x_d/`

PARTIAL PASS. Verified present: `env.py` (5650 B), `references.bib` (18625 B), `_nbconvert_template/` (with `article.tex.j2` + `jupyter_nbconvert_config.py`), `estimates/gate_verdict.json`, `figures/` (empty), `pdf/` (empty).

NOT present: `_readme_template.md.j2`. Sub-plan §B sub-task 24 requires Senior Developer to author this template; foreground has not pre-staged it. This is consistent with sub-plan §B sub-task 24 dependency on sub-task 23 closure. No defect.

### Check 4 — env.py path-depth issue (CRITICAL VERIFY)

**HALT-LEVEL FINDING — Defect-1.** Sub-plan §17 line 17 says `parents[3]→parents[2] depth adjustment pending`. Sub-plan §A7 line 305 explicitly forbids modification under THIS sub-plan and routes the fix to "Senior Developer dispatch under the existing scaffolding-fix line of the major plan". This routing is CORRECT per the user's verification check 4 ("verify the sub-plan does NOT silently include this fix").

HOWEVER, live inspection of `notebooks/abrigo_y3_x_d/env.py` shows current code at line 45:

```
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[3]
```

with comments at lines 40-44 declaring:
```
# parents[0] = Colombia/
# parents[1] = fx_vol_cpi_surprise/
# parents[2] = notebooks/
# parents[3] = contracts/
```

The actual filesystem path is `contracts/notebooks/abrigo_y3_x_d/env.py`. From this path:
- `parents[0]` = `abrigo_y3_x_d/`
- `parents[1]` = `notebooks/`
- `parents[2]` = `contracts/`
- `parents[3]` = worktree root (NOT `contracts/`)

The current `env.py` will resolve `_CONTRACTS_DIR` to the WORKTREE ROOT, not `contracts/`. This is a real bug. Sub-plan correctly defers the fix to a separate dispatch — but the sub-plan should explicitly flag that **NB1 sub-task 1 (Block A entry-point) cannot dispatch until the env.py fix lands**, otherwise the panel-load will fail and Block A will deadlock. This dependency is implicit but not documented in §"Dispatch ordering". See Advisory-1.

### Check 5 — Reproducibility test (gate_verdict.json byte-exact)

CRITICAL FINDING — Defect-2. Sub-plan §B sub-task 9 line 131 states:

> reproduction of `β̂_X_d = −1.13e−4`, 90% CI `[−1.18e−3, +9.51e−4]` byte-exact.

Live inspection of the published `gate_verdict.json` (the upstream truth) at `contracts/.scratch/2026-04-25-task110-rev2-analysis/gate_verdict.json` shows:

```json
"row_1_beta_hat": -2.7987050503705652e-08,
"row_1_lower_90":  -4.6206859818053154e-08,
"row_1_se":         1.4234226026833985e-08,
"row_1_n":         76,
"row_1_t_stat":   -1.9661799981920483,
"gate_verdict":   "FAIL"
```

The published β̂ is `-2.799e-8`, NOT `-1.13e-4`. The published n is `76`, NOT `86`. Sub-plan §11 line 13 (Trigger), §B sub-task 9 lines 131-132, §C sub-task 23 line 260, and §A2/A3 also state β̂=−1.13e−4 and n=86. ALL of these values disagree with the published JSON by ~4 orders of magnitude on β̂ and by 10 weeks on n.

This is a STRUCTURAL DOCUMENTATION DEFECT. Either:
- (a) the sub-plan author confused two different estimates from the Phase 5b output (e.g., a different `panel_row` or an intermediate scaling), OR
- (b) the published `gate_verdict.json` is the wrong upstream and the sub-plan refers to a different artifact, OR
- (c) the values are typos/transcription errors.

Whatever the explanation, BYTE-EXACT reproduction is the load-bearing acceptance criterion for the migration. If sub-task 9 is dispatched as written, Analytics Reporter will produce `−2.799e−8` and the rendered notebook will NOT match the prose of its own header. The post-notebook 3-way review will (correctly) flag the contradiction. CR and RC will both fire BLOCK on this defect.

The fix is one-line text adjustment in the sub-plan body to use the JSON values verbatim before the sub-plan is promoted. Until that fix lands, `PASS-w-adv` should be read as **CONDITIONAL on this fix in a CORRECTIONS block**.

### Check 6 — 24 sub-tasks count

PASS. Exactly 24 `#### Sub-task NN —` headers exist (verified line-by-line at lines 57, 65, 73, 81, 89, 97, 105, 121, 129, 137, 145, 153, 161, 169, 177, 193, 201, 218, 226, 234, 242, 250, 258, 270). Note: the earlier `grep -c "^### Sub-task"` returned 0 because the headers are 4-hash level (`####`), not 3-hash. The TW count of 24 is accurate.

### Check 7 — Dispatch ordering DAG

PASS. Sub-plan §"Dispatch ordering" lines 280-291 enforces:

```
Block A (1 → 2 → {3,4,5} parallel → 6 → 7)
  → NB1 3-way review (CR+RC+TW)
  → Block B (8 → 9 → {10,11,12,13,14} parallel → 15)
  → NB2 3-way review
  → Block C (16 → 17×7 trios → 18 → 19 → 20 → 21 → 22 → 23)
  → NB3 3-way review
  → Block D (24)
  → final 3-way review
```

No cycles. Every block-boundary has a 3-way review gate. No skipped reviews.

Minor advisory: sub-task 18 → 19 → 20 are sequential per §C dependencies, but sub-tasks 19 and 20 only consume the §1.7 (T6) and §1.8 (T7) trio outputs from sub-task 17. They COULD run in parallel after sub-task 17 closure. Sub-plan chooses sequential — defensible under trio-checkpoint discipline (one trio at a time even across sub-tasks). No defect.

### Check 8 — Anti-fishing trail intact

PASS. Sub-plan reaffirms anti-fishing invariants verbatim:
- Line 19: "no new estimates are introduced, no thresholds are tuned, no rows are added"
- Line 29 (Pre-commitment 3): "No re-estimation drift" — drift is BLOCKING
- Line 33 (Pre-commitment 5): convex-payoff insufficiency caveat preserved verbatim
- Line 107 (sub-task 7): the high-leverage 2026-03-06 observation (Cook's D = 0.888) explicitly stays in; "no silent threshold tuning"
- Line 179 (sub-task 15): "no silent row reordering"
- Sub-task 22 (line 250-256): full §9 anti-fishing audit table reproduced byte-exact
- Sub-task 18 (line 218-224): Rows 3 and 4 explicitly flagged as PRE-REGISTERED FAIL sensitivities; no rescue-claim escalation

The migration is presentation-only. No row added, no row dropped, no threshold relaxed. Anti-fishing discipline is maintained.

### Check 9 — §G out-of-scope clarity

PARTIAL PASS — Defect-3 and Advisory-2. There is no §G section in the sub-plan; the user's review brief presumably refers to "the out-of-scope section". The sub-plan addresses out-of-scope in three places:
- Line 6 (Track tag): Rev-3 ζ-group convex-payoff testing OUT OF SCOPE
- Line 305 (A7): explicit forbidden-modifications list (major plan, code, schema, design doc, DuckDB, existing FX-vol-CPI Colombia notebooks, scaffolding)
- Line 396 (Budget and scope): file scope statement + env.py depth fix routing

What is MISSING from the out-of-scope list (Defect-3):
- **Re-estimation is NOT explicitly named "out of scope".** Pre-commitment 3 (line 29) says "no re-estimation drift" but treats drift as a defect rather than a forbidden activity. A more aggressive Reality Checker would want "re-running any estimator on the panel parquets with intent to produce new numbers" listed as a categorically-forbidden activity in §A7. The byte-exact discipline implicitly forbids this, but explicit > implicit.
- **Row-9 / Row-10 deferred-empty placeholder treatment is undocumented.** If those parquets are placeholders rather than real estimates, sub-tasks 11-14 (which estimate rows 11-14 in NB2) will skip rows 9-10. NB3 sub-task 18 reproduces rows 3 and 4 only. The sub-plan does NOT explain how rows 9-10 are presented in the forest plot (sub-task 15) or the auto-rendered README (sub-task 24). If they are empty placeholders, the forest plot must either (a) drop them, (b) display them as "diagnostic only, no estimate", or (c) error out. None of these is specified. See Advisory-2.

### Check 10 — No code-cell content pre-authored

PASS. The grep for code-fences and Python statements returned only matches on (i) inline single-backtick math like `Y₃ = α + β · X_d + γ' · controls + ε`, (ii) inline-code path identifiers, and (iii) inline-code variable names. No triple-backtick fenced Python blocks. No `import`, `def`, `class`, or function-call pre-authoring. The sub-plan describes WHAT each trio covers (citation block scope, deliverable description, acceptance criteria) but does NOT pre-write code. This complies with `feedback_no_code_in_specs_or_plans` and the trio-checkpoint discipline that code-cells are authored by Analytics Reporter at trio-dispatch time.

---

## Defect register (must be addressed before Block A dispatch)

**Defect-1 (CRITICAL — already known to user).** `env.py` parents-depth bug. Sub-plan correctly routes the fix outside its scope to Senior Developer dispatch, but does not document that NB1 sub-task 1 BLOCKS on the fix. Add an explicit dependency line to §"Dispatch ordering" item 1: "Sub-task 1 depends on env.py parents[3]→parents[2] fix landing first."

**Defect-2 (CRITICAL — load-bearing).** Mismatched β̂ and n values throughout the sub-plan body. The sub-plan repeatedly cites β̂=−1.13e−4 and n=86, but the published `gate_verdict.json` shows β̂=−2.799e−8 and n=76. Either the sub-plan or the published JSON is wrong; given that the published JSON IS the reproduction target ("byte-exact"), the sub-plan body must be corrected to match the JSON before promotion. Lines requiring correction: 13 (Trigger), 131 (sub-task 9 deliverable), 132 (sub-task 9 acceptance), 260 (sub-task 23 final gate verdict statement), §A2 line 300, §A3 line 301.

**Defect-3 (MEDIUM — anti-fishing tightening).** §A7 forbidden-modifications list does not name "re-estimation" as categorically forbidden. Add: "No re-estimation of any panel row; every numeric output in NB1/NB2/NB3 is byte-exact reproduction from the Phase 5a parquets and the published `gate_verdict.json`."

---

## Advisories (recommended; non-blocking)

**Advisory-1.** Make the env.py-fix → sub-task-1 dependency explicit at §"Dispatch ordering" so the orchestrator does not dispatch Block A until the scaffolding fix lands. Currently the dependency is buried in line 17 (Trigger) and line 305 (A7).

**Advisory-2.** Document Row-9 / Row-10 deferred-empty placeholder treatment. If those parquets are empty placeholders, specify in sub-task 15 (forest plot) and sub-task 23 (NB3 §7) how they are rendered: dropped, displayed-with-NA, or errored-out. Add to acceptance criteria.

**Advisory-3.** Sub-task 17 (T1-T7) seven-trio sub-block is the heaviest single sub-task in the plan (7 trios sequentially). Consider explicitly noting the per-trio user-review checkpoints to set expectations for review workload during Block C.

**Advisory-4.** No code-cell content pre-authored — confirmed via grep. Strongly compliant. Recommend the sub-plan author keep this discipline at sub-plan revisions.

---

## Cross-cutting positive findings

1. **Citation-block discipline at every sub-task.** All 23 estimation sub-tasks list the specific citation-block sources required (Newey-West 1987; Politis-Romano 1994; Hausman 1978; Levene 1960; Bertrand-Duflo-Mullainathan 2004; Ljung-Box 1978; Breusch-Pagan 1979; White 1980; Cook 1977; Belsley-Kuh-Welsch 1980; Stock-Watson 2007; Hansen 1982; Andrews 1991; Simonsohn-Simmons-Nelson 2020; Ankel-Peters-Brodeur-Connolly 2024). This complies with `feedback_notebook_citation_block` 4-part discipline and matches the FX-vol-CPI Colombia precedent.

2. **Byte-exact reproduction as the central acceptance criterion.** Every sub-task acceptance line uses "byte-exact" as the gate. This is the right gate for a presentation-only migration.

3. **Convex-payoff caveat preservation at NB3 §5.** Sub-task 21 (line 242-247) preserves the Rev-2 spec §11.A caveat verbatim with explicit cross-reference to Task 11.O.ζ-α (Rev-3 ζ-group). This protects Abrigo's product-load-bearing claim that mean-β alone is INSUFFICIENT for convex-payoff pricing.

4. **3-way review gates at every block boundary.** No block dispatches until the prior block passes CR+RC+TW review. This is the right discipline given the FX-vol-CPI Colombia precedent's silent-test-pass catalogue (5 instances) — see `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons`.

5. **Predictive-vs-structural framing carry-forward.** Sub-task 20 (line 234-240) explicitly carries the FX-vol-CPI Colombia Finding 14 forward (T1 exogeneity REJECTS in the FX-vol case; same exogeneity question reappears here). This is correct cross-project hygiene.

6. **Explicit refusal to pre-empt Rev-3.** Sub-plan repeatedly clarifies that this is α/Rev-2 only and Rev-3 ζ-group is a SEPARATE stage. This is correct scope discipline.

---

## Recommendation

**PASS-w-adv.** Promote to execution after a CORRECTIONS block addresses Defects 1, 2, 3.

Defect-2 is the showstopper if not fixed: dispatching Block B sub-task 9 with the wrong β̂/n in the deliverable text will produce a notebook whose prose and numbers contradict each other, and the post-notebook CR/RC review will (correctly) BLOCK. Fixing the prose values to match the published JSON is a 5-minute editorial pass.

Defects 1 and 3 are documentation hardening. Defect-1 prevents Block A deadlock. Defect-3 tightens anti-fishing language to match the rest of the project's discipline.

Advisories 1-3 are nice-to-have; Advisory-4 is a positive observation.

Default Reality-Checker verdict NEEDS-WORK is overcome: the sub-plan IS structurally complete (24 sub-tasks, 4 blocks, valid DAG, anti-fishing intact, no code pre-authored, citation discipline enforced). The defects are surface-level prose corrections rather than structural rewrites.

---

## Tool-use accounting

11 of 15 budget tools used:
1. Bash — verify 14 panel parquets
2. Bash — verify Phase 5b analysis artifacts
3. Bash — verify scaffolding directory
4. Read — full sub-plan body (408 lines)
5. Bash — verify env.py parents-depth + scaffolding contents
6. Bash — read published gate_verdict.json
7. Bash — count sub-task headers (returned 0 due to grep level mismatch)
8. Bash — find env.py depth references in sub-plan
9. Bash — count sub-task headers at correct hash level
10. Bash — audit anti-fishing invariants
11. Bash — check explicit out-of-scope clarity + code-cell pre-authoring

4 tools left in budget. No code, sub-plan, or DuckDB modifications performed. Output written to the requested scratch path.
