# Code Reviewer — Task 11.O Step-0 default-flip review

**Commit:** `202874565` on `phase0-vb-mvp`
**Subject:** `load_onchain_y3_weekly` default `source_methodology` flip + Step-7 test migration
**Reviewer:** Code Reviewer (3-way trio dispatch slot)
**Date:** 2026-04-25
**Verdict:** **PASS**

---

## §1. Verification trace (7-axis CR lens)

### 1. Default-arg flip is exact — PASS

`econ_query_api.py:1525` — sole signature change is the literal:

```diff
-    source_methodology: str = "y3_v1",
+    source_methodology: str = (
+        "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"
+    ),
```

Function body unchanged. Validation guard branch unchanged (confirmed in §4). The two-line parenthesized literal is a stylistic line-length choice (Black-compatible), behaviorally equivalent to a single-line literal.

### 2. Step-7 test migration preserves logic — PASS

`test_y3.py:285-326` diff contains exactly two substantive changes:

- **Docstring expansion** (+7 lines) explaining the Step-0 rationale.
- **Single line of executable change** at `test_y3.py:322-324`:

```diff
-    rows = load_onchain_y3_weekly(conn)
+    # Explicit ``source_methodology="y3_v1"`` per Rev-5.3.2 Task 11.O Step 0;
+    # the bare default no longer returns ``"y3_v1"`` rows.
+    rows = load_onchain_y3_weekly(conn, source_methodology="y3_v1")
```

All downstream assertions (`isinstance`, `len(rows) == 1`, frozen-dataclass field-by-field equality at lines 327–334) are byte-exact preserved. Round-trip semantics intact: the synthetic in-memory DB is populated with one `y3_v1`-tagged row, the explicit-arg load retrieves exactly that row, and identity is checked field-wise. **Test logic preserved; only the API call form changed.** ✓

### 3. New failing-first test — PASS

`test_y3_default_methodology.py` (NEW, 115 lines) contains:

- **Two real assertions** (NOT just imports):
  - `test_load_onchain_y3_weekly_default_returns_v2_primary_literal_rows` → asserts `len(rows) > 0` AND `all(r.source_methodology == REV_5_3_2_V2_PRIMARY_LITERAL for r in rows)`.
  - `test_load_onchain_y3_weekly_default_matches_explicit_v2_primary_call` → asserts default-arg row count matches explicit-arg row count AND `default_rows == explicit_rows` via frozen-dataclass field-wise equality.
- **Real-data discipline** (per `feedback_real_data_over_mocks`): both tests consume the session-scoped `conn` fixture from `scripts/tests/conftest.py:322` against canonical `contracts/data/structural_econ.duckdb`. No mocks. ✓
- **Defensive constant** `REV_5_3_2_V2_PRIMARY_LITERAL: Final[str]` is mirrored from `econ_query_api.py` and pinned at module top — explicit invitation for a future-rename to break this test in lockstep. Strong structural-coupling pattern, NOT silent drift surface.
- **Failing-first verified red→green** (commit body §"Test-migration scope" + memo §6): pre-flip RED 0 rows; post-flip GREEN 116 rows. Strict-TDD compliance. ✓

### 4. Anti-fishing invariants preserved — PASS

- `_KNOWN_Y3_METHODOLOGY_TAGS` membership: not in diff → still 4 tags (`y3_v1`, `y3_v1_3country_ke_unavailable`, `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`, `y3_v2_imf_only_sensitivity_3country_ke_unavailable`). The flip selects FROM the admitted-set without expanding it. ✓
- Validation guard (`if source_methodology not in _KNOWN_Y3_METHODOLOGY_TAGS: raise ValueError`): not in diff → byte-exact preserved. ✓
- DuckDB schema mutation: zero (read-only access; loader function only). ✓
- `MDES_FORMULATION_HASH`: not referenced in diff. Out-of-scope per plan line 1228. ✓

### 5. Docstring quality — PASS

The +22/-7 docstring rewrite (econ_query_api.py:1530-1571) accomplishes three load-bearing things cleanly:

