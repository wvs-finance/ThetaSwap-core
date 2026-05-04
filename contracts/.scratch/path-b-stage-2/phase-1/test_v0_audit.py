"""TDD failing-test scaffold for Pair D Stage-2 Path B v0 audit deliverable.

Per `feedback_strict_tdd` (NON-NEGOTIABLE): this test module is authored
BEFORE any v0 audit-generation implementation lands. The 5 tests below
encode spec §2 v0 Exit criteria + spec §4.0 normative parquet schema
verbatim and must FAIL on first run because:

  (i)  the three v0 parquet artifacts have NOT yet been emitted to
       `contracts/.scratch/path-b-stage-2/v0/`; AND
  (ii) `v0_audit.py` is a stub raising NotImplementedError on every
       artifact-generation entry point.

Phase 1 Tasks 1.2 + 1.3 + 1.4 (Data Engineer + parquet emission +
test-suite hardening) implement the v0 audit ladder; Task 1.3 lands
the parquet emit that turns these 5 FAILs into 5 PASSes.

Spec governing tests:
  contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md
    v1.3 sha256 4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea

Plan governing tests:
  contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md
    sha256 406c55a33e28af9e57b4cb912017e3bea26993733dc5260c0486e507d7f9cd38

Stage-1 PASS verdict (READ-ONLY anchor; NOT re-tested here; provides Pair D
window context):
  contracts/.scratch/simple-beta-pair-d/results/VERDICT.md
    sha256 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf

Test naming convention (5-test mapping per dispatch brief):
  test_a_audit_summary_schema             — spec §4.0 Artifact 1 (audit_summary.parquet)
  test_b_address_inventory_schema         — spec §4.0 Artifact 2 (address_inventory.parquet) + FK
  test_c_event_inventory_schema           — spec §4.0 Artifact 3 (event_inventory.parquet)
  test_d_data_provenance_mirror           — spec §3.A 8-field per-input schema + sha256 mirror
  test_e_feasibility_verdict_present      — spec §4.0 feasibility_v1 + feasibility_notes invariant

Real-data discipline per `feedback_real_data_over_mocks`:
  All parquet reads use real pyarrow / DuckDB I/O against the on-disk
  parquet files in `contracts/.scratch/path-b-stage-2/v0/`. There are no
  mocked file reads. When the parquet files do not yet exist (Task 1.1
  RED state), the tests FAIL with a clear AssertionError pointing at the
  missing artifact path; pytest collection still succeeds.

CORRECTIONS-γ structural-exposure framing:
  Tests assert column names + schema verbatim from spec §4.0; the
  "demand-side" vocabulary appears nowhere in this scaffold (the
  `relevance_v1` enum value `cf_as_input` is the framework's economic-leg
  terminology and is preserved as such, not as behavioral-demand language).
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq
import pytest

# ── Add phase-1/ to sys.path so the v0_audit stub is importable ──────────────
_HERE: Path = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import v0_audit  # noqa: E402  (intentional post-sys.path mutation)


# ── Spec-pinned paths + schema constants (mirrored from spec §4.0) ───────────

# v0 artifacts land at this directory per spec §4.0 last paragraph.
V0_DIR: Path = (
    _HERE.parent.parent  # contracts/.scratch
    / "pair-d-stage-2-B"
    / "v0"
)

AUDIT_SUMMARY_PATH: Path = V0_DIR / "audit_summary.parquet"
ADDRESS_INVENTORY_PATH: Path = V0_DIR / "address_inventory.parquet"
EVENT_INVENTORY_PATH: Path = V0_DIR / "event_inventory.parquet"
DATA_PROVENANCE_PATH: Path = V0_DIR / "DATA_PROVENANCE.md"

# Spec §4.0 Artifact 1 schema (column → (pyarrow type string, nullable)).
# Verbatim from spec §4.0 table; ordering matches column order in spec table.
AUDIT_SUMMARY_SCHEMA: dict[str, tuple[str, bool]] = {
    "venue_id": ("string", False),
    "venue_name": ("string", False),
    "network": ("string", False),
    "contract_address": ("string", False),
    "venue_kind": ("string", False),
    "deployment_block": ("int64", False),
    "first_event_block": ("int64", True),
    "last_event_block": ("int64", True),
    "event_count": ("int64", False),
    "cumulative_volume_usd": ("double", True),
    "tvl_usd_snapshot": ("double", True),
    "snapshot_timestamp_utc": ("timestamp[ns, tz=UTC]", False),
    "audit_block": ("int64", False),
    "data_source_primary": ("string", False),
    "feasibility_v1": ("string", False),
    "feasibility_notes": ("string", True),
}
# Spec v1.4 §4.0 Artifact 1 row-count expectation: 6-12 typical; <4 or >20
# triggers HALT-review per Stage2PathBAuditScopeAnomaly. The HALT threshold
# (not the typical band) is the test's enforcement boundary so values within
# [4, 20] do not fire a false positive against the v1.4 substrate set
# (n=13 = 4 a_l-side Mento + 5 Mento V3 FPMM + 4 ethereum-side venues).
AUDIT_SUMMARY_ROWS_MIN: int = 4
AUDIT_SUMMARY_ROWS_MAX: int = 20

# Spec §4.0 Artifact 1 enum allowlists.
AUDIT_NETWORK_ENUM: frozenset[str] = frozenset({"celo-mainnet", "ethereum-mainnet"})
# Spec v1.4 §4.0 venue_kind enum: includes v1.4 NEW values (mento_v2_bipool,
# mento_broker) per CORRECTIONS-ε; preserves DEPRECATED values (uniswap_v3_pool,
# bill_pay_router, remittance_router) for predecessor-chain audit per spec
# v1.4 §4.0 line 1321.
AUDIT_VENUE_KIND_ENUM: frozenset[str] = frozenset({
    "mento_fpmm",
    "mento_v2_bipool",         # v1.4 NEW per CORRECTIONS-ε
    "mento_broker",            # v1.4 NEW per CORRECTIONS-ε
    "uniswap_v3_pool",         # DEPRECATED v1.4 — preserved for predecessor-chain audit
    "uniswap_v4_pool",
    "panoptic_factory",
    "bill_pay_router",         # DEPRECATED v1.4 — preserved per spec §4.0
    "remittance_router",       # DEPRECATED v1.4 — preserved per spec §4.0
})
# v1.2.1 corrected `alchemy_growth` → `alchemy_free` (free-tier alignment).
AUDIT_DATA_SOURCE_PRIMARY_ENUM: frozenset[str] = frozenset({
    "sqd_network",
    "alchemy_free",
    "dune",
    "the_graph",
    "celoscan",
    "etherscan",
})
AUDIT_FEASIBILITY_V1_ENUM: frozenset[str] = frozenset({"pass", "marginal", "halt"})

# Spec §4.0 Artifact 2 schema.
ADDRESS_INVENTORY_SCHEMA: dict[str, tuple[str, bool]] = {
    "address": ("string", False),
    "network": ("string", False),
    "venue_id": ("string", False),
    "address_role": ("string", False),
    "is_contract": ("bool", False),
    "first_seen_block": ("int64", False),
    "last_seen_block": ("int64", False),
    "tx_count_window": ("int64", False),
}
ADDRESS_INVENTORY_ROWS_MIN: int = 10
ADDRESS_INVENTORY_ROWS_MAX: int = 200
ADDRESS_ROLE_ENUM: frozenset[str] = frozenset({
    "router",
    "factory",
    "pool",
    "token",
    "fee_collector",
    "merchant",
    "user_eoa",
    "mev_bot",
    "other",
})

# Spec §4.0 Artifact 3 schema.
EVENT_INVENTORY_SCHEMA: dict[str, tuple[str, bool]] = {
    "venue_id": ("string", False),
    "event_signature": ("string", False),
    "topic0": ("string", False),
    "event_count": ("int64", False),
    "first_emit_block": ("int64", True),
    "last_emit_block": ("int64", True),
    "relevance_v1": ("string", False),
}
EVENT_INVENTORY_ROWS_PER_VENUE_MIN: int = 2
EVENT_INVENTORY_ROWS_PER_VENUE_MAX: int = 8
RELEVANCE_V1_ENUM: frozenset[str] = frozenset({
    "cf_al_input",
    "cf_as_input",
    "oracle_input",
    "metadata",
    "unused",
})

# Spec §3.A 8-field per-input provenance schema (regex-anchored field labels).
PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "source",
    "fetch_method",
    "fetch_timestamp",
    "sha256",
    "row_count",
    "block_range",
    "schema_version",
    "filter_applied",
)


# ── Helpers (no mocks; real pyarrow + filesystem I/O per
# `feedback_real_data_over_mocks`) ────────────────────────────────────────────


def _read_parquet_or_fail(path: Path, artifact_label: str) -> pq.ParquetFile:
    """Open a parquet file via real pyarrow I/O; AssertionError if absent.

    Avoids `pytest.fail` so the FAILURE shows as a clean AssertionError the
    Phase 1 RED state test_run.md can grep for.
    """
    assert path.exists(), (
        f"spec §4.0: {artifact_label} parquet missing at {path}. "
        "Phase 1 Task 1.3 (Data Engineer parquet emission) has not yet "
        "produced the artifact. RED state expected at Task 1.1."
    )
    return pq.ParquetFile(path)


def _check_pyarrow_dtype(actual_field, expected_type_str: str) -> bool:
    """Compare pyarrow DataType against the spec §4.0 string descriptor.

    Mapping deliberately conservative: matches the spec §4.0 column dtype
    column verbatim. Timestamp comparison uses pyarrow's repr form
    `timestamp[ns, tz=UTC]`.
    """
    actual_str = str(actual_field.type)
    return actual_str == expected_type_str


def _sha256_file(path: Path) -> str:
    """Compute sha256 hex digest of file contents (real I/O)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── test_a — spec §4.0 Artifact 1 (audit_summary.parquet) ────────────────────


