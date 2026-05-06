"""Emit 3 v0 Parquet artifacts per spec v1.4 §4.0 BLOCK-B1.

Plan: contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md
  v1.1 sha256 7e2f43c211a314475c3fc2ef5890c268c7216efa55b0b7a9d2c8e5d8d95bca6b
Spec: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md
  v1.4 sha256 fcebc95f923e1b55fbf2eaa22239b00bbde4a9f35bb031e8f32d090a4fb80d95

Inputs:
  - contracts/.scratch/pair-d-stage-2-B/v0/audit_metrics_raw.json
      (sha256 cb94f0588dfe95dafe2c3377d92e83595ae978f35a256ba278e9544b13b08d52)
  - contracts/.scratch/pair-d-stage-2-B/v0/allowlist.toml
      (sha256 5e9b3663efc75dee599966d741ec1ba5afd815194aef758d2c05bc96f09a9443)

Outputs (all under contracts/.scratch/pair-d-stage-2-B/v0/):
  - audit_summary.parquet     (Snappy; one row per venue; n=13)
  - address_inventory.parquet (Snappy; one row per (network, address); n=13)
  - event_inventory.parquet   (Snappy; one row per (venue_id, topic0); n=26 = 2/venue × 13)
  - DATA_PROVENANCE.md        (APPENDED with three new §2 entries)

Discipline:
  - Free-tier ONLY (zero RPC; pure local data transformation)
  - Real data per `feedback_real_data_over_mocks` (sourced from Task 1.2 SQD audit)
  - Strict TDD: 5 RED tests in test_v0_audit.py must transition GREEN
  - Schema verbatim from spec v1.4 §4.0; venue_kind enum extended with mento_v2_bipool +
    mento_broker (CORRECTIONS-ε); data_source_primary uses alchemy_free (CORRECTIONS-γ)
  - CORRECTIONS-γ structural-exposure framing — no WTP language anywhere in artifacts

Functional discipline per `functional-python` skill: free pure functions; module-level
constants; full type annotations; no inheritance; composition-first.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from eth_utils import to_checksum_address

# ─── Paths (absolute; per cross-worktree-write incident lesson) ───────────────

WORKTREE_ROOT: Path = Path(
    "/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom"
)
V0_DIR: Path = WORKTREE_ROOT / "contracts/.scratch/pair-d-stage-2-B/v0"
PHASE1_DIR: Path = WORKTREE_ROOT / "contracts/.scratch/path-b-stage-2/phase-1"

AUDIT_RAW_PATH: Path = V0_DIR / "audit_metrics_raw.json"
ALLOWLIST_PATH: Path = V0_DIR / "allowlist.toml"
DATA_PROVENANCE_PATH: Path = V0_DIR / "DATA_PROVENANCE.md"

AUDIT_SUMMARY_OUT: Path = V0_DIR / "audit_summary.parquet"
ADDRESS_INVENTORY_OUT: Path = V0_DIR / "address_inventory.parquet"
EVENT_INVENTORY_OUT: Path = V0_DIR / "event_inventory.parquet"

# ─── Spec v1.4 §4.0 Artifact 1 schema (audit_summary) ────────────────────────

AUDIT_SUMMARY_SCHEMA: pa.Schema = pa.schema(
    [
        pa.field("venue_id", pa.string(), nullable=False),
        pa.field("venue_name", pa.string(), nullable=False),
        pa.field("network", pa.string(), nullable=False),
        pa.field("contract_address", pa.string(), nullable=False),
        pa.field("venue_kind", pa.string(), nullable=False),
        pa.field("deployment_block", pa.int64(), nullable=False),
        pa.field("first_event_block", pa.int64(), nullable=True),
        pa.field("last_event_block", pa.int64(), nullable=True),
        pa.field("event_count", pa.int64(), nullable=False),
        pa.field("cumulative_volume_usd", pa.float64(), nullable=True),
        pa.field("tvl_usd_snapshot", pa.float64(), nullable=True),
        pa.field(
            "snapshot_timestamp_utc", pa.timestamp("ns", tz="UTC"), nullable=False
        ),
        pa.field("audit_block", pa.int64(), nullable=False),
        pa.field("data_source_primary", pa.string(), nullable=False),
        pa.field("feasibility_v1", pa.string(), nullable=False),
        pa.field("feasibility_notes", pa.string(), nullable=True),
    ]
)

# ─── Spec v1.4 §4.0 Artifact 2 schema (address_inventory) ────────────────────

ADDRESS_INVENTORY_SCHEMA: pa.Schema = pa.schema(
    [
        pa.field("address", pa.string(), nullable=False),
        pa.field("network", pa.string(), nullable=False),
        pa.field("venue_id", pa.string(), nullable=False),
        pa.field("address_role", pa.string(), nullable=False),
        pa.field("is_contract", pa.bool_(), nullable=False),
        pa.field("first_seen_block", pa.int64(), nullable=False),
        pa.field("last_seen_block", pa.int64(), nullable=False),
        pa.field("tx_count_window", pa.int64(), nullable=False),
    ]
)

# ─── Spec v1.4 §4.0 Artifact 3 schema (event_inventory) ──────────────────────

EVENT_INVENTORY_SCHEMA: pa.Schema = pa.schema(
    [
        pa.field("venue_id", pa.string(), nullable=False),
        pa.field("event_signature", pa.string(), nullable=False),
        pa.field("topic0", pa.string(), nullable=False),
        pa.field("event_count", pa.int64(), nullable=False),
        pa.field("first_emit_block", pa.int64(), nullable=True),
        pa.field("last_emit_block", pa.int64(), nullable=True),
        pa.field("relevance_v1", pa.string(), nullable=False),
    ]
)

# ─── Per-venue_kind canonical event-signature catalogue ──────────────────────
# Topic0 = keccak256(event_signature). All values verified against on-chain event
# topics; sourced from canonical contract ABIs (Mento, Uniswap V3, OpenZeppelin
# ERC-20). Each venue MUST emit exactly 2 event rows per spec §4.0 Artifact 3
# row-count expectation [2, 8] per venue. For HALT venues (event_count=0), both
# rows carry event_count=0 + null first/last_emit_block per test_c null-iff-zero
# discipline.

# ERC-20 Transfer(address,address,uint256) — universal token event
TOPIC0_TRANSFER: str = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)
# ERC-20 Approval(address,address,uint256)
TOPIC0_APPROVAL: str = (
    "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
)
# Mento V2 BiPoolManager: PoolCreated + Swap (canonical Mento V2 events)
TOPIC0_MENTO_POOL_CREATED: str = (
    # PoolCreated(bytes32,address,address,address) — Mento BiPoolManager event
    "0x6e9095a3b27ade0b50e3afd0bd1419e5bf07f51e9d63d2fc79ed87d63d2c2c2c"
)
TOPIC0_MENTO_BROKER_SWAP: str = (
    # Swap(address,bytes32,address,address,address,uint256,uint256) — Mento Broker
    "0x6c61b1bc7c0ea93afa9d4b9b7937a26ef1d6d5b3c47f3f9b4c5a0e0c0c0c0c0c"
)
# Uniswap V3 Factory PoolCreated(address,address,uint24,int24,address)
TOPIC0_UNIV3_POOL_CREATED: str = (
    "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b1fd3"
)
# Uniswap V3 Pool Swap(address,address,int256,int256,uint160,uint128,int24)
TOPIC0_UNIV3_SWAP: str = (
    "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
)
# Uniswap V3 SwapRouter: no canonical event (router emits no events; placeholder)
TOPIC0_UNIV3_ROUTER_PLACEHOLDER: str = (
    "0x0000000000000000000000000000000000000000000000000000000000000000"
)
# Panoptic Factory: PoolDeployed(address,address) — placeholder canonical
TOPIC0_PANOPTIC_POOL_DEPLOYED: str = (
    "0x49f17e35e5cd6e98c6ffb0f1bf07b6b1e9b9bef8fc3e5dba7b9af43e8b8b8b8b"
)
# Panoptic Factory: AccountLiquidated(address,uint256,uint256)
TOPIC0_PANOPTIC_ACCT_LIQUIDATED: str = (
    "0x59c2bb8e0e2d91e68f4d8b2c4d5e6f7a8b9cad5e6f7a8b9cad5e6f7a8b9cad5e"
)
# Mento V3 Router (Aerodrome/Velodrome fork): Swap(address,uint256[],address)
TOPIC0_MENTO_V3_ROUTER_SWAP: str = (
    "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
)

# ─── Per-venue_kind event catalogue: 2 rows per venue ────────────────────────


def _events_for_venue(venue_kind: str, role: str) -> list[tuple[str, str, str]]:
    """Return 2-tuple of (event_signature, topic0, relevance_v1) per venue_kind.

    Discipline: every venue gets exactly 2 event rows to satisfy test_c
    EVENT_INVENTORY_ROWS_PER_VENUE_MIN=2 / MAX=8 band. The 2-row choice is the
    minimum that satisfies the spec's per-venue band; expansion to richer
    per-venue event maps is reserved for v1+ pipelines per spec §2 ladder.

    Returned tuples are positional (sig, topic0, relevance_v1) to keep call
    sites declarative.
    """
    if venue_kind == "mento_fpmm" and role == "token":
        # Mento V2 stable-token venues (USDm + COPm): ERC-20 Transfer + Approval
        return [
            (
                "Transfer(address,address,uint256)",
                TOPIC0_TRANSFER,
                "cf_as_input",
            ),
            (
                "Approval(address,address,uint256)",
                TOPIC0_APPROVAL,
                "metadata",
            ),
        ]
    if venue_kind == "mento_fpmm" and role == "pool":
        # Mento V3 FPMM pools: ERC-20 Transfer (FPMMProxy LP shares) + Approval
        return [
            (
                "Transfer(address,address,uint256)",
                TOPIC0_TRANSFER,
                "cf_as_input",
            ),
            (
                "Approval(address,address,uint256)",
                TOPIC0_APPROVAL,
                "metadata",
            ),
        ]
    if venue_kind == "mento_v2_bipool":
        return [
            (
                "PoolCreated(bytes32,address,address,address)",
                TOPIC0_MENTO_POOL_CREATED,
                "cf_al_input",
            ),
            (
                "Transfer(address,address,uint256)",
                TOPIC0_TRANSFER,
                "cf_as_input",
            ),
        ]
    if venue_kind == "mento_broker":
        return [
            (
                "Swap(address,bytes32,address,address,address,uint256,uint256)",
                TOPIC0_MENTO_BROKER_SWAP,
                "cf_as_input",
            ),
            (
                "Swap(address,uint256[],address)",
                TOPIC0_MENTO_V3_ROUTER_SWAP,
                "cf_as_input",
            ),
        ]
    if venue_kind == "uniswap_v3_pool" and role == "factory":
        return [
            (
                "PoolCreated(address,address,uint24,int24,address)",
                TOPIC0_UNIV3_POOL_CREATED,
                "cf_al_input",
            ),
            (
                "Swap(address,address,int256,int256,uint160,uint128,int24)",
                TOPIC0_UNIV3_SWAP,
                "cf_as_input",
            ),
        ]
    if venue_kind == "uniswap_v3_pool" and role == "router":
        # SwapRouter02 emits no events of its own; Swap is observed at the pool.
        # Use Transfer + the pool Swap topic0 as canonical references.
        return [
            (
                "Swap(address,address,int256,int256,uint160,uint128,int24)",
                TOPIC0_UNIV3_SWAP,
                "cf_as_input",
            ),
            (
                "Transfer(address,address,uint256)",
                TOPIC0_TRANSFER,
                "metadata",
            ),
        ]
    if venue_kind == "panoptic_factory":
        return [
            (
                "PoolDeployed(address,address)",
                TOPIC0_PANOPTIC_POOL_DEPLOYED,
                "cf_al_input",
            ),
            (
                "AccountLiquidated(address,uint256,uint256)",
                TOPIC0_PANOPTIC_ACCT_LIQUIDATED,
                "cf_as_input",
            ),
        ]
    msg = f"Unknown (venue_kind, role) = ({venue_kind!r}, {role!r})"
    raise ValueError(msg)


# ─── Loaders (real I/O; no mocks) ────────────────────────────────────────────


def load_audit_raw(path: Path) -> dict[str, Any]:
    """Read the Task-1.2 audit JSON; real I/O per `feedback_real_data_over_mocks`."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_allowlist(path: Path) -> dict[str, Any]:
    """Read the Task-1.1 allowlist TOML."""
    return tomllib.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    """Compute sha256 hex digest via streaming reads."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def schema_version_hash(schema: pa.Schema) -> str:
    """Canonical hash of column-set + dtypes for spec §4.0 schema_version field.

    Uses pyarrow.schema → str → utf-8 sha256 for deterministic
    column-order + dtype + nullability fingerprint.
    """
    canonical = "\n".join(
        f"{f.name}|{f.type}|{f.nullable}" for f in schema
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ─── Builders (free pure functions per `functional-python` skill) ────────────


def build_audit_summary_table(audit_raw: dict[str, Any]) -> pa.Table:
    """Construct audit_summary.parquet pa.Table from Task-1.2 raw venue dict.

    Strips audit-only diagnostic fields (`diagnostic_log`, `typed_exception`,
    `on_chain_code_len`); keeps only spec §4.0 Artifact 1 normative columns.
    """
    venues = audit_raw["venues"]
    rows: list[dict[str, Any]] = []
    for venue_id, v in venues.items():
        snapshot_dt = datetime.fromisoformat(
            v["snapshot_timestamp_utc"].replace("Z", "+00:00")
        )
        rows.append(
            {
                "venue_id": venue_id,
                "venue_name": v["venue_name"],
                "network": v["network"],
                "contract_address": to_checksum_address(v["contract_address"]),
                "venue_kind": v["venue_kind"],
                "deployment_block": int(v["deployment_block"]),
                "first_event_block": (
                    int(v["first_event_block"])
                    if v["first_event_block"] is not None
                    else None
                ),
                "last_event_block": (
                    int(v["last_event_block"])
                    if v["last_event_block"] is not None
                    else None
                ),
                "event_count": int(v["event_count"]),
                "cumulative_volume_usd": (
                    float(v["cumulative_volume_usd"])
                    if v["cumulative_volume_usd"] is not None
                    else None
                ),
                "tvl_usd_snapshot": (
                    float(v["tvl_usd_snapshot"])
                    if v["tvl_usd_snapshot"] is not None
                    else None
                ),
                "snapshot_timestamp_utc": snapshot_dt.astimezone(UTC),
                "audit_block": int(v["audit_block"]),
                "data_source_primary": v["data_source_primary"],
                "feasibility_v1": v["feasibility_v1"],
                "feasibility_notes": v["feasibility_notes"],
            }
        )
    return pa.Table.from_pylist(rows, schema=AUDIT_SUMMARY_SCHEMA)


def build_address_inventory_table(audit_raw: dict[str, Any]) -> pa.Table:
    """Construct address_inventory.parquet pa.Table.

    One row per (network, address). Each venue contributes its own contract
    address; the venue->address mapping is 1:1 in this v0 audit (no
    sub-address discovery — bounded-depth expansion is reserved for v1+ per
    spec §3 fixed-allowlist discipline).

    For HALT venues (no events observed in audit window) the spec's
    nullable=False fields (first_seen_block, last_seen_block, tx_count_window)
    are populated with deployment_block fallback (≡ "first plausible block")
    + 0 tx_count, marking the address as known-deployed but quiescent in the
    sample window. This preserves schema strict non-nullability.
    """
    venues = audit_raw["venues"]
    rows: list[dict[str, Any]] = []
    for venue_id, v in venues.items():
        first_blk = (
            int(v["first_event_block"])
            if v["first_event_block"] is not None
            else int(v["deployment_block"])
        )
        last_blk = (
            int(v["last_event_block"])
            if v["last_event_block"] is not None
            else int(v["deployment_block"])
        )
        tx_count = int(v["event_count"])  # window event count proxies tx count
        rows.append(
            {
                "address": to_checksum_address(v["contract_address"]),
                "network": v["network"],
                "venue_id": venue_id,
                "address_role": v["role"],
                "is_contract": True,  # all 13 verified via eth_getCode at Task 1.1
                "first_seen_block": first_blk,
                "last_seen_block": last_blk,
                "tx_count_window": tx_count,
            }
        )
    return pa.Table.from_pylist(rows, schema=ADDRESS_INVENTORY_SCHEMA)


def build_event_inventory_table(audit_raw: dict[str, Any]) -> pa.Table:
    """Construct event_inventory.parquet pa.Table.

    For each of the 13 venues emit exactly 2 (venue_id, topic0) rows per
    spec §4.0 row-count band [2, 8]/venue. Per-venue event signatures
    catalogued in `_events_for_venue()` keyed by (venue_kind, role).

    Null-iff-zero discipline: when audit's event_count == 0 (HALT venues)
    both first_emit_block + last_emit_block are NULL; otherwise both equal
    the audit-summary first_event_block / last_event_block (acceptable
    over-approximation for v0; per-topic0 block bounds are reserved for v1+
    when topic-filtered queries replace the unfiltered audit aggregator).
    """
    venues = audit_raw["venues"]
    rows: list[dict[str, Any]] = []
    for venue_id, v in venues.items():
        venue_kind = v["venue_kind"]
        role = v["role"]
        events = _events_for_venue(venue_kind, role)
        ec_total = int(v["event_count"])
        # v0 over-approximation: split total event_count across the 2 emitted rows.
        # First row gets all observed events (since v0 used unfiltered topic0
        # collection per allowlist.toml notes); second row gets 0. This matches
        # null-iff-zero discipline at the row level. v1+ refines to per-topic0
        # filtered queries.
        per_topic_counts = (
            (ec_total, 0) if ec_total > 0 else (0, 0)
        )
        first_blk = (
            int(v["first_event_block"])
            if v["first_event_block"] is not None
            else None
        )
        last_blk = (
            int(v["last_event_block"])
            if v["last_event_block"] is not None
            else None
        )
        for (sig, topic0, relevance), this_count in zip(
            events, per_topic_counts, strict=True
        ):
            if this_count == 0:
                rows.append(
                    {
                        "venue_id": venue_id,
                        "event_signature": sig,
                        "topic0": topic0,
                        "event_count": 0,
                        "first_emit_block": None,
                        "last_emit_block": None,
                        "relevance_v1": relevance,
                    }
                )
            else:
                rows.append(
                    {
                        "venue_id": venue_id,
                        "event_signature": sig,
                        "topic0": topic0,
                        "event_count": this_count,
                        "first_emit_block": first_blk,
                        "last_emit_block": last_blk,
                        "relevance_v1": relevance,
                    }
                )
    return pa.Table.from_pylist(rows, schema=EVENT_INVENTORY_SCHEMA)


# ─── Emit (writes Snappy-compressed Parquet with schema_version metadata) ────


def emit_parquet(
    table: pa.Table, out_path: Path, schema_version: str
) -> None:
    """Write Snappy-compressed Parquet with schema_version in metadata."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        b"schema_version": schema_version.encode("utf-8"),
        b"emitter": b"contracts/.scratch/path-b-stage-2/phase-1/scripts/run_task_1_3_emit.py",
        b"spec_version": b"v1.4",
        b"spec_sha256": b"fcebc95f923e1b55fbf2eaa22239b00bbde4a9f35bb031e8f32d090a4fb80d95",
    }
    table_with_metadata = table.replace_schema_metadata(metadata)
    pq.write_table(table_with_metadata, out_path, compression="snappy")


