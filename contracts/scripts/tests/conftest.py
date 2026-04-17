"""Shared test fixtures for the RAN growth pipeline + FX-vol notebooks.

Two responsibilities coexist here:
  * RAN growth pipeline fixtures (mock RPC transport, populated DuckDBs,
    pool configs) — prerequisites for Tasks 2-6 of the RAN pipeline.
  * FX-vol structural econometrics `conn` fixture — a session-scoped,
    read-only DuckDB connection to the real populated ``structural_econ.duckdb``
    used by the notebook test suite (Task 1b onward of the econ-notebook plan).

This file must stay self-contained — no imports from pipeline modules.
"""
from __future__ import annotations

import json
import random
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final

import duckdb
import httpx
import pytest

# ── Constants ──

FIXED_TIMESTAMP: Final[str] = "2026-04-10 00:00:00"
USDC_WETH_POOL_ID: Final[str] = (
    "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657"
)
POOL_REWARDS_SLOT: Final[int] = 7
REWARD_GROWTH_SIZE: Final[int] = 16_777_216

CREATE_TABLE_DDL: Final[str] = (
    "CREATE TABLE IF NOT EXISTS accumulator_samples ("
    "block_number UBIGINT, "
    "pool_id VARCHAR, "
    "global_growth VARCHAR, "
    "block_timestamp UBIGINT, "
    "sampled_at TIMESTAMP, "
    "stride USMALLINT, "
    "PRIMARY KEY (pool_id, block_number))"
)

# ── Mock data ──

MOCK_BLOCKS_AND_GROWTH: Final[dict[int, str]] = {
    22_972_937: "0x0000000000000000000000000000000000002d2c02eeae24bd7a65341761b9c3",
    22_972_987: "0x0000000000000000000000000000000000002d2c20f39492940b8e1e976b5ad2",
    22_973_037: "0x0000000000000000000000000000000000002d2c25dac528b30438b74a1fb3eb",
    22_973_087: "0x0000000000000000000000000000000000002d2c264a9db5732dd906c9ef5491",
    22_973_137: "0x0000000000000000000000000000000000002d2c30aabbcc11223344deadbeef",
    22_973_187: "0x" + "0" * 64,  # zero value block
}

MOCK_BLOCK_TIMESTAMPS: Final[dict[int, int]] = {
    block: 1_700_000_000 + (i * 600)
    for i, block in enumerate(sorted(MOCK_BLOCKS_AND_GROWTH))
}

DEFAULT_HEAD_BLOCK: Final[int] = max(MOCK_BLOCKS_AND_GROWTH) + 1000


# ── Mock RPC Transport ──

@dataclass(frozen=True)
class _MockTransportConfig:
    """Configuration for a mock httpx transport instance."""
    growth_data: dict[int, str]
    block_timestamps: dict[int, int] = None  # type: ignore[assignment]
    shuffle: bool = False
    fail_count: int = 0
    fail_status: int = 429
    timeout_count: int = 0
    head_block: int = DEFAULT_HEAD_BLOCK

    def __post_init__(self) -> None:
        if self.block_timestamps is None:
            object.__setattr__(self, "block_timestamps", MOCK_BLOCK_TIMESTAMPS)


class MockRpcTransport(httpx.BaseTransport):
    """Mock httpx transport for JSON-RPC batch requests.

    Test infrastructure — exempt from functional-python no-class rule.
    Mutable state (request counter) is required for fail/timeout simulation.
    """

    def __init__(self, config: _MockTransportConfig) -> None:
        self._config = config
        self._request_count = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self._request_count += 1

        # Timeout simulation
        if self._request_count <= self._config.timeout_count:
            raise httpx.TimeoutException(
                f"Mock timeout on request {self._request_count}"
            )

        # Failure simulation
        if self._request_count <= (
            self._config.timeout_count + self._config.fail_count
        ):
            return httpx.Response(
                status_code=self._config.fail_status,
                json={"error": "rate limited"},
            )

        # Parse the request body
        body = json.loads(request.content.decode())

        # Handle single object as batch of one
        requests_list: list[dict[str, object]] = (
            body if isinstance(body, list) else [body]
        )

        responses: list[dict[str, object]] = [
            self._handle_single_rpc(rpc_req) for rpc_req in requests_list
        ]

        if self._config.shuffle:
            random.shuffle(responses)

        # Return single object if input was single, array if batch
        result = responses if isinstance(body, list) else responses[0]
        return httpx.Response(status_code=200, json=result)

    def _handle_single_rpc(
        self, rpc_req: dict[str, object]
    ) -> dict[str, object]:
        method = rpc_req.get("method", "")
        req_id = rpc_req.get("id", 0)

        if method in ("eth_getBlockNumber", "eth_blockNumber"):
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": hex(self._config.head_block),
            }

        if method == "eth_getStorageAt":
            params = rpc_req.get("params", [])
            assert isinstance(params, list) and len(params) >= 3
            # Block number is the THIRD element, hex-encoded
            block_hex = str(params[2])
            block_num = int(block_hex, 16)
            value = self._config.growth_data.get(
                block_num, "0x" + "0" * 64
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": value}

        if method == "eth_getBlockByNumber":
            params = rpc_req.get("params", [])
            assert isinstance(params, list) and len(params) >= 1
            block_hex = str(params[0])
            block_num = int(block_hex, 16)
            ts = self._config.block_timestamps.get(block_num)
            if ts is None:
                return {"jsonrpc": "2.0", "id": req_id, "result": None}
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"timestamp": hex(ts), "number": hex(block_num)},
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }


# ── Fixtures ──

