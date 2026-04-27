# Code Review — Task 11.N.2.CO-dane-wire (commit `f7b03caac`)

**Reviewer:** Code Reviewer agent
**Date:** 2026-04-25
**Scope:** Single commit `f7b03caac` on branch `phase0-vb-mvp`, 4 files modified.
**Plan ref:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` §Task 11.N.2.CO-dane-wire (line 1864)
**Design ref:** `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` §3, §8, §10 row 2, §7
**Verdict:** **PASS-with-non-blocking-advisories**

---

## Summary

The commit cleanly wires the existing `dane_ipc_monthly` DuckDB table into the CO branch of `fetch_country_wc_cpi_components` via a new opt-in `conn` kwarg. The change is genuinely additive at the dispatch layer: no existing function bodies were modified, the IMF-IFS-via-DBnomics path is byte-exact preserved as the sensitivity comparator for Task 11.N.2d.1-reframe, and the consumer DataFrame shape is preserved across both code paths. The `dane_ipc_monthly` table is consumed read-only — zero DDL, zero DML, all DuckDB connections opened with `read_only=True` and closed in `try/finally`. The new `DaneIpcMonthly` dataclass and `load_dane_ipc_monthly` reader follow the project-wide `frozen=True, slots=True` + `_check_table` + `_date_filter` pattern verbatim. TDD discipline is evident from the test design (3 mutation tests asserting the new `conn`-kwarg contract would fail on the pre-commit `TypeError`; 6 reader/preservation tests pass independent of the wire-up). The verification memo is honest about the 2 pre-existing failures in `scripts/tests/remittance/test_cleaning_remittance.py` and correctly attributes them to commit `28d76cbb0` (out of scope per `feedback_agent_scope`).

I have **3 non-blocking advisories** below. None of them block merge; all are improvement opportunities for follow-up work.

---

## Section-by-section findings (mapped to the 10 review angles)

### 1. Consume-only discipline — PASS

**Verified:**
- `grep -nE "INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE"` against all 4 in-scope files returns zero hits.
- `load_dane_ipc_monthly` reads the table via the canonical `_check_table` + `_date_filter` helpers — same pattern as `load_fed_funds_weekly`, `load_banrep_ibr_weekly`, and the 9 on-chain loaders introduced under Task 11.M.5.
- The connection is opened in test code with `duckdb.connect(str(_STRUCTURAL_ECON_DB), read_only=True)` (`test_y3_co_dane_wire.py:64`). No mutation primitive is callable on a `read_only=True` connection — DuckDB will hard-fail any DDL or DML against such a handle. This is belt-and-suspenders against the consume-only contract.
- The SELECT statement in `load_dane_ipc_monthly` is parameterized on dates (`?` placeholders) and the column list is hard-coded — no dynamic SQL surface that could mutate schema.

The wire-up genuinely is consume-only.

### 2. TDD discipline preserved — PASS

The 3-red → 9-green sequence is structurally evident:

- **Pre-implementation red set (3 tests):** all three tests in Step B (`test_fetch_country_wc_cpi_components_co_via_dane_*`) call `fetch_country_wc_cpi_components(..., conn=conn)`. Pre-commit, `fetch_country_wc_cpi_components` accepted only `(country, start, end)` positional — passing `conn=` would raise `TypeError: got an unexpected keyword argument 'conn'`. The verification memo §"TDD compliance" records this failure mode verbatim.
- **Pre-implementation green set (6 tests):** Step A's 4 reader tests + Step C's 2 preservation tests do not depend on the new dispatch path. Step A would actually have been red prior to the `DaneIpcMonthly` + `load_dane_ipc_monthly` landing, but the verification memo notes (§"File scope per `feedback_agent_scope`") that those were pre-staged in an earlier subagent stream — so for this specific commit the 6-green starting state is consistent.

**Tests assert real behavior, not just import success:**
- `test_load_dane_ipc_monthly_returns_tuple_of_frozen_dataclasses` asserts `len(rows) > 0`, `isinstance(r0, DaneIpcMonthly)`, AND that mutation raises (`with pytest.raises(...)`). This is genuine behavioral coverage.
- `test_fetch_country_wc_cpi_components_co_dane_values_match_live_table` round-trips DANE rows through the reader AND through the fetcher, then asserts `abs(got - expected) < 1e-12`. This is real-data integration per `feedback_real_data_over_mocks`.
- `test_fetch_country_wc_cpi_components_co_dane_returns_4_components` verifies the headline-broadcast invariant per row (`food == energy == housing == transport`).

The test design is what TDD should look like — specific, behavioral, real-data, with no dummy assertions.

### 3. IMF-IFS path preservation — PASS (byte-exact verified)

`git diff f7b03caac~1 f7b03caac -- contracts/scripts/y3_data_fetchers.py` shows zero deletion (`-`) lines inside the `_fetch_imf_ifs_headline_broadcast` function body. The only proximate change is a context line at the function's closing `)` shown in the diff hunk header — no behavior change.

`test_fetch_imf_ifs_headline_broadcast_function_remains_callable` locks in the signature `(country, start, end)`. `test_fetch_country_wc_cpi_components_co_without_conn_uses_imf_path` monkeypatches the IMF-IFS function to a sentinel and asserts the dispatch hits it when `conn` is None — this contract test will **break the build** if a future refactor accidentally re-routes CO-without-conn elsewhere. Excellent guard for Task 11.N.2d.1-reframe's downstream consumption.

### 4. Headline-broadcast invariant — PASS

The new `_fetch_dane_headline_broadcast` constructs the DataFrame by referencing the same `levels` list four times:

```python
levels = [r.ipc_index for r in rows]
...
"food_cpi": levels,
"energy_cpi": levels,
"housing_cpi": levels,
"transport_cpi": levels,
```

This is structurally identical to `_fetch_imf_ifs_headline_broadcast` (which references `headline["value"]` four times). Per-row equality is enforced by construction — there is no code path where the four columns diverge for a single row.

The test `test_fetch_country_wc_cpi_components_co_via_dane_returns_4_components` asserts the invariant on the last row of the smoke-window output. The smoke-test memo §(a) confirms the live last row reads `food == energy == housing == transport == 156.94` for 2026-03-01.

### 5. Type discipline — PASS

`DaneIpcMonthly`:
- `@dataclass(frozen=True, slots=True)` — matches the 17 prior dataclass declarations in `econ_query_api.py` (positions 52, 67, 81, 96, 769, 828, 846, 865, 890, 903, 915, 927, 943, 953, 1080, 1274, 1374).
- All three fields fully typed: `date: date`, `ipc_index: float`, `ipc_pct_change: float | None`.
- `ipc_pct_change` is `float | None` to honor the natural NULL of the earliest series row — surfaced as `None` rather than synthesised zero. Correct decision; documented in the docstring; consistent with the project-wide preference for natural representation.

`load_dane_ipc_monthly`:
- Returns `tuple[DaneIpcMonthly, ...]` — same return shape as `load_fed_funds_weekly`, `load_banrep_ibr_weekly`.
- `start: date | None = None, end: date | None = None` — same default-`None` pattern as the rest of the loader family.
- No inheritance, no mutation, no global state. Pure function over the connection handle.

`fetch_country_wc_cpi_components`:
- The new `conn` kwarg uses the `*,` keyword-only marker — correct: `conn` cannot be accidentally bound positionally by callers used to the prior 3-arg signature.
- The forward-reference type annotation `"duckdb.DuckDBPyConnection | None"` (string-form) paired with `if TYPE_CHECKING: import duckdb` is the right pattern: callers that don't have `duckdb` installed (none in this repo, but the principle is correct) won't pay the import cost; static type-checkers still see the annotation.

All three follow the `functional-python` skill conventions.

### 6. `conn` kwarg design — PASS-with-advisory-A1

**API surface is clean:**
- Keyword-only marker (`*,`) prevents positional misuse.
- `Optional[conn]` with a `None` default preserves the prior 3-arg call sites byte-exact — no caller in `econ_pipeline.py` or elsewhere needs to change to keep working under the IMF-IFS path.

**Dispatch logic is correct:**
```python
if country == "EU":
    return _fetch_eu_hicp_split(start, end)
