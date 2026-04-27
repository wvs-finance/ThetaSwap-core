# Senior-Developer Review — Task 11.N.2d.1-reframe (recovery commit `9a1f00068`)

**Date:** 2026-04-25
**Branch:** `phase0-vb-mvp`
**Reviewer:** Senior Developer (third of three: Code Reviewer + Reality Checker + Senior Developer per `feedback_implementation_review_agents`)
**Commit:** `9a1f00068` — recovery commit (orchestrator-authored after DE was credit-capped at ~71 tool uses)
**Sibling commit reviewed:** `c5cc9b66b` (Task 11.N.2d-rev primary panel) — converged at `d730c39ac`
**Predecessor SD reviews carried forward:** `2026-04-25-y3-rev532-rereview-senior-developer.md` (SD-RR-A1, SD-RR-A2 forward to Task 11.O); `2026-04-25-co-dane-wire-review-senior-developer.md` (A1 dispatch refactor at 3rd source upgrade; A2 `ingest_y3_weekly` plumbing — already actioned in 11.N.2d-rev)
**Reviewer lens:** "Is this code I would want to maintain in 6 months? Does the API scale? Did the recovery preserve integrity?"

---

## Verdict — **PASS-with-non-blocking-advisories**

The recovery commit is structurally clean. The DE's intended deliverable landed intact: an additive, kwarg-only API extension to `ingest_y3_weekly`; a single new admitted-set literal; one new test file with the right shape; a 288-line comparison memo. The orchestrator's recovery integrity-check is verifiable via `git show --stat` (4 files, 731+/1−). No drift, no scope leakage. The two carried-forward advisories (SD-RR-A1 default flip; SD-RR-A2 RC A3 LOCF-tail-excluded sensitivity) are **unchanged in disposition** — neither is blocking and neither is contradicted by this commit.

Two new non-blocking advisories surfaced in this review (SD-A3 type-annotation fidelity; SD-A4 admitted-set scaling debt). Both forward to Task 11.O dispatch; neither is blocking.

---

## SD-lens-by-lens findings

### 1. `source_mode` API design quality — PASS-with-advisory (SD-A3)

**Literal type, kwarg-only, sensible defaults?** Two of three: yes-ish. The parameter is correctly keyword-only (declared after the existing `*` in the signature) and the default `"primary"` preserves backward-compat byte-exact for all 30+ existing call sites. The third dimension — Literal type — is **stated in the commit message and memo as `Literal['primary','imf_only_sensitivity']`** but the actual signature at `econ_pipeline.py:2835` declares `source_mode: str = "primary"`. The constraint is enforced at runtime via the `ValueError` guard at line 2883 (admitted set `("primary", "imf_only_sensitivity")` named explicitly in the error message — same discipline as the `_KNOWN_Y3_METHODOLOGY_TAGS` validation). This is a **type-annotation fidelity gap, not a behavior gap** — the same constraint is enforced, just at runtime rather than at type-check time.

**Does the API surface scale to a 3rd `source_mode`?** Acceptably. The current shape (`if source_mode not in (...)` + `wc_conn = conn if source_mode == "primary" else None`) is a 2-mode binary dispatch that works because IMF-IFS is the natural fallback for both CO and BR. A 3rd mode (e.g., `"eurostat_only_sensitivity"` if δ-EU ever lands) would require the dispatch to grow per-country forwarding logic, since "Eurostat only" is not a uniform-conn-routing answer (CO/BR have no Eurostat path). At that point the right shape becomes a per-country mode resolver:

```python
# Hypothetical 3rd-mode shape (DO NOT implement now):
_SOURCE_MODE_DISPATCH: Final[dict[str, dict[str, str]]] = frozenset(...)  # mode → country → source
```

The current binary shape will need refactoring at the 3rd-mode threshold, which is the same threshold flagged in the CO-dane-wire SD-A1 advisory (3rd source upgrade triggers fold to dispatch dict). The two advisories converge: at the 3rd mode/source, fold both routing layers into a structured dispatch table.

