"""Tests for ran_data_api — pure-function query API.

All tests open their own read-only DuckDB connection from populated_db_path.
No mocks — real on-chain data via conftest fixtures.
"""
from __future__ import annotations

import ast
import importlib
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Final

import duckdb
import pytest

from scripts.tests.conftest import (
    MOCK_BLOCK_TIMESTAMPS,
    MOCK_BLOCKS_AND_GROWTH,
    USDC_WETH_POOL_ID,
)

# ── Constants ─────────────────────────────────────────────────────────────────

SORTED_BLOCKS: Final[list[int]] = sorted(MOCK_BLOCKS_AND_GROWTH)
UNKNOWN_POOL: Final[str] = "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"


# ── Helpers ───────────────────────────────────────────────────────────────────


def open_ro(db_path: str) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(db_path, read_only=True)


# ── Batch 1: QueryError + Row ─────────────────────────────────────────────────


def test_query_error_importable_and_is_exception() -> None:
    from scripts.ran_data_api import QueryError

    assert issubclass(QueryError, Exception)
    err = QueryError("test message")
    assert str(err) == "test message"


def test_row_is_frozen_dataclass_with_correct_fields() -> None:
    from scripts.ran_data_api import Row

    assert is_dataclass(Row)
    # Verify frozen
    instance = Row(block_number=1, block_timestamp=2, global_growth="0x00")
    with pytest.raises((TypeError, AttributeError)):
        instance.block_number = 99  # type: ignore[misc]

    field_names = {f.name for f in fields(Row)}
    assert field_names == {"block_number", "block_timestamp", "global_growth"}


# ── Batch 2: dataset_len ──────────────────────────────────────────────────────


def test_dataset_len_returns_six(populated_db_path: str) -> None:
    from scripts.ran_data_api import dataset_len

    conn = open_ro(populated_db_path)
    try:
        assert dataset_len(conn, USDC_WETH_POOL_ID) == 6
    finally:
        conn.close()


def test_dataset_len_unknown_pool_returns_zero(populated_db_path: str) -> None:
    from scripts.ran_data_api import dataset_len

    conn = open_ro(populated_db_path)
    try:
        assert dataset_len(conn, UNKNOWN_POOL) == 0
    finally:
        conn.close()


# ── Batch 3: get_row ──────────────────────────────────────────────────────────


def test_get_row_index_zero_returns_first_block(populated_db_path: str) -> None:
    from scripts.ran_data_api import Row, get_row

    conn = open_ro(populated_db_path)
    try:
        row = get_row(conn, USDC_WETH_POOL_ID, 0)
        assert isinstance(row, Row)
        assert row.block_number == SORTED_BLOCKS[0]  # 22972937
        assert row.block_timestamp == MOCK_BLOCK_TIMESTAMPS[SORTED_BLOCKS[0]]  # 1700000000
        assert row.global_growth == MOCK_BLOCKS_AND_GROWTH[SORTED_BLOCKS[0]]
    finally:
        conn.close()


def test_get_row_index_five_returns_last_block(populated_db_path: str) -> None:
    from scripts.ran_data_api import Row, get_row

    conn = open_ro(populated_db_path)
    try:
        row = get_row(conn, USDC_WETH_POOL_ID, 5)
        assert isinstance(row, Row)
        assert row.block_number == SORTED_BLOCKS[5]  # 22973187
        assert row.block_timestamp == MOCK_BLOCK_TIMESTAMPS[SORTED_BLOCKS[5]]  # 1700003000
        assert row.global_growth == MOCK_BLOCKS_AND_GROWTH[SORTED_BLOCKS[5]]
    finally:
        conn.close()


def test_get_row_out_of_bounds_raises_query_error(populated_db_path: str) -> None:
    from scripts.ran_data_api import QueryError, get_row

    conn = open_ro(populated_db_path)
    try:
        with pytest.raises(QueryError):
            get_row(conn, USDC_WETH_POOL_ID, 6)
    finally:
        conn.close()


def test_get_row_negative_index_raises_query_error(populated_db_path: str) -> None:
    from scripts.ran_data_api import QueryError, get_row

    conn = open_ro(populated_db_path)
    try:
        with pytest.raises(QueryError):
            get_row(conn, USDC_WETH_POOL_ID, -1)
    finally:
        conn.close()


# ── Batch 4: get_by_timestamp ─────────────────────────────────────────────────


