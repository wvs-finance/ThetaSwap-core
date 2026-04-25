# Senior Developer Review — Task 11.N.2.BR-bcb-fetcher

**Reviewer:** Senior Developer (third of three; alongside Code Reviewer + Reality Checker per `feedback_implementation_review_agents`)
**Commit:** `4ecbf2813` on `phase0-vb-mvp`
**Date:** 2026-04-25
**Reviewer lens:** "Is this code I would want to maintain in 6 months? Does it integrate cleanly with the rest of the system? Does it learn from the CO-precedent's M1 finding?"
**Sibling precedent:** Task 11.N.2.CO-dane-wire (commit `f7b03caac`, prior SD review verdict: PASS-with-non-blocking-advisories + M1 paper-trail correction)

**Verdict:** **PASS-with-non-blocking-advisories**

The implementation is functionally correct, type-safe, scoped tightly, well-tested, and integrates cleanly with the CO-precedent. The DE explicitly addressed the prior CO M1 finding (false-pre-staging-claim) — provenance is now byte-exact verifiable. Three non-blocking advisories (B1, B2, B3) and one minor inconsistency note (N1) are documented below. None block merge. The code is maintenance-grade.

---

## Lens-by-lens findings

### 1. Pattern consistency with CO sibling — PASS

The BR dispatch (`_fetch_bcb_headline_broadcast`) cleanly mirrors the CO dispatch (`_fetch_dane_headline_broadcast`). Direct comparison of the diff at `y3_data_fetchers.py:294` and `:296`:

```
if country == "CO" and conn is not None:
    return _fetch_dane_headline_broadcast(conn, start, end)
if country == "BR" and conn is not None:
    return _fetch_bcb_headline_broadcast(conn, start, end)
```

* **Identical guard semantics:** both branches require `conn is not None`; both default to IMF-IFS fallback otherwise.
* **Identical positional argument ordering:** `(conn, start, end)` in both `_fetch_<source>_headline_broadcast` helpers.
* **Identical error-handling pattern:** both raise `Y3FetchError` on empty result with `f"<table>: no rows in [{start}, {end}]"` shape.
* **Identical broadcast contract:** levels list, then four columns (food/energy/housing/transport) all assigned the same `levels` list — preserving design doc §10 row 2 substitution-fallback rule.
* **Identical local-import pattern for the canonical reader** (avoids circular import) — the CO precedent's hidden-invariant comment was carried forward verbatim.

**One stylistic asymmetry (non-blocking, no fix needed):** the DANE helper consumes `r.ipc_index` (a single field on `DaneIpcMonthly`); the BCB helper consumes `r.ipca_index_cumulative`. The naming differs because the underlying source semantics differ (DANE publishes a level-index already; BCB publishes variation %). This is inherent to the source contract, not divergence in the dispatcher abstraction.

PASS on this dimension.

---

### 2. API design durability — recommendation: **DO NOT yet refactor**

The prior CO review's A1 advisory said: "Once Task 11.N.2.BR-bcb-fetcher lands … flag as a refactor candidate when the third source upgrade lands or when `fetch_country_wc_cpi_components` exceeds ~50 SLOC."

I traced the current state. After the BR commit, `fetch_country_wc_cpi_components`'s **dispatch body** (post-docstring) is 5 lines of straight-line conditional code:

```
if country == "EU":
    return _fetch_eu_hicp_split(start, end)
if country == "CO" and conn is not None:
    return _fetch_dane_headline_broadcast(conn, start, end)
if country == "BR" and conn is not None:
    return _fetch_bcb_headline_broadcast(conn, start, end)
return _fetch_imf_ifs_headline_broadcast(country, start, end)
```

This is **5 lines, 4 branches, perfectly readable**. The docstring explaining the per-country behavior is verbose but is the right place for that explanation — the docstring is the documentation, the body is the dispatcher.

**Express recommendation, not hedge:** **the `_SOURCE_DISPATCH` dict refactor should NOT happen now.** Reasoning:

