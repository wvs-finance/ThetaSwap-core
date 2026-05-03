"""v0 data-coverage audit — STUB module (Phase 1 Task 1.1 TDD scaffold).

This module declares the API surface that Phase 1 Tasks 1.2 / 1.3 / 1.4 will
implement under Data-Engineer dispatch discipline. Every function raises
NotImplementedError so that Task 1.1's failing-test scaffold
(test_v0_audit.py) FAILS as required by `feedback_strict_tdd`.

API contract derived from spec §4.0 v0 Output Schema (normative;
resolves BLOCK-B1) and §3.A Provenance Discipline (normative;
resolves BLOCK-B2). See:

  contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md
    v1.3 sha256 4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea

Spec §2 v0 exit (verbatim):
  "feasibility yes/no per data source, with sha-pinned snapshot of pool
  addresses, cumulative metrics, and block-range bounds. Frontmatter
  on_chain_pins block frozen. v0 output artifacts conform to §4.0
  normative schema."

Three artifact-generation entry points correspond to spec §4.0's three
parquet artifacts:

- `audit_summary_generate(...)` → emits `audit_summary.parquet`
  (one row per audited venue; 6-12 rows expected; primary key venue_id;
  feasibility_v1 ∈ {pass, marginal, halt}; data_source_primary ∈
  {sqd_network, alchemy_free, dune, the_graph, celoscan, etherscan}
  per v1.2.1 free-tier alignment).

- `address_inventory_generate(...)` → emits `address_inventory.parquet`
  (one row per unique on-chain address; 10-200 rows expected; FK to
  audit_summary.venue_id; PK (network, address)).

- `event_inventory_generate(...)` → emits `event_inventory.parquet`
  (one row per (venue, event_topic) pair; 2-8 rows per venue;
  PK (venue_id, topic0); relevance_v1 ∈ {cf_al_input, cf_as_input,
  oracle_input, metadata, unused}).

All implementations land in Phase 1 Tasks 1.2 (per-venue audit, parallel
within rate-limit budget per spec §5.A) + 1.3 (parquet emission per §4.0)
+ 1.4 (TDD test suite for emitted artifacts). This stub exists only to
make the test scaffold collectible and failing.

Provenance mirror per spec §3.A: every parquet emit MUST be accompanied
by a `DATA_PROVENANCE.md` co-located in the v0/ output directory with the
8-field schema populated per input. The TDD test test_d_data_provenance_mirror
enforces this; the implementation entry points below are responsible for
emitting both the parquet and the provenance entry atomically.

CORRECTIONS-γ structural-exposure framing (per spec v1.3 change log):
this module audits *structural-exposure cash-flow geometry* of on-chain
venues — NOT behavioral demand or willingness-to-pay. The "demand-side"
language is preserved only as economic-leg terminology (a_l vs a_s legs).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def audit_summary_generate(
    output_path: Path | str,
    *,
    network_config_path: Path | str,
    venue_allowlist: list[dict[str, Any]],
    audit_block_celo: int,
    audit_block_ethereum: int,
) -> Path:
    """Generate `audit_summary.parquet` per spec §4.0 Artifact 1.

    Per spec §4.0 row-count expectation: 6-12 rows. Per spec §4.0 column
    schema: 14 columns; 5 nullable; primary key `venue_id` UNIQUE within
    file; `feasibility_v1` enum ∈ {pass, marginal, halt}; `feasibility_notes`
    REQUIRED if feasibility_v1 ∈ {marginal, halt}; `data_source_primary`
    enum ∈ {sqd_network, alchemy_free, dune, the_graph, celoscan, etherscan}.

    Implementation must:
    - read the fixed allowlist from spec frontmatter on_chain_pins +
      Mento V3 deployment manifest (per FLAG-B7 fixed-allowlist discipline);
    - per-venue audit via SQD Network gateway (primary) with Alchemy-free /
      public-RPC fallbacks per spec §5;
    - emit parquet at `output_path` with schema_version metadata field;
    - co-emit DATA_PROVENANCE.md entry per spec §3.A 8-field schema;
    - HALT-and-surface typed exception `Stage2PathBAuditScopeAnomaly`
      if final row count is <4 or >20.

    Returns the absolute path of the emitted parquet.
    """
    raise NotImplementedError(
        "Task 1.1 stub: audit_summary_generate() is implemented in Phase 1 "
        "Tasks 1.2 + 1.3 (Data Engineer + parquet emission). Spec §4.0 "
        "Artifact 1 schema must be honored."
    )


def address_inventory_generate(
    output_path: Path | str,
    *,
    audit_summary_path: Path | str,
    network_config_path: Path | str,
) -> Path:
    """Generate `address_inventory.parquet` per spec §4.0 Artifact 2.

    Per spec §4.0 row-count expectation: 10-200 rows. Per spec §4.0
    column schema: 8 columns; 0 nullable; primary key `(network, address)`
    UNIQUE within file; foreign key `(venue_id)` references
    `audit_summary.venue_id`; `address_role` enum ∈ {router, factory,
    pool, token, fee_collector, merchant, user_eoa, mev_bot, other}.

    Implementation must:
    - load `audit_summary.parquet` and dereference each venue_id's
      contract_address as a starting node for address-graph expansion;
    - perform bounded-depth traversal of `eth_getCode`-confirmed contract
      neighbors PLUS top-N counterparty EOAs per spec §3 fixed-allowlist
      discipline (no unbounded discovery);
    - HALT-and-surface typed exception (HALT review per spec §6) if
      final row count is <5.

    Returns the absolute path of the emitted parquet.
    """
    raise NotImplementedError(
        "Task 1.1 stub: address_inventory_generate() is implemented in "
        "Phase 1 Tasks 1.2 + 1.3. Spec §4.0 Artifact 2 schema must be "
        "honored; FK referential integrity to audit_summary.venue_id is "
        "load-bearing."
    )


def event_inventory_generate(
    output_path: Path | str,
    *,
    audit_summary_path: Path | str,
    network_config_path: Path | str,
) -> Path:
    """Generate `event_inventory.parquet` per spec §4.0 Artifact 3.

    Per spec §4.0 row-count expectation: 2-8 rows PER VENUE. Per spec
    §4.0 column schema: 7 columns; 2 nullable (`first_emit_block`,
    `last_emit_block` — null iff `event_count == 0`); primary key
    `(venue_id, topic0)` UNIQUE within file; `relevance_v1` enum ∈
    {cf_al_input, cf_as_input, oracle_input, metadata, unused}.

    Implementation must:
    - load `audit_summary.parquet` and enumerate canonical event
      signatures per `venue_kind` (e.g., Mento_FPMM emits Swap +
      LiquidityAdded + LiquidityRemoved; Uniswap V3 pools emit Swap +
      Mint + Burn + Collect; Panoptic factory emits PoolCreated);
    - per-(venue, topic0) tuple, count event emissions in audit window
      via SQD Network gateway primary with rate-limited Alchemy
      fallback per spec §5.A burst budget;
    - emit null first_emit_block / last_emit_block iff event_count == 0;
      otherwise emit the actual block bounds.

    Returns the absolute path of the emitted parquet.
    """
    raise NotImplementedError(
        "Task 1.1 stub: event_inventory_generate() is implemented in "
        "Phase 1 Tasks 1.2 + 1.3. Spec §4.0 Artifact 3 schema must be "
        "honored; PK (venue_id, topic0) uniqueness + null-iff-zero-count "
        "discipline on first_emit_block/last_emit_block is load-bearing."
    )