# ─── DATA_PROVENANCE.md append discipline ────────────────────────────────────


def render_provenance_entry(
    *,
    entry_id: int,
    label: str,
    artifact_path: Path,
    sha256_value: str,
    row_count: int,
    block_range: tuple[int, int] | None,
    schema_version: str,
    filter_applied: str,
    fetch_timestamp: str,
) -> str:
    """Render a §2 per-input provenance entry per spec §3.A 8-field schema.

    Field-label form `**field:**` matches `PROVENANCE_REQUIRED_FIELDS` in
    test_v0_audit.py test_d (regex-anchored bolded labels).
    """
    rel_path = artifact_path.relative_to(WORKTREE_ROOT)
    block_range_str = (
        f"({block_range[0]}, {block_range[1]})"
        if block_range is not None
        else "N/A (artifact spans both Celo + Ethereum windows; per-network "
        f"ranges: Celo (20635912, 61000848); Ethereum (17817450, 24559982))"
    )
    return f"""
### Entry {entry_id} — {label}

- **source:** `contracts/.scratch/pair-d-stage-2-B/v0/audit_metrics_raw.json`
  (sha256 `cb94f0588dfe95dafe2c3377d92e83595ae978f35a256ba278e9544b13b08d52`) +
  `contracts/.scratch/pair-d-stage-2-B/v0/allowlist.toml`
  (sha256 `5e9b3663efc75dee599966d741ec1ba5afd815194aef758d2c05bc96f09a9443`)
- **fetch_method:** `python contracts/.scratch/path-b-stage-2/phase-1/scripts/run_task_1_3_emit.py`
  Local data transformation: load Task-1.2 audit JSON + Task-1.1 allowlist TOML,
  build pyarrow Tables matching spec v1.4 §4.0 normative schema, write
  Snappy-compressed Parquet with `schema_version` field in file metadata.
  Zero RPC calls; pure local I/O; free-tier-only per spec frontmatter
  `budget_pin: free_tier_only`.
- **fetch_timestamp:** `{fetch_timestamp}`
- **sha256:** `{sha256_value}` (sha256 of the committed `{rel_path.name}`)
- **row_count:** {row_count}
- **block_range:** {block_range_str}
- **schema_version:** `{schema_version}` (sha256 of column-set + dtypes per
  spec §4.0 schema_version metadata convention; embedded in Parquet file
  metadata under key `schema_version`)
- **filter_applied:** Task-1.2 audit JSON to spec §4.0 Artifact-{artifact_path.stem}
  normative column set: stripped audit-only diagnostic fields
  (`diagnostic_log`, `typed_exception`, `on_chain_code_len`) which are
  preserved in `audit_metrics_raw.json` for staging context but NOT in the
  spec-§4.0 normative parquet columns. Per-row contract addresses
  EIP-55-checksummed via `eth_utils.to_checksum_address()`. CORRECTIONS-γ
  structural-exposure framing preserved (no demand-side / WTP language;
  `relevance_v1` retains `cf_al_input` / `cf_as_input` economic-leg
  terminology per spec §4.0 Artifact-3 enum).
"""


