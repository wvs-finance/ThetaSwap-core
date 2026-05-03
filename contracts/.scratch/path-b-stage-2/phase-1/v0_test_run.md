# v0 audit TDD test-run record (Phase 1 Task 1.1 RED state)

This file records the **expected RED state** of the v0 audit test scaffold
authored under Phase 1 Task 1.1. Per `feedback_strict_tdd`, the 5 tests in
`test_v0_audit.py` MUST FAIL before any audit-generation implementation
lands; this file is the audit-trail proof that they do.

## Spec + plan governing artifacts (sha-pinned)

| Artifact | sha256 |
|---|---|
| `contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md` (v1.3) | `4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea` |
| `contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md` | `406c55a33e28af9e57b4cb912017e3bea26993733dc5260c0486e507d7f9cd38` |

## Stage-1 read-only anchor (NOT re-tested in Path B)

| Artifact | sha256 |
|---|---|
| `contracts/.scratch/simple-beta-pair-d/results/VERDICT.md` | `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf` |

## Test-scaffold artifacts (Phase 1 Task 1.1 outputs)

| File | sha256 |
|---|---|
| `contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py` | `029ad2ec207f6c55f52fece40ef8931a57a99995faefdc57c17f11e88c23c412` |
| `contracts/.scratch/path-b-stage-2/phase-1/v0_audit.py` (stub) | `3a4c9d24e04c8777ed7e26c47a618f85a603c9a2a896e2e16133e169c707b8a1` |

## Pytest run command (UTC 2026-05-03T11:05:42Z)

```
source contracts/.venv/bin/activate
pytest contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py --tb=short -v
```

## Pytest run output (verbatim tail)

```
============================= test session starts ==============================
platform linux -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
configfile: pyproject.toml
plugins: typeguard-4.5.1, anyio-4.13.0
collected 5 items

contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_a_audit_summary_schema FAILED [ 20%]
contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_b_address_inventory_schema FAILED [ 40%]
contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_c_event_inventory_schema FAILED [ 60%]
contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_d_data_provenance_mirror FAILED [ 80%]
contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_e_feasibility_verdict_present FAILED [100%]

=========================== short test summary info ============================
FAILED contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_a_audit_summary_schema
FAILED contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_b_address_inventory_schema
FAILED contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_c_event_inventory_schema
FAILED contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_d_data_provenance_mirror
FAILED contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_e_feasibility_verdict_present
============================== 5 failed in 0.18s ===============================
```

## Failure-mode verification (5 tests, 5 explicit AssertionErrors; 0 ERROR)

All 5 tests halt on `AssertionError` raised inside `_read_parquet_or_fail`
(or the analogous `DATA_PROVENANCE.md.exists()` check in test_d), NOT on
import error / collection error / unhandled exception. This satisfies the
dispatch's "5 FAILED (not ERROR)" success criterion.

| Test name | Failure path | AssertionError message anchor |
|---|---|---|
| `test_a_audit_summary_schema` | `_read_parquet_or_fail(AUDIT_SUMMARY_PATH, ...)` | `audit_summary parquet missing at .../v0/audit_summary.parquet` |
| `test_b_address_inventory_schema` | `_read_parquet_or_fail(ADDRESS_INVENTORY_PATH, ...)` | `address_inventory parquet missing at .../v0/address_inventory.parquet` |
| `test_c_event_inventory_schema` | `_read_parquet_or_fail(EVENT_INVENTORY_PATH, ...)` | `event_inventory parquet missing at .../v0/event_inventory.parquet` |
| `test_d_data_provenance_mirror` | `assert DATA_PROVENANCE_PATH.exists()` | `DATA_PROVENANCE.md missing at .../v0/DATA_PROVENANCE.md` |
| `test_e_feasibility_verdict_present` | `_read_parquet_or_fail(AUDIT_SUMMARY_PATH, ...)` | `audit_summary parquet missing at .../v0/audit_summary.parquet` |

## Real-data discipline (per `feedback_real_data_over_mocks`)

The test scaffold uses **real pyarrow + filesystem I/O** for every
parquet/file read. There are no mocked file objects, no in-memory
fixtures substituting for parquets, and no `unittest.mock` or
`pytest-mock` calls. When the artifacts at
`contracts/.scratch/pair-d-stage-2-B/v0/` finally exist (Phase 1
Task 1.3), the same code paths will exercise the real on-disk
parquets via `pyarrow.parquet.ParquetFile` and `pyarrow.Table`.

The `_sha256_file` helper in test_d also uses real binary I/O on the
parquet bytes, so the BLOCK-B2 sha-mirror invariant is tested against
real artifact contents — no synthetic sha values are accepted.

## Free-tier discipline (zero RPC calls)

Task 1.1 is offline pytest-only. No SQD Network gateway calls, no
Alchemy calls, no Dune queries, no public-RPC fetches are performed
by this test scaffold. The `burst_rate_log.csv` is NOT updated by this
task. The DATA_PROVENANCE.md entry below records `network_calls=0` to
make this explicit.

## SAA disposition (next-step routing)

- **S(uccess) for Task 1.1** = 5 FAILED tests (RED state confirmed).
  Routes to **Phase 1 Task 1.2** (per-venue on-chain audit, parallel
  within rate-limit budget per spec §5.A) under a SEPARATE Data Engineer
  dispatch (concurrent-agent serialization discipline).
- **A(bort)** = pytest collection error / import error / >0 ERROR
  outcomes. Triage: fix imports / pyarrow API drift / spec-§4.0
  ambiguity in scaffold; re-run.
- **A(bort)-with-Pivot** = unrecoverable spec ambiguity surfaces during
  scaffold authoring (none surfaced; report-back caveats item (d) is
  empty).
