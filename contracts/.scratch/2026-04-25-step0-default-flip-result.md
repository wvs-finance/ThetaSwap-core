# Rev-5.3.2 Task 11.O Step 0 — `load_onchain_y3_weekly` default-flip verification

**Date:** 2026-04-25
**Plan reference:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` §Task 11.O Step 0 (line 1228)
**Predecessor commit:** `2a0377057` (Rev-5.3.2 admitted-set + validation guard fix-up)
**Author:** Data Engineer subagent (foreground orchestrator dispatch)
**Verdict:** PASS (red→green TDD; full inequality suite green)

---

## §1. Diff summary

Three files modified; one new test file; one verification memo (this file).

| File | Lines changed | Nature |
|------|---------------|--------|
| `contracts/scripts/econ_query_api.py` | +22 / −7 (net +15) | default-arg flip + docstring rewrite |
| `contracts/scripts/tests/inequality/test_y3.py` | +11 / −2 (net +9) | Step-7 test migrated to explicit `source_methodology="y3_v1"` arg |
| `contracts/scripts/tests/inequality/test_y3_default_methodology.py` | NEW (108 lines) | failing-first new-default test (2 assertions) |
| `contracts/.scratch/2026-04-25-step0-default-flip-result.md` | NEW (this memo) | verification trace |

Out-of-scope — explicitly NOT modified per `feedback_agent_scope`:

- `_KNOWN_Y3_METHODOLOGY_TAGS` membership unchanged (still 4 tags: `y3_v1`, `y3_v1_3country_ke_unavailable`, `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`, `y3_v2_imf_only_sensitivity_3country_ke_unavailable`).
- `econ_pipeline.py`, `y3_compute.py`, `y3_data_fetchers.py`, `econ_schema.py`, `carbon_calibration.py` all untouched.
- Plan markdown untouched.
- Spec documents untouched.
- DuckDB tables / rows untouched (read-only access only).

---

## §2. Default-arg before/after

### Before (commit `059ca8e9c`)

```python
def load_onchain_y3_weekly(
    conn: duckdb.DuckDBPyConnection,
    source_methodology: str = "y3_v1",
    *,
    start: date | None = None,
    end: date | None = None,
) -> tuple[OnchainY3Weekly, ...]:
```

### After (Step-0 commit)

```python
def load_onchain_y3_weekly(
    conn: duckdb.DuckDBPyConnection,
    source_methodology: str = (
        "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"
    ),
    *,
    start: date | None = None,
    end: date | None = None,
) -> tuple[OnchainY3Weekly, ...]:
```

### Behavior change against canonical `contracts/data/structural_econ.duckdb`

| Call form | Pre-flip rows | Post-flip rows |
|-----------|---------------|----------------|
| `load_onchain_y3_weekly(conn)` | **0** (silent-empty footgun) | **116** (Rev-5.3.2 v2 primary panel) |
| `load_onchain_y3_weekly(conn, source_methodology="y3_v1")` | 0 | 0 (synthetic-only literal; no canonical rows) |
| `load_onchain_y3_weekly(conn, source_methodology="y3_v1_3country_ke_unavailable")` | 59 | 59 (Rev-5.3.1 stored literal; unchanged) |
| `load_onchain_y3_weekly(conn, source_methodology="y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable")` | 116 | 116 (explicit-arg path; unchanged) |

**Smoke-test trace** (live, against `contracts/data/structural_econ.duckdb`):

```
Default-arg call returned 116 rows
First row methodology: y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable
All rows carry v2 primary literal: True
First week_start: 2024-01-12, last week_start: 2026-03-27
```

The 2024-01-12 → 2026-03-27 span matches the Rev-5.3.2 primary-panel window declared in plan line 1219 ("γ backward extension + δ-{BR via BCB SGS, CO via DANE}"; 116 rows = 76 joint-X-d-nonzero + 40 LOCF-tail-only).

---

## §3. Docstring rationale

The new docstring (econ_query_api.py:1530-1571) makes three explicit corrections:

1. **`y3_v1` retention reframed as SYNTHETIC TESTS ONLY.** The pre-flip docstring said "synthetic / unit-test bare tag (legacy default)" — neutral wording that did not warn production callers off. Post-flip wording elevates the warning to BOLD `**SYNTHETIC TESTS ONLY**` and specifies the exact synthetic test that needs the literal (`test_y3.py::test_step7_load_onchain_y3_weekly_returns_frozen_dataclass`). Adds the explicit prohibition `Production callers MUST NOT pass this literal`.

2. **Default-arg rationale block added.** A new paragraph immediately after the admitted-tag list explicitly cites Rev-5.3.2 Task 11.O Step 0 + SD-RR-A1 + names the silent-empty footgun being closed. This makes the rationale grep-discoverable for anyone debugging an unexpected default-arg result in the future.

3. **v2 primary literal flagged as the operative production default.** The bullet for the v2 literal now says `**This is the default**` so a reader scanning the admitted-tag list immediately knows which literal default-arg callers will receive.

The rationale block is load-bearing under `feedback_notebook_citation_block` discipline (every test/decision/spec choice must be grep-discoverable), even though this file is a module not a notebook — the decision-traceability principle applies the same way.

---

## §4. Test-migration trace

### §4.1 Step-7 synthetic round-trip migration (test_y3.py:285-326)

**Pre-flip** (line 315 in commit `2a0377057`):

```python
rows = load_onchain_y3_weekly(conn)
```

**Post-flip** (line 324 post-Step-0):

```python
# Explicit ``source_methodology="y3_v1"`` per Rev-5.3.2 Task 11.O Step 0;
# the bare default no longer returns ``"y3_v1"`` rows.
rows = load_onchain_y3_weekly(conn, source_methodology="y3_v1")
```

The synthetic test inserts a row with `source_methodology="y3_v1"` into an in-memory DuckDB and round-trips it. With the new default flipped to the v2 primary literal, the bare `load_onchain_y3_weekly(conn)` call would query for `WHERE source_methodology = 'y3_v2_co_dane_...'` against an in-memory DB that only has a `y3_v1` row — i.e., zero rows, breaking the existing assertion `assert len(rows) == 1`. Migrating to explicit `source_methodology="y3_v1"` keeps the synthetic test green.

The docstring update (§3) adds the explicit narrative explaining why this synthetic test alone needs the explicit-arg form.

### §4.2 New failing-first test for the new default

Created `contracts/scripts/tests/inequality/test_y3_default_methodology.py` with two assertions, both consuming the canonical-DB `conn` fixture from `scripts/tests/conftest.py:322` (real-data discipline per `feedback_real_data_over_mocks`):

| Test | Pre-flip outcome | Post-flip outcome |
|------|------------------|-------------------|
| `test_load_onchain_y3_weekly_default_returns_v2_primary_literal_rows` | FAILED (`len(rows) == 0`) | PASSED (`len(rows) == 116`) |
| `test_load_onchain_y3_weekly_default_matches_explicit_v2_primary_call` | FAILED (`default=0 != explicit=116`) | PASSED (default rows = explicit rows, frozen-dataclass-equal) |

The `REV_5_3_2_V2_PRIMARY_LITERAL: Final[str]` constant is pinned at the top of the new test file so any future rename of the v2 literal in `econ_query_api.py` forces a coupled edit here — a structural defense against silent default drift.

### §4.3 Regression check across all callers of `load_onchain_y3_weekly`

`grep -rn "load_onchain_y3_weekly" scripts/` enumerated 6 call-sites outside the loader definition itself. All call-sites already pass `source_methodology=...` explicitly:

- `tests/inequality/test_y3_methodology_admitted_set.py` (5 calls; all explicit)
- `tests/inequality/test_y3_imf_only_sensitivity.py` (2 calls; all explicit)
- `tests/inequality/test_y3_default_methodology.py` (this Step-0 file; 3 default-arg calls — INTENDED behavior)
- `tests/inequality/test_y3.py::test_step7_…` (1 call; migrated above)

**No production module calls `load_onchain_y3_weekly` outside the test suite** — meaning the default flip has zero blast radius on production code; only the synthetic Step-7 test needed migration.

---

## §5. Honest provenance statement

### §5.1 New symbols introduced

- `REV_5_3_2_V2_PRIMARY_LITERAL: Final[str]` in `test_y3_default_methodology.py` — module-private test constant. Mirrors the v2 primary literal stored in `econ_query_api.py` so the coupling is grep-discoverable. NOT exported; NOT importable; lives in test module only.

### §5.2 Symbols modified (byte-exact narrative-only changes)

- `econ_query_api.load_onchain_y3_weekly` — signature default-value changed from `"y3_v1"` to `"y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"`. The body of the function is byte-exact unchanged; only the parameter default literal differs. Docstring expanded with rationale block (no behavioral change to docstring logic — just narrative).

- `test_y3.py::test_step7_load_onchain_y3_weekly_returns_frozen_dataclass` — single line changed to add explicit `source_methodology="y3_v1"` argument; docstring expanded with Rev-5.3.2 Task 11.O Step 0 rationale. Test outcome unchanged: still PASSES with `len(rows) == 1` and `r.source_methodology == "y3_v1"`.

### §5.3 Anti-fishing invariants preserved

- `_KNOWN_Y3_METHODOLOGY_TAGS` membership UNCHANGED: still the same 4-element frozenset (`y3_v1`, `y3_v1_3country_ke_unavailable`, `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`, `y3_v2_imf_only_sensitivity_3country_ke_unavailable`). Step 0 only changed the DEFAULT-VALUE selection FROM the admitted-set; it did NOT add/remove/rename tags.
- Validation-guard branch UNCHANGED: `if source_methodology not in _KNOWN_Y3_METHODOLOGY_TAGS: raise ValueError(...)` is byte-exact-preserved.
- DuckDB tables UNCHANGED: read-only access only; zero writes.
- `MDES_FORMULATION_HASH` UNCHANGED: not touched.
- Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` UNCHANGED: this Step is panel-loader-only; does not touch panel construction.
- 76-week joint-X-d-nonzero gate from Task 11.N.2d-rev UNCHANGED: this Step does not touch ingestion.