1. **Premature abstraction tax.** A `dict[CountryCode, Callable]` selector would force every branch into an unconditional `def _branch(conn, start, end) -> pd.DataFrame` signature, papering over that EU's branch does NOT take `conn` and that the IMF-IFS fallback dispatches by `country` (which the dict key would have to encode redundantly). The result would be more code, not less, with worse type-checker support.
2. **The 4-branch shape is the natural shape.** Two branches are `conn`-conditional (CO, BR), one is unconditional source-specific (EU), one is the country-dispatched fallback (BR-without-conn, KE). A dict cannot represent the conditional-on-conn axis without a parallel dispatch table or a wrapper function — neither of which is simpler than the current shape.
3. **Future country additions remain trivially additive.** A δ-EU upgrade or a future KE source upgrade is one new private helper + one new `if country == "XX" and conn is not None: return ...` line. The marginal cost is ~3 lines.
4. **The third source upgrade has NOT landed.** The A1 trigger condition was "third source upgrade" — Task 11.N.2.OECD-probe is diagnostic-only per Rev-5.3.2, NOT a fetcher consumer. There is no third consumer source.

**Reconsider the refactor only if:**
- A fourth fetcher branch is added (i.e., a δ-EU upgrade lands AND a KE upgrade lands), OR
- The dispatch body crosses ~10 SLOC (which would require more than 4 conditional source branches).

Today's body is clean. PASS on this dimension; no refactor needed.

---

### 3. Cumulative-index utility design — PASS-with-advisory

`materialize_ipca_cumulative_index` at `econ_pipeline.py:3088`:

* **Pure free function.** No I/O, no class, no global state. ✅ Functional-Python compliant.
* **Frozen immutable input dataclass** (`BcbIpcaObservation` at line 3027 — `@dataclass(frozen=True, slots=True)`).
* **Output is immutable tuples** in a list (return type `list[tuple[date, float, float]]`). The list is mutable but the elements are tuples, which is the correct trade-off for a pipeline-stage intermediate.
* **Default base value is parameterized** (`*, base: float = _BCB_IPCA_CUMULATIVE_BASE`) — a caller can override for testing or alt-source experimentation, but the default is the documented deterministic 100.0.
* **Base-value documentation is excellent.** The docstring at lines 3097–3105 explicitly states:
    * "The base-value choice is methodologically arbitrary"
    * "Δlog is invariant under a global rescale of the index"
    * "no tuning"
    * Cross-references the test that locks this in (`test_cumulative_index_dlog_matches_pct_change_within_tolerance`)
* **Anti-fishing-disciplined.** Verification memo §"Anti-fishing guards honored" line 120 explicitly states: "Cumulative-index base value not tuned. I_0 = 100 was chosen deterministically before measuring any downstream metric." The 1e-9 tolerance test is the safety net.

**Could it be reused for future country sources publishing variations only?** The function is **named** `materialize_ipca_cumulative_index` — IPCA-specific. The implementation is **algorithm-specific**, not source-specific (`level *= (1 + var/100)` is the universal compounding formula). A future country with the same shape could reuse the math but would need to either:
- Rename the function (`materialize_pct_change_cumulative_index`) — minor refactor
- Wrap it in a source-agnostic alias

> **Advisory B1 (non-blocking, forward-looking):** when a third source publishing variation% (not levels) lands — e.g., Mexico INEGI INPC or Argentina INDEC IPC — extract `materialize_ipca_cumulative_index` to a name-neutral `materialize_cumulative_index_from_pct_changes` and have `BcbIpca` and the new source consume the same primitive. Until then, the IPCA-specific name signals that this is a BCB-specific utility, which is correct documentation.

PASS on this dimension.

---

### 4. HTTP integration robustness — PASS-with-2-advisories

`fetch_bcb_sgs_433` at `econ_pipeline.py:3068`:

```python
def fetch_bcb_sgs_433(
    start: date,
    end: date,
    *,
    timeout: int = 60,
) -> list[BcbIpcaObservation]:
    url = _BCB_SGS_433_URL.format(...)
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    parsed = parse_bcb_sgs_433_json(payload)
    parsed.sort(key=lambda o: o.date)
    return parsed
```