@pytest.fixture
def duckdb_conn() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with accumulator_samples table. For unit tests."""
    conn = duckdb.connect(":memory:")
    conn.execute(CREATE_TABLE_DDL)
    return conn


@pytest.fixture
def duckdb_file_conn(tmp_path: object) -> tuple[duckdb.DuckDBPyConnection, str]:
    """File-backed DuckDB for crash recovery tests (B-P5).

    Returns (connection, file_path) so tests can close and reopen.
    """
    assert hasattr(tmp_path, "__truediv__")  # pathlib.Path
    db_path = str(tmp_path / "test_accumulator.duckdb")  # type: ignore[operator]
    conn = duckdb.connect(db_path)
    conn.execute(CREATE_TABLE_DDL)
    return conn, db_path


@pytest.fixture
def mock_growth_data() -> dict[int, str]:
    """Block number → globalGrowth hex values for test scenarios."""
    return dict(MOCK_BLOCKS_AND_GROWTH)


@pytest.fixture
def mock_rpc_transport(
    mock_growth_data: dict[int, str],
) -> object:
    """Factory fixture returning a callable that creates MockRpcTransport instances.

    Usage: transport = mock_rpc_transport(shuffle=True, head_block=23_000_000)
    Then:  client = httpx.Client(transport=transport)
    """
    def _factory(
        *,
        shuffle: bool = False,
        fail_count: int = 0,
        fail_status: int = 429,
        timeout_count: int = 0,
        head_block: int = DEFAULT_HEAD_BLOCK,
        block_timestamps: dict[int, int] | None = None,
    ) -> MockRpcTransport:
        config = _MockTransportConfig(
            growth_data=mock_growth_data,
            block_timestamps=block_timestamps if block_timestamps is not None else MOCK_BLOCK_TIMESTAMPS,
            shuffle=shuffle,
            fail_count=fail_count,
            fail_status=fail_status,
            timeout_count=timeout_count,
            head_block=head_block,
        )
        return MockRpcTransport(config)

    return _factory


@pytest.fixture
def usdc_weth_config() -> dict[str, object]:
    """USDC_WETH pool configuration matching Ethereum.sol constants.

    Returns a plain dict so tests don't depend on ran_utils PoolConfig type.
    Agents implementing ran_utils.py will create the real frozen dataclass.
    """
    return {
        "pool_id": USDC_WETH_POOL_ID,
        "pool_rewards_slot": POOL_REWARDS_SLOT,
        "reward_growth_size": REWARD_GROWTH_SIZE,
        "name": "usdc-weth",
    }


@pytest.fixture
def populated_db_path(
    tmp_path: object,
    mock_growth_data: dict[int, str],
) -> str:
    """File-backed DuckDB pre-populated with mock data, then CLOSED.

    Returns the file path as a string for query tests (Task 5).
    Uses raw SQL inserts — does NOT import from ran_growth_pipeline.
    """
    assert hasattr(tmp_path, "__truediv__")
    db_path = str(tmp_path / "populated_accumulator.duckdb")  # type: ignore[operator]
    conn = duckdb.connect(db_path)
    conn.execute(CREATE_TABLE_DDL)
    for block_num, growth_hex in mock_growth_data.items():
        conn.execute(
            "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
            [block_num, USDC_WETH_POOL_ID, growth_hex, MOCK_BLOCK_TIMESTAMPS[block_num], FIXED_TIMESTAMP, 50],
        )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def large_populated_db_path(tmp_path: object) -> str:
    """File-backed DuckDB with 1,050 synthetic rows at stride 50.

    Tests the 1,000-row range limit independently from bounds checking.
    Blocks: 22_972_937 + (i * 50) for i in 0..1049
    Timestamps: 1_700_000_000 + (i * 600) for deterministic progression
    Growth: synthetic incrementing hex "0x" + hex(i+1)[2:].zfill(64)
    Pool ID: USDC_WETH_POOL_ID
    Stride: 50

    Returns the file path as a string, connection CLOSED.
    Uses raw SQL inserts — does NOT import from ran_growth_pipeline.
    """
    assert hasattr(tmp_path, "__truediv__")
    db_path = str(tmp_path / "large_populated_accumulator.duckdb")  # type: ignore[operator]
    conn = duckdb.connect(db_path)
    conn.execute(CREATE_TABLE_DDL)

    base_block = 22_972_937
    base_timestamp = 1_700_000_000

    for i in range(1050):
        block_num = base_block + (i * 50)
        growth_hex = "0x" + hex(i + 1)[2:].zfill(64)
        block_timestamp = base_timestamp + (i * 600)
        conn.execute(
            "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
            [block_num, USDC_WETH_POOL_ID, growth_hex, block_timestamp, FIXED_TIMESTAMP, 50],
        )
    conn.commit()
    conn.close()
    return db_path


# ── FX-vol structural econometrics fixture ──

# The DuckDB file is at <contracts>/data/structural_econ.duckdb.
# This conftest lives at <contracts>/scripts/tests/conftest.py, so the
# contracts/ root is parents[2] from here.
_STRUCTURAL_ECON_DB: Final[Path] = (
    Path(__file__).resolve().parents[2] / "data" / "structural_econ.duckdb"
)


@pytest.fixture(scope="session")
def conn() -> Iterator[duckdb.DuckDBPyConnection]:
    """Session-scoped read-only DuckDB connection to structural_econ.duckdb.

    Opens the real populated database — no mocks. Yield-pattern cleanup
    closes the connection at session teardown.

    Tests requesting this fixture can run SQL directly, e.g.:
        conn.execute("SELECT COUNT(*) FROM weekly_panel").fetchone()
    """
    assert _STRUCTURAL_ECON_DB.is_file(), (
        f"structural_econ.duckdb missing at {_STRUCTURAL_ECON_DB}"
    )
    connection = duckdb.connect(str(_STRUCTURAL_ECON_DB), read_only=True)
    try:
        yield connection
    finally:
        connection.close()
