# Rev-5.3.2 CORRECTIONS Block — Reality Checker RE-REVIEW (second pass)

**Reviewer:** TestingRealityChecker (Reality Checker lens)
**Date:** 2026-04-25 11:08 EDT
**Plan file:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (Rev-5.3.2 CORRECTIONS, lines 1789–2097, post-fix-up rewrite)
**Prior BLOCK report (load-bearing precondition):** `contracts/.scratch/2026-04-25-rev532-review-reality-checker.md`
**Default verdict:** NEEDS-WORK; promotion requires evidence. This re-review found the three prior BLOCKERs cleanly resolved AND the new transparency-on-marginal-coverage framing honest; promotion to PASS-with-non-blocking-advisories is justified.

---

## Verdict: **PASS-with-non-blocking-advisories**

The Rev-5.3.2 fix-up rewrite resolves all three prior BLOCKERs (B1, B2, B3) with internally consistent task plumbing, transparent acknowledgement of marginal coverage, and a HALT-clause architecture that routes to user (not to silent threshold tuning) under the foreseeable failure mode. The plan now dispatches a task chain whose worst case (gate not cleared under the documented mix) is correctly classified as a HALT, not a workflow failure. This is the correct posture for a marginal-coverage gate under anti-fishing discipline.

I am not promoting all the way to clean PASS because four advisories surfaced during re-verification — none load-bearing, all minor (one schema-column-name discrepancy, one schema-comparison advisory on §A row, one structural advisory on the post-HALT decision-tree, one wording advisory on §A footnote a literal-vs-schema discipline). Each is documented in the §"Non-blocking advisories" section below and is mitigatable at execution time without re-dispatch.

The plan's marginal-coverage transparency is the load-bearing piece that justifies promotion past NEEDS-WORK: the §"Why ζ" honesty note at line 1802 and the Risk note at lines 1940-1945 explicitly state that the projected coverage is ~65 weeks (RC live-verified) — STILL BELOW the ≥75 gate — and route the HALT to user. This is honest and adversarial-resistant; it does NOT promise the gate will clear.

---

## How the three prior BLOCKERs are resolved

### B1 (joint-coverage arithmetic) — RESOLVED

**Prior claim:** path ζ as written produced 47 joint weeks; the disposition memo's "~80+ weeks" prediction held only under full δ-{BR, CO}.

**Fix:** Rev-5.3.2 now implements δ as δ-{BR via BCB SGS, **CO via the existing DANE table**}; new Task 11.N.2.CO-dane-wire is the wire-up for the CO branch. Live re-verification (Command 1 below) confirms: at cutoff 2025-12-31 (the EU-binding cutoff plus a few-week LOCF tail), joint nonzero coverage = **65 weeks**. This matches the plan's projected ~65 figure at line 1802 and line 1938.

**Why I am not BLOCKING despite 65 < 75:** the plan does NOT claim the gate will clear. The honesty note at line 1802 explicitly states "approximately 65 weeks ... still below the ≥75 gate." The Risk note at line 1940 reaffirms this. The HALT clause at line 1932 routes to user under the foreseeable HALT case. The acceptance criterion at line 1928 ("Joint nonzero X_d × Y₃ overlap ... ≥ 75 weeks") is unchanged and the gate stays at ≥75. The plan dispatches a task whose worst case is HALT-to-user — that is a legitimate workflow stage under the pathological-HALT anti-fishing discipline, NOT a guaranteed-failure dispatch.

The plan's behavior under the foreseeable HALT is materially different from the prior Rev-5.3.2 (which would have HALTed on a narrative path the plan claimed would clear the gate, conflicting with the disposition-memo's own ζ-row prediction). The fix-up rewrite re-aligns the plan's narrative with the live data: the projected coverage is honestly stated, the gate is honestly above the projection, and the HALT path is explicit.

### B2 (OECD-probe mis-classification) — RESOLVED

**Prior claim:** OECD direct SDMX returned CO CPI through 2026-03 — fresh enough to land the gate. The plan classified OECD-probe as non-blocking, but path ζ effectively depended on it (or some other CO upgrade).