**What is good:**
* **Timeout is parameterized** (`timeout=60`, kwarg-only). Caller can override for test scenarios. Default 60s is reasonable for a single GET with a small payload.
* **`raise_for_status()` correctly bubbles 4xx/5xx as `requests.HTTPError`** rather than swallowing them.
* **Defensive parsing in `parse_bcb_sgs_433_json`** (line 3045): missing keys, malformed dates, malformed numbers — each path skips the bad row rather than crashing. This is appropriate for a public source where the schema could drift.
* **Sort is post-fetch** — robust to BCB API ordering changes.

**What is missing (advisories):**

> **Advisory B2 (non-blocking):** No retry logic for transient failures. A single 503 / 504 / connection timeout will propagate up to `ingest_bcb_ipca_monthly` and abort the ingest. For a monthly-cadence pipeline (run once a month or on-demand), a single failure is annoying-but-acceptable — the operator can re-run. For a CI-scheduled cron, retry would be defensive. Consider wrapping the `requests.get` call with a tenacity-style retry (3 attempts, exponential backoff, retry on `(ConnectionError, Timeout, HTTPError-with-5xx)`). This is consistent with how the project already handles flaky public-API fetches in other modules — RC's review may surface specific precedents. **No fix required for this task.**

> **Advisory B3 (non-blocking):** No explicit rate-limit handling. BCB SGS direct API is generally permissive (no documented per-IP RPS cap on the public series endpoint), but a User-Agent header is a courtesy that makes the operator identifiable to BCB if they ever introduce throttling. Today the request goes out as `requests`'s default `User-Agent: python-requests/...`, which is anonymous-but-functional. Consider adding `headers={"User-Agent": "abrigo-y3-pipeline/0.1 (https://github.com/<repo>)"}` once the project decides on a canonical UA string. **Not required for this task.**

**For a monthly-cadence ingest:** the current robustness level is **adequate**. The function is idempotent (UPSERT on PK), so a re-run after failure is safe. The transaction wrapper at `ingest_bcb_ipca_monthly:3173` ensures partial-write rollback. The acceptance criterion (cutoff ≥ 2026-02-01) is verifiable each run, so a stale or empty response surfaces immediately.

PASS on this dimension; B2 + B3 are forward-looking nice-to-haves.

---

### 5. Test fixture organization — PASS

The new file `test_y3_br_bcb_wire.py` (615 lines, 16 tests) follows the CO sibling pattern faithfully:

* **Same path resolution helper** (`_open_canonical_readwrite` / `_open_canonical_readonly` / `_open_inmemory`) — copy-paste-equivalent to the CO test file's helpers.
* **Same canonical-DB skip pattern** (`pytest.skip(...)` if the file is missing).
* **Same Step A/B/C/D/E organizational structure** (schema migration / ingest / reader / dispatch / cross-country safety) — directly parallels the CO file's Step A/B/C/D structure with one additional "E" step for cross-country safety (which the CO file did NOT have because there was no prior wired country at that time).
* **Naming consistency:** `test_y3_br_bcb_wire.py` matches `test_y3_co_dane_wire.py`'s 3-segment slug pattern. The prior CO review noted the slug as "slightly awkward" — the BR file is consistent with that precedent, which is the right call (do NOT diverge for cosmetic reasons).
* **Cross-country isolation tests** (Step E):
    * `test_co_with_conn_still_routes_to_dane` — locks in that the BR change does not regress CO.
    * `test_ke_still_routes_to_imf_ifs_path` — locks in that KE remains unchanged.
    
    These are **net-new** vs. the CO test file and are exactly the right tests to add now that two countries are wired.

**Minor inconsistency note (N1, non-blocking):** The CO test file ended at Step D. The BR test file adds Step E. A future maintainer reading the CO file may not realize the cross-country isolation pattern was retroactively introduced in the BR commit. **Not actionable here** — modifying the CO test file would be out of scope per `feedback_agent_scope`. If a future task touches `test_y3_co_dane_wire.py`, consider backfilling a "Step E — cross-country isolation" section there for parity.

PASS on this dimension.

---

### 6. `ingest_y3_weekly` plumbing parity — INTENTIONAL gap, confirmed

