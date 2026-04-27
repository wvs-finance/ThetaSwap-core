# Rev-5.3.2 CORRECTIONS Block — Reality Checker Review

**Reviewer:** TestingRealityChecker (Reality Checker lens)
**Date:** 2026-04-25 10:50 EDT
**Plan file:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (Rev-5.3.2 CORRECTIONS, lines 1789–2030)
**Disposition memo:** `contracts/.scratch/2026-04-25-y3-coverage-halt-disposition.md`
**Default verdict:** NEEDS-WORK. Promotion requires overwhelming evidence; this review found two BLOCKERs.

---

## Verdict: **BLOCK**

The Rev-5.3.2 CORRECTIONS block, as written, **cannot satisfy its own load-bearing acceptance criterion** (Task 11.N.2d-rev: "Joint nonzero X_d × Y₃ overlap ≥ 75 weeks for `carbon_basket_user_volume_usd`"). Live DuckDB queries against the canonical structural-econ database show that the maximum joint nonzero coverage achievable under path ζ as written (γ + δ-BR-only) is **47 weeks** — *lower* than the current Rev-5.3.1 state of 56 weeks and **28 weeks short of the N_MIN=75 gate**. The plan fails the disposition-memo's own §3 ζ-row prediction of "~80+ weeks" because that prediction implicitly assumed a CO source upgrade that is not in the implemented task list.

A second, independent BLOCKER: live probe of OECD direct SDMX (which the plan describes as "not yet probed") returns Colombia CPI **fresh through 2026-03**. This contradicts the plan's load-bearing premise that CO is unavoidably stuck on IMF IFS at 2025-07-01 cutoff. The OECD-probe is therefore not "non-blocking advisory" as the plan classifies it — it is the only path that lets path ζ recover N≥75. The classification is wrong; the dispatch ordering is wrong.

A third BLOCKER (data-engineering reality check): an existing DuckDB table `dane_ipc_monthly` is **already populated and current through 2026-03-01** (861 rows, ingested 2026-04-16). The plan asserts "DANE direct paths return 404" and treats DANE as "EXISTING / reuseable if a DANE-feed becomes reachable" (i.e., currently NOT reachable). That assertion is contradicted by the DuckDB state. A wired DANE feed for CO would solve the same problem the plan defers to a hypothetical Rev-5.3.3.

Until these three issues are resolved, dispatching Task 11.N.2d-rev would consume the entire fetcher-engineering budget on a BR-source upgrade that mathematically cannot satisfy the gate, then escalate via the plan's own HALT clause back to the user — wasting ~1-2 days of fetcher work the plan explicitly invokes.

---

## Blockers

### BLOCKER B1 — Joint-coverage arithmetic does not math out under path ζ as written

**Claim under review** (Task 11.N.2d-rev acceptance criterion, plan line 1887):
> "Joint nonzero X_d × Y₃ overlap for `proxy_kind = "carbon_basket_user_volume_usd"` ≥ 75 weeks — recovers the pre-committed `N_MIN = 75` from Rev-5.3.1. This is the load-bearing ζ-disposition gate."

**What the plan implements as path ζ** (per §A table at line 1816–1824):
- `PRIMARY_PANEL_START`: 2024-09-01 → 2023-08-01 (γ window swap; backward extension of Y₃ start)
- BR (Brazil) WC-CPI source: IMF IFS via DBnomics → BCB SGS direct API series 433 (δ-BR upgrade)
- CO (Colombia) WC-CPI source: **HELD on IMF IFS via DBnomics** (no δ-CO)
- EU: PRESERVED (Eurostat, already current to 2025-12)
- KE: PRESERVED (drops out)

**Y₃ panel cutoff under this mix** = min(CO=2025-07-01, BR≈2026-03-01, EU=2025-12-01) = **2025-07-01** → with weekly-anchor LOCF, the Y₃ panel ends near **2025-08-22** (the plan itself states this in line 1886: *"panel cutoff is bounded by min-of-three ≈ 2025-07-01 → 2025-08-22 weekly anchor"*).

**Live verification — current DuckDB state:**