def test_a_audit_summary_schema() -> None:
    """spec §4.0 Artifact 1: audit_summary.parquet exists with 6-12 rows;
    column types match spec §4.0 table; primary key venue_id UNIQUE.

    Failure modes (Task 1.1 RED state):
      - parquet absent at AUDIT_SUMMARY_PATH (Task 1.3 has not emitted);
      - schema mismatch (column missing, dtype wrong, nullability inverted);
      - row count outside [6, 12] (triggers spec §6 typed exception
        Stage2PathBAuditScopeAnomaly under <4 or >20; the [6, 12] interior
        range is the §4.0 expected band);
      - venue_id duplicates.
    """
    pf = _read_parquet_or_fail(AUDIT_SUMMARY_PATH, "audit_summary")
    schema = pf.schema_arrow

    # Schema parity: every spec column present with expected dtype + nullability.
    actual_field_names = set(schema.names)
    expected_field_names = set(AUDIT_SUMMARY_SCHEMA.keys())
    missing = expected_field_names - actual_field_names
    extra = actual_field_names - expected_field_names
    assert not missing, (
        f"spec §4.0 Artifact 1: audit_summary.parquet missing columns {missing}. "
        f"Spec column set: {sorted(expected_field_names)}."
    )
    assert not extra, (
        f"spec §4.0 Artifact 1: audit_summary.parquet has unexpected columns "
        f"{extra}. Spec is normative; column set is fixed."
    )

    for col_name, (expected_type, expected_nullable) in AUDIT_SUMMARY_SCHEMA.items():
        field = schema.field(col_name)
        assert _check_pyarrow_dtype(field, expected_type), (
            f"spec §4.0 Artifact 1: column '{col_name}' dtype mismatch. "
            f"Expected {expected_type!r}; got {str(field.type)!r}."
        )
        assert field.nullable == expected_nullable, (
            f"spec §4.0 Artifact 1: column '{col_name}' nullability mismatch. "
            f"Expected nullable={expected_nullable}; got {field.nullable}."
        )

    # Row-count expectation per spec §4.0 paragraph after Artifact 1 table.
    table = pf.read()
    n_rows = table.num_rows
    assert AUDIT_SUMMARY_ROWS_MIN <= n_rows <= AUDIT_SUMMARY_ROWS_MAX, (
        f"spec §4.0 Artifact 1: audit_summary.parquet row count {n_rows} "
        f"outside expected [{AUDIT_SUMMARY_ROWS_MIN}, {AUDIT_SUMMARY_ROWS_MAX}]. "
        f"Spec §6 typed exception Stage2PathBAuditScopeAnomaly fires at <4 or >20."
    )

    # Primary key uniqueness: venue_id unique within file.
    venue_ids = table.column("venue_id").to_pylist()
    assert len(venue_ids) == len(set(venue_ids)), (
        f"spec §4.0 Artifact 1: venue_id primary key NOT unique. "
        f"Duplicates present in {[v for v in venue_ids if venue_ids.count(v) > 1]}."
    )

    # Enum validation: network, venue_kind, data_source_primary.
    for col_name, allowed in (
        ("network", AUDIT_NETWORK_ENUM),
        ("venue_kind", AUDIT_VENUE_KIND_ENUM),
        ("data_source_primary", AUDIT_DATA_SOURCE_PRIMARY_ENUM),
    ):
        values = set(table.column(col_name).to_pylist())
        invalid = values - allowed
        assert not invalid, (
            f"spec §4.0 Artifact 1: column '{col_name}' contains values "
            f"{invalid} outside spec enum {sorted(allowed)}."
        )


