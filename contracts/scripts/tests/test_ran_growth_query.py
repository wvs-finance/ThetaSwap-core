"""Tests for ran_growth_query — the CLI query interface (Task 5)."""
from __future__ import annotations

import json
import subprocess
import sys
from typing import Final

import pytest

# ── Constants from conftest ──
USDC_WETH_POOL_ID: Final[str] = (
    "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657"
)


def _run_query(
    *,
    pool: str,
    block: int,
    db: str,
) -> subprocess.CompletedProcess[str]:
    """Run ran_growth_query.py as a subprocess and return the result."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.ran_growth_query",
            "--pool", pool,
            "--block", str(block),
            "--db", db,
        ],
        capture_output=True,
        text=True,
        cwd=str(__file__).rsplit("/scripts/", 1)[0],  # contracts/
    )


# ── B-Q1: Exact block match ──


class TestExactBlockMatch:
    """Query a block that exists in the DB returns exact result."""

    def test_exact_match_returns_correct_json(
        self, populated_db_path: str
    ) -> None:
        result = _run_query(pool="usdc-weth", block=22_972_937, db=populated_db_path)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        payload = json.loads(result.stdout)
        assert payload["blockNumber"] == 22_972_937
        assert payload["globalGrowth"] == (
            "0x0000000000000000000000000000000000002d2c02eeae24bd7a65341761b9c3"
        )
        assert payload["poolId"] == USDC_WETH_POOL_ID
        assert payload["exact"] is True

    def test_exact_match_has_exactly_four_keys(
        self, populated_db_path: str
    ) -> None:
        result = _run_query(pool="usdc-weth", block=22_972_937, db=populated_db_path)
        payload = json.loads(result.stdout)
        assert set(payload.keys()) == {"blockNumber", "globalGrowth", "poolId", "exact"}

    def test_exact_match_another_block(
        self, populated_db_path: str
    ) -> None:
        result = _run_query(pool="usdc-weth", block=22_973_087, db=populated_db_path)
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["blockNumber"] == 22_973_087
        assert payload["globalGrowth"] == (
            "0x0000000000000000000000000000000000002d2c264a9db5732dd906c9ef5491"
        )
        assert payload["exact"] is True


# ── B-Q2: Nearest-lower match ──


class TestNearestLowerMatch:
    """Query a block NOT in DB returns nearest lower sample."""

    def test_nearest_lower_returns_six_keys(
        self, populated_db_path: str
    ) -> None:
        # 22_972_950 is between 22_972_937 and 22_972_987
        result = _run_query(pool="usdc-weth", block=22_972_950, db=populated_db_path)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        payload = json.loads(result.stdout)
        assert set(payload.keys()) == {
            "blockNumber", "globalGrowth", "poolId",
            "exact", "sampledBlock", "blockDelta",
        }

    def test_nearest_lower_values(
        self, populated_db_path: str
    ) -> None:
        result = _run_query(pool="usdc-weth", block=22_972_950, db=populated_db_path)
        payload = json.loads(result.stdout)
        assert payload["blockNumber"] == 22_972_950
        assert payload["exact"] is False
        assert payload["sampledBlock"] == 22_972_937
        assert payload["blockDelta"] == 22_972_950 - 22_972_937
        assert payload["globalGrowth"] == (
            "0x0000000000000000000000000000000000002d2c02eeae24bd7a65341761b9c3"
        )
        assert payload["poolId"] == USDC_WETH_POOL_ID

    def test_block_before_earliest_exits_1(
        self, populated_db_path: str
    ) -> None:
        result = _run_query(pool="usdc-weth", block=100, db=populated_db_path)
        assert result.returncode == 1
        assert "Requested block 100 is before earliest sample at block 22972937" in result.stderr


# ── B-Q3: Missing pool error ──


class TestMissingPool:
    """Unknown pool name exits 1 with valid pool names listed."""

    def test_unknown_pool_exits_1(
        self, populated_db_path: str
    ) -> None:
        result = _run_query(pool="nonexistent", block=22_972_937, db=populated_db_path)
        assert result.returncode == 1

    def test_unknown_pool_lists_valid_names(
        self, populated_db_path: str
    ) -> None:
        result = _run_query(pool="nonexistent", block=22_972_937, db=populated_db_path)
        assert "usdc-weth" in result.stderr
        assert "weth-usdt" in result.stderr


# ── B-Q4: Empty DB ──


class TestEmptyDb:
    """Query pool with no rows exits 1 with 'no data fetched' message."""

    def test_empty_db_exits_1(self, tmp_path: object) -> None:
        import duckdb
        assert hasattr(tmp_path, "__truediv__")
        db_path = str(tmp_path / "empty.duckdb")  # type: ignore[operator]
        conn = duckdb.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS accumulator_samples ("
            "block_number UBIGINT, pool_id VARCHAR, global_growth VARCHAR, "
            "sampled_at TIMESTAMP, stride USMALLINT, "
            "PRIMARY KEY (pool_id, block_number))"
        )
        conn.close()
        result = _run_query(pool="usdc-weth", block=22_972_937, db=db_path)
        assert result.returncode == 1
        assert "no data fetched" in result.stderr.lower()


# ── B-Q5: Zero network dependency ──


class TestZeroNetworkDependency:
    """The query module must not import any network library."""

    def test_no_network_imports(self) -> None:  # noqa: PLR6301
        import ast
        import pathlib
        module_path = (
            pathlib.Path(__file__).parent.parent / "ran_growth_query.py"
        )
        tree = ast.parse(module_path.read_text())
        forbidden = {"httpx", "requests", "urllib", "urllib3", "aiohttp", "socket"}
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    imported.add(node.module.split(".")[0])
        violations = imported & forbidden
        assert not violations, f"Forbidden network imports found: {violations}"


# ── B-Q6: Nonexistent DB file ──


class TestNonexistentDbFile:
    """--db pointing to a nonexistent path exits 1 with clean error."""

    def test_nonexistent_db_exits_1(self) -> None:
        result = _run_query(pool="usdc-weth", block=22_972_937, db="/nonexistent/path.duckdb")
        assert result.returncode == 1

    def test_nonexistent_db_clean_error_message(self) -> None:
        result = _run_query(pool="usdc-weth", block=22_972_937, db="/nonexistent/path.duckdb")
        assert "Traceback" not in result.stderr
        assert "database" in result.stderr.lower() or "db" in result.stderr.lower() or "open" in result.stderr.lower()


# ── B-Q7: Negative block number ──


class TestNegativeBlockNumber:
    """--block with negative value exits 1 with clean error."""

    def test_negative_block_exits_1(self, populated_db_path: str) -> None:
        result = _run_query(pool="usdc-weth", block=-1, db=populated_db_path)
        assert result.returncode == 1

    def test_negative_block_error_message(self, populated_db_path: str) -> None:
        result = _run_query(pool="usdc-weth", block=-1, db=populated_db_path)
        assert "non-negative" in result.stderr.lower() or "non negative" in result.stderr.lower()
