# Code Reviewer — Task 11.N.2.BR-bcb-fetcher (Rev-5.3.2)

**Reviewer:** Code Reviewer subagent
**Date:** 2026-04-25
**Commit:** `4ecbf2813` on `phase0-vb-mvp`
**Sibling precedent:** Task 11.N.2.CO-dane-wire (commit `f7b03caac`)
**Verdict:** **PASS-with-non-blocking-advisories**

---

## Executive summary

This is a clean, well-scoped, well-tested implementation. Provenance integrity is genuinely intact (verified: zero BR symbols pre-existed in `4ecbf2813~1` or `f7b03caac~1`), the IMF-IFS path is preserved byte-exact (function-body diff confirms zero changes), the schema migration is strictly additive and idempotent, the cumulative-index transform is mathematically correct (Δlog round-trip test asserts < 1e-9), and the in-scope test suite is fully green. The CO sibling's CORRIGENDUM lesson (mis-claimed provenance) was clearly internalized — the commit message explicitly distinguishes BR (fresh) from CO (pre-staged).

What follows are five non-blocking advisories ranked by potential impact. None warrant blocking the merge; all are improvements that either preserve invariants more robustly or improve future-proofing against locale / float-precision edge cases the BCB endpoint *currently does not exercise* but *could under unannounced upstream behavior changes*.

---

## Findings against the 10-item checklist

### 1. Schema migration discipline — PASS

- `_DDL_BCB_IPCA_MONTHLY` (econ_schema.py:710-717) uses `CREATE TABLE IF NOT EXISTS` — strictly additive, no destructive DDL.
- `migrate_bcb_ipca_monthly` (econ_schema.py:719-739) is idempotent: it inspects `SHOW TABLES`, returns `True` on first creation and `False` on no-op subsequent calls. Test `test_migrate_bcb_ipca_monthly_creates_table_idempotent` asserts both branches.
- `EXPECTED_TABLES` (econ_schema.py:14) is correctly extended with `"bcb_ipca_monthly"`.
- `init_db` (econ_schema.py:743-752) appends the DDL after the existing block — additive, preserves pre-existing call sites.
- Step Atomicity Protocol comment (CR-P5 / PM-P1) is correctly propagated from the Y₃ precedent.

### 2. HTTP integration safety — PASS with one nit

- **Timeout:** ✅ `fetch_bcb_sgs_433(...)` (econ_pipeline.py:3075-3095) defaults to `timeout=60`, propagated to `requests.get`.
- **Status-code check:** ✅ `resp.raise_for_status()` is called before `.json()`.
- **JSON parsing robustness:** ✅ `parse_bcb_sgs_433_json` (econ_pipeline.py:3050-3072) defensively `try/except`-s both the `dd/mm/yyyy` strptime and the `float()` conversion, and silently skips malformed rows. This is the correct stance for an endpoint where one bad row should not poison an otherwise-good window.
- **Date format `dd/mm/yyyy`:** ✅ Parsed via `datetime.strptime(raw_date, "%d/%m/%Y").date()` — Brazilian-locale-correct (zero ambiguity with the `dd/mm` US-vs-BR footgun the prompt called out).
- **Decimal handling for `valor`:** Live-probed the BCB endpoint at review time; observed payload is `[{"data":"01/03/2026","valor":"0.88"}]` — a period-decimal, period-correct for `float()`. No comma-decimal issue at the current endpoint.
- 💭 **Nit (defensive future-proofing, advisory only):** the BCB *publishing-platform-wide* convention is comma-decimal (e.g., `"0,88"`); SGS/433 happens to emit period-decimal because the endpoint is the JSON-direct one. If the upstream were ever to change the format under us, `float("0,88")` would `ValueError` and the row would be silently skipped (which is the safer outcome — neither a wrong number nor a crash — but the resulting silent staleness would be detectable only by the staleness gate). Consider one of: (a) a logger.warning on a nonzero `skipped_count`, (b) a one-line normalizer `raw_val.replace(",", ".")` before `float()`. Either is an additive change appropriate for a follow-up rather than this PR.

### 3. Cumulative-index correctness — PASS with one documentation nit

