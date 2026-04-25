# Senior Developer Review — Task 11.N.2.CO-dane-wire

**Reviewer:** Senior Developer (third of three; alongside Code Reviewer + Reality Checker per `feedback_implementation_review_agents`)
**Commit:** `f7b03caac` on `phase0-vb-mvp`
**Date:** 2026-04-25
**Reviewer lens:** "Is this code I would want to maintain in 6 months? Does it integrate cleanly with the rest of the system?"

**Verdict:** PASS-with-non-blocking-advisories

The implementation is functionally correct, type-safe, scoped tightly, well-tested, and integrates with project conventions. Two non-blocking advisories (A1, A2) and one **must-fix-or-correct-the-record** finding (M1) are documented below. M1 is a paperwork problem — the commit message and the verification memo each contain a verifiably false claim about which lines were "pre-staged from a prior stream." The code itself is fine; the trail is not. Senior-dev calculus: ship the code, fix the claim before downstream consumers cite the trail.

---

## Lens-by-lens findings

### 1. API design quality of the `conn` kwarg — PASS-with-advisory

The `conn` kwarg approach (`fetch_country_wc_cpi_components(country, start, end, *, conn=None)`) is the **correct level of abstraction for the immediate task**. Reasoning:

* The function is a per-country dispatcher. Adding a per-country source override at the dispatcher's signature is the lowest-blast-radius change possible.
* `conn` is a duck-typed object — `TYPE_CHECKING`-guarded import means callers without DuckDB still see a clean public signature.
* Default `conn=None` preserves backward compatibility byte-exactly. The IMF-IFS path is the dispatch fallback; existing callers that pre-date Rev-5.3.2 are unaffected.
* The implementation is keyword-only (`*, conn=...`), which is a deliberate ergonomics choice — callers cannot accidentally pass `conn` positionally and break under future signature evolution.

**Does it leak DuckDB as an implementation detail?** Yes, in a controlled way. The forward-reference `"duckdb.DuckDBPyConnection | None"` is gated behind `TYPE_CHECKING`, so the leak is purely lexical, not runtime. Any caller that doesn't already have a DuckDB connection in scope simply passes `None` and gets the IMF-IFS path. That is the right tradeoff for this task.

**Could a strategy-pattern source-selector scale better?** Yes — and that's the advisory:

> **A1 (non-blocking):** Once Task 11.N.2.BR-bcb-fetcher lands, `fetch_country_wc_cpi_components` will have a 4-branch dispatch (`EU → Eurostat`, `CO with conn → DANE`, `BR with X → BCB SGS cumulative`, `else → IMF-IFS`). At that point the function body will start to feel cluttered. A `_SOURCE_DISPATCH: dict[CountryCode, Callable]` + selector would localize per-country source rules and make the next country (Kenya, future) trivially additive. **Do not refactor as part of this task** — the current shape is correct for one upgrade. Flag this as a refactor candidate when the third source upgrade lands or when `fetch_country_wc_cpi_components` exceeds ~50 SLOC.

For the immediate task: the `conn`-based design is good-enough-not-perfect. Not actively bad. PASS on this dimension.

---

### 2. Integration with `ingest_y3_weekly` — DOES need follow-up plumbing (advisory)

I traced the call path. `contracts/scripts/econ_pipeline.py:2905`:

```python
comp = fetch_country_wc_cpi_components(country, start, end)
```

This call site does NOT forward `conn`, even though `conn` is a parameter of `ingest_y3_weekly` itself (line 2830). Under the current commit, the actual production ingest pipeline still resolves CO via the IMF-IFS path. The new DANE wire-up is reachable ONLY by direct callers (the new test suite, the smoke-test invocation in the verification memo, and any future Task 11.N.2d-rev work).

**Is this in scope for Task 11.N.2.CO-dane-wire?** The plan body at line 1869 is explicit: "*Modify the CO branch of `fetch_country_wc_cpi_components`* … so it consumes the existing `dane_ipc_monthly` DuckDB table". The plan does NOT direct this task to also patch `ingest_y3_weekly`. That is Task 11.N.2d-rev's job (see plan line 1916ff., dependency line 1951 explicitly chains through both fetcher tasks before re-ingest). Therefore, **the gap is correct, not a defect**.

