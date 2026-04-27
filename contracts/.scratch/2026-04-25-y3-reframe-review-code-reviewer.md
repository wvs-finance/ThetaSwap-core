# Code Reviewer Review — Task 11.N.2d.1-reframe (commit `9a1f00068`)

**Reviewer:** Code Reviewer
**Date:** 2026-04-25
**Commit under review:** `9a1f00068` — Rev-5.3.2 Task 11.N.2d.1-reframe (IMF-IFS-only sensitivity Y₃ panel)
**Sibling reference:** `c5cc9b66b` (Task 11.N.2d-rev primary panel) + `2a0377057` (admitted-set fix-up)
**Scope:** Read-only review against the 8-axis CR lens supplied by the orchestrator.
**Verdict:** **PASS** (no blocking issues; 2 non-blocking advisories below).

---

## Summary

This is a tight, well-scoped recovery commit. The Data Engineer's intact working-tree state was committed by the foreground orchestrator after the credit-cap cutoff, and the result holds together cleanly across all 8 review axes. The change is genuinely additive: a single `source_mode` keyword-only parameter, one admitted-set entry, one new test file, and an additive INSERT under composite PK. The IMF-IFS dispatch body (`_fetch_imf_ifs_headline_broadcast`) is byte-exact preserved (zero diff against `c5cc9b66b`), which was load-bearing for the sensitivity construction.

The headline finding (PRIMARY 76 PASS / SENSITIVITY 56 FAIL, Δ = 20 weeks) is the *demonstrative* outcome the task was designed to produce — it locks the source upgrades against silent reversal in future revisions. The 56-week FAIL is a diagnostic finding, not a gate failure for this task; N_MIN held at 75 with no tuning.

---

## Axis-by-axis findings

### 1. `source_mode` parameter design — PASS

The signature at `contracts/scripts/econ_pipeline.py:2829-2836` declares:

```python
def ingest_y3_weekly(
    conn: "duckdb.DuckDBPyConnection",
    *,
    start: date | None = None,
    end: date | None = None,
    source_methodology: str = "y3_v1",
    source_mode: str = "primary",
) -> dict[str, int]:
```

- **Keyword-only confirmed** — `source_mode` is after the `*` separator (`*` is implicit because `start`, `end`, `source_methodology` were already keyword-only in the predecessor commit). The `inspect.signature` test at line 80-100 of the test file directly asserts `param.kind is inspect.Parameter.KEYWORD_ONLY` and `param.default == "primary"`. Verified.
- **Default `"primary"` preserves backward-compat** — every existing caller (notebooks, sibling tests, downstream cells) keeps original behavior byte-exact. Confirmed by the regression-guard test at lines 132-204.
- **Conditional dispatch is clean** — line 2944: `wc_conn = conn if source_mode == "primary" else None`. This is a one-line ternary that introduces no leaked DuckDB-conn-as-state. The `wc_conn` local is computed from the immutable input; `conn` is not mutated. The fetcher receives the right kwarg per branch.
- **Fail-fast validation** — the ValueError at lines 2883-2891 fires *before* any imports, fetches, or DB writes; the error message names the admitted set so callers self-correct. This matches the established `_KNOWN_Y3_METHODOLOGY_TAGS` discipline from `2a0377057`.

**Non-blocking advisory CR-A1:** the test docstring (lines 12-23) and DE memo §1.1 describe the parameter as `Literal["primary", "imf_only_sensitivity"]`, but the signature uses bare `str` for both `source_methodology` and `source_mode`. This is **consistent with the existing codebase style** (no `Literal` import anywhere in `econ_pipeline.py`), and runtime validation at line 2883 is the enforcement contract that actually ships. The "Literal" wording is a minor documentation aspiration, not a code defect. Optional future work: when `source_methodology` itself migrates to a `Literal` type alias, `source_mode` can ride along. Not a blocker for this commit.

### 2. Admitted-set extension — PASS

`contracts/scripts/econ_query_api.py:60-77`:

- The constant remains `_KNOWN_Y3_METHODOLOGY_TAGS: Final[frozenset[str]]` (line 72). `Final` and `frozenset` typing both preserved byte-exact.
- The new tag `y3_v2_imf_only_sensitivity_3country_ke_unavailable` is added as a literal `frozenset` element alongside the three prior tags; no mutation of the prior entries.
- The 14-line docstring block (lines 59-71) explains the new tag's source mix, why it differs from primary, and the expected joint-coverage shortfall — readable and honest about the diagnostic role.