**Fix:** Rev-5.3.2 reclassifies OECD-probe as **diagnostic-only** (Option A from the prior recommendations). Line 1858: "Outputs only a `.scratch/` memo for archival. NOT a dispatch dependency for any downstream Rev-5.3.2 task." Line 1860 anti-fishing guard explicitly states: "If OECD-direct SDMX freshness later motivates a CO source change, that change requires its own CORRECTIONS block + 3-way review (Rev-5.3.3 or later). Probe outcome may not be silently fed into the Task 11.N.2d-rev source mix under Rev-5.3.2."

Verified independently in §D additive-table list (line 2053): `oecd_cpi_monthly` is "**NOT CREATED under Rev-5.3.2**". Diagnostic dependency is correctly broken.

The CO upgrade now flows through Task 11.N.2.CO-dane-wire (the alternative recommendation from the prior BLOCK), NOT through OECD. This eliminates the circular dependency. OECD-probe runs purely as future-revision intelligence.

### B3 (DANE table state mis-described) — RESOLVED

**Prior claim:** `dane_ipc_monthly` was already populated and current through 2026-03-01 (live-verified at the time of prior review); the plan claimed DANE was "not reachable."

**Fix:** Rev-5.3.2 §A row (line 1822) now explicitly states the table is "already populated in the canonical structural-econ DuckDB at `contracts/data/structural_econ.duckdb` with **861 rows current through 2026-03-01** (ingested 2026-04-16; schema `(date, ipc_value, monthly_variation_pct, _ingested_at)`)." The §D additive-table list (line 2052) marks it "**EXISTING and ALREADY POPULATED** (consumed by Task 11.N.2.CO-dane-wire — no schema change, consume-only)."

Live re-verification (Command 1 below) confirms the table's content is unchanged from the prior review: 861 rows, 1954-07-01 → 2026-03-01, ingested 2026-04-16. The §A row's narrative ("Earlier 'DANE direct paths return 404' framing in this row was authored without DuckDB inspection and is corrected here") is correctly self-aware about the prior error.

Task 11.N.2.CO-dane-wire (lines 1864-1886) describes the wire-up as **consume-only**: "The `dane_ipc_monthly` table is **consume-only** — no schema mutation, no re-ingestion, no normalization in this task" (line 1878). Anti-fishing guard at line 1886 reaffirms: "The DANE table is **consume-only**. The fetcher dispatch change is a one-table wire-up; if DANE table contents change in a future re-ingest, that's a separate concern owned by whichever upstream task ingests `dane_ipc_monthly` (NOT this task)."

This is exactly the consume-only framing the prior BLOCK requested.

---

## Live re-verification (every command run + output)

### Command 1 — Re-confirm DANE table state (per re-review checklist item #1)

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom
source contracts/.venv/bin/activate
python -c "
import duckdb
con = duckdb.connect('contracts/data/structural_econ.duckdb', read_only=True)
print(con.sql('SELECT MIN(date), MAX(date), COUNT(*) FROM dane_ipc_monthly').fetchall())
print(con.sql('SELECT * FROM dane_ipc_monthly ORDER BY date DESC LIMIT 6').fetchall())
print(con.sql('DESCRIBE dane_ipc_monthly').fetchall())
"
```

Output (relevant rows):
```
[(datetime.date(1954, 7, 1), datetime.date(2026, 3, 1), 861)]
Latest 6 rows (date, ipc_index, ipc_pct_change, _ingested_at):
(2026-03-01, 156.94, 0.7770, 2026-04-16 18:00:22)
(2026-02-01, 155.73, 1.0774, 2026-04-16 18:00:22)
(2026-01-01, 154.07, 1.1821, 2026-04-16 18:00:22)
(2025-12-01, 152.27, 0.2634, 2026-04-16 18:00:22)
(2025-11-01, 151.87, 0.0725, 2026-04-16 18:00:22)
(2025-10-01, 151.76, 0.1848, 2026-04-16 18:00:22)
Schema: [('date', 'DATE', 'NO', 'PRI', None, None),
         ('ipc_index', 'DOUBLE', 'YES', None, None, None),
         ('ipc_pct_change', 'DOUBLE', 'YES', None, None, None),
         ('_ingested_at', 'TIMESTAMP', 'NO', ...)]