> **A2 (non-blocking, forward-looking):** Task 11.N.2d-rev MUST patch `econ_pipeline.py:2905` to forward `conn` for CO. The simplest patch is `fetch_country_wc_cpi_components(country, start, end, conn=conn if country == "CO" else None)`, OR unconditionally `conn=conn` since the dispatcher is `country == "CO" and conn is not None`-guarded. The senior-dev recommendation is **unconditional pass-through** — it minimizes per-country if-branches in `econ_pipeline.py` and pushes the routing logic into `y3_data_fetchers.py` where it belongs. Flag this in the Task 11.N.2d-rev verification memo so the reviewer ack-ing that task can verify line 2905 was patched.

PASS on this dimension because the gap is intentional per plan dependency chain. The follow-up requirement is documented above.

---

### 3. Test fixture organization — PASS

The new file `test_y3_co_dane_wire.py` does NOT duplicate or contradict patterns in `test_y3.py`. It:

* Uses the same import-driven TDD style (`from scripts.econ_query_api import ...` inside each test).
* Uses the same canonical-DB-readonly pattern (parents[3] traversal to `contracts/data/structural_econ.duckdb`).
* Skips when the canonical DB is missing (CI-time guard).
* Asserts the same property-bag conventions: frozen dataclass, `_date_filter`-inclusive bounds, ascending order.

**Should some tests have lived in `test_y3.py` instead?** No. `test_y3.py` is the Rev-5.3.1 panel test suite (Steps 0–7 of the original Y₃ panel). The wire-up is a separate, future-source upgrade — putting it in its own file is the correct organizational choice. The new file's docstring header explicitly cross-references both the plan task ID and the predecessor task (Task 11.N.2d at commit 7afcd2ad6), which makes the relationship discoverable.

**File naming consistency:** `test_y3_co_dane_wire.py` — the `_co_dane_wire` 3-segment suffix is slightly awkward but matches the task ID slug. Existing files in the directory are `test_y3.py`, `test_carbon_calibration.py`, `test_carbon_xd_filter.py`, `test_copm_xd_filter.py` — all 1- or 2-segment suffixes. A future-self-friendlier name would have been `test_y3_dane.py`. Not blocking; do not rename.

**Step-C test #2 (`test_fetch_country_wc_cpi_components_co_without_conn_uses_imf_path`):** monkeypatches a private function (`_fetch_imf_ifs_headline_broadcast`) by direct attribute assignment. This is a contract-preservation test, not a data mock — it asserts the dispatch hits IMF-IFS when `conn` is None. The pattern is fragile if `_fetch_imf_ifs_headline_broadcast` is ever renamed (which Step-C #1 already guards against via signature locking) but is acceptable for a high-value preservation assertion. The `# type: ignore[assignment]` comments are correctly placed. PASS.

---

### 4. Maintenance burden — PASS-with-advisory

In 6 months, when someone adds a δ-EU upgrade or a new country source, the extension pattern is:

1. Add a private `_fetch_<source>_<shape>_broadcast` (or `_split`) function alongside the existing two.
2. Add a per-country dispatch line in `fetch_country_wc_cpi_components` between the EU branch and the IMF-IFS fallback.
3. Add a frozen dataclass + `load_<table>_<cadence>` reader to `econ_query_api.py` if the source materializes through a DuckDB table.

The pattern is **discoverable** because the existing `_fetch_eu_hicp_split` / `_fetch_imf_ifs_headline_broadcast` / `_fetch_dane_headline_broadcast` triplet establishes a clear naming convention and the docstrings explicitly cross-reference design doc §10 row 2. A future maintainer reading `fetch_country_wc_cpi_components` will see three private helpers below it, each with a clear source-name + shape-name in the function name, and a docstring that explains the broadcast invariant.

**Is the headline-broadcast pattern documented enough?** Yes — three places all converge on the same explanation:

* `y3_data_fetchers.py:271-275` — module-level fetcher docstring cites design doc §10 row 2.
* `y3_data_fetchers.py:330-337` — IMF-IFS broadcast helper docstring cites the same.
* `y3_data_fetchers.py:369-374` — new DANE broadcast helper docstring cites the same.

A future maintainer would have to actively delete three docstring blocks to lose the pattern memory. That's a strong defense.

> **A1 (carryover):** When the third source upgrade lands, fold the dispatch into a `_SOURCE_DISPATCH` dict to keep the dispatcher body under ~10 lines.

PASS on this dimension.

---

### 5. Code-comment discipline — PASS-with-1-finding

The diff comments are **mostly WHY-oriented** (correct):

* `y3_data_fetchers.py:46-47` (TYPE_CHECKING guard) — implicit WHY (avoid runtime `import duckdb`).
* `y3_data_fetchers.py:379-380` ("Local import to avoid a circular import at module-load time") — explicit WHY, exactly the kind of hidden-invariant comment that IS warranted. Good.
* `econ_query_api.py:750-766` — block-comment header explaining the consume-only contract, the live schema, and the plan-vs-live column-name discrepancy. Multi-line WHY block — this is exactly when a comment IS warranted.

**No WHAT-restating-the-code comments found.** The verbose docstrings are arguably over-cited (multiple references to "Rev-5.3.2 Task 11.N.2.CO-dane-wire" inside the function body), but project convention seems to lean heavy-docstring (every `econ_query_api.py` reader has multi-paragraph docstrings).

> **One micro-finding (non-blocking):** `econ_query_api.py:762` says "`_ingested_at TIMESTAMP (audit metadata, not surfaced)`" inside a block comment, but the dataclass at lines 769-785 has no `_ingested_at` field. The docstring at lines 786-800 doesn't mention this column either. If a future maintainer wants to surface `_ingested_at` for staleness diagnostics (a plausible next-need), they will have to re-read the live schema and add it manually. Consider adding the field as `_ingested_at: datetime | None` with default `None` so the dataclass already accommodates it. **Not required for this task.**

PASS on this dimension.

---

### 6. Scope drift — **MUST-FIX-OR-CORRECT-THE-RECORD (M1)**

The commit message at file `contracts/scripts/econ_query_api.py` line says:

> "(pre-staged from prior stream; consumed here)"

The verification memo at line 129 says:

> "`load_dane_ipc_monthly` and `DaneIpcMonthly` dataclass already existed (scaffolded under prior commit 7afcd2ad6 / earlier Rev-5.3.2 prep). No changes needed."

**Both claims are verifiably false.**

```
$ git show f7b03caac~1:contracts/scripts/econ_query_api.py | grep -c "DaneIpcMonthly\|def load_dane_ipc_monthly"
0
$ git show 7afcd2ad6:contracts/scripts/econ_query_api.py | grep -c "DaneIpcMonthly\|def load_dane_ipc_monthly"
0
```

Neither symbol existed in the parent commit. Neither symbol existed in commit `7afcd2ad6` (the predecessor commit cited in the verification memo). The diff for this commit shows `+69 lines` to `econ_query_api.py` introducing both for the first time.

**Why this matters from a senior-dev lens:**

* The "pre-staged" claim is a scope-drift red flag (Lens 6). If real, it would mean the DE silently inherited half-finished work from a non-committed stream — bad. If false (as is the case here), it means the trail says "I reused existing scaffolding" when in fact the DE authored the scaffolding inside this commit. That makes future readers re-derive the truth from `git show f7b03caac~1` instead of trusting the verification memo.
* The verification memo's `feedback_agent_scope` table at lines 122-134 lists `econ_query_api.py` under "Files **untouched**". This is also wrong — `git show f7b03caac --stat` shows `+69 -0` for that file. The memo's Files Modified section (lines 124-125) only mentions `y3_data_fetchers.py`. The 69 new lines in `econ_query_api.py` are silently elided.
* The 3-way reviewer protocol (`feedback_three_way_review`) depends on the commit's authored claims being a faithful summary of the diff. Reality Checker and Code Reviewer are both reading the same memo and the same commit message; both will inherit the same false premise unless one of them runs the parent-commit grep that I ran above.