- `_BCB_IPCA_CUMULATIVE_BASE: Final[float] = 100.0` (econ_pipeline.py:3035) is module-level, `Final`, deterministic — not user-tunable. ✅
- Math (econ_pipeline.py:3098-3130): `level = base; level = level * (1 + obs.pct_change / 100.0)` — formula is correct.
- Δlog round-trip test (`test_cumulative_index_dlog_matches_pct_change_within_tolerance`, test file lines 297-333) asserts `|Δlog(I_t) - ln(1 + var_t/100)| < 1e-9` over the full ingest window. ✅ The 1e-9 tolerance is appropriate for IEEE-754 doubles over ~30 multiplications.
- **Float precision over hundreds of months:** the 27-row window currently used produces accumulated FP error well below 1e-12 — non-issue at current scale. However, the cumulative index is stored as `DOUBLE` and the round-trip test only verifies *first-difference* fidelity, not absolute level accumulation. For the current Y₃ pipeline this is the correct contract (the consumer is `compute_weekly_log_change`, which only sees Δlog), so flagging only as a nit.
- 💭 **Nit (documentation accuracy):** the docstring of `materialize_ipca_cumulative_index` (econ_pipeline.py:3098-3119) and several adjacent comments say "I_0 = 100 at the earliest observation" or "I_0 = 100 at base obs". Strictly speaking, the *seed* is 100 and the *first observation's* index is `100 × (1 + pct_0/100)` — i.e., I_0 ≠ 100, but I_seed = 100. The docstring acknowledges this carefully ("the first observed Δlog is faithful, not synthesised"), but the verification memo (line 24, table at line 38) and the schema-comment (econ_schema.py:710 docstring) read more loosely. This does not affect correctness — Δlog is invariant under positive global rescale, and the round-trip test catches the math. Suggest tightening the verification-memo prose on a future pass; no code change required.

### 4. TDD discipline preserved — PASS

- 16 tests authored across the 5 documented steps (A schema / B ingest / C reader / D dispatch / E cross-country safety) match the count claimed in the verification memo.
- The verification memo asserts a verified RED-phase first run (memo §"Strict TDD protocol"). Cross-checking the imports in each test against the symbols introduced in the same commit confirms every test would have failed `ImportError` against `4ecbf2813~1`. ✅
- Real-data integration (no fetch mocks) on Step B happy-path (`test_ingest_bcb_ipca_monthly_real_data_round_trip`, `test_ingest_bcb_ipca_monthly_idempotent_replays_byte_exact`, `test_cumulative_index_dlog_matches_pct_change_within_tolerance`). ✅ — per `feedback_real_data_over_mocks`.
- Mocks are scoped to the dispatch-routing tests (Step D `_fetch_imf_ifs_headline_broadcast`, Step E CO-DANE & KE-IMF) where the goal is *to assert the dispatch decision*, not to round-trip the real adapter — this is the legitimate use of monkey-patching and matches the CO sibling pattern.
- Coverage: schema migration, HTTP fetch, JSON parsing, cumulative materialization, UPSERT idempotence, reader, dispatch, IMF-IFS preservation, cross-country safety — all 9 axes from the prompt are exercised.

### 5. IMF-IFS path preservation — PASS (verified via diff)

- `diff` of `_fetch_imf_ifs_headline_broadcast` body between `f7b03caac` and `4ecbf2813` returns empty — function body is byte-exact preserved. ✅
- `test_fetch_imf_ifs_headline_broadcast_signature_preserved` (test file lines 586-599) locks the parameter list `["country", "start", "end"]` via `inspect.signature`. ✅
- The docstring of `fetch_country_wc_cpi_components` was edited to update the prose (BR moved from grouped "BR/KE" to a separate clause), but only the *prose*, not the dispatch logic — the IMF-IFS path is still the catch-all return at the bottom of the dispatch chain.

### 6. Headline-broadcast invariant — PASS (enforce-by-construction)

- `_fetch_bcb_headline_broadcast` (y3_data_fetchers.py:406-459) builds the DataFrame as:
  ```
  food_cpi=levels, energy_cpi=levels, housing_cpi=levels, transport_cpi=levels
  ```
  where `levels = [r.ipca_index_cumulative for r in rows]` is a **single shared list**. All four columns therefore reference the identical sequence — broadcast is enforced *at construction* (not via a runtime equality check that could drift). ✅ Pandas may copy on assignment, but the values are bit-equal by construction regardless.
