"""Pure-function query API for the RAN accumulator sample database.

Zero network dependencies — reads only from an open DuckDB connection.
All functions are pure free functions operating on a caller-supplied connection.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import duckdb

# ── Table name ────────────────────────────────────────────────────────────────

_TABLE: Final[str] = "accumulator_samples"

# ── Domain types ──────────────────────────────────────────────────────────────


class QueryError(Exception):
    """Raised when a query cannot be satisfied (bounds, missing data, NULL ts)."""


@dataclass(frozen=True)
class Row:
    """One accumulator sample row from the DB."""

    block_number: int
    block_timestamp: int
    global_growth: str


# ── Internal helpers ──────────────────────────────────────────────────────────


def _check_null_ts(row_tuple: tuple[int, int | None, str]) -> Row:
    """Convert a DB row tuple to Row, raising QueryError if timestamp is NULL."""
    block_number, block_timestamp, global_growth = row_tuple
    if block_timestamp is None:
        raise QueryError(
            f"block_timestamp is NULL for block {block_number} — "
            "run pipeline to backfill timestamps"
        )
    return Row(
        block_number=block_number,
        block_timestamp=block_timestamp,
        global_growth=global_growth,
    )


# ── Public API ────────────────────────────────────────────────────────────────


def dataset_len(conn: duckdb.DuckDBPyConnection, pool_id: str) -> int:
    """Count ALL rows for pool_id (including NULL block_timestamp rows)."""
    result = conn.execute(
        f"SELECT COUNT(*) FROM {_TABLE} WHERE pool_id = ?",
        [pool_id],
    ).fetchone()
    return int(result[0]) if result is not None else 0


def get_row(conn: duckdb.DuckDBPyConnection, pool_id: str, idx: int) -> Row:
    """Return the row at 0-based index ordered by block_number ASC.

    Raises QueryError for negative idx, out-of-bounds idx, or NULL timestamp.
    """
    if idx < 0:
        raise QueryError(f"Index {idx} is negative")

    length = dataset_len(conn, pool_id)
    if idx >= length:
        raise QueryError(
            f"Index {idx} is out of bounds for pool '{pool_id}' (dataset_len={length})"
        )

    result = conn.execute(
        f"SELECT block_number, block_timestamp, global_growth "
        f"FROM {_TABLE} "
        f"WHERE pool_id = ? "
        f"ORDER BY block_number ASC "
        f"LIMIT 1 OFFSET ?",
        [pool_id, idx],
    ).fetchone()

    if result is None:
        raise QueryError(f"No row at index {idx} for pool '{pool_id}'")

    return _check_null_ts(result)


def get_by_timestamp(
    conn: duckdb.DuckDBPyConnection,
    pool_id: str,
    ts: int,
    exact: bool = True,
) -> Row:
    """Return row matching the given block_timestamp.

    exact=True: exact match; raises QueryError if not found.
    exact=False: nearest-lower (block_timestamp <= ts), highest block_number wins;
                 raises QueryError if ts is below minimum.
    NULL block_timestamp in result raises QueryError.
    """
    if exact:
        result = conn.execute(
            f"SELECT block_number, block_timestamp, global_growth "
            f"FROM {_TABLE} "
            f"WHERE pool_id = ? AND block_timestamp = ? "
            f"ORDER BY block_timestamp DESC, block_number DESC "
            f"LIMIT 1",
            [pool_id, ts],
        ).fetchone()
        if result is None:
            raise QueryError(
                f"No row with block_timestamp={ts} for pool '{pool_id}'"
            )
        return _check_null_ts(result)
    else:
        result = conn.execute(
            f"SELECT block_number, block_timestamp, global_growth "
            f"FROM {_TABLE} "
            f"WHERE pool_id = ? AND block_timestamp <= ? "
            f"ORDER BY block_timestamp DESC, block_number DESC "
            f"LIMIT 1",
            [pool_id, ts],
        ).fetchone()
        if result is None:
            raise QueryError(
                f"Timestamp {ts} is below the minimum for pool '{pool_id}'"
            )
        return _check_null_ts(result)


def get_range(
    conn: duckdb.DuckDBPyConnection,
    pool_id: str,
    from_idx: int,
    to_idx: int,
) -> list[Row]:
    """Return rows [from_idx, to_idx) ordered by block_number ASC.

    Raises QueryError if:
    - from_idx > to_idx
    - from_idx < 0 or to_idx > dataset_len
    - to_idx - from_idx > 1000
    Returns empty list if from_idx == to_idx.
    """
    if from_idx > to_idx:
        raise QueryError(
            f"from_idx ({from_idx}) > to_idx ({to_idx})"
        )
    if from_idx == to_idx:
        return []
    if from_idx < 0:
        raise QueryError(f"from_idx ({from_idx}) is negative")

    length = dataset_len(conn, pool_id)
    if to_idx > length:
        raise QueryError(
            f"to_idx ({to_idx}) exceeds dataset_len ({length}) for pool '{pool_id}'"
        )

    span = to_idx - from_idx
    if span > 1000:
        raise QueryError(
            f"Range [{from_idx}, {to_idx}) spans {span} rows — maximum is 1000"
        )

    results = conn.execute(
        f"SELECT block_number, block_timestamp, global_growth "
        f"FROM {_TABLE} "
        f"WHERE pool_id = ? "
        f"ORDER BY block_number ASC "
        f"LIMIT ? OFFSET ?",
        [pool_id, span, from_idx],
    ).fetchall()

    return [_check_null_ts(r) for r in results]


def get_min(conn: duckdb.DuckDBPyConnection, pool_id: str) -> Row:
    """Return the row with the smallest block_number for pool_id.

    Raises QueryError if pool_id is unknown (no rows).
    """
    if dataset_len(conn, pool_id) == 0:
        raise QueryError(f"No data for pool '{pool_id}'")

    result = conn.execute(
        f"SELECT block_number, block_timestamp, global_growth "
        f"FROM {_TABLE} "
        f"WHERE pool_id = ? "
        f"ORDER BY block_number ASC "
        f"LIMIT 1",
        [pool_id],
    ).fetchone()

    if result is None:
        raise QueryError(f"No data for pool '{pool_id}'")

    return _check_null_ts(result)


def get_max(conn: duckdb.DuckDBPyConnection, pool_id: str) -> Row:
    """Return the row with the largest block_number for pool_id.

    Raises QueryError if pool_id is unknown (no rows).
    """
    if dataset_len(conn, pool_id) == 0:
        raise QueryError(f"No data for pool '{pool_id}'")

    result = conn.execute(
        f"SELECT block_number, block_timestamp, global_growth "
        f"FROM {_TABLE} "
        f"WHERE pool_id = ? "
        f"ORDER BY block_number DESC "
        f"LIMIT 1",
        [pool_id],
    ).fetchone()

    if result is None:
        raise QueryError(f"No data for pool '{pool_id}'")

    return _check_null_ts(result)


def get_all(conn: duckdb.DuckDBPyConnection, pool_id: str) -> list[Row]:
    """Return all rows for pool_id ordered by block_number ASC."""
    results = conn.execute(
        f"SELECT block_number, block_timestamp, global_growth "
        f"FROM {_TABLE} "
        f"WHERE pool_id = ? "
        f"ORDER BY block_number ASC",
        [pool_id],
    ).fetchall()

    return [_check_null_ts(r) for r in results]
