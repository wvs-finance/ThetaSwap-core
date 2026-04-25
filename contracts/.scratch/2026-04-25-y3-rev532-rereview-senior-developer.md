# Senior-Developer Re-Review — Task 11.N.2d-rev fix-up `2a0377057`

**Date:** 2026-04-25
**Branch:** `phase0-vb-mvp`
**Reviewer:** Senior Developer (final convergence reviewer)
**Predecessor review:** `2026-04-25-y3-rev532-review-senior-developer.md` (NEEDS-WORK on §4 BLOCKING)
**Sibling reviews:** CR PASS, RC PASS (both with non-blocking advisories)

---

## Verdict — **PASS-with-non-blocking-advisories**

§4 BLOCKING is **fully cleared**. The fix-up DE delivered a tight, scope-respecting, TDD-disciplined patch that closes the silent-empty-tuple footgun without collateral drift. One residual non-blocking advisory carries forward to Task 11.O (see SD-RR-A1 below).

---

## Verification against the seven re-review points

**(1) Admitted-set existence + contents — PASS.** `_KNOWN_Y3_METHODOLOGY_TAGS: Final[frozenset[str]]` lands at `econ_query_api.py:59` (above the existing `_DATE_TABLES` constant) and contains exactly the three required literals: `"y3_v1"`, `"y3_v1_3country_ke_unavailable"`, `"y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"`. Per-tag provenance is documented in a 23-line block comment with row counts and revision attribution.

**(2) Validation guard correctness — PASS.** The guard at the top of `load_onchain_y3_weekly()` raises `ValueError` *before* `_check_table()` and any DB I/O. Error message names the rejected tag (`{source_methodology!r}`), enumerates the `sorted(_KNOWN_Y3_METHODOLOGY_TAGS)` admitted set, and cites plan line 1929 + the canonical constant path so callers can self-correct without grepping. Two synthetic-DB tests (`test_load_onchain_y3_weekly_rejects_unknown_methodology_tag`, `test_load_onchain_y3_weekly_rejects_typo_with_close_match`) assert both the rejection and the message-content invariants. The near-miss-typo test specifically targets the SD §4 footgun (downstream caller passing the *base* tag without the runtime `_3country_ke_unavailable` suffix).

**(3) Default-value trade-off — PASS, advisory raised (SD-RR-A1).** The DE preserved `source_methodology: str = "y3_v1"` to keep the Step-7 round-trip test in `test_y3.py:285-323` green without expanding file scope. **My stance:** this is an *acceptable* trade-off for this fix-up because (a) the production codepaths the SD §4 BLOCKING was actually concerned about — Task 11.N.2d.1-reframe and Task 11.O Rev-2 — *will not* call with the default; they pass the v2 literal explicitly, and the docstring now says so in **bold** ("**production callers reading the canonical `structural_econ.duckdb` MUST pass the Rev-5.3.2 literal explicitly**"); (b) the silent-empty-tuple risk that *was* CR-A1's concern is now blocked by the *guard*, not by the default — any unknown tag raises before DB access. The narrow remaining surface is a production caller who explicitly passes `"y3_v1"` against the canonical DB and expects rows; they would now get an empty tuple rather than a `ValueError`. This is a residual hole, but it is *strictly smaller* than the original CR-A1 footgun (footgun shifts from "any typo" to "the single legacy tag against canonical DB") and is documented. **Non-blocking advisory SD-RR-A1:** when Task 11.O Rev-2 lands, the orchestrator should follow up with a separate task that flips the default to `"y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"` and migrates the Step-7 synthetic test to pass an explicit tag, eliminating the residual hole. Not actioned here because it is outside the fix-up brief's file scope (touching `test_y3.py`).