- **Disambiguates `y3_v1` vs `y3_v1_3country_ke_unavailable`**: the new `y3_v1` bullet explicitly states "the canonical Rev-5.3.1 stored literal is `'y3_v1_3country_ke_unavailable'` (the suffix is appended at ingest time by `ingest_y3_weekly`)". This kills the conflation risk. ✓
- **Flags v2 literal as the default** with bold `**This is the default**`. A reader scanning the admitted-tag list immediately knows which tag default-arg callers receive. ✓
- **Explains "why default is v2 primary now"** in a dedicated "Default-arg rationale" paragraph that names Rev-5.3.2 Task 11.O Step 0 + SD-RR-A1 + the silent-empty-tuple footgun. Grep-discoverable for any future debugger. ✓
- **Production-prohibition warning on `y3_v1`**: "Production callers MUST NOT pass this literal." Bold + caps emphasis. ✓

No confusion residue between legacy `y3_v1` and canonical `y3_v1_3country_ke_unavailable`. The docstring also names the exact synthetic test (`test_y3.py::test_step7_load_onchain_y3_weekly_returns_frozen_dataclass`) authorized to use `y3_v1` — sole legitimate consumer.

### 6. `feedback_agent_scope` compliance — PASS

`git show 202874565 --stat` returns exactly four files:

| File | Status | Size |
|---|---|---|
| `contracts/.scratch/2026-04-25-step0-default-flip-result.md` | NEW | +193 |
| `contracts/scripts/econ_query_api.py` | MOD | +22/−7 (net +15) |
| `contracts/scripts/tests/inequality/test_y3.py` | MOD | +11/−2 (net +9) |
| `contracts/scripts/tests/inequality/test_y3_default_methodology.py` | NEW | +115 |

No untouched files modified. No other `*.py` or `*.sol` or plan/spec markdown touched. ✓

### 7. Provenance honesty — PASS

`git ls-tree 202874565~1 -- contracts/scripts/tests/inequality/test_y3_default_methodology.py` returns empty (file did not exist in predecessor `2a0377057`). The DE memo's "NEW" claim is verified. ✓

---

## §2. Cross-checks against plan and sibling pattern

- **Plan line 1228** (read directly): authorizes precisely (a) the default flip from `"y3_v1"` to the v2 primary literal and (b) the Step-7 test migration to explicit-arg form. Commit scope matches plan scope 1:1. ✓
- **Sibling pattern `2a0377057`** (Rev-5.3.2 admitted-set + validation-guard fix-up): closed the silent-empty footgun against TYPOED literals. Step 0 closes the residual silent-empty footgun against the LEGACY DEFAULT, completing the SD-RR-A1 pair. The DE narrative correctly distinguishes the two and frames Step 0 as the strict complement. ✓
- **Smoke test** (memo §2): default-arg call against canonical DB returns 116 rows; span 2024-01-12 → 2026-03-27 matches plan-line-1219 declared primary-panel window. Empirical verification reasonable; full re-run is RC's domain.

---

## §3. Non-blocking advisories (informational only)

- **A1 (FYI, not actionable in this commit):** the DE memo §7 forwards SD-A4 — promote `REV_5_3_2_V2_PRIMARY_LITERAL` to a module-level `Final[str]` in `econ_query_api.py` so `test_y3_default_methodology.py` can import it instead of duplicating the literal. This is **explicitly out of Step-0 scope** (file-scope rule + admitted-set scaling threshold note at plan line 1236 — fold becomes strictly better at 6+ tags, current shape is acceptable through 5). Forward to Senior Developer review. **Not a blocker.**
- **A2 (FYI):** the Step-7 test migration leaves `y3_v1` as the only synthetic-test consumer of the bare-tag literal. If a future revision adds another `y3_v1`-using synthetic test, the docstring's "naming the one test that uses it" promise breaks. Consider whether `y3_v1` should be retired entirely once Rev-5.3.2 stabilizes. Not in this commit's scope.

---

## §4. Verdict

**PASS.** Step-0 is a textbook surgical fix:

- Single-literal default flip with no body changes.
- Failing-first new test with two real assertions, real data, and a structural-coupling constant.
- Existing synthetic round-trip test migrated minimally to preserve identical semantics.
- Docstring rewritten to make the new default + the production-prohibition on `y3_v1` impossible to miss.
- `feedback_agent_scope` honored (4 files, exactly as declared).
- All anti-fishing invariants preserved (admitted-set, validation guard, DuckDB read-only, MDES hash, decision_hash, 76-week gate).
- Provenance claims (new file did not exist pre-commit) verified independently via `git ls-tree`.

No blockers. No suggested fixes. Foreground orchestrator may proceed to RC + SD reviews and (on PASS-trio) to Step 1 spec authoring.

---

End of review.
