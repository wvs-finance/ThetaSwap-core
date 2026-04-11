"""RAN FFI query script for Solidity fork tests.

Outputs ABI-encoded hex to stdout for consumption by Forge vm.ffi().
Two subcommands:
  len  — row count as abi.encode(uint256)
  row  — single row as abi.encode(uint256, uint256, bytes32)

Zero network dependency — reads only from local DuckDB.
"""
from __future__ import annotations

import argparse
import sys
from typing import Final

import duckdb
import eth_abi

_LEN_SQL: Final[str] = (
    "SELECT count(*) FROM accumulator_samples WHERE pool_id = ?"
)

_ROW_SQL: Final[str] = (
    "SELECT block_number, block_timestamp, global_growth "
    "FROM accumulator_samples WHERE pool_id = ? "
    "ORDER BY block_number LIMIT 1 OFFSET ?"
)


def _normalize_pool_id(raw: str) -> str:
    """Normalize pool ID to 0x-prefixed lowercase hex."""
    if raw.startswith("0x") or raw.startswith("0X"):
        return raw.lower()
    return "0x" + raw.lower()


def _open_db(path: str) -> duckdb.DuckDBPyConnection:
    """Open DuckDB read-only, exit 1 on failure."""
    try:
        return duckdb.connect(path, read_only=True)
    except Exception as exc:
        print(f"error: cannot open database: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_len(args: argparse.Namespace) -> None:
    """Handle the 'len' subcommand."""
    pool_id = _normalize_pool_id(args.pool)
    conn = _open_db(args.db)
    try:
        row = conn.execute(_LEN_SQL, [pool_id]).fetchone()
        if row is None:
            print("unexpected: query returned no result", file=sys.stderr)
            sys.exit(1)
        count: int = row[0]
        if count == 0:
            print("error: pool not found", file=sys.stderr)
            sys.exit(1)
        encoded = eth_abi.encode(["uint256"], [count])
        print("0x" + encoded.hex())
    finally:
        conn.close()


def _cmd_row(args: argparse.Namespace) -> None:
    """Handle the 'row' subcommand."""
    pool_id = _normalize_pool_id(args.pool)
    idx: int = args.idx
    conn = _open_db(args.db)
    try:
        # Check pool exists and get count for bounds check
        count_row = conn.execute(_LEN_SQL, [pool_id]).fetchone()
        if count_row is None:
            print("unexpected: query returned no result", file=sys.stderr)
            sys.exit(1)
        count: int = count_row[0]
        if count == 0:
            print("error: pool not found", file=sys.stderr)
            sys.exit(1)
        if idx >= count:
            print(
                f"error: index {idx} out of range [0, {count - 1}]",
                file=sys.stderr,
            )
            sys.exit(1)
        row = conn.execute(_ROW_SQL, [pool_id, idx]).fetchone()
        if row is None:
            print("unexpected: query returned no result", file=sys.stderr)
            sys.exit(1)
        block_number: int = row[0]
        block_timestamp = row[1]
        global_growth_hex: str = row[2]
        if block_timestamp is None:
            print(
                "error: run pipeline to backfill timestamps",
                file=sys.stderr,
            )
            sys.exit(1)
        growth_bytes: bytes = bytes.fromhex(global_growth_hex[2:])
        encoded = eth_abi.encode(
            ["uint256", "uint256", "bytes32"],
            [block_number, int(block_timestamp), growth_bytes],
        )
        print("0x" + encoded.hex())
    finally:
        conn.close()


def main() -> None:
    """Entry point for ran_ffi CLI."""
    parser = argparse.ArgumentParser(
        description="RAN FFI query — ABI-encoded output for Forge vm.ffi()",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # len subcommand
    len_parser = subparsers.add_parser("len", help="Row count for a pool")
    len_parser.add_argument("--pool", required=True, help="Pool ID (hex)")
    len_parser.add_argument("--db", required=True, help="DuckDB file path")

    # row subcommand
    row_parser = subparsers.add_parser("row", help="Single row by index")
    row_parser.add_argument("--pool", required=True, help="Pool ID (hex)")
    row_parser.add_argument("--idx", required=True, type=int, help="Row index")
    row_parser.add_argument("--db", required=True, help="DuckDB file path")

    args = parser.parse_args()
    if args.command == "len":
        _cmd_len(args)
    elif args.command == "row":
        _cmd_row(args)


if __name__ == "__main__":
    main()
