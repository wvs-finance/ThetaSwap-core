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

from scripts.tests.conftest import (
    MOCK_BLOCKS_AND_GROWTH,
    MOCK_BLOCK_TIMESTAMPS,
    USDC_WETH_POOL_ID,
)

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
