# Senior Developer Review — Task 11.O Rev-2 Phase 5a Data-Prep

**Reviewer:** Senior Developer (parallel with CR + RC per `feedback_implementation_review_agents`)
**Commit under review:** `2eed63994` on `phase0-vb-mvp`
**Spec consumed:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` @ `d9e7ed4c8`
**Reviewer scope:** API design, maintainability, scaling-to-Rev-3, test organization, downstream-consumer ergonomics. Read-only. No edits.
**Verdict:** **PASS-with-non-blocking-advisories** (3 advisories — all forward-looking; none block Phase 5b handoff).

---

## 1. Summary

The Data Engineer's 14-row panel-prep deliverable is a clean, well-typed, single-responsibility module that I would happily inherit on a senior-eng rotation. The public API is conservative and honest (it does not pretend to support OLS-fit-time concerns it intentionally defers); the SQL composition is parametric without going overboard; the Friday-anchor reconciliation is documented in three load-bearing places (CTE, manifest, validation, tests); the parquet writer was an honest call to use DuckDB-native `COPY` rather than introduce pyarrow as a dep; and the artifact set is structured so Analytics Reporter (Phase 5b) can consume it without re-querying DuckDB.

I have three forward-looking advisories about (a) hoisting the Friday-anchor translation to a named helper for Rev-3 ζ-group reuse, (b) marking `THREE_PARSIMONIOUS_CONTROLS` as a "row-recipe constant" so future ad-hoc subsets don't promote-themselves to module-level, and (c) the `audit_panel` raise-on-empty contract bumping into the deferred-row write path. None block Phase 5b.

---

## 2. Tool-by-tool tally (target ≤ 15)

| # | Tool call | Purpose |
|---|---|---|
| 1 | `git show 2eed63994 --stat` | Provenance + scope verification |
| 2 | `Read manifest.md` | Row-table + downstream contract |
| 3 | `Read data_dictionary.md` | Variable provenance |
| 4 | `Read validation.md` | Outlier + anchor + admitted-set posture |
| 5 | `Read phase5_data_prep.py` | Module body |
| 6 | `Read test_phase5_data_prep.py` | Test organization |
| 7 | `Read queries.md` | SQL-fragment composition |
| 8 | `pytest test_phase5_data_prep.py -v` | Green-phase verification |
| 9 | `pytest scripts/tests/ -q` | Pre-existing-failure baseline (background) |
| 10 | `grep spec headings` | Phase 5b downstream needs |
| 11 | `Read _audit_summary.json` | Machine-readable audit format |
| 12 | `pytest test_y3_br_bcb_wire.py -q` | Confirm BR BCB failures are flaky-not-real |
| 13 | `git log` of remittance test | Confirm 2 remittance failures predate DE |
| 14 | `git diff 2eed63994..HEAD` | DE commit IS HEAD verification |

14 tool uses; on budget.

---

## 3. Senior-Developer findings

### 3.1 API design quality of `phase5_data_prep.py` — PASS

**Public surface:**

```python
build_panel(
    conn: duckdb.DuckDBPyConnection,
    *,
    x_d_kind: str,
    y3_methodology: str,
    controls: Sequence[str],
    locf_tail_cutoff: date | None = None,
) -> pd.DataFrame
```

* **Kwarg-only after `conn` is the right call.** Three of the four substantive arguments are easy to swap by accident (`x_d_kind` and `y3_methodology` are both string-literals; `controls` is a tuple). Forcing kwarg-only at the call site removes the largest class of off-by-name bugs on a 14-row script.
* **`locf_tail_cutoff: date | None = None` is parameterized cleanly.** It's the ONE genuine row-shape parameter that doesn't fit the `(x_d_kind, y3_methodology, controls)` triple. Modeling it as a sentinel default keeps Row 1 (the canonical call) ergonomic while letting Row 3 opt in. Better than threading a richer `RowConfig` dataclass for one optional parameter.
* **Does it scale to 14 rows + 4 ζ-group rows?** Yes. Of the 14 rows: 8 are direct `build_panel` calls (Rows 1, 2, 3, 4, 6, 7, 8, plus Rows 11–14 which share Row 1's panel). Rows 5, 11, 12, 13 are "same panel as Row 1, transform at fit time" — correctly handled by writing the same parquet content to a uniquely-named file rather than parameterizing `build_panel` with `lag=`, `student_t=`, `hac_bandwidth=` flags it has no business carrying. **The function defends itself against feature-creep.** Future Rev-3 ζ-group rows (quantile, GARCH-X, lower-tail) are estimator-stage concerns and should NOT be threaded through `build_panel`; the panel-prep contract is "X_d × Y₃ × controls × optional cutoff," and the spec-author's analytical concerns belong in the Analytics Reporter at fit time. This is correct senior-eng decomposition.

**`PanelAuditReport` dataclass:**

* Frozen, slotted, fully typed. `(n_obs, n_x_d_nonzero, dt_min, dt_max, n_null_y3)`. Useful surface for Analytics Reporter to construct its manifest table programmatically. **PASS.**
* Minor: the rationale for `n_null_y3` ("enforced = 0 by joint filter; surfaced for defense-in-depth") is documented in the docstring. I would have liked one more field: `controls: tuple[str, ...]` so `audit_panel(panel)` could echo the control set back. Today it's only available via the JSON summary, which is one extra step for a downstream reader. **Non-blocking; advisory in §5.**

**`write_panel_parquet`:**

* Correctly **NOT** a pure function — it's a documented side-effecting writer. The `register/unregister` flanking the `COPY` is the right hygiene against view-name leak across calls. The `if panel.empty: raise ValueError` short-circuit is **the right discipline for the gate-bearing rows** (1, 3, 4, 7, 8) but bumps into Rows 9 + 10 which are explicitly DEFERRED with empty schema-typed parquets. The DE clearly bypasses this raise-on-empty for those two rows somehow; I did not find a `write_empty_panel_parquet` or equivalent, so presumably the row-9/10 parquets are written by a separate code path or a one-off DuckDB statement at script time. **Non-blocking but documentation gap; advisory in §5.**

### 3.2 Friday-anchor reconciliation pattern — ADVISORY (hoist for Rev-3)

The `+ INTERVAL 4 DAY` Monday→Friday translation is currently:

* **Buried in the `wp_friday` CTE** inside `build_panel`'s SQL string (line 274–280 of `phase5_data_prep.py`).
* **Documented in three places**: docstring §2 ("Friday-anchor invariant"), `queries.md` §1.2 ("Friday-anchor reconciliation (load-bearing)"), `validation.md` §2.1 ("Anchor convention sources"), and three TDD invariants enforce it from three angles (source-side Monday, source-side Friday for the other 3 tables, output Friday-only).

This is **good** for the current 14-row scope. It will become **less good** when Rev-3 ζ-group rows arrive and Analytics Reporter starts wanting to do its own custom panels for quantile or lower-tail regression — they'll need to re-derive the translation.

**Senior-eng recommendation (non-blocking, Rev-3 advisory):** lift the translation to a named module-level constant + a tiny pure helper:

```python
# In a future Rev-3 refactor, expose:
WEEKLY_PANEL_FRIDAY_SHIFT_DAYS: Final[int] = 4
def to_friday_anchor_sql_fragment(table_alias: str) -> str:
    return f"({table_alias}.week_start + INTERVAL {WEEKLY_PANEL_FRIDAY_SHIFT_DAYS} DAY)::DATE"