> **SD-A3 (non-blocking, forward to next-mode dispatch):** When the type annotation drifts into runtime-only enforcement, downstream readers using `mypy --strict` will not catch invalid mode literals at type-check time. Two paths: (a) tighten the annotation to `Literal["primary", "imf_only_sensitivity"]` (zero behavior change; pure metadata uplift), (b) leave it as `str` and document the runtime-only enforcement contract in the docstring. **Recommendation:** path (a) — it costs one line, matches the commit-message claim verbatim, and brings call-site IDE autocomplete + mypy coverage back in line with the runtime guard. Not blocking; carried forward to the dispatch that adds the 3rd mode (where the cost of NOT having Literal coverage rises).

PASS on this dimension because the runtime guard fully closes the silent-bad-input footgun. The Literal type drift is a paperwork issue, not a code-correctness issue.

---

### 2. Admitted-set lifecycle scaling — PASS-with-advisory (SD-A4)

The admitted set has now grown to 4 entries:
1. `y3_v1` — Rev-5.3.1 base (un-suffixed legacy default)
2. `y3_v1_3country_ke_unavailable` — Rev-5.3.1 with KE-skip suffix (59 rows in canonical DB)
3. `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` — Rev-5.3.2 primary (116 rows)
4. `y3_v2_imf_only_sensitivity_3country_ke_unavailable` — Rev-5.3.2 sensitivity (116 rows; this commit)

**Is this scaling well?** The admitted-set + composite-PK + per-tag block-comment provenance discipline is the right shape for the current size; the 14-line block comment added in this commit (matching the existing convention from commit `2a0377057`) keeps each tag's revision attribution + row-count fingerprint discoverable. A future maintainer reading `econ_query_api.py:56-90` sees a chronologically-ordered changelog of methodology evolution.

**Where it starts to strain:** at the next-tag landing. Each new tag is an O(1) addition to the frozenset and an O(N_lines) addition to the block comment. The block comment is now ~36 lines and growing linearly with revisions; by tag #6 or #7 it will exceed a screen-height. At that point the natural fold is:

```python
# Hypothetical at tag #6+:
_Y3_METHODOLOGY_PROVENANCE: Final[dict[str, str]] = MappingProxyType({
    "y3_v1": "Rev-5.3.1 base; 59 rows; Sep-2024..Oct-2025; KE skipped per design §10.1",
    "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable":
        "Rev-5.3.2 primary; 116 rows; Jan-2024..Mar-2026; CO=DANE, BR=BCB, EU=Eurostat",
    ...
})
_KNOWN_Y3_METHODOLOGY_TAGS: Final[frozenset[str]] = frozenset(_Y3_METHODOLOGY_PROVENANCE)
```

This shape encodes the provenance as data (queryable, machine-traversable for sensitivity-cross-validation tooling) rather than as block-comment prose. The current shape is fine for 4 entries; the fold becomes strictly better at ~6+.