if country == "CO" and conn is not None:
    return _fetch_dane_headline_broadcast(conn, start, end)
return _fetch_imf_ifs_headline_broadcast(country, start, end)
```

The `country == "CO" and conn is not None` guard is the only branch that consumes `conn`. EU does not consume `conn` (its source is Eurostat HICP via DBnomics, not DuckDB). BR/KE fall through to IMF IFS. So a caller that passes `conn=conn` for BR or KE silently has the `conn` ignored — by design under Rev-5.3.2 (per the docstring: "Other branches ignore it, preserving backward compatibility").

**Advisory A1 (NON-BLOCKING):** the silent-ignore behavior is documented in the docstring but not asserted by a test. If Task 11.N.2.BR-bcb-fetcher (the next task in the sequential stream) ever wants to consume `conn` for BR, a caller might already be passing `conn=conn` for BR believing it's a no-op — and the BR branch would silently start consuming it. This isn't a problem for the current commit (BR branch ignores `conn` per design), but a one-line test asserting `fetch_country_wc_cpi_components("BR", ..., conn=conn)` raises if the BR branch is ever rewired without explicit acknowledgment would future-proof this. Defer to the BR-fetcher task.

### 7. Pre-existing failures — PASS

Verified via `git log --oneline -- contracts/scripts/tests/remittance/test_cleaning_remittance.py | head -5`:

```
28d76cbb0 feat(remittance): cleaning.py extension — load_cleaned_remittance_panel (V1: primary-RHS only), additive to Rev-4
```

Commit `28d76cbb0` predates `f7b03caac`. The DE's verification memo §"Pre-existing-failure disclosure" correctly identifies the root cause (stale `pytest.raises(FileNotFoundError)` assertion that was sound when written but became obsolete after the fixture landed at `939df12e1`). The DE's choice to disclose-not-fix is the right call under `feedback_agent_scope` — the fix is owned by a separate stream (the Phase-A.0 remittance stream, now CLOSED at `2317f72a5`).

The DE was correct: **out of scope.** Flagging it transparently in the commit message + verification memo is exactly the right disposition.

### 8. `feedback_agent_scope` compliance — PASS

`git diff f7b03caac~1 f7b03caac --name-only` returns exactly 4 files:

```
contracts/.scratch/2026-04-25-co-dane-wireup-result.md
contracts/scripts/econ_query_api.py
contracts/scripts/tests/inequality/test_y3_co_dane_wire.py
contracts/scripts/y3_data_fetchers.py
```

These are exactly the files in the agent's brief. No drift into `docs/superpowers/specs/`, `docs/superpowers/plans/`, `src/`, `test/*.sol`, or `foundry.toml`. The `dane_ipc_monthly` table itself is untouched (no migration script, no `econ_pipeline.py` change). Compliant.

### 9. Security / performance — PASS-with-advisories-A2-A3

**Security:**
- All DuckDB queries are parameterized via `?` placeholders + `_date_filter`'s param list. No string interpolation of user-controlled input. SQL injection surface = zero.
- The DuckDB connection is opened with `read_only=True` in tests; production callers (e.g., `econ_pipeline.py` ingest scripts) should also adopt this — though this commit does not add a production caller of the new `conn=conn` path, so the read_only contract is enforceable at the call site of Task 11.N.2d-rev (the next downstream task).

**Performance:**
- The query is `SELECT date, ipc_index, ipc_pct_change FROM dane_ipc_monthly WHERE date >= ? AND date <= ? ORDER BY date`. The `dane_ipc_monthly` table is 861 rows; even a full scan is sub-millisecond. No N+1 risk; no unindexed-on-large-table risk.
- The `[r.ipc_index for r in rows]` + `[r.date for r in rows]` list comprehensions in `_fetch_dane_headline_broadcast` walk the rows tuple twice. For 861 rows this is irrelevant (O(n) twice = O(n)), but for cleanliness a single-pass `dates, levels = zip(*((r.date, r.ipc_index) for r in rows))` would be marginally cleaner. **Advisory A2 (NON-BLOCKING):** flagged for stylistic consistency, not for performance. Don't change.

**Resource lifecycle:**
- The reader does NOT open or close the connection — it accepts a passed-in handle. This is the right separation of concerns: connection lifetime is the caller's responsibility. All test sites correctly wrap the call in `try/finally: conn.close()`. Production callers (Task 11.N.2d-rev's ingest path) should follow the same pattern; the docstring of `load_dane_ipc_monthly` could optionally note "Caller owns connection lifetime" as a hint. **Advisory A3 (NON-BLOCKING):** docstring nit. Don't change.

### 10. No CHECK-constraint or schema mutation on `dane_ipc_monthly` — PASS

The commit does not touch `dane_ipc_monthly`'s schema. There is no `ALTER TABLE`, no `CREATE TABLE`, no migration script. The verification memo §"Acceptance criteria checklist" rows 5-6 ("`dane_ipc_monthly` table consume-only — no schema mutation" / "Rev-4 `decision_hash` byte-exact preserved") are honest. Rev-4 `decision_hash` is preserved by construction (no schema change anywhere).

The ingest schema cited in the comment block at `econ_query_api.py:758-762` (`date DATE PK, ipc_index DOUBLE, ipc_pct_change DOUBLE, _ingested_at TIMESTAMP`) is the live schema observed at `contracts/data/structural_econ.duckdb` and referenced for documentation — not declared by this commit.

---

## Non-blocking advisories (consolidated)

**A1 (kwarg silent-ignore on BR/KE):** The current dispatch silently ignores `conn` for non-CO countries. Documented in the docstring, untested. When Task 11.N.2.BR-bcb-fetcher wires BR to consume `conn`, add a regression test that locks in BR's pre-rewire silent-ignore behavior to prevent silent drift if the wire-up is ever reverted. Defer to the BR-fetcher task.

**A2 (single-pass extraction stylistic nit):** `[r.ipc_index for r in rows]` + `[r.date for r in rows]` walks the tuple twice. A single-pass `zip(*...)` would be marginally cleaner. Don't change for this commit; flagged only for the next refactor pass.

**A3 (connection-lifetime docstring nit):** `load_dane_ipc_monthly`'s docstring could note "Caller owns connection lifetime" to mirror the implicit contract. Don't change for this commit; pure documentation enhancement.

---

## Acceptance against the plan body (line 1864 onward)

| Plan acceptance criterion | Status | Evidence |
|---|---|---|
| Failing-test-first (verify red, then green) | **PASS** | 3 red on `TypeError(unexpected kwarg 'conn')` → 9 green. Verification memo §"TDD compliance" records the verbatim red message. |
| Real-data integration test asserts cutoff ≥ 2026-02-01 | **PASS** | `test_load_dane_ipc_monthly_cutoff_at_least_2026_02_01` + `test_fetch_country_wc_cpi_components_co_via_dane_cutoff_ge_2026_02_01`. Live cutoff = 2026-03-01 per memo §(a). |
| Existing tests under `scripts/tests/inequality/` remain green | **PASS** | Memo: 66 passed, 1 skipped in inequality suite. |
| `pytest contracts/scripts/tests/` exits 0 | **PARTIAL — but DE-disclosed transparency** | 1000 pass, 7 skip, 2 fail; the 2 fails are pre-existing in `scripts/tests/remittance/test_cleaning_remittance.py` per `28d76cbb0`, out of scope per `feedback_agent_scope`. The transparency-not-bypass disposition is correct. |
| `dane_ipc_monthly` consume-only — no schema mutation | **PASS** | Zero DDL/DML in any in-scope file; `read_only=True` connections in tests. |
| Rev-4 `decision_hash` byte-exact preserved | **PASS** | No schema change anywhere; precondition trivially holds. |
| Y₃ design doc §10 row 2 broadcast pattern preserved | **PASS** | `_fetch_dane_headline_broadcast` is structurally identical to `_fetch_imf_ifs_headline_broadcast`; same DataFrame shape; per-row equality enforced by construction. |

---

## Final verdict

**PASS-with-non-blocking-advisories**

The commit is correct, minimal, well-tested, and fully documented. The DE held the consume-only contract, preserved the IMF-IFS comparator path byte-exact for downstream sensitivity work, and disclosed the 2 out-of-scope test failures with an honest root-cause trace. The 3 advisories are improvement opportunities, not gating issues — none of them affect Rev-4 `decision_hash` preservation, the consumer contract of `fetch_country_wc_cpi_components`, or the downstream Task 11.N.2d-rev / Task 11.N.2d.1-reframe consumption paths.

Recommend: **proceed to the parallel Reality Checker + Senior Developer reviews**, then dispatch Task 11.N.2.BR-bcb-fetcher (the heavier of the two CO/BR fetcher tasks) per the sequential stream order in the plan.

---

## Files reviewed (absolute paths)

- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/y3_data_fetchers.py`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/econ_query_api.py`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/tests/inequality/test_y3_co_dane_wire.py`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-co-dane-wireup-result.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (plan body lines 1864-1888)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` (§3, §8, §10 row 2)