```

Then `build_panel`'s `wp_friday` CTE becomes a one-line call to the helper, future ζ-group panels share it, and the TDD suite gains one more anchor-related invariant test pinning the constant. This is a **deliberate Rev-3 refactor**, not a Rev-2 fix-up — for Rev-2, the buried CTE form is correct and ships clean. **PASS for Rev-2; hoist on Rev-3.**

### 3.3 Test organization — PASS

The 6-section TDD suite is correctly organized:

| Section | What it tests | Belongs here? |
|---|---|---|
| 1. DuckDB schema (4) | column-name drift defense | YES — these are *consumed by* `phase5_data_prep`; they fail tomorrow if upstream renames occur. |
| 2. Anchor invariant (2) | source-side Monday/Friday | YES — same reason; Friday-anchor reconciliation depends on these contracts. |
| 3. Joint nonzero (5) | byte-exact n=76/65/56/45/47 | YES — gate-bearing TDD anchors. |
| 4. Output contract (4) | columns, x_d>0, no NULL, Friday-only | YES — direct API contract. |
| 5. Audit helper (1) | dataclass shape | YES. |
| 6. Admitted-set guard (1) | typoed methodology raises | YES. |

**Could the schema tests live in `test_econ_schema.py` instead?** Marginally — the schema invariants are not unique to `phase5_data_prep`. But there's a senior-eng case for keeping them here: they document the consumed schema at the *seam* of consumption, so a future maintainer of `phase5_data_prep` reading this test file alone has a complete picture. The DE chose **co-located schema-defense** over centralized `test_econ_schema.py` placement, and I think that's defensible. **PASS.**

### 3.4 Per-row data-prep approach — PASS

**Strategy chosen:** 14 panels via parametric `build_panel(...)` calls + `write_panel_parquet`, presumably driven by a (not-shown-in-this-commit) script-level driver loop. Each row = one tuple of arguments.

**Alternative considered:** a strategy-dispatch dict like:

```python
ROW_RECIPES: dict[str, Callable[[duckdb.DuckDBPyConnection], pd.DataFrame]] = {
    "row_01_primary": lambda c: build_panel(c, x_d_kind=..., y3_methodology=..., controls=...),
    ...
}
```

The DE's actual choice (parametric calls without the dispatch dict) is **correct for 14 rows**, because:

1. The dispatch dict adds indirection without readability gain at this scale.
2. Rows 9 + 10 are DEFERRED — they have NO recipe — and a dict would have to carry sentinel `None` entries.
3. Rows 2, 5, 11, 12, 13 share Row 1's panel; in the dispatch dict they'd be aliases or `lambda c: ROW_RECIPES["row_01_primary"](c)`, a code-smell.

**At Rev-3 ζ-group expansion (4 more rows, possibly more):** the dispatch dict starts winning at ~20 rows because the recipe metadata (n_pre_committed, deferred_flag, notes) wants a structured home. At that point the right refactor is `RowSpec` frozen dataclass + a tuple of them, not a dict. **PASS for Rev-2; defer this refactor to Rev-3.**

### 3.5 Functional-Python compliance — PASS

Spot-checks against `functional-python` skill:

* `PanelAuditReport`: `@dataclass(frozen=True, slots=True)` ✓
* All public functions are free (no class methods). ✓
* Full typing: `Final`, `Sequence`, `date | None`, `tuple[str, ...]`, `frozenset[str]`, `pd.DataFrame` return types. ✓
* No `is`-inheritance, no Python class hierarchy. ✓
* `_validate_controls` and `_validate_y3_methodology` are pure (raise-only side effects on bad input). ✓
* `_build_select_columns_sql` and `_build_where_clause` are pure string-builders. ✓
* `build_panel` is *almost* pure: side effects are limited to (a) the DuckDB read via `conn` (caller-supplied, no implicit global) and (b) the `pd.to_datetime` cast, which is local to the returned DataFrame. ✓
* `write_panel_parquet` is the ONE intentionally side-effecting function and is documented as such. ✓

**PASS.** This is what functional-Python is supposed to look like.

### 3.6 `pyarrow` decision + downstream contract — PASS with one clarity note

**Decision:** DuckDB-native `COPY (...) TO 'path' (FORMAT PARQUET, COMPRESSION ZSTD)` instead of `panel.to_parquet(...)` (which would require pyarrow or fastparquet).

**Senior-eng read:** correct. The contracts venv intentionally minimizes new deps; pyarrow is a 100MB+ wheel, ZSTD is a transparent compression choice, and DuckDB already has the codec linked. **Avoiding a new transitive dep here is the right call.**

**Downstream-consumer-correctness check (the question the prompt asks):**

* `manifest.md` §6 line 146 says: "Read via `duckdb.connect().sql("SELECT * FROM 'panel_row_01_primary.parquet'")` or pandas `pd.read_parquet` (pyarrow-required for the latter)."
* The parenthetical "pyarrow-required for the latter" **does** flag the gotcha. **PASS.**

**One non-blocking clarity advisory:** in §5 below I suggest the manifest should also recommend the DuckDB-native read pattern as the default rather than the secondary, because if Analytics Reporter installs pyarrow they might not realize the DE already chose to avoid it. Currently the manifest reads as "either works, here's a side note about pyarrow," which under-emphasizes that "no pyarrow" was a deliberate dep-management choice.

### 3.7 Outlier-flagging-without-removal — PASS (correct discipline)

`validation.md` §4 makes the flag/remove split explicit:

* §4 header: "Outlier flagging (NOT removed)"
* §4 body: "Per the Data Engineer agent contract, **outliers are flagged and surfaced; they are NOT removed**. The Analytics Reporter at Phase 5b is the deciding party."
* §4.1 body: "None of these outliers should be removed by the Data Engineer; they reflect real macro-financial variation and removing them would bias the regression sample."
* §9 header: "Anti-fishing posture" with the explicit "no silent threshold tuning / no mid-stream X_d swap / no missing-data imputation" trifecta.

This is the correct discipline per `feedback_pathological_halt_anti_fishing_checkpoint`. **PASS.**

### 3.8 Provenance integrity — PASS

`git show 2eed63994 --stat` confirms: 21 files changed, **1775 insertions(+), 0 deletions**. The DE's "ADDS files only" claim is byte-verifiable:

* 1 NEW module (`scripts/phase5_data_prep.py`, 355 lines)
* 1 NEW test file (`scripts/tests/inequality/test_phase5_data_prep.py`, 430 lines)
* 19 NEW artifacts in `contracts/.scratch/2026-04-25-task110-rev2-data/` (4 docs + 14 parquets + 1 JSON)
* No existing module touched. No `_KNOWN_Y3_METHODOLOGY_TAGS` modification. No existing notebook touched.

**PASS.** Pure additive commit; reviewable as a self-contained unit.

### 3.9 Pre-existing failures — PASS (confirmed disclosure-ready)

Full `pytest scripts/tests/` (293s wall):

```
1043 passed, 7 skipped, 11 failed
```

Failures break down as:

* **2 in `test_cleaning_remittance.py`** — `test_load_cleaned_remittance_panel_raises_file_not_found_without_fixture`, `test_load_cleaned_remittance_panel_calls_rev4_loader_first`. These are the documented pre-existing remittance failures (predating commit `28d76cbb0` which introduced the cleaning extension).
* **9 in `test_y3_br_bcb_wire.py`** — these FLAKE in full-suite runs but PASS when run alone (`pytest test_y3_br_bcb_wire.py` → 16/16 passed in 9s). Likely BCB SGS rate-limiting or session-scoped-fixture interaction during full runs. **Not a regression introduced by this commit; not the DE's responsibility.**

**PASS.** The 2 remittance failures are correctly out-of-scope; the 9 BR-BCB-wire intermittents merit a separate HALT-BCB-flakiness investigation but are outside Phase 5a's explicit scope.

### 3.10 Downstream readiness for Analytics Reporter — PASS with one note

What Analytics Reporter (Phase 5b) needs for §4 estimation + §7 specification tests T1–T7:

| Need | Provided? |
|---|---|
| Panel artifacts | YES — 14 parquets (12 buildable + 2 deferred-empty) |
| Per-row metadata (X_d kind, Y₃ tag, controls, cutoff) | YES — `_audit_summary.json` |
| Schema-stable column names matching spec §4.1 | YES — byte-exact `y3_value`, `x_d`, `vix_avg`, … |
| Per-country diff columns for Row 14 alt-weights | YES — `copm_diff`, `brl_diff`, `kes_diff`, `eur_diff` carried on every panel |
| Friday-anchor invariant guarantee | YES — three TDD tests + one CTE |
| Joint-nonzero filter rationale | YES — `validation.md` §3 |
| Outlier flag-not-remove split | YES — `validation.md` §4 |
| Spec-pre-commitment audit (76/65/56/45/47) | YES — manifest §3 + validation §1 |
| Read pattern for parquets (DuckDB-native vs pandas) | YES — `manifest.md` §6 (with pyarrow caveat) |
| Reference to spec for §4 estimator + §7 tests | YES — every doc cites it |

**One gap, non-blocking:** Row 5 (lag), Row 11 (Student-t), Row 12 (HAC(12)), Row 13 (first-differenced), Row 14 (alt-weights) all carry "transform at fit time" semantics. The manifest documents these but **does not include a code-level fixture or notebook stub** for the Analytics Reporter to apply each transform consistently. Each transform is a 1–3-line pandas operation, but inconsistent application could silently shift n=76→75 in Rows 5 and 13 without uniform discipline. **Recommendation:** Phase 5b should write its own thin `phase5_fit_helpers.py` for these transforms; the DE's contract correctly stops at the panel.

**PASS.** Analytics Reporter has everything needed to start Phase 5b.

---

## 4. Inline code spot-checks

I confirmed by reading the module:

* **No global state.** `conn` is always passed in. `register/unregister` is balanced.
* **Parametric SQL via `?` placeholders, not string interpolation.** Line 256 builds `params: list[object] = [x_d_kind, y3_methodology]` and the LOCF cutoff appends to that list. **No SQL injection vector.** Even though the inputs are spec-literals from a frozen admitted set, the parametric pattern is correct hygiene.
* **`fetchdf()` then post-cast `week_start` to `datetime.date`** — line 294. Necessary because DuckDB returns numpy `datetime64`; downstream `.isoweekday()` is a `datetime.date` API. The `pd.to_datetime(df["week_start"]).dt.date` round-trip is correct.
* **Error messages enumerate the admitted set** on `_validate_y3_methodology` failure — correct UX for the typoed-tag class of bug. **Defense-in-depth re-test of the upstream guard**, useful at the seam.

---

## 5. Non-blocking advisories

### Advisory 1: hoist Friday-anchor translation to a named helper at Rev-3

**Why:** Rev-3 ζ-group panels (quantile β̂(τ), GARCH-X variance, lower-tail conditional regression) will want the same Monday→Friday shift. Burying it in `build_panel`'s CTE means future authors re-derive it, with non-zero risk of regressing the load-bearing invariant.

**Non-blocking** — Rev-2 ships clean. Address at Rev-3 entry.

### Advisory 2: document the empty-parquet write path for Rows 9 + 10

**Why:** `write_panel_parquet` raises `ValueError` on empty DataFrames. The deferred Rows 9 + 10 ARE empty (387-byte schema-only parquets). The driver script that produces those two artifacts must therefore either (a) bypass `write_panel_parquet`, or (b) DE has a separate `write_empty_deferred_panel(...)` that I didn't see in this commit.

**Recommendation:** the manifest or the module docstring should explicitly document the Row 9 + Row 10 write path so a future maintainer who sees an empty parquet doesn't trip the `audit_panel`/`write_panel_parquet` raise-on-empty. Five sentences in `manifest.md` §1.2 footnote, or a small `# DEFERRED rows 9 + 10 are written via …` comment in the module docstring, would close it.