> **SD-A4 (non-blocking, forward to Task 11.O dispatch):** The admitted-set + block-comment shape will fold into a structured provenance dict at the ~6-tag threshold. Currently 4; Task 11.O Rev-2 spec authoring may add a 5th tag if the spec pre-registers a separate sensitivity (e.g., RC A3's LOCF-tail-excluded sensitivity per SD-RR-A2 — that is a separate methodology tag). Track this against the threshold; do not refactor preemptively.

PASS on this dimension. Not accumulating debt yet, but the trajectory is visible — flag for Task 11.O+.

---

### 3. DE's IMF-IFS path preservation — PASS

`git show 9a1f00068 --stat` confirms `y3_data_fetchers.py` is **NOT in the commit**. The IMF-IFS dispatch path body is byte-exact preserved from its prior state. Verified by inspection:

- `y3_data_fetchers.py:293-299` — the dispatch in `fetch_country_wc_cpi_components`:
  - `EU` → `_fetch_eu_hicp_split` (unconditional first branch — sensitivity preserves this byte-exact, since EU has no IMF-IFS series at month-CPI cadence on free-tier APIs)
  - `CO` + `conn is not None` → `_fetch_dane_headline_broadcast`
  - `BR` + `conn is not None` → `_fetch_bcb_headline_broadcast`
  - **fallback** → `_fetch_imf_ifs_headline_broadcast(country, start, end)` — this is the path the `imf_only_sensitivity` mode lands on for CO/BR (and KE, which is downstream-skipped per design §10 row 1)

The sensitivity dispatch is the **dispatch fallback** of an existing per-country branch. No new code path through the fetcher; no value-mutating logic. The DE's claim in the comparison memo §1.1 ("the IMF-IFS path is preserved byte-exact in the fetcher (no dispatch logic duplicated at the pipeline layer)") is verifiable by the absence of `y3_data_fetchers.py` from the commit's `git show --stat`.

This is the architecturally correct shape: the new `source_mode` parameter is a **caller-side dispatch** at `econ_pipeline.py:2944` (`wc_conn = conn if source_mode == "primary" else None`), not a fetcher-side branch. The sensitivity is constructed by *routing* the existing dispatch table differently, not by *adding* a new dispatch row. This minimizes blast radius and preserves the principle that the brain (fetcher logic) is sibling-mode-agnostic.

PASS — the implementation honors the design contract from CO-dane-wire SD review A1: "the conn-based design is good-enough-not-perfect" and the new mode parameter scales orthogonally rather than mutating the existing per-country dispatch.

---

### 4. Test fixture organization — PASS

`test_y3_imf_only_sensitivity.py` (NEW, 7 tests). Verified by `grep -c "^def test_"`.

**Naming consistency.** Existing siblings: `test_y3.py`, `test_y3_co_dane_wire.py`, `test_y3_methodology_admitted_set.py`. The new file's name `test_y3_imf_only_sensitivity.py` is consistent with the `test_y3_<mode>` pattern that emerged with `test_y3_co_dane_wire.py` (CO-dane-wire SD review noted the awkward 3-segment suffix as non-blocking; the same pattern is now reinforced — at this point it IS the project convention for Y₃-related extension tests).

**Coverage axes.** Verified the 7 tests partition into:
- **Section 1 (signature contract):** `test_ingest_y3_weekly_signature_has_source_mode_kwarg` (kwarg presence + default + KEYWORD_ONLY kind) and `test_ingest_y3_weekly_rejects_unknown_source_mode` (ValueError + message-content invariants). These are the right signature-locking pair — every future maintainer who refactors `ingest_y3_weekly` must keep both green.
- **Section 2 (regression guard for primary mode):** `test_primary_mode_forwards_conn_to_wc_cpi_fetcher` — captures `conn_id` to assert the **same connection object** is forwarded, not just "some non-None conn". This is stricter than just `conn_is_none == False`; it catches the silent footgun where a refactor passes a wrapper conn instead of the live one.
- **Section 3 (load-bearing dispatch for sensitivity mode):** `test_imf_only_sensitivity_passes_conn_none_to_wc_cpi_fetcher` — symmetric to Section 2 but asserts `conn_is_none == True`. The two together pin down the binary dispatch in both directions.
- **Section 4 (admitted-set + composite PK):** `test_known_y3_methodology_tags_contains_sensitivity_literal` (admitted-set extension), `test_load_onchain_y3_weekly_accepts_sensitivity_literal_against_canonical_db` (round-trip from canonical DB; per `feedback_real_data_over_mocks`), `test_primary_panel_rows_unchanged_post_sensitivity_ingest` (composite-PK byte-exact preservation guard — asserts `len(primary) == 116`).

**Right axes covered:** dispatch (Sections 2+3), admitted-set extension (Section 4 first test), gate-CLEAR-on-primary preserved (Section 4 third test). What's **not** in this file (correctly so):
- The actual gate-FAIL-on-sensitivity assertion (56 weeks < 75) is in the comparison memo §3.3, not in a unit test. **This is the right call** — it's an analytical finding tied to a specific data state, not an invariant. Re-running the ingest with different windows would change the count; pinning a test against `count == 56` would be brittle. The `len(rows) > 0` assertion in Section 4 second test is the right shape for a unit-test-level invariant.
- `source_mode` dispatch on the 3rd-mode-not-yet-existing case — N/A (binary dispatch).

**Pattern fragility.** The Section 2/3 tests monkeypatch `y3_data_fetchers.fetch_country_wc_cpi_components` and `y3_data_fetchers.fetch_country_equity` for short-circuit capture. The pattern raises `Y3FetchError` after capture to short-circuit the per-country loop without persisting test rows. The CO-dane-wire SD review flagged a similar monkeypatch pattern as "fragile if the function is renamed but acceptable for high-value preservation assertion" — the same calculus holds here. Section 1's signature-locking test is the renames-guard; the dispatch tests inherit that guard transitively.

PASS — 7 tests on 4 axes, all the right axes, monkeypatch fragility bounded by signature-lock test.

---

### 5. Recovery-commit integrity — PASS

`git show 9a1f00068 --stat`:
```
contracts/.scratch/...sensitivity-comparison.md  | 288 +++++++++++++++
contracts/scripts/econ_pipeline.py               |  41 ++-
contracts/scripts/econ_query_api.py              |  14 +
contracts/scripts/tests/inequality/test_y3_imf_only_sensitivity.py | 389 +++++++++++++++++++++
4 files changed, 731 insertions(+), 1 deletion(-)
```

Cross-referenced against the comparison memo §9 "Files modified":
- `econ_pipeline.py` (sig + 3-line dispatch tweak + ValueError guard + docstring) ✓ matches the +41/-1 count
- `econ_query_api.py` (1 set element + 14-line block comment) ✓ matches the +14 count
- `test_y3_imf_only_sensitivity.py` NEW ✓ matches the +389 count
- The comparison memo itself ✓ matches the +288 count

**Untouched files in scope (verified `git show --stat` does NOT list them):**
- `y3_data_fetchers.py` — IMF-IFS path body byte-exact preserved (Lens 3 above)
- `y3_compute.py` — recently-converged; no logic change required
- `econ_schema.py` — no schema migration; existing `onchain_y3_weekly` schema admits the new tag via composite PK
- `carbon_calibration.py` — out of scope
- The plan markdown — not modified (the in-place superseded-banner edit is part of Task 11.O-scope-update per plan §11.O-scope-update bullet, not this task)
- DuckDB binary file — additive INSERT-only (no schema mutation; verified via composite-PK Section 4 third test asserting primary 116 rows preserved)

**No collateral drift.** The recovery commit is byte-equal to what a credit-uncapped DE would have committed. The orchestrator's role here was custodial: verify integrity, run tests, commit. The commit message is honest about the recovery context (lines 5-12 of the message body explicitly call out the credit-cap interruption + custodial role + which tests were run pre-commit).

**One observation worth flagging:** the commit message paragraph at lines 47-51 contains a "Provenance statement (honest, no false pre-staging claim)" — this is the orchestrator pre-empting the M1 trap from the CO-dane-wire SD review (where the verification memo falsely claimed pre-staged symbols). The provenance is verifiable by `git show 9a1f00068~1:contracts/scripts/econ_pipeline.py | grep -c "source_mode"` → `0` (the parameter did not exist before this commit). Verified by inspection: only one `source_mode` mention exists pre-commit, and it's not in any signature. Good — the M1 anti-pattern from CO-dane-wire is correctly avoided.

PASS — the recovery commit is faithful to the DE's intended deliverable, scope is tight, no extra files leaked in, provenance is honest.

---

### 6. Forward-advisories disposition check — UNCHANGED

**SD-RR-A1 (flip default `source_methodology` to v2 literal):** still forwarded to Task 11.O dispatch. This commit does **not** affect the disposition — it neither flips the default nor exacerbates the residual hole. The new `source_mode` parameter is a separate axis of dispatch (mode != methodology-tag), so the SD-RR-A1 hole remains the same: a production caller passing `source_methodology="y3_v1"` against the canonical DB still gets an empty tuple under the unchanged default. The `source_mode` default of `"primary"` is the **right** default for that axis (most callers want the upgraded sources); SD-RR-A1's recommendation to flip the **methodology-tag** default does not extend to flipping the **mode** default. Two independent decisions.

**SD-RR-A2 (surface RC A3 LOCF-tail-excluded sensitivity in Task 11.O Rev-2 spec):** still forwarded to Task 11.O dispatch. Unchanged. The current commit added a **different** sensitivity (single-source-fallback IMF-IFS-only), not the LOCF-tail-excluded sensitivity. Both sensitivities are now pre-registered for Task 11.O consumption: the IMF-IFS-only at 56 weeks (FAIL) lands in this commit's panel; the LOCF-tail-excluded at 65 weeks (FAIL — per RC re-review probe-5) is separately pre-registered in the §A.4-style comparison framework. Task 11.O Rev-2 spec authoring should reference both.

**CO-dane-wire SD-A1 (dispatch dict at 3rd source upgrade):** still forwarded. This commit does not add a 3rd source — it adds a 2nd **mode** that re-routes existing sources. The 3rd-source threshold has not been crossed.

**CO-dane-wire SD-A2 (`ingest_y3_weekly` plumbing CO conn):** **already actioned** in Task 11.N.2d-rev (commit `c5cc9b66b`); preserved here (the `conn` forwarding is exactly what `source_mode='primary'` re-uses). This advisory is **closed** by the chain `c5cc9b66b → 2a0377057 → d730c39ac → 9a1f00068`.

**No advisory disposition shifts. Three open + one closed.**

---

### 7. Functional-Python compliance — PASS

- `source_mode: str = "primary"` — see SD-A3 advisory above for the Literal-tightening forward. The default-immutable string is correct.
- `if source_mode not in ("primary", "imf_only_sensitivity")` — pure free expression; tuple of immutable string literals.
- `wc_conn = conn if source_mode == "primary" else None` — pure free expression; no class, no inheritance, no mutation.
- The 14 lines added to `econ_query_api.py` are a frozenset element addition + block comment. The frozenset is `Final[frozenset[str]]` — immutable container, type-pinned, project-canonical shape.
- The new test file uses `Final[Path]` and `Final[str]` for module-level constants; in-test `pytest.MonkeyPatch` for capturing dispatch (acceptable per the same reasoning as CO-dane-wire SD review §3 Step-C #2).

No `class` introduction. No inheritance. No `is`-relationship hierarchies. No sneak-mutations. PASS.

---

## Summary table

| Lens                                          | Verdict   | Notes                                                                                                                  |
|-----------------------------------------------|-----------|------------------------------------------------------------------------------------------------------------------------|
| 1. `source_mode` API design                   | PASS-w/A  | Kwarg-only + default-primary correct; SD-A3 = `str` vs `Literal` annotation drift (forward to next-mode dispatch)       |
| 2. Admitted-set lifecycle                     | PASS-w/A  | 4 entries; SD-A4 = fold to provenance dict at ~6-tag threshold (forward to Task 11.O if 5th tag lands)                 |
| 3. IMF-IFS path preservation                  | PASS      | `y3_data_fetchers.py` not in commit; sensitivity routes through existing dispatch fallback byte-exact                   |
| 4. Test fixture organization                  | PASS      | 7 tests on 4 axes (sig/rejection/primary-dispatch/sensitivity-dispatch/admitted-set/round-trip/PK-preservation)         |
| 5. Recovery-commit integrity                  | PASS      | 4 files / 731+ / 1−; no collateral drift; M1 anti-pattern explicitly avoided in commit message                          |
| 6. Forward advisories                         | UNCHANGED | SD-RR-A1, SD-RR-A2, CO-dane-wire SD-A1 all open; CO-dane-wire SD-A2 closed by 11.N.2d-rev chain                        |
| 7. Functional-Python                          | PASS      | Free pure functions, frozen Final containers, no class/inheritance/mutation                                             |

---

## Final verdict

**PASS-with-non-blocking-advisories.**

The recovery commit ships a tight, scope-respecting, TDD-disciplined extension. The DE's intended deliverable is intact; the orchestrator's custodial role is verifiable; the IMF-IFS path body is byte-exact preserved (the sensitivity is constructed by *routing* the existing dispatch fallback, not by adding new code paths). The new `source_mode` parameter is an additive, kwarg-only extension that preserves backward-compat for all existing callers byte-exact.

The 7-test suite covers the right axes — dispatch (both directions), admitted-set extension, composite-PK preservation. The Section 2/3 monkeypatch pattern is fragile under fetcher renames but bounded by Section 1's signature-lock test (transitive guard).

Two new non-blocking advisories surface (SD-A3 type-annotation tightening; SD-A4 admitted-set provenance-dict fold at ~6-tag threshold). Both forward to Task 11.O dispatch; neither is blocking. Three carried-forward advisories (SD-RR-A1, SD-RR-A2, CO-dane-wire SD-A1) remain open at unchanged disposition; one (CO-dane-wire SD-A2) is now closed by the 11.N.2d-rev chain.

This is code I would be willing to maintain in 6 months. The recovery integrity is faithful — no extra files slipped in, the commit message provenance statement is honest, and the comparison memo's CO/BR cutoff projections (2025-07-01 binding country) are confirmed by the actual ingest output.

Task 11.N.2d.1-reframe is **CONVERGED** at the implementation layer pending CR + RC verdicts. Downstream Task 11.O-scope-update is unblocked (was already unblocked by Task 11.N.2d-rev's gate clearance at 76 ≥ 75; the sensitivity FAIL at 56 < 75 is the diagnostic finding that locks the gate against silent source-upgrade reversal — exactly the demonstrative outcome the task was designed to produce).

---

## Reviewer-ack checkbox (per memo §5 RC advisory A6)

- [x] **Senior Developer ack** — methodology literal `y3_v2_imf_only_sensitivity_3country_ke_unavailable` ack'd. Decomposition matches the convention established by `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`: schema-generation tag (`y3_v2`) + sensitivity-name (`imf_only_sensitivity`) + runtime KE-skip suffix (`_3country_ke_unavailable`). Admitted-set frozenset extension at `econ_query_api.py:60-78` is correctly placed (chronological order; 14-line block comment matches the existing per-tag provenance discipline).

---

## Verification trail

1. `git show 9a1f00068 --stat` — 4 files / 731+ / 1−; sensitivity files only; no production code outside `econ_pipeline.py` + `econ_query_api.py`.
2. `git show 9a1f00068 --format=fuller` — orchestrator-authored recovery commit; commit message body explicitly discloses credit-cap recovery context + provenance statement.
3. `grep -c "^def test_" contracts/scripts/tests/inequality/test_y3_imf_only_sensitivity.py` → `7` (matches memo §2 TDD record + commit message "+7 new sensitivity tests").
4. `grep -n "source_mode" contracts/scripts/econ_pipeline.py` → 7 references; all in the new signature + docstring + ValueError guard + dispatch tweak. Type annotation is `str` not `Literal` (SD-A3 evidence).
5. Inspection of `y3_data_fetchers.py:283-299` — dispatch table verified: EU unconditional, CO+conn → DANE, BR+conn → BCB, fallback → IMF-IFS. Sensitivity mode routes CO/BR through the fallback (Lens 3 evidence).
6. `git show 9a1f00068 --stat` confirms `y3_data_fetchers.py` NOT in commit (Lens 3 byte-exact preservation evidence).
7. Inspection of `_KNOWN_Y3_METHODOLOGY_TAGS` at `econ_query_api.py` — 4 entries, frozenset, `Final` typed, chronologically ordered with per-tag block-comment provenance (Lens 2 evidence).
8. Comparison memo §3.3 numerics cross-referenced: PRIMARY 76 weeks (CLEARED), SENSITIVITY 56 weeks (FAILS), Δ = 20 weeks concentrated post-2025-10-24 (LOCF-tail-extended IMF-IFS cutoff). Mechanism: binding country = min(CO=2025-07-01, BR=2025-07-01, EU=2025-12-01) + 120-day LOCF tail = 2025-10-29 → last Friday 2025-10-24 (matches observed). Arithmetic verified.

— Senior Developer, 2026-04-25