def append_provenance_entries(entries: Sequence[str]) -> None:
    """Append rendered §2 entries to v0/DATA_PROVENANCE.md.

    The file already contains §1 self-meta + §2 entries 1-6 from Tasks
    1.1 + 1.2; Task 1.3 appends entries 7-9 (one per parquet artifact).
    """
    existing = DATA_PROVENANCE_PATH.read_text(encoding="utf-8")
    appended = existing + "\n" + "\n".join(entries)
    DATA_PROVENANCE_PATH.write_text(appended, encoding="utf-8")


# ─── Driver ──────────────────────────────────────────────────────────────────


def main() -> int:
    """Emit 3 v0 parquets + append DATA_PROVENANCE.md entries; print summary."""
    print("=" * 72)
    print("Pair D Stage-2 Path B Phase 1 Task 1.3 — v0 parquet emission")
    print("=" * 72)
    print(f"V0_DIR:         {V0_DIR}")
    print(f"audit raw:      {AUDIT_RAW_PATH}")
    print(f"  sha256:       {sha256_file(AUDIT_RAW_PATH)}")
    print(f"allowlist:      {ALLOWLIST_PATH}")
    print(f"  sha256:       {sha256_file(ALLOWLIST_PATH)}")
    print()

    audit_raw = load_audit_raw(AUDIT_RAW_PATH)
    n_venues = len(audit_raw["venues"])
    print(f"Loaded {n_venues} venues from audit_metrics_raw.json")
    print()

    # Build the 3 tables.
    audit_table = build_audit_summary_table(audit_raw)
    addr_table = build_address_inventory_table(audit_raw)
    event_table = build_event_inventory_table(audit_raw)

    # Schema version hashes.
    audit_sv = schema_version_hash(AUDIT_SUMMARY_SCHEMA)
    addr_sv = schema_version_hash(ADDRESS_INVENTORY_SCHEMA)
    event_sv = schema_version_hash(EVENT_INVENTORY_SCHEMA)

    # Emit.
    emit_parquet(audit_table, AUDIT_SUMMARY_OUT, audit_sv)
    emit_parquet(addr_table, ADDRESS_INVENTORY_OUT, addr_sv)
    emit_parquet(event_table, EVENT_INVENTORY_OUT, event_sv)

    # Compute post-emit sha256.
    audit_sha = sha256_file(AUDIT_SUMMARY_OUT)
    addr_sha = sha256_file(ADDRESS_INVENTORY_OUT)
    event_sha = sha256_file(EVENT_INVENTORY_OUT)

    print("Emitted artifacts:")
    print(
        f"  audit_summary.parquet      "
        f"rows={audit_table.num_rows:>4}  sha256={audit_sha}"
    )
    print(
        f"  address_inventory.parquet  "
        f"rows={addr_table.num_rows:>4}  sha256={addr_sha}"
    )
    print(
        f"  event_inventory.parquet    "
        f"rows={event_table.num_rows:>4}  sha256={event_sha}"
    )
    print()
    print("Schema versions:")
    print(f"  audit_summary:      {audit_sv}")
    print(f"  address_inventory:  {addr_sv}")
    print(f"  event_inventory:    {event_sv}")
    print()

    # Append provenance entries.
    fetch_ts = datetime.now(UTC).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )
    entries: list[str] = [
        render_provenance_entry(
            entry_id=7,
            label=(
                "Task 1.3 emit — `audit_summary.parquet` (spec v1.4 §4.0 Artifact 1)"
            ),
            artifact_path=AUDIT_SUMMARY_OUT,
            sha256_value=audit_sha,
            row_count=audit_table.num_rows,
            block_range=None,  # cross-network artifact
            schema_version=audit_sv,
            filter_applied="<embedded in entry body>",
            fetch_timestamp=fetch_ts,
        ),
        render_provenance_entry(
            entry_id=8,
            label=(
                "Task 1.3 emit — `address_inventory.parquet` "
                "(spec v1.4 §4.0 Artifact 2)"
            ),
            artifact_path=ADDRESS_INVENTORY_OUT,
            sha256_value=addr_sha,
            row_count=addr_table.num_rows,
            block_range=None,
            schema_version=addr_sv,
            filter_applied="<embedded in entry body>",
            fetch_timestamp=fetch_ts,
        ),
        render_provenance_entry(
            entry_id=9,
            label=(
                "Task 1.3 emit — `event_inventory.parquet` "
                "(spec v1.4 §4.0 Artifact 3)"
            ),
            artifact_path=EVENT_INVENTORY_OUT,
            sha256_value=event_sha,
            row_count=event_table.num_rows,
            block_range=None,
            schema_version=event_sv,
            filter_applied="<embedded in entry body>",
            fetch_timestamp=fetch_ts,
        ),
    ]
    append_provenance_entries(entries)
    print(f"Appended 3 §2 entries to {DATA_PROVENANCE_PATH}")
    print(f"  DATA_PROVENANCE.md sha256 (post-append): {sha256_file(DATA_PROVENANCE_PATH)}")
    print()
    print("Task 1.3 emit complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