I re-confirmed the gap from the CO review, applied to BR:

```
$ grep -n "fetch_country_wc_cpi_components" contracts/scripts/econ_pipeline.py
2877:        fetch_country_wc_cpi_components,
2905:            comp = fetch_country_wc_cpi_components(country, start, end)
```

`econ_pipeline.py:2905` does NOT forward `conn`. Under the current commit:

* CO with conn → DANE (when called directly with `conn`)
* CO under `ingest_y3_weekly` (no conn forwarded) → IMF-IFS fallback ❌ — CO upgrade not yet plumbed through the production ingest
* BR with conn → BCB (when called directly with `conn`)
* BR under `ingest_y3_weekly` (no conn forwarded) → IMF-IFS fallback ❌ — BR upgrade not yet plumbed through the production ingest

**Is this in scope for Task 11.N.2.BR-bcb-fetcher?** Plan body line 1890–1913 directs this task to (a) add the new fetcher path, (b) add the cumulative-index utility, (c) add the new DuckDB raw table, (d) wire BR-with-conn to dispatch to the new path. The plan does NOT direct this task to patch `ingest_y3_weekly`'s call site at line 2905. That work is **explicitly Task 11.N.2d-rev's** per plan dependency line 1951:

> "**Dependency:** Task 11.N.2.BR-bcb-fetcher AND Task 11.N.2.CO-dane-wire (both fetcher branches must commit before the re-ingest can consume the BR + CO upgrades)."

The verification memo's "Cross-country safety" tests confirm that the new wire-up is reachable only via direct `conn`-forwarding callers — which is precisely the contract shape that Task 11.N.2d-rev needs to consume.

**Confirmed:** the gap is **intentional, plan-correct, not a defect**. The CO review's A2 advisory remains the open follow-up: Task 11.N.2d-rev MUST patch `econ_pipeline.py:2905` to forward `conn`, AND must do so for both CO and BR simultaneously (both branches will lift at the same patch site).

> **Reaffirmed advisory (carryover from CO A2):** Task 11.N.2d-rev's verification memo MUST cite the patch to `econ_pipeline.py:2905` as one of the in-scope deliverables. The simplest patch — `fetch_country_wc_cpi_components(country, start, end, conn=conn)` — works for both CO and BR because the dispatcher is `country == "XX" and conn is not None`-guarded for both branches. Pass-through is the senior-dev recommendation; per-country if-branches in `econ_pipeline.py` would push routing logic into the wrong layer.

PASS on this dimension because the gap is correct per plan dependency chain.

---

### 7. Provenance integrity — **PASS** (DE explicitly addressed prior CO M1)

The CO review surfaced a **must-fix-or-correct-the-record** finding (M1) on the false-pre-staging claim. The BR commit's verification memo lines 141–167 explicitly addresses this:

> **Verbatim from the BR memo (line 161-167):**
>
> *"Verified absent in `git show f7b03caac~1`: all symbols above. None were pre-staged in a prior stream — the entire surface area was authored under this task. This contrasts with the CO precedent, where `DaneIpcMonthly` and `load_dane_ipc_monthly` had been pre-staged in `econ_query_api.py` by an earlier stream and were merely consumed by the CO wire. (The CO memo's CORRIGENDUM noted this distinction; the present task explicitly does not repeat the mis-claim.)"*

I verified this claim independently:

```
$ git show 4ecbf2813~1:contracts/scripts/econ_pipeline.py | grep -cE "_BCB_SGS_433_URL|BcbIpcaObservation|parse_bcb_sgs_433_json|fetch_bcb_sgs_433|materialize_ipca_cumulative_index|upsert_bcb_ipca_monthly|ingest_bcb_ipca_monthly|_BCB_IPCA_CUMULATIVE_BASE"
0
$ git show 4ecbf2813~1:contracts/scripts/econ_query_api.py | grep -cE "BcbIpcaMonthly|load_bcb_ipca_monthly"
0
$ git show 4ecbf2813~1:contracts/scripts/econ_schema.py | grep -cE "_DDL_BCB_IPCA_MONTHLY|migrate_bcb_ipca_monthly|bcb_ipca_monthly"
0
$ git show 4ecbf2813~1:contracts/scripts/y3_data_fetchers.py | grep -cE "_fetch_bcb_headline_broadcast"
0
```