# ── test_b — spec §4.0 Artifact 2 (address_inventory.parquet) + FK ───────────


def test_b_address_inventory_schema() -> None:
    """spec §4.0 Artifact 2: address_inventory.parquet exists with 10-200 rows;
    FK venue_id references audit_summary.venue_id; PK (network, address) unique;
    column types match spec §4.0 table.

    Failure modes (Task 1.1 RED state):
      - parquet absent at ADDRESS_INVENTORY_PATH;
      - schema mismatch;
      - row count outside [10, 200] (HALT-review at <5);
      - PK (network, address) duplicates;
      - FK referential integrity violation (venue_id not in audit_summary).
    """
    pf_addr = _read_parquet_or_fail(ADDRESS_INVENTORY_PATH, "address_inventory")
    pf_audit = _read_parquet_or_fail(AUDIT_SUMMARY_PATH, "audit_summary (FK target)")
    schema = pf_addr.schema_arrow

    # Schema parity.
    actual_field_names = set(schema.names)
    expected_field_names = set(ADDRESS_INVENTORY_SCHEMA.keys())
    missing = expected_field_names - actual_field_names
    extra = actual_field_names - expected_field_names
    assert not missing, (
        f"spec §4.0 Artifact 2: address_inventory.parquet missing columns "
        f"{missing}. Spec column set: {sorted(expected_field_names)}."
    )
    assert not extra, (
        f"spec §4.0 Artifact 2: address_inventory.parquet has unexpected columns "
        f"{extra}."
    )
    for col_name, (expected_type, expected_nullable) in ADDRESS_INVENTORY_SCHEMA.items():
        field = schema.field(col_name)
        assert _check_pyarrow_dtype(field, expected_type), (
            f"spec §4.0 Artifact 2: column '{col_name}' dtype mismatch. "
            f"Expected {expected_type!r}; got {str(field.type)!r}."
        )
        assert field.nullable == expected_nullable, (
            f"spec §4.0 Artifact 2: column '{col_name}' nullability mismatch. "
            f"Expected nullable={expected_nullable}; got {field.nullable}."
        )

    table = pf_addr.read()
    n_rows = table.num_rows
    assert ADDRESS_INVENTORY_ROWS_MIN <= n_rows <= ADDRESS_INVENTORY_ROWS_MAX, (
        f"spec §4.0 Artifact 2: row count {n_rows} outside expected "
        f"[{ADDRESS_INVENTORY_ROWS_MIN}, {ADDRESS_INVENTORY_ROWS_MAX}]; "
        "<5 triggers HALT review per spec §4.0 / §6."
    )

    # Primary key (network, address) uniqueness.
    networks = table.column("network").to_pylist()
    addresses = table.column("address").to_pylist()
    pk_pairs = list(zip(networks, addresses, strict=True))
    assert len(pk_pairs) == len(set(pk_pairs)), (
        f"spec §4.0 Artifact 2: PK (network, address) NOT unique. "
        f"Duplicates present."
    )

    # address_role enum.
    role_values = set(table.column("address_role").to_pylist())
    invalid_roles = role_values - ADDRESS_ROLE_ENUM
    assert not invalid_roles, (
        f"spec §4.0 Artifact 2: address_role contains values {invalid_roles} "
        f"outside spec enum {sorted(ADDRESS_ROLE_ENUM)}."
    )

    # FK referential integrity: every venue_id in address_inventory must appear
    # in audit_summary.venue_id.
    audit_venue_ids = set(pf_audit.read().column("venue_id").to_pylist())
    addr_venue_ids = set(table.column("venue_id").to_pylist())
    orphans = addr_venue_ids - audit_venue_ids
    assert not orphans, (
        f"spec §4.0 Artifact 2: FK violation — address_inventory.venue_id "
        f"contains {orphans} not present in audit_summary.venue_id."
    )


