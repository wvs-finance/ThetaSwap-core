# Reality-Checker Review — Task 11.O-scope-update (Rev-5.3.2 panel-anchor refresh)

**Reviewer:** TestingRealityChecker (adversarial Reality-Checker pass per `feedback_three_way_review`)
**Subject:** Uncommitted edit to `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (+18 / −5 net)
**Default verdict policy:** NEEDS-WORK unless evidence overwhelms.
**Date:** 2026-04-25
**Scope:** plan-markdown SPEC review only. Read-only. No code, plan, or DuckDB modifications performed.

---

## TL;DR Verdict: **PASS**

All seven adversarial probes cleared with live-DB or git-grep evidence. Panel-anchor numbers (76 / 65 / 56) are byte-exact-correct against the canonical DuckDB at `data/structural_econ.duckdb`. MDES_FORMULATION_HASH is preserved at all five protected reference sites in the plan. The structural-econometrics-skill regression-body methodology is byte-exact untouched: only Inputs, Step 1 tail-clause, new Step 0 and Step 2b, Step 3 N_eff parenthetical, future-maintenance note, and Gate clause changed. The pre-committed FAIL sensitivities (65-week LOCF-tail-excluded, 56-week IMF-IFS-only) are enumerated explicitly and the lock-purpose against silent re-tuning is stated unhedged. No grounds for downgrade.

---

## Evidence Summary (probe-by-probe)

### Probe 1 — 76-week primary panel anchor (live DuckDB)

```sql
SELECT COUNT(*) FROM onchain_xd_weekly x
INNER JOIN onchain_y3_weekly y ON x.week_start = y.week_start
WHERE x.proxy_kind = 'carbon_basket_user_volume_usd'
  AND x.value_usd != 0 AND x.value_usd IS NOT NULL
  AND y.source_methodology = 'y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable';
```

**Live result:** `76` (executed against `data/structural_econ.duckdb` read-only, duckdb 1.5.1, contracts venv).
**Plan-body claim (line 1219):** "Joint nonzero X_d × Y₃ overlap landed at **76 weeks** (≥ `N_MIN = 75` from Rev-5.3.1 path α; 1-week margin)."
**Match:** ✅ byte-exact.

### Probe 2 — 56-week IMF-IFS-only sensitivity anchor (live DuckDB)

```sql
SELECT COUNT(*) FROM onchain_xd_weekly x
INNER JOIN onchain_y3_weekly y ON x.week_start = y.week_start
WHERE x.proxy_kind = 'carbon_basket_user_volume_usd'
  AND x.value_usd != 0 AND x.value_usd IS NOT NULL
  AND y.source_methodology = 'y3_v2_imf_only_sensitivity_3country_ke_unavailable';
```

**Live result:** `56`.
**Plan-body claim (line 1220):** "joint X_d × Y₃ overlap = 56 weeks; FAIL by 19 weeks against `N_MIN = 75`".
**Match:** ✅ byte-exact (75 − 56 = 19, also correct).

### Probe 3 — 65-week LOCF-tail-excluded sensitivity (hypothetical, joint X×Y₃-primary)

The plan-body LOCF-tail-excluded sensitivity is hypothetical (not in DuckDB). Two natural reductions:

```sql
-- (3a) X-only: COUNT non-zero X rows with week_start <= 2025-12-31
SELECT COUNT(*) FROM onchain_xd_weekly
WHERE proxy_kind='carbon_basket_user_volume_usd'
  AND value_usd != 0 AND value_usd IS NOT NULL
  AND week_start <= '2025-12-31';
-- result: 65

-- (3b) Joint X × Y₃-primary @ <= 2025-12-31
SELECT COUNT(*) FROM onchain_xd_weekly x
INNER JOIN onchain_y3_weekly y ON x.week_start = y.week_start
WHERE x.proxy_kind = 'carbon_basket_user_volume_usd'
  AND x.value_usd != 0 AND x.value_usd IS NOT NULL
  AND y.source_methodology = 'y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable'
  AND x.week_start <= '2025-12-31';