**All 14 symbols listed in the verification memo's PROVENANCE INTEGRITY block are absent in the parent commit.** The provenance claim is true.

**Process finding:** the DE explicitly internalized the prior CO M1 review finding and used it as a guardrail for this task's verification memo. This is an **excellent** sign of an iterative-improvement loop. The memo even calls out the contrast paragraph explicitly so future readers don't re-derive the trail integrity.

**Note on memo accuracy elsewhere (N1, non-blocking):** the memo's "Files Modified" table at lines 173–180 correctly accounts for all 6 in-scope files including `econ_query_api.py` (+70 lines per `git show 4ecbf2813 --stat`). The CO memo's silent elision of `econ_query_api.py` from the Files-Modified section is NOT repeated here. Memo accounting is byte-correct.

PASS on this dimension. The DE earned the trust back that the CO precedent's M1 finding cost.

---

### 8. Functional-Python compliance — PASS

Spot-check across the diff:

* `BcbIpcaObservation` — `@dataclass(frozen=True, slots=True)` at line 3027. ✅
* `BcbIpcaMonthly` — `@dataclass(frozen=True, slots=True)` at line 833. ✅
* `parse_bcb_sgs_433_json` — pure function. No mutation of input. Output is a fresh list. ✅
* `fetch_bcb_sgs_433` — pure-ish (HTTP I/O is bounded; no global state mutation). ✅
* `materialize_ipca_cumulative_index` — pure. No I/O, no global state. ✅
* `upsert_bcb_ipca_monthly` — has DuckDB side effects (INSERT OR REPLACE), but the side effects are explicit and bounded by the connection. The function takes `conn` as an argument, doesn't reach for global state. ✅
* `ingest_bcb_ipca_monthly` — orchestrator function; combines pure pieces (parse, materialize) with bounded I/O (fetch, upsert). The transaction-wrap pattern at lines 3193–3198 is correct (begin / commit / rollback-on-exception). ✅
* `_fetch_bcb_headline_broadcast` — pure free function (DuckDB read + pandas DataFrame construction; no mutation of `conn`). ✅
* `load_bcb_ipca_monthly` — pure free function. Returns `tuple[BcbIpcaMonthly, ...]` (immutable, ordered). ✅
* No inheritance anywhere. ✅
* No `class` keyword except for the two frozen dataclasses. ✅
* Type hints: complete. `tuple[BcbIpcaMonthly, ...]`, `list[BcbIpcaObservation]`, `list[tuple[date, float, float]]`, `date | None`, `dict[str, int]`. ✅
* Forward-reference `"duckdb.DuckDBPyConnection"` in `_fetch_bcb_headline_broadcast` parameter type — gated under `TYPE_CHECKING` at the module level. ✅

**Sneak-mutation check:** none found.
* `parse_bcb_sgs_433_json:3045` builds `out: list[BcbIpcaObservation]` and returns it; never mutates the input `payload`.
* `fetch_bcb_sgs_433:3081` calls `parsed.sort(...)` on its own local list — that's not external mutation.
* `materialize_ipca_cumulative_index:3120` builds `rows: list[tuple[...]]` from scratch; never mutates `observations`.

**Mutability-discipline note:** `materialize_ipca_cumulative_index` returns `list[tuple[...]]` rather than `tuple[tuple[...], ...]`. The list is local-scoped through the ingest pipeline and not returned to long-lived state. Acceptable trade-off (keeping construction simple); the immutability story is preserved at the public API boundary because `ingest_bcb_ipca_monthly` consumes-then-discards the list.

PASS on this dimension.

---

### 9. Schema migration patterns — PASS

`migrate_bcb_ipca_monthly` at `econ_schema.py:728`:

```python
def migrate_bcb_ipca_monthly(conn: duckdb.DuckDBPyConnection) -> bool:
    existing = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    already = "bcb_ipca_monthly" in existing
    conn.execute(_DDL_BCB_IPCA_MONTHLY)
    return not already
```

