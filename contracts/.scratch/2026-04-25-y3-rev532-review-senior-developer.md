# Senior Developer review — Task 11.N.2d-rev (Rev-5.3.2)

**Date:** 2026-04-25
**Reviewer:** Senior Developer subagent (third reviewer per `feedback_implementation_review_agents`)
**Commit under review:** `c5cc9b66b` on branch `phase0-vb-mvp`
**Predecessors in chain:** `f7b03caac` (CO DANE wire) → `4ecbf2813` (BR BCB fetcher) → `c5cc9b66b` (this commit, conn-forwarding)
**Plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` §Task 11.N.2d-rev (line 1916)
**Memo under review:** `contracts/.scratch/2026-04-25-y3-rev532-ingest-result.md`

---

## Verdict

**NEEDS-WORK** — one acceptance-criterion gap (a), one honesty-narrative misattribution (b), and one downstream-readiness blocker for Task 11.N.2d.1-reframe (c). The core conn-forwarding patch is technically correct and the gate-clearing arithmetic checks out; what fails my lens is *contractual* rather than *mechanical*.

The three items are not "the patch is wrong" — they are "the verification memo + acceptance-criterion ledger has a real omission, an honestly-misattributed causation, and a known-blocker for the next task that must be acknowledged before downstream dispatches fire." Items (a) and (c) are the same root cause (admitted-set / methodology-tag-filter contract) viewed from two angles.

---

## §1. Patch quality (line 2909, NOT 2905 as DE memo cites)

**Lens:** is the one-line conn-forwarding patch surgically correct, and is nothing else changed?

The DE's verification memo cites the call site at `econ_pipeline.py:2905`. I read the actual file at HEAD `c5cc9b66b`: the call site is at **line 2909**, with a 4-line preamble comment at lines 2904–2907. This is a **minor documentation imprecision** in the memo, not a code defect. The diff itself shows the canonical kwarg form:

```python
# Rev-5.3.2 Task 11.N.2d-rev: forward ``conn`` so the kwarg-aware
# dispatch in ``fetch_country_wc_cpi_components`` activates the
# CO → DANE and BR → BCB source upgrades. Without this kwarg the
# fetcher falls back to the IMF-IFS path for all countries.
try:
    comp = fetch_country_wc_cpi_components(country, start, end, conn=conn)
