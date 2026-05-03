# DATA_PROVENANCE.md — Pair D Stage-2 Path B Phase 1

> Per spec §3.A (normative; resolves BLOCK-B2): every committed dataset
> directory MUST contain exactly one `DATA_PROVENANCE.md` file co-located
> with its artifacts. Field-by-field schema parity with the Stage-1 Pair D
> pattern at `contracts/.scratch/simple-beta-pair-d/data/DATA_PROVENANCE.md`
> is REQUIRED; on-chain extensions (`block_range`, `filter_applied`) are
> added on top of the Stage-1 8-field schema, never instead of.
>
> Phase 1 dispatch units append their own §2 entries; sections are
> independent — no Task overwrites another Task's content.

**Governing artifacts (sha-pinned):**

| Artifact | sha256 |
|---|---|
| Spec v1.3 (`contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md`) | `4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea` |
| Plan (`contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md`) | `406c55a33e28af9e57b4cb912017e3bea26993733dc5260c0486e507d7f9cd38` |
| Stage-1 read-only verdict (`contracts/.scratch/simple-beta-pair-d/results/VERDICT.md`) | `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf` |

---

## §1 — Self-meta

- **artifact_path:** `contracts/.scratch/path-b-stage-2/phase-1/`
- **artifact_sha256:** N/A (this directory is a scaffold, not a data artifact;
  per-file sha256 listed in §2 entries)
- **artifact_row_count:** N/A (no parquet emitted at Task 1.1; v0 parquets
  are emitted at Task 1.3)
- **artifact_schema_version:** N/A (the spec §4.0 schema_version field is
  attached to v0 parquet metadata at Task 1.3 emit; Task 1.1 only encodes
  the schema as Python constants in `test_v0_audit.py`)
- **emit_timestamp_utc:** `2026-05-03T11:05:42Z`
- **emit_commit_sha:** `<recorded by orchestrator post-commit; see git log>`
- **emit_plan_task:** `1.1`

---

## §2 — Per-input provenance entries

### Entry 1 — Test scaffold module `test_v0_audit.py`

- **source:** authored in-session under Phase 1 Task 1.1 dispatch. Spec §4.0
  + §3.A drove every assertion; CPO mathematical framework reference
  `contracts/notes/2026-04-29-macro-markets-draft-import.md` informed the
  framing comments. NO on-chain data fetched, NO RPC calls issued.
- **fetch_method:** N/A (in-session authoring; no fetch). Test execution
  command:
  - `source contracts/.venv/bin/activate && pytest contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py --tb=short -v`
- **fetch_timestamp:** `2026-05-03T11:05:42Z` (UTC of pytest execution)
- **sha256:** `029ad2ec207f6c55f52fece40ef8931a57a99995faefdc57c17f11e88c23c412`
  (sha256 of the committed `test_v0_audit.py` file at Task 1.1 close)
- **row_count:** 5 (test functions: test_a_audit_summary_schema,
  test_b_address_inventory_schema, test_c_event_inventory_schema,
  test_d_data_provenance_mirror, test_e_feasibility_verdict_present)
- **block_range:** N/A (no on-chain query)
- **schema_version:** N/A (test module; not a parquet)
- **filter_applied:** N/A (no data partitioning at Task 1.1)

### Entry 2 — v0 audit stub module `v0_audit.py`

- **source:** authored in-session under Phase 1 Task 1.1 dispatch. API
  surface derived verbatim from spec §4.0 v0 Output Schema (3 artifact
  generators) + §3.A Provenance Discipline (atomic provenance-mirror
  emission requirement).
- **fetch_method:** N/A (in-session authoring; no fetch).
- **fetch_timestamp:** `2026-05-03T11:05:42Z`
- **sha256:** `3a4c9d24e04c8777ed7e26c47a618f85a603c9a2a896e2e16133e169c707b8a1`
  (sha256 of the committed `v0_audit.py` stub at Task 1.1 close)
- **row_count:** 3 (entry-point functions: audit_summary_generate,
  address_inventory_generate, event_inventory_generate; each raises
  NotImplementedError at Task 1.1 RED state)
- **block_range:** N/A
- **schema_version:** N/A
- **filter_applied:** N/A

### Entry 3 — Test-run artifact `v0_test_run.md`

- **source:** captured in-session from `pytest --tb=short -v` stdout against
  the Task 1.1 RED state.
- **fetch_method:**
  - `source contracts/.venv/bin/activate && pytest contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py --tb=short -v > /tmp/path_b_phase1_pytest.txt 2>&1`
- **fetch_timestamp:** `2026-05-03T11:05:42Z`
- **sha256:** `<computed at commit; not pinned in this entry because the
  file's own footer references its sibling artifacts' shas — recursive
  sha-pin is anti-pattern>`
- **row_count:** 5 FAILED tests (0 ERROR, 0 PASSED) — see file body for
  verbatim pytest tail.
- **block_range:** N/A
- **schema_version:** N/A (markdown record, not parquet)
- **filter_applied:** N/A

---

## §3 — Re-execution discipline (per spec §3.A)

For Task 1.1's offline pytest scaffold:

- Re-running `pytest contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py`
  in the RED state (no v0 parquets emitted) MUST produce 5 FAILED + 0
  ERROR + 0 PASSED. Drift from this outcome before Task 1.3 emit is a
  test-scaffold regression, NOT a data-fetch regression — triage path is
  pytest debugger / pyarrow API drift / spec ambiguity, NOT
  `Stage2PathBProvenanceMismatch`.
- The on-chain extensions (`block_range`, `filter_applied`) are populated
  to `N/A` for Task 1.1 because the dispatch is offline-only (zero RPC
  calls). Future Phase 1 Tasks 1.2 + 1.3 will populate these fields with
  concrete values per spec §3.A.

---

## §4 — Free-tier + zero-cost certification (Task 1.1)

- **Network calls issued:** 0 (offline pytest only)
- **Alchemy CU consumed:** 0 / 30 000 000 monthly free-tier ceiling
- **Dune credits consumed:** 0 / ~2 500 working assumption
- **SQD Network requests issued:** 0
- **Public RPC requests issued:** 0
- **`burst_rate_log.csv` updates:** 0 (Task 1.1 is offline; no rate-limit
  pin exercised)

This certification is verifiable: re-execution of Task 1.1 against an
isolated network namespace would still produce 5 FAILED tests because no
network access is required.

---

## §5 — Cross-path serialization note (concurrent-agent discipline)

Path A Phase 1 is paused mid-flight (Task 1.4 + Gate B1 not yet
dispatched per orchestrator state). Both paths share the
`phase0-vb-mvp` branch. Task 1.1 commits ONLY Path B paths
(`contracts/.scratch/path-b-stage-2/phase-1/**`); no Path A files are
staged. Path A's pre-existing scaffold at
`contracts/.scratch/path-a-stage-2/phase-1/` is left untouched.