**Pattern parity check** vs. the precedents `migrate_onchain_y3_weekly`, `migrate_dane_ipc_monthly` (which I confirmed exists in the same file family — same idempotent-DDL pattern):

* **Same return-bool semantics** (`True` if newly created, `False` if pre-existed). ✅
* **Same idiom for existence-check** — `SHOW TABLES` set membership. ✅
* **Same `CREATE TABLE IF NOT EXISTS` DDL** so the migration is idempotent under either branch (already-exists → no-op; not-exists → create). ✅
* **Same `EXPECTED_TABLES` registration** (line 42 of the schema, the new table is added to the frozenset). ✅
* **Same `init_db` registration** (line 752, the new DDL is appended to the bootstrap path). ✅
* **Step Atomicity Protocol cited in the docstring** (lines 740–745) — references CR-P5 / PM-P1 propagated from Task 11.N.2b / 11.N.2d. This is project-conventional safety guidance: in-memory probe first, then canonical mutation.

**Common pitfalls checked:**

1. **Idempotence:** ✅ `INSERT OR REPLACE` at the upsert layer + `CREATE TABLE IF NOT EXISTS` at the schema layer = re-running the ingest on the same window yields a byte-exact final state.
2. **Error handling:** ✅ The migration is a single DDL statement; failure propagates as a DuckDB error. The ingest wrapper at `ingest_bcb_ipca_monthly` calls migration BEFORE `BEGIN TRANSACTION`, so a migration failure aborts before any transactional work — clean.
3. **Schema drift detection:** the test suite Step A includes `test_bcb_ipca_monthly_schema_columns_match` (verified by reading test file lines 96 onward) — locks in the four-column shape (`date`, `ipca_pct_change`, `ipca_index_cumulative`, `_ingested_at`). Any future schema change would break the test, surfacing the drift immediately.
4. **PRIMARY KEY collision risk:** `date` is PK; BCB SGS/433 returns one row per month (always `01/MM/YYYY`). The dedup behavior of `INSERT OR REPLACE` is correct for this source — re-fetch overwrites rather than fails.