- Test `test_fetch_country_wc_cpi_components_br_via_bcb_returns_4_components` validates the runtime invariant (`food == energy == housing == transport`) on the last row. ✅
- The empty-rows path correctly raises `Y3FetchError` with a windowed message — matches the CO and IMF-IFS sibling helpers' contracts.

### 7. Type discipline — PASS

- `BcbIpcaMonthly` (econ_query_api.py:826-849): `@dataclass(frozen=True, slots=True)` — matches the project pattern.
- `BcbIpcaObservation` (econ_pipeline.py:3037-3047): same pattern. ✅
- 💭 **Nit (cosmetic):** both dataclasses use the field annotation `date: date`, which under `from __future__ import annotations` is safe (annotation is a string at class-body time, resolves correctly when introspected). The CO sibling uses the identical idiom, so consistency is preserved. If a future cleanup wanted to remove this self-shadowing, the canonical alternative is `import datetime as _dt; date: _dt.date` — purely cosmetic.

### 8. `conn` kwarg consistency with CO — PASS

The dispatch chain (y3_data_fetchers.py:294-301):
```
if country == "EU":           return _fetch_eu_hicp_split(start, end)
if country == "CO" and conn:  return _fetch_dane_headline_broadcast(conn, start, end)
if country == "BR" and conn:  return _fetch_bcb_headline_broadcast(conn, start, end)
return _fetch_imf_ifs_headline_broadcast(country, start, end)
```

- BR mirrors CO exactly: `country == "X" and conn is not None → direct adapter; else → IMF-IFS catch-all`. ✅
- KE intentionally has no `conn`-opt-in branch — confirmed by `test_ke_still_routes_to_imf_ifs_path` (asserts that even with `conn=object()`, KE still dispatches to IMF-IFS). ✅
- The docstring update (lines 60-93 of the diff) accurately re-describes the new dispatch behavior — no documentation drift.

### 9. Provenance honesty — PASS (verified empirically)

Ran the prompt's provenance probe and a strengthening cross-check:

```
git show 4ecbf2813~1 -- scripts/econ_query_api.py | grep -cE "BcbIpcaMonthly|load_bcb_ipca_monthly"
→ 0  (no matches before this commit)

git show 4ecbf2813~1 -- scripts/econ_schema.py    | grep -cE "bcb_ipca_monthly|migrate_bcb_ipca_monthly|_DDL_BCB"
→ 0

git show 4ecbf2813~1 -- scripts/econ_pipeline.py  | grep -cE "BcbIpcaObservation|fetch_bcb_sgs_433|materialize_ipca|ingest_bcb_ipca|upsert_bcb"
→ 0

git show f7b03caac~1 -- scripts/econ_query_api.py | grep -cE "BcbIpcaMonthly|load_bcb_ipca_monthly|bcb_ipca_monthly"
→ 0  (cross-checked against the wider window per task instructions)
```

Every BR symbol enumerated in the verification memo's PROVENANCE INTEGRITY section is confirmed absent in both the immediate parent (`4ecbf2813~1`) and the older window (`f7b03caac~1`). The commit message's explicit "fresh-authored under this task — none pre-staged" claim is **accurate**.

The CO CORRIGENDUM lesson (DaneIpcMonthly + load_dane_ipc_monthly were pre-staged in an earlier stream and the original commit message overclaimed authorship) is correctly distinguished from the BR situation in both the commit message and the verification memo. ✅

### 10. `feedback_agent_scope` compliance — PASS

`git diff-tree --no-commit-id --name-only -r 4ecbf2813` returns exactly:

```
contracts/.scratch/2026-04-25-br-bcb-fetcher-result.md
contracts/scripts/econ_pipeline.py
contracts/scripts/econ_query_api.py
contracts/scripts/econ_schema.py
contracts/scripts/tests/inequality/test_y3_br_bcb_wire.py
contracts/scripts/y3_data_fetchers.py
```

— exactly the 6 files declared in-scope. **Zero drift** into `src/`, `test/*.sol`, `foundry.toml`, plan markdown, spec docs, `y3_compute.py`, or any sibling adapter (CO `_fetch_dane_headline_broadcast`, IMF `_fetch_imf_ifs_headline_broadcast`, `dane_ipc_monthly` schema). ✅