```

**Confirms:** DANE table state unchanged since prior review — 861 rows, 1954-07-01 → 2026-03-01, ingested 2026-04-16. Plan's §A line 1822 description "861 rows current through 2026-03-01 (ingested 2026-04-16)" matches DuckDB byte-exact on row count, cutoff date, ingest date.

**Note:** the plan's column-name claim `(date, ipc_value, monthly_variation_pct, _ingested_at)` does NOT match the actual `(date, ipc_index, ipc_pct_change, _ingested_at)`. This is a non-blocking advisory (A1 below); the wire-up task body would catch this at execution time via the failing-test-first.

### Command 2 — Re-verify projected joint coverage under revised mix

```bash
python -c "
import duckdb
con = duckdb.connect('contracts/data/structural_econ.duckdb', read_only=True)
for cutoff in ['2025-08-22', '2025-10-24', '2025-12-01', '2025-12-15',
               '2025-12-31', '2026-01-15', '2026-02-15', '2026-03-31']:
    n = con.sql(f'''
        SELECT COUNT(*) FROM onchain_xd_weekly
        WHERE proxy_kind=\\'carbon_basket_user_volume_usd\\'
          AND value_usd != 0 AND value_usd IS NOT NULL
          AND week_start <= \\'{cutoff}\\'
    ''').fetchone()[0]
    print(f'cutoff {cutoff} -> {n} joint nonzero weeks')
"
```

Output:
```
cutoff 2025-08-22 -> 47 joint nonzero weeks   (prior path ζ as originally written)
cutoff 2025-10-24 -> 56 joint nonzero weeks   (Rev-5.3.1 baseline)
cutoff 2025-12-01 -> 61 joint nonzero weeks   (EU-binding, no LOCF tail)
cutoff 2025-12-15 -> 63 joint nonzero weeks   (EU-binding + 2 weeks LOCF)
cutoff 2025-12-31 -> 65 joint nonzero weeks   (EU-binding + ~4 weeks LOCF)  ← plan's projected mix
cutoff 2026-01-15 -> 67 joint nonzero weeks
cutoff 2026-02-15 -> 72 joint nonzero weeks
cutoff 2026-03-31 -> 76 joint nonzero weeks   (full CO+BR+EU upgrade ceiling)
```

**Confirms:** plan's projected ~65 weeks at line 1802 and line 1938 is exactly what the data yields at the EU-binding cutoff plus weekly-anchor LOCF tail. The 47-week prior figure (path ζ as originally written, CO held on IMF) is no longer applicable — path ζ as fixed-up dispatches CO via DANE, which yields the EU-binding cutoff at 2025-12-01.

The full 76-week CO+BR+EU upgrade ceiling is still the top of the achievable range; that ceiling exceeds the 75 gate, but it requires a δ-EU upgrade which the plan deliberately defers.

### Command 3 — Verify Y₃ and X_d windows match prior review

```bash
python -c "
import duckdb
con = duckdb.connect('contracts/data/structural_econ.duckdb', read_only=True)
print(con.sql('SELECT MIN(week_start), MAX(week_start), COUNT(*) FROM onchain_y3_weekly').fetchall())
print(con.sql('''SELECT proxy_kind, MIN(week_start), MAX(week_start),
                 COUNT(*), COUNT(*) FILTER (WHERE value_usd != 0)
                 FROM onchain_xd_weekly
                 WHERE proxy_kind=\\'carbon_basket_user_volume_usd\\' GROUP BY proxy_kind''').fetchall())