def test_get_by_timestamp_exact_match(populated_db_path: str) -> None:
    from scripts.ran_data_api import Row, get_by_timestamp

    conn = open_ro(populated_db_path)
    try:
        # block 22972987 has timestamp 1700000600
        ts = MOCK_BLOCK_TIMESTAMPS[SORTED_BLOCKS[1]]  # 1700000600
        row = get_by_timestamp(conn, USDC_WETH_POOL_ID, ts, exact=True)
        assert isinstance(row, Row)
        assert row.block_number == SORTED_BLOCKS[1]
        assert row.block_timestamp == ts
    finally:
        conn.close()


def test_get_by_timestamp_exact_no_match_raises(populated_db_path: str) -> None:
    from scripts.ran_data_api import QueryError, get_by_timestamp

    conn = open_ro(populated_db_path)
    try:
        with pytest.raises(QueryError):
            get_by_timestamp(conn, USDC_WETH_POOL_ID, 1700000601, exact=True)
    finally:
        conn.close()


def test_get_by_timestamp_nearest_lower(populated_db_path: str) -> None:
    from scripts.ran_data_api import Row, get_by_timestamp

    conn = open_ro(populated_db_path)
    try:
        # 1700000900 is between ts[1]=1700000600 and ts[2]=1700001200
        # nearest-lower should return block at ts=1700000600
        row = get_by_timestamp(conn, USDC_WETH_POOL_ID, 1700000900, exact=False)
        assert isinstance(row, Row)
        assert row.block_timestamp == MOCK_BLOCK_TIMESTAMPS[SORTED_BLOCKS[1]]  # 1700000600
        assert row.block_number == SORTED_BLOCKS[1]
    finally:
        conn.close()


def test_get_by_timestamp_nearest_lower_below_min_raises(populated_db_path: str) -> None:
    from scripts.ran_data_api import QueryError, get_by_timestamp

    conn = open_ro(populated_db_path)
    try:
        with pytest.raises(QueryError):
            get_by_timestamp(conn, USDC_WETH_POOL_ID, 1699999999, exact=False)
    finally:
        conn.close()


def test_get_by_timestamp_tiebreak_highest_block_number(tmp_path: object) -> None:
    """Two rows with identical timestamp — highest block_number wins."""
    from scripts.ran_data_api import get_by_timestamp
    from scripts.tests.conftest import CREATE_TABLE_DDL, FIXED_TIMESTAMP

    assert hasattr(tmp_path, "__truediv__")
    db_path = str(tmp_path / "tiebreak_test.duckdb")  # type: ignore[operator]
    conn_w = duckdb.connect(db_path)
    conn_w.execute(CREATE_TABLE_DDL)
    shared_ts = 1_700_000_000
    conn_w.execute(
        "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
        [100, USDC_WETH_POOL_ID, "0x" + "aa" * 32, shared_ts, FIXED_TIMESTAMP, 50],
    )
    conn_w.execute(
        "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
        [200, USDC_WETH_POOL_ID, "0x" + "bb" * 32, shared_ts, FIXED_TIMESTAMP, 50],
    )
    conn_w.commit()
    conn_w.close()

    conn_r = duckdb.connect(db_path, read_only=True)
    try:
        row = get_by_timestamp(conn_r, USDC_WETH_POOL_ID, shared_ts, exact=True)
        assert row.block_number == 200, "Tie-break should pick highest block_number"
        assert row.global_growth == "0x" + "bb" * 32

        row_nearest = get_by_timestamp(conn_r, USDC_WETH_POOL_ID, shared_ts + 100, exact=False)
        assert row_nearest.block_number == 200, "Nearest-lower tie-break should also pick highest block_number"
    finally:
        conn_r.close()


# ── Batch 5: get_range ────────────────────────────────────────────────────────


def test_get_range_zero_to_three_returns_three_rows(populated_db_path: str) -> None:
    from scripts.ran_data_api import Row, get_range

    conn = open_ro(populated_db_path)
    try:
        rows = get_range(conn, USDC_WETH_POOL_ID, 0, 3)
        assert len(rows) == 3
        assert all(isinstance(r, Row) for r in rows)
        assert [r.block_number for r in rows] == SORTED_BLOCKS[:3]
    finally:
        conn.close()


def test_get_range_empty_when_from_eq_to(populated_db_path: str) -> None:
    from scripts.ran_data_api import get_range

    conn = open_ro(populated_db_path)
    try:
        rows = get_range(conn, USDC_WETH_POOL_ID, 0, 0)
        assert rows == []
    finally:
        conn.close()


def test_get_range_from_greater_than_to_raises(populated_db_path: str) -> None:
    from scripts.ran_data_api import QueryError, get_range

    conn = open_ro(populated_db_path)
    try:
        with pytest.raises(QueryError):
            get_range(conn, USDC_WETH_POOL_ID, 3, 0)
    finally:
        conn.close()