---

## Non-blocking advisories (ranked by usefulness)

🟡 **A1 — Cumulative-index docstring/comment precision.** Several places say "I_0 = 100 at the earliest observation"; strictly the *seed* is 100 and the *first observation's* index is `100 × (1 + pct_0/100)`. The docstring of `materialize_ipca_cumulative_index` already explains this carefully — propagate that precision to the schema comment (`econ_schema.py:710` block) and to the verification memo's table (line 24, line 38). Documentation-only; no code change.

🟡 **A2 — Defensive locale handling for the BCB `valor` field.** Endpoint currently emits period-decimal; if upstream ever switched to comma-decimal the parser would silently drop rows. Two cheap mitigations: (a) `raw_val = raw_val.replace(",", ".")` before `float()`, or (b) a logger.warning on `len(payload) - len(out)` mismatches. Defensive only.

💭 **A3 — Transaction granularity vs. row-by-row UPSERT.** `upsert_bcb_ipca_monthly` calls `conn.execute(...)` in a Python `for` loop. For 27 rows the cost is negligible; if this scales to multi-thousand-row backfills (unlikely for monthly cadence, but possible if the start window were extended back to 1980), DuckDB would be more efficient with a single `INSERT OR REPLACE ... SELECT * FROM (VALUES ...)` or a Pandas-roundtrip via `conn.register('df_name', df); conn.execute("INSERT OR REPLACE INTO ... SELECT * FROM df_name")`. Optimization, not correctness.

💭 **A4 — Field-name self-shadowing (`date: date`).** Stylistic only; works correctly under `from __future__ import annotations`. Project-wide consistency outweighs the cosmetic concern.

💭 **A5 — `ingest_bcb_ipca_monthly` return-type annotation.** Declared `dict[str, int]`, but `first_date` and `last_date` carry `str | None`, not `int`. Minor type-hint precision: `dict[str, int | str | None]` or a TypedDict. Documentation-only; no runtime impact.

---

## Things done well (call-outs)

🟢 **Provenance discipline learned from the CO CORRIGENDUM.** The commit message's explicit "fresh-authored ... none pre-staged ... contrasts with the CO precedent" is exactly the kind of self-correction a reviewer wants to see after a prior memo's mis-claim was caught.

🟢 **Headline-broadcast enforced by construction, not by check.** Single shared `levels` list assigned to all four columns — no possibility of silent drift between component slots.

🟢 **Anti-fishing guard via Δlog tolerance assertion.** The 1e-9 round-trip test on the cumulative-index transformation rules out a category of "I tweaked the base value to make the downstream regression behave" failures by demonstrating that the base value cannot influence the Δlog signal.

🟢 **Transaction-wrapped UPSERT** with explicit `BEGIN / COMMIT / ROLLBACK` — partial-write failure leaves the canonical DB consistent.

🟢 **Test isolation in Step E.** `test_co_with_conn_still_routes_to_dane` and `test_ke_still_routes_to_imf_ifs_path` lock in the cross-country isolation by monkey-patching the *other* country's adapter and asserting it fires — preventing a future regression where a BR change leaks into CO or KE routing.

---

## Final verdict

**PASS-with-non-blocking-advisories.**

The implementation is correct, well-tested, scope-compliant, and provenance-honest. All 10 checklist items pass. The 5 advisories above are all either documentation precision, defensive future-proofing, or cosmetic — none of them justify blocking the commit, and several are appropriate as a follow-up clean-up rather than rework on this PR.

Recommend the foreground orchestrator merge after the parallel Reality Checker and Senior Developer reviews converge.

---

## File pointers

- Commit under review: `4ecbf2813` (HEAD of `phase0-vb-mvp` at review time)
- Sibling precedent: `f7b03caac` (CO-dane-wire) + `be4048ec6` (CO 3-way + CORRIGENDUM)
- Verification memo: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-br-bcb-fetcher-result.md`
- Files reviewed (all absolute):
  - `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/econ_schema.py`
  - `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/econ_pipeline.py`
  - `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/econ_query_api.py`
  - `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/y3_data_fetchers.py`
  - `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/tests/inequality/test_y3_br_bcb_wire.py`
