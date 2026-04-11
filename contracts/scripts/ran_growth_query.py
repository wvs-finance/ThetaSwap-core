"""CLI query interface for the RAN accumulator sample database.

Usage:
    python -m scripts.ran_growth_query --pool usdc-weth --block 22972937 --db path/to/db

Zero network dependencies — reads only from a local DuckDB file.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Final, Optional

import duckdb

from scripts.ran_utils import POOL_REGISTRY


# ── Result types ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ExactMatch:
    """An exact block match result."""

    block_number: int
    global_growth: str
    pool_id: str


@dataclass(frozen=True, slots=True)
class NearestLowerMatch:
    """A nearest-lower block match result."""

    requested_block: int
    sampled_block: int
    global_growth: str
    pool_id: str


QueryResult = ExactMatch | NearestLowerMatch


# ── Pure functions ───────────────────────────────────────────────────────────


def format_exact(match: ExactMatch) -> str:
    """Serialize an exact match to JSON."""
    return json.dumps(
        {
            "blockNumber": match.block_number,
            "globalGrowth": match.global_growth,
            "poolId": match.pool_id,
            "exact": True,
        }
    )


def format_nearest_lower(match: NearestLowerMatch) -> str:
    """Serialize a nearest-lower match to JSON."""
    return json.dumps(
        {
            "blockNumber": match.requested_block,
            "globalGrowth": match.global_growth,
            "poolId": match.pool_id,
            "exact": False,
            "sampledBlock": match.sampled_block,
            "blockDelta": match.requested_block - match.sampled_block,
        }
    )


def format_result(result: QueryResult) -> str:
    """Format a query result as JSON."""
    if isinstance(result, ExactMatch):
        return format_exact(result)
    return format_nearest_lower(result)


def validate_pool(pool_name: str) -> Optional[str]:
    """Return an error message if pool_name is not in the registry, else None."""
    if pool_name not in POOL_REGISTRY:
        valid: str = ", ".join(sorted(POOL_REGISTRY.keys()))
        return f"Unknown pool '{pool_name}'. Valid pools: {valid}"
    return None


def query_block(
    conn: duckdb.DuckDBPyConnection,
    pool_id: str,
    block: int,
) -> QueryResult | str:
    """Query for a block's growth data.

    Returns a QueryResult on success, or an error string on failure.
    """
    # Exact match
    row = conn.execute(
        "SELECT global_growth FROM accumulator_samples "
        "WHERE pool_id = ? AND block_number = ?",
        [pool_id, block],
    ).fetchone()
    if row is not None:
        return ExactMatch(
            block_number=block,
            global_growth=row[0],
            pool_id=pool_id,
        )

    # Nearest lower
    row = conn.execute(
        "SELECT block_number, global_growth FROM accumulator_samples "
        "WHERE pool_id = ? AND block_number < ? "
        "ORDER BY block_number DESC LIMIT 1",
        [pool_id, block],
    ).fetchone()
    if row is not None:
        return NearestLowerMatch(
            requested_block=block,
            sampled_block=row[0],
            global_growth=row[1],
            pool_id=pool_id,
        )

    # Check if there are ANY rows for this pool
    count_row = conn.execute(
        "SELECT COUNT(*) FROM accumulator_samples WHERE pool_id = ?",
        [pool_id],
    ).fetchone()
    count: int = count_row[0] if count_row is not None else 0

    if count == 0:
        return f"Pool '{pool_id}' has no data fetched yet."

    # Block is before earliest sample
    earliest_row = conn.execute(
        "SELECT MIN(block_number) FROM accumulator_samples WHERE pool_id = ?",
        [pool_id],
    ).fetchone()
    earliest: int = earliest_row[0] if earliest_row is not None else 0
    return (
        f"Requested block {block} is before earliest sample at block {earliest}"
    )


# ── CLI ──────────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Query RAN accumulator samples from a local DuckDB."
    )
    parser.add_argument("--pool", required=True, help="Pool name (e.g. usdc-weth)")
    parser.add_argument("--block", required=True, type=int, help="Block number to query")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the query CLI."""
    args = parse_args(argv)

    # Validate pool name
    pool_error = validate_pool(args.pool)
    if pool_error is not None:
        print(pool_error, file=sys.stderr)
        return 1

    # Validate block number is non-negative
    if args.block < 0:
        print("block must be non-negative", file=sys.stderr)
        return 1

    pool_config = POOL_REGISTRY[args.pool]
    try:
        conn = duckdb.connect(args.db, read_only=True)
    except duckdb.IOException as exc:
        print(f"Cannot open database '{args.db}': {exc}", file=sys.stderr)
        return 1
    try:
        result = query_block(conn, pool_config.pool_id, args.block)
    finally:
        conn.close()

    if isinstance(result, str):
        print(result, file=sys.stderr)
        return 1

    print(format_result(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