**Non-blocking** — current artifacts work; Phase 5b just needs to know to skip Rows 9 + 10 with a `"deferred"` tag (which manifest §2.2 already says).

### Advisory 3: emphasize DuckDB-native read in the Phase-5b consumer guide

**Why:** `manifest.md` §6 currently presents `pd.read_parquet` and DuckDB-native as equivalent options with a side-note about pyarrow. If the DE intentionally avoided pyarrow as a dep-management choice, the recommended-default in the consumer guide should match:

> Recommended: `duckdb.sql("SELECT * FROM 'panel_row_01_primary.parquet'").df()` — matches the writer (no pyarrow dep). Alternative: `pd.read_parquet(...)` requires pyarrow; install only if Analytics Reporter prefers pandas-first ergonomics.

**Non-blocking** — both methods work; this is a clarity nudge.

---

## 6. Verdict

**PASS-with-non-blocking-advisories.**

The Phase 5a deliverable is a clean, well-typed, single-responsibility data-prep module that defends its scope correctly (does not creep into estimator-stage concerns), implements the load-bearing Friday-anchor invariant defensively across SQL + tests + docs, reproduces all five spec pre-commitments byte-exact, and hands Phase 5b a consumable artifact set with explicit downstream-read instructions.

The three advisories are forward-looking (Rev-3 hoist of the anchor helper, empty-parquet write-path documentation, DuckDB-read default emphasis) and do **not** block Phase 5b handoff. Analytics Reporter can start Phase 5b on these artifacts as-is.

I would unblock and dispatch Phase 5b.

---

## 7. Files referenced

* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/phase5_data_prep.py`
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/tests/inequality/test_phase5_data_prep.py`
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/manifest.md`
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/data_dictionary.md`
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/validation.md`
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/queries.md`
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/_audit_summary.json`
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`