**The code is fine.** The 69 lines added to `econ_query_api.py` are correct, in-scope (the wire-up genuinely needs a reader), follow project conventions, and are tested by Step A of the new test suite. The problem is paper-trail integrity, not code integrity.

**Required correction (M1):** before any downstream task (Task 11.N.2d-rev, Task 11.N.2.BR-bcb-fetcher) cites the verification memo, fix the memo to:

1. Remove the line "*`load_dane_ipc_monthly` and `DaneIpcMonthly` dataclass already existed (scaffolded under prior commit 7afcd2ad6 / earlier Rev-5.3.2 prep). No changes needed.*"
2. Move `econ_query_api.py` from "Files **untouched**" to "Files **modified**" with the +69-line accounting.
3. Add a brief explanation of the new symbols (`DaneIpcMonthly` dataclass, `load_dane_ipc_monthly` reader) and their consume-only contract.

The commit message itself is immutable (don't amend; create a follow-on note in the memo cross-referencing the discrepancy). This is a one-paragraph fix to the verification memo.

**Who owns the fix:** the orchestrator. Per `feedback_agent_scope`, this reviewer cannot edit the memo. Per the plan's review protocol, the orchestrator dispatches reviewers and consolidates their findings; this M1 finding is the consolidation point.

**Not a blocker for the code merging** — the code is correct. It IS a blocker for downstream-task dispatch trusting the memo without re-verification. The orchestrator should resolve M1 before dispatching Task 11.N.2.BR-bcb-fetcher, which is sequenced next per plan line 1834-1840.

---

### 7. Pre-existing remittance test failures — sufficient disclosure

The DE disclosed transparently in §"Pre-existing-failure disclosure" of the verification memo:

* The 2 failing tests (`test_load_cleaned_remittance_panel_*`) are in `scripts/tests/remittance/test_cleaning_remittance.py`.
* They were committed at `28d76cbb0`, which predates this task.
* Root cause: stale-test condition — the tests assert `pytest.raises(FileNotFoundError)` against a path where the fixture has since been committed at `939df12e1`, so the loader now raises `NotImplementedError` instead.
* The owning stream (Phase-A.0 remittance) closed at `2317f72a5` with `EXIT_NON_REMITTANCE` verdict.

**Senior-dev call:** the disclosure + cross-reference is sufficient. `feedback_agent_scope` explicitly forbids this stream from touching `scripts/cleaning.py` or `scripts/tests/remittance/`. Forcing the DE to "fix" out-of-scope tests would have been a scope violation.

**Recommendation (non-blocking, forward-looking):** the orchestrator should open a separate issue/task to retire the obsolete tests under the closed Phase-A.0 stream's epilogue, OR add an `@pytest.mark.skip(reason="superseded by Task 15 panel-integration test; awaiting cleanup")` decorator to the two stale tests. This is a 5-line change to a closed stream's test file; it should be its own narrowly-scoped task with a 1-paragraph plan note.

PASS on this dimension.

---

### 8. Functional-Python compliance — PASS

The implementation honors functional-python convention (per project CLAUDE.md "Frozen dataclasses, free pure functions, full typing"):

* `DaneIpcMonthly` — `@dataclass(frozen=True, slots=True)` (line 769). Test 1 explicitly asserts the frozen-mutation invariant (`pytest.raises((dataclasses.FrozenInstanceError, AttributeError))`).
* `load_dane_ipc_monthly` — pure free function. No mutation, no global state, no side effects beyond reading `conn`.
* `_fetch_dane_headline_broadcast` — pure free function. No mutation.
* `fetch_country_wc_cpi_components` — extended signature is keyword-only (`*, conn=None`), default-immutable (`None`), no positional ambiguity.
* No `class` introduction anywhere except the frozen dataclass. No inheritance. No `is`-relationship hierarchies.

**Type hints:** complete. `tuple[DaneIpcMonthly, ...]` (immutable, ordered). `date | None` for the optional bounds. `float | None` for the nullable column. `"duckdb.DuckDBPyConnection | None"` forward-referenced under `TYPE_CHECKING`.

**Sneak-mutations:** none found. The list-comprehension at line 388 (`levels = [r.ipc_index for r in rows]`) creates a new list; the rows tuple is not mutated. The pandas DataFrame construction at lines 390-397 creates a new DataFrame; no in-place modification.

PASS on this dimension.

---

## Summary table

| Lens                          | Verdict   | Notes                                                                                                                  |
|-------------------------------|-----------|------------------------------------------------------------------------------------------------------------------------|
| 1. API design (`conn` kwarg)  | PASS      | Right level of abstraction; advisory A1 for refactor at next source upgrade.                                            |
| 2. `ingest_y3_weekly` integ.  | PASS      | Gap is intentional per plan dependency chain; advisory A2 for Task 11.N.2d-rev follow-up.                              |
| 3. Test fixture organization  | PASS      | Correct file split; minor naming awkwardness (non-blocking).                                                            |
| 4. Maintenance burden         | PASS      | Pattern discoverable; 3-way docstring redundancy is a strong defense.                                                  |
| 5. Comment discipline         | PASS      | WHY-oriented; one micro-finding on `_ingested_at` field (non-blocking).                                                |
| 6. Scope drift / paper trail  | **M1**    | Commit message + memo claim "pre-staged" symbols that did NOT exist before this commit. Fix the memo.                   |
| 7. Remittance failures        | PASS      | Disclosure + cross-reference sufficient; out-of-scope per `feedback_agent_scope`.                                      |
| 8. Functional-Python          | PASS      | Frozen dataclass, pure free functions, complete typing, no sneak-mutations.                                            |

---

## Final verdict

**PASS-with-non-blocking-advisories.**

The code is correct, well-tested, scoped tightly, and follows project conventions. It will be maintainable in 6 months. The integration story with `ingest_y3_weekly` is intentionally deferred to Task 11.N.2d-rev per plan dependency chain.

The single must-fix-or-correct-the-record finding (M1) is **paper-trail-only**, not code-related. The orchestrator should patch the verification memo to remove the false "pre-staged" claim and accurately record the +69 lines added to `econ_query_api.py` before any downstream reviewer cites this memo as ground-truth scope.

Once M1 is corrected (estimated 5 minutes of memo edits), advisories A1 + A2 are flagged for the next-revision orchestrator (Task 11.N.2.BR-bcb-fetcher and Task 11.N.2d-rev respectively). Neither is required for this task to ship.

The implementation is code I would be willing to maintain in 6 months.

---

## Verification trail

1. `git show f7b03caac --stat` — confirms +666 lines / 4 files.
2. `git show f7b03caac~1:contracts/scripts/econ_query_api.py | grep -c "DaneIpcMonthly\|def load_dane_ipc_monthly"` → `0` (M1 evidence).
3. `git show 7afcd2ad6:contracts/scripts/econ_query_api.py | grep -c "DaneIpcMonthly\|def load_dane_ipc_monthly"` → `0` (M1 evidence — falsifies the verification memo's "scaffolded under 7afcd2ad6" claim).
4. `pytest scripts/tests/inequality/test_y3_co_dane_wire.py -v` → 9 passed, 0 failed (TDD red→green confirmed).
5. `pytest scripts/tests/inequality/ -v` → 66 passed, 1 skipped (full inequality suite green).
6. `grep -n "fetch_country_wc_cpi_components" scripts/econ_pipeline.py` → line 2905 confirmed not forwarding `conn` (Lens 2 evidence).
7. Plan body line 1864-1886 read; acceptance criteria at lines 1874-1880 cross-referenced against the verification memo's checklist at lines 138-149.
8. `pytest scripts/tests/` (full suite) → `2 failed, 1000 passed, 7 skipped` in 273s. The 2 failures are the disclosed pre-existing `test_cleaning_remittance.py::test_load_cleaned_remittance_panel_*` tests (Lens 7); all 1000 passing tests include the 9 new TDD tests for this task. Confirms DE's disclosure was accurate and the in-scope test surface is fully green.