**One micro-note (informational):** the DDL hardcodes `_ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp`. This is the same pattern as `dane_ipc_monthly`, so it is convention-consistent. If a future refactor wants to surface `_ingested_at` for staleness diagnostics (the prior CO review's micro-finding), the column already exists at the DDL layer; only the dataclass + reader need to be extended. No action here.

PASS on this dimension.

---

## Summary table

| Lens                                  | Verdict   | Notes                                                                                                                        |
|---------------------------------------|-----------|------------------------------------------------------------------------------------------------------------------------------|
| 1. Pattern consistency with CO        | PASS      | BR dispatch mirrors CO; same guard, ordering, error-handling, broadcast contract, local-import pattern.                       |
| 2. API design durability              | PASS      | DO NOT refactor to `_SOURCE_DISPATCH` dict yet — current 4-branch shape is naturally readable and trivially additive.         |
| 3. Cumulative-index utility           | PASS      | Pure free function; base value documented + tested as deterministic; advisory B1 for name-neutralization at 3rd source.       |
| 4. HTTP integration robustness        | PASS      | Adequate for monthly cadence; B2 (retry) + B3 (UA header) are forward-looking nice-to-haves, not required.                    |
| 5. Test fixture organization          | PASS      | Follows CO pattern; net-new Step E cross-country isolation tests are the right addition.                                       |
| 6. `ingest_y3_weekly` plumbing parity | PASS      | Gap is intentional per plan; Task 11.N.2d-rev MUST patch `econ_pipeline.py:2905` to forward `conn` (carryover from CO A2).    |
| 7. Provenance integrity               | PASS      | DE explicitly internalized prior CO M1; all 14 BR symbols verified absent in `4ecbf2813~1`; memo accounting byte-correct.     |
| 8. Functional-Python compliance       | PASS      | Frozen dataclasses, pure free functions, complete typing, no sneak-mutations.                                                  |
| 9. Schema migration patterns          | PASS      | Mirrors `migrate_onchain_y3_weekly` / `migrate_dane_ipc_monthly`; idempotent; schema drift locked by Step A test.              |

---

## Final verdict

**PASS-with-non-blocking-advisories.**

The code is correct, well-tested, scoped tightly per `feedback_agent_scope`, and follows project conventions. Provenance integrity is verifiable and the DE explicitly addressed the prior CO precedent's M1 paper-trail finding — earning back the trust that the CO commit cost.

The integration story with `ingest_y3_weekly` remains intentionally deferred to Task 11.N.2d-rev per plan dependency chain. The carryover advisory from the CO review (patch `econ_pipeline.py:2905` to forward `conn`) now applies to both CO and BR simultaneously and remains the next-orchestrator's responsibility — a single one-line patch will lift both branches.

Three non-blocking advisories are flagged for future work:

* **B1** (when third pct-change-source lands): rename `materialize_ipca_cumulative_index` to `materialize_cumulative_index_from_pct_changes`.
* **B2** (production-hardening, optional): add tenacity-style retry around `requests.get` in `fetch_bcb_sgs_433`.
* **B3** (production-hardening, optional): add a project-canonical `User-Agent` header to BCB requests.

None block merge. None are required for this task to ship.

The express recommendation on the `_SOURCE_DISPATCH` refactor is **DO NOT refactor now** — the current 4-branch shape is more readable and more type-checker-friendly than a callable-map alternative; the trigger condition for revisiting is "a fourth fetcher branch lands, OR dispatch body crosses ~10 SLOC."

The implementation is code I would be willing to maintain in 6 months.

---

## Verification trail

1. `git show 4ecbf2813 --stat` — confirms +1248 / -11 across 6 files (matches verification memo file table).
2. `git show 4ecbf2813~1:contracts/scripts/econ_pipeline.py | grep -cE "_BCB_SGS_433_URL|BcbIpcaObservation|parse_bcb_sgs_433_json|fetch_bcb_sgs_433|materialize_ipca_cumulative_index|upsert_bcb_ipca_monthly|ingest_bcb_ipca_monthly|_BCB_IPCA_CUMULATIVE_BASE"` → `0` (provenance verified for 8 pipeline symbols).
3. `git show 4ecbf2813~1:contracts/scripts/econ_query_api.py | grep -cE "BcbIpcaMonthly|load_bcb_ipca_monthly"` → `0` (provenance verified for 2 query-api symbols).
4. `git show 4ecbf2813~1:contracts/scripts/econ_schema.py | grep -cE "_DDL_BCB_IPCA_MONTHLY|migrate_bcb_ipca_monthly|bcb_ipca_monthly"` → `0` (provenance verified for 3 schema symbols).
5. `git show 4ecbf2813~1:contracts/scripts/y3_data_fetchers.py | grep -cE "_fetch_bcb_headline_broadcast"` → `0` (provenance verified for 1 fetcher symbol).
6. `grep -n "fetch_country_wc_cpi_components" contracts/scripts/econ_pipeline.py` → line 2905 confirmed not forwarding `conn` (Lens 6 evidence; intentional per plan dependency chain).
7. Plan body lines 1890–1913 read; acceptance criteria cross-referenced against verification memo §"Acceptance-criterion checklist" (lines 95–114). All 8 checklist items map 1:1 to plan acceptance criteria; verification memo claims them all met.
8. CO sibling SD review (`2026-04-25-co-dane-wire-review-senior-developer.md`) re-read for advisory carryover (A1, A2) and M1 finding tracking; M1 explicitly addressed in BR memo §PROVENANCE INTEGRITY.
9. Test file structure scanned — Step A/B/C/D/E organization confirmed; cross-country isolation tests at Step E are net-new vs. CO precedent (the right tests at the right time).
10. Diff fully read across all 5 code files (y3_data_fetchers, econ_schema, econ_query_api, econ_pipeline, test_y3_br_bcb_wire) — no unexpected hunks; no out-of-scope edits to `dane_ipc_monthly`, `_fetch_dane_headline_broadcast`, `_fetch_imf_ifs_headline_broadcast`, `y3_compute.py`, or any spec/plan body.