def test_get_range_exceeds_1000_raises(large_populated_db_path: str) -> None:
    from scripts.ran_data_api import QueryError, get_range

    conn = open_ro(large_populated_db_path)
    try:
        with pytest.raises(QueryError):
            get_range(conn, USDC_WETH_POOL_ID, 0, 1001)
    finally:
        conn.close()


def test_get_range_oob_on_six_row_fixture_raises(populated_db_path: str) -> None:
    from scripts.ran_data_api import QueryError, get_range

    conn = open_ro(populated_db_path)
    try:
        # to_idx=100 > dataset_len=6 → OOB
        with pytest.raises(QueryError):
            get_range(conn, USDC_WETH_POOL_ID, 0, 100)
    finally:
        conn.close()


def test_get_range_negative_from_raises(populated_db_path: str) -> None:
    from scripts.ran_data_api import QueryError, get_range

    conn = open_ro(populated_db_path)
    try:
        with pytest.raises(QueryError):
            get_range(conn, USDC_WETH_POOL_ID, -1, 3)
    finally:
        conn.close()


# ── Batch 6: get_min / get_max ────────────────────────────────────────────────


def test_get_min_equals_get_row_zero(populated_db_path: str) -> None:
    from scripts.ran_data_api import get_min, get_row

    conn = open_ro(populated_db_path)
    try:
        assert get_min(conn, USDC_WETH_POOL_ID) == get_row(conn, USDC_WETH_POOL_ID, 0)
    finally:
        conn.close()


def test_get_max_equals_get_row_five(populated_db_path: str) -> None:
    from scripts.ran_data_api import get_max, get_row

    conn = open_ro(populated_db_path)
    try:
        assert get_max(conn, USDC_WETH_POOL_ID) == get_row(conn, USDC_WETH_POOL_ID, 5)
    finally:
        conn.close()


def test_get_min_unknown_pool_raises(populated_db_path: str) -> None:
    from scripts.ran_data_api import QueryError, get_min

    conn = open_ro(populated_db_path)
    try:
        with pytest.raises(QueryError):
            get_min(conn, UNKNOWN_POOL)
    finally:
        conn.close()


def test_get_max_unknown_pool_raises(populated_db_path: str) -> None:
    from scripts.ran_data_api import QueryError, get_max

    conn = open_ro(populated_db_path)
    try:
        with pytest.raises(QueryError):
            get_max(conn, UNKNOWN_POOL)
    finally:
        conn.close()


# ── Batch 7: get_all ──────────────────────────────────────────────────────────


def test_get_all_returns_six_rows_ordered(populated_db_path: str) -> None:
    from scripts.ran_data_api import Row, get_all

    conn = open_ro(populated_db_path)
    try:
        rows = get_all(conn, USDC_WETH_POOL_ID)
        assert len(rows) == 6
        assert all(isinstance(r, Row) for r in rows)
        assert [r.block_number for r in rows] == SORTED_BLOCKS
    finally:
        conn.close()


# ── Batch 8: NULL timestamp + zero network ────────────────────────────────────


def test_get_row_null_timestamp_raises_query_error(tmp_path: object) -> None:
    """Insert a row with NULL block_timestamp; get_row at that index must raise."""
    from scripts.ran_data_api import QueryError, get_row
    from scripts.tests.conftest import CREATE_TABLE_DDL, FIXED_TIMESTAMP

    assert hasattr(tmp_path, "__truediv__")
    db_path = str(tmp_path / "null_ts_test.duckdb")  # type: ignore[operator]
    conn_w = duckdb.connect(db_path)
    conn_w.execute(CREATE_TABLE_DDL)
    conn_w.execute(
        "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
        [22_999_999, USDC_WETH_POOL_ID, "0x" + "ab" * 32, None, FIXED_TIMESTAMP, 50],
    )
    conn_w.commit()
    conn_w.close()

    conn_r = duckdb.connect(db_path, read_only=True)
    try:
        with pytest.raises(QueryError, match="backfill"):
            get_row(conn_r, USDC_WETH_POOL_ID, 0)
    finally:
        conn_r.close()


def test_ran_data_api_has_no_network_imports() -> None:
    """AST check: ran_data_api must not import httpx, requests, urllib, socket."""
    module_path = Path(
        "/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/ran_data_api.py"
    )
    source = module_path.read_text()
    tree = ast.parse(source)

    forbidden: Final[frozenset[str]] = frozenset({"httpx", "requests", "urllib", "socket"})

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                assert top not in forbidden, f"Forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                assert top not in forbidden, f"Forbidden from-import: {node.module}"