The test at lines 295-310 of the test file directly asserts `_SENSITIVITY_TAG_STORED in _KNOWN_Y3_METHODOLOGY_TAGS`. Verified.

### 3. TDD discipline — PASS

`contracts/scripts/tests/inequality/test_y3_imf_only_sensitivity.py` (NEW, 7 tests, 389 lines):

| Section | Test | Real assertion verified |
|---|---|---|
| 1 | `test_ingest_y3_weekly_signature_has_source_mode_kwarg` | `inspect.signature` → `source_mode in parameters`, `kind is KEYWORD_ONLY`, `default == "primary"` |
| 1 | `test_ingest_y3_weekly_rejects_unknown_source_mode` | `pytest.raises(ValueError)` + msg contains `"source_mode"`, `"primary"`, `"imf_only_sensitivity"` |
| 2 | `test_primary_mode_forwards_conn_to_wc_cpi_fetcher` | regression: `conn_id == id(test_conn)` (live conn forwarded) |
| 3 | `test_imf_only_sensitivity_passes_conn_none_to_wc_cpi_fetcher` | sensitivity: `conn_is_none` is True (the load-bearing dispatch) |
| 4 | `test_known_y3_methodology_tags_contains_sensitivity_literal` | admitted-set membership |
| 4 | `test_load_onchain_y3_weekly_accepts_sensitivity_literal_against_canonical_db` | `len(rows) > 0` + per-row `source_methodology == _SENSITIVITY_TAG_STORED` (real DuckDB) |
| 4 | `test_primary_panel_rows_unchanged_post_sensitivity_ingest` | `len(primary) == 116` (composite-PK byte-exact preservation) |