# ── test_c — spec §4.0 Artifact 3 (event_inventory.parquet) ──────────────────


def test_c_event_inventory_schema() -> None:
    """spec §4.0 Artifact 3: event_inventory.parquet exists with 2-8 rows
    PER VENUE; column types match spec §4.0 table; PK (venue_id, topic0)
    unique; first_emit_block / last_emit_block null iff event_count == 0.

    Failure modes (Task 1.1 RED state):
      - parquet absent at EVENT_INVENTORY_PATH;
      - schema mismatch;
      - any venue with row count outside [2, 8];
      - PK (venue_id, topic0) duplicates;
      - first_emit_block / last_emit_block nullness inconsistent with
        event_count == 0;
      - relevance_v1 enum violation.
    """
    pf_event = _read_parquet_or_fail(EVENT_INVENTORY_PATH, "event_inventory")
    pf_audit = _read_parquet_or_fail(AUDIT_SUMMARY_PATH, "audit_summary (FK target)")
    schema = pf_event.schema_arrow

    # Schema parity.
    actual_field_names = set(schema.names)
    expected_field_names = set(EVENT_INVENTORY_SCHEMA.keys())
    missing = expected_field_names - actual_field_names
    extra = actual_field_names - expected_field_names
    assert not missing, (
        f"spec §4.0 Artifact 3: event_inventory.parquet missing columns "
        f"{missing}. Spec column set: {sorted(expected_field_names)}."
    )
    assert not extra, (
        f"spec §4.0 Artifact 3: event_inventory.parquet has unexpected columns "
        f"{extra}."
    )
    for col_name, (expected_type, expected_nullable) in EVENT_INVENTORY_SCHEMA.items():
        field = schema.field(col_name)
        assert _check_pyarrow_dtype(field, expected_type), (
            f"spec §4.0 Artifact 3: column '{col_name}' dtype mismatch. "
            f"Expected {expected_type!r}; got {str(field.type)!r}."
        )
        assert field.nullable == expected_nullable, (
            f"spec §4.0 Artifact 3: column '{col_name}' nullability mismatch. "
            f"Expected nullable={expected_nullable}; got {field.nullable}."
        )

    table = pf_event.read()

    # Per-venue row-count window per spec §4.0 ("2-8 rows per venue").
    venue_ids = table.column("venue_id").to_pylist()
    audit_venue_ids = set(pf_audit.read().column("venue_id").to_pylist())
    from collections import Counter

    counts_by_venue = Counter(venue_ids)
    for venue_id, count in counts_by_venue.items():
        assert (
            EVENT_INVENTORY_ROWS_PER_VENUE_MIN
            <= count
            <= EVENT_INVENTORY_ROWS_PER_VENUE_MAX
        ), (
            f"spec §4.0 Artifact 3: venue_id={venue_id!r} has {count} event rows "
            f"outside expected per-venue range "
            f"[{EVENT_INVENTORY_ROWS_PER_VENUE_MIN}, "
            f"{EVENT_INVENTORY_ROWS_PER_VENUE_MAX}]."
        )

    # FK referential integrity.
    orphans = set(venue_ids) - audit_venue_ids
    assert not orphans, (
        f"spec §4.0 Artifact 3: FK violation — event_inventory.venue_id "
        f"contains {orphans} not present in audit_summary.venue_id."
    )

    # PK (venue_id, topic0) uniqueness.
    topic0s = table.column("topic0").to_pylist()
    pk_pairs = list(zip(venue_ids, topic0s, strict=True))
    assert len(pk_pairs) == len(set(pk_pairs)), (
        f"spec §4.0 Artifact 3: PK (venue_id, topic0) NOT unique."
    )

    # relevance_v1 enum.
    relevance_values = set(table.column("relevance_v1").to_pylist())
    invalid_relevance = relevance_values - RELEVANCE_V1_ENUM
    assert not invalid_relevance, (
        f"spec §4.0 Artifact 3: relevance_v1 contains values {invalid_relevance} "
        f"outside spec enum {sorted(RELEVANCE_V1_ENUM)}."
    )

    # null-iff-zero discipline on first_emit_block / last_emit_block.
    event_counts = table.column("event_count").to_pylist()
    first_blocks = table.column("first_emit_block").to_pylist()
    last_blocks = table.column("last_emit_block").to_pylist()
    for i, (ec, fb, lb) in enumerate(zip(event_counts, first_blocks, last_blocks, strict=True)):
        if ec == 0:
            assert fb is None and lb is None, (
                f"spec §4.0 Artifact 3 row {i}: event_count == 0 but "
                f"first_emit_block={fb!r}, last_emit_block={lb!r}; "
                "spec requires both null iff event_count == 0."
            )
        else:
            assert fb is not None and lb is not None, (
                f"spec §4.0 Artifact 3 row {i}: event_count == {ec} > 0 but "
                f"first_emit_block={fb!r}, last_emit_block={lb!r}; "
                "spec requires both non-null iff event_count > 0."
            )