```

This is correct. The receiver `fetch_country_wc_cpi_components` (per `y3_data_fetchers.py:244-249`) declares `conn` as keyword-only after `*` — positional would have been a TypeError. The CO and BR branches both gate on `conn is not None` (lines 295 and 297), so without forwarding, the upgrades silently no-op and IMF-IFS fallback fires — exactly as the DE narrates. The kwarg form is contractually mandatory and is what landed.

**Patch quality: PASS.** Memo line-number imprecision (2905 vs 2909) is a non-blocking advisory — the DE memo should be amended in a follow-up to cite the actual call-site line. Not a re-commit ask.

---

## §2. Test fixture design

**Lens:** are the two new tests targeted and specific, or trivial "import succeeds" boilerplate?

`scripts/tests/inequality/test_y3_rev532_conn_forward.py` introduces two tests:

1. **`test_ingest_y3_weekly_forwards_conn_to_wc_cpi_fetcher`** — monkeypatches `fetch_country_wc_cpi_components` with a capture sentinel that raises `Y3FetchError` after recording the kwargs. The assertion is sharp: `not cap["conn_is_none"]` AND `cap["conn_id"] == id(test_conn)`. This locks in (i) the fact of forwarding AND (ii) object-identity preservation (the conn forwarded is the same one the caller passed). Pre-patch: `conn_is_none=True` ⇒ red. Post-patch: green. This is a real failing-first test.

2. **`test_ingest_y3_weekly_call_site_uses_kwarg_form`** — `inspect.getsource(ingest_y3_weekly)` + `assert "conn=conn" in src`. This is a static-source guard against accidental positional-form regressions. It's narrow but has a real purpose: the receiver's signature is keyword-only, so a positional revert would be a TypeError at runtime — but only after the loop launches, which costs an HTTP round-trip. Cheap unit-time guard.

The two tests are NOT redundant: (1) verifies runtime behavior; (2) verifies static call-site form. Both are targeted to the load-bearing contract.

**The tests would NOT have passed against a fake "import succeeds" patch.** They specifically lock down the country-routing dispatch.

I checked one subtle scaffolding choice: the test mocks at `y3_data_fetchers.fetch_country_wc_cpi_components` (the source module), not at `econ_pipeline.fetch_country_wc_cpi_components`. This is correct because `ingest_y3_weekly` imports the name from `y3_data_fetchers` at module top — but if the import pattern in `econ_pipeline.py` is `from .y3_data_fetchers import fetch_country_wc_cpi_components` (i.e., binds a local module-level name), the monkeypatch on the source module would NOT take effect, and the test would silently false-pass. Let me note this as an **advisory** to verify with a quick `grep import fetch_country_wc_cpi_components` inside `econ_pipeline.py`. If the import is `from scripts import y3_data_fetchers; ... y3_data_fetchers.fetch_country_wc_cpi_components(...)`, the monkeypatch is correct; if it's `from scripts.y3_data_fetchers import fetch_country_wc_cpi_components` and the function is called as bare `fetch_country_wc_cpi_components(...)`, the monkeypatch misses. The DE narrates "red→green verified" so empirically the test fired pre-patch — but that empirical observation is the load-bearing assurance, not the scaffolding logic.

**Test fixture design: PASS-with-non-blocking-advisory.** Targeted, not trivial. Advisory: a comment in the test file explaining *why* the monkeypatch is at the source module (and not the consuming module) would harden future maintenance.

---

## §3. Methodology literal pin — maintenance-friendliness

**Lens:** is `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` self-documenting for a 6-month-future maintainer?

The literal decomposes (per memo §6) as:

| Segment | Meaning |
|---|---|
| `y3_v2` | Schema generation (distinguishes from `y3_v1`) |
| `co_dane` | CO source = DANE table |
| `br_bcb` | BR source = BCB SGS series 433 |
| `eu_eurostat` | EU source = Eurostat HICP via DBnomics |
| `ke_skip` | KE intentionally skipped per design §10 row 1 |
| `_3country_ke_unavailable` | Runtime-appended fallback flag |

This is **self-documenting for someone who has read the design doc § 10**, but **opaque without that context**. A 6-month-future maintainer reading a DuckDB query result and seeing this 64-character string in a `source_methodology` column will need to either:
- have the design doc memorized, OR
- find a code-level comment or a docstring or a memo mapping these tag literals to source-mix descriptions.

The DE memo §6 IS that mapping document — and it's checked into `.scratch/`. That's adequate but fragile: `.scratch/` is per-task ephemeral by convention; a maintainer 6 months out is unlikely to grep `.scratch/` first.

**Recommendation (advisory, not blocker):** the next pass on `econ_query_api.load_onchain_y3_weekly` should include a docstring section enumerating the admitted methodology-tag literals and what each segment means. The right place is the docstring of `load_onchain_y3_weekly` (lines 1472–1486) since that's the canonical reader. A `_KNOWN_Y3_METHODOLOGY_TAGS: Final[dict[str, str]]` constant would also work and would let the function signature docstring point at it.

The literal itself is not so long as to be intractable, and the segments are reasonably mnemonic (`co_dane`, `br_bcb`, `eu_eurostat`). Compared to alternatives (a sha256-style opaque tag, or a numeric version), this is the better tradeoff. I would NOT block on the literal; I would flag the mapping-discoverability gap.

**Methodology literal: PASS-with-non-blocking-advisory.** Reviewer-ack checkbox per RC advisory A6: literal accepted from this reviewer's lens.

---

## §4. Composite PK exploitation — downstream double-count footgun (the load-bearing finding)

**Lens:** is there ANY query path where downstream consumers might accidentally double-count `y3_v1` + `y3_v2` rows?

I read `econ_query_api.load_onchain_y3_weekly` (lines 1472–1511). The function signature is:

```python
def load_onchain_y3_weekly(
    conn: duckdb.DuckDBPyConnection,
    source_methodology: str = "y3_v1",
    *,
    start: date | None = None,
    end: date | None = None,
) -> tuple[OnchainY3Weekly, ...]:
```

The `where` clause **always** filters by `source_methodology = ?` (lines 1488-1493 — there is no branch where the filter is omitted). Default is `"y3_v1"`. This is **filtered-by-default** ⇒ NO double-count footgun exists in this reader.

**HOWEVER** — and this is the load-bearing finding — the inverse footgun fires:

- A maintainer who knows about the new Rev-5.3.2 panel must pass `source_methodology="y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"` **EXACTLY**, byte-for-byte.
- Default callers (those calling `load_onchain_y3_weekly(conn)` with no `source_methodology` override) silently get **only the y3_v1 rows** — i.e., they will not see the new Rev-5.3.2 panel at all. The new panel is invisible by default.
- The plan's acceptance criterion at line 1929 explicitly states: *"The methodology tag literal value is recorded in the verification memo and is added to the `econ_query_api.load_onchain_y3_weekly()` admitted-set (additive schema-migration test asserts this)."*
- The DE memo §6 directly admits: *"The `econ_query_api.load_onchain_y3_weekly` reader is parameter-driven (`source_methodology: str = "y3_v1"`) — no admitted-set whitelist exists in code; the new tag is consumable as-is by passing the literal string. ... Per the file-scope discipline, no code change to `econ_query_api.py` was made."*

This is a **direct gap against acceptance criterion line 1929**. The plan asks for an "admitted-set" with an additive schema-migration test asserting it; the implementation defends not making the change on file-scope grounds. This is a *contractual mismatch*, not a technical one. Two valid resolutions exist:

1. **Patch the gap now** — add a `_KNOWN_Y3_METHODOLOGY_TAGS: Final[frozenset[str]]` constant in `econ_query_api.py`, validate the `source_methodology` argument against it (or warn on miss), and add a schema-migration test that the new literal is in the set. This is a small additive change, not a refactor, and is well within file-scope discipline (one new constant + one new validation guard + one new test).

2. **Document the gap, route the plan to a CORRECTIONS block, and let downstream tasks proceed under the parameter-driven contract.** This requires an explicit acknowledgment from the orchestrator that the plan's literal acceptance criterion is being relaxed, and a plan-body amendment that removes the "admitted-set" requirement.

The current commit takes neither path — it executes the ingest, declares the gate cleared, and asserts downstream dispatches are unblocked. **From a senior-eng lens, this is contract drift.** The plan is a binding document; the acceptance criterion is part of it; an unaddressed acceptance-criterion gap should not pass a senior-developer review without an explicit disposition.

**This is the blocking finding.** I would not dispatch Task 11.N.2d.1-reframe or Task 11.O-scope-update until either (1) lands or (2) is explicitly chosen via CORRECTIONS block.

---

## §5. Honesty discipline — the 76-vs-65 narrative is plausible but misattributed

**Lens:** is the DE's "γ backward extension explains the 76-vs-65 gap" narrative honest?

The plan's risk note (line 1940) projects ~65 joint weeks under the documented mix. The DE memo §3.2 reports 76. The DE memo §3.2 + §0 attributes the gap to:

> *"The γ window swap to `start = 2023-08-01` extends the per-country panels backward by ~5 months over the prior `2024-09-01` start. This adds backward-direction coverage that the risk note's EU-binding-only arithmetic did not include explicitly."*

I checked the joint window detail in memo §3.3:

> *"First joint nonzero week: 2024-09-27. Last joint nonzero week: 2026-03-13."*

The X_d series `carbon_basket_user_volume_usd` has its own start date — per `MEMORY.md::project_duckdb_xd_weekly_state_post_rev531`, the X_d panel starts on **2024-08-30** (82 weeks, 77 nonzero through panel max ~2026-04-03). So the joint *lower bound* is `max(Y3_min, Xd_min)` ≈ 2024-08-30, snapped forward to the first nonzero week of `carbon_basket_user_volume_usd` = 2024-09-27.

**Crucial:** if the γ backward extension to 2023-08-01 added Y₃ rows in 2023-08 → 2024-08, those rows have **no X_d counterpart** (X_d starts 2024-08-30). They would contribute **zero** to the joint nonzero count. The γ backward extension *cannot* be the source of the 76-vs-65 gap on the joint metric.

The DE memo §3.2 *does* mention the LOCF-tail effect:
> *"The Friday-anchor + LOCF tail (per Y₃ design doc §7) extends the panel beyond the EU 2025-12-01 source cutoff to 2026-03-27 (panel max)."*

This LOCF tail (~16 Friday-weeks from 2025-12-01 to 2026-03-27) IS where the gap comes from — the joint-window upper end is `min(Y3_end_with_LOCF, Xd_end)` ≈ 2026-03-13 (per memo §3.3), which extends the joint count from the EU-cutoff arithmetic projection (~65) toward 76. The LOCF tail is the load-bearing mechanism; the γ extension contributes 0 to the joint count.

**The DE memo lists BOTH mechanisms in §3.2 (γ + LOCF), but the §0 / §5 / commit-message narrative emphasizes γ as the dominant explanation.** This is **a misattribution of causation**, not a fabrication — both mechanisms are mentioned, but the dominant one (LOCF tail) is downplayed.

**This is an honesty issue under `feedback_strict_tdd` and the project's anti-fishing discipline.** It is not the same as a tuned PASS, but it does drift from the project's standard of "explain what actually happened." The fix is small: amend the memo §3.2 to lead with LOCF-tail extension as the dominant mechanism, with γ noted as contributing only to the panel-row count (116 vs the binding-cutoff projection of ~109), not to the joint-overlap count.

I take this as a NEEDS-WORK item but a *narrative* one, not a *gate* one. The 76 figure itself is correct; the explanation of why 76 emerged is misattributed.

---

## §6. Provenance integrity

**Lens:** is the DE's claim "two new symbols introduced" verifiable?

DE claims (memo §7):
> *"Two new test functions in `scripts/tests/inequality/test_y3_rev532_conn_forward.py` (file-scoped to this task)."*
> *"One new `source_methodology` literal value in `onchain_y3_weekly` (additive INSERT under composite PK)."*

Verified: `test_y3_rev532_conn_forward.py` defines exactly two `def test_*` functions:
- `test_ingest_y3_weekly_forwards_conn_to_wc_cpi_fetcher` (line 70)
- `test_ingest_y3_weekly_call_site_uses_kwarg_form` (line 185)

The single new methodology-tag literal in DuckDB is a runtime artifact (additive INSERT); I did not run a live DB read to verify the exact rowcount, but the DE memo §3.2 reports it (116 rows under the new tag). RC will live-verify this.

The `git show --stat` output confirms:
- `contracts/scripts/econ_pipeline.py` — 6 lines changed (5 added comment + 1 changed call-site line, consistent with a one-line patch + 4-line preamble).
- `contracts/scripts/tests/inequality/test_y3_rev532_conn_forward.py` — 206 lines added (new file).
- `contracts/.scratch/2026-04-25-y3-rev532-ingest-result.md` — 205 lines added (new memo).

No mutations to `y3_data_fetchers.py`, `y3_compute.py`, `econ_schema.py`, `econ_query_api.py`, `carbon_calibration.py`, or any other production code. Provenance ledger matches the file scope claim.

**Provenance integrity: PASS.**

---

## §7. Downstream readiness — Task 11.N.2d.1-reframe blocker

**Lens:** can downstream tasks dispatch immediately, or is something technically missing?

DE asserts (memo §8):
> *"Task 11.N.2d.1-reframe (IMF-IFS-only sensitivity panel) is unblocked."*
> *"Task 11.O-scope-update is unblocked."*

For Task 11.N.2d.1-reframe specifically, the body (plan lines 1957–1975) requires the *primary* panel to commit first, which it has. **However**, the reframe will need to do per-week comparisons between the primary (Rev-5.3.2 mixed-source) panel and the IMF-IFS-only sensitivity panel. The natural query path is something like:

```python
primary = load_onchain_y3_weekly(
    conn, source_methodology="y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"
)
sensitivity = load_onchain_y3_weekly(
    conn, source_methodology="y3_v2_imf_only_sensitivity_3country_..."  # literal TBD
)
```

This works **only if** the reframe agent knows the byte-exact primary literal. The DE memo §6 records it; that is the channel. But the broader concern from §4 (no admitted-set whitelist) applies: if the reframe agent typoes the literal by one character, the call returns an empty tuple silently (no `KeyError`, no `ValueError` — just empty results). That silent-empty behavior is exactly the kind of guard `feedback_silent_test_pass` patterns warn against.

**For Task 11.N.2d.1-reframe to dispatch with the right safeguards, either:**
- (A) the §4 admitted-set + validation guard lands first, OR
- (B) the reframe's plan-body explicitly requires a "non-empty result post-load" assertion in the comparison memo authoring step.

The plan body for 11.N.2d.1-reframe (lines 1957–1975) does NOT currently include such an assertion. So dispatching the reframe under the current state is technically possible but **risks silent-empty regression**.

**For Task 11.O-scope-update**, the in-place plan-body edit consumes the new literal as a string token; no DB-read query path is in scope, so the silent-empty risk does not fire. Task 11.O-scope-update is genuinely dispatch-ready.

**Downstream readiness:** Task 11.O-scope-update READY; Task 11.N.2d.1-reframe READY-WITH-RISK (silent-empty footgun if §4 unaddressed and no per-task guard added).

---

## §8. Reviewer-ack checkbox (per RC advisory A6)

The methodology tag literal landed in `onchain_y3_weekly` is:

> `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`

- [x] **Senior Developer ack** — literal accepted from this reviewer's lens. It is self-documenting given the design-doc §10 mapping; the discoverability advisory in §3 above is a non-blocking suggestion.

(CR + RC ack checkboxes are theirs to mark.)

---

## §9. Verdict summary

**NEEDS-WORK** with three items:

1. **§4 BLOCKING (acceptance-criterion gap):** plan line 1929 requires the new methodology-tag literal to be added to a `load_onchain_y3_weekly()` admitted-set with an additive schema-migration test. The implementation skipped this on file-scope grounds. Resolve by EITHER (a) adding a `_KNOWN_Y3_METHODOLOGY_TAGS: Final[frozenset[str]]` constant + validation guard + test in `econ_query_api.py`, OR (b) issuing a plan-body CORRECTIONS block that removes the admitted-set requirement. Without one of these, downstream Task 11.N.2d.1-reframe inherits a silent-empty footgun.

2. **§5 NEEDS-WORK (honesty narrative):** the memo §0 / §5 + commit message attribute the 76-vs-65 joint-coverage gap to the γ backward extension. Mechanically, γ adds Y₃ rows pre-2024-08-30 where X_d data does not exist; those rows contribute 0 to the joint count. The dominant mechanism is the **LOCF tail extension** beyond the EU 2025-12-01 cutoff to 2026-03-27 (memo §3.3 has the right facts but the wrong emphasis). Amend memo §0 + §3.2 + §5 to lead with LOCF-tail extension as the dominant mechanism. The 76 figure itself is correct.

3. **§7 ADVISORY (downstream readiness):** Task 11.N.2d.1-reframe risks silent-empty regression if a maintainer typoes the byte-exact primary methodology literal. Either resolve §4 first, or require a non-empty-result assertion in the reframe's plan body before dispatch.

**Non-blocking advisories:**
- §1 memo line-number imprecision (cites :2905, actual call site is :2909).
- §2 add a comment to the test file explaining why monkeypatch is at source module, not consumer module.
- §3 add a methodology-tag mapping docstring or constant near `load_onchain_y3_weekly` for 6-month maintenance discoverability (this dovetails with §4's resolution).

**Patch quality, test design, provenance integrity, anti-fishing discipline (N_MIN gate held at 75, hash pin matched, no silent threshold drift)** all PASS.

The patch is correct; the verification memo is *substantively* solid; the contractual gap with plan line 1929 + the misattributed causation narrative are real and need resolution before the chain advances. This is not a "rewrite the commit" ask — this is a "two follow-up patches and an amended memo" ask.

---

## Files referenced

- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/econ_pipeline.py` (lines 2890–2920 — the patched call site)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/y3_data_fetchers.py` (lines 244–299 — the receiver's signature and dispatch)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/econ_query_api.py` (lines 1472–1511 — the reader; site of the §4 acceptance-criterion gap)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/tests/inequality/test_y3_rev532_conn_forward.py` (the new failing-first test file)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-y3-rev532-ingest-result.md` (the DE verification memo under review)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (Task 11.N.2d-rev spec, lines 1916–1953; downstream Task 11.N.2d.1-reframe lines 1957–1975)

---

## Senior Developer signature

This review was conducted read-only per `feedback_implementation_review_agents`. No code modifications, no DB mutations. Three reviewers (CR + RC + SD) operated in parallel under `feedback_three_way_review`; this report is the SD third leg.