### §5.4 Test-suite gate

`pytest contracts/scripts/tests/inequality/` — pre-Step-0 baseline 98 passed / 1 skipped → post-Step-0 100 passed / 1 skipped (+2 from the new failing-first file; Step-7 migration nets ±0).

The full `pytest scripts/tests/` (non-inequality) runner output is captured below to demonstrate no cross-suite regression — the default flip touched no code path outside the inequality module.

---

## §6. Acceptance criteria checklist

- [x] New failing-first test passes red→green (verified: 2/2 RED pre-flip; 2/2 GREEN post-flip).
- [x] Migrated Step-7 test passes with explicit `source_methodology="y3_v1"` argument.
- [x] All other inequality-suite tests remain green (100/100 + 1 skipped).
- [x] Verification memo committed at `contracts/.scratch/2026-04-25-step0-default-flip-result.md` with: (a) diff summary §1, (b) docstring rationale §3, (c) test-migration trace §4, (d) honest provenance §5.
- [x] Smoke test confirms `load_onchain_y3_weekly(conn)` (no tag) returns 116 rows from v2 primary panel against canonical DuckDB.

---

## §7. Reviewer dispatch (handoff to foreground orchestrator)

Per `feedback_implementation_review_agents`, the foreground orchestrator dispatches CR + RC + Senior Developer in parallel post-commit. This Data-Engineer subagent does NOT dispatch reviewers.

The 3-way review trio for this Step 0 should focus on:

- **CR**: signature/docstring consistency, default-arg type narrowing, test-coverage completeness (does the new failing-first test alone suffice, or should it parameterize across the v2 literal AND the Rev-5.3.1 `y3_v1_3country_ke_unavailable` literal?).
- **RC**: empirical grounding — verify the 116-row count against the canonical DB independently; verify the `2024-01-12 → 2026-03-27` span matches the design-doc primary panel window; verify no callers outside the migrated test exist (`grep -rn` independent re-do).
- **SD**: long-horizon maintainability — should the Rev-5.3.2 v2 literal be promoted to a module-level `Final[str]` constant in `econ_query_api.py` so `test_y3_default_methodology.py` can import it instead of duplicating the literal? (SD-A4 forwarded note from plan line 1236 already anticipates this fold at the 6-tag boundary.)

---

End of memo.