**(4) §3.2 corrigendum quality — PASS.** Memo carries a 20-line CORRIGENDUM block at the top (post-§gate-verdict-summary, pre-§gate-verdict-detail) explaining that the original γ-backward-extension narrative is mechanically incorrect because X_d (`carbon_basket_user_volume_usd`) only begins 2024-08-30 — γ-extended Y₃ rows pre-that-date have zero X_d counterpart and contribute zero to the joint count. The corrected LOCF-tail-forward mechanism is laid out with byte-exact arithmetic (EU 2025-12-01 + 120 days = 2026-03-31; panel last Friday = 2026-03-27; gain `+5+4+2=+11` over Jan/Feb/Mar 2026) and corroborated against RC probe-5 (`2025-12-31 → 65` byte-exact). Original incorrect text in §3.2 is preserved with `~~strikethrough~~` followed by an explicit "see CORRIGENDUM above" pointer. Sources cited: SD §5 + RC A1. Mirrors the corrigendum precedent in `2026-04-25-co-dane-wireup-result.md`. The 76 figure is correctly attributed as still valid; only the *explanation* was misattributed.

**(5) TDD discipline — PASS.** `test_y3_methodology_admitted_set.py` (184 lines) is genuinely TDD: every test contains real `assert` / `pytest.raises` machinery (verified by inspection of all 7 test bodies, not just imports). Section 1 (3 tests) covers constant-existence and membership. Section 2 (2 tests) covers ValueError-on-unknown + near-miss-typo. Section 3 (2 tests) covers round-trip from canonical DuckDB via the session-scoped `conn` fixture (per `feedback_real_data_over_mocks`). Module docstring explicitly cites the failing-first sequence and the `feedback_strict_tdd` rule. DE's commit message reports `pytest scripts/tests/inequality/: 91 passed, 1 skipped (was 84; +7 new)` — number-consistent with 7 admitted-set tests added.

**(6) Functional-Python compliance — PASS.** `_KNOWN_Y3_METHODOLOGY_TAGS: Final[frozenset[str]] = frozenset({...})` — `Final` is already imported at `econ_query_api.py:10` (alongside `Literal`); `frozenset` is the canonical immutable container per `functional-python` skill. Validation guard is a free pure block of statements inside an existing free function (no class, no inheritance, no mutation of the constant). The leading underscore on `_KNOWN_Y3_METHODOLOGY_TAGS` correctly marks it module-private; tests reach in via direct import (`from scripts.econ_query_api import _KNOWN_Y3_METHODOLOGY_TAGS`), which is acceptable for a TDD admitted-set assertion.

**(7) No drift outside file scope — PASS.** `git show 2a0377057 --stat` confirms exactly three files: `econ_query_api.py` (+75/-14 lines), `test_y3_methodology_admitted_set.py` (+184/-0, NEW), `2026-04-25-y3-rev532-ingest-result.md` (+46/-14). No production files outside scope, no plan markdown, no DuckDB rebuild, no `test_y3.py` (Step-7 synthetic test untouched, consistent with the trade-off documented above). Total: 291 insertions / 14 deletions across 3 files — proportionate to a single-issue BLOCKING fix-up.

---

## Residual non-blocking advisories

**SD-RR-A1 (forward to Task 11.O dispatch):** The `source_methodology: str = "y3_v1"` default in `load_onchain_y3_weekly()` still admits a production-caller foot-shoot — passing the legacy default explicitly against canonical DB returns empty tuple rather than `ValueError`. Resolve in a follow-up task that (a) flips the default to the Rev-5.3.2 v2 literal and (b) migrates the Step-7 round-trip test (`test_y3.py:285-323`) to pass `"y3_v1"` explicitly. Not blocking because it falls outside this fix-up's file-scope authorization and the residual surface is strictly smaller than the original CR-A1 footgun.

**SD-RR-A2 (forward to Task 11.O Rev-2 spec):** RC A3's pre-registered LOCF-tail-excluded sensitivity (= 65 weeks, FAIL) remains on the dispatch checklist for Task 11.O. The fix-up commit message correctly forwards this; verify the Task 11.O brief surfaces it as a precondition.

---

## Convergence

§4 BLOCKING from the prior SD review is **closed**. CR PASS + RC PASS verdicts stand. The 3-way review converges to **PASS** for commit `2a0377057`. Task 11.N.2d-rev is cleared for downstream consumption (Task 11.N.2d.1-reframe, Task 11.O Rev-2).

— Senior Developer, 2026-04-25