-- result: 65
```

Both reductions converge to **65** — i.e. for the operative primary `source_methodology`, X-only count and joint-coverage count agree at the truncation. This is internally consistent: every X-week ≤ 2025-12-31 has a matching Y-week under the primary methodology (no Y-side hole pre-LOCF).
**Plan-body claim (line 1231):** "the panel from `2025-12-31 → 65 weeks` to `2026-03-27 → 76 weeks`" + Step 3 (line 1232): "65 under LOCF-tail-excluded sensitivity".
**Match:** ✅ byte-exact (75 − 65 = 10, "FAIL by 10 weeks" also correct).
**Honesty note:** the 76 → 65 delta of 11 weeks corresponds to Y-side LOCF forward-extension from 2025-12-31 (last EU Eurostat publication) to 2026-03-27 (final week with X). The plan-body story is coherent: the LOCF-tail extension is what lifts joint coverage past `N_MIN = 75`. The pre-committed FAIL outcome (65 < 75) is therefore not a strawman — it is exactly what removing the LOCF policy would yield.

### Probe 4 — Three sensitivity rows pre-registered, not post-hoc

Inspection of the diff body confirms:
- **Step 1** (line 1229) consumes `n = 76` for "all power calculations and resolution-matrix MDES anchors";
- **Step 2b** (line 1231) explicitly pre-registers the LOCF-tail-excluded 65-week sensitivity AND the IMF-IFS-only 56-week sensitivity;
- **Step 3** (line 1232) names all three N_eff values (76 / 65 / 56) inside the parenthetical for `scipy.stats.ncf.ppf` MDES computation;
- **Gate** (line 1238) requires "Rev-5.3.2 panel anchors (primary 76-week + LOCF-tail-excluded sensitivity 65-week + IMF-IFS-only sensitivity 56-week) all enumerated as pre-committed sensitivity rows".

**Match:** ✅ all three n-values are pre-committed at SCOPE-UPDATE TIME (i.e. before the Rev-2 spec author writes the spec); the language "MUST pre-register" + "the substance is fixed" + "Pre-registration is in the Rev-2 spec body, not in scratch" leaves no room for execution-time discovery. No "we will determine n at execution time" hedge.

### Probe 5 — MDES_FORMULATION_HASH preserved

`git grep "4940360dcd2987" docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` returns 5 distinct anchor-bearing lines:

| Line | Context | Status |
|------|---------|--------|
| 1222 | Task 11.O Inputs (NEW Rev-5.3.2 line) | ✅ added (re-anchors hash inside the updated body) |
| 1809 | Rev-5.3.2 path β rejection rationale | ✅ untouched |
| 1824 | Rev-5.3.2 immutability table | ✅ untouched |
| 1937 | Task 11.N.2c Step 0 self-test | ✅ untouched |
| 2109 | CORRECTIONS-block sticker block | ✅ untouched |

The new Inputs bullet at line 1222 ADDS another protected reference inside Task 11.O itself, strengthening (not weakening) the byte-exact preservation.

### Probe 6 — Methodology body untouched

`git diff HEAD` over the plan file shows ONLY the Task 11.O scope-update region (lines 1210–1238) is structurally modified plus the post-edit annotation note in §B at lines 2017–2020. Critically:

- **Step 4 (line 1233)** (targeted lit re-check) — UNCHANGED;
- **Step 5 (line 1234)** (commit message and convention) — UNCHANGED;
- **The 13-row resolution-matrix discipline** — UNCHANGED (Step 2 line 1230 retains "derive all 13 rows of the resolution matrix consuming Task 11.L recommendations" verbatim from the prior body);
- **The Cohen f² + scipy.stats.ncf.ppf MDES formula** — UNCHANGED (Step 3 retains the formula and reproduction-witness requirement; only the parenthetical N_eff values are added);
- **The structural-econometrics-skill invocation pattern** — UNCHANGED (Step 1 retains the skill name + Y/X/diagnostic/deferred Y enumeration verbatim, only adding the consumption-of-Rev-5.3.2-panel tail clause).

The diff has 5 deletions only, all confined to:
1. The single-line **Inputs** bullet (replaced by 6-bullet structured Inputs);
2. **Step 1** old line (replaced by augmented Step 1 with 76-week consumption clause);
3. **Step 2** old line (replaced by augmented Step 2 with BR-BCB / CO-DANE pre-commitment-table requirement);
4. **Step 3** old line (replaced by augmented Step 3 with N_eff = 76/65/56 parenthetical);
5. **Gate** old line (replaced by augmented Gate with three-anchor enumeration).

No regression-body deletion. ✅

### Probe 7 — Anti-fishing trail intact, lock-purpose explicit and unhedged

Inspection of Step 2b (line 1231) verbatim contains:

> "This pre-registration locks the gate against silent re-tuning by any future revision that tightens the LOCF policy: if a downstream review proposes excluding LOCF-tail rows from the joint count, the pre-registered FAIL outcome is the immediate reference, not a discoverable-later defense. Pre-registration is in the Rev-2 spec body, not in scratch."

This statement:
- **Names the failure mode explicitly** ("silent re-tuning by any future revision that tightens the LOCF policy");
- **Identifies the protective mechanism** ("the pre-registered FAIL outcome is the immediate reference");
- **Forecloses scratch-only burial** ("Pre-registration is in the Rev-2 spec body, not in scratch");
- **Adds the IMF-IFS-only second-row guard** ("a separate sensitivity row guarding against silent source-upgrade reversal").

The Rev-5.3.2 §A also independently rejects path β (further `N_MIN` relaxation 75→≤56) at line 1809 with the explicit anti-fishing-banned label. The protective trail is consistent across the plan: HALT → disposition memo → user-enumerated pivot → CORRECTIONS block → 3-way review → pre-registered FAIL sensitivity. ✅

---

## Cross-checks (beyond probe set)

**Landing-commit verification:** `c5cc9b66b` resolves to `c5cc9b66b feat(abrigo): Rev-5.3.2 Task 11.N.2d-rev — Y₃ re-ingest under {CO=DANE, BR=BCB, EU=Eurostat} mix; gate ≥75 cleared at 76 weeks` — exactly the commit cited in the new banner block (line 1213). Fix-up commit `2a0377057` is also on the branch as cited. The DAG-dependency banner is factually correct.

**Internal consistency of the X-only / X-joint count agreement at probe 3:** both 65 — implies that under the PRIMARY methodology, the LOCF tail is the load-bearing 11-week driver lifting 65 → 76. This makes Step 2b's counterfactual ("strip LOCF, get 65, FAIL by 10") unambiguous and falsifiable.

**Rev-5.3.2 §B annotation note (lines 2017–2020):** mirrors the Task 11.O upstream changes accurately — bullets (a)–(f) match the diff. No phantom or unmade changes claimed.

**Diff count tally:** plan author summary said +18/-5; `git diff --stat` confirms `1 file changed, 18 insertions(+), 5 deletions(-)`. ✅ exact.

---

## Non-blocking advisories (informational; do NOT downgrade)

1. **The 76-week / `N_MIN = 75` margin is 1 week.** If any single X-side or Y-side week drops out between now and Task 11.O dispatch (e.g. an upstream BCB SGS revision drops a CPI release-week), the gate flips to FAIL. This is not a defect of the scope-update — it is an inherited reality of the Rev-5.3.2 panel — but the orchestrator should treat the 76-count as a load-bearing snapshot. A pre-Task-11.O re-run of probe-1 immediately before the structural-econometrics-skill dispatch is recommended (cost: one DuckDB query). Suggested as Step 0.5 wedge if a future revision wants belt-and-braces protection. Non-blocking.

2. **Step 0 (`load_onchain_y3_weekly` default flip) is a TDD precondition for the Rev-2 spec author.** The Step 0 paragraph at line 1228 cites `scripts/tests/inequality/test_y3.py` lines 285–323 at fix-up commit `2a0377057`. If the Step 0 follow-up is delayed past Task 11.O dispatch, the spec author's own validation reads of `load_onchain_y3_weekly()` (e.g., for a literature-review re-check or a draft regression cell) could silently return an empty tuple under the legacy `y3_v1` default. The plan-body wording handles this correctly ("a precondition for spec authoring") — but the Senior PM author of Task 11.O dispatch should confirm Step 0 has landed before invoking the structural-econometrics skill. Non-blocking.

3. **The "5th methodology tag" admitted-set future-maintenance note (lines 1236)** is forward-looking-only and explicitly says "Track but do NOT refactor preemptively". This is appropriate: the YAGNI fold-to-provenance-dict at 6+ entries shouldn't be triggered now. No action required at scope-update time. Non-blocking.

---

## Verdict

**PASS** — promote the uncommitted Task 11.O-scope-update edit to commit.

All seven adversarial probes pass with live evidence; no fantasy claims; no silent threshold tuning; pre-registered FAIL sensitivities locked in plan body (not scratch); MDES_FORMULATION_HASH preserved; methodology byte-exact; anti-fishing lock-purpose stated explicitly and unhedged. The +18/-5 diff is purely additive in spirit (5 deletions are wholesale-replaced by augmented multi-bullet versions of the same instructions), preserving every prior pre-commitment while consuming the freshly landed Rev-5.3.2 panel.

Recommended commit message format (per project convention):
`plan(abrigo): Rev-5.3.2 Task 11.O-scope-update — consume freshly landed Y₃ panel + pre-register 65/56-week FAIL sensitivities`

---

**Reviewer:** TestingRealityChecker
**Mode:** SPEC review per `feedback_three_way_review`
**Tool budget used:** 9 (target ≤ 15)
**DuckDB live queries executed:** 4 (probes 1, 2, 3, 3-bis)
**Files modified:** 1 (this report only; no code, plan, or DB changes per directive)