```sql
-- Y₃ panel window (current, Rev-5.3.1 state)
SELECT MIN(week_start), MAX(week_start), COUNT(*) FROM onchain_y3_weekly;
-- → ('2024-09-13', '2025-10-24', 59)
-- (Note: current end is 2025-10-24, which already runs LOCF a few weeks past the
--  CO 2025-07-01 month-cutoff; under Rev-5.3.1 with no upgrades.)

-- X_d window
SELECT proxy_kind, MIN(week_start), MAX(week_start), COUNT(*) AS n_total,
       COUNT(*) FILTER (WHERE value_usd != 0 AND value_usd IS NOT NULL) AS n_nz
FROM onchain_xd_weekly WHERE proxy_kind='carbon_basket_user_volume_usd' GROUP BY 1;
-- → ('carbon_basket_user_volume_usd', '2024-08-30', '2026-04-03', 82, 76)

-- Existing joint nonzero (Rev-5.3.1 baseline)
SELECT COUNT(*) FROM onchain_xd_weekly x
INNER JOIN onchain_y3_weekly y ON x.week_start = y.week_start
WHERE x.proxy_kind='carbon_basket_user_volume_usd'
  AND x.value_usd != 0 AND x.value_usd IS NOT NULL;
-- → 56  (matches disposition memo §1)
```

**Live verification — projected under Rev-5.3.2 path ζ as written:**

```sql
-- Path ζ as written: CO binds at 2025-07-01 → Y₃ ends ~2025-08-22.
-- The X_d series begins 2024-08-30 (no pre-2024-08-30 X_d data exists at all,
-- because Carbon DeFi protocol on Celo only started trading at that cutoff).
-- So γ extends Y₃ backward into territory where X_d is empty — gain = 0 joint.
-- Upper bound is set by min-CO = 2025-08-22 LOCF tail.

SELECT COUNT(*) FROM onchain_xd_weekly
WHERE proxy_kind='carbon_basket_user_volume_usd'
  AND value_usd != 0 AND value_usd IS NOT NULL
  AND week_start <= '2025-08-22';
-- → 47

-- For comparison: if CO+BR both upgraded (EU binds at 2025-12-01)
SELECT COUNT(*) FROM onchain_xd_weekly
WHERE proxy_kind='carbon_basket_user_volume_usd'
  AND value_usd != 0 AND value_usd IS NOT NULL
  AND week_start <= '2025-12-31';
-- → 65

-- For comparison: if CO+BR+EU all upgraded (BR binds at 2026-03-01)
SELECT COUNT(*) FROM onchain_xd_weekly
WHERE proxy_kind='carbon_basket_user_volume_usd'
  AND value_usd != 0 AND value_usd IS NOT NULL
  AND week_start <= '2026-03-31';
-- → 76
```

**Quantified contradiction:**

| Scenario | Y₃ upper-bound | Joint nonzero X_d × Y₃ |
|---|---|---|
| Current Rev-5.3.1 baseline (no upgrades) | 2025-10-24 (LOCF runs further than monthly cutoff) | **56** |
| Path ζ as written (γ + δ-BR-only) | 2025-08-22 | **47** |
| ζ + δ-CO (CO+BR upgraded) | 2025-12-01 | **65** |
| ζ + δ-CO + δ-EU (full) | 2026-03-01 | **76** |
| Plan's stated target (Task 11.N.2d-rev acceptance) | — | ≥ **75** |

**Path ζ as written produces 47 joint weeks — *lower* than the 56-week starting state.** The disposition memo's §3 ζ-row prediction of "~80+ weeks" is correct ONLY if both δ-BR and δ-CO are implemented. The CORRECTIONS block, as written, implements δ-BR (Task 11.N.2.BR-bcb-fetcher) but explicitly HOLDS CO on IMF IFS (§A table line 1820). The acceptance criterion ≥75 is mathematically unreachable under the implemented task set.

The disposition memo also explicitly notes a parallel intuition ("X_d × Y₃ intersection ~80+ weeks → exceeds N_MIN=75" only under "γ + δ" where δ implicitly meant *both CO and BR* source upgrades). The CORRECTIONS block silently narrows δ to δ-BR-only and inherits a coverage prediction that no longer holds.

**Why this is a BLOCKER (not advisory):** the plan's own HALT clause at line 1891 ("If joint overlap lands < 75 weeks: HALT — write a NEW disposition memo …; do NOT silently re-relax `N_MIN`") guarantees that Task 11.N.2d-rev WILL HALT under path ζ as written. The plan dispatches a task it knows will fail. That is a process anti-pattern — a guaranteed second pathological-HALT cycle — and contradicts the spirit of the anti-fishing checkpoint protocol (HALT-disposition-pivot is a recovery mechanism, not a workflow stage).