The dispatch tests (sections 2 + 3) use `monkeypatch` to short-circuit the fetcher with a Y3FetchError sentinel that captures the `conn` kwarg the call site forwards. This is **the correct mock scope** under `feedback_real_data_over_mocks`: the unit under test is the call-site dispatch (not the fetcher's behavior); the equity stub is minimal and present only because `ingest_y3_weekly` would crash on Yahoo before reaching the WC-CPI line under test. No behavioral mocks of CPI data.

The canonical-DB tests (section 4) use real `data/structural_econ.duckdb` reads — verified live below in axis 6.

The TDD red→green claim (memo §2 table) is plausible: pre-patch, the signature lacks `source_mode`, so test 1 fails on `assert "source_mode" in sig.parameters` (AssertionError) and tests 2-3 fail on `TypeError: ingest_y3_weekly() got an unexpected keyword argument 'source_mode'`. Test 4-1 fails on `AssertionError`. Tests 4-2 and 4-3 fail until ingest runs.

### 4. Anti-fishing — PASS

- **N_MIN held at 75.** Memo §6 line 1: "`N_MIN` was **not** silently relaxed. The Rev-5.3.1 path-α relaxation 80→75 (recorded in `MEMORY.md::rev531_n_min_relaxation_path_alpha`) holds."
- **Sensitivity FAIL at 56 weeks is DEMONSTRATIVE.** The task design pre-registered the comparison; the 56 < 75 outcome locks the source upgrades against silent reversal. The commit message and memo §0 + §4 both frame this correctly.
- **Methodology tag was finalized at implementation time and added to the admitted-set BEFORE the ingest landed.** Memo §6 line 3 names this. The test-first-failing discipline holds.
- **No N_MIN tuning, no MDES tuning, no window tuning** in this commit (window, gates, Cohen f² formulation all preserved).

### 5. IMF-IFS path body byte-exact preserved — PASS

`git diff c5cc9b66b 9a1f00068 -- contracts/scripts/y3_data_fetchers.py` returns **0 lines**. Confirmed: `_fetch_imf_ifs_headline_broadcast` is the foundation of this sensitivity, and the sibling brain in `y3_data_fetchers.py` is untouched.

### 6. Composite PK additivity — PASS (live DuckDB verified)

```sql
SELECT source_methodology, COUNT(*) FROM onchain_y3_weekly GROUP BY source_methodology ORDER BY 1;
```

Live verified results:
| `source_methodology` | rows |
|---|---|
| `y3_v1_3country_ke_unavailable` | **59** |
| `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` | **116** |
| `y3_v2_imf_only_sensitivity_3country_ke_unavailable` | **116** |

All three methodology tags coexist; composite PK `(week_start, source_methodology)` admits the new tag without mutating the prior 59 + 116 rows. Counts match the commit-message claim and memo §3.2 / §3.4 byte-exact.

### 7. Provenance honesty — PASS

The DE memo's §7 provenance statement enumerates exactly:
1. `source_mode` parameter added to `ingest_y3_weekly` signature
2. Methodology tag added to `_KNOWN_Y3_METHODOLOGY_TAGS`
3. 7 new TDD tests in `test_y3_imf_only_sensitivity.py` (NEW file)
4. 116 new rows in `onchain_y3_weekly` under the new methodology

`git show 9a1f00068~1 -- contracts/scripts/econ_pipeline.py` shows `ingest_y3_weekly` had no `source_mode` parameter prior. `git show 9a1f00068~1 -- contracts/scripts/econ_query_api.py` shows the admitted-set held three tags prior, not four. The "no fresh symbols beyond" enumeration matches the diff exactly. No false pre-staging claim.

The commit message's transparent recovery context (DE cut off after 71 tool uses, foreground orchestrator verified working-tree integrity, ran inequality suite 98/1, full pytest blocked by pre-existing user-resolved disk-quota issue) is honest about what was tested and what was not, and matches `feedback_concurrent_agent_filesystem_interleaving` discipline.

### 8. `feedback_agent_scope` — PASS

`git show 9a1f00068 --name-only` returns exactly 4 files:
1. `contracts/.scratch/2026-04-25-y3-imf-only-sensitivity-comparison.md`
2. `contracts/scripts/econ_pipeline.py`
3. `contracts/scripts/econ_query_api.py`
4. `contracts/scripts/tests/inequality/test_y3_imf_only_sensitivity.py`

All 4 are explicitly declared in the DE memo §9 in-scope list. No untouched files modified. No collateral changes to `y3_compute.py`, `y3_data_fetchers.py`, `econ_schema.py`, `carbon_calibration.py`, or any plan/spec markdown. Clean scope.

---

## Non-blocking advisories

**CR-A1 (documentation polish, not a blocker).** Test file docstring (lines 12-23) and DE memo §1.1 describe `source_mode` as `Literal["primary", "imf_only_sensitivity"]`, but the actual signature uses bare `str`. This is consistent with the codebase's existing `source_methodology: str` style (no `Literal` import anywhere). Runtime validation at `econ_pipeline.py:2883` is the enforcement contract. Optional future work when `source_methodology` itself migrates to a `Literal` type alias.

**CR-A2 (review checkbox completion).** Memo §5 line 232 has a `- [ ] Code Reviewer ack` checkbox awaiting this review. The literal `y3_v2_imf_only_sensitivity_3country_ke_unavailable` is **acked** by this reviewer:
- The decomposition (`y3_v2` schema generation + `imf_only_sensitivity` flag + `_3country_ke_unavailable` runtime suffix) is internally consistent with the prior literals.
- The runtime suffix appending is the same convention as primary panel literal.
- The literal is admitted-set-registered and round-trips correctly through `load_onchain_y3_weekly`.

The orchestrator should mark §5 line 232 checked in the memo after the review converges.

---

## Test coverage status (axis-out-of-scope but noted)

- `pytest scripts/tests/inequality/` (per commit message): 98 passed, 1 skipped (was 91; +7 new sensitivity tests). Verified via inequality-suite-only run was the foreground orchestrator's chosen signal under disk-quota constraint.
- The 2 pre-existing remittance Task-9 stub failures (`scripts/tests/remittance/test_cleaning_remittance.py`, intentional `NotImplementedError` seams) are NOT introduced by this commit and are out of scope per `feedback_agent_scope`.

---

## Verdict

**PASS** — clean recovery commit; no must-fix items; two non-blocking advisories above for orchestrator awareness.

The work converges at the implementation layer per plan §Task 11.N.2d.1-reframe. The Data Engineer's intact pre-cutoff state was committed cleanly by the foreground orchestrator with full provenance honesty. The sensitivity panel demonstrates exactly what the task pre-registered: under the pre-Rev-5.3.2 mix, path ζ does NOT clear N_MIN=75 — the source upgrades were genuinely necessary, not arbitrary.

Next dispatch (per plan §Task 11.N.2d.1-reframe Reviewers list): Reality Checker + Senior Developer.