# ── test_d — spec §3.A DATA_PROVENANCE.md mirror discipline ──────────────────


def test_d_data_provenance_mirror() -> None:
    """spec §3.A: every committed artifact has a co-located DATA_PROVENANCE.md
    with 8-field per-input schema; sha256 recorded in provenance matches
    sha256 of the parquet file.

    The 8 normative fields per spec §3.A:
      source, fetch_method, fetch_timestamp, sha256, row_count, block_range,
      schema_version, filter_applied.

    Failure modes (Task 1.1 RED state):
      - DATA_PROVENANCE.md absent at V0_DIR;
      - any of the 3 parquet artifacts missing a provenance entry;
      - any required field missing from a provenance entry;
      - sha256 field value does not match sha256 of the actual parquet
        bytes on disk (BLOCK-B2 sha-mirror discipline; spec §3.A
        "HALT-on-mismatch" trigger for `Stage2PathBProvenanceMismatch`).
    """
    assert DATA_PROVENANCE_PATH.exists(), (
        f"spec §3.A: DATA_PROVENANCE.md missing at {DATA_PROVENANCE_PATH}. "
        "Per BLOCK-B2 closure, every committed dataset directory MUST contain "
        "exactly one DATA_PROVENANCE.md co-located with its parquets. "
        "Phase 1 Task 1.3 has not yet emitted this file."
    )

    provenance_text = DATA_PROVENANCE_PATH.read_text(encoding="utf-8")

    # Verify each of the 3 parquet artifacts has a referenced provenance entry
    # AND the recorded sha256 matches the actual parquet sha256 on disk.
    for parquet_path in (
        AUDIT_SUMMARY_PATH,
        ADDRESS_INVENTORY_PATH,
        EVENT_INVENTORY_PATH,
    ):
        assert parquet_path.exists(), (
            f"spec §3.A: parquet {parquet_path.name} missing — provenance "
            f"sha-mirror cannot be evaluated. Phase 1 Task 1.3 produces this."
        )
        actual_sha = _sha256_file(parquet_path)
        assert actual_sha in provenance_text, (
            f"spec §3.A: sha256 of {parquet_path.name} ({actual_sha}) NOT "
            f"found in DATA_PROVENANCE.md. Per spec §3.A 'HALT-on-mismatch' "
            f"this triggers Stage2PathBProvenanceMismatch typed exception."
        )

    # Verify the 8 normative provenance fields each appear at least once.
    # Match against canonical bolded-label form: e.g., `- **source:**` per the
    # template `contracts/.scratch/path-b-stage-2/phase-0/DATA_PROVENANCE.md.template`.
    # The canonical template form is `**field:**` (closing `**` after colon),
    # NOT `**field**:` — fixed in v1.1 of this scaffold to align with the
    # template at phase-0/DATA_PROVENANCE.md.template lines 25-46.
    for field in PROVENANCE_REQUIRED_FIELDS:
        pattern = rf"\*\*{re.escape(field)}:\*\*"
        assert re.search(pattern, provenance_text), (
            f"spec §3.A: required provenance field '**{field}:**' missing "
            f"from DATA_PROVENANCE.md. The 8 normative fields are: "
            f"{PROVENANCE_REQUIRED_FIELDS}."
        )