**Mathematical proof** (calendar-week pencil math, independent of DuckDB):
- γ-window Y₃ weeks (2023-08-01 → 2025-08-22): 107 weeks
- X_d earliest week: 2024-08-30 (no earlier X_d data exists)
- Joint window upper-bounded by Y₃ end (2025-08-22) and lower-bounded by X_d start (2024-08-30)
- Joint calendar weeks: (2025-08-22 − 2024-08-30) / 7 = **51 calendar weeks**
- Of those 51 calendar weeks, ~4 had zero X_d trading → 47 joint nonzero weeks (matches DuckDB query)

---

### BLOCKER B2 — OECD-direct SDMX is not "non-blocking advisory"; live probe shows it returns CO CPI through 2026-03

**Claim under review** (Task 11.N.2.OECD-probe classification, plan line 1843, 1845):
> "Reviewer: Reality Checker (single-pass, advisory; **non-blocking** — the Task 11.N.2d-rev path executes regardless of OECD-probe outcome since it is BR-source-only-driven)."
> "Dependency: None. Parallel-executable with everything else in this CORRECTIONS block."

**Claim under review** (§A table line 1820):
> "OECD/MEI via DBnomics is staler than IMF IFS (cutoff 2023-12); OECD-direct SDMX endpoint not yet probed."

**Live probe — OECD direct SDMX REST endpoint:**

```
GET https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/COL.M.N.CPI.PA._T.N.GY?startPeriod=2025-01&endPeriod=2026-04&format=jsondata
```

Response: **200 OK**, returns Colombia (COL) monthly CPI observations through **2026-03** (most recent observation period).

Sample observations:
- 2026-03: 5.290032
- 2026-02: (returned)
- 2026-01: (returned)
- 2025-12, 2025-11, 2025-10, 2025-09, 2025-08, 2025-07, 2025-06, 2025-05, 2025-04, 2025-03, 2025-02, 2025-01

(Headline annual % change variant; level-series equivalent retrievable via the `IX` filter.)

**Implication:** OECD direct SDMX returns CO CPI fresh through 2026-03-01 — that is **8 months fresher** than the plan's load-bearing assumption (CO stale at 2025-07-01).

**Why this is a BLOCKER (not advisory):**

1. The Rev-5.3.2 plan's coverage arithmetic depends on CO being stale at 2025-07-01 (otherwise Y₃ panel cutoff would jump from 2025-08-22 to ~2025-12-01, giving 65 joint weeks; the gate becomes *almost* reachable from BR-only).
2. The plan classifies OECD-probe as non-blocking because it claims path ζ executes BR-source-only-driven. But path ζ executing without δ-CO yields 47 joint weeks (B1) — well below the gate. Therefore path ζ EFFECTIVELY DEPENDS ON the OECD-probe (or some other CO-source upgrade) succeeding to land the gate.
3. The plan's stated rationale for treating OECD-probe as exploratory ("if GO, a future Rev-5.3.3 wants to upgrade CO source mid-plan, that revision requires its own CORRECTIONS block + 3-way review") creates a 3-way circular blocker: (a) Rev-5.3.2 needs CO upgrade to satisfy its gate; (b) CO upgrade requires Rev-5.3.3 CORRECTIONS block; (c) Rev-5.3.3 CORRECTIONS block requires Rev-5.3.2 to land first, which requires its gate to be met. The dependency is circular as written.

**Recommendation:** EITHER fold the CO source upgrade into Rev-5.3.2 (most likely as the existing-but-unwired DANE feed — see B3) OR rescope the gate acceptance criterion ≥75 downward to the 47 weeks actually achievable, which the plan's anti-fishing protocol will not permit.

---

### BLOCKER B3 — `dane_ipc_monthly` is already populated and current through 2026-03; plan claims DANE is unreachable

**Claim under review** (§A table line 1820, 1824):
> "BanRep XLSX is gated behind PerimeterX (soft-404s); DANE direct paths return 404; OECD/MEI via DBnomics is staler than IMF IFS (cutoff 2023-12); OECD-direct SDMX endpoint not yet probed."
> "`dane_ipc_monthly` | EXISTING / reuseable if a DANE-feed becomes reachable | DANE direct (currently 404; not reachable) | Reserved for future use"

