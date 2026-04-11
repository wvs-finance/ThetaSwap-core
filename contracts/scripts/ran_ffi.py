"""RAN FFI query script for Solidity fork tests.

Outputs ABI-encoded hex to stdout for consumption by Forge vm.ffi().
Subcommands:
  len       — row count as abi.encode(uint256)
  row       — single row as abi.encode(uint256, uint256, bytes32)
  row-by-ts — single row by timestamp as abi.encode(uint256, uint256, bytes32)
  range     — row slice as abi.encode(uint256, uint256[], uint256[], bytes32[])
  min       — minimum block row as abi.encode(uint256, uint256, bytes32)
  max       — maximum block row as abi.encode(uint256, uint256, bytes32)

Zero network dependency — reads only from local DuckDB.
"""
from __future__ import annotations

import argparse
import sys

import duckdb
import eth_abi

from scripts.ran_data_api import (
    QueryError,
    Row,
    dataset_len,
    get_by_timestamp,
    get_max,
    get_min,
    get_range,
    get_row,
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


def _encode_row(row: Row) -> str:
    """ABI-encode a single Row as (uint256, uint256, bytes32), returning 0x hex."""
    growth_bytes: bytes = bytes.fromhex(row.global_growth[2:])
    encoded = eth_abi.encode(
        ["uint256", "uint256", "bytes32"],
        [row.block_number, row.block_timestamp, growth_bytes],
    )
    return "0x" + encoded.hex()


def _cmd_len(args: argparse.Namespace) -> None:
    """Handle the 'len' subcommand."""
    pool_id = _normalize_pool_id(args.pool)
    conn = _open_db(args.db)
    try:
        count: int = dataset_len(conn, pool_id)
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
        # Preserve backward-compatible error messages
        count: int = dataset_len(conn, pool_id)
        if count == 0:
            print("error: pool not found", file=sys.stderr)
            sys.exit(1)
        if idx >= count:
            print(
                f"error: index {idx} out of range [0, {count - 1}]",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            row = get_row(conn, pool_id, idx)
        except QueryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(_encode_row(row))
    finally:
        conn.close()


def _cmd_row_by_ts(args: argparse.Namespace) -> None:
    """Handle the 'row-by-ts' subcommand."""
    pool_id = _normalize_pool_id(args.pool)
    ts: int = args.ts
    exact: bool = not args.nearest
    conn = _open_db(args.db)
    try:
        try:
            row = get_by_timestamp(conn, pool_id, ts, exact=exact)
        except QueryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(_encode_row(row))
    finally:
        conn.close()


def _cmd_range(args: argparse.Namespace) -> None:
    """Handle the 'range' subcommand."""
    pool_id = _normalize_pool_id(args.pool)
    from_idx: int = args.from_idx
    to_idx: int = args.to
    conn = _open_db(args.db)
    try:
        try:
            rows = get_range(conn, pool_id, from_idx, to_idx)
        except QueryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        growth_bytes_list = [bytes.fromhex(r.global_growth[2:]) for r in rows]
        encoded = eth_abi.encode(
            ["uint256", "uint256[]", "uint256[]", "bytes32[]"],
            [
                len(rows),
                [r.block_number for r in rows],
                [r.block_timestamp for r in rows],
                growth_bytes_list,
            ],
        )
        print("0x" + encoded.hex())
    finally:
        conn.close()


def _cmd_min(args: argparse.Namespace) -> None:
    """Handle the 'min' subcommand."""
    pool_id = _normalize_pool_id(args.pool)
    conn = _open_db(args.db)
    try:
        try:
            row = get_min(conn, pool_id)
        except QueryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(_encode_row(row))
    finally:
        conn.close()


def _cmd_max(args: argparse.Namespace) -> None:
    """Handle the 'max' subcommand."""
    pool_id = _normalize_pool_id(args.pool)
    conn = _open_db(args.db)
    try:
        try:
            row = get_max(conn, pool_id)
        except QueryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(_encode_row(row))
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

    # row-by-ts subcommand
    row_by_ts_parser = subparsers.add_parser(
        "row-by-ts", help="Single row by block_timestamp"
    )
    row_by_ts_parser.add_argument("--pool", required=True, help="Pool ID (hex)")
    row_by_ts_parser.add_argument(
        "--ts", required=True, type=int, help="Block timestamp (unix seconds)"
    )
    row_by_ts_parser.add_argument(
        "--nearest",
        action="store_true",
        default=False,
        help="Return nearest-lower row instead of requiring exact match",
    )
    row_by_ts_parser.add_argument("--db", required=True, help="DuckDB file path")

    # range subcommand
    range_parser = subparsers.add_parser("range", help="Row slice [from, to)")
    range_parser.add_argument("--pool", required=True, help="Pool ID (hex)")
    range_parser.add_argument(
        "--from", dest="from_idx", required=True, type=int, help="Start index (inclusive)"
    )
    range_parser.add_argument(
        "--to", required=True, type=int, help="End index (exclusive)"
    )
    range_parser.add_argument("--db", required=True, help="DuckDB file path")

    # min subcommand
    min_parser = subparsers.add_parser("min", help="Row with smallest block_number")
    min_parser.add_argument("--pool", required=True, help="Pool ID (hex)")
    min_parser.add_argument("--db", required=True, help="DuckDB file path")

    # max subcommand
    max_parser = subparsers.add_parser("max", help="Row with largest block_number")
    max_parser.add_argument("--pool", required=True, help="Pool ID (hex)")
    max_parser.add_argument("--db", required=True, help="DuckDB file path")

    args = parser.parse_args()
    dispatch = {
        "len": _cmd_len,
        "row": _cmd_row,
        "row-by-ts": _cmd_row_by_ts,
        "range": _cmd_range,
        "min": _cmd_min,
        "max": _cmd_max,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