# ── test_e — spec §4.0 feasibility_v1 + feasibility_notes invariant ──────────


def test_e_feasibility_verdict_present() -> None:
    """spec §4.0 Artifact 1: feasibility_v1 column populated for every venue
    (one of {pass, marginal, halt}); feasibility_notes REQUIRED if
    feasibility_v1 ∈ {marginal, halt}.

    Failure modes (Task 1.1 RED state):
      - audit_summary.parquet absent;
      - any feasibility_v1 value null or outside the 3-element enum;
      - any row with feasibility_v1 ∈ {marginal, halt} but null/empty
        feasibility_notes (spec §4.0 explicit: "required if feasibility_v1
        is marginal or halt").
    """
    pf = _read_parquet_or_fail(AUDIT_SUMMARY_PATH, "audit_summary")
    table = pf.read()

    feasibility_values = table.column("feasibility_v1").to_pylist()
    feasibility_notes = table.column("feasibility_notes").to_pylist()

    # No null feasibility_v1 (spec column nullability = NO).
    null_idxs = [i for i, v in enumerate(feasibility_values) if v is None]
    assert not null_idxs, (
        f"spec §4.0 Artifact 1: feasibility_v1 nullable=NO but null at row "
        f"indices {null_idxs}."
    )

    # Enum membership.
    invalid = [
        (i, v) for i, v in enumerate(feasibility_values)
        if v not in AUDIT_FEASIBILITY_V1_ENUM
    ]
    assert not invalid, (
        f"spec §4.0 Artifact 1: feasibility_v1 contains invalid values "
        f"{invalid}; spec enum is {sorted(AUDIT_FEASIBILITY_V1_ENUM)}."
    )

    # feasibility_notes required for marginal / halt.
    needs_notes_violations = [
        (i, v, n)
        for i, (v, n) in enumerate(zip(feasibility_values, feasibility_notes, strict=True))
        if v in {"marginal", "halt"} and (n is None or str(n).strip() == "")
    ]
    assert not needs_notes_violations, (
        f"spec §4.0 Artifact 1: feasibility_notes REQUIRED when "
        f"feasibility_v1 ∈ {{marginal, halt}}, but null/empty at rows "
        f"{needs_notes_violations}."
    )