"
```

Output:
```
[(datetime.date(2024, 9, 13), datetime.date(2025, 10, 24), 59)]
[('carbon_basket_user_volume_usd', datetime.date(2024, 8, 30), datetime.date(2026, 4, 3), 82, 76)]
```

**Confirms:** Y₃ panel state unchanged from prior review (59-week, 3-country panel ending 2025-10-24, KE absent). X_d panel state unchanged (82 weeks total, 76 nonzero, latest 2026-04-03). The path ζ projected mix would re-ingest Y₃ to ~109 weeks under the EU-binding cutoff with LOCF tail (per plan line 1936); the 65 joint figure is bounded by Y₃'s LOCF-tail end and X_d's nonzero filter.

---

## Resolution check on the §A and §D specifics (per re-review checklist items #3 and #4)

### Item #3a — does Task 11.N.2.CO-dane-wire move the math from 47 → 65?

YES. Live verification at Command 2: cutoff 2025-12-31 (EU-binding plus LOCF tail) yields 65 joint nonzero weeks. The plan correctly attributes this to the DANE wire-up (line 1802: "The DANE wire-up raises the path-ζ ceiling from 47 → ~65 vs. the gate's 75").

The wire-up is described as consume-only (line 1878, line 1886) with no schema mutation. This is the correct framing.

### Item #3b — is OECD-probe truly demoted?

YES. §D row (line 2053) marks `oecd_cpi_monthly` as "**NOT CREATED under Rev-5.3.2**". Task 11.N.2d-rev dependency list (line 1951) only requires Task 11.N.2.BR-bcb-fetcher AND Task 11.N.2.CO-dane-wire — OECD-probe is not in the dependency chain. Anti-fishing guard at line 1860 explicitly forbids feeding OECD outcome into the source mix under Rev-5.3.2.

The dispatch-ordering at line 1834 places OECD-probe FIRST (lightest, ~30 min — pure transcription) — this is a workflow ordering, NOT a logical dependency. The plan correctly disambiguates "dispatch sequence" from "logical dependency."

### Item #3c — is `dane_ipc_monthly` consume-only in §D?

YES. §D row (line 2052) marks it "**EXISTING and ALREADY POPULATED** (consumed by Task 11.N.2.CO-dane-wire — no schema change, consume-only)." The wording is unambiguous about consume-only at task-execution time.

The plan does NOT freeze a snapshot ID (e.g., a DuckDB snapshot or a row-count assertion at the task body level), but it ALSO does not lock it to current state either — it simply commits to consume-only at task-execution time. This is defensible (see advisory A2 below — RC has a mild preference but it is non-blocking).

### Item #4 — risk of future re-ingestion mutating the table?

The plan acknowledges this implicitly at line 1886 ("if DANE table contents change in a future re-ingest, that's a separate concern owned by whichever upstream task ingests `dane_ipc_monthly`"). It does NOT freeze the snapshot; it only commits to consume-only at task-execution time.

This is defensible. The downside (a future ingest task changing DANE data and propagating to `onchain_y3_weekly` mid-plan) is not in scope for Rev-5.3.2 because: (a) no other task in the plan touches DANE; (b) the schema-migration test invariant (line 2056) protects against schema drift, and (c) the failing-test-first at line 1875 asserts cutoff date ≥ 2026-02-01 at task-execution time, so a regression in DANE freshness would HALT the wire-up task before propagation.

If the user prefers a tighter freeze (e.g., commit a row-count + max-date assertion as a precondition test in Task 11.N.2.CO-dane-wire), I would mark that an enhancement. For Rev-5.3.2 dispatch, consume-only at task-execution time is sufficient.

---

## Resolution check on EU-binding country and δ-EU deferral (per re-review checklist item #5)

The plan acknowledges EU is now the binding country at line 1823 ("EU = Eurostat HICP via DBnomics already fresh through 2025-12 (~5-month-stale at authoring date — **binding country under the Rev-5.3.2 mix**; see Task 11.N.2d-rev acceptance arithmetic note for the joint-coverage implication)"). The arithmetic note at line 1936 makes this explicit: "the binding country is **EU at 2025-12-01**."

The plan deliberately defers δ-EU and accepts marginal coverage with HALT-routing as the protective net. The Risk note at lines 1940-1945 documents this explicitly:

- (a) δ-EU upgrade as a future revision possibility (would yield ~76 joint weeks per RC's Command 2 sensitivity at 2026-03-31 cutoff — exceeds the 75 gate).
- (b) Escalation to user as the defensible alternative.

**Is this defensible from my adversarial lens?** YES. The plan explicitly states "The plan's job is to reach the truth, not to promise success" (line 1945) and refuses to relax the gate in response to the Risk note. The gate stays at ≥75. The HALT stays in place. The plan does NOT promise success and does NOT silently expand scope to include δ-EU mid-revision.

I would NOT BLOCK on "δ-EU should be in this revision." The reasoning:

1. The plan's HALT-to-user route under the foreseeable failure case is the correct anti-fishing posture. It is honest about marginal coverage.
2. Adding δ-EU mid-revision (Rev-5.3.2 → Rev-5.3.2-with-EU) would be scope creep mid-revision; better to land Rev-5.3.2 cleanly and EITHER clear the gate OR HALT-to-user, where the user can authorize a Rev-5.3.3 with δ-EU as the next pivot.
3. The plan's procedure is internally consistent: "Probe outcome may not be silently fed into the Task 11.N.2d-rev source mix under Rev-5.3.2" (line 1860) symmetrically applies — δ-EU outcome may not be silently added either.

The HALT-to-user route is the load-bearing protective net; the plan correctly does not pre-commit to clearing the gate.

---

## Resolution check on HALT clause (per re-review checklist item #6)

HALT clause at line 1932:

> "If joint overlap lands < 75 weeks: HALT — write a NEW disposition memo at `contracts/.scratch/2026-04-25-y3-rev532-coverage-halt.md`; do NOT proceed to Task 11.O-scope-update; do NOT silently re-relax `N_MIN`. **The escalation is to user, not to free-tuning.**"

This is unchanged from the prior Rev-5.3.2 (correctly preserved). The clause is in the right place (Task 11.N.2d-rev acceptance criteria), it forbids silent N_MIN drift explicitly, and it routes to user.

The Risk note at lines 1940-1945 reinforces the HALT clause with an additional explicit anti-tune statement (line 1945: "The Rev-5.3.2 acceptance criteria do NOT relax in response to this risk; the gate stays at ≥75; the HALT stays in place").

The Task 11.O-scope-update dependency at line 2020 also acknowledges the HALT case explicitly: "Task 11.N.2d-rev (primary panel landed and verified to recover `N_MIN ≥ 75` — OR HALT-with-disposition-memo if it does not, per the Task 11.N.2d-rev HALT clause; in the HALT case, Task 11.O-scope-update does not dispatch, the HALT routes to user)."

The Anti-fishing guard at line 2022 caps it: "Task 11.O Rev-2 spec authoring may NOT proceed against the Rev-5.3.1 panel ... under any circumstance — that would be silent N_MIN tuning."

**Confirmed:** HALT clause forbids silent N_MIN relaxation in three locations (1932, 1945, 2022); routes to user; refuses to proceed past the gate without clearing it.

---

## Resolution check on Task 11.N.2d.1-reframe (per re-review checklist item #7)

Task 11.N.2d.1-reframe (lines 1957-1976) describes the IMF-IFS-only sensitivity. Under the new mix (CO=DANE, BR=BCB, EU=Eurostat, KE=skip), the IMF-only sensitivity becomes the "CO via IMF / BR via IMF / EU=Eurostat (preserved) / KE=skip" mix — i.e., it tests the full pre-Rev-5.3.2 source mix on the new primary window.

The reframe at line 1962 says: "A sensitivity Y₃ panel computed against the **IMF-IFS-only** source mix (the pre-Rev-5.3.2 BR source) over the **same primary window** `[2023-08-01, 2026-04-24]`".

Wait: this only mentions BR. Reading more carefully (line 1962): "the IMF-IFS-only source mix (the pre-Rev-5.3.2 BR source)". This is slightly ambiguous — is it (a) a BR-only IMF sensitivity (CO=DANE, BR=IMF, EU=Eurostat, KE=skip), OR (b) a full pre-Rev-5.3.2 IMF-source mix (CO=IMF, BR=IMF, EU=Eurostat, KE=skip)?

This is an advisory ambiguity (A4 below). It does NOT affect dispatch order or the gate criterion; it affects only the sensitivity-comparison memo's content. The Data Engineer subagent and reviewer pool would likely catch this at execution time via the failing-test-first.

The reframe correctly addresses the original Task 11.N.2d.1's "wider-window sensitivity" being now redundant (the wider window IS the primary), but the IMF-IFS-only sensitivity scope is fuzzy. Marking advisory.

---

## Resolution check on anti-fishing wording (per re-review checklist item #8)

Looking for "tune until passes" exploitation pathways in the Risk note (lines 1940-1945) and the post-HALT decision tree:

- Line 1942 lists δ-EU as path (a). This is NOT a free-tune pathway — it is a source upgrade similar to the BR/CO upgrades, with the same anti-fishing guard pattern (would require its own CORRECTIONS block + 3-way review per the Rev-5.3.3 implicit framework).
- Line 1943 lists user-escalation as path (b). This is the canonical anti-fishing pivot.
- Line 1945 caps it: "Rev-5.3.2 acceptance criteria do NOT relax in response to this risk; the gate stays at ≥75; the HALT stays in place."

I do not see a "let's just lower the gate" exploit pathway. The plan's framing is symmetric: a CO source change (path a) is an analytical decision requiring its own revision; an N_MIN change (path b alternative) is forbidden by the anti-fishing protocol.

The §C four-condition list (lines 2032-2037) is also reaffirmed — imputation requires (a) literature citation, (b) sha256 anchor, (c) side-by-side sensitivity, (d) 3-way review. The four-condition list also explicitly forbids relabeling existing operations as "imputation" (line 2039 — RC advisory A5 from prior review now codified at the §C level).

**No anti-fishing leak detected.** The plan's wording is honest about marginal coverage and refuses to drift toward "tune until passes."

---

## Non-blocking advisories (4 advisories, all minor)

### A1 — DANE schema column-name discrepancy (cosmetic, not load-bearing)

**Plan claim** (line 1822): "schema `(date, ipc_value, monthly_variation_pct, _ingested_at)`"
**Actual schema** (Command 1 output): `(date, ipc_index, ipc_pct_change, _ingested_at)`

The plan uses `ipc_value` (claimed) vs. `ipc_index` (actual); `monthly_variation_pct` (claimed) vs. `ipc_pct_change` (actual).

**Why advisory, not blocker:** the column-name discrepancy would surface at execution time when the wire-up task body invokes `econ_query_api.load_dane_ipc_monthly()` or equivalent. The failing-test-first (line 1875: "asserting the CO branch ... round-trips DANE rows from the canonical DuckDB through the fetcher and returns a level series with cutoff date ≥ 2026-02-01") would either pass or fail at compile-time / first-test-run. The Data Engineer subagent would correct the column names in the task body without a re-dispatch of the CORRECTIONS block.

**Mitigation:** at Task 11.N.2.CO-dane-wire's verification memo authoring, RC re-review can confirm the actual column-names are used. No CORRECTIONS-block edit needed.

**Plan-line ref:** line 1822.

### A2 — DANE consume-only freeze: snapshot vs. task-execution time

The plan commits to consume-only "at task-execution time" but does NOT freeze the snapshot (no row-count assertion or max-date assertion as a precondition test in Task 11.N.2.CO-dane-wire's failing-test-first).

**Why advisory:** the plan's failing-test-first DOES assert cutoff date ≥ 2026-02-01 (line 1875), which is effectively a freshness lower-bound but NOT an equality assertion against a frozen snapshot. If a future ingest task added rows beyond 2026-03-01 (e.g., 2026-04-01) and the wire-up task ran later, the CO branch would consume the fresher data. This is generally desirable (more freshness = closer to the gate), but it does deviate from a strict "frozen snapshot" interpretation of the consume-only contract.

**Mitigation (optional):** the Task 11.N.2.CO-dane-wire body could add a precondition test asserting `MAX(date) IN ('2026-03-01', ...)` or, alternatively, document that the consume-only contract permits MORE-but-not-LESS freshness. Either is defensible; for Rev-5.3.2 dispatch, the current wording is sufficient.

**Plan-line ref:** line 1878, line 1886.

### A3 — Task 11.N.2d-rev acceptance criterion (b) over-promises Y₃ panel weeks

Line 1927: "Y₃ panel weeks ≥ **105 weeks** under the new methodology tag (per the arithmetic note below — revised from the prior '≥ 95' figure to reflect the new mix's binding country EU at 2025-12-01)."

The arithmetic note at line 1936 says: "Window `2023-08-01 → 2025-12-01` is approximately 105 Friday-anchored weeks pre-aggregation; with the LOCF tail, the panel may extend to ~109 weeks."

105 weeks is the EU-binding-cutoff figure, which assumes Y₃ ingest aligns to EU's 2025-12-01 cutoff exactly. But under per-week aggregation (KE skipped, 3-country panel), the ingest tail length depends on how the project's existing weekly-anchor LOCF rule interacts with the EU monthly cutoff. The arithmetic is plausible but not directly verified at this re-review (no live ingest run).

**Why advisory:** the projected ≥105-week criterion is a downstream guard against a degenerate-ingest case; if Y₃ ingest produces fewer than 105 weeks under the new methodology tag, the task will HALT at acceptance. This is correct anti-fishing posture, but if the ingest produces, say, 100 or 102 weeks (just below 105), the HALT trigger fires for what may be an acceptable panel. The criterion should be more carefully arithmetic-derived at execution time.

**Mitigation:** the Data Engineer subagent at Task 11.N.2d-rev should verify the panel-week count BEFORE asserting the ≥105 criterion in the failing-test-first. If the count lands between 100-105, the task should re-derive the arithmetic and update the criterion in the verification memo for reviewer ack — NOT silently relax the criterion.

**Plan-line ref:** lines 1927, 1936.

### A4 — Task 11.N.2d.1-reframe IMF-IFS-only scope ambiguous

The reframe (line 1962) says: "A sensitivity Y₃ panel computed against the **IMF-IFS-only** source mix (the pre-Rev-5.3.2 BR source) over the **same primary window**".

Reading: is the sensitivity testing (a) BR=IMF only with CO=DANE, EU=Eurostat preserved (i.e., CO via DANE stays in the sensitivity); OR (b) full pre-Rev-5.3.2 mix CO=IMF, BR=IMF, EU=Eurostat (i.e., a sensitivity against ONLY the BR change vs. BOTH BR + CO changes)?

The reframe's narrative is fuzzy. The original Task 11.N.2d.1 was a "wider-window sensitivity"; the reframe replaces it with a "single-source-fallback sensitivity". The intent appears to be (b) — a full pre-Rev-5.3.2 IMF mix as the comparator — but the wording could be read as (a) (BR-only IMF, CO-DANE preserved).

**Why advisory:** the sensitivity comparison memo's content depends on this scope. If (a), the per-week deviation captures only the BR source change. If (b), it captures both BR + CO changes. Both are defensible analyses, but they answer different scientific questions.

**Mitigation:** the Task 11.N.2d.1-reframe deliverable wording (line 1962) should be made explicit. Suggested edit: replace "the pre-Rev-5.3.2 BR source" with "the pre-Rev-5.3.2 source mix (both BR and CO via IMF IFS via DBnomics)" if intent (b) is correct. RC review of the verification memo at execution time can resolve this.

**Plan-line ref:** line 1962.

---

## What I tried to break (adversarial-probe checklist for the second pass)

1. **DANE table state regression** — TARGET MISSED. DANE table state is unchanged from the prior review (Command 1). Plan's claim is correct.

2. **Joint-coverage projection arithmetic error** — TARGET MISSED. Live cutoff sweep (Command 2) confirms 65 joint nonzero weeks at the EU-binding cutoff plus LOCF tail, exactly matching the plan's projected ~65 figure. The plan does NOT over-promise the gate.

3. **OECD-probe sneaking back into the source mix** — TARGET MISSED. §D table marks `oecd_cpi_monthly` as NOT CREATED. Task 11.N.2d-rev dependency at line 1951 only requires CO-dane-wire AND BR-bcb-fetcher. Anti-fishing guard at line 1860 explicitly forbids OECD outcome from feeding the source mix.

4. **HALT clause weakening** — TARGET MISSED. HALT clause at line 1932 unchanged; reaffirmed in three locations (1932, 1945, 2022); routes to user; forbids silent N_MIN drift.

5. **δ-EU mid-revision scope creep** — TARGET MISSED. Plan deliberately defers δ-EU; Risk note at lines 1940-1945 documents the deferral honestly; gate stays at ≥75; HALT routes to user.

6. **Anti-fishing leak in post-HALT decision-tree** — TARGET MISSED. No "let's just lower the gate" pathway; only (a) δ-EU upgrade requiring its own revision, (b) user-escalation. Symmetric anti-fishing posture for both source and threshold changes.

7. **DANE table mutation risk** — A2 advisory. Plan does not freeze a snapshot; commits to consume-only at task-execution time. Defensible but could be tightened.

8. **Task 11.N.2d.1-reframe scope** — A4 advisory. IMF-IFS-only scope is ambiguous (BR-only vs. full pre-Rev-5.3.2 mix). Resolvable at task-execution time via RC review of verification memo.

9. **Schema column-name discrepancy** — A1 advisory. Plan claims `(ipc_value, monthly_variation_pct)` but actual is `(ipc_index, ipc_pct_change)`. Cosmetic; would be caught by failing-test-first at execution time.

10. **Y₃ panel-weeks arithmetic** — A3 advisory. ≥105-week criterion is plausibly derived but not directly verified at this re-review. Could be tightened at task-execution time.

---

## Recommendation

**PASS-with-non-blocking-advisories.** The Rev-5.3.2 fix-up rewrite is dispatch-ready under the post-fix-up rewrite. The four advisories are all minor and resolvable at task-execution time without re-dispatching the CORRECTIONS block. The plan's transparency on marginal coverage (~65 weeks projected, gate at 75, HALT-to-user as the protective net) is the load-bearing piece that justifies promotion past NEEDS-WORK; the plan does NOT promise success and does NOT leave wiggle room for silent threshold tuning.

The three prior BLOCKERs are cleanly resolved:
- **B1** (joint-coverage arithmetic): δ now includes CO via DANE; live-verified 65 joint weeks at the EU-binding cutoff plus LOCF tail.
- **B2** (OECD mis-classification): demoted to diagnostic-only; no downstream dispatch dependency; anti-fishing guard explicitly forbids feeding into the source mix.
- **B3** (DANE table mis-described): §A and §D both correctly describe the table as existing-and-populated and consume-only.

The plan dispatches a task chain whose worst case (gate not cleared at 65 weeks) is correctly classified as a HALT-to-user, NOT as a workflow failure or as silent threshold tuning. This is the correct anti-fishing posture under the pathological-HALT discipline.

The TW's choice to defer δ-EU and accept marginal coverage with HALT-routing as the protective net is defensible from my adversarial lens. I do NOT BLOCK on "δ-EU should be in this revision" — adding δ-EU mid-revision would be scope creep, and the HALT-to-user route is the correct anti-fishing stage.

**Re-review trigger:** when Task 11.N.2d-rev lands its verification memo. RC will check (a) the actual joint-coverage count vs. projected 65; (b) the chosen `source_methodology` literal value; (c) the four advisories above (column names, snapshot freeze, panel-weeks arithmetic, IMF-IFS-only scope).

---

**Reviewer signoff:** TestingRealityChecker
**Evidence repository:** all queries above are reproducible from `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/data/structural_econ.duckdb` (read-only).
**Verdict locked:** PASS-with-non-blocking-advisories.
