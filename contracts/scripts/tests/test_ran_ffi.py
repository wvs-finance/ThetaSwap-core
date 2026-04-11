"""Tests for the RAN FFI query script (Task 3).

Strict TDD: each behavior tested before implementation.
Uses populated_db_path fixture from conftest (6 blocks with timestamps).
"""
from __future__ import annotations

import subprocess
import sys
from typing import Final

import eth_abi
import pytest

import duckdb

from scripts.ran_data_api import dataset_len, get_min, get_max
from scripts.tests.conftest import (
    MOCK_BLOCKS_AND_GROWTH,
    MOCK_BLOCK_TIMESTAMPS,
    USDC_WETH_POOL_ID,
    FIXED_TIMESTAMP,
)

SORTED_BLOCKS: Final[list[int]] = sorted(MOCK_BLOCKS_AND_GROWTH.keys())

SCRIPTS_DIR: Final[str] = "scripts"
MODULE: Final[str] = "scripts.ran_ffi"


def _run_ffi(
    *args: str,
    db: str,
) -> subprocess.CompletedProcess[str]:
    """Run ran_ffi as a module, returning the CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", MODULE, *args, "--db", db],
        capture_output=True,
        text=True,
    )


# ── Behavior 1: len subcommand ──


class TestLenSubcommand:
    """len returns 0x-prefixed ABI-encoded uint256 row count."""

    def test_len_returns_correct_count(self, populated_db_path: str) -> None:
        result = _run_ffi("len", "--pool", USDC_WETH_POOL_ID, db=populated_db_path)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = result.stdout.strip()
        assert output.startswith("0x")
        (count,) = eth_abi.decode(["uint256"], bytes.fromhex(output[2:]))
        assert count == len(MOCK_BLOCKS_AND_GROWTH)


# ── Behavior 2: row at index 0 ──


class TestRowSubcommand:
    """row returns 0x-prefixed ABI-encoded (uint256, uint256, bytes32)."""

    def test_row_index_0_returns_earliest_block(
        self, populated_db_path: str
    ) -> None:
        result = _run_ffi(
            "row", "--pool", USDC_WETH_POOL_ID, "--idx", "0",
            db=populated_db_path,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = result.stdout.strip()
        assert output.startswith("0x")
        block_num, block_ts, growth_bytes = eth_abi.decode(
            ["uint256", "uint256", "bytes32"],
            bytes.fromhex(output[2:]),
        )
        sorted_blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())
        earliest = sorted_blocks[0]
        assert block_num == earliest
        assert block_ts == MOCK_BLOCK_TIMESTAMPS[earliest]
        expected_growth = bytes.fromhex(MOCK_BLOCKS_AND_GROWTH[earliest][2:])
        assert growth_bytes == expected_growth

    def test_row_last_index_returns_latest_block(
        self, populated_db_path: str
    ) -> None:
        sorted_blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())
        last_idx = len(sorted_blocks) - 1
        result = _run_ffi(
            "row", "--pool", USDC_WETH_POOL_ID, "--idx", str(last_idx),
            db=populated_db_path,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = result.stdout.strip()
        block_num, block_ts, growth_bytes = eth_abi.decode(
            ["uint256", "uint256", "bytes32"],
            bytes.fromhex(output[2:]),
        )
        latest = sorted_blocks[-1]
        assert block_num == latest
        assert block_ts == MOCK_BLOCK_TIMESTAMPS[latest]
        expected_growth = bytes.fromhex(MOCK_BLOCKS_AND_GROWTH[latest][2:])
        assert growth_bytes == expected_growth


# ── Behavior 4: 0x prefix verification ──


class TestHexPrefixOutput:
    """Both len and row outputs must start with 0x."""

    def test_len_output_has_0x_prefix(self, populated_db_path: str) -> None:
        result = _run_ffi("len", "--pool", USDC_WETH_POOL_ID, db=populated_db_path)
        assert result.returncode == 0
        assert result.stdout.strip().startswith("0x")

    def test_row_output_has_0x_prefix(self, populated_db_path: str) -> None:
        result = _run_ffi(
            "row", "--pool", USDC_WETH_POOL_ID, "--idx", "0",
            db=populated_db_path,
        )
        assert result.returncode == 0
        assert result.stdout.strip().startswith("0x")


# ── Behavior 5: Error — invalid index ──


class TestErrorInvalidIndex:
    """Out-of-bounds index exits 1 with range info on stderr."""

    def test_index_equal_to_count_exits_1(self, populated_db_path: str) -> None:
        oob_idx = len(MOCK_BLOCKS_AND_GROWTH)
        result = _run_ffi(
            "row", "--pool", USDC_WETH_POOL_ID, "--idx", str(oob_idx),
            db=populated_db_path,
        )
        assert result.returncode == 1
        assert "out of range" in result.stderr.lower()
        assert str(oob_idx) in result.stderr

    def test_large_index_exits_1(self, populated_db_path: str) -> None:
        result = _run_ffi(
            "row", "--pool", USDC_WETH_POOL_ID, "--idx", "9999",
            db=populated_db_path,
        )
        assert result.returncode == 1
        assert "out of range" in result.stderr.lower()


# ── Behavior 6: Error — unknown pool ──

DEAD_POOL_ID: Final[str] = "0x" + "dead" * 16


class TestErrorUnknownPool:
    """Unknown pool ID exits 1 with 'pool not found' on stderr."""

    def test_len_unknown_pool_exits_1(self, populated_db_path: str) -> None:
        result = _run_ffi("len", "--pool", DEAD_POOL_ID, db=populated_db_path)
        assert result.returncode == 1
        assert "pool not found" in result.stderr.lower()

    def test_row_unknown_pool_exits_1(self, populated_db_path: str) -> None:
        result = _run_ffi(
            "row", "--pool", DEAD_POOL_ID, "--idx", "0",
            db=populated_db_path,
        )
        assert result.returncode == 1
        assert "pool not found" in result.stderr.lower()


# ── Behavior 7: Error — NULL timestamp ──


class TestErrorNullTimestamp:
    """Row with NULL block_timestamp exits 1 with backfill message."""

    def test_null_timestamp_exits_1(self, tmp_path: object) -> None:
        """Insert a row with NULL block_timestamp, query it via row."""
        assert hasattr(tmp_path, "__truediv__")
        db_path = str(tmp_path / "null_ts.duckdb")  # type: ignore[operator]
        import duckdb
        conn = duckdb.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS accumulator_samples ("
            "block_number UBIGINT, pool_id VARCHAR, global_growth VARCHAR, "
            "block_timestamp UBIGINT, sampled_at TIMESTAMP, stride USMALLINT, "
            "PRIMARY KEY (pool_id, block_number))"
        )
        conn.execute(
            "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
            [100, USDC_WETH_POOL_ID, "0x" + "ab" * 32, None, "2026-04-10 00:00:00", 50],
        )
        conn.commit()
        conn.close()
        result = _run_ffi(
            "row", "--pool", USDC_WETH_POOL_ID, "--idx", "0",
            db=db_path,
        )
        assert result.returncode == 1
        assert "backfill" in result.stderr.lower()


# ── Behavior 8: Error — nonexistent DB ──


class TestErrorNonexistentDb:
    """Missing DB file exits 1 with clean error (no traceback)."""

    def test_missing_db_exits_1(self) -> None:
        result = _run_ffi(
            "len", "--pool", USDC_WETH_POOL_ID,
            db="/nonexistent/path/missing.duckdb",
        )
        assert result.returncode == 1
        assert "traceback" not in result.stderr.lower()
        assert result.stderr.strip() != ""


# ── Behavior 9: Zero network dependency ──


class TestZeroNetworkDependency:
    """ran_ffi.py must not import any network libraries."""

    def test_no_network_imports(self) -> None:
        import ast
        from pathlib import Path
        src = Path(__file__).resolve().parent.parent / "ran_ffi.py"
        tree = ast.parse(src.read_text())
        banned = {"httpx", "requests", "urllib", "socket"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in banned, (
                        f"Banned network import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    assert node.module.split(".")[0] not in banned, (
                        f"Banned network import: {node.module}"
                    )


# ── Behavior 10: Pool ID normalization ──


class TestPoolIdNormalization:
    """--pool accepts both 0x-prefixed and bare hex."""

    def test_bare_hex_pool_id_matches(self, populated_db_path: str) -> None:
        bare_pool = USDC_WETH_POOL_ID[2:]  # strip 0x
        result_bare = _run_ffi("len", "--pool", bare_pool, db=populated_db_path)
        result_prefixed = _run_ffi("len", "--pool", USDC_WETH_POOL_ID, db=populated_db_path)
        assert result_bare.returncode == 0, f"stderr: {result_bare.stderr}"
        assert result_bare.stdout.strip() == result_prefixed.stdout.strip()


# ── Behavior 11: row-by-ts subcommand ──


class TestRowByTsSubcommand:
    """row-by-ts returns ABI-encoded (uint256, uint256, bytes32) by timestamp."""

    def test_row_by_ts_exact_match(self, populated_db_path: str) -> None:
        """Exact timestamp lookup returns the expected row."""
        earliest_block = SORTED_BLOCKS[0]
        exact_ts = MOCK_BLOCK_TIMESTAMPS[earliest_block]
        result = _run_ffi(
            "row-by-ts", "--pool", USDC_WETH_POOL_ID,
            "--ts", str(exact_ts),
            db=populated_db_path,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = result.stdout.strip()
        assert output.startswith("0x")
        block_num, block_ts, growth_bytes = eth_abi.decode(
            ["uint256", "uint256", "bytes32"],
            bytes.fromhex(output[2:]),
        )
        assert block_num == earliest_block
        assert block_ts == exact_ts
        expected_growth = bytes.fromhex(MOCK_BLOCKS_AND_GROWTH[earliest_block][2:])
        assert growth_bytes == expected_growth

    def test_row_by_ts_nearest_lower(self, populated_db_path: str) -> None:
        """--nearest flag returns nearest-lower row when ts falls between two rows."""
        # Use a timestamp between blocks[0] and blocks[1]
        block_0 = SORTED_BLOCKS[0]
        block_1 = SORTED_BLOCKS[1]
        ts_0 = MOCK_BLOCK_TIMESTAMPS[block_0]
        ts_1 = MOCK_BLOCK_TIMESTAMPS[block_1]
        between_ts = ts_0 + (ts_1 - ts_0) // 2  # midpoint
        result = _run_ffi(
            "row-by-ts", "--pool", USDC_WETH_POOL_ID,
            "--ts", str(between_ts),
            "--nearest",
            db=populated_db_path,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = result.stdout.strip()
        block_num, block_ts, growth_bytes = eth_abi.decode(
            ["uint256", "uint256", "bytes32"],
            bytes.fromhex(output[2:]),
        )
        # Nearest-lower: should return block_0 (highest block <= between_ts)
        assert block_num == block_0
        assert block_ts == ts_0

    def test_row_by_ts_exact_miss_exits_1(self, populated_db_path: str) -> None:
        """Without --nearest, a timestamp that misses exactly exits 1."""
        block_0 = SORTED_BLOCKS[0]
        block_1 = SORTED_BLOCKS[1]
        ts_0 = MOCK_BLOCK_TIMESTAMPS[block_0]
        ts_1 = MOCK_BLOCK_TIMESTAMPS[block_1]
        miss_ts = ts_0 + 1  # not an exact timestamp in the DB
        result = _run_ffi(
            "row-by-ts", "--pool", USDC_WETH_POOL_ID,
            "--ts", str(miss_ts),
            db=populated_db_path,
        )
        assert result.returncode == 1
        assert result.stderr.strip() != ""


# ── Behavior 12: range subcommand ──


class TestRangeSubcommand:
    """range returns ABI-encoded (uint256, uint256[], uint256[], bytes32[])."""

    def test_range_0_to_3_returns_first_three_rows(
        self, populated_db_path: str
    ) -> None:
        """range [0,3) returns count=3, arrays matching first 3 fixture blocks."""
        result = _run_ffi(
            "range", "--pool", USDC_WETH_POOL_ID,
            "--from", "0", "--to", "3",
            db=populated_db_path,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = result.stdout.strip()
        assert output.startswith("0x")
        count, block_numbers, block_timestamps, growth_list = eth_abi.decode(
            ["uint256", "uint256[]", "uint256[]", "bytes32[]"],
            bytes.fromhex(output[2:]),
        )
        assert count == 3
        assert len(block_numbers) == 3
        assert len(block_timestamps) == 3
        assert len(growth_list) == 3
        expected_blocks = SORTED_BLOCKS[:3]
        for i, blk in enumerate(expected_blocks):
            assert block_numbers[i] == blk
            assert block_timestamps[i] == MOCK_BLOCK_TIMESTAMPS[blk]
            assert growth_list[i] == bytes.fromhex(MOCK_BLOCKS_AND_GROWTH[blk][2:])

    def test_range_exceeds_1000_exits_1(
        self, large_populated_db_path: str
    ) -> None:
        """range [0, 1001) exceeds 1000-row limit and exits 1."""
        result = _run_ffi(
            "range", "--pool", USDC_WETH_POOL_ID,
            "--from", "0", "--to", "1001",
            db=large_populated_db_path,
        )
        assert result.returncode == 1
        assert result.stderr.strip() != ""


# ── Behavior 13: min subcommand ──


class TestMinSubcommand:
    """min returns ABI-encoded row with smallest block_number."""

    def test_min_abi_round_trip(self, populated_db_path: str) -> None:
        """ABI-decoded output matches get_min result."""
        # Get expected via direct API call
        import duckdb as _duckdb
        conn = _duckdb.connect(populated_db_path, read_only=True)
        from scripts.ran_data_api import get_min as _get_min
        expected = _get_min(conn, USDC_WETH_POOL_ID)
        conn.close()

        result = _run_ffi(
            "min", "--pool", USDC_WETH_POOL_ID,
            db=populated_db_path,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = result.stdout.strip()
        assert output.startswith("0x")
        block_num, block_ts, growth_bytes = eth_abi.decode(
            ["uint256", "uint256", "bytes32"],
            bytes.fromhex(output[2:]),
        )
        assert block_num == expected.block_number
        assert block_ts == expected.block_timestamp
        assert growth_bytes == bytes.fromhex(expected.global_growth[2:])


# ── Behavior 14: max subcommand ──


class TestMaxSubcommand:
    """max returns ABI-encoded row with largest block_number."""

    def test_max_abi_round_trip(self, populated_db_path: str) -> None:
        """ABI-decoded output matches get_max result."""
        import duckdb as _duckdb
        conn = _duckdb.connect(populated_db_path, read_only=True)
        from scripts.ran_data_api import get_max as _get_max
        expected = _get_max(conn, USDC_WETH_POOL_ID)
        conn.close()

        result = _run_ffi(
            "max", "--pool", USDC_WETH_POOL_ID,
            db=populated_db_path,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = result.stdout.strip()
        assert output.startswith("0x")
        block_num, block_ts, growth_bytes = eth_abi.decode(
            ["uint256", "uint256", "bytes32"],
            bytes.fromhex(output[2:]),
        )
        assert block_num == expected.block_number
        assert block_ts == expected.block_timestamp
        assert growth_bytes == bytes.fromhex(expected.global_growth[2:])