**Live verification — DuckDB state:**

```sql
SELECT MIN(date), MAX(date), COUNT(*) FROM dane_ipc_monthly;
-- → ('1954-07-01', '2026-03-01', 861)

SELECT * FROM dane_ipc_monthly ORDER BY date DESC LIMIT 6;
-- (2026-03-01, 156.94, 0.7770, 2026-04-16 18:00:22)
-- (2026-02-01, 155.73, 1.0774, 2026-04-16 18:00:22)
-- (2026-01-01, 154.07, 1.1821, 2026-04-16 18:00:22)
-- (2025-12-01, 152.27, 0.2634, 2026-04-16 18:00:22)
-- (2025-11-01, 151.87, 0.0725, 2026-04-16 18:00:22)
-- (2025-10-01, 151.76, 0.1848, 2026-04-16 18:00:22)
```

**Implication:** Colombia CPI from DANE is *already in the canonical DuckDB*, current through **2026-03-01**, with 861 historical observations (back to 1954-07-01). The data was ingested 2026-04-16. This contradicts the plan's "DANE direct paths return 404; not reachable" assertion.

**Why this is a BLOCKER:**

1. The Rev-5.3.2 plan creates a NEW BCB SGS fetcher for BR (Task 11.N.2.BR-bcb-fetcher; ~half-day of work + cumulative-index utility + fail-test-first + reproduction witness + ~1 hour 3-way review) but does NOT propose to wire the *already-landed* DANE feed for CO into `fetch_country_wc_cpi_components`. This is engineering effort allocation in inverse proportion to the data freshness gain: BR upgrade alone cannot land the gate (per B1); a CO upgrade alone (DANE wire-up + 1 minor schema hook in `y3_data_fetchers.py`'s CO dispatch path) jumps joint coverage from 47 → ~50 weeks under path ζ alone, and combined with BR yields ~65 joint weeks. Still below 75, but vastly closer.
2. The plan's pre-flight intelligence is internally inconsistent: line 1989's table classifies `dane_ipc_monthly` as "EXISTING / reuseable" while line 1820 claims DANE is "not reachable." The plan was authored without inspecting the DuckDB state.
3. Even if the user prefers BCB SGS over DANE for some reason not stated in the plan, the plan should acknowledge the DANE state as the baseline option and JUSTIFY the choice. Currently, the plan's BR-source-upgrade choice is presented as the only mid-plan option, which is misleading.

**Recommendation:** Inspect why `dane_ipc_monthly` was ingested (2026-04-16 ingest timestamp suggests prior plan work landed it). Wire CO dispatch in `y3_data_fetchers.py` to consume DANE (one-line code change in `_fetch_imf_ifs_headline_broadcast` or a parallel `_fetch_dane_ipc_broadcast`); update the §A table to reflect the upgrade; recompute joint-coverage prediction.

---

## Non-blocking advisories

### A1 — Disposition-memo §3 ζ-row prediction is more conservative than disposition-memo abstract

The disposition memo §3 ζ-row says "~110-115 weeks" Y₃ panel and "~80+ weeks joint." The §4 recommendation calls ζ "the only path that lands the original Rev-5.3.1 N_MIN=75 commitment without further relaxation." The actual coverage achievable depends on which countries get the source upgrade. The CORRECTIONS block at line 1801 ("δ alone … leaves Aug-2023→Sep-2024 pre-period unused; below the joint-coverage target unless paired with γ") and line 1799 ("γ alone … recovers coverage from 56 → ~65 weeks") use language that implies γ + δ is sufficient WITHOUT specifying that δ must mean δ-BR + δ-CO + (δ-EU). This ambiguity makes the gate target appear feasible when it is not, given the implemented task set.

**Plan-line ref:** lines 1796–1802.
**Mitigation:** name the source-upgrade scope explicitly as "δ-BR" or "δ-CO" or "δ-{BR,CO}" so a reviewer can audit the implementation gap between intent and code.

### A2 — Task 11.O-scope-update authorship is internally redundant

Line 1962 (Task 11.O-scope-update reviewers): "Code Reviewer + Reality Checker + Technical Writer (spec-review trio per `feedback_three_way_review`)."
Line 1952 (Task 11.O-scope-update subagent): "Technical Writer (spec-update authoring)."

If the Technical Writer authors the task and is also one of the three reviewers of the same authoring, the reviewer pool collapses to two independent reviewers. Per `feedback_three_way_review`, the trio assumes the author is NOT one of the three reviewers.

**Plan-line ref:** lines 1952, 1962.
**Mitigation:** dispatch Senior Developer or another author for Task 11.O-scope-update so the TW remains an independent reviewer.

### A3 — `MDES_FORMULATION_HASH` claim repeated; verify against actual file

The plan asserts `MDES_FORMULATION_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` (line 1798, 2030). The MEMORY.md note `mdes_formulation_pin` records the same hash with a slightly truncated value (`4940360dcd2987…cefa`). I did not run `sha256sum` on the source file because the relevant file path was not specified. Task 11.N.2d-rev should not consume this hash without re-validating it against `scripts/y3_compute.py` (or wherever `required_power` is canonically defined) at execution time.

**Plan-line ref:** lines 1798, 1811, 2030.
**Mitigation:** dispatch a `sha256sum` self-test as the first step of Task 11.N.2d-rev's failing-test-first.

### A4 — Task dependency DAG: Task 11.N.2.BR-bcb-fetcher and 11.N.2.OECD-probe parallel-execution claim

Line 1845: "Dependency: None. Parallel-executable with everything else in this CORRECTIONS block. Author dispatches Task 11.N.2.OECD-probe and Task 11.N.2.BR-bcb-fetcher concurrently."

Both tasks dispatch the same Data Engineer subagent. If the orchestrator is sequential per `feedback_specialized_agents_per_task`, "concurrent dispatch" actually means "sequential execution by the same agent." The claim of parallelism is operationally false.

**Plan-line ref:** line 1845.
**Mitigation:** sequence them: 11.N.2.OECD-probe FIRST (lighter — read-only HTTP probe), then 11.N.2.BR-bcb-fetcher (heavier — fetcher + cumulative-index + DuckDB schema migration). OECD-probe outcome should be allowed to *inform* whether 11.N.2.BR-bcb-fetcher proceeds or is supplanted by an OECD-direct fetcher (which would land BR fresher than BCB).

### A5 — Task 11.N.2d.2-NEW deliberate-non-task placement is fragile

Lines 1923–1947 reserve a placeholder task slot for imputation methodology but explicitly list five candidate mechanisms (LOCF, AR(p), cross-country, truncation, γ backward extension). Truncation IS the chosen path; γ backward extension IS already implemented. The other three (LOCF, AR(p), cross-country) are "off the primary path." A future revision wanting to introduce imputation has documented requirements (a)–(d) at line 1940–1944, but those requirements do NOT actually prevent a "minor edit" exploitation (e.g., a future revision could relabel γ backward extension as an "imputation mechanism" and silently extend the panel forward).

**Plan-line ref:** lines 1923–1947.
**Mitigation:** strengthen the reservation by listing the EXACT panel-construction operations that ARE permitted under Rev-5.3.2 ("γ backward extension into existing-data territory; truncation at min-country cutoff; idempotent UPSERT under new `source_methodology` tag") and forbidding ANY operation that materially changes the response variable Y₃ values for any week present in the prior `y3_v1` panel.

### A6 — `source_methodology` literal-vs-schema discipline asks reviewers to wing it

Lines 1823, 1882, 1890, 1906, 1910 repeatedly say "literal value finalized at implementation; the schema is described, not the literal." This places a non-trivial reviewer burden at execution time: reviewers must verify, post-hoc, that whatever the literal turned out to be is consistent with §A and §B. There is no in-plan mechanism for the orchestrator to surface the chosen literal back to the reviewers for confirmation before commit.

**Plan-line ref:** lines 1823, 1882, 1890, 1906, 1910.
**Mitigation:** require Task 11.N.2d-rev's verification memo (line 1883 item d) to explicitly call out the chosen literal and require reviewer ack of the literal before Task 11.O-scope-update dispatches.

---

## Verification trail (every command run + output)

### Command 1 — confirm Y₃ DuckDB state matches disposition memo §1

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom
source contracts/.venv/bin/activate
python -c "
import duckdb
con = duckdb.connect('contracts/data/structural_econ.duckdb', read_only=True)
print(con.sql('SELECT MIN(week_start), MAX(week_start), COUNT(*) FROM onchain_y3_weekly').fetchall())
print(con.sql('''
SELECT
  COUNT(*) FILTER (WHERE copm_diff IS NOT NULL) AS co_n,
  COUNT(*) FILTER (WHERE brl_diff IS NOT NULL) AS br_n,
  COUNT(*) FILTER (WHERE kes_diff IS NOT NULL) AS ke_n,
  COUNT(*) FILTER (WHERE eur_diff IS NOT NULL) AS eu_n
FROM onchain_y3_weekly
''').fetchall())
"
```

Output:
```
[(datetime.date(2024, 9, 13), datetime.date(2025, 10, 24), 59)]
[(59, 59, 0, 59)]
```

**Confirms:** disposition memo §1 (59-week 3-country panel ending 2025-10-24, KE absent).

### Command 2 — X_d window per proxy_kind

```bash
python -c "
import duckdb
con = duckdb.connect('contracts/data/structural_econ.duckdb', read_only=True)
print(con.sql('''
SELECT proxy_kind, MIN(week_start), MAX(week_start), COUNT(*) AS n_total,
       COUNT(*) FILTER (WHERE value_usd != 0 AND value_usd IS NOT NULL) AS n_nonzero
FROM onchain_xd_weekly GROUP BY proxy_kind ORDER BY proxy_kind
''').fetchall())
"
```

Output (key rows):
```
('carbon_basket_user_volume_usd', 2024-08-30, 2026-04-03, 82, 76)
('b2b_to_b2c_net_flow_usd', 2024-10-04, 2026-04-24, 79, 70)
('net_primary_issuance_usd', 2024-09-20, 2026-04-24, 84, 66)
```

**Confirms:** X_d earliest week 2024-08-30. No X_d data before this date — γ backward extension into pre-2024-08-30 gains 0 joint weeks.

### Command 3 — joint nonzero coverage by cutoff

```bash
python -c "
import duckdb
con = duckdb.connect('contracts/data/structural_econ.duckdb', read_only=True)
for cutoff in ['2025-08-22', '2025-10-24', '2025-12-31', '2026-03-31']:
    n = con.sql(f\"\"\"
        SELECT COUNT(*) FROM onchain_xd_weekly
        WHERE proxy_kind='carbon_basket_user_volume_usd'
          AND value_usd != 0 AND value_usd IS NOT NULL
          AND week_start <= '{cutoff}'
    \"\"\").fetchone()[0]
    print(cutoff, '→', n)
"
```

Output:
```
2025-08-22 → 47   (path ζ as written: CO binds, Y₃ ends here)
2025-10-24 → 56   (current Rev-5.3.1 baseline)
2025-12-31 → 65   (CO+BR upgraded: EU binds at 2025-12-01)
2026-03-31 → 76   (CO+BR+EU all upgraded: BR binds at 2026-03)
```

**Confirms BLOCKER B1:** path ζ as written → 47 joint weeks; gate ≥75 → mathematically unreachable without CO upgrade.

### Command 4 — calendar-week sanity check (independent of DuckDB)

```bash
python -c "
from datetime import date
for label, start, end in [
    ('γ-window Y₃ weeks (Aug-2023 → Aug-2025)', date(2023,8,1), date(2025,8,22)),
    ('JOINT path ζ as written', date(2024,8,30), date(2025,8,22)),
    ('JOINT CO+BR upgraded', date(2024,8,30), date(2025,12,1)),
    ('JOINT CO+BR+EU upgraded', date(2024,8,30), date(2026,3,1))]:
    print(label, '→', (end-start).days // 7, 'weeks')
"
```

Output:
```
γ-window Y₃ weeks (Aug-2023 → Aug-2025) → 107 weeks
JOINT path ζ as written → 51 weeks (calendar)
JOINT CO+BR upgraded → 65 weeks (calendar)
JOINT CO+BR+EU upgraded → 78 weeks (calendar)
```

**Confirms:** the disposition-memo §3 ζ-row "~80+ weeks" prediction is correct ONLY under full CO+BR+EU upgrade. Under BR-only (the implemented task set), gate cannot be reached.

### Command 5 — BCB SGS API live probe (BR series 433)

```
GET https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial=01/01/2026&dataFinal=24/04/2026
```

Output:
```
| Date       | Value |
|------------|-------|
| 01/03/2026 | 0.88  |
| 01/02/2026 | 0.70  |
| 01/01/2026 | 0.33  |
```

**Confirms:** BCB SGS endpoint is reachable, no auth required, returns 2026-03 (March 2026) IPCA monthly variation. The plan's BR-source-upgrade pre-flight intelligence is correct on the source-availability dimension.

```
GET https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/3?formato=json
```

Output: same three records (2026-01, 2026-02, 2026-03). Endpoint stable.

### Command 6 — OECD direct SDMX live probe (CO CPI)

```
GET https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/COL.M.N.CPI.PA._T.N.GY?startPeriod=2025-01&endPeriod=2026-04&format=jsondata
```

Output:
```
Most Recent Observation Date: 2026-03 (March 2026)
Sample values:
- 2026-03: 5.290032
- 2025-04: 5.162292
- 2025-03: 5.089996
Observation periods: 2025-01..2025-12, 2026-01..2026-03 (15 months)
```

**Confirms BLOCKER B2:** OECD direct SDMX returns CO CPI through 2026-03 — 8 months fresher than IMF IFS via DBnomics. The plan's "not yet probed" assertion is now resolved as GO.

### Command 7 — `dane_ipc_monthly` DuckDB inspection

```bash
python -c "
import duckdb
con = duckdb.connect('contracts/data/structural_econ.duckdb', read_only=True)
print(con.sql('SELECT MIN(date), MAX(date), COUNT(*) FROM dane_ipc_monthly').fetchall())
print(con.sql('SELECT * FROM dane_ipc_monthly ORDER BY date DESC LIMIT 6').fetchall())
"
```

Output:
```
[(datetime.date(1954, 7, 1), datetime.date(2026, 3, 1), 861)]
Latest 6 rows:
(2026-03-01, 156.94, 0.7770, ingested 2026-04-16 18:00:22)
(2026-02-01, 155.73, 1.0774, ingested 2026-04-16 18:00:22)
(2026-01-01, 154.07, 1.1821, ingested 2026-04-16 18:00:22)
(2025-12-01, 152.27, 0.2634, ingested 2026-04-16 18:00:22)
(2025-11-01, 151.87, 0.0725, ingested 2026-04-16 18:00:22)
(2025-10-01, 151.76, 0.1848, ingested 2026-04-16 18:00:22)
```

**Confirms BLOCKER B3:** DANE CPI for Colombia is ALREADY in the canonical DuckDB, fresh through 2026-03-01, ingested 9 days before the Rev-5.3.2 CORRECTIONS block was authored. The plan's "DANE direct paths return 404; not reachable" assertion is contradicted by direct database inspection.

### Command 8 — fetcher dispatch inspection

```bash
grep -n "fetch_country_wc_cpi_components\|IMF\|DBnomics\|imf_ifs\|dane" \
  /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/y3_data_fetchers.py
```

Output (key lines):
```
72: # IMF IFS headline CPI (monthly index, M.{country}.PCPI_IX)
73: "CO": "IMF/IFS/M.CO.PCPI_IX",
74: "BR": "IMF/IFS/M.BR.PCPI_IX",
75: "KE": "IMF/IFS/M.KE.PCPI_IX",
…
241: def fetch_country_wc_cpi_components(country, start, end) -> pd.DataFrame
…
257: * CO/BR/KE: IMF IFS headline CPI via DBnomics — split components
…
306: def _fetch_imf_ifs_headline_broadcast(country, start, end)
```

(No mention of `dane_ipc_monthly` or `DANE` anywhere in `y3_data_fetchers.py`.)

**Confirms:** the existing fetcher dispatch path for CO is hardcoded to IMF IFS via DBnomics. A DANE wire-up is a small code change but is not implemented today.

---

## What I tried to break

Following the Reality Checker brief's adversarial-probe checklist:

1. **Coverage arithmetic stress-test** — TARGET HIT (B1). Path ζ as written produces 47 joint weeks, well below the 75 gate. The disposition-memo's "~80+ weeks" prediction holds only under full δ; the CORRECTIONS block silently narrows δ to δ-BR-only.

2. **OECD-probe outcome unknown** — TARGET HIT (B2). Live probe returns GO. The plan classifies OECD-probe as non-blocking, but path ζ EFFECTIVELY DEPENDS on it (or some other CO upgrade) to land the gate.

3. **γ-window-swap arithmetic** — VERIFIED. γ extends Y₃ backward into pre-2024-08-30 territory where X_d is empty. γ alone gains 0 joint weeks. This matches the disposition memo §3 (γ alone: 56 → ~65 weeks, but only because the original 56-week boundary was constrained by Y₃'s upper bound, not by γ).

4. **BCB SGS feasibility** — VERIFIED. Endpoint reachable, no auth, returns 2026-03 freshness. δ-BR is a viable source upgrade.

5. **Task dependency cycle check** — A4 advisory: claimed parallelism between 11.N.2.OECD-probe and 11.N.2.BR-bcb-fetcher is operationally false (both dispatch the same Data Engineer subagent). Functionally non-blocking but should be sequenced.

6. **Imputation discipline** — A5 advisory. Reservation language is mostly defensive but doesn't forbid relabeling existing operations as "imputation" in a future revision.

7. **DuckDB-invariant claims** — TARGET HIT (B3). The §D additive-table list claims `dane_ipc_monthly` is "EXISTING / reuseable if a DANE-feed becomes reachable." The DuckDB shows DANE is already populated and current. The list is internally inconsistent with reality.

8. **Specific items the TW flagged for your attention** — "Reality Checker must sanity-check the cutoff arithmetic at execution time and challenge if landed values diverge." DONE. Cutoff arithmetic does not produce N≥75 under path ζ as written; challenged at this review.

---

## Recommendation

**HALT Rev-5.3.2 dispatch until at least one of the following is resolved:**

1. **(Preferred)** Fold a CO source upgrade into Rev-5.3.2 — either wire the existing `dane_ipc_monthly` table (B3 mitigation, ~30-minute code change) OR add an OECD-direct CO fetcher (B2 mitigation, similar effort to BCB SGS). Recompute joint-coverage prediction; gate ≥75 becomes near-feasible (CO+BR+EU all upgraded → 76 joint weeks).

2. **(Acceptable)** Restate path ζ as δ-{BR + CO} (both source upgrades) with explicit task additions for CO; recompute the prediction; commit. The plan's narrative ("γ + δ") then matches the implementation.

3. **(Anti-fishing-clean but slow)** Author a Rev-5.3.3 BEFORE Rev-5.3.2 dispatches, folding CO upgrade into 5.3.2 retroactively. The plan's stated procedure (5.3.3 fires AFTER OECD-probe returns GO) creates a dispatch ordering that wastes BR-fetcher work. Better to merge.

4. **(Not recommended)** Lower the gate to 47 weeks. The plan explicitly forbids this at line 1798 ("REJECTED — would compound the Rev-5.3.1 80→75 relaxation into 'tune until it passes.'"). I agree with the plan's anti-fishing position; this option is mentioned for completeness only.

The cleanest path is option 1: a single ~half-day data-engineer task to wire `dane_ipc_monthly` into the CO branch of `fetch_country_wc_cpi_components`, plus a one-line update to the §A table and the §D additive-table list. This is far smaller than the BR fetcher Rev-5.3.2 already authorizes, and it lands the gate.

---

## Final note

Reality Checker default is NEEDS-WORK. Promotion to PASS requires overwhelming evidence; this review found three independent, evidence-backed BLOCKERs against the load-bearing acceptance criterion. Verdict locked at **BLOCK**.

The plan's anti-fishing process discipline (HALT-disposition-pivot-CORRECTIONS-review) is sound. The execution of the discipline in Rev-5.3.2 (the specific source-mix chosen for path ζ) is wrong on the data — it dispatches a task the math says will HALT. Fixing this requires rescoping path ζ to include a CO source upgrade, not running it as written.

---

**Reviewer signoff:** TestingRealityChecker
**Evidence repository:** all queries above are reproducible from `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/data/structural_econ.duckdb` (read-only) and from public BCB SGS / OECD SDMX endpoints.
**Re-review trigger:** when the orchestrator either (a) folds CO upgrade into Rev-5.3.2, OR (b) provides a written rebuttal showing how path ζ as written can satisfy gate ≥75. Either path requires re-dispatch of all three reviewers.
