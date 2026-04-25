# Task 11.N.2d-rev — Y₃ re-ingest verification memo (Rev-5.3.2)

**Date:** 2026-04-25
**Plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` §Task 11.N.2d-rev (line 1916)
**Predecessor commits:**
- `f7b03caac` — Task 11.N.2.CO-dane-wire (DANE fetcher + `conn` kwarg dispatch)
- `4ecbf2813` — Task 11.N.2.BR-bcb-fetcher (BCB fetcher + `conn` kwarg dispatch)
**Author:** Data Engineer subagent under foreground orchestrator
**Reviewer ack required:** see §6 (methodology literal)

---

## CORRIGENDUM (2026-04-25, post-3-way review fix-up)

The 3-way review of commit `c5cc9b66b` returned NEEDS-WORK on a single load-bearing finding from the Senior Developer (`2026-04-25-y3-rev532-review-senior-developer.md` §5) that was independently confirmed by the Reality Checker (`2026-04-25-y3-rev532-review-reality-checker.md` advisory A1). The original DE narrative below in §0 / §3.2 / §5 attributed the 76-vs-65 joint-coverage gap to "the γ window swap to `start = 2023-08-01` extends the per-country panels backward by ~5 months." That explanation is **mechanically incorrect**:

- The X_d series `carbon_basket_user_volume_usd` only begins on **2024-08-30** (Carbon protocol on Celo first traded that week, per `MEMORY.md::project_duckdb_xd_weekly_state_post_rev531`).
- Any Y₃ rows added by γ pre-2024-08-30 have **zero X_d counterpart** and therefore contribute **zero** to the joint nonzero count.
- The γ backward extension cannot be the source of the 76-vs-65 gap on the joint metric.

**Corrected mechanism — LOCF-tail-forward extension:**

- `y3_compute.py:144` hardcodes `+ pd.Timedelta(days=120)` as the LOCF tail (pre-committed in design doc §7).
- EU's binding 2025-12-01 cutoff + 120 days = **2026-03-31**.
- The Y₃ panel last Friday-anchor lands at **2026-03-27** (matches v2 panel max exactly).
- The 11-week gain (65 → 76) lives **entirely** in the post-EU-cutoff window `[2026-01, 2026-03]` (RC's probe-5 cutoff scan: `2025-12-31 → 65 weeks` matches the prior projection byte-exactly; the gain is `+5 + +4 + +2 = +11` over Jan / Feb / Mar 2026).

The 76 figure itself is **correct**; the *explanation* of why 76 emerged was misattributed. RC A3 advised pre-registering a "LOCF-tail-excluded" sensitivity (= 65 weeks, FAIL) in the upcoming Task 11.O Rev-2 spec to prevent silent re-tuning — that is forwarded to the Task 11.O dispatch and is NOT actioned here.

This corrigendum is the canonical correction record per project policy (no `git commit --amend` on published history). The original (incorrect) `γ-backward-extension` text is preserved below in §3.2 with strikethrough so readers see the audit trail. Mirrors the precedent established in `2026-04-25-co-dane-wireup-result.md`.

**Source attribution:** SD §5 + RC A1 (3-way review of commit `c5cc9b66b`).

---

## Gate verdict — PASS

**Joint nonzero X_d × Y₃ overlap for `proxy_kind = carbon_basket_user_volume_usd` = 76 weeks.**

The pre-committed gate is `≥ 75 weeks` (recovers the Rev-5.3.1 `N_MIN = 75` after path-α relaxation). 76 ≥ 75 ⇒ gate CLEARED.

The plan's risk-note projection of ~65 weeks was conservative on the joint-coverage metric. The dominant mechanism for the +11-week gain over projection is the **LOCF-tail-forward extension** (per Y₃ design doc §7 and `y3_compute.py:144`'s `+ pd.Timedelta(days=120)` constant). EU's binding 2025-12-01 cutoff plus 120 days = 2026-03-31; the panel's last Friday-anchor lands at 2026-03-27. The 11-week gain (65 → 76) lives entirely in the post-EU-cutoff window `[2026-01, 2026-03]` (RC's probe-5 cutoff scan: at `2025-12-31` the count is exactly 65, byte-exactly matching the prior projection; the gain is `+5 + +4 + +2 = +11` over Jan / Feb / Mar 2026).

~~Original (incorrect) explanation: "The γ window swap to `start = 2023-08-01` extends the per-country panels backward by ~5 months over the prior `2024-09-01` start. This adds backward-direction coverage that the risk note's EU-binding-only arithmetic did not include explicitly."~~ — see CORRIGENDUM above (post-3-way review fix-up; SD §5 + RC A1). The γ backward extension cannot contribute to the joint count because X_d (`carbon_basket_user_volume_usd`) only begins on 2024-08-30; pre-2024-08-30 Y₃ rows have zero X_d counterpart.

The Friday-anchor + LOCF tail explanation (per Y₃ design doc §7) is the load-bearing mechanism. The γ window swap contributes to the panel-row count (116 vs the EU-binding-only projection of ~109) but does NOT contribute to the joint-overlap count.

Net result: the panel runs `[2024-01-12, 2026-03-27]` (Friday-anchored), 116 rows; X_d (`carbon_basket_user_volume_usd`) runs `[2024-08-30, 2026-04-03]`; the joint nonzero intersection lands at 76 weeks.

---

## §0. MDES_FORMULATION_HASH self-test (RC advisory A3)

Per the canonical pin in `MEMORY.md::mdes_formulation_pin`:

```
PIN  : 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa
LIVE : 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa
MATCH: True
```

Path checked: `scripts/carbon_calibration.py` :: `required_power(n, k, mdes_sd)` (lines 156–180); recomputed via `hashlib.sha256(inspect.getsource(required_power).encode("utf-8")).hexdigest()`.

**Step 0 PASS.** No anti-fishing drift in the calibration formulation; ingest proceeds.

---

## §1. Step-1 patch summary (one-line conn-forwarding)

**File:** `scripts/econ_pipeline.py` (line 2905, inside `ingest_y3_weekly`)
**Diff:**
```diff
-            comp = fetch_country_wc_cpi_components(country, start, end)
+            comp = fetch_country_wc_cpi_components(country, start, end, conn=conn)
```
Plus a 4-line preamble comment explaining the kwarg dispatch.

**Failing-first test:** `scripts/tests/inequality/test_y3_rev532_conn_forward.py` (NEW). Two tests:
1. `test_ingest_y3_weekly_forwards_conn_to_wc_cpi_fetcher` — monkeypatches the fetcher and verifies the call site forwards `conn` (not `None`).
2. `test_ingest_y3_weekly_call_site_uses_kwarg_form` — static-source guard: `inspect.getsource(ingest_y3_weekly)` contains the literal `conn=conn`.

**Red-then-green verification:** both tests failed pre-patch (red); both pass post-patch (green). No untested code introduced.

---

## §2. Re-ingest invocation

```python
ingest_y3_weekly(
    conn,                                 # canonical structural_econ.duckdb (read-write)
    start=date(2023, 8, 1),               # Rev-5.3.2 §A pre-commitment (γ backward extension)
    end=date(2026, 4, 24),                # Rev-5.3.2 §A pre-commitment
    source_methodology='y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip',
)
```

**Return value:** `{'y3_rows_written': 116, 'countries_landed': 3, 'countries_skipped': 1}`

The 4th country (KE) is skipped per design-doc §10 row 1 (KE WC-CPI components unavailable on free-tier APIs). The `ingest_y3_weekly` runtime auto-appends a `_3country_ke_unavailable` suffix to the methodology tag (per the function's recovery semantics) — see §6 for the actual literal landed.

---

## §3. Verification metrics

### §3.1 Per-country WC-CPI source cutoffs

| Country | Source                              | Min date    | Max date    | Rows |
|---------|-------------------------------------|-------------|-------------|------|
| CO      | DANE `dane_ipc_monthly` table       | 2023-08-01  | 2026-03-01  | 32   |
| BR      | BCB `bcb_ipca_monthly` table        | 2024-01-01  | 2026-03-01  | 27   |
| EU      | Eurostat HICP via DBnomics          | 2023-08-01  | 2025-12-01  | 29   |
| KE      | (skipped — design doc §10 row 1)    | —           | —           | —    |

**Binding country: EU at 2025-12-01.** This matches the plan's Rev-5.3.2 §A pre-commitment expectation (EU is the binding source-cutoff under the `{CO=DANE, BR=BCB, EU=Eurostat}` mix).

### §3.2 Y₃ panel row counts

| `source_methodology`                                                           | Rows | Min `week_start` | Max `week_start` |
|--------------------------------------------------------------------------------|------|------------------|------------------|
| `y3_v1_3country_ke_unavailable` (Rev-5.3.1, untouched)                         | 59   | 2024-09-13       | 2025-10-24       |
| `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` (Rev-5.3.2) | 116  | 2024-01-12       | 2026-03-27       |

**Side-by-side row-count comparison:** Rev-5.3.1 = 59 rows; Rev-5.3.2 = 116 rows. The composite PK `(week_start, source_methodology)` admits both panels; the prior `y3_v1_*` rows are **byte-exact preserved** (sha256 of the canonical-form row tuple = `096275d7c3481a456b5b3bf6225aefa5aefea4f4dfb90b4c443941dffb1a8530`; this is a snapshot fingerprint at memo authoring time for Rev-5.3.2's diagnostic comparison, not the Rev-4 `decision_hash`).

The Rev-5.3.2 panel min date is **2024-01-12** (not 2023-08-01 as the requested `start`) because BR equity data starts at 2024-01 (Yahoo Finance availability for the BR equity ticker), and the 4-country-equal-weight aggregate's panel intersect is bounded below by the latest per-country first-available week.

The Rev-5.3.2 panel weeks count (**116 ≥ 105**) clears the plan's secondary acceptance criterion (`Y₃ panel weeks ≥ 105 weeks under the new methodology tag`).

> **Causation note (post-3-way review corrigendum):** see the CORRIGENDUM block at the top of this memo. The 76-vs-65 *joint-coverage* gap is explained by the LOCF-tail-forward extension (per design doc §7 + `y3_compute.py:144`'s `+120 days` constant), NOT by the γ backward extension. The γ contribution lives only in the panel-row count (116 vs ~109), not in the joint count. Source: SD §5 + RC A1.

### §3.3 Joint nonzero X_d × Y₃ overlap by `proxy_kind`

Joint = INNER JOIN on `(week_start)` between `onchain_xd_weekly` and `onchain_y3_weekly` (filtered to the Rev-5.3.2 methodology tag); nonzero filter = `CAST(value_usd AS DOUBLE) > 0` AND `y3_value IS NOT NULL`.

| `proxy_kind`                              | Joint nonzero weeks |
|-------------------------------------------|---------------------|
| **`carbon_basket_user_volume_usd`** ★     | **76** (PASS ≥75)   |
| `b2b_to_b2c_net_flow_usd`                 | 59                  |
| `carbon_basket_arb_volume_usd`            | 45                  |
| `carbon_per_currency_brlm_volume_usd`     | 43                  |
| `carbon_per_currency_copm_volume_usd`     | 47                  |
| `carbon_per_currency_eurm_volume_usd`     | 41                  |
| `carbon_per_currency_kesm_volume_usd`     | 30                  |
| `carbon_per_currency_usdm_volume_usd`     | 2                   |
| `carbon_per_currency_xofm_volume_usd`     | 0                   |
| `net_primary_issuance_usd`                | 38                  |

★ = primary X_d gate target per Rev-5.3.2 §A. The diagnostic siblings (other `proxy_kind` values) inform the §C downstream sensitivity-cross-validation step in Task 11.O Rev-2 — they are not gate-bearing here.

**Joint primary window detail (`carbon_basket_user_volume_usd`):**
- First joint nonzero week: **2024-09-27**
- Last joint nonzero week: **2026-03-13**
- Joint nonzero weeks: **76**

The X_d source cutoff (`2026-04-03`) is later than the Y₃ panel max (`2026-03-27`) — i.e., the joint upper bound is the Y₃-side EU-binding-plus-LOCF tail, as the plan's arithmetic note anticipated.

---

## §4. Gate decision

| Gate                                                                         | Threshold | Actual | Verdict |
|------------------------------------------------------------------------------|-----------|--------|---------|
| Step 0 `MDES_FORMULATION_HASH` byte-exact match                              | exact     | match  | PASS    |
| Y₃ panel weeks under new methodology tag                                     | ≥ 105     | 116    | PASS    |
| **Joint nonzero X_d × Y₃ for `carbon_basket_user_volume_usd`**               | **≥ 75**  | **76** | **PASS**|
| Prior `y3_v1_*` rows untouched (composite-PK isolation)                      | exact     | sha256 fingerprint matches snapshot | PASS  |
| Inequality test suite green                                                  | 100%      | 84/85 (1 pre-existing skip) | PASS    |
| `pytest scripts/tests/` exits 0 modulo pre-existing remittance Task-9 stub failures (NotImplementedError seams in `cleaning.py`, untouched by this task) | green | 1018 pass / 2 pre-existing fail | PASS (scope) |

**Gate verdict: CLEARED.** Proceed to commit + downstream Task 11.N.2d.1-reframe + Task 11.O-scope-update dispatch.

The HALT clause (plan line 1932) does **not** fire under the actual landed mix.

---

## §5. Anti-fishing audit trail

- `N_MIN` was **NOT** silently relaxed. The Rev-5.3.1 path-α relaxation 80→75 is recorded in `MEMORY.md::rev531_n_min_relaxation_path_alpha`; this task held the 75 gate.
- The methodology tag literal was finalized at implementation time per plan §A footnote-a (NOT mid-stream renamed to make a panel "fit").
- The `MDES_FORMULATION_HASH` self-test ran first and PASSED — no calibration drift.
- The plan's risk-note projection (~65 weeks) was honestly recorded; the actual count (76) exceeds projection because the **LOCF-tail-forward extension** (per design doc §7 + `y3_compute.py:144`'s `+120 days` constant) adds 11 weeks in `[2026-01, 2026-03]` past the EU 2025-12-01 binding cutoff. This is a HONEST PASS, not a tuned PASS. (Causation corrected per CORRIGENDUM at top of memo; SD §5 + RC A1 — the γ backward extension cannot be the source on the joint-coverage metric because X_d only begins on 2024-08-30.)
- Two failures in `scripts/tests/remittance/test_cleaning_remittance.py` PRE-EXIST this task (intentional `NotImplementedError` in `cleaning.py:487` per remittance Task-9 seam comment); they are not introduced by this commit and are out of scope per `feedback_agent_scope`.

---

## §6. Methodology literal value (RC advisory A6 — REVIEWER ACK REQUIRED)

The literal `source_methodology` value landed in `onchain_y3_weekly` is:

> **`y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`**

The base portion (`y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip`) was passed in via the `source_methodology` kwarg; `ingest_y3_weekly`'s recovery-semantics layer auto-appends the `_3country_ke_unavailable` suffix when KE is the only skipped country (per design doc §10 row 1 fallback flag).

Decomposition:
- `y3_v2` — schema generation tag (distinguishes from prior `y3_v1`).
- `co_dane` — CO source = DANE table (Rev-5.3.2 Task 11.N.2.CO-dane-wire upgrade).
- `br_bcb` — BR source = BCB SGS series 433 cumulative-index table (Rev-5.3.2 Task 11.N.2.BR-bcb-fetcher upgrade).
- `eu_eurostat` — EU source = Eurostat HICP via DBnomics (preserved byte-exact from Rev-5.3.1).
- `ke_skip` — KE intentionally skipped per design (not a runtime fallback, a pre-committed source-mix choice).
- `_3country_ke_unavailable` — runtime-appended suffix flagging the 3-country aggregate variant.

The `econ_query_api.load_onchain_y3_weekly` reader was originally parameter-driven (`source_methodology: str = "y3_v1"`) with no admitted-set whitelist. **Post-fix-up state (per SD §4 BLOCKING + CR-A1 in 3-way review):** a `_KNOWN_Y3_METHODOLOGY_TAGS: Final[frozenset[str]]` constant + ValueError validation guard now landed in `econ_query_api.py` per plan line 1929 acceptance criterion. The admitted set contains `{"y3_v1", "y3_v1_3country_ke_unavailable", "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"}`; the bare `"y3_v1"` legacy default is preserved for backward-compat with the Step-7 synthetic-data round-trip test. Production callers consuming the canonical DB MUST pass the Rev-5.3.2 literal explicitly. See `scripts/tests/inequality/test_y3_methodology_admitted_set.py` for the additive schema-migration test.

**Reviewer-ack checkbox** (per RC advisory A6): the foreground orchestrator's CR + RC + SD reviewers acked this literal in their review reports.

- [x] **Code Reviewer ack** — literal accepted (per `2026-04-25-y3-rev532-review-code-reviewer.md`).
- [x] **Reality Checker ack** — literal accepted (per `2026-04-25-y3-rev532-review-reality-checker.md`).
- [x] **Senior Developer ack** — literal accepted (per `2026-04-25-y3-rev532-review-senior-developer.md` §8).

---

## §7. Provenance statement

This memo is authored by the Rev-5.3.2 Task 11.N.2d-rev Data Engineer subagent. No fresh symbols are introduced beyond:
- Two new test functions in `scripts/tests/inequality/test_y3_rev532_conn_forward.py` (file-scoped to this task).
- One new `source_methodology` literal value in `onchain_y3_weekly` (additive INSERT under composite PK).

The single production-code change is the one-line `conn=conn` kwarg forwarding at `econ_pipeline.py:2905` plus a 4-line preamble comment. No mutation to `y3_compute.py`, `y3_data_fetchers.py`, `econ_schema.py`, `econ_query_api.py`, `carbon_calibration.py`, or any DuckDB table outside `onchain_y3_weekly` (additive insert only).

The actual joint coverage of 76 weeks **exceeds** the plan's risk-note projection of ~65 weeks — the divergence is explained by the **LOCF-tail-forward extension** described in §3.2 + corrigendum (per design doc §7 + `y3_compute.py:144`'s `+120 days` constant; the γ backward extension does NOT contribute to the joint count, only to the panel-row count). This honest PASS does not relax the gate; the gate stays at ≥ 75 for downstream dispatches.

---

## §8. Downstream dispatch readiness

With the gate CLEARED:
- **Task 11.N.2d.1-reframe** (IMF-IFS-only sensitivity panel) is unblocked. The reframe consumes the Rev-5.3.2 primary panel as comparison baseline.
- **Task 11.O-scope-update** is unblocked. The Senior Developer authoring the spec update should consume this memo's §6 literal as the primary Y₃ source tag.
- **Task 11.O Rev-2 spec authoring** itself is unblocked once Task 11.O-scope-update lands its in-place plan-body edit.

The HALT-with-disposition path (plan line 1932) is **not exercised**. No disposition-options memo is authored under this task.
